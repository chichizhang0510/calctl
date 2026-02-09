"""
Unit tests for calctl

Unit tests are fast, isolated tests that use mocks for dependencies.
Each test should test a single unit of functionality.

Guidelines:
- Use Mock/patch for external dependencies
- Tests should be < 0.01s
- One assertion per test (ideally)
- Follow AAA pattern (Arrange-Act-Assert)
"""

import pytest
from unittest.mock import Mock
from datetime import date, datetime


# ============================================================================
# Shared Fixtures for Unit Tests
# ============================================================================

@pytest.fixture
def mock_store():
    """Create a mock store for testing services"""
    return Mock()


@pytest.fixture
def mock_datetime():
    """Create a fixed datetime for testing"""
    return datetime(2026, 2, 10, 12, 0, 0)


# ============================================================================
# Helper Functions
# ============================================================================

def make_mock_event(event_id: str, title: str, event_date: date):
    """
    Create a mock event for testing
    
    Args:
        event_id: Event ID (e.g., 'evt-1234')
        title: Event title
        event_date: Event date
    
    Returns:
        Mock: Mock event object with common attributes
    """
    mock_event = Mock()
    mock_event.id = event_id
    mock_event.title = title
    mock_event.date = event_date
    mock_event.start_time = "10:00"
    mock_event.duration_min = 60
    mock_event.description = None
    mock_event.location = None
    mock_event.create_at = datetime.now()
    mock_event.update_at = datetime.now()
    return mock_event


def assert_error_raised(func, error_class, message_contains=None):
    """
    Helper to assert that an error is raised with optional message check
    
    Args:
        func: Function to call
        error_class: Expected error class
        message_contains: Optional substring to check in error message
    """
    import pytest
    
    if message_contains:
        with pytest.raises(error_class, match=message_contains):
            func()
    else:
        with pytest.raises(error_class):
            func()


# ============================================================================
# Test Markers
# ============================================================================

# Mark tests as unit tests
pytest.mark.unit = pytest.mark.unit