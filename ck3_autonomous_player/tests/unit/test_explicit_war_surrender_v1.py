"""Synthetic Python boundary tests; no game/native execution qualification."""
from __future__ import annotations
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from threading import RLock
import unittest

from xar_autoplayer.bridge import explicit_war_surrender_v1 as explicit
from xar_autoplayer.bridge.driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, _emergency_surrender_readiness
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004


def snapshot():
    war = {"war_id": 8, "player_side": "defender", "player_is_primary_war_leader": True,
        "player_relative_war_score": 0}
    option = {"outcome": "attacker_victory", "hostage_variant": "none", "context_constructed": True,
        "native_validator_passed": True, "available": True, "auto_accept_observable": True,
        "auto_accept": True, "terms_observable": False,
        "terms": {"status": "unavailable", "reason": "cb_specific_terms_not_observable"},
        "recipient_response": {"status": "unavailable", "decision_status_raw": None, "would_accept_now": None}}
    row = {**war, "queried_snapshot_id": "native:100", "queried_revision": 3,
        "queried_native_revision": 100, "queried_connection_generation": 1,
        "episode_run_id": "synthetic-explicit-surrender", "query_sequence": 2, "options": {"surrender": option}}
    return {"revision": 3, "native_revision": 100, "snapshot_id": "native:100", "date_raw": 53171400,
        "paused": True, "map_ready": True, "episode_run_id": "synthetic-explicit-surrender",
        "played_character": {"character_id": 31254, "alive": True}, "active_wars": [war],
        "war_termination_options": [row], "diagnostics": {"connection_generation": 1, "bridge_pid": 99,
            "hello": {"expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256, "ck3_build_match": True,
                "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "pid": 99}}}


def driver_at(folder, before=None, *, unknown=False, remove_war=True, omit_projection=False):
    value = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
    value.state_dir = Path(folder)
    value._war31_one_shot_surrender_gate = None
    value._history_snapshot = lambda: []
    caps = ["game.command.query-war-termination-options-N", "game.command.surrender-war-N"]
    value.state = SimpleNamespace(capabilities=lambda: {"bridge_capabilities": caps})
    value.capabilities = lambda: {"action_steps": [], "bridge_capabilities": caps}
    before = copy.deepcopy(before or snapshot())
    row = copy.deepcopy(before["war_termination_options"][0])
    value._driver_state_lock = RLock()
    value._war_termination_options = {row["war_id"]: {"options": row,
        "query_sequence": row["query_sequence"], "cache_binding": {
            "native_revision": row["queried_native_revision"], "snapshot_id": row["queried_snapshot_id"],
            "connection_generation": row["queried_connection_generation"], "episode_run_id": row["episode_run_id"]}}}
    if omit_projection:
        before.pop("war_termination_options")
    after = copy.deepcopy(before)
    if remove_war:
        after["active_wars"] = []
    sent = []
    value.take_snapshot = lambda: copy.deepcopy(after if sent else before)
    def send(step, **kwargs):
        # Exercise the production reservation ordering, not a precomputed DTO.
        claims = list(Path(folder).rglob("*.claim.json"))
        if len(claims) != 1:
            raise AssertionError("durable exclusive claim was not written before send")
        sent.append({"step": step, **kwargs})
        if unknown:
            raise TimeoutError("synthetic unknown transport result")
        return {"step": step, "accepted": True, "status": "submitted", "backend_id": "native-headless"}
    value._execute_primitive_step = send
    return value, sent, before


class ExplicitSurrenderTests(unittest.TestCase):
    def test_normal_defender_permission_is_not_an_emergency_policy(self):
        before = snapshot()
        evidence = explicit.explicit_surrender_evidence(before, 8, 3)
        self.assertFalse(_emergency_surrender_readiness(before, 8)[0])
        self.assertEqual(evidence["surrender"]["outcome"], "attacker_victory")
        self.assertFalse(evidence["surrender"]["terms_observable"])
        self.assertIsNone(evidence["surrender"]["recipient_response"]["would_accept_now"])

    def test_freshness_identity_and_original_permissions_fail_before_claim_or_send(self):
        mutations = [lambda s: s.update(paused=False), lambda s: s.update(revision=4),
            lambda s: s["diagnostics"].update(connection_generation=2),
            lambda s: s["active_wars"][0].update(player_is_primary_war_leader=False),
            lambda s: s["active_wars"][0].update(war_id=0x1000008),
            lambda s: s.update(native_revision=101),
            lambda s: s["war_termination_options"][0]["options"]["surrender"].update(native_validator_passed=False),
            lambda s: s["war_termination_options"][0]["options"]["surrender"].update(auto_accept=None),
            lambda s: s["war_termination_options"][0]["options"]["surrender"].update(outcome="attacker_defeat")]
        with TemporaryDirectory() as folder:
            for mutation in mutations:
                with self.subTest(mutation=mutation):
                    state = snapshot(); mutation(state)
                    value, sent, _ = driver_at(folder, state)
                    with self.assertRaises((BridgeUnavailableError, PreSubmissionRevisionMismatchError, ValueError)):
                        value.surrender_war_explicit_v1(8, expected_revision=3)
                    self.assertEqual(sent, [])
                    self.assertEqual(list(Path(folder).rglob("*.claim.json")), [])

    def test_common_automatic_executor_still_rejects_ordinary_war(self):
        with TemporaryDirectory() as folder:
            value, sent, before = driver_at(folder)
            with self.assertRaises(BridgeUnavailableError):
                value._execute_war_termination_step("surrender-war-8", starting=before,
                    selected_revision=3, query_war_id=None, surrender_war_id=8, white_peace_war_id=None)
            self.assertEqual(sent, [])

    def test_public_service_uses_explicit_driver_and_independent_after_war_inventory(self):
        with TemporaryDirectory() as folder:
            value, sent, _ = driver_at(folder)
            service = GameplayBridgeService.__new__(GameplayBridgeService); service.driver = value
            result = service.surrender_war(8, expected_revision=3)
            self.assertEqual(len(sent), 1)
            action = result["war_termination_result"]
            self.assertEqual(action["outcome"], "attacker_victory")
            self.assertEqual(action["status"], "applied")
            self.assertTrue(action["war_id_absent_after_ack"])
            self.assertTrue(action["explicit_player_request"])
            self.assertFalse(action["native_option"]["terms_observable"])
            self.assertIsNone(action["recipient_would_accept_now"])
            self.assertEqual(sent[0]["required_capability"], "game.command.surrender-war-N")
            self.assertEqual(value.capabilities()["action_steps"], [])

    def test_ack_with_war_still_present_is_pending(self):
        with TemporaryDirectory() as folder:
            value, sent, _ = driver_at(folder, remove_war=False)
            result = value.surrender_war_explicit_v1(8, expected_revision=3)
            self.assertEqual(result["war_termination_result"]["status"], "submitted_pending")
            self.assertFalse(result["war_termination_result"]["war_id_absent_after_ack"])

    def test_missing_public_projection_uses_only_real_same_frame_driver_cache(self):
        with TemporaryDirectory() as folder:
            value, sent, before = driver_at(folder, omit_projection=True)
            self.assertNotIn("war_termination_options", before)
            result = value.surrender_war_explicit_v1(8, expected_revision=3)
            self.assertEqual(result["war_termination_result"]["outcome"], "attacker_victory")
            self.assertEqual(len(sent), 1)

    def test_unknown_claim_survives_restart_revision_and_connection_changes(self):
        with TemporaryDirectory() as folder:
            value, sent, before = driver_at(folder, unknown=True)
            with self.assertRaises(TimeoutError):
                value.surrender_war_explicit_v1(8, expected_revision=3)
            self.assertEqual(len(sent), 1)
            later = copy.deepcopy(before)
            later.update(revision=4, native_revision=101, snapshot_id="native:101")
            later["diagnostics"]["connection_generation"] = 2
            later["war_termination_options"][0].update(queried_revision=4, queried_native_revision=101,
                queried_snapshot_id="native:101", queried_connection_generation=2, query_sequence=3)
            restarted, sent_again, _ = driver_at(folder, later)
            with self.assertRaises(BridgeUnavailableError):
                restarted.surrender_war_explicit_v1(8, expected_revision=4)
            with self.assertRaises(BridgeUnavailableError):
                explicit.reject_existing_explicit_surrender(restarted, later, 8)
            self.assertEqual(sent_again, [])
            self.assertEqual(len(list(Path(folder).rglob("*.claim.json"))), 1)


class RealMcpRegistrationBoundary(unittest.IsolatedAsyncioTestCase):
    async def test_existing_public_tool_reaches_explicit_typed_method(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        with TemporaryDirectory() as folder:
            value, sent, _ = driver_at(folder)
            async with Client(create_server(value)) as client:
                tools = await client.list_tools()
                self.assertIn("ck3_surrender_war", [t.name for t in tools.tools])
                result = await client.call_tool("ck3_surrender_war", {"war_id": 8, "expected_revision": 3})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["war_termination_result"]["outcome"], "attacker_victory")
            self.assertEqual(len(sent), 1)
