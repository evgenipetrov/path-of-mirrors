# API Changelog

This document tracks breaking changes and major updates to the Path of Mirrors API.

## 2025-11-22 - API URL Consistency Sprint

**Status:** ✅ Completed

### Breaking Changes

#### Notes API
- **BREAKING:** Removed `game_context` field from request bodies for Notes endpoints
  - `POST /api/v1/{game}/notes` now takes game from path parameter only
  - `PUT /api/v1/{game}/notes/{note_id}` now takes game from path parameter only
  - Request schemas `NoteCreate` and `NoteUpdate` no longer accept `game_context`
  - Game context is now validated from the URL path parameter

#### Health Endpoints
- **NEW:** Added per-context health endpoints for all contexts:
  - `GET /api/v1/{game}/notes/health` - Notes context health check
  - `GET /api/v1/{game}/items/health` - Economy context health check
  - `GET /api/v1/{game}/pob/health` - PoB context health check
  - Existing health endpoints for builds, analysis, and catalog unchanged

### Migration Guide

#### Frontend Changes
1. Regenerate API client: `./scripts/generate-api.sh`
2. Update any manual calls to notes endpoints:
   ```typescript
   // Before
   createNote({ game_context: 'poe1', title: 'My Note', content: '...' })

   // After
   createNote({ game: 'poe1', data: { title: 'My Note', content: '...' } })
   ```

#### Backend Changes
- No migration needed for consumers - all routes maintain backward compatibility via path parameters
- Internal services now receive `game` as an explicit parameter instead of from request body

### Rationale
This change completes the API URL consistency sprint, ensuring:
- Single, predictable location for game selection (`/api/v1/{game}/...`)
- No duplicate game parameters in path + body
- Consistent health check pattern across all contexts
- Cleaner OpenAPI spec and generated client code

### Testing
- ✅ 194 backend tests pass, 3 skipped (upstream API route tests now included)
- ✅ 7 upstream API route tests now running (fixed REPO_ROOT path issue)
- ✅ Health endpoints verified via manual curl: `/api/v1/{poe1|poe2}/{notes|items|pob}/health`

### Related Documents
- Sprint plan: [SPRINT.md](SPRINT.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
