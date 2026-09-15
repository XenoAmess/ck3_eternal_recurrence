"""Seal one Council R694 read-only private-query candidate without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_SAVE_SHA256 = (
    "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"
)
SOURCE_COMMIT = "76a3da267102e7184ab9af29832af7f6e945e685"
RUNTIME_ROOTS = (
    "ck3_autonomous_player/agent.py",
    "ck3_autonomous_player/pyproject.toml",
    "ck3_autonomous_player/src",
    "ck3_autonomous_player/configs",
    "ck3_autonomous_player/schemas",
    "ck3_autonomous_player/strategies",
    "ck3_autonomous_player/knowledge",
    "tools/build_release.py",
)
BINARIES = (
    "xar_ck3_bridge.dll",
    "xar_ck3_bridge_injector.exe",
    "xar_ck3_bridge_host.exe",
    "xar_ck3_bridge_target.exe",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def copy_file(source: Path, target: Path) -> None:
    if not source.is_file():
        raise RuntimeError(f"source file is absent: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def prepare(
    repo: Path,
    old_candidate: Path,
    build: Path,
    game: Path,
    output: Path,
    python: Path,
) -> dict[str, object]:
    repo = repo.resolve()
    old_candidate = old_candidate.resolve()
    build = build.resolve()
    game = game.resolve()
    output = output.resolve()
    python = python.resolve()
    if output.exists():
        raise RuntimeError(f"candidate output already exists: {output}")
    if (git(repo, "rev-parse", "origin/master") != SOURCE_COMMIT
            or git(repo, "merge-base", "HEAD", "origin/master") != SOURCE_COMMIT):
        raise RuntimeError("R694 runtime base is not the frozen master commit")
    if git(repo, "diff", "--name-only", "origin/master", "--", *RUNTIME_ROOTS):
        raise RuntimeError("R694 runtime differs from frozen master")
    exe = game / "binaries" / "ck3.exe"
    if not exe.is_file() or sha256(exe) != EXPECTED_EXE_SHA256:
        raise RuntimeError("exact CK3 executable is absent or differs")
    if not python.is_file():
        raise RuntimeError("operator Python is absent")
    source_save = old_candidate / "source-save" / "dev3b_r639.ck3"
    if sha256(source_save) != EXPECTED_SAVE_SHA256:
        raise RuntimeError("R693 source save differs from the frozen scene")

    output.mkdir(parents=True)
    for binary in BINARIES:
        copy_file(build / binary, output / "candidate-bin" / binary)
    copy_file(source_save, output / "source-save" / "dev3b_r639.ck3")

    # R693's frozen profile supplies the same mod/DLC/game-rule combination.
    # Copy only its sealed prelaunch files, never historical logs, driver state,
    # live evidence or cache. The new candidate gets its own writable -userdir.
    prior_manifest = json.loads(
        (old_candidate / "sealed-prep-manifest.json").read_text(encoding="utf-8")
    )
    profile_rows = [
        str(row["path"])
        for row in prior_manifest["files"]
        if str(row["path"]).startswith("fresh-profile-state/profile/")
        and not str(row["path"]).endswith("/xar-autoplayer-environment.json")
    ]
    for relative in profile_rows:
        copy_file(old_candidate / relative, output / relative)
    target_save = (
        output / "fresh-profile-state" / "profile" / "save games" / "dev3b_r639.ck3"
    )
    if sha256(target_save) != EXPECTED_SAVE_SHA256:
        raise RuntimeError("R694 target save differs before launch")
    descriptor = output / "fresh-profile-state" / "profile" / "mod" / "xar_autoplayer.mod"
    text = descriptor.read_text(encoding="utf-8-sig")
    old_path = (
        old_candidate / "fresh-profile-state" / "profile" / "mod-content" / "xar-production"
    ).as_posix()
    new_path = (
        output / "fresh-profile-state" / "profile" / "mod-content" / "xar-production"
    ).as_posix()
    if f'path="{old_path}"' not in text:
        raise RuntimeError("prior outer mod descriptor has an unknown path")
    descriptor.write_text(text.replace(old_path, new_path), encoding="utf-8")

    tracked = git(repo, "ls-files", "--", *RUNTIME_ROOTS).splitlines()
    if not tracked:
        raise RuntimeError("frozen Python runtime has no tracked files")
    for relative in tracked:
        copy_file(repo / relative, output / "source-repo" / relative)

    runner = repo / "ck3_autonomous_player" / "native_bridge" / "research"
    for name in ("run_council_r694_query.py", "verify_council_r694_query_prep.py"):
        copy_file(runner / name, output / name)
    operator = {
        "schema": "xar.ck3.g2_m4_council_r694_query_operator_v1",
        "python": str(python),
        "game_dir": str(game),
        "pipe": r"\\.\pipe\xar_ck3_bridge_g2_m4_council_r694_query_76a3da26",
        "old_round": "R693",
        "new_round": "R694",
        "readiness_timeout_seconds": 300,
        "query_timeout_seconds": 60,
        "overall_window_seconds": 480,
    }
    write_json(output / "operator-runtime.json", operator)

    rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name not in {
            "sealed-prep-manifest.json",
            "sealed-prep-manifest.sha256",
        }:
            rows.append(
                {
                    "path": path.relative_to(output).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    manifest: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_council_r694_query_sealed_prep_v1",
        "status": "sealed-no-launch",
        "source_commit": SOURCE_COMMIT,
        "game_version": "1.19.0.6",
        "game_exe_sha256": EXPECTED_EXE_SHA256,
        "source_save_sha256": EXPECTED_SAVE_SHA256,
        "bridge_dll_sha256": sha256(output / "candidate-bin" / "xar_ck3_bridge.dll"),
        "prior_profile_prep_sha256": sha256(old_candidate / "sealed-prep-manifest.json"),
        "profile_lineage": "R693 frozen prelaunch DLC/mod/settings; own descriptor path; stale environment fingerprint omitted",
        "python_exe_sha256": sha256(python),
        "cmake_private_option":
            "XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1=ON",
        "public_query_registered": False,
        "public_action_registered": False,
        "gameplay_actions": 0,
        "file_count": len(rows),
        "files": rows,
    }
    path = output / "sealed-prep-manifest.json"
    write_json(path, manifest)
    (output / "sealed-prep-manifest.sha256").write_text(
        sha256(path) + "  sealed-prep-manifest.json\n", encoding="ascii"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--r693-candidate", type=Path, required=True)
    parser.add_argument("--build-release", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(
        args.repo, args.r693_candidate, args.build_release,
        args.game_dir, args.output, args.python,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "source_commit": manifest["source_commit"],
                "file_count": manifest["file_count"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
