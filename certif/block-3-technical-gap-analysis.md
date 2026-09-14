# Block 3 — Technical Coverage and Gap Analysis

## Purpose and scope

This document assesses the current technical coverage of certification Block 3:
**Build an application integrating an artificial intelligence service**.

It covers competencies C14 to C21:

- C14 — analyze and model the application need;
- C15 — design and validate the technical framework;
- C16 — coordinate implementation in an agile and MLOps context;
- C17 — develop application components and interfaces;
- C18 — automate application tests through continuous integration;
- C19 — create a continuous delivery process for the application;
- C20 — monitor the application;
- C21 — diagnose and resolve technical incidents.

Unlike Block 2, Block 3 contains no technical-watch-only competency. C20 and
C21 are evaluated through the separate E5 incident case, but the current
project can still provide reusable monitoring, debugging and incident evidence.

This is a technical gap analysis, not the final certification report. It
separates existing application evidence, missing elements, realistic technical
improvements and evidence to retain.

## Executive assessment

Block 3 is the most mature application block. The project is already a real
multi-page Django application rather than a single AI demonstration. It
includes authentication, character creation, persistent saves, a narrative
game loop, deterministic combat, RAG-backed AI generation, bilingual UI,
automated tests and local observability.

```text
Browser
  |
  +--> Django pages and JSON endpoints
          |
          +--> authentication, sessions and persistent saves
          +--> character and adventure flows
          +--> GameEngine
                  |
                  +--> deterministic combat
                  +--> LangGraph + OpenAI + RAG
          +--> Prometheus metrics --> Grafana
```

The largest weaknesses are around engineering formalization and
industrialization rather than missing product functionality:

- the need, user journeys and acceptance criteria are not formally modeled;
- agile planning evidence is absent from the repository;
- security and accessibility need systematic audits and corrections;
- mutable global combat state is unsafe for concurrent users;
- tests are not executed by CI;
- the application is not packaged and continuously delivered;
- monitoring has no alerting or structured logging;
- no incident is documented from reproduction to verified resolution.

### Status summary

| Competency | Current status | Realistic status after focused work |
|---|---|---|
| C14 — Analyze and model the application need | Partially covered | Coverable largely through formalization and targeted audits |
| C15 — Design the technical framework | Strongly partially covered | Coverable |
| C16 — Coordinate agile implementation | Weakly covered | Coverable if real project-management evidence is maintained |
| C17 — Develop components and interfaces | Strongly covered technically | Coverable after security/accessibility/concurrency work |
| C18 — Continuous integration of tests | Not covered | Coverable |
| C19 — Continuous delivery of the application | Not covered | Coverable after C18 |
| C20 — Monitor the application | Partially covered | Coverable |
| C21 — Resolve technical incidents | Partially evidenced by Git history | Coverable with a formal incident exercise |

## Existing technical assets

- `src/django/call_to_aidventure/`: Django project configuration;
- `src/django/game/views.py` and `urls.py`: pages and JSON endpoints;
- `src/django/game/models.py` and migrations: accounts-related application
  persistence;
- `src/django/game/services/`: application service layer and game-state
  persistence;
- `src/django/game/templates/`: bilingual user interfaces;
- `src/agents/`: active AI workflow and prompts;
- `src/retrieval/`: active RAG subsystem;
- `src/combat/core.py`: deterministic combat rules;
- `src/utils/`: domain models and database adapters;
- `src/observability/metrics.py`: business, application and AI metrics;
- `monitoring/` and `compose.monitoring.yml`: local Prometheus/Grafana stack;
- `src/django/game/tests.py`: 72 currently passing automated tests;
- `README.md`: clean-install procedure;
- `docs/django-app-architecture.md`, `docs/rag-system.md` and
  `docs/monitoring.md`: detailed technical documentation;
- `architecture.drawio.png`: existing architecture illustration;
- Git history: incremental feature and corrective commits.

---

## C14 — Analyze and model the application need

### What is covered by the application

The implemented product makes the main need understandable:

- a player selects an adventure and creates a character;
- the application generates a contextual interactive story;
- the player selects proposed actions;
- the AI may trigger deterministic game tools and combat;
- authenticated players can maintain multiple saves and review finished games;
- the UI supports English and French;
- RAG restricts narrative knowledge to the selected adventure;
- failures of the external storytelling service preserve the current game.

The architecture documentation describes the active components, routes,
runtime flow, persistence model and known limitations. Pydantic and Django
models also provide partial formalization of application data.

