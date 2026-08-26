#region IMPORTS
import re
import json

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain.agents import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from typing_extensions import TypedDict

from utils.player import Player
from utils.monster import Monster
from utils.adventure import Adventure, load_adventure

from agents.prompts import (
    build_thinker_instruction,
    build_thinker_system_message,
    build_pre_combat_fluff_prompt,
    build_post_combat_story_prompt,
    build_post_heal_story_prompt,
    build_post_damage_story_prompt,
    build_regular_story_prompt,
    build_current_room_prompt,
    build_room_completion_prompt,
    build_room_arrival_prompt,
    build_goal_evaluation_prompt,
    build_victory_wrapup_prompt,
)

from agents.llm_runtime import (
    story_chain,
    summary_chain,
    choicer_chain,
    goal_evaluator_chain,
    room_completion_chain,
    build_thinker_agent,
)
from agents.llm_resilience import invoke_llm_with_retries
from retrieval.schemas import EntityType, RagContext
from retrieval.service import (
    build_retrieval_scope,
    retrieve_location_context,
    retrieve_lore_context,
)
from retrieval.chunker import load_location
from utils.pathing import project_path
#endregion

load_dotenv()


#region CONFIG
CHAR_COL = "characters"
LOC_COL = "locations"
EMBEDDING_MODEL = "mxbai-embed-large:latest"
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
    damage_amount: int
    actual_damage_amount: int
    ongoing_goals: list[str]
    finished_goals: list[str]
    adventure_completed: bool
    end_reason: str | None
    current_location_id: str | None
    completed_location_ids: list[str]
    location_index: int
#endregion

#region RUNTIME INIT
instruction = ""
thinker_agent = None


def initialize_graph_runtime(state: GameState) -> None:
    global instruction, thinker_agent

    instruction = build_thinker_instruction(state["adventure"].monsters)

    thinker_agent = build_thinker_agent()

def prompt_fn(state: AgentState) -> list[SystemMessage | HumanMessage]:
    sys = SystemMessage(content=instruction)
    return [sys, *state["messages"]]


def parse_thinker_action(message) -> dict:
    """Normalize tool output from both Chat Completions and Responses API messages."""
    tool_calls = getattr(message, "tool_calls", None) or []
    if tool_calls:
        call = tool_calls[-1]
        name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
        args = call.get("args", {}) if isinstance(call, dict) else getattr(call, "args", {})
        if isinstance(args, str):
            args = json.loads(args)
        return {"action": name, **(args or {})}

    content = message.content
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
            else:
                text = getattr(block, "text", None)
            if text:
                text_parts.append(text)
        content = "".join(text_parts)

    if not isinstance(content, str):
        raise ValueError(f"Unsupported thinker response content: {type(content).__name__}")

    content = content.strip()
    match = re.fullmatch(r'<function=(?P<name>\w+)(?P<args>\{.*?\})</function>', content)
    if match:
        name, raw_args = match.groups()
        return {"action": name, **json.loads(raw_args)}

    payload = json.loads(content)
    if "name" in payload:
        args = payload.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        return {"action": payload["name"], **(args or {})}
    return payload
#endregion


#region UTILS
def empty_rag_context() -> str:
    return RagContext().format_for_prompt()


def retrieve_rag_context(
    state: GameState,
    query: str,
    entity_types: list[EntityType] | None = None,
    top_k: int = 5,
) -> str:
    if not state.get("adventure"):
        return empty_rag_context()

    try:
        scope = build_retrieval_scope(
            state["adventure"],
            current_location_id=state.get("current_location_id"),
        )
        context = retrieve_lore_context(
            query,
            scope,
            entity_types=entity_types,
            top_k=top_k,
        )
        return context.format_for_prompt()
    except Exception as e:
        print("ERROR RAG RETRIEVAL:", e)
        return empty_rag_context()


def retrieve_known_location_context(
    state: GameState,
    location_id: str | None,
) -> str:
    if not location_id:
        return empty_rag_context()
    if location_id not in location_order(state):
        return empty_rag_context()

    try:
        return retrieve_location_context(location_id).format_for_prompt()
    except Exception as e:
        print("ERROR LOCATION CONTEXT:", e)
        return empty_rag_context()


def make_choice(
    history: list[str],
    player_summary: str,
    previous_choices: list[str],
    rag_context: str,
) -> list[str]:
    context = "\n".join(history)
    last_choices = " - ".join(previous_choices) if previous_choices else "None"

    result = invoke_llm_with_retries(
        choicer_chain.invoke,
        {
            "context": context,
            "player_summary": player_summary,
            "last_choices": last_choices,
            "rag_context": rag_context,
        },
        call_name="choice generation",
    )

    print("DEBUG CHOICES ==", result)
    return result.choices

