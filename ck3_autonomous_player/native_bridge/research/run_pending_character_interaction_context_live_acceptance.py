#!/usr/bin/env python3
"""Materialize and prove one nonreligious pending white-peace request.

The immutable source checkpoint is never launched in place.  A disposable
seed clone loads the production bridge plus the repository ``mod_bridge``.
While paused, the source player first proves that WarID 16777290 is the
ordinary ``claim_cb`` fixture, then submits the production native
``offer-white-peace-16777290`` command through a deliberately seed-only raw
bridge call.  ``mod_bridge`` switches the played character, on the same game
date, to the recipient and a native checkpoint is saved while the request is
still pending.

Only the checkpoint bytes enter a fresh, verified production-only clone.  A
new supervised CK3 process cold-loads that save as the recipient and performs
exactly two adjacent read-only
``query-pending-character-interaction-context-v1`` calls.  GREEN requires
the same full pending ID, canonical white-peace definition, roles, routing,
zero send-option rows, deadline, reply legalities, exact EXE/DLL hashes,
immutable source bytes, and complete managed cleanup.  The runner never
accepts, rejects, blocks, or acknowledges the request.

Religion is intentionally outside this fixture.  It proves the generic
``claim_cb`` white-peace interaction only and reads no faith, doctrine,
tenet, fervor, conversion, reformation, or holy-war semantics.
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
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_loaded_feature_manifest_live_acceptance as manifest_live  # noqa: E402
import run_owner_subset_retreat_live_acceptance as owner_live  # noqa: E402
from xar_autoplayer.bridge.mod_driver import DataModGameplayDriver  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.pending_character_interaction_context_contract import (  # noqa: E402,E501
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    OFFER_WHITE_PEACE_CAPABILITY,
    QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
    query_war_termination_options_step,
)
from xar_autoplayer.environment import (  # noqa: E402
    OUTER_DESCRIPTOR_REF,
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


PURE_NATIVE_MODE = "native-headless"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
EXPECTED_SOURCE_SAVE_SHA256 = (
    "5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F"
)
DEFAULT_SOURCE_PROFILE = Path(
    r"C:\Users\xenoa\AppData\Local\Temp"
    r"\xar-war-entry-known-good-profile-control\profile"
)
DEFAULT_SOURCE_SAVE = Path(
    r"save games\xar_checkpoint_pre_white_peace_53175816.ck3"
)
CONTINUE_SAVE_NAME = owner_live.CONTINUE_SAVE_NAME
WAR_ID = 16_777_290
SOURCE_CHARACTER_ID = 29_829
RECIPIENT_CHARACTER_ID = 36_108
RECIPIENT_ANCHOR_PROVINCE_ID = 2_543
EXPECTED_TARGET_TITLE_ID = 2_388
EXPECTED_CASUS_BELLI_KEY = "claim_cb"
EXPECTED_INTERACTION_KEY = "end_war_attacker_white_peace_interaction"
OFFER_WHITE_PEACE_STEP = f"offer-white-peace-{WAR_ID}"
WAR_OPTIONS_STEP = query_war_termination_options_step(WAR_ID)
SAVE_CHECKPOINT_STEP = "save-checkpoint"

SWITCH_MARKER = (
    "XAR_FIXTURE:PENDING_INTERACTION_RECIPIENT_SWITCH|target=36108"
)
CLEAR_MARKER = "XAR_FIXTURE:PENDING_INTERACTION_SWITCH_GUARD_CLEARED"
SWITCH_GUARD = "xar_fixture_pending_interaction_switch_consumed"
SWITCH_SCOPE = "xar_fixture_pending_interaction_recipient"
SEED_NOOP_INBOX = (
    "# XAR pending-interaction fixture inbox: intentionally no effects.\n"
)
_ROOT_MARKER_NAME = ".xar-pending-interaction-context-live.json"
_ROOT_KIND = "xar_pending_interaction_context_live_acceptance"

_FORBIDDEN_REPLY_STEPS = frozenset(
    {
        "accept-pending-character-interaction",
        "reject-pending-character-interaction",
        "block-pending-character-interaction",
        "acknowledge-pending-character-interaction",
    }
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-profile", type=Path, default=DEFAULT_SOURCE_PROFILE
    )
    parser.add_argument(
        "--source-save", type=Path, default=DEFAULT_SOURCE_SAVE
    )
    parser.add_argument(
        "--expected-source-save-sha256",
        default=EXPECTED_SOURCE_SAVE_SHA256,
    )
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--expected-bridge-dll-sha256", required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
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
        "xar-pending-interaction-context-" + uuid.uuid4().hex
    )


def _resolve_source_save(
    source_profile: Path,
    requested: Path,
    expected_sha256: str,
) -> tuple[Path, dict[str, object]]:
    profile = source_profile.expanduser().resolve()
    if not profile.is_dir():
        raise AgentError(f"immutable source profile is missing: {profile}")
    candidate, identity = owner_live._resolve_source_save(
        profile, requested, expected_sha256
    )
    stat = candidate.stat()
    return candidate, {
        "profile": str(profile),
        **identity,
        "mtime_ns": stat.st_mtime_ns,
    }


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
        },
    )
    return {
        "path": str(target),
        "marker": str(marker),
        "nonce": nonce,
    }


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
    unclean: list[object] = []
    for value in stages:
        stage = value if isinstance(value, dict) else {}
        cleanup = stage.get("cleanup")
        cleanup = cleanup if isinstance(cleanup, dict) else {}
        if (
            stage.get("session_started") is True
            and cleanup.get("ok") is not True
        ):
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


def _switch_effect() -> str:
    return (
        f"province:{RECIPIENT_ANCHOR_PROVINCE_ID} = {{\n"
        "\tprovince_owner = {\n"
        f"\t\tsave_temporary_scope_as = {SWITCH_SCOPE}\n"
        "\t}\n"
        "}\n"
        "if = {\n"
        "\tlimit = {\n"
        f"\t\texists = scope:{SWITCH_SCOPE}\n"
        f"\t\tNOT = {{ global_var:{SWITCH_GUARD} = 1 }}\n"
        "\t}\n"
        "\tset_global_variable = {\n"
        f"\t\tname = {SWITCH_GUARD}\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        f"\tset_player_character = scope:{SWITCH_SCOPE}\n"
        f'\tdebug_log = "{SWITCH_MARKER}"\n'
        "}\n"
    )


def _clear_effect() -> str:
    return (
        "if = {\n"
        f"\tlimit = {{ exists = global_var:{SWITCH_GUARD} }}\n"
        f"\tremove_global_variable = {SWITCH_GUARD}\n"
        f'\tdebug_log = "{CLEAR_MARKER}"\n'
        "}\n"
    )


def _played_character_id(snapshot: object) -> int | None:
    return owner_live._played_character_id(snapshot)


def _snapshot_revision(snapshot: dict[str, object]) -> int:
    value = snapshot.get("revision")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError("paused snapshot lacks a public revision")
    return value


def _snapshot_native_revision(snapshot: dict[str, object]) -> int:
    value = snapshot.get("native_revision")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuntimeError("paused snapshot lacks a positive native revision")
    return value


def _snapshot_date(snapshot: dict[str, object]) -> int:
    value = snapshot.get("date_raw")
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("paused snapshot lacks date_raw")
    return value


def _assert_paused_map_ready(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True:
        raise RuntimeError("pending-interaction fixture requires pause")
    if snapshot.get("map_ready") is not True:
        raise RuntimeError("pending-interaction fixture requires map-ready")


def _pending_identity(snapshot: object) -> dict[str, object] | None:
    if not isinstance(snapshot, dict):
        return None
    pending = snapshot.get("pending_character_interaction")
    if not isinstance(pending, dict):
        return None
    pending_id = pending.get("instance_id")
    sender = pending.get("sender_character_id")
    notification = pending.get("auto_accept_notification")
    if (
        isinstance(pending_id, bool)
        or not isinstance(pending_id, int)
        or not 1 <= pending_id <= 2**31 - 1
        or isinstance(sender, bool)
        or not isinstance(sender, int)
        or sender <= 0
        or not isinstance(notification, bool)
    ):
        return None
    return {
        "instance_id": pending_id,
        "sender_character_id": sender,
        "auto_accept_notification": notification,
    }


def _compact_snapshot(snapshot: object) -> object:
    if not isinstance(snapshot, dict):
        return snapshot
    war = next(
        (
            row
            for row in snapshot.get("active_wars", [])
            if isinstance(row, dict) and row.get("war_id") == WAR_ID
        ),
        None,
    )
    compact_war = None
    if isinstance(war, dict):
        compact_war = {
            key: copy.deepcopy(war.get(key))
            for key in (
                "war_id",
                "player_side",
                "primary_opponent_character_id",
                "player_is_primary_war_leader",
                "targeted_title_ids",
                "player_relative_war_score",
            )
        }
    return {
        key: copy.deepcopy(snapshot.get(key))
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "paused",
            "map_ready",
            "episode_run_id",
            "backend_id",
        )
    } | {
        "played_character_id": _played_character_id(snapshot),
        "pending_character_interaction": _pending_identity(snapshot),
        "fixed_war": compact_war,
    }


def _same_paused_binding(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return bool(
        before.get("paused") is True
        and before.get("map_ready") is True
        and after.get("paused") is True
        and after.get("map_ready") is True
        and all(
            before.get(key) == after.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "episode_run_id",
                "pending_character_interaction",
            )
        )
    )


def _source_war_proof(snapshot: object) -> dict[str, object]:
    raw = snapshot if isinstance(snapshot, dict) else {}
    wars = raw.get("active_wars")
    rows = wars if isinstance(wars, list) else []
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("war_id") == WAR_ID
    ]
    war = matches[0] if len(matches) == 1 else {}
    targeted = war.get("targeted_title_ids")
    checks = {
        "paused_map_ready": raw.get("paused") is True
        and raw.get("map_ready") is True,
        "source_player": _played_character_id(raw) == SOURCE_CHARACTER_ID,
        "one_exact_war": len(matches) == 1,
        "source_is_primary_attacker": war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True,
        "recipient_is_primary_opponent": war.get(
            "primary_opponent_character_id"
        )
        == RECIPIENT_CHARACTER_ID,
        "known_target_title": isinstance(targeted, list)
        and EXPECTED_TARGET_TITLE_ID in targeted,
    }
    return {
        "war": copy.deepcopy(war) if isinstance(war, dict) else None,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _war_options_proof(result: object) -> dict[str, object]:
    envelope = result if isinstance(result, dict) else {}
    value = envelope.get("war_termination_options")
    options = value if isinstance(value, dict) else {}
    cb_value = options.get("active_casus_belli_identity")
    cb = cb_value if isinstance(cb_value, dict) else {}
    outcomes_value = options.get("options")
    outcomes = outcomes_value if isinstance(outcomes_value, dict) else {}
    white_value = outcomes.get("white_peace")
    white = white_value if isinstance(white_value, dict) else {}
    checks = {
        "exact_step": envelope.get("step") == WAR_OPTIONS_STEP,
        "accepted_available": envelope.get("accepted") is True
        and envelope.get("status") == "available",
        "matching_war": options.get("war_id") == WAR_ID,
        "primary_attacker": options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True,
        "ordinary_claim_cb": cb.get("canonical_key")
        == EXPECTED_CASUS_BELLI_KEY,
        "white_peace_allowed": options.get("cb_allows_white_peace") is True,
        "white_peace_context_valid": white.get("context_constructed") is True
        and white.get("native_validator_passed") is True
        and white.get("available") is True,
    }
    return {
        "casus_belli_identity": copy.deepcopy(cb),
        "white_peace_option": copy.deepcopy(white),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _raw_offer_white_peace(
    driver: object,
    *,
    expected_revision: int,
) -> dict[str, object]:
    primitive = getattr(driver, "_execute_primitive_step", None)
    if not callable(primitive):
        raise AgentError("native driver lacks the seed-only raw bridge call")
    result = primitive(
        OFFER_WHITE_PEACE_STEP,
        expected_revision=expected_revision,
        required_capability=OFFER_WHITE_PEACE_CAPABILITY,
    )
    if not isinstance(result, dict):
        raise AgentError("raw white-peace call returned a non-object")
    checks = {
        "exact_step": result.get("step") == OFFER_WHITE_PEACE_STEP,
        "accepted": result.get("accepted") is True,
        "submitted": result.get("status") == "submitted",
        "native_backend": result.get("backend_id") == PURE_NATIVE_MODE,
    }
    return {
        "result": copy.deepcopy(result),
        "seed_only_raw_call": True,
        "required_capability": OFFER_WHITE_PEACE_CAPABILITY,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    return manifest_live._diagnostics(capabilities)


def _capability_proof(
    capabilities: object,
    *,
    seed_stage: bool,
) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    advertised_value = raw.get("bridge_capabilities")
    advertised = advertised_value if isinstance(advertised_value, list) else []
    hello_value = _diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_caps_value = hello.get("capabilities")
    hello_caps = (
        hello_caps_value if isinstance(hello_caps_value, list) else []
    )
    action_value = raw.get("action_steps")
    actions = action_value if isinstance(action_value, list) else []
    required = (
        {
            OFFER_WHITE_PEACE_CAPABILITY,
            QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY,
            QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
        }
        if seed_stage
        else {QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY}
    )
    checks = {
        "bridge_capabilities": required.issubset(set(advertised)),
        "hello_capabilities": required.issubset(set(hello_caps)),
        "pending_query_action_identity_gate": (
            QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP not in actions
            if seed_stage
            else QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
            in actions
        ),
        "driver_pending_query_surface": raw.get(
            "pending_character_interaction_context_v1_query_supported"
        )
        is True,
    }
    if seed_stage:
        checks.update(
            {
                "war_options_action": WAR_OPTIONS_STEP in actions,
                "save_checkpoint_action": SAVE_CHECKPOINT_STEP in actions,
                "white_peace_not_public_action": not any(
                    isinstance(step, str)
                    and step.startswith("offer-white-peace-")
                    for step in actions
                ),
            }
        )
    return {
        "seed_stage": seed_stage,
        "required_bridge_capabilities": sorted(required),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _exact_binary_proof(
    capabilities: object,
    *,
    executable_sha256: str,
    dll_sha256: str,
    expected_dll_sha256: str,
) -> dict[str, object]:
    result = manifest_live._exact_binary_proof(
        capabilities,
        managed_executable_sha256=executable_sha256,
        production_dll_sha256=dll_sha256,
        expected_production_dll_sha256=expected_dll_sha256,
    )
    checks = result.get("checks")
    if isinstance(checks, dict):
        checks["pending_contract_game_version"] = (
            result.get("expected_game_version")
            == PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION
        )
        checks["pending_contract_executable_sha256"] = (
            result.get("expected_executable_sha256")
            == PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
        )
        checks["pending_contract_adapter"] = (
            result.get("expected_adapter_id") == EXPECTED_ADAPTER_ID
        )
        result["ok"] = all(checks.values())
    return result


def _same_process_proof(
    before_capabilities: object, after_capabilities: object
) -> dict[str, object]:
    return manifest_live._same_process_proof(
        before_capabilities, after_capabilities
    )


def _mutation_boundary_proof(
    commands: object,
    *,
    seed_stage: bool,
) -> dict[str, object]:
    rows = commands if isinstance(commands, list) else []
    expected = (
        [WAR_OPTIONS_STEP, OFFER_WHITE_PEACE_STEP, SAVE_CHECKPOINT_STEP]
        if seed_stage
        else [
            QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
            QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
        ]
    )
    reply_steps = [step for step in rows if step in _FORBIDDEN_REPLY_STEPS]
    checks = {
        "exact_commands": rows == expected,
        "no_reply_action": reply_steps == [],
        "no_auto_turn": "auto-turn" not in rows,
        "only_seed_has_gameplay_mutation": (
            OFFER_WHITE_PEACE_STEP in rows
            if seed_stage
            else all(step.startswith("query-") for step in rows)
        ),
    }
    return {
        "seed_stage": seed_stage,
        "commands": list(rows),
        "expected_commands": expected,
        "forbidden_reply_steps_observed": reply_steps,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _context_proof(
    result: object,
    *,
    pending_id: int,
    native_revision: int,
    date_raw: int,
) -> dict[str, object]:
    envelope = result if isinstance(result, dict) else {}
    frame_value = envelope.get("pending_character_interaction_context")
    frame = frame_value if isinstance(frame_value, dict) else {}
    definition_value = frame.get("definition")
    definition = definition_value if isinstance(definition_value, dict) else {}
    roles_value = frame.get("roles")
    roles = roles_value if isinstance(roles_value, dict) else {}
    target_value = frame.get("target")
    target = target_value if isinstance(target_value, dict) else {}
    options_value = frame.get("send_options")
    options = options_value if isinstance(options_value, dict) else {}
    rows_value = options.get("rows")
    rows = rows_value if isinstance(rows_value, list) else []
    routing_value = frame.get("routing")
    routing = routing_value if isinstance(routing_value, dict) else {}
    deadline_value = frame.get("deadline")
    deadline = deadline_value if isinstance(deadline_value, dict) else {}
    auto_value = frame.get("auto_accept")
    auto = auto_value if isinstance(auto_value, dict) else {}
    legality_value = frame.get("legality")
    legality = legality_value if isinstance(legality_value, dict) else {}
    terms_value = frame.get("terms")
    terms = terms_value if isinstance(terms_value, dict) else {}
    readiness_value = frame.get("readiness")
    readiness = readiness_value if isinstance(readiness_value, dict) else {}
    binding_value = envelope.get("binding")
    binding = binding_value if isinstance(binding_value, dict) else {}

    target_present = target.get("present")
    target_type_closed = bool(
        target_present is False
        and target.get("type_key_status") == "absent"
        and target.get("typed_identity_status") == "absent"
        or target_present is True
        and target.get("type_key_status") == "available"
        and isinstance(target.get("type_key"), str)
        and bool(target.get("type_key"))
        and target.get("typed_identity_status") == "unavailable"
        and target.get("typed_identity") is None
    )
    options_exact = bool(
        options.get("exclusive") is True
        and options.get("definition_count") == 0
        and options.get("context_count") == 0
        and rows == []
    )
    legality_available = all(
        isinstance(legality.get(key), dict)
        and legality[key].get("status") == "available"
        for key in ("accept", "reject", "block", "acknowledge")
    )
    structured_terms_unavailable = all(
        isinstance(terms.get(key), dict)
        and terms[key].get("status") == "unavailable"
        and terms[key].get("value") is None
        for key in (
            "structured_costs",
            "structured_exchanges",
            "structured_effect_preview",
            "recipient_ai_acceptance_score",
            "recipient_ai_final_decision",
        )
    )
    partial_ready_keys = (
        "stable_definition_ready",
        "roles_ready",
        "target_type_key_ready",
        "send_options_ready",
        "routing_ready",
        "deadline_ready",
        "auto_accept_ready",
        "reply_legality_ready",
        "same_frame_ready",
    )
    checks = {
        "typed_available": envelope.get("status") == "available"
        and frame.get("status") == "available"
        and frame.get("reason") is None,
        "exact_scope": envelope.get("step")
        == QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
        and envelope.get("accepted") is True
        and envelope.get("scope")
        == "exact-pending-character-interaction-context",
        "snapshot_binding": frame.get("snapshot_revision")
        == native_revision
        and frame.get("date_raw") == date_raw
        and frame.get("pending_interaction_id") == pending_id
        and envelope.get("snapshot_revision") == native_revision
        and binding.get("native_revision") == native_revision
        and binding.get("date_raw") == date_raw
        and binding.get("pending_interaction_id") == pending_id,
        "exact_build": frame.get("build")
        == {
            "version": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
            "exe_sha256": (
                PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
            ),
        },
        "canonical_white_peace_definition": definition.get("canonical_key")
        == EXPECTED_INTERACTION_KEY
        and isinstance(definition.get("deterministic_key_hash"), int)
        and not isinstance(definition.get("deterministic_key_hash"), bool)
        and isinstance(definition.get("runtime_ordinal"), int)
        and not isinstance(definition.get("runtime_ordinal"), bool),
        "exact_roles": roles
        == {
            "actor_character_id": SOURCE_CHARACTER_ID,
            "recipient_character_id": RECIPIENT_CHARACTER_ID,
            "secondary_actor_character_id": -1,
            "secondary_recipient_character_id": -1,
            "intermediary_character_id": -1,
        },
        "target_envelope_typed": target_type_closed,
        "zero_send_options_exact": options_exact,
        "recipient_local_route": routing
        == {
            "kind": 0,
            "played_character_id": RECIPIENT_CHARACTER_ID,
            "current_responder_role": "recipient",
            "reply_execution_channel": "recipient",
            "local_route": True,
            "auto_accept_notification": False,
        },
        "fresh_deadline": deadline.get("age_days") == 0
        and isinstance(deadline.get("expiration_days"), int)
        and not isinstance(deadline.get("expiration_days"), bool)
        and deadline.get("expiration_days", 0) > 0
        and deadline.get("remaining_days") == deadline.get("expiration_days")
        and deadline.get("expiry_boundary_status") == "not_reached",
        "not_auto_accept": auto
        == {"status": "available", "value": False, "reason": None},
        "reply_legalities_available": legality_available,
        "accept_and_reject_legal": isinstance(legality.get("accept"), dict)
        and legality["accept"].get("allowed") is True
        and isinstance(legality.get("reject"), dict)
        and legality["reject"].get("allowed") is True,
        "block_legal": isinstance(legality.get("block"), dict)
        and legality["block"].get("allowed") is True,
        "acknowledge_not_normal_reply": isinstance(
            legality.get("acknowledge"), dict
        )
        and legality["acknowledge"].get("allowed") is False
        and legality["acknowledge"].get("reason")
        == "normal_reply_channel",
        "special_data_present": terms.get("special_data_present") is True,
        "structured_terms_explicit_unavailable": (
            structured_terms_unavailable
        ),
        "partial_observation_readiness": all(
            readiness.get(key) is True for key in partial_ready_keys
        )
        and readiness.get("structured_terms_ready") is False
        and readiness.get("interaction_semantic_decision_ready") is False
        and envelope.get(
            "pending_character_interaction_context_ready"
        )
        is False,
    }
    return {
        "definition": copy.deepcopy(definition),
        "roles": copy.deepcopy(roles),
        "target": copy.deepcopy(target),
        "send_options": copy.deepcopy(options),
        "routing": copy.deepcopy(routing),
        "deadline": copy.deepcopy(deadline),
        "auto_accept": copy.deepcopy(auto),
        "legality": copy.deepcopy(legality),
        "terms": copy.deepcopy(terms),
        "readiness": copy.deepcopy(readiness),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _without_query_sequence(result: object) -> object:
    normalized = copy.deepcopy(result)
    if isinstance(normalized, dict):
        normalized.pop("query_sequence", None)
    return normalized


def _run_double_query_sequence(
    service: GameplayBridgeService,
    *,
    expected_pending_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    commands: list[str] = []
    before = service.snapshot()
    _assert_paused_map_ready(before)
    if _played_character_id(before) != RECIPIENT_CHARACTER_ID:
        raise RuntimeError("cold query did not bind the recipient character")
    pending = _pending_identity(before)
    if pending is None or pending.get("instance_id") != expected_pending_id:
        raise RuntimeError("cold query did not restore the full pending ID")
    if pending.get("sender_character_id") != SOURCE_CHARACTER_ID:
        raise RuntimeError("cold query restored a different sender")
    if pending.get("auto_accept_notification") is not False:
        raise RuntimeError("fixture restored an auto-accept notification")
    revision = _snapshot_revision(before)
    native_revision = _snapshot_native_revision(before)
    date_raw = _snapshot_date(before)
    if date_raw != expected_date_raw:
        raise RuntimeError("cold query changed the fixture date")

    first = service.query_pending_character_interaction_context_v1(
        expected_pending_id,
        expected_revision=revision,
    )
    commands.append(QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP)
    between = service.snapshot()
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
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    first_frame = first.get("pending_character_interaction_context")
    second_frame = second.get("pending_character_interaction_context")
    mutation = _mutation_boundary_proof(commands, seed_stage=False)
    checks = {
        "initial_paused_map_ready": before.get("paused") is True
        and before.get("map_ready") is True,
        "between_same_paused_binding": _same_paused_binding(before, between),
        "after_same_paused_binding": _same_paused_binding(before, after),
        "first_context_valid": first_proof.get("ok") is True,
        "second_context_valid": second_proof.get("ok") is True,
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
        "before": _compact_snapshot(before),
        "between": _compact_snapshot(between),
        "after": _compact_snapshot(after),
        "first_query": copy.deepcopy(first),
        "second_query": copy.deepcopy(second),
        "first_context_proof": first_proof,
        "second_context_proof": second_proof,
        "context_sha256": _canonical_json_sha256(first_frame),
        "mutation_boundary": mutation,
        "commands": commands,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _production_projection_proof(spec: Any) -> dict[str, object]:
    load_path = spec.profile_dir / "dlc_load.json"
    try:
        payload = json.loads(load_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {
            "checks": {},
            "ok": False,
            "error": f"{type(error).__name__}: {error}",
        }
    seed_mod_dir = (
        spec.profile_dir
        / "mod-content"
        / owner_live.MOD_BRIDGE_TARGET_NAME
    )
    seed_outer = spec.profile_dir / "mod" / owner_live.MOD_BRIDGE_OUTER_NAME
    checks = {
        "exact_production_playset": payload
        == {"enabled_mods": [OUTER_DESCRIPTOR_REF], "disabled_dlcs": []},
        "production_tree_present": spec.production_dir.is_dir(),
        "seed_mod_tree_absent": not seed_mod_dir.exists(),
        "seed_outer_descriptor_absent": not seed_outer.exists(),
        "seed_inbox_absent": not owner_live._seed_inbox_path(spec).exists(),
    }
    return {
        "dlc_load": payload,
        "production_dir": str(spec.production_dir.resolve()),
        "seed_mod_dir": str(seed_mod_dir.resolve()),
        "checks": checks,
        "ok": all(checks.values()),
        "error": None,
    }


def _checkpoint_transfer_proof(
    seed_checkpoint: Path,
    production_spec: Any,
) -> dict[str, object]:
    source = owner_live._checkpoint_identity(seed_checkpoint)
    continue_save = (
        production_spec.profile_dir / "save games" / CONTINUE_SAVE_NAME
    )
    last_save = production_spec.profile_dir / "last_save.ck3"
    continue_identity = owner_live._checkpoint_identity(continue_save)
    last_identity = owner_live._checkpoint_identity(last_save)
    checks = {
        "continue_bytes_equal": continue_identity["sha256"]
        == source["sha256"],
        "last_save_bytes_equal": last_identity["sha256"]
        == source["sha256"],
        "sizes_equal": continue_identity["size"]
        == last_identity["size"]
        == source["size"],
        "fresh_continue_name": continue_save.name == CONTINUE_SAVE_NAME,
    }
    return {
        "seed_checkpoint": source,
        "production_continue_save": continue_identity,
        "production_last_save": last_identity,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _wait_for_switch_and_pending(
    service: GameplayBridgeService,
    *,
    debug_log: Path,
    log_offset: int,
    expected_date_raw: int,
    deadline: float,
    session_done: threading.Event,
    session_state: dict[str, object],
) -> tuple[dict[str, object], bool]:
    observed_marker = False
    while time.monotonic() < deadline:
        observed_marker = owner_live._debug_marker_observed(
            debug_log, SWITCH_MARKER, offset=log_offset
        )
        candidate = service.snapshot()
        pending = _pending_identity(candidate)
        if (
            observed_marker
            and _played_character_id(candidate) == RECIPIENT_CHARACTER_ID
            and candidate.get("date_raw") == expected_date_raw
            and pending is not None
            and pending.get("sender_character_id") == SOURCE_CHARACTER_ID
            and pending.get("auto_accept_notification") is False
        ):
            return candidate, True
        if session_done.is_set():
            raise AgentError(
                str(
                    session_state.get("error")
                    or "seed session ended before recipient pending appeared"
                )
            )
        time.sleep(0.05)
    raise AgentError(
        "mod_bridge did not produce the same-day recipient pending request"
    )


def _run_seed_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    expected_dll_sha256: str,
    timeout: float,
    readiness_timeout: float,
    seed_timeout: float,
) -> dict[str, object]:
    started = time.monotonic()
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
    source_war: dict[str, object] | None = None
    war_options_result: dict[str, object] | None = None
    war_options_proof: dict[str, object] | None = None
    raw_offer: dict[str, object] | None = None
    initial: dict[str, object] | None = None
    switched: dict[str, object] | None = None
    stable: dict[str, object] | None = None
    after_save: dict[str, object] | None = None
    save_result: dict[str, object] | None = None
    checkpoint: dict[str, object] | None = None
    switch_write: dict[str, object] | None = None
    noop_after_switch: dict[str, object] | None = None
    clear_write: dict[str, object] | None = None
    final_noop: dict[str, object] | None = None
    switch_marker_observed = False
    clear_marker_observed = False
    poll_frames: list[dict[str, object]] = []
    clear_poll_frames: list[dict[str, object]] = []
    commands: list[str] = []
    primary_error: str | None = None
    executable_sha256: str | None = None
    dll_sha256: str | None = None
    injector_sha256: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = owner_live._fixture_native_session(
                spec=spec,
                config=config,
                timeout=timeout + 90.0,
                stop_event=stop_event,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
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

        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-pending-interaction-seed-session",
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
        initial = service.snapshot()
        _assert_paused_map_ready(initial)
        source_war = _source_war_proof(initial)
        if source_war.get("ok") is not True:
            raise AgentError("immutable source war identity differs")

        capabilities_before = driver.capabilities()
        exact_binary = _exact_binary_proof(
            capabilities_before,
            executable_sha256=executable_sha256,
            dll_sha256=dll_sha256,
            expected_dll_sha256=expected_dll_sha256,
        )
        capability = _capability_proof(
            capabilities_before, seed_stage=True
        )
        if exact_binary.get("ok") is not True:
            raise RuntimeError("seed exact EXE/DLL proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("seed bridge capabilities are incomplete")

        initial_revision = _snapshot_revision(initial)
        initial_date = _snapshot_date(initial)
        war_options_result = service.query_war_termination_options(
            WAR_ID, expected_revision=initial_revision
        )
        commands.append(WAR_OPTIONS_STEP)
        war_options_proof = _war_options_proof(war_options_result)
        if war_options_proof.get("ok") is not True:
            raise AgentError("source war is not the exact ordinary claim fixture")

        offer_snapshot = service.snapshot()
        _assert_paused_map_ready(offer_snapshot)
        if (
            _played_character_id(offer_snapshot) != SOURCE_CHARACTER_ID
            or _snapshot_date(offer_snapshot) != initial_date
        ):
            raise AgentError("source identity/date changed before raw offer")
        raw_offer = _raw_offer_white_peace(
            driver,
            expected_revision=_snapshot_revision(offer_snapshot),
        )
        commands.append(OFFER_WHITE_PEACE_STEP)
        if raw_offer.get("ok") is not True:
            raise AgentError("raw white-peace submission was not accepted")

        debug_log = spec.profile_dir / "logs" / "debug.log"
        switch_offset = owner_live._debug_log_offset(debug_log)
        switch_write = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), _switch_effect()
        )
        switched, switch_marker_observed = _wait_for_switch_and_pending(
            service,
            debug_log=debug_log,
            log_offset=switch_offset,
            expected_date_raw=initial_date,
            deadline=time.monotonic() + seed_timeout,
            session_done=session_done,
            session_state=session_state,
        )
        pending_before = _pending_identity(switched)
        if pending_before is None:
            raise AgentError("recipient switch lacks a full pending ID")

        noop_after_switch = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), SEED_NOOP_INBOX
        )
        poll_driver = DataModGameplayDriver(
            spec.profile_dir,
            request_timeout_seconds=seed_timeout,
            poll_interval_seconds=0.05,
        )
        poll_frames = [poll_driver.take_snapshot(), poll_driver.take_snapshot()]
        if (
            len({row.get("request_id") for row in poll_frames}) != 2
            or any(
                row.get("player_id") != RECIPIENT_CHARACTER_ID
                for row in poll_frames
            )
            or poll_frames[0].get("total_days")
            != poll_frames[1].get("total_days")
        ):
            raise AgentError("post-switch mod_bridge polls were not stable")
        stable = service.snapshot()
        if (
            _played_character_id(stable) != RECIPIENT_CHARACTER_ID
            or _snapshot_date(stable) != initial_date
            or _pending_identity(stable) != pending_before
        ):
            raise AgentError("pending identity drifted after recipient switch")

        clear_offset = owner_live._debug_log_offset(debug_log)
        clear_write = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), _clear_effect()
        )
        clear_deadline = time.monotonic() + seed_timeout
        while time.monotonic() < clear_deadline:
            clear_marker_observed = owner_live._debug_marker_observed(
                debug_log, CLEAR_MARKER, offset=clear_offset
            )
            if clear_marker_observed:
                break
            if session_done.is_set():
                raise AgentError(
                    str(
                        session_state.get("error")
                        or "seed session ended before guard clear"
                    )
                )
            time.sleep(0.05)
        if not clear_marker_observed:
            raise AgentError("mod_bridge did not acknowledge guard removal")
        clear_poll_frames = [
            poll_driver.take_snapshot(),
            poll_driver.take_snapshot(),
        ]
        if (
            len({row.get("request_id") for row in clear_poll_frames}) != 2
            or any(
                row.get("player_id") != RECIPIENT_CHARACTER_ID
                for row in clear_poll_frames
            )
            or clear_poll_frames[0].get("total_days")
            != clear_poll_frames[1].get("total_days")
        ):
            raise AgentError("post-clear mod_bridge polls were not stable")
        final_noop = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), SEED_NOOP_INBOX
        )
        if (
            owner_live._seed_inbox_path(spec).read_text(
                encoding="utf-8-sig"
            )
            != SEED_NOOP_INBOX
        ):
            raise AgentError("seed inbox did not remain at final no-op")

        stable = service.snapshot()
        if (
            _played_character_id(stable) != RECIPIENT_CHARACTER_ID
            or _snapshot_date(stable) != initial_date
            or _pending_identity(stable) != pending_before
        ):
            raise AgentError("pending identity changed before checkpoint save")
        save_result = service.save_checkpoint(
            expected_revision=_snapshot_revision(stable)
        )
        commands.append(SAVE_CHECKPOINT_STEP)
        checkpoint = owner_live._checkpoint_identity(
            owner_live._checkpoint_path(spec)
        )
        after_save = service.snapshot()
        if (
            _played_character_id(after_save) != RECIPIENT_CHARACTER_ID
            or _snapshot_date(after_save) != initial_date
            or _pending_identity(after_save) != pending_before
        ):
            raise AgentError("checkpoint save changed the pending request")
        mutation = _mutation_boundary_proof(commands, seed_stage=True)
        if mutation.get("ok") is not True:
            raise AgentError("seed command boundary differs")

        capabilities_after = driver.capabilities()
        same_process = _same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("seed fixture crossed bridge process")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        try:
            final_noop = owner_live._write_seed_inbox(
                owner_live._seed_inbox_path(spec), SEED_NOOP_INBOX
            )
        except BaseException as error:
            detail = f"{type(error).__name__}: {error}"
            primary_error = (
                detail
                if primary_error is None
                else f"{primary_error}; final inbox reset failed: {detail}"
            )
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
            or "seed managed cleanup was not proven"
        )
    session = _compact_session_report(session_state.get("report"))
    mutation = _mutation_boundary_proof(commands, seed_stage=True)
    pending = _pending_identity(stable)
    return {
        "stage": "seed-offer-switch-save",
        "session_started": session_started,
        "production_native_bridge": True,
        "production_profile": False,
        "seed_only_mod_bridge": True,
        "debug_mode": False,
        "ok": bool(
            primary_error is None
            and exact_binary
            and exact_binary.get("ok") is True
            and capability
            and capability.get("ok") is True
            and source_war
            and source_war.get("ok") is True
            and war_options_proof
            and war_options_proof.get("ok") is True
            and raw_offer
            and raw_offer.get("ok") is True
            and switch_marker_observed
            and clear_marker_observed
            and pending is not None
            and pending.get("sender_character_id") == SOURCE_CHARACTER_ID
            and checkpoint is not None
            and mutation.get("ok") is True
            and same_process
            and same_process.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
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
        "readiness": readiness,
        "exact_binary_proof": exact_binary,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "initial_snapshot": _compact_snapshot(initial),
        "source_war_proof": source_war,
        "war_options": war_options_result,
        "war_options_proof": war_options_proof,
        "raw_offer_proof": raw_offer,
        "switch_protocol": {
            "switch_marker": SWITCH_MARKER,
            "switch_marker_observed": switch_marker_observed,
            "clear_marker": CLEAR_MARKER,
            "clear_marker_observed": clear_marker_observed,
            "switch_write": switch_write,
            "noop_after_switch": noop_after_switch,
            "clear_write": clear_write,
            "final_noop": final_noop,
            "post_switch_frames": poll_frames,
            "post_clear_frames": clear_poll_frames,
        },
        "switched_snapshot": _compact_snapshot(switched),
        "stable_pre_save_snapshot": _compact_snapshot(stable),
        "post_save_snapshot": _compact_snapshot(after_save),
        "pending_identity": pending,
        "save_result": save_result,
        "checkpoint": checkpoint,
        "mutation_boundary": mutation,
        "session": session,
        "cleanup": cleanup,
        "error": primary_error,
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
    projection = _production_projection_proof(spec)
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

        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-pending-interaction-production-query",
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
        exact_binary = _exact_binary_proof(
            capabilities_before,
            executable_sha256=executable_sha256,
            dll_sha256=dll_sha256,
            expected_dll_sha256=expected_dll_sha256,
        )
        capability = _capability_proof(
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
            raise RuntimeError("adjacent pending-interaction queries failed")
        capabilities_after = driver.capabilities()
        same_process = _same_process_proof(
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
        "stage": "fresh-production-cold-query",
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


def _cross_stage_proof(
    seed_stage: object,
    production_stage: object,
    transfer: object,
) -> dict[str, object]:
    seed = seed_stage if isinstance(seed_stage, dict) else {}
    production = (
        production_stage if isinstance(production_stage, dict) else {}
    )
    sequence_value = production.get("sequence")
    sequence = sequence_value if isinstance(sequence_value, dict) else {}
    seed_pending_value = seed.get("pending_identity")
    seed_pending = (
        seed_pending_value if isinstance(seed_pending_value, dict) else {}
    )
    first_value = sequence.get("first_query")
    first = first_value if isinstance(first_value, dict) else {}
    frame_value = first.get("pending_character_interaction_context")
    frame = frame_value if isinstance(frame_value, dict) else {}
    seed_process_value = seed.get("same_process_proof")
    seed_process = (
        seed_process_value
        if isinstance(seed_process_value, dict)
        else {}
    )
    production_process_value = production.get("same_process_proof")
    production_process = (
        production_process_value
        if isinstance(production_process_value, dict)
        else {}
    )
    seed_pid = seed_process.get("bridge_pid")
    production_pid = production_process.get("bridge_pid")
    transfer_value = transfer if isinstance(transfer, dict) else {}
    seed_snapshot_value = seed.get("stable_pre_save_snapshot")
    seed_snapshot = (
        seed_snapshot_value if isinstance(seed_snapshot_value, dict) else {}
    )
    checks = {
        "both_stages_green": seed.get("ok") is True
        and production.get("ok") is True,
        "checkpoint_bytes_transferred": transfer_value.get("ok") is True,
        "distinct_positive_pids": isinstance(seed_pid, int)
        and not isinstance(seed_pid, bool)
        and seed_pid > 0
        and isinstance(production_pid, int)
        and not isinstance(production_pid, bool)
        and production_pid > 0
        and seed_pid != production_pid,
        "same_full_pending_id": seed_pending.get("instance_id")
        == sequence.get("pending_interaction_id")
        == frame.get("pending_interaction_id"),
        "same_sender": seed_pending.get("sender_character_id")
        == SOURCE_CHARACTER_ID
        and frame.get("roles", {}).get("actor_character_id")
        == SOURCE_CHARACTER_ID,
        "recipient_cold_loaded": frame.get("roles", {}).get(
            "recipient_character_id"
        )
        == RECIPIENT_CHARACTER_ID,
        "same_game_date": seed_snapshot.get("date_raw")
        == sequence.get("date_raw")
        == frame.get("date_raw"),
        "canonical_nonreligious_interaction": frame.get(
            "definition", {}
        ).get("canonical_key")
        == EXPECTED_INTERACTION_KEY,
        "no_default_reply": seed.get("mutation_boundary", {}).get(
            "checks", {}
        ).get("no_reply_action")
        is True
        and sequence.get("mutation_boundary", {}).get("checks", {}).get(
            "no_reply_action"
        )
        is True,
        "fresh_production_only": production.get(
            "production_projection_proof", {}
        ).get("ok")
        is True,
    }
    return {
        "seed_bridge_pid": seed_pid,
        "production_bridge_pid": production_pid,
        "pending_interaction_id": seed_pending.get("instance_id"),
        "date_raw": seed_snapshot.get("date_raw"),
        "checks": checks,
        "ok": all(checks.values()),
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
        source_save, source_identity = _resolve_source_save(
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
        seed_materialization["fixture_bridge"] = (
            owner_live._install_seed_bridge(seed_spec)
        )
        seed_stage = _run_seed_stage(
            spec=seed_spec,
            config=config,
            expected_dll_sha256=expected_dll_sha,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
        )
        if seed_stage.get("ok") is not True:
            raise AgentError(
                str(seed_stage.get("error") or "seed stage failed")
            )
        seed_pending_value = seed_stage.get("pending_identity")
        if not isinstance(seed_pending_value, dict):
            raise AgentError("seed stage lacks pending identity")
        pending_id = seed_pending_value.get("instance_id")
        if (
            isinstance(pending_id, bool)
            or not isinstance(pending_id, int)
            or pending_id <= 0
        ):
            raise AgentError("seed stage lacks a positive full pending ID")
        seed_snapshot_value = seed_stage.get("stable_pre_save_snapshot")
        seed_snapshot = (
            seed_snapshot_value
            if isinstance(seed_snapshot_value, dict)
            else {}
        )
        expected_date_raw = seed_snapshot.get("date_raw")
        if isinstance(expected_date_raw, bool) or not isinstance(
            expected_date_raw, int
        ):
            raise AgentError("seed stage lacks a signed game date")
        seed_checkpoint = owner_live._checkpoint_path(seed_spec)

        production_spec, production_materialization = (
            owner_live._prepare_stage(
                source_profile=source_profile,
                target_state=root / "fresh-production-cold-query",
                game_dir=game_dir,
                save_source=seed_checkpoint,
                save_name=CONTINUE_SAVE_NAME,
            )
        )
        transfer = _checkpoint_transfer_proof(
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
                    or "production query stage failed"
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
    if not source_unchanged and primary_error is None:
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
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            cleanup.get("reason") or "disposable root cleanup failed"
        )

    seed_report = _mapping(seed_stage)
    production_report = _mapping(production_stage)
    sequence = _mapping(production_report.get("sequence"))
    context_proof = _mapping(sequence.get("first_context_proof"))
    context_checks = _mapping(context_proof.get("checks"))
    sequence_checks = _mapping(sequence.get("checks"))
    cross_checks = _mapping(_mapping(cross_stage).get("checks"))
    seed_war_checks = _mapping(
        _mapping(seed_report.get("war_options_proof")).get("checks")
    )
    seed_switch = _mapping(seed_report.get("switch_protocol"))
    seed_initial = _mapping(seed_report.get("initial_snapshot"))
    seed_stable = _mapping(seed_report.get("stable_pre_save_snapshot"))
    seed_binary = _mapping(seed_report.get("exact_binary_proof"))
    production_binary = _mapping(
        production_report.get("exact_binary_proof")
    )
    readiness_gates = {
        "source_claim_cb_nonreligious_fixture": (
            seed_war_checks.get("ordinary_claim_cb") is True
        ),
        "production_native_white_peace_submitted": bool(
            _mapping(seed_report.get("raw_offer_proof")).get("ok") is True
        ),
        "same_day_recipient_switch": bool(
            seed_switch.get("switch_marker_observed") is True
            and seed_initial.get("date_raw") == seed_stable.get("date_raw")
        ),
        "stable_full_pending_id_across_cold_reload": (
            cross_checks.get("same_full_pending_id") is True
        ),
        "fresh_production_only_cold_reload": (
            cross_checks.get("fresh_production_only") is True
        ),
        "canonical_white_peace_definition": context_checks.get(
            "canonical_white_peace_definition"
        ) is True,
        "roles_routing_options_deadline_legalities": all(
            context_checks.get(key) is True
            for key in (
                "exact_roles",
                "zero_send_options_exact",
                "recipient_local_route",
                "fresh_deadline",
                "reply_legalities_available",
                "accept_and_reject_legal",
                "block_legal",
                "acknowledge_not_normal_reply",
                "not_auto_accept",
                "special_data_present",
                "structured_terms_explicit_unavailable",
            )
        ),
        "adjacent_same_revision_double_query": bool(
            sequence
            and all(
                sequence_checks.get(key) is True
                for key in (
                    "between_same_paused_binding",
                    "after_same_paused_binding",
                    "query_sequence_exact_successor",
                    "adjacent_context_frames_strictly_equal",
                    "only_query_sequence_changed",
                )
            )
        ),
        "no_default_accept_or_reject": (
            cross_checks.get("no_default_reply") is True
        ),
        "exact_exe_and_dll": bool(
            seed_binary.get("ok") is True
            and production_binary.get("ok") is True
        ),
        "immutable_source_bytes_and_metadata": source_unchanged,
        "managed_process_cleanup": bool(
            no_ck3_processes
            and all(
                isinstance(stage, dict)
                and _mapping(stage.get("cleanup")).get("ok") is True
                for stage in stages
            )
        ),
        "nonce_disposable_cleanup": cleanup.get("ok") is True,
    }
    ok = bool(primary_error is None and all(readiness_gates.values()))
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_pending_character_interaction_context_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "fixed_scenario": {
            "war_id": WAR_ID,
            "source_character_id": SOURCE_CHARACTER_ID,
            "recipient_character_id": RECIPIENT_CHARACTER_ID,
            "recipient_anchor_province_id": RECIPIENT_ANCHOR_PROVINCE_ID,
            "target_title_id": EXPECTED_TARGET_TITLE_ID,
            "casus_belli_key": EXPECTED_CASUS_BELLI_KEY,
            "interaction_key": EXPECTED_INTERACTION_KEY,
        },
        "policy": {
            "seed_stage_native_bridge_is_production": True,
            "seed_stage_mod_bridge_only_switches_player_and_clears_guard": True,
            "white_peace_action_is_raw_seed_only": True,
            "production_stage_is_read_only": True,
            "ordinary_pending_interaction_only": True,
            "auto_accept_notification_discovery_unclosed": False,
            "acknowledge_live_fixture_gap": (
                "production notification discovery/query and the strict ACK "
                "action are wired, but this ordinary read-only fixture does "
                "not exercise an auto-accept notification or its full-ID "
                "advancement postcondition"
            ),
            "forbidden_reply_steps": sorted(_FORBIDDEN_REPLY_STEPS),
            "forbidden_reply_steps_invoked": [],
            "religion_domain_deferred": True,
            "religion_specific_semantics_read": False,
            "semantic_decision_ready_expected": False,
            "structured_terms_remain_explicit_unavailable": True,
        },
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
    cross_stage = payload.get("cross_stage_proof")
    if not isinstance(cross_stage, dict):
        cross_stage = {}
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
                "pending_interaction_id": cross_stage.get(
                    "pending_interaction_id"
                ),
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
