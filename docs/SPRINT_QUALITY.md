# Sprint: Quality Infrastructure & Testing Excellence

**Sprint Goal:** Establish world-class testing infrastructure with comprehensive coverage, strong typing, and automated quality checks.

**Sprint Duration:** 2-3 weeks
**Sprint Status:** 🚧 In Progress (15%)
**Start Date:** 2025-11-18

---

## Definition of Done

Quality Sprint is complete when:

- ✅ Frontend has Vitest + React Testing Library with 70%+ coverage
- ✅ Playwright E2E tests cover critical user flows
- ✅ Backend has pytest with 70%+ coverage
- ✅ mypy strict mode enabled with zero type errors
- ✅ Dead code detection tools configured and integrated
- ✅ Code complexity analysis integrated
- ✅ Pre-commit hooks prevent bad code from being committed
- ✅ CI/CD pipeline enforces quality standards
- ✅ Coverage reports visible and tracked
- ✅ Documentation for testing best practices complete

---

## Sprint Focus

This sprint is about **building the foundation for perfect code**. We want:

1. **Comprehensive test coverage** - Catch bugs before they reach production
2. **Strong type safety** - Eliminate type-related bugs entirely
3. **Automated quality gates** - Make it impossible to commit bad code
4. **Continuous monitoring** - Track code quality metrics over time

---

## Sprint Backlog

### Epic 1: Frontend Testing Infrastructure (6-8 hours)

#### Task 1.1: Vitest + React Testing Library Setup
**Effort:** 2 hours
**Status:** 📋 Not Started
**Priority:** High

**Description:**
- Install vitest and @vitest/ui
- Install @testing-library/react and @testing-library/jest-dom
- Install @vitest/coverage-v8 for coverage reporting
- Create vitest.config.ts
- Create test setup file (test-setup.ts)
- Configure coverage thresholds (70% minimum)
- Add test scripts to package.json

**Acceptance Criteria:**
- [ ] `npm test` runs vitest
- [ ] `npm run test:ui` opens vitest UI
- [ ] `npm run test:coverage` generates coverage report
- [ ] Coverage thresholds enforced (build fails if < 70%)
- [ ] Testing utilities configured (custom render, etc.)

**Files to create:**
- `frontend/vitest.config.ts`
- `frontend/src/test-setup.ts`
- `frontend/src/test-utils.tsx` (custom render with providers)

**Dependencies to install:**
```bash
npm install -D vitest @vitest/ui @vitest/coverage-v8
npm install -D @testing-library/react @testing-library/jest-dom
npm install -D @testing-library/user-event
npm install -D jsdom
```

---

#### Task 1.2: Write Tests for Notes Feature
**Effort:** 3 hours
**Status:** 📋 Not Started
**Priority:** High
**Dependencies:** Task 1.1

**Description:**
- Write unit tests for useGameContext hook
- Write component tests for Notes page
- Write component tests for NoteFormDialog
- Write component tests for NotesTable
- Write tests for notes-columns
- Achieve 70%+ coverage on Notes feature

**Acceptance Criteria:**
- [ ] useGameContext hook tested (get, set, localStorage)
- [ ] Notes CRUD operations tested
- [ ] Game filtering tested
- [ ] Form validation tested
- [ ] Error states tested
- [ ] Loading states tested
- [ ] Coverage > 70% on Notes feature

**Test files to create:**
- `frontend/src/hooks/useGameContext.test.ts`
- `frontend/src/features/notes/index.test.tsx`
- `frontend/src/features/notes/components/note-form-dialog.test.tsx`
- `frontend/src/features/notes/components/notes-table.test.tsx`

**Example test structure:**
```typescript
import { renderHook, act } from '@testing-library/react'
import { useGameContext, GameProvider } from '@/hooks/useGameContext'

describe('useGameContext', () => {
  it('should default to poe1', () => {
    const { result } = renderHook(() => useGameContext(), {
      wrapper: GameProvider,
    })
    expect(result.current.game).toBe('poe1')
  })

  it('should persist to localStorage', () => {
    const { result } = renderHook(() => useGameContext(), {
      wrapper: GameProvider,
    })
    act(() => {
      result.current.setGame('poe2')
    })
    expect(localStorage.getItem('pom-game-context')).toBe('poe2')
  })
})
```

---

#### Task 1.3: Playwright E2E Tests
**Effort:** 2.5 hours
**Status:** 📋 Not Started
**Priority:** Medium
**Dependencies:** Task 1.2

**Description:**
- Install Playwright
- Configure Playwright for Docker support
- Write E2E test for Notes CRUD flow
- Write E2E test for game switching persistence
- Write E2E test for error handling
- Configure screenshots on failure

