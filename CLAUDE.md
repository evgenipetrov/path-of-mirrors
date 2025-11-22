# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Path of Mirrors is a full-stack economic intelligence platform for Path of Exile 1 and PoE 2, built with FastAPI (backend) and React (frontend) using a **hexagonal architecture** pattern. The project is organized around **bounded contexts** (feature modules) with clean separation between domain logic and infrastructure.

## Tech Stack

**Backend:**
- FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 17 + Redis
- Python 3.12+, package manager: `uv`
- Alembic for migrations
- structlog for JSON logging

**Frontend:**
- React 19 + Vite + TypeScript
- TanStack Router (file-based routing)
- TanStack Query (server state) + TanStack Table (dense data grids)
- shadcn/ui + Tailwind CSS
- orval (auto-generates TypeScript API client from OpenAPI)

**Infrastructure:**
- Docker Compose for local development
- Development: Backend in Docker, frontend runs native (optimal HMR)

## Essential Commands

```bash
# First-time setup (installs deps, starts Docker services, runs migrations)
./scripts/setup-project.sh

# Daily development (starts PostgreSQL, Redis, Backend, and Frontend with HMR)
./scripts/start-services.sh --dev

# Stop all services
./scripts/stop-services.sh --dev  # or just Ctrl+C

# Run tests
./scripts/run-tests.sh              # All tests
./scripts/run-tests.sh --backend    # Backend only (pytest)
./scripts/run-tests.sh --frontend   # Frontend only (vitest)

# Code quality & automation
./scripts/check-code.sh --fix       # All checks: schema, docs, locks, linting, type checking
./scripts/check-schema.sh           # OpenAPI schema freshness
./scripts/check-docs.sh             # Route documentation consistency
./scripts/check-locks.sh            # Dependency lock consistency

# Database migrations
./scripts/migrate-db.sh create "description"  # Create migration
./scripts/migrate-db.sh                       # Apply migrations
./scripts/migrate-db.sh rollback              # Rollback one migration
./scripts/reset-db.sh --force                 # Nuclear option (deletes all data)

# API client regeneration (after backend schema changes)
./scripts/generate-api.sh

# View logs
./scripts/view-logs.sh backend -f   # Follow backend logs
./scripts/view-logs.sh backend -n 100  # Last 100 lines

# Production build
./scripts/build-images.sh --prod
```

## Project Structure

**Backend bounded contexts (hexagonal architecture):**
```
backend/src/
├── contexts/              # Bounded contexts (feature modules)
│   ├── catalog/          # Static game data (items, modifiers, recipes)
│   ├── economy/          # Market data (prices, trends, currencies)
│   ├── builds/           # User build data (PoB imports, item sets)
│   ├── analysis/         # Computed/ephemeral (valuations, deal finder, craft sims)
│   ├── upstream/         # Legacy data ingestion (migrating to economy)
│   └── placeholder/      # Phase 0 demo (notes CRUD, will be removed)
├── infrastructure/       # Cross-cutting concerns
│   ├── database.py       # SQLAlchemy async session management
│   ├── cache.py          # Redis client
│   ├── logging.py        # structlog setup
│   ├── health.py         # Health check endpoints
│   └── middleware.py     # Request logging middleware
├── shared/               # Shared domain (Game enum, etc.)
└── main.py              # FastAPI app entrypoint
```

**Each context follows hexagonal pattern:**
```
contexts/{context_name}/
├── domain/              # Business entities (SQLAlchemy models, Pydantic schemas)
├── ports/               # Repository protocols (interfaces)
├── adapters/            # Concrete implementations (Postgres repos, external API clients)
├── services/            # Application services (orchestration)
└── api/                 # FastAPI routes
```

**Frontend structure:**
```
frontend/src/
├── routes/              # File-based routes (TanStack Router)
├── features/            # Feature modules (catalog, economy, builds, analysis)
├── components/
│   ├── ui/             # shadcn/ui components (copied, customizable)
│   └── tables/         # TanStack Table wrappers
├── hooks/
│   ├── api/            # Auto-generated TanStack Query hooks (from orval)
│   └── useGameContext.tsx
└── lib/
    ├── api-client.ts   # Axios instance
    └── utils.ts
```

## Architectural Principles

### Hexagonal Architecture (Ports & Adapters)

**Dependency direction:** Outer layers depend on inner layers, never reverse.

