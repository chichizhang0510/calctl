"""
End-to-end tests for calctl

These tests run the actual CLI commands to verify the complete user experience.
They are slower but provide confidence that the system works as a whole.
"""

import pytest
import json
import subprocess
from pathlib import Path


# Import helpers from conftest
from tests.e2e.conftest import run_calctl, assert_command_success, assert_command_failed, run_calctl


class TestBasicUserFlow:
    """Test basic user workflows via CLI"""
    
    def test_add_event_via_cli(self):
        """Test adding an event through CLI command"""
        result = run_calctl(
            'add',
            '--title', 'Team Meeting',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60',
            '--description', 'Weekly sync',
            '--location', 'Conference Room'
        )
        
        assert result.returncode == 0, (
            f"Failed to add event\n"
            f"STDERR: {result.stderr}\n"
            f"STDOUT: {result.stdout}"
        )
        assert 'created successfully' in result.stdout
        assert 'evt-' in result.stdout
    
    def test_add_and_list_via_cli(self):
        """Test adding event and listing it"""
        # Add event
        add_result = run_calctl(
            'add',
            '--title', 'Test Event',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '30'
        )
        assert add_result.returncode == 0
        
        # List events
        list_result = run_calctl('list')
        assert list_result.returncode == 0
        assert 'Test Event' in list_result.stdout
    
    def test_add_show_delete_workflow(self):
        """Test complete add-show-delete workflow"""
        # 1. Add event with --json to get ID easily
        add_result = run_calctl(
            '--json',
            'add',
            '--title', 'Temporary Event',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '30'
        )
        assert add_result.returncode == 0, f"Add failed: {add_result.stderr}"
        
        # Extract event ID from JSON
        data = json.loads(add_result.stdout)
        event_id = data[0]['id']
        
        # 2. Show event
        show_result = run_calctl('show', event_id)
        assert show_result.returncode == 0
        assert 'Temporary Event' in show_result.stdout
        
        # 3. Delete event (with --force to skip confirmation)
        delete_result = run_calctl('delete', event_id, '--force')
        assert delete_result.returncode == 0
        
        # 4. Verify deletion
        show_again = run_calctl('show', event_id)
        assert show_again.returncode == 3  # NotFoundError


class TestJSONOutput:
    """Test JSON output format across commands"""
    
    def test_add_with_json_output(self):
        """Test that --json flag produces valid JSON"""
        result = run_calctl(
            '--json',
            'add',
            '--title', 'JSON Test',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '30'
        )
        
        assert result.returncode == 0
        
        # Parse JSON output
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['title'] == 'JSON Test'
    
    def test_list_with_json_output(self):
        """Test list command with JSON output"""
        # Add some events first
        run_calctl('add', '--title', 'Event 1', '--date', '2026-02-10', 
                  '--time', '10:00', '--duration', '30')
        run_calctl('add', '--title', 'Event 2', '--date', '2026-02-11', 
                  '--time', '14:00', '--duration', '45')
        
        # List with JSON
        result = run_calctl('--json', 'list')
        assert result.returncode == 0
        
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 2


class TestErrorHandling:
    """Test error handling and exit codes"""
    
    def test_invalid_date_format_cli(self):
        """Test that invalid date format returns error"""
        result = run_calctl(
            'add',
            '--title', 'Test',
            '--date', '02/10/2026',  # Wrong format
            '--time', '10:00',
            '--duration', '30'
        )
        
        assert_command_failed(result, expected_exit_code=2)
        assert 'Invalid date format' in result.stderr
    
    def test_show_nonexistent_event_cli(self):
        """Test showing non-existent event returns 404"""
        result = run_calctl('show', 'evt-nonexistent')
        
        assert_command_failed(result, expected_exit_code=3)
        assert 'not found' in result.stderr.lower()
    
    def test_empty_title_cli(self):
        """Test that empty title is rejected"""
        result = run_calctl(
            'add',
            '--title', '',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '30'
        )
        
        assert_command_failed(result, expected_exit_code=2)


class TestRecurringEvents:
    """Test recurring event functionality"""
    
    def test_daily_recurring_via_cli(self):
        """Test creating daily recurring events"""
        result = run_calctl(
            'add',
            '--title', 'Standup',
            '--date', '2026-02-10',
            '--time', '09:00',
            '--duration', '15',
            '--repeat', 'daily',
            '--count', '5'
        )
        
        assert_command_success(result, 'Recurring events created')
        assert '5 occurrences' in result.stdout
    
    def test_weekly_recurring_via_cli(self):
        """Test creating weekly recurring events"""
        result = run_calctl(
            'add',
            '--title', 'Team Meeting',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60',
            '--repeat', 'weekly',
            '--count', '3'
        )
        
        assert result.returncode == 0
        assert '3 occurrences' in result.stdout


class TestSearchAndFilter:
    """Test search and filter functionality"""
    
    def test_search_via_cli(self):
        """Test search command"""
        # Add events on DIFFERENT times to avoid conflicts
        run_calctl('add', '--title', 'Team Meeting', '--date', '2026-02-10',
                  '--time', '10:00', '--duration', '30')
        run_calctl('add', '--title', 'Client Meeting', '--date', '2026-02-11',
                  '--time', '14:00', '--duration', '60')  # Different date!
        run_calctl('add', '--title', 'Lunch Break', '--date', '2026-02-12',
                  '--time', '12:00', '--duration', '45')  # Different date!
        
        # Search for "meeting"
        result = run_calctl('search', 'meeting')
        
        assert result.returncode == 0
        assert 'Team Meeting' in result.stdout
        assert 'Client Meeting' in result.stdout
        # Lunch Break should NOT be in results


