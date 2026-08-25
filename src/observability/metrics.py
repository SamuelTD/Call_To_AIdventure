"""Low-cardinality Prometheus metrics for gameplay and LLM activity."""

from prometheus_client import Counter, Histogram


GAMES_STARTED = Counter(
    "aidventure_games_started_total",
    "Number of games started",
    ["adventure"],
)

GAME_TURNS = Counter(
    "aidventure_game_turns_total",
    "Number of game turns processed",
    ["mode"],
)

COMBATS_STARTED = Counter(
    "aidventure_combats_started_total",
    "Number of combats started",
    ["monster"],
)

COMBAT_ACTIONS = Counter(
    "aidventure_combat_actions_total",
    "Number of valid combat actions selected",
    ["action"],
)

COMBAT_RESULTS = Counter(
    "aidventure_combat_results_total",
    "Number of completed combats",
    ["result"],
)

ADVENTURE_RESULTS = Counter(
    "aidventure_adventure_results_total",
    "Number of completed adventures",
    ["result"],
)

LLM_REQUESTS = Counter(
    "aidventure_llm_requests_total",
    "Number of logical LLM requests",
    ["operation", "status"],
)

LLM_ATTEMPTS = Counter(
    "aidventure_llm_attempts_total",
    "Number of individual LLM provider attempts",
    ["operation"],
)

LLM_RETRIES = Counter(
    "aidventure_llm_retries_total",
    "Number of LLM provider retries",
    ["operation"],
)

LLM_REQUEST_DURATION = Histogram(
    "aidventure_llm_request_duration_seconds",
    "Duration of logical LLM requests, including retry delays",
    ["operation"],
    buckets=(0.25, 0.5, 1, 2, 5, 10, 20, 30, 60),
)
