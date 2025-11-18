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
