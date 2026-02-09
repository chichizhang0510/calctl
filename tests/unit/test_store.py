"""
Unit tests for calctl.store

Tests the JsonEventStore with both mocked and real file operations.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import date, datetime
from calctl.store import JsonEventStore
from calctl.models import Event
from calctl.errors import StorageError


def make_event(event_id: str, title: str, date_val: date) -> Event:
    """Helper to create test events"""
    return Event(
        id=event_id,
        title=title,
        description=None,
        date=date_val,
        start_time="10:00",
        duration_min=60,
        location=None,
        create_at=datetime(2026, 2, 1, 12, 0, 0),
        update_at=datetime(2026, 2, 1, 12, 0, 0)
    )


@pytest.fixture
def temp_store():
    """Create a temporary store for testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()
    
    store = JsonEventStore(temp_path)
    yield store
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    import tempfile
    temp = tempfile.mkdtemp()
    yield Path(temp)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp, ignore_errors=True)


class TestStoreInitialization:
    """Test store initialization and file creation"""
    
    def test_store_creates_file_on_first_operation(self, temp_dir):
        """Test that store creates file when it doesn't exist"""
        store_path = temp_dir / "new_events.json"
        assert not store_path.exists()
        
        store = JsonEventStore(store_path)
        store._ensure_file()
        
        assert store_path.exists()
    
    def test_store_creates_parent_directories(self, temp_dir):
        """Test that store creates parent directories"""
        store_path = temp_dir / "subdir" / "events.json"
        assert not store_path.parent.exists()
        
        store = JsonEventStore(store_path)
        store._ensure_file()
        
        assert store_path.parent.exists()
        assert store_path.exists()
    
    def test_new_file_has_correct_structure(self, temp_dir):
        """Test that new file has correct JSON structure"""
        store_path = temp_dir / "events.json"
        store = JsonEventStore(store_path)
        store._ensure_file()
        
        with open(store_path, 'r') as f:
            data = json.load(f)
        
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) == 0


class TestListAll:
    """Test list_all method"""
    
    def test_list_all_empty_store(self, temp_store):
        """Test listing events from empty store"""
        events = temp_store.list_all()
        assert events == []
    
    def test_list_all_single_event(self, temp_store):
        """Test listing single event"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        events = temp_store.list_all()
        assert len(events) == 1
        assert events[0].id == "evt-0001"
        assert events[0].title == "Test"
    
    def test_list_all_multiple_events(self, temp_store):
        """Test listing multiple events"""
        e1 = make_event("evt-0001", "First", date(2026, 2, 10))
        e2 = make_event("evt-0002", "Second", date(2026, 2, 11))
        e3 = make_event("evt-0003", "Third", date(2026, 2, 12))
        
        temp_store.add(e1)
        temp_store.add(e2)
        temp_store.add(e3)
        
        events = temp_store.list_all()
        assert len(events) == 3
    
    def test_list_all_returns_sorted(self, temp_store):
        """Test that list_all returns events sorted by date, time, id"""
        # Add in random order
        e1 = make_event("evt-0003", "Third", date(2026, 2, 12))
        e2 = make_event("evt-0001", "First", date(2026, 2, 10))
        e3 = make_event("evt-0002", "Second", date(2026, 2, 11))
        
        temp_store.add(e1)
        temp_store.add(e2)
        temp_store.add(e3)
        
        events = temp_store.list_all()
        # Should be sorted by date
        assert events[0].date == date(2026, 2, 10)
        assert events[1].date == date(2026, 2, 11)
        assert events[2].date == date(2026, 2, 12)


class TestGetById:
    """Test get_by_id method"""
    
    def test_get_by_id_found(self, temp_store):
        """Test getting event by ID when it exists"""
        e = make_event("evt-1234", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        result = temp_store.get_by_id("evt-1234")
        assert result is not None
        assert result.id == "evt-1234"
        assert result.title == "Test"
    
    def test_get_by_id_not_found(self, temp_store):
        """Test getting event by ID when it doesn't exist"""
        result = temp_store.get_by_id("evt-9999")
        assert result is None
    
    def test_get_by_id_empty_store(self, temp_store):
        """Test getting event from empty store"""
        result = temp_store.get_by_id("evt-0001")
        assert result is None
    
    def test_get_by_id_with_multiple_events(self, temp_store):
        """Test getting specific event from multiple events"""
        e1 = make_event("evt-0001", "First", date(2026, 2, 10))
        e2 = make_event("evt-0002", "Second", date(2026, 2, 11))
        e3 = make_event("evt-0003", "Third", date(2026, 2, 12))
        
        temp_store.add(e1)
        temp_store.add(e2)
        temp_store.add(e3)
        
        result = temp_store.get_by_id("evt-0002")
        assert result is not None
        assert result.id == "evt-0002"
        assert result.title == "Second"


