# User Journey 5: Calculate Exact Stat Deltas with PoB

**User Story:** "Show me EXACT DPS increase if I swap this item"

**Priority:** P2 (High value, complex implementation)

**Complexity:** High

**Database Required:** No (but caching recommended)

______________________________________________________________________

## User Flow

1. User provides build (PoB XML/code)
1. System displays current build stats:
   - Total DPS (all skills)
   - Effective HP (life + ES + mitigation)
   - Clear speed metrics
   - Other defensive stats
1. User clicks "Test Item Swap" on any equipment slot
1. User either:
   - Selects item from market search (Journey 1)
   - Pastes item from trade (uses Trade API item ID)
   - Manually creates test item (custom stats)
1. System:
   - Modifies PoB XML with new item
   - Calls PoB binary to recalculate stats
   - Returns exact before/after comparison
1. User sees detailed stat deltas:
   - DPS change (total + per skill)
   - HP change (effective + raw)
   - Resistance changes
   - Other defensive metrics
   - Cost-benefit analysis

______________________________________________________________________

## Technical Architecture

### Why PoB Binary?

**Problem:** Calculating exact DPS is extremely complex

- Skill mechanics
- Support gems interactions
- Passive tree modifiers
- Ascendancy bonuses
- Item interactions (trigger, CoC, etc.)
- Buffs, debuffs, configurations

**Solution:** Use Path of Building's calculation engine

- It already handles all mechanics correctly
- Community-maintained and up-to-date
- Expose CLI interface for automated calculations

### Path of Building CLI

**PoB Community Fork:** https://github.com/PathOfBuildingCommunity/PathOfBuilding

**CLI wrapper needed:**

```lua
-- pob_cli.lua
-- Wrapper script to load build XML and return stats

function main(buildFile, outputFormat)
    -- Load build
    local build = loadBuildFromFile(buildFile)

    -- Calculate stats
    local output = build.calcsTab:buildOutput()

    -- Return as JSON
    if outputFormat == "json" then
        return json.encode(output)
    end
end
```

______________________________________________________________________

## Backend Components

```
backend/src/contexts/pob/
├── domain/
│   ├── build_stats.py           # Stat output from PoB
│   └── stat_delta.py            # Before/after comparison
├── services/
│   ├── pob_wrapper.py           # Subprocess wrapper for PoB CLI
│   ├── xml_modifier.py          # Modify PoB XML (item swap)
│   └── stat_calculator.py       # Calculate deltas
└── api/
    └── routes.py                # POST /api/pob/calculate-delta
```

______________________________________________________________________

## API Contract

### Request

**Endpoint:** `POST /api/pob/calculate-delta`

**Parameters:**

```python
{
  # Build source:
  "pob_code": str,               # Base64 PoB import code

  # Item to swap in:
  "slot": str,                   # "weapon", "amulet", etc.
  "new_item": {
    # Option 1: From trade API
    "trade_id": str,             # Trade API item ID

    # Option 2: Custom item
    "base_type": str,
    "rarity": str,
    "mods": {
      "implicit": [...],
      "explicit": [...],
      "crafted": [...]
    }
  },

  # Configuration:
  "config_overrides": {          # Optional PoB config changes
    "enemy_is_boss": true,
    "is_shocked": false,
    "enemy_physical_reduction": 0
  }
}
```

### Response

