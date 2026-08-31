set dotenv-load := true

api := "services/api"

# List available recipes
default:
    @just --list

# --- Setup ---

# Install backend (uv) and frontend (pnpm) dependencies
install:
    cd {{api}} && uv sync
    pnpm install

# --- Backend ---

# Run the API with autoreload
dev-api:
    cd {{api}} && uv run uvicorn app.main:app --reload

# Run the pipeline worker as a standalone process
worker:
    cd {{api}} && uv run python -m app.worker

# Apply database migrations
migrate:
    cd {{api}} && uv run alembic upgrade head

# Create a new migration revision: just makemigration "add something"
makemigration name:
    cd {{api}} && uv run alembic revision -m "{{name}}"

# Load synthetic demo leads
seed:
    cd {{api}} && uv run python -m app.seed

# Lint + format check + type check
lint:
    cd {{api}} && uv run ruff check .
    cd {{api}} && uv run ruff format --check .
    cd {{api}} && uv run mypy .

# Auto-fix lint + format
fix:
    cd {{api}} && uv run ruff check --fix .
    cd {{api}} && uv run ruff format .

# Run backend tests
test:
    cd {{api}} && uv run pytest

# --- Frontend ---

# Run the web dashboard dev server
dev-web:
    pnpm --filter web dev

# Build the web dashboard
build-web:
    pnpm --filter web build

# Dump the API's OpenAPI schema to packages/shared/openapi.json
openapi:
    cd {{api}} && uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > ../../packages/shared/openapi.json

# Regenerate the typed API client (schema dump + openapi-typescript)
gen-client: openapi
    pnpm --filter @crm-ai/shared gen
