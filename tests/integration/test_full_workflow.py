"""
Integration tests for complete user workflows

Tests complete scenarios that users would perform, including:
- Multiple operations in sequence
- Complex data manipulations
- Edge cases and boundary conditions
- Error recovery scenarios
"""

import pytest
import json
from pathlib import Path
from datetime import date, datetime, timedelta

from calctl.store import JsonEventStore
from calctl.service import CalendarService
from calctl.errors import InvalidInputError, NotFoundError, ConflictError, StorageError


class TestCompleteUserJourneys:
    """Test complete user scenarios from start to finish"""
    
    def test_new_user_first_week_workflow(self, integrated_service):
        """Test a new user's first week of using the app"""
        svc, data_path = integrated_service
        
        # Day 1: Add first event
        events = svc.add_event("Morning Meeting", "2026-02-10", "09:00", 30)
        meeting_id = events[0].id
        
        # Day 1: Add lunch
        svc.add_event("Lunch", "2026-02-10", "12:00", 60)
        
        # Day 2: Add recurring standup
        standups = svc.add_event(
            "Daily Standup",
            "2026-02-11",
            "09:00",
            15,
            repeat="daily",
            count=5
        )
        assert len(standups) == 5
        
        # Day 3: Realize meeting time changed, edit it
        updated, changes = svc.edit_event(meeting_id, time_str="10:00")
        assert "start_time" in changes
        
        # Day 4: Add all-hands meeting
        svc.add_event("All Hands Meeting", "2026-02-13", "14:00", 60)
        
        # Day 5: Search for all meetings
        meetings = svc.search_events("meeting")
        assert len(meetings) == 2  # Morning Meeting + All Hands
        
        # Week end: Review all events
        all_events = svc.list_events()
        assert len(all_events) == 8  # 2 + 5 standups + 1 all-hands
        
        # Verify persistence
        with open(data_path, 'r') as f:
            data = json.load(f)
        assert len(data["events"]) == 8
    
    def test_busy_professional_day(self, integrated_service):
        """Test a very busy day with many events"""
        svc, _ = integrated_service
        
        # Morning routine
        svc.add_event("Gym", "2026-02-10", "06:00", 60)
        svc.add_event("Breakfast", "2026-02-10", "07:30", 30)
        svc.add_event("Commute", "2026-02-10", "08:00", 30)
        
        # Work day - back-to-back meetings
        svc.add_event("Team Standup", "2026-02-10", "09:00", 15)
        svc.add_event("1-on-1 with Manager", "2026-02-10", "09:30", 30)
        svc.add_event("Project Review", "2026-02-10", "10:00", 60)
        svc.add_event("Client Call", "2026-02-10", "11:00", 45)
        svc.add_event("Lunch Break", "2026-02-10", "12:00", 60)
        svc.add_event("Design Discussion", "2026-02-10", "13:00", 90)
        svc.add_event("Code Review", "2026-02-10", "15:00", 45)
        svc.add_event("Planning Meeting", "2026-02-10", "16:00", 60)
        
        # Evening
        svc.add_event("Dinner", "2026-02-10", "18:00", 60)
        
        # Verify all events created
        events = svc.list_events()
        assert len(events) == 12
        
        # Verify they're all on the same day
        assert all(e.date == date(2026, 2, 10) for e in events)
        
        # No conflicts (all sequential)
        for i in range(len(events) - 1):
            assert events[i].end_dt() <= events[i + 1].start_dt()


