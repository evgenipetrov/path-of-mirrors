"""Tests for Modifier value object."""

from decimal import Decimal

import pytest

from src.contexts.core.domain.modifier import Modifier, ModifierType


class TestModifierCreation:
    """Test basic Modifier creation."""

    def test_create_explicit_modifier(self):
        """Test creating a simple explicit modifier."""
        mod = Modifier(
            type=ModifierType.EXPLICIT,
            text="+21% to Lightning Resistance",
            values=(Decimal("21"),),
        )

        assert mod.type == ModifierType.EXPLICIT
        assert mod.text == "+21% to Lightning Resistance"
        assert mod.values == (Decimal("21"),)
        assert mod.tier is None

    def test_create_implicit_modifier_with_tier(self):
        """Test creating an implicit modifier with tier."""
        mod = Modifier(
            type=ModifierType.IMPLICIT,
            text="Regenerate 2.2 Life per second",
            values=(Decimal("2.2"),),
            tier="T1",
        )

        assert mod.type == ModifierType.IMPLICIT
        assert mod.text == "Regenerate 2.2 Life per second"
        assert mod.values == (Decimal("2.2"),)
        assert mod.tier == "T1"

    def test_create_crafted_modifier(self):
        """Test creating a crafted modifier."""
        mod = Modifier(
            type=ModifierType.CRAFTED,
            text="+32 to maximum Life",
            values=(Decimal("32"),),
        )

        assert mod.type == ModifierType.CRAFTED
        assert mod.text == "+32 to maximum Life"
        assert mod.values == (Decimal("32"),)

    def test_modifier_immutable(self):
        """Test that modifiers are immutable."""
        mod = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )

        with pytest.raises(Exception):  # dataclass frozen error
            mod.text = "Different text"

        with pytest.raises(Exception):
            mod.values = (Decimal("30"),)


