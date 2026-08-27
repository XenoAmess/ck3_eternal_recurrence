#!/usr/bin/env python3
"""Prove one ordinary white-peace pending special-war binding live.

The immutable CK3 1.19.0.6 source save is never launched in place.  This
runner reuses the established pending-interaction seed seam: a disposable
seed clone proves the ordinary ``claim_cb`` WarID, submits one production
native white-peace offer, switches to the recipient on the same paused date,
and saves the still-pending request.  Only those checkpoint bytes enter a
fresh production-only clone.

The cold production process performs exactly two adjacent typed pending
context queries.  A read-only ``war_state`` observation between them must
remain on the same public/native revision and must independently identify the
same active WarID and primary leaders.  The typed term must be the exact
white-peace subtype, with actor 29829 as primary attacker and recipient 36108
as primary defender.  The runner never accepts, rejects, blocks, acknowledges,
or otherwise resolves the request.

This is an ordinary nonreligious ``claim_cb`` fixture.  Generic ``piety`` is
retained only as one raw resource slot in the ten-entry cost vector.  The
runner does not inspect faith, doctrine, tenet, fervor, conversion,
reformation, holy-war, or any other religion-specific semantics.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import time
from typing import Any
import uuid


RESEARCH_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_pending_character_interaction_context_live_acceptance as pending_live  # noqa: E402,E501
import run_owner_subset_retreat_live_acceptance as owner_live  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.pending_character_interaction_context_contract import (  # noqa: E402,E501
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
    normalize_pending_interaction_id,
    normalize_pending_character_interaction_context_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    ensure_state_path_safe,
    is_relative_to,
    paths_overlap,
    write_json_atomic,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import (  # noqa: E402
    NativeBridgeLaunchConfig,
    ck3_processes,
    utc_now,
)


PURE_NATIVE_MODE = pending_live.PURE_NATIVE_MODE
EXPECTED_ADAPTER_ID = pending_live.EXPECTED_ADAPTER_ID
EXPECTED_SOURCE_SAVE_SHA256 = pending_live.EXPECTED_SOURCE_SAVE_SHA256
DEFAULT_SOURCE_PROFILE = pending_live.DEFAULT_SOURCE_PROFILE
DEFAULT_SOURCE_SAVE = pending_live.DEFAULT_SOURCE_SAVE
CONTINUE_SAVE_NAME = owner_live.CONTINUE_SAVE_NAME

FROZEN_SPECIAL_WAR_SOURCE_COMMIT = (
    "542228a3c1221c189e4c9e84c35d8728aad4d1a1"
)
FROZEN_SPECIAL_WAR_DLL_SHA256 = (
    "2E60BC15320AA5C82E6C78AC236BC986601AFACB3C579A2F10881F43FD8B6C9F"
)
FROZEN_SPECIAL_WAR_INJECTOR_SHA256 = (
    "632A6EE3A87CA2658F20B7ECDA9F3B2F25414DFD8BDB77A4F929C8B142290E87"
)
DEFAULT_BRIDGE_BUILD_DIR = (
    WORKSPACE_ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / ".build-pending-special-war-binding-v1d-msvc"
)
DEFAULT_BRIDGE_DLL = DEFAULT_BRIDGE_BUILD_DIR / "xar_ck3_bridge.dll"
DEFAULT_BRIDGE_INJECTOR = (
    DEFAULT_BRIDGE_BUILD_DIR / "xar_ck3_bridge_injector.exe"
)
DEFAULT_GAME_DIR = WORKSPACE_ROOT / "Crusader Kings III"
DEFAULT_BRIDGE_PIPE = r"\\.\pipe\xar-pending-special-war-binding-live"

WAR_ID = pending_live.WAR_ID
SOURCE_CHARACTER_ID = pending_live.SOURCE_CHARACTER_ID
RECIPIENT_CHARACTER_ID = pending_live.RECIPIENT_CHARACTER_ID
EXPECTED_TARGET_TITLE_ID = pending_live.EXPECTED_TARGET_TITLE_ID
EXPECTED_CASUS_BELLI_KEY = pending_live.EXPECTED_CASUS_BELLI_KEY
EXPECTED_INTERACTION_KEY = pending_live.EXPECTED_INTERACTION_KEY
EXPECTED_SPECIAL_INTERACTION_KIND = "end_war_white_peace_interaction"
EXPECTED_ABSOLUTE_OUTCOME = "white_peace"
EXPECTED_BINDING_SOURCE = "native_common_war_relation"
EXPECTED_ACTOR_WAR_ROLE = "primary_attacker"
EXPECTED_RECIPIENT_WAR_ROLE = "primary_defender"

_COST_RESOURCE_KEYS = (
    "gold",
    "prestige",
    "piety",
    "renown",
    "influence",
    "herd",
    "treasury",
    "treasury_or_gold",
    "merit",
    "barter_goods",
)
_UNAVAILABLE_TERM_REASONS = {
    "structured_exchanges": "structured_exchanges_unavailable",
    "structured_effect_preview": "structured_effect_preview_unavailable",
    "recipient_ai_acceptance_score": (
        "recipient_ai_acceptance_score_unavailable"
    ),
    "recipient_ai_final_decision": (
        "recipient_ai_final_decision_unavailable"
    ),
}
_NOT_READY_REASONS = [
    "special_outcome_terms_unavailable",
    "structured_exchanges_unavailable",
    "structured_effect_preview_unavailable",
]
_FORBIDDEN_REPLY_STEPS = frozenset(
    {
        "accept-pending-character-interaction",
        "reject-pending-character-interaction",
        "block-pending-character-interaction",
        "acknowledge-pending-character-interaction",
    }
)
_ROOT_MARKER_NAME = ".xar-pending-special-war-binding-live.json"
_ROOT_KIND = "xar_pending_special_war_binding_live_acceptance"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-profile", type=Path, default=DEFAULT_SOURCE_PROFILE
    )
    parser.add_argument("--source-save", type=Path, default=DEFAULT_SOURCE_SAVE)
    parser.add_argument(
        "--expected-source-save-sha256",
        default=EXPECTED_SOURCE_SAVE_SHA256,
    )
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--bridge-pipe", default=DEFAULT_BRIDGE_PIPE)
    parser.add_argument("--bridge-dll", type=Path, default=DEFAULT_BRIDGE_DLL)
    parser.add_argument(
        "--expected-bridge-dll-sha256",
        default=FROZEN_SPECIAL_WAR_DLL_SHA256,
    )
    parser.add_argument(
        "--bridge-injector",
        type=Path,
        default=DEFAULT_BRIDGE_INJECTOR,
    )
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--seed-timeout", type=float, default=45.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _canonical_sha256(value: object, name: str) -> str:
    result = str(value).strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", result):
        raise ValueError(f"{name} must be 64 hex digits")
    return result


def _canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _positive_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _target_root(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-pending-special-war-binding-" + uuid.uuid4().hex
    )


def _prepare_root(
    root: Path,
    *,
    source_profile: Path,
    source_save_sha256: str,
    nonce: str,
) -> dict[str, object]:
    target = root.resolve()
    source = source_profile.resolve()
    if target.exists():
        raise AgentError(f"disposable root already exists: {target}")
    ensure_state_path_safe(target)
    if paths_overlap(source, target):
        raise AgentError("immutable source and disposable root overlap")
    target.mkdir(parents=True, exist_ok=False)
    marker = target / _ROOT_MARKER_NAME
    write_json_atomic(
        marker,
        {
            "kind": _ROOT_KIND,
            "nonce": nonce,
            "source_profile": str(source),
            "source_save_sha256": source_save_sha256,
            "frozen_source_commit": FROZEN_SPECIAL_WAR_SOURCE_COMMIT,
        },
    )
    return {"path": str(target), "marker": str(marker), "nonce": nonce}


def _cleanup_root(
    root: Path,
    *,
    nonce: str,
    retain: bool,
    stages: list[object],
) -> dict[str, object]:
    target = root.resolve()
    if retain:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "--retain-state prevents cleanup qualification",
        }
    unclean = []
    for raw in stages:
        stage = _mapping(raw)
        cleanup = _mapping(stage.get("cleanup"))
        if stage.get("session_started") is True and cleanup.get("ok") is not True:
            unclean.append(stage.get("stage"))
    if unclean:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "managed cleanup unproven for: "
            + ", ".join(str(value) for value in unclean),
        }
    marker = target / _ROOT_MARKER_NAME
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == _ROOT_KIND
            and payload.get("nonce") == nonce
        ):
            raise AgentError("disposable root marker differs")
        ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "path": str(target),
            "ok": removed,
            "reason": None if removed else "disposable root still exists",
        }
    except BaseException as error:
        return {
            "attempted": True,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": f"{type(error).__name__}: {error}",
        }


def _frozen_binary_preflight(
    *,
    bridge_dll: Path,
    bridge_injector: Path,
    expected_dll_sha256: str,
) -> dict[str, object]:
    dll_path = bridge_dll.expanduser().resolve()
    injector_path = bridge_injector.expanduser().resolve()
    dll_sha256 = _sha256_file(dll_path)
    injector_sha256 = _sha256_file(injector_path)
    checks = {
        "requested_dll_hash_is_frozen": (
            expected_dll_sha256 == FROZEN_SPECIAL_WAR_DLL_SHA256
        ),
        "dll_bytes_are_frozen": dll_sha256 == FROZEN_SPECIAL_WAR_DLL_SHA256,
        "injector_bytes_are_frozen": (
            injector_sha256 == FROZEN_SPECIAL_WAR_INJECTOR_SHA256
        ),
    }
    return {
        "source_commit": FROZEN_SPECIAL_WAR_SOURCE_COMMIT,
        "bridge_dll": str(dll_path),
        "bridge_dll_sha256": dll_sha256,
        "expected_bridge_dll_sha256": FROZEN_SPECIAL_WAR_DLL_SHA256,
        "bridge_injector": str(injector_path),
        "bridge_injector_sha256": injector_sha256,
        "expected_bridge_injector_sha256": (
            FROZEN_SPECIAL_WAR_INJECTOR_SHA256
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _zero_cost_proof(terms: dict[str, object]) -> dict[str, object]:
    item = _mapping(terms.get("structured_costs"))
    value = _mapping(item.get("value"))
    raw_entries = value.get("entries")
    entries = raw_entries if isinstance(raw_entries, list) else []
    exact_entries = [
        {"resource_key": key, "raw": 0} for key in _COST_RESOURCE_KEYS
    ]
    checks = {
        "typed_available": item.get("status") == "available"
        and item.get("reason") is None,
        "q100000": value.get("raw_scale") == 100_000,
        "actor_paid_on_send": value.get("payer_role") == "actor"
        and value.get("application_timing") == "on_send"
        and value.get("pending_payment_state") == "already_applied",
        "all_ten_stable_keys_zero": entries == exact_entries,
    }
    return {
        "value": copy.deepcopy(value),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _special_binding_proof(terms: dict[str, object]) -> dict[str, object]:
    item = _mapping(terms.get("special_war_binding"))
    value = _mapping(item.get("value"))
    expected = {
        "special_interaction_kind": EXPECTED_SPECIAL_INTERACTION_KIND,
        "absolute_outcome": EXPECTED_ABSOLUTE_OUTCOME,
        "war_id": WAR_ID,
        "actor_war_role": EXPECTED_ACTOR_WAR_ROLE,
        "recipient_war_role": EXPECTED_RECIPIENT_WAR_ROLE,
        "binding_source": EXPECTED_BINDING_SOURCE,
    }
    checks = {
        "typed_available": item.get("status") == "available"
        and item.get("reason") is None,
        "exact_white_peace_binding": value == expected,
    }
    return {
        "value": copy.deepcopy(value),
        "expected": expected,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _incomplete_terms_proof(
    terms: dict[str, object], readiness: dict[str, object]
) -> dict[str, object]:
    unavailable_checks = {
        key: _mapping(terms.get(key))
        == {"status": "unavailable", "value": None, "reason": reason}
        for key, reason in _UNAVAILABLE_TERM_REASONS.items()
    }
    readiness_checks = {
        "generic_costs_ready": readiness.get("generic_costs_ready") is True,
        "special_war_binding_ready": (
            readiness.get("special_war_binding_ready") is True
        ),
        "special_outcome_terms_not_ready": (
            readiness.get("special_outcome_terms_ready") is False
        ),
        "structured_terms_not_ready": (
            readiness.get("structured_terms_ready") is False
        ),
        "semantic_decision_not_ready": (
            readiness.get("interaction_semantic_decision_ready") is False
        ),
        "not_ready_reasons_exact": (
            readiness.get("not_ready_reasons") == _NOT_READY_REASONS
        ),
    }
    checks = {**unavailable_checks, **readiness_checks}
    return {"checks": checks, "ok": all(checks.values())}


def _context_proof(
    result: object,
    *,
    pending_id: int,
    native_revision: int,
    date_raw: int,
) -> dict[str, object]:
    envelope = _mapping(result)
    frame = _mapping(envelope.get("pending_character_interaction_context"))
    normalization_error: str | None = None
    normalized: dict[str, object] | None = None
    try:
        normalized = normalize_pending_character_interaction_context_v1(
            frame,
            expected_pending_interaction_id=pending_id,
            expected_date_raw=date_raw,
            expected_snapshot_revision=native_revision,
        )
    except (TypeError, ValueError) as error:
        normalization_error = f"{type(error).__name__}: {error}"
    observed = normalized if isinstance(normalized, dict) else frame
    definition = _mapping(observed.get("definition"))
    roles = _mapping(observed.get("roles"))
    terms = _mapping(observed.get("terms"))
    readiness = _mapping(observed.get("readiness"))
    binding = _mapping(envelope.get("binding"))
    special = _special_binding_proof(terms)
    costs = _zero_cost_proof(terms)
    incomplete = _incomplete_terms_proof(terms, readiness)
    checks = {
        "strict_contract_normalized": normalized is not None,
        "typed_available": envelope.get("status") == "available"
        and observed.get("status") == "available"
        and observed.get("reason") is None,
        "exact_query_envelope": envelope.get("step")
        == QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
        and envelope.get("accepted") is True
        and envelope.get("scope")
        == "exact-pending-character-interaction-context",
        "snapshot_binding": observed.get("snapshot_revision")
        == native_revision
        and observed.get("date_raw") == date_raw
        and observed.get("pending_interaction_id") == pending_id
        and envelope.get("snapshot_revision") == native_revision
        and binding.get("native_revision") == native_revision
        and binding.get("date_raw") == date_raw
        and binding.get("pending_interaction_id") == pending_id,
        "exact_build": observed.get("build")
        == {
            "version": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
            "exe_sha256": (
                PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
            ),
        },
        "canonical_white_peace_definition": definition.get("canonical_key")
        == EXPECTED_INTERACTION_KEY,
        "exact_roles": roles
        == {
            "actor_character_id": SOURCE_CHARACTER_ID,
            "recipient_character_id": RECIPIENT_CHARACTER_ID,
            "secondary_actor_character_id": -1,
            "secondary_recipient_character_id": -1,
            "intermediary_character_id": -1,
        },
        "special_data_present": terms.get("special_data_present") is True,
        "special_war_binding_exact": special.get("ok") is True,
        "generic_zero_cost_exact": costs.get("ok") is True,
        "remaining_terms_incomplete": incomplete.get("ok") is True,
        "overall_context_not_semantically_ready": envelope.get(
            "pending_character_interaction_context_ready"
        )
        is False,
    }
    return {
        "definition": copy.deepcopy(definition),
        "roles": copy.deepcopy(roles),
        "special_war_binding": special,
        "generic_zero_costs": costs,
        "incomplete_terms": incomplete,
        "readiness": copy.deepcopy(readiness),
        "strict_normalization_error": normalization_error,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _war_state_proof(
    value: object,
    *,
    paused_snapshot: dict[str, object],
) -> dict[str, object]:
    state = _mapping(value)
    raw_wars = state.get("active_wars")
    wars = raw_wars if isinstance(raw_wars, list) else []
    matches = [
        row
        for row in wars
        if isinstance(row, dict) and row.get("war_id") == WAR_ID
    ]
    war = matches[0] if len(matches) == 1 else {}
    checks = {
        "same_public_revision": state.get("revision")
        == paused_snapshot.get("revision"),
        "same_snapshot_id": state.get("snapshot_id")
        == paused_snapshot.get("snapshot_id"),
        "active_status": state.get("status") == "active",
        "one_exact_active_war": len(matches) == 1,
        "recipient_is_primary_defender": war.get("player_side") == "defender"
        and war.get("player_is_primary_war_leader") is True
        and pending_live._played_character_id(paused_snapshot)
        == RECIPIENT_CHARACTER_ID,
        "actor_is_primary_attacker": war.get(
            "primary_opponent_character_id"
        )
        == SOURCE_CHARACTER_ID,
        "native_war_projection": war.get("source") == "native",
        "same_nonreligious_target": EXPECTED_TARGET_TITLE_ID
        in (
            war.get("targeted_title_ids")
            if isinstance(war.get("targeted_title_ids"), list)
            else []
        ),
    }
    return {
        "war": copy.deepcopy(war) if isinstance(war, dict) else None,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _without_query_sequence(result: object) -> object:
    normalized = copy.deepcopy(result)
    if isinstance(normalized, dict):
        normalized.pop("query_sequence", None)
    return normalized


def _mutation_boundary_proof(commands: object) -> dict[str, object]:
    rows = commands if isinstance(commands, list) else []
    expected = [
        QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
        QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
    ]
    forbidden = [step for step in rows if step in _FORBIDDEN_REPLY_STEPS]
    checks = {
        "exact_two_pending_queries": rows == expected,
        "no_reply_or_ack": forbidden == [],
        "no_auto_turn": "auto-turn" not in rows,
        "all_commands_read_only": all(
            isinstance(step, str) and step.startswith("query-") for step in rows
        ),
    }
    return {
        "commands": list(rows),
        "expected_commands": expected,
        "forbidden_reply_steps_observed": forbidden,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _cross_stage_proof(
    seed_stage: object,
    production_stage: object,
    transfer: object,
) -> dict[str, object]:
    """Adapt the shared cross-stage proof to this runner's stricter key."""

    proof = pending_live._cross_stage_proof(
        seed_stage, production_stage, transfer
    )
    checks = _mapping(proof.get("checks"))
    seed = _mapping(seed_stage)
    production = _mapping(production_stage)
    seed_mutation = _mapping(seed.get("mutation_boundary"))
    seed_mutation_checks = _mapping(seed_mutation.get("checks"))
    sequence = _mapping(production.get("sequence"))
    production_mutation = _mapping(sequence.get("mutation_boundary"))
    production_mutation_checks = _mapping(
        production_mutation.get("checks")
    )
    seed_no_reply = seed_mutation_checks.get("no_reply_action") is True
    production_no_reply_or_ack = (
        production_mutation_checks.get("no_reply_or_ack") is True
    )
    checks["no_default_reply"] = seed_no_reply and production_no_reply_or_ack
    proof["checks"] = checks
    proof["reply_boundary_adapter"] = {
        "seed_check_key": "no_reply_action",
        "seed_check_value": seed_no_reply,
        "production_check_key": "no_reply_or_ack",
        "production_check_value": production_no_reply_or_ack,
        "production_is_stricter": True,
    }
    proof["ok"] = all(checks.values())
    return proof


