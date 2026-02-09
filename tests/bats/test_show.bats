#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

teardown() {
    :
}

# ============================================================================
# Show Command Tests
# ============================================================================

@test "show: displays event details" {
    # Add event and get ID
    EVENT_ID=$(calctl --json add \
        --title "Team Meeting" \
        --date "2026-02-10" \
        --time "14:00" \
        --duration 60 \
        --description "Weekly sync" \
        --location "Room 101" \
        | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl show "$EVENT_ID"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "ID: $EVENT_ID" ]] || [[ "$output" =~ "$EVENT_ID" ]]
    [[ "$output" =~ "Team Meeting" ]]
    [[ "$output" =~ "2026-02-10" ]]
    [[ "$output" =~ "14:00" ]]
    [[ "$output" =~ "60 min" ]] || [[ "$output" =~ "60" ]]
    [[ "$output" =~ "Weekly sync" ]]
    [[ "$output" =~ "Room 101" ]]
}

@test "show: displays event with minimal fields" {
    EVENT_ID=$(calctl --json add \
        --title "Simple Event" \
        --date "2026-02-10" \
        --time "10:00" \
        --duration 30 \
        | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl show "$EVENT_ID"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Simple Event" ]]
}

@test "show: JSON output returns valid JSON" {
    EVENT_ID=$(calctl --json add \
        --title "Test" \
        --date "2026-02-10" \
        --time "10:00" \
        --duration 30 \
        | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl --json show "$EVENT_ID"
    
    [ "$status" -eq 0 ]
    
    # Validate JSON structure
    echo "$output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert 'event' in data
assert 'conflicts' in data
assert data['event']['id'] == '$EVENT_ID'
"
    [ $? -eq 0 ]
}

@test "show: non-existent event returns exit code 3" {
    run calctl show "evt-nonexistent"
    
    [ "$status" -eq 3 ]  # NotFoundError
    [[ "$output" =~ "not found" ]] || [[ "$output" =~ "Not found" ]]
}

@test "show: displays conflicts when they exist" {
    # Add two overlapping events with --force
    EVENT1_ID=$(calctl --json add --title "Event 1" --date "2026-02-10" --time "14:00" --duration 60 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    EVENT2_ID=$(calctl --json add --title "Event 2" --date "2026-02-10" --time "14:30" --duration 60 --force | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    # Show event should display conflicts
    run calctl show "$EVENT2_ID"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Conflict" ]] || [[ "$output" =~ "conflict" ]]
}

@test "show: displays no conflicts when none exist" {
    EVENT_ID=$(calctl --json add --title "Solo Event" --date "2026-02-10" --time "10:00" --duration 30 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl show "$EVENT_ID"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "none" ]] || [[ "$output" =~ "Conflicts: none" ]]
}

@test "show: displays created and updated timestamps" {
    EVENT_ID=$(calctl --json add --title "Test" --date "2026-02-10" --time "10:00" --duration 30 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl show "$EVENT_ID"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Created:" ]] || [[ "$output" =~ "created" ]]
    [[ "$output" =~ "Updated:" ]] || [[ "$output" =~ "updated" ]]
}

@test "show: displays end time calculation" {
    EVENT_ID=$(calctl --json add --title "Test" --date "2026-02-10" --time "14:00" --duration 90 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl show "$EVENT_ID"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "15:30" ]]  # 14:00 + 90min = 15:30
}