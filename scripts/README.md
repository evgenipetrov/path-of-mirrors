# Development Scripts

Convenient scripts for managing the Path of Mirrors development environment.

## Quick Reference

| Script | Purpose | Common Usage |
|--------|---------|--------------|
| `setup.sh` | Initial project setup | `./scripts/setup.sh` |
| `start.sh` | Start services | `./scripts/start.sh` or `./scripts/start.sh --dev` |
| `stop.sh` | Stop services | `./scripts/stop.sh` or `./scripts/stop.sh --dev` |
| `restart.sh` | Restart services | `./scripts/restart.sh` or `./scripts/restart.sh --dev` |
| `build.sh` | Build Docker images | `./scripts/build.sh --prod` |
| `run-tests.sh` | Run tests | `./scripts/run-tests.sh` |
| `check-code.sh` | Run linters | `./scripts/check-code.sh --fix` |
| `migrate-db.sh` | Database migrations | `./scripts/migrate-db.sh` |
| `reset-db.sh` | Reset database | `./scripts/reset-db.sh --force` |
| `view-logs.sh` | View logs | `./scripts/view-logs.sh backend -f` |

---

## Available Scripts

### `setup.sh` - Initial Project Setup

Sets up a new development environment from scratch.

```bash
./scripts/setup.sh
```

**What it does:**
1. Checks prerequisites (Docker, Node.js, npm)
2. Installs frontend dependencies
3. Starts Docker services (PostgreSQL, Redis, Backend)
4. Waits for services to be healthy
5. Runs database migrations
6. Seeds sample data (if available)

**Options:**
- `--skip-seed` - Skip seeding sample data

**Use this when:**
- Setting up the project for the first time
- Onboarding a new developer
- Recovering from a broken environment

---

### `start.sh` - Start Services

Starts services in development or production mode.

```bash
# Development mode (default) - includes frontend
./scripts/start.sh
./scripts/start.sh --dev

# Production mode - backend services only
./scripts/start.sh --prod

# Rebuild before starting
./scripts/start.sh --dev --build
```

**What it does (dev mode):**
1. Starts Docker services (PostgreSQL, Redis, Backend API)
2. Waits for health checks to pass (database + cache)
3. Checks/installs frontend dependencies if needed
4. Starts Vite frontend dev server with HMR
5. Displays unified status and logs
6. Handles graceful shutdown on Ctrl+C

**Services started:**
- PostgreSQL 17 (port 5432)
- Redis 7 (port 6379)
- FastAPI Backend (port 8000)
- Vite Frontend (port 5173) - dev mode only

**Options:**
- `--dev` - Development mode (default)
- `--prod` - Production mode
- `--build` - Rebuild Docker images before starting

**Press Ctrl+C to stop all services cleanly**

---

### `stop.sh` - Stop Services

Stops all running services.

```bash
# Stop development services (default)
./scripts/stop.sh
./scripts/stop.sh --dev

# Stop production services
./scripts/stop.sh --prod
```

**What it does:**
1. Stops Docker Compose services
2. Kills any remaining frontend processes (dev mode)
3. Cleans up background processes

**Options:**
- `--dev` - Stop dev services (default)
- `--prod` - Stop prod services

---

### `restart.sh` - Restart Services

Convenience script to stop and restart services.

```bash
# Restart development services (default)
./scripts/restart.sh
./scripts/restart.sh --dev

# Restart production services
./scripts/restart.sh --prod

# Restart with rebuild
./scripts/restart.sh --dev --build
```

**What it does:**
1. Runs `stop.sh` to stop services
2. Waits 2 seconds for clean shutdown
3. Runs `start.sh` to start everything fresh

**Options:**
- `--dev` - Restart dev services (default)
- `--prod` - Restart prod services
- `--build` - Rebuild before starting

**Use this when:**
- Services are stuck or behaving strangely
- You want a quick "turn it off and on again"
- Faster than manually stopping and starting

---

### `build.sh` - Build Docker Images

Builds Docker images for development or production.

```bash
# Build for development (default)
./scripts/build.sh
./scripts/build.sh --dev

# Build for production
./scripts/build.sh --prod
```

**What it does:**
1. Builds backend Docker image with appropriate target
2. Shows build summary

**Options:**
- `--dev` - Build development image (default)
- `--prod` - Build production image

---

### `run-tests.sh` - Run Tests

Runs all tests (backend and frontend) with optional coverage.

```bash
# Run all tests
./scripts/run-tests.sh

# Run with coverage
./scripts/run-tests.sh --coverage

# Run backend tests only
./scripts/run-tests.sh --backend

# Run frontend tests only
./scripts/run-tests.sh --frontend
```

