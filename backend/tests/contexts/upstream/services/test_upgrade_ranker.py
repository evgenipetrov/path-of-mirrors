"""Tests for upgrade ranking service."""

from src.contexts.upstream.services.upgrade_ranker import (
    DEFAULT_STAT_WEIGHTS,
    UpgradeScore,
    calculate_stat_improvements,
    calculate_upgrade_score,
    calculate_value_score,
    compare_items,
    rank_upgrades,
)


class TestCalculateStatImprovements:
    """Test calculating stat improvements."""

    def test_simple_improvement(self):
        """Test calculating improvement for single stat."""
        current = {"life": 60}
        candidate = {"life": 80}

        improvements = calculate_stat_improvements(current, candidate)

        assert improvements["life"] == 20

    def test_multiple_improvements(self):
        """Test multiple stat improvements."""
        current = {"life": 60, "fire_res": 30}
        candidate = {"life": 80, "fire_res": 45}

        improvements = calculate_stat_improvements(current, candidate)

        assert improvements["life"] == 20
        assert improvements["fire_res"] == 15

    def test_negative_improvement(self):
        """Test when candidate is worse (negative improvement)."""
        current = {"life": 80}
        candidate = {"life": 60}

        improvements = calculate_stat_improvements(current, candidate)

        assert improvements["life"] == -20

    def test_new_stat_on_candidate(self):
        """Test when candidate has stat that current doesn't."""
        current = {"life": 60}
        candidate = {"life": 60, "fire_res": 45}

        improvements = calculate_stat_improvements(current, candidate)

        assert improvements["fire_res"] == 45  # New stat is improvement
        assert "life" not in improvements  # No change, so not in improvements

    def test_missing_stat_on_candidate(self):
        """Test when candidate is missing a stat."""
        current = {"life": 60, "fire_res": 45}
        candidate = {"life": 80}

        improvements = calculate_stat_improvements(current, candidate)

        assert improvements["life"] == 20
        assert improvements["fire_res"] == -45  # Lost stat

    def test_no_changes(self):
        """Test when items are identical."""
        current = {"life": 60, "fire_res": 45}
        candidate = {"life": 60, "fire_res": 45}

        improvements = calculate_stat_improvements(current, candidate)

        assert improvements == {}


class TestCalculateUpgradeScore:
    """Test upgrade score calculation."""

    def test_simple_score(self):
        """Test basic score calculation."""
        current = {"life": 60}
        candidate = {"life": 80}

        # Improvement: +20 life
        # Score: 20 * 1.0 (life weight) = 20
        score = calculate_upgrade_score(current, candidate)

        assert score == 20.0

    def test_multiple_stats_score(self):
        """Test score with multiple stats."""
        current = {"life": 60, "fire_res": 30}
        candidate = {"life": 80, "fire_res": 45}

        # Improvements: +20 life, +15 fire_res
        # Score: (20 * 1.0) + (15 * 0.6) = 29.0
        score = calculate_upgrade_score(current, candidate)

        assert score == 29.0

    def test_negative_score(self):
        """Test that downgrades result in negative score."""
        current = {"life": 80}
        candidate = {"life": 60}

        # Improvement: -20 life
        # Score: -20 * 1.0 = -20
        score = calculate_upgrade_score(current, candidate)

        assert score == -20.0

    def test_custom_weights(self):
        """Test score with custom stat weights."""
        current = {"life": 60}
        candidate = {"life": 80}

        custom_weights = {"life": 2.0}  # Double the default weight

        # Improvement: +20 life
        # Score: 20 * 2.0 = 40
        score = calculate_upgrade_score(current, candidate, custom_weights)

        assert score == 40.0

    def test_unknown_stat_weight(self):
        """Test that unknown stats have zero weight."""
        current = {}
        candidate = {"unknown_stat": 100}

        # Unknown stat has no weight, so score should be 0
        score = calculate_upgrade_score(current, candidate)

        assert score == 0.0


class TestCompareItems:
    """Test item comparison."""

    def test_compare_basic_items(self):
        """Test comparing two simple items."""
        current = {
            "explicit_mods": ["+60 to maximum Life"],
        }
        candidate = {
            "explicit_mods": ["+80 to maximum Life"],
        }

        result = compare_items(current, candidate)

        assert result.score == 20.0
        assert result.improvements["life"] == 20
        assert result.current_stats["life"] == 60
        assert result.candidate_stats["life"] == 80

    def test_compare_with_implicit(self):
        """Test comparing items with implicit mods."""
        current = {
            "implicit_mods": ["+25 to Dexterity"],
            "explicit_mods": ["+60 to maximum Life"],
        }
        candidate = {
            "implicit_mods": ["+25 to Dexterity"],
            "explicit_mods": ["+80 to maximum Life"],
        }

        result = compare_items(current, candidate)

        # Dexterity is the same, only life improved
        assert result.improvements["life"] == 20
        assert "dexterity" not in result.improvements

    def test_compare_with_price(self):
        """Test comparison including price."""
        current = {
            "explicit_mods": ["+60 to maximum Life"],
        }
        candidate = {
            "explicit_mods": ["+80 to maximum Life"],
        }

        result = compare_items(current, candidate, candidate_price=25.0)

        assert result.score == 20.0
        assert result.price_chaos == 25.0

    def test_compare_with_all_res(self):
        """Test that all res bonus is applied correctly."""
        current = {
            "explicit_mods": [
                "+30% to Fire Resistance",
            ],
        }
        candidate = {
            "explicit_mods": [
                "+30% to Fire Resistance",
                "+15% to all Elemental Resistances",
            ],
        }

        result = compare_items(current, candidate)

        # Candidate has +15 to all res, which adds to fire (and creates cold/lightning)
        # Current fire_res: 30
        # Candidate fire_res: 30 + 15 = 45
        # Improvement: +15 fire, +15 cold, +15 lightning
        assert result.improvements["fire_res"] == 15
        assert result.improvements["cold_res"] == 15
        assert result.improvements["lightning_res"] == 15


