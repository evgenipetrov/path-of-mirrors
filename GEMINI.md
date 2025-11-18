# Path of Mirrors - Gemini Context
This document provides a comprehensive overview of the Path of Mirrors project, its architecture, and development conventions to be used as instructional context for Gemini.

## Project Overview

Path of Mirrors is a full-stack web application designed to provide economic intelligence for the games Path of Exile 1 and Path of Exile 2. It is built with a Python/FastAPI backend and a React/TypeScript frontend. The project is in its early stages (Phase 0), with the core architecture and development patterns established.

The backend follows a hexagonal architecture, with a clear separation of domain logic and infrastructure. The frontend is built with React, Vite, and Tailwind CSS, and uses TanStack Query for server state management. The project uses Docker for local development, with services defined in `docker-compose.yml`.

## Key Technologies

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL 17, Redis 7, Alembic, `uv`
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, TanStack Table
- **Infrastructure:** Docker Compose, nginx (for production)

## Building and Running

The project includes a set of scripts in the `scripts/` directory to manage the development environment.

### One-Command Startup

The recommended way to start the development environment is to use the `start-dev.sh` script:

```bash
./scripts/start-dev.sh
```

This script will:
1.  Start the PostgreSQL, Redis, and backend services in Docker.
2.  Wait for the services to become healthy.
3.  Install frontend dependencies if necessary.
4.  Start the frontend development server.
5.  Stream logs from all services.

### Manual Startup

Alternatively, you can start the services manually:

1.  **Start backend services:**
    ```bash
    docker compose up -d
    ```

2.  **Run database migrations:**
    ```bash
    docker compose exec backend uv run alembic upgrade head
    ```

3.  **Start frontend:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

### Key Commands

-   **Start all services:** `./scripts/start-dev.sh`
-   **Stop all services:** `./scripts/stop-dev.sh`
-   **Restart all services:** `./scripts/restart-dev.sh`
-   **Run backend tests:** `docker compose exec backend uv run pytest`
-   **Run frontend linting:** `cd frontend && npm run lint`
-   **Generate frontend API client:** `cd frontend && npm run generate:api`

## Development Conventions

### Backend

-   The backend follows a hexagonal architecture, with code organized into bounded contexts in `backend/src/contexts/`.
-   Each context has its own domain models, services, repositories, and API routes.
-   Database migrations are managed with Alembic. To create a new migration, run:
    ```bash
    docker compose exec backend uv run alembic revision --autogenerate -m "Your migration message"
    ```
-   Dependencies are managed with `uv` and are defined in `backend/pyproject.toml`.

### Frontend

-   The frontend is a React application built with Vite.
-   Components are located in `frontend/src/components/`.
-   The application uses TanStack Router for routing, with routes defined in `frontend/src/routes/`.
-   Server state is managed with TanStack Query. API hooks are auto-generated from the backends OpenAPI specification using `orval`.
-   Styling is done with Tailwind CSS.
-   Dependencies are managed with `npm` and are defined in `frontend/package.json`.

### Game Context

A key feature of the application is the ability to switch between Path of Exile 1 and Path of Exile 2. This is managed by the `useGameContext` hook in the frontend (`frontend/src/hooks/useGameContext.tsx`). The selected game is stored in local storage and is passed to the backend in API requests.

## Project Structure

```
path-of-mirrors/
├── backend/
│   ├── src/
│   │   ├── contexts/           # Bounded contexts (features)
│   │   ├── infrastructure/     # Cross-cutting concerns (DB, cache, etc.)
│   │   └── main.py             # FastAPI app entrypoint
│   ├── alembic/                # Database migrations
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── main.tsx            # Frontend entrypoint
│   └── package.json
├── scripts/                    # Development scripts
├── docs/                       # Project documentation
└── docker-compose.yml
```
