# Sprint: Phase 1 Epic 1.3 - Core Domain Model Design

**Sprint Duration:** 1-2 weeks (10-12 hours)
**Sprint Goal:** Design and validate canonical domain models against collected upstream samples
**Phase:** Phase 1 - Upstream Foundation
**Epic:** Epic 1.3 - Core Domain Model Design

---

## Sprint Overview

This sprint focuses on **designing canonical domain models** that can represent data from all upstream sources (poe.ninja, Trade API, Path of Building, RePoE). We now have ~60MB of real-world samples collected in Epic 1.2 to validate our designs.

**Why this matters:**
- Evidence-based modeling using real data from all sources
- Prevents refactoring when integrating new upstreams
- Ensures PoE1 and PoE2 data can coexist in the same models
- Establishes the foundation for all future features

**This is a design sprint** - no HTTP clients or adapters yet. We're defining the "shape" of our data model and proving it works with collected samples.

---

## Current State

✅ **Already Complete (Epic 1.1):**
- BaseProvider Protocol interface
- Provider factory pattern with stub implementations
- 12 passing tests with 100% coverage
- Upstream context structure (ports, adapters)

✅ **Already Complete (Epic 1.2):**
- **60MB of samples** from all major sources:
  - poe.ninja: 36 samples (PoE1 + PoE2)
  - Trade API: 5 samples + 10 schema files (3.1MB "Rosetta Stone")
  - Path of Building: 4 builds (PoE1 + PoE2)
  - RePoE: 6 files (25MB PoE1 game data)
  - dat-schema: 2 files (3.4MB schemas)
- Comprehensive analysis documented in `_samples/SAMPLE_ANALYSIS.md`

🎯 **Epic 1.3 Goal:**
- Design canonical domain models (Item, Modifier, League, etc.)
- Validate models handle ALL collected samples
- Write transformation contracts for adapters
- Document design decisions and trade-offs

⏭️ **What Comes After (Epic 1.4):**
- Implement poe.ninja adapter (easiest - already normalized)
- Background job system for daily snapshots
- Database schema + migrations

---

## Design Principles

### 1. Game Variant Awareness
**Every entity must be scoped by game variant (PoE1 or PoE2)**

```python
class Item(Base, MappedAsDataclass):
    variant: Mapped[GameVariant]  # POE1 or POE2
    # ... other fields
```

**Rationale:** PoE1 and PoE2 have different:
- Classes/Ascendancies (7 vs 6 classes)
- Skill systems (item-socketed vs skill grid)
- Passive trees (shared vs class-specific)
- Item bases and mods

### 2. Source Agnostic
**Models should accommodate data from ANY upstream source**

Sources we must support:
- **poe.ninja** - Pre-normalized, structured JSON
- **Trade API** - Raw JSON with string-based mods
- **Path of Building** - Text-based XML format
- **RePoE** - Game file extracts (PoE1 only)

### 3. Immutability Where Appropriate
**Snapshots and historical data should be immutable**

- Character builds → `CharacterSnapshot` (immutable, timestamped)
- Trade listings → `TradeListing` (immutable, timestamped)
- Daily economy data → Immutable snapshots

Mutable entities:
- User preferences, notes, saved searches

### 4. Rich Domain Models
**Prefer value objects and domain logic over anemic models**

```python
@dataclass(frozen=True)
class Price:
    amount: Decimal
    currency: CurrencyType

    def to_chaos(self, rates: ExchangeRates) -> Decimal:
        """Domain logic lives in the model."""
        return rates.convert(self.amount, self.currency, CurrencyType.CHAOS)
```

### 5. Dual Representation Strategy
**For items: Store both raw upstream data AND normalized fields**

```python
class Item:
    # Normalized fields (for queries)
    name: str
    base_type: str
    rarity: Rarity
    ilvl: int

    # Raw upstream data (for fidelity)
    upstream_source: str  # "poeninja", "trade_api", "pob"
    upstream_data: JSONB  # Full original JSON/XML
```

**Rationale:**
- Normalized fields enable fast queries
- Raw data preserves fidelity for edge cases
- Can re-normalize later without re-fetching

---

## Sample Coverage Matrix

Our models must handle these real-world samples:

| Source | PoE1 | PoE2 | Use Case |
|--------|------|------|----------|
| poe.ninja builds | ✅ 16 samples | ✅ 18 samples | Character snapshots, passive trees |
| poe.ninja meta | ✅ 1 file | ✅ 1 file | League/class/item enums |
| Trade API samples | ✅ 4 files | ✅ 1 file | Live item listings |
| Trade API schemas | ✅ 5 files | ✅ 5 files | Stat ID ↔ text mappings |
| Path of Building | ✅ 3 builds | ✅ 1 build | Build import/export |
| RePoE | ✅ 6 files (25MB) | ❌ N/A | Base types, mod pools, stat defs |

