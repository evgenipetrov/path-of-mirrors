# Sprint: Phase 1 - Polish & Foundation

**Sprint Goal:** Polish the admin template with POE branding, ensure Notes feature quality, and verify development tooling.

**Sprint Duration:** 1 week
**Sprint Status:** 🚧 In Progress (15%)
**Start Date:** 2025-11-18

---

## Definition of Done

Phase 1 Sprint is complete when:

- ✅ Admin template is customized with POE branding
- ✅ Game selector UI component is implemented
- ✅ Navigation cleaned up with proper POE-themed structure
- ✅ Notes feature is fully functional end-to-end
- ✅ Basic test coverage added for Notes feature
- ✅ All linters verified and working (backend + frontend)
- ✅ Test runners verified and working with coverage
- ✅ Documentation updated with testing guidelines

---

## Sprint Focus

This sprint focuses on **polishing what we have** and **verifying our development tooling** is production-ready. We want to:

1. Make the admin template feel like "Path of Mirrors" not "Shadcn Admin"
2. Ensure the notes feature works flawlessly (our reference implementation)
3. Verify all our development scripts work correctly (linters, tests, coverage)
4. Establish testing patterns and quality standards for future development

---

## Sprint Backlog

### Epic 1: UI Polish & Branding (4-6 hours)

#### Task 1.1: Customize Branding & Theme
**Effort:** 2 hours
**Status:** 📋 Not Started
**Priority:** High

**Description:**
- Update app name from "Shadcn Admin" to "Path of Mirrors"
- Replace logo/favicon with POE-themed assets
- Customize color scheme for POE aesthetic (dark gold, purple)
- Update sidebar team switcher with POE1/POE2 contexts
- Clean up example pages (remove Clerk auth pages, etc.)

**Acceptance Criteria:**
- [ ] App title shows "Path of Mirrors" everywhere
- [ ] Sidebar shows POE-themed logo
- [ ] Color scheme matches POE aesthetic
- [ ] Team switcher removed or repurposed for games
- [ ] Unused demo pages removed

**Files to modify:**
- `frontend/src/components/layout/data/sidebar-data.ts`
- `frontend/public/images/` (favicon, logo)
- `frontend/src/styles/theme.css` (color variables)
- `frontend/index.html` (title)

---

#### Task 1.2: Implement Game Selector UI Component
**Effort:** 2 hours
**Status:** 📋 Not Started
**Priority:** High
**Dependencies:** Task 1.1

**Description:**
- Create GameSelector dropdown component (POE1 / POE2)
- Add to top navigation bar
- Persist selection to localStorage
- Update useGameContext to load from localStorage on init
- Style to match POE aesthetic

**Acceptance Criteria:**
- [ ] Dropdown visible in top nav
- [ ] Shows "Path of Exile 1" and "Path of Exile 2" options
- [ ] Selection persists across page reloads
- [ ] Current game shows in dropdown
- [ ] Notes page filters by selected game

**Component API:**
```tsx
<GameSelector
  value={game}
  onChange={setGame}
  className="w-48"
/>
```

---

#### Task 1.3: Clean Up Navigation & Pages
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** Medium

**Description:**
- Remove unused pages (Clerk auth, extra settings)
- Simplify sidebar navigation
- Add placeholders for Phase 1 features (Items, Builds, Market)
- Update dashboard with POE-relevant KPIs

**Acceptance Criteria:**
- [ ] Sidebar shows only: Dashboard, Notes, Items (placeholder), Builds (placeholder), Market (placeholder), Settings
- [ ] Clerk-related pages removed
- [ ] Coming Soon placeholders for future features
- [ ] Dashboard shows POE-relevant widgets (mock data OK)

---

### Epic 2: Notes Feature Polish (3-4 hours)

#### Task 2.1: End-to-End Testing & Fixes
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** High

**Description:**
- Manually test full CRUD flow (create, read, update, delete)
- Test game context filtering
- Add loading states and error handling
- Add empty state messaging
- Fix any bugs discovered

