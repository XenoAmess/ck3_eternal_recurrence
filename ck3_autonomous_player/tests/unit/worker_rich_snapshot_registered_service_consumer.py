"""One offline rich WorkerAdapter envelope -> native Driver -> registered snapshot workflow."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


class OwnedFrameEndpoint:
    def __init__(self):
        self.on_frame = None
        self.on_disconnect = None
        self.sent = []
        self.transport_pings = []

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def emit(self, frame):
        assert self.on_frame is not None
        self.on_frame(deepcopy(frame))

    def send(self, frame, **kwargs):
        if (frame.get("type") == "ping" and frame.get("protocol_version") == 1
                and isinstance(frame.get("request_id"), str)):
            self.transport_pings.append(deepcopy(frame))
            self.emit({"protocol_version": 1, "type": "pong",
                       "request_id": frame["request_id"]})
            return
        self.sent.append(deepcopy(frame))
        raise AssertionError("offline snapshot consumer must submit zero gameplay commands")

    def transport_error(self):
        return None

    def close(self):
        if self.on_disconnect:
            self.on_disconnect()


def require_rich_preservation(raw, result):
    state = raw["state"]
    assert result["date_raw"] == state["date_raw"]
    assert result["paused"] is True and result["map_ready"] is True
    assert result["played_character"]["character_id"] == 29829
    assert len(result["player_armies"]) == len(state["player_armies"]) == 2
    assert [r["army_id"] for r in result["player_armies"]] == [
        r["army_id"] for r in state["player_armies"]]
    wars = result["active_wars"]
    raw_wars = state["active_wars"]
    assert len(wars) == len(raw_wars) == 2
    for war, native_war in zip(wars, raw_wars, strict=True):
        assert war["war_id"] == native_war["war_id"]
        assert war["targeted_title_ids"] == native_war["targeted_title_ids"]
        assert len(war["allied_armies"]) == len(native_war["allied_armies"]) == 2
        assert len(war["enemy_armies"]) == len(native_war["enemy_armies"]) == 2
        rows = war["objective_province_states"]
        raw_rows = native_war["objective_province_states"]
        assert len(rows) == len(raw_rows) == 2
        for row, native_row in zip(rows, raw_rows, strict=True):
            for key in ("province_id", "fort_level", "garrison_size",
                        "current_besieging_army_selection"):
                assert row[key] == native_row[key], (key, row, native_row)
            siege = row["active_siege"]
            raw_siege = native_row["active_siege"]
            for key in ("current_work", "total_work"):
                assert siege[key] == raw_siege[key]
            occurrences = siege["province_unit_occurrences"]
            raw_occurrences = raw_siege["province_unit_occurrences"]
            assert len(occurrences) == len(raw_occurrences) == 2
            for occurrence, native_occurrence in zip(
                    occurrences, raw_occurrences, strict=True):
                assert occurrence["qualified_regiment_ids"] == native_occurrence[
                    "qualified_regiment_ids"]
                assert len(occurrence["qualified_regiment_ids"]) == 2


async def consume(wire_dir, result_dir, source_head):
    from mcp import Client
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

    context = json.loads((wire_dir / "NATIVE-CONTEXT.json").read_text(encoding="utf-8"))
    assert context["producer"] == "fixture-native-gameadapter-rich-snapshot-v1"
    assert context["execution_status"] == "passed"
    assert context["samples"] == 2 and context["raw_reads"] == 2
    assert context["semantic_calls"] == context["wrong_owner"] == 0
    assert context["Game_executed"] is False

    endpoint = OwnedFrameEndpoint()
    driver = NativeHeadlessGameplayDriver(
        pipe_name="offline-owned-worker-rich-snapshot",
        endpoint=endpoint, state_dir=result_dir / "state",
        save_dir=result_dir / "unused-save-directory",
        command_timeout_seconds=0.1, episode_projection="native_campaign")
    endpoint.emit({
        "protocol_version": 1, "type": "hello", "pid": 1,
        "connection_generation": 1,
        "capabilities": ["bridge.heartbeat", "game.state.snapshot"]})
    samples = []
    try:
        async with Client(create_server(driver)) as client:
            for name in ("initial", "updated"):
                raw = json.loads((wire_dir / (name + ".native-frame.json")).read_text(
                    encoding="utf-8"))
                assert raw["type"] == "state_snapshot" and raw["protocol_version"] == 1
                original = deepcopy(raw)
                endpoint.emit(raw)
                response = await client.call_tool("ck3_take_snapshot", {
                    "include_native_command_history": False})
                assert response.is_error is False
                result = response.structured_content
                assert isinstance(result, dict)
                require_rich_preservation(original, result)
                assert raw == original
                assert driver.state.raw_transport_snapshot()["native_packet"] == original
                assert driver.state.raw_transport_snapshot()["semantic_packet_accepted"] is True
                (result_dir / (name + ".registered-snapshot.json")).write_text(
                    json.dumps(result, indent=2) + "\n", encoding="utf-8")
                samples.append(result)
        assert samples[1]["date_raw"] == samples[0]["date_raw"] + 1
        assert samples[1]["revision"] == samples[0]["revision"] + 1
        assert samples[1]["native_revision"] == samples[0]["native_revision"] + 1
        before = samples[0]["active_wars"][1]["objective_province_states"][1]
        after = samples[1]["active_wars"][1]["objective_province_states"][1]
        assert after["garrison_size"] != before["garrison_size"]
        assert after["current_besieging_army_selection"] != before[
            "current_besieging_army_selection"]
        assert after["active_siege"]["province_unit_occurrences"] != before[
            "active_siege"]["province_unit_occurrences"]
        assert endpoint.sent == []
        assert len(endpoint.transport_pings) == 1
    finally:
        endpoint.close()
    return {
        "schema": "xar.worker-rich-snapshot-registered-consumer.v1",
        "status": "GREEN", "source_root": str(ROOT.parent),
        "source_head": source_head, "whole_workflows": 1,
        "registered_tool": "ck3_take_snapshot", "registered_MCP_calls": 2,
        "native_commands_sent": 0, "transport_pings": len(endpoint.transport_pings),
        "Game_calls": 0,
        "native_fixture_context": context,
        "synthetic_native_reader": True, "real_game_snapshot_captured": False,
        "live_readiness": False, "old_FIRST_replays": 0,
        "preserved_samples": ["initial", "updated"],
        "report_date": "2026-10-08", "iso_week": "2026-W41"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wire-dir", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    args = parser.parse_args()
    if args.result_dir.exists():
        raise ValueError("a fresh nonexistent consumer result directory is required")
    args.result_dir.mkdir(parents=True)
    started = time.perf_counter()
    result = asyncio.run(consume(args.wire_dir, args.result_dir, args.source_head))
    result["elapsed_seconds"] = time.perf_counter() - started
    (args.result_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "registered_MCP_calls": 2,
                      "native_commands_sent": 0, "Game_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
