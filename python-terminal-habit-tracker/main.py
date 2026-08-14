import time
import threading
from datetime import datetime

from database import DatabaseManager
from tui import HabitTrackerApp


def reminder_loop(db):
    """Check habits every 60s and send notifications when due."""
    while True:
        time.sleep(60)
        try:
            if db.get_setting("notifications_enabled") != "true":
                continue
            now = datetime.now().strftime("%H:%M")
            for h in db.get_all_habits():
                if h["remind_time"] == now:
                    from plyer import notification
                    notification.notify(
                        title="Habit Reminder",
                        message=f"Time to: {h['name']}",
                        timeout=5,
                    )
        except Exception:
            pass  # don't crash the background thread


def main():
    db = DatabaseManager()
    t = threading.Thread(target=reminder_loop, args=(db,), daemon=True)
    t.start()
    app = HabitTrackerApp(db)
    app.run()
    db.close()


if __name__ == "__main__":
    main()
