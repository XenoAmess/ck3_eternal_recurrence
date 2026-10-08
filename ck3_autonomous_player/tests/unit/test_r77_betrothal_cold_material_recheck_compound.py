"""One R77 production compound using cached family replies; SOURCE_NOTRUN."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_current_first_heir_betrothal_formal_consumer import Driver, scene
from xar_autoplayer.bridge.current_first_heir_betrothal_private_action_v1 import SUBMIT_STEP
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    RESULT_STEP, SUBMIT_STEP as MARRIAGE_SUBMIT_STEP,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_contract import query_war_termination_options_step
from xar_autoplayer.family_marriage_formal_consumer import read_family_marriage_ledger


UTC_TOKEN = "20261008054004.201294+000"
WMI_TOKEN = "20261008134004.201294+480"
CHANGED_INSTANT = "20261008134004.201295+480"


class RecordedR77Driver(Driver):
    """Endpoint/cache fixture; inherited cold method runs production transport."""

    def __init__(self, state_dir, recorded):
        super().__init__(state_dir)
        self.allow_private_family_marriage_formal_trial = True
        self.backend_id = CK3_12004.backend_id("headless")
        self.pid = 99872
        self.creation_token = UTC_TOKEN
        source = recorded["plan"]["source_frame"]
        self.frame = scene(source["native_revision"], source["date_raw"])
        self.frame.update(
            snapshot_id=source["snapshot_id"], revision=source["revision"],
            episode_run_id=source["episode_run_id"],
            active_wars=[{"war_id": recorded["plan"]["war_id"]}],
            diagnostics={"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }},
        )
        self.current_relation = deepcopy(recorded["plan"]["current_betrothal_relationship"])
        self.marriage_reply = deepcopy(recorded["normalized_marriage_result"])
        self.normal_step = query_war_termination_options_step(recorded["plan"]["war_id"])
        self.root_reads = []

    def capabilities(self):
        return {"backend_id": self.backend_id,
                "action_steps": ["life-advance", self.normal_step],
                "bridge_capabilities": []}

    def query_current_first_heir_relationship_private_v1(
        self, *, expected_native_revision, campaign_root_result=None,
    ):
        assert expected_native_revision == self.frame["native_revision"]
        self.reads += 1
        return deepcopy(self.current_relation)

    def _execute_campaign_root_context_v1_query(self, *, expected_revision):
        assert expected_revision == self.frame["revision"]
        self.root_reads.append(expected_revision)
        # Existing helper boundary, with the actual cached current heir ID.
        return {"status": "available", "held_title_partition": [{
            "primary": True,
            "first_heir_character_id": self.current_relation["heir_character_id"],
        }]}

    def send(self, request):
        assert request["step"] in {RESULT_STEP, self.normal_step}
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        request = self.requests[-1]
        assert request["request_id"] == request_id
        assert timeout > 0
        if request["step"] == RESULT_STEP:
            assert request["cold_recovery"] == 1
            assert request["fulfill_existing_betrothal"] is True
            assert request["matrilineal_option_selected"] is False
            return {"ok": True, "request_id": request_id,
                    "result": deepcopy(self.marriage_reply)}
        # Synthetic receipt only: this compound claims query dispatch, not
        # any newly observed war terms or material war outcome.
        return {"ok": True, "request_id": request_id, "result": {
            "step": self.normal_step, "accepted": True, "read_only": True,
        }}

    def execute_step(self, step, *, expected_revision=None):
        assert step == self.normal_step
        assert expected_revision == self.frame["revision"]
        request_id = f"r77-normal-query-{len(self.requests)}"
        self.send({"type": "execute_step", "protocol_version": 1,
                   "request_id": request_id, "step": step,
                   "expected_revision": self.frame["native_revision"]})
        return self.wait_for_command_result(request_id, 30.0)["result"]


class R77BetrothalColdMaterialRecheckCompoundTest(unittest.TestCase):
    def test_actual_cold_result_then_equivalent_identity_preserves_war_query(self):
        summary_path = Path(os.environ["XAR_FAMILY_COLD_RECHECK_SUMMARY"])
        output_path = Path(os.environ["XAR_FAMILY_COLD_RECHECK_COMPOUND_OUTPUT"])
        temp_root = Path(os.environ["XAR_TEST_TEMP_ROOT"])
        self.assertEqual(temp_root.drive.upper(), "Z:")
        self.assertEqual(output_path.drive.upper(), "Z:")
        summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
        recorded = next(row for row in summary["scenes"] if row["scene"] == "003")
        companion = next(row for row in summary["scenes"] if row["scene"] == "007")
        self.assertEqual(recorded["normalized_marriage_result"],
                         companion["normalized_marriage_result"])
        self.assertEqual(recorded["plan"]["current_betrothal_relationship"],
                         companion["plan"]["current_betrothal_relationship"])
        native_reply = recorded["normalized_marriage_result"]
        self.assertEqual(native_reply["exact_ck3_build"], CK3_12004.game_version)
        self.assertEqual(native_reply["exe_sha256"], CK3_12004.executable_sha256)
        self.assertEqual((native_reply["status"], native_reply["material_result"],
                          native_reply["cold_recovery"], native_reply["pre_native_revision"],
                          native_reply["post_native_revision"]),
                         ("marriage", True, True, 0, 2))
        source_pending = deepcopy(recorded["plan"]["current_betrothal_pending"])
        self.assertEqual(source_pending["source_bridge_pid"], 24044)
        self.assertEqual(source_pending["played_character_id"], 29829)
        self.assertEqual(source_pending["exact_ck3_build"], "1.20.0.3")

        with tempfile.TemporaryDirectory(dir=temp_root) as temporary:
            state_dir = Path(temporary)
            ledger_path = state_dir / "first-heir-marriage-formal-v1.json"
            # Synthetic historical resolution seed in the existing durable
            # schema. Native pair and pending inputs are copied from cache.
            initial_ledger = read_family_marriage_ledger(state_dir)
            initial_ledger["resolved"] = {
                "status": "marriage", "material_result": True,
                "episode_run_id": source_pending["episode_run_id"],
                "heir_character_id": source_pending["heir_character_id"],
                "candidate_character_id": source_pending["candidate_character_id"],
                "post_native_revision": native_reply["post_native_revision"],
                "source_pending": deepcopy(source_pending),
                "post_bridge_pid": source_pending["source_bridge_pid"],
                "post_bridge_creation_date": source_pending["source_bridge_creation_date"],
                "cold_recovery_verified": False,
                "fulfill_existing_betrothal": True,
            }
            ledger_path.write_text(json.dumps(initial_ledger), encoding="utf-8")
            driver = RecordedR77Driver(state_dir, recorded)
            service = GameplayBridgeService(driver)
            identity_source = lambda current: (current.pid, current.creation_token)
            stages = []
            with patch("xar_autoplayer.current_first_heir_betrothal_formal_consumer._identity",
                       side_effect=identity_source), patch(
                    "xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                    side_effect=identity_source):
                cold = service.auto_turn()
                self.assertEqual(cold["status"], "executed")
                self.assertEqual(cold["selected_step"], RESULT_STEP)
                self.assertEqual(cold["plan"]["phase"],
                                 "current_first_heir_betrothal_cold_material_recheck")
                self.assertIs(cold["plan"]["current_betrothal_material_recheck"], True)
                self.assertEqual(cold["result"], native_reply)
                self.assertEqual(cold["plan"]["current_betrothal_relationship"],
                                 recorded["plan"]["current_betrothal_relationship"])
                self.assertEqual(driver.root_reads, [3])
                self.assertEqual(len(driver.requests), 1)
                request = driver.requests[0]
                self.assertEqual(request["expected_revision"], 2)
                self.assertEqual((request["heir_character_id"], request["candidate_character_id"],
                                  request["recipient_character_id"], request["source_date_raw"]),
                                 (38822, 38718, 32897, source_pending["source_date_raw"]))
                verified_ledger = read_family_marriage_ledger(state_dir)
                self.assertIsNone(verified_ledger["pending"])
                self.assertIs(verified_ledger["resolved"]["cold_recovery_verified"], True)
                self.assertEqual((verified_ledger["resolved"]["post_bridge_pid"],
                                  verified_ledger["resolved"]["post_bridge_creation_date"]),
                                 (99872, UTC_TOKEN))
                self.assertEqual(verified_ledger["resolved"]["source_pending"], source_pending)
                stages.append({"case": "historical_pid_cold_read", "outcome": cold,
                               "ledger": deepcopy(verified_ledger)})

                # Same Service, same paused frame, actual WMI spelling of the
                # same creation instant persisted above in UTC spelling.
                driver.creation_token = WMI_TOKEN
                following = service.auto_turn()
                self.assertEqual(following["status"], "executed")
                self.assertEqual(following["selected_step"], driver.normal_step)
                self.assertEqual(following["plan"]["phase"], "native_war_termination_query")
                self.assertEqual(following["plan"]["current_betrothal_status"], "marriage")
                self.assertEqual(following["plan"]["current_betrothal_result_consumed"],
                                 verified_ledger["resolved"])
                self.assertEqual(driver.reads, 2)
                self.assertEqual(driver.root_reads, [3])
                self.assertEqual([row["step"] for row in driver.requests],
                                 [RESULT_STEP, driver.normal_step])
                self.assertEqual(read_family_marriage_ledger(state_dir), verified_ledger)
                stages.append({"case": "equivalent_current_identity_normal_war_query",
                               "outcome": following, "ledger": deepcopy(verified_ledger)})

                for label, pid, creation in (
                    ("changed_pid", 99873, WMI_TOKEN),
                    ("changed_creation_microsecond", 99872, CHANGED_INSTANT),
                ):
                    # Fresh receivers avoid the legitimate same-date family
                    # memo populated by the preceding normal war query.
                    ledger_path.write_text(json.dumps(verified_ledger), encoding="utf-8")
                    changed = RecordedR77Driver(state_dir, recorded)
                    changed.pid, changed.creation_token = pid, creation
                    outcome = GameplayBridgeService(changed).auto_turn()
                    self.assertEqual(outcome["status"], "executed")
                    self.assertEqual(outcome["selected_step"], RESULT_STEP)
                    self.assertEqual(outcome["plan"]["phase"],
                                     "current_first_heir_betrothal_cold_material_recheck")
                    self.assertEqual(outcome["result"], native_reply)
                    self.assertEqual(changed.root_reads, [3])
                    self.assertEqual([row["step"] for row in changed.requests], [RESULT_STEP])
                    updated = read_family_marriage_ledger(state_dir)
                    self.assertIsNone(updated["pending"])
                    self.assertIs(updated["resolved"]["cold_recovery_verified"], True)
                    self.assertEqual((updated["resolved"]["post_bridge_pid"],
                                      updated["resolved"]["post_bridge_creation_date"]),
                                     (pid, creation))
                    self.assertEqual(updated["resolved"]["source_pending"], source_pending)
                    stages.append({"case": label, "identity": [pid, creation],
                                   "outcome": outcome, "ledger": updated})

                self.assertFalse(any(row["step"] in {SUBMIT_STEP, MARRIAGE_SUBMIT_STEP}
                                     for row in driver.requests))
                self.assertEqual(driver.marriage_reply, recorded["normalized_marriage_result"])
                self.assertEqual(driver.current_relation,
                                 recorded["plan"]["current_betrothal_relationship"])

            # Emitted only after every production-path assertion above passes.
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps({
                "schema": "xar.ck3.r77-cold-material-recheck-compound.v1",
                "qualification": "offline_production_compound",
                "source_kind": "cached_actual_family_reply_with_synthetic_endpoint",
                "cached_scenes": ["003", "007"],
                "exact_ck3_build": CK3_12004.game_version,
                "exe_sha256": CK3_12004.executable_sha256,
                "family_requests": driver.requests, "stages": stages,
                "new_game_or_sdk_calls": 0,
            }, indent=2), encoding="utf-8")
            print("R77_COLD_MATERIAL_RECHECK_COMPOUND=" + str(output_path))


if __name__ == "__main__":
    unittest.main()
