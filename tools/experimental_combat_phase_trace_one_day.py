"""Bounded research driver for one original CK3 combat phase-event day.

This is an acceptance runner, not a gameplay policy or a probability source.
The caller owns an officially prepared, cold-restored native session and its
supervised CK3 process.  Any exception requires controlled process stop;
the frozen source pair is never resumed from this derived research state.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable


BEGIN = "experimental-combat-phase-event-trace-begin-v1"
FINISH = "experimental-combat-phase-event-trace-finish-v1"
CAPABILITY = "game.command.experimental-combat-phase-event-trace-managed-v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def verify_official_no_launch_pair(index_path: Path, index_sha256: str) -> dict[str, Any]:
    """Pin an official prepare/rebind/preflight pair before the first write."""
    if _sha256(index_path) != index_sha256.upper():
        raise ValueError("official no-launch index SHA-256 differs")
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if not isinstance(index, dict):
        raise ValueError("official no-launch index is malformed")
    if (index.get("status") != "NO_LAUNCH_READY" or
            index.get("profile") != "ordinary_campaign_succession/xar_off"):
        raise ValueError("official prepare/rebind/preflight binding is not green")
    files = index.get("files")
    if not isinstance(files, dict):
        raise ValueError("official pair file inventory is absent")
    for key in ("manifest", "preflight", "semantic", "rebind",
                "prepared_save", "prepared_driver", "exe", "dll", "injector"):
        item = files.get(key)
        if not isinstance(item, dict):
            raise ValueError(f"official pair lacks {key}")
        path = Path(item.get("path", ""))
        expected = item.get("sha256")
        if not path.is_file() or not isinstance(expected, str) or _sha256(path) != expected.upper():
            raise ValueError(f"official pair {key} SHA-256 differs")
    preflight = json.loads(Path(files["preflight"]["path"]).read_text(encoding="utf-8-sig"))
    expected = preflight.get("expected") if isinstance(preflight, dict) else None
    if (not isinstance(preflight, dict) or preflight.get("ok") is not True
            or preflight.get("status") != "ready"
            or preflight.get("ck3_launch_attempted") is not False
            or not isinstance(expected, dict)
            or expected.get("xar_enabled") != "xar_off"
            or expected.get("succession_lifecycle") != "ordinary_campaign_succession"
            or expected.get("episode_character_id") != index.get("actor")
            or expected.get("episode_run_id") != index.get("episode")
            or expected.get("checkpoint_sha256", "").upper() != files["prepared_save"]["sha256"].upper()
            or expected.get("driver_state_sha256", "").upper() != files["prepared_driver"]["sha256"].upper()):
        raise ValueError("official preflight identity or lifecycle differs")
    return index


def _frame(snapshot: object) -> tuple[int, int, int, str]:
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        raise ValueError("research trace requires a paused native frame")
    return (
        _positive_int(snapshot.get("revision"), "revision"),
        _positive_int(snapshot.get("native_revision"), "native_revision"),
        _positive_int(snapshot.get("date_raw"), "date_raw"),
        str(snapshot.get("episode_run_id")),
    )


def _private(driver: object, step: str, revision: int, fields: dict[str, int]) -> dict[str, Any]:
    capabilities = driver.capabilities()  # type: ignore[attr-defined]
    if CAPABILITY not in capabilities.get("bridge_capabilities", []):
        raise ValueError("native DLL does not expose the explicit research capability")
    result = driver._execute_primitive_step(  # type: ignore[attr-defined]
        step,
        expected_revision=revision,
        required_capability=CAPABILITY,
        request_fields=fields,
    )
    if not isinstance(result, dict) or result.get("step") != step or result.get("accepted") is not True:
        raise ValueError(f"{step} result is malformed")
    return result


def run_bounded_original_phase_event_day(
    driver: object,
    *,
    official_index: dict[str, Any],
    combat_id: int,
    subject_army_id: int,
    daily_token: int,
    deadline_seconds: float = 30.0,
    terminal_observation_sink: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Capture one day in a disposable, officially restored research session.

    The caller must run ``verify_official_no_launch_pair`` before cold launch,
    retain its index, and stop the CK3 process after this function returns or
    raises.  The function never restores or advances the frozen source pair.
    """
    _positive_int(combat_id, "combat_id")
    _positive_int(subject_army_id, "subject_army_id")
    _positive_int(daily_token, "daily_token")
    if not 0 < deadline_seconds <= 60:
        raise ValueError("bounded deadline must be in (0, 60] seconds")
    identity = official_index
    session_control = driver.capabilities().get("native_session_control")  # type: ignore[attr-defined]
    if (
        not isinstance(session_control, dict)
        or session_control.get("driver_state_restored") is not True
        or session_control.get("driver_state_restore_kind") != "cold_checkpoint"
        or session_control.get("driver_state_error") is not None
    ):
        raise ValueError("official cold checkpoint restore is not confirmed")
    starting = driver.take_snapshot()  # type: ignore[attr-defined]
    revision, native_revision, date_raw, episode = _frame(starting)
    if (identity.get("episode"), identity.get("date_raw")) != (episode, date_raw):
        raise ValueError("cold restored episode/date differs from official pair")
    played = starting.get("played_character")
    if not isinstance(played, dict) or played.get("character_id") != identity.get("actor"):
        raise ValueError("cold restored actor differs from official pair")
    battle = driver.execute_step(  # type: ignore[attr-defined]
        f"query-battle-control-snapshot-v1-{subject_army_id}",
        expected_revision=revision,
    )
    scope = battle.get("battle_control_snapshot") if isinstance(battle, dict) else None
    if (
        not isinstance(scope, dict)
        or battle.get("status") != "available"
        or scope.get("battle_control_ready") is not True
        or scope.get("combat_id") != combat_id
        or scope.get("observed_date_raw") != date_raw
        or scope.get("subject_public_cunit_id") != subject_army_id
        or battle.get("queried_native_revision") != native_revision
    ):
        raise ValueError("fresh same-CombatID battle-control proof is absent")
    if (
        scope.get("phase_raw") != 1
        or isinstance(scope.get("phase_day"), bool)
        or not isinstance(scope.get("phase_day"), int)
        or scope["phase_day"] < 0
        or scope.get("winner_raw") != -1
        or scope.get("forced_winner_raw") != -1
        or scope.get("finalized") is not False
        or any(
            not isinstance(scope.get(side), dict)
            or scope[side].get("stored_current_matches_derived") is not True
            or isinstance(scope[side].get("stored_current_fighting_raw"), bool)
            or not isinstance(scope[side].get("stored_current_fighting_raw"), int)
            or scope[side]["stored_current_fighting_raw"] <= 0
            for side in ("attacker", "defender")
        )
    ):
        raise ValueError("seven-boundary trace requires an undecided main phase with both sides fighting")

    saved = driver.execute_step("save-checkpoint", expected_revision=revision)  # type: ignore[attr-defined]
    checkpoint = saved.get("checkpoint") if isinstance(saved, dict) else None
    submission = saved.get("submission") if isinstance(saved, dict) else None
    if not isinstance(checkpoint, dict) or checkpoint.get("status") != "saved" or not isinstance(submission, dict):
        raise ValueError("native checkpoint did not materialize")
    checkpoint_path = Path(checkpoint.get("path", ""))
    receipt_sha256 = checkpoint.get("sha256")
    if (
        not checkpoint_path.is_file()
        or checkpoint_path.stat().st_size != checkpoint.get("size")
        or not isinstance(receipt_sha256, str)
        or len(receipt_sha256) != 64
        or any(character not in "0123456789abcdef" for character in receipt_sha256)
        or _sha256(checkpoint_path).lower() != receipt_sha256
        or checkpoint.get("date_raw") != date_raw
    ):
        raise ValueError("materialized checkpoint SHA/date/size differs")
    checkpoint_sequence = _positive_int(submission.get("sequence"), "checkpoint_sequence")
    if submission.get("date_raw") != date_raw:
        raise ValueError("checkpoint submission date differs")
    now = driver.take_snapshot()  # type: ignore[attr-defined]
    new_revision, _, new_date, new_episode = _frame(now)
    if (new_date, new_episode) != (date_raw, episode):
        raise ValueError("checkpoint crossed the original paused frame")

    fields = {"combat_id": combat_id, "managed_daily_sequence_token": daily_token}
    try:
        begin = _private(driver, BEGIN, new_revision, {**fields, "checkpoint_sequence": checkpoint_sequence})
        if begin.get("status") != "armed" or begin.get("managed_daily_sequence_token") != daily_token:
            raise ValueError("native managed trace did not arm")
    except Exception:
        # The request may have reached application-main before a transport
        # error. Attempt a same-frame finish, then require supervised stop.
        try:
            _private(driver, FINISH, new_revision, fields)
        except Exception:
            pass
        raise
    armed = True
    timeline: list[dict[str, Any]] = []
    ending: dict[str, Any] | None = None
    finish: dict[str, Any] | None = None
    try:
        timeline.append(driver.execute_step("set-speed-1"))  # type: ignore[attr-defined]
        timeline.append(driver.execute_step("resume-map"))  # type: ignore[attr-defined]
        deadline = time.monotonic() + deadline_seconds
        observed = driver.take_snapshot()  # type: ignore[attr-defined]
        while observed.get("paused") is not False and time.monotonic() < deadline:
            if (observed.get("date_raw"), observed.get("episode_run_id")) != (date_raw, episode):
                break
            time.sleep(0.1)
            observed = driver.take_snapshot()  # type: ignore[attr-defined]
        if observed.get("paused") is not False:
            raise ValueError("resume-map did not yield a running native frame")
        while time.monotonic() < deadline:
            observed = driver.take_snapshot()  # type: ignore[attr-defined]
            observed_date = observed.get("date_raw") if isinstance(observed, dict) else None
            if observed_date != date_raw or observed.get("paused") is True:
                break
            time.sleep(0.1)
        timeline.append(driver.execute_step("pause-map"))  # type: ignore[attr-defined]
        ending = driver.take_snapshot()  # type: ignore[attr-defined]
        pause_deadline = time.monotonic() + min(deadline_seconds, 10.0)
        while ending.get("paused") is not True and time.monotonic() < pause_deadline:
            time.sleep(0.1)
            ending = driver.take_snapshot()  # type: ignore[attr-defined]
        ending_revision, _, ending_date, ending_episode = _frame(ending)
        if ending_episode != episode:
            raise ValueError("original trace changed episode")
        finish = _private(driver, FINISH, ending_revision, fields)
        armed = False
        if terminal_observation_sink is not None:
            terminal_observation_sink({
                "schema": "xar.ck3.experimental-combat-phase-terminal-observation/v1",
                "ending": {
                    "revision": ending_revision,
                    "native_revision": ending["native_revision"],
                    "date_raw": ending_date,
                    "episode_run_id": ending_episode,
                    "paused": ending["paused"],
                },
                "private_finish": finish,
            })
        if ending_date != date_raw + 24 or finish.get("status") != "bounded_trace_available":
            raise ValueError("original trace did not produce one exact bounded day")
        managed = finish.get("managed_trace")
        checkpoint_proof = managed.get("managed_checkpoint") if isinstance(managed, dict) else None
        if (
            not isinstance(checkpoint_proof, dict)
            or checkpoint_proof.get("recoverable_checkpoint_created") is not True
            or checkpoint_proof.get("exact_one_day_observed") is not True
            or checkpoint_proof.get("detours_uninstalled") is not True
            or checkpoint_proof.get("before", {}).get("combat_id") != combat_id
            or checkpoint_proof.get("after", {}).get("combat_id") != combat_id
        ):
            raise ValueError("managed seven-boundary checkpoint proof is incomplete")
        return {
            "status": "bounded_original_trace_observed",
            "production_trace_ready": False,
            "win_probability_available": False,
            "source_save_sha256": official_index["files"]["prepared_save"]["sha256"],
            "research_checkpoint_sha256": checkpoint["sha256"],
            "combat_id": combat_id,
            "daily_token": daily_token,
            "starting_native_revision": native_revision,
            "starting_date_raw": date_raw,
            "ending_date_raw": ending_date,
            "battle_control_probe": battle,
            "begin": begin,
            "timeline": timeline,
            "finish": finish,
            "requires_controlled_stop_and_new_official_restore": True,
        }
    finally:
        if armed:
            # Finish also drains/uninstalls on a short or failed day. If this
            # cleanup fails, the supervised wrapper must stop the CK3 process.
            try:
                current = driver.take_snapshot()  # type: ignore[attr-defined]
                if current.get("paused") is not True:
                    driver.execute_step("pause-map")  # type: ignore[attr-defined]
                    current = driver.take_snapshot()  # type: ignore[attr-defined]
                current_revision, _, _, _ = _frame(current)
                _private(driver, FINISH, current_revision, fields)
            except Exception:
                pass
