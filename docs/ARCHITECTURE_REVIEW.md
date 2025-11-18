# Architecture Review: File & Folder Placement Analysis

**Date**: 2025-11-18
**Reviewer**: Claude Code
**Scope**: Complete codebase review for architectural violations
**Status**: 🔴 **CRITICAL ISSUES FOUND**

---

## Executive Summary

**Violations Found**: 6 major categories, 50+ files misplaced

**Critical Issues**:
1. **DUPLICATE DATABASE INFRASTRUCTURE**: Two separate database modules (`app/core/db/` vs `infrastructure/database.py`)
2. **LEGACY APP STRUCTURE**: Entire `app/` directory violates hexagonal architecture
3. **MISSING CORE CONTEXT**: Canonical domain models have no home (should be `contexts/core/`)
4. **MIXED CONCERNS**: Models, CRUD, schemas all in separate directories instead of bounded contexts

**Impact**: High - violates architectural purity, creates technical debt, confuses dependencies

**Recommended Action**: Immediate refactoring before Epic 1.3 implementation

---

## 1. Critical Violation: Duplicate Database Infrastructure

### Issue
Two separate database modules exist with identical functionality:

**Location 1**: `backend/src/app/core/db/database.py`
```python
class Base(DeclarativeBase, MappedAsDataclass):
    pass

async_engine = create_async_engine(DATABASE_URL, ...)
local_session = async_sessionmaker(...)
async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    ...
```

**Location 2**: `backend/src/infrastructure/database.py`
```python
class Base(DeclarativeBase, MappedAsDataclass):
    pass

async_engine = create_async_engine(DATABASE_URL, ...)
local_session = async_sessionmaker(...)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    ...
```

### Architectural Violation
- **DUPLICATE INFRASTRUCTURE**: Two SQLAlchemy Base classes, two engines, two session makers
- **INCONSISTENT NAMING**: `async_get_db()` vs `get_db()`
- **UNCLEAR CANONICAL SOURCE**: Which one should domain models use?

### Impact
- Models may import from wrong Base class
- Migrations may not detect all models
- Session leaks if different session makers used

### Resolution
**DELETE**: `backend/src/app/core/db/` entirely
**KEEP**: `backend/src/infrastructure/database.py` (matches target architecture)
**UPDATE**: All imports from `app.core.db.database` → `infrastructure.database`

**Affected Files**:
```
backend/src/app/models/user.py:9          from ..core.db.database import Base
backend/src/app/models/post.py            from ..core.db.database import Base
backend/src/app/models/rate_limit.py      from ..core.db.database import Base
backend/src/app/models/tier.py            from ..core.db.database import Base
```

---

## 2. Critical Violation: Legacy `app/` Structure

### Issue
The entire `backend/src/app/` directory follows **anemic domain model** pattern, violating hexagonal architecture:

```
backend/src/app/
├── models/          # SQLAlchemy models (persistence)
├── schemas/         # Pydantic schemas (API contracts)
├── crud/            # CRUD operations (data access)
├── api/v1/          # API routes (HTTP layer)
├── core/            # Config, security, utils
└── admin/           # Admin panel
```

### Architectural Violation
This is the **old FastAPI boilerplate structure** (MVC-like), NOT hexagonal architecture.

**Problems**:
1. **No bounded contexts** - all models in one `models/` folder
2. **Anemic domain models** - models are just data containers, business logic in CRUD/routes
3. **Direct repository pattern** - CRUD functions access database directly, no interfaces
4. **No ports/adapters** - tight coupling between API and database
5. **Schemas separate from domain** - API contracts disconnected from domain models

### Comparison with Target Architecture

**Current (WRONG)**:
```
app/
├── models/user.py           # Persistence layer
├── schemas/user.py          # API layer
├── crud/crud_users.py       # Data access layer
└── api/v1/users.py          # HTTP layer
```

**Target (CORRECT)**:
```
contexts/users/              # Bounded context
├── domain/
│   ├── models.py           # Domain entities (SQLAlchemy)
│   └── schemas.py          # API contracts (Pydantic)
├── ports/
│   └── repository.py       # Repository interface (Protocol)
├── adapters/
│   └── postgres_repository.py  # Repository implementation
├── services/
│   └── user_service.py     # Business logic
└── api/
    └── routes.py           # HTTP layer
```