```
API Layer (FastAPI routes)
    ↓ depends on
Service Layer (business logic orchestration)
    ↓ depends on
Ports (repository protocols, provider interfaces)
    ↑ implemented by
Adapters (PostgreSQL repos, PoE1/PoE2 providers, external APIs)
    ↓ uses
Domain Models (entities, shared concepts)
```

**Key patterns:**
- **Protocols over inheritance:** Use `typing.Protocol` for repository interfaces
- **Factory pattern:** `get_provider(game: Game) -> BaseProvider` for game-specific logic
- **No cross-context imports:** Contexts reference each other by natural keys/slugs, not database FKs
- **Pragmatic compromise:** SQLAlchemy models ARE the domain models (not pure DDD)

### Game Abstraction Layer

Both PoE1 and PoE2 are supported via **provider pattern**:

```python
from src.contexts.upstream.adapters import get_provider
from src.shared import Game

# Get game-specific implementation
provider = get_provider(Game.POE1)  # Returns PoE1Provider or PoE2Provider
leagues = await provider.get_active_leagues()
data = await provider.fetch_economy_snapshot("Settlers", "Currency")
```

Frontend uses `useGameContext()` hook for global game state.

### Bounded Context Rules

1. **Resource-oriented design:** Contexts expose stable resources (`/items`, `/prices`, `/builds`), not user journeys
2. **Contexts don't import each other** (except via `shared/`)
3. **Cross-context linking:** Use natural keys (slugs) or stable UUIDs, never database FKs
4. **Contexts own their data:** Economy owns prices, Catalog owns items, Builds owns user data
5. **Analysis context is stateless:** Computes on-demand, caches in Redis

## Development Workflow

### Adding a New Feature (Backend)

1. Identify the appropriate bounded context (or create new one)
2. Define domain models in `domain/models.py` (SQLAlchemy + Pydantic schemas)
3. Create repository protocol in `ports/repository.py`
4. Implement adapter in `adapters/postgres_repository.py`
5. Add service layer in `services/` for business logic
6. Create API routes in `api/routes.py`
7. Generate migration: `./scripts/migrate-db.sh create "add feature"`
8. Apply migration: `./scripts/migrate-db.sh`
9. Run tests: `./scripts/run-tests.sh --backend`

### Adding a New Feature (Frontend)

1. Create or update route in `src/routes/` (TanStack Router file-based)
2. Add feature components in `src/features/{context}/`
3. Use auto-generated API hooks from `src/hooks/api/`
4. If backend schema changed: `./scripts/generate-api.sh` to regenerate hooks
5. Leverage `useGameContext()` for game-specific filtering
6. Run tests: `./scripts/run-tests.sh --frontend`

### Database Migrations

**Creating migrations:**
```bash
# 1. Edit models in backend/src/contexts/{context}/domain/models.py
# 2. Generate migration
./scripts/migrate-db.sh create "add user preferences table"
# 3. Review migration in backend/alembic/versions/
# 4. Apply migration
./scripts/migrate-db.sh
```

**Troubleshooting:**
- Rollback: `./scripts/migrate-db.sh rollback`
- Check status: `./scripts/migrate-db.sh current`
- Nuclear reset: `./scripts/reset-db.sh --force`

### Testing

**Backend (pytest):**
- Tests mirror `src/` structure in `tests/`
- Use fixtures for database session, mock repositories
- Mock external APIs (poe.ninja, trade API)
- Run in Docker: `./scripts/run-tests.sh --backend`

**Frontend (vitest + Playwright):**
- Unit tests: `*.test.ts[x]` files, run with `./scripts/run-tests.sh --frontend`
- E2E tests: Playwright in `frontend/e2e/`
- Component tests use React Testing Library

**Coverage target:** ≥70% for domain/service layers

## Code Style

**Python:**
- Line length: 100 characters
- Formatter: ruff format
- Linter: ruff check + mypy type checking
- Type hints required for all function signatures
- Async functions for all I/O operations
- Auto-fix: `./scripts/check-code.sh --fix`

**TypeScript/React:**
- Functional components with hooks (no class components)
- Props defined with `type`, not `interface`
- Filename conventions: `ComponentName.tsx`, `useSomething.ts`
- Use auto-generated API hooks from `orval`
- ESLint + Prettier enforced

## API Design

**Conventions:**
- Version prefix: `/api/v1/{context}/...`
- Pagination: `?limit=50&offset=0`
- Filtering: `?game=poe1&league=settlers`
- Sorting: `?sort=-price` (descending)
- Errors follow RFC 7807 (problem details)

