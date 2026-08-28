FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

RUN pip install --no-cache-dir uv==0.9.11
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev
COPY src ./src
COPY data ./data
COPY db ./db
COPY evaluation ./evaluation

RUN uv run python src/django/manage.py check
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uv", "run", "gunicorn", "--chdir", "src/django", "--bind", "0.0.0.0:8000", "call_to_aidventure.wsgi:application"]
