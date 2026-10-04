"""Two new complete replenishment-record wires through the registered MCP, offline."""
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
LABELS = ("first-and-nonfirst", "empty-records")

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def pin(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

async def run(projection: Path, source: Path, native_dir: Path,
              output: Path) -> dict[str, object]:
    sys.path.insert(0, str(source / "tools"))
    sys.path.insert(0, str(projection / "ck3_autonomous_player/src"))
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.version_identity import CK3_12003

    checks: list[str] = []
    calls: list[dict[str, str]] = []
    requests: list[dict[str, object]] = []
    def check(condition: bool, message: str) -> None:
        require(condition, message)
        checks.append(message)

    class Endpoint:
        pipe_name = r"\\.\pipe\army-full-replenishment-records-offline-fixture"
        def __init__(self, row: dict[str, object], sequence: int) -> None:
            self.row, self.sequence = row, sequence
            self.on_frame = None
        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame
        def publish(self, value: dict[str, object]) -> None:
            require(callable(self.on_frame), "production driver binds the fixture receiver")
            self.on_frame(deepcopy(value))
        def send(self, request: dict[str, object]) -> None:
            if request.get("type") != "execute_step":
                return
            requests.append(deepcopy(request))
            require(request.get("step") == STEP, "focused cases submit only the existing army query")
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": {"step": STEP, "accepted": True,
                                     "status": "available", "query_sequence": self.sequence,
                                     "army_strengths": [deepcopy(self.row)]}})
        def close(self) -> None:
            pass
        def transport_error(self) -> None:
            return None

    def profile(frame, event, argument) -> None:
        name = frame.f_code.co_name
        if event == "call" and ("army_strength" in name or "replenishment_records" in name
                                or name in {"execute_step", "_execute_primitive_step"}):
            calls.append({"function": name, "source": frame.f_code.co_filename})
    previous, previous_thread = sys.getprofile(), threading.getprofile()
    sys.setprofile(profile)
    threading.setprofile(profile)
    mapped = {}
    inputs = []
    try:
        for sequence, label in enumerate(LABELS, 1):
            path = native_dir / (label + ".json")
            original = path.read_bytes()
            rows = json.loads(original)["army_strengths"]
            require(len(rows) == 1 and isinstance(rows[0], dict), "one native row per focused case")
            row = rows[0]
            require(row["scope_role"] == "player" and row["war_ids"] == [],
                    "producer retains the precise ordinary player scope")
            army_id = row["army_id"]
            actor = 29829
            army = {"army_id": army_id, "owner_character_id": actor, "soldiers": row["current_soldiers"],
                    "current_province_id": 472, "move_target_province_id": None,
                    "controllable": True}
            endpoint = Endpoint(row, sequence)
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                                 command_timeout_seconds=1.0)
            endpoint.publish({"type": "hello", "protocol_version": 1,
                              "bridge_version": "0.1.0", "pid": 4242, "session_generation": 0,
                              "expected_ck3_version": CK3_12003.game_version,
                              "expected_ck3_sha256": CK3_12003.executable_sha256,
                              "capabilities": ["game.state.snapshot", "game.command." + STEP]})
            endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
                              "snapshot_id": "native:11", "revision": 11,
                              "state": {"phase": "map_hud", "date": "fixture-only", "date_raw": 0,
                                        "speed": 1, "paused": True, "map_ready": True, "history": [],
                                        "active_event": None, "pending_character_interaction": None,
                                        "played_character": {"character_id": actor, "alive": True},
                                        "player_armies": [deepcopy(army)], "active_wars": []}})
            try:
                before = driver.take_snapshot()
                async with Client(create_server(driver)) as client:
                    result = await client.call_tool(TOOL, {"army_ids": [army_id],
                                                           "expected_revision": before["revision"]})
                check(result.is_error is False, label + " returns through the registered MCP")
                returned = result.structured_content["army_strengths"][0]
                check(returned["regiment_replenishment_records_v1"] == row["regiment_replenishment_records_v1"],
                      label + " retains all complete record observations from the native producer")
                leaf=returned["regiment_replenishment_records_v1"]
                if label == "first-and-nonfirst":
                    records=leaf[0]["records"]
                    check(leaf[0]["status"] == "available" and leaf[0]["ready"] is True
                          and len(records) == leaf[0]["native_data_record_count"] == 3,
                          "complete stored record count and order pass the registered MCP")
                    check(records[0]["current_soldiers"] == records[0]["maximum_soldiers"]
                          and any(record["record_index"] > 0 and record["current_soldiers"] < record["maximum_soldiers"]
                                  and record["effective_current_soldiers"] < record["maximum_soldiers"]
                                  for record in records),
                          "a full first record no longer hides the nonfirst current deficit")
                    check(any(record["state_raw"] == 3 and record["current_soldiers"] == 0
                              and record["effective_current_soldiers"] == record["maximum_soldiers"]
                              for record in records),
                          "physical zero and the native state3 effective maximum remain distinct")
                    check(any(record["persistent_monthly_replenishment_fraction_raw"] != record["persistent_prepared_replenishment_fraction_raw"]
                              for record in records),
                          "fresh fraction and actual prepared cache remain independent")
                    first=returned["regiment_replenishment"][0]
                    check(first["source"] == "native_first_record" and first["native_data_record_count"] == 3
                          and all(chunk["current_soldiers"] == chunk["maximum_soldiers"] for chunk in first["chunks"]),
                          "the existing first-record observation keeps its original coverage")
                else:
                    check(any(item["status"] == "available" and item["ready"] is True
                              and item["native_data_record_count"] == 0 and item["records"] == [] for item in leaf),
                          "a readable zero-record regiment preserves legitimate empty coverage")
                    partial=[item for item in leaf if item["status"] == "partial"]
                    check(bool(partial) and all(item["ready"] is False and len(item["records"]) == item["native_data_record_count"]
                                               for item in partial),
                          "identity failure keeps its stored record position and partial read status")
                    check(any(record["status"] == "unavailable" and isinstance(record["unavailable_reason"],str)
                              for item in partial for record in item["records"]),
                          "unresolved identity is explicit rather than a dummy chunk")
                check(returned["army_id"] == army_id and returned["native_carmy_id"] == row["native_carmy_id"]
                      and returned["status"] == row["status"] == "available"
                      and returned["current_soldiers"] == row["current_soldiers"]
                      and returned["maximum_soldiers"] == row["maximum_soldiers"],
                      label + " preserves the independent parent army binding and health")
                after = driver.take_snapshot()
                check(after["date_raw"] == before["date_raw"] and after["paused"] is True
                      and after["player_armies"] == before["player_armies"],
                      label + " leaves paused time and army state unchanged")
                check(path.read_bytes() == original, label + " native producer bytes remain unchanged")
                mapped[label] = result.structured_content
                inputs.append(pin(path))
            finally:
                driver.close()
    finally:
        sys.setprofile(previous)
        threading.setprofile(previous_thread)
    executed = {(Path(call["source"]).name, call["function"]) for call in calls}
    check({("mcp_server.py", TOOL), ("service.py", "query_army_strengths"),
           ("native_driver.py", "_execute_army_strength_query"),
           ("war_contract.py", "normalize_army_strengths"),
           ("army_replenishment_records_contract.py", "normalize_regiment_replenishment_records_v1")} <= executed,
          "the new wires traverse real registered MCP, service, driver and production normalization")
    check(len(requests) == 2 and all(item["step"] == STEP for item in requests),
          "exactly the two new observations run, with no gameplay operation or retry")
    mapped_path = output / "registered-full-records-results.json"
    mapped_path.write_text(json.dumps(mapped, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "GREEN", "focused_case_count": 2, "check_count": len(checks),
            "checks": checks, "native_inputs": inputs, "mapped_result": pin(mapped_path),
            "actual_call_chain": calls, "execute_step_requests": requests,
            "readiness": "static-ready", "live": False, "sdk_calls": 0,
            "game_actions": 0, "window_actions": 0, "saved_days": 0,
            "old_tests_repeated": False,
            "stub_boundary": "Synthetic transport/hello/paused snapshot only. Two unchanged rows from production native Strength reader and serializer pass the real registered MCP/service/driver/normalizer. No live full-record observation is credited."}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        receipt = asyncio.run(run(args.projection_root, args.source_root or args.projection_root,
                                  args.native_dir, args.output_dir))
        code = 0
    except Exception as error:
        failure = args.output_dir / "failure.log"
        failure.write_text(traceback.format_exc(), encoding="utf-8")
        receipt = {"status": "HARNESS-RED", "failure": str(error), "traceback": pin(failure),
                   "live": False, "game_actions": 0}
        code = 1
    receipt.update({"test_source": pin(Path(__file__)), "run_exit": code,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    (args.output_dir / "RESULT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in
                      ("status", "focused_case_count", "check_count", "run_exit", "failure")}))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
