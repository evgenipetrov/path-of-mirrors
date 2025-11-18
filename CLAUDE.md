# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

Path of Mirrors is a full-stack economic intelligence platform for Path of Exile 1 and Path of Exile 2, built as a modular monolith with hexagonal architecture.

**Stack:**
- Backend: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 17 + Redis
- Frontend: React 19 + TypeScript + Vite + TanStack Router/Query/Table + shadcn/ui + Tailwind CSS
- Package Management: `uv` (Python), `npm` (Node)
- Infrastructure: Docker Compose

## Essential Commands

### Development Environment
```bash
# Start backend services (Postgres + Redis + FastAPI in Docker)
docker compose up -d

# Start frontend dev server (run in frontend/)
cd frontend && npm run dev

# Access:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Backend Development
```bash
# CRITICAL: Always use 'uv run' for Python commands
uv run pytest                           # Run all tests
uv run pytest tests/path/to/test.py     # Run specific test
uv run pytest -k "test_pattern"         # Run tests matching pattern
uv run pytest --cov=src                 # Run with coverage

# Database migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run alembic upgrade head             # Apply migrations
uv run alembic downgrade -1             # Rollback one migration

# Linting and formatting
uv run ruff check src tests             # Check code
uv run ruff check --fix src tests       # Auto-fix issues
uv run mypy src                         # Type checking

# Running scripts (e.g., data collection)
uv run python scripts/collect_poeninja_samples.py --game poe1
```

### Frontend Development
```bash
cd frontend

npm run dev                # Dev server with HMR
npm run build              # Production build
npm run preview            # Preview production build
npm run lint               # ESLint check
npm run format             # Prettier format
npm run test               # Run Vitest unit tests
npm run test:watch         # Vitest watch mode
npm run test:e2e           # Playwright E2E tests
```

### Docker Operations
```bash
docker compose logs -f backend          # Follow backend logs
docker compose exec backend bash        # Shell into backend container
docker compose down                     # Stop services
docker compose down -v                  # Stop and remove volumes (fresh DB)
```

## Architecture Overview

### Hexagonal Architecture (Ports & Adapters)

Every bounded context follows this structure:
```
contexts/{context_name}/
├── domain/             # Business logic (models, enums, value objects)
│   ├── models.py       # SQLAlchemy models (MappedAsDataclass)
│   └── schemas.py      # Pydantic schemas for API
├── ports/              # Interfaces (repository protocols)
│   └── repository.py   # Abstract repository interface
├── adapters/           # Infrastructure implementations
│   └── postgres_repository.py  # Concrete SQLAlchemy repository
├── services/           # Application/domain services (orchestration)
│   └── {name}_service.py
└── api/                # FastAPI routes
    └── routes.py       # HTTP layer
```

**Key principles:**
- Domain models are SQLAlchemy 2.0 `MappedAsDataclass` (no `__init__`, use class attributes)
- Repositories use Protocol-based interfaces (duck typing)
- Services orchestrate domain logic, never called from routes directly
- API routes only handle HTTP concerns (request/response), delegate to services
- Dependencies flow: API → Services → Repositories → Domain

### Game Abstraction Layer

The provider pattern enables PoE1/PoE2 dual support:
```
contexts/upstream/
├── ports/
│   └── provider.py              # BaseProvider Protocol
└── adapters/
    ├── provider_factory.py      # get_provider(game) -> BaseProvider
    ├── poe1_provider.py         # PoE1 implementation
    └── poe2_provider.py         # PoE2 implementation
```

**Usage:**
```python
from src.contexts.upstream.adapters import get_provider
from src.shared import Game

provider = get_provider(Game.POE1)  # Returns PoE1Provider
leagues = await provider.get_active_leagues()
```

### Database Patterns

**SQLAlchemy 2.0 async models (MappedAsDataclass):**
```python
from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass
from src.infrastructure.database import Base

class Note(Base, MappedAsDataclass):
    __tablename__ = "notes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid7)
    title: Mapped[str]
    content: Mapped[str | None] = mapped_column(default=None)
    game_context: Mapped[str] = mapped_column(index=True)
```

**Repository pattern:**
```python
# Port (protocol)
class NoteRepository(Protocol):
    async def create(self, note: Note) -> Note: ...
    async def get_by_id(self, note_id: UUID) -> Note | None: ...

