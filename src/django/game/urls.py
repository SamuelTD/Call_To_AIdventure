from django.urls import path
from .views import (
    HealthView, PlayView, StartGameView, 
    DebugPageView, StepGameView, StartCombatView, 
    CombatActionView, AdventureListView, LandingPageView,
    PlayPageView, CurrentGameStateView, CombatPageView,
    CombatStateView, CurrentMonsterImageView)

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("play/", PlayPageView.as_view(), name="play"),
    path("health", HealthView.as_view(), name="health"),
    path("debug", DebugPageView.as_view(), name="debug"),
    path("api/adventures/", AdventureListView.as_view(), name="api_adventures"),
    path("api/play", PlayView.as_view(), name="api_play"),
    path("api/start", StartGameView.as_view(), name="api_start"),
    path("api/step", StepGameView.as_view(), name="api_step"),
    path("api/combat/start", StartCombatView.as_view(), name="api_combat_start"),
    path("api/combat/action", CombatActionView.as_view(), name="api_combat_action"),
    path("combat/", CombatPageView.as_view(), name="combat"),
    path("api/combat/state/", CombatStateView.as_view(), name="api_combat_state"),
    path("api/combat/image/", CurrentMonsterImageView.as_view(), name="api_combat_image"),
    path("api/state/", CurrentGameStateView.as_view(), name="api_state"),
]