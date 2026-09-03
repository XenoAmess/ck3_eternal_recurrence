from __future__ import annotations

import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.raiktor_surrender_truce_contract import (
    BACKEND_ID,
    OPEN_KAISHEK_G2_CAPABILITY_ID,
    OPEN_KAISHEK_G2_PROFILE_COMMIT,
    OPEN_KAISHEK_G2_PROFILE_ID,
    normalize_raiktor_surrender_truce,
)
from xar_autoplayer.bridge import (
    OPEN_KAISHEK_G2_CAPABILITY_ID as PUBLIC_G2_CAPABILITY_ID,
    OPEN_KAISHEK_G2_PROFILE_COMMIT as PUBLIC_G2_PROFILE_COMMIT,
    OPEN_KAISHEK_G2_PROFILE_ID as PUBLIC_G2_PROFILE_ID,
)


ROOT = Path(__file__).resolve().parents[2]


def _observation() -> dict[str, object]:
    return {
        "schema_version": 1,
        "backend_id": BACKEND_ID,
        "status": "available",
        "failure": None,
        "snapshot_revision": 73,
        "native_revision": 4,
        "date_raw": 53_175_816,
        "paused": True,
        "war_id": 16_777_290,
        "active_casus_belli_database_index": 411,
        "active_casus_belli_key": "raiktor_claim_cb",
        "owner_character_id": 29_829,
        "toward_character_id": 17_116,
        "evaluated_days": 1_825,
        "pointer_shape_verified": True,
        "evaluator_double_read_stable": True,
        "same_frame_stable": True,
        "expiry_observable": False,
        "expiry_date_raw": None,
    }


def _normalize(value: object) -> dict[str, object]:
    return normalize_raiktor_surrender_truce(
        value,
        expected_war_id=16_777_290,
        expected_snapshot_revision=73,
        expected_native_revision=4,
        expected_date_raw=53_175_816,
        expected_attacker_character_id=29_829,
        expected_defender_character_id=17_116,
    )


class RaiktorSurrenderTruceContractTests(unittest.TestCase):
    def test_open_kaishek_g2_profile_binding_is_descriptive_only(self) -> None:
        self.assertEqual(
            OPEN_KAISHEK_G2_CAPABILITY_ID,
            "game.command.query-g2-truce-evaluated-days-v1",
        )
        self.assertEqual(
            OPEN_KAISHEK_G2_PROFILE_ID,
            "ck3-1.19.0.6-g2-truce-evaluator-v1",
        )
        self.assertEqual(
            OPEN_KAISHEK_G2_PROFILE_COMMIT,
            "981c79388a07e447b18f8e4472a16fd65e28c083",
        )

    def test_open_kaishek_binding_is_publicly_exported(self) -> None:
        self.assertEqual(PUBLIC_G2_CAPABILITY_ID, OPEN_KAISHEK_G2_CAPABILITY_ID)
        self.assertEqual(PUBLIC_G2_PROFILE_ID, OPEN_KAISHEK_G2_PROFILE_ID)
        self.assertEqual(PUBLIC_G2_PROFILE_COMMIT, OPEN_KAISHEK_G2_PROFILE_COMMIT)

    def test_accepts_exact_evaluated_days_without_expiry_claim(self) -> None:
        value = _observation()
        self.assertEqual(_normalize(value), value)

    def test_rejects_schema_or_binding_drift(self) -> None:
        for key, replacement in (
            ("war_id", 16_777_291),
            ("snapshot_revision", 74),
            ("native_revision", 5),
            ("date_raw", 53_175_817),
            ("active_casus_belli_key", "claim_cb"),
            ("owner_character_id", 17_116),
            ("toward_character_id", 29_829),
        ):
            with self.subTest(key=key):
                value = _observation()
                value[key] = replacement
                with self.assertRaises(ValueError):
                    _normalize(value)
        value = _observation()
        value["extra"] = True
        with self.assertRaises(ValueError):
            _normalize(value)

    def test_rejects_unpaused_unstable_or_negative_observation(self) -> None:
        for key, replacement in (
            ("paused", False),
            ("pointer_shape_verified", False),
            ("evaluator_double_read_stable", False),
            ("same_frame_stable", False),
            ("evaluated_days", -1),
        ):
            with self.subTest(key=key):
                value = _observation()
                value[key] = replacement
                with self.assertRaises(ValueError):
                    _normalize(value)

    def test_rejects_any_invented_expiry(self) -> None:
        value = _observation()
        value["expiry_observable"] = True
        value["expiry_date_raw"] = 53_219_616
        with self.assertRaises(ValueError):
            _normalize(value)
        value = _observation()
        value["expiry_date_raw"] = 53_219_616
        with self.assertRaises(ValueError):
            _normalize(value)

    def test_frozen_source_contract_excludes_crashing_preview_path(self) -> None:
        fixture_path = (
            ROOT
            / "native_bridge"
            / "research"
            / "fixtures"
            / "raiktor_surrender_truce_v1_source_contract.json"
        )
        contract = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(contract["readiness"]["stage"], "fixture-confirmed/static-ready")
        self.assertTrue(contract["readiness"]["live_shape_probe_required"])
        self.assertTrue(contract["readiness"]["public_wire_complete"])
        self.assertEqual(
            contract["readiness"]["public_wire_scope"],
            "evaluated_days_only; expiry_observable=false; expiry_date_raw=null",
        )
        self.assertFalse(contract["readiness"]["production_live"])
        self.assertTrue(contract["read_contract"]["evaluated_days_public_wire"])
        self.assertFalse(contract["read_contract"]["expiry_observable"])
        source = (
            ROOT
            / "native_bridge"
            / "src"
            / "raiktor_surrender_truce_v1.cpp"
        ).read_text(encoding="utf-8")
        for forbidden in contract["forbidden_production_paths"][:5]:
            self.assertNotIn(forbidden, source)
        self.assertNotIn("24LL", source)
        self.assertNotIn("expiry_date_raw", source)


if __name__ == "__main__":
    unittest.main()