**What it does:**
1. Runs backend tests via pytest in Docker
2. Runs frontend tests via vitest (when implemented)
3. Shows summary of all test results
4. Returns appropriate exit code for CI

**Options:**
- `--coverage` - Include coverage reports
- `--backend` - Run backend tests only
- `--frontend` - Run frontend tests only

---

### `check-code.sh` - Run Linters and Formatters

Runs all code quality checks (linting, formatting, type checking).

```bash
# Check all code
./scripts/check-code.sh

# Auto-fix issues
./scripts/check-code.sh --fix

# Check backend only
./scripts/check-code.sh --backend

# Check frontend only
./scripts/check-code.sh --frontend
```

**What it does:**
1. Backend: ruff check, ruff format, mypy type checking
2. Frontend: eslint, TypeScript type checking
3. Reports all issues with clear summaries

**Options:**
- `--fix` - Automatically fix issues where possible
- `--backend` - Lint backend code only
- `--frontend` - Lint frontend code only

---

### `migrate-db.sh` - Database Migration Management

Convenient wrapper for Alembic database migrations.

```bash
# Run migrations (upgrade to latest)
./scripts/migrate-db.sh

# Create new migration
./scripts/migrate-db.sh create "add user table"

# Show current version
./scripts/migrate-db.sh current

# Rollback one migration
./scripts/migrate-db.sh rollback

# Show migration history
./scripts/migrate-db.sh history
```

**Commands:**
- `(no args)` - Upgrade to latest migration
- `create <message>` - Create new auto-generated migration
- `current` - Show current migration version
- `rollback` - Rollback one migration (with confirmation)
- `history` - Show full migration history

---

### `reset-db.sh` - Reset Database

Completely resets the database (WARNING: deletes all data).

```bash
# Interactive (prompts for confirmation)
./scripts/reset-db.sh

# Skip confirmation
./scripts/reset-db.sh --force

# Reset and seed sample data
./scripts/reset-db.sh --force --seed
```

**What it does:**
1. Prompts for confirmation (unless --force)
2. Stops all Docker services
3. Removes PostgreSQL volume (deletes all data)
4. Starts services and waits for health
5. Runs migrations to recreate schema
6. Optionally seeds sample data

**Options:**
- `--force` - Skip confirmation prompt
- `--seed` - Seed sample data after reset

**Use this when:**
- Database is corrupted
- Testing migrations from scratch
- Need a fresh start with clean data

---

### `view-logs.sh` - View Service Logs

View Docker service logs with filtering and follow options.

```bash
# View all logs (dev mode)
./scripts/view-logs.sh

# View all logs (prod mode)
./scripts/view-logs.sh --prod

# View backend logs only
./scripts/view-logs.sh backend

# Follow backend logs (real-time)
./scripts/view-logs.sh backend -f

# View last 100 lines
./scripts/view-logs.sh -n 100

# Follow last 50 lines of backend
./scripts/view-logs.sh backend -f -n 50
```

**Available services:**
- `backend` - FastAPI backend logs
- `postgres` - PostgreSQL logs
- `redis` - Redis logs
- (no service) - All services

**Options:**
- `--dev` - Use dev compose files (default)
- `--prod` - Use prod compose files
- `-f, --follow` - Follow log output in real-time
- `-n, --lines NUM` - Show last NUM lines

---

## Usage Examples

### First Time Setup

```bash
# Clone repository and set up everything
git clone <repository-url>
cd path-of-mirrors
./scripts/setup.sh

# Start frontend in a separate terminal
cd frontend && npm run dev

# Open browser: http://localhost:5173
```

### Daily Development

```bash
# Morning: start everything
./scripts/start.sh

# Work on features...
# Frontend changes auto-reload via HMR
# Backend changes auto-reload via Docker watch

# Run tests before committing
./scripts/run-tests.sh

# Run linters and auto-fix issues
./scripts/check-code.sh --fix

# Evening: stop everything
# Press Ctrl+C (or run ./scripts/stop.sh)
```

### Database Workflows

```bash
# Create a new migration
./scripts/migrate-db.sh create "add user preferences table"

# Review the migration file in backend/alembic/versions/

# Apply the migration
./scripts/migrate-db.sh

# Check current version
./scripts/migrate-db.sh current

# If something goes wrong, rollback
./scripts/migrate-db.sh rollback

# Or completely reset the database
./scripts/reset-db.sh --force --seed
```

### Testing Workflow

```bash
# Run all tests
./scripts/run-tests.sh

# Run backend tests only (faster during backend development)
./scripts/run-tests.sh --backend

# Run with coverage to check test completeness
./scripts/run-tests.sh --coverage

# View backend logs while tests run (in another terminal)
./scripts/view-logs.sh backend -f
```