**Total validation points**: 61 sample files across 6 data sources

---

## Sprint Backlog

### Task 1.3.1: Review Sample Analysis 📚
**Estimated:** 2 hours
**Priority:** P0 (foundation)

**Description:**
Deep dive into `_samples/SAMPLE_ANALYSIS.md` to understand data structures, patterns, and constraints from all sources.

**Key Questions:**
- What fields are common across all sources?
- What fields are source-specific?
- How do PoE1 and PoE2 differ structurally?
- What are the normalization challenges?

**Deliverables:**
- [ ] Read and annotate SAMPLE_ANALYSIS.md
- [ ] List 5-10 key insights per source
- [ ] Identify normalization pain points
- [ ] Document PoE1 vs PoE2 differences

---

### Task 1.3.2: Define Core Entities 🏗️
**Estimated:** 3 hours
**Priority:** P0 (critical path)

**Description:**
Design the core domain entities that represent items, characters, leagues, and pricing.

**Entities to Define:**

#### 1. Item
**Purpose:** Canonical representation of any in-game item

**Fields (preliminary):**
```python
class Item(Base, MappedAsDataclass):
    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid7)
    variant: Mapped[GameVariant] = mapped_column(index=True)

    # Identity
    name: Mapped[str]  # Unique name (or empty for non-uniques)
    base_type: Mapped[str]  # Item base (e.g., "Glorious Plate")
    rarity: Mapped[Rarity]  # NORMAL, MAGIC, RARE, UNIQUE

    # Core properties
    ilvl: Mapped[int]
    corrupted: Mapped[bool] = mapped_column(default=False)

    # Upstream fidelity
    upstream_source: Mapped[str]  # "poeninja", "trade", "pob"
    upstream_id: Mapped[str | None] = mapped_column(default=None)
    upstream_data: Mapped[dict] = mapped_column(type_=JSONB)

    # Timestamps
    collected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
```

**Questions to Answer:**
- How to handle sockets/links? (Separate table? JSONB?)
- How to model modifiers? (Separate entity? Embedded?)
- How to represent item identity? (Hash? Composite key?)

#### 2. Modifier
**Purpose:** Represent item modifiers (affixes, implicits, etc.)

**Fields (preliminary):**
```python
@dataclass(frozen=True)
class Modifier:
    stat_id: str  # From Trade API schemas or RePoE
    value: Decimal | tuple[Decimal, Decimal]  # Single or range
    tier: str | None  # T1, T2, etc. (from RePoE)
    type: ModifierType  # IMPLICIT, EXPLICIT, CRAFTED, etc.
    text: str  # Human-readable (e.g., "+42% to Fire Resistance")
```

**Questions to Answer:**
- Store as separate table or JSONB array?
- How to link stat_id to display text? (Use Trade API schemas? RePoE?)
- How to handle complex mods (conditional, variable)?

#### 3. CharacterSnapshot
**Purpose:** Immutable snapshot of a character build (from poe.ninja)

**Fields (preliminary):**
```python
class CharacterSnapshot(Base, MappedAsDataclass):
    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid7)
    variant: Mapped[GameVariant]

    # Character identity
    name: Mapped[str]
    level: Mapped[int]
    class_name: Mapped[str]
    ascendancy: Mapped[str | None] = mapped_column(default=None)
    league: Mapped[str]

    # Build data
    main_skill: Mapped[str | None] = mapped_column(default=None)
    passive_hashes: Mapped[list[int]] = mapped_column(type_=ARRAY(Integer))

    # Stats (aggregated)
    stats: Mapped[dict] = mapped_column(type_=JSONB)

    # Relationships
    items: Mapped[list["Item"]] = relationship()

    # Metadata
    collected_at: Mapped[datetime]
    upstream_source: Mapped[str] = mapped_column(default="poeninja")
```

#### 4. TradeListing
**Purpose:** Snapshot of an item listed on Trade API

**Fields (preliminary):**
```python
class TradeListing(Base, MappedAsDataclass):
    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid7)
    variant: Mapped[GameVariant]

    # Listing metadata
    upstream_id: Mapped[str]  # Trade API listing hash
    indexed: Mapped[datetime]  # When listed
    collected_at: Mapped[datetime]  # When we scraped
    league: Mapped[str]

    # Pricing
    price_amount: Mapped[Decimal | None] = mapped_column(default=None)
    price_currency: Mapped[str | None] = mapped_column(default=None)

    # Seller (consider privacy/GDPR)
    seller_account: Mapped[str | None] = mapped_column(default=None)

    # Item
    item: Mapped["Item"] = relationship()
```

