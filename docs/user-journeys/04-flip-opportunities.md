# User Journey 4: Identify Flip Opportunities

**User Story:** "Find underpriced items that popular builds need"

**Priority:** P2 (Core product differentiator)

**Complexity:** High

**Database Required:** YES (build demand patterns, price history)

---

## User Flow

1. User navigates to "Flip Finder" dashboard
2. User selects:
   - Game (PoE1/PoE2)
   - League
   - Budget range (e.g., "10-100 chaos investment")
   - Time investment (e.g., "quick flips" vs "hold for profit")
3. System shows:
   - Current flip opportunities (sorted by profit potential)
   - Item demand score (how many builds want this)
   - Expected profit margin
   - Time to sell estimate
   - Risk level (market volatility)
4. User clicks on opportunity to see:
   - Which builds want this item
   - Comparable listings (why this is underpriced)
   - Price history chart
   - Recommended flip price
5. User buys item and relists at suggested price

---

## Technical Architecture

### Frontend Components

```
frontend/src/routes/flip-finder/
├── index.tsx                    # Main dashboard
├── components/
│   ├── FlipOpportunities.tsx    # List of current opportunities
│   ├── ItemDemandChart.tsx      # Demand over time
│   ├── PriceHistoryChart.tsx    # Price trends
│   ├── BuildDemandBreakdown.tsx # Which builds want this
│   ├── MarketAnalysis.tsx       # Supply/demand metrics
│   └── RiskIndicator.tsx        # Volatility and risk
```

### Backend Components

```
backend/src/contexts/
├── market/                      # NEW CONTEXT
│   ├── domain/
│   │   ├── flip_opportunity.py  # Flip opportunity value object
│   │   ├── market_snapshot.py   # Price/supply data point
│   │   └── item_demand.py       # Build demand aggregation
│   ├── ports/
│   │   └── repository.py        # Persistence interfaces
│   ├── adapters/
│   │   └── postgres_repository.py
│   ├── services/
│   │   ├── demand_analyzer.py   # Analyze build popularity
│   │   ├── price_analyzer.py    # Detect underpriced items
│   │   ├── flip_finder.py       # Find opportunities
│   │   └── market_scanner.py    # Continuous market monitoring
│   └── api/
│       └── routes.py            # GET /api/market/flip-opportunities
│
└── analytics/                   # NEW CONTEXT
    ├── services/
    │   ├── build_clustering.py  # Group similar builds
    │   └── demand_aggregator.py # Calculate item demand from builds
```

---

## API Contract

### Request

**Endpoint:** `GET /api/market/flip-opportunities`

**Query Parameters:**

```python
{
  "game": str,                   # "poe1" or "poe2"
  "league": str,                 # "Affliction", "Standard"
  "min_investment": float,       # e.g., 10.0 (min chaos to invest)
  "max_investment": float,       # e.g., 100.0 (max chaos to invest)
  "min_profit": float,           # e.g., 20.0 (min profit in chaos)
  "min_demand_score": float,     # e.g., 50.0 (popularity threshold)
  "risk_tolerance": str,         # "low", "medium", "high"
  "flip_speed": str,             # "quick" (<1 day), "medium" (1-3 days), "slow" (>3 days)
  "sort_by": str,                # "profit", "profit_margin", "demand", "risk"
  "limit": int                   # Default 50, max 200
}
```

### Response

