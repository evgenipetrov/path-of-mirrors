# Sprint: Automated Codebase Alignment & Governance

## Objective

Implement a fully automated "Gold Standard" system to prevent drift between backend code, frontend clients, and documentation. This system replaces human process (CODEOWNERS, manual reviews) with deterministic CI/CD checks and scripts.

## 1. Single Source of Truth & Synchronization

- [ ] **Enforce OpenAPI Freshness**
  - Create `scripts/check-schema.sh`: Generates OpenAPI spec in memory and compares with `backend/openapi.json`. Fails if they differ.
  - Update `scripts/generate-api.sh`: Add auto-commit capability or pre-commit hook integration.
- [ ] **Automated Client Regeneration**
  - Ensure `frontend/src/api` is strictly read-only for humans.
  - Add CI step: Fail if `npm run generate-api` results in file changes (implies committed client is stale).

## 2. Automated Drift Guards (The "Docs Check")

- [ ] **Route-to-Doc Consistency**
  - Create `scripts/check-docs.sh`:
    - Introspect FastAPI app to get list of all registered routes (method + path).
    - Parse `docs/API_ROUTES.md` (and potentially `QUICKSTART.md`).
    - **Failure Condition**: Any active route not found in markdown tables.
    - **Failure Condition**: Any documented route that no longer exists in code.
- [ ] **Dependency Lock Consistency**
  - Add `uv sync --locked --check` to backend CI.
  - Add `npm ci --dry-run` to frontend CI.

## 3. Interface Fitness Functions (Contract Tests)

- [ ] **Black-box Contract Test**
  - Create `scripts/test-contract.sh`:
    1. Build/Start Backend (Docker).
    1. Generate *ephemeral* TS client from current `openapi.json`.
    1. Run a minimal TS script using this client to perform "smoke tests" (Health, Auth, basic resource fetch).
    1. **Goal**: Verify that the generated types match the actual runtime JSON responses.
- [ ] **Startup Health Assertions**
  - Implement `backend/src/initializers/check_resources.py`:
    - Validate DB connection.
    - Validate Redis connection.
    - Validate critical config variables (fail fast if missing).
  - Run this before `uvicorn` starts serving traffic.

## 4. Tight Developer Feedback Loop

- [ ] **Unified `check-all` Script**
  - Refactor `scripts/check-code.sh` to include:
    - `check-schema.sh` (Is OpenAPI up to date?)
    - `check-docs.sh` (Are docs up to date?)
    - `check-locks.sh` (Are deps locked?)
    - Existing linters (ruff, mypy, eslint, tsc).
- [ ] **Pre-commit / Pre-push Guardrails**
  - Add `.pre-commit-config.yaml` with fast per-commit hooks:
    - Backend: `ruff`, `ruff-format`, `mypy`, trailing whitespace, detect-private-key.
    - Frontend: `eslint`, `prettier --check`, `knip --changed` for dead code on touched files.
    - Scripts: `shellcheck`, `yamllint`, json/yaml validators.
  - Add **pre-push** stage (via pre-commit `stages: [push]` or `.git/hooks/pre-push`) running heavy gates:
    - Backend: `uv run pytest --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing --cov-fail-under=70`.
    - Frontend: `npm test -- --runInBand --coverage` (or `vitest run --coverage`).
    - Optional CI-only: `npm run knip` full project, `ruff --select C90` (complexity), `vulture` for dead code.
  - Document setup in `docs/CONTRIBUTING.md`: `uv tool install pre-commit`, `pre-commit install`, `pre-commit install --hook-type pre-push`, `npm install` in `frontend/`.
  - Mirror the same commands in CI to ensure local == CI behavior.

## 5. Observability & Hygiene

- [ ] **Structured Logging**
  - Replace standard logging with `structlog` or similar JSON formatter.
  - Ensure `request_id` is propagated through all logs.
- [ ] **Stability Budget**
  - Add middleware to track 5xx rates and latency.

## 6. Versioning Strategy

- [ ] **Semantic Release Automation**
  - Setup `semantic-release` (or similar) to parse commit messages and bump versions in `pyproject.toml` / `package.json` automatically.
