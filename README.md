# calctl

A command-line calendar management tool.
[![CI Status](https://github.com/chichizhang0510/calctl/workflows/Main%20Branch%20CI/badge.svg)](https://github.com/chichizhang0510/calctl/actions)
[![Coverage](https://codecov.io/gh/chichizhang0510/calctl/branch/main/graph/badge.svg)](https://codecov.io/gh/chichizhang0510/calctl)
[![Docker](https://img.shields.io/docker/v/chichizhang/calctl)](https://hub.docker.com/r/chichizhang/calctl)

This project demonstrates:
- CLI design best practices
- Conflict detection
- Automated testing
- Docker-based distribution
- CI/CD with GitHub Actions



## Features

- Add, edit, delete, and search events
- Conflict detection with optional `--force`
- Daily and weekly agenda views
- Recurring events (daily / weekly)
- JSON output support
- File-based persistence




## Installation (Local)

### Prerequisites
- Python 3.10+
- pip

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

### Verify:
```bash
calctl --version
calctl --help
```


## Usage (CLI)

### Quick Start
Here's a complete workflow to get you started:

#### 1.Add your first event
```bash
calctl add --title "Lunch with Alice" --date 2026-02-15 --time 12:00 --duration 60

# Output: Event evt-abc123 created successfully
```


#### 2. See what you have
```bash
calctl list

# Output: 
# ID           Date         Time     Duration   Title
# ----------------------------------------------------------------------
# evt-abc123   2026-02-15   12:00    60 min     Lunch with Alice
```


#### 3. Add another event (this will detect conflict!)
```bash
calctl add --title "Dentist" --date 2026-02-15 --time 12:30 --duration 30

# Output: Error: Conflict detected with evt-abc123 (Lunch with Alice)
#         Use --force to override
```

#### 4. Check today's schedule
```bash
calctl list --today
```

#### 5. View this week's agenda
```bash
calctl agenda --week
```

#### 6. Edit an event
```bash
calctl edit evt-abc123 --title "Lunch with Alice & Bob" --duration 90
```

#### 7. Delete when done
```bash
calctl delete evt-abc123
```

### Add an event
```bash
# Basic event
calctl add --title "Team Meeting" --date 2026-02-10 --time 14:00 --duration 60


# With full details
calctl add --title "Team Meeting" \
  --date 2026-02-10 \
  --time 14:00 \
  --duration 60 \
  --description "Q1 Planning" \
  --location "Conference Room A"

# Recurring events**
calctl add --title "Daily Standup" --date 2026-02-10 --time 09:00 --duration 15 \
  --repeat daily --count 5

calctl add --title "Weekly Review" --date 2026-02-10 --time 16:00 --duration 30 \
  --repeat weekly --count 4

# Force add (skip conflict detection)
calctl add --title "Emergency Meeting" --date 2026-02-10 --time 14:30 --duration 30 --force
```

### Edit an event
```bash
# Edit specific fields
calctl edit evt-abc123 --title "Updated Title"
calctl edit evt-abc123 --time 15:00 --duration 90

# Edit multiple fields at once
calctl edit evt-abc123 \
  --title "New Title" \
  --description "New description" \
  --location "New location"
```

### Delete events
```bash
# Delete single event
calctl delete evt-abc123

# Preview deletion (dry-run)
calctl delete evt-abc123 --dry-run

# Delete all events on a specific date
calctl delete --date 2026-02-15

# Skip confirmation
calctl delete evt-abc123 --force
```

### Viewing Events
List events
```bash
# List all events
calctl list

# Filter by time period
calctl list --today
calctl list --week

# Custom date range
calctl list --from 2026-02-10 --to 2026-02-20
```

Show event details
```bash
# Display full details of a specific event
calctl show evt-abc123
```

Agenda view
```bash
# Today's agenda (default)
calctl agenda

# This week's agenda
calctl agenda --week

# Specific date
calctl agenda --date 2026-02-15
```


### Search
Search events by keyword:
```bash
# Search in title and description
calctl search "meeting"

# Search only in titles
calctl search "standup" --title
```

### Global Options
These options work with any command:
```bash
# JSON output (useful for scripting)
calctl --json list 
calctl --json show evt-abc123 

# Disable colored output
calctl --no-color list

# Show version
calctl --version

# Show help
calctl --help
calctl add --help  # Command-specific help
```


## Exit Codes

calctl uses specific exit codes to indicate different types of failures, making it easy to handle errors in scripts:

| Code | Meaning | Example |
|------|---------|---------|
| `0` | Success | Command completed successfully |
| `1` | General error | Storage I/O failure, unexpected error |
| `2` | Invalid input | Missing required arguments, invalid date format |
| `3` | Not found | Event ID doesn't exist |
| `4` | Conflict detected | Time slot already occupied (without `--force`) |
| `130` | User cancelled | Ctrl+C pressed during execution |



## Data Storage
Events are stored locally in:
```bash
~/.calctl/events.json
```
The directory and file are created automatically on first use.




## Docker Usage

### Build image
```bash
docker build -t calctl .
```

### Run with persistent storage
```bash
docker volume create calctl-data

docker run --rm -v calctl-data:/home/calctl/.calctl \
  username/calctl list
```
You can also mount a local directory:
```bash
docker run --rm -v $(pwd)/data:/home/calctl/.calctl \
  username/calctl list
```



## Development & Testing

Run tests and coverage:
```bash
pytest
coverage run -m pytest
coverage report
```

Build documentation:
```bash
mkdocs build
```


## CI/CD
The project uses GitHub Actions:
- PR workflow: lint, tests, coverage, docs build
- Main workflow: full validation and build artifacts
- Release workflow: triggered on SemVer tags, builds and publishes Docker image



## Author

ChiChi Zhang 

GitHub: https://github.com/chichizhang  
Docker Hub: https://hub.docker.com/r/chichizhang/calctl




## License

MIT License