"""Tests for stat extraction and normalization."""

from src.contexts.upstream.services.stat_extractor import (
    calculate_total_resistances,
    extract_stats_from_mods,
    extract_stats_from_pob_item,
    get_item_summary,
)


class TestExtractStatsFromMods:
    """Test extracting stats from PoB mod strings."""

    def test_extract_life(self):
        """Test extracting life from mod."""
        mods = ["+80 to maximum Life"]
        stats = extract_stats_from_mods(mods)

        assert stats["life"] == 80

    def test_extract_energy_shield(self):
        """Test extracting energy shield."""
        mods = ["+50 to maximum Energy Shield"]
        stats = extract_stats_from_mods(mods)

        assert stats["energy_shield"] == 50

    def test_extract_resistances(self):
        """Test extracting resistances."""
        mods = [
            "+45% to Fire Resistance",
            "+32% to Cold Resistance",
            "+28% to Lightning Resistance",
        ]
        stats = extract_stats_from_mods(mods)

        assert stats["fire_res"] == 45
        assert stats["cold_res"] == 32
        assert stats["lightning_res"] == 28

    def test_extract_attributes(self):
        """Test extracting attributes."""
        mods = [
            "+30 to Strength",
            "+25 to Dexterity",
            "+40 to Intelligence",
        ]
        stats = extract_stats_from_mods(mods)

        assert stats["strength"] == 30
        assert stats["dexterity"] == 25
        assert stats["intelligence"] == 40

    def test_extract_movement_speed(self):
        """Test extracting movement speed."""
        mods = ["30% increased Movement Speed"]
        stats = extract_stats_from_mods(mods)

        assert stats["movement_speed"] == 30

    def test_extract_attack_speed(self):
        """Test extracting attack speed."""
        mods = ["15% increased Attack Speed"]
        stats = extract_stats_from_mods(mods)

        assert stats["attack_speed"] == 15

    def test_extract_crit_multi(self):
        """Test extracting critical strike multiplier."""
        mods = ["+25% to Global Critical Strike Multiplier"]
        stats = extract_stats_from_mods(mods)

        assert stats["crit_multi"] == 25

    def test_multiple_same_stat(self):
        """Test that multiple mods of same stat are summed."""
        mods = [
            "+60 to maximum Life",
            "+20 to maximum Life",
        ]
        stats = extract_stats_from_mods(mods)

        assert stats["life"] == 80  # Sum of both

    def test_mixed_stats(self):
        """Test extracting multiple different stats."""
        mods = [
            "+80 to maximum Life",
            "+45% to Fire Resistance",
            "+30 to Strength",
            "15% increased Movement Speed",
        ]
        stats = extract_stats_from_mods(mods)

        assert stats["life"] == 80
        assert stats["fire_res"] == 45
        assert stats["strength"] == 30
        assert stats["movement_speed"] == 15

    def test_unrecognized_mod(self):
        """Test that unrecognized mods are ignored."""
        mods = [
            "+80 to maximum Life",
            "Some exotic mod we don't recognize",
            "+45% to Fire Resistance",
        ]
        stats = extract_stats_from_mods(mods)

        # Should only extract recognized stats
        assert stats["life"] == 80
        assert stats["fire_res"] == 45
        assert len(stats) == 2

    def test_empty_mods(self):
        """Test with empty mod list."""
        mods = []
        stats = extract_stats_from_mods(mods)

        assert stats == {}


