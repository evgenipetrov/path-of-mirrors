# API Routes Reference

This document provides a comprehensive listing of all API endpoints in Path of Mirrors, organized by bounded context.

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** Configured via environment variables

## Route Pattern

All context routes follow the pattern:

```
/api/v1/{game}/{context}/{resource}
```

Where:

- `{game}` = `poe1` | `poe2` (game context)
- `{context}` = bounded context (notes, catalog, economy, builds, analysis, pob)
- `{resource}` = specific resource within the context

## Global Health Endpoints

### Liveness Check

```
GET /health
```

Returns 200 if application is running.

**Example:**

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{
  "status": "healthy"
}
```

### Readiness Check

```
GET /ready
```

Returns 200 if all dependencies (database, Redis) are healthy, 503 otherwise.

**Example:**

```bash
curl http://localhost:8000/ready
```

**Response:**

```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "redis": true
  }
}
```

## Context Routes

### Notes Context (Placeholder)

**Base Path:** `/api/v1/{game}/notes`

#### Health Check

```
GET /api/v1/{game}/notes/health
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/notes/health
```

#### Create Note

```
POST /api/v1/{game}/notes
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/poe1/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Note", "content": "This is a test note"}'
```

#### List Notes

```
GET /api/v1/{game}/notes
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/notes
```

#### Get Note

```
GET /api/v1/{game}/notes/{note_id}
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/notes/550e8400-e29b-41d4-a716-446655440000
```

#### Update Note

```
PUT /api/v1/{game}/notes/{note_id}
```

**Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/poe1/notes/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "content": "Updated content"}'
```

#### Delete Note

```
DELETE /api/v1/{game}/notes/{note_id}
```

**Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/poe1/notes/550e8400-e29b-41d4-a716-446655440000
```

______________________________________________________________________

### Catalog Context

**Base Path:** `/api/v1/{game}/catalog`

#### Health Check

```
GET /api/v1/{game}/catalog/health
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/catalog/health
```

______________________________________________________________________

### Economy Context

**Base Path:** `/api/v1/{game}/items`

#### Health Check

```
GET /api/v1/{game}/items/health
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/items/health
```

#### Search Items

```
POST /api/v1/{game}/items/search
```

Search for items on Trade API with filtering.

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/poe1/items/search \
  -H "Content-Type: application/json" \
  -d '{
    "league": "Settlers",
    "item_type": "Jade Amulet",
    "min_life": 80,
    "max_price_chaos": 50,
    "limit": 10
  }'
```

______________________________________________________________________

### Builds Context

**Base Path:** `/api/v1/{game}/builds`

#### Health Check

```
GET /api/v1/{game}/builds/health
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/builds/health
```

#### Parse Build

```
POST /api/v1/{game}/builds/parse
```

Parse Path of Building file or import code into standardized Build object.

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/poe1/builds/parse \
  -H "Content-Type: application/json" \
  -d '{"pob_code": "eNqVW2uT2zYS..."}'
```

#### Analyze Build

```
POST /api/v1/{game}/builds/analyze
```

Analyze build to calculate stat weights and upgrade priorities.

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/poe1/builds/analyze \
  -H "Content-Type: application/json" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

#### Get Canonical Stats

```
GET /api/v1/{game}/builds/stats
```

Get canonical stat definitions for a specific game.

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/builds/stats
```

______________________________________________________________________

### Analysis Context

**Base Path:** `/api/v1/{game}/analysis`

#### Health Check

```
GET /api/v1/{game}/analysis/health
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/analysis/health
```

#### Rank Items

```
POST /api/v1/{game}/analysis/rank
```

Rank candidate items against a target item with optional stat weights.

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/poe1/analysis/rank \
  -H "Content-Type: application/json" \
  -d '{
    "target_item": {...},
    "candidates": [{...}, {...}],
    "stat_weights": {"life": 2.0, "fire_res": 0.8}
  }'
```

______________________________________________________________________

### PoB (Path of Building) Context

**Base Path:** `/api/v1/{game}/pob`

#### Health Check

```
GET /api/v1/{game}/pob/health
```

**Example:**

```bash
curl http://localhost:8000/api/v1/poe1/pob/health
```

#### Parse PoB

```
POST /api/v1/{game}/pob/parse
```

Parse Path of Building file or import code (standalone parser endpoint).

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/poe1/pob/parse \
  -H "Content-Type: application/json" \
  -d '{"pob_code": "eNqVW2uT2zYS..."}'
```

______________________________________________________________________

## Route Contract Summary

| Context      | Base Path                 | Tag        | Status         |
| ------------ | ------------------------- | ---------- | -------------- |
| **Notes**    | `/api/v1/{game}/notes`    | `notes`    | Phase 0 (Demo) |
| **Catalog**  | `/api/v1/{game}/catalog`  | `catalog`  | Stub           |
| **Economy**  | `/api/v1/{game}/items`    | `economy`  | Stub           |
| **Builds**   | `/api/v1/{game}/builds`   | `builds`   | Stub           |
| **Analysis** | `/api/v1/{game}/analysis` | `analysis` | Stub           |
| **PoB**      | `/api/v1/{game}/pob`      | `pob`      | Stub           |

## Interactive Documentation

For a complete, interactive API reference with schemas and try-it-out functionality:

- **Swagger UI:** http://localhost:8000/docs
- **OpenAPI Spec:** http://localhost:8000/openapi.json

## Common Response Patterns

### Success Responses

- **200 OK** - Successful GET, PUT requests
- **201 Created** - Successful POST creating a resource
- **204 No Content** - Successful DELETE requests

### Error Responses

All errors follow RFC 7807 problem details format:

```json
{
  "detail": "Note with id 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

Common status codes:

- **400 Bad Request** - Invalid input data
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **500 Internal Server Error** - Server error
- **503 Service Unavailable** - Dependencies unhealthy (from `/ready`)

## Filtering

Game context filtering is handled via path parameter:

- `/api/v1/poe1/*` - PoE 1 resources
- `/api/v1/poe2/*` - PoE 2 resources

(Prefix with `-` for descending order)
