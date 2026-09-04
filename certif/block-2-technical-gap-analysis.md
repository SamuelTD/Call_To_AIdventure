# Block 2 — Technical Coverage and Gap Analysis

## Purpose and scope

This document assesses the current technical coverage of certification Block 2:
**Integrate artificial intelligence models and services**.

Block 2 covers competencies C6 to C13. C6 is the technical and regulatory
watch competency. It is intentionally excluded from this analysis because it
will be handled as a separate piece of work. This document therefore focuses
on C7 to C13:

- selecting suitable AI services;
- configuring an AI service;
- exposing AI functions through a REST API;
- integrating that API into an application;
- monitoring the AI service;
- testing AI behavior;
- continuously delivering the AI component.

This is a technical gap analysis, not the final certification report. For each
competency it identifies what the application already demonstrates, what is
missing, what can be closed with focused work, and which evidence should be
retained.

## Executive assessment

Block 2 is one of the strongest technical areas of the project. The application
does not merely display an isolated chatbot: it orchestrates multiple AI
operations within a complete game flow.

```text
Django UI and JSON endpoints
            |
            v
        GameEngine
            |
            v
    LangGraph game workflow
       |              |
       |              +--> ChromaDB retrieval --> Ollama embeddings
       |
       +--> OpenAI service
              - story generation
              - choice generation
              - summarization
              - tool selection
              - goal evaluation
              - room evaluation
```

The code already provides structured outputs, tool calls, scoped RAG,
resilience rules, automated tests, Prometheus metrics and a Grafana dashboard.
The primary gaps are not a lack of AI integration. They are:

- no formal and measurable service-selection study;
- no dedicated, secured and documented model API;
- no repeatable AI quality evaluation dataset;
- incomplete model-specific monitoring and alerting;
- no continuous integration or delivery pipeline for the AI component.

### Remediation update — 2026-08-28

The statements below preserve the original gap assessment for traceability.
Focused remediation has since added:

- validated centralized AI runtime configuration and a safe service-check
  command;
- bounded embedding timeout/retries and privacy-aware logging;
- an authenticated, CSRF-protected, versioned AI turn API with ownership,
  server-choice validation, payload limits, quota and OpenAPI documentation;
- a versioned evaluation dataset, offline/live runner, thresholds, test strategy
  and requirements traceability;
- token/cost, structured-output and RAG metrics, SLOs, Prometheus alerts and
  Alertmanager configuration;
- a locked container artifact and GitHub Actions workflow for checks, coverage,
  RAG validation, evaluation and container smoke testing;
- delivery, promotion and rollback documentation.

Still external: executing two paid candidate-model benchmarks, confirming
current provider legal/retention terms, configuring protected repository and
notification secrets, publishing/deploying an immutable image, and retaining
live pipeline, alert and staging evidence. The older browser JSON endpoints
remain CSRF-exempt for compatibility; only the new `/api/v1` AI boundary should
be used as secured C9 evidence until those legacy routes are migrated.

### Status summary

| Competency | Current status | Realistic status after focused work |
|---|---|---|
| C6 — Technical and regulatory watch | Handled separately | Out of scope here |
| C7 — Identify suitable AI services | Partially covered | Coverable mostly through formal experiments and evidence |
| C8 — Configure an AI service | Strongly partially covered | Coverable |
| C9 — Expose an AI model through REST | Partially covered | Coverable |
| C10 — Integrate the AI API into an application | Strongly covered technically | Coverable with security and accessibility evidence |
| C11 — Monitor an AI model/service | Partially covered | Coverable |
| C12 — Automate AI model/service tests | Partially covered | Coverable |
| C13 — Continuously deliver the AI model/component | Not covered | Coverable after C12 |

## Existing technical assets

The following components should be retained and used as evidence:

- `src/agents/llm_runtime.py`: OpenAI client and AI chains;
- `src/agents/game_master_graph.py`: LangGraph state and AI orchestration;
- `src/agents/prompts/`: English and French prompt builders;
- `src/agents/schemas.py`: structured AI output schemas;
- `src/agents/tools.py`: model-callable game actions;
- `src/agents/llm_resilience.py`: timeout, retry, backoff and service-failure
  handling;
- `src/retrieval/`: RAG ingestion, ChromaDB queries, scoped retrieval and
  Ollama embeddings;
