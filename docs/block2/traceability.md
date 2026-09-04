# AI requirements traceability

| Need | Implementation | API/evidence | Automated validation |
|---|---|---|---|
| Narrative turns | `agents/game_master_graph.py`, `game/services/game_engine.py` | Versioned turn endpoint | Graph, retry and state tests |
| Typed output | `agents/schemas.py`, `agents/llm_runtime.py` | OpenAPI and schema metrics | Schema tests and evaluation dataset |
| Deterministic actions | `agents/tools.py`, `combat/core.py` | Server-provided choices only | Tool and adversarial API tests |
| Scoped lore | `retrieval/service.py`, active graph calls | RAG documentation and metrics | Scope/cache and source tests |
| Provider outage | resilience layer and views | Controlled 503, unchanged state | Retry-exhaustion tests |
| Ownership | `game/ai_api.py`, `SaveGame.user` | Session auth, CSRF, isolation | Cross-user/auth tests |
| Reproducibility | config, lock, evaluation report | Safe metadata endpoint | CI artifacts |
| Monitoring | observability and monitoring configs | SLOs and alerts | Metric/rule validation |
