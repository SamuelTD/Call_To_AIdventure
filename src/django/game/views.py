from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from utils.adventure import load_adv_outro, load_all_adventures

from game.models import CharacterTemplate, SaveGame
from game.services.tools import initialize_game, persist_game, rebuild_state
from game.services.game_engine import get_engine
from utils.player import create_player, get_character_creation_options
from observability.metrics import (
    ADVENTURE_RESULTS,
    COMBAT_ACTIONS,
    COMBAT_RESULTS,
    COMBATS_STARTED,
    GAMES_STARTED,
    GAME_TURNS,
    STORY_TURN_READY_DURATION,
)

from uuid import uuid4
import json
import math
from pathlib import Path

# region HELPERS
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SYSTEM_TEMPLATE_USER_ID = -1

def build_character_sheet(player):
    inv = player.inventory if player.inventory else []
    inventory_md = "\n".join([f"- {item}" for item in inv]) if inv else "*None*"

    return {
        "name": player.name,
        "class": player.p_class.value,
        "race": player.race,
        "gender": player.gender,
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

def build_character_template_payload(template):
    return {
        "id": template.id,
        "name": template.name,
        "race": template.race,
        "class": template.character_class,
        "gender": template.gender,
        "is_generic": template.user_id == SYSTEM_TEMPLATE_USER_ID,
    }

# region VIEWS
class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})

class DebugPageView(TemplateView):
    template_name = "game/debug.html"


class DevAccountDashboardView(TemplateView):
    """Small account-management utility that is deliberately local-development only."""

    template_name = "game/dev_accounts.html"

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG or request.META.get("REMOTE_ADDR") not in {"127.0.0.1", "::1"}:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = get_user_model().objects.order_by("username")
        return context

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")
        try:
            user = get_user_model().objects.get(pk=user_id)
        except (get_user_model().DoesNotExist, ValueError, TypeError):
            raise Http404

        if action == "delete":
            username = user.get_username()
            user.delete()
            messages.success(request, f'Deleted account "{username}".')
        elif action == "set_password":
            new_password = request.POST.get("new_password", "")
            if not new_password:
                messages.error(request, "Enter a new password first.")
            else:
                user.set_password(new_password)
                user.save(update_fields=["password"])
                messages.success(request, f'Updated password for "{user.get_username()}".')
        else:
            return HttpResponseBadRequest("Unknown action")

        return redirect("dev_accounts")

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

        character = body.get("character") or {}
        try:
            player = create_player(
                name=character.get("name", ""),
                race=character.get("race", ""),
                p_class=character.get("class", ""),
                gender=character.get("gender", ""),
            )
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        try:
            state, intro, adventure = initialize_game(adventure_id, player)
        except StopIteration:
            return JsonResponse({"error": "Unknown adventure_id"}, status=404)

        # run the engine initialization (this runs pre_graph)
        engine = get_engine()
        state = engine.initialize(state)
        GAMES_STARTED.labels(adventure=adventure.id).inc()

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
        GAME_TURNS.labels(mode=result["mode"]).inc()

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
            ADVENTURE_RESULTS.labels(result="defeat").inc()
            persist_game(request, state, finish=True)
            return JsonResponse({
                "mode": "gameover",
                "player": player_sheet,
            })

        if result["mode"] == "adventure_victory":
            ADVENTURE_RESULTS.labels(result="victory").inc()
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
class StoryTurnMetricView(View):
    def post(self, request):
        serialized_state = request.session.get("game_state")
        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        duration_seconds = body.get("duration_seconds")
        if (
            isinstance(duration_seconds, bool)
            or not isinstance(duration_seconds, (int, float))
            or not math.isfinite(duration_seconds)
            or duration_seconds <= 0
            or duration_seconds > 900
        ):
            return JsonResponse(
                {"error": "duration_seconds must be between 0 and 900"},
                status=400,
            )

        adventure = serialized_state.get("adventure") or {}
        adventure_id = adventure.get("id") or "unknown"
        STORY_TURN_READY_DURATION.labels(adventure=adventure_id).observe(
            duration_seconds
        )

        return JsonResponse({"ok": True})

