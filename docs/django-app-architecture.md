# Django App Architecture and Experience Flow

This document describes the current Django application infrastructure, runtime
architecture, and user experience flow for Call_To_AIdventure.

The current web app lives under:

```text
src/django/
```

The active Django project is:

```text
src/django/call_to_aidventure/
```

The active Django app is:

```text
src/django/game/
```

Older Gradio and legacy graph files are not the current browser experience.

## Current Role of Django

Django is the web shell around the game runtime. It owns:

- URL routing
- server-rendered HTML templates
- browser-facing JSON endpoints
- Django auth pages and signup
- session storage for anonymous and active game state
- database-backed saves for authenticated users
- character templates
- page transitions between landing, character creation, story play, combat,
  victory, and game-over screens

Django does not directly generate story text. It delegates story and choice
generation to `GameEngine`, which wraps the active LangGraph graph in
`src/agents/game_master_graph.py`.

Django also does not directly resolve combat rules. It delegates combat to
`GameEngine`, which wraps functions from `src/combat/core.py`.

## Infrastructure Map

```text
Browser
  |
  | server-rendered pages + fetch() JSON calls
  v
src/django/game/templates/
  |
  v
src/django/game/urls.py
  |
  v
src/django/game/views.py
  |
  +--> src/django/game/services/tools.py
  |       - initialize game state
  |       - serialize and rebuild state
  |       - persist sessions and SaveGame rows
  |
  +--> src/django/game/services/game_engine.py
  |       - LangGraph story/choice adapter
  |       - combat adapter
  |
  +--> src/django/game/models.py
  |       - SaveGame
  |       - CharacterTemplate
  |
  +--> src/utils/
  |       - player creation
  |       - adventure loading
  |       - monster loading
  |
  +--> src/agents/
  |       - LLM runtime
  |       - graph flow
  |       - prompts
  |
  +--> src/combat/
          - mutable combat loop state
          - combat resolution
```

## Django Project Configuration

### Settings

File:

```text
src/django/call_to_aidventure/settings.py
```

Important configuration:

- `DEBUG = True`
- `ALLOWED_HOSTS = []`
- SQLite Django database at `src/django/db.sqlite3`
- installed Django apps include auth, sessions, messages, staticfiles, and
  `game`
- `STATIC_URL = "/static/"`
- `LOGIN_URL = "/accounts/login/"`
- `LOGIN_REDIRECT_URL = "/"`
- `LOGOUT_REDIRECT_URL = "/"`
- timezone is `Europe/Paris`

The settings file also appends `src/` to `sys.path`, because the Django app
imports modules such as `utils`, `agents`, `combat`, and `retrieval` from the
main source tree.

LLM resilience settings are read from environment variables:

- `LLM_REQUEST_TIMEOUT_SECONDS`
- `LLM_PROVIDER_MAX_RETRIES`
- `LLM_RETRY_MAX_ATTEMPTS`
- `LLM_RETRY_INITIAL_DELAY_SECONDS`
- `LLM_RETRY_BACKOFF_MULTIPLIER`
- `LLM_RETRY_MAX_DELAY_SECONDS`
- `LLM_RETRY_JITTER_SECONDS`
- `LLM_TRANSIENT_ERROR_KEYWORDS`
- `LLM_TRANSIENT_STATUS_CODES`
- `LLM_SERVICE_UNAVAILABLE_STATUS_CODE`
- `LLM_SERVICE_UNAVAILABLE_MESSAGE`

### Root URLs

File:

```text
src/django/call_to_aidventure/urls.py
```

Routes:

- `/admin/`: Django admin
- `/accounts/`: Django built-in auth URLs
- `/`: includes `game.urls`

## Game App Files

```text
src/django/game/models.py              Persistent DB models
src/django/game/views.py               Pages and JSON endpoints
src/django/game/urls.py                App route table
src/django/game/services/tools.py      State setup, serialization, persistence
src/django/game/services/game_engine.py
                                      LangGraph and combat adapter
src/django/game/templates/game/        Main HTML pages
src/django/game/templates/registration/
                                      Login, logout, signup pages
src/django/game/static/game/monster_pictures/
                                      Combat monster images
src/django/game/migrations/            Save/template schema and seed data
src/django/game/tests.py               Current behavioral coverage
```

## Models

### `SaveGame`

File:

```text
src/django/game/models.py
```

Fields:

