# Call_To_AIdventure

A school project exploring LLM and RAG integration through a fantasy
choose-your-own-adventure game.

The current app is a Django web application in `src/django`. Older Gradio files
and files with `legacy` in the name are kept for reference, but they are not the
main way to run the project.

## Requirements

- Python 3.12 or newer
- `uv` for dependency and virtual environment management
- A Groq API key for the story-generation LLM
- Optional: Ollama, only if you want to rebuild or experiment with the RAG
  Chroma database

Install `uv` if you do not already have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your shell, or follow the installer message to add `uv` to your
`PATH`.

## Fresh Installation

Run these commands from the repository root.

1. Clone or download the repository.

```bash
git clone https://github.com/SamuelTD/Call_To_AIdventure.git
cd Call_To_AIdventure
```

2. Create the Python environment and install dependencies.

```bash
uv sync
```

If the downloaded copy does not include a lock file, `uv` will resolve from
`pyproject.toml`.

3. Create your local environment file.

```bash
cp .env.example .env
```

Edit `.env` and fill in at least these values:

```bash
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model_name
DB_PATH=db/sqlite/data.db
```

`DB_PATH` is required because the adventure loader reads it during Django
startup.

4. Build the game data SQLite database.

```bash
uv run python db/sqlite/setup_db.py --reset
```

This creates `db/sqlite/data.db` and loads monsters plus every adventure found
under `data/world/adventures/`.

5. Create the Django application database.

```bash
uv run python src/django/manage.py migrate
```

This creates `src/django/db.sqlite3`, applies Django migrations, and seeds the
generic character templates through the existing migrations.

6. Verify the app configuration.

```bash
uv run python src/django/manage.py check
```

7. Start the development server.

```bash
uv run python src/django/manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Useful Development Commands

Run Django checks:

```bash
uv run python src/django/manage.py check
```

Rebuild game data after editing monsters or adventure JSON:

```bash
uv run python db/sqlite/setup_db.py --reset
```

Create an admin user:

```bash
uv run python src/django/manage.py createsuperuser
```

Open the Django admin:

```text
http://127.0.0.1:8000/admin/
```

Run the server on another port:

```bash
uv run python src/django/manage.py runserver 127.0.0.1:8001
```

## Environment Variables

Required for normal gameplay:

- `GROQ_API_KEY`: Groq API key used by `langchain-groq`
- `GROQ_MODEL`: Groq chat model used for story generation
- `DB_PATH`: project-relative path to the game data SQLite database, normally
  `db/sqlite/data.db`

Optional LLM retry and timeout settings:

- `LLM_REQUEST_TIMEOUT_SECONDS`, default `30`
- `LLM_PROVIDER_MAX_RETRIES`, default `0`
- `LLM_RETRY_MAX_ATTEMPTS`, default `3`
- `LLM_RETRY_INITIAL_DELAY_SECONDS`, default `0.5`
- `LLM_RETRY_BACKOFF_MULTIPLIER`, default `2`
- `LLM_RETRY_MAX_DELAY_SECONDS`, default `4`
- `LLM_RETRY_JITTER_SECONDS`, default `0.25`
- `LLM_TRANSIENT_ERROR_KEYWORDS`
- `LLM_TRANSIENT_STATUS_CODES`
- `LLM_SERVICE_UNAVAILABLE_STATUS_CODE`, default `503`
- `LLM_SERVICE_UNAVAILABLE_MESSAGE`

Optional RAG settings:

- `OLLAMA_HOST`, default `http://localhost:11434`
- `EMBED_MODEL`, default `mxbai-embed-large:latest`
- `OLLAMA_KEY`, if your Ollama setup requires one

Optional LangSmith tracing settings:

- `LANGSMITH_TRACING`
- `LANGSMITH_ENDPOINT`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`

## Main Project Layout

```text
src/django/                         Django project and web app
src/agents/                         LangGraph game master and LLM runtime
src/combat/                         Combat resolution
src/retrieval/                      Optional Chroma/Ollama RAG utilities
src/utils/                          Game data, player, monster, and path helpers
data/world/adventures/              Adventure JSON and intro/outro text
data/world/characters/              Character lore JSON
data/world/locations/               Location lore JSON
data/documents/monsters.json        Monster source data
db/sqlite/setup_db.py               Game data database builder
monster_scrapping/                  Optional scraping experiments
```

Additional architecture notes:

- `docs/django-app-architecture.md`
- `docs/rag-system.md`

## Optional RAG Ingestion

The Django game flow does not currently require the retrieval subsystem, but the
code exists under `src/retrieval`.

For implementation details, see `docs/rag-system.md`.

To rebuild the Chroma lore collection, start Ollama and make sure the embedding
model is available:

```bash
ollama pull mxbai-embed-large:latest
```

Then run:

```bash
uv run python -m retrieval.ingest --reset
```

Use `--dry-run` to validate chunking without embedding:

```bash
uv run python -m retrieval.ingest --dry-run
```

## Optional Monster Scraping Project

`monster_scrapping/` is a separate scraping workspace used to collect monster
data. It is not required to install or run the Django game. See
`monster_scrapping/README.md` if you want to explore it.

## Troubleshooting

If Django fails during import with a database path error, check that `.env`
exists and contains:

```bash
DB_PATH=db/sqlite/data.db
```

If adventures do not appear on the landing page, rebuild the game data database:

```bash
uv run python db/sqlite/setup_db.py --reset
```

If story generation fails, verify `GROQ_API_KEY` and `GROQ_MODEL` in `.env`.

If imports fail when running scripts outside Django, run through `uv` from the
repository root. For module-style commands that import `src` packages directly,
use:

```bash
PYTHONPATH=src uv run python -m retrieval.ingest --dry-run
```
