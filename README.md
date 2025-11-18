# Path of Mirrors

> Path of Exile Economic Intelligence Platform for Data-Driven Decision Making

Path of Mirrors is a full-stack web application designed to provide economic intelligence for Path of Exile 1 and Path of Exile 2. Built with performance and scalability in mind, it's optimized for displaying and analyzing dense economic data.

## Features

- **Dual Game Support** - Seamless context switching between PoE1 and PoE2
- **Notes Management** - Full CRUD operations with game-specific filtering (Phase 0 demo)
- **Modern UI** - Dark PoE-inspired theme with shadcn/ui, TanStack Table, and Tremor
- **Type-Safe API** - Auto-generated TypeScript client from OpenAPI spec
- **Production-Ready Architecture** - Hexagonal architecture, structured logging, health checks

## Tech Stack

### Backend
- **FastAPI** - Async Python web framework
- **SQLAlchemy 2.0** - Async ORM with dataclass models
- **PostgreSQL 17** - Primary database
- **Redis 7** - Caching and job queue
- **Alembic** - Database migrations
- **structlog** - Structured JSON logging
- **uv** - Fast Python package manager

### Frontend
- **React 18.3** - UI framework
- **Vite 7** - Build tool with HMR
- **TypeScript** - Type safety
- **TanStack Query** - Server state management
- **TanStack Table** - Data grids (handles 100k+ rows)
- **shadcn/ui** - Composable UI components
- **Tremor** - Dashboard charts and KPIs
- **Tailwind CSS** - Utility-first styling
- **orval** - OpenAPI → TypeScript generator

### Infrastructure
- **Docker Compose** - Local development environment
- **nginx** - Reverse proxy (production)

## Quick Start

> **⚡ Want to get started fast?** See [docs/QUICKSTART.md](docs/QUICKSTART.md) for essential commands only.

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ & npm
- Python 3.12+ (for local development)

### Option 1: One-Command Startup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd path-of-mirrors

# Start everything (backend + frontend)
./scripts/start-dev.sh
```

This will:
- Start PostgreSQL, Redis, and Backend in Docker
- Wait for services to be healthy
- Install frontend dependencies (if needed)
- Start frontend dev server with HMR
- Show unified logs and status

**Press Ctrl+C to stop all services**

### Option 2: Manual Startup

**1. Clone the Repository**

```bash
git clone <repository-url>
cd path-of-mirrors
```

**2. Start Backend Services**

```bash
# Start PostgreSQL, Redis, and FastAPI backend
docker compose up -d

# Verify services are running
docker compose ps

# Check backend health
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

The backend will be available at http://localhost:8000

**3. Run Database Migrations**

```bash
# Create a migration (if needed)
docker compose exec backend uv run alembic revision --autogenerate -m "description"

# Run migrations
docker compose exec backend uv run alembic upgrade head
```

**4. Start Frontend**

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173

### Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **OpenAPI Spec:** http://localhost:8000/openapi.json

## Development Workflow

### Development Scripts

The `scripts/` directory contains convenient startup scripts:

```bash
# Start all services (backend + frontend)
./scripts/start-dev.sh

# Stop all services
./scripts/stop-dev.sh

# Restart all services
./scripts/restart-dev.sh
```

**What `start-dev.sh` does:**
1. Starts Docker services (PostgreSQL, Redis, Backend)
2. Waits for health checks to pass
3. Installs frontend dependencies (if needed)
4. Starts frontend dev server with HMR
5. Shows unified logs from all services
6. Gracefully shuts down everything on Ctrl+C

### Backend Development

```bash
# View logs
docker compose logs -f backend

# Access backend shell
docker compose exec backend bash

# Run tests (when implemented)
docker compose exec backend uv run pytest

# Stop services
docker compose down

# Stop services and remove volumes
docker compose down -v
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Regenerate API client from backend OpenAPI spec
npm run generate:api

# Lint code
npm run lint
```

### Adding New Backend Features

1. Create bounded context in `backend/src/contexts/`
2. Define domain models in `domain/models.py`
3. Create repository in `adapters/repositories/`
4. Implement service in `services/`
5. Add API routes in `api/routes.py`
6. Create Alembic migration
7. Run migration and test

### Adding New Frontend Features

1. Generate API client: `npm run generate:api`
2. Create page component in `src/pages/`
3. Add route to `App.tsx`
4. Use TanStack Query hooks from `@/hooks/api`
5. Use shadcn/ui components from `@/components/ui`
6. Test with HMR

## Project Structure

```
path-of-mirrors/
├── backend/
│   ├── src/
│   │   ├── contexts/           # Bounded contexts (features)
│   │   │   ├── placeholder/    # Notes CRUD (Phase 0 demo)
│   │   │   └── shared/         # Shared domain logic
│   │   ├── infrastructure/     # Cross-cutting concerns
│   │   │   ├── database.py     # SQLAlchemy setup
│   │   │   ├── redis.py        # Redis client
│   │   │   └── logging.py      # Structured logging
│   │   └── main.py             # FastAPI app entrypoint
│   ├── alembic/                # Database migrations
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   └── tables/         # TanStack Table wrappers
│   │   ├── hooks/
│   │   │   ├── api/            # Auto-generated API hooks
│   │   │   └── useGameContext.tsx
│   │   ├── lib/
│   │   │   ├── api-client.ts   # Axios client
│   │   │   └── utils.ts        # Helper functions
│   │   ├── pages/              # Route components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── orval.config.ts         # API client generator config
│   └── package.json
├── scripts/
│   ├── start-dev.sh                  # Start all services
│   ├── stop-dev.sh                 # Stop all services
│   ├── restart-dev.sh              # Restart all services
│   └── README.md               # Scripts documentation
├── docs/
│   ├── PRODUCT.md              # Product vision
│   ├── ARCHITECTURE.md         # Architecture decisions
│   └── SPRINT.md               # Sprint planning
├── docker-compose.yml
└── README.md
```

