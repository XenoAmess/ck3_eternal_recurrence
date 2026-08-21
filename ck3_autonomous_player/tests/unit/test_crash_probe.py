from __future__ import annotations

import json
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest import mock

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.crash_probe import (  # noqa: E402
    CRASH_EXIT_CODE,
    CONTROL_FILE_LABELS,
    REPLAY_TRUST_MODEL,
    _REPLAY_OCR_CACHE,
    _canonical_job_name,
    _named_job_absent,
    _pin_process,
    _report_body_sha256,
    _replay_main_menu_ocr,
    _run_named_job_owner_fixture,
    _run_outer_guard_outer_fixture,
    _validate_crash_success_payload,
    _validate_environment_archive_semantics,
    _validate_subject_invocation,
    validate_crash_report,
    _wait_named_job_absent,
    _wait_pinned_exit,
)
from xar_autoplayer.environment import (  # noqa: E402
    EXPECTED_GAME_VERSION,
    EXPECTED_MOD_NAME,
    OUTER_DESCRIPTOR_REF,
    _contract_digest,
    EnvironmentSpec,
    sha256_file,
    snapshot_digest,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.runtime import (  # noqa: E402
    MAIN_MENU_REGION,
    _close_job,
    _create_kill_on_close_job,
    _ocr_items,
    append_event,
    launch,
    unique_exact_ocr_match,
    validate_event_chain,
)


class CrashEvidencePathTests(unittest.TestCase):
    def _spec(self, root: Path) -> EnvironmentSpec:
        return EnvironmentSpec(root / "state", root / "game")

    def test_launch_rejects_profile_or_control_evidence_targets_without_deleting(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-path-") as temporary:
            spec = self._spec(Path(temporary))
            targets = [
                spec.profile_dir / "dlc_load.json",
                spec.state_dir / "control" / "ck3.json",
            ]
            for target in targets:
                with self.subTest(target=target):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("protected", encoding="ascii")
                    with mock.patch(
                        "xar_autoplayer.runtime.verify_profile", return_value={}
                    ), mock.patch(
                        "xar_autoplayer.runtime.ck3_processes", return_value=[]
                    ):
                        with self.assertRaisesRegex(
                            AgentError, "runs/<run-id>/artifacts"
                        ):
                            launch(spec, watchdog_final_evidence=target)
                    self.assertEqual(target.read_text(encoding="ascii"), "protected")

    def test_launch_rejects_existing_evidence_or_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-existing-") as temporary:
            spec = self._spec(Path(temporary))
            run = spec.state_dir / "runs" / "run-1" / "artifacts"
            run.mkdir(parents=True)
            targets = [run / "final.json", run / "other.json"]
            targets[0].write_text("existing", encoding="ascii")
            targets[1].with_name("other.json.tmp").write_text(
                "existing", encoding="ascii"
            )
            for target in targets:
                with self.subTest(target=target), mock.patch(
                    "xar_autoplayer.runtime.verify_profile", return_value={}
                ), mock.patch(
                    "xar_autoplayer.runtime.ck3_processes", return_value=[]
                ):
                    with self.assertRaisesRegex(AgentError, "already exists"):
                        launch(spec, watchdog_final_evidence=target)

    def test_unsafe_marker_precedes_evidence_path_validation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-marker-") as temporary:
            spec = self._spec(Path(temporary))
            marker = spec.state_dir / "control" / "unsafe-cleanup.json"
            marker.parent.mkdir(parents=True)
            marker.write_text('{"nonce":"old"}\n', encoding="ascii")
            with mock.patch(
                "xar_autoplayer.runtime.verify_profile", return_value={}
            ), mock.patch(
                "xar_autoplayer.runtime.ck3_processes", return_value=[]
            ):
                with self.assertRaisesRegex(AgentError, "unsafe cleanup marker"):
                    launch(
                        spec,
                        watchdog_final_evidence=spec.profile_dir / "dlc_load.json",
                    )


class CrashReportContractTests(unittest.TestCase):
    def _run(self, temporary: str) -> Path:
        return (
            Path(temporary).resolve()
            / "state"
            / "runs"
            / "20260822T010203Z-crash-deadbeef"
        )

    def _report(self, run: Path) -> dict[str, object]:
        artifacts_dir = run / "artifacts"
        artifacts_dir.mkdir(parents=True)
        self.assertEqual(run.parent.name, "runs")
        state = run.parents[1]
        production = state / "profile" / "mod-content" / "xar-production"
        dlc_root = run / "archived-game-dlc" / "dlc001_test"
        game_exe = run / "game" / "binaries" / "ck3.exe"
        probe_nonce = "a" * 32
        watchdog_nonce = "b" * 32

        def entry(path: Path) -> dict[str, str]:
            return {
                "path": path.resolve().relative_to(run.resolve()).as_posix(),
                "sha256": sha256_file(path),
            }

        production_files = [
            {
                "path": "common/game_rules/xar_game_rules.txt",
                "sha256": "d" * 64,
                "size": 123,
            },
            {
                "path": "common/on_action/eternal_recurrence_on_actions.txt",
                "sha256": "e" * 64,
                "size": 234,
            },
            {"path": "descriptor.mod", "sha256": "f" * 64, "size": 345},
            {
                "path": "events/xar_events.txt",
                "sha256": "1" * 64,
                "size": 456,
            },
        ]
        production_tree = {
            entry["path"]: {
                "size": entry["size"],
                "sha256": entry["sha256"],
            }
            for entry in production_files
        }
        production_manifest_payload = {
            "files": production_files,
            "format_version": 2,
            "git_sha": "c" * 40,
            "git_tag": None,
            "mod_version": "1.0.0",
            "workshop_item_id": "3784706360",
        }
        production_manifest = run / "production.manifest.json"
        production_manifest.write_text(
            json.dumps(production_manifest_payload) + "\n", encoding="utf-8"
        )
        environment = run / "environment.json"
        runtime_paths = [
            "agent/src/xar_autoplayer/crash_probe.py",
            "agent/src/xar_autoplayer/environment.py",
            "agent/src/xar_autoplayer/process_watchdog.py",
            "agent/src/xar_autoplayer/runtime.py",
            "repo/tools/build_release.py",
        ]
        runtime_files = [
            {"path": path, "size": index + 1, "sha256": f"{index + 2:x}" * 64}
            for index, path in enumerate(runtime_paths)
        ]
        runtime_payload = {
            "file_count": len(runtime_files),
            "files": runtime_files,
            "interpreter": {
                "path": str(Path(sys.executable).resolve()),
                "sha256": "8" * 64,
                "version": sys.version,
            },
            "distributions": {"Pillow": "12.3.0"},
            "git": {
                "selected_runtime_revision": "c" * 40,
                "all_files_tracked": True,
                "untracked_runtime_files": [],
                "dirty": False,
                "status": [],
            },
        }
        runtime_payload["sha256"] = snapshot_digest(runtime_payload)
        rule_profile = [
            {"rule": f"vanilla_rule_{index:02}", "setting": f"default_{index:02}"}
            for index in range(81)
        ] + [
            {"rule": "xar_enabled", "setting": "xar_on"},
            {"rule": "xar_inheritance", "setting": "xar_inherit_100"},
            {"rule": "xar_score_basis", "setting": "xar_score_growth"},
        ]
        serialized_rule_profile = json.dumps(
            rule_profile, ensure_ascii=True, separators=(",", ":")
        ).encode("ascii")
        vanilla_rules = run / "game" / "game" / "common" / "game_rules" / "00_game_rules.txt"
        environment_payload = {
            "format_version": 1,
            "agent_version": "0.1.0",
            "agent_runtime": runtime_payload,
            "prepared_at": "2026-08-22T01:00:00+00:00",
            "state_dir": str(state.resolve()),
            "profile_dir": str((state / "profile").resolve()),
            "game": {
                "raw_version": EXPECTED_GAME_VERSION,
                "display_version": EXPECTED_GAME_VERSION,
                "distribution": "steam",
                "launcher_settings_sha256": "4" * 64,
                "executable": str(game_exe),
                "executable_sha256": "5" * 64,
                "vanilla_rules": str(vanilla_rules),
                "vanilla_rules_sha256": "6" * 64,
                "debug_mode": False,
            },
            "dlc": {
                "installed_descriptor_count": 1,
                "installed_descriptors_sha256": "7" * 64,
                "allowed_mount_roots": [str(dlc_root.resolve())],
                "allowed_mount_roots_sha256": snapshot_digest(
                    [str(dlc_root.resolve())]
                ),
                "note": "test fixture",
            },
            "mod": {
                "git_revision": "c" * 40,
                "source_provenance": {
                    "git_revision": "c" * 40,
                    "git_tags_at_revision": [],
                    "git_dirty": False,
                    "git_status": [],
                    "all_release_files_tracked": True,
                    "untracked_release_files": [],
                    "release_source_file_count": len(production_files),
                    "release_source_sha256": "9" * 64,
                },
                "production_manifest_sha256": sha256_file(production_manifest),
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
                "source_sha256": "6" * 64,
                "declared_vanilla_rule_count": 81,
                "profile": rule_profile,
                "profile_sha256": hashlib.sha256(serialized_rule_profile).hexdigest(),
                "ironman": False,
            },
            "display": {
                "language": "l_simp_chinese",
                "resolution": [2560, 1440],
                "mode": "fullscreen",
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
        environment_payload["environment_sha256"] = _contract_digest(
            environment_payload
        )
        environment.write_text(
            json.dumps(environment_payload) + "\n", encoding="utf-8"
        )
        environment_sha256 = environment_payload["environment_sha256"]
        debug_prefix = artifacts_dir / f"runtime-debug-prefix-{probe_nonce}.log"
        debug_prefix.write_text(
            "Log system initialized\n"
            f"{EXPECTED_MOD_NAME}|{OUTER_DESCRIPTOR_REF}|Enabled\n"
            f"Mounted Data: {dlc_root}\n"
            f"Mounted Data: {production}\n",
            encoding="utf-8",
        )
        load = {
            "enabled_mods": [
                {"name": EXPECTED_MOD_NAME, "descriptor": OUTER_DESCRIPTOR_REF}
            ],
            "isolated_mod_mounts": [str(production.resolve())],
            "runtime_dlc_mounts": [str(dlc_root.resolve())],
            "unclassified_mounts": [],
            "evidence_lines": [],
            "session_marker_count": 1,
            "source": "test",
            "policy_boundary": "not available to gameplay perception or strategy",
            "debug_log": {
                "archive_path": str(debug_prefix.resolve()),
                "archive_sha256": sha256_file(debug_prefix),
            },
        }
        load_path = artifacts_dir / f"load-attestation-{probe_nonce}.json"
        load_path.write_text(
            json.dumps(load, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        supervisor = {
            "pid": 123,
            "parent_pid": 100,
            "name": Path(sys.executable).name,
            "executable": str(sys.executable),
            "creation_date": "supervisor-created",
            "command_line": f'"{sys.executable}" agent.py _crash-subject',
        }
        ck3 = {
            "pid": 150,
            "parent_pid": 123,
            "name": "ck3.exe",
            "executable": str(game_exe),
            "creation_date": "ck3-created",
            "command_line": f'"{game_exe}" -gdpr-compliant',
        }
        watchdog = {
            "pid": 456,
            "parent_pid": 999,
            "name": Path(sys.executable).name,
            "executable": str(sys.executable),
            "creation_date": "watchdog-created",
            "command_line": f'"{sys.executable}" process_watchdog.py',
        }
        control_payloads = {
            "record": {
                "format_version": 1,
                "nonce": watchdog_nonce,
                "ck3_pid": ck3["pid"],
                "parent_pid": supervisor["pid"],
                "executable": ck3["executable"],
                "creation_date": ck3["creation_date"],
            },
            "ready": {
                "nonce": watchdog_nonce,
                "parent_pid": supervisor["pid"],
                "parent_executable": supervisor["executable"],
                "parent_creation_date": supervisor["creation_date"],
                "watchdog_pid": watchdog["pid"],
            },
            "unsafe_marker": {
                "nonce": watchdog_nonce,
                "ck3_pid": ck3["pid"],
                "reason": "suspended launch active; removed only after authenticated tree shutdown",
            },
        }
        control_entries: dict[str, dict[str, str]] = {}
        control_hashes: dict[str, str] = {}
        for label in ("record", "ready", "unsafe_marker"):
            path = artifacts_dir / f"control-before-{label}-{probe_nonce}.json"
            path.write_text(
                json.dumps(control_payloads[label]) + "\n", encoding="utf-8"
            )
            control_entries[label] = entry(path)
            control_hashes[f"{label}_sha256"] = sha256_file(path)

        evidence = artifacts_dir / f"watchdog-final-{probe_nonce}.json"
        evidence.write_text(
            json.dumps(
                {
                    "format_version": 1,
                    "nonce": watchdog_nonce,
                    "parent_pid": 123,
                    "parent_executable": str(sys.executable),
                    "parent_creation_date": "supervisor-created",
                    "watchdog_pid": 456,
                    "watchdog_creation_date": "watchdog-created",
                    "expected_ck3_executable": str(game_exe),
                    "parent_termination_observed": True,
                    "authenticated_candidates": [],
                    "ok": True,
                    "stage": "complete",
                    "measured_stable_empty_seconds": 5.1,
                    "empty_poll_count": 52,
                    "control_files_removed": True,
                }
            )
            + "\n",
            encoding="ascii",
        )
        before = run / "protected-before.json.gz"
        after = run / "protected-after.json.gz"
        protected_stores = {
            "real_profile": {},
            "steam_userdata": {},
            "workshop": {},
        }
        protected_digest = snapshot_digest(protected_stores)
        protected_payload = {
            "digest": protected_digest,
            "stores": protected_stores,
            "allowed_volatile": {
                "steam_remotecache": {},
                "policy": "Only top-level ChangeNumber/mtime may change; semantic bytes remain protected.",
            },
        }
        for path in (before, after):
            with gzip.open(path, "wt", encoding="utf-8") as output:
                json.dump(protected_payload, output)

        armed_path = artifacts_dir / f"armed-{probe_nonce}.json"
        handoff_path = artifacts_dir / f"handoff-{probe_nonce}.json"
        owner_path = artifacts_dir / f"owner-{probe_nonce}.json"
        job_name = _canonical_job_name(probe_nonce)
        font_path = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "msyh.ttc"
        if not font_path.is_file():
            self.skipTest("Microsoft YaHei is required for deterministic OCR fixtures")
        visual_font = ImageFont.truetype(str(font_path), 48)

        def rendered_main_menu(
            path: Path, background: tuple[int, int, int]
        ) -> list[dict[str, object]]:
            image = Image.new("RGB", (2560, 1440), background)
            ImageDraw.Draw(image).text(
                (540, 520), "新游戏", font=visual_font, fill=(255, 255, 255)
            )
            image.save(path, format="PNG")
            items = _ocr_items(image, MAIN_MENU_REGION)
            self.assertIsNotNone(
                next(
                    (
                        item
                        for item in items
                        if str(item.get("text", "")).replace(" ", "") == "新游戏"
                    ),
                    None,
                )
            )
            return items

        first_visual_screenshot = artifacts_dir / "main-menu-frame-1.png"
        first_items = rendered_main_menu(first_visual_screenshot, (12, 24, 36))
        first_visual_ocr = artifacts_dir / "main-menu-frame-1-ocr.json"
        first_visual_ocr.write_text(
            json.dumps(first_items, ensure_ascii=False),
            encoding="utf-8",
        )
        visual_screenshot = artifacts_dir / "main-menu.png"
        second_items = rendered_main_menu(visual_screenshot, (13, 25, 37))
        visual_ocr = artifacts_dir / "main-menu-ocr.json"
        visual_ocr.write_text(
            json.dumps(second_items, ensure_ascii=False),
            encoding="utf-8",
        )
        stable_frame_evidence = [
            {
                "frame": 1,
                "capture_sequence": 17,
                "captured_at": "2026-08-22T01:02:03+00:00",
                "captured_monotonic": 100.0,
                "window_rect": [0, 0, 2560, 1440],
                "screenshot": str(first_visual_screenshot.resolve()),
                "screenshot_sha256": sha256_file(first_visual_screenshot),
                "ocr": str(first_visual_ocr.resolve()),
                "ocr_sha256": sha256_file(first_visual_ocr),
                "exact_match_count": 1,
            },
            {
                "frame": 2,
                "capture_sequence": 18,
                "captured_at": "2026-08-22T01:02:04+00:00",
                "captured_monotonic": 101.0,
                "window_rect": [0, 0, 2560, 1440],
                "screenshot": str(visual_screenshot.resolve()),
                "screenshot_sha256": sha256_file(visual_screenshot),
                "ocr": str(visual_ocr.resolve()),
                "ocr_sha256": sha256_file(visual_ocr),
                "exact_match_count": 1,
            },
        ]
        visual_attestation = {
            "target": "新游戏",
            "target_normalized": "新游戏",
            "stable_frames": 2,
            "stable_frame_evidence": stable_frame_evidence,
            "window_rect": [0, 0, 2560, 1440],
            "screenshot": str(visual_screenshot.resolve()),
            "screenshot_sha256": sha256_file(visual_screenshot),
            "ocr": str(visual_ocr.resolve()),
            "ocr_sha256": sha256_file(visual_ocr),
        }
        armed = {
            "format_version": 1,
            "probe_nonce": probe_nonce,
            "watchdog_nonce": watchdog_nonce,
            "job_name": job_name,
            "job_active_processes": 3,
            "process_resumed": True,
            "supervisor": supervisor,
            "ck3": ck3,
            "sentinel_parent": {
                "pid": 200,
                "parent_pid": 123,
                "name": Path(sys.executable).name,
                "executable": str(sys.executable),
                "creation_date": "sentinel-parent-created",
                "command_line": f'"{sys.executable}" sentinel-parent',
            },
            "sentinel_child": {
                "pid": 201,
                "parent_pid": 200,
                "name": Path(sys.executable).name,
                "executable": str(sys.executable),
                "creation_date": "sentinel-child-created",
                "command_line": f'"{sys.executable}" sentinel-child',
            },
            "watchdog": watchdog,
            "control": {
                "record": str(state / "control" / "ck3.json"),
                "ready": str(
                    state / "control" / f"watchdog-{watchdog_nonce}.ready.json"
                ),
                "unsafe_marker": str(state / "control" / "unsafe-cleanup.json"),
                "watchdog_error": str(state / "control" / "ck3.watchdog_error"),
                **control_hashes,
            },
            "load_attestation": load,
            "visual_attestation": visual_attestation,
            "artifacts": {
                "runtime_debug_prefix": entry(debug_prefix),
                "load_attestation": entry(load_path),
                "visual_frame_1_screenshot": entry(first_visual_screenshot),
                "visual_frame_1_ocr": entry(first_visual_ocr),
                "visual_frame_2_screenshot": entry(visual_screenshot),
                "visual_frame_2_ocr": entry(visual_ocr),
            },
            "environment_sha256": environment_sha256,
            "armed_at": "2026-08-22T01:02:03+00:00",
        }
        armed_path.write_text(
            json.dumps(armed, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        owner_payload = {
            "pid": 100,
            "thread_id": 987,
            "purpose": "crash-smoke",
            "state_dir": str(state.resolve()),
        }
        owner_path.write_text(json.dumps(owner_payload) + "\n", encoding="utf-8")
        handoff = {
            "format_version": 1,
            "probe_nonce": probe_nonce,
            "run_id": run.name,
            "state_dir": str(state.resolve()),
            "artifacts": str(artifacts_dir.resolve()),
            "armed": str(armed_path.resolve()),
            "watchdog_final": str(evidence.resolve()),
            "outer": {
                "pid": 100,
                "parent_pid": 10,
                "name": Path(sys.executable).name,
                "executable": str(sys.executable),
                "creation_date": "outer-created",
                "command_line": f'"{sys.executable}" agent.py crash-smoke',
            },
            "environment_sha256": environment_sha256,
            "owner_sha256": sha256_file(owner_path),
        }
        handoff_path.write_text(json.dumps(handoff) + "\n", encoding="utf-8")
        artifact_manifest = {
            "protected_before": entry(before),
            "environment": entry(environment),
            "production_manifest": entry(production_manifest),
            "owner": entry(owner_path),
            "handoff": entry(handoff_path),
            "armed": entry(armed_path),
            "runtime_debug_prefix": entry(debug_prefix),
            "load_attestation": entry(load_path),
            "visual_frame_1_screenshot": entry(first_visual_screenshot),
            "visual_frame_1_ocr": entry(first_visual_ocr),
            "visual_frame_2_screenshot": entry(visual_screenshot),
            "visual_frame_2_ocr": entry(visual_ocr),
            "control_before_record": control_entries["record"],
            "control_before_ready": control_entries["ready"],
            "control_before_unsafe_marker": control_entries["unsafe_marker"],
            "watchdog_final": entry(evidence),
            "protected_after": entry(after),
        }
        return {
            "run_dir": str(run.resolve()),
            "run_id": run.name,
            "kind": "crash_recovery_smoke",
            "acceptance_claim": "post_resume_supervisor_crash_recovery_only",
            "valid_score_episode": False,
            "replay_trust_model": dict(REPLAY_TRUST_MODEL),
            "environment_sha256": environment_sha256,
            "artifacts": artifact_manifest,
            "crash_attestation": {
                "probe_nonce": probe_nonce,
                "subject_pid": 123,
                "subject_exit_code": CRASH_EXIT_CODE,
                "cleanup_proven": True,
                "job_name": job_name,
                "job_active_processes_before": 3,
                "named_job_destroyed": True,
                "pinned_processes_signaled": {
                    "supervisor": True,
                    "ck3": True,
                    "sentinel_parent": True,
                    "sentinel_child": True,
                },
                "pinned_process_identities": {
                    "supervisor": supervisor,
                    "ck3": ck3,
                    "sentinel_parent": armed["sentinel_parent"],
                    "sentinel_child": armed["sentinel_child"],
                },
                "pinned_process_exit_codes": {
                    "supervisor": CRASH_EXIT_CODE,
                    "ck3": 1,
                    "sentinel_parent": 1,
                    "sentinel_child": 1,
                },
                "watchdog_identity_before": watchdog,
                "watchdog_state_before": "running",
                "watchdog_state_after": "absent",
                "watchdog_exit_code": 0,
                "watchdog_nonce": watchdog_nonce,
                "handoff_sha256": sha256_file(handoff_path),
                "armed_sha256": sha256_file(armed_path),
                "control_files_before": control_entries,
                "control_files_absent": {
                    label: True for label in CONTROL_FILE_LABELS
                },
                "final_ck3_inventory": {
                    "tasklist_returncode": 0,
                    "tasklist_pids": [],
                    "wmi_pids": [],
                    "processes": [],
                    "continuous_empty_seconds": 5,
                    "poll_count": 26,
                },
                "watchdog_final": str(evidence),
                "watchdog_final_sha256": sha256_file(evidence),
            },
            "visual_attestation": armed["visual_attestation"],
            "load_attestation": load,
            "protected_storage": {
                "post_exit_matches_baseline": True,
                "continuous_quiet_seconds": 5,
                "runtime_write_absence_proven": False,
                "sha256": protected_digest,
                "before_snapshot_sha256": sha256_file(before),
                "after_snapshot_sha256": sha256_file(after),
            },
            "production_tree_unchanged": True,
        }

    def _finalize(
        self,
        run: Path,
        report: dict[str, object],
        *,
        ok: bool,
        include_cleanup_events: bool = True,
    ) -> None:
        report.update(
            {
                "format_version": 1,
                "run_dir": str(run.resolve()),
                "runtime_write_absence_proven": False,
                "finalized": False,
                "ok": False,
            }
        )
        events = run / "events.jsonl"
        append_event(events, {"kind": "smoke_started"})
        cleanup_claimed = report.get("crash_attestation", {}).get(
            "cleanup_proven"
        ) is True
        if (ok or cleanup_claimed) and include_cleanup_events:
            append_event(events, {"kind": "crash_subject_armed"})
            append_event(events, {"kind": "supervisor_crash_injected"})
            append_event(events, {"kind": "watchdog_cleanup_attested"})
        elif "error" not in report:
            report["error"] = "test RED"
        body = _report_body_sha256(report)
        report["report_body_sha256"] = body
        tail = append_event(
            events,
            {"kind": "smoke_finished", "ok": ok, "report_body_sha256": body},
        )
        report["final_event_sha256"] = tail
        report["finalized"] = True
        report["ok"] = ok
        chain = validate_event_chain(events)
        report["event_chain"] = {
            "event_count": chain["event_count"],
            "tail_sha256": chain["tail_sha256"],
        }
        (run / "report.json").write_text(
            json.dumps(report, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def test_success_contract_binds_watchdog_artifact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-report-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            _validate_crash_success_payload(report, run)
            evidence = Path(report["crash_attestation"]["watchdog_final"])
            evidence.write_text("{}\n", encoding="ascii")
            with self.assertRaisesRegex(AgentError, "hash differs"):
                _validate_crash_success_payload(report, run)

    def test_success_contract_rejects_missing_tree_member(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-tree-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            del report["crash_attestation"]["pinned_processes_signaled"][
                "sentinel_child"
            ]
            with self.assertRaisesRegex(AgentError, "pinned-process proof"):
                _validate_crash_success_payload(report, run)

    def test_success_contract_rejects_nonfinite_watchdog_quiet_window(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-nan-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            evidence = Path(report["crash_attestation"]["watchdog_final"])
            payload = json.loads(evidence.read_text(encoding="ascii"))
            payload["measured_stable_empty_seconds"] = float("nan")
            evidence.write_text(json.dumps(payload) + "\n", encoding="ascii")
            digest = sha256_file(evidence)
            report["crash_attestation"]["watchdog_final_sha256"] = digest
            report["artifacts"]["watchdog_final"]["sha256"] = digest
            with self.assertRaisesRegex(AgentError, "payload differs"):
                _validate_crash_success_payload(report, run)

    def test_success_contract_requires_all_four_control_absence_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-controls-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            del report["crash_attestation"]["control_files_absent"]["ready"]
            with self.assertRaisesRegex(AgentError, "control-file proof"):
                _validate_crash_success_payload(report, run)

    def test_success_contract_requires_post_resume_ck3_binding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-resume-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            armed_path = run / report["artifacts"]["armed"]["path"]
            armed = json.loads(armed_path.read_text(encoding="utf-8"))
            armed["process_resumed"] = False
            armed_path.write_text(json.dumps(armed) + "\n", encoding="utf-8")
            digest = sha256_file(armed_path)
            report["artifacts"]["armed"]["sha256"] = digest
            report["crash_attestation"]["armed_sha256"] = digest
            with self.assertRaisesRegex(AgentError, "handoff or armed payload"):
                _validate_crash_success_payload(report, run)

    def test_report_body_digest_changes_with_semantic_evidence(self) -> None:
        report = {"kind": "crash_recovery_smoke", "evidence": {"ok": True}}
        first = _report_body_sha256(report)
        report["finalized"] = True
        report["ok"] = True
        report["final_event_sha256"] = "ignored"
        self.assertEqual(first, _report_body_sha256(report))
        report["evidence"]["ok"] = False
        self.assertNotEqual(first, _report_body_sha256(report))

    def test_public_replay_validator_accepts_complete_green(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-public-green-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            self._finalize(run, report, ok=True)
            self.assertTrue(validate_crash_report(run)["ok"])

    def test_public_replay_validator_accepts_relocated_complete_archive(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-crash-origin-"
        ) as origin_parent, tempfile.TemporaryDirectory(
            prefix="xar-crash-copy-"
        ) as copy_parent:
            origin = self._run(origin_parent)
            report = self._report(origin)
            self._finalize(origin, report, ok=True)
            relocated = Path(copy_parent) / origin.name
            shutil.copytree(origin, relocated)
            shutil.rmtree(origin.parents[1])
            _REPLAY_OCR_CACHE.clear()
            self.assertTrue(validate_crash_report(relocated)["ok"])

    def test_cleanup_claim_requires_the_complete_crash_event_sequence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-events-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            self._finalize(
                run, report, ok=False, include_cleanup_events=False
            )
            with self.assertRaisesRegex(AgentError, "attested crash event sequence"):
                validate_crash_report(run)

    def test_public_replay_requires_explicit_unkeyed_trust_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-trust-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            del report["replay_trust_model"]
            self._finalize(run, report, ok=True)
            with self.assertRaisesRegex(AgentError, "base contract"):
                validate_crash_report(run)

    def test_archived_game_and_rule_semantics_are_not_skeleton_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-rules-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            environment_path = run / report["artifacts"]["environment"]["path"]
            original = json.loads(environment_path.read_text(encoding="utf-8"))
            _validate_environment_archive_semantics(original)
            mutations = (
                ("debug", lambda payload: payload["game"].__setitem__("debug_mode", True)),
                ("ironman", lambda payload: payload["rules"].__setitem__("ironman", True)),
                (
                    "vanilla-count",
                    lambda payload: payload["rules"].__setitem__(
                        "declared_vanilla_rule_count", 80
                    ),
                ),
                (
                    "profile-hash",
                    lambda payload: payload["rules"].__setitem__(
                        "profile_sha256", "0" * 64
                    ),
                ),
            )
            for label, mutate in mutations:
                with self.subTest(label=label):
                    payload = json.loads(json.dumps(original))
                    mutate(payload)
                    with self.assertRaises(AgentError):
                        _validate_environment_archive_semantics(payload)

    def test_replay_ocr_rejects_a_plain_image_with_handwritten_claims(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-plain-png-") as temporary:
            path = Path(temporary) / "plain.png"
            Image.new("RGB", (2560, 1440), "black").save(path, format="PNG")
            items = _replay_main_menu_ocr(path, sha256_file(path))
            self.assertIsNone(unique_exact_ocr_match(items, "新游戏"))

    def test_ck3_process_name_parent_and_pid_uniqueness_are_bound(self) -> None:
        mutations = (
            ("name", lambda armed: armed["ck3"].__setitem__("name", "notepad.exe")),
            (
                "parent",
                lambda armed: armed["ck3"].__setitem__(
                    "parent_pid", armed["supervisor"]["parent_pid"]
                ),
            ),
            (
                "duplicate-pid",
                lambda armed: armed["ck3"].__setitem__(
                    "pid", armed["supervisor"]["pid"]
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                prefix=f"xar-crash-identity-{label}-"
            ) as temporary:
                run = self._run(temporary)
                report = self._report(run)
                armed_path = run / report["artifacts"]["armed"]["path"]
                armed = json.loads(armed_path.read_text(encoding="utf-8"))
                mutate(armed)
                armed_path.write_text(json.dumps(armed) + "\n", encoding="utf-8")
                digest = sha256_file(armed_path)
                report["artifacts"]["armed"]["sha256"] = digest
                report["crash_attestation"]["armed_sha256"] = digest
                with self.assertRaisesRegex(AgentError, "process identity chain"):
                    _validate_crash_success_payload(report, run)

    def test_public_red_cleanup_rejects_still_active_pinned_member(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-red-active-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            report["crash_attestation"]["pinned_process_exit_codes"]["ck3"] = 259
            self._finalize(run, report, ok=False)
            with self.assertRaisesRegex(AgentError, "exit codes"):
                validate_crash_report(run)

    def test_public_red_accepts_complete_cleanup_with_partial_postflight(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-red-postflight-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            del report["production_tree_unchanged"]
            report["postflight_error"] = "profile verification failed after storage proof"
            self._finalize(run, report, ok=False)
            self.assertFalse(validate_crash_report(run)["ok"])

    def test_public_red_validator_rejects_fake_cleanup_shortcut(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-public-red-") as temporary:
            run = self._run(temporary)
            report = self._report(run)
            armed_path = run / report["artifacts"]["armed"]["path"]
            armed = json.loads(armed_path.read_text(encoding="utf-8"))
            armed["process_resumed"] = False
            armed_path.write_text(json.dumps(armed) + "\n", encoding="utf-8")
            digest = sha256_file(armed_path)
            report["artifacts"]["armed"]["sha256"] = digest
            report["crash_attestation"]["armed_sha256"] = digest
            self._finalize(run, report, ok=False)
            with self.assertRaisesRegex(AgentError, "handoff or armed payload"):
                validate_crash_report(run)


class CrashSubjectInvocationTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[EnvironmentSpec, dict[str, object]]:
        spec = EnvironmentSpec(root / "state", root / "game")
        run = spec.state_dir / "runs" / "20260822T010203Z-crash-deadbeef"
        artifacts = run / "artifacts"
        artifacts.mkdir(parents=True)
        nonce = "a" * 32
        armed = artifacts / f"armed-{nonce}.json"
        final = artifacts / f"watchdog-final-{nonce}.json"
        handoff = artifacts / f"handoff-{nonce}.json"
        owner = spec.state_dir / "control" / "owner.json"
        owner.parent.mkdir(parents=True)
        owner.write_text(
            json.dumps(
                {
                    "pid": 10,
                    "purpose": "crash-smoke",
                    "state_dir": str(spec.state_dir.resolve()),
                }
            ),
            encoding="utf-8",
        )
        outer = {
            "pid": 10,
            "executable": str(Path(sys.executable).resolve()),
            "creation_date": "outer-created",
            "command_line": f"{ROOT / 'agent.py'} crash-smoke",
        }
        payload = {
            "format_version": 1,
            "probe_nonce": nonce,
            "run_id": run.name,
            "state_dir": str(spec.state_dir.resolve()),
            "artifacts": str(artifacts.resolve()),
            "armed": str(armed.resolve()),
            "watchdog_final": str(final.resolve()),
            "outer": outer,
            "environment_sha256": "e" * 64,
            "owner_sha256": sha256_file(owner),
        }
        handoff.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        return spec, {
            "nonce": nonce,
            "artifacts": artifacts,
            "armed": armed,
            "final": final,
            "handoff": handoff,
            "handoff_sha256": sha256_file(handoff),
            "outer": outer,
        }

    def test_rejects_artifact_path_outside_exact_run_before_launch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-subject-path-") as temporary:
            root = Path(temporary)
            spec, fixture = self._fixture(root)
            with self.assertRaisesRegex(AgentError, "outside its exact run"):
                _validate_subject_invocation(
                    spec,
                    probe_nonce=fixture["nonce"],
                    handoff_path=fixture["handoff"],
                    handoff_sha256=fixture["handoff_sha256"],
                    armed_path=fixture["armed"],
                    watchdog_final=fixture["final"],
                    artifacts=root / "outside",
                    outer_identity=fixture["outer"],
                )

    def test_rejects_non_parent_outer_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-subject-parent-") as temporary:
            spec, fixture = self._fixture(Path(temporary))
            current = {"pid": 20, "parent_pid": 999}
            actual_outer = {
                **fixture["outer"],
                "command_line": str(fixture["outer"]["command_line"]),
            }
            with mock.patch(
                "xar_autoplayer.crash_probe._process_identity",
                side_effect=[current, actual_outer],
            ), self.assertRaisesRegex(AgentError, "not a direct child"):
                _validate_subject_invocation(
                    spec,
                    probe_nonce=fixture["nonce"],
                    handoff_path=fixture["handoff"],
                    handoff_sha256=fixture["handoff_sha256"],
                    armed_path=fixture["armed"],
                    watchdog_final=fixture["final"],
                    artifacts=fixture["artifacts"],
                    outer_identity=fixture["outer"],
                )

    def test_rejects_existing_armed_evidence_before_process_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-subject-existing-") as temporary:
            spec, fixture = self._fixture(Path(temporary))
            fixture["armed"].write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(AgentError, "already exists"):
                _validate_subject_invocation(
                    spec,
                    probe_nonce=fixture["nonce"],
                    handoff_path=fixture["handoff"],
                    handoff_sha256=fixture["handoff_sha256"],
                    armed_path=fixture["armed"],
                    watchdog_final=fixture["final"],
                    artifacts=fixture["artifacts"],
                    outer_identity=fixture["outer"],
                )

    def test_accepts_public_relative_script_and_console_entry_commands(self) -> None:
        commands = (
            r'python.exe ck3_autonomous_player\agent.py crash-smoke',
            r'xar-autoplayer.exe --state-dir C:\AgentState crash-smoke',
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory(
                prefix="xar-subject-public-command-"
            ) as temporary:
                spec, fixture = self._fixture(Path(temporary))
                current = {"pid": 20, "parent_pid": 10}
                actual_outer = {
                    **fixture["outer"],
                    "command_line": command,
                }
                with mock.patch(
                    "xar_autoplayer.crash_probe._process_identity",
                    side_effect=[current, actual_outer],
                ), mock.patch(
                    "xar_autoplayer.crash_probe._require_mutex_owned_elsewhere"
                ) as mutex:
                    result = _validate_subject_invocation(
                        spec,
                        probe_nonce=fixture["nonce"],
                        handoff_path=fixture["handoff"],
                        handoff_sha256=fixture["handoff_sha256"],
                        armed_path=fixture["armed"],
                        watchdog_final=fixture["final"],
                        artifacts=fixture["artifacts"],
                        outer_identity=fixture["outer"],
                    )
                self.assertEqual(result["probe_nonce"], fixture["nonce"])
                self.assertEqual(mutex.call_count, 2)


@unittest.skipUnless(os.name == "nt", "Windows named Job crash contract")
class NamedJobCrashIntegrationTests(unittest.TestCase):
    def test_existing_named_job_is_rejected(self) -> None:
        name = f"XarAutoplayer-TestCrash-{uuid.uuid4().hex}"
        job = _create_kill_on_close_job(name)
        try:
            with self.assertRaisesRegex(AgentError, "already exists"):
                _create_kill_on_close_job(name)
        finally:
            _close_job(job)

    def test_owner_death_destroys_named_job_and_spawned_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-job-") as temporary:
            root = Path(temporary).resolve()
            ready = root / "ready.json"
            job_name = f"XarAutoplayer-TestCrash-{uuid.uuid4().hex}"
            code = (
                "import pathlib,sys;"
                "sys.path.insert(0,sys.argv[1]);"
                "from xar_autoplayer.crash_probe import _run_named_job_owner_fixture;"
                "_run_named_job_owner_fixture(pathlib.Path(sys.argv[2]),sys.argv[3])"
            )
            owner = subprocess.Popen(
                [sys.executable, "-c", code, str(PACKAGE_ROOT), str(ready), job_name]
            )
            pins: list[object] = []
            try:
                deadline = time.monotonic() + 10
                while not ready.is_file() and time.monotonic() < deadline:
                    if owner.poll() is not None:
                        self.fail(f"Job owner exited early: {owner.returncode}")
                    time.sleep(0.05)
                self.assertTrue(ready.is_file())
                payload = json.loads(ready.read_text(encoding="utf-8"))
                self.assertGreaterEqual(payload["job_active_processes"], 2)
                owner_pin = _pin_process(payload["owner"], allow_terminate=True)
                parent_pin = _pin_process(payload["sentinel_parent"])
                child_pin = _pin_process(payload["sentinel_child"])
                pins.extend([owner_pin, parent_pin, child_pin])

                import win32api

                win32api.TerminateProcess(owner_pin, 91)
                _wait_pinned_exit(owner_pin, "fixture owner", 10)
                _wait_pinned_exit(parent_pin, "fixture sentinel parent", 10)
                _wait_pinned_exit(child_pin, "fixture sentinel child", 10)
                owner.wait(timeout=5)
                self.assertEqual(owner.returncode, 91)
                _wait_named_job_absent(job_name)
                self.assertTrue(_named_job_absent(job_name))
            finally:
                if owner.poll() is None:
                    owner.terminate()
                    owner.wait(timeout=5)
                if pins:
                    import win32api

                    for pinned in reversed(pins):
                        win32api.CloseHandle(pinned)

    def test_outer_death_during_prearm_wait_reclaims_subject_job_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-crash-outer-guard-") as temporary:
            root = Path(temporary).resolve()
            ready = root / "ready.json"
            job_name = f"XarAutoplayer-TestCrash-{uuid.uuid4().hex}"
            code = (
                "import pathlib,sys;"
                "sys.path.insert(0,sys.argv[1]);"
                "from xar_autoplayer.crash_probe import _run_outer_guard_outer_fixture;"
                "_run_outer_guard_outer_fixture(pathlib.Path(sys.argv[2]),"
                "sys.argv[3],pathlib.Path(sys.argv[1]))"
            )
            outer = subprocess.Popen(
                [sys.executable, "-c", code, str(PACKAGE_ROOT), str(ready), job_name]
            )
            pins: list[object] = []
            try:
                deadline = time.monotonic() + 12
                while not ready.is_file() and time.monotonic() < deadline:
                    if outer.poll() is not None:
                        self.fail(f"outer fixture exited early: {outer.returncode}")
                    time.sleep(0.05)
                self.assertTrue(ready.is_file())
                payload = json.loads(ready.read_text(encoding="utf-8"))
                self.assertGreaterEqual(payload["job_active_processes"], 2)
                outer_pin = _pin_process(payload["outer"], allow_terminate=True)
                subject_pin = _pin_process(
                    payload["subject"], allow_terminate=True
                )
                parent_pin = _pin_process(payload["sentinel_parent"])
                child_pin = _pin_process(payload["sentinel_child"])
                pins.extend([outer_pin, subject_pin, parent_pin, child_pin])

                import win32api

                win32api.TerminateProcess(outer_pin, 92)
                self.assertEqual(_wait_pinned_exit(outer_pin, "outer fixture", 10), 92)
                self.assertEqual(
                    _wait_pinned_exit(subject_pin, "outer-guard subject", 10),
                    86,
                )
                _wait_pinned_exit(parent_pin, "outer-guard sentinel parent", 10)
                _wait_pinned_exit(child_pin, "outer-guard sentinel child", 10)
                outer.wait(timeout=5)
                self.assertEqual(outer.returncode, 92)
                _wait_named_job_absent(job_name)
            finally:
                if outer.poll() is None:
                    outer.terminate()
                    outer.wait(timeout=5)
                if pins:
                    import win32api

                    for pinned in reversed(pins):
                        try:
                            win32api.CloseHandle(pinned)
                        except Exception:
                            pass


if __name__ == "__main__":
    unittest.main()
