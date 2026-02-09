#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

# ============================================================================
# Delete Tests
# ============================================================================

@test "delete: deletes event by ID with --force" {
    # Add event
    EVENT_ID=$(calctl --json add --title "Test" --date "2026-02-10" --time "10:00" --duration 30 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    # Delete with force
    run calctl delete "$EVENT_ID" --force
    
    [ "$status" -eq 0 ]
    
    # Verify deleted
    run calctl show "$EVENT_ID"
    [ "$status" -eq 3 ]  # NotFoundError
}

@test "delete: dry-run shows what would be deleted" {
    EVENT_ID=$(calctl --json add --title "Test" --date "2026-02-10" --time "10:00" --duration 30 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    # Dry run
    run calctl delete "$EVENT_ID" --dry-run
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Would delete" ]]
    
    # Verify NOT actually deleted
    run calctl show "$EVENT_ID"
    [ "$status" -eq 0 ]  # Still exists
}

@test "delete: deletes all events on date with --force" {
    # Add multiple events on same date
    calctl add --title "Event 1" --date "2026-02-10" --time "09:00" --duration 30
    calctl add --title "Event 2" --date "2026-02-10" --time "14:00" --duration 45
    calctl add --title "Event 3" --date "2026-02-11" --time "10:00" --duration 60
    
    # Delete by date
    run calctl delete --date "2026-02-10" --force
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "2" ]] || [[ "$output" =~ "Deleted" ]]
}

@test "delete: dry-run for date deletion" {
    calctl add --title "Event 1" --date "2026-02-10" --time "10:00" --duration 30
    
    run calctl delete --date "2026-02-10" --dry-run
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Would delete" ]] || [[ "$output" =~ "dry-run" ]]
}

@test "delete: non-existent event returns exit code 3" {
    run calctl delete "evt-nonexistent" --force
    
    [ "$status" -eq 3 ]  # NotFoundError
    [[ "$output" =~ "not found" ]]
}