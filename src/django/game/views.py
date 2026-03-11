from django.http import JsonResponse, HttpResponseBadRequest, FileResponse, Http404
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from utils.adventure import load_all_adventures
from utils.player import Player

from game.services.tools import initialize_game, rebuild_state, make_serializable_state
from game.services.game_engine import get_engine

from uuid import uuid4
import json
from pathlib import Path

# region HELPERS
PROJECT_ROOT = Path(__file__).resolve().parents[3]

def build_character_sheet(player):
    inv = player.inventory if player.inventory else []
    inventory_md = "\n".join([f"- {item}" for item in inv]) if inv else "*None*"

    return {
        "name": player.name,
        "class": player.p_class.value,
        "race": player.race,
        "gold": player.gold,
        "hp": player.hp,
        "max_hp": player.max_hp,
        "weapon": player.weapon.name if player.weapon else "None",
        "inventory": inv,
        "inventory_markdown": inventory_md,
    }

def build_character_sheet(player):
    inv = player.inventory if player.inventory else []

    return {
        "name": player.name,
        "class": player.p_class.value,
        "race": player.race,
        "gold": player.gold,
        "hp": player.hp,
        "max_hp": player.max_hp,
        "weapon": player.weapon.name if player.weapon else "None",
        "inventory": inv,
    }

def build_combat_state_payload(state):
    player = state["player"]
    monster = state.get("current_monster")

    return {
        "monster_name": state.get("current_monster_name"),
        "player_hp": player.hp,
        "player_max_hp": player.max_hp,
        "monster_hp": monster.HP if monster else None,
        "monster_max_hp": monster.max_HP if monster else None,
        "player": build_character_sheet(player),
    }

# region VIEWS
class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})

class DebugPageView(TemplateView):
    template_name = "game/debug.html"

@method_decorator(csrf_exempt, name="dispatch")  # simple for now; we'll do proper CSRF/auth later
class PlayView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON body")

        user_input = (payload.get("input") or "").strip()
        session_id = payload.get("session_id")  # optional for now

        if not user_input:
            return JsonResponse({"error": "input is required"}, status=400)

        # TODO: wire to your engine in the next step
        return JsonResponse({"ok": True, "echo": user_input, "session_id": session_id})


@method_decorator(csrf_exempt, name="dispatch")
class StartGameView(View):

    def post(self, request):

        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        adventure_id = body.get("adventure_id")
        if not adventure_id:
            return JsonResponse({"error": "Missing adventure_id"}, status=400)

        user = request.user if request.user.is_authenticated else None

        state, serializable_state, intro, adventure = initialize_game(user, adventure_id)

        # run the engine initialization (this runs pre_graph)
        engine = get_engine()
        state = engine.initialize(state)

        # store in session
        session_id = str(uuid4())

        request.session["game_state"] = make_serializable_state(state)
        request.session["session_id"] = session_id
        request.session.modified = True

        return JsonResponse({
            "session_id": session_id,
            "adventure_name": adventure.name,
            "story": state["current_story"],
            "choices": state["current_choices"],
        })

@method_decorator(csrf_exempt, name="dispatch")
class StepGameView(View):

    def post(self, request):

        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        choice = body.get("choice")

        if not choice:
            return JsonResponse({"error": "choice is required"}, status=400)

        # Load state from session
        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        # Rebuild runtime objects
        state = rebuild_state(serialized_state)

        # Run engine step
        engine = get_engine()
        result = engine.step(state, choice)

        state = result["state"]

        # Save updated state
        request.session["game_state"] = make_serializable_state(state)
        request.session.modified = True

        player_sheet = build_character_sheet(state["player"])
        
        # Return response depending on mode
        # COMBAT BRANCH
        if result["mode"] == "combat":
            request.session["game_state"] = make_serializable_state(state)
            request.session["combat_fluff"] = result["combat_fluff"]
            request.session.modified = True
            
            return JsonResponse({
                "mode": "combat",
                "combat_fluff": result["combat_fluff"],
                "player": player_sheet
            })

        # STORY BRANCH
        request.session["combat_fluff"] = ""        
        return JsonResponse({
            "mode": "story",
            "story": result["story"],
            "choices": result["choices"],
            "player": player_sheet
        })

@method_decorator(csrf_exempt, name="dispatch")
class StartCombatView(View):

    def post(self, request):

        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        state = rebuild_state(serialized_state)

        engine = get_engine()
        result = engine.start_combat(state)

        state = result["state"]

        request.session["game_state"] = make_serializable_state(state)
        request.session.modified = True

        response_payload = {k: v for k, v in result.items() if k != "state"}
        return JsonResponse(response_payload)
        
@method_decorator(csrf_exempt, name="dispatch")
class CombatActionView(View):

    def post(self, request):

        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        action = body.get("action")

        if not action:
            return JsonResponse({"error": "action is required"}, status=400)

        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        state = rebuild_state(serialized_state)

        engine = get_engine()
        result = engine.combat_action(state, action)

        state = result["state"]

        request.session["game_state"] = make_serializable_state(state)
        request.session.modified = True
        
        response_payload = {k: v for k, v in result.items() if k != "state"}
        response_payload["player"] = build_character_sheet(state["player"])

        return JsonResponse(response_payload)

@method_decorator(csrf_exempt, name="dispatch")
class CombatStateView(View):

    def get(self, request):
        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        state = rebuild_state(serialized_state)

        if not state.get("current_monster_name"):
            return JsonResponse({"error": "No active combat"}, status=400)

        payload = build_combat_state_payload(state)
        payload["combat_fluff"] = request.session.get("combat_fluff", "")

        return JsonResponse(payload)

class CombatPageView(TemplateView):
    template_name = "game/combat.html"    
    
class LandingPageView(TemplateView):
    template_name = "game/landing.html"

class AdventureListView(View):
    def get(self, request):
        adventures = load_all_adventures()

        data = [
            {
                "id": adv.id,
                "name": adv.name,
                "description": adv.description,
            }
            for adv in adventures
        ]

        return JsonResponse({"adventures": data})
    
class PlayPageView(TemplateView):
    template_name = "game/play.html"
    
@method_decorator(csrf_exempt, name="dispatch")
class CurrentGameStateView(View):

    def get(self, request):
        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        state = rebuild_state(serialized_state)
        player_sheet = build_character_sheet(state["player"])

        return JsonResponse({
            "story": state.get("current_story", ""),
            "choices": state.get("current_choices", []),
            "player": player_sheet,
            "adventure_name": state["adventure"].name if state.get("adventure") else "Adventure",
        })