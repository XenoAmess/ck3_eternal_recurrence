"""Seal an isolated R739 feudal checkpoint with the proven R700 gate-only reader.

The caller copies both frozen sources into a new candidate directory first. This
script performs only no-launch version/config checks and freezes the candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from inspect_council_final_gate_scene import sha256
from run_council_native_gate_scene_v1 import EXE_SHA, PRIVATE_FLAGS, SCHEMA


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def entries(root: Path, candidate: Path) -> list[dict[str, object]]:
    require(root.is_dir(), f"frozen tree absent: {root}")
    return [{"path": path.relative_to(candidate).as_posix(),
             "size_bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(root.rglob("*")) if path.is_file()]


def equal_tree(source: Path, target: Path, candidate: Path) -> list[dict[str, object]]:
    left = [(path.relative_to(source).as_posix(), path.stat().st_size, sha256(path))
            for path in sorted(source.rglob("*")) if path.is_file()]
    right = [(path.relative_to(target).as_posix(), path.stat().st_size, sha256(path))
             for path in sorted(target.rglob("*")) if path.is_file()]
    require(left and left == right, f"isolated copy differs from frozen tree: {source}")
    return [{"path": (target / relative).relative_to(candidate).as_posix(),
             "size_bytes": size, "sha256": digest}
            for relative, size, digest in right]


def relocate_profile(candidate: Path, r739: Path) -> str:
    env_path = candidate / "state" / "profile" / "xar-autoplayer-environment.json"
    descriptor = candidate / "state" / "profile" / "mod" / "xar_autoplayer.mod"
    source = json.loads(env_path.read_text(encoding="utf-8"))
    old_state = str((r739 / "fresh-profile-state").resolve())
    old_source = str((r739 / "sealed-source").resolve())
    new_state = str((candidate / "state").resolve())
    new_source = str((candidate / "sealed-source").resolve())

    def replace(value: object) -> object:
        if isinstance(value, str):
            return value.replace(old_state, new_state).replace(old_source, new_source)
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        return value

    env = replace(source)
    require(isinstance(env, dict), "profile environment is not a typed object")
    load = env.get("load_profile")
    require(isinstance(load, dict), "profile load contract absent")
    load["outer_descriptor_sha256"] = sha256(descriptor).lower()
    sys.path.insert(0, str(candidate / "source-repo" / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.environment import _contract_digest

    env["environment_sha256"] = _contract_digest(env)
    env_path.write_text(json.dumps(env, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    require(env.get("state_dir") == new_state and
            env.get("profile_dir") == str((candidate / "state" / "profile").resolve())
            and env["environment_sha256"] == _contract_digest(env),
            "relocated profile environment digest/path differs")
    return str(env["environment_sha256"])


def seal(candidate: Path, r739: Path, r700: Path, game: Path,
         python: Path, repo: Path) -> dict[str, object]:
    candidate = candidate.resolve()
    r739 = r739.resolve()
    r700 = r700.resolve()
    repo = repo.resolve()
    manifest_path = candidate / "candidate-manifest.json"
    require(candidate.is_dir() and not manifest_path.exists(),
            "candidate absent or already sealed; do not overwrite a frozen version")
    report_path = r739 / "live-R739" / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    root = report["read"]["campaign_root_frame"]["result"]["campaign_root_context"]
    positions = [row for row in root["council"]["positions"]
                 if row.get("position_key") == "councillor_steward"]
    require(report.get("round_id") == "R739" and len(positions) == 1
            and root["government"]["key"] == "feudal_government"
            and report["starting_frame"]["date_raw"] ==
            report["read"]["ending_frame"]["date_raw"],
            "R739 source is not one unchanged ordinary-feudal paused scene")
    frame = {"played_character_id": report["starting_frame"]["played_character_id"],
             "date_raw": report["starting_frame"]["date_raw"],
             "native_revision": report["starting_frame"]["native_revision"],
             "snapshot_id": report["starting_frame"]["snapshot_id"],
             "government_key": "feudal_government",
             "steward_incumbent_character_id": positions[0]["incumbent_character_id"],
             "steward_task_key": positions[0]["task_key"]}
    save = r739 / "source-seed" / "xar_checkpoint.ck3"
    driver = r739 / "source-seed" / "driver-state.json"
    save_sha = sha256(save)
    driver_sha = sha256(driver)
    require(save_sha == report["source_save_sha256"].upper()
            and driver_sha == report["paired_driver_state_sha256"].upper()
            and save_sha == sha256(candidate / "source-save" / "xar_checkpoint.ck3")
            == sha256(candidate / "state" / "profile" / "save games" / "xar_checkpoint.ck3")
            and driver_sha == sha256(candidate / "state" / "native-session" / "driver-state.json"),
            "new candidate source/target game save and driver are not the exact R739 pair")
    checkpoint = json.loads(driver.read_text(encoding="utf-8"))["last_checkpoint"]
    require(checkpoint["sha256"].upper() == save_sha
            and checkpoint["date_raw"] == frame["date_raw"]
            and checkpoint["episode_character_id"] == frame["played_character_id"],
            "R739 driver checkpoint binding differs")
    old = json.loads((r700 / "sealed-prep-manifest.json").read_text(encoding="utf-8"))
    require(old.get("native_source_commit") ==
            "72882e69c11a8b77e4926dfa22ae52998b0e1a61"
            and old.get("bridge_dll_sha256", "").upper() ==
            "77515453226DEE89E24044BB4B173F795258FCAFE44F3C5EA1CE5E75159ECA8D",
            "R700 proven gate-only binary/version differs")
    for name in ("xar_ck3_bridge.dll", "xar_ck3_bridge_injector.exe", "CMakeCache.txt"):
        require(sha256(r700 / "candidate-bin" / name) ==
                sha256(candidate / "candidate-bin" / name),
                f"R700 private native binary/cache copy differs: {name}")
    cache = (candidate / "candidate-bin" / "CMakeCache.txt").read_text(
        encoding="utf-8", errors="replace")
    require(all(f"{flag}:BOOL={value}" in cache
                for flag, value in PRIVATE_FLAGS.items()),
            "R700 native gate-only build flags differ")
    require(sha256(game / "binaries" / "ck3.exe") == EXE_SHA,
            "CK3 executable is not the frozen 1.19.0.6 build")
    dlc = json.loads((candidate / "state" / "profile" / "dlc_load.json").read_text(
        encoding="utf-8-sig"))
    require(dlc == {"enabled_mods": ["mod/xar_autoplayer.mod"],
                    "disabled_dlcs": []}, "formal mod/DLC profile differs")
    mod_root = candidate / "state" / "profile" / "mod-content" / "xar-production"
    descriptor = candidate / "state" / "profile" / "mod" / "xar_autoplayer.mod"
    require(f'path="{mod_root.as_posix()}"' in descriptor.read_text(encoding="utf-8-sig"),
            "candidate mod descriptor still points to another workspace")
    environment_digest = relocate_profile(candidate, r739)
    rows = equal_tree(r739 / "fresh-profile-state" / "profile" / "mod-content" /
                      "xar-production", mod_root, candidate)
    rows += equal_tree(r739 / "sealed-source" / "XenoAmess_s_Eternal_Recurrence",
                       candidate / "sealed-source" / "XenoAmess_s_Eternal_Recurrence",
                       candidate)
    rows += equal_tree(r700 / "source-repo", candidate / "source-repo", candidate)
    selected = ["source-save/xar_checkpoint.ck3",
                "state/profile/save games/xar_checkpoint.ck3",
                "state/native-session/driver-state.json",
                "candidate-bin/xar_ck3_bridge.dll",
                "candidate-bin/xar_ck3_bridge_injector.exe",
                "candidate-bin/CMakeCache.txt",
                "state/profile/dlc_load.json", "state/profile/pdx_settings.txt",
                "state/profile/xar-autoplayer-environment.json",
                "state/profile/mod/xar_autoplayer.mod",
                "state/profile/mod-content/xar-production.manifest.json",
                "state/profile/mod-content/xar-production.zip",
                "run_council_native_gate_scene_v1.py",
                "inspect_council_final_gate_scene.py"]
    for relative in selected:
        path = candidate / relative
        require(path.is_file(), f"essential frozen candidate file absent: {relative}")
        rows.append({"path": relative, "size_bytes": path.stat().st_size,
                     "sha256": sha256(path)})
    require(len(rows) == len({row["path"] for row in rows}),
            "candidate frozen file manifest contains duplicate paths")
    runner_tip = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo,
                                         text=True).strip()
    pipe_suffix = hashlib.sha256(str(candidate).encode()).hexdigest()[:10]
    manifest = {
        "schema": SCHEMA, "status": "sealed-no-launch",
        "work_package_id": "G2-COUNCIL-R739-GATE-QUERY-SEAL",
        "source_round": "R739", "source_commit": report["source_commit"],
        "r739_report_sha256": sha256(report_path),
        "r700_sealed_manifest_sha256": sha256(r700 / "sealed-prep-manifest.json"),
        "native_source_commit": old["native_source_commit"],
        "runner_source_commit": runner_tip,
        "source_save_sha256": save_sha, "source_driver_sha256": driver_sha,
        "dll_sha256": sha256(candidate / "candidate-bin" / "xar_ck3_bridge.dll"),
        "injector_sha256": sha256(candidate / "candidate-bin" /
                                  "xar_ck3_bridge_injector.exe"),
        "private_build_flags": PRIVATE_FLAGS,
        "game_dir": str(game.resolve()), "game_exe_sha256": EXE_SHA,
        "operator_python": str(python.resolve()),
        "operator_python_sha256": sha256(python),
        "enabled_mods_in_order": ["mod/xar_autoplayer.mod"],
        "disabled_dlcs": [],
        "profile_environment_sha256": environment_digest,
        "expected_frame": frame,
        "pipe": r"\\.\pipe\xar_ck3_g2_council_r739_scene_" + pipe_suffix,
        "bounded_seconds": {"overall": 480, "readiness": 300, "native_query": 60},
        "gameplay_actions": 0, "public_registered_or_advertised": False,
        "controlled_rejection_verified": False,
        "three_positive_scene_status": "unknown_until_native_paused_query",
        "frozen_file_count": len(rows), "frozen_files": sorted(rows, key=lambda x: x["path"]),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    return {"status": "sealed-no-launch", "candidate_manifest_sha256":
            sha256(manifest_path), "frozen_file_count": len(rows),
            "source_save_sha256": save_sha, "source_driver_sha256": driver_sha,
            "dll_sha256": manifest["dll_sha256"], "ck3_launched": False,
            "public_registered_or_advertised": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--r739-root", type=Path, required=True)
    parser.add_argument("--r700-root", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--operator-python", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    args = parser.parse_args()
    result = seal(args.candidate_root, args.r739_root, args.r700_root,
                  args.game_dir, args.operator_python, args.source_repo)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
