# Phase 1 Epic Sequence (Revised)

This document outlines the revised epic sequence for Phase 1, following a **sample-driven development** approach.

## Why the Change?

**Original Plan:** Implement HTTP clients → Design models → Build mappers → Add persistence

**Problem:** Models designed around one source (poe.ninja) would likely need refactoring when adding trade API, PoB, etc.

**Revised Plan:** Collect samples from ALL sources → Design models that fit ALL samples → Implement clients → Add persistence

**Benefit:** Models are proven to work with all data sources before any implementation investment.

---

## Epic Timeline

### ✅ Epic 1.1: Game Abstraction Layer (5 hours - COMPLETE)

**Deliverables:**
- BaseProvider Protocol interface
- Provider factory pattern
- Stub implementations for PoE1/PoE2
- 12 tests with 100% coverage
- Documentation

**Status:** Complete as of 2025-11-18

---

### 📋 Epic 1.2: Upstream Data Sample Collection (8-12 hours - PLANNED)

**Goal:** Collect representative samples from ALL upstream sources

**Sources:**
1. **poe.ninja** (PoE1 + PoE2)
   - Economy snapshots (currency, uniques, gems, etc.)
   - Build ladders
   - Current league + Standard

2. **Trade API** (PoE1 + PoE2)
   - Item search results
   - Bulk exchange results
   - Detailed item data with modifiers
   - Current league + Standard

3. **Path of Building XML** (PoE1 + PoE2)
   - 5-10 build exports
   - Various item types
   - Character data

4. **PoeDB/Poe2DB** (PoE1 + PoE2)
   - Base item data
   - Modifier pools
   - Crafting recipes

**Deliverables:**
- `_samples/data/` directory with organized samples
- Sample collection scripts
- Metadata documentation (meta.json per source)
- Analysis document identifying common structures

**Tasks:**
1. Create sample collection infrastructure
2. Collect poe.ninja samples (PoE1)
3. Collect poe.ninja samples (PoE2)
4. Collect trade API samples (PoE1)
5. Collect trade API samples (PoE2)
6. Collect PoB XML samples
7. Collect PoeDB/Poe2DB samples
8. Document analysis and findings

---

### 📋 Epic 1.3: Core Domain Model Design (8-10 hours - PLANNED)

**Goal:** Design canonical models validated against ALL collected samples

**Approach:**
- Analyze samples from Epic 1.2
- Identify common fields across all sources
- Design minimal core models that work for everything
- Write validation tests using samples as fixtures

**Deliverables:**
- `backend/src/contexts/upstream/domain/item.py` - CoreItem
- `backend/src/contexts/upstream/domain/league.py` - CoreLeague
- `backend/src/contexts/upstream/domain/modifier.py` - CoreModifier
- `backend/src/contexts/upstream/domain/price.py` - CorePrice
- Validation tests proving samples map to models without data loss
- Documentation of design decisions

**Success Criteria:**
Every sample file from Epic 1.2 can map to core models successfully.

---

### 📋 Epic 1.4: Data Mappers (8-10 hours - PLANNED)

**Goal:** Implement bidirectional mappers between raw data and core models

**Deliverables:**
- `backend/src/contexts/upstream/adapters/mappers/poeninja_mapper.py`
- `backend/src/contexts/upstream/adapters/mappers/trade_mapper.py`
- `backend/src/contexts/upstream/adapters/mappers/pob_mapper.py` (optional)
- Comprehensive tests using samples as input
- Round-trip tests where applicable

**Example Test:**
```python
def test_poeninja_currency_maps_to_core_item():
    with open("_samples/data/poe1/poeninja/economy_standard_currency.json") as f:
        raw = json.load(f)
    items = PoeNinjaMapper.to_core_items(raw)
    assert all(isinstance(item, CoreItem) for item in items)
    assert items[0].name == "Chaos Orb"
```

---

### 📋 Epic 1.5: HTTP Client Implementation (5-8 hours - PLANNED)

**Goal:** Replace sample loading with real HTTP fetching

**Deliverables:**
- `backend/src/contexts/upstream/adapters/poeninja_client.py`
- `backend/src/contexts/upstream/adapters/trade_client.py`
- Replace provider stubs with real implementations
- Retry logic and rate limiting
- Error handling and logging
- Tests using VCR.py or similar (samples as mocks)

**Note:** This epic is now simpler because:
- We know exactly what data to expect (from samples)
- Mappers are already tested and working
- Models are proven to handle the data

---

### 📋 Epic 1.6: Persistence Layer (8-10 hours - PLANNED)

**Goal:** Store core models in PostgreSQL

**Deliverables:**
- Database schema for core models (not raw JSON dumps)
- SQLAlchemy models
- Repository implementations
- Alembic migrations
- Background jobs (ARQ) for scheduled fetching
- 28-day retention cleanup job

**Design:**
- Store normalized core models, not raw API responses
- Partitioned tables by date for time-series data
- Materialized views for trend analysis

---

## Total Timeline

- **Epic 1.1:** 5 hours ✅
- **Epic 1.2:** 8-12 hours 📋
- **Epic 1.3:** 8-10 hours 📋
- **Epic 1.4:** 8-10 hours 📋
- **Epic 1.5:** 5-8 hours 📋
- **Epic 1.6:** 8-10 hours 📋

**Total: 42-55 hours** (original estimate: 40-50 hours)

---

## Key Benefits of Revised Approach

1. **Risk Reduction:** Models proven to work with all sources before implementation
2. **Faster Development:** Offline development with samples, no API dependencies
3. **Better Testing:** Real data as test fixtures from day one
4. **Less Refactoring:** One model design iteration instead of 3-4
5. **Documentation:** Samples serve as living documentation of API structures

---

**Last Updated:** 2025-11-18
**Current Epic:** 1.2 - Upstream Data Sample Collection
**Status:** Ready to start (Epic 1.1 complete)
