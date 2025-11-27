from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from game.services.game_engine import initialize_game
from uuid import uuid4

class HealthView(View):
    def get(self, request):
        return JsonResponse({"status": "ok"})

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

        state, intro, adventure = initialize_game(user, adventure_id)

        # store in session
        session_id = str(uuid4())
        request.session["game_state"] = state
        request.session["session_id"] = session_id
        request.session.modified = True

        return JsonResponse({
            "session_id": session_id,
            "adventure_name": adventure.name,
            "story": intro,
            "choices": state["current_choices"],
        })
