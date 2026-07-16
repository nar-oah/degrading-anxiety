FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY . .
RUN uv sync --frozen --no-dev --package api

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/api
EXPOSE 8000

CMD ["uv", "run", "gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "main:app"]