**Acceptance Criteria:**
- [ ] Can create note with title + content
- [ ] Can edit existing note
- [ ] Can delete note with confirmation
- [ ] Game filter works correctly
- [ ] Empty state shows helpful message
- [ ] Loading spinner shows during API calls
- [ ] Errors display with helpful messages

---

#### Task 2.2: Add Basic Tests
**Effort:** 1.5 hours
**Status:** ✅ Completed (Backend Only)
**Priority:** Medium
**Dependencies:** Task 2.1

**Description:**
- ~~Set up pytest with coverage for backend~~ ✅
- ~~Write backend API tests for notes endpoint~~ ✅
- Set up Vitest + React Testing Library (deferred to Quality Sprint)
- Write tests for Notes feature components (deferred to Quality Sprint)
- Write tests for useGameContext hook (deferred to Quality Sprint)

**Acceptance Criteria:**
- [ ] `pnpm test` runs frontend tests (deferred)
- [x] `uv run pytest` runs backend tests ✅
- [x] Notes CRUD operations tested ✅ (32 tests)
- [x] Game context filtering tested ✅
- [x] Tests pass ✅
- [x] Coverage > 70% ✅ (76.39%)

**Test files created:**
- ✅ `backend/tests/contexts/placeholder/test_notes_api.py` (594 lines, 32 tests)
- ✅ `backend/scripts/test.sh` (test runner script)
- 🔜 `frontend/src/features/notes/index.test.tsx` (deferred)
- 🔜 `frontend/src/hooks/useGameContext.test.ts` (deferred)

---

### Epic 3: Development Tooling Verification (3-4 hours)

#### Task 3.1: Verify Linters & Formatters
**Effort:** 1 hour
**Status:** 📋 Not Started
**Priority:** High

**Description:**
- Run `./scripts/check-code.sh` and verify all tools work
- Ensure ruff (check + format) works for backend
- Ensure mypy type checking works for backend
- Ensure eslint works for frontend
- Ensure TypeScript type checking works for frontend
- Document any configuration issues

**Acceptance Criteria:**
- [ ] `./scripts/check-code.sh` runs successfully
- [ ] `./scripts/check-code.sh --fix` auto-fixes issues
- [ ] Backend linters catch common Python issues
- [ ] Frontend linters catch common TypeScript/React issues
- [ ] All linter configs documented in code style conventions

**Files to verify:**
- `backend/pyproject.toml` (ruff config)
- `backend/mypy.ini` or inline config
- `frontend/.eslintrc.cjs`
- `frontend/tsconfig.json`

---

#### Task 3.2: Verify Test Runners & Coverage
**Effort:** 1.5 hours
**Status:** ✅ Completed (Backend Only)
**Priority:** High

**Description:**
- ~~Run backend test script and verify it works~~ ✅
- ~~Set up pytest-cov for backend coverage reporting~~ ✅
- ~~Establish minimum coverage thresholds (70%)~~ ✅
- ~~Document coverage in README~~ ✅
- Set up vitest coverage for frontend (deferred to Quality Sprint)

**Acceptance Criteria:**
- [x] `./scripts/test.sh` runs backend tests ✅
- [x] Coverage reports work (HTML + terminal) ✅
- [x] Backend coverage > 70% ✅ (76.39%)
- [x] Coverage thresholds configured in pyproject.toml ✅
- [x] Backend README updated with testing documentation ✅
- [ ] Frontend coverage (deferred to Quality Sprint)

**Coverage tools configured:**
- ✅ Backend: `pytest-cov` configured with 70% threshold
- 🔜 Frontend: `@vitest/coverage-v8` (deferred)

---

#### Task 3.3: Document Testing & Quality Guidelines
**Effort:** 1 hour
**Status:** 📋 Not Started
**Priority:** Medium
**Dependencies:** Task 3.1, Task 3.2

**Description:**
- Create `docs/TESTING.md` with testing best practices
- Document how to run tests locally
- Document how to check coverage
- Document pre-commit checklist
- Add testing examples for common patterns