- `src/django/game/services/game_engine.py`: adapter between Django and the AI
  workflow;
- `src/django/game/views.py`: application endpoints and AI failure responses;
- `src/observability/metrics.py`: AI and application metrics;
- `monitoring/` and `compose.monitoring.yml`: Prometheus and Grafana stack;
- `src/django/game/tests.py`: tests for prompts, structured outputs, RAG,
  retries, tool calls and game-state behavior;
- `docs/rag-system.md`, `docs/monitoring.md` and
  `docs/django-app-architecture.md`: existing technical documentation.

---

## C6 — Organize technical and regulatory watch

C6 is part of Block 2, but it is explicitly set aside for a separate report and
workstream. It must not be forgotten when calculating final Block 2 readiness.

No C6 implementation plan is included in this document.

---

## C7 — Identify AI services matching the need

### What is covered by the application

The implemented architecture shows that several service categories were
identified correctly:

- a hosted generative model through OpenAI for narrative and decision tasks;
- structured outputs for choices and game-state evaluation;
- tool calling for deterministic game actions;
- Ollama's OpenAI-compatible embedding endpoint for local embeddings;
- ChromaDB as the vector store;
- LangGraph as the stateful orchestration layer;
- optional LangSmith tracing configuration.

The chosen services address real functional needs. OpenAI generates narrative
content, while the RAG subsystem constrains world knowledge. The application
also separates deterministic combat logic from probabilistic model output,
which is a defensible architectural decision.

### What is not covered

- There is no formal statement translating the commander's need into AI
  functions and measurable constraints.
- The repository contains no comparison of candidate services or models.
- There are no documented elimination criteria.
- Cost, latency, context capacity, output structure, multilingual behavior,
  data protection and service availability are not compared.
- There is no benchmark dataset used to compare candidate models.
- The decision to use hosted generation but local embeddings is not recorded in
  an architecture decision record.
- Expected request volume and budget are not estimated.
- Provider terms, data retention and geographic-processing implications are
  not summarized.

### What can become covered with limited work

This competency needs more experimentation and documentation than application
development:

1. Write a concise AI requirements specification. Define every AI function,
   expected input/output, response-time target, language, privacy constraint
   and acceptable failure behavior.
2. Create a small representative evaluation dataset containing story turns,
   choices, tool decisions, goal evaluations and RAG questions.
3. Compare at least two realistic generation models using the same dataset.
4. Compare relevant embedding options, or justify why only the current local
   embedding model is feasible.
5. Record objective results: schema-validity rate, task-success rate, latency,
   approximate cost and language quality.
6. Document discarded options and the reasons for rejection.
7. Create an architecture decision record for OpenAI, Ollama, ChromaDB and
   LangGraph.
8. Estimate demonstration and production-like monthly cost from measured
   request volume and token usage.

The application can keep the current services if the measurements support
them. C7 does not require replacing a functioning stack merely to show that
alternatives were considered.

### Evidence to retain

- AI requirements specification;
- candidate-service comparison matrix;
- versioned evaluation dataset;
- benchmark command and raw results;
- cost and latency calculations;
- decision records and rejection rationale;
- link between each application need and the selected AI function.

---

## C8 — Configure an AI service

### What is covered by the application

- The OpenAI model, API key and reasoning effort are environment-driven.
- Provider timeout and retries are configurable.
- Application-level retries use bounded exponential backoff and jitter.
- Transient HTTP status codes and error keywords are configurable.
- The application returns a controlled service-unavailable response when all
  attempts fail.
- Pydantic-backed structured outputs are used for choices, goal evaluation and
  room evaluation.
- The model receives explicit tools for combat, healing, damage and no-op game
  actions.
- Separate English and French prompts are available.
- Ollama host and embedding-model settings are configurable.
- RAG ingestion has reset, dry-run and collection options.
- Dependencies and main environment variables are documented.

### What is not covered

- Required settings are not validated centrally at application startup.
- Configuration errors can surface late, during the first request.
- Secret management is limited to a local `.env` convention.
- A checked-in safe `.env.example` now documents generation, retrieval,
  resilience, request-limit and cost-estimation settings without real secrets.
- Model parameters and prompt versions are not grouped in one explicit runtime
  configuration object.
