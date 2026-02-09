#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

# ============================================================================
# Conflict Detection Tests
# ============================================================================

@test "conflicts: overlapping events detected" {
    # Add first event
    run calctl add --title "Event 1" --date "2026-02-10" --time "14:00" --duration 60
    [ "$status" -eq 0 ]
    
    # Try to add conflicting event
    run calctl add --title "Event 2" --date "2026-02-10" --time "14:30" --duration 60
    
    [ "$status" -eq 4 ]  # ConflictError exit code
    [[ "$output" =~ "conflict" ]]
}

@test "conflicts: force flag bypasses conflict check" {
    # Add first event
    calctl add --title "Event 1" --date "2026-02-10" --time "14:00" --duration 60
    
    # Force add conflicting event
    run calctl add --title "Event 2" --date "2026-02-10" --time "14:30" --duration 60 --force
    
    [ "$status" -eq 0 ]
}

@test "conflicts: adjacent events do not conflict" {
    # Add first event: 14:00-15:00
    run calctl add --title "Event 1" --date "2026-02-10" --time "14:00" --duration 60
    [ "$status" -eq 0 ]
    
    # Add adjacent event: 15:00-16:00
    run calctl add --title "Event 2" --date "2026-02-10" --time "15:00" --duration 60
    
    [ "$status" -eq 0 ]  # Should succeed
}

@test "conflicts: events on different dates do not conflict" {
    calctl add --title "Event 1" --date "2026-02-10" --time "14:00" --duration 60
    
    run calctl add --title "Event 2" --date "2026-02-11" --time "14:00" --duration 60
    
    [ "$status" -eq 0 ]
}

@test "conflicts: show command displays conflicts" {
    # Add two overlapping events with --force
    calctl add --title "Event 1" --date "2026-02-10" --time "14:00" --duration 60
    EVENT_ID=$(calctl --json add --title "Event 2" --date "2026-02-10" --time "14:30" --duration 60 --force | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    # Show should display conflicts
    run calctl show "$EVENT_ID"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Conflict" ]]
}