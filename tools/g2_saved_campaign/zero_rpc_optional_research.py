"""Pure qualification and local settlement of an optional research preflight.

The caller collects immutable source/SEM evidence and dispatch marker facts.
No SDK import, process operation, gameplay call or automatic retry lives here.
The historical external succession dispatcher alias is not this operation.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any

ARMY_CONFIG_TOOL = "ck3_set_army_private_auto_scalar_ab_v1"
KNOWN_PREFLIGHT_ERROR = "Army AB research needs actual paused cold SEM/CAP"
SEMANTIC_TOOL = "ck3_take_semantic_snapshot_private_v1"
METRICS_TOOL = "root_current_runtime_metrics"
PENDING_FIELDS = ("pending_cycle", "pending_checkpoint", "terminal",
                  "pending_natural_succession", "pending_unsafe_route_halt")
FRAME_FIELDS = ("snapshot_id", "revision", "native_revision", "date_raw",
                "actor_character_id", "episode_run_id")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("zero-RPC optional research denied: " + message)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def qualify_optional_research_preflight_v1(
    original: Mapping[str, Any], *, error: Mapping[str, Any], state: Mapping[str, Any],
    readonly_research_tools: Sequence[str], semantic_row: Mapping[str, Any], semantic_raw: bytes,
    semantic_source: str, semantic_sha256: str, unused_sequence: int,
    inflight_requests: Mapping[int, Mapping[str, Any]], before_submit_sequences: Sequence[int],
    expected_game: Mapping[str, Any], observed_game_creation_filetime: int,
    expected_lifecycle: Mapping[str, Any], source_mode_raw: bytes,
    source_mode_sha256: str, expected_driver_source: str,
    source_pins: Mapping[str, str], observed_source_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Accept the exact known compare-config error only when no dispatch began.

    Marker inventories, source hashes and process FILETIME are facts collected
    by the caller. Their collection remains outside this portable pure function.
    """
    request = original.get("request") or {}
    sequence = request.get("sequence")
    arguments = request.get("arguments")
    _require(type(sequence) is int and sequence > 0
             and type(unused_sequence) is int and unused_sequence > sequence,
             "exact original and unused control sequence required")
    _require(original.get("row") is None and original.get("response") is None
             and error.get("error_type") == "ValueError"
             and error.get("message") == KNOWN_PREFLIGHT_ERROR,
             "only the reviewed pre-response ValueError is eligible")
    _require(request.get("tool") == ARMY_CONFIG_TOOL and "command" not in request
             and ARMY_CONFIG_TOOL in readonly_research_tools
             and isinstance(arguments, dict) and set(arguments) == {"mode", "expected_revision"}
             and arguments["mode"] == "compare"
             and type(arguments["expected_revision"]) is int and arguments["expected_revision"] >= 0,
             "exact optional compare configuration in the reviewed research scope required")
    _require(all(state.get(key) is None for key in PENDING_FIELDS),
             "unsettled gameplay must keep its original recovery")
    _require(sequence not in inflight_requests and sequence not in before_submit_sequences,
             "original dispatch or before-submit evidence excludes zero-RPC recovery")
    for number, inflight in inflight_requests.items():
        _require(type(number) is int and isinstance(inflight, Mapping),
                 "typed dispatch-marker inventory required")
        if sequence <= number < unused_sequence:
            _require(inflight.get("tool") in (SEMANTIC_TOOL, METRICS_TOOL),
                     "only independent readonly SEM/METRICS may follow the rejection")
    _require(isinstance(source_mode_raw, bytes) and len(source_mode_raw) <= 16384
             and hashlib.sha256(source_mode_raw).hexdigest() == source_mode_sha256,
             "actual bounded Driver mode bytes and SHA required")
    mode = json.loads(source_mode_raw)
    _require(isinstance(mode, dict) and mode.get("driver_class") == "NativeHeadlessGameplayDriver"
             and mode.get("episode_projection") == "one_life"
             and mode.get("before_submit_observation") is True
             and mode.get("policy_replaced") is False and mode.get("transport_cap_replaced") is False
             and mode.get("source_file") == expected_driver_source,
             "actual before-submit producer/source mode differs")
    _require(bool(source_pins) and expected_driver_source in source_pins
             and all(isinstance(path, str) and bool(path) and isinstance(digest, str)
                     and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
                     for path, digest in source_pins.items())
             and all(observed_source_hashes.get(path) == digest for path, digest in source_pins.items()),
             "actual frozen source hashes differ")
    _require(type(expected_game.get("pid")) is int and expected_game["pid"] > 0
             and type(expected_game.get("creation_filetime")) is int
             and expected_game["creation_filetime"] > 0
             and type(observed_game_creation_filetime) is int
             and observed_game_creation_filetime == expected_game["creation_filetime"],
             "actual retained Game process generation differs")
    fresh_request = semantic_row.get("request") or {}
    fresh_sequence = fresh_request.get("sequence")
    result = semantic_row.get("result") or {}
    body = result.get("structured_content")
    _require(isinstance(semantic_raw, bytes) and len(semantic_raw) <= 512 * 1024**2 + 65536
             and hashlib.sha256(semantic_raw).hexdigest() == semantic_sha256
             and json.loads(semantic_raw) == semantic_row,
             "retained SEM bytes/hash and decoded row differ")
    _require(type(fresh_sequence) is int and sequence < fresh_sequence < unused_sequence
             and fresh_request.get("tool") == SEMANTIC_TOOL and "command" not in fresh_request
             and fresh_request.get("arguments") == {} and result.get("is_error") is False
             and semantic_row.get("client_error") is None and isinstance(body, dict),
             "actual completed independent SEM after the rejection required")
    actor, diagnostics = body.get("played_character") or {}, body.get("diagnostics") or {}
    frame = {key: body.get(key) for key in FRAME_FIELDS}
    frame["actor_character_id"] = actor.get("character_id")
    before = state.get("before") or {}
    _require(body.get("paused") is True and body.get("map_ready") is True and actor.get("alive") is True
             and body.get("one_life_terminal") is not True
             and body.get("succession_lifecycle") == expected_lifecycle
             and diagnostics.get("bridge_pid") == expected_game["pid"]
             and (diagnostics.get("hello") or {}).get("pid") == expected_game["pid"]
             and all(type(frame.get(key)) is int for key in ("revision", "native_revision", "date_raw", "actor_character_id"))
             and frame["revision"] >= 0 and frame["native_revision"] > 0 and frame["actor_character_id"] > 0
             and frame["snapshot_id"] == "native:" + str(frame["native_revision"])
             and isinstance(frame["episode_run_id"], str) and bool(frame["episode_run_id"])
             and all(frame[key] == before.get(key) for key in ("actor_character_id", "episode_run_id", "date_raw"))
             and type(before.get("native_revision")) is int
             and frame["native_revision"] >= before["native_revision"],
             "fresh paused living same-Game actor/date/episode/lifecycle required")
    _require(type(state.get("completed_cycles")) is int and state["completed_cycles"] >= 0
             and isinstance(semantic_source, str) and bool(semantic_source)
             and isinstance(semantic_sha256, str) and len(semantic_sha256) == 64,
             "actual settled count and immutable SEM source pin required")
    return {"qualification": "zero_rpc_optional_research_preflight",
            "original_request": copy.deepcopy(request), "original_error": copy.deepcopy(dict(error)),
            "original_response": None, "fresh_frame": frame,
            "fresh_semantic_response": semantic_source, "fresh_semantic_sha256": semantic_sha256,
            "source_mode_sha256": source_mode_sha256, "source_pins": dict(source_pins),
            "same_game": dict(expected_game), "completed_cycles": state["completed_cycles"],
            "state_sha256": _digest(state), "unused_sequence": unused_sequence,
            "new_MCP_or_native_calls": 0, "original_request_replayed": False,
            "new_business_credit": 0, "succession_performed": False}