- There is no environment matrix for development, test and production.
- There is no configurable budget, request quota or concurrency control.
- The embedding HTTP request has no explicit timeout or retry policy.
- Raw `print` calls are used instead of structured logging in AI and RAG paths.
- There is no configuration smoke test proving that each external service is
  reachable with the selected model.

### What can become covered with limited work

1. Introduce a validated settings layer for OpenAI, Ollama, Chroma and retry
   configuration.
2. Fail fast with a safe, clear message when a required setting is absent.
3. Add a safe `.env.example` with no real secrets.
4. Add explicit timeouts and retry behavior to the embedding request.
5. Replace diagnostic `print` statements with structured, privacy-aware logs.
6. Add a `check_ai_services` management command that verifies configuration,
   connectivity and model availability without exposing secrets.
7. Document development, test and production configuration profiles.
8. Record the chosen prompt/model configuration in evaluation results.
9. Add configurable request or cost limits appropriate to the application.
10. Add tests for invalid settings, missing credentials and unavailable
    providers.

### Evidence to retain

- environment-variable reference;
- safe example configuration;
- configuration validation tests;
- successful service-check output;
- screenshots of accessible services;
- dependency lock file;
- explanation of each selected parameter and its project constraint.

---

## C9 — Develop a REST API exposing an AI model

### What is covered by the application

- Django endpoints trigger AI-backed story turns and current-room narration.
- The view layer delegates AI work to `GameEngine`, keeping provider code out
  of HTTP controllers.
- JSON inputs are parsed and basic validation is performed.
- AI results are converted to JSON-serializable story, choice, state and error
  payloads.
- Session state provides continuity between calls.
- Authenticated users own their persistent saved games.
- Unavailable AI services produce an HTTP 503 response and do not persist a
  partially advanced game state.
- Endpoint behavior and ownership rules have automated tests.

### What is not covered

- A dedicated, versioned authenticated AI turn boundary now exists under
  `/api/v1`, with health and safe-configuration endpoints.
- `docs/block2/openapi.yaml` documents its endpoints, schemas, status codes,
  security schemes and an example.
- Model access is not protected by a consistent authentication policy.
- Several JSON endpoints use `csrf_exempt`, including AI-triggering writes.
- Anonymous callers can cause paid model invocations.
- There is no rate limiting, quota or request-size limit specific to AI calls.
- Error payloads are not standardized.
- The API does not expose model/configuration metadata suitable for
  reproducibility.
- There are no explicit prompt-injection or abuse controls.
- The echo/debug endpoint is not a real model endpoint and should not be
  presented as C9 evidence.

### What can become covered with limited work

Define the existing story-turn operation as a clear versioned API instead of
building a second application:

```text
POST /api/v1/games/{game_id}/turns/
GET  /api/v1/ai/health/
GET  /api/v1/ai/configuration/
```

Recommended work:

1. Define request, success and error schemas.
2. Publish an OpenAPI specification with examples.
3. Require an authenticated user for persistent games and define an explicit,
   limited guest policy if anonymous play is retained.
4. Restore CSRF protection for browser session authentication, or use a
   documented token mechanism for non-browser API clients.
5. Add per-user rate limits and maximum input sizes.
6. Validate choices against the server-side current choices instead of
   accepting arbitrary text where appropriate.
7. Standardize provider failure, validation, conflict and quota errors.
8. Expose only safe model metadata; never expose keys or sensitive prompts.
9. Add authentication, authorization, rate-limit and malformed-input tests.
10. Document prompt-injection boundaries and the fact that deterministic game
    rules remain server-controlled.

### Evidence to retain

- OpenAPI file and rendered documentation;
- endpoint and security architecture;
- example requests and responses;
- access-control and abuse-case tests;
- proof that unauthorized access is rejected;
- successful live API demonstration;
- documented security recommendations.

---

## C10 — Integrate an AI model or service API into an application

### What is covered by the application

This competency has strong implementation evidence:

- OpenAI is integrated into the active Django game, not a standalone demo.
- LangGraph coordinates multiple AI tasks and preserves application state.
- Model outputs drive stories, choices, goals, room progression and tool
  selection.
