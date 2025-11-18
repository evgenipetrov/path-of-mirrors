# Migration Test Plan

## Post-Restructure Verification

After moving migrations from `backend/src/migrations` to `backend/alembic`, the following tests should be performed to ensure the system works correctly.

## Prerequisites

Ensure Docker and Docker Compose are installed and running.

## Test 1: Docker Build Verification

**Purpose:** Verify the Dockerfile correctly copies alembic files.

```bash
# Build backend container
docker compose build backend

# Expected: Build completes successfully
# Expected: No errors about missing alembic.ini or alembic/ directory
```

**Success Criteria:**
- ✅ Build completes without errors
- ✅ Alembic files are copied to `/app/alembic/` in container
- ✅ `alembic.ini` is copied to `/app/alembic.ini`

## Test 2: Start Services

**Purpose:** Verify all services start correctly.

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# Expected: All services running and healthy
# - postgres (healthy)
# - redis (healthy)
# - backend (running)
```

**Success Criteria:**
- ✅ PostgreSQL container is healthy
- ✅ Redis container is healthy
- ✅ Backend container starts without errors
- ✅ No import errors in backend logs

## Test 3: Alembic Check (In Container)

**Purpose:** Verify Alembic can load migrations properly.

```bash
# Execute alembic check inside container
docker compose exec backend sh -c "cd /app && uv run alembic check"

# Expected: No errors about missing migrations or configuration
```

**Success Criteria:**
- ✅ Alembic loads configuration successfully
- ✅ Alembic can import all models
- ✅ No path errors

## Test 4: Run Migrations

**Purpose:** Verify migrations execute correctly with new structure.

```bash
# Run migrations using the updated script
bash backend/scripts/migrate.sh

# Alternative: Run directly in container
docker compose exec backend sh -c "cd /app && uv run alembic upgrade head"

# Expected: Migrations run successfully
# Expected: Tables created in database
```

**Success Criteria:**
- ✅ Migrations execute without errors
- ✅ `alembic_version` table created
- ✅ `notes` table created with correct schema

## Test 5: Verify Database Schema

**Purpose:** Confirm migrations created the correct schema.

```bash
# Connect to database
docker compose exec postgres psql -U postgres -d pathofmirrors

# List tables
\dt

# Describe notes table
\d notes

# Check alembic version
SELECT * FROM alembic_version;

# Exit
\q
```

**Success Criteria:**
- ✅ `notes` table exists
- ✅ `alembic_version` table exists
- ✅ Schema matches model definition
- ✅ Alembic version matches latest migration

## Test 6: Create New Migration

**Purpose:** Verify alembic can create new migrations.

```bash
# Create a test migration
docker compose exec backend sh -c "cd /app && uv run alembic revision --autogenerate -m 'test migration creation'"

# Expected: New migration file created in backend/alembic/versions/
```

**Success Criteria:**
- ✅ Migration file created successfully
- ✅ File contains proper imports
- ✅ No errors during generation

**Cleanup:**
```bash
# Delete the test migration (don't commit it)
rm backend/alembic/versions/*_test_migration_creation.py
```

## Test 7: Backend API Health

**Purpose:** Verify backend can connect to database.

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check readiness endpoint
curl http://localhost:8000/ready

# Expected: Both return 200 OK with healthy status
```

**Success Criteria:**
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Readiness check returns `{"status": "ready", "checks": {"database": true, "redis": true}}`

## Test 8: API CRUD Operations

**Purpose:** Verify database operations work end-to-end.

```bash
# Create a note
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Note", "content": "Migration test", "game_context": "poe1"}'

# List notes
curl http://localhost:8000/api/notes

# Expected: Note created and retrieved successfully
```

**Success Criteria:**
- ✅ POST returns 201 Created
- ✅ GET returns 200 OK with note data
- ✅ Database persists data correctly

## Test 9: Development Workflow

**Purpose:** Verify typical development workflow works.

```bash
# Make a model change in src/contexts/placeholder/domain/models.py
# For example, add a new field:
# description: Mapped[str | None] = mapped_column(default=None)

# Generate migration
docker compose exec backend sh -c "cd /app && uv run alembic revision --autogenerate -m 'add description field'"

# Review generated migration in backend/alembic/versions/

# Apply migration
docker compose exec backend sh -c "cd /app && uv run alembic upgrade head"

# Verify in database
docker compose exec postgres psql -U postgres -d pathofmirrors -c '\d notes'

# Cleanup: Revert changes and delete test migration
```

**Success Criteria:**
- ✅ Alembic detects model changes
- ✅ Migration file is created correctly
- ✅ Migration applies successfully
- ✅ Database schema updated

## Test 10: Core Domain Models

**Purpose:** Verify core context models can be imported and used.

```bash
# Start Python REPL in backend container
docker compose exec backend sh -c "cd /app && uv run python"

# In Python:
>>> from src.contexts.core import BaseEntity, Money, Currency, League
>>> from decimal import Decimal
>>>
>>> # Test Money value object
>>> price = Money(amount=Decimal("150.5"), currency="chaos")
>>> print(price)
>>>
>>> # Test enums
>>> print(League.CHALLENGE.display_name)
>>> print(Currency.CHAOS.display_name)
>>>
>>> exit()
```

**Success Criteria:**
- ✅ All core imports work
- ✅ Value objects behave correctly
- ✅ Enums have proper values
- ✅ No import errors

## Test 11: Production Build

**Purpose:** Verify production Docker build works.

```bash
# Build production image
docker build -t pathofmirrors-backend:prod --target production backend/

# Expected: Build succeeds with production dependencies only
```

**Success Criteria:**
- ✅ Production build completes
- ✅ Alembic files included
- ✅ No dev dependencies in image

## Test 12: Rollback Test

**Purpose:** Verify migrations can be rolled back.

```bash
# Check current version
docker compose exec backend sh -c "cd /app && uv run alembic current"

# Rollback one migration
docker compose exec backend sh -c "cd /app && uv run alembic downgrade -1"

# Verify rollback
docker compose exec postgres psql -U postgres -d pathofmirrors -c 'SELECT version_num FROM alembic_version;'

# Re-apply
docker compose exec backend sh -c "cd /app && uv run alembic upgrade head"
```

**Success Criteria:**
- ✅ Downgrade executes successfully
- ✅ Schema reverted correctly
- ✅ Re-upgrade works

## Cleanup

```bash
# Stop all services
docker compose down

# Remove volumes (optional - for fresh state)
docker compose down -v
```

## Troubleshooting

### Issue: "alembic: command not found"
**Solution:** Ensure running commands inside container or using `uv run alembic`

### Issue: "ModuleNotFoundError: No module named 'src'"
**Solution:** Verify `PYTHONPATH=/app/src` is set in Dockerfile and docker-compose.yml

### Issue: "Can't locate revision identified by 'head'"
**Solution:** Run `uv run alembic heads` to check migration chain

### Issue: Connection refused to database
**Solution:** Ensure PostgreSQL container is healthy: `docker compose ps`

## Success Summary

All tests passing means:
- ✅ Migrations successfully moved from `src/migrations` → `alembic/`
- ✅ Docker configuration updated correctly
- ✅ Alembic configuration working
- ✅ All imports resolved properly
- ✅ Core domain models functional
- ✅ End-to-end workflow operational

## Next Steps After Verification

1. Commit changes to git
2. Update team documentation
3. Run tests in CI/CD pipeline
4. Deploy to staging environment
