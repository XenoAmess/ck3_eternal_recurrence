"""Bounded, read-only exact-native reroute research from one cold checkpoint.

This is not a production policy entry or a gameplay acceptance result.  It
launches the managed native session, asks only native move previews and full
hostile contact horizons, and always stops the session without an action or
date advance.  No target is presumed safe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--round", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    source = Path(manifest["source_repo"]).resolve()
    sys.path.insert(0, str(source / "ck3_autonomous_player" / "src"))

    from xar_autoplayer.bridge.native_driver import (
        NativeHeadlessGameplayDriver,
        _route_contact_hostile_ids,
    )
    from xar_autoplayer.bridge.war_contract import (
        preview_move_army_step,
        query_route_contact_horizon_step,
    )
    from xar_autoplayer.bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION,
        bind_succession_lifecycle_from_environment_v1,
    )
    from xar_autoplayer.environment import make_spec
    from xar_autoplayer.native_auto_run import (
        READINESS_POLL_SECONDS,
        READINESS_STABLE_SECONDS,
        SESSION_TIMEOUT_GRACE_SECONDS,
        _cleanup_report,
        _wait_for_readiness,
    )
    from xar_autoplayer.native_session import (
        native_session,
        validate_cold_start_checkpoint_for_pipe,
    )
    from xar_autoplayer.runtime import (
        configure_native_bridge_launch_environment,
    )

    timeout = min(float(manifest["timeout_seconds"]), 300.0)
    readiness_timeout = min(float(manifest["readiness_timeout_seconds"]), 180.0)
    state = Path(manifest["state_dir"]).resolve()
    save = state / "profile" / "save games" / "xar_checkpoint.ck3"
    driver_file = state / "native-session" / "driver-state.json"
    before = {"save_sha256": sha(save), "driver_sha256": sha(driver_file)}
    if before["save_sha256"].lower() != manifest["checkpoint_sha256"].lower():
        raise RuntimeError("prelaunch checkpoint SHA mismatch")
    if before["driver_sha256"].lower() != manifest["driver_state_sha256"].lower():
        raise RuntimeError("prelaunch driver SHA mismatch")
    spec = make_spec(state, Path(manifest["game_dir"]))
    config = configure_native_bridge_launch_environment(
        "native-headless",
        pipe_name=manifest["pipe"],
        dll_path=Path(manifest["dll"]),
        injector_path=Path(manifest["injector"]),
    )
    assert config is not None
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
    if checkpoint.get("saved_date_raw") != manifest["date_raw"] or checkpoint.get("history_index") != 1566:
        raise RuntimeError("cold checkpoint anchor mismatch")
    environment_manifest = json.loads(spec.manifest_path.read_text(encoding="utf-8-sig"))
    succession_lifecycle_binding = bind_succession_lifecycle_from_environment_v1(
        environment_manifest,
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
        ordinary_campaign_no_pact=True,
    )
    if (manifest["xar_enabled"], manifest["succession_lifecycle"]) != (
        succession_lifecycle_binding["xar_enabled"],
        succession_lifecycle_binding["lifecycle"],
    ):
        raise RuntimeError("run manifest differs from prepared lifecycle")
    persisted_driver = json.loads(driver_file.read_text(encoding="utf-8"))
    if (
        checkpoint.get("succession_lifecycle") != succession_lifecycle_binding
        or persisted_driver.get("succession_lifecycle") != succession_lifecycle_binding
    ):
        raise RuntimeError("cold checkpoint/driver lifecycle differs from prepared profile")
    if args.preflight_only:
        report = {
            "schema": "xar.ck3.private-read-only-reroute-preflight/v1",
            "round": args.round,
            "status": "NO_LAUNCH_GREEN",
            "ck3_launch_attempted": False,
            "checkpoint": checkpoint,
            "succession_lifecycle": succession_lifecycle_binding,
            "files": before,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"round": args.round, "status": report["status"], "report": str(args.report)}))
        return 0

    started = time.monotonic()
    deadline = started + timeout
    stop_event = threading.Event()
    done = threading.Event()
    session_state = {"report": None, "error": None}
    driver = None
    session_thread = None
    observations = []
    error = None
    readiness = None
    first = None
    last = None
    cleanup = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + SESSION_TIMEOUT_GRACE_SECONDS,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=READINESS_POLL_SECONDS,
                cold_start_checkpoint=True,
                stop_event=stop_event,
                prepared_xar_enabled=manifest["xar_enabled"],
            )
        except BaseException as exc:
            session_state["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=state,
            save_dir=spec.profile_dir / "save games",
            succession_lifecycle_binding=succession_lifecycle_binding,
        )
        session_thread = threading.Thread(target=supervise, daemon=False)
        session_thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=done,
            session_state=session_state,
            timeout_seconds=min(readiness_timeout, max(0.001, deadline - time.monotonic())),
            stable_seconds=READINESS_STABLE_SECONDS,
            poll_interval_seconds=READINESS_POLL_SECONDS,
            cold_start_checkpoint=True,
            allow_terminal=True,
            require_post_ready_pump=True,
        )
        first = driver.take_internal_semantic_snapshot()
        if not (
            first.get("paused") is True
            and first.get("map_ready") is True
            and first.get("date_raw") == manifest["date_raw"]
            and first.get("episode_run_id") == manifest["episode_run_id"]
            and first.get("episode_character_id") == manifest["episode_character_id"]
            and isinstance(first.get("played_character"), dict)
            and first["played_character"].get("character_id") == manifest["episode_character_id"]
            and first["played_character"].get("alive") is True
            and first.get("active_event") is None
            and first.get("pending_character_interaction") is None
        ):
            raise RuntimeError("fresh paused actor/episode/date/pending binding mismatch")
        wars = first.get("active_wars")
        armies = first.get("player_armies")
        if not isinstance(wars, list) or not any(w.get("war_id") == 251658364 for w in wars if isinstance(w, dict)):
            raise RuntimeError("expected defender war absent")
        if not isinstance(armies, list) or not any(a.get("army_id") == 419430662 for a in armies if isinstance(a, dict)):
            raise RuntimeError("expected subject army absent")
        hostile_ids = _route_contact_hostile_ids(first)
        if not hostile_ids:
            raise RuntimeError("complete hostile scope unavailable")
        # Historical targets only: current sea province and prior committed
        # route provinces; this is research, not an autonomous selector.
        for target in (715, 975, 714, 700, 699, 45):
            if time.monotonic() >= deadline:
                raise TimeoutError("bounded probe deadline reached")
            step = preview_move_army_step(419430662, target)
            row = {"target": target, "preview_step": step}
            try:
                result = driver._execute_native_war_step(
                    step, expected_revision=first["revision"]
                )
                driver._record_command(step, ok=True, result=result)
                row["preview"] = result
                route = result.get("route_preview") if isinstance(result, dict) else None
                if isinstance(route, dict) and route.get("status") == "available":
                    contact_step = query_route_contact_horizon_step(
                        419430662, target, hostile_ids
                    )
                    contact = driver._execute_native_war_step(
                        contact_step, expected_revision=first["revision"]
                    )
                    driver._record_command(contact_step, ok=True, result=contact)
                    row["contact_step"] = contact_step
                    row["contact"] = contact
            except BaseException as exc:
                driver._record_command(step, ok=False, result=None, error=f"{type(exc).__name__}: {exc}")
                row["error"] = f"{type(exc).__name__}: {exc}"
            observations.append(row)
            last = driver.take_internal_semantic_snapshot()
            if any(last.get(k) != first.get(k) for k in ("date_raw", "snapshot_id", "native_revision", "episode_run_id")) or last.get("paused") is not True:
                raise RuntimeError("read-only query crossed paused native frame")
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        stop_event.set()
        if session_thread is not None:
            session_thread.join()
        driver_closed = False
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as exc:
                error = (error + "; " if error else "") + f"driver close: {type(exc).__name__}: {exc}"
        cleanup = _cleanup_report(
            session_state["report"],
            session_error=session_state["error"],
            driver_closed=driver_closed,
            elapsed_seconds=0,
        )
    after = {"save_sha256": sha(save), "driver_sha256": sha(driver_file)}
    if after["save_sha256"] != before["save_sha256"]:
        error = (error + "; " if error else "") + "save bytes changed"
    if cleanup.get("ok") is not True:
        error = (error + "; " if error else "") + f"cleanup unproven: {cleanup}"
    report = {
        "schema": "xar.ck3.private-read-only-reroute-probe/v1",
        "round": args.round,
        "status": "RED" if error else "QUERY_COMPLETE_SAFETY_UNASSESSED",
        "error": error,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "checkpoint": checkpoint,
        "before_files": before,
        "after_files": after,
        "readiness": readiness,
        "first_frame": first,
        "last_frame": last,
        "observations": observations,
        "cleanup": cleanup,
        "forbidden_action_counts": {"move": 0, "termination": 0, "date_advance": 0, "gameplay": 0},
        "production_policy_evidence": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"round": args.round, "status": report["status"], "error": error, "elapsed_seconds": report["elapsed_seconds"], "report": str(args.report)}, ensure_ascii=False))
    return 0 if error is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
