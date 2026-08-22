from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    EXPECTED_MOD_NAME,
    OUTER_DESCRIPTOR_REF,
    _contract_digest,
    EnvironmentSpec,
    sha256_file,
    snapshot_digest,
    tree_snapshot,
    write_json_atomic,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.control.executor import (  # noqa: E402
    VisibleUiDriver,
    _IssuedControl,
)
from xar_autoplayer.menu_smoke import (  # noqa: E402
    GREEN_EVENT_ORDER,
    LEGACY_NORMAL_QUALIFICATION_VALIDATOR,
    MENU_ACCEPTANCE_CLAIM,
    MENU_KIND,
    NORMAL_V2_QUALIFICATION_VALIDATOR,
    REPLAY_TRUST_MODEL,
    ACTION_RECEIPT_SCHEMA,
    ACTION_RECEIPT_SCHEMA_AGENT_RUNTIME_PATH,
    OBSERVATION_SCHEMA,
    OBSERVATION_SCHEMA_AGENT_RUNTIME_PATH,
    UI_CONTRACT_AGENT_RUNTIME_PATH,
    UI_CONTRACT_ARCHIVE,
    UI_CONTRACT_REPOSITORY_RELATIVE,
    _archive_ui_contract,
    _archive_menu_qualification,
    _require_menu_qualification,
    _validate_archived_menu_qualification,
    _validate_normal_qualification,
    _validate_archived_environment,
    _validate_json_schema,
    _validate_preseal_candidate,
    _validated_menu_event_rows,
    _artifact_manifest,
    _menu_smoke_locked,
    _memory_image_sha256,
    _replay_visible_frame,
    _report_body_sha256,
    _run_menu_scenario,
    _verified_artifact_manifest,
    _write_final_report_transactionally,
    validate_menu_smoke_report,
)
from xar_autoplayer.runtime import (  # noqa: E402
    analyze_engine_log_bytes,
    append_event,
    validate_event_chain,
    write_gzip_json_atomic,
)
from xar_autoplayer.vision.classifier import load_ui_contract  # noqa: E402
from xar_autoplayer.vision.model import (  # noqa: E402
    Observation,
    OcrSpan,
    StableObservation,
    VisibleAnchor,
    VisibleControl,
)


def stable_observation(screen: str, *, controls: bool, sequence: int) -> dict[str, object]:
    first_id = f"{sequence:032x}"
    second_id = f"{sequence + 1:032x}"
    visible_controls = (
        [
            {
                "control_id": "main_menu.new_game",
                "label": "新游戏",
                "control_token": "c" * 64,
                "bbox": [560, 543, 640, 571],
                "center": [600, 557],
            }
        ]
        if controls
        else []
    )
    return {
        "format_version": 2,
        "observation_id": second_id,
        "frame_id": f"{sequence + 101:032x}",
        "captured_at": "2026-08-22T00:00:01+00:00",
        "screen": screen,
        "image": {"ref": "frame:test", "sha256": "a" * 64, "width": 2560, "height": 1440},
        "ocr": [],
        "visible_anchors": [],
        "visible_controls": visible_controls,
        "visible_facts": {"screen": screen, "anchors": []},
        "confidence": 0.9,
        "unknown_reasons": [],
        "policy_boundary": "player-visible pixels and OCR only",
        "stability": {
            "stable_frames": 2,
            "expected_screen": screen,
            "frames": [
                {
                    "observation_id": first_id,
                    "frame_id": f"{sequence + 100:032x}",
                    "captured_at": "2026-08-22T00:00:00+00:00",
                    "capture_sequence": sequence,
                    "captured_monotonic": 10.0,
                    "screenshot_sha256": "b" * 64,
                },
                {
                    "observation_id": second_id,
                    "frame_id": f"{sequence + 101:032x}",
                    "captured_at": "2026-08-22T00:00:01+00:00",
                    "capture_sequence": sequence + 1,
                    "captured_monotonic": 10.5,
                    "screenshot_sha256": "c" * 64,
                },
            ],
            "monotonic_delta": 0.5,
        },
    }


def foreground_attestation(pid: int = 42, hwnd: int = 84) -> dict[str, object]:
    return {
        "format_version": 1,
        "target_pid": pid,
        "target_hwnd": hwnd,
        "target_thread_id": 100,
        "caller_thread_id": 200,
        "foreground_hwnd_before": hwnd,
        "foreground_thread_id_before": 100,
        "foreground_pid_before": pid,
        "last_input_tick_before": 300,
        "synthetic_input": False,
        "mode": "already_foreground",
        "attached_fallback": False,
        "detach_succeeded": None,
        "foreground_hwnd_after": hwnd,
        "foreground_thread_id_after": 100,
        "foreground_pid_after": pid,
        "last_input_tick_after": 300,
        "observed_last_input_tick_unchanged": True,
    }


def navigation_payload() -> dict[str, object]:
    start = stable_observation("main_menu", controls=True, sequence=1)
    after = stable_observation("bookmark_lobby", controls=False, sequence=20)
    action = {
        "format_version": 2,
        "action_id": "d" * 32,
        "planned_at": "2026-08-22T00:00:01+00:00",
        "kind": "click_visible_control",
        "control_id": "main_menu.new_game",
        "control_token_sha256": "e" * 64,
        "before_observation_id": start["observation_id"],
        "expected_post_screen": "bookmark_lobby",
        "status": "confirmed",
        "input_may_have_occurred": True,
        "risk": "reversible",
        "policy_boundary": "no caller-supplied coordinates or postconditions",
        "fresh_observation_id": "f" * 32,
        "hover_observation_id": "1" * 32,
        "input_attempted_at": "2026-08-22T00:00:02+00:00",
        "result_observation_id": after["observation_id"],
        "finished_at": "2026-08-22T00:00:03+00:00",
        "contract_sha256": "9" * 64,
        "receipt_artifact": "artifacts/00001-action.json",
        "control_token_sha256": "e" * 64,
        "binding": {"process": {"pid": 42}, "window": {"hwnd": 84}},
        "before_stable_observation": {
            "frames": start["stability"]["frames"],
        },
        "after_stable_observation": {
            "frames": after["stability"]["frames"],
        },
        "target": {
            "issued": {"bbox": [1, 2, 3, 4]},
            "fresh": {"bbox": [1, 2, 3, 4]},
            "hover": {"patch_sha256": "8" * 64},
            "final_patch_sha256": "8" * 64,
        },
        "send_input": {"requested": 2, "accepted": 2, "last_error": 0},
        "durable_events": {},
    }
    return {
        "claim": "visible_main_menu_to_bookmark_lobby_only",
        "foreground_activation": foreground_attestation(),
        "start_observation": start,
        "transition": {"action": action, "observation": after},
        "registered_capabilities": ["main_menu.new_game"],
        "forbidden_capabilities": ["bookmark_lobby.start_game"],
        "start_game_capability_registered": False,
    }


def load_attestation() -> dict[str, object]:
    return {
        "enabled_mods": [{"name": "琉焰卿的永恒轮回", "descriptor": "mod/xar_autoplayer.mod"}],
        "isolated_mod_mounts": ["X:/state/profile/mod-content/xar-production"],
        "runtime_dlc_mounts": [],
        "unclassified_mounts": [],
        "session_marker_count": 1,
        "debug_log": {"path": "debug.log"},
        "post_exit_revalidated": True,
        "post_exit_debug_log": {"path": "debug.log"},
    }


def build_green_report(run_dir: Path) -> dict[str, object]:
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True)
    for relative in (
        "environment.json",
        "production.manifest.json",
        "protected-before.json.gz",
        "protected-after.json.gz",
        UI_CONTRACT_ARCHIVE,
        "artifacts/supervisor-load-attestation.json",
    ):
        path = run_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.encode("utf-8"))
    navigation = navigation_payload()
    events = run_dir / "events.jsonl"
    action_id = navigation["transition"]["action"]["action_id"]
    action = navigation["transition"]["action"]
    append_event(
        events,
        {
            "kind": "smoke_started",
            "probe": "main_menu_to_bookmark_lobby",
            "environment_sha256": "a" * 64,
            "protected_storage_sha256": "7" * 64,
            "ui_contract_sha256": action["contract_sha256"],
            "normal_qualification_run_id": "normal-fixture",
            "crash_qualification_run_id": "crash-fixture",
        },
    )
    append_event(events, {"kind": "ck3_launched", "pid": 42})
    append_event(events, {"kind": "single_mod_runtime_attested"})
    append_event(
        events,
        {
            "kind": "foreground_activation_planned",
            "pid": 42,
            "hwnd": 84,
            "operation": "exact_hwnd_foreground_without_synthetic_input",
            "synthetic_input": False,
        },
    )
    append_event(
        events,
        {
            "kind": "foreground_activation_armed",
            "pid": 42,
            "hwnd": 84,
            "operation": "exact_hwnd_foreground_without_synthetic_input",
            "foreground_may_have_changed": True,
            "synthetic_input_may_have_occurred": False,
        },
    )
    append_event(
        events,
        {
            "kind": "foreground_activation_finished",
            "pid": 42,
            "hwnd": 84,
            "status": "confirmed",
            "attestation": navigation["foreground_activation"],
        },
    )
    append_event(
        events,
        {
            "kind": "visible_main_menu_attested",
            "contract_sha256": action["contract_sha256"],
            "observation_id": navigation["start_observation"]["observation_id"],
            "frame_ids": [
                frame["frame_id"]
                for frame in action["before_stable_observation"]["frames"]
            ],
        },
    )
    action["durable_events"]["planned"] = append_event(
        events,
        {
            "kind": "ui_action_planned",
            "action_id": action_id,
            "control_id": "main_menu.new_game",
            "contract_sha256": action["contract_sha256"],
            "receipt_artifact": action["receipt_artifact"],
            "token_sha256": action["control_token_sha256"],
            "before_frame_ids": [
                frame["frame_id"]
                for frame in action["before_stable_observation"]["frames"]
            ],
        },
    )
    action["durable_events"]["armed"] = append_event(
        events,
        {
            "kind": "ui_input_armed",
            "action_id": action_id,
            "control_id": "main_menu.new_game",
            "contract_sha256": action["contract_sha256"],
            "receipt_artifact": action["receipt_artifact"],
            "binding": action["binding"],
            "target": {
                key: action["target"][key] for key in ("issued", "fresh")
            },
            "pointer_input_may_have_occurred": True,
            "button_click_may_have_occurred": True,
        },
    )
    action["durable_events"]["finished"] = append_event(
        events,
        {
            "kind": "ui_action_finished",
            "action_id": action_id,
            "status": "confirmed",
            "receipt_artifact": action["receipt_artifact"],
            "result_frame_ids": [
                frame["frame_id"]
                for frame in action["after_stable_observation"]["frames"]
            ],
            "send_input": action["send_input"],
        },
    )
    append_event(
        events,
        {
            "kind": "bookmark_lobby_attested",
            "contract_sha256": action["contract_sha256"],
            "observation_id": navigation["transition"]["observation"]["observation_id"],
            "frame_ids": [
                frame["frame_id"]
                for frame in action["after_stable_observation"]["frames"]
            ],
        },
    )
    append_event(events, {"kind": "tracked_process_stopped", "pid": 42, "cleanup_proven": True})
    append_event(
        events,
        {
            "kind": "postflight_attested",
            "protected_storage_sha256": "7" * 64,
        },
    )
    write_json_atomic(artifacts / "00001-action.json", action)
    contract_path = run_dir / UI_CONTRACT_ARCHIVE
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run_dir.name,
        "kind": MENU_KIND,
        "acceptance_claim": MENU_ACCEPTANCE_CLAIM,
        "clean_engine_boot_required": False,
        "valid_score_episode": False,
        "growth100_lobby_adoption_proven": False,
        "runtime_write_absence_proven": False,
        "replay_trust_model": dict(REPLAY_TRUST_MODEL),
        "started_at": "2026-08-22T00:00:00+00:00",
        "finished_at": "2026-08-22T00:01:00+00:00",
        "environment_sha256": "a" * 64,
        "run_dir": ".",
        "ui_contract": {
            "agent_runtime_path": UI_CONTRACT_AGENT_RUNTIME_PATH,
            "source_repository_relative": UI_CONTRACT_REPOSITORY_RELATIVE.as_posix(),
            "archive_path": UI_CONTRACT_ARCHIVE,
            "size": contract_path.stat().st_size,
            "sha256": sha256_file(contract_path),
        },
        "qualification": {
            "normal": {"run_id": "normal-fixture"},
            "crash": {"run_id": "crash-fixture"},
        },
        "process": {"pid": 42},
        "navigation_attestation": navigation,
        "load_attestation": load_attestation(),
        "shutdown_attestation": {"cleanup_proven": True, "ok": True},
        "post_shutdown_ck3_inventory": {"processes": []},
        "protected_storage": {
            "post_exit_matches_baseline": True,
            "continuous_quiet_seconds": 5,
            "runtime_write_absence_proven": False,
            "sha256": "7" * 64,
        },
        "production_tree_unchanged": True,
        "engine_diagnostics": {"current_mod_diagnostics": False},
        "finalized": False,
        "ok": False,
    }
    report["artifacts"] = _artifact_manifest(run_dir)
    body = _report_body_sha256(report)
    report["report_body_sha256"] = body
    tail = append_event(
        events,
        {"kind": "smoke_finished", "ok": True, "report_body_sha256": body},
    )
    report["final_event_sha256"] = tail
    report["finalized"] = True
    report["ok"] = True
    chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    write_json_atomic(run_dir / "report.json", report)
    return report


