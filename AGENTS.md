# Repository Guidelines

## Project Structure & Module Organization
Path of Mirrors is a dual-service workspace. `backend/` hosts FastAPI contexts under `src/contexts/*`, shared contracts in `src/shared`, infrastructure helpers in `src/infrastructure`, and Alembic migrations in `src/migrations`; `backend/tests` mirrors this tree with fixtures in `tests/conftest.py`. `frontend/` is a Vite + React app with primitives in `src/components/ui`, feature bundles in `src/components/features`, TanStack hooks in `src/hooks/api`, and routes defined in `src/pages`. Docs live in `docs/`; helper scripts in `scripts/`.

## Build, Test, and Development Commands
- `./scripts/start-dev.sh` – boot the full stack with unified logs; Ctrl+C stops it cleanly.
- `docker compose up --watch` – run only the containerized services with live reload.
- Backend: `cd backend && uv run uvicorn src.main:app --reload` for API loops and `uv run alembic upgrade head` to apply migrations.
- Frontend: `cd frontend && npm run dev` for HMR, `npm run generate:api` after OpenAPI changes, `npm run build` to validate production output.

## Coding Style & Naming Conventions
Backend commits must pass Black (line length 100), Ruff, and mypy via `uv run black src tests && uv run ruff check src tests && uv run mypy src`; keep modules async, typed, and grouped by context directories (e.g., `market/services/pricing.py`). Frontend code uses Prettier (`npm run format`), ESLint, and `npm run type-check`; prefer functional components, `ComponentName.tsx` files, `useThing.ts` hooks, and colocated assets inside `src/components/features/<feature>/`.

## Testing Guidelines
Run backend suites with `cd backend && uv run pytest`; isolate domain logic, reuse fixtures, mock PoE APIs, and target >80% coverage. Frontend specs sit beside components as `*.test.tsx`; use `npm test` for single runs, `npm run test:watch` while iterating, and `npm run test:coverage` before PRs. Favor Vitest + React Testing Library for UI paths and keep utility tests lean.

## Commit & Pull Request Guidelines
Use Conventional Commits (`feat|fix|refactor|docs|test|chore`) with imperatives such as `feat: add market dashboard endpoint`. Keep branches focused (`feature/<topic>`), rebase on `main`, and verify formatters, linters, type-checkers, and both test suites locally. PRs need a concise summary, `Closes #issue`, testing notes, UI screenshots when applicable, and doc updates for API or workflow shifts. Expect one maintainer review and squash merge once CI passes.

## Configuration & Ops Notes
Copy `.env.example` in both backend and frontend before running services and never commit secrets. Use `docker compose down -v` to reset PostgreSQL/Redis volumes, redeploy, and `uv run alembic upgrade head`. Consult `docs/QUICKSTART.md` for minimal commands and `docs/CONTRIBUTING.md` for full workflows.
