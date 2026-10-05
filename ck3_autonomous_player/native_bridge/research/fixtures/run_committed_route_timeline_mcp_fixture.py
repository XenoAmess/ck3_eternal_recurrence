"""Complete committed-route wires through the existing registered MCP, offline."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import threading
import traceback

TOOL = "ck3_query_army_strengths"
STEP = "query-army-strengths-v1"
LABELS = ("multi-edge", "zero-duration", "empty-route", "unavailable-route")


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def synthetic_row(label: str) -> dict[str, object]:
    """Consumer-only fixture; it never counts as native reader verification."""
    timeline = {
        "status": "available", "source": "native_committed_route", "native_duration_scale": 100000,
        "committed_route_province_ids": [2, 3],
        "native_route_prefix_remaining_days_q100000": [86868, 1134729],
        "native_full_route_remaining_days_q100000": 1134729,
        "projected_route_arrival_date_raws": [43823128, 43823368], "unavailable_reason": None,
    }
    if label == "zero-duration":
        timeline.update(native_route_prefix_remaining_days_q100000=[0, 0],
                        native_full_route_remaining_days_q100000=0,
                        projected_route_arrival_date_raws=[43823104, 43823104])
    elif label == "empty-route":
        timeline.update(status="not_applicable", committed_route_province_ids=[],
                        native_route_prefix_remaining_days_q100000=[],
                        native_full_route_remaining_days_q100000=None,
                        projected_route_arrival_date_raws=[])
    elif label == "unavailable-route":
        timeline.update(status="unavailable", committed_route_province_ids=None,
                        native_route_prefix_remaining_days_q100000=None,
                        native_full_route_remaining_days_q100000=None,
                        projected_route_arrival_date_raws=None,
                        unavailable_reason="committed_route_timeline_unavailable")
    return {
        "status": "available", "army_id": 16777217, "native_carmy_id": 33554433,
        "scope_role": "player", "war_ids": [], "regiment_count": 0, "current_soldiers": 0,
        "maximum_soldiers": 0, "ai_base_power_raw": 0, "ai_base_power_scale": 100000,
        "unavailable_reason": None,
        "current_movement_progress": {
            "status": "not_applicable" if label == "empty-route" else "available",
            "source": "native_current_route_edge", "unit_state_raw": 7,
            "accumulated_movement_weight_raw": 40000, "cached_edge_speed_raw": 100000,
            "normalized_edge_progress": None if label == "empty-route" else {"raw": 40000, "scale": 100000},
            "first_route_edge_remaining_duration": None if label == "empty-route" else {"raw": 86868, "scale": 100000},
            "unavailable_reason": None, "committed_route_timeline": timeline,
        },
    }


async def run(root: Path, native_dir: Path | None, output: Path) -> dict[str, object]:
    sys.path.insert(0, str(root / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003
    from xar_autoplayer.bridge.war_contract import normalize_army_strengths

    checks, requests, calls, inputs, mapped = [], [], [], [], {}

    def check(value: bool, message: str) -> None:
        require(value, message)
        checks.append(message)

    class Endpoint:
        pipe_name = r"\\.\pipe\committed-route-offline-fixture"
        def __init__(self, row, sequence):
            self.row, self.sequence, self.on_frame = row, sequence, None
        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame
        def publish(self, packet):
            require(callable(self.on_frame), "fixture receiver bound")
            self.on_frame(deepcopy(packet))
        def send(self, request):
            if request.get("type") != "execute_step":
                return
            requests.append(deepcopy(request))
            require(request.get("step") == STEP, "only existing army query executes")
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": {"step": STEP, "accepted": True, "status": "available",
                                     "query_sequence": self.sequence, "army_strengths": [self.row]}})
        def close(self):
            pass
        def transport_error(self):
            return None

    def profile(frame, event, argument):
        name = frame.f_code.co_name
        if event == "call" and ("army_strength" in name or "committed_route_timeline" in name):
            calls.append({"function": name, "source": frame.f_code.co_filename})

    previous, previous_thread = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    try:
        for sequence, label in enumerate(LABELS, 1):
            path = None if native_dir is None else native_dir / (label + ".json")
            row = synthetic_row(label) if path is None else json.loads(path.read_text(encoding="utf-8-sig"))["army_strengths"][0]
            timeline = row["current_movement_progress"]["committed_route_timeline"]
            endpoint = Endpoint(row, sequence)
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
            army_id = row["army_id"]
            army = {"army_id": army_id, "owner_character_id": 29829, "soldiers": 0,
                    "current_province_id": 1, "move_target_province_id": None, "controllable": True}
            endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                              "pid": 4242, "session_generation": 0,
                              "expected_ck3_version": CK3_12003.game_version,
                              "expected_ck3_sha256": CK3_12003.executable_sha256,
                              "capabilities": ["game.state.snapshot", "game.command." + STEP]})
            endpoint.publish({"type": "state_snapshot", "protocol_version": 1, "snapshot_id": "native:11", "revision": 11,
                              "state": {"phase": "map_hud", "date": "fixture-only", "date_raw": 43823104,
                                        "speed": 1, "paused": True, "map_ready": True, "history": [],
                                        "active_event": None, "pending_character_interaction": None,
                                        "played_character": {"character_id": 29829, "alive": True},
                                        "player_armies": [army], "active_wars": []}})
            try:
                before = driver.take_snapshot()
                async with Client(create_server(driver)) as client:
                    result = await client.call_tool(TOOL, {"army_ids": [army_id], "expected_revision": before["revision"]})
                check(result.is_error is False, label + " existing registered MCP succeeds")
                returned = result.structured_content["army_strengths"][0]
                check(returned == row, label + " native row survives service/driver/all normalizers")
                check(returned["current_movement_progress"]["committed_route_timeline"] == timeline,
                      label + " raw native prefix and rounded date arrays remain unchanged")
                check(returned["status"] == "available", label + " optional route status leaves strength available")
                after = driver.take_snapshot()
                check(after["date_raw"] == before["date_raw"] and after["paused"] is True,
                      label + " paused fixture time remains unchanged")
                mapped[label] = result.structured_content
                if path is not None:
                    inputs.append(pin(path))
            finally:
                driver.close()
        legacy = synthetic_row("multi-edge")
        legacy["current_movement_progress"].pop("committed_route_timeline")
        check(normalize_army_strengths([legacy]) == [legacy], "older edge-only producer stays compatible")
        check(mapped["zero-duration"]["army_strengths"][0]["current_movement_progress"]["committed_route_timeline"]
              ["native_full_route_remaining_days_q100000"] == 0, "valid zero full remainder survives")
    finally:
        sys.setprofile(previous)
        threading.setprofile(previous_thread)
    executed = {(Path(call["source"]).name, call["function"]) for call in calls}
    check({("mcp_server.py", TOOL), ("service.py", "query_army_strengths"),
           ("native_driver.py", "_execute_army_strength_query"),
           ("war_contract.py", "normalize_army_strengths"),
           ("war_contract.py", "_normalize_committed_route_timeline")} <= executed,
          "production registered MCP/service/driver/normalizer chain actually executes")
    check(len(requests) == 4, "exactly four offline queries, no gameplay action or retry")
    mapped_path = output / "registered-route-results.json"
    mapped_path.write_text(json.dumps(mapped, indent=2) + "\n", encoding="utf-8")
    return {"status": "GREEN", "focused_case_count": 4, "checks": checks,
            "native_inputs": inputs, "synthetic_python_only": native_dir is None,
            "mapped_result": pin(mapped_path), "actual_call_chain": calls, "execute_step_requests": requests,
            "readiness": "consumer-static-ready" if native_dir is None else "static-ready",
            "native_reader_tested": native_dir is not None, "live": False, "sdk_calls": 0,
            "game_actions": 0, "window_actions": 0, "saved_days": 0,
            "boundary": "Synthetic transport/hello/paused snapshot. No CK3 or native CK3 function execution."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--native-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        receipt = asyncio.run(run(args.projection_root, args.native_dir, args.output_dir))
        code = 0
    except Exception as error:
        log = args.output_dir / "failure.log"
        log.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(log), "live": False}
        code = 1
    receipt.update(test_source=pin(Path(__file__)), run_exit=code,
                   completed_at_utc=datetime.now(timezone.utc).isoformat())
    (args.output_dir / "RESULT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in ("status", "focused_case_count", "run_exit", "failure")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
