"""One original whole-native shared-wire consumer; Root owns FIRST execution.

The synthetic transport supplies hello/paused scope and correlates request_id.
Only auto_turn's planner selection is fixed; its ordinary Service execution,
NativeDriver query, normalizers and all three registered MCP builders are real.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import threading
import traceback
import unittest
from unittest.mock import patch


_OPTIONS = None
_STEP = "query-army-strengths-v1"
_CASES = (
    "available-equal", "partial-equal", "unavailable-equal", "single-fallback",
    "absent-fallback", "unequal-fallback", "presence-fallback",
)
_ROUTES = ("ck3_query_army_strengths", "ck3_execute_step", "ck3_auto_turn")


def _json_bytes(value: object) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _readiness(value: object, prefix: str = "") -> dict[str, object]:
    result: dict[str, object] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if key == "ready" or key.endswith("_ready") or key == "readiness":
                result[path] = child
            result.update(_readiness(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.update(_readiness(child, f"{prefix}[{index}]"))
    return result


class _OriginalWholeEndpoint:
    pipe_name = r"\\.\pipe\xar-army-manager-shared-12004-fixture"

    def __init__(self, whole: dict[str, object]) -> None:
        self.whole = whole
        self.requests: list[dict[str, object]] = []
        self.delivered: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame, self.on_disconnect = on_frame, on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("production Driver did not start its endpoint")
        self.on_frame(deepcopy(frame))

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(deepcopy(request))
        if request.get("type") == "ping":
            self.publish({
                "type": "pong", "protocol_version": 1,
                "request_id": request["request_id"],
            })
            return
        if (request.get("type"), request.get("step")) != ("execute_step", _STEP):
            raise AssertionError(f"unexpected fixture transport request: {request}")
        delivered = deepcopy(self.whole)
        delivered["request_id"] = request["request_id"]
        self.delivered.append(deepcopy(delivered))
        self.publish(delivered)

    def close(self) -> None:
        if self.on_disconnect is not None:
            self.on_disconnect()


class ArmyManagerSharedRegisteredMcp12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_original_native_wholes_through_driver_service_and_three_mcp_routes(self) -> None:
        if _OPTIONS is None:
            raise RuntimeError("use this consumer's explicit source/native/output CLI")
        from xar_autoplayer.bridge.army_strengths_manager_shared_wire import (
            FIELD_NAMES, SHARED_KEY, expand_army_strengths_manager_inputs,
            pack_army_strengths_manager_inputs,
        )
        from xar_autoplayer.bridge import war_contract

        project = _OPTIONS.source_root.resolve() / "ck3_autonomous_player"
        if not project.is_dir():
            project = _OPTIONS.source_root.resolve()
        self.assertEqual(
            Path(war_contract.__file__).resolve(),
            project / "src/xar_autoplayer/bridge/war_contract.py",
        )
        native_dir = _OPTIONS.native_dir.resolve()
        output_dir = _OPTIONS.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "COMPOUND-RECEIPT.json"
        if report_path.exists():
            raise FileExistsError(report_path)
        report: dict[str, object] = {
            "status": "RUNNING", "source_root": str(_OPTIONS.source_root.resolve()),
            "native_dir": str(native_dir), "cases": [],
            "registered_routes": list(_ROUTES), "native_producer_reexecutions": 0,
            "native_body_rewrites": 0, "live_queries": 0,
            "synthetic_boundary": "hello/paused all-player scope/request_id; auto_turn planner selection only",
            "internal_full_semantics_retained": False,
            "prior_consumer_dir": str(_OPTIONS.prior_consumer_dir.resolve()) if _OPTIONS.prior_consumer_dir else None,
            "registered_calls_executed": 0, "registered_calls_reused": 0,
            "registered_calls_completed_this_attempt": 0,
            "registered_calls_first_successful_this_attempt": 0,
            "registered_calls_replayed_without_retained_result": 0,
            "registered_calls_retried_after_prior_harness_failure": 0,
            "registered_call_receipts": [],
        }

        def persist() -> None:
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )

        persist()
        first_shared = None
        try:
            for name in _CASES:
                legacy_path = native_dir / f"{name}-legacy.json"
                shared_path = native_dir / f"{name}-shared.json"
                legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
                shared = json.loads(shared_path.read_text(encoding="utf-8"))
                originals = deepcopy((legacy, shared))
                for whole in (legacy, shared):
                    self.assertEqual(
                        set(whole), {"type", "protocol_version", "request_id", "ok", "result"},
                    )
                    self.assertEqual(whole["type"], "command_result")
                    self.assertEqual(whole["protocol_version"], 1)
                    self.assertIs(whole["ok"], True)
                    self.assertEqual(whole["result"]["step"], _STEP)
                    self.assertIs(whole["result"]["accepted"], True)
                self.assertEqual(
                    expand_army_strengths_manager_inputs(shared["result"]), legacy["result"],
                )
                self.assertEqual(
                    pack_army_strengths_manager_inputs(legacy["result"]), shared["result"],
                )
                native_shared = SHARED_KEY in shared["result"]
                self.assertIs(native_shared, name in {
                    "available-equal", "partial-equal", "unavailable-equal",
                })
                if native_shared:
                    first_shared = first_shared or shared["result"]
                    self.assertLess(_json_bytes(shared["result"]), _json_bytes(legacy["result"]))
                    self.assertEqual(
                        set(shared["result"][SHARED_KEY]["fields"]), set(FIELD_NAMES),
                    )
                expected_scope = [{
                    "army_id": row["army_id"], "scope_role": row["scope_role"],
                    "war_ids": row["war_ids"],
                } for row in legacy["result"]["army_strengths"]]
                self.assertTrue(all(row["scope_role"] == "player" and row["war_ids"] == []
                                    for row in expected_scope))
                expected_rows = war_contract.normalize_army_strengths(
                    deepcopy(legacy["result"]["army_strengths"]), expected_scope=expected_scope,
                )
                route_receipts = []
                for route in _ROUTES:
                    baseline, baseline_receipt = await self._run_and_record_route(
                        legacy, route, expected_rows, output_dir, name, "legacy", report, persist,
                    )
                    observed, observed_receipt = await self._run_and_record_route(
                        shared, route, expected_rows, output_dir, name, "shared", report, persist,
                    )
                    self.assertEqual(observed, baseline)
                    self.assertEqual(_readiness(observed), _readiness(baseline))
                    route_receipts.append({
                        "registered_tool": route, "legacy": baseline_receipt,
                        "shared": observed_receipt,
                        "expanded_semantics_equal": True,
                        "readiness_entries_equal": len(_readiness(observed)),
                    })
                self.assertEqual((legacy, shared), originals)
                report["cases"].append({
                    "case": name, "legacy_packet": str(legacy_path),
                    "shared_packet": str(shared_path), "shared_native_bundle": native_shared,
                    "army_ids": [row["army_id"] for row in expected_rows],
                    "legacy_native_result_bytes": _json_bytes(legacy["result"]),
                    "shared_native_result_bytes": _json_bytes(shared["result"]),
                    "routes": route_receipts,
                })
                persist()
            self.assertIsNotNone(first_shared)
            self._check_codec_contract(first_shared)
            report["codec_contract"] = "presence/null, legacy fallback, detached copies, exact shared schema"
            report["internal_full_semantics_retained"] = True
            report["status"] = "GREEN"
        except BaseException:
            report["status"] = "RED"
            report["error"] = traceback.format_exc()
            raise
        finally:
            persist()

    async def _run_and_record_route(
        self, whole, route, expected_rows, output_dir, name, variant, report, persist,
    ):
        relative = Path(name) / route / variant
        prior = (_OPTIONS.prior_consumer_dir.resolve() / relative / "REGISTERED-CALL-RECEIPT.json"
                 if _OPTIONS.prior_consumer_dir else None)
        if prior is not None and prior.exists():
            saved = json.loads(prior.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "GREEN")
            self.assertEqual(saved["native_dir"], str(_OPTIONS.native_dir.resolve()))
            self.assertEqual((saved["case"], saved["registered_tool"], saved["wire_variant"]),
                             (name, route, variant))
            self.assertEqual(saved["query_sequence"], whole["result"]["query_sequence"])
            full, route_receipt = saved["expanded_result"], saved["route_receipt"]
            report["registered_calls_reused"] += 1
            report["registered_call_receipts"].append({
                "case": name, "registered_tool": route, "wire_variant": variant,
                "receipt": str(prior), "execution": "retained_actual03_successful_registered_call",
            })
            persist()
            return full, route_receipt
        retry = bool(_OPTIONS.prior_consumer_dir) and relative.as_posix() == (
            "presence-fallback/ck3_query_army_strengths/legacy"
        )
        report["registered_calls_executed"] += 1
        if retry:
            report["registered_calls_retried_after_prior_harness_failure"] += 1
        full, route_receipt = await self._run_route(
            whole, route, expected_rows, output_dir / relative,
        )
        receipt_path = output_dir / relative / "REGISTERED-CALL-RECEIPT.json"
        saved = {
            "status": "GREEN", "native_dir": str(_OPTIONS.native_dir.resolve()),
            "case": name, "registered_tool": route, "wire_variant": variant,
            "query_sequence": whole["result"]["query_sequence"],
            "expanded_result": full, "route_receipt": route_receipt,
        }
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(
            json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        report["registered_calls_completed_this_attempt"] += 1
        report["registered_calls_first_successful_this_attempt"] += 1
        report["registered_call_receipts"].append({
            "case": name, "registered_tool": route, "wire_variant": variant,
            "receipt": str(receipt_path), "execution": (
                "retry_of_registered_return_with_prior_harness_assertion_failure"
                if retry else "new_registered_call"
            ),
        })
        persist()
        return full, route_receipt

    async def _run_route(self, whole, route, expected_rows, state_dir):
        from xar_autoplayer.bridge.army_strengths_manager_shared_wire import (
            FIELD_NAMES, SHARED_KEY, expand_army_strengths_manager_inputs,
        )
        from xar_autoplayer.bridge.mcp_server import create_server
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.version_identity import CK3_12004
        from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_CAPABILITY

        watched = {
            ("mcp_server.py", route), ("native_driver.py", "execute_step"),
            ("native_driver.py", "_execute_army_strength_query"),
            ("war_contract.py", "_normalize_army_strength_row"),
            ("service.py", "query_army_strengths" if route == _ROUTES[0] else "execute_step"),
        }
        if route == "ck3_auto_turn":
            watched |= {("service.py", "auto_turn"), ("service.py", "_execute_planned_turn")}
        endpoint = _OriginalWholeEndpoint(whole)
        driver = None
        receipt = {"calls": [], "native_body_rewrites": 0}
        previous_profile, previous_thread_profile = sys.getprofile(), threading.getprofile()
        service_method = {
            "ck3_query_army_strengths": "query_army_strengths",
            "ck3_execute_step": "execute_step", "ck3_auto_turn": "auto_turn",
        }[route]

        def observe(frame, event, value):
            key = (Path(frame.f_code.co_filename).name, frame.f_code.co_name)
            if key not in watched:
                return
            if event == "call":
                receipt["calls"].append({"source": frame.f_code.co_filename, "function": key[1]})
                if key[0] == "service.py":
                    self.assertIs(type(frame.f_locals["self"]), GameplayBridgeService)
                    self.assertIs(frame.f_locals["self"].driver, driver)
            elif event == "return":
                if key == ("service.py", service_method):
                    receipt["service_result"] = deepcopy(value)
                if key == ("native_driver.py", "execute_step"):
                    receipt["driver_result"] = deepcopy(value)

        try:
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                state_dir=state_dir, episode_projection="native_campaign",
            )
            server = create_server(driver)
            self.assertIn(route, server._tool_manager._tools)
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 4242, "connection_generation": 1,
                "game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
                "capabilities": ["game.state.snapshot", QUERY_ARMY_STRENGTHS_CAPABILITY],
            })
            endpoint.publish({
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": "native:1", "revision": 1,
                "state": {
                    "phase": "map_hud", "date": "synthetic-current-not-live",
                    "date_raw": 10000, "speed": 1, "paused": True, "map_ready": True,
                    "history": [], "active_event": None, "pending_character_interaction": None,
                    "played_character": {"character_id": 29829, "alive": True},
                    "player_armies": [{
                        "army_id": row["army_id"], "controllable": True,
                        "owner_character_id": 29829, "current_province_id": 100,
                    } for row in expected_rows],
                    "active_wars": [],
                },
            })
            before = driver.take_snapshot()
            self.assertEqual(before["snapshot_id"], "native:1")
            self.assertEqual(before["native_revision"], 1)
            arguments = (
                {"army_ids": [row["army_id"] for row in expected_rows],
                 "expected_revision": before["revision"]}
                if route == "ck3_query_army_strengths"
                else {"step": _STEP, "expected_revision": before["revision"]}
            )
            # AnyIO reuses worker threads. setprofile() alone leaves a reused
            # worker running the previous route's observer/Driver closure.
            threading.setprofile_all_threads(observe)
            sys.setprofile(observe)
            if route == "ck3_auto_turn":
                planned = {
                    "snapshot_id": before["snapshot_id"], "revision": before["revision"],
                    "plan": {"selected_step": _STEP, "phase": "synthetic_army_query_selection"},
                }
                with patch.object(GameplayBridgeService, "plan_turn", autospec=True,
                                  return_value=planned) as select_plan:
                    result = await server.call_tool(route, {})
                select_plan.assert_called_once()
            else:
                result = await server.call_tool(route, arguments)
            self.assertIs(result.is_error, False)
            structured = result.structured_content
            self.assertIsInstance(structured, dict)
            full = (
                {**structured, "result": expand_army_strengths_manager_inputs(structured["result"])}
                if route == "ck3_auto_turn"
                else expand_army_strengths_manager_inputs(structured)
            )
            self.assertEqual(full, receipt["service_result"])
            semantic = full["result"] if route == "ck3_auto_turn" else full
            self.assertEqual(receipt["driver_result"]["army_strengths"], expected_rows)
            self.assertEqual(driver._army_strength_query["army_strengths"], expected_rows)
            self.assertNotIn(SHARED_KEY, receipt["driver_result"])
            self.assertNotIn(SHARED_KEY, semantic)
            for field in FIELD_NAMES:
                if (len(expected_rows) > 1 and isinstance(expected_rows[0].get(field), dict)
                        and isinstance(expected_rows[1].get(field), dict)):
                    self.assertIsNot(
                        driver._army_strength_query["army_strengths"][0][field],
                        driver._army_strength_query["army_strengths"][1][field],
                    )
            compact_semantic = structured["result"] if route == "ck3_auto_turn" else structured
            if SHARED_KEY in compact_semantic:
                self.assertLess(_json_bytes(compact_semantic), _json_bytes(semantic))
            self.assertEqual(len(result.content), 1)
            summary = json.loads(result.content[0].text)
            query_summary = summary["result"] if route == "ck3_auto_turn" else summary
            self.assertEqual(query_summary["army_ids"], [row["army_id"] for row in expected_rows])
            self.assertEqual(query_summary["query_sequence"], whole["result"]["query_sequence"])
            self.assertEqual(query_summary["status"], semantic["status"])
            self.assertEqual(query_summary["source"]["native_revision"], 1)
            self.assertEqual(query_summary["result_location"], "structuredContent")
            self.assertLess(len(result.content[0].text.encode("utf-8")), 4096)
            decoded = json.loads(result.model_dump_json(by_alias=True))
            self.assertEqual(decoded["structuredContent"], structured)
            executed = {(Path(item["source"]).name, item["function"])
                        for item in receipt["calls"]}
            self.assertTrue(watched <= executed, watched - executed)
            commands = [item for item in endpoint.requests if item["type"] == "execute_step"]
            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0]["expected_revision"], before["native_revision"])
            self.assertEqual(len(endpoint.delivered), 1)
            delivered = endpoint.delivered[0]
            self.assertEqual(delivered["result"], whole["result"])
            self.assertEqual(
                {key: value for key, value in delivered.items() if key != "request_id"},
                {key: value for key, value in whole.items() if key != "request_id"},
            )
            route_receipt = {
                "calls": receipt["calls"], "transport_requests": 1,
                "native_command_body_unchanged": True, "internal_full_rows_equal": True,
                "shared_mcp_bundle": SHARED_KEY in compact_semantic,
                "expanded_semantic_bytes": _json_bytes(semantic),
                "compact_structured_result_bytes": _json_bytes(compact_semantic),
                "summary_bytes": len(result.content[0].text.encode("utf-8")),
            }
            return full, route_receipt
        finally:
            threading.setprofile_all_threads(previous_thread_profile)
            sys.setprofile(previous_profile)
            if driver is not None:
                driver.close()

    def _check_codec_contract(self, shared):
        from xar_autoplayer.bridge.army_strengths_manager_shared_wire import (
            FIELD_NAMES, SHARED_KEY, expand_army_strengths_manager_inputs,
            pack_army_strengths_manager_inputs,
        )
        original = deepcopy(shared)
        detached = expand_army_strengths_manager_inputs(shared)
        attached = expand_army_strengths_manager_inputs(shared, detached=False)
        for field, value in shared[SHARED_KEY]["fields"].items():
            if isinstance(value, dict):
                self.assertIs(attached["army_strengths"][0][field], value)
                self.assertIsNot(detached["army_strengths"][0][field], value)
                self.assertIsNot(detached["army_strengths"][0][field],
                                 detached["army_strengths"][1][field])
        field = FIELD_NAMES[0]
        nullable = {"army_strengths": [{"army_id": 0, field: None}, {"army_id": 16777217, field: None}]}
        self.assertEqual(expand_army_strengths_manager_inputs(
            pack_army_strengths_manager_inputs(nullable)), nullable)
        self.assertNotIn(FIELD_NAMES[1], pack_army_strengths_manager_inputs(nullable)[SHARED_KEY]["fields"])
        for fallback in (
            {"army_strengths": []}, {"army_strengths": [{"army_id": 0, field: None}]},
            {"army_strengths": [{"army_id": 0}, {"army_id": 16777217}]},
            {"army_strengths": [{"army_id": 0, field: None}, {"army_id": 16777217}]},
            {"army_strengths": [{"army_id": 0, field: {}}, {"army_id": 16777217, field: None}]},
        ):
            self.assertIs(pack_army_strengths_manager_inputs(fallback), fallback)
            self.assertEqual(expand_army_strengths_manager_inputs(fallback), fallback)
            self.assertIsNot(expand_army_strengths_manager_inputs(fallback), fallback)
        malformed = []
        for version in (True, 2):
            candidate = deepcopy(shared)
            candidate[SHARED_KEY]["schema_version"] = version
            malformed.append(candidate)
        candidate = deepcopy(shared)
        candidate[SHARED_KEY]["extra"] = None
        malformed.append(candidate)
        candidate = deepcopy(shared)
        candidate[SHARED_KEY]["army_ids"].reverse()
        malformed.append(candidate)
        candidate = deepcopy(shared)
        candidate[SHARED_KEY]["army_ids"][1] = candidate[SHARED_KEY]["army_ids"][0]
        malformed.append(candidate)
        for fields in ({}, {"unrelated_family": {}}, {field: 7}):
            candidate = deepcopy(shared)
            candidate[SHARED_KEY]["fields"] = fields
            malformed.append(candidate)
        candidate = deepcopy(shared)
        candidate["army_strengths"][0][field] = None
        malformed.append(candidate)
        for candidate in malformed:
            with self.assertRaises(ValueError):
                expand_army_strengths_manager_inputs(candidate)
        self.assertEqual(shared, original)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--prior-consumer-dir", type=Path,
                        help="Retained actual03 complete call receipts; execute only missing presence-fallback calls")
    _OPTIONS = parser.parse_args()
    _project = _OPTIONS.source_root.resolve() / "ck3_autonomous_player"
    if not _project.is_dir():
        _project = _OPTIONS.source_root.resolve()
    _repository = _project.parent
    sys.path[0:0] = [str(_repository / "tools"), str(_repository / "ck3_workshop_mcp/src"),
                       str(_project / "src")]
    unittest.main(argv=[sys.argv[0]], verbosity=2)
