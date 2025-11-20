# Sprint: User Journey 1 - Single Item Upgrade Finder (MVP)

**Sprint Duration:** 1-2 weeks (8-16 hours)
**Sprint Goal:** Ship end-to-end upgrade finder feature (PoB import → Trade API search → Ranked results)
**Phase:** Phase 0 → Phase 1 (First Production Feature)
**Status:** ACTIVE

---

## Why This Sprint Matters

**Strategic Pivot from Phase 1 Infrastructure:**

We're pivoting from bottom-up infrastructure (Epic 1.4: upstream ingestion) to **top-down vertical slice** (User Journey 1). This delivers:

✅ **Immediate user value** - Working feature in 1-2 weeks
✅ **Domain model validation** - Test models in production context
✅ **Faster feedback** - Users can validate core value proposition
✅ **Reduced risk** - No wasted effort on unused infrastructure

**User Story:** "I want to upgrade my amulet for my current build"

This is the **MVP feature** that validates the entire product concept:
- Users provide PoB build (XML or import code)
- System finds better items on Trade API
- Results ranked by improvement and value

---

## Current State

✅ **Phase 0 Complete:**
- Infrastructure: Docker, FastAPI, PostgreSQL, Redis
- Placeholder CRUD context (notes demo)
- Frontend: React 19, TanStack Router/Query, shadcn/ui
- High test coverage on placeholder context (not currently enforced at 100%)

✅ **Epic 1.3 COMPLETE (Domain Models):**
- **4 core domain models implemented:**
  - `Currency` (8 fields, 17 tests) ✅
  - `Modifier` (8 fields, 36 tests) ✅
  - `Item` (14 fields incl. base_type_id, 25 tests) ✅
  - `Build` (14 fields incl. pob_code, 22 tests) ✅
- Dozens of passing tests across models (coverage enforced via `uv run pytest` locally; CI still pending)
- **5 user journey documents** created:
  - Journey 1: Single Item Upgrade (MVP) - THIS SPRINT
  - Journey 2: All Slot Upgrades
  - Journey 3: Budget Upgrades
  - Journey 4: Flip Opportunities (requires DB + ML)
  - Journey 5: PoB Stat Deltas (requires PoB binary)
- Database migrations created and applied
- Validation scripts for all models

🎯 **Sprint Goal:**
Implement User Journey 1 end-to-end - from PoB import to ranked upgrade results

⏭️ **What Comes After:**
- User Journey 2 (All Slot Upgrades)
- User Journey 3 (Budget Upgrades)
- User Journey 4 (Flip Opportunities - requires Phase 1 upstream)

---

## Sprint Architecture

### Key Components (from Journey 1 Design Doc)

**Backend Services (current code paths):**
```
backend/src/contexts/upstream/
├── api/builds_routes.py         # POST /api/v1/builds/parse, /analyze
├── services/pob_parser.py       # Parse PoB XML/code → Build
├── services/trade_api_client.py # Query pathofexile.com/trade
├── services/stat_extractor.py   # Extract item stats for comparison
├── services/upgrade_ranker.py   # Rank items by improvement
└── domain/schemas.py            # Pydantic request/response models
```

**Frontend Components (current layout):**
```
frontend/src/features/upgrades/
├── UpgradeFinder.tsx            # Main feature shell
├── components/
│   ├── PoBInput.tsx             # File upload + paste code (tabs)
│   ├── BuildDisplay.tsx         # Display parsed build summary
```
Planned route wiring is not yet created under `frontend/src/routes`; hook up a route before user-facing delivery.

**Critical Insight:** NO database required initially - all stateless processing.

---

## Sprint Backlog

### Phase 1: Backend Core (Days 1-3)

#### Task 1.1: PoB Parser Service ⚙️
**Estimated:** 4 hours
**Priority:** P0 (critical path)

**Description:**
Implement service to parse Path of Building XML files and import codes into Build domain objects.

**Implementation Details:**

