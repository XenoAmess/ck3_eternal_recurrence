"""Seal a Council controlled-replacement candidate without launching CK3."""

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
PRIVATE_OPTIONS = {
    "XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1": "ON",
    "XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1": "ON",
    "XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1": "ON",
}
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
    prior_candidate: Path,
    build: Path,
    game: Path,
    output: Path,
    python: Path,
    source_commit: str,
) -> dict[str, object]:
    repo = repo.resolve()
    prior_candidate = prior_candidate.resolve()
    build = build.resolve()
    game = game.resolve()
    output = output.resolve()
    python = python.resolve()
    if output.exists():
        raise RuntimeError(f"candidate output already exists: {output}")
    if len(source_commit) != 40 or any(character not in "0123456789abcdef" for character in source_commit):
        raise RuntimeError("source commit must be one exact 40-character Git ID")
    head = git(repo, "rev-parse", "HEAD")
    if git(repo, "merge-base", head, source_commit) != source_commit:
        raise RuntimeError("runner branch does not descend from frozen G2 code")
    if git(repo, "diff", "--name-only", source_commit, "HEAD", "--", *RUNTIME_ROOTS,
           "ck3_autonomous_player/native_bridge/src",
           "ck3_autonomous_player/native_bridge/include",
           "ck3_autonomous_player/native_bridge/CMakeLists.txt"):
        raise RuntimeError("R696 build/Python source differs from frozen G2 code")
    cache_path = build.parent / "CMakeCache.txt"
    if not cache_path.is_file():
        raise RuntimeError("Release DLL has no CMake configuration cache")
    cache = cache_path.read_text(encoding="utf-8", errors="replace")
    for key, value in PRIVATE_OPTIONS.items():
        if f"{key}:BOOL={value}" not in cache:
            raise RuntimeError(f"controlled CMake option differs: {key}")
    if f"CMAKE_HOME_DIRECTORY:INTERNAL={str(repo / 'ck3_autonomous_player' / 'native_bridge').replace(chr(92), '/')}".lower() not in cache.lower():
        raise RuntimeError("DLL CMake source checkout differs from frozen repo")
    exe = game / "binaries" / "ck3.exe"
    if not exe.is_file() or sha256(exe) != EXPECTED_EXE_SHA256:
        raise RuntimeError("exact CK3 executable is absent or differs")
    if not python.is_file():
        raise RuntimeError("operator Python is absent")
    source_save = prior_candidate / "source-save" / "dev3b_r639.ck3"
    if sha256(source_save) != EXPECTED_SAVE_SHA256:
        raise RuntimeError("R695 source save differs from the frozen scene")

    output.mkdir(parents=True)
    for binary in BINARIES:
        copy_file(build / binary, output / "candidate-bin" / binary)
    copy_file(cache_path, output / "candidate-bin" / "CMakeCache.txt")
    copy_file(source_save, output / "source-save" / "dev3b_r639.ck3")

    # R695's sealed prelaunch profile supplies the same mod/DLC/game-rule combination.
    # Copy only its sealed prelaunch files, never historical logs, driver state,
    # live evidence or cache. The new candidate gets its own writable -userdir.
    prior_manifest = json.loads((prior_candidate / "sealed-prep-manifest.json").read_text(encoding="utf-8"))
    if prior_manifest.get("schema") != "xar.ck3.g2_m4_council_r695_gate_sealed_prep_v1":
        raise RuntimeError("prior R695 sealed profile identity differs")
    profile_rows = [row for row in prior_manifest["files"]
                    if str(row["path"]).startswith("fresh-profile-state/profile/")]
    for row in profile_rows:
        relative = str(row["path"])
        source = prior_candidate / relative
        if not source.is_file() or source.stat().st_size != row["size_bytes"] or sha256(source) != row["sha256"]:
            raise RuntimeError(f"R695 sealed prelaunch profile changed: {relative}")
        copy_file(source, output / relative)
    target_save = (
        output / "fresh-profile-state" / "profile" / "save games" / "dev3b_r639.ck3"
    )
    if sha256(target_save) != EXPECTED_SAVE_SHA256:
        raise RuntimeError("R696 target save differs before launch")
    descriptor = output / "fresh-profile-state" / "profile" / "mod" / "xar_autoplayer.mod"
    text = descriptor.read_text(encoding="utf-8-sig")
    old_path = (
        prior_candidate / "fresh-profile-state" / "profile" / "mod-content" / "xar-production"
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

    runner = Path(__file__).resolve().parent
    for name in ("run_council_r696_controlled_replace.py", "verify_council_r696_controlled_prep.py",
                 "council_r696_controlled_input_contract.template.json"):
        copy_file(runner / name, output / name)
    operator = {
        "schema": "xar.ck3.g2_m4_council_r696_controlled_operator_v1",
        "python": str(python),
        "game_dir": str(game),
        "pipe": r"\\.\pipe\xar_ck3_bridge_g2_m4_council_r696_replace_" + source_commit[:8],
        "last_completed_round": "R695",
        "suggested_new_round": "R696",
        "round_allocated": False,
        "readiness_timeout_seconds": 300,
        "operation_timeout_seconds": 60,
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
        "schema": "xar.ck3.g2_m4_council_r696_controlled_sealed_prep_v1",
        "status": "sealed-no-launch",
        "source_commit": source_commit,
        "runner_commit": git(runner.parents[2], "rev-parse", "HEAD"),
        "game_version": "1.19.0.6",
        "game_exe_sha256": EXPECTED_EXE_SHA256,
        "source_save_sha256": EXPECTED_SAVE_SHA256,
        "bridge_dll_sha256": sha256(output / "candidate-bin" / "xar_ck3_bridge.dll"),
        "injector_sha256": sha256(output / "candidate-bin" / "xar_ck3_bridge_injector.exe"),
        "prior_profile_prep_sha256": sha256(prior_candidate / "sealed-prep-manifest.json"),
        "profile_lineage": "R695 frozen prelaunch DLC/mod/settings; own descriptor path; dynamic live files omitted",
        "python_exe_sha256": sha256(python),
        "cmake_cache_sha256": sha256(cache_path),
        "cmake_options": PRIVATE_OPTIONS,
        "public_query_registered": False,
        "public_action_registered": False,
        "private_action_admitted": True,
        "private_action_budget": 1,
        "prior_r695_live_report_sha256": "16428FCD73665A8E72670D7DCDF2E29328DF9C405AD8C13A3AE60054184F72F2",
        "expected_scene": {
            "owner_character_id": 29829,
            "incumbent_character_id": 32716,
            "candidate_character_id": 33433,
            "already_councillor_positive_ids": [33435, 34333, 34867],
            "candidate_count": 11,
        },
        "gameplay_actions_maximum": 1,
        "formal_next_turn_consumption": "unsupported_private_candidate",
        "formal_goal_cold_restore": "unverified",
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
    parser.add_argument("--r695-candidate", type=Path, required=True)
    parser.add_argument("--build-release", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    manifest = prepare(
        args.repo, args.r695_candidate, args.build_release,
        args.game_dir, args.output, args.python, args.source_commit,
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
