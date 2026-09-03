from langgraph.graph import StateGraph
import random
from combat.core import (
    restore_combat_session,
    resolve_monster_attack,
    resolve_player_action,
    setup_combat_session,
)
from utils.enums import PlayerAction
from agents.game_master_graph import (
    GameState,
    build_pre_input_graph,
    build_post_input_graph,
    initialize_graph_runtime,
    describe_current_room,
)
from agents.llm_resilience import TemporaryLLMServiceError

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
            mode = "adventure_victory" if state.get("end_reason") == "victory" else "gameover"
            return {
                "state": state,
                "mode": mode,
            }

        try:
            state = self.post_graph.invoke(
                input={**state, "latest_user": choice}
            )
        except TemporaryLLMServiceError:
            return {
                "state": state,
                "mode": "service_unavailable",
            }

        # combat trigger
        if state["last_cmd"] == "combat":
            return {
                "state": state,
                "mode": "combat",
                "combat_fluff": state["combat_fluff"],
            }

        # run pre graph again
        state["last_choices"] = state["current_choices"]
        try:
            state = self.pre_graph.invoke(input=state)
        except TemporaryLLMServiceError:
            return {
                "state": state,
                "mode": "service_unavailable",
            }

        return {
            "state": state,
            "mode": "story",
            "story": state["current_story"],
            "choices": state["current_choices"],
        }

    def check_current_room(self, state):
        try:
            room_description = describe_current_room(state)
        except TemporaryLLMServiceError:
            return {
                "state": state,
                "mode": "service_unavailable",
            }

        state["current_story"] = room_description
        return {
            "state": state,
            "mode": "story",
            "story": room_description,
            "choices": state.get("current_choices", []),
        }
    
    def start_combat(self, state):
        if not state.get("current_monster_name"):
            return {
                "state": state,
                "mode": "error",
                "error": "No pending combat",
            }

        if state.get("current_monster") is not None:
            session = restore_combat_session(state["player"], state["current_monster"])
            payload = self._build_combat_payload(state)
            payload["combat_log"] = "\n".join(session.log) or "Combat already underway."
            return {
                "state": state,
                "mode": "combat",
                **payload,
            }

        combat_log, combat_session = setup_combat_session(
            state["current_monster_name"],
            state["player"]
        )
        state["current_monster"] = combat_session.monster if combat_session else None
        if state["current_monster"] is None:
            return {
                "state": state,
                "mode": "error",
                "error": "Monster not found",
            }
        
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

        try:
            action = PlayerAction(combat_action_value)
        except ValueError:
            return {
                "state": state,
                "mode": "error",
                "error": "Invalid combat action",
            }

        combat_session = restore_combat_session(state["player"], state["current_monster"])
        player_has_won, combat_log = resolve_player_action(combat_session, action)
        player_has_died = False

        if not player_has_won:
            player_has_died, combat_log = resolve_monster_attack(combat_session)

        state["player"] = combat_session.player
        state["current_monster"] = combat_session.monster
        
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
