from datetime import datetime, timedelta
from collections import defaultdict

DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class HabitCalculator:

    def get_expected_dates(self, created_at, frequency, custom_days):
        """All dates from created_at to today that match the frequency."""
        start = datetime.strptime(created_at, "%Y-%m-%d").date()
        today = datetime.now().date()
        custom = [d.strip() for d in custom_days.split(",") if d.strip()] if custom_days else []

        dates = []
        d = start
        while d <= today:
            if frequency == "daily":
                dates.append(d)
            elif frequency == "weekly":
                if d.weekday() == 0:  # Monday
                    dates.append(d)
            elif frequency == "custom" and custom:
                if DAY_ABBR[d.weekday()] in custom:
                    dates.append(d)
            d += timedelta(days=1)
        return dates

    def get_current_streak(self, completion_dates, frequency, custom_days):
        if not completion_dates:
            return 0
        completed = set(completion_dates)
        today = datetime.now().date()
        oldest = min(datetime.strptime(d, "%Y-%m-%d").date() for d in completion_dates)
        streak = 0
        d = today

        # Walk backwards but don't go before first completion
        while d >= oldest:
            if not self._is_expected_day(d, frequency, custom_days):
                d -= timedelta(days=1)
                continue
            if d.strftime("%Y-%m-%d") in completed:
                streak += 1
                d -= timedelta(days=1)
            else:
                break
        return streak

    def get_longest_streak(self, completion_dates, frequency, custom_days):
        if not completion_dates:
            return 0
        completed = set(completion_dates)
        # Walk forward through all days from first completion
        first = min(datetime.strptime(d, "%Y-%m-%d").date() for d in completion_dates)
        today = datetime.now().date()

        longest = 0
        current = 0
        d = first
        while d <= today:
            if not self._is_expected_day(d, frequency, custom_days):
                d += timedelta(days=1)
                continue
            if d.strftime("%Y-%m-%d") in completed:
                current += 1
                longest = max(longest, current)
            else:
                current = 0
            d += timedelta(days=1)
        return longest

    def get_completion_rate(self, completion_dates, created_at, frequency, custom_days):
        expected = self.get_expected_dates(created_at, frequency, custom_days)
        if not expected:
            return 0.0
        completed = len(set(completion_dates))
        return round(completed / len(expected) * 100, 1)

    def get_weekly_summary(self, completion_dates):
        summary = defaultdict(int)
        for d in completion_dates:
            dt = datetime.strptime(d, "%Y-%m-%d")
            week_key = dt.strftime("%G-W%V")
            summary[week_key] += 1
        return dict(sorted(summary.items()))

    def get_monthly_summary(self, completion_dates):
        summary = defaultdict(int)
        for d in completion_dates:
            dt = datetime.strptime(d, "%Y-%m-%d")
            summary[dt.strftime("%Y-%m")] += 1
        return dict(sorted(summary.items()))

    def is_due_today(self, frequency, custom_days):
        today = datetime.now().date()
        return self._is_expected_day(today, frequency, custom_days)

    def _is_expected_day(self, d, frequency, custom_days):
        if frequency == "daily":
            return True
        if frequency == "weekly":
            return d.weekday() == 0
        if frequency == "custom":
            custom = [x.strip() for x in custom_days.split(",") if x.strip()] if custom_days else []
            return DAY_ABBR[d.weekday()] in custom
        return True
