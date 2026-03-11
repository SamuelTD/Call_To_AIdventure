#region IMPORTS
import os
import re, json
from dotenv import load_dotenv
from typing_extensions import TypedDict

load_dotenv()

import chromadb
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq

from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import AgentState
from langchain_core.output_parsers import StrOutputParser

from utils.python_utils import clear
from utils.player import Player, save_player, load_player
from utils.monster import Monster
from utils.adventure import Adventure, load_adventure, load_all_adventures
from utils.enums import PlayerAction
from utils.pathing import CHROMA_DIR
from combat.core import setup_combat, player_action, monster_attack
from llm.models import ChoiceOutput

import gradio as gr
from functools import partial
from PIL import Image
from pathlib import Path

import random


#region CONFIG
seed=random.randrange(2**32)

# --- Configuration constants ---
CHAR_COL = "characters"
LOC_COL = "locations"
EMBEDDING_MODEL = "mxbai-embed-large:latest"
LLM_MODEL = "llama3.2:latest"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL= os.getenv("GROQ_MODEL")

# --- Define Graph State Schema ---
class GameState(TypedDict, total=False):
    player: Player
    adventure: Adventure
    history: list[str]
    story_steps: int
    latest_user: str
    last_cmd: dict
    combat_result: dict
    should_end: bool
    current_monster_name: str
    current_monster: Monster
    current_choices: list[str]
    last_choices: list[str]
    current_story: str
    combat_fluff: str
    gold_loot: int
    item_loot: list[str]
    after_combat: bool

# --- Embeddings & Vector Stores ---
ollama_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
vectorstore_char = Chroma(
    client=chromadb.PersistentClient(path=str(CHROMA_DIR)),
    collection_name=CHAR_COL,
    embedding_function=ollama_embeddings
)
vectorstore_loc = Chroma(
    client=chromadb.PersistentClient(path=str(CHROMA_DIR)),
    collection_name=LOC_COL,
    embedding_function=ollama_embeddings
)

# region TOOLS
# --- tool definitions ---
def combat_tool(enemy: str) -> dict:
    return {"action": "combat", "enemy": enemy}

def nothing_tool(_: str) -> dict:
    return {"action": "continue"}

def heal_tool(amount: int) -> dict:
    #player.hp += amount
    return {"action": "continue"}

tools = [
    Tool(name="combat", func=combat_tool, description="When the player is facing a monster, start combat against that monster ; arg monster name", return_direct=True),
    Tool(name="nothing", func=nothing_tool, description="Return nothing, do nothing.", return_direct=True),
    Tool(name="heal", func=heal_tool, description="When the player should regain health ; arg heal amount", return_direct=True)
]


#region LLM AND AGENTS
# llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.5, model_kwargs={"seed": seed})
llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.5, model_kwargs={"seed": seed})



template = ChatPromptTemplate.from_template("{full_prompt}")
story_chain = template | llm | StrOutputParser()

instruction = ""

def prompt_fn(state: AgentState) -> list[SystemMessage | HumanMessage]:
    # Prepend your system instructions...
    sys = SystemMessage(content=instruction)
    # …then include whatever messages the agent has already seen
    return [sys, *state["messages"]]

thinker_agent = ""

summary_template = ChatPromptTemplate.from_template(
    "You are a concise summarizer for fantasy narrative. You write in the past tense, in the third person and replace the 2nd person by \"the player\"."
    "Condense the following narrative context into a single paragraph starting with \"Summary of the story :\":\n\n"
    "{context}"
)

summary_chain = summary_template | llm | StrOutputParser()

choicer_template = ChatPromptTemplate.from_template(
    "You are a role player in a fantasy adventure.\n"
    "Here is the current state of your character:\n"
    "{player_summary}\n\n"
    "Here is the current narrative context:\n"
    "{context}\n\n"
    "Return exactly three possible next actions for the player.\n"
    "Rules:\n"
    "- Each action must be at most 6 words long.\n"
    "- The three actions must be meaningfully different.\n"
    "- Only offer actions that make sense in the immediate current situation.\n"
    "- Only offer spellcasting if the class is wizard.\n"
    "- If another character is actively speaking, one action may be dialogue.\n"
    "- Do not repeat or closely paraphrase these previous choices:\n"
    "{last_choices}\n"
)

