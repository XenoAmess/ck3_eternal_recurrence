"""Exercise one new native received-ransom wire through the actual registered MCP."""
from __future__ import annotations
import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-fixture", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

    raw = args.native_fixture.read_bytes()
    native = json.loads(raw)
    step = "query-pending-character-interaction-context-v1"
    capability = "game.command." + step
    checks = 0
    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    class Endpoint:
        pipe_name = "offline-fixture:received-ransom-quote"
        def __init__(self) -> None:
            self.frames = []
            self.on_frame = None
        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame
        def publish(self, packet: dict) -> None:
            self.on_frame(copy.deepcopy(packet))
        def send(self, request: dict) -> None:
            check(request["type"] == "execute_step" and request["step"] == step,
                  "only the existing readonly query is dispatched")
            check(request["pending_interaction_id"] == 1946157063,
                  "full actual R0047 pending identity")
            check("played_character_id" not in request,
                  "player role comes from the native current frame")
            self.frames.append(copy.deepcopy(request))
            self.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": {
                    "step": step, "accepted": True, "status": native["status"],
                    "query_sequence": 1, "snapshot_revision": native["snapshot_revision"],
                    "pending_character_interaction_context": native,
                    "backend_id": "native-headless",
                },
            })
        def close(self) -> None:
            pass
        def transport_error(self):
            return None

    async def exercise() -> dict:
        endpoint = Endpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                              command_timeout_seconds=0.1)
        endpoint.publish({
            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 7878, "session_generation": 0,
            "game_version": native["build"]["version"],
            "expected_ck3_version": native["build"]["version"],
            "executable_sha256": native["build"]["exe_sha256"],
            "capabilities": ["game.state.snapshot", capability],
        })
        endpoint.publish({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:894", "revision": 894,
            "state": {
                "phase": "map_hud", "date": "synthetic:R0047", "date_raw": 53275704,
                "speed": 1, "paused": True, "map_ready": True,
                "history": [], "active_event": None,
                "pending_character_interaction": {
                    "instance_id": 1946157063, "sender_character_id": 34180,
                    "auto_accept_notification": False,
                },
                "played_character": {"character_id": 29829, "alive": True},
                "one_life_settlement": None, "active_wars": [], "player_armies": [],
            },
        })
        server = create_server(driver)
        name = "ck3_query_pending_character_interaction_context_v1"
        check(name in {tool.name for tool in await server.list_tools()},
              "existing pending query is registered")
        response = await server.call_tool(name, {
            "pending_interaction_id": 1946157063,
            "expected_revision": driver.take_snapshot()["revision"],
        })
        check(not response.is_error, "registered MCP accepts the new native quote")
        actual = response.structured_content
        check(actual["terms"] == native["terms"], "all native terms survive normalization")
        check(actual["send_options"] == native["send_options"], "verified nine option keys survive")
        term = actual["terms"]["ransom_quote"]
        quote = term["value"]
        check(term["status"] == "available" and term["reason"] is None,
              "independent quote is available")
        check(quote["gold_raw"] == 1250000 and quote["raw_scale"] == 100000,
              "synthetic native fractional amount survives without rounding")
        check(all(e["raw"] == 0 for e in actual["terms"]["structured_costs"]["value"]["entries"]),
              "zero on-send costs remain separate from acceptance ransom")
        check(quote["decision_input_ready"] and quote["custody_matches_recipient"],
              "native ordinary-gold and current custody inputs are ready")
        check(quote["actor_character_id"] == 34180 and quote["jailer_character_id"] == 29829
              and quote["prisoner_character_id"] == 61540,
              "received roles are preserved without outgoing redirect")
        check(quote["payment_state"] == "pending" and quote["amount_is_current_quote"],
              "quote never claims payment or custody release")
        check(not actual["readiness"]["interaction_semantic_decision_ready"],
              "overall effects stay honestly unqualified")
        check(actual["send_options"]["rows"][8]["canonical_flag_key"] == "hook"
              and actual["send_options"]["exclusive"] is False,
              "received hook and nonexclusive semantics differ from outgoing ransom")
        check(len(endpoint.frames) == 1, "one readonly registered query")
        driver.close()
        return actual

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.pending-ransom-quote-mcp-validation.v1", "status": "RED"}
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(
            json.dumps(observed, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        report.update(status="GREEN", samples=1, checks=checks, native_fixture=str(args.native_fixture),
                      native_fixture_sha256=hashlib.sha256(raw).hexdigest(),
                      source_root=str(args.source_root), live_queries=0, game_actions=0,
                      amount_kind="synthetic-native-fixture", output_file_count=2)
    except Exception as error:
        report.update(checks=checks, error=str(error))
        raise
    finally:
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
