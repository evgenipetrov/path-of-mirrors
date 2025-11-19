# User Journey 2: Find All Upgrades for Build

**User Story:** "Show me all possible upgrades across all slots"

**Priority:** P1 (After MVP)

**Complexity:** Medium

**Database Required:** No (but caching recommended)

---

## User Flow

1. User navigates to "Full Build Analysis" page
2. User provides build (PoB XML/code)
3. System parses build and displays all equipped items
4. User optionally sets global filters:
   - Total budget (e.g., "200 chaos across all slots")
   - Minimum improvement threshold
5. User clicks "Analyze All Slots"
6. System:
   - Extracts all equipped items
   - Queries Trade API for each slot in parallel
   - Ranks all upgrades across all slots
7. User sees:
   - Current build summary
   - Table of all possible upgrades
   - Sorted by biggest improvement OR best value
   - Total cost for recommended upgrades

---

## Technical Architecture

### Frontend Components

```
frontend/src/routes/build-analysis/
├── index.tsx                    # Main page route
├── components/
│   ├── PoBInput.tsx             # Reused from Journey 1
│   ├── BuildSummary.tsx         # Show all current items
│   ├── BudgetAllocator.tsx      # Set budget per slot or total
│   ├── AllSlotsResults.tsx      # Master table of all upgrades
│   ├── SlotUpgradeCard.tsx      # Individual slot upgrade section
│   └── UpgradePath.tsx          # Optimal upgrade order
```

### Backend Components

```
backend/src/contexts/upgrades/
├── api/
│   └── routes.py                # POST /api/upgrades/analyze-all
├── services/
│   ├── pob_parser.py            # Reused from Journey 1
│   ├── trade_api_client.py      # Reused from Journey 1
│   ├── multi_slot_analyzer.py   # NEW: Orchestrate multi-slot queries
│   ├── budget_optimizer.py      # NEW: Allocate budget across slots
│   └── upgrade_path_planner.py  # NEW: Determine upgrade order
```

---

## API Contract

### Request

**Endpoint:** `POST /api/upgrades/analyze-all`

**Parameters:**

```python
{
  # Build source (one of):
  "pob_file": File,
  "pob_code": str,

  # Required:
  "game": str,
  "league": str,

  # Optional:
  "total_budget_chaos": float,     # e.g., 200.0 (distributed across slots)
  "budget_per_slot": dict,         # e.g., {"weapon": 50, "amulet": 30, ...}
  "min_improvement_score": float,  # Skip slots with low improvement potential
  "exclude_slots": list[str],      # e.g., ["weapon"] (already perfect)
}
```

### Response

```json
{
  "build_summary": {
    "name": "RF Juggernaut",
    "class": "Marauder",
    "level": 95,
    "total_life": 8500,
    "total_es": 0
  },
  "current_items": {
    "weapon": { "name": "...", "stats": {...} },
    "helmet": { "name": "...", "stats": {...} },
    // ... all slots
  },
  "slot_analysis": [
    {
      "slot": "amulet",
      "current_item": {...},
      "best_upgrade": {
        "item": {...},
        "improvement_score": 85.0,
        "price_chaos": 25.0,
        "value_ratio": 3.4
      },
      "upgrade_count": 15,          // Total upgrades found
      "budget_allocated": 30.0
    },
    {
      "slot": "ring1",
      "current_item": {...},
      "best_upgrade": {...},
      "upgrade_count": 22,
      "budget_allocated": 25.0
    }
    // ... all slots
  ],
  "recommended_path": [
    {
      "order": 1,
      "slot": "amulet",
      "item": {...},
      "reason": "Highest value ratio (3.4)"
    },
    {
      "order": 2,
      "slot": "ring1",
      "item": {...},
      "reason": "Second highest improvement (82.0)"
    }
    // ... ordered by priority
  ],
  "total_cost": 175.5,
  "total_improvement": 420.0,
  "query_time_ms": 4500
}
```

---

## Core Component Details

### 1. Multi-Slot Analyzer (`multi_slot_analyzer.py`)

**Purpose:** Coordinate upgrade searches across all equipment slots

