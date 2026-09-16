#!/usr/bin/env python3
"""Bounded paused CK3 scope check for a frozen production preview seed.

This operator check uses the existing controlled campaign-root acceptance path.
It never chooses or submits a gameplay action, so GREEN here is only scope
eligibility for a separate formal ``native-auto-run`` run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


ROGUE_ONE_LIFE = "rogue_one_life"
ORDINARY_CAMPAIGN_SUCCESSION = "ordinary_campaign_succession"
LEGACY_LIFECYCLE_CONTRACT = {
    "xar_enabled": "xar_on",
    "succession_lifecycle": ROGUE_ONE_LIFE,
    "ordinary_campaign_no_pact": False,
}
ORDINARY_LIFECYCLE_CONTRACT = {
    "xar_enabled": "xar_off",
    "succession_lifecycle": ORDINARY_CAMPAIGN_SUCCESSION,
    "ordinary_campaign_no_pact": True,
}


def _lifecycle_contract(manifest: dict[str, Any]) -> dict[str, Any]:
    fields = tuple(LEGACY_LIFECYCLE_CONTRACT)
    present = [field for field in fields if field in manifest]
    if not present:
        return {**LEGACY_LIFECYCLE_CONTRACT, "source": "legacy-default"}
    if len(present) != len(fields):
        missing = [field for field in fields if field not in manifest]
        raise ValueError(
            "preview lifecycle manifest is partial; lacks: "
            + ", ".join(missing)
        )
    candidate = {field: manifest[field] for field in fields}
    if candidate not in (LEGACY_LIFECYCLE_CONTRACT, ORDINARY_LIFECYCLE_CONTRACT):
        raise ValueError("preview lifecycle manifest fields are inconsistent")
    return {**candidate, "source": "manifest"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pin(path: Path, expected: str, label: str) -> None:
    actual = _sha256(path)
    if actual.lower() != expected.lower():
        raise RuntimeError(f"{label} SHA-256 differs: {actual} != {expected}")


def _read_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict):
        raise ValueError("preview manifest must be an object")
    required = (
        "source_commit", "source_repo", "game_dir", "game_exe_sha256",
        "state_dir", "source_save", "checkpoint_sha256",
        "driver_state_sha256", "episode_character_id", "episode_run_id",
        "date_raw", "pipe", "dll", "dll_sha256", "injector",
        "injector_sha256", "environment_sha256", "timeout_seconds",
        "session_ceiling_seconds", "readiness_timeout_seconds",
        "supported_government",
    )
    missing = [field for field in required if field not in manifest]
    if missing:
        raise ValueError(f"preview manifest lacks: {', '.join(missing)}")
    if manifest["supported_government"] != "feudal_government":
        raise ValueError("this preview operator check supports feudal_government")
    _lifecycle_contract(manifest)
    if not (
        isinstance(manifest["timeout_seconds"], (int, float))
        and 0 < manifest["timeout_seconds"]
        and isinstance(manifest["readiness_timeout_seconds"], (int, float))
        and 0 < manifest["readiness_timeout_seconds"] <= manifest["timeout_seconds"]
        and isinstance(manifest["session_ceiling_seconds"], (int, float))
        and manifest["timeout_seconds"] + 90 <= manifest["session_ceiling_seconds"]
    ):
        raise ValueError("stage/readiness/session bounds conflict with native-session +90s grace")
    return manifest


def _backend(repo: Path) -> dict[str, Any]:
    sys.path.insert(0, str(repo / "ck3_autonomous_player" / "native_bridge" / "research"))
    sys.path.insert(0, str(repo / "ck3_autonomous_player" / "src"))
    import run_campaign_root_context_live_acceptance as controlled  # noqa: PLC0415
    from xar_autoplayer.bridge.native_driver import (  # noqa: PLC0415
        load_native_driver_state_for_resume,
    )
    from xar_autoplayer.bridge.succession_transition_contract import (  # noqa: PLC0415
        bind_succession_lifecycle_from_environment_v1,
        legacy_rogue_one_life_binding_v1,
    )
    from xar_autoplayer.environment import (  # noqa: PLC0415
        ck3_process_inventory,
        make_spec,
        verify_profile,
    )
    from xar_autoplayer.native_session import (  # noqa: PLC0415
        validate_cold_start_checkpoint_for_pipe,
    )
    from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: PLC0415

    return locals()


def _preflight(manifest: dict[str, Any], backend: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    repo = Path(manifest["source_repo"]).resolve()
    commit = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != manifest["source_commit"]:
        raise RuntimeError("frozen agent source commit changed")
    if subprocess.check_output(
        ["git", "-C", str(repo), "status", "--porcelain"], text=True
    ).strip():
        raise RuntimeError("frozen agent source is dirty")
    state = Path(manifest["state_dir"]).resolve()
    spec = backend["make_spec"](state, Path(manifest["game_dir"]).resolve())
    contract = _lifecycle_contract(manifest)
    profile = backend["verify_profile"](
        spec, xar_enabled=contract["xar_enabled"]
    )
    if profile["environment_sha256"].lower() != manifest["environment_sha256"].lower():
        raise RuntimeError("production-only profile differs from freeze")
    lifecycle_binding = backend["bind_succession_lifecycle_from_environment_v1"](
        profile,
        lifecycle=contract["succession_lifecycle"],
        ordinary_campaign_no_pact=contract["ordinary_campaign_no_pact"],
    )
    _pin(spec.game_exe, manifest["game_exe_sha256"], "CK3 EXE")
    _pin(Path(manifest["source_save"]), manifest["checkpoint_sha256"], "immutable source save")
    _pin(
        state / "profile" / "save games" / "xar_checkpoint.ck3",
        manifest["checkpoint_sha256"], "prepared checkpoint",
    )
    _pin(
        state / "native-session" / "driver-state.json",
        manifest["driver_state_sha256"], "prepared driver state",
    )
    _pin(Path(manifest["dll"]), manifest["dll_sha256"], "Release DLL")
    _pin(Path(manifest["injector"]), manifest["injector_sha256"], "Release injector")
    checkpoint = backend["validate_cold_start_checkpoint_for_pipe"](spec, manifest["pipe"])
    driver_state = backend["load_native_driver_state_for_resume"](
        state / "native-session" / "driver-state.json", manifest["pipe"]
    )
    legacy_binding = backend["legacy_rogue_one_life_binding_v1"]()
    driver_lifecycle = (
        driver_state.get("succession_lifecycle")
        if isinstance(driver_state, dict)
        else None
    )
    checkpoint_lifecycle = checkpoint.get("succession_lifecycle")
    if (
        driver_lifecycle != lifecycle_binding
        and not (
            contract["succession_lifecycle"] == ROGUE_ONE_LIFE
            and driver_lifecycle == legacy_binding
        )
    ):
        raise RuntimeError("driver lifecycle differs from preview manifest")
    if (
        contract["succession_lifecycle"] == ORDINARY_CAMPAIGN_SUCCESSION
        and checkpoint_lifecycle != lifecycle_binding
    ):
        raise RuntimeError("ordinary checkpoint lifecycle differs from preview manifest")
    if (
        contract["succession_lifecycle"] == ROGUE_ONE_LIFE
        and checkpoint_lifecycle is not None
        and checkpoint_lifecycle not in (lifecycle_binding, legacy_binding)
    ):
        raise RuntimeError("legacy checkpoint lifecycle differs from preview manifest")
    if not (
        isinstance(driver_state, dict)
        and driver_state.get("episode_character_id") == manifest["episode_character_id"]
        and driver_state.get("episode_run_id") == manifest["episode_run_id"]
        and checkpoint.get("saved_date_raw") == manifest["date_raw"]
    ):
        raise RuntimeError("cold checkpoint/driver episode binding differs")
    inventory = backend["ck3_process_inventory"]()
    if inventory.get("processes"):
        raise RuntimeError("CK3 already runs on this host")
    return spec, {
        "status": "ready-no-launch", "source_commit": commit,
        "environment_sha256": profile["environment_sha256"],
        "lifecycle": contract,
        "succession_lifecycle_binding": lifecycle_binding,
        "checkpoint": checkpoint,
        "driver_state_sha256": manifest["driver_state_sha256"],
        "dll_sha256": manifest["dll_sha256"],
        "injector_sha256": manifest["injector_sha256"],
        "ck3_inventory": inventory, "ck3_launched": False,
    }


def _qualify(
    manifest: dict[str, Any], stage: dict[str, Any], backend: dict[str, Any]
) -> dict[str, bool]:
    sequence = stage.get("sequence") if isinstance(stage, dict) else None
    readiness = stage.get("readiness") if isinstance(stage, dict) else None
    root = (
        sequence.get("first_query", {}).get("campaign_root_context")
        if isinstance(sequence, dict) else None
    )
    active = readiness.get("active_context") if isinstance(readiness, dict) else None
    government = root.get("government") if isinstance(root, dict) else None
    rule_tokens = (
        root.get("selected_game_rule_tokens") if isinstance(root, dict) else None
    )
    contract = _lifecycle_contract(manifest)
    selected_rules_match = True
    if contract["succession_lifecycle"] == ORDINARY_CAMPAIGN_SUCCESSION:
        selected_rules_match = (
            isinstance(rule_tokens, list)
            and all(isinstance(value, str) for value in rule_tokens)
            and "xar_off" in rule_tokens
            and "xar_on" not in rule_tokens
        )
    state = Path(manifest["state_dir"])
    inventory = backend["ck3_process_inventory"]()
    return {
        "same_version_managed_queries": stage.get("ok") is True,
        "native_player_expected": isinstance(readiness, dict)
        and readiness.get("played_character_id") == manifest["episode_character_id"],
        "saved_date_expected": isinstance(readiness, dict)
        and readiness.get("date_raw") == manifest["date_raw"],
        "government_exact_feudal": isinstance(government, dict)
        and government.get("key") == manifest["supported_government"],
        "selected_rules_match_lifecycle": selected_rules_match,
        "no_war_event_pending_army": isinstance(active, dict)
        and active.get("war_ids") == [] and active.get("army_ids") == []
        and active.get("active_event") is None
        and active.get("pending_character_interaction") is None,
        "source_save_unchanged": _sha256(Path(manifest["source_save"])).lower()
        == manifest["checkpoint_sha256"].lower(),
        "prepared_checkpoint_unchanged": _sha256(
            state / "profile" / "save games" / "xar_checkpoint.ck3"
        ).lower() == manifest["checkpoint_sha256"].lower(),
        "process_recycled": inventory.get("processes") == [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"output exists; one attempt only: {output}")
    started = time.monotonic()
    report: dict[str, Any] = {
        "schema": "xar.ck3.g2_preview_eligibility_report_v1",
        "status": "RED", "qualification": "read_only_eligibility_only",
        "ck3_launch_attempted": False, "ui_inputs": 0, "gameplay_actions": 0,
        "manual_date_advance": False,
        "manifest": str(args.manifest.resolve()),
    }
    try:
        manifest = _read_manifest(args.manifest)
        report["lifecycle"] = _lifecycle_contract(manifest)
        report["bounds"] = {
            "stage_timeout_seconds": manifest["timeout_seconds"],
            "native_session_ceiling_seconds": manifest["session_ceiling_seconds"],
            "readiness_seconds": manifest["readiness_timeout_seconds"],
            "campaign_root_queries": 2, "save_checkpoint_commands": 0,
        }
        backend = _backend(Path(manifest["source_repo"]).resolve())
        spec, pre = _preflight(manifest, backend)
        report["preflight"] = pre
        if args.preflight_only:
            report["status"] = "READY_NO_LAUNCH"
            report["ok"] = True
        else:
            config = backend["NativeBridgeLaunchConfig"](
                mode="native-headless", pipe_name=manifest["pipe"],
                dll_path=Path(manifest["dll"]),
                injector_path=Path(manifest["injector"]),
            )
            report["ck3_launch_attempted"] = True
            stage = backend["controlled"]._run_live_stage(
                stage="preview-feudal-eligibility", spec=spec, config=config,
                cold_start_checkpoint=True, save_checkpoint=False,
                timeout=float(manifest["timeout_seconds"]),
                readiness_timeout=float(manifest["readiness_timeout_seconds"]),
                prepared_xar_enabled=report["lifecycle"]["xar_enabled"],
                succession_lifecycle_binding=pre[
                    "succession_lifecycle_binding"
                ],
            )
            report["stage"] = stage
            checks = _qualify(manifest, stage, backend)
            report["checks"] = checks
            report["postflight_ck3_inventory"] = backend["ck3_process_inventory"]()
            report["status"] = "GREEN_READ_ONLY" if all(checks.values()) else "RED"
            report["ok"] = all(checks.values())
    except BaseException as error:
        report["error"] = f"{type(error).__name__}: {error}"
        report["status"] = "RED"
        report["ok"] = False
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], "ok": report["ok"],
                      "report": str(output / "report.json")}))
    return 0 if report["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