### Pre-Commit Checklist

```bash
# 1. Run linters and auto-fix
./scripts/check-code.sh --fix

# 2. Run tests
./scripts/run-tests.sh

# 3. Check logs for errors
./scripts/view-logs.sh backend -n 50

# 4. Commit if everything passes
git add .
git commit -m "Your message"
```

### Debugging Issues

```bash
# View recent backend logs
./scripts/view-logs.sh backend -n 100

# Follow logs in real-time
./scripts/view-logs.sh backend -f

# Check all services
./scripts/view-logs.sh -n 50

# Restart everything if stuck
./scripts/restart.sh

# If database is corrupted, reset it
./scripts/reset-db.sh --force
```

### Production Build and Deployment

```bash
# Build production images
./scripts/build.sh --prod

# Test production backend
./scripts/start.sh --prod

# View production logs
./scripts/view-logs.sh --prod backend -f

# Stop production services
./scripts/stop.sh --prod
```

---

## Architecture Notes

**Development vs Production Modes:**

All unified scripts (`start.sh`, `stop.sh`, `restart.sh`, `build.sh`, `view-logs.sh`) support `--dev` and `--prod` flags:
- **`--dev` (default):** Uses `docker-compose.yml` + `docker-compose.dev.yml`
  - Includes volume mounts for hot-reload
  - Starts frontend dev server
  - Development command (uvicorn with --reload)
- **`--prod`:** Uses `docker-compose.yml` + `docker-compose.prod.yml`
  - No volume mounts (code baked into image)
  - Backend only (no frontend)
  - Production command (gunicorn with workers)

**Why frontend is separate from Docker:**

The frontend runs outside Docker Compose in dev mode for optimal HMR performance:
- ✅ Sub-second hot reload
- ✅ No Docker volume overhead
- ✅ Direct file system access
- ✅ Simpler node_modules handling

Backend services run in Docker for:
- ✅ Consistent environment (PostgreSQL, Redis)
- ✅ Easy database management
- ✅ Production-like setup
- ✅ Isolated dependencies

This hybrid approach gives the best developer experience while maintaining environment consistency where it matters.

---

## Requirements

- Docker & Docker Compose
- Node.js 18+
- Bash shell
- Ports available: 5432, 6379, 8000, 5173

---

## Troubleshooting

**Script won't run:**
```bash
# Make sure it's executable
chmod +x scripts/*.sh
```

**Port conflicts:**
```bash
# Find what's using a port
lsof -i :8000
lsof -i :5173

# Kill the process or change port in config
```

**Frontend won't start:**
```bash
# Clean install dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
./scripts/start.sh
```

**Database issues:**
```bash
# Reset database (WARNING: deletes all data)
./scripts/reset-db.sh --force

# Or reset with sample data
./scripts/reset-db.sh --force --seed

# Check migration status
./scripts/migrate-db.sh current
```

**Service logs for debugging:**
```bash
# View backend errors
./scripts/view-logs.sh backend -n 100

# Follow all logs in real-time
./scripts/view-logs.sh -f

# Check PostgreSQL logs
./scripts/view-logs.sh postgres -n 50
```

**Test failures:**
```bash
# Run tests with verbose output
./scripts/run-tests.sh --backend

# View logs during test run
./scripts/view-logs.sh backend -f

# Check for linting issues
./scripts/check-code.sh
```

---

## Script Development

All scripts follow these conventions:

1. **Shebang:** `#!/usr/bin/env bash`
2. **Error handling:** `set -e -u -o pipefail`
3. **Colors:** Green (✅), Red (❌), Yellow (⚠️), Blue (ℹ️)
4. **Help:** All scripts support `--help`
5. **Exit codes:** 0 = success, non-zero = failure
6. **Mode flags:** Unified scripts default to `--dev` if no flag specified

**Adding a new script:**

1. Create script in `scripts/` directory
2. Follow the template pattern (see existing scripts)
3. Make it executable: `chmod +x scripts/your-script.sh`
4. Add documentation to this README
5. Test with various flags and error conditions

---

## Integration with CI/CD

These scripts are designed to be used in CI/CD pipelines:

```yaml
# Example GitHub Actions usage
- name: Setup
  run: ./scripts/setup.sh

- name: Lint
  run: ./scripts/check-code.sh

- name: Test
  run: ./scripts/run-tests.sh --coverage

- name: Build Production
  run: ./scripts/build.sh --prod
```

---

## See Also

- [Main README](../README.md) - Project overview and quick start
- [Architecture Guide](../docs/ARCHITECTURE.md) - Technical architecture
- [Sprint Planning](../docs/SPRINT.md) - Development roadmap
- [Docker Compose](../docker-compose.yml) - Service configuration
