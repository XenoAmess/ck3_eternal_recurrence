"""One offline registered clergy MCP chain consuming native full-serializer JSON.

The native wire is read unchanged. Only MCP SDK registration, the endpoint that
receives that wire, and paused snapshot metadata are fixture stubs. The actual
registered callable, native driver query, protocol cache/wait and normalizers run.
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
import uuid
from unittest.mock import patch


TOOL = "ck3_query_player_clergy_appointment_v1"
BASE_HEAD = "8cf176b436b6b0024fb591d4114b92448146181a"


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class _SdkArgumentMetadata:
    """Registration API metadata stub; argument validation is outside this case."""

    def __init__(self) -> None:
        self.model_config: dict[str, object] = {}

    def model_rebuild(self, *, force: bool) -> None:
        pass

    def model_json_schema(self) -> dict[str, object]:
        return {"type": "object", "additionalProperties": self.model_config.get("extra") != "forbid"}


class CapturingSdkServer:
    def __init__(self, **kwargs: object) -> None:
        self._tool_manager = SimpleNamespace(_tools={})
        self.resources: dict[str, object] = {}

    def tool(self, **kwargs: object):
        def register(function):
            self._tool_manager._tools[function.__name__] = SimpleNamespace(
                function=function, annotations=kwargs.get("annotations"),
                fn_metadata=SimpleNamespace(arg_model=_SdkArgumentMetadata()),
            )
            return function
        return register

    def resource(self, uri: str):
        def register(function):
            self.resources[uri] = function
            return function
        return register


def install_sdk_registration_stub() -> None:
    package = ModuleType("mcp")
    package.__path__ = []
    server = ModuleType("mcp.server")
    server.MCPServer = CapturingSdkServer
    types = ModuleType("mcp.types")
    types.ToolAnnotations = lambda **kwargs: SimpleNamespace(**kwargs)
    sys.modules.update({"mcp": package, "mcp.server": server, "mcp.types": types})


def run_case(source_root: Path, projection_root: Path, wire_path: Path, output_dir: Path) -> dict[str, object]:
    install_sdk_registration_stub()
    sys.path.insert(0, str(source_root / "ck3_autonomous_player/src"))
    import xar_autoplayer.bridge as bridge_package
    bridge_package.__path__.insert(0, str(projection_root / "ck3_autonomous_player/src/xar_autoplayer/bridge"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState

    wire_bytes = wire_path.read_bytes()
    wire = json.loads(wire_bytes)
    result = wire["result"]
    county_native = result["county_conversion"]
    appointment_native = result["player_clergy_appointment"]
    snapshot = {
        "snapshot_id": "county-share-glue-native-wire-frame", "revision": 9001,
        "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
        "paused": True, "map_ready": True,
        "played_character": {"character_id": county_native["owner_character_id"], "alive": True},
        "diagnostics": {"hello": {
            "expected_ck3_version": result["game_version"],
            "expected_ck3_sha256": result["executable_sha256"],
        }},
    }
    state = NativeProtocolState("county-focused-offline-no-pipe")
    requests: list[dict[str, object]] = []

    class ReceiveFrozenNativeWire:
        def send(self, request: dict[str, object]) -> None:
            requests.append(deepcopy(request))
            if request["request_id"] != wire["request_id"]:
                raise AssertionError("frozen native request_id differs from real transport request")
            state.ingest(wire)

    # Avoid constructing a named pipe or starting a driver thread. This is a real
    # driver instance whose production query method uses only these interfaces.
    driver = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
    driver.endpoint = ReceiveFrozenNativeWire()
    driver.state = state
    driver.command_timeout_seconds = 1.0
    driver.allow_private_player_clergy_appointment_query = True
    snapshot_reads: list[int] = []

    def paused_metadata_snapshot() -> dict[str, object]:
        snapshot_reads.append(1)
        return deepcopy(snapshot)

    driver.take_snapshot = paused_metadata_snapshot
    server = create_server(driver)
    registered = server._tool_manager._tools[TOOL]
    calls: list[dict[str, str]] = []
    interesting = {
        TOOL, "query_player_clergy_appointment_private_v1", "read_private_g2_native_query_v1",
        "ingest", "wait_for_command_result", "normalize_player_clergy_appointment_v1",
        "normalize_player_county_conversion_v1",
    }

    def trace(frame, event, argument):
        if event == "call" and frame.f_code.co_name in interesting:
            calls.append({"function": frame.f_code.co_name, "source": frame.f_code.co_filename})

    with patch("uuid.uuid4", return_value=uuid.UUID(int=0x3203)):
        sys.setprofile(trace)
        try:
            observed = registered.function(
                expected_revision=9001,
                candidate_character_id=appointment_native["candidate_character_id"],
            )
        finally:
            sys.setprofile(None)
    checks: list[str] = []

    def check(condition: bool, name: str) -> None:
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    check(registered.function.__module__ == "xar_autoplayer.bridge.mcp_server", "actual registered clergy tool callable")
    check(registered.annotations.readOnlyHint is True, "existing MCP readonly annotation")
    required_calls = {
        ("mcp_server.py", TOOL),
        ("native_driver.py", "query_player_clergy_appointment_private_v1"),
        ("player_clergy_appointment_private_transport.py", "query_player_clergy_appointment_private_v1"),
        ("g2_private_query_transport.py", "read_private_g2_native_query_v1"),
        ("native_driver.py", "ingest"),
        ("native_driver.py", "wait_for_command_result"),
        ("player_clergy_appointment_private_transport.py", "normalize_player_clergy_appointment_v1"),
        ("player_county_conversion_private_observation.py", "normalize_player_county_conversion_v1"),
    }
    executed = {(Path(call["source"]).name, call["function"]) for call in calls}
    check(required_calls <= executed, "actual registered tool to driver transport protocol and both normalizers")
    check(len(requests) == 1 and requests[0]["step"] == "query-player-clergy-appointment-v1", "one existing execute_step query")
    check(requests[0]["expected_revision"] == result["snapshot_revision"]
          and requests[0]["expected_snapshot_revision"] == result["snapshot_revision"], "native revision binding")
    check(requests[0]["candidate_character_id"] == appointment_native["candidate_character_id"], "unchanged clergy candidate request")
    check(len(snapshot_reads) == 2, "existing before and after paused snapshot binding")
    check(observed["county_conversion"] == county_native, "all native county sibling values preserved unchanged")
    county = observed["county_conversion"]
    check(county["current_task_key"] == "task_conversion", "actual current conversion task")
    check(county["current_conversion_monthly_rate_raw"] == 777000, "actual current monthly rate retained")
    check(county["current_percentage_progress_raw"] == 8750000
          and county["current_percentage_progress_raw"] != county["current_conversion_monthly_rate_raw"], "percentage progress remains separate from monthly rate")
    check(county["current_task_frozen"] is True, "frozen task remains frozen despite positive month rate")
    check(county["current_target_county_rite_id"] == 0, "legal zero current target Rite retained")
    check(county["candidate_count"] == 3 and len(county["candidates"]) == 3, "three actual native candidates retained")
    check([candidate["native_monthly_rate_raw"] for candidate in county["candidates"]]
          == [350000, 125000, 500000], "distinct native candidate rates retained in native ordering")
    check(county["candidates"][0]["county_rite_id"] == 2197815299, "unsigned full generation-bearing Rite retained")
    check(county["capture_epoch"] == appointment_native["capture_epoch"]
          and county["capture_epoch"] != observed["snapshot_revision"], "epoch remains independent of snapshot revision")
    check(observed["action_eligibility_complete"] is False
          and county["action_eligibility_complete"] is False, "readonly observation keeps action readiness false")
    check(all(observed[key] == value for key, value in appointment_native.items()), "original appointment mapping remains unchanged")
    check(observed["read_only"] is True and observed["advertised"] is False, "existing private readonly result metadata")
    check(wire_path.read_bytes() == wire_bytes, "native full wire unchanged")
    output_dir.mkdir(parents=True, exist_ok=True)
    mapped = output_dir / "registered-mcp-mapped.json"
    mapped.write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "GREEN", "focused_case_count": 1, "assertion_count": len(checks),
        "checks": checks, "registered_tool": TOOL, "actual_call_chain": calls,
        "execute_step_requests": requests, "native_wire": pin(wire_path), "mapped_result": pin(mapped),
        "source_pins": [pin(Path(create_server.__code__.co_filename)),
                        pin(Path(NativeHeadlessGameplayDriver.query_player_clergy_appointment_private_v1.__code__.co_filename)),
                        pin(projection_root / "ck3_autonomous_player/src/xar_autoplayer/bridge/player_clergy_appointment_private_transport.py"),
                        pin(projection_root / "ck3_autonomous_player/src/xar_autoplayer/bridge/player_county_conversion_private_observation.py")],
        "stub_boundary": "MCP SDK registration and argument metadata API; endpoint receive of unchanged native full command_result; synthetic paused snapshot metadata derived from that wire. Real create_server callable, NativeHeadlessGameplayDriver query, NativeProtocolState ingest/wait, G2 transport and both Python normalizers executed. No official SDK invocation, pipe, game, windows or source mutation.",
        "readiness": "static-ready", "live": False, "sdk_calls": 0, "pipe_operations": 0,
        "game_window_operations": 0, "old_leaf_fixture_repeated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-wire", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        receipt = run_case(args.source_root, args.projection_root, args.native_wire, args.output_dir)
        code = 0
    except Exception as error:
        trace_path = args.output_dir / "failure.log"
        trace_path.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(trace_path)}
        code = 1
    receipt.update({"base_source_head": BASE_HEAD, "test_source": pin(Path(__file__)),
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(), "run_exit": code})
    (args.output_dir / "RESULT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in ("status", "focused_case_count", "assertion_count", "run_exit")}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
