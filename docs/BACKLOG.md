# Product Backlog

This document outlines the planned work for Phases 1-6 of Path of Mirrors. Each phase builds on the previous one, gradually transforming the application from a data ingestion pipeline into a complete economic intelligence platform.

**Current Phase:** Phase 1 (see [SPRINT.md](SPRINT.md) for detailed tasks)

______________________________________________________________________

## Deferred from Phase 0

The following items were deferred from Phase 0 and should be addressed as needed:

- **Task 1.6:** Backend Tests (>80% coverage for contexts)
- **Task 2.4:** Game Selector UI Component (context exists, UI component pending)
- **Task 2.6:** Frontend Tests (>80% coverage for components)
- **Task 3.2:** CI/CD Pipeline (GitHub Actions for automated testing/linting)
- **Task 4.1:** E2E Smoke Test (Manual testing completed, automated pending)
- **Task 4.2:** Documentation Review (Living document, ongoing)

These can be added incrementally during Phase 1+ when capacity allows.

______________________________________________________________________

## Table of Contents

- [Deferred from Phase 0](#deferred-from-phase-0)
- [Phase 1: Upstream Foundation](#phase-1-upstream-foundation)
- [Phase 2: Market Intelligence](#phase-2-market-intelligence)
- [Phase 3: Crafting Assistant](#phase-3-crafting-assistant)
- [Phase 4: Deal Finder](#phase-4-deal-finder)
- [Phase 5: Price Checker](#phase-5-price-checker)
- [Phase 6: Planner & Ops](#phase-6-planner--ops)

______________________________________________________________________

## Phase 1: Upstream Foundation

**Goal:** Build the data ingestion pipeline that powers all downstream features

**Duration:** 3-4 weeks (40-50 hours)

**Status:** Planned

**Dependencies:** Phase 0 complete

### Objectives

Establish a reliable, automated data pipeline that fetches, normalizes, and stores economic data from poe.ninja for both PoE1 and PoE2, enabling trend analysis and market intelligence.

### Key Deliverables

1. **Game Abstraction Layer**

   - Game enum (`poe1`, `poe2`)
   - Provider factory pattern
   - Unified interface for game-specific adapters

1. **poe.ninja Integration**

   - PoE1 adapter (economy snapshots, build ladders)
   - PoE2 adapter (economy snapshots, build ladders)
   - Error handling and retry logic
   - Rate limiting to respect API limits

1. **Canonical Schemas**

   - Item model (game-agnostic with game-specific extensions)
   - Modifier model (affixes, implicits, enchants)
   - League model (league names, start/end dates, game context)
   - Currency model (pricing, fluctuations)

1. **Data Normalization**

   - PoE1 → Canonical mapping
   - PoE2 → Canonical mapping
   - Modifier parsing and categorization
   - Price normalization (chaos equivalents)

1. **Background Job System**

   - ARQ job queue configuration
   - Daily snapshot fetch job (PoE1 + PoE2)
   - 28-day retention cleanup job
   - Job monitoring and alerting

1. **Database Schema**

   - Game-specific snapshot tables (partitioned by date)
   - Normalized item tables
   - Materialized views for trend queries
   - Indexes for performance

### Epics

#### Epic 1.1: Game Abstraction Layer (8-10 hours)

**Tasks:**

- Define `Game` enum and context models
- Create provider factory pattern
- Implement base provider interface
- Add game context to database queries
- Update API endpoints to accept game parameter

**Acceptance Criteria:**

- [ ] Game enum (`poe1`, `poe2`) defined in `shared/game_context.py`
- [ ] Factory returns correct provider based on game
- [ ] All database queries filter by game context
- [ ] API endpoints accept `game` query parameter

______________________________________________________________________

#### Epic 1.2: poe.ninja API Integration (12-15 hours)

**Tasks:**

- Research poe.ninja API endpoints (PoE1 and PoE2)
- Implement HTTP client with retry logic
- Create PoE1 poe.ninja adapter
- Create PoE2 poe.ninja adapter
- Add rate limiting (respect API limits)
- Implement error handling and logging
- Write integration tests (mock poe.ninja responses)

**Acceptance Criteria:**

- [ ] Can fetch economy snapshots for PoE1 leagues
- [ ] Can fetch economy snapshots for PoE2 leagues
- [ ] Can fetch build ladder data for both games
- [ ] Rate limiting prevents API abuse
- [ ] Failed requests retry with exponential backoff
- [ ] Integration tests cover success and error cases

**poe.ninja API Endpoints:**

- `https://poe.ninja/api/data/CurrencyOverview?league=X&type=Currency`
- `https://poe.ninja/api/data/ItemOverview?league=X&type=UniqueArmour`
- `https://poe.ninja/api/data/ItemOverview?league=X&type=DivinationCard`
- (Similar for PoE2, different base URL)

______________________________________________________________________

#### Epic 1.3: Canonical Schemas (10-12 hours)

**Tasks:**

- Define canonical `Item` model (SQLAlchemy)
- Define canonical `Modifier` model
- Define canonical `League` model
- Define canonical `Currency` model
- Add Pydantic schemas for API responses
- Create database migrations
- Document schema design decisions

**Acceptance Criteria:**

- [ ] Item model supports both PoE1 and PoE2 items
- [ ] Modifier model handles affixes, implicits, enchants
- [ ] League model tracks active leagues per game
- [ ] Currency model stores chaos equivalents
- [ ] Database migrations apply cleanly
- [ ] API responses use Pydantic schemas

**Item Model (Example):**

```python
class Item(Base):
    id: UUID
    game: Game  # poe1 or poe2
    name: str
    base_type: str
    item_class: str  # Armor, Weapon, etc.
    icon: str  # Image URL
    modifiers: List[Modifier]  # Relationship
    league: str
    chaos_value: float
    snapshot_date: datetime
```

______________________________________________________________________

#### Epic 1.4: Data Normalization (10-12 hours)

**Tasks:**

- Implement PoE1 normalizer (poe.ninja → canonical)
- Implement PoE2 normalizer (poe.ninja → canonical)
- Parse and categorize modifiers
- Calculate chaos equivalents
- Handle missing/invalid data gracefully
- Write unit tests for normalization logic

**Acceptance Criteria:**

- [ ] PoE1 poe.ninja data maps to canonical schema
- [ ] PoE2 poe.ninja data maps to canonical schema
- [ ] Modifiers are parsed and categorized correctly
- [ ] Chaos equivalents calculated using currency rates
- [ ] Invalid data is logged and skipped (doesn't crash)
- [ ] Unit tests cover edge cases

**Normalization Logic (Example):**

```python
def normalize_poe1_item(raw_item: dict) -> Item:
    return Item(
        game=Game.POE1,
        name=raw_item['name'],
        base_type=raw_item['baseType'],
        chaos_value=raw_item['chaosValue'],
        modifiers=parse_modifiers(raw_item.get('explicitModifiers', [])),
        ...
    )
```

______________________________________________________________________

#### Epic 1.5: Background Job System (8-10 hours)

**Tasks:**

- Configure ARQ worker
- Create daily snapshot fetch job
- Create 28-day retention cleanup job
- Add job monitoring (logs, metrics)
- Set up job scheduling (cron-like)
- Write tests for job execution

**Acceptance Criteria:**

- [ ] ARQ worker runs in Docker Compose
- [ ] Daily job fetches snapshots for all active leagues (PoE1 + PoE2)
- [ ] Cleanup job deletes snapshots older than 28 days
- [ ] Jobs log start/completion/errors
- [ ] Job scheduling works (daily at 2 AM UTC)
- [ ] Tests verify job execution logic

**Job Structure:**

```python
# backend/src/contexts/upstream/jobs/fetch_snapshots.py
async def fetch_daily_snapshots(ctx):
    for game in [Game.POE1, Game.POE2]:
        provider = get_provider(game)
        leagues = await provider.get_active_leagues()
        for league in leagues:
            snapshot = await provider.fetch_snapshot(league)
            await save_snapshot(snapshot)
```

______________________________________________________________________

#### Epic 1.6: Database Schema & Optimization (6-8 hours)

**Tasks:**

- Design partitioned snapshot tables (by date)
- Create indexes for common queries
- Implement materialized views for trend analysis
- Add foreign key constraints
- Write database migrations
- Test query performance

**Acceptance Criteria:**

- [ ] Snapshot tables partitioned by month
- [ ] Indexes speed up game/league/date queries
- [ ] Materialized view aggregates daily prices
- [ ] Foreign keys maintain referential integrity
- [ ] Migrations apply and rollback cleanly
- [ ] Common queries execute in \<100ms

**Partitioned Table (Example):**

```sql
CREATE TABLE poe1_snapshots (
    id UUID PRIMARY KEY,
    league VARCHAR NOT NULL,
    snapshot_date TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL
) PARTITION BY RANGE (snapshot_date);

CREATE TABLE poe1_snapshots_2025_11
    PARTITION OF poe1_snapshots
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

______________________________________________________________________

### Success Criteria

Phase 1 is complete when:

- ✅ Daily job fetches poe.ninja data for PoE1 and PoE2
- ✅ Data is normalized and stored in canonical schema
- ✅ 28-day retention policy is enforced
- ✅ API endpoints expose league and item data by game
- ✅ Database queries are performant (\<100ms for common queries)
- ✅ All tests pass (unit + integration)
- ✅ Job monitoring shows successful daily runs

### Estimated Effort

**Total:** 40-50 hours

**Breakdown:**

- Game Abstraction: 8-10 hours (20%)
- poe.ninja Integration: 12-15 hours (30%)
- Canonical Schemas: 10-12 hours (23%)
- Data Normalization: 10-12 hours (23%)
- Background Jobs: 8-10 hours (18%)
- Database Schema: 6-8 hours (14%)

______________________________________________________________________

## Phase 2: Market Intelligence

**Goal:** Provide unified economic and meta insights through a Market Dashboard and Meta Analyzer

**Duration:** 4-5 weeks (50-60 hours)

**Status:** Planned

**Dependencies:** Phase 1 complete

### Objectives

Build the data analysis and visualization layer that transforms raw market data into actionable insights for players. This phase delivers the foundation for all other features (Crafting, Deal Finder, Price Checker).

### Key Deliverables

1. **Market Dashboard UI**

   - Currency price trends (line charts)
   - Item price trends (filterable by category)
   - League economy summary
   - Game selector integration

1. **Market Intelligence API**

   - Trend analysis endpoints (7-day, 28-day)
   - Price prediction (simple moving average)
   - Volatility metrics
   - Top movers (gainers/losers)

1. **Meta Analyzer**

   - Build popularity tracking (from ladder data)
   - Item usage correlation with builds
   - Modifier prevalence on top gear
   - Underutilized item detection

1. **Data Visualization Components**

   - Time-series charts (recharts + shadcn/ui)
   - Tables with sorting/filtering
   - Price change indicators
   - Responsive design for mobile

### Epics

#### Epic 2.1: Market Intelligence Bounded Context (10-12 hours)

**Tasks:**

- Create `contexts/market/` structure
- Define domain models (Trend, PricePoint, Volatility)
- Implement repository pattern
- Create service layer (trend analysis, predictions)
- Add API routes

**Acceptance Criteria:**

- [ ] Bounded context follows hexagonal architecture
- [ ] Domain models represent market concepts
- [ ] Repository abstracts database queries
- [ ] Service layer contains business logic (no DB coupling)
- [ ] API routes expose market intelligence

______________________________________________________________________

#### Epic 2.2: Trend Analysis Engine (12-15 hours)

**Tasks:**

- Implement 7-day moving average
- Implement 28-day moving average
- Calculate price volatility (standard deviation)
- Identify top gainers/losers
- Detect price anomalies
- Add caching for expensive queries

**Acceptance Criteria:**

- [ ] Can calculate moving averages for any item/currency
- [ ] Volatility metrics are accurate
- [ ] Top movers endpoint returns ranked results
- [ ] Anomaly detection flags unusual price movements
- [ ] Queries are cached (1 hour TTL)

______________________________________________________________________

#### Epic 2.3: Market Dashboard UI (15-18 hours)

**Tasks:**

- Create Market Dashboard page
- Implement currency price chart (line chart)
- Implement item price chart (filterable by category)
- Add league selector dropdown
- Add date range selector
- Integrate with TanStack Query hooks
- Add loading/error states
- Make responsive for mobile

**Acceptance Criteria:**

- [ ] Dashboard shows currency trends for selected game
- [ ] Item price chart updates when category changes
- [ ] League selector filters data correctly
- [ ] Date range selector (7 days, 28 days, custom)
- [ ] Charts render smoothly with real data
- [ ] Mobile-friendly layout

______________________________________________________________________

#### Epic 2.4: Meta Analyzer (10-12 hours)

**Tasks:**

- Fetch build ladder data from poe.ninja
- Analyze build popularity trends
- Correlate item usage with build adoption
- Analyze modifier prevalence on top gear
- Surface underutilized items
- Create Meta Analyzer API endpoints

**Acceptance Criteria:**

- [ ] Can fetch and parse build ladder data
- [ ] Build popularity ranked by usage
- [ ] Item usage correlated with builds
- [ ] Modifier prevalence calculated for top 100 players
- [ ] Underutilized items flagged (high power, low adoption)

______________________________________________________________________

#### Epic 2.5: Visualization Components (8-10 hours)

**Tasks:**

- Install recharts library
- Create reusable LineChart component
- Create reusable BarChart component
- Create PriceTable component (sortable, filterable)
- Add tooltips and legends
- Style with PoE theme (dark mode)

**Acceptance Criteria:**

- [ ] LineChart component is reusable across features
- [ ] BarChart component supports custom data
- [ ] PriceTable supports sorting and filtering
- [ ] Tooltips show detailed data on hover
- [ ] Charts match PoE dark theme aesthetic

______________________________________________________________________

### Success Criteria

Phase 2 is complete when:

- ✅ Market Dashboard displays currency and item trends
- ✅ Users can filter by game, league, and date range
- ✅ Trend analysis calculates moving averages and volatility
- ✅ Meta Analyzer surfaces build popularity and item usage
- ✅ All charts are responsive and performant
- ✅ Data updates daily via Phase 1 ingestion pipeline

### Estimated Effort

**Total:** 50-60 hours

**Breakdown:**

- Market Context: 10-12 hours (20%)
- Trend Analysis: 12-15 hours (25%)
- Dashboard UI: 15-18 hours (30%)
- Meta Analyzer: 10-12 hours (20%)
- Visualization: 8-10 hours (15%)

______________________________________________________________________

## Phase 3: Crafting Assistant

**Goal:** Help players craft high-end items cost-effectively with step-by-step guidance

**Duration:** 4-5 weeks (50-60 hours)

**Status:** Planned

**Dependencies:** Phase 2 complete (market data for pricing)

### Objectives

Build a crafting optimization engine that analyzes pasted items, determines the most cost-effective crafting path, and integrates with market data to suggest when to buy vs. craft.

### Key Deliverables

1. **Item Parser**

   - Parse PoE1 item text (copy from game)
   - Parse PoE2 item text
   - Extract base type, modifiers, sockets, links
   - Validate item data

1. **Crafting Path Engine**

   - Generate crafting steps (fossil, essence, harvest, etc.)
   - Calculate expected cost per step
   - Compare multiple crafting paths
   - Suggest cheapest path to target modifiers

1. **Crafting Assistant UI**

   - Item paste input
   - Target modifier selection
   - Step-by-step crafting plan display
   - Cost breakdown (materials + expected tries)
   - Integration with Market Dashboard (live pricing)

1. **GGG Schema Integration**

   - Fetch GGG base item data
   - Fetch crafting rule exports
   - Map modifiers to crafting methods
   - Keep schemas updated with game patches

### Epics

#### Epic 3.1: Item Parser (12-15 hours)

**Tasks:**

- Research PoE1 item text format
- Research PoE2 item text format
- Implement regex-based parser
- Extract base type, rarity, modifiers, sockets
- Handle corrupted/mirrored items
- Write comprehensive tests (50+ item samples)

**Acceptance Criteria:**

- [ ] Can parse PoE1 item text correctly
- [ ] Can parse PoE2 item text correctly
- [ ] Extracts all relevant fields (base, mods, sockets, etc.)
- [ ] Handles edge cases (corrupted, synthesized, etc.)
- [ ] Tests cover diverse item types

______________________________________________________________________

#### Epic 3.2: GGG Schema Integration (10-12 hours)

**Tasks:**

- Fetch GGG base item schema
- Fetch GGG crafting rules schema
- Parse and store in database
- Create API endpoint to query schemas
- Set up auto-update job (weekly)

**Acceptance Criteria:**

- [ ] GGG schemas stored in database
- [ ] API exposes base items and crafting rules
- [ ] Weekly job updates schemas
- [ ] Schema versioning tracks game patches

______________________________________________________________________

#### Epic 3.3: Crafting Path Engine (15-18 hours)

**Tasks:**

- Define crafting methods (fossil, essence, harvest, etc.)
- Implement modifier weighting (tier, rarity)
- Calculate expected cost per method
- Generate multi-step crafting paths
- Compare paths and rank by cost-effectiveness
- Integrate market pricing from Phase 2

**Acceptance Criteria:**

- [ ] Engine generates valid crafting paths
- [ ] Cost calculation uses real market prices
- [ ] Multiple paths compared (fossil vs. essence vs. harvest)
- [ ] Path ranking prioritizes cost-effectiveness
- [ ] Handles complex targets (multiple desired mods)

______________________________________________________________________

#### Epic 3.4: Crafting Assistant UI (12-15 hours)

**Tasks:**

- Create Crafting Assistant page
- Add item paste textarea
- Display parsed item details
- Add target modifier selector
- Display step-by-step crafting plan
- Show cost breakdown (materials, expected tries)
- Integrate market pricing (live updates)

**Acceptance Criteria:**

- [ ] Users can paste item text
- [ ] Parsed item displays correctly
- [ ] Users can select target modifiers
- [ ] Crafting plan shows actionable steps
- [ ] Cost breakdown is accurate and up-to-date

______________________________________________________________________

### Success Criteria

Phase 3 is complete when:

- ✅ Users can paste items and get crafting recommendations
- ✅ Crafting paths use live market pricing
- ✅ Multiple paths compared (cheapest highlighted)
- ✅ Step-by-step instructions are clear and actionable
- ✅ Works for both PoE1 and PoE2 items

### Estimated Effort

**Total:** 50-60 hours

**Breakdown:**

- Item Parser: 12-15 hours (25%)
- GGG Schema: 10-12 hours (20%)
- Crafting Engine: 15-18 hours (30%)
- Assistant UI: 12-15 hours (25%)

______________________________________________________________________

## Phase 4: Deal Finder

**Goal:** Surface undervalued item upgrades based on character stat weights

**Duration:** 5-6 weeks (60-70 hours)

**Status:** Planned

**Dependencies:** Phase 2 complete (market data)

### Objectives

Build a character-aware upgrade discovery tool that imports Path of Building characters, extracts stat weights, queries the trade API for available items, and visualizes results on a "Power vs. Price" scatter plot.

### Key Deliverables

1. **Path of Building Integration**

   - Parse PoB XML exports (PoE1)
   - Parse PoB XML exports (PoE2)
   - Extract stat weights (DPS, EHP, resistances, etc.)
   - Display character summary

1. **Trade API Integration**

   - PoE1 trade API client
   - PoE2 trade API client
   - Build search queries from stat weights
   - Fetch listings for each equipment slot
   - Handle API rate limits

1. **Value Analysis Engine**

   - Calculate "power score" per item (weighted stats)
   - Calculate "value score" (power / price)
   - Identify outliers (undervalued items)
   - Rank items by value

1. **Deal Finder UI**

   - PoB import (file upload or paste)
   - Character summary display
   - Stat weight adjustment sliders
   - Power vs. Price scatter plot (recharts)
   - Item detail hover tooltips
   - Link to trade site for purchase

### Epics

#### Epic 4.1: Path of Building Integration (15-18 hours)

**Tasks:**

- Research PoB XML format (PoE1 and PoE2)
- Implement XML parser
- Extract character stats (DPS, EHP, resistances, etc.)
- Calculate stat weights from PoB config
- Create PoB import API endpoint
- Display character summary in UI

**Acceptance Criteria:**

- [ ] Can parse PoB XML for PoE1 characters
- [ ] Can parse PoB XML for PoE2 characters
- [ ] Stat weights extracted accurately
- [ ] API accepts PoB file upload or paste
- [ ] Character summary displays key stats

______________________________________________________________________

#### Epic 4.2: Trade API Integration (18-20 hours)

**Tasks:**

- Research PoE1 trade API
- Research PoE2 trade API
- Implement PoE1 trade client
- Implement PoE2 trade client
- Build search queries from stat weights
- Fetch item listings per equipment slot
- Handle rate limiting (respect GGG limits)
- Cache results (1 hour TTL)

**Acceptance Criteria:**

- [ ] Can query PoE1 trade API successfully
- [ ] Can query PoE2 trade API successfully
- [ ] Search queries filter by stat weights
- [ ] Listings fetched for all equipment slots
- [ ] Rate limiting prevents API abuse
- [ ] Results cached to reduce API calls

______________________________________________________________________

#### Epic 4.3: Value Analysis Engine (12-15 hours)

**Tasks:**

- Calculate power score (weighted sum of stats)
- Normalize prices (chaos equivalents)
- Calculate value score (power / price)
- Identify outliers (>2 std dev from median)
- Rank items by value score
- Add filters (budget, min power, etc.)

**Acceptance Criteria:**

- [ ] Power score reflects character stat priorities
- [ ] Prices normalized to chaos equivalents
- [ ] Value score identifies best deals
- [ ] Outliers flagged for user attention
- [ ] Filters allow budget constraints

______________________________________________________________________

#### Epic 4.4: Deal Finder UI (15-18 hours)

**Tasks:**

- Create Deal Finder page
- Add PoB import (file upload + paste)
- Display character summary (stats, current gear)
- Add stat weight adjustment sliders
- Implement Power vs. Price scatter plot (recharts)
- Add hover tooltips (item details)
- Link to trade site for purchase
- Add loading/error states

**Acceptance Criteria:**

- [ ] Users can import PoB builds
- [ ] Character summary is accurate
- [ ] Stat weight sliders update results in real-time
- [ ] Scatter plot shows all items (color by slot)
- [ ] Tooltips show full item details on hover
- [ ] Click item to open trade site listing

______________________________________________________________________

### Success Criteria

Phase 4 is complete when:

- ✅ Users can import PoB builds for PoE1 and PoE2
- ✅ Stat weights extracted and adjustable
- ✅ Trade API queries return relevant items
- ✅ Power vs. Price scatter plot identifies best deals
- ✅ Users can purchase items directly from trade site

### Estimated Effort

**Total:** 60-70 hours

**Breakdown:**

- PoB Integration: 15-18 hours (25%)
- Trade API: 18-20 hours (30%)
- Value Analysis: 12-15 hours (20%)
- Deal Finder UI: 15-18 hours (25%)

______________________________________________________________________

## Phase 5: Price Checker

**Goal:** Rapid, accurate item valuation to prevent costly mistakes

**Duration:** 3-4 weeks (40-50 hours)

**Status:** Planned

**Dependencies:** Phase 2 (Market Intelligence), Phase 3 (Item Parser)

### Objectives

Build a fast, accurate item pricing tool that analyzes pasted items, identifies valuable modifiers using Meta Analyzer data, and provides recommended listing prices with confidence intervals.

### Key Deliverables

1. **Valuation Engine**

   - Partial trade search (similar items)
   - Modifier value weighting (from Meta Analyzer)
   - Price range estimation (min, median, max)
   - Confidence intervals (based on sample size)

1. **Price Checker UI**

   - Item paste input (reuse from Crafting Assistant)
   - Instant price display (large, prominent)
   - Breakdown by modifier value
   - Similar items comparison table
   - Recommended listing price
   - Historical price trend (if available)

1. **Price Alerts** (Optional)

   - Save items to watchlist
   - Notify when price crosses threshold
   - Requires notification system (Phase 6?)

### Epics

#### Epic 5.1: Valuation Engine (15-18 hours)

**Tasks:**

- Build partial trade search (similar base + mods)
- Implement modifier weighting (from Meta Analyzer)
- Calculate price range (percentiles: 10th, 50th, 90th)
- Estimate confidence interval (based on sample size)
- Handle rare/unique items separately
- Add caching for common items

**Acceptance Criteria:**

- [ ] Trade search finds similar items
- [ ] Modifier weighting reflects meta value
- [ ] Price range covers 80% of listings
- [ ] Confidence interval shown (high/medium/low)
- [ ] Rare items handled with larger uncertainty

______________________________________________________________________

#### Epic 5.2: Price Checker UI (12-15 hours)

**Tasks:**

- Create Price Checker page
- Reuse item parser from Phase 3
- Display price estimate (large, prominent)
- Show modifier value breakdown
- Display similar items table
- Add recommended listing price
- Show historical trend (if available)

**Acceptance Criteria:**

- [ ] Users can paste item text
- [ ] Price estimate displays immediately
- [ ] Modifier breakdown explains valuation
- [ ] Similar items table shows comparisons
- [ ] Recommended price is actionable

______________________________________________________________________

#### Epic 5.3: Price History Integration (8-10 hours)

**Tasks:**

- Query market data from Phase 2
- Display 7-day price trend
- Highlight unusual price movements
- Add "good time to sell" indicator

**Acceptance Criteria:**

- [ ] Price history chart shows 7-day trend
- [ ] Unusual movements flagged (>20% change)
- [ ] Sell indicator suggests optimal timing

______________________________________________________________________

#### Epic 5.4: Testing & Refinement (5-7 hours)

**Tasks:**

- Test with 100+ real items
- Validate accuracy against actual sales
- Tune modifier weightings
- Improve edge case handling

**Acceptance Criteria:**

- [ ] Accuracy within 20% of actual sale price
- [ ] Edge cases handled gracefully
- [ ] Performance \<500ms per valuation

______________________________________________________________________

### Success Criteria

Phase 5 is complete when:

- ✅ Users can paste items and get instant prices
- ✅ Price estimates are accurate (within 20%)
- ✅ Modifier breakdown explains valuation
- ✅ Recommended listing price prevents underselling
- ✅ Works for both PoE1 and PoE2

### Estimated Effort

**Total:** 40-50 hours

**Breakdown:**

- Valuation Engine: 15-18 hours (35%)
- Price Checker UI: 12-15 hours (30%)
- Price History: 8-10 hours (20%)
- Testing: 5-7 hours (15%)

______________________________________________________________________

## Phase 6: Planner & Ops

**Goal:** Operational hardening, performance optimization, and advanced features

**Duration:** 4-5 weeks (50-60 hours)

**Status:** Planned

**Dependencies:** Phases 1-5 complete

### Objectives

Harden the application for production use, optimize performance, add advanced features, and prepare for potential public launch.

### Key Deliverables

1. **Performance Optimization**

   - Database query optimization (indexing, explain plans)
   - Frontend bundle optimization (code splitting, lazy loading)
   - API response caching (Redis)
   - CDN for static assets

1. **Monitoring & Alerting**

   - Prometheus metrics
   - Grafana dashboards
   - Error tracking (Sentry or similar)
   - Uptime monitoring

1. **Advanced Features**

   - User preferences (saved searches, favorites)
   - Export functionality (CSV, JSON)
   - Dark/light theme toggle
   - Keyboard shortcuts

1. **Security Hardening**

   - Rate limiting for public endpoints
   - Input validation and sanitization
   - SQL injection prevention audit
   - XSS prevention audit
   - CORS configuration

1. **Documentation & Onboarding**

   - User guide (how to use each feature)
   - Video tutorials
   - FAQ
   - Glossary of PoE terms

1. **Deployment Preparation** (if going public)

   - Multi-user authentication (JWT)
   - User database schema
   - Production Docker Compose config
   - NGINX reverse proxy
   - SSL certificates (Let's Encrypt)
   - Backup strategy
   - Disaster recovery plan

### Epics

#### Epic 6.1: Performance Optimization (12-15 hours)

**Tasks:**

- Analyze slow queries (EXPLAIN ANALYZE)
- Add database indexes
- Implement query result caching (Redis)
- Optimize frontend bundle (code splitting)
- Add lazy loading for heavy components
- Benchmark and validate improvements

**Acceptance Criteria:**

- [ ] 95th percentile API response time \<200ms
- [ ] Frontend bundle size \<500KB (gzipped)
- [ ] Time to Interactive \<2s
- [ ] Database queries \<50ms

______________________________________________________________________

#### Epic 6.2: Monitoring & Alerting (10-12 hours)

**Tasks:**

- Set up Prometheus metrics
- Create Grafana dashboards (API latency, error rate, job success)
- Integrate error tracking (Sentry)
- Set up uptime monitoring (UptimeRobot or similar)
- Configure alerts (email or Discord)

**Acceptance Criteria:**

- [ ] Metrics collected for all API endpoints
- [ ] Grafana dashboards show system health
- [ ] Errors tracked and grouped by type
- [ ] Alerts fire on critical issues (DB down, job failure)

______________________________________________________________________

#### Epic 6.3: Advanced Features (15-18 hours)

**Tasks:**

- User preferences (saved searches, favorites)
- Export functionality (CSV, JSON)
- Dark/light theme toggle
- Keyboard shortcuts (Cmd+K command palette)
- Bulk operations (compare multiple items)

**Acceptance Criteria:**

- [ ] Users can save searches and favorites
- [ ] Export works for all data views
- [ ] Theme toggle persists across sessions
- [ ] Keyboard shortcuts improve power user workflow

______________________________________________________________________

#### Epic 6.4: Security Hardening (8-10 hours)

**Tasks:**

- Add rate limiting (per IP, per endpoint)
- Audit input validation (Pydantic schemas)
- Run SQL injection scanner
- Run XSS scanner
- Configure CORS properly
- Add security headers (CSP, HSTS)

**Acceptance Criteria:**

- [ ] Rate limiting prevents abuse
- [ ] All inputs validated with Pydantic
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Security headers pass Mozilla Observatory scan

______________________________________________________________________

#### Epic 6.5: Documentation & Onboarding (8-10 hours)

**Tasks:**

- Write user guide (one page per feature)
- Create video tutorials (screen recordings)
- Write FAQ
- Create glossary of PoE terms
- Add in-app tooltips and help text

**Acceptance Criteria:**

- [ ] User guide covers all features
- [ ] Video tutorials demonstrate key workflows
- [ ] FAQ answers common questions
- [ ] Glossary defines PoE-specific terms

______________________________________________________________________

#### Epic 6.6: Deployment Preparation (Optional, 10-12 hours)

**Tasks:**

- Set up multi-user authentication (JWT)
- Create user database schema
- Configure production Docker Compose
- Set up NGINX reverse proxy
- Obtain SSL certificates
- Configure backups (daily DB snapshots)
- Write disaster recovery plan

**Acceptance Criteria:**

- [ ] Users can register and log in
- [ ] Production deployment documented
- [ ] SSL certificates auto-renew
- [ ] Daily backups to S3/MinIO
- [ ] Recovery plan tested

______________________________________________________________________

### Success Criteria

Phase 6 is complete when:

- ✅ Application is performant (API \<200ms, TTI \<2s)
- ✅ Monitoring dashboards show system health
- ✅ Security audit passes (no major vulnerabilities)
- ✅ User documentation is comprehensive
- ✅ (Optional) Application is ready for public deployment

### Estimated Effort

**Total:** 50-60 hours

**Breakdown:**

- Performance: 12-15 hours (23%)
- Monitoring: 10-12 hours (20%)
- Advanced Features: 15-18 hours (28%)
- Security: 8-10 hours (16%)
- Documentation: 8-10 hours (16%)
- Deployment (Optional): 10-12 hours

______________________________________________________________________

## Summary: Roadmap Timeline

| Phase       | Goal                | Duration        | Effort            |
| ----------- | ------------------- | --------------- | ----------------- |
| **Phase 0** | Template Baseline   | 2-3 weeks       | 19-25 hours       |
| **Phase 1** | Upstream Foundation | 3-4 weeks       | 40-50 hours       |
| **Phase 2** | Market Intelligence | 4-5 weeks       | 50-60 hours       |
| **Phase 3** | Crafting Assistant  | 4-5 weeks       | 50-60 hours       |
| **Phase 4** | Deal Finder         | 5-6 weeks       | 60-70 hours       |
| **Phase 5** | Price Checker       | 3-4 weeks       | 40-50 hours       |
| **Phase 6** | Planner & Ops       | 4-5 weeks       | 50-60 hours       |
| **Total**   | -                   | **25-32 weeks** | **310-375 hours** |

**At 10 hours/week:** ~31-38 weeks (~7-9 months)
**At 20 hours/week:** ~16-19 weeks (~4-5 months)

______________________________________________________________________

## Prioritization Framework

When deciding what to work on, prioritize tasks by:

1. **Dependency:** Does another feature need this?
1. **Impact:** How much value does this deliver to users?
1. **Effort:** How much time will this take?
1. **Risk:** Is this blocking or high-uncertainty?

**High Priority = High Impact + Low Effort + High Dependency**

______________________________________________________________________

## Open Questions & Future Considerations

### Short-term (Phases 1-3)

- Should we support PoE1 and PoE2 equally, or prioritize one?
- How do we handle league transitions (mid-league, end-of-league)?
- Do we need a separate analytics warehouse, or is PostgreSQL sufficient?

### Medium-term (Phases 4-5)

- Should we support account-based character imports (GGG OAuth)?
- Do we integrate with trade sites directly, or just link to them?
- How do we monetize (freemium, subscription, donations)?

### Long-term (Phase 6+)

- Should we support mobile apps (React Native)?
- Do we extract bounded contexts into microservices?
- Should we build a public API for third-party developers?

______________________________________________________________________

## Resources

- [PRODUCT.md](PRODUCT.md) - Product vision and roadmap
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [CONTRIBUTING.md](CONTRIBUTING.md) - Developer workflow
- [SPRINT.md](SPRINT.md) - Current sprint (Phase 0) tasks

______________________________________________________________________

**Last Updated:** 2025-11-17
**Product Owner:** TBD
**Status:** Planning
