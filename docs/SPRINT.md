# Sprint: Phase 1 Epic 1.2 - Upstream Data Sample Collection

**Sprint Duration:** 1-2 weeks (8-12 hours)
**Sprint Goal:** Collect representative data samples from all upstream sources to inform core model design
**Phase:** Phase 1 - Upstream Foundation
**Epic:** Epic 1.2 - Upstream Data Sample Collection

---

## Sprint Overview

This sprint focuses on **collecting real-world data samples** from all upstream sources before designing core domain models. This evidence-based approach ensures our canonical models can handle data from poe.ninja, trade APIs, Path of Building, and wiki databases.

**Why this matters:**
- Prevents premature modeling based on assumptions
- Validates that core models work for ALL sources before implementation
- Enables offline development and testing with real data
- Reduces refactoring risk when adding new sources later

**This is a fundamental shift from the original Epic 1.2 plan** which would have implemented HTTP clients first. Instead, we collect samples first, then design models that fit the samples.

---

## Current State

✅ **Already Complete (Epic 1.1):**
- BaseProvider Protocol interface
- Provider factory pattern with stub implementations
- 12 passing tests with 100% coverage
- Upstream context structure (ports, adapters)

🎯 **Epic 1.2 Goal:**
- Collect samples from ALL upstream sources
- Document sample structure and metadata
- Organize samples for model design in Epic 1.3

⏭️ **What Comes After (Epic 1.3):**
- Design core models validated against these samples
- Write validation tests proving models handle all sources

---

## Upstream Sources

### 1. poe.ninja (Priority: P0 - Critical)
**PoE1:** `https://poe.ninja/api/data/`
**PoE2:** `https://poe2.ninja/api/data/` (or similar)

**Categories to sample:**
- Currency
- Fragments
- DivinationCards
- Artifacts
- Oils
- Incubators
- UniqueWeapons
- UniqueArmours
- UniqueAccessories
- UniqueFlasks
- UniqueJewels
- SkillGems
- ClusterJewels
- Maps
- Blighted Maps
- Blight-ravaged Maps
- Invitations
- Scarabs
- Memories
- Essences
- Fossils
- Resonators

**Leagues:** Current league + Standard for both PoE1 and PoE2

### 2. Trade API (Priority: P0 - Critical)
**PoE1:** `https://www.pathofexile.com/api/trade/`
**PoE2:** `https://www.pathofexile.com/api/trade2/` (verify endpoint)

**Sample types:**
- Item search results (various item types)
- Bulk exchange results (currency trading)
- Live search results
- Item details with modifiers

**Leagues:** Current league + Standard

### 3. Path of Building XML (Priority: P1 - Important)
**Source:** User-exported PoB files, pastebin imports

**Sample types:**
- Complete build exports (XML format)
- Character data with items
- Skill trees
- Item configurations

**Note:** This is for Phase 4, but we should collect samples now to validate our core item model can handle PoB format.

### 4. PoeDB/Poe2DB (Priority: P2 - Nice to have)
**PoE1:** `https://poedb.tw/`
**PoE2:** `https://poe2db.tw/`

**Sample types:**
- Base item data
- Modifier pools
- Crafting recipes
- League mechanics data

**Note:** May need scraping or manual collection if no API exists.

---

## Sprint Backlog

### Task 1.2.1: Create Sample Collection Infrastructure 🔧
**Estimated:** 2 hours
**Priority:** P0 (foundation)

**Description:**
Set up the infrastructure for collecting, storing, and documenting data samples.

**Acceptance Criteria:**
- [x] Create `_samples/data/` directory structure
- [x] Create `_samples/data/README.md` documenting:
  - Purpose of samples
  - Directory structure
  - Naming conventions
  - Metadata format
