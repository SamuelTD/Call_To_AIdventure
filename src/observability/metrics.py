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

STORY_TURN_READY_DURATION = Histogram(
    "aidventure_story_turn_ready_duration_seconds",
    "Browser-observed time from submitting a story choice until choices are usable again",
    ["adventure"],
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 45, 60, 90, 120, 300),
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

LLM_STRUCTURED_OUTPUTS = Counter(
    "aidventure_llm_structured_outputs_total",
    "Structured LLM output validation outcomes",
    ["operation", "status"],
)

LLM_TOKEN_USAGE = Counter(
    "aidventure_llm_tokens_total",
    "Provider-reported token usage where available",
    ["direction", "model"],
)

LLM_ESTIMATED_COST_USD = Counter(
    "aidventure_llm_estimated_cost_usd_total",
    "Estimated provider cost from reported tokens and configured rates",
    ["model"],
)

RAG_REQUESTS = Counter(
    "aidventure_rag_requests_total",
    "RAG retrieval outcomes",
    ["status"],
)

RAG_REQUEST_DURATION = Histogram(
    "aidventure_rag_request_duration_seconds",
    "RAG query duration including embedding and vector lookup",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

RAG_EMBEDDING_REQUESTS = Counter(
    "aidventure_rag_embedding_requests_total",
    "Embedding request outcomes",
    ["status"],
)

RAG_EMBEDDING_DURATION = Histogram(
    "aidventure_rag_embedding_duration_seconds",
    "Embedding provider request duration",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