### What is not covered

- There is no named commander, stakeholder map or project-context statement.
- Functional and non-functional requirements are not numbered or prioritized.
- There are no personas or accessibility-needs profiles.
- User journeys are described in prose but not modeled with a recognized
  formalism.
- User stories and acceptance criteria are not versioned.
- There is no requirements traceability matrix.
- Data models are not represented by a formal entity-relationship or Merise
  diagram.
- Accessibility objectives are not defined against RGAA or WCAG criteria.
- Security, privacy, performance, availability and cost requirements are not
  specified measurably.
- Constraints such as API budget, expected concurrency, hosting and supported
  browsers are not stated.
- There are no versioned wireframes or UI validation records.

### What can become covered with limited work

1. Write a concise project brief identifying the commander, users,
   stakeholders, objective, boundaries and constraints.
2. Create a numbered requirements catalogue covering functional and
   non-functional requirements.
3. Add personas, including at least one user with accessibility needs.
4. Model the main journeys: guest game, authenticated save/load, combat,
   victory/defeat, provider outage and account-data deletion.
5. Convert current behavior into user stories with testable acceptance
   criteria.
6. Produce an entity-relationship or Merise model for application data.
7. Define accessibility targets against a selected standard and level.
8. Define measurable response-time, security, availability and cost targets.
9. Create low-fidelity wireframes or preserve the implemented UI as a baseline,
   then document user review findings.
10. Build a traceability matrix connecting requirements to components, tests
    and demonstration steps.

This work should document genuine current behavior first. It should not invent
requirements that the application does not satisfy unless they are clearly
marked as planned.

### Evidence to retain

- project brief and stakeholder map;
- requirements catalogue;
- personas and user journeys;
- user stories with acceptance criteria;
- data model;
- wireframes and review notes;
- accessibility and security objectives;
- requirements-to-code/test traceability matrix.

---

## C15 — Design the technical framework

### What is covered by the application

- Django provides a coherent web framework with routing, templates, sessions,
  authentication, ORM and migrations.
- Application concerns are separated into views, services, domain utilities,
  AI workflow, retrieval, combat and observability.
- LangGraph is used for stateful AI orchestration.
- OpenAI, Ollama and ChromaDB have distinct responsibilities.
- SQLite supports the current local demonstration and Django persistence.
- Prometheus and Grafana provide a local observability proof of concept.
- Installation dependencies and environment variables are documented.
- Architecture, runtime flow and RAG behavior are documented in detail.
- The application is a working proof of concept with substantial automated
  test coverage.

### What is not covered

- Technical choices are described but rarely compared or justified against
  alternatives.
- There is no architecture decision record set.
- Deployment architecture is not defined.
- Scalability and concurrent-user assumptions are absent.
- The combat engine uses process-global mutable state, which conflicts with a
  multi-user server architecture.
- Two SQLite persistence paths are used without a complete data-ownership and
  lifecycle diagram.
- Security zones, trust boundaries and external data flows are not modeled.
- There is no threat model.
- Production configuration and operational dependencies are incomplete.
- No load or capacity test validates feasibility beyond local use.
- The proof-of-concept conclusion is not written against explicit success
  criteria.

### What can become covered with focused work

1. Create architecture decision records for Django, LangGraph, OpenAI, Ollama,
   ChromaDB, SQLite and Prometheus/Grafana.
2. Add C4-style data models and a deployment diagram.
3. Draw trust boundaries and external service/data flows.
4. Document development, test and target deployment environments.
5. Remove mutable global combat state by storing all combat state in the
   per-game serialized state or database.
6. Add a basic concurrent-session test proving that two users cannot affect
   each other's combat.
7. Run a modest load test on read-only and non-live-AI paths, then document the
   limits of AI-backed paths.
8. Complete production-ready settings using environment variables for secret
   key, debug mode, allowed hosts, secure cookies and HTTPS behavior.
9. Write a proof-of-concept conclusion showing which feasibility criteria pass
   and which remain out of scope.

### Evidence to retain

- logical, deployment and data-flow diagrams;
- architecture decision records;
- threat model and trust-boundary diagram;
- environment matrix;
- proof-of-concept success criteria and conclusion;
- concurrent-user and load-test results;
- technical-risk register.

---

## C16 — Coordinate technical implementation in an agile and MLOps context

### What is covered by the application

