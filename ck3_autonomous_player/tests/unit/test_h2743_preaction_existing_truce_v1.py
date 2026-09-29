"""Fail-closed checks for the H2743 native read-only slot wire."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.h2743_preaction_existing_truce_v1 import (
    CHECKPOINT_SHA256, DATE_RAW, EPISODE, QUERY_STEP, normalize_result,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


def result() -> dict[str, object]:
    return {
        "step": QUERY_STEP, "accepted": True, "query_sequence": 1,
        "snapshot_revision": 3, "backend_id": "native-headless",
        "h2743_preaction_existing_truce": {
            "schema": "xar.ck3.h2743_preaction_existing_truce.v1",
            "backend_id": "ck3-1.19.0.6-native-h2743-existing-truce-v1",
            "war_id": 16777231, "owner_character_id": 30097,
            "toward_character_id": 29829, "episode_id_claim": EPISODE,
            "episode_authenticated_here": False,
            "checkpoint_sha256_claim": CHECKPOINT_SHA256,
            "checkpoint_bytes_authenticated_here": False,
            "status": "existing_truce", "snapshot_revision": 3,
            "date_raw": DATE_RAW, "same_frame_stable": True,
            "preaction_existing_expiry_observable": True,
            "preaction_existing_expiry_date_raw": DATE_RAW + 100,
            "post_surrender_actual_expiry_date_raw": None,
            "script_candidate_days": None,
            "effect_projection_complete": False, "material_complete": False,
            "recommended_outcome": None, "action_literal": None,
            "unavailable_reason": None,
        },
    }


class ExistingTruceWireTest(unittest.TestCase):
    def test_existing_and_absent_slot(self) -> None:
        sample = result()
        self.assertEqual(normalize_result(sample, native_revision=3)["status"], "existing_truce")
        absent = copy.deepcopy(sample)
        wire = absent["h2743_preaction_existing_truce"]
        wire.update(status="no_existing_truce", preaction_existing_expiry_observable=False,
                    preaction_existing_expiry_date_raw=None, unavailable_reason="no_existing_truce")
        self.assertEqual(normalize_result(absent, native_revision=3)["status"], "no_existing_truce")

    def test_future_effect_claim_is_rejected(self) -> None:
        for key, value in (("post_surrender_actual_expiry_date_raw", DATE_RAW + 200),
                           ("script_candidate_days", 30), ("effect_projection_complete", True),
                           ("material_complete", True), ("action_literal", "surrender-war-16777231")):
            sample = result()
            sample["h2743_preaction_existing_truce"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_result(sample, native_revision=3)

    def test_source_frame_and_direction_are_bound(self) -> None:
        for key, value in (("war_id", 16777232), ("owner_character_id", 29829),
                           ("toward_character_id", 30097), ("date_raw", DATE_RAW + 1),
                           ("episode_id_claim", "different"),
                           ("checkpoint_sha256_claim", "0" * 64)):
            sample = result()
            sample["h2743_preaction_existing_truce"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_result(sample, native_revision=3)

    def test_expiry_must_be_future_and_native_revision_exact(self) -> None:
        sample = result()
        sample["h2743_preaction_existing_truce"]["preaction_existing_expiry_date_raw"] = DATE_RAW
        with self.assertRaises(ValueError):
            normalize_result(sample, native_revision=3)
        with self.assertRaises(ValueError):
            normalize_result(result(), native_revision=4)
        boolean_revision = result()
        boolean_revision["snapshot_revision"] = True
        with self.assertRaises(ValueError):
            normalize_result(boolean_revision, native_revision=1)

    def test_unknown_fields_are_rejected(self) -> None:
        sample = result()
        sample["h2743_preaction_existing_truce"]["invented"] = 0
        with self.assertRaises(ValueError):
            normalize_result(sample, native_revision=3)

    def test_driver_binds_all_native_request_claims(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        starting = {
            "revision": 3, "native_revision": 3, "snapshot_id": "native:3",
            "date_raw": DATE_RAW, "episode_run_id": EPISODE, "paused": True,
        }
        captured = {}

        def primitive(step: str, **kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            self.assertEqual(step, QUERY_STEP)
            return result()

        with (patch.object(driver, "take_internal_semantic_snapshot", return_value=starting),
              patch.object(driver, "_execute_primitive_step", side_effect=primitive)):
            proof = driver._execute_native_war_step(QUERY_STEP, expected_revision=3)
        self.assertEqual(proof["h2743_preaction_existing_truce_proof"]["status"], "existing_truce")
        self.assertEqual(captured["expected_revision"], 3)
        self.assertTrue(captured["internal_semantic_snapshot"])
        fields = captured["request_fields"]
        self.assertEqual(fields["expected_snapshot_id"], "native:3")
        self.assertEqual(fields["expected_episode_id"], EPISODE)
        self.assertEqual(fields["expected_checkpoint_sha256"], CHECKPOINT_SHA256)
        self.assertEqual(fields["expected_date_raw"], DATE_RAW)
        self.assertEqual(fields["expected_exe_sha256"],
                         "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86")

    def test_driver_rejects_wrong_snapshot_before_native_call(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        starting = {
            "revision": 3, "native_revision": 3, "snapshot_id": "native:4",
            "date_raw": DATE_RAW, "episode_run_id": EPISODE, "paused": True,
        }
        with (patch.object(driver, "take_internal_semantic_snapshot", return_value=starting),
              patch.object(driver, "_execute_primitive_step") as primitive):
            with self.assertRaisesRegex(Exception, "source/frame claim"):
                driver._execute_native_war_step(QUERY_STEP, expected_revision=3)
        primitive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
