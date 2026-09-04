# Block 3 requirements traceability

## Requirement to implementation and validation

| Requirement | Components | Automated validation | Demo/evidence |
|---|---|---|---|
| FR-01 Adventure listing | `game.views.AdventureListView`, `utils.adventure.load_all_adventures`, `landing.html` | `game.tests` adventure/start coverage | Landing page adventure selector |
| FR-02 Character creation | `utils.player.create_player`, `CharacterCreatePageView`, `StartGameView` | invalid/valid character tests | Character creation page |
| FR-03 Start adventure | `initialize_game`, `GameEngine.initialize`, `StartGameView` | start-game persistence tests | `/character/create/` to `/play/` flow |
| FR-04 Story choice turn | `StepGameView`, `GameEngine.step`, LangGraph post/pre graphs | service, localization and persistence tests | `/play/` choice submission |
| FR-05 Scoped RAG | `retrieval.service`, `agents.game_master_graph` | retrieval scope/cache tests | `docs/rag-system.md` and story generation trace |
| FR-06 Combat transition | `agents.tools.combat_tool`, `GameEngine.step`, `combat.html` | graph tool schema tests | Story choice triggers `/combat/` |
| FR-07 Server-owned combat | `combat.core`, `GameEngine.combat_action`, `CombatActionView` | combat engine tests | Combat page action submission |
| FR-08 Combat isolation | `CombatSession`, serialized `current_monster` and `player` state | `test_combat_actions_are_isolated_between_session_states` | Priority 1 regression result |
| FR-09 Endings | `StepGameView`, `VictoryPageView`, `GameOverPageView`, `SaveGame.is_finished` | victory/gameover/defeat save tests | `/victory/` and `/gameover/` |
| FR-10 Save management | `SaveGame`, `SaveGameListView`, `LoadSaveGameView`, `DeleteSaveGameView` | save ownership/load/delete tests | Landing save tabs |
| FR-11 Character templates | `CharacterTemplate`, template list/save/delete views | template authorization tests | Character template tab |
| FR-12 Anonymous play | session persistence in `persist_game` | anonymous start/session-only tests | Guest flow without login |
| FR-13 English/French UI | language middleware, templates, prompts | language toggle and French prompt tests | Language selector |
| FR-14 AI outage resilience | `TemporaryLLMServiceError`, `StepGameView`, retry config | service-unavailable state-preservation tests | forced provider outage demo |
| FR-15 Monitoring metrics | `observability.metrics`, `/metrics`, monitoring compose | metrics endpoint tests | Prometheus/Grafana local stack |
| NFR-01 Env-managed secrets | `settings.py` | `check --deploy` with non-debug env | env var checklist |
| NFR-02 CSRF enforced | Django CSRF middleware, template `csrfFetch` helpers | enforced-CSRF tests | Browser POSTs keep working |
| NFR-03 Body-size limits | `parse_json_body`, `MAX_JSON_BODY_BYTES` | oversized JSON test | HTTP 413 result |
| NFR-04 AI route quotas | `check_rate_limit`, Django cache | AI step rate-limit test | HTTP 429 result |
| NFR-05 LLM timeouts/retries | `agents.runtime_config`, resilience layer | retry/failure tests | env settings and CLI checks |
| NFR-06 Data isolation | ORM filters by `request.user` | cross-user save/template tests | direct object access attempts |
| NFR-07 Failed AI turn preserves state | `StepGameView`, persistence boundary | state-preservation tests | retry after outage |
| NFR-08 Deterministic tests | mocked provider paths | full Django test suite | `uv run python src/django/manage.py test game` |
| NFR-09 Accessibility target | templates and future audit | pending automated/manual audit | owner-selected WCAG/RGAA evidence |
| NFR-10 Deploy check | Django deployment checks | `manage.py check --deploy` | non-debug command output |
| NFR-11 Eco-design baseline | templates/static/AI call policy | pending page-weight/call-count checks | Priority 3 evidence |
| NFR-12 Privacy-preserving observability | metrics labels, future structured logs | metrics tests and review | monitoring docs/screenshots |

## Competency coverage mapping

| Competency | Current evidence | Remaining owner/project evidence |
|---|---|---|
| C14 | project brief, requirements, personas, journeys, user stories, traceability | validate commander, constraints, budget, accessibility target |
| C15 | C4/container/data/deployment models, ADRs, environment matrix, threat model | validate target hosting and production database decision |
| C16 | backlog, DoR/DoD, risks, decision log, iteration template | maintain real iterations, commits, review/retro notes from now on |
| C17 | working Django app, security hardening, tests | Priority 3 accessibility/security/eco-design audits |
| C18 | test suite and commands exist | Priority 4 CI workflow evidence |
| C19 | local setup and deployment model exist | Priority 4 container promotion/deployment proof |
| C20 | metrics and local monitoring exist | Priority 5 SLOs, alerting and runbooks |
| C21 | concurrency issue can serve as incident candidate | formal incident ticket, timeline, before/after evidence |

## Demonstration script baseline

1. Open landing page as guest.
2. Select an adventure.
3. Create a valid character.
4. Start game and show initial story/choices.
5. Submit a story choice.
6. Trigger or load combat.
7. Resolve one attack/defend action.
8. Log in and start another adventure.
9. Show save appears on landing.
10. Load and delete an owned save.
11. Attempt a forbidden cross-user access in tests.
12. Show `/metrics` and local dashboard.
13. Run tests and production checks.

## Traceability maintenance rule

When a feature changes, update the same requirement row with:

- the changed component;
- the new or updated test;
- the manual demonstration step;
- any new residual risk.
