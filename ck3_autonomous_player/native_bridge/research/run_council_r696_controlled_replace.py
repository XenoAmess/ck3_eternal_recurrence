"""Run one bounded private Council replacement under sole CK3 ownership."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

from verify_council_r696_controlled_prep import sha256, verify


class HeldLaunchLocks(ExitStack):
    """Keep both launch locks until tracked CK3 shutdown in outer finally."""

    def __exit__(self, *arguments: object) -> bool:
        return False

    def close(self) -> None:
        ExitStack.__exit__(self, None, None, None)

QUERY = "private-query-council-final-gates-v1"
ASSIGN = "private-assign-councillor-v1"
RECEIPT = "private-query-assign-councillor-receipt-v1"
STATUS = "private-council-application-main-status-v1"
PUBLIC_SCHEMA = "xar.ck3.council-composition-candidates/v1"
ENVELOPE_SCHEMA = "xar.ck3.council-application-main/v1"
GATE_SCHEMA = "xar.ck3.private.council-final-gates/v1"
EXPECTED_OWNER = 29829
EXPECTED_INCUMBENT = 32716
SCENE_CANDIDATE = 33433
ALREADY_POSITIVE_IDS = (33435, 34333, 34867)
EXPECTED_ROW_COUNT = 11
SAVE_SHA = "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"
NEGATIVE_CANDIDATE = 33435


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def command(driver: object, step: str, request_id: str, revision: int,
            wait_seconds: float, *, candidate_character_id: int | None = None) -> dict[str, object]:
    frame = {
        "type": "execute_step", "protocol_version": 1, "request_id": request_id,
        "step": step, "expected_revision": revision,
    }
    if candidate_character_id is not None:
        frame["candidate_character_id"] = candidate_character_id
    driver.endpoint.send(frame)
    result = driver.state.wait_for_command_result(request_id, wait_seconds)
    require(isinstance(result, dict), f"private command timed out: {step}")
    return result


def bounded_operation(driver: object, handle: object, evidence: Path,
                      label: str, step: str, request_id: str, revision: int,
                      overall_deadline: float, date_raw: int,
                      *, candidate_character_id: int | None = None) -> dict[str, object]:
    """Retain the queue result and every status before checking the terminal envelope."""
    start = time.monotonic()
    deadline = min(start + 60, overall_deadline - 20)
    require(deadline > start + 2, f"no bounded {label} window remains")
    request = {
        "step": step, "request_id": request_id,
        "expected_revision": revision,
        "candidate_character_id": candidate_character_id,
    }
    write_json(evidence / f"{label}-request.json", request)
    first = command(driver, step, request_id, revision,
                    min(5, deadline - time.monotonic()),
                    candidate_character_id=candidate_character_id)
    write_json(evidence / f"{label}-queue-result.json", first)
    require(first.get("ok") is True and isinstance(first.get("result"), dict) and
            first["result"].get("status") == "pending",
            f"{label} queue RED: {first!r}")
    attempts: list[dict[str, object]] = []
    terminal = None
    while time.monotonic() < deadline:
        require(handle.process.poll() is None, f"CK3 exited during {label}")
        current = driver.take_internal_semantic_snapshot()
        require(current.get("paused") is True and current.get("date_raw") == date_raw,
                f"paused/date invariant changed during {label}")
        status = command(driver, STATUS, f"{request_id}-status-{len(attempts)+1}",
                         revision, min(2, max(0.1, deadline - time.monotonic())))
        attempts.append(status)
        write_json(evidence / f"{label}-raw-status-results.json", attempts)
        payload = status.get("result")
        require(status.get("ok") is True, f"{label} status RED: {status!r}")
        if isinstance(payload, dict) and payload.get("schema") == ENVELOPE_SCHEMA:
            terminal = status
            break
        time.sleep(0.1)
    require(terminal is not None, f"{label} did not publish within 60 seconds")
    write_json(evidence / f"{label}-raw-terminal-result.json", terminal)
    return terminal


def envelope(result: dict[str, object], expected_step: str) -> dict[str, object]:
    payload = result.get("result")
    require(result.get("ok") is True and isinstance(payload, dict) and
            payload.get("schema") == ENVELOPE_SCHEMA and
            payload.get("step") == expected_step and
            payload.get("accepted") is True,
            f"{expected_step} terminal envelope RED: {result!r}")
    return payload


def public_from_gate(result: dict[str, object]) -> dict[str, object]:
    payload = envelope(result, QUERY)
    gates = payload.get("council_final_gates")
    require(isinstance(gates, dict) and gates.get("status") == "available" and
            isinstance(gates.get("council_composition_candidates"), dict),
            f"native Council gate/public query unavailable: {gates!r}")
    return gates["council_composition_candidates"]


def validate_gate_query(result: dict[str, object], initial: dict[str, object]) -> dict[str, object]:
    require(result.get("type") == "command_result" and result.get("ok") is True,
            f"private status returned RED: {result!r}")
    payload = result.get("result")
    require(isinstance(payload, dict), "private query has no result object")
    require(payload.get("schema") == ENVELOPE_SCHEMA and
            payload.get("step") == QUERY and payload.get("status") == "available" and
            payload.get("accepted") is True and payload.get("private") is True and
            payload.get("advertised") is False,
            f"gate envelope unavailable or not private: {payload!r}")
    helper_delta = payload.get("native_helper_invocations_delta")
    require(type(helper_delta) is int and helper_delta == 0 and
            "council_assign_councillor_ack" not in payload,
            "gate-only query invoked native helper or emitted action ACK")
    gates = payload.get("council_final_gates")
    require(isinstance(gates, dict) and gates.get("schema") == GATE_SCHEMA and
            gates.get("status") == "available" and
            gates.get("unavailable_reason") == "none",
            f"typed final gates unavailable: {gates!r}")
    public = gates.get("council_composition_candidates")
    require(isinstance(public, dict) and public.get("schema") == PUBLIC_SCHEMA and
            public.get("status") == "available", "public council query unavailable")
    exact = public.get("exact_build")
    require(isinstance(exact, dict) and exact.get("game_version") == "1.19.0.6" and
            exact.get("executable_sha256") ==
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "private result exact-build identity differs")
    binding = public.get("snapshot")
    require(isinstance(binding, dict) and binding.get("paused") is True and
            binding.get("date_raw") == initial["date_raw"] and
            binding.get("snapshot_id") == f"native:{binding.get('native_revision')}" and
            binding.get("native_revision") == binding.get("public_revision") and
            isinstance(binding.get("native_revision"), int) and
            not isinstance(binding.get("native_revision"), bool),
            f"same-frame binding differs: {binding!r}")
    require(payload.get("snapshot_revision") == binding.get("public_revision") and
            type(payload.get("query_sequence")) is int and payload["query_sequence"] > 0,
            "gate envelope is not bound to the public query frame")
    require(public.get("owner_character_id") == EXPECTED_OWNER,
            "Council owner differs from frozen scene")
    position = public.get("position")
    require(isinstance(position, dict) and position.get("position_key") ==
            "councillor_steward" and position.get("incumbent_character_id") ==
            EXPECTED_INCUMBENT and position.get("vacant") is False and
            position.get("action_route") == "replace", f"incumbent differs: {position!r}")
    readiness = public.get("readiness")
    require(isinstance(readiness, dict) and readiness.get("ready") is True and
            all(value is True for value in readiness.values()),
            f"public query readiness differs: {readiness!r}")
    candidates = public.get("candidates")
    require(public.get("candidate_collection_complete") is True and
            isinstance(candidates, list) and len(candidates) == EXPECTED_ROW_COUNT,
            "candidate collection is incomplete or differs from frozen scene")
    rows = gates.get("rows")
    require(type(gates.get("candidate_count")) is int and
            gates["candidate_count"] == EXPECTED_ROW_COUNT and
            isinstance(rows, list) and len(rows) == EXPECTED_ROW_COUNT,
            "gate query has partial or unexpected row count")
    ids = []
    typed_gate_fields = (
        "final_gate_available", "candidate_already_councillor",
        "candidate_is_guest", "pending_character_interaction",
        "incumbent_fireability_evaluated", "incumbent_can_be_fired",
    )
    for index, (candidate, row) in enumerate(zip(candidates, rows)):
        require(isinstance(candidate, dict) and isinstance(row, dict),
                f"gate/public row {index} is not typed")
        candidate_id = candidate.get("character_id")
        require(type(candidate_id) is int and candidate_id > 0 and
                row.get("character_id") == candidate_id and
                type(row.get("native_collection_ordinal")) is int and
                row["native_collection_ordinal"] == candidate.get("native_collection_ordinal"),
                f"gate/public row {index} identity or ordinal differs")
        for field in typed_gate_fields:
            require(type(row.get(field)) is bool,
                    f"gate row {index} {field} is unknown/null, not a boolean")
        require(row["final_gate_available"] is True and
                row["incumbent_fireability_evaluated"] is True,
                f"gate row {index} not fully available/evaluated")
        ids.append(candidate_id)
    require(len(ids) == len(set(ids)), "gate/public candidate IDs are duplicated")
    gate_by_id = {row["character_id"]: row for row in rows}
    require(all(character_id in gate_by_id and
                gate_by_id[character_id]["candidate_already_councillor"] is True
                for character_id in ALREADY_POSITIVE_IDS),
            "frozen already-councillor positive controls are absent or false")
    scene = next((candidate for candidate in candidates
                  if candidate.get("character_id") == SCENE_CANDIDATE), None)
    require(isinstance(scene, dict) and SCENE_CANDIDATE in gate_by_id,
            "Ivo full-ID 33433 is missing from same-frame gate/query rows")
    incumbent_skill = position.get("incumbent_main_skill")
    skill = scene.get("main_skill")
    require(isinstance(skill, dict) and skill.get("key") == "stewardship" and
            type(skill.get("value")) is int and skill["value"] == 16 and
            isinstance(incumbent_skill, dict) and
            incumbent_skill.get("key") == "stewardship" and
            type(incumbent_skill.get("value")) is int and
            incumbent_skill["value"] == 12 and scene.get("eligible") is True,
            "Ivo/temporary incumbent positive-delta scene differs")
    return {
        "owner": EXPECTED_OWNER,
        "incumbent": position,
        "candidate_count": len(candidates),
        "scene_candidate_33433": {
            "public_candidate": scene,
            "native_final_gates": gate_by_id[SCENE_CANDIDATE],
            "stewardship_delta": 4,
        },
        "already_councillor_positive_ids": list(ALREADY_POSITIVE_IDS),
        "guest_positive_ids": [row["character_id"] for row in rows
                               if row["candidate_is_guest"]],
        "pending_interaction_positive_ids": [row["character_id"] for row in rows
                                             if row["pending_character_interaction"]],
        "incumbent_fireable_ids": [row["character_id"] for row in rows
                                   if row["incumbent_can_be_fired"]],
        "all_gate_rows": rows,
        "snapshot": binding,
        "native_helper_invocations_delta": 0,
        "action_effect_live_verified": False,
        "gameplay_actions": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--new-round", help="persistent round allocated by sole CK3 owner")
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    preflight = verify(root)
    if args.preflight_only:
        print(json.dumps(preflight, sort_keys=True))
        return 0
    require(isinstance(args.new_round, str) and args.new_round.startswith("R") and
            args.new_round[1:].isdigit() and int(args.new_round[1:]) > 695,
            "sole CK3 owner must allocate a new monotonic round above R695")
    round_id = args.new_round
    operator = json.loads((root / "operator-runtime.json").read_text(encoding="utf-8"))
    source = root / "source-repo"
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"), str(source / "tools")]
    from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
        build_assign_councillor_request_v1,
        normalize_assign_councillor_ack_v1,
        normalize_assign_councillor_receipt_v1,
    )
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
    from xar_autoplayer.native_auto_run import _wait_for_readiness
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked

    evidence = root / f"live-{round_id.lower()}"
    require(not evidence.exists(), f"{round_id} already has a live attempt; do not reuse round")
    evidence.mkdir(parents=True)
    report: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_council_r696_controlled_live_v1",
        "status": "preflight", "started_at": now(), "round": round_id,
        "last_completed_round": "R695",
        "policy": {
            "private_route": True, "public_council_advertised": False,
            "positive_helper_budget": 1, "negative_helper_budget": 0,
            "ui_inputs": 0, "date_advance": False, "manual_save_mutation": False,
            "readiness_timeout_seconds": 300,
            "operation_timeout_seconds": 60, "overall_window_seconds": 480,
        },
        "formal_next_turn_council_consumption": "unsupported_private_candidate",
        "formal_high_level_goal_cold_restore": "unverified",
        "positive_submission_attempted": False,
        "pending_ack": None, "red": None, "preflight": preflight,
    }
    handle = None
    driver = None
    locks = HeldLaunchLocks()
    started = time.monotonic()
    deadline = started + 480
    state_dir = root / "fresh-profile-state"
    source_save = root / "source-save" / "dev3b_r639.ck3"
    target_save = state_dir / "profile" / "save games" / "dev3b_r639.ck3"
    checkpoint_save = state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
    try:
        spec = make_spec(state_dir, Path(str(operator["game_dir"])))
        inventory = ck3_process_inventory()
        require(not inventory.get("processes"), "CK3 inventory nonzero before owner launch")
        write_json(evidence / "preflight.json", {**preflight, "ck3_inventory": inventory,
                                                 "owner_allocated_round": round_id})
        with locks:
            locks.enter_context(exclusive_launch_lock(spec.game_exe))
            locks.enter_context(exclusive_state_lock(state_dir,
                                                     f"council-{round_id.lower()}-controlled"))
            driver = NativeHeadlessGameplayDriver(
                str(operator["pipe"]), state_dir=state_dir,
                save_dir=state_dir / "profile" / "save games",
            )
            handle = launch(
                spec, native_bridge=NativeBridgeLaunchConfig(
                    mode="native-headless", pipe_name=str(operator["pipe"]),
                    dll_path=root / "candidate-bin" / "xar_ck3_bridge.dll",
                    injector_path=root / "candidate-bin" / "xar_ck3_bridge_injector.exe",
                ), continue_last_save=False, load_save_name="dev3b_r639",
                verify_prepared_profile=False,
            )
            report["process"] = {
                "pid": handle.process.pid, "creation_date": handle.ck3_creation_date,
                "watchdog_pid": handle.watchdog_pid,
                "watchdog_creation_date": handle.watchdog_creation_date,
                "command": handle.command, "launched_at": now(),
                "owner_allocated_round": round_id,
            }
            write_json(evidence / "round-ownership.json", report["process"])
            remaining = deadline - time.monotonic()
            require(remaining > 30, "overall window consumed before CK3 readiness")
            binding = _wait_for_readiness(
                driver, session_done=threading.Event(), session_state={},
                timeout_seconds=min(300, remaining - 20), stable_seconds=1.0,
                poll_interval_seconds=0.1, cold_start_checkpoint=False,
                allow_terminal=False,
            )
            initial = driver.take_internal_semantic_snapshot()
            require(initial.get("paused") is True and
                    initial.get("episode_character_id") == EXPECTED_OWNER and
                    type(initial.get("date_raw")) is int and
                    type(initial.get("native_revision")) is int,
                    f"frozen paused scene differs: {initial!r}")
            advertised = driver.capabilities().get("capabilities")
            require(not isinstance(advertised, list) or all(value not in {
                "game.query.council-composition-candidates-v1",
                "game.action.assign-councillor-v1",
            } for value in advertised), "private Council leaked into public hello")
            date_raw = initial["date_raw"]
            revision = initial["native_revision"]
            first_gate = bounded_operation(
                driver, handle, evidence, "first-gate", QUERY,
                f"{round_id.lower()}-first-gate", revision, deadline, date_raw)
            first_semantic = validate_gate_query(first_gate, initial)
            first_public = public_from_gate(first_gate)
            negative_request_id = f"{round_id.lower()}-reject-33435"
            negative_request = build_assign_councillor_request_v1(
                first_public, candidate_character_id=NEGATIVE_CANDIDATE,
                request_id=negative_request_id)
            negative = bounded_operation(
                driver, handle, evidence, "negative-33435", ASSIGN,
                negative_request_id, revision, deadline, date_raw,
                candidate_character_id=NEGATIVE_CANDIDATE)
            negative_payload = envelope(negative, "assign-councillor-v1")
            write_json(evidence / "negative-33435-raw-ack.json",
                       negative_payload.get("council_assign_councillor_ack"))
            negative_ack = normalize_assign_councillor_ack_v1(
                negative_payload.get("council_assign_councillor_ack"),
                expected_request=negative_request)
            require(negative_ack["status"] == "rejected_before_submit" and
                    negative_ack["failure"] == "candidate_already_councillor" and
                    negative_ack["native_helper_invoked"] is False and
                    negative_ack["verification_pending"] is False,
                    f"33435 did not reject before native helper: {negative_ack!r}")
            report["negative_33435"] = negative_ack
            write_json(evidence / "report-progress.json", report)

            # Submit preparation clears query_result; never reuse the old frame.
            refreshed = driver.take_internal_semantic_snapshot()
            require(refreshed.get("paused") is True and
                    refreshed.get("date_raw") == date_raw and
                    type(refreshed.get("native_revision")) is int,
                    "native paused state changed after negative rejection")
            revision = refreshed["native_revision"]
            fresh_gate = bounded_operation(
                driver, handle, evidence, "fresh-gate", QUERY,
                f"{round_id.lower()}-fresh-gate", revision, deadline, date_raw)
            fresh_semantic = validate_gate_query(fresh_gate, initial)
            fresh_public = public_from_gate(fresh_gate)
            legal_row = fresh_semantic["scene_candidate_33433"]["native_final_gates"]
            require(legal_row["final_gate_available"] is True and
                    legal_row["candidate_already_councillor"] is False and
                    legal_row["candidate_is_guest"] is False and
                    legal_row["pending_character_interaction"] is False and
                    legal_row["incumbent_fireability_evaluated"] is True and
                    legal_row["incumbent_can_be_fired"] is True,
                    f"Ivo 33433 is not legal in fresh exact native gates: {legal_row!r}")
            positive_request_id = f"{round_id.lower()}-replace-33433"
            positive_request = build_assign_councillor_request_v1(
                fresh_public, candidate_character_id=SCENE_CANDIDATE,
                request_id=positive_request_id)
            write_json(evidence / "positive-33433-typed-request.json",
                       positive_request.as_wire_fields())
            report["positive_submission_attempted"] = True
            write_json(evidence / "report-progress.json", report)
            positive = bounded_operation(
                driver, handle, evidence, "positive-33433", ASSIGN,
                positive_request_id, revision, deadline, date_raw,
                candidate_character_id=SCENE_CANDIDATE)
            positive_payload = envelope(positive, "assign-councillor-v1")
            raw_ack = positive_payload.get("council_assign_councillor_ack")
            write_json(evidence / "positive-33433-raw-ack.json", raw_ack)
            report["pending_ack"] = raw_ack
            write_json(evidence / "report-progress.json", report)
            ack = normalize_assign_councillor_ack_v1(
                raw_ack, expected_request=positive_request)
            require(ack["status"] == "native_helper_invoked_verification_pending" and
                    ack["native_helper_invoked"] is True and
                    ack["verification_pending"] is True and
                    ack["queue_acceptance_observed"] is False,
                    f"positive action did not yield helper-only pending ACK: {ack!r}")
            report["pending_ack"] = ack

            # Observe native material result in a later read-only paused query.
            # Do not submit a second assignment if the effect remains unknown.
            material_deadline = min(time.monotonic() + 60, deadline - 20)
            material_public = None
            material_attempts = 0
            while time.monotonic() < material_deadline - 2:
                material_attempts += 1
                current = driver.take_internal_semantic_snapshot()
                require(current.get("paused") is True and
                        current.get("date_raw") == date_raw and
                        type(current.get("native_revision")) is int,
                        "paused/date state changed while awaiting incumbent result")
                material_result = bounded_operation(
                    driver, handle, evidence, f"material-query-{material_attempts}",
                    QUERY, f"{round_id.lower()}-material-{material_attempts}",
                    current["native_revision"], material_deadline + 20,
                    date_raw)
                observed = public_from_gate(material_result)
                position = observed.get("position")
                require(isinstance(position, dict) and
                        observed.get("owner_character_id") == EXPECTED_OWNER and
                        position.get("position_key") == "councillor_steward",
                        "post-action Council position unavailable")
                if position.get("incumbent_character_id") == SCENE_CANDIDATE:
                    material_public = observed
                    break
                require(position.get("incumbent_character_id") == EXPECTED_INCUMBENT,
                        f"unexpected post-action incumbent: {position!r}")
                time.sleep(0.2)
            require(material_public is not None,
                    "helper-only ACK unresolved: incumbent 33433 absent in later native paused query; no retry")
            write_json(evidence / "material-public-council-result.json", material_public)
            report["material_incumbent_observed"] = SCENE_CANDIDATE
            write_json(evidence / "report-progress.json", report)

            require(time.monotonic() < deadline - 30,
                    "no bounded checkpoint/receipt window remains")
            checkpoint_start = time.monotonic()
            checkpoint = driver.execute_step("save-checkpoint", expected_revision=None)
            write_json(evidence / "typed-checkpoint-result.json", checkpoint)
            materialization = checkpoint.get("checkpoint")
            require(time.monotonic() - checkpoint_start <= 60 and
                    isinstance(materialization, dict) and
                    materialization.get("status") == "saved" and
                    materialization.get("name") == "xar_checkpoint.ck3" and
                    isinstance(materialization.get("sha256"), str) and
                    checkpoint_save.is_file() and
                    sha256(checkpoint_save) == materialization["sha256"],
                    f"typed checkpoint did not materialize within bound: {checkpoint!r}")
            report["checkpoint"] = materialization
            revision_deadline = min(time.monotonic() + 60, deadline - 20)
            post = driver.take_internal_semantic_snapshot()
            while (type(post.get("native_revision")) is not int or
                   post["native_revision"] <= ack["pre_native_revision"]) and time.monotonic() < revision_deadline:
                time.sleep(0.1)
                post = driver.take_internal_semantic_snapshot()
            require(post.get("paused") is True and post.get("date_raw") == date_raw and
                    type(post.get("native_revision")) is int and
                    post["native_revision"] > ack["pre_native_revision"],
                    "checkpoint failed to create independent paused native revision")
            receipt_terminal = bounded_operation(
                driver, handle, evidence, "later-receipt", RECEIPT,
                f"{round_id.lower()}-receipt-33433", post["native_revision"],
                deadline, date_raw)
            receipt_payload = envelope(receipt_terminal,
                                       "query-assign-councillor-receipt-v1")
            raw_receipt = receipt_payload.get("council_assign_councillor_receipt")
            write_json(evidence / "later-raw-receipt.json", raw_receipt)
            receipt = normalize_assign_councillor_receipt_v1(raw_receipt,
                                                               expected_ack=ack)
            require(receipt["status"] == "applied" and
                    receipt["postcondition_verified"] is True and
                    receipt["incumbent_character_id"] == SCENE_CANDIDATE,
                    f"later independent receipt did not verify incumbent 33433: {receipt!r}")
            report["receipt"] = receipt
            report["capture"] = {
                "binding": binding, "initial_snapshot": initial,
                "first_gate": first_semantic, "fresh_gate": fresh_semantic,
                "material_attempts": material_attempts,
                "post_checkpoint_snapshot": post,
                "positive_helper_count": 1, "negative_helper_count": 0,
            }
            report["status"] = "green_pending_cleanup"
    except BaseException as error:
        report["status"] = "red_pending_cleanup"
        report["red"] = {
            "at": now(), "reason": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
            "positive_submission_attempted": report["positive_submission_attempted"],
            "pending_ack_unresolved": report.get("pending_ack") is not None and
                                      report.get("receipt") is None,
            "positive_action_retry_allowed": False,
        }
    finally:
        if handle is not None:
            try:
                report["cleanup"] = stop_tracked(handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {"ok": False,
                                     "reason": f"{type(error).__name__}: {error}"}
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_red"] = f"{type(error).__name__}: {error}"
        try:
            locks.close()
        except BaseException as error:
            report["lock_cleanup_red"] = f"{type(error).__name__}: {error}"
        try:
            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_save_sha256": sha256(source_save),
                "target_save_sha256": sha256(target_save),
                "checkpoint_sha256": sha256(checkpoint_save) if checkpoint_save.is_file() else None,
                "wall_seconds": time.monotonic() - started,
            }
        except BaseException as error:
            report["postflight_red"] = f"{type(error).__name__}: {error}"
        cleanup = report.get("cleanup")
        postflight = report.get("postflight")
        ok = (report["status"] == "green_pending_cleanup" and
              isinstance(cleanup, dict) and cleanup.get("ok") is True and
              isinstance(postflight, dict) and
              not postflight["ck3_inventory"].get("processes") and
              postflight["source_save_sha256"] == SAVE_SHA and
              postflight["target_save_sha256"] == SAVE_SHA and
              isinstance(report.get("checkpoint"), dict) and
              postflight["checkpoint_sha256"] == report["checkpoint"]["sha256"] and
              postflight["wall_seconds"] <= 480 and
              not report.get("driver_close_red") and
              not report.get("lock_cleanup_red"))
        report["ok"] = ok
        report["status"] = "green" if ok else "red"
        report["finished_at"] = now()
        write_json(evidence / "report.json", report)
    print(json.dumps({"status": report["status"], "ok": report["ok"],
                      "red": report["red"]}, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
