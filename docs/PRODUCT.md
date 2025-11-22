# Product Overview: Path of Mirrors

## Vision

**To be the ultimate tool for Path of Exile players who want to master the in-game economy and build powerful characters efficiently.**

Path of Mirrors empowers players to "get rich" in Path of Exile by providing data-driven insights and tools that automate and optimize complex economic and crafting decisions. The application transforms the overwhelming complexity of PoE's economy into actionable intelligence.

## Mission

Empower Path of Exile players to move beyond the standard gameplay loop of "farming maps" and engage profitably in crafting, trading, and market speculation—saving time while dramatically increasing in-game wealth.

## Target Users

The primary user is a **sophisticated Path of Exile player** who:

- Understands the game's complex economic and crafting systems
- Wants to optimize their time and currency generation
- Currently lacks the tools to master market dynamics
- Is ready to make data-driven decisions about character builds, item acquisition, and wealth accumulation

## Problem Statement

Path of Exile players face significant friction in economic activities:

- **Inefficient Crafting:** Determining the most cost-effective crafting path for high-end items is complex and time-consuming
- **Difficult Upgrade Discovery:** Finding best value-for-money item upgrades on the trade site requires tedious manual analysis
- **Market Opacity:** Spotting and capitalizing on economic trends (build popularity, currency fluctuations) is nearly impossible without sophisticated tooling
- **Costly Valuation Errors:** Accidentally selling valuable items for low prices is a common and frustrating experience

## Core Features (Roadmap)

Path of Mirrors will deliver four interconnected capabilities that transform player economics:

**Note:** Phase 6 (Planner & Ops) anchors operational hardening. The list below focuses on the four player-facing feature phases (2‑5) that define the core product experience.

### Phase 2 – Market Intelligence

**Goal:** Provide unified economic and meta insights that power downstream decisions

#### Market Dashboard

- **Economic Trend Analysis:** Track price fluctuations of currencies, crafting materials, and economy items over time
- **Meta Build Analysis:** Monitor popular and powerful builds in current leagues
- Enable informed investment and crafting decisions based on trend data

#### Meta Analyzer

- Track build popularity trends within the current league
- Monitor item usage and price correlations with build adoption
- Analyze modifier prevalence on top-ranking player gear
- Surface powerful, under-utilized items or strategies

**Status:** Phase 2 – Core capability providing data foundation for all other features

### Phase 3 – Crafting Assistant

**Goal:** Help players craft high-end items cost-effectively

- Analyze pasted items to determine optimal crafting paths
- Provide step-by-step crafting instructions with current market pricing
- Suggest when to purchase partially-crafted intermediates vs. continuing to craft
- Integrate with Market Intelligence to proactively suggest profitable craft opportunities
- **Status:** Phase 3 – Planned after Market Intelligence foundation

### Phase 4 – Deal Finder

**Goal:** Surface undervalued item upgrades based on character needs

- Integrate with Path of Building (PoB) to extract character stat weights
- Query trade API with weighted stat priorities
- Visualize items on a "Power vs. Price" scatter plot
- Identify investment opportunities based on Market Dashboard trend analysis
- **Status:** Phase 4 – Depends on PoB bridge implementation

### Phase 5 – Price Checker

**Goal:** Rapid, accurate item valuation to prevent costly mistakes

- Paste-to-price workflow with confidence intervals
- Identify most valuable modifiers using Meta Analyzer data
- Execute partial trade searches to determine price sensitivity
- Provide recommended listing prices with market justification
- **Status:** Phase 5 – Depends on Market Intelligence + Crafting Assistant foundations

## Success Metrics

Path of Mirrors success is measured by delivering tangible value to players:

- **Time Saved:** Demonstrably reduce time spent on manual trade searches, crafting research, and market analysis
- **Currency Earned:** Measurable increase in player in-game wealth through better crafting, trading, and investment decisions
- **User Engagement:** Active usage across multiple features per session, indicating deep integration into player workflows

## Technical Foundation

### Phase 0 – Template Baseline (Target)

The project will start with a **full-stack template baseline** that establishes architectural patterns and development workflows:

- **Backend:** FastAPI (Python) with SQLAlchemy 2.0, structured as bounded contexts following hexagonal architecture
- **Frontend:** React 18 + shadcn/ui + Tailwind CSS with OpenAPI-generated client and game selector component (PoE1/PoE2)
- **Database:** PostgreSQL 17 with Alembic migrations
- **Package Management:** uv (Python), npm (Node)
- **Background Jobs:** Redis + ARQ for async task queue
- **Auth:** Single-user local runtime (no authentication required)
- **Infrastructure:** Docker Compose with Traefik reverse proxy and hot-reload development workflow
- **Testing:** pytest (backend) + Vitest + React Testing Library (frontend) with CI pipeline
- **Observability:** Structured logging (structlog), health/readiness endpoints, request tracing
- **Validation:** Dummy placeholder CRUD entity to prove the full stack works (not PoE-specific)