- Pydantic schemas constrain several model responses.
- Tool calls bridge probabilistic decisions to deterministic application code.
- RAG retrieves adventure-scoped character and location knowledge.
- The game degrades gracefully when retrieval returns no context.
- Retry and failure behavior is integrated into the browser flow.
- Game state is not persisted when a failed AI call leaves the turn incomplete.
- English and French interfaces and prompts are integrated.
- Automated tests isolate AI calls with mocks and validate application state.

### What is not covered

- The formal API contract and security gaps identified under C9 remain.
- There is no requirements-to-implementation traceability matrix.
- Accessibility has not been audited against a named standard.
- No end-to-end test exercises a controlled fake AI server through HTTP.
- Provider response changes are handled for some formats, but contract
  compatibility is not systematically tested.
- User-facing handling of unsafe or inappropriate generated content is not
  specified.
- No measured acceptance criteria demonstrate that the integrated AI meets the
  functional need.

### What can become covered with limited work

1. Complete the C9 API contract and security work.
2. Create a traceability table connecting AI requirements, endpoints, graph
   nodes, tests and acceptance criteria.
3. Add a fake OpenAI-compatible test service or HTTP mock to test the full
   integration boundary deterministically.
4. Add an accessibility audit and correct critical findings in the AI-driven
   user journey.
5. Define content-safety and user-error behavior.
6. Run and retain an end-to-end demonstration scenario covering story, RAG,
   structured choice, tool call and provider outage.
7. Measure response time and task-success targets defined for C7.

### Evidence to retain

- architecture and sequence diagrams;
- requirements traceability matrix;
- end-to-end test results;
- accessibility audit and corrections;
- demonstration script and screenshots;
- provider-outage demonstration;
- measured latency and functional acceptance results.

---

## C11 — Monitor an AI model or service

### What is covered by the application

- Prometheus counters track logical AI requests by operation and status.
- Provider attempts and retries are counted separately.
- A histogram measures logical AI request duration including retry delays.
- Browser-observed story-turn duration is measured.
- Application metrics cover games, turns, combats and outcomes.
- Grafana and Prometheus are reproducibly configured through Docker Compose.
- A provisioned dashboard is versioned in the repository.
- The documentation explains important queries and local installation.
- Metric labels intentionally avoid prompts, usernames, session identifiers
  and unbounded private values.

### What is not covered

- There are no defined service-level objectives or alert thresholds.
- Alerts and notifications are not configured.
- Token usage and estimated cost are not recorded.
- Structured-output validation failures are not counted explicitly.
- Tool-selection errors and fallback events are not first-class metrics.
- RAG retrieval latency, empty-context rate, distance and ingestion freshness
  are not monitored.
- There are no model-quality or task-success metrics.
- User feedback is not collected for a feedback loop.
- Logs are not structured or centralized.
- Dashboard and alert behavior are not tested automatically.
- The metrics endpoint and Grafana deployment need production access controls.

### What can become covered with limited work

1. Define a metric catalogue with purpose, type, labels, expected range and
   privacy classification.
2. Define measurable objectives for availability, latency, schema-validity
   rate and successful story-turn completion.
3. Add metrics for tokens, estimated cost, invalid structured responses, RAG
   latency, empty RAG results and service fallbacks.
4. Instrument evaluation success separately from transport success.
5. Add Prometheus alert rules and Alertmanager notifications for a local
   demonstration channel.
6. Add a minimal user rating or issue signal that can feed the evaluation
   dataset without storing private prompts as metric labels.
7. Replace `print` diagnostics with structured, redacted logs and correlation
   identifiers.
8. Protect monitoring endpoints in production documentation and configuration.
9. Add tests that assert metric increments and validate Prometheus rules.
10. Demonstrate one forced outage and one threshold-triggered alert.

### Evidence to retain

- metric and threshold catalogue;
- Prometheus alert-rule files;
- Alertmanager configuration with secrets excluded;
- versioned Grafana dashboard;
- screenshot of healthy metrics and a firing test alert;
- privacy analysis of metrics and logs;
- outage test results and incident timeline.

---

## C12 — Program automated tests for an AI model or service

### What is covered by the application

The current suite already includes valuable AI tests:

- prompt-language requirements;
- structured choice-output behavior;
- provider tool-call parsing across response formats;
- healing and damage tool normalization;
- transient failure retry and exhausted-retry behavior;
- preservation of state after failed generation;
- RAG scoping and retrieval caching;
- avoidance of unnecessary embedding calls for known locations;
- goal and room-completion transitions;
- end-state generation;
- metrics endpoint and metric-observation behavior.