class TestRankUpgrades:
    """Test ranking multiple upgrade candidates."""

    def test_rank_simple_upgrades(self):
        """Test ranking simple upgrades."""
        current = {
            "explicit_mods": ["+60 to maximum Life"],
        }

        candidates = [
            {"explicit_mods": ["+70 to maximum Life"]},  # +10 life, score 10
            {"explicit_mods": ["+100 to maximum Life"]},  # +40 life, score 40
            {"explicit_mods": ["+80 to maximum Life"]},  # +20 life, score 20
        ]

        results = rank_upgrades(current, candidates)

        # Should be sorted by score (best first)
        assert len(results) == 3
        assert results[0].score == 40.0  # Best
        assert results[1].score == 20.0  # Middle
        assert results[2].score == 10.0  # Worst

    def test_rank_with_prices(self):
        """Test ranking with price information."""
        current = {
            "explicit_mods": ["+60 to maximum Life"],
        }

        candidates = [
            {"explicit_mods": ["+80 to maximum Life"]},  # Score 20
            {"explicit_mods": ["+100 to maximum Life"]},  # Score 40
        ]

        prices = [10.0, 50.0]  # First is better value

        results = rank_upgrades(current, candidates, candidate_prices=prices)

        # Best score still first (not sorted by value)
        assert results[0].score == 40.0
        assert results[0].price_chaos == 50.0

        # But we can check value separately
        assert results[1].score == 20.0
        assert results[1].price_chaos == 10.0

    def test_rank_empty_candidates(self):
        """Test ranking with no candidates."""
        current = {
            "explicit_mods": ["+60 to maximum Life"],
        }

        results = rank_upgrades(current, [])

        assert results == []

    def test_rank_includes_downgrades(self):
        """Test that downgrades (negative scores) are included."""
        current = {
            "explicit_mods": ["+80 to maximum Life"],
        }

        candidates = [
            {"explicit_mods": ["+100 to maximum Life"]},  # +20, score 20
            {"explicit_mods": ["+60 to maximum Life"]},  # -20, score -20
        ]

        results = rank_upgrades(current, candidates)

        assert results[0].score == 20.0  # Upgrade
        assert results[1].score == -20.0  # Downgrade


class TestCalculateValueScore:
    """Test value score calculation."""

    def test_value_score_basic(self):
        """Test basic value score calculation."""
        score = UpgradeScore(
            score=30.0,
            improvements={},
            current_stats={},
            candidate_stats={},
            stat_weights={},
            price_chaos=10.0,
        )

        value = calculate_value_score(score)

        assert value == 3.0  # 30 / 10

    def test_value_score_no_price(self):
        """Test value score when price is None."""
        score = UpgradeScore(
            score=30.0,
            improvements={},
            current_stats={},
            candidate_stats={},
            stat_weights={},
            price_chaos=None,
        )

        value = calculate_value_score(score)

        assert value is None

    def test_value_score_zero_price(self):
        """Test value score with zero price."""
        score = UpgradeScore(
            score=30.0,
            improvements={},
            current_stats={},
            candidate_stats={},
            stat_weights={},
            price_chaos=0.0,
        )

        value = calculate_value_score(score)

        assert value is None  # Avoid division by zero


class TestUpgradeScoreDataclass:
    """Test UpgradeScore dataclass."""

    def test_repr(self):
        """Test string representation."""
        score = UpgradeScore(
            score=29.5,
            improvements={"life": 20},
            current_stats={"life": 60},
            candidate_stats={"life": 80},
            stat_weights=DEFAULT_STAT_WEIGHTS,
            price_chaos=25.0,
        )

        repr_str = repr(score)

        assert "29.5" in repr_str
        assert "25" in repr_str

    def test_get_summary(self):
        """Test human-readable summary."""
        score = UpgradeScore(
            score=29.0,
            improvements={"life": 20, "fire_res": 15},
            current_stats={},
            candidate_stats={},
            stat_weights={},
            price_chaos=25.0,
        )

        summary = score.get_summary()

        assert "29.0" in summary
        assert "chaos" in summary
        assert "25" in summary
        assert "Life" in summary
        assert "Fire Res" in summary or "Fire" in summary
