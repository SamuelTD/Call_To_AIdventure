from django.urls import path
from .views import HealthView, PlayView, StartGameView, DebugPageView, StepGameView

urlpatterns = [
    path("", HealthView.as_view(), name="index"),
    path("health", HealthView.as_view(), name="health"),
    path("debug", DebugPageView.as_view(), name="debug"),
    path("api/play", PlayView.as_view(), name="api_play"),
    path("api/start", StartGameView.as_view(), name="api_start"),
    path("api/step", StepGameView.as_view(), name="api_step"),
]