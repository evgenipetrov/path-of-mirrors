# Observability & Structured Logging

Path of Mirrors uses **structured logging** with automatic request tracing to ensure all logs are queryable, debuggable, and traceable across the entire request lifecycle.

## Table of Contents

- [Architecture](#architecture)
- [Request ID Propagation](#request-id-propagation)
- [Usage Examples](#usage-examples)
- [Log Formats](#log-formats)
- [Querying Logs](#querying-logs)
- [Testing](#testing)

______________________________________________________________________

## Architecture

### Structured Logging Stack

- **Library:** [structlog](https://www.structlog.org/) - Python structured logging
- **Format:** JSON (production) / Console (development)
- **Request Tracing:** Automatic via middleware + contextvars
- **Output:** stdout (captured by Docker/K8s)

### Key Components

```
┌─────────────────────────────────────────────────────┐
│           RequestLoggingMiddleware                   │
│  1. Generate request_id (UUID)                       │
│  2. Bind to structlog context                        │
│  3. Add X-Request-ID header to response              │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              structlog Configuration                 │
│  - contextvars processor (automatic context merge)  │
│  - JSONRenderer (production)                         │
│  - ConsoleRenderer (development)                     │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           Application Logs (All Services)            │
│  Every log call automatically includes:              │
│  - request_id                                        │
│  - method (GET/POST/etc)                             │
│  - path (/api/v1/...)                                │
│  - timestamp                                         │
│  - log level                                         │
└─────────────────────────────────────────────────────┘
```

______________________________________________________________________

## Request ID Propagation

### How It Works

Every HTTP request automatically gets a **unique request_id** (UUID v4) that is:

1. **Generated** by `RequestLoggingMiddleware` at request start
1. **Bound** to structlog context via `structlog.contextvars.bind_contextvars()`
1. **Propagated** automatically to all log calls during the request
1. **Returned** in the `X-Request-ID` response header
1. **Cleared** at the start of the next request (no leakage)

### Code Flow

```python
# 1. Middleware generates request_id
request_id = str(uuid4())

# 2. Bind to structlog context
structlog.contextvars.bind_contextvars(
    request_id=request_id,
    method=request.method,
    path=request.url.path,
)

# 3. All subsequent logs automatically include request_id
logger.info("processing_user_data", user_id=123)
# Output: {"event": "processing_user_data", "user_id": 123, "request_id": "...", ...}

# 4. Add to response headers
response.headers["X-Request-ID"] = request_id
```

### No Manual Passing Required

Because request_id is bound to **contextvars**, you never need to manually pass it:

```python
# ❌ Old way (manual passing - NOT needed)
def service_method(user_id: int, request_id: str):
    logger.info("processing", user_id=user_id, request_id=request_id)

# ✅ New way (automatic propagation)
def service_method(user_id: int):
    logger.info("processing", user_id=user_id)  # request_id added automatically
```

______________________________________________________________________

## Usage Examples

### Basic Logging

```python
from src.infrastructure import get_logger

logger = get_logger(__name__)

# Simple event logging
logger.info("market_snapshot_fetched", game="poe1", league="Settlers")
```

**Output (production JSON):**

```json
{
  "event": "market_snapshot_fetched",
  "game": "poe1",
  "league": "Settlers",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/api/v1/poe1/items/search",
  "timestamp": "2025-01-22T10:30:00.123Z",
  "level": "info"
}
```

**Output (development console):**

```
2025-01-22 10:30:00 [info     ] market_snapshot_fetched  game=poe1 league=Settlers request_id=550e8400...
```

### Logging with Metrics

```python
import time

start = time.time()
# ... do work ...
duration_ms = (time.time() - start) * 1000

logger.info(
    "api_call_completed",
    api="poe_ninja",
    status_code=200,
    duration_ms=round(duration_ms, 2),
    item_count=1234,
)
```

### Logging Errors

```python
try:
    result = await trade_api.search(query)
except Exception as e:
    logger.error(
        "trade_api_search_failed",
        error=str(e),
        error_type=type(e).__name__,
        query=query,
    )
    raise
```

### Logging with Additional Context

```python
# Bind additional context for a block of code
from structlog.contextvars import bind_contextvars

bind_contextvars(user_id=user.id, game="poe1")

logger.info("processing_build_analysis")  # Includes user_id and game
# ...
logger.info("analysis_complete")  # Also includes user_id and game
```

______________________________________________________________________

## Log Formats

### Development (Console)

**Configuration:**

- Enabled when: `ENVIRONMENT=local`
- Renderer: `structlog.dev.ConsoleRenderer()`
- Output: Human-readable colored text

**Example:**

```
2025-01-22 10:30:00 [info     ] request_started          method=GET path=/api/v1/poe1/notes request_id=550e8400-e29b-41d4-a716-446655440000 client_ip=127.0.0.1
2025-01-22 10:30:00 [info     ] fetching_notes           game=poe1
2025-01-22 10:30:00 [info     ] request_completed        status_code=200 duration_ms=45.32
```

### Production (JSON)

**Configuration:**

- Enabled when: `ENVIRONMENT=production` or `staging`
- Renderer: `structlog.processors.JSONRenderer()`
- Output: Newline-delimited JSON (NDJSON)

**Example:**

```json
{"event":"request_started","method":"GET","path":"/api/v1/poe1/notes","request_id":"550e8400-e29b-41d4-a716-446655440000","client_ip":"127.0.0.1","timestamp":"2025-01-22T10:30:00.123Z","level":"info"}
{"event":"fetching_notes","game":"poe1","request_id":"550e8400-e29b-41d4-a716-446655440000","timestamp":"2025-01-22T10:30:00.145Z","level":"info"}
{"event":"request_completed","status_code":200,"duration_ms":45.32,"request_id":"550e8400-e29b-41d4-a716-446655440000","timestamp":"2025-01-22T10:30:00.168Z","level":"info"}
```

______________________________________________________________________

## Querying Logs

### Using Docker Compose

**View all logs:**

```bash
./scripts/view-logs.sh backend -f
```

**Filter by request_id:**

```bash
docker compose logs backend | grep "550e8400-e29b-41d4-a716-446655440000"
```

### Using jq (Production JSON logs)

**Extract all events for a specific request:**

```bash
docker compose logs backend --no-log-prefix | jq -r 'select(.request_id == "550e8400-e29b-41d4-a716-446655440000")'
```

**Find slow requests (>1000ms):**

```bash
docker compose logs backend --no-log-prefix | jq -r 'select(.duration_ms > 1000)'
```

**Count requests by status code:**

```bash
docker compose logs backend --no-log-prefix | jq -r '.status_code' | sort | uniq -c
```

### Using Observability Platforms

In production, ship logs to:

- **Datadog:** Filter by `@request_id` field
- **Elasticsearch/Kibana:** Query `request_id.keyword`
- **Grafana Loki:** `{app="path-of-mirrors"} | json | request_id="..."`
- **CloudWatch Logs:** Insights query on `fields.request_id`

______________________________________________________________________

## Testing

### Automated Tests

Tests for request_id propagation are in:

```
backend/tests/infrastructure/test_request_id_propagation.py
```

**Run tests:**

```bash
cd backend
uv run pytest tests/infrastructure/test_request_id_propagation.py -v
```

**What's tested:**

- ✅ X-Request-ID header is present in responses
- ✅ Request IDs are valid UUIDs
- ✅ Different requests get different request_ids
- ✅ Context is cleared between requests (no leakage)

### Manual Testing

**1. Check X-Request-ID header:**

```bash
curl -I http://localhost:8000/health
# Look for: X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

**2. Trace a request through logs:**

```bash
# 1. Make a request and capture the request_id
REQUEST_ID=$(curl -s -I http://localhost:8000/api/v1/poe1/notes/health | grep -i x-request-id | awk '{print $2}' | tr -d '\r')

# 2. View all logs for that request
docker compose logs backend | grep "$REQUEST_ID"
```

**Expected output:**

```
request_started       request_id=550e8400... method=GET path=/api/v1/poe1/notes/health
notes_health_check    request_id=550e8400... game=poe1
request_completed     request_id=550e8400... status_code=200 duration_ms=12.34
```

______________________________________________________________________

## Best Practices

### DO ✅

- Use structured key-value logging: `logger.info("event_name", key1=value1, key2=value2)`
- Use snake_case for log keys
- Log business events, not implementation details
- Include metrics where relevant (duration_ms, item_count, etc.)
- Use appropriate log levels (info for normal operations, error for failures)

### DON'T ❌

- Don't log sensitive data (passwords, API keys, PII)
- Don't log request_id manually (it's automatic)
- Don't use string formatting in logs: `logger.info(f"User {user_id}")` ❌
- Don't over-log (every line) or under-log (only errors)

### Log Levels

- **DEBUG:** Verbose diagnostic information (disabled in production)
- **INFO:** Normal operational events (API calls, business events)
- **WARNING:** Unexpected but handled situations (deprecated API usage, slow queries)
- **ERROR:** Errors that require attention (failed API calls, exceptions)

______________________________________________________________________

## Configuration

### Environment Variables

```bash
# .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=local  # local, staging, production
```

### Changing Log Level

**Temporary (for debugging):**

```bash
LOG_LEVEL=DEBUG docker compose up backend
```

**Permanent:**
Edit `backend/.env` and restart services.

______________________________________________________________________

## Future Enhancements

### Planned (Phase 2+)

- [ ] Distributed tracing with OpenTelemetry
- [ ] Request metrics (latency percentiles, throughput)
- [ ] Error rate alerting (5xx rates, SLO tracking)
- [ ] Log sampling for high-volume endpoints

______________________________________________________________________

## References

- **structlog documentation:** https://www.structlog.org/
- **Middleware implementation:** `backend/src/infrastructure/middleware.py`
- **Logging configuration:** `backend/src/infrastructure/logging.py`
- **Tests:** `backend/tests/infrastructure/test_request_id_propagation.py`

______________________________________________________________________

## Quick Reference

**Get a logger:**

```python
from src.infrastructure import get_logger
logger = get_logger(__name__)
```

**Log an event:**

```python
logger.info("event_name", key1=value1, key2=value2)
```

**View logs:**

```bash
./scripts/view-logs.sh backend -f
```

**Find a specific request:**

```bash
docker compose logs backend | grep "request_id"
```
