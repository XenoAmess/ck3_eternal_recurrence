from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_g2_source_specific_war_loss_live_adapter.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_source_specific_war_loss_live_adapter_v1_manifest.json"
)
SPEC = importlib.util.spec_from_file_location("g2_source_live_adapter", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)


PID = 43210


class _Completed:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.stdout = "PASS"
        self.stderr = ""


class _Process:
    def __init__(self, pid: int = PID, running: bool = True) -> None:
        self.pid = pid
        self.running = running
        self.returncode = None if running else 0
        self.wait_calls: list[float] = []

    def poll(self) -> int | None:
        return None if self.running else self.returncode

    def wait(self, timeout: float) -> int:
        self.wait_calls.append(timeout)
        self.running = False
        self.returncode = 0
        return 0


class _Driver:
    def __init__(self, pid: int = PID, *, paused: bool = True) -> None:
        self.pid = pid
        self.paused = paused
        self.close_calls = 0

    def diagnostics(self) -> dict[str, object]:
        return {"bridge_pid": self.pid, "connection_generation": 1}

    def take_snapshot(self) -> dict[str, object]:
        return {
            "paused": self.paused,
            "map_ready": True,
            "played_character": {"character_id": 29829},
            "episode_run_id": "native-29829-source",
            "snapshot_id": "native:7",
            "revision": 8,
            "native_revision": 7,
            "date_raw": 53150000,
        }

    def close(self) -> None:
        self.close_calls += 1


def _paths(root: Path) -> object:
    return ADAPTER.AdapterPaths(
        game_executable=root / "ck3.exe",
        capture_executable=root / "capture.exe",
        bridge_dll=root / "bridge.dll",
        bridge_injector=root / "injector.exe",
        bookmark_events=root / "bookmark_events.txt",
    )


def _timeouts(bridge_attach_seconds: float = 1.0) -> object:
    return ADAPTER.AdapterTimeouts(
        process_discovery_seconds=1.0,
        main_menu_seconds=1,
        main_menu_stage_seconds=(1,),
        private_attach_seconds=1.0,
        map_hud_seconds=1.0,
        natural_event_seconds=1.0,
        observer_timeout_ms=1000,
        post_selection_seconds=1.0,
        bridge_attach_seconds=bridge_attach_seconds,
    )


def _write_profile_settings_template(root: Path) -> Path:
    template = root / "known-good-profile" / "pdx_settings.txt"
    template.parent.mkdir(parents=True)
    template.write_text(
        '\n'.join(
            [
                '"game"={',
                '  "Graphics"={',
                '    renderer="dx11"',
                '  }',
                '  "System"={',
                '    language="l_english"',
                '  }',
                '}',
            ]
            + [f'padding_{index}="{"x" * 64}"' for index in range(24)]
        )
        + "\n",
        encoding="utf-8",
    )
    cache = template.parent / "shadercache" / "dx11"
    for lane in ("ps_5_0", "vs_5_0"):
        target = cache / lane
        target.mkdir(parents=True)
        (target / f"{lane}.bin").write_bytes(b"compiled-shader")
        (target / f"{lane}.scache").write_bytes(b"cache-record")
    return template


def _installed_game_root() -> Path:
    candidates = (
        ADAPTER.REPOSITORY_ROOT / "Crusader Kings III",
        ADAPTER.REPOSITORY_ROOT.parent / "Crusader Kings III",
    )
    for candidate in candidates:
        if (
            (candidate / "binaries" / "ck3.exe").is_file()
            and (candidate / "game" / "events" / "bookmark_events.txt").is_file()
        ):
            return candidate
    return candidates[0]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _write_resume_save(root: Path) -> tuple[Path, str]:
    payload = b"SAV0101fixture-header-1.19.0.6\n" + (b"checkpoint" * 64)
    path = root / "source" / "resume.ck3"
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    return path, _sha256(payload)


def _write_self_contained_manifest(
    root: Path,
) -> tuple[Path, Path, Path, Path, str]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dependencies = root / "dependencies"
    dependencies.mkdir()
    for name in manifest["paths"]:
        if name in {"game_executable", "bookmark_events"}:
            manifest["paths"][name] = str(root / "manifest-missing" / name)
            continue
        payload = f"dependency:{name}".encode("utf-8")
        path = dependencies / f"{name}.bin"
        path.write_bytes(payload)
        manifest["paths"][name] = str(path)
        manifest["sha256"][name] = _sha256(payload)

    game_root = root / "installed-game"
    game_executable = game_root / "binaries" / "ck3.exe"
    bookmark_events = game_root / "game" / "events" / "bookmark_events.txt"
    game_executable.parent.mkdir(parents=True)
    bookmark_events.parent.mkdir(parents=True)
    game_payload = b"exact-build-game-executable"
    bookmark_payload = b"exact-bookmark-events-source"
    game_executable.write_bytes(game_payload)
    bookmark_events.write_bytes(bookmark_payload)
    manifest["sha256"]["game_executable"] = _sha256(game_payload)
    manifest["sha256"]["bookmark_events"] = _sha256(bookmark_payload)

    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return (
        manifest_path,
        game_root,
        game_executable,
        bookmark_events,
        _sha256(game_payload),
    )


