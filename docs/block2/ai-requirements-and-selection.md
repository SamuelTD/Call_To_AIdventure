# AI requirements and service-selection record

## Measurable needs

| Function | Contract | Target | Failure behavior |
|---|---|---|---|
| Story generation | State, selected choice and scoped lore → English/French narrative | p95 under 30 s; successful turn rate ≥99% | Retry transient errors; return 503; do not persist partial state |
| Choice generation | Context → exactly 3 distinct actions, each ≤6 words | 100% schema validity; correct requested language | Reject invalid structure and preserve current state |
| Tool selection | State → allow-listed deterministic game tool | No unregistered action; arguments validated server-side | No-op or controlled failure; rules stay server-owned |
| Goal/room evaluation | Narrative/state → typed classification | ≥90% labelled-set agreement | Conservative incomplete result and diagnostic metric |
| Lore retrieval | Scoped query → chunks with source metadata | ≥90% expected-source recall; p95 baseline established in staging | Empty context; game continues without invented retrieval |

Inputs are limited to 1,000 characters at the versioned API boundary. Prompts,
responses, identities and session IDs are excluded from metric labels. English
and French are required. Provider credentials must stay outside Git.

## Architecture decision ADR-002

**Decision:** hosted OpenAI-compatible generation, local Ollama embeddings,
ChromaDB retrieval and LangGraph orchestration.

Hosted generation was selected because the application needs strong structured
outputs, tool calling and multilingual narrative without hosting a large model.
Embeddings remain local because lore is stable, retrieval must be inexpensive,
and the corpus can stay on the project machine. ChromaDB matches the small
corpus and metadata-filtering need. LangGraph makes state transitions and
deterministic tool boundaries explicit.

Rejected categories: a fully local generation model until comparable schema,
language and latency measurements support it; provider-managed vector storage
because it adds cost and data transfer without a demonstrated need; plain
chat-completion orchestration because explicit state transitions are central.

## Candidate benchmark protocol

Run every candidate against the same Git revision and `evaluation/dataset.json`.
Record model/version, date, schema-validity and case pass rates, p50/p95 latency,
tokens, estimated cost, French review, availability region and retention setting.
A candidate is eliminated if it cannot produce constrained outputs, lacks the
required language quality, violates privacy, or exceeds approved budget/latency.

| Candidate | Schema/quality | Latency/cost | Privacy | Status |
|---|---|---|---|---|
| Current configured OpenAI model | Pending live run | Pending | Owner review required | Provisional |
| Second hosted structured-output model | Pending | Pending | Owner review required | Required comparison |
| Local generation candidate | Pending | Hardware-dependent | Local | Optional comparison |
| Ollama `mxbai-embed-large` | Expected-source run pending | Local compute | Local | Current embedding |

No fabricated benchmark values are recorded. Live runs require approved budget,
current pricing, credentials and human language-quality review.

## Cost worksheet

`turns/month × calls/turn × ((mean input tokens × input rate) + (mean output tokens × output rate)) / 1,000,000`

Use Prometheus token counters for observed means and set cost-rate environment
variables from current provider pricing. Add hosting, storage and local compute.
