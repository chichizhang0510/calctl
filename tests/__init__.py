"""
Test suite for calctl

This package contains all tests for the calctl application.

Test structure:
- unit/        : Unit tests (fast, isolated)
- integration/ : Integration tests (moderate speed, real dependencies)
- e2e/         : End-to-end tests (slow, full system)
"""

import sys
from pathlib import Path


project_root = Path(__file__).parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

__version__ = "0.1.0"

TEST_DATA_DIR = Path(__file__).parent / "data"
TEMP_DIR = Path(__file__).parent / "temp"


def get_test_resource_path(filename: str) -> Path:
    """Get path to test resource file"""
    return TEST_DATA_DIR / filename