```python
async def analyze_all_slots(
    build: Build,
    game: str,
    league: str,
    budget_per_slot: dict = None,
    min_improvement: float = 0
) -> dict:
    """Analyze all equipment slots for upgrades.

    Args:
        build: Parsed PoB build
        game: "poe1" or "poe2"
        league: League name
        budget_per_slot: Optional budget constraints per slot
        min_improvement: Skip slots with low improvement potential

    Returns:
        Dict with analysis for each slot
    """
    # Extract all equipped items
    equipped_items = extract_all_equipped_items(build)

    # Define all possible slots
    slots = [
        "weapon", "offhand", "helmet", "body_armour",
        "gloves", "boots", "amulet", "ring1", "ring2", "belt"
    ]

    # Query all slots in parallel
    tasks = []
    for slot in slots:
        if slot in equipped_items:
            max_price = budget_per_slot.get(slot) if budget_per_slot else None
            task = find_upgrades_for_slot(
                current_item=equipped_items[slot],
                slot=slot,
                game=game,
                league=league,
                max_price=max_price
            )
            tasks.append((slot, task))

    # Wait for all queries
    results = await asyncio.gather(*[task for _, task in tasks])

    # Aggregate results
    slot_analysis = []
    for (slot, _), upgrades in zip(tasks, results):
        if not upgrades:
            continue

        best_upgrade = upgrades[0]  # Already sorted by improvement
        if best_upgrade["improvement_score"] < min_improvement:
            continue

        slot_analysis.append({
            "slot": slot,
            "current_item": equipped_items[slot],
            "best_upgrade": best_upgrade,
            "upgrade_count": len(upgrades),
            "all_upgrades": upgrades[:10]  # Top 10 for this slot
        })

    return slot_analysis

async def find_upgrades_for_slot(
    current_item: dict,
    slot: str,
    game: str,
    league: str,
    max_price: float = None
) -> list[dict]:
    """Find upgrades for a specific slot.

    Reuses logic from Journey 1's upgrade finder.
    """
    # Build trade filters from current item
    filters = build_filters_from_item(current_item, slot)
    if max_price:
        filters["max_price_chaos"] = max_price

    # Query trade API
    candidates = await trade_api_client.search_items(game, league, filters)

    # Rank by improvement
    return upgrade_ranker.rank_upgrades(current_item, candidates)
```

---

### 2. Budget Optimizer (`budget_optimizer.py`)

**Purpose:** Distribute budget across slots for maximum improvement

```python
def allocate_budget(
    slot_analysis: list[dict],
    total_budget: float
) -> dict:
    """Allocate budget across slots to maximize total improvement.

    Uses greedy algorithm:
    1. Sort slots by value ratio (improvement per chaos)
    2. Allocate budget to highest value slots first
    3. Stop when budget exhausted or no more upgrades

    Args:
        slot_analysis: List of slot upgrade analyses
        total_budget: Total chaos budget

    Returns:
        Dict mapping slot → allocated budget
    """
    # Sort by value ratio
    sorted_slots = sorted(
        slot_analysis,
        key=lambda x: x["best_upgrade"]["value_ratio"],
        reverse=True
    )

    allocation = {}
    remaining_budget = total_budget

    for slot_data in sorted_slots:
        slot = slot_data["slot"]
        best_upgrade = slot_data["best_upgrade"]
        price = best_upgrade["price_chaos"]

        if price <= remaining_budget:
            allocation[slot] = price
            remaining_budget -= price
        else:
            # Can't afford this upgrade, skip
            continue

        if remaining_budget <= 0:
            break

    return allocation

def optimize_budget_allocation(
    slot_analysis: list[dict],
    total_budget: float,
    constraints: dict = None
) -> dict:
    """More sophisticated budget allocation with constraints.

    Constraints example:
    {
        "min_per_slot": 10.0,       # Don't allocate less than 10c to any slot
        "max_per_slot": 100.0,      # Cap per slot
        "priority_slots": ["weapon", "amulet"],  # Allocate to these first
        "reserve_budget": 50.0      # Reserve some budget
    }
    """
    # TODO: More sophisticated algorithm (dynamic programming?)
    pass
```

---

### 3. Upgrade Path Planner (`upgrade_path_planner.py`)

**Purpose:** Determine optimal order to purchase upgrades