```python
# backend/src/contexts/upgrades/services/pob_parser.py

import base64
import zlib
import xml.etree.ElementTree as ET
from src.contexts.core.domain import Build, Item, Game

def parse_pob_xml(xml_content: str, game: Game) -> Build:
    """Parse PoB XML string into Build object."""
    tree = ET.fromstring(xml_content)
    build_elem = tree.find("Build")

    # Extract character info
    character_class = build_elem.get("className")
    level = int(build_elem.get("level"))
    ascendancy = build_elem.get("ascendClassName")

    # Extract items from ItemSet
    items = {}
    items_elem = tree.find("Items")
    if items_elem is not None:
        for slot_elem in items_elem.findall("Slot"):
            slot_name = slot_elem.get("name")
            item_data = parse_item_element(slot_elem)
            if item_data:
                items[slot_name] = item_data

    # Extract passive tree
    passive_tree = extract_passive_tree(tree)

    return Build(
        game=game,
        name=build_elem.get("buildName", "Unnamed Build"),
        character_class=character_class,
        level=level,
        ascendancy=ascendancy,
        items=items,
        passive_tree=passive_tree,
    )

def parse_pob_code(import_code: str, game: Game) -> Build:
    """Decode and parse PoB import code."""
    # 1. Base64 decode
    compressed = base64.b64decode(import_code)
    # 2. Decompress (zlib)
    xml_content = zlib.decompress(compressed).decode('utf-8')
    # 3. Parse XML
    return parse_pob_xml(xml_content, game)

def extract_item_from_slot(build: Build, slot: str) -> dict:
    """Get current item from specific equipment slot."""
    return build.items.get(slot)
```

**Deliverables:**
- [ ] Implement `parse_pob_xml()` function
- [ ] Implement `parse_pob_code()` function (base64 decode + zlib decompress)
- [ ] Implement `extract_item_from_slot()` helper
- [ ] Parse item text format (line-based) into structured dict
- [ ] Write 10+ unit tests with sample PoB files
- [ ] Handle edge cases (corrupted items, empty slots, missing fields)

**Dependencies:** `xml.etree.ElementTree`, `base64`, `zlib` (all stdlib)

---

#### Task 1.2: Trade API Client ⚙️
**Estimated:** 5 hours
**Priority:** P0 (critical path)

**Description:**
Implement async client to query pathofexile.com/trade API for item listings.

**Implementation Details:**

```python
# backend/src/contexts/upgrades/services/trade_api_client.py

import httpx
from typing import AsyncIterator

async def search_items(
    game: str,
    league: str,
    item_filters: dict
) -> list[dict]:
    """Search for items on trade API.

    Args:
        game: "poe1" or "poe2"
        league: League name (e.g., "Affliction", "Standard")
        item_filters: {
            "base_type": "Amulet",
            "min_life": 60,
            "max_price_chaos": 50,
            ...
        }

    Returns:
        List of item dicts with stats and prices
    """
    # 1. Build trade API query JSON
    query = build_trade_query(item_filters)

    # 2. POST to trade API search endpoint
    search_url = f"https://www.pathofexile.com/api/trade/search/{league}"
    async with httpx.AsyncClient() as client:
        response = await client.post(search_url, json=query)
        result_ids = response.json()["result"][:50]  # Top 50 results

    # 3. Fetch item details
    fetch_url = f"https://www.pathofexile.com/api/trade/fetch/{','.join(result_ids)}"
    async with httpx.AsyncClient() as client:
        items_response = await client.get(fetch_url)

    # 4. Parse and normalize items
    return [parse_trade_item(item) for item in items_response.json()["result"]]

def build_trade_query(filters: dict) -> dict:
    """Build trade API query JSON from filters."""
    return {
        "query": {
            "status": {"option": "online"},
            "type": filters["base_type"],
            "stats": [
                {"type": "and", "filters": [
                    {"id": "pseudo.pseudo_total_life", "value": {"min": filters.get("min_life")}}
                ]}
            ],
            "filters": {
                "trade_filters": {
                    "price": {"max": filters.get("max_price_chaos")}
                }
            }
        },
        "sort": {"price": "asc"}
    }

def parse_trade_item(item_data: dict) -> dict:
    """Parse trade API item response into normalized format."""
    item = item_data["item"]
    listing = item_data["listing"]

    return {
        "id": item["id"],
        "name": item["name"] or item["typeLine"],
        "base_type": item["baseType"],
        "rarity": item["rarity"],
        "stats": extract_stats_from_mods(item),
        "price_chaos": convert_price_to_chaos(listing["price"]),
        "account": listing["account"]["name"],
        "whisper": listing["whisper"],
        "trade_url": f"https://www.pathofexile.com/trade/search/{item['league']}"
    }
```