# choicer_template = ChatPromptTemplate.from_template(
#     "You are a role player in an adventure." 
#     "Here is the current state of your character :"
#     "{player_summary}"
#     "Your role is to determine which next courses of action are aceptable based on your character and the current context :"
#     "{context}"
#     "You will ONLY output EXACTLY three (3) actions using the following schema :"
#     "[action1, action2, action3]"
#     "Each action is at maximum 6 words long."
#     "You will refrain from giving actions that are similar to each other."
#     "You can only cast spells if your class is \"wizard\"."
#     "An action can be speech (for example: \"My name is ...\" or \"I'm looking for ...\") if another character in the scene speaks to you."
#     "You MUST offer actions that are different from those actions :"
#     "{last_choices}"
#     "You MUST be reactive to the current narrative. The actions you offer MUST be logical based on the most recent events."
#     "For example if you are falling down a hall you cannot \"take your time to look around\"."
# )
# choicer_chain = choicer_template | llm | StrOutputParser()

choicer_model = llm.with_structured_output(ChoiceOutput)
choicer_chain = choicer_template | choicer_model

# region UTILS

def make_choice(history: list[str], player_summary: str, previous_choices:list[str]) -> str:
    context = "\n".join(history)
    last_choices = " - ".join(previous_choices)
    
    result = choicer_chain.invoke({
        "context": context,
        "player_summary": player_summary,
        "last_choices": last_choices,
    })

    print("DEBUG CHOICES == ", result)
    return result.choices

def compress_history(history: list[str]) -> list[str]:
    # Only summarize when there are more than 4 entries
    if len(history) <= 6:
        return history

    # 2) Extract the part to summarize
    to_summarize = "\n".join(history[:-4])

    # 3) Get the summary
    summary = summary_chain.invoke({"context": to_summarize}).strip()

    # 4) Pull out the trailing four entries
    #    history[-4] = 2nd-to-last user input
    #    history[-3] = 2nd-to-last story beat
    #    history[-2] = last user input
    #    history[-1] = last story beat
    second_last_user  = history[-4]
    second_last_story = history[-3]
    last_user         = history[-2]
    last_story        = history[-1]

    #    Reorder to: summary, story(n−1), user(n−1), story(n), user(n)
    result = [
        summary,
        second_last_story,
        second_last_user,
        last_story,
        last_user
    ]
    
    # print("====================== DEBUG ===========================")
    # print(result)
   
    return result

# region GAME LOGIC

def load_adv(id: str, print: bool) -> str:
    
    adv = load_adventure(id)
    
    with open(f"data/world/adventures/{id}/intro.txt", "r") as f:
        intro = f.read()
        
    if print: print(intro)
    return adv, intro

def load_adv_intro(id: str) -> str:
    with open(f"data/world/adventures/{id}/intro.txt", "r") as f:
        intro = f.read()
        
    return intro

# region STEPS
# --- Step Implementations ---

def step_get_input(state: GameState) -> GameState:
    if state["after_combat"]:
        choices = ["Go onward."]
        state["after_combat"] = False
    else:
        if state["story_steps"] > -1:        
            try:
                choices = make_choice(
                    state["history"],
                    state["player"].get_summary(),
                    state["last_choices"]
                )
                
            except Exception as e : 
                print("ERROR : ", e)   
                choices = ["Move forward [Debug]"]  
            

    return {"current_choices": choices, "after_combat": False}


