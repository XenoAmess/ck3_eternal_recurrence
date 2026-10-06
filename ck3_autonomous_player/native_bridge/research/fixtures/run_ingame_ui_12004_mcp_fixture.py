"""Consume whole native .4 snapshots and Army UI return through registered MCP.

This is an offline owned-memory replay. Only the endpoint is replaced: the
production protocol cache, snapshot projection, driver, Service, registration,
normalizer and original-return receipt all run normally. Authoring this file
does not establish a fixture pass or any live gameplay capability.
"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import traceback
import uuid


checks = 0


def require(value: bool, message: str) -> None:
    global checks
    checks += 1
    if not value:
        raise RuntimeError(message)


def read_frame(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), f"whole native frame required: {path.name}")
    return value


async def consume(args: argparse.Namespace) -> dict[str, object]:
    sys.path.insert(0, str(args.projection_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.ingame_ui_contract import (
        QUERY_CAPABILITY, QUERY_STEP, normalize_ui_result,
    )
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import (
        DEFAULT_PIPE_NAME, NativeHeadlessGameplayDriver,
    )
    from xar_autoplayer.bridge.succession_transition_contract import (
        unknown_succession_lifecycle_binding_v1,
    )
    from xar_autoplayer.bridge.version_identity import CK3_12004

    paths = {
        "before": args.native_dir / "state-snapshot-before.json",
        "after": args.native_dir / "state-snapshot-after.json",
        "query": args.native_dir / "army-query.json",
    }
    before, after, packet = (read_frame(paths[key]) for key in ("before", "after", "query"))
    for frame in (before, after):
        require(frame.get("type") == "state_snapshot" and frame.get("protocol_version") == 1,
                "snapshot inputs are complete production state_snapshot envelopes")
        require(isinstance(frame.get("state"), dict), "native snapshot carries its full state")
    require(packet.get("type") == "command_result" and packet.get("protocol_version") == 1
            and packet.get("ok") is True and isinstance(packet.get("result"), dict),
            "Army input is the complete normal native command_result envelope")
    native = packet["result"]
    require(native.get("schema") == "ck3-ingame-ui-window-v1"
            and native.get("window_kind") == "army" and native.get("requested_subject_id") == 0,
            "native producer qualified the existing Army window query")
    require(native.get("game_version") == CK3_12004.game_version
            and native.get("executable_sha256") == CK3_12004.executable_sha256,
            "native Army return carries the exact actual .4 identity")
    require(before["state"].get("paused") is True and before["state"].get("map_ready") is True
            and before["state"].get("played_character", {}).get("character_id") == 29829,
            "normal native Snapshot observes paused map-ready Robert")
    require(before == after, "read-only native query preserves its independently reread Snapshot")

    class PacketEndpoint:
        """Transport-only hello/pong plus unmodified native state/result payloads."""

        pipe_name = DEFAULT_PIPE_NAME

        def __init__(self) -> None:
            self.requests: list[dict[str, object]] = []
            self.returned: dict[str, object] | None = None
            self._on_frame = None
            self._on_disconnect = None

        def start(self, on_frame, on_disconnect) -> None:
            self._on_frame, self._on_disconnect = on_frame, on_disconnect
            on_frame({
                "type": "hello", "protocol_version": 1, "pid": 1,
                "connection_generation": 1,
                "capabilities": ["game.state.snapshot", QUERY_CAPABILITY],
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            })
            on_frame(deepcopy(before))

        def send(self, request: dict[str, object]) -> None:
            self.requests.append(deepcopy(request))
            if request.get("type") == "ping":
                self._on_frame({"type": "pong", "protocol_version": 1,
                                "request_id": request["request_id"]})
                return
            require(request.get("type") == "execute_step" and request.get("step") == QUERY_STEP
                    and request.get("window_kind") == "army" and request.get("subject_id") == 0
                    and request.get("expected_revision") == before["revision"],
                    "registered Service posts the producer-qualified normal native request")
            require(self.returned is None, "one registered query sends exactly one native operation")
            self.returned = deepcopy(packet)
            # Correlation belongs to replay transport; all native result bytes
            # and every other envelope field retain the producer's values.
            self.returned["request_id"] = request["request_id"]
            self._on_frame(deepcopy(self.returned))
            self._on_frame(deepcopy(after))

        def close(self) -> None:
            if self._on_disconnect is not None:
                self._on_disconnect()

    state_dir = args.out.parent / f"ingame-ui-replay-state-{uuid.uuid4().hex}"
    endpoint = PacketEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint=endpoint, command_timeout_seconds=1.0, state_dir=state_dir,
        succession_lifecycle_binding=unknown_succession_lifecycle_binding_v1(),
    )
    try:
        source = driver.take_snapshot()
        require(source["native_revision"] == before["revision"]
                and source["revision"] != source["native_revision"],
                "production protocol cache retains distinct public and native revisions")
        require(source["snapshot_id"] == before["snapshot_id"]
                and source["date_raw"] == before["state"]["date_raw"],
                "production projection consumes the native Snapshot identity and date")
        require(isinstance(source.get("episode_run_id"), str) and bool(source["episode_run_id"])
                and source["diagnostics"]["connection_generation"] == 1,
                "normal driver projection provides its episode and transport binding")
        require(driver.state.raw_transport_snapshot()["semantic_packet_accepted"] is True
                and driver.state.raw_transport_snapshot()["native_packet"] == before,
                "normal protocol state accepted and retained the whole native Snapshot")
        server = create_server(driver)
        tool = next(row for row in await server.list_tools()
                    if row.name == "ck3_query_ingame_ui_window_v1")
        require(set(tool.input_schema["required"]) == {"window_kind", "expected_revision"},
                "existing registered tool keeps its typed window/revision arguments")
        response = await server.call_tool("ck3_query_ingame_ui_window_v1", {
            "window_kind": "army", "expected_revision": source["revision"],
        })
        require(getattr(response, "is_error", False) is False,
                "existing registered MCP query completed without a consumer error")
        observed = response.structured_content
        require(isinstance(observed, dict), "registered MCP returns the typed native UI result")
        expected = normalize_ui_result(
            native, operation="query", kind="army", subject_id=0,
            native_revision=source["native_revision"], date_raw=source["date_raw"],
            actor_id=29829, expected_build=CK3_12004,
        )
        require(all(observed.get(key) == value for key, value in expected.items()),
                "complete native UI payload survives driver, Service and registered MCP")
        require(observed["dispatch_invoked"] is False and observed["verification_pending"] is False,
                "independent Army query remains read-only observation")
        require(observed["available"] is True and observed["status"] == "observed"
                and observed["subject_id_available"] is True
                and observed["current_subject_id"] == 0x01000003
                and observed["native_army_id"] == 0x02000004
                and observed["owner_character_id_available"] is True
                and observed["owner_character_id"] == 29829,
                "genuine native public Unit, Army and played-owner identities remain distinct")
        tree = observed["tree"]
        require(tree["root_available"] is True and tree["widget_count"] == 2
                and [row["runtime_name"] for row in tree["widgets"]] == ["army_window", "army_details"],
                "normal native observation retains the complete measured Army subtree")
        require(observed["queried_snapshot_id"] == source["snapshot_id"]
                and observed["queried_revision"] == source["revision"]
                and observed["queried_native_revision"] == source["native_revision"]
                and observed["episode_run_id"] == source["episode_run_id"]
                and observed["queried_connection_generation"] == 1,
                "registered result retains the normal paused session binding")
        native_requests = [row for row in endpoint.requests if row["type"] == "execute_step"]
        require(len(native_requests) == 1, "no extra native query or action was synthesized")
        receipt = observed["native_ui_raw_return_receipt"]
        receipt_path = Path(receipt["path"])
        receipt_bytes = receipt_path.read_bytes()
        original = json.loads(receipt_bytes)
        require(original["original_parsed_command_result"] == endpoint.returned
                and original["request"] == native_requests[0],
                "production create-only receipt retains the original parsed native return and request")
        require(original["actual_pre_submission_snapshot"]["snapshot_id"] == source["snapshot_id"]
                and original["actual_pre_submission_snapshot"]["episode_run_id"] == source["episode_run_id"]
                and original["wire_bytes_preserved"] is False,
                "original-return receipt records the actual submission Snapshot without wire claims")
        require(receipt["bytes"] == len(receipt_bytes)
                and receipt["sha256"] == hashlib.sha256(receipt_bytes).hexdigest(),
                "production receipt names its retained parsed return")
        end = driver.take_snapshot()
        require(driver.state.raw_transport_snapshot()["native_packet"] == after
                and end["revision"] == source["revision"]
                and end["native_revision"] == source["native_revision"],
                "independent native after Snapshot preserves the paused query frame")
        history = end["native_command_history"]
        require(len(history) == 1 and history[0]["command"] == QUERY_STEP and history[0]["ok"] is True,
                "unmodified production driver records one successful query")
        return {
            "case": "normal-army-query", "status": "GREEN",
            "native_status": observed["status"], "available": observed["available"],
            "public_revision": source["revision"], "native_revision": source["native_revision"],
            "original_return_receipt": receipt, "state_dir": str(state_dir),
            "inputs": {key: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                       for key, path in paths.items()},
        }
    finally:
        driver.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    args.out = args.out or args.native_dir.parent / "INGAME-UI-PYTHON-CONSUMER-RESULT.json"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        case = asyncio.run(consume(args))
        report = {"status": "GREEN", "readiness": "static-ready", "checks": checks,
                  "cases": [case], "game_operations": 0, "sdk_calls_to_game": 0,
                  "window_operations": 0, "live_validation": False,
                  "whole_dll_built": False, "hello_source": "fixture-transport"}
    except Exception as error:
        report = {"status": "RED", "classification": "harness-or-consumer", "checks": checks,
                  "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc(),
                  "game_operations": 0, "sdk_calls_to_game": 0, "window_operations": 0,
                  "live_validation": False}
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        raise
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
