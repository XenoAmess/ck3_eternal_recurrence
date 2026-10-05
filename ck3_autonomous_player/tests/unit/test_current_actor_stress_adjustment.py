"""Focused synthetic stress-getter and actual MCP SDK schema regressions.

Native responses and frames here are fixtures, never real CK3 observations.
The production JSON encoder writes only to memory; no pipe or game is opened.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge.current_actor_stress_adjustment_contract import (
    STEP, CAPABILITY, SCHEMA, EXE_SHA256, PROOFS, NUMBERS,
    validate_base_amount, stress_query_binding, normalize_native_stress_query,
    normalize_public_stress_query, project_stress_query,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeNamedPipeServer, _action_steps
from xar_autoplayer.bridge.service import GameplayBridgeService


def source_frame():
    return {
        "revision": 1, "native_revision": 7, "snapshot_id": "synthetic-paused-frame-7",
        "paused": True, "map_ready": True, "speed": 3, "date_raw": 12345,
        "episode_run_id": "synthetic-episode", "episode_character_id": 7001,
        "local_player_id": 0, "one_life_terminal_reason": None,
        "played_character": {"character_id": 7001, "alive": True, "stress_points": 17},
        "active_event": {"instance_id": 101}, "pending_character_interaction": None,
        "diagnostics": {"connected": True, "connection_generation": 2, "bridge_pid": 991,
                        "hello": {"pid": 991, "ck3_build_match": True,
                                  "game_adapter_id": "ck3-1.20.0.3-msvc-x64",
                                  "expected_ck3_version": "1.20.0.3", "expected_ck3_sha256": EXE_SHA256}},
    }


def native_response(base_amount=15, *, available=True):
    payload = {
        "schema": SCHEMA, "status": "available" if available else "unavailable",
        "source": "native_current_actor_stress_consumer_1.20.0.3", "read_only": True,
        "exact_build": "1.20.0.3", "executable_sha256": EXE_SHA256.upper(),
        "snapshot_revision": 7, "date_raw": 12345, "game_pid": 991, "connection_generation": 2,
        "player_character_id": 7001, "base_amount": base_amount,
        "current_stress_points": 17 if available else None,
        "stress_gain_modifier_raw": 25000 if available else None,
        "stress_loss_modifier_raw": -10000 if available else None,
        "modifier_scale": 100000, "modifier_semantics": "additive_increment",
        # Intentionally unrelated to a Python formula. Only the native return is consumed.
        "adjusted_delta_points": 23 if available else None,
        "stress_gain_consumer_index": 143, "stress_loss_consumer_index": 144,
        "native_aggregator_getter_rva": "0x28C3AE0", "native_modifier_reader_rva": "0x2303700",
        "native_adjuster_rva": "0x28BC800", **{key: available for key in PROOFS},
        "owner_thread_id": 345 if available else 0, "owner_pump_epoch": 678 if available else 0,
        "unavailable_reason": None if available else "synthetic_native_read_unavailable",
        "final_after_stress_prediction_ready": False, "option_cost_binding_ready": False,
        "business_postcondition_verified": False,
    }
    return {"step": STEP, "accepted": True, "status": payload["status"], "read_only": True,
            "query_sequence": 11, "snapshot_revision": 7, "date_raw": 12345,
            "game_pid": 991, "connection_generation": 2, "current_actor_stress_adjustment": payload,
            "backend_id": "native-headless"}


class SyntheticGetter:
    query_current_actor_stress_adjustment_v1 = NativeHeadlessGameplayDriver.query_current_actor_stress_adjustment_v1

    def __init__(self):
        self.frame = source_frame()
        self.result = native_response()
        self.calls = []
        self.caps = {CAPABILITY}
        self.after = None

    def take_snapshot(self):
        return deepcopy(self.frame)

    def _execute_primitive_step(self, step, **kwargs):
        if kwargs["required_capability"] not in self.caps:
            raise UnsupportedStepError("synthetic capability absent")
        self.calls.append((step, deepcopy(kwargs)))
        result = deepcopy(self.result)
        if self.after:
            self.after(self.frame)
        return result


class MemoryPrimitiveGetter(SyntheticGetter):
    _execute_primitive_step = NativeHeadlessGameplayDriver._execute_primitive_step
    _verify_idempotent_map_control_postcondition = NativeHeadlessGameplayDriver._verify_idempotent_map_control_postcondition

    def __init__(self):
        super().__init__()
        self._request_sequence = 0
        self.command_timeout_seconds = .1
        self.packets = []
        self.endpoint = SimpleNamespace(send=self.capture_request)
        self.state = SimpleNamespace(wait_for_command_result=lambda *_: {"ok": True, "result": deepcopy(self.result)})

    def capabilities(self):
        return {"bridge_capabilities": sorted(self.caps), "action_steps": []}

    def capture_request(self, request):
        fake_pipe = SimpleNamespace(_write_lock=threading.Lock(), _current_handle=lambda: 1)
        def collect(_handle, packet):
            self.packets.append(bytes(packet))
            directory = os.environ.get("XAR_STRESS_GETTER_TEST_ARTIFACTS")
            if directory:
                folder = Path(directory)
                folder.mkdir(parents=True, exist_ok=True)
                path = folder / f"actual-production-encoder-{len(self.packets):02d}.bin"
                with path.open("xb") as stream:
                    stream.write(packet)
                with path.with_suffix(".json").open("x", encoding="utf-8") as stream:
                    json.dump(json.loads(packet[4:]), stream, indent=2)
            return True
        with patch("xar_autoplayer.bridge.native_driver._write_all", side_effect=collect):
            NativeNamedPipeServer.send(fake_pipe, request)


class ContractTests(unittest.TestCase):
    def binding(self):
        return stress_query_binding(source_frame(), 1)

    def test_signed_amount_bounds_reject_bool_float_string_null(self):
        for value in (-300, 0, 300):
            self.assertEqual(validate_base_amount(value), value)
        for value in (True, False, 1.0, "15", None, -301, 301, 2**31):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_base_amount(value)

    def test_native_raw_and_adjuster_return_are_preserved_without_recalculation(self):
        raw = native_response()
        value = raw["current_actor_stress_adjustment"]
        value["stress_gain_modifier_raw"] = 2**63 - 1
        value["stress_loss_modifier_raw"] = -(2**63)
        value["adjusted_delta_points"] = -(2**31)
        result = normalize_native_stress_query(raw, self.binding(), 15)
        self.assertEqual(result, raw)
        self.assertIsNot(result, raw)

    def test_unavailable_is_a_completed_read_with_four_explicit_nulls(self):
        raw = native_response(available=False)
        result = project_stress_query(raw, self.binding(), 15)
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["current_actor_stress_adjustment_ready"])
        self.assertTrue(all(result["current_actor_stress_adjustment"][key] is None for key in NUMBERS))

    def test_unavailable_partial_numbers_missing_reason_and_default_zeros_fail(self):
        for key, value in [(key, 0) for key in NUMBERS] + [("unavailable_reason", None), ("unavailable_reason", "")]:
            raw = native_response(available=False)
            raw["current_actor_stress_adjustment"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_native_stress_query(raw, self.binding(), 15)

    def test_every_available_proof_and_owner_stamp_is_required(self):
        for key, value in [(key, False) for key in PROOFS] + [("owner_thread_id", 0), ("owner_pump_epoch", 0), ("owner_thread_id", True)]:
            raw = native_response()
            raw["current_actor_stress_adjustment"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_native_stress_query(raw, self.binding(), 15)

    def test_numeric_types_and_ranges_are_not_coerced(self):
        for key, value in [("current_stress_points", True), ("current_stress_points", -1),
                           ("adjusted_delta_points", 23.0), ("adjusted_delta_points", 2**31),
                           ("stress_gain_modifier_raw", 2**63), ("stress_loss_modifier_raw", "-10000")]:
            raw = native_response()
            raw["current_actor_stress_adjustment"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_native_stress_query(raw, self.binding(), 15)

    def test_actor_revision_date_pid_and_generation_must_match_actual_frame(self):
        for key in ("player_character_id", "snapshot_revision", "date_raw", "game_pid", "connection_generation", "base_amount"):
            raw = native_response()
            raw["current_actor_stress_adjustment"][key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_native_stress_query(raw, self.binding(), 15)

    def test_envelope_and_payload_are_closed_and_reject_overcredit(self):
        for target in ("envelope", "payload"):
            raw = native_response()
            (raw if target == "envelope" else raw["current_actor_stress_adjustment"])["unknown"] = 1
            with self.subTest(target=target), self.assertRaises(ValueError):
                normalize_native_stress_query(raw, self.binding(), 15)
        for key in ("final_after_stress_prediction_ready", "option_cost_binding_ready", "business_postcondition_verified"):
            raw = native_response()
            raw["current_actor_stress_adjustment"][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_native_stress_query(raw, self.binding(), 15)

    def test_fixed_point_scale_semantics_indices_image_and_rva_are_exact(self):
        for key, value in (("modifier_scale", 1000), ("modifier_semantics", "multiplier"),
                           ("stress_gain_consumer_index", 144), ("stress_loss_consumer_index", 143),
                           ("executable_sha256", "0" * 64), ("native_adjuster_rva", "0x28BCA60")):
            raw = native_response()
            raw["current_actor_stress_adjustment"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_native_stress_query(raw, self.binding(), 15)

    def test_actual_snapshot_stress_disagreement_is_rejected(self):
        raw = native_response()
        raw["current_actor_stress_adjustment"]["current_stress_points"] = 18
        with self.assertRaises(ValueError):
            normalize_native_stress_query(raw, self.binding(), 15)

    def test_public_revision_and_native_revision_remain_distinct(self):
        result = project_stress_query(native_response(), self.binding(), 15)
        self.assertEqual(result["queried_revision"], 1)
        self.assertEqual(result["queried_native_revision"], 7)
        self.assertEqual(result["snapshot_revision"], 7)
        result["queried_revision"] = 7
        with self.assertRaises(ValueError):
            normalize_public_stress_query(result, self.binding(), 15)


class GetterTests(unittest.TestCase):
    def test_actual_method_injects_only_current_actor_identity(self):
        driver = SyntheticGetter()
        result = driver.query_current_actor_stress_adjustment_v1(15, expected_revision=1)
        self.assertTrue(result["current_actor_stress_adjustment_ready"])
        self.assertEqual(driver.calls, [(STEP, {"expected_revision": 1, "required_capability": CAPABILITY,
            "request_fields": {"base_amount": 15, "expected_player_character_id": 7001,
                               "expected_game_pid": 991, "expected_connection_generation": 2}})])

    def test_stale_or_malformed_revision_and_ineligible_frame_do_not_submit(self):
        cases = [("revision", 2), ("revision", True), ("paused", False), ("map_ready", False),
                 ("alive", False), ("connected", False), ("image", "0" * 64), ("actor", 2**31)]
        for key, value in cases:
            driver = SyntheticGetter()
            expected = value if key == "revision" else 1
            if key == "alive": driver.frame["played_character"]["alive"] = value
            elif key == "connected": driver.frame["diagnostics"]["connected"] = value
            elif key == "image": driver.frame["diagnostics"]["hello"]["expected_ck3_sha256"] = value
            elif key == "actor": driver.frame["played_character"]["character_id"] = value
            elif key != "revision": driver.frame[key] = value
            with self.subTest(key=key), self.assertRaises((ValueError, BridgeUnavailableError)):
                driver.query_current_actor_stress_adjustment_v1(15, expected_revision=expected)
            self.assertEqual(driver.calls, [])

    def test_after_revision_actor_date_reconnect_and_stress_drift_fail(self):
        mutations = [lambda f: f.update(revision=2), lambda f: f.update(date_raw=12346),
                     lambda f: f["played_character"].update(character_id=7002),
                     lambda f: f["played_character"].update(stress_points=18),
                     lambda f: f["diagnostics"].update(connection_generation=3),
                     lambda f: f.update(active_event={"instance_id": 102})]
        for index, mutation in enumerate(mutations):
            driver = SyntheticGetter()
            driver.after = mutation
            with self.subTest(index=index), self.assertRaises(BridgeUnavailableError):
                driver.query_current_actor_stress_adjustment_v1(15, expected_revision=1)
            self.assertEqual(len(driver.calls), 1)

    def test_missing_native_capability_is_not_simulated(self):
        driver = MemoryPrimitiveGetter()
        driver.caps.clear()
        with self.assertRaises(UnsupportedStepError):
            driver.query_current_actor_stress_adjustment_v1(15, expected_revision=1)
        self.assertEqual(driver.packets, [])
        self.assertNotIn(STEP, _action_steps([CAPABILITY], paused=True))

    def test_actual_production_packet_encoder_maps_public_to_native_revision_in_memory(self):
        driver = MemoryPrimitiveGetter()
        result = driver.query_current_actor_stress_adjustment_v1(15, expected_revision=1)
        self.assertEqual(len(driver.packets), 1)
        packet = driver.packets[0]
        self.assertEqual(struct.unpack("<I", packet[:4])[0], len(packet) - 4)
        request = json.loads(packet[4:])
        self.assertEqual(request["expected_revision"], 7)
        self.assertEqual(request["expected_player_character_id"], 7001)
        self.assertEqual(request["base_amount"], 15)
        self.assertEqual(set(request), {"type", "protocol_version", "request_id", "step", "expected_revision",
                                      "base_amount", "expected_player_character_id", "expected_game_pid",
                                      "expected_connection_generation"})
        self.assertEqual(result["queried_revision"], 1)

    def test_service_independently_validates_a_driver_projection(self):
        driver = SyntheticGetter()
        driver.query_current_actor_stress_adjustment_v1 = lambda *a, **k: project_stress_query(
            native_response(), stress_query_binding(driver.frame, 1), 15)
        service = GameplayBridgeService(driver)
        self.assertTrue(service.query_current_actor_stress_adjustment_v1(15, expected_revision=1)["current_actor_stress_adjustment_ready"])
        original = driver.query_current_actor_stress_adjustment_v1
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            result["current_actor_stress_adjustment"]["option_cost_binding_ready"] = True
            return result
        driver.query_current_actor_stress_adjustment_v1 = changed
        with self.assertRaises(BridgeUnavailableError):
            service.query_current_actor_stress_adjustment_v1(15, expected_revision=1)

    def test_service_requires_backend_method_and_actual_after_frame(self):
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(SimpleNamespace()).query_current_actor_stress_adjustment_v1(15, expected_revision=1)
        driver = SyntheticGetter()
        def changed(*args, **kwargs):
            result = project_stress_query(native_response(), stress_query_binding(driver.frame, 1), 15)
            driver.frame["played_character"]["character_id"] = 7002
            return result
        driver.query_current_actor_stress_adjustment_v1 = changed
        with self.assertRaises(BridgeUnavailableError):
            GameplayBridgeService(driver).query_current_actor_stress_adjustment_v1(15, expected_revision=1)


def profile_fixture():
    import ck3_native_profile_mcp as profile
    driver = SyntheticGetter()
    service = object.__new__(profile.NativeProfileService)
    service._lock = threading.RLock()
    service._attach_result = {"status": "attached_snapshot_verified"}
    service._gameplay = GameplayBridgeService(driver)
    service.guard_count = 0
    def guard():
        service.guard_count += 1
        return {}
    service.guard = guard
    service._snapshot = driver.take_snapshot
    service._receipt = lambda action, result: {"action": action, **deepcopy(result)}
    return service, driver


class ProfileTests(unittest.TestCase):
    def test_profile_keeps_guards_and_declares_only_read_observation(self):
        service, driver = profile_fixture()
        result = service.query_stress_adjustment(15, 1)
        self.assertEqual(service.guard_count, 2)
        self.assertEqual(len(driver.calls), 1)
        self.assertEqual(result["status"], "native_stress_adjustment_observed")
        self.assertFalse(result["business_effects_verified"])
        self.assertFalse(result["full_product_acceptance_credit"])

    def test_profile_explicit_unavailable_is_not_readiness_or_business_success(self):
        service, driver = profile_fixture()
        driver.result = native_response(available=False)
        result = service.query_stress_adjustment(15, 1)
        self.assertEqual(result["status"], "native_stress_adjustment_unavailable")
        self.assertFalse(result["result"]["current_actor_stress_adjustment_ready"])

    def test_profile_requires_attachment_guard_and_current_paused_revision(self):
        for mode in ("attachment", "guard", "stale", "running"):
            service, driver = profile_fixture()
            if mode == "attachment": service._attach_result = None
            elif mode == "guard": service.guard = lambda: (_ for _ in ()).throw(RuntimeError("synthetic lease guard failed"))
            elif mode == "running": driver.frame["paused"] = False
            with self.subTest(mode=mode), self.assertRaises((ValueError, RuntimeError)):
                service.query_stress_adjustment(15, 2 if mode == "stale" else 1)
            self.assertEqual(driver.calls, [])


# These independently registered tools may coexist with the stress getter.
# Unknown additions still fail the frozen pre-interaction inventory count.
GAMEPLAY_COEXISTING_TOOLS = frozenset({
    "ck3_query_character_interaction_ordinary_v1",
    "ck3_initiate_character_interaction_ordinary_v1",
    "ck3_query_normal_exit_context_v1",
    "ck3_request_normal_exit_v1",
    "ck3_observe_normal_exit_v1",
})
PROFILE_COEXISTING_TOOLS = frozenset({
    "ck3_query_profile_character_interaction_ordinary_v1",
    "ck3_initiate_profile_character_interaction_ordinary_v1",
    "ck3_query_normal_exit_context_v1",
    "ck3_request_normal_exit_v1",
    "ck3_observe_profile_normal_exit_v1",
})


class SchemaTests(unittest.IsolatedAsyncioTestCase):
    async def probe(self, server, name, baseline_count, coexisting_tools, driver):
        from mcp import Client
        async with Client(server, cache=None) as client:
            rows = (await client.list_tools()).tools
            tool_names = {row.name for row in rows}
            self.assertEqual(len(tool_names), len(rows))
            self.assertEqual(len(tool_names - coexisting_tools), baseline_count)
            tool = next(tool for tool in rows if tool.name == name)
            schema = tool.input_schema
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(set(schema["properties"]), {"base_amount", "expected_revision"})
            self.assertEqual(set(schema["required"]), {"base_amount", "expected_revision"})
            amount = schema["properties"]["base_amount"]
            self.assertEqual((amount["type"], amount["minimum"], amount["maximum"]), ("integer", -300, 300))
            self.assertTrue(tool.annotations.read_only_hint)
            self.assertFalse(tool.annotations.destructive_hint)
            self.assertTrue(tool.annotations.idempotent_hint)
            args = {"base_amount": 15, "expected_revision": 1}
            for override in ({"base_amount": True}, {"base_amount": "15"}, {"base_amount": 15.0},
                             {"base_amount": -301}, {"base_amount": 301}, {"expected_revision": True},
                             {"expected_revision": -1}, {"expected_revision": 2**64},
                             {"actor": 7002}, {"address": 123}, {"modifier_index": 143},
                             {"option_cost": 15}, {"expected_revision": 2}):
                response = await client.call_tool(name, {**args, **override})
                self.assertTrue(response.is_error, str(response))
                self.assertEqual(driver.calls, [])
            response = await client.call_tool(name, args)
            self.assertFalse(response.is_error, str(response))
            self.assertEqual(len(driver.calls), 1)

    async def test_actual_gameplay_sdk_closed_schema_and_validation(self):
        from xar_autoplayer.bridge.mcp_server import create_server
        driver = SyntheticGetter()
        await self.probe(create_server(driver), "ck3_query_current_actor_stress_adjustment_v1", 158, GAMEPLAY_COEXISTING_TOOLS, driver)

    async def test_actual_profile_sdk_closed_schema_and_validation(self):
        import ck3_native_profile_mcp as profile
        service, driver = profile_fixture()
        await self.probe(profile.create_server(service), "ck3_query_profile_current_actor_stress_adjustment_v1", 16, PROFILE_COEXISTING_TOOLS, driver)


if __name__ == "__main__":
    unittest.main()
