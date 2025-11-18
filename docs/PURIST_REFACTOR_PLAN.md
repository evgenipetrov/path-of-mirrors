# PURIST ARCHITECTURAL REFACTOR PLAN

**Date**: 2025-11-18
**Scope**: Complete codebase restructure to hexagonal architecture purity
**Zero Tolerance Policy**: Every file in its proper place, no exceptions

---

## Executive Summary

**Current State**: 98 Python files, 55 in legacy `app/` structure (56% of codebase violates architecture)

**Target State**: Pure hexagonal architecture with bounded contexts only

**Strategy**: **NUCLEAR OPTION** - Delete entire `app/` directory, keep only what's architecturally pure

**Rationale**:
- `app/` is boilerplate demo code (users, posts, tiers, rate limits)
- We have **zero production users** - nothing to migrate
- Clean slate is faster than refactoring legacy code
- Enforces architectural purity from Day 1

---

## Current State Analysis

### What We Actually Use (✅ KEEP)
```
backend/src/
├── main.py                        # ✅ Clean, uses infrastructure correctly
├── contexts/
│   ├── placeholder/               # ✅ Perfect hexagonal structure
│   └── upstream/                  # ✅ Correct (needs completion)
├── infrastructure/                # ✅ Clean separation
├── shared/                        # ✅ Minimal, correct
└── migrations/                    # ✅ Alembic setup correct
```

### What We Don't Use (🗑️ DELETE)
```
backend/src/
└── app/                           # 🗑️ ENTIRE DIRECTORY - Boilerplate demo
    ├── models/                    # User, Post, Tier, RateLimit - NOT OUR DOMAIN
    ├── schemas/                   # API contracts for demo features
    ├── crud/                      # Anemic CRUD for demo models
    ├── api/v1/                    # Demo endpoints (login, users, posts, etc.)
    ├── core/                      # Duplicates infrastructure
    ├── admin/                     # Admin panel for demo models
    ├── middleware/                # Client cache (move to infrastructure)
    ├── main.py                    # Legacy app (we have src/main.py)
    └── logs/                      # Should be at root, gitignored
```

**Evidence**: `backend/src/main.py` does NOT import from `app/` - it's already clean!
```python
from src.contexts.placeholder.api.routes import router as notes_router
from src.infrastructure import (...)  # ✅ Correct imports
```

---

## The Nuclear Option: Delete `app/` Entirely

### Why This Is Safe

1. **No Production Code**: `app/` is FastAPI boilerplate demo (users, posts, tiers)
2. **Not Used**: `src/main.py` doesn't import from `app/`
3. **Zero Users**: No production data to migrate
4. **Duplicate Infrastructure**: Everything in `app/core/` duplicates `infrastructure/`
5. **Wrong Pattern**: Anemic domain model, not hexagonal architecture

### What We Lose (Nothing Important)

