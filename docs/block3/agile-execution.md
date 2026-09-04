# Block 3 agile and MLOps execution record

## Working agreement

This project uses a lightweight solo-project process. Evidence should be real,
short and maintained as work happens.

## Roles

| Role | Person/source | Responsibility |
|---|---|---|
| Product owner | Owner validation required | Prioritize scope, validate requirements, accept trade-offs |
| Developer | Solo developer with Codex support | Implement, test, document and keep evidence current |
| Evaluator | Certification jury/evaluator | Review evidence against competencies |
| Operator | Same as developer until hosting exists | Run checks, monitor, diagnose incidents |

## Definition of ready

A work item is ready when:

- the user need or technical gap is written in one sentence;
- acceptance criteria are testable;
- impacted components are identified;
- security, accessibility and data ownership risks are considered;
- required credentials or external services are available or mocked;
- evidence to retain is named.

## Definition of done

A work item is done when:

- implementation or documentation is committed in the repository;
- relevant tests/checks pass locally;
- requirement traceability is updated when behavior changes;
- security-sensitive settings are not committed as secrets;
- user-facing behavior is manually checked when templates/routes change;
- residual risks are recorded instead of hidden;
- the item has a short review note.

## Product backlog

| ID | Priority | Item | Competencies | Acceptance criteria | Status |
|---|---|---|---|---|---|
| B3-01 | P1 | Externalize production settings and secrets | C15, C17 | Non-debug mode requires secret and allowed hosts; deploy check passes | Done |
| B3-02 | P1 | Restore CSRF on browser JSON POSTs | C17 | Enforced-CSRF test rejects missing token; templates send token | Done |
| B3-03 | P1 | Add body-size limits and AI quotas | C17, C20 | Oversized JSON returns 413; repeated AI route returns 429 | Done |
| B3-04 | P1 | Remove process-global combat state from Django path | C15, C17, C21 | Concurrent session-state test proves isolation | Done |
| B3-05 | P1 | Create initial threat model | C15, C17 | Assets, trust boundaries, OWASP review and residual risks documented | Done |
| B3-06 | P2 | Create project brief and stakeholder map | C14 | Commander/users/scope/constraints written and owner validations listed | Done |
| B3-07 | P2 | Number functional and non-functional requirements | C14, C17 | Requirements have IDs, priorities and acceptance criteria | Done |
| B3-08 | P2 | Model personas and user journeys | C14 | Guest, authenticated, combat, outage and deletion journeys documented | Done |
| B3-09 | P2 | Model data ownership and deployment | C15 | ERD, data ownership, deployment and environment matrix documented | Done |
| B3-10 | P2 | Create architecture decision records | C15 | Main technical choices list alternatives and consequences | Done |
| B3-11 | P2 | Build traceability matrix | C14-C17 | Requirements map to components, tests and demo evidence | Done |
| B3-12 | P2 | Maintain real iteration/review notes | C16 | Each future iteration has goal, outcome and retrospective note | To do |
| B3-13 | P3 | Accessibility audit and critical fixes | C17 | Automated scan plus keyboard/manual checks; critical issues fixed | Partial |
| B3-14 | P3 | Security scan and critical fixes | C17, C18 | Dependency/static checks run and critical findings addressed | To do |
| B3-15 | P3 | Browser end-to-end tests | C17, C18 | Principal guest/auth/combat flows covered with fake AI provider | Partial |
| B3-16 | P3 | Eco-design baseline | C17 | Page weight, repeated calls and avoidable AI calls measured | Partial |
| B3-17 | P4 | CI quality gate | C18 | Workflow runs lint, checks, migrations, tests and coverage | Done |
| B3-18 | P4 | Build immutable app container | C19 | CI builds and smoke-tests exact artifact | Done |
| B3-19 | P4 | Delivery and rollback procedure | C19 | Staging/local-equivalent deploy and rollback demonstrated | Partial |
| B3-20 | P5 | SLOs, alerting and runbooks | C20 | Alert rules, notification demo and diagnostic runbooks exist | To do |
| B3-21 | P5 | Formal incident exercise | C21 | Ticket, reproduction, root cause, fix, regression and postmortem exist | To do |