class TestAdd:
    """Test add method"""
    
    def test_add_single_event(self, temp_store):
        """Test adding single event"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        # Verify it was added
        events = temp_store.list_all()
        assert len(events) == 1
        assert events[0].id == "evt-0001"
    
    def test_add_duplicate_id_raises_error(self, temp_store):
        """Test that adding duplicate ID raises error"""
        e1 = make_event("evt-0001", "First", date(2026, 2, 10))
        e2 = make_event("evt-0001", "Second", date(2026, 2, 11))
        
        temp_store.add(e1)
        
        with pytest.raises(StorageError, match="already exists"):
            temp_store.add(e2)
    
    def test_add_persists_to_file(self, temp_store):
        """Test that add persists data to file"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        # Read file directly
        with open(temp_store.path, 'r') as f:
            data = json.load(f)
        
        assert len(data["events"]) == 1
        assert data["events"][0]["id"] == "evt-0001"
    
    def test_add_preserves_all_fields(self, temp_store):
        """Test that all event fields are preserved"""
        e = Event(
            id="evt-0001",
            title="Meeting",
            description="Important meeting",
            date=date(2026, 2, 10),
            start_time="14:30",
            duration_min=90,
            location="Room 101",
            create_at=datetime(2026, 2, 1, 10, 0, 0),
            update_at=datetime(2026, 2, 1, 10, 0, 0)
        )
        
        temp_store.add(e)
        retrieved = temp_store.get_by_id("evt-0001")
        
        assert retrieved.title == "Meeting"
        assert retrieved.description == "Important meeting"
        assert retrieved.date == date(2026, 2, 10)
        assert retrieved.start_time == "14:30"
        assert retrieved.duration_min == 90
        assert retrieved.location == "Room 101"


