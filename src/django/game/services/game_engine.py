from langgraph.graph import StateGraph
import random
from combat.core import (
    setup_combat,
    restore_combat,
    player_action,
    monster_attack,
    get_current_combat_state,
)
from utils.enums import PlayerAction
from agents.game_master_graph import (
    GameState,
    build_pre_input_graph,
    build_post_input_graph,
    initialize_graph_runtime
)
from langchain.agents import create_agent
from agents.game_master_graph import tools
from agents.llm_runtime import llm

class GameEngine:

    def __init__(self):
        self.pre_graph = build_pre_input_graph(StateGraph(GameState))
        self.post_graph = build_post_input_graph(StateGraph(GameState))

    def initialize(self, state):
        
        initialize_graph_runtime(state)
        ctx = self.pre_graph.invoke(input=state)
        state["current_choices"] = ctx["current_choices"]

        return state

    def step(self, state, choice):
        """
        Equivalent of the old step() function.
        """
        if state.get("should_end"):
            return {
                "state": state,
                "mode": "gameover",
            }

        state = self.post_graph.invoke(
            input={**state, "latest_user": choice}
        )

        # combat trigger
        if state["last_cmd"] == "combat":
            return {
                "state": state,
                "mode": "combat",
                "combat_fluff": state["combat_fluff"],
            }

        # run pre graph again
        state["last_choices"] = state["current_choices"]
        state = self.pre_graph.invoke(input=state)

        return {
            "state": state,
            "mode": "story",
            "story": state["current_story"],
            "choices": state["current_choices"],
        }
    
    def start_combat(self, state):
        if not state.get("current_monster_name"):
            return {
                "state": state,
                "mode": "error",
                "error": "No pending combat",
            }

        if state.get("current_monster") is not None:
            restore_combat(state["player"], state["current_monster"])
            payload = self._build_combat_payload(state)
            payload["combat_log"] = payload["combat_log"] or "Combat already underway."
            return {
                "state": state,
                "mode": "combat",
                **payload,
            }

        combat_log, state["current_monster"] = setup_combat(
            state["current_monster_name"],
            state["player"]
        )
        if state["current_monster"] is None:
            return {
                "state": state,
                "mode": "error",
                "error": "Monster not found",
            }

        combat_state = get_current_combat_state()
        if combat_state.get("player") is not None:
            state["player"] = combat_state["player"]
        if combat_state.get("monster") is not None:
            state["current_monster"] = combat_state["monster"]
        
        payload = self._build_combat_payload(state, combat_log)

        return {
            "state": state,
            "mode": "combat",
            **payload,
        }

    def combat_action(self, state, combat_action_value):
        if state.get("current_monster") is None:
            return {
                "state": state,
                "mode": "error",
                "error": "No active combat",
            }

        restore_combat(state["player"], state["current_monster"])
        try:
            action = PlayerAction(combat_action_value)
        except ValueError:
            return {
                "state": state,
                "mode": "error",
                "error": "Invalid combat action",
            }

        player_has_won, combat_log = player_action(action)
        player_has_died = False

        if not player_has_won:
            player_has_died, combat_log = monster_attack()

        combat_state = get_current_combat_state()
        if combat_state.get("player") is not None:
            state["player"] = combat_state["player"]
        if combat_state.get("monster") is not None:
            state["current_monster"] = combat_state["monster"]
        
        if not player_has_died and not player_has_won:
            payload = self._build_combat_payload(state, combat_log)
            return {
                "state": state,
                "mode": "combat",
                **payload,
            }

        if player_has_won:
            state["gold_loot"] = random.randint(*state["current_monster"].gold_loot)
            state["item_loot"] = random.choice(state["current_monster"].items_loot)
            state["player"].inventory.append(state["item_loot"])
            state["after_combat"] = True

            payload = self._build_combat_payload(state, combat_log)
            return {
                "state": state,
                "mode": "victory",
                **payload,
            }

        payload = self._build_combat_payload(state, combat_log)
        return {
            "state": state,
            "mode": "defeat",
            **payload,
        }
        
    def _build_combat_payload(self, state, combat_log=None):
        monster = state.get("current_monster")
        player = state.get("player")

        return {
            "combat_log": "\n".join(combat_log) if isinstance(combat_log, list) else (combat_log or ""),
            "monster_name": state.get("current_monster_name"),
            "player_hp": player.hp if player else None,
            "player_max_hp": player.max_hp if player else None,
            "monster_hp": monster.HP if monster else None,
            "monster_max_hp": monster.max_HP if monster else None,
            "choices": [a.value for a in player.actions] if player else [],
        }
        

# SINGLETON PATTERN  
_engine = None

def get_engine():
    global _engine

    if _engine is None:
        _engine = GameEngine()

    return _engine
