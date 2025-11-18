# Configuration Guide

## Overview

The sample collection scripts use a centralized configuration system managed by `config.py`.

## Quick Start

```bash
# 1. Create your config file
cd backend/scripts
cp config.example.json config.json

# 2. Edit config.json - update the current league name
# Replace "REPLACE_WITH_CURRENT_LEAGUE" with actual league name

# 3. Test configuration
uv run python config.py

# 4. Run collection scripts
uv run python collect_poeninja_samples.py --game poe1
```

## Configuration Module (`config.py`)

### Features

✅ **Type-safe** - Uses dataclasses for strong typing
✅ **Validated** - Checks for required fields and valid values
✅ **Clear errors** - Helpful messages if config is missing or invalid
✅ **Singleton pattern** - Config loaded once, cached for all scripts
✅ **Easy to use** - Simple `get_config()` function

### Usage in Scripts

```python
from config import get_config

CONFIG = get_config()

# Access configuration
leagues = CONFIG.poe1.leagues
base_url = CONFIG.poeninja.base_url_poe1
rate_limit = CONFIG.poeninja.rate_limit_delay
```

### Configuration Structure

```python
@dataclass
class Config:
    poe1: LeagueConfig           # PoE1 leagues
    poe2: LeagueConfig           # PoE2 leagues
    poeninja: PoeNinjaConfig     # poe.ninja API settings
    trade_api: TradeAPIConfig    # Trade API settings
    poedb: PoeDBConfig           # PoeDB/Poe2DB settings
```

## Configuration File (`config.json`)

### Required Fields

```json
{
  "poe1": {
    "current_temp_league": "Necropolis",
    "leagues": ["Standard", "Necropolis"],
    "note": "..."
  },
  "poe2": {
    "current_temp_league": null,
    "leagues": ["Standard"],
    "note": "..."
  },
  "poeninja": {
    "rate_limit_delay": 1.0,
    "base_url_poe1": "https://poe.ninja/poe1/api/economy/stash/current",
    "base_url_poe2": "https://poe.ninja/poe2/api/economy/stash/current",
    "categories": [...]
  },
  "trade_api": {...},
  "poedb": {...}
}
```

### Finding League Names

1. Visit **https://poe.ninja/**
2. Check the league selector dropdown
3. Copy the exact league name (case-sensitive)

Recent league examples:
- "Necropolis" (3.24)
- "Affliction" (3.23)
- "Ancestor" (3.22)
- "Crucible" (3.21)

### Validation

The config module validates:
- ✅ `config.json` exists
- ✅ All required fields present
- ✅ No placeholder values (e.g., "REPLACE_WITH_CURRENT_LEAGUE")
- ✅ Leagues are not empty
- ✅ Rate limits are positive

### Error Messages

**Missing config:**
```
❌ ERROR: config.json not found!

📋 Setup instructions:
   1. Copy the example config:
      cp config.example.json config.json
   2. Edit config.json and update league names
   3. Visit https://poe.ninja/ to find current league name
```

**Placeholder values:**
```
❌ ERROR: Please update config.json with the current PoE1 league name!

📋 Steps:
   1. Visit https://poe.ninja/
   2. Check the league selector dropdown
   3. Update config.json with the exact league name (case-sensitive)

   Recent examples: 'Necropolis', 'Affliction', 'Ancestor', 'Crucible'
```

## Testing Configuration

```bash
# Test config loading
cd backend/scripts
uv run python config.py
```

**Expected output:**
```
📋 Configuration loaded successfully!

PoE1 Leagues: Standard, Necropolis
  Current: Necropolis

PoE2 Leagues: Standard

poe.ninja rate limit: 1.0s between requests
Trade API rate limit: 2.0s between requests
```

## Updating Configuration

When a new league launches:

1. Edit `backend/scripts/config.json`
2. Update `poe1.current_temp_league`
3. Update `poe1.leagues` array
4. Run `uv run python config.py` to verify

## Git Ignore

The `config.json` file is gitignored, so your local configuration won't be committed to the repository. This allows each developer to have their own settings.

---

**Created:** 2025-11-18
**Epic:** 1.2 - Upstream Data Sample Collection
