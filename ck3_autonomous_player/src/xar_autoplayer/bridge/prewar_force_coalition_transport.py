"""One fresh private query for a partial declaration-bound force observation.

The independently stamped top-level execution receipt is preserved before
the bare domain validator runs. Neither its ticket nor the effective defender
can be supplied by the domain to prove itself. This v1 never grants DECLARE.
"""

from __future__ import annotations

from collections.abc import Mapping
import math
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .prewar_force_coalition_contract import _declaration, normalize_prewar_force_coalition_v1
from .version_identity import CK3_12004, require_exact_native_build

STEP = "query-prewar-force-coalition-coverage-v1"
DOMAIN_KEY = "prewar_force_coalition_coverage"
_UINT64_MAX = (1 << 64) - 1
_TOP_KEYS = {"type", "protocol_version", "request_id", "ok", "execution_receipt", "result"}
_RESULT_KEYS = {"step", "accepted", "status", "private_build", "read_only", "advertised", "domain_key", DOMAIN_KEY}
_RECEIPT_KEYS = {"ticket", "query_sequence", "capture_epoch"}


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"prewar transport {name} is outside [{minimum}, {maximum}]")
    return value


def _frame_binding(snapshot: Mapping[str, object]) -> dict[str, object]:
    actor = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or not isinstance(hello, Mapping)):
        raise ValueError("prewar query requires a living paused native map")
    build = require_exact_native_build(hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))
    if build != CK3_12004:
        raise ValueError("prewar query requires the frozen exact .4 build")
    snapshot_id = snapshot.get("snapshot_id")
    episode = snapshot.get("episode_run_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("prewar query lacks a native snapshot identity")
    if episode is not None and (not isinstance(episode, str) or not episode):
        raise ValueError("prewar query episode lease is malformed")
    return {
        "snapshot_id": snapshot_id,
        "revision": _integer(snapshot.get("revision"), "public revision", 1, _UINT64_MAX),
        "native_revision": _integer(snapshot.get("native_revision"), "native revision", 1, _UINT64_MAX),
        "date_raw": _integer(snapshot.get("date_raw"), "date", -(1 << 31), (1 << 31) - 1),
        "actor_character_id": _integer(actor.get("character_id"), "actor", 1, (1 << 31) - 1),
        "connection_generation": _integer(diagnostics.get("connection_generation"), "connection generation", 0, _UINT64_MAX),
        "episode_run_id": episode,
        "game_version": build.game_version,
        "executable_sha256": build.executable_sha256,
    }


def current_prewar_declaration_source(
    driver: object, snapshot: dict[str, object], declaration_id: str,
) -> tuple[dict[str, object], dict[str, object], int]:
    """Freeze one current canonical selection without issuing a query."""
    declarations, declaration_sequence = driver._declarable_wars_cache_for_snapshot(
        snapshot, episode_run_id=snapshot.get("episode_run_id"),
    )
    proof_snapshot = {**snapshot, "declarable_wars": declarations}
    matches = [row for row in declarations if row.get("declaration_id") == declaration_id]
    if len(matches) != 1:
        raise ValueError("prewar query lacks one current selected declaration")
    identity, selected = _declaration(matches[0], "current declaration")
    expected = {"declaration_id": identity, **selected}
    sequence = _integer(declaration_sequence, "declaration sequence", 1, _UINT64_MAX)
    return proof_snapshot, expected, sequence


def _current_sources(
    driver: object, snapshot: dict[str, object], declaration_id: str,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Pair qualified v1 generic caches; never issue a prerequisite query."""
    proof_snapshot, expected, declaration_sequence = current_prewar_declaration_source(
        driver, snapshot, declaration_id,
    )
    observed = driver._war_entry_assessments_cache_for_snapshot(
        proof_snapshot, episode_run_id=snapshot.get("episode_run_id"),
    )
    if not isinstance(observed, Mapping) or observed.get("status") != "available":
        raise ValueError("prewar query lacks an independent current war-entry assessment")
    assessment = observed.get("war_entry_assessments")
    if not isinstance(assessment, Mapping):
        raise ValueError("prewar query lost its independent assessment")
    provenance = assessment.get("provenance")
    if (not isinstance(provenance, Mapping) or require_exact_native_build(
        provenance.get("game_version"), provenance.get("executable_sha256"),
    ) != CK3_12004):
        raise ValueError("prewar independent assessment belongs to another build")
    actor = snapshot.get("played_character")
    if (assessment.get("date_raw") != snapshot.get("date_raw")
            or assessment.get("actor_character_id") != actor.get("character_id")
            or assessment.get("snapshot_revision") != snapshot.get("native_revision")
            or observed.get("queried_snapshot_id") != snapshot.get("snapshot_id")
            or observed.get("queried_revision") != snapshot.get("revision")):
        raise ValueError("prewar independent assessment frame is stale")
    rows = assessment.get("assessments")
    candidates = [row for row in rows if isinstance(row, Mapping)
                  and row.get("target_character_id") == expected["target_character_id"]] if isinstance(rows, list) else []
    if len(candidates) != 1:
        raise ValueError("prewar selected target lacks one independent assessment")
    effective = _integer(candidates[0].get("effective_target_character_id"), "effective target", 1, (1 << 31) - 1)
    if effective == actor.get("character_id"):
        raise ValueError("prewar primary sides collapse to the actor")
    expected["effective_target_character_id"] = effective
    source_lease = {
        "declaration_query_sequence": declaration_sequence,
        "assessment_query_sequence": _integer(observed.get("query_sequence"), "assessment sequence", 1, _UINT64_MAX),
        "requested_target_character_id": expected["target_character_id"],
        "effective_target_character_id": effective,
        "effective_source": "same_frame_native_war_entry_assessment_generic_target",
        "assessment_game_version": CK3_12004.game_version,
        "assessment_executable_sha256": CK3_12004.executable_sha256,
    }
    return proof_snapshot, expected, source_lease


def validate_prewar_force_coalition_execution_receipt(
    frame: object, *, expected_request_id: str,
) -> tuple[dict[str, object], Mapping[str, object]]:
    """Validate the actual matched outer receipt, independently of domain data."""
    if not isinstance(frame, Mapping) or set(frame) != _TOP_KEYS:
        raise ValueError("prewar command_result top-level shape is malformed")
    if (frame["type"] != "command_result" or type(frame["protocol_version"]) is not int
            or frame["protocol_version"] != 1 or frame["request_id"] != expected_request_id
            or not isinstance(expected_request_id, str) or not expected_request_id or frame["ok"] is not True):
        raise ValueError("prewar command_result request binding mismatch")
    raw = frame["execution_receipt"]
    if not isinstance(raw, Mapping) or set(raw) != _RECEIPT_KEYS:
        raise ValueError("prewar independent execution receipt is missing or malformed")
    receipt = {key: _integer(raw[key], f"execution_receipt.{key}", 1, _UINT64_MAX) for key in _RECEIPT_KEYS}
    if receipt["query_sequence"] != receipt["ticket"]:
        raise ValueError("prewar execution sequence differs from its actual ticket")
    result = frame["result"]
    if (not isinstance(result, Mapping) or set(result) != _RESULT_KEYS
            or result["step"] != STEP or result["accepted"] is not True
            or result["status"] != "available_partial" or result["private_build"] is not True
            or result["read_only"] is not True or result["advertised"] is not False
            or result["domain_key"] != DOMAIN_KEY):
        raise ValueError("prewar partial private result envelope is malformed")
    return receipt, result


def query_prewar_force_coalition_coverage_v1(
    driver: object, declaration_id: str, *, expected_revision: int,
    timeout_seconds: float = 35.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_prewar_force_coalition_query", False) is not True:
        raise UnsupportedStepError("private prewar force/coalition query is disabled")
    _integer(expected_revision, "expected_revision", 1, _UINT64_MAX)
    if not isinstance(declaration_id, str) or not declaration_id:
        raise ValueError("declaration_id must be a nonempty canonical string")
    if type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("prewar query timeout must be finite and positive")
    before = driver.take_internal_semantic_snapshot()
    try:
        binding = _frame_binding(before)
        if binding["revision"] != expected_revision:
            raise PreSubmissionRevisionMismatchError("prewar force/coalition source revision is stale")
        _, expected, source_lease = _current_sources(driver, before, declaration_id)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    request_id = "prewar-coalition-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1, "request_id": request_id,
        "step": STEP, "expected_revision": binding["native_revision"],
        "expected_public_revision": binding["revision"], "declaration_id": declaration_id,
        "selected_declaration": {key: expected[key] for key in (
            "target_character_id", "casus_belli_index", "casus_belli_key",
            "configuration_index", "claimant_character_id", "target_title_ids",
        )},
    }
    driver.endpoint.send(request)
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if frame is None:
        raise BridgeUnavailableError("prewar force/coalition command_result timed out")
    if isinstance(frame, Mapping) and frame.get("request_id") == request_id and frame.get("ok") is False:
        if (set(frame) != {"type", "protocol_version", "request_id", "ok", "error"}
                or frame.get("type") != "command_result" or type(frame.get("protocol_version")) is not int
                or frame.get("protocol_version") != 1 or not isinstance(frame.get("error"), str)):
            raise BridgeUnavailableError("prewar force/coalition refusal envelope is malformed")
        raise BridgeUnavailableError(f"Native prewar force/coalition query refused: {frame.get('error')}")
    try:
        receipt, result = validate_prewar_force_coalition_execution_receipt(frame, expected_request_id=request_id)
        after = driver.take_internal_semantic_snapshot()
        if _frame_binding(after) != binding:
            raise ValueError("prewar force/coalition crossed its paused frame lease")
        current_proof, current_expected, current_sources = _current_sources(driver, after, declaration_id)
        if current_expected != expected or current_sources != source_lease:
            raise ValueError("prewar force/coalition selected tuple or independent source lease changed")
        domain = normalize_prewar_force_coalition_v1(
            result[DOMAIN_KEY], snapshot=current_proof, expected_declaration=expected,
            expected_request_binding=receipt,
        )
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **dict(result), DOMAIN_KEY: domain, "backend_id": "native-headless",
        "execution_receipt": receipt, "native_request_id": request_id,
        "queried_snapshot_id": binding["snapshot_id"], "queried_revision": binding["revision"],
        "queried_native_revision": binding["native_revision"], "queried_date_raw": binding["date_raw"],
        "queried_actor_character_id": binding["actor_character_id"],
        "queried_connection_generation": binding["connection_generation"],
        "queried_episode_run_id": binding["episode_run_id"], "independent_effective_source": source_lease,
    }


def prewar_force_coalition_history_summary(result: Mapping[str, object]) -> dict[str, object]:
    """A separate bounded history record, never a replacement domain DTO."""
    domain = result[DOMAIN_KEY]
    return {
        "schema": "prewar-force-coalition-history-summary-v1", "schema_version": 1,
        "step": STEP, "accepted": result["accepted"], "status": result["status"],
        "read_only": True, "full_result_preserved": False,
        "unavailable_reason": "domain_details_omitted_from_command_history",
        "native_request_id": result["native_request_id"], "execution_receipt": dict(result["execution_receipt"]),
        "frame_binding": {key: result[key] for key in (
            "queried_snapshot_id", "queried_revision", "queried_native_revision", "queried_date_raw",
            "queried_actor_character_id", "queried_connection_generation", "queried_episode_run_id",
        )},
        "declaration_id": domain["declaration_id"], "effective_target_character_id": domain["effective_target_character_id"],
        "actor_ready_unraised_lower_soldiers": domain["actor_ready_unraised_lower_soldiers"],
        "enemy_upper_soldiers": None, "enemy_force_coverage_complete": False,
        "complete_initial_participants_ready": False, "automatic_declaration_enabled": False,
        "current_allies_owner_rows": len(domain["current_allies"]), "owner_force_rows": len(domain["owner_forces"]),
        "raised_army_rows": sum(len(row["raised_armies"] or []) for row in domain["owner_forces"]),
    }