- `user`: owning Django user
- `adventure_id`: id of the adventure module
- `adventure_name`: display name of the adventure
- `state`: serialized `GameState` JSON
- `is_finished`: whether the save belongs in history
- `finished_at`: timestamp for completed/failed saves
- `created_at`
- `updated_at`

Only authenticated users get `SaveGame` rows. Anonymous users keep game state in
the Django session only.

Users can have multiple saves for the same adventure. Migration
`0002_remove_savegame_unique_adventure.py` removed the old uniqueness
constraint.

### `CharacterTemplate`

Fields:

- `user`: owning Django user
- `name`
- `race`
- `character_class`
- `gender`
- `created_at`
- `updated_at`

Constraints:

- `user` plus `name` must be unique
- default ordering is by `name`

Authenticated users can create, update, and delete their own templates.
Anonymous users can view generic templates but cannot save or delete templates.

### Generic Character Templates

Migration `0005_seed_generic_character_templates.py` creates an inactive system
user with id `-1` and seeds three generic templates:

- Borin Stoneguard: Dwarf fighter, Male
- Mira Quickstep: Human rogue, Female
- Elara Moonveil: Elf wizard, Female

These are displayed to both guests and authenticated users.

## Service Layer

### `game.services.tools`

File:

```text
src/django/game/services/tools.py
```

This module owns game-state preparation and persistence.

Important functions:

- `initialize_game(adventure_id, player)`
- `make_serializable_state(state)`
- `rebuild_state(serialized_state)`
- `ensure_goal_state(state)`
- `persist_game(request, state, create_new=False, finish=False)`

`initialize_game()` loads an adventure from the game data SQLite database,
loads the intro text, and builds the initial runtime state.

Initial state includes:

- `player`
- `adventure`
- `history`
- `story_steps`
- `should_end`
- `combat_result`
- `current_story`
- `last_cmd`
- `after_combat`
- `last_choices`
- `current_choices`
- `ongoing_goals`
- `finished_goals`
- `adventure_completed`
- `end_reason`
- `current_location_id`
- heal/damage bookkeeping fields

`make_serializable_state()` converts Pydantic-style objects to dicts before
putting them in the session or `SaveGame.state`.

`rebuild_state()` turns serialized dicts back into runtime objects:

- `Player`
- `Adventure`
- `Monster`

`ensure_goal_state()` backfills goal-tracking fields for old saves and removes
already finished goals from `ongoing_goals`.

`persist_game()` is the central write path:

- always writes serialized state to `request.session["game_state"]`
- clears `save_game_id` for anonymous users
- creates or updates a `SaveGame` for authenticated users
- marks saves finished when `finish=True`
- stores the active `save_game_id` in the session for authenticated users

### `game.services.game_engine`

File:

```text
src/django/game/services/game_engine.py
```

`GameEngine` is the Django-facing adapter around the story graph and combat
system.

It builds two LangGraph graphs:

- `pre_graph`: generates current choices
- `post_graph`: processes player input, story progression, combat triggers,
  damage/healing, goal evaluation, and victory wrap-up

Important methods:

- `initialize(state)`
- `step(state, choice)`
- `start_combat(state)`
- `combat_action(state, combat_action_value)`

`initialize()` prepares graph runtime for the selected adventure, invokes the
pre-input graph, and stores initial choices.

`step()` handles one story turn. It can return:

- `story`: normal story continuation with new choices
- `combat`: combat has been triggered
- `gameover`: the player has died or reached a death ending
- `adventure_victory`: all adventure goals are complete
- `service_unavailable`: transient LLM failure

`start_combat()` initializes combat from `current_monster_name`. It is designed
to be idempotent: if a serialized monster already exists in state, it restores
combat instead of starting over.

`combat_action()` resolves a player combat action, then possibly a monster
counterattack. It returns:

- `combat`: fight continues
- `victory`: monster defeated
- `defeat`: player defeated
- `error`: invalid or missing combat state

The module uses a singleton `get_engine()` so the same `GameEngine` instance is
reused.

## URL and Endpoint Inventory

### Page Routes

