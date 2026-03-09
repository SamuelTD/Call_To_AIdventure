from langgraph.graph import StateGraph

from agents.game_master_graph import (
    GameState,
    build_pre_input_graph,
    build_post_input_graph,
)

class GameEngine:

    def __init__(self):
        self.pre_graph = build_pre_input_graph(StateGraph(GameState))
        self.post_graph = build_post_input_graph(StateGraph(GameState))

    def initialize(self, state):
        """
        Equivalent of the old init() Gradio logic.
        """
        ctx = self.pre_graph.invoke(input=state)
        state["current_choices"] = ctx["current_choices"]
        return state

    def step(self, state, choice):
        """
        Equivalent of the old step() function.
        """
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
      
      
# SINGLETON PATTERN  
_engine = None

def get_engine():
    global _engine

    if _engine is None:
        _engine = GameEngine()

    return _engine