def settle_optional_research_preflight_v1(
    qualification: Mapping[str, Any], *, control_sequence: int, state: Mapping[str, Any],
    consume_sequence: Callable[[int], int], write_audit: Callable[[dict], None],
    persist_state: Callable[[dict], None], write_response: Callable[[dict], None],
    clear_halt: Callable[[], None], audit_exists: bool = False, response_exists: bool = False,
) -> dict[str, Any]:
    """Commit local metadata once through the host's existing atomic callbacks.

    Any callback failure retains the original halt: clear_halt is last. This
    API never retries a failed write or interprets a partial write as success.
    """
    _require(qualification.get("qualification") == "zero_rpc_optional_research_preflight"
             and type(control_sequence) is int
             and control_sequence == qualification.get("unused_sequence")
             and qualification.get("state_sha256") == _digest(state)
             and all(state.get(key) is None for key in PENDING_FIELDS)
             and qualification.get("new_MCP_or_native_calls") == 0
             and qualification.get("new_business_credit") == 0
             and qualification.get("original_request_replayed") is False
             and qualification.get("succession_performed") is False
             and (qualification.get("original_error") or {}).get("message") == KNOWN_PREFLIGHT_ERROR
             and (qualification.get("original_request") or {}).get("tool") == ARMY_CONFIG_TOOL
             and audit_exists is False and response_exists is False,
             "unique exact qualified local settlement required")
    receipt = {**qualification, "status": "zero_rpc_optional_research_preflight_cleared",
               "control_sequence": control_sequence, "counts_unchanged": True,
               "optional_research_deferred": True, "new_auto_admitted": True}
    _require(len(json.dumps(receipt, ensure_ascii=False).encode()) <= 16384,
             "local metadata receipt exceeds existing producer bound")
    projected = copy.deepcopy(dict(state))
    projected.update(before=copy.deepcopy(receipt["fresh_frame"]),
                     before_metrics_response=receipt["fresh_semantic_response"])
    _require(consume_sequence(control_sequence) == control_sequence,
             "host consumed a different sequence")
    write_audit(copy.deepcopy(receipt))
    persist_state(projected)
    write_response(copy.deepcopy(receipt))
    clear_halt()
    return receipt