- Git history shows incremental features, fixes and refactoring.
- Commits generally identify the purpose of a change.
- The application evolved through visible technical stages: Django migration,
  RAG, resilience, character creation, objectives, monitoring and
  internationalization.
- Automated tests support iterative development.
- The code and documentation are kept in the same repository.

These are useful traces of iterative work, but Git history alone does not prove
agile project coordination.

### What is not covered

- There is no product backlog in the repository or exported from a project
  tool.
- No sprint or iteration goals are recorded.
- Tasks are not consistently linked to issues, acceptance criteria or commits.
- Roles, responsibilities and stakeholders are not documented.
- There is no definition of ready or definition of done.
- Planning, review and retrospective evidence is absent.
- Technical risks, dependencies and impediments are not tracked formally.
- There are no collaborative decision or meeting records.
- MLOps-specific work such as prompt/evaluation changes is not tracked through
  a defined lifecycle.

### What can become covered with ongoing work

This competency cannot be recreated credibly in one final document. It needs a
real, lightweight process from now on:

1. Create a backlog containing the certification gaps from all three block
   analyses.
2. Organize work into short iterations with explicit objectives.
3. Write acceptance criteria before implementing each item.
4. Link branches, commits and pull requests to tracked tasks.
5. Define ready and done, including documentation, tests, security and evidence
   capture.
6. Maintain a risk and decision log.
7. Record short planning, review and retrospective notes.
8. Track model, prompt, RAG and evaluation changes as MLOps work items.
9. Use pull requests, even as a solo project, to preserve review evidence and
   quality-gate results.
10. Export or screenshot the project board periodically for the report.

The process should remain proportional to a solo school project. A simple
board and short Markdown records are sufficient if they are real and
consistent.

### Evidence to retain

- backlog and project-board exports;
- iteration goals and outcomes;
- user stories and acceptance criteria;
- issue/commit/pull-request links;
- definitions of ready and done;
- risk and decision logs;
- review and retrospective notes;
- examples of feedback changing implementation priorities.

---

## C17 — Develop application components and interfaces

### What is covered by the application

This is the strongest Block 3 competency. The project includes:

- multiple server-rendered pages and dynamic JSON-driven interactions;
- signup, login and logout;
- user-owned persistent saves and character templates;
- generic character templates for guests;
- adventure selection and character creation;
- narrative turns and AI-generated choices;
- current-room and goal progression;
- deterministic combat, victory and defeat flows;
- session persistence for guests;
- database persistence for authenticated users;
- English and French UI and AI behavior;
- service-unavailable handling that preserves game state;
- RAG integration with adventure scoping;
- domain validation through Django forms and Pydantic models;
- automated unit, service and endpoint tests;
- Git versioning and installation documentation.

The templates already include useful accessibility foundations such as
language attributes, explicit form labels, some ARIA tab semantics and image
alternative text.

### What is not covered

#### Security

- A hard-coded insecure Django secret key is committed.
- `DEBUG` is hard-coded to `True`.
- Numerous write endpoints use `csrf_exempt`.
- AI-triggering endpoints have no rate limit or cost quota.
- There is no systematic OWASP Top 10 review or automated security scan.
- Production cookie, HTTPS, HSTS and proxy settings are absent.
- Debug endpoints need an explicit production exclusion strategy.
- User-provided and AI-generated content boundaries need a documented XSS and
  prompt-injection analysis.

#### Concurrency and reliability

- Combat uses mutable module-level global state and is not safe for concurrent
  users or multiple server workers.
- The singleton engine and graph runtime use mutable global objects that need a
  thread-safety review.
- Long synchronous AI calls occupy Django request workers.
- There is no idempotency or duplicate-request strategy for story turns.

#### Accessibility

- No RGAA/WCAG audit has been performed.
- Dynamic status and story updates are not consistently announced through
  live regions.
- Keyboard behavior of custom tab interfaces is not proven.
- Focus management after navigation, errors and dynamic updates is not
  documented.
- Color contrast and zoom/reflow have not been measured.
- Automated and manual accessibility tests are absent.
- Technical documentation itself has not been reviewed for accessibility.

#### Eco-design and maintainability

- No eco-design assessment or budget is defined.
- CSS and JavaScript are duplicated inside large templates.
- Repeated polling/calls and AI request cost are not assessed from an
  eco-design perspective.
- Several modules use diagnostic `print` calls.

### What can become covered with focused work

