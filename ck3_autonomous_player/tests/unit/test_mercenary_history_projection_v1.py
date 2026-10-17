"""Real SDK paths with small synthetic market observations and in-memory transport."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_war_reinforcement_tradeoff_v1 import army, company, context
from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.bridge import player_mercenary_context as contract
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer import war_mercenary_consumer_v1 as consumer


SUMMARY_SCHEMA = "xar.market-history-observation-summary.v1"


class InMemoryMarketEndpoint:
    """Synchronous Python callbacks; no real pipe, daemon, Native DLL or Game."""

    pipe_name = r"\\.\pipe\offline-mercenary-history-projection-fixture"

    def __init__(self):
        self.sequence = 0
        self.requests = []
        self.transform = None
        self.cross_frame = False

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, revision=3):
        self.on_frame({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:" + str(revision), "revision": revision,
            "state": {
                "phase": "map_hud", "date": "synthetic-only", "date_raw": 53178312,
                "speed": 1, "paused": True, "map_ready": True, "history": [],
                "played_character": {"character_id": 29829, "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "player_armies": [], "active_wars": [],
            },
        })

    def send(self, request):
        self.requests.append(copy.deepcopy(request))
        if request.get("type") != "execute_step":
            return
        self.sequence += 1
        value = context(
            {"played_character": {"character_id": 29829}, "date_raw": 53178312},
            rows=[company(identity) for identity in range(3)], epoch=self.sequence,
        )
        if self.transform is not None:
            self.transform(value)
        result = {
            "step": contract.STEP, "accepted": True, "status": "completed", "read_only": True,
            "query_sequence": self.sequence, "snapshot_revision": 3,
            "date_raw": 53178312, "player_mercenary_context": value,
            "test_preserved_other_result_key": {"sentinel": self.sequence},
        }
        if self.cross_frame:
            self.publish(revision=4)
        self.on_frame({
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": result,
        })

    def close(self):
        pass

    def transport_error(self):
        return None


class MercenaryHistoryProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mercenary-history-offline-")
        self.root = Path(self.temp.name)
        self.endpoint = InMemoryMarketEndpoint()
        self.driver = nd.NativeHeadlessGameplayDriver(
            self.endpoint.pipe_name, endpoint=self.endpoint, state_dir=self.root,
            command_timeout_seconds=0.5,
        )
        self.endpoint.on_frame({
            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 4242, "session_generation": 0,
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", contract.CAPABILITY],
        })
        self.endpoint.publish()
        self.service = GameplayBridgeService(self.driver)
        self.initial_requests = len(self.endpoint.requests)

    def tearDown(self):
        self.driver.close()
        self.temp.cleanup()

    def query(self, *, service=False):
        revision = self.driver.take_snapshot_without_native_command_history()["revision"]
        if service:
            return self.service.query_player_mercenary_context_v1(expected_revision=revision)
        return self.driver.execute_step(contract.STEP, expected_revision=revision)

    def history(self):
        return self.driver._history_snapshot()

    def market(self, row):
        return row["result"]["player_mercenary_context"]

    def test_valid_market_preserves_latest_full_returns_and_projects_old_rows_idempotently(self):
        first = self.query()
        before = self.history()
        second = self.query(service=True)
        after = self.history()
        self.assertEqual(len(after), 2)
        self.assertEqual([row["index"] for row in after], [row["index"] for row in before] + [2])
        old = self.market(after[0])
        self.assertEqual(old.get("schema"), SUMMARY_SCHEMA)
        self.assertNotIn("rows", old)
        canonical = json.dumps(
            first["player_mercenary_context"], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(old["canonical_sha256"], hashlib.sha256(canonical).hexdigest())
        self.assertEqual(old["canonical_json_bytes"], len(canonical))
        self.assertEqual(old["row_count"], 3)
        self.assertEqual(old["original_query_sequence"], first["query_sequence"])
        self.assertEqual(old["source_frame"], before[0]["result"]["mercenary_query_source_frame_v1"])
        self.assertIs(old["full_body_reconstructible_from_summary"], False)
        self.assertEqual(self.market(after[-1]), second["player_mercenary_context"])
        expected = copy.deepcopy(before[0])
        expected["result"]["player_mercenary_context"] = old
        self.assertEqual(after[0], expected)
        snapshot = self.driver.take_snapshot_without_native_command_history()
        self.assertEqual(consumer._context(after, snapshot), second["player_mercenary_context"])
        sent = self.endpoint.requests[self.initial_requests:]
        self.assertEqual(len(sent), 2)
        self.assertTrue(all(request.get("type") == "execute_step" for request in sent))

        first_summary = copy.deepcopy(after[0])
        third = self.query()
        final = self.history()
        self.assertEqual([row["index"] for row in final], [1, 2, 3])
        self.assertEqual(final[0], first_summary)
        self.assertEqual(self.market(final[1])["schema"], SUMMARY_SCHEMA)
        expected_second = copy.deepcopy(after[1])
        expected_second["result"]["player_mercenary_context"] = self.market(final[1])
        self.assertEqual(final[1], expected_second)
        self.assertEqual(self.market(final[2]), third["player_mercenary_context"])
        self.assertTrue(all(len(result["player_mercenary_context"]["rows"]) == 3
                            for result in (first, second, third)))
        self.assertEqual(consumer._context(final, snapshot), third["player_mercenary_context"])

    def test_invalid_unavailable_and_cross_frame_results_preserve_old_full_market(self):
        for case in ("invalid", "unavailable", "cross_frame"):
            with self.subTest(case=case):
                if case != "invalid":
                    self.tearDown()
                    self.setUp()
                first = self.query()
                if case == "invalid":
                    self.endpoint.transform = lambda value: value.update(actor_character_id=999)
                elif case == "unavailable":
                    self.endpoint.transform = lambda value: value.update(
                        available=False, unavailable_reason="synthetic_unavailable",
                    )
                else:
                    self.endpoint.cross_frame = True
                if case == "unavailable":
                    unavailable = self.query(service=True)
                    self.assertIs(unavailable["player_mercenary_context"]["available"], False)
                else:
                    with self.assertRaises(nd.BridgeUnavailableError):
                        self.query(service=True)
                self.assertEqual(self.market(self.history()[0]), first["player_mercenary_context"])
                self.assertEqual(self.driver.take_snapshot()["native_command_history"], self.history())

    def test_cached_encoder_and_actual_persist_restore_use_compacted_interior(self):
        self.query()
        old_full = self.market(self.history()[0])
        with self.driver._driver_state_lock:
            initial = json.loads(self.driver._encode_driver_state_locked())
        self.assertEqual(initial["command_history"][0]["result"]["player_mercenary_context"], old_full)
        self.assertTrue(self.driver._driver_state_history_json)
        self.query()
        expected = self.history()
        self.assertEqual(self.market(expected[0])["schema"], SUMMARY_SCHEMA)
        self.assertIsNone(self.driver._persist_driver_state())
        restored = nd.load_native_driver_state_for_resume(
            self.driver._native_driver_state_path(), self.endpoint.pipe_name,
        )
        self.assertEqual(restored["command_history"], expected)
        self.assertNotIn("rows", self.market(restored["command_history"][0]))
        self.assertEqual(len(self.market(restored["command_history"][-1])["rows"]), 3)

    def test_summary_only_history_or_stale_full_market_requires_safe_policy_requery(self):
        self.query()
        self.query()
        history = self.history()
        snapshot = self.driver.take_snapshot_without_native_command_history()
        snapshot["active_wars"] = [{
            "war_id": 100663323, "player_side": "defender",
            "player_is_primary_war_leader": True, "player_relative_war_score": -12,
            "targeted_title_ids": [2230], "enemy_armies": [army(2, 1500, 2629, controllable=False)],
        }]
        snapshot["player_armies"] = [army()]
        summary_only = history[:-1]
        self.assertIsNone(consumer._context(summary_only, snapshot))
        if hasattr(self.driver, "_war_mercenary_query_frame_v1"):
            delattr(self.driver, "_war_mercenary_query_frame_v1")
        planned = consumer.plan_war_mercenary_turn_v1(
            self.driver, {"selected_step": "life-advance", "phase": "test"},
            snapshot=snapshot, history=summary_only, bridge_capabilities={contract.CAPABILITY},
        )
        self.assertEqual(planned["selected_step"], contract.STEP)
        stale = copy.deepcopy(snapshot)
        stale["date_raw"] += 1
        self.assertIsNone(consumer._context(history, stale))

    def test_other_rows_errors_selected_claim_and_pending_ledger_are_unchanged(self):
        pending = {
            "schema": "xar.war-mercenary-pending.v1",
            "pending": {"company_id": 2, "pre_capture_epoch": 1,
                        "source_frame": {"episode_run_id": "synthetic"}},
            "observed": [],
        }
        path = self.root / "war-mercenary-pending-v1.json"
        blob = json.dumps(pending).encode()
        path.write_bytes(blob)
        selected = {"selected_step": "hire-mercenary-v1", "selected_company_id": 2,
                    "selection_proof": {"full_selected_candidate": company(2)}}
        self.driver._war_finance_selected_plan_v1 = copy.deepcopy(selected)
        self.driver._record_command("query-synthetic-unrelated", ok=True, result={"nested": [1, 2]})
        self.driver._record_command(contract.STEP, ok=False, result={"raw": "kept"}, error="synthetic rejection")
        with self.assertRaises(nd.UnsupportedStepError):
            self.driver.execute_step("query-synthetic-unsupported")
        unaffected = self.history()
        self.query()
        self.query()
        self.assertEqual(self.history()[:len(unaffected)], unaffected)
        self.assertEqual(self.driver._war_finance_selected_plan_v1, selected)
        self.assertEqual(path.read_bytes(), blob)

    def test_market_queries_skip_history_export_without_changing_public_snapshot(self):
        self.query()
        with patch.object(self.driver, "_history_snapshot", side_effect=AssertionError("market cloned full history")):
            result = self.query(service=True)
        self.assertEqual(len(result["player_mercenary_context"]["rows"]), 3)
        self.assertEqual(len(self.driver.take_snapshot()["native_command_history"]), 2)

    def test_direct_primitive_market_returns_full_without_cloning_or_recording_history(self):
        self.query()
        revision = self.driver.take_snapshot_without_native_command_history()["revision"]
        with patch.object(self.driver, "_history_snapshot", side_effect=AssertionError("primitive cloned full history")):
            result = self.driver._execute_primitive_step(
                contract.STEP, expected_revision=revision, required_capability=contract.CAPABILITY,
            )
        self.assertEqual(len(result["player_mercenary_context"]["rows"]), 3)
        self.assertEqual(len(self.history()), 1)
        self.assertEqual(len(self.driver.take_snapshot()["native_command_history"]), 1)
