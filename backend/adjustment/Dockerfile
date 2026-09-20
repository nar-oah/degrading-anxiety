FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
WORKDIR /app
ENV UV_LINK_MODE=copy

COPY . .
RUN uv sync --locked --no-dev --no-editable --package adjustment

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/adjustment /app/adjustment

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/adjustment

CMD ["celery", "-A", "main:celery_app", "worker", "-Q", "adjustment", "--loglevel=info"]