The full Django suite contained 85 passing tests at the 2026-08-28 baseline,
before the Block 2 hardening tests were added. Most external AI
calls are mocked, which keeps tests deterministic and inexpensive.

### What is not covered

- There is no written AI test strategy or test-case catalogue.
- There is no versioned golden evaluation dataset.
- Generated text quality is not evaluated against defined criteria.
- There are no repeatable model-comparison or regression scores.
- RAG relevance is not evaluated on a question/expected-source dataset.
- Prompt injection, harmful output and malformed provider responses are not
  covered systematically.
- Timeout, rate-limit and concurrency behavior are not load-tested.
- Tests do not validate an actual AI service in a controlled optional stage.
- There is no coverage report or explicit minimum coverage threshold.
- The tests are not automatically executed on Git pushes or pull requests.

### What can become covered with limited work

Create two complementary test levels:

1. **Deterministic integration suite** — continue using mocks and fixtures to
   test schemas, state changes, provider errors, security and fallbacks.
2. **Versioned AI evaluation suite** — run representative cases against a
   configured model and store aggregate scores without committing secrets or
   uncontrolled private content.

The evaluation dataset should include:

- valid three-choice generation;
- correct tool selection;
- goal-completion classification;
- room-completion classification;
- required language and narrative viewpoint;
- RAG expected-source retrieval;
- refusal or safe handling of adversarial input;
- latency and schema-validity checks.

Recommended work:

1. Define pass/fail thresholds before executing the evaluation.
2. Implement a CLI producing JSON and Markdown evaluation reports.
3. Add fixtures for malformed, empty and changed provider responses.
4. Add tests for embedding timeout and unavailable Chroma/Ollama services.
5. Add prompt-injection and authorization tests.
6. Add coverage measurement and a realistic threshold.
7. Keep live-provider tests optional locally and scheduled or manually
   approved in CI to control cost.

### Evidence to retain

- AI test plan and case catalogue;
- versioned evaluation dataset;
- evaluation runner;
- threshold definitions;
- JSON/Markdown evaluation reports;
- unit/integration test and coverage output;
- documented separation between mocked and live-provider tests;
- before/after regression evidence for at least one model or prompt change.

---

## C13 — Create a continuous delivery chain for the AI component

### What is covered by the application

- Source code, prompts, schemas and RAG documents are stored in Git.
- Dependencies are declared in `pyproject.toml`.
- The RAG ingestion command is reproducible and supports validation-only dry
  runs.
- Automated tests already exist and can become CI quality gates.
- Monitoring configuration is versioned.
- Environment-based model configuration allows deployment-specific settings.

These are prerequisites, but they do not constitute continuous delivery.

### What is not covered

- A GitHub Actions workflow is now versioned for deterministic checks,
  container smoke testing and manually approved live evaluation. Executed
  pipeline evidence is still required.
- Tests and AI evaluations are not triggered automatically.
- There is no packaging step for the application or AI service layer.
- A versioned Dockerfile now defines an application artifact. Publishing the
  image and retaining its immutable registry digest still require deployment
  access.
- Prompt, model and evaluation-dataset versions are not recorded together.
- RAG ingestion is not validated as part of a delivery workflow.
- There is no test or staging environment.
- Secrets and environment approvals are not configured in a delivery platform.
- There is no deployment, rollback or release procedure.
- No evaluation report is attached to a release.

### What can become covered with focused work

Implement a CI/CD workflow in progressive stages:

```text
Pull request / push
        |
        +--> install locked dependencies
        +--> static checks
        +--> Django system check
        +--> deterministic tests + coverage
        +--> RAG dry-run validation
        +--> build application container
        +--> smoke-test container
        +--> publish versioned artifact after approval
        +--> optional AI evaluation stage
        +--> deploy to test environment after quality gates
```

Recommended work:

1. Retain the committed `uv.lock` dependency lock and verify frozen installs in
   CI.
