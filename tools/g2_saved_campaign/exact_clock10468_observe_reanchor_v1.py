"""Finite F97 recovery: one fixed readonly status and one semantic read.

This is a local Queue control, not an MCP tool or a successful AUTO classifier.
The exact failed transaction stays unknown; a current paused frame is a new
planning anchor. Only the sole runtime owner may install/call this source.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import time

MACHINE = "xenoamess-full-tower-eb9d2c1186"
BASE = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
T = BASE / "robert30-v20261019-campaign01/runtime"
F97 = BASE / "p51-fresh1066-v20261019-prepare01/c20-exact-clock10468-failure97"
FROZEN_SHA = "1149fcb9f3f5a86cba384c10fcd733179ec87bea8e631167f48258152a087281"
TIMING_SHA = "2d17044ba8c6f17288d5c66e1bb9de7e475c130e94958979829ae18db91a76c6"
QUEUE_SHA = "ed5f8b77b5fbb69b27be204d36f28e1a2e45acd572ff7fae2658444f07f9a09d"
FREEZE_SHA = "6def1ffc381f0d532c57e54a2bc51b9bdfebef7b88a015375c0ad95eb26c9c9e"
DISPATCHER_SHA = "d507d3295a035a631f28ed1961be6f80b8a0609dc20ef230cf1f313acb3eb2e0"
KIND = "c20_exact_clock10468_observe_reanchor"
SCHEMA = "xar.C20-exact-clock10468-observe-reanchor/v1"
ERROR = "Error executing tool ck3_auto_turn: exact-day native clock did not stop the map"
GAME, BIRTH, CONNECTION = 30852, 134368995759027619, 4
OLD_DATE, DATE, CYCLES = 53274576, 53274600, 4752
EPISODE = "native-40526-1bec95182886"
SELECTED = "advance-route-contact-horizon-v1-234881394-to-2627-h-2-117440697-285212941"
STATUS_STEP = "research-query-tactical-daily-sentinel-v1"
ROW_TOTAL_LIMIT = 192 * 1024


def require(ok, why):
    if not ok:
        raise ValueError("F97 only-observe recovery denied: " + why)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _raw(path, limit=262144):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "bounded source exceeded: " + str(path))
    return raw


def _exists(path):
    return Path(path).exists()


def _pinned(ref, limit=262144):
    raw = _raw(ref["path"], limit)
    require(type(ref["bytes"]) is int and len(raw) == ref["bytes"]
            and _sha(raw) == ref["sha256"], "closed input changed: " + ref["path"])
    return raw, json.loads(raw)


def transform_dispatcher_v1(raw):
    """One exact, reversible prelude; original dispatcher bytes stay intact."""
    require(type(raw) is bytes and _sha(raw) == DISPATCHER_SHA, "dispatcher baseline differs")
    marker = b"async def recover(queue, session, request, path, env, *, birth_reader=process_birth_filetime):\n"
    extra = (b"    if request.get('arguments') == {'recovery_kind': 'c20_exact_clock10468_observe_reanchor'}:\n"
             b"        from root_p37c20_exact_clock10468_reconcile import recover as recover10468\n"
             b"        return await recover10468(queue, session, request, path, env, birth_reader=birth_reader)\n")
    require(raw.count(marker) == 1, "dispatcher shape differs")
    output = raw.replace(marker, marker + extra)
    require(output.replace(marker + extra, marker) == raw, "dispatcher inverse differs")
    return output


def _inputs(queue, env):
    manifest_raw = _raw(F97 / "FROZEN.json", 16384)
    require(len(manifest_raw) == 8600 and _sha(manifest_raw) == FROZEN_SHA,
            "exact F97 manifest required")
    manifest = json.loads(manifest_raw)
    require(manifest["machine_id"] == MACHINE and manifest["business_commit"]
            == "f19864de1cc073eed62617faad2307c57ad45a97", "F97 machine/source differs")
    values, raw_values = {}, {}
    for name, pair in manifest["sources"].items():
        raw_values[name], values[name] = _pinned(pair["frozen"])
        require(pair["original"]["sha256"] == pair["frozen"]["sha256"], "freeze provenance differs")
    _, clock = _pinned(manifest["readonly_current_clock"])
    _, partial = _pinned(manifest["partial"])
    timing_raw = _raw(F97 / "EXISTING-CLOCK-TIMING-10468.json", 8192)
    require(len(timing_raw) == 5944 and _sha(timing_raw) == TIMING_SHA, "original timing excerpt differs")
    timing = json.loads(timing_raw)
    require(timing["machine_id"] == MACHINE and timing["selected_AUTO"] == 10468,
            "timing source identity differs")
    require(_sha(_raw(T / "root_p37c20_sdk_queue.py", 1024**2)) == QUEUE_SHA
            and _sha(_raw(T / "ROOT-FINAL-SDK-FREEZE-P37C20.json", 1024**2)) == FREEZE_SHA,
            "actual Queue/source freeze differs")
    state, gov, auto = values["state"], values["gov"], values["AUTO"]
    require(Path(env["Q"]).resolve() == (T / "p37-queue").resolve()
            and Path(env["INBOX"]).resolve() == (T / "p37-requests").resolve()
            and Path(env["OUTBOX"]).resolve() == (T / "p37-responses").resolve(), "runtime roots differ")
    require(queue.full_loop_state == state and _raw(env["Q"] / "ROOT-CUMULATIVE-LOOP-STATE.json") == raw_values["state"]
            and _raw(env["Q"] / "ROOT-GOVERNANCE-RESULT-STATE.json") == raw_values["gov"],
            "current state/governance CAS differs")
    require(isinstance(queue.halted, dict) and queue.halted["request"] == auto["request"] and queue.halted["row"] == auto
            and Path(queue.halted["response"]).resolve() == (env["OUTBOX"] / "10468-1-result.json").resolve()
            and _raw(queue.halted["response"]) == raw_values["AUTO"], "original received error differs")
    require(auto["request"]["sequence"] == 10468 and auto["request"]["tool"] == "ck3_auto_turn"
            and auto["request"]["arguments"] == {} and auto.get("client_error") is None
            and auto["result"]["is_error"] is True and auto["result"]["result_type"] == "complete"
            and auto["result"]["structured_content"] is None
            and [row.get("text") for row in auto["result"]["content"]] == [ERROR], "received failure is not F97")
    plan = values["plan"]["result"]["structured_content"]
    require(plan["selected_step"] == SELECTED and plan["snapshot_id"] == "native:4363"
            and plan["revision"] == 2 and values["plan"]["request"]["parent_sequence"] == 10468,
            "original pre-submit plan differs")
    pending = state["pending_cycle"]
    require(state["completed_cycles"] == CYCLES and state["before"]["date_raw"] == OLD_DATE
            and state["before"]["native_revision"] == 4363 and state["before"]["revision"] == 2
            and pending["global_turn"] == 4753 and pending["auto_sequence"] == 10468
            and pending["stage"] == "auto_unsettled" and gov["pending_cycle"] == pending
            and gov["completed_cycles"] == CYCLES and gov["new_business_credit"] == 0
            and all(state.get(k) is None for k in ("pending_checkpoint", "terminal", "pending_natural_succession", "pending_unsafe_route_halt")),
            "exact failed pending frontier required")
    require(partial["actual_settled"] == 4 and partial["first_turn"] == 4749
            and partial["last_turn"] == CYCLES and partial["new_day_credit"] == 0, "four settled cycles differ")
    require(clock["machine_id"] == MACHINE and clock["clock"]["date_raw"] == DATE
            and clock["clock"]["paused"] is True and clock["clock"]["played_character_id"] == 40526
            and clock["kernel_before"] == clock["kernel_after"]
            and clock["kernel_before"]["pid"] == GAME
            and int(clock["kernel_before"]["creation_filetime"]) == BIRTH
            and clock["kernel_before"]["wait0"] == 258, "closed late read-only clock evidence differs")
    require(queue.next_sequence == values["NEXT"]["next_sequence"] == 10469
            and queue.launch["pid"] == GAME and queue.job["game_creation_filetime"] == BIRTH,
            "same live generation/unused control required")
    require(getattr(queue, "governance_result_state", None) == gov["state"]
            and getattr(queue, "lifestyle_pending_focus", None) == gov["pending_focus"]
            and getattr(queue, "result_classifier_pin", None) == gov["classifier"], "business sidecar cache differs")
    method = queue.recover_partial_life_advance
    namespace = getattr(method, "__func__", method).__globals__
    require(Path(namespace["__file__"]).resolve() == (T / "root_p37c20_sdk_queue.py").resolve()
            and callable(namespace.get("frame")), "actual inherited recovery/frame source required")
    return state, gov, manifest, namespace["frame"]


def _checked_frame(body, queue, state, frame):
    result = frame(body, semantic=True, expected_lifecycle=queue.expected_lifecycle_binding)
    diag = body.get("diagnostics") or {}
    hello = diag.get("hello") or {}
    require(body.get("one_life_terminal") is False and body.get("one_life_terminal_reason") is None
            and result["actor_character_id"] == 40526 and result["episode_run_id"] == EPISODE
            and result["date_raw"] == DATE and type(result["native_revision"]) is int
            and result["native_revision"] > 4363 and result["revision"] > 2
            and result["snapshot_id"] == f"native:{result['native_revision']}"
            and diag.get("bridge_pid") == hello.get("pid") == GAME
            and diag.get("connection_generation") == hello.get("connection_generation") == CONNECTION
            and diag.get("pipe_name") == queue.launch["pipe"]
            and hello.get("ck3_build_match") is True and hello.get("game_adapter_status") == "ready"
            and hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64"
            and body.get("campaign_goal") == state["campaign_goal_anchor"],
            "fresh paused same-owner/date/Native/goal proof differs")
    # New modal/event/interaction/army/war fields are deliberately retained in
    # the complete semantic body; ordinary planning must arbitrate them afresh.
    return result


async def recover(queue, session, request, path, env, *, birth_reader):
    require(request.get("command") == "recover_partial_life_advance" and "tool" not in request
            and request.get("arguments") == {"recovery_kind": KIND}
            and request.get("sequence") == 10469 and path.name == "10469-1-result.json",
            "one exact unused local control required")
    old_state, old_gov, manifest, frame = _inputs(queue, env)
    original_halt, original_attempt = queue.halted, queue.current_attempt
    audit_path = env["Q"] / "EXACT-CLOCK10468-OBSERVE-10469.json"
    started_path = audit_path.with_name(audit_path.stem + "-STARTED.json")
    require(not _exists(audit_path) and not _exists(started_path)
            and not _exists(env["OUTBOX"] / path.name)
            and not _exists(env["INBOX"] / "10470-1-result.json")
            and not _exists(env["OUTBOX"] / "10470-1-result.json")
            and not _exists(env["INBOX"] / "10471-1-result.json")
            and not _exists(env["OUTBOX"] / "10471-1-result.json"), "recovery is create-only; never repeat its reads")

    def guard():
        require(birth_reader(GAME) == BIRTH, "kernel Game birth changed")
        queue.guard()

    guard()
    sequence = queue.consume_sequence(request)
    queue.held_control = path.name
    started = {"schema": SCHEMA, "machine_id": MACHINE, "utc": env["now"]().isoformat(),
               "request": request, "original_AUTO": 10468, "replay_allowed": False}
    env["atomic"](started_path, started, limit=4096)
    env["atomic"](env["Q"] / f"INFLIGHT-{sequence:04d}.json", {"request": request, "control_only": True, "replay_allowed": False}, limit=16384)
    semantic_path = env["OUTBOX"] / "10471-1-result.json"
    body = fresh = None
    audit = {**started, "source_manifest_sha256": FROZEN_SHA,
             "original_pending_cycle": copy.deepcopy(old_state["pending_cycle"]),
             "settled_cycles_before_after": CYCLES, "retained_preceding_settled_cycles": 4,
             "failed_cycle_credit": 0, "failed_day_credit": 0, "business_credit": 0,
             "original_AUTO_replayed": False, "new_pause_arm_resume_cancel": 0,
             "status_query_limit": 1, "semantic_read_limit": 1,
             "sentinel_stop_validation": "not_reached", "original_generation": "unknown",
             "cleanup_cancel_result": "unknown", "physical_no_action_claimed": False,
             "original_timing_excerpt": {"path": str(F97 / "EXISTING-CLOCK-TIMING-10468.json"), "sha256": TIMING_SHA},
             "late_readonly_clock": manifest["readonly_current_clock"],
             "fresh_semantic_response": str(semantic_path)}
    row_bytes = 0

    async def observe_once(tool, arguments, expected_sequence):
        nonlocal row_bytes
        guard()
        require(queue.next_sequence == expected_sequence, "unique readonly sequence changed")
        child_path = env["OUTBOX"] / f"{expected_sequence:04d}-1-result.json"
        child = {"sequence": expected_sequence, "tool": tool, "arguments": arguments,
                 "source": "F97 only-observe recovery; unique readonly request; original AUTO never replayed"}
        env["atomic"](env["INBOX"] / child_path.name, child, limit=16384)
        queue.consume_sequence(child)
        env["atomic"](env["Q"] / f"INFLIGHT-{expected_sequence:04d}.json", {"request": child, "replay_allowed": False}, limit=16384)
        at, mono = env["now"]().isoformat(), time.monotonic()
        try:
            result = await session.call_tool(tool, arguments, read_timeout_seconds=queue.call_budget(tool))
            row = {"started_at_utc": at, "ended_at_utc": env["now"]().isoformat(),
                   "elapsed_seconds": time.monotonic() - mono, "request": child,
                   "result": result.model_dump(mode="json")}
        except Exception as error:
            row = {"started_at_utc": at, "ended_at_utc": env["now"]().isoformat(),
                   "elapsed_seconds": time.monotonic() - mono, "request": child,
                   "client_error": repr(error), "replay_allowed": False}
        size = len(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        require(row_bytes + size <= ROW_TOTAL_LIMIT, "combined readonly reply budget exceeded; no repeat")
        env["atomic"](child_path, row, limit=min(env["REPLY_RESERVE"], ROW_TOTAL_LIMIT - row_bytes))
        row_bytes += size
        guard()
        return row, child_path

    try:
        status_row, status_path = await observe_once("ck3_execute_step", {"step": STATUS_STEP}, 10470)
        audit["current_status_response"] = {"path": str(status_path), "sha256": env["sha256"](status_path)}
        try:
            status_body = env["decoded"](status_row)
            slot = status_body.get("tactical_daily_sentinel")
            observed = (status_body.get("step") == STATUS_STEP and status_body.get("accepted") is True
                        and isinstance(slot, dict))
            audit["current_slot_observed"] = observed
            audit["current_slot_readback"] = copy.deepcopy(slot) if observed else None
        except Exception as error:
            audit["current_slot_observed"] = False
            audit["current_slot_readback"] = None
            audit["current_status_unavailable"] = str(error)
        # This is the current slot, never the missing original Arm transaction.
        row, _ = await observe_once(env["SEMANTIC"], {}, 10471)
        require(row.get("client_error") is None and row["result"]["is_error"] is False
                and row["result"]["result_type"] == "complete", "unique semantic did not complete successfully")
        body = env["decoded"](row)
        fresh = _checked_frame(body, queue, old_state, frame)
        require(_raw(env["Q"] / "ROOT-CUMULATIVE-LOOP-STATE.json") == _raw(F97 / "state.json")
                and _raw(env["Q"] / "ROOT-GOVERNANCE-RESULT-STATE.json") == _raw(F97 / "gov.json")
                and queue.full_loop_state == old_state, "pre-persist old-state CAS changed")
        work = copy.deepcopy(old_state)
        work.update(before=fresh, before_metrics_response=str(semantic_path), pending_cycle=None,
                    before_source_kind="actual_F97_readonly_semantic_reanchor",
                    checkpoint_dirty_since_save=True,
                    exact_clock10468_recovery_last={"audit": str(audit_path), "failed_cycle_credit": 0,
                        "original_AUTO_replayed": False, "sentinel_stop_claimed": False})
        expected_gov = {**old_gov, "pending_cycle": None}
        audit.update(status="PREDICATES_PASSED_METADATA_COMMIT_REQUIRED", fresh_frame=fresh,
                     observed_date_delta_raw=DATE - OLD_DATE,
                     fresh_semantic_sha256=env["sha256"](semantic_path),
                     counts_unchanged=work["counts"] == old_state["counts"],
                     checkpoint_anchor_unchanged=work["actual_saved_checkpoint"] == old_state["actual_saved_checkpoint"])
        env["atomic"](audit_path, audit, limit=16384)
        queue.full_loop_state = work
        queue.persist_loop_state()
        require(json.loads(_raw(env["Q"] / "ROOT-CUMULATIVE-LOOP-STATE.json")) == work
                and json.loads(_raw(env["Q"] / "ROOT-GOVERNANCE-RESULT-STATE.json")) == expected_gov,
                "two-file metadata readback differs; halt remains, no atomic-success claim")
        guard()
        queue.semantic = body
        result = {"status": "unknown_failed_clock_observed_and_reanchored", "audit": str(audit_path),
                  "frame": fresh, "completed_cycles": CYCLES, "failed_cycle_credit": 0,
                  "original_AUTO_replayed": False, "sentinel_stop_claimed": False,
                  "new_MCP_calls": 2, "new_auto_must_use_fresh_ordinary_planning": True}
        env["atomic"](env["OUTBOX"] / path.name, {"request": request, "result": {"is_error": False, "structured_content": result}}, limit=16384)
        queue.halted = queue.current_attempt = queue.held_control = None
        return result
    except Exception as error:
        queue.full_loop_state = old_state
        queue.halted, queue.current_attempt, queue.held_control = original_halt, original_attempt, None
        failure = {"status": "F97_observe_reanchor_failed_halt_retained", "message": str(error),
                   "original_AUTO": 10468, "original_AUTO_replayed": False, "failed_cycle_credit": 0,
                   "semantic_retry_allowed": False, "fresh_frame_if_checked": fresh,
                   "metadata_may_be_partially_committed": _exists(audit_path)}
        env["atomic"](env["OUTBOX"] / path.name, {"request": request, "result": {"is_error": True, "structured_content": failure}}, limit=16384)
        return failure
