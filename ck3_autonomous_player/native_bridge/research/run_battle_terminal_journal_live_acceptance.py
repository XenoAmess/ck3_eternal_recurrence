#!/usr/bin/env python3
"""Prove one normal CK3 battle terminal through the passive native journal.

The source active-battle save is immutable.  This harness copies it into a
fresh production profile, loads it without debug mode, observes the paused
combat, and advances at most one game day per command.  Once the old full
CombatID disappears, the dedicated terminal-transition query must join a
gap-free passive journal event to the old identity and to the current
subject/successor state.  CK3 lifetime, process-tree cleanup, clone cleanup,
and the source-save hash are all part of the acceptance result.

The only gameplay mutation allowed here is ``life-advance``.  The runner
never invokes a combat finalizer, contact resolver, battle-score writer, or
combat constructor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import time
from typing import Any, Callable
import uuid


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.battle_terminal_transition_contract import (  # noqa: E402
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
)
from xar_autoplayer.bridge.battle_transition_contract import (  # noqa: E402
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    ensure_state_path_safe,
    is_relative_to,
    make_spec,
    paths_overlap,
    prepare_profile,
    verify_profile,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
EXPECTED_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ONE_GAME_DAY_RAW = 24
CONTINUE_SAVE_NAME = "autosave.ck3"
DEFAULT_MAX_DAYS = 30
_CLONE_MARKER_NAME = ".xar-battle-terminal-journal-clone.json"
_PROFILE_ROOT_EXCLUDES = frozenset(
    {
        "crashes",
        "dumps",
        "exceptions",
        "logs",
        "mod",
        "mod-content",
        "save games",
        "last_save.ck3",
        "xar-autoplayer-environment.json",
    }
)
FORBIDDEN_NATIVE_CALLS = (
    "0x230A590",
    "0x222A5A0",
    "0x2208320",
    "0x220D2A0",
    "0x18721B0",
    "0x27FB7C0",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-state-dir", type=Path, required=True)
    parser.add_argument(
        "--state-dir",
        type=Path,
        help="new disposable root; omitted creates one under the temp dir",
    )
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--battle-save", type=Path, required=True)
    parser.add_argument("--expected-battle-save-sha256", required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--prior-combat-id", type=int, required=True)
    parser.add_argument("--subject-public-cunit-id", type=int, required=True)
    parser.add_argument("--max-days", type=int, default=DEFAULT_MAX_DAYS)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest().upper()


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _positive_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be positive")
    result = float(value)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _expected_sha256(value: object) -> str:
    normalized = str(value).strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", normalized):
        raise ValueError("expected battle save SHA-256 must be 64 hex digits")
    return normalized


def _target_state_dir(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-battle-terminal-journal-" + uuid.uuid4().hex
    )


def _copy_source_profile(source_profile: Path, target_profile: Path) -> None:
    for path in source_profile.rglob("*"):
        if path.is_symlink():
            raise AgentError(f"source profile contains a symlink: {path}")

    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == source_profile.resolve():
            return set(names) & _PROFILE_ROOT_EXCLUDES
        return set()

    shutil.copytree(
        source_profile,
        target_profile,
        copy_function=shutil.copy2,
        ignore=ignore,
    )


def _resolve_source_save(
    source_profile: Path, requested: Path, expected_sha256: str
) -> tuple[Path, dict[str, object]]:
    candidate = (
        requested.expanduser().resolve()
        if requested.is_absolute()
        else (source_profile / requested).resolve()
    )
    if not is_relative_to(candidate, source_profile.resolve()):
        raise AgentError("battle save escapes the source profile")
    if not candidate.is_file():
        raise AgentError(f"battle save is missing: {candidate}")
    actual = _sha256_file(candidate)
    if actual != expected_sha256:
        raise AgentError(
            f"battle save SHA-256 differs: {actual} != {expected_sha256}"
        )
    return candidate, {
        "path": str(candidate),
        "relative_path": candidate.relative_to(source_profile).as_posix(),
        "size": candidate.stat().st_size,
        "sha256": actual,
    }


def _prepare_clone(
    *,
    source_state_dir: Path,
    target_state_dir: Path,
    game_dir: Path,
    source_save: Path,
    clone_nonce: str,
) -> tuple[Any, dict[str, object]]:
    source_state = source_state_dir.resolve()
    source_profile = source_state / "profile"
    target = target_state_dir.resolve()
    if not source_profile.is_dir():
        raise AgentError(f"source profile is missing: {source_profile}")
    if target.exists():
        raise AgentError(f"disposable state already exists: {target}")
    ensure_state_path_safe(target)
    if paths_overlap(source_state, target):
        raise AgentError("source and disposable state directories overlap")

    target.mkdir(parents=True, exist_ok=False)
    marker = target / _CLONE_MARKER_NAME
    marker.write_text(
        json.dumps(
            {
                "kind": "xar_battle_terminal_journal_clone",
                "nonce": clone_nonce,
                "source_state_dir": str(source_state),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _copy_source_profile(source_profile, target / "profile")
    spec = make_spec(target, game_dir)
    manifest = prepare_profile(spec)
    save_dir = spec.profile_dir / "save games"
    save_dir.mkdir(parents=True, exist_ok=True)
    continue_save = save_dir / CONTINUE_SAVE_NAME
    root_last_save = spec.profile_dir / "last_save.ck3"
    shutil.copy2(source_save, continue_save)
    shutil.copy2(source_save, root_last_save)
    verified = verify_profile(spec)
    expected = _sha256_file(source_save)
    if not (
        _sha256_file(continue_save) == expected
        and _sha256_file(root_last_save) == expected
    ):
        raise AgentError("disposable active-battle save bytes differ")
    mod = manifest.get("mod")
    return spec, {
        "source_state_dir": str(source_state),
        "target_state_dir": str(target),
        "continue_save_name": CONTINUE_SAVE_NAME,
        "continue_save_path": str(continue_save),
        "continue_save_sha256": expected,
        "last_save_path": str(root_last_save),
        "last_save_sha256": expected,
        "excluded_profile_roots": sorted(_PROFILE_ROOT_EXCLUDES),
        "environment_sha256": verified.get("environment_sha256"),
        "production_tree_sha256": (
            mod.get("production_tree_sha256")
            if isinstance(mod, dict)
            else None
        ),
    }


def _snapshot_revision(snapshot: dict[str, object]) -> int:
    value = snapshot.get("revision")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError("paused snapshot lacks a public revision")
    return value


def _snapshot_date(snapshot: dict[str, object]) -> int:
    value = snapshot.get("date_raw")
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**63) <= value <= 2**63 - 1
    ):
        raise RuntimeError("paused snapshot lacks a signed date_raw")
    return value


def _assert_paused(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True:
        raise RuntimeError("terminal acceptance requires a paused snapshot")


def _old_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("old CombatID query returned a non-object")
    frame = result.get("battle_transition_snapshot")
    if not isinstance(frame, dict):
        raise RuntimeError("old CombatID query omitted its lifecycle frame")
    return frame


def _terminal_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("terminal query returned a non-object")
    frame = result.get("battle_terminal_transition")
    if not isinstance(frame, dict):
        raise RuntimeError("terminal query omitted battle_terminal_transition")
    return frame


def _ordered_prior_participants(frame: dict[str, object]) -> list[int]:
    attackers = frame.get("attacker_public_cunit_ids_in_stored_order")
    defenders = frame.get("defender_public_cunit_ids_in_stored_order")
    if not isinstance(attackers, list) or not isinstance(defenders, list):
        raise RuntimeError("initial active battle omitted ordered participants")
    values = [*attackers, *defenders]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
        for value in values
    ):
        raise RuntimeError("initial active battle has invalid participant IDs")
    if len(set(values)) != len(values):
        raise RuntimeError("initial active battle participant IDs overlap")
    return values


def _is_ordered_subsequence(values: list[int], expected_order: list[int]) -> bool:
    cursor = 0
    for value in values:
        try:
            cursor = expected_order.index(value, cursor) + 1
        except ValueError:
            return False
    return len(values) == len(set(values))


def _active_terminal_cursor_proof(
    frame: dict[str, object],
    *,
    prior_combat_id: int,
    subject_public_cunit_id: int,
) -> dict[str, object]:
    journal = frame.get("terminal_journal")
    prior = frame.get("prior")
    removal = frame.get("removal")
    journal = journal if isinstance(journal, dict) else {}
    prior = prior if isinstance(prior, dict) else {}
    removal = removal if isinstance(removal, dict) else {}
    latest = journal.get("latest_sequence")
    oldest = journal.get("oldest_available_sequence")
    checks = {
        "available": frame.get("status") == "available"
        and frame.get("battle_terminal_transition_ready") is True,
        "request_identities": frame.get("prior_combat_id")
        == prior_combat_id
        and frame.get("subject_public_cunit_id")
        == subject_public_cunit_id,
        "prior_identity": prior.get("combat_id") == prior_combat_id,
        "active_not_terminal": prior.get("terminal_kind")
        == "active_not_terminal",
        "journal_has_no_matching_event": journal.get("event_status")
        == "not_observed"
        and journal.get("event_sequence") is None
        and journal.get("requested_after_sequence") is None,
        "journal_bounds_typed": isinstance(latest, int)
        and not isinstance(latest, bool)
        and latest >= 0
        and isinstance(oldest, int)
        and not isinstance(oldest, bool)
        and oldest >= 0
        and ((latest == oldest == 0) or 1 <= oldest <= latest),
        "old_combat_resolves": removal.get(
            "prior_combat_strictly_resolves"
        )
        is True,
    }
    return {
        "cursor": (
            latest
            if checks["journal_bounds_typed"] and isinstance(latest, int)
            and latest > 0
            else None
        ),
        "latest_sequence": latest,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _normal_terminal_proof(
    frame: dict[str, object],
    *,
    prior_combat_id: int,
    subject_public_cunit_id: int,
    requested_after_sequence: int | None,
    initial_participants: list[int],
) -> dict[str, object]:
    journal = frame.get("terminal_journal")
    prior = frame.get("prior")
    removal = frame.get("removal")
    subject = frame.get("subject")
    successor = frame.get("successor")
    journal = journal if isinstance(journal, dict) else {}
    prior = prior if isinstance(prior, dict) else {}
    removal = removal if isinstance(removal, dict) else {}
    subject = subject if isinstance(subject, dict) else {}
    successor = successor if isinstance(successor, dict) else {}
    event_sequence = journal.get("event_sequence")
    oldest = journal.get("oldest_available_sequence")
    latest = journal.get("latest_sequence")
    prior_attackers = prior.get(
        "attacker_public_cunit_ids_in_stored_order"
    )
    prior_defenders = prior.get(
        "defender_public_cunit_ids_in_stored_order"
    )
    prior_flat = (
        [*prior_attackers, *prior_defenders]
        if isinstance(prior_attackers, list)
        and isinstance(prior_defenders, list)
        else []
    )
    overlap = successor.get(
        "participant_overlap_public_cunit_ids_in_prior_order"
    )
    matching = successor.get("matching_combat_ids_in_native_order")
    overlap = overlap if isinstance(overlap, list) else []
    matching = matching if isinstance(matching, list) else []
    selected = successor.get("selected_successor_combat_id")
    successor_state = successor.get("state")
    active_id = subject.get("active_combat_id")
    blocked = subject.get("blocked_by_active_combat")
    movement_state = subject.get("movement_or_retreat_state_raw")
    ai_membership_status = subject.get("ai_membership_status")
    membership_values = (
        subject.get("coordinator_id"),
        subject.get("unit_stack_stored_index"),
        subject.get("subunit_stored_index"),
    )
    membership_consistent = (
        ai_membership_status == "observed"
        and isinstance(membership_values[0], int)
        and not isinstance(membership_values[0], bool)
        and membership_values[0] > 0
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value >= 0
            for value in membership_values[1:]
        )
    ) or (
        ai_membership_status in {"none", "unavailable"}
        and all(value is None for value in membership_values)
    )

    successor_contract_consistent = False
    successor_observed = False
    if successor_state == "residual_new_combat":
        successor_contract_consistent = bool(
            isinstance(selected, int)
            and not isinstance(selected, bool)
            and selected > 0
            and selected != prior_combat_id
            and selected in matching
            and overlap
            and active_id == selected
            and blocked is True
        )
        successor_observed = successor_contract_consistent
    elif successor_state == "subject_missing":
        successor_contract_consistent = bool(
            subject.get("exists") is False
            and selected is None
            and active_id is None
            and ai_membership_status == "none"
        )
        successor_observed = successor_contract_consistent
    elif successor_state == "subject_retreating":
        successor_contract_consistent = bool(
            subject.get("exists") is True
            and selected is None
            and active_id is None
            and blocked is False
            and isinstance(movement_state, int)
            and not isinstance(movement_state, bool)
            and movement_state > 0
        )
        successor_observed = successor_contract_consistent
    elif successor_state == "subject_assignment_reopened":
        successor_contract_consistent = bool(
            subject.get("exists") is True
            and selected is None
            and active_id is None
            and blocked is False
            and ai_membership_status == "observed"
            and isinstance(subject.get("coordinator_id"), int)
            and subject.get("coordinator_id", 0) > 0
            and isinstance(subject.get("unit_stack_stored_index"), int)
            and subject.get("unit_stack_stored_index", -1) >= 0
            and isinstance(subject.get("subunit_stored_index"), int)
            and subject.get("subunit_stored_index", -1) >= 0
        )
        successor_observed = successor_contract_consistent
    elif successor_state == "no_successor":
        successor_contract_consistent = bool(
            subject.get("exists") is True
            and selected is None
            and active_id is None
            and blocked is not True
            and ai_membership_status == "none"
            and not matching
            and not overlap
        )
        successor_observed = successor_contract_consistent
    elif successor_state == "unavailable":
        successor_contract_consistent = bool(
            selected is None
            and not overlap
            and (
                ai_membership_status == "unavailable"
                or active_id is not None
                or bool(matching)
                or removal.get("prior_province_strictly_resolves")
                is not True
            )
        )

    cursor_floor = (
        requested_after_sequence
        if isinstance(requested_after_sequence, int)
        and not isinstance(requested_after_sequence, bool)
        else 0
    )
    warscore = prior.get("battle_warscore")
    checks = {
        "available": frame.get("status") == "available"
        and frame.get("battle_terminal_transition_ready") is True,
        "request_identities": frame.get("prior_combat_id")
        == prior_combat_id
        and frame.get("subject_public_cunit_id")
        == subject_public_cunit_id,
        "journal_cursor_bound": journal.get("requested_after_sequence")
        == requested_after_sequence,
        "journal_event_observed": journal.get("event_status") == "observed"
        and isinstance(event_sequence, int)
        and not isinstance(event_sequence, bool)
        and event_sequence > cursor_floor,
        "journal_event_in_retained_bounds": isinstance(oldest, int)
        and not isinstance(oldest, bool)
        and isinstance(latest, int)
        and not isinstance(latest, bool)
        and isinstance(event_sequence, int)
        and not isinstance(event_sequence, bool)
        and 1 <= oldest <= event_sequence <= latest,
        "normal_result_from_entry_argument": prior.get("combat_id")
        == prior_combat_id
        and prior.get("terminal_kind") == "normal_result"
        and prior.get("suppress_normal_result_envelopes") is False
        and prior.get("finalized_before") is False,
        "gap_free_warscore_discriminant": isinstance(warscore, dict)
        and warscore.get("status")
        in {"recorded", "not_recorded_by_native"},
        "old_combat_removed_globally": removal.get(
            "prior_combat_strictly_resolves"
        )
        is False,
        "old_combat_removed_from_prior_province": removal.get(
            "prior_province_strictly_resolves"
        )
        is True
        and removal.get("prior_province_contains_prior_combat_id") is False,
        "journal_prior_participants_match_initial": prior_flat
        == initial_participants,
        "subject_was_prior_participant": initial_participants.count(
            subject_public_cunit_id
        )
        == 1,
        "successor_ids_typed_unique": all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 1 <= value <= 2**31 - 1
            for value in matching
        )
        and len(set(matching)) == len(matching)
        and prior_combat_id not in matching,
        "successor_overlap_is_prior_ordered_subsequence": all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in overlap
        )
        and _is_ordered_subsequence(overlap, initial_participants),
        "subject_ai_membership_tristate_consistent": membership_consistent,
        "successor_state_contract_consistent": successor_contract_consistent,
        "successor_or_reentry_state_observed": successor_observed,
    }
    core_checks = {
        key: value
        for key, value in checks.items()
        if key != "successor_or_reentry_state_observed"
    }
    terminal_core_ok = all(core_checks.values())
    subject_reentry_ready = successor_observed
    return {
        "journal_event_sequence": event_sequence,
        "terminal_kind": prior.get("terminal_kind"),
        "battle_warscore": warscore,
        "successor_state": successor_state,
        "subject_ai_membership_status": ai_membership_status,
        "successor_matching_combat_ids": matching,
        "participant_overlap_public_cunit_ids_in_prior_order": overlap,
        "checks": checks,
        "terminal_core_ok": terminal_core_ok,
        "subject_reentry_ready": subject_reentry_ready,
        "core_ok": terminal_core_ok,
        "ok": terminal_core_ok and subject_reentry_ready,
    }


def _membership_only_terminal_unavailable(
    frame: dict[str, object], proof: dict[str, object]
) -> bool:
    removal = frame.get("removal")
    subject = frame.get("subject")
    successor = frame.get("successor")
    removal = removal if isinstance(removal, dict) else {}
    subject = subject if isinstance(subject, dict) else {}
    successor = successor if isinstance(successor, dict) else {}
    movement_state = subject.get("movement_or_retreat_state_raw")
    return bool(
        proof.get("terminal_core_ok") is True
        and proof.get("subject_reentry_ready") is False
        and proof.get("successor_state") == "unavailable"
        and proof.get("subject_ai_membership_status") == "unavailable"
        and subject.get("exists") is True
        and subject.get("active_combat_id") is None
        and subject.get("combat_backlink_id") is None
        and subject.get("blocked_by_active_combat") is False
        and isinstance(movement_state, int)
        and not isinstance(movement_state, bool)
        and movement_state <= 0
        and successor.get("matching_combat_ids_in_native_order") == []
        and successor.get("selected_successor_combat_id") is None
        and successor.get(
            "participant_overlap_public_cunit_ids_in_prior_order"
        )
        == []
        and removal.get("prior_province_strictly_resolves") is True
    )


def _corroborating_terminal_shared_checks(
    player_frame: dict[str, object],
    candidate_frame: dict[str, object],
    *,
    expected_revision: int,
    requested_after_sequence: int | None,
) -> dict[str, bool]:
    player_journal = player_frame.get("terminal_journal")
    candidate_journal = candidate_frame.get("terminal_journal")
    player_journal = player_journal if isinstance(player_journal, dict) else {}
    candidate_journal = (
        candidate_journal if isinstance(candidate_journal, dict) else {}
    )
    player_event_sequence = player_journal.get("event_sequence")
    return {
        "same_paused_snapshot_revision": (
            player_frame.get("snapshot_revision") == expected_revision
            and candidate_frame.get("snapshot_revision")
            == expected_revision
        ),
        "same_observed_date_raw": candidate_frame.get("observed_date_raw")
        == player_frame.get("observed_date_raw"),
        "same_requested_terminal_cursor": (
            player_journal.get("requested_after_sequence")
            == requested_after_sequence
            and candidate_journal.get("requested_after_sequence")
            == requested_after_sequence
        ),
        "same_terminal_event_sequence": (
            isinstance(player_event_sequence, int)
            and not isinstance(player_event_sequence, bool)
            and candidate_journal.get("event_sequence")
            == player_event_sequence
        ),
        "same_prior_terminal_facts": candidate_frame.get("prior")
        == player_frame.get("prior"),
        "same_removal_facts": candidate_frame.get("removal")
        == player_frame.get("removal"),
    }


def _compact_snapshot(snapshot: object) -> object:
    if not isinstance(snapshot, dict):
        return snapshot
    return {
        key: snapshot.get(key)
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "phase",
            "map_ready",
            "paused",
            "episode_character_id",
            "episode_run_id",
            "active_event",
        )
    }


def _run_terminal_loop(
    service: GameplayBridgeService,
    *,
    prior_combat_id: int,
    subject_public_cunit_id: int,
    max_days: int,
    wait_after_advance: Callable[[], dict[str, object]],
) -> dict[str, object]:
    initial_snapshot = service.snapshot()
    _assert_paused(initial_snapshot)
    initial_revision = _snapshot_revision(initial_snapshot)
    initial_old_result = service.query_battle_transition_v1(
        prior_combat_id,
        expected_revision=initial_revision,
    )
    initial_old_frame = _old_frame(initial_old_result)
    if not (
        initial_old_frame.get("status") == "available"
        and initial_old_frame.get("combat_id") == prior_combat_id
        and initial_old_frame.get("finalized") is False
    ):
        raise RuntimeError("source save does not contain the requested active combat")
    initial_participants = _ordered_prior_participants(initial_old_frame)
    if initial_participants.count(subject_public_cunit_id) != 1:
        raise RuntimeError("subject is not exactly one initial battle participant")

    initial_terminal_result = service.query_battle_terminal_transition_v1(
        prior_combat_id,
        subject_public_cunit_id,
        expected_revision=initial_revision,
        after_terminal_sequence=None,
    )
    initial_terminal_frame = _terminal_frame(initial_terminal_result)
    cursor_proof = _active_terminal_cursor_proof(
        initial_terminal_frame,
        prior_combat_id=prior_combat_id,
        subject_public_cunit_id=subject_public_cunit_id,
    )
    if cursor_proof.get("ok") is not True:
        subject_probes: dict[str, object] = {}
        for diagnostic_subject_id in [
            *(
                value
                for value in initial_participants
                if value != subject_public_cunit_id
            ),
            2**31 - 1,
        ]:
            try:
                subject_probes[str(diagnostic_subject_id)] = (
                    service.query_battle_terminal_transition_v1(
                        prior_combat_id,
                        diagnostic_subject_id,
                        expected_revision=initial_revision,
                        after_terminal_sequence=None,
                    )
                )
            except BaseException as error:
                subject_probes[str(diagnostic_subject_id)] = (
                    f"{type(error).__name__}: {error}"
                )
        diagnostic = json.dumps(
            {
                "proof": cursor_proof,
                "frame": initial_terminal_frame,
                "subject_probes": subject_probes,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        raise RuntimeError(
            "initial active terminal-journal frame failed: " + diagnostic
        )
    cursor = cursor_proof.get("cursor")
    if cursor is not None and (
        isinstance(cursor, bool) or not isinstance(cursor, int) or cursor <= 0
    ):
        raise RuntimeError("initial terminal journal cursor is invalid")

    days: list[dict[str, object]] = []
    terminal_result: dict[str, object] | None = None
    terminal_frame: dict[str, object] | None = None
    terminal_proof: dict[str, object] | None = None
    current_snapshot = initial_snapshot
    for day_index in range(1, max_days + 1):
        before = current_snapshot
        _assert_paused(before)
        before_revision = _snapshot_revision(before)
        before_date = _snapshot_date(before)
        advance = service.execute_step(
            "life-advance", expected_revision=before_revision
        )
        wait_after_advance()
        after = service.snapshot()
        _assert_paused(after)
        after_date = _snapshot_date(after)
        if after_date - before_date != ONE_GAME_DAY_RAW:
            raise RuntimeError(
                "one life-advance did not advance exactly one CK3 day"
            )
        after_revision = _snapshot_revision(after)
        old_result = service.query_battle_transition_v1(
            prior_combat_id,
            expected_revision=after_revision,
        )
        old_frame = _old_frame(old_result)
        status = old_frame.get("status")
        first = service.query_battle_terminal_transition_v1(
            prior_combat_id,
            subject_public_cunit_id,
            expected_revision=after_revision,
            after_terminal_sequence=cursor,
        )
        first_frame = _terminal_frame(first)
        terminal_kind_value = first_frame.get("prior")
        terminal_kind = (
            terminal_kind_value.get("terminal_kind")
            if isinstance(terminal_kind_value, dict)
            else None
        )
        row: dict[str, object] = {
            "day_index": day_index,
            "before_snapshot": _compact_snapshot(before),
            "after_snapshot": _compact_snapshot(after),
            "date_delta_raw": after_date - before_date,
            "advance": advance,
            "old_combat_query": old_result,
            "old_combat_status": status,
            "terminal_query": first,
            "terminal_kind": terminal_kind,
        }
        days.append(row)
        current_snapshot = after
        if status == "available":
            if not (
                old_frame.get("combat_id") == prior_combat_id
                and old_frame.get("finalized") is False
                and _ordered_prior_participants(old_frame)
                == initial_participants
                and terminal_kind == "active_not_terminal"
                and isinstance(first_frame.get("terminal_journal"), dict)
                and first_frame["terminal_journal"].get("event_status")
                == "not_observed"
                and isinstance(first_frame.get("removal"), dict)
                and first_frame["removal"].get(
                    "prior_combat_strictly_resolves"
                )
                is True
            ):
                raise RuntimeError(
                    "continuing old combat and terminal journal disagree"
                )
            continue
        if status != "combat_not_found":
            raise RuntimeError(
                f"old CombatID query became non-terminal status {status!r}"
            )

        second = service.query_battle_terminal_transition_v1(
            prior_combat_id,
            subject_public_cunit_id,
            expected_revision=after_revision,
            after_terminal_sequence=cursor,
        )
        first_frame = _terminal_frame(first)
        second_frame = _terminal_frame(second)
        if first_frame != second_frame:
            raise RuntimeError("immediate terminal-transition frames differ")
        first_sequence = first.get("query_sequence")
        second_sequence = second.get("query_sequence")
        if not (
            isinstance(first_sequence, int)
            and not isinstance(first_sequence, bool)
            and isinstance(second_sequence, int)
            and not isinstance(second_sequence, bool)
            and second_sequence > first_sequence
        ):
            raise RuntimeError("terminal query sequence did not increase")
        player_terminal_proof = _normal_terminal_proof(
            first_frame,
            prior_combat_id=prior_combat_id,
            subject_public_cunit_id=subject_public_cunit_id,
            requested_after_sequence=cursor,
            initial_participants=initial_participants,
        )
        if player_terminal_proof.get("terminal_core_ok") is not True:
            raise RuntimeError("normal terminal core postconditions failed")

        player_reentry_ready = (
            player_terminal_proof.get("subject_reentry_ready") is True
        )
        corroborating_subjects: list[dict[str, object]] = []
        corroborating_subject_ids: list[int] = []
        if not player_reentry_ready:
            if not _membership_only_terminal_unavailable(
                first_frame, player_terminal_proof
            ):
                raise RuntimeError(
                    "player strong-reentry proof failed for a reason other "
                    "than unavailable AI membership"
                )
            for candidate_subject_id in initial_participants:
                if candidate_subject_id == subject_public_cunit_id:
                    continue
                try:
                    candidate_result = (
                        service.query_battle_terminal_transition_v1(
                            prior_combat_id,
                            candidate_subject_id,
                            expected_revision=after_revision,
                            after_terminal_sequence=cursor,
                        )
                    )
                    candidate_frame = _terminal_frame(candidate_result)
                    candidate_proof = _normal_terminal_proof(
                        candidate_frame,
                        prior_combat_id=prior_combat_id,
                        subject_public_cunit_id=candidate_subject_id,
                        requested_after_sequence=cursor,
                        initial_participants=initial_participants,
                    )
                    shared_checks = _corroborating_terminal_shared_checks(
                        first_frame,
                        candidate_frame,
                        expected_revision=after_revision,
                        requested_after_sequence=cursor,
                    )
                    membership_observed = (
                        candidate_proof.get(
                            "subject_ai_membership_status"
                        )
                        == "observed"
                    )
                    strong_reentry_ready = (
                        candidate_proof.get("terminal_core_ok") is True
                        and candidate_proof.get("subject_reentry_ready")
                        is True
                    )
                    qualifies = bool(
                        all(shared_checks.values())
                        and membership_observed
                        and strong_reentry_ready
                    )
                    if qualifies:
                        corroborating_subject_ids.append(
                            candidate_subject_id
                        )
                    corroborating_subjects.append(
                        {
                            "subject_public_cunit_id": candidate_subject_id,
                            "query": candidate_result,
                            "frame_sha256": _canonical_sha256(
                                candidate_frame
                            ),
                            "shared_terminal_checks": shared_checks,
                            "membership_observed": membership_observed,
                            "strong_reentry_ready": strong_reentry_ready,
                            "qualifies": qualifies,
                            "terminal_proof": candidate_proof,
                        }
                    )
                except Exception as error:
                    corroborating_subjects.append(
                        {
                            "subject_public_cunit_id": candidate_subject_id,
                            "query_error": (
                                f"{type(error).__name__}: {error}"
                            ),
                            "qualifies": False,
                        }
                    )

            if any(
                "query_error" in candidate
                for candidate in corroborating_subjects
            ):
                raise RuntimeError(
                    "one or more corroborating terminal queries failed"
                )
            if any(
                not all(shared_checks.values())
                for candidate in corroborating_subjects
                for shared_checks in [
                    candidate.get("shared_terminal_checks")
                ]
                if isinstance(shared_checks, dict)
            ):
                raise RuntimeError(
                    "corroborating terminal query crossed revision or "
                    "terminal event facts"
                )
            if not corroborating_subject_ids:
                raise RuntimeError(
                    "no corroborating prior participant established strong "
                    "successor or reentry state"
                )

        corroborating_subject_reentry_ready = bool(
            corroborating_subject_ids
        )
        overall_checks = {
            "player_terminal_core_valid": (
                player_terminal_proof.get("terminal_core_ok") is True
            ),
            "player_or_corroborating_reentry_ready": (
                player_reentry_ready
                or corroborating_subject_reentry_ready
            ),
        }
        terminal_proof = {
            **player_terminal_proof,
            "player_terminal_core_ok": overall_checks[
                "player_terminal_core_valid"
            ],
            "player_reentry_ready": player_reentry_ready,
            "corroboration_attempted": not player_reentry_ready,
            "corroborating_subject_reentry_ready": (
                corroborating_subject_reentry_ready
            ),
            "corroborating_subject_ids": corroborating_subject_ids,
            "corroborating_subjects": corroborating_subjects,
            "overall_checks": overall_checks,
            "ok": all(overall_checks.values()),
        }
        terminal_result = {
            "first": first,
            "second": second,
            "immediate_frame_equal": True,
            "query_sequence_increased": True,
            "frame_sha256": _canonical_sha256(first_frame),
            "corroborating_subject_queries": corroborating_subjects,
        }
        terminal_frame = first_frame
        row["terminal_query_pair"] = terminal_result
        break

    if terminal_frame is None or terminal_proof is None:
        raise RuntimeError(
            f"normal battle terminal was not observed within {max_days} days"
        )
    ending_snapshot = service.snapshot()
    _assert_paused(ending_snapshot)
    if not (
        ending_snapshot.get("snapshot_id")
        == current_snapshot.get("snapshot_id")
        and ending_snapshot.get("revision") == current_snapshot.get("revision")
        and ending_snapshot.get("native_revision")
        == current_snapshot.get("native_revision")
        and ending_snapshot.get("date_raw") == current_snapshot.get("date_raw")
    ):
        raise RuntimeError("terminal proof crossed a paused snapshot revision")
    return {
        "prior_combat_id": prior_combat_id,
        "subject_public_cunit_id": subject_public_cunit_id,
        "initial_snapshot": _compact_snapshot(initial_snapshot),
        "initial_old_combat_query": initial_old_result,
        "initial_terminal_query": initial_terminal_result,
        "initial_participants_in_side_order": initial_participants,
        "initial_cursor_proof": cursor_proof,
        "after_terminal_sequence": cursor,
        "days": days,
        "days_advanced": len(days),
        "terminal_query_pair": terminal_result,
        "terminal_frame": terminal_frame,
        "terminal_proof": terminal_proof,
        "ending_snapshot": _compact_snapshot(ending_snapshot),
        "assertions": {
            "started_active_and_paused": True,
            "every_advance_exactly_one_day": all(
                row.get("date_delta_raw") == ONE_GAME_DAY_RAW
                for row in days
            ),
            "normal_terminal_observed": terminal_proof.get("ok") is True,
            "player_terminal_core_valid": terminal_proof.get(
                "player_terminal_core_ok"
            )
            is True,
            "player_reentry_ready": terminal_proof.get(
                "player_reentry_ready"
            )
            is True,
            "corroborating_subject_reentry_ready": terminal_proof.get(
                "corroborating_subject_reentry_ready"
            )
            is True,
            "terminal_within_bound": 1 <= len(days) <= max_days,
            "only_life_advance_mutated_gameplay": True,
        },
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    if not isinstance(capabilities, dict):
        return {}
    value = capabilities.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _exact_build_proof(
    capabilities: object, managed_executable_sha256: str
) -> dict[str, object]:
    diagnostics = _diagnostics(capabilities)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    observed_sha = hello.get(
        "expected_ck3_sha256", hello.get("executable_sha256")
    )
    observed_version = hello.get(
        "expected_ck3_version", hello.get("game_version")
    )
    checks = {
        "game_version": observed_version == EXPECTED_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": isinstance(observed_sha, str)
        and observed_sha.upper() == EXPECTED_EXECUTABLE_SHA256,
        "managed_executable_sha256": managed_executable_sha256.upper()
        == EXPECTED_EXECUTABLE_SHA256,
    }
    return {
        "expected_game_version": EXPECTED_GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _capability_proof(capabilities: object) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    advertised_value = raw.get("bridge_capabilities")
    advertised = advertised_value if isinstance(advertised_value, list) else []
    diagnostics = _diagnostics(raw)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_value = hello.get("capabilities")
    hello_capabilities = hello_value if isinstance(hello_value, list) else []
    required = (
        QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
        QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    )
    checks = {
        "bridge_capabilities": all(value in advertised for value in required),
        "hello_capabilities": all(
            value in hello_capabilities for value in required
        ),
        "driver_terminal_query_supported": raw.get(
            "battle_terminal_transition_v1_query_supported"
        )
        is True,
    }
    return {
        "required": list(required),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _same_process_proof(
    before_capabilities: object, after_capabilities: object
) -> dict[str, object]:
    before = _diagnostics(before_capabilities)
    after = _diagnostics(after_capabilities)
    before_pid = before.get("bridge_pid")
    after_pid = after.get("bridge_pid")
    before_generation = before.get("connection_generation")
    after_generation = after.get("connection_generation")
    checks = {
        "same_positive_bridge_pid": isinstance(before_pid, int)
        and not isinstance(before_pid, bool)
        and before_pid > 0
        and after_pid == before_pid,
        "same_positive_connection_generation": isinstance(
            before_generation, int
        )
        and not isinstance(before_generation, bool)
        and before_generation > 0
        and after_generation == before_generation,
        "connection_remained_live": before.get("connected") is True
        and after.get("connected") is True,
    }
    return {
        "before_bridge_pid": before_pid,
        "after_bridge_pid": after_pid,
        "before_connection_generation": before_generation,
        "after_connection_generation": after_generation,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _runner_boundary_proof() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    loop_start = source.index("\ndef _run_terminal_loop(") + 1
    loop_end = source.index("\ndef _diagnostics(", loop_start)
    loop_source = source[loop_start:loop_end]
    forbidden_service_tokens = (
        "preview_active_combat_retreat",
        "order_active_combat_retreat",
        "save_checkpoint",
        "query_battle_reinforcement_assignment",
    )
    checks = {
        "only_one_execute_step_literal": loop_source.count(
            "service.execute_step("
        )
        == 1,
        "only_life_advance_literal": '"life-advance"' in loop_source,
        "no_forbidden_service_surface": not any(
            value in loop_source for value in forbidden_service_tokens
        ),
        "old_and_terminal_queries_are_distinct": (
            "service.query_battle_transition_v1(" in loop_source
            and "service.query_battle_terminal_transition_v1(" in loop_source
        ),
    }
    return {
        "mode": "production_non_debug_managed_one_day_steps",
        "allowed_mutation_steps": ["life-advance"],
        "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        "forbidden_native_calls_invoked": [],
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_live_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    prior_combat_id: int,
    subject_public_cunit_id: int,
    max_days: int,
    timeout: float,
    readiness_timeout: float,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    readiness: dict[str, object] | None = None
    exact_build: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    loop: dict[str, object] | None = None
    primary_error: str | None = None
    executable_sha256: str | None = None

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
        executable_sha256 = _sha256_file(spec.game_exe)
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-battle-terminal-journal-live-session",
            daemon=False,
        )
        session_thread.start()
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
        exact_build = _exact_build_proof(
            capabilities_before, executable_sha256
        )
        capability = _capability_proof(capabilities_before)
        if exact_build.get("ok") is not True:
            raise RuntimeError("exact-build proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("terminal journal query capability is unavailable")

        def wait_after_advance() -> dict[str, object]:
            return _wait_for_readiness(
                driver,
                session_done=session_done,
                session_state=session_state,
                timeout_seconds=readiness_timeout,
                stable_seconds=0.0,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                allow_terminal=False,
            )

        loop = _run_terminal_loop(
            service,
            prior_combat_id=prior_combat_id,
            subject_public_cunit_id=subject_public_cunit_id,
            max_days=max_days,
            wait_after_advance=wait_after_advance,
        )
        capabilities_after = driver.capabilities()
        same_process = _same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError(
                "active and terminal observations crossed bridge process "
                "identity"
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None and session_started:
            session_thread.join()
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
    boundary = _runner_boundary_proof()
    assertions = loop.get("assertions") if isinstance(loop, dict) else {}
    loop_ok = bool(
        isinstance(assertions, dict)
        and assertions.get("started_active_and_paused") is True
        and assertions.get("every_advance_exactly_one_day") is True
        and assertions.get("normal_terminal_observed") is True
        and assertions.get("terminal_within_bound") is True
        and assertions.get("only_life_advance_mutated_gameplay") is True
    )
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "managed cleanup was not proven"
        )
    return {
        "ok": bool(
            primary_error is None
            and exact_build
            and exact_build.get("ok") is True
            and capability
            and capability.get("ok") is True
            and same_process
            and same_process.get("ok") is True
            and loop_ok
            and boundary.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "session_started": session_started,
        "readiness": readiness,
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": _sha256_file(config.dll_path),
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": _sha256_file(config.injector_path),
        },
        "exact_build_proof": exact_build,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "terminal_loop": loop,
        "runner_boundary_proof": boundary,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _cleanup_clone(
    target_state_dir: Path,
    *,
    clone_nonce: str,
    retain_state: bool,
    session_started: bool,
    session_cleanup_proven: bool,
) -> dict[str, object]:
    target = target_state_dir.resolve()
    if retain_state:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "--retain-state prevents full cleanup qualification",
        }
    if session_started and not session_cleanup_proven:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": (
                "managed process cleanup was not proven; disposable state "
                "was retained"
            ),
        }
    marker = target / _CLONE_MARKER_NAME
    try:
        marker_payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            marker_payload.get("kind")
            == "xar_battle_terminal_journal_clone"
            and marker_payload.get("nonce") == clone_nonce
        ):
            raise AgentError("disposable state marker differs")
        ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "path": str(target),
            "ok": removed,
            "reason": None if removed else "disposable state still exists",
        }
    except BaseException as error:
        return {
            "attempted": True,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": f"{type(error).__name__}: {error}",
        }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    started_wall = utc_now()
    prior_combat_id = _positive_int32(
        args.prior_combat_id, "prior_combat_id"
    )
    subject_public_cunit_id = _positive_int32(
        args.subject_public_cunit_id, "subject_public_cunit_id"
    )
    max_days = _positive_int32(args.max_days, "max_days")
    timeout = _positive_number(args.timeout, "timeout")
    readiness_timeout = _positive_number(
        args.readiness_timeout, "readiness_timeout"
    )
    expected_save_sha256 = _expected_sha256(
        args.expected_battle_save_sha256
    )
    source_state = args.source_state_dir.expanduser().resolve()
    target_state = _target_state_dir(args.state_dir)
    output = args.output.expanduser().resolve()
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    if is_relative_to(output, target_state):
        raise AgentError("artifact output must be outside disposable state")
    if is_relative_to(output, source_state):
        raise AgentError("artifact output must be outside immutable source state")
    if target_state.exists():
        raise AgentError(f"disposable state already exists: {target_state}")

    clone_nonce = uuid.uuid4().hex
    source_save: Path | None = None
    source_save_identity: dict[str, object] | None = None
    source_before: str | None = None
    clone: dict[str, object] | None = None
    live: dict[str, object] | None = None
    primary_error: str | None = None
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.expanduser().resolve(),
        injector_path=args.bridge_injector.expanduser().resolve(),
    )
    try:
        source_save, source_save_identity = _resolve_source_save(
            source_state / "profile",
            args.battle_save,
            expected_save_sha256,
        )
        source_before = _sha256_file(source_save)
        spec, clone = _prepare_clone(
            source_state_dir=source_state,
            target_state_dir=target_state,
            game_dir=args.game_dir.expanduser().resolve(),
            source_save=source_save,
            clone_nonce=clone_nonce,
        )
        live = _run_live_session(
            spec=spec,
            config=config,
            prior_combat_id=prior_combat_id,
            subject_public_cunit_id=subject_public_cunit_id,
            max_days=max_days,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if live.get("ok") is not True:
            primary_error = str(
                live.get("error") or "terminal live session did not qualify"
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"

    source_after = (
        _sha256_file(source_save)
        if source_save is not None and source_save.is_file()
        else None
    )
    source_unchanged = bool(
        source_before is not None and source_before == source_after
    )
    session_started = bool(
        isinstance(live, dict) and live.get("session_started") is True
    )
    session_cleanup_proven = bool(
        isinstance(live, dict)
        and isinstance(live.get("cleanup"), dict)
        and live["cleanup"].get("ok") is True
    )
    clone_cleanup = (
        _cleanup_clone(
            target_state,
            clone_nonce=clone_nonce,
            retain_state=bool(args.retain_state),
            session_started=session_started,
            session_cleanup_proven=session_cleanup_proven,
        )
        if target_state.exists()
        else {
            "attempted": False,
            "removed": True,
            "path": str(target_state),
            "ok": True,
            "reason": "disposable state was not materialized",
        }
    )
    if not source_unchanged and primary_error is None:
        primary_error = "source active-battle save changed during live run"
    if clone_cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            clone_cleanup.get("reason") or "clone cleanup was not proven"
        )
    ok = bool(
        primary_error is None
        and isinstance(live, dict)
        and live.get("ok") is True
        and source_unchanged
        and clone_cleanup.get("ok") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_battle_terminal_journal_v1_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "bounds": {
            "max_days": max_days,
            "one_game_day_raw": ONE_GAME_DAY_RAW,
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
        },
        "policy": {
            "production_non_debug": True,
            "load_kind": "continue_last_save",
            "continue_save_name": CONTINUE_SAVE_NAME,
            "only_gameplay_mutation": "life-advance, one day per command",
            "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        },
        "source_save": source_save_identity,
        "source_save_invariant": {
            "before_sha256": source_before,
            "after_sha256": source_after,
            "unchanged": source_unchanged,
        },
        "clone": clone,
        "live": live,
        "clone_cleanup": clone_cleanup,
        "readiness_gates": {
            "normal_terminal_live_ready": bool(
                live
                and live.get("ok") is True
                and isinstance(live.get("terminal_loop"), dict)
                and isinstance(live["terminal_loop"].get("terminal_proof"), dict)
                and live["terminal_loop"]["terminal_proof"].get("ok") is True
            ),
            "source_save_unchanged": source_unchanged,
            "managed_cleanup_ready": session_cleanup_proven,
            "disposable_state_cleanup_ready": clone_cleanup.get("ok") is True,
        },
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
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
                "readiness_gates": payload.get("readiness_gates"),
                "cleanup": payload.get("clone_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