**Acceptance Criteria:**
- [ ] Playwright installed and configured
- [ ] Can run tests against local dev server
- [ ] Can run tests in Docker container
- [ ] Notes CRUD flow fully tested
- [ ] Game switching tested
- [ ] Screenshots captured on failures

**Dependencies to install:**
```bash
npm install -D @playwright/test
npx playwright install
```

**Test files to create:**
- `frontend/e2e/notes.spec.ts`
- `frontend/e2e/game-switching.spec.ts`
- `frontend/playwright.config.ts`

---

### Epic 2: Backend Testing Enhancement (4-5 hours)

#### Task 2.1: Write Tests for Notes API
**Effort:** 2 hours
**Status:** ✅ Completed
**Priority:** High

**Description:**
- ~~Write API tests for GET /api/notes~~ ✅
- ~~Write API tests for POST /api/notes~~ ✅
- ~~Write API tests for PUT /api/notes/{id}~~ ✅
- ~~Write API tests for DELETE /api/notes/{id}~~ ✅
- ~~Test game context filtering~~ ✅
- ~~Test validation errors~~ ✅
- ~~Test 404 scenarios~~ ✅

**Acceptance Criteria:**
- [x] All CRUD endpoints tested ✅ (32 tests)
- [x] Game filtering tested ✅
- [x] Validation tested ✅
- [x] Error cases tested ✅
- [x] Tests use proper fixtures ✅
- [x] Tests are isolated (clean DB between tests) ✅

**Test file created:**
- ✅ `backend/tests/contexts/placeholder/test_notes_api.py` (594 lines, 32 tests)

