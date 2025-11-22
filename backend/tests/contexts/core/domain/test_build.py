"""Tests for Build domain model.

Tests cover:
- Build creation with required fields
- JSONB storage for passive tree, items, skills
- Character stats handling
- Game context separation
- Source tracking (pob, poeninja, generated)
- PoB code storage
- Real-world examples (PoB imports, poe.ninja snapshots)
- Database operations (CRUD)
- Query patterns for build analysis
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.core import Build
from src.shared import Game


class TestBuildCreation:
    """Test Build entity creation with various configurations."""

    @pytest.mark.asyncio
    async def test_create_basic_build(self, db_session: AsyncSession):
        """Test creating a basic build with minimal required fields."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.id is not None
        assert build.game == Game.POE1
        assert build.name == "Test Build"
        assert build.character_class == "Witch"
        assert build.level == 90
        assert build.ascendancy is None

    @pytest.mark.asyncio
    async def test_create_build_with_ascendancy(self, db_session: AsyncSession):
        """Test creating a build with ascendancy class."""
        build = Build(
            game=Game.POE1,
            name="RF Juggernaut",
            character_class="Marauder",
            level=95,
            ascendancy="Juggernaut",
            league="Affliction",
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.ascendancy == "Juggernaut"
        assert build.league == "Affliction"

    @pytest.mark.asyncio
    async def test_create_build_with_stats(self, db_session: AsyncSession):
        """Test creating a build with character stats."""
        build = Build(
            game=Game.POE1,
            name="ES Build",
            character_class="Witch",
            level=92,
            life=3500,
            energy_shield=8000,
            mana=1200,
            armour=5000,
            evasion=2000,
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.life == 3500
        assert build.energy_shield == 8000
        assert build.mana == 1200
        assert build.armour == 5000
        assert build.evasion == 2000


class TestBuildComponents:
    """Test JSONB storage for build components."""

    @pytest.mark.asyncio
    async def test_store_passive_tree(self, db_session: AsyncSession):
        """Test storing passive tree data in JSONB."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
            passive_tree={
                "nodes": [12345, 23456, 34567, 45678],
                "masteries": {
                    "life": ["10% increased Life"],
                    "es": ["15% increased Energy Shield"],
                },
                "jewels": {
                    "slot_1": {"name": "Watcher's Eye", "stats": ["..."]},
                },
            },
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert "nodes" in build.passive_tree
        assert len(build.passive_tree["nodes"]) == 4
        assert "masteries" in build.passive_tree
        assert "jewels" in build.passive_tree

    @pytest.mark.asyncio
    async def test_store_items(self, db_session: AsyncSession):
        """Test storing item data in JSONB."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
            items={
                "weapon": {
                    "name": "Doomfletch's Prism",
                    "type": "Royal Bow",
                    "rarity": "unique",
                },
                "body_armour": {
                    "name": None,
                    "type": "Vaal Regalia",
                    "rarity": "rare",
                    "mods": ["+90 to maximum Life", "+40% Fire Resistance"],
                },
            },
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert "weapon" in build.items
        assert build.items["weapon"]["name"] == "Doomfletch's Prism"
        assert "body_armour" in build.items

    @pytest.mark.asyncio
    async def test_store_skills(self, db_session: AsyncSession):
        """Test storing skill gem data in JSONB."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
            skills=[
                {
                    "name": "Raise Spectre",
                    "gems": [
                        "Raise Spectre",
                        "Minion Damage Support",
                        "Predator Support",
                        "Spell Echo Support",
                        "Meat Shield Support",
                        "Elemental Army Support",
                    ],
                    "links": 6,
                    "active": True,
                },
                {
                    "name": "Flame Dash",
                    "gems": ["Flame Dash", "Faster Casting Support"],
                    "links": 2,
                    "active": False,
                },
            ],
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert len(build.skills) == 2
        assert build.skills[0]["name"] == "Raise Spectre"
        assert build.skills[0]["links"] == 6
        assert len(build.skills[0]["gems"]) == 6


class TestBuildMetadata:
    """Test build metadata and provenance."""

    @pytest.mark.asyncio
    async def test_pob_source(self, db_session: AsyncSession):
        """Test build from PoB import."""
        pob_code = "eNqVW2uT2zYS_StTqUrtnJpShwxyM..."  # Truncated for test

        build = Build(
            game=Game.POE1,
            name="RF Juggernaut from PoB",
            character_class="Marauder",
            level=95,
            source="pob",
            pob_code=pob_code,
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.source == "pob"
        assert build.pob_code == pob_code

    @pytest.mark.asyncio
    async def test_poeninja_source(self, db_session: AsyncSession):
        """Test build from poe.ninja ladder."""
        build = Build(
            game=Game.POE1,
            name="Ladder #1 Necromancer",
            character_class="Witch",
            level=100,
            ascendancy="Necromancer",
            league="Affliction HC",
            source="poeninja",
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.source == "poeninja"
        assert build.pob_code is None  # poe.ninja builds may not have PoB code

    @pytest.mark.asyncio
    async def test_properties_storage(self, db_session: AsyncSession):
        """Test storing additional properties in JSONB."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
            properties={
                "dps": 5000000,
                "effective_hp": 50000,
                "config": {
                    "enemy_is_boss": True,
                    "is_shocked": False,
                },
                "cost_estimate": 150.5,  # in divine orbs
            },
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.properties["dps"] == 5000000
        assert build.properties["config"]["enemy_is_boss"] is True
        assert build.properties["cost_estimate"] == 150.5

    @pytest.mark.asyncio
    async def test_upstream_data_storage(self, db_session: AsyncSession):
        """Test storing raw upstream data for fidelity."""
        upstream_pob_data = {
            "Build": {
                "className": "Marauder",
                "ascendClassName": "Juggernaut",
                "level": "95",
                "buildName": "RF Jugg",
            },
            "Tree": {
                "activeSpec": "1",
                "treeVersion": "3_23",
                "nodes": "12345,23456,34567",
            },
        }

        build = Build(
            game=Game.POE1,
            name="RF Juggernaut",
            character_class="Marauder",
            level=95,
            source="pob",
            upstream_data=upstream_pob_data,
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.upstream_data is not None
        assert build.upstream_data["Build"]["className"] == "Marauder"
        assert build.upstream_data["Tree"]["treeVersion"] == "3_23"


class TestBuildGameContext:
    """Test game context separation."""

    @pytest.mark.asyncio
    async def test_same_build_different_games(self, db_session: AsyncSession):
        """Test that same build archetype can exist in both games."""
        build_poe1 = Build(
            game=Game.POE1,
            name="RF Juggernaut",
            character_class="Marauder",
            level=95,
            ascendancy="Juggernaut",
        )
        build_poe2 = Build(
            game=Game.POE2,
            name="RF Juggernaut",
            character_class="Marauder",
            level=95,
            ascendancy="Titan",  # Different ascendancy name in PoE2
        )
        db_session.add_all([build_poe1, build_poe2])
        await db_session.commit()

        result = await db_session.execute(select(Build).where(Build.name == "RF Juggernaut"))
        builds = result.scalars().all()
        assert len(builds) == 2

        games = {build.game for build in builds}
        assert games == {Game.POE1, Game.POE2}

    @pytest.mark.asyncio
    async def test_filter_by_game(self, db_session: AsyncSession):
        """Test filtering builds by game context."""
        poe1_builds = [
            Build(
                game=Game.POE1,
                name=f"PoE1 Build {i}",
                character_class="Witch",
                level=90,
            )
            for i in range(3)
        ]
        poe2_builds = [
            Build(
                game=Game.POE2,
                name=f"PoE2 Build {i}",
                character_class="Witch",
                level=90,
            )
            for i in range(2)
        ]
        db_session.add_all(poe1_builds + poe2_builds)
        await db_session.commit()

        result = await db_session.execute(select(Build).where(Build.game == Game.POE1))
        poe1_count = len(result.scalars().all())

        result = await db_session.execute(select(Build).where(Build.game == Game.POE2))
        poe2_count = len(result.scalars().all())

        assert poe1_count == 3
        assert poe2_count == 2


class TestBuildQueries:
    """Test common build queries using indexes."""

    @pytest.mark.asyncio
    async def test_query_by_class(self, db_session: AsyncSession):
        """Test querying builds by character class (uses ix_build_game_class)."""
        builds = [
            Build(game=Game.POE1, name="Witch 1", character_class="Witch", level=90),
            Build(game=Game.POE1, name="Witch 2", character_class="Witch", level=92),
            Build(game=Game.POE1, name="Marauder 1", character_class="Marauder", level=95),
        ]
        db_session.add_all(builds)
        await db_session.commit()

        result = await db_session.execute(
            select(Build).where(Build.game == Game.POE1, Build.character_class == "Witch")
        )
        witches = result.scalars().all()
        assert len(witches) == 2

    @pytest.mark.asyncio
    async def test_query_by_ascendancy(self, db_session: AsyncSession):
        """Test querying builds by ascendancy (uses ix_build_game_ascendancy)."""
        builds = [
            Build(
                game=Game.POE1,
                name="Necro 1",
                character_class="Witch",
                level=90,
                ascendancy="Necromancer",
            ),
            Build(
                game=Game.POE1,
                name="Necro 2",
                character_class="Witch",
                level=92,
                ascendancy="Necromancer",
            ),
            Build(
                game=Game.POE1,
                name="Elementalist",
                character_class="Witch",
                level=95,
                ascendancy="Elementalist",
            ),
        ]
        db_session.add_all(builds)
        await db_session.commit()

        result = await db_session.execute(
            select(Build).where(Build.game == Game.POE1, Build.ascendancy == "Necromancer")
        )
        necros = result.scalars().all()
        assert len(necros) == 2

    @pytest.mark.asyncio
    async def test_query_by_league(self, db_session: AsyncSession):
        """Test querying builds by league (uses ix_build_game_league)."""
        builds = [
            Build(
                game=Game.POE1,
                name="Build 1",
                character_class="Witch",
                level=90,
                league="Affliction",
            ),
            Build(
                game=Game.POE1,
                name="Build 2",
                character_class="Marauder",
                level=95,
                league="Affliction",
            ),
            Build(
                game=Game.POE1,
                name="Build 3",
                character_class="Templar",
                level=92,
                league="Standard",
            ),
        ]
        db_session.add_all(builds)
        await db_session.commit()

        result = await db_session.execute(
            select(Build).where(Build.game == Game.POE1, Build.league == "Affliction")
        )
        affliction_builds = result.scalars().all()
        assert len(affliction_builds) == 2

    @pytest.mark.asyncio
    async def test_query_by_level_range(self, db_session: AsyncSession):
        """Test querying builds by level range (uses ix_build_level)."""
        builds = [
            Build(game=Game.POE1, name=f"Build {i}", character_class="Witch", level=i)
            for i in range(85, 100, 5)
        ]
        db_session.add_all(builds)
        await db_session.commit()

        result = await db_session.execute(select(Build).where(Build.level >= 90, Build.level <= 95))
        mid_level_builds = result.scalars().all()
        assert len(mid_level_builds) == 2  # Level 90 and 95

    @pytest.mark.asyncio
    async def test_query_by_source(self, db_session: AsyncSession):
        """Test querying builds by source (uses ix_build_source)."""
        builds = [
            Build(
                game=Game.POE1,
                name="PoB Build",
                character_class="Witch",
                level=90,
                source="pob",
            ),
            Build(
                game=Game.POE1,
                name="Ninja Build",
                character_class="Marauder",
                level=95,
                source="poeninja",
            ),
        ]
        db_session.add_all(builds)
        await db_session.commit()

        result = await db_session.execute(select(Build).where(Build.source == "pob"))
        pob_builds = result.scalars().all()
        assert len(pob_builds) == 1


class TestBuildRealExamples:
    """Test with real-world build examples."""

    @pytest.mark.asyncio
    async def test_pob_rf_juggernaut(self, db_session: AsyncSession):
        """Test realistic RF Juggernaut build from PoB."""
        build = Build(
            game=Game.POE1,
            name="RF Juggernaut - 5M DPS",
            character_class="Marauder",
            level=95,
            ascendancy="Juggernaut",
            league="Affliction",
            life=8500,
            energy_shield=0,
            mana=500,
            armour=45000,
            evasion=1000,
            source="pob",
            pob_code="eNqVW2uT2...",
            passive_tree={"nodes": list(range(100))},  # Simplified
            items={
                "helmet": {"name": "The Brass Dome", "rarity": "unique"},
                "weapon": {"name": "Doryani's Catalyst", "rarity": "unique"},
            },
            skills=[
                {
                    "name": "Righteous Fire",
                    "gems": ["RF", "Elemental Focus", "Burning Damage"],
                    "links": 6,
                }
            ],
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.name == "RF Juggernaut - 5M DPS"
        assert build.life == 8500
        assert build.armour == 45000
        assert build.source == "pob"

    @pytest.mark.asyncio
    async def test_poeninja_necromancer(self, db_session: AsyncSession):
        """Test realistic Necromancer build from poe.ninja."""
        build = Build(
            game=Game.POE1,
            name="Ziz_Spectre_SSF",
            character_class="Witch",
            level=98,
            ascendancy="Necromancer",
            league="Affliction HC SSF",
            life=4500,
            energy_shield=2500,
            source="poeninja",
            items={
                "equipment": [
                    {"slot": "helmet", "name": None, "base": "Bone Helmet"},
                    {"slot": "weapon", "name": "+3 Convoking Wand"},
                ]
            },
            skills=[
                {
                    "name": "Raise Spectre",
                    "gems": ["Spectre", "Minion Damage", "Predator"],
                    "links": 6,
                }
            ],
        )
        db_session.add(build)
        await db_session.commit()
        await db_session.refresh(build)

        assert build.name == "Ziz_Spectre_SSF"
        assert build.ascendancy == "Necromancer"
        assert "HC SSF" in build.league


class TestBuildRepresentation:
    """Test Build string representation."""

    def test_build_repr(self):
        """Test __repr__ shows key build info."""
        build = Build(
            game=Game.POE1,
            name="RF Juggernaut",
            character_class="Marauder",
            level=95,
        )
        repr_str = repr(build)
        assert "RF Juggernaut" in repr_str
        assert "Marauder" in repr_str
        assert "95" in repr_str


class TestBuildUpdates:
    """Test updating build fields."""

    @pytest.mark.asyncio
    async def test_update_level(self, db_session: AsyncSession):
        """Test updating build level."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
        )
        db_session.add(build)
        await db_session.commit()

        build.level = 95
        await db_session.commit()
        await db_session.refresh(build)

        assert build.level == 95

    @pytest.mark.asyncio
    async def test_update_stats(self, db_session: AsyncSession):
        """Test updating build stats."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
            life=4000,
        )
        db_session.add(build)
        await db_session.commit()

        build.life = 5000
        build.energy_shield = 3000
        await db_session.commit()
        await db_session.refresh(build)

        assert build.life == 5000
        assert build.energy_shield == 3000


class TestBuildDeletion:
    """Test deleting builds."""

    @pytest.mark.asyncio
    async def test_delete_build(self, db_session: AsyncSession):
        """Test deleting a build from the database."""
        build = Build(
            game=Game.POE1,
            name="Test Build",
            character_class="Witch",
            level=90,
        )
        db_session.add(build)
        await db_session.commit()
        build_id = build.id

        await db_session.delete(build)
        await db_session.commit()

        result = await db_session.execute(select(Build).where(Build.id == build_id))
        deleted_build = result.scalar_one_or_none()
        assert deleted_build is None