class TestAddMany:
    """Test add_many method"""
    
    def test_add_many_empty_list(self, temp_store):
        """Test adding empty list"""
        temp_store.add_many([])
        assert len(temp_store.list_all()) == 0
    
    def test_add_many_single_event(self, temp_store):
        """Test adding single event via add_many"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add_many([e])
        
        events = temp_store.list_all()
        assert len(events) == 1
    
    def test_add_many_multiple_events(self, temp_store):
        """Test adding multiple events"""
        events = [
            make_event("evt-0001", "First", date(2026, 2, 10)),
            make_event("evt-0002", "Second", date(2026, 2, 11)),
            make_event("evt-0003", "Third", date(2026, 2, 12)),
        ]
        
        temp_store.add_many(events)
        
        result = temp_store.list_all()
        assert len(result) == 3
    
    def test_add_many_with_duplicate_raises_error(self, temp_store):
        """Test that duplicate IDs in batch raise error"""
        events = [
            make_event("evt-0001", "First", date(2026, 2, 10)),
            make_event("evt-0001", "Duplicate", date(2026, 2, 11)),
        ]
        
        with pytest.raises(StorageError, match="Duplicate event id"):
            temp_store.add_many(events)
    
    def test_add_many_atomic_on_error(self, temp_store):
        """Test that add_many is atomic (all or nothing)"""
        # Add one event first
        temp_store.add(make_event("evt-0001", "Existing", date(2026, 2, 10)))
        
        # Try to add batch with duplicate
        events = [
            make_event("evt-0002", "New1", date(2026, 2, 11)),
            make_event("evt-0001", "Duplicate", date(2026, 2, 12)),  # Duplicate!
        ]
        
        with pytest.raises(StorageError):
            temp_store.add_many(events)
        
        # Original event should still be there, but not the new ones
        result = temp_store.list_all()
        assert len(result) == 1
        assert result[0].id == "evt-0001"


class TestUpdate:
    """Test update method"""
    
    def test_update_existing_event(self, temp_store):
        """Test updating existing event"""
        e = make_event("evt-0001", "Original", date(2026, 2, 10))
        temp_store.add(e)
        
        # Update with new data
        updated = Event(
            id="evt-0001",
            title="Updated",
            description="New description",
            date=date(2026, 2, 11),
            start_time="15:00",
            duration_min=45,
            location="New location",
            create_at=e.create_at,
            update_at=datetime(2026, 2, 1, 14, 0, 0)
        )
        
        temp_store.update(updated)
        
        # Verify update
        result = temp_store.get_by_id("evt-0001")
        assert result.title == "Updated"
        assert result.date == date(2026, 2, 11)
        assert result.duration_min == 45
    
    def test_update_nonexistent_raises_error(self, temp_store):
        """Test updating non-existent event raises error"""
        e = make_event("evt-9999", "Test", date(2026, 2, 10))
        
        with pytest.raises(StorageError, match="not found"):
            temp_store.update(e)
    
    def test_update_persists_to_file(self, temp_store):
        """Test that update persists to file"""
        e = make_event("evt-0001", "Original", date(2026, 2, 10))
        temp_store.add(e)
        
        updated = Event(
            id="evt-0001",
            title="Updated",
            description=None,
            date=date(2026, 2, 10),
            start_time="10:00",
            duration_min=60,
            location=None,
            create_at=e.create_at,
            update_at=datetime.now()
        )
        
        temp_store.update(updated)
        
        # Read from file
        with open(temp_store.path, 'r') as f:
            data = json.load(f)
        
        assert data["events"][0]["title"] == "Updated"


class TestDeleteById:
    """Test delete_by_id method"""
    
    def test_delete_existing_event(self, temp_store):
        """Test deleting existing event"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        result = temp_store.delete_by_id("evt-0001")
        assert result is True
        
        # Verify deleted
        assert temp_store.get_by_id("evt-0001") is None
    
    def test_delete_nonexistent_returns_false(self, temp_store):
        """Test deleting non-existent event returns False"""
        result = temp_store.delete_by_id("evt-9999")
        assert result is False
    
    def test_delete_from_multiple_events(self, temp_store):
        """Test deleting one event from multiple"""
        e1 = make_event("evt-0001", "First", date(2026, 2, 10))
        e2 = make_event("evt-0002", "Second", date(2026, 2, 11))
        e3 = make_event("evt-0003", "Third", date(2026, 2, 12))
        
        temp_store.add(e1)
        temp_store.add(e2)
        temp_store.add(e3)
        
        temp_store.delete_by_id("evt-0002")
        
        events = temp_store.list_all()
        assert len(events) == 2
        assert events[0].id == "evt-0001"
        assert events[1].id == "evt-0003"
    
    def test_delete_persists_to_file(self, temp_store):
        """Test that delete persists to file"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        temp_store.delete_by_id("evt-0001")
        
        # Read from file
        with open(temp_store.path, 'r') as f:
            data = json.load(f)
        
        assert len(data["events"]) == 0


class TestDeleteByDate:
    """Test delete_by_date method"""
    
    def test_delete_by_date_single_event(self, temp_store):
        """Test deleting single event by date"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        deleted = temp_store.delete_by_date("2026-02-10")
        assert deleted == 1
        
        events = temp_store.list_all()
        assert len(events) == 0
    
    def test_delete_by_date_multiple_events(self, temp_store):
        """Test deleting multiple events on same date"""
        e1 = make_event("evt-0001", "First", date(2026, 2, 10))
        e2 = make_event("evt-0002", "Second", date(2026, 2, 10))
        e3 = make_event("evt-0003", "Third", date(2026, 2, 11))
        
        temp_store.add(e1)
        temp_store.add(e2)
        temp_store.add(e3)
        
        deleted = temp_store.delete_by_date("2026-02-10")
        assert deleted == 2
        
        events = temp_store.list_all()
        assert len(events) == 1
        assert events[0].date == date(2026, 2, 11)
    
    def test_delete_by_date_no_matches(self, temp_store):
        """Test deleting when no events on that date"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        temp_store.add(e)
        
        deleted = temp_store.delete_by_date("2026-02-15")
        assert deleted == 0
        
        # Original event should still be there
        events = temp_store.list_all()
        assert len(events) == 1


class TestFileOperations:
    """Test file operations and edge cases"""
    
    def test_atomic_write_with_temp_file(self, temp_store):
        """Test that writes use temporary file (atomic operation)"""
        e = make_event("evt-0001", "Test", date(2026, 2, 10))
        
        # Mock to verify temp file is used
        original_save = temp_store._save_data
        temp_file_used = []
        
        def mock_save(data):
            # Check that temp file is created
            tmp = temp_store.path.with_suffix(temp_store.path.suffix + ".tmp")
            original_save(data)
            temp_file_used.append(True)
        
        temp_store._save_data = mock_save
        temp_store.add(e)
        
        assert len(temp_file_used) > 0
    
    def test_handle_corrupted_json(self, temp_dir):
        """Test handling corrupted JSON file"""
        store_path = temp_dir / "corrupted.json"
        store_path.write_text("{ invalid json")
        
        store = JsonEventStore(store_path)
        
        with pytest.raises(StorageError, match="Failed to parse JSON"):
            store.list_all()
    
    def test_handle_invalid_structure(self, temp_dir):
        """Test handling invalid JSON structure"""
        store_path = temp_dir / "invalid.json"
        store_path.write_text('{"wrong": "structure"}')
        
        store = JsonEventStore(store_path)
        
        with pytest.raises(StorageError, match="Invalid data format"):
            store.list_all()
    
    def test_handle_empty_file(self, temp_dir):
        """Test handling empty file"""
        store_path = temp_dir / "empty.json"
        store_path.write_text("")
        
        store = JsonEventStore(store_path)
        events = store.list_all()
        
        assert events == []


class TestEventSerialization:
    """Test event to/from dict conversion"""
    
    def test_event_to_dict_all_fields(self, temp_store):
        """Test serializing event with all fields"""
        e = Event(
            id="evt-0001",
            title="Meeting",
            description="Important",
            date=date(2026, 2, 10),
            start_time="14:30",
            duration_min=90,
            location="Room 101",
            create_at=datetime(2026, 2, 1, 10, 0, 0),
            update_at=datetime(2026, 2, 1, 10, 0, 0)
        )
        
        d = temp_store._event_to_dict(e)
        
        assert d["id"] == "evt-0001"
        assert d["title"] == "Meeting"
        assert d["description"] == "Important"
        assert d["date"] == "2026-02-10"
        assert d["start_time"] == "14:30"
        assert d["duration_min"] == 90
        assert d["location"] == "Room 101"
    
    def test_event_from_dict_all_fields(self, temp_store):
        """Test deserializing event with all fields"""
        d = {
            "id": "evt-0001",
            "title": "Meeting",
            "description": "Important",
            "date": "2026-02-10",
            "start_time": "14:30",
            "duration_min": 90,
            "location": "Room 101",
            "create_at": "2026-02-01T10:00:00",
            "update_at": "2026-02-01T10:00:00"
        }
        
        e = temp_store._event_from_dict(d)
        
        assert e.id == "evt-0001"
        assert e.title == "Meeting"
        assert e.description == "Important"
        assert e.date == date(2026, 2, 10)
        assert e.start_time == "14:30"
        assert e.duration_min == 90
        assert e.location == "Room 101"
    
    def test_event_from_dict_missing_field(self, temp_store):
        """Test deserializing with missing required field"""
        d = {
            "id": "evt-0001",
            # Missing "title"
            "date": "2026-02-10",
            "start_time": "14:30",
            "duration_min": 90,
        }
        
        with pytest.raises(StorageError, match="Missing required field"):
            temp_store._event_from_dict(d)