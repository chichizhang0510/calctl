#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

@test "edit: updates event title" {
    EVENT_ID=$(calctl --json add --title "Original" --date "2026-02-10" --time "10:00" --duration 30 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl edit "$EVENT_ID" --title "Updated"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Updated" ]]
}

@test "edit: updates multiple fields" {
    EVENT_ID=$(calctl --json add --title "Test" --date "2026-02-10" --time "10:00" --duration 30 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl edit "$EVENT_ID" --title "New Title" --duration 60 --location "Office"
    
    [ "$status" -eq 0 ]
}

@test "edit: with no fields returns error" {
    EVENT_ID=$(calctl --json add --title "Test" --date "2026-02-10" --time "10:00" --duration 30 | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
    
    run calctl edit "$EVENT_ID"
    
    [ "$status" -eq 2 ]  # InvalidInputError
    [[ "$output" =~ "No fields provided" ]]
}

@test "edit: non-existent event returns error" {
    run calctl edit "evt-nonexistent" --title "Test"
    
    [ "$status" -eq 3 ]  # NotFoundError
}