from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from test_declaration_contract import _declaration


def fixture(test: unittest.TestCase, *, timeout: float = 0.001):
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint,
        declarable_wars_timeout_seconds=timeout,
    )
    test.addCleanup(driver.close)
    endpoint.publish(_hello("game.state.snapshot", "game.state.declarable-wars",
                            "game.command.query-declarable-wars"))
    endpoint.publish(_snapshot(40, played_character={"character_id": 707, "alive": True}))
    return driver, endpoint


def requests(endpoint):
    return [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]


def result_frame(request_id: str):
    return {
        "type": "command_result", "protocol_version": 1,
        "request_id": request_id, "ok": True,
        "result": {"step": "query-declarable-wars", "accepted": True,
                   "status": "available", "query_sequence": 1,
                   "declarable_wars": [_declaration()]},
    }


def submit_timeout(test, driver, endpoint):
    starting = driver.take_snapshot()
    with test.assertRaisesRegex(BridgeUnavailableError, "retained_declaration_query=") as raised:
        driver.execute_step("query-declarable-wars", expected_revision=starting["revision"])
    sent = requests(endpoint)
    test.assertEqual(len(sent), 1)
    test.assertIn(sent[0]["request_id"], str(raised.exception))
    return starting, sent[0]["request_id"]


class DeclarableQueryCollectionTests(unittest.TestCase):
    def test_independent_budget_keeps_normal_query_cache_behavior(self):
        driver, endpoint = fixture(self, timeout=120.0)
        endpoint.send_hook = lambda frame: endpoint.publish(result_frame(frame["request_id"]))
        with patch.object(driver.state, "wait_for_command_result",
                          wraps=driver.state.wait_for_command_result) as wait:
            driver.execute_step("query-declarable-wars",
                                expected_revision=driver.take_snapshot()["revision"])
        self.assertEqual(wait.call_args.args[1], 120.0)
        self.assertEqual(driver.command_timeout_seconds, 10.0)
        self.assertEqual(driver.take_snapshot()["declaration_query_sequence"], 1)

    def test_timeout_records_binding_and_blocks_duplicate_submission(self):
        driver, endpoint = fixture(self)
        starting, request_id = submit_timeout(self, driver, endpoint)
        pending = driver.diagnostics()["pending_declaration_query"]
        self.assertEqual(pending["request_id"], request_id)
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["binding"]["native_revision"], 40)
        self.assertEqual(pending["binding"]["player_character_id"], 707)
        self.assertEqual(pending["binding"]["bridge_pid"], 4242)
        with self.assertRaisesRegex(BridgeUnavailableError, "collect its original request"):
            driver.execute_step("query-declarable-wars", expected_revision=starting["revision"])
        self.assertEqual(len(requests(endpoint)), 1)

    def test_pending_then_late_result_restores_cache_without_resend_or_history_rewrite(self):
        driver, endpoint = fixture(self)
        starting, request_id = submit_timeout(self, driver, endpoint)
        failed_history = copy.deepcopy(driver.take_snapshot()["native_command_history"])
        pending = driver.collect_declarable_wars_result_v1(request_id, expected_revision=starting["revision"])
        self.assertEqual(pending["status"], "pending")
        frame = result_frame(request_id)
        endpoint.publish(frame)
        result = driver.collect_declarable_wars_result_v1(request_id, expected_revision=starting["revision"])
        self.assertEqual(result["status"], "available")
        self.assertFalse(result["native_resubmitted"])
        self.assertTrue(result["cache_restored"])
        self.assertEqual(result["native_result_frame"], frame)
        snapshot = driver.take_snapshot()
        self.assertEqual(snapshot["declaration_query_sequence"], 1)
        self.assertEqual(snapshot["declarable_wars"][0]["declaration_id"], "808-17-0")
        self.assertEqual(snapshot["native_command_history"], failed_history)
        self.assertEqual(len(requests(endpoint)), 1)
        self.assertIsNone(driver.diagnostics()["pending_declaration_query"])

    def test_unknown_request_or_wrong_public_revision_does_not_consume_result(self):
        driver, endpoint = fixture(self)
        starting, request_id = submit_timeout(self, driver, endpoint)
        endpoint.publish(result_frame(request_id))
        with self.assertRaisesRegex(BridgeUnavailableError, "no pending"):
            driver.collect_declarable_wars_result_v1("other-request", expected_revision=starting["revision"])
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            driver.collect_declarable_wars_result_v1(request_id, expected_revision=starting["native_revision"])
        result = driver.collect_declarable_wars_result_v1(request_id, expected_revision=starting["revision"])
        self.assertEqual(result["status"], "available")
        self.assertEqual(len(requests(endpoint)), 1)

    def test_changed_binding_returns_stale_without_adopting_late_rows(self):
        paths = [
            ("snapshot_id",), ("native_revision",), ("revision",), ("date_raw",),
            ("episode_run_id",), ("played_character", "character_id"),
            ("diagnostics", "bridge_pid"), ("diagnostics", "connection_generation"),
            ("paused",), ("map_ready",),
        ]
        for path in paths:
            with self.subTest(path=path):
                driver, endpoint = fixture(self)
                starting, request_id = submit_timeout(self, driver, endpoint)
                endpoint.publish(result_frame(request_id))
                changed = copy.deepcopy(starting)
                target = changed
                for key in path[:-1]:
                    target = target[key]
                key = path[-1]
                old = target[key]
                target[key] = not old if isinstance(old, bool) else old + 1 if isinstance(old, int) else str(old) + "-changed"
                with patch.object(driver, "take_snapshot", return_value=changed):
                    result = driver.collect_declarable_wars_result_v1(request_id, expected_revision=changed["revision"])
                self.assertEqual(result["status"], "stale")
                self.assertFalse(result["cache_restored"])
                self.assertEqual(driver.take_snapshot()["declarable_wars"], [])
                self.assertEqual(len(requests(endpoint)), 1)

    def test_changed_binding_with_no_reply_is_stale_and_not_a_new_query(self):
        driver, endpoint = fixture(self)
        starting, request_id = submit_timeout(self, driver, endpoint)
        endpoint.publish(_snapshot(41, played_character={"character_id": 707, "alive": True}))
        result = driver.collect_declarable_wars_result_v1(request_id, expected_revision=driver.take_snapshot()["revision"])
        self.assertEqual(result["status"], "stale")
        self.assertFalse(result["cache_restored"])
        self.assertEqual(len(requests(endpoint)), 1)

    def test_native_rejection_is_preserved_without_cache(self):
        driver, endpoint = fixture(self)
        starting, request_id = submit_timeout(self, driver, endpoint)
        frame = result_frame(request_id)
        frame.update(ok=False, error="CK3 declarable-war query is unavailable")
        frame.pop("result")
        endpoint.publish(frame)
        result = driver.collect_declarable_wars_result_v1(request_id, expected_revision=starting["revision"])
        self.assertEqual(result["status"], "native-rejected")
        self.assertEqual(result["native_result_frame"], frame)
        self.assertEqual(driver.take_snapshot()["declarable_wars"], [])

    def test_malformed_reply_remains_retained_after_validation_failure(self):
        driver, endpoint = fixture(self)
        starting, request_id = submit_timeout(self, driver, endpoint)
        frame = result_frame(request_id)
        frame["result"]["query_sequence"] = True
        endpoint.publish(frame)
        for _ in range(2):
            with self.assertRaisesRegex(BridgeUnavailableError, "lacks query_sequence"):
                driver.collect_declarable_wars_result_v1(request_id, expected_revision=starting["revision"])
        self.assertEqual(driver._pending_declaration_query["result_frame"], frame)
        self.assertEqual(len(requests(endpoint)), 1)


class DeclarableQueryCollectionMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_mcp_collects_same_request_through_service(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server

        driver, endpoint = fixture(self)
        starting, request_id = submit_timeout(self, driver, endpoint)
        async with Client(create_server(driver)) as client:
            pending = await client.call_tool("ck3_collect_declarable_wars_result_v1", {
                "request_id": request_id, "expected_revision": starting["revision"],
            })
            self.assertFalse(pending.is_error)
            self.assertEqual(pending.structured_content["status"], "pending")
            endpoint.publish(result_frame(request_id))
            collected = await client.call_tool("ck3_collect_declarable_wars_result_v1", {
                "request_id": request_id, "expected_revision": starting["revision"],
            })
        self.assertFalse(collected.is_error)
        self.assertEqual(collected.structured_content["status"], "available")
        self.assertEqual(len(requests(endpoint)), 1)


if __name__ == "__main__":
    unittest.main()