class TestExtractStatsFromPoBItem:
    """Test extracting stats from PoB item dictionaries."""

    def test_extract_from_item_with_implicit_and_explicit(self):
        """Test extracting from item with both implicit and explicit mods."""
        item = {
            "base_type": "Jade Amulet",
            "implicit_mods": ["+25 to Dexterity"],
            "explicit_mods": [
                "+80 to maximum Life",
                "+45% to Fire Resistance",
                "+32% to Cold Resistance",
            ],
        }

        stats = extract_stats_from_pob_item(item)

        assert stats["dexterity"] == 25
        assert stats["life"] == 80
        assert stats["fire_res"] == 45
        assert stats["cold_res"] == 32

    def test_extract_from_item_explicit_only(self):
        """Test item with only explicit mods."""
        item = {
            "base_type": "Leather Belt",
            "explicit_mods": [
                "+100 to maximum Life",
                "+40 to Strength",
            ],
        }

        stats = extract_stats_from_pob_item(item)

        assert stats["life"] == 100
        assert stats["strength"] == 40

    def test_extract_from_item_no_mods(self):
        """Test item with no mods."""
        item = {
            "base_type": "Simple Item",
        }

        stats = extract_stats_from_pob_item(item)

        assert stats == {}

    def test_extract_from_ring(self):
        """Test extracting from a typical ring."""
        item = {
            "implicit_mods": [],
            "explicit_mods": [
                "+60 to maximum Life",
                "+40% to Fire Resistance",
                "+35% to Cold Resistance",
                "+30 to Strength",
                "+25 to Dexterity",
            ],
        }

        stats = extract_stats_from_pob_item(item)

        assert stats["life"] == 60
        assert stats["fire_res"] == 40
        assert stats["cold_res"] == 35
        assert stats["strength"] == 30
        assert stats["dexterity"] == 25


class TestCalculateTotalResistances:
    """Test resistance and attribute calculations."""

    def test_all_res_bonus_fire(self):
        """Test that all res bonus is applied to fire resistance."""
        stats = {
            "fire_res": 30,
            "all_res": 15,
        }

        updated = calculate_total_resistances(stats)

        assert updated["fire_res"] == 45  # 30 + 15

    def test_all_res_bonus_all_elements(self):
        """Test all res bonus applied to all elemental resistances."""
        stats = {
            "fire_res": 30,
            "cold_res": 20,
            "lightning_res": 25,
            "all_res": 15,
        }

        updated = calculate_total_resistances(stats)

        assert updated["fire_res"] == 45  # 30 + 15
        assert updated["cold_res"] == 35  # 20 + 15
        assert updated["lightning_res"] == 40  # 25 + 15

    def test_all_res_creates_missing_resistances(self):
        """Test that all res creates missing resistance entries."""
        stats = {
            "fire_res": 30,
            "all_res": 15,
        }

        updated = calculate_total_resistances(stats)

        assert updated["fire_res"] == 45
        assert updated["cold_res"] == 15  # Created from all_res
        assert updated["lightning_res"] == 15  # Created from all_res

    def test_all_attributes_bonus(self):
        """Test that all attributes bonus is applied."""
        stats = {
            "strength": 20,
            "dexterity": 15,
            "all_attributes": 10,
        }

        updated = calculate_total_resistances(stats)

        assert updated["strength"] == 30  # 20 + 10
        assert updated["dexterity"] == 25  # 15 + 10
        assert updated["intelligence"] == 10  # Created from all_attributes

    def test_no_bonuses(self):
        """Test with no all_res or all_attributes."""
        stats = {
            "fire_res": 30,
            "strength": 20,
        }

        updated = calculate_total_resistances(stats)

        assert updated["fire_res"] == 30
        assert updated["strength"] == 20


class TestGetItemSummary:
    """Test human-readable item summaries."""

    def test_simple_summary(self):
        """Test summary for simple item."""
        stats = {
            "life": 80,
            "fire_res": 45,
        }

        summary = get_item_summary(stats)

        assert "Life: +80" in summary
        assert "Fire Resistance: +45%" in summary

    def test_empty_stats(self):
        """Test summary for empty stats."""
        stats = {}
        summary = get_item_summary(stats)

        assert summary == "No stats"

    def test_multi_stat_summary(self):
        """Test summary with multiple stats."""
        stats = {
            "life": 80,
            "fire_res": 45,
            "cold_res": 32,
            "strength": 30,
            "movement_speed": 20,
        }

        summary = get_item_summary(stats)

        assert "Life: +80" in summary
        assert "Fire Resistance: +45%" in summary
        assert "Cold Resistance: +32%" in summary
        assert "Strength: +30" in summary
        assert "Movement Speed: +20%" in summary
