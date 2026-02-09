"""
End-to-end tests for calctl

E2E tests verify the entire system working together, including:
- CLI command parsing
- Service layer logic
- Data persistence
- User output

These tests are slower but provide confidence that the system works as a whole.

Guidelines:
- Test complete user workflows
- Use subprocess to run CLI commands
- Verify actual command output
- Tests may take > 0.1s
"""

import pytest
import subprocess
import tempfile
from pathlib import Path


# ============================================================================
# Shared Fixtures for E2E Tests
# ============================================================================

@pytest.fixture
def isolated_env(monkeypatch):
    """
    Create an isolated environment for E2E testing
    
    Sets up:
    - Temporary data directory
    - Environment variables
    
    Yields:
        Path: Path to temporary data file
    """
    temp_dir = tempfile.mkdtemp()
    data_path = Path(temp_dir) / "events.json"
    
    # Set environment variable (if your app supports it)
    # monkeypatch.setenv("CALCTL_DATA_PATH", str(data_path))
    
    yield data_path
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Helper Functions
# ============================================================================

def run_calctl(*args, **kwargs):
    """
    Run calctl command and return result
    
    Args:
        *args: Command arguments
        **kwargs: Additional subprocess.run kwargs
    
    Returns:
        subprocess.CompletedProcess: Command result
    
    Example:
        result = run_calctl('add', '--title', 'Test', '--date', '2026-02-10')
    """
    cmd = ['calctl'] + list(args)
    
    defaults = {
        'capture_output': True,
        'text': True,
    }
    defaults.update(kwargs)
    
    return subprocess.run(cmd, **defaults)


def assert_command_success(result, expected_in_output=None):
    """
    Assert that a command succeeded
    
    Args:
        result: subprocess.CompletedProcess result
        expected_in_output: Optional string to check in output
    """
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    if expected_in_output:
        assert expected_in_output in result.stdout, \
            f"Expected '{expected_in_output}' in output, got: {result.stdout}"


def assert_command_failed(result, expected_exit_code=None):
    """
    Assert that a command failed with expected exit code
    
    Args:
        result: subprocess.CompletedProcess result
        expected_exit_code: Expected exit code (if None, any non-zero is OK)
    """
    assert result.returncode != 0, "Command should have failed but succeeded"
    
    if expected_exit_code:
        assert result.returncode == expected_exit_code, \
            f"Expected exit code {expected_exit_code}, got {result.returncode}"


# ============================================================================
# Test Markers
# ============================================================================

pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow