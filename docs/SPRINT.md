# Sprint: Backlog Burn — Fix Critical Parity & Stability Gaps

**Duration:** 1 week  
**Goal:** Resolve the six highest-impact issues uncovered in the audit: broken frontend API client, route/docs desync, misleading infra claims, HTTP client leaks, brittle config loading, and dead/stubbed modules.

---

## Objectives
- Restore working frontend→backend calls by aligning the API client contract with Orval-generated hooks.
- Bring public docs (README/QUICKSTART) into strict agreement with actual FastAPI routes and paths.
- Remove infra misinformation (Traefik, ARQ) or add the missing pieces; the docs must match the repo.
- Eliminate HTTP client leaks in upstream trade calls and introduce lifecycle-managed clients.
- Make config loading fail-safe (no `sys.exit` inside request paths) with startup-time validation.
- Clarify or excise empty stubs so the code surface reflects reality.

---

## Plan (issue-aligned)

1) **Frontend API client contract**
   - Refactor `frontend/src/lib/api-client.ts` to accept AxiosRequestConfig and return `AXIOS_INSTANCE(config)`; keep cancellation support.
   - Add a minimal integration test using `useListNotesApiV1GameNotesGet` against a mocked Axios adapter to prevent regressions.
   - Optional: regenerate hooks with `--client axios` to enforce shape alignment (documented fallback).

2) **Docs ↔ Routes parity**
   - Update `README.md` and `docs/QUICKSTART.md` endpoint sections to the real paths: `/api/v1/{game}/notes` etc.; include working curl examples for all CRUD verbs.
   - Add a short “route contract” table to `docs/CHANGELOG.md` (or new `docs/API_ROUTES.md`) that lists each context and base path.

3) **Infra claims (Traefik/ARQ) correction**
   - Edit `docs/ARCHITECTURE.md` to remove Traefik and ARQ assertions; state current stack (nginx only, no job runner yet) and mark ingestion/jobs as “planned”.
   - If future work is desired, open TODOs in `docs/ARCHITECTURE.md` with prerequisites instead of implying they exist.

4) **HTTP client lifecycle**
   - Introduce a shared `httpx.AsyncClient` created in `main.lifespan`; pass/inject into upstream trade services.
   - Ensure graceful shutdown via `client.aclose()` in lifespan teardown; add a unit test that monkeypatches the client and asserts close is called.

5) **Config loading resilience**
   - Replace `sys.exit` calls in `backend/src/infrastructure/config/base.py` with custom exceptions; validate configs once during startup and fail FastAPI boot with clear logs.
   - Add tests for missing/invalid config files that assert exceptions, not process exit.

6) **Stub cleanup and signaling**
   - For empty modules (`upstream/services/ingestion_service.py`, `core/ports/repository.py`, `core/adapters/postgres_repository.py`), replace bodies with `NotImplementedError` and a concise module docstring noting planned scope; or delete if out-of-scope.
   - Update `docs/ARCHITECTURE.md` “Current state” section to match the pared-down surface area.

---

## Deliverables
- Patched `api-client.ts` + passing integration test.
- Updated README/QUICKSTART route examples; new/updated route contract table.
- Corrected architecture doc (no Traefik/ARQ unless implemented).
- HTTP client lifespan management in backend with tests.
- Config loader raising exceptions, tested.
- Stub modules either deleted or explicitly marked; docs aligned.

---

## Validation & Exit Criteria
- `npm test` (frontend) passes, including new API client smoke test.
- `./scripts/run-tests.sh --backend --coverage` passes (config + http client tests included).
- Hitting `/api/v1/poe1/notes` via generated hook works in dev (manual smoke).
- Docs reviewed: no claimed component lacks code/config in repo.

---

## Risk & Mitigation
- **Axios contract drift:** lock a test around the generated hook signature and `api-client`.
- **Unhandled startup failure:** ensure config exceptions surface during app boot, not mid-request; add log guidance.
- **Doc rot recurrence:** lightweight checklist added to PR template (future work) to touch docs when routes/config change.
