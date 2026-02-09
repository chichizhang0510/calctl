"""
Integration tests for Store + Service layer

These tests use real JsonEventStore with temporary files to verify
that the service and storage layers work correctly together.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import date, datetime

from calctl.store import JsonEventStore
from calctl.service import CalendarService
from calctl.errors import ConflictError, NotFoundError


class TestAddAndRetrieve:
    """Test adding events and retrieving them"""
    
    def test_add_single_event_persists(self, integrated_service):
        """Test that adding an event persists to disk"""
        svc, data_path = integrated_service
        
        # Add event
        events = svc.add_event(
            "Team Meeting",
            "2026-02-10",
            "14:00",
            60,
            description="Weekly sync",
            location="Room 101"
        )
        
        assert len(events) == 1
        event_id = events[0].id
        
        # Verify in service
        retrieved = svc.show_event(event_id)
        assert retrieved.title == "Team Meeting"
        assert retrieved.description == "Weekly sync"
        
        # Verify in file
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "Team Meeting"
    
    def test_add_multiple_events_maintains_order(self, integrated_service):
        """Test that multiple events are stored and retrieved in order"""
        svc, _ = integrated_service
        
        # Add events in specific order
        svc.add_event("Event 1", "2026-02-15", "10:00", 30)
        svc.add_event("Event 2", "2026-02-10", "14:00", 45)
        svc.add_event("Event 3", "2026-02-12", "09:00", 60)
        
        # List should be sorted by date
        events = svc.list_events()
        assert len(events) == 3
        assert events[0].date == date(2026, 2, 10)
        assert events[1].date == date(2026, 2, 12)
        assert events[2].date == date(2026, 2, 15)


class TestFullCRUDWorkflow:
    """Test complete Create-Read-Update-Delete workflow"""
    
    def test_complete_event_lifecycle(self, integrated_service):
        """Test creating, reading, updating, and deleting an event"""
        svc, data_path = integrated_service
        
        # 1. CREATE
        events = svc.add_event("Original Title", "2026-02-10", "10:00", 60)
        event_id = events[0].id
        
        # 2. READ
        event = svc.show_event(event_id)
        assert event.title == "Original Title"
        
        # 3. UPDATE (using edit_event)
        updated, changes = svc.edit_event(
            event_id,
            title="Updated Title",
            duration=90
        )
        assert updated.title == "Updated Title"
        assert updated.duration_min == 90
        assert "title" in changes
        assert "duration_min" in changes
        
        # Verify update persisted
        event = svc.show_event(event_id)
        assert event.title == "Updated Title"
        
        # 4. DELETE
        deleted = svc.delete_event(event_id)
        assert deleted.id == event_id
        
        # Verify deletion
        with pytest.raises(NotFoundError):
            svc.show_event(event_id)
        
        # Verify file is empty
        events = svc.list_events()
        assert len(events) == 0


class TestConflictDetection:
    """Test conflict detection across service and store"""
    
    def test_adding_conflicting_events_raises_error(self, integrated_service):
        """Test that conflicting events are detected"""
        svc, _ = integrated_service
        
        # Add first event
        svc.add_event("Meeting 1", "2026-02-10", "14:00", 60)
        
        # Try to add conflicting event
        with pytest.raises(ConflictError) as exc_info:
            svc.add_event("Meeting 2", "2026-02-10", "14:30", 60)
        
        assert "conflict" in str(exc_info.value).lower()
    
    def test_force_add_allows_conflicts(self, integrated_service):
        """Test that force=True bypasses conflict detection"""
        svc, _ = integrated_service
        
        # Add first event
        svc.add_event("Meeting 1", "2026-02-10", "14:00", 60)
        
        # Force add conflicting event
        events = svc.add_event("Meeting 2", "2026-02-10", "14:30", 60, force=True)
        
        assert len(events) == 1
        
        # Both events should exist
        all_events = svc.list_events()
        assert len(all_events) == 2


class TestRecurringEvents:
    """Test recurring event creation"""
    
    def test_daily_recurring_events_persist(self, integrated_service):
        """Test that daily recurring events are all persisted"""
        svc, _ = integrated_service
        
        # Create 5 daily events
        events = svc.add_event(
            "Standup",
            "2026-02-10",
            "09:00",
            15,
            repeat="daily",
            count=5
        )
        
        assert len(events) == 5
        
        # Verify all persisted
        all_events = svc.list_events()
        assert len(all_events) == 5
        
        # Verify dates
        for i, event in enumerate(all_events):
            expected_date = date(2026, 2, 10 + i)
            assert event.date == expected_date
    
    def test_weekly_recurring_events_persist(self, integrated_service):
        """Test that weekly recurring events are all persisted"""
        svc, _ = integrated_service
        
        events = svc.add_event(
            "Team Meeting",
            "2026-02-10",
            "14:00",
            60,
            repeat="weekly",
            count=3
        )
        
        assert len(events) == 3
        
        # Verify dates are 7 days apart
        all_events = svc.list_events()
        assert all_events[0].date == date(2026, 2, 10)
        assert all_events[1].date == date(2026, 2, 17)
        assert all_events[2].date == date(2026, 2, 24)


class TestSearchAndFilter:
    """Test search and filtering functionality"""
    
    def test_search_finds_persisted_events(self, integrated_service):
        """Test search functionality with real data"""
        svc, _ = integrated_service
        
        # Add diverse events
        svc.add_event("Team Meeting", "2026-02-10", "10:00", 60)
        svc.add_event("Lunch Break", "2026-02-10", "12:00", 45)
        svc.add_event("Client Meeting", "2026-02-11", "14:00", 90)
        
        # Search for "meeting"
        results = svc.search_events("meeting")
        assert len(results) == 2
        assert all("meeting" in e.title.lower() for e in results)
    
    def test_list_events_with_date_filters(self, integrated_service):
        """Test date filtering with real data"""
        svc, _ = integrated_service
        
        # Add events on different dates
        svc.add_event("Event 1", "2026-02-10", "10:00", 60)
        svc.add_event("Event 2", "2026-02-15", "10:00", 60)
        svc.add_event("Event 3", "2026-02-20", "10:00", 60)
        
        # Filter by date range
        filtered = svc.list_events(
            from_date=date(2026, 2, 12),
            to_date=date(2026, 2, 18)
        )
        
        assert len(filtered) == 1
        assert filtered[0].title == "Event 2"


class TestDeleteOperations:
    """Test various delete operations"""
    
    def test_delete_by_date_removes_all_events(self, integrated_service):
        """Test deleting all events on a specific date"""
        svc, _ = integrated_service
        
        # Add multiple events on same date
        svc.add_event("Event 1", "2026-02-10", "09:00", 30)
        svc.add_event("Event 2", "2026-02-10", "14:00", 45)
        svc.add_event("Event 3", "2026-02-11", "10:00", 60)
        
        # Delete all events on 2026-02-10
        count = svc.delete_on_date("2026-02-10")
        assert count == 2
        
        # Verify only Event 3 remains
        remaining = svc.list_events()
        assert len(remaining) == 1
        assert remaining[0].title == "Event 3"


class TestDataPersistence:
    """Test that data persists across service instances"""
    
    def test_data_survives_service_restart(self, temp_data_path):
        """Test that data persists when service is recreated"""
        # Create service and add event
        store1 = JsonEventStore(temp_data_path)
        svc1 = CalendarService(store1)
        
        events = svc1.add_event("Persistent Event", "2026-02-10", "10:00", 60)
        event_id = events[0].id
        
        # Destroy service (simulate restart)
        del svc1
        del store1
        
        # Create new service with same file
        store2 = JsonEventStore(temp_data_path)
        svc2 = CalendarService(store2)
        
        # Data should still be there
        retrieved = svc2.show_event(event_id)
        assert retrieved.title == "Persistent Event"
        
        all_events = svc2.list_events()
        assert len(all_events) == 1


class TestConcurrentOperations:
    """Test edge cases with multiple operations"""
    
    def test_multiple_edits_persist_correctly(self, integrated_service):
        """Test that multiple edits are all persisted"""
        svc, _ = integrated_service
        
        # Create event
        events = svc.add_event("Original", "2026-02-10", "10:00", 60)
        event_id = events[0].id
        
        # Edit multiple times
        svc.edit_event(event_id, title="Updated 1")
        svc.edit_event(event_id, duration=90)
        svc.edit_event(event_id, title="Final Title")
        
        # Verify final state
        event = svc.show_event(event_id)
        assert event.title == "Final Title"
        assert event.duration_min == 90