```json
{
  "before": {
    "total_dps": 5000000,
    "main_skill_dps": 5000000,
    "skill_breakdown": {
      "Righteous Fire": {
        "total_dps": 5000000,
        "hit_dps": 0,
        "dot_dps": 5000000
      }
    },
    "defenses": {
      "life": 8500,
      "energy_shield": 0,
      "effective_life": 85000,
      "physical_reduction": 90,
      "fire_res": 75,
      "cold_res": 75,
      "lightning_res": 76,
      "chaos_res": 20,
      "block": 15,
      "spell_block": 0
    },
    "offensive": {
      "crit_chance": 0,
      "hit_chance": 100,
      "attack_speed": 0,
      "cast_speed": 0
    },
    "other": {
      "movement_speed": 30
    }
  },
  "after": {
    // Same structure as "before"
    "total_dps": 5750000,
    "main_skill_dps": 5750000,
    // ...
  },
  "deltas": {
    "total_dps": +750000,
    "total_dps_percent": +15.0,
    "life": +75,
    "effective_life": +7500,
    "fire_res": +5,
    // ... all changed stats
  },
  "summary": {
    "dps_change": "+15.0% DPS (+750k)",
    "ehp_change": "+8.8% eHP (+7.5k)",
    "major_improvements": [
      "+15% DPS",
      "+75 Life",
      "+5% Fire Resistance"
    ],
    "major_downgrades": [],
    "overall_rating": "significant upgrade",  // "huge", "significant", "moderate", "small", "downgrade"
    "worth_it": true
  },
  "calculation_time_ms": 850
}
```

______________________________________________________________________

## Core Components

### 1. PoB Wrapper (`pob_wrapper.py`)

**Purpose:** Execute PoB binary and parse results

```python
import subprocess
import json
import tempfile
from pathlib import Path

class PoBWrapper:
    """Wrapper for Path of Building CLI.

    Requires PoB Community Fork installed.
    """

    def __init__(self, pob_path: str = None):
        """Initialize PoB wrapper.

        Args:
            pob_path: Path to PoB installation
                     (default: auto-detect or use environment variable)
        """
        self.pob_path = pob_path or self._find_pob()
        self.lua_cli = Path(__file__).parent / "pob_cli.lua"

    def calculate_build_stats(
        self,
        build_xml: str,
        config_overrides: dict = None
    ) -> dict:
        """Calculate build stats using PoB.

        Args:
            build_xml: PoB build as XML string
            config_overrides: Optional config changes

        Returns:
            Dict of calculated stats
        """
        # Write XML to temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.xml',
            delete=False
        ) as f:
            f.write(build_xml)
            xml_path = f.name

        try:
            # Call PoB CLI
            result = subprocess.run(
                [
                    self.pob_path,
                    "--script", str(self.lua_cli),
                    "--build", xml_path,
                    "--format", "json"
                ],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"PoB calculation failed: {result.stderr}")

            # Parse JSON output
            stats = json.loads(result.stdout)
            return stats

        finally:
            # Cleanup temp file
            Path(xml_path).unlink()

    def _find_pob(self) -> str:
        """Auto-detect PoB installation."""
        # Check environment variable
        pob_path = os.getenv("POB_PATH")
        if pob_path and Path(pob_path).exists():
            return pob_path

        # Common installation paths
        common_paths = [
            "/usr/local/bin/PathOfBuilding",
            "C:\\Program Files\\Path of Building\\PathOfBuilding.exe",
            "~/.local/share/PathOfBuilding/PathOfBuilding",
        ]

        for path in common_paths:
            expanded = Path(path).expanduser()
            if expanded.exists():
                return str(expanded)

        raise FileNotFoundError(
            "Path of Building not found. Set POB_PATH environment variable."
        )
```

______________________________________________________________________

### 2. XML Modifier (`xml_modifier.py`)

**Purpose:** Modify PoB XML to swap items