def compress_history(history: list[str]) -> list[str]:
    if len(history) <= 6:
        return history

    to_summarize = "\n".join(history[:-4])
    try:
        summary = invoke_llm_with_retries(
            summary_chain.invoke,
            {"context": to_summarize},
            call_name="history compression",
        ).strip()
    except Exception as e:
        print("ERROR HISTORY COMPRESSION:", e)
        return history

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

def normalize_damage_amount(amount) -> int:
    try:
        return max(0, int(amount or 0))
    except (TypeError, ValueError):
        return 0

def completed_ongoing_goals(ongoing_goals: list[str], completed_goals: list[str]) -> list[str]:
    ongoing_set = set(ongoing_goals)
    return [goal for goal in completed_goals if goal in ongoing_set]


def location_order(state: GameState) -> list[str]:
    adventure = state.get("adventure")
    if not adventure:
        return []
    return list(adventure.locations.available)


def current_location_index(state: GameState) -> int | None:
    order = location_order(state)
    if not order:
        return None

    location_id = state.get("current_location_id")
    if location_id in order:
        return order.index(location_id)

    index = state.get("location_index")
    if isinstance(index, int) and 0 <= index < len(order):
        return index

    return None


def load_location_by_id(location_id: str):
    path = project_path(f"data/world/locations/{location_id}.json")
    if not path.exists():
        return None
    return load_location(path)


def next_location_id(state: GameState) -> str | None:
    order = location_order(state)
    index = current_location_index(state)
    if index is None:
        return None

    next_index = index + 1
    if next_index >= len(order):
        return None
    return order[next_index]
#endregion


