"""
Integration tests for CLI + Service + Store layers

These tests verify that the CLI layer correctly integrates with
the service and storage layers using real dependencies.

Note: These are NOT E2E tests (we don't use subprocess).
      We call main() directly but with real dependencies.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import patch
from datetime import date, datetime

from calctl.cli import main, build_parser
from calctl.errors import InvalidInputError, NotFoundError, ConflictError


@pytest.fixture
def isolated_cli_env(monkeypatch, tmp_path):
    """
    Create isolated environment for CLI testing
    
    Sets up temporary data directory and returns path
    """
    data_file = tmp_path / "events.json"
    
    # Mock default_data_path to use temp file
    def mock_default_path():
        return data_file
    
    monkeypatch.setattr("calctl.cli.default_data_path", mock_default_path)
    
    return data_file


def run_cli_command(*args):
    """
    Helper to run CLI command and capture output
    
    Args:
        *args: Command arguments
    
    Returns:
        tuple: (stdout, stderr, exit_code)
    """
    test_args = ['calctl'] + list(args)
    
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', stdout_capture):
            with patch('sys.stderr', stderr_capture):
                try:
                    main()
                    exit_code = 0
                except SystemExit as e:
                    exit_code = e.code if e.code is not None else 0
    
    return stdout_capture.getvalue(), stderr_capture.getvalue(), exit_code


class TestCLIAddCommand:
    """Test 'add' command integration"""
    
    def test_add_basic_event_success(self, isolated_cli_env):
        """Test adding a basic event via CLI"""
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Team Meeting',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60'
        )
        
        assert code == 0
        assert 'created successfully' in stdout.lower() or 'evt-' in stdout
        
        # Verify event was persisted
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 1
        assert data['events'][0]['title'] == 'Team Meeting'
    
    def test_add_event_with_all_fields(self, isolated_cli_env):
        """Test adding event with all optional fields"""
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Important Meeting',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '90',
            '--description', 'Quarterly review',
            '--location', 'Conference Room A'
        )
        
        assert code == 0
        
        # Verify all fields persisted
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event = data['events'][0]
        assert event['title'] == 'Important Meeting'
        assert event['description'] == 'Quarterly review'
        assert event['location'] == 'Conference Room A'
        assert event['duration_min'] == 90
    
    def test_add_recurring_daily_events(self, isolated_cli_env):
        """Test adding daily recurring events via CLI"""
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Standup',
            '--date', '2026-02-10',
            '--time', '09:00',
            '--duration', '15',
            '--repeat', 'daily',
            '--count', '5'
        )
        
        assert code == 0
        assert '5 occurrences' in stdout or 'Recurring events created' in stdout
        
        # Verify 5 events created
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 5
    
    def test_add_recurring_weekly_events(self, isolated_cli_env):
        """Test adding weekly recurring events via CLI"""
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Team Sync',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60',
            '--repeat', 'weekly',
            '--count', '3'
        )
        
        assert code == 0
        
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 3
        
        # Verify dates are 7 days apart
        dates = [event['date'] for event in data['events']]
        assert dates[0] == '2026-02-10'
        assert dates[1] == '2026-02-17'
        assert dates[2] == '2026-02-24'
    
    def test_add_with_conflict_error(self, isolated_cli_env):
        """Test that conflicting events are rejected"""
        # Add first event
        run_cli_command(
            'add',
            '--title', 'Meeting 1',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60'
        )
        
        # Try to add conflicting event
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Meeting 2',
            '--date', '2026-02-10',
            '--time', '14:30',
            '--duration', '60'
        )
        
        assert code == 4  # ConflictError exit code
        assert 'conflict' in stderr.lower()
    
    def test_add_with_force_bypasses_conflict(self, isolated_cli_env):
        """Test that --force bypasses conflict detection"""
        # Add first event
        run_cli_command(
            'add',
            '--title', 'Meeting 1',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60'
        )
        
        # Add conflicting event with --force
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Meeting 2',
            '--date', '2026-02-10',
            '--time', '14:30',
            '--duration', '60',
            '--force'
        )
        
        assert code == 0
        
        # Both events should exist
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 2
    
    def test_add_invalid_date_format(self, isolated_cli_env):
        """Test error handling for invalid date format"""
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Meeting',
            '--date', '02/10/2026',  # Wrong format
            '--time', '14:00',
            '--duration', '60'
        )
        
        assert code == 2  # InvalidInputError
        assert 'invalid date format' in stderr.lower()
    
    def test_add_invalid_time_format(self, isolated_cli_env):
        """Test error handling for invalid time format"""
        stdout, stderr, code = run_cli_command(
            'add',
            '--title', 'Meeting',
            '--date', '2026-02-10',
            '--time', '2:30pm',  # Wrong format
            '--duration', '60'
        )
        
        assert code == 2
        assert 'invalid time format' in stderr.lower()


class TestCLIListCommand:
    """Test 'list' command integration"""
    
    def test_list_empty_calendar(self, isolated_cli_env):
        """Test listing when no events exist"""
        stdout, stderr, code = run_cli_command('list')
        
        assert code == 0
        assert 'no events' in stdout.lower() or stdout.strip() == ''
    
    def test_list_multiple_events(self, isolated_cli_env):
        """Test listing multiple events"""
        # Add several events
        run_cli_command('add', '--title', 'Event 1', '--date', '2026-02-10', '--time', '09:00', '--duration', '30')
        run_cli_command('add', '--title', 'Event 2', '--date', '2026-02-10', '--time', '14:00', '--duration', '45')
        run_cli_command('add', '--title', 'Event 3', '--date', '2026-02-11', '--time', '10:00', '--duration', '60')
        
        # List all
        stdout, stderr, code = run_cli_command('list')
        
        assert code == 0
        assert 'Event 1' in stdout
        assert 'Event 2' in stdout
        assert 'Event 3' in stdout
    
    def test_list_with_today_filter(self, isolated_cli_env):
        """Test listing today's events only"""
        today = date.today().isoformat()
        tomorrow = (date.today().replace(day=date.today().day + 1)).isoformat()
        
        # Add events for different days
        run_cli_command('add', '--title', 'Today Event', '--date', today, '--time', '10:00', '--duration', '30')
        run_cli_command('add', '--title', 'Tomorrow Event', '--date', tomorrow, '--time', '10:00', '--duration', '30')
        
        # List only today's events
        stdout, stderr, code = run_cli_command('list', '--today')
        
        assert code == 0
        assert 'Today Event' in stdout
        assert 'Tomorrow Event' not in stdout
    
    def test_list_with_date_range(self, isolated_cli_env):
        """Test listing with date range filter"""
        # Add events across different dates
        run_cli_command('add', '--title', 'Event 1', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        run_cli_command('add', '--title', 'Event 2', '--date', '2026-02-15', '--time', '10:00', '--duration', '30')
        run_cli_command('add', '--title', 'Event 3', '--date', '2026-02-20', '--time', '10:00', '--duration', '30')
        
        # List events in range
        stdout, stderr, code = run_cli_command(
            'list',
            '--from', '2026-02-12',
            '--to', '2026-02-18'
        )
        
        assert code == 0
        assert 'Event 2' in stdout
        assert 'Event 1' not in stdout
        assert 'Event 3' not in stdout
    
    def test_list_json_output(self, isolated_cli_env):
        """Test JSON output format"""
        # Add event
        run_cli_command('add', '--title', 'Test Event', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        # List with JSON format
        stdout, stderr, code = run_cli_command('--json', 'list')
        
        assert code == 0
        
        # Parse JSON
        data = json.loads(stdout)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['title'] == 'Test Event'


class TestCLIShowCommand:
    """Test 'show' command integration"""
    
    def test_show_existing_event(self, isolated_cli_env):
        """Test showing an existing event"""
        # Add event
        stdout_add, _, _ = run_cli_command(
            'add',
            '--title', 'Test Event',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '60',
            '--description', 'Test description',
            '--location', 'Test location'
        )
        
        # Extract event ID from output
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Show event
        stdout, stderr, code = run_cli_command('show', event_id)
        
        assert code == 0
        assert 'Test Event' in stdout
        assert 'Test description' in stdout
        assert 'Test location' in stdout
    
    def test_show_nonexistent_event(self, isolated_cli_env):
        """Test showing event that doesn't exist"""
        stdout, stderr, code = run_cli_command('show', 'evt-9999')
        
        assert code == 3  # NotFoundError
        assert 'not found' in stderr.lower()
    
    def test_show_with_conflicts(self, isolated_cli_env):
        """Test showing event with conflicts"""
        # Add overlapping events
        run_cli_command('add', '--title', 'Event 1', '--date', '2026-02-10', '--time', '10:00', '--duration', '60')
        run_cli_command('add', '--title', 'Event 2', '--date', '2026-02-10', '--time', '10:30', '--duration', '60', '--force')
        
        # Get first event ID
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Show should display conflict
        stdout, stderr, code = run_cli_command('show', event_id)
        
        assert code == 0
        assert 'conflict' in stdout.lower() or 'Event 2' in stdout
    
    def test_show_json_output(self, isolated_cli_env):
        """Test show command with JSON output"""
        # Add event
        run_cli_command('add', '--title', 'Test', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Show with JSON
        stdout, stderr, code = run_cli_command('--json', 'show', event_id)
        
        assert code == 0
        data = json.loads(stdout)
        assert 'event' in data
        assert data['event']['title'] == 'Test'


class TestCLIDeleteCommand:
    """Test 'delete' command integration"""
    
    def test_delete_by_id_with_force(self, isolated_cli_env):
        """Test deleting event by ID with --force"""
        # Add event
        run_cli_command('add', '--title', 'To Delete', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Delete with force
        stdout, stderr, code = run_cli_command('delete', event_id, '--force')
        
        assert code == 0
        assert 'deleted' in stdout.lower()
        
        # Verify deleted
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 0
    
    def test_delete_by_id_dry_run(self, isolated_cli_env):
        """Test delete with --dry-run"""
        # Add event
        run_cli_command('add', '--title', 'Test', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Dry run
        stdout, stderr, code = run_cli_command('delete', event_id, '--dry-run')
        
        assert code == 0
        assert 'would delete' in stdout.lower() or 'dry' in stdout.lower()
        
        # Event should still exist
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 1
    
    def test_delete_by_date_with_force(self, isolated_cli_env):
        """Test deleting all events on a date"""
        # Add multiple events on same date
        run_cli_command('add', '--title', 'Event 1', '--date', '2026-02-10', '--time', '09:00', '--duration', '30')
        run_cli_command('add', '--title', 'Event 2', '--date', '2026-02-10', '--time', '14:00', '--duration', '30')
        run_cli_command('add', '--title', 'Event 3', '--date', '2026-02-11', '--time', '10:00', '--duration', '30')
        
        # Delete all on 2026-02-10
        stdout, stderr, code = run_cli_command('delete', '--date', '2026-02-10', '--force')
        
        assert code == 0
        assert '2' in stdout  # Should mention 2 events deleted
        
        # Only Event 3 should remain
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 1
        assert data['events'][0]['title'] == 'Event 3'
    
    def test_delete_nonexistent_event(self, isolated_cli_env):
        """Test deleting event that doesn't exist"""
        stdout, stderr, code = run_cli_command('delete', 'evt-9999', '--force')
        
        assert code == 3  # NotFoundError
        assert 'not found' in stderr.lower()


class TestCLIEditCommand:
    """Test 'edit' command integration"""
    
    def test_edit_event_title(self, isolated_cli_env):
        """Test editing event title"""
        # Add event
        run_cli_command('add', '--title', 'Original', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Edit title
        stdout, stderr, code = run_cli_command('edit', event_id, '--title', 'Updated')
        
        assert code == 0
        assert 'updated' in stdout.lower()
        
        # Verify change
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert data['events'][0]['title'] == 'Updated'
    
    def test_edit_multiple_fields(self, isolated_cli_env):
        """Test editing multiple fields at once"""
        # Add event
        run_cli_command('add', '--title', 'Original', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Edit multiple fields
        stdout, stderr, code = run_cli_command(
            'edit', event_id,
            '--title', 'New Title',
            '--duration', '60',
            '--location', 'New Location'
        )
        
        assert code == 0
        
        # Verify changes
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event = data['events'][0]
        assert event['title'] == 'New Title'
        assert event['duration_min'] == 60
        assert event['location'] == 'New Location'
    
    def test_edit_creates_conflict_error(self, isolated_cli_env):
        """Test that editing to create conflict fails"""
        # Add two events
        run_cli_command('add', '--title', 'Event 1', '--date', '2026-02-10', '--time', '10:00', '--duration', '60')
        run_cli_command('add', '--title', 'Event 2', '--date', '2026-02-10', '--time', '14:00', '--duration', '60')
        
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event2_id = data['events'][1]['id']
        
        # Try to edit event2 to overlap with event1
        stdout, stderr, code = run_cli_command('edit', event2_id, '--time', '10:30')
        
        assert code == 4  # ConflictError
        assert 'conflict' in stderr.lower()


class TestCLISearchCommand:
    """Test 'search' command integration"""
    
    def test_search_finds_events(self, isolated_cli_env):
        """Test searching for events"""
        # Add events
        run_cli_command('add', '--title', 'Team Meeting', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        run_cli_command('add', '--title', 'Lunch Break', '--date', '2026-02-10', '--time', '12:00', '--duration', '60')
        run_cli_command('add', '--title', 'Client Meeting', '--date', '2026-02-11', '--time', '14:00', '--duration', '60')
        
        # Search for "meeting"
        stdout, stderr, code = run_cli_command('search', 'meeting')
        
        assert code == 0
        assert 'Team Meeting' in stdout
        assert 'Client Meeting' in stdout
        assert 'Lunch Break' not in stdout
    
    def test_search_case_insensitive(self, isolated_cli_env):
        """Test that search is case-insensitive"""
        run_cli_command('add', '--title', 'IMPORTANT Event', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        stdout, stderr, code = run_cli_command('search', 'important')
        
        assert code == 0
        assert 'IMPORTANT' in stdout
    
    def test_search_no_results(self, isolated_cli_env):
        """Test search with no matching events"""
        run_cli_command('add', '--title', 'Meeting', '--date', '2026-02-10', '--time', '10:00', '--duration', '30')
        
        stdout, stderr, code = run_cli_command('search', 'nonexistent')
        
        assert code == 0
        assert 'found 0' in stdout.lower() or 'no events' in stdout.lower()


class TestCLIAgendaCommand:
    """Test 'agenda' command integration"""
    
    def test_agenda_default_today(self, isolated_cli_env):
        """Test agenda shows today by default"""
        today = date.today().isoformat()
        
        # Add event for today
        run_cli_command('add', '--title', 'Today Event', '--date', today, '--time', '10:00', '--duration', '30')
        
        # Get agenda (should default to today)
        stdout, stderr, code = run_cli_command('agenda')
        
        assert code == 0
        assert 'Today Event' in stdout or 'Agenda' in stdout
    
    def test_agenda_specific_date(self, isolated_cli_env):
        """Test agenda for specific date"""
        # Add events on different dates
        run_cli_command('add', '--title', 'Event 1', '--date', '2026-02-10', '--time', '09:00', '--duration', '30')
        run_cli_command('add', '--title', 'Event 2', '--date', '2026-02-10', '--time', '14:00', '--duration', '30')
        run_cli_command('add', '--title', 'Event 3', '--date', '2026-02-11', '--time', '10:00', '--duration', '30')
        
        # Get agenda for specific date
        stdout, stderr, code = run_cli_command('agenda', '--date', '2026-02-10')
        
        assert code == 0
        assert 'Event 1' in stdout
        assert 'Event 2' in stdout
        assert 'Event 3' not in stdout
    
    def test_agenda_week(self, isolated_cli_env):
        """Test weekly agenda"""
        # Add events across week
        run_cli_command('add', '--title', 'Monday', '--date', '2026-02-09', '--time', '10:00', '--duration', '30')
        run_cli_command('add', '--title', 'Wednesday', '--date', '2026-02-11', '--time', '10:00', '--duration', '30')
        run_cli_command('add', '--title', 'Friday', '--date', '2026-02-13', '--time', '10:00', '--duration', '30')
        
        # Get week agenda
        stdout, stderr, code = run_cli_command('agenda', '--week')
        
        assert code == 0
        assert 'Week' in stdout or 'Agenda' in stdout


class TestCLIComplexWorkflows:
    """Test complex multi-command workflows"""
    
    def test_add_edit_delete_workflow(self, isolated_cli_env):
        """Test complete lifecycle: add, edit, delete"""
        # Add
        stdout_add, _, code_add = run_cli_command(
            'add',
            '--title', 'Original',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '30'
        )
        assert code_add == 0
        
        # Get ID
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        event_id = data['events'][0]['id']
        
        # Edit
        stdout_edit, _, code_edit = run_cli_command('edit', event_id, '--title', 'Updated')
        assert code_edit == 0
        
        # Delete
        stdout_delete, _, code_delete = run_cli_command('delete', event_id, '--force')
        assert code_delete == 0
        
        # Verify empty
        with open(isolated_cli_env, 'r') as f:
            data = json.load(f)
        assert len(data['events']) == 0
    
    def test_bulk_add_and_search(self, isolated_cli_env):
        """Test adding many events and searching"""
        # Add 10 events
        for i in range(10):
            run_cli_command(
                'add',
                '--title', f'Event {i}',
                '--date', '2026-02-10',
                '--time', f'{9+i}:00',
                '--duration', '30',
                '--force'
            )
        
        # List all
        stdout_list, _, code_list = run_cli_command('list')
        assert code_list == 0
        assert '10' in stdout_list or 'Event 9' in stdout_list
        
        # Search for specific event
        stdout_search, _, code_search = run_cli_command('search', 'Event 5')
        assert code_search == 0
        assert 'Event 5' in stdout_search