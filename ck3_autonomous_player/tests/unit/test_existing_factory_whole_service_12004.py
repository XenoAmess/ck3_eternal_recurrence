"""First .4 existing-factory whole producer -> real Service -> registered MCP.

Launch this one compound explicitly with --source-root, --native-wire and
--output-dir. Native result bodies come directly from the compiled producer.
Only hello, paused scope and outer request correlation are synthetic.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
import unittest

_CONFIG: dict[str, Path] | None = None
_ORDER = ("before", "assignment", "after")
_FRAME_KEYS = {"type", "protocol_version", "request_id", "ok", "result"}
_QUERY_KEYS = {
    "step", "accepted", "status", "read_only", "query_sequence",
    "snapshot_revision", "date_raw", "army_commander_candidates",
}
_ASSIGNMENT_KEYS = {
    "step", "accepted", "status", "read_only", "command_sequence",
    "snapshot_revision", "date_raw", "army_commander_assignment",
}
_REQUEST_IDS = {
    "before": "existing-factory-before",
    "assignment": "existing-factory-assignment",
    "after": "existing-factory-after",
}


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class _CompiledWholeEndpoint:
    """Offline endpoint; it serves three untouched compiled result bodies."""

    pipe_name = r"\\.\pipe\offline-existing-factory-whole-12004"

    def __init__(
        self, frames: dict[str, dict[str, object]],
        state_frame: dict[str, object],
        capabilities: list[str],
    ) -> None:
        self.frames = frames
        self.state_frame = state_frame
        self.capabilities = capabilities
        self.requests: list[dict[str, object]] = []
        self.correlations: list[dict[str, object]] = []
        self._on_frame = None
        self._on_disconnect = None
        self.closed = False

    def start(self, on_frame, on_disconnect) -> None:
        self._on_frame = on_frame
        self._on_disconnect = on_disconnect
        on_frame({
            "type": "hello",
            "protocol_version": 1,
            "pid": 12004,
            "connection_generation": 1,
            "capabilities": self.capabilities,
        })
        on_frame(copy.deepcopy(self.state_frame))

    def send(self, request: dict[str, object]) -> None:
        index = len(self.requests)
        if index >= len(_ORDER):
            raise AssertionError("unexpected fourth native command")
        name = _ORDER[index]
        native = self.frames[name]
        result = native["result"]
        if (
            set(request) != {
                "type", "protocol_version", "request_id", "step",
                "expected_revision",
            }
            or request["type"] != "execute_step"
            or request["protocol_version"] != 1
            or request["step"] != result["step"]
            or request["expected_revision"] != result["snapshot_revision"]
            or not isinstance(request["request_id"], str)
            or not request["request_id"]
        ):
            raise AssertionError(f"{name} request differs from the real primitive contract")
        self.requests.append(copy.deepcopy(request))
        self.correlations.append({
            "packet": name,
            "producer_request_id": native["request_id"],
            "transport_request_id": request["request_id"],
        })
        # Correlate the outer nonce only; the compiled result is unmodified.
        response = {**native, "request_id": request["request_id"]}
        self._on_frame(response)

    def close(self) -> None:
        self.closed = True
        if self._on_disconnect is not None:
            self._on_disconnect()


class ExistingFactoryWholeService12004Tests(unittest.IsolatedAsyncioTestCase):
    async def test_first_whole_commander_assignment_preserves_pending_through_registered_mcp(self) -> None:
        if _CONFIG is None:
            raise RuntimeError("use the explicit source-root/native-wire/output-dir launcher")
        source_root = _CONFIG["source_root"]
        native_wire = _CONFIG["native_wire"]
        output_dir = _CONFIG["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "FIRST-EXISTING-FACTORY-WHOLE-SERVICE-12004.json"
        report: dict[str, object] = {
            "schema": "xar.existing-factory-whole-service-12004.first.v1",
            "date": "2026-10-07",
            "iso_week": "2026-W41",
            "status": "RUNNING",
            "source_root": str(source_root),
            "native_wire": str(native_wire),
            "active_phase": "read_compiled_whole_packet",
            "boundary": (
                "Compiled .4 factory binding and genuine native executor/serializers; "
                "native callbacks/storage and endpoint hello/paused scope are synthetic. "
                "No native image execution, CK3 live assignment or applied-state claim."
            ),
        }
        _write_json(report_path, report)
        driver = None
        endpoint = None
        try:
            bundle = json.loads(native_wire.read_text(encoding="utf-8-sig"))
            self.assertEqual(set(bundle), {"schema_version", "scene_order", "samples"})
            self.assertIs(type(bundle["schema_version"]), int)
            self.assertEqual(bundle["schema_version"], 1)
            self.assertEqual(bundle["scene_order"], list(_ORDER))
            frames = bundle["samples"]
            self.assertEqual(set(frames), set(_ORDER))
            frozen_bundle = copy.deepcopy(bundle)
            for name in _ORDER:
                frame = frames[name]
                self.assertEqual(set(frame), _FRAME_KEYS)
                self.assertEqual(frame["type"], "command_result")
                self.assertIs(type(frame["protocol_version"]), int)
                self.assertEqual(frame["protocol_version"], 1)
                self.assertEqual(frame["request_id"], _REQUEST_IDS[name])
                self.assertIs(frame["ok"], True)
                self.assertIsInstance(frame["result"], dict)
            before_native = frames["before"]["result"]
            assignment_native = frames["assignment"]["result"]
            after_native = frames["after"]["result"]
            self.assertEqual(set(before_native), _QUERY_KEYS)
            self.assertEqual(set(after_native), _QUERY_KEYS)
            self.assertEqual(set(assignment_native), _ASSIGNMENT_KEYS)
            self.assertEqual(before_native["query_sequence"], 1)
            self.assertEqual(after_native["query_sequence"], 2)
            self.assertEqual(assignment_native["command_sequence"], 1)
            for name in _ORDER:
                result = frames[name]["result"]
                self.assertIs(result["accepted"], True)
                self.assertEqual(result["snapshot_revision"], 7)
                self.assertEqual(result["date_raw"], 10000)
                self.assertIs(
                    result["read_only"], name != "assignment",
                )
            self.assertEqual(before_native["status"], "completed")
            self.assertEqual(after_native["status"], "completed")
            self.assertEqual(
                assignment_native["status"], "submitted_verification_pending",
            )
            assignment_leaf = assignment_native["army_commander_assignment"]
            before_leaf = before_native["army_commander_candidates"]
            after_leaf = after_native["army_commander_candidates"]
            self.assertEqual(
                assignment_leaf["schema"], "ck3_12003_army_commander_assignment_v1",
            )
            self.assertEqual(assignment_leaf["status"], "submitted")
            army_id = assignment_leaf["army_id"]
            commander_id = assignment_leaf["requested_commander_character_id"]
            owner_id = assignment_leaf["owner_character_id"]
            native_army_id = assignment_leaf["native_carmy_id"]
            for value in (army_id, commander_id, owner_id, native_army_id):
                self.assertIs(type(value), int)
                self.assertGreaterEqual(value, 0)
            self.assertEqual(
                (owner_id, army_id, native_army_id, commander_id),
                (29829, 83886367, 50331794, 34333),
            )
            self.assertNotEqual(army_id, native_army_id)
            for leaf in (before_leaf, after_leaf):
                self.assertEqual(leaf["army_id"], army_id)
                self.assertEqual(leaf["native_carmy_id"], native_army_id)
                self.assertEqual(leaf["owner_character_id"], owner_id)
                self.assertEqual(leaf["snapshot_revision"], 7)
                self.assertEqual(leaf["date_raw"], 10000)
                self.assertEqual(
                    leaf["schema"], "ck3_12004_army_commander_candidates_v1",
                )
                self.assertIs(leaf["candidate_collection_complete"], True)
                self.assertEqual(leaf["candidate_source_count"], 2)
                self.assertEqual(
                    [row["character_id"] for row in leaf["candidates"]],
                    [34333, 34334],
                )
                self.assertEqual(
                    [row["can_assign"] for row in leaf["candidates"]],
                    [True, False],
                )
                self.assertEqual(
                    [row["native_ai_base_quality"] for row in leaf["candidates"]],
                    [125, 90],
                )
                for candidate in leaf["candidates"]:
                    self.assertIs(candidate["available"], True)
                    self.assertIs(candidate["final_eligibility_observable"], True)
                    self.assertIs(candidate["quality_observable"], True)
                self.assertEqual(leaf["current_commander"]["status"], "absent")
                self.assertIsNone(leaf["current_commander"]["character_id"])
                martial = leaf["current_commander"]["current_total_martial"]
                self.assertEqual(martial, {
                    "status": "unavailable",
                    "source": "native_current_assigned_commander_total_skill_cache",
                    "source_character_id": None,
                    "skill_index": 1,
                    "value": None,
                    "unavailable_reason": "current_commander_absent",
                })
                movement = leaf["current_movement_speed"]
                for name in ("land", "naval"):
                    self.assertEqual(movement[name]["status"], "available")
                    self.assertIs(type(movement[name]["raw"]), int)
                    self.assertEqual(movement[name]["raw"], 0)
                self.assertEqual(movement["route_read_status"], "complete_empty")
                self.assertEqual(movement["current_edge"]["status"], "not_applicable")
                self.assertIsNone(movement["current_edge"]["raw"])
                self.assertEqual(
                    movement["current_edge"]["unavailable_reason"], "empty_route",
                )
            self.assertEqual(
                before_leaf["current_commander"], after_leaf["current_commander"],
            )
            self.assertEqual(
                before_leaf["current_commander"]["character_id"],
                assignment_leaf["prior_commander_character_id"],
            )
            self.assertNotEqual(
                after_leaf["current_commander"]["character_id"], commander_id,
            )
            for field in (
                "final_eligibility_observable", "can_assign",
                "native_command_validation_observable", "native_command_valid",
                "command_submitted", "verification_pending",
            ):
                self.assertIs(assignment_leaf[field], True)
            self.assertIsNone(assignment_leaf["unavailable_reason"])

            report["active_phase"] = "construct_real_driver_and_service"
            _write_json(report_path, report)
            sys.path.insert(0, str(source_root / "src"))
            # First production imports occur only during Root's explicit run.
            from xar_autoplayer.bridge.army_commander_assignment import (
                ASSIGN_ARMY_COMMANDER_V1_CAPABILITY,
                assign_army_commander_v1_step,
            )
            from xar_autoplayer.bridge.army_commander_candidates import (
                QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
                query_army_commander_candidates_v1_step,
            )
            from xar_autoplayer.bridge.mcp_server import create_server
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService

            assignment_step = assign_army_commander_v1_step(army_id, commander_id)
            query_step = query_army_commander_candidates_v1_step(army_id)
            self.assertEqual(assignment_native["step"], assignment_step)
            self.assertEqual(before_native["step"], query_step)
            self.assertEqual(after_native["step"], query_step)
            state_frame = {
                "type": "state_snapshot",
                "protocol_version": 1,
                "snapshot_id": "synthetic-existing-factory-paused-scope-12004",
                "revision": 7,
                "state": {
                    "paused": True,
                    "speed": 0,
                    "date_raw": 10000,
                    "map_ready": True,
                    "played_character": {"character_id": owner_id, "alive": True},
                    "player_character_id": owner_id,
                    "active_wars": [],
                    "player_armies": [{
                        "army_id": army_id,
                        "owner_character_id": owner_id,
                        "controllable": True,
                    }],
                    "history": [],
                },
            }
            endpoint = _CompiledWholeEndpoint(
                frames, state_frame,
                [
                    "game.state.snapshot",
                    ASSIGN_ARMY_COMMANDER_V1_CAPABILITY,
                    QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
                ],
            )
            driver = NativeHeadlessGameplayDriver(
                endpoint=endpoint,
                pipe_name=endpoint.pipe_name,
                command_timeout_seconds=1.0,
                state_dir=output_dir / "isolated-driver-state",
                save_dir=output_dir / "isolated-saves",
                episode_projection="native_campaign",
            )
            service = GameplayBridgeService(driver)
            starting = service.snapshot()
            self.assertIs(starting["paused"], True)
            self.assertEqual(starting["native_revision"], 7)
            self.assertEqual(starting["date_raw"], 10000)
            public_revision = starting["revision"]
            report["active_phase"] = "genuine_compiled_before_through_service"
            _write_json(report_path, report)
            before = service.query_army_commander_candidates_v1(
                army_id, expected_revision=public_revision,
            )
            self.assertEqual(before["army_commander_candidates"], before_leaf)
            self.assertEqual(len(endpoint.requests), 1)

            report["active_phase"] = "registered_assignment_and_independent_after"
            _write_json(report_path, report)
            server = create_server(driver)
            mcp_result = await server.call_tool(
                "ck3_assign_army_commander_v1",
                {
                    "army_id": army_id,
                    "commander_character_id": commander_id,
                    "expected_revision": public_revision,
                },
            )
            mcp_wire = json.loads(mcp_result.model_dump_json(by_alias=True))
            self.assertIsNot(mcp_wire.get("isError"), True)
            receipt = mcp_wire["structuredContent"]
            self.assertIsInstance(receipt, dict)
            for key, value in assignment_native.items():
                self.assertEqual(receipt[key], value)
            self.assertEqual(receipt["backend_id"], "native-headless")
            self.assertEqual(receipt["submitted_revision"], public_revision)
            self.assertEqual(receipt["submitted_native_revision"], 7)
            self.assertEqual(
                receipt["submitted_snapshot_id"], starting["snapshot_id"],
            )
            self.assertEqual(receipt["status"], "submitted_verification_pending")
            self.assertEqual(
                receipt["native_submission_status"], "submitted_verification_pending",
            )
            self.assertIs(
                receipt["army_commander_assignment"]["verification_pending"], True,
            )
            verification = receipt["commander_assignment_verification"]
            self.assertEqual(verification["status"], "verification_pending")
            self.assertIs(verification["verified"], False)
            self.assertIs(verification["army_context_matches"], True)
            self.assertIs(verification["commander_matches"], False)
            self.assertEqual(
                verification["observed_commander_character_id"],
                after_leaf["current_commander"]["character_id"],
            )
            readback = receipt["commander_readback"]
            self.assertEqual(readback["army_commander_candidates"], after_leaf)
            for key, value in after_native.items():
                self.assertEqual(readback[key], value)
            self.assertEqual(len(endpoint.requests), 3)
            self.assertEqual(
                [request["step"] for request in endpoint.requests],
                [query_step, assignment_step, query_step],
            )
            self.assertEqual(
                [request["expected_revision"] for request in endpoint.requests],
                [7, 7, 7],
            )
            self.assertEqual(bundle, frozen_bundle)
            self.assertEqual(
                json.loads(native_wire.read_text(encoding="utf-8-sig")), frozen_bundle,
            )
            _write_json(output_dir / "service-before.json", before)
            _write_json(output_dir / "registered-assignment-mcp.json", mcp_wire)
            _write_json(output_dir / "endpoint-requests-and-correlations.json", {
                "requests": endpoint.requests,
                "correlations": endpoint.correlations,
                "native_result_bodies_unchanged": True,
            })
            report.update({
                "status": "GREEN",
                "active_phase": "complete",
                "native_packet_count": 3,
                "native_command_order": ["before", "assignment", "after"],
                "registered_tool_calls": 1,
                "assignment_submissions": 1,
                "independent_after_queries": 1,
                "public_revision_from_real_protocol_state": public_revision,
                "native_revision": 7,
                "native_result_bodies_unchanged": True,
                "observed_commander_unchanged": True,
                "verification_pending": True,
                "verified": False,
                "production_live": False,
            })
        except BaseException as error:
            report.update({
                "status": "RED",
                "error_type": type(error).__name__,
                "error": str(error),
            })
            raise
        finally:
            if driver is not None:
                try:
                    driver.close()
                except BaseException as error:
                    report.update({
                        "status": "RED",
                        "cleanup_error_type": type(error).__name__,
                        "cleanup_error": str(error),
                    })
                    _write_json(report_path, report)
                    raise
            report["endpoint_closed"] = endpoint.closed if endpoint is not None else None
            _write_json(report_path, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-wire", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args()
    _CONFIG = {
        "source_root": arguments.source_root.resolve(),
        "native_wire": arguments.native_wire.resolve(),
        "output_dir": arguments.output_dir.resolve(),
    }
    outcome = unittest.main(argv=[sys.argv[0]], verbosity=2, exit=False)
    raise SystemExit(0 if outcome.result.wasSuccessful() else 1)
