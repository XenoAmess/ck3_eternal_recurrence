"""Actual failure replay and planned refreshed DTOs; this is an offline regression."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from xar_autoplayer import player_child_default_formal_consumer as consumer
from xar_autoplayer.bridge.player_child_marriage_subject_private_transport import (
    query_player_child_marriage_subject_private_v1,
)
from xar_autoplayer.bridge.player_child_marriage_value_private_transport import (
    query_player_child_marriage_value_private_v1,
)
from xar_autoplayer.bridge.player_child_matrilineal_private_action_v1 import (
    submit_player_child_matrilineal_private_v1,
)


FIXTURE = (Path(__file__).resolve().parents[1] / "fixtures"
           / "robert_guy_child_default_fresh_legality_12003.json")
ROOT_STEP = "query-campaign-root-context-v1"
SUBJECT_STEP = "query-player-child-marriage-subject-v1-private"
VALUE_STEP = "query-player-child-marriage-value-v1-private"
SUBMIT_STEP = "submit-player-child-default-marriage-v1-private"


class NativeEndpointFixture:
    def __init__(self, native_rows, snapshot, plan, failed_packet, failed_response):
        self.native_rows = native_rows
        self.snapshot = snapshot
        self.plan = plan
        self.sequence = plan["child_default_legality"]["query_sequence"]
        self.failed_packet = failed_packet
        self.failed_response = failed_response
        self.root_recheck_seen = False
        self.refreshed_legality_fixture_seen = False
        self.selected_pair = None
        self.sent = []
        self.frames = {}

    def send(self, packet):
        packet = copy.deepcopy(packet)
        self.sent.append(packet)
        step = packet["step"]
        result = None
        error = None
        if step == ROOT_STEP:
            self.root_recheck_seen = True
            self.selected_pair = None
            result = copy.deepcopy(self.native_rows[ROOT_STEP])
        elif step == SUBJECT_STEP:
            assert self.root_recheck_seen
            assert packet["subject_character_id"] == 38988
            assert packet["expected_revision"] == 27
            self.sequence += 1
            self.refreshed_legality_fixture_seen = True
            self.selected_pair = None
            result = copy.deepcopy(self.native_rows[SUBJECT_STEP])
            result["query_sequence"] = self.sequence
        elif step == VALUE_STEP:
            assert self.root_recheck_seen
            if not self.refreshed_legality_fixture_seen:
                assert {key: value for key, value in packet.items() if key != "request_id"} == {
                    key: value for key, value in self.failed_packet.items() if key != "request_id"}
                frame = copy.deepcopy(self.failed_response)
                frame["request_id"] = packet["request_id"]
                self.frames[packet["request_id"]] = frame
                return
            else:
                assert packet["legality_query_sequence"] == self.sequence == 3
                candidate = packet["candidate_character_id"]
                assert candidate in {37909, 37571}
                assert packet["subject_character_id"] == 38988
                assert packet["request_matrilineal_option"] is False
                result = copy.deepcopy(self.native_rows[(VALUE_STEP, candidate)])
                result["legality_query_sequence"] = self.sequence
                self.selected_pair = candidate
        elif step == SUBMIT_STEP:
            assert self.refreshed_legality_fixture_seen
            assert packet["legality_query_sequence"] == self.sequence == 3
            assert packet["subject_character_id"] == 38988
            assert packet["candidate_character_id"] == self.selected_pair == 37571
            row = self.plan["child_default_value"]["row"]
            result = {"step": SUBMIT_STEP, "accepted": True, "private_build": True,
                      "advertised": False, "status": "receipt_pending", "material_result": False,
                      "pre_native_revision": 27, "played_character_id": 29829,
                      "heir_character_id": 38988, "candidate_character_id": 37571,
                      "recipient_character_id": row["recipient_character_id"],
                      "matrilineal_option_selected": False}
        else:
            raise AssertionError("Unexpected fixture endpoint step: " + step)
        frame = {"type": "command_result", "request_id": packet["request_id"],
                 "ok": error is None}
        if error:
            frame["error"] = error
        else:
            frame["result"] = result
        self.frames[packet["request_id"]] = frame

    def wait_for_command_result(self, request_id, timeout_seconds):
        assert timeout_seconds > 0
        return copy.deepcopy(self.frames.pop(request_id))


class _FixtureDriver:
    allow_private_player_child_marriage_subject_query = True
    allow_private_player_child_default_action = True

    def __init__(self, state_dir: Path, snapshot: dict, endpoint: NativeEndpointFixture):
        self.state_dir = state_dir
        self.snapshot = snapshot
        self.endpoint = endpoint
        self.state = endpoint

    def take_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def _execute_campaign_root_context_v1_query(self, *, expected_revision):
        assert expected_revision == self.snapshot["revision"]
        self.endpoint.send({"type": "execute_step", "protocol_version": 1,
                            "request_id": "fixture-root-recheck", "step": ROOT_STEP,
                            "expected_revision": self.snapshot["native_revision"]})
        frame = self.state.wait_for_command_result("fixture-root-recheck", 1.0)
        return {"status": "available", "campaign_root_context": frame["result"]["campaign_root_context"],
                "queried_revision": self.snapshot["revision"],
                "queried_native_revision": self.snapshot["native_revision"],
                "queried_snapshot_id": self.snapshot["snapshot_id"]}

    def query_player_child_marriage_subject_private_v1(self, **kwargs):
        return query_player_child_marriage_subject_private_v1(self, **kwargs)

    def query_player_child_marriage_value_private_v1(self, **kwargs):
        return query_player_child_marriage_value_private_v1(self, **kwargs)

    def submit_player_child_default_private_v1(self, **kwargs):
        return submit_player_child_matrilineal_private_v1(self, default_route=True, **kwargs)


class PlayerChildDefaultFreshLegalityTest(unittest.TestCase):
    def test_root_recheck_refreshes_legality_before_value_and_submit(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8-sig"))
        snapshot, plan = fixture["snapshot"], fixture["plan"]
        native_rows = {ROOT_STEP: fixture["root_result"],
                       SUBJECT_STEP: fixture["subject_result"]}
        native_rows.update({(VALUE_STEP, int(candidate)): result
                            for candidate, result in fixture["value_results_by_candidate"].items()})
        endpoint = NativeEndpointFixture(native_rows, snapshot, plan,
                                         fixture["failed_packet"], fixture["failed_response"])
        self.assertEqual(plan["child_default_legality"]["query_sequence"], 2)
        self.assertEqual(plan["child_default_observation"]["attempted_candidate_ids"], [37909])
        with TemporaryDirectory(prefix="ck3-child-fresh-legality-") as temporary:
            driver = _FixtureDriver(Path(temporary), snapshot, endpoint)
            consumer._write(driver.state_dir, {"schema": consumer.LEDGER_SCHEMA,
                                               "pending": None,
                                               "resolved": copy.deepcopy(plan["child_default_retry_source"])})
            with patch.object(consumer, "bridge_process_identity",
                              return_value=(70968, "offline-fixture-only")):
                result = consumer.submit_child_default_private(
                    driver, plan=copy.deepcopy(plan), snapshot=copy.deepcopy(snapshot))
            submissions = [packet for packet in endpoint.sent if packet["step"] == SUBMIT_STEP]
            durable = consumer.read_child_default_ledger(driver.state_dir)
            self.assertEqual(result["status"], "receipt_pending")
            self.assertIs(result["material_result"], False)
            self.assertEqual(len(submissions), 1)
            self.assertEqual(submissions[0]["candidate_character_id"], 37571)
            self.assertEqual(submissions[0]["legality_query_sequence"], 3)
            self.assertEqual([packet["step"] for packet in endpoint.sent],
                             [ROOT_STEP, SUBJECT_STEP, VALUE_STEP, VALUE_STEP, VALUE_STEP, SUBMIT_STEP])
            self.assertEqual([packet["candidate_character_id"] for packet in endpoint.sent
                              if packet["step"] == VALUE_STEP], [37909, 37571, 37571])
            self.assertEqual(durable["pending"], result)
            self.assertEqual(result["selected_value_projection"], plan["child_default_value"]["row"])
            self.assertEqual(result["prior_attempted_candidate_ids"], [37909])
            self.assertEqual(result["prior_rejected_candidate_ids"], [])
            self.assertEqual(durable["resolved"], plan["child_default_retry_source"])


if __name__ == "__main__":
    unittest.main()
