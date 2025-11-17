# Architecture Overview

Path of Mirrors is built as a **modular monolith** with **hexagonal architecture** principles, designed to evolve from a single-user local application into a scalable economic intelligence platform for Path of Exile.

## Tech Stack

### Backend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Web Framework** | FastAPI | Modern async framework, excellent OpenAPI support, high performance |
| **ORM** | SQLAlchemy 2.0 (async) | Mature, powerful query capabilities, async support for data pipelines |
| **Database** | PostgreSQL 17 | Advanced features (materialized views, JSONB), excellent for analytics |
| **Migrations** | Alembic | Industry standard, works seamlessly with SQLAlchemy |
| **Package Manager** | uv | Fast, modern Python package management with lock files |
| **Background Jobs** | Redis + ARQ | Async task queue for poe.ninja polling and data ingestion |
| **Python Version** | 3.12+ | Modern Python with performance improvements and better typing |

**Starting point:** [benavlabs/fastapi-boilerplate](https://github.com/benavlabs/fastapi-boilerplate) - provides uv, SQLAlchemy 2.0, Redis/ARQ, and Docker setup out of the box.

### Frontend

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Framework** | React 18+ | Industry standard, excellent ecosystem, concurrent rendering |
| **UI Components** | shadcn/ui | Copy-paste components with full control, AI-friendly, beautiful defaults |
| **Data Tables** | TanStack Table | Best-in-class for dense data: virtualization, sorting, filtering, grouping for 100k+ rows |
| **Dashboards/Charts** | Tremor | Purpose-built for data-dense UIs, Tailwind-based, KPIs and charts optimized for decisions |
| **Styling** | Tailwind CSS | Utility-first, excellent DX, easy theming for PoE aesthetic |
| **State Management** | TanStack Query | Perfect for server state, built-in caching/refetch/loading states |
| **Build Tool** | Vite | Fast HMR, modern build pipeline, great DX |
| **API Client** | orval | Generates TypeScript types + TanStack Query hooks from OpenAPI spec |
| **Node Version** | LTS (20+) | Long-term support, stable |

**Stack optimized for:** Displaying thousands of rows of economic data with advanced filtering, sorting, and visualization for data-driven decision making.

### Infrastructure

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Container Runtime** | Docker Compose | Local development parity with production, easy multi-service orchestration |
| **Reverse Proxy** | Traefik | Automatic SSL, service discovery, works well with Docker Compose |
| **Cache/Queue** | Redis | Fast in-memory store for API caching and background job queue |
| **Observability** | structlog | Structured logging for Python, easy to query and debug |

### Testing

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend Tests** | pytest + pytest-asyncio | Standard Python testing, excellent async support |
| **Frontend Tests** | React Testing Library + Vitest | Component testing best practices, fast test runner |
| **E2E Tests** | Playwright (Phase 1+) | Reliable cross-browser testing for critical user flows |
| **CI/CD** | GitHub Actions | Standard CI platform, easy integration with Docker |

---

## Architectural Patterns

### Hexagonal Architecture (Ports and Adapters)

Path of Mirrors follows hexagonal architecture to isolate domain logic from infrastructure concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     Adapters (Infrastructure)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ FastAPI  │  │PostgreSQL│  │ poe.ninja│  │  Redis  │ │
│  │ REST API │  │ Repository│  │  Client  │  │  Cache  │ │
│  └────┬─────┘  └─────┬────┘  └─────┬────┘  └────┬────┘ │
│       │              │              │             │      │
│  ┌────▼──────────────▼──────────────▼─────────────▼───┐ │
│  │              Ports (Interfaces)                     │ │
│  │  - HTTP Controllers                                 │ │
│  │  - Repository Interfaces                            │ │
│  │  - External API Interfaces                          │ │
│  └──────────────────────┬──────────────────────────────┘ │
│                         │                                 │
│  ┌──────────────────────▼──────────────────────────────┐ │
│  │           Domain Core (Business Logic)              │ │
│  │  - Market Intelligence                              │ │
│  │  - Crafting Logic                                   │ │
│  │  - Item Valuation                                   │ │
│  │  - Game-agnostic models                             │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Benefits:**
- Domain logic is testable without infrastructure
- Easy to swap adapters (e.g., different data sources)
- Clear dependency direction (infrastructure → domain, never reverse)

### Bounded Contexts

Each major capability is organized into a bounded context with its own:
- Domain models
- Service layer
- Repository interfaces
- API endpoints
- Tests

**Planned Bounded Contexts (Phase 1+):**
```
backend/src/
├── contexts/
│   ├── market/          # Market Intelligence (Phase 2)
│   ├── crafting/        # Crafting Assistant (Phase 3)
│   ├── deals/           # Deal Finder (Phase 4)
│   ├── pricing/         # Price Checker (Phase 5)
│   └── upstream/        # Data ingestion (Phase 1)
├── shared/              # Shared domain models, utilities
└── infrastructure/      # Cross-cutting: DB, cache, logging
```

**Phase 0 Structure:**
```
backend/src/
├── contexts/
│   └── placeholder/     # Dummy CRUD to validate stack
├── shared/
│   └── game_selector.py # Game context enum (PoE1/PoE2)
└── infrastructure/
    ├── database.py
    ├── logging.py
    └── health.py
```

---

## Game Abstraction Layer

Path of Mirrors supports both **PoE1 and PoE2** from Phase 1 onward through a pluggable adapter pattern.

### Design Principles

1. **Shared Core Models:** Common abstractions (Item, Modifier, Build) work across both games
2. **Game-Specific Adapters:** Each game has its own schema parser, API client, and normalization logic
3. **Context Switching:** User selects game in UI; all features operate on that game's data context

### Structure

```
backend/src/contexts/upstream/
├── domain/
│   ├── item.py              # Canonical item model (game-agnostic)
│   ├── modifier.py          # Canonical modifier model
│   └── league.py            # League abstraction
├── adapters/
│   ├── poe1/
│   │   ├── schema.py        # PoE1-specific schema
│   │   ├── poeninja.py      # PoE1 poe.ninja client
│   │   └── normalizer.py    # PoE1 → canonical mapping
│   └── poe2/
│       ├── schema.py        # PoE2-specific schema
│       ├── poeninja.py      # PoE2 poe.ninja client
│       └── normalizer.py    # PoE2 → canonical mapping
└── ports/
    ├── league_provider.py   # Interface: get_active_leagues()
    └── item_provider.py     # Interface: fetch_items(game, league)
```

### Example: Fetching Market Data

```python
# Domain service (game-agnostic)
async def get_market_snapshot(game: Game, league: str) -> MarketSnapshot:
    provider = get_provider(game)  # Factory returns PoE1Provider or PoE2Provider
    raw_data = await provider.fetch_snapshot(league)
    return provider.normalize(raw_data)  # Returns canonical MarketSnapshot
```

---

## Data Flow

### Phase 0: Validation Flow
```
User → React UI → FastAPI → PostgreSQL → React UI
         (Dummy CRUD entity - proves stack works)
```

### Phase 1: Ingestion Flow
```
ARQ Scheduler (daily) → poe.ninja API → Normalizer → PostgreSQL
                                                    → Redis (cache)
```

### Phase 2+: Query Flow
```
User → React (Game Selector: PoE1/PoE2)
    → TanStack Query → FastAPI → PostgreSQL (filtered by game)
    → TanStack Table (10k+ rows with virtualization)
    → Tremor Charts (price trends, KPIs)
```

---

## Data Strategy

### PostgreSQL Schema Design

**Principles:**
- Game-specific tables (e.g., `poe1_items`, `poe2_items`)
- Shared analytics views (e.g., `market_trends` unions data from both games)
- Partitioning by date for time-series data (28-day retention)

**Example Schema (Phase 1):**
```sql
-- Game-specific tables
CREATE TABLE poe1_snapshots (
    id UUID PRIMARY KEY,
    league VARCHAR NOT NULL,
    snapshot_date TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL  -- Raw poe.ninja response
) PARTITION BY RANGE (snapshot_date);

CREATE TABLE poe2_snapshots (
    id UUID PRIMARY KEY,
    league VARCHAR NOT NULL,
    snapshot_date TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL
) PARTITION BY RANGE (snapshot_date);

-- Normalized canonical items (game-agnostic view)
CREATE MATERIALIZED VIEW canonical_items AS
SELECT 'poe1' AS game, league, (data->>'name') AS name, ...
FROM poe1_snapshots
UNION ALL
SELECT 'poe2' AS game, league, (data->>'name') AS name, ...
FROM poe2_snapshots;
```

### Data Retention Policy

- **28-day rolling window:** Automated cleanup job deletes snapshots older than 28 days
- **Materialized views:** Refreshed daily for trend analysis
- **Object storage (TBD):** Raw snapshots may be archived to S3/MinIO for replayability (decision deferred to Phase 1)

---

## Observability

### Logging Strategy

**Structured logging with context:**
```python
import structlog

log = structlog.get_logger()

log.info("market_snapshot_fetched",
    game="poe1",
    league="Settlers",
    item_count=1234,
    duration_ms=456
)
```

**Output:**
```json
{
  "event": "market_snapshot_fetched",
  "game": "poe1",
  "league": "Settlers",
  "item_count": 1234,
  "duration_ms": 456,
  "timestamp": "2025-11-17T10:30:00Z"
}
```

### Health Endpoints

- `GET /health` - Basic liveness check
- `GET /ready` - Readiness check (DB connection, Redis connection)
- `GET /metrics` - Prometheus-style metrics (Phase 2+)

### Request Tracing

- Request ID injected into all logs
- Frontend sends `X-Request-ID` header
- Backend propagates through all service calls

---

## Frontend Architecture

### Component Structure

```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui components (copied, customizable)
│   ├── tables/          # TanStack Table implementations
│   │   ├── data-table.tsx       # Generic table component
│   │   └── columns/             # Reusable column definitions
│   ├── charts/          # Tremor dashboard components
│   │   ├── price-chart.tsx
│   │   └── metric-cards.tsx
│   ├── game-selector/   # Game context switcher
│   └── features/        # Feature-specific components
│       ├── market/      # Market intelligence tables/charts
│       ├── crafting/    # Crafting calculator
│       └── pricing/     # Price checker
├── hooks/
│   ├── api/             # orval-generated TanStack Query hooks
│   ├── useGameContext.ts
│   └── useTableState.ts # Persist table filters/sorting
├── lib/
│   ├── api-client.ts    # Axios instance with interceptors
│   ├── table-utils.ts   # TanStack Table helpers
│   └── utils.ts
└── pages/
    ├── market.tsx       # Data-dense market overview
    ├── crafting.tsx
    └── pricing.tsx
```

### Dense Data Display Patterns

**TanStack Table for Large Datasets:**
```tsx
import { useReactTable, getCoreRowModel } from '@tanstack/react-table';

// Market items table with 10k+ rows
const table = useReactTable({
  data: marketItems,
  columns,
  getCoreRowModel: getCoreRowModel(),
  enableSorting: true,
  enableFiltering: true,
  enableColumnResizing: true,
  // Virtualization via @tanstack/react-virtual for 100k+ rows
});
```

**Tremor for Dashboard Metrics:**
```tsx
import { Card, Metric, Text, AreaChart } from '@tremor/react';

// KPI cards + price trend chart
<Card>
  <Text>Total Market Value</Text>
  <Metric>1,234,567 chaos</Metric>
</Card>

<AreaChart
  data={priceHistory}
  categories={['chaos', 'divine']}
  index="date"
  colors={['amber', 'cyan']}
/>
```

### State Management Pattern

**Server State (TanStack Query):**
```tsx
// Auto-generated by orval from OpenAPI spec
const { data, isLoading, error } = useGetMarketSnapshot({
  game: gameContext,  // From useGameContext()
  league: 'Settlers'
});
```

**Client State (React Context):**
```tsx
// Game selector context
const { game, setGame } = useGameContext();  // 'poe1' | 'poe2'

// Table state (filters, sorting, pagination)
const { tableState, setTableState } = useTableState('market-items');
```

### Theming

Tailwind CSS with custom PoE-inspired dark theme:
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        poe: {
          bg: '#1a1a1a',      // Dark background
          gold: '#c89b3c',    // Unique item gold
          blue: '#8888ff',    // Magic item blue
          rare: '#ffff77',    // Rare item yellow
        }
      }
    }
  }
}
```

---

## Security Considerations

### Phase 0-1 (Single-User Local)
- No authentication required
- CORS disabled (localhost only)
- No sensitive data stored

### Phase 2+ (Future Multi-User)
- JWT authentication (already in boilerplate, currently unused)
- OAuth integration (GGG/Steam) for character imports
- Rate limiting for public API endpoints
- Input validation via Pydantic schemas

---

## Evolution Path

### Phase 0 → Phase 1
- Add game abstraction layer (Game enum, provider factory)
- Implement poe.ninja adapters for PoE1 and PoE2
- Set up ARQ background jobs for scheduled ingestion

### Phase 1 → Phase 2
- Add `contexts/market/` bounded context
- Implement materialized views for trend queries
- Build Market Dashboard UI with TanStack Table + Tremor (price trends, KPIs, sortable/filterable item tables)

### Monolith → Microservices (Phase 6+)
- Extract bounded contexts into separate services if needed
- Shared database → per-service databases
- API Gateway for routing
- Event-driven architecture with message bus

**Current decision:** Stay monolith through Phase 5. Only extract if scale demands it.

---

## Open Architectural Questions

1. **Object Storage for Raw Snapshots (Phase 1):** S3/MinIO vs PostgreSQL JSONB?
   - Tradeoff: Replayability vs complexity
   - Decision deferred until we see data volumes

2. **Analytics Warehouse (Phase 3+):** PostgreSQL materialized views vs DuckDB/Parquet?
   - Tradeoff: Simplicity vs query performance at scale
   - Start with PostgreSQL, migrate if needed

3. **Real-time Updates (Phase 4+):** WebSockets vs polling?
   - For market alerts and price updates
   - Polling is simpler; defer WebSockets until user demand is clear

---

## References

### Documentation
- [PRODUCT.md](PRODUCT.md) - Product vision and roadmap
- [CONTRIBUTING.md](CONTRIBUTING.md) - Developer setup and workflow
- [SPRINT.md](SPRINT.md) - Phase 0 task breakdown

### Backend
- [benavlabs/fastapi-boilerplate](https://github.com/benavlabs/fastapi-boilerplate) - Starting point for backend
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) - Ports and Adapters pattern

### Frontend
- [shadcn/ui](https://ui.shadcn.com) - UI component philosophy and library
- [TanStack Table](https://tanstack.com/table) - Headless table library for dense data
- [Tremor](https://tremor.so) - React components for dashboards and data visualization
- [TanStack Query](https://tanstack.com/query) - Server state management
