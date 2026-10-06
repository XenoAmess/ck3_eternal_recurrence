"""FIRST registered-MCP compound for six new negotiated whole collection wires.

Prepared FIRST_NOT_RUN. Root alone runs this after the new native producer.
Callbacks/definition/costs are synthetic; no live observation or release effect
is qualified, and no existing release or kinship FIRST matrix is invoked.
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
    "gain_hook_accepted", "gain_hook_refused", "gain_hook_native_false",
    "gain_hook_mask_changed", "renounce_claims_gain_hook", "change_prison_auto_accept",
)
_REQUESTS = {
    "gain_hook_accepted": (["gain_hook"], 8),
    "gain_hook_refused": (["gain_hook"], 8),
    "gain_hook_native_false": (["gain_hook"], 8),
    "gain_hook_mask_changed": (["gain_hook"], 8),
    "renounce_claims_gain_hook": (["renounce_claims", "gain_hook"], 10),
    "change_prison_auto_accept": (["change_prison"], 32),
}
_NATIVE_ANSWERS = {
    "gain_hook_accepted": (5_000_001, 0, True),
    "gain_hook_refused": (-5_000_002, 2, False),
    "renounce_claims_gain_hook": (2_500_003, 1, True),
}
_STEP = "query-player-prisoner-collection-private-v1-ransom-ordinal-2"
_TOOL = "ck3_query_player_prisoner_collection_private_v1"
_EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
_PRISONERS = [54235, 56063, 61540, 70766]
_COSTS = [100_001 * index for index in range(1, 11)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--native-fixture-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.mcp_server import create_server
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.prisoner_negotiated_preview_contract_12003 import (
        normalize_prisoner_negotiated_preview_12003,
    )
    from xar_autoplayer.bridge.prisoner_release_preview_contract_12003 import (
        RELEASE_COST_KEYS_12003, RELEASE_OPTION_KEYS_12003,
    )

    native_wires, native_inputs = {}, {}
    for case in _CASES:
        path = args.native_fixture_dir / f"{case}.json"
        raw = path.read_bytes()
        native_wires[case] = json.loads(raw)
        native_inputs[case] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}

    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    class Endpoint:
        pipe_name = r"\\.\pipe\xar_prisoner_negotiated_12003_fixture"

        def __init__(self) -> None:
            self.requests = []
            self.on_frame = None
            self.case = None

        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame

        def publish(self, packet: dict) -> None:
            self.on_frame(copy.deepcopy(packet))

        def send(self, request: dict) -> None:
            if request.get("type") == "ping":
                return
            check(request.get("type") == "execute_step" and request.get("step") == _STEP,
                  "registered MCP dispatches the existing selected-ordinal read-only step")
            check(request.get("expected_revision") == 1014,
                  "actual request binds the native public revision")
            check(request.get("protocol_version") == 1 and "played_character_id" not in request,
                  "actual protocol shape and native player role are preserved")
            check(self.case in native_wires, "the new native whole fixture exists")
            keys, mask = _REQUESTS[self.case]
            check(type(request.get("release_option_mask_bits")) is int
                  and request["release_option_mask_bits"] == mask,
                  "production transport maps explicit authored keys to actual numeric request mask")
            check("release_option_keys" not in request,
                  "native compact request carries the numeric mask")
            self.requests.append(copy.deepcopy(request))
            # Forward the complete production-serialized native envelope intact.
            # No selected mask, CanSend, answer, row or queried_* field is invented.
            self.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": native_wires[self.case],
            })

        def close(self) -> None:
            pass

        def transport_error(self):
            return None

    async def exercise() -> dict:
        endpoint = Endpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.1,
        )
        driver.allow_private_prisoner_collection_query = True
        observed = {}
        try:
            endpoint.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 7878, "session_generation": 0,
                "game_version": "1.20.0.3", "expected_ck3_version": "1.20.0.3",
                "executable_sha256": _EXE_SHA256,
                "capabilities": ["game.state.snapshot", "game.command." + _STEP],
            })
            endpoint.publish({
                "type": "state_snapshot", "protocol_version": 1,
                "snapshot_id": "native:1014", "revision": 1014,
                "state": {
                    "phase": "map_hud", "date": "synthetic:release-source721",
                    "date_raw": 53286360, "speed": 1, "paused": True, "map_ready": True,
                    "history": [], "active_event": None,
                    "pending_character_interaction": None,
                    "played_character": {"character_id": 29829, "alive": True},
                    "one_life_settlement": None, "active_wars": [], "player_armies": [],
                },
            })
            server = create_server(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            check(_TOOL in tools, "actual existing private collection MCP is registered")
            check(tools[_TOOL].annotations.read_only_hint is True,
                  "actual registered tool is read-only")
            for index, case in enumerate(_CASES):
                endpoint.case = case
                keys, mask = _REQUESTS[case]
                wire = native_wires[case]
                check(isinstance(wire, dict) and wire.get("step") == _STEP
                      and not any(key.startswith("queried_") for key in wire),
                      f"{case}: actual native envelope contains no invented transport provenance")
                before = driver.take_snapshot()
                response = await server.call_tool(_TOOL, {
                    "expected_revision": before["revision"], "ransom_ordinal": 2,
                    "release_option_keys": list(keys),
                })
                check(not response.is_error, f"{case}: actual registered compound accepts new whole wire")
                actual = response.structured_content
                observed[case] = actual
                check(all(actual.get(key) == value for key, value in wire.items()),
                      f"{case}: every native envelope and collection field survives normalization")
                check(actual["queried_release_option_keys"] == keys
                      and type(actual["queried_release_option_mask_bits"]) is int
                      and actual["queried_release_option_mask_bits"] == mask,
                      f"{case}: actual wrapper binds the explicit keys and numeric mask")
                check(actual["queried_revision"] == before["revision"]
                      and actual["queried_native_revision"] == 1014
                      and actual["queried_snapshot_id"] == "native:1014"
                      and actual["exact_ck3_build"] == "1.20.0.3"
                      and actual["exe_sha256"].upper() == _EXE_SHA256,
                      f"{case}: actual public/native/exact-build provenance is retained")
                collection = actual["player_prisoner_collection"]
                rows = collection["prisoners"]
                check(collection["schema_version"] == 7
                      and collection["snapshot_revision"] == 1014
                      and collection["date_raw"] == 53286360
                      and collection["played_character_id"] == 29829
                      and collection["played_house_id"] == collection["played_dynasty_id"] == 174
                      and collection["played_dread_raw"] == 1680000
                      and collection["collection_complete"] is True
                      and collection["total_count"] == collection["returned_count"] == 4,
                      f"{case}: schema7 retains all complete collection metadata")
                check([row["prisoner_character_id"] for row in rows] == _PRISONERS
                      and [row["source_ordinal"] for row in rows] == [0, 1, 2, 3]
                      and all(row["jailer_character_id"] == 29829
                              and row["collection_owner_character_id"] == 29829
                              and row["custody_relation_verified"] is True for row in rows)
                      and rows[2]["dynasty_id"] == 2237
                      and rows[2]["is_child_of_played_character"] is False
                      and rows[3]["primary_title_tier_raw"] == 3,
                      f"{case}: original full-ID/custody/lineage/child/title fields are retained")
                check(all("unconditional_release_preview" in row
                          and "ransom_quote_preview" in row
                          and "native_kinship" in row
                          and "negotiated_release_preview" in row for row in rows),
                      f"{case}: actual schema7 row is the requested negotiated/kinship union")
                check(all(row["negotiated_release_preview"]["requested_option_mask_bits"] == mask
                          for row in rows)
                      and all(row["negotiated_release_preview"].get("unavailable_reason") == "not_evaluated"
                              for ordinal, row in enumerate(rows) if ordinal != 2),
                      f"{case}: every returned row binds mask and only actual ordinal is evaluated")
                kinship = rows[2]["native_kinship"]
                check(kinship["status"] == "available"
                      and kinship["is_close_family_of_played_character"] is False
                      and kinship["is_close_or_extended_family_of_played_character"] is False
                      and kinship["source_ordinal"] == 2
                      and kinship["prisoner_character_id"] == 61540
                      and kinship["jailer_character_id"] == 29829
                      and kinship["proof_epoch"] == actual["observation_revision"]
                      and all(row["native_kinship"].get("unavailable_reason") == "not_evaluated"
                              for ordinal, row in enumerate(rows) if ordinal != 2),
                      f"{case}: actual native kinship control stays frame-bound in the union")
                preview = rows[2]["negotiated_release_preview"]
                detached = normalize_prisoner_negotiated_preview_12003(
                    preview, native_revision=1014, date_raw=53286360,
                    player_character_id=29829, prisoner_character_id=61540,
                    requested_option_mask_bits=mask,
                )
                check(detached == preview and detached is not preview,
                      f"{case}: production strict contract returns a detached actual observation")
                if case == "gain_hook_mask_changed":
                    check(preview["status"] == "unavailable"
                          and preview["unavailable_reason"] == "requested_release_options_not_retained"
                          and preview["observed_option_mask_bits"] == 0
                          and "selected_option_mask_bits" not in preview
                          and "can_send" not in preview and "acceptance" not in preview,
                          f"{case}: final native mask0 is a diagnostic rather than fabricated legal data")
                else:
                    sendable = case != "gain_hook_native_false"
                    check(preview["status"] == "available"
                          and preview["roles"] == {"actor_character_id": 29829,
                                                   "recipient_character_id": 61540}
                          and preview["puppet_or_actor_character_id"] == 29829
                          and preview["definition"]["canonical_key"] == "release_from_prison_interaction"
                          and preview["definition"]["runtime_ordinal"] == 186
                          and preview["definition"]["deterministic_key_hash"] == 0x51520123
                          and preview["option_keys"] == list(RELEASE_OPTION_KEYS_12003)
                          and len(preview["option_keys"]) == 13
                          and preview["selected_option_mask_bits"] == mask
                          and preview["can_send"] is sendable
                          and preview["proof_epoch"] == actual["observation_revision"],
                          f"{case}: actual finalized roles/all13 selection/native gate bind this whole wire")
                    costs = preview["costs"]
                    check(costs["raw_scale"] == 100000 and costs["payer_role"] == "actor"
                          and costs["application_timing"] == "on_send"
                          and [entry["resource_key"] for entry in costs["entries"]] ==
                              list(RELEASE_COST_KEYS_12003)
                          and [entry["raw"] for entry in costs["entries"]] == _COSTS,
                          f"{case}: ten distinct actual actor/on-send costs survive")
                    acceptance = preview["acceptance"]
                    if case in _NATIVE_ANSWERS:
                        score, status, would_accept = _NATIVE_ANSWERS[case]
                        check(acceptance == {
                            "auto_accept": False, "kind": "native_answer", "raw_scale": 100000,
                            "recipient_acceptance_score_raw": score,
                            "recipient_answer_status_raw": status,
                            "would_accept_now": would_accept,
                        }, f"{case}: exact actual score/native answer retains engine semantics")
                    elif case == "gain_hook_native_false":
                        check(acceptance == {"auto_accept": False, "kind": "not_evaluated_unsendable"},
                              f"{case}: observed native false gate preserves costs and typed absent answer")
                    else:
                        check(acceptance == {"auto_accept": True, "kind": "auto_accept",
                                             "would_accept_now": True},
                              f"{case}: actual change-prison autoaccept contains no invented score")
                    check(preview["readiness"]["acceptance_ready"] is sendable
                          and all(value is True for key, value in preview["readiness"].items()
                                  if key != "acceptance_ready"),
                          f"{case}: readiness applies only to actual current inputs")
                snapshot = driver.take_snapshot()
                history = snapshot["native_command_history"]
                check(len(history) == index + 1 and history[-1]["command"] == _STEP
                      and history[-1]["ok"] is True and history[-1]["result"] == actual,
                      f"{case}: actual production driver history records validated requested result")
                check(snapshot["native_revision"] == 1014 and snapshot["date_raw"] == 53286360
                      and snapshot["paused"] is True,
                      f"{case}: read-only compound leaves paused frame unchanged")
            check(len(endpoint.requests) == 6, "exactly six new negotiated queries; zero gameplay actions")
            return {"cases": observed, "requests": endpoint.requests,
                    "history": driver.take_snapshot()["native_command_history"]}
        finally:
            driver.close()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.prisoner-negotiated-registered-mcp-12003.v1",
        "status": "RED", "native_inputs": native_inputs, "source_root": str(args.source_root),
        "live_queries": 0, "game_actions": 0, "release_actions": 0,
        "old_release_first_runs": 0, "old_kinship_first_runs": 0,
        "full_effect_readiness_qualified": False, "amount_kind": "synthetic-native-fixture",
    }
    try:
        observed = asyncio.run(exercise())
        with (args.output_dir / "observed.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(observed, ensure_ascii=False, indent=2) + "\n")
        report.update(status="GREEN", checks=checks, cases=6,
                      readonly_mcp_queries=6, output_file_count=2)
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
