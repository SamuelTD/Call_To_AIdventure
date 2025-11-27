from uuid import uuid4
from game.models import SaveGame
from utils.player import load_player
from utils.adventure import load_all_adventures, load_adv_intro

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
        "current_choices": []
    }

    # optional DB persistence
    if user and not user.is_anonymous:
        SaveGame.objects.update_or_create(
            user=user,
            adventure_id=adventure_id,
            defaults={
                "adventure_name": adventure.name,
                "state": state,
            },
        )

    return state, intro, adventure
