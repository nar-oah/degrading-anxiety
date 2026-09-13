FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
WORKDIR /app
ENV UV_LINK_MODE=copy

COPY . .
RUN uv sync --locked --no-dev --no-editable --package course

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/course /app/course

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/course

CMD ["celery", "-A", "main:celery_app", "worker", "-Q", "course", "--loglevel=info"]
