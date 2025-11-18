# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Path of Mirrors is a full-stack economic intelligence platform for Path of Exile 1 and Path of Exile 2. It's built as a modular monolith using hexagonal architecture, optimized for displaying dense economic data.

**Tech Stack:**
- Backend: FastAPI (async), SQLAlchemy 2.0, PostgreSQL 17, Redis 7, structlog
- Frontend: React 18.3, Vite 7, TanStack Query/Table, shadcn/ui, Tremor, TypeScript
- Package Managers: uv (backend), pnpm (frontend)
- Infrastructure: Docker Compose

## Essential Commands

### Development Workflow

```bash
# Start entire development stack (recommended)
./scripts/start-dev.sh

# Stop all services
./scripts/stop-dev.sh

# Restart everything
./scripts/restart-dev.sh
```

**Development mode** runs minimal containers (PostgreSQL, Redis, Backend) with the frontend running locally via Vite dev server for HMR and fast iteration. Press Ctrl+C to stop everything.

### Production Workflow

```bash
# Build production artifacts (frontend + backend Docker image)
./scripts/build-prod.sh

# Start production environment
./scripts/start-prod.sh

# Start in detached mode (background)
./scripts/start-prod.sh --detach

# Build and start in one command
./scripts/start-prod.sh --build

# Stop production environment
./scripts/stop-prod.sh

# Restart production environment
./scripts/restart-prod.sh

# Restart with rebuild
./scripts/restart-prod.sh --rebuild
```

The production environment is **fully containerized**:
- Frontend: Multi-stage Docker build (Node.js build → nginx serve) on port 3000
- Backend: FastAPI container on port 8000
- PostgreSQL and Redis with separate prod volumes
- All services managed via `docker-compose.prod.yml`

### Backend Testing

```bash
# Run all backend tests
./backend/scripts/test.sh

# Run with coverage report
./backend/scripts/test.sh --cov=src --cov-report=term-missing

# Run specific test file
./backend/scripts/test.sh tests/contexts/placeholder/test_notes_api.py

# Run tests matching a pattern
./backend/scripts/test.sh -k "test_create"
```

**Coverage target:** 70%+ (currently 76.39%)

### Database Migrations

```bash
# Create new migration (auto-detect changes)
docker compose exec backend uv run alembic revision --autogenerate -m "description"

# Run migrations (apply pending)
docker compose exec backend uv run alembic upgrade head

# Check current version
docker compose exec backend uv run alembic current

# Rollback one migration
docker compose exec backend uv run alembic downgrade -1

# View migration history
docker compose exec backend uv run alembic history
```

Alembic files are in `backend/src/migrations/` and `backend/src/alembic.ini`.

### Linting and Formatting

```bash
# Backend (inside Docker)
docker compose exec backend uv run ruff check .
docker compose exec backend uv run ruff format .
docker compose exec backend uv run mypy src

# Frontend
cd frontend
pnpm lint
pnpm format
```

### Frontend Development

```bash
cd frontend

# Install dependencies
pnpm install

# Start dev server (if not using start-dev.sh)
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview
```

### Frontend Testing

```bash
cd frontend

# Run tests (single run)
pnpm test

# Run tests in watch mode (for development)
pnpm test:watch

# Run tests with UI
pnpm test:ui

# Run tests with coverage
pnpm test:coverage
```

**Coverage target:** 60%+ (currently 63.52%)

### Regenerate API Client

When backend OpenAPI spec changes, regenerate the frontend TypeScript client:

```bash
cd frontend
pnpm generate:api
```

This uses orval to generate TanStack Query hooks from `http://localhost:8000/openapi.json`.

### Docker Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f postgres

# Access backend shell
docker compose exec backend bash

