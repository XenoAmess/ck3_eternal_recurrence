"""One source-authored connected compound; FIRST NOTRUN.

Consumes the NEW native cache/whole fixture and labelled actual008 validated
readback. The only submit response reproduces the actual pre-mailbox rejection;
no successful ACK or future legal native answer is fabricated.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-fixture-dir", type=Path, required=True)
    parser.add_argument("--actual-receipt-response", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge import mcp_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.bridge.player_prisoner_collection_private_transport import _ENVELOPE_KEYS
    from xar_autoplayer.prisoner_release_formal_consumer import (
        _LEDGER, SUBMIT_STEP, plan_release_formal, read_release_ledger,
    )

    cache = json.loads((args.native_fixture_dir / "CACHE-FIRST.json").read_text(encoding="utf-8"))
    fresh_packet = json.loads((args.native_fixture_dir / "lifecycle-next.json").read_text(encoding="utf-8"))
    actual = json.loads(args.actual_receipt_response.read_text(encoding="utf-8"))["result"]
    outcome = actual.get("structured_content")
    if not isinstance(outcome, dict):
        outcome = next(json.loads(block["text"]) for block in actual["content"]
                       if block["type"] == "text" and block["text"].lstrip().startswith("{"))
    prior_receipt = outcome["result"]
    actual_readback = prior_receipt["independent_readback"]
    # Drop only transport-wrapper provenance. Keep every original native
    # envelope/collection/leaf value; label this as validated readback reuse.
    keys = set(_ENVELOPE_KEYS) | {"prisoner_release_material_opinion",
                                 "prisoner_keeper_opinion", "prisoner_retained_target_state"}
    observed_wire = {key: copy.deepcopy(value) for key, value in actual_readback.items() if key in keys}
    observed_packet = {"type": "command_result", "protocol_version": 1,
                       "request_id": "fixture-derived-validated-readback", "ok": True,
                       "result": observed_wire}
    checks = 0

    def check(value, message):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(message)

    check(cache["held_preserved"] and cache["absence_closed"] and cache["old_terms_invalidated"]
          and cache["native_actions"] == 0, "new compiled production lifecycle controls passed")
    check(prior_receipt["status"] == "applied" and prior_receipt["prisoner_character_id"] == 56063
          and prior_receipt["current_target_state"]["custody_state"] == "free",
          "reuse the actual prior terminal receipt, without inventing an ACK")
    actor = observed_wire["player_prisoner_collection"]["played_character_id"]
    native = observed_wire["snapshot_revision"]
    date = observed_wire["player_prisoner_collection"]["date_raw"]

    class Endpoint:
        pipe_name = r"\\.\pipe\xar_release_stale_lifecycle_fixture"

        def __init__(self):
            self.packet = observed_packet
            self.requests = []

        def start(self, on_frame, on_disconnect):
            self.on_frame = on_frame

        def publish(self, frame):
            self.on_frame(copy.deepcopy(frame))

        def send(self, request):
            if request.get("type") == "ping":
                return
            self.requests.append(copy.deepcopy(request))
            if request["step"] == "submit-player-prisoner-release-private-v1":
                self.publish({"type": "command_result", "protocol_version": 1,
                              "request_id": request["request_id"], "ok": False,
                              "error": "private release terms or request are stale"})
            else:
                check(request["step"] == "query-player-prisoner-collection-private-v1",
                      "refresh uses the existing collection token")
                frame = copy.deepcopy(self.packet)
                frame["request_id"] = request["request_id"]
                self.publish(frame)

        def close(self):
            pass

        def transport_error(self):
            return None

    class IdleFixtureService(GameplayBridgeService):
        def plan_turn(self):
            snapshot = self.driver.take_snapshot()
            baseline = {"snapshot_id": snapshot["snapshot_id"], "revision": snapshot["revision"],
                        "plan": {"selected_step": "life-advance", "phase": "fixture_idle"}}
            return plan_release_formal(self.driver, baseline, snapshot)

    async def exercise():
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            endpoint = Endpoint()
            driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                state_dir=state_dir, command_timeout_seconds=.1)
            driver.allow_private_prisoner_collection_query = True
            driver.allow_private_prisoner_ransom_action = True
            try:
                identity = observed_wire["prisoner_retained_target_state"]
                endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                    "pid": 80809, "session_generation": 0,
                    "game_version": identity["build_version"],
                    "expected_ck3_version": identity["build_version"],
                    "executable_sha256": identity["executable_sha256"],
                    "capabilities": ["game.state.snapshot",
                        "game.command.query-player-prisoner-collection-private-v1"]})
                endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
                    "snapshot_id": f"native:{native}", "revision": native,
                    "state": {"phase": "map_hud", "date": "fixture:stale-lifecycle", "date_raw": date,
                        "speed": 1, "paused": True, "map_ready": True, "history": [],
                        "active_event": None, "pending_character_interaction": None,
                        "played_character": {"character_id": actor, "alive": True},
                        "one_life_settlement": None, "active_wars": [], "player_armies": []}})
                driver.query_player_prisoner_collection_private_v1(
                    expected_revision=driver.take_snapshot()["revision"],
                    release_material_target_character_id=56063)
                prior_ledger = {"pending": None, "resolved": prior_receipt}
                (state_dir / _LEDGER).write_text(json.dumps(prior_ledger), encoding="utf-8")
                with patch.object(mcp_server, "GameplayBridgeService", IdleFixtureService):
                    server = mcp_server.create_server(driver)
                before = len(endpoint.requests)
                rejected = await server.call_tool("ck3_auto_turn", {})
                check(not rejected.is_error, "exact pre-mailbox rejection is consumed by the normal typed path")
                result = rejected.structured_content
                check(result["selected_step"] == SUBMIT_STEP and
                      result["result"]["status"] == "rejected_before_submit" and
                      result["result"]["material_result"] is False,
                      "no action/ACK is credited for the actual rejection kind")
                check(len(endpoint.requests) == before + 1 and
                      endpoint.requests[-1]["step"] == "submit-player-prisoner-release-private-v1",
                      "the failed call sends once and never retries")
                check(read_release_ledger(state_dir) == prior_ledger,
                      "only the new no-ACK pending rolls back; original prior receipt stays intact")
                failed_id = endpoint.requests[-1]["request_id"]
                check(result["result"]["request_id"] == failed_id,
                      "returned rejection keeps its real fixture command correlation")
                endpoint.packet = fresh_packet
                refreshed = await server.call_tool("ck3_auto_turn", {})
                check(not refreshed.is_error, "next normal registered turn performs a fresh collection query")
                fresh = refreshed.structured_content
                check(fresh["selected_step"] == "query-player-prisoner-collection-private-v1" and
                      fresh["result"]["query_sequence"] == fresh_packet["result"]["query_sequence"],
                      "compiled new whole packet passes unchanged through actual strict/Driver/Service/MCP")
                check(sum(row["step"] == "submit-player-prisoner-release-private-v1"
                          for row in endpoint.requests) == 1, "refresh does not resend the rejected submit")
                plan = IdleFixtureService(driver).plan_turn()["plan"]
                check(plan["selected_step"] == "life-advance" and
                      plan["prisoner_release_observation"]["status"] == "input_unavailable",
                      "fresh actual unavailable offer is respected; no legal/send value is invented")
                check(driver._prisoner_release_requery_required is None,
                      "old query invalidation clears only after a genuinely different validated query")
                return {"native_cache": cache, "rejected": result, "refreshed": fresh,
                        "ledger": read_release_ledger(state_dir), "requests": endpoint.requests}
            finally:
                driver.close()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "xar.prisoner-release-stale-connected-first-12004-v1",
              "status": "RED", "actual_source": str(args.actual_receipt_response),
              "actual_input_kind": "validated existing readback reused, derived software envelope",
              "new_native_fixture": str(args.native_fixture_dir), "live_credit": False,
              "successful_ACKs_created": 0, "game_sdk_process_actions": 0}
    try:
        observed = asyncio.run(exercise())
        (args.output_dir / "observed.json").write_text(json.dumps(observed, indent=2) + "\n", encoding="utf-8")
        report.update(status="GREEN", checks=checks, connected_compounds=1)
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}")
        raise
    finally:
        report["checks"] = checks
        with (args.output_dir / "RESULT.json").open("x", encoding="utf-8") as out:
            out.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
