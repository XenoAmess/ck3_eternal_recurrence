from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge import war31_one_shot_surrender as gate_module
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.mcp_server import parser as mcp_parser
from xar_autoplayer.cli import parser as player_parser
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot, _war


def _war31_snapshot() -> dict[str, object]:
    return {
        "paused": True,
        "map_ready": True,
        "episode_run_id": gate_module.EPISODE,
        "date_raw": gate_module.DATE_RAW,
        "played_character": {"character_id": gate_module.CHARACTER_ID},
        "snapshot_id": "native:3",
        "revision": 4,
        "native_revision": 3,
        "diagnostics": {"connection_generation": 1},
        "active_wars": [{
            "war_id": gate_module.WAR_ID,
            "player_side": "defender",
            "player_is_primary_war_leader": True,
            "primary_opponent_character_id": gate_module.OPPONENT_ID,
            "targeted_title_ids": [2128],
            "player_relative_war_score": -15,
        }],
        "war_termination_options": [{
            "war_id": gate_module.WAR_ID,
            "query_sequence": 1,
            "queried_snapshot_id": "native:3",
            "queried_revision": 4,
            "queried_native_revision": 3,
            "queried_connection_generation": 1,
            "episode_run_id": gate_module.EPISODE,
            "player_side": "defender",
            "player_is_primary_war_leader": True,
            "player_relative_war_score": -15,
            "war_duration_days": 1045,
            "absolute_war_scores_observable": True,
            "attacker_war_score": 15,
            "defender_war_score": -15,
            "war_score_breakdown": {
                "battles": 0,
                "imprisonment": 0,
                "occupation": 39,
                "ticking": -24,
            },
            "active_casus_belli_present": True,
            "active_casus_belli_identity": {
                "database_index": 17,
                "canonical_key": "individual_county_de_jure_cb",
            },
            "options": {"surrender": {
                "outcome": "attacker_victory",
                "hostage_variant": "none",
                "context_constructed": True,
                "native_validator_passed": True,
                "available": True,
                "auto_accept_observable": True,
                "auto_accept": True,
                "recipient_response": {
                    "status": "available",
                    "decision_status_raw": 0,
                    "would_accept_now": True,
                },
            }},
        }],
    }


