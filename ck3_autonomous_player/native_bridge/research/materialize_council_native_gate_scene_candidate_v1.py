"""Materialize a fresh read-only Council gate candidate from a durable pair.

This is a no-launch tool.  It copies the proven private query-only native
binary/runtime, projects the source driver to its last durable checkpoint, and
relocates an isolated CK3 profile.  Gameplay after the checkpoint is never
carried into the candidate.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from inspect_council_final_gate_scene import sha256
from run_council_native_gate_scene_v1 import EXE_SHA, PRIVATE_FLAGS, SCHEMA


DLL_SHA = "77515453226DEE89E24044BB4B173F795258FCAFE44F3C5EA1CE5E75159ECA8D"
INJECTOR_SHA = "09E35E9E86FF714CBA8D716223C951EAC271DBDEFA8C6C638B0765D265A99D51"
NATIVE_SOURCE_COMMIT = "72882e69c11a8b77e4926dfa22ae52998b0e1a61"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def replace_strings(value: object, pairs: tuple[tuple[str, str], ...]) -> object:
    if isinstance(value, str):
        for old, new in pairs:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [replace_strings(item, pairs) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item, pairs) for key, item in value.items()}
    return value


def derive_checkpoint_projection(
    driver: dict[str, object], save_sha: str, target_save: Path, pipe: str
) -> tuple[dict[str, object], dict[str, object]]:
    """Return a checkpoint-only driver and its observed ordinary-feudal frame."""

    checkpoint = driver.get("last_checkpoint")
    history = driver.get("command_history")
    require(driver.get("format_version") == 2 and isinstance(checkpoint, dict)
            and isinstance(history, list), "source driver/checkpoint history is malformed")
    history_index = checkpoint.get("history_index")
    actor = checkpoint.get("episode_character_id")
    date_raw = checkpoint.get("date_raw")
    require(type(history_index) is int and 0 < history_index <= len(history)
            and type(actor) is int and actor > 0 and type(date_raw) is int
            and checkpoint.get("sha256", "").upper() == save_sha,
            "source checkpoint does not bind the supplied save/history")
    require(all(isinstance(row, dict) and row.get("index") == index
                for index, row in enumerate(history, start=1)),
            "source command history is not contiguous")

    observations: list[tuple[dict[str, object], dict[str, object]]] = []
    for row in history:
        if not isinstance(row, dict):
            continue
        result = row.get("result")
        context = result.get("campaign_root_context") if isinstance(result, dict) else None
        if (isinstance(context, dict) and context.get("date_raw") == date_raw
                and context.get("player_character_id") == actor):
            observations.append((row, context))
    require(observations, "no campaign-root observation binds the checkpoint frame")
    source_row, context = observations[-1]
    government = context.get("government")
    council = context.get("council")
    require(isinstance(government, dict)
            and government.get("key") == "feudal_government"
            and isinstance(council, dict)
            and council.get("owner_character_id") == actor,
            "checkpoint observation is not standard-feudal player Council state")
    positions = [row for row in council.get("positions", [])
                 if isinstance(row, dict)
                 and row.get("position_key") == "councillor_steward"]
    require(len(positions) == 1, "checkpoint has no unique steward position")
    steward = positions[0]
    incumbent = steward.get("incumbent_character_id")
    require(type(incumbent) is int and incumbent > 0,
            "checkpoint steward is vacant; replacement-fireability query needs occupancy")

    projected = copy.deepcopy(driver)
    projected["pipe_name"] = pipe
    projected["command_history"] = copy.deepcopy(history[:history_index])
    projected["managed_restore_transaction"] = None
    projected["succession_expectation"] = None
    projected_checkpoint = copy.deepcopy(checkpoint)
    projected_checkpoint["path"] = str(target_save.resolve())
    projected["last_checkpoint"] = projected_checkpoint
    require(len(projected["command_history"]) == history_index
            and projected["command_history"][-1].get("index") == history_index,
            "checkpoint projection retained non-durable command history")

    frame = {
        "played_character_id": actor,
        "date_raw": date_raw,
        "source_snapshot_revision": context.get("snapshot_revision"),
        "source_command_history_index": source_row.get("index"),
        "source_checkpoint_history_index": history_index,
        "government_key": "feudal_government",
        "steward_vacant": False,
        "steward_incumbent_character_id": incumbent,
        "steward_task_key": steward.get("task_key"),
    }
    return projected, frame


def copy_profile(source_profile: Path, target_profile: Path) -> None:
    shutil.copytree(source_profile, target_profile)
    for relative in ("logs", "save games"):
        path = target_profile / relative
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)


def frozen_rows(root: Path, manifest_path: Path) -> list[dict[str, object]]:
    rows = [{"path": path.relative_to(root).as_posix(),
             "size_bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(root.rglob("*"))
            if path.is_file() and path != manifest_path]
    require(rows and len(rows) == len({row["path"] for row in rows}),
            "candidate frozen-file inventory is empty or duplicated")
    return rows


def resolve_source_state(
    source_stage: Path | None, source_state: Path | None
) -> Path:
    """Resolve either the legacy stage/state layout or a direct state root."""

    require((source_stage is None) != (source_state is None),
            "provide exactly one source stage or source state root")
    return (
        source_state.resolve()
        if source_state is not None
        else (source_stage.resolve() / "state")
    )


def materialize(
    candidate: Path, static: Path, source_state: Path, source_pair: Path,
    game: Path, python: Path, repo: Path, source_round: str, source_commit: str,
) -> dict[str, object]:
    candidate = candidate.resolve()
    static = static.resolve()
    source_state = source_state.resolve()
    source_pair = source_pair.resolve()
    repo = repo.resolve()
    require(not candidate.exists(), "candidate root already exists; frozen versions are immutable")
    require(re.fullmatch(r"R[1-9][0-9]*", source_round) is not None,
            "source round is not monotonic")
    require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
            "source commit is not a full lowercase Git object id")
    source_save = source_pair / "xar_checkpoint.ck3"
    source_driver = source_pair / "driver-state.json"
    source_profile = source_state / "profile"
    require(source_save.is_file() and source_driver.is_file()
            and source_profile.is_dir(), "durable source pair/profile is absent")
    save_sha = sha256(source_save)
    original_driver_sha = sha256(source_driver)
    require(source_save.open("rb").read(7) == b"SAV0101",
            "source checkpoint is not SAV0101")

    candidate.mkdir(parents=True)
    shutil.copytree(static / "candidate-bin", candidate / "candidate-bin")
    shutil.copytree(static / "source-repo", candidate / "source-repo")
    for name in ("run_council_native_gate_scene_v1.py",
                 "inspect_council_final_gate_scene.py"):
        shutil.copy2(repo / "ck3_autonomous_player" / "native_bridge" /
                     "research" / name, candidate / name)
    copy_profile(source_profile, candidate / "state" / "profile")
    production_mod = candidate / "state" / "profile" / "mod-content" / "xar-production"
    require(production_mod.is_dir(), "source profile has no production mod tree")
    shutil.copytree(production_mod, candidate / "sealed-source" /
                    "XenoAmess_s_Eternal_Recurrence")

    pipe_suffix = hashlib.sha256(str(candidate).encode()).hexdigest()[:10]
    pipe = rf"\\.\pipe\xar_ck3_g2_council_{source_round.lower()}_query_{pipe_suffix}"
    target_save = candidate / "state" / "profile" / "save games" / "xar_checkpoint.ck3"
    target_save.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_save, target_save)
    (candidate / "source-save").mkdir()
    shutil.copy2(source_save, candidate / "source-save" / "xar_checkpoint.ck3")
    driver = json.loads(source_driver.read_text(encoding="utf-8"))
    projected, frame = derive_checkpoint_projection(driver, save_sha, target_save, pipe)
    driver_path = candidate / "state" / "native-session" / "driver-state.json"
    driver_path.parent.mkdir(parents=True)
    driver_path.write_text(json.dumps(projected, ensure_ascii=False,
                                      separators=(",", ":")) + "\n", encoding="utf-8")
    projected_driver_sha = sha256(driver_path)

    descriptor = candidate / "state" / "profile" / "mod" / "xar_autoplayer.mod"
    descriptor_text = descriptor.read_text(encoding="utf-8-sig")
    old_mod = (source_profile / "mod-content" / "xar-production").as_posix()
    new_mod = production_mod.as_posix()
    require(descriptor_text.count(old_mod) == 1,
            "source descriptor does not have one relocatable production path")
    descriptor.write_text(descriptor_text.replace(old_mod, new_mod), encoding="utf-8-sig")
    dlc = json.loads((candidate / "state" / "profile" / "dlc_load.json").read_text(
        encoding="utf-8-sig"))
    require(dlc == {"enabled_mods": ["mod/xar_autoplayer.mod"], "disabled_dlcs": []},
            "source profile mod/DLC contract differs")

    env_path = candidate / "state" / "profile" / "xar-autoplayer-environment.json"
    env = json.loads(env_path.read_text(encoding="utf-8"))
    old_mod_source = str(env.get("mod", {}).get("source", ""))
    require(old_mod_source and Path(old_mod_source).is_absolute(),
            "source environment has no relocatable absolute mod source")
    env = replace_strings(env, (
        (str(source_state), str(candidate / "state")),
        (str(source_profile), str(candidate / "state" / "profile")),
        (old_mod_source, str(candidate / "sealed-source" /
                             "XenoAmess_s_Eternal_Recurrence")),
    ))
    require(isinstance(env, dict) and isinstance(env.get("load_profile"), dict),
            "source environment is malformed")
    env["load_profile"]["outer_descriptor_sha256"] = sha256(descriptor).lower()
    sys.path.insert(0, str(candidate / "source-repo" / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.environment import _contract_digest
    env["environment_sha256"] = _contract_digest(env)
    env_path.write_text(json.dumps(env, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    require(env.get("state_dir") == str((candidate / "state").resolve())
            and env.get("profile_dir") ==
            str((candidate / "state" / "profile").resolve())
            and env["environment_sha256"] == _contract_digest(env),
            "relocated environment path/digest differs")

    cache = (candidate / "candidate-bin" / "CMakeCache.txt").read_text(
        encoding="utf-8", errors="replace")
    dll = candidate / "candidate-bin" / "xar_ck3_bridge.dll"
    injector = candidate / "candidate-bin" / "xar_ck3_bridge_injector.exe"
    require(sha256(dll) == DLL_SHA and sha256(injector) == INJECTOR_SHA
            and all(f"{key}:BOOL={value}" in cache for key, value in PRIVATE_FLAGS.items()),
            "proven private query-only native binary differs")
    require(sha256(game / "binaries" / "ck3.exe") == EXE_SHA,
            "CK3 exact build differs")

    manifest_path = candidate / "candidate-manifest.json"
    rows = frozen_rows(candidate, manifest_path)
    runner_tip = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo,
                                         text=True).strip()
    manifest = {
        "schema": SCHEMA, "status": "sealed-no-launch",
        "work_package_id": f"G2-COUNCIL-{source_round}-CHECKPOINT-QUERY",
        "source_round": source_round, "source_commit": source_commit,
        "source_save_sha256": save_sha,
        "source_original_driver_sha256": original_driver_sha,
        "source_driver_sha256": projected_driver_sha,
        "source_checkpoint_history_index": frame["source_checkpoint_history_index"],
        "source_tail_policy": "discarded_after_last_durable_checkpoint",
        "native_source_commit": NATIVE_SOURCE_COMMIT,
        "runner_source_commit": runner_tip,
        "dll_sha256": sha256(dll), "injector_sha256": sha256(injector),
        "private_build_flags": PRIVATE_FLAGS,
        "game_dir": str(game.resolve()), "game_exe_sha256": EXE_SHA,
        "operator_python": str(python.resolve()),
        "operator_python_sha256": sha256(python),
        "enabled_mods_in_order": ["mod/xar_autoplayer.mod"], "disabled_dlcs": [],
        "profile_environment_sha256": env["environment_sha256"],
        "expected_frame": frame, "pipe": pipe,
        "bounded_seconds": {"overall": 480, "readiness": 300, "native_query": 60},
        "gameplay_actions": 0, "public_registered_or_advertised": False,
        "controlled_rejection_verified": False,
        "four_gate_scene_status": "unknown_until_native_paused_query",
        "frozen_file_count": len(rows), "frozen_files": rows,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    return {"status": "sealed-no-launch",
            "candidate_manifest_sha256": sha256(manifest_path),
            "source_save_sha256": save_sha,
            "source_original_driver_sha256": original_driver_sha,
            "projected_driver_sha256": projected_driver_sha,
            "projected_history_count": len(projected["command_history"]),
            "expected_frame": frame, "frozen_file_count": len(rows),
            "ck3_launched": False, "public_registered_or_advertised": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--static-root", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--source-stage", type=Path,
        help="legacy preview/staging root containing state/profile",
    )
    source.add_argument(
        "--source-state", type=Path,
        help="direct runtime state root containing profile and native-session",
    )
    parser.add_argument("--source-pair", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--operator-python", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--source-round", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    source_state = resolve_source_state(args.source_stage, args.source_state)
    result = materialize(args.candidate_root, args.static_root, source_state,
                         args.source_pair, args.game_dir, args.operator_python,
                         args.source_repo, args.source_round, args.source_commit)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
