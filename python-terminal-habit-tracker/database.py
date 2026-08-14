import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path="habits.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                tags TEXT DEFAULT '',
                frequency TEXT DEFAULT 'daily',
                custom_days TEXT DEFAULT '',
                remind_time TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_date TEXT NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Insert default if missing
        c.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("notifications_enabled", "true"),
        )
        self.conn.commit()

    def add_habit(self, name, category, tags, frequency, custom_days, remind_time):
        try:
            self.conn.execute(
                """INSERT INTO habits
                   (name, category, tags, frequency, custom_days, remind_time, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, category, tags, frequency, custom_days, remind_time,
                 datetime.now().strftime("%Y-%m-%d")),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB error adding habit: {e}")

    def delete_habit(self, habit_id):
        try:
            self.conn.execute("DELETE FROM completions WHERE habit_id = ?", (habit_id,))
            self.conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB error deleting habit: {e}")

    def get_all_habits(self):
        return self.conn.execute("SELECT * FROM habits ORDER BY id").fetchall()

    def get_habit_by_id(self, habit_id):
        return self.conn.execute(
            "SELECT * FROM habits WHERE id = ?", (habit_id,)
        ).fetchone()

    def mark_complete(self, habit_id, date_str):
        try:
            # Avoid duplicate entries for same day
            existing = self.conn.execute(
                "SELECT id FROM completions WHERE habit_id = ? AND completed_date = ?",
                (habit_id, date_str),
            ).fetchone()
            if not existing:
                self.conn.execute(
                    "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?)",
                    (habit_id, date_str),
                )
                self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB error marking complete: {e}")

    def get_completions(self, habit_id):
        rows = self.conn.execute(
            "SELECT completed_date FROM completions WHERE habit_id = ? ORDER BY completed_date",
            (habit_id,),
        ).fetchall()
        return [r["completed_date"] for r in rows]

    def update_habit(self, habit_id, name, category, tags, frequency, custom_days, remind_time):
        try:
            self.conn.execute(
                """UPDATE habits
                   SET name=?, category=?, tags=?, frequency=?, custom_days=?, remind_time=?
                   WHERE id=?""",
                (name, category, tags, frequency, custom_days, remind_time, habit_id),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB error updating habit: {e}")

    def get_setting(self, key):
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def save_setting(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