**Acceptance Criteria:**
- [ ] `docs/TESTING.md` created with comprehensive guide
- [ ] Examples for backend unit tests (pytest)
- [ ] Examples for frontend component tests (vitest + RTL)
- [ ] Pre-commit checklist documented
- [ ] Coverage interpretation guidelines included

**Topics to cover:**
- How to write unit tests (backend + frontend)
- How to run tests locally
- How to check coverage reports
- Testing best practices (arrange-act-assert, mocking, etc.)
- Pre-commit workflow

---

## Sprint Metrics

**Total Estimated Effort:** 10-14 hours

**Breakdown by Epic:**
- Epic 1 (UI Polish & Branding): 5.5 hours (44%)
- Epic 2 (Notes Feature Polish): 3 hours (24%)
- Epic 3 (Tooling Verification): 3.5 hours (28%)

**Priority Distribution:**
- High Priority: 8.5 hours (68%)
- Medium Priority: 4 hours (32%)

---

## Sprint Board

### To Do 📋
- Task 1.1: Customize Branding & Theme
- Task 1.2: Implement Game Selector UI Component
- Task 1.3: Clean Up Navigation & Pages
- Task 2.1: End-to-End Testing & Fixes
- Task 3.1: Verify Linters & Formatters
- Task 3.3: Document Testing & Quality Guidelines

### In Progress 🚧
*(None - Sprint paused to jump to Quality Sprint)*

### Done ✅
- Task 2.2: Add Basic Tests (Backend) - 32 tests, 76.39% coverage
- Task 3.2: Verify Test Runners & Coverage (Backend) - test.sh script works

### Deferred to Future Sprint 🔮
- Epic: poe.ninja Integration PoC (6-8 hours)
  - Research poe.ninja API
  - Create poe.ninja Adapter
  - Display Sample Data in Frontend
- Epic: Database Schema Design (2-3 hours)
  - Design Item/Price Schema
  - Create Alembic Migration

---

## Success Criteria

At the end of this sprint, we should have:

1. **A polished UI** that looks and feels like "Path of Mirrors" not "Shadcn Admin"
2. **A working game selector** that persists and filters data correctly
3. **A fully tested Notes feature** as our reference implementation
4. **Verified development tooling** - all linters, tests, and coverage tools working
5. **Quality standards established** - testing patterns and guidelines documented

This sets us up perfectly for future sprints where we'll build out the data ingestion pipeline with confidence in our development workflow.

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Frontend tests not yet set up | High | Medium | Start with backend tests, add frontend tests incrementally |
| Coverage tools need configuration | Medium | Medium | Use default configs first, customize as needed |
| Branding assets not available | Medium | Medium | Use placeholders, finalize design later |
| Testing takes longer than expected | Medium | Low | Focus on critical paths first, expand coverage later |

---

## Next Sprint Preview

After this sprint, future development will focus on:

1. **poe.ninja Integration** - Research API, create adapter, display sample data
2. **Database Schema Design** - Design and migrate items/prices tables
3. **Data Ingestion Pipeline** - ARQ jobs to fetch daily snapshots
4. **Market Intelligence UI** - Dashboard with price trends and analytics

---

**Last Updated:** 2025-11-18 (Updated after backend testing completion)
**Sprint Owner:** TBD
**Status:** 🚧 Paused (15%) - Pivoting to Quality Sprint

---

## Notes

**Scope Changes:**
- Deferred Epic 3 (poe.ninja Integration) and Epic 4 (Database Schema) to future sprint
- Added Epic 3 (Development Tooling Verification) to ensure quality infrastructure
- Reduced sprint duration from 1-2 weeks to 1 week
- Reduced total effort from 17-23 hours to 10-14 hours
- Focused on polishing existing work and establishing quality standards

**Sprint Pivot (2025-11-18):**
- After completing backend testing infrastructure (Tasks 2.2 & 3.2), decided to pivot to **Quality Sprint**
- Backend tests completed: 32 tests with 76.39% coverage
- Remaining Phase 1 tasks (UI polish, frontend tests) will be completed after Quality Sprint
- Quality Sprint will establish comprehensive testing & quality infrastructure across the entire stack
- This ensures a solid foundation before continuing with feature development