class TestEdgeCaseScenarios:
    """Test edge cases and boundary conditions"""
    
    def test_event_at_midnight_boundary(self, integrated_service):
        """Test events at midnight (00:00)"""
        svc, _ = integrated_service
        
        # Event starting at midnight
        events = svc.add_event("Midnight Task", "2026-02-10", "00:00", 30)
        assert events[0].start_time == "00:00"
        
        # Retrieve and verify
        retrieved = svc.show_event(events[0].id)
        assert retrieved.start_time == "00:00"
    
    def test_event_ending_at_midnight(self, integrated_service):
        """Test event that ends exactly at midnight"""
        svc, _ = integrated_service
        
        # Event from 22:00 to 00:00 (2 hours)
        with pytest.raises(InvalidInputError, match="cross midnight"):
            svc.add_event("Late Night", "2026-02-10", "22:00", 120)
    
    def test_very_short_event(self, integrated_service):
        """Test 1-minute event"""
        svc, _ = integrated_service
        
        events = svc.add_event("Quick Check", "2026-02-10", "10:00", 1)
        assert events[0].duration_min == 1
        
        end_time = events[0].end_dt()
        start_time = events[0].start_dt()
        assert (end_time - start_time).total_seconds() == 60
    
    def test_maximum_duration_event(self, integrated_service):
        """Test 24-hour event (maximum allowed)"""
        svc, _ = integrated_service
        
        # 24 hours starting at 00:00
        with pytest.raises(InvalidInputError, match="cross midnight"):
            svc.add_event("All Day", "2026-02-10", "00:00", 1440)
        
        # But 23:59 should work
        events = svc.add_event("Almost All Day", "2026-02-10", "00:00", 1439)
        assert events[0].duration_min == 1439
    
    def test_many_events_same_time_with_force(self, integrated_service):
        """Test adding many overlapping events with force"""
        svc, _ = integrated_service
        
        # Add 10 events at the same time (with force)
        for i in range(10):
            svc.add_event(f"Meeting {i}", "2026-02-10", "10:00", 60, force=True)
        
        events = svc.list_events()
        assert len(events) == 10
        
        # All should overlap
        first_event = events[0]
        conflicts = [e for e in events if e.id != first_event.id]
        
        from calctl.conflict import overlaps
        for conflict in conflicts:
            assert overlaps(first_event, conflict)
    
    def test_event_with_very_long_title(self, integrated_service):
        """Test event with extremely long title"""
        svc, _ = integrated_service
        
        long_title = "A" * 1000  # 1000 characters
        events = svc.add_event(long_title, "2026-02-10", "10:00", 60)
        
        retrieved = svc.show_event(events[0].id)
        assert retrieved.title == long_title
        assert len(retrieved.title) == 1000
    
    def test_event_with_special_characters(self, integrated_service):
        """Test event with special characters in all fields"""
        svc, _ = integrated_service
        
        special_chars = "!@#$%^&*()[]{}|\\;:'\",<.>/?"
        events = svc.add_event(
            title=f"Title {special_chars}",
            date_str="2026-02-10",
            time_str="10:00",
            duration=60,
            description=f"Description {special_chars}",
            location=f"Location {special_chars}"
        )
        
        retrieved = svc.show_event(events[0].id)
        assert special_chars in retrieved.title
        assert special_chars in retrieved.description
        assert special_chars in retrieved.location
    
    def test_event_with_unicode_characters(self, integrated_service):
        """Test event with emoji and unicode"""
        svc, _ = integrated_service
        
        events = svc.add_event(
            title="Meeting 📅 with Team 👥",
            date_str="2026-02-10",
            time_str="10:00",
            duration=60,
            description="讨论项目进度 🚀",
            location="会议室 🏢"
        )
        
        retrieved = svc.show_event(events[0].id)
        assert "📅" in retrieved.title
        assert "🚀" in retrieved.description
        assert "🏢" in retrieved.location


class TestRecurringEventEdgeCases:
    """Test edge cases for recurring events"""
    
    def test_recurring_event_spanning_month_boundary(self, integrated_service):
        """Test daily recurring events that cross month boundaries"""
        svc, _ = integrated_service
        
        # Create daily events from Feb 26 to Mar 5 (10 days)
        events = svc.add_event(
            "Daily Task",
            "2026-02-26",
            "10:00",
            30,
            repeat="daily",
            count=8  # Feb 26-28 (3) + Mar 1-5 (5)
        )
        
        assert len(events) == 8
        
        # Check dates span months
        assert events[0].date == date(2026, 2, 26)
        assert events[2].date == date(2026, 2, 28)
        assert events[3].date == date(2026, 3, 1)
        assert events[7].date == date(2026, 3, 5)
    
    def test_recurring_event_spanning_year_boundary(self, integrated_service):
        """Test weekly recurring events that cross year boundaries"""
        svc, _ = integrated_service
        
        # Create weekly events from Dec 25, 2026 (4 weeks)
        events = svc.add_event(
            "Weekly Review",
            "2026-12-25",
            "10:00",
            60,
            repeat="weekly",
            count=4
        )
        
        assert len(events) == 4
        assert events[0].date == date(2026, 12, 25)
        assert events[1].date == date(2027, 1, 1)  # New year!
        assert events[3].date == date(2027, 1, 15)
    
    def test_many_recurring_events(self, integrated_service):
        """Test creating many recurring events (stress test)"""
        svc, _ = integrated_service
        
        # Create 100 daily events
        events = svc.add_event(
            "Daily Standup",
            "2026-02-01",
            "09:00",
            15,
            repeat="daily",
            count=100
        )
        
        assert len(events) == 100
        
        # Verify all persisted
        all_events = svc.list_events(from_date=date(2026, 2, 1), to_date=date(2026, 5, 31))
        assert len(all_events) == 100
        
        # Verify dates are consecutive
        for i in range(1, len(events)):
            delta = events[i].date - events[i-1].date
            assert delta.days == 1


