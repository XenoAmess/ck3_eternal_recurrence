"""Actual4 registered ransom action and cold formal receipt compound.

AUTHORED_NOTRUN. Root alone runs this migration FIRST against five newly
compiled producer packets. Native calls use fixture-owned memory; later
custody/gold facts are synthetic. Pending ACKs give no material/live credit.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import sys


_CASES = (
    "queued_pending", "queued_applied", "queued_ambiguous",
    "quote_changed", "queue_failure",
)
_OFFERS = {
    "queued_pending": ("gold", 9_000_000, False),
    "queued_applied": ("current_gold", 12_000_000, True),
    "queued_ambiguous": ("current_gold", 12_000_000, True),
    "quote_changed": ("current_gold", 12_000_000, True),
    "queue_failure": ("current_gold", 12_000_000, True),
}
_RECEIPTS = {
    "queued_pending": ("pending", 0, False),
    "queued_applied": ("applied", 7_000_000, True),
    "queued_ambiguous": ("ambiguous", 0, False),
}
_QUERY_STEP = "query-player-prisoner-collection-private-v1"
_ACTION_STEP = "submit-player-prisoner-ransom-private-v1"
_QUERY_TOOL = "ck3_query_player_prisoner_collection_private_v1"
_ACTION_TOOL = "ck3_ransom_player_prisoner_private_v1"
_GAME_VERSION = "1.20.0.4"
_EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-fixture-dir", "--native-fixtures-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.prisoner_ransom_formal_consumer import (
        read_ransom_ledger, read_ransom_receipt_private, submit_ransom_private,
    )

    packets = {}
    native_inputs = {}
    for case in _CASES:
        path = args.native_fixture_dir / f"{case}.json"
        raw = path.read_bytes()
        packets[case] = json.loads(raw)
        native_inputs[case] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}

    checks = 0
    action_calls = 0
    receipt_reads = 0
    observed = {}
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    class Endpoint:
        pipe_name = r"\\.\pipe\xar_prisoner_ransom_action_12004_fixture"

        def __init__(self, packet: dict) -> None:
            self.packet = packet
            self.requests = []
            self.on_frame = None
            self.post = False

        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame

        def publish(self, packet: dict) -> None:
            self.on_frame(copy.deepcopy(packet))

        def send(self, request: dict) -> None:
            if request.get("type") == "ping":
                return
            check(request.get("type") == "execute_step",
                  "the real driver sends the existing native command protocol")
            self.requests.append(copy.deepcopy(request))
            if request.get("step") == _QUERY_STEP:
                name = "post_collection" if self.post else "before_collection"
                wire = self.packet[name]
                check(request.get("expected_revision") == wire["snapshot_revision"],
                      "the actual collection request binds the producer's native frame")
                self.publish({
                    "type": "command_result", "protocol_version": 1,
                    "request_id": request["request_id"], "ok": True,
                    "result": wire,
                })
                return
            check(request.get("step") == _ACTION_STEP and self.post is False,
                  "only one existing ransom action is dispatched on the pre frame")
            quote = self.packet["before_collection"]["player_prisoner_collection"][
                "prisoners"][0]["ransom_quote_preview"]
            check(request.get("expected_revision") == 1014
                  and request.get("quote_query_sequence") == 1
                  and request.get("prisoner_character_id") == 61540
                  and request.get("payer_character_id") == 73000
                  and request.get("quoted_gold_raw") == quote["quoted_gold_raw"]
                      == _OFFERS[self.packet["scenario"]][1],
                  "the registered action forwards the actual latest native offer")
            # Preserve the production serializer's complete ACK/error frame.
            # Only its fixture transport correlation token is rebound to UUID.
            wire = copy.deepcopy(self.packet["command_result"])
            wire["request_id"] = request["request_id"]
            self.publish(wire)

        def close(self) -> None:
            pass

        def transport_error(self):
            return None

    report = {
        "schema": "xar.prisoner-ransom-action-registered-mcp-12004.v1",
        "status": "RED", "source_root": str(args.source_root),
        "native_inputs": native_inputs,
        "fixture_expected_game_version": _GAME_VERSION,
        "fixture_expected_executable_sha256": _EXE_SHA256,
        "qualification": "synthetic-native-fixture",
        "planned_action_option_branches": ["gold", "current_gold"],
        "live_queries": 0, "game_actions": 0,
        "production_live_action_qualified": False,
        "full_effect_readiness_qualified": False,
    }
    try:
        for case in _CASES:
            packet = packets[case]
            check(packet["scenario"] == case, f"{case}: the genuine producer packet matches its file")
            option, amount, acceptance_time = _OFFERS[case]
            endpoint = Endpoint(packet)
            state_dir = args.output_dir / case / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
                command_timeout_seconds=0.1,
                allow_private_prisoner_collection_query=True,
                allow_private_prisoner_ransom_action=True,
            )
            try:
                endpoint.publish({
                    "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                    "pid": 7878, "session_generation": 0,
                    "game_version": _GAME_VERSION, "expected_ck3_version": _GAME_VERSION,
                    "executable_sha256": _EXE_SHA256,
                    "capabilities": ["game.state.snapshot", "game.command." + _QUERY_STEP,
                                     "game.command." + _ACTION_STEP],
                })
                endpoint.publish(packet["before_snapshot"])
                server = create_server(driver)
                tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
                check(_QUERY_TOOL in tools and _ACTION_TOOL in tools
                      and tools[_QUERY_TOOL].annotations.read_only_hint is True,
                      f"{case}: the existing query and action are actually registered")
                before = driver.take_snapshot()
                response = asyncio.run(server.call_tool(_QUERY_TOOL, {
                    "expected_revision": before["revision"], "ransom_ordinal": 0,
                }))
                check(not response.is_error, f"{case}: actual transport accepts the whole pre collection")
                collection = response.structured_content
                check(all(collection.get(key) == value for key, value in packet["before_collection"].items())
                      and collection["exact_ck3_build"] == _GAME_VERSION
                      and collection["exe_sha256"].upper() == _EXE_SHA256,
                      f"{case}: whole native fields and actual4 provenance survive")
                rows = collection["player_prisoner_collection"]["prisoners"]
                check(len(rows) == 1 and rows[0]["prisoner_character_id"] == 61540,
                      f"{case}: the sole held prisoner is a native collection row")
                quote = rows[0]["ransom_quote_preview"]
                check(quote["selected_option"] == option
                      and quote["quoted_gold_raw"] == amount
                      and quote["amount_is_acceptance_time_quote"] is acceptance_time
                      and quote["recipient_answer_status_raw"] == 1,
                      f"{case}: the native gold/current-gold offer matches its scene and timing")
                choice = {
                    "collection": collection, "prisoner_character_id": rows[0]["prisoner_character_id"],
                    "payer_character_id": quote["payer_character_id"],
                    "selected_option": quote["selected_option"],
                    "quoted_gold_raw": quote["quoted_gold_raw"],
                    "amount_is_acceptance_time_quote": quote["amount_is_acceptance_time_quote"],
                }
                action_responses = []

                class RegisteredSubmitDriver:
                    """Route formal submission through this actual registered MCP."""
                    state_dir = driver.state_dir

                    def take_snapshot(self):
                        return driver.take_snapshot()

                    def capabilities(self):
                        return driver.capabilities()

                    def submit_player_prisoner_ransom_private_v1(self, *, collection, prisoner_character_id):
                        nonlocal action_calls
                        ledger = read_ransom_ledger(self.state_dir)
                        check(ledger["pending"]["stage"] == "submission_unresolved"
                              and ledger["pending"]["pre_player_gold_raw"] == 5000000,
                              f"{case}: the existing formal writer persists the fence before send")
                        action_calls += 1
                        result = asyncio.run(server.call_tool(_ACTION_TOOL, {
                            "collection": collection, "prisoner_character_id": prisoner_character_id,
                        }))
                        action_responses.append({
                            "is_error": result.is_error,
                            "structured_content": result.structured_content,
                            "text": [item.text for item in result.content if hasattr(item, "text")],
                        })
                        if result.is_error:
                            raise BridgeUnavailableError("registered native ransom rejected: " +
                                                         " ".join(action_responses[-1]["text"]))
                        return result.structured_content

                failure = None
                try:
                    pending = submit_ransom_private(
                        RegisteredSubmitDriver(), plan={"prisoner_ransom_choice": choice},
                    )
                except BridgeUnavailableError as error:
                    if case in _RECEIPTS:
                        raise
                    failure = str(error)
                    pending = None
                check(len(action_responses) == 1,
                      f"{case}: the formal path calls the registered action exactly once")
                cold = read_ransom_ledger(state_dir)
                receipt = None
                if case in _RECEIPTS:
                    ack = action_responses[0]["structured_content"]
                    check(action_responses[0]["is_error"] is False
                          and ack["status"] == "submitted_verification_pending"
                          and ack["material_result"] is False
                          and ack["selected_option"] == option
                          and ack["quoted_gold_raw"] == amount
                          and ack["exact_ck3_build"] == _GAME_VERSION
                          and ack["exe_sha256"].upper() == _EXE_SHA256,
                          f"{case}: the actual registered ACK identifies actual4 and stays nonmaterial")
                    check(cold["pending"] == pending and cold["resolved"] is None
                          and cold["pending"]["stage"] == "receipt_pending"
                          and cold["pending"]["selected_option"] == option
                          and cold["pending"]["quoted_gold_raw"] == amount
                          and cold["pending"]["amount_is_acceptance_time_quote"] is acceptance_time
                          and cold["pending"]["action_ack"] == ack,
                          f"{case}: cold reload retains the original formal pending ACK")
                    endpoint.post = True
                    endpoint.publish(packet["post_snapshot"])
                    check(driver.take_snapshot()["native_revision"] == 1015
                          and driver.take_snapshot()["date_raw"] == 53286361,
                          f"{case}: the receipt reads independent later producer facts")
                    receipt = read_ransom_receipt_private(driver, pending=cold["pending"])
                    receipt_reads += 1
                    expected, gain, applied = _RECEIPTS[case]
                    check(receipt["status"] == expected
                          and receipt["material_result"] is applied
                          and receipt["postcondition_verified"] is applied
                          and receipt["observed_player_gold_gain_raw"] == gain
                          and receipt["quoted_gold_raw"] == amount
                          and receipt["amount_is_acceptance_time_quote"] is acceptance_time,
                          f"{case}: existing payment logic distinguishes held, paid and ambiguous")
                    check(receipt["prisoner_no_longer_held"] is (case != "queued_pending"),
                          f"{case}: independent custody agrees with the actual receipt")
                    recovered = read_ransom_ledger(state_dir)
                    check((recovered["pending"] is None and recovered["resolved"] == receipt)
                          if applied else (recovered["pending"] is not None
                                           and recovered["resolved"] is None),
                          f"{case}: only observed material payment resolves the durable ledger")
                else:
                    check(failure is not None and action_responses[0]["is_error"] is True
                          and cold["pending"]["stage"] == "submission_unresolved"
                          and cold["resolved"] is None
                          and "action_ack" not in cold["pending"],
                          f"{case}: native fresh-quote/queue RED supplies no pending ACK or material receipt")
                history = driver.take_snapshot()["native_command_history"]
                check(sum(request["step"] == _ACTION_STEP for request in endpoint.requests) == 1
                      and sum(request["step"] == _QUERY_STEP for request in endpoint.requests)
                          == (2 if case in _RECEIPTS else 1),
                      f"{case}: there is one action and only required pre/post collection reads")
                latest = packet["post_collection"] if case in _RECEIPTS else packet["before_collection"]
                check(history[-1]["command"] == _QUERY_STEP
                      and all(history[-1]["result"].get(key) == value for key, value in latest.items()),
                      f"{case}: existing driver history preserves the genuine last whole collection")
                observed[case] = {
                    "collection": collection, "action_responses": action_responses,
                    "cold_pending_ledger": cold, "receipt": receipt, "error": failure,
                    "final_ledger": read_ransom_ledger(state_dir),
                    "requests": endpoint.requests, "native_command_history": history,
                    "native_expectations": packet["native_expectations"],
                }
            finally:
                driver.close()
        check(action_calls == 5 and receipt_reads == 3,
              "five real registered fixture actions and three independent cold receipts")
        with (args.output_dir / "observed.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(observed, ensure_ascii=False, indent=2) + "\n")
        report.update(status="GREEN", checks=checks, cases=len(_CASES),
                      registered_action_calls=action_calls, registered_readonly_queries=len(_CASES),
                      cold_receipt_reads=receipt_reads, receipt_collection_queries=receipt_reads,
                      registered_action_option_branches=sorted({
                          observed[case]["action_responses"][0]["structured_content"]["selected_option"]
                          for case in _RECEIPTS
                      }))
    except Exception as error:
        report.update(checks=checks, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
