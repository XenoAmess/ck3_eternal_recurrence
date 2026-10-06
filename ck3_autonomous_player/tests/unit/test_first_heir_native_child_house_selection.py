"""Production first-heir planning consumes readable native child-house value."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_family_marriage_formal_consumer import FakeDriver, scene
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import SUBMIT_STEP
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.family_marriage_formal_consumer import (
    plan_family_marriage_private,
    read_family_marriage_ledger,
    submit_family_marriage_private,
)
from xar_autoplayer.m5_observed_opportunity_selector import first_heir_marriage_proposal


def native_scene(*, dynasty_continuity: bool = True) -> dict[str, object]:
    snapshot = {
        **scene(),
        "revision": 8,
        "snapshot_id": "native:7",
        "played_character": {"character_id": 101, "alive": True},
        "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256,
        }},
    }
    if dynasty_continuity:
        snapshot["campaign_goal"] = {"goal_key": "dynasty_continuity"}
    return snapshot


class NativeChildHouseDriver(FakeDriver):
    """Use existing five legal adult candidates and normalized FAMILY returns."""

    allow_private_family_obligations_query = True

    def __init__(self, state_dir: Path):
        super().__init__(state_dir)
        self.allow_private_current_first_heir_relationship_query = True
        self.legality.update(
            exact_ck3_build=CK3_12003.game_version,
            exe_sha256=CK3_12003.executable_sha256,
        )
        self.preview_requests: list[dict[str, object]] = []
        self.preview_observations = {
            candidate_id: self._observation(candidate_id)
            for candidate_id in range(300, 305)
        }

    @staticmethod
    def _observation(candidate_id: int) -> dict[str, object]:
        available = candidate_id != 300
        return {
            "schema_version": 1,
            "kind": "ck3_12002_family_obligations_private_v1",
            "game_version": CK3_12003.game_version,
            "executable_sha256": CK3_12003.executable_sha256,
            "query_status": "available" if available else "partial",
            "frame": {
                "snapshot_revision": 7,
                "date_raw": 53215920,
                "played_character_id": 101,
                "paused": True,
                "map_ready": True,
                "played_character_alive": True,
            },
            "native_child_house_preview": {
                "status": "available" if available else "unavailable",
                "reason": "" if available else
                          "native_child_house_preview_parent_unavailable",
                "subject_character_id": 202,
                "candidate_character_id": candidate_id,
                "requested_matrilineal_option": False,
                "selected_matrilineal_option": False if available else None,
                "effective_matrilineal_if_accepted": False if available else None,
                "complete_can_send": True if available else None,
                "native_selected_parent_character_id": 202 if available else None,
                "house_id": 21 if available else None,
                "dynasty_id": 20 if available else None,
            },
            "alliance_obligations": {
                "status": "not_requested",
                "reason": "",
                "first_character_id": 101,
                "second_character_id": None,
            },
            "betrothal_break_terms": {
                "status": "not_requested",
                "reason": "",
                "actor_character_id": None,
                "subject_character_id": 202,
                "requested_recipient_character_id": None,
            },
            "step": "read-family-obligations-private-12002",
            "accepted": True,
            "private_build": True,
            "read_only": True,
            "advertised": False,
            "snapshot_revision": 7,
            "queried_snapshot_id": "native:7",
            "queried_revision": 8,
            "queried_native_revision": 7,
        }

    def query_family_obligations_private_v1(
        self, *, expected_revision, subject_character_id,
        candidate_character_id, request_matrilineal_option=False,
    ):
        request = {
            "expected_revision": expected_revision,
            "subject_character_id": subject_character_id,
            "candidate_character_id": candidate_character_id,
            "request_matrilineal_option": request_matrilineal_option,
        }
        self.preview_requests.append(request)
        self.calls.append(f"native-preview-{candidate_character_id}")
        return deepcopy(self.preview_observations[candidate_character_id])


class FirstHeirNativeChildHouseSelectionTests(unittest.TestCase):
    def test_production_plan_uses_next_readable_preview_and_preserves_submission_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = NativeChildHouseDriver(Path(temporary))
            baseline = {"plan": {"selected_step": "life-advance"}}

            # The existing adult/age/acceptance order prefers 300 before the
            # dynasty-continuity goal asks for a native offspring preview.
            ordinary = plan_family_marriage_private(
                driver, baseline, native_scene(dynasty_continuity=False))["plan"]
            self.assertEqual(ordinary["family_marriage_choice"]["candidate_character_id"],
                             300)
            self.assertEqual(driver.preview_requests, [])
            driver.calls.clear()

            snapshot = native_scene()
            plan = plan_family_marriage_private(driver, baseline, snapshot)["plan"]
            self.assertEqual(plan["selected_step"], SUBMIT_STEP)
            self.assertEqual(plan["family_marriage_choice"]["candidate_character_id"],
                             301)
            expected_preview = driver.preview_observations[301]
            self.assertEqual(
                plan["family_marriage_choice"]["native_child_house_preview"],
                expected_preview,
            )
            self.assertEqual(driver.preview_requests, [
                {"expected_revision": 8, "subject_character_id": 202,
                 "candidate_character_id": 300, "request_matrilineal_option": False},
                {"expected_revision": 8, "subject_character_id": 202,
                 "candidate_character_id": 301, "request_matrilineal_option": False},
            ])
            self.assertEqual(driver.calls, [
                "relationship", "legality", "projection",
                "native-preview-300", "native-preview-301",
            ])
            self.assertEqual(
                [choice["candidate_character_id"]
                 for choice in plan["family_marriage_valued_choices"]], [301],
            )
            self.assertEqual(
                [row["reason"] for row in plan["family_marriage_native_lineage_previews"]],
                ["native_child_house_preview_parent_unavailable",
                 "native_main_dynasty_opportunity"],
            )
            proposal = first_heir_marriage_proposal(
                frame={"played_character_id": 101,
                       "native_revision": snapshot["native_revision"],
                       "date_raw": snapshot["date_raw"],
                       "episode_run_id": snapshot["episode_run_id"],
                       "snapshot_id": snapshot["snapshot_id"],
                       "revision": snapshot["revision"]},
                plan=plan,
            )
            self.assertEqual(proposal["evidence"]["candidate_character_id"], 301)
            self.assertEqual(proposal["character_ids"], [202, 301, 401])

            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                pending = submit_family_marriage_private(
                    driver, plan=plan, snapshot=snapshot)
            selected_value = pending["selected_value_projection"]
            self.assertEqual(selected_value["native_child_house_preview"], expected_preview)
            self.assertEqual(selected_value["child_dynasty_prediction_status"], "native_preview")
            self.assertEqual(selected_value["predicted_child_dynasty_id"], 20)
            self.assertIn("future_child_identity_and_dynasty",
                          selected_value["unobserved_at_submission"])
            self.assertEqual(
                read_family_marriage_ledger(driver.state_dir)["pending"]
                ["selected_value_projection"], selected_value,
            )
            self.assertEqual(driver.calls[-1], "submit")
            self.assertEqual(len(driver.preview_requests), 2)

    def test_current_partnered_and_resolved_paths_do_not_query_candidate_previews(self):
        for resolved_path in (False, True):
            with self.subTest(resolved=resolved_path):
                with tempfile.TemporaryDirectory() as temporary:
                    driver = NativeChildHouseDriver(Path(temporary))
                    driver.current_first_heir_relationship.update(
                        primary_spouse_character_id=301,
                        spouse_character_ids=[301],
                    )
                    if resolved_path:
                        resolved = {
                            "status": "marriage",
                            "material_result": True,
                            "episode_run_id": "robert-test",
                            "heir_character_id": 202,
                            "candidate_character_id": 301,
                            "post_native_revision": 7,
                            "post_bridge_pid": 55,
                            "post_bridge_creation_date": "created",
                            "source_pending": {
                                "played_character_id": 101,
                                "heir_character_id": 202,
                                "candidate_character_id": 301,
                                "recipient_character_id": 401,
                            },
                            "alliance_result": {
                                "status": "allied",
                                "bridge_pid": 55,
                                "bridge_creation_date": "created",
                            },
                        }
                        ledger = {
                            "schema": "xar.ck3.first-heir-marriage-formal.v1",
                            "pending": None,
                            "resolved": resolved,
                        }
                        (driver.state_dir / "first-heir-marriage-formal-v1.json").write_text(
                            json.dumps(ledger), encoding="utf-8")
                    with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                               return_value=(55, "created")):
                        plan = plan_family_marriage_private(
                            driver, {"plan": {"selected_step": "life-advance"}},
                            native_scene())["plan"]
                    self.assertEqual(plan["selected_step"], "life-advance")
                    if resolved_path:
                        self.assertEqual(plan["family_marriage_result_consumed"]["status"],
                                         "marriage")
                    else:
                        self.assertEqual(plan["family_marriage_status"],
                                         "current_first_heir_already_partnered")
                    self.assertEqual(driver.calls, ["relationship"])
                    self.assertEqual(driver.preview_requests, [])


if __name__ == "__main__":
    unittest.main()
