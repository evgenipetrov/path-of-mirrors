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
│   └── game_context.py  # Game enum (PoE1/PoE2)
└── infrastructure/
    ├── database.py
    ├── logging.py
    └── health.py
```

**Phase 1 Epic 1.1 Structure (Current):**
```
backend/src/
├── contexts/
│   ├── placeholder/         # Dummy CRUD (Phase 0)
│   └── upstream/            # Data ingestion (Epic 1.1+)
│       ├── ports/
│       │   └── provider.py  # BaseProvider Protocol
│       └── adapters/
│           ├── provider_factory.py
│           ├── poe1_provider.py
│           └── poe2_provider.py
├── shared/
│   └── game_context.py      # Game enum
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

### Structure (Phase 1 Epic 1.1+)

```
backend/src/contexts/upstream/
├── ports/
│   └── provider.py          # BaseProvider Protocol (interface)
├── adapters/
│   ├── provider_factory.py  # Factory: get_provider(game) -> BaseProvider
│   ├── poe1_provider.py     # PoE1 implementation
│   └── poe2_provider.py     # PoE2 implementation
├── domain/                  # Epic 1.3: Canonical models
│   ├── item.py              # Canonical item model (game-agnostic)
│   ├── modifier.py          # Canonical modifier model
│   └── league.py            # League abstraction
└── services/                # Epic 1.4: Normalization and orchestration
    └── normalizer.py        # Raw data → canonical models
```

### Provider Pattern (Epic 1.1)

**Design:** Protocol-based interface with factory pattern for game-specific implementations.

**BaseProvider Protocol:**
```python
from typing import Any, Protocol
from src.shared import Game

class BaseProvider(Protocol):
    """Minimal interface for fetching game-specific data."""

    @property
    def game(self) -> Game:
        """Which game this provider serves."""
        ...

    async def get_active_leagues(self) -> list[dict[str, Any]]:
        """Fetch active leagues for this game."""
        ...

    async def fetch_economy_snapshot(
        self, league: str, category: str
    ) -> dict[str, Any]:
        """Fetch economy data for a league/category."""
        ...

    async def fetch_build_ladder(self, league: str) -> dict[str, Any]:
        """Fetch build ladder data for a league."""
        ...
```

**Factory Pattern:**
```python
from src.shared import Game
from ..ports import BaseProvider
from .poe1_provider import PoE1Provider
from .poe2_provider import PoE2Provider

def get_provider(game: Game) -> BaseProvider:
    """Return the appropriate provider for the given game."""
    match game:
        case Game.POE1:
            return PoE1Provider()
        case Game.POE2:
            return PoE2Provider()
        case _:
            raise ValueError(f"Unsupported game: {game}")
```

**Usage Example:**
```python
# Domain service (game-agnostic)
from src.contexts.upstream.adapters import get_provider
from src.shared import Game

async def get_active_leagues_for_game(game: Game):
    provider = get_provider(game)  # Returns PoE1Provider or PoE2Provider
    leagues = await provider.get_active_leagues()
    return leagues

# Example call
leagues = await get_active_leagues_for_game(Game.POE1)
# [{"name": "Standard", "active": True}, ...]
```

**Design Decisions:**
- **Protocol vs ABC**: Using `typing.Protocol` for duck typing and flexibility
- **dict[str, Any] returns**: Deferring structured models to Epic 1.3 (YAGNI principle)
- **Stateless providers**: Factory returns new instances each call (no caching yet)
- **Match statement**: Python 3.10+ pattern matching for clarity

**Adding New Games:**
1. Add new game to `src.shared.Game` enum
2. Create `{game}_provider.py` implementing `BaseProvider`
3. Add case to `get_provider()` factory function
4. Write tests in `tests/contexts/upstream/test_providers.py`

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


# Path of Mirrors - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Path of Mirrors                              │
│              Economic Intelligence Platform for PoE1/PoE2            │
└─────────────────────────────────────────────────────────────────────┘