**Health checks:**
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe (checks DB + Redis)

**Auto-generated OpenAPI:**
- Spec available at: `http://localhost:8000/openapi.json`
- Interactive docs: `http://localhost:8000/docs`

## Common Patterns

### Structured Logging

```python
from src.infrastructure import get_logger

logger = get_logger(__name__)

logger.info(
    "market_snapshot_fetched",
    game="poe1",
    league="Settlers",
    item_count=1234,
    duration_ms=456
)
```

### Game Context (Frontend)

```typescript
import { useGameContext } from '@/hooks/useGameContext';

function MyComponent() {
  const { game, setGame } = useGameContext();  // 'poe1' | 'poe2'

  // API hooks automatically filter by game
  const { data: items } = useGetItemsApiV1CatalogItemsGet({ game });

  return <GameSelector value={game} onChange={setGame} />;
}
```

### Repository Pattern (Backend)

```python
# Port (interface)
class ItemRepository(Protocol):
    async def get_by_slug(self, slug: str) -> Item | None: ...
    async def list(self, filters: ItemFilters) -> list[Item]: ...

# Adapter (implementation)
class PostgresItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_slug(self, slug: str) -> Item | None:
        result = await self.session.execute(
            select(Item).where(Item.slug == slug)
        )
        return result.scalar_one_or_none()
```

## Troubleshooting

**Services won't start:**
```bash
./scripts/restart-services.sh --dev            # Restart everything
./scripts/view-logs.sh backend -f     # Check backend logs
docker compose ps                     # Check service status
```

**Database issues:**
```bash
./scripts/migrate-db.sh current       # Check migration status
./scripts/reset-db.sh --force         # Nuclear option (deletes all data)
```

**Frontend API calls fail:**
```bash
curl http://localhost:8000/health     # Verify backend is running
./scripts/generate-api.sh             # Regenerate API client if schema changed
```

**Port conflicts:**
- Frontend: 5173 (Vite)
- Backend: 8000 (FastAPI)
- PostgreSQL: 5432
- Redis: 6379

Use `lsof -i :PORT` to find conflicting processes.

## Important Files

**Configuration:**
- `backend/src/.env` - Backend environment variables (copy from `.env.example`)
- `frontend/.env` - Frontend environment variables
- `docker-compose.yml` + `docker-compose.dev.yml` - Docker orchestration
- `backend/pyproject.toml` - Python dependencies (managed by `uv`)
- `frontend/package.json` - Node dependencies (use `npm`, not `pnpm`)

**Entry points:**
- `backend/src/main.py` - FastAPI application
- `frontend/src/main.tsx` - React application
- `backend/alembic/` - Database migrations

**Documentation:**
- `docs/ARCHITECTURE.md` - Detailed architecture decisions
- `docs/DESIGN.md` - Future resource-oriented design
- `docs/CONTRIBUTING.md` - Contributor guide
- `scripts/README.md` - All development scripts explained

## Project Phases

**Current state:** Transitioning from Phase 0 to Phase 1

- **Phase 0 (complete):** Stack validation with placeholder CRUD
- **Phase 1 (in progress):** Data ingestion, PoB parsing, dual-game support
- **Phase 2 (planned):** Market intelligence dashboard
- **Phase 3+:** Crafting assistant, deal finder, price checker

**Migration in progress:**
- Old `contexts/core` → splitting into `catalog` + `builds`
- Old `contexts/upstream` → moving ingestion to `economy`
- Old `contexts/upgrades` → refactoring to `analysis/deals`

When working in these areas, consult `docs/DESIGN.md` for the target structure.

## Known Issues & Conventions

1. **Frontend uses npm, not pnpm:** Despite `pnpm-lock.yaml` existing, `npm` is the supported tool
2. **Backend excludes `src/app/**`:** Legacy FastCRUD template pending cleanup (see `pyproject.toml`)
3. **Frontend auto-generated code:** Never edit files in `frontend/src/hooks/api/generated/` directly
4. **Docker watch mode:** Backend auto-reloads on code changes via Docker Compose watch

## When to Read Documentation

- **New bounded context?** Read `docs/ARCHITECTURE.md` sections on hexagonal architecture and bounded contexts
- **Database changes?** See migration examples in `scripts/README.md`
- **Confused about structure?** Check `docs/DESIGN.md` for resource-oriented design principles
- **Need examples?** See git history for recent feature additions (commit messages follow Conventional Commits)
