#!/usr/bin/env bats

# Setup/teardown for each test
setup() {
    # Clean data before each test
    rm -rf ~/.calctl
}

teardown() {
    # Optional cleanup
    :
}

# ============================================================================
# Basic Add Tests
# ============================================================================

@test "add: creates event with required fields" {
    run calctl add \
        --title "Team Meeting" \
        --date "2026-02-10" \
        --time "14:00" \
        --duration 60
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "created successfully" ]]
    [[ "$output" =~ "evt-" ]]
}

@test "add: creates event with all optional fields" {
    run calctl add \
        --title "Client Call" \
        --date "2026-02-10" \
        --time "10:00" \
        --duration 45 \
        --description "Quarterly review" \
        --location "Zoom"
    
    [ "$status" -eq 0 ]
}

@test "add: JSON output returns valid JSON" {
    run calctl --json add \
        --title "Test" \
        --date "2026-02-10" \
        --time "10:00" \
        --duration 30
    
    [ "$status" -eq 0 ]
    
    # Verify JSON is valid (using jq if available, or python)
    echo "$output" | python3 -m json.tool > /dev/null
    [ $? -eq 0 ]
}

# ============================================================================
# Input Validation Tests
# ============================================================================

@test "add: empty title returns exit code 2" {
    run calctl add \
        --title "" \
        --date "2026-02-10" \
        --time "10:00" \
        --duration 30
    
    [ "$status" -eq 2 ]
    [[ "$output" =~ "Title is required" ]]
}

@test "add: invalid date format returns exit code 2" {
    run calctl add \
        --title "Test" \
        --date "02/10/2026" \
        --time "10:00" \
        --duration 30
    
    [ "$status" -eq 2 ]
    [[ "$output" =~ "Invalid date format" ]]
}

@test "add: invalid time format returns exit code 2" {
    run calctl add \
        --title "Test" \
        --date "2026-02-10" \
        --time "2:30pm" \
        --duration 30
    
    [ "$status" -eq 2 ]
    [[ "$output" =~ "Invalid time format" ]]
}

@test "add: negative duration returns exit code 2" {
    run calctl add \
        --title "Test" \
        --date "2026-02-10" \
        --time "10:00" \
        --duration -30
    
    [ "$status" -eq 2 ]
}

@test "add: event crossing midnight returns exit code 2" {
    run calctl add \
        --title "Late Night" \
        --date "2026-02-10" \
        --time "23:30" \
        --duration 120
    
    [ "$status" -eq 2 ]
    [[ "$output" =~ "cannot cross midnight" ]]
}

# ============================================================================
# Recurring Events
# ============================================================================

@test "add: daily recurring events" {
    run calctl add \
        --title "Standup" \
        --date "2026-02-10" \
        --time "09:00" \
        --duration 15 \
        --repeat daily \
        --count 5
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "5 occurrences" ]]
}

@test "add: weekly recurring events" {
    run calctl add \
        --title "Team Meeting" \
        --date "2026-02-10" \
        --time "14:00" \
        --duration 60 \
        --repeat weekly \
        --count 3
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "3 occurrences" ]]
}