"""
Unit tests for calctl.conflict

Tests the event overlap detection algorithm.
"""

import pytest
from datetime import date, datetime
from calctl.models import Event
from calctl.conflict import overlaps


def make_event(event_id: str, date_val: date, start: str, duration: int) -> Event:
    """Helper to create test events"""
    return Event(
        id=event_id,
        title="Test Event",
        description=None,
        date=date_val,
        start_time=start,
        duration_min=duration,
        location=None,
        create_at=datetime.now(),
        update_at=datetime.now()
    )


class TestNoOverlap:
    """Test cases where events do not overlap"""
    
    def test_different_dates_no_overlap(self):
        """Events on different dates never overlap"""
        e1 = make_event("evt-0001", date(2026, 2, 10), "10:00", 60)
        e2 = make_event("evt-0002", date(2026, 2, 11), "10:00", 60)
        
        assert not overlaps(e1, e2)
        assert not overlaps(e2, e1)  # symmetric
    
    def test_sequential_events_no_overlap(self):
        """Sequential events (one ends when other starts) do not overlap"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "09:00", 60)  # 9:00-10:00
        e2 = make_event("evt-0002", d, "10:00", 60)  # 10:00-11:00
        
        assert not overlaps(e1, e2)
        assert not overlaps(e2, e1)
    
    def test_morning_and_afternoon_no_overlap(self):
        """Morning and afternoon events with large gap"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "09:00", 60)   # 9:00-10:00
        e2 = make_event("evt-0002", d, "14:00", 60)   # 14:00-15:00
        
        assert not overlaps(e1, e2)
        assert not overlaps(e2, e1)
    
    def test_one_minute_gap_no_overlap(self):
        """Events with just 1 minute gap"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "10:00", 30)  # 10:00-10:30
        e2 = make_event("evt-0002", d, "10:31", 30)  # 10:31-11:01
        
        assert not overlaps(e1, e2)
    
    def test_same_id_no_overlap(self):
        """Same event (same ID) should not be considered overlapping"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-1234", d, "10:00", 60)
        e2 = make_event("evt-1234", d, "10:30", 60)  # Different time but same ID
        
        assert not overlaps(e1, e2)
        assert not overlaps(e2, e1)


class TestOverlap:
    """Test cases where events do overlap"""
    
    def test_partial_overlap_start(self):
        """Second event starts during first event"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "09:00", 60)  # 9:00-10:00
        e2 = make_event("evt-0002", d, "09:30", 60)  # 9:30-10:30
        
        assert overlaps(e1, e2)
        assert overlaps(e2, e1)
    
    def test_partial_overlap_end(self):
        """First event ends during second event"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "09:30", 60)  # 9:30-10:30
        e2 = make_event("evt-0002", d, "09:00", 60)  # 9:00-10:00
        
        assert overlaps(e1, e2)
        assert overlaps(e2, e1)
    
    def test_complete_containment_smaller_inside(self):
        """Smaller event completely contained in larger event"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "09:00", 120)  # 9:00-11:00
        e2 = make_event("evt-0002", d, "09:30", 30)   # 9:30-10:00
        
        assert overlaps(e1, e2)
        assert overlaps(e2, e1)
    
    def test_complete_containment_larger_contains(self):
        """Larger event contains smaller event"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "10:15", 15)   # 10:15-10:30
        e2 = make_event("evt-0002", d, "10:00", 60)   # 10:00-11:00
        
        assert overlaps(e1, e2)
        assert overlaps(e2, e1)
    
    def test_exact_same_time_and_duration(self):
        """Events at exactly the same time with same duration"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "14:00", 60)
        e2 = make_event("evt-0002", d, "14:00", 60)
        
        assert overlaps(e1, e2)
        assert overlaps(e2, e1)
    
    def test_one_minute_overlap(self):
        """Events that overlap by just 1 minute"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "10:00", 31)  # 10:00-10:31
        e2 = make_event("evt-0002", d, "10:30", 30)  # 10:30-11:00
        
        assert overlaps(e1, e2)
    
    def test_overlap_across_noon(self):
        """Events that overlap across noon"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "11:30", 60)  # 11:30-12:30
        e2 = make_event("evt-0002", d, "12:00", 60)  # 12:00-13:00
        
        assert overlaps(e1, e2)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_duration_events_no_overlap(self):
        """Zero duration events (instants) at different times"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "10:00", 0)
        e2 = make_event("evt-0002", d, "10:01", 0)
        
        assert not overlaps(e1, e2)
    
    def test_zero_duration_same_time_overlap(self):
        """Zero duration events at same time"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "10:00", 0)
        e2 = make_event("evt-0002", d, "10:00", 0)
        
        # Two instants at same time don't overlap (start < end condition)
        assert not overlaps(e1, e2)
    
    def test_very_long_events(self):
        """Very long duration events"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "00:00", 1440)  # All day: 00:00-24:00
        e2 = make_event("evt-0002", d, "12:00", 60)     # Lunch: 12:00-13:00
        
        assert overlaps(e1, e2)
    
    def test_late_night_events(self):
        """Events late at night"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "23:00", 30)  # 23:00-23:30
        e2 = make_event("evt-0002", d, "23:15", 30)  # 23:15-23:45
        
        assert overlaps(e1, e2)
    
    def test_midnight_start(self):
        """Events starting at midnight"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "00:00", 30)  # 00:00-00:30
        e2 = make_event("evt-0002", d, "00:15", 30)  # 00:15-00:45
        
        assert overlaps(e1, e2)


class TestSymmetry:
    """Test that overlap detection is symmetric"""
    
    def test_overlap_is_symmetric(self):
        """overlaps(a, b) == overlaps(b, a)"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "10:00", 60)
        e2 = make_event("evt-0002", d, "10:30", 60)
        
        # Both should overlap
        assert overlaps(e1, e2) == overlaps(e2, e1)
        assert overlaps(e1, e2) is True
    
    def test_no_overlap_is_symmetric(self):
        """Non-overlapping is also symmetric"""
        d = date(2026, 2, 10)
        e1 = make_event("evt-0001", d, "10:00", 30)
        e2 = make_event("evt-0002", d, "11:00", 30)
        
        assert overlaps(e1, e2) == overlaps(e2, e1)
        assert overlaps(e1, e2) is False


class TestIntervalLogic:
    """Test the interval overlap logic [start, end)"""
    
    def test_half_open_interval_semantics(self):
        """Test [start, end) half-open interval semantics"""
        d = date(2026, 2, 10)
        # e1: [09:00, 10:00)
        # e2: [10:00, 11:00)
        # These should NOT overlap
        e1 = make_event("evt-0001", d, "09:00", 60)
        e2 = make_event("evt-0002", d, "10:00", 60)
        
        assert not overlaps(e1, e2)
        
        # But if e2 starts at 09:59, they SHOULD overlap
        e3 = make_event("evt-0003", d, "09:59", 60)
        assert overlaps(e1, e3)