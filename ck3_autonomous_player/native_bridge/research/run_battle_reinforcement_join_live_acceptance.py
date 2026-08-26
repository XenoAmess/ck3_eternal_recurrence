#!/usr/bin/env python3
"""Prove native AI reinforcement assignment and an actual combat join.

This managed production runner clones one frozen checkpoint, clears the
player army's stale route with the ordinary preview/move commands, and then
lets CK3 advance exactly one day per command.  Every paused day queries the
requester and helper in their native parent order.  The proof requires a real
help override with an aligned native ETA followed by a same-CombatID unique
tail append.  It never calls contact, combat join/finalizer, or constructor
helpers directly.
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

from xar_autoplayer.bridge.battle_reinforcement_assignment_contract import (  # noqa: E402
    QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
)
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
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    MOVE_ARMY_CAPABILITY,
    PREVIEW_MOVE_ARMY_CAPABILITY,
)
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
EXPECTED_SOURCE_SAVE_SHA256 = (
    "5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F"
)
DEFAULT_SOURCE_STATE_DIR = Path(
    r"C:\Users\xenoa\AppData\Local\XarAutoplayer"
)
DEFAULT_BATTLE_SAVE = Path(
    r"save games\xar_checkpoint_pre_white_peace_53175816.ck3"
)
CONTINUE_SAVE_NAME = "autosave.ck3"
ONE_GAME_DAY_RAW = 24
PLAYER_CUNIT_ID = 83_886_341
REQUESTER_CUNIT_ID = 357
HELPER_CUNIT_ID = 33_554_657
TARGET_PROVINCE_ID = 2596
EXPECTED_PLAYER_ROUTE = [2595, 2603, 2604]
EXPECTED_REQUESTER_ROUTE = [2582, 2587, 2597, 2596]
EXPECTED_HELPER_ROUTE = [2581]
_ASSIGNED_ARCHIVE_NAME = "xar_reinforcement_assigned.ck3"
_JOINED_ARCHIVE_NAME = "xar_reinforcement_joined.ck3"
_CLONE_MARKER_NAME = ".xar-battle-reinforcement-join-clone.json"
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
    "0x1872BF0",
    "0x1848310",
    "0x1848570",
    "0x18721B0",
    "0x186B190",
    "0x973E00",
    "0x2208320",
    "0x23040A0",
    "0x23043F0",
    "0x23044F0",
    "0x23C9100",
    "0x23CB840",
    "0x2305580",
    "0x230A590",
    "0x27FB7C0",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-state-dir", type=Path, default=DEFAULT_SOURCE_STATE_DIR
    )
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--battle-save", type=Path, default=DEFAULT_BATTLE_SAVE)
    parser.add_argument(
        "--expected-battle-save-sha256",
        default=EXPECTED_SOURCE_SAVE_SHA256,
    )
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--max-contact-days", type=int, default=20)
    parser.add_argument("--max-assignment-days", type=int, default=10)
    parser.add_argument("--max-eta-days", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=1200.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--route-clear-timeout", type=float, default=10.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: object) -> str:
    result = str(value).strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", result):
        raise ValueError("expected save SHA-256 must be 64 hex digits")
    return result


def _positive_int(value: object, name: str) -> int:
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


def _target_state_dir(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-battle-reinforcement-join-" + uuid.uuid4().hex
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
        raise AgentError("battle save escapes the immutable source profile")
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
                "kind": "xar_battle_reinforcement_join_clone",
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
    last_save = spec.profile_dir / "last_save.ck3"
    shutil.copy2(source_save, continue_save)
    shutil.copy2(source_save, last_save)
    verified = verify_profile(spec)
    expected = _sha256_file(source_save)
    if not (
        _sha256_file(continue_save) == expected
        and _sha256_file(last_save) == expected
    ):
        raise AgentError("disposable checkpoint bytes differ from source")
    mod = manifest.get("mod")
    return spec, {
        "source_state_dir": str(source_state),
        "target_state_dir": str(target),
        "continue_save_name": CONTINUE_SAVE_NAME,
        "continue_save_path": str(continue_save),
        "continue_save_sha256": expected,
        "last_save_path": str(last_save),
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
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("paused snapshot lacks date_raw")
    return value


def _assert_paused(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True:
        raise RuntimeError("reinforcement join acceptance requires pause")


def _same_paused_binding(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return bool(
        before.get("paused") is True
        and after.get("paused") is True
        and all(
            before.get(key) == after.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "episode_run_id",
            )
        )
    )


def _subject_observations(
    snapshot: dict[str, object], public_cunit_id: int
) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []

    def collect(value: object, source: str, war_id: object = None) -> None:
        for row in value if isinstance(value, list) else []:
            if isinstance(row, dict) and row.get("army_id") == public_cunit_id:
                observations.append(
                    {"source": source, "war_id": war_id, "army": dict(row)}
                )

    collect(snapshot.get("player_armies"), "player_armies")
    wars = snapshot.get("active_wars")
    for index, war in enumerate(wars if isinstance(wars, list) else []):
        if not isinstance(war, dict):
            continue
        war_id = war.get("war_id")
        collect(war.get("allied_armies"), f"active_wars[{index}].allied", war_id)
        collect(war.get("enemy_armies"), f"active_wars[{index}].enemy", war_id)
    return observations


def _army_signature(army: dict[str, object]) -> tuple[object, ...]:
    route = army.get("route_province_ids")
    return (
        army.get("army_id"),
        army.get("owner_character_id"),
        army.get("current_province_id"),
        army.get("move_target_province_id"),
        army.get("move_target_observable"),
        tuple(route) if isinstance(route, list) else None,
        army.get("in_combat"),
        army.get("retreating"),
        army.get("army_state_code"),
    )


def _subject_army(
    snapshot: dict[str, object], public_cunit_id: int
) -> dict[str, object]:
    observations = _subject_observations(snapshot, public_cunit_id)
    armies = [
        row["army"]
        for row in observations
        if isinstance(row.get("army"), dict)
    ]
    signatures = [_army_signature(army) for army in armies]
    if not armies or len(set(signatures)) != 1:
        raise RuntimeError(
            f"CUnit {public_cunit_id} semantic observations disagree"
        )
    return dict(armies[0])


def _initial_geometry_proof(snapshot: dict[str, object]) -> dict[str, object]:
    _assert_paused(snapshot)
    expected = (
        (PLAYER_CUNIT_ID, TARGET_PROVINCE_ID, EXPECTED_PLAYER_ROUTE),
        (REQUESTER_CUNIT_ID, 2564, EXPECTED_REQUESTER_ROUTE),
        (HELPER_CUNIT_ID, 2564, EXPECTED_HELPER_ROUTE),
    )
    observations: dict[str, object] = {}
    checks: dict[str, bool] = {}
    for public_id, province_id, route in expected:
        army = _subject_army(snapshot, public_id)
        observations[str(public_id)] = army
        checks[f"cunit_{public_id}_current_province"] = (
            army.get("current_province_id") == province_id
        )
        checks[f"cunit_{public_id}_route"] = (
            army.get("route_province_ids") == route
            and army.get("move_target_province_id") == route[-1]
            and army.get("move_target_observable") is True
        )
        checks[f"cunit_{public_id}_not_in_combat"] = (
            army.get("in_combat") is False
        )
    checks["player_controllable"] = (
        observations[str(PLAYER_CUNIT_ID)].get("controllable") is True
    )
    return {"observations": observations, "checks": checks, "ok": all(checks.values())}


def _route_clear_proof(
    before: dict[str, object],
    preview: object,
    move: object,
    after: dict[str, object],
) -> dict[str, object]:
    before_army = _subject_army(before, PLAYER_CUNIT_ID)
    after_army = _subject_army(after, PLAYER_CUNIT_ID)
    preview_row = (
        preview.get("route_preview") if isinstance(preview, dict) else None
    )
    preview_row = preview_row if isinstance(preview_row, dict) else {}
    preview_route = preview_row.get("route_province_ids")
    normalized_preview = list(preview_route) if isinstance(preview_route, list) else []
    if normalized_preview and normalized_preview[0] == TARGET_PROVINCE_ID:
        normalized_preview = normalized_preview[1:]
    action = move.get("war_action") if isinstance(move, dict) else None
    action = action if isinstance(action, dict) else {}
    checks = {
        "before_has_expected_stale_route": before_army.get("route_province_ids")
        == EXPECTED_PLAYER_ROUTE,
        "preview_available": preview_row.get("status") == "available",
        "preview_identity": preview_row.get("army_id") == PLAYER_CUNIT_ID
        and preview_row.get("origin_province_id") == TARGET_PROVINCE_ID
        and preview_row.get("target_province_id") == TARGET_PROVINCE_ID,
        "preview_current_target_is_empty_route": isinstance(preview_route, list)
        and not normalized_preview,
        "move_command_accepted": isinstance(move, dict)
        and move.get("accepted") is True
        and action.get("army_id") == PLAYER_CUNIT_ID
        and action.get("target_province_id") == TARGET_PROVINCE_ID,
        "fresh_snapshot": _snapshot_revision(after) > _snapshot_revision(before)
        and after.get("snapshot_id") != before.get("snapshot_id"),
        "date_unchanged": _snapshot_date(after) == _snapshot_date(before),
        "paused_after_move": after.get("paused") is True,
        "current_province_unchanged": after_army.get("current_province_id")
        == TARGET_PROVINCE_ID,
        "fresh_native_target_cleared": after_army.get("move_target_province_id")
        is None
        and after_army.get("move_target_observable") is False,
        "fresh_native_route_cleared": after_army.get("route_province_ids") == [],
    }
    return {
        "before_player_army": before_army,
        "preview": preview,
        "move": move,
        "after_player_army": after_army,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _wait_for_route_clear(
    service: GameplayBridgeService,
    before: dict[str, object],
    *,
    timeout_seconds: float,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, object] | None = None
    while True:
        candidate = service.snapshot()
        last = candidate
        try:
            army = _subject_army(candidate, PLAYER_CUNIT_ID)
        except RuntimeError:
            army = {}
        if (
            candidate.get("paused") is True
            and _snapshot_revision(candidate) > _snapshot_revision(before)
            and candidate.get("snapshot_id") != before.get("snapshot_id")
            and _snapshot_date(candidate) == _snapshot_date(before)
            and army.get("current_province_id") == TARGET_PROVINCE_ID
            and army.get("move_target_province_id") is None
            and army.get("move_target_observable") is False
            and army.get("route_province_ids") == []
        ):
            return candidate
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "move-to-current arrived shortcut lacked a fresh cleared route; "
                f"last_snapshot={last!r}"
            )
        time.sleep(0.05)


def _reinforcement_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("reinforcement query returned a non-object")
    frame = result.get("battle_reinforcement_assignment")
    if not isinstance(frame, dict):
        raise RuntimeError("reinforcement query omitted its typed frame")
    return frame


def _battle_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("battle query returned a non-object")
    frame = result.get("battle_transition_snapshot")
    if not isinstance(frame, dict):
        raise RuntimeError("battle query omitted its lifecycle frame")
    return frame


def _terminal_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("terminal query returned a non-object")
    frame = result.get("battle_terminal_transition")
    if not isinstance(frame, dict):
        raise RuntimeError("terminal query omitted its journal frame")
    return frame


def _native_parent_order_proof(
    snapshot: dict[str, object],
    requester_result: dict[str, object],
    helper_result: dict[str, object],
) -> dict[str, object]:
    requester = _reinforcement_frame(requester_result)
    helper = _reinforcement_frame(helper_result)
    requester_order = requester.get("native_order")
    helper_order = helper.get("native_order")
    requester_order = requester_order if isinstance(requester_order, dict) else {}
    helper_order = helper_order if isinstance(helper_order, dict) else {}
    rows = requester_order.get("parent_subunits_in_stored_order")
    rows = rows if isinstance(rows, list) else []
    observed_rows = [
        row.get("public_cunit_ids_in_stored_order")
        if isinstance(row, dict)
        else None
        for row in rows
    ]
    flattened: list[int] = []
    locations: dict[int, tuple[int, int]] = {}
    order_typed = True
    for row_index, ids in enumerate(observed_rows):
        if not isinstance(ids, list):
            order_typed = False
            continue
        for within_row_index, value in enumerate(ids):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
                or value in locations
            ):
                order_typed = False
                continue
            locations[value] = (row_index, within_row_index)
            flattened.append(value)
    requester_location = locations.get(REQUESTER_CUNIT_ID)
    helper_location = locations.get(HELPER_CUNIT_ID)
    first_sequence = requester_result.get("query_sequence")
    second_sequence = helper_result.get("query_sequence")
    checks = {
        "both_available": requester.get("status") == "available"
        and helper.get("status") == "available",
        "selected_ids": requester.get("selected_public_cunit_id")
        == REQUESTER_CUNIT_ID
        and helper.get("selected_public_cunit_id") == HELPER_CUNIT_ID,
        "same_paused_native_binding": requester.get("snapshot_revision")
        == snapshot.get("native_revision")
        == helper.get("snapshot_revision")
        and requester.get("observed_date_raw")
        == snapshot.get("date_raw")
        == helper.get("observed_date_raw"),
        "queried_in_native_order": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence > first_sequence,
        "same_parent": requester.get("coordinator_id")
        == helper.get("coordinator_id")
        and requester.get("unit_stack_stored_index")
        == helper.get("unit_stack_stored_index"),
        "selected_subunit_indices_match_native_rows": bool(
            requester_location is not None
            and helper_location is not None
            and requester.get("subunit_stored_index")
            == requester_location[0]
            and helper.get("subunit_stored_index") == helper_location[0]
        ),
        "parent_order_identical_between_queries": requester_order == helper_order,
        "parent_flattened_order_exact": order_typed
        and flattened == [REQUESTER_CUNIT_ID, HELPER_CUNIT_ID],
    }
    return {
        "requester_result": requester_result,
        "helper_result": helper_result,
        "requester_frame": requester,
        "helper_frame": helper,
        "observed_parent_public_cunit_rows": observed_rows,
        "observed_parent_flattened_public_cunit_order": flattened,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _query_native_parent_pair(
    service: GameplayBridgeService, snapshot: dict[str, object]
) -> dict[str, object]:
    revision = _snapshot_revision(snapshot)
    requester = service.query_battle_reinforcement_assignment_v1(
        REQUESTER_CUNIT_ID, expected_revision=revision
    )
    helper = service.query_battle_reinforcement_assignment_v1(
        HELPER_CUNIT_ID, expected_revision=revision
    )
    proof = _native_parent_order_proof(snapshot, requester, helper)
    if proof.get("ok") is not True:
        raise RuntimeError(
            "native requester/helper parent order changed: "
            + json.dumps(
                proof,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    return proof


def _active_combat_id(frame: dict[str, object]) -> int | None:
    assignment = frame.get("assignment")
    value = (
        assignment.get("active_combat_id")
        if isinstance(assignment, dict)
        else None
    )
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def _contact_battle_proof(frame: dict[str, object]) -> dict[str, object]:
    attackers = frame.get("attacker_public_cunit_ids_in_stored_order")
    defenders = frame.get("defender_public_cunit_ids_in_stored_order")
    attackers = attackers if isinstance(attackers, list) else []
    defenders = defenders if isinstance(defenders, list) else []
    requester_attacker = REQUESTER_CUNIT_ID in attackers
    requester_defender = REQUESTER_CUNIT_ID in defenders
    player_attacker = PLAYER_CUNIT_ID in attackers
    player_defender = PLAYER_CUNIT_ID in defenders
    requester_side_name = "attacker" if requester_attacker else "defender"
    same_side = attackers if requester_attacker else defenders
    opposite_side = defenders if requester_attacker else attackers
    checks = {
        "available_active_combat": frame.get("status") == "available"
        and frame.get("battle_transition_ready") is True
        and frame.get("finalized") is False,
        "target_province": frame.get("province_id") == TARGET_PROVINCE_ID,
        "nonterminal_phase": frame.get("phase_raw") in {0, 1, 2}
        and frame.get("winner_raw") == -1
        and frame.get("battle_result_id") is None,
        "requester_exactly_one_side": requester_attacker is not requester_defender,
        "player_exactly_one_side": player_attacker is not player_defender,
        "requester_opposes_player": requester_attacker == player_defender
        and requester_defender == player_attacker,
        "helper_not_yet_present": HELPER_CUNIT_ID not in attackers
        and HELPER_CUNIT_ID not in defenders,
    }
    return {
        "combat_id": frame.get("combat_id"),
        "requester_side": requester_side_name,
        "same_side_before_join": list(same_side),
        "opposite_side_before_join": list(opposite_side),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _active_terminal_guard(
    frame: dict[str, object],
    battle: dict[str, object],
    *,
    combat_id: int,
    requested_cursor: int | None,
) -> dict[str, object]:
    journal = frame.get("terminal_journal")
    prior = frame.get("prior")
    removal = frame.get("removal")
    journal = journal if isinstance(journal, dict) else {}
    prior = prior if isinstance(prior, dict) else {}
    removal = removal if isinstance(removal, dict) else {}
    latest = journal.get("latest_sequence")
    oldest = journal.get("oldest_available_sequence")
    bounds_typed = bool(
        isinstance(latest, int)
        and not isinstance(latest, bool)
        and latest >= 0
        and isinstance(oldest, int)
        and not isinstance(oldest, bool)
        and oldest >= 0
        and ((oldest == latest == 0) or 1 <= oldest <= latest)
    )
    checks = {
        "query_available": frame.get("status") == "available"
        and frame.get("battle_terminal_transition_ready") is True,
        "combat_identity": frame.get("prior_combat_id") == combat_id
        and prior.get("combat_id") == combat_id,
        "active_not_terminal": prior.get("terminal_kind")
        == "active_not_terminal",
        "cursor_bound": journal.get("requested_after_sequence")
        == requested_cursor,
        "no_terminal_event": journal.get("event_status") == "not_observed"
        and journal.get("event_sequence") is None,
        "journal_bounds_typed": bounds_typed,
        "old_combat_still_resolves": removal.get(
            "prior_combat_strictly_resolves"
        )
        is True,
        "participants_match_lifecycle": prior.get(
            "attacker_public_cunit_ids_in_stored_order"
        )
        == battle.get("attacker_public_cunit_ids_in_stored_order")
        and prior.get("defender_public_cunit_ids_in_stored_order")
        == battle.get("defender_public_cunit_ids_in_stored_order"),
    }
    next_cursor = latest if bounds_typed and isinstance(latest, int) and latest > 0 else requested_cursor
    return {
        "requested_cursor": requested_cursor,
        "next_cursor": next_cursor,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _assignment_proof(
    pair: dict[str, object],
    snapshot: dict[str, object],
    *,
    combat_id: int,
) -> dict[str, object]:
    requester = pair.get("requester_frame")
    helper = pair.get("helper_frame")
    requester = requester if isinstance(requester, dict) else {}
    helper = helper if isinstance(helper, dict) else {}
    requester_signal = requester.get("signal")
    requester_assignment = requester.get("assignment")
    helper_signal = helper.get("signal")
    helper_assignment = helper.get("assignment")
    helper_route = helper.get("route")
    helper_order = helper.get("native_order")
    requester_signal = requester_signal if isinstance(requester_signal, dict) else {}
    requester_assignment = requester_assignment if isinstance(requester_assignment, dict) else {}
    helper_signal = helper_signal if isinstance(helper_signal, dict) else {}
    helper_assignment = helper_assignment if isinstance(helper_assignment, dict) else {}
    helper_route = helper_route if isinstance(helper_route, dict) else {}
    helper_order = helper_order if isinstance(helper_order, dict) else {}
    rows = helper_order.get("parent_subunits_in_stored_order")
    rows = rows if isinstance(rows, list) else []
    requester_index = requester.get("subunit_stored_index")
    helper_index = helper.get("subunit_stored_index")
    requester_row = (
        rows[requester_index]
        if isinstance(requester_index, int)
        and not isinstance(requester_index, bool)
        and 0 <= requester_index < len(rows)
        and isinstance(rows[requester_index], dict)
        else {}
    )
    helper_row = (
        rows[helper_index]
        if isinstance(helper_index, int)
        and not isinstance(helper_index, bool)
        and 0 <= helper_index < len(rows)
        and isinstance(rows[helper_index], dict)
        else {}
    )
    route_ids = helper_route.get("route_province_ids")
    arrivals = helper_route.get("arrival_date_raws")
    eta = helper_route.get("assignment_eta_date_raw")
    helper_army = _subject_army(snapshot, HELPER_CUNIT_ID)
    checks = {
        "parent_pair_typed": pair.get("ok") is True,
        "requester_is_active_asker": requester_signal.get("asking_for_help")
        is True
        and requester_assignment.get("combat_binding_status")
        == "already_in_active_combat"
        and requester_assignment.get("active_combat_id") == combat_id,
        "helper_assigned_to_help": helper_signal.get("assigned_to_help") is True
        and helper_signal.get("asking_for_help") is False,
        "native_help_override_target": helper_assignment.get(
            "assignment_target_province_id"
        )
        == TARGET_PROVINCE_ID
        and helper_assignment.get("target_provenance")
        == "native_help_override",
        "combat_unbound_until_contact": helper_assignment.get(
            "combat_binding_status"
        )
        == "unbound_until_contact"
        and helper_assignment.get("active_combat_id") is None,
        "route_aligned_to_assignment": helper_route.get("route_alignment")
        == "aligned_to_assignment"
        and helper_route.get("move_target_province_id") == TARGET_PROVINCE_ID
        and isinstance(route_ids, list)
        and bool(route_ids)
        and route_ids[-1] == TARGET_PROVINCE_ID,
        "typed_parallel_eta": isinstance(arrivals, list)
        and isinstance(route_ids, list)
        and len(arrivals) == len(route_ids)
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in arrivals
        )
        and arrivals == sorted(arrivals)
        and isinstance(eta, int)
        and not isinstance(eta, bool)
        and eta == arrivals[-1]
        and eta >= _snapshot_date(snapshot),
        "semantic_helper_route_matches": helper_army.get("current_province_id")
        == helper_route.get("current_province_id")
        and helper_army.get("route_province_ids") == route_ids
        and helper_army.get("move_target_province_id") == TARGET_PROVINCE_ID
        and helper_army.get("in_combat") is False,
        "native_rows_show_request_and_assignment": requester_row.get(
            "asking_for_help"
        )
        is True
        and helper_row.get("assigned_to_help") is True
        and helper_row.get("assignment_target_province_id")
        == TARGET_PROVINCE_ID,
    }
    return {
        "assignment_eta_date_raw": eta,
        "requester_frame": requester,
        "helper_frame": helper,
        "helper_semantic_army": helper_army,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _join_proof(
    baseline_battle: dict[str, object],
    before_join_battle: dict[str, object],
    joined_battle: dict[str, object],
    helper_frame: dict[str, object],
    snapshot: dict[str, object],
    *,
    combat_id: int,
) -> dict[str, object]:
    baseline = _contact_battle_proof(baseline_battle)
    side_name = baseline.get("requester_side")
    same_key = (
        "attacker_public_cunit_ids_in_stored_order"
        if side_name == "attacker"
        else "defender_public_cunit_ids_in_stored_order"
    )
    opposite_key = (
        "defender_public_cunit_ids_in_stored_order"
        if side_name == "attacker"
        else "attacker_public_cunit_ids_in_stored_order"
    )
    same_before = baseline_battle.get(same_key)
    opposite_before = baseline_battle.get(opposite_key)
    same_joined = joined_battle.get(same_key)
    opposite_joined = joined_battle.get(opposite_key)
    helper_assignment = helper_frame.get("assignment")
    helper_assignment = helper_assignment if isinstance(helper_assignment, dict) else {}
    helper_army = _subject_army(snapshot, HELPER_CUNIT_ID)
    checks = {
        "baseline_is_contact_battle": baseline.get("ok") is True,
        "same_combat_identity": joined_battle.get("status") == "available"
        and joined_battle.get("combat_id") == combat_id
        and joined_battle.get("province_id") == TARGET_PROVINCE_ID,
        "helper_absent_immediately_before": HELPER_CUNIT_ID
        not in (
            (before_join_battle.get("attacker_public_cunit_ids_in_stored_order") or [])
            + (before_join_battle.get("defender_public_cunit_ids_in_stored_order") or [])
        ),
        "same_side_unique_tail_append": isinstance(same_before, list)
        and isinstance(same_joined, list)
        and same_joined == [*same_before, HELPER_CUNIT_ID]
        and same_joined.count(HELPER_CUNIT_ID) == 1,
        "opposite_side_unchanged": isinstance(opposite_before, list)
        and opposite_joined == opposite_before,
        "helper_exact_active_combat_binding": helper_assignment.get(
            "combat_binding_status"
        )
        == "already_in_active_combat"
        and helper_assignment.get("active_combat_id") == combat_id,
        "semantic_helper_joined": helper_army.get("in_combat") is True
        and helper_army.get("current_province_id") == TARGET_PROVINCE_ID,
        "battle_phase_remains_active": joined_battle.get("finalized") is False
        and joined_battle.get("phase_raw") in {0, 1, 2}
        and joined_battle.get("winner_raw") == -1
        and joined_battle.get("battle_result_id") is None,
    }
    return {
        "combat_id": combat_id,
        "requester_side": side_name,
        "same_side_before": same_before,
        "same_side_joined": same_joined,
        "opposite_side_before": opposite_before,
        "opposite_side_joined": opposite_joined,
        "helper_semantic_army": helper_army,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _advance_one_day(
    service: GameplayBridgeService,
    before: dict[str, object],
    wait_after_advance: Callable[[], dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    _assert_paused(before)
    before_date = _snapshot_date(before)
    before_revision = _snapshot_revision(before)
    result = service.execute_step(
        "life-advance", expected_revision=before_revision
    )
    after = wait_after_advance()
    _assert_paused(after)
    checks = {
        "step": isinstance(result, dict)
        and result.get("step") == "life-advance",
        "result_dates": result.get("starting_date_raw") == before_date
        and result.get("ending_date_raw") == before_date + ONE_GAME_DAY_RAW,
        "result_elapsed_days": result.get("elapsed_days") == 1,
        "snapshot_exactly_one_day": _snapshot_date(after)
        == before_date + ONE_GAME_DAY_RAW,
        "fresh_revision": _snapshot_revision(after) > before_revision,
        "same_episode": after.get("episode_run_id")
        == before.get("episode_run_id"),
    }
    proof = {
        "before_date_raw": before_date,
        "after_date_raw": _snapshot_date(after),
        "before_revision": before_revision,
        "after_revision": _snapshot_revision(after),
        "date_delta_raw": _snapshot_date(after) - before_date,
        "result": result,
        "checks": checks,
        "ok": all(checks.values()),
    }
    if proof["ok"] is not True:
        raise RuntimeError("life-advance did not advance exactly one CK3 day")
    return after, proof


def _archive_checkpoint(
    result: object,
    *,
    archive_name: str,
    expected_date_raw: int,
) -> dict[str, object]:
    checkpoint = result.get("checkpoint") if isinstance(result, dict) else None
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    source_value = checkpoint.get("path")
    source = Path(source_value).resolve() if isinstance(source_value, str) else None
    if (
        checkpoint.get("status") != "saved"
        or source is None
        or not source.is_file()
        or checkpoint.get("date_raw") != expected_date_raw
    ):
        raise RuntimeError("save-checkpoint did not materialize the expected date")
    archive = source.with_name(archive_name)
    if archive.exists():
        raise RuntimeError(f"checkpoint archive already exists: {archive}")
    shutil.copy2(source, archive)
    source_sha = _sha256_file(source)
    archive_sha = _sha256_file(archive)
    if source_sha != archive_sha:
        raise RuntimeError("checkpoint archive bytes differ from materialization")
    return {
        "checkpoint": checkpoint,
        "archive_path": str(archive),
        "archive_size": archive.stat().st_size,
        "archive_sha256": archive_sha,
        "ok": True,
    }


def _mutation_boundary_proof(commands: list[str]) -> dict[str, object]:
    preview = f"preview-move-army-{PLAYER_CUNIT_ID}-to-{TARGET_PROVINCE_ID}"
    move = f"move-army-{PLAYER_CUNIT_ID}-to-{TARGET_PROVINCE_ID}"
    allowed = {preview, move, "life-advance", "save-checkpoint"}
    checks = {
        "only_existing_production_commands": all(row in allowed for row in commands),
        "one_preview": commands.count(preview) == 1,
        "one_move": commands.count(move) == 1,
        "two_checkpoint_saves": commands.count("save-checkpoint") == 2,
        "at_least_one_exact_day": commands.count("life-advance") >= 1,
        "preview_precedes_move": preview in commands
        and move in commands
        and commands.index(preview) < commands.index(move),
    }
    return {
        "commands": list(commands),
        "allowed_commands": sorted(allowed),
        "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
        "forbidden_native_calls_invoked": [],
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_reinforcement_join_sequence(
    service: GameplayBridgeService,
    *,
    wait_after_advance: Callable[[], dict[str, object]],
    max_contact_days: int,
    max_assignment_days: int,
    max_eta_days: int,
    route_clear_timeout: float,
) -> dict[str, object]:
    commands: list[str] = []
    advances: list[dict[str, object]] = []
    daily_pairs: list[dict[str, object]] = []
    terminal_guards: list[dict[str, object]] = []

    initial = service.snapshot()
    initial_geometry = _initial_geometry_proof(initial)
    if initial_geometry.get("ok") is not True:
        raise RuntimeError("frozen checkpoint geometry differs")

    preview_step = (
        f"preview-move-army-{PLAYER_CUNIT_ID}-to-{TARGET_PROVINCE_ID}"
    )
    preview = service.execute_step(
        preview_step, expected_revision=_snapshot_revision(initial)
    )
    commands.append(preview_step)
    after_preview = service.snapshot()
    if not _same_paused_binding(initial, after_preview):
        raise RuntimeError("move preview changed the paused snapshot")
    move = service.move_army(
        PLAYER_CUNIT_ID,
        TARGET_PROVINCE_ID,
        expected_revision=_snapshot_revision(after_preview),
    )
    commands.append(
        f"move-army-{PLAYER_CUNIT_ID}-to-{TARGET_PROVINCE_ID}"
    )
    cleared = _wait_for_route_clear(
        service, after_preview, timeout_seconds=route_clear_timeout
    )
    route_clear = _route_clear_proof(after_preview, preview, move, cleared)
    if route_clear.get("ok") is not True:
        raise RuntimeError("fresh native route-clear proof failed")

    snapshot = cleared
    contact_pair: dict[str, object] | None = None
    baseline_battle: dict[str, object] | None = None
    contact_proof: dict[str, object] | None = None
    combat_id: int | None = None
    for day_index in range(max_contact_days + 1):
        pair = _query_native_parent_pair(service, snapshot)
        daily_pairs.append(
            {"stage": "contact", "day_index": day_index, "pair": pair}
        )
        requester = pair["requester_frame"]
        assert isinstance(requester, dict)
        candidate = _active_combat_id(requester)
        if candidate is not None:
            combat_result = service.query_battle_transition_v1(
                candidate, expected_revision=_snapshot_revision(snapshot)
            )
            battle = _battle_frame(combat_result)
            candidate_proof = _contact_battle_proof(battle)
            if candidate_proof.get("ok") is not True:
                raise RuntimeError(
                    "requester active CombatID is not player contact: "
                    + json.dumps(
                        {
                            "candidate_combat_id": candidate,
                            "contact_proof": candidate_proof,
                            "battle": battle,
                            "requester_frame": requester,
                            "date_raw": snapshot.get("date_raw"),
                            "revision": snapshot.get("revision"),
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            combat_id = candidate
            contact_pair = pair
            baseline_battle = battle
            contact_proof = candidate_proof
            break
        if day_index == max_contact_days:
            raise RuntimeError("requester did not contact player within bound")
        snapshot, advance = _advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
    if (
        combat_id is None
        or contact_pair is None
        or baseline_battle is None
        or contact_proof is None
    ):
        raise RuntimeError("contact loop ended without an exact CombatID")

    cursor: int | None = None
    assignment: dict[str, object] | None = None
    assigned_pair = contact_pair
    assigned_battle = baseline_battle
    for day_index in range(max_assignment_days + 1):
        if day_index > 0:
            assigned_pair = _query_native_parent_pair(service, snapshot)
            daily_pairs.append(
                {"stage": "assignment", "day_index": day_index, "pair": assigned_pair}
            )
            assigned_battle = _battle_frame(
                service.query_battle_transition_v1(
                    combat_id, expected_revision=_snapshot_revision(snapshot)
                )
            )
        lifecycle = _contact_battle_proof(assigned_battle)
        if lifecycle.get("ok") is not True:
            raise RuntimeError("contact combat changed before helper assignment")
        terminal = _terminal_frame(
            service.query_battle_terminal_transition_v1(
                combat_id,
                REQUESTER_CUNIT_ID,
                expected_revision=_snapshot_revision(snapshot),
                after_terminal_sequence=cursor,
            )
        )
        guard = _active_terminal_guard(
            terminal,
            assigned_battle,
            combat_id=combat_id,
            requested_cursor=cursor,
        )
        terminal_guards.append(guard)
        if guard.get("ok") is not True:
            raise RuntimeError("combat terminal journal changed before assignment")
        cursor = guard["next_cursor"]
        candidate_assignment = _assignment_proof(
            assigned_pair, snapshot, combat_id=combat_id
        )
        if candidate_assignment.get("ok") is True:
            assignment = candidate_assignment
            break
        if day_index == max_assignment_days:
            raise RuntimeError("helper assignment was not observed within bound")
        snapshot, advance = _advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
    if assignment is None:
        raise RuntimeError("assignment loop ended without a typed ETA")

    assigned_date = _snapshot_date(snapshot)
    eta = assignment.get("assignment_eta_date_raw")
    if (
        isinstance(eta, bool)
        or not isinstance(eta, int)
        or eta < assigned_date
        or eta > assigned_date + max_eta_days * ONE_GAME_DAY_RAW
    ):
        raise RuntimeError("assignment ETA is outside the bounded daily loop")
    assigned_save_result = service.save_checkpoint(
        expected_revision=_snapshot_revision(snapshot)
    )
    commands.append("save-checkpoint")
    assigned_checkpoint = _archive_checkpoint(
        assigned_save_result,
        archive_name=_ASSIGNED_ARCHIVE_NAME,
        expected_date_raw=assigned_date,
    )
    after_assigned_save = service.snapshot()
    _assert_paused(after_assigned_save)
    if (
        _snapshot_date(after_assigned_save) != assigned_date
        or after_assigned_save.get("episode_run_id")
        != snapshot.get("episode_run_id")
    ):
        raise RuntimeError("assigned checkpoint changed the gameplay frame")
    snapshot = after_assigned_save

    before_join_battle = assigned_battle
    join: dict[str, object] | None = None
    joined_pair: dict[str, object] | None = None
    joined_battle: dict[str, object] | None = None
    eta_day_index = 0
    while _snapshot_date(snapshot) < eta:
        if eta_day_index >= max_eta_days:
            raise RuntimeError("helper join exceeded max_eta_days")
        snapshot, advance = _advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
        eta_day_index += 1
        pair = _query_native_parent_pair(service, snapshot)
        daily_pairs.append(
            {"stage": "eta", "day_index": eta_day_index, "pair": pair}
        )
        battle = _battle_frame(
            service.query_battle_transition_v1(
                combat_id, expected_revision=_snapshot_revision(snapshot)
            )
        )
        terminal = _terminal_frame(
            service.query_battle_terminal_transition_v1(
                combat_id,
                REQUESTER_CUNIT_ID,
                expected_revision=_snapshot_revision(snapshot),
                after_terminal_sequence=cursor,
            )
        )
        guard = _active_terminal_guard(
            terminal,
            battle,
            combat_id=combat_id,
            requested_cursor=cursor,
        )
        terminal_guards.append(guard)
        if guard.get("ok") is not True:
            raise RuntimeError("combat terminal journal changed before helper join")
        cursor = guard["next_cursor"]
        attackers = battle.get("attacker_public_cunit_ids_in_stored_order")
        defenders = battle.get("defender_public_cunit_ids_in_stored_order")
        participants = [
            *(attackers if isinstance(attackers, list) else []),
            *(defenders if isinstance(defenders, list) else []),
        ]
        if HELPER_CUNIT_ID in participants:
            helper_frame = pair.get("helper_frame")
            assert isinstance(helper_frame, dict)
            candidate_join = _join_proof(
                baseline_battle,
                before_join_battle,
                battle,
                helper_frame,
                snapshot,
                combat_id=combat_id,
            )
            if candidate_join.get("ok") is not True:
                raise RuntimeError("helper contact did not satisfy tail-append proof")
            join = candidate_join
            joined_pair = pair
            joined_battle = battle
            break
        persistence = _assignment_proof(pair, snapshot, combat_id=combat_id)
        if persistence.get("ok") is not True:
            raise RuntimeError("helper assignment disappeared before contact")
        before_join_battle = battle
    if join is None or joined_pair is None or joined_battle is None:
        raise RuntimeError("helper did not join the exact CombatID by native ETA")

    joined_date = _snapshot_date(snapshot)
    if joined_date > eta:
        raise RuntimeError("helper joined after the captured native ETA")
    joined_save_result = service.save_checkpoint(
        expected_revision=_snapshot_revision(snapshot)
    )
    commands.append("save-checkpoint")
    joined_checkpoint = _archive_checkpoint(
        joined_save_result,
        archive_name=_JOINED_ARCHIVE_NAME,
        expected_date_raw=joined_date,
    )
    after_joined_save = service.snapshot()
    _assert_paused(after_joined_save)
    if _snapshot_date(after_joined_save) != joined_date:
        raise RuntimeError("joined checkpoint changed the gameplay date")

    boundary = _mutation_boundary_proof(commands)
    assertions = {
        "frozen_geometry_observed": initial_geometry.get("ok") is True,
        "fresh_route_clear_observed": route_clear.get("ok") is True,
        "daily_native_parent_order": all(
            isinstance(row.get("pair"), dict)
            and row["pair"].get("ok") is True
            for row in daily_pairs
        ),
        "requester_created_player_combat": contact_proof.get("ok") is True,
        "helper_assignment_and_eta_observed": assignment.get("ok") is True,
        "every_advance_exactly_one_day": bool(advances)
        and all(row.get("ok") is True for row in advances),
        "terminal_remained_active": bool(terminal_guards)
        and all(row.get("ok") is True for row in terminal_guards),
        "helper_joined_exact_combat_tail": join.get("ok") is True,
        "assigned_checkpoint_saved": assigned_checkpoint.get("ok") is True,
        "joined_checkpoint_saved": joined_checkpoint.get("ok") is True,
        "production_command_boundary": boundary.get("ok") is True,
    }
    return {
        "initial_snapshot": initial,
        "initial_geometry_proof": initial_geometry,
        "route_clear_proof": route_clear,
        "contact_combat_id": combat_id,
        "contact_proof": contact_proof,
        "baseline_battle": baseline_battle,
        "assignment_proof": assignment,
        "assigned_date_raw": assigned_date,
        "assignment_eta_date_raw": eta,
        "assigned_checkpoint": assigned_checkpoint,
        "joined_date_raw": joined_date,
        "joined_pair": joined_pair,
        "joined_battle": joined_battle,
        "join_proof": join,
        "joined_checkpoint": joined_checkpoint,
        "daily_pairs": daily_pairs,
        "terminal_guards": terminal_guards,
        "advances": advances,
        "ending_snapshot": after_joined_save,
        "command_boundary_proof": boundary,
        "assertions": assertions,
        "ok": all(assertions.values()),
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
    hello_value = _diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_value = hello.get("capabilities")
    hello_capabilities = hello_value if isinstance(hello_value, list) else []
    required = (
        QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
        QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
        QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
        PREVIEW_MOVE_ARMY_CAPABILITY,
        MOVE_ARMY_CAPABILITY,
    )
    action_steps = raw.get("action_steps")
    action_steps = action_steps if isinstance(action_steps, list) else []
    exact_steps = (
        f"preview-move-army-{PLAYER_CUNIT_ID}-to-{TARGET_PROVINCE_ID}",
        f"move-army-{PLAYER_CUNIT_ID}-to-{TARGET_PROVINCE_ID}",
        "life-advance",
        "save-checkpoint",
    )
    checks = {
        "bridge_capabilities": all(value in advertised for value in required),
        "hello_capabilities": all(value in hello_capabilities for value in required),
        "exact_action_steps": all(value in action_steps for value in exact_steps),
        "reinforcement_driver_surface": raw.get(
            "battle_reinforcement_assignment_v1_query_supported"
        )
        is True,
        "terminal_driver_surface": raw.get(
            "battle_terminal_transition_v1_query_supported"
        )
        is True,
    }
    return {
        "required_bridge_capabilities": list(required),
        "required_action_steps": list(exact_steps),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _same_process_proof(
    before_capabilities: object, after_capabilities: object
) -> dict[str, object]:
    before = _diagnostics(before_capabilities)
    after = _diagnostics(after_capabilities)
    before_pid = before.get("bridge_pid")
    before_generation = before.get("connection_generation")
    checks = {
        "same_positive_bridge_pid": isinstance(before_pid, int)
        and not isinstance(before_pid, bool)
        and before_pid > 0
        and after.get("bridge_pid") == before_pid,
        "same_positive_connection_generation": isinstance(
            before_generation, int
        )
        and not isinstance(before_generation, bool)
        and before_generation > 0
        and after.get("connection_generation") == before_generation,
        "connection_remained_live": before.get("connected") is True
        and after.get("connected") is True,
    }
    return {"checks": checks, "ok": all(checks.values())}


def _run_live_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    max_contact_days: int,
    max_assignment_days: int,
    max_eta_days: int,
    route_clear_timeout: float,
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
    sequence: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
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
            name="xar-battle-reinforcement-join-live-session",
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
            raise RuntimeError("reinforcement join capabilities are incomplete")

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

        sequence = _run_reinforcement_join_sequence(
            service,
            wait_after_advance=wait_after_advance,
            max_contact_days=max_contact_days,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
            route_clear_timeout=route_clear_timeout,
        )
        if sequence.get("ok") is not True:
            raise RuntimeError("reinforcement join sequence did not qualify")
        same_process = _same_process_proof(
            capabilities_before, driver.capabilities()
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("reinforcement proof crossed bridge process")
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
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "managed process cleanup was not proven"
        )
    return {
        "ok": bool(
            primary_error is None
            and exact_build
            and exact_build.get("ok") is True
            and capability
            and capability.get("ok") is True
            and sequence
            and sequence.get("ok") is True
            and same_process
            and same_process.get("ok") is True
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
        "sequence": sequence,
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
            "reason": "--retain-state prevents cleanup qualification",
        }
    if session_started and not session_cleanup_proven:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "managed process cleanup was not proven; clone retained",
        }
    marker = target / _CLONE_MARKER_NAME
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == "xar_battle_reinforcement_join_clone"
            and payload.get("nonce") == clone_nonce
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
    max_contact_days = _positive_int(args.max_contact_days, "max_contact_days")
    max_assignment_days = _positive_int(
        args.max_assignment_days, "max_assignment_days"
    )
    max_eta_days = _positive_int(args.max_eta_days, "max_eta_days")
    timeout = _positive_number(args.timeout, "timeout")
    readiness_timeout = _positive_number(
        args.readiness_timeout, "readiness_timeout"
    )
    route_clear_timeout = _positive_number(
        args.route_clear_timeout, "route_clear_timeout"
    )
    expected_save_sha256 = _expected_sha256(
        args.expected_battle_save_sha256
    )
    if expected_save_sha256 != EXPECTED_SOURCE_SAVE_SHA256:
        raise AgentError("reinforcement milestone requires the frozen save hash")
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
            max_contact_days=max_contact_days,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
            route_clear_timeout=route_clear_timeout,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if live.get("ok") is not True:
            primary_error = str(
                live.get("error") or "reinforcement join live session failed"
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
    session_started = bool(live and live.get("session_started") is True)
    session_cleanup_proven = bool(
        live
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
        primary_error = "immutable source checkpoint changed"
    if clone_cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            clone_cleanup.get("reason") or "clone cleanup was not proven"
        )
    ok = bool(
        primary_error is None
        and live
        and live.get("ok") is True
        and source_unchanged
        and clone_cleanup.get("ok") is True
    )
    sequence = live.get("sequence") if isinstance(live, dict) else None
    sequence = sequence if isinstance(sequence, dict) else {}
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_battle_reinforcement_join_v1_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "fixed_scenario": {
            "player_public_cunit_id": PLAYER_CUNIT_ID,
            "requester_public_cunit_id": REQUESTER_CUNIT_ID,
            "helper_public_cunit_id": HELPER_CUNIT_ID,
            "target_province_id": TARGET_PROVINCE_ID,
            "player_initial_route": EXPECTED_PLAYER_ROUTE,
            "requester_initial_route": EXPECTED_REQUESTER_ROUTE,
            "helper_initial_route": EXPECTED_HELPER_ROUTE,
        },
        "bounds": {
            "max_contact_days": max_contact_days,
            "max_assignment_days": max_assignment_days,
            "max_eta_days": max_eta_days,
            "one_game_day_raw": ONE_GAME_DAY_RAW,
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "route_clear_timeout_seconds": route_clear_timeout,
        },
        "policy": {
            "production_non_debug": True,
            "load_kind": "continue_last_save",
            "continue_save_name": CONTINUE_SAVE_NAME,
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
            "fresh_player_route_clear": bool(
                sequence.get("route_clear_proof")
                and sequence["route_clear_proof"].get("ok") is True
            ),
            "native_assignment_aligned_eta": bool(
                sequence.get("assignment_proof")
                and sequence["assignment_proof"].get("ok") is True
            ),
            "actual_same_combat_tail_join": bool(
                sequence.get("join_proof")
                and sequence["join_proof"].get("ok") is True
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
