"""Exercise three retained release packets through real production Service hooks.

Authored without execution. The native callbacks, captive and date are synthetic.
An endpoint supplied to the production Driver replays original whole responses;
only request_id changes. ACKs are pending, with no live or material release credit.
The two original unsendable/refused cases reuse their existing registered GREEN.
A separately labeled synthetic caller checkpoint baseline uses persisted Driver
state. It is not a native checkpoint command, save file or material game result.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import traceback


_CASES = (
    "all_off_pending", "gain_hook_pending", "gain_hook_copied_mask_changed",
)
_POSITIVE = {"all_off_pending", "gain_hook_pending"}
_REUSED_CASES = ("gain_hook_native_false", "gain_hook_native_refused")
_QUERY_STEP = "query-player-prisoner-collection-private-v1"
_NATIVE_SUBMIT_STEP = "submit-player-prisoner-release-private-v1"
_PENDING = "submitted_verification_pending"


def require(condition: object, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def frame_binding(snapshot: dict[str, object]) -> dict[str, object]:
    return {key: snapshot.get(key) for key in (
        "snapshot_id", "revision", "native_revision", "date_raw", "date",
        "phase", "paused", "map_ready", "played_character", "active_wars",
        "player_armies", "active_event", "pending_character_interaction",
    )}


def traceback_plan_context(failure: Exception) -> list[dict[str, object]]:
    """Retain actual plan classifications from failure frames, without providers."""
    result = []
    trace = failure.__traceback__
    while trace is not None and len(result) < 16:
        frame = trace.tb_frame
        local = frame.f_locals
        entry = {"file": frame.f_code.co_filename, "function": frame.f_code.co_name,
                 "line": trace.tb_lineno, "plans": {}}
        for name in ("current", "planned", "plan"):
            value = local.get(name)
            if not isinstance(value, dict):
                continue
            plan = value.get("plan") if isinstance(value.get("plan"), dict) else value
            classification = {}
            for key in ("policy", "phase", "selected_step", "reason", "required_step",
                        "required_observation", "prisoner_release_initial_expectation_root_deferred"):
                observed = plan.get(key)
                if observed is None or isinstance(observed, (bool, int, float, str)):
                    classification[key] = observed[:1200] if isinstance(observed, str) else observed
            entry["plans"][name] = classification
        snapshot = local.get("snapshot")
        if isinstance(snapshot, dict):
            entry["snapshot"] = {
                key: snapshot.get(key) for key in (
                    "snapshot_id", "revision", "native_revision", "date_raw", "phase",
                    "paused", "map_ready", "one_life_terminal_reason",
                )
            }
        if entry["plans"] or "snapshot" in entry:
            result.append(entry)
        trace = trace.tb_next
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--native-wire-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--succession-lifecycle-binding-json", type=Path, required=True,
                        help="Existing frozen ordinary campaign configuration; not a native frame.")
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / "ck3_autonomous_player/src"))
    from xar_autoplayer.bridge.driver import BridgeUnavailableError
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.bridge.service import GameplayBridgeService
    from xar_autoplayer.environment import write_json_atomic
    from xar_autoplayer.bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION, normalize_succession_lifecycle_binding_v1,
    )
    from xar_autoplayer.prisoner_release_formal_consumer import (
        SUBMIT_STEP, read_release_ledger,
    )

    class Endpoint:
        pipe_name = r"\\.\pipe\unused-offline-prisoner-release-service-12004"

        def __init__(self, packet: dict[str, object]) -> None:
            self.packet = packet
            self.requests: list[dict[str, object]] = []
            self.responses: list[dict[str, object]] = []
            self.on_frame = None

        def start(self, on_frame, on_disconnect) -> None:
            self.on_frame = on_frame

        def publish(self, frame: dict[str, object]) -> None:
            self.on_frame(copy.deepcopy(frame))

        def send(self, request: dict[str, object]) -> None:
            if request.get("type") == "ping":
                return
            require(request.get("type") == "execute_step"
                    and request.get("protocol_version") == 1,
                    "the production Driver changed its native command protocol")
            self.requests.append(copy.deepcopy(request))
            native = self.packet["before_collection"]["result"]
            expectations = self.packet["native_expectations"]
            mask = expectations["requested_option_mask_bits"]
            require(request.get("expected_revision") == native["snapshot_revision"],
                    "the production request lost the exact native revision")
            if request.get("step") == _QUERY_STEP:
                require(set(request) == {
                    "type", "protocol_version", "request_id", "step", "expected_revision",
                } | ({"release_option_mask_bits"} if mask else set()),
                    "collection replay requested terms absent from the original native packet")
                require(("release_option_mask_bits" not in request if mask == 0 else
                         request.get("release_option_mask_bits") == mask),
                        "collection query changed the original selected option mask")
                response = copy.deepcopy(self.packet["before_collection"])
            else:
                require(request.get("step") == _NATIVE_SUBMIT_STEP,
                        "Service dispatched an action outside the retained release packets")
                row = native["player_prisoner_collection"]["prisoners"][0]
                require(set(request) == {
                    "type", "protocol_version", "request_id", "step", "expected_revision",
                    "release_query_sequence", "prisoner_character_id", "release_option_mask_bits",
                }, "formal release invented action fields")
                require(request["release_query_sequence"] == native["query_sequence"]
                        and request["prisoner_character_id"] == row["prisoner_character_id"]
                        and request["release_option_mask_bits"] == mask,
                        "formal action changed the queried full ID, sequence or option mask")
                response = copy.deepcopy(self.packet["command_result"])
            response["request_id"] = request["request_id"]
            self.responses.append(copy.deepcopy(response))
            self.publish(response)

        def close(self) -> None:
            pass

        def transport_error(self):
            return None

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "xar.ck3.prisoner-release-service-first/v1",
        "status": "RED", "compound_methods": 1, "service_packet_count": 3,
        "original_native_packet_count": 5, "reused_negative_packet_count": 2,
        "source_root": str(args.source_root), "native_wire_dir": str(args.native_wire_dir),
        "consumer_methods": ["Driver.query_player_prisoner_collection_private_v1",
                             "Service.plan_turn", "Service._execute_planned_turn",
                             "Driver.submit_player_prisoner_release_private_v1"],
        "scope": "offline_native_owned_packets_and_production_service",
        "sdk_calls": 0, "named_pipe_connections": 0, "game_actions": 0,
        "fixture_owned_synthetic_caller_baseline": True,
        "native_checkpoint_commands": 0, "native_checkpoint_materialized": False,
        "live_capture": False, "live_release": False, "production_live_release": False,
        "real_captive_credit": False, "custody_change_credit": False,
        "independent_after_native_frame": False, "material_result": False,
        "mailbox_route_fixture_covered": False,
        "native_wire_mutations": "request_id correlation only", "cases": {},
        "reused_negative_evidence": {},
    }
    lines = ["One offline production Service compound; original native whole packets."]
    exit_code = 1
    try:
        binding_bytes = args.succession_lifecycle_binding_json.read_bytes()
        lifecycle_binding = normalize_succession_lifecycle_binding_v1(json.loads(binding_bytes))
        require(lifecycle_binding["lifecycle"] == ORDINARY_CAMPAIGN_SUCCESSION,
                "this Service compound requires explicit ordinary campaign configuration")
        report["configured_succession_lifecycle"] = {
            "path": str(args.succession_lifecycle_binding_json),
            "sha256": hashlib.sha256(binding_bytes).hexdigest(),
            "binding": lifecycle_binding,
            "scope": "offline_fixture_configuration_not_native_game_rule_observation",
        }
        existing_path = (
            args.native_wire_dir.parent / "registered-toolsvenv-02" / "CONSUMER-FIRST.json"
        )
        existing_bytes = existing_path.read_bytes()
        existing = json.loads(existing_bytes)
        require(existing["status"] == "GREEN" and existing["material_result"] is False,
                "the reused registered five-case evidence is not pending-only GREEN")
        for case in _REUSED_CASES:
            packet_path = args.native_wire_dir / (case + ".json")
            packet_bytes = packet_path.read_bytes()
            packet = json.loads(packet_bytes)
            rows = [row for row in existing["rows"] if row["scenario"] == case]
            require(packet["scenario"] == case
                    and packet["native_expectations"]["queue_calls"] == 0
                    and packet["native_expectations"]["material_result"] is False
                    and len(rows) == 1 and rows[0]["action_request_count"] == 0
                    and rows[0]["material_result"] is False,
                    case + ": reused evidence does not show the original no-action branch")
            report["reused_negative_evidence"][case] = {
                "native_packet": str(packet_path),
                "native_packet_sha256": hashlib.sha256(packet_bytes).hexdigest(),
                "native_expectations": packet["native_expectations"],
                "registered_consumer_first": str(existing_path),
                "registered_consumer_first_sha256": hashlib.sha256(existing_bytes).hexdigest(),
                "registered_case_result": rows[0],
                "replayed_by_this_service_compound": False,
                "material_result": False,
            }
        lines.append("Three original packets replayed by Service; two negative cases reuse the prior registered GREEN.")
        for case in _CASES:
            packet_path = args.native_wire_dir / (case + ".json")
            packet_bytes = packet_path.read_bytes()
            packet = json.loads(packet_bytes)
            require(packet["scenario"] == case, "native packet scenario differs from its filename")
            expectations = packet["native_expectations"]
            require(expectations["fixture_owned_memory"] is True
                    and expectations["synthetic_native_callbacks"] is True
                    and expectations["live_capture"] is False
                    and expectations["live_release"] is False
                    and expectations["material_result"] is False,
                    "retained packet qualification changed")
            endpoint = Endpoint(packet)
            state_dir = args.output_dir / case / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            entry = {
                "native_packet": str(packet_path),
                "native_packet_sha256": hashlib.sha256(packet_bytes).hexdigest(),
                "native_expectations": expectations, "requests": endpoint.requests,
                "responses": endpoint.responses, "outcome": None, "action_error": None,
                "material_result": False, "status": "RED",
            }
            report["cases"][case] = entry
            driver = NativeHeadlessGameplayDriver(
                endpoint.pipe_name, endpoint=endpoint, state_dir=state_dir,
                command_timeout_seconds=0.1,
                allow_private_prisoner_collection_query=True,
                allow_private_prisoner_ransom_action=True,
                succession_lifecycle_binding=lifecycle_binding,
            )
            try:
                baseline_row = {
                    "index": 1, "command": "save-checkpoint", "ok": True,
                    "result": {
                        "step": "save-checkpoint",
                        "fixture_owned_synthetic_caller_baseline": True,
                        "native_command_sent": False, "material_result": False,
                        "checkpoint": {
                            "status": "fixture_owned_synthetic_caller_baseline",
                            "path": None, "size": None, "sha256": None,
                        },
                        "materialization": {
                            "available": False, "reason": "offline_caller_fixture_only",
                        },
                    },
                }
                baseline_payload = {
                    "format_version": 2, "pipe_name": endpoint.pipe_name,
                    "bridge_pid": packet["hello"]["pid"],
                    "episode_character_id": None, "episode_run_id": None,
                    "command_history": [baseline_row], "last_checkpoint": None,
                    "rollback_war_failure": None, "rollback_war_failures": [],
                    "managed_restore_transaction": None, "succession_expectation": None,
                    "succession_lifecycle": lifecycle_binding, "campaign_goal": None,
                }
                baseline_path = driver._native_driver_state_path()
                write_json_atomic(baseline_path, baseline_payload)
                entry["caller_baseline_state"] = {
                    "path": str(baseline_path),
                    "setup_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                    "payload": baseline_payload,
                    "scope": "root_authorized_fixture_owned_synthetic_caller_only",
                    "material_result": False, "native_checkpoint_commands": 0,
                }
                endpoint.publish(packet["hello"])
                endpoint.publish(packet["before_snapshot"])
                before = driver.take_snapshot()
                entry["before_snapshot"] = before
                require(before["succession_lifecycle"]["lifecycle"] == ORDINARY_CAMPAIGN_SUCCESSION
                        and isinstance(before.get("campaign_goal"), dict),
                        case + ": actual Driver did not use the configured ordinary campaign scope")
                require(before["native_command_history"] == [baseline_row],
                        case + ": actual same-PID Driver state did not restore the synthetic caller baseline")
                query_arguments = {"expected_revision": before["revision"], "ransom_ordinal": 0}
                if case != "all_off_pending":
                    query_arguments["release_option_keys"] = ["gain_hook"]
                collection = driver.query_player_prisoner_collection_private_v1(**query_arguments)
                entry["collection"] = collection
                native = packet["before_collection"]["result"]
                require(all(collection.get(key) == value for key, value in native.items()),
                        case + ": production query changed an original native collection field")
                row = collection["player_prisoner_collection"]["prisoners"][0]
                preview = row["unconditional_release_preview"] if case == "all_off_pending" else row["negotiated_release_preview"]
                require(row["prisoner_character_id"] == 0x03000002
                        and row["source_ordinal"] == 0
                        and row["custody_relation_verified"] is True,
                        "original synthetic full ID and player custody binding were not preserved")
                before_plan = driver.take_snapshot()
                entry["before_plan_snapshot"] = before_plan
                require(frame_binding(before_plan) == frame_binding(before),
                        case + ": the read-only collection changed the native frame")
                require(any(history.get("command") == _QUERY_STEP
                            and history.get("ok") is True
                            and history.get("result") == collection
                            for history in before_plan["native_command_history"]),
                        case + ": real Driver query did not create its production history receipt")
                service = GameplayBridgeService(driver)
                planned = service.plan_turn()
                entry["planned"] = planned
                plan = planned["plan"]
                selected = plan.get("selected_step")
                require(selected == SUBMIT_STEP,
                        case + ": Service did not select the observed current accepted release")
                choice = plan["prisoner_release_choice"]
                require(choice["prisoner_character_id"] == row["prisoner_character_id"]
                        and choice["source_ordinal"] == row["source_ordinal"]
                        and choice["release_option_mask_bits"] == expectations["requested_option_mask_bits"]
                        and choice["release_option_keys"] == query_arguments.get("release_option_keys", [])
                        and choice["preview"] == preview
                        and choice["collection"] == collection,
                        case + ": formal planning changed typed native release terms")
                try:
                    entry["outcome"] = service._execute_planned_turn(planned)
                except BridgeUnavailableError as failure:
                    entry["action_error"] = {
                        "type": type(failure).__name__, "message": str(failure),
                        "selected_step": getattr(failure, "selected_step", None),
                        "plan": getattr(failure, "plan", None),
                        "traceback": traceback.format_exc(),
                        "traceback_plan_context": traceback_plan_context(failure),
                        "prisoner_release_arbitration": getattr(
                            failure, "prisoner_release_arbitration", None,
                        ),
                    }
                after = driver.take_snapshot()
                entry["after_snapshot"] = after
                entry["after_frame_kind"] = "same_retained_native_frame_after_service_dispatch"
                entry["ledger"] = read_release_ledger(state_dir)
                actions = [request for request in endpoint.requests
                           if request.get("step") == _NATIVE_SUBMIT_STEP]
                require(frame_binding(after) == frame_binding(before),
                        case + ": pending ACK or rejection was promoted to a new native state")
                require(sum(request.get("step") == _QUERY_STEP for request in endpoint.requests) == 1,
                        case + ": formal consumer re-queried or replaced the original selected offer")
                if case in _POSITIVE:
                    outcome = entry["outcome"]
                    require(entry["action_error"] is None and len(actions) == 1
                            and outcome["status"] == "executed"
                            and outcome["selected_step"] == SUBMIT_STEP,
                            case + ": formal dispatch failed to submit one accepted offer")
                    action = outcome["result"]
                    ack = action["action_ack"]
                    require(action["status"] == _PENDING and action["material_result"] is False
                            and ack["status"] == _PENDING and ack["material_result"] is False
                            and ack["costs"] == preview["costs"]
                            and ack["acceptance"] == preview["acceptance"]
                            and ack["release_option_mask_bits"] == expectations["requested_option_mask_bits"],
                            case + ": Service ACK lost actual terms or claimed a material result")
                    require(isinstance(entry["ledger"].get("pending"), dict)
                            and entry["ledger"]["pending"]["stage"] == "receipt_pending"
                            and entry["ledger"]["pending"]["material_result"] is False
                            and expectations["queue_calls"] == 1
                            and expectations["clone_calls"] == 1
                            and expectations["queued_option_mask_bits"] == ack["release_option_mask_bits"],
                            case + ": pending ledger or native owned queue mask differs")
                    entry["status"] = _PENDING
                else:
                    retained = entry["ledger"].get("pending")
                    require(len(actions) == 1 and entry["outcome"] is None
                            and entry["action_error"] is not None
                            and entry["action_error"]["selected_step"] == SUBMIT_STEP
                            and "private release native RED" in entry["action_error"]["message"]
                            and expectations["queue_calls"] == 0
                            and isinstance(retained, dict)
                            and retained["stage"] == "submission_unresolved"
                            and retained["material_result"] is False
                            and "action_ack" not in retained
                            and retained.get("status") != _PENDING,
                            case + ": actual copied-mask native rejection gained an ACK/material credit")
                    entry["status"] = "native_copied_mask_rejected"
                lines.append(f"{case}: {entry['status']}; native release requests={len(actions)}; material_result=false")
            finally:
                driver.close()
        report["status"] = "GREEN"
        exit_code = 0
    except Exception as failure:
        report["error"] = {"type": type(failure).__name__, "message": str(failure),
                           "traceback": traceback.format_exc(),
                           "traceback_plan_context": traceback_plan_context(failure),
                           "prisoner_release_arbitration": getattr(
                               failure, "prisoner_release_arbitration", None,
                           )}
        lines.append(f"RED: {type(failure).__name__}: {failure}")
        lines.append("Actual plan context: " + json.dumps(report["error"]["traceback_plan_context"]))
        lines.append(report["error"]["traceback"])
    finally:
        lines.append("Synthetic offline packets only; no live captive, custody change or material freedom credit.")
        (args.output_dir / "CONSUMER-FIRST.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8",
        )
        (args.output_dir / "consumer-first.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
