#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

@test "search: finds events by title" {
    calctl add --title "Team Meeting" --date "2026-02-10" --time "10:00" --duration 30
    calctl add --title "Lunch Break" --date "2026-02-10" --time "12:00" --duration 45
    calctl add --title "Client Meeting" --date "2026-02-11" --time "14:00" --duration 60
    
    run calctl search "meeting"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Team Meeting" ]]
    [[ "$output" =~ "Client Meeting" ]]
    [[ ! "$output" =~ "Lunch Break" ]]  # Should not match
}

@test "search: case insensitive" {
    calctl add --title "IMPORTANT" --date "2026-02-10" --time "10:00" --duration 30
    
    run calctl search "important"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "IMPORTANT" ]]
}

@test "search: empty query returns error" {
    run calctl search ""
    
    [ "$status" -eq 2 ]  # InvalidInputError
}

@test "search: --title flag searches only titles" {
    calctl add --title "Meeting" --date "2026-02-10" --time "10:00" --duration 30 --description "Important discussion"
    
    run calctl search "discussion" --title
    
    # Should not find (search only in title)
    [[ ! "$output" =~ "Meeting" ]]
}