**Deliverables:**
- [ ] Implement async `search_items()` function
- [ ] Implement `build_trade_query()` with filter translation
- [ ] Implement `parse_trade_item()` response parser
- [ ] Handle rate limiting (exponential backoff)
- [ ] Write integration tests with mock responses
- [ ] Document Trade API query structure

**Dependencies:** `httpx` (already in dependencies)

---

#### Task 1.3: Stat Extractor Service ⚙️
**Estimated:** 3 hours
**Priority:** P0 (critical path)

**Description:**
Extract and normalize stats from items for comparison.

**Implementation Details:**

```python
# backend/src/contexts/upgrades/services/stat_extractor.py

import re
from decimal import Decimal

def extract_stats(item: dict) -> dict:
    """Extract numeric stats from item mods.

    Handles:
    - Life, ES, mana
    - Resistances
    - Attributes (str, dex, int)
    - Damage mods
    - Special mods (movement speed, rarity, etc.)
    """
    stats = {}

    for mod in item.get("explicit_mods", []):
        stat_type, value = parse_mod_text(mod)
        if stat_type:
            stats[stat_type] = stats.get(stat_type, 0) + value

    return stats

def parse_mod_text(mod_text: str) -> tuple[str, float]:
    """Parse mod text into (stat_type, value).

    Examples:
        "+72 to maximum Life" → ("life", 72)
        "+40% to Fire Resistance" → ("fire_res", 40)
        "15% increased Rarity of Items found" → ("item_rarity", 15)
    """
    patterns = {
        r"[+-]?(\d+) to maximum Life": ("life", 1),
        r"[+-]?(\d+)% to Fire Resistance": ("fire_res", 1),
        r"[+-]?(\d+)% to Cold Resistance": ("cold_res", 1),
        r"[+-]?(\d+)% to Lightning Resistance": ("lightning_res", 1),
        r"[+-]?(\d+) to Strength": ("strength", 1),
        r"[+-]?(\d+) to Dexterity": ("dexterity", 1),
        r"[+-]?(\d+) to Intelligence": ("intelligence", 1),
        # ... more patterns
    }

    for pattern, (stat_name, _) in patterns.items():
        match = re.search(pattern, mod_text)
        if match:
            return stat_name, float(match.group(1))

    return None, 0
```

**Deliverables:**
- [ ] Implement `extract_stats()` function
- [ ] Implement `parse_mod_text()` with regex patterns
- [ ] Support 20+ common stat types (life, res, attributes, etc.)
- [ ] Handle implicit and explicit mods
- [ ] Write 15+ unit tests for different mod formats
- [ ] Document supported stat types

---

#### Task 1.4: Upgrade Ranker Service ⚙️
**Estimated:** 4 hours
**Priority:** P0 (critical path)

**Description:**
Compare items and rank by improvement score.

**Implementation Details:**

