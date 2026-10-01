#!/usr/bin/env python3
"""Run one coordinator-owned isolated migration session and preserve wire data.

The caller prepares the state/profile first. This tool owns only the session
it launches through native_session; it never attaches to another CK3 process
or uses desktop input. Source saves and the real user profile are not edited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid

_source_parser = argparse.ArgumentParser(add_help=False)
_source_parser.add_argument("--agent-source-root", type=Path)
_source_args, _ = _source_parser.parse_known_args()
AGENT_SOURCE_ROOT = (
    _source_args.agent_source_root or Path(os.environ.get(
        "XAR_MIGRATION_AGENT_SOURCE_ROOT", str(Path(__file__).resolve().parents[2] / "src")
    ))
).resolve()
sys.path.insert(0, str(AGENT_SOURCE_ROOT))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import QUERY_ARMY_STRENGTHS_STEP, army_strength_scope
from xar_autoplayer.environment import make_spec, verify_profile
from xar_autoplayer.native_auto_run import _cleanup_report, _wait_for_readiness
from xar_autoplayer.native_session import native_session
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now


EXPECTED_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
EXPECTED_ADAPTER = "ck3-1.20.0.2-msvc-x64"
QUERY_NAMES = ("campaign-root", "features", "army-strength", "declarable-wars", "marriage")


class RecordingDriver(NativeHeadlessGameplayDriver):
    def __init__(self, *args: object, wire_path: Path, **kwargs: object) -> None:
        self._wire_path = wire_path
        self._wire_lock = threading.Lock()
        super().__init__(*args, **kwargs)

    def _ingest(self, frame: dict[str, object]) -> None:
        with self._wire_lock:
            with self._wire_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"received_at": utc_now(), "frame": frame}, ensure_ascii=False) + "\n")
        super()._ingest(frame)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--state-dir", type=Path, required=True, help="already prepared disposable managed state")
    result.add_argument("--agent-source-root", type=Path, help="clean committed package src directory")
    result.add_argument("--game-dir", type=Path, required=True)
    result.add_argument("--bridge-dll", type=Path, required=True)
    result.add_argument("--bridge-injector", type=Path, required=True)
    result.add_argument("--bridge-pipe", default=None)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--timeout", type=float, default=300)
    result.add_argument("--command-timeout", type=float, default=60)
    result.add_argument("--queries", nargs="*", choices=QUERY_NAMES, default=list(QUERY_NAMES[:3]))
    result.add_argument("--private-step", action="append", default=[], help="one-off native diagnostic step, preserved without the public typed parser")
    result.add_argument("--hold-seconds", type=float, default=0, help="keep the owned session after the probe before tracked cleanup")
    return result


def run(args: argparse.Namespace) -> dict[str, object]:
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    wire_path = output.with_suffix(".wire.jsonl")
    spec = make_spec(args.state_dir.resolve(), args.game_dir.resolve())
    config = NativeBridgeLaunchConfig(
        mode="native-headless",
        pipe_name=args.bridge_pipe or (r"\\.\pipe\xar-ck3-migration-12002-" + uuid.uuid4().hex),
        dll_path=args.bridge_dll.resolve(),
        injector_path=args.bridge_injector.resolve(),
    )
    stop = threading.Event()
    done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    report: dict[str, object] = {
        "status": "RUNNING", "started_at": utc_now(), "game_version": "1.20.0.2",
        "state_dir": str(spec.state_dir), "pipe": config.pipe_name, "wire_path": str(wire_path),
        "agent_source_root": str(AGENT_SOURCE_ROOT),
        "queries": [], "diagnostics": [], "session": session_state,
        "capabilities": None, "snapshot": None, "error": None,
    }

    def write() -> None:
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec, timeout_seconds=args.timeout + args.hold_seconds + 90,
                native_bridge=config, stop_event=stop, input_stream=None, output_stream=None,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            done.set()

    driver = None
    session_thread = None
    driver_closed = False
    write()
    try:
        report["profile"] = verify_profile(spec)
        report["identity"] = {
            "executable": str(spec.game_exe), "executable_sha256": sha256(spec.game_exe),
            "bridge_dll": str(config.dll_path), "bridge_dll_sha256": sha256(config.dll_path),
            "injector": str(config.injector_path), "injector_sha256": sha256(config.injector_path),
        }
        if report["identity"]["executable_sha256"] != EXPECTED_SHA:
            raise RuntimeError("migration probe requires the frozen 1.20.0.2 executable")
        driver = RecordingDriver(
            config.pipe_name, wire_path=wire_path, state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games", command_timeout_seconds=args.command_timeout,
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(target=supervise, name="ck3-12002-migration-session", daemon=False)
        session_thread.start()
        report["readiness"] = _wait_for_readiness(
            driver, session_done=done, session_state=session_state, timeout_seconds=args.timeout,
            stable_seconds=0.5, poll_interval_seconds=0.05,
            cold_start_checkpoint=False, allow_terminal=False,
        )
        capabilities = driver.capabilities()
        report["capabilities"] = capabilities
        report["snapshot"] = service.snapshot()
        diagnostics = capabilities.get("diagnostics", {})
        hello = diagnostics.get("hello", {})
        if hello.get("game_adapter_id") != EXPECTED_ADAPTER or hello.get("expected_ck3_sha256") != EXPECTED_SHA:
            raise RuntimeError("actual native hello does not match the migration build")
        write()
        methods = {
            "campaign-root": service.query_campaign_root_context_v1,
            "features": service.query_loaded_feature_manifest_v1,
            "army-strength": service.query_army_strengths,
            "declarable-wars": service.query_declarable_wars,
            "marriage": service.query_arrange_marriage_choices,
        }
        for name in args.queries:
            attempt: dict[str, object] = {"name": name, "started_at": utc_now()}
            report["queries"].append(attempt)
            try:
                before = service.snapshot()
                attempt["before_snapshot"] = before
                revision = int(before["revision"])
                if name == "army-strength":
                    army_ids = [int(row["army_id"]) for row in army_strength_scope(before)][:64]
                    attempt["army_ids"] = army_ids
                    attempt["result"] = (
                        service.query_army_strengths(army_ids, expected_revision=revision)
                        if army_ids else service.execute_step(QUERY_ARMY_STRENGTHS_STEP, expected_revision=revision)
                    )
                else:
                    attempt["result"] = methods[name](expected_revision=revision)
                attempt["after_snapshot"] = service.snapshot()
                attempt["ok"] = True
            except BaseException as error:
                attempt["ok"] = False
                attempt["error"] = f"{type(error).__name__}: {error}"
            attempt["finished_at"] = utc_now()
            write()
        for step in args.private_step:
            attempt = {"step": step, "started_at": utc_now()}
            report["diagnostics"].append(attempt)
            try:
                before = service.snapshot()
                attempt["before_snapshot"] = before
                attempt["result"] = driver._execute_primitive_step(
                    step, expected_revision=int(before["revision"]),
                    required_capability="game.adapter.exact-build",
                )
                attempt["after_snapshot"] = service.snapshot()
                attempt["ok"] = True
            except BaseException as error:
                attempt["ok"] = False
                attempt["error"] = f"{type(error).__name__}: {error}"
            attempt["finished_at"] = utc_now()
            write()
        deadline = time.monotonic() + args.hold_seconds
        while not done.is_set() and time.monotonic() < deadline:
            time.sleep(min(0.25, deadline - time.monotonic()))
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if driver is not None:
            try:
                report["capabilities_final"] = driver.capabilities()
                report["snapshot_final"] = driver.take_snapshot()
            except BaseException as error:
                report["final_observation_error"] = f"{type(error).__name__}: {error}"
        stopped_at = time.monotonic()
        stop.set()
        if session_thread is not None:
            session_thread.join()
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                report["driver_close_error"] = f"{type(error).__name__}: {error}"
        report["cleanup"] = _cleanup_report(
            session_state["report"], session_error=session_state["error"],
            driver_closed=driver_closed, elapsed_seconds=time.monotonic() - stopped_at,
        )
        report["finished_at"] = utc_now()
        report["status"] = "GREEN" if (
            report["error"] is None and report.get("readiness") is not None
            and all(row.get("ok") is True for row in report["queries"])
            and all(row.get("ok") is True for row in report["diagnostics"])
            and report["cleanup"].get("ok") is True
        ) else "RED"
        write()
    return report


def main() -> int:
    args = parser().parse_args()
    if args.timeout <= 0 or args.command_timeout <= 0 or args.hold_seconds < 0:
        raise SystemExit("timeouts must be positive and hold seconds nonnegative")
    report = run(args)
    print(json.dumps({"status": report["status"], "output": str(args.output.resolve()), "error": report["error"]}, ensure_ascii=False))
    return 0 if report["status"] == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