```json
{
  "opportunities": [
    {
      "id": "opp_abc123",
      "item": {
        "id": "item_xyz789",
        "name": "Rare Amulet",
        "base_type": "Amber Amulet",
        "stats": {
          "life": 75,
          "fire_res": 42,
          "cold_res": 38,
          "strength": 25
        },
        "current_listing": {
          "price_chaos": 25.0,
          "seller": "PlayerName",
          "whisper": "@PlayerName ...",
          "listed_at": "2025-01-19T14:30:00Z"
        }
      },
      "analysis": {
        "demand_score": 85.0,        // 0-100 scale
        "builds_wanting": 127,       // Number of builds this would upgrade
        "market_price": 45.0,        // Expected market price
        "suggested_flip_price": 42.0, // Recommended relist price
        "expected_profit": 17.0,     // After fees
        "profit_margin": 68.0,       // Percentage
        "time_to_sell_hours": 6,     // Estimated
        "risk_level": "low",         // "low", "medium", "high"
        "confidence": 0.87           // 0-1, model confidence
      },
      "demand_breakdown": {
        "by_archetype": {
          "RF Juggernaut": 45,
          "Cold DoT Occultist": 32,
          "Generic Life Build": 50
        },
        "by_stat_need": {
          "life": 95,                // 95 builds need more life
          "fire_res": 78,
          "cold_res": 65
        }
      },
      "market_context": {
        "similar_listings_count": 8,
        "cheapest_comparable": 40.0,
        "most_expensive_comparable": 55.0,
        "supply_level": "low",       // "very_low", "low", "medium", "high"
        "demand_trend": "increasing", // "decreasing", "stable", "increasing"
        "price_volatility": 0.15     // 0-1, lower is more stable
      }
    }
    // ... more opportunities
  ],
  "market_summary": {
    "total_opportunities": 156,
    "avg_profit": 23.5,
    "avg_profit_margin": 45.0,
    "total_potential_profit": 3666.0,
    "market_activity": "high",
    "last_updated": "2025-01-19T15:00:00Z"
  }
}
```

---

## Core Components

### 1. Build Clustering (`analytics/services/build_clustering.py`)

**Purpose:** Group builds with similar item requirements

```python
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

def cluster_builds_by_needs(builds: list[Build]) -> dict:
    """Cluster builds by their item stat requirements.

    Uses DBSCAN clustering on stat vectors.

    Returns:
        {
            "clusters": [
                {
                    "id": "cluster_1",
                    "archetype": "Life + Resistance",
                    "build_count": 145,
                    "avg_stats": {...},
                    "common_items": [...]
                }
            ],
            "build_to_cluster": {"build_id": "cluster_1", ...}
        }
    """
    # Extract stat requirements from each build
    stat_vectors = []
    build_ids = []

    for build in builds:
        stats = extract_stat_requirements(build)
        stat_vectors.append([
            stats.get("life", 0),
            stats.get("es", 0),
            stats.get("total_res", 0),
            stats.get("str", 0),
            stats.get("dex", 0),
            stats.get("int", 0),
            # ... more stats
        ])
        build_ids.append(build.id)

    # Normalize
    scaler = StandardScaler()
    normalized = scaler.fit_transform(stat_vectors)

    # Cluster
    clustering = DBSCAN(eps=0.5, min_samples=5).fit(normalized)
    labels = clustering.labels_

    # Group builds by cluster
    clusters = defaultdict(list)
    for build_id, label in zip(build_ids, labels):
        if label != -1:  # -1 is noise
            clusters[f"cluster_{label}"].append(build_id)

    # Analyze each cluster
    cluster_info = []
    for cluster_id, build_ids in clusters.items():
        cluster_builds = [b for b in builds if b.id in build_ids]
        cluster_info.append({
            "id": cluster_id,
            "archetype": identify_archetype(cluster_builds),
            "build_count": len(build_ids),
            "avg_stats": calculate_avg_stats(cluster_builds),
            "common_items": find_common_items(cluster_builds)
        })

    return {
        "clusters": cluster_info,
        "build_to_cluster": dict(zip(build_ids, labels))
    }

def extract_stat_requirements(build: Build) -> dict:
    """Extract what stats a build needs (gaps in current gear)."""
    # Look at build's current totals
    current = {
        "life": build.life or 0,
        "es": build.energy_shield or 0,
        # ... more stats from build
    }

    # Determine what's missing (vs ideal)
    ideal = get_ideal_stats_for_class(build.character_class, build.ascendancy)

    gaps = {}
    for stat, ideal_val in ideal.items():
        current_val = current.get(stat, 0)
        if current_val < ideal_val:
            gaps[stat] = ideal_val - current_val

    return gaps
```