def step_agent_think(state: GameState) -> GameState:
    # hist = f"Context: {state["current_story"]}\n Player action: {state['latest_user']}"
    
    sys_msg = SystemMessage(
        content=(
            "You are the assistant to a fantasy Game Master.\n"
            "You have exactly two tools available:\n"
            "  • combat(enemy: str) — start a fight with that monster\n"
            "  • nothing(_)        — continue the story without combat\n\n"
            "You must respond with exactly one JSON object calling one of these tools—no extra text.\n\n"
            "You may also infer from the user’s description whether one of the known monsters is present—even if they don’t name it.  "
            "If the user says “Strike” “Attack”, “Slash“ or depicts combat intent against a creature on your list, call combat() with that monster’s exact name.\n\n"
            f"Available monsters this adventure: {" - ".join(state["adventure"].monsters)}"
            "If unsure, return {'action':'nothing'}."
        )
    )
    human_msg = HumanMessage(
        content=(
            f"Context:\n{state.get('current_story','')}\n\n"
            f"Player input:\n{state.get('latest_user','')}\n"
        )
    )
    
    resp = thinker_agent.invoke({"messages": [sys_msg, human_msg]})
    # print("AGENT THINKER RESPONSE : ", resp)
    content = resp["messages"][-1].content
    print("DEBUG ========== ", content)
    m = re.match(r'^<function=(?P<name>\w+)(?P<args>\{.*?\})</function>$', content)
    print("DEBUG M ========= ", m)
    if not m:
        tool_msg=json.loads(content)
    else:
        name, raw_args = m.groups()
        args = json.loads(raw_args)
        tool_msg = {"action": name, **args}        
        # return {"last_cmd": "end", "current_monster_name": tool_msg.get("enemy", None)}
        
    # print("DEBUG ================== ", tool_msg)
    action = tool_msg.get("action")
    return {"last_cmd": "continue" if (action == "nothing" or action is None) else action, "current_monster_name": tool_msg.get("enemy", None)}


def step_prepare_combat(state: GameState) -> GameState:
    prompt = f"""
    You are a game master for a fantasy role playing game. Your role is to write short (2-3 sentences maximum) 
    descriptive scenes that will precede a combat. 
    You base your narration on the following context and player input.
    Context: {state["current_story"]}
    Player input: {state["latest_user"]}
    The enemy the player is about to combat is {state["current_monster_name"]}.
    """
    fluff = story_chain.invoke({"full_prompt":prompt}).strip()
   
    return {"combat_fluff": fluff}

def step_generate_story(state: GameState) -> GameState:
    
    state["history"] = compress_history(state["history"])
    
    player_summary = state["player"].get_summary()
    chat_hist = "\n".join(state["history"])
    q = state["latest_user"]
    cmd = state["last_cmd"]
    
    if cmd == "combat":
        enemy = state["current_monster_name"]
        prompt = f"""
                    Here are the informations on the user :
                    {player_summary}
                    
                    Here is the adventure so far:
                    {chat_hist}

                    You are the Game Master for a narrative adventure game. You take continue the story\
                        based on the events so far. You use a refined, fantasy inspired tone to craft the story.\
                            You write in the second person.\
                                Limit each of your answer to four sentences maximum. The user juste vanquished and killed {enemy}.\
                                    Start your output by "You vanquished {enemy}" and go from there, assuming {enemy} is dead.
                                    On the corpse the player found {state["gold_loot"]} gold pieces and {state["item_loot"]} as loot. Incorporate those 
                                    into your narrative.
                    """
        
        state["player"].gold += state["gold_loot"]
        state["last_cmd"] = "continue"
        state["current_monster"] = None
        state["current_monster_name"] = None
        state["gold_loot"] = 0
        state["item_loot"] = []
    else:
        prompt = f"""
                Here are the informations on the user :
                {player_summary}
                
                Here is the adventure so far:
                {chat_hist}

                You are the Game Master for a narrative adventure game. You take the user input and continue the story\
                    based on the events so far and the user input. You use a refined, fantasy inspired tone to craft the story.\
                        You write in the second person.\
                            Limit each of your answer to four sentences maximum. You do your best to make the story go forward without being rushed.
                            You can and should inflict bad outcomes on the player if it makes sense in the story.

                User input: {q}
                """
    story = story_chain.invoke({"full_prompt":prompt}).strip()
    
    print("Story:", story, "\n")
    return {"history": state["history"] + [f"You: {q}", f"Story: {story}"], "current_story": story, "story_steps": state["story_steps"] + 1, "last_cmd": state["last_cmd"]}


#region GRAPHS

def build_pre_input_graph(builder): 
    
     # Nodes

    builder.add_node("get_input", step_get_input)

    # Edges
   
    builder.add_edge(START, "get_input")
    builder.add_edge("get_input", END)
    
    # # Conditional routing after user input
    # builder.add_conditional_edges(
    #     "get_input",
    #     lambda s: s.get("should_end", False),
    #     {True: "end", False: "agent_think"}
    # )   

    graph = builder.compile()

    return graph

