from game.models import SaveGame
from django.utils import timezone
from utils.player import Player
from utils.adventure import Adventure, load_all_adventures, load_adv_intro
from utils.monster import Monster

def ensure_goal_state(state: dict) -> dict:
    adventure = state.get("adventure")
    adventure_goals = list(adventure.goals) if adventure else []
    finished_goals = list(state.get("finished_goals") or [])
    ongoing_goals = list(state.get("ongoing_goals") or [
        goal for goal in adventure_goals if goal not in finished_goals
    ])

    state["finished_goals"] = finished_goals
    state["ongoing_goals"] = [goal for goal in ongoing_goals if goal not in finished_goals]
    state.setdefault("adventure_completed", False)
    state.setdefault("end_reason", None)

    return state


def ensure_room_state(state: dict) -> dict:
    adventure = state.get("adventure")
    locations = list(adventure.locations.available) if adventure else []
    current_location_id = state.get("current_location_id")

    if not current_location_id and adventure:
        current_location_id = adventure.locations.start
        state["current_location_id"] = current_location_id

    if current_location_id in locations:
        state["location_index"] = locations.index(current_location_id)
    else:
        state.setdefault("location_index", 0 if locations else -1)

    state.setdefault("completed_location_ids", [])
    return state

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

    state.setdefault("language", "en")
    return ensure_room_state(ensure_goal_state(state))

def persist_game(
    request,
    state: dict,
    *,
    save_game=None,
    create_new=False,
    finish=False,
) -> tuple[dict, SaveGame | None]:
    serializable_state = make_serializable_state(state)

    request.session["game_state"] = serializable_state

    if not request.user.is_authenticated:
        request.session.pop("save_game_id", None)
        request.session.modified = True
        return serializable_state, None

    adventure = state.get("adventure")
    save = save_game

    if save is None and not create_new:
        save_id = request.session.get("save_game_id")
        if save_id:
            save = SaveGame.objects.filter(id=save_id, user=request.user).first()

    if save is None:
        save = SaveGame(
            user=request.user,
            adventure_id=adventure.id if adventure else "",
            adventure_name=adventure.name if adventure else "Adventure",
        )

    save.state = serializable_state
    if adventure:
        save.adventure_id = adventure.id
        save.adventure_name = adventure.name
    if create_new:
        save.is_finished = False
        save.finished_at = None
    if finish and not save.is_finished:
        save.is_finished = True
        save.finished_at = timezone.now()
    save.save()

    request.session["save_game_id"] = save.id
    request.session.modified = True
    return serializable_state, save

def initialize_game(adventure_id: str, player: Player, language: str = "en"):
    adventures = load_all_adventures()
    adventure = next(a for a in adventures if a.id == adventure_id)
    intro = load_adv_intro(adventure_id)

    state = {
        "language": "fr" if str(language).lower().startswith("fr") else "en",
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
        "ongoing_goals": list(adventure.goals),
        "finished_goals": [],
        "adventure_completed": False,
        "end_reason": None,
        "current_location_id": adventure.locations.start,
        "location_index": (
            adventure.locations.available.index(adventure.locations.start)
            if adventure.locations.start in adventure.locations.available
            else -1
        ),
        "completed_location_ids": [],
        "heal_amount": 0,
        "actual_heal_amount": 0,
        "damage_amount": 0,
        "actual_damage_amount": 0,
    }
    
    return state, intro, adventure