| Route | View | Template | Purpose |
| --- | --- | --- | --- |
| `/` | `LandingPageView` | `game/landing.html` | landing, adventure selection, saves |
| `/character/create/` | `CharacterCreatePageView` | `game/character_create.html` | character creation and templates |
| `/play/` | `PlayPageView` | `game/play.html` | story screen |
| `/combat/` | `CombatPageView` | `game/combat.html` | combat screen |
| `/gameover/` | `GameOverPageView` | `game/gameover.html` | defeat/death ending |
| `/victory/` | `VictoryPageView` | `game/victory.html` | victory ending and outro |
| `/debug` | `DebugPageView` | `game/debug.html` | manual debug helper |
| `/accounts/login/` | Django auth | `registration/login.html` | login |
| `/accounts/logout/` | Django auth | `registration/logged_out.html` | logout |
| `/accounts/signup/` | `SignupView` | `registration/signup.html` | signup |
| `/admin/` | Django admin | Django admin | admin |

### JSON Routes

| Route | Method | View | Purpose |
| --- | --- | --- | --- |
| `/health` | GET | `HealthView` | health check |
| `/api/adventures/` | GET | `AdventureListView` | list adventures from game data DB |
| `/api/character-options/` | GET | `CharacterCreationOptionsView` | races, classes, genders |
| `/api/character-templates/` | GET | `CharacterTemplateListView` | generic and user templates |
| `/api/character-templates/save` | POST | `CharacterTemplateSaveView` | save/update user template |
| `/api/character-templates/<id>/delete` | POST | `CharacterTemplateDeleteView` | delete user template |
| `/api/saves/` | GET | `SaveGameListView` | active saves and history |
| `/api/saves/<id>/load` | POST | `LoadSaveGameView` | restore a save into session |
| `/api/saves/<id>/delete` | POST | `DeleteSaveGameView` | delete a save |
| `/api/start` | POST | `StartGameView` | create player and start adventure |
| `/api/state/` | GET | `CurrentGameStateView` | read current story screen state |
| `/api/step` | POST | `StepGameView` | advance story or transition mode |
| `/api/combat/state/` | GET | `CombatStateView` | read current combat state |
| `/api/combat/start` | POST | `StartCombatView` | initialize/restore combat |
| `/api/combat/action` | POST | `CombatActionView` | resolve combat turn |
| `/api/play` | POST | `PlayView` | echo/debug endpoint, not the real game step |

Several JSON POST views are currently decorated with `csrf_exempt`. The login
and logout form pages still use normal Django CSRF tokens.

## Frontend Experience Flow

The frontend is mostly server-rendered HTML plus inline JavaScript. There is no
separate frontend build system.

### 1. Landing Page

Template:

```text
src/django/game/templates/game/landing.html
```

Route:

```text
GET /
```

On load, browser JavaScript calls:

- `GET /api/adventures/`
- `GET /api/saves/` if the user is authenticated

The landing page has two modes:

- Guest mode: choose a new adventure, log in, or create an account.
- Authenticated mode: tabs for New Adventure, Continue Adventure, and History.

Adventure selection flow:

1. `GET /api/adventures/` returns id, name, and description.
2. The user chooses an adventure.
3. The page shows the adventure description.
4. Clicking Start Adventure redirects to:

```text
/character/create/?adventure_id=<id>
```

Save flow for authenticated users:

1. `GET /api/saves/` returns `saves` and `history`.
2. Active saves show Continue and Delete actions.
3. Finished saves show as history and cannot be continued.
4. Continue calls `POST /api/saves/<id>/load`.
5. The server restores the save to the session and returns a redirect URL:
   `/play/` or `/combat/`.

### 2. Character Creation

Template:

```text
src/django/game/templates/game/character_create.html
```

Route:

```text
GET /character/create/?adventure_id=<id>
```

The server resolves the selected adventure and passes it into the template for
display.

On load, browser JavaScript calls:

- `GET /api/character-options/`
- `GET /api/character-templates/`

Character options currently come from `src/utils/player.py`:

- races: Human, Elf, Dwarf, Halfling
- classes: fighter, rogue, wizard
- genders: Female, Male

Class loadouts:

- fighter: 30 HP, 10 gold, Longsword, higher strength
- rogue: 24 HP, 14 gold, Twin Daggers, higher agility
- wizard: 20 HP, 8 gold, Quarterstaff, higher arcana

The user can:

- create a character manually
- use a generic character template
- use a saved character template
- save a character as a template if authenticated
- delete their own saved templates

Starting an adventure calls:

```text
POST /api/start
```

Payload:

```json
{
  "adventure_id": "emerald_sword",
  "character": {
    "name": "Stan",
    "race": "Human",
    "class": "fighter",
    "gender": "Male"
  }
}
```

Server behavior:

1. Validate character fields with `create_player()`.
2. Load adventure metadata and intro text.
3. Build initial game state.
4. Run `GameEngine.initialize()` to generate initial choices.
5. Create a new session id.
6. Persist state in the session.
7. If authenticated, create a new `SaveGame`.
8. Return initial story data.

The browser then redirects to:

```text
/play/
```

### 3. Story Play

Template:

```text
src/django/game/templates/game/play.html
```

Route:

```text
GET /play/
```

On load, browser JavaScript calls:

```text
GET /api/state/
```

Response includes:

- current story
- current choices
- player sheet
- adventure name

When the user submits a choice, the browser calls:

```text
POST /api/step
```

Payload:

```json
{
  "choice": "Examine the surroundings"
}
```

`StepGameView`:

1. Loads serialized state from the session.
2. Rebuilds runtime objects.
3. Calls `GameEngine.step(state, choice)`.
4. Handles the returned mode.
5. Persists updated state unless the result is an LLM service failure.
6. Returns JSON or a mode that causes the browser to redirect.

Possible browser outcomes:

- `mode: "story"`: update story, choices, and player sheet in place.
- `mode: "combat"`: store combat fluff in `sessionStorage`, redirect to
  `/combat/`.
- `mode: "gameover"`: redirect to `/gameover/`.
- `mode: "adventure_victory"`: redirect to `/victory/`.
- HTTP service-unavailable status: show the configured storyteller unavailable
  message without advancing the persisted state.

### 4. Combat

Template:

```text
src/django/game/templates/game/combat.html
```

Route:

```text
GET /combat/
```

On load, browser JavaScript calls:

1. `GET /api/combat/state/`
2. `POST /api/combat/start`

The state endpoint reads the serialized session state and returns:

- monster name
- player HP
- monster HP
- player sheet
- pre-combat fluff

The start endpoint initializes or restores combat. It returns:

- combat log
- monster name
- HP values
- available combat choices

Monster images are loaded from:

```text
src/django/game/static/game/monster_pictures/
```

The image filename is derived from the monster name by replacing spaces with
underscores and appending `.png`.

Example:

```text
Kobold Warrior -> Kobold_Warrior.png
```

When the user submits a combat action, the browser calls:

```text
POST /api/combat/action
```

Payload:

```json
{
  "action": "attack"
}
```

`CombatActionView`:

1. Rebuilds runtime objects from session state.
2. Calls `GameEngine.combat_action()`.
3. Persists updated state.
4. Marks the active save finished if the player is defeated.
5. Returns combat payload.

Possible outcomes:

- `mode: "combat"`: fight continues; UI updates HP, log, and choices.
- `mode: "victory"`: show victory message and Return to Story button.
- `mode: "defeat"`: show defeat message and landing-page return link.

After combat victory, the player clicks Return to Story. The browser calls:

```text
POST /api/step
```

With:

```json
{
  "choice": "Go onward."
}
```

The server advances the story once with the post-combat choice and persists the
updated state. The combat page then redirects back to:

```text
/play/
```

### 5. Endings

Game-over page:

```text
GET /gameover/
```

Victory page:

```text
GET /victory/
```

When `GameEngine.step()` reports `gameover`, `StepGameView` persists the state
with `finish=True` and the browser redirects to `/gameover/`.

When it reports `adventure_victory`, `StepGameView` also persists with
`finish=True` and the browser redirects to `/victory/`.

`VictoryPageView` rebuilds the current session state, reads the adventure id,
loads the adventure outro text with `load_adv_outro()`, and renders it.

Finished authenticated saves move from active saves to history.

## State and Persistence

### Session Keys

The app currently uses these session keys:

- `game_state`: serialized game state
- `save_game_id`: active `SaveGame` id for authenticated users
- `session_id`: UUID for the current browser game session
- `combat_fluff`: pre-combat narration shown on the combat page

### Anonymous Users

Anonymous users can play a full adventure in one browser session.

Their state is stored in Django session storage only. No `SaveGame` row is
created for them.

### Authenticated Users

Authenticated users get both:

- session state for active browser flow
- database-backed `SaveGame` persistence

Starting a new adventure always creates a new save when authenticated. Loading a
save restores `game_state`, `save_game_id`, `session_id`, and `combat_fluff` in
the session.

Finished saves are retained as history but cannot be loaded.

### Serialized Runtime Objects

The runtime state contains objects that are not naturally JSON serializable:

- `Player`
- `Adventure`
- `Monster`

Before writing to the session or DB, `make_serializable_state()` converts them
to dictionaries. Before running the engine, `rebuild_state()` reconstructs the
runtime objects.