**Questions to Answer:**
- Store seller info? (Privacy concerns)
- TTL for old listings? (Expire after 1 hour?)
- How to deduplicate listings?

#### 5. League
**Purpose:** Track active leagues per game

**Fields (preliminary):**
```python
class League(Base, MappedAsDataclass):
    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid7)
    variant: Mapped[GameVariant]

    # League identity
    api_id: Mapped[str] = mapped_column(unique=True)  # "Keepers", "Standard"
    display_name: Mapped[str]

    # Temporal
    start: Mapped[datetime]
    end: Mapped[datetime | None] = mapped_column(default=None)  # None = permanent
    is_current: Mapped[bool] = mapped_column(default=False)
    is_hardcore: Mapped[bool] = mapped_column(default=False)
```

**Deliverables:**
- [ ] Define all 5 core entities (Item, Modifier, CharacterSnapshot, TradeListing, League)
- [ ] Document design decisions for each
- [ ] Answer open questions (listed above)
- [ ] Create SQLAlchemy models in `backend/src/contexts/upstream/domain/models.py`

---

### Task 1.3.3: Define Value Objects 💎
**Estimated:** 2 hours
**Priority:** P1 (important)

**Description:**
Design immutable value objects for common concepts like Price, SocketConfig, Requirements.

**Value Objects to Define:**

#### 1. Price
```python
@dataclass(frozen=True)
class Price:
    amount: Decimal
    currency: CurrencyType

    def to_chaos(self, rates: ExchangeRates) -> Decimal:
        """Convert to chaos equivalent using live rates."""
        ...

    @classmethod
    def from_trade_api(cls, data: dict) -> "Price":
        """Parse from Trade API price object."""
        ...
```

#### 2. SocketConfig
```python
@dataclass(frozen=True)
class SocketConfig:
    sockets: list[SocketColor]  # [R, R, G, G, B, B]
    links: int  # Max link group size (6, 5, etc.)

    @property
    def is_six_link(self) -> bool:
        return self.links == 6

    @classmethod
    def from_trade_api(cls, socket_data: list[dict]) -> "SocketConfig":
        """Parse from Trade API socket array."""
        ...

    @classmethod
    def from_pob(cls, socket_text: str) -> "SocketConfig":
        """Parse from PoB socket notation (e.g., 'R-R-G')."""
        ...
```

#### 3. Requirements
```python
@dataclass(frozen=True)
class Requirements:
    level: int | None = None
    strength: int | None = None
    dexterity: int | None = None
    intelligence: int | None = None
```

**Deliverables:**
- [ ] Define Price, SocketConfig, Requirements value objects
- [ ] Add parsing methods for each source (Trade API, PoB, poe.ninja)
- [ ] Write unit tests for value object construction
- [ ] Document in `backend/src/contexts/upstream/domain/value_objects.py`

---

### Task 1.3.4: Design Adapter Contracts 📜
**Estimated:** 2 hours
**Priority:** P0 (critical path)

**Description:**
Define the transformation contracts that each adapter must implement to convert upstream data → canonical models.

**Adapter Contract Structure:**

```python
from typing import Protocol

class ItemAdapter(Protocol):
    """Contract for adapters that transform upstream data to Item entities."""

    def to_item(self, upstream_data: dict, variant: GameVariant) -> Item:
        """
        Transform upstream item data to canonical Item.

        Args:
            upstream_data: Raw JSON/dict from upstream source
            variant: Game variant (POE1 or POE2)

        Returns:
            Canonical Item entity

        Raises:
            ValidationError: If upstream data is invalid
        """
        ...

    def extract_modifiers(self, upstream_data: dict) -> list[Modifier]:
        """Extract modifiers from upstream item data."""
        ...
```

**Adapters to Design Contracts For:**

1. **PoeNinjaAdapter**
   - `to_character_snapshot()` - poe.ninja build → CharacterSnapshot
   - `to_items()` - Extract items from build
   - Complexity: LOW (already normalized)

2. **TradeApiAdapter**
   - `to_trade_listing()` - Trade search result → TradeListing
   - `to_item()` - Trade item → Item
   - `parse_modifiers()` - String mods → Modifier list (use `schema_stats.json`)
   - Complexity: HIGH (string parsing, stat ID lookups)