```python
# backend/src/contexts/upgrades/services/upgrade_ranker.py

from decimal import Decimal

def rank_upgrades(
    current_item: dict,
    candidate_items: list[dict],
    weights: dict = None
) -> list[dict]:
    """Rank candidate items by improvement over current item.

    Args:
        current_item: Current equipped item stats
        candidate_items: List of items from trade API
        weights: Stat weights for scoring (optional)
            e.g., {"life": 1.0, "fire_res": 0.5, ...}

    Returns:
        Sorted list with improvement scores
    """
    if weights is None:
        weights = get_default_weights()

    ranked = []
    for item in candidate_items:
        improvements = calculate_improvements(current_item, item)
        score = calculate_weighted_score(improvements, weights)
        value_ratio = score / item["price_chaos"] if item["price_chaos"] > 0 else 0

        ranked.append({
            **item,
            "improvements": improvements,
            "improvement_score": score,
            "value_ratio": value_ratio
        })

    # Sort by improvement score (descending)
    return sorted(ranked, key=lambda x: x["improvement_score"], reverse=True)

def calculate_improvements(current: dict, candidate: dict) -> dict:
    """Calculate stat differences."""
    current_stats = current.get("stats", {})
    candidate_stats = candidate.get("stats", {})

    improvements = {}
    all_stats = set(current_stats.keys()) | set(candidate_stats.keys())

    for stat in all_stats:
        current_val = current_stats.get(stat, 0)
        candidate_val = candidate_stats.get(stat, 0)
        diff = candidate_val - current_val
        if diff != 0:
            improvements[stat] = diff

    return improvements

def calculate_weighted_score(improvements: dict, weights: dict) -> float:
    """Calculate weighted improvement score."""
    score = 0.0
    for stat, improvement in improvements.items():
        weight = weights.get(stat, 0.1)  # Default weight for unknown stats
        score += improvement * weight
    return score

def get_default_weights() -> dict:
    """Default stat weights for general builds."""
    return {
        "life": 1.0,
        "energy_shield": 0.8,
        "fire_res": 0.6,
        "cold_res": 0.6,
        "lightning_res": 0.6,
        "chaos_res": 0.4,
        "strength": 0.3,
        "dexterity": 0.3,
        "intelligence": 0.3,
        "item_rarity": 0.2,
        # ... more stats
    }
```

**Deliverables:**
- [ ] Implement `rank_upgrades()` function
- [ ] Implement `calculate_improvements()` diff calculator
- [ ] Implement `calculate_weighted_score()` with default weights
- [ ] Add value ratio calculation (improvement / price)
- [ ] Write 10+ unit tests with mock data
- [ ] Document weighting system

---

#### Task 1.5: API Endpoint ⚙️
**Estimated:** 2 hours
**Priority:** P0 (critical path)

**Description:**
Create FastAPI endpoint to wire up all services.

**Implementation Details:**

```python
# backend/src/contexts/upgrades/api/routes.py

from fastapi import APIRouter, UploadFile, File, Form
from src.contexts.upgrades.services import (
    pob_parser,
    trade_api_client,
    stat_extractor,
    upgrade_ranker
)
from src.contexts.upgrades.domain.schemas import (
    UpgradeFindRequest,
    UpgradeFindResponse
)

router = APIRouter(prefix="/api/upgrades", tags=["upgrades"])

@router.post("/find", response_model=UpgradeFindResponse)
async def find_upgrades(
    pob_file: UploadFile = File(None),
    pob_code: str = Form(None),
    item_slot: str = Form(...),
    game: str = Form(...),
    league: str = Form(...),
    max_price_chaos: float = Form(None),
    min_life: int = Form(None),
    min_resistance: int = Form(None)
):
    """Find upgrades for a specific item slot."""

    # 1. Parse PoB input
    if pob_file:
        xml_content = await pob_file.read()
        build = pob_parser.parse_pob_xml(xml_content.decode('utf-8'), game)
    elif pob_code:
        build = pob_parser.parse_pob_code(pob_code, game)
    else:
        raise ValueError("Must provide pob_file or pob_code")

    # 2. Extract current item from slot
    current_item = pob_parser.extract_item_from_slot(build, item_slot)

    # 3. Build filters from current item + user constraints
    filters = {
        "base_type": current_item["base_type"],
        "max_price_chaos": max_price_chaos,
        "min_life": min_life,
        "min_resistance": min_resistance,
    }

    # 4. Query Trade API
    candidate_items = await trade_api_client.search_items(game, league, filters)

    # 5. Extract stats from all items
    current_item["stats"] = stat_extractor.extract_stats(current_item)
    for item in candidate_items:
        item["stats"] = stat_extractor.extract_stats(item)

    # 6. Rank upgrades
    upgrades = upgrade_ranker.rank_upgrades(current_item, candidate_items)

    return UpgradeFindResponse(
        current_item=current_item,
        upgrades=upgrades,
        query_time_ms=...  # Add timing
    )
```