## Iteration plan

### Iteration 1 - Secure current application

Goal: remove the largest production-safety risks in the active Django app.

Items: B3-01 to B3-05.

Outcome: completed in repository. Tests and deploy check pass locally.

Review note: CSRF, body limits, AI route quotas and combat isolation now have
automated regression coverage. Remaining risks are target-hosting and full
manual audits.

### Iteration 2 - Formalize requirements and architecture

Goal: make C14/C15 evidence explicit and traceable.

Items: B3-06 to B3-11.

Outcome: completed in repository. Owner validations remain open where external
truth is required.

Review note: documentation describes current behavior first and marks planned
or owner-dependent evidence explicitly.

### Iteration 3 - Product quality

Goal: improve accessibility, security scan coverage, browser journeys and
eco-design measurements.

Items: B3-13 to B3-16.

Outcome: automated template accessibility checks, dynamic-focus corrections,
ARIA tab fixes, HP progressbar semantics, a fake-AI guest smoke journey and an
eco-design baseline were added. Manual accessibility checks and external
security tooling remain open.

Planned remaining checks:

- automated accessibility scan on principal pages;
- manual keyboard walkthrough;
- dependency/static security scan;
- browser smoke test with mocked AI;
- page weight and AI call count baseline.

### Iteration 4 - Industrialization

Goal: add CI/CD and delivery artifact evidence.

Items: B3-17 to B3-19.

Outcome: a GitHub Actions workflow, production-oriented Dockerfile, container
entrypoint, local delivery compose file and CI/CD delivery procedure were
versioned. The image was built locally and smoke-tested successfully on
`/health`.

Planned remaining checks:

- CI workflow passes and fails intentionally once;
- repository branch protection is configured;
- image registry publishing is configured;
- staging deployment and rollback are demonstrated on the selected platform.

### Iteration 5 - Operations and incident

Goal: complete monitoring and incident evidence.

Items: B3-20 to B3-21.

Planned checks:

- alert rule validation;
- demo alert notification;
- documented incident based on a real bounded defect or controlled outage.

## Risk register

| ID | Risk | Impact | Likelihood | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | AI provider outage stops story turns | High | Medium | retry policy, 503 response, unchanged state | Developer |
| R-02 | Provider cost spike from repeated turns | Medium | Medium | rate limits, future token/cost dashboard | Owner/developer |
| R-03 | Target hosting not selected | Medium | High | document target model, keep local equivalent evidence | Owner |
| R-04 | SQLite is insufficient for public concurrency | Medium | Medium | use SQLite only for demo or migrate to PostgreSQL | Owner |
| R-05 | Accessibility defects remain undiscovered | Medium | High | automated and manual audit in Priority 3 | Developer/owner |
| R-06 | Graph runtime thread-safety issue under load | High | Medium | load/concurrent tests and worker review | Developer |
| R-07 | Secrets accidentally committed | High | Low | env variables, `.env.example`, git review before commit | Developer |
| R-08 | Monitoring exposes personal content | High | Low | avoid PII labels, redact logs, review dashboards | Developer |
| R-09 | Documentation drifts from implementation | Medium | Medium | update traceability as part of DoD | Developer |

## Decision log

| Date | Decision | Link |
|---|---|---|
| 2026-09-03 | Keep Django as active browser app and Gradio as legacy only | `docs/block3/architecture-decisions.md` |
| 2026-09-03 | Use per-state combat sessions for Django combat isolation | ADR-008 |
| 2026-09-03 | Keep local Markdown process for agile evidence | This file |

## Review and retrospective template

Copy this section for each future iteration.

```text
Iteration:
Dates:
Goal:
Completed items:
Tests/checks run:
Evidence retained:
What changed after review:
What slowed us down:
Next adjustment:
```

## MLOps change tracking rule

Any change to prompts, model/provider config, RAG chunking, retrieval scope or
evaluation thresholds should be tracked as a backlog item with:

- changed file(s);
- reason for change;
- expected effect;
- evaluation or regression check;
- risk to cost, privacy or language quality.
