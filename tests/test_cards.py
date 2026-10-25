import datetime as dt
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "cards", Path(__file__).resolve().parents[1] / "tools" / "make_cards.py"
)
cards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cards)


class ContributionCalendarTests(unittest.TestCase):
    def test_calendar_crossing_year_boundary_uses_github_total(self):
        calendar = {"totalContributions": 5, "weeks": [{"contributionDays": [
            {"date": "2025-12-31", "contributionCount": 2},
            {"date": "2026-01-01", "contributionCount": 3},
        ]}]}
        with patch.object(cards, "gql", return_value={
            "contributionsCollection": {"contributionCalendar": calendar}
        }) as request:
            days = cards.fetch_days("test-token", "example", dt.date(2026, 1, 1))
        request.assert_called_once_with("test-token", {
            "login": "example", "from": "2025-01-02T00:00:00Z",
            "to": "2026-01-01T23:59:59Z",
        })
        self.assertEqual(cards.streaks(days)[0], 5)
        self.assertEqual(days[0][0], dt.date(2025, 12, 31))

    def test_inconsistent_api_total_is_rejected(self):
        with patch.object(cards, "gql", return_value={"contributionsCollection": {
            "contributionCalendar": {"totalContributions": 1, "weeks": []}
        }}):
            with self.assertRaises(ValueError):
                cards.fetch_days("test-token", "example")

    def test_today_can_be_empty_but_yesterday_cannot(self):
        start = dt.date(2026, 10, 20)
        days = [(start + dt.timedelta(days=i), c) for i, c in enumerate([1, 2, 0])]
        self.assertEqual(cards.streaks(days)[1], 2)
        days.append((start + dt.timedelta(days=3), 0))
        self.assertEqual(cards.streaks(days)[1], 0)


if __name__ == "__main__":
    unittest.main()
