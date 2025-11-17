# Sprint: Phase 1 - Polish & Foundation

**Sprint Goal:** Polish the admin template integration, customize branding, and lay groundwork for data ingestion pipeline.

**Sprint Duration:** 1-2 weeks
**Sprint Status:** 🚧 In Progress (0%)
**Start Date:** 2025-11-17

---

## Definition of Done

Phase 1 Sprint is complete when:

- ✅ Admin template is customized with POE branding
- ✅ Game selector UI component is implemented
- ✅ Notes feature is fully functional end-to-end
- ✅ Basic test coverage added for critical paths
- ✅ poe.ninja API integration proof-of-concept working
- ✅ Database schema designed for item/price data
- ✅ Documentation updated with new architecture decisions

---

## Sprint Focus

This sprint focuses on **polishing what we have** and **proving out the data pipeline concept** before diving deep into implementation. We want to:

1. Make the admin template feel like "Path of Mirrors" not "Shadcn Admin"
2. Ensure the notes feature works flawlessly (our reference implementation)
3. Validate that we can fetch and parse poe.ninja data
4. Design the database schema for Phase 1 properly

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
**Status:** 📋 Not Started
**Priority:** Medium
**Dependencies:** Task 2.1

**Description:**
- Set up Vitest + React Testing Library
- Write tests for Notes feature components
- Write tests for useGameContext hook
- Write backend API tests for notes endpoint

**Acceptance Criteria:**
- [ ] `pnpm test` runs frontend tests
- [ ] `uv run pytest` runs backend tests
- [ ] Notes CRUD operations tested
- [ ] Game context filtering tested
- [ ] Tests pass in CI (manual run OK for now)

**Test files to create:**
- `frontend/src/features/notes/index.test.tsx`
- `frontend/src/hooks/useGameContext.test.ts`
- `backend/tests/contexts/placeholder/test_notes_api.py`

---

### Epic 3: poe.ninja Integration PoC (6-8 hours)

#### Task 3.1: Research poe.ninja API
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** High

**Description:**
- Document poe.ninja API endpoints
- Understand data structure for items, currency, builds
- Identify rate limits and best practices
- Create API documentation in `docs/POE_NINJA_API.md`

**Acceptance Criteria:**
- [ ] API endpoints documented with examples
- [ ] Data structures understood and documented
- [ ] Rate limits identified
- [ ] Authentication requirements (if any) documented

**API Endpoints to Document:**
- Economy snapshots: `/api/data/itemoverview`
- Currency rates: `/api/data/currencyoverview`
- Build ladders: (TBD - needs research)

---

#### Task 3.2: Create poe.ninja Adapter
**Effort:** 3 hours
**Status:** 📋 Not Started
**Priority:** High
**Dependencies:** Task 3.1

**Description:**
- Create `contexts/upstream/` bounded context
- Implement poe.ninja client with httpx
- Add error handling and retries
- Add rate limiting
- Parse item data into Python dataclasses

**Acceptance Criteria:**
- [ ] Can fetch economy snapshot for POE1
- [ ] Can fetch economy snapshot for POE2
- [ ] Data parsed into structured models
- [ ] Errors handled gracefully
- [ ] Rate limiting prevents API abuse

**Files to create:**
- `backend/src/contexts/upstream/adapters/poe_ninja_adapter.py`
- `backend/src/contexts/upstream/domain/models.py`
- `backend/src/contexts/upstream/ports/provider.py`

---

#### Task 3.3: Display Sample Data in Frontend
**Effort:** 2 hours
**Status:** 📋 Not Started
**Priority:** Medium
**Dependencies:** Task 3.2

**Description:**
- Create Items page (placeholder)
- Add API endpoint to fetch sample poe.ninja data
- Display in a simple table
- Show we can ingest and display real POE data

**Acceptance Criteria:**
- [ ] Items page shows table of items from poe.ninja
- [ ] Data includes item name, price, change %
- [ ] Refreshes on game context switch
- [ ] Proves out the full data flow

---

### Epic 4: Database Schema Design (2-3 hours)

#### Task 4.1: Design Item/Price Schema
**Effort:** 1.5 hours
**Status:** 📋 Not Started
**Priority:** Medium

**Description:**
- Design PostgreSQL schema for items table
- Design schema for price_history table
- Plan for partitioning by date
- Document schema in `docs/DATABASE_SCHEMA.md`

**Acceptance Criteria:**
- [ ] Schema supports both POE1 and POE2
- [ ] Supports time-series price data
- [ ] Optimized for trend queries
- [ ] Migration plan documented

**Schema considerations:**
- Game context (poe1/poe2)
- Item base type, variant, links, etc.
- Price in chaos equivalent
- Date/time of snapshot
- Indexes for performance

---

#### Task 4.2: Create Alembic Migration
**Effort:** 1 hour
**Status:** 📋 Not Started
**Priority:** Low
**Dependencies:** Task 4.1

**Description:**
- Create Alembic migration for items/prices tables
- Test migration up/down
- Add sample data seeding script

**Acceptance Criteria:**
- [ ] Migration creates tables successfully
- [ ] Migration is reversible
- [ ] Sample data can be seeded for testing

---

## Sprint Metrics

**Total Estimated Effort:** 17-23 hours

**Breakdown by Epic:**
- Epic 1 (UI Polish): 4-6 hours (29%)
- Epic 2 (Notes Polish): 3-4 hours (18%)
- Epic 3 (poe.ninja PoC): 6-8 hours (38%)
- Epic 4 (Database Design): 2-3 hours (15%)

**Priority Distribution:**
- High Priority: 12-16 hours (70%)
- Medium Priority: 4-6 hours (24%)
- Low Priority: 1 hour (6%)

---

## Sprint Board

### To Do 📋
- Task 1.1: Customize Branding & Theme
- Task 1.2: Implement Game Selector UI Component
- Task 1.3: Clean Up Navigation & Pages
- Task 2.1: End-to-End Testing & Fixes
- Task 2.2: Add Basic Tests
- Task 3.1: Research poe.ninja API
- Task 3.2: Create poe.ninja Adapter
- Task 3.3: Display Sample Data in Frontend
- Task 4.1: Design Item/Price Schema
- Task 4.2: Create Alembic Migration

### In Progress 🚧
*(None yet)*

### Done ✅
*(None yet)*

---

## Success Criteria

At the end of this sprint, we should have:

1. **A polished UI** that looks and feels like "Path of Mirrors"
2. **A working game selector** that persists and filters data correctly
3. **A fully tested Notes feature** as our reference implementation
4. **Proof that we can fetch poe.ninja data** and display it
5. **A solid database schema** ready for Phase 1 implementation

This sets us up perfectly for Phase 1 proper, where we'll build out the full data ingestion pipeline.

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| poe.ninja API changes format | Low | High | Document format, add tests, version API calls |
| Rate limiting blocks development | Medium | Medium | Implement caching, use sample data for dev |
| Database schema needs rework | Medium | Medium | Start simple, iterate based on real data |
| Testing setup takes longer than expected | Medium | Low | Defer to Phase 1 if needed, focus on manual testing |

---

## Next Sprint Preview

After this sprint, Phase 1 proper will focus on:

1. **Full Data Ingestion** - ARQ jobs to fetch daily snapshots
2. **Historical Storage** - 28-day rolling window
3. **Basic Analytics** - Price trends, popular items
4. **Market Dashboard** - Real-time market intelligence UI

---

**Last Updated:** 2025-11-17
**Sprint Owner:** TBD
**Status:** 🚧 In Progress (0%)
