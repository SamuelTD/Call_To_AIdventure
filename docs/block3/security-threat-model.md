# Block 3 security threat model

## Scope

This threat model covers the active Django application, server-rendered pages,
JSON endpoints, session-backed game state, authenticated save games, the AI
story turn flow, the read-only dataset database, and local Prometheus/Grafana
monitoring.

It does not cover a public cloud provider configuration, DNS, TLS certificate
management, or third-party account security because no target hosting account
is versioned in this repository.

## Assets

- User accounts and Django session cookies.
- User-owned save games and character templates.
- Game state stored in Django sessions and `SaveGame.state`.
- AI provider API key and runtime configuration.
- Prompt, choice and retrieval inputs sent to the AI workflow.
- Monitoring metrics exposed by `/metrics`.
- Read-only monster/adventure dataset content.

## Trust boundaries

```text
Browser
  | HTTPS in target deployment
  v
Django views and CSRF/session middleware
  | internal Python calls
  v
GameEngine, combat engine, LangGraph workflow
  | local filesystem / SQLite
  v
Application DB and read-only dataset DB
  |
  +--> External OpenAI-compatible provider
  +--> Local Ollama / ChromaDB services when configured
  +--> Prometheus scrape of /metrics
```

## Main threats and current controls

| Area | Threat | Current control |
|---|---|---|
| Secrets | Production `SECRET_KEY` committed or missing | `DJANGO_SECRET_KEY` is required when `DJANGO_DEBUG=false`; development fallback is explicit |
| Debug exposure | Debug mode accidentally enabled in production | `DJANGO_DEBUG` controls debug; dev account dashboard is disabled unless debug and loopback |
| Host header | Untrusted host accepted in production | `DJANGO_ALLOWED_HOSTS` is required when `DJANGO_DEBUG=false` |
| CSRF | Cross-site POST against game, saves or templates | Application JSON POST views use Django CSRF middleware; browser fetch calls send `X-CSRFToken` |
| Session isolation | One user's combat mutates another user's fight | Django `GameEngine` uses per-state `CombatSession` objects instead of module-level combat globals |
| Authorization | User loads/deletes another user's data | Save and template mutations filter by `request.user` |
| Input size | Oversized JSON body consumes memory or worker time | JSON POST helper rejects bodies above `MAX_JSON_BODY_BYTES` |
| Cost abuse | Repeated AI turns burn provider quota | AI-start, AI-step and current-room endpoints are rate-limited per user/session |
| XSS | AI or user content rendered as HTML | Main dynamic content is assigned through `textContent`; Django templates auto-escape server variables |
| Prompt injection | Retrieved/user text manipulates tool policy | RAG is scoped by adventure/location; final provider hardening still needs a dedicated AI security review |
| Monitoring privacy | Metrics leak personal data or prompts | Metric labels avoid usernames, prompts, session IDs and raw exception text |

## OWASP-oriented review

- Broken access control: save games and character templates are user-scoped;
  continue testing direct object references when new endpoints are added.
- Cryptographic failures: production secret and secure cookie settings are
  environment-driven; deployment must provide HTTPS.
- Injection: SQL access in monster lookup uses parameter binding; AI prompt
  injection remains a model-specific risk to track separately.
- Insecure design: combat state isolation has been corrected for the Django
  path; legacy Gradio modules still keep compatibility wrappers and are out of
  production scope.
- Security misconfiguration: non-debug mode requires key host variables and
  enables secure cookies/HSTS defaults.
- Vulnerable components: dependency scanning should be added in CI.
- Identification/authentication failures: Django auth and password validators
  are used; account lockout is not implemented.
- Software/data integrity failures: no signed release artifact exists yet.
- Logging/monitoring failures: structured application logging and alerting are
  planned in C20.
- SSRF: no user-provided outbound URL fetch is exposed by the active Django UI.

## Residual risks

- The global `GameEngine` singleton still contains LangGraph graph objects.
  The graph runtime should be reviewed under threaded/multi-worker load.
- Long synchronous AI calls can occupy Django workers. A production deployment
  should use background jobs, async workers, or strict upstream timeouts.
- Rate limiting currently uses Django cache and is suitable for local/test
  evidence. A multi-instance deployment should use a shared cache such as Redis.
- Debug and legacy Gradio code must stay excluded from production routing.
- Full accessibility and security audits are still required for C17 evidence.

## Evidence added by Priority 1

- CSRF enforcement regression test with `Client(enforce_csrf_checks=True)`.
- JSON body-size regression test.
- AI endpoint rate-limit regression test.
- Combat session isolation regression test.
- Production-sensitive Django settings externalized through environment
  variables with non-debug validation.
