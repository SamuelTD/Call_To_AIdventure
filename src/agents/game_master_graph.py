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
from langgraph.prebuilt import create_react_agent
from langchain.agents import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.llm import LLMChain
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt.chat_agent_executor import AgentState

from utils.python_utils import clear
from utils.player import Player, save_player, load_player
from utils.adventure import Adventure, load_adventure, load_all_adventures
from combat.core import run_combat

import gradio as gr
from functools import partial

import random


#region CONFIG
seed=random.randrange(2**32)

# --- Configuration constants ---
CHAR_COL = "characters"
LOC_COL = "locations"
EMBEDDING_MODEL = "mxbai-embed-large:latest"
LLM_MODEL = "llama3.2:latest"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
    current_enemy: str
    current_choices: list[str]
    current_story: str
    combat_fluff: str

# --- Embeddings & Vector Stores ---
ollama_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
vectorstore_char = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=CHAR_COL,
    embedding_function=ollama_embeddings
)
vectorstore_loc = Chroma(
    client=chromadb.PersistentClient(path="db/chroma"),
    collection_name=LOC_COL,
    embedding_function=ollama_embeddings
)

# region TOOLS
# --- Tool definitions ---
def combat_tool(enemy: str) -> dict:
    return {"action": "combat", "enemy": enemy}

def nothing_tool(_: str) -> dict:
    return {"action": "continue"}

tools = [
    Tool(name="combat", func=combat_tool, description="When the player is facing a monster, start combat against that monster ; arg monster name", return_direct=True),
    Tool(name="nothing", func=nothing_tool, description="Return nothing, do nothing.", return_direct=True),
]


#region LLM AND AGENTS
llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.5, model_kwargs={"seed": seed})


template = ChatPromptTemplate.from_template("{full_prompt}")
story_chain = LLMChain(llm=llm, prompt=template)

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

summary_chain = LLMChain(llm=llm, prompt=summary_template)

choicer_template = ChatPromptTemplate.from_template(
    "You are role player in an adventure." 
    "Here is the current state of your character :"
    "{player_summary}"
    "Your role is to determine which next courses of action are aceptable based on your character and the current context :"
    "{context}"
    "You will ONLY output EXACTLY three (3) actions using the following schema :"
    "[action1, action2, action3]"
    "Each action is at maximum 6 words long."
    "You will refrain from giving actions that are similar to each other."
)
choicer_chain = LLMChain(llm=llm, prompt=choicer_template)

# region UTILS

def make_choice(history: list[str], player_summary: str) -> str:
    context = "\n".join(history)
    
    choices = choicer_chain.predict(context=context, player_summary=player_summary).strip()
    return choices

def compress_history(history: list[str]) -> list[str]:
    # Only summarize when there are more than 4 entries
    if len(history) <= 6:
        return history

    # 2) Extract the part to summarize
    to_summarize = "\n".join(history[:-4])

    # 3) Get the summary
    summary = summary_chain.predict(context=to_summarize).strip()

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

def character_creation() -> Player:
    clear()
    print("=== Character Creation ===")
    name = input("Name: ")
    cls = input("Class: ")
    race = input("Race: ")
    gender = input("Gender: ")
    gold = int(input("Starting gold: "))
    player = Player(name=name, p_class=cls, race=race, gold=gold, gender=gender)
    save_player(player)
    clear()
    return player

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
    if state["story_steps"] > -1:        
        try:
            choices = [item.strip() for item in make_choice(state["history"], state["player"].get_summary()).strip("[]").split(", ")]
            
        except:    
            choices = ["DEBUG == COULDNT PARSE CHOICER LIST."]  
            

    return {"current_choices": choices}


def step_agent_think(state: GameState) -> GameState:
    # hist = f"Context: {state["current_story"]}\n Player action: {state['latest_user']}"
    
    messages = [
    SystemMessage(content=f"Context: {state['current_story']}"),
    HumanMessage(content=state['latest_user']),
    ]
    
    resp = thinker_agent.invoke({"messages": messages})
    content = resp["messages"][-1].content
    # print(resp)
    # print("DEBUG ========== ", content)
    m = re.match(r'^<function=(?P<name>\w+)(?P<args>\{.*?\})</function>$', content)
    # print("DEBUG M ========= ", m)
    if not m:
        tool_msg=json.loads(content)
    else:
        name, raw_args = m.groups()
        args = json.loads(raw_args)
        tool_msg = {"action": name, **args}        
        # return {"last_cmd": "end", "current_enemy": tool_msg.get("enemy", None)}
        
    # print("DEBUG ================== ", tool_msg)
    action = tool_msg.get("action")
    return {"last_cmd": "continue" if action == "nothing" else action, "current_enemy": tool_msg.get("enemy", None)}


