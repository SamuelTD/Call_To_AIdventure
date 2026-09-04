# Agent Guide

This project is a school project exploring LLM and RAG integration through a fantasy choose-your-own-adventure game.

## First Rules

- Ignore any file or path with `legacy` in its name unless the user explicitly asks about it.
- Do not treat old Gradio or legacy graph files as the current app surface.
- Prefer reading the current Django, agent, combat, retrieval, and utility modules before making assumptions.
- Preserve user changes in the worktree. Do not revert files unless explicitly asked.

## Current Architecture

The current operating surface is a Django web app under `src/django`.

- Django project: `src/django/call_to_aidventure`
- Django app: `src/django/game`
- Main URL wiring: `src/django/call_to_aidventure/urls.py` includes `game.urls`
- Main views and JSON endpoints: `src/django/game/views.py`
- Runtime game service: `src/django/game/services/game_engine.py`
- Game initialization and session serialization: `src/django/game/services/tools.py`

The game engine uses LangGraph to manage narrative turns:

- `src/agents/game_master_graph.py` defines `GameState`, graph nodes, and graph builders.
- `src/agents/llm_runtime.py` owns the OpenAI LLM, story chain, summary chain, chooser chain, and thinker agent factory.
- `src/agents/prompts/` contains prompt templates and prompt builders.
- `src/agents/tools.py` defines tool actions such as combat/no-op/heal.

Combat is separate from the LLM graph:

- `src/combat/core.py` owns the mutable combat globals and combat resolution.
- `GameEngine.start_combat()` initializes combat from a monster name.
- `GameEngine.combat_action()` resolves player and monster turns, then returns combat/victory/defeat payloads.

Data loading is mostly SQLite plus JSON files:

- `db/sqlite/data.db` contains populated `adventures` and `monsters` tables.
- `db/sqlite/setup_db.py` creates tables and loads monster data.
- `src/utils/adventure.py` reads adventures from SQLite and intro text from `data/world/adventures/<id>/intro.txt`.
- `src/utils/monster.py` reads monsters from SQLite.
- `src/utils/player.py` reads the default player from `data/world/other/player.json`.

The retrieval subsystem under `src/retrieval` uses ChromaDB and Ollama embeddings. It is wired into the active LangGraph for scoped choice, room, combat-fluff, and story context. Retrieval failures degrade to empty lore rather than stopping the game.

## Runtime Flow

The normal browser flow is:

1. `GET /` renders `game/landing.html`.
2. The landing page calls `GET /api/adventures/`.
3. `AdventureListView` loads adventures from SQLite.
4. The user starts an adventure with `POST /api/start`.
5. `StartGameView` calls `initialize_game()`, then `GameEngine.initialize()`.
6. Serialized game state is stored in the Django session as `game_state`.
7. `GET /play/` renders `game/play.html`.
8. The play page calls `GET /api/state/` to display story, choices, and player state.
9. The user submits a choice to `POST /api/step`.
10. `GameEngine.step()` runs the post-input LangGraph.
11. If the result mode is `story`, the page updates story and choices.
12. If the result mode is `combat`, the browser redirects to `/combat/`.
13. The combat page calls `/api/combat/start`, then `/api/combat/action` until victory or defeat.
14. After victory, the page sends `"Go onward."` to `/api/step` to resume narrative generation.

## Environment

The project expects Python 3.12 according to `pyproject.toml`.

Important environment variables:

- `OPENAI_API_KEY`: required by `ChatOpenAI`.
- `OPENAI_MODEL`: model name used by the LLM runtime; defaults to `gpt-5.6-luna`.
- `OPENAI_REASONING_EFFORT`: optional reasoning effort; defaults to `low`.
- `DB_PATH`: SQLite path used by adventure and monster loading. The expected default shape is `db/sqlite/data.db`.
- `OLLAMA_HOST`: optional, defaults to `http://localhost:11434` for retrieval embedding calls.
- `EMBED_MODEL`: optional, defaults to `mxbai-embed-large:latest`.

The repo has a local `.venv`. Prefer `.venv/bin/python` when running Django commands from this workspace.

Useful commands:

```bash
.venv/bin/python src/django/manage.py check
.venv/bin/python src/django/manage.py runserver
.venv/bin/python db/sqlite/setup_db.py
```

If imports fail when running Django, first check whether `src/django/call_to_aidventure/settings.py` is adding the right `src` path to `sys.path`, then inspect imports in `src/django/game/services/game_engine.py`, `src/agents/game_master_graph.py`, and `src/agents/llm_runtime.py`.

## Coding Conventions

- Keep changes scoped to the current feature or bug.
- Follow the existing simple module style; avoid large abstractions unless they remove real duplication.
- Keep Django view payloads JSON-serializable.
- Use the serialization helpers in `src/django/game/services/tools.py` when storing runtime objects in sessions.
- Use existing Pydantic models' `to_dict()` / `from_dict()` methods for session-safe state.
- When adding player, adventure, monster, or equipment fields, update both serialization and UI rendering paths if needed.
- Avoid adding unrelated frontend redesigns while touching game behavior.

## Frontend Notes

Templates currently contain their own CSS and JavaScript:

- `src/django/game/templates/game/landing.html`
- `src/django/game/templates/game/play.html`
- `src/django/game/templates/game/combat.html`
- `src/django/game/templates/game/debug.html`

The UI is intentionally simple: dark panels, story text, radio-button choices, character sheet, combat HP bars, and monster images. Monster images are loaded from:

```text
src/django/game/static/game/monster_pictures/
```

The combat page maps monster names to filenames by replacing spaces with underscores and adding `.png`.

## Known Edges

- `combat.core` uses module-level mutable globals for the current combat. This is simple but not safe for concurrent multi-user combat.
- Django session state is the active persistence path for anonymous play.
- `SaveGame` exists and is used only when `request.user` is authenticated during game initialization.
- `PlayView` at `/api/play` is currently just an echo/debug endpoint, not the real game step path.
- The retrieval/RAG code is part of active story generation; preserve its adventure scope and graceful-empty behavior.
- Some setup notes are stale or minimal; prefer the actual Django flow over `setup.md` when they disagree.

## Testing And Verification

Before claiming the app works, prefer at least:

```bash
.venv/bin/python src/django/manage.py check
```

For behavior changes, manually exercise:

- landing page adventure loading,
- starting an adventure,
- one `/api/step` story turn,
- a combat trigger if the change touches combat,
- victory resume flow if the change touches post-combat state.

Network-backed LLM calls require valid OpenAI environment variables, so distinguish import/config checks from full runtime verification.
