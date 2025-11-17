# Contributing to Path of Mirrors

Thank you for your interest in contributing to Path of Mirrors! This guide will help you get started with development.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

---

## Tech Stack

For detailed technical architecture and design decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).

**Quick overview:**

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL 17 + Redis
- **Frontend:** React 18 + shadcn/ui + Tailwind CSS + TanStack Query
- **Package Management:** `uv` (Python), `npm` (Node)
- **Infrastructure:** Docker Compose + Traefik
- **Testing:** pytest (backend), Vitest + React Testing Library (frontend)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required

- **Docker & Docker Compose** (v2.0+)
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Verify: `docker --version && docker compose version`

- **Python 3.12+** (for local development outside Docker)
  - [Install Python](https://www.python.org/downloads/)
  - Verify: `python --version`

- **uv** (Python package manager)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Or: pip install uv
  ```
  - Verify: `uv --version`

- **Node.js LTS (20+)** and npm
  - [Install Node.js](https://nodejs.org/)
  - Verify: `node --version && npm --version`

### Optional (for enhanced development experience)

- **Git** (for version control)
- **VSCode** or your preferred editor
- **PostgreSQL client** (e.g., `psql`, TablePlus, pgAdmin) for database inspection

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/path-of-mirrors.git
cd path-of-mirrors
```

### 2. Backend Setup

**Install Python dependencies:**
```bash
cd backend
uv sync  # Creates virtual environment and installs dependencies
```

**Activate virtual environment:**
```bash
source .venv/bin/activate  # On macOS/Linux
# Or: .venv\Scripts\activate  # On Windows
```

**Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your local configuration
```

### 3. Frontend Setup

**Install Node dependencies:**
```bash
cd frontend
npm install
```

**Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your local API endpoint (usually http://localhost:8000)
```

### 4. Start Development Environment

**Option A: Docker Compose (Recommended)**
```bash
# From project root
docker compose up --watch
```

This starts:
- Backend (FastAPI) on `http://localhost:8000`
- Frontend (React/Vite) on `http://localhost:3000`
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- Traefik reverse proxy on `http://localhost`

The `--watch` flag enables hot-reload for both backend and frontend.

**Option B: Local Development (without Docker)**

Terminal 1 (Backend):
```bash
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Terminal 3 (PostgreSQL + Redis):
```bash
docker compose up postgres redis
```

### 5. Verify Setup

Visit the following URLs to confirm everything is running:

- **Frontend:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Development Workflow

### Daily Development Loop

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Start development environment:**
   ```bash
   docker compose up --watch
   ```

4. **Make your changes** with hot-reload active

5. **Run tests locally** (see [Testing](#testing) section)

6. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** (see [Pull Request Process](#pull-request-process))

### Database Migrations

**Create a new migration:**
```bash
cd backend
uv run alembic revision --autogenerate -m "describe your changes"
```

**Apply migrations:**
```bash
uv run alembic upgrade head
```

**Rollback migration:**
```bash
uv run alembic downgrade -1
```

### Adding a New Bounded Context

When adding a new feature (e.g., Market Intelligence in Phase 2):

1. **Create context directory structure:**
   ```bash
   mkdir -p backend/src/contexts/market/{domain,ports,adapters,services}
   ```

2. **Define domain models** in `domain/`
3. **Define port interfaces** in `ports/`
4. **Implement adapters** in `adapters/` (database, external APIs)
5. **Implement services** in `services/` (business logic)
6. **Add API routes** in `api/routes/market.py`
7. **Write tests** in `tests/contexts/market/`

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed patterns.

---

## Testing

### Backend Tests

**Run all tests:**
```bash
cd backend
uv run pytest
```

**Run with coverage:**
```bash
uv run pytest --cov=src --cov-report=html
```

**Run specific test file:**
```bash
uv run pytest tests/contexts/market/test_services.py
```

**Run tests matching a pattern:**
```bash
uv run pytest -k "test_market"
```

### Frontend Tests

**Run all tests:**
```bash
cd frontend
npm test
```

**Run with coverage:**
```bash
npm run test:coverage
```

**Run tests in watch mode:**
```bash
npm run test:watch
```

### Testing Best Practices

- **Write tests first** (TDD) for complex business logic
- **Test domain logic in isolation** (no database dependencies)
- **Use fixtures** for test data setup
- **Mock external APIs** (poe.ninja, trade API) in tests
- **Aim for >80% coverage** on domain and service layers

---

## Code Style

### Backend (Python)

**Formatter:** Black (line length: 100)
```bash
cd backend
uv run black src tests
```

**Linter:** Ruff
```bash
uv run ruff check src tests
```

**Type Checker:** mypy
```bash
uv run mypy src
```

**Pre-commit hooks** (recommended):
```bash
cd backend
uv run pre-commit install
```

**Key conventions:**
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Docstrings for public APIs (Google style)
- Async functions for I/O operations

### Frontend (TypeScript/React)

**Formatter:** Prettier
```bash
cd frontend
npm run format
```

**Linter:** ESLint
```bash
npm run lint
```

**Type Checker:** TypeScript
```bash
npm run type-check
```

**Key conventions:**
- Functional components with hooks (no class components)
- Use `const` for component definitions
- Explicit return types for hooks
- Props interfaces defined with `type`, not `interface`
- Filename conventions: `ComponentName.tsx`, `useSomething.ts`

---

## Pull Request Process

### Before Opening a PR

1. **Ensure tests pass locally:**
   ```bash
   # Backend
   cd backend && uv run pytest

   # Frontend
   cd frontend && npm test
   ```

2. **Check code formatting:**
   ```bash
   # Backend
   cd backend && uv run black src tests && uv run ruff check src tests

   # Frontend
   cd frontend && npm run lint && npm run format
   ```

3. **Update documentation** if you changed APIs or architecture

4. **Rebase on main** to avoid merge conflicts:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

### PR Guidelines

**Title format:**
```
<type>: <short description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Examples:
- `feat: add market dashboard API endpoint`
- `fix: correct item normalization for PoE2`
- `docs: update architecture diagrams`

**PR Description should include:**
- Summary of changes
- Related issue (if applicable): `Closes #123`
- Testing performed
- Screenshots (for UI changes)
- Breaking changes (if any)

**PR Checklist:**
- [ ] Tests added/updated and passing
- [ ] Code follows style guidelines
- [ ] Documentation updated (if needed)
- [ ] Commits are atomic and well-described
- [ ] No merge conflicts with `main`

### Review Process

1. **Automated checks** (CI) must pass (tests, linting, type checking)
2. **Code review** by at least one maintainer
3. **Approval required** before merging
4. **Squash and merge** to keep history clean

---

## Project Structure

### Backend Structure

```
backend/
├── src/
│   ├── contexts/              # Bounded contexts (feature modules)
│   │   ├── placeholder/       # Phase 0: Dummy CRUD
│   │   ├── upstream/          # Phase 1: Data ingestion
│   │   ├── market/            # Phase 2: Market Intelligence
│   │   └── ...
│   ├── shared/                # Shared domain models, utilities
│   │   ├── game_context.py    # Game enum (PoE1/PoE2)
│   │   └── schemas.py         # Shared Pydantic schemas
│   ├── infrastructure/        # Cross-cutting concerns
│   │   ├── database.py        # DB connection, session management
│   │   ├── logging.py         # Structured logging setup
│   │   ├── cache.py           # Redis cache client
│   │   └── health.py          # Health check endpoints
│   └── main.py                # FastAPI app entrypoint
├── tests/                     # Mirror of src/ structure
│   ├── contexts/
│   │   └── placeholder/
│   └── conftest.py            # Shared fixtures
├── migrations/                # Alembic migrations
├── pyproject.toml             # uv configuration
└── .env.example               # Environment variables template
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                # shadcn/ui components (copied)
│   │   ├── game-selector/     # Game context switcher
│   │   └── features/          # Feature-specific components
│   │       ├── market/
│   │       └── placeholder/
│   ├── hooks/
│   │   ├── api/               # orval-generated TanStack Query hooks
│   │   └── useGameContext.ts  # Game context hook
│   ├── lib/
│   │   ├── api-client.ts      # Axios instance
│   │   └── utils.ts           # Utility functions
│   ├── pages/                 # Route components
│   │   ├── market.tsx
│   │   └── index.tsx
│   └── main.tsx               # React entrypoint
├── public/                    # Static assets
├── tests/                     # Component tests
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── .env.example
```

---

## Common Tasks

### Regenerate API Client (Frontend)

When backend OpenAPI schema changes:

```bash
cd frontend
npm run generate:api
```

This runs orval to regenerate TypeScript types and TanStack Query hooks.

### Reset Database

```bash
docker compose down -v  # Remove volumes
docker compose up postgres -d
cd backend
uv run alembic upgrade head
```

### View Logs

**All services:**
```bash
docker compose logs -f
```

**Specific service:**
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Run Background Job Manually (Phase 1+)

```bash
cd backend
uv run python -m src.contexts.upstream.jobs.fetch_poeninja
```

---

## Troubleshooting

### Docker issues

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill it or change port in docker-compose.yml
```

**Stale containers:**
```bash
docker compose down
docker system prune -f
docker compose up --build
```

### Backend issues

**Import errors:**
```bash
cd backend
uv sync  # Reinstall dependencies
```

**Migration conflicts:**
```bash
uv run alembic downgrade -1
uv run alembic upgrade head
```

### Frontend issues

**Module not found:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Vite cache issues:**
```bash
npm run clean  # If available, or manually:
rm -rf .vite node_modules/.vite
```

---

## Getting Help

- **Documentation:** Start with [PRODUCT.md](PRODUCT.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues:** Check [GitHub Issues](https://github.com/yourusername/path-of-mirrors/issues)
- **Discussions:** Join [GitHub Discussions](https://github.com/yourusername/path-of-mirrors/discussions)
- **Discord:** [Path of Mirrors Community](https://discord.gg/yourserver) (TBD)

---

## Code of Conduct

Be respectful, collaborative, and constructive. We're building a tool for the PoE community together.

---

Happy coding! 🎮⚔️