def step_prepare_combat(state: GameState) -> GameState:
    prompt = f"""
    You are a game master for a fantasy role playing game. Your role is to write short (2-3 sentences maximum) 
    descriptive scenes that will precede a combat. 
    You base your narration on the following context and player input.
    Context: {state["current_story"]}
    Player input: {state["latest_user"]}
    The enemy the player is about to combat is {state["current_enemy"]}.
    """
    fluff = story_chain.predict(full_prompt=prompt)
    
    # result = run_combat(state["current_enemy"], state["player"])
    # if type(result) == str: #Enemy not found in the DB.
    #     print(result)
    #     return
    # if result.get("signal") == 2:
    #     print(result.get("message", "You have fallen."))
    return {"combat_fluff": fluff}

def step_generate_story(state: GameState) -> GameState:
    
    state["history"] = compress_history(state["history"])
    
    player_summary = state["player"].get_summary()
    chat_hist = "\n".join(state["history"])
    q = state["latest_user"]
    cmd = state["last_cmd"]
    
    if cmd == "combat":
        enemy = state["current_enemy"]
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
                    """
    else:
        prompt = f"""
                Here are the informations on the user :
                {player_summary}
                
                Here is the adventure so far:
                {chat_hist}

                You are the Game Master for a narrative adventure game. You take the user input and continue the story\
                    based on the events so far and the user input. You use a refined, fantasy inspired tone to craft the story.\
                        You write in the second person.\
                            Limit each of your answer to four sentences maximum.

                User input: {q}
                """
    story = story_chain.predict(full_prompt=prompt)
    print("Story:", story, "\n")
    return {"history": state["history"] + [f"You: {q}", f"Story: {story}"], "current_story": story, "story_steps": state["story_steps"] + 1}


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
    
    
    builder.add_edge(START, "agent_think")
    
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

def init(index, adventure):
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
        "current_story": intro
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
    
    thinker_agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=prompt_fn
    )
    
    ctx = pre_graph.invoke(input=state)
    state["current_choices"] = ctx["current_choices"]
    return state
    # return state["current_story"], gr.update(choices=choices, value=None), state

def step(choice, state):
    # 1) drive the “post” graph to update your world‐state
    state = post_graph.invoke(input={**state, "latest_user": choice})
    if state["last_cmd"] == "combat":
        
        return state["combat_fluff"], gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), state
    
    # 2) immediately re‐run the “pre” graph on that new state
    ctx = pre_graph.invoke(input=state)
    # 3) extract narrative + next‐choices
    story = ctx["current_story"]
    choices = ctx["current_choices"]
    # choices = ["I attack the Zombie, starting a combat."]
    return story, gr.update(choices=choices, value=None, visible=True), gr.update(visible=True), gr.update(visible=False), state

def init_load(file_obj):
    # saved_state = load_state_from_file(file_obj.name)
    # return init(saved_state)
    return None

def start_callback(index, adventures, mode):
    if mode == "new":
        st = init(index, adventures)
    else:
        pass
        # story, choices, st = init_load(file_obj)
    story = st["current_story"]
    choices = st["current_choices"]
    return (
        story,
        gr.update(choices=choices, value=None),
        st,
        gr.update(visible=False),  # hide landing
        gr.update(visible=True),   # show game
        gr.update(value=f"### Call to AIdventure : {st['adventure'].name}")
    )

def show_intro(index, adventures):
    print(index)
    print(adventures)
    if index < 0 or index == None:
        print("debug : inside the not index")
        return ""
    # adventures_list is your original Python list
    return gr.update(value=adventures[index].description)

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
    with gr.Blocks() as demo:
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
            new_btn = gr.Button("Start New Game")
            adv_state = gr.State(adventures)
            # load_btn   = gr.Button("Load Saved Game")

        # main game UI (hidden at first)
        with gr.Column(visible=False) as game:
            title_md    = gr.Markdown("")    # adventure title
        # now nest a Row inside this Column:
            with gr.Row():
                with gr.Column(scale=3):
                    story_box    = gr.Textbox(interactive=False, elem_classes="large-text")
                    choice_radio = gr.Radio(label="Your action")
                    submit_btn   = gr.Button("Next")
                    combat_btn   = gr.Button("It's a fight! ⚔️", visible=False)
                    state_holder = gr.State()
                with gr.Column(scale=1):
                    gr.Markdown("### Character Sheet")
                    stats_panel = gr.JSON()

         # whenever the dropdown changes, update the intro_box
        adv_drop.change(
            fn=show_intro,
            inputs=[adv_drop, adv_state],
            outputs=[intro_box]
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
                game,
                title_md
            ]
        ).then(
            # once state_holder is set, show the character sheet
            fn=lambda st: st["player"].model_dump(),
            inputs=[state_holder],
            outputs=[stats_panel]
        )

        # the in‑game “Go” button remains exactly as before
        submit = submit_btn.click(
            fn=step,
            inputs=[choice_radio, state_holder],
            outputs=[story_box, choice_radio, submit_btn, combat_btn, state_holder]
        )
        submit.then(
            fn=lambda st: st["player"].model_dump(),
            inputs=[state_holder],
            outputs=[stats_panel]
        )

    demo.launch()
    
        
