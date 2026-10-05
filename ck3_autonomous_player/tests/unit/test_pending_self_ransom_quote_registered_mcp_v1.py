"""Exercise one new native self-ransom wire and ordinary planner consumer through the actual registered MCP."""
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
    from xar_autoplayer.strategy import choose_one_life_turn

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
        pipe_name = r"\\.\pipe\xar_pending_self_ransom_quote_fixture"
        def __init__(self) -> None:
            self.frames = []
            self.on_frame = None
        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame
        def publish(self, packet: dict) -> None:
            self.on_frame(copy.deepcopy(packet))
        def send(self, request: dict) -> None:
            if request.get("type") == "ping":
                return
            check(request["type"] == "execute_step" and request["step"] == step,
                  "only the existing readonly query is dispatched")
            check(request["pending_interaction_id"] == 1107296271,
                  "full actual pending720 identity")
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
            "snapshot_id": "native:1014", "revision": 1014,
            "state": {
                "phase": "map_hud", "date": "synthetic:self-ransom720", "date_raw": 53286360,
                "speed": 1, "paused": True, "map_ready": True,
                "history": [], "active_event": None,
                "pending_character_interaction": {
                    "instance_id": 1107296271, "sender_character_id": 70766,
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
            "pending_interaction_id": 1107296271,
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
        check(quote["gold_raw"] == 3700000 and quote["raw_scale"] == 100000,
              "synthetic native current-gold named floor value survives")
        check(all(e["raw"] == 0 for e in actual["terms"]["structured_costs"]["value"]["entries"]),
              "zero on-send costs remain separate from acceptance ransom")
        check(quote["decision_input_ready"] and quote["custody_matches_recipient"],
              "native ordinary-gold and current custody inputs are ready")
        check(quote["actor_character_id"] == 70766 and quote["jailer_character_id"] == 29829
              and quote["prisoner_character_id"] == 70766,
              "received roles are preserved without outgoing redirect")
        check(quote["payment_state"] == "pending" and quote["amount_is_current_quote"],
              "quote never claims payment or custody release")
        check(not actual["readiness"]["interaction_semantic_decision_ready"],
              "overall effects stay honestly unqualified")
        check(actual["send_options"]["rows"][8]["canonical_flag_key"] == "hook"
              and actual["send_options"]["exclusive"] is False,
              "received hook and nonexclusive semantics differ from outgoing ransom")
        check(quote["selected_option_index"] == 3 and quote["selected_option_key"] == "current_gold"
              and quote["amount_source_key"] == "current_gold_value",
              "selected current-gold producer differs from full normal ransom")
        check(actual["roles"]["secondary_recipient_character_id"] == -1,
              "self prisoner resolves from actor despite absent secondary recipient")
        check(quote["ordinary_gold_decision_ready"] is True,
              "independent financial input is available despite global semantic false")
        snapshot = driver.take_snapshot()
        metadata = {
            "step": "query-player-prisoner-collection-private-v1",
            "accepted": True, "status": "available", "query_sequence": 3,
            "snapshot_revision": snapshot["native_revision"],
            "queried_snapshot_id": snapshot["snapshot_id"],
            "queried_revision": snapshot["revision"],
            "queried_native_revision": snapshot["native_revision"],
            "player_prisoner_collection": {
                "status": "available", "snapshot_revision": snapshot["native_revision"],
                "date_raw": snapshot["date_raw"], "played_character_id": 29829,
                "played_house_id": 174, "played_dynasty_id": 174,
                "total_count": 1, "returned_count": 1, "collection_complete": True,
                "prisoners": [{
                    "source_ordinal": 0, "prisoner_character_id": 70766,
                    "collection_owner_character_id": 29829, "jailer_character_id": 29829,
                    "custody_relation_verified": True, "house_id": 12690, "dynasty_id": 12077,
                    "same_house": False, "same_dynasty": False,
                    "is_child_of_played_character": False, "primary_title_tier_raw": 3,
                }],
            },
        }
        reply = "accept-pending-character-interaction"
        commands = [{"command": step, "ok": True, "result": actual},
                    {"command": metadata["step"], "ok": True, "result": metadata}]
        planned = choose_one_life_turn(commands, snapshot=snapshot, action_steps=[step, reply])
        check(planned["selected_step"] == reply
              and planned["phase"] == "pending_received_ransom_ordinary_gold_accept",
              "existing ordinary planner consumes independent input and accepts")
        decision = planned["decision"]
        assessment = decision["received_ransom"]
        check(decision["ordinary_gold_decision_ready"] and not decision["semantic_decision_ready"],
              "financial readiness never upgrades the complete effect semantics")
        check(assessment["evidence"]["prisoner"]["primary_title_tier_raw"] == 3
              and assessment["quality_gaps"], "known duke political gap is retained")
        check(assessment["postconditions"]["prisoner_character_id"] == 70766
              and assessment["postconditions"]["independent_player_gold_and_custody_required"]
              and not assessment["postconditions"]["reply_ack_verifies_payment_or_release"],
              "future reply requires independent gold and custody rather than ACK credit")
        missing = choose_one_life_turn(commands[:1], snapshot=snapshot, action_steps=[step, reply])
        check(missing["selected_step"] is None
              and missing["required_mcp_tool"] == "ck3_query_player_prisoner_collection_private_v1",
              "actual missing metadata names the existing observation dependency")
        own = copy.deepcopy(commands)
        own[1]["result"]["player_prisoner_collection"]["prisoners"][0]["same_dynasty"] = True
        own_plan = choose_one_life_turn(own, snapshot=snapshot, action_steps=[step, reply])
        check(own_plan["selected_step"] is None,
              "existing dynasty qualification prevents accepting own-dynasty release")
        zero = copy.deepcopy(commands)
        zero_context = zero[0]["result"]["pending_character_interaction_context"]
        zero_context["terms"]["ransom_quote"]["value"]["gold_raw"] = 0
        zero_plan = choose_one_life_turn(zero, snapshot=snapshot, action_steps=[step, reply])
        check(zero_plan["selected_step"] is None, "zero quote adds no monetary accept value")
        actual["new_ordinary_ransom_planner_fixture"] = planned
        check(len(endpoint.frames) == 1, "one readonly registered query and no action")
        driver.close()
        return actual

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.pending-self-ransom-quote-mcp-validation.v1", "status": "RED"}
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(
            json.dumps(observed, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        report.update(status="GREEN", samples=1, checks=checks, native_fixture=str(args.native_fixture),
                      native_fixture_sha256=hashlib.sha256(raw).hexdigest(),
                      source_root=str(args.source_root), live_queries=0, game_actions=0, planner_cases=4,
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