---

### 2. Demand Analyzer (`market/services/demand_analyzer.py`)

**Purpose:** Calculate demand score for items

```python
def calculate_item_demand(
    item_stats: dict,
    build_clusters: dict,
    popular_builds: list[Build]
) -> dict:
    """Calculate how many builds would want this item.

    Args:
        item_stats: Item's stats (life, res, etc.)
        build_clusters: Clustered builds from analytics
        popular_builds: Top builds from poe.ninja

    Returns:
        {
            "demand_score": 85.0,
            "builds_wanting": 127,
            "by_archetype": {...},
            "by_stat": {...}
        }
    """
    builds_wanting = []
    by_archetype = defaultdict(int)
    by_stat = defaultdict(int)

    for build in popular_builds:
        # Check if this item would upgrade the build
        stat_gaps = extract_stat_requirements(build)

        improvement_score = 0
        stats_improved = []

        for stat, gap in stat_gaps.items():
            if stat in item_stats and item_stats[stat] > 0:
                # This item helps fill this gap
                improvement = min(item_stats[stat], gap)
                improvement_score += improvement
                stats_improved.append(stat)
                by_stat[stat] += 1

        # If item improves build significantly, count it
        if improvement_score > MIN_IMPROVEMENT_THRESHOLD:
            builds_wanting.append(build.id)
            archetype = identify_archetype([build])
            by_archetype[archetype] += 1

    # Normalize demand score (0-100)
    demand_score = min(100, (len(builds_wanting) / len(popular_builds)) * 100)

    return {
        "demand_score": demand_score,
        "builds_wanting": len(builds_wanting),
        "by_archetype": dict(by_archetype),
        "by_stat": dict(by_stat)
    }
```

---

### 3. Price Analyzer (`market/services/price_analyzer.py`)

**Purpose:** Detect underpriced items

```python
def detect_underpriced_items(
    trade_results: list[dict],
    demand_data: dict
) -> list[dict]:
    """Find items priced below their demand-adjusted market value.

    Args:
        trade_results: Current listings from Trade API
        demand_data: Demand scores for item types

    Returns:
        List of underpriced items with flip potential
    """
    underpriced = []

    for item in trade_results:
        # Calculate expected price based on stats and demand
        expected_price = estimate_market_price(item, demand_data)

        # Current listing price
        current_price = item["price_chaos"]

        # Is it underpriced?
        if current_price < expected_price * 0.7:  # >30% discount
            profit_potential = expected_price - current_price
            profit_margin = (profit_potential / current_price) * 100

            underpriced.append({
                "item": item,
                "current_price": current_price,
                "expected_price": expected_price,
                "profit_potential": profit_potential,
                "profit_margin": profit_margin,
                "demand_score": demand_data.get(item["base_type"], 0)
            })

    # Sort by profit potential
    return sorted(underpriced, key=lambda x: x["profit_potential"], reverse=True)

def estimate_market_price(item: dict, demand_data: dict) -> float:
    """Estimate item's market value based on stats and demand.

    Uses regression model trained on historical price data.
    """
    # Feature vector: item stats + demand score
    features = {
        "life": item["stats"].get("life", 0),
        "total_res": sum([
            item["stats"].get("fire_res", 0),
            item["stats"].get("cold_res", 0),
            item["stats"].get("lightning_res", 0)
        ]),
        "es": item["stats"].get("energy_shield", 0),
        "demand_score": demand_data.get(item["base_type"], 50),
        # ... more features
    }

    # Use trained model to predict price
    predicted_price = price_model.predict([feature_vector])

    return predicted_price[0]
```

---

### 4. Market Scanner (`market/services/market_scanner.py`)

**Purpose:** Continuously scan market for opportunities