1. Move all production-sensitive settings to validated environment variables.
2. Restore CSRF protection and send CSRF tokens from browser requests.
3. Add rate limits, request-size validation and authorization checks.
4. Remove global combat state and make the game state request/session scoped.
5. Test isolation between two concurrent authenticated sessions.
6. Run a threat-model review and an OWASP-oriented automated/manual audit.
7. Add dependency and static security scanning to CI.
8. Perform an accessibility audit with automated tools and keyboard/screen
   reader manual checks.
9. Add live regions, focus management and complete tab keyboard semantics.
10. Extract common frontend assets and remove avoidable duplication.
11. Define simple eco-design measures: reduce unnecessary LLM calls, cache
    retrieval, compress/minify static assets and measure page weight.
12. Add end-to-end browser tests for the principal user journeys.

### Evidence to retain

- requirement-to-component traceability;
- screenshots and end-to-end journey tests;
- ownership and concurrent-session tests;
- threat model and security-audit report;
- dependency/static scan reports;
- accessibility audit, corrections and before/after evidence;
- eco-design checklist and measurements;
- clean-install documentation and test output.

---

## C18 — Automate application tests with continuous integration

### What is covered by the application

- The Django test suite currently contains 72 passing tests.
- Tests cover authentication, authorization, saves, templates, game state,
  combat, RAG, AI failures, tools, objectives, localization and metrics.
- External AI calls are usually mocked, keeping the main suite deterministic.
- `manage.py check` currently completes successfully.
- Ruff is declared as a project dependency.
- The repository already has commands suitable for automation.

### What is not covered

- No continuous-integration workflow is versioned.
- Tests do not run automatically on push or pull request.
- There is no dependency cache or locked reproducible environment enforced by
  CI.
- Linting and formatting are not configured as quality gates.
- There is no coverage measurement or threshold.
- No browser end-to-end tests are run.
- Database migration checks are not automated.
- Security and accessibility checks are absent.
- Pipeline triggers, variables and failure procedures are not documented.

### What can become covered with limited work

Create one CI workflow for the complete application:

```text
Pull request / main-branch push
        |
        +--> install locked Python dependencies
        +--> lint and static checks
        +--> Django system and migration checks
        +--> unit/integration tests + coverage
        +--> RAG dry-run validation
        +--> security checks
        +--> build application artifact
        +--> browser smoke test
```

Recommended work:

1. Select GitHub Actions or the actual remote repository's CI system.
2. Commit workflow configuration and dependency lock data.
3. Run Ruff, `manage.py check`, migration consistency checks and tests.
4. Generate a coverage report with a realistic initial threshold.
5. Add at least one browser smoke test for signup/start/play using a fake AI
   provider.
6. Add dependency and Django deployment checks.
7. Add an automated accessibility smoke scan for major pages.
8. Document triggers, required variables, local reproduction and debugging.
9. Configure branch protection or equivalent quality-gate policy if available.

C18 can share the workflow introduced for Block 2 C13. The evidence should
show that this stage validates the whole application, not only AI assets.

### Evidence to retain

- versioned workflow file;
- successful and intentionally failed pipeline runs;
- test and coverage reports;
- lint, migration, security and accessibility results;
- branch quality-gate configuration;
- CI user and debugging documentation.

---

## C19 — Create a continuous delivery process for the application

### What is covered by the application

- The repository has a reproducible local installation procedure.
- Dependencies are declared.
- Database setup and migrations are scripted.
- A `/health` endpoint exists.
- Monitoring services are already containerized and configured through Docker
  Compose.
- Environment variables configure external services and selected runtime
  behavior.

These are delivery prerequisites, not a continuous delivery chain.

### What is not covered

- The Django application has no Dockerfile or other versioned package format.
- CI does not build or test a delivery artifact.
- There is no test or staging environment.
- There is no automated deployment or environment promotion.
- Production secrets and configuration are not managed.
- Static-file serving and production WSGI/ASGI execution are not defined.
- Database migration and rollback procedures are absent.
- No release numbering, changelog or artifact retention is defined.
- No post-deployment health verification exists.
- No rollback has been demonstrated.

### What can become covered with focused work

1. Create a production-oriented Dockerfile for the active Django application.
2. Add a Compose file for application, database and monitoring in a test
   environment, or document a chosen platform deployment.
3. Use a production server and explicit static-file strategy.
4. Build and smoke-test the exact container artifact in CI.
5. Publish immutable versioned images only after validation succeeds.
6. Deploy automatically to a test environment after an approval or protected
   branch event.