```python
def plan_upgrade_path(
    slot_analysis: list[dict],
    budget_allocation: dict
) -> list[dict]:
    """Determine optimal order to upgrade items.

    Strategy:
    1. Prioritize high value ratio upgrades
    2. Consider budget constraints
    3. Account for stat synergies (optional)

    Args:
        slot_analysis: All slot upgrade options
        budget_allocation: Budget per slot

    Returns:
        Ordered list of upgrades to make
    """
    planned_upgrades = []

    for slot_data in slot_analysis:
        slot = slot_data["slot"]
        if slot not in budget_allocation:
            continue

        best_upgrade = slot_data["best_upgrade"]
        planned_upgrades.append({
            "slot": slot,
            "item": best_upgrade,
            "budget": budget_allocation[slot],
            "improvement": best_upgrade["improvement_score"],
            "value_ratio": best_upgrade["value_ratio"]
        })

    # Sort by priority (value ratio)
    planned_upgrades.sort(key=lambda x: x["value_ratio"], reverse=True)

    # Add order and reasoning
    for i, upgrade in enumerate(planned_upgrades):
        upgrade["order"] = i + 1
        upgrade["reason"] = get_upgrade_reason(upgrade, i)

    return planned_upgrades

def get_upgrade_reason(upgrade: dict, position: int) -> str:
    """Generate human-readable reason for upgrade priority."""
    if position == 0:
        return f"Best value (improvement/cost = {upgrade['value_ratio']:.1f})"
    elif upgrade["improvement"] > 100:
        return f"Large improvement ({upgrade['improvement']:.0f} points)"
    elif upgrade["budget"] < 20:
        return f"Low cost ({upgrade['budget']:.1f} chaos)"
    else:
        return f"Value ratio: {upgrade['value_ratio']:.1f}"
```

---

## Implementation Sequence

### Phase 1: Backend Extension
1. Implement multi-slot analyzer
2. Add parallel query execution
3. Implement budget optimizer (simple greedy algorithm)
4. Implement upgrade path planner
5. Create new API endpoint
6. Test with various builds

### Phase 2: Frontend
1. Create build analysis page
2. Reuse PoB input from Journey 1
3. Build all-slots results table
4. Add slot-by-slot breakdown
5. Show recommended upgrade path
6. Add budget allocation controls

### Phase 3: Optimization
1. Add request caching (same build = cached results)
2. Implement rate limiting for Trade API
3. Add retry logic for failed queries
4. Optimize parallel queries (connection pooling)

---

## Performance Considerations

**Challenge:** Querying 10 slots × 50 items = 500 items from Trade API

**Solutions:**

1. **Parallel queries** - Use asyncio to query all slots simultaneously
   - Expected time: ~5-10 seconds (vs 50+ seconds sequential)

2. **Result limits** - Only fetch top N items per slot
   - Default: 10-20 items per slot
   - Reduces API calls and processing time

3. **Caching** - Cache build analyses for 5-10 minutes
   - Same PoB code → return cached results
   - Significantly faster for repeated analyses

4. **Rate limiting** - Respect Trade API limits
   - Implement exponential backoff
   - Queue requests if needed

---

## User Experience Enhancements

### Visual Improvements
- Color-code slots by improvement potential (red/yellow/green)
- Show current vs upgraded stats side-by-side
- Highlight biggest upgrades
- Show cumulative cost as user selects items

### Interactive Features
- Toggle slots on/off
- Adjust budget per slot with sliders
- Filter by stat type (e.g., "only life upgrades")
- Save upgrade plans for later

### Smart Defaults
- Auto-detect build archetype (life vs ES vs hybrid)
- Suggest budget allocation based on current gaps
- Highlight "low-hanging fruit" (cheap, high-impact upgrades)

---

## Differences from Journey 1

| Aspect | Journey 1 | Journey 2 |
|--------|-----------|-----------|
| Scope | Single slot | All slots |
| Queries | 1 Trade API call | 10+ Trade API calls |
| Complexity | Low | Medium |
| Response time | 1-2 seconds | 5-10 seconds |
| Budget | Per-item | Total budget allocation |
| Optimization | Not needed | Budget optimizer, path planner |
| Caching | Optional | Recommended |

---

## Future Enhancements

1. **Synergy detection** - Identify item combinations that work well together
2. **Incremental upgrades** - Show step-by-step path from current to ideal
3. **Budget scenarios** - "What if I had 500 chaos vs 100 chaos?"
4. **Market timing** - "Wait for better deals on these slots"
5. **Upgrade alerts** - Notify when good upgrades appear on market

---

## Open Questions

1. **Should we analyze unique items differently?**
   - Uniques have fixed rolls, easier to compare
   - Could have curated upgrade paths for popular uniques

2. **How to handle influenced items?**
   - Elder/Shaper/Crusader/etc mods are powerful but rare
   - Might blow budget on one slot

3. **Should we consider corruptions?**
   - Corrupted items can't be modified further
   - But might be best-in-slot for budget

4. **What about crafting opportunities?**
   - Sometimes better to craft than buy
   - Out of scope for now, but worth considering

---

## Dependencies

**Same as Journey 1, plus:**
- Caching library (e.g., `redis` or `cachetools`)
- Connection pooling for Trade API queries
