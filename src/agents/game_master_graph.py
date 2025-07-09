# -*- coding: utf-8 -*-
"""
A LangGraph-based refactoring of the Call to AIdventure narrative game.
"""
import os
import json
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

from utils.python_utils import clear
from utils.player import Player, save_player, load_player
from combat.core import run_combat
import random
from time import sleep

# --- Configuration constants ---
CHAR_COL = "characters"
LOC_COL = "locations"
EMBEDDING_MODEL = "mxbai-embed-large:latest"
LLM_MODEL = "llama3.2:latest"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Define Graph State Schema ---
class GameState(TypedDict, total=False):
    player: Player
    history: list[str]
    story_steps: int
    latest_user: str
    last_cmd: dict
    combat_result: dict
    should_end: bool
    current_enemy: str

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
    Tool(name="combat", func=combat_tool, description="Start combat against enemy ; arg enemy name", return_direct=True),
    Tool(name="nothing", func=nothing_tool, description="Continue narrative without combat.", return_direct=True),
]


#region LLM AND AGENTS
llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-maverick-17b-128e-instruct")

# --- Agent & Story Chain Setup ---
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="You are the assistant to a fantasy Game Master. \
        You decide which way the game goes next based on the tools you have and the user input."
)

template = ChatPromptTemplate.from_template("{full_prompt}")
story_chain = LLMChain(llm=llm, prompt=template)

summary_template = ChatPromptTemplate.from_template(
    "You are a concise summarizer for fantasy narrative. You write in the past tense, in the third person and replace the 2nd person by \"the player\"."
    "Condense the following narrative context into a single paragraph starting with \"Summary of the story :\":\n\n"
    "{context}"
)

summary_chain = LLMChain(llm=llm, prompt=summary_template)

choicer_template = ChatPromptTemplate.from_template(
    "You are role player in an adventure. Your role is to determine which next courses of action are aceptable based on the current context :"
    "{context}"
    "You will ONLY output 3 actions using the following schema :"
    "[action1, action2, action3]"
    "Each action is a single, first person sentence describing the chosen action."
)
choicer_chain = LLMChain(llm=llm, prompt=choicer_template)

# region UTILS

def make_choice(history: list[str]) -> str:
    context = "\n".join(history)
    
    choices = choicer_chain.predict(context=context).strip()
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

def load_intro() -> str:
    clear()
    with open("data/documents/intro.txt", "r") as f:
        intro = f.read()
    print(intro)
    return intro


# region STEPS
# --- Step Implementations ---

def step_get_input(state: GameState) -> GameState:
    if state["story_steps"] > -1:        
        try:
            choices = [item.strip() for item in make_choice(state["history"]).strip("[]").split(", ")]
            q = choices[random.randint(0, len(choices)-1)]
            print(f"You: {q}")
            sleep(2)
        except:    
            print("DEBUG == COULDNT PARSE CHOICER LIST.")    
            q = input("You: ")
            if q.strip().lower() == "exit":
                return {"should_end": True}
            
    return {"latest_user": q}


def step_agent_think(state: GameState) -> GameState:
    hist = "\n".join(state["history"] + [f"Player: {state['latest_user']}"])
    resp = agent.invoke({"messages": [{"role": "user", "content": hist}]})
    print("DEBUG ========== ", resp["messages"][-1].content)
    tool_msg=json.loads(resp["messages"][-1].content)
    print("DEBUG ========== ", tool_msg)
    return {"last_cmd": tool_msg.get("action"), "current_enemy": tool_msg.get("enemy", None)}


def step_run_combat(state: GameState) -> GameState:
    result = run_combat(state["current_enemy"], state["player"])
    if type(result) == str:
        print(result)
        return
    if result.get("signal") == 2:
        print(result.get("message", "You have fallen."))
    return {"combat_result": result}

def choose_entry(state: GameState) -> str:
    # On the very first run, you won't have init_done set → load the intro
    if not state.get("init_done", False):
        return "load_intro"
    # Once you've done that step, always go straight to get_input
    return "get_input"

def step_generate_story(state: GameState) -> GameState:
    
    state["history"] = compress_history(state["history"])
    
    p = state["player"]
    player_summary = f"Name: {p.name} - Race: {p.race} - Class: {p.p_class} - Gold: {p.gold}"
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

                    You are the Game Master for a narrative adventure game. You take the user input and continue the story\
                        based on the events so far and the user input. You use a refined, fantasy inspired tone to craft the story.\
                            You write in the second person and conclude every message by "Now, what do you do?".\
                                Limit each of your answer to six sentences maximum. The user juste vanquished {enemy}.\
                                    Start your output by "You vanquished {enemy}" and go from there.

                    User input: {q}
                    """
    else:
        prompt = f"""
                Here are the informations on the user :
                {player_summary}
                
                Here is the adventure so far:
                {chat_hist}

                You are the Game Master for a narrative adventure game. You take the user input and continue the story\
                    based on the events so far and the user input. You use a refined, fantasy inspired tone to craft the story.\
                        You write in the second person and conclude every message by "Now, what do you do?".\
                            Limit each of your answer to four sentences maximum.

                User input: {q}
                """
    story = story_chain.predict(full_prompt=prompt)
    print("Story:", story, "\n")
    return {"history": state["history"] + [f"You: {q}", f"Story: {story}"], "story_steps": state["story_steps"] + 1}


def step_end(state: GameState) -> GameState:
    if state["combat_result"]["signal"] != 2:        
        print("Farewell, adventurer.")
    return {}

def build_graph(builder): 
    
     # Nodes

    builder.add_node("get_input", step_get_input)
    builder.add_node("agent_think", step_agent_think)
    builder.add_node("run_combat", step_run_combat)
    builder.add_node("generate_story", step_generate_story)
    builder.add_node("end", step_end)

    # Edges
   
    builder.add_edge(START, "get_input")
    # Conditional routing after user input
    builder.add_conditional_edges(
        "get_input",
        lambda s: s.get("should_end", False),
        {True: "end", False: "agent_think"}
    )
    # Conditional routing after agent thinking
    builder.add_conditional_edges(
        "agent_think",
        lambda s: s.get("last_cmd"),
        {"combat": "run_combat", "continue": "generate_story"}
    )
    # Conditional routing after combat
    builder.add_conditional_edges(
        "run_combat",
        lambda s: s["combat_result"]["signal"] == 2,
        {True: "end", False: "generate_story"}
    )
    # Loop back for story generation
    builder.add_edge("generate_story", "get_input")
    builder.add_edge("end", END)

    graph = builder.compile()

    return graph

# --- Build & Run StateGraph ---
if __name__ == "__main__":
    
    player = load_player()
    intro = load_intro()
        
    graph = build_graph(StateGraph(GameState))
    
    state: GameState = {
        "player": player,
        "history": [intro],
        "story_steps": 0,
        "should_end": False,
        "combat_result": {"signal": 0, "message": ""}
    }
    
    while True:

        ctx = graph.invoke(input=state)
        state = ctx
        