## Architecture Highlights

### Backend: Hexagonal Architecture

```
contexts/
└── placeholder/
    ├── domain/          # Business logic (models, enums)
    ├── ports/           # Interfaces (repository protocols)
    ├── adapters/        # Implementations (SQLAlchemy repos)
    ├── services/        # Application services
    └── api/             # FastAPI routes
```

**Benefits:**
- Domain logic isolated from infrastructure
- Easy to test with mock repositories
- Swappable implementations (e.g., switch databases)

### Frontend: Component-Based Architecture

- **Atomic Design** - Reusable components from ui primitives
- **Server State** - TanStack Query manages API data with caching
- **Client State** - React Context for game selection
- **Type Safety** - Auto-generated types from backend OpenAPI spec

## Key Features Explained

### Game Context Switching

The `useGameContext()` hook provides global game state:

```typescript
const { game, setGame } = useGameContext();
// game: 'poe1' | 'poe2'

// API hooks automatically filter by game
const { data: notes } = useListNotesApiNotesGet({ game });
```

### Auto-Generated API Client

Changes to backend automatically flow to frontend:

1. Update backend endpoint
2. Run `npm run generate:api` in frontend
3. Get type-safe hooks with IntelliSense

Example:

```typescript
import { useCreateNoteApiNotesPost } from '@/hooks/api';

const mutation = useCreateNoteApiNotesPost();
mutation.mutate({
  data: {
    title: "Currency Strategy",
    content: "Focus on essences",
    game_context: "poe2"
  }
});
```

### Structured Logging

All logs are JSON with request correlation:

```json
{
  "event": "note_created",
  "note_id": "123e4567-e89b-12d3-a456-426614174000",
  "game_context": "poe1",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-17T19:08:34.576416Z",
  "level": "info"
}
```

## API Endpoints

### Health Checks

- `GET /health` - Liveness probe (always returns 200)
- `GET /ready` - Readiness probe (checks DB + Redis)

### Notes API (Phase 0 Demo)

- `GET /api/notes` - List notes (optional `?game=poe1|poe2`)
- `POST /api/notes` - Create note
- `GET /api/notes/{id}` - Get single note
- `PUT /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note

## Environment Variables

### Backend

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/path_of_mirrors

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=development  # development | staging | production
LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
```

### Frontend

```bash
# API URL
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. Port 8000 already in use
#    Solution: Change port in docker-compose.yml

# 2. Database connection failed
#    Solution: Ensure PostgreSQL is running
docker compose up -d db
docker compose restart backend
```

### Frontend API calls fail

```bash
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Verify CORS is configured (already set in backend)

# 3. Regenerate API client
npm run generate:api
```

### Database migrations fail

```bash
# 1. Check current migration state
docker compose exec backend uv run alembic current

# 2. Rollback to previous version
docker compose exec backend uv run alembic downgrade -1

# 3. Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d
docker compose exec backend uv run alembic upgrade head
```

### Port conflicts

```bash
# Find process using port
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Stop conflicting process or change port in config
```

## Performance Tips

### Backend

- Connection pooling configured (10 min, 20 max)
- Redis for caching and session management
- Async SQLAlchemy for concurrent requests
- Indexed queries on foreign keys

### Frontend

- TanStack Table virtualizes large datasets
- TanStack Query caches API responses (5 min stale time)
- Vite code-splitting for lazy loading
- Tailwind CSS purges unused styles

## Testing

### Backend Tests (Optional - Phase 1)

```bash
# Run all tests
docker compose exec backend uv run pytest

# Run with coverage
docker compose exec backend uv run pytest --cov=src

# Run specific test
docker compose exec backend uv run pytest tests/test_notes.py
```

### Frontend Tests (Optional - Phase 1)

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## Deployment (Production)

See `docs/ARCHITECTURE.md` for full deployment guide.

**Quick overview:**

1. Build frontend: `npm run build`
2. Serve static files with nginx
3. Run backend with gunicorn + uvicorn workers
4. Use managed PostgreSQL and Redis
5. Set `ENVIRONMENT=production`
6. Configure HTTPS with Let's Encrypt

## Contributing

This is a Phase 0 project. Future phases will include:

- **Phase 1:** Market intelligence (item prices, trends)
- **Phase 2:** Crafting calculator
- **Phase 3:** Deal finder (arbitrage opportunities)
- **Phase 4:** Real-time alerts

## License

[License TBD]

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 5 minutes ⚡
- [Product Vision](docs/PRODUCT.md) - Feature roadmap and business logic
- [Architecture Guide](docs/ARCHITECTURE.md) - Technical design decisions
- [Sprint Planning](docs/SPRINT.md) - Development progress
- [Scripts Reference](scripts/README.md) - All development scripts

## Support

For issues, questions, or contributions, please refer to the project documentation or open an issue.

---

**Built with** ⚡ **by developers, for Path of Exile theorycrafters**
