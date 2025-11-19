# Backend Scripts

Utility scripts for data collection, database management, and maintenance.

## Configuration Setup

**⚠️ IMPORTANT: Complete this step before running any collection scripts!**

### 1. Create your config file

```bash
cd backend/scripts
cp config.example.json config.json
```

### 2. Update current league names

Edit `config.json` and replace placeholders:

```json
{
  "poe1": {
    "current_temp_league": "Necropolis",  // ← Update this
    "leagues": ["Standard", "Necropolis"] // ← And this
  }
}
```

### 3. Find current league names

- Visit **https://poe.ninja/** and check the league selector dropdown
- League names are **case-sensitive** and must match exactly
- Recent league examples: "Necropolis", "Affliction", "Ancestor", "Crucible"

### 4. Verify configuration

The scripts will validate your config and show helpful errors if:
- `config.json` is missing (will prompt you to copy from example)
- League name still contains `REPLACE_WITH_CURRENT_LEAGUE` placeholder

**Note:** `config.json` is gitignored, so your local configuration won't be committed to the repository.

---

## Sample Collection Scripts

These scripts collect data samples from upstream sources for Epic 1.2.

### collect_poeninja_samples.py

Collects economy snapshots and build ladder data from poe.ninja.

```bash
# Collect PoE1 samples
uv run python scripts/collect_poeninja_samples.py --game poe1

# Collect PoE2 samples
uv run python scripts/collect_poeninja_samples.py --game poe2

# Collect both
uv run python scripts/collect_poeninja_samples.py --all
```

**Output:** `_samples/data/{game}/poeninja/`

**Rate Limit:** 1 request/second (respectful)

### collect_trade_samples.py

Collects item search and bulk exchange data from official trade API.

```bash
uv run python scripts/collect_trade_samples.py --game poe1
uv run python scripts/collect_trade_samples.py --game poe2
```

**Output:** `_samples/data/{game}/trade/`

**Rate Limit:** See official docs, implements exponential backoff

**Status:** ⚠️ Skeleton only - needs implementation in Task 1.2.4/1.2.5

### collect_poedb_samples.py

Collects base item data, modifiers, and crafting recipes from PoeDB/Poe2DB.

```bash
uv run python scripts/collect_poedb_samples.py
```

**Output:** `_samples/data/{poe1,poe2}/{poedb,poe2db}/`

**Status:** ⚠️ Not yet created - Task 1.2.7

### validate_modifier_design.py

**NEW:** Validates the Modifier value object design against all collected samples.

```bash
# Validate all sources and games
uv run python backend/scripts/validate_modifier_design.py

# Validate specific game
uv run python backend/scripts/validate_modifier_design.py --game poe2

# Validate specific source
uv run python backend/scripts/validate_modifier_design.py --source trade

# Verbose output
uv run python backend/scripts/validate_modifier_design.py --verbose
```

**Output:** Validation summary with success/failure rates

**Purpose:**
- Proves Modifier design works with real data from all sources
- Demonstrates adapter parsing logic for Epic 1.4+
- Contains reusable functions for Trade API, poe.ninja, and PoB parsing
- Exit code 0 = all passed, 1 = failures found

**Note:** Run from project root (not backend/ directory)

### validate_currency_design.py

**NEW:** Validates the Currency domain model design against poe.ninja economy data.

```bash
# Validate all games
uv run python backend/scripts/validate_currency_design.py

# Validate specific game
uv run python backend/scripts/validate_currency_design.py --game poe2

# Verbose output
uv run python backend/scripts/validate_currency_design.py --verbose
```

**Output:** Validation summary with success/failure rates, unique currency comparison

**Purpose:**
- Proves Currency design works with real poe.ninja economy data
- Demonstrates adapter parsing logic for Epic 1.4+
- Contains reusable `parse_poeninja_currency()` function
- Shows PoE1 vs PoE2 currency differences
- Exit code 0 = all passed, 1 = failures found

**Note:** Run from project root (not backend/ directory)

## Usage Notes

- Collection scripts should be run from the `backend/` directory
- Validation scripts should be run from project root
- Use `uv run` to execute in the project's virtual environment
- Check `_samples/data/README.md` for sample documentation
- Samples are .gitignored by default (except meta.json)

## Adding New Collection Scripts

When creating new collection scripts:

1. Follow the same structure as existing scripts
2. Use `structlog` for logging
3. Save metadata to `meta.json`
4. Respect rate limits for external APIs
5. Handle errors gracefully (don't fail entire collection)
6. Document in this README

---

**Last Updated:** 2025-11-18
**Epic:** 1.2 - Upstream Data Sample Collection
