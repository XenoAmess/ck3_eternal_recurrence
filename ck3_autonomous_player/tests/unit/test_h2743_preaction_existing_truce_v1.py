"""Fail-closed checks for the H2743 native read-only slot wire."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.h2743_preaction_existing_truce_v1 import (
    CHECKPOINT_SHA256, DATE_RAW, EPISODE, QUERY_STEP,
    frame_claim_from_snapshot, normalize_result,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


def result(native_revision: int = 3) -> dict[str, object]:
    return {
        "step": QUERY_STEP, "accepted": True, "query_sequence": 1,
        "snapshot_revision": native_revision, "backend_id": "native-headless",
        "h2743_preaction_existing_truce": {
            "schema": "xar.ck3.h2743_preaction_existing_truce.v1",
            "backend_id": "ck3-1.19.0.6-native-h2743-existing-truce-v1",
            "war_id": 16777231, "owner_character_id": 30097,
            "toward_character_id": 29829, "episode_id_claim": EPISODE,
            "episode_authenticated_here": False,
            "checkpoint_sha256_claim": CHECKPOINT_SHA256,
            "checkpoint_bytes_authenticated_here": False,
            "status": "existing_truce", "snapshot_revision": native_revision,
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


def starting_frame(native_revision: int = 4,
                   public_revision: int | None = None) -> dict[str, object]:
    return {
        "revision": (native_revision + 1 if public_revision is None else public_revision),
        "native_revision": native_revision,
        "snapshot_id": f"native:{native_revision}", "date_raw": DATE_RAW,
        "episode_run_id": EPISODE, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "active_wars": [{"war_id": 16777231, "player_side": "defender",
                         "player_is_primary_war_leader": True,
                         "primary_opponent_character_id": 30097,
                         "targeted_title_ids": [2128]}],
        "diagnostics": {"connection_generation": 1},
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
        starting = starting_frame(4)  # R0110's actual paused frame.
        claim = frame_claim_from_snapshot(starting)
        captured = {}

        def primitive(step: str, **kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            self.assertEqual(step, QUERY_STEP)
            return result(4)

        with (patch.object(driver, "take_internal_semantic_snapshot", return_value=starting),
              patch.object(driver, "_execute_primitive_step", side_effect=primitive)):
            proof = driver._execute_native_war_step(
                QUERY_STEP, expected_revision=5, expected_h2743_frame=claim,
            )
        self.assertEqual(proof["h2743_preaction_existing_truce_proof"]["status"], "existing_truce")
        self.assertEqual(captured["expected_revision"], 5)
        self.assertTrue(captured["internal_semantic_snapshot"])
        fields = captured["request_fields"]
        self.assertEqual(fields["expected_snapshot_id"], "native:4")
        self.assertEqual(fields["expected_public_revision"], 5)
        self.assertEqual(fields["expected_native_revision"], 4)
        self.assertEqual(fields["expected_actor_character_id"], 29829)
        self.assertEqual(fields["expected_war_id"], 16777231)
        self.assertEqual(fields["expected_episode_id"], EPISODE)
        self.assertEqual(fields["expected_checkpoint_sha256"], CHECKPOINT_SHA256)
        self.assertEqual(fields["expected_date_raw"], DATE_RAW)
        self.assertEqual(fields["expected_exe_sha256"],
                         "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86")

    def test_independent_public_counter_binds_current_frame(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        before = starting_frame(4, public_revision=7)
        claim = frame_claim_from_snapshot(before)
        self.assertEqual(claim["snapshot_id"], "native:4")
        self.assertEqual(claim["revision"], 7)
        with (patch.object(driver, "take_internal_semantic_snapshot", return_value=before),
              patch.object(driver, "_execute_primitive_step", return_value=result(4)) as primitive):
            driver._execute_native_war_step(
                QUERY_STEP, expected_revision=7, expected_h2743_frame=claim,
            )
        self.assertEqual(primitive.call_args.kwargs["expected_revision"], 7)
        self.assertEqual(primitive.call_args.kwargs["request_fields"]["expected_public_revision"], 7)
        with (patch.object(driver, "take_internal_semantic_snapshot",
                           return_value=starting_frame(4, public_revision=8)),
              patch.object(driver, "_execute_primitive_step") as denied):
            with self.assertRaisesRegex(Exception, "source/frame claim"):
                driver._execute_native_war_step(
                    QUERY_STEP, expected_revision=7, expected_h2743_frame=claim,
                )
        denied.assert_not_called()

    def test_driver_rejects_missing_or_drifted_before_frame(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        before = starting_frame(4)
        claim = frame_claim_from_snapshot(before)
        mutations = [
            {"snapshot_id": "native:3"}, {"revision": 6}, {"revision": 0},
            {"native_revision": 5}, {"date_raw": DATE_RAW + 1},
            {"episode_run_id": "wrong"}, {"paused": False},
            {"map_ready": False},
            {"played_character": {"character_id": 29830, "alive": True}},
            {"active_wars": [{"war_id": 16777232}]},
            {"diagnostics": {"connection_generation": 2}},
        ]
        for changed in mutations:
            with self.subTest(changed=changed):
                current = dict(before, **changed)
                with (patch.object(driver, "take_internal_semantic_snapshot", return_value=current),
                      patch.object(driver, "_execute_primitive_step") as primitive):
                    with self.assertRaisesRegex(Exception, "source/frame claim"):
                        driver._execute_native_war_step(
                            QUERY_STEP, expected_revision=5,
                            expected_h2743_frame=claim,
                        )
                primitive.assert_not_called()
        with (patch.object(driver, "take_internal_semantic_snapshot", return_value=before),
              patch.object(driver, "_execute_primitive_step") as primitive):
            with self.assertRaisesRegex(Exception, "source/frame claim"):
                driver._execute_native_war_step(QUERY_STEP, expected_revision=5)
        primitive.assert_not_called()
        with (patch.object(driver, "take_internal_semantic_snapshot", return_value=before),
              patch.object(driver, "_execute_primitive_step") as primitive):
            with self.assertRaisesRegex(Exception, "public before-frame revision"):
                driver._execute_native_war_step(
                    QUERY_STEP, expected_revision=4, expected_h2743_frame=claim,
                )
        primitive.assert_not_called()

    def test_service_requires_explicit_claim_before_dispatch(self) -> None:
        service = object.__new__(GameplayBridgeService)
        service.driver = Mock()
        claim = frame_claim_from_snapshot(starting_frame(4))
        with self.assertRaisesRegex(Exception, "explicit before-frame claim"):
            service.execute_step(QUERY_STEP, expected_revision=5)
        with self.assertRaisesRegex(Exception, "explicit before-frame claim"):
            service.execute_step("wait-one-day", expected_revision=5,
                                 expected_h2743_frame=claim)
        service.driver.execute_step.assert_not_called()
        service.driver.query_h2743_preaction_existing_truce_v1.return_value = result(4)
        returned = service.execute_step(
            QUERY_STEP, expected_revision=5, expected_h2743_frame=claim,
        )
        self.assertEqual(returned["snapshot_revision"], 4)
        service.driver.query_h2743_preaction_existing_truce_v1.assert_called_once_with(
            claim, expected_revision=5,
        )


if __name__ == "__main__":
    unittest.main()
