#!/usr/bin/env bats

setup() {
    rm -rf ~/.calctl
}

@test "agenda: shows daily agenda" {
    calctl add --title "Event 1" --date "2026-02-10" --time "09:00" --duration 30
    calctl add --title "Event 2" --date "2026-02-10" --time "14:00" --duration 60
    
    run calctl agenda --date "2026-02-10"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "2026-02-10" ]]
    [[ "$output" =~ "Event 1" ]]
    [[ "$output" =~ "Event 2" ]]
}

@test "agenda: shows weekly agenda" {
    calctl add --title "Monday Event" --date "2026-02-10" --time "10:00" --duration 30
    
    run calctl agenda --week
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Week Agenda" ]] || [[ "$output" =~ "Agenda" ]]
}

@test "agenda: JSON output format" {
    calctl add --title "Test" --date "2026-02-10" --time "10:00" --duration 30
    
    run calctl --json agenda --date "2026-02-10"
    
    [ "$status" -eq 0 ]
    echo "$output" | python3 -m json.tool > /dev/null
}