"""
Unit tests for calctl.errors

Tests the custom exception hierarchy.
"""

import pytest
from calctl.errors import (
    CalctlError,
    InvalidInputError,
    NotFoundError,
    StorageError,
    ConflictError
)


class TestErrorHierarchy:
    """Test exception inheritance"""
    
    def test_all_errors_inherit_from_calctl_error(self):
        """Test that all custom errors inherit from CalctlError"""
        assert issubclass(InvalidInputError, CalctlError)
        assert issubclass(NotFoundError, CalctlError)
        assert issubclass(StorageError, CalctlError)
        assert issubclass(ConflictError, CalctlError)
    
    def test_all_errors_inherit_from_exception(self):
        """Test that CalctlError inherits from Exception"""
        assert issubclass(CalctlError, Exception)
        assert issubclass(InvalidInputError, Exception)


class TestErrorExitCodes:
    """Test exit codes for each error type"""
    
    def test_calctl_error_exit_code(self):
        """Test CalctlError has exit code 1"""
        assert CalctlError.exit_code == 1
    
    def test_invalid_input_error_exit_code(self):
        """Test InvalidInputError has exit code 2"""
        assert InvalidInputError.exit_code == 2
    
    def test_not_found_error_exit_code(self):
        """Test NotFoundError has exit code 3"""
        assert NotFoundError.exit_code == 3
    
    def test_storage_error_exit_code(self):
        """Test StorageError has exit code 1"""
        assert StorageError.exit_code == 1
    
    def test_conflict_error_exit_code(self):
        """Test ConflictError has exit code 4"""
        assert ConflictError.exit_code == 4
    
    def test_exit_codes_are_distinct(self):
        """Test that different error types have distinct exit codes (where appropriate)"""
        codes = {
            InvalidInputError.exit_code,
            NotFoundError.exit_code,
            ConflictError.exit_code
        }
        # These should all be different
        assert len(codes) == 3


class TestErrorRaising:
    """Test that errors can be raised and caught"""
    
    def test_raise_invalid_input_error(self):
        """Test raising InvalidInputError"""
        with pytest.raises(InvalidInputError) as exc_info:
            raise InvalidInputError("Invalid input")
        
        assert str(exc_info.value) == "Invalid input"
        assert exc_info.value.exit_code == 2
    
    def test_raise_not_found_error(self):
        """Test raising NotFoundError"""
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError("Event not found")
        
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.exit_code == 3
    
    def test_raise_storage_error(self):
        """Test raising StorageError"""
        with pytest.raises(StorageError) as exc_info:
            raise StorageError("Failed to read file")
        
        assert "failed" in str(exc_info.value).lower()
        assert exc_info.value.exit_code == 1
    
    def test_raise_conflict_error(self):
        """Test raising ConflictError"""
        with pytest.raises(ConflictError) as exc_info:
            raise ConflictError("Event conflicts")
        
        assert "conflict" in str(exc_info.value).lower()
        assert exc_info.value.exit_code == 4
    
    def test_catch_as_calctl_error(self):
        """Test that specific errors can be caught as CalctlError"""
        with pytest.raises(CalctlError):
            raise InvalidInputError("Test")
        
        with pytest.raises(CalctlError):
            raise NotFoundError("Test")
    
    def test_error_with_formatted_message(self):
        """Test errors with formatted messages"""
        event_id = "evt-1234"
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError(f"Event {event_id} not found")
        
        assert "evt-1234" in str(exc_info.value)


class TestErrorMessages:
    """Test error message handling"""
    
    def test_error_preserves_message(self):
        """Test that error message is preserved"""
        msg = "This is a custom error message"
        err = InvalidInputError(msg)
        assert str(err) == msg
    
    def test_error_with_multiline_message(self):
        """Test error with multiline message"""
        msg = "Line 1\nLine 2\nLine 3"
        err = ConflictError(msg)
        assert str(err) == msg
    
    def test_error_with_special_characters(self):
        """Test error message with special characters"""
        msg = "Error: 'title' field is required (got: \"\")"
        err = InvalidInputError(msg)
        assert str(err) == msg