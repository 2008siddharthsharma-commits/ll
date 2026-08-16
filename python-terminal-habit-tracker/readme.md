# Habit Tracker

A terminal-based habit tracker with streaks, charts, and system notifications.

## Description

Track daily, weekly, or custom-schedule habits right from your terminal. Built with Textual for the UI, plotext for in-terminal charts, and plyer for desktop notifications. All data lives in a local SQLite database that's created automatically on first run.

## Features

- **Streak Tracking** — current streak and longest streak for every habit
- **Flexible Scheduling** — daily, weekly (Monday), or custom days (Mon,Wed,Fri)
- **SQLite Persistence** — `habits.db` created automatically, zero config
- **Categories & Tags** — organize habits with categories and comma-separated tags
- **Reminders** — set a time (HH:MM) and get desktop notifications when it's due
- **Completion Rate** — percentage of expected days you actually completed
- **Terminal Charts** — bar charts of weekly completions rendered in your terminal
- **Keyboard-Driven UI** — full navigation without touching the mouse

## Project Files

```
database.py       → SQLite database layer (DatabaseManager class)
calculation.py    → Streak, rate, and summary logic (HabitCalculator class)
tui.py            → Terminal UI screens and app (Textual)
main.py           → Entry point, starts reminder thread + app
requirements.txt  → 3 dependencies: textual, plotext, plyer
readme.md         → This file
habits.db         → Auto-created on first run (not in repo)
```

## Installation

```bash
# Clone or download the files
pip install -r requirements.txt
```

Requires Python 3.9+.

## How To Use

```bash
python main.py
```

### Keyboard Shortcuts (Dashboard)

| Key | Action |
|-----|--------|
| `a` | Add a new habit |
| `d` | Delete selected habit |
| `c` | Mark selected habit complete for today |
| `v` | View habit detail (streaks, chart) |
| `n` | Toggle notifications on/off |
| `q` | Quit |
| `↑↓` | Navigate habit list |
| `Esc` | Go back from any screen |

### Adding a Habit

- **Name** — required
- **Category** — optional, defaults to "General"
- **Tags** — comma-separated, e.g. `fitness,morning`
- **Frequency** — Daily, Weekly (Monday), or Custom
- **Custom days** — e.g. `Mon,Wed,Fri` (only used with Custom frequency)
- **Reminder time** — `HH:MM` format, e.g. `08:00` (leave empty for no reminder)

After saving, you'll see a confirmation with two choices: **Add Another** (clears the form for a new habit) or **Done** (back to dashboard).

### Confirmations

Every action that changes data asks you to confirm first:

- **Delete** → "Delete 'Habit Name'?" → Yes / No
- **Complete** → "Mark 'Habit Name' complete for today?" → Yes / No
- **Add** → saves, then shows "✓ Habit saved!" with Add Another / Done

### Notifications

Press `n` on the dashboard to toggle notifications on or off. The current state is shown in the status bar. When enabled, the app checks every 60 seconds and sends a desktop notification if a habit's reminder time matches the current time.

## How To Extend

The code is split into clean layers:

1. **Add a new table** — edit `create_tables()` in `database.py`
2. **Add analytics** — add methods to `HabitCalculator` in `calculation.py`
3. **Add a screen** — create a new `Screen` class in `tui.py` and wire a keybinding

Each file handles one concern. Database knows SQL. Calculator knows math. TUI knows display. Main just wires them together.