```python
async def scan_market_continuously(
    game: str,
    league: str,
    scan_interval_minutes: int = 15
):
    """Background task to continuously scan for flip opportunities.

    Runs periodically (e.g., every 15 minutes) and updates database.
    """
    while True:
        try:
            # 1. Query trade API for recent listings
            recent_items = await fetch_recent_listings(game, league)

            # 2. Calculate demand scores
            popular_builds = await get_popular_builds(game, league)
            demand_scores = calculate_bulk_demand(recent_items, popular_builds)

            # 3. Detect underpriced items
            opportunities = detect_underpriced_items(recent_items, demand_scores)

            # 4. Save to database
            await save_opportunities(opportunities)

            # 5. Clean up old opportunities (>24 hours)
            await cleanup_stale_opportunities()

            logger.info(f"Found {len(opportunities)} flip opportunities")

        except Exception as e:
            logger.error(f"Market scan failed: {e}")

        # Wait before next scan
        await asyncio.sleep(scan_interval_minutes * 60)
```

---

## Database Schema

### Tables Needed

```sql
-- Build popularity tracking
CREATE TABLE build_snapshots (
    id UUID PRIMARY KEY,
    game VARCHAR(10),
    league VARCHAR(100),
    character_class VARCHAR(50),
    ascendancy VARCHAR(50),
    level INT,
    stats JSONB,
    items JSONB,
    popularity_rank INT,        -- Ladder position
    snapshot_date TIMESTAMPTZ,
    source VARCHAR(20)          -- "poeninja", "pob_trends"
);

CREATE INDEX idx_build_snapshots_game_league ON build_snapshots(game, league);
CREATE INDEX idx_build_snapshots_date ON build_snapshots(snapshot_date DESC);

-- Item demand aggregation
CREATE TABLE item_demand (
    id UUID PRIMARY KEY,
    game VARCHAR(10),
    league VARCHAR(100),
    base_type VARCHAR(200),
    stat_profile JSONB,         -- Which stats make it desirable
    demand_score FLOAT,         -- 0-100
    builds_wanting INT,
    calculated_at TIMESTAMPTZ,

    UNIQUE(game, league, base_type, stat_profile)
);

CREATE INDEX idx_item_demand_score ON item_demand(demand_score DESC);

-- Price history
CREATE TABLE price_history (
    id UUID PRIMARY KEY,
    game VARCHAR(10),
    league VARCHAR(100),
    base_type VARCHAR(200),
    stat_profile JSONB,
    price_chaos FLOAT,
    listing_count INT,
    snapshot_date TIMESTAMPTZ
);

CREATE INDEX idx_price_history_date ON price_history(base_type, snapshot_date DESC);

-- Flip opportunities (cached results)
CREATE TABLE flip_opportunities (
    id UUID PRIMARY KEY,
    game VARCHAR(10),
    league VARCHAR(100),
    item_data JSONB,            -- Full item details
    current_price FLOAT,
    expected_price FLOAT,
    profit_potential FLOAT,
    demand_score FLOAT,
    risk_level VARCHAR(20),
    confidence FLOAT,
    discovered_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,     -- When listing likely sold

    INDEX idx_flip_profit(profit_potential DESC),
    INDEX idx_flip_discovered(discovered_at DESC)
);
```

---

## Data Pipeline

### Continuous Data Flow

```
┌─────────────────┐
│  poe.ninja API  │
│  (Popular builds)│
└────────┬────────┘
         │
         ├─→ [Ingest] → build_snapshots
         │
         ├─→ [Cluster] → Build archetypes
         │
         └─→ [Analyze] → item_demand
                              │
                              ↓
         ┌────────────────────┴──────┐
         │                           │
┌────────▼────────┐         ┌───────▼────────┐
│  Trade API      │         │  item_demand   │
│  (Live listings)│         │  (Stored)      │
└────────┬────────┘         └───────┬────────┘
         │                          │
         └──────────┬───────────────┘
                    │
           [Compare & Detect]
                    │
                    ↓
         ┌──────────────────┐
         │flip_opportunities│
         │     (Cached)     │
         └──────────────────┘
                    │
                    ↓
         ┌──────────────────┐
         │   API Response   │
         │   (to Frontend)  │
         └──────────────────┘
```

