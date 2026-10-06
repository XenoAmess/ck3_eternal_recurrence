"""Exercise the production service dispatch after a completed fulfillment.

Synthetic relation values represent native normalized observations. No spouse
death, successor, CK3 action or current campaign opportunity is claimed.
"""

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

from test_current_first_heir_betrothal_formal_consumer import relation
from test_first_heir_native_child_house_selection import (
    NativeChildHouseDriver, native_scene,
)
from xar_autoplayer.bridge.current_first_heir_betrothal_private_action_v1 import (
    SUBMIT_STEP as FULFILL_STEP,
)
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    RESULT_STEP, SUBMIT_STEP as MARRIAGE_STEP,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12003


class FulfillmentRelationshipDriver(NativeChildHouseDriver):
    allow_private_current_first_heir_betrothal_fulfillment = True

    def __init__(self, state_dir: Path):
        super().__init__(state_dir)
        self.current_first_heir_relationship.update(
            exact_ck3_build=CK3_12003.game_version,
            exe_sha256=CK3_12003.executable_sha256,
        )

    def ready_pair(self, heir: int, candidate: int):
        value = deepcopy(relation()["betrothal_actionability"])
        value.update(actor_character_id=101, heir_character_id=heir,
                     partner_character_id=candidate, recipient_character_id=401)
        self.current_first_heir_relationship.update(
            heir_character_id=heir, betrothed_character_id=candidate,
            primary_spouse_character_id=None, spouse_character_ids=[],
            betrothal_actionability=value,
        )


def completed_ledger(*, status: str = "marriage", cold: bool = False):
    return {
        "schema": "xar.ck3.first-heir-marriage-formal.v1",
        "pending": None,
        "resolved": {
            "status": status, "material_result": status == "marriage",
            "episode_run_id": "robert-test",
            "played_character_id": 101,
            "heir_character_id": 202, "candidate_character_id": 300,
            "post_native_revision": 7,
            "post_bridge_pid": 54 if cold else 55,
            "post_bridge_creation_date": "previous" if cold else "created",
            "fulfill_existing_betrothal": True,
            "source_pending": {
                "episode_run_id": "robert-test",
                "played_character_id": 101,
                "heir_character_id": 202, "candidate_character_id": 300,
                "recipient_character_id": 400,
                "fulfill_existing_betrothal": True,
            },
        },
    }


class FirstHeirFulfillmentRelationshipTransitionTests(unittest.TestCase):
    def test_service_dispatch_tracks_current_heir_and_pair_after_fulfillment(self):
        cases = (
            "new_heir_betrothal", "ended_pair", "unavailable",
            "same_marriage", "same_marriage_cold", "same_refused_betrothal",
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                driver = FulfillmentRelationshipDriver(Path(temporary))
                ledger = completed_ledger(
                    status="refused" if case == "same_refused_betrothal" else "marriage",
                    cold=case == "same_marriage_cold",
                )
                path = driver.state_dir / "first-heir-marriage-formal-v1.json"
                path.write_text(json.dumps(ledger), encoding="utf-8")
                historical_bytes = path.read_bytes()
                if case == "new_heir_betrothal":
                    driver.ready_pair(203, 301)
                elif case == "same_refused_betrothal":
                    driver.ready_pair(202, 300)
                elif case in {"same_marriage", "same_marriage_cold"}:
                    driver.current_first_heir_relationship.update(
                        primary_spouse_character_id=300, spouse_character_ids=[300])
                elif case == "unavailable":
                    driver.current_first_heir_relationship.update(
                        status="unavailable", bilateral_verified=False,
                        spouse_character_ids=None,
                        unavailable_reason="native_relationship_unavailable")

                service = GameplayBridgeService.__new__(GameplayBridgeService)
                service.driver = driver
                with patch(
                    "xar_autoplayer.current_first_heir_betrothal_formal_consumer._identity",
                    return_value=(55, "created"),
                ), patch(
                    "xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                    return_value=(55, "created"),
                ):
                    plan = service._plan_private_family_opportunity_v1(
                        {"plan": {"selected_step": "life-advance"}}, native_scene())["plan"]

                if case == "new_heir_betrothal":
                    self.assertEqual(plan["selected_step"], FULFILL_STEP)
                    self.assertEqual(plan["current_betrothal_choice"]["heir_character_id"], 203)
                    self.assertEqual(plan["current_betrothal_choice"]["candidate_character_id"], 301)
                    self.assertNotIn("current_betrothal_result_consumed", plan)
                    self.assertEqual(driver.calls, ["relationship"])
                elif case == "ended_pair":
                    self.assertEqual(plan["selected_step"], MARRIAGE_STEP)
                    self.assertEqual(plan["family_marriage_choice"]["candidate_character_id"], 301)
                    self.assertNotIn("current_betrothal_fulfillment", plan)
                    self.assertIn("legality", driver.calls)
                    self.assertIn("projection", driver.calls)
                elif case == "unavailable":
                    self.assertEqual(plan["selected_step"], "life-advance")
                    self.assertEqual(plan["current_betrothal_status"],
                                     "current_first_heir_relation_unavailable")
                    self.assertEqual(driver.calls, ["relationship"])
                    self.assertEqual(driver.preview_requests, [])
                elif case == "same_marriage_cold":
                    self.assertEqual(plan["selected_step"], RESULT_STEP)
                    self.assertIs(plan["current_betrothal_material_recheck"], True)
                    self.assertEqual(plan["current_betrothal_pending"],
                                     ledger["resolved"]["source_pending"])
                    self.assertEqual(driver.calls, ["relationship"])
                else:
                    self.assertEqual(plan["selected_step"], "life-advance")
                    self.assertEqual(plan["current_betrothal_result_consumed"], ledger["resolved"])
                    self.assertEqual(driver.calls, ["relationship"])
                self.assertEqual(path.read_bytes(), historical_bytes)
                self.assertNotIn("result", driver.calls)
                self.assertNotIn("submit", driver.calls)


if __name__ == "__main__":
    unittest.main()
