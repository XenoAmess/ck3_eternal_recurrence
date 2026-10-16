"""Pure Python capture identity and finite Army-result evidence helpers.

These functions do not connect to a process. Identity receipts are Root's
source-reviewed, per-runtime attestations, not a universal historical-ID map.
Army sidecars preserve the complete Driver result, never original pipe bytes.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROBERT_INTENT = {
    "bookmark_key": "bm_1066_rags_to_riches",
    "character_name_key": "bookmark_rags_to_riches_duke_robert",
    "history_id": 1128,
    "history_title_key": "d_apulia",
}
MAX_ARMY_HISTORY_SIDECAR_BYTES = 512 * 1024 * 1024
_PREPARED_KEYS = ("machine_id", "profile_dir", "state_dir", "pipe_name", "target_build",
                  "game", "bridge_dll", "succession_lifecycle", "checkpoint", "expected_character_id")

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)

def read_pinned_small_json(pin: dict, limit: int = 65536) -> dict:
    require(type(pin) is dict and set(pin) >= {"path", "bytes", "sha256"}, "identity receipt pin absent")
    path = Path(pin["path"])
    require(path.suffix.lower() == ".json" and path.is_file() and not path.is_symlink(), "identity JSON absent or symlink")
    require(type(pin["bytes"]) is int and 0 < pin["bytes"] <= limit and path.stat().st_size == pin["bytes"], "identity JSON size changed")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == str(pin["sha256"]).lower(), "identity receipt hash changed")
    result = json.loads(raw.decode("utf-8-sig"))
    require(type(result) is dict, "identity JSON must be an object")
    return result

def validate_prepared_robert_intent(prepared: dict) -> None:
    intent = prepared.get("character_intent")
    if intent is None:
        # Only the old known input form remains readable. Its numeric intent is
        # explicitly superseded by a separately pinned runtime receipt below.
        require(type(prepared.get("expected_character_id")) is int and prepared["expected_character_id"] == 29829,
                "legacy .4 preparation has no recognized Robert source intent")
    else:
        require(intent == ROBERT_INTENT, "prepared Robert source intent changed")

def validate_runtime_actor_context(receipt_pin: dict, prepared: dict, snapshot: dict,
                                   diagnostics: dict, arguments: dict, machine_id: str) -> dict:
    proof = read_pinned_small_json(receipt_pin)
    require(proof.get("schema") == "xar.e04.robert-identity-source-chain.actual.v1", "wrong normal-Robert identity receipt schema")
    require(proof.get("machine_id") == prepared.get("machine_id") == machine_id, "identity receipt belongs to another machine")
    intent = proof.get("stable_character_intent") or {}
    require(intent.get("bookmark_character_name_key") == ROBERT_INTENT["character_name_key"] and
            type(intent.get("historical_id")) is int and intent["historical_id"] == ROBERT_INTENT["history_id"] and
            intent.get("historical_title_key") == ROBERT_INTENT["history_title_key"], "wrong Robert source intent")
    require(re.fullmatch(r"[0-9a-f]{40}", str(proof.get("source_head", ""))) is not None,
            "identity source commit absent")
    layers = {r.get("layer") for r in proof.get("proof_chain", []) if type(r) is dict}
    require({"source-controlled-flow", "independent-live-reads-produced-by-root",
             "normal-save-materialization-and-bounded-header-read"}.issubset(layers), "normal-Robert source chain incomplete")
    superseded = proof.get("superseded_prelaunch_numeric_expectation") or {}
    archived = read_pinned_small_json(superseded.get("prepared"))
    require(prepared.get("expected_character_id") == archived.get("expected_character_id") == superseded.get("old_expected_character_id"),
            "old numeric intent not explicitly superseded")
    for key in _PREPARED_KEYS:
        require(prepared.get(key) == archived.get(key), "prepared scope changed: " + key)
    validate_prepared_robert_intent(prepared)
    target = prepared.get("target_build") or {}
    require(target.get("version") == "1.20.0.4" and
            target.get("exe_sha256") == (prepared.get("game") or {}).get("sha256"), "identity exact build changed")
    actor, pid, generation = (proof.get("actual_runtime_character_full_id"), proof.get("pid"), proof.get("connection_generation"))
    require(all(type(x) is int and x > 0 for x in (actor, pid, generation)), "identity runtime fields absent")
    player = snapshot.get("played_character") or {}
    require(player.get("character_id") == actor and player.get("alive") is True and
            snapshot.get("episode_character_id") == actor and snapshot.get("episode_run_id") == proof.get("episode_run_id"),
            "capture crossed admitted Robert actor/episode")
    require(snapshot.get("paused") is True and type(snapshot.get("date_raw")) is int and
            snapshot["date_raw"] >= proof.get("initial_date_raw", 2**63), "capture before proved normal root")
    hello, frame = diagnostics.get("hello") or {}, snapshot.get("diagnostics") or {}
    require(diagnostics.get("connected") is True and hello.get("ck3_build_match") is True and
            hello.get("game_adapter_status") == "ready" and hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64" and
            hello.get("expected_ck3_version") == target["version"] and
            str(hello.get("expected_ck3_sha256", "")).lower() == target["exe_sha256"], "capture exact native adapter changed")
    require(pid == diagnostics.get("bridge_pid") == hello.get("pid") == arguments.get("target_pid") == frame.get("bridge_pid") and
            generation == diagnostics.get("connection_generation") == frame.get("connection_generation"), "capture crossed admitted PID/generation")
    return {"machine_id": machine_id, "at_utc": datetime.now(timezone.utc).isoformat(), "target_build": target,
            "bridge_pid": pid, "connection_generation": generation, "expected_character_id": actor,
            "episode_run_id": proof["episode_run_id"], "snapshot_id": snapshot.get("snapshot_id"),
            "native_revision": snapshot.get("native_revision"), "identity_receipt": dict(receipt_pin),
            "identity_source_head": proof["source_head"], "identity_recorded_at_utc": proof.get("recorded_at_utc"),
            "superseded_prelaunch_expected_character_id": superseded.get("old_expected_character_id"),
            "identity_scope": "Root-reviewed normal-Robert source chain; exact one runtime; not universal numeric mapping"}

def make_capture_guard(original_guard, receipt_pin: dict, machine_id_provider):
    """Root may adopt this closure in an existing Python owner; no adoption here.

    The original prepared dict and .3 behavior stay unchanged. A new native
    PID/build/episode requires its own source-reviewed identity receipt.
    """
    pinned = copy.deepcopy(receipt_pin)
    read_pinned_small_json(pinned)
    def guarded(prepared, snapshot, diagnostics, arguments):
        if arguments.get("operation") != "start":
            return None
        target = prepared.get("target_build") or {}
        if target.get("version") != "1.20.0.4":
            return original_guard(prepared, snapshot, diagnostics, arguments)
        return validate_runtime_actor_context(pinned, prepared, snapshot, diagnostics, arguments, machine_id_provider())
    return guarded

def validate_army_history_limit(limit: int) -> int:
    require(type(limit) is int and 0 <= limit <= MAX_ARMY_HISTORY_SIDECAR_BYTES,
            "Army full-result sidecar budget must be an explicit integer from 0 to 512MiB")
    return limit

def admit_army_history_budget(args, prepared, *, source_head, machine_id, budget_factory=None):
    """Only an explicit Root receipt can extend the existing sidecar budget."""
    limit = args.army_history_sidecar_limit_bytes
    admission = getattr(args, "runtime_capacity_admission", None)
    if admission is None and type(limit) is int and 0 <= limit <= MAX_ARMY_HISTORY_SIDECAR_BYTES:
        return validate_army_history_limit(limit), None
    require(type(limit) is int and 0 <= limit < 2**63 and admission is not None,
            "Extended Army sidecar budget requires exact Root capacity PATH SHA256")
    require(prepared.get("machine_id") == machine_id
            and (prepared.get("target_build") or {}).get("version") == "1.20.0.4",
            "Extended Army sidecars require this machine's exact .4 prepared context")
    require(isinstance(admission, (list, tuple)) and len(admission) == 2,
            "Root capacity pin requires PATH SHA256")
    path = Path(admission[0]).resolve()
    require(path.suffix.lower() == ".json" and 0 < path.stat().st_size <= 1024*1024,
            "Root capacity must be bounded JSON")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == admission[1].lower(), "Root capacity exact SHA differs")
    capacity = json.loads(raw)
    if budget_factory is None:
        from review02.comparison.r10_compare import runtime_total_budget
        budget_factory = runtime_total_budget
    budget = budget_factory({"max_runtime_total_bytes": limit,
            "runtime_capacity_admission": admission}, scene_root=Path(prepared["assets_root"]),
        source_head=source_head, machine_id=machine_id,
        deadline_utc=capacity["quota_review_at_utc"])
    return limit, budget


def army_history_evidence(driver, request: dict, machine_id: str, previous_history_index: int) -> dict | None:
    tool, arguments = request.get("tool"), request.get("arguments") or {}
    if not (tool == "ck3_query_army_strengths" or
            (tool == "ck3_execute_step" and arguments.get("step") == "query-army-strengths-v1")):
        return None
    with driver._driver_state_lock:
        history = driver._command_history
        entry = history[-1] if history else {}
        fresh = (type(entry.get("index")) is int and entry["index"] > previous_history_index)
        result = copy.deepcopy(entry.get("result")) if fresh and entry.get("command") == "query-army-strengths-v1" else None
    report = {"machine_id": machine_id, "at_utc": datetime.now(timezone.utc).isoformat(),
              "request_id": request.get("request_id"), "limit_bytes": driver.army_query_history_sidecar_limit_bytes,
              "full_result_kind": "complete Driver result; not original pipe bytes", "full_result_preserved": False}
    if type(result) is not dict or result.get("history_summary_schema") != "xar.ck3.army-query-history-summary.v1":
        report["unavailable_reason"] = "matching_driver_history_summary_unavailable"
        return report
    report.update(driver_history_index=entry.get("index"), query_sequence=result.get("query_sequence"),
                  queried_revision=result.get("queried_revision"), queried_native_revision=result.get("queried_native_revision"),
                  army_strengths_profile=result.get("army_strengths_profile"),
                  full_result_preserved=result.get("full_result_preserved") is True)
    if report["full_result_preserved"]:
        report["raw_result_reference"] = result.get("raw_result_reference")
    else:
        report["unavailable_reason"] = result.get("unavailable_reason")
        report["history_storage_diagnostic"] = result.get("history_storage_diagnostic")
    return report