7. Apply migrations through a controlled release step.
8. Run post-deployment health and browser smoke checks.
9. Document secrets, backup, migration rollback and application rollback.
10. Record release metadata and generate a concise changelog.

The same artifact should be promoted between environments. Rebuilding a
different image for deployment would weaken reproducibility evidence.

### Evidence to retain

- Dockerfile and deployment configuration;
- versioned CI/CD workflow;
- immutable artifact identifier;
- staging deployment URL or local equivalent;
- packaging and deployment logs;
- post-deployment checks;
- database and application rollback demonstration;
- release and debugging procedure.

---

## C20 — Monitor an AI application

### What is covered by the application

- Django exposes framework and custom metrics through `/metrics`.
- Metrics cover games started, turns, combat actions/results, adventure
  outcomes and AI behavior.
- Browser-observed story-turn latency is recorded.
- Prometheus scrapes the application.
- Grafana is provisioned with a versioned project dashboard.
- Monitoring installation, verification and privacy constraints are
  documented.
- Metric labels avoid usernames, prompts, session IDs and exception text.
- Prometheus retains local data for a configured period.

### What is not covered

- Application service-level indicators and objectives are not formally
  defined.
- No warning or critical thresholds are documented.
- Alert rules and notification delivery are absent.
- Application logging is not structured or centralized.
- Unhandled exceptions, HTTP error rates and database failures do not have
  dedicated project dashboards or alerts.
- Health checking only reports a static success response; it does not verify
  dependencies or readiness.
- No synthetic user journey is monitored.
- No operational runbook explains how to investigate each alert.
- Monitoring configuration is local-development oriented and not secured for
  production.
- There is no automated validation of dashboards or alert rules.

### What can become covered with focused work

1. Define application indicators for availability, HTTP errors, latency,
   database health, AI failures and successful game turns.
2. Define warning/critical thresholds and their rationale.
3. Add Prometheus alert rules and Alertmanager.
4. Configure a safe demonstration notification destination.
5. Replace `print` diagnostics with structured redacted logging.
6. Add correlation IDs so one browser request can be followed through game,
   AI and retrieval operations without logging personal content.
7. Add readiness checks for database access and required configuration, while
   keeping a lightweight liveness endpoint.
8. Add a synthetic smoke journey or scheduled health probe.
9. Create an operational dashboard and runbook linking alerts to diagnostic
   queries and first actions.
10. Test rules with `promtool` and demonstrate at least one firing alert.

C20 can reuse the model-specific monitoring developed for Block 2 C11. C20
must additionally cover the web application, database and full user journey.

### Evidence to retain

- metric/SLO/threshold catalogue;
- versioned alert rules and Alertmanager configuration;
- dashboards and screenshots;
- structured-log examples with redaction proof;
- readiness and synthetic-check results;
- alert notification demonstration;
- operational runbook;
- monitoring installation and security documentation.

---

## C21 — Diagnose and resolve technical incidents

### What is covered by the application

- Git history contains real corrective commits.
- The test suite includes regression cases for previously fragile behavior,
  including AI response formats, unavailable services, save persistence and
  combat restoration.
- Retry behavior produces controlled failure instead of corrupting saved game
  state.
- Metrics provide some evidence for investigating latency and provider
  failures.
- The architecture documentation records several known technical risks.

This is useful source material, but the repository does not yet contain a
complete incident-resolution record.

### What is not covered

- There is no versioned incident ticket or report.
- No incident contains exact symptoms, timestamp, environment and impact.
- Reproduction steps and initial evidence are not preserved.
- Root-cause analysis is not formalized.
- Debugging commands and hypotheses are not documented chronologically.
- A corrective commit is not explicitly linked to a report and regression
  test.
- There is no before/after monitoring evidence.
- No prevention or follow-up actions are tracked.
- The limited logging system makes realistic diagnosis harder than it should
  be.

### What can become covered with limited work

Use a real, bounded application defect as the E5 preparation exercise. The
global combat-state concurrency issue is a strong candidate because it is
reproducible, technically meaningful and connected to the application design.
Another valid candidate is a controlled AI-provider outage, but it may overlap
too heavily with existing resilience behavior.

Recommended incident workflow:

1. Open an incident issue with environment, version, symptoms, expected
   behavior, impact and severity.
