"""One NEW registered normal receipt compound; Root FIRST NOT RUN.

Run as a standalone script after the new native whole target writes its five
packets. The idle baseline is fixture-selected; production release planning,
normal typed dispatch, Driver transport and registered wrappers are retained.
No native submit is replayed, and synthetic postconditions have no live credit.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


_CASES = {
    "retained-free": ("applied", True, True),
    "retained-held-player": ("pending", False, False),
    "retained-held-other": ("transferred", False, True),
    "retained-dead": ("dead", False, True),
    "retained-unavailable": ("pending", False, False),
}
_QUERY = "query-player-prisoner-collection-private-v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-fixture-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge import mcp_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.bridge.prisoner_retained_target_state_contract_12004 import (
        normalize_prisoner_retained_target_state_12004,
    )
    from xar_autoplayer.prisoner_release_formal_consumer import (
        _LEDGER, plan_release_formal, read_release_ledger,
    )
    from xar_autoplayer.prisoner_release_receipt_consumer_12004 import RECEIPT_STEP

    checks = 0
    inputs = {}
    wires = {}
    for case in _CASES:
        path = args.native_fixture_dir / f"{case}.json"
        raw = path.read_bytes()
        wires[case] = json.loads(raw)
        inputs[case] = {"path": str(path), "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest()}

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    class IdleFixtureService(GameplayBridgeService):
        # Only the unrelated underlying campaign arbitration is fixed to idle.
        # The new production release planner and Service dispatch are exercised.
        def plan_turn(self):
            snapshot = self.driver.take_snapshot()
            planned = {"snapshot_id": snapshot["snapshot_id"],
                       "revision": snapshot["revision"],
                       "plan": {"selected_step": "life-advance", "phase": "fixture_idle"}}
            return plan_release_formal(self.driver, planned, snapshot)

    class Endpoint:
        pipe_name = r"\\.\pipe\xar_prisoner_retained_receipt_fixture"

        def __init__(self, wire):
            self.wire = wire
            self.requests = []

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def publish(self, value):
            self.on_frame(copy.deepcopy(value))

        def send(self, request):
            if request.get("type") == "ping":
                return
            leaf = self.wire["prisoner_retained_target_state"]
            check(request.get("type") == "execute_step" and request.get("step") == _QUERY,
                  "only the existing retained-target read is sent, never release submit")
            check(request["release_material_target_character_id"] == leaf["target_character_id"],
                  "the original full target ID reaches the native request")
            check(request["expected_revision"] == leaf["snapshot_revision"],
                  "the actual Driver maps current public revision to native revision")
            self.requests.append(copy.deepcopy(request))
            self.publish({"type": "command_result", "protocol_version": 1,
                          "request_id": request["request_id"], "ok": True,
                          "result": self.wire})

        def close(self):
            pass

        def transport_error(self):
            return None

    async def exercise():
        results = {}
        for case, (status, material, terminal) in _CASES.items():
            wire = wires[case]
            leaf = wire["prisoner_retained_target_state"]
            actor, target = leaf["actor_character_id"], leaf["target_character_id"]
            native, date = leaf["snapshot_revision"], leaf["date_raw"]
            check(wire["step"] == _QUERY, f"{case}: new whole native collection packet")
            with tempfile.TemporaryDirectory() as temporary:
                state_dir = Path(temporary)
                endpoint = Endpoint(wire)
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=.1,
                    state_dir=state_dir,
                )
                driver.allow_private_prisoner_collection_query = True
                driver.allow_private_prisoner_ransom_action = True
                try:
                    endpoint.publish({
                        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                        "pid": 80808, "session_generation": 0,
                        "game_version": leaf["build_version"],
                        "expected_ck3_version": leaf["build_version"],
                        "executable_sha256": leaf["executable_sha256"],
                        "capabilities": ["game.state.snapshot", "game.command." + _QUERY],
                    })
                    endpoint.publish({
                        "type": "state_snapshot", "protocol_version": 1,
                        "snapshot_id": f"native:{native}", "revision": native,
                        "state": {"phase": "map_hud", "date": "synthetic:retained-custody",
                                  "date_raw": date, "speed": 1, "paused": True, "map_ready": True,
                                  "history": [], "active_event": None,
                                  "pending_character_interaction": None,
                                  "played_character": {"character_id": actor, "alive": True},
                                  "one_life_settlement": None, "active_wars": [], "player_armies": []},
                    })
                    original = {
                        "stage": "receipt_pending", "material_result": False,
                        "player_character_id": actor, "prisoner_character_id": target,
                        "pre_native_revision": native - 1, "pre_date_raw": date - 1,
                        "release_query_sequence": 91,
                        "release_option_keys": [], "release_option_mask_bits": 0,
                        "action_ack": {"status": "submitted_verification_pending",
                                       "material_result": False, "request_id": "fixture-original-release"},
                    }
                    # Historical one-key pending files remain compatible.
                    (state_dir / _LEDGER).write_text(json.dumps({"pending": original}), encoding="utf-8")
                    with patch.object(mcp_server, "GameplayBridgeService", IdleFixtureService):
                        server = mcp_server.create_server(driver)
                    tools = {tool.name for tool in await server.list_tools()}
                    check("ck3_auto_turn" in tools and "ck3_query_player_prisoner_collection_private_v1" in tools,
                          "actual registered normal turn and existing query are present")
                    response = await server.call_tool("ck3_auto_turn", {})
                    check(not response.is_error, f"{case}: registered normal typed receipt dispatch")
                    outcome = response.structured_content
                    result = outcome["result"]
                    check(outcome["selected_step"] == RECEIPT_STEP and outcome["status"] == "executed",
                          f"{case}: ordinary pending selects the receipt, not a submit")
                    check(result["status"] == status and result["material_result"] is material,
                          f"{case}: free/held/transfer/death/unavailable remain distinct")
                    check(result["postcondition_verified"] is material
                          and result["release_causation_observed"] is False
                          and result["command_costs_verified"] is False,
                          f"{case}: freedom postcondition does not fabricate causation or fees")
                    check(result["source_pending"] == original and result["current_target_state"] == leaf,
                          f"{case}: original ACK and independent full target state are retained")
                    readback = result["independent_readback"]
                    check(all(readback.get(key) == value for key, value in wire.items()),
                          f"{case}: complete new native packet survives strict normalization")
                    check(readback["queried_native_revision"] == native
                          and readback["queried_release_material_target_character_id"] == target,
                          f"{case}: real transport binds the independent current frame and full target")
                    ledger = read_release_ledger(state_dir)
                    check((ledger["pending"] is None) is terminal,
                          f"{case}: only verified terminal state resolves pending")
                    check(ledger["resolved"] == result if terminal else
                          ledger["pending"]["last_receipt"] == result,
                          f"{case}: ordinary durable result remains observable")
                    check(len(endpoint.requests) == 1, f"{case}: one fresh query, zero actions")
                    history = driver.take_snapshot()["native_command_history"]
                    check(history[-1]["command"] == _QUERY and history[-1]["result"] == readback,
                          f"{case}: production Driver history retains validated full readback")
                    # No real native repeat: test unchanged-frame suppression at planner level.
                    if not terminal:
                        plan = IdleFixtureService(driver).plan_turn()["plan"]
                        check(plan["selected_step"] == "life-advance",
                              f"{case}: same checked paused frame is not re-read or re-submitted")
                    malformed = copy.deepcopy(leaf)
                    malformed["target_character_id"] = target ^ 0x01000000
                    try:
                        normalize_prisoner_retained_target_state_12004(
                            malformed, native_revision=native, date_raw=date,
                            player_character_id=actor, target_character_id=target,
                        )
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("full generation target mismatch accepted")
                    checks_before = len(endpoint.requests)
                    results[case] = {"outcome": outcome, "ledger": ledger,
                                     "requests": endpoint.requests,
                                     "full_id_mismatch_rejected": True}
                    check(checks_before == 1, "pure mismatch control does not send a native query")
                finally:
                    driver.close()
        return results

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.prisoner-retained-release-registered-compound-12004-v1",
              "status": "RED", "source_root": str(args.source_root), "native_inputs": inputs,
              "game_sdk_process_actions": 0, "native_submits": 0,
              "qualification": "new synthetic whole-native packets; no live credit"}
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(json.dumps(observed, indent=2) + "\n", encoding="utf-8")
        report.update(status="GREEN", checks=checks, cases=len(_CASES), readonly_queries=len(_CASES))
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}")
        raise
    finally:
        report["checks"] = checks
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