### Impact
- **Violates hexagonal architecture** - infrastructure (FastAPI, SQLAlchemy) tightly coupled to domain
- **Not testable** - cannot test business logic without database
- **Not swappable** - cannot replace adapters (e.g., different database)
- **Confuses new developers** - two architectural patterns coexist

### Resolution
**Phase 1: Quarantine** (Immediate)
- ✅ Already done: `placeholder/` context created (correct structure)
- ⚠️ Keep `app/` for now (it's the boilerplate demo)
- 🎯 **DO NOT** add new features to `app/` structure

**Phase 2: Migration** (Post-Epic 1.3)
- Move user/auth to `contexts/auth/` (when auth is needed)
- Delete `app/models/`, `app/schemas/`, `app/crud/`
- Keep `app/api/v1/` only as router aggregator (mounts context routes)

**Phase 3: Cleanup** (Phase 1 complete)
- Delete entire `app/` directory
- Move `app/main.py` → `src/main.py`
- Update all imports

---

## 3. Critical Violation: Missing `contexts/core/`

### Issue
**Canonical domain models have no home.**

According to Epic 1.3 analysis and v0.4 reference:
- We need **canonical/core models** (Item, CharacterSnapshot, TradeListing, League, etc.)
- These are **shared across multiple contexts** (upstream, market, crafting, etc.)
- Should live in `contexts/core/` (renamed from `canonical/` per user request)

**Currently**: This directory does not exist.

### Architectural Violation
- **INCOMPLETE ARCHITECTURE**: Target structure (ARCHITECTURE.md line 170) specifies `domain/` for canonical models
- **NO SHARED KERNEL**: Cannot start Epic 1.3 domain modeling without proper location

### Impact
- Epic 1.3 blocked until structure created
- Risk of placing models in wrong location (e.g., `upstream/domain/` as I initially suggested)

### Resolution
**CREATE**: `backend/src/contexts/core/` with proper structure:

```
backend/src/contexts/core/
├── domain/
│   ├── __init__.py
│   ├── models.py           # Item, CharacterSnapshot, TradeListing, League
│   ├── value_objects.py    # Price, SocketConfig, Requirements, Modifier
│   └── enums.py            # Rarity, CurrencyType, ModifierType
├── ports/
│   ├── __init__.py
│   └── repository.py       # Future: Repository interfaces for core models
├── adapters/
│   └── __init__.py         # Future: Postgres repositories for core models
└── __init__.py
```

**Priority**: 🔴 **IMMEDIATE** (blocks Epic 1.3)

---

## 4. Major Violation: Inconsistent Context Structure

### Issue
`contexts/placeholder/` follows correct hexagonal architecture, but `contexts/upstream/` is incomplete.

**Placeholder Context** (✅ CORRECT):
```
contexts/placeholder/
├── domain/
│   ├── models.py           # Note entity
│   └── schemas.py          # API schemas
├── ports/
│   └── repository.py       # NoteRepository Protocol
├── adapters/
│   └── postgres_repository.py  # PostgresNoteRepository implementation
├── services/
│   └── note_service.py     # Business logic
└── api/
    └── routes.py           # HTTP endpoints
```

**Upstream Context** (⚠️ INCOMPLETE):
```
contexts/upstream/
├── ports/
│   └── provider.py         # BaseProvider Protocol
└── adapters/
    ├── provider_factory.py
    ├── poe1_provider.py
    └── poe2_provider.py
```

**Missing in upstream**:
- ❌ `domain/` - Should contain StatSchema model (Trade API schemas stored in DB)
- ❌ `services/` - Should contain orchestration logic (Epic 1.4+)
- ❌ `api/` - Should contain upstream admin routes (Epic 1.4+)

### Architectural Violation
- **INCOMPLETE BOUNDED CONTEXT**: Missing layers (domain, services, API)
- **INCONSISTENT STRUCTURE**: Placeholder has all layers, upstream missing most

### Impact
- Unclear where to place new upstream-specific models (e.g., StatSchema)
- No place for upstream business logic
- Cannot expose upstream admin endpoints

### Resolution
**CREATE**: Missing directories in `contexts/upstream/`:

```
contexts/upstream/
├── domain/
│   ├── __init__.py
│   └── schemas.py          # StatSchema, ItemSchema, etc. (Trade API schemas in DB)
├── services/
│   ├── __init__.py
│   └── ingestion_service.py  # Future: Orchestrates data ingestion
├── api/
│   ├── __init__.py
│   └── routes.py           # Future: Admin endpoints (trigger ingestion, view status)
├── ports/
│   └── provider.py         # ✅ Already exists
└── adapters/
    ├── provider_factory.py  # ✅ Already exists
    ├── poe1_provider.py    # ✅ Already exists
    └── poe2_provider.py    # ✅ Already exists
```

**Priority**: 🟡 **MEDIUM** (needed for Epic 1.4, not blocking Epic 1.3)

---

## 5. Minor Violation: Duplicate Health Checks

### Issue
Two health check implementations:

**Location 1**: `backend/src/app/core/health.py`
**Location 2**: `backend/src/infrastructure/health.py`

### Architectural Violation
- **DUPLICATE FUNCTIONALITY**: Two modules doing the same thing
- **UNCLEAR CANONICAL SOURCE**: Which one is used?

### Resolution
**KEEP**: `infrastructure/health.py` (correct location for cross-cutting concern)
**DELETE**: `app/core/health.py`
**UPDATE**: Routes to import from `infrastructure.health`

---

## 6. Minor Violation: Duplicate Logging

### Issue
Two logging implementations:

**Location 1**: `backend/src/app/core/logger.py`
**Location 2**: `backend/src/infrastructure/logging.py`

### Architectural Violation
- **DUPLICATE FUNCTIONALITY**: Two logging configurations
- **INCONSISTENT NAMING**: `logger.py` vs `logging.py`

### Resolution
**KEEP**: `infrastructure/logging.py` (correct location)
**DELETE**: `app/core/logger.py`
**UPDATE**: All imports to use `infrastructure.logging`

---

## 7. Minor Violation: Scripts in Wrong Location

### Issue
Scripts in `backend/src/scripts/` should be in `backend/scripts/` (outside src/)

**Current**:
```
backend/src/scripts/
├── create_first_superuser.py
├── create_first_tier.py
└── __init__.py
```

**Target**:
```
backend/scripts/              # ✅ Already exists
├── collect_poeninja_samples.py
├── collect_trade_samples.py
├── collect_trade_schemas.py
└── (add admin scripts here)
```

### Architectural Violation
- **WRONG LOCATION**: Scripts are not importable code, shouldn't be in `src/`
- **INCONSISTENT**: Data collection scripts in `backend/scripts/`, admin scripts in `backend/src/scripts/`

### Resolution
**MOVE**: `backend/src/scripts/*` → `backend/scripts/`
**DELETE**: `backend/src/scripts/` directory

---

## 8. Minor Issue: Unused Directories

### Issue
Several empty or placeholder directories:

**Empty**:
- `backend/src/app/logs/` - Contains only `app.log` (should be in `logs/` at root, gitignored)
- `backend/src/contexts/upstream/adapters/__pycache__/` - Should be gitignored

**Legacy**:
- `backend/src/app/middleware/` - Single file, could move to `infrastructure/middleware.py`

### Resolution
**UPDATE**: `.gitignore` to exclude:
```
__pycache__/
*.pyc
*.log
logs/
```

**MOVE**: `app/middleware/client_cache_middleware.py` → `infrastructure/middleware.py` (consolidate)

---

## Summary of Required Actions

### 🔴 IMMEDIATE (Blocks Epic 1.3)

1. **CREATE** `contexts/core/` structure:
   ```bash
   mkdir -p backend/src/contexts/core/{domain,ports,adapters}
   touch backend/src/contexts/core/__init__.py
   touch backend/src/contexts/core/domain/{__init__.py,models.py,value_objects.py,enums.py}
   touch backend/src/contexts/core/ports/__init__.py
   touch backend/src/contexts/core/adapters/__init__.py
   ```

2. **RESOLVE** database duplication:
   - Update all `app/models/*.py` imports: `from ..core.db.database import Base` → `from infrastructure.database import Base`
   - Delete `backend/src/app/core/db/` directory
   - Verify all models import from `infrastructure.database`

### 🟡 HIGH PRIORITY (Before Epic 1.4)

3. **COMPLETE** `contexts/upstream/` structure:
   ```bash
   mkdir -p backend/src/contexts/upstream/{domain,services,api}
   touch backend/src/contexts/upstream/domain/{__init__.py,schemas.py}
   touch backend/src/contexts/upstream/services/__init__.py
   touch backend/src/contexts/upstream/api/__init__.py
   ```

4. **CONSOLIDATE** infrastructure utilities:
   - Delete `app/core/health.py` → use `infrastructure/health.py`
   - Delete `app/core/logger.py` → use `infrastructure/logging.py`
   - Update all imports

### 🟢 MEDIUM PRIORITY (Phase 1 cleanup)

5. **QUARANTINE** legacy `app/` structure:
   - Add comment to `app/README.md`: "LEGACY - DO NOT ADD NEW FEATURES HERE"
   - Document migration plan to bounded contexts

6. **MOVE** scripts:
   ```bash
   mv backend/src/scripts/* backend/scripts/
   rmdir backend/src/scripts/
   ```

7. **CLEANUP** gitignore, remove empty directories

### ⚪ LOW PRIORITY (Post-Phase 1)

8. **MIGRATE** user/auth to `contexts/auth/`
9. **DELETE** entire `app/` directory
10. **MOVE** `app/main.py` → `src/main.py`

---

## Architectural Compliance Checklist

### ✅ COMPLIANT
- [x] `contexts/placeholder/` - Perfect hexagonal structure
- [x] `infrastructure/` - Clean separation of concerns
- [x] `shared/` - Minimal, game context enum only
- [x] Migration structure - Using Alembic correctly

### ⚠️ PARTIALLY COMPLIANT
- [ ] `contexts/upstream/` - Missing domain/services/api layers
- [ ] Import consistency - Mixed imports from app/core vs infrastructure

### ❌ NON-COMPLIANT
- [ ] `app/` directory - Legacy MVC structure, violates hexagonal architecture
- [ ] `contexts/core/` - Doesn't exist (should contain canonical models)
- [ ] Database infrastructure - Duplicated in two locations
- [ ] Scripts location - Mixed between `src/scripts/` and `scripts/`

---

## Migration Strategy

### Phase 1: Prepare for Epic 1.3 (NOW)
1. Create `contexts/core/` structure
2. Fix database import duplication
3. Complete `contexts/upstream/` structure

### Phase 2: During Epic 1.3-1.4
4. Implement core domain models in `contexts/core/domain/`
5. Use `contexts/core/` models from upstream adapters
6. Quarantine `app/` (no new features)

### Phase 3: Post-Epic 1.4
7. Migrate user/auth to `contexts/auth/`
8. Delete legacy `app/` directory
9. Full architectural compliance

---

## References

- **v0.4 Structure**: `_samples/code/path-of-mirrors_v0.4/backend/app/domains/canonical/`
- **Target Architecture**: `docs/ARCHITECTURE.md` lines 104-176
- **Hexagonal Pattern**: `docs/ARCHITECTURE.md` lines 59-92
- **Epic 1.3 Requirements**: `docs/SPRINT.md`, `_samples/ANALYSIS_REVIEW.md`

---

## Appendix: File-by-File Impact Analysis

### Files Importing Wrong Database Base
```
backend/src/app/models/user.py:9
backend/src/app/models/post.py:9
backend/src/app/models/rate_limit.py:9
backend/src/app/models/tier.py:9
```

**Fix**: Change to `from infrastructure.database import Base`

### Files to Delete (Duplicates)
```
backend/src/app/core/db/database.py
backend/src/app/core/db/models.py
backend/src/app/core/db/crud_token_blacklist.py
backend/src/app/core/db/token_blacklist.py
backend/src/app/core/db/__init__.py
backend/src/app/core/health.py
backend/src/app/core/logger.py
```

### Files to Move
```
backend/src/scripts/create_first_superuser.py → backend/scripts/
backend/src/scripts/create_first_tier.py → backend/scripts/
backend/src/app/middleware/client_cache_middleware.py → backend/src/infrastructure/middleware.py (merge)
```

### Directories to Create
```
backend/src/contexts/core/
backend/src/contexts/core/domain/
backend/src/contexts/core/ports/
backend/src/contexts/core/adapters/
backend/src/contexts/upstream/domain/
backend/src/contexts/upstream/services/
backend/src/contexts/upstream/api/
```

---

**End of Report**
