# Block 3 architecture decision records

## ADR-001 - Use Django as the web application framework

**Status:** accepted.

**Decision:** use Django for routing, templates, authentication, sessions,
forms, ORM migrations and JSON endpoints.

**Rationale:** the project needs a complete server-side web shell around a
stateful game. Django provides built-in authentication, CSRF middleware,
session storage and a mature test client, reducing custom security code.

**Alternatives considered:**

- FastAPI plus separate frontend: better for pure APIs, but would require
  additional auth/session/frontend structure.
- Flask: simpler, but more custom work for auth, admin, forms and security.
- Gradio only: useful for prototypes, but not enough for a multi-page app with
  accounts, saves and browser flows.

**Consequences:** Django owns browser security and persistence boundaries.
Long-running AI calls must be managed carefully because synchronous views can
occupy request workers.

## ADR-002 - Use LangGraph for stateful AI orchestration

**Status:** accepted.

**Decision:** keep story progression, tool selection, RAG use and typed graph
state in LangGraph behind `GameEngine`.

**Rationale:** the application is not a single prompt. It needs stateful turns,
tool routing, pre/post input phases, goal evaluation and controlled failure
modes. LangGraph makes these transitions explicit and testable.

**Alternatives considered:**

- Plain provider chat calls: simpler, but would hide state transitions in
  ad-hoc code.
- Fully deterministic story engine: safer, but would not satisfy the AI
  integration objective.

**Consequences:** graph/runtime thread-safety must be reviewed before scaling
to multiple workers. `GameEngine` remains the integration boundary.

## ADR-003 - Use OpenAI-compatible hosted generation

**Status:** provisional accepted.

**Decision:** use a hosted OpenAI-compatible provider for narrative generation
and tool-capable structured outputs.

**Rationale:** the project needs multilingual narrative quality, robust
instruction following, tool calling and bounded latency without hosting a
large local model.

**Alternatives considered:**

- Fully local generation: stronger privacy, but requires local hardware,
  quality benchmarks and schema reliability evidence.
- Multiple live providers: useful for comparison, but increases integration
  cost for the current certification scope.

**Consequences:** provider availability, price, retention policy and API budget
must be validated by the owner using current provider terms.

## ADR-004 - Use local Ollama embeddings

**Status:** accepted.

**Decision:** keep embedding generation local through Ollama.

**Rationale:** lore is relatively stable, small, and inexpensive to embed
locally. Local embeddings reduce provider cost and avoid sending the full lore
corpus to a hosted embedding provider.

**Alternatives considered:**

- Hosted embeddings: simpler operations if already using hosted generation,
  but adds external data transfer and cost.
- Keyword-only retrieval: cheaper, but weaker for semantic lore lookup.

**Consequences:** developer/test machines need the embedding service for live
retrieval operations. Tests should mock or use cached/dry-run paths.

## ADR-005 - Use ChromaDB for vector retrieval

**Status:** accepted.

**Decision:** store RAG chunks and metadata in ChromaDB.

**Rationale:** the corpus is small and metadata scoping by adventure/location
is central. ChromaDB is enough for local proof-of-concept retrieval without a
managed vector database.

**Alternatives considered:**

- Managed vector store: more production-friendly, but unnecessary for the
  current local corpus and adds account/deployment complexity.
- SQLite FTS only: useful for keyword search, but not equivalent to semantic
  retrieval.

**Consequences:** production deployment must decide whether ChromaDB remains
local, containerized, or is replaced by a managed store.

## ADR-006 - Use SQLite for local application persistence

**Status:** accepted for local/demo; revisit for public deployment.

**Decision:** use SQLite for Django persistence and a separate read-only
dataset SQLite database.

**Rationale:** SQLite keeps setup simple for a solo certification project and
is sufficient for local demonstration, tests and low-concurrency proof of
concept.

**Alternatives considered:**

- PostgreSQL: stronger production concurrency and operational model, but adds
  setup and hosting requirements.
- Single merged database: simpler topology, but weaker separation between
  application-owned data and generated/read-only game dataset.

**Consequences:** target deployment must either justify SQLite limits or select
a production database. Data ownership must remain documented.

## ADR-007 - Use Prometheus and Grafana for observability

**Status:** accepted.

**Decision:** expose Django metrics and scrape them with Prometheus, with
Grafana dashboards provisioned locally.

**Rationale:** the project needs inspectable evidence for application, AI and
business metrics. Prometheus/Grafana are standard, versionable and already
containerized in the repository.

**Alternatives considered:**

- Plain logs only: insufficient for SLOs and alert evidence.
- Hosted observability platform: production-friendly, but requires accounts
  and external configuration not available in this repository.

**Consequences:** alerting, structured logs and secured production monitoring
remain Priority 5 work.

## ADR-008 - Store combat state in per-game serialized state

**Status:** accepted after Priority 1.

**Decision:** use `CombatSession` objects created from the current game state
instead of process-global mutable combat variables in the Django path.

**Rationale:** Django can serve multiple users in one process or multiple
workers. Process-global combat state lets one request overwrite another
player's fight. Rebuilding combat from serialized state keeps ownership with
the current session/save.

**Alternatives considered:**

- Keep module globals and rely on single-user demo: simpler, but unsafe and
  difficult to justify for Block 3.
- Store active combat in a separate database table: stronger audit trail, but
  larger schema change than required.

**Consequences:** the current fix is suitable for session/save isolation.
Future multiplayer or long-running combat analytics may justify a normalized
combat table.

## ADR-009 - Keep browser UI server-rendered with progressive JSON updates

**Status:** accepted.

**Decision:** keep Django templates plus inline JavaScript/fetch calls as the
main UI implementation.

**Rationale:** the application needs a small number of pages with dynamic
updates, not a complex client-side state manager. Server-rendered templates
keep auth, language and CSRF integration straightforward.

**Alternatives considered:**

- React/Vue/Svelte SPA: richer frontend architecture, but adds build tooling
  and client-side state complexity.
- Static HTML only: simpler, but insufficient for authenticated saves and
  live story/combat updates.

**Consequences:** CSS/JS duplication should be reduced later, but a frontend
framework migration is not necessary for the certification scope.
