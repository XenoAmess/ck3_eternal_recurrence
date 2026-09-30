"""Freeze an explicitly supplied H3937 job for the local stdio operator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from xar_autoplayer.h3937_run_config import apply_run_config


def freeze_profile(config: Path, output: Path, operator_state: Path) -> dict[str, object]:
    """Write a create-only profile; never allocate IDs, create GO or start a job."""
    if not operator_state.is_absolute():
        raise ValueError("operator state directory must be an explicit absolute path")
    runner = ModuleType("h3937_profile_inputs")
    config_identity = apply_run_config(runner, config)
    entry = ROOT / "h3937_cold_observer_once.py"
    required = {
        runner.FROZEN_PYTHON, entry, runner.RUN_CONFIG_PATH, runner.DLL, runner.INJECTOR,
        ROOT / "agent.py", ROOT.parent / "tools/process_watchdog.py",
        ROOT.parent / "tools/build_release.py",
        ROOT.parent / "tools/codex_task_bus.py",
        ROOT.parent / "promo/ck3_native_war_ai/integration/screen_bus_lease.py",
        *ROOT.joinpath("src/xar_autoplayer").rglob("*.py"),
    }
    pins = []
    for path in sorted(required, key=str):
        data = path.read_bytes()
        pins.append({"path": str(path.resolve()), "kind": "file", "size": len(data),
                     "sha256": hashlib.sha256(data).hexdigest().upper()})
    for path, expected in (
        (runner.DLL, "3438E8725AA06839CA1F2DFAF6D6CC98D41A4F33C02AC0702AC8D48AD241531B"),
        (runner.INJECTOR, "ECBC1B3B24E8A9BF1F85E9CBE195E4A5B8D3E928DB0FC8124ABF4D6D95A4B0D3"),
    ):
        if next(item["sha256"] for item in pins if Path(item["path"]) == path.resolve()) != expected:
            raise ValueError("H3937 source-verified native pair differs")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    profile = {
        "schema_version": 1,
        "target": {"id": "h3937-local-" + runner.ROUND,
                   "display_name": "H3937 same-machine read-only operator",
                   "expected": {"token_user": "1", "desktop": "WinSta0\\Default",
                                "machine": "DESKTOP-3FEVHD2"}},
        "endpoint": {"transport": "stdio", "host": "127.0.0.1", "port": 8766},
        "state_directory": str(operator_state),
        "jobs": {"h3937-six-readonly": {
            "command": [str(runner.FROZEN_PYTHON), "-B", str(entry), "--config", str(runner.RUN_CONFIG_PATH)],
            "working_directory": str(ROOT.parent),
            "exclusive_process_names": ["ck3.exe", "obs64.exe", "xar_ck3_bridge_injector.exe"],
            "required_paths": pins,
            "absent_paths": [str(runner.OUTPUT), str(runner.STATE / "control/unsafe-cleanup.json")],
            "controls": {},
        }},
    }
    # Preserve the emitted bytes even if the existing profile validator rejects them.
    from xar_autoplayer.operator_mcp import load_operator_profile
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    data = (json.dumps(profile, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with output.open("xb") as stream:
        stream.write(data)
    load_operator_profile(output)
    return {"profile": str(output), "sha256": hashlib.sha256(data).hexdigest().upper(),
            "source_head": head, "config": config_identity,
            "required_files": len(pins), "live_id_allocated": False, "go_created": False,
            "job_started": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--operator-state-dir", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(freeze_profile(args.config, args.output, args.operator_state_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
