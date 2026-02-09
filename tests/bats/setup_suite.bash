#!/usr/bin/env bash

# setup_suite runs once before ALL tests in the Bats suite
# Use this for expensive one-time setup operations

setup_suite() {
    # Ensure calctl is installed and available
    if ! command -v calctl &> /dev/null; then
        echo "ERROR: calctl command not found. Please run: pip install -e ." >&2
        exit 1
    fi
    
    # Verify calctl version
    calctl --version &> /dev/null || {
        echo "ERROR: calctl --version failed" >&2
        exit 1
    }
    
    # Export test environment variables
    export CALCTL_TEST_MODE=1
    export BATS_TEST_TIMEOUT=30
    
    # Create backup of existing data (optional)
    if [ -d "$HOME/.calctl" ]; then
        export CALCTL_BACKUP_DIR="$HOME/.calctl.bats.backup.$$"
        mv "$HOME/.calctl" "$CALCTL_BACKUP_DIR"
        echo "# Backed up existing calctl data to: $CALCTL_BACKUP_DIR" >&2
    fi
    
    # Clean test data directory
    rm -rf ~/.calctl
    
    echo "# Bats suite setup complete" >&2
}