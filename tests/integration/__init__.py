"""
Integration tests for calctl

Integration tests verify that multiple components work together correctly.
They use real dependencies (real files, real storage) but are still relatively fast.

Guidelines:
- Use real JsonEventStore with temp files
- Test component interactions
- Tests should be < 0.1s
- Clean up resources in fixtures
"""

import pytest
import tempfile
from pathlib import Path
from datetime import date, datetime

from calctl.store import JsonEventStore
from calctl.service import CalendarService
from calctl.models import Event


# ============================================================================
# Shared Fixtures for Integration Tests
# ============================================================================

@pytest.fixture
def temp_data_path():
    """
    Create a temporary file path for testing
    
    Yields:
        Path: Temporary file path
    
    Cleanup:
        Removes the temporary file after test
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def real_store(temp_data_path):
    """
    Create a real JsonEventStore with temporary file
    
    Returns:
        JsonEventStore: Store instance with temp file
    """
    return JsonEventStore(temp_data_path)


@pytest.fixture
def integrated_service(temp_data_path):
    """
    Create a CalendarService with real store
    
    Returns:
        tuple: (CalendarService, Path) - Service and data file path
    """
    store = JsonEventStore(temp_data_path)
    service = CalendarService(store)
    return service, temp_data_path


# ============================================================================
# Helper Functions
# ============================================================================

def make_real_event(
    event_id: str,
    title: str,
    event_date: date,
    start_time: str = "10:00",
    duration: int = 60
) -> Event:
    """
    Create a real Event object for testing
    
    Args:
        event_id: Event ID
        title: Event title
        event_date: Event date
        start_time: Start time (HH:MM)
        duration: Duration in minutes
    
    Returns:
        Event: Real Event instance
    """
    now = datetime.now()
    return Event(
        id=event_id,
        title=title,
        description=None,
        date=event_date,
        start_time=start_time,
        duration_min=duration,
        location=None,
        create_at=now,
        update_at=now
    )


def verify_file_contains_event(file_path: Path, event_id: str) -> bool:
    """
    Verify that a JSON file contains an event with given ID
    
    Args:
        file_path: Path to JSON file
        event_id: Event ID to look for
    
    Returns:
        bool: True if event found in file
    """
    import json
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return any(e["id"] == event_id for e in data.get("events", []))


# ============================================================================
# Test Markers
# ============================================================================

pytest.mark.integration = pytest.mark.integration