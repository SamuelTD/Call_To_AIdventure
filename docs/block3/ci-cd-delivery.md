# Block 3 CI/CD and delivery process

## Scope

This process covers the complete Django application, not only the AI component.
It validates source quality, migrations, deterministic tests, coverage, RAG
dry-run behavior, container build, container startup and the `/health` endpoint.

## Versioned files

| File | Purpose |
|---|---|
| `.github/workflows/block3-ci-cd.yml` | CI/CD workflow for pull requests, main-branch pushes and manual staging gate |
| `Dockerfile` | Production-oriented Django image |
| `scripts/docker-entrypoint.sh` | Runtime data DB setup, migrations and Gunicorn handoff |
| `compose.delivery.yml` | Local staging-equivalent compose file |
| `.dockerignore` | Keeps local secrets/cache out while allowing required dataset source |

## Pipeline

```text
Pull request / main push / manual dispatch
        |
        +--> install locked dependencies with uv
        +--> rebuild read-only game dataset
        +--> ruff check
        +--> Django deploy check
        +--> migration consistency check
        +--> Django tests with coverage
        +--> RAG dry-run validation
        +--> build SHA-tagged Docker image
        +--> run container
        +--> smoke-test /health
        +--> upload image tar artifact
        +--> manual staging gate on workflow_dispatch
```

## Local validation commands

Run deterministic checks:

```bash
uv sync --frozen --all-groups
uv run python db/sqlite/setup_db.py --reset
uv run ruff check src tests
uv run python src/django/manage.py check --deploy
uv run python src/django/manage.py makemigrations --check --dry-run
uv run coverage run src/django/manage.py test game
uv run coverage report
PYTHONPATH=src uv run python -m retrieval.ingest --dry-run
```

Build the delivery image:

```bash
docker build --tag call-to-aidventure:local .
```

Smoke-test the image:

```bash
docker run --detach --rm \
  --name call-to-aidventure-smoke \
  --publish 8000:8000 \
  --env DJANGO_DEBUG=false \
  --env DJANGO_SECURE_SSL_REDIRECT=false \
  --env DJANGO_SECRET_KEY=replace-with-a-long-secret \
  --env DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  --env DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1 \
  --env RAG_ENABLED=false \
  --env OPENAI_API_KEY=replace-with-real-key-for-story-turns \
  call-to-aidventure:local
curl --fail http://127.0.0.1:8000/health
docker stop call-to-aidventure-smoke
```

Run local staging equivalent:

```bash
APP_VERSION=local docker compose -f compose.delivery.yml up --build
```

## Runtime configuration

Required for non-debug delivery:

- `DJANGO_SECRET_KEY`;
- `DJANGO_ALLOWED_HOSTS`;
- `OPENAI_API_KEY`;
- `DB_PATH`, defaulted in the image to `db/sqlite/data.db`.

Recommended:

- `DJANGO_CSRF_TRUSTED_ORIGINS`;
- `DJANGO_SECURE_SSL_REDIRECT=true` only when the runtime sits behind HTTPS
  or a proxy setting `X-Forwarded-Proto: https`;
- `RAG_ENABLED=false` unless Ollama/ChromaDB are available in the environment;
- `MAX_JSON_BODY_BYTES`;
- `AI_RATE_LIMIT_REQUESTS`;
- `AI_RATE_LIMIT_WINDOW_SECONDS`;
- `OPENAI_MODEL`;
- `OPENAI_REASONING_EFFORT`.

## Artifact rule

The Docker image is the delivery artifact. CI tags it with the exact Git SHA.
The same image must be smoke-tested and then promoted. Do not rebuild a
different image for staging or production.

## Promotion

1. Merge only after the deterministic quality gate and container smoke test
   pass.
2. Keep the image artifact name and Git SHA.
3. Publish the SHA image to the selected registry when registry access exists.
4. Deploy that exact image digest to staging.
5. Run `/health` and the browser smoke journey.
6. Promote the same digest to production after owner approval.

## Rollback

Rollback means redeploying the previous known-good image digest and matching
environment configuration.

Minimum rollback evidence:

- previous image tag/digest;
- command or platform action used to redeploy it;
- post-rollback `/health` result;
- note confirming whether database migrations were backward-compatible.

SQLite migrations are applied at container startup in the current local
delivery model. For a public deployment, use a controlled release step before
switching traffic.

## Debugging failed pipeline runs

| Failure | First checks |
|---|---|
| dependency install | verify `uv.lock` is committed and Python version matches |
| dataset setup | verify `monster_scrapping/monsters.json` is present in build context |
| Django deploy check | verify required env vars and import-time AI configuration |
| migration check | run `makemigrations --check --dry-run` locally |
| tests | reproduce with `uv run python src/django/manage.py test game` |
| RAG dry-run | verify `PYTHONPATH=src` and world data files exist |
| Docker build | inspect `Dockerfile`, `.dockerignore`, dependency size and build logs |
| container smoke | inspect `docker logs`, entrypoint output, migrations and `/health` |

## Current artifact size

The web runtime no longer ships legacy/local ML packages such as `torch`,
CUDA-related transitive dependencies, `transformers` or `gradio`. The local
Priority 4 slim image built from the locked dependency set is about 203 MB.
