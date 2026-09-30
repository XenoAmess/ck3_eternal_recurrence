#!/usr/bin/env python3
"""Render reviewable launch commands from disk; never launch or prepare a profile."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import ck3_installation


ROOT = Path(__file__).resolve().parent.parent
MIGRATION_ROOT = ROOT / "artifacts/migrations/2026-09-30/post-update-1.20.0.2"
DEFAULT_CANDIDATE = (
    ROOT / "ck3_autonomous_player/configs/ck3-1.20.0.2-native-candidate.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def render_plan(
    candidate_path: Path,
    game_dir: Path | None = None,
    bridge_build_dir: Path | None = None,
    state_dir: Path | None = None,
) -> dict[str, object]:
    candidate = json.loads(candidate_path.read_text(encoding="utf-8-sig"))
    game = candidate["game"]
    game_dir = (game_dir or Path(game["installation_root"])).resolve()
    executable = game_dir / "binaries/ck3.exe"
    version = ck3_installation.installed_game_version(executable)
    executable_sha256 = sha256_file(executable)
    if version != game["version"] or executable_sha256 != game["executable_sha256"]:
        raise ValueError(
            "candidate differs from the installed build: "
            f"version={version}, sha256={executable_sha256}"
        )
    if state_dir is None:
        local = os.environ.get("LOCALAPPDATA")
        base = Path(local) if local else Path.home() / "AppData/Local"
        state_dir = base / candidate["state_directory_name"]
    state_dir = state_dir.expanduser().resolve()
    bridge_build_dir = (
        bridge_build_dir or MIGRATION_ROOT / "build-migration-msvc"
    ).resolve()
    dll = bridge_build_dir / "xar_ck3_bridge.dll"
    injector = bridge_build_dir / "xar_ck3_bridge_injector.exe"
    python = ROOT / "tools/.venv/Scripts/python.exe"
    agent = ROOT / "ck3_autonomous_player/agent.py"
    base_command = [
        str(python), str(agent), "--state-dir", str(state_dir),
        "--game-dir", str(game_dir),
    ]
    native_command = base_command + [
        "--bridge-mode", candidate["bridge_mode"],
        "--bridge-pipe", candidate["bridge_pipe"],
        "--bridge-dll", str(dll), "--bridge-injector", str(injector),
    ]
    commands = [
        {
            "phase": "prepare-isolated-profile",
            "argv": base_command + ["prepare-profile"],
            "requires": "Separate live-test window; writes only the chosen new state.",
        },
        {
            "phase": "verify-isolated-profile",
            "argv": base_command + ["verify-profile"],
            "requires": "A newly prepared 1.20.0.2 profile.",
        },
        {
            "phase": "native-owning-thread-paused-snapshot-and-command-test",
            "argv": native_command + ["native-session", "--timeout", "21600"],
            "requires": (
                "Integrated candidate DLL and injector; user has finished playing; "
                "MCP uses the candidate pipe; a paused game is created in this profile."
            ),
        },
        {
            "phase": "single-turn-native-loop",
            "argv": native_command + [
                "native-auto-run", "--turns", "1", "--timeout", "900",
                "--readiness-timeout", "300", "--cold-start-checkpoint",
            ],
            "requires": (
                "A 1.20.0.2 xar_checkpoint created in the isolated profile; "
                "owning-thread/snapshot/action validation has passed."
            ),
        },
    ]
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "preparation_mode": "disk-only-command-plan",
        "live_validated": False,
        "process_accessed": False,
        "profile_prepared": False,
        "candidate_config": str(candidate_path.resolve()),
        "candidate_config_sha256": sha256_file(candidate_path),
        "game": {
            "version": version,
            "installation_root": str(game_dir),
            "executable": str(executable),
            "executable_sha256": executable_sha256,
            "vanilla_rules": str(game_dir / "game/common/game_rules/00_game_rules.txt"),
        },
        "state_directory": str(state_dir),
        "state_directory_created": False,
        "bridge": {
            "mode": candidate["bridge_mode"],
            "pipe": candidate["bridge_pipe"],
            "dll": str(dll),
            "dll_present_on_disk": dll.is_file(),
            "injector": str(injector),
            "injector_present_on_disk": injector.is_file(),
        },
        "commands": commands,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--bridge-build-dir", type=Path)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument(
        "--output", type=Path, default=MIGRATION_ROOT / "offline-launch-plan.json"
    )
    args = parser.parse_args()
    plan = render_plan(
        args.candidate, args.game_dir, args.bridge_build_dir, args.state_dir
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig"
    )
    print(json.dumps({
        "output": str(args.output.resolve()),
        "game_version": plan["game"]["version"],
        "live_validated": False,
        "profile_prepared": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
