# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

# --- Dependencies (cached unless pyproject/uv.lock change) ---
FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# --- Runtime ---
FROM base AS runtime
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY . .
EXPOSE 8000
# Render sets $PORT. Migrations run on boot so a fresh deploy is self-provisioning.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
