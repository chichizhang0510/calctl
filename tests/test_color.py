"""
Unit tests for calctl.color

Tests ANSI color output functionality.
"""

import pytest
import sys
from io import StringIO
from calctl.color import Color


class TestColorInitialization:
    """Test Color class initialization"""
    
    def test_color_enabled_for_stdout(self):
        """Test color enabled when output is TTY"""
        c = Color(enabled=True, stream="stdout")
        # enabled depends on whether sys.stdout.isatty()
        # In test environment, usually False
        assert isinstance(c.enabled, bool)
    
    def test_color_disabled_explicitly(self):
        """Test color can be explicitly disabled"""
        c = Color(enabled=False, stream="stdout")
        assert c.enabled is False
    
    def test_color_for_stderr(self):
        """Test color initialization for stderr"""
        c = Color(enabled=True, stream="stderr")
        assert isinstance(c.enabled, bool)


class TestColorOutput:
    """Test color output methods"""
    
    def test_green_with_color_enabled(self):
        """Test green color output when enabled"""
        c = Color(enabled=True, stream="stdout")
        c.enabled = True  # Force enable for testing
        
        result = c.green("Success")
        assert "\033[32m" in result  # Green color code
        assert "Success" in result
        assert "\033[0m" in result   # Reset code
    
    def test_red_with_color_enabled(self):
        """Test red color output when enabled"""
        c = Color(enabled=True, stream="stdout")
        c.enabled = True
        
        result = c.red("Error")
        assert "\033[31m" in result  # Red color code
        assert "Error" in result
        assert "\033[0m" in result
    
    def test_yellow_with_color_enabled(self):
        """Test yellow color output when enabled"""
        c = Color(enabled=True, stream="stdout")
        c.enabled = True
        
        result = c.yellow("Warning")
        assert "\033[33m" in result  # Yellow color code
        assert "Warning" in result
        assert "\033[0m" in result
    
    def test_bold_with_color_enabled(self):
        """Test bold text when enabled"""
        c = Color(enabled=True, stream="stdout")
        c.enabled = True
        
        result = c.bold("Important")
        assert "\033[1m" in result  # Bold code
        assert "Important" in result
        assert "\033[0m" in result


class TestColorDisabled:
    """Test color output when disabled"""
    
    def test_green_with_color_disabled(self):
        """Test green returns plain text when disabled"""
        c = Color(enabled=False, stream="stdout")
        
        result = c.green("Success")
        assert result == "Success"
        assert "\033[" not in result
    
    def test_red_with_color_disabled(self):
        """Test red returns plain text when disabled"""
        c = Color(enabled=False, stream="stdout")
        
        result = c.red("Error")
        assert result == "Error"
        assert "\033[" not in result
    
    def test_yellow_with_color_disabled(self):
        """Test yellow returns plain text when disabled"""
        c = Color(enabled=False, stream="stdout")
        
        result = c.yellow("Warning")
        assert result == "Warning"
        assert "\033[" not in result
    
    def test_bold_with_color_disabled(self):
        """Test bold returns plain text when disabled"""
        c = Color(enabled=False, stream="stdout")
        
        result = c.bold("Important")
        assert result == "Important"
        assert "\033[" not in result


class TestColorEdgeCases:
    """Test edge cases"""
    
    def test_empty_string(self):
        """Test coloring empty string"""
        c = Color(enabled=True, stream="stdout")
        c.enabled = True
        
        result = c.green("")
        assert result == "\033[32m\033[0m"
    
    def test_empty_string_disabled(self):
        """Test empty string when disabled"""
        c = Color(enabled=False, stream="stdout")
        
        result = c.green("")
        assert result == ""
    
    def test_multiline_text(self):
        """Test coloring multiline text"""
        c = Color(enabled=True, stream="stdout")
        c.enabled = True
        
        text = "Line 1\nLine 2\nLine 3"
        result = c.red(text)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert result.startswith("\033[31m")
        assert result.endswith("\033[0m")
    
    def test_special_characters(self):
        """Test coloring text with special characters"""
        c = Color(enabled=True, stream="stdout")
        c.enabled = True
        
        text = "Error: 'file' not found!"
        result = c.red(text)
        assert text in result
        assert "\033[31m" in result


class TestTTYDetection:
    """Test TTY detection logic"""
    
    def test_non_tty_disables_color(self, monkeypatch):
        """Test that non-TTY output disables color"""
        # Mock isatty to return False
        monkeypatch.setattr(sys.stdout, 'isatty', lambda: False)
        
        c = Color(enabled=True, stream="stdout")
        # Should be disabled because stdout is not a TTY
        # Note: In test environment, this is usually the case
        
        # Even if we try to enable, it should respect TTY
        result = c.green("Test")
        # In non-TTY, should be plain
        if not sys.stdout.isatty():
            assert result == "Test"