@method_decorator(csrf_exempt, name="dispatch")
class CurrentRoomView(View):

    def post(self, request):
        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        state = rebuild_state(serialized_state)
        engine = get_engine()
        result = engine.check_current_room(state)

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

        persist_game(request, result["state"])

        return JsonResponse({
            "mode": "story",
            "story": result["story"],
            "choices": result["choices"],
            "player": player_sheet,
        })

@method_decorator(csrf_exempt, name="dispatch")
class StartCombatView(View):

    def post(self, request):

        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        state = rebuild_state(serialized_state)
        was_already_started = state.get("current_monster") is not None

        engine = get_engine()
        result = engine.start_combat(state)

        state = result["state"]

        if result.get("mode") == "error":
            return JsonResponse({"error": result.get("error", "Failed to start combat")}, status=400)

        if not was_already_started:
            COMBATS_STARTED.labels(
                monster=state.get("current_monster_name") or "unknown"
            ).inc()

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

        COMBAT_ACTIONS.labels(action=action).inc()
        if result.get("mode") in {"victory", "defeat"}:
            COMBAT_RESULTS.labels(result=result["mode"]).inc()

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

class CharacterCreatePageView(TemplateView):
    template_name = "game/character_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adventure_id = self.request.GET.get("adventure_id", "")
        adventure = next(
            (adv for adv in load_all_adventures() if adv.id == adventure_id),
            None,
        )

        context["adventure_id"] = adventure_id
        context["adventure"] = adventure
        return context

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

class CharacterCreationOptionsView(View):
    def get(self, request):
        return JsonResponse(get_character_creation_options())

class CharacterTemplateListView(View):
    def get(self, request):
        user_ids = [SYSTEM_TEMPLATE_USER_ID]
        if request.user.is_authenticated:
            user_ids.append(request.user.id)

        templates = CharacterTemplate.objects.filter(user_id__in=user_ids).order_by(
            "user_id",
            "name",
        )

        return JsonResponse({
            "templates": [
                build_character_template_payload(template)
                for template in templates
            ],
        })

@method_decorator(csrf_exempt, name="dispatch")
class CharacterTemplateSaveView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)

        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        character = body.get("character") or {}
        try:
            player = create_player(
                name=character.get("name", ""),
                race=character.get("race", ""),
                p_class=character.get("class", ""),
                gender=character.get("gender", ""),
            )
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        duplicate_template = CharacterTemplate.objects.filter(
            user=request.user,
            name=player.name,
            race=player.race,
            character_class=player.p_class.value,
            gender=player.gender,
        ).first()

        if duplicate_template is not None:
            return JsonResponse({
                "created": False,
                "skipped": True,
                "template": {
                    "id": duplicate_template.id,
                    "name": duplicate_template.name,
                    "race": duplicate_template.race,
                    "class": duplicate_template.character_class,
                    "gender": duplicate_template.gender,
                },
            })

        template, created = CharacterTemplate.objects.update_or_create(
            user=request.user,
            name=player.name,
            defaults={
                "race": player.race,
                "character_class": player.p_class.value,
                "gender": player.gender,
            },
        )

        return JsonResponse({
            "created": created,
            "skipped": False,
            "template": {
                "id": template.id,
                "name": template.name,
                "race": template.race,
                "class": template.character_class,
                "gender": template.gender,
            },
        })

@method_decorator(csrf_exempt, name="dispatch")
class CharacterTemplateDeleteView(View):
    def post(self, request, template_id):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Login required"}, status=401)

        deleted_count, _ = CharacterTemplate.objects.filter(
            id=template_id,
            user=request.user,
        ).delete()

        if not deleted_count:
            raise Http404("Character template not found")

        return JsonResponse({"ok": True})

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