#region STEP FUNCTIONS
def step_get_input(state: GameState) -> GameState:
    if state.get("should_end"):
        return {
            "current_choices": ["Continue."],
        }

    if state.get("after_combat"):
        return {
            "current_choices": ["Go onward."],
            "after_combat": False,
        }

    try:
        rag_context = retrieve_rag_context(
            state,
            "\n".join([
                state.get("current_story", ""),
                "What can the player do next?",
            ]),
            top_k=4,
        )
        choices = make_choice(
            state["history"],
            state["player"].get_summary(),
            state.get("last_choices", []),
            rag_context,
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
    global thinker_agent

    # A saved game can be resumed after the Django process has restarted, without
    # passing through GameEngine.initialize(). Recreate the process-local agent
    # lazily in that case.
    if thinker_agent is None:
        initialize_graph_runtime(state)

    sys_msg = SystemMessage(content=build_thinker_system_message(state["adventure"].monsters))

    human_msg = HumanMessage(
        content=(
            f"Context:\n{state.get('current_story', '')}\n\n"
            f"Player input:\n{state.get('latest_user', '')}\n"
        )
    )

    resp = invoke_llm_with_retries(
        thinker_agent.invoke,
        {"messages": [sys_msg, human_msg]},
        call_name="agent thinking",
    )
    tool_msg = parse_thinker_action(resp["messages"][-1])

    action = tool_msg.get("action")
    if action == "deal_damage":
        action = "damage"
    amount = tool_msg.get("amount", 0)

    return {
        "last_cmd": "continue" if (action == "nothing" or action is None) else action,
        "current_monster_name": tool_msg.get("enemy", None),
        "heal_amount": amount if action == "heal" else 0,
        "damage_amount": amount if action == "damage" else 0,
    }

def step_prepare_combat(state: GameState) -> GameState:
    rag_context = retrieve_rag_context(
        state,
        "\n".join([
            state.get("current_story", ""),
            state.get("latest_user", ""),
            state.get("current_monster_name") or "",
        ]),
        top_k=3,
    )
    prompt = build_pre_combat_fluff_prompt(
        state["current_story"],
        state["latest_user"],
        state["current_monster_name"],
        rag_context,
    )
    fluff = invoke_llm_with_retries(
        story_chain.invoke,
        {"full_prompt": prompt},
        call_name="combat narration",
    ).strip()

    return {"combat_fluff": fluff}


def describe_current_room(state: GameState) -> str:
    rag_context = retrieve_known_location_context(
        state,
        state.get("current_location_id"),
    )
    prompt = build_current_room_prompt(
        player_summary=state["player"].get_summary(),
        current_story=state.get("current_story", ""),
        rag_context=rag_context,
    )
    return invoke_llm_with_retries(
        story_chain.invoke,
        {"full_prompt": prompt},
        call_name="current room description",
    ).strip()


def step_evaluate_room_progression(state: GameState) -> GameState:
    if state.get("should_end"):
        return {}

    location_id = state.get("current_location_id")
    if not location_id:
        return {}

    location = load_location_by_id(location_id)
    if not location or not location.completion.objective:
        return {}

    history = compress_history(state.get("history", []))
    prompt = build_room_completion_prompt(
        player_summary=state["player"].get_summary(),
        current_location_id=location_id,
        room_objective=location.completion.objective,
        room_signals=location.completion.signals,
        chat_history="\n".join(history),
        latest_user=state.get("latest_user", ""),
        current_story=state.get("current_story", ""),
    )

    try:
        result = invoke_llm_with_retries(
            room_completion_chain.invoke,
            {"full_prompt": prompt},
            call_name="room completion evaluation",
        )
    except Exception as e:
        print("ERROR ROOM EVALUATION:", e)
        return {}

    if not result.room_completed:
        return {}

    completed_location_ids = list(state.get("completed_location_ids") or [])
    if location_id not in completed_location_ids:
        completed_location_ids.append(location_id)

    next_id = next_location_id(state)
    if next_id is None:
        return {
            "completed_location_ids": completed_location_ids,
        }

    next_index = location_order(state).index(next_id)
    transition_state = {
        **state,
        "current_location_id": next_id,
        "location_index": next_index,
    }
    rag_context = retrieve_known_location_context(
        transition_state,
        next_id,
    )
    arrival_prompt = build_room_arrival_prompt(
        player_summary=state["player"].get_summary(),
        previous_story=state.get("current_story", ""),
        previous_location_id=location_id,
        next_location_id=next_id,
        rag_context=rag_context,
    )
    arrival_story = invoke_llm_with_retries(
        story_chain.invoke,
        {"full_prompt": arrival_prompt},
        call_name="room arrival narration",
    ).strip()

    return {
        "history": history + [f"Story: {arrival_story}"],
        "current_story": arrival_story,
        "current_location_id": next_id,
        "location_index": next_index,
        "completed_location_ids": completed_location_ids,
    }


def step_generate_story(state: GameState) -> GameState:
    history = compress_history(state["history"])
    player_summary = state["player"].get_summary()
    chat_hist = "\n".join(history)
    q = state["latest_user"]
    cmd = state["last_cmd"]
    rag_context = retrieve_rag_context(
        state,
        "\n".join([state.get("current_story", ""), q]),
        top_k=5,
    )
    state_updates = {
        "last_cmd": state["last_cmd"],
        "should_end": state.get("should_end", False),
        "end_reason": state.get("end_reason"),
        "heal_amount": state.get("heal_amount", 0),
        "actual_heal_amount": state.get("actual_heal_amount", 0),
        "damage_amount": state.get("damage_amount", 0),
        "actual_damage_amount": state.get("actual_damage_amount", 0),
    }

    if cmd == "combat":
        enemy = state["current_monster_name"]
        gold_loot = state["gold_loot"]
        item_loot = state["item_loot"]
        prompt = build_post_combat_story_prompt(
            player_summary=player_summary,
            chat_history=chat_hist,
            enemy=enemy,
            gold_loot=gold_loot,
            item_loot=item_loot,
            rag_context=rag_context,
        )

        state_updates.update({
            "last_cmd": "continue",
            "current_monster": None,
            "current_monster_name": None,
            "gold_loot": 0,
            "item_loot": [],
        })

    elif cmd == "heal":
        requested_heal_amount = normalize_heal_amount(state.get("heal_amount", 0))
        previous_hp = state["player"].hp
        next_hp = min(
            state["player"].max_hp,
            previous_hp + requested_heal_amount,
        )
        actual_heal_amount = next_hp - previous_hp

        prompt = build_post_heal_story_prompt(
            player_summary=player_summary,
            chat_history=chat_hist,
            latest_user=q,
            requested_heal_amount=requested_heal_amount,
            actual_heal_amount=actual_heal_amount,
            current_hp=next_hp,
            max_hp=state["player"].max_hp,
            rag_context=rag_context,
        )

        state_updates.update({
            "last_cmd": "continue",
            "heal_amount": 0,
            "actual_heal_amount": actual_heal_amount,
        })

    elif cmd == "damage":
        requested_damage_amount = normalize_damage_amount(state.get("damage_amount", 0))
        previous_hp = state["player"].hp
        next_hp = max(0, previous_hp - requested_damage_amount)
        actual_damage_amount = previous_hp - next_hp
        player_has_died = next_hp <= 0

        prompt = build_post_damage_story_prompt(
            player_summary=player_summary,
            chat_history=chat_hist,
            latest_user=q,
            requested_damage_amount=requested_damage_amount,
            actual_damage_amount=actual_damage_amount,
            current_hp=next_hp,
            max_hp=state["player"].max_hp,
            player_has_died=player_has_died,
            rag_context=rag_context,
        )

        state_updates.update({
            "last_cmd": "continue",
            "damage_amount": 0,
            "actual_damage_amount": actual_damage_amount,
            "should_end": player_has_died,
        })
        if player_has_died:
            state_updates["end_reason"] = "death"

    else:
        prompt = build_regular_story_prompt(
            player_summary=player_summary,
            chat_history=chat_hist,
            latest_user=q,
            rag_context=rag_context,
        )
    
    story = invoke_llm_with_retries(
        story_chain.invoke,
        {"full_prompt": prompt},
        call_name="story generation",
    ).strip()

    if cmd == "combat":
        state["player"].gold += gold_loot
    elif cmd == "heal":
        state["player"].hp = next_hp
    elif cmd == "damage":
        state["player"].hp = next_hp

    state.update(state_updates)

    print("Story:", story, "\n")

    return {
        "history": history + [f"You: {q}", f"Story: {story}"],
        "current_story": story,
        "story_steps": state["story_steps"] + 1,
        **state_updates,
    }

def step_evaluate_goals(state: GameState) -> GameState:
    if state.get("should_end"):
        return {}

    ongoing_goals = list(state.get("ongoing_goals") or [])
    if not ongoing_goals:
        return {
            "adventure_completed": True,
        }

    history = compress_history(state.get("history", []))
    prompt = build_goal_evaluation_prompt(
        player_summary=state["player"].get_summary(),
        chat_history="\n".join(history),
        latest_user=state.get("latest_user", ""),
        current_story=state.get("current_story", ""),
        ongoing_goals=ongoing_goals,
    )

    try:
        result = invoke_llm_with_retries(
            goal_evaluator_chain.invoke,
            {"full_prompt": prompt},
            call_name="goal evaluation",
        )
        completed_goals = completed_ongoing_goals(ongoing_goals, result.completed_goals)
    except Exception as e:
        print("ERROR GOAL EVALUATION:", e)
        completed_goals = []

    if not completed_goals:
        return {
            "ongoing_goals": ongoing_goals,
            "finished_goals": list(state.get("finished_goals") or []),
            "adventure_completed": False,
        }

    finished_goals = list(state.get("finished_goals") or [])
    for goal in completed_goals:
        if goal not in finished_goals:
            finished_goals.append(goal)

    remaining_goals = [goal for goal in ongoing_goals if goal not in completed_goals]

    return {
        "ongoing_goals": remaining_goals,
        "finished_goals": finished_goals,
        "adventure_completed": not remaining_goals,
    }

def step_generate_victory_wrapup(state: GameState) -> GameState:
    history = compress_history(state.get("history", []))
    prompt = build_victory_wrapup_prompt(
        player_summary=state["player"].get_summary(),
        chat_history="\n".join(history),
        latest_user=state.get("latest_user", ""),
        current_story=state.get("current_story", ""),
        finished_goals=list(state.get("finished_goals") or []),
    )

    story = invoke_llm_with_retries(
        story_chain.invoke,
        {"full_prompt": prompt},
        call_name="victory wrapup",
    ).strip()

    return {
        "history": history + [f"Story: {story}"],
        "current_story": story,
        "current_choices": ["Continue."],
        "should_end": True,
        "end_reason": "victory",
        "adventure_completed": True,
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
    builder.add_node("evaluate_room_progression", step_evaluate_room_progression)
    builder.add_node("evaluate_goals", step_evaluate_goals)
    builder.add_node("generate_victory_wrapup", step_generate_victory_wrapup)

    builder.add_conditional_edges(
        START,
        lambda s: s.get("last_cmd"),
        {
            "combat": "generate_story",
            "heal": "generate_story",
            "damage": "generate_story",
            "continue": "agent_think",
        }
    )

    builder.add_conditional_edges(
        "agent_think",
        lambda s: s.get("last_cmd"),
        {
            "combat": "prepare_combat",
            "heal": "generate_story",
            "damage": "generate_story",
            "continue": "generate_story",
            "end": END,
        }
    )

    builder.add_edge("prepare_combat", END)
    builder.add_edge("generate_story", "evaluate_room_progression")
    builder.add_edge("evaluate_room_progression", "evaluate_goals")
    builder.add_conditional_edges(
        "evaluate_goals",
        lambda s: "victory" if s.get("adventure_completed") and not s.get("should_end") else "continue",
        {
            "victory": "generate_victory_wrapup",
            "continue": END,
        }
    )
    builder.add_edge("generate_victory_wrapup", END)

    return builder.compile()
#endregion
