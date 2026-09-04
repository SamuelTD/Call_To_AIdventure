FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DJANGO_DEBUG=false \
    DJANGO_SECURE_SSL_REDIRECT=false \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0 \
    DB_PATH=db/sqlite/data.db

RUN pip install --no-cache-dir uv==0.9.11
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev
COPY src ./src
COPY data ./data
COPY db ./db
COPY evaluation ./evaluation
COPY monster_scrapping/monsters.json ./monster_scrapping/monsters.json
COPY scripts/docker-entrypoint.sh ./scripts/docker-entrypoint.sh
RUN chmod +x ./scripts/docker-entrypoint.sh

RUN DJANGO_SECRET_KEY=build-check-secret-key-9d33A1f088eb4F4aB8fD662de9b7d6e0 \
    OPENAI_API_KEY=build-check-dummy-key \
    uv run python src/django/manage.py check --deploy
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
ENTRYPOINT ["./scripts/docker-entrypoint.sh"]
CMD ["uv", "run", "gunicorn", "--chdir", "src/django", "--bind", "0.0.0.0:8000", "call_to_aidventure.wsgi:application"]