# Adapter (implementation)
class PostgresNoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
```

### Frontend Architecture

**TanStack Router for file-based routing:**
- Routes defined in `frontend/src/routes/` with `.tsx` files
- Uses `@tanstack/react-router` with type-safe navigation
- Game context managed via React Context (`useGameContext()`)

**State management:**
- Server state: TanStack Query (auto-generated hooks from OpenAPI via orval)
- Client state: Zustand or React Context
- URL state: TanStack Router search params

**API client generation:**
Frontend types and hooks are auto-generated from backend OpenAPI spec. When backend API changes:
```bash
cd frontend
npm run generate:api  # Not implemented yet - manual for now
```

## Development Guidelines

### Working with Contexts

**Creating a new bounded context:**
1. Create directory structure: `backend/src/contexts/{name}/{domain,ports,adapters,services,api}`
2. Define domain models in `domain/models.py` (SQLAlchemy MappedAsDataclass)
3. Define Pydantic schemas in `domain/schemas.py` for API validation
4. Create repository protocol in `ports/repository.py`
5. Implement repository in `adapters/{db}_repository.py`
6. Create service layer in `services/{name}_service.py`
7. Add API routes in `api/routes.py`
8. Register routes in `backend/src/main.py`
9. Create Alembic migration: `uv run alembic revision --autogenerate -m "add {name} context"`
10. Write tests in `backend/tests/contexts/{name}/`

### Code Style Conventions

**Backend:**
- Python 3.12+ with type hints (enforced by mypy)
- Line length: 100 characters (ruff)
- Async/await for all I/O operations
- Use `structlog` for logging with structured context
- Pydantic schemas for validation (v2 syntax)
- Repository methods return domain objects, not dicts

**Frontend:**
- Functional components with hooks only
- Use `type` for props and interfaces
- Explicit return types for custom hooks
- Filename convention: `ComponentName.tsx`, `useSomething.ts`
- Tailwind CSS for styling (no CSS modules)
- shadcn/ui components copied to `src/components/ui/` (fully customizable)

### Testing Patterns

**Backend tests:**
```bash
# Test structure mirrors src/ structure
tests/
├── contexts/
│   └── placeholder/
│       ├── test_models.py
│       ├── test_repository.py
│       ├── test_service.py
│       └── test_routes.py
└── conftest.py  # Shared fixtures

# Run tests with uv run
uv run pytest                           # All tests
uv run pytest tests/contexts/upstream/  # Specific module
uv run pytest -k "test_provider"        # Pattern match
```

**Frontend tests:**
- Unit tests: Vitest + React Testing Library
- E2E tests: Playwright (in `frontend/e2e/`)

### Common Pitfalls

1. **NEVER call `python` directly** - always use `uv run python`
2. **NEVER call `pytest` directly** - always use `uv run pytest`
3. **Don't mix domain and infrastructure** - keep domain/ pure Python
4. **Don't forget migrations** - any model change needs `alembic revision --autogenerate`
5. **Don't use old SQLAlchemy patterns** - models are MappedAsDataclass (no `__init__`)
6. **Game context is mandatory** - all game-specific data must be filtered by `game_context`

## Agent Coordination

- **Claude (this agent):** Primary implementation - writes backend/frontend code
- **Gemini agent:** Design and gap analysis (consult `AGENTS.md`)
- **Codex agent:** Test generation (consult `AGENTS.md`)

**Workflow:** Always check if code changes require doc updates. Treat tasks incomplete until `docs/` is updated or a docs-TODO is created.

## Key Documentation

Read these for comprehensive understanding (in order of importance):
1. `docs/ARCHITECTURE.md` - Detailed architecture patterns and decisions
2. `docs/QUICKSTART.md` - Essential commands and workflows
3. `docs/CONTRIBUTING.md` - Full development setup and conventions
4. `docs/PRODUCT.md` - Product vision and feature roadmap
5. `docs/SPRINT.md` - Current sprint priorities
6. `backend/scripts/README.md` - Data collection scripts usage

## Project Structure Summary

```
path-of-mirrors/
├── backend/
│   ├── src/
│   │   ├── contexts/           # Bounded contexts (features)
│   │   │   ├── placeholder/    # Notes CRUD (Phase 0 demo)
│   │   │   └── upstream/       # Data ingestion (Phase 1+)
│   │   ├── infrastructure/     # DB, Redis, logging, health
│   │   ├── shared/             # Game enum, shared utilities
│   │   └── main.py             # FastAPI app entrypoint
│   ├── alembic/                # Database migrations
│   ├── scripts/                # Data collection utilities
│   ├── tests/                  # Mirror of src/ structure
│   └── pyproject.toml          # uv dependencies
├── frontend/
│   ├── src/
│   │   ├── components/ui/      # shadcn/ui components
│   │   ├── routes/             # TanStack Router file-based routes
│   │   ├── hooks/              # React hooks (API, context)
│   │   └── lib/                # Utilities, API client
│   └── package.json
├── docs/                       # Documentation (single source of truth)
└── docker-compose.yml          # Local development services
```
