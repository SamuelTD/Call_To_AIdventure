# Block 3 project brief and requirements

## Project brief

| Field | Current statement |
|---|---|
| Project name | Call To AIdventure |
| Certification block | Block 3 - Build an application integrating an artificial intelligence service |
| Product objective | Provide a browser-based interactive adventure game where deterministic game rules and an AI storyteller cooperate safely. |
| Commander | Owner validation required. Proposed placeholder: solo student project owner. |
| Primary users | Players who want a short narrative role-playing session in English or French. |
| Secondary users | Project evaluator, developer/operator, future maintainer. |
| In scope | Adventure selection, character creation, narrative turns, RAG-backed story generation, combat, saves, account flows, metrics and local monitoring. |
| Out of scope | Public payment, multiplayer interaction, user-generated adventure authoring, mobile app stores, production cloud operation without a selected host. |
| Main constraint | AI generation depends on external provider availability and budget. |
| Current maturity | Functional proof of concept with automated tests, local monitoring and production-hardening work in progress. |

## Stakeholders

| Stakeholder | Interest | Evidence or action |
|---|---|---|
| Student developer / owner | Build, demonstrate and maintain the project | Git commits, docs, tests, final report |
| Certification evaluator | Verify competencies C14-C21 | This documentation set and repository evidence |
| Player | Play a coherent adventure without losing progress | Browser flows, saves, failure behavior |
| Authenticated player | Recover active saves and history | `SaveGame`, account flows, tests |
| Operator | Run, monitor and diagnose the app | health, metrics, future CI/CD and runbooks |
| AI provider | Receive bounded, non-secret prompts | runtime config, timeouts, rate limits |

## Constraints

| ID | Constraint | Current handling |
|---|---|---|
| CON-01 | External AI calls must not corrupt game state when unavailable | Transient failures return service-unavailable without persisting the failed turn |
| CON-02 | Provider credentials must stay outside Git | Runtime reads secrets from environment variables |
| CON-03 | Anonymous users can play but cannot recover after session loss | State is stored in Django session only |
| CON-04 | Authenticated users own their saves and templates | Queries filter by `request.user` |
| CON-05 | The project must remain small enough for a solo certification project | Lightweight Markdown process and local-first tooling |
| CON-06 | Target hosting is not selected yet | Deployment architecture is documented as target-state, not as live production evidence |

## Functional requirements

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---|---|
| FR-01 | The user can list available adventures | Must | Landing page loads adventure ids, names and descriptions from server data. |
| FR-02 | The user can create a character | Must | Name, race, class and gender are validated server-side before game creation. |
| FR-03 | The application starts a selected adventure | Must | A valid adventure and character create an initial state, story and choices. |
| FR-04 | The player can advance the story by selecting a choice | Must | A selected choice updates story, choices and player sheet or returns a controlled mode transition. |
| FR-05 | The AI storyteller uses scoped adventure knowledge | Must | RAG retrieval is scoped to the selected adventure/location and tested. |
| FR-06 | The game can enter combat from the AI tool flow | Must | A combat command redirects to the combat page with the expected monster. |
| FR-07 | Combat is deterministic server-owned logic | Must | Attack/defend are resolved server-side from current player and monster state. |
| FR-08 | Combat state is isolated per game session | Must | Two session states can resolve combat without changing each other's monster/player. |
| FR-09 | The app supports victory and defeat endings | Must | Finished state redirects to victory/gameover pages and closes active saves. |
| FR-10 | Authenticated users can manage save games | Should | Active saves can be listed, loaded and deleted only by their owner. |
| FR-11 | Authenticated users can manage character templates | Should | Templates can be saved, listed and deleted only by their owner; generic templates are read-only. |
| FR-12 | Anonymous users can play without an account | Should | A guest game stores state in the session and does not create `SaveGame`. |
| FR-13 | The interface supports English and French | Should | Language toggle changes visible UI strings and prompts use the selected language. |
| FR-14 | AI provider outage is handled gracefully | Must | The app returns configured service-unavailable text and preserves prior state. |
| FR-15 | Monitoring exposes application and AI metrics | Should | `/metrics` exposes counters/histograms without personal content labels. |

## Non-functional requirements

