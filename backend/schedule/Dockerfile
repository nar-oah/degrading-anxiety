FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
WORKDIR /app
ENV UV_LINK_MODE=copy

COPY . .
RUN uv sync --locked --no-dev --no-editable --package schedule

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/schedule /app/schedule

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/schedule

CMD ["celery", "-A", "main:celery_app", "worker", "-Q", "pdf", "--loglevel=info"]