def _qualification_fixture(
    run_dir: Path, environment_sha256: str
) -> dict[str, object]:
    normal_id = "20260821T235900Z-qualification-normal"
    crash_id = "20260822T000100Z-crash-qualification"
    normal_relative = Path("qualification") / "normal" / "runs" / normal_id
    crash_relative = Path("qualification") / "crash" / "runs" / crash_id
    normal_dir = run_dir / normal_relative
    crash_dir = run_dir / crash_relative
    normal_dir.mkdir(parents=True)
    crash_dir.mkdir(parents=True)

    def finalize(directory: Path, report: dict[str, object]) -> None:
        events = directory / "events.jsonl"
        tail = append_event(events, {"kind": "smoke_finished", "ok": True})
        chain = validate_event_chain(events)
        report.update(
            {
                "finalized": True,
                "ok": True,
                "final_event_sha256": tail,
                "event_chain": {
                    "event_count": chain["event_count"],
                    "tail_sha256": chain["tail_sha256"],
                },
            }
        )
        write_json_atomic(directory / "report.json", report)

    normal_finished = "2026-08-22T00:00:00+00:00"
    crash_started = "2026-08-22T00:01:00+00:00"
    finalize(
        normal_dir,
        {
            "format_version": 2,
            "run_id": normal_id,
            "kind": "infrastructure_smoke",
            "acceptance_claim": "isolated_single_mod_visible_main_menu_only",
            "environment_sha256": environment_sha256,
            "valid_score_episode": False,
            "finished_at": normal_finished,
            "load_attestation": {
                "enabled_mods": [
                    {"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}
                ],
                "unclassified_mounts": [],
                "post_exit_revalidated": True,
            },
            "shutdown_attestation": {
                "cleanup_proven": True,
                "tree_gone": True,
                "job_active_processes_final": 0,
                "watchdog_state_after": "absent",
            },
            "post_shutdown_ck3_inventory": {"processes": []},
            "production_tree_unchanged": True,
        },
    )
    finalize(
        crash_dir,
        {
            "run_id": crash_id,
            "kind": "crash_recovery_smoke",
            "environment_sha256": environment_sha256,
            "valid_score_episode": False,
            "started_at": crash_started,
            "crash_attestation": {"cleanup_proven": True},
            "production_tree_unchanged": True,
        },
    )
    return {
        "environment_sha256": environment_sha256,
        "normal": {
            "run_id": normal_id,
            "archive_path": normal_relative.as_posix(),
            "report_sha256": sha256_file(normal_dir / "report.json"),
            "events_sha256": sha256_file(normal_dir / "events.jsonl"),
            "validator": NORMAL_V2_QUALIFICATION_VALIDATOR,
            "prelaunch_validation_passed": True,
        },
        "crash": {
            "run_id": crash_id,
            "archive_path": crash_relative.as_posix(),
            "report_sha256": sha256_file(crash_dir / "report.json"),
            "events_sha256": sha256_file(crash_dir / "events.jsonl"),
            "validator": "validate_crash_report",
            "prelaunch_validation_passed": True,
        },
        "normal_finished_at": normal_finished,
        "crash_started_at": crash_started,
    }


def build_strict_green_report(
    run_dir: Path,
) -> tuple[dict[str, object], dict[int, tuple[object, ...]]]:
    """Create a complete relocatable archive for the public validator."""
    from PIL import Image
    from xar_autoplayer.vision.classifier import load_ui_contract
    from xar_autoplayer.vision.model import OcrSpan
    from xar_autoplayer.vision.ocr import normalize_visible_text

    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True)
    source_contract = ROOT.parent / UI_CONTRACT_REPOSITORY_RELATIVE
    contract_path = run_dir / UI_CONTRACT_ARCHIVE
    shutil.copy2(source_contract, contract_path)
    contract = load_ui_contract(
        contract_path, expected_sha256=sha256_file(contract_path)
    )

    historical_root = (run_dir.parent / "historical-machine").resolve()
    state = historical_root / "state"
    profile = state / "profile"
    production = profile / "mod-content" / "xar-production"
    dlc_root = historical_root / "game" / "game" / "dlc" / "dlc001"
    dlc_root_second = historical_root / "game" / "game" / "dlc" / "dlc002"
    game_exe = historical_root / "game" / "binaries" / "ck3.exe"
    vanilla_rules = historical_root / "game" / "game" / "common" / "game_rules" / "00_game_rules.txt"

    production_files = [
        {"path": path, "size": index + 1, "sha256": f"{index + 1:x}" * 64}
        for index, path in enumerate(
            (
                "common/game_rules/xar_game_rules.txt",
                "common/on_action/eternal_recurrence_on_actions.txt",
                "descriptor.mod",
                "events/xar_events.txt",
            )
        )
    ]
    production_tree = {
        entry["path"]: {"size": entry["size"], "sha256": entry["sha256"]}
        for entry in production_files
    }
    production_payload = {
        "files": production_files,
        "format_version": 2,
        "git_sha": "c" * 40,
        "git_tag": None,
        "mod_version": "1.0.0",
        "workshop_item_id": "3784706360",
    }
    write_json_atomic(run_dir / "production.manifest.json", production_payload)

    runtime_files = [
        {
            "path": UI_CONTRACT_AGENT_RUNTIME_PATH,
            "size": contract_path.stat().st_size,
            "sha256": sha256_file(contract_path),
        },
        {
            "path": OBSERVATION_SCHEMA_AGENT_RUNTIME_PATH,
            "size": OBSERVATION_SCHEMA.stat().st_size,
            "sha256": sha256_file(OBSERVATION_SCHEMA),
        },
        {
            "path": ACTION_RECEIPT_SCHEMA_AGENT_RUNTIME_PATH,
            "size": ACTION_RECEIPT_SCHEMA.stat().st_size,
            "sha256": sha256_file(ACTION_RECEIPT_SCHEMA),
        },
    ]
    runtime_files.sort(key=lambda item: str(item["path"]))
    runtime = {
        "file_count": len(runtime_files),
        "files": runtime_files,
        "git": {
            "selected_runtime_revision": "c" * 40,
            "all_files_tracked": True,
            "untracked_runtime_files": [],
            "dirty": False,
            "status": [],
        },
    }
    runtime["sha256"] = snapshot_digest(runtime)
    rule_profile = [
        {"rule": f"vanilla_rule_{index:02}", "setting": f"default_{index:02}"}
        for index in range(81)
    ] + [
        {"rule": "xar_enabled", "setting": "xar_on"},
        {"rule": "xar_inheritance", "setting": "xar_inherit_100"},
        {"rule": "xar_score_basis", "setting": "xar_score_growth"},
    ]
    serialized_rules = json.dumps(
        rule_profile, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")
    environment = {
        "format_version": 1,
        "agent_version": "0.1.0",
        "agent_runtime": runtime,
        "prepared_at": "2026-08-22T00:00:00+00:00",
        "state_dir": str(state),
        "profile_dir": str(profile),
        "game": {
            "raw_version": "1.19.0.6",
            "display_version": "1.19.0.6",
            "distribution": "steam",
            "launcher_settings_sha256": "1" * 64,
            "executable": str(game_exe),
            "executable_sha256": "2" * 64,
            "vanilla_rules": str(vanilla_rules),
            "vanilla_rules_sha256": "3" * 64,
            "debug_mode": False,
        },
        "mod": {
            "name": EXPECTED_MOD_NAME,
            "git_revision": "c" * 40,
            "source_provenance": {
                "git_revision": "c" * 40,
                "git_tags_at_revision": [],
                "git_dirty": False,
                "git_status": [],
                "all_release_files_tracked": True,
                "untracked_release_files": [],
                "release_source_file_count": 86,
                "release_source_sha256": "5" * 64,
            },
            "production_path": str(production),
            "production_manifest": str(historical_root / "production.manifest.json"),
            "production_manifest_sha256": sha256_file(
                run_dir / "production.manifest.json"
            ),
            "production_tree_sha256": snapshot_digest(production_tree),
            "production_file_count": len(production_files),
            "release_identity": {
                "format_version": 2,
                "mod_version": "1.0.0",
                "git_tag": None,
                "workshop_item_id": "3784706360",
            },
        },
        "load_profile": {
            "enabled_mods": [OUTER_DESCRIPTOR_REF],
            "disabled_dlcs": [],
        },
        "rules": {
            "source": str(vanilla_rules),
            "source_sha256": "3" * 64,
            "declared_vanilla_rule_count": 81,
            "profile": rule_profile,
            "profile_sha256": hashlib.sha256(serialized_rules).hexdigest(),
            "ironman": False,
        },
        "display": {
            "language": "l_simp_chinese",
            "resolution": [2560, 1440],
            "mode": "fullscreen",
        },
        "dlc": {
            "installed_descriptor_count": 2,
            "installed_descriptors_sha256": "4" * 64,
            "allowed_mount_roots": [str(dlc_root), str(dlc_root_second)],
            "allowed_mount_roots_sha256": snapshot_digest(
                [str(dlc_root), str(dlc_root_second)]
            ),
            "note": "fixture",
        },
        "persistent_tutorial_state": {"policy": "preserve"},
        "legality": {
            "production_only": True,
            "single_mod": True,
            "visible_ui_only_for_decisions": True,
            "save_rollback": False,
            "runtime_logs": "environment attestation only; never policy input",
        },
    }
    environment["environment_sha256"] = _contract_digest(environment)
    write_json_atomic(run_dir / "environment.json", environment)

    debug_prefix = (
        "Log system initialized\n"
        f"{EXPECTED_MOD_NAME}|{OUTER_DESCRIPTOR_REF}|Enabled\n"
        f"Mounted Data: {dlc_root_second}\n"
        f"Mounted Data: {dlc_root}\n"
        f"Mounted Data: {production}\n"
    ).encode("utf-8")
    debug_path = artifacts / "runtime-debug-prefix.log"
    debug_path.write_bytes(debug_prefix)
    post_exit_debug_path = artifacts / "runtime-debug-post-exit.log"
    post_exit_debug_path.write_bytes(debug_prefix)
    debug_metadata = {
        "path": str(profile / "logs" / "debug.log"),
        "captured_prefix_size": len(debug_prefix),
        "captured_prefix_sha256": hashlib.sha256(debug_prefix).hexdigest(),
        "file_size_after_read": len(debug_prefix),
        "mtime_ns": 1,
        "prelaunch_epoch_ns": 1,
        "cleared_before_launch": [],
    }
    load = {
        "enabled_mods": [
            {"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}
        ],
        "isolated_mod_mounts": [str(production)],
        # Preserve engine/debug-log order; it is not a lexical set encoding.
        "runtime_dlc_mounts": [str(dlc_root_second), str(dlc_root)],
        "unclassified_mounts": [],
        "evidence_lines": [
            f"{EXPECTED_MOD_NAME}|{OUTER_DESCRIPTOR_REF}|Enabled",
            f"Mounted Data: {dlc_root_second}",
            f"Mounted Data: {dlc_root}",
            f"Mounted Data: {production}",
        ],
        "session_marker_count": 1,
        "source": "fresh non-debug boot log, reduced to load attestation only",
        "policy_boundary": "not available to gameplay perception or strategy",
        "debug_log": {
            **debug_metadata,
            "archive_path": "artifacts/runtime-debug-prefix.log",
            "archive_sha256": sha256_file(debug_path),
        },
        "post_exit_revalidated": True,
        "post_exit_debug_log": {
            **debug_metadata,
            "archive_path": "artifacts/runtime-debug-post-exit.log",
            "archive_sha256": sha256_file(post_exit_debug_path),
        },
    }
    write_json_atomic(artifacts / "supervisor-load-attestation.json", load)

    stores = {"real_profile": {}, "steam_userdata": {}, "workshop": {}}
    volatile = {
        "steam_remotecache": {},
        "policy": "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected.",
    }
    protected_payload = {
        "digest": snapshot_digest(stores),
        "stores": stores,
        "allowed_volatile": volatile,
    }
    write_gzip_json_atomic(run_dir / "protected-before.json.gz", protected_payload)
    write_gzip_json_atomic(run_dir / "protected-after.json.gz", protected_payload)

    pid = 42
    hwnd = 84
    creation_date = "20260822000000.000000+000"
    client_rect = [0, 0, 2560, 1440]
    binding = {
        "process": {
            "pid": pid,
            "parent_pid": 41,
            "name": "ck3.exe",
            "creation_date": creation_date,
            "executable": str(game_exe),
            "wmi_executable": str(game_exe),
            "handle_executable": str(game_exe),
        },
        "window": {
            "hwnd": hwnd,
            "client_rect": client_rect,
            "client_size": [2560, 1440],
        },
    }
    replay_spans: dict[int, tuple[object, ...]] = {}

    def make_observation(
        sequence: int, screen: str, color: tuple[int, int, int]
    ) -> tuple[dict[str, object], dict[str, object]]:
        observation_id = f"{sequence:032x}"
        frame_id = f"{sequence + 100:032x}"
        screenshot_ref = f"artifacts/frame-{sequence:02}.png"
        observation_ref = f"artifacts/frame-{sequence:02}.observation.json"
        image = Image.new("RGB", (2560, 1440), color)
        image.putpixel((0, 0), (sequence, 0, 0))
        screen_spec = next(item for item in contract.screens if item.screen_id == screen)
        for probe in screen_spec.pixel_probes:
            probe_rgb = tuple(
                int((minimum + maximum) / 2)
                for minimum, maximum in zip(
                    probe.mean_rgb_min, probe.mean_rgb_max
                )
            )
            image.paste(probe_rgb, probe.rect)
        image.save(run_dir / screenshot_ref)
        screenshot_hash = sha256_file(run_dir / screenshot_ref)
        spans = []
        anchors = []
        for anchor in screen_spec.anchors:
            left, top, right, bottom = anchor.region
            center = [int(2560 * (left + right) / 2), int(1440 * (top + bottom) / 2)]
            bbox = [center[0] - 40, center[1] - 15, center[0] + 40, center[1] + 15]
            span = OcrSpan(
                text=anchor.text,
                normalized=normalize_visible_text(anchor.text),
                score=0.9,
                center=tuple(center),
                bbox=tuple(bbox),
            )
            spans.append(span)
            anchors.append(
                {
                    "anchor_id": anchor.anchor_id,
                    "text": anchor.text,
                    "score": 0.9,
                    "bbox": bbox,
                    "center": center,
                }
            )
        replay_spans[sequence] = tuple(spans)
        ocr = [span.to_json() for span in spans]
        target_span = next(
            span.to_json()
            for span, anchor in zip(spans, screen_spec.anchors)
            if anchor.anchor_id == "main.new_game"
        ) if screen == "main_menu" else None
        controls = (
            [
                {
                    "control_id": "main_menu.new_game",
                    "label": contract.control("main_menu.new_game").label,
                    "control_token": f"{sequence:x}" * 64,
                    "bbox": target_span["bbox"],
                    "center": target_span["center"],
                }
            ]
            if screen == "main_menu"
            else []
        )
        policy = {
            "format_version": 2,
            "observation_id": observation_id,
            "frame_id": frame_id,
            "captured_at": f"2026-08-22T00:00:{sequence:02}+00:00",
            "screen": screen,
            "image": {
                "ref": f"frame:{frame_id}",
                "sha256": screenshot_hash,
                "width": 2560,
                "height": 1440,
            },
            "ocr": ocr,
            "visible_anchors": anchors,
            "visible_controls": controls,
            "visible_facts": {
                "screen": screen,
                "anchors": [item["anchor_id"] for item in anchors],
            },
            "confidence": 0.9,
            "unknown_reasons": [],
            "policy_boundary": "player-visible pixels and OCR only",
        }
        private = {
            "process": {"pid": pid, "hwnd": hwnd},
            "client_rect": client_rect,
            "screenshot_path": screenshot_ref,
            "observation_path": observation_ref,
            "capture_sequence": sequence,
            "captured_monotonic": float(sequence),
            "capture_started_at": policy["captured_at"],
        }
        write_json_atomic(
            run_dir / observation_ref,
            {
                "format_version": 2,
                "policy_observation": policy,
                "private_audit": private,
            },
        )
        evidence = {
            "observation_id": observation_id,
            "frame_id": frame_id,
            "captured_at": policy["captured_at"],
            "capture_sequence": sequence,
            "captured_monotonic": float(sequence),
            "screenshot_sha256": screenshot_hash,
            "screenshot": screenshot_ref,
            "observation": observation_ref,
            "pid": pid,
            "hwnd": hwnd,
            "client_rect": client_rect,
        }
        return policy, evidence

    policies: dict[int, dict[str, object]] = {}
    evidences: dict[int, dict[str, object]] = {}
    for sequence, screen, color in (
        (1, "main_menu", (10, 10, 10)),
        (2, "main_menu", (11, 11, 11)),
        (3, "main_menu", (12, 12, 12)),
        (4, "main_menu", (13, 13, 13)),
        (5, "bookmark_lobby", (14, 14, 14)),
        (6, "bookmark_lobby", (15, 15, 15)),
    ):
        policies[sequence], evidences[sequence] = make_observation(
            sequence, screen, color
        )

    def stable_policy(first: int, second: int, screen: str) -> dict[str, object]:
        payload = dict(policies[second])
        payload["stability"] = {
            "stable_frames": 2,
            "expected_screen": screen,
            "frames": [
                {
                    key: evidences[index][key]
                    for key in (
                        "observation_id",
                        "frame_id",
                        "captured_at",
                        "capture_sequence",
                        "captured_monotonic",
                        "screenshot_sha256",
                    )
                }
                for index in (first, second)
            ],
            "monotonic_delta": 1.0,
        }
        return payload

    def stable_audit(first: int, second: int, screen: str) -> dict[str, object]:
        return {
            "stable_frames": 2,
            "expected_screen": screen,
            "frames": [evidences[first], evidences[second]],
            "monotonic_delta": 1.0,
        }

    start = stable_policy(1, 2, "main_menu")
    start_audit = stable_audit(1, 2, "main_menu")
    after = stable_policy(5, 6, "bookmark_lobby")
    after_audit = stable_audit(5, 6, "bookmark_lobby")
    issued_span = next(
        dict(span)
        for span in policies[2]["ocr"]
        if span["text"] == contract.control("main_menu.new_game").text
    )
    issued_span.pop("score")
    fresh_span = next(
        dict(span)
        for span in policies[3]["ocr"]
        if span["text"] == contract.control("main_menu.new_game").text
    )
    fresh_span.pop("score")
    fresh_span["screen_point"] = list(fresh_span["center"])
    hover_span = next(
        dict(span)
        for span in policies[4]["ocr"]
        if span["text"] == contract.control("main_menu.new_game").text
    )
    hover_span.pop("score")
    hover_bbox = hover_span["bbox"]
    hover_span["patch_bbox"] = [
        max(0, hover_bbox[0] - 12),
        max(0, hover_bbox[1] - 12),
        min(2560, hover_bbox[2] + 12),
        min(1440, hover_bbox[3] + 12),
    ]
    with Image.open(run_dir / evidences[4]["screenshot"]) as source:
        source.load()
        hover_patch = source.crop(tuple(hover_span["patch_bbox"]))
    patch_pixel_sha = _memory_image_sha256(hover_patch)
    hover_span["patch_sha256"] = patch_pixel_sha
    hover_patch_path = artifacts / "00007-action.hover-patch.png"
    final_patch_path = artifacts / "00007-action.final-patch.png"
    hover_patch.save(hover_patch_path)
    hover_patch.save(final_patch_path)
    target = {
        "issued": issued_span,
        "fresh": fresh_span,
        "hover": hover_span,
        "final_patch_sha256": patch_pixel_sha,
        "hover_patch_artifact": {
            "path": "artifacts/00007-action.hover-patch.png",
            "sha256": sha256_file(hover_patch_path),
            "pixel_sha256": patch_pixel_sha,
        },
        "final_patch_artifact": {
            "path": "artifacts/00007-action.final-patch.png",
            "sha256": sha256_file(final_patch_path),
            "pixel_sha256": patch_pixel_sha,
        },
    }
    token = start["visible_controls"][0]["control_token"]
    fresh_evidence = {**evidences[3], "screen": "main_menu"}
    hover_evidence = {**evidences[4], "screen": "main_menu"}
    action = {
        "format_version": 2,
        "action_id": "a" * 32,
        "planned_at": "2026-08-22T00:00:02+00:00",
        "kind": "click_visible_control",
        "control_id": "main_menu.new_game",
        "control_token_sha256": hashlib.sha256(token.encode("ascii")).hexdigest(),
        "before_observation_id": start["observation_id"],
        "expected_post_screen": "bookmark_lobby",
        "status": "confirmed",
        "input_may_have_occurred": True,
        "risk": contract.control("main_menu.new_game").risk,
        "policy_boundary": "no caller-supplied coordinates or postconditions",
        "contract_sha256": contract.source_sha256,
        "receipt_artifact": "artifacts/00007-action.json",
        "input_budget": {"limit": 1, "consumed": 1},
        "binding": binding,
        "before_stable_observation": start_audit,
        "target": target,
        "pointer_input_may_have_occurred": True,
        "button_click_may_have_occurred": True,
        "send_input": {"requested": 2, "accepted": 2, "last_error": 0},
        "durable_events": {},
        "fresh_observation_id": policies[3]["observation_id"],
        "fresh_observation": fresh_evidence,
        "hover_observation_id": policies[4]["observation_id"],
        "hover_observation": hover_evidence,
        "input_attempted_at": "2026-08-22T00:00:03+00:00",
        "result_observation_id": after["observation_id"],
        "after_stable_observation": after_audit,
        "binding_after": binding,
        "finished_at": "2026-08-22T00:00:06+00:00",
    }
    navigation = {
        "claim": MENU_ACCEPTANCE_CLAIM,
        "window_binding": binding,
        "foreground_activation": foreground_attestation(pid, hwnd),
        "start_observation": start,
        "start_observation_audit": start_audit,
        "transition": {"action": action, "observation": after},
        "registered_capabilities": ["main_menu.new_game"],
        "forbidden_capabilities": ["bookmark_lobby.start_game"],
        "start_game_capability_registered": False,
    }

    process = {
        "pid": pid,
        "creation_date": creation_date,
        "executable": str(game_exe),
        "watchdog_pid": 43,
        "arguments": [str(game_exe), "-gdpr-compliant", f"-userdir={profile}"],
        "debug_mode": False,
        "fresh_log_epoch_ns": 1,
        "prelaunch_logs_removed": [],
        "pre_resume_ck3_inventory": {
            "tasklist_returncode": 0,
            "tasklist_pids": [pid],
            "wmi_pids": [pid],
            "processes": [
                {
                    "pid": pid,
                    "parent_pid": 41,
                    "name": "ck3.exe",
                    "executable": str(game_exe),
                    "creation_date": "2026-08-22T00:00:00.0000000Z",
                }
            ]
        },
    }
    shutdown = {
        "nonce": "b" * 32,
        "ck3_pid": pid,
        "ck3_creation_date": creation_date,
        "ck3_exit_code": 0,
        "job_active_processes_before_termination": 1,
        "job_active_processes_final": 0,
        "tree_gone": True,
        "cleanup_proven": True,
        "final_ck3_inventory": {"processes": []},
        "watchdog_pid": 43,
        "watchdog_creation_date": "20260822000000.000001+000",
        "watchdog_state_before": "running",
        "watchdog_state_after": "absent",
        "control_files_absent": {
            str(state / "control" / "ck3.json"): True,
            str(state / "control" / f"watchdog-{'b' * 32}.ready.json"): True,
            str(state / "control" / "ck3.watchdog_error"): True,
            str(state / "control" / "unsafe-cleanup.json"): True,
        },
        "contract_errors": [],
        "ok": True,
    }
    protected = {
        "post_exit_matches_baseline": True,
        "continuous_quiet_seconds": 5,
        "runtime_write_absence_proven": False,
        "sha256": protected_payload["digest"],
        "before_snapshot": "protected-before.json.gz",
        "before_snapshot_sha256": sha256_file(run_dir / "protected-before.json.gz"),
        "after_snapshot": "protected-after.json.gz",
        "after_snapshot_sha256": sha256_file(run_dir / "protected-after.json.gz"),
        "allowed_volatile_before": volatile,
        "allowed_volatile_after": volatile,
    }
    qualification = _qualification_fixture(
        run_dir, str(environment["environment_sha256"])
    )
    events = run_dir / "events.jsonl"
    append_event(
        events,
        {
            "kind": "smoke_started",
            "probe": "main_menu_to_bookmark_lobby",
            "environment_sha256": environment["environment_sha256"],
            "protected_storage_sha256": protected_payload["digest"],
            "ui_contract_sha256": contract.source_sha256,
            "normal_qualification_run_id": qualification["normal"]["run_id"],
            "crash_qualification_run_id": qualification["crash"]["run_id"],
        },
    )
    append_event(events, {"kind": "ck3_launched", "pid": pid})
    append_event(events, {"kind": "single_mod_runtime_attested"})
    append_event(
        events,
        {
            "kind": "foreground_activation_planned",
            "pid": pid,
            "hwnd": hwnd,
            "operation": "exact_hwnd_foreground_without_synthetic_input",
            "synthetic_input": False,
        },
    )
    append_event(
        events,
        {
            "kind": "foreground_activation_armed",
            "pid": pid,
            "hwnd": hwnd,
            "operation": "exact_hwnd_foreground_without_synthetic_input",
            "foreground_may_have_changed": True,
            "synthetic_input_may_have_occurred": False,
        },
    )
    append_event(
        events,
        {
            "kind": "foreground_activation_finished",
            "pid": pid,
            "hwnd": hwnd,
            "status": "confirmed",
            "attestation": navigation["foreground_activation"],
        },
    )
    append_event(
        events,
        {
            "kind": "visible_main_menu_attested",
            "contract_sha256": contract.source_sha256,
            "observation_id": start["observation_id"],
            "frame_ids": [item["frame_id"] for item in start_audit["frames"]],
        },
    )
    action["durable_events"]["planned"] = append_event(
        events,
        {
            "kind": "ui_action_planned",
            "action_id": action["action_id"],
            "control_id": action["control_id"],
            "token_sha256": action["control_token_sha256"],
            "contract_sha256": contract.source_sha256,
            "receipt_artifact": action["receipt_artifact"],
            "before_frame_ids": [item["frame_id"] for item in start_audit["frames"]],
        },
    )
    action["durable_events"]["armed"] = append_event(
        events,
        {
            "kind": "ui_input_armed",
            "action_id": action["action_id"],
            "control_id": action["control_id"],
            "contract_sha256": contract.source_sha256,
            "receipt_artifact": action["receipt_artifact"],
            "binding": binding,
            "target": {key: target[key] for key in ("issued", "fresh")},
            "pointer_input_may_have_occurred": True,
            "button_click_may_have_occurred": True,
        },
    )
    action["durable_events"]["finished"] = append_event(
        events,
        {
            "kind": "ui_action_finished",
            "action_id": action["action_id"],
            "status": "confirmed",
            "receipt_artifact": action["receipt_artifact"],
            "result_frame_ids": [item["frame_id"] for item in after_audit["frames"]],
            "send_input": action["send_input"],
        },
    )
    append_event(
        events,
        {
            "kind": "bookmark_lobby_attested",
            "contract_sha256": contract.source_sha256,
            "observation_id": after["observation_id"],
            "frame_ids": [item["frame_id"] for item in after_audit["frames"]],
        },
    )
    append_event(
        events,
        {"kind": "tracked_process_stopped", "pid": pid, "cleanup_proven": True},
    )
    append_event(
        events,
        {
            "kind": "postflight_attested",
            "protected_storage_sha256": protected_payload["digest"],
            "production_tree_sha256": environment["mod"]["production_tree_sha256"],
        },
    )
    write_json_atomic(artifacts / "00007-action.json", action)

    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run_dir.name,
        "kind": MENU_KIND,
        "acceptance_claim": MENU_ACCEPTANCE_CLAIM,
        "clean_engine_boot_required": False,
        "valid_score_episode": False,
        "growth100_lobby_adoption_proven": False,
        "runtime_write_absence_proven": False,
        "replay_trust_model": dict(REPLAY_TRUST_MODEL),
        "started_at": "2026-08-22T00:00:00+00:00",
        "finished_at": "2026-08-22T00:01:00+00:00",
        "environment_sha256": environment["environment_sha256"],
        "run_dir": ".",
        "ui_contract": {
            "agent_runtime_path": UI_CONTRACT_AGENT_RUNTIME_PATH,
            "source_repository_relative": UI_CONTRACT_REPOSITORY_RELATIVE.as_posix(),
            "archive_path": UI_CONTRACT_ARCHIVE,
            "size": contract_path.stat().st_size,
            "sha256": contract.source_sha256,
        },
        "qualification": qualification,
        "process": process,
        "load_attestation": load,
        "navigation_attestation": navigation,
        "shutdown_attestation": shutdown,
        "post_shutdown_ck3_inventory": {"processes": []},
        "protected_storage": protected,
        "production_tree_unchanged": True,
        "engine_diagnostics": {
            "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
            "zero_diagnostics": True,
            "current_mod_diagnostics": False,
            "current_mod_diagnostic_hits": [],
            "logs": {
                "error.log": {"present": False, "diagnostic_records": 0},
                "gui_warnings.log": {"present": False, "diagnostic_records": 0},
            },
        },
        "finalized": False,
        "ok": False,
    }
    report["artifacts"] = _artifact_manifest(run_dir)
    body_hash = _report_body_sha256(report)
    report["report_body_sha256"] = body_hash
    report["final_event_sha256"] = append_event(
        events,
        {"kind": "smoke_finished", "ok": True, "report_body_sha256": body_hash},
    )
    report["finalized"] = True
    report["ok"] = True
    chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    write_json_atomic(run_dir / "report.json", report)
    return report, replay_spans


def _tamper_report_process(run_dir: Path) -> None:
    report_path = run_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["process"]["pid"] += 1
    write_json_atomic(report_path, report)


def _tamper_event_digest(run_dir: Path) -> None:
    events = run_dir / "events.jsonl"
    rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
    rows[4]["event_sha256"] = "0" * 64
    events.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _resign_after_artifact_mutation(run_dir: Path) -> None:
    report_path = run_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["artifacts"] = _artifact_manifest(run_dir)
    body = _report_body_sha256(report)
    report["report_body_sha256"] = body
    events = run_dir / "events.jsonl"
    lines = events.read_text(encoding="utf-8").splitlines()
    events.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    report["final_event_sha256"] = append_event(
        events,
        {"kind": "smoke_finished", "ok": report["ok"], "report_body_sha256": body},
    )
    chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    write_json_atomic(report_path, report)


def _tamper_fresh_observation_envelope(run_dir: Path) -> None:
    path = run_dir / "artifacts" / "frame-03.observation.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["policy_observation"]["image"]["width"] = 2559
    write_json_atomic(path, payload)
    _resign_after_artifact_mutation(run_dir)


def _tamper_private_artifact_reference(run_dir: Path) -> None:
    path = run_dir / "artifacts" / "frame-03.observation.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["private_audit"]["screenshot_path"] = "evil/frame-03.png"
    write_json_atomic(path, payload)
    _resign_after_artifact_mutation(run_dir)


def _event_payloads(run_dir: Path) -> list[dict[str, object]]:
    return [
        {
            key: value
            for key, value in json.loads(line).items()
            if key not in {"event_index", "previous_event_sha256", "event_sha256"}
        }
        for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ][:-1]


def _archived_observation(run_dir: Path, index: int) -> Observation:
    path = run_dir / "artifacts" / f"frame-{index:02}.observation.json"
    archived = json.loads(path.read_text(encoding="utf-8"))
    policy = archived["policy_observation"]
    private = archived["private_audit"]
    spans = tuple(
        OcrSpan(
            text=item["text"],
            normalized=item["normalized"],
            score=float(item["score"]),
            center=tuple(item["center"]),
            bbox=tuple(item["bbox"]),
        )
        for item in policy["ocr"]
    )
    anchors = tuple(
        VisibleAnchor(
            anchor_id=item["anchor_id"],
            text=item["text"],
            score=float(item["score"]),
            bbox=tuple(item["bbox"]),
            center=tuple(item["center"]),
        )
        for item in policy["visible_anchors"]
    )
    controls = tuple(
        VisibleControl(
            control_id=item["control_id"],
            label=item["label"],
            token=item["control_token"],
            bbox=tuple(item["bbox"]),
            center=tuple(item["center"]),
        )
        for item in policy["visible_controls"]
    )
    return Observation(
        observation_id=policy["observation_id"],
        frame_id=policy["frame_id"],
        captured_at=policy["captured_at"],
        screen=policy["screen"],
        pid=int(private["process"]["pid"]),
        hwnd=int(private["process"]["hwnd"]),
        client_rect=tuple(private["client_rect"]),
        screenshot=private["screenshot_path"],
        screenshot_sha256=policy["image"]["sha256"],
        spans=spans,
        anchors=anchors,
        controls=controls,
        confidence=float(policy["confidence"]),
        unknown_reasons=tuple(policy["unknown_reasons"]),
        capture_sequence=int(private["capture_sequence"]),
        captured_monotonic=float(private["captured_monotonic"]),
        audit_path=private["observation_path"],
    )


def _strict_driver(
    run_dir: Path, report: dict[str, object], callback
) -> tuple[VisibleUiDriver, str, object]:
    contract = load_ui_contract(
        run_dir / UI_CONTRACT_ARCHIVE,
        expected_sha256=report["ui_contract"]["sha256"],
    )
    first = _archived_observation(run_dir, 1)
    before = _archived_observation(run_dir, 2)
    stable = StableObservation("main_menu", (first, before))
    control = before.controls[0]
    spec = contract.control(control.control_id)
    target = next(span for span in before.spans if span.bbox == control.bbox)
    driver = object.__new__(VisibleUiDriver)
    driver.contract = contract
    driver.artifacts = run_dir / "artifacts"
    driver._contract_sha256 = report["ui_contract"]["sha256"]
    driver._durable_event_callback = callback
    driver._secret = b"fixture-secret"
    driver._session_nonce = "fixture-session"
    driver._sequence = 6
    driver._capture_sequence = 6
    driver._input_budget_consumed = False
    driver._issued = {
        control.token: _IssuedControl(
            before,
            spec,
            target,
            time.monotonic(),
            stable,
        )
    }
    binding = report["navigation_attestation"]["window_binding"]
    window = mock.Mock()
    window.pid = binding["process"]["pid"]
    window.hwnd = binding["window"]["hwnd"]
    window.client_rect = tuple(binding["window"]["client_rect"])
    window.audit_binding.return_value = binding
    driver.window = window
    return driver, control.token, window


def _finalize_red_fixture(
    run_dir: Path,
    report: dict[str, object],
    rows: list[dict[str, object]],
    *,
    action: dict[str, object] | None = None,
) -> None:
    events = run_dir / "events.jsonl"
    events.unlink()
    if action is not None:
        action["durable_events"] = {}
    event_labels = {
        "ui_action_planned": "planned",
        "ui_input_armed": "armed",
        "ui_action_finished": "finished",
    }
    for row in rows:
        digest = append_event(events, row)
        if action is not None and row.get("kind") in event_labels:
            action["durable_events"][event_labels[str(row["kind"])]] = digest
    if action is not None:
        write_json_atomic(run_dir / str(action["receipt_artifact"]), action)
    report["artifacts"] = _artifact_manifest(run_dir)
    report["finalized"] = False
    report["ok"] = False
    report["error"] = "synthetic RED fixture"
    report["error_type"] = "AgentError"
    body = _report_body_sha256(report)
    report["report_body_sha256"] = body
    report["final_event_sha256"] = append_event(
        events,
        {"kind": "smoke_finished", "ok": False, "report_body_sha256": body},
    )
    report["finalized"] = True
    chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    write_json_atomic(run_dir / "report.json", report)


def _prepare_prefinal_fixture(
    run_dir: Path,
    report: dict[str, object],
    rows: list[dict[str, object]],
    *,
    action: dict[str, object] | None = None,
) -> None:
    """Restore a finalized fixture to its exact pre-smoke_finished state."""
    events = run_dir / "events.jsonl"
    events.unlink()
    if action is not None:
        action["durable_events"] = {}
    event_labels = {
        "ui_action_planned": "planned",
        "ui_input_armed": "armed",
        "ui_action_finished": "finished",
    }
    for row in rows:
        digest = append_event(events, row)
        if action is not None and row.get("kind") in event_labels:
            action["durable_events"][event_labels[str(row["kind"])]] = digest
    if action is not None:
        write_json_atomic(run_dir / str(action["receipt_artifact"]), action)
        report["navigation_attestation"]["transition"]["action"] = action
    report["artifacts"] = _artifact_manifest(run_dir)
    for field in (
        "report_body_sha256",
        "final_event_sha256",
        "event_chain",
    ):
        report.pop(field, None)
    report["finalized"] = False
    report["ok"] = False
    write_json_atomic(run_dir / "report.json", report)


def _refinalize_green_fixture(
    run_dir: Path,
    report: dict[str, object],
    rows: list[dict[str, object]],
    action: dict[str, object],
) -> None:
    events = run_dir / "events.jsonl"
    events.unlink()
    action["durable_events"] = {}
    labels = {
        "ui_action_planned": "planned",
        "ui_input_armed": "armed",
        "ui_action_finished": "finished",
    }
    for row in rows:
        digest = append_event(events, row)
        if row.get("kind") in labels:
            action["durable_events"][labels[str(row["kind"])]] = digest
    write_json_atomic(run_dir / str(action["receipt_artifact"]), action)
    report["navigation_attestation"]["transition"]["action"] = action
    report["artifacts"] = _artifact_manifest(run_dir)
    report["finalized"] = False
    report["ok"] = False
    body = _report_body_sha256(report)
    report["report_body_sha256"] = body
    report["final_event_sha256"] = append_event(
        events,
        {"kind": "smoke_finished", "ok": True, "report_body_sha256": body},
    )
    report["finalized"] = True
    report["ok"] = True
    chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    write_json_atomic(run_dir / "report.json", report)


def build_red_report(
    run_dir: Path, mode: str
) -> tuple[dict[str, object], dict[int, tuple[object, ...]]]:
    report, replay_spans = build_strict_green_report(run_dir)
    rows = _event_payloads(run_dir)
    action_path = run_dir / "artifacts" / "00007-action.json"
    action = json.loads(action_path.read_text(encoding="utf-8"))
    if mode in {
        "clean-pre-input",
        "foreground-failed",
        "foreground-completed-no-observation",
    }:
        allowed = {
            "smoke_started",
            "ck3_launched",
            "single_mod_runtime_attested",
            "tracked_process_stopped",
            "postflight_attested",
        }
        if mode in {"foreground-failed", "foreground-completed-no-observation"}:
            allowed.update(
                {
                    "foreground_activation_planned",
                    "foreground_activation_armed",
                }
            )
        if mode == "foreground-completed-no-observation":
            allowed.add("foreground_activation_finished")
        rows = [
            row
            for row in rows
            if row["kind"] in allowed
        ]
        report.pop("navigation_attestation")
        action_path.unlink()
        for suffix in ("hover-patch.png", "final-patch.png"):
            (run_dir / "artifacts" / f"00007-action.{suffix}").unlink()
        action = None
    elif mode == "failed-after-input":
        report.pop("navigation_attestation")
        action["status"] = "failed_after_possible_input"
        action["error"] = "AgentError: bookmark lobby timeout"
        action.pop("result_observation_id")
        action.pop("after_stable_observation")
        action.pop("binding_after")
        rows = [row for row in rows if row["kind"] != "bookmark_lobby_attested"]
        finished = next(row for row in rows if row["kind"] == "ui_action_finished")
        finished.clear()
        finished.update(
            {
                "kind": "ui_action_finished",
                "action_id": action["action_id"],
                "status": "failed_after_possible_input",
                "receipt_artifact": action["receipt_artifact"],
                "input_may_have_occurred": True,
                "button_click_may_have_occurred": True,
            }
        )
    elif mode == "armed-wal-failed-before-commit":
        report.pop("navigation_attestation")
        action["status"] = "failed_after_possible_input"
        action["input_may_have_occurred"] = True
        action["pointer_input_may_have_occurred"] = True
        action["button_click_may_have_occurred"] = False
        action["send_input"] = {
            "requested": 2,
            "accepted": None,
            "last_error": None,
        }
        action["error"] = "OSError: ui_input_armed WAL callback failed"
        for key in (
            "hover_observation_id",
            "hover_observation",
            "result_observation_id",
            "after_stable_observation",
            "binding_after",
        ):
            action.pop(key, None)
        for key in (
            "hover",
            "final_patch_sha256",
            "hover_patch_artifact",
            "final_patch_artifact",
        ):
            action["target"].pop(key, None)
        for suffix in ("hover-patch.png", "final-patch.png"):
            (run_dir / "artifacts" / f"00007-action.{suffix}").unlink()
        rows = [
            row
            for row in rows
            if row["kind"]
            not in {
                "ui_input_armed",
                "ui_action_finished",
                "bookmark_lobby_attested",
            }
        ]
    elif mode == "unsafe-cleanup":
        rows = [
            row
            for row in rows
            if row["kind"] not in {"tracked_process_stopped", "postflight_attested"}
        ]
        for key in (
            "shutdown_attestation",
            "protected_storage",
            "engine_diagnostics",
            "production_tree_unchanged",
        ):
            report.pop(key)
        report["post_shutdown_ck3_inventory"] = {
            "processes": [{"pid": report["process"]["pid"]}]
        }
        report["unsafe_cleanup"] = True
        (run_dir / "protected-after.json.gz").unlink()
        load = report["load_attestation"]
        load.pop("post_exit_revalidated")
        load.pop("post_exit_debug_log")
        write_json_atomic(
            run_dir / "artifacts" / "supervisor-load-attestation.json", load
        )
    elif mode == "cleanup-contract-error":
        # stop_tracked can prove the complete process/control-tree absence
        # while still reporting a non-safety shutdown contract error.  That
        # must remain a replayable RED with protected postflight retained.
        report["shutdown_attestation"]["ok"] = False
        report["shutdown_attestation"]["contract_errors"] = [
            "CK3 exited before a require-running stop"
        ]
    else:
        raise AssertionError(mode)
    _finalize_red_fixture(run_dir, report, rows, action=action)
    return report, replay_spans


class ForegroundScenarioTests(unittest.TestCase):
    def test_bound_foreground_failure_is_armed_once_and_never_retried(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-foreground-") as temporary:
            run_dir = Path(temporary).resolve() / "run"
            artifacts = run_dir / "artifacts"
            artifacts.mkdir(parents=True)
            events = run_dir / "events.jsonl"
            contract_archive = run_dir / "ui-contract.json"
            contract_archive.write_text("{}\n", encoding="utf-8")
            process = mock.Mock()
            process.poll.return_value = None
            handle = SimpleNamespace(process=process)
            spec = SimpleNamespace(game_exe=Path("C:/game/binaries/ck3.exe"))
            window = mock.Mock(pid=42, hwnd=84)
            window.request_foreground_without_input.side_effect = AgentError(
                "foreground fallback detach failed"
            )
            with mock.patch(
                "xar_autoplayer.vision.load_ui_contract", return_value=object()
            ), mock.patch(
                "xar_autoplayer.vision.BoundGameWindow.bind_session",
                return_value=window,
            ) as bind, mock.patch(
                "xar_autoplayer.control.VisibleUiDriver"
            ) as driver:
                with self.assertRaisesRegex(AgentError, "detach failed"):
                    _run_menu_scenario(
                        spec,
                        handle,
                        {"display": {"language": "l_simp_chinese"}},
                        artifacts,
                        events,
                        contract_archive,
                        "a" * 64,
                        1,
                    )
            bind.assert_called_once_with(handle, spec.game_exe)
            window.request_foreground_without_input.assert_called_once_with()
            driver.assert_not_called()
            rows = [
                json.loads(line)
                for line in events.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [row["kind"] for row in rows],
                ["foreground_activation_planned", "foreground_activation_armed"],
            )
            self.assertFalse(rows[0]["synthetic_input"])
            self.assertFalse(rows[1]["synthetic_input_may_have_occurred"])

    def test_committed_foreground_wal_failures_preserve_single_prefix(self) -> None:
        for failure_kind, expected_kinds, expected_request_count in (
            (
                "foreground_activation_planned",
                ["foreground_activation_planned"],
                0,
            ),
            (
                "foreground_activation_armed",
                ["foreground_activation_planned", "foreground_activation_armed"],
                0,
            ),
            (
                "foreground_activation_finished",
                [
                    "foreground_activation_planned",
                    "foreground_activation_armed",
                    "foreground_activation_finished",
                ],
                1,
            ),
        ):
            with self.subTest(failure_kind=failure_kind), tempfile.TemporaryDirectory(
                prefix="xar-menu-foreground-wal-"
            ) as temporary:
                run_dir = Path(temporary).resolve() / "run"
                artifacts = run_dir / "artifacts"
                artifacts.mkdir(parents=True)
                events = run_dir / "events.jsonl"
                contract_archive = run_dir / "ui-contract.json"
                contract_archive.write_text("{}\n", encoding="utf-8")
                process = mock.Mock()
                process.poll.return_value = None
                handle = SimpleNamespace(process=process)
                spec = SimpleNamespace(game_exe=Path("C:/game/binaries/ck3.exe"))
                window = mock.Mock(pid=42, hwnd=84)
                window.request_foreground_without_input.return_value = (
                    foreground_attestation()
                )

                def committed_then_raise(event_path: Path, payload: dict[str, object]):
                    digest = append_event(event_path, payload)
                    if payload.get("kind") == failure_kind:
                        raise OSError(f"committed {failure_kind}")
                    return digest

                with mock.patch(
                    "xar_autoplayer.vision.load_ui_contract", return_value=object()
                ), mock.patch(
                    "xar_autoplayer.vision.BoundGameWindow.bind_session",
                    return_value=window,
                ), mock.patch(
                    "xar_autoplayer.control.VisibleUiDriver"
                ) as driver, mock.patch(
                    "xar_autoplayer.menu_smoke.append_event",
                    side_effect=committed_then_raise,
                ):
                    with self.assertRaisesRegex(OSError, failure_kind):
                        _run_menu_scenario(
                            spec,
                            handle,
                            {"display": {"language": "l_simp_chinese"}},
                            artifacts,
                            events,
                            contract_archive,
                            "a" * 64,
                            1,
                        )
                self.assertEqual(
                    window.request_foreground_without_input.call_count,
                    expected_request_count,
                )
                driver.assert_not_called()
                rows = [
                    json.loads(line)
                    for line in events.read_text(encoding="utf-8").splitlines()
                ]
                self.assertEqual([row["kind"] for row in rows], expected_kinds)


class MenuQualificationGenerationTests(unittest.TestCase):
    @staticmethod
    def _write_candidate(
        runs: Path,
        run_id: str,
        *,
        kind: str,
        environment_sha256: str,
        format_version: int | None = None,
        finished_at: str | None = None,
        started_at: str | None = None,
    ) -> Path:
        run = runs / run_id
        run.mkdir(parents=True)
        payload: dict[str, object] = {
            "run_id": run_id,
            "kind": kind,
            "environment_sha256": environment_sha256,
            "finalized": True,
            "ok": True,
            "valid_score_episode": False,
        }
        if format_version is not None:
            payload["format_version"] = format_version
        if kind == "infrastructure_smoke":
            payload.update(
                {
                    "run_dir": "." if format_version == 2 else str(run),
                    "acceptance_claim": "isolated_single_mod_visible_main_menu_only",
                    "finished_at": finished_at,
                }
            )
        else:
            payload["started_at"] = started_at
            payload["crash_attestation"] = {"cleanup_proven": True}
            payload["production_tree_unchanged"] = True
        write_json_atomic(run / "report.json", payload)
        return run

    def test_live_scanner_skips_newer_v1_and_selects_older_v2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-live-v2-") as temporary:
            state = Path(temporary).resolve()
            runs = state / "runs"
            environment_sha256 = "a" * 64
            legacy = self._write_candidate(
                runs,
                "20260822T030000Z-normal-v1",
                kind="infrastructure_smoke",
                environment_sha256=environment_sha256,
                format_version=1,
                finished_at="2026-08-22T03:00:01+00:00",
            )
            normal = self._write_candidate(
                runs,
                "20260822T020000Z-normal-v2",
                kind="infrastructure_smoke",
                environment_sha256=environment_sha256,
                format_version=2,
                # Z is intentionally lexically later than '+00:00'; the gate
                # must compare parsed UTC instants rather than strings.
                finished_at="2026-08-22T02:00:01Z",
            )
            crash = self._write_candidate(
                runs,
                "20260822T040000Z-crash-v2",
                kind="crash_recovery_smoke",
                environment_sha256=environment_sha256,
                started_at="2026-08-22T02:01:01+00:00",
            )

            def replay_normal(path: Path) -> dict[str, object]:
                return json.loads((path / "report.json").read_text(encoding="utf-8"))

            def replay_crash(path: Path) -> dict[str, object]:
                return json.loads((path / "report.json").read_text(encoding="utf-8"))

            with mock.patch(
                "xar_autoplayer.runtime.validate_smoke_report",
                side_effect=replay_normal,
            ), mock.patch(
                "xar_autoplayer.crash_probe.validate_crash_report",
                side_effect=replay_crash,
            ):
                selected = _require_menu_qualification(
                    SimpleNamespace(state_dir=state),
                    {"environment_sha256": environment_sha256},
                )
            self.assertEqual(selected["normal_source"], normal)
            self.assertNotEqual(selected["normal_source"], legacy)
            self.assertEqual(selected["crash_source"], crash)

    def test_live_scanner_never_authorizes_only_v1_normal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-live-v1-only-") as temporary:
            state = Path(temporary).resolve()
            runs = state / "runs"
            environment_sha256 = "b" * 64
            self._write_candidate(
                runs,
                "20260822T020000Z-normal-v1",
                kind="infrastructure_smoke",
                environment_sha256=environment_sha256,
                format_version=1,
                finished_at="2026-08-22T02:00:01+00:00",
            )
            with mock.patch(
                "xar_autoplayer.runtime.validate_smoke_report",
                side_effect=lambda path: json.loads(
                    (path / "report.json").read_text(encoding="utf-8")
                ),
            ):
                with self.assertRaisesRegex(AgentError, "ordinary smoke GREEN"):
                    _require_menu_qualification(
                        SimpleNamespace(state_dir=state),
                        {"environment_sha256": environment_sha256},
                    )

    def test_archive_uses_v2_validator_and_survives_source_removal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-archive-v2-") as temporary:
            root = Path(temporary).resolve()
            source_root = root / "sources"
            menu_run = root / "menu-run"
            menu_run.mkdir()
            environment_sha256 = "c" * 64
            normal = self._write_candidate(
                source_root,
                "normal-v2",
                kind="infrastructure_smoke",
                environment_sha256=environment_sha256,
                format_version=2,
                finished_at="2026-08-22T02:00:00+00:00",
            )
            crash = self._write_candidate(
                source_root,
                "crash-v2",
                kind="crash_recovery_smoke",
                environment_sha256=environment_sha256,
                started_at="2026-08-22T02:01:00+00:00",
            )
            for path in (normal, crash):
                append_event(path / "events.jsonl", {"kind": "smoke_finished", "ok": True})
            normal_report = json.loads((normal / "report.json").read_text(encoding="utf-8"))
            crash_report = json.loads((crash / "report.json").read_text(encoding="utf-8"))

            def replay_normal(path: Path) -> dict[str, object]:
                return json.loads((path / "report.json").read_text(encoding="utf-8"))

            def replay_crash(path: Path) -> dict[str, object]:
                return json.loads((path / "report.json").read_text(encoding="utf-8"))

            with mock.patch(
                "xar_autoplayer.runtime.validate_smoke_report",
                side_effect=replay_normal,
            ), mock.patch(
                "xar_autoplayer.crash_probe.validate_crash_report",
                side_effect=replay_crash,
            ):
                archived = _archive_menu_qualification(
                    {
                        "environment_sha256": environment_sha256,
                        "normal_source": normal,
                        "normal_report": normal_report,
                        "crash_source": crash,
                        "crash_report": crash_report,
                    },
                    menu_run,
                )
            self.assertEqual(
                archived["normal"]["validator"],
                NORMAL_V2_QUALIFICATION_VALIDATOR,
            )
            shutil.rmtree(source_root)
            nested = menu_run / archived["normal"]["archive_path"]
            self.assertTrue((nested / "report.json").is_file())
            self.assertEqual(
                json.loads((nested / "report.json").read_text(encoding="utf-8")),
                normal_report,
            )


class MenuReportValidatorTests(unittest.TestCase):
    @staticmethod
    def _legacy_zero_input_red(
        run_dir: Path, *, retain_observations: bool = False
    ) -> tuple[dict[str, object], dict[int, tuple[object, ...]]]:
        report, replay = build_red_report(run_dir, "clean-pre-input")
        if not retain_observations:
            for path in (run_dir / "artifacts").iterdir():
                if path.suffix.casefold() == ".png" or path.name.endswith(
                    ".observation.json"
                ):
                    path.unlink()
        normal_entry = report["qualification"]["normal"]
        nested_report_path = (
            run_dir / normal_entry["archive_path"] / "report.json"
        )
        nested = json.loads(nested_report_path.read_text(encoding="utf-8"))
        nested["format_version"] = 1
        write_json_atomic(nested_report_path, nested)
        normal_entry["validator"] = LEGACY_NORMAL_QUALIFICATION_VALIDATOR
        normal_entry["report_sha256"] = sha256_file(nested_report_path)
        rows = _event_payloads(run_dir)
        _finalize_red_fixture(run_dir, report, rows)
        return report, replay

    @staticmethod
    def _legacy_replay_patches():
        def replay_legacy(path: Path, expected: str) -> dict[str, object]:
            payload = json.loads((path / "report.json").read_text(encoding="utf-8"))
            if payload.get("environment_sha256") != expected:
                raise AgentError("fixture legacy qualification environment differs")
            return payload

        def replay_crash(path: Path) -> dict[str, object]:
            return json.loads((path / "report.json").read_text(encoding="utf-8"))

        return (
            mock.patch(
                "xar_autoplayer.menu_smoke._validate_legacy_normal_qualification",
                side_effect=replay_legacy,
            ),
            mock.patch(
                "xar_autoplayer.crash_probe.validate_crash_report",
                side_effect=replay_crash,
            ),
        )

    def test_legacy_v1_qualification_replays_only_for_zero_input_red(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-legacy-red-") as temporary:
            run_dir = Path(temporary).resolve() / "20260822T000000Z-menu-legacyred"
            self._legacy_zero_input_red(run_dir)
            legacy_patch, crash_patch = self._legacy_replay_patches()
            with legacy_patch, crash_patch:
                replayed = validate_menu_smoke_report(run_dir)
            self.assertFalse(replayed["ok"])

    def test_legacy_v1_zero_input_red_may_retain_pure_observations(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-legacy-observation-red-"
        ) as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-legacy-observation"
            )
            _report, replay_spans = self._legacy_zero_input_red(
                run_dir, retain_observations=True
            )
            legacy_patch, crash_patch = self._legacy_replay_patches()
            with mock.patch(
                "xar_autoplayer.vision.ocr.ocr_spans",
                side_effect=lambda image, *_args, **_kwargs: replay_spans[
                    int(image.getpixel((0, 0))[0])
                ],
            ), legacy_patch, crash_patch:
                replayed = validate_menu_smoke_report(run_dir)
            self.assertFalse(replayed["ok"])

    def test_legacy_v1_qualification_is_rejected_if_authorizing_or_input_bearing(self) -> None:
        cases = (
            "green",
            "ui-event",
            "bookmark-event",
            "receipt",
            "action",
            "navigation-artifact",
            "navigation-report",
        )
        for mode in cases:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-legacy-{mode}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / f"20260822T000000Z-menu-legacy-{mode}"
                )
                report, _replay = self._legacy_zero_input_red(run_dir)
                verified = _verified_artifact_manifest(report, run_dir)
                if mode == "green":
                    report["ok"] = True
                elif mode == "ui-event":
                    append_event(
                        run_dir / "events.jsonl",
                        {"kind": "ui_input_armed"},
                    )
                elif mode == "bookmark-event":
                    append_event(
                        run_dir / "events.jsonl",
                        {"kind": "bookmark_lobby_attested"},
                    )
                elif mode == "navigation-report":
                    report["navigation_attestation"] = {}
                else:
                    names = {
                        "receipt": "forged-receipt.json",
                        "action": "00001-action.json",
                        "navigation-artifact": "navigation.json",
                    }
                    name = names[mode]
                    artifact = run_dir / "artifacts" / name
                    artifact.write_text("{}\n", encoding="utf-8")
                    verified[f"artifacts/{name}"] = artifact
                legacy_patch, crash_patch = self._legacy_replay_patches()
                with legacy_patch, crash_patch, self.assertRaisesRegex(
                    AgentError, "normal qualification archive differs"
                ):
                    _validate_archived_menu_qualification(report, verified)

    @staticmethod
    def _validate_strict(
        run_dir: Path, replay_spans: dict[int, tuple[object, ...]]
    ) -> dict[str, object]:
        def replay_nested_normal(path: Path, expected: str) -> dict[str, object]:
            payload = json.loads((path / "report.json").read_text(encoding="utf-8"))
            if payload.get("environment_sha256") != expected:
                raise AgentError("fixture normal qualification environment differs")
            return payload

        def replay_nested_crash(path: Path) -> dict[str, object]:
            return json.loads((path / "report.json").read_text(encoding="utf-8"))

        # The normal and crash replay engines have their own exhaustive suites.
        # Treat them as leaf validators here so this fixture can focus on the
        # menu archive, pixel/OCR replay, lifecycle, and cross-artifact bindings.
        with mock.patch(
            "xar_autoplayer.vision.ocr.ocr_spans",
            side_effect=lambda image, *_args, **_kwargs: replay_spans[
                int(image.getpixel((0, 0))[0])
            ],
        ), mock.patch(
            "xar_autoplayer.menu_smoke._validate_normal_qualification",
            side_effect=replay_nested_normal,
        ), mock.patch(
            "xar_autoplayer.crash_probe.validate_crash_report",
            side_effect=replay_nested_crash,
        ):
            return validate_menu_smoke_report(run_dir)

    def test_public_validator_rejects_pseudo_qualification_without_leaf_stubs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-pseudo-qualification-") as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-12345678"
            )
            _report, _replay = build_strict_green_report(run_dir)
            with self.assertRaisesRegex(
                AgentError, "normal qualification replay failed"
            ):
                validate_menu_smoke_report(run_dir)

    def test_public_validator_accepts_complete_archive_and_relocation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-strict-") as temporary:
            root = Path(temporary).resolve()
            run_dir = root / "first" / "20260822T000000Z-menu-12345678"
            _report, replay = build_strict_green_report(run_dir)
            self.assertTrue(self._validate_strict(run_dir, replay)["ok"])
            relocated = root / "relocated" / run_dir.name
            shutil.copytree(run_dir, relocated)
            self.assertTrue(self._validate_strict(relocated, replay)["ok"])

    def test_public_replay_rejects_artifact_created_by_semantic_leaf(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-public-artifact-race-"
        ) as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-public-race"
            )
            _report, replay_spans = build_strict_green_report(run_dir)

            def replay_nested_normal(
                path: Path, expected: str
            ) -> dict[str, object]:
                payload = json.loads(
                    (path / "report.json").read_text(encoding="utf-8")
                )
                if payload.get("environment_sha256") != expected:
                    raise AgentError(
                        "fixture normal qualification environment differs"
                    )
                (run_dir / "artifacts" / "late-unreferenced.bin").write_bytes(
                    b"created during semantic replay"
                )
                return payload

            def replay_nested_crash(path: Path) -> dict[str, object]:
                return json.loads(
                    (path / "report.json").read_text(encoding="utf-8")
                )

            with mock.patch(
                "xar_autoplayer.vision.ocr.ocr_spans",
                side_effect=lambda image, *_args, **_kwargs: replay_spans[
                    int(image.getpixel((0, 0))[0])
                ],
            ), mock.patch(
                "xar_autoplayer.menu_smoke._validate_normal_qualification",
                side_effect=replay_nested_normal,
            ), mock.patch(
                "xar_autoplayer.crash_probe.validate_crash_report",
                side_effect=replay_nested_crash,
            ), self.assertRaisesRegex(AgentError, "complete run set"):
                validate_menu_smoke_report(run_dir)

    def test_preseal_rejects_rechained_green_with_invalid_event_timestamp(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-preseal-green-event-"
        ) as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-preseal-green"
            )
            report, _replay = build_strict_green_report(run_dir)
            rows = _event_payloads(run_dir)
            rows[1]["at"] = "invalid-date"
            action_path = run_dir / "artifacts" / "00007-action.json"
            action = json.loads(action_path.read_text(encoding="utf-8"))
            _prepare_prefinal_fixture(
                run_dir,
                report,
                rows,
                action=action,
            )
            verified = _verified_artifact_manifest(report, run_dir)
            prefix_rows, prefix_chain = _validated_menu_event_rows(
                run_dir / "events.jsonl"
            )
            before_events = (run_dir / "events.jsonl").read_bytes()
            with self.assertRaisesRegex(AgentError, "event timestamp differs"):
                _validate_preseal_candidate(
                    report,
                    run_dir,
                    verified,
                    prefix_rows,
                    prefix_chain,
                    ok=True,
                )
            self.assertEqual(
                (run_dir / "events.jsonl").read_bytes(), before_events
            )
            self.assertNotIn(
                "smoke_finished", [row["kind"] for row in prefix_rows]
            )
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])

    def test_preseal_rejects_stably_manifested_red_ui_contract_mismatch(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-preseal-red-contract-"
        ) as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-preseal-red"
            )
            report, _replay = build_red_report(run_dir, "clean-pre-input")
            rows = _event_payloads(run_dir)
            _prepare_prefinal_fixture(run_dir, report, rows)
            contract_path = run_dir / UI_CONTRACT_ARCHIVE
            contract_path.write_bytes(contract_path.read_bytes() + b"\n")
            report["artifacts"] = _artifact_manifest(run_dir)
            write_json_atomic(run_dir / "report.json", report)
            verified = _verified_artifact_manifest(report, run_dir)
            prefix_rows, prefix_chain = _validated_menu_event_rows(
                run_dir / "events.jsonl"
            )
            before_events = (run_dir / "events.jsonl").read_bytes()

            def replay_nested_normal(
                path: Path, expected: str
            ) -> dict[str, object]:
                payload = json.loads(
                    (path / "report.json").read_text(encoding="utf-8")
                )
                if payload.get("environment_sha256") != expected:
                    raise AgentError(
                        "fixture normal qualification environment differs"
                    )
                return payload

            def replay_nested_crash(path: Path) -> dict[str, object]:
                return json.loads(
                    (path / "report.json").read_text(encoding="utf-8")
                )

            with mock.patch(
                "xar_autoplayer.menu_smoke._validate_normal_qualification",
                side_effect=replay_nested_normal,
            ), mock.patch(
                "xar_autoplayer.crash_probe.validate_crash_report",
                side_effect=replay_nested_crash,
            ), self.assertRaisesRegex(
                AgentError, "UI contract report binding differs"
            ):
                _validate_preseal_candidate(
                    report,
                    run_dir,
                    verified,
                    prefix_rows,
                    prefix_chain,
                    ok=False,
                )
            self.assertEqual(
                (run_dir / "events.jsonl").read_bytes(), before_events
            )
            self.assertNotIn(
                "smoke_finished", [row["kind"] for row in prefix_rows]
            )
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])

    def test_pre_resume_inventory_envelope_and_row_are_exact(self) -> None:
        mutations = {
            "extra-envelope": lambda value: value.update(extra=True),
            "tasklist-rc": lambda value: value.update(tasklist_returncode=9),
            "tasklist-pids": lambda value: value.update(tasklist_pids=[]),
            "wmi-pids": lambda value: value.update(wmi_pids=[]),
            "wrong-name": lambda value: value["processes"][0].update(
                name="not-ck3.exe"
            ),
            "wrong-parent": lambda value: value["processes"][0].update(
                parent_pid=0
            ),
            "extra-row-key": lambda value: value["processes"][0].update(
                command_line="forged"
            ),
            "bad-creation": lambda value: value["processes"][0].update(
                creation_date="not-a-process-time"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-inventory-{label}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                report, replay = build_strict_green_report(run_dir)
                mutate(report["process"]["pre_resume_ck3_inventory"])
                write_json_atomic(run_dir / "report.json", report)
                _resign_after_artifact_mutation(run_dir)
                with self.assertRaisesRegex(AgentError, "process contract"):
                    self._validate_strict(run_dir, replay)

    def test_foreground_attestation_is_bound_to_events_and_rejects_input_claim(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-foreground-proof-") as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-12345678"
            )
            report, replay = build_strict_green_report(run_dir)
            rows = _event_payloads(run_dir)
            attestation = report["navigation_attestation"]["foreground_activation"]
            attestation["synthetic_input"] = True
            finished = next(
                row
                for row in rows
                if row["kind"] == "foreground_activation_finished"
            )
            finished["attestation"] = dict(attestation)
            action = report["navigation_attestation"]["transition"]["action"]
            _refinalize_green_fixture(run_dir, report, rows, action)
            with self.assertRaisesRegex(AgentError, "foreground activation"):
                self._validate_strict(run_dir, replay)

    def test_foreground_direct_attestation_accepts_null_initial_foreground(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-null-foreground-") as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-12345678"
            )
            report, replay = build_strict_green_report(run_dir)
            rows = _event_payloads(run_dir)
            attestation = report["navigation_attestation"]["foreground_activation"]
            attestation.update(
                {
                    "foreground_hwnd_before": 0,
                    "foreground_thread_id_before": 0,
                    "foreground_pid_before": 0,
                    "mode": "direct",
                }
            )
            finished = next(
                row
                for row in rows
                if row["kind"] == "foreground_activation_finished"
            )
            finished["attestation"] = dict(attestation)
            action = report["navigation_attestation"]["transition"]["action"]
            _refinalize_green_fixture(run_dir, report, rows, action)
            self.assertTrue(self._validate_strict(run_dir, replay)["ok"])

    def test_foreground_events_reject_resigned_extra_input_claims(self) -> None:
        mutations = {
            "planned": (
                "foreground_activation_planned",
                "synthetic_input_may_have_occurred",
            ),
            "armed": ("foreground_activation_armed", "synthetic_input"),
            "finished": ("foreground_activation_finished", "synthetic_input"),
        }
        for label, (kind, key) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-foreground-event-{label}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                report, replay = build_strict_green_report(run_dir)
                rows = _event_payloads(run_dir)
                next(row for row in rows if row["kind"] == kind)[key] = True
                action = report["navigation_attestation"]["transition"]["action"]
                _refinalize_green_fixture(run_dir, report, rows, action)
                with self.assertRaisesRegex(AgentError, "event schema"):
                    self._validate_strict(run_dir, replay)

    def test_public_validator_rejects_resigned_invalid_event_timestamp(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-event-time-") as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-12345678"
            )
            report, replay = build_strict_green_report(run_dir)
            rows = _event_payloads(run_dir)
            next(
                row
                for row in rows
                if row["kind"] == "foreground_activation_armed"
            )["at"] = "not-a-time"
            action = report["navigation_attestation"]["transition"]["action"]
            _refinalize_green_fixture(run_dir, report, rows, action)
            with self.assertRaisesRegex(AgentError, "event timestamp"):
                self._validate_strict(run_dir, replay)

    def test_public_validator_allows_wmi_path_visibility_to_vary_across_bindings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-wmi-visibility-") as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-12345678"
            )
            report, replay = build_strict_green_report(run_dir)
            rows = _event_payloads(run_dir)
            action = report["navigation_attestation"]["transition"]["action"]
            expected_executable = report["process"]["executable"]
            action["binding"]["process"]["wmi_executable"] = ""
            action["binding_after"]["process"]["wmi_executable"] = expected_executable
            report["navigation_attestation"]["window_binding"]["process"][
                "wmi_executable"
            ] = ""
            armed = next(row for row in rows if row["kind"] == "ui_input_armed")
            armed["binding"] = action["binding"]
            _refinalize_green_fixture(run_dir, report, rows, action)
            self.assertTrue(self._validate_strict(run_dir, replay)["ok"])

    def test_public_validator_rejects_png_observation_process_and_event_tamper(
        self,
    ) -> None:
        mutations = {
            "png": lambda run: (run / "artifacts" / "frame-01.png").write_bytes(
                b"not-the-recorded-png"
            ),
            "observation": lambda run: (run / "artifacts" / "frame-01.observation.json").write_text(
                "{}\n", encoding="utf-8"
            ),
            "process": lambda run: _tamper_report_process(run),
            "event": lambda run: _tamper_event_digest(run),
            "fresh-envelope": lambda run: _tamper_fresh_observation_envelope(run),
            "private-reference": lambda run: _tamper_private_artifact_reference(run),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-{label}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                _report, replay = build_strict_green_report(run_dir)
                mutate(run_dir)
                with self.assertRaises(AgentError):
                    self._validate_strict(run_dir, replay)

    def test_public_validator_rejects_resigned_core_proof_tampering(self) -> None:
        def failure_field(key: str, value: object):
            def mutate(run: Path) -> None:
                report_path = run / "report.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                report[key] = value
                write_json_atomic(report_path, report)
                _resign_after_artifact_mutation(run)

            return mutate

        def process_field(key: str, value: object):
            def mutate(run: Path) -> None:
                report_path = run / "report.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                report["process"][key] = value
                write_json_atomic(report_path, report)
                _resign_after_artifact_mutation(run)

            return mutate

        def mutate_missing_final_debug(run: Path) -> None:
            report_path = run / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["load_attestation"].pop("post_exit_debug_log")
            load_path = run / "artifacts" / "supervisor-load-attestation.json"
            load = json.loads(load_path.read_text(encoding="utf-8"))
            load.pop("post_exit_debug_log")
            write_json_atomic(load_path, load)
            (run / "artifacts" / "runtime-debug-post-exit.log").unlink()
            write_json_atomic(report_path, report)
            _resign_after_artifact_mutation(run)

        def mutate_forged_diagnostic(run: Path) -> None:
            report_path = run / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            path = run / "artifacts" / "supervisor-error.log"
            raw = b"[E][audit] xar_forged diagnostic\n"
            path.write_bytes(raw)
            report["engine_diagnostics"] = {
                "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
                "zero_diagnostics": False,
                "current_mod_diagnostics": False,
                "current_mod_diagnostic_hits": [],
                "logs": {
                    "error.log": {
                        "present": True,
                        "path": "artifacts/supervisor-error.log",
                        "sha256": sha256_file(path),
                        "size": len(raw),
                        "mtime_ns": 1,
                        "diagnostic_records": 1,
                        "nonempty_lines": 1,
                    },
                    "gui_warnings.log": {"present": False, "diagnostic_records": 0},
                },
            }
            write_json_atomic(report_path, report)
            _resign_after_artifact_mutation(run)

        def mutate_honest_current_mod_diagnostic(run: Path) -> None:
            report_path = run / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            environment = json.loads(
                (run / "environment.json").read_text(encoding="utf-8")
            )
            path = run / "artifacts" / "supervisor-error.log"
            raw = b"[E][audit] xar_forged current-mod diagnostic\n"
            path.write_bytes(raw)
            analysis = analyze_engine_log_bytes(
                "error.log",
                raw,
                expected_mod_name=EXPECTED_MOD_NAME,
                production_path=Path(environment["mod"]["production_path"]),
            )
            hits = analysis["current_mod_diagnostic_hits"]
            self.assertTrue(hits)
            report["engine_diagnostics"] = {
                "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
                "zero_diagnostics": False,
                "current_mod_diagnostics": True,
                "current_mod_diagnostic_hits": hits,
                "logs": {
                    "error.log": {
                        "present": True,
                        "path": "artifacts/supervisor-error.log",
                        "sha256": sha256_file(path),
                        "size": len(raw),
                        "mtime_ns": 1,
                        "diagnostic_records": analysis["diagnostic_records"],
                        "nonempty_lines": analysis["nonempty_lines"],
                    },
                    "gui_warnings.log": {
                        "present": False,
                        "diagnostic_records": 0,
                    },
                },
            }
            write_json_atomic(report_path, report)
            _resign_after_artifact_mutation(run)

        def mutate_stale_empty_diagnostic(run: Path) -> None:
            report_path = run / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            path = run / "artifacts" / "supervisor-error.log"
            raw = b""
            path.write_bytes(raw)
            report["engine_diagnostics"] = {
                "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
                "zero_diagnostics": True,
                "current_mod_diagnostics": False,
                "current_mod_diagnostic_hits": [],
                "logs": {
                    "error.log": {
                        "present": True,
                        "path": "artifacts/supervisor-error.log",
                        "sha256": sha256_file(path),
                        "size": 0,
                        "mtime_ns": 0,
                        "diagnostic_records": 0,
                        "nonempty_lines": 0,
                    },
                    "gui_warnings.log": {
                        "present": False,
                        "diagnostic_records": 0,
                    },
                },
            }
            write_json_atomic(report_path, report)
            _resign_after_artifact_mutation(run)

        def mutate_missing_shutdown_identity(run: Path) -> None:
            report_path = run / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["shutdown_attestation"]["nonce"] = None
            report["shutdown_attestation"]["control_files_absent"] = None
            write_json_atomic(report_path, report)
            _resign_after_artifact_mutation(run)

        def mutate_observation_schema(run: Path) -> None:
            path = run / "artifacts" / "frame-02.observation.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["policy_observation"]["caller_coordinates"] = [1, 2]
            write_json_atomic(path, payload)
            report_path = run / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["navigation_attestation"]["start_observation"][
                "caller_coordinates"
            ] = [1, 2]
            write_json_atomic(report_path, report)
            _resign_after_artifact_mutation(run)

        cases = {
            "missing-final-debug": mutate_missing_final_debug,
            "forged-diagnostic": mutate_forged_diagnostic,
            "honest-current-mod-diagnostic": mutate_honest_current_mod_diagnostic,
            "stale-empty-diagnostic": mutate_stale_empty_diagnostic,
            "missing-shutdown-identity": mutate_missing_shutdown_identity,
            "observation-schema": mutate_observation_schema,
            "fresh-log-epoch": process_field("fresh_log_epoch_ns", 2),
            "prelaunch-logs": process_field(
                "prelaunch_logs_removed", ["debug.log"]
            ),
            "green-error": failure_field("error", "runtime: AgentError: forged"),
            "green-error-type": failure_field("error_type", "AgentError"),
            "green-interrupted": failure_field("interrupted", True),
            "green-secondary-errors": failure_field(
                "secondary_errors", ["postflight: forged"]
            ),
            "green-unsafe-cleanup": failure_field("unsafe_cleanup", True),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-core-{label}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                _report, replay = build_strict_green_report(run_dir)
                mutate(run_dir)
                with self.assertRaises(AgentError):
                    self._validate_strict(run_dir, replay)

    def test_archived_environment_requires_clean_tracked_provenance(self) -> None:
        for mutation in ("runtime-dirty", "mod-untracked"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-environment-{mutation}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                report, _replay = build_strict_green_report(run_dir)
                environment_path = run_dir / "environment.json"
                environment = json.loads(
                    environment_path.read_text(encoding="utf-8")
                )
                if mutation == "runtime-dirty":
                    runtime = environment["agent_runtime"]
                    runtime["git"]["dirty"] = True
                    runtime["git"]["status"] = [" M forged.py"]
                    runtime_without_hash = dict(runtime)
                    runtime_without_hash.pop("sha256", None)
                    runtime["sha256"] = snapshot_digest(runtime_without_hash)
                else:
                    provenance = environment["mod"]["source_provenance"]
                    provenance["all_release_files_tracked"] = False
                    provenance["untracked_release_files"] = ["forged.txt"]
                environment["environment_sha256"] = _contract_digest(environment)
                write_json_atomic(environment_path, environment)
                report["environment_sha256"] = environment["environment_sha256"]
                verified = {
                    str(item["path"]): run_dir / str(item["path"])
                    for item in report["artifacts"]
                }
                with self.assertRaisesRegex(AgentError, "environment semantics"):
                    _validate_archived_environment(report, verified)

    def test_public_validator_replays_red_lifecycle_variants(self) -> None:
        for mode in (
            "clean-pre-input",
            "foreground-failed",
            "foreground-completed-no-observation",
            "armed-wal-failed-before-commit",
            "failed-after-input",
            "cleanup-contract-error",
            "unsafe-cleanup",
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-red-{mode}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                _report, replay = build_red_report(run_dir, mode)
                validated = self._validate_strict(run_dir, replay)
                self.assertFalse(validated["ok"])

    def test_shutdown_result_and_cleanup_claim_match_runtime_reachable_states(self) -> None:
        mutations = {
            "ok-with-errors": (True, ["forged contract error"]),
            "not-ok-without-errors": (False, []),
            "returned-unproven-cleanup": (False, ["forged contract error"]),
        }
        for label, (ok, errors) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-shutdown-{label}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                report, replay = build_red_report(
                    run_dir, "cleanup-contract-error"
                )
                report["shutdown_attestation"]["ok"] = ok
                report["shutdown_attestation"]["contract_errors"] = errors
                if label == "returned-unproven-cleanup":
                    report["shutdown_attestation"]["cleanup_proven"] = False
                write_json_atomic(run_dir / "report.json", report)
                _resign_after_artifact_mutation(run_dir)
                with self.assertRaisesRegex(
                    AgentError, "shutdown contract result|cleanup claim"
                ):
                    self._validate_strict(run_dir, replay)

    def test_actual_driver_committed_callback_failures_replay_as_menu_red(
        self,
    ) -> None:
        for failure_kind in ("ui_input_armed", "ui_action_finished"):
            with self.subTest(failure_kind=failure_kind), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-driver-{failure_kind}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                report, replay = build_strict_green_report(run_dir)
                original_rows = _event_payloads(run_dir)
                events = run_dir / "events.jsonl"
                events.unlink()
                for row in original_rows:
                    append_event(events, row)
                    if row["kind"] == "visible_main_menu_attested":
                        break
                old_action = run_dir / "artifacts" / "00007-action.json"
                old_action.unlink()
                for suffix in ("hover-patch.png", "final-patch.png"):
                    (run_dir / "artifacts" / f"00007-action.{suffix}").unlink()

                def durable(event: dict[str, object]) -> str:
                    digest = append_event(events, event)
                    if event["kind"] == failure_kind:
                        raise OSError(f"committed {failure_kind} callback failed")
                    return digest

                driver, token, window = _strict_driver(run_dir, report, durable)
                fresh = _archived_observation(run_dir, 3)
                hover = _archived_observation(run_dir, 4)
                after = StableObservation(
                    "bookmark_lobby",
                    (
                        _archived_observation(run_dir, 5),
                        _archived_observation(run_dir, 6),
                    ),
                )
                with Image.open(run_dir / hover.screenshot) as source:
                    source.load()
                    hover_image = source.copy()
                window.capture_patch.side_effect = lambda bbox: hover_image.crop(bbox)
                fake_gui = types.SimpleNamespace(
                    FAILSAFE=True,
                    moveTo=mock.Mock(),
                )
                submit = mock.Mock(return_value=(2, 0))
                with mock.patch.object(
                    driver, "_capture_observation", return_value=fresh
                ), mock.patch.object(
                    driver,
                    "_capture_observation_with_image",
                    return_value=(hover, hover_image),
                ), mock.patch.object(
                    driver, "observe_stable", return_value=after
                ), mock.patch.dict(
                    sys.modules, {"pyautogui": fake_gui}
                ), mock.patch(
                    "xar_autoplayer.control.executor._prepare_left_click_batch",
                    return_value=submit,
                ), mock.patch(
                    "xar_autoplayer.control.executor.time.sleep"
                ):
                    with self.assertRaisesRegex(AgentError, "committed"):
                        driver.click_visible_control(token, timeout_seconds=1)
                if failure_kind == "ui_input_armed":
                    fake_gui.moveTo.assert_not_called()
                    submit.assert_not_called()
                else:
                    submit.assert_called_once_with()

                for kind in ("tracked_process_stopped", "postflight_attested"):
                    append_event(
                        events,
                        next(row for row in original_rows if row["kind"] == kind),
                    )
                report.pop("navigation_attestation")
                report["error"] = f"OSError: committed {failure_kind} callback failed"
                report["error_type"] = "AgentError"
                report["finalized"] = False
                report["ok"] = False
                report["artifacts"] = _artifact_manifest(run_dir)
                body = _report_body_sha256(report)
                report["report_body_sha256"] = body
                report["final_event_sha256"] = append_event(
                    events,
                    {
                        "kind": "smoke_finished",
                        "ok": False,
                        "report_body_sha256": body,
                    },
                )
                report["finalized"] = True
                chain = validate_event_chain(events)
                report["event_chain"] = {
                    "event_count": chain["event_count"],
                    "tail_sha256": chain["tail_sha256"],
                }
                write_json_atomic(run_dir / "report.json", report)
                validated = self._validate_strict(run_dir, replay)
                self.assertFalse(validated["ok"])

    def test_actual_driver_visual_guard_failures_replay_as_menu_red(self) -> None:
        for failure_kind in ("fresh-screen", "hover-screen", "final-pixels"):
            with self.subTest(failure_kind=failure_kind), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-driver-{failure_kind}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                report, replay = build_strict_green_report(run_dir)
                original_rows = _event_payloads(run_dir)
                events = run_dir / "events.jsonl"
                events.unlink()
                for row in original_rows:
                    append_event(events, row)
                    if row["kind"] == "visible_main_menu_attested":
                        break
                (run_dir / "artifacts" / "00007-action.json").unlink()
                for suffix in ("hover-patch.png", "final-patch.png"):
                    (run_dir / "artifacts" / f"00007-action.{suffix}").unlink()

                driver, token, window = _strict_driver(
                    run_dir, report, lambda event: append_event(events, event)
                )
                fresh = _archived_observation(run_dir, 3)
                hover = _archived_observation(run_dir, 4)
                unexpected = _archived_observation(run_dir, 5)
                with Image.open(run_dir / hover.screenshot) as source:
                    source.load()
                    hover_image = source.copy()
                with Image.open(run_dir / unexpected.screenshot) as source:
                    source.load()
                    unexpected_image = source.copy()

                capture_observation = fresh
                capture_with_image = (hover, hover_image)
                if failure_kind == "fresh-screen":
                    capture_observation = unexpected
                elif failure_kind == "hover-screen":
                    capture_with_image = (unexpected, unexpected_image)
                else:
                    def changed_patch(bbox):
                        patch = hover_image.crop(bbox)
                        changed = patch.copy()
                        pixel = changed.getpixel((0, 0))
                        changed.putpixel((0, 0), tuple(255 - int(value) for value in pixel))
                        return changed

                    window.capture_patch.side_effect = changed_patch

                fake_gui = types.SimpleNamespace(FAILSAFE=True, moveTo=mock.Mock())
                submit = mock.Mock(return_value=(2, 0))
                with mock.patch.object(
                    driver, "_capture_observation", return_value=capture_observation
                ), mock.patch.object(
                    driver,
                    "_capture_observation_with_image",
                    return_value=capture_with_image,
                ), mock.patch.dict(
                    sys.modules, {"pyautogui": fake_gui}
                ), mock.patch(
                    "xar_autoplayer.control.executor._prepare_left_click_batch",
                    return_value=submit,
                ), mock.patch(
                    "xar_autoplayer.control.executor.time.sleep"
                ):
                    with self.assertRaises(AgentError) as raised:
                        driver.click_visible_control(token, timeout_seconds=1)
                submit.assert_not_called()

                for kind in ("tracked_process_stopped", "postflight_attested"):
                    append_event(
                        events,
                        next(row for row in original_rows if row["kind"] == kind),
                    )
                report.pop("navigation_attestation")
                report["error"] = f"{type(raised.exception).__name__}: {raised.exception}"
                report["error_type"] = type(raised.exception).__name__
                report["finalized"] = False
                report["ok"] = False
                report["artifacts"] = _artifact_manifest(run_dir)
                body = _report_body_sha256(report)
                report["report_body_sha256"] = body
                report["final_event_sha256"] = append_event(
                    events,
                    {
                        "kind": "smoke_finished",
                        "ok": False,
                        "report_body_sha256": body,
                    },
                )
                report["finalized"] = True
                chain = validate_event_chain(events)
                report["event_chain"] = {
                    "event_count": chain["event_count"],
                    "tail_sha256": chain["tail_sha256"],
                }
                write_json_atomic(run_dir / "report.json", report)
                validated = self._validate_strict(run_dir, replay)
                self.assertFalse(validated["ok"])

    def test_public_validator_rejects_resigned_red_semantic_tampering(self) -> None:
        cases = (
            ("clean-pre-input", "protected-after"),
            ("failed-after-input", "armed-receipt"),
            ("unsafe-cleanup", "smuggled-postflight"),
        )
        for mode, mutation in cases:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-red-tamper-{mutation}-"
            ) as temporary:
                run_dir = (
                    Path(temporary).resolve()
                    / "20260822T000000Z-menu-12345678"
                )
                _report, replay = build_red_report(run_dir, mode)
                report_path = run_dir / "report.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                if mutation == "protected-after":
                    after_path = run_dir / "protected-after.json.gz"
                    with gzip.open(after_path, "rt", encoding="utf-8") as source:
                        after = json.load(source)
                    after["stores"]["real_profile"]["forged"] = {"sha256": "0" * 64}
                    after["digest"] = snapshot_digest(after["stores"])
                    write_gzip_json_atomic(after_path, after)
                    report["protected_storage"]["after_snapshot_sha256"] = sha256_file(
                        after_path
                    )
                elif mutation == "armed-receipt":
                    action_path = run_dir / "artifacts" / "00007-action.json"
                    action = json.loads(action_path.read_text(encoding="utf-8"))
                    action["durable_events"]["armed"] = "0" * 64
                    write_json_atomic(action_path, action)
                elif mutation == "smuggled-postflight":
                    shutil.copy2(
                        run_dir / "protected-before.json.gz",
                        run_dir / "protected-after.json.gz",
                    )
                    report["protected_storage"] = {
                        "post_exit_matches_baseline": True
                    }
                else:  # pragma: no cover - the fixed matrix is exhaustive.
                    raise AssertionError(mutation)
                write_json_atomic(report_path, report)
                _resign_after_artifact_mutation(run_dir)
                with self.assertRaises(AgentError):
                    self._validate_strict(run_dir, replay)

    def test_replay_leaf_rejects_invalid_png_before_ocr(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-invalid-png-") as temporary:
            path = Path(temporary).resolve() / "invalid.png"
            path.write_bytes(b"not a png")
            contract = SimpleNamespace(resolution=(2560, 1440))
            with self.assertRaisesRegex(AgentError, "valid PNG"):
                _replay_visible_frame(path, contract)

    def test_green_report_binds_full_artifact_set_body_and_single_action(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-report-") as temporary:
            run_dir = Path(temporary).resolve() / "20260822T000000Z-menu-12345678"
            build_green_report(run_dir)
            with mock.patch(
                "xar_autoplayer.menu_smoke._validate_success_payload"
            ):
                validated = validate_menu_smoke_report(run_dir)
            self.assertTrue(validated["ok"])
            self.assertEqual(
                [row["kind"] for row in (
                    json.loads(line)
                    for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                )],
                list(GREEN_EVENT_ORDER),
            )

    def test_report_body_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-tamper-") as temporary:
            run_dir = Path(temporary).resolve() / "20260822T000000Z-menu-12345678"
            report = build_green_report(run_dir)
            report["acceptance_claim"] = "inflated"
            write_json_atomic(run_dir / "report.json", report)
            with self.assertRaises(AgentError):
                validate_menu_smoke_report(run_dir)

    def test_unmanifested_ui_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-extra-") as temporary:
            run_dir = Path(temporary).resolve() / "20260822T000000Z-menu-12345678"
            build_green_report(run_dir)
            (run_dir / "artifacts" / "unbound-frame.png").write_bytes(b"pixels")
            with mock.patch(
                "xar_autoplayer.menu_smoke._validate_success_payload"
            ), self.assertRaisesRegex(AgentError, "complete run set"):
                validate_menu_smoke_report(run_dir)


class CanonicalContractTests(unittest.TestCase):
    def test_contract_source_bytes_are_bound_to_environment_inventory(self) -> None:
        source = ROOT.parent / UI_CONTRACT_REPOSITORY_RELATIVE
        raw = source.read_bytes()
        manifest = {
            "agent_runtime": {
                "files": [
                    {
                        "path": UI_CONTRACT_AGENT_RUNTIME_PATH,
                        "size": len(raw),
                        "sha256": sha256_file(source),
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory(prefix="xar-menu-contract-") as temporary:
            run_dir = Path(temporary).resolve()
            evidence = _archive_ui_contract(manifest, run_dir)
            self.assertEqual(evidence["sha256"], sha256_file(source))
            self.assertEqual((run_dir / UI_CONTRACT_ARCHIVE).read_bytes(), raw)

    def test_contract_environment_hash_mismatch_is_rejected(self) -> None:
        source = ROOT.parent / UI_CONTRACT_REPOSITORY_RELATIVE
        manifest = {
            "agent_runtime": {
                "files": [
                    {
                        "path": UI_CONTRACT_AGENT_RUNTIME_PATH,
                        "size": source.stat().st_size,
                        "sha256": "0" * 64,
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory(prefix="xar-menu-contract-red-") as temporary:
            with self.assertRaisesRegex(AgentError, "differ"):
                _archive_ui_contract(manifest, Path(temporary).resolve())

    def test_visible_ui_schemas_reject_invalid_rfc3339_timestamps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-schema-time-") as temporary:
            run_dir = (
                Path(temporary).resolve()
                / "20260822T000000Z-menu-12345678"
            )
            report, _replay = build_strict_green_report(run_dir)
            action = report["navigation_attestation"]["transition"]["action"]
            action["planned_at"] = "invalid-date"
            with self.assertRaisesRegex(AgentError, "Draft 2020-12 schema"):
                _validate_json_schema(
                    action, ACTION_RECEIPT_SCHEMA, "invalid action timestamp"
                )
            archived = json.loads(
                (
                    run_dir / "artifacts" / "frame-01.observation.json"
                ).read_text(encoding="utf-8")
            )
            observation = archived["policy_observation"]
            observation["captured_at"] = "invalid-date"
            with self.assertRaisesRegex(AgentError, "Draft 2020-12 schema"):
                _validate_json_schema(
                    observation, OBSERVATION_SCHEMA, "invalid observation timestamp"
                )


class MenuLifecycleTests(unittest.TestCase):
    def _run(
        self,
        root: Path,
        scenario_error: BaseException | None = None,
        cleanup: bool = True,
        post_exit_write_failure: str | None = None,
        process_pid_failure: BaseException | None = None,
        shutdown_contract_error: bool = False,
        final_report_write_failure: str | None = None,
    ):
        spec = EnvironmentSpec((root / "state").resolve(), (root / "game").resolve())
        spec.production_dir.mkdir(parents=True)
        (spec.production_dir / "payload.txt").write_text("production", encoding="utf-8")
        spec.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        spec.manifest_path.write_text("{}\n", encoding="utf-8")
        production_source = root / "source-production.manifest.json"
        production_source.write_text("{}\n", encoding="utf-8")
        manifest = {
            "environment_sha256": "a" * 64,
            "agent_runtime": {
                "git": {
                    "all_files_tracked": True,
                    "dirty": False,
                    "selected_runtime_revision": "b" * 40,
                },
                "files": [],
            },
            "display": {"language": "l_simp_chinese", "resolution": [2560, 1440]},
            "mod": {
                "production_manifest": str(production_source.resolve()),
                "production_tree_sha256": snapshot_digest(tree_snapshot(spec.production_dir)),
                "source_provenance": {"release_source_sha256": "c" * 64},
            },
        }
        class LifecycleProcess:
            returncode = 1

            def __init__(self) -> None:
                self.pid_reads = 0

            @property
            def pid(self) -> int:
                self.pid_reads += 1
                if self.pid_reads == 1 and process_pid_failure is not None:
                    raise process_pid_failure
                return 42

            @staticmethod
            def poll():
                return None

        process = LifecycleProcess()
        handle = SimpleNamespace(
            process=process,
            ck3_creation_date="20260822000000.000000+000",
            watchdog_pid=43,
            command=[str(spec.game_exe), "-gdpr-compliant"],
            log_epoch_ns=1,
            cleared_logs=[],
            pre_resume_inventory={"processes": [{"pid": 42}]},
        )
        load = load_attestation()
        load.pop("post_exit_revalidated")
        load.pop("post_exit_debug_log")

        def archive_contract(_manifest, run_dir):
            path = run_dir / UI_CONTRACT_ARCHIVE
            path.write_bytes(b"contract")
            return {
                "agent_runtime_path": UI_CONTRACT_AGENT_RUNTIME_PATH,
                "source_repository_relative": UI_CONTRACT_REPOSITORY_RELATIVE.as_posix(),
                "archive_path": UI_CONTRACT_ARCHIVE,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }

        def scenario(_spec, _handle, _manifest, artifacts, events, *_args):
            if scenario_error is not None:
                raise scenario_error
            navigation = navigation_payload()
            action = navigation["transition"]["action"]
            write_json_atomic(artifacts / "00001-action.json", action)
            append_event(
                events,
                {
                    "kind": "foreground_activation_planned",
                    "pid": 42,
                    "hwnd": 84,
                    "operation": "exact_hwnd_foreground_without_synthetic_input",
                    "synthetic_input": False,
                },
            )
            append_event(
                events,
                {
                    "kind": "foreground_activation_armed",
                    "pid": 42,
                    "hwnd": 84,
                    "operation": "exact_hwnd_foreground_without_synthetic_input",
                    "foreground_may_have_changed": True,
                    "synthetic_input_may_have_occurred": False,
                },
            )
            append_event(
                events,
                {
                    "kind": "foreground_activation_finished",
                    "pid": 42,
                    "hwnd": 84,
                    "status": "confirmed",
                    "attestation": navigation["foreground_activation"],
                },
            )
            append_event(events, {"kind": "visible_main_menu_attested"})
            append_event(events, {"kind": "ui_action_planned", "action_id": action["action_id"], "control_id": "main_menu.new_game"})
            append_event(events, {"kind": "ui_input_armed", "action_id": action["action_id"]})
            append_event(events, {"kind": "ui_action_finished", "action_id": action["action_id"], "status": "confirmed"})
            append_event(events, {"kind": "bookmark_lobby_attested"})
            return navigation

        def archive_load(_spec, evidence, artifacts):
            archived = dict(evidence)
            write_json_atomic(
                artifacts / "supervisor-load-attestation.json", archived
            )
            return archived

        def archive_debug(_spec, _debug, artifacts, archive_name):
            path = artifacts / archive_name
            path.write_bytes(b"fresh debug prefix\n")
            return {
                "path": str(spec.profile_dir / "logs" / "debug.log"),
                "captured_prefix_size": path.stat().st_size,
                "captured_prefix_sha256": sha256_file(path),
                "file_size_after_read": path.stat().st_size,
                "mtime_ns": 1,
                "prelaunch_epoch_ns": 1,
                "cleared_before_launch": [],
                "archive_path": f"artifacts/{archive_name}",
                "archive_sha256": sha256_file(path),
            }

        def validate_final(run_dir):
            return json.loads((run_dir / "report.json").read_text(encoding="utf-8"))

        shutdown = {
            "ck3_pid": 42,
            "ck3_creation_date": handle.ck3_creation_date,
            "watchdog_pid": handle.watchdog_pid,
            "cleanup_proven": cleanup,
            "ok": not shutdown_contract_error,
            "contract_errors": (
                ["CK3 exited before a require-running stop"]
                if shutdown_contract_error
                else []
            ),
        }
        current_mod = {
            "git_dirty": False,
            "all_release_files_tracked": True,
            "git_revision": "d" * 40,
            "release_source_sha256": "c" * 64,
        }
        qualification_evidence = {
            "environment_sha256": "a" * 64,
            "normal": {"run_id": "normal-fixture"},
            "crash": {"run_id": "crash-fixture"},
            "normal_finished_at": "2026-08-22T00:00:00+00:00",
            "crash_started_at": "2026-08-22T00:01:00+00:00",
        }
        post_exit_failure_injected = False
        final_report_failure_injected = False

        def lifecycle_write_json(path, payload):
            nonlocal post_exit_failure_injected, final_report_failure_injected
            is_post_exit_load = (
                Path(path).name == "supervisor-load-attestation.json"
                and isinstance(payload, dict)
                and payload.get("post_exit_revalidated") is True
            )
            if (
                is_post_exit_load
                and post_exit_write_failure
                and not post_exit_failure_injected
            ):
                post_exit_failure_injected = True
                if post_exit_write_failure == "after-commit":
                    write_json_atomic(path, payload)
                raise OSError(
                    f"synthetic post-exit load {post_exit_write_failure} write failure"
                )
            is_final_report = (
                Path(path).name == "report.json"
                and isinstance(payload, dict)
                and payload.get("finalized") is True
            )
            if (
                is_final_report
                and final_report_write_failure
                and not final_report_failure_injected
            ):
                final_report_failure_injected = True
                if final_report_write_failure == "after-commit":
                    write_json_atomic(path, payload)
                raise OSError(
                    "synthetic final report "
                    f"{final_report_write_failure} write failure"
                )
            return write_json_atomic(path, payload)

        patches = (
            mock.patch("xar_autoplayer.menu_smoke.verify_profile", return_value=manifest),
            mock.patch("xar_autoplayer.menu_smoke.doctor"),
            mock.patch("xar_autoplayer.menu_smoke.mod_source_fingerprint", return_value=current_mod),
            mock.patch("xar_autoplayer.menu_smoke._require_menu_qualification", return_value={}),
            mock.patch("xar_autoplayer.menu_smoke._archive_menu_qualification", return_value=qualification_evidence),
            mock.patch("xar_autoplayer.menu_smoke.ck3_process_inventory", return_value={"processes": []}),
            mock.patch("xar_autoplayer.menu_smoke.protected_snapshot", return_value={"digest": "e" * 64}),
            mock.patch("xar_autoplayer.menu_smoke.verify_protected_unchanged", return_value={"digest": "e" * 64}),
            mock.patch("xar_autoplayer.menu_smoke._archive_ui_contract", side_effect=archive_contract),
            mock.patch("xar_autoplayer.menu_smoke._archive_runtime_attestation", side_effect=archive_load),
            mock.patch("xar_autoplayer.menu_smoke._archive_runtime_debug_prefix", side_effect=archive_debug),
            mock.patch("xar_autoplayer.menu_smoke.launch", return_value=handle),
            mock.patch("xar_autoplayer.menu_smoke.wait_for_runtime_attestation", side_effect=[dict(load), dict(load)]),
            mock.patch("xar_autoplayer.menu_smoke._run_menu_scenario", side_effect=scenario),
            mock.patch("xar_autoplayer.menu_smoke.stop_tracked", return_value=shutdown),
            mock.patch("xar_autoplayer.menu_smoke.collect_engine_log_evidence", return_value={"current_mod_diagnostics": False}),
            mock.patch("xar_autoplayer.menu_smoke._validate_menu_report_base_contract"),
            mock.patch("xar_autoplayer.menu_smoke._validate_event_semantics"),
            mock.patch("xar_autoplayer.menu_smoke._validate_success_payload"),
            mock.patch("xar_autoplayer.menu_smoke._validate_red_payload"),
            mock.patch("xar_autoplayer.menu_smoke.validate_menu_smoke_report", side_effect=validate_final),
            mock.patch(
                "xar_autoplayer.menu_smoke.write_json_atomic",
                side_effect=lifecycle_write_json,
            ),
        )
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        return spec, handle

    def test_green_lifecycle_loads_before_one_action_and_then_stops(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-life-") as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            report = _menu_smoke_locked(spec, 30)
            self.assertTrue(report["ok"])
            self.assertTrue(report["shutdown_attestation"]["cleanup_proven"])
            self.assertFalse(report["valid_score_episode"])

    def test_physical_cleanup_with_shutdown_contract_error_keeps_postflight(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-stop-red-") as temporary:
            spec, _handle = self._run(
                Path(temporary).resolve(), shutdown_contract_error=True
            )
            with self.assertRaisesRegex(AgentError, "shutdown contract errors"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertTrue(report["shutdown_attestation"]["cleanup_proven"])
            self.assertFalse(report["shutdown_attestation"]["ok"])
            self.assertTrue(report["shutdown_attestation"]["contract_errors"])
            self.assertIn("protected_storage", report)
            self.assertNotIn("unsafe_cleanup", report)

    def test_committed_final_event_exception_does_not_duplicate_tail(self) -> None:
        for scenario_error in (None, AgentError("synthetic scenario RED")):
            label = "green" if scenario_error is None else "red"
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-final-event-{label}-"
            ) as temporary:
                spec, _handle = self._run(
                    Path(temporary).resolve(), scenario_error=scenario_error
                )
                injected = False

                def append_then_raise(path, payload):
                    nonlocal injected
                    digest = append_event(path, payload)
                    if payload.get("kind") == "smoke_finished" and not injected:
                        injected = True
                        raise OSError("synthetic committed final WAL failure")
                    return digest

                with mock.patch(
                    "xar_autoplayer.menu_smoke.append_event",
                    side_effect=append_then_raise,
                ):
                    if scenario_error is None:
                        result = _menu_smoke_locked(spec, 30)
                        self.assertTrue(result["ok"])
                    else:
                        with self.assertRaisesRegex(AgentError, "menu smoke failed"):
                            _menu_smoke_locked(spec, 30)
                run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
                report = json.loads(
                    (run_dir / "report.json").read_text(encoding="utf-8")
                )
                chain = validate_event_chain(run_dir / "events.jsonl")
                kinds = [
                    json.loads(line)["kind"]
                    for line in (run_dir / "events.jsonl").read_text(
                        encoding="utf-8"
                    ).splitlines()
                ]
                self.assertEqual(kinds.count("smoke_finished"), 1)
                self.assertTrue(report["finalized"])
                self.assertEqual(report["final_event_sha256"], chain["tail_sha256"])
                self.assertIs(report["ok"], scenario_error is None)

    def test_committed_final_event_without_recovery_fsync_never_goes_green(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-final-event-undurable-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            injected = False

            def append_then_raise(path, payload):
                nonlocal injected
                digest = append_event(path, payload)
                if payload.get("kind") == "smoke_finished" and not injected:
                    injected = True
                    raise OSError("synthetic uncertain final WAL fsync")
                return digest

            with mock.patch(
                "xar_autoplayer.menu_smoke.append_event",
                side_effect=append_then_raise,
            ), mock.patch(
                "xar_autoplayer.menu_smoke._fsync_existing_file",
                side_effect=OSError("synthetic recovery barrier failure"),
            ), self.assertRaisesRegex(OSError, "uncertain final WAL fsync"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            provisional = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(provisional["finalized"])
            self.assertFalse(provisional["ok"])

    def test_actual_final_row_cannot_bypass_prevalidated_timestamp(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-final-event-split-clock-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())

            def replace_only_actual_final_timestamp(
                path: Path, payload: dict[str, object]
            ) -> str:
                if payload.get("kind") != "smoke_finished":
                    return append_event(path, payload)
                altered = dict(payload)
                altered.pop("at", None)
                with mock.patch(
                    "xar_autoplayer.runtime.utc_now",
                    return_value="invalid-date",
                ):
                    return append_event(path, altered)

            with mock.patch(
                "xar_autoplayer.menu_smoke.append_event",
                side_effect=replace_only_actual_final_timestamp,
            ), self.assertRaisesRegex(
                AgentError, "committed final WAL digest differs"
            ):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            provisional = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(provisional["finalized"])
            self.assertFalse(provisional["ok"])
            self.assertNotIn("final_event_sha256", provisional)
            rows = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(rows[-1]["kind"], "smoke_finished")
            self.assertEqual(rows[-1]["at"], "invalid-date")

    def test_actual_final_row_reuses_exact_prevalidated_timestamp(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-final-event-planned-clock-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            planned_at = "2026-08-22T03:30:00+00:00"

            def split_clock_append(
                path: Path, payload: dict[str, object]
            ) -> str:
                if payload.get("kind") == "smoke_finished":
                    with mock.patch(
                        "xar_autoplayer.runtime.utc_now",
                        return_value="invalid-date",
                    ):
                        return append_event(path, payload)
                return append_event(path, payload)

            with mock.patch(
                "xar_autoplayer.menu_smoke.utc_now",
                return_value=planned_at,
            ), mock.patch(
                "xar_autoplayer.menu_smoke.append_event",
                side_effect=split_clock_append,
            ):
                result = _menu_smoke_locked(spec, 30)
            self.assertTrue(result["ok"])
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            chain = validate_event_chain(run_dir / "events.jsonl")
            tail = chain["tail"]
            self.assertEqual(tail["kind"], "smoke_finished")
            self.assertEqual(tail["at"], planned_at)
            self.assertEqual(
                result["final_event_sha256"], tail["event_sha256"]
            )

    def test_final_report_prefsync_failure_keeps_provisional_report(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-final-report-prefsync-"
        ) as temporary:
            path = Path(temporary) / "report.json"
            provisional = {"finalized": False, "ok": False}
            final = {"finalized": True, "ok": True}
            write_json_atomic(path, provisional)
            before = path.read_bytes()
            with mock.patch(
                "xar_autoplayer.menu_smoke.os.fsync",
                side_effect=OSError("synthetic temporary fsync failure"),
            ), self.assertRaisesRegex(OSError, "temporary fsync failure"):
                _write_final_report_transactionally(path, final)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")), provisional
            )
            self.assertEqual(list(path.parent.glob(".report.json.final-*.tmp")), [])

    def test_final_report_prefsync_and_unlink_failure_aborts_without_retry(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-final-report-prefsync-leftover-"
        ) as temporary:
            path = Path(temporary) / "report.json"
            provisional = {"finalized": False, "ok": False}
            final = {"finalized": True, "ok": True}
            write_json_atomic(path, provisional)
            before = path.read_bytes()
            path_type = type(path)
            real_unlink = path_type.unlink
            unlink_calls = 0

            def refuse_final_temporary_unlink(
                candidate: Path, *args: object, **kwargs: object
            ) -> None:
                nonlocal unlink_calls
                if candidate.name.startswith(".report.json.final-"):
                    unlink_calls += 1
                    raise PermissionError("synthetic temporary unlink failure")
                real_unlink(candidate, *args, **kwargs)

            with mock.patch(
                "xar_autoplayer.menu_smoke.os.fsync",
                side_effect=OSError("synthetic temporary fsync failure"),
            ) as fsync_mock, mock.patch.object(
                path_type,
                "unlink",
                new=refuse_final_temporary_unlink,
            ), mock.patch(
                "xar_autoplayer.menu_smoke.os.replace", wraps=os.replace
            ) as replace_mock, self.assertRaisesRegex(
                AgentError, "temporary remains"
            ):
                _write_final_report_transactionally(path, final)
            self.assertEqual(fsync_mock.call_count, 1)
            self.assertEqual(unlink_calls, 1)
            self.assertEqual(replace_mock.call_count, 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(
                len(list(path.parent.glob(".report.json.final-*.tmp"))), 1
            )

    def test_final_report_uncommitted_replace_and_unlink_failure_aborts_without_retry(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-final-report-replace-leftover-"
        ) as temporary:
            path = Path(temporary) / "report.json"
            provisional = {"finalized": False, "ok": False}
            final = {"finalized": True, "ok": True}
            write_json_atomic(path, provisional)
            before = path.read_bytes()
            path_type = type(path)
            real_unlink = path_type.unlink
            unlink_calls = 0

            def refuse_final_temporary_unlink(
                candidate: Path, *args: object, **kwargs: object
            ) -> None:
                nonlocal unlink_calls
                if candidate.name.startswith(".report.json.final-"):
                    unlink_calls += 1
                    raise PermissionError("synthetic temporary unlink failure")
                real_unlink(candidate, *args, **kwargs)

            with mock.patch(
                "xar_autoplayer.menu_smoke.os.replace",
                side_effect=OSError("synthetic pre-commit replace failure"),
            ) as replace_mock, mock.patch.object(
                path_type,
                "unlink",
                new=refuse_final_temporary_unlink,
            ), self.assertRaisesRegex(
                AgentError, "temporary remains"
            ):
                _write_final_report_transactionally(path, final)
            self.assertEqual(replace_mock.call_count, 1)
            self.assertEqual(unlink_calls, 1)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(
                len(list(path.parent.glob(".report.json.final-*.tmp"))), 1
            )

    def test_final_report_committed_replace_exception_is_reconciled(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-final-report-replace-"
        ) as temporary:
            path = Path(temporary) / "report.json"
            write_json_atomic(path, {"finalized": False, "ok": False})
            final = {"finalized": True, "ok": True, "seal": "a" * 64}
            real_replace = os.replace
            calls = 0

            def committed_then_raise(source: object, destination: object) -> None:
                nonlocal calls
                calls += 1
                real_replace(source, destination)
                raise OSError("synthetic committed replace exception")

            with mock.patch(
                "xar_autoplayer.menu_smoke.os.replace",
                side_effect=committed_then_raise,
            ):
                _write_final_report_transactionally(path, final)
            self.assertEqual(calls, 1)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), final)

    def test_public_replay_failure_after_publish_downgrades_to_provisional(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-post-publish-drift-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            real_writer = _write_final_report_transactionally

            def publish_then_mutate(
                path: Path, payload: dict[str, object]
            ) -> None:
                real_writer(path, payload)
                contract = path.parent / UI_CONTRACT_ARCHIVE
                contract.write_bytes(contract.read_bytes() + b"\n")

            def replay_manifest(run_dir: Path) -> dict[str, object]:
                payload = json.loads(
                    (run_dir / "report.json").read_text(encoding="utf-8")
                )
                _verified_artifact_manifest(payload, run_dir)
                return payload

            with mock.patch(
                "xar_autoplayer.menu_smoke._write_final_report_transactionally",
                side_effect=publish_then_mutate,
            ), mock.patch(
                "xar_autoplayer.menu_smoke.validate_menu_smoke_report",
                side_effect=replay_manifest,
            ), self.assertRaisesRegex(AgentError, "artifact differs"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("report_body_sha256", persisted)
            self.assertNotIn("final_event_sha256", persisted)
            self.assertNotIn("event_chain", persisted)
            self.assertIn("published final report replay", persisted["error"])
            rows = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(rows[-1]["kind"], "smoke_finished")

    def test_public_failure_downgrade_precommit_failure_preserves_final_bytes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-downgrade-precommit-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            real_replace = os.replace
            replace_calls = 0
            downgrade_armed = False

            def fail_only_downgrade_replace(
                source: object, destination: object
            ) -> None:
                nonlocal replace_calls
                if (
                    not downgrade_armed
                    or not Path(str(source)).name.startswith(
                        ".report.json.final-"
                    )
                ):
                    real_replace(source, destination)
                    return
                replace_calls += 1
                raise OSError("synthetic downgrade precommit failure")

            def mutate_then_reject(run_dir: Path) -> dict[str, object]:
                nonlocal downgrade_armed
                contract = run_dir / UI_CONTRACT_ARCHIVE
                contract.write_bytes(contract.read_bytes() + b"\n")
                downgrade_armed = True
                raise AgentError("synthetic public replay rejection")

            with mock.patch(
                "xar_autoplayer.menu_smoke.os.replace",
                side_effect=fail_only_downgrade_replace,
            ), mock.patch(
                "xar_autoplayer.menu_smoke.validate_menu_smoke_report",
                side_effect=mutate_then_reject,
            ), self.assertRaisesRegex(AgentError, "public replay rejection"):
                _menu_smoke_locked(spec, 30)
            self.assertEqual(replace_calls, 2)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertTrue(persisted["finalized"])
            self.assertTrue(persisted["ok"])
            self.assertIn("final_event_sha256", persisted)

    def test_public_failure_downgrade_committed_replace_exception_is_exact_provisional(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-downgrade-committed-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            real_replace = os.replace
            replace_calls = 0
            downgrade_armed = False

            def commit_downgrade_then_raise(
                source: object, destination: object
            ) -> None:
                nonlocal replace_calls
                if (
                    not downgrade_armed
                    or not Path(str(source)).name.startswith(
                        ".report.json.final-"
                    )
                ):
                    real_replace(source, destination)
                    return
                replace_calls += 1
                real_replace(source, destination)
                raise OSError(
                    "synthetic committed downgrade replace exception"
                )

            def mutate_then_reject(run_dir: Path) -> dict[str, object]:
                nonlocal downgrade_armed
                contract = run_dir / UI_CONTRACT_ARCHIVE
                contract.write_bytes(contract.read_bytes() + b"\n")
                downgrade_armed = True
                raise AgentError("synthetic public replay rejection")

            with mock.patch(
                "xar_autoplayer.menu_smoke.os.replace",
                side_effect=commit_downgrade_then_raise,
            ), mock.patch(
                "xar_autoplayer.menu_smoke.validate_menu_smoke_report",
                side_effect=mutate_then_reject,
            ), self.assertRaisesRegex(AgentError, "public replay rejection"):
                _menu_smoke_locked(spec, 30)
            self.assertEqual(replace_calls, 1)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("report_body_sha256", persisted)
            self.assertNotIn("final_event_sha256", persisted)
            self.assertNotIn("event_chain", persisted)
            self.assertIn("published final report replay", persisted["error"])

    def test_initial_manifest_failure_keeps_provisional_and_has_no_final_wal(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-manifest-failure-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            with mock.patch(
                "xar_autoplayer.menu_smoke._artifact_manifest",
                side_effect=OSError("synthetic manifest enumeration failure"),
            ), self.assertRaisesRegex(OSError, "manifest enumeration failure"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("final_event_sha256", persisted)
            kinds = [
                json.loads(line)["kind"]
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertNotIn("smoke_finished", kinds)

    def test_green_candidate_semantic_failure_keeps_provisional_without_final_wal(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-candidate-semantic-failure-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())
            with mock.patch(
                "xar_autoplayer.menu_smoke._validate_success_payload",
                side_effect=AgentError("synthetic candidate semantic failure"),
            ), self.assertRaisesRegex(AgentError, "candidate semantic failure"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("final_event_sha256", persisted)
            _verified_artifact_manifest(persisted, run_dir)
            self.assertNotIn(
                "smoke_finished",
                [
                    json.loads(line)["kind"]
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ],
            )

    def test_red_candidate_semantic_failure_keeps_provisional_without_final_wal(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-red-candidate-semantic-failure-"
        ) as temporary:
            spec, _handle = self._run(
                Path(temporary).resolve(),
                scenario_error=AgentError("synthetic operational RED"),
            )
            with mock.patch(
                "xar_autoplayer.menu_smoke._validate_red_payload",
                side_effect=AgentError("synthetic RED public replay mismatch"),
            ), self.assertRaisesRegex(AgentError, "RED public replay mismatch"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("final_event_sha256", persisted)
            _verified_artifact_manifest(persisted, run_dir)
            self.assertNotIn(
                "smoke_finished",
                [
                    json.loads(line)["kind"]
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ],
            )

    def test_used_artifact_drift_keeps_provisional_and_has_no_final_wal(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-used-artifact-drift-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())

            def mutate_used_artifact(
                _report: dict[str, object],
                _run_dir: Path,
                verified: dict[str, Path],
                **_kwargs: object,
            ) -> None:
                verified[UI_CONTRACT_ARCHIVE].write_bytes(
                    b"synthetic changed contract"
                )
                raise AgentError("synthetic used artifact semantic drift")

            with mock.patch(
                "xar_autoplayer.menu_smoke._validate_success_payload",
                side_effect=mutate_used_artifact,
            ), self.assertRaisesRegex(AgentError, "artifact bytes changed"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("final_event_sha256", persisted)
            verified = _verified_artifact_manifest(persisted, run_dir)
            self.assertEqual(
                verified[UI_CONTRACT_ARCHIVE].read_bytes(),
                b"synthetic changed contract",
            )
            self.assertNotIn(
                "smoke_finished",
                [
                    json.loads(line)["kind"]
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ],
            )
            with self.assertRaises(AgentError):
                validate_menu_smoke_report(run_dir)

    def test_unused_artifact_drift_keeps_provisional_and_has_no_final_wal(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-menu-unused-artifact-drift-"
        ) as temporary:
            spec, _handle = self._run(Path(temporary).resolve())

            def add_unused_artifact(
                _report: dict[str, object],
                run_dir: Path,
                _verified: dict[str, Path],
                **_kwargs: object,
            ) -> None:
                (run_dir / "artifacts" / "unreferenced.bin").write_bytes(
                    b"synthetic new artifact"
                )

            with mock.patch(
                "xar_autoplayer.menu_smoke._validate_success_payload",
                side_effect=add_unused_artifact,
            ), self.assertRaisesRegex(AgentError, "artifact bytes changed"):
                _menu_smoke_locked(spec, 30)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            persisted = json.loads(
                (run_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("final_event_sha256", persisted)
            verified = _verified_artifact_manifest(persisted, run_dir)
            self.assertEqual(
                verified["artifacts/unreferenced.bin"].read_bytes(),
                b"synthetic new artifact",
            )
            self.assertNotIn(
                "smoke_finished",
                [
                    json.loads(line)["kind"]
                    for line in (run_dir / "events.jsonl")
                    .read_text(encoding="utf-8")
                    .splitlines()
                ],
            )
            with self.assertRaises(AgentError):
                validate_menu_smoke_report(run_dir)

    def test_baseexception_finalizes_red_cleans_and_is_rethrown(self) -> None:
        class FatalProbe(BaseException):
            pass

        fatal = FatalProbe("interrupt after load")
        with tempfile.TemporaryDirectory(prefix="xar-menu-fatal-") as temporary:
            spec, _handle = self._run(Path(temporary).resolve(), scenario_error=fatal)
            with self.assertRaises(FatalProbe) as raised:
                _menu_smoke_locked(spec, 30)
            self.assertIs(raised.exception, fatal)
            report_path = next((spec.state_dir / "runs").glob("*-menu-*/report.json"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["finalized"])
            self.assertFalse(report["ok"])
            self.assertTrue(report["interrupted"])
            self.assertTrue(report["shutdown_attestation"]["cleanup_proven"])

    def test_finalization_failure_never_replaces_original_baseexception(self) -> None:
        class FatalProbe(BaseException):
            pass

        fatal = FatalProbe("interrupt before finalization")
        with tempfile.TemporaryDirectory(prefix="xar-menu-fatal-final-") as temporary:
            spec, _handle = self._run(
                Path(temporary).resolve(), scenario_error=fatal
            )

            def fail_final_event(path, payload):
                if payload.get("kind") == "smoke_finished":
                    raise RuntimeError("synthetic final event failure")
                return append_event(path, payload)

            with mock.patch(
                "xar_autoplayer.menu_smoke.append_event",
                side_effect=fail_final_event,
            ), self.assertRaises(FatalProbe) as raised:
                _menu_smoke_locked(spec, 30)
            self.assertIs(raised.exception, fatal)

    def test_unproven_cleanup_withholds_protected_postflight(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-menu-unsafe-") as temporary:
            spec, _handle = self._run(Path(temporary).resolve(), cleanup=False)
            with self.assertRaisesRegex(AgentError, "cleanup"):
                _menu_smoke_locked(spec, 30)
            report_path = next((spec.state_dir / "runs").glob("*-menu-*/report.json"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["unsafe_cleanup"])
            self.assertNotIn("protected_storage", report)
            self.assertFalse((report_path.parent / "protected-after.json.gz").exists())

    def test_post_exit_load_write_failure_keeps_report_and_archive_aligned(self) -> None:
        for failure in ("before-commit", "after-commit"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory(
                prefix=f"xar-menu-load-{failure}-"
            ) as temporary:
                spec, _handle = self._run(
                    Path(temporary).resolve(), post_exit_write_failure=failure
                )
                with self.assertRaisesRegex(AgentError, failure):
                    _menu_smoke_locked(spec, 30)
                run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
                report = json.loads(
                    (run_dir / "report.json").read_text(encoding="utf-8")
                )
                archived = json.loads(
                    (
                        run_dir
                        / "artifacts"
                        / "supervisor-load-attestation.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertFalse(report["ok"])
                self.assertEqual(report["load_attestation"], archived)
                self.assertEqual(
                    "post_exit_revalidated" in report["load_attestation"],
                    failure == "after-commit",
                )

    def test_launch_identity_interrupt_recovers_process_envelope_from_shutdown(
        self,
    ) -> None:
        class FatalProbe(BaseException):
            pass

        fatal = FatalProbe("interrupt during launch identity publication")
        with tempfile.TemporaryDirectory(prefix="xar-menu-process-envelope-") as temporary:
            spec, _handle = self._run(
                Path(temporary).resolve(), process_pid_failure=fatal
            )
            with self.assertRaises(FatalProbe) as raised:
                _menu_smoke_locked(spec, 30)
            self.assertIs(raised.exception, fatal)
            run_dir = next((spec.state_dir / "runs").glob("*-menu-*"))
            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertEqual(report["process"]["pid"], 42)
            self.assertEqual(
                report["process"]["creation_date"],
                report["shutdown_attestation"]["ck3_creation_date"],
            )
            kinds = [
                json.loads(line)["kind"]
                for line in (run_dir / "events.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertNotIn("ck3_launched", kinds)
            self.assertIn("tracked_process_stopped", kinds)


class MenuCliTests(unittest.TestCase):
    def test_menu_command_never_falls_through_to_crash_smoke(self) -> None:
        payload = {"ok": True, "kind": MENU_KIND}
        fake_crash = types.ModuleType("xar_autoplayer.crash_probe")
        fake_crash.crash_smoke = mock.Mock(side_effect=AssertionError("crash fallthrough"))
        with tempfile.TemporaryDirectory(prefix="xar-menu-cli-") as temporary, mock.patch(
            "xar_autoplayer.menu_smoke.menu_smoke", return_value=payload
        ) as run_menu, mock.patch.dict(
            sys.modules, {"xar_autoplayer.crash_probe": fake_crash}
        ), mock.patch("builtins.print"):
            code = cli.main(
                [
                    "--state-dir",
                    str(Path(temporary) / "state"),
                    "--game-dir",
                    str(Path(temporary) / "game"),
                    "menu-smoke",
                    "--timeout",
                    "12",
                ]
            )
        self.assertEqual(code, 0)
        run_menu.assert_called_once()
        self.assertEqual(run_menu.call_args.kwargs["timeout_seconds"], 12)
        fake_crash.crash_smoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()