```python
import xml.etree.ElementTree as ET
from copy import deepcopy

def swap_item_in_build(
    build_xml: str,
    slot: str,
    new_item_xml: str
) -> str:
    """Replace item in specific slot.

    Args:
        build_xml: Original PoB XML
        slot: Equipment slot (e.g., "Weapon 1", "Amulet")
        new_item_xml: New item as PoB item XML

    Returns:
        Modified build XML
    """
    # Parse XMLs
    tree = ET.fromstring(build_xml)
    new_item = ET.fromstring(new_item_xml)

    # Find Items section
    items_elem = tree.find("Items")
    if items_elem is None:
        raise ValueError("No Items section found")

    # Find item in specified slot
    found = False
    for item_elem in items_elem.findall("Item"):
        if item_elem.get("id") == map_slot_to_id(slot):
            # Replace with new item
            items_elem.remove(item_elem)
            new_item.set("id", map_slot_to_id(slot))
            items_elem.append(new_item)
            found = True
            break

    if not found:
        # Slot was empty, add new item
        new_item.set("id", map_slot_to_id(slot))
        items_elem.append(new_item)

    # Return modified XML
    return ET.tostring(tree, encoding='unicode')

def create_item_xml(item_data: dict) -> str:
    """Create PoB item XML from item data.

    Args:
        item_data: Item dict with mods, base type, etc.

    Returns:
        PoB-formatted item XML
    """
    item_elem = ET.Element("Item")

    # Basic properties
    item_elem.set("rarity", item_data["rarity"])
    item_elem.text = item_data["base_type"]

    # Add mods as text lines
    mod_lines = []

    if item_data.get("implicit_mods"):
        for mod in item_data["implicit_mods"]:
            mod_lines.append(mod)

    if item_data.get("explicit_mods"):
        for mod in item_data["explicit_mods"]:
            mod_lines.append(mod)

    # PoB format: newline-separated mods
    item_elem.text += "\n" + "\n".join(mod_lines)

    return ET.tostring(item_elem, encoding='unicode')

def map_slot_to_id(slot: str) -> int:
    """Map slot name to PoB item ID.

    PoB uses numeric IDs for slots:
    1 = Weapon 1
    2 = Weapon 2 (or Offhand)
    3 = Helmet
    4 = Body Armour
    5 = Gloves
    6 = Boots
    7 = Amulet
    8 = Ring 1
    9 = Ring 2
    10 = Belt
    """
    slot_map = {
        "weapon": 1,
        "offhand": 2,
        "helmet": 3,
        "body_armour": 4,
        "gloves": 5,
        "boots": 6,
        "amulet": 7,
        "ring1": 8,
        "ring2": 9,
        "belt": 10
    }
    return slot_map.get(slot.lower(), 1)
```

______________________________________________________________________

### 3. Stat Calculator (`stat_calculator.py`)

**Purpose:** Calculate deltas between before/after

```python
def calculate_stat_deltas(before: dict, after: dict) -> dict:
    """Calculate differences between before/after stats.

    Args:
        before: Stats before item swap
        after: Stats after item swap

    Returns:
        Dict of deltas with absolute and percentage changes
    """
    deltas = {}

    # DPS deltas
    deltas["total_dps"] = after["total_dps"] - before["total_dps"]
    deltas["total_dps_percent"] = (
        (deltas["total_dps"] / before["total_dps"]) * 100
        if before["total_dps"] > 0 else 0
    )

    # Defensive deltas
    for stat in ["life", "energy_shield", "effective_life", "physical_reduction"]:
        before_val = before["defenses"][stat]
        after_val = after["defenses"][stat]
        deltas[stat] = after_val - before_val
        if before_val > 0:
            deltas[f"{stat}_percent"] = (deltas[stat] / before_val) * 100

    # Resistance deltas
    for res in ["fire_res", "cold_res", "lightning_res", "chaos_res"]:
        deltas[res] = after["defenses"][res] - before["defenses"][res]

    return deltas

def generate_summary(deltas: dict, item_price: float = None) -> dict:
    """Generate human-readable summary of changes.

    Args:
        deltas: Calculated stat deltas
        item_price: Optional price for cost-benefit analysis

    Returns:
        Summary dict with major changes and rating
    """
    major_improvements = []
    major_downgrades = []

    # Check DPS
    if deltas["total_dps_percent"] > 10:
        major_improvements.append(
            f"+{deltas['total_dps_percent']:.1f}% DPS "
            f"(+{format_number(deltas['total_dps'])})"
        )
    elif deltas["total_dps_percent"] < -5:
        major_downgrades.append(f"{deltas['total_dps_percent']:.1f}% DPS")

    # Check life
    if deltas["life"] > 50:
        major_improvements.append(f"+{deltas['life']} Life")
    elif deltas["life"] < -50:
        major_downgrades.append(f"{deltas['life']} Life")

    # Check eHP
    if deltas.get("effective_life", 0) > 5000:
        major_improvements.append(
            f"+{format_number(deltas['effective_life'])} eHP"
        )

    # Check resistances
    for res in ["fire_res", "cold_res", "lightning_res"]:
        if deltas[res] > 10:
            major_improvements.append(f"+{deltas[res]}% {res.split('_')[0].title()} Res")
        elif deltas[res] < -10:
            major_downgrades.append(f"{deltas[res]}% {res.split('_')[0].title()} Res")

    # Overall rating
    improvement_count = len(major_improvements)
    downgrade_count = len(major_downgrades)

    if improvement_count >= 3 and downgrade_count == 0:
        rating = "huge upgrade"
    elif improvement_count >= 2 and downgrade_count == 0:
        rating = "significant upgrade"
    elif improvement_count > downgrade_count:
        rating = "moderate upgrade"
    elif improvement_count == downgrade_count:
        rating = "sidegrade"
    else:
        rating = "downgrade"

    # Cost-benefit if price provided
    worth_it = None
    if item_price:
        value_score = improvement_count * 10 - downgrade_count * 5
        worth_it = value_score > (item_price / 10)  # Rough heuristic

    return {
        "major_improvements": major_improvements,
        "major_downgrades": major_downgrades,
        "overall_rating": rating,
        "worth_it": worth_it
    }
```