class TestModifierValidation:
    """Test Modifier validation rules."""

    def test_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            Modifier(
                type=ModifierType.EXPLICIT,
                text="",
                values=(Decimal("20"),),
            )

    def test_empty_values_raises_error(self):
        """Test that empty values raises ValueError."""
        with pytest.raises(ValueError, match="must have at least one value"):
            Modifier(
                type=ModifierType.EXPLICIT,
                text="+20 to Intelligence",
                values=(),
            )

    def test_invalid_tier_format_raises_error(self):
        """Test that invalid tier format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid tier format"):
            Modifier(
                type=ModifierType.EXPLICIT,
                text="+20 to Intelligence",
                values=(Decimal("20"),),
                tier="Invalid",
            )

    def test_valid_tier_formats(self):
        """Test that valid tier formats are accepted."""
        # T1, T2, etc.
        mod1 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
            tier="T1",
        )
        assert mod1.tier == "T1"

        # Unique tier
        mod2 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
            tier="Unique",
        )
        assert mod2.tier == "Unique"


class TestModifierFromText:
    """Test Modifier.from_text() parsing."""

    def test_parse_simple_positive_value(self):
        """Test parsing simple positive value."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+21% to Lightning Resistance",
        )

        assert mod.type == ModifierType.EXPLICIT
        assert mod.text == "+21% to Lightning Resistance"
        assert mod.values == (Decimal("21"),)
        assert mod.tier is None

    def test_parse_decimal_value(self):
        """Test parsing decimal value."""
        mod = Modifier.from_text(
            ModifierType.IMPLICIT,
            "Regenerate 2.2 Life per second",
        )

        assert mod.type == ModifierType.IMPLICIT
        assert mod.values == (Decimal("2.2"),)

    def test_parse_negative_value(self):
        """Test parsing negative value."""
        mod = Modifier.from_text(
            ModifierType.CRAFTED,
            "-5 to Mana Cost of Skills",
        )

        assert mod.values == (Decimal("-5"),)

    def test_parse_range_adds_damage(self):
        """Test parsing range (Adds X to Y Damage)."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "Adds 4 to 6 Physical Damage to Attacks",
        )

        assert mod.values == (Decimal("4"), Decimal("6"))

    def test_parse_multiple_values(self):
        """Test parsing modifier with multiple values."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "Adds 10 to 20 Physical Damage and 5 to 8 Cold Damage",
        )

        assert mod.values == (Decimal("10"), Decimal("20"), Decimal("5"), Decimal("8"))

    def test_parse_boolean_like_no_values(self):
        """Test parsing boolean-like mod with no numeric values."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "Cannot be Frozen",
        )

        # Default to 1 for boolean-like mods
        assert mod.values == (Decimal("1"),)

    def test_parse_poe2_metadata_tags(self):
        """Test parsing PoE2 modifiers with metadata tags."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+11 to [Spirit|Spirit]",
        )

        # Text preserved with tags
        assert mod.text == "+11 to [Spirit|Spirit]"
        assert mod.values == (Decimal("11"),)

    def test_parse_poe2_elemental_resistance(self):
        """Test parsing PoE2 elemental resistance with metadata."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+10% to all [ElementalDamage|Elemental] [Resistances]",
        )

        assert mod.text == "+10% to all [ElementalDamage|Elemental] [Resistances]"
        assert mod.values == (Decimal("10"),)

    def test_parse_real_poe1_examples(self):
        """Test parsing real PoE1 modifier examples from validation."""
        # From Trade API
        mod1 = Modifier.from_text(ModifierType.EXPLICIT, "+20 to Intelligence")
        assert mod1.values == (Decimal("20"),)

        # From poe.ninja builds
        mod2 = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+1 to Level of Socketed Gems",
        )
        assert mod2.values == (Decimal("1"),)

        # From PoB
        mod3 = Modifier.from_text(
            ModifierType.EXPLICIT,
            "44% increased Energy Shield",
        )
        assert mod3.values == (Decimal("44"),)

    def test_parse_real_poe2_examples(self):
        """Test parsing real PoE2 modifier examples from validation."""
        # From poe.ninja builds
        mod1 = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+101 to maximum Life",
        )
        assert mod1.values == (Decimal("101"),)

        # With metadata
        mod2 = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+1 to Maximum [Charges|Endurance Charges]",
        )
        assert mod2.values == (Decimal("1"),)


class TestModifierProperties:
    """Test Modifier convenience properties."""

    def test_value_property_single_value(self):
        """Test .value property for single-value modifier."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+20 to Intelligence",
        )

        assert mod.value == Decimal("20")
        assert mod.value == mod.values[0]

    def test_has_range_false_for_single_value(self):
        """Test has_range is False for single value."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "+20 to Intelligence",
        )

        assert mod.has_range is False
        assert mod.value_min is None
        assert mod.value_max is None

    def test_has_range_true_for_range(self):
        """Test has_range is True for range modifier."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "Adds 4 to 6 Physical Damage",
        )

        assert mod.has_range is True
        assert mod.value_min == Decimal("4")
        assert mod.value_max == Decimal("6")

    def test_has_range_false_for_duplicate_values(self):
        """Test has_range is False when values are identical."""
        mod = Modifier(
            type=ModifierType.EXPLICIT,
            text="Test",
            values=(Decimal("5"), Decimal("5")),
        )

        # Same values = not a range
        assert mod.has_range is False

    def test_value_min_max_for_multi_value(self):
        """Test value_min/max for multi-value modifier."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "Adds 10 to 20 Physical Damage and 5 to 8 Cold Damage",
        )

        assert mod.has_range is True
        assert mod.value_min == Decimal("5")  # Minimum of all values
        assert mod.value_max == Decimal("20")  # Maximum of all values


class TestModifierSerialization:
    """Test Modifier to_dict() and from_dict() serialization."""

    def test_to_dict_simple(self):
        """Test serializing simple modifier to dict."""
        mod = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )

        data = mod.to_dict()

        assert data == {
            "type": "explicit",
            "text": "+20 to Intelligence",
            "values": ["20"],
            "tier": None,
        }

    def test_to_dict_with_tier(self):
        """Test serializing modifier with tier."""
        mod = Modifier(
            type=ModifierType.IMPLICIT,
            text="Regenerate 2.2 Life per second",
            values=(Decimal("2.2"),),
            tier="T1",
        )

        data = mod.to_dict()

        assert data == {
            "type": "implicit",
            "text": "Regenerate 2.2 Life per second",
            "values": ["2.2"],
            "tier": "T1",
        }

    def test_to_dict_range(self):
        """Test serializing range modifier."""
        mod = Modifier.from_text(
            ModifierType.EXPLICIT,
            "Adds 4 to 6 Physical Damage",
        )

        data = mod.to_dict()

        assert data == {
            "type": "explicit",
            "text": "Adds 4 to 6 Physical Damage",
            "values": ["4", "6"],
            "tier": None,
        }

    def test_from_dict_simple(self):
        """Test deserializing simple modifier from dict."""
        data = {
            "type": "explicit",
            "text": "+20 to Intelligence",
            "values": ["20"],
            "tier": None,
        }

        mod = Modifier.from_dict(data)

        assert mod.type == ModifierType.EXPLICIT
        assert mod.text == "+20 to Intelligence"
        assert mod.values == (Decimal("20"),)
        assert mod.tier is None

    def test_from_dict_with_tier(self):
        """Test deserializing modifier with tier."""
        data = {
            "type": "implicit",
            "text": "Regenerate 2.2 Life per second",
            "values": ["2.2"],
            "tier": "T1",
        }

        mod = Modifier.from_dict(data)

        assert mod.type == ModifierType.IMPLICIT
        assert mod.text == "Regenerate 2.2 Life per second"
        assert mod.values == (Decimal("2.2"),)
        assert mod.tier == "T1"

    def test_roundtrip_serialization(self):
        """Test that to_dict -> from_dict roundtrip preserves data."""
        original = Modifier(
            type=ModifierType.CRAFTED,
            text="Adds 10 to 20 Physical Damage",
            values=(Decimal("10"), Decimal("20")),
            tier="T2",
        )

        data = original.to_dict()
        restored = Modifier.from_dict(data)

        assert restored.type == original.type
        assert restored.text == original.text
        assert restored.values == original.values
        assert restored.tier == original.tier


class TestModifierTypes:
    """Test all ModifierType enum values."""

    def test_all_modifier_types_valid(self):
        """Test creating modifiers with all modifier types."""
        types = [
            ModifierType.IMPLICIT,
            ModifierType.EXPLICIT,
            ModifierType.CRAFTED,
            ModifierType.ENCHANT,
            ModifierType.FRACTURED,
            ModifierType.CRUCIBLE,
            ModifierType.SCOURGE,
            ModifierType.SYNTHESISED,
        ]

        for mod_type in types:
            mod = Modifier(
                type=mod_type,
                text="Test modifier",
                values=(Decimal("1"),),
            )
            assert mod.type == mod_type

    def test_modifier_type_string_value(self):
        """Test ModifierType string representation."""
        assert str(ModifierType.EXPLICIT) == "explicit"
        assert str(ModifierType.IMPLICIT) == "implicit"
        assert str(ModifierType.CRAFTED) == "crafted"

    def test_modifier_type_from_string(self):
        """Test creating ModifierType from string value."""
        assert ModifierType("explicit") == ModifierType.EXPLICIT
        assert ModifierType("implicit") == ModifierType.IMPLICIT
        assert ModifierType("crafted") == ModifierType.CRAFTED


class TestModifierEquality:
    """Test Modifier equality and hashing."""

    def test_identical_modifiers_equal(self):
        """Test that identical modifiers are equal."""
        mod1 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )
        mod2 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )

        assert mod1 == mod2

    def test_different_values_not_equal(self):
        """Test that modifiers with different values are not equal."""
        mod1 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )
        mod2 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("30"),),
        )

        assert mod1 != mod2

    def test_different_types_not_equal(self):
        """Test that modifiers with different types are not equal."""
        mod1 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )
        mod2 = Modifier(
            type=ModifierType.IMPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )

        assert mod1 != mod2

    def test_modifiers_hashable(self):
        """Test that modifiers can be used in sets/dicts."""
        mod1 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+20 to Intelligence",
            values=(Decimal("20"),),
        )
        mod2 = Modifier(
            type=ModifierType.EXPLICIT,
            text="+30 to Strength",
            values=(Decimal("30"),),
        )

        mod_set = {mod1, mod2}
        assert len(mod_set) == 2
        assert mod1 in mod_set
        assert mod2 in mod_set
