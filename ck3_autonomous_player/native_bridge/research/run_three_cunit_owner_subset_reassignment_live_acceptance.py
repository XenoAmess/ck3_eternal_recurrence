#!/usr/bin/env python3
"""Build a three-CUnit defender fixture and prove native reassignment/rejoin.

The immutable 5BA pre-contact checkpoint is cloned through seven managed
stages.  Seed-only stages only switch the played Character.  Production-only
stages clear the stale attacker route, split CUnit 33554657, route both
retained armies, materialize contact, execute the owner-subset retreat, and
observe native assignment/ETA/same-CombatID rejoin.  The retreat is forbidden
unless the requester parent exposes at least three distinct native subunit
rows, so removing CUnit 357 necessarily leaves at least two rows that can ask
for help through the frozen 0x1848310 decision path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
from typing import Any, Callable
import uuid


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_battle_reinforcement_join_live_acceptance as join_live  # noqa: E402
import run_active_combat_retreat_live_acceptance as retreat_live  # noqa: E402
import run_owner_subset_ai_reassignment_rejoin_live_acceptance as ai_live  # noqa: E402
import run_owner_subset_reinforcement_rejoin_live_acceptance as rejoin_live  # noqa: E402
import run_owner_subset_retreat_live_acceptance as owner_live  # noqa: E402
from xar_autoplayer.bridge.mod_driver import DataModGameplayDriver  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    MOVE_ARMY_CAPABILITY,
    PREVIEW_MOVE_ARMY_CAPABILITY,
    SPLIT_ARMY_HALF_CAPABILITY,
    split_army_half_step,
)
from xar_autoplayer.environment import (  # noqa: E402
    ensure_state_path_safe,
    is_relative_to,
    paths_overlap,
    write_json_atomic,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import _wait_for_readiness  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, ck3_processes, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
EXPECTED_SOURCE_SAVE_SHA256 = (
    "5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F"
)
DEFAULT_SOURCE_STATE_DIR = Path(r"C:\Users\xenoa\AppData\Local\XarAutoplayer")
DEFAULT_BATTLE_SAVE = Path(
    r"save games\xar_checkpoint_pre_white_peace_53175816.ck3"
)
CONTINUE_SAVE_NAME = owner_live.CONTINUE_SAVE_NAME
ONE_GAME_DAY_RAW = owner_live.ONE_GAME_DAY_RAW
WAR_ID = 16_777_290
ORIGINAL_CHARACTER_ID = owner_live.ORIGINAL_CHARACTER_ID
REQUESTER_CHARACTER_ID = owner_live.OWNER_SUBSET_CHARACTER_ID
RETAINED_CHARACTER_ID = owner_live.UNCONTROLLED_ALLY_OWNER_ID
OPPOSITE_CUNIT_ID = owner_live.ORIGINAL_ATTACKER_CUNIT_ID
REQUESTER_CUNIT_ID = owner_live.OWNER_SUBSET_CUNIT_ID
ANCHOR_CUNIT_ID = owner_live.UNCONTROLLED_ALLY_CUNIT_ID
CONTACT_PROVINCE_ID = join_live.TARGET_PROVINCE_ID
RETREAT_PROVINCE_ID = owner_live.TARGET_PROVINCE_ID
RETURN_ANCHOR_PROVINCE_ID = ai_live.RETURN_CHARACTER_ANCHOR_PROVINCE_ID
REQUESTER_ANCHOR_PROVINCE_ID = owner_live.TARGET_CHARACTER_ANCHOR_PROVINCE_ID
SIDE_INDEX = owner_live.EXPECTED_SIDE_INDEX

ALLY_SWITCH_MARKER = "XAR_FIXTURE:THREE_CUNIT_ALLY_SWITCH|target=secondary_defender"
ALLY_CLEAR_MARKER = "XAR_FIXTURE:THREE_CUNIT_ALLY_SWITCH_GUARD_CLEARED"
ALLY_SWITCH_GUARD = "xar_fixture_three_cunit_ally_switch_consumed"
ALLY_CANDIDATE_COUNT = "xar_fixture_three_cunit_secondary_defender_count"
REQUESTER_SWITCH_MARKER = "XAR_FIXTURE:THREE_CUNIT_REQUESTER_SWITCH|target=36108"
REQUESTER_CLEAR_MARKER = "XAR_FIXTURE:THREE_CUNIT_REQUESTER_GUARD_CLEARED"
REQUESTER_SWITCH_GUARD = "xar_fixture_three_cunit_requester_switch_consumed"
RETURN_SWITCH_MARKER = "XAR_FIXTURE:THREE_CUNIT_RETURN|target=29829"
RETURN_CLEAR_MARKER = "XAR_FIXTURE:THREE_CUNIT_RETURN_GUARD_CLEARED"
RETURN_SWITCH_GUARD = "xar_fixture_three_cunit_return_consumed"

SPLIT_ARCHIVE_NAME = "xar_three_cunit_split.ck3"
RETREAT_ARCHIVE_NAME = "xar_three_cunit_retreat.ck3"
ASSIGNED_ARCHIVE_NAME = "xar_three_cunit_assigned.ck3"
JOINED_ARCHIVE_NAME = "xar_three_cunit_joined.ck3"
_ROOT_MARKER_NAME = ".xar-three-cunit-owner-subset.json"
FORBIDDEN_NATIVE_CALLS = rejoin_live.FORBIDDEN_NATIVE_CALLS


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
    parser.add_argument("--max-split-wait-days", type=int, default=10)
    parser.add_argument("--max-contact-days", type=int, default=45)
    parser.add_argument("--max-assignment-days", type=int, default=30)
    parser.add_argument("--max-eta-days", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=1200.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--seed-timeout", type=float, default=30.0)
    parser.add_argument("--postcondition-timeout", type=float, default=10.0)
    parser.add_argument("--route-timeout", type=float, default=10.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _positive_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be positive")
    result = float(value)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: object) -> str:
    result = str(value).strip().upper()
    if len(result) != 64 or any(ch not in "0123456789ABCDEF" for ch in result):
        raise ValueError("expected save SHA-256 must be 64 hex digits")
    return result


def _dynamic_ally_switch_effect() -> str:
    """Select the unique non-primary defender without a dynamic ID link."""
    return (
        f"set_global_variable = {{ name = {ALLY_CANDIDATE_COUNT} value = 0 }}\n"
        f"province:{RETURN_ANCHOR_PROVINCE_ID} = {{\n"
        "\tprovince_owner = {\n"
        "\t\tsave_temporary_scope_as = xar_fixture_three_cunit_attacker\n"
        "\t}\n"
        "}\n"
        "scope:xar_fixture_three_cunit_attacker = {\n"
        "\tevery_character_war = {\n"
        "\t\tlimit = { primary_attacker = scope:xar_fixture_three_cunit_attacker }\n"
        "\t\tprimary_defender = {\n"
        "\t\t\tsave_temporary_scope_as = xar_fixture_three_cunit_primary_defender\n"
        "\t\t}\n"
        "\t\tevery_war_defender = {\n"
        "\t\t\tlimit = { NOT = { this = scope:xar_fixture_three_cunit_primary_defender } }\n"
        f"\t\t\tchange_global_variable = {{ name = {ALLY_CANDIDATE_COUNT} add = 1 }}\n"
        "\t\t\tsave_temporary_scope_as = xar_fixture_three_cunit_secondary_defender\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
        "if = {\n"
        "\tlimit = {\n"
        "\t\texists = scope:xar_fixture_three_cunit_secondary_defender\n"
        f"\t\tglobal_var:{ALLY_CANDIDATE_COUNT} = 1\n"
        f"\t\tNOT = {{ global_var:{ALLY_SWITCH_GUARD} = 1 }}\n"
        "\t}\n"
        f"\tset_global_variable = {{ name = {ALLY_SWITCH_GUARD} value = 1 }}\n"
        "\tset_player_character = scope:xar_fixture_three_cunit_secondary_defender\n"
        f'\tdebug_log = "{ALLY_SWITCH_MARKER}"\n'
        "}\n"
    )


def _dynamic_ally_clear_effect() -> str:
    return (
        "if = {\n"
        "\tlimit = {\n"
        f"\t\tOR = {{ exists = global_var:{ALLY_SWITCH_GUARD} exists = global_var:{ALLY_CANDIDATE_COUNT} }}\n"
        "\t}\n"
        f"\tremove_global_variable = {ALLY_SWITCH_GUARD}\n"
        f"\tremove_global_variable = {ALLY_CANDIDATE_COUNT}\n"
        f'\tdebug_log = "{ALLY_CLEAR_MARKER}"\n'
        "}\n"
    )


def _province_owner_switch_effect(
    *, province_id: int, guard: str, marker: str, scope_name: str
) -> str:
    return (
        f"province:{province_id} = {{\n"
        "\tprovince_owner = {\n"
        f"\t\tsave_temporary_scope_as = {scope_name}\n"
        "\t}\n"
        "}\n"
        "if = {\n"
        "\tlimit = {\n"
        f"\t\texists = scope:{scope_name}\n"
        f"\t\tNOT = {{ global_var:{guard} = 1 }}\n"
        "\t}\n"
        f"\tset_global_variable = {{ name = {guard} value = 1 }}\n"
        f"\tset_player_character = scope:{scope_name}\n"
        f'\tdebug_log = "{marker}"\n'
        "}\n"
    )


def _guard_clear_effect(*, guard: str, marker: str) -> str:
    return (
        "if = {\n"
        f"\tlimit = {{ exists = global_var:{guard} }}\n"
        f"\tremove_global_variable = {guard}\n"
        f'\tdebug_log = "{marker}"\n'
        "}\n"
    )


def _army(snapshot: dict[str, object], public_cunit_id: int) -> dict[str, object]:
    return rejoin_live._subject_army(snapshot, public_cunit_id)


def _precontact_army_proof(
    snapshot: dict[str, object],
    public_cunit_id: int,
    *,
    owner_character_id: int,
    controllable: bool,
) -> dict[str, object]:
    try:
        army = _army(snapshot, public_cunit_id)
    except RuntimeError:
        army = {}
    checks = {
        "paused": snapshot.get("paused") is True,
        "identity": army.get("army_id") == public_cunit_id
        and army.get("owner_character_id") == owner_character_id,
        "control": army.get("controllable") is controllable,
        "not_in_combat": army.get("in_combat") is False,
        "not_retreating": army.get("retreating") is False,
    }
    return {"army": army, "checks": checks, "ok": all(checks.values())}


def _split_postcondition_proof(
    before: dict[str, object],
    after: dict[str, object],
    result: object,
    *,
    source_cunit_id: int = ANCHOR_CUNIT_ID,
    owner_character_id: int = RETAINED_CHARACTER_ID,
) -> dict[str, object]:
    def controllable_ids(snapshot: dict[str, object]) -> set[int]:
        rows = snapshot.get("player_armies")
        return {
            int(row["army_id"])
            for row in (rows if isinstance(rows, list) else [])
            if isinstance(row, dict)
            and row.get("controllable") is True
            and isinstance(row.get("army_id"), int)
            and not isinstance(row.get("army_id"), bool)
            and int(row["army_id"]) > 0
        }

    before_ids = controllable_ids(before)
    after_ids = controllable_ids(after)
    delta = sorted(after_ids - before_ids)
    sibling_id = delta[0] if len(delta) == 1 else None
    action = result.get("war_action") if isinstance(result, dict) else None
    action = action if isinstance(action, dict) else {}
    try:
        source = _army(after, source_cunit_id)
        sibling = _army(after, sibling_id) if sibling_id is not None else {}
    except RuntimeError:
        source, sibling = {}, {}
    checks = {
        "same_paused_date": before.get("paused") is True
        and after.get("paused") is True
        and before.get("date_raw") == after.get("date_raw"),
        "same_episode": before.get("episode_run_id")
        == after.get("episode_run_id"),
        "fresh_snapshot": rejoin_live._snapshot_revision(after)
        > rejoin_live._snapshot_revision(before),
        "source_was_controllable": source_cunit_id in before_ids,
        "exact_one_new_controllable_cunit": len(delta) == 1,
        "source_persists": source_cunit_id in after_ids,
        "typed_split_result": isinstance(result, dict)
        and result.get("accepted") is True
        and action.get("source_army_id") == source_cunit_id
        and action.get("status") in {"split_submitted", "split_applied"},
        "dynamic_result_identity_consistent": action.get("sibling_army_id")
        in {None, sibling_id},
        "same_owner": source.get("owner_character_id") == owner_character_id
        and sibling.get("owner_character_id") == owner_character_id,
        "both_controllable": source.get("controllable") is True
        and sibling.get("controllable") is True,
        "both_precontact": source.get("in_combat") is False
        and sibling.get("in_combat") is False
        and source.get("retreating") is False
        and sibling.get("retreating") is False,
    }
    return {
        "source_cunit_id": source_cunit_id,
        "sibling_cunit_id": sibling_id,
        "before_controllable_ids": sorted(before_ids),
        "after_controllable_ids": sorted(after_ids),
        "source_army": source,
        "sibling_army": sibling,
        "result": result,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    if not isinstance(capabilities, dict):
        return {}
    value = capabilities.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _stage_capability_proof(
    capabilities: object, *, exact_steps: list[str], required: list[str]
) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    advertised = raw.get("bridge_capabilities")
    advertised = advertised if isinstance(advertised, list) else []
    hello = _diagnostics(raw).get("hello")
    hello = hello if isinstance(hello, dict) else {}
    hello_caps = hello.get("capabilities")
    hello_caps = hello_caps if isinstance(hello_caps, list) else []
    action_steps = raw.get("action_steps")
    action_steps = action_steps if isinstance(action_steps, list) else []
    checks = {
        "bridge_capabilities": all(value in advertised for value in required),
        "hello_capabilities": all(value in hello_caps for value in required),
        "exact_action_steps": all(value in action_steps for value in exact_steps),
    }
    return {
        "required_bridge_capabilities": list(required),
        "required_action_steps": list(exact_steps),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _wait_after_advance(
    driver: NativeHeadlessGameplayDriver,
    *,
    session_done: threading.Event,
    session_state: dict[str, object],
    readiness_timeout: float,
) -> dict[str, object]:
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


def _save_archive(
    service: GameplayBridgeService,
    snapshot: dict[str, object],
    *,
    archive_name: str,
) -> dict[str, object]:
    return rejoin_live._archive_checkpoint(
        service.save_checkpoint(
            expected_revision=rejoin_live._snapshot_revision(snapshot)
        ),
        archive_name=archive_name,
        expected_date_raw=rejoin_live._snapshot_date(snapshot),
    )


def _wait_for_army_condition(
    service: GameplayBridgeService,
    stale: dict[str, object],
    *,
    public_cunit_id: int,
    timeout_seconds: float,
    predicate: Callable[[dict[str, object]], bool],
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, object] | None = None
    while time.monotonic() < deadline:
        candidate = service.snapshot()
        last = candidate
        if not (
            candidate.get("paused") is True
            and candidate.get("date_raw") == stale.get("date_raw")
            and candidate.get("episode_run_id") == stale.get("episode_run_id")
            and rejoin_live._snapshot_revision(candidate)
            >= rejoin_live._snapshot_revision(stale)
        ):
            raise RuntimeError("paused army postcondition crossed date/episode")
        try:
            army = _army(candidate, public_cunit_id)
        except RuntimeError:
            army = {}
        if predicate(army):
            return candidate
        time.sleep(0.05)
    raise RuntimeError(f"CUnit {public_cunit_id} postcondition timed out: {last!r}")


def _move_to_target(
    service: GameplayBridgeService,
    snapshot: dict[str, object],
    *,
    public_cunit_id: int,
    target_province_id: int,
    timeout_seconds: float,
) -> tuple[dict[str, object], dict[str, object]]:
    before = snapshot
    rejoin_live._assert_paused(before)
    before_army = _army(before, public_cunit_id)
    if not (
        before_army.get("controllable") is True
        and before_army.get("in_combat") is False
        and before_army.get("retreating") is False
    ):
        raise RuntimeError(f"CUnit {public_cunit_id} is not safely movable")
    preview_step = f"preview-move-army-{public_cunit_id}-to-{target_province_id}"
    move_step = f"move-army-{public_cunit_id}-to-{target_province_id}"
    preview = service.execute_step(
        preview_step, expected_revision=rejoin_live._snapshot_revision(before)
    )
    after_preview = service.snapshot()
    if not join_live._same_paused_binding(before, after_preview):
        raise RuntimeError("move preview changed the paused binding")
    move = service.move_army(
        public_cunit_id,
        target_province_id,
        expected_revision=rejoin_live._snapshot_revision(after_preview),
    )

    def applied(army: dict[str, object]) -> bool:
        route = army.get("route_province_ids")
        if army.get("current_province_id") == target_province_id:
            return route == [] and army.get("move_target_province_id") is None
        return (
            army.get("move_target_province_id") == target_province_id
            and isinstance(route, list)
            and bool(route)
            and route[-1] == target_province_id
        )

    after = _wait_for_army_condition(
        service,
        after_preview,
        public_cunit_id=public_cunit_id,
        timeout_seconds=timeout_seconds,
        predicate=applied,
    )
    action = move.get("war_action") if isinstance(move, dict) else None
    action = action if isinstance(action, dict) else {}
    after_army = _army(after, public_cunit_id)
    checks = {
        "preview_available": isinstance(preview, dict)
        and isinstance(preview.get("route_preview"), dict)
        and preview["route_preview"].get("status") == "available",
        "move_accepted": isinstance(move, dict)
        and move.get("accepted") is True
        and action.get("army_id") == public_cunit_id
        and action.get("target_province_id") == target_province_id,
        "same_paused_date": before.get("date_raw") == after.get("date_raw")
        and after.get("paused") is True,
        "fresh_revision": rejoin_live._snapshot_revision(after)
        > rejoin_live._snapshot_revision(before),
        "semantic_target_applied": applied(after_army),
        "control_preserved": after_army.get("controllable") is True,
    }
    proof = {
        "preview_step": preview_step,
        "move_step": move_step,
        "before_army": before_army,
        "preview": preview,
        "move": move,
        "after_army": after_army,
        "checks": checks,
        "ok": all(checks.values()),
    }
    if proof["ok"] is not True:
        raise RuntimeError(f"CUnit {public_cunit_id} move proof failed")
    return after, proof


def _run_seed_switch_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    seed_timeout: float,
    expected_date_raw: int,
    from_character_id: int,
    to_character_id: int,
    switch_effect: str,
    clear_effect: str,
    switch_marker: str,
    clear_marker: str,
    name: str,
    precheck: Callable[[dict[str, object]], dict[str, object]],
    postcheck: Callable[[dict[str, object]], dict[str, object]],
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        _driver: NativeHeadlessGameplayDriver,
        session_done: threading.Event,
        session_state: dict[str, object],
    ) -> dict[str, object]:
        initial = service.snapshot()
        initial_proof = precheck(initial)
        if not (
            owner_live._played_character_id(initial) == from_character_id
            and initial.get("date_raw") == expected_date_raw
            and initial.get("paused") is True
            and initial_proof.get("ok") is True
        ):
            return {
                "ok": False,
                "outcome": "seed_switch_precondition_drift",
                "initial_snapshot": initial,
                "precondition_proof": initial_proof,
                "error": "seed switch precondition differs",
            }
        debug_log = spec.profile_dir / "logs" / "debug.log"
        switch_offset = owner_live._debug_log_offset(debug_log)
        switch_identity = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), switch_effect
        )
        deadline = time.monotonic() + seed_timeout
        switched: dict[str, object] | None = None
        switch_marker_observed = False
        while time.monotonic() < deadline:
            switch_marker_observed = owner_live._debug_marker_observed(
                debug_log, switch_marker, offset=switch_offset
            )
            candidate = service.snapshot()
            if (
                switch_marker_observed
                and owner_live._played_character_id(candidate) == to_character_id
            ):
                switched = candidate
                break
            if session_done.is_set():
                raise RuntimeError(
                    str(session_state.get("error") or "seed session ended")
                )
            time.sleep(0.05)
        if switched is None or switched.get("date_raw") != expected_date_raw:
            return {
                "ok": False,
                "outcome": "seed_switch_target_not_observed",
                "initial_snapshot": initial,
                "precondition_proof": initial_proof,
                "switch_marker_observed": switch_marker_observed,
                "error": "seed switch marker/player/date was not observed",
            }
        noop_after_switch = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), owner_live.SEED_NOOP_INBOX
        )
        poll_driver = DataModGameplayDriver(
            spec.profile_dir,
            request_timeout_seconds=seed_timeout,
            poll_interval_seconds=0.05,
        )
        switch_polls = [poll_driver.take_snapshot(), poll_driver.take_snapshot()]
        polls_ok = bool(
            len({row.get("request_id") for row in switch_polls}) == 2
            and all(row.get("player_id") == to_character_id for row in switch_polls)
            and switch_polls[0].get("total_days")
            == switch_polls[1].get("total_days")
        )
        if not polls_ok:
            raise RuntimeError("seed switch two-poll proof was not stable")

        clear_offset = owner_live._debug_log_offset(debug_log)
        clear_identity = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), clear_effect
        )
        clear_deadline = time.monotonic() + seed_timeout
        clear_marker_observed = False
        while time.monotonic() < clear_deadline:
            clear_marker_observed = owner_live._debug_marker_observed(
                debug_log, clear_marker, offset=clear_offset
            )
            if clear_marker_observed:
                break
            if session_done.is_set():
                raise RuntimeError(
                    str(session_state.get("error") or "seed session ended")
                )
            time.sleep(0.05)
        if not clear_marker_observed:
            raise RuntimeError("seed switch guard-clear marker was not observed")
        clear_polls = [poll_driver.take_snapshot(), poll_driver.take_snapshot()]
        if not (
            len({row.get("request_id") for row in clear_polls}) == 2
            and all(row.get("player_id") == to_character_id for row in clear_polls)
            and clear_polls[0].get("total_days") == clear_polls[1].get("total_days")
        ):
            raise RuntimeError("seed clear two-poll proof was not stable")
        final_noop = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), owner_live.SEED_NOOP_INBOX
        )
        final = service.snapshot()
        final_proof = postcheck(final)
        if not (
            owner_live._played_character_id(final) == to_character_id
            and final.get("date_raw") == expected_date_raw
            and final.get("paused") is True
            and final_proof.get("ok") is True
        ):
            return {
                "ok": False,
                "outcome": "seed_switch_postcondition_drift",
                "initial_snapshot": initial,
                "precondition_proof": initial_proof,
                "final_snapshot": final,
                "postcondition_proof": final_proof,
                "error": "seed switch postcondition differs",
            }
        checkpoint = _save_archive(
            service, final, archive_name=f"xar_{name}_switch.ck3"
        )
        return {
            "ok": True,
            "outcome": "same_date_player_switch",
            "initial_snapshot": initial,
            "precondition_proof": initial_proof,
            "switched_snapshot": switched,
            "final_snapshot": final,
            "postcondition_proof": final_proof,
            "inbox_protocol": {
                "switch_marker": switch_marker,
                "switch_marker_observed": switch_marker_observed,
                "clear_marker": clear_marker,
                "clear_marker_observed": clear_marker_observed,
                "switch_effect": switch_identity,
                "noop_after_switch": noop_after_switch,
                "clear_effect": clear_identity,
                "final_noop": final_noop,
                "switch_polls": switch_polls,
                "clear_polls": clear_polls,
            },
            "checkpoint": checkpoint,
            "date_raw": expected_date_raw,
        }

    try:
        return ai_live._run_managed_session(
            spec=spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            name=f"xar-three-cunit-{name}-seed",
            fixture=True,
            body=body,
        )
    finally:
        owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), owner_live.SEED_NOOP_INBOX
        )


def _all_precontact_proof(
    snapshot: dict[str, object],
    *,
    sibling_cunit_id: int | None = None,
) -> dict[str, object]:
    identities = [OPPOSITE_CUNIT_ID, REQUESTER_CUNIT_ID, ANCHOR_CUNIT_ID]
    if sibling_cunit_id is not None:
        identities.append(sibling_cunit_id)
    armies: dict[str, object] = {}
    checks: dict[str, bool] = {"paused": snapshot.get("paused") is True}
    for public_id in identities:
        try:
            army = _army(snapshot, public_id)
        except RuntimeError:
            army = {}
        armies[str(public_id)] = army
        checks[f"cunit_{public_id}_not_in_combat"] = (
            army.get("in_combat") is False
        )
        checks[f"cunit_{public_id}_not_retreating"] = (
            army.get("retreating") is False
        )
    return {"armies": armies, "checks": checks, "ok": all(checks.values())}


def _run_route_clear_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    route_timeout: float,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        driver: NativeHeadlessGameplayDriver,
        _session_done: threading.Event,
        _session_state: dict[str, object],
    ) -> dict[str, object]:
        initial = service.snapshot()
        exact_build = rejoin_live._exact_build_proof(
            driver.capabilities(), _sha256_file(spec.game_exe)
        )
        capability = join_live._capability_proof(driver.capabilities())
        geometry = join_live._initial_geometry_proof(initial)
        if not (
            exact_build.get("ok") is True
            and capability.get("ok") is True
            and geometry.get("ok") is True
            and owner_live._played_character_id(initial) == ORIGINAL_CHARACTER_ID
        ):
            return {
                "ok": False,
                "outcome": "precontact_source_geometry_drift",
                "initial_snapshot": initial,
                "exact_build_proof": exact_build,
                "capability_proof": capability,
                "geometry_proof": geometry,
                "error": "precontact route-clear gate differs",
            }
        preview_step = (
            f"preview-move-army-{OPPOSITE_CUNIT_ID}-to-{CONTACT_PROVINCE_ID}"
        )
        preview = service.execute_step(
            preview_step,
            expected_revision=rejoin_live._snapshot_revision(initial),
        )
        after_preview = service.snapshot()
        if not join_live._same_paused_binding(initial, after_preview):
            raise RuntimeError("attacker route preview changed paused binding")
        move = service.move_army(
            OPPOSITE_CUNIT_ID,
            CONTACT_PROVINCE_ID,
            expected_revision=rejoin_live._snapshot_revision(after_preview),
        )
        cleared = join_live._wait_for_route_clear(
            service, after_preview, timeout_seconds=route_timeout
        )
        route_proof = join_live._route_clear_proof(
            after_preview, preview, move, cleared
        )
        precontact = _all_precontact_proof(cleared)
        if not (route_proof.get("ok") is True and precontact.get("ok") is True):
            return {
                "ok": False,
                "outcome": "attacker_route_clear_postcondition_drift",
                "initial_snapshot": initial,
                "route_clear_proof": route_proof,
                "precontact_proof": precontact,
                "error": "attacker route clear did not preserve precontact",
            }
        checkpoint = _save_archive(
            service, cleared, archive_name="xar_three_cunit_route_cleared.ck3"
        )
        return {
            "ok": True,
            "outcome": "attacker_route_cleared",
            "initial_snapshot": initial,
            "exact_build_proof": exact_build,
            "capability_proof": capability,
            "geometry_proof": geometry,
            "preview": preview,
            "move": move,
            "cleared_snapshot": cleared,
            "route_clear_proof": route_proof,
            "precontact_proof": precontact,
            "checkpoint": checkpoint,
            "date_raw": rejoin_live._snapshot_date(cleared),
            "commands": [preview_step, f"move-army-{OPPOSITE_CUNIT_ID}-to-{CONTACT_PROVINCE_ID}", "save-checkpoint"],
        }

    return ai_live._run_managed_session(
        spec=spec,
        config=config,
        timeout=timeout,
        readiness_timeout=readiness_timeout,
        name="xar-three-cunit-route-clear-production",
        fixture=False,
        body=body,
    )


def _run_split_route_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    route_timeout: float,
    max_split_wait_days: int,
    expected_date_raw: int,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        driver: NativeHeadlessGameplayDriver,
        session_done: threading.Event,
        session_state: dict[str, object],
    ) -> dict[str, object]:
        initial = service.snapshot()
        initial_control = _precontact_army_proof(
            initial,
            ANCHOR_CUNIT_ID,
            owner_character_id=RETAINED_CHARACTER_ID,
            controllable=True,
        )
        exact_build = rejoin_live._exact_build_proof(
            driver.capabilities(), _sha256_file(spec.game_exe)
        )
        if not (
            owner_live._played_character_id(initial) == RETAINED_CHARACTER_ID
            and initial.get("date_raw") == expected_date_raw
            and initial_control.get("ok") is True
            and exact_build.get("ok") is True
        ):
            return {
                "ok": False,
                "outcome": "anchor_not_controllable_before_split",
                "initial_snapshot": initial,
                "anchor_control_proof": initial_control,
                "exact_build_proof": exact_build,
                "commands": [],
                "error": "CUnit 33554657 is not controllable before split",
            }

        snapshot = initial
        commands: list[str] = []
        advances: list[dict[str, object]] = []
        wait_frames: list[dict[str, object]] = []
        for day_index in range(max_split_wait_days + 1):
            anchor = _army(snapshot, ANCHOR_CUNIT_ID)
            precontact = _all_precontact_proof(snapshot)
            frame = {
                "day_index": day_index,
                "snapshot": snapshot,
                "anchor": anchor,
                "precontact_proof": precontact,
            }
            wait_frames.append(frame)
            if precontact.get("ok") is not True:
                return {
                    "ok": False,
                    "outcome": "contact_before_split",
                    "initial_snapshot": initial,
                    "anchor_control_proof": initial_control,
                    "wait_frames": wait_frames,
                    "commands": commands,
                    "advances": advances,
                    "error": "contact occurred before split",
                }
            if not (
                anchor.get("controllable") is True
                and anchor.get("owner_character_id") == RETAINED_CHARACTER_ID
            ):
                return {
                    "ok": False,
                    "outcome": "anchor_control_drift_before_split",
                    "initial_snapshot": initial,
                    "anchor_control_proof": initial_control,
                    "wait_frames": wait_frames,
                    "commands": commands,
                    "advances": advances,
                    "error": "anchor control drifted before split",
                }
            route = anchor.get("route_province_ids")
            if isinstance(route, list) and not route:
                break
            if day_index == max_split_wait_days:
                return {
                    "ok": False,
                    "outcome": "anchor_movement_not_settled_within_bound",
                    "initial_snapshot": initial,
                    "anchor_control_proof": initial_control,
                    "wait_frames": wait_frames,
                    "commands": commands,
                    "advances": advances,
                    "error": "anchor did not reach a stable split frame",
                }
            snapshot, advance = rejoin_live._advance_one_day(
                service,
                snapshot,
                lambda: _wait_after_advance(
                    driver,
                    session_done=session_done,
                    session_state=session_state,
                    readiness_timeout=readiness_timeout,
                ),
            )
            advances.append(advance)
            commands.append("life-advance")

        # This proof is intentionally immediately before the first split
        # command.  No split is submitted when CUnit335 is not controllable.
        before_split_control = _precontact_army_proof(
            snapshot,
            ANCHOR_CUNIT_ID,
            owner_character_id=RETAINED_CHARACTER_ID,
            controllable=True,
        )
        split_step = split_army_half_step(ANCHOR_CUNIT_ID)
        capability = _stage_capability_proof(
            driver.capabilities(),
            exact_steps=[split_step, "life-advance", "save-checkpoint"],
            required=[SPLIT_ARMY_HALF_CAPABILITY],
        )
        if not (
            before_split_control.get("ok") is True
            and capability.get("ok") is True
        ):
            return {
                "ok": False,
                "outcome": "split_precondition_or_capability_not_ready",
                "initial_snapshot": initial,
                "before_split_snapshot": snapshot,
                "anchor_control_proof": before_split_control,
                "capability_proof": capability,
                "wait_frames": wait_frames,
                "commands": commands,
                "advances": advances,
                "error": "split gate is not ready",
            }
        split_result = service.execute_step(
            split_step,
            expected_revision=rejoin_live._snapshot_revision(snapshot),
        )
        commands.append(split_step)
        before_ids = {
            int(row["army_id"])
            for row in snapshot.get("player_armies", [])
            if isinstance(row, dict)
            and row.get("controllable") is True
            and isinstance(row.get("army_id"), int)
            and not isinstance(row.get("army_id"), bool)
        }
        deadline = time.monotonic() + route_timeout
        after_split: dict[str, object] | None = None
        while time.monotonic() < deadline:
            candidate = service.snapshot()
            candidate_ids = {
                int(row["army_id"])
                for row in candidate.get("player_armies", [])
                if isinstance(row, dict)
                and row.get("controllable") is True
                and isinstance(row.get("army_id"), int)
                and not isinstance(row.get("army_id"), bool)
            }
            if (
                candidate.get("paused") is True
                and candidate.get("date_raw") == snapshot.get("date_raw")
                and candidate.get("episode_run_id")
                == snapshot.get("episode_run_id")
                and ANCHOR_CUNIT_ID in candidate_ids
                and len(candidate_ids - before_ids) == 1
            ):
                after_split = candidate
                break
            time.sleep(0.05)
        if after_split is None:
            return {
                "ok": False,
                "outcome": "split_sibling_not_materialized_same_day",
                "initial_snapshot": initial,
                "before_split_snapshot": snapshot,
                "anchor_control_proof": before_split_control,
                "capability_proof": capability,
                "split_result": split_result,
                "wait_frames": wait_frames,
                "commands": commands,
                "advances": advances,
                "error": "split did not expose exact +1 controllable CUnit",
            }
        split_proof = _split_postcondition_proof(
            snapshot, after_split, split_result
        )
        sibling = split_proof.get("sibling_cunit_id")
        if split_proof.get("ok") is not True or not isinstance(sibling, int):
            return {
                "ok": False,
                "outcome": "split_postcondition_drift",
                "initial_snapshot": initial,
                "before_split_snapshot": snapshot,
                "split_snapshot": after_split,
                "split_proof": split_proof,
                "commands": commands,
                "advances": advances,
                "error": "split exact delta proof failed",
            }
        route_capability = _stage_capability_proof(
            driver.capabilities(),
            exact_steps=[
                f"preview-move-army-{ANCHOR_CUNIT_ID}-to-{CONTACT_PROVINCE_ID}",
                f"move-army-{ANCHOR_CUNIT_ID}-to-{CONTACT_PROVINCE_ID}",
                f"preview-move-army-{sibling}-to-{CONTACT_PROVINCE_ID}",
                f"move-army-{sibling}-to-{CONTACT_PROVINCE_ID}",
            ],
            required=[PREVIEW_MOVE_ARMY_CAPABILITY, MOVE_ARMY_CAPABILITY],
        )
        if route_capability.get("ok") is not True:
            return {
                "ok": False,
                "outcome": "split_route_capability_not_ready",
                "initial_snapshot": initial,
                "before_split_snapshot": snapshot,
                "split_snapshot": after_split,
                "split_proof": split_proof,
                "route_capability_proof": route_capability,
                "commands": commands,
                "advances": advances,
                "error": "dynamic sibling route capability is not ready",
            }
        snapshot, anchor_move = _move_to_target(
            service,
            after_split,
            public_cunit_id=ANCHOR_CUNIT_ID,
            target_province_id=CONTACT_PROVINCE_ID,
            timeout_seconds=route_timeout,
        )
        commands.extend([anchor_move["preview_step"], anchor_move["move_step"]])
        snapshot, sibling_move = _move_to_target(
            service,
            snapshot,
            public_cunit_id=sibling,
            target_province_id=CONTACT_PROVINCE_ID,
            timeout_seconds=route_timeout,
        )
        commands.extend([sibling_move["preview_step"], sibling_move["move_step"]])
        routed_precontact = _all_precontact_proof(
            snapshot, sibling_cunit_id=sibling
        )
        if routed_precontact.get("ok") is not True:
            return {
                "ok": False,
                "outcome": "split_routes_lost_precontact",
                "split_proof": split_proof,
                "anchor_move": anchor_move,
                "sibling_move": sibling_move,
                "routed_precontact_proof": routed_precontact,
                "commands": commands,
                "advances": advances,
                "error": "split routes did not preserve precontact",
            }
        checkpoint = _save_archive(
            service, snapshot, archive_name=SPLIT_ARCHIVE_NAME
        )
        commands.append("save-checkpoint")
        return {
            "ok": True,
            "outcome": "retained_anchor_split_and_routed",
            "initial_snapshot": initial,
            "exact_build_proof": exact_build,
            "capability_proof": capability,
            "initial_anchor_control_proof": initial_control,
            "before_split_control_proof": before_split_control,
            "wait_frames": wait_frames,
            "split_result": split_result,
            "split_snapshot": after_split,
            "split_proof": split_proof,
            "route_capability_proof": route_capability,
            "sibling_cunit_id": sibling,
            "anchor_move": anchor_move,
            "sibling_move": sibling_move,
            "routed_snapshot": snapshot,
            "routed_precontact_proof": routed_precontact,
            "checkpoint": checkpoint,
            "date_raw": rejoin_live._snapshot_date(snapshot),
            "commands": commands,
            "advances": advances,
        }

    return ai_live._run_managed_session(
        spec=spec,
        config=config,
        timeout=timeout,
        readiness_timeout=readiness_timeout,
        name="xar-three-cunit-split-route-production",
        fixture=False,
        body=body,
    )


def _battle_control_frame(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        return {}
    nested = result.get("battle_control_snapshot")
    if isinstance(nested, dict):
        return nested
    return result if "battle_control_ready" in result else {}


def _owner_subset_control_proof(
    result: object,
    *,
    sibling_cunit_id: int,
    combat_id: int,
    retained_same_side_order: list[int] | None = None,
) -> dict[str, object]:
    frame = _battle_control_frame(result)
    legality = frame.get("legality")
    legality = legality if isinstance(legality, dict) else {}
    expected_retained = (
        list(retained_same_side_order)
        if retained_same_side_order is not None
        else [ANCHOR_CUNIT_ID, sibling_cunit_id]
    )
    checks = {
        "available_control_frame": frame.get("status") == "available"
        and frame.get("battle_control_ready") is True,
        "selected_requester_owned_by_player": frame.get(
            "selected_public_cunit_id"
        )
        == REQUESTER_CUNIT_ID
        and frame.get("selected_owner_character_id") == REQUESTER_CHARACTER_ID,
        "same_combat_side": frame.get("combat_id") == combat_id
        and frame.get("side_index") == SIDE_INDEX,
        "owner_subset_scope": frame.get("side_scope") == "owner_subset",
        "affected_exactly_requester": frame.get(
            "affected_public_cunit_ids_in_stored_order"
        )
        == [REQUESTER_CUNIT_ID],
        "retained_exactly_two": frame.get(
            "unaffected_same_side_public_cunit_ids_in_stored_order"
        )
        == expected_retained,
        "native_retreat_legal_now": legality.get("status") == "available"
        and legality.get("native_boolean") is True
        and legality.get("legal_now") is True,
    }
    return {
        "frame": frame,
        "expected_retained": expected_retained,
        "legality": legality,
        "checks": checks,
        "structural_ok": all(
            value
            for key, value in checks.items()
            if key != "native_retreat_legal_now"
        ),
        "legal_now": checks["native_retreat_legal_now"],
        "ok": all(checks.values()),
    }


def _read_only_bundle_transient(error: BaseException) -> bool:
    detail = str(error)
    return bool(
        rejoin_live._is_read_only_heartbeat_transient(error)
        or "battle-control snapshot changed; retry after heartbeat" in detail
        or "battle-control revision mismatch: expected " in detail
        or "battle-control query crossed a snapshot revision" in detail
        or "requester reinforcement query crossed a snapshot revision" in detail
    )


def _query_requester_membership(
    service: GameplayBridgeService,
    snapshot: dict[str, object],
    *,
    retry_attempts: int = 6,
    retry_timeout_seconds: float = 8.0,
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    if retry_attempts <= 0 or retry_timeout_seconds <= 0:
        raise ValueError("requester query retry bounds must be positive")
    rejoin_live._assert_paused(snapshot)
    fixed_date = rejoin_live._snapshot_date(snapshot)
    fixed_episode = snapshot.get("episode_run_id")
    current = snapshot
    retries: list[dict[str, object]] = []
    deadline = time.monotonic() + retry_timeout_seconds
    for attempt in range(1, retry_attempts + 1):
        try:
            result = service.query_battle_reinforcement_assignment_v1(
                REQUESTER_CUNIT_ID,
                expected_revision=rejoin_live._snapshot_revision(current),
            )
            frame = rejoin_live._reinforcement_frame(result)
            if not (
                frame.get("snapshot_revision") == current.get("native_revision")
                and frame.get("observed_date_raw") == fixed_date
            ):
                raise RuntimeError(
                    "requester reinforcement query crossed a snapshot revision"
                )
            return current, result, retries
        except BaseException as error:
            if not _read_only_bundle_transient(error):
                raise
            if attempt >= retry_attempts or time.monotonic() >= deadline:
                raise RuntimeError(
                    "requester reinforcement retry bound exhausted"
                ) from error
            fresh = rejoin_live._wait_for_fresh_paused_observation(
                service, current, deadline=deadline
            )
            if (
                rejoin_live._snapshot_date(fresh) != fixed_date
                or fresh.get("episode_run_id") != fixed_episode
            ):
                raise RuntimeError(
                    "requester reinforcement retry crossed date/episode"
                ) from error
            retries.append(
                {
                    "attempt": attempt,
                    "transient": str(error),
                    "stale_snapshot_id": current.get("snapshot_id"),
                    "fresh_snapshot_id": fresh.get("snapshot_id"),
                    "date_raw": fixed_date,
                    "episode_run_id": fixed_episode,
                    "restart_scope": "requester_membership_query",
                }
            )
            current = fresh
    raise RuntimeError("unreachable requester membership retry state")


def _query_three_cunit_combat_bundle(
    service: GameplayBridgeService,
    snapshot: dict[str, object],
    *,
    sibling_cunit_id: int,
    combat_id: int,
    retry_attempts: int = 6,
    retry_timeout_seconds: float = 8.0,
) -> tuple[
    dict[str, object],
    list[dict[str, object]],
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
]:
    rejoin_live._assert_paused(snapshot)
    fixed_date = rejoin_live._snapshot_date(snapshot)
    fixed_episode = snapshot.get("episode_run_id")
    current = snapshot
    retries: list[dict[str, object]] = []
    deadline = time.monotonic() + retry_timeout_seconds
    for attempt in range(1, retry_attempts + 1):
        try:
            revision = rejoin_live._snapshot_revision(current)
            results = [
                service.query_battle_reinforcement_assignment_v1(
                    public_id, expected_revision=revision
                )
                for public_id in (
                    REQUESTER_CUNIT_ID,
                    ANCHOR_CUNIT_ID,
                    sibling_cunit_id,
                )
            ]
            battle = rejoin_live._battle_frame(
                service.query_battle_transition_v1(
                    combat_id, expected_revision=revision
                )
            )
            control = service.query_battle_control_snapshot_v1(
                REQUESTER_CUNIT_ID, expected_revision=revision
            )
            return current, results, battle, control, retries
        except BaseException as error:
            if not _read_only_bundle_transient(error):
                raise
            if attempt >= retry_attempts or time.monotonic() >= deadline:
                raise RuntimeError(
                    "three-CUnit read-only bundle retry bound exhausted"
                ) from error
            fresh = rejoin_live._wait_for_fresh_paused_observation(
                service, current, deadline=deadline
            )
            if (
                rejoin_live._snapshot_date(fresh) != fixed_date
                or fresh.get("episode_run_id") != fixed_episode
            ):
                raise RuntimeError(
                    "three-CUnit read-only bundle crossed date/episode"
                ) from error
            retries.append(
                {
                    "attempt": attempt,
                    "transient": str(error),
                    "stale_snapshot_id": current.get("snapshot_id"),
                    "fresh_snapshot_id": fresh.get("snapshot_id"),
                    "date_raw": fixed_date,
                    "episode_run_id": fixed_episode,
                    "restart_scope": "three_memberships_then_battle_then_control",
                }
            )
            current = fresh
    raise RuntimeError("unreachable three-CUnit observation retry state")


def _post_retreat_three_cunit_proof(
    snapshot: dict[str, object],
    battle: dict[str, object],
    *,
    sibling_cunit_id: int,
    combat_id: int,
    expected_date_raw: int,
    retained_same_side_order: list[int] | None = None,
) -> dict[str, object]:
    roster = _retained_combat_roster_proof(
        battle,
        sibling_cunit_id=sibling_cunit_id,
        combat_id=combat_id,
        retained_same_side_order=retained_same_side_order,
    )
    try:
        requester = _army(snapshot, REQUESTER_CUNIT_ID)
        anchor = _army(snapshot, ANCHOR_CUNIT_ID)
        sibling = _army(snapshot, sibling_cunit_id)
    except RuntimeError:
        requester, anchor, sibling = {}, {}, {}
    route = requester.get("route_province_ids")
    checks = {
        "same_paused_date": snapshot.get("paused") is True
        and snapshot.get("date_raw") == expected_date_raw,
        "requester_retreating": requester.get("controllable") is True
        and requester.get("in_combat") is False
        and requester.get("retreating") is True
        and requester.get("move_target_province_id") == RETREAT_PROVINCE_ID
        and isinstance(route, list)
        and bool(route)
        and route[-1] == RETREAT_PROVINCE_ID,
        "retained_anchor_stays_in_combat": anchor.get("in_combat") is True
        and anchor.get("retreating") is False,
        "retained_sibling_stays_in_combat": sibling.get("in_combat") is True
        and sibling.get("retreating") is False,
        "strict_retained_roster": roster.get("ok") is True,
    }
    return {
        "requester_army": requester,
        "anchor_army": anchor,
        "sibling_army": sibling,
        "roster_proof": roster,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_contact_retreat_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    postcondition_timeout: float,
    max_contact_days: int,
    expected_date_raw: int,
    sibling_cunit_id: int,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        driver: NativeHeadlessGameplayDriver,
        session_done: threading.Event,
        session_state: dict[str, object],
    ) -> dict[str, object]:
        initial = service.snapshot()
        requester_control = _precontact_army_proof(
            initial,
            REQUESTER_CUNIT_ID,
            owner_character_id=REQUESTER_CHARACTER_ID,
            controllable=True,
        )
        exact_build = rejoin_live._exact_build_proof(
            driver.capabilities(), _sha256_file(spec.game_exe)
        )
        capability = rejoin_live._capability_proof(driver.capabilities())
        if not (
            initial.get("date_raw") == expected_date_raw
            and owner_live._played_character_id(initial) == REQUESTER_CHARACTER_ID
            and requester_control.get("ok") is True
            and exact_build.get("ok") is True
            and capability.get("ok") is True
        ):
            return {
                "ok": False,
                "outcome": "requester_control_not_ready_before_contact",
                "initial_snapshot": initial,
                "requester_control_proof": requester_control,
                "exact_build_proof": exact_build,
                "capability_proof": capability,
                "commands": [],
                "error": "requester is not production-controlled precontact",
            }
        snapshot = initial
        observations: list[dict[str, object]] = []
        advances: list[dict[str, object]] = []
        commands: list[str] = []
        combat_id: int | None = None
        parent_proof: dict[str, object] | None = None
        control_result: dict[str, object] | None = None
        control_proof: dict[str, object] | None = None
        pre_battle: dict[str, object] | None = None
        for day_index in range(max_contact_days + 1):
            snapshot, result, requester_retries = _query_requester_membership(
                service, snapshot
            )
            frame = rejoin_live._reinforcement_frame(result)
            candidate_combat_id = join_live._active_combat_id(frame)
            observation: dict[str, object] = {
                "day_index": day_index,
                "snapshot": snapshot,
                "requester_result": result,
                "candidate_combat_id": candidate_combat_id,
                "requester_query_retries": requester_retries,
            }
            if candidate_combat_id is not None:
                combat_id = candidate_combat_id
                snapshot, results, battle, control, retries = (
                    _query_three_cunit_combat_bundle(
                        service,
                        snapshot,
                        sibling_cunit_id=sibling_cunit_id,
                        combat_id=combat_id,
                    )
                )
                candidate_parent = _three_cunit_parent_proof(
                    snapshot,
                    results,
                    battle,
                    sibling_cunit_id=sibling_cunit_id,
                    combat_id=combat_id,
                )
                retained_order = candidate_parent.get("retained_same_side_order")
                retained_order = (
                    retained_order if isinstance(retained_order, list) else None
                )
                candidate_control = _owner_subset_control_proof(
                    control,
                    sibling_cunit_id=sibling_cunit_id,
                    combat_id=combat_id,
                    retained_same_side_order=retained_order,
                )
                observation.update(
                    {
                        "snapshot": snapshot,
                        "membership_results": results,
                        "battle": battle,
                        "control": control,
                        "parent_proof": candidate_parent,
                        "control_proof": candidate_control,
                        "observation_retries": retries,
                    }
                )
                observations.append(observation)
                if candidate_parent.get("checks", {}).get(
                    "same_active_combat_roster"
                ) is not True:
                    return {
                        "ok": False,
                        "outcome": "three_cunit_contact_roster_drift",
                        "initial_snapshot": initial,
                        "requester_control_proof": requester_control,
                        "combat_id": combat_id,
                        "observations": observations,
                        "advances": advances,
                        "commands": commands,
                        "error": "contact did not contain exact three-CUnit side",
                    }
                if candidate_parent.get("ok") is not True:
                    parent_proof = candidate_parent
                    control_result = control
                    control_proof = candidate_control
                    pre_battle = battle
                elif candidate_control.get("structural_ok") is not True:
                    return {
                        "ok": False,
                        "outcome": "owner_subset_control_scope_drift",
                        "initial_snapshot": initial,
                        "combat_id": combat_id,
                        "parent_proof": candidate_parent,
                        "control_proof": candidate_control,
                        "observations": observations,
                        "advances": advances,
                        "commands": commands,
                        "error": "owner-subset control is not exactly 357",
                    }
                elif candidate_control.get("legal_now") is True:
                    parent_proof = candidate_parent
                    control_result = control
                    control_proof = candidate_control
                    pre_battle = battle
                    break
                else:
                    parent_proof = candidate_parent
                    control_result = control
                    control_proof = candidate_control
                    pre_battle = battle
            else:
                precontact = _all_precontact_proof(
                    snapshot, sibling_cunit_id=sibling_cunit_id
                )
                observation["precontact_proof"] = precontact
                observations.append(observation)
                if precontact.get("ok") is not True:
                    return {
                        "ok": False,
                        "outcome": "combat_membership_unavailable_after_contact",
                        "initial_snapshot": initial,
                        "observations": observations,
                        "advances": advances,
                        "commands": commands,
                        "error": "semantic contact lacks requester CombatID",
                    }
            if day_index == max_contact_days:
                outcome = (
                    "fixture_subunit_structure_insufficient"
                    if combat_id is not None
                    and parent_proof is not None
                    and parent_proof.get("ok") is not True
                    else "retreat_legality_not_ready_within_contact_bound"
                    if combat_id is not None
                    else "three_cunit_contact_not_observed_within_bound"
                )
                return {
                    "ok": False,
                    "outcome": outcome,
                    "initial_snapshot": initial,
                    "combat_id": combat_id,
                    "parent_proof": parent_proof,
                    "control_result": control_result,
                    "control_proof": control_proof,
                    "pre_battle": pre_battle,
                    "observations": observations,
                    "advances": advances,
                    "commands": commands,
                    "error": outcome,
                }
            snapshot, advance = rejoin_live._advance_one_day(
                service,
                snapshot,
                lambda: _wait_after_advance(
                    driver,
                    session_done=session_done,
                    session_state=session_state,
                    readiness_timeout=readiness_timeout,
                ),
            )
            advances.append(advance)
            commands.append("life-advance")

        if not (
            isinstance(combat_id, int)
            and parent_proof is not None
            and parent_proof.get("ok") is True
            and control_proof is not None
            and control_proof.get("ok") is True
            and pre_battle is not None
        ):
            raise RuntimeError("retreat loop escaped without all hard gates")
        retained_order = parent_proof.get("retained_same_side_order")
        if not isinstance(retained_order, list):
            raise RuntimeError("three-CUnit parent proof lost retained order")

        # Nothing above this line submitted a retreat.  The exact three-row
        # native parent proof and exact owner-subset control proof are the last
        # two gates immediately before preview/order.
        preview = service.preview_active_combat_retreat_v1(
            REQUESTER_CUNIT_ID,
            RETREAT_PROVINCE_ID,
            expected_revision=rejoin_live._snapshot_revision(snapshot),
        )
        target_preview = preview.get("target_preview")
        target_preview = target_preview if isinstance(target_preview, dict) else {}
        token = target_preview.get("candidate_token")
        if not (
            preview.get("status") == "available"
            and preview.get("action_ready") is True
            and isinstance(token, str)
            and bool(token)
        ):
            return {
                "ok": False,
                "outcome": "retreat_preview_not_ready_after_three_row_gate",
                "combat_id": combat_id,
                "parent_proof": parent_proof,
                "control_proof": control_proof,
                "preview": preview,
                "observations": observations,
                "advances": advances,
                "commands": commands,
                "error": "retreat preview is not action-ready",
            }
        order = service.order_active_combat_retreat_v1(
            REQUESTER_CUNIT_ID,
            expected_revision=int(preview["source_binding"]["revision"]),
            expected_combat_id=combat_id,
            expected_side_index=SIDE_INDEX,
            expected_scope="owner_subset",
            target_province_id=RETREAT_PROVINCE_ID,
            candidate_token=token,
        )
        commands.extend(
            [
                f"preview-active-combat-retreat-v1-{REQUESTER_CUNIT_ID}-to-{RETREAT_PROVINCE_ID}",
                f"order-active-combat-retreat-v1-{REQUESTER_CUNIT_ID}",
            ]
        )
        if not (
            order.get("accepted") is True
            and order.get("status") == "accepted_verification_pending"
        ):
            raise RuntimeError("owner-subset retreat order was not accepted")
        retreat_date = rejoin_live._snapshot_date(snapshot)
        deadline = time.monotonic() + postcondition_timeout
        post_frames: list[dict[str, object]] = []
        post_snapshot: dict[str, object] | None = None
        post_battle: dict[str, object] | None = None
        post_proof: dict[str, object] | None = None
        while time.monotonic() < deadline:
            candidate = service.snapshot()
            row: dict[str, object] = {"snapshot": candidate}
            if retreat_live._retreat_semantic_ready(
                candidate, REQUESTER_CUNIT_ID, RETREAT_PROVINCE_ID
            ):
                battle = rejoin_live._battle_frame(
                    service.query_battle_transition_v1(
                        combat_id,
                        expected_revision=rejoin_live._snapshot_revision(candidate),
                    )
                )
                proof = _post_retreat_three_cunit_proof(
                    candidate,
                    battle,
                    sibling_cunit_id=sibling_cunit_id,
                    combat_id=combat_id,
                    expected_date_raw=retreat_date,
                    retained_same_side_order=retained_order,
                )
                row.update({"battle": battle, "proof": proof})
                if proof.get("ok") is True:
                    post_snapshot, post_battle, post_proof = candidate, battle, proof
                    post_frames.append(row)
                    break
            post_frames.append(row)
            time.sleep(0.05)
        if post_snapshot is None or post_battle is None or post_proof is None:
            return {
                "ok": False,
                "outcome": "three_cunit_owner_subset_postcondition_timeout",
                "combat_id": combat_id,
                "parent_proof": parent_proof,
                "control_proof": control_proof,
                "preview": preview,
                "order": order,
                "post_frames": post_frames,
                "observations": observations,
                "advances": advances,
                "commands": commands,
                "error": "retreat did not retain exactly two anchors",
            }
        checkpoint = _save_archive(
            service, post_snapshot, archive_name=RETREAT_ARCHIVE_NAME
        )
        commands.append("save-checkpoint")
        return {
            "ok": True,
            "outcome": "three_cunit_owner_subset_retreat",
            "initial_snapshot": initial,
            "requester_control_proof": requester_control,
            "exact_build_proof": exact_build,
            "capability_proof": capability,
            "combat_id": combat_id,
            "combat_province_id": pre_battle.get("province_id"),
            "retained_same_side_order": retained_order,
            "parent_proof_immediately_before_retreat": parent_proof,
            "control_result_immediately_before_retreat": control_result,
            "control_proof_immediately_before_retreat": control_proof,
            "pre_battle": pre_battle,
            "preview": preview,
            "order": order,
            "post_frames": post_frames,
            "post_snapshot": post_snapshot,
            "post_battle": post_battle,
            "post_retreat_proof": post_proof,
            "checkpoint": checkpoint,
            "date_raw": retreat_date,
            "observations": observations,
            "advances": advances,
            "commands": commands,
        }

    return ai_live._run_managed_session(
        spec=spec,
        config=config,
        timeout=timeout,
        readiness_timeout=readiness_timeout,
        name="xar-three-cunit-contact-retreat-production",
        fixture=False,
        body=body,
    )


def _switch_armies_proof(
    snapshot: dict[str, object],
    *,
    played_character_id: int,
    sibling_cunit_id: int,
    requester_controllable: bool,
    retained_controllable: bool,
    require_precontact: bool,
) -> dict[str, object]:
    armies: dict[int, dict[str, object]] = {}
    for public_id in (
        REQUESTER_CUNIT_ID,
        ANCHOR_CUNIT_ID,
        sibling_cunit_id,
        OPPOSITE_CUNIT_ID,
    ):
        try:
            armies[public_id] = _army(snapshot, public_id)
        except RuntimeError:
            armies[public_id] = {}
    requester = armies[REQUESTER_CUNIT_ID]
    anchor = armies[ANCHOR_CUNIT_ID]
    sibling = armies[sibling_cunit_id]
    checks = {
        "played_character": owner_live._played_character_id(snapshot)
        == played_character_id,
        "paused": snapshot.get("paused") is True,
        "requester_identity_control": requester.get("owner_character_id")
        == REQUESTER_CHARACTER_ID
        and requester.get("controllable") is requester_controllable,
        "anchor_identity_control": anchor.get("owner_character_id")
        == RETAINED_CHARACTER_ID
        and anchor.get("controllable") is retained_controllable,
        "sibling_identity_control": sibling.get("owner_character_id")
        == RETAINED_CHARACTER_ID
        and sibling.get("controllable") is retained_controllable,
    }
    if require_precontact:
        checks["all_precontact"] = all(
            army.get("in_combat") is False
            and army.get("retreating") is False
            for army in armies.values()
        )
        checks["retained_routes_target_contact"] = all(
            army.get("move_target_province_id") == CONTACT_PROVINCE_ID
            and isinstance(army.get("route_province_ids"), list)
            and bool(army.get("route_province_ids"))
            and army["route_province_ids"][-1] == CONTACT_PROVINCE_ID
            for army in (anchor, sibling)
        )
    return {
        "armies": {str(key): value for key, value in armies.items()},
        "checks": checks,
        "ok": all(checks.values()),
    }


def _post_retreat_switch_proof(
    snapshot: dict[str, object],
    *,
    played_character_id: int,
    sibling_cunit_id: int,
) -> dict[str, object]:
    try:
        requester = _army(snapshot, REQUESTER_CUNIT_ID)
        anchor = _army(snapshot, ANCHOR_CUNIT_ID)
        sibling = _army(snapshot, sibling_cunit_id)
    except RuntimeError:
        requester, anchor, sibling = {}, {}, {}
    route = requester.get("route_province_ids")
    checks = {
        "played_character": owner_live._played_character_id(snapshot)
        == played_character_id,
        "paused": snapshot.get("paused") is True,
        "requester_ai_control": requester.get("owner_character_id")
        == REQUESTER_CHARACTER_ID
        and requester.get("controllable") is (
            played_character_id == REQUESTER_CHARACTER_ID
        ),
        "requester_retreat_preserved": requester.get("in_combat") is False
        and requester.get("retreating") is True
        and requester.get("move_target_province_id") == RETREAT_PROVINCE_ID
        and isinstance(route, list)
        and bool(route)
        and route[-1] == RETREAT_PROVINCE_ID,
        "anchor_retained_in_combat": anchor.get("in_combat") is True
        and anchor.get("retreating") is False,
        "sibling_retained_in_combat": sibling.get("in_combat") is True
        and sibling.get("retreating") is False,
    }
    return {
        "requester_army": requester,
        "anchor_army": anchor,
        "sibling_army": sibling,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _retained_parent_capacity_proof(
    pair: dict[str, object], *, sibling_cunit_id: int
) -> dict[str, object]:
    anchor = pair.get("anchor_frame")
    anchor = anchor if isinstance(anchor, dict) else {}
    rows = rejoin_live._native_rows(anchor)
    locations: dict[int, tuple[int, int]] = {}
    rows_typed = bool(rows)
    for row_index, row in enumerate(rows):
        ids = row.get("public_cunit_ids_in_stored_order")
        if not isinstance(ids, list) or not ids:
            rows_typed = False
            continue
        for column, value in enumerate(ids):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
                or value in locations
            ):
                rows_typed = False
            else:
                locations[value] = (row_index, column)
    anchor_location = locations.get(ANCHOR_CUNIT_ID)
    sibling_location = locations.get(sibling_cunit_id)
    checks = {
        "anchor_membership_available": ai_live._typed_native_membership_proof(
            anchor, ANCHOR_CUNIT_ID
        ).get("ok")
        is True,
        "rows_typed": rows_typed,
        "at_least_two_native_subunit_rows": len(rows) >= 2,
        "retained_cunits_in_distinct_rows": anchor_location is not None
        and sibling_location is not None
        and anchor_location[0] != sibling_location[0],
    }
    return {
        "classification": (
            "retained_parent_can_ask"
            if all(checks.values())
            else "retained_parent_subunit_structure_collapsed"
        ),
        "rows": rows,
        "subunit_count": len(rows),
        "locations": {str(key): list(value) for key, value in locations.items()},
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_final_reassignment_sequence(
    service: GameplayBridgeService,
    *,
    wait_after_advance: Callable[[], dict[str, object]],
    sibling_cunit_id: int,
    combat_id: int,
    combat_province_id: int,
    retained_same_side_order: list[int],
    expected_date_raw: int,
    max_assignment_days: int,
    max_eta_days: int,
) -> dict[str, object]:
    commands: list[str] = []
    advances: list[dict[str, object]] = []
    observations: list[dict[str, object]] = []
    terminal_boundaries: list[dict[str, object]] = []
    initial = service.snapshot()
    snapshot, pair, battle, terminal, retries = (
        rejoin_live._query_paused_observation_bundle(
            service,
            initial,
            combat_id=combat_id,
            terminal_cursor=None,
        )
    )
    initial_episode = snapshot.get("episode_run_id")
    context = ai_live._daily_ai_context_proof(
        snapshot,
        expected_date_raw=expected_date_raw,
        expected_episode_run_id=initial_episode,
    )
    roster = _retained_combat_roster_proof(
        battle,
        sibling_cunit_id=sibling_cunit_id,
        combat_id=combat_id,
        retained_same_side_order=retained_same_side_order,
    )
    boundary = rejoin_live._terminal_boundary_proof(
        terminal, battle, combat_id=combat_id, requested_cursor=None
    )
    requester = _post_retreat_switch_proof(
        snapshot,
        played_character_id=ORIGINAL_CHARACTER_ID,
        sibling_cunit_id=sibling_cunit_id,
    )
    transient = ai_live._retreating_membership_transient_proof(snapshot, pair)
    membership = ai_live._independent_native_pair_available_proof(pair)
    initial_membership_ok = bool(
        transient.get("ok") is True or membership.get("ok") is True
    )
    initial_checks = {
        "daily_context": context.get("ok") is True,
        "requester_under_ai": requester.get("ok") is True,
        "retained_old_combat": roster.get("ok") is True,
        "terminal_active": boundary.get("active") is True,
        "typed_membership_start": initial_membership_ok,
    }
    initial_proof = {
        "context": context,
        "requester": requester,
        "roster": roster,
        "terminal_boundary": boundary,
        "retreating_transient": transient,
        "independent_membership": membership,
        "observation_retries": retries,
        "checks": initial_checks,
        "ok": all(initial_checks.values()),
    }
    if initial_proof["ok"] is not True:
        return {
            "ok": False,
            "outcome": "final_ai_reload_gate_drift",
            "initial_snapshot": initial,
            "snapshot": snapshot,
            "pair": pair,
            "battle": battle,
            "terminal": terminal,
            "initial_proof": initial_proof,
            "commands": commands,
            "advances": advances,
            "observations": observations,
            "readiness_gates": {
                "ai_control_live_ready": False,
                "retained_parent_can_ask_live_ready": False,
                "assignment_reopened_aligned_eta_live_ready": False,
                "same_combat_rejoin_live_ready": False,
            },
        }
    baseline_battle = battle
    cursor = boundary.get("next_cursor")
    membership_reopened: dict[str, object] | None = (
        membership if membership.get("ok") is True else None
    )
    capacity: dict[str, object] | None = None
    assignment: dict[str, object] | None = None
    assigned_battle: dict[str, object] | None = None

    def diagnostic(outcome: str, **extra: object) -> dict[str, object]:
        return {
            "ok": False,
            "outcome": outcome,
            "initial_snapshot": initial,
            "initial_proof": initial_proof,
            "baseline_battle": baseline_battle,
            "membership_reopened_proof": membership_reopened,
            "retained_parent_capacity_proof": capacity,
            "assignment_proof": assignment,
            "diagnostic_frame": extra,
            "observations": observations,
            "terminal_boundaries": terminal_boundaries,
            "commands": list(commands),
            "advances": advances,
            "readiness_gates": {
                "ai_control_live_ready": True,
                "retained_parent_can_ask_live_ready": bool(
                    capacity and capacity.get("ok") is True
                ),
                "assignment_reopened_aligned_eta_live_ready": False,
                "same_combat_rejoin_live_ready": False,
            },
        }

    for day_index in range(max_assignment_days + 1):
        if day_index > 0:
            snapshot, pair, battle, terminal, retries = (
                rejoin_live._query_paused_observation_bundle(
                    service,
                    snapshot,
                    combat_id=combat_id,
                    terminal_cursor=cursor,
                )
            )
        context = ai_live._daily_ai_context_proof(
            snapshot,
            expected_date_raw=expected_date_raw
            + len(advances) * ONE_GAME_DAY_RAW,
            expected_episode_run_id=initial_episode,
        )
        roster = _retained_combat_roster_proof(
            battle,
            sibling_cunit_id=sibling_cunit_id,
            combat_id=combat_id,
            retained_same_side_order=retained_same_side_order,
        )
        boundary = rejoin_live._terminal_boundary_proof(
            terminal,
            battle,
            combat_id=combat_id,
            requested_cursor=None if day_index == 0 else cursor,
        )
        transient = ai_live._retreating_membership_transient_proof(snapshot, pair)
        membership = ai_live._independent_native_pair_available_proof(pair)
        if membership.get("ok") is True:
            membership_reopened = membership
            capacity = _retained_parent_capacity_proof(
                pair, sibling_cunit_id=sibling_cunit_id
            )
        observation = {
            "stage": "assignment",
            "day_index": day_index,
            "snapshot": snapshot,
            "pair": pair,
            "battle": battle,
            "terminal": terminal,
            "boundary": boundary,
            "daily_context": context,
            "roster": roster,
            "transient": transient,
            "membership": membership,
            "retained_parent_capacity": capacity,
            "observation_retries": retries,
        }
        observations.append(observation)
        terminal_boundaries.append(
            {"stage": "assignment", "day_index": day_index, **boundary}
        )
        if boundary.get("terminal_event") is True:
            return diagnostic("terminal_before_assignment", **observation)
        if context.get("ok") is not True or roster.get("ok") is not True:
            return diagnostic("old_combat_or_context_drift_before_assignment", **observation)
        cursor = boundary.get("next_cursor")
        if membership.get("ok") is not True and transient.get("ok") is not True:
            return diagnostic("native_membership_transition_drift", **observation)
        candidate = {"ok": False}
        if membership.get("ok") is True and capacity is not None:
            candidate = ai_live._independent_assignment_reopened_proof(
                pair,
                snapshot,
                battle,
                combat_id=combat_id,
                combat_province_id=combat_province_id,
            )
        if candidate.get("ok") is True:
            if capacity is None or capacity.get("ok") is not True:
                return diagnostic(
                    "assignment_observed_without_two_row_requester_parent",
                    assignment_candidate=candidate,
                    **observation,
                )
            assignment = candidate
            assigned_battle = battle
            break
        if day_index == max_assignment_days:
            return diagnostic(
                (
                    "retained_parent_subunit_structure_collapsed"
                    if capacity is not None and capacity.get("ok") is not True
                    else "assignment_not_observed_within_bound"
                ),
                **observation,
            )
        snapshot, advance = rejoin_live._advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")

    if assignment is None or assigned_battle is None:
        raise RuntimeError("assignment loop escaped without assignment")
    assigned_date = rejoin_live._snapshot_date(snapshot)
    eta = assignment.get("assignment_eta_date_raw")
    if not (
        isinstance(eta, int)
        and not isinstance(eta, bool)
        and assigned_date < eta <= assigned_date + max_eta_days * ONE_GAME_DAY_RAW
    ):
        return diagnostic("assignment_eta_outside_bound", eta=eta)
    assigned_checkpoint = _save_archive(
        service, snapshot, archive_name=ASSIGNED_ARCHIVE_NAME
    )
    commands.append("save-checkpoint")
    snapshot = service.snapshot()
    immediately_before = assigned_battle
    join_proof: dict[str, object] | None = None
    joined_battle: dict[str, object] | None = None
    for day_index in range(1, max_eta_days + 1):
        if rejoin_live._snapshot_date(snapshot) >= eta:
            return diagnostic(
                "rejoin_not_observed_by_eta",
                day_index=day_index - 1,
                assigned_checkpoint=assigned_checkpoint,
            )
        snapshot, advance = rejoin_live._advance_one_day(
            service, snapshot, wait_after_advance
        )
        advances.append(advance)
        commands.append("life-advance")
        snapshot, pair, battle, terminal, retries = (
            rejoin_live._query_paused_observation_bundle(
                service,
                snapshot,
                combat_id=combat_id,
                terminal_cursor=cursor,
            )
        )
        boundary = rejoin_live._terminal_boundary_proof(
            terminal, battle, combat_id=combat_id, requested_cursor=cursor
        )
        context = ai_live._daily_ai_context_proof(
            snapshot,
            expected_date_raw=expected_date_raw
            + len(advances) * ONE_GAME_DAY_RAW,
            expected_episode_run_id=initial_episode,
        )
        roster = _retained_combat_roster_proof(
            battle,
            sibling_cunit_id=sibling_cunit_id,
            combat_id=combat_id,
            retained_same_side_order=retained_same_side_order,
        )
        observation = {
            "stage": "eta",
            "day_index": day_index,
            "snapshot": snapshot,
            "pair": pair,
            "battle": battle,
            "terminal": terminal,
            "boundary": boundary,
            "daily_context": context,
            "roster": roster,
            "observation_retries": retries,
        }
        observations.append(observation)
        terminal_boundaries.append({"stage": "eta", "day_index": day_index, **boundary})
        if boundary.get("terminal_event") is True:
            return diagnostic("terminal_before_rejoin", **observation)
        if context.get("ok") is not True or boundary.get("active") is not True:
            return diagnostic("context_or_terminal_drift_before_rejoin", **observation)
        cursor = boundary.get("next_cursor")
        participants = [
            *(battle.get("attacker_public_cunit_ids_in_stored_order") or []),
            *(battle.get("defender_public_cunit_ids_in_stored_order") or []),
        ]
        if REQUESTER_CUNIT_ID in participants:
            candidate_join = rejoin_live._same_combat_rejoin_proof(
                baseline_battle,
                immediately_before,
                battle,
                pair,
                snapshot,
                combat_id=combat_id,
                combat_province_id=combat_province_id,
                side_index=SIDE_INDEX,
            )
            if candidate_join.get("ok") is not True:
                return diagnostic(
                    "same_combat_tail_join_postcondition_drift",
                    join_candidate=candidate_join,
                    **observation,
                )
            join_proof = candidate_join
            joined_battle = battle
            break
        if roster.get("ok") is not True:
            return diagnostic("retained_roster_drift_before_rejoin", **observation)
        immediately_before = battle
    if join_proof is None or joined_battle is None:
        return diagnostic("eta_loop_ended_without_rejoin")
    joined_date = rejoin_live._snapshot_date(snapshot)
    joined_checkpoint = _save_archive(
        service, snapshot, archive_name=JOINED_ARCHIVE_NAME
    )
    commands.append("save-checkpoint")
    mutation_checks = {
        "only_daily_advance_and_save": all(
            command in {"life-advance", "save-checkpoint"}
            for command in commands
        ),
        "two_checkpoint_saves": commands.count("save-checkpoint") == 2,
        "at_least_one_daily_advance": commands.count("life-advance") >= 1,
    }
    assertions = {
        "initial_ai_control": initial_proof.get("ok") is True,
        "retained_parent_has_two_rows": capacity is not None
        and capacity.get("ok") is True,
        "assignment_aligned_eta": assignment.get("ok") is True,
        "strict_same_combat_tail_join": join_proof.get("ok") is True,
        "joined_by_eta": joined_date <= eta,
        "all_advances_exactly_one_day": bool(advances)
        and all(row.get("ok") is True for row in advances),
        "assigned_checkpoint": assigned_checkpoint.get("ok") is True,
        "joined_checkpoint": joined_checkpoint.get("ok") is True,
        "production_mutation_boundary": all(mutation_checks.values()),
    }
    return {
        "ok": all(assertions.values()),
        "outcome": "three_cunit_native_assignment_same_combat_rejoin",
        "initial_snapshot": initial,
        "initial_proof": initial_proof,
        "baseline_battle": baseline_battle,
        "membership_reopened_proof": membership_reopened,
        "retained_parent_capacity_proof": capacity,
        "assignment_proof": assignment,
        "assigned_date_raw": assigned_date,
        "assignment_eta_date_raw": eta,
        "assigned_checkpoint": assigned_checkpoint,
        "joined_date_raw": joined_date,
        "joined_battle": joined_battle,
        "join_proof": join_proof,
        "joined_checkpoint": joined_checkpoint,
        "observations": observations,
        "terminal_boundaries": terminal_boundaries,
        "commands": commands,
        "advances": advances,
        "mutation_boundary_proof": {
            "commands": commands,
            "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
            "forbidden_native_calls_invoked": [],
            "checks": mutation_checks,
            "ok": all(mutation_checks.values()),
        },
        "assertions": assertions,
        "readiness_gates": {
            "ai_control_live_ready": True,
            "retained_parent_can_ask_live_ready": capacity.get("ok") is True,
            "assignment_reopened_aligned_eta_live_ready": assignment.get("ok")
            is True,
            "same_combat_rejoin_live_ready": join_proof.get("ok") is True,
        },
    }


def _run_final_reassignment_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    sibling_cunit_id: int,
    combat_id: int,
    combat_province_id: int,
    retained_same_side_order: list[int],
    expected_date_raw: int,
    max_assignment_days: int,
    max_eta_days: int,
) -> dict[str, object]:
    def body(
        service: GameplayBridgeService,
        driver: NativeHeadlessGameplayDriver,
        session_done: threading.Event,
        session_state: dict[str, object],
    ) -> dict[str, object]:
        capabilities = driver.capabilities()
        exact_build = rejoin_live._exact_build_proof(
            capabilities, _sha256_file(spec.game_exe)
        )
        capability = rejoin_live._capability_proof(capabilities)
        if not (exact_build.get("ok") is True and capability.get("ok") is True):
            return {
                "ok": False,
                "outcome": "final_exact_build_or_capability_not_ready",
                "exact_build_proof": exact_build,
                "capability_proof": capability,
                "error": "final production query/action surface is not ready",
            }

        sequence = _run_final_reassignment_sequence(
            service,
            wait_after_advance=lambda: _wait_after_advance(
                driver,
                session_done=session_done,
                session_state=session_state,
                readiness_timeout=readiness_timeout,
            ),
            sibling_cunit_id=sibling_cunit_id,
            combat_id=combat_id,
            combat_province_id=combat_province_id,
            retained_same_side_order=retained_same_side_order,
            expected_date_raw=expected_date_raw,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
        )
        after_capabilities = driver.capabilities()
        same_process = rejoin_live._same_process_proof(
            capabilities, after_capabilities
        )
        sequence_gates = sequence.get("readiness_gates")
        sequence_gates = (
            dict(sequence_gates) if isinstance(sequence_gates, dict) else {}
        )
        sequence_gates["one_pid_generation_live_ready"] = (
            same_process.get("ok") is True
        )
        return {
            **sequence,
            "ok": sequence.get("ok") is True and same_process.get("ok") is True,
            "exact_build_proof": exact_build,
            "capability_proof": capability,
            "same_process_proof": same_process,
            "after_capabilities": after_capabilities,
            "readiness_gates": sequence_gates,
            "error": (
                None
                if sequence.get("ok") is True and same_process.get("ok") is True
                else str(
                    sequence.get("outcome")
                    or "final one-PID reassignment sequence failed"
                )
            ),
        }

    return ai_live._run_managed_session(
        spec=spec,
        config=config,
        timeout=timeout,
        readiness_timeout=readiness_timeout,
        name="xar-three-cunit-final-reassignment-production",
        fixture=False,
        body=body,
    )






def _three_cunit_parent_proof(
    snapshot: dict[str, object],
    results: list[dict[str, object]],
    battle: dict[str, object],
    *,
    sibling_cunit_id: int,
    combat_id: int,
) -> dict[str, object]:
    expected = [REQUESTER_CUNIT_ID, ANCHOR_CUNIT_ID, sibling_cunit_id]
    frames: list[dict[str, object]] = []
    sequences: list[int] = []
    for result in results:
        try:
            frames.append(rejoin_live._reinforcement_frame(result))
        except RuntimeError:
            frames.append({})
        sequence = result.get("query_sequence") if isinstance(result, dict) else None
        if isinstance(sequence, int) and not isinstance(sequence, bool):
            sequences.append(sequence)
    requester = frames[0] if len(frames) == 3 else {}
    rows = rejoin_live._native_rows(requester)
    locations: dict[int, tuple[int, int]] = {}
    rows_typed = bool(rows)
    for row_index, row in enumerate(rows):
        ids = row.get("public_cunit_ids_in_stored_order")
        if not isinstance(ids, list) or not ids:
            rows_typed = False
            continue
        for column, value in enumerate(ids):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
                or value in locations
            ):
                rows_typed = False
            else:
                locations[value] = (row_index, column)
    try:
        same_side, opposite_side = rejoin_live._side_ids(battle, SIDE_INDEX)
    except RuntimeError:
        same_side, opposite_side = [], []
    memberships = [
        ai_live._typed_native_membership_proof(frame, public_id)
        for frame, public_id in zip(frames, expected)
    ]
    distinct_row_indices = {
        locations[value][0] for value in expected if value in locations
    }
    coordinators = [frame.get("coordinator_id") for frame in frames]
    unit_stack_indices = [frame.get("unit_stack_stored_index") for frame in frames]
    parent_orders = [rejoin_live._native_rows(frame) for frame in frames]
    checks = {
        "three_results": len(results) == len(frames) == 3,
        "same_paused_native_binding": all(
            frame.get("snapshot_revision") == snapshot.get("native_revision")
            and frame.get("observed_date_raw") == snapshot.get("date_raw")
            for frame in frames
        ),
        "query_order": len(sequences) == 3
        and sequences == sorted(sequences)
        and len(set(sequences)) == 3,
        "all_memberships_typed": all(row.get("ok") is True for row in memberships),
        "same_coordinator": len(coordinators) == 3
        and isinstance(coordinators[0], int)
        and coordinators[0] > 0
        and len(set(coordinators)) == 1,
        # selected_native_carmy_id identifies each queried CUnit's own CArmy;
        # siblings in one CAIUnitStack parent can therefore publish different
        # values.  Shared parent identity is the coordinator + unit-stack
        # index + identical stored parent rows, never CArmy-ID equality.
        "same_requester_parent_identity": len(unit_stack_indices) == 3
        and isinstance(unit_stack_indices[0], int)
        and not isinstance(unit_stack_indices[0], bool)
        and unit_stack_indices[0] >= 0
        and len(set(unit_stack_indices)) == 1,
        "same_requester_parent_order": len(parent_orders) == 3
        and all(order == rows for order in parent_orders),
        "requester_parent_rows_typed": rows_typed,
        "requester_parent_has_at_least_three_subunit_rows": len(rows) >= 3,
        "three_expected_cunits_in_distinct_rows": all(
            value in locations for value in expected
        )
        and len(distinct_row_indices) == 3,
        "requester_selected_row_matches": locations.get(REQUESTER_CUNIT_ID)
        is not None
        and requester.get("subunit_stored_index")
        == locations[REQUESTER_CUNIT_ID][0],
        "same_active_combat_roster": battle.get("status") == "available"
        and battle.get("battle_transition_ready") is True
        and battle.get("combat_id") == combat_id
        and battle.get("finalized") is False
        and len(same_side) == 3
        and len(set(same_side)) == 3
        and set(same_side) == set(expected)
        and opposite_side == [OPPOSITE_CUNIT_ID],
    }
    return {
        "classification": (
            "three_distinct_requester_parent_subunits"
            if all(checks.values())
            else "fixture_subunit_structure_insufficient"
        ),
        "expected_same_side_order": expected,
        "same_side": same_side,
        "retained_same_side_order": [
            value for value in same_side if value != REQUESTER_CUNIT_ID
        ],
        "opposite_side": opposite_side,
        "requester_parent_rows": rows,
        "requester_parent_subunit_count": len(rows),
        "cunit_locations": {str(key): list(value) for key, value in locations.items()},
        "memberships": memberships,
        "frames": frames,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _retained_combat_roster_proof(
    battle: dict[str, object],
    *,
    sibling_cunit_id: int,
    combat_id: int,
    retained_same_side_order: list[int] | None = None,
) -> dict[str, object]:
    try:
        same_side, opposite_side = rejoin_live._side_ids(battle, SIDE_INDEX)
    except RuntimeError:
        same_side, opposite_side = [], []
    expected = (
        list(retained_same_side_order)
        if retained_same_side_order is not None
        else [ANCHOR_CUNIT_ID, sibling_cunit_id]
    )
    expected_identity_ok = bool(
        len(expected) == 2
        and len(set(expected)) == 2
        and set(expected) == {ANCHOR_CUNIT_ID, sibling_cunit_id}
    )
    phase_raw = battle.get("phase_raw")
    winner_raw = battle.get("winner_raw")
    checks = {
        "active_identity": battle.get("status") == "available"
        and battle.get("battle_transition_ready") is True
        and battle.get("combat_id") == combat_id
        and battle.get("finalized") is False,
        "phase_winner_typed": (phase_raw in {0, 1} and winner_raw == -1)
        or (phase_raw == 2 and winner_raw in {0, 1}),
        "retained_identity_typed": expected_identity_ok,
        "owner_subset_removed_only_requester": same_side == expected,
        "opposite_unchanged": opposite_side == [OPPOSITE_CUNIT_ID],
    }
    return {
        "expected_same_side": expected,
        "same_side": same_side,
        "opposite_side": opposite_side,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _single_anchor_switch_proof(
    snapshot: dict[str, object],
    *,
    played_character_id: int,
    anchor_controllable: bool,
) -> dict[str, object]:
    anchor = _precontact_army_proof(
        snapshot,
        ANCHOR_CUNIT_ID,
        owner_character_id=RETAINED_CHARACTER_ID,
        controllable=anchor_controllable,
    )
    precontact = _all_precontact_proof(snapshot)
    checks = {
        "played_character": owner_live._played_character_id(snapshot)
        == played_character_id,
        "anchor_identity_and_control": anchor.get("ok") is True,
        "all_armies_precontact": precontact.get("ok") is True,
    }
    return {
        "anchor_proof": anchor,
        "precontact_proof": precontact,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _managed_body(stage: object) -> dict[str, object]:
    if not isinstance(stage, dict):
        return {}
    body = stage.get("body")
    return body if isinstance(body, dict) else {}


def _managed_cleanup_ok(stage: object) -> bool:
    if not isinstance(stage, dict):
        return False
    cleanup = stage.get("cleanup")
    return isinstance(cleanup, dict) and cleanup.get("ok") is True


def _target_root(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-three-cunit-owner-subset-" + uuid.uuid4().hex
    )


def _cleanup_root(
    root: Path,
    *,
    nonce: str,
    retain: bool,
    all_sessions_clean: bool,
) -> dict[str, object]:
    target = root.resolve()
    if retain:
        return {
            "attempted": False,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": "--retain-state prevents cleanup qualification",
        }
    if not all_sessions_clean:
        return {
            "attempted": False,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": "a managed stage cleanup was not proven",
        }
    marker = target / _ROOT_MARKER_NAME
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == "xar_three_cunit_owner_subset_fixture"
            and payload.get("nonce") == nonce
        ):
            raise AgentError("three-CUnit fixture root marker differs")
        ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "ok": removed,
            "path": str(target),
            "reason": None if removed else "fixture root still exists",
        }
    except BaseException as error:
        return {
            "attempted": True,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": f"{type(error).__name__}: {error}",
        }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    timeout = _positive_seconds(args.timeout, "timeout")
    readiness_timeout = _positive_seconds(
        args.readiness_timeout, "readiness_timeout"
    )
    seed_timeout = _positive_seconds(args.seed_timeout, "seed_timeout")
    postcondition_timeout = _positive_seconds(
        args.postcondition_timeout, "postcondition_timeout"
    )
    route_timeout = _positive_seconds(args.route_timeout, "route_timeout")
    max_split_wait_days = _positive_int(
        args.max_split_wait_days, "max_split_wait_days"
    )
    max_contact_days = _positive_int(args.max_contact_days, "max_contact_days")
    max_assignment_days = _positive_int(
        args.max_assignment_days, "max_assignment_days"
    )
    max_eta_days = _positive_int(args.max_eta_days, "max_eta_days")
    expected_sha = _expected_sha256(args.expected_battle_save_sha256)
    source_state = args.source_state_dir.expanduser().resolve()
    source_profile = source_state / "profile"
    game_dir = args.game_dir.expanduser().resolve()
    root = _target_root(args.state_dir)
    output = args.output.expanduser().resolve()
    if root.exists():
        raise AgentError(f"fixture root already exists: {root}")
    ensure_state_path_safe(root)
    if paths_overlap(source_state, root):
        raise AgentError("source and fixture state roots overlap")
    if is_relative_to(output, root):
        raise AgentError("artifact output must be outside disposable root")
    if is_relative_to(output, source_state):
        raise AgentError("artifact output must be outside immutable source")
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    source_save, source_identity = owner_live._resolve_source_save(
        source_profile, args.battle_save, expected_sha
    )
    source_before = _sha256_file(source_save)
    nonce = uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    write_json_atomic(
        root / _ROOT_MARKER_NAME,
        {
            "kind": "xar_three_cunit_owner_subset_fixture",
            "nonce": nonce,
            "source_state_dir": str(source_state),
            "source_save_sha256": source_before,
        },
    )
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.expanduser().resolve(),
        injector_path=args.bridge_injector.expanduser().resolve(),
    )

    materializations: dict[str, object] = {}
    reports: dict[str, object] = {}
    cleanup_flags: list[bool] = []
    primary_error: str | None = None
    expected_date_raw: int | None = None
    sibling_cunit_id: int | None = None
    combat_id: int | None = None
    combat_province_id: int | None = None
    retained_same_side_order: list[int] | None = None

    try:
        route_spec, materializations["p0_route_clear"] = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "p0-route-clear",
            game_dir=game_dir,
            save_source=source_save,
            save_name=CONTINUE_SAVE_NAME,
        )
        route_stage = _run_route_clear_stage(
            spec=route_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            route_timeout=route_timeout,
        )
        reports["p0_route_clear"] = route_stage
        cleanup_flags.append(_managed_cleanup_ok(route_stage))
        if route_stage.get("ok") is not True:
            raise AgentError(str(route_stage.get("error") or "P0 route clear failed"))
        route_body = _managed_body(route_stage)
        expected_date_raw = _positive_int(route_body.get("date_raw"), "P0 date")
        route_checkpoint = owner_live._checkpoint_path(route_spec)

        ally_spec, ally_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "s1-ally-switch",
            game_dir=game_dir,
            save_source=route_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        ally_materialization["fixture_bridge"] = owner_live._install_seed_bridge(
            ally_spec
        )
        materializations["s1_ally_switch"] = ally_materialization
        ally_stage = _run_seed_switch_stage(
            spec=ally_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
            expected_date_raw=expected_date_raw,
            from_character_id=ORIGINAL_CHARACTER_ID,
            to_character_id=RETAINED_CHARACTER_ID,
            switch_effect=_dynamic_ally_switch_effect(),
            clear_effect=_dynamic_ally_clear_effect(),
            switch_marker=ALLY_SWITCH_MARKER,
            clear_marker=ALLY_CLEAR_MARKER,
            name="ally",
            precheck=lambda snapshot: _single_anchor_switch_proof(
                snapshot,
                played_character_id=ORIGINAL_CHARACTER_ID,
                anchor_controllable=False,
            ),
            postcheck=lambda snapshot: _single_anchor_switch_proof(
                snapshot,
                played_character_id=RETAINED_CHARACTER_ID,
                anchor_controllable=True,
            ),
        )
        reports["s1_ally_switch"] = ally_stage
        cleanup_flags.append(_managed_cleanup_ok(ally_stage))
        if ally_stage.get("ok") is not True:
            raise AgentError(str(ally_stage.get("error") or "S1 ally switch failed"))
        ally_checkpoint = owner_live._checkpoint_path(ally_spec)

        split_spec, materializations["p2_split_route"] = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "p2-split-route",
            game_dir=game_dir,
            save_source=ally_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        split_stage = _run_split_route_stage(
            spec=split_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            route_timeout=route_timeout,
            max_split_wait_days=max_split_wait_days,
            expected_date_raw=expected_date_raw,
        )
        reports["p2_split_route"] = split_stage
        cleanup_flags.append(_managed_cleanup_ok(split_stage))
        if split_stage.get("ok") is not True:
            raise AgentError(str(split_stage.get("error") or "P2 split/route failed"))
        split_body = _managed_body(split_stage)
        sibling_cunit_id = _positive_int(
            split_body.get("sibling_cunit_id"), "dynamic sibling CUnitID"
        )
        expected_date_raw = _positive_int(split_body.get("date_raw"), "P2 date")
        split_checkpoint = owner_live._checkpoint_path(split_spec)

        requester_spec, requester_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "s3-requester-switch",
            game_dir=game_dir,
            save_source=split_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        requester_materialization["fixture_bridge"] = (
            owner_live._install_seed_bridge(requester_spec)
        )
        materializations["s3_requester_switch"] = requester_materialization
        requester_stage = _run_seed_switch_stage(
            spec=requester_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
            expected_date_raw=expected_date_raw,
            from_character_id=RETAINED_CHARACTER_ID,
            to_character_id=REQUESTER_CHARACTER_ID,
            switch_effect=_province_owner_switch_effect(
                province_id=REQUESTER_ANCHOR_PROVINCE_ID,
                guard=REQUESTER_SWITCH_GUARD,
                marker=REQUESTER_SWITCH_MARKER,
                scope_name="xar_fixture_three_cunit_requester",
            ),
            clear_effect=_guard_clear_effect(
                guard=REQUESTER_SWITCH_GUARD, marker=REQUESTER_CLEAR_MARKER
            ),
            switch_marker=REQUESTER_SWITCH_MARKER,
            clear_marker=REQUESTER_CLEAR_MARKER,
            name="requester",
            precheck=lambda snapshot: _switch_armies_proof(
                snapshot,
                played_character_id=RETAINED_CHARACTER_ID,
                sibling_cunit_id=sibling_cunit_id,
                requester_controllable=False,
                retained_controllable=True,
                require_precontact=True,
            ),
            postcheck=lambda snapshot: _switch_armies_proof(
                snapshot,
                played_character_id=REQUESTER_CHARACTER_ID,
                sibling_cunit_id=sibling_cunit_id,
                requester_controllable=True,
                retained_controllable=False,
                require_precontact=True,
            ),
        )
        reports["s3_requester_switch"] = requester_stage
        cleanup_flags.append(_managed_cleanup_ok(requester_stage))
        if requester_stage.get("ok") is not True:
            raise AgentError(
                str(requester_stage.get("error") or "S3 requester switch failed")
            )
        requester_checkpoint = owner_live._checkpoint_path(requester_spec)

        retreat_spec, materializations["p4_contact_retreat"] = (
            owner_live._prepare_stage(
                source_profile=source_profile,
                target_state=root / "p4-contact-retreat",
                game_dir=game_dir,
                save_source=requester_checkpoint,
                save_name=CONTINUE_SAVE_NAME,
            )
        )
        retreat_stage = _run_contact_retreat_stage(
            spec=retreat_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            postcondition_timeout=postcondition_timeout,
            max_contact_days=max_contact_days,
            expected_date_raw=expected_date_raw,
            sibling_cunit_id=sibling_cunit_id,
        )
        reports["p4_contact_retreat"] = retreat_stage
        cleanup_flags.append(_managed_cleanup_ok(retreat_stage))
        if retreat_stage.get("ok") is not True:
            raise AgentError(
                str(retreat_stage.get("error") or "P4 contact/retreat failed")
            )
        retreat_body = _managed_body(retreat_stage)
        expected_date_raw = _positive_int(retreat_body.get("date_raw"), "P4 date")
        combat_id = _positive_int(retreat_body.get("combat_id"), "CombatID")
        combat_province_id = _positive_int(
            retreat_body.get("combat_province_id"), "combat ProvinceID"
        )
        raw_retained_order = retreat_body.get("retained_same_side_order")
        if not (
            isinstance(raw_retained_order, list)
            and len(raw_retained_order) == 2
            and set(raw_retained_order) == {ANCHOR_CUNIT_ID, sibling_cunit_id}
        ):
            raise AgentError("P4 retained same-side stored order is not exact")
        retained_same_side_order = list(raw_retained_order)
        retreat_checkpoint = owner_live._checkpoint_path(retreat_spec)

        return_spec, return_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "s5-return-switch",
            game_dir=game_dir,
            save_source=retreat_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        return_materialization["fixture_bridge"] = owner_live._install_seed_bridge(
            return_spec
        )
        materializations["s5_return_switch"] = return_materialization
        return_stage = _run_seed_switch_stage(
            spec=return_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
            expected_date_raw=expected_date_raw,
            from_character_id=REQUESTER_CHARACTER_ID,
            to_character_id=ORIGINAL_CHARACTER_ID,
            switch_effect=_province_owner_switch_effect(
                province_id=RETURN_ANCHOR_PROVINCE_ID,
                guard=RETURN_SWITCH_GUARD,
                marker=RETURN_SWITCH_MARKER,
                scope_name="xar_fixture_three_cunit_return",
            ),
            clear_effect=_guard_clear_effect(
                guard=RETURN_SWITCH_GUARD, marker=RETURN_CLEAR_MARKER
            ),
            switch_marker=RETURN_SWITCH_MARKER,
            clear_marker=RETURN_CLEAR_MARKER,
            name="return",
            precheck=lambda snapshot: _post_retreat_switch_proof(
                snapshot,
                played_character_id=REQUESTER_CHARACTER_ID,
                sibling_cunit_id=sibling_cunit_id,
            ),
            postcheck=lambda snapshot: _post_retreat_switch_proof(
                snapshot,
                played_character_id=ORIGINAL_CHARACTER_ID,
                sibling_cunit_id=sibling_cunit_id,
            ),
        )
        reports["s5_return_switch"] = return_stage
        cleanup_flags.append(_managed_cleanup_ok(return_stage))
        if return_stage.get("ok") is not True:
            raise AgentError(
                str(return_stage.get("error") or "S5 return switch failed")
            )
        return_checkpoint = owner_live._checkpoint_path(return_spec)

        final_spec, materializations["p6_final_reassignment"] = (
            owner_live._prepare_stage(
                source_profile=source_profile,
                target_state=root / "p6-final-reassignment",
                game_dir=game_dir,
                save_source=return_checkpoint,
                save_name=CONTINUE_SAVE_NAME,
            )
        )
        final_stage = _run_final_reassignment_stage(
            spec=final_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            sibling_cunit_id=sibling_cunit_id,
            combat_id=combat_id,
            combat_province_id=combat_province_id,
            retained_same_side_order=retained_same_side_order,
            expected_date_raw=expected_date_raw,
            max_assignment_days=max_assignment_days,
            max_eta_days=max_eta_days,
        )
        reports["p6_final_reassignment"] = final_stage
        cleanup_flags.append(_managed_cleanup_ok(final_stage))
        if final_stage.get("ok") is not True:
            raise AgentError(
                str(final_stage.get("error") or "P6 final reassignment failed")
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"

    try:
        source_after = _sha256_file(source_save)
    except BaseException as error:
        source_after = None
        if primary_error is None:
            primary_error = f"{type(error).__name__}: {error}"
    source_unchanged = source_after == source_before
    all_sessions_clean = bool(
        cleanup_flags and all(cleanup_flags) and not ck3_processes()
    )
    cleanup = _cleanup_root(
        root,
        nonce=nonce,
        retain=bool(args.retain_state),
        all_sessions_clean=all_sessions_clean,
    )
    if not source_unchanged and primary_error is None:
        primary_error = "immutable source save changed"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(cleanup.get("reason") or "fixture cleanup failed")

    route_body = _managed_body(reports.get("p0_route_clear"))
    ally_body = _managed_body(reports.get("s1_ally_switch"))
    split_body = _managed_body(reports.get("p2_split_route"))
    requester_body = _managed_body(reports.get("s3_requester_switch"))
    retreat_body = _managed_body(reports.get("p4_contact_retreat"))
    return_body = _managed_body(reports.get("s5_return_switch"))
    final_body = _managed_body(reports.get("p6_final_reassignment"))
    parent_proof = retreat_body.get("parent_proof_immediately_before_retreat")
    parent_proof = parent_proof if isinstance(parent_proof, dict) else {}
    control_proof = retreat_body.get("control_proof_immediately_before_retreat")
    control_proof = control_proof if isinstance(control_proof, dict) else {}
    final_gates = final_body.get("readiness_gates")
    final_gates = final_gates if isinstance(final_gates, dict) else {}
    readiness_gates = {
        "production_route_clear_ready": route_body.get("ok") is True,
        "same_day_dynamic_ally_switch_ready": ally_body.get("ok") is True,
        "production_anchor_control_before_split_ready": (
            isinstance(split_body.get("before_split_control_proof"), dict)
            and split_body["before_split_control_proof"].get("ok") is True
        ),
        "production_three_cunit_split_route_ready": split_body.get("ok") is True,
        "same_day_requester_switch_ready": requester_body.get("ok") is True,
        "three_distinct_parent_rows_before_retreat_ready": parent_proof.get("ok")
        is True,
        "exact_owner_subset_control_before_retreat_ready": control_proof.get("ok")
        is True,
        "production_owner_subset_retreat_ready": retreat_body.get("ok") is True,
        "same_day_return_to_ai_ready": return_body.get("ok") is True,
        "retained_parent_can_ask_live_ready": final_gates.get(
            "retained_parent_can_ask_live_ready"
        )
        is True,
        "assignment_reopened_aligned_eta_live_ready": final_gates.get(
            "assignment_reopened_aligned_eta_live_ready"
        )
        is True,
        "same_combat_rejoin_live_ready": final_gates.get(
            "same_combat_rejoin_live_ready"
        )
        is True,
        "one_pid_generation_final_ready": final_gates.get(
            "one_pid_generation_live_ready"
        )
        is True,
        "source_save_unchanged": source_unchanged,
        "managed_cleanup_ready": all_sessions_clean,
        "disposable_state_cleanup_ready": cleanup.get("ok") is True,
    }
    ok = bool(primary_error is None and all(readiness_gates.values()))
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_three_cunit_owner_subset_reassignment_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "fixed_scenario": {
            "war_id": WAR_ID,
            "original_character_id": ORIGINAL_CHARACTER_ID,
            "requester_character_id": REQUESTER_CHARACTER_ID,
            "retained_character_id": RETAINED_CHARACTER_ID,
            "opposite_public_cunit_id": OPPOSITE_CUNIT_ID,
            "requester_public_cunit_id": REQUESTER_CUNIT_ID,
            "anchor_public_cunit_id": ANCHOR_CUNIT_ID,
            "dynamic_sibling_public_cunit_id": sibling_cunit_id,
            "combat_id": combat_id,
            "combat_province_id": combat_province_id,
            "retained_same_side_stored_order": retained_same_side_order,
            "requester_identity_claimed_for_assignment": False,
        },
        "bounds": {
            "max_split_wait_days": max_split_wait_days,
            "max_contact_days": max_contact_days,
            "max_assignment_days": max_assignment_days,
            "max_eta_days": max_eta_days,
            "one_game_day_raw": ONE_GAME_DAY_RAW,
        },
        "policy": {
            "seven_managed_stages": True,
            "seed_stages_only_switch_played_character": True,
            "split_retreat_and_final_observation_production_only": True,
            "required_pre_retreat_native_parent_subunit_rows": 3,
            "required_post_retreat_native_parent_subunit_rows": 2,
            "forbidden_native_calls": list(FORBIDDEN_NATIVE_CALLS),
            "forbidden_native_calls_invoked": [],
            "assignment_evidence_boundary": (
                "the assignment stores target and ETA facts, not requester identity"
            ),
        },
        "source_save": source_identity
        | {
            "before_sha256": source_before,
            "after_sha256": source_after,
            "unchanged": source_unchanged,
        },
        "stage_materializations": materializations,
        "stages": reports,
        "readiness_gates": readiness_gates,
        "state_cleanup": cleanup,
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
                "state_cleanup": payload.get("state_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