______________________________________________________________________

## Implementation Sequence

### Phase 1: PoB Integration (Week 1)

1. ✅ Set up PoB Community Fork locally
1. ✅ Create Lua CLI wrapper script
1. ✅ Test manual stat calculations
1. ✅ Parse PoB output format

### Phase 2: Python Wrapper (Week 1)

5. ✅ Implement subprocess wrapper
1. ✅ Add timeout and error handling
1. ✅ Write tests with sample builds
1. ✅ Optimize performance (caching, reuse)

### Phase 3: XML Modification (Week 2)

9. ✅ Implement item XML creation
1. ✅ Implement item swapping logic
1. ✅ Test with various item types
1. ✅ Handle edge cases (corrupted, influenced, etc.)

### Phase 4: API Endpoint (Week 2)

13. ✅ Create stat calculator service
01. ✅ Build API endpoint
01. ✅ Add request validation
01. ✅ Implement caching (same build + same item = cached)

### Phase 5: Frontend (Week 3)

17. ✅ Build stat comparison UI
01. ✅ Add before/after visualization
01. ✅ Integrate with Journey 1 (test items from search)
01. ✅ Polish UX (loading states, error handling)

______________________________________________________________________

## Performance Optimization

**Challenge:** PoB calculations take 500ms-2s per build

**Solutions:**

1. **Caching**

   ```python
   cache_key = hash(pob_code + item_json + config)
   if cache_key in redis:
       return cached_result
   ```

1. **Pre-calculation** - Calculate common swaps ahead of time

   - Cache results for top 100 builds × common item types
   - Refresh cache periodically

1. **Parallel processing** - Use process pool for multiple calculations

   ```python
   with ProcessPoolExecutor(max_workers=4) as executor:
       futures = [executor.submit(calculate_stats, build) for build in builds]
   ```

1. **Approximation mode** - Fast estimates for UI preview

   - Use simplified calculation (no PoB binary)
   - Show "Calculating exact stats..." while PoB runs
   - Update UI when exact results ready

______________________________________________________________________

## Limitations and Workarounds

### Limitation 1: PoB Binary Required

**Problem:** Users need PoB installed to use this feature

**Workarounds:**

- Provide Docker image with PoB pre-installed
- Cloud-hosted PoB service (run on our servers)
- Fallback to approximate calculations

### Limitation 2: Calculation Time

**Problem:** 1-2 seconds per calculation is slow

**Workarounds:**

- Show "calculating..." UI with progress
- Cache aggressively
- Offer "quick estimate" mode

### Limitation 3: PoB Format Changes

**Problem:** PoB format might change between versions

**Workarounds:**

- Pin PoB version
- Add version detection
- Graceful degradation if format incompatible

______________________________________________________________________

## Alternative: Approximate Calculations

