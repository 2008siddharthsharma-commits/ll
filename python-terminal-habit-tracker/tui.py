import io
from contextlib import redirect_stdout
from datetime import datetime

import plotext as plt
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, DataTable, Static, Input, Button, Select, Label,
)

from database import DatabaseManager
from calculation import HabitCalculator


# ─── Confirm Dialog (reusable) ────────────────────────────────────

class ConfirmScreen(Screen):
    """Yes/No dialog. Dismisses with True or False."""
    BINDINGS = [Binding("escape", "no", "Cancel")]

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"\n  {self.message}\n", classes="title")
        with Horizontal():
            yield Button("Yes", variant="success", id="yes")
            yield Button("No", variant="error", id="no")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id == "yes")

    def action_no(self):
        self.dismiss(False)


# ─── Dashboard ────────────────────────────────────────────────────

class DashboardScreen(Screen):
    BINDINGS = [
        Binding("a", "add", "Add Habit"),
        Binding("d", "delete", "Delete"),
        Binding("c", "complete", "Complete"),
        Binding("v", "view", "View Detail"),
        Binding("n", "toggle_notif", "Notifications"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("  Habit Tracker Dashboard", classes="title")
        yield DataTable(id="habits_table")
        yield Static("", id="status_bar")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#habits_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Name", "Category", "Tags", "Streak", "Due", "Rate%")
        self.load_habits()

    def load_habits(self):
        db: DatabaseManager = self.app.db
        calc: HabitCalculator = self.app.calc
        table = self.query_one("#habits_table", DataTable)
        table.clear()

        habits = db.get_all_habits()
        notif = db.get_setting("notifications_enabled")
        notif_label = "ON" if notif == "true" else "OFF"
        status = self.query_one("#status_bar", Static)

        if not habits:
            status.update(f"  No habits yet. Press [bold]a[/bold] to add one.  |  Notifications: {notif_label}")
            return

        status.update(f"  {len(habits)} habit(s)  |  Notifications: {notif_label}")

        for h in habits:
            comps = db.get_completions(h["id"])
            streak = calc.get_current_streak(comps, h["frequency"], h["custom_days"])
            due = "Yes" if calc.is_due_today(h["frequency"], h["custom_days"]) else ""
            rate = calc.get_completion_rate(comps, h["created_at"], h["frequency"], h["custom_days"])
            table.add_row(
                str(h["id"]), h["name"], h["category"],
                h["tags"], str(streak), due, f"{rate}%",
                key=str(h["id"]),
            )

    def _selected_id(self):
        table = self.query_one("#habits_table", DataTable)
        if table.row_count == 0:
            return None
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        row = table.get_row(row_key)
        return int(row[0])

    def action_add(self):
        def on_done(result):
            self.load_habits()
            if result == "another":
                self.action_add()

        self.app.push_screen(AddHabitScreen(), on_done)

    def action_delete(self):
        hid = self._selected_id()
        if hid is None:
            return
        habit = self.app.db.get_habit_by_id(hid)
        name = habit["name"] if habit else "this habit"

        def on_confirm(confirmed):
            if confirmed:
                self.app.db.delete_habit(hid)
                self.load_habits()

        self.app.push_screen(ConfirmScreen(f"Delete '{name}'?"), on_confirm)

    def action_complete(self):
        hid = self._selected_id()
        if hid is None:
            return
        habit = self.app.db.get_habit_by_id(hid)
        name = habit["name"] if habit else "this habit"

        def on_confirm(confirmed):
            if confirmed:
                self.app.db.mark_complete(hid, datetime.now().strftime("%Y-%m-%d"))
                self.load_habits()

        self.app.push_screen(ConfirmScreen(f"Mark '{name}' complete for today?"), on_confirm)

    def action_view(self):
        hid = self._selected_id()
        if hid is None:
            return
        self.app.push_screen(HabitDetailScreen(hid))

    def action_toggle_notif(self):
        db = self.app.db
        current = db.get_setting("notifications_enabled")
        db.save_setting("notifications_enabled", "false" if current == "true" else "true")
        self.load_habits()

    def action_quit(self):
        self.app.exit()


# ─── Add Habit ────────────────────────────────────────────────────

class AddHabitScreen(Screen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Label("Add New Habit", classes="title")
            yield Label("Name *")
            yield Input(placeholder="e.g. Morning Run", id="name")
            yield Label("Category")
            yield Input(placeholder="e.g. Health", id="category")
            yield Label("Tags (comma separated)")
            yield Input(placeholder="e.g. fitness,cardio", id="tags")
            yield Label("Frequency")
            yield Select(
                [("Daily", "daily"), ("Weekly (Mon)", "weekly"), ("Custom days", "custom")],
                value="daily", id="frequency",
            )
            yield Label("Custom days (e.g. Mon,Wed,Fri)")
            yield Input(placeholder="Mon,Wed,Fri", id="custom_days")
            yield Label("Reminder time (HH:MM or empty)")
            yield Input(placeholder="08:00", id="remind_time")
            yield Button("Save", variant="success", id="save")
            yield Button("Cancel", variant="error", id="cancel")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "save":
            self._save()

    def _save(self):
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.query_one("#name", Input).focus()
            return
        category = self.query_one("#category", Input).value.strip() or "General"
        tags = self.query_one("#tags", Input).value.strip()
        freq = self.query_one("#frequency", Select).value
        custom = self.query_one("#custom_days", Input).value.strip()
        remind = self.query_one("#remind_time", Input).value.strip()

        self.app.db.add_habit(name, category, tags, freq, custom, remind)

        # Ask if they want to add another
        def on_answer(add_more):
            self.dismiss("another" if add_more else "done")

        self.app.push_screen(
            ConfirmScreen("Habit saved! Add another?"), on_answer
        )

    def action_cancel(self):
        self.dismiss(None)


# ─── Habit Detail ─────────────────────────────────────────────────

class HabitDetailScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def __init__(self, habit_id: int):
        super().__init__()
        self.habit_id = habit_id

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static("", id="detail_info")
            yield Static("", id="chart_area")
        yield Footer()

    def on_mount(self):
        db = self.app.db
        calc = self.app.calc
        h = db.get_habit_by_id(self.habit_id)
        if not h:
            self.query_one("#detail_info", Static).update("Habit not found.")
            return

        comps = db.get_completions(self.habit_id)
        cur_streak = calc.get_current_streak(comps, h["frequency"], h["custom_days"])
        long_streak = calc.get_longest_streak(comps, h["frequency"], h["custom_days"])
        rate = calc.get_completion_rate(comps, h["created_at"], h["frequency"], h["custom_days"])
        weekly = calc.get_weekly_summary(comps)

        info = (
            f"[bold]{h['name']}[/bold]\n"
            f"Category: {h['category']}   Tags: {h['tags']}\n"
            f"Frequency: {h['frequency']}   Custom days: {h['custom_days']}\n"
            f"Reminder: {h['remind_time'] or 'None'}   Created: {h['created_at']}\n\n"
            f"Current Streak: [green]{cur_streak}[/green]   "
            f"Longest Streak: [cyan]{long_streak}[/cyan]   "
            f"Completion Rate: [yellow]{rate}%[/yellow]\n"
            f"Total completions: {len(comps)}"
        )
        self.query_one("#detail_info", Static).update(info)

        chart_str = self._build_chart(weekly)
        self.query_one("#chart_area", Static).update(chart_str)

    def _build_chart(self, weekly):
        if not weekly:
            return "No completion data to chart yet."
        items = list(weekly.items())[-12:]
        labels = [k for k, _ in items]
        values = [v for _, v in items]

        plt.clear_figure()
        plt.bar(labels, values)
        plt.title("Weekly Completions")
        plt.theme("dark")
        plt.plot_size(70, 15)

        buf = io.StringIO()
        with redirect_stdout(buf):
            plt.show()
        return buf.getvalue()

    def action_back(self):
        self.app.pop_screen()


# ─── App ──────────────────────────────────────────────────────────

class HabitTrackerApp(App):
    CSS = """
    .title { padding: 1 2; text-style: bold; }
    #status_bar { padding: 0 2; color: $text-muted; }
    #habits_table { height: 1fr; margin: 0 1; }
    #detail_info { padding: 1 2; }
    #chart_area { padding: 0 2; }
    Input { margin: 0 2 1 2; }
    Select { margin: 0 2 1 2; }
    Label { padding: 0 2; }
    Horizontal { padding: 1 2; }
    Button { margin: 0 2 1 2; }
    """

    TITLE = "Habit Tracker"

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.calc = HabitCalculator()

    def on_mount(self):
        self.push_screen(DashboardScreen())

    def on_screen_resume(self, event):
        screen = self.screen
        if isinstance(screen, DashboardScreen):
            screen.load_habits()