**Deliverables:**
- [ ] Create API route with multipart/form-data support
- [ ] Define Pydantic request/response schemas
- [ ] Wire up all 4 services
- [ ] Add error handling (invalid PoB, API failures)
- [ ] Write integration test for full flow
- [ ] Register route in `main.py`

---

### Phase 2: Frontend (Days 4-6)

#### Task 2.1: PoB Input Component 🎨
**Estimated:** 3 hours
**Priority:** P0 (critical path)

**Description:**
Create tabbed component for PoB XML upload and import code paste.

**Deliverables:**
- [ ] Create `PoBInput.tsx` with tabs (File Upload / Paste Code)
- [ ] File upload with `.xml` validation
- [ ] Textarea with PoB code validation (base64 check)
- [ ] Loading state during parse
- [ ] Error display for invalid input
- [ ] Use shadcn/ui Tabs component

---

#### Task 2.2: Build Summary Display 🎨
**Estimated:** 2 hours
**Priority:** P1 (nice-to-have)

**Description:**
Display parsed build info (class, level, key stats).

**Deliverables:**
- [ ] Create `CurrentBuild.tsx` component
- [ ] Show character class, level, ascendancy
- [ ] Show key stats (life, ES, resistances)
- [ ] Display all equipped items
- [ ] Use shadcn/ui Card component

---

#### Task 2.3: Item Slot Selector 🎨
**Estimated:** 1 hour
**Priority:** P0 (critical path)

**Description:**
Dropdown to select which equipment slot to upgrade.

**Deliverables:**
- [ ] Create `ItemSlotSelector.tsx` with dropdown
- [ ] Options: weapon, helmet, body armour, gloves, boots, amulet, ring1, ring2, belt
- [ ] Use shadcn/ui Select component
- [ ] Show current item preview

---

#### Task 2.4: Upgrade Filters 🎨
**Estimated:** 2 hours
**Priority:** P1 (nice-to-have)

**Description:**
Filters for price and minimum stat requirements.

**Deliverables:**
- [ ] Create `UpgradeFilters.tsx` component
- [ ] Max price slider (chaos)
- [ ] Min life input
- [ ] Min resistance input
- [ ] Use shadcn/ui Input and Slider components

---

#### Task 2.5: Results Table 🎨
**Estimated:** 4 hours
**Priority:** P0 (critical path)

**Description:**
Display ranked upgrades with sortable table.

**Deliverables:**
- [ ] Create `UpgradeResults.tsx` with TanStack Table
- [ ] Columns: Item Name, Stats, Improvements, Price, Value Ratio
- [ ] Sortable by all columns
- [ ] Stat comparison visualization (before/after)
- [ ] Trade whisper copy button
- [ ] Use shadcn/ui Table component

---

#### Task 2.6: Trade Whisper Component 🎨
**Estimated:** 1 hour
**Priority:** P1 (nice-to-have)

**Description:**
Button to copy Trade API whisper command.

**Deliverables:**
- [ ] Create `TradeWhisper.tsx` component
- [ ] Copy to clipboard functionality
- [ ] Toast notification on copy
- [ ] Use shadcn/ui Button and Toast

---

### Phase 3: Integration & Polish (Days 7-8)

#### Task 3.1: End-to-End Testing ✅
**Estimated:** 3 hours
**Priority:** P0 (quality gate)

**Deliverables:**
- [ ] Write Playwright E2E test for full user flow
- [ ] Test with real PoB file
- [ ] Test with PoB import code
- [ ] Verify results table renders
- [ ] Test filtering and sorting
- [ ] Validate Trade whisper copy

---

#### Task 3.2: Error Handling & Loading States 🎨
**Estimated:** 2 hours
**Priority:** P0 (UX)

**Deliverables:**
- [ ] Loading spinners for all async operations
- [ ] Error boundaries for component failures
- [ ] User-friendly error messages
- [ ] Empty state (no upgrades found)
- [ ] Network error handling

---

#### Task 3.3: Documentation 📝
**Estimated:** 2 hours
**Priority:** P1 (documentation)

**Deliverables:**
- [ ] Update README with usage instructions
- [ ] Add screenshots to docs
- [ ] Document API endpoint in OpenAPI
- [ ] Create demo video (optional)