**Example test structure:**
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_note(client: AsyncClient, db: AsyncSession):
    response = await client.post(
        "/api/notes",
        json={
            "title": "Test Note",
            "content": "Test content",
            "game_context": "poe1"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["game_context"] == "poe1"

@pytest.mark.asyncio
async def test_list_notes_filters_by_game(client: AsyncClient, db: AsyncSession):
    # Create notes for both games
    # Test filtering
    pass
```

---

#### Task 2.2: Backend Test Coverage & Type Safety
**Effort:** 2 hours
**Status:** ✅ Partially Completed (Coverage Done, Type Safety Pending)
**Priority:** High
**Dependencies:** Task 2.1

**Description:**
- ~~Configure pytest-cov for coverage reporting~~ ✅
- ~~Set coverage threshold to 70%~~ ✅
- ~~Generate HTML coverage reports~~ ✅
- ~~Create test runner script~~ ✅
- Enable mypy strict mode (pending)
- Fix all type errors in our code (src/contexts/) (pending)
- Add type hints to all functions (pending)

**Acceptance Criteria:**
- [x] `./scripts/test.sh --coverage` shows coverage ✅
- [x] Coverage threshold enforced (70%) ✅ (Currently 76.39%)
- [x] HTML coverage report generated ✅
- [ ] mypy strict mode enabled
- [ ] Zero type errors in src/contexts/
- [ ] All functions have type hints

**Files to modify:**
- `backend/pyproject.toml` - Add coverage config
- `backend/mypy.ini` or inline config - Enable strict mode

**Coverage config example:**
```toml
[tool.coverage.run]
source = ["src/contexts"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 70
show_missing = true
```

---

### Epic 3: Code Quality Tools (3-4 hours)

#### Task 3.1: Dead Code Detection
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** Medium

**Description:**
- Install vulture for Python dead code detection
- Install knip for TypeScript/JavaScript dead code detection
- Configure both tools with proper exclusions
- Run analysis and document findings
- Remove or document dead code
- Add to CI pipeline

**Acceptance Criteria:**
- [ ] vulture configured and working
- [ ] knip configured and working
- [ ] Analysis run on both codebases
- [ ] Dead code documented or removed
- [ ] Tools integrated into check-code.sh

**Dependencies to install:**
```bash
# Backend
uv add --dev vulture

# Frontend
npm install -D knip
```

**Scripts to add:**
```bash
# Backend
docker compose exec backend uv run vulture src/contexts/

# Frontend
npm run knip
```

---

#### Task 3.2: Code Complexity Analysis
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** Medium

**Description:**
- Install radon for Python complexity analysis
- Configure complexity linting in eslint
- Set complexity thresholds (cyclomatic complexity < 10)
- Run analysis and identify complex functions
- Document complex code that needs refactoring
- Add to CI pipeline

**Acceptance Criteria:**
- [ ] radon configured for Python
- [ ] eslint complexity rules enabled
- [ ] Complexity thresholds set
- [ ] Complex functions documented
- [ ] Tools integrated into check-code.sh

**Dependencies to install:**
```bash
# Backend
uv add --dev radon

# Frontend (already has eslint)
# Just configure complexity rules
```

**Radon usage:**
```bash
docker compose exec backend uv run radon cc src/contexts/ -a -nb
docker compose exec backend uv run radon mi src/contexts/
```

---

#### Task 3.3: Pre-commit Hooks
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** High
**Dependencies:** Task 3.1, Task 3.2

**Description:**
- Install pre-commit framework
- Create .pre-commit-config.yaml
- Add hooks for linting (ruff, eslint)
- Add hooks for formatting (ruff format, prettier)
- Add hooks for type checking (mypy, tsc)
- Add hooks for tests (fast tests only)
- Add hooks for dead code detection
- Document pre-commit workflow

**Acceptance Criteria:**
- [ ] pre-commit installed and configured
- [ ] Hooks run on every commit
- [ ] Bad commits are blocked
- [ ] Hooks run fast (< 10 seconds)
- [ ] Documentation updated with pre-commit workflow

**File to create:**
- `.pre-commit-config.yaml`

**Pre-commit config example:**
```yaml
repos:
  - repo: local
    hooks:
      - id: backend-lint
        name: Backend Linting (ruff)
        entry: docker compose exec -T backend uv run ruff check src/contexts/
        language: system
        pass_filenames: false

      - id: backend-format
        name: Backend Formatting (ruff format)
        entry: docker compose exec -T backend uv run ruff format --check src/contexts/
        language: system
        pass_filenames: false

      - id: backend-types
        name: Backend Type Checking (mypy)
        entry: docker compose exec -T backend uv run mypy src/contexts/
        language: system
        pass_filenames: false

      - id: frontend-lint
        name: Frontend Linting (eslint)
        entry: bash -c "cd frontend && npm run lint"
        language: system
        pass_filenames: false

      - id: frontend-types
        name: Frontend Type Checking (tsc)
        entry: bash -c "cd frontend && npx tsc --noEmit"
        language: system
        pass_filenames: false
```

---

### Epic 4: CI/CD Pipeline (2-3 hours)

#### Task 4.1: GitHub Actions Workflows
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** High

**Description:**
- Create .github/workflows/ci.yml
- Add job for linting (backend + frontend)
- Add job for type checking (backend + frontend)
- Add job for tests (backend + frontend)
- Add job for coverage reporting
- Configure caching for dependencies
- Add status badges to README

**Acceptance Criteria:**
- [ ] CI runs on every push
- [ ] CI runs on every pull request
- [ ] All quality checks run in parallel
- [ ] Failed checks block PR merge
- [ ] Status badges in README

**File to create:**
- `.github/workflows/ci.yml`

**Workflow example:**
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Lint Backend
        run: |
          docker compose up -d postgres redis
          docker compose exec -T backend uv run ruff check src/contexts/
          docker compose exec -T backend uv run mypy src/contexts/

  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Backend Tests
        run: |
          docker compose up -d
          docker compose exec -T backend uv run pytest --cov=src/contexts --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Lint
        run: cd frontend && npm run lint
      - name: Type check
        run: cd frontend && npx tsc --noEmit

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Test
        run: cd frontend && npm run test:coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

#### Task 4.2: Coverage Reporting & Enforcement
**Effort:** 1 hour
**Status:** 📋 Not Started
**Priority:** Medium
**Dependencies:** Task 4.1

**Description:**
- Set up Codecov (or similar)
- Configure coverage thresholds
- Add coverage badges to README
- Configure PR comments with coverage diff
- Block PRs with coverage decrease

**Acceptance Criteria:**
- [ ] Codecov integrated
- [ ] Coverage visible in PR comments
- [ ] Coverage badges in README
- [ ] PRs blocked if coverage drops

---

### Epic 5: Documentation (1-2 hours)

#### Task 5.1: Testing Best Practices Guide
**Effort:** 1 hour
**Status:** 📋 Not Started
**Priority:** Medium

**Description:**
- Create docs/TESTING.md
- Document how to write unit tests
- Document how to write E2E tests
- Document testing patterns (arrange-act-assert)
- Add examples for common scenarios
- Document mocking strategies
- Document coverage interpretation

**Acceptance Criteria:**
- [ ] docs/TESTING.md created
- [ ] Unit test examples included
- [ ] E2E test examples included
- [ ] Mocking patterns documented
- [ ] Coverage guidelines included

---

#### Task 5.2: Pre-commit Workflow Documentation
**Effort:** 0.5 hours
**Status:** 📋 Not Started
**Priority:** Low
**Dependencies:** Epic 3

**Description:**
- Update README with pre-commit instructions
- Document how to install pre-commit hooks
- Document how to skip hooks (emergency only)
- Add pre-commit workflow to development guide

**Acceptance Criteria:**
- [ ] README updated
- [ ] Installation instructions clear
- [ ] Emergency skip documented
- [ ] Examples included

---

## Sprint Metrics

**Total Estimated Effort:** 17-22 hours

**Breakdown by Epic:**
- Epic 1 (Frontend Testing): 7.5 hours (38%)
- Epic 2 (Backend Testing): 4 hours (20%)
- Epic 3 (Code Quality): 4.5 hours (23%)
- Epic 4 (CI/CD): 2.5 hours (13%)
- Epic 5 (Documentation): 1.5 hours (8%)

**Priority Distribution:**
- High Priority: 12.5 hours (63%)
- Medium Priority: 7 hours (35%)
- Low Priority: 0.5 hours (3%)

---

## Sprint Board

### To Do 📋
- Task 1.1: Vitest + React Testing Library Setup
- Task 1.2: Write Tests for Notes Feature
- Task 1.3: Playwright E2E Tests
- Task 2.2: Backend Test Coverage & Type Safety (Type Safety portion)
- Task 3.1: Dead Code Detection
- Task 3.2: Code Complexity Analysis
- Task 3.3: Pre-commit Hooks
- Task 4.1: GitHub Actions Workflows
- Task 4.2: Coverage Reporting & Enforcement
- Task 5.1: Testing Best Practices Guide
- Task 5.2: Pre-commit Workflow Documentation

### In Progress 🚧
*(None yet)*

### Done ✅
- Task 2.1: Write Tests for Notes API ✅ (32 tests, 594 lines)
- Task 2.2: Backend Test Coverage (partial) ✅ (76.39% coverage, test.sh script)

---

## Success Criteria

At the end of this sprint, we should have:

1. **Comprehensive test coverage** - 70%+ on both frontend and backend
2. **E2E tests** - Critical user flows tested with Playwright
3. **Strong type safety** - mypy strict mode with zero errors
4. **Automated quality gates** - Pre-commit hooks prevent bad code
5. **CI/CD pipeline** - All quality checks automated
6. **Code quality metrics** - Dead code and complexity monitored
7. **Documentation** - Clear guidelines for testing and quality

This establishes a **world-class quality infrastructure** that ensures perfect code.

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Test setup takes longer than expected | Medium | Medium | Start with backend (simpler), learn patterns |
| Playwright in Docker is complex | Medium | Low | Use local dev server first, Docker later |
| mypy strict mode reveals many errors | High | Medium | Fix incrementally, focus on src/contexts/ only |
| Pre-commit hooks slow down commits | Medium | Low | Optimize hooks, run only fast checks |
| CI/CD pipeline configuration issues | Low | Low | Start simple, add complexity gradually |

---

## Dependencies

**Before starting this sprint:**
- Phase 1 complete ✅
- Development environment working ✅
- Notes feature functional ✅

**External dependencies:**
- GitHub account for Actions
- Codecov account (or alternative)
- Docker running locally

---

## Notes

**Philosophy:**
This sprint is an investment in quality that will pay dividends for the entire project lifecycle. Every hour spent here saves 10 hours of debugging later.

**Testing Strategy:**
- Start with backend tests (simpler, faster feedback)
- Move to frontend unit tests (most value)
- Finish with E2E tests (most complex, but covers everything)

**Type Safety:**
- mypy strict mode is non-negotiable for production code
- TypeScript strict mode already enabled
- All functions must have type hints

**Quality Gates:**
- Pre-commit hooks are the first line of defense
- CI/CD is the safety net
- Coverage requirements prevent untested code

---

**Last Updated:** 2025-11-18
**Sprint Owner:** TBD
**Status:** 🚧 In Progress (15%)

---

## Progress Notes

**2025-11-18 - Sprint Started:**
- Completed Task 2.1: Write Tests for Notes API
  - Created 32 comprehensive integration tests (594 lines)
  - Tests cover all CRUD operations, validation, error cases, and game context filtering
  - Fixed partial update bug in service layer
  - Fixed SQLAlchemy deprecation warning
- Completed Task 2.2 (Coverage portion): Backend Test Coverage
  - Configured pytest-cov with 70% threshold
  - Achieved 76.39% coverage (exceeds target)
  - Created test runner script (scripts/test.sh)
  - Updated backend README with testing documentation
- Next up: Frontend testing (Vitest + React Testing Library)
