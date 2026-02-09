#!/usr/bin/env bash

# teardown_suite runs once after ALL tests in the Bats suite
# Use this for cleanup operations

teardown_suite() {
    # Clean up test data
    rm -rf ~/.calctl
    
    # Restore backed up data (if exists)
    if [ -n "$CALCTL_BACKUP_DIR" ] && [ -d "$CALCTL_BACKUP_DIR" ]; then
        mv "$CALCTL_BACKUP_DIR" "$HOME/.calctl"
        echo "# Restored original calctl data" >&2
    fi
    
    # Unset test environment variables
    unset CALCTL_TEST_MODE
    unset BATS_TEST_TIMEOUT
    
    echo "# Bats suite teardown complete" >&2
}