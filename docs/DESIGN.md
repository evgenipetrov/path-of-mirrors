# Future Design: Path of Mirrors (Resource-Oriented)

This document outlines the proposed folder structure, component hierarchy, and API contracts for the upcoming phases of Path of Mirrors.

**Design Philosophy:**
- **Resource-Oriented:** Organized around core domain entities (Models) rather than transient user journeys.
- **Pure REST:** APIs expose resources (`/items`, `/prices`, `/builds`) allowing the frontend to compose features.
- **Stability:** Core models change rarely, whereas user journeys change frequently.
- **User-Defined Journeys:** We ship stable building blocks; journeys are client compositions and may change without requiring API changes.

## 1. Architectural Alignment

This design refines the Bounded Context definitions in `docs/ARCHITECTURE.md` while preserving the **Modular Monolith** and **Hexagonal Architecture** patterns.

Instead of 1:1 mapping between Features and Contexts, we use a **Compositional Approach**:

| Feature (User Journey) | Composed From Resources |
|------------------------|-------------------------|
| **Market Intelligence**| `Economy` (Prices) + `Catalog` (Items) |
| **Crafting Assistant** | `Catalog` (Recipes) + `Economy` (Costs) + `Analysis` (Sim) |
| **Deal Finder**        | `Builds` (Weights) + `Economy` (Prices) + `Analysis` (Scoring) |
| **Price Checker**      | `Economy` (History) + `Analysis` (Valuation) |

This separation allows "Business Logic" (Analysis) to evolve independently of "Data Ingestion" (Economy/Catalog).

---

## 2. Canonical Resource Contracts

Every resource must define its identifier strategy, scope, and invariants.

### 2.1. Catalog Context (Static Data)
**Scope:** Global (Game-specific, League-agnostic).
**Read/Write:** Read-only for users; Writable only by System (Ingestion).

| Resource | ID Strategy | Scope | Invariants |
|----------|-------------|-------|------------|
| `BaseItem` | `slug` (e.g. `poe1:tabula-rasa`) | Game | Immutable attributes. |
| `Modifier` | `slug` (e.g. `poe1:life-tier1`) | Game | Text must be parseable. |
| `Recipe` | `id` (UUID) | Game | Inputs must exist in Catalog. |

### 2.2. Economy Context (Market Data)
**Scope:** Game + League.
**Read/Write:** Read-only for users; Writable only by System (Ingestion).
**Freshness:** Prices < 4 hours old; History retained for 28 days.

| Resource | ID Strategy | Scope | Invariants |
|----------|-------------|-------|------------|
| `PriceSnapshot` | `id` (UUID) | Game, League | Must link to valid `BaseItem`. |
| `Currency` | `slug` (e.g. `chaos`) | Game | Exchange rates > 0. |
| `Trend` | `item_id` + `date` | Game, League | Monotonic time series. |

### 2.3. Builds Context (Player Data)
**Scope:** User-owned.
**Read/Write:** Read/Write by User.

| Resource | ID Strategy | Scope | Invariants |
|----------|-------------|-------|------------|
| `Build` | `id` (UUID) | User, Game | Must have valid character class. |
| `ItemSet` | `id` (UUID) | Build | Items must be valid for slot. |

### 2.4. Analysis Context (Computed)
**Scope:** Ephemeral / On-demand.
**Read/Write:** Read-only (Computation results).

| Resource | ID Strategy | Scope | Invariants |
|----------|-------------|-------|------------|
| `Valuation` | N/A (Response) | Request | Confidence score 0.0-1.0. |
| `CraftPlan` | N/A (Response) | Request | Steps must be valid recipes. |

---

### 2.5. Abstract Endpoint Map (stable building blocks)

**Catalog (read-only)**
- `GET /api/v1/catalog/base-items?game={g}&class={c}`
- `GET /api/v1/catalog/modifiers?game={g}&domain={d}`
- `GET /api/v1/catalog/recipes?game={g}&mechanic={m}`

**Economy (ingestion-owned)**
- `GET /api/v1/economy/prices?game={g}&league={l}&item_id=...`
- `GET /api/v1/economy/history?game={g}&league={l}&item_id=...`
- `GET /api/v1/economy/currencies?game={g}`

**Builds (user-owned)**
- `POST /api/v1/builds` (import PoB or manual)
- `GET /api/v1/builds/{id}`
- `GET /api/v1/builds/{id}/items`

**Analysis (computed, stateless)**
- `POST /api/v1/analysis/valuation` (item or recipe → value/score)
- `POST /api/v1/analysis/deals/search` (build + weights → ranked items)
- `POST /api/v1/analysis/crafting/simulate` (recipe + inputs → outcome)

Principle: these endpoints remain stable; journeys are just compositions of them.

---

## 3. Composable Journey Examples (illustrative only)

These are *examples*, not prescriptions. The goal is to show how stable resources compose into any journey users imagine.

1) **Single-Item Upgrade (stateless)**
   - POST `/api/v1/builds` (import PoB) → returns `build_id`
   - GET `/api/v1/economy/prices?item_class=amulet&game=poe1&league=settlers`
   - POST `/api/v1/analysis/deals/search` with `{ build_id, slot: "amulet", price_cap_chaos }`