## Data Sources

The Django app reads from two SQLite databases:

1. Django application database:

```text
src/django/db.sqlite3
```

This stores users, sessions, saves, templates, migrations, and standard Django
tables.

2. Game data database:

```text
db/sqlite/data.db
```

This stores adventures and monsters. The path is configured by `DB_PATH` and
used by `src/utils/adventure.py` and `src/utils/monster.py`.

Adventure intro/outro text is still loaded from files under:

```text
data/world/adventures/<adventure_id>/
```

## Relationship to LangGraph, LLM, RAG, and Combat

### LangGraph

Django calls LangGraph only through `GameEngine`.

`GameEngine.initialize()` invokes the pre-input graph to produce initial
choices.

`GameEngine.step()` invokes the post-input graph to resolve user choices, then
usually invokes the pre-input graph again to produce the next choices.

### LLM Runtime

The graph uses OpenAI through `src/agents/llm_runtime.py`. Django only sees the
resulting mode and payload.

Transient LLM failures are surfaced as `service_unavailable`. The view returns
the configured `LLM_SERVICE_UNAVAILABLE_STATUS_CODE` and does not persist the
failed state.

### RAG

The active graph retrieves RAG context before story, combat narration, and
choice generation. Django does not call the RAG service directly.

See:

```text
docs/rag-system.md
```

### Combat

Django calls combat only through `GameEngine`.

The lower-level combat module uses module-level mutable globals for current
combat state. `GameEngine.start_combat()` and `GameEngine.combat_action()`
restore the player and monster from session state before resolving actions.

This makes normal single-session play work, but it is not safe for true
concurrent multi-user combat in a shared process.

## Current Tests

File:

```text
src/django/game/tests.py
```

The current test suite covers:

- combat idempotency and action validation
- login, signup, logout
- character template creation, update, no-op, list, and delete permissions
- anonymous game start staying session-only
- authenticated saves and multiple saves for the same adventure
- save loading, history splitting, and finished-save load rejection
- service-unavailable responses preserving persisted state
- gameover, victory, and defeat save finalization
- victory page outro rendering
- healing and damage tools
- fatal damage and pending end transitions
- goal evaluation and victory wrap-up

Useful command:

```bash
uv run python src/django/manage.py test game
```

Lightweight configuration check:

```bash
uv run python src/django/manage.py check
```

## Current Known Edges

- Several JSON endpoints use `csrf_exempt`, so they are development-friendly
  but not hardened for production.
- `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` are development settings.
- The Django admin file does not currently register `SaveGame` or
  `CharacterTemplate`.
- `src/django/db.sqlite3` is a local development database and should be
  recreated with migrations on a fresh clone.
- Game data lives in a separate SQLite database from the Django application
  database.
- `PlayView` at `/api/play` is an echo/debug endpoint, not the main gameplay
  endpoint.
- Combat uses module-level mutable globals in `src/combat/core.py`, which is a
  concurrency risk.
- Templates contain their own CSS and JavaScript instead of shared static
  bundles.
- The frontend is mostly full-page route transitions plus fetch calls, not a
  client-side app framework.
- Authenticated save persistence depends on session `save_game_id`; anonymous
  sessions have no durable recovery path.

## Files at a Glance

```text
src/django/manage.py
    Django command entry point

src/django/call_to_aidventure/settings.py
    Project settings, DB config, auth redirects, LLM resilience env vars

src/django/call_to_aidventure/urls.py
    Admin, Django auth URLs, and game URL include

src/django/game/urls.py
    Page routes and JSON API routes

src/django/game/views.py
    Class-based page views, JSON endpoints, auth/signup, saves/templates

src/django/game/models.py
    SaveGame and CharacterTemplate

src/django/game/services/tools.py
    Game state initialization, serialization, rebuild, persistence

src/django/game/services/game_engine.py
    Adapter around LangGraph and combat

src/django/game/templates/game/landing.html
    Adventure selection, saved games, history

src/django/game/templates/game/character_create.html
    Character creation and template selection

src/django/game/templates/game/play.html
    Story display, choices, player sheet

src/django/game/templates/game/combat.html
    Combat display, HP bars, combat actions, monster image

src/django/game/templates/game/victory.html
    Victory page and adventure outro

src/django/game/templates/game/gameover.html
    Defeat/death page

src/django/game/templates/registration/
    Login, logout, signup pages

src/django/game/tests.py
    App-level behavior tests
```