def build_post_input_graph(builder):
    
    builder.add_node("agent_think", step_agent_think)
    builder.add_node("prepare_combat", step_prepare_combat)
    builder.add_node("generate_story", step_generate_story)
    
    
    builder.add_conditional_edges(START, lambda s: s.get("last_cmd"),
        {"combat": "generate_story", "continue": "agent_think"})
    
     # Conditional routing after agent thinking
    builder.add_conditional_edges(
        "agent_think",
        lambda s: s.get("last_cmd"),
        {"combat": "prepare_combat", "continue": "generate_story", "end": END}
    )
    # Conditional routing after combat
    builder.add_edge("prepare_combat", END)
    
    #   builder.add_conditional_edges(
    #     "prepare_combat",
    #     lambda s: s["combat_result"]["signal"] == 2,
    #     {True: "end_node", False: "generate_story"}
    # )
   
    builder.add_edge("generate_story", END)

    graph = builder.compile()

    return graph

# region GRADIO

def init(index):
    # only called once, at app start
    global instruction, thinker_agent
    
    player = load_player()
    intro = load_adv_intro(adventures[index].id)
    
    state: GameState = {
        "player": player,
        "adventure": adventures[index],
        "history": [intro],
        "story_steps": 0,
        "should_end": False,
        "combat_result": {"signal": 0, "message": ""},
        "current_story": intro,
        "last_cmd": "continue",
        "after_combat": False,
        "last_choices": []
    }
    
    instruction = (
    "You are the assistant to a fantasy Game Master.\n"
    "You have exactly two tools available:\n"
    "  • combat(enemy: str) — start a fight with that monster\n"
    "  • nothing(_)        — continue the story without combat\n\n"
    "You must respond with exactly one JSON object calling one of these tools—no extra text.\n\n"
    "You may also infer from the user’s description whether one of the known monsters is present—even if they don’t name it.  "
    "If the user says “Strike” “Attack”, “Slash“ or depicts combat intent against a creature on your list, call combat() with that monster’s exact name.\n\n"
    f"Available monsters this adventure: {" - ".join(state["adventure"].monsters)}"
    )
    
    thinker_agent = create_agent(llm, tools)
    
    ctx = pre_graph.invoke(input=state)
    state["current_choices"] = ctx["current_choices"]
    return state
    # return state["current_story"], gr.update(choices=choices, value=None), state

def step(choice, state):
    # 1) drive the “post” graph to update your world‐state
    state = post_graph.invoke(input={**state, "latest_user": choice})
    if state["last_cmd"] == "combat":      
        print("DEBUG : STATE = combat")  
        return gr.update(visible=True), gr.update(visible=False), state["combat_fluff"], gr.update(visible=False), gr.update(visible=False),\
            gr.update(visible=True),  gr.update(visible=False), state
    
    # 2) immediately re‐run the “pre” graph on that new state
    state["last_choices"]=state["current_choices"]
    state = pre_graph.invoke(input=state)
    # 3) extract narrative + next‐choices
    story = state["current_story"]
    choices = state["current_choices"]
    # choices = ["I attack the Zombie, starting a combat."]
    return gr.update(visible=True), gr.update(visible=False), story, gr.update(choices=choices, value=choices[0], visible=True),\
        gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), state

def init_load(file_obj):
    # saved_state = load_state_from_file(file_obj.name)
    # return init(saved_state)
    return None


def start_callback(index, adventures, mode):
    if mode == "new":
        st = init(index)
    else:
        pass
        # story, choices, st = init_load(file_obj)
    story = st["current_story"]
    choices = st["current_choices"]
    # print("DEBUG CHOICES : ", choices)
    return (
        story,
        gr.update(choices=choices, value=choices[0]),
        st,
        gr.update(visible=False),  # hide landing
        gr.update(visible=True),   # show game
        gr.update(value=f"### Call to AIdventure : {st['adventure'].name}")
    )

def show_intro(index, adventures):

    if index is None or index < 0:
        return "", gr.update(visible=False)
    
    return gr.update(value=adventures[index].description), gr.update(visible=True)

def start_combat(state):
    combat_log, state["current_monster"] = setup_combat(state["current_monster_name"], state["player"])
    script_dir   = Path(__file__).resolve().parent            # .../src/argents
    project_root = script_dir.parents[1]  
    
    image = Image.open(f"{project_root}/data/pictures/{state["current_monster_name"].replace(" ", "_")}.png")
    choices=[a.value for a in state["player"].actions]
    return (gr.update(visible=False), gr.update(visible=True), "\n".join(combat_log),\
        gr.update(choices=choices, value=choices[0], interactive=True, visible=True),\
        gr.update(visible=True),
        gr.update(value=f"### {state['current_monster_name']}"), image, state)

