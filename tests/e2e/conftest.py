"""
Fixtures for E2E tests

E2E tests run the actual CLI commands via subprocess.
"""

import pytest
import subprocess
import tempfile
import json
from pathlib import Path
import os
import shutil

@pytest.fixture(autouse=True)
def clean_calctl_data():
    """
    Automatically clean calctl data before and after each E2E test
    
    This fixture runs automatically (autouse=True) for all E2E tests
    to ensure test isolation.
    """
    data_dir = Path.home() / ".calctl"
    
    # Cleanup before test
    if data_dir.exists():
        shutil.rmtree(data_dir)
    
    yield  # Run the test
    
    # Cleanup after test (optional, 可以注释掉保留最后一个测试的数据用于调试)
    # if data_dir.exists():
    #     shutil.rmtree(data_dir)

@pytest.fixture
def isolated_calctl_env(monkeypatch):
    """
    Create an isolated environment for E2E testing
    
    This fixture:
    - Creates a temporary data directory
    - Sets CALCTL_DATA_PATH environment variable (if supported)
    - Cleans up after the test
    
    Yields:
        Path: Path to the temporary data file
    """
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    data_file = Path(temp_dir) / "events.json"
    
    # Option 1: Use environment variable (需要你的代码支持)
    # monkeypatch.setenv("CALCTL_DATA_PATH", str(data_file))
    
    # Option 2: Use --data-file flag (需要你的CLI支持)
    # 或者使用默认路径，在每个测试前清空
    
    yield data_file
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def run_calctl(*args, input_text=None, check=False):
    """
    Run calctl command via subprocess
    
    Args:
        *args: Command arguments (e.g., 'add', '--title', 'Test')
        input_text: Text to send to stdin (for interactive prompts)
        check: Whether to raise exception on non-zero exit
    
    Returns:
        subprocess.CompletedProcess: Result with stdout, stderr, returncode
    
    Example:
        result = run_calctl('add', '--title', 'Meeting', 
                           '--date', '2026-02-10', '--time', '14:00', 
                           '--duration', '60')
        assert result.returncode == 0
        assert 'created successfully' in result.stdout
    """
    cmd = ['calctl'] + list(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input_text,
        check=check
    )
    
    return result


def assert_command_success(result, expected_in_output=None):
    """Assert that command succeeded"""
    assert result.returncode == 0, (
        f"Command failed with exit code {result.returncode}\n"
        f"STDERR: {result.stderr}\n"
        f"STDOUT: {result.stdout}"
    )
    
    if expected_in_output:
        assert expected_in_output in result.stdout, (
            f"Expected '{expected_in_output}' in output\n"
            f"Got: {result.stdout}"
        )


def assert_command_failed(result, expected_exit_code=None, expected_in_stderr=None):
    """Assert that command failed with expected error"""
    assert result.returncode != 0, "Command should have failed but succeeded"
    
    if expected_exit_code:
        assert result.returncode == expected_exit_code, (
            f"Expected exit code {expected_exit_code}, got {result.returncode}"
        )
    
    if expected_in_stderr:
        assert expected_in_stderr in result.stderr, (
            f"Expected '{expected_in_stderr}' in stderr\n"
            f"Got: {result.stderr}"
        )

def run_calctl(*args, input_text=None, check=False):
    """
    Run calctl command via subprocess
    
    Args:
        *args: Command arguments
        input_text: Text to send to stdin
        check: Raise exception on non-zero exit
    
    Returns:
        subprocess.CompletedProcess
    """
    cmd = ['calctl'] + list(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input_text,
        check=check
    )
    
    return result