This establishes the foundation for building Path of Mirrors features with proper testing, observability, and architectural patterns from day one.

**For detailed tech stack rationale and architectural patterns, see [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).**

### Target Architecture (Phases 1-6)

Path of Mirrors will evolve into a **modular monolith** with hexagonal architecture:

- **Backend:** Bounded contexts for each major capability (Crafting, Market Intelligence, Deal Finder, etc.)
- **Game Abstraction:** Unified interface with pluggable adapters for PoE1 and PoE2 (separate schemas, APIs, and datasets)
- **Data Strategy:**
  - PostgreSQL as the single store for transactional data and near-term analytics, using materialized views and aggregates for trend queries
  - 28-day rolling window retention for economic snapshots and trend analysis
  - Object storage for raw upstream snapshots and replayability (TBD in Phase 1)
  - Dedicated analytics warehouse (e.g., DuckDB/Parquet) deferred until data scale demands it
- **Integrations:**
  - poe.ninja (economy snapshots, build ladders) for both PoE1 and PoE2
  - Path of Exile Trade API (live listings, searches) for both games
  - Path of Building (character imports, stat weights)
  - GGG schema exports (base items, crafting rules) for both games

## Current Development Status

**Phase 0 (Next):** Template Baseline

- FastAPI backend with bounded context folder structure (hexagonal architecture pattern)
- React 18 frontend with shadcn/ui + Tailwind CSS and game selector component
- PostgreSQL 17 database with SQLAlchemy 2.0
- Redis + ARQ for background job queue
- Docker Compose development environment with hot-reload (`docker compose watch`)
- Full test infrastructure (pytest + Vitest + React Testing Library + CI pipeline)
- Structured logging and observability (structlog, health/readiness endpoints)
- Dummy placeholder CRUD entity to validate the full stack (not PoE-specific yet)
- Starting point: [benavlabs/fastapi-boilerplate](https://github.com/benavlabs/fastapi-boilerplate)

**Phase 1 (Planned):** Upstream Foundation

- **Game abstraction layer:** Support both PoE1 and PoE2 from the start with pluggable game-specific adapters
- Implement league provider for both games (separate endpoints, unified interface)
- Build modifier ingestion pipeline with game-specific normalization
- Create canonical schemas for items and builds (shared abstractions, game-specific extensions)
- Integrate with poe.ninja APIs for both PoE1 and PoE2 datasets
- 28-day rolling window data retention for trend analysis
- **TBD:** Object storage for raw snapshots vs PostgreSQL-only archival approach

**Upcoming Work:** See [`docs/BACKLOG.md`](BACKLOG.md) for Phases 2-6 (Market Intelligence → Crafting Assistant → Deal Finder → Price Checker → Planner & Ops).

## User Journeys (Vision)

**Note:** These journeys describe the target experience once all phases are complete.

### New Player Onboarding

1. Clone repo → set up `.env` → run `docker compose watch`
1. Explore pre-populated league and economy data
1. Paste first item into Price Checker for instant valuation
1. Browse Market Dashboard to understand current economic trends

### Crafting Power User

1. Identify target item for current build
1. Use Crafting Assistant to generate optimal crafting plan
1. Cross-reference intermediate steps with Deal Finder for purchase opportunities
1. Track progress and costs against Market Dashboard price movements

### Market Speculator

1. Monitor Meta Analyzer for emerging build popularity trends
1. Use Deal Finder to identify underpriced items in trending categories
1. Set alerts in Market Dashboard for price movement triggers
1. Validate purchase decisions with Price Checker before committing currency

### Upgrade Items (Deal Finder Core Flow)

1. **Load Character:** Import character from Path of Building (PoE1 or PoE2)
1. **Analyze Weights:** Deal Finder queries PoB to extract stat weights and optimization focus (EHP, damage, etc.)
1. **Adjust Priorities:** Player reviews and adjusts stat weights based on their preferences (prioritize survivability vs. DPS, etc.)
1. **Search Trade Site:** Deal Finder queries the respective game's trade site (PoE1 or PoE2) for available items in each equipment slot
1. **Value Analysis:** Results displayed on "Power vs. Price" scatter plot using median prices to identify best value-for-money upgrades
1. **Make Decision:** Player selects undervalued items and purchases directly from trade site

## Architectural Principles

Path of Mirrors is built following these design principles:

1. **Feature-aligned bounded contexts** – Each capability owns its domain language and lifecycle
1. **Hexagonal isolation** – Domain cores depend only on ports; adapters are swappable
1. **Game abstraction layer** – Unified interface with pluggable adapters for PoE1 and PoE2
1. **Canonical schemas everywhere** – Shared schemas generate Python/TypeScript bindings across backend and frontend
1. **Observability baked in** – Structured logging, health probes, request tracing from day one
1. **Evolutionary modularity** – Clear seams enable future service extraction if needed

These principles guide development from Phase 0 onward.

**For detailed architecture, tech stack rationale, and design patterns, see [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).**

## UX/UI Principles

- **Clarity and Efficiency:** The UI must present complex data in a clear, intuitive, and actionable way. User workflows should be optimized for speed and efficiency.
- **Game Context Switching:** A persistent game selector (PoE1/PoE2) allows users to seamlessly switch between games, with all features operating on the selected game's data context.
- **Responsive Design:** The application will be fully responsive, providing a seamless experience on both desktop and mobile devices.
- **Accessibility:** We will strive to meet WCAG 2.1 AA standards to ensure the tool is usable by as many players as possible.
- **Consistency:** A consistent design language and component library (based on Chakra UI) will be used across all features to create a cohesive user experience.

## Go-to-Market Strategy

This section is a placeholder for the go-to-market strategy, which will be developed during Phase 2. Initial thoughts include:

- **Community Engagement:** Announce the project and gather feedback from alpha testers on relevant subreddits (e.g., r/pathofexile, r/poebuilds) and Discord communities.
- **Content Creation:** Develop blog posts and video tutorials showcasing how to use the tool to achieve specific economic goals in-game.
- **Phased Rollout:** Invite users in waves, starting with a small group of sophisticated players to gather high-quality feedback before a public launch.

## Monetization Strategy

This section is a placeholder. A formal monetization strategy will be defined during Phase 2. The leading approach is a **freemium model**:

- **Free Tier:** Core features like the Price Checker and a limited version of the Market Dashboard will be available to all users to provide immediate value.
- **Premium Tier:** Advanced features like the Crafting Assistant, the full Deal Finder, historical data analysis, and real-time alerts would be part of a subscription tier. This model ensures the project is sustainable while keeping it accessible.

## Legal and Compliance

- **Terms of Service:** The project will operate in good faith and make every effort to comply with the Terms of Service of all third-party data sources, including Grinding Gear Games (GGG) and poe.ninja. A formal review of these terms is a prerequisite for the implementation of any new integration.
- **No Automation:** As stated in the "Non-Goals," this tool will **never** perform automated in-game actions, access user accounts, or otherwise interact with the game client. It is a purely informational and analytical tool.
- **Data Privacy:** User data (email, password) will be handled securely. No in-game account information is ever stored.

## Roadmap Links

- **Current Sprint:** [`docs/SPRINT.md`](SPRINT.md) (detailed task tracking)
- **Backlog:** [`docs/BACKLOG.md`](BACKLOG.md) (upcoming work by phase)
- **Architecture Decisions:** `docs/adr/` (accepted decisions)
- **Glossary:** [`docs/GLOSSARY.md`](GLOSSARY.md) (shared domain language)

## Non-Goals

- **No automation/botting:** Path of Mirrors does NOT perform automated in-game actions (e.g., auto-buying items). All actions are user-initiated.
- **No build editor:** Full-fledged build planning lives in Path of Building; we integrate with it rather than replace it.
- **No account access:** The application reads public trade/ladder data and PoB exports; it never accesses player accounts directly.

## Open Questions

- **Snapshot Archival Strategy (Phase 1):** Should raw poe.ninja snapshots be stored in object storage (S3/MinIO) for replayability, or is PostgreSQL-only sufficient for the 28-day rolling window?
- **OAuth Integration:** Should we support GGG/Steam OAuth for personalized features (stash tab scanning, character imports)?
- **Real-time Alerts:** Infrastructure requirements for push notifications on market opportunities?

## Contributing

Developers contributing to Path of Mirrors should:

1. Review [`docs/CONTRIBUTING.md`](CONTRIBUTING.md) for setup, testing, and PR guidelines
1. Consult [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) to understand system design and integration patterns
1. Check [`docs/SPRINT.md`](SPRINT.md) for current sprint goals and in-progress tasks
1. Reference this PRODUCT.md when proposing new features to ensure alignment with vision

______________________________________________________________________

Path of Mirrors transforms Path of Exile's economic complexity into player advantage. Every feature, from the Price Checker to the Crafting Assistant, serves the singular mission: **help players get rich and save time.**