# Stop and remove volumes (deletes database)
docker compose down -v
```

## Architecture Patterns

### Hexagonal Architecture (Backend)

The backend follows strict hexagonal architecture with ports and adapters:

```
contexts/<feature>/
├── domain/          # Pure business logic (models, schemas)
├── ports/           # Repository interfaces (Protocols)
├── adapters/        # Concrete implementations (PostgreSQL)
├── services/        # Application services (business logic)
└── api/             # FastAPI routes (thin controllers)
```

**Key Principles:**
- Domain logic is isolated from infrastructure
- Services depend on abstract repository protocols, not concrete implementations
- API routes delegate to services (no business logic in routes)
- Dependencies flow: infrastructure → domain, never reverse

**Example Flow:**
1. API route receives request
2. Route calls service method
3. Service orchestrates domain logic using repository interface
4. Repository adapter implements interface using SQLAlchemy

### Adding New Features

#### Backend (New Bounded Context)

1. Create context directory: `backend/src/contexts/<feature>/`
2. Define domain models: `domain/models.py` (SQLAlchemy)
3. Define schemas: `domain/schemas.py` (Pydantic)
4. Create repository protocol: `ports/repository.py`
5. Implement repository: `adapters/postgres_repository.py`
6. Create service: `services/<feature>_service.py`
7. Add API routes: `api/routes.py`
8. Register routes in `backend/src/main.py`
9. Create migration: `docker compose exec backend uv run alembic revision --autogenerate -m "add <feature>"`
10. Run migration: `docker compose exec backend uv run alembic upgrade head`
11. Write tests in `backend/tests/contexts/<feature>/`

#### Frontend (New Page/Feature)

1. Ensure backend changes are deployed
2. Regenerate API client: `cd frontend && npm run generate:api`
3. Create page component: `frontend/src/pages/<Feature>Page.tsx`
4. Add route to `frontend/src/App.tsx` (or router config)
5. Use auto-generated hooks from `@/hooks/api`
6. Use shadcn/ui components from `@/components/ui`
7. Use TanStack Table for data grids, Tremor for charts/KPIs

### Game Context Pattern

The application supports both PoE1 and PoE2 through a global game context:

```typescript
// Access game context
const { game, setGame } = useGameContext(); // 'poe1' | 'poe2'

// API hooks automatically filter by game
const { data: notes } = useListNotesApiNotesGet({ game });
```

Backend models should include a `game_context` field when game-specific data is needed.

### Code Style

#### Backend (Python)

- Use Python 3.12+ syntax: `list[T]`, `dict[K, V]`, `X | None` instead of `Optional[X]`
- Always use type hints for function signatures
- Use `async def` for async functions; all DB operations are async
- Use `from typing import Protocol` for interfaces
- Use structlog for logging with context: `log.info("event", key=value)`
- Follow ruff rules (line length: 100)
- No unused imports, no `# type: ignore` comments

**Example:**
```python
from typing import Protocol
from uuid import UUID

class NoteRepository(Protocol):
    async def create(self, note: Note) -> Note: ...
    async def get_by_id(self, note_id: UUID) -> Note | None: ...

class NoteService:
    def __init__(self, repository: NoteRepository):
        self.repository = repository

    async def create_note(self, data: NoteCreate) -> Note:
        log.info("creating_note", title=data.title)
        note = Note(**data.model_dump())
        return await self.repository.create(note)
```

#### Frontend (TypeScript/React)

- Use functional components with TypeScript interfaces for props
- Use auto-generated API hooks from `@/hooks/api` (never fetch manually)
- Handle loading/error states from TanStack Query
- Use `cn()` helper from `@/lib/utils` to merge Tailwind classes
- Prefer composition over prop drilling (use context when needed)

**Example:**
```typescript
interface NotesTableProps {
  gameContext: 'poe1' | 'poe2';
}

export function NotesTable({ gameContext }: NotesTableProps) {
  const { data: notes, isLoading, error } = useListNotesApiNotesGet({
    game: gameContext
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <DataTable columns={columns} data={notes} />;
}
```

### Testing Guidelines

**Backend:**
- Test services with mocked repositories (unit tests)
- Test repositories against real database in Docker (integration tests)
- Test API endpoints with FastAPI TestClient
- Use pytest fixtures in `backend/tests/conftest.py`
- Use faker for test data generation
- Aim for 70%+ coverage

**Frontend:**
- Use React Testing Library for component tests (Phase 1+)
- Mock API responses using TanStack Query test utilities
- Test user interactions, not implementation details

## Important Constraints

### Database