---

## Implementation Sequence

### Phase 1: Data Collection (Week 1-2)
1. ✅ Build poe.ninja scraper
2. ✅ Create build_snapshots table
3. ✅ Ingest top 1000 builds per league
4. ✅ Implement build clustering
5. ✅ Test with manual queries

### Phase 2: Demand Analysis (Week 2-3)
6. ✅ Implement demand analyzer
7. ✅ Create item_demand table
8. ✅ Calculate demand for common item types
9. ✅ Validate demand scores manually

### Phase 3: Price Analysis (Week 3-4)
10. ✅ Create price_history table
11. ✅ Start collecting price snapshots
12. ✅ Train price prediction model
13. ✅ Implement underpriced detection

### Phase 4: Market Scanner (Week 4)
14. ✅ Implement continuous scanner
15. ✅ Create flip_opportunities table
16. ✅ Build API endpoint
17. ✅ Add caching and rate limiting

### Phase 5: Frontend (Week 5)
18. ✅ Build flip finder dashboard
19. ✅ Add charts and visualizations
20. ✅ Implement filters and sorting

---

## Machine Learning Components

### Price Prediction Model

**Training data:**
- Historical price_history records
- Item stats (life, res, etc.)
- Demand scores
- Supply levels
- Time of day/week (seasonal effects)

**Model:** Random Forest Regressor or Gradient Boosting

**Features:**
```python
features = [
    "life", "es", "mana",
    "fire_res", "cold_res", "lightning_res", "chaos_res",
    "total_res", "str", "dex", "int",
    "demand_score", "supply_level",
    "day_of_week", "hour_of_day",
    "item_level", "is_influenced"
    # ... ~30 features total
]
```

**Target:** `price_chaos`

---

## Performance Considerations

**Challenge:** Analyzing thousands of items continuously

**Solutions:**

1. **Batch processing** - Process items in batches of 100-500
2. **Caching** - Cache demand scores for item types (refresh hourly)
3. **Incremental updates** - Only reanalyze changed items
4. **Database indexes** - Optimize queries with proper indexes
5. **Background jobs** - Use Celery/ARQ for heavy processing

---

## Risks and Mitigations

### Risk 1: Market Manipulation
**Risk:** Bots might abuse flip finder to corner markets

**Mitigation:**
- Rate limit API
- Add randomness to opportunity detection
- Don't show all opportunities (sample)
- Delay updates (15-30 min lag)

### Risk 2: Stale Data
**Risk:** Opportunities already bought by time user sees them

**Mitigation:**
- Show "last updated" timestamp
- Mark opportunities as "likely sold" after N hours
- Verify item still available before showing

### Risk 3: Inaccurate Predictions
**Risk:** Price model is wrong, users lose money

**Mitigation:**
- Show confidence scores
- Conservative profit estimates
- Risk indicators
- Disclaimer: "Not financial advice"

---

## Future Enhancements

1. **Crafting opportunities** - Items that can be profitably crafted
2. **Bulk flipping** - Buy 10 similar items, flip all
3. **Portfolio tracking** - Track user's flip performance
4. **Alerts** - Notify when great opportunity appears
5. **Historical analysis** - "This would have made 50ex last league"

---

## Dependencies

**New dependencies:**
- `scikit-learn` - Machine learning (clustering, regression)
- `pandas` - Data analysis
- `celery` or `arq` - Background job queue
- `redis` - Caching and job queue backend

**External APIs:**
- poe.ninja API (build data, economy data)
- pathofexile.com/trade API (reused from Journey 1)

**Database:** PostgreSQL with JSONB (already have)
