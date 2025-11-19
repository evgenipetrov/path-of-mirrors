"""Tests for Item domain model.

Tests cover:
- Item creation with required fields
- JSONB modifier storage
- Nullable fields handling
- Rarity types
- Game context separation
- Unique constraints
- Real-world examples from validation
- Database operations (CRUD)
"""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.core import Item, ItemRarity, Modifier, ModifierType
from src.shared import Game


class TestItemCreation:
    """Test Item entity creation with various configurations."""

    @pytest.mark.asyncio
    async def test_create_basic_item(self, db_session: AsyncSession):
        """Test creating a basic item with minimal required fields."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Iron Ring",
            base_type="Iron Ring",
            rarity=ItemRarity.NORMAL,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.id is not None
        assert item.game == Game.POE1
        assert item.name is None
        assert item.type_line == "Iron Ring"
        assert item.base_type == "Iron Ring"
        assert item.rarity == ItemRarity.NORMAL
        assert item.base_type_id is None  # Not enriched yet

    @pytest.mark.asyncio
    async def test_create_item_with_base_type_id(self, db_session: AsyncSession):
        """Test creating an item with dat-schema base type ID."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Vaal Regalia",
            base_type="Vaal Regalia",
            base_type_id="Metadata/Items/Armours/BodyArmours/BodyInt3",
            rarity=ItemRarity.RARE,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.base_type_id == "Metadata/Items/Armours/BodyArmours/BodyInt3"
        assert item.base_type == "Vaal Regalia"

    @pytest.mark.asyncio
    async def test_create_unique_item(self, db_session: AsyncSession):
        """Test creating a unique item with name."""
        item = Item(
            game=Game.POE1,
            name="Headhunter",
            type_line="Leather Belt",
            base_type="Leather Belt",
            rarity=ItemRarity.UNIQUE,
            item_level=84,
            item_class="Belts",
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.name == "Headhunter"
        assert item.rarity == ItemRarity.UNIQUE
        assert item.item_level == 84
        assert item.item_class == "Belts"

    @pytest.mark.asyncio
    async def test_create_item_with_modifiers(self, db_session: AsyncSession):
        """Test creating an item with JSONB modifier arrays."""
        implicit_mod = Modifier(
            type=ModifierType.IMPLICIT,
            text="+20 to maximum Life",
            values=(Decimal("20"),),
        )
        explicit_mod = Modifier(
            type=ModifierType.EXPLICIT,
            text="+45% to Fire Resistance",
            values=(Decimal("45"),),
        )

        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Coral Ring",
            base_type="Coral Ring",
            rarity=ItemRarity.RARE,
            implicit_mods=[implicit_mod.to_dict()],
            explicit_mods=[explicit_mod.to_dict()],
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert len(item.implicit_mods) == 1
        assert len(item.explicit_mods) == 1
        assert item.implicit_mods[0]["text"] == "+20 to maximum Life"
        assert item.explicit_mods[0]["text"] == "+45% to Fire Resistance"


class TestItemModifiers:
    """Test JSONB modifier storage and retrieval."""

    @pytest.mark.asyncio
    async def test_store_all_modifier_types(self, db_session: AsyncSession):
        """Test storing all modifier types in JSONB columns."""
        item = Item(
            game=Game.POE1,
            name="Test Item",
            type_line="Test Base",
            base_type="Test Base",
            rarity=ItemRarity.RARE,
            implicit_mods=[{"text": "implicit mod", "values": [10]}],
            explicit_mods=[{"text": "explicit mod", "values": [20]}],
            crafted_mods=[{"text": "crafted mod", "values": [30]}],
            enchant_mods=[{"text": "enchant mod", "values": [40]}],
            fractured_mods=[{"text": "fractured mod", "values": [50]}],
            crucible_mods=[{"text": "crucible mod", "values": [60]}],
            scourge_mods=[{"text": "scourge mod", "values": [70]}],
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.implicit_mods[0]["text"] == "implicit mod"
        assert item.explicit_mods[0]["text"] == "explicit mod"
        assert item.crafted_mods[0]["text"] == "crafted mod"
        assert item.enchant_mods[0]["text"] == "enchant mod"
        assert item.fractured_mods[0]["text"] == "fractured mod"
        assert item.crucible_mods[0]["text"] == "crucible mod"
        assert item.scourge_mods[0]["text"] == "scourge mod"

    @pytest.mark.asyncio
    async def test_modifiers_nullable(self, db_session: AsyncSession):
        """Test that all modifier columns are nullable."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Simple Item",
            base_type="Simple Item",
            rarity=ItemRarity.NORMAL,
            # All modifier fields omitted
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.implicit_mods is None
        assert item.explicit_mods is None
        assert item.crafted_mods is None
        assert item.enchant_mods is None
        assert item.fractured_mods is None
        assert item.crucible_mods is None
        assert item.scourge_mods is None

    @pytest.mark.asyncio
    async def test_multiple_modifiers_same_type(self, db_session: AsyncSession):
        """Test storing multiple modifiers of the same type."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Rare Ring",
            base_type="Gold Ring",
            rarity=ItemRarity.RARE,
            explicit_mods=[
                {"text": "+50 to maximum Life", "values": [50]},
                {"text": "+30% to Fire Resistance", "values": [30]},
                {"text": "+25% to Cold Resistance", "values": [25]},
                {"text": "15% increased Rarity of Items found", "values": [15]},
            ],
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert len(item.explicit_mods) == 4
        assert item.explicit_mods[0]["values"] == [50]
        assert item.explicit_mods[3]["values"] == [15]


class TestItemProperties:
    """Test JSONB properties field and other optional fields."""

    @pytest.mark.asyncio
    async def test_store_properties(self, db_session: AsyncSession):
        """Test storing arbitrary properties in JSONB field."""
        item = Item(
            game=Game.POE1,
            name="Test Weapon",
            type_line="Vaal Axe",
            base_type="Vaal Axe",
            rarity=ItemRarity.RARE,
            properties={
                "quality": 20,
                "physical_damage": "120-240",
                "attacks_per_second": 1.2,
                "critical_strike_chance": 5.0,
                "requirements": {
                    "level": 64,
                    "strength": 158,
                    "dexterity": 76,
                },
            },
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.properties["quality"] == 20
        assert item.properties["physical_damage"] == "120-240"
        assert item.properties["requirements"]["level"] == 64

    @pytest.mark.asyncio
    async def test_store_sockets(self, db_session: AsyncSession):
        """Test storing socket configuration in JSONB field."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Vaal Regalia",
            base_type="Vaal Regalia",
            rarity=ItemRarity.RARE,
            sockets={
                "socket_count": 6,
                "links": [[0, 1, 2, 3, 4, 5]],  # 6-link
                "colors": ["R", "R", "G", "G", "B", "B"],
            },
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.sockets["socket_count"] == 6
        assert len(item.sockets["links"][0]) == 6
        assert item.sockets["colors"] == ["R", "R", "G", "G", "B", "B"]

    @pytest.mark.asyncio
    async def test_nullable_optional_fields(self, db_session: AsyncSession):
        """Test that optional fields can be null."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Basic Item",
            base_type="Basic Item",
            rarity=ItemRarity.NORMAL,
            item_level=None,
            item_class=None,
            sockets=None,
            properties=None,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.item_level is None
        assert item.item_class is None
        assert item.sockets is None
        assert item.properties is None


class TestItemRarity:
    """Test item rarity handling."""

    @pytest.mark.asyncio
    async def test_all_rarity_types(self, db_session: AsyncSession):
        """Test creating items with all rarity types."""
        rarities = [
            (ItemRarity.NORMAL, "Normal Item"),
            (ItemRarity.MAGIC, "Magic Item"),
            (ItemRarity.RARE, "Rare Item"),
            (ItemRarity.UNIQUE, "Unique Item"),
        ]

        for rarity, name in rarities:
            item = Item(
                game=Game.POE1,
                name=name if rarity == ItemRarity.UNIQUE else None,
                type_line="Test Base",
                base_type="Test Base",
                rarity=rarity,
            )
            db_session.add(item)

        await db_session.commit()

        result = await db_session.execute(select(Item))
        items = result.scalars().all()
        assert len(items) == 4

        rarity_values = {item.rarity for item in items}
        assert rarity_values == {
            ItemRarity.NORMAL,
            ItemRarity.MAGIC,
            ItemRarity.RARE,
            ItemRarity.UNIQUE,
        }


class TestItemGameContext:
    """Test game context separation."""

    @pytest.mark.asyncio
    async def test_same_item_different_games(self, db_session: AsyncSession):
        """Test that same item can exist in both games."""
        item_poe1 = Item(
            game=Game.POE1,
            name="Tabula Rasa",
            type_line="Simple Robe",
            base_type="Simple Robe",
            rarity=ItemRarity.UNIQUE,
        )
        item_poe2 = Item(
            game=Game.POE2,
            name="Tabula Rasa",
            type_line="Simple Robe",
            base_type="Simple Robe",
            rarity=ItemRarity.UNIQUE,
        )
        db_session.add_all([item_poe1, item_poe2])
        await db_session.commit()

        result = await db_session.execute(select(Item).where(Item.name == "Tabula Rasa"))
        items = result.scalars().all()
        assert len(items) == 2

        games = {item.game for item in items}
        assert games == {Game.POE1, Game.POE2}

    @pytest.mark.asyncio
    async def test_filter_by_game(self, db_session: AsyncSession):
        """Test filtering items by game context."""
        poe1_items = [
            Item(
                game=Game.POE1,
                name=f"Item {i}",
                type_line="Base",
                base_type="Base",
                rarity=ItemRarity.UNIQUE,
            )
            for i in range(3)
        ]
        poe2_items = [
            Item(
                game=Game.POE2,
                name=f"Item {i}",
                type_line="Base",
                base_type="Base",
                rarity=ItemRarity.UNIQUE,
            )
            for i in range(2)
        ]
        db_session.add_all(poe1_items + poe2_items)
        await db_session.commit()

        result = await db_session.execute(select(Item).where(Item.game == Game.POE1))
        poe1_count = len(result.scalars().all())

        result = await db_session.execute(select(Item).where(Item.game == Game.POE2))
        poe2_count = len(result.scalars().all())

        assert poe1_count == 3
        assert poe2_count == 2


class TestItemQueries:
    """Test common item queries using indexes."""

    @pytest.mark.asyncio
    async def test_query_by_base_type(self, db_session: AsyncSession):
        """Test querying items by base type (uses ix_item_game_base_type)."""
        items = [
            Item(
                game=Game.POE1,
                name=None,
                type_line="Leather Belt",
                base_type="Leather Belt",
                rarity=ItemRarity.RARE,
            ),
            Item(
                game=Game.POE1,
                name="Headhunter",
                type_line="Leather Belt",
                base_type="Leather Belt",
                rarity=ItemRarity.UNIQUE,
            ),
            Item(
                game=Game.POE1,
                name=None,
                type_line="Iron Ring",
                base_type="Iron Ring",
                rarity=ItemRarity.NORMAL,
            ),
        ]
        db_session.add_all(items)
        await db_session.commit()

        result = await db_session.execute(
            select(Item).where(
                Item.game == Game.POE1, Item.base_type == "Leather Belt"
            )
        )
        belts = result.scalars().all()
        assert len(belts) == 2

    @pytest.mark.asyncio
    async def test_query_by_rarity(self, db_session: AsyncSession):
        """Test querying items by rarity (uses ix_item_game_rarity)."""
        items = [
            Item(
                game=Game.POE1,
                name=f"Unique {i}",
                type_line="Base",
                base_type="Base",
                rarity=ItemRarity.UNIQUE,
            )
            for i in range(3)
        ]
        items.append(
            Item(
                game=Game.POE1,
                name=None,
                type_line="Base",
                base_type="Base",
                rarity=ItemRarity.RARE,
            )
        )
        db_session.add_all(items)
        await db_session.commit()

        result = await db_session.execute(
            select(Item).where(Item.game == Game.POE1, Item.rarity == ItemRarity.UNIQUE)
        )
        uniques = result.scalars().all()
        assert len(uniques) == 3

    @pytest.mark.asyncio
    async def test_query_by_name(self, db_session: AsyncSession):
        """Test querying items by name (uses ix_item_name)."""
        items = [
            Item(
                game=Game.POE1,
                name="Headhunter",
                type_line="Leather Belt",
                base_type="Leather Belt",
                rarity=ItemRarity.UNIQUE,
            ),
            Item(
                game=Game.POE2,
                name="Headhunter",
                type_line="Leather Belt",
                base_type="Leather Belt",
                rarity=ItemRarity.UNIQUE,
            ),
            Item(
                game=Game.POE1,
                name="Mageblood",
                type_line="Heavy Belt",
                base_type="Heavy Belt",
                rarity=ItemRarity.UNIQUE,
            ),
        ]
        db_session.add_all(items)
        await db_session.commit()

        result = await db_session.execute(select(Item).where(Item.name == "Headhunter"))
        headhunters = result.scalars().all()
        assert len(headhunters) == 2

    @pytest.mark.asyncio
    async def test_query_by_base_type_id(self, db_session: AsyncSession):
        """Test querying items by base_type_id (uses ix_items_base_type_id)."""
        base_id = "Metadata/Items/Armours/BodyArmours/BodyInt3"
        items = [
            Item(
                game=Game.POE1,
                name=None,
                type_line="Vaal Regalia",
                base_type="Vaal Regalia",
                base_type_id=base_id,
                rarity=ItemRarity.RARE,
            ),
            Item(
                game=Game.POE1,
                name="Shavronne's Wrappings",
                type_line="Occultist's Vestment",
                base_type="Occultist's Vestment",
                base_type_id="Metadata/Items/Armours/BodyArmours/BodyInt2",
                rarity=ItemRarity.UNIQUE,
            ),
            Item(
                game=Game.POE1,
                name=None,
                type_line="Vaal Regalia",
                base_type="Vaal Regalia",
                base_type_id=base_id,
                rarity=ItemRarity.RARE,
            ),
        ]
        db_session.add_all(items)
        await db_session.commit()

        result = await db_session.execute(
            select(Item).where(Item.base_type_id == base_id)
        )
        vaal_regalias = result.scalars().all()
        assert len(vaal_regalias) == 2


class TestItemRealExamples:
    """Test with real-world item examples from validation data."""

    @pytest.mark.asyncio
    async def test_unique_weapon_example(self, db_session: AsyncSession):
        """Test creating a unique weapon with mods (Soul Taker example)."""
        item = Item(
            game=Game.POE1,
            name="Soul Taker",
            type_line="Siege Axe",
            base_type="Siege Axe",
            rarity=ItemRarity.UNIQUE,
            item_level=70,
            item_class="One Hand Axes",
            implicit_mods=[
                {"text": "+5 to Armour", "values": [5]},
            ],
            explicit_mods=[
                {"text": "Insufficient Mana doesn't prevent your Melee Attacks", "values": []},
                {"text": "30% reduced Enemy Stun Threshold", "values": [30]},
                {"text": "+50 to Strength", "values": [50]},
            ],
            properties={
                "quality": 20,
                "physical_damage": "150-280",
                "critical_strike_chance": 5.0,
            },
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.name == "Soul Taker"
        assert item.item_class == "One Hand Axes"
        assert len(item.explicit_mods) == 3
        assert item.properties["quality"] == 20

    @pytest.mark.asyncio
    async def test_rare_equipment_example(self, db_session: AsyncSession):
        """Test creating rare equipment with multiple mods."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Hubris Circlet",
            base_type="Hubris Circlet",
            rarity=ItemRarity.RARE,
            item_level=86,
            item_class="Helmets",
            explicit_mods=[
                {"text": "+90 to maximum Life", "values": [90]},
                {"text": "+40% to Fire Resistance", "values": [40]},
                {"text": "+38% to Cold Resistance", "values": [38]},
                {"text": "+25% to Lightning Resistance", "values": [25]},
            ],
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.name is None  # Rare items have no unique name
        assert item.item_level == 86
        assert len(item.explicit_mods) == 4

    @pytest.mark.asyncio
    async def test_poe2_item_example(self, db_session: AsyncSession):
        """Test creating a PoE2 item with Spirit modifier."""
        item = Item(
            game=Game.POE2,
            name=None,
            type_line="Azure Amulet",
            base_type="Azure Amulet",
            rarity=ItemRarity.RARE,
            item_level=45,
            explicit_mods=[
                {"text": "+11 to [Spirit|Spirit]", "values": [11]},  # PoE2 metadata tag
                {"text": "+35 to maximum Life", "values": [35]},
            ],
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.game == Game.POE2
        assert "[Spirit|Spirit]" in item.explicit_mods[0]["text"]


class TestItemRepresentation:
    """Test Item string representation."""

    def test_unique_item_repr(self):
        """Test __repr__ for unique items shows the name."""
        item = Item(
            game=Game.POE1,
            name="Headhunter",
            type_line="Leather Belt",
            base_type="Leather Belt",
            rarity=ItemRarity.UNIQUE,
        )
        repr_str = repr(item)
        assert "Headhunter" in repr_str
        assert "poe1" in repr_str.lower()
        assert "Unique" in repr_str

    def test_rare_item_repr(self):
        """Test __repr__ for rare items shows type_line."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Hubris Circlet",
            base_type="Hubris Circlet",
            rarity=ItemRarity.RARE,
        )
        repr_str = repr(item)
        assert "Hubris Circlet" in repr_str
        assert "Rare" in repr_str


class TestItemUpdates:
    """Test updating item fields."""

    @pytest.mark.asyncio
    async def test_update_item_modifiers(self, db_session: AsyncSession):
        """Test updating item modifiers."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Test Item",
            base_type="Test Item",
            rarity=ItemRarity.RARE,
            explicit_mods=[{"text": "old mod", "values": [10]}],
        )
        db_session.add(item)
        await db_session.commit()

        item.explicit_mods = [
            {"text": "new mod 1", "values": [20]},
            {"text": "new mod 2", "values": [30]},
        ]
        await db_session.commit()
        await db_session.refresh(item)

        assert len(item.explicit_mods) == 2
        assert item.explicit_mods[0]["text"] == "new mod 1"

    @pytest.mark.asyncio
    async def test_update_item_properties(self, db_session: AsyncSession):
        """Test updating item properties."""
        item = Item(
            game=Game.POE1,
            name=None,
            type_line="Weapon",
            base_type="Weapon",
            rarity=ItemRarity.RARE,
            item_level=70,
        )
        db_session.add(item)
        await db_session.commit()

        item.item_level = 85
        await db_session.commit()
        await db_session.refresh(item)

        assert item.item_level == 85


class TestItemDeletion:
    """Test deleting items."""

    @pytest.mark.asyncio
    async def test_delete_item(self, db_session: AsyncSession):
        """Test deleting an item from the database."""
        item = Item(
            game=Game.POE1,
            name="Test Item",
            type_line="Test Base",
            base_type="Test Base",
            rarity=ItemRarity.UNIQUE,
        )
        db_session.add(item)
        await db_session.commit()
        item_id = item.id

        await db_session.delete(item)
        await db_session.commit()

        result = await db_session.execute(select(Item).where(Item.id == item_id))
        deleted_item = result.scalar_one_or_none()
        assert deleted_item is None
