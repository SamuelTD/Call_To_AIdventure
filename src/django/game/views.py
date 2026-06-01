from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.conf import settings
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from utils.adventure import load_adv_outro, load_all_adventures

from game.models import SaveGame
from game.services.tools import initialize_game, persist_game, rebuild_state
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

def build_ending_reason_label(state):
    reason = state.get("end_reason")
    player = state.get("player") or {}
    player_hp = player.get("hp")

    if reason == "victory":
        return "Ending: Victory"
    if reason == "death":
        return "Ending: Death"
    if player_hp == 0:
        return "Ending: Defeat"
    return "Ending: Finished"

def build_save_game_payload(save_game):
    state = save_game.state or {}
    player = state.get("player") or {}
    story = state.get("current_story") or ""
    choices = state.get("current_choices") or []

    return {
        "id": save_game.id,
        "adventure_id": save_game.adventure_id,
        "adventure_name": save_game.adventure_name,
        "player_name": player.get("name", "Adventurer"),
        "player_hp": player.get("hp"),
        "player_max_hp": player.get("max_hp"),
        "story_preview": story[:180],
        "ending_reason": build_ending_reason_label(state) if save_game.is_finished else "",
        "choice_count": len(choices),
        "is_finished": save_game.is_finished,
        "finished_at": save_game.finished_at.isoformat() if save_game.finished_at else None,
        "updated_at": save_game.updated_at.isoformat(),
        "created_at": save_game.created_at.isoformat(),
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

        try:
            state, intro, adventure = initialize_game(adventure_id)
        except StopIteration:
            return JsonResponse({"error": "Unknown adventure_id"}, status=404)

        # run the engine initialization (this runs pre_graph)
        engine = get_engine()
        state = engine.initialize(state)

        session_id = str(uuid4())

        request.session["session_id"] = session_id
        serializable_state, save_game = persist_game(request, state, create_new=True)

        return JsonResponse({
            "session_id": session_id,
            "save_game_id": save_game.id if save_game else None,
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

        player_sheet = build_character_sheet(state["player"])

        if result["mode"] == "service_unavailable":
            return JsonResponse(
                {
                    "mode": "service_unavailable",
                    "error": settings.LLM_SERVICE_UNAVAILABLE_MESSAGE,
                    "player": player_sheet,
                },
                status=settings.LLM_SERVICE_UNAVAILABLE_STATUS_CODE,
            )

        if result["mode"] == "gameover":
            persist_game(request, state, finish=True)
            return JsonResponse({
                "mode": "gameover",
                "player": player_sheet,
            })

        if result["mode"] == "adventure_victory":
            persist_game(request, state, finish=True)
            return JsonResponse({
                "mode": "adventure_victory",
                "player": player_sheet,
            })

        # Save updated state
        persist_game(request, state)
        
        # Return response depending on mode
        # COMBAT BRANCH
        if result["mode"] == "combat":
            request.session["combat_fluff"] = result["combat_fluff"]
            request.session.modified = True
            
            return JsonResponse({
                "mode": "combat",
                "combat_fluff": result["combat_fluff"],
                "player": player_sheet
            })

        # STORY BRANCH
        request.session["combat_fluff"] = ""        
        request.session.modified = True
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

        if result.get("mode") == "error":
            return JsonResponse({"error": result.get("error", "Failed to start combat")}, status=400)

        persist_game(request, state)

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

        if result.get("mode") == "error":
            return JsonResponse({"error": result.get("error", "Combat action failed")}, status=400)

        persist_game(request, state, finish=result.get("mode") == "defeat")
        
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

class GameOverPageView(TemplateView):
    template_name = "game/gameover.html"

class VictoryPageView(TemplateView):
    template_name = "game/victory.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        serialized_state = self.request.session.get("game_state") or {}
        state = rebuild_state(serialized_state) if serialized_state else {}
        adventure = state.get("adventure")

        context["adventure_name"] = adventure.name if adventure else "Adventure Complete"
        context["outro"] = load_adv_outro(adventure.id) if adventure else ""
        return context
    
class LandingPageView(TemplateView):
    template_name = "game/landing.html"

class SignupView(View):
    template_name = "registration/signup.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("landing")

        return render(request, self.template_name, {"form": UserCreationForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("landing")

        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("landing")

        return render(request, self.template_name, {"form": form})

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

class SaveGameListView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"saves": []})

        saves = SaveGame.objects.filter(user=request.user).order_by("-updated_at")
        active_saves = [save for save in saves if not save.is_finished]
        history_saves = [save for save in saves if save.is_finished]

        return JsonResponse({
            "saves": [build_save_game_payload(save) for save in active_saves],
            "history": [build_save_game_payload(save) for save in history_saves],
        })

@method_decorator(csrf_exempt, name="dispatch")
class LoadSaveGameView(View):
    def post(self, request, save_game_id):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)

        save_game = SaveGame.objects.filter(id=save_game_id, user=request.user).first()
        if save_game is None:
            raise Http404("Save game not found")

        if save_game.is_finished:
            return JsonResponse({"error": "Finished games are in history and cannot be loaded"}, status=400)

        request.session["game_state"] = save_game.state
        request.session["save_game_id"] = save_game.id
        request.session["session_id"] = str(uuid4())
        request.session["combat_fluff"] = ""
        request.session.modified = True

        state = save_game.state or {}
        redirect_url = "/combat/" if state.get("current_monster_name") else "/play/"

        return JsonResponse({
            "save_game": build_save_game_payload(save_game),
            "redirect_url": redirect_url,
        })

@method_decorator(csrf_exempt, name="dispatch")
class DeleteSaveGameView(View):
    def post(self, request, save_game_id):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)

        deleted_count, _ = SaveGame.objects.filter(id=save_game_id, user=request.user).delete()

        if not deleted_count:
            raise Http404("Save game not found")

        if request.session.get("save_game_id") == save_game_id:
            request.session.pop("save_game_id", None)
            request.session.pop("game_state", None)
            request.session.pop("combat_fluff", None)
            request.session.modified = True

        return JsonResponse({"ok": True})
    
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