class TestConflictDetectionEdgeCases:
    """Test edge cases in conflict detection"""
    
    def test_adjacent_events_no_conflict(self, integrated_service):
        """Test that adjacent events (touching but not overlapping) don't conflict"""
        svc, _ = integrated_service
        
        # First event: 10:00-11:00
        svc.add_event("Meeting 1", "2026-02-10", "10:00", 60)
        
        # Second event: 11:00-12:00 (starts when first ends)
        events = svc.add_event("Meeting 2", "2026-02-10", "11:00", 60)
        
        # Should succeed (no conflict)
        assert len(events) == 1
        
        all_events = svc.list_events()
        assert len(all_events) == 2
    
    def test_one_minute_overlap_detected(self, integrated_service):
        """Test that even 1 minute overlap is detected"""
        svc, _ = integrated_service
        
        # First event: 10:00-11:00
        svc.add_event("Meeting 1", "2026-02-10", "10:00", 60)
        
        # Second event: 10:59-11:59 (1 minute overlap)
        with pytest.raises(ConflictError):
            svc.add_event("Meeting 2", "2026-02-10", "10:59", 60)
    
    def test_contained_event_conflict(self, integrated_service):
        """Test that smaller event inside larger event conflicts"""
        svc, _ = integrated_service
        
        # Large event: 09:00-12:00
        svc.add_event("Long Meeting", "2026-02-10", "09:00", 180)
        
        # Small event inside: 10:00-10:30
        with pytest.raises(ConflictError):
            svc.add_event("Short Meeting", "2026-02-10", "10:00", 30)
    
    def test_recurring_events_with_conflicts(self, integrated_service):
        """Test conflict detection across recurring events"""
        svc, _ = integrated_service
        
        # Create weekly meeting
        svc.add_event("Weekly Standup", "2026-02-10", "10:00", 30, repeat="weekly", count=4)
        
        # Try to create daily meeting that conflicts with one occurrence
        with pytest.raises(ConflictError):
            svc.add_event("Daily Check", "2026-02-10", "10:15", 30, repeat="daily", count=3)


class TestDataIntegrityAndCornerCases:
    """Test data integrity and corner cases"""
    
    def test_edit_to_create_conflict_fails(self, integrated_service):
        """Test that editing an event to create a conflict fails"""
        svc, _ = integrated_service
        
        # Create two events
        event1 = svc.add_event("Meeting 1", "2026-02-10", "10:00", 60)[0]
        event2 = svc.add_event("Meeting 2", "2026-02-10", "14:00", 60)[0]
        
        # Try to edit event2 to overlap with event1
        with pytest.raises(ConflictError):
            svc.edit_event(event2.id, time_str="10:30")
    
    def test_delete_and_recreate_same_id_pattern(self, integrated_service):
        """Test deleting event and verifying it's truly gone"""
        svc, _ = integrated_service
        
        # Create event
        events = svc.add_event("Test Event", "2026-02-10", "10:00", 60)
        event_id = events[0].id
        
        # Delete it
        svc.delete_event(event_id)
        
        # Verify it's gone
        with pytest.raises(NotFoundError):
            svc.show_event(event_id)
        
        # Create new event - should get different ID
        new_events = svc.add_event("New Event", "2026-02-10", "10:00", 60)
        new_id = new_events[0].id
        
        assert new_id != event_id
    
    def test_multiple_services_same_file(self, temp_data_path):
        """Test multiple service instances accessing same file"""
        store1 = JsonEventStore(temp_data_path)
        svc1 = CalendarService(store1)
        
        store2 = JsonEventStore(temp_data_path)
        svc2 = CalendarService(store2)
        
        # Add event via service 1
        events = svc1.add_event("Event 1", "2026-02-10", "10:00", 60)
        event_id = events[0].id
        
        # Read via service 2
        retrieved = svc2.show_event(event_id)
        assert retrieved.title == "Event 1"
        
        # Add event via service 2
        svc2.add_event("Event 2", "2026-02-11", "10:00", 60)
        
        # List via service 1
        all_events = svc1.list_events()
        assert len(all_events) == 2
    
    def test_empty_optional_fields(self, integrated_service):
        """Test event with all optional fields empty"""
        svc, _ = integrated_service
        
        events = svc.add_event(
            title="Minimal Event",
            date_str="2026-02-10",
            time_str="10:00",
            duration=60,
            description=None,
            location=None
        )
        
        retrieved = svc.show_event(events[0].id)
        assert retrieved.description is None
        assert retrieved.location is None
    
    def test_whitespace_handling_in_fields(self, integrated_service):
        """Test that whitespace is handled correctly"""
        svc, _ = integrated_service
        
        # Fields with leading/trailing whitespace
        events = svc.add_event(
            title="  Title with spaces  ",
            date_str="2026-02-10",
            time_str="10:00",
            duration=60,
            description="  Description  ",
            location="  Location  "
        )
        
        retrieved = svc.show_event(events[0].id)
        # Service should strip whitespace
        assert retrieved.title == "Title with spaces"
        assert retrieved.description == "Description"
        assert retrieved.location == "Location"


