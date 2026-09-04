# Block 2 AI test strategy

The project separates deterministic integration tests from live model evaluation.

## Quality gates

- Every commit: Django checks, unit/integration tests, coverage, OpenAPI parsing,
  RAG dry-run validation and offline evaluation-dataset validation.
- Manually approved or scheduled: `python -m evaluation.runner --live` using a
  restricted provider secret and explicit budget.
- Release threshold: 100% structured-schema validity and at least 90% total
  case success. Any security-boundary or authorization failure blocks release.

The versioned dataset is `evaluation/dataset.json`. Reports record the Git,
dataset, model and non-secret runtime configuration revisions. Live reports are
artifacts and are not committed by default.

## Coverage catalogue

The deterministic suite covers prompt language, schemas, tool parsing, retry
exhaustion, state preservation, RAG scope/cache, game transitions, ownership,
CSRF, malformed JSON, arbitrary-choice rejection, payload limits and quotas.
The evaluation dataset covers English/French choice constraints, expected RAG
sources, and adversarial input at the API boundary.

Provider transport success is not treated as model-quality success. Reviewers
should add representative cases before changing a prompt or model, capture a
baseline report, make the change, and retain the before/after reports.
