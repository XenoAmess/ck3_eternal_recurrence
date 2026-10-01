"""Generate portable CK3 1.20 nonwar operator commands without touching CK3.

The default writes metadata and argv arrays only. An explicit
--prepare-profile-files builds the production projection and profile in a
fresh isolated state using the existing filesystem preparation core. Neither
mode queries CK3 processes, connects a pipe, copies a pair, allocates a live
run, or starts an operator. All machine paths are explicit inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "ck3_autonomous_player/configs/ck3-1.20.0.2-nonwar-runner.json"
SCHEMA = "xar.ck3.nonwar-offline-runner-plan/v1"
SOURCE_FILES = (
    "ck3_autonomous_player/agent.py",
    "ck3_autonomous_player/src/xar_autoplayer/cli.py",
    "ck3_autonomous_player/src/xar_autoplayer/one_generation_run.py",
    "ck3_autonomous_player/src/xar_autoplayer/one_generation_preflight.py",
    "tools/g2_preview_operator.py",
)


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha(value: str, label: str) -> str:
    if re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
        raise ValueError(f"{label} must be a SHA-256")
    return value.lower()


def lifecycle_args(lane: dict[str, Any]) -> list[str]:
    result = ["--xar-enabled", lane["xar_enabled"], "--succession-lifecycle",
              lane["succession_lifecycle"]]
    if lane["ordinary_campaign_no_pact"]:
        result.append("--ordinary-campaign-no-pact")
    return result


def plan(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    config = read_object(args.config)
    if config.get("schema") != "xar.ck3.nonwar-offline-runner-config/v1":
        raise ValueError("unsupported runner config schema")
    if config.get("game_version") != "1.20.0.2":
        raise ValueError("this entry requires the 1.20.0.2 config")
    if args.lane not in {"ordinary", "rogue"}:
        raise ValueError("lane must be ordinary or rogue")
    lane = config[args.lane]
    expected_lifecycle = {
        "ordinary": ("xar_off", "ordinary_campaign_succession", True),
        "rogue": ("xar_on", "rogue_one_life", False),
    }[args.lane]
    if (lane.get("xar_enabled"), lane.get("succession_lifecycle"),
            lane.get("ordinary_campaign_no_pact")) != expected_lifecycle:
        raise ValueError("lane lifecycle fields are inconsistent")
    if config.get("private_formal_trials_enabled") != []:
        raise ValueError("initial 1.20 plan requires private formal trials OFF")
    if not args.pipe.startswith("\\\\.\\pipe\\"):
        raise ValueError("pipe must be an explicit local Windows named pipe")
    source = args.source_repo.resolve()
    output = args.output_dir.resolve()
    state = args.state_dir.absolute()
    manifest_path = output / "operator-manifest.json"
    python = str(args.python.absolute())
    manifest: dict[str, Any] = {
        "python": python,
        "source_repo": str(source),
        "state_dir": str(state),
        "game_dir": str(args.game_dir.absolute()),
        "pipe": args.pipe,
        "dll": str(args.dll.absolute()),
        "injector": str(args.injector.absolute()),
        "dll_sha256": sha(args.dll_sha256, "DLL SHA"),
        "injector_sha256": sha(args.injector_sha256, "injector SHA"),
        "ck3_exe_sha256": sha(config["game_executable_sha256"], "EXE SHA"),
        "game_version": config["game_version"],
        "display_mode": config["display_mode"],
        **{name: lane[name] for name in (
            "xar_enabled", "succession_lifecycle", "ordinary_campaign_no_pact")},
        "formal_turns": lane.get("formal_turns", 20),
        "timeout_seconds": lane["timeout_seconds"],
        "readiness_timeout_seconds": lane["readiness_timeout_seconds"],
    }
    operator = [python, "-B", str(source / "tools/g2_preview_operator.py")]
    common = [python, "-B", str(source / "ck3_autonomous_player/agent.py"),
              "--state-dir", manifest["state_dir"],
              "--game-dir", manifest["game_dir"],
              "--bridge-mode", "native-headless", "--bridge-pipe", args.pipe,
              "--bridge-dll", manifest["dll"],
              "--bridge-injector", manifest["injector"]]
    prepare = [*operator, "prepare-state", "--manifest", str(manifest_path),
               "--sample-dir", str(args.sample_dir.absolute())]
    commands: list[dict[str, Any]] = [{
        "id": "official-prepare-and-pair",
        "occupies_ck3": False,
        "accesses_game_or_pair_assets": True,
        "executed": False,
        "argv": prepare,
    }]
    if args.lane == "ordinary":
        commands.append({
            "id": "ordinary-formal-20-turn",
            "occupies_ck3": True,
            "executed": False,
            "argv": [*operator, "run", "--manifest", str(manifest_path),
                     "--output", str(output / "live-formal-20-turn"),
                     "--turns", str(lane["formal_turns"]),
                     "--live-run-state-root", str(args.live_run_state_root.absolute())],
        })
        preflight = "official prepare-state derives identity pins after ordinary rebind and runs native-one-generation-preflight; no manually edited driver"
    else:
        if args.seed_identity is None:
            raise ValueError("rogue lane requires --seed-identity metadata for exact preflight")
        identity = read_object(args.seed_identity)
        if identity.get("game_version") != config["game_version"]:
            raise ValueError("seed metadata must describe a 1.20.0.2 pair")
        if type(identity.get("episode_character_id")) is not int or identity["episode_character_id"] < 1:
            raise ValueError("seed metadata requires a positive CharacterID")
        if not isinstance(identity.get("episode_run_id"), str) or not identity["episode_run_id"]:
            raise ValueError("seed metadata requires an episode_run_id")
        commands.append({
            "id": "exact-lifetime-preflight",
            "occupies_ck3": False,
            "accesses_game_or_pair_assets": True,
            "executed": False,
            "argv": [*common, "native-one-generation-preflight",
                     "--expected-character-id", str(identity["episode_character_id"]),
                     "--expected-episode-run-id", identity["episode_run_id"],
                     "--expected-checkpoint-sha256", sha(identity["checkpoint_sha256"], "seed checkpoint SHA"),
                     "--expected-driver-state-sha256", sha(identity["driver_state_sha256"], "seed driver SHA"),
                     *lifecycle_args(lane)],
        })
        run_limits = ["--max-turns", str(lane["max_turns"]),
                      "--timeout", str(lane["timeout_seconds"]),
                      "--readiness-timeout", str(lane["readiness_timeout_seconds"]),
                      "--checkpoint-every-advances", str(lane["checkpoint_every_advances"]),
                      "--route-contact-speed", str(lane["route_contact_speed"])]
        for command, label in (("native-one-generation", "full-lifetime"),
                               ("native-next-episode", "next-episode-after-settlement")):
            commands.append({
                "id": f"allocate-{label}", "occupies_ck3": False,
                "writes_live_allocator": True, "executed": False,
                "argv": [python, "-B", str(source / "tools/ck3_live_run_id.py"),
                         "allocate", "--mod", "eternal-recurrence",
                         "--state-root", str(args.live_run_state_root.absolute())],
            })
            commands.append({"id": label, "occupies_ck3": True,
                             "executed": False, "argv": [*common, command, *run_limits]})
        preflight = "explicit exact-lifetime-preflight must pass on the official prepared pair before the lifetime command"
    fingerprints = {name: digest(source / name) for name in SOURCE_FILES}
    result = {
        "schema": SCHEMA,
        "status": "static-ready-command-plan",
        "lane": args.lane,
        "candidate_identity": "independent-1.20.0.2-pair",
        "historical_robert_continuation": False,
        "history": config["history"],
        "new_g2_completed": 0,
        "new_durable_days": 0,
        "game_version": config["game_version"],
        "game_executable_sha256": manifest["ck3_exe_sha256"],
        "bundle_hashes": {"dll_declared": manifest["dll_sha256"],
                          "injector_declared": manifest["injector_sha256"],
                          "binary_files_read_or_verified": False},
        "source_file_sha256": fingerprints,
        "commands": commands,
        "prepare_pair_rule": preflight,
        "actual_ck3_access": False,
        "game_installation_files_read": False,
        "actual_profile_prepared": False,
        "actual_save_or_driver_read_or_copied": False,
        "ck3_launch_attempted": False,
        "runtime_live_verified": False,
        "live_execution_note": "Commands are an ordered plan, not an executable batch. Review official preparation and each previous result before the next phase; attach allocator IDs to lifetime artifacts. next-episode requires a verified terminal settlement, not turn-bound exhaustion.",
        "open_kaishek_precheck": {
            "status": "not-applicable",
            "reason": "argv/lifecycle/metadata composition contains no CK3 script, IR, finite-runtime or replay semantics",
        },
        "remaining_real_work": [
            "Freeze the selected 1.20 native bundle and matching runtime source; this plan does not attest private nonwar capabilities.",
            "Use a valid independent 1.20 paired sample; Robert h4025 remains an unchanged historical 1.19 pair.",
            "Run official prepare/rebind and exact no-launch preflight when asset access is permitted.",
            "Obtain local owner/Steam offline/live-run allocation before the commands marked occupies_ck3.",
            "Verify real material outcomes, next-turn consumption and cold restore; update G2/days only from durable original-lineage evidence.",
        ],
    }
    return manifest, result


def prepare_profile_files(args: argparse.Namespace, manifest: dict[str, Any]) -> dict[str, Any]:
    """Build a fresh profile without the public wrapper's process inventory.

    The public prepare-profile entry also refreshes existing states and thus
    refuses any CK3 process. Here only an unused isolated root is accepted;
    the existing preparation/verification core still owns all generated
    files, source projection, exact-game hashes and rule contracts.
    """
    source = args.source_repo.resolve()
    state = args.state_dir.absolute()
    if state.exists():
        raise ValueError("file-only preparation requires a fresh nonexistent state directory")
    sys.path.insert(0, str(source / "ck3_autonomous_player/src"))
    from xar_autoplayer import environment
    from xar_autoplayer.locking import exclusive_state_lock

    if Path(environment.__file__).resolve() != (
            source / "ck3_autonomous_player/src/xar_autoplayer/environment.py").resolve():
        raise RuntimeError("imported runtime is not the selected source repo")
    spec = environment.EnvironmentSpec(
        state_dir=state, game_dir=args.game_dir.absolute(),
        expected_game_version="1.20.0.2")
    with exclusive_state_lock(state, "nonwar-12002-fresh-profile-files"):
        prepared = environment._prepare_profile_locked(
            spec, xar_enabled=manifest["xar_enabled"],
            display_mode=manifest["display_mode"])
    actual_exe_sha = prepared["game"]["executable_sha256"].lower()
    if actual_exe_sha != manifest["ck3_exe_sha256"]:
        raise RuntimeError("prepared profile game EXE differs from the declared exact 1.20 build")
    return {
        "status": "profile-files-prepared",
        "profile_dir": prepared["profile_dir"],
        "environment_sha256": prepared["environment_sha256"],
        "executable_sha256": actual_exe_sha,
        "production_tree_sha256": prepared["mod"]["production_tree_sha256"],
        "process_inventory_called": False,
        "save_or_driver_copied": False,
        "pairing_or_cold_preflight_complete": False,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config", type=Path, default=CONFIG)
    result.add_argument("--lane", choices=("ordinary", "rogue"), default="ordinary")
    for name in ("source-repo", "python", "game-dir", "state-dir", "dll", "injector",
                 "sample-dir", "output-dir", "live-run-state-root"):
        result.add_argument(f"--{name}", type=Path, required=True)
    for name in ("pipe", "dll-sha256", "injector-sha256"):
        result.add_argument(f"--{name}", required=True)
    result.add_argument("--seed-identity", type=Path)
    result.add_argument("--prepare-profile-files", action="store_true",
                        help="explicitly prepare only fresh isolated production profile files; no CK3 process access or pair copying")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        manifest, result = plan(args)
        output = args.output_dir.resolve()
        # Default mode writes metadata; the explicit mode adds only a fresh profile.
        output.mkdir(parents=True, exist_ok=False)
        if args.prepare_profile_files:
            result["profile_file_preparation"] = prepare_profile_files(args, manifest)
            result.update({"status": "static-ready-profile-files",
                           "game_installation_files_read": True,
                           "actual_profile_prepared": True})
        for name, value in (("operator-manifest.json", manifest),
                            ("OFFLINE-RUNNER-PLAN.json", result)):
            (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
        print(json.dumps({"ok": True, "status": result["status"],
                          "output": str(output), "ck3_launch_attempted": False}))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, ImportError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
