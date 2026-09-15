"""Seal one version-matched, no-launch G2-M4 player-view read candidate.

Profile preparation is a separate, single-instance-gated operation: run the
existing production ``prepare_profile`` against a clean frozen source first,
then copy the immutable source checkpoint and paired driver state into that
new profile. This script verifies that result and only copies into an isolated
candidate directory. It never starts CK3 or uses a private gameplay harness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


EXE_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
SEED_SHA = "d8bdc3c44d21a6f94dc7e4c050db464f6c5036d5ba7e66233354b171f3401474"
PAIRED_SHA = "163850711947eacb8dfb3dec82e39bad332bd00bc119dbb36642ed701de4fb1a"
ACTOR = 29829
DATE_RAW = 53178312
COUNTY_IDS = [2102, 2142, 2173]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def git(source: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(source), *args], text=True).strip()


def r697_anchor(report_path: Path) -> dict[str, object]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    need(report.get("status") == "GREEN_READ_ONLY" and report.get("ok") is True,
         "R697 paired-seed qualification is not GREEN_READ_ONLY")
    stage = report.get("stage")
    need(isinstance(stage, dict) and stage.get("ok") is True, "R697 stage is not GREEN")
    ready = stage.get("readiness")
    need(isinstance(ready, dict), "R697 readiness missing")
    active = ready.get("active_context")
    need(isinstance(active, dict) and active.get("war_ids") == [] and active.get("army_ids") == []
         and active.get("active_event") is None and active.get("pending_character_interaction") is None,
         "R697 seed is not a peaceful unblocked paused scene")
    need(ready.get("paused") is True and ready.get("map_ready") is True
         and ready.get("played_character_id") == ACTOR and ready.get("date_raw") == DATE_RAW,
         "R697 paused actor/date differs")
    context = stage.get("sequence", {}).get("first_query", {}).get("campaign_root_context")
    need(isinstance(context, dict) and context.get("status") == "available"
         and context.get("snapshot_revision") == ready.get("native_revision")
         and context.get("date_raw") == DATE_RAW
         and context.get("player_character_id") == ACTOR,
         "R697 campaign-root actor/frame differs")
    government = context.get("government")
    need(isinstance(government, dict) and government.get("key") == "feudal_government",
         "R697 government is outside standard feudal scope")
    partition = context.get("held_title_partition")
    need(isinstance(partition, list), "R697 held title partition missing")
    counties = sorted(row["title"]["title_id"] for row in partition
                      if isinstance(row, dict) and isinstance(row.get("title"), dict)
                      and row["title"].get("tier_key") == "county")
    need(counties == COUNTY_IDS and context.get("capital_province_id") == 2619,
         "R697 held county/capital profile differs")
    return {
        "report_path": str(report_path), "report_sha256": sha(report_path),
        "round_id": "R697", "snapshot_id": ready.get("snapshot_id"),
        "native_revision": ready.get("native_revision"), "date_raw": DATE_RAW,
        "played_character_id": ACTOR, "government_key": "feudal_government",
        "held_county_title_ids": counties, "capital_province_id": 2619,
        "peace_no_army_event_or_pending": True,
        "coverage": "read_only_scene_qualification_only",
    }


def seal(args: argparse.Namespace) -> dict[str, object]:
    root = args.candidate_root.resolve()
    source = root / "sealed-source"
    profile_state = root / "fresh-profile-state"
    source_commit = args.source_commit.lower()
    need(len(source_commit) == 40 and all(ch in "0123456789abcdef" for ch in source_commit),
         "source commit must be a full Git SHA")
    need(root.is_dir() and source.is_dir() and profile_state.is_dir(),
         "candidate source/profile must exist before sealing")
    need(not (root / "candidate-manifest.json").exists(),
         "candidate is already sealed; make a new version for changes")
    need(git(source, "rev-parse", "HEAD") == source_commit
         and not git(source, "status", "--porcelain")
         and git(source, "branch", "--list", "work/*") == "",
         "sealed source is not clean master at frozen commit")
    exe = args.game_dir.resolve() / "binaries" / "ck3.exe"
    need(sha(exe) == EXE_SHA, "CK3 EXE differs from exact build")
    need(sha(args.source_save) == SEED_SHA and sha(args.paired_driver_state) == PAIRED_SHA,
         "immutable R697 checkpoint/paired state differs")
    cache_path = args.build_dir.resolve() / "CMakeCache.txt"
    cache = cache_path.read_text(encoding="utf-8", errors="replace")
    need("XAR_CK3_ENABLE_G2_PLAYER_CONSTRUCTION_VIEW_PROBE_PRIVATE_V1:BOOL=ON" in cache,
         "Release candidate private read option is not ON")
    need(f"CMAKE_HOME_DIRECTORY:INTERNAL={(args.build_source / 'ck3_autonomous_player' / 'native_bridge').resolve().as_posix()}".lower() in cache.lower(),
         "candidate DLL was built from a different source checkout")
    build_head = git(args.build_source, "rev-parse", "HEAD")
    need(build_head == source_commit and not git(args.build_source, "diff", "--name-only", source_commit,
         "--", "ck3_autonomous_player/src", "ck3_autonomous_player/native_bridge/src",
         "ck3_autonomous_player/native_bridge/include", "ck3_autonomous_player/native_bridge/CMakeLists.txt"),
         "candidate native/Python runtime differs from frozen source")
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"), str(source / "tools")]
    from xar_autoplayer.environment import ck3_process_inventory, make_spec, verify_profile
    from xar_autoplayer.native_session import validate_cold_start_checkpoint_for_pipe
    from xar_autoplayer.bridge.native_driver import load_native_driver_state_for_resume
    need(not ck3_process_inventory().get("processes"), "CK3 single-instance slot is occupied")
    spec = make_spec(profile_state, args.game_dir)
    environment = verify_profile(spec)
    prepared_save = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    prepared_driver = profile_state / "native-session" / "driver-state.json"
    need(sha(prepared_save) == SEED_SHA and sha(prepared_driver) == PAIRED_SHA,
         "prepared profile does not contain immutable R697 pair")
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, args.pipe)
    driver_state = load_native_driver_state_for_resume(prepared_driver, args.pipe)
    need(checkpoint.get("saved_date_raw") == DATE_RAW and isinstance(driver_state, dict)
         and driver_state.get("episode_character_id") == ACTOR,
         "cold restore qualification actor/date differs")
    anchor = r697_anchor(args.r697_report)
    bin_dir = root / "sealed-bin"
    bin_dir.mkdir()
    for name in ("xar_ck3_bridge.dll", "xar_ck3_bridge_injector.exe"):
        shutil.copy2(args.build_dir / name, bin_dir / name)
    seed_dir = root / "source-seed"
    seed_dir.mkdir()
    shutil.copy2(args.source_save, seed_dir / "xar_checkpoint.ck3")
    shutil.copy2(args.paired_driver_state, seed_dir / "driver-state.json")
    shutil.copy2(cache_path, root / "build-release-cache.txt")
    runner = Path(__file__).with_name("run_g2m4_player_view_live_candidate.py")
    shutil.copy2(runner, root / runner.name)
    profile_manifest = json.loads(spec.manifest_path.read_text(encoding="utf-8"))
    dlc_load = json.loads((spec.profile_dir / "dlc_load.json").read_text(encoding="utf-8"))
    result: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_player_view_private_live_candidate_v1",
        "status": "READY_NO_LAUNCH", "advertised": False,
        "source_commit": source_commit, "source_repo": str(source),
        "read_kind": args.read_kind,
        "candidate_root": str(root), "state_dir": str(profile_state),
        "game_dir": str(args.game_dir.resolve()), "game_exe_sha256": EXE_SHA,
        "source_save": str(seed_dir / "xar_checkpoint.ck3"), "source_save_sha256": SEED_SHA,
        "paired_driver_state": str(seed_dir / "driver-state.json"),
        "paired_driver_state_sha256": PAIRED_SHA,
        "prepared_save": str(prepared_save), "prepared_driver_state": str(prepared_driver),
        "pipe": args.pipe, "episode_character_id": ACTOR,
        "episode_run_id": driver_state.get("episode_run_id"), "date_raw": DATE_RAW,
        "dll": str(bin_dir / "xar_ck3_bridge.dll"),
        "dll_sha256": sha(bin_dir / "xar_ck3_bridge.dll"),
        "injector": str(bin_dir / "xar_ck3_bridge_injector.exe"),
        "injector_sha256": sha(bin_dir / "xar_ck3_bridge_injector.exe"),
        "cmake_cache_sha256": sha(root / "build-release-cache.txt"),
        "private_feature_on": True, "source_feature_default_off": True,
        "profile_environment_sha256": environment.get("environment_sha256"),
        "production_mod_tree_sha256": profile_manifest.get("mod", {}).get("production_tree_sha256"),
        "dlc_descriptor_fingerprint": profile_manifest.get("dlc"),
        "dlc_mod_load_order": dlc_load,
        "configuration": {
            "rules": profile_manifest.get("rules"),
            "display": profile_manifest.get("display"),
            "load_profile": profile_manifest.get("load_profile"),
        },
        "operator_python": str(args.operator_python.resolve()),
        "operator_python_sha256": sha(args.operator_python),
        "r697_qualification": anchor,
        "live_entry": str(root / runner.name), "live_entry_sha256": sha(root / runner.name),
        "assertions": ["same paused actor/date/feudal/held county", "no war/army/event/pending",
                       "root native_revision same frame", "private cache status/count consistent",
                       "unchanged paused frame before/after", "CK3 process reclaimed"] + (
                           ["slot42 player-model source TitleID/ProvinceID and definition count same paused frame",
                            "active CHoldingView model binding true; legality not inferred or action submitted"]
                       if args.read_kind == "player-model-sources" else (
                           ["slot42 independent world CBuildingType registry count and six directly held TitleID/ProvinceID rows in same paused revision",
                            "bounded stock player final-legality checks with nonempty pointer-free true sample or evidence_insufficient",
                            "cost/action false, no CK3 action/date and private/public ad false"]
                           if args.read_kind == "player-world-definitions" else [])),
        "bounds": {"readiness_timeout_seconds": 300, "query_timeout_seconds_each": 12,
                   "overall_window_seconds": 480},
        "ck3_inventory_before_launch": ck3_process_inventory(),
        "live_evidence": None, "construction_action_loop": False,
    }
    (root / "candidate-manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate-root", "build-dir", "build-source", "source-save",
                 "paired-driver-state", "game-dir", "r697-report", "operator-python"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--pipe", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--read-kind", choices=("cache-view", "player-model-sources",
                                                "player-world-definitions"),
                        default="cache-view")
    args = parser.parse_args()
    result = seal(args)
    print(json.dumps({key: result[key] for key in (
        "status", "source_commit", "dll_sha256", "injector_sha256",
        "profile_environment_sha256", "live_entry")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
