"""Integration tests for Notes API endpoints.

This module contains comprehensive integration tests for the Notes CRUD API,
including happy paths, validation, error scenarios, and game context filtering.
"""

from uuid import UUID, uuid4

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm.session import Session

from contexts.placeholder.domain.models import Note


class TestCreateNote:
    """Test POST /api/notes endpoint for creating notes."""

    def test_create_note_success_poe1(self, client: TestClient, db: Session) -> None:
        """Test successful note creation for POE1."""
        payload = {
            "title": "Test Note POE1",
            "content": "This is a test note for Path of Exile 1",
            "game_context": "poe1",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["content"] == payload["content"]
        assert data["game_context"] == "poe1"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify UUID format
        note_id = UUID(data["id"])
        assert isinstance(note_id, UUID)

        # Verify note exists by retrieving it via API
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == status.HTTP_200_OK
        retrieved = get_response.json()
        assert retrieved["title"] == payload["title"]
        assert retrieved["game_context"] == "poe1"

    def test_create_note_success_poe2(self, client: TestClient, db: Session) -> None:
        """Test successful note creation for POE2."""
        payload = {
            "title": "Test Note POE2",
            "content": "This is a test note for Path of Exile 2",
            "game_context": "poe2",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["game_context"] == "poe2"

    def test_create_note_without_content(self, client: TestClient, db: Session) -> None:
        """Test creating a note without content (content is optional)."""
        payload = {
            "title": "Note Without Content",
            "game_context": "poe1",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["content"] is None
        assert data["game_context"] == "poe1"

    def test_create_note_with_null_content(self, client: TestClient) -> None:
        """Test creating a note with explicitly null content."""
        payload = {
            "title": "Note With Null Content",
            "content": None,
            "game_context": "poe1",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] is None

    def test_create_note_missing_title(self, client: TestClient) -> None:
        """Test creating a note without required title field."""
        payload = {
            "content": "Content without title",
            "game_context": "poe1",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = response.json()
        assert "detail" in error_detail

    def test_create_note_empty_title(self, client: TestClient) -> None:
        """Test creating a note with empty title (should fail validation)."""
        payload = {
            "title": "",
            "content": "Content with empty title",
            "game_context": "poe1",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_note_title_too_long(self, client: TestClient) -> None:
        """Test creating a note with title exceeding 255 characters."""
        payload = {
            "title": "x" * 256,  # Exceeds max_length=255
            "content": "Test content",
            "game_context": "poe1",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_note_missing_game_context(self, client: TestClient) -> None:
        """Test creating a note without required game_context field."""
        payload = {
            "title": "Note without game context",
            "content": "This should fail",
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_note_invalid_game_context(self, client: TestClient) -> None:
        """Test creating a note with invalid game_context value."""
        payload = {
            "title": "Note with invalid game",
            "content": "This should fail",
            "game_context": "poe3",  # Invalid - only poe1 and poe2 allowed
        }

        response = client.post("/api/notes", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListNotes:
    """Test GET /api/notes endpoint for listing notes."""

    def test_list_notes_empty(self, client: TestClient, db: Session) -> None:
        """Test listing notes when no notes exist."""
        # Clear all notes using raw SQL
        db.execute(text("DELETE FROM notes"))
        db.commit()

        response = client.get("/api/notes")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_notes_all(self, client: TestClient, db: Session) -> None:
        """Test listing all notes without game filter."""
        # Create test notes
        note1 = Note(title="POE1 Note", content="Content 1", game_context="poe1")
        note2 = Note(title="POE2 Note", content="Content 2", game_context="poe2")
        db.add_all([note1, note2])
        db.commit()

        response = client.get("/api/notes")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        titles = [note["title"] for note in data]
        assert "POE1 Note" in titles
        assert "POE2 Note" in titles

    def test_list_notes_filter_poe1(self, client: TestClient, db: Session) -> None:
        """Test listing notes filtered by POE1 game context."""
        # Clear existing and create test notes
        db.query(Note).delete()
        note1 = Note(title="POE1 Note 1", content="Content 1", game_context="poe1")
        note2 = Note(title="POE1 Note 2", content="Content 2", game_context="poe1")
        note3 = Note(title="POE2 Note", content="Content 3", game_context="poe2")
        db.add_all([note1, note2, note3])
        db.commit()

        response = client.get("/api/notes?game=poe1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        for note in data:
            assert note["game_context"] == "poe1"
        titles = [note["title"] for note in data]
        assert "POE1 Note 1" in titles
        assert "POE1 Note 2" in titles

    def test_list_notes_filter_poe2(self, client: TestClient, db: Session) -> None:
        """Test listing notes filtered by POE2 game context."""
        # Clear existing and create test notes
        db.query(Note).delete()
        note1 = Note(title="POE1 Note", content="Content 1", game_context="poe1")
        note2 = Note(title="POE2 Note 1", content="Content 2", game_context="poe2")
        note3 = Note(title="POE2 Note 2", content="Content 3", game_context="poe2")
        db.add_all([note1, note2, note3])
        db.commit()

        response = client.get("/api/notes?game=poe2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        for note in data:
            assert note["game_context"] == "poe2"

    def test_list_notes_invalid_game_filter(self, client: TestClient) -> None:
        """Test listing notes with invalid game filter."""
        response = client.get("/api/notes?game=invalid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetNote:
    """Test GET /api/notes/{note_id} endpoint for retrieving a single note."""

    def test_get_note_success(self, client: TestClient, db: Session) -> None:
        """Test successfully retrieving a note by ID."""
        # Create a test note
        note = Note(
            title="Test Note",
            content="Test content for retrieval",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        response = client.get(f"/api/notes/{note.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(note.id)
        assert data["title"] == note.title
        assert data["content"] == note.content
        assert data["game_context"] == "poe1"

    def test_get_note_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent note."""
        non_existent_id = uuid4()
        response = client.get(f"/api/notes/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_detail = response.json()
        assert "detail" in error_detail
        assert str(non_existent_id) in error_detail["detail"]

    def test_get_note_invalid_uuid(self, client: TestClient) -> None:
        """Test retrieving a note with invalid UUID format."""
        response = client.get("/api/notes/invalid-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateNote:
    """Test PUT /api/notes/{note_id} endpoint for updating notes."""

    def test_update_note_all_fields(self, client: TestClient, db: Session) -> None:
        """Test updating all fields of a note."""
        # Create a test note
        note = Note(
            title="Original Title",
            content="Original content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        payload = {
            "title": "Updated Title",
            "content": "Updated content",
            "game_context": "poe2",
        }

        response = client.put(f"/api/notes/{note.id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(note.id)
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"
        assert data["game_context"] == "poe2"

        # Verify in database
        db.refresh(note)
        assert note.title == "Updated Title"
        assert note.content == "Updated content"
        assert note.game_context == "poe2"

    def test_update_note_partial_title_only(self, client: TestClient, db: Session) -> None:
        """Test updating only the title field."""
        note = Note(
            title="Original Title",
            content="Original content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        payload = {"title": "New Title"}

        response = client.put(f"/api/notes/{note.id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Title"
        assert data["content"] == "Original content"
        assert data["game_context"] == "poe1"

    def test_update_note_partial_content_only(self, client: TestClient, db: Session) -> None:
        """Test updating only the content field."""
        note = Note(
            title="Original Title",
            content="Original content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        payload = {"content": "New content"}

        response = client.put(f"/api/notes/{note.id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Original Title"
        assert data["content"] == "New content"

    def test_update_note_set_content_to_null(self, client: TestClient, db: Session) -> None:
        """Test setting content to null."""
        note = Note(
            title="Test Note",
            content="Some content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        payload = {"content": None}

        response = client.put(f"/api/notes/{note.id}", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] is None

    def test_update_note_not_found(self, client: TestClient) -> None:
        """Test updating a non-existent note."""
        non_existent_id = uuid4()
        payload = {"title": "New Title"}

        response = client.put(f"/api/notes/{non_existent_id}", json=payload)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_note_empty_title(self, client: TestClient, db: Session) -> None:
        """Test updating note with empty title (should fail validation)."""
        note = Note(
            title="Original Title",
            content="Original content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        payload = {"title": ""}

        response = client.put(f"/api/notes/{note.id}", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_note_invalid_game_context(self, client: TestClient, db: Session) -> None:
        """Test updating note with invalid game_context."""
        note = Note(
            title="Test Note",
            content="Test content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        payload = {"game_context": "invalid"}

        response = client.put(f"/api/notes/{note.id}", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_note_empty_payload(self, client: TestClient, db: Session) -> None:
        """Test updating note with empty payload (no fields to update)."""
        note = Note(
            title="Test Note",
            content="Test content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        original_title = note.title
        original_content = note.content
        original_game = note.game_context

        payload = {}

        response = client.put(f"/api/notes/{note.id}", json=payload)

        # Empty update should succeed and keep original values
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == original_title
        assert data["content"] == original_content
        assert data["game_context"] == original_game


class TestDeleteNote:
    """Test DELETE /api/notes/{note_id} endpoint for deleting notes."""

    def test_delete_note_success(self, client: TestClient, db: Session) -> None:
        """Test successfully deleting a note."""
        # Create a test note
        note = Note(
            title="Note to Delete",
            content="This note will be deleted",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        note_id = note.id

        response = client.delete(f"/api/notes/{note_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""

        # Verify note is deleted from database
        deleted_note = db.query(Note).filter(Note.id == note_id).first()
        assert deleted_note is None

    def test_delete_note_not_found(self, client: TestClient) -> None:
        """Test deleting a non-existent note."""
        non_existent_id = uuid4()
        response = client.delete(f"/api/notes/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_note_invalid_uuid(self, client: TestClient) -> None:
        """Test deleting a note with invalid UUID format."""
        response = client.delete("/api/notes/invalid-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_note_idempotency(self, client: TestClient, db: Session) -> None:
        """Test that deleting the same note twice returns 404 on second attempt."""
        note = Note(
            title="Note for idempotency test",
            content="Test content",
            game_context="poe1",
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        note_id = note.id

        # First delete - should succeed
        response1 = client.delete(f"/api/notes/{note_id}")
        assert response1.status_code == status.HTTP_204_NO_CONTENT

        # Second delete - should fail with 404
        response2 = client.delete(f"/api/notes/{note_id}")
        assert response2.status_code == status.HTTP_404_NOT_FOUND


class TestNotesIntegrationScenarios:
    """Integration tests covering complete workflows."""

    def test_full_crud_lifecycle(self, client: TestClient, db: Session) -> None:
        """Test complete CRUD lifecycle: create, read, update, delete."""
        # 1. Create a note
        create_payload = {
            "title": "Lifecycle Test Note",
            "content": "Initial content",
            "game_context": "poe1",
        }
        create_response = client.post("/api/notes", json=create_payload)
        assert create_response.status_code == status.HTTP_201_CREATED
        note_id = create_response.json()["id"]

        # 2. Read the note
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["title"] == "Lifecycle Test Note"

        # 3. Update the note
        update_payload = {"title": "Updated Lifecycle Note", "content": "Updated content"}
        update_response = client.put(f"/api/notes/{note_id}", json=update_payload)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["title"] == "Updated Lifecycle Note"

        # 4. Delete the note
        delete_response = client.delete(f"/api/notes/{note_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # 5. Verify note is gone
        get_after_delete = client.get(f"/api/notes/{note_id}")
        assert get_after_delete.status_code == status.HTTP_404_NOT_FOUND

    def test_game_context_isolation(self, client: TestClient, db: Session) -> None:
        """Test that game context filtering properly isolates notes."""
        # Clear existing notes
        db.query(Note).delete()
        db.commit()

        # Create notes for both games
        poe1_notes = [
            {"title": f"POE1 Note {i}", "content": f"Content {i}", "game_context": "poe1"}
            for i in range(3)
        ]
        poe2_notes = [
            {"title": f"POE2 Note {i}", "content": f"Content {i}", "game_context": "poe2"}
            for i in range(2)
        ]

        for note_data in poe1_notes + poe2_notes:
            response = client.post("/api/notes", json=note_data)
            assert response.status_code == status.HTTP_201_CREATED

        # Verify POE1 filter returns only POE1 notes
        poe1_response = client.get("/api/notes?game=poe1")
        assert poe1_response.status_code == status.HTTP_200_OK
        poe1_data = poe1_response.json()
        assert len(poe1_data) == 3
        assert all(note["game_context"] == "poe1" for note in poe1_data)

        # Verify POE2 filter returns only POE2 notes
        poe2_response = client.get("/api/notes?game=poe2")
        assert poe2_response.status_code == status.HTTP_200_OK
        poe2_data = poe2_response.json()
        assert len(poe2_data) == 2
        assert all(note["game_context"] == "poe2" for note in poe2_data)

        # Verify no filter returns all notes
        all_response = client.get("/api/notes")
        assert all_response.status_code == status.HTTP_200_OK
        all_data = all_response.json()
        assert len(all_data) == 5

    def test_concurrent_note_creation(self, client: TestClient, db: Session) -> None:
        """Test creating multiple notes in sequence (simulating concurrent users)."""
        notes_to_create = [
            {"title": f"Concurrent Note {i}", "content": f"Content {i}", "game_context": "poe1"}
            for i in range(10)
        ]

        created_ids = []
        for note_data in notes_to_create:
            response = client.post("/api/notes", json=note_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_ids.append(response.json()["id"])

        # Verify all notes were created with unique IDs
        assert len(set(created_ids)) == 10

        # Verify all notes can be retrieved
        for note_id in created_ids:
            response = client.get(f"/api/notes/{note_id}")
            assert response.status_code == status.HTTP_200_OK
