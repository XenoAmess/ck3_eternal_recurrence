from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.settlement_contract import (
    normalize_fixed_score,
    normalize_one_life_settlement,
    parse_completed_tutorial_lessons,
    settlement_ready_for_episode,
    tutorial_record_observation,
)


def _settlement(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "ready": True,
        "commit_serial": 1,
        "source_character_id": 707,
        "final_score": {"raw": 40_525_000, "scale": 100_000},
        "score_before_reject": {"raw": 41_000_000, "scale": 100_000},
        "record_candidate": 405,
        "old_record": 400,
        "record_delta": 5,
        "blessing_count": 3,
        "refusal_count": 1,
        "contract_progress": 7,
        "record_written": True,
    }
    result.update(overrides)
    return result


class SettlementContractTests(unittest.TestCase):
    def test_normalizes_ready_semantic_score_payload(self) -> None:
        normalized = normalize_one_life_settlement(_settlement())

        self.assertEqual(normalized["final_score"], 405.25)
        self.assertEqual(normalized["score_before_reject"], 410)
        self.assertTrue(settlement_ready_for_episode(normalized, 707))
        self.assertFalse(settlement_ready_for_episode(normalized, 808))

    def test_integral_fixed_score_is_canonical_integer(self) -> None:
        self.assertEqual(normalize_fixed_score(405.0), 405)
        self.assertEqual(
            normalize_fixed_score({"raw": 40_525_000, "scale": 100_000}),
            405.25,
        )
        with self.assertRaisesRegex(ValueError, "malformed"):
            normalize_fixed_score({"raw": 405_000, "scale": 0})

    def test_pending_payload_does_not_require_unpublished_values(self) -> None:
        self.assertEqual(
            normalize_one_life_settlement(
                {"ready": 0, "commit_serial": 0}
            ),
            {"ready": False, "commit_serial": 0},
        )

    def test_ready_payload_rejects_inconsistent_record_delta(self) -> None:
        with self.assertRaisesRegex(ValueError, "record_delta"):
            normalize_one_life_settlement(_settlement(record_delta=4))

    def test_prohibits_record_written_without_new_record(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a new record"):
            normalize_one_life_settlement(
                _settlement(
                    record_candidate=400,
                    old_record=400,
                    record_delta=0,
                    record_written=True,
                )
            )

    def test_parses_and_observes_completed_record_lesson(self) -> None:
        source = (
            '\ufefflast_lesson_chain="reactive_advice"\n'
            "completed_lessons={\n"
            "\treactive_advice_army_automation\n"
            "\t\"xar_hs_ge_405\"\n"
            "}\n"
        )
        self.assertEqual(
            parse_completed_tutorial_lessons(source),
            frozenset(
                {"reactive_advice_army_automation", "xar_hs_ge_405"}
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tutorial.txt"
            path.write_text(source, encoding="utf-8")
            observed = tutorial_record_observation(path, 405)

        self.assertTrue(observed["present"])
        self.assertEqual(observed["lesson_id"], "xar_hs_ge_405")
        self.assertEqual(len(observed["sha256"]), 64)

    def test_zero_record_requires_no_tutorial_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            observed = tutorial_record_observation(
                Path(temporary) / "missing.txt", 0
            )
        self.assertTrue(observed["present"])
        self.assertIsNone(observed["lesson_id"])


if __name__ == "__main__":
    unittest.main()
