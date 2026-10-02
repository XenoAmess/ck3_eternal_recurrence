from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    is_native_war_step,
    normalize_province_local_siege_result,
    parse_query_province_local_siege_step,
    query_province_local_siege_step,
)


def _result() -> dict[str, object]:
    return {
        "step": "query-province-local-siege-v1-2610",
        "accepted": True,
        "status": "available",
        "query_sequence": 1,
        "snapshot_revision": 4,
        "date_raw": 53219928,
        "province_state": {
            "province_id": 2610,
            "occupation_observable": True,
            "is_occupied": False,
            "occupying_character_id": None,
            "fort_level": 2,
            "garrison_size": 500,
            "besieging_strength": 0,
            "siege_observable": True,
            "active_siege": None,
        },
        "backend_id": "native-headless",
    }


def _normalize(value: dict[str, object]) -> dict[str, object]:
    return normalize_province_local_siege_result(
        value,
        expected_step="query-province-local-siege-v1-2610",
        expected_province_id=2610,
        expected_snapshot_revision=4,
        expected_date_raw=53219928,
    )


class ProvinceLocalSiegeContractTests(unittest.TestCase):
    def test_canonical_step(self) -> None:
        step = query_province_local_siege_step(2610)
        self.assertEqual(step, "query-province-local-siege-v1-2610")
        self.assertEqual(parse_query_province_local_siege_step(step), 2610)
        self.assertTrue(is_native_war_step(step))
        for invalid in (
            "query-province-local-siege-v1-02610",
            "query-province-local-siege-v1-0",
            "query-province-local-siege-v1--1",
            "query-province-local-siege-v1-2610x",
        ):
            self.assertIsNone(parse_query_province_local_siege_step(invalid))

    def test_available_and_partial_keep_null_semantics(self) -> None:
        complete = _normalize(_result())
        self.assertIsNone(complete["province_state"]["active_siege"])
        partial = _result()
        partial["status"] = "partial"
        partial["province_state"]["siege_observable"] = False
        self.assertEqual(_normalize(partial)["status"], "partial")

    def test_reject_stale_or_inferred_state(self) -> None:
        malformed: list[dict[str, object]] = []
        for key, bad in (
            ("snapshot_revision", 5),
            ("date_raw", 53219929),
            ("status", "partial"),
            ("query_sequence", True),
        ):
            row = _result()
            row[key] = bad
            malformed.append(row)
        wrong_id = _result()
        wrong_id["province_state"]["province_id"] = 2611
        malformed.append(wrong_id)
        fake_no_siege = _result()
        fake_no_siege["province_state"]["siege_observable"] = False
        malformed.append(fake_no_siege)
        for row in malformed:
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    _normalize(row)


if __name__ == "__main__":
    unittest.main()
