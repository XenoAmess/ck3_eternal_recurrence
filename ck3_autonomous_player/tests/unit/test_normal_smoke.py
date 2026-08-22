from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from PIL import Image


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.environment import (  # noqa: E402
    EnvironmentSpec,
    EXPECTED_MOD_NAME,
    OUTER_DESCRIPTOR_REF,
    _contract_digest,
    sha256_file,
    snapshot_digest,
    write_json_atomic,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.rules import MOD_RULES  # noqa: E402
from xar_autoplayer.runtime import (  # noqa: E402
    MAIN_MENU_REGION,
    NORMAL_REPLAY_TRUST_MODEL,
    _SuspendedWindowsProcess,
    _append_normal_final_event_transactionally,
    _finalize_normal_smoke_report,
    _normal_artifact_manifest,
    _normal_report_body_sha256,
    _region_bbox,
    _smoke_locked,
    _write_normal_final_report_transactionally,
    analyze_engine_log_bytes,
    append_event,
    parse_runtime_attestation,
    validate_event_chain,
    validate_smoke_report,
    write_gzip_json_atomic,
)


OCR_ITEMS = [
    {
        "text": "\u65b0\u6e38\u620f",
        "score": 0.99,
        "center": [600, 600],
        "bbox": [520, 570, 680, 630],
    }
]
NONCE = "1" * 32
CREATION_DMTF = "20260822090033.870978+480"
CREATION_CIM = "2026-08-22T01:00:33.8709780Z"


def _production_manifest() -> dict[str, object]:
    paths = sorted(
        {
            "descriptor.mod",
            "common/game_rules/xar_game_rules.txt",
            "common/on_action/eternal_recurrence_on_actions.txt",
            "events/xar_events.txt",
        }
    )
    return {
        "format_version": 1,
        "git_sha": "a" * 40,
        "git_tag": None,
        "mod_version": "0.0.0-test",
        "workshop_item_id": "3784706360",
        "files": [
            {
                "path": path,
                "size": len(path.encode("utf-8")),
                "sha256": hashlib.sha256(path.encode("utf-8")).hexdigest(),
            }
            for path in paths
        ],
    }


def _environment(run: Path, production_path: Path) -> dict[str, object]:
    state = run.parent.parent
    profile = state / "profile"
    game_exe = run.parent / "game" / "binaries" / "ck3.exe"
    production_file = run / "production.manifest.json"
    production = json.loads(production_file.read_text(encoding="utf-8"))
    projected = {
        entry["path"]: {"size": entry["size"], "sha256": entry["sha256"]}
        for entry in production["files"]
    }
    runtime = {
        "files": [],
        "file_count": 0,
        "git": {
            "selected_runtime_revision": "b" * 40,
            "all_files_tracked": True,
            "untracked_runtime_files": [],
            "dirty": False,
            "status": [],
        },
    }
    runtime["sha256"] = snapshot_digest(runtime)
    allowed_mounts = [str((run.parent / "game" / "game" / "dlc" / "base").resolve())]
    rule_profile = [
        {"rule": f"vanilla_rule_{index}", "setting": f"vanilla_setting_{index}"}
        for index in range(81)
    ] + [{"rule": rule, "setting": setting} for rule, setting in MOD_RULES]
    manifest: dict[str, object] = {
        "state_dir": str(state.resolve()),
        "profile_dir": str(profile.resolve()),
        "game": {
            "raw_version": "1.19.0.6",
            "debug_mode": False,
            "executable": str(game_exe.resolve()),
        },
        "mod": {
            "name": EXPECTED_MOD_NAME,
            "git_revision": "a" * 40,
            "source_provenance": {
                "git_revision": "a" * 40,
                "git_dirty": False,
                "all_release_files_tracked": True,
                "untracked_release_files": [],
                "git_status": [],
            },
            "production_path": str(production_path.resolve()),
            "production_manifest": str(production_file.resolve()),
            "production_manifest_sha256": sha256_file(production_file),
            "production_tree_sha256": snapshot_digest(projected),
            "production_file_count": len(projected),
            "release_identity": {
                "format_version": 1,
                "git_tag": None,
                "mod_version": "0.0.0-test",
                "workshop_item_id": "3784706360",
            },
        },
        "load_profile": {
            "enabled_mods": [OUTER_DESCRIPTOR_REF],
            "disabled_dlcs": [],
        },
        "display": {
            "language": "l_simp_chinese",
            "resolution": [2560, 1440],
            "mode": "fullscreen",
        },
        "legality": {
            "production_only": True,
            "single_mod": True,
            "visible_ui_only_for_decisions": True,
            "save_rollback": False,
            "runtime_logs": "environment attestation only; never policy input",
        },
        "agent_runtime": runtime,
        "rules": {
            "declared_vanilla_rule_count": 81,
            "ironman": False,
            "profile": rule_profile,
            "profile_sha256": hashlib.sha256(
                json.dumps(
                    rule_profile, ensure_ascii=True, separators=(",", ":")
                ).encode("ascii")
            ).hexdigest(),
        },
        "dlc": {
            "allowed_mount_roots": allowed_mounts,
            "allowed_mount_roots_sha256": snapshot_digest(allowed_mounts),
            "installed_descriptor_count": len(allowed_mounts),
            "installed_descriptors_sha256": "d" * 64,
        },
    }
    manifest["environment_sha256"] = _contract_digest(manifest)
    return manifest


def _inventory(processes: list[dict[str, object]]) -> dict[str, object]:
    pids = [int(row["pid"]) for row in processes]
    return {
        "tasklist_returncode": 0,
        "tasklist_pids": pids,
        "wmi_pids": pids,
        "processes": processes,
    }


def _make_fixture(parent: Path, name: str = "run-v2") -> Path:
    run = parent / name
    artifacts = run / "artifacts"
    artifacts.mkdir(parents=True)
    production = _production_manifest()
    write_json_atomic(run / "production.manifest.json", production)
    state = run.parent.parent
    profile = state / "profile"
    production_path = profile / "mod-content" / "xar-production"
    environment = _environment(run, production_path)
    write_json_atomic(run / "environment.json", environment)

    stores = {"real_profile": {}, "steam_userdata": {}, "workshop": {}}
    protected = {
        "digest": snapshot_digest(stores),
        "stores": stores,
        "allowed_volatile": {
            "steam_remotecache": {},
            "policy": "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected.",
        },
    }
    write_gzip_json_atomic(run / "protected-before.json.gz", protected)
    write_gzip_json_atomic(run / "protected-after.json.gz", protected)

    first = Image.new("RGB", (2560, 1440), (24, 28, 36))
    second = Image.new("RGB", (2560, 1440), (25, 29, 37))
    first_path = artifacts / "main-menu-frame-1.png"
    second_path = artifacts / "main-menu.png"
    first.save(first_path)
    second.save(second_path)
    second.crop(_region_bbox(second.size, MAIN_MENU_REGION)).save(
        artifacts / "main-menu-crop.png"
    )
    write_json_atomic(artifacts / "main-menu-frame-1-ocr.json", OCR_ITEMS)
    write_json_atomic(artifacts / "main-menu-ocr.json", OCR_ITEMS)

    dlc = environment["dlc"]["allowed_mount_roots"][0]
    debug_raw = (
        "Log system initialized fixture\n"
        f"{EXPECTED_MOD_NAME}|{OUTER_DESCRIPTOR_REF}|Enabled\n"
        f"Mounted Data: {production_path.resolve()}\n"
        f"Mounted Data: {dlc}\n"
    ).encode("utf-8")
    initial_debug = artifacts / "runtime-debug-prefix.log"
    final_debug = artifacts / "runtime-debug-post-exit.log"
    initial_debug.write_bytes(debug_raw)
    final_debug.write_bytes(debug_raw)
    debug_hash = hashlib.sha256(debug_raw).hexdigest()
    debug_metadata = {
        "captured_prefix_size": len(debug_raw),
        "captured_prefix_sha256": debug_hash,
        "file_size_after_read": len(debug_raw),
        "mtime_ns": 2_000,
        "prelaunch_epoch_ns": 1_000,
        "cleared_before_launch": ["debug.log", "error.log"],
    }
    initial_metadata = {
        **debug_metadata,
        "archive_path": "artifacts/runtime-debug-prefix.log",
        "archive_sha256": debug_hash,
    }
    final_metadata = {
        **debug_metadata,
        "archive_path": "artifacts/runtime-debug-post-exit.log",
        "archive_sha256": debug_hash,
    }
    load = parse_runtime_attestation(
        debug_raw.decode("utf-8"),
        profile,
        production_path,
        allowed_dlc_mounts=environment["dlc"]["allowed_mount_roots"],
    )
    load["debug_log"] = initial_metadata
    load["post_exit_revalidated"] = True
    load["post_exit_debug_log"] = final_metadata
    write_json_atomic(artifacts / "supervisor-load-attestation.json", load)

    diagnostic_path = artifacts / "supervisor-error.log"
    diagnostic_raw = b""
    diagnostic_path.write_bytes(diagnostic_raw)
    diagnostic_analysis = analyze_engine_log_bytes(
        "error.log",
        diagnostic_raw,
        expected_mod_name=EXPECTED_MOD_NAME,
        production_path=production_path,
    )
    diagnostics = {
        "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
        "zero_diagnostics": True,
        "current_mod_diagnostics": False,
        "current_mod_diagnostic_hits": [],
        "logs": {
            "error.log": {
                "present": True,
                "path": "artifacts/supervisor-error.log",
                "sha256": hashlib.sha256(diagnostic_raw).hexdigest(),
                "size": 0,
                "mtime_ns": 2_001,
                "diagnostic_records": diagnostic_analysis["diagnostic_records"],
                "nonempty_lines": diagnostic_analysis["nonempty_lines"],
            },
            "gui_warnings.log": {"present": False, "diagnostic_records": 0},
        },
    }

    pid = 4242
    exe = environment["game"]["executable"]
    row = {
        "pid": pid,
        "parent_pid": 3131,
        "name": "ck3.exe",
        "executable": "",
        "creation_date": CREATION_CIM,
    }
    control = Path(environment["state_dir"]) / "control"
    process = {
        "pid": pid,
        "watchdog_pid": 4343,
        "arguments": [
            exe,
            "-gdpr-compliant",
            f"-userdir={environment['profile_dir']}",
        ],
        "debug_mode": False,
        "fresh_log_epoch_ns": 1_000,
        "prelaunch_logs_removed": ["debug.log", "error.log"],
        "pre_resume_ck3_inventory": _inventory([row]),
        "identity": {
            "pid": pid,
            "parent_pid": 3131,
            "name": "ck3.exe",
            "executable": exe,
            "creation_date": CREATION_DMTF,
        },
        "handle_trust": {
            "pinned_process_handle": True,
            "owned_kill_on_close_job": True,
            "created_suspended_before_job_assignment": True,
            "pre_resume_identity_cross_validated": True,
        },
    }
    empty_inventory = _inventory([])
    shutdown = {
        "nonce": NONCE,
        "ck3_pid": pid,
        "ck3_creation_date": CREATION_DMTF,
        "ck3_exit_code": 1,
        "job_active_processes_before_termination": 1,
        "job_active_processes_final": 0,
        "tree_gone": True,
        "cleanup_proven": True,
        "final_ck3_inventory": empty_inventory,
        "watchdog_pid": 4343,
        "watchdog_creation_date": "20260822090030.000000+480",
        "watchdog_state_before": "running",
        "watchdog_state_after": "absent",
        "control_files_absent": {
            str(control / "ck3.json"): True,
            str(control / "ck3.watchdog_error"): True,
            str(control / f"watchdog-{NONCE}.ready.json"): True,
            str(control / "unsafe-cleanup.json"): True,
        },
        "contract_errors": [],
        "ok": True,
    }
    visual = {
        "target": "\u65b0\u6e38\u620f",
        "target_normalized": "\u65b0\u6e38\u620f",
        "stable_frames": 2,
        "stable_frame_evidence": [
            {
                "frame": 1,
                "capture_sequence": 7,
                "captured_at": "2026-08-22T01:00:40+00:00",
                "captured_monotonic": 10.0,
                "window_rect": [0, 0, 2560, 1440],
                "screenshot": "artifacts/main-menu-frame-1.png",
                "screenshot_sha256": sha256_file(first_path),
                "ocr": "artifacts/main-menu-frame-1-ocr.json",
                "ocr_sha256": sha256_file(artifacts / "main-menu-frame-1-ocr.json"),
                "exact_match_count": 1,
            },
            {
                "frame": 2,
                "capture_sequence": 8,
                "captured_at": "2026-08-22T01:00:41+00:00",
                "captured_monotonic": 10.75,
                "window_rect": [0, 0, 2560, 1440],
                "screenshot": "artifacts/main-menu.png",
                "screenshot_sha256": sha256_file(second_path),
                "ocr": "artifacts/main-menu-ocr.json",
                "ocr_sha256": sha256_file(artifacts / "main-menu-ocr.json"),
                "exact_match_count": 1,
            },
        ],
        "window_rect": [0, 0, 2560, 1440],
        "screenshot": "artifacts/main-menu.png",
        "screenshot_sha256": sha256_file(second_path),
        "ocr": "artifacts/main-menu-ocr.json",
        "ocr_sha256": sha256_file(artifacts / "main-menu-ocr.json"),
    }

    events = run / "events.jsonl"
    append_event(
        events,
        {
            "kind": "smoke_started",
            "environment_sha256": environment["environment_sha256"],
            "protected_storage_sha256": protected["digest"],
            "protected_snapshot_sha256": sha256_file(run / "protected-before.json.gz"),
        },
    )
    append_event(events, {"kind": "ck3_launched", "pid": pid})
    append_event(events, {"kind": "visible_main_menu_attested"})
    append_event(events, {"kind": "single_mod_runtime_attested"})
    append_event(events, {"kind": "tracked_process_stopped", "pid": pid})

    report: dict[str, object] = {
        "format_version": 2,
        "run_id": name,
        "kind": "infrastructure_smoke",
        "acceptance_claim": "isolated_single_mod_visible_main_menu_only",
        "clean_engine_boot_required": False,
        "started_at": "2026-08-22T01:00:00+00:00",
        "finished_at": "2026-08-22T01:01:00+00:00",
        "valid_score_episode": False,
        "environment_sha256": environment["environment_sha256"],
        "run_dir": ".",
        "replay_trust_model": copy.deepcopy(NORMAL_REPLAY_TRUST_MODEL),
        "process": process,
        "visual_attestation": visual,
        "load_attestation": load,
        "shutdown_attestation": shutdown,
        "post_shutdown_ck3_inventory": empty_inventory,
        "engine_diagnostics": diagnostics,
        "protected_storage": {
            "post_exit_matches_baseline": True,
            "continuous_quiet_seconds": 5,
            "runtime_write_absence_proven": False,
            "sha256": protected["digest"],
            "before_snapshot": "protected-before.json.gz",
            "before_snapshot_sha256": sha256_file(run / "protected-before.json.gz"),
            "after_snapshot": "protected-after.json.gz",
            "after_snapshot_sha256": sha256_file(run / "protected-after.json.gz"),
            "allowed_volatile_before": protected["allowed_volatile"],
            "allowed_volatile_after": protected["allowed_volatile"],
        },
        "production_tree_unchanged": True,
        "artifacts": _normal_artifact_manifest(run),
        "finalized": False,
        "ok": False,
    }
    body = _normal_report_body_sha256(report)
    report["report_body_sha256"] = body
    tail = append_event(
        events,
        {"kind": "smoke_finished", "ok": True, "report_body_sha256": body},
    )
    chain = validate_event_chain(events)
    report["final_event_sha256"] = tail
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    report["finalized"] = True
    report["ok"] = True
    write_json_atomic(run / "report.json", report)
    return run


def _resign(run: Path) -> None:
    report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    report["artifacts"] = _normal_artifact_manifest(run)
    lines = (run / "events.jsonl").read_text(encoding="utf-8").splitlines()
    (run / "events.jsonl").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    body = _normal_report_body_sha256(report)
    report["report_body_sha256"] = body
    tail = append_event(
        run / "events.jsonl",
        {"kind": "smoke_finished", "ok": True, "report_body_sha256": body},
    )
    chain = validate_event_chain(run / "events.jsonl")
    report["final_event_sha256"] = tail
    report["event_chain"] = {
        "event_count": chain["event_count"],
        "tail_sha256": chain["tail_sha256"],
    }
    write_json_atomic(run / "report.json", report)


class NormalSmokeReplayTests(unittest.TestCase):
    def validate(self, run: Path) -> dict[str, object]:
        with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS) as ocr:
            result = validate_smoke_report(run)
        self.assertEqual(ocr.call_count, 2)
        return result

    def test_self_contained_green_replays_after_relocation_and_origin_deletion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-v2-") as temporary:
            root = Path(temporary)
            origin = _make_fixture(root / "origin" / "state" / "runs")
            relocated = root / "relocated" / origin.name
            shutil.copytree(origin, relocated)
            shutil.rmtree(root / "origin")
            result = self.validate(relocated)
            self.assertTrue(result["ok"])

    def test_legacy_v1_retains_only_the_historical_shallow_validator(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-v1-") as temporary:
            run = Path(temporary)
            events = run / "events.jsonl"
            append_event(events, {"kind": "smoke_started"})
            tail = append_event(events, {"kind": "smoke_finished", "ok": False})
            write_json_atomic(
                run / "report.json",
                {
                    "format_version": 1,
                    "finalized": True,
                    "ok": False,
                    "final_event_sha256": tail,
                },
            )
            self.assertFalse(validate_smoke_report(run)["ok"])

    def test_unknown_format_cannot_downgrade_to_the_legacy_validator(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-version-") as temporary:
            run = Path(temporary)
            events = run / "events.jsonl"
            append_event(events, {"kind": "smoke_started"})
            tail = append_event(events, {"kind": "smoke_finished", "ok": False})
            write_json_atomic(
                run / "report.json",
                {
                    "format_version": 99,
                    "finalized": True,
                    "ok": False,
                    "final_event_sha256": tail,
                },
            )
            with self.assertRaisesRegex(AgentError, "unsupported"):
                validate_smoke_report(run)

    def test_png_tamper_is_rejected_even_after_unkeyed_resigning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-png-") as temporary:
            run = _make_fixture(Path(temporary))
            (run / "artifacts" / "main-menu-frame-1.png").write_bytes(b"not-png")
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "visible frame"):
                    validate_smoke_report(run)

    def test_ocr_tamper_is_rejected_even_after_unkeyed_resigning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-ocr-") as temporary:
            run = _make_fixture(Path(temporary))
            write_json_atomic(
                run / "artifacts" / "main-menu-frame-1-ocr.json",
                [{**OCR_ITEMS[0], "text": "\u9000\u51fa\u6e38\u620f"}],
            )
            report = json.loads((run / "report.json").read_text(encoding="utf-8"))
            report["visual_attestation"]["stable_frame_evidence"][0][
                "ocr_sha256"
            ] = sha256_file(run / "artifacts" / "main-menu-frame-1-ocr.json")
            write_json_atomic(run / "report.json", report)
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "replayed visible frame"):
                    validate_smoke_report(run)

    def test_debug_tamper_is_rejected_after_manifest_resigning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-debug-") as temporary:
            run = _make_fixture(Path(temporary))
            path = run / "artifacts" / "runtime-debug-prefix.log"
            path.write_bytes(path.read_bytes() + b"Other|mod/other.mod|Enabled\n")
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "debug prefix"):
                    validate_smoke_report(run)

    def test_diagnostic_tamper_is_rejected_after_manifest_resigning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-diag-") as temporary:
            run = _make_fixture(Path(temporary))
            (run / "artifacts" / "supervisor-error.log").write_text(
                "[E][x] xar_fixture failed\n", encoding="utf-8"
            )
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "diagnostic record"):
                    validate_smoke_report(run)

    def test_protected_tamper_is_rejected_after_manifest_resigning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-protected-") as temporary:
            run = _make_fixture(Path(temporary))
            changed_stores = {"real_profile": {"new": {}}, "steam_userdata": {}, "workshop": {}}
            write_gzip_json_atomic(
                run / "protected-after.json.gz",
                {
                    "digest": snapshot_digest(changed_stores),
                    "stores": changed_stores,
                    "allowed_volatile": {
                        "steam_remotecache": {},
                        "policy": "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected.",
                    },
                },
            )
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "protected-storage replay"):
                    validate_smoke_report(run)

    def test_unmanifested_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-manifest-") as temporary:
            run = _make_fixture(Path(temporary))
            (run / "artifacts" / "unbound.bin").write_bytes(b"unbound")
            with self.assertRaisesRegex(AgentError, "complete run inventory"):
                validate_smoke_report(run)

    def test_report_body_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-report-") as temporary:
            run = _make_fixture(Path(temporary))
            report = json.loads((run / "report.json").read_text(encoding="utf-8"))
            report["production_tree_unchanged"] = False
            write_json_atomic(run / "report.json", report)
            with self.assertRaisesRegex(AgentError, "report-body binding"):
                validate_smoke_report(run)

    def test_event_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-event-") as temporary:
            run = _make_fixture(Path(temporary))
            lines = (run / "events.jsonl").read_text(encoding="utf-8").splitlines()
            row = json.loads(lines[1])
            row["pid"] += 1
            lines[1] = json.dumps(row, separators=(",", ":"))
            (run / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(AgentError, "digest differs"):
                validate_smoke_report(run)

    def test_process_command_cannot_be_replaced_and_resigned(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-process-") as temporary:
            run = _make_fixture(Path(temporary))
            report = json.loads((run / "report.json").read_text(encoding="utf-8"))
            report["process"]["arguments"] = [
                "C:/attacker.exe",
                "-gdpr-compliant",
                "-userdir=C:/attacker",
            ]
            report["process"]["identity"]["executable"] = "C:/attacker.exe"
            write_json_atomic(run / "report.json", report)
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "command executable"):
                    validate_smoke_report(run)

    def test_core_nested_extra_fields_are_rejected_after_resigning(self) -> None:
        cases = {
            "visual": ("visual_attestation", "synthetic_input"),
            "shutdown": ("shutdown_attestation", "cleanup_uncertain"),
            "protected": ("protected_storage", "runtime_write_detected"),
            "load": ("load_attestation", "unclassified_mounts_v2"),
        }
        for label, (section, field) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-normal-extra-{label}-"
            ) as temporary:
                run = _make_fixture(Path(temporary))
                report = json.loads((run / "report.json").read_text(encoding="utf-8"))
                report[section][field] = True
                if section == "load_attestation":
                    write_json_atomic(
                        run / "artifacts" / "supervisor-load-attestation.json",
                        report[section],
                    )
                write_json_atomic(run / "report.json", report)
                _resign(run)
                with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                    with self.assertRaises(AgentError):
                        validate_smoke_report(run)

    def test_visual_frame_alias_is_rejected_after_resigning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-frame-alias-") as temporary:
            run = _make_fixture(Path(temporary))
            report = json.loads((run / "report.json").read_text(encoding="utf-8"))
            frames = report["visual_attestation"]["stable_frame_evidence"]
            frames[0]["screenshot"] = frames[1]["screenshot"]
            frames[0]["screenshot_sha256"] = frames[1]["screenshot_sha256"]
            frames[0]["ocr"] = frames[1]["ocr"]
            frames[0]["ocr_sha256"] = frames[1]["ocr_sha256"]
            write_json_atomic(run / "report.json", report)
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "replayed visible frame"):
                    validate_smoke_report(run)

    def test_initial_final_debug_alias_is_rejected_after_resigning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-debug-alias-") as temporary:
            run = _make_fixture(Path(temporary))
            report = json.loads((run / "report.json").read_text(encoding="utf-8"))
            report["load_attestation"]["debug_log"] = copy.deepcopy(
                report["load_attestation"]["post_exit_debug_log"]
            )
            write_json_atomic(
                run / "artifacts" / "supervisor-load-attestation.json",
                report["load_attestation"],
            )
            write_json_atomic(run / "report.json", report)
            _resign(run)
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                with self.assertRaisesRegex(AgentError, "debug archive reference"):
                    validate_smoke_report(run)