class War31OneShotGateTests(unittest.TestCase):
    def test_explicit_cli_routes_exist_and_default_remains_closed(self) -> None:
        supervisor = player_parser().parse_args([
            "native-session", "--cold-start-checkpoint", "--xar-enabled", "xar_off",
        ])
        self.assertEqual(supervisor.xar_enabled, "xar_off")
        self.assertTrue(supervisor.cold_start_checkpoint)
        mcp = mcp_parser().parse_args([
            "--driver", "native-headless",
            "--war31-one-shot-authorization-receipt", "receipt.json",
            "--war31-one-shot-source-checkpoint", "xar_checkpoint.ck3",
            "--war31-one-shot-source-driver", "driver-state.json",
            "--war31-one-shot-submission-fence", "fence.json",
        ])
        self.assertEqual(mcp.war31_one_shot_authorization_receipt, "receipt.json")
        self.assertIsNone(mcp_parser().parse_args([]).war31_one_shot_authorization_receipt)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkpoint = self.root / "xar_checkpoint.ck3"
        self.driver = self.root / "driver-state.json"
        self.receipt = self.root / "authorization.json"
        self.fence = self.root / "war31-one-shot-submission-reservation.json"
        self.checkpoint.write_bytes(b"exact source save test fixture")
        self.driver.write_bytes(b"exact source driver test fixture")
        self.checkpoint_hash = hashlib.sha256(self.checkpoint.read_bytes()).hexdigest().upper()
        self.driver_hash = hashlib.sha256(self.driver.read_bytes()).hexdigest().upper()
        self.checkpoint_patch = mock.patch.object(gate_module, "CHECKPOINT_SHA256", self.checkpoint_hash)
        self.driver_patch = mock.patch.object(gate_module, "DRIVER_SHA256", self.driver_hash)
        self.checkpoint_patch.start()
        self.driver_patch.start()
        self.addCleanup(self.checkpoint_patch.stop)
        self.addCleanup(self.driver_patch.stop)
        self.payload = {
            "schema": "xar.ck3.war31-one-shot-user-authorization/v1",
            "request_id": gate_module.REQUEST_ID,
            "action_step": gate_module.STEP,
            "source_checkpoint_sha256": self.checkpoint_hash,
            "source_driver_sha256": self.driver_hash,
            "episode_run_id": gate_module.EPISODE,
            "date_raw": gate_module.DATE_RAW,
            "authorization_text": gate_module.AUTHORIZATION_TEXT,
            "scope": "one matching checkpoint surrender action only",
        }
        self._write_receipt()

    def _write_receipt(self) -> None:
        self.receipt.write_text(json.dumps(self.payload, ensure_ascii=False), encoding="utf-8")

    def _gate(self) -> gate_module.War31OneShotSurrenderGate:
        return gate_module.War31OneShotSurrenderGate(
            authorization_receipt=self.receipt,
            source_checkpoint=self.checkpoint,
            source_driver=self.driver,
            submission_fence=self.fence,
        )

    def test_exact_source_receipt_same_frame_and_durable_one_shot(self) -> None:
        gate = self._gate()
        snapshot = _war31_snapshot()
        self.assertEqual(gate.readiness(snapshot)[0:2], (True, "ready"))
        marker = gate.reserve(snapshot, query_sequence=1)
        self.assertEqual(marker["status"], "reserved_before_native_dispatch")
        self.assertEqual(marker["source_checkpoint_sha256"], self.checkpoint_hash)
        self.assertEqual(gate.readiness(snapshot)[1], "one_shot_submission_fence_exists")
        with self.assertRaisesRegex(ValueError, "fence already exists"):
            self._gate()

    def test_mismatched_source_or_receipt_fails_closed(self) -> None:
        self.payload["action_step"] = "surrender-war-16777232"
        self._write_receipt()
        with self.assertRaisesRegex(ValueError, "receipt does not match"):
            self._gate()
        self.payload["action_step"] = gate_module.STEP
        self._write_receipt()
        self.driver.write_bytes(b"wrong source driver")
        with self.assertRaisesRegex(ValueError, "driver SHA-256 mismatch"):
            self._gate()

    def test_defender_query_must_be_fresh_legal_and_accepting(self) -> None:
        gate = self._gate()
        snapshot = _war31_snapshot()
        changes = (
            ("date_raw", 53215921),
            ("episode_run_id", "wrong"),
            ("paused", False),
        )
        for field, value in changes:
            changed = copy.deepcopy(snapshot)
            changed[field] = value
            self.assertFalse(gate.readiness(changed)[0], field)
        changed = copy.deepcopy(snapshot)
        changed["war_termination_options"][0]["queried_native_revision"] = 2
        self.assertEqual(gate.readiness(changed)[1], "termination_query_not_same_frame")
        changed = copy.deepcopy(snapshot)
        changed["war_termination_options"][0]["options"]["surrender"]["outcome"] = "attacker_defeat"
        self.assertFalse(gate.readiness(changed)[0])
        changed = copy.deepcopy(snapshot)
        changed["war_termination_options"][0]["options"]["surrender"]["recipient_response"]["would_accept_now"] = False
        self.assertFalse(gate.readiness(changed)[0])
        changed = copy.deepcopy(snapshot)
        changed["active_wars"][0]["targeted_title_ids"] = [2129]
        self.assertEqual(gate.readiness(changed)[1], "war_identity_mismatch")

    def test_typed_driver_uses_defender_outcome_and_sends_only_once(self) -> None:
        gate = self._gate()
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name,
            endpoint=endpoint,
            command_timeout_seconds=0.1,
            war31_one_shot_surrender_gate=gate,
        )
        endpoint.publish(_hello(
            "game.state.snapshot",
            "game.command.query-war-termination-options-N",
            "game.command.surrender-war-N",
        ))
        driver._episode_character_id = gate_module.CHARACTER_ID
        driver._episode_run_id = gate_module.EPISODE
        war = _war(gate_module.WAR_ID, score=-15, targeted_title_ids=[2128])
        war["player_side"] = "defender"
        war["primary_opponent_character_id"] = gate_module.OPPONENT_ID
        endpoint.publish(_snapshot(
            3,
            date_raw=gate_module.DATE_RAW,
            played_character={"character_id": gate_module.CHARACTER_ID, "alive": True},
            active_wars=[war],
        ))
        freeze = json.loads((
            ROOT.parent / "docs" / "autonomous-agent-progress" / "coordination"
            / "war-requests" / "evidence"
            / "WAR-INPUT-R0221-WAR31-20260927.termination-options.json"
        ).read_text(encoding="utf-8"))
        submissions = []

        def answer(frame: dict[str, object]) -> None:
            if frame.get("type") != "execute_step":
                return
            step = frame["step"]
            if step == gate_module.STEP:
                submissions.append(step)
                result = {"step": step, "accepted": True, "status": "submitted"}
            else:
                self.assertEqual(step, "query-war-termination-options-16777231")
                result = {
                    "step": step,
                    "accepted": True,
                    "status": "available",
                    "query_sequence": 1,
                    "war_termination_options": freeze["war_termination_options"],
                }
            endpoint.publish({
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": result,
            })

        endpoint.send_hook = answer
        self.assertNotIn(gate_module.STEP, driver.capabilities()["action_steps"])
        driver.execute_step("query-war-termination-options-16777231")
        self.assertIn(gate_module.STEP, driver.capabilities()["action_steps"])
        result = driver.execute_step(gate_module.STEP)
        self.assertEqual(result["war_termination_result"]["outcome"], "attacker_victory")
        self.assertEqual(result["war_termination_result"]["status"], "submitted_pending")
        self.assertEqual(submissions, [gate_module.STEP])
        self.assertTrue(self.fence.is_file())
        self.assertNotIn(gate_module.STEP, driver.capabilities()["action_steps"])
        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(gate_module.STEP)
        self.assertEqual(submissions, [gate_module.STEP])
        driver.close()


if __name__ == "__main__":
    unittest.main()
