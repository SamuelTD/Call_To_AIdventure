# AI component delivery and rollback

The `Block 2 AI component` workflow locks dependencies, lints current code,
runs Django checks and tests with a 55% minimum coverage gate, validates RAG
documents without embeddings, validates the versioned evaluation dataset, and
builds and smoke-tests an immutable image tagged with the Git SHA.

Live evaluation is manual, protected by the `ai-evaluation` GitHub environment,
and requires `OPENAI_API_KEY`. Set `OPENAI_MODEL` as an environment variable.
This prevents pull requests from spending provider budget or accessing secrets.

## Promotion

1. Require the deterministic and container jobs on the protected main branch.
2. Review the evaluation artifact and its model, prompt, dataset and Git metadata.
3. Publish the exact SHA-tagged image to the selected registry after approval.
4. Deploy that immutable digest to staging and run the API health/outage demo.
5. Promote the same digest to production; do not rebuild it.

## Rollback

Keep at least the previous known-good image digest and its release metadata.
Rollback means redeploying that digest, restoring the matching environment
configuration, and re-running health and smoke checks. RAG collection changes
must use a versioned collection name; switch the configured collection back
instead of destructively rebuilding it during an incident.

Deployment credentials, registry publishing, staging URLs and approval rules
are intentionally external to the repository and must be configured by its
owner. Retain successful/failed workflow links, artifact digest, alert timeline
and staging screenshots as certification evidence.
