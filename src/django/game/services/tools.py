from uuid import uuid4
from game.models import SaveGame
from utils.player import Player, load_player
from utils.adventure import Adventure, load_all_adventures, load_adv_intro
from utils.monster import Monster

def make_serializable_state(state: dict) -> dict:
    safe = state.copy()

    if safe.get("player"):
        safe["player"] = safe["player"].to_dict()

    if safe.get("adventure"):
        safe["adventure"] = safe["adventure"].to_dict()

    if safe.get("current_monster"):
        safe["current_monster"] = safe["current_monster"].to_dict()

    return safe

def rebuild_state(serialized_state: dict) -> dict:

    state = serialized_state.copy()

    if state.get("player"):
        state["player"] = Player.from_dict(state["player"])

    if state.get("adventure"):
        state["adventure"] = Adventure.from_dict(state["adventure"])

    if state.get("current_monster"):
        state["current_monster"] = Monster.from_dict(state["current_monster"])

    return state

def initialize_game(user, adventure_id: str):
    adventures = load_all_adventures()
    adventure = next(a for a in adventures if a.id == adventure_id)
    intro = load_adv_intro(adventure_id)
    player = load_player()

    state = {
        "player": player,
        "adventure": adventure,
        "history": [intro],
        "story_steps": 0,
        "should_end": False,
        "combat_result": {"signal": 0, "message": ""},
        "current_story": intro,
        "last_cmd": "continue",
        "after_combat": False,
        "last_choices": [],
        "current_choices": [],
        "heal_amount": 0,
        "actual_heal_amount": 0,
    }
    
    serializable_state = make_serializable_state(state)

    # optional DB persistence
    if user and not user.is_anonymous:
        SaveGame.objects.update_or_create(
            user=user,
            adventure_id=adventure_id,
            defaults={
                "adventure_name": adventure.name,
                "state": serializable_state,
            },
        )

    return state, serializable_state, intro, adventure
