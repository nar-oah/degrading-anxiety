FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY . .
RUN uv sync --frozen --no-dev --package schedule

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/api

CMD ["uv", "run", "celery", "-A", "main:celery_app", "worker", "-Q", "pdf", "--loglevel=info"]
