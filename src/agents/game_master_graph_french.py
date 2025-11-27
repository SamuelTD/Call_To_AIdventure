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
from utils.monster import Monster
from utils.adventure import Adventure, load_adventure, load_all_adventures
from utils.enums import PlayerAction
from combat.core import setup_combat, player_action, monster_attack

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
    current_story: str
    combat_fluff: str
    gold_loot: int
    item_loot: list[str]
    after_combat: bool

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
llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.5, model_kwargs={"seed": seed})



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
    """Tu es un résumeur concis de récits fantasy. Tu écris au passé, à la troisième personne, et tu remplaces la deuxième personne par « le joueur ».
    Condense le contexte narratif suivant en un seul paragraphe commençant par « Résumé de l’histoire : » :
    {context}"""
    )

summary_chain = LLMChain(llm=llm, prompt=summary_template)

choicer_template = ChatPromptTemplate.from_template(
    """Tu es un personnage-joueur dans une aventure.
    Voici l’état actuel de ton personnage :
    {player_summary}
    Ton rôle est de déterminer quelles actions sont acceptables en fonction de ton personnage et du contexte suivant :
    {context}
    Tu dois UNIQUEMENT proposer EXACTEMENT trois (3) actions en utilisant le format suivant :
    [action1, action2, action3]
    Chaque action doit comporter au maximum 6 mots.
    Tu éviteras de proposer des actions similaires entre elles.
    Tu ne peux lancer des sorts que si ta classe est « wizard ».
    Une action peut être une phrase (par exemple : « Je m'appelle... » ou « Je cherche... ») si un autre personnage dans la scène s'adresse à toi."""
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
        choices = ["Continuer."]
        state["after_combat"] = False
    else:
        if state["story_steps"] > -1:        
            try:
                choices = [item.strip() for item in make_choice(state["current_story"], state["player"].get_summary()).strip("[]").split(", ")]
                
            except:    
                choices = ["DEBUG == COULDNT PARSE CHOICER LIST."]  
            

    return {"current_choices": choices, "after_combat": False}


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
        # return {"last_cmd": "end", "current_monster_name": tool_msg.get("enemy", None)}
        
    # print("DEBUG ================== ", tool_msg)
    action = tool_msg.get("action")
    return {"last_cmd": "continue" if (action == "nothing" or action is None) else action, "current_monster_name": tool_msg.get("enemy", None)}


def step_prepare_combat(state: GameState) -> GameState:
    prompt = f"""
    Tu es un maître de jeu pour un jeu de rôle fantasy. Ton rôle est d’écrire de courtes scènes descriptives (2 à 3 phrases maximum) qui précèdent un combat.
    Tu bases ta narration sur le contexte suivant et sur l’action du joueur.
    Contexte : {state["current_story"]}
    Action du joueur : {state["latest_user"]}
    L’ennemi que le joueur s’apprête à affronter est : {state["current_monster_name"]}.
    """
    fluff = story_chain.predict(full_prompt=prompt)
    
    # result = run_combat(state["current_monster_name"], state["player"])
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
        enemy = state["current_monster_name"]
        prompt = f"""
                    Voici les informations sur le joueur :
                    {player_summary}

                    Voici le résumé de l’aventure jusqu’à présent :
                    {chat_hist}

                    Tu es le Maître du Jeu d’une aventure narrative. Tu dois poursuivre l’histoire en t’appuyant sur les événements précédents.
                    Tu utilises un ton raffiné, inspiré de la fantasy, pour raconter l’histoire.
                    Tu écris à la deuxième personne du singulier.
                    Limite ta réponse à un maximum de quatre phrases. Le joueur vient de vaincre et de tuer {enemy}.
                    Commence ta narration par « Tu as vaincu {enemy} », en partant du principe que {enemy} est mort.
                    Sur le cadavre, le joueur a trouvé {state["gold_loot"]} pièces d’or et {state["item_loot"]} comme butin. Intègre ces éléments dans ton récit.
                    """
        state["player"].gold += state["gold_loot"]
        state["last_cmd"] = "continue"
    else:
        prompt = f"""
                Voici les informations sur le joueur :
                {player_summary}

                Voici le résumé de l’aventure jusqu’à présent :
                {chat_hist}

                Tu es le Maître du Jeu d’un jeu d’aventure narrative. Tu prends en compte l’action du joueur et poursuis l’histoire en fonction des événements précédents et de son choix.
                Tu utilises un ton raffiné, inspiré de la fantasy, pour raconter l’histoire.
                Tu écris à la deuxième personne du singulier.
                Limite ta réponse à un maximum de quatre phrases. Tu fais progresser l’histoire sans précipitation.
                Tu peux — et tu dois — infliger de mauvaises conséquences au joueur si cela a du sens dans le récit.

                Action du joueur : {q}
                """
    story = story_chain.predict(full_prompt=prompt)
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
        "current_story": intro,
        "last_cmd": "continue",
        "after_combat": False
    }
    
    instruction = (
   f"""Tu es l’assistant d’un Maître du Jeu fantasy.
    Tu disposes exactement de deux outils :
    • combat(enemy: str) — commence un combat contre ce monstre
    • nothing(_) — continue l’histoire sans combat

    Tu dois répondre avec un UNIQUE objet JSON appelant l’un de ces outils — aucun texte supplémentaire.

    Tu peux également déduire à partir de la description du joueur si un des monstres connus est présent — même s’il n’est pas nommé explicitement.
    Si le joueur dit « Frapper », « Attaquer », « Trancher » ou montre une intention de combat contre une créature de ta liste, appelle combat() avec le nom exact de ce monstre.

    Monstres disponibles dans cette aventure : {" - ".join(state["adventure"].monsters)}"""
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
        print("DEBUG : STATE = combat")  
        return gr.update(visible=True), gr.update(visible=False), state["combat_fluff"], gr.update(visible=False), gr.update(visible=False),\
            gr.update(visible=True),  gr.update(visible=False), state
    
    # 2) immediately re‐run the “pre” graph on that new state
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
        st = init(index, adventures)
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
        return f"**Votre santé :** [{bar}] {int(hp_percent)}%"   
    else:
        return f"**Santé de l'adversaire :** [{bar}] {int(hp_percent)}%"    

def update_health_bar(state):
    return render_health_bar((state["player"].hp/state["player"].max_hp)*100, state["player"].max_hp),\
        render_health_bar((state["current_monster"].HP/state["current_monster"].max_HP)*100, state["current_monster"].max_HP, False)

def return_to_title_screen():
    return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(value=None),\
        gr.update(value=None, placeholder="Sélectionnez une aventure pour en voir le synopsis…")

def update_character_sheet(player: Player):
    inv = player.inventory if player.inventory else []
    inventory_md = "\n".join([f"- {item}" for item in inv]) if inv else "*None*"

    return f"""\
        **Nom:** {player.name}  
        **Classe:** {player.p_class.value}  
        **Race:** {player.race}  
        **Richesse:** 💰 {player.gold} or  
        **Santé:** ❤️ {player.hp}/{player.max_hp}  
        
        ---
        **Arme:**  
        {player.weapon.name}  
        **Inventaire:**  
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
            gr.Markdown("## 🎲 Bienvenue dans l'AIdventure")
            adv_drop = gr.Dropdown(choices=[(a.name, i) for i, a in enumerate(adventures)], label="Choisissez une nouvelle aventure", value=None)
            intro_box = gr.Textbox(
            label="Synopsis de l'aventure",
            interactive=False,
            lines=5,
            placeholder="Sélectionnez une aventure pour en voir le synopsis…",
            elem_classes="large-text"
            )
            # save_upload= gr.File(label="—or load a saved game—")
            new_btn = gr.Button("Commencer la partie", visible=False)
            adv_state = gr.State(adventures)
            # load_btn   = gr.Button("Load Saved Game")

        # main game UI (hidden at first)
        with gr.Column(visible=False) as narration_screen:
            title_md    = gr.Markdown("")    # adventure title
        # now nest a Row inside this Column:
            with gr.Row():
                with gr.Column(scale=3):
                    story_box    = gr.Textbox(interactive=False, elem_classes="large-text")
                    choice_radio = gr.Radio(label="Votre action")
                    submit_btn   = gr.Button("Suivant")
                    combat_btn   = gr.Button("Combattez ! ⚔️", visible=False)
                    state_holder = gr.State()
                with gr.Column(scale=1) as character_sheet_container:
                    gr.Markdown("### Fiche de personnage")
                    char_sheet = gr.Markdown("Chargement...")
                    stats_panel = gr.JSON(visible=False)
        
        with gr.Column(visible=False) as combat_screen:
            title_md_combat = gr.Markdown("")
            with gr.Row():
                with gr.Column(scale=3):
                    combat_log = gr.Textbox(interactive=False, elem_classes="large-text", label="Journal de combat")
                    combat_radio = gr.Radio(label="Votre action")
                    player_health_md = gr.Markdown(render_health_bar(100))
                    combat_action_btn = gr.Button("Suivant")
                    victory_btn = gr.Button("Victoire ! 👑", visible=False)
                    defeat_btn = gr.Button("Vous avez péri... 🪦", visible=False)
                    
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
    
        