┌───────────────────────┐         ┌───────────────────────┐
│      Frontend         │         │    External APIs       │
│   React + TanStack    │         │  (Data Sources)        │
│                       │         │                        │
│  ┌─────────────────┐ │         │  • poe.ninja           │
│  │  Routes (Pages) │ │         │  • Trade API           │
│  │  - Notes        │ │         │  • poedb               │
│  │  - Dashboard    │ │         │  • Path of Building    │
│  │  - Analytics    │ │         │                        │
│  └────────┬────────┘ │         └───────────┬────────────┘
│           │          │                     │
│  ┌────────▼────────┐ │                     │
│  │  TanStack Query │ │                     │
│  │  (State Mgmt)   │ │                     │
│  └────────┬────────┘ │                     │
│           │          │                     │
│  ┌────────▼────────┐ │                     │
│  │   API Client    │ │                     │
│  │  (Auto-gen'd)   │ │                     │
│  └────────┬────────┘ │                     │
└───────────┼──────────┘                     │
            │                                │
            │ HTTP/REST                      │ HTTP
            │                                │
            ▼                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     API Layer (HTTP)                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ Notes Routes │  │ Data Routes  │  │ Upstream API │      │   │
│  │  │  (CRUD)      │  │ (Analytics)  │  │  (Ingestion) │      │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │   │
│  └─────────┼──────────────────┼──────────────────┼──────────────┘   │
│            │                  │                  │                   │
│            │ FastAPI Depends  │                  │                   │
│            ▼                  ▼                  ▼                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Service Layer (Orchestration)              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ Note Service │  │ Data Service │  │ Ingestion Svc│      │   │
│  │  │              │  │              │  │              │      │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │   │
│  └─────────┼──────────────────┼──────────────────┼──────────────┘   │
│            │                  │                  │                   │
│            │ Protocol-based   │                  │                   │
│            ▼                  ▼                  ▼                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │          Ports (Repository Protocols & Provider Interfaces)  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │ NoteRepo     │  │ DataRepo     │  │ BaseProvider │      │   │
│  │  │ (Protocol)   │  │ (Protocol)   │  │ (Protocol)   │      │   │
│  │  └──────────────┘  └──────────────┘  └──────┬───────┘      │   │
│  └─────────┼──────────────────┼──────────────────┼──────────────┘   │
│            │                  │                  │                   │
│            │ Implemented by   │                  │ Implemented by    │
│            ▼                  ▼                  ▼                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            Adapters (Infrastructure Implementations)         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │   │
│  │  │   Postgres   │  │   Postgres   │  │ PoE1Provider │      │   │
│  │  │  Note Repo   │  │  Data Repo   │  │ PoE2Provider │      │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │   │
│  └─────────┼──────────────────┼──────────────────┼──────────────┘   │
│            │                  │                  │                   │
│  ┌─────────▼──────────────────▼──────────────────┼──────────────┐   │
│  │                    Domain Models                              │   │
│  │  ┌──────────────┐  ┌──────────────┐           │              │   │
│  │  │     Note     │  │  EconomyData │  ┌────────▼────────┐    │   │
│  │  │  (SQLAlchemy)│  │  (SQLAlchemy)│  │  External APIs  │    │   │
│  │  └──────────────┘  └──────────────┘  │  - poe.ninja    │    │   │
│  │                                       │  - Trade API    │    │   │
│  │  ┌─────────────────────────────────┐ └─────────────────┘    │   │
│  │  │  Core Domain (Shared Concepts)  │                         │   │
│  │  │  • BaseEntity                   │                         │   │
│  │  │  • Enums (League, Currency)     │                         │   │
│  │  │  • Value Objects (Money, %)     │                         │   │
│  │  └─────────────────────────────────┘                         │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Infrastructure Layer                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ Database │  │  Redis   │  │  Logging │  │  Config  │    │   │
│  │  │  (Base)  │  │  (Cache) │  │ (structlog)│ │ (Settings)│   │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Infrastructure      │
                    │                       │
                    │  ┌────────────────┐  │
                    │  │  PostgreSQL 17 │  │
                    │  │   (Database)   │  │
                    │  └────────────────┘  │
                    │                       │
                    │  ┌────────────────┐  │
                    │  │    Redis 7     │  │
                    │  │  (Cache/Queue) │  │
                    │  └────────────────┘  │
                    └───────────────────────┘
```

## Hexagonal Architecture (Ports & Adapters)

```
                    Hexagonal Architecture View
                    ============================

                        ┌─────────────────┐
                        │   External      │
                        │   World         │
                        │  (HTTP, APIs)   │
                        └────────┬────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │                        │
         ┌──────────┤    Primary Adapters    ├──────────┐
         │          │    (API Routes)        │          │
         │          └────────────────────────┘          │
         │                                               │
         ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│  Placeholder    │                           │   Upstream      │
│   Context       │                           │   Context       │
│                 │                           │                 │
│  ┌───────────┐ │        CORE DOMAIN        │  ┌───────────┐ │
│  │   API     │ │    (Application Core)     │  │   API     │ │
│  └─────┬─────┘ │                           │  └─────┬─────┘ │
│        │       │    ┌───────────────┐      │        │       │
│  ┌─────▼─────┐ │    │   Services    │      │  ┌─────▼─────┐ │
│  │ Service   │ │◄───┤ (Orchestration)│────►│  │ Service   │ │
│  └─────┬─────┘ │    └───────────────┘      │  └─────┬─────┘ │
│        │       │                           │        │       │
│  ┌─────▼─────┐ │    ┌───────────────┐      │  ┌─────▼─────┐ │
│  │   Ports   │ │    │    Domain     │      │  │   Ports   │ │
│  │(Protocols)│ │◄───┤    Models     │────►│  │(Protocols)│ │
│  └─────┬─────┘ │    └───────────────┘      │  └─────┬─────┘ │
│        │       │                           │        │       │
│  ┌─────▼─────┐ │                           │  ┌─────▼─────┐ │
│  │ Adapters  │ │                           │  │ Adapters  │ │
│  │(Postgres) │ │                           │  │(Providers)│ │
│  └─────┬─────┘ │                           │  └─────┬─────┘ │
└────────┼───────┘                           └────────┼───────┘
         │                                            │
         │          ┌────────────────────────┐        │
         └──────────┤  Secondary Adapters    ├────────┘
                    │  (Database, APIs)      │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Infrastructure │
                    │ (Postgres,     │
                    │  Redis, APIs)  │
                    └────────────────┘
```

## Bounded Contexts Structure

```
contexts/
│
├── core/                          # Shared domain kernel
│   ├── domain/
│   │   ├── models.py             # BaseEntity, mixins
│   │   ├── enums.py              # League, Currency, DataSource
│   │   └── value_objects.py      # Money, Percentage, TimeWindow
│   ├── ports/
│   │   └── repository.py         # Base repository protocols
│   └── adapters/
│       └── postgres_repository.py # Base Postgres implementations
│
├── placeholder/                   # Notes CRUD (Phase 0 demo)
│   ├── domain/
│   │   ├── models.py             # Note entity
│   │   └── schemas.py            # Pydantic DTOs
│   ├── ports/
│   │   └── repository.py         # NoteRepository protocol
│   ├── adapters/
│   │   └── postgres_repository.py # PostgresNoteRepository
│   ├── services/
│   │   └── note_service.py       # Business logic
│   └── api/
│       └── routes.py             # FastAPI endpoints
│
└── upstream/                      # Data ingestion (Phase 1)
    ├── domain/
    │   └── schemas.py            # API response models
    ├── ports/
    │   ├── repository.py         # Data repository protocol
    │   └── provider.py           # BaseProvider protocol
    ├── adapters/
    │   ├── postgres_repository.py # Postgres implementation
    │   ├── poe1_provider.py      # PoE1 API client
    │   ├── poe2_provider.py      # PoE2 API client
    │   └── provider_factory.py   # get_provider(game)
    ├── services/
    │   └── ingestion_service.py  # Data collection orchestration
    └── api/
        └── routes.py             # Ingestion endpoints
```

## Data Flow: User Request → Response

```
1. Frontend Request
   └─► HTTP GET /api/notes?game=poe1

2. API Layer (routes.py)
   └─► Receives request
   └─► Validates query params
   └─► Calls service via Depends()

3. Service Layer (note_service.py)
   └─► Receives call from API
   └─► Orchestrates business logic
   └─► Calls repository (via protocol)

4. Repository Protocol (NoteRepository)
   └─► Interface only - no implementation

5. Adapter (PostgresNoteRepository)
   └─► Implements repository protocol
   └─► Constructs SQLAlchemy query
   └─► Executes against database

6. Database
   └─► PostgreSQL executes query
   └─► Returns rows

7. ORM Mapping
   └─► SQLAlchemy maps rows to Note models
   └─► Returns List[Note]

8. Service Layer
   └─► Receives List[Note] from repository
   └─► Applies business logic (if any)
   └─► Returns to API layer

9. API Layer
   └─► Converts Note → NoteResponse (Pydantic)
   └─► Serializes to JSON
   └─► Returns HTTP 200 with JSON body

10. Frontend
    └─► TanStack Query receives response
    └─► Updates React state
    └─► Re-renders UI
```

## Dependency Direction (Clean Architecture)

```
                   Dependency Rule
                   ===============

    Outer Layers depend on Inner Layers
    Inner Layers NEVER depend on Outer Layers


    ┌───────────────────────────────────────┐
    │        API Layer (FastAPI)            │ ◄─── User requests
    │     (Framework & HTTP concerns)       │
    └───────────────┬───────────────────────┘
                    │ Depends on
                    ▼
    ┌───────────────────────────────────────┐
    │      Service Layer (Use Cases)        │
    │    (Business logic orchestration)     │
    └───────────────┬───────────────────────┘
                    │ Depends on
                    ▼
    ┌───────────────────────────────────────┐
    │    Ports (Repository Protocols)       │
    │       (Abstract interfaces)           │
    └───────────────┬───────────────────────┘
                    │ Implemented by
                    ▼
    ┌───────────────────────────────────────┐
    │  Adapters (Concrete Implementations)  │
    │   (Postgres, Redis, External APIs)    │
    └───────────────┬───────────────────────┘
                    │ Uses
                    ▼
    ┌───────────────────────────────────────┐
    │        Domain Models (Entities)       │ ◄─── Core
    │    (Pure business logic + SQLAlchemy) │
    └───────────────────────────────────────┘

    All layers can depend on → Domain Models
    Domain Models depend on → Infrastructure (Base)
       ⚠️ Pragmatic violation - see ADR 001
```

## Game Abstraction (Provider Pattern)

```
                Provider Pattern for PoE1/PoE2
                ===============================

    ┌─────────────────────────────────────────┐
    │      Service Layer                      │
    │  (Needs game-specific data)             │
    └────────────────┬────────────────────────┘
                     │
                     │ Requests provider
                     ▼
    ┌────────────────────────────────────────┐
    │    get_provider(Game.POE1) → Provider  │
    │         (Provider Factory)             │
    └────────┬──────────────────────┬────────┘
             │                      │
             ▼                      ▼
    ┌───────────────┐      ┌───────────────┐
    │ PoE1Provider  │      │ PoE2Provider  │
    │               │      │               │
    │ Implements:   │      │ Implements:   │
    │ BaseProvider  │      │ BaseProvider  │
    └───────┬───────┘      └───────┬───────┘
            │                      │
            ▼                      ▼
    ┌─────────────────────────────────────┐
    │      External APIs                  │
    │  • poe.ninja (PoE1 endpoints)       │
    │  • poe.ninja (PoE2 endpoints)       │
    │  • Trade API (different structure)  │
    └─────────────────────────────────────┘


    Usage Example:
    ──────────────
    provider = get_provider(Game.POE1)
    leagues = await provider.get_active_leagues()
    data = await provider.fetch_economy_snapshot("Settlers", "Currency")
```

## Docker Architecture (Production)

```
┌────────────────────────────────────────────────────────────────┐
│                      Docker Compose Network                     │
│                                                                 │
│  ┌──────────────────────┐      ┌──────────────────────┐       │
│  │   Frontend Container │      │  Backend Container   │       │
│  │   ┌──────────────┐   │      │   ┌──────────────┐   │       │
│  │   │  Nginx +     │   │      │   │  FastAPI +   │   │       │
│  │   │  React Build │   │      │   │  uvicorn     │   │       │
│  │   │  (Static)    │   │      │   │              │   │       │
│  │   └──────┬───────┘   │      │   └──────┬───────┘   │       │
│  │          │ :80       │      │          │ :8000     │       │
│  └──────────┼───────────┘      └──────────┼───────────┘       │
│             │                             │                    │
│             │ Reverse Proxy               │ API Calls          │
│             └────────────────┬────────────┘                    │
│                              │                                 │
│          ┌───────────────────┼───────────────────┐             │
│          │                   │                   │             │
│          ▼                   ▼                   ▼             │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐     │
│  │ PostgreSQL   │    │    Redis     │   │   Alembic    │     │
│  │ Container    │    │  Container   │   │  Migrations  │     │
│  │              │    │              │   │ (Init Job)   │     │
│  │ Port: 5432   │    │ Port: 6379   │   └──────────────┘     │
│  └──────────────┘    └──────────────┘                         │
│        ▲                    ▲                                  │
│        │                    │                                  │
│        └────────────────────┴──────────────────────────┐      │
│                        Persistent Volumes              │      │
│                      (postgres_data, redis_data)       │      │
└────────────────────────────────────────────────────────┼──────┘
                                                         │
                                                         ▼
                                                  Host Machine
```

## File Structure Overview

```
path-of-mirrors/
│
├── backend/
│   ├── src/                          # Application source
│   │   ├── contexts/                 # Bounded contexts
│   │   │   ├── core/                # Shared domain
│   │   │   ├── placeholder/         # Notes CRUD
│   │   │   └── upstream/            # Data ingestion
│   │   ├── infrastructure/          # Database, cache, logging
│   │   ├── shared/                  # Cross-cutting (Game enum)
│   │   └── main.py                  # FastAPI app entry
│   │
│   ├── alembic/                     # Database migrations
│   │   ├── versions/                # Migration files
│   │   └── env.py                   # Alembic config
│   ├── alembic.ini                  # Alembic settings
│   │
│   ├── scripts/                     # Admin scripts
│   │   ├── collect_*.py            # Data collection
│   │   ├── create_first_*.py       # Setup scripts
│   │   └── migrate.sh              # Migration helper
│   │
│   ├── tests/                       # Mirror of src/
│   │   ├── contexts/
│   │   └── conftest.py
│   │
│   ├── Dockerfile                   # Multi-stage build
│   ├── pyproject.toml               # uv dependencies
│   └── uv.lock                      # Locked dependencies
│
├── frontend/
│   ├── src/
│   │   ├── routes/                  # TanStack Router pages
│   │   ├── components/ui/           # shadcn/ui components
│   │   ├── hooks/                   # React hooks
│   │   └── lib/                     # API client, utils
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                            # Documentation
│   ├── adr/                         # Architecture decisions
│   │   └── 001-domain-infrastructure-coupling.md
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_DIAGRAM.md     # This file
│   └── QUICKSTART.md
│
├── docker-compose.yml               # Local development
└── CLAUDE.md                        # Project instructions
```

---

## Key Architectural Principles

1. **Hexagonal Architecture** - Core business logic isolated from infrastructure
2. **Dependency Inversion** - Depend on abstractions (protocols), not concretions
3. **Single Responsibility** - Each layer has one reason to change
4. **Bounded Contexts** - Contexts don't import from each other (except shared)
5. **Provider Pattern** - Game-specific logic abstracted via protocols
6. **Protocol-Based Repositories** - Duck typing for flexibility
7. **Pragmatic Trade-offs** - SQLAlchemy as domain (see ADR 001)

## Navigation

- Full details: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Decision records: [docs/adr/](adr/)
- Quick start: [docs/QUICKSTART.md](QUICKSTART.md)
