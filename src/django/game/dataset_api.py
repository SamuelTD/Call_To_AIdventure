from __future__ import annotations

import json

from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views import View

from data_pipeline.repository import DatasetRepository


MAX_PAGE_SIZE = 100


def error_response(code: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def repository() -> DatasetRepository:
    return DatasetRepository(settings.DATASET_DB_PATH)


def parse_positive_integer(value: str | None, default: int, name: str) -> int:
    if value is None:
        return default
    parsed = int(value)
    if parsed < 1:
        raise ValueError(f"{name} must be at least 1")
    return parsed


def parse_optional_float(value: str | None, name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be numeric") from exc


class MonsterCollectionView(View):
    def get(self, request):
        try:
            page = parse_positive_integer(request.GET.get("page"), 1, "page")
            page_size = parse_positive_integer(
                request.GET.get("page_size"), 20, "page_size"
            )
            if page_size > MAX_PAGE_SIZE:
                raise ValueError(f"page_size cannot exceed {MAX_PAGE_SIZE}")
            challenge_min = parse_optional_float(
                request.GET.get("challenge_min"), "challenge_min"
            )
            challenge_max = parse_optional_float(
                request.GET.get("challenge_max"), "challenge_max"
            )
            if (
                challenge_min is not None
                and challenge_max is not None
                and challenge_min > challenge_max
            ):
                raise ValueError("challenge_min cannot exceed challenge_max")
            result = repository().list_monsters(
                search=request.GET.get("search"),
                challenge_min=challenge_min,
                challenge_max=challenge_max,
                ordering=request.GET.get("ordering", "name"),
                limit=page_size,
                offset=(page - 1) * page_size,
            )
        except (ValueError, TypeError) as exc:
            return error_response("invalid_query", str(exc), 400)
        except Exception as exc:
            if "no such table" in str(exc) or "unable to open database" in str(exc):
                return error_response("dataset_unavailable", "Dataset is not initialized", 503)
            raise
        return JsonResponse(
            {
                "count": result.total,
                "page": page,
                "page_size": page_size,
                "results": result.items,
            }
        )


class MonsterDetailView(View):
    def get(self, request, monster_id: int):
        try:
            monster = repository().get_monster(monster_id)
        except Exception as exc:
            if "no such table" in str(exc) or "unable to open database" in str(exc):
                return error_response("dataset_unavailable", "Dataset is not initialized", 503)
            raise
        if monster is None:
            return error_response("not_found", "Monster not found", 404)
        monster["items_loot"] = json.loads(monster["items_loot"])
        return JsonResponse(monster)


class IngestionRunSummaryView(View):
    def get(self, request, run_id: str):
        if not request.user.is_authenticated:
            return error_response("authentication_required", "Login required", 401)
        if not request.user.is_staff:
            return error_response("permission_denied", "Staff access required", 403)
        run = repository().get_run(run_id)
        if run is None:
            return error_response("not_found", "Ingestion run not found", 404)
        return JsonResponse(run)


class DatasetOpenApiView(View):
    def get(self, request):
        path = settings.PROJECT_ROOT.parent / "docs" / "block1" / "openapi.yaml"
        return FileResponse(path.open("rb"), content_type="application/yaml")


class DatasetApiDocsView(View):
    def get(self, request):
        return HttpResponse(
            """<!doctype html>
<html><head><title>Monster Dataset API</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head><body><div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url:'/api/v1/openapi.yaml',dom_id:'#swagger-ui'});</script>
</body></html>"""
        )
