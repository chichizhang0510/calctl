#!/bin/bash
# test_workflow.sh

set -e  # if any command fails, stop the script

echo "=== delete old data ==="
rm -rf ~/.calctl

echo -e "\n=== test add event ==="
EVENT1=$(calctl add --title "Morning Meeting" --date "2026-02-10" --time "09:00" --duration 30 | grep -oE 'evt-[a-f0-9]+')
echo "Created: $EVENT1"

EVENT2=$(calctl add --title "Lunch Break" --date "2026-02-10" --time "12:00" --duration 60 --location "Cafeteria")
echo "$EVENT2"

echo -e "\n=== test list events ==="
calctl list

echo -e "\n=== test show event ==="
calctl show "$EVENT1"

echo -e "\n=== test delete event ==="
calctl delete "$EVENT1"

echo -e "\n=== test delete event successfully ==="
calctl list

echo -e "\n=== test error handling ==="
calctl add --title "" --date "2026-02-10" --time "10:00" --duration 30 || echo "✓ 空标题错误捕获成功"

echo -e "\n=== view data file ==="
cat ~/.calctl/events.json

echo -e "\n all tests passed!"