class NormalSmokeFinalizationTests(unittest.TestCase):
    def test_manifest_failure_leaves_provisional_report_and_no_final_wal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-manifest-fault-") as temporary:
            run = Path(temporary) / "run"
            (run / "artifacts").mkdir(parents=True)
            events = run / "events.jsonl"
            append_event(events, {"kind": "smoke_started"})
            report = {
                "format_version": 2,
                "run_id": "run",
                "run_dir": ".",
                "finalized": False,
                "ok": False,
            }
            write_json_atomic(run / "report.json", report)
            with mock.patch(
                "xar_autoplayer.runtime._normal_artifact_manifest",
                side_effect=OSError("enumeration failed"),
            ):
                with self.assertRaisesRegex(AgentError, "could not be established"):
                    _finalize_normal_smoke_report(report, run, events, None)
            persisted = json.loads((run / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            self.assertNotIn("final_event_sha256", persisted)
            self.assertEqual(validate_event_chain(events)["event_count"], 1)

    def test_candidate_artifact_drift_is_resealed_as_replayable_red(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-drift-fault-") as temporary:
            run = Path(temporary) / "run"
            artifacts = run / "artifacts"
            artifacts.mkdir(parents=True)
            evidence = artifacts / "evidence.bin"
            evidence.write_bytes(b"before")
            events = run / "events.jsonl"
            append_event(events, {"kind": "smoke_started"})
            report = {
                "format_version": 2,
                "run_id": "run",
                "kind": "infrastructure_smoke",
                "acceptance_claim": "isolated_single_mod_visible_main_menu_only",
                "valid_score_episode": False,
                "run_dir": ".",
                "replay_trust_model": copy.deepcopy(NORMAL_REPLAY_TRUST_MODEL),
                "finished_at": "2026-08-22T01:00:00+00:00",
                "finalized": False,
                "ok": False,
            }
            write_json_atomic(run / "report.json", report)

            def mutate_during_candidate(*_args: object) -> None:
                evidence.write_bytes(b"after")

            with mock.patch(
                "xar_autoplayer.runtime._validate_normal_v2_green_candidate",
                side_effect=mutate_during_candidate,
            ):
                error = _finalize_normal_smoke_report(report, run, events, None)
            self.assertIsInstance(error, AgentError)
            self.assertIn("changed during candidate", str(error))
            persisted = validate_smoke_report(run)
            self.assertTrue(persisted["finalized"])
            self.assertFalse(persisted["ok"])
            entry = next(
                item
                for item in persisted["artifacts"]
                if item["path"] == "artifacts/evidence.bin"
            )
            self.assertEqual(entry["sha256"], hashlib.sha256(b"after").hexdigest())

    def test_final_event_recovers_only_the_exact_committed_after_fsync_row(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-final-event-") as temporary:
            events = Path(temporary) / "events.jsonl"
            append_event(events, {"kind": "smoke_started"})
            real_append = append_event

            def committed_then_raised(path: Path, payload: dict[str, object]) -> str:
                real_append(path, payload)
                raise OSError("after fsync")

            with mock.patch(
                "xar_autoplayer.runtime.append_event",
                side_effect=committed_then_raised,
            ):
                tail = _append_normal_final_event_transactionally(
                    events, ok=True, report_body_sha256="a" * 64
                )
            chain = validate_event_chain(events)
            self.assertEqual(chain["event_count"], 2)
            self.assertEqual(tail, chain["tail_sha256"])

    def test_final_report_recovers_an_exact_committed_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-final-report-") as temporary:
            path = Path(temporary) / "report.json"
            write_json_atomic(path, {"format_version": 2, "ok": False})
            report = {"format_version": 2, "ok": True}
            real_replace = os.replace

            def committed_then_raised(source: Path, target: Path) -> None:
                real_replace(source, target)
                raise OSError("after replace")

            with mock.patch(
                "xar_autoplayer.runtime.os.replace",
                side_effect=committed_then_raised,
            ):
                _write_normal_final_report_transactionally(path, report)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), report)

    def test_final_report_barrier_failure_never_replaces_provisional(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-report-barrier-") as temporary:
            path = Path(temporary) / "report.json"
            provisional = {"format_version": 2, "finalized": False, "ok": False}
            final = {"format_version": 2, "finalized": True, "ok": True}
            write_json_atomic(path, provisional)
            with mock.patch(
                "xar_autoplayer.runtime.os.fsync",
                side_effect=OSError("barrier failed"),
            ):
                with self.assertRaisesRegex(AgentError, "pre-publication barrier"):
                    _write_normal_final_report_transactionally(path, final)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), provisional)
            self.assertFalse(path.with_name(path.name + ".final.tmp").exists())

    def test_producer_archives_v2_debug_visual_diagnostic_and_process_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-normal-producer-") as temporary:
            root = Path(temporary).resolve()
            state = root / "state"
            seed = _make_fixture(state / "runs", "seed")
            manifest = json.loads((seed / "environment.json").read_text(encoding="utf-8"))
            game = Path(manifest["game"]["executable"]).parents[1]
            spec = EnvironmentSpec(state, game)
            spec.production_dir.mkdir(parents=True)
            production_source = seed / "production.manifest.json"
            manifest["mod"]["production_manifest"] = str(production_source)
            production_payload = json.loads(production_source.read_text(encoding="utf-8"))
            projected = {
                entry["path"]: {"size": entry["size"], "sha256": entry["sha256"]}
                for entry in production_payload["files"]
            }
            write_json_atomic(spec.manifest_path, manifest)
            logs = spec.profile_dir / "logs"
            logs.mkdir(parents=True)
            debug_raw = (seed / "artifacts" / "runtime-debug-prefix.log").read_bytes()
            debug_source = logs / "debug.log"
            debug_source.write_bytes(debug_raw)
            debug = {
                "path": str(debug_source),
                "captured_prefix_size": len(debug_raw),
                "captured_prefix_sha256": hashlib.sha256(debug_raw).hexdigest(),
                "file_size_after_read": len(debug_raw),
                "mtime_ns": 2_000,
                "prelaunch_epoch_ns": 1_000,
                "cleared_before_launch": ["debug.log", "error.log"],
            }
            load = parse_runtime_attestation(
                debug_raw.decode("utf-8"),
                spec.profile_dir,
                spec.production_dir,
                allowed_dlc_mounts=manifest["dlc"]["allowed_mount_roots"],
            )
            load["debug_log"] = debug
            protected = {
                "digest": snapshot_digest(
                    {"real_profile": {}, "steam_userdata": {}, "workshop": {}}
                ),
                "stores": {
                    "real_profile": {},
                    "steam_userdata": {},
                    "workshop": {},
                },
                "allowed_volatile": {
                    "steam_remotecache": {},
                    "policy": "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected.",
                },
            }
            process = object.__new__(_SuspendedWindowsProcess)
            process.pid = 4242
            process._process_handle = object()
            process.resumed = True
            process.returncode = 1
            empty = _inventory([])
            row = {
                "pid": 4242,
                "parent_pid": 3131,
                "name": "ck3.exe",
                "executable": "",
                "creation_date": CREATION_CIM,
            }
            handle = SimpleNamespace(
                process=process,
                watchdog_pid=4343,
                command=[
                    str(spec.game_exe),
                    "-gdpr-compliant",
                    f"-userdir={spec.profile_dir}",
                ],
                log_epoch_ns=1_000,
                cleared_logs=["debug.log", "error.log"],
                pre_resume_inventory=_inventory([row]),
                ck3_creation_date=CREATION_DMTF,
                job_handle=object(),
            )

            def visible(_handle: object, artifacts: Path, _timeout: float) -> dict[str, object]:
                artifacts.mkdir(parents=True, exist_ok=True)
                first = Image.new("RGB", (2560, 1440), (1, 2, 3))
                second = Image.new("RGB", (2560, 1440), (4, 5, 6))
                first_path = artifacts / "main-menu-frame-1.png"
                second_path = artifacts / "main-menu.png"
                first.save(first_path)
                second.save(second_path)
                second.crop(_region_bbox(second.size, MAIN_MENU_REGION)).save(
                    artifacts / "main-menu-crop.png"
                )
                first_ocr = artifacts / "main-menu-frame-1-ocr.json"
                second_ocr = artifacts / "main-menu-ocr.json"
                write_json_atomic(first_ocr, OCR_ITEMS)
                write_json_atomic(second_ocr, OCR_ITEMS)
                frames = [
                    {
                        "frame": 1,
                        "capture_sequence": 1,
                        "captured_at": "2026-08-22T01:00:00+00:00",
                        "captured_monotonic": 1.0,
                        "window_rect": [0, 0, 2560, 1440],
                        "screenshot": str(first_path),
                        "screenshot_sha256": sha256_file(first_path),
                        "ocr": str(first_ocr),
                        "ocr_sha256": sha256_file(first_ocr),
                        "exact_match_count": 1,
                    },
                    {
                        "frame": 2,
                        "capture_sequence": 2,
                        "captured_at": "2026-08-22T01:00:01+00:00",
                        "captured_monotonic": 2.0,
                        "window_rect": [0, 0, 2560, 1440],
                        "screenshot": str(second_path),
                        "screenshot_sha256": sha256_file(second_path),
                        "ocr": str(second_ocr),
                        "ocr_sha256": sha256_file(second_ocr),
                        "exact_match_count": 1,
                    },
                ]
                return {
                    "target": "\u65b0\u6e38\u620f",
                    "target_normalized": "\u65b0\u6e38\u620f",
                    "stable_frames": 2,
                    "stable_frame_evidence": frames,
                    "window_rect": frames[1]["window_rect"],
                    "screenshot": frames[1]["screenshot"],
                    "screenshot_sha256": frames[1]["screenshot_sha256"],
                    "ocr": frames[1]["ocr"],
                    "ocr_sha256": frames[1]["ocr_sha256"],
                }

            def diagnostics(_spec: object, _handle: object, artifacts: Path) -> dict[str, object]:
                path = artifacts / "supervisor-error.log"
                path.write_bytes(b"")
                return {
                    "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
                    "zero_diagnostics": True,
                    "current_mod_diagnostics": False,
                    "current_mod_diagnostic_hits": [],
                    "logs": {
                        "error.log": {
                            "present": True,
                            "path": str(path),
                            "sha256": sha256_file(path),
                            "size": 0,
                            "mtime_ns": 2_000,
                            "diagnostic_records": 0,
                            "nonempty_lines": 0,
                        },
                        "gui_warnings.log": {"present": False, "diagnostic_records": 0},
                    },
                }

            seed_report = json.loads((seed / "report.json").read_text(encoding="utf-8"))
            shutdown = copy.deepcopy(seed_report["shutdown_attestation"])
            identity = {
                "pid": 4242,
                "parent_pid": 3131,
                "name": "ck3.exe",
                "executable": "",
                "creation_date": CREATION_DMTF,
                "command_line": "ck3.exe",
            }
            mod_git = copy.deepcopy(manifest["mod"]["source_provenance"])
            with (
                mock.patch("xar_autoplayer.runtime.verify_profile", return_value=manifest),
                mock.patch("xar_autoplayer.runtime.doctor"),
                mock.patch("xar_autoplayer.runtime.mod_source_fingerprint", return_value=mod_git),
                mock.patch("xar_autoplayer.runtime.protected_snapshot", return_value=protected),
                mock.patch("xar_autoplayer.runtime.verify_protected_unchanged", return_value=protected),
                mock.patch("xar_autoplayer.runtime.launch", return_value=handle),
                mock.patch("xar_autoplayer.runtime._process_identity", return_value=identity),
                mock.patch("xar_autoplayer.runtime.wait_for_main_menu", side_effect=visible),
                mock.patch(
                    "xar_autoplayer.runtime.wait_for_runtime_attestation",
                    side_effect=lambda *_args: copy.deepcopy(load),
                ),
                mock.patch("xar_autoplayer.runtime.stop_tracked", return_value=shutdown),
                mock.patch("xar_autoplayer.runtime.ck3_process_inventory", return_value=empty),
                mock.patch("xar_autoplayer.runtime.collect_engine_log_evidence", side_effect=diagnostics),
                mock.patch("xar_autoplayer.runtime.tree_snapshot", return_value=projected),
                mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS),
                mock.patch("xar_autoplayer.runtime.os.getpid", return_value=3131),
            ):
                report = _smoke_locked(spec, 30)

            self.assertEqual(report["format_version"], 2)
            self.assertEqual(report["run_dir"], ".")
            self.assertEqual(report["process"]["identity"]["creation_date"], CREATION_DMTF)
            self.assertTrue(all(report["process"]["handle_trust"].values()))
            load_report = report["load_attestation"]
            self.assertNotIn("path", load_report["debug_log"])
            self.assertNotIn("path", load_report["post_exit_debug_log"])
            self.assertTrue(load_report["debug_log"]["archive_path"].startswith("artifacts/"))
            self.assertTrue(
                load_report["post_exit_debug_log"]["archive_path"].startswith("artifacts/")
            )
            for frame in report["visual_attestation"]["stable_frame_evidence"]:
                self.assertTrue(frame["screenshot"].startswith("artifacts/"))
                self.assertTrue(frame["ocr"].startswith("artifacts/"))
            self.assertTrue(
                report["engine_diagnostics"]["logs"]["error.log"]["path"].startswith(
                    "artifacts/"
                )
            )
            manifested = {item["path"] for item in report["artifacts"]}
            self.assertIn("artifacts/runtime-debug-prefix.log", manifested)
            self.assertIn("artifacts/runtime-debug-post-exit.log", manifested)
            self.assertIn("protected-before.json.gz", manifested)
            self.assertIn("protected-after.json.gz", manifested)
            chain = validate_event_chain(
                spec.state_dir / "runs" / report["run_id"] / "events.jsonl"
            )
            self.assertEqual(
                chain["tail"]["report_body_sha256"], report["report_body_sha256"]
            )
            with mock.patch("xar_autoplayer.runtime._ocr_items", return_value=OCR_ITEMS):
                replayed = validate_smoke_report(
                    spec.state_dir / "runs" / report["run_id"]
                )
            self.assertEqual(replayed, report)


if __name__ == "__main__":
    unittest.main()
