#region IMPORTS
import os
import re
import json
import random

from dotenv import load_dotenv
from typing_extensions import TypedDict

load_dotenv()

from langgraph.graph import StateGraph, START, END
from langchain.agents import AgentState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from utils.player import Player
from utils.monster import Monster
from utils.adventure import Adventure, load_adventure

from agents.tools import tools
from agents.schemas import ChoiceOutput
from agents.prompts import (
    CHOOSER_TEMPLATE,
    SUMMARY_TEMPLATE,
    build_thinker_instruction,
    build_thinker_system_message,
    build_pre_combat_fluff_prompt,
    build_post_combat_story_prompt,
    build_post_heal_story_prompt,
    build_regular_story_prompt,
)

from agents.llm_runtime import (
    story_chain,
    summary_chain,
    choicer_chain,
    build_thinker_agent,
)
#endregion


#region CONFIG
seed = random.randrange(2**32)

CHAR_COL = "characters"
LOC_COL = "locations"
EMBEDDING_MODEL = "mxbai-embed-large:latest"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL")
#endregion


#region STATE SCHEMA
class GameState(TypedDict, total=False):
    player: Player
    adventure: Adventure
    history: list[str]
    story_steps: int
    latest_user: str
    last_cmd: str
    combat_result: dict
    should_end: bool
    current_monster_name: str | None
    current_monster: Monster | None
    current_choices: list[str]
    last_choices: list[str]
    current_story: str
    combat_fluff: str
    gold_loot: int
    item_loot: list[str]
    after_combat: bool
    heal_amount: int
    actual_heal_amount: int
#endregion

#region RUNTIME INIT
def initialize_graph_runtime(state: GameState) -> None:
    global instruction, thinker_agent

    instruction = build_thinker_instruction(state["adventure"].monsters)

    thinker_agent = build_thinker_agent()

def prompt_fn(state: AgentState) -> list[SystemMessage | HumanMessage]:
    sys = SystemMessage(content=instruction)
    return [sys, *state["messages"]]
#endregion


#region UTILS
def make_choice(history: list[str], player_summary: str, previous_choices: list[str]) -> list[str]:
    context = "\n".join(history)
    last_choices = " - ".join(previous_choices) if previous_choices else "None"

    result = choicer_chain.invoke({
        "context": context,
        "player_summary": player_summary,
        "last_choices": last_choices,
    })

    print("DEBUG CHOICES ==", result)
    return result.choices

def compress_history(history: list[str]) -> list[str]:
    if len(history) <= 6:
        return history

    to_summarize = "\n".join(history[:-4])
    summary = summary_chain.invoke({"context": to_summarize}).strip()

    second_last_user = history[-4]
    second_last_story = history[-3]
    last_user = history[-2]
    last_story = history[-1]

    return [
        summary,
        second_last_story,
        second_last_user,
        last_story,
        last_user
    ]

def load_adv(id: str, print_text: bool = False):
    adv = load_adventure(id)

    with open(f"data/world/adventures/{id}/intro.txt", "r") as f:
        intro = f.read()

    if print_text:
        print(intro)

    return adv, intro

def load_adv_intro(id: str) -> str:
    with open(f"data/world/adventures/{id}/intro.txt", "r") as f:
        return f.read()

def normalize_heal_amount(amount) -> int:
    try:
        return max(0, int(amount or 0))
    except (TypeError, ValueError):
        return 0
#endregion


#region STEP FUNCTIONS
def step_get_input(state: GameState) -> GameState:
    if state.get("after_combat"):
        return {
            "current_choices": ["Go onward."],
            "after_combat": False,
        }

    try:
        choices = make_choice(
            state["history"],
            state["player"].get_summary(),
            state.get("last_choices", [])
        )
    except Exception as e:
        print("ERROR:", e)
        choices = [
            "Move forward carefully",
            "Examine the surroundings",
            "Prepare for danger",
        ]

    return {
        "current_choices": choices,
        "after_combat": False,
    }

