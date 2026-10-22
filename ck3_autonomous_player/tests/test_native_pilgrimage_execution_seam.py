"""Consume fresh production C++ serializer packets; never create positive bodies."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import unittest

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge import player_pilgrimage_planner_private_transport as T
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import CK3_12004

CASES = (
    "read", "can-select-false", "quote-dynamic-index", "start-pending",
    "start-unknown", "post-pending", "post-full-generation", "quote-unavailable",
    "hajj-read", "hajj-quote", "hajj-start", "worldly-read", "worldly-quote", "worldly-start",
)
QUERY_TOOL = "ck3_query_player_pilgrimage_planner_v1"
SUBMIT_TOOL = "ck3_submit_player_pilgrimage_planner_v1"


def semantic_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class NativePacketDriver:
    """Actual facade/state with an owned offline process, not an injected CK3."""
    query_player_pilgrimage_planner_private_v1 = NativeHeadlessGameplayDriver.query_player_pilgrimage_planner_private_v1
    submit_player_pilgrimage_planner_private_v1 = NativeHeadlessGameplayDriver.submit_player_pilgrimage_planner_private_v1
    allow_private_player_pilgrimage_activities_query = False

    def __init__(self, packet, *, enabled=True):
        self.allow_private_player_pilgrimage_execution = enabled
        self.packet = deepcopy(packet)
        body = self.packet["result"]["player_pilgrimage_planner"]
        self.state = NativeProtocolState("owned-offline:production-pilgrimage-execution-seam")
        self.owned_hello = {
            "type": "hello", "protocol_version": 1, "pid": os.getpid(),
            "capabilities": [], "connection_generation": 1,
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
            "fixture_owned_process": True, "original_engine_executed": False,
        }
        self.hello_ingest = self.state.ingest(deepcopy(self.owned_hello))
        revision = body["snapshot_revision"]
        self.snapshot = {
            "snapshot_id": "owned-native-packet:" + str(revision),
            "revision": revision + 1, "native_revision": revision,
            "date_raw": body["date_raw"], "paused": True, "map_ready": True,
            "played_character": {"character_id": body["played_character_id"], "alive": True},
            "episode_run_id": "owned-offline-python-seam:" + str(os.getpid()),
            "diagnostics": {"connection_generation": 1, "hello": deepcopy(self.owned_hello)},
        }
        self.endpoint = self
        self.sent = []
        self.ingested_types = []
        self.body_sha_before = semantic_sha(body)

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def capabilities(self):
        return {}

    def send(self, request):
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        # Only nonce correlation changes. All actual production result fields survive.
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class NativeExecutionSeamTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        path = os.environ.get("XAR_PILGRIMAGE_EXECUTION_NATIVE_WIRE_DIR")
        if not path:
            raise RuntimeError("fresh native execution wire required; skipping is forbidden")
        cls.wire = Path(path)
        cls.provenance = json.loads((cls.wire / "PROVENANCE.json").read_text(encoding="utf-8-sig"))
        cls.packets = {name: json.loads((cls.wire / (name + ".json")).read_text(encoding="utf-8-sig")) for name in CASES}
        if cls.provenance.get("owned_result_dtos") is not True or cls.provenance.get("game_queried") is not False:
            raise AssertionError("native fixture provenance does not declare owned, non-game DTOs")

    async def consume(self, name):
        from mcp import Client
        packet = self.packets[name]
        before = deepcopy(packet)
        native = packet["result"]["player_pilgrimage_planner"]
        driver = NativePacketDriver(packet)
        submit = not native["read_only"]
        key = "pilgrimage_type_" + name.split("-")[0] if name.startswith(("hajj-", "worldly-")) else "pilgrimage_type_pious"
        self.assertEqual(native["special_option_key"], key)
        args = {"expected_revision": driver.snapshot["revision"], "operation": native["operation"], "option_key": key}
        if native["operation"] in {"can_select", "start"}:
            # Owned input for the facade; native body is never rewritten to agree.
            args["province_id"] = 1
        if submit:
            args["policy_positive"] = True
        tool = SUBMIT_TOOL if submit else QUERY_TOOL
        async with Client(create_server(driver)) as client:
            tools = {t.name: t for t in (await client.list_tools()).tools}
            self.assertIn(tool, tools)
            result = await client.call_tool(tool, args)
        self.assertFalse(result.is_error, result)
        actual = result.structured_content
        self.assertIsInstance(actual, dict)
        for key, value in native.items():
            self.assertEqual(actual[key], value, key)
        self.assertEqual(driver.hello_ingest, "hello")
        self.assertEqual(driver.ingested_types, ["command_result"])
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.sent[0]["step"], T.SUBMIT_STEP if submit else T.QUERY_STEP)
        self.assertEqual(driver.sent[0]["expected_actor_character_id"], native["played_character_id"])
        self.assertEqual(driver.sent[0]["expected_date_raw"], native["date_raw"])
        self.assertEqual(driver.sent[0]["expected_revision"], native["snapshot_revision"])
        self.assertEqual(driver.state.wait_for_command_result(driver.sent[0]["request_id"], 0.0), None)
        self.assertEqual(packet, before)
        self.assertEqual(driver.packet, before)
        self.assertEqual(semantic_sha(native), driver.body_sha_before)
        self.assertFalse(actual["automatic_retry"])
        self.assertFalse(actual["business_outcome_observed"])
        self.assertFalse(actual["action_ready"])
        self.assertFalse(actual["absence_is_completion"])
        self.assertFalse(actual["raw_pointer_fields_persisted"])
        self.assertEqual(actual["exact_ck3_build"], CK3_12004.game_version)
        self.assertEqual(actual["exe_sha256"], CK3_12004.executable_sha256)
        return actual

    async def test_01_actual_read_packet(self):
        for name in ("read", "hajj-read", "worldly-read"):
            value = await self.consume(name)
            self.assertEqual(value["operation"], "read")
            self.assertFalse(value["invoked"])

    async def test_02_actual_can_select_false_is_not_promoted(self):
        value = await self.consume("can-select-false")
        self.assertIs(value["planner"]["can_select"], False)

    async def test_03_actual_quote_preserves_dynamic_index_and_diagnostic_distinction(self):
        for name in ("hajj-quote", "worldly-quote"):
            variant = await self.consume(name)
            self.assertEqual(variant["quote"]["selected_option"]["key"], variant["special_option_key"])
        value = await self.consume("quote-dynamic-index")
        quote = value["quote"]
        self.assertEqual(quote["known_name_resource_indices"], [3, 7, 2, 9])
        self.assertEqual(quote["configured_cost_raw"][3], 25000000)
        self.assertEqual(quote["diagnostic_aggregate_raw"][3], 123456)
        self.assertNotEqual(quote["configured_cost_raw"], quote["diagnostic_aggregate_raw"])
        self.assertEqual(len(quote["configured_cost_raw"]), 10)
        self.assertIs(quote["failure_display_known"], False)
        self.assertIsNone(quote["failure_display"])

    async def test_04_actual_start_pending_is_pending(self):
        for name in ("hajj-start", "worldly-start"):
            variant = await self.consume(name)
            self.assertEqual(variant["operation_status"], "submitted_pending")
            self.assertTrue(variant["invoked"])
        value = await self.consume("start-pending")
        self.assertEqual(value["operation_status"], "submitted_pending")
        self.assertTrue(value["invoked"])
        self.assertIsNone(value["new_identity"])

    async def test_05_actual_start_unknown_stays_unknown(self):
        value = await self.consume("start-unknown")
        self.assertEqual(value["operation_status"], "submission_outcome_unknown")
        self.assertEqual(value["ledger_state"], "submission_outcome_unknown")
        self.assertTrue(value["needs_recovery"])

    async def test_06_actual_post_pending_is_not_completion(self):
        value = await self.consume("post-pending")
        self.assertEqual(value["operation_status"], "post_pending")
        self.assertTrue(value["needs_recovery"])
        self.assertIsNone(value["new_identity"])

    async def test_07_actual_post_full_generation_identity(self):
        value = await self.consume("post-full-generation")
        self.assertEqual(value["operation_status"], "identity_observed")
        self.assertEqual(value["new_identity"]["activity_id"], 0xFE000005)
        self.assertEqual(value["new_identity"]["host_character_id"], value["played_character_id"])
        self.assertFalse(value["new_identity"]["native_completion_stamp_observed"])
        self.assertIsNone(value["new_identity"]["native_completion_stamp_raw"])

    async def test_08_actual_unavailable_quote_remains_unavailable(self):
        value = await self.consume("quote-unavailable")
        self.assertEqual(value["operation_status"], "unavailable")
        self.assertEqual(value["failure"], "normal_refresh_not_observed")
        self.assertIsNone(value["quote"])

    async def test_09_default_off_and_identity_only_never_register_execution(self):
        from mcp import Client
        for identity_only in (False, True):
            driver = NativePacketDriver(self.packets["read"], enabled=False)
            driver.allow_private_player_pilgrimage_activities_query = identity_only
            driver.case_declared_read_only_mcp_tools = {QUERY_TOOL, "ck3_query_player_pilgrimage_activities_v1"}
            async with Client(create_server(driver)) as client:
                names = {t.name for t in (await client.list_tools()).tools}
            self.assertNotIn(QUERY_TOOL, names)
            self.assertNotIn(SUBMIT_TOOL, names)
            with self.assertRaises(UnsupportedStepError):
                driver.query_player_pilgrimage_planner_private_v1(expected_revision=driver.snapshot["revision"])
            self.assertEqual(driver.sent, [])

    async def test_10_registered_unknown_argument_and_false_policy_reject_before_send(self):
        from mcp import Client
        driver = NativePacketDriver(self.packets["start-pending"])
        async with Client(create_server(driver)) as client:
            bad = await client.call_tool(QUERY_TOOL, {"expected_revision": driver.snapshot["revision"], "fabricated": True})
            self.assertTrue(bad.is_error)
            bad = await client.call_tool(SUBMIT_TOOL, {"expected_revision": driver.snapshot["revision"], "operation": "start", "province_id": 1, "policy_positive": False})
            self.assertTrue(bad.is_error)
        self.assertEqual(driver.sent, [])

    async def test_11_strict_normalizer_rejects_corrupted_actual_quote(self):
        packet = self.packets["quote-dynamic-index"]
        driver = NativePacketDriver(packet)
        original = packet["result"]["player_pilgrimage_planner"]
        for mutate in (
            lambda q: q["configured_cost_raw"].pop(),
            lambda q: q["known_name_resource_indices"].__setitem__(1, 3),
            lambda q: q.__setitem__("failure_display_known", True),
            lambda q: q.__setitem__("raw_pointer_fields_persisted", True),
            lambda q: q.__setitem__("actor_character_id", q["actor_character_id"] + 1),
        ):
            negative = deepcopy(original)
            mutate(negative["quote"])
            with self.assertRaises(BridgeUnavailableError):
                T.normalize_player_pilgrimage_planner_v1(negative, source=driver.snapshot, operation="quote", submit=False)


if __name__ == "__main__":
    unittest.main()