def start_player_action(state, combat_action):
    player_has_won, combat_log = player_action(PlayerAction(combat_action))
    player_has_died = False
    if not player_has_won:
        player_has_died, combat_log = monster_attack()
    
    #Neither player nor creature are dead : combat continues
    if not player_has_died and not player_has_won:
        choices=[a.value for a in state["player"].actions]
        return "\n".join(combat_log), gr.update(choices=choices, value=choices[0], interactive=True), gr.update(visible=True),\
            gr.update(visible=False), gr.update(visible=False), state
    
    else:
        if player_has_won:
            state["gold_loot"] = random.randint(*state["current_monster"].gold_loot)
            state["item_loot"] = random.choice(state["current_monster"].items_loot)
            print("LOOT = ", state["item_loot"])        
            state["player"].inventory.append(state["item_loot"])
            state["after_combat"] = True
            return "\n".join(combat_log), gr.update(visible=False), gr.update(visible=False),\
                gr.update(visible=True), gr.update(visible=False), state
        else:
            return "\n".join(combat_log), gr.update(visible=False), gr.update(visible=False),\
                gr.update(visible=False), gr.update(visible=True), state
 
    
def render_health_bar(hp_percent: int, length: int = 20, player: bool=True):
    # length = number of blocks in your bar
    filled_blocks = int(hp_percent / 100 * length)
    empty_blocks  = length - filled_blocks
    bar = "🟥" * filled_blocks + "⬛" * empty_blocks
    if player:
        return f"**Your health:** [{bar}] {int(hp_percent)}%"   
    else:
        return f"**Enemy health:** [{bar}] {int(hp_percent)}%"    

def update_health_bar(state):
    return render_health_bar((state["player"].hp/state["player"].max_hp)*100, state["player"].max_hp),\
        render_health_bar((state["current_monster"].HP/state["current_monster"].max_HP)*100, state["current_monster"].max_HP, False)

def return_to_title_screen():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(value=None),\
        gr.update(value=None, placeholder="Select an adventure to see its intro…")

def update_character_sheet(player: Player):
    inv = player.inventory if player.inventory else []
    inventory_md = "\n".join([f"- {item}" for item in inv]) if inv else "*None*"

    return f"""\
        **Name:** {player.name}  
        **Class:** {player.p_class.value}  
        **Race:** {player.race}  
        **Money:** 💰 {player.gold} gold  
        **Health:** ❤️ {player.hp}/{player.max_hp}  
        
        ---
        **Weapon:**  
        {player.weapon.name}  
        **Inventory:**  
        {inventory_md}
        """
    
def show_character_sheet(state):
    player = state["player"]
    markdown = update_character_sheet(player)
    return gr.update(value=markdown)


#region MAIN
# --- Build & Run StateGraph ---
if __name__ == "__main__":
    
    clear()
     
    adventures = load_all_adventures()
        
    pre_graph = build_pre_input_graph(StateGraph(GameState))
#     png_bytes = pre_graph.get_graph().draw_mermaid_png(
#     draw_method=MermaidDrawMethod.PYPPETEER
# )
#     # e.g. to save:
#     with open("graph_pre.png", "wb") as f:
#         f.write(png_bytes)

    post_graph = build_post_input_graph(StateGraph(GameState))