| ID | Requirement | Target | Acceptance criteria |
|---|---|---|---|
| NFR-01 | Production secrets are environment-managed | 100% | Non-debug startup fails without `DJANGO_SECRET_KEY`; no production secret is committed. |
| NFR-02 | CSRF is enforced on browser POSTs | 100% active JSON POST views | Tests with enforced CSRF reject missing token and browser templates send `X-CSRFToken`. |
| NFR-03 | Request bodies are bounded | `MAX_JSON_BODY_BYTES` default 8192 | Oversized JSON returns HTTP 413. |
| NFR-04 | AI-triggering routes have quotas | Default 12 calls per 300 seconds per actor | Repeated calls return HTTP 429 after threshold. |
| NFR-05 | External LLM calls have bounded retries/timeouts | Configurable timeout and retry values | Runtime config exposes timeout/retry settings and tests cover transient failures. |
| NFR-06 | Authenticated data is isolated | No cross-user read/write | Tests prove another user cannot load/delete saves/templates. |
| NFR-07 | Main game state survives AI transient failures | No partial failed turn persisted | Regression tests compare state before/after provider outage. |
| NFR-08 | Local test suite remains deterministic | AI calls mocked in tests | `uv run python src/django/manage.py test game` passes without live provider. |
| NFR-09 | Accessibility target is explicit | WCAG 2.2 AA / RGAA aligned target | Owner validation and audit still required. |
| NFR-10 | Production readiness check is clean | `manage.py check --deploy` no issues with valid env | Verified with non-debug env and a strong secret. |
| NFR-11 | Page weight and avoidable AI calls are controlled | Baseline to be measured | Eco-design measurement still required. |
| NFR-12 | Operational observability avoids personal data | No usernames/prompts/session IDs in labels | Metrics and logs must be reviewed before public deployment. |

## Personas

### P1 - Guest player

- Goal: try a short adventure immediately.
- Needs: clear adventure selection, quick character creation, understandable choices.
- Risk: loses progress when the browser session disappears.
- Accessibility profile: may use keyboard navigation and browser zoom.

### P2 - Returning authenticated player

- Goal: resume a saved adventure and keep history of finished games.
- Needs: login, active saves, history, safe delete actions.
- Risk: accidental deletion or loading another user's data.
- Accessibility profile: needs visible focus, readable contrast and clear error messages.

### P3 - Certification evaluator

- Goal: verify that a real app integrates AI with engineering controls.
- Needs: reproducible setup, tests, traceability, diagrams and evidence.
- Risk: evidence that only describes intentions instead of current behavior.

### P4 - Developer/operator

- Goal: run, debug and improve the app.
- Needs: environment documentation, health checks, logs, metrics, test commands.
- Risk: hidden mutable state, missing secrets, provider cost spikes.

## Main user journeys

### J-01 Guest game

1. Guest opens landing page.
2. App loads available adventures.
3. Guest selects an adventure.
4. Guest creates a character.
5. App starts the adventure and stores state in session.
6. Guest plays story turns.
7. App ends in victory, defeat or continued session state.

### J-02 Authenticated save/load

1. User creates account or logs in.
2. User starts an adventure.
3. App creates a `SaveGame`.
4. User leaves and returns to landing.
5. App lists active saves.
6. User loads a save.
7. App restores session state and redirects to story or combat.

### J-03 Combat

1. AI graph returns a combat command.
2. Story page redirects to combat page.
3. Combat page reads current combat state.
4. Combat start initializes or restores the monster.
5. User submits attack or defend.
6. Server resolves player action and monster counterattack.
7. App returns combat, victory or defeat mode.

### J-04 Provider outage

1. User submits a story choice.
2. LLM runtime exhausts configured retry policy.
3. View returns service-unavailable response.
4. Previous state remains persisted.
5. User retries later from the same state.

### J-05 Account data deletion

1. Authenticated user requests save/template deletion.
2. Server filters object by id and current user.
3. Object is deleted only when owned by that user.
4. Current session state is cleared when the active save is deleted.

## User stories

| ID | Story | Acceptance criteria |
|---|---|---|
| US-01 | As a guest, I want to select an adventure so that I can start quickly. | Adventure list loads; empty/unknown ids are rejected. |
| US-02 | As a player, I want to create a valid character so that game rules have stats. | Invalid race/class/gender/name return 400; valid payload starts a game. |
| US-03 | As a player, I want story choices so that I can interact with the AI narrative. | `api_step` accepts a choice and returns story/combat/ending/error mode. |
| US-04 | As a player, I want combat actions to be resolved consistently. | Server updates HP and combat log from current serialized state. |
| US-05 | As a returning user, I want to resume saves so that I keep progress. | Active saves are listed and loadable by owner only. |
| US-06 | As an authenticated user, I want character templates so that I can reuse characters. | Owner can create/update/delete; guest cannot mutate. |
| US-07 | As a player, I want the app to survive AI outages so that I do not lose progress. | Transient failure returns 503 and previous save/session state is preserved. |
| US-08 | As an operator, I want metrics so that failures and latency can be observed. | Metrics endpoint exposes project counters/histograms without PII labels. |
| US-09 | As an evaluator, I want requirements linked to code/tests so that coverage is auditable. | Traceability matrix lists requirement, implementation and validation. |

## Open owner validations

- Confirm the named commander and project context.
- Confirm expected user volume, AI budget and anonymous-play policy.
- Confirm target accessibility standard and level.
- Confirm target deployment environment and supported browsers.
- Confirm whether the debug page remains available only in local debug mode.