3. **PathOfBuildingAdapter**
   - `parse_xml()` - XML → dict
   - `to_character_snapshot()` - PoB build → CharacterSnapshot
   - `to_items()` - Text-based items → Item list
   - `parse_item_text()` - Line-based format → structured data
   - Complexity: MEDIUM (text parsing, format differences)

4. **RePoEAdapter**
   - `get_base_type()` - Look up base item metadata
   - `get_mod_info()` - Look up mod tier/weights
   - `translate_stat()` - Stat ID → display text
   - Complexity: LOW (read-only lookups)

**Deliverables:**
- [ ] Define adapter protocols in `backend/src/contexts/upstream/ports/adapters.py`
- [ ] Document transformation rules for each adapter
- [ ] List required helper methods (e.g., `parse_socket_string()`)
- [ ] Identify shared utilities (e.g., stat ID → text translator)

---

### Task 1.3.5: Write Validation Tests ✅
**Estimated:** 3 hours
**Priority:** P0 (validation)

**Description:**
Write tests that prove our models can handle real samples from all sources.

**Test Strategy:**

```python
# tests/contexts/upstream/test_model_validation.py

def test_item_from_poeninja_sample():
    """Validate Item model handles poe.ninja character item."""
    # Load real sample
    with open("_samples/data/poe1/poeninja/builds/keepers/character_000.json") as f:
        data = json.load(f)

    # Extract first item
    item_data = data["build"]["items"][0]

    # Transform (will implement adapter in Epic 1.4)
    item = Item(
        variant=GameVariant.POE1,
        name=item_data.get("name", ""),
        base_type=item_data["baseType"],
        rarity=Rarity.from_string(item_data["rarity"]),
        ilvl=item_data["ilvl"],
        upstream_source="poeninja",
        upstream_data=item_data,
    )

    # Validate
    assert item.variant == GameVariant.POE1
    assert item.base_type == item_data["baseType"]
    # ... more assertions

def test_item_from_trade_api_sample():
    """Validate Item model handles Trade API listing."""
    with open("_samples/data/poe1/trade/keepers/rare_accessory_amulet.json") as f:
        data = json.load(f)

    # Extract first listing
    listing = data["items"]["result"][0]

    # Transform and validate
    # ...

def test_modifier_from_trade_api_with_schema():
    """Validate Modifier parsing using Trade API stat schema."""
    # Load schema (Rosetta Stone)
    with open("_samples/data/poe1/trade/schema_stats.json") as f:
        stats_schema = json.load(f)

    # Load sample item with mods
    # Parse mod string: "+42% to Fire Resistance"
    # Look up stat ID in schema
    # Create Modifier
    # Validate
    # ...
```

**Test Coverage Goals:**
- [ ] ✅ Item from poe.ninja sample
- [ ] ✅ Item from Trade API sample
- [ ] ✅ Item from PoB sample
- [ ] ✅ Modifier parsing with Trade API schema
- [ ] ✅ Modifier parsing with RePoE stat_translations
- [ ] ✅ CharacterSnapshot from poe.ninja
- [ ] ✅ CharacterSnapshot from PoB
- [ ] ✅ TradeListing from Trade API
- [ ] ✅ Price conversion (chaos equivalent)
- [ ] ✅ SocketConfig from all sources

**Deliverables:**
- [ ] 10+ validation tests covering all sources
- [ ] Tests use real samples from `_samples/data/`
- [ ] 100% pass rate (models validated against reality)
- [ ] Document any model adjustments made based on test failures

---

### Task 1.3.6: Document Design Decisions 📝
**Estimated:** 1 hour
**Priority:** P1 (documentation)

**Description:**
Create comprehensive documentation explaining the domain model design, trade-offs, and future considerations.

**Documentation to Create:**

#### 1. Architecture Decision Records (ADRs)

**ADR-001: Dual Representation Strategy (Normalized + Raw)**
- Context: Need to balance query performance with data fidelity
- Decision: Store both normalized fields AND raw upstream JSON
- Consequences: Larger storage, but preserves fidelity and enables re-normalization

**ADR-002: Game Variant Scoping**
- Context: PoE1 and PoE2 have different data structures
- Decision: Every entity has `variant: GameVariant` field
- Consequences: All queries must filter by variant, prevents cross-game pollution

**ADR-003: Immutable Snapshots**
- Context: Historical data should not change
- Decision: CharacterSnapshot and TradeListing are immutable
- Consequences: Simpler reasoning, append-only storage, easier caching

**ADR-004: Modifier Representation**
- Context: Mods differ across sources (structured vs strings)
- Decision: TBD - Need to decide table vs JSONB
- Options:
  - Separate `Modifier` table (normalized, queryable)
  - JSONB array on Item (faster, less joins)

