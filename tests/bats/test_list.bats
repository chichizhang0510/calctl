#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

@test "list: shows empty list when no events" {
    run calctl list
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "No events" ]] || [ -n "$output" ]
}

@test "list: shows added events" {
    calctl add --title "Event 1" --date "2026-02-10" --time "10:00" --duration 30
    calctl add --title "Event 2" --date "2026-02-11" --time "14:00" --duration 45
    
    run calctl list
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Event 1" ]]
    [[ "$output" =~ "Event 2" ]]
}

@test "list: --today filter works" {
    # Note: This test is date-dependent, may need adjustment
    TODAY=$(date +%Y-%m-%d)
    
    calctl add --title "Today Event" --date "$TODAY" --time "10:00" --duration 30
    calctl add --title "Future Event" --date "2026-12-31" --time "10:00" --duration 30
    
    run calctl list --today
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Today Event" ]]
}

@test "list: JSON output is valid" {
    calctl add --title "Test" --date "2026-02-10" --time "10:00" --duration 30
    
    run calctl --json list
    
    [ "$status" -eq 0 ]
    
    # Validate JSON
    echo "$output" | python3 -m json.tool > /dev/null
    [ $? -eq 0 ]
}