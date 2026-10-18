"""Summarize old hypothetical observations after a fresh usable query.

Current canonical/model inputs and the latest history row remain complete. A
summary is not an archive and cannot reconstruct an omitted old body.
"""
from __future__ import annotations

import copy
import hashlib
import json

from .combat_contract import (
    combat_simulation_inputs_status, parse_query_combat_simulation_inputs_step,
)
from .combat_phase_contract import (
    combat_simulation_inputs_v3_status, parse_query_combat_simulation_inputs_v3_step,
)

SUMMARY_SCHEMA = "xar.superseded-combat-input-history-summary.v1"
MAX_BODY_BYTES = 64 * 1024 * 1024
MAX_BATCH_BYTES = 128 * 1024 * 1024
MAX_ROWS = 8


def _parsed(step):
    for version, parser in (
        (2, parse_query_combat_simulation_inputs_step),
        (3, parse_query_combat_simulation_inputs_v3_step),
    ):
        value = parser(step)
        if value is not None:
            return version, value
    return None


def _usable(step, result):
    parsed = _parsed(step)
    if (parsed is None or not isinstance(result, dict)
            or result.get("step") != step or result.get("accepted") is not True
            or result.get("status") != "available"
            or type(result.get("query_sequence")) is not int
            or not 0 < result["query_sequence"] < 2**64
            or not isinstance(result.get("queried_snapshot_id"), str)
            or type(result.get("queried_revision")) is not int
            or type(result.get("queried_native_revision")) is not int):
        return None
    body = result.get("combat_simulation_inputs")
    if (not isinstance(body, dict) or "projection_schema" in body
            or body.get("schema") == SUMMARY_SCHEMA):
        return None
    version, scenario = parsed
    base = body.get("base_inputs") if version == 3 else body
    if not isinstance(base, dict):
        return None
    observed = base.get("scenario")
    if (base.get("target_province_id") != scenario[0]
            or not isinstance(observed, dict)
            or observed.get("attacker_entry_province_id") != scenario[1]
            or observed.get("attacker_army_ids") != scenario[2]
            or observed.get("defender_army_ids") != scenario[3]):
        return None
    status = (combat_simulation_inputs_v3_status(body) if version == 3
              else combat_simulation_inputs_status(body))
    return (version, body) if status == "available" else None


def _digest(body, limit):
    digest = hashlib.sha256()
    size = 0
    encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
    for piece in encoder.iterencode(body):
        raw = piece.encode("utf-8")
        size += len(raw)
        if size > limit:
            raise ValueError("bounded combat history digest budget exceeded")
        digest.update(raw)
    return digest.hexdigest(), size


def _summary(version, result, body, limit):
    digest, size = _digest(body, limit)
    base = body.get("base_inputs") if version == 3 else body
    knight = base.get("knight_stat_consumption_v1")
    events = knight.get("events") if isinstance(knight, dict) else None
    return {
        "schema": SUMMARY_SCHEMA, "original_query_version": version,
        "query_sequence": result["query_sequence"],
        "queried_frame": {key: copy.deepcopy(result[key]) for key in (
            "queried_snapshot_id", "queried_revision", "queried_native_revision")},
        "target_province_id": base.get("target_province_id"),
        "scenario": copy.deepcopy(base.get("scenario")),
        "completeness": copy.deepcopy(body.get("completeness")),
        "base_completeness": copy.deepcopy(base.get("completeness")),
        "original_top_keys": list(body),
        "counts": {
            "armies": len(base["armies"]) if isinstance(base.get("armies"), list) else None,
            "knight_events": len(events) if isinstance(events, list) else None,
            "knight_contexts": sum(len(row["contexts"]) for row in events
                if isinstance(row, dict) and isinstance(row.get("contexts"), list))
                if isinstance(events, list) else None,
        },
        "canonical_sha256": digest, "canonical_json_bytes": size,
        "canonical_json_encoding": "utf-8;ensure_ascii=false;sort_keys=true;compact;allow_nan=false",
        "full_body_retained_in_driver_history": False,
        "full_body_reconstructible_from_summary": False,
        "immutable_archive_created_by_this_summary": False,
        "original_raw_MCP_receipt": {
            "preservation_status": "not_bound_by_this_helper", "exact_path_known": False,
            "lookup_facts": {"step": result["step"],
                "query_sequence": result["query_sequence"],
                "queried_native_revision": result["queried_native_revision"]},
        },
    }


def compact_superseded_combat_history_v1(driver, *, result):
    """Run only after the original typed query and successful normal recorder.

    Capture immutable recorded body references under the history lock, hash them
    off-lock, and check identities before replacing old body fields. Every row,
    envelope, current input and API result remains; errors retain full history.
    """
    step = result.get("step")
    usable = _usable(step, result)
    if usable is None:
        return 0
    version, _ = usable
    parsed = _parsed(step)[1]
    with driver._driver_state_lock:
        cache = getattr(driver, "_combat_simulation_inputs_query" if version == 2
                        else "_combat_simulation_inputs_v3_query", None)
        binding = cache.get("cache_binding") if isinstance(cache, dict) else None
        if (not isinstance(binding, dict) or cache.get("status") != "available"
                or cache.get("query_sequence") != result["query_sequence"]
                or binding.get("snapshot_id") != result["queried_snapshot_id"]
                or binding.get("revision") != result["queried_revision"]
                or binding.get("native_revision") != result["queried_native_revision"]
                or (binding.get("target_province_id"), binding.get("attacker_entry_province_id"),
                    binding.get("attacker_army_ids"), binding.get("defender_army_ids")) != parsed):
            return 0
    with driver._history_lock:
        history = driver._command_history
        if not history:
            return 0
        latest = history[-1]
        last = latest.get("result")
        if (latest.get("command") != step or latest.get("ok") is not True
                or not isinstance(last, dict)
                or any(last.get(key) != result.get(key) for key in (
                    "step", "accepted", "status", "query_sequence", "queried_snapshot_id",
                    "queried_revision", "queried_native_revision"))):
            return 0
        work = []
        for pos, row in enumerate(history[:-1]):
            old = row.get("result") if isinstance(row, dict) else None
            if not isinstance(row, dict) or row.get("ok") is not True:
                continue
            candidate = _usable(row.get("command"), old)
            if candidate is None or candidate[0] != version:
                continue
            if (old["query_sequence"] >= result["query_sequence"]
                    or old["queried_native_revision"] >= result["queried_native_revision"]
                    or old["queried_snapshot_id"] == result["queried_snapshot_id"]):
                continue
            work.append((pos, row, old, candidate[1]))
            if len(work) >= MAX_ROWS:
                break
    prepared = []
    bytes_hashed = 0
    for pos, row, old, body in work:
        summary = _summary(version, old, body,
                           min(MAX_BODY_BYTES, MAX_BATCH_BYTES - bytes_hashed))
        bytes_hashed += summary["canonical_json_bytes"]
        prepared.append((pos, row, old, body, summary))
    if not prepared:
        return 0
    with driver._history_lock:
        if driver._command_history is not history or not history or history[-1] is not latest:
            return 0
        if not all(pos < len(history) and history[pos] is row and row.get("result") is old
                   and old.get("combat_simulation_inputs") is body
                   for pos, row, old, body, summary in prepared):
            return 0
        for pos, row, old, body, summary in prepared:
            old["combat_simulation_inputs"] = summary
        driver._driver_state_history_json.invalidate()
        driver._driver_state_dirty = True
        return len(prepared)
