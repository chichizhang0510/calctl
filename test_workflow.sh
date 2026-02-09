#!/usr/bin/env bash
#
# test_workflow.sh - Comprehensive test suite for calctl
#
# This script tests all commands with edge cases and boundary conditions.
# Tests are organized by command, with sub-tests for different scenarios.
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Data directory
DATA_DIR="$HOME/.calctl"
DATA_FILE="$DATA_DIR/events.json"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo ""
    echo -e "${YELLOW}───────────────────────────────────────────────────────────${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}───────────────────────────────────────────────────────────${NC}"
}

test_pass() {
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
    echo -e "${GREEN}✓${NC} $1"
}

test_fail() {
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
    echo -e "${RED}✗${NC} $1"
}

assert_success() {
    local desc="$1"
    shift
    if "$@" &>/dev/null; then
        test_pass "$desc"
        return 0
    else
        test_fail "$desc (command failed: $*)"
        return 1
    fi
}

assert_fail() {
    local desc="$1"
    local expected_code="$2"
    shift 2
    
    local actual_code=0
    "$@" &>/dev/null || actual_code=$?
    
    if [ "$actual_code" -eq "$expected_code" ]; then
        test_pass "$desc (exit code: $expected_code)"
        return 0
    else
        test_fail "$desc (expected exit $expected_code, got $actual_code)"
        return 1
    fi
}

assert_contains() {
    local desc="$1"
    local pattern="$2"
    shift 2
    
    local output
    output=$("$@" 2>&1)
    
    if echo "$output" | grep -q "$pattern"; then
        test_pass "$desc"
        return 0
    else
        test_fail "$desc (pattern '$pattern' not found)"
        echo "  Output was: $output"
        return 1
    fi
}

cleanup() {
    rm -rf "$DATA_DIR"
}

# =============================================================================
# Test Suite
# =============================================================================

