"""Cold-load one hash-bound CoA campaign checkpoint and prove its identity."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import threading
import time


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.environment import ensure_state_path_safe, make_spec  # noqa: E402
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


EXPECTED_CK3_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--expected-prior-pid", type=int, required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--expected-date-raw", type=int, required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    state_dir = args.state_dir.resolve()
    ensure_state_path_safe(state_dir)
    spec = make_spec(state_dir, args.game_dir.resolve())
    checkpoint = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    before_sha256 = _sha256(checkpoint)
    expected_sha256 = args.expected_checkpoint_sha256.lower()
    if before_sha256 != expected_sha256:
        raise RuntimeError("checkpoint SHA-256 differs before cold reload")
    if _sha256(spec.game_exe).upper() != EXPECTED_CK3_SHA256:
        raise RuntimeError("CK3 executable SHA-256 differs from the exact-build pin")

    config = NativeBridgeLaunchConfig(
        mode="native-headless",
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.resolve(),
        injector_path=args.bridge_injector.resolve(),
    )
    driver = NativeHeadlessGameplayDriver(
        config.pipe_name,
        state_dir=state_dir,
        save_dir=spec.profile_dir / "save games",
    )
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=float(args.timeout) + 30.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=True,
                stop_event=stop_event,
                verify_prepared_profile=False,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    session_thread = threading.Thread(
        target=supervise,
        name="xar-coa-campaign-cold-reload-v1",
        daemon=False,
    )
    primary_error: str | None = None
    snapshot: dict[str, object] | None = None
    stable_snapshot: dict[str, object] | None = None
    campaign_root: dict[str, object] | None = None
    session_thread.start()
    deadline = time.monotonic() + float(args.timeout)
    try:
        while time.monotonic() < deadline:
            if session_done.is_set():
                raise RuntimeError(
                    str(session_state.get("error") or "native-session exited early")
                )
            try:
                candidate = driver.take_snapshot()
            except Exception:
                time.sleep(0.25)
                continue
            played = candidate.get("played_character")
            if (
                candidate.get("paused") is True
                and candidate.get("map_ready") is True
                and isinstance(played, dict)
                and played.get("character_id") == args.expected_character_id
                and candidate.get("date_raw") == args.expected_date_raw
            ):
                snapshot = candidate
                break
            time.sleep(0.25)
        if snapshot is None:
            raise RuntimeError("expected paused checkpoint identity was not observed")
        stable_snapshot = driver._wait_for_frontend_start_post_ready_pump_v1(
            snapshot
        )
        campaign_root = driver._execute_campaign_root_context_v1_query(
            expected_revision=None
        )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_event.set()
        session_thread.join()
        driver.close()

    after_sha256 = _sha256(checkpoint)
    diagnostics = (
        stable_snapshot.get("diagnostics")
        if isinstance(stable_snapshot, dict)
        else None
    )
    played = (
        stable_snapshot.get("played_character")
        if isinstance(stable_snapshot, dict)
        else None
    )
    session_report = session_state.get("report")
    shutdown = (
        session_report.get("shutdown")
        if isinstance(session_report, dict)
        else None
    )
    checks = {
        "checkpoint_hash_unchanged": (
            before_sha256 == expected_sha256 == after_sha256
        ),
        "replacement_pid": bool(
            isinstance(diagnostics, dict)
            and diagnostics.get("bridge_pid") != args.expected_prior_pid
        ),
        "paused_map_ready": bool(
            isinstance(stable_snapshot, dict)
            and stable_snapshot.get("paused") is True
            and stable_snapshot.get("map_ready") is True
        ),
        "stable_character_identity": bool(
            isinstance(played, dict)
            and played.get("character_id") == args.expected_character_id
        ),
        "stable_date": bool(
            isinstance(stable_snapshot, dict)
            and stable_snapshot.get("date_raw") == args.expected_date_raw
        ),
        "campaign_root_identity": bool(
            isinstance(campaign_root, dict)
            and campaign_root.get("campaign_root_context_ready") is True
            and campaign_root.get("player_character_id")
            == args.expected_character_id
            and campaign_root.get("date_raw") == args.expected_date_raw
        ),
        "cleanup_proven": bool(
            isinstance(session_report, dict)
            and session_report.get("ok") is True
            and isinstance(shutdown, dict)
            and shutdown.get("cleanup_proven") is True
            and shutdown.get("tree_gone") is True
        ),
    }
    ok = primary_error is None and all(checks.values())
    report: dict[str, object] = {
        "schema": "xar.ck3.coa-campaign-cold-reload-v1",
        "schema_version": 1,
        "created_at": utc_now(),
        "ok": ok,
        "status": "GREEN" if ok else "RED",
        "checkpoint": {
            "path": str(checkpoint.resolve()),
            "bytes": checkpoint.stat().st_size,
            "sha256_before": before_sha256,
            "sha256_after": after_sha256,
        },
        "expected": {
            "prior_pid": args.expected_prior_pid,
            "character_id": args.expected_character_id,
            "date_raw": args.expected_date_raw,
        },
        "stable_snapshot": stable_snapshot,
        "campaign_root": campaign_root,
        "session": session_report,
        "session_error": session_state.get("error"),
        "checks": checks,
        "error": primary_error,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    _write_json(args.output.resolve(), report)
    return report, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    try:
        report, exit_code = _run(args)
    except BaseException as error:
        print(f"CoA campaign cold reload setup failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
