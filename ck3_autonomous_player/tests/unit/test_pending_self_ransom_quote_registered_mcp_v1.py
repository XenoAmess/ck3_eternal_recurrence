"""Consume one new self-ransom wire and readonly custody query through registered MCP planning."""
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
    collection_step = "query-player-prisoner-collection-private-v1"
    reply = "accept-pending-character-interaction"
    capability = "game.command." + step
    # Captured721 schema-v6 metadata, replayed as a native response. The
    # transport, rather than this fixture, must produce queried_* fields.
    custody_rows = [
        (54235, None, None, None), (56063, None, None, None),
        (61540, 2237, 2237, None), (70766, 12690, 12077, 3),
    ]
    collection_native = {
        "step": collection_step, "accepted": True, "status": "available",
        "query_sequence": 3, "observation_revision": 1926335,
        "snapshot_revision": 1014, "private_build": True,
        "read_only": True, "advertised": False, "backend_id": "native-headless",
        "player_prisoner_collection": {
            "schema": "player-prisoner-collection-private-v1", "schema_version": 6,
            "snapshot_revision": 1014, "status": "available", "unavailable_reason": None,
            "date_raw": 53286360, "played_character_id": 29829,
            "played_house_id": 174, "played_dynasty_id": 174, "played_dread_raw": 1680000,
            "total_count": 4, "returned_count": 4, "collection_complete": True,
            "prisoners": [{
                "source_ordinal": ordinal, "prisoner_character_id": character_id,
                "collection_owner_character_id": 29829, "jailer_character_id": 29829,
                "custody_relation_verified": True, "house_id": house_id,
                "dynasty_id": dynasty_id, "same_house": False, "same_dynasty": False,
                "is_child_of_played_character": False, "primary_title_tier_raw": tier,
                "unconditional_release_preview": {
                    "private_build": True, "read_only": True, "advertised": False,
                    "action_surface_present": False, "status": "unavailable",
                    "unavailable_reason": "release_preview_not_enabled_for_12002_ransom",
                },
                "ransom_quote_preview": {
                    "private_build": True, "read_only": True, "advertised": False,
                    "action_surface_present": False, "status": "unavailable",
                    "unavailable_reason": "role_unavailable" if ordinal == 0 else "not_evaluated",
                },
            } for ordinal, (character_id, house_id, dynasty_id, tier) in enumerate(custody_rows)],
        },
    }
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
            check(request["type"] == "execute_step" and request["step"] in (step, collection_step),
                  "only the two existing readonly queries are dispatched")
            if request["step"] == step:
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
                } if request["step"] == step else collection_native,
            })
        def close(self) -> None:
            pass
        def transport_error(self):
            return None

    async def exercise() -> dict:
        endpoint = Endpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                              command_timeout_seconds=0.1)
        driver.allow_private_prisoner_collection_query = True
        endpoint.publish({
            "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 7878, "session_generation": 0,
            "game_version": native["build"]["version"],
            "expected_ck3_version": native["build"]["version"],
            "executable_sha256": native["build"]["exe_sha256"],
            "capabilities": ["game.state.snapshot", capability, "game.command." + reply],
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
        collection_name = "ck3_query_player_prisoner_collection_private_v1"
        check(collection_name in {tool.name for tool in await server.list_tools()},
              "existing private collection query is registered")
        collection_response = await server.call_tool(collection_name, {
            "expected_revision": driver.take_snapshot()["revision"],
        })
        check(not collection_response.is_error, "actual private transport accepts captured721 metadata")
        metadata = collection_response.structured_content
        snapshot = driver.take_snapshot()
        commands = snapshot["native_command_history"]
        check(len(commands) == 2 and commands[1]["command"] == collection_step,
              "both readonly queries reach the real driver history")
        check(commands[1]["result"] == metadata
              and metadata["queried_revision"] == snapshot["revision"]
              and metadata["queried_native_revision"] == snapshot["native_revision"]
              and metadata["queried_snapshot_id"] == snapshot["snapshot_id"],
              "validated transport wrapper is retained by the production recording hook")
        planned_response = await server.call_tool("ck3_plan_turn", {})
        check(not planned_response.is_error, "registered planner consumes actual recorded observations")
        planned = planned_response.structured_content["plan"]
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
        own[1]["result"]["player_prisoner_collection"]["prisoners"][3]["same_dynasty"] = True
        own_plan = choose_one_life_turn(own, snapshot=snapshot, action_steps=[step, reply])
        check(own_plan["selected_step"] is None,
              "existing dynasty qualification prevents accepting own-dynasty release")
        zero = copy.deepcopy(commands)
        zero_context = zero[0]["result"]["pending_character_interaction_context"]
        zero_context["terms"]["ransom_quote"]["value"]["gold_raw"] = 0
        zero_plan = choose_one_life_turn(zero, snapshot=snapshot, action_steps=[step, reply])
        check(zero_plan["selected_step"] is None, "zero quote adds no monetary accept value")
        actual["new_ordinary_ransom_planner_fixture"] = planned
        actual["recorded_prisoner_collection_fixture"] = metadata
        check(len(endpoint.frames) == 2, "two readonly registered queries and no action")
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
                       readonly_mcp_queries=2, registered_planner_calls=1,
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
