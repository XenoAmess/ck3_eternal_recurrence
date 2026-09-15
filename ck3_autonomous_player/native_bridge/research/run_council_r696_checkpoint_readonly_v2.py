"""Cold-load the R696 checkpoint and read Council incumbent; submit no action."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
import traceback
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

MANIFEST_SCHEMA = "xar.ck3.g2_m4_council_r696_checkpoint_readonly_sealed_v2"
OPERATOR_SCHEMA = "xar.ck3.g2_m4_council_r696_checkpoint_readonly_operator_v2"
CHECKPOINT_SHA = "599B9EEE2E2C78A2AA341567FE5C52C36A1292AE1C5F8F00A231E2D7DCA27F64"
EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
GATE_DLL_SHA = "77515453226DEE89E24044BB4B173F795258FCAFE44F3C5EA1CE5E75159ECA8D"
INJECTOR_SHA = "09E35E9E86FF714CBA8D716223C951EAC271DBDEFA8C6C638B0765D265A99D51"
QUERY = "private-query-council-final-gates-v1"
STATUS = "private-council-application-main-status-v1"
ENVELOPE_SCHEMA = "xar.ck3.council-application-main/v1"
GATE_SCHEMA = "xar.ck3.private.council-final-gates/v1"
PUBLIC_SCHEMA = "xar.ck3.council-composition-candidates/v1"


class HeldLaunchLocks(ExitStack):
    def __exit__(self, *arguments: object) -> bool:
        return False

    def close(self) -> None:
        ExitStack.__exit__(self, None, None, None)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def verify(root: Path) -> dict[str, object]:
    root = root.resolve()
    manifest_path = root / "sealed-prep-manifest.json"
    checksum = (root / "sealed-prep-manifest.sha256").read_text(encoding="ascii").split()[0]
    require(sha256(manifest_path) == checksum.upper(), "sealed manifest checksum differs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("schema") == MANIFEST_SCHEMA and
            manifest.get("status") == "sealed-no-launch" and
            manifest.get("read_only") is True and
            manifest.get("private_assign_admitted") is False and
            manifest.get("public_council_advertised") is False,
            "read-only sealed identity differs")
    rows = manifest.get("files")
    require(isinstance(rows, list) and len(rows) == manifest.get("file_count"),
            "sealed file count differs")
    for row in rows:
        relative = row.get("path") if isinstance(row, dict) else None
        require(isinstance(relative, str), "sealed file row path absent")
        path = (root / relative).resolve()
        require(path.is_relative_to(root) and path.is_file() and
                path.stat().st_size == row.get("size_bytes") and
                sha256(path) == row.get("sha256"),
                f"sealed file differs: {relative}")
    operator = json.loads((root / "operator-runtime.json").read_text(encoding="utf-8"))
    require(operator.get("schema") == OPERATOR_SCHEMA and
            operator.get("round_allocated") is False and
            operator.get("last_completed_council_round") == "R696" and
            [operator.get("readiness_timeout_seconds"),
             operator.get("query_timeout_seconds"),
             operator.get("overall_window_seconds")] == [300, 60, 480] and
            operator.get("pipe") ==
            r"\\.\pipe\xar_ck3_bridge_g2_m4_council_r696_restore_72882e69",
            "bounded operator configuration differs")
    game = Path(str(operator["game_dir"]))
    python = Path(str(operator["python"]))
    require(sha256(game / "binaries" / "ck3.exe") == EXE_SHA and
            sha256(python) == manifest.get("python_exe_sha256"),
            "operator EXE/Python exact build differs")
    source = root / "source-checkpoint" / "xar_checkpoint.ck3"
    target = root / "fresh-profile-state" / "profile" / "save games" / "xar_checkpoint.ck3"
    require(sha256(source) == CHECKPOINT_SHA and
            sha256(target) == CHECKPOINT_SHA and
            source.stat().st_size == manifest.get("checkpoint_size_bytes") and
            source.open("rb").read(7) == b"SAV0101",
            "R696 source/target material checkpoint differs")
    cache = (root / "candidate-bin" / "CMakeCache.txt").read_text(
        encoding="utf-8", errors="replace")
    for key, value in manifest["cmake_options"].items():
        require(f"{key}:BOOL={value}" in cache,
                f"gate-only native build option differs: {key}")
    require(sha256(root / "candidate-bin" / "xar_ck3_bridge.dll") == GATE_DLL_SHA and
            sha256(root / "candidate-bin" / "xar_ck3_bridge_injector.exe") == INJECTOR_SHA and
            manifest.get("bridge_dll_sha256") == GATE_DLL_SHA and
            manifest.get("injector_sha256") == INJECTOR_SHA,
            "gate-only DLL or injector differs")
    descriptor = root / "fresh-profile-state" / "profile" / "mod" / "xar_autoplayer.mod"
    mod_path = (root / "fresh-profile-state" / "profile" / "mod-content"
                / "xar-production").as_posix()
    require(f'path="{mod_path}"' in descriptor.read_text(encoding="utf-8-sig"),
            "private profile mod descriptor differs")
    dlc = root / "fresh-profile-state" / "profile" / "dlc_load.json"
    require(json.loads(dlc.read_text(encoding="utf-8-sig")) == {
        "enabled_mods": ["mod/xar_autoplayer.mod"], "disabled_dlcs": []},
        "frozen DLC/mod loading differs")
    return {"status": "green-no-launch", "checkpoint_sha256": CHECKPOINT_SHA,
            "r696_red_report_sha256": manifest["r696_red_report_sha256"],
            "native_source_commit": manifest["native_source_commit"],
            "bridge_dll_sha256": GATE_DLL_SHA, "injector_sha256": INJECTOR_SHA,
            "game_exe_sha256": EXE_SHA, "pipe": operator["pipe"],
            "file_count": len(rows), "ck3_launched": False,
            "action_helper_admitted": False}


def command(driver: object, step: str, request_id: str, revision: int,
            wait_seconds: float) -> dict[str, object]:
    frame = {"type": "execute_step", "protocol_version": 1,
             "request_id": request_id, "step": step,
             "expected_revision": revision}
    driver.endpoint.send(frame)
    result = driver.state.wait_for_command_result(request_id, wait_seconds)
    require(isinstance(result, dict), f"read-only command timed out: {step}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--new-round", help="new persistent round allocated by sole CK3 owner")
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    preflight = verify(root)
    if args.preflight_only:
        print(json.dumps(preflight, sort_keys=True))
        return 0
    require(isinstance(args.new_round, str) and args.new_round.startswith("R") and
            args.new_round[1:].isdigit() and int(args.new_round[1:]) > 696,
            "sole CK3 owner must allocate a fresh round after R696")
    round_id = args.new_round
    operator = json.loads((root / "operator-runtime.json").read_text(encoding="utf-8"))
    source_repo = root / "source-repo"
    sys.path[:0] = [str(source_repo / "ck3_autonomous_player" / "src"),
                    str(source_repo / "tools")]
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
    from xar_autoplayer.native_auto_run import _wait_for_readiness
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch, stop_tracked

    evidence = root / f"live-{round_id.lower()}"
    require(not evidence.exists(), f"{round_id} attempt already exists; do not reuse")
    evidence.mkdir(parents=True)
    report: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_council_r696_checkpoint_readonly_live_v2",
        "round": round_id, "source_round": "R696",
        "started_at": now(), "status": "preflight", "red": None,
        "policy": {"read_only": True, "assign_commands": 0,
                   "native_helper_invocations_expected": 0,
                   "date_advance": False, "checkpoint_save_commands": 0,
                   "readiness_timeout_seconds": 300,
                   "query_timeout_seconds": 60,
                   "overall_window_seconds": 480},
        "typed_receipt_across_process": "unavailable_process_local_pending_ack",
        "formal_high_level_goal_restore": "unverified_private_action_not_in_driver_state",
        "preflight": preflight,
    }
    state_dir = root / "fresh-profile-state"
    source_checkpoint = root / "source-checkpoint" / "xar_checkpoint.ck3"
    target_checkpoint = state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
    locks = HeldLaunchLocks()
    handle = None
    driver = None
    started = time.monotonic()
    deadline = started + 480
    try:
        spec = make_spec(state_dir, Path(str(operator["game_dir"])))
        inventory = ck3_process_inventory()
        require(not inventory.get("processes"), "CK3 inventory nonzero before owner launch")
        write_json(evidence / "preflight.json", {**preflight,
                                                 "ck3_inventory": inventory,
                                                 "owner_allocated_round": round_id})
        with locks:
            locks.enter_context(exclusive_launch_lock(spec.game_exe))
            locks.enter_context(exclusive_state_lock(state_dir,
                                                     f"council-{round_id.lower()}-readonly"))
            driver = NativeHeadlessGameplayDriver(
                str(operator["pipe"]), state_dir=state_dir,
                save_dir=state_dir / "profile" / "save games")
            handle = launch(
                spec, native_bridge=NativeBridgeLaunchConfig(
                    mode="native-headless", pipe_name=str(operator["pipe"]),
                    dll_path=root / "candidate-bin" / "xar_ck3_bridge.dll",
                    injector_path=root / "candidate-bin" / "xar_ck3_bridge_injector.exe"),
                continue_last_save=False, load_save_name="xar_checkpoint",
                verify_prepared_profile=False)
            report["process"] = {
                "pid": handle.process.pid, "creation_date": handle.ck3_creation_date,
                "watchdog_pid": handle.watchdog_pid,
                "watchdog_creation_date": handle.watchdog_creation_date,
                "command": handle.command, "launched_at": now(),
                "owner_allocated_round": round_id}
            write_json(evidence / "round-ownership.json", report["process"])
            remaining = deadline - time.monotonic()
            require(remaining > 30, "overall window consumed before readiness")
            binding = _wait_for_readiness(
                driver, session_done=threading.Event(), session_state={},
                timeout_seconds=min(300, remaining - 20), stable_seconds=1.0,
                poll_interval_seconds=0.1, cold_start_checkpoint=False,
                allow_terminal=False)
            initial = driver.take_internal_semantic_snapshot()
            require(initial.get("paused") is True and
                    initial.get("episode_character_id") == 29829 and
                    initial.get("date_raw") == 53178264 and
                    type(initial.get("native_revision")) is int,
                    f"restored paused owner/date differs: {initial!r}")
            advertised = driver.capabilities().get("capabilities")
            require(not isinstance(advertised, list) or all(value not in {
                "game.query.council-composition-candidates-v1",
                "game.action.assign-councillor-v1"} for value in advertised),
                "read-only private Council leaked into public hello")
            revision = initial["native_revision"]
            query_deadline = min(time.monotonic() + 60, deadline - 20)
            first = command(driver, QUERY, f"{round_id.lower()}-restored-gate", revision,
                            min(5, query_deadline - time.monotonic()))
            write_json(evidence / "raw-query-queue-result.json", first)
            require(first.get("ok") is True and isinstance(first.get("result"), dict) and
                    first["result"].get("status") == "pending",
                    f"read-only query queue RED: {first!r}")
            attempts: list[dict[str, object]] = []
            terminal = None
            while time.monotonic() < query_deadline:
                require(handle.process.poll() is None, "CK3 exited before Council read")
                current = driver.take_internal_semantic_snapshot()
                require(current.get("paused") is True and current.get("date_raw") == 53178264,
                        "paused/date changed during cold-restore query")
                status = command(driver, STATUS,
                                 f"{round_id.lower()}-restore-status-{len(attempts)+1}",
                                 revision, min(2, max(0.1, query_deadline-time.monotonic())))
                attempts.append(status)
                write_json(evidence / "raw-status-results.json", attempts)
                require(status.get("ok") is True, f"read-only status RED: {status!r}")
                payload = status.get("result")
                if isinstance(payload, dict) and payload.get("schema") == ENVELOPE_SCHEMA:
                    terminal = status
                    break
                time.sleep(0.1)
            require(terminal is not None, "restored Council query did not publish within 60s")
            write_json(evidence / "raw-terminal-result.json", terminal)
            payload = terminal["result"]
            gates = payload.get("council_final_gates")
            require(payload.get("step") == QUERY and payload.get("status") == "available" and
                    payload.get("private") is True and
                    payload.get("advertised") is False and
                    payload.get("native_helper_invocations_delta") == 0 and
                    isinstance(gates, dict) and gates.get("schema") == GATE_SCHEMA and
                    gates.get("status") == "available",
                    f"restored gate-only envelope differs: {payload!r}")
            public = gates.get("council_composition_candidates")
            require(isinstance(public, dict) and public.get("schema") == PUBLIC_SCHEMA and
                    public.get("status") == "available" and
                    public.get("owner_character_id") == 29829 and
                    isinstance(public.get("snapshot"), dict) and
                    public["snapshot"].get("paused") is True and
                    public["snapshot"].get("date_raw") == 53178264,
                    f"restored public Council observation differs: {public!r}")
            position = public.get("position")
            require(isinstance(position, dict) and
                    position.get("position_key") == "councillor_steward" and
                    position.get("incumbent_character_id") == 33433 and
                    position.get("incumbent_main_skill") == {
                        "key": "stewardship", "value": 16},
                    f"R696 checkpoint did not restore material incumbent33433: {position!r}")
            final = driver.take_internal_semantic_snapshot()
            require(final.get("paused") is True and final.get("date_raw") == 53178264,
                    "paused/date changed after restored Council read")
            report["capture"] = {"binding": binding, "initial_snapshot": initial,
                                 "public_council": public,
                                 "final_snapshot": final,
                                 "native_helper_invocations_delta": 0,
                                 "assign_commands": 0,
                                 "checkpoint_sha256": CHECKPOINT_SHA}
            report["status"] = "green_pending_cleanup"
    except BaseException as error:
        report["status"] = "red_pending_cleanup"
        report["red"] = {"at": now(),
                         "reason": f"{type(error).__name__}: {error}",
                         "traceback": traceback.format_exc(),
                         "assign_retry_allowed": False}
    finally:
        if handle is not None:
            try:
                report["cleanup"] = stop_tracked(handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {"ok": False,
                                     "reason": f"{type(error).__name__}: {error}"}
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_red"] = f"{type(error).__name__}: {error}"
        try:
            locks.close()
        except BaseException as error:
            report["lock_cleanup_red"] = f"{type(error).__name__}: {error}"
        try:
            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_checkpoint_sha256": sha256(source_checkpoint),
                "target_checkpoint_sha256": sha256(target_checkpoint),
                "wall_seconds": time.monotonic() - started}
        except BaseException as error:
            report["postflight_red"] = f"{type(error).__name__}: {error}"
        cleanup = report.get("cleanup")
        post = report.get("postflight")
        ok = (report["status"] == "green_pending_cleanup" and
              isinstance(cleanup, dict) and cleanup.get("ok") is True and
              isinstance(post, dict) and not post["ck3_inventory"].get("processes") and
              post["source_checkpoint_sha256"] == CHECKPOINT_SHA and
              post["target_checkpoint_sha256"] == CHECKPOINT_SHA and
              post["wall_seconds"] <= 480 and
              not report.get("driver_close_red") and
              not report.get("lock_cleanup_red"))
        report["ok"] = ok
        report["status"] = "green" if ok else "red"
        report["finished_at"] = now()
        write_json(evidence / "report.json", report)
    print(json.dumps({"status": report["status"], "ok": report["ok"],
                      "red": report["red"]}, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