**ADR-005: Trade API Schema as Rosetta Stone**
- Context: Need to translate stat IDs ↔ display text
- Decision: Use Trade API `schema_stats.json` as primary translation layer
- Consequences: Simpler than RePoE, works for PoE2, requires periodic refresh

#### 2. Domain Model Diagram

Create visual diagram showing:
- Core entities (Item, CharacterSnapshot, TradeListing, League)
- Value objects (Price, SocketConfig, Modifier)
- Relationships (1-to-many, many-to-many)
- Upstream sources feeding into models

#### 3. Transformation Guide

Document how each upstream source maps to canonical models:

```markdown
# Transformation Guide

## poe.ninja → CharacterSnapshot

| poe.ninja field | Canonical field | Transformation |
|----------------|----------------|----------------|
| `character.name` | `name` | Direct copy |
| `character.level` | `level` | Direct copy |
| `character.class` | `class_name` | Direct copy |
| `build.passives.hashes` | `passive_hashes` | Direct copy (array) |
| `build.items` | `items` | Transform each via ItemAdapter |

## Trade API → TradeListing

| Trade API field | Canonical field | Transformation |
|----------------|----------------|----------------|
| `id` | `upstream_id` | Direct copy |
| `listing.indexed` | `indexed` | Parse ISO datetime |
| `listing.price.amount` | `price_amount` | Decimal conversion |
| `listing.price.currency` | `price_currency` | Direct copy |
| `item` | `item` | Transform via ItemAdapter |
```

**Deliverables:**
- [ ] 5+ ADRs documenting key decisions
- [ ] Domain model diagram (Mermaid or similar)
- [ ] Transformation guide for each source
- [ ] Save in `docs/architecture/` folder

---

## Success Criteria

**Epic 1.3 is complete when:**

- [x] All 5 core entities defined (Item, Modifier, CharacterSnapshot, TradeListing, League)
- [x] All 3 value objects defined (Price, SocketConfig, Requirements)
- [x] Adapter contracts designed for all 4 sources
- [x] 10+ validation tests pass using real samples
- [x] Models proven to handle PoE1 AND PoE2 data
- [x] Documentation complete (ADRs, diagrams, transformation guide)

**Quality Gates:**
- Models accommodate ALL 61 sample files without errors
- Tests use actual sample data (not mocks)
- Design decisions documented with rationale
- No hard-coded PoE1-specific assumptions

---

## Out of Scope (Defer to Epic 1.4)

The following are explicitly NOT in this sprint:

- ❌ HTTP client implementation
- ❌ Adapter implementation (transformation code)
- ❌ Database migrations
- ❌ Background job system
- ❌ API endpoints
- ❌ Frontend integration

This sprint is **pure design and validation**. Implementation comes next.

---

## Resources

**Sample Data:**
- `_samples/data/` - All collected samples (~60MB)
- `_samples/SAMPLE_ANALYSIS.md` - Preliminary analysis
- `_samples/COLLECTION_STATUS.md` - Sample inventory

**Reference Code:**
- `_samples/code/path-of-mirrors_v0.4/` - Working v0.4 implementation
  - `backend/app/domains/upstream/poetrade/` - Trade API patterns
  - `backend/app/domains/canonical/` - Example canonical models

**External Resources:**
- Trade API schemas: `_samples/data/*/trade/schema_*.json`
- RePoE data: `_samples/data/poe1/repoe/`
- dat-schema: `_samples/data/dat-schema/`

---

## Timeline

**Week 1:**
- Day 1-2: Task 1.3.1 (Sample Analysis Review)
- Day 3-4: Task 1.3.2 (Core Entities)
- Day 5: Task 1.3.3 (Value Objects)

**Week 2:**
- Day 1-2: Task 1.3.4 (Adapter Contracts)
- Day 3-4: Task 1.3.5 (Validation Tests)
- Day 5: Task 1.3.6 (Documentation)

**Total Estimated Hours:** 10-12 hours

---

## Next Sprint Preview (Epic 1.4)

After Epic 1.3 completes, Epic 1.4 will focus on:

1. **Implement poe.ninja Adapter** (easiest first)
   - Transform poe.ninja JSON → CharacterSnapshot + Item
   - Use validated models from Epic 1.3

2. **Database Schema + Migrations**
   - Alembic migrations for all entities
   - Indexes for performance

3. **Background Job: Daily Snapshot**
   - ARQ job to fetch poe.ninja data
   - Store in database

4. **Simple API Endpoint**
   - GET `/api/snapshots?game=poe1&league=Keepers`
   - Return latest character snapshots

**Goal:** End-to-end data flow from poe.ninja → Database → API
