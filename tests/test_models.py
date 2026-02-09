"""
Unit tests for calctl.models

Tests the Event dataclass and its methods.
"""

import pytest
from datetime import date, datetime, timedelta
from calctl.models import Event


class TestEventCreation:
    """Test Event object creation and immutability"""
    
    def test_event_creation_with_all_fields(self):
        """Test creating an Event with all fields"""
        now = datetime.now()
        e = Event(
            id="evt-1234",
            title="Team Meeting",
            description="Weekly standup",
            date=date(2026, 2, 10),
            start_time="09:00",
            duration_min=30,
            location="Conference Room A",
            create_at=now,
            update_at=now
        )
        
        assert e.id == "evt-1234"
        assert e.title == "Team Meeting"
        assert e.description == "Weekly standup"
        assert e.date == date(2026, 2, 10)
        assert e.start_time == "09:00"
        assert e.duration_min == 30
        assert e.location == "Conference Room A"
        assert e.create_at == now
        assert e.update_at == now
    
    def test_event_creation_with_optional_none(self):
        """Test creating an Event with None optional fields"""
        now = datetime.now()
        e = Event(
            id="evt-5678",
            title="Quick Task",
            description=None,
            date=date(2026, 2, 10),
            start_time="14:30",
            duration_min=15,
            location=None,
            create_at=now,
            update_at=now
        )
        
        assert e.description is None
        assert e.location is None
    
    def test_event_is_immutable(self):
        """Test that Event is frozen and cannot be modified"""
        now = datetime.now()
        e = Event(
            id="evt-0000",
            title="Test",
            description=None,
            date=date(2026, 2, 10),
            start_time="10:00",
            duration_min=60,
            location=None,
            create_at=now,
            update_at=now
        )
        
        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(AttributeError):
            e.title = "New Title"
        
        with pytest.raises(AttributeError):
            e.duration_min = 90


class TestEventStartDt:
    """Test Event.start_dt() method"""
    
    def test_start_dt_morning(self):
        """Test start_dt calculation for morning time"""
        e = Event(
            id="evt-0001",
            title="Morning Meeting",
            description=None,
            date=date(2026, 2, 10),
            start_time="09:30",
            duration_min=60,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        dt = e.start_dt()
        assert dt.date() == date(2026, 2, 10)
        assert dt.hour == 9
        assert dt.minute == 30
        assert dt.second == 0
    
    def test_start_dt_afternoon(self):
        """Test start_dt calculation for afternoon time"""
        e = Event(
            id="evt-0002",
            title="Afternoon Meeting",
            description=None,
            date=date(2026, 3, 15),
            start_time="14:45",
            duration_min=30,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        dt = e.start_dt()
        assert dt.date() == date(2026, 3, 15)
        assert dt.hour == 14
        assert dt.minute == 45
    
    def test_start_dt_midnight(self):
        """Test start_dt calculation for midnight"""
        e = Event(
            id="evt-0003",
            title="Midnight Task",
            description=None,
            date=date(2026, 2, 10),
            start_time="00:00",
            duration_min=30,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        dt = e.start_dt()
        assert dt.hour == 0
        assert dt.minute == 0
    
    def test_start_dt_end_of_day(self):
        """Test start_dt calculation for late evening"""
        e = Event(
            id="evt-0004",
            title="Late Meeting",
            description=None,
            date=date(2026, 2, 10),
            start_time="23:45",
            duration_min=10,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        dt = e.start_dt()
        assert dt.hour == 23
        assert dt.minute == 45


class TestEventEndDt:
    """Test Event.end_dt() method"""
    
    def test_end_dt_simple_case(self):
        """Test end_dt calculation for simple duration"""
        e = Event(
            id="evt-0005",
            title="30 min meeting",
            description=None,
            date=date(2026, 2, 10),
            start_time="10:00",
            duration_min=30,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        end = e.end_dt()
        assert end.hour == 10
        assert end.minute == 30
    
    def test_end_dt_crosses_hour_boundary(self):
        """Test end_dt when duration crosses hour boundary"""
        e = Event(
            id="evt-0006",
            title="Cross hour",
            description=None,
            date=date(2026, 2, 10),
            start_time="14:45",
            duration_min=30,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        end = e.end_dt()
        assert end.hour == 15
        assert end.minute == 15
    
    def test_end_dt_multiple_hours(self):
        """Test end_dt with multi-hour duration"""
        e = Event(
            id="evt-0007",
            title="Long meeting",
            description=None,
            date=date(2026, 2, 10),
            start_time="09:00",
            duration_min=150,  # 2.5 hours
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        end = e.end_dt()
        assert end.hour == 11
        assert end.minute == 30
    
    def test_end_dt_full_day(self):
        """Test end_dt with maximum allowed duration"""
        e = Event(
            id="evt-0008",
            title="All day",
            description=None,
            date=date(2026, 2, 10),
            start_time="00:00",
            duration_min=1440,  # 24 hours
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        end = e.end_dt()
        # Should be next day at 00:00
        assert end.date() == date(2026, 2, 11)
        assert end.hour == 0
        assert end.minute == 0
    
    def test_end_dt_preserves_date_info(self):
        """Test that end_dt preserves date information"""
        e = Event(
            id="evt-0009",
            title="Test",
            description=None,
            date=date(2026, 2, 10),
            start_time="14:00",
            duration_min=90,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        start = e.start_dt()
        end = e.end_dt()
        
        # Verify relationship
        assert (end - start) == timedelta(minutes=90)


class TestEventEdgeCases:
    """Test Event edge cases and boundary conditions"""
    
    def test_zero_duration_event(self):
        """Test event with zero duration (instant event)"""
        e = Event(
            id="evt-0010",
            title="Instant",
            description=None,
            date=date(2026, 2, 10),
            start_time="12:00",
            duration_min=0,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        assert e.start_dt() == e.end_dt()
    
    def test_event_with_empty_string_fields(self):
        """Test that empty strings can be stored (validation is service layer)"""
        e = Event(
            id="",
            title="",
            description="",
            date=date(2026, 2, 10),
            start_time="10:00",
            duration_min=30,
            location="",
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        assert e.id == ""
        assert e.title == ""
        assert e.description == ""
        assert e.location == ""
    
    def test_event_equality(self):
        """Test that two events with same data are equal (dataclass)"""
        now = datetime(2026, 2, 10, 12, 0, 0)
        
        e1 = Event(
            id="evt-1234",
            title="Test",
            description=None,
            date=date(2026, 2, 10),
            start_time="10:00",
            duration_min=30,
            location=None,
            create_at=now,
            update_at=now
        )
        
        e2 = Event(
            id="evt-1234",
            title="Test",
            description=None,
            date=date(2026, 2, 10),
            start_time="10:00",
            duration_min=30,
            location=None,
            create_at=now,
            update_at=now
        )
        
        assert e1 == e2
    
    def test_event_hash(self):
        """Test that frozen dataclass is hashable"""
        e = Event(
            id="evt-1234",
            title="Test",
            description=None,
            date=date(2026, 2, 10),
            start_time="10:00",
            duration_min=30,
            location=None,
            create_at=datetime.now(),
            update_at=datetime.now()
        )
        
        # Should be able to add to set
        event_set = {e}
        assert len(event_set) == 1
        assert e in event_set