"""Focused offline registered submit/result chain using unchanged native leafs.

Native core and production serializer supply the Submission and independent
result. MCP registration, outer envelope and paused snapshot metadata are the
fixture boundary; no game, pipe, SDK invocation or window operation occurs.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


SUBMIT_TOOL = "ck3_submit_county_conversion_task"
RESULT_TOOL = "ck3_query_county_conversion_task_result"


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class ArgumentMetadata:
    def __init__(self) -> None:
        self.model_config: dict[str, object] = {}

    def model_rebuild(self, *, force: bool) -> None:
        pass

    def model_json_schema(self) -> dict[str, object]:
        return {"type": "object", "additionalProperties": self.model_config.get("extra") != "forbid"}


class CapturingSdkServer:
    def __init__(self, **kwargs: object) -> None:
        self._tool_manager = SimpleNamespace(_tools={})

    def tool(self, **kwargs: object):
        def register(function):
            self._tool_manager._tools[function.__name__] = SimpleNamespace(
                function=function, annotations=kwargs.get("annotations"),
                fn_metadata=SimpleNamespace(arg_model=ArgumentMetadata()),
            )
            return function
        return register

    def resource(self, uri: str):
        return lambda function: function


def install_sdk_stub() -> None:
    package = ModuleType("mcp")
    package.__path__ = []
    server = ModuleType("mcp.server")
    server.MCPServer = CapturingSdkServer
    types = ModuleType("mcp.types")
    types.ToolAnnotations = lambda **kwargs: SimpleNamespace(**kwargs)
    sys.modules.update({"mcp": package, "mcp.server": server, "mcp.types": types})


def run_case(projection: Path, source_root: Path, native_wire: Path, output: Path) -> dict[str, object]:
    install_sdk_stub()
    # File-only projections omit repository build helpers. Import those from the
    # explicit source root while all changed bridge code uses the projection.
    sys.path.insert(0, str(source_root / "tools"))
    sys.path.insert(0, str(projection / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
    from xar_autoplayer.bridge.version_identity import CK3_12003
    from xar_autoplayer.bridge.county_conversion_task_private_action_v1 import SUBMIT_STEP, RESULT_STEP

    frozen = native_wire.read_bytes()
    native = json.loads(frozen)
    submission, independent = native["submission"], native["independent_result"]
    request_id = submission["request_id"]
    if not request_id.startswith("county-task-"):
        raise AssertionError("native fixture request must use production county-task transport prefix")
    intent = submission["request"]
    snapshot = {
        "revision": intent["expected_revision"], "native_revision": submission["native_revision"],
        "date_raw": submission["date_raw"], "paused": True, "map_ready": True,
        "played_character": {"character_id": submission["played_character_id"], "alive": True},
        "diagnostics": {"hello": {"expected_ck3_version": CK3_12003.game_version,
                                   "expected_ck3_sha256": CK3_12003.executable_sha256}},
    }
    state = NativeProtocolState("county-task-focused-offline-no-pipe")
    requests: list[dict[str, object]] = []
    snapshot_reads: list[int] = []
    calls: list[dict[str, str]] = []

    class FrozenNativeLeavesEndpoint:
        def send(self, request: dict[str, object]) -> None:
            requests.append(deepcopy(request))
            is_result = request["step"] == RESULT_STEP
            result = {
                "step": request["step"], "accepted": True, "private_build": True,
                "advertised": False, "backend_id": "native-headless", "read_only": is_result,
                "game_version": CK3_12003.game_version,
                "executable_sha256": CK3_12003.executable_sha256,
                "snapshot_revision": snapshot["native_revision"],
                "public_revision": snapshot["revision"], "date_raw": snapshot["date_raw"],
                "capture_epoch": independent["after"]["capture_epoch"] if is_result else submission["capture_epoch"],
                "submission": deepcopy(submission),
            }
            if is_result:
                result["independent_result"] = deepcopy(independent)
            state.ingest({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True, "result": result})

    driver = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
    driver.endpoint = FrozenNativeLeavesEndpoint()
    driver.state = state
    driver.allow_private_player_clergy_appointment_query = True

    def paused_snapshot() -> dict[str, object]:
        snapshot_reads.append(1)
        return deepcopy(snapshot)

    driver.take_snapshot = paused_snapshot
    server = create_server(driver)
    registered_submit = server._tool_manager._tools[SUBMIT_TOOL]
    registered_result = server._tool_manager._tools[RESULT_TOOL]
    interesting = {SUBMIT_TOOL, RESULT_TOOL, "submit_county_conversion_task_private_v1",
                   "query_county_conversion_task_result_private_v1", "ingest", "wait_for_command_result",
                   "_frame", "_send", "_task", "_owner", "_matches"}

    def profile(frame, event, argument):
        if event == "call" and frame.f_code.co_name in interesting:
            calls.append({"function": frame.f_code.co_name, "source": frame.f_code.co_filename})

    with patch("uuid.uuid4", side_effect=[SimpleNamespace(hex=request_id[len("county-task-"):]),
                                         SimpleNamespace(hex="independent-result-fixture")]):
        sys.setprofile(profile)
        try:
            submitted = registered_submit.function(**intent)
            snapshot["revision"] += 1
            snapshot["native_revision"] += 1
            snapshot["date_raw"] = independent["after"]["date_raw"]
            observed = registered_result.function(
                expected_revision=snapshot["revision"], submitted_request_id=request_id,
                action_id=intent["action_id"],
            )
        finally:
            sys.setprofile(None)
    checks: list[str] = []

    def check(condition: bool, name: str) -> None:
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    check(registered_submit.function.__module__ == "xar_autoplayer.bridge.mcp_server"
          and registered_result.function.__module__ == "xar_autoplayer.bridge.mcp_server",
          "actual registered submit and independent result callables")
    check(registered_submit.annotations is None and registered_result.annotations.readOnlyHint is True,
          "submit mutates and independent result is readonly")
    executed = {(Path(call["source"]).name, call["function"]) for call in calls}
    expected = {
        ("mcp_server.py", SUBMIT_TOOL), ("mcp_server.py", RESULT_TOOL),
        ("service.py", "submit_county_conversion_task_private_v1"),
        ("service.py", "query_county_conversion_task_result_private_v1"),
        ("native_driver.py", "submit_county_conversion_task_private_v1"),
        ("native_driver.py", "query_county_conversion_task_result_private_v1"),
        ("native_driver.py", "ingest"), ("native_driver.py", "wait_for_command_result"),
        ("county_conversion_task_private_action_v1.py", "submit_county_conversion_task_private_v1"),
        ("county_conversion_task_private_action_v1.py", "query_county_conversion_task_result_private_v1"),
    }
    check(expected <= executed, "actual MCP service driver protocol and task normalizer chain")
    check(len(requests) == 2 and [row["step"] for row in requests] == [SUBMIT_STEP, RESULT_STEP],
          "one submit and one distinct later result transaction")
    check(requests[0]["expected_revision"] == submission["native_revision"]
          and requests[0]["expected_public_revision"] == intent["expected_revision"], "native public revisions remain distinct")
    check(all(requests[0][key] == value for key, value in intent.items() if key != "expected_revision"),
          "task incumbent target replacement and caller action bound unchanged")
    check(requests[1]["submitted_request_id"] == request_id
          and requests[1]["request_id"] != request_id, "result observes a fresh retained request transaction")
    check(len(snapshot_reads) == 4, "each native transaction binds before and after paused player frame")
    check(submitted["owner_submission"] == submission and observed["owner_submission"] == submission
          and observed["owner_result"] == independent, "unchanged production native serializer leaves retained")
    check(submitted["status"] == "queued_verification_pending"
          and submitted["material_result"] is False and submitted["verification_pending"] is True,
          "queue ACK never verifies assignment")
    check(observed["status"] == "task_assignment_material_observed"
          and observed["material_result"] is True and observed["verification_pending"] is False,
          "later real task type owner incumbent and province verify assignment")
    check(observed["actual_task_id_unchanged"] is True
          and observed["before_task"]["active_task_id"] == observed["after_task"]["active_task_id"],
          "material task assignment permits unchanged native FullTaskID")
    check(observed["after_task"]["task_key"] == "task_conversion"
          and observed["after_task"]["target_scope_tag"] == 8
          and observed["after_task"]["target_province_id"] == intent["province_id"],
          "actual conversion type and Province scope preserved")
    check(submitted["county_conversion_completed"] is False
          and observed["county_conversion_completed"] is False, "assignment makes no county Faith Rite completion claim")
    check(submitted["automatic_retry"] is False and observed["automatic_retry"] is False,
          "no implicit submission retry")
    check(native_wire.read_bytes() == frozen, "native fixture bytes unchanged")
    output.mkdir(parents=True, exist_ok=True)
    mapped = output / "registered-mcp-mapped.json"
    mapped.write_text(json.dumps({"submit": submitted, "result": observed}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "GREEN", "focused_case_count": 1, "assertion_count": len(checks), "checks": checks,
        "registered_tools": [SUBMIT_TOOL, RESULT_TOOL], "actual_call_chain": calls,
        "execute_step_requests": requests, "native_wire": pin(native_wire), "mapped_result": pin(mapped),
        "source_pins": [pin(projection / "ck3_autonomous_player/src/xar_autoplayer/bridge" / name)
                        for name in ("mcp_server.py", "service.py", "native_driver.py", "county_conversion_task_private_action_v1.py")],
        "stub_boundary": "MCP SDK registration/argument metadata, endpoint command_result envelope, and synthetic paused snapshot metadata. Submission and independent result leafs unchanged from native production serializer; actual registered callable, service, driver, protocol ingest/wait and action mapping execute.",
        "readiness": "static-ready", "live": False, "sdk_calls": 0, "pipe_operations": 0,
        "game_window_operations": 0, "old_county_matrix_repeated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--native-wire", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        receipt = run_case(args.projection_root, args.source_root or args.projection_root,
                           args.native_wire, args.output_dir)
        code = 0
    except Exception as error:
        trace = args.output_dir / "failure.log"
        trace.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(trace)}
        code = 1
    receipt.update({"test_source": pin(Path(__file__)), "run_exit": code,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (args.output_dir / "RESULT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in ("status", "focused_case_count", "assertion_count", "run_exit")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