def step_agent_think(state: GameState) -> GameState:
    sys_msg = SystemMessage(content=build_thinker_system_message(state["adventure"].monsters))

    human_msg = HumanMessage(
        content=(
            f"Context:\n{state.get('current_story', '')}\n\n"
            f"Player input:\n{state.get('latest_user', '')}\n"
        )
    )

    resp = thinker_agent.invoke({"messages": [sys_msg, human_msg]})
    content = resp["messages"][-1].content
    print("DEBUG THINKER RAW =", content)

    m = re.match(r'^<function=(?P<name>\w+)(?P<args>\{.*?\})</function>$', content)
    if not m:
        tool_msg = json.loads(content)
    else:
        name, raw_args = m.groups()
        args = json.loads(raw_args)
        tool_msg = {"action": name, **args}

    action = tool_msg.get("action")
    return {
        "last_cmd": "continue" if (action == "nothing" or action is None) else action,
        "current_monster_name": tool_msg.get("enemy", None),
        "heal_amount": tool_msg.get("amount", 0),
    }

def step_prepare_combat(state: GameState) -> GameState:
    prompt = build_pre_combat_fluff_prompt(
        state["current_story"],
        state["latest_user"],
        state["current_monster_name"],
    )
    fluff = story_chain.invoke({"full_prompt": prompt}).strip()

    return {"combat_fluff": fluff}

def step_generate_story(state: GameState) -> GameState:
    history = compress_history(state["history"])
    player_summary = state["player"].get_summary()
    chat_hist = "\n".join(history)
    q = state["latest_user"]
    cmd = state["last_cmd"]

    if cmd == "combat":
        enemy = state["current_monster_name"]
        prompt = build_post_combat_story_prompt(
            player_summary=player_summary,
            chat_history=chat_hist,
            enemy=enemy,
            gold_loot=state["gold_loot"],
            item_loot=state["item_loot"],
        )

        state["player"].gold += state["gold_loot"]
        state["last_cmd"] = "continue"
        state["current_monster"] = None
        state["current_monster_name"] = None
        state["gold_loot"] = 0
        state["item_loot"] = []

    elif cmd == "heal":
        requested_heal_amount = normalize_heal_amount(state.get("heal_amount", 0))
        previous_hp = state["player"].hp
        state["player"].hp = min(
            state["player"].max_hp,
            previous_hp + requested_heal_amount,
        )
        actual_heal_amount = state["player"].hp - previous_hp

        prompt = build_post_heal_story_prompt(
            player_summary=player_summary,
            chat_history=chat_hist,
            latest_user=q,
            requested_heal_amount=requested_heal_amount,
            actual_heal_amount=actual_heal_amount,
            current_hp=state["player"].hp,
            max_hp=state["player"].max_hp,
        )

        state["last_cmd"] = "continue"
        state["heal_amount"] = 0
        state["actual_heal_amount"] = actual_heal_amount

    else:
        prompt = build_regular_story_prompt(
            player_summary=player_summary,
            chat_history=chat_hist,
            latest_user=q,
        )
    
    story = story_chain.invoke({"full_prompt": prompt}).strip()

    print("Story:", story, "\n")

    return {
        "history": history + [f"You: {q}", f"Story: {story}"],
        "current_story": story,
        "story_steps": state["story_steps"] + 1,
        "last_cmd": state["last_cmd"],
    }
#endregion


#region GRAPH BUILDERS
def build_pre_input_graph(builder: StateGraph):
    builder.add_node("get_input", step_get_input)
    builder.add_edge(START, "get_input")
    builder.add_edge("get_input", END)
    return builder.compile()

def build_post_input_graph(builder: StateGraph):
    builder.add_node("agent_think", step_agent_think)
    builder.add_node("prepare_combat", step_prepare_combat)
    builder.add_node("generate_story", step_generate_story)

    builder.add_conditional_edges(
        START,
        lambda s: s.get("last_cmd"),
        {
            "combat": "generate_story",
            "heal": "generate_story",
            "continue": "agent_think",
        }
    )

    builder.add_conditional_edges(
        "agent_think",
        lambda s: s.get("last_cmd"),
        {
            "combat": "prepare_combat",
            "heal": "generate_story",
            "continue": "generate_story",
            "end": END,
        }
    )

    builder.add_edge("prepare_combat", END)
    builder.add_edge("generate_story", END)

    return builder.compile()
#endregion