def _run_double_query_sequence(
    service: GameplayBridgeService,
    *,
    expected_pending_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    commands: list[str] = []
    before = service.snapshot()
    pending_live._assert_paused_map_ready(before)
    if pending_live._played_character_id(before) != RECIPIENT_CHARACTER_ID:
        raise RuntimeError("cold query did not bind the recipient character")
    pending = pending_live._pending_identity(before)
    if pending is None or pending.get("instance_id") != expected_pending_id:
        raise RuntimeError("cold query did not restore the full pending ID")
    if pending.get("sender_character_id") != SOURCE_CHARACTER_ID:
        raise RuntimeError("cold query restored a different sender")
    if pending.get("auto_accept_notification") is not False:
        raise RuntimeError("fixture restored an auto-accept notification")
    revision = pending_live._snapshot_revision(before)
    native_revision = pending_live._snapshot_native_revision(before)
    date_raw = pending_live._snapshot_date(before)
    if date_raw != expected_date_raw:
        raise RuntimeError("cold query changed the fixture date")

    first = service.query_pending_character_interaction_context_v1(
        expected_pending_id,
        expected_revision=revision,
    )
    commands.append(QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP)
    war_state = service.war_state()
    second = service.query_pending_character_interaction_context_v1(
        expected_pending_id,
        expected_revision=revision,
    )
    commands.append(QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP)
    after = service.snapshot()

    first_proof = _context_proof(
        first,
        pending_id=expected_pending_id,
        native_revision=native_revision,
        date_raw=date_raw,
    )
    second_proof = _context_proof(
        second,
        pending_id=expected_pending_id,
        native_revision=native_revision,
        date_raw=date_raw,
    )
    war_proof = _war_state_proof(war_state, paused_snapshot=before)
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    first_frame = first.get("pending_character_interaction_context")
    second_frame = second.get("pending_character_interaction_context")
    mutation = _mutation_boundary_proof(commands)
    first_special = _mapping(first_proof.get("special_war_binding"))
    first_special_value = _mapping(first_special.get("value"))
    war = _mapping(war_proof.get("war"))
    checks = {
        "initial_paused_map_ready": before.get("paused") is True
        and before.get("map_ready") is True,
        "after_same_paused_binding": pending_live._same_paused_binding(
            before, after
        ),
        "first_context_valid": first_proof.get("ok") is True,
        "second_context_valid": second_proof.get("ok") is True,
        "war_state_same_revision_valid": war_proof.get("ok") is True,
        "war_id_cross_corroborated": first_special_value.get("war_id")
        == war.get("war_id")
        == WAR_ID,
        "primary_roles_cross_corroborated": first_special_value.get(
            "actor_war_role"
        )
        == EXPECTED_ACTOR_WAR_ROLE
        and first_special_value.get("recipient_war_role")
        == EXPECTED_RECIPIENT_WAR_ROLE
        and war.get("player_side") == "defender"
        and war.get("player_is_primary_war_leader") is True
        and war.get("primary_opponent_character_id") == SOURCE_CHARACTER_ID,
        "query_sequence_exact_successor": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and first_sequence > 0
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence == first_sequence + 1,
        "adjacent_context_frames_strictly_equal": isinstance(
            first_frame, dict
        )
        and first_frame == second_frame,
        "only_query_sequence_changed": _without_query_sequence(first)
        == _without_query_sequence(second),
        "exact_two_read_only_commands": mutation.get("ok") is True,
    }
    return {
        "expected_revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "pending_interaction_id": expected_pending_id,
        "before": pending_live._compact_snapshot(before),
        "war_state": copy.deepcopy(war_state),
        "war_state_proof": war_proof,
        "after": pending_live._compact_snapshot(after),
        "first_query": copy.deepcopy(first),
        "second_query": copy.deepcopy(second),
        "first_context_proof": first_proof,
        "second_context_proof": second_proof,
        "context_sha256": _canonical_json_sha256(first_frame),
        "mutation_boundary": mutation,
        "commands": commands,
        "observation_order": [
            "snapshot-before",
            "pending-query-1",
            "war-state-read-only",
            "pending-query-2",
            "snapshot-after",
        ],
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_production_query_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    expected_dll_sha256: str,
    expected_pending_id: int,
    expected_date_raw: int,
    timeout: float,
    readiness_timeout: float,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    readiness: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    exact_binary: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    sequence: dict[str, object] | None = None
    projection = pending_live._production_projection_proof(spec)
    primary_error: str | None = None
    executable_sha256: str | None = None
    dll_sha256: str | None = None
    injector_sha256: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                stop_event=stop_event,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        if projection.get("ok") is not True:
            raise AgentError("fresh query clone is not production-only")
        executable_sha256 = _sha256_file(spec.game_exe)
        dll_sha256 = _sha256_file(config.dll_path)
        injector_sha256 = _sha256_file(config.injector_path)
        if (
            executable_sha256
            != PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
        ):
            raise RuntimeError("managed CK3 executable SHA-256 differs")
        if dll_sha256 != expected_dll_sha256:
            raise RuntimeError("production bridge DLL SHA-256 differs")
        if injector_sha256 != FROZEN_SPECIAL_WAR_INJECTOR_SHA256:
            raise RuntimeError("production bridge injector SHA-256 differs")

        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-pending-special-war-binding-production-query",
            daemon=False,
        )
        thread.start()
        session_started = True
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        capabilities_before = driver.capabilities()
        exact_binary = pending_live._exact_binary_proof(
            capabilities_before,
            executable_sha256=executable_sha256,
            dll_sha256=dll_sha256,
            expected_dll_sha256=expected_dll_sha256,
        )
        capability = pending_live._capability_proof(
            capabilities_before, seed_stage=False
        )
        if exact_binary.get("ok") is not True:
            raise RuntimeError("production exact EXE/DLL proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("pending query capabilities are incomplete")
        sequence = _run_double_query_sequence(
            service,
            expected_pending_id=expected_pending_id,
            expected_date_raw=expected_date_raw,
        )
        if sequence.get("ok") is not True:
            raise RuntimeError("special-war live query sequence failed")
        capabilities_after = driver.capabilities()
        same_process = pending_live._same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("pending queries crossed bridge process")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if thread is not None and session_started:
            thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "production managed cleanup was not proven"
        )
    return {
        "stage": "fresh-production-special-war-binding-query",
        "session_started": session_started,
        "fresh_process_cold_reload": True,
        "production_profile": True,
        "debug_mode": False,
        "ok": bool(
            primary_error is None
            and projection.get("ok") is True
            and exact_binary
            and exact_binary.get("ok") is True
            and capability
            and capability.get("ok") is True
            and sequence
            and sequence.get("ok") is True
            and same_process
            and same_process.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path.resolve()),
            "bridge_dll_sha256": dll_sha256,
            "expected_bridge_dll_sha256": expected_dll_sha256,
            "bridge_injector": str(config.injector_path.resolve()),
            "bridge_injector_sha256": injector_sha256,
        },
        "production_projection_proof": projection,
        "readiness": readiness,
        "exact_binary_proof": exact_binary,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "sequence": sequence,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    started_wall = utc_now()
    timeout = _positive_seconds(args.timeout, "timeout")
    readiness_timeout = _positive_seconds(
        args.readiness_timeout, "readiness_timeout"
    )
    seed_timeout = _positive_seconds(args.seed_timeout, "seed_timeout")
    expected_source_sha = _canonical_sha256(
        args.expected_source_save_sha256,
        "expected source save SHA-256",
    )
    expected_dll_sha = _canonical_sha256(
        args.expected_bridge_dll_sha256,
        "expected bridge DLL SHA-256",
    )
    source_profile = args.source_profile.expanduser().resolve()
    root = _target_root(args.state_dir)
    output = args.output.expanduser().resolve()
    game_dir = args.game_dir.expanduser().resolve()
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    if is_relative_to(output, root):
        raise AgentError("artifact output must be outside disposable root")
    if is_relative_to(output, source_profile):
        raise AgentError("artifact output must be outside immutable source")
    if paths_overlap(source_profile, root):
        raise AgentError("immutable source and disposable root overlap")

    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.expanduser().resolve(),
        injector_path=args.bridge_injector.expanduser().resolve(),
    )
    frozen_binary: dict[str, object] | None = None
    source_save: Path | None = None
    source_identity: dict[str, object] | None = None
    source_before: dict[str, object] | None = None
    source_after: dict[str, object] | None = None
    disposable: dict[str, object] | None = None
    seed_materialization: dict[str, object] | None = None
    production_materialization: dict[str, object] | None = None
    seed_stage: dict[str, object] | None = None
    production_stage: dict[str, object] | None = None
    transfer: dict[str, object] | None = None
    cross_stage: dict[str, object] | None = None
    primary_error: str | None = None
    nonce = uuid.uuid4().hex

    try:
        if expected_source_sha != EXPECTED_SOURCE_SAVE_SHA256:
            raise AgentError("source save hash is not the frozen fixture")
        frozen_binary = _frozen_binary_preflight(
            bridge_dll=config.dll_path,
            bridge_injector=config.injector_path,
            expected_dll_sha256=expected_dll_sha,
        )
        if frozen_binary.get("ok") is not True:
            raise AgentError("bridge binary is not the frozen 542228a build")
        source_save, source_identity = pending_live._resolve_source_save(
            source_profile,
            args.source_save,
            expected_source_sha,
        )
        source_before = {
            "sha256": _sha256_file(source_save),
            "size": source_save.stat().st_size,
            "mtime_ns": source_save.stat().st_mtime_ns,
        }
        disposable = _prepare_root(
            root,
            source_profile=source_profile,
            source_save_sha256=expected_source_sha,
            nonce=nonce,
        )
        seed_spec, seed_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "seed-offer-switch-save",
            game_dir=game_dir,
            save_source=source_save,
            save_name=CONTINUE_SAVE_NAME,
        )
        seed_materialization["fixture_bridge"] = owner_live._install_seed_bridge(
            seed_spec
        )
        seed_stage = pending_live._run_seed_stage(
            spec=seed_spec,
            config=config,
            expected_dll_sha256=expected_dll_sha,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
        )
        if seed_stage.get("ok") is not True:
            raise AgentError(str(seed_stage.get("error") or "seed stage failed"))
        seed_pending = _mapping(seed_stage.get("pending_identity"))
        pending_id = seed_pending.get("instance_id")
        try:
            pending_id = normalize_pending_interaction_id(pending_id)
        except ValueError as error:
            raise AgentError(
                "seed stage lacks a valid signed full pending ID"
            ) from error
        seed_snapshot = _mapping(seed_stage.get("stable_pre_save_snapshot"))
        expected_date_raw = seed_snapshot.get("date_raw")
        if isinstance(expected_date_raw, bool) or not isinstance(
            expected_date_raw, int
        ):
            raise AgentError("seed stage lacks a signed game date")
        seed_checkpoint = owner_live._checkpoint_path(seed_spec)

        production_spec, production_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "fresh-production-special-war-binding-query",
            game_dir=game_dir,
            save_source=seed_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        transfer = pending_live._checkpoint_transfer_proof(
            seed_checkpoint, production_spec
        )
        if transfer.get("ok") is not True:
            raise AgentError("pending checkpoint transfer differs")
        production_stage = _run_production_query_stage(
            spec=production_spec,
            config=config,
            expected_dll_sha256=expected_dll_sha,
            expected_pending_id=pending_id,
            expected_date_raw=expected_date_raw,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if production_stage.get("ok") is not True:
            raise AgentError(
                str(
                    production_stage.get("error")
                    or "production special-war query stage failed"
                )
            )
        cross_stage = _cross_stage_proof(
            seed_stage, production_stage, transfer
        )
        if cross_stage.get("ok") is not True:
            raise AgentError("pending request changed across cold reload")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"

    if source_save is not None:
        try:
            source_after = {
                "sha256": _sha256_file(source_save),
                "size": source_save.stat().st_size,
                "mtime_ns": source_save.stat().st_mtime_ns,
            }
        except BaseException as error:
            if primary_error is None:
                primary_error = f"{type(error).__name__}: {error}"
    source_unchanged = bool(
        source_before is not None
        and source_after is not None
        and source_before == source_after
    )
    if source_save is not None and not source_unchanged and primary_error is None:
        primary_error = "immutable source save changed"

    stages: list[object] = [seed_stage, production_stage]
    no_ck3_processes = not ck3_processes()
    cleanup = _cleanup_root(
        root,
        nonce=nonce,
        retain=bool(args.retain_state),
        stages=stages,
    )
    if not no_ck3_processes and primary_error is None:
        primary_error = "a CK3 process remains after managed stages"
    if (
        cleanup.get("ok") is not True
        and disposable is not None
        and primary_error is None
    ):
        primary_error = str(cleanup.get("reason") or "disposable cleanup failed")

    seed_report = _mapping(seed_stage)
    production_report = _mapping(production_stage)
    sequence = _mapping(production_report.get("sequence"))
    sequence_checks = _mapping(sequence.get("checks"))
    first_proof = _mapping(sequence.get("first_context_proof"))
    first_checks = _mapping(first_proof.get("checks"))
    cross_checks = _mapping(_mapping(cross_stage).get("checks"))
    seed_war_checks = _mapping(
        _mapping(seed_report.get("war_options_proof")).get("checks")
    )
    seed_binary = _mapping(seed_report.get("exact_binary_proof"))
    production_binary = _mapping(production_report.get("exact_binary_proof"))
    readiness_gates = {
        "frozen_542228a_bridge_and_injector": _mapping(frozen_binary).get(
            "ok"
        )
        is True,
        "source_claim_cb_nonreligious_fixture": seed_war_checks.get(
            "ordinary_claim_cb"
        )
        is True,
        "production_native_white_peace_submitted": _mapping(
            seed_report.get("raw_offer_proof")
        ).get("ok")
        is True,
        "stable_full_pending_id_across_cold_reload": cross_checks.get(
            "same_full_pending_id"
        )
        is True,
        "fresh_production_only_cold_reload": cross_checks.get(
            "fresh_production_only"
        )
        is True,
        "exact_white_peace_special_war_binding": first_checks.get(
            "special_war_binding_exact"
        )
        is True,
        "same_revision_active_war_corroboration": all(
            sequence_checks.get(key) is True
            for key in (
                "war_state_same_revision_valid",
                "war_id_cross_corroborated",
                "primary_roles_cross_corroborated",
            )
        ),
        "adjacent_same_revision_double_query": all(
            sequence_checks.get(key) is True
            for key in (
                "after_same_paused_binding",
                "query_sequence_exact_successor",
                "adjacent_context_frames_strictly_equal",
                "only_query_sequence_changed",
            )
        ),
        "generic_zero_cost_baseline_only": first_checks.get(
            "generic_zero_cost_exact"
        )
        is True,
        "remaining_terms_and_semantics_stay_incomplete": first_checks.get(
            "remaining_terms_incomplete"
        )
        is True,
        "no_reply_or_ack": _mapping(sequence.get("mutation_boundary")).get(
            "ok"
        )
        is True,
        "exact_exe_and_dll": seed_binary.get("ok") is True
        and production_binary.get("ok") is True,
        "immutable_source_bytes_and_metadata": source_unchanged,
        "managed_process_cleanup": no_ck3_processes
        and all(
            isinstance(stage, dict)
            and _mapping(stage.get("cleanup")).get("ok") is True
            for stage in stages
        ),
        "nonce_disposable_cleanup": cleanup.get("ok") is True,
    }
    ok = bool(primary_error is None and all(readiness_gates.values()))
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": (
            "ck3_pending_character_interaction_special_war_binding_v1_"
            "live_acceptance"
        ),
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "fixed_scenario": {
            "war_id": WAR_ID,
            "actor_character_id": SOURCE_CHARACTER_ID,
            "recipient_character_id": RECIPIENT_CHARACTER_ID,
            "target_title_id": EXPECTED_TARGET_TITLE_ID,
            "casus_belli_key": EXPECTED_CASUS_BELLI_KEY,
            "interaction_key": EXPECTED_INTERACTION_KEY,
            "special_interaction_kind": EXPECTED_SPECIAL_INTERACTION_KIND,
            "absolute_outcome": EXPECTED_ABSOLUTE_OUTCOME,
            "actor_war_role": EXPECTED_ACTOR_WAR_ROLE,
            "recipient_war_role": EXPECTED_RECIPIENT_WAR_ROLE,
        },
        "policy": {
            "seed_generation_seam_reused": True,
            "production_stage_is_read_only": True,
            "ordinary_nonreligious_claim_cb_only": True,
            "white_peace_outcome_only": True,
            "victory_and_defeat_live_unproven": True,
            "generic_zero_cost_is_only_a_baseline": True,
            "generic_nonzero_cost_live_unproven": True,
            "special_outcome_terms_ready_expected": False,
            "structured_terms_ready_expected": False,
            "interaction_semantic_decision_ready_expected": False,
            "forbidden_reply_steps": sorted(_FORBIDDEN_REPLY_STEPS),
            "forbidden_reply_steps_invoked": [],
            "religion_domain_deferred": True,
            "piety_is_generic_raw_resource_only": True,
            "religion_specific_semantics_read": False,
        },
        "frozen_binary_contract": frozen_binary,
        "source_save": source_identity,
        "source_save_invariant": {
            "before": source_before,
            "after": source_after,
            "unchanged": source_unchanged,
        },
        "disposable": disposable,
        "seed_materialization": seed_materialization,
        "production_materialization": production_materialization,
        "checkpoint_transfer": transfer,
        "seed_stage": seed_stage,
        "production_stage": production_stage,
        "cross_stage_proof": cross_stage,
        "readiness_gates": readiness_gates,
        "no_ck3_processes_after": no_ck3_processes,
        "disposable_cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
    sequence = _mapping(_mapping(payload.get("production_stage")).get("sequence"))
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "output": str(output),
                "artifact_sha256": _sha256_file(output),
                "pending_interaction_id": sequence.get(
                    "pending_interaction_id"
                ),
                "war_id": WAR_ID,
                "readiness_gates": payload.get("readiness_gates"),
                "cleanup": payload.get("disposable_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
