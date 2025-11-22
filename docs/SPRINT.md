
# Sprint: API URL Consistency (poe1/poe2)

**Duration:** 1 week
**Goal:** Make game selection and versioning consistent across all backend endpoints and surface the changes to the API client/frontend.
**Assumption:** Greenfield API — no backward compatibility required; we can break existing paths.

---

## Objectives
- Single, predictable location for `game` (`poe1|poe2`) in every endpoint.
- Uniform versioned base path (`/api/v1`), no mixed legacy prefixes.
- Remove duplicate or dead routers to avoid shadowed routes.
- Ship updated client contract (OpenAPI + generated frontend client) with minimal breakage plan.

## Current Gaps (baseline)
- `game` lives in three places: query (`/api/notes?game=`), path (`/api/v1/builds/stats/{game}`), and request body (builds, economy, pob parse).
- Notes router is unversioned (`/api/notes`) while others use `/api/v1/...`.
- Two routers define `/api/v1/builds` (builds vs upstream/builds_routes); only one is mounted.

## Design Decisions
- **Base path:** `/api/v1` for all contexts (including notes).
- **Game placement:** path segment immediately after version → `/api/v1/{game}/...` (accepted values: `poe1`, `poe2`).
- **Noun pluralization:** prefer plural resources (`/items` not `/item`).
- **Per-context health:** `/api/v1/{game}/{context}/health` (keep global `/health` and `/ready`).
- **Deprecations:** remove unused `contexts/upstream/api/builds_routes.py` or merge its functionality into the active builds router.
- **Compatibility:** no legacy routes or shims; clients must adopt the new paths.

## Deliverables
1) ✅ Updated FastAPI routers reflecting the new URL scheme.
2) ❌ Migration shim (temporary) to accept old URLs with deprecation warnings - **SKIPPED** (greenfield assumption; no production users to migrate).
3) ✅ Regenerated OpenAPI spec + frontend API client.
4) ✅ Brief change log for frontend/backend consumers (docs/CHANGELOG.md).

## Plan (step-by-step)
1) **Inventory & mapping** – enumerate every current route, map old → new URL, decide which require shims.
2) **Router refactor** –
   - Add `{game}` path param to notes, builds, pob, economy, analysis routes.
   - Normalize prefixes to `/api/v1/{game}/...` and pluralize `/item` → `/items`.
   - Remove or integrate `upstream/api/builds_routes.py` to avoid duplicate `/builds` prefix.
3) **Dependency updates** – ensure downstream services/functions accept `game` from path (propagate through services where bodies previously carried it).
4) **Health endpoints** – standardize per-context health under new scheme; keep global `/health` + `/ready` untouched.
5) **Backward compatibility** – skipped (greenfield; breaking changes allowed).
6) **Docs & schema** – regenerate OpenAPI, update `docs/README.md` route tables, and rebuild frontend API client (`./scripts/generate-api.sh`).
7) **Tests** – update existing tests and add coverage for both `poe1`/`poe2` path variants; verify `./scripts/run-tests.sh --backend --coverage`.

## Risks & Mitigations
- **Client breakage:** Mitigate with temporary shims and explicit changelog.
- **Hidden `game` assumptions in services:** Use typing + mypy to surface missing plumbed params.
- **Routing conflicts:** Remove dead router before refactor to prevent overlap.

## Definition of Done
- All routes mounted under `/api/v1/{game}/...` (no remaining mixed patterns).
- No duplicate `/api/v1/builds` router registrations.
- OpenAPI + generated client reflect new paths; frontend builds without manual edits.
- Tests green via `./scripts/run-tests.sh --backend --frontend`.
