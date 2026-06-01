from django.urls import path
from .views import (
    HealthView, PlayView, StartGameView, 
    DebugPageView, StepGameView, StartCombatView, 
    CombatActionView, AdventureListView, LandingPageView,
    PlayPageView, CurrentGameStateView, CombatPageView,
    CombatStateView, GameOverPageView, SignupView,
    SaveGameListView, LoadSaveGameView, DeleteSaveGameView,
    VictoryPageView)

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("accounts/signup/", SignupView.as_view(), name="signup"),
    path("play/", PlayPageView.as_view(), name="play"),
    path("health", HealthView.as_view(), name="health"),
    path("debug", DebugPageView.as_view(), name="debug"),
    path("api/adventures/", AdventureListView.as_view(), name="api_adventures"),
    path("api/saves/", SaveGameListView.as_view(), name="api_saves"),
    path("api/saves/<int:save_game_id>/load", LoadSaveGameView.as_view(), name="api_save_load"),
    path("api/saves/<int:save_game_id>/delete", DeleteSaveGameView.as_view(), name="api_save_delete"),
    path("api/play", PlayView.as_view(), name="api_play"),
    path("api/start", StartGameView.as_view(), name="api_start"),
    path("api/step", StepGameView.as_view(), name="api_step"),
    path("api/combat/start", StartCombatView.as_view(), name="api_combat_start"),
    path("api/combat/action", CombatActionView.as_view(), name="api_combat_action"),
    path("combat/", CombatPageView.as_view(), name="combat"),
    path("gameover/", GameOverPageView.as_view(), name="gameover"),
    path("victory/", VictoryPageView.as_view(), name="victory"),
    path("api/combat/state/", CombatStateView.as_view(), name="api_combat_state"),
    path("api/state/", CurrentGameStateView.as_view(), name="api_state"),
]
