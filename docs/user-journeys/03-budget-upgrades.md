# User Journey 3: Find Budget Upgrades

**User Story:** "Show me upgrades under 50 chaos"

**Priority:** P1 (Enhancement of Journey 1)

**Complexity:** Low (extends Journey 1)

**Database Required:** No

---

## User Flow

1. User navigates to "Budget Upgrades" or uses Journey 1 with price filter
2. User provides build (PoB XML/code)
3. User sets budget constraint:
   - Max price per item (e.g., "50 chaos")
   - Total budget across selected slots (e.g., "200 chaos for 3 slots")
4. User optionally sets stat priorities:
   - "Prioritize life upgrades"
   - "Need more resistances"
5. System finds upgrades within budget, ranked by **value** (improvement per chaos)
6. User sees items sorted by best bang-for-buck

---

## Technical Architecture

### Key Difference from Journey 1

**Journey 1:** Rank by absolute improvement (best item, any price)

**Journey 3:** Rank by **value ratio** (improvement / price)

This is primarily a **sorting and filtering change**, not new architecture.

---

## API Contract

### Request

**Endpoint:** `POST /api/upgrades/find` (same as Journey 1)

**Additional Parameters:**

```python
{
  # ... same as Journey 1

  # Budget constraints:
  "max_price_chaos": float,          # e.g., 50.0
  "total_budget_chaos": float,       # e.g., 200.0 (for multi-slot)
  "price_weight": float,             # 0-1, how much to weight price (default: 0.5)

  # Stat priorities (optional):
  "stat_priorities": {
    "life": "high",                  # "low", "medium", "high", "required"
    "fire_res": "medium",
    "cold_res": "medium",
    // ...
  }
}
```

### Response

**Same structure as Journey 1, but:**

```json
{
  "upgrades": [
    {
      // ... all fields from Journey 1
      "value_ratio": 3.4,            // Highlighted: improvement / price
      "value_category": "excellent"  // "excellent", "good", "fair", "poor"
    }
  ],
  "budget_summary": {
    "max_budget": 50.0,
    "cheapest_upgrade": 5.0,
    "most_expensive": 50.0,
    "average_price": 25.3,
    "affordable_count": 15           // How many within budget
  }
}
```

---

## Core Component Changes

### 1. Enhanced Upgrade Ranker

**Modify `upgrade_ranker.py` from Journey 1:**

```python
def rank_upgrades(
    current_item: dict,
    candidate_items: list[dict],
    weights: dict = None,
    sort_by: str = "improvement"  # NEW: "improvement" or "value"
) -> list[dict]:
    """Rank candidate items.

    Args:
        sort_by:
            - "improvement": Sort by absolute improvement (Journey 1)
            - "value": Sort by improvement/price (Journey 3)
    """
    # ... existing logic to calculate improvements and scores

    # Calculate value ratio for all items
    for item in ranked:
        price = item["price_chaos"]
        if price > 0:
            item["value_ratio"] = item["improvement_score"] / price
            item["value_category"] = categorize_value(item["value_ratio"])
        else:
            item["value_ratio"] = float('inf')  # Free items!
            item["value_category"] = "free"

    # Sort by requested metric
    if sort_by == "value":
        ranked.sort(key=lambda x: x["value_ratio"], reverse=True)
    else:
        ranked.sort(key=lambda x: x["improvement_score"], reverse=True)

    return ranked

def categorize_value(value_ratio: float) -> str:
    """Categorize value ratio for UI display.

    Value ratio = improvement per chaos
    """
    if value_ratio >= 3.0:
        return "excellent"      # >3 improvement points per chaos
    elif value_ratio >= 2.0:
        return "good"
    elif value_ratio >= 1.0:
        return "fair"
    else:
        return "poor"
```

---

### 2. Smart Budget Filter

**New helper in `upgrade_ranker.py`:**

```python
def filter_by_budget(
    upgrades: list[dict],
    max_price: float = None,
    total_budget: float = None,
    min_value_ratio: float = None
) -> list[dict]:
    """Filter upgrades by budget constraints.

    Args:
        max_price: Max price per item
        total_budget: Total budget for all items (for multi-slot)
        min_value_ratio: Minimum value threshold

    Returns:
        Filtered list of affordable upgrades
    """
    filtered = upgrades

    # Filter by max price
    if max_price:
        filtered = [u for u in filtered if u["price_chaos"] <= max_price]

    # Filter by value ratio
    if min_value_ratio:
        filtered = [u for u in filtered if u["value_ratio"] >= min_value_ratio]

    # If total budget specified, select best items within budget
    if total_budget:
        filtered = select_within_budget(filtered, total_budget)

    return filtered

def select_within_budget(upgrades: list[dict], budget: float) -> list[dict]:
    """Select best upgrades within total budget using greedy algorithm.

    Assumes upgrades are sorted by value ratio (best first).
    """
    selected = []
    remaining_budget = budget

    for upgrade in upgrades:
        price = upgrade["price_chaos"]
        if price <= remaining_budget:
            selected.append(upgrade)
            remaining_budget -= price

    return selected
```

---

### 3. Stat Priority Weights

**Enhance weight calculation:**