def _relocate_runtime_binaries(
    manifest_path: Path,
    destination: Path,
) -> dict[str, Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    destination.mkdir()
    relocated: dict[str, Path] = {}
    for name in ("capture_executable", "bridge_dll", "bridge_injector"):
        source = Path(manifest["paths"][name])
        target = destination / source.name
        target.write_bytes(source.read_bytes())
        relocated[name] = target
    return relocated


class G2SourceSpecificWarLossLiveAdapterTests(unittest.TestCase):
    def test_resume_checkpoint_requires_an_exact_hash_bound_save(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save, digest = _write_resume_save(root)
            evidence = ADAPTER.inspect_resume_checkpoint(save, digest)
            self.assertEqual(evidence["status"], "READY_TO_COPY")
            self.assertEqual(evidence["game_version"], "1.19.0.6")
            with self.assertRaisesRegex(
                ADAPTER.LiveAdapterError, "must be supplied together"
            ):
                ADAPTER.inspect_resume_checkpoint(save, None)
            with self.assertRaisesRegex(ADAPTER.LiveAdapterError, "SHA-256 drifted"):
                ADAPTER.inspect_resume_checkpoint(save, "A" * 64)

    def test_resume_checkpoint_copy_is_verified_before_popen(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            userdir = root / "userdir"
            userdir.mkdir()
            template = _write_profile_settings_template(root)
            save, digest = _write_resume_save(root)
            process = _Process()
            popen = mock.Mock(return_value=process)
            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=userdir,
                profile_settings_template=template,
                resume_save=save,
                resume_save_sha256=digest,
                process_inventory=lambda: [],
                popen=popen,
            )
            with mock.patch.object(
                operations, "_validate_owned_ck3", return_value={"pid": PID}
            ):
                receipt = asyncio.run(
                    operations.launch_normal_event_process(object())
                )

            popen.assert_called_once()
            self.assertEqual(receipt["startup_mode"], "normal-event")
            self.assertEqual(receipt["startup_source"], "resume-checkpoint")
            copied = userdir / "save games" / "autosave.ck3"
            self.assertEqual(copied.read_bytes(), save.read_bytes())
            self.assertEqual(
                receipt["resume_checkpoint"]["destination_sha256"], digest
            )

    def test_resume_navigation_uses_continue_game_once(self) -> None:
        acceptance = mock.Mock()
        acceptance.MAIN_MENU_REGION = (0.0, 0.0, 1.0, 1.0)
        acceptance.wait_for_ocr_text.return_value = (640, 720)
        ADAPTER.navigate_resume_checkpoint(acceptance, Path("evidence"))
        acceptance.wait_for_ocr_text.assert_called_once_with(
            "继续游戏",
            acceptance.MAIN_MENU_REGION,
            30,
            Path("evidence"),
            "01_resume_checkpoint.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.deliberate_click.assert_called_once_with(
            (640, 720), "main-menu Continue Game"
        )

    def test_target_option_tokens_arm_before_generic_recovery(self) -> None:
        acceptance = mock.Mock()
        acceptance.EVENT_OPTIONS_FULL_REGION = (0.2, 0.5, 0.8, 0.9)
        acceptance.find_ocr_text.return_value = None
        acceptance.ocr_results.return_value = [
            ("我会将他扶上君士坦丁堡", (930, 1043), (700, 1020, 1120, 1060), 0.91),
            ("的皇位！", (930, 1070), (850, 1058, 1010, 1082), 0.89),
        ]

        option = ADAPTER._find_target_option(acceptance, object())

        self.assertEqual(option, (930, 1043))
        acceptance.find_ocr_text.assert_called_once()
        acceptance.quick_stall_and_recover.assert_not_called()

        acceptance.ocr_results.return_value = [
            ("君士坦丁堡见闻", (930, 1043), (700, 1020, 1120, 1060), 0.91),
        ]
        self.assertIsNone(ADAPTER._find_target_option(acceptance, object()))

    def test_chancellor_task_1004_requires_body_and_exact_option_region(self) -> None:
        acceptance = mock.Mock()
        acceptance.EVENT_OPTIONS_FULL_REGION = (0.2, 0.5, 0.8, 0.9)
        acceptance.find_ocr_text.return_value = (1266, 984)
        image = object()

        option = ADAPTER._find_chancellor_task_1004_option(
            acceptance,
            image,
            "我已经和你的掌玺大臣交流过了 这是可耻的外交行为 "
            "这之间一定是有一些可怕的误会",
        )

        self.assertEqual(option, (1266, 984))
        acceptance.find_ocr_text.assert_called_once_with(
            image,
            ADAPTER.CHANCELLOR_TASK_1004_OPTION,
            acceptance.EVENT_OPTIONS_FULL_REGION,
            contains=True,
        )

        acceptance.reset_mock()
        self.assertIsNone(
            ADAPTER._find_chancellor_task_1004_option(
                acceptance, image, "这之间一定是有一些可怕的误会"
            )
        )
        acceptance.find_ocr_text.assert_not_called()

    def test_natural_event_blocker_uses_verified_ocr_recovery(self) -> None:
        acceptance = mock.Mock()
        acceptance.quick_stall_and_recover.return_value = {
            "text": "They grow up fast.",
            "center": [930, 1043],
        }

        selected = ADAPTER._recover_natural_event_blocker(
            acceptance, Path("evidence"), 4
        )

        self.assertEqual(selected["center"], [930, 1043])
        acceptance.quick_stall_and_recover.assert_called_once_with(
            Path("evidence"), "g2-source-specific-natural-event", 4
        )

        acceptance.quick_stall_and_recover.return_value = None
        acceptance.set_speed_five_and_unpause.return_value = 394_550
        resumed = ADAPTER._recover_natural_event_blocker(
            acceptance, Path("evidence"), 5
        )
        self.assertTrue(resumed["timeline_progress_verified"])
        self.assertEqual(resumed["game_day"], 394_550)
        acceptance.set_speed_five_and_unpause.assert_called_once_with(
            Path("evidence"), "g2-no-modal-stall-5", require_progress=True
        )

        acceptance.set_speed_five_and_unpause.side_effect = RuntimeError(
            "date remained frozen"
        )
        with self.assertRaisesRegex(
            ADAPTER.LiveAdapterError, "timeline progress could not be restored"
        ):
            ADAPTER._recover_natural_event_blocker(
                acceptance, Path("evidence"), 6
            )

    def test_inventory_falls_back_to_toolhelp_when_wmi_is_denied(self) -> None:
        fallback = [{"Name": "ck3.exe", "ProcessId": PID}]
        with (
            mock.patch.object(
                ADAPTER.source_ui,
                "process_inventory",
                side_effect=RuntimeError("WMI access denied"),
            ),
            mock.patch.object(
                ADAPTER, "_toolhelp_process_inventory", return_value=fallback
            ) as toolhelp,
        ):
            self.assertEqual(ADAPTER._process_inventory(), fallback)
        toolhelp.assert_called_once_with()

    def test_toolhelp_row_preserves_exact_owned_pid_path_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / "ck3.exe"
            executable.write_bytes(b"exact-build-fixture")
            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=root / "userdir",
                process_inventory=lambda: [
                    {
                        "ProcessId": PID,
                        "ParentProcessId": 1,
                        "Name": "ck3.exe",
                        "ExecutablePath": str(executable),
                        "InventorySource": "toolhelp32",
                    }
                ],
            )
            with mock.patch.object(
                ADAPTER, "EXPECTED_EXE_SHA256", ADAPTER._sha256_file(executable)
            ):
                identity = operations._validate_owned_ck3(PID)
        self.assertEqual(identity["pid"], PID)
        self.assertEqual(identity["name"], "ck3.exe")
        self.assertEqual(identity["inventory_source"], "toolhelp32")
        self.assertEqual(identity["executable_path"], str(executable.resolve()))

    def test_frozen_preflight_is_no_launch_and_exposes_speed_five_command(self) -> None:
        inventory = [{"Name": "ck3.exe", "ProcessId": 999}]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "preflight.json"
            template = _write_profile_settings_template(root)
            calls = 0

            def unchanged_inventory() -> list[dict[str, object]]:
                nonlocal calls
                calls += 1
                return inventory

            report = ADAPTER.run_no_launch_preflight(
                MANIFEST,
                output,
                process_inventory=unchanged_inventory,
                profile_settings_template=template,
                inspect_profile_settings_template=True,
                game_root=_installed_game_root(),
            )
            self.assertEqual(calls, 2)
            self.assertEqual(report["process_inventory_before"], inventory)
            self.assertEqual(report["process_inventory_after"], inventory)
            self.assertEqual(report["status"], ADAPTER.PREFLIGHT_STATUS)
            self.assertTrue(report["live_command"]["available"])
            self.assertTrue(report["live_command"]["default_off"])
            self.assertTrue(report["live_command"]["startup_profile_asset_gate"])
            self.assertTrue(
                report["live_command"]["asset_failure_blocks_before_popen"]
            )
            self.assertEqual(
                report["startup_profile_template"]["inspection"],
                "validated-without-copy",
            )
            self.assertGreater(
                report["startup_profile_template"]["source_pair"]["shadercache"][
                    "file_count"
                ],
                0,
            )
            self.assertEqual(report["live_command"]["timeline_speed"], 5)
            self.assertFalse(report["boundaries"]["source_specific_loss_ready"])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)

    def test_manifest_pins_concrete_same_pid_composition(self) -> None:
        manifest, paths, timeouts, checked = ADAPTER._load_manifest(
            MANIFEST, game_root=_installed_game_root()
        )
        composition = manifest["composition"]
        self.assertTrue(composition["concrete_live_adapter_implemented"])
        self.assertTrue(composition["observer_detach_before_bridge"])
        self.assertTrue(composition["same_pid_bridge_attach"])
        self.assertTrue(composition["outer_owner_final_cleanup_only"])
        self.assertTrue(composition["expected_date_bound_from_bridge_snapshot"])
        self.assertFalse(composition["standalone_capture_runner_main_reused"])
        self.assertTrue(composition["startup_profile_asset_gate_integrated"])
        self.assertTrue(composition["launch_fail_closed"])
        self.assertEqual(timeouts.natural_event_seconds, 520.0)
        self.assertEqual(timeouts.observer_timeout_ms, 1_200_000)
        self.assertEqual(paths.game_executable.name, "ck3.exe")
        self.assertIn("adapter", checked)

    def test_explicit_game_root_yields_a_complete_exact_hash_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (
                manifest_path,
                game_root,
                game_executable,
                bookmark_events,
                expected_game_sha256,
            ) = _write_self_contained_manifest(root)
            output = root / "preflight.json"
            template = _write_profile_settings_template(root)
            with mock.patch.object(
                ADAPTER, "EXPECTED_EXE_SHA256", expected_game_sha256
            ):
                report = ADAPTER.run_no_launch_preflight(
                    manifest_path,
                    output,
                    repo_root=root,
                    process_inventory=lambda: [],
                    profile_settings_template=template,
                    inspect_profile_settings_template=True,
                    game_root=game_root,
                )

        self.assertEqual(len(report["dependencies"]), 14)
        self.assertTrue(report["game_source_binding"]["exact_hashes_verified"])
        self.assertEqual(
            report["dependencies"]["game_executable"]["path"],
            str(game_executable.resolve()),
        )
        self.assertEqual(
            report["dependencies"]["bookmark_events"]["path"],
            str(bookmark_events.resolve()),
        )
        self.assertEqual(
            report["dependencies"]["game_executable"]["path_source"],
            "explicit-game-root",
        )
        self.assertEqual(
            report["dependencies"]["bookmark_events"]["path_source"],
            "explicit-game-root",
        )

    def test_explicit_files_override_game_root_but_cannot_bypass_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (
                manifest_path,
                _game_root,
                game_executable,
                bookmark_events,
                expected_game_sha256,
            ) = _write_self_contained_manifest(root)
            unavailable_root = root / "unavailable-game-root"
            with mock.patch.object(
                ADAPTER, "EXPECTED_EXE_SHA256", expected_game_sha256
            ):
                _manifest, paths, _timeouts, checked = ADAPTER._load_manifest(
                    manifest_path,
                    repo_root=root,
                    game_root=unavailable_root,
                    game_executable=game_executable,
                    bookmark_events=bookmark_events,
                )
                bad_executable = root / "wrong-ck3.exe"
                bad_executable.write_bytes(b"wrong-build")
                with self.assertRaisesRegex(
                    ADAPTER.LiveAdapterError,
                    "manifest dependency drifted: game_executable",
                ):
                    ADAPTER._load_manifest(
                        manifest_path,
                        repo_root=root,
                        game_root=unavailable_root,
                        game_executable=bad_executable,
                        bookmark_events=bookmark_events,
                    )

        self.assertEqual(paths.game_executable, game_executable.resolve())
        self.assertEqual(paths.bookmark_events, bookmark_events.resolve())
        self.assertEqual(
            checked["game_executable"]["path_source"],
            "explicit-game-executable",
        )
        self.assertEqual(
            checked["bookmark_events"]["path_source"],
            "explicit-bookmark-events",
        )

    def test_explicit_runtime_binaries_override_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (
                manifest_path,
                game_root,
                _game_executable,
                _bookmark_events,
                expected_game_sha256,
            ) = _write_self_contained_manifest(root)
            relocated = _relocate_runtime_binaries(
                manifest_path, root / "relocated-runtime"
            )
            with mock.patch.object(
                ADAPTER, "EXPECTED_EXE_SHA256", expected_game_sha256
            ):
                _manifest, paths, _timeouts, checked = ADAPTER._load_manifest(
                    manifest_path,
                    repo_root=root,
                    game_root=game_root,
                    capture_executable=relocated["capture_executable"],
                    bridge_dll=relocated["bridge_dll"],
                    bridge_injector=relocated["bridge_injector"],
                )

        self.assertEqual(
            paths.capture_executable, relocated["capture_executable"].resolve()
        )
        self.assertEqual(paths.bridge_dll, relocated["bridge_dll"].resolve())
        self.assertEqual(
            paths.bridge_injector, relocated["bridge_injector"].resolve()
        )
        self.assertEqual(
            checked["capture_executable"]["path_source"],
            "explicit-capture-executable",
        )
        self.assertEqual(
            checked["bridge_dll"]["path_source"], "explicit-bridge-dll"
        )
        self.assertEqual(
            checked["bridge_injector"]["path_source"],
            "explicit-bridge-injector",
        )

    def test_explicit_runtime_binary_hash_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (
                manifest_path,
                game_root,
                _game_executable,
                _bookmark_events,
                expected_game_sha256,
            ) = _write_self_contained_manifest(root)
            relocated = _relocate_runtime_binaries(
                manifest_path, root / "relocated-runtime"
            )
            relocated["bridge_dll"].write_bytes(b"wrong-bridge-dll")
            with (
                mock.patch.object(
                    ADAPTER, "EXPECTED_EXE_SHA256", expected_game_sha256
                ),
                self.assertRaisesRegex(
                    ADAPTER.LiveAdapterError,
                    "manifest dependency drifted: bridge_dll",
                ),
            ):
                ADAPTER._load_manifest(
                    manifest_path,
                    repo_root=root,
                    game_root=game_root,
                    capture_executable=relocated["capture_executable"],
                    bridge_dll=relocated["bridge_dll"],
                    bridge_injector=relocated["bridge_injector"],
                )

    def test_manifest_runtime_binary_paths_remain_the_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (
                manifest_path,
                game_root,
                _game_executable,
                _bookmark_events,
                expected_game_sha256,
            ) = _write_self_contained_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            with mock.patch.object(
                ADAPTER, "EXPECTED_EXE_SHA256", expected_game_sha256
            ):
                _manifest, paths, _timeouts, checked = ADAPTER._load_manifest(
                    manifest_path,
                    repo_root=root,
                    game_root=game_root,
                )

        self.assertEqual(
            paths.capture_executable,
            Path(manifest["paths"]["capture_executable"]).resolve(),
        )
        self.assertEqual(
            paths.bridge_dll, Path(manifest["paths"]["bridge_dll"]).resolve()
        )
        self.assertEqual(
            paths.bridge_injector,
            Path(manifest["paths"]["bridge_injector"]).resolve(),
        )
        for name in ("capture_executable", "bridge_dll", "bridge_injector"):
            self.assertEqual(checked[name]["path_source"], "manifest")

    def test_profile_asset_failure_blocks_before_popen_and_writes_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "userdir").mkdir()
            popen = mock.Mock()

            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=root / "userdir",
                profile_settings_template=root / "missing" / "pdx_settings.txt",
                process_inventory=lambda: [],
                popen=popen,
            )
            with self.assertRaisesRegex(
                ADAPTER.LiveAdapterError, "startup profile asset gate blocked"
            ):
                asyncio.run(operations.launch_normal_event_process(object()))
            popen.assert_not_called()
            evidence_path = root / "artifacts" / "startup-profile-assets.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["status"], "BLOCKED")
            self.assertFalse(evidence["profile_ready"])
            self.assertIsNone(evidence["settings"]["destination_sha256"])

    def test_profile_assets_are_copied_and_verified_before_popen(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            userdir = root / "userdir"
            userdir.mkdir()
            template = _write_profile_settings_template(root)
            process = _Process()
            popen = mock.Mock(return_value=process)
            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=userdir,
                profile_settings_template=template,
                process_inventory=lambda: [],
                popen=popen,
            )
            with mock.patch.object(
                operations, "_validate_owned_ck3", return_value={"pid": PID}
            ):
                receipt = asyncio.run(
                    operations.launch_normal_event_process(object())
                )

            popen.assert_called_once()
            evidence = receipt["startup_profile_assets"]
            self.assertEqual(evidence["status"], "GREEN")
            self.assertTrue(evidence["profile_ready"])
            self.assertEqual(
                evidence["settings"]["source_sha256"],
                evidence["settings"]["destination_sha256"],
            )
            self.assertEqual(
                evidence["settings"]["source_bytes"],
                evidence["settings"]["destination_bytes"],
            )
            self.assertGreater(evidence["shadercache"]["file_count"], 0)
            self.assertGreater(evidence["shadercache"]["bytes"], 0)
            self.assertEqual(
                evidence["shadercache"]["source_manifest"]["tree_sha256"],
                evidence["shadercache"]["tree_sha256"],
            )
            self.assertTrue((userdir / "pdx_settings.txt").is_file())
            self.assertTrue((userdir / "shadercache").is_dir())

    def test_launch_discovers_exact_target_through_toolhelp_after_cim_denial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            userdir = root / "userdir"
            userdir.mkdir()
            executable = root / "ck3.exe"
            executable.write_bytes(b"exact-build-fixture")
            template = _write_profile_settings_template(root)
            process = _Process()
            target_row = {
                "ProcessId": PID,
                "ParentProcessId": 1,
                "Name": "ck3.exe",
                "ExecutablePath": str(executable),
                "InventorySource": "toolhelp32",
            }
            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=userdir,
                profile_settings_template=template,
                popen=mock.Mock(return_value=process),
            )
            with (
                mock.patch.object(
                    ADAPTER.source_ui,
                    "process_inventory",
                    side_effect=RuntimeError("Get-CimInstance Access denied"),
                ),
                mock.patch.object(
                    ADAPTER,
                    "_toolhelp_process_inventory",
                    side_effect=[[], [target_row]],
                ) as toolhelp,
                mock.patch.object(
                    ADAPTER,
                    "EXPECTED_EXE_SHA256",
                    ADAPTER._sha256_file(executable),
                ),
            ):
                receipt = asyncio.run(
                    operations.launch_normal_event_process(object())
                )
        self.assertEqual(receipt["pid"], PID)
        self.assertEqual(toolhelp.call_count, 2)
        self.assertTrue(process.running)

    def test_launch_discovery_failure_reclaims_process_after_asset_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            userdir = root / "userdir"
            userdir.mkdir()
            template = _write_profile_settings_template(root)
            process = _Process()
            commands: list[list[str]] = []
            timeouts = _timeouts()
            timeouts = ADAPTER.AdapterTimeouts(
                **{
                    **timeouts.__dict__,
                    "process_discovery_seconds": 0.0,
                }
            )

            def run_process(command: list[str], **_kwargs: object) -> _Completed:
                commands.append(command)
                process.running = False
                process.returncode = 0
                return _Completed()

            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=timeouts,
                artifact_dir=root / "artifacts",
                userdir=userdir,
                profile_settings_template=template,
                process_inventory=lambda: [],
                popen=lambda *_args, **_kwargs: process,
                run_process=run_process,
            )
            with self.assertRaisesRegex(
                ADAPTER.LiveAdapterError, "normally launched process was reclaimed"
            ):
                asyncio.run(operations.launch_normal_event_process(object()))

            self.assertEqual(
                commands,
                [["taskkill.exe", "/F", "/T", "/PID", str(PID)]],
            )
            self.assertEqual(process.wait_calls, [10])
            self.assertFalse(process.running)

    def test_explicit_pipe_attach_returns_only_a_paused_same_pid_driver(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            driver = _Driver()
            commands: list[list[str]] = []

            def run_process(command: list[str], **_kwargs: object) -> _Completed:
                commands.append(command)
                return _Completed()

            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=root / "userdir",
                process_inventory=lambda: [],
                driver_factory=lambda *_args, **_kwargs: driver,
                run_process=run_process,
            )
            observed = asyncio.run(operations.attach_bridge_to_pid({}, PID))
            binding = asyncio.run(operations.read_bridge_binding(observed))

            self.assertIs(observed, driver)
            self.assertEqual(binding["bridge_pid"], PID)
            self.assertEqual(binding["explicit_target_pid"], PID)
            self.assertTrue(binding["attached"])
            self.assertEqual(binding["played_character_id"], 29829)
            self.assertEqual(commands[0][1], "--pipe")
            self.assertTrue(commands[0][2].startswith(ADAPTER.PIPE_PREFIX))
            self.assertEqual(commands[0][3], str(PID))

    def test_continuation_binds_expected_date_from_same_bridge_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            driver = _Driver()
            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=root / "userdir",
                process_inventory=lambda: [],
            )
            operations._driver = driver
            operations._bridge_binding = {
                "bridge_pid": PID,
                "date_raw": 53149944,
            }
            expected_result = {"ok": True}
            with mock.patch.object(
                ADAPTER.outer.lifecycle,
                "run_same_lifecycle_sequence",
                new=mock.AsyncMock(return_value=expected_result),
            ) as continuation:
                result = asyncio.run(
                    operations.continue_same_lifecycle_from_bridge(
                        driver,
                        source_capture={"schema": "capture"},
                        capture_sha256="A" * 64,
                        expected_character_id=29829,
                        expected_date_raw=0,
                        postwar_timeout=45,
                    )
                )

            self.assertIs(result, expected_result)
            self.assertEqual(
                continuation.await_args.kwargs["expected_date_raw"], 53149944
            )
            self.assertEqual(
                continuation.await_args.kwargs["expected_war_id"],
                ADAPTER.EXPECTED_LIVE_WAR_ID,
            )

    def test_cli_requires_exact_war_id_and_external_runtime_paths(self) -> None:
        parser = ADAPTER._parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "--manifest", str(MANIFEST),
                    "--preflight-output", "preflight.json",
                    "--profile-settings-template", "pdx_settings.txt",
                    "--verify-only",
                ]
            )
        parsed = parser.parse_args(
            [
                "--manifest", str(MANIFEST),
                "--preflight-output", "preflight.json",
                "--profile-settings-template", "pdx_settings.txt",
                "--expected-war-id", str(ADAPTER.EXPECTED_LIVE_WAR_ID),
                "--verify-only",
            ]
        )
        self.assertEqual(parsed.expected_war_id, ADAPTER.EXPECTED_LIVE_WAR_ID)
        self.assertIsNone(parsed.resume_save)
        self.assertIsNone(parsed.resume_save_sha256)
        explicit_game_root = Path("explicit-game")
        explicit_game_executable = Path("explicit-ck3.exe")
        explicit_bookmark_events = Path("explicit-bookmark-events.txt")
        explicit_capture_executable = Path("explicit-capture.exe")
        explicit_bridge_dll = Path("explicit-bridge.dll")
        explicit_bridge_injector = Path("explicit-injector.exe")
        explicit_resume_save = Path("explicit-resume.ck3")
        explicit_resume_sha256 = "B" * 64
        parsed = parser.parse_args(
            [
                "--manifest", str(MANIFEST),
                "--preflight-output", "preflight.json",
                "--profile-settings-template", "pdx_settings.txt",
                "--expected-war-id", str(ADAPTER.EXPECTED_LIVE_WAR_ID),
                "--game-root", str(explicit_game_root),
                "--game-executable", str(explicit_game_executable),
                "--bookmark-events", str(explicit_bookmark_events),
                "--capture-executable", str(explicit_capture_executable),
                "--bridge-dll", str(explicit_bridge_dll),
                "--bridge-injector", str(explicit_bridge_injector),
                "--resume-save", str(explicit_resume_save),
                "--resume-save-sha256", explicit_resume_sha256,
                "--verify-only",
            ]
        )
        self.assertEqual(parsed.game_root, explicit_game_root)
        self.assertEqual(parsed.game_executable, explicit_game_executable)
        self.assertEqual(parsed.bookmark_events, explicit_bookmark_events)
        self.assertEqual(parsed.capture_executable, explicit_capture_executable)
        self.assertEqual(parsed.bridge_dll, explicit_bridge_dll)
        self.assertEqual(parsed.bridge_injector, explicit_bridge_injector)
        self.assertEqual(parsed.resume_save, explicit_resume_save)
        self.assertEqual(parsed.resume_save_sha256, explicit_resume_sha256)
        with self.assertRaisesRegex(
            ADAPTER.LiveAdapterError, "outside the repository"
        ):
            ADAPTER._require_external_runtime_paths(
                ADAPTER.REPOSITORY_ROOT / "_runtime" / "artifacts",
                ADAPTER.REPOSITORY_ROOT / "_runtime" / "userdir",
            )

        preflight = mock.Mock()
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(ADAPTER, "run_no_launch_preflight", preflight),
        ):
            root = Path(temporary)
            result = ADAPTER.main(
                [
                    "--manifest", str(MANIFEST),
                    "--preflight-output", str(root / "preflight.json"),
                    "--profile-settings-template", str(root / "pdx_settings.txt"),
                    "--expected-war-id", str(ADAPTER.EXPECTED_LIVE_WAR_ID + 1),
                    "--verify-only",
                ]
            )
        self.assertEqual(result, 2)
        preflight.assert_not_called()

        preflight = mock.Mock(return_value={"status": ADAPTER.PREFLIGHT_STATUS})
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(ADAPTER, "run_no_launch_preflight", preflight),
        ):
            root = Path(temporary)
            result = ADAPTER.main(
                [
                    "--manifest", str(MANIFEST),
                    "--preflight-output", str(root / "preflight.json"),
                    "--profile-settings-template", str(root / "pdx_settings.txt"),
                    "--expected-war-id", str(ADAPTER.EXPECTED_LIVE_WAR_ID),
                    "--capture-executable", str(explicit_capture_executable),
                    "--bridge-dll", str(explicit_bridge_dll),
                    "--bridge-injector", str(explicit_bridge_injector),
                    "--verify-only",
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(
            preflight.call_args.kwargs["capture_executable"],
            explicit_capture_executable,
        )
        self.assertEqual(
            preflight.call_args.kwargs["bridge_dll"], explicit_bridge_dll
        )
        self.assertEqual(
            preflight.call_args.kwargs["bridge_injector"],
            explicit_bridge_injector,
        )

    def test_bridge_pid_or_pause_drift_never_returns_a_driver(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            driver = _Driver(PID + 1, paused=False)
            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(bridge_attach_seconds=0.01),
                artifact_dir=root / "artifacts",
                userdir=root / "userdir",
                process_inventory=lambda: [],
                driver_factory=lambda *_args, **_kwargs: driver,
                run_process=lambda *_args, **_kwargs: _Completed(),
            )
            with self.assertRaisesRegex(ADAPTER.LiveAdapterError, "readiness timed out"):
                asyncio.run(operations.attach_bridge_to_pid({}, PID))
            self.assertEqual(driver.close_calls, 1)

    def test_outer_cleanup_targets_owned_process_once_and_clears_driver(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            driver = _Driver()
            process = _Process()
            observer = _Process(pid=9876, running=False)
            commands: list[list[str]] = []

            def run_process(command: list[str], **_kwargs: object) -> _Completed:
                commands.append(command)
                if command[0] == "taskkill.exe":
                    process.running = False
                    process.returncode = 0
                return _Completed()

            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=root / "userdir",
                process_inventory=lambda: [],
                run_process=run_process,
            )
            operations._process = process
            operations._observer = observer
            asyncio.run(operations.final_cleanup({}, driver, PID))

            self.assertEqual(driver.close_calls, 1)
            self.assertEqual(commands, [["taskkill.exe", "/F", "/T", "/PID", str(PID)]])
            self.assertTrue(operations._cleanup_receipt["ok"])
            with self.assertRaisesRegex(ADAPTER.LiveAdapterError, "more than once"):
                asyncio.run(operations.final_cleanup({}, driver, PID))

    def test_pause_uses_rendered_state_only_after_observer_handoff(self) -> None:
        class Acceptance:
            ACTIVE_CK3_PID = None

            def __init__(self) -> None:
                self.calls: list[tuple[Path, str]] = []

            def ensure_game_paused(self, path: Path, stem: str) -> None:
                self.calls.append((path, stem))

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            acceptance = Acceptance()
            operations = ADAPTER.ConcreteLiveOperations(
                paths=_paths(root),
                timeouts=_timeouts(),
                artifact_dir=root / "artifacts",
                userdir=root / "userdir",
                process_inventory=lambda: [],
            )
            operations._process = _Process()
            operations._acceptance = acceptance
            operations._image_grab = object()
            operations._pyautogui = object()
            with mock.patch.object(
                operations, "_validate_owned_ck3", return_value={"pid": PID}
            ):
                receipt = asyncio.run(operations.pause_owned_process({}, PID))
            self.assertEqual(
                receipt,
                {"pid": PID, "paused": True, "after_observer_detach": True},
            )
            self.assertEqual(
                acceptance.calls,
                [(operations.ui_dir, "g2-post-observer")],
            )


if __name__ == "__main__":
    unittest.main()
