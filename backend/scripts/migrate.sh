#!/bin/bash
# Database migration script for Docker environment

set -e

echo "Running database migrations..."

# Run migrations in the backend container (must run from src/ directory where alembic.ini is located)
docker compose exec backend sh -c "cd /app/src && uv run alembic upgrade head"

echo "Migrations complete!"
