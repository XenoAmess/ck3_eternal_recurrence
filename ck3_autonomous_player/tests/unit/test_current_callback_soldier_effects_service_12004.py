"""One new source-shaped registered-Service compound; Root owns FIRST."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import FrameType
from typing import Literal, NotRequired, TypedDict
import unittest


RegimentSpec = tuple[int, int, int, bool, bool, int, int]


def _object(value: object) -> dict[str, object]:
    """Narrow the dynamic fixture/profiler JSON boundary without trusting casts."""
    if not isinstance(value, dict):
        raise AssertionError("expected a JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise AssertionError("expected string JSON object keys")
        result[key] = item
    return result


def _array(value: object) -> list[object]:
    if not isinstance(value, list):
        raise AssertionError("expected a JSON array")
    return list(value)


def _objects(value: object) -> list[dict[str, object]]:
    return [_object(item) for item in _array(value)]


def _integer(value: object) -> int:
    if type(value) is not int:
        raise AssertionError("expected a JSON integer")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError("expected a JSON string")
    return value


class _TraceEntry(TypedDict):
    source: str
    function: str


class _SceneReport(TypedDict):
    scene: str
    status: Literal["RED", "GREEN"]
    call_trace: list[_TraceEntry]
    source_shaped_native_envelope: dict[str, object]
    actual_driver_result: NotRequired[object]
    actual_service_result: NotRequired[object]
    registered_response: NotRequired[dict[str, object]]
    registered_result: NotRequired[dict[str, object]]
    driver_cache: NotRequired[dict[str, object]]
    transport_request: NotRequired[dict[str, object]]


class _Failure(TypedDict):
    type: str
    message: str


class _Report(TypedDict):
    schema: str
    status: Literal["RED", "GREEN"]
    sole_method: str
    registered_tool: str
    scene_count: int
    fixture_boundary: str
    compiled_native_producer: bool
    old_GREEN_replays: int
    live: bool
    actual_loss: bool
    actual_post_stage_current: None
    full_daily_supply_transition_ready: bool
    full_monthly_ready: bool
    scenes: list[_SceneReport]
    actual_registered_queries: NotRequired[int]
    actual_native_driver_queries: NotRequired[int]
    actual_service_queries: NotRequired[int]
    failure: NotRequired[_Failure]


class _CurrentCallbackEndpoint:
    """Supply whole source-shaped query bodies and correlate only the nonce."""

    pipe_name = r"\\.\pipe\source-current-callback-soldiers-not-live"

    def __init__(self) -> None:
        self.on_frame: Callable[[dict[str, object]], None] | None = None
        self.whole: dict[str, object] | None = None
        self.requests: list[dict[str, object]] = []
        self.delivered: list[dict[str, object]] = []

    def start(
        self,
        on_frame: Callable[[dict[str, object]], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("actual NativeDriver did not start the endpoint")
        self.on_frame(deepcopy(frame))

    def send(self, request: dict[str, object]) -> None:
        if request.get("type") == "ping":
            self.publish({"protocol_version": 1, "type": "pong",
                          "request_id": request["request_id"]})
            return
        if request.get("type") != "execute_step" or self.whole is None:
            raise AssertionError("fixture permits only the existing Army query")
        result = _object(self.whole["result"])
        if request.get("step") != result["step"]:
            raise AssertionError("fixture permits only the existing Army query")
        if request.get("army_strengths_profile") != result["army_strengths_profile"]:
            raise AssertionError("fixture profile must match the actual driver request")
        self.requests.append(deepcopy(request))
        response = deepcopy(self.whole)
        response["request_id"] = request["request_id"]
        self.delivered.append(deepcopy(response))
        self.publish(response)

    def transport_error(self) -> str | None:
        return None

    def close(self) -> None:
        pass


class CurrentCallbackSoldierEffectsService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_current_callback_budget_interleaves_conditional_soldier_stages(self) -> None:
        from test_current_callback_supply_risk_service_12004 import current_packet
        from test_native_bridge_driver import _army, _hello, _snapshot
        from xar_autoplayer.bridge.army_strengths_profile_contract import (
            ARMY_STRENGTHS_PROFILE_KEY, ARMY_OBSERVED_PHASE_COVERAGE_KEY,
            ORDINARY_CORE_PROFILE,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import (
            QUERY_ARMY_STRENGTHS_CAPABILITY, QUERY_ARMY_STRENGTHS_STEP,
        )

        self.assertEqual(sys.flags.optimize, 0)

        def packet(
            specs: Sequence[RegimentSpec], fraction: int = 40000, siege: int = 2, raid: int = 2,
        ) -> dict[str, object]:
            row = _object(current_packet())
            strength_template = _objects(row["regiment_strengths"])[0]
            data_template = _objects(row["regiment_replenishment_records_v1"])[0]
            strengths: list[dict[str, object]] = []
            data_rows: list[dict[str, object]] = []
            for index, (current, maximum, tier, eligible, skipped, physical, aliases) in enumerate(specs):
                regiment = 10 * (index + 1)
                strength = deepcopy(strength_template)
                strength.update(army_regiment_id=regiment, current_soldiers=current,
                                maximum_soldiers=maximum, siege_tier=tier,
                                maa_type_key=f"tier_{tier}", native_supply_loss_eligible=eligible)
                data = deepcopy(data_template)
                data.update(army_regiment_id=regiment, native_data_record_count=aliases,
                            native_loss_writer_skipped=skipped)
                record = _objects(data["records"])[0]
                record.update(persistent_regiment_id=100 + regiment, chunk_index=0,
                              chunk_army_regiment_id=regiment, current_soldiers=physical,
                              effective_current_soldiers=physical,
                              maximum_soldiers=maximum // aliases, state_raw=0)
                data["records"] = [{**deepcopy(record), "record_index": i} for i in range(aliases)]
                strengths.append(strength)
                data_rows.append(data)
            row.update(regiment_count=len(strengths), regiment_strengths=strengths,
                       regiment_replenishment_records_v1=data_rows,
                       current_soldiers=sum(_integer(item["current_soldiers"]) for item in strengths),
                       maximum_soldiers=sum(_integer(item["maximum_soldiers"]) for item in strengths),
                       current_attrition_fraction_raw=0)
            monthly_inputs = _object(row["monthly_loss_budget_inputs_v1"])
            monthly_inputs.update(
                loaded_supply_state_levels=[7, 0], loaded_supply_state_fractions_raw=[0, fraction],
                commander_valid=False, commander_supply_modifier_id=None,
                commander_supply_modifier_raw=None)
            row["monthly_loss_budget_inputs_v1"] = monthly_inputs
            loss_inputs = _object(row["loss_application_inputs_v1"])
            loss_inputs.update(
                whole_soldiers=row["current_soldiers"],
                definition_le_zero_soldiers=sum(_integer(item["current_soldiers"]) for item in strengths
                                               if _integer(item["siege_tier"]) <= 0),
                supply_eligible_soldiers=sum(_integer(item["current_soldiers"]) for item in strengths
                                             if item["native_supply_loss_eligible"]),
                definition_le_zero_supply_eligible_soldiers=sum(
                    _integer(item["current_soldiers"]) for item in strengths
                    if _integer(item["siege_tier"]) <= 0 and item["native_supply_loss_eligible"]),
                current_supply_loss_budget=0, siege_loss_budget=siege, raid_loss_budget=raid,
                siege_active=siege > 0, raid_active=raid > 0,
                raid_association_id=0 if raid > 0 else -1,
                siege_rate_raw=25000 if siege else 0, raid_rate_raw=25000 if raid else 0)
            row["loss_application_inputs_v1"] = loss_inputs
            return row

        ordinary: tuple[RegimentSpec, ...] = ((1, 1, 0, True, False, 1, 1),
                    (4, 4, 1, True, False, 4, 1),
                    (3, 3, 0, False, False, 3, 1))
        main = packet(ordinary)
        alias = packet(((4, 4, 0, True, False, 2, 2),), fraction=50000, siege=0, raid=0)
        skipped = packet(((1, 1, 0, True, True, 1, 1),), fraction=100000, siege=0, raid=0)
        zero = packet(ordinary)
        zero.update(current_supply_raw=None, current_supply_capacity_raw=None,
                    current_supply_change_monthly_raw=None)
        zero_monthly_inputs = _object(zero["monthly_loss_budget_inputs_v1"])
        zero_monthly_inputs.update(
            status="unavailable", ready=False, unavailable_reason="unused_stock_inputs_unavailable",
            unit_native_170_raw=3, loaded_supply_state_levels=None,
            loaded_supply_state_fractions_raw=None)
        zero["monthly_loss_budget_inputs_v1"] = zero_monthly_inputs
        missing = packet(ordinary)
        missing.pop("regiment_replenishment_records_v1")
        scenes: tuple[tuple[str, dict[str, object], int, int | None, int | None, int | None], ...] = (
                  ("crossed-stock-four-pass", main, 2, 2, -6, 4),
                  ("physical-alias-reload", alias, 2, 0, -2, 4),
                  ("character-writer-skipped", skipped, 1, 1, 0, 1),
                  ("known-zero-unused-stock", zero, 0, 4, -4, 4),
                  ("positive-budget-missing-DATA", missing, 2, None, None, None))
        report: _Report = {
            "schema": "xar.current-callback-soldier-effects12004.registered-service.v1",
            "status": "RED", "sole_method": self._testMethodName,
            "registered_tool": "ck3_query_army_strengths", "scene_count": 5,
            "fixture_boundary": "New source-shaped whole query envelopes; original native reader not executed.",
            "compiled_native_producer": False, "old_GREEN_replays": 0,
            "live": False, "actual_loss": False, "actual_post_stage_current": None,
            "full_daily_supply_transition_ready": False, "full_monthly_ready": False,
            "scenes": [],
        }

        def persist() -> None:
            if target := os.environ.get("XAR_CURRENT_CALLBACK_SOLDIER_EFFECTS_FIRST_OUTPUT"):
                path = Path(target)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

        active: _SceneReport | None = None
        interesting = {
            ("mcp_server.py", "ck3_query_army_strengths"),
            ("service.py", "query_army_strengths"),
            ("native_driver.py", "query_army_strengths"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("native_driver.py", "_execute_primitive_step"),
            ("war_contract.py", "normalize_army_strengths"),
            ("army_current_callback_supply_risk_projection.py", "project_current_callback_supply_risk_v1"),
            ("army_current_callback_soldier_effects_projection.py", "project_current_callback_soldier_effects_v1"),
            ("army_loss_sequence_replay.py", "project_conditional_army_loss_sequence"),
            ("army_chunk_loss_writeback_projection.py", "project_observed_writer_chunk_changes"),
            ("army_regiment_refresh_projection.py", "project_observed_raised_regiment_refresh"),
        }

        def observe(frame: FrameType, event: str, value: object) -> None:
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if key not in interesting or active is None:
                return
            if event == "call":
                active["call_trace"].append({"source": frame.f_code.co_filename, "function": key[1]})
                if key == ("service.py", "query_army_strengths"):
                    self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                    self.assertIs(frame.f_locals["self"].driver, driver)
                elif key == ("native_driver.py", "query_army_strengths"):
                    self.assertIs(type(frame.f_locals["self"]), NativeHeadlessGameplayDriver)
                    self.assertIs(frame.f_locals["self"], driver)
                    self.assertIs(frame.f_code, NativeHeadlessGameplayDriver.query_army_strengths.__code__)
            elif event == "return" and key == ("native_driver.py", "query_army_strengths"):
                active["actual_driver_result"] = deepcopy(value)
            elif event == "return" and key == ("service.py", "query_army_strengths"):
                active["actual_service_result"] = deepcopy(value)

        prior_profile, prior_thread_profile = sys.getprofile(), threading.getprofile()
        endpoint = _CurrentCallbackEndpoint()
        driver: NativeHeadlessGameplayDriver | None = None
        persist()
        try:
            with tempfile.TemporaryDirectory(prefix="current-callback-soldiers-") as temp:
                driver = NativeHeadlessGameplayDriver(
                    endpoint=endpoint, state_dir=Path(temp) / "state", save_dir=Path(temp) / "unused-save",
                    command_timeout_seconds=0.1, episode_projection="native_campaign")
                hello = _hello("bridge.heartbeat", "game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY)
                hello.update(game_version=CK3_12004.game_version,
                             executable_sha256=CK3_12004.executable_sha256)
                endpoint.publish(hello)
                server = create_server(driver)
                sys.setprofile(observe)
                threading.setprofile(observe)
                for index, (name, source, budget, final, delta, old_final) in enumerate(scenes, 1):
                    with self.subTest(scene=name):
                        original = deepcopy(source)
                        endpoint.whole = {
                            "type": "command_result", "protocol_version": 1,
                            "request_id": f"authored-{name}", "ok": True,
                            "result": {"step": QUERY_ARMY_STRENGTHS_STEP, "accepted": True,
                                       "status": "available", "query_sequence": index,
                                       ARMY_STRENGTHS_PROFILE_KEY: ORDINARY_CORE_PROFILE,
                                       ARMY_OBSERVED_PHASE_COVERAGE_KEY: "not_requested",
                                       "army_strengths": [deepcopy(source)]},
                        }
                        authority = deepcopy(endpoint.whole)
                        endpoint.publish(_snapshot(
                            revision=index, date_raw=264,
                            played_character={"character_id": 29829, "alive": True, "name": "Robert"},
                            player_armies=[_army(0, soldiers=_integer(source["current_soldiers"]), owner_character_id=29829)],
                            active_wars=[]))
                        before = driver.take_snapshot()
                        active = {"scene": name, "status": "RED", "call_trace": [],
                                  "source_shaped_native_envelope": authority}
                        report["scenes"].append(active)
                        response = await server.call_tool("ck3_query_army_strengths", {
                            "army_ids": [0], "expected_revision": before["revision"]})
                        active["registered_response"] = response.model_dump(mode="json", by_alias=True)
                        self.assertIs(response.is_error, False)
                        self.assertIsInstance(response.structured_content, dict)
                        summary = _object(response.structured_content)
                        service_result = active["actual_service_result"]
                        self.assertIsInstance(service_result, dict)
                        result = _object(service_result)
                        summary_fields = (
                            "status", "army_id", "native_carmy_id", "regiment_count",
                            "current_soldiers", "maximum_soldiers", "ai_base_power_raw",
                            "ai_base_power_scale", "current_supply_raw", "current_supply_scale",
                            "current_attrition_fraction_raw", "current_attrition_fraction_scale",
                            "unavailable_reason",
                        )
                        result_source = _object(result["source"])
                        driver_value = active["actual_driver_result"]
                        self.assertIsInstance(driver_value, dict)
                        driver_result = _object(driver_value)
                        self.assertIs(driver_result["accepted"], True)
                        self.assertEqual(driver_result["status"], "available")
                        self.assertEqual(driver_result["step"], QUERY_ARMY_STRENGTHS_STEP)
                        self.assertEqual(driver_result["query_sequence"], index)
                        for identity_key in ("snapshot_id", "revision", "native_revision", "date_raw"):
                            self.assertEqual(driver_result["queried_" + identity_key], result_source[identity_key])
                        for binding_key in ("queried_connection_generation", "queried_episode_run_id"):
                            self.assertEqual(driver_result[binding_key], result[binding_key])
                        driver_army = _objects(driver_result["army_strengths"])[0]
                        for raw_key, value in original.items():
                            self.assertEqual(driver_army[raw_key], value, raw_key)
                        expected_summary: dict[str, object] = {
                            "accepted": True, "status": "available", "query_sequence": index,
                            ARMY_STRENGTHS_PROFILE_KEY: ORDINARY_CORE_PROFILE,
                            ARMY_OBSERVED_PHASE_COVERAGE_KEY: "not_requested",
                            "source": {"revision": result_source["revision"],
                                       "native_revision": result_source["native_revision"]},
                            "army_ids": [0],
                            "armies": [{field: row.get(field) for field in summary_fields}
                                       for row in _objects(result["army_strengths"])],
                            "result_location": "compact_mcp_summary",
                        }
                        native_timing = result.get("army_native_timing_v1")
                        if native_timing is not None:
                            self.assertIsInstance(native_timing, dict)
                            timing = _object(native_timing)
                            self.assertEqual(set(timing), {
                                "read_total_ns", "owner_query_ns", "baseline_read_ns",
                                "rich_attach_ns", "serialize_ns",
                            })
                            for timing_value in timing.values():
                                self.assertIs(type(timing_value), int)
                                self.assertGreaterEqual(_integer(timing_value), 0)
                            self.assertLessEqual(max(_integer(timing["baseline_read_ns"]),
                                                     _integer(timing["rich_attach_ns"])),
                                                 _integer(timing["owner_query_ns"]))
                            self.assertLessEqual(_integer(timing["owner_query_ns"]),
                                                 _integer(timing["read_total_ns"]))
                            expected_summary["army_native_timing_v1"] = native_timing
                        self.assertEqual(summary, expected_summary)
                        self.assertEqual(len(_array(summary["armies"])), 1)
                        self.assertEqual(_object(summary["source"])["native_revision"], index)
                        self.assertEqual(response.model_dump(mode="json", by_alias=True)["structuredContent"], summary)
                        self.assertEqual(len(response.content), 1)
                        self.assertEqual(response.content[0].type, "text")
                        self.assertEqual(json.loads(response.content[0].text), summary)
                        self.assertEqual(result_source["game_version"], "1.20.0.4")
                        self.assertEqual(_text(result_source["executable_sha256"]).upper(), CK3_12004.executable_sha256.upper())
                        self.assertEqual(result["queried_native_revision"], index)
                        self.assertEqual(len(endpoint.requests), index)
                        self.assertEqual(endpoint.requests[-1]["expected_revision"], index)
                        self.assertEqual(endpoint.delivered[-1]["result"], authority["result"])
                        self.assertEqual(endpoint.whole, authority)
                        self.assertEqual(source, original)
                        result_army = _objects(result["army_strengths"])[0]
                        driver_cache = _object(driver._army_strength_query)
                        cached_army = _objects(driver_cache["army_strengths"])[0]
                        for raw_key, value in original.items():
                            self.assertEqual(result_army[raw_key], value, raw_key)
                        cache_core_fields = (
                            "status", "army_id", "native_carmy_id", "scope_role", "war_ids",
                            "regiment_count", "current_soldiers", "maximum_soldiers",
                            "ai_base_power_raw", "ai_base_power_scale", "unavailable_reason",
                        )
                        self.assertEqual(set(cached_army), set(cache_core_fields))
                        for core_key in cache_core_fields:
                            self.assertEqual(cached_army[core_key], original[core_key], core_key)
                        effects = _object(_objects(result["current_callback_soldier_effects_v1"])[0]["projection"])
                        risk = _object(_objects(result["current_callback_supply_risk_v1"])[0]["projection"])
                        sequence = _object(effects["conditional_loss_sequence_v1"])
                        self.assertEqual(effects["source_contract_game_version"], "1.20.0.4")
                        self.assertEqual(effects["source_entries"], {
                            "caller": "24E3410", "writer": "2634190", "record_selector": "260DB50",
                            "current_setter": "2657E80", "raised_refresh": "2633320", "residual_allocator": "2A957E0"})
                        self.assertEqual(sequence["source_contract_game_version"], "1.20.0.3")
                        self.assertIs(effects["conditional_supply_budget_ready"], True)
                        self.assertEqual(effects["conditional_supply_budget_soldiers"], budget)
                        self.assertEqual(effects["observed_current_supply_budget_soldiers"], 0)
                        source_loss_inputs = _object(source["loss_application_inputs_v1"])
                        self.assertEqual((effects["observed_siege_budget_soldiers"], effects["observed_raid_budget_soldiers"]),
                                         (source_loss_inputs["siege_loss_budget"], source_loss_inputs["raid_loss_budget"]))
                        self.assertEqual(sequence["conditional_final_current_soldiers"], final)
                        self.assertEqual(sequence["conditional_physical_current_delta"], delta)
                        self.assertIs(effects["conditional_soldier_effects_ready"], final is not None)
                        self.assertIs(effects["ready"], final is not None)
                        allocation = _objects(result["loss_allocation_requests_v1"])[0]
                        self.assertEqual(_object(allocation["same_input_conditional_loss_sequence_v1"])["conditional_final_current_soldiers"], old_final)
                        self.assertIs(allocation["applied_loss_ready"], False)
                        self.assertIsNone(allocation["applied_soldier_loss"])
                        self.assertIs(sequence["actual_loss"], False)
                        self.assertIsNone(sequence["actual_post_stage_current"])
                        for key in ("actual_callback_observed", "actual_loss", "earlier_stage_outputs_reconstructed",
                                    "future_callback_selection_ready", "full_daily_supply_transition_ready", "full_monthly_ready"):
                            self.assertIs(effects[key], False, key)
                        self.assertIsNone(effects["actual_post_stage_current"])
                        phases = _objects(sequence["passes"])
                        if name == "crossed-stock-four-pass":
                            self.assertEqual(risk["conditional_post_stock_raw"], 650000)
                            self.assertEqual(risk["observed_subject_callback_positions"], [1, 3])
                            self.assertEqual([stage["phase"] for stage in phases], [
                                "supply_preferred", "supply_residual", "siege_raid_preferred", "siege_raid_residual"])
                            self.assertEqual([stage["native_filter_flags"] for stage in phases], [3, 2, 1, 0])
                            self.assertEqual([stage["request_budget_soldiers"] for stage in phases], [2, 1, 4, 1])
                            self.assertEqual([stage["native_eligible_total_soldiers"] for stage in phases], [1, 4, 3, 3])
                            self.assertEqual([[request["requested_soldiers"] for request in _objects(stage["requests"])] for stage in phases],
                                             [[1], [0, 1], [0, 3], [0, 1]])
                            self.assertEqual([item["current_soldiers"] for item in _objects(sequence["conditional_final_regiment_strengths"])], [0, 2, 0])
                        elif name == "physical-alias-reload":
                            writer = _object(_objects(phases[0]["requests"])[0]["conditional_chunk_writeback"])
                            self.assertEqual(writer["physical_current_delta"], -2)
                            self.assertEqual(_object(writer["conditional_raised_regiment_refresh"])["current_soldiers"], 0)
                            self.assertEqual([(write["pass"], write["current_before"], write["current_after"]) for write in _objects(writer["writes"])],
                                             [(1, 2, 0), (2, 0, 0)])
                            self.assertEqual(len(_array(sequence["conditional_physical_chunks_after"])), 1)
                        elif name == "character-writer-skipped":
                            request = _objects(phases[0]["requests"])[0]
                            self.assertEqual(request["requested_soldiers"], 1)
                            writer = _object(request["conditional_chunk_writeback"])
                            self.assertIs(writer["writer_skipped"], True)
                            self.assertIs(writer["refresh_requested"], False)
                            self.assertEqual(_object(writer["conditional_raised_regiment_refresh"])["status"], "not_called")
                        elif name == "known-zero-unused-stock":
                            self.assertIs(risk["ready"], False)
                            self.assertIs(risk["conditional_callback_admitted"], False)
                            self.assertEqual(risk["admission_rejection"], "unit_native_170_raw")
                            self.assertIs(effects["conditional_post_stock_ready"], False)
                            self.assertIsNone(effects["conditional_post_stock_raw"])
                            self.assertEqual(effects["missing_inputs"], [])
                        else:
                            self.assertEqual(effects["status"], "partial")
                            self.assertEqual(sequence["status"], "partial")
                            self.assertIs(sequence["conditional_sequence_ready"], False)
                            self.assertIsNone(sequence["conditional_final_regiment_strengths"])
                            self.assertEqual(effects["missing_inputs"], [{
                                "phase": "supply_preferred", "army_regiment_id": 10,
                                "inputs": ["matching_native_regiment_and_DATA"]}])
                        executed = {(Path(item["source"]).name, item["function"]) for item in active["call_trace"]}
                        reached = interesting - ({("army_regiment_refresh_projection.py", "project_observed_raised_regiment_refresh")}
                                                 if name in {"character-writer-skipped", "positive-budget-missing-DATA"} else set())
                        self.assertTrue(reached <= executed)
                        self.assertEqual(sum(item["function"] == "project_current_callback_supply_risk_v1"
                                             for item in active["call_trace"]), 1)
                        self.assertEqual(sum((Path(item["source"]).name, item["function"])
                                             == ("service.py", "query_army_strengths")
                                             for item in active["call_trace"]), 1)
                        self.assertEqual(sum((Path(item["source"]).name, item["function"])
                                             == ("native_driver.py", "query_army_strengths")
                                             for item in active["call_trace"]), 1)
                        active["status"] = "GREEN"
                        active["registered_result"] = summary
                        active["driver_cache"] = deepcopy(driver_cache)
                        active["transport_request"] = deepcopy(endpoint.requests[-1])
                        persist()
                self.assertEqual(len(report["scenes"]), 5)
                self.assertTrue(all(scene["status"] == "GREEN" for scene in report["scenes"]))
                self.assertEqual(len(endpoint.requests), 5)
                report["status"] = "GREEN"
                report["actual_registered_queries"] = 5
                report["actual_native_driver_queries"] = 5
                report["actual_service_queries"] = 5
        except BaseException as error:
            report["failure"] = {"type": type(error).__name__, "message": str(error)}
            raise
        finally:
            sys.setprofile(prior_profile)
            threading.setprofile(prior_thread_profile)
            if driver is not None:
                driver.close()
            persist()


if __name__ == "__main__":
    unittest.main()