- ❌ User authentication demo (we'll rebuild properly in `contexts/auth/` when needed)
- ❌ Posts CRUD demo (placeholder/notes already shows pattern)
- ❌ Rate limiting demo (we have Redis, can rebuild when needed)
- ❌ Admin panel demo (not our product)
- ❌ JWT token blacklist (we'll rebuild auth properly)

### What We Gain

- ✅ **Architectural Purity**: 100% hexagonal, zero violations
- ✅ **Clarity**: Every file follows bounded context pattern
- ✅ **Clean Slate**: No legacy code to refactor
- ✅ **Fast Development**: No confusion about which pattern to follow
- ✅ **Perfect Onboarding**: New developers see only correct patterns

---

## Target Architecture (Post-Cleanup)

```
backend/
├── src/
│   ├── main.py                    # ✅ Application entry point (already clean)
│   │
│   ├── contexts/                  # Bounded contexts (hexagonal)
│   │   ├── core/                  # 🆕 CREATE - Shared kernel
│   │   │   ├── domain/
│   │   │   │   ├── models.py          # Item, CharacterSnapshot, TradeListing, League
│   │   │   │   ├── value_objects.py   # Price, SocketConfig, Modifier, Requirements
│   │   │   │   └── enums.py           # Rarity, CurrencyType, ModifierType
│   │   │   ├── ports/
│   │   │   │   └── repository.py      # Core model repository interfaces
│   │   │   └── adapters/
│   │   │       └── postgres_repository.py  # Core model repositories
│   │   │
│   │   ├── upstream/              # ✅ KEEP + COMPLETE
│   │   │   ├── domain/
│   │   │   │   └── schemas.py         # 🆕 StatSchema (Trade API schemas in DB)
│   │   │   ├── ports/
│   │   │   │   ├── provider.py        # ✅ BaseProvider Protocol
│   │   │   │   └── repository.py      # 🆕 StatSchema repository interface
│   │   │   ├── adapters/
│   │   │   │   ├── provider_factory.py    # ✅ Factory
│   │   │   │   ├── poe1_provider.py       # ✅ PoE1 implementation
│   │   │   │   ├── poe2_provider.py       # ✅ PoE2 implementation
│   │   │   │   └── postgres_repository.py # 🆕 StatSchema repository
│   │   │   ├── services/
│   │   │   │   └── ingestion_service.py   # 🆕 Orchestration (Epic 1.4)
│   │   │   └── api/
│   │   │       └── routes.py              # 🆕 Admin endpoints (Epic 1.4)
│   │   │
│   │   └── placeholder/           # ✅ KEEP - Demo of correct pattern
│   │       ├── domain/
│   │       │   ├── models.py          # Note entity
│   │       │   └── schemas.py         # API schemas
│   │       ├── ports/
│   │       │   └── repository.py      # NoteRepository Protocol
│   │       ├── adapters/
│   │       │   └── postgres_repository.py
│   │       ├── services/
│   │       │   └── note_service.py
│   │       └── api/
│   │           └── routes.py
│   │
│   ├── infrastructure/            # ✅ KEEP - Cross-cutting concerns
│   │   ├── __init__.py
│   │   ├── database.py                # ✅ SQLAlchemy setup
│   │   ├── cache.py                   # ✅ Redis setup
│   │   ├── logging.py                 # ✅ structlog setup
│   │   ├── health.py                  # ✅ Health checks
│   │   ├── middleware.py              # ✅ Request logging
│   │   ├── settings.py                # ✅ Pydantic settings
│   │   └── config/                    # ✅ Domain-specific configs
│   │       ├── global_config.py
│   │       ├── poeninja.py
│   │       ├── trade.py
│   │       ├── pob.py
│   │       └── poedb.py
│   │
│   ├── shared/                    # ✅ KEEP - Shared utilities
│   │   ├── __init__.py
│   │   └── game_context.py            # Game enum (POE1, POE2)
│   │
│   └── migrations/                # ✅ KEEP - Alembic
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           └── 2a1185ac4b28_create_notes_table.py
│
├── scripts/                       # ✅ KEEP + ADD - CLI utilities (outside src/)
│   ├── collect_poeninja_samples.py
│   ├── collect_trade_samples.py
│   └── collect_trade_schemas.py
│
├── tests/                         # ✅ KEEP - Mirrors src/ structure
│   ├── contexts/
│   │   ├── core/
│   │   ├── upstream/
│   │   └── placeholder/
│   └── infrastructure/
│
├── alembic.ini                    # ✅ Configuration
├── pyproject.toml                 # ✅ uv dependencies
└── README.md
```

---

## Cleanup Execution Plan

### Phase 1: Nuclear Deletion (5 minutes)

```bash
# 1. Delete entire app/ directory
rm -rf backend/src/app/

# 2. Move app/middleware to infrastructure (only useful file)
# (Already done - RequestLoggingMiddleware in infrastructure/middleware.py)

# 3. Verify main.py still works
cd backend && uv run python -c "from src.main import app; print('✅ App loads')"
```

**Affected migrations**: None - `placeholder/` migrations don't reference `app/` models

**Affected tests**: Check for any tests importing from `app/`
```bash
grep -r "from app\." backend/tests/ --include="*.py" || echo "✅ No app imports in tests"
grep -r "import app\." backend/tests/ --include="*.py" || echo "✅ No app imports in tests"
```

### Phase 2: Create Core Context (10 minutes)

```bash
# Create directory structure
mkdir -p backend/src/contexts/core/{domain,ports,adapters}

# Create __init__.py files
touch backend/src/contexts/core/__init__.py
touch backend/src/contexts/core/domain/__init__.py
touch backend/src/contexts/core/ports/__init__.py
touch backend/src/contexts/core/adapters/__init__.py

# Create domain files (empty skeletons)
touch backend/src/contexts/core/domain/models.py
touch backend/src/contexts/core/domain/value_objects.py
touch backend/src/contexts/core/domain/enums.py

# Create port files
touch backend/src/contexts/core/ports/repository.py

# Create adapter files
touch backend/src/contexts/core/adapters/postgres_repository.py
```

### Phase 3: Complete Upstream Context (5 minutes)

```bash
# Create missing directories
mkdir -p backend/src/contexts/upstream/{domain,services,api}

# Create __init__.py files
touch backend/src/contexts/upstream/domain/__init__.py
touch backend/src/contexts/upstream/services/__init__.py
touch backend/src/contexts/upstream/api/__init__.py

# Create domain files
touch backend/src/contexts/upstream/domain/schemas.py

# Create port files
touch backend/src/contexts/upstream/ports/repository.py

# Create adapter files
touch backend/src/contexts/upstream/adapters/postgres_repository.py

# Create service files
touch backend/src/contexts/upstream/services/ingestion_service.py

# Create API files
touch backend/src/contexts/upstream/api/routes.py
```

### Phase 4: Update .gitignore (2 minutes)

```bash
cat >> backend/.gitignore << 'EOF'

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Logs
*.log
logs/
app.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Environment
.env
.env.local

# Database
*.db
*.sqlite
EOF
```

### Phase 5: Verify Clean Architecture (3 minutes)

```bash
# Run all tests
cd backend && uv run pytest

# Check for any remaining app/ imports
grep -r "from app\." backend/src --include="*.py" || echo "✅ No app imports"
grep -r "import app\." backend/src --include="*.py" || echo "✅ No app imports"

# Verify database migrations work
cd backend && uv run alembic upgrade head

# Verify application starts
cd backend && uv run python -c "from src.main import app; print('✅ Application ready')"
```

---

## Post-Cleanup State

### File Count
- **Before**: 98 files (55 in `app/`)
- **After**: ~45 files (100% architecturally pure)

### Import Graph Purity
```
✅ contexts/core/        → (no dependencies except shared/)
✅ contexts/upstream/    → contexts/core/, shared/, infrastructure/
✅ contexts/placeholder/ → infrastructure/
✅ infrastructure/       → shared/ only
✅ shared/               → (no dependencies)
✅ main.py              → contexts/*, infrastructure/
```

**Zero circular dependencies, zero violations**

### Architecture Compliance
- ✅ 100% hexagonal architecture
- ✅ All contexts follow same structure
- ✅ Clear dependency direction
- ✅ Infrastructure isolated
- ✅ Domain logic pure

---

## Migration Notes for Future Auth Context

When we need authentication (Phase 2+), we'll build it **properly**:

```
contexts/auth/
├── domain/
│   ├── models.py           # User, Session (SQLAlchemy)
│   └── schemas.py          # LoginRequest, TokenResponse (Pydantic)
├── ports/
│   ├── repository.py       # UserRepository Protocol
│   └── token_service.py    # TokenService Protocol (for testing)
├── adapters/
│   ├── postgres_repository.py   # UserRepository implementation
│   └── jwt_token_service.py     # TokenService implementation (JWT)
├── services/
│   └── auth_service.py     # Login, register, verify logic
└── api/
    └── routes.py           # POST /login, POST /register, etc.
```

**No CRUD files, no anemic models, pure hexagonal from Day 1.**

---

## Risk Analysis

### Risks

1. **Deleted Useful Code**: Admin panel, auth demo
   - **Mitigation**: All demo code, we'll rebuild properly when needed
   - **Severity**: Low (no production usage)

2. **Breaking Changes**: Tests may fail
   - **Mitigation**: Run test suite before/after
   - **Severity**: Low (easy to fix, good cleanup opportunity)

3. **Lost Learning Value**: Boilerplate examples gone
   - **Mitigation**: We have `placeholder/` as reference, v0.4 code for patterns
   - **Severity**: Very Low (boilerplate was wrong pattern anyway)

### Benefits

1. **Architectural Purity**: 100% hexagonal, zero confusion
2. **Clean Slate**: Build all features with correct pattern from start
3. **Fast Development**: No legacy code to work around
4. **Perfect Documentation**: Code shows only correct patterns
5. **Easy Onboarding**: New developers see pure architecture

---

## Decision Points

### Option A: Nuclear Deletion (RECOMMENDED)
**Action**: Delete `app/` entirely, create pure structure
**Timeline**: 30 minutes
**Risk**: Low (no production code)
**Benefit**: Perfect architectural purity

### Option B: Gradual Migration
**Action**: Keep `app/`, mark as legacy, migrate piece by piece
**Timeline**: Weeks of work
**Risk**: Medium (confusion, dual patterns)
**Benefit**: Preserve boilerplate examples

### Option C: Do Nothing
**Action**: Keep both structures
**Timeline**: N/A
**Risk**: High (architectural violations persist)
**Benefit**: None

---

## Recommendation

**EXECUTE OPTION A: Nuclear Deletion**

**Rationale**:
1. We have **zero production users**
2. `app/` is demo code (users, posts, tiers) - **not our domain**
3. `src/main.py` already doesn't use `app/` - **it's already clean**
4. Perfect time for cleanup: **before Epic 1.3** (domain modeling)
5. Clean architecture >>> preserving boilerplate examples

**Timeline**: 30 minutes to execute, 0 minutes to debug (no production impact)

**Next Steps**:
1. User approves plan
2. Execute Phases 1-5 (automated script)
3. Run tests, verify clean
4. Commit: "refactor: remove legacy app/ directory, establish pure hexagonal architecture"
5. Begin Epic 1.3 with perfect foundation

---

## Automation Script

```bash
#!/bin/bash
# cleanup_architecture.sh - Execute purist refactor

set -e  # Exit on error

echo "🔥 PURIST ARCHITECTURE CLEANUP"
echo "=============================="
echo ""

# Phase 1: Nuclear Deletion
echo "Phase 1: Deleting legacy app/ directory..."
rm -rf backend/src/app/
echo "✅ Deleted backend/src/app/"

# Phase 2: Create Core Context
echo ""
echo "Phase 2: Creating contexts/core/ structure..."
mkdir -p backend/src/contexts/core/{domain,ports,adapters}
touch backend/src/contexts/core/__init__.py
touch backend/src/contexts/core/domain/{__init__.py,models.py,value_objects.py,enums.py}
touch backend/src/contexts/core/ports/{__init__.py,repository.py}
touch backend/src/contexts/core/adapters/{__init__.py,postgres_repository.py}
echo "✅ Created contexts/core/"

# Phase 3: Complete Upstream Context
echo ""
echo "Phase 3: Completing contexts/upstream/ structure..."
mkdir -p backend/src/contexts/upstream/{domain,services,api}
touch backend/src/contexts/upstream/domain/{__init__.py,schemas.py}
touch backend/src/contexts/upstream/ports/repository.py
touch backend/src/contexts/upstream/adapters/postgres_repository.py
touch backend/src/contexts/upstream/services/{__init__.py,ingestion_service.py}
touch backend/src/contexts/upstream/api/{__init__.py,routes.py}
echo "✅ Completed contexts/upstream/"

# Phase 4: Update .gitignore
echo ""
echo "Phase 4: Updating .gitignore..."
cat >> backend/.gitignore << 'EOF'

# Python
__pycache__/
*.py[cod]
*$py.class

# Logs
*.log
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/
EOF
echo "✅ Updated .gitignore"

# Phase 5: Verify
echo ""
echo "Phase 5: Verifying clean architecture..."

# Check for app imports
if grep -r "from app\." backend/src --include="*.py" 2>/dev/null; then
    echo "❌ ERROR: Found imports from app/"
    exit 1
fi

# Verify main.py loads
cd backend && uv run python -c "from src.main import app; print('✅ Application loads successfully')" || {
    echo "❌ ERROR: Application failed to load"
    exit 1
}

cd ..

echo ""
echo "✅ CLEANUP COMPLETE"
echo "===================="
echo ""
echo "Summary:"
echo "  - Deleted: backend/src/app/ (55 files)"
echo "  - Created: contexts/core/ (hexagonal structure)"
echo "  - Completed: contexts/upstream/ (hexagonal structure)"
echo "  - Verified: Application loads successfully"
echo ""
echo "Next step: Begin Epic 1.3 (Core Domain Model Design)"
```

**Save as**: `backend/scripts/cleanup_architecture.sh`

---

## Final Verification Checklist

After cleanup, verify:

- [ ] `backend/src/app/` directory deleted
- [ ] `contexts/core/` structure created
- [ ] `contexts/upstream/` structure completed
- [ ] `.gitignore` updated
- [ ] No imports from `app/` anywhere
- [ ] Application starts: `uv run python -m src.main`
- [ ] Tests pass: `uv run pytest`
- [ ] Migrations work: `uv run alembic upgrade head`
- [ ] Architecture review passes (no violations)

---

**END OF PLAN**
