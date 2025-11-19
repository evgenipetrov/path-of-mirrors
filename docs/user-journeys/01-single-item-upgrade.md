# User Journey 1: Find Single Item Upgrade

**User Story:** "I want to upgrade my amulet for my current build"

**Priority:** P0 (MVP - Start here)

**Complexity:** Low

**Database Required:** No

---

## User Flow

1. User navigates to "Upgrade Finder" page
2. User provides build via:
   - Upload PoB XML file, OR
   - Paste PoB import code (base64 string)
3. System parses build and displays current items
4. User selects item slot to upgrade (e.g., "Amulet")
5. User optionally sets filters:
   - Max price (e.g., "50 chaos")
   - Minimum stat improvements (e.g., "+20 life minimum")
6. User clicks "Find Upgrades"
7. System:
   - Extracts current item stats
   - Queries Trade API for similar items
   - Compares stats and ranks by improvement
8. User sees ranked list of upgrades with:
   - Item name and stats
   - Stat comparison (before/after)
   - Price
   - Trade whisper command

---

## Technical Architecture

### Frontend Components

```
frontend/src/routes/upgrades/
├── index.tsx                    # Main page route
├── components/
│   ├── PoBInput.tsx             # File upload + paste code (tabs)
│   ├── CurrentBuild.tsx         # Display parsed build summary
│   ├── ItemSlotSelector.tsx     # Dropdown for equipment slots
│   ├── UpgradeFilters.tsx       # Price, stat filters
│   ├── UpgradeResults.tsx       # Results table with TanStack Table
│   └── TradeWhisper.tsx         # Copy whisper command button
```

**Key UI interactions:**
- File upload: `<input type="file" accept=".xml" />`
- Import code: `<textarea>` with validation
- Results: Sortable table (by price, stat improvement, value ratio)

### Backend Components

```
backend/src/contexts/upgrades/
├── api/
│   └── routes.py                # POST /api/upgrades/find
├── services/
│   ├── pob_parser.py            # Parse PoB XML/code → Build
│   ├── trade_api_client.py      # Query pathofexile.com/trade
│   ├── stat_extractor.py        # Extract item stats for comparison
│   └── upgrade_ranker.py        # Rank items by improvement
├── domain/
│   └── schemas.py               # Request/response Pydantic models
```

---

## API Contract

### Request

**Endpoint:** `POST /api/upgrades/find`

**Content-Type:** `multipart/form-data`

**Parameters:**

```python
{
  # Build source (one of):
  "pob_file": File,                  # Optional: XML file upload
  "pob_code": str,                   # Optional: base64 import string

  # Required:
  "item_slot": str,                  # "amulet", "ring1", "ring2", "helmet", etc.
  "game": str,                       # "poe1" or "poe2"
  "league": str,                     # "Affliction", "Standard", etc.

  # Optional filters:
  "max_price_chaos": float,          # e.g., 50.0
  "min_life": int,                   # e.g., 60
  "min_resistance": int,             # e.g., 30
}
```

### Response

**Status:** 200 OK

**Body:**

```json
{
  "current_item": {
    "name": "Amber Amulet",
    "stats": {
      "life": 45,
      "fire_res": 28,
      "cold_res": 15,
      "strength": 12
    }
  },
  "upgrades": [
    {
      "id": "abc123",
      "name": "Coral Amulet",
      "type": "Rare",
      "price_chaos": 25.0,
      "stats": {
        "life": 72,
        "fire_res": 40,
        "cold_res": 35,
        "strength": 18
      },
      "improvements": {
        "life": +27,
        "fire_res": +12,
        "cold_res": +20,
        "strength": +6
      },
      "improvement_score": 65.0,    // Weighted score
      "value_ratio": 2.6,            // improvement_score / price
      "trade_url": "https://www.pathofexile.com/trade/search/...",
      "whisper": "@Player Hi, I would like to buy your Coral Amulet..."
    }
    // ... more items
  ],
  "query_time_ms": 1250
}
```

---

## Core Component Details

### 1. PoB Parser (`pob_parser.py`)

**Purpose:** Convert PoB XML or import code into Build domain object

**Key functions:**

```python
def parse_pob_xml(xml_content: str) -> Build:
    """Parse PoB XML string into Build object."""
    tree = ET.fromstring(xml_content)
    build_elem = tree.find("Build")
    items_elem = tree.find("Items")
    # Extract: character class, level, items, passive tree, skills
    return Build(...)

def parse_pob_code(import_code: str) -> Build:
    """Decode and parse PoB import code."""
    # 1. Base64 decode
    compressed = base64.b64decode(import_code)
    # 2. Decompress (zlib)
    xml_content = zlib.decompress(compressed).decode('utf-8')
    # 3. Parse XML
    return parse_pob_xml(xml_content)

def extract_item_from_slot(build: Build, slot: str) -> dict:
    """Get current item from specific equipment slot."""
    # Parse items JSONB, find item in specified slot
    return build.items.get(slot)
```

**Dependencies:**
- `xml.etree.ElementTree` (standard library)
- `base64`, `zlib` (standard library)
- `src.contexts.core.Build` (domain model)

---

### 2. Trade API Client (`trade_api_client.py`)

