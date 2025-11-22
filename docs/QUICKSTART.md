# Quick Start Guide

Get Path of Mirrors running in under 5 minutes.

## Prerequisites

- Docker & Docker Compose
- Node.js 18+
- npm (project uses npm as the supported package manager)

## First Time Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd path-of-mirrors

# 2. Run setup script (installs dependencies, starts services, runs migrations)
./scripts/setup-project.sh

# 3. Start frontend (in a new terminal)
cd frontend
npm run dev
```

**Access the application:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

______________________________________________________________________

## Daily Development

```bash
# Start all backend services (PostgreSQL, Redis, Backend API) and launch frontend
./scripts/start-services.sh --dev

# Frontend is started by the script (Vite on 5173). If you prefer manual control:
# cd frontend && npm run dev
```

**Stop everything:** Press `Ctrl+C` in both terminals

______________________________________________________________________

## Essential Commands

### Running Tests

```bash
./scripts/run-tests.sh                 # Run all tests
./scripts/run-tests.sh --backend       # Backend only
```

### Regenerate API Client

```bash
./scripts/generate-api.sh              # From OpenAPI at http://localhost:8000/openapi.json
```

### Code Quality

```bash
./scripts/check-code.sh --fix           # Lint and auto-fix issues
```

### Database

```bash
./scripts/migrate-db.sh                        # Run migrations
./scripts/migrate-db.sh create "description"   # Create new migration
./scripts/reset-db.sh --force                  # Reset database (deletes all data)
```

### Debugging

```bash
./scripts/view-logs.sh backend -f      # Follow backend logs
./scripts/view-logs.sh backend -n 100  # Last 100 lines
```

### Production Build

```bash
./scripts/build-images.sh --prod              # Build frontend + backend Docker image
```

______________________________________________________________________

## Troubleshooting

**Services won't start?**

```bash
./scripts/restart-services.sh --dev            # Restart everything
```

**Database corrupted?**

```bash
./scripts/reset-db.sh --force     # Nuclear option: fresh database
```

**Need help?**

```bash
./scripts/setup-project.sh --help         # Any script supports --help
```

______________________________________________________________________

## File Structure (What You'll Work With)

```
path-of-mirrors/
├── backend/src/
│   ├── contexts/          # Feature modules (e.g., placeholder/notes)
│   │   └── placeholder/   # Notes CRUD (Phase 0 demo)
│   └── infrastructure/    # Database, logging, health checks
├── frontend/src/
│   ├── routes/           # File-based routes (TanStack Router)
│   ├── components/       # UI and layout components
│   └── features/         # Feature modules (notes, upgrades, etc.)
├── scripts/              # Development scripts (setup, test, lint, etc.)
└── docs/                 # Documentation (SPRINT.md, ARCHITECTURE.md)
```

## Testing the API

### Health Checks

```bash
# Liveness check
curl http://localhost:8000/health

# Readiness check (includes DB and Redis)
curl http://localhost:8000/ready
```

### Example API Calls

```bash
# List notes for PoE1
curl http://localhost:8000/api/v1/poe1/notes

# Create a note
curl -X POST http://localhost:8000/api/v1/poe1/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Hello"}'

# Get context health
curl http://localhost:8000/api/v1/poe1/notes/health
```

**See [API_ROUTES.md](API_ROUTES.md) for complete API reference with all endpoints.**

______________________________________________________________________

## Common Workflows

### Making a Backend Change

```bash
# 1. Edit code in backend/src/
# 2. Backend auto-reloads (Docker watch)
# 3. Test the API:
curl http://localhost:8000/api/v1/poe1/notes/health
# 4. Run tests: ./scripts/run-tests.sh --backend
```

### Making a Frontend Change

```bash
# 1. Edit code in frontend/src/
# 2. Frontend auto-reloads (HMR) on http://localhost:5173
# 3. Check console and terminal for errors
```

### Adding a Database Migration

```bash
# 1. Edit models in backend/src/contexts/*/domain/models.py
# 2. Create migration:
./scripts/migrate-db.sh create "add new field"

# 3. Review migration in backend/alembic/versions/
# 4. Apply migration:
./scripts/migrate-db.sh
```

### Before Committing

```bash
./scripts/check-code.sh --fix           # Fix code style
./scripts/run-tests.sh                 # Run tests
git add .
git commit -m "Your message"
```

______________________________________________________________________

## What's Running?

| Service           | Port | Docker Service    | Purpose            |
| ----------------- | ---- | ----------------- | ------------------ |
| Frontend (Vite)   | 5173 | *(not in Docker)* | React app with HMR |
| Backend (FastAPI) | 8000 | `backend`         | Python API         |
| PostgreSQL        | 5432 | `postgres`        | Database           |
| Redis             | 6379 | `redis`           | Cache & job queue  |

**View logs:**

```bash
./scripts/view-logs.sh backend    # Backend logs
./scripts/view-logs.sh postgres   # PostgreSQL logs
./scripts/view-logs.sh redis      # Redis logs
```

______________________________________________________________________

## Next Steps

- **Read the architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **See the roadmap**: [SPRINT.md](SPRINT.md)
- **Explore all scripts**: [../scripts/README.md](../scripts/README.md)
- **Full README**: [../README.md](../README.md)

______________________________________________________________________

**Need more detail?** See [../README.md](../README.md) for comprehensive documentation.
