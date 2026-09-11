#!/usr/bin/env python3
"""Four-domain terminal readback and one same-supervisor checkpoint restore.

The caller owns the admitted GameplayBridgeService, its existing supervisor,
the saved terminal checkpoint and final cleanup. No process is started here:
restore_checkpoint delegates the restart to that service's lifecycle queue.
Business projections exclude per-process pointers and query revisions; full
query responses remain in the evidence beside the compared durable fields.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from zg361_phase2_terminal_stages_action_cell import _stage11_terminal

DOMAINS = ("b1", "af5", "central", "workforce")


class TerminalColdRestoreError(RuntimeError):
    def __init__(self, reason: str, evidence: Mapping[str, object] | None = None):
        self.evidence = copy.deepcopy(dict(evidence or {}))
        super().__init__(reason)


def _write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} is not an object")
    return value


def _positive(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} is not a positive integer")
    return value


def _nonce(value: str, *, maximum: int = 54) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", value) is None:
        raise ValueError(f"request_nonce must be a nonempty ASCII token of at most {maximum} characters")


def _binding(snapshot: object) -> dict[str, object]:
    frame = _object(snapshot, "snapshot")
    if frame.get("paused") is not True or frame.get("map_ready") is not True:
        raise ValueError("terminal readback requires a paused map-ready session")
    diagnostics = _object(frame.get("diagnostics"), "diagnostics")
    played = _object(frame.get("played_character"), "played_character")
    return {
        "bridge_pid": _positive(diagnostics.get("bridge_pid"), "bridge PID"),
        "connection_generation": _positive(diagnostics.get("connection_generation"), "generation"),
        "player_character_id": _positive(played.get("character_id"), "played character"),
        "date_raw": frame["date_raw"],
    }


def _available(value: object, label: str, *, ready_key: str = "ready") -> Mapping[str, object]:
    result = _object(value, label)
    ready = _object(result.get("readiness"), label + " readiness")
    if result.get("status") != "available" or ready.get(ready_key) is not True:
        raise ValueError(f"{label} is not observable at the terminal checkpoint")
    return result


def _af5_available_or_tombstone(value: object) -> Mapping[str, object]:
    """Accept a live AF5 frame or its explicit destroyed-subject tombstone."""

    result = _object(value, "AF5")
    if result.get("status") == "available":
        return _available(result, "AF5")
    if not (
        result.get("status") == "unavailable"
        and result.get("unavailable_reason") == "subject_projection_read_failed"
        and isinstance(result.get("subject_character_id"), int)
        and not isinstance(result.get("subject_character_id"), bool)
        and result.get("subject_character_id") > 0
        and result.get("terminal") is False
    ):
        raise ValueError("AF5 is neither observable nor an explicit subject tombstone")
    readiness = _object(result.get("readiness"), "AF5 tombstone readiness")
    if any(value is not False for value in readiness.values()):
        raise ValueError("AF5 subject tombstone has an unexpected ready projection")
    leaves: list[Mapping[str, object]] = []

    def collect(node: object) -> None:
        if isinstance(node, Mapping):
            if {"status", "value", "unavailable_reason"} <= set(node):
                leaves.append(node)
                return
            for child in node.values():
                collect(child)
        elif isinstance(node, list):
            for child in node:
                collect(child)

    collect(_object(result.get("af5"), "AF5 tombstone payload"))
    if not leaves or any(
        leaf.get("status") != "unavailable"
        or leaf.get("value") is not None
        or leaf.get("unavailable_reason") != "variable_absent"
        for leaf in leaves
    ):
        raise ValueError("AF5 subject tombstone retains a partial business payload")
    return result


def read_terminal_domains_v1(
    service: object, *, request_nonce: str = "p1.restore",
    evidence_out: dict[str, object] | None = None,
) -> dict[str, object]:
    """Read actual B1/AF5/Central/Workforce durable state on one paused date.

    Each query binds the latest public revision. PID, generation, played owner
    and game date remain constant across the independent queries. The
    representative save must itself retain the Stage 11 Workforce terminal,
    while the independent B1 and AF5 business gates remain proven by their own
    P1 slices. This readback only proves that their current durable state and
    receipts survive the process replacement unchanged.
    """
    _nonce(request_nonce)
    evidence = {} if evidence_out is None else evidence_out
    initial = service.snapshot()
    binding = _binding(initial)
    evidence.update(before_snapshot=copy.deepcopy(initial), queries={})

    def query(name: str, method: str) -> Mapping[str, object]:
        current = service.snapshot()
        if _binding(current) != binding:
            raise ValueError("terminal queries crossed the paused session/date")
        response = getattr(service, method)(request_nonce + "." + name, expected_revision=current["revision"])
        evidence["queries"][name] = copy.deepcopy(response)
        return _object(response, name + " query")

    b1 = _available(query("b1", "query_zhongguo_b1_cycle_snapshot_v1"), "B1")
    af5 = _af5_available_or_tombstone(
        query("af5", "query_zhongguo_compensation_af5_snapshot_v1")
    )
    central_response = query("central", "query_zhongguo_promotion_source_progress_v1")
    if central_response.get("status") != "available":
        raise ValueError("Central query is unavailable")
    central = _available(central_response.get("zhongguo_promotion_source_progress"), "Central", ready_key="query_ready")
    workforce = _available(query("workforce", "query_zhongguo_workforce_owner_snapshot_v1"), "Workforce owner")
    if _stage11_terminal(workforce) is None:
        raise ValueError("Workforce closure or the Central stage11 callback is incomplete")
    for name, provider in (("b1", b1), ("af5", af5), ("central", central), ("workforce", workforce)):
        if provider.get("player_character_id") != binding["player_character_id"]:
            raise ValueError(f"{name} provider differs from the admitted played owner")

    widgets = central.get("widgets")
    if not isinstance(widgets, list) or not widgets:
        raise ValueError("Central stable widgets are unavailable")
    widget_state = []
    for raw in widgets:
        widget = _object(raw, "Central widget")
        identity = widget.get("stable_identity")
        if not isinstance(identity, str) or not identity:
            raise ValueError("Central widget stable identity is absent")
        widget_state.append({key: copy.deepcopy(widget[key]) for key in (
            "stable_identity", "exists", "effective_visible", "enabled",
        )})
    af = _object(af5.get("af5"), "AF5 payload")
    af_case = _object(af.get("case"), "AF5 case")
    wf = _object(workforce.get("workforce"), "Workforce payload")
    wf_case = _object(wf.get("al_case"), "AL case")
    identity_fields = ("owner_character_id", "subject_character_id", "cycle_serial", "case_serial")
    result = {
        "b1": {
            "identity": {"player_character_id": b1["player_character_id"],
                         "manager_character_id": b1["manager_character_id"],
                         **{key: copy.deepcopy(b1["cycle"][key]) for key in ("cycle_serial", "case_serial")}},
            "state": {key: copy.deepcopy(b1[key]) for key in ("cycle", "roster", "processing", "closure", "pending")},
            "receipt": {key: copy.deepcopy(b1[key]) for key in ("quota", "readiness", "invariants", "anomalies")},
        },
        "af5": {
            "identity": {"player_character_id": af5["player_character_id"],
                         "subject_character_id": af5["subject_character_id"],
                         "case_identity": copy.deepcopy(af_case["identity"]),
                         "result_identity": copy.deepcopy(af["portfolio"]["result_identity"])},
            "state": {"terminal": af5.get("terminal") is True, "portfolio": copy.deepcopy(af["portfolio"]),
                      "case": {key: copy.deepcopy(value) for key, value in af_case.items() if key != "identity"}},
            "receipt": {"observation_status": af5["status"],
                        "unavailable_reason": af5.get("unavailable_reason"),
                        "m299": copy.deepcopy(af["m299"]), "m300": copy.deepcopy(af["m300"]),
                        "readiness": copy.deepcopy(af5["readiness"])},
        },
        "central": {
            "identity": {"player_character_id": central["player_character_id"],
                         "stable_widget_identities": [row["stable_identity"] for row in widget_state],
                         "central_tuple": {key: copy.deepcopy(wf["central"][key]) for key in (
                             "subject_character_id", "cycle_serial", "case_serial",
                         )}},
            "state": {"widgets": widget_state, "stage11_status": copy.deepcopy(wf["central"]["stage11_status"])},
            "receipt": {"status": central["status"], "readiness": copy.deepcopy(central["readiness"])},
        },
        "workforce": {
            "identity": {"player_character_id": workforce["player_character_id"],
                         "subject_character_id": workforce["subject_character_id"],
                         "al_case": {key: copy.deepcopy(wf_case[key]) for key in identity_fields}},
            "state": {"terminal": workforce.get("terminal") is True, "terminal_kind": workforce["terminal_kind"],
                      "al_case": {key: copy.deepcopy(value) for key, value in wf_case.items() if key not in identity_fields},
                      "portfolio": copy.deepcopy(wf["portfolio"])},
            "receipt": {"source": copy.deepcopy(wf["source"]), "m360_receipt": copy.deepcopy(wf["m360_receipt"]),
                        "readiness": copy.deepcopy(workforce["readiness"])},
        },
    }
    final = service.snapshot()
    evidence["after_snapshot"] = copy.deepcopy(final)
    if _binding(final) != binding:
        raise ValueError("terminal queries crossed the paused session/date")
    evidence["readback"] = copy.deepcopy(result)
    return result


def _checkpoint(save_result: Mapping[str, object]) -> Mapping[str, object]:
    checkpoint = _object(save_result.get("checkpoint"), "saved checkpoint")
    if save_result.get("accepted") is not True or checkpoint.get("status") != "saved":
        raise ValueError("cold restore requires an accepted materialized terminal save")
    size = _positive(checkpoint.get("size"), "checkpoint size")
    expected_sha = checkpoint.get("sha256")
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha) is None:
        raise ValueError("terminal checkpoint lacks SHA256")
    path = Path(str(checkpoint["path"]))
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if path.stat().st_size != size or digest.hexdigest().upper() != expected_sha.upper():
        raise ValueError("terminal checkpoint differs from its saved bytes")
    return checkpoint


def _same_checkpoint(
    candidate: object, saved: Mapping[str, object]
) -> bool:
    if not isinstance(candidate, Mapping):
        return False
    try:
        candidate_path = Path(str(candidate.get("path", ""))).resolve()
        saved_path = Path(str(saved.get("path", ""))).resolve()
    except (OSError, RuntimeError):
        return False
    return bool(
        candidate.get("size") == saved.get("size")
        and str(candidate.get("sha256", "")).upper()
        == str(saved.get("sha256", "")).upper()
        and candidate_path == saved_path
    )


def _recover_completed_restore(
    service: object,
    state: Mapping[str, object],
    saved: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]] | None:
    """Recover an ACK lost after native-session already replaced CK3.

    The replacement driver records the completed managed transaction in its
    command history.  The lifecycle queue keeps the independent supervisor ACK.
    Both must match the saved bytes and the observed old/new PID pair before a
    retry may resume readback without launching a third process.
    """

    before_value = state.get("before_snapshot")
    if not isinstance(before_value, Mapping):
        return None
    before_binding = _binding(before_value)
    current = service.snapshot()
    current_binding = _binding(current)
    if not (
        current_binding["bridge_pid"] != before_binding["bridge_pid"]
        and current_binding["player_character_id"]
        == before_binding["player_character_id"]
        and current_binding["date_raw"] == before_binding["date_raw"]
    ):
        return None

    history_value = current.get("native_command_history")
    history = history_value if isinstance(history_value, list) else []
    history_entry: Mapping[str, object] | None = None
    history_result: Mapping[str, object] | None = None
    for item in reversed(history):
        if not isinstance(item, Mapping):
            continue
        result = item.get("result")
        if not (
            item.get("command") == "restore-checkpoint"
            and item.get("ok") is True
            and isinstance(result, Mapping)
            and result.get("accepted") is True
            and result.get("status") == "restored"
            and result.get("source") == "native-session-cold-start"
            and _same_checkpoint(result.get("checkpoint"), saved)
        ):
            continue
        lifecycle = result.get("lifecycle")
        if not (
            isinstance(lifecycle, Mapping)
            and lifecycle.get("previous_pid") == before_binding["bridge_pid"]
            and lifecycle.get("pid") == current_binding["bridge_pid"]
            and result.get("restored_date_raw") == current_binding["date_raw"]
            and result.get("map_ready") is True
        ):
            continue
        history_entry = item
        history_result = result
        break
    if history_entry is None or history_result is None:
        return None

    saved_path = Path(str(saved["path"])).resolve()
    state_dir = saved_path.parent.parent.parent
    outbox = state_dir / "native-session" / "bridge" / "outbox"
    queue_path: Path | None = None
    queue_response: Mapping[str, object] | None = None
    queue_result: Mapping[str, object] | None = None
    for candidate in sorted(
        outbox.glob("restore-*.json"),
        key=lambda item: item.stat().st_mtime_ns,
        reverse=True,
    ):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        result = payload.get("result") if isinstance(payload, Mapping) else None
        checkpoint = result.get("checkpoint") if isinstance(result, Mapping) else None
        if not (
            isinstance(payload, Mapping)
            and payload.get("protocol_version") == 1
            and payload.get("ok") is True
            and isinstance(payload.get("request_id"), str)
            and candidate.stem == payload.get("request_id")
            and isinstance(result, Mapping)
            and result.get("status") == "relaunched"
            and result.get("lifecycle_intent") == "restore"
            and result.get("previous_pid") == before_binding["bridge_pid"]
            and result.get("pid") == current_binding["bridge_pid"]
            and isinstance(checkpoint, Mapping)
            and checkpoint.get("size") == saved.get("size")
            and str(checkpoint.get("sha256", "")).upper()
            == str(saved.get("sha256", "")).upper()
        ):
            continue
        queue_path = candidate
        queue_response = payload
        queue_result = result
        break
    if queue_path is None or queue_response is None or queue_result is None:
        return None

    restored = copy.deepcopy(dict(history_result))
    restored["source"] = "native-session-lifecycle-queue"
    restored["checkpoint"] = {
        **copy.deepcopy(dict(saved)),
        **copy.deepcopy(dict(_object(history_result.get("checkpoint"), "history checkpoint"))),
        "status": "restored",
    }
    restored["starting_date"] = {"date_raw": before_binding["date_raw"]}
    restored["restored_date"] = {"date_raw": current_binding["date_raw"]}
    restored["starting_date_raw"] = before_binding["date_raw"]
    restored["restored_date_raw"] = current_binding["date_raw"]
    restored["paused"] = True
    restored["lifecycle"] = {
        **copy.deepcopy(dict(queue_result)),
        "request_id": queue_response["request_id"],
        "previous_connection_generation": before_binding[
            "connection_generation"
        ],
        "connection_generation": current_binding["connection_generation"],
    }
    recovery = {
        "status": "recovered_completed_restore",
        "source": "native_command_history_and_lifecycle_outbox",
        "history_index": history_entry.get("index"),
        "queue_response_path": str(queue_path.resolve()),
        "request_id": queue_response["request_id"],
        "before_binding": before_binding,
        "current_binding": current_binding,
    }
    return restored, recovery


def run_terminal_cold_restore(
    service: object, *, evidence_directory: Path, request_nonce: str,
    save_result: Mapping[str, object],
) -> dict[str, object]:
    """Restore the current terminal save once and return the canonical P1 row.

    A retry after a completed restore resumes readback on the new PID; it never
    repeats that lifecycle transition. The caller keeps this service and its
    supervisor alive until cleanup, including after a readback failure.
    """
    _nonce(request_nonce, maximum=47)
    directory = Path(evidence_directory)
    path = directory / "terminal-cold-restore.json"
    saved = _checkpoint(save_result)
    if path.is_file():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["request_nonce"] != request_nonce or state["save_result"] != dict(save_result):
            raise ValueError("cold restore retry belongs to another terminal checkpoint")
        if state["result"] == "GREEN":
            return state
    else:
        state = {"schema_version": 1, "kind": "zg361_phase2_terminal_cold_restore",
                 "result": "RED", "request_nonce": request_nonce, "attempt": 0,
                 "save_result": copy.deepcopy(dict(save_result)), "restore_result": None,
                 "mcp_only": True, "direct_process_launch_used": False, "cleanup_performed": False,
                 "failure_reason": None}
    state["attempt"] += 1
    state["failure_reason"] = None
    _write(path, state)
    try:
        if state["restore_result"] is None:
            recovered = (
                _recover_completed_restore(service, state, saved)
                if state["attempt"] > 1
                else None
            )
            if recovered is not None:
                state["restore_result"], state["restore_recovery"] = recovered
                _write(path, state)
            else:
                before = service.snapshot()
                before_binding = _binding(before)
                state["before_snapshot"] = before
                state["before_queries"] = {}
                state["before_readback"] = read_terminal_domains_v1(
                    service, request_nonce=request_nonce + ".before", evidence_out=state["before_queries"],
                )
                current = service.snapshot()
                if _binding(current) != before_binding:
                    raise ValueError("terminal session changed before the restore command")
                if saved.get("date_raw") != current["date_raw"]:
                    raise ValueError("terminal checkpoint date differs from the observed terminal frame")
                _write(path, state)
                state["restore_result"] = service.restore_checkpoint(expected_revision=current["revision"])
                # Preserve the lifecycle response before any follow-up provider call.
                _write(path, state)
        before = state["before_snapshot"]
        before_binding = _binding(before)
        restored = _object(state["restore_result"], "restore result")
        after = service.snapshot()
        after_binding = _binding(after)
        state["after_snapshot"] = after
        lifecycle = _object(restored.get("lifecycle"), "restore lifecycle")
        restored_checkpoint = _object(restored.get("checkpoint"), "restored checkpoint")
        capabilities = service.capabilities()
        state["final_capabilities"] = capabilities
        diagnostics = _object(capabilities.get("diagnostics"), "final capabilities diagnostics")
        first_pid, second_pid = before_binding["bridge_pid"], after_binding["bridge_pid"]
        first_generation, second_generation = before_binding["connection_generation"], after_binding["connection_generation"]
        checks = {
            "restore_acknowledged": restored.get("accepted") is True and restored.get("status") == "restored",
            "same_supervisor_lifecycle_queue": restored.get("source") == "native-session-lifecycle-queue" and lifecycle.get("lifecycle_intent") == "restore",
            "pid_changed": first_pid != second_pid,
            "process_local_generations_valid": first_generation > 0 and second_generation > 0,
            "lifecycle_pid_pair": lifecycle.get("previous_pid") == first_pid and lifecycle.get("pid") == second_pid,
            "lifecycle_generation_pair": lifecycle.get("previous_connection_generation") == first_generation and lifecycle.get("connection_generation") == second_generation,
            "restore_request_id_present": isinstance(lifecycle.get("request_id"), str) and bool(lifecycle.get("request_id")),
            "checkpoint_identical": str(restored_checkpoint.get("sha256", "")).upper() == str(saved["sha256"]).upper() and restored_checkpoint.get("size") == saved["size"] and Path(str(restored_checkpoint.get("path", ""))).resolve() == Path(str(saved["path"])).resolve(),
            "player_and_date_identical": before_binding["player_character_id"] == after_binding["player_character_id"] and before_binding["date_raw"] == after_binding["date_raw"],
            "final_capabilities_bind_second_pid": diagnostics.get("connected") is True and diagnostics.get("bridge_pid") == second_pid and diagnostics.get("connection_generation") == second_generation,
        }
        state["checks"] = checks
        if not all(checks.values()):
            raise ValueError("cold restore transition failed: " + ", ".join(key for key, good in checks.items() if not good))
        lineage = {
            "schema_version": 1, "result": "GREEN", "scope": "phase2_one_save_one_restore_two_pid_lineage",
            "mcp_only": True, "ocr_used": False, "image_used": False, "coordinates_used": False,
            "before": {**before_binding, "revision": before.get("revision"), "native_revision": before.get("native_revision"), "paused": True, "map_ready": True},
            "after_save": {**before_binding, "paused": True, "map_ready": True},
            "before_restore": {**before_binding, "paused": True, "map_ready": True},
            "after_restore": {**after_binding, "revision": after.get("revision"), "native_revision": after.get("native_revision"), "paused": True, "map_ready": True},
            "save_result": state["save_result"], "restore_result": restored,
            "first_pid": first_pid, "second_pid": second_pid, "pid_lineage": [first_pid, second_pid],
            "first_connection_generation": first_generation, "second_connection_generation": second_generation,
            "connection_generation_lineage": [first_generation, second_generation],
            "two_pid_lineage_proven": True, "checks": copy.deepcopy(checks), "failure_reason": None,
        }
        state["save_restore_lineage"] = lineage
        state["cleanup_handoff"] = {
            "supervisor_initial_pid": first_pid, "supervisor_initial_generation": first_generation,
            "current_pid": second_pid, "current_generation": second_generation,
            "scenario_evidence": {"save_restore_lineage": lineage}, "final_capabilities": capabilities,
        }
        state["after_queries"] = {}
        state["after_readback"] = read_terminal_domains_v1(
            service, request_nonce=request_nonce + ".after", evidence_out=state["after_queries"],
        )
        checks["four_domain_terminal_identity"] = state["after_readback"] == state["before_readback"]
        if not checks["four_domain_terminal_identity"]:
            raise ValueError("restored B1/AF5/Central/Workforce terminal readback differs")
        gate = {"result": "GREEN", "save_result": state["save_result"], "restore_result": restored,
                "pid_lineage": [first_pid, second_pid], "connection_generation_lineage": [first_generation, second_generation],
                "before_readback": state["before_readback"], "after_readback": state["after_readback"]}
        state["p1_acceptance_evidence"] = {"representative_terminal_cold_restore": gate}
        state["result"] = "GREEN"
        return state
    except Exception as error:
        state["failure_reason"] = f"{type(error).__name__}: {error}"
        raise TerminalColdRestoreError(str(error), state) from error
    finally:
        _write(path, state)
        _write(directory / f"attempt-{state['attempt']:03d}.json", state)
