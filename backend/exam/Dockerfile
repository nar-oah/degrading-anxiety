FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY . .
RUN uv sync --locked --no-dev --no-editable --package exam

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/exam /app/exam

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/exam

CMD ["celery", "-A", "main:celery_app", "worker", "-Q", "exam", "--loglevel=info"]
