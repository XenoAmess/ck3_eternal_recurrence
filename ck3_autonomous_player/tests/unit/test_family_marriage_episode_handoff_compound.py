"""New whole software path; consumes saved qualified household wire, never game."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from xar_autoplayer.bridge.campaign_root_context_contract import QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import STEP
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.succession_transition_contract import CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.family_marriage_formal_consumer import _write, read_family_marriage_ledger
from test_succession_transition_contract import (
    _FakeEndpoint, _bundle, _hello, _native_snapshot, _ordinary_binding, _row,
)


class FamilyMarriageEpisodeHandoffCompoundTests(unittest.TestCase):
    def test_matched_successor_archives_predecessor_and_observes_current_household(self) -> None:
        """Actual driver M3 -> local family handoff -> strict query -> Service plan."""
        wire_dir = os.environ["XAR_CURRENT_HEIR_REPRODUCTIVE_NATIVE_WIRE_DIR"]
        packet = json.loads((Path(wire_dir) / "married-pair.json").read_text(encoding="utf-8"))
        actor, heir, spouse = 0x03000001, 0x03000002, 0x03000003

        class Endpoint(_FakeEndpoint):
            def __init__(self) -> None:
                super().__init__()
                self.requests = []
                self.current_packet = None

            def send(self, request) -> None:
                if request.get("type") == "ping":
                    return super().send(request)
                self.requests.append(deepcopy(request))
                if request.get("step") != STEP or self.current_packet is None:
                    raise AssertionError("compound permits only current-household query envelopes")
                response = deepcopy(self.current_packet)
                response["request_id"] = request["request_id"]
                self.publish(response)

        def succession_bundle(frame, played, next_heir):
            return _bundle(character_id=played, snapshot_id=frame["snapshot_id"],
                revision=frame["revision"], native_revision=frame["native_revision"],
                date_raw=frame["date_raw"], title_rows=[_row(10, next_heir, primary=True),
                    _row(11, next_heir, primary=False)], primary_heir=next_heir)

        with tempfile.TemporaryDirectory(prefix="xar-family-episode-compound-") as directory:
            state_dir = Path(directory)
            endpoint = Endpoint()
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                state_dir=state_dir, succession_lifecycle_binding=_ordinary_binding())
            self.addCleanup(driver.close)
            endpoint.publish({**_hello(), "pid": os.getpid(), "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256})
            endpoint.publish(_native_snapshot(20, character_id=100, date_raw=53_180_000))
            before = driver.take_snapshot()
            old_episode = before["episode_run_id"]
            old_pending = {"episode_run_id": old_episode, "played_character_id": 100,
                "heir_character_id": actor, "candidate_character_id": 300,
                "status": "receipt_pending", "submission_state": "receipt_pending",
                "fulfill_existing_betrothal": True, "native_revision": 20}
            old_resolved = {"episode_run_id": old_episode, "played_character_id": 100,
                "heir_character_id": actor, "candidate_character_id": 300,
                "status": "betrothal", "material_result": True,
                "source_pending": {"episode_run_id": old_episode,
                    "played_character_id": 100, "fulfill_existing_betrothal": True}}
            earlier_history = [{"source_episode_run_id": "earlier-fixture-life",
                                "resolved": {"status": "marriage", "material_result": True}}]
            _write(state_dir, {"schema": "xar.ck3.first-heir-marriage-formal.v1",
                "pending": old_pending, "resolved": old_resolved,
                "episode_history": earlier_history})
            driver._arrange_marriage_choices = [{"choice_id": "old-choice-fixture"}]
            service = GameplayBridgeService(driver)
            root_capabilities = {"action_steps": [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP],
                                 "bridge_capabilities": []}
            with mock.patch.object(service, "query_turn_bundle_v1",
                    return_value=succession_bundle(before, 100, actor)), mock.patch.object(
                    service, "capabilities", return_value=root_capabilities):
                service.plan_turn()
            endpoint.publish(_native_snapshot(24, character_id=actor, date_raw=53_180_720))
            transition = driver.take_snapshot()
            with mock.patch.object(service, "query_turn_bundle_v1",
                    return_value=succession_bundle(transition, actor, heir)), mock.patch.object(
                    service, "capabilities", return_value=root_capabilities):
                service.plan_turn()
            turn = service.auto_turn()
            self.assertEqual(turn["plan"]["selected_step"], CONTINUE_AS_RECONCILED_SUCCESSOR_STEP)
            self.assertFalse(turn["result"]["ck3_command_submitted"])
            self.assertEqual(endpoint.requests, [])
            continued = driver.take_snapshot()
            self.assertEqual(continued["episode_character_id"], actor)
            self.assertNotEqual(continued["episode_run_id"], old_episode)
            self.assertEqual(driver._arrange_marriage_choices, [])
            self.assertEqual(continued["campaign_goal"]["progress"]["reconciled_successions"], 1)
            handoff = turn["result"]["family_marriage_episode_handoff"]
            self.assertEqual(handoff["status"], "predecessor_records_archived")
            ledger = read_family_marriage_ledger(state_dir)
            self.assertIsNone(ledger["pending"])
            self.assertIsNone(ledger["resolved"])
            self.assertEqual(ledger["episode_history"][0], earlier_history[0])
            archived = ledger["episode_history"][-1]
            self.assertEqual(archived["pending"], old_pending)
            self.assertEqual(archived["resolved"], old_resolved)

            current_packet = deepcopy(packet)
            wire = current_packet["result"]
            wire["native_revision"] = continued["native_revision"]
            for key in ("current_first_heir_descendants_v1", "current_first_heir_reproductive_inputs_v1"):
                wire[key]["native_revision"] = continued["native_revision"]
                wire[key]["date_raw"] = continued["date_raw"]
            endpoint.current_packet = current_packet
            driver.allow_private_current_first_heir_relationship_query = True
            driver.allow_private_current_first_heir_betrothal_fulfillment = True
            driver.allow_private_family_marriage_formal_trial = True
            current_root = {"status": "available", "query_sequence": 11,
                "held_title_partition": [{"primary": True, "first_heir_character_id": heir}]}
            planned = {"snapshot_id": continued["snapshot_id"], "revision": continued["revision"],
                       "plan": {"selected_step": "life-advance"}}
            with mock.patch.object(driver, "_execute_campaign_root_context_v1_query",
                    return_value=current_root), mock.patch.object(driver,
                    "query_observed_first_heir_marriage_legality_v1") as legality:
                result = service._plan_private_family_opportunity_v1(planned, continued)
                legality.assert_not_called()
            self.assertEqual(result["plan"]["selected_step"], "life-advance")
            relation = result["plan"]["family_marriage_current_relationship"]
            self.assertEqual(relation["heir_character_id"], heir)
            self.assertEqual(relation["primary_spouse_character_id"], spouse)
            self.assertEqual(relation["current_first_heir_reproductive_inputs_v1"],
                             wire["current_first_heir_reproductive_inputs_v1"])
            self.assertEqual(relation["current_first_heir_descendants_v1"],
                             wire["current_first_heir_descendants_v1"])
            self.assertTrue(endpoint.requests)
            self.assertTrue(all(request["step"] == STEP for request in endpoint.requests))
            self.assertEqual(read_family_marriage_ledger(state_dir), ledger)


if __name__ == "__main__":
    unittest.main()
