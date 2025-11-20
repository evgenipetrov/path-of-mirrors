"""Integration tests for upstream API routes."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLE_POB_XML = REPO_ROOT / "_samples/data/poe1/pob/Sample build PoE 1.xml"
if not SAMPLE_POB_XML.exists():
    import pytest

    pytest.skip("Sample PoB files missing in test environment", allow_module_level=True)


class TestPoBParseEndpoint:
    """Test POST /api/v1/pob/parse endpoint."""

    def test_parse_pob_xml_success(self):
        """Test parsing PoB XML successfully."""
        # Read sample PoB file
        sample_path = REPO_ROOT / "_samples" / "data/poe1/pob/Sample build PoE 1.xml"

        with sample_path.open() as f:
            pob_xml = f.read()

        # Make API request
        response = client.post(
            "/api/v1/pob/parse",
            json={
                "pob_xml": pob_xml,
                "game": "poe1",
            },
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        # Verify basic fields
        assert data["game"] == "poe1"
        assert data["character_class"] == "Duelist"
        assert data["ascendancy"] == "Champion"
        assert data["level"] == 100
        assert data["source"] == "pob"

        # Verify items were extracted
        assert data["items"] is not None
        assert isinstance(data["items"], dict)
        assert len(data["items"]) > 0

    def test_parse_pob_code_invalid_base64(self):
        """Test parsing invalid PoB import code."""
        response = client.post(
            "/api/v1/pob/parse",
            json={
                "pob_code": "this-is-not-valid-base64!!!",
                "game": "poe1",
            },
        )

        # Should return 422 for invalid data
        assert response.status_code == 422
        assert "Invalid PoB data" in response.json()["detail"]

    def test_parse_pob_missing_both_inputs(self):
        """Test error when neither pob_xml nor pob_code is provided."""
        response = client.post(
            "/api/v1/pob/parse",
            json={
                "game": "poe1",
            },
        )

        # Should return 400 for missing input
        assert response.status_code == 400
        assert "Either pob_xml or pob_code must be provided" in response.json()["detail"]

    def test_parse_pob_invalid_xml(self):
        """Test parsing malformed XML."""
        response = client.post(
            "/api/v1/pob/parse",
            json={
                "pob_xml": "this is not valid xml",
                "game": "poe1",
            },
        )

        # Should return 422 for invalid XML
        assert response.status_code == 422
        assert "Invalid PoB data" in response.json()["detail"]

    def test_parse_pob_xml_missing_required_fields(self):
        """Test parsing XML missing required Build fields."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build level="90"/>
        </PathOfBuilding>
        """

        response = client.post(
            "/api/v1/pob/parse",
            json={
                "pob_xml": invalid_xml,
                "game": "poe1",
            },
        )

        # Should return 422 for missing className
        assert response.status_code == 422
        assert "missing className" in response.json()["detail"]

    def test_parse_pob_poe2(self):
        """Test parsing PoB for PoE2."""
        pob_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Monk" level="85" buildName="Test Monk"/>
        </PathOfBuilding>
        """

        response = client.post(
            "/api/v1/pob/parse",
            json={
                "pob_xml": pob_xml,
                "game": "poe2",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["game"] == "poe2"
        assert data["character_class"] == "Monk"
        assert data["level"] == 85

    def test_parse_pob_response_schema(self):
        """Test that response matches PoBParseResponse schema."""
        pob_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PathOfBuilding>
            <Build className="Witch" ascendClassName="Necromancer" level="92" buildName="Test Build"/>
        </PathOfBuilding>
        """

        response = client.post(
            "/api/v1/pob/parse",
            json={
                "pob_xml": pob_xml,
                "game": "poe1",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields exist
        assert "game" in data
        assert "name" in data
        assert "character_class" in data
        assert "level" in data
        assert "ascendancy" in data
        assert "source" in data

        # Verify optional fields are present (even if None)
        assert "items" in data
        assert "passive_tree" in data
        assert "skills" in data
        assert "life" in data
        assert "energy_shield" in data