**For cases where PoB binary isn't available:**

```python
def approximate_dps_change(
    current_item_stats: dict,
    new_item_stats: dict,
    build_type: str
) -> float:
    """Rough DPS estimate without PoB.

    Not accurate, but fast and good enough for filtering.
    """
    # Simple heuristic based on build type
    if build_type == "spell":
        # Spell DPS scales with added damage, cast speed, crit
        stat_value = (
            new_item_stats.get("added_spell_damage", 0) * 100 +
            new_item_stats.get("cast_speed", 0) * 50 +
            new_item_stats.get("crit_chance", 0) * 200
        )
    elif build_type == "attack":
        # Attack DPS scales with added damage, attack speed, crit
        stat_value = (
            new_item_stats.get("added_physical_damage", 0) * 100 +
            new_item_stats.get("attack_speed", 0) * 50 +
            new_item_stats.get("crit_chance", 0) * 200
        )
    else:
        # Generic
        stat_value = sum(new_item_stats.values())

    # Very rough estimate: 1% DPS per 10 stat points
    return stat_value / 10
```

______________________________________________________________________

## Frontend: Before/After Comparison

### Visual Design

```tsx
<StatComparisonView>
  <Column name="Before">
    <StatGroup label="Offense">
      <Stat name="Total DPS" value="5.0M" />
      <Stat name="Crit Chance" value="45%" />
      <Stat name="Hit Chance" value="100%" />
    </StatGroup>
    <StatGroup label="Defense">
      <Stat name="Life" value="8,500" />
      <Stat name="eHP" value="85k" />
      <Stat name="Phys Reduction" value="90%" />
    </StatGroup>
  </Column>

  <Column name="Change">
    <StatGroup label="Offense">
      <Delta value="+750k" percent="+15.0%" positive />
      <Delta value="+3%" percent="+6.7%" positive />
      <Delta value="0%" neutral />
    </StatGroup>
    <StatGroup label="Defense">
      <Delta value="+75" positive />
      <Delta value="+7.5k" percent="+8.8%" positive />
      <Delta value="-2%" negative />
    </StatGroup>
  </Column>

  <Column name="After">
    <StatGroup label="Offense">
      <Stat name="Total DPS" value="5.75M" highlight />
      <Stat name="Crit Chance" value="48%" highlight />
      <Stat name="Hit Chance" value="100%" />
    </StatGroup>
    <StatGroup label="Defense">
      <Stat name="Life" value="8,575" highlight />
      <Stat name="eHP" value="92.5k" highlight />
      <Stat name="Phys Reduction" value="88%" lowlight />
    </StatGroup>
  </Column>
</StatComparisonView>

<SummaryCard>
  <Badge>Significant Upgrade</Badge>
  <Improvements>
    <Chip>+15% DPS</Chip>
    <Chip>+75 Life</Chip>
    <Chip>+5% Fire Res</Chip>
  </Improvements>
  {itemPrice && (
    <CostBenefit>
      Price: {itemPrice}c → <Badge>Worth It</Badge>
    </CostBenefit>
  )}
</SummaryCard>
```

______________________________________________________________________

## Dependencies

**New dependencies:**

- Path of Building Community Fork (external, not Python package)
- `lupa` or `lunatic-python` (optional, for Lua integration)

**System requirements:**

- PoB binary installed (or Docker image)
- 1-2GB disk space for PoB data files

______________________________________________________________________

## Open Questions

1. **PoB hosting strategy:**

   - Local installation (user installs PoB)?
   - Cloud service (we host PoB)?
   - Docker image (easy deployment)?

1. **Accuracy vs speed trade-off:**

   - Always use exact PoB calculations (slow)?
   - Approximate first, exact on demand (complex UX)?
   - Cache everything aggressively (stale data)?

1. **Multi-item swaps:**

   - Allow testing multiple item changes at once?
   - Show cumulative effect of upgrading all slots?

1. **Config management:**

   - Parse config from PoB build?
   - Let user override (boss DPS, shocked, etc.)?
   - Provide presets ("mapping", "bossing", "tankiness")?
