"""Consume a frozen G2 native build and prepare a new file-only candidate.

Default mode writes plans. --prepare-profile-files additionally uses the
existing fresh-profile core and canonical-pair copier. No CK3 process
inventory, pipe, desktop, Steam, official preflight or live allocator runs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import run_nonwar_12002_offline as offline


REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "ck3_autonomous_player/configs/ck3-1.20.0.2-g2-offline-runner.json"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_build_inputs(args: argparse.Namespace) -> dict[str, Any]:
    manifest_sha = offline.digest(args.integration_manifest)
    if manifest_sha != offline.sha(args.integration_manifest_sha256, "integration manifest SHA"):
        raise ValueError("integration manifest differs from the final frozen SHA")
    manifest = offline.read_object(args.integration_manifest)
    if manifest.get("schema") != "xar.g2.offline.central-native-build.v1":
        raise ValueError("requires the new G2 central native build manifest")
    source_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, check=True,
        capture_output=True, text=True).stdout.strip()
    if source_head != manifest["source_head"]:
        raise ValueError("candidate source HEAD differs from the frozen native build")
    config = offline.read_object(args.config)
    required_on = config["native_candidate_required_on"]
    required_off = config["native_candidate_required_off"]
    builds = manifest["build"]
    for label in ("selected_private", "shipping"):
        bundle = builds[label]
        for flag in required_on + required_off:
            expected = "ON" if label == "selected_private" and flag in required_on else "OFF"
            if bundle["flags"].get(flag) != expected:
                raise ValueError(f"{label} does not provide the configured {flag}={expected}")
        for name in ("dll", "injector"):
            pin = bundle[name]
            path = Path(pin["path"])
            if path.stat().st_size != pin["bytes"] or offline.digest(path) != pin["sha256"].lower():
                raise ValueError(f"{label} {name} differs from the frozen build pin")
    return {"manifest": manifest, "manifest_sha256": manifest_sha,
            "source_head": source_head, "builds": builds, "config": config}


def runner_args(args: argparse.Namespace, bundle: dict[str, Any], lane: str,
                output: Path) -> argparse.Namespace:
    identity_path = args.canonical_seed_root / "SEED-IDENTITY.json"
    identity = offline.read_object(identity_path)
    state = args.state_dir if lane == "rogue" else args.state_dir.parent / "ordinary-plan-only-state"
    sample = args.canonical_seed_root if lane == "rogue" else args.ordinary_sample_dir
    argv = ["--config", str(args.config), "--lane", lane,
            "--source-repo", str(REPO), "--python", str(args.python),
            "--game-dir", str(args.game_dir), "--state-dir", str(state),
            "--dll", bundle["dll"]["path"], "--injector", bundle["injector"]["path"],
            "--dll-sha256", bundle["dll"]["sha256"],
            "--injector-sha256", bundle["injector"]["sha256"],
            "--pipe", identity["pipe"], "--sample-dir", str(sample),
            "--output-dir", str(output), "--live-run-state-root", str(args.live_run_state_root)]
    if lane == "rogue":
        argv += ["--seed-identity", str(identity_path)]
    return offline.parser().parse_args(argv)


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    inputs = load_build_inputs(args)
    output = args.output_dir.resolve()
    if args.prepare_profile_files and args.state_dir.exists():
        raise ValueError("candidate requires a new nonexistent state; no existing profile refresh")
    output.mkdir(parents=True, exist_ok=False)
    plans: dict[str, Any] = {}
    for lane, bundle_name in (("rogue", "selected_private"), ("ordinary", "shipping")):
        lane_output = output / ("rogue" if lane == "rogue" else "ordinary-plan-only")
        lane_output.mkdir()
        parsed = runner_args(args, inputs["builds"][bundle_name], lane, lane_output)
        manifest, plan = offline.plan(parsed)
        plan["frozen_native_build"] = {
            "integration_manifest": str(args.integration_manifest.resolve()),
            "integration_manifest_sha256": inputs["manifest_sha256"],
            "source_head": inputs["source_head"],
            "bundle": bundle_name, "flags": inputs["builds"][bundle_name]["flags"],
            "binary_files_read_or_verified": True,
        }
        if lane == "rogue" and args.prepare_profile_files:
            plan["profile_file_preparation"] = offline.prepare_profile_files(parsed, manifest)
            plan.update({"status": "static-ready-profile-files",
                         "game_installation_files_read": True, "actual_profile_prepared": True})
        write_json(lane_output / "operator-manifest.json", manifest)
        write_json(lane_output / "OFFLINE-RUNNER-PLAN.json", plan)
        plans[lane] = plan
    pair = None
    environment = None
    if args.prepare_profile_files:
        import stage_nonwar_12002_pair_files as staging
        identity = offline.read_object(args.canonical_seed_root / "SEED-IDENTITY.json")
        pair_args = staging.parser().parse_args([
            "--source-save", str(args.canonical_seed_root / "profile/save games/xar_checkpoint.ck3"),
            "--source-driver", str(args.canonical_seed_root / "native-session/driver-state.json"),
            "--target-state", str(args.state_dir), "--into-prepared-profile",
            "--game-dir", str(args.game_dir), "--pipe", identity["pipe"],
            "--expected-save-sha256", identity["checkpoint_sha256"],
            "--expected-driver-sha256", identity["driver_state_sha256"],
            "--expected-character-id", str(identity["episode_character_id"]),
            "--expected-episode-run-id", identity["episode_run_id"],
            "--expected-date-raw", str(identity["date_raw"]),
            "--expected-history-index", str(identity["history_index"]),
        ])
        pair = staging.stage(pair_args)
        environment = offline.read_object(args.state_dir / "profile/xar-autoplayer-environment.json")
    next_commands = plans["rogue"]["commands"]
    if args.prepare_profile_files:
        next_commands = [row for row in next_commands if row["id"] != "official-prepare-and-pair"]
    write_json(output / "NEXT-LIVE-PHASES.json", {
        "schema": "xar.ck3.g2-candidate-next-live-phases/v1", "executed": False,
        "profile_and_pair_files_prepared": args.prepare_profile_files,
        "commands": next_commands,
        "next_episode_requires_verified_terminal_settlement": True,
        "ordinary_lane_is_plan_only": True,
    })
    identity = offline.read_object(args.canonical_seed_root / "SEED-IDENTITY.json")
    write_json(output / "MCP-READONLY-NEXT-PLAN.json", {
        "schema": "xar.ck3.g2-candidate-mcp-read-plan/v1", "executed": False,
        "requires_real_restored_candidate_and_paused_frame": True,
        "formal_action_permits_enabled": False,
        "argv": [str(args.python.absolute()), "-B", str(REPO / "ck3_autonomous_player/mcp_server.py"),
                 "--driver", "native-headless", "--transport", "stdio",
                 "--state-dir", str(args.state_dir.absolute()), "--pipe-name", identity["pipe"],
                 "--environment-manifest", str(args.state_dir.absolute() / "profile/xar-autoplayer-environment.json"),
                 "--succession-lifecycle", "rogue_one_life", *inputs["config"]["private_mcp_read_queries"]],
        "scope": "MCP stdio query permits only; these flags are not lifetime/native-auto-run arguments",
    })
    file_hashes = {str(path): offline.digest(path) for path in output.rglob("*.json")}
    if args.prepare_profile_files:
        for name in ("profile/xar-autoplayer-environment.json", "SEED-IDENTITY.json",
                     "PAIR-FILES-QUALIFICATION.json"):
            path = args.state_dir / name
            file_hashes[str(path.absolute())] = offline.digest(path)
    receipt = {
        "schema": "xar.ck3.g2-offline-candidate-profile-pair/v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_STATIC_PROFILE_AND_FILE_PAIR" if pair else "PASS_FROZEN_BUILD_COMMAND_PLAN",
        "readiness": "static-ready", "source_repo": str(REPO),
        "source_commit": inputs["source_head"],
        "integration_manifest": str(args.integration_manifest.resolve()),
        "integration_manifest_sha256": inputs["manifest_sha256"],
        "config": str(args.config.resolve()), "config_sha256": offline.digest(args.config),
        "selected_private_binary": {name: inputs["builds"]["selected_private"][name]
                                     for name in ("dll", "injector")},
        "selected_private_flags": inputs["builds"]["selected_private"]["flags"],
        "shipping_plan_binary": {name: inputs["builds"]["shipping"][name]
                                 for name in ("dll", "injector")},
        "formal_consumer_trials_enabled": inputs["config"]["private_formal_trials_enabled"],
        "profile_state": str(args.state_dir.absolute()),
        "profile_file_preparation": plans["rogue"].get("profile_file_preparation"),
        "environment": ({"environment_sha256": environment["environment_sha256"],
                         "agent_runtime_sha256": environment["agent_runtime"]["sha256"],
                         "production_tree_sha256": environment["mod"]["production_tree_sha256"],
                         "production_file_count": environment["mod"]["production_file_count"]}
                        if environment else None),
        "canonical_seed_root": str(args.canonical_seed_root.resolve()),
        "pair_receipt": pair,
        "ordinary_state_prepared": False, "historical_robert_continuation": False,
        "robert_durable_days_increment": 0, "g2_completed_increment": 0,
        "actual_ck3_process_pipe_desktop_steam_or_allocator_access": False,
        "official_zero_process_preflight_completed": False,
        "real_game_cold_restore_completed": False,
        "original_P_Robert_current_userdir_or_previous_profiles_written": False,
        "remaining_live": ["official exact zero-process preflight", "new PID cold restore/readiness",
                           "representative paused new-domain queries and actual typed outcome/next-turn/checkpoint",
                           "full lifetime/next; ordinary G2 only from actual durable lineage"],
        "file_hashes": file_hashes,
    }
    write_json(output / "FINAL-G2-FILE-PROFILE-PAIR-RECEIPT.json", receipt)
    return receipt


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config", type=Path, default=CONFIG)
    result.add_argument("--python", type=Path, default=Path(sys.executable))
    for name in ("integration-manifest", "game-dir", "state-dir", "canonical-seed-root",
                 "output-dir", "live-run-state-root"):
        result.add_argument(f"--{name}", type=Path, required=True)
    result.add_argument("--integration-manifest-sha256", required=True)
    result.add_argument("--ordinary-sample-dir", type=Path,
                        help="metadata-only ordinary input; must be a separately qualified ordinary seed before real preparation")
    result.add_argument("--prepare-profile-files", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.ordinary_sample_dir is None:
        args.ordinary_sample_dir = args.output_dir / "requires-qualified-ordinary-sample"
    try:
        receipt = prepare(args)
        print(json.dumps({"ok": True, "status": receipt["status"], "output": str(args.output_dir)}))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, ImportError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