class TestSearchAndFilterEdgeCases:
    """Test edge cases in search and filtering"""
    
    def test_search_case_insensitive(self, integrated_service):
        """Test that search is case-insensitive"""
        svc, _ = integrated_service
        
        svc.add_event("IMPORTANT Meeting", "2026-02-10", "10:00", 60)
        svc.add_event("important task", "2026-02-11", "10:00", 60)
        svc.add_event("Not Important", "2026-02-12", "10:00", 60)
        
        # Search should find all three
        results = svc.search_events("important")
        assert len(results) == 3
    
    def test_search_with_special_characters(self, integrated_service):
        """Test search with special characters in query"""
        svc, _ = integrated_service
        
        svc.add_event("Team @ Office", "2026-02-10", "10:00", 60)
        svc.add_event("Meeting @ Home", "2026-02-11", "10:00", 60)
        
        results = svc.search_events("@")
        assert len(results) == 2
    
    def test_list_events_across_year_boundary(self, integrated_service):
        """Test listing events that span year boundaries"""
        svc, _ = integrated_service
        
        svc.add_event("Event 2026", "2026-12-31", "10:00", 60)
        svc.add_event("Event 2027", "2027-01-01", "10:00", 60)
        
        # List all
        all_events = svc.list_events(
            from_date=date(2026, 12, 1),
            to_date=date(2027, 1, 31)
        )
        assert len(all_events) == 2
    
    def test_filter_with_no_results(self, integrated_service):
        """Test filtering that returns no results"""
        svc, _ = integrated_service
        
        svc.add_event("Event", "2026-02-10", "10:00", 60)
        
        # Filter to different date range
        results = svc.list_events(
            from_date=date(2026, 3, 1),
            to_date=date(2026, 3, 31)
        )
        assert len(results) == 0


class TestBulkOperations:
    """Test bulk operations and large datasets"""
    
    def test_delete_many_events_by_date(self, integrated_service):
        """Test deleting many events on same date"""
        svc, _ = integrated_service
        
        # Add 20 events on same date
        for i in range(20):
            svc.add_event(f"Event {i}", "2026-02-10", f"{9+i%8}:00", 30, force=True)
        
        # Add some events on different date
        svc.add_event("Keep 1", "2026-02-11", "10:00", 60)
        svc.add_event("Keep 2", "2026-02-12", "10:00", 60)
        
        # Delete all events on 2026-02-10
        count = svc.delete_on_date("2026-02-10")
        assert count == 20
        
        # Only 2 events should remain
        remaining = svc.list_events()
        assert len(remaining) == 2


class TestTimeZoneAndDateEdgeCases:
    """Test edge cases related to dates and times"""
    
    def test_leap_year_date(self, integrated_service):
        """Test event on leap year date (Feb 29)"""
        svc, _ = integrated_service
        
        # 2024 is a leap year
        events = svc.add_event("Leap Day Event", "2024-02-29", "10:00", 60)
        assert events[0].date == date(2024, 2, 29)
    
    def test_last_day_of_month(self, integrated_service):
        """Test events on last days of various months"""
        svc, _ = integrated_service
        
        # Different month lengths
        svc.add_event("End of Jan", "2026-01-31", "10:00", 60)  # 31 days
        svc.add_event("End of Feb", "2026-02-28", "10:00", 60)  # 28 days
        svc.add_event("End of Apr", "2026-04-30", "10:00", 60)  # 30 days
        
        events = svc.list_events(from_date=date(2026, 1, 1), to_date=date(2026, 12, 31))
        assert len(events) == 3