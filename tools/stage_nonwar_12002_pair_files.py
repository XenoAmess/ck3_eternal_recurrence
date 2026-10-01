"""Freeze or stage one explicitly pinned rogue CK3 pair using file-only checks.

The save and full persisted driver are copied byte-for-byte. No game process,
named pipe, desktop, allocator, ordinary rebind or official preflight runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge.native_driver import load_native_driver_state_for_resume
from xar_autoplayer.bridge.succession_transition_contract import ROGUE_ONE_LIFE
from xar_autoplayer.ck3_save_artifacts import inspect_ck3_save_artifact_v1, require_seedable_ck3_save_v1
from xar_autoplayer.environment import EnvironmentSpec, verify_profile
from xar_autoplayer.locking import exclusive_state_lock
from xar_autoplayer.native_session import validate_cold_start_checkpoint_for_pipe


def qualify(spec: EnvironmentSpec, args: argparse.Namespace) -> dict[str, Any]:
    save = spec.profile_dir / "save games/xar_checkpoint.ck3"
    driver = spec.state_dir / "native-session/driver-state.json"
    artifact = inspect_ck3_save_artifact_v1(save, profile_dir=spec.profile_dir)
    require_seedable_ck3_save_v1(artifact)
    raw_bytes = driver.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8-sig"))
    consumed = load_native_driver_state_for_resume(driver, args.pipe)
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, args.pipe)
    driver_sha = hashlib.sha256(raw_bytes).hexdigest()
    checks = {
        "save_sha": artifact["sha256"] == args.expected_save_sha256.lower(),
        "driver_sha": driver_sha == args.expected_driver_sha256.lower(),
        "full_driver_v2": raw.get("format_version") == 2,
        "pipe": raw.get("pipe_name") == args.pipe,
        "character": raw.get("episode_character_id") == args.expected_character_id,
        "episode": raw.get("episode_run_id") == args.expected_episode_run_id,
        "date": checkpoint["saved_date_raw"] == args.expected_date_raw,
        "history_anchor": checkpoint["history_index"] == args.expected_history_index,
        "consumer_accepted": consumed is not None,
        "rogue_lifecycle": isinstance(consumed, dict) and consumed["succession_lifecycle"]["lifecycle"] == ROGUE_ONE_LIFE,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError("file pair differs from expected pins: " + ", ".join(failed))
    return {"status": "PASS_FILE_PAIR", "save": artifact,
            "driver": {"path": str(driver), "bytes": len(raw_bytes), "sha256": driver_sha,
                       "format_version": raw["format_version"],
                       "history_count": len(raw["command_history"]),
                       "episode_character_id": raw["episode_character_id"],
                       "episode_run_id": raw["episode_run_id"],
                       "persisted_lifecycle": raw.get("succession_lifecycle"),
                       "consumer_lifecycle": consumed["succession_lifecycle"]},
            "checkpoint": checkpoint, "checks": checks}


def stage(args: argparse.Namespace) -> dict[str, Any]:
    source_save = args.source_save.resolve()
    source_driver = args.source_driver.resolve()
    source_state = source_driver.parent.parent
    source = EnvironmentSpec(state_dir=source_state, game_dir=Path("unused-game-not-read"))
    if (source_driver != source_state / "native-session/driver-state.json"
            or source_save != source.profile_dir / "save games/xar_checkpoint.ck3"):
        raise ValueError("explicit source files must be the canonical save/full-driver pair")
    source_qualification = qualify(source, args)
    target_state = args.target_state.absolute()
    target = EnvironmentSpec(state_dir=target_state,
                             game_dir=args.game_dir.absolute() if args.game_dir else Path("unused-game-not-read"),
                             expected_game_version="1.20.0.2")
    target_save = target.profile_dir / "save games/xar_checkpoint.ck3"
    target_driver = target.state_dir / "native-session/driver-state.json"
    if args.into_prepared_profile:
        if args.game_dir is None:
            raise ValueError("--into-prepared-profile requires --game-dir")
        profile = verify_profile(target, xar_enabled="xar_on")
        if profile["game"]["raw_version"] != "1.20.0.2":
            raise ValueError("prepared profile must be CK3 1.20.0.2")
    elif target_state.exists():
        raise ValueError("pair freeze requires a fresh nonexistent target state")
    if target_save.exists() or target_driver.exists():
        raise ValueError("refusing to overwrite an existing target save or full driver")
    with exclusive_state_lock(target_state, "nonwar-12002-pair-file-stage"):
        target_save.parent.mkdir(parents=True, exist_ok=True)
        target_driver.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_save, target_save)
        shutil.copyfile(source_driver, target_driver)
        target_qualification = qualify(target, args)
    identity = {
        "game_version": "1.20.0.2", "episode_character_id": args.expected_character_id,
        "episode_run_id": args.expected_episode_run_id,
        "checkpoint_sha256": args.expected_save_sha256.lower(),
        "driver_state_sha256": args.expected_driver_sha256.lower(),
        "date_raw": args.expected_date_raw, "history_index": args.expected_history_index,
        "pipe": args.pipe,
    }
    (target_state / "SEED-IDENTITY.json").write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
    result = {
        "schema": "xar.ck3.nonwar-12002-file-pair-stage/v1",
        "status": "PASS_STATIC_FILE_PAIR",
        "source": source_qualification, "target": target_qualification,
        "into_prepared_profile": args.into_prepared_profile,
        "source_files_written": False, "pipe_episode_history_rewritten": False,
        "ordinary_campaign_rebind_performed": False,
        "official_zero_process_preflight_completed": False,
        "ck3_process_pipe_desktop_steam_or_allocator_accessed": False,
        "real_game_cold_restore_completed": False,
        "robert_credit_days": 0, "g2_completed_increment": 0,
        "scope": "rogue canonical save/full-driver byte pairing only; no private NW sidecar or tutorial continuity claim",
        "seed_identity": identity,
    }
    (target_state / "PAIR-FILES-QUALIFICATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    for name in ("source-save", "source-driver", "target-state"):
        result.add_argument(f"--{name}", type=Path, required=True)
    for name in ("expected-save-sha256", "expected-driver-sha256", "expected-episode-run-id", "pipe"):
        result.add_argument(f"--{name}", required=True)
    for name in ("expected-character-id", "expected-date-raw", "expected-history-index"):
        result.add_argument(f"--{name}", type=int, required=True)
    result.add_argument("--into-prepared-profile", action="store_true")
    result.add_argument("--game-dir", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    target_existed = args.target_state.exists()
    try:
        result = stage(args)
        print(json.dumps({"status": result["status"], "target": str(args.target_state),
                          "real_game_cold_restore_completed": False}))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        failure = {"status": "RED_STATIC_FILE_PAIR", "error": f"{type(error).__name__}: {error}",
                   "source_files_written": False, "ck3_process_pipe_desktop_steam_or_allocator_accessed": False}
        # Preserve an existing state/archive on a repeated or refused request.
        if not target_existed:
            args.target_state.mkdir(parents=True, exist_ok=True)
            (args.target_state / "PAIR-FILES-QUALIFICATION-RED.json").write_text(json.dumps(failure, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failure), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