main() {
    print_header "CALCTL COMPREHENSIVE TEST SUITE"
    
    # Clean start
    cleanup
    
    # Run all test groups
    test_add_command
    test_list_command
    test_show_command
    test_delete_command
    test_edit_command
    test_search_command
    test_agenda_command
    test_conflict_detection
    test_recurring_events
    test_datetime_edge_cases
    test_force_flag
    test_date_range_inclusive
    
    # Summary
    print_header "TEST SUMMARY"
    echo "Total:  $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    
    if [ "$TESTS_FAILED" -gt 0 ]; then
        echo -e "${RED}Failed: $TESTS_FAILED${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

# =============================================================================
# ADD Command Tests
# =============================================================================

test_add_command() {
    print_header "Testing: calctl add"
    cleanup
    
    print_section "Basic add functionality"
    
    # Valid add
    assert_success "Add valid event" \
        calctl add --title "Meeting" --date "2026-03-15" --time "14:00" --duration 60
    
    # With optional fields
    assert_success "Add with description and location" \
        calctl add --title "Lunch" --date "2026-03-15" --time "12:00" --duration 45 \
        --description "Team lunch" --location "Cafeteria"
    
    print_section "Input validation"
    
    # Empty title
    assert_fail "Reject empty title" 2 \
        calctl add --title "" --date "2026-03-15" --time "14:00" --duration 60
    
    # Invalid date format
    assert_fail "Reject invalid date format (MM/DD/YYYY)" 2 \
        calctl add --title "Test" --date "03/15/2026" --time "14:00" --duration 60
    
    assert_fail "Reject invalid date format (YYYY-M-D)" 2 \
        calctl add --title "Test" --date "2026-3-15" --time "14:00" --duration 60
    
    # Invalid time format
    assert_fail "Reject 12-hour time format" 2 \
        calctl add --title "Test" --date "2026-03-15" --time "2:00pm" --duration 60
    
    # Test that time without leading zero is accepted and normalized
    assert_success "Accept and normalize time without leading zero (9:00 -> 09:00)" \
        calctl add --title "Normalize Test" --date "2026-03-15" --time "9:00" --duration 60
    
    # Verify the time was normalized to 09:00
    local output_183
    output_183=$(calctl add --title "Time Normalization" --date "2026-03-16" --time "9:30" --duration 60 2>&1)
    local event_id_183
    event_id_183=$(echo "$output_183" | grep -oE 'evt-[a-f0-9]+')
    if calctl show "$event_id_183" 2>/dev/null | grep -q "Start: 09:30"; then
        test_pass "Time normalized from 9:30 to 09:30"
    else
        test_fail "Time normalization failed"
    fi

    # Invalid duration
    assert_fail "Reject negative duration" 2 \
        calctl add --title "Test" --date "2026-03-15" --time "14:00" --duration -30
    
    assert_fail "Reject zero duration" 2 \
        calctl add --title "Test" --date "2026-03-15" --time "14:00" --duration 0
    
    assert_fail "Reject too large duration (>24h)" 2 \
        calctl add --title "Test" --date "2026-03-15" --time "14:00" --duration 1500
    
    print_section "Midnight crossing validation"
    
    # Event crossing midnight
    assert_fail "Reject event crossing midnight" 2 \
        calctl add --title "Late Event" --date "2026-03-15" --time "23:30" --duration 120
    
    # Edge case: ends exactly at midnight (should fail)
    assert_fail "Reject event ending exactly at midnight" 2 \
        calctl add --title "Night Event" --date "2026-03-15" --time "22:00" --duration 120
    
    # Edge case: ends one minute before midnight (should pass)
    assert_success "Accept event ending at 23:59" \
        calctl add --title "Late Work" --date "2026-03-16" --time "22:00" --duration 119
}

# =============================================================================
# CONFLICT DETECTION Tests
# =============================================================================

test_conflict_detection() {
    print_header "Testing: Conflict Detection Edge Cases"
    cleanup
    
    print_section "Boundary conflicts"
    
    # Base event: 10:00-11:00
    calctl add --title "Base Event" --date "2026-03-20" --time "10:00" --duration 60 &>/dev/null
    
    # End == Start (no conflict) ✅
    assert_success "No conflict: end == start (10:00 event after 09:00-10:00)" \
        calctl add --title "Before" --date "2026-03-20" --time "09:00" --duration 60
    
    assert_success "No conflict: start == end (11:00 event after 10:00-11:00)" \
        calctl add --title "After" --date "2026-03-20" --time "11:00" --duration 60
    
    print_section "Overlap scenarios"
    
    # Complete containment (new event contains existing)
    assert_fail "Conflict: new event completely contains existing" 4 \
        calctl add --title "Wrapper" --date "2026-03-20" --time "09:30" --duration 120
    
    # Complete containment (existing contains new)
    assert_fail "Conflict: existing event completely contains new" 4 \
        calctl add --title "Inner" --date "2026-03-20" --time "10:15" --duration 30
    
    # Partial overlap (start before, end during)
    assert_fail "Conflict: partial overlap (start before)" 4 \
        calctl add --title "Overlap Start" --date "2026-03-20" --time "09:30" --duration 45
    
    # Partial overlap (start during, end after)
    assert_fail "Conflict: partial overlap (end after)" 4 \
        calctl add --title "Overlap End" --date "2026-03-20" --time "10:30" --duration 45
    
    # Exact match
    assert_fail "Conflict: exact same time slot" 4 \
        calctl add --title "Duplicate Time" --date "2026-03-20" --time "10:00" --duration 60
    
    print_section "Multi-event conflicts"
    
    # Add more events
    calctl add --title "Event2" --date "2026-03-20" --time "14:00" --duration 60 &>/dev/null
    calctl add --title "Event3" --date "2026-03-20" --time "16:00" --duration 60 &>/dev/null
    
    # New event conflicts with multiple existing events
    assert_fail "Conflict: new event conflicts with multiple events" 4 \
        calctl add --title "Long Meeting" --date "2026-03-20" --time "13:30" --duration 180
    
    print_section "Different dates (no conflict)"
    
    # Same time, different date
    assert_success "No conflict: same time, different date" \
        calctl add --title "Next Day" --date "2026-03-21" --time "10:00" --duration 60
}

# =============================================================================
# FORCE FLAG Tests
# =============================================================================

test_force_flag() {
    print_header "Testing: --force Flag"
    cleanup
    
    # Add base event
    calctl add --title "Existing" --date "2026-03-25" --time "10:00" --duration 60 &>/dev/null
    
    print_section "Force bypasses conflict check"
    
    # Without force: should fail
    assert_fail "Without --force: conflict detected" 4 \
        calctl add --title "Conflict" --date "2026-03-25" --time "10:30" --duration 60
    
    # With force: should succeed
    assert_success "With --force: conflict ignored" \
        calctl add --title "Forced" --date "2026-03-25" --time "10:30" --duration 60 --force
    
    # Verify both events exist
    local count
    count=$(calctl --json list | grep -c '"id"' || true)
    if [ "$count" -eq 2 ]; then
        test_pass "Both conflicting events exist after --force"
    else
        test_fail "Expected 2 events, found $count"
    fi
}

# =============================================================================
# RECURRING EVENTS Tests
# =============================================================================

test_recurring_events() {
    print_header "Testing: Recurring Events (--repeat + --count)"
    cleanup
    
    print_section "Basic recurring events"
    
    # Daily recurring
    assert_success "Create daily recurring events (count=3)" \
        calctl add --title "Daily Standup" --date "2026-04-01" --time "09:00" --duration 15 \
        --repeat daily --count 3
    
    # Weekly recurring
    assert_success "Create weekly recurring events (count=4)" \
        calctl add --title "Weekly Review" --date "2026-04-01" --time "14:00" --duration 60 \
        --repeat weekly --count 4
    
    print_section "Edge case: count=1"
    
    # count=1 should still work
    assert_success "Recurring with count=1 works" \
        calctl add --title "One Time" --date "2026-04-02" --time "10:00" --duration 30 \
        --repeat daily --count 1
    
    print_section "Validation: missing or invalid count"
    
    # Missing count with repeat (defaults to 1, should work)
    assert_success "Repeat without explicit count (uses default)" \
        calctl add --title "Default Count" --date "2026-04-03" --time "11:00" --duration 30 --repeat daily
    
    # Invalid count
    assert_fail "Reject negative count" 2 \
        calctl add --title "Bad Count" --date "2026-04-04" --time "12:00" --duration 30 \
        --repeat daily --count -1
    
    assert_fail "Reject zero count" 2 \
        calctl add --title "Zero Count" --date "2026-04-04" --time "12:00" --duration 30 \
        --repeat daily --count 0
    
    print_section "Validation: invalid repeat value"
    
    assert_fail "Reject invalid repeat value (monthly)" 2 \
        calctl add --title "Invalid Repeat" --date "2026-04-05" --time "13:00" --duration 30 \
        --repeat monthly --count 3
    
    print_section "Conflict handling: batch rejection"
    cleanup
    
    # Add existing event on 2026-04-10
    calctl add --title "Blocker" --date "2026-04-10" --time "15:00" --duration 60 &>/dev/null
    
    # Try to create recurring events where one occurrence conflicts
    # Expected: entire batch is rejected (no partial success)
    assert_fail "Reject entire batch when one occurrence conflicts" 4 \
        calctl add --title "Recurring" --date "2026-04-08" --time "15:30" --duration 60 \
        --repeat daily --count 5
    
    # Verify no partial events were created
    local conflict_count
    conflict_count=$(calctl --json list 2>/dev/null | grep -c '"Recurring"' || true)
    if [ "$conflict_count" -eq 0 ]; then
        test_pass "No partial recurring events created after conflict"
    else
        test_fail "Found $conflict_count partial events (expected 0)"
    fi
    
    print_section "Force with recurring events"
    
    # Same scenario but with --force
    assert_success "With --force: create all recurring events despite conflict" \
        calctl add --title "Forced Recurring" --date "2026-04-08" --time "15:30" --duration 60 \
        --repeat daily --count 5 --force
}

# =============================================================================
# DATE RANGE INCLUSIVE Tests
# =============================================================================

test_date_range_inclusive() {
    print_header "Testing: --from/--to Inclusive Behavior"
    cleanup
    
    # Setup: events on consecutive days
    calctl add --title "Day1" --date "2026-05-10" --time "10:00" --duration 60 &>/dev/null
    calctl add --title "Day2" --date "2026-05-11" --time "10:00" --duration 60 &>/dev/null
    calctl add --title "Day3" --date "2026-05-12" --time "10:00" --duration 60 &>/dev/null
    calctl add --title "Day4" --date "2026-05-13" --time "10:00" --duration 60 &>/dev/null
    
    print_section "Inclusive boundaries"
    
    # Test --from is inclusive (<=)
    local from_result
    from_result=$(calctl --json list --from "2026-05-11" --to "2026-05-13" | grep -c '"title"' || true)
    if [ "$from_result" -eq 3 ]; then
        test_pass "--from is inclusive: includes start date (3 events: Day2, Day3, Day4)"
    else
        test_fail "--from inclusive check: expected 3, got $from_result"
    fi
    
    # Test --to is inclusive (<=)
    local to_result
    to_result=$(calctl --json list --from "2026-05-10" --to "2026-05-12" | grep -c '"title"' || true)
    if [ "$to_result" -eq 3 ]; then
        test_pass "--to is inclusive: includes end date (3 events: Day1, Day2, Day3)"
    else
        test_fail "--to inclusive check: expected 3, got $to_result"
    fi
    
    # Exact range
    local exact_result
    exact_result=$(calctl --json list --from "2026-05-11" --to "2026-05-12" | grep -c '"title"' || true)
    if [ "$exact_result" -eq 2 ]; then
        test_pass "Both boundaries inclusive (2 events: Day2, Day3)"
    else
        test_fail "Both boundaries check: expected 2, got $exact_result"
    fi
    
    # Single day range (from == to)
    local single_result
    single_result=$(calctl --json list --from "2026-05-11" --to "2026-05-11" | grep -c '"title"' || true)
    if [ "$single_result" -eq 1 ]; then
        test_pass "Single day range (from == to): 1 event"
    else
        test_fail "Single day range: expected 1, got $single_result"
    fi
    
    print_section "Only --from or --to"
    
    # Only --from (no upper bound)
    local from_only
    from_only=$(calctl --json list --from "2026-05-12" | grep -c '"title"' || true)
    if [ "$from_only" -eq 2 ]; then
        test_pass "--from only: includes all events from date onwards (2 events)"
    else
        test_fail "--from only: expected 2, got $from_only"
    fi
    
    # Only --to (no lower bound)
    local to_only
    to_only=$(calctl --json list --to "2026-05-11" | grep -c '"title"' || true)
    if [ "$to_only" -eq 2 ]; then
        test_pass "--to only: includes all events up to date (2 events)"
    else
        test_fail "--to only: expected 2, got $to_only"
    fi
}

# =============================================================================
# DATE/TIME EDGE CASES
# =============================================================================

test_datetime_edge_cases() {
    print_header "Testing: Date/Time Edge Cases"
    cleanup
    
    print_section "Time format validation"
    
    # Valid formats
    assert_success "Accept time: 00:00" \
        calctl add --title "Midnight" --date "2026-06-01" --time "00:00" --duration 30
    
    # Test event that ends exactly at 23:59:59 (last valid second of the day)
    assert_success "Accept event ending at 23:59 (23:00 + 59min)" \
        calctl add --title "Late Evening" --date "2026-06-02" --time "23:00" --duration 59

    # Verify that events crossing midnight are rejected
    assert_fail "Reject event crossing midnight (23:59 + 1min)" 2 \
        calctl add --title "Cross Midnight" --date "2026-06-02" --time "23:59" --duration 1
     
    # Invalid formats
    assert_fail "Reject time: 24:00" 2 \
        calctl add --title "Invalid" --date "2026-06-03" --time "24:00" --duration 30
    
    assert_fail "Reject time: 12:60" 2 \
        calctl add --title "Invalid" --date "2026-06-03" --time "12:60" --duration 30
    
    # Test single digit hour normalization
    local output_492
    output_492=$(calctl add --title "Normalize Hour" --date "2026-06-03" --time "9:30" --duration 30 2>&1)
    local event_id_492
    event_id_492=$(echo "$output_492" | grep -oE 'evt-[a-f0-9]+')
    if calctl show "$event_id_492" 2>/dev/null | grep -q "Start: 09:30"; then
        test_pass "Single digit hour normalized (9:30 -> 09:30)"
    else
        test_fail "Single digit hour normalization failed"
    fi

    print_section "Date format validation"
    
    # Invalid dates
    assert_fail "Reject date: month > 12" 2 \
        calctl add --title "Invalid" --date "2026-13-01" --time "10:00" --duration 30
    
    assert_fail "Reject date: day > 31" 2 \
        calctl add --title "Invalid" --date "2026-01-32" --time "10:00" --duration 30
    
    assert_fail "Reject date: Feb 30" 2 \
        calctl add --title "Invalid" --date "2026-02-30" --time "10:00" --duration 30
    
    # Leap year edge case
    assert_success "Accept: Feb 28 (non-leap year)" \
        calctl add --title "Feb 28" --date "2026-02-28" --time "10:00" --duration 30
    
    assert_fail "Reject: Feb 29 (non-leap year 2026)" 2 \
        calctl add --title "Feb 29" --date "2026-02-29" --time "10:00" --duration 30
    
    print_section "Duration edge cases"
    
    # Minimum valid duration
    assert_success "Accept: duration=1 minute" \
        calctl add --title "Quick" --date "2026-06-10" --time "10:00" --duration 1
    
    # Maximum valid duration (just under 24 hours)
    assert_success "Accept: duration=1439 minutes (23:59)" \
        calctl add --title "Long" --date "2026-06-11" --time "00:00" --duration 1439
    
    # Just over 24 hours
    assert_fail "Reject: duration=1441 minutes (>24h)" 2 \
        calctl add --title "Too Long" --date "2026-06-12" --time "10:00" --duration 1441
}

# =============================================================================
# LIST Command Tests
# =============================================================================

test_list_command() {
    print_header "Testing: calctl list"
    cleanup
    
    # Setup test data
    local today
    today=$(date +%Y-%m-%d)
    
    calctl add --title "Today1" --date "$today" --time "09:00" --duration 60 &>/dev/null
    calctl add --title "Today2" --date "$today" --time "14:00" --duration 60 &>/dev/null
    calctl add --title "Tomorrow" --date "2026-07-01" --time "10:00" --duration 60 &>/dev/null
    calctl add --title "NextWeek" --date "2026-07-08" --time "10:00" --duration 60 &>/dev/null
    
    print_section "List filters"
    
    # --today
    assert_contains "List --today shows today's events" "Today1" \
        calctl list --today
    
    # --week
    assert_success "List --week succeeds" \
        calctl list --week
    
    # --from / --to (tested in detail in test_date_range_inclusive)
    assert_success "List --from --to succeeds" \
        calctl list --from "2026-07-01" --to "2026-07-31"
    
    # Default (no flags) - should show future events from today
    assert_success "List with no flags shows future events" \
        calctl list
}

# =============================================================================
# SHOW Command Tests
# =============================================================================

test_show_command() {
    print_header "Testing: calctl show"
    cleanup
    
    # Add event
    local output
    output=$(calctl add --title "ShowTest" --date "2026-07-15" --time "10:00" --duration 60 2>&1)
    local event_id
    event_id=$(echo "$output" | grep -oE 'evt-[a-f0-9]+')
    
    print_section "Show event details"
    
    assert_success "Show existing event" \
        calctl show "$event_id"
    
    assert_contains "Show displays event title" "ShowTest" \
        calctl show "$event_id"
    
    assert_fail "Show non-existent event" 3 \
        calctl show "evt-9999"
    
    print_section "Show with conflicts"
    
    # Add conflicting event
    calctl add --title "Conflict" --date "2026-07-15" --time "10:30" --duration 60 --force &>/dev/null
    
    assert_contains "Show displays conflicts" "Conflicts:" \
        calctl show "$event_id"
}

# =============================================================================
# DELETE Command Tests
# =============================================================================

test_delete_command() {
    print_header "Testing: calctl delete"
    cleanup
    
    print_section "Delete by ID"
    
    # Add and delete
    local output
    output=$(calctl add --title "ToDelete" --date "2026-08-01" --time "10:00" --duration 60 2>&1)
    local event_id
    event_id=$(echo "$output" | grep -oE 'evt-[a-f0-9]+')
    
    assert_success "Delete existing event with --force" \
        calctl delete "$event_id" --force
    
    assert_fail "Deleted event not found" 3 \
        calctl show "$event_id"
    
    assert_fail "Delete non-existent event" 3 \
        calctl delete "evt-9999" --force
    
    print_section "Delete by date"
    
    # Add multiple events on same date
    calctl add --title "Del1" --date "2026-08-05" --time "09:00" --duration 60 &>/dev/null
    calctl add --title "Del2" --date "2026-08-05" --time "11:00" --duration 60 &>/dev/null
    calctl add --title "Keep" --date "2026-08-06" --time "10:00" --duration 60 &>/dev/null
    
    assert_success "Delete by date with --force" \
        calctl delete --date "2026-08-05" --force
    
    local remaining
    remaining=$(calctl --json list | grep -c '"Del' || true)
    if [ "$remaining" -eq 0 ]; then
        test_pass "All events on date deleted"
    else
        test_fail "Expected 0 'Del' events, found $remaining"
    fi
    
    print_section "Dry-run mode"
    
    output=$(calctl add --title "DryRun" --date "2026-08-10" --time "10:00" --duration 60 2>&1)
    event_id=$(echo "$output" | grep -oE 'evt-[a-f0-9]+')
    
    assert_success "Delete --dry-run succeeds" \
        calctl delete "$event_id" --dry-run
    
    # Verify event still exists
    if calctl show "$event_id" &>/dev/null; then
        test_pass "Event not deleted after --dry-run"
    else
        test_fail "Event was deleted despite --dry-run"
    fi
}

# =============================================================================
# EDIT Command Tests
# =============================================================================

test_edit_command() {
    print_header "Testing: calctl edit"
    cleanup
    
    # Add base event
    local output
    output=$(calctl add --title "Original" --date "2026-09-01" --time "10:00" --duration 60 2>&1)
    local event_id
    event_id=$(echo "$output" | grep -oE 'evt-[a-f0-9]+')
    
    print_section "Edit fields"
    
    assert_success "Edit title" \
        calctl edit "$event_id" --title "Updated"
    
    assert_contains "Title updated" "Updated" \
        calctl show "$event_id"
    
    assert_success "Edit time" \
        calctl edit "$event_id" --time "14:00"
    
    assert_success "Edit duration" \
        calctl edit "$event_id" --duration 90
    
    print_section "Edit validation"
    
    assert_fail "Reject empty title" 2 \
        calctl edit "$event_id" --title ""
    
    assert_fail "Reject no fields provided" 2 \
        calctl edit "$event_id"
    
    print_section "Edit conflict detection"
    
    # Add another event
    calctl add --title "Blocker" --date "2026-09-01" --time "16:00" --duration 60 &>/dev/null
    
    # Try to edit first event to conflict with second
    assert_fail "Edit rejected due to conflict" 4 \
        calctl edit "$event_id" --time "16:30"
}

# =============================================================================
# SEARCH Command Tests
# =============================================================================

test_search_command() {
    print_header "Testing: calctl search"
    cleanup
    
    # Add test events
    calctl add --title "Team Meeting" --date "2026-10-01" --time "10:00" --duration 60 \
        --description "Weekly sync" &>/dev/null
    calctl add --title "Lunch Break" --date "2026-10-01" --time "12:00" --duration 45 \
        --location "Cafeteria" &>/dev/null
    calctl add --title "Code Review" --date "2026-10-02" --time "14:00" --duration 30 &>/dev/null
    
    print_section "Search functionality"
    
    assert_contains "Search by title (partial match)" "Team Meeting" \
        calctl search "team"
    
    assert_contains "Search in description" "Team Meeting" \
        calctl search "sync"
    
    assert_contains "Search in location" "Lunch Break" \
        calctl search "cafeteria"
    
    assert_success "Search --title limits to title field" \
        calctl search "team" --title
    
    assert_fail "Search empty query" 2 \
        calctl search ""
    
    # Case insensitive
    assert_contains "Search is case-insensitive" "Code Review" \
        calctl search "CODE"
}

# =============================================================================
# AGENDA Command Tests
# =============================================================================

test_agenda_command() {
    print_header "Testing: calctl agenda"
    cleanup
    
    local today
    today=$(date +%Y-%m-%d)
    
    # Add events
    calctl add --title "Morning" --date "$today" --time "09:00" --duration 60 &>/dev/null
    calctl add --title "Afternoon" --date "$today" --time "14:00" --duration 60 &>/dev/null
    
    print_section "Agenda views"
    
    assert_success "Agenda for today (default)" \
        calctl agenda
    
    assert_success "Agenda --week" \
        calctl agenda --week
    
    assert_success "Agenda --date" \
        calctl agenda --date "$today"
    
    assert_contains "Agenda shows event count" "Total:" \
        calctl agenda
}

# =============================================================================
# Run Tests
# =============================================================================

main "$@"