- Migrations are in `backend/src/migrations/versions/`
- Always create migrations for schema changes using `alembic revision --autogenerate`
- Review auto-generated migrations before applying (Alembic may miss things)
- Database URL: `postgresql+asyncpg://postgres:postgres@db:5432/path_of_mirrors`

### Environment Variables

**Backend** (`.env` in `backend/src/`):
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/path_of_mirrors
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Frontend** (`.env` in `frontend/`):
```bash
VITE_API_URL=http://localhost:8000
```

### Ports

- PostgreSQL: 5432
- Redis: 6379
- Backend API: 8000
- Frontend dev server: 5173

### File Locations

- Backend source: `backend/src/`
- Backend tests: `backend/tests/`
- Backend migrations: `backend/src/migrations/versions/`
- Frontend source: `frontend/src/`
- Development scripts: `scripts/`
- Documentation: `docs/`

## Common Patterns

### Structured Logging

```python
import structlog
log = structlog.get_logger()

log.info("note_created", note_id=str(note.id), game=note.game_context)
log.error("database_error", error=str(e), query=query)
```

Logs are JSON with request correlation IDs.

### Dependency Injection (FastAPI)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

@router.get("/notes")
async def list_notes(db: AsyncSession = Depends(get_db)):
    # Use db here
    pass
```

### TanStack Table (Large Datasets)

```typescript
import { useReactTable, getCoreRowModel } from '@tanstack/react-table';

const table = useReactTable({
  data: items,
  columns,
  getCoreRowModel: getCoreRowModel(),
  enableSorting: true,
  enableFiltering: true,
  // Add virtualization for 100k+ rows with @tanstack/react-virtual
});
```

### Tremor Charts

```typescript
import { Card, Metric, AreaChart } from '@tremor/react';

<Card>
  <Text>Market Value</Text>
  <Metric>1.2M chaos</Metric>
</Card>

<AreaChart
  data={priceHistory}
  categories={['chaos', 'divine']}
  index="date"
  colors={['amber', 'cyan']}
/>
```

## Project Structure

```
path-of-mirrors/
├── backend/
│   ├── src/
│   │   ├── contexts/          # Bounded contexts (features)
│   │   │   ├── placeholder/   # Notes CRUD (Phase 0 demo)
│   │   │   └── shared/        # Shared domain logic (game enum)
│   │   ├── infrastructure/    # Cross-cutting (DB, Redis, logging)
│   │   ├── migrations/        # Alembic migrations
│   │   └── main.py            # FastAPI entrypoint
│   ├── tests/                 # Pytest tests
│   ├── scripts/               # Backend-specific scripts
│   ├── pyproject.toml         # Dependencies (uv)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/ui/     # shadcn/ui components
│   │   ├── hooks/api/         # Auto-generated API hooks
│   │   ├── pages/             # Route components
│   │   └── lib/               # Utilities (api-client, utils)
│   ├── package.json           # Dependencies (pnpm)
│   ├── Dockerfile             # Production build (multi-stage)
│   └── nginx.conf             # Production nginx config
├── scripts/                   # Operational scripts
├── docs/                      # Documentation
├── docker-compose.yml         # Dev: PostgreSQL, Redis, Backend only
└── docker-compose.prod.yml    # Prod: All services containerized
```

## Health Checks

- `GET /health` - Liveness check (always 200)
- `GET /ready` - Readiness check (verifies DB + Redis)

## Troubleshooting

**Backend won't start:**
```bash
docker compose logs backend
docker compose restart backend
```

**Frontend API calls fail:**
```bash
# Check backend health
curl http://localhost:8000/health

# Regenerate API client
cd frontend && npm run generate:api
```

**Database migration conflicts:**
```bash
# Check current state
docker compose exec backend uv run alembic current

# Rollback if needed
docker compose exec backend uv run alembic downgrade -1

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d
docker compose exec backend uv run alembic upgrade head
```

**Port conflicts:**
```bash
# Find what's using a port
lsof -i :8000
lsof -i :5173
```

## API Documentation

When backend is running:
- Swagger UI: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

## Current Phase

Phase 0 (Complete): Stack validation with Notes CRUD
Phase 1 (Current): Building out core features

See `docs/SPRINT.md` for detailed sprint planning.