---

## Success Criteria

**Sprint is complete when:**

- [ ] User can upload PoB XML or paste import code
- [ ] System parses build and displays current items
- [ ] User can select item slot to upgrade
- [ ] System queries Trade API and returns ranked results
- [ ] Results show stat improvements and value ratios
- [ ] User can copy Trade whisper command
- [ ] All tests passing (unit + integration + E2E)
- [ ] Feature deployed and accessible

**Quality Gates:**
- 80%+ test coverage for new code
- No P0 bugs
- API response time < 5 seconds
- Frontend renders within 100ms

---

## Out of Scope (Defer to Later)

The following are explicitly NOT in this sprint:

- ❌ Multi-slot analysis (Journey 2)
- ❌ Budget optimization (Journey 3)
- ❌ Database storage (stateless for MVP)
- ❌ User accounts / saved searches
- ❌ PoB stat delta calculations (Journey 5)
- ❌ Flip opportunity detection (Journey 4)

This sprint delivers **one vertical slice** - the core upgrade finder flow.

---

## Timeline

**Week 1: Backend (Days 1-3)**
- Day 1: PoB Parser + tests
- Day 2: Trade API Client + Stat Extractor
- Day 3: Upgrade Ranker + API Endpoint

**Week 2: Frontend (Days 4-6)**
- Day 4: PoB Input + Item Slot Selector
- Day 5: Results Table + Filters
- Day 6: Polish + Error Handling

**Week 3: Testing & Deploy (Days 7-8)**
- Day 7: E2E tests + Bug fixes
- Day 8: Documentation + Deploy

**Total Estimated Hours:** 8-16 hours (depends on experience with PoB format and Trade API)

---

## Next Sprint Preview

After Journey 1 ships, we can choose:

**Option A: Journey 2 (All Slot Upgrades)**
- Natural extension of Journey 1
- Multi-slot analyzer with budget allocation
- 1-2 weeks additional work

**Option B: Journey 3 (Budget Upgrades)**
- Primarily sorting/ranking changes
- Value ratio optimization
- 3-5 days additional work

**Option C: Upstream Ingestion (Epic 1.4)**
- poe.ninja adapter implementation
- Background job system
- Database schema for snapshots
- Required before Journey 4 (Flip Opportunities)

**Recommendation:** Ship Journey 2 or 3 first (compound user value), then pivot to Epic 1.4 for Journey 4.

---

## Resources

**User Journey Design:**
- `docs/user-journeys/01-single-item-upgrade.md` - Detailed feature spec

**Domain Models:**
- `backend/src/contexts/core/domain/item.py` - Item entity (25 tests passing)
- `backend/src/contexts/core/domain/build.py` - Build entity (22 tests passing)
- `backend/src/contexts/core/domain/modifier.py` - Modifier value object (36 tests passing)

**Sample Data:**
- `_samples/data/poe1/pob/` - Sample PoB builds
- `_samples/data/poe1/trade/` - Sample Trade API responses

**External APIs:**
- Trade API: https://www.pathofexile.com/developer/docs/reference
- PoB Format: https://github.com/PathOfBuildingCommunity/PathOfBuilding

---

## Epic 1.3 Completion Summary

**What Was Completed:**

✅ **4 Core Domain Models:**
- Currency (8 fields, 17 tests)
- Modifier (8 fields, 36 tests)
- Item (14 fields, 25 tests)
- Build (14 fields, 22 tests)

✅ **100 Passing Tests** - Full coverage with real examples

✅ **5 User Journey Documents:**
- Comprehensive feature specifications
- API contracts
- Component details
- Implementation sequences

✅ **Database Migrations:**
- All models migrated to production schema
- Indexes for performance
- Validation scripts

**What Was NOT Completed (Deferred):**

❌ Upstream ingestion (Epic 1.4) - Not needed for MVP
❌ Trade API adapter - Will implement for Journey 1
❌ poe.ninja adapter - Will implement for Journey 4
❌ Background job system - Not needed for stateless MVP

**Strategic Decision:**
Pivoted from infrastructure-first to feature-first approach. Validates domain models in production context before building unused infrastructure.
