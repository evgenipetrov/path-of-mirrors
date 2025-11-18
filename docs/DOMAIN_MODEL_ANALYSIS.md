# Domain Model Analysis - Epic 1.3

**Date:** 2025-11-18
**Status:** 🔄 In Progress
**Approach:** Sample-driven, incremental design

---

## Overview

This document analyzes collected samples to design canonical domain models that work across all data sources. We're taking a **slow, careful approach** - starting minimal and adding complexity only when needed.

---

## Current Samples

### Available Data (11MB, 35 files)

**PoE1 (poe.ninja):**
- ✅ 15 character builds (Keepers of the Flame league)
- ✅ 1 build search summary
- ❌ Economy data (currency, items) - **NOT YET COLLECTED**

**PoE2 (poe.ninja):**
- ✅ 2 character builds (Rise of the Abyssal league)
- ✅ 1 build search summary
- ❌ Economy data - **NOT YET COLLECTED**

### What We're Designing For

**Phase 1 Priority:** Character build snapshots (what we have)
**Future:** Economy snapshots (currency prices, item prices) - will add later

---

## Sample Analysis: Character Builds

### Data Source Structure

**poe.ninja character endpoint:** `/builds/{league}/get-character`

```json
{
  "account": "Poteitik-3151",
  "name": "Lyaguxesht",
  "league": "Keepers",
  "defensiveStats": { ... },
  "offensiveStats": { ... },
  "skills": [ ... ],
  "items": [ ... ],
  "passives": { ... },
  "jewels": [ ... ],
  "metadata": { ... }
}
```

### Key Observations

1. **Immutable Snapshots** - Build data is a point-in-time snapshot
2. **Rich Nested Data** - Skills, items, passives are complex nested objects
3. **Game-Specific** - PoE1 and PoE2 have different skill systems, classes
4. **Large Payloads** - 150KB - 300KB per character (lots of detail)

---

## Design Philosophy: Start Minimal

### Principle 1: Don't Model Everything at Once

❌ **DON'T:** Try to model every field in the 300KB payload
✅ **DO:** Model the **metadata** first, store raw JSON for details

### Principle 2: Defer Complex Nested Data

❌ **DON'T:** Create Item, Skill, Passive models in Epic 1.3
✅ **DO:** Store as JSONB, extract to models in later epics when needed

### Principle 3: Validate Before Normalizing

❌ **DON'T:** Assume structure across all samples
✅ **DO:** Test against all 17+ samples to find edge cases

---

## Proposed Model: CharacterSnapshot (Minimal)

### Purpose

Store **metadata** about a character build snapshot with the **full JSON payload** for later processing.

### Design Rationale

**Why minimal?**
- We don't know all use cases yet
- Parsing 300KB payloads into ORM models = complexity
- JSONB gives flexibility while we learn the domain
- Can extract fields to columns incrementally

**What we need NOW:**
- Track which characters we've collected
- Query by league, class, level
- Avoid re-fetching same character
- Basic analytics (class distribution, level ranges)

### Model Definition (v1 - Minimal)

```python
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.contexts.core import BaseEntity
from src.shared import Game

class CharacterSnapshot(BaseEntity):
    """Immutable snapshot of a PoE character build.

    Stores metadata for querying + full JSON payload for flexibility.
    Future epics will extract specific fields (items, skills) as needed.
    """

    __tablename__ = "character_snapshots"

    # Core identity
    game: Mapped[Game] = mapped_column(String(10), index=True)
    account_name: Mapped[str] = mapped_column(String(255), index=True)
    character_name: Mapped[str] = mapped_column(String(255), index=True)
    league: Mapped[str] = mapped_column(String(100), index=True)

    # Queryable metadata (extracted from JSON)
    level: Mapped[int | None] = mapped_column(Integer, default=None)
    class_name: Mapped[str | None] = mapped_column(String(50), default=None, index=True)

    # Full payload (for future processing)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Data provenance
    source: Mapped[str] = mapped_column(String(50), default="poe.ninja")
    snapshot_version: Mapped[str | None] = mapped_column(String(100), default=None)
```

### Composite Unique Constraint

```python
# In Alembic migration
sa.UniqueConstraint(
    'game', 'account_name', 'character_name', 'snapshot_version',
    name='uq_character_snapshot'
)
```

**Rationale:** Same character can be snapshotted multiple times (different versions)

---

## Model Fields Explained

| Field | Type | Nullable | Indexed | Purpose |
|-------|------|----------|---------|---------|
| `game` | Enum | No | Yes | PoE1 vs PoE2 filtering |
| `account_name` | str | No | Yes | Owner account |
| `character_name` | str | No | Yes | Character name |
| `league` | str | No | Yes | League filtering (Keepers, Standard, etc.) |
| `level` | int | Yes | No | Character level (for analytics) |
| `class_name` | str | Yes | Yes | Class filtering (Witch, Ranger, etc.) |
| `raw_data` | JSON | No | No | Full poe.ninja payload |
| `source` | str | No | No | Data source ("poe.ninja") |
| `snapshot_version` | str | Yes | No | poe.ninja snapshot ID |

### Why These Fields?