#     png_bytes = post_graph.get_graph().draw_mermaid_png(
#     draw_method=MermaidDrawMethod.PYPPETEER
# )
#     # e.g. to save:
#     with open("graph_post.png", "wb") as f:
#         f.write(png_bytes)
    
    
    # ----GRADIO-----
    with gr.Blocks(title="Call to AIdventure") as demo:
        gr.HTML("""
            <style>
            .large-text textarea {
                font-size: 20px !important;
            }
            </style>
            """)
        
        # landing page
        with gr.Column(visible=True) as landing:
            gr.Markdown("## 🎲 Welcome to AIdventure")
            adv_drop = gr.Dropdown(choices=[(a.name, i) for i, a in enumerate(adventures)], label="Choose a new adventure", value=None)
            intro_box = gr.Textbox(
            label="Adventure Intro",
            interactive=False,
            lines=5,
            placeholder="Select an adventure to see its intro…",
            elem_classes="large-text"
            )
            # save_upload= gr.File(label="—or load a saved game—")
            new_btn = gr.Button("Start New Game", visible=False)
            adv_state = gr.State(adventures)
            # load_btn   = gr.Button("Load Saved Game")

        # main game UI (hidden at first)
        with gr.Column(visible=False) as narration_screen:
            title_md    = gr.Markdown("")    # adventure title
        # now nest a Row inside this Column:
            with gr.Row():
                with gr.Column(scale=3):
                    story_box    = gr.Textbox(interactive=False, elem_classes="large-text")
                    choice_radio = gr.Radio(label="Your action")
                    submit_btn   = gr.Button("Next")
                    combat_btn   = gr.Button("It's a fight! ⚔️", visible=False)
                    state_holder = gr.State()
                with gr.Column(scale=1) as character_sheet_container:
                    gr.Markdown("### Character Sheet")
                    char_sheet = gr.Markdown("Loading...")
                    stats_panel = gr.JSON(visible=False)
        
        with gr.Column(visible=False) as combat_screen:
            title_md_combat = gr.Markdown("")
            with gr.Row():
                with gr.Column(scale=3):
                    combat_log = gr.Textbox(interactive=False, elem_classes="large-text", label="Combat Log")
                    combat_radio = gr.Radio(label="Your action")
                    player_health_md = gr.Markdown(render_health_bar(100))
                    combat_action_btn = gr.Button("Next")
                    victory_btn = gr.Button("Victory! 👑", visible=False)
                    defeat_btn = gr.Button("You died... 🪦", visible=False)
                    
                with gr.Column(scale=1):
                    monster_md = gr.Markdown("")
                    monster_image = gr.Image()
                    monster_health_md = gr.Markdown(render_health_bar(100))
                
                
         # whenever the dropdown changes, update the intro_box
        adv_drop.change(
            fn=show_intro,
            inputs=[adv_drop, adv_state],
            outputs=[intro_box, new_btn]
        )
        
        # wire up the “start” buttons
        new_btn.click(
            fn=start_callback,
            inputs=[adv_drop, adv_state, gr.State(value="new")],
            outputs=[
                story_box,
                choice_radio,
                state_holder,
                landing,
                narration_screen,
                title_md
            ]
        ).then(
             fn=show_character_sheet,
            inputs=[state_holder],
            outputs=[char_sheet]
        )

        # the in‑game “Go” button remains exactly as before
        submit = submit_btn.click(
            fn=step,
            inputs=[choice_radio, state_holder],
            outputs=[narration_screen, combat_screen, story_box, choice_radio, submit_btn, combat_btn, victory_btn, state_holder]
        )
        submit.then(
            fn=show_character_sheet,
            inputs=[state_holder],
            outputs=[char_sheet]
        )
        
        #combat start button
        combat_btn.click(
            fn=start_combat,
            inputs=[state_holder],
            outputs=[narration_screen, combat_screen, combat_log, combat_radio, combat_action_btn, monster_md, monster_image, state_holder]
        ).then(
            fn=update_health_bar,
            inputs=[state_holder],
            outputs=[player_health_md, monster_health_md]
        )
        
        #combat action selection button
        combat_action_btn.click(
            fn=start_player_action,
            inputs=[state_holder, combat_radio],
            outputs=[combat_log, combat_radio, combat_action_btn, victory_btn, defeat_btn, state_holder]
        ).then(
            fn=update_health_bar,
            inputs=[state_holder],
            outputs=[player_health_md, monster_health_md]
        )
        
         # the in‑game “Go” button remains exactly as before
        victory_btn.click(
            fn=step,
            inputs=[choice_radio, state_holder],
            outputs=[narration_screen, combat_screen, story_box, choice_radio, submit_btn, combat_btn, victory_btn, state_holder]
        ).then(
            fn=lambda st: st["player"].model_dump(),
            inputs=[state_holder],
            outputs=[stats_panel]
        )
        
        defeat_btn.click(
            fn=return_to_title_screen,
            inputs=[],
            outputs=[landing, narration_screen, combat_screen, adv_drop, intro_box]
        )
        
    demo.launch()
    
        