- [x] Create sample collection script template
- [x] Add `.gitignore` rules (don't commit large samples to git)
- [x] Document how to run sample collection

**Directory Structure:**
```
_samples/data/
├── README.md              # Documentation
├── poe1/
│   ├── poeninja/
│   │   ├── meta.json      # Collection metadata
│   │   ├── economy_<league>_<category>.json
│   │   └── builds_<league>.json
│   ├── trade/
│   │   ├── meta.json
│   │   ├── search_<itemtype>.json
│   │   └── bulk_<currency>.json
│   ├── pob/
│   │   ├── meta.json
│   │   └── build_<name>.xml
│   └── poedb/
│       ├── meta.json
│       └── <category>.json
└── poe2/
    ├── poeninja/
    ├── trade/
    ├── pob/
    └── poe2db/
```

**Metadata Format (meta.json):**
```json
{
  "source": "poe.ninja",
  "game": "poe1",
  "collected_at": "2025-11-18T10:30:00Z",
  "collector_version": "1.0",
  "samples": [
    {
      "filename": "economy_standard_currency.json",
      "league": "Standard",
      "category": "Currency",
      "url": "https://poe.ninja/api/data/CurrencyOverview?league=Standard&type=Currency",
      "item_count": 42,
      "collected_at": "2025-11-18T10:30:00Z"
    }
  ]
}
```

---

### Task 1.2.2: Collect poe.ninja Samples (PoE1) 📊
**Estimated:** 2 hours
**Priority:** P0 (critical data source)

**Description:**
Collect economy and build data from poe.ninja for Path of Exile 1.

**Acceptance Criteria:**
- [x] Collect samples from current league (as of November 2025)
- [x] Collect samples from Standard league
- [x] Cover at least these categories:
  - Currency
  - Fragments
  - DivinationCards
  - UniqueWeapons
  - UniqueArmours
  - UniqueAccessories
  - SkillGems
  - Maps
  - Scarabs
  - Essences
  - Fossils
- [x] Save with descriptive filenames
- [x] Document in meta.json

**Implementation Notes:**
- Use `httpx` or `requests` for fetching
- Add rate limiting (1 req/sec to be respectful)
- Log collection progress
- Handle errors gracefully (skip if endpoint fails)

**Sample Script:**
```python
# backend/scripts/collect_poeninja_samples.py
import httpx
import json
from pathlib import Path
from datetime import datetime
import time

LEAGUES = ["Standard", "Settlers"]  # Update with current league
CATEGORIES = ["Currency", "Fragment", "DivinationCard", ...]

async def collect_poeninja_samples():
    base_url = "https://poe.ninja/api/data"
    output_dir = Path("_samples/data/poe1/poeninja")
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = []
    async with httpx.AsyncClient() as client:
        for league in LEAGUES:
            for category in CATEGORIES:
                # Fetch sample
                # Save to file
                # Add to metadata
                time.sleep(1)  # Rate limiting

    # Save metadata
    meta = {
        "source": "poe.ninja",
        "game": "poe1",
        "collected_at": datetime.utcnow().isoformat(),
        "samples": samples
    }
    # Write meta.json
```

---

### Task 1.2.3: Collect poe.ninja Samples (PoE2) 📊
**Estimated:** 1.5 hours
**Priority:** P0 (critical data source)

**Description:**
Collect economy and build data from poe.ninja for Path of Exile 2.

**Acceptance Criteria:**
- [x] Identify correct poe.ninja endpoint for PoE2 (poe2.ninja or different URL)
- [x] Collect samples from current league
- [x] Collect samples from Standard league
- [x] Cover available categories (may differ from PoE1)
- [x] Save with descriptive filenames
- [x] Document in meta.json

**Implementation Notes:**
- PoE2 may have fewer categories than PoE1
- API structure may differ slightly
- Document any differences found

---

### Task 1.2.4: Collect Trade API Samples (PoE1) 🛒
**Estimated:** 2 hours
**Priority:** P0 (critical for Phase 5)

**Description:**
Collect item search and bulk exchange data from official PoE1 trade API.

**Acceptance Criteria:**
- [x] Collect item search results for various item types:
  - Unique items
  - Rare items with mods
  - Currency
  - Maps
  - Gems
- [x] Collect bulk exchange results
- [x] Collect detailed item data (full mod lists)
- [x] Use current league + Standard
- [x] Document in meta.json

**Implementation Notes:**
- Trade API requires rate limiting (check official docs)
- May need to use search IDs → fetch results workflow
- Document rate limits discovered

**API Endpoints:**
```
POST https://www.pathofexile.com/api/trade/search/{league}
GET  https://www.pathofexile.com/api/trade/fetch/{ids}?query={query_id}
POST https://www.pathofexile.com/api/trade/exchange/{league}
```

---

### Task 1.2.5: Collect Trade API Samples (PoE2) 🛒
**Estimated:** 1.5 hours
**Priority:** P0 (critical for Phase 5)

**Description:**
Collect item search and bulk exchange data from official PoE2 trade API.

**Acceptance Criteria:**
- [x] Identify correct trade API endpoint for PoE2
- [x] Collect search results for available item types
- [x] Collect bulk exchange results
- [x] Use current league + Standard
- [x] Document any differences from PoE1 format

---

### Task 1.2.6: Collect Path of Building Samples 🔨
**Estimated:** 1 hour
**Priority:** P1 (needed for Phase 4)

**Description:**
Collect sample Path of Building XML exports to validate item model compatibility.

**Acceptance Criteria:**
- [x] Collect 5-10 PoB XML exports (user builds)
- [x] Cover various build types (different item types)
- [x] Include both PoE1 and PoE2 builds (if PoE2 PoB exists)
- [x] Anonymize if needed (remove account names)
- [x] Document in meta.json

**Sources:**
- Export from Path of Building Community Fork
- Public build pastebins (poe.ninja builds, forums)
- Personal builds (anonymized)

---

### Task 1.2.7: Collect PoeDB/Poe2DB Samples 📚
**Estimated:** 1.5 hours
**Priority:** P2 (reference data)

**Description:**
Collect base item data, modifier pools, and crafting data from wiki databases.

**Acceptance Criteria:**
- [x] Collect base item type data
- [x] Collect modifier/affix pools
- [x] Collect crafting recipe data (if accessible)
- [x] Cover both PoE1 (poedb.tw) and PoE2 (poe2db.tw)
- [x] Document collection method (API or scraping)

**Implementation Notes:**
- Check if APIs exist, otherwise may need scraping
- Focus on structured data (JSON if possible)
- This is reference data, not real-time prices

---

### Task 1.2.8: Document Sample Analysis 📝
**Estimated:** 1.5 hours
**Priority:** P1 (informs Epic 1.3)

**Description:**
Analyze collected samples and document findings to inform core model design.

**Acceptance Criteria:**
- [x] Create `_samples/data/ANALYSIS.md` documenting:
  - Common data structures across sources
  - Differences between PoE1 and PoE2 formats
  - Key fields for canonical models
  - Edge cases discovered
  - Recommendations for Epic 1.3
- [x] Identify minimal common schema for items
- [x] Identify game-specific extensions needed
- [x] Document any surprising findings

**Analysis Questions:**
- What fields are common across all item sources?
- How do modifiers differ between sources?
- What's the best way to represent item identity?
- Do we need separate models for PoE1/PoE2 or can we unify?
- What's the cardinality of each data type (1 item, 100s, 1000s)?

---

## Success Criteria

Epic 1.2 is complete when:

- ✅ We have representative samples from all 4 sources (poe.ninja, trade, PoB, poedb)
- ✅ Samples cover both PoE1 and PoE2 where applicable
- ✅ Samples include current league + Standard
- ✅ All samples are documented with metadata
- ✅ Analysis document identifies common structures and edge cases
- ✅ We can confidently design core models in Epic 1.3 based on this data

---

## Dependencies

### Upstream Dependencies
- Epic 1.1 complete ✅

### Downstream Dependencies (What This Unblocks)
- **Epic 1.3:** Core Domain Model Design (needs samples for validation)
- **Epic 1.4:** Data Mappers (needs samples for testing)
- **Epic 1.5:** HTTP Client Implementation (knows what data to expect)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| poe.ninja rate limiting | Medium | Add delays, collect only essential categories |
| Trade API auth/blocking | High | Use official rate limits, add backoff, document limits |
| PoE2 endpoints unknown | Medium | Research first, fallback to PoE1 structure assumptions |
| PoeDB has no API | Low | Manual collection or scraping as fallback |
| Sample size too large for git | Low | Use .gitignore, document how to regenerate samples |

---

## Technical Decisions

### Why Collect Samples Before Implementation?
- **Evidence-based design:** Real data reveals edge cases assumptions miss
- **Prevents refactoring:** Models designed for all sources from start
- **Enables TDD:** Samples become test fixtures
- **Offline development:** No API dependency during model design

### Why All Sources Now (Not Just poe.ninja)?
- Phase 4 (PoB) and Phase 5 (Trade) will need same core models
- Cheaper to design once correctly than refactor twice
- Trade API shows real item mods (poe.ninja is aggregated)

### Sample Size Strategy
- **Current league + Standard only** (not historical leagues)
- **Top categories only** (not every single category)
- **~5-10 items per category** (representative, not exhaustive)
- **Total ~100-200 sample files** (~50-100MB uncompressed)

### Git Storage Decision
- **DO commit:** Small, representative samples (<1MB each)
- **DON'T commit:** Large dumps (>10MB)
- **DO document:** How to regenerate samples

---

## Sprint Checklist

**Before Starting:**
- [x] Epic 1.1 complete
- [ ] Identify current PoE1 league name
- [ ] Identify current PoE2 league name (if launched)
- [ ] Verify poe.ninja rate limits
- [ ] Verify trade API rate limits

**During Sprint:**
- [ ] Run sample collection scripts
- [ ] Monitor for rate limit issues
- [ ] Document any API changes/surprises
- [ ] Update meta.json after each source
- [ ] Commit samples in batches (per source)

**After Sprint:**
- [ ] All samples collected and documented
- [ ] Analysis document complete
- [ ] Samples validate via smoke test (can load JSON/XML)
- [ ] Archive sprint to `docs/sprints/phase1-epic1.2.md`
- [ ] Create Epic 1.3 sprint plan based on analysis

---

## Resources

### APIs and Documentation
- [poe.ninja API (unofficial docs)](https://poe.ninja/api)
- [PoE Trade API (official)](https://www.pathofexile.com/developer/docs/reference)
- [Path of Building Community Fork](https://github.com/PathOfBuildingCommunity/PathOfBuilding)
- [PoeDB](https://poedb.tw/)
- [Poe2DB](https://poe2db.tw/)

### Project Docs
- [BACKLOG.md - Epic 1.2](../docs/BACKLOG.md)
- [ARCHITECTURE.md - Game Abstraction Layer](../docs/ARCHITECTURE.md#game-abstraction-layer)
- [_samples/README.md](../_samples/README.md) - Reference code samples

---

**Sprint Status:** 📋 Planned
**Created:** 2025-11-18
**Ready to Start:** Yes (Epic 1.1 complete)

**Next Sprint:** Epic 1.3 - Core Domain Model Design (8-10 hours)
