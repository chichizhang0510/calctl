#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

# ============================================================================
# Error Code Tests
# ============================================================================

@test "error-codes: exit code 2 for invalid input" {
    run calctl add --title "" --date "2026-02-10" --time "10:00" --duration 30
    [ "$status" -eq 2 ]
}

@test "error-codes: exit code 3 for not found" {
    run calctl show "evt-nonexistent"
    [ "$status" -eq 3 ]
}

@test "error-codes: exit code 4 for conflicts" {
    calctl add --title "Event 1" --date "2026-02-10" --time "14:00" --duration 60
    
    run calctl add --title "Event 2" --date "2026-02-10" --time "14:30" --duration 60
    
    [ "$status" -eq 4 ]
}

@test "error-codes: exit code 0 for success" {
    run calctl add --title "Test" --date "2026-02-10" --time "10:00" --duration 30
    [ "$status" -eq 0 ]
}

@test "error-codes: exit code 130 for Ctrl-C simulation" {
    skip "Cannot easily test Ctrl-C in Bats"
    # This would require special handling
}