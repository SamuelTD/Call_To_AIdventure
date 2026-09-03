"""Versioned and secured HTTP boundary for AI-backed game turns."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.cache import cache
from django.http import FileResponse, JsonResponse
from django.views import View

from agents.runtime_config import AIRuntimeConfig, AIConfigurationError
from game.models import SaveGame
from game.views import StepGameView


def api_error(code: str, message: str, status: int, *, details=None) -> JsonResponse:
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return JsonResponse(payload, status=status)


class AuthenticatedJsonView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_error("authentication_required", "Authentication is required.", 401)
        return super().dispatch(request, *args, **kwargs)


class AIHealthView(View):
    def get(self, request):
        try:
            config = AIRuntimeConfig.from_env()
        except AIConfigurationError:
            return api_error("configuration_invalid", "AI configuration is invalid.", 503)
        return JsonResponse({
            "status": "configured" if config.openai_api_key else "degraded",
            "generation_configured": bool(config.openai_api_key),
            "retrieval_configured": config.rag_enabled,
        })


class AIConfigurationView(AuthenticatedJsonView):
    def get(self, request):
        return JsonResponse({"configuration": AIRuntimeConfig.from_env().safe_metadata()})


class AITurnView(AuthenticatedJsonView):
    """Advance a saved game owned by the authenticated caller."""

    def post(self, request, game_id: int):
        save_game = SaveGame.objects.filter(id=game_id, user=request.user).first()
        if save_game is None:
            return api_error("game_not_found", "Game not found.", 404)
        if save_game.is_finished:
            return api_error("game_finished", "A finished game cannot be advanced.", 409)

        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
        config = AIRuntimeConfig.from_env()
        if content_length > config.max_input_chars + 256:
            return api_error("payload_too_large", "Request payload is too large.", 413)
        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return api_error("invalid_json", "Request body must be valid JSON.", 400)

        choice = body.get("choice")
        if not isinstance(choice, str) or not choice.strip():
            return api_error("validation_error", "choice is required.", 400)
        if len(choice) > config.max_input_chars:
            return api_error("validation_error", "choice exceeds the configured limit.", 400)

        allowed_choices = (save_game.state or {}).get("current_choices") or []
        if allowed_choices and choice not in allowed_choices:
            return api_error(
                "invalid_choice",
                "choice must match one of the current server-provided choices.",
                422,
            )

        throttle_key = f"ai-turn:user:{request.user.pk}"
        count = cache.get(throttle_key, 0)
        limit = max(1, config.user_turn_limit_per_hour)
        if count >= limit:
            return api_error("rate_limit_exceeded", "AI turn quota exceeded.", 429)
        if count == 0:
            cache.set(throttle_key, 1, timeout=3600)
        else:
            try:
                cache.incr(throttle_key)
            except ValueError:
                cache.set(throttle_key, count + 1, timeout=3600)

        request.session["game_state"] = save_game.state
        request.session["save_game_id"] = save_game.id
        response = StepGameView().post(request)
        if isinstance(response, JsonResponse) and response.status_code >= 400:
            return response
        return response


class AIOpenApiView(View):
    def get(self, request):
        path = Path(__file__).resolve().parents[3] / "docs" / "block2" / "openapi.yaml"
        return FileResponse(path.open("rb"), content_type="application/yaml")
