from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inspect_ck3_save_scheduled_events import inspect_melted


class ScheduledEventInspectionTests(unittest.TestCase):
    def test_filters_event_prefix_and_root_and_reports_relative_days(self) -> None:
        text = '''version="1.19.0.6"
date=1067.10.28
triggered_event={
\tevent="zg361b1.102"
\tscope={
\t\troot={
\t\t\ttype=char
\t\t\tidentity=29037
\t\t}
\t}
\tdate=1067.10.29
}
triggered_event={
\tevent="other.1"
\tscope={
\t\troot={
\t\t\ttype=char
\t\t\tidentity=29037
\t\t}
\t}
\tdate=1067.11.1
}
'''
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_text(text, encoding="utf-8")
            result = inspect_melted(
                path, event_prefix="zg361b1.", root_character_id=29037
            )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["matched_count"], 1)
        self.assertEqual(
            result["matches"],
            [
                {
                    "event": "zg361b1.102",
                    "root_character_id": 29037,
                    "date": "1067.10.29",
                    "days_from_current": 1,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