2. Add a CI workflow triggered by pull requests and the main branch.
3. Run formatting/linting, Django checks, deterministic tests and coverage.
4. Run RAG schema/chunking validation without external embeddings.
5. Build a Docker image containing the active Django application.
6. Smoke-test health and a fake-provider AI turn inside the built artifact.
7. Publish artifacts only after all validation stages pass.
8. Add an optional or scheduled live AI evaluation with a strict budget.
9. Store model name, prompt revision, dataset revision and evaluation result as
   release metadata.
10. Document environment promotion, secret handling, rollback and debugging.

C13 overlaps technically with Block 3 C18 and C19, but the evidence must make
the distinction clear: C13 validates and versions the AI component, prompts,
RAG assets and model evaluation; C18/C19 concern the complete application and
its delivery.

### Evidence to retain

- versioned CI/CD workflow;
- screenshots and links for successful and failed pipeline runs;
- built artifact identifier;
- test, coverage, RAG validation and AI evaluation reports;
- release metadata connecting model, prompts and dataset versions;
- staging deployment proof;
- rollback and pipeline-debugging procedure.

---

## Recommended implementation plan

### Priority 1 — Formalize and secure the existing AI boundary

- define measurable AI requirements;
- validate runtime configuration at startup;
- add a safe example environment file;
- formalize the versioned REST contract;
- restore appropriate CSRF/authentication protection;
- add request limits and access-control tests.

This primarily strengthens C7, C8, C9 and C10.

### Priority 2 — Build the AI evaluation system

- create the representative evaluation dataset;
- define thresholds;
- implement the evaluation CLI and reports;
- add RAG relevance, safety and malformed-response cases;
- measure candidate models using the same protocol.

This primarily strengthens C7 and C12 and creates the foundation for C11 and
C13.

### Priority 3 — Complete model-specific observability

- add cost, token, schema-validity, RAG and task-success metrics;
- define service objectives and alert thresholds;
- add Alertmanager and one safe notification route;
- use structured, redacted logs;
- demonstrate forced failure and alert handling.

This primarily closes C11.

### Priority 4 — Add CI/CD for the AI component

- run deterministic tests and RAG validation on every change;
- build and smoke-test a versioned artifact;
- run budget-controlled AI evaluation at an appropriate trigger;
- attach evaluation and configuration metadata to releases;
- document promotion and rollback.

This primarily closes C13 and prepares Block 3 industrialization work.

## Definition of done for Block 2 technical work

Excluding the separately handled C6 workstream, Block 2 should be considered
technically ready for final report writing when:

- AI functions and measurable constraints are specified;
- candidate services have been compared on a versioned dataset;
- selected and rejected solutions are justified;
- all required AI settings are validated and documented;
- OpenAI, Ollama and Chroma connectivity can be checked reproducibly;
- AI functions are exposed through a versioned and documented REST contract;
- model-triggering operations have explicit authentication, authorization and
  abuse controls;
- the application demonstrates story, structured output, tool calling, RAG and
  graceful provider failure end to end;
- an AI test plan, evaluation dataset, runner and pass thresholds exist;
- model quality and RAG relevance can be measured repeatedly;
- AI latency, availability, schema failures, RAG behavior and cost are
  monitored;
- alert thresholds are configured and a test alert can be demonstrated;
- CI automatically runs deterministic AI tests and RAG validation;
- a versioned application/AI artifact is built and smoke-tested;
- releases identify the model, prompt, RAG dataset and evaluation revisions;
- deployment and rollback procedures are documented;
- C6 technical and regulatory watch evidence is completed in its separate
  workstream.

## Scope warning

The project should already be presented as a substantial AI integration, but
not yet as a fully industrialized MLOps implementation.

In particular:

- mocked AI tests demonstrate deterministic integration behavior, not model
  quality by themselves;
- Prometheus counters and latency histograms are a monitoring foundation, but
  not a complete model feedback loop without quality metrics and alerts;
- environment variables demonstrate configurability, but not complete secret
  management or deployment configuration;
- Django JSON endpoints demonstrate application integration, but not the full
  C9 API requirement until their contract and access controls are formalized;
- Git versioning and a reproducible local command do not constitute continuous
  delivery without an executed pipeline and a deliverable artifact.

The good news is that C8 and C10 require reinforcement rather than redesign.
C7, C11 and C12 mainly need formal experiments and targeted instrumentation.
C9 needs a security and API-contract pass. C13 is the only genuinely new
industrialization layer.
