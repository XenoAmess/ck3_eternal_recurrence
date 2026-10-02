"""Focused semantic tamper tests against the sealed a02 native response."""

from __future__ import annotations

from copy import deepcopy
import unittest

from verify_e2_05_a02_candidate import DEFAULT_ROOT, source, verify_trace_binding


FINISH = "ck3-output/interactive-requests-responses/e2-05-d26-trace-finish.json"


class TraceBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original = source(DEFAULT_ROOT, FINISH)["body"]

    def test_sealed_trace_binding(self) -> None:
        verify_trace_binding(self.original)

    def test_rejects_mutated_sequence_identity_dates_and_events(self) -> None:
        mutations = {
            "finish token": lambda d: d.update(managed_daily_sequence_token=102),
            "checkpoint token": lambda d: d["managed_trace"]["managed_checkpoint"]["after"].update(
                managed_daily_sequence_token=102),
            "record token": lambda d: d["managed_trace"]["trace"]["records"][5].update(
                managed_daily_sequence_token=102),
            "record date": lambda d: d["managed_trace"]["trace"]["records"][5].update(
                native_date_raw=53146848),
            "wound prelude": lambda d: d["managed_trace"]["trace"]["records"][2]
                ["battle_events"][0].update(right_character_id=1),
            "opposite side": lambda d: next(
                knight for knight in d["managed_trace"]["trace"]["records"][5]
                ["sides"][0]["knights"] if knight["character_id"] == 34120
            ).update(character_id=1),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                tampered = deepcopy(self.original)
                mutate(tampered)
                with self.assertRaises(ValueError):
                    verify_trace_binding(tampered)


if __name__ == "__main__":
    unittest.main()
