# AI monitoring catalogue and objectives

No metric label contains prompts, generated text, usernames, session IDs or
other unbounded/private values.

| Signal | Purpose | Objective / alert |
|---|---|---|
| `aidventure_llm_requests_total` | Logical availability | At least 99% successful over 30 days; warn after 3 unavailable calls in 10 minutes |
| `aidventure_llm_request_duration_seconds` | End-user provider latency | p95 below 30 seconds; warn for 10 sustained minutes |
| `aidventure_llm_structured_outputs_total` | Schema validity | 100%; alert on any invalid output |
| `aidventure_llm_tokens_total` | Reported usage | Capacity and cost analysis; bounded model/direction labels |
| `aidventure_llm_estimated_cost_usd_total` | Estimated spend | Configure current per-million-token rates outside code |
| `aidventure_rag_requests_total` | Hits, empty results and failures | Investigate more than 2 failures in 15 minutes |
| `aidventure_rag_request_duration_seconds` | Complete retrieval latency | Track p95; establish final threshold from staging baseline |
| `aidventure_rag_embedding_*` | Embedding provider behavior | Diagnose timeout and response failures |

The Alertmanager configuration deliberately has only a local sink. A deployment
owner must add a protected receiver. To demonstrate alert delivery safely,
temporarily change the test rule from `vector(0)` to `vector(1)`, reload
Prometheus, retain a screenshot/timeline, and restore it immediately.
