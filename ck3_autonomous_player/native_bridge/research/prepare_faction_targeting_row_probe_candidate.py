"""Create a sealed, no-launch R692 faction-row probe candidate.

The candidate embeds a Git-archived source tree, frozen save, private bridge
binaries, a generated Python launcher, and hashes for every live input.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_bounded_private_probe_wrapper import (
    render_wrapper,
    validate_named_pipe,
)


EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_GAME_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_OLD_ROUND = "R691"
EXPECTED_NEW_ROUND = "R692"
EXPECTED_OPTION = "XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_ASYNC_PRIVATE_PROBE_V1=ON"
EXPECTED_BINARIES = (
    "xar_ck3_bridge.dll",
    "xar_ck3_bridge_injector.exe",
    "xar_ck3_bridge_host.exe",
    "xar_ck3_bridge_target.exe",
    "xar_ck3_faction_targeting_row_probe_v1_test.exe",
)
WRAPPER_ARGUMENTS = (
    "--artifact-dir",
    "--state-dir",
    "--game-dir",
    "--source-save",
    "--save-name",
    "--expected-save-sha256",
    "--candidate-manifest",
    "--expected-candidate-manifest-sha256",
    "--bridge-dll",
    "--expected-bridge-dll-sha256",
    "--bridge-injector",
    "--expected-bridge-injector-sha256",
    "--expected-game-exe-sha256",
    "--expected-character-id",
    "--pipe",
    "--old-round",
    "--new-round",
    "--candidate-revision",
    "--publish-timeout",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def entry(root: Path, path: Path) -> dict[str, object]:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise RuntimeError(f"candidate entry is absent or escapes root: {path}")
    return {
        "relative_path": resolved.relative_to(root.resolve()).as_posix(),
        "size": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip())
    return completed.stdout.strip()


def _archive_head(repo: Path, destination: Path) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", "HEAD"],
        check=False,
        capture_output=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode(errors="replace").strip())
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
        archive.extractall(destination, filter="data")


def parser_option_names(runner: Path) -> set[str]:
    tree = ast.parse(runner.read_text(encoding="utf-8"), filename=str(runner))
    options: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            if first.value.startswith("--"):
                options.add(first.value)
    return options


def verify_parameter_contract(runner: Path) -> dict[str, object]:
    parser_options = parser_option_names(runner)
    missing = sorted(set(WRAPPER_ARGUMENTS) - parser_options)
    if missing:
        raise RuntimeError(f"generated wrapper arguments missing from runner: {missing}")
    return {
        "status": "green",
        "wrapper_argument_count": len(WRAPPER_ARGUMENTS),
        "wrapper_arguments": list(WRAPPER_ARGUMENTS),
        "runner_parser_option_count": len(parser_options),
        "missing_runner_options": missing,
    }


def process_inventory() -> dict[str, object]:
    completed = subprocess.run(
        ["tasklist.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    watched = {
        "ck3.exe",
        "xar_ck3_bridge_host.exe",
        "xar_ck3_bridge_injector.exe",
        "xar_ck3_bridge_target.exe",
    }
    rows: list[dict[str, object]] = []
    if completed.returncode == 0:
        for fields in csv.reader(completed.stdout.splitlines()):
            if len(fields) < 2 or fields[0].lower() not in watched:
                continue
            try:
                process_id: object = int(fields[1])
            except ValueError:
                process_id = fields[1]
            rows.append({"name": fields[0], "pid": process_id})
    return {
        "observed_at_utc": _now(),
        "command_status": "green" if completed.returncode == 0 else "red",
        "processes": rows,
    }


def _find_binary(directory: Path, name: str) -> Path:
    direct = directory / name
    release = directory / "Release" / name
    matches = [path for path in (direct, release) if path.is_file()]
    if len(matches) != 1:
        raise RuntimeError(f"expected one candidate binary {name}: {matches}")
    return matches[0]


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_checksum(data: Path, output: Path) -> None:
    output.write_text(
        f"{sha256(data)}  {data.name}\n", encoding="ascii", newline="\n"
    )


def build_candidate(args: argparse.Namespace) -> dict[str, Any]:
    repo = args.repo_root.resolve()
    candidate = args.candidate_root.resolve()
    source_save = args.source_save.resolve()
    binary_dir = args.binary_dir.resolve()
    game_exe = args.game_dir.resolve() / "binaries" / "ck3.exe"
    if candidate.exists():
        raise RuntimeError(f"candidate root already exists: {candidate}")
    if not source_save.is_file() or not game_exe.is_file():
        raise RuntimeError("source save or exact-build game executable is missing")
    if sha256(game_exe) != EXPECTED_GAME_EXE_SHA256:
        raise RuntimeError("game executable is not exact CK3 1.19.0.6")
    status = _git(repo, "status", "--porcelain")
    if status:
        raise RuntimeError("candidate source repository must be clean")
    commit = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    branch = _git(repo, "branch", "--show-current")
    if len(commit) != 40 or not branch:
        raise RuntimeError("candidate requires a named branch at one full commit")
    remote_tip = _git(repo, "ls-remote", "--heads", "origin", branch).split()
    pushed = bool(remote_tip and remote_tip[0] == commit)
    if not pushed:
        raise RuntimeError("candidate commit must already be pushed to its work branch")
    if args.old_round != EXPECTED_OLD_ROUND or args.new_round != EXPECTED_NEW_ROUND:
        raise RuntimeError("candidate generator is frozen to R691 -> R692")
    unique_pipe = args.unique_pipe or (
        rf"\\.\pipe\xar_ck3_bridge_g2_m4_r692_faction_{commit[:7]}"
    )
    validate_named_pipe(unique_pipe)

    inventory_before = process_inventory()
    candidate.mkdir(parents=True)
    source_repo = candidate / "source-repo"
    _archive_head(repo, source_repo)
    save_dir = candidate / "source-save"
    save_dir.mkdir()
    save_path = save_dir / source_save.name
    shutil.copy2(source_save, save_path)
    bin_dir = candidate / "bin"
    bin_dir.mkdir()
    binaries: dict[str, dict[str, object]] = {}
    for name in EXPECTED_BINARIES:
        target = bin_dir / name
        shutil.copy2(_find_binary(binary_dir, name), target)
        binaries[name] = entry(candidate, target)

    runner = (
        source_repo
        / "ck3_autonomous_player"
        / "native_bridge"
        / "research"
        / "run_faction_targeting_row_private_probe_live.py"
    )
    bootstrap = source_repo / "tools" / "run_g2_faction_targeting_row_probe.py"
    parameter_contract = verify_parameter_contract(runner)
    if not bootstrap.is_file():
        raise RuntimeError("candidate bootstrap is missing from archived commit")

    manifest_path = candidate / "candidate-manifest.json"
    wrapper_path = candidate / "run-r692.py"
    manifest: dict[str, Any] = {
        "format_version": 1,
        "kind": "g2_m4_faction9_r692_paused_row_probe_candidate_v1",
        "status": "static-ready-no-launch",
        "created_at_utc": _now(),
        "source": {
            "branch": branch,
            "commit": commit,
            "tree": tree,
            "remote_branch": f"origin/{branch}",
            "pushed": True,
            "source_repo_relative_path": "source-repo",
        },
        "exact_build": {
            "game_version": EXPECTED_GAME_VERSION,
            "executable_sha256": EXPECTED_GAME_EXE_SHA256,
        },
        "build": {
            "configuration": "Release",
            "option": EXPECTED_OPTION,
            "source_commit": commit,
        },
        "artifacts": binaries,
        "runtime_assets": {
            "bootstrap": entry(candidate, bootstrap),
            "private_runner": entry(candidate, runner),
            "source_save": entry(candidate, save_path),
            "expected_character_id": args.expected_character_id,
        },
        "parameter_contract": parameter_contract,
        "next_live": {
            "suggested_round": args.new_round,
            "old_round": args.old_round,
            "new_round": args.new_round,
            "unique_pipe": unique_pipe,
            "publish_timeout_seconds": args.publish_timeout,
            "paused_only": True,
            "gameplay_actions": 0,
            "date_advance": False,
            "save_mutation": False,
            "retry": False,
            "operator_ui_requirement": (
                "after paused admission, open or refresh the Factions view once "
                "so the exact targeting-row callback fires"
            ),
            "acceptance": [
                "private async heartbeat reaches terminal",
                "async_failure_flags=0",
                "terminal is ready or known-empty; typed unavailable remains RED",
                "required and observed four-key bindings match the paused frame",
                "raw private heartbeat is persisted before semantic validation",
            ],
        },
        "public_surface": {
            "native_capability_registered": False,
            "mcp_schema_changed": False,
            "planner_changed": False,
            "open_kaishek_change_required": False,
        },
        "honest_boundary": {
            "ck3_live_validated": False,
            "production_live": False,
            "candidate_generator_launched_ck3": False,
            "next": "one R692 exact-build paused private heartbeat; no same-round retry",
        },
    }
    _write_json(manifest_path, manifest)
    wrapper_path.write_text(
        render_wrapper(
            manifest_relative=manifest_path.name,
            bootstrap_relative="source-repo/tools/run_g2_faction_targeting_row_probe.py",
            save_relative=f"source-save/{save_path.name}",
            dll_relative="bin/xar_ck3_bridge.dll",
            injector_relative="bin/xar_ck3_bridge_injector.exe",
            save_name=save_path.name,
            expected_save_sha256=sha256(save_path),
            expected_dll_sha256=sha256(bin_dir / "xar_ck3_bridge.dll"),
            expected_injector_sha256=sha256(
                bin_dir / "xar_ck3_bridge_injector.exe"
            ),
            expected_game_exe_sha256=EXPECTED_GAME_EXE_SHA256,
            expected_character_id=args.expected_character_id,
            old_round=args.old_round,
            new_round=args.new_round,
            candidate_revision=commit,
            publish_timeout=args.publish_timeout,
        ),
        encoding="utf-8-sig",
        newline="\n",
    )
    manifest["runtime_assets"]["wrapper"] = entry(candidate, wrapper_path)
    manifest["wrapper_contract"] = {
        "manifest_pipe_authoritative": True,
        "ordinal_argument_equality_required": True,
        "canonical_prefix": "\\\\.\\pipe\\",
        "generated_wrapper": wrapper_path.name,
        "dry_run_required": True,
        "python_runtime_argument_required": True,
    }
    _write_json(manifest_path, manifest)
    _write_checksum(manifest_path, candidate / "candidate-manifest.sha256")

    dry_run = subprocess.run(
        [
            sys.executable,
            str(wrapper_path),
            "--python",
            sys.executable,
            "--game-dir",
            str(args.game_dir.resolve()),
            "--artifact-dir",
            str(candidate / "never-created-live-artifact"),
            "--state-dir",
            str(candidate / "never-created-live-state"),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if dry_run.returncode != 0:
        raise RuntimeError(f"wrapper dry run failed: {dry_run.stderr}")
    dry_payload = json.loads(dry_run.stdout)
    if (
        dry_payload.get("status") != "green"
        or dry_payload.get("ck3_launched") is not False
        or dry_payload.get("manifest_pipe") != unique_pipe
        or dry_payload.get("argument_pipe") != unique_pipe
    ):
        raise RuntimeError("wrapper dry-run parameter contract failed")
    _write_json(candidate / "no-launch-dry-run.json", dry_payload)
    inventory_after = process_inventory()
    _write_json(
        candidate / "no-launch-process-inventory.json",
        {
            "before": inventory_before,
            "after": inventory_after,
            "candidate_generator_launched_ck3": False,
            "candidate_generator_attached_ck3": False,
        },
    )
    seal_files = [
        manifest_path,
        candidate / "candidate-manifest.sha256",
        wrapper_path,
        candidate / "no-launch-dry-run.json",
        candidate / "no-launch-process-inventory.json",
        bootstrap,
        runner,
        save_path,
        *[bin_dir / name for name in EXPECTED_BINARIES],
    ]
    seal = {
        "schema": "xar.ck3.g2_m4_faction9_r692_candidate_seal_v1",
        "status": "GREEN_NO_LAUNCH",
        "sealed_at_utc": _now(),
        "candidate_root": str(candidate),
        "commit": commit,
        "files": [entry(candidate, path) for path in seal_files],
        "checks": {
            "candidate_commit_pushed": True,
            "parameter_contract": "GREEN",
            "dry_run": "GREEN",
            "manifest_pipe_equals_argument": True,
            "ck3_launched": False,
            "ck3_attached": False,
        },
    }
    seal_path = candidate / "candidate-seal.json"
    _write_json(seal_path, seal)
    _write_checksum(seal_path, candidate / "candidate-seal.sha256")
    return {
        "candidate_root": str(candidate),
        "commit": commit,
        "candidate_manifest_sha256": sha256(manifest_path),
        "candidate_seal_sha256": sha256(seal_path),
        "unique_pipe": unique_pipe,
        "status": "GREEN_NO_LAUNCH",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--source-save", type=Path, required=True)
    parser.add_argument("--binary-dir", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--old-round", default=EXPECTED_OLD_ROUND)
    parser.add_argument("--new-round", default=EXPECTED_NEW_ROUND)
    parser.add_argument("--unique-pipe")
    parser.add_argument("--publish-timeout", type=int, default=90)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.expected_character_id <= 0 or args.publish_timeout <= 0:
        raise SystemExit("character id and publish timeout must be positive")
    result = build_candidate(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
