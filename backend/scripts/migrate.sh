#!/bin/bash
# Database migration script for Docker environment

set -e

echo "Running database migrations..."

# Run migrations in the backend container (alembic.ini is now at /app root)
docker compose exec backend sh -c "cd /app && uv run alembic upgrade head"

echo "Migrations complete!"