**Purpose:** Query pathofexile.com/trade API for items

**Key functions:**

```python
async def search_items(
    game: str,
    league: str,
    item_filters: dict
) -> list[dict]:
    """Search for items on trade API.

    Args:
        game: "poe1" or "poe2"
        league: League name
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

    # 2. POST to trade API
    search_url = f"https://www.pathofexile.com/api/trade/search/{league}"
    response = await http_client.post(search_url, json=query)
    result_ids = response.json()["result"][:50]  # Top 50 results

    # 3. Fetch item details
    fetch_url = f"https://www.pathofexile.com/api/trade/fetch/{','.join(result_ids)}"
    items_response = await http_client.get(fetch_url)

    # 4. Parse and normalize items
    return [parse_trade_item(item) for item in items_response.json()["result"]]

def build_trade_query(filters: dict) -> dict:
    """Build trade API query JSON from filters."""
    # Translate our filters to trade API format
    # Trade API has complex nested query structure
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

**Dependencies:**
- `httpx` (async HTTP client)
- Trade API documentation: https://www.pathofexile.com/developer/docs/reference

**Rate limiting:**
- Trade API has rate limits (need to implement backoff)
- Consider caching recent queries (optional for MVP)

---

### 3. Stat Extractor (`stat_extractor.py`)

**Purpose:** Extract comparable stats from items

**Key functions:**

```python
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
        # Parse mod text like "+72 to maximum Life"
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
    # Use regex patterns to extract stat types and values
    patterns = {
        r"[+-]?(\d+) to maximum Life": ("life", 1),
        r"[+-]?(\d+)% to Fire Resistance": ("fire_res", 1),
        r"[+-]?(\d+)% to Cold Resistance": ("cold_res", 1),
        r"[+-]?(\d+)% to Lightning Resistance": ("lightning_res", 1),
        r"[+-]?(\d+) to Strength": ("strength", 1),
        # ... more patterns
    }

    for pattern, (stat_name, _) in patterns.items():
        match = re.search(pattern, mod_text)
        if match:
            return stat_name, float(match.group(1))

    return None, 0
```

---

### 4. Upgrade Ranker (`upgrade_ranker.py`)

**Purpose:** Compare items and rank by improvement

**Key functions:**

```python
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

---

## Implementation Sequence

### Phase 1: Backend Core (Day 1)
1. ✅ Create `contexts/upgrades/` structure
2. ✅ Implement PoB parser (XML + import code)
3. ✅ Write tests for PoB parser with sample builds
4. ✅ Implement Trade API client (search + fetch)
5. ✅ Implement stat extractor
6. ✅ Implement upgrade ranker

### Phase 2: API Endpoint (Day 1-2)
7. ✅ Create FastAPI route
8. ✅ Wire up components
9. ✅ Add request validation (Pydantic schemas)
10. ✅ Test end-to-end with Postman/curl

### Phase 3: Frontend (Day 2-3)
11. ✅ Create upgrade finder page
12. ✅ Build PoB input component (file + code tabs)
13. ✅ Build results table with TanStack Table
14. ✅ Add filtering and sorting
15. ✅ Style with Tailwind + shadcn/ui

### Phase 4: Polish (Day 3)
16. ✅ Error handling (invalid PoB, API failures)
17. ✅ Loading states
18. ✅ Empty states
19. ✅ Trade whisper copy button
20. ✅ Price conversion (divine/exalt → chaos)

---

## Testing Strategy

### Unit Tests
- PoB parser with various XML formats
- Stat extractor with different mod formats
- Upgrade ranker with mock data

### Integration Tests
- Full API endpoint with mock Trade API
- Test with real PoB exports from samples

### Manual Testing
- Test with various build archetypes (life, ES, hybrid)
- Test different item slots
- Verify trade whispers work in-game

---

## Future Enhancements

**Not in MVP, but easy to add later:**

1. **Custom stat weights** - Let user adjust importance of stats
2. **Multiple results pages** - Pagination for >50 results
3. **Save searches** - Bookmark specific upgrade searches
4. **Price history** - Show if item is good deal vs historical prices
5. **Bulk upgrade** - Find upgrades for multiple slots at once
6. **DPS calculations** - Use PoB binary for exact DPS improvement (Journey 5)

---

## Open Questions

1. **Price conversion rates** - How to get current divine/exalt → chaos rates?
   - Option A: Hardcode (needs manual updates)
   - Option B: Query poe.ninja API (adds dependency)
   - Option C: User provides conversion rate (annoying)

2. **Stat weights** - Should we have build-specific weights?
   - Option A: Universal weights (simpler, less accurate)
   - Option B: Detect build archetype from passive tree (complex)
   - Option C: User selects archetype (manual but accurate)

3. **Item slot naming** - PoB uses different names than Trade API
   - Need mapping: PoB "Weapon 1" → Trade API "weapon1"
   - Document the canonical slot names

4. **Corrupted items** - Include or exclude?
   - Default: Exclude (can't modify)
   - Add filter option later

---

## Dependencies

**Python packages:**
```
httpx          # Async HTTP client
pydantic       # Request/response validation
```

**External APIs:**
- pathofexile.com/trade API (public, rate limited)

**No database required** - All processing is stateless and ephemeral
