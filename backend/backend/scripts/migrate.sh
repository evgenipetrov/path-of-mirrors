#!/bin/bash
# Database migration script for Docker environment

set -e

echo "Running database migrations..."

# Run migrations in the backend container
docker compose exec backend uv run alembic upgrade head

echo "Migrations complete!"