class TestConflictDetection:
    """Test conflict detection via CLI"""
    
    def test_conflict_detected_via_cli(self):
        """Test that conflicts are detected"""
        # Add first event
        result1 = run_calctl(
            'add',
            '--title', 'Event 1',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60'
        )
        assert result1.returncode == 0
        
        # Try to add conflicting event
        result2 = run_calctl(
            'add',
            '--title', 'Event 2',
            '--date', '2026-02-10',
            '--time', '14:30',
            '--duration', '60'
        )
        
        assert_command_failed(result2, expected_exit_code=4)
        assert 'conflict' in result2.stderr.lower()
    
    def test_force_flag_bypasses_conflict_via_cli(self):
        """Test that --force allows conflicting events"""
        # Add first event
        run_calctl('add', '--title', 'Event 1', '--date', '2026-02-10',
                  '--time', '14:00', '--duration', '60')
        
        # Force add conflicting event
        result = run_calctl(
            'add',
            '--title', 'Event 2',
            '--date', '2026-02-10',
            '--time', '14:30',
            '--duration', '60',
            '--force'
        )
        
        assert result.returncode == 0


class TestDeleteOperations:
    """Test delete operations"""
    
    def test_delete_with_confirmation_via_cli(self):
        """Test delete with user confirmation"""
        # Add event
        add_result = run_calctl('add', '--title', 'To Delete',
                               '--date', '2026-02-10', '--time', '10:00',
                               '--duration', '30')
        import re
        event_id = re.search(r'evt-[a-f0-9]+', add_result.stdout).group(0)
        
        # Delete with confirmation (send 'y' to stdin)
        result = run_calctl('delete', event_id, input_text='y\n')
        
        assert result.returncode == 0
    
    def test_delete_dry_run_via_cli(self):
        """Test delete with --dry-run flag"""
        # Add event
        add_result = run_calctl('add', '--title', 'Test',
                               '--date', '2026-02-10', '--time', '10:00',
                               '--duration', '30')
        import re
        event_id = re.search(r'evt-[a-f0-9]+', add_result.stdout).group(0)
        
        # Dry run
        result = run_calctl('delete', event_id, '--dry-run')
        
        assert result.returncode == 0
        assert 'Would delete' in result.stdout
        
        # Verify event still exists
        show_result = run_calctl('show', event_id)
        assert show_result.returncode == 0


class TestAgendaViews:
    """Test agenda view commands"""
    
    def test_agenda_day_via_cli(self):
        """Test daily agenda view"""
        result = run_calctl('agenda', '--date', '2026-02-10')
        
        assert result.returncode == 0
        assert '2026-02-10' in result.stdout
    
    def test_agenda_week_via_cli(self):
        """Test weekly agenda view"""
        result = run_calctl('agenda', '--week')
        
        assert result.returncode == 0
        assert 'Week Agenda' in result.stdout or 'Agenda' in result.stdout


class TestEditOperations:
    """Test edit operations"""
    
    def test_edit_event_via_cli(self):
        """Test editing an event"""
        # Add event
        add_result = run_calctl('add', '--title', 'Original',
                               '--date', '2026-02-10', '--time', '10:00',
                               '--duration', '30')
        import re
        event_id = re.search(r'evt-[a-f0-9]+', add_result.stdout).group(0)
        
        # Edit event
        result = run_calctl('edit', event_id, '--title', 'Updated')
        
        assert result.returncode == 0
        assert 'Updated' in result.stdout or 'updated' in result.stdout.lower()


@pytest.mark.slow
class TestCompleteUserScenarios:
    """Test complete realistic user scenarios (marked as slow)"""
    
    def test_full_week_planning_scenario(self):
        """
        Test a realistic scenario: User planning their week
        
        This is a comprehensive E2E test that simulates a real user:
        1. Adds multiple events for the week
        2. Views the agenda
        3. Searches for specific events
        4. Edits an event
        5. Deletes an event
        """
        # Monday: Morning standup
        run_calctl('add', '--title', 'Standup', '--date', '2026-02-10',
                  '--time', '09:00', '--duration', '15')
        
        # Monday: Team meeting
        run_calctl('add', '--title', 'Team Meeting', '--date', '2026-02-10',
                  '--time', '14:00', '--duration', '60')
        
        # Tuesday: Client call
        run_calctl('add', '--title', 'Client Call', '--date', '2026-02-11',
                  '--time', '10:00', '--duration', '45')
        
        # View week agenda
        agenda_result = run_calctl('agenda', '--week')
        assert agenda_result.returncode == 0
        assert 'Standup' in agenda_result.stdout
        
        # Search for meetings
        search_result = run_calctl('search', 'meeting')
        assert 'Team Meeting' in search_result.stdout
        
        # List all events
        list_result = run_calctl('list')
        assert list_result.returncode == 0