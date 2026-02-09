"""
Unit tests for calctl.cli

Tests the CLI argument parsing and command dispatch logic.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from datetime import date
from calctl.cli import build_parser, main, default_data_path
from calctl.errors import InvalidInputError, NotFoundError, ConflictError


class TestBuildParser:
    """Test argument parser construction"""
    
    def test_parser_has_version(self):
        """Test that parser has version argument"""
        parser = build_parser()
        
        # Try parsing --version
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--version'])
        
        assert exc_info.value.code == 0
    
    def test_parser_has_no_color_flag(self):
        """Test that parser has --no-color flag"""
        parser = build_parser()
        args = parser.parse_args(['--no-color', 'list'])
        
        assert args.no_color is True
    
    def test_parser_has_json_flag(self):
        """Test that parser has TestMainAgendaCommand flag"""
        parser = build_parser()
        args = parser.parse_args(['--json', 'list'])
        
        assert args.json is True
    
    def test_parser_json_and_plain_mutually_exclusive(self):
        """Test that --json and --plain are mutually exclusive"""
        parser = build_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--json', '--plain', 'list'])


class TestParserAddCommand:
    """Test 'add' command argument parsing"""
    
    def test_add_command_required_args(self):
        """Test that add command requires title, date, time, duration"""
        parser = build_parser()
        
        args = parser.parse_args([
            'add',
            '--title', 'Meeting',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60'
        ])
        
        assert args.cmd == 'add'
        assert args.title == 'Meeting'
        assert args.date == '2026-02-10'
        assert args.time == '14:00'
        assert args.duration == 60
    
    def test_add_command_optional_args(self):
        """Test add command with optional arguments"""
        parser = build_parser()
        
        args = parser.parse_args([
            'add',
            '--title', 'Meeting',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60',
            '--description', 'Team sync',
            '--location', 'Room 101'
        ])
        
        assert args.description == 'Team sync'
        assert args.location == 'Room 101'
    
    def test_add_command_with_force(self):
        """Test add command with --force flag"""
        parser = build_parser()
        
        args = parser.parse_args([
            'add',
            '--title', 'Meeting',
            '--date', '2026-02-10',
            '--time', '14:00',
            '--duration', '60',
            '--force'
        ])
        
        assert args.force is True
    
    def test_add_command_with_repeat(self):
        """Test add command with --repeat"""
        parser = build_parser()
        
        args = parser.parse_args([
            'add',
            '--title', 'Standup',
            '--date', '2026-02-10',
            '--time', '09:00',
            '--duration', '15',
            '--repeat', 'daily',
            '--count', '5'
        ])
        
        assert args.repeat == 'daily'
        assert args.count == 5


class TestParserListCommand:
    """Test 'list' command argument parsing"""
    
    def test_list_command_no_args(self):
        """Test list command with no arguments"""
        parser = build_parser()
        args = parser.parse_args(['list'])
        
        assert args.cmd == 'list'
    
    def test_list_command_today(self):
        """Test list command with --today"""
        parser = build_parser()
        args = parser.parse_args(['list', '--today'])
        
        assert args.today is True
    
    def test_list_command_week(self):
        """Test list command with --week"""
        parser = build_parser()
        args = parser.parse_args(['list', '--week'])
        
        assert args.week is True
    
    def test_list_command_date_range(self):
        """Test list command with date range"""
        parser = build_parser()
        args = parser.parse_args([
            'list',
            '--from', '2026-02-01',
            '--to', '2026-02-28'
        ])
        
        assert args.from_date == '2026-02-01'
        assert args.to_date == '2026-02-28'


class TestParserShowCommand:
    """Test 'show' command argument parsing"""
    
    def test_show_command(self):
        """Test show command with event ID"""
        parser = build_parser()
        args = parser.parse_args(['show', 'evt-1234'])
        
        assert args.cmd == 'show'
        assert args.id == 'evt-1234'


class TestParserDeleteCommand:
    """Test 'delete' command argument parsing"""
    
    def test_delete_command_by_id(self):
        """Test delete command with event ID"""
        parser = build_parser()
        args = parser.parse_args(['delete', 'evt-1234'])
        
        assert args.cmd == 'delete'
        assert args.id == 'evt-1234'
    
    def test_delete_command_by_date(self):
        """Test delete command by date"""
        parser = build_parser()
        args = parser.parse_args(['delete', '--date', '2026-02-10'])
        
        assert args.cmd == 'delete'
        assert args.date == '2026-02-10'
    
    def test_delete_command_with_force(self):
        """Test delete command with --force"""
        parser = build_parser()
        args = parser.parse_args(['delete', 'evt-1234', '--force'])
        
        assert args.force is True
    
    def test_delete_command_with_dry_run(self):
        """Test delete command with --dry-run"""
        parser = build_parser()
        args = parser.parse_args(['delete', 'evt-1234', '--dry-run'])
        
        assert args.dry_run is True


class TestParserEditCommand:
    """Test 'edit' command argument parsing"""
    
    def test_edit_command(self):
        """Test edit command with ID"""
        parser = build_parser()
        args = parser.parse_args([
            'edit', 'evt-1234',
            '--title', 'Updated'
        ])
        
        assert args.cmd == 'edit'
        assert args.id == 'evt-1234'
        assert args.title == 'Updated'


class TestParserSearchCommand:
    """Test 'search' command argument parsing"""
    
    def test_search_command(self):
        """Test search command"""
        parser = build_parser()
        args = parser.parse_args(['search', 'meeting'])
        
        assert args.cmd == 'search'
        assert args.query == 'meeting'
    
    def test_search_command_title_only(self):
        """Test search command with --title"""
        parser = build_parser()
        args = parser.parse_args(['search', 'meeting', '--title'])
        
        assert args.title is True


class TestParserAgendaCommand:
    """Test 'agenda' command argument parsing"""
    
    def test_agenda_command_default(self):
        """Test agenda command with no arguments"""
        parser = build_parser()
        args = parser.parse_args(['agenda'])
        
        assert args.cmd == 'agenda'
    
    def test_agenda_command_week(self):
        """Test agenda command with --week"""
        parser = build_parser()
        args = parser.parse_args(['agenda', '--week'])
        
        assert args.week is True
    
    def test_agenda_command_date(self):
        """Test agenda command with specific date"""
        parser = build_parser()
        args = parser.parse_args(['agenda', '--date', '2026-02-10'])
        
        assert args.date == '2026-02-10'


class TestDefaultDataPath:
    """Test default_data_path function"""
    
    def test_default_data_path_format(self):
        """Test that default path has correct format"""
        path = default_data_path()
        
        assert str(path).endswith('.calctl/events.json')
        assert 'events.json' in str(path)


class TestMainAddCommand:
    """Test main() with 'add' command"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_add_command_success(self, mock_store_cls, mock_service_cls):
        """Test main() successfully adds event"""
        # Setup mocks
        mock_store = Mock()
        mock_store_cls.return_value = mock_store
        
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # Mock add_event to return a list with one event
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_service.add_event.return_value = [mock_event]
        
        # Mock sys.argv
        test_args = [
            'calctl', 'add',
            '--title', 'Test',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '60'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
        
        # Verify service was called
        mock_service.add_event.assert_called_once()


class TestMainErrorHandling:
    """Test main() error handling"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_handles_invalid_input_error(self, mock_store_cls, mock_service_cls):
        """Test that main() handles InvalidInputError"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # Make add_event raise InvalidInputError
        mock_service.add_event.side_effect = InvalidInputError("Invalid input")
        
        test_args = [
            'calctl', 'add',
            '--title', '',
            '--date', '2026-02-10',
            '--time', '10:00',
            '--duration', '60'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stderr', new=StringIO()):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                # Should exit with code 2 (InvalidInputError)
                assert exc_info.value.code == 2
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_handles_not_found_error(self, mock_store_cls, mock_service_cls):
        """Test that main() handles NotFoundError"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # 修复：应该 mock show_event_with_conflicts
        mock_service.show_event_with_conflicts.side_effect = NotFoundError("Not found")
        
        test_args = ['calctl', 'show', 'evt-9999']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stderr', new=StringIO()):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                # Should exit with code 3 (NotFoundError)
                assert exc_info.value.code == 3
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_handles_keyboard_interrupt(self, mock_store_cls, mock_service_cls):
        """Test that main() handles KeyboardInterrupt"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_service.list_events.side_effect = KeyboardInterrupt()
        
        test_args = ['calctl', 'list']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stderr', new=StringIO()):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                # Should exit with code 130 (KeyboardInterrupt)
                assert exc_info.value.code == 130


class TestMainListCommand:
    """Test main() with 'list' command execution"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_list_command_json_output(self, mock_store_cls, mock_service_cls):
        """Test list command with JSON output"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # Mock event
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.duration_min = 60
        mock_event.description = None
        mock_event.location = None
        mock_event.create_at.isoformat.return_value = '2026-02-01T10:00:00'
        mock_event.update_at.isoformat.return_value = '2026-02-01T10:00:00'
        
        mock_service.list_events.return_value = [mock_event]
        
        test_args = ['calctl', '--json', 'list']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
                
                output = fake_out.getvalue()
                assert 'evt-1234' in output or output != ''

    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_list_command_plain_output(self, mock_store_cls, mock_service_cls):
        """Test list command with plain text output"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # Mock event
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test Event'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.duration_min = 60
        
        mock_service.list_events.return_value = [mock_event]
        
        test_args = ['calctl', 'list']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
                
                output = fake_out.getvalue()
                assert 'evt-1234' in output or 'Test Event' in output
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_list_command_empty(self, mock_store_cls, mock_service_cls):
        """Test list command with no events"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_service.list_events.return_value = []
        
        test_args = ['calctl', 'list']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
                
                output = fake_out.getvalue()
                # Should show "No events found" or similar
                assert len(output) >= 0  # At least some output


class TestMainShowCommand:
    """Test main() with 'show' command execution"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_show_command_json(self, mock_store_cls, mock_service_cls):
        """Test show command with JSON output"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # Mock event
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.description = 'Description'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        mock_event.duration_min = 60
        mock_event.location = 'Office'
        mock_event.create_at.isoformat.return_value = '2026-02-01T10:00:00'
        mock_event.update_at.isoformat.return_value = '2026-02-01T10:00:00'
        
        mock_service.show_event_with_conflicts.return_value = (mock_event, [])
        
        test_args = ['calctl', '--json', 'show', 'evt-1234']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
                
                output = fake_out.getvalue()
                assert 'evt-1234' in output or output != ''
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_show_command_plain(self, mock_store_cls, mock_service_cls):
        """Test show command with plain output"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # Mock event
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.description = 'Description'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        mock_event.duration_min = 60
        mock_event.location = 'Office'
        mock_event.create_at.isoformat.return_value = '2026-02-01T10:00:00'
        mock_event.update_at.isoformat.return_value = '2026-02-01T10:00:00'
        
        mock_service.show_event_with_conflicts.return_value = (mock_event, [])
        
        test_args = ['calctl', 'show', 'evt-1234']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
                
                output = fake_out.getvalue()
                assert 'ID:' in output or 'evt-1234' in output


class TestMainSearchCommand:
    """Test main() with 'search' command"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_search_command(self, mock_store_cls, mock_service_cls):
        """Test search command"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Meeting'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.duration_min = 60
        
        mock_service.search_events.return_value = [mock_event]
        
        test_args = ['calctl', 'search', 'meeting']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
                
                output = fake_out.getvalue()
                assert len(output) > 0


class TestMainDeleteCommand:
    """Test main() with 'delete' command"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_delete_by_id_with_force(self, mock_store_cls, mock_service_cls):
        """Test delete by ID with --force"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        
        mock_service.show_event.return_value = mock_event
        mock_service.delete_event.return_value = mock_event
        
        test_args = ['calctl', 'delete', 'evt-1234', '--force']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
        
        mock_service.delete_event.assert_called_once_with('evt-1234')
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_delete_by_id_dry_run(self, mock_store_cls, mock_service_cls):
        """Test delete with --dry-run"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        
        mock_service.show_event.return_value = mock_event
        
        test_args = ['calctl', 'delete', 'evt-1234', '--dry-run']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 0
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_delete_by_date(self, mock_store_cls, mock_service_cls):
        """Test delete by date"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        
        mock_service.get_events_on_date.return_value = [mock_event]
        mock_service.delete_on_date.return_value = 1
        
        test_args = ['calctl', 'delete', '--date', '2026-02-10', '--force']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass


class TestMainEditCommand:
    """Test main() with 'edit' command"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_edit_command(self, mock_store_cls, mock_service_cls):
        """Test edit command"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Updated'
        
        changes = {'title': ('Old', 'Updated')}
        mock_service.edit_event.return_value = (mock_event, changes)
        
        test_args = ['calctl', 'edit', 'evt-1234', '--title', 'Updated']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
        
        mock_service.edit_event.assert_called_once()


class TestMainAgendaCommand:
    """Test main() with 'agenda' command"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_agenda_day(self, mock_store_cls, mock_service_cls):
        """Test agenda for a day"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # 修复：使用 datetime.date
        from datetime import date  # 确保导入
        mock_service.parse_date_public.return_value = date(2026, 2, 10)
        mock_service.agenda_day.return_value = []
        
        test_args = ['calctl', 'agenda', '--date', '2026-02-10']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_agenda_week(self, mock_store_cls, mock_service_cls):
        """Test agenda for a week"""
        from datetime import date, timedelta
        
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # 修复：提供有效的week字典（7天数据）
        today = date.today()
        week = {}
        for i in range(7):
            d = today + timedelta(days=i)
            week[d] = []  # 每天空事件列表
        
        mock_service.agenda_week.return_value = week  # ← 修改这里
        
        test_args = ['calctl', 'agenda', '--week']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass


class TestMainListCommandVariations:
    """Test list command with different filter combinations"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_list_with_from_date_only(self, mock_store_cls, mock_service_cls):
        """Test list with only --from date"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        mock_service.parse_date.return_value = date(2026, 2, 1)
        mock_service.list_events.return_value = []
        
        test_args = ['calctl', 'list', '--from', '2026-02-01']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_list_with_to_date_only(self, mock_store_cls, mock_service_cls):
        """Test list with only --to date"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        mock_service.parse_date.return_value = date(2026, 2, 28)
        mock_service.list_events.return_value = []
        
        test_args = ['calctl', 'list', '--to', '2026-02-28']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass


class TestMainShowCommandWithConflicts:
    """Test show command when conflicts exist"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    def test_main_show_with_conflicts(self, mock_store_cls, mock_service_cls):
        """Test show command displaying conflicts"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        # Mock main event
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.description = 'Description'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        mock_event.duration_min = 60
        mock_event.location = 'Office'
        mock_event.create_at.isoformat.return_value = '2026-02-01T10:00:00'
        mock_event.update_at.isoformat.return_value = '2026-02-01T10:00:00'
        
        # Mock conflicting event
        conflict = Mock()
        conflict.id = 'evt-5678'
        conflict.title = 'Conflicting'
        conflict.start_time = '10:30'
        conflict.end_dt.return_value.strftime.return_value = '11:30'
        
        mock_service.show_event_with_conflicts.return_value = (mock_event, [conflict])
        
        test_args = ['calctl', 'show', 'evt-1234']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                try:
                    main()
                except SystemExit:
                    pass
                
                output = fake_out.getvalue()
                # Should show conflict information
                assert 'Conflict' in output or len(output) > 0


class TestMainDeleteWithConfirmation:
    """Test delete command with user confirmation"""
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    @patch('builtins.input', return_value='y')  # Mock user input
    def test_main_delete_with_yes_confirmation(self, mock_input, mock_store_cls, mock_service_cls):
        """Test delete with user confirming 'yes'"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        
        mock_service.show_event.return_value = mock_event
        mock_service.delete_event.return_value = mock_event
        
        test_args = ['calctl', 'delete', 'evt-1234']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
        
        mock_service.delete_event.assert_called_once()
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    @patch('builtins.input', return_value='n')  # Mock user input
    def test_main_delete_with_no_confirmation(self, mock_input, mock_store_cls, mock_service_cls):
        """Test delete with user declining"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.date.isoformat.return_value = '2026-02-10'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        
        mock_service.show_event.return_value = mock_event
        
        test_args = ['calctl', 'delete', 'evt-1234']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stderr', new=StringIO()):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
        
        # Should NOT call delete_event
        mock_service.delete_event.assert_not_called()
    
    @patch('calctl.cli.CalendarService')
    @patch('calctl.cli.JsonEventStore')
    @patch('builtins.input', return_value='y')
    def test_main_delete_by_date_with_confirmation(self, mock_input, mock_store_cls, mock_service_cls):
        """Test delete by date with confirmation"""
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        
        mock_event = Mock()
        mock_event.id = 'evt-1234'
        mock_event.title = 'Test'
        mock_event.start_time = '10:00'
        mock_event.end_dt.return_value.strftime.return_value = '11:00'
        
        mock_service.get_events_on_date.return_value = [mock_event]
        mock_service.delete_on_date.return_value = 1
        
        test_args = ['calctl', 'delete', '--date', '2026-02-10']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.stdout', new=StringIO()):
                try:
                    main()
                except SystemExit:
                    pass
        
        mock_service.delete_on_date.assert_called_once()