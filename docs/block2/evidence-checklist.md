# Block 2 evidence checklist

## Repository evidence now available

- [x] Requirements, measurable constraints, ADR and candidate protocol
- [x] Safe environment example, validated configuration and service-check CLI
- [x] Embedding timeout/retries and redacted active-path logs
- [x] Versioned AI API, OpenAPI, authentication, CSRF, ownership, limits and tests
- [x] Requirements-to-code-to-test traceability
- [x] Versioned evaluation dataset, runner, thresholds and test strategy
- [x] Token/cost, schema and RAG telemetry plus documented SLOs
- [x] Prometheus rules, Alertmanager template and provisioned Grafana dashboard
- [x] Locked dependencies, coverage gate, Docker artifact and CI workflow
- [x] Promotion, rollback and pipeline-debugging procedure

## Owner/external evidence still required

- [ ] Approve expected monthly request volume, budget and anonymous-play policy
- [ ] Run the same dataset against at least two generation candidates
- [ ] Record current provider price, retention, training-use and processing-region terms
- [ ] Perform human English/French quality and named-standard accessibility review
- [ ] Configure the protected `ai-evaluation` GitHub environment and secret
- [ ] Execute successful and intentionally failed CI runs and retain their links
- [ ] Publish the SHA-tagged image and retain its immutable digest
- [ ] Deploy to staging; retain health, story/RAG/tool/outage demonstration evidence
- [ ] Configure a secret-backed Alertmanager receiver and retain a firing-alert screenshot
- [ ] Record the final acceptance decision and any justified threshold exception

Do not present the legacy CSRF-exempt browser endpoints as C9 security evidence.
Use only the authenticated `/api/v1` AI endpoints until migration is complete.
