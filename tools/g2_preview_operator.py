"""Python-only operator wrapper for the frozen G2 preview package.

This keeps the documented Windows workflow in one reviewable Python entry
point: immutable ZIP verification, new-state preparation, exact preflight,
bounded production execution, stop requests, and report inspection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def manifest_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"manifest field {field!r} must be a nonempty path")
    return Path(value).resolve()


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = read_json(path)
    for field in ("python", "source_repo", "state_dir", "game_dir", "pipe", "dll", "injector"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            raise ValueError(f"manifest field {field!r} is required")
    return manifest


def agent_command(manifest: dict[str, Any]) -> list[str]:
    source_repo = manifest_path(manifest["source_repo"], "source_repo")
    entry = source_repo / "ck3_autonomous_player" / "agent.py"
    return [
        str(manifest_path(manifest["python"], "python")),
        "-B",
        str(entry),
        "--state-dir",
        str(manifest_path(manifest["state_dir"], "state_dir")),
        "--game-dir",
        str(manifest_path(manifest["game_dir"], "game_dir")),
        "--bridge-mode",
        "native-headless",
        "--bridge-pipe",
        str(manifest["pipe"]),
        "--bridge-dll",
        str(manifest_path(manifest["dll"], "dll")),
        "--bridge-injector",
        str(manifest_path(manifest["injector"], "injector")),
    ]


def current_checkpoint_identity(manifest: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    state_dir = manifest_path(manifest["state_dir"], "state_dir")
    save = state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
    driver_path = state_dir / "native-session" / "driver-state.json"
    if not save.is_file() or not driver_path.is_file():
        raise FileNotFoundError("paired checkpoint save or driver state is missing")
    driver = read_json(driver_path)
    return save, driver_path, driver


def episode_value(driver: dict[str, Any], manifest: dict[str, Any], key: str) -> Any:
    value = driver.get(key, manifest.get(key))
    if value is None or value == "":
        raise ValueError(f"paired checkpoint does not provide {key!r}")
    return value


def run_logged(command: list[str], stdout_path: Path, stderr_path: Path) -> int:
    with stdout_path.open("w", encoding="utf-8", newline="") as stdout_stream:
        with stderr_path.open("w", encoding="utf-8", newline="") as stderr_stream:
            completed = subprocess.run(command, stdout=stdout_stream, stderr=stderr_stream, check=False)
    return completed.returncode


def command_verify_zip(args: argparse.Namespace) -> int:
    archive = args.zip.resolve()
    actual = sha256(archive)
    expected = args.expected_sha256.casefold()
    if actual != expected:
        raise ValueError(f"preview ZIP hash mismatch: expected {expected}, got {actual}")
    print(json.dumps({"ok": True, "zip": str(archive), "bytes": archive.stat().st_size, "sha256": actual}))
    return 0


def command_prepare_state(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest.resolve())
    state_dir = manifest_path(manifest["state_dir"], "state_dir")
    sample_dir = args.sample_dir.resolve()
    save_source = sample_dir / "xar_checkpoint.ck3"
    driver_source = sample_dir / "driver-state.json"
    save_target = state_dir / "profile" / "save games" / "xar_checkpoint.ck3"
    driver_target = state_dir / "native-session" / "driver-state.json"
    for path in (save_source, driver_source):
        if not path.is_file():
            raise FileNotFoundError(path)
    for path in (save_target, driver_target):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite prepared state: {path}")
    common = agent_command(manifest)
    if subprocess.run([*common, "prepare-profile"], check=False).returncode != 0:
        raise RuntimeError("production profile preparation failed")
    save_target.parent.mkdir(parents=True, exist_ok=True)
    driver_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(save_source, save_target)
    shutil.copy2(driver_source, driver_target)
    if subprocess.run([*common, "verify-profile"], check=False).returncode != 0:
        raise RuntimeError("production profile verification failed")
    print(json.dumps({
        "ok": True,
        "state_dir": str(state_dir),
        "checkpoint_sha256": sha256(save_target),
        "driver_state_sha256": sha256(driver_target),
    }))
    return 0


def command_run(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest.resolve())
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"attempt output already exists: {output}")
    output.mkdir(parents=True)
    save, driver_path, driver = current_checkpoint_identity(manifest)
    character_id = episode_value(driver, manifest, "episode_character_id")
    episode_run_id = episode_value(driver, manifest, "episode_run_id")
    common = agent_command(manifest)
    preflight = [
        *common,
        "native-one-generation-preflight",
        "--expected-character-id",
        str(character_id),
        "--expected-episode-run-id",
        str(episode_run_id),
        "--expected-checkpoint-sha256",
        sha256(save),
        "--expected-driver-state-sha256",
        sha256(driver_path),
    ]
    preflight_exit = run_logged(
        preflight,
        output / "preflight-stdout.txt",
        output / "preflight-stderr.txt",
    )
    receipt: dict[str, Any] = {
        "schema": "xar-g2-preview-python-operator-v1",
        "manifest": str(args.manifest.resolve()),
        "output": str(output),
        "checkpoint_sha256_before": sha256(save),
        "driver_state_sha256_before": sha256(driver_path),
        "preflight_exit_code": preflight_exit,
    }
    if preflight_exit != 0:
        receipt.update({"ok": False, "status": "preflight_blocked", "game_launched": False})
        (output / "operator-receipt.json").write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return preflight_exit
    turns = args.turns if args.turns is not None else int(manifest.get("formal_turns", 20))
    timeout = args.timeout if args.timeout is not None else int(manifest.get("timeout_seconds", 390))
    readiness_timeout = args.readiness_timeout if args.readiness_timeout is not None else int(
        manifest.get("readiness_timeout_seconds", 300)
    )
    formal_report = output / "formal-report.txt"
    formal_stderr = output / "formal-stderr.txt"
    stop_path = manifest_path(manifest["state_dir"], "state_dir") / "native-auto-run.stop"
    print(f"Operator stop request file: {stop_path}", file=sys.stderr, flush=True)
    formal_exit = run_logged(
        [
            *common,
            "native-auto-run",
            "--turns",
            str(turns),
            "--timeout",
            str(timeout),
            "--readiness-timeout",
            str(readiness_timeout),
            "--cold-start-checkpoint",
        ],
        formal_report,
        formal_stderr,
    )
    receipt.update({
        "ok": formal_exit == 0,
        "status": "completed" if formal_exit == 0 else "formal_run_failed",
        "game_launched": True,
        "formal_exit_code": formal_exit,
        "formal_report": str(formal_report),
        "formal_stderr": str(formal_stderr),
        "turns": turns,
        "timeout_seconds": timeout,
        "readiness_timeout_seconds": readiness_timeout,
        "checkpoint_sha256_after": sha256(save) if save.is_file() else None,
        "driver_state_sha256_after": sha256(driver_path) if driver_path.is_file() else None,
    })
    (output / "operator-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False))
    return formal_exit


def command_request_stop(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest.resolve())
    stop_path = manifest_path(manifest["state_dir"], "state_dir") / "native-auto-run.stop"
    if stop_path.exists():
        raise FileExistsError(f"stale or active stop request already exists: {stop_path}")
    stop_path.write_text("stop\n", encoding="utf-8")
    print(json.dumps({"ok": True, "stop_request": str(stop_path)}))
    return 0


def tasklist_ck3() -> list[dict[str, str]]:
    if sys.platform != "win32":
        return []
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq ck3.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
    )
    rows = []
    for row in csv.reader(completed.stdout.splitlines()):
        if row and row[0].casefold() == "ck3.exe":
            rows.append({"image": row[0], "pid": row[1], "memory": row[4] if len(row) > 4 else ""})
    return rows


def command_status(args: argparse.Namespace) -> int:
    report_path = args.report.resolve()
    report: Any = None
    if report_path.is_file():
        text = report_path.read_text(encoding="utf-8-sig")
        try:
            report = json.loads(text)
        except json.JSONDecodeError:
            report = {"unparsed_report": str(report_path), "bytes": report_path.stat().st_size}
    summary = {"report": report, "ck3_processes": tasklist_ck3()}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    verify_zip = commands.add_parser("verify-zip")
    verify_zip.add_argument("--zip", type=Path, required=True)
    verify_zip.add_argument("--expected-sha256", required=True)
    verify_zip.set_defaults(handler=command_verify_zip)

    prepare = commands.add_parser("prepare-state")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument("--sample-dir", type=Path, required=True)
    prepare.set_defaults(handler=command_prepare_state)

    run = commands.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--turns", type=int)
    run.add_argument("--timeout", type=int)
    run.add_argument("--readiness-timeout", type=int)
    run.set_defaults(handler=command_run)

    request_stop = commands.add_parser("request-stop")
    request_stop.add_argument("--manifest", type=Path, required=True)
    request_stop.set_defaults(handler=command_request_stop)

    status = commands.add_parser("status")
    status.add_argument("--report", type=Path, required=True)
    status.set_defaults(handler=command_status)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.handler(args))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
