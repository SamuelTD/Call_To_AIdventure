from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from game.services.tools import initialize_game, rebuild_state, make_serializable_state
from game.services.game_engine import get_engine

from uuid import uuid4
import json

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

        # 1️⃣ Load state from session
        serialized_state = request.session.get("game_state")

        if not serialized_state:
            return JsonResponse({"error": "No active game"}, status=400)

        # 2️⃣ Rebuild runtime objects
        state = rebuild_state(serialized_state)

        # 3️⃣ Run engine step
        engine = get_engine()
        result = engine.step(state, choice)

        state = result["state"]

        # 4️⃣ Save updated state
        request.session["game_state"] = make_serializable_state(state)
        request.session.modified = True

        # 5️⃣ Return response depending on mode
        if result["mode"] == "combat":
            return JsonResponse({
                "mode": "combat",
                "combat_fluff": result["combat_fluff"]
            })

        return JsonResponse({
            "mode": "story",
            "story": result["story"],
            "choices": result["choices"]
        })