2. Reproduce the problem with two isolated users or workers.
3. Preserve failing test output, relevant logs and metrics.
4. List diagnostic hypotheses and the commands used to test them.
5. Identify the root cause and explain why the architecture allowed it.
6. Implement the smallest complete correction on a linked branch.
7. Add a regression test that fails before and passes after the fix.
8. Run the complete test and CI pipeline.
9. Verify behavior through the UI and monitoring.
10. Merge through a pull request and write a short post-incident review with
    preventive follow-up actions.

The certification evidence should remain authentic. Do not deliberately ship
a defect to production. A reproducible defect in a development branch or
controlled test environment is sufficient.

### Evidence to retain

- incident ticket and timeline;
- exact reproduction procedure;
- failing logs, metrics and test;
- hypothesis and root-cause analysis;
- linked branch, commits and pull request;
- regression test and full test output;
- before/after demonstration;
- resolution procedure and preventive actions.

---

## Recommended implementation plan

### Priority 1 — Secure the current application architecture

- externalize production settings and secrets;
- restore CSRF protection;
- add rate limiting and input-size controls;
- eliminate global combat state;
- test concurrent-session isolation;
- create a threat model and address critical OWASP findings.

This primarily strengthens C15 and C17 and creates a strong candidate incident
for C21.

### Priority 2 — Formalize requirements and project execution

- create the project brief, requirements, personas and user journeys;
- model application data and deployment;
- build the traceability matrix;
- create and use a real backlog with iterations and acceptance criteria;
- record decisions, risks, reviews and retrospectives.

This primarily closes C14, C15 and C16.

### Priority 3 — Complete product quality

- perform security and accessibility audits;
- fix critical accessibility issues and add automated checks;
- add browser end-to-end tests;
- document eco-design choices and reduce avoidable calls/duplication.

This primarily closes C17.

### Priority 4 — Implement one shared CI/CD system

- run static checks, migrations, tests, coverage, RAG validation and security
  checks;
- build an immutable application container;
- smoke-test the container;
- deploy the same artifact to a controlled test environment;
- verify health and document rollback.

This closes C18 and C19 and should reuse Block 2 C13 work.

### Priority 5 — Complete operations and incident evidence

- add application SLOs, alert rules and structured logging;
- add readiness and synthetic checks;
- write operational runbooks;
- reproduce, resolve and document one real technical incident end to end.

This closes C20 and C21.

## Definition of done for Block 3

Block 3 should be considered technically ready for final report writing when:

- the commander, users, constraints and application objectives are explicit;
- functional and non-functional requirements have measurable acceptance
  criteria;
- user journeys, data model and interfaces are formally modeled;
- requirements are traceable to implementation and tests;
- architecture choices and proof-of-concept conclusions are justified;
- deployment, trust boundaries and technical risks are documented;
- a real backlog and iteration history demonstrate project coordination;
- critical settings are production-safe and secrets are externalized;
- state is isolated between concurrent users;
- CSRF, authorization, rate limiting and main OWASP risks are addressed;
- an accessibility audit has been performed and critical failures corrected;
- core business and access-control components have automated tests;
- CI runs application tests and quality gates automatically;
- CI builds and smoke-tests an immutable delivery artifact;
- that artifact can be delivered to a controlled test environment;
- database and application rollback procedures are proven;
- application indicators, thresholds, alerts and runbooks exist;
- structured logs support diagnosis without exposing personal or prompt data;
- one incident has been reproduced, diagnosed, fixed, tested, versioned and
  documented from beginning to end.

## Scope and overlap warning

Several improvements contribute to more than one competency. They should be
implemented once and referenced from the relevant evidence:

- the shared CI workflow supports Block 2 C13 and Block 3 C18;
- the same built container and environment promotion support Block 2 C13 and
  Block 3 C19, with different emphasis;
- AI metrics support Block 2 C11, while web/database/user-journey metrics
  support Block 3 C20;
- the AI API security work supports Block 2 C9/C10 and Block 3 C17;
- requirements and acceptance criteria support C14, C15, C16 and C17;
- a concurrency correction can support C15, C17 and C21.

The application should already be described as functionally substantial and
well beyond a basic proof of concept. It should not yet be described as
production-ready because the current hard-coded development settings, CSRF
exemptions, global combat state, absence of CI/CD and absence of alerting are
material engineering gaps.

Most of the product behavior needed for C17 already exists. C14 to C16 require
formalization and sustained project evidence. C18 and C19 are the main new
industrialization layer. C20 extends the monitoring foundation, while C21 can
be completed through one carefully documented real correction.