**Indexed fields** = Common query patterns:
- "Show builds for Keepers league"
- "Show all Witch builds"
- "Show builds by account X"

**Non-indexed fields** = Metadata only:
- `level` - For sorting/filtering (small cardinality)
- `snapshot_version` - For deduplication only

**JSONB `raw_data`** = Everything else:
- Skills, items, passives, defensive stats, offensive stats
- Can be queried with JSONB operators when needed
- Deferred extraction to later epics

---

## What We're NOT Modeling Yet

❌ **Item model** - Complex, many types, game-specific
❌ **Skill model** - PoE1 vs PoE2 have different systems
❌ **Passive tree model** - Large, complex graph structure
❌ **Defensive/Offensive stats** - 50+ fields, unclear which matter

**Why defer?**
- Don't know which fields are actually used in UI
- Structure may change between games
- JSONB queries are fine for MVP

**When to extract?**
- Epic 2.X: Build comparison features → extract key stats to columns
- Epic 3.X: Item search → create Item model
- Epic 4.X: Skill analysis → create Skill model

---

## Validation Strategy

### Test Against All Samples

```python
def test_all_poe1_characters_map_to_snapshot():
    """Validate model works with all PoE1 samples."""
    samples_dir = Path("backend/_samples/data/poe1/poeninja/builds/keepers")

    for sample_file in samples_dir.glob("character_*.json"):
        with open(sample_file) as f:
            raw = json.load(f)

        # Map to model
        snapshot = CharacterSnapshot(
            game=Game.POE1,
            account_name=raw["account"],
            character_name=raw["name"],
            league=raw["league"],
            level=raw.get("level"),  # May not exist
            class_name=raw.get("class"),  # May not exist
            raw_data=raw,
            source="poe.ninja",
        )

        # Validate
        assert snapshot.account_name
        assert snapshot.character_name
        assert snapshot.league
        assert snapshot.raw_data is not None
```

### Edge Cases to Check

1. **Missing optional fields** (`level`, `class_name`)
2. **Unicode in names** (Korean, Chinese characters - we have samples!)
3. **Duplicate snapshots** (same char, different snapshot_version)
4. **League name variations** ("Keepers" vs "Keepers of the Flame")

---

## Database Design Decisions

### JSONB vs Normalized Tables

**Decision:** Use JSONB for `raw_data`

**Pros:**
- ✅ Schema flexibility
- ✅ Fast iteration (no migrations for new fields)
- ✅ PostgreSQL JSONB is indexed and queryable
- ✅ Preserves exact API response for debugging

**Cons:**
- ❌ Less type safety
- ❌ Harder to query deeply nested data
- ❌ Larger storage footprint

**Mitigation:**
- Extract frequently queried fields to columns incrementally
- Use generated columns for common JSONB queries (PostgreSQL 12+)
- Monitor JSONB query performance

### Partitioning Strategy (Future)

**Not needed for MVP** - Only 17 builds
**Revisit when:** > 100k snapshots (likely Phase 2)

**Potential strategy:**
- Partition by `created_at` (monthly)
- Or partition by `game` (PoE1 vs PoE2)

---

## Next Steps

### ✅ Step 1: Create Minimal Model (This Doc)

Document the design before writing code.

### 📋 Step 2: Implement Model

Create `backend/src/contexts/upstream/domain/models.py`:
- CharacterSnapshot class
- Pydantic schemas for API

### 📋 Step 3: Write Validation Tests

Test against all 17 samples:
- PoE1: 15 characters
- PoE2: 2 characters

### 📋 Step 4: Create Migration

Alembic migration for `character_snapshots` table.

### 📋 Step 5: Verify and Iterate

Run tests, fix issues, document learnings.

---

## Future Expansion

### When to Add Fields

Add extracted fields when:
1. **Frequent query pattern emerges** (e.g., "builds with >5k life")
2. **Performance issue with JSONB query** (extract to indexed column)
3. **Feature requires it** (e.g., skill tree visualization needs passive extraction)

### Candidate Fields for Future Extraction

**Defensive stats** (if build comparison feature):
- `life`, `energy_shield`, `evasion`, `armour`
- Resistances (fire, cold, lightning, chaos)

**Offensive stats** (if DPS analysis feature):
- `total_dps`, `skill_dps`
- Main skill name

**Items** (if item search feature):
- Extract to separate `Item` model with foreign key

---

## Questions to Resolve

### Q1: Should we store snapshot_version?

**Answer:** Yes - allows tracking API changes over time.

### Q2: Should level and class_name be nullable?

**Answer:** Yes - some API responses may not include them (defensive programming).

### Q3: What's the unique constraint?

**Answer:** `(game, account_name, character_name, snapshot_version)` - allows multiple snapshots of same character.

---

## Summary

**Model:** CharacterSnapshot (minimal metadata + JSONB)
**Fields:** 9 total (4 indexed, 5 metadata/data)
**Strategy:** Store everything in JSONB, extract incrementally
**Validation:** Test against all 17 samples
**Migration:** Simple table with indexes

**Next:** Implement the model and validate against samples.

---

**Last Updated:** 2025-11-18
**Status:** Ready for implementation