```python
def calculate_stat_weights(
    stat_priorities: dict = None,
    build_type: str = None
) -> dict:
    """Calculate stat weights based on user priorities.

    Args:
        stat_priorities: User-specified priorities
            e.g., {"life": "high", "fire_res": "required", ...}
        build_type: Auto-detected build type
            e.g., "life", "es", "hybrid"

    Returns:
        Dict of stat weights
    """
    # Start with defaults
    weights = get_default_weights()

    # Apply user priorities
    if stat_priorities:
        priority_multipliers = {
            "required": 10.0,
            "high": 3.0,
            "medium": 1.0,
            "low": 0.3,
            "ignore": 0.0
        }

        for stat, priority in stat_priorities.items():
            if stat in weights:
                multiplier = priority_multipliers.get(priority, 1.0)
                weights[stat] *= multiplier

    # Apply build type adjustments
    if build_type == "es":
        weights["energy_shield"] *= 2.0
        weights["life"] *= 0.5
    elif build_type == "life":
        weights["life"] *= 2.0
        weights["energy_shield"] *= 0.3

    return weights
```

---

## Frontend Enhancements

### Budget-Focused UI

```tsx
// Budget slider component
<BudgetSlider
  value={maxPrice}
  onChange={setMaxPrice}
  min={1}
  max={500}
  step={5}
  label="Max Price per Item"
  showChaosIcon={true}
/>

// Value indicator
<ValueBadge valueRatio={item.value_ratio} category={item.value_category}>
  {item.value_ratio.toFixed(1)}x value
</ValueBadge>

// Budget summary card
<BudgetSummary>
  <Stat label="Your Budget" value={`${maxPrice} chaos`} />
  <Stat label="Affordable Options" value={affordableCount} />
  <Stat label="Best Value" value={`${bestValueRatio}x`} />
  <Stat label="Avg Price" value={`${avgPrice} chaos`} />
</BudgetSummary>
```

### Stat Priority Selector

```tsx
<StatPrioritySelector
  stats={["life", "fire_res", "cold_res", "lightning_res"]}
  priorities={{
    life: "high",
    fire_res: "medium",
    // ...
  }}
  onChange={setPriorities}
/>

// Renders:
// Life:            [Ignore] [Low] [Medium] [High] [Required] ✓
// Fire Res:        [Ignore] [Low] [Medium] ✓ [High] [Required]
```

---

## Use Case Examples

### Example 1: SSF Player (Self-Found)

**Scenario:** Player found some chaos, wants best upgrades under 20c

**Input:**
- Build: RF Juggernaut
- Budget: 20 chaos per item
- Priority: Life > Resistances > Everything else

**Output:**
- 8 affordable upgrades found
- Best value: Rare ring with +70 life, 30% fire res for 12c (value ratio: 4.2)
- Total improvement if buying all: +180 life, +90% total res for 95 chaos

### Example 2: League Starter

**Scenario:** Day 3 of league, 50 chaos saved up

**Input:**
- Build: Lightning Arrow Deadeye
- Total budget: 50 chaos
- Priority: Life, movement speed, resistances

**Output:**
- Optimal purchases within 50c budget:
  1. Boots: 15c (+25% MS, +60 life)
  2. Amulet: 20c (+70 life, +50% total res)
  3. Ring: 12c (+55 life, +35% fire res)
- Total cost: 47c
- Total improvement: +190 life, +85% res, +25% MS

### Example 3: Resistance Capping

**Scenario:** Player needs to cap resistances, limited budget

**Input:**
- Build: Any
- Budget: 30 chaos total
- Priority: Fire res (required), Cold res (high), Lightning res (high)

**Output:**
- Focus on resistance items only
- Ignore life/damage upgrades
- Find 3 items that cap all res for 28 chaos

---

## Implementation Sequence

### Phase 1: Backend (Easy - extends Journey 1)
1. ✅ Add value ratio calculation to ranker
2. ✅ Add `sort_by` parameter
3. ✅ Implement budget filters
4. ✅ Add stat priority weights
5. ✅ Test with various budgets

### Phase 2: Frontend
1. ✅ Add budget slider
2. ✅ Add value ratio display
3. ✅ Add stat priority selector
4. ✅ Add budget summary card
5. ✅ Add "value" vs "improvement" sort toggle

---

## Key Metrics to Track

**For future optimization:**

1. **Price distribution** - What's the typical price range for upgrades?
2. **Value sweet spot** - What budget gives best value ratio?
3. **Stat priorities** - What do users prioritize most?
4. **Budget utilization** - Do users spend their full budget?

---

## Future Enhancements

### Smart Budget Allocation

```python
def suggest_budget_allocation(
    current_build: dict,
    total_budget: float
) -> dict:
    """Analyze build and suggest budget per slot.

    Logic:
    1. Identify weakest slots (lowest stats)
    2. Allocate more budget to weak slots
    3. Reserve some budget for expensive but important upgrades (weapon)
    """
    # Analyze current stats
    weak_slots = identify_weak_slots(current_build)

    # Allocate budget
    allocation = {}
    for slot in weak_slots:
        # More budget to weaker slots
        allocation[slot] = calculate_slot_budget(slot, total_budget, weakness_score)

    return allocation
```

### Price Alerts

"Notify me when a good value upgrade appears"

```python
# Save user preferences
alert = {
    "build_id": "user_build_123",
    "slot": "amulet",
    "max_price": 30.0,
    "min_value_ratio": 2.5,
    "min_life": 70,
    "min_total_res": 60
}

# Background job checks trade API periodically
# Sends notification when matching item found
```

---

## Differences from Journey 1 & 2

| Aspect | Journey 1 | Journey 2 | Journey 3 |
|--------|-----------|-----------|-----------|
| Focus | Best item | All slots | Best value |
| Sort by | Improvement | Improvement | Value ratio |
| Budget | Optional | Total budget | Per-item budget |
| Use case | Rich players | Mid-budget | League start, SSF |
| Complexity | Low | Medium | Low |

---

## Dependencies

**Same as Journey 1** - No new dependencies needed

This is primarily a UX and algorithm enhancement, not new infrastructure.