2) **Crafting Profitability**
   - GET `/api/v1/catalog/recipes?mechanic=essence&game=poe2`
   - GET `/api/v1/economy/prices?ids=[...]&league=settlers`
   - POST `/api/v1/analysis/valuation` with `{ recipe_id, inputs, league }`

3) **Budget Planner**
   - GET `/api/v1/builds/{id}`
   - GET `/api/v1/economy/currencies?game=poe1`
   - POST `/api/v1/analysis/deals/search` with `{ build_id, budget_chaos, weights }`

These stay valid even if front-end journeys change, because the underlying resources remain stable.

---

## 4. Cross-Context Linking

To maintain loose coupling, contexts reference each other by **Natural Keys** or **Stable UUIDs**, never by database foreign keys.

- **Economy -> Catalog:** `PriceSnapshot` references `BaseItem` via `slug` (e.g., `poe1:headhunter`).
- **Builds -> Catalog:** `EquippedItem` references `BaseItem` via `slug`.
- **Analysis -> Economy:** `Valuation` references `PriceSnapshot` via `item_id` (UUID) or `slug` lookup.

**Resolution Strategy:**
- Frontend fetches `PriceSnapshot` from Economy.
- Frontend fetches `BaseItem` details from Catalog using `slug` from snapshot.
- No cross-context SQL joins.

---

## 5. API Shape & Evolution

### 5.1. Conventions
- **Versioning:** `/api/v1/...`
- **Pagination:** `?limit=50&offset=0` (Link headers for next/prev).
- **Filtering:** `?type=armour&min_price=10`
- **Sorting:** `?sort=-price` (descending).
- **Envelopes:** No success envelope (return raw JSON list/object).

### 5.3. Error & Auth Envelopes

**Error Response (RFC 7807):**
```json
{
  "type": "https://pathofmirrors.com/errors/resource-not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Item 'poe1:unknown' not found in catalog.",
  "instance": "/api/v1/catalog/items/poe1:unknown",
  "trace_id": "abc-123"
}
```

**Auth Context (Frontend):**
```typescript
// frontend/src/lib/auth.ts
interface AuthState {
  isAuthenticated: boolean;
  user: {
    id: string;
    permissions: string[];
  } | null;
  token: string | null;
}
```

---

## 6. Data Lifecycle

### 6.1. Ingestion (Economy)
- **Cadence:** Every 4 hours (via ARQ jobs).
- **Source:** poe.ninja API.
- **Retention:**
    - `PriceSnapshot`: Latest only (overwrite/update).
    - `PriceHistory`: Daily aggregates kept for 28 days.

### 6.2. Recomputation (Analysis)
- **Trigger:** On-demand (API call).
- **Caching:** Redis (TTL 15 mins for valuations).

---

## 7. Transition Plan (progress: scaffolding ✅)

We will migrate from the current structure to the target structure in stages.

### 7.1. Mapping

| Current Location | Target Location | Action |
|------------------|-----------------|--------|
| `src/contexts/upstream` | `src/contexts/economy/ingestion` | Move & Refactor |
| `src/contexts/core` | `src/contexts/catalog` | Split (Static data) |
| `src/contexts/core` | `src/contexts/builds` | Split (User data) |
| `src/contexts/upgrades` | `src/contexts/analysis/deals` | Move & Refactor |
| `src/contexts/placeholder` | N/A | Delete |

### 7.2. Concrete Execution Steps

1.  **Scaffold New Contexts:** ✅ done
    ```bash
    mkdir -p backend/src/contexts/{catalog,economy,builds,analysis}/{api,domain,services,adapters}
    touch backend/src/contexts/{catalog,economy,builds,analysis}/__init__.py
    ```

2.  **Migrate Core Domain:**
    - Move `Item`, `Modifier` -> `catalog/domain/models.py`
    - Move `Build` -> `builds/domain/models.py`
    - Move `Currency` -> `economy/domain/models.py`

3.  **Migrate Upstream (Ingestion):**
    - Move `upstream/adapters/poe_ninja` -> `economy/adapters/poe_ninja`
    - Move `upstream/services/ingestion` -> `economy/services/ingestion`

4.  **Migrate Upgrades (Analysis):**
    - Move `upgrades/services/ranker` -> `analysis/services/deal_finder.py`

5.  **Cleanup:**
    - Remove `src/contexts/core`, `src/contexts/upstream`, `src/contexts/upgrades`.
    - Update `main.py` to include new routers. ✅ routers wired to stubs

---

## 8. Frontend Consumption

### 7.1. Shared State
- **Game Context:** `useGame()` (Global).
- **League Context:** `useLeague()` (Global).

### 7.2. Feature Bindings

| Feature | Primary Query | Cache Key |
|---------|---------------|-----------|
| **Market** | `useGetPrices(game, league)` | `['prices', game, league]` |
| **Encyclopedia** | `useGetBaseItems(game)` | `['catalog', game]` |
| **Planner** | `useGetBuild(id)` | `['build', id]` |
| **Crafting** | `useGetRecipes(game)` | `['recipes', game]` |

---

## 9. Non-Goals

- **Full PoB Parity:** We will not replicate 100% of Path of Building's calculation engine. We rely on simplified models or external tools where possible.
- **Real-Time Trading:** We will not support live sniping or websocket-based trade feeds in the MVP.
- **Inventory Management:** We are not building a stash manager (yet).
