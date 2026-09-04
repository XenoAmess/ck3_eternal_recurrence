from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_evaluated_days_current_pin_capture.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_evaluated_days_current_pin_live_manifest.json"
)
SPEC = importlib.util.spec_from_file_location(
    "prepare_g2_evaluated_days_current_pin_capture", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load preflight: {SCRIPT}")
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class G2EvaluatedDaysCurrentPinCapturePreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def _fixture(self, root: Path) -> tuple[dict[str, object], Path]:
        repo = root / "repo"
        repo.mkdir()
        runner = repo / "runner.py"
        analyzer = repo / "analyzer.py"
        source = repo / "source.txt"
        python = root / "python.exe"
        checkpoint = root / "checkpoint.ck3"
        driver = root / "driver-state.json"
        game_dir = root / "game"
        game_exe = game_dir / "binaries" / "ck3.exe"
        private_dll = root / "private.dll"
        injector = root / "injector.exe"
        source_zip = root / "source.zip"
        private_cache = root / "private-cache.txt"
        default_cache = root / "default-cache.txt"
        default_dll = root / "default.dll"
        jar = root / "kaishek.jar"
        for path, data in (
            (runner, b"runner"),
            (analyzer, b"analyzer"),
            (source, b"source"),
            (python, b"python"),
            (checkpoint, b"checkpoint"),
            (game_exe, b"game"),
            (
                private_dll,
                PREFLIGHT.PRIVATE_CAPTURE_SCHEMA.encode("ascii")
                + PREFLIGHT.PRIVATE_BOUNDARY_SCHEMA.encode("ascii")
                + PREFLIGHT.PRIVATE_CAPTURE_ENVIRONMENT.encode("utf-16le"),
            ),
            (injector, b"injector"),
            (source_zip, b"zip"),
            (default_dll, b"default"),
            (jar, b"jar"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        private_cache.write_text(
            "\n".join(
                (
                    "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1:BOOL=ON",
                    "XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1:BOOL=OFF",
                    "XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1:BOOL=OFF",
                )
            ),
            encoding="utf-8",
        )
        default_cache.write_text(
            "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1:BOOL=OFF\n",
            encoding="utf-8",
        )
        driver.write_text(
            json.dumps(
                {
                    "format_version": 2,
                    "pipe_name": r"\\.\pipe\fixture",
                    "episode_character_id": 29_829,
                    "episode_run_id": "fixture-episode",
                    "last_checkpoint": {
                        "sha256": _sha256(checkpoint),
                        "date_raw": 53_223_936,
                        "episode_character_id": 29_829,
                        "episode_run_id": "fixture-episode",
                    },
                }
            ),
            encoding="utf-8",
        )
        manifest = copy.deepcopy(self.manifest)
        manifest["paths"] = {
            "python": str(python),
            "runner": "runner.py",
            "analyzer": "analyzer.py",
            "source_checkpoint": str(checkpoint),
            "source_driver_state": str(driver),
            "game_dir": str(game_dir),
            "bridge_dll": str(private_dll),
            "bridge_injector": str(injector),
            "source_zip": str(source_zip),
            "private_cmake_cache": str(private_cache),
            "default_cmake_cache": str(default_cache),
            "default_bridge_dll": str(default_dll),
            "open_kaishek_checkout": str(root / "open_kaishek"),
            "open_kaishek_jar": str(jar),
            "fresh_attempt": str(root / "future-attempt"),
        }
        file_map = {
            "python": python,
            "runner": runner,
            "analyzer": analyzer,
            "checkpoint": checkpoint,
            "driver_state": driver,
            "game_executable": game_exe,
            "bridge_dll": private_dll,
            "bridge_injector": injector,
            "source_zip": source_zip,
            "private_cmake_cache": private_cache,
            "default_cmake_cache": default_cache,
            "default_bridge_dll": default_dll,
            "open_kaishek_jar": jar,
        }
        manifest["sha256"] = {name: _sha256(path) for name, path in file_map.items()}
        manifest["source_sha256"] = {"source.txt": _sha256(source)}
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest, repo

    @staticmethod
    def _open_audit(**_: object) -> dict[str, object]:
        return {
            "ok": True,
            "status": "GREEN_STATIC",
            "external": {
                "head": "135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b",
                "origin_main": "135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b",
                "clean": True,
            },
        }

    def test_committed_manifest_is_bounded_and_current_pin(self) -> None:
        PREFLIGHT.validate_manifest_contract(self.manifest)
        self.assertEqual(
            self.manifest["open_kaishek"]["commit"],
            "135113d3c1426a9d8f0c8c7d8368e3d525ab0d3b",
        )
        self.assertFalse(self.manifest["open_kaishek"]["native_certified"])
        self.assertFalse(self.manifest["open_kaishek"]["runtime_certified"])

    def test_unique_command_runs_runner_then_analyzer(self) -> None:
        commands = PREFLIGHT.build_commands(self.manifest, repo_root=ROOT.parents[0])
        combined = commands["combined"]
        self.assertEqual(combined.count("run_war_termination_terms_live_acceptance.py"), 1)
        self.assertEqual(combined.count("analyze_g2_evaluated_days_private_capture.py"), 1)
        self.assertEqual(combined.count("--war-id"), 1)
        self.assertEqual(combined.count("--expected-war-id"), 1)
        self.assertIn("$runnerExit = $LASTEXITCODE", combined)
        self.assertIn("if ($analysisExit -eq 0) { exit 0 }", combined)
        self.assertIn(PREFLIGHT.PRIVATE_CAPTURE_ENVIRONMENT, combined)
        for forbidden in ("surrender-war", "offer-white-peace", "enforce-demands", "life-advance"):
            self.assertNotIn(forbidden, combined)

    def test_full_preflight_green_with_exact_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, repo = self._fixture(root)
            report_path = root / "preflight.json"
            report = PREFLIGHT.run_preflight(
                root / "manifest.json",
                report_path,
                repo_root=repo,
                process_inventory=lambda: {
                    "counts": {"ck3.exe": 0, "xar_ck3_bridge_injector.exe": 0},
                    "all_zero": True,
                },
                open_audit=self._open_audit,
                evaluator_verify=lambda _exe, _contract: [],
            )
            self.assertTrue(report["ok"])
            self.assertEqual(report["status"], "ready-to-run")
            self.assertFalse(report["ck3_started"])
            self.assertFalse(report["process_attached"])
            self.assertFalse(report["profile_prepared"])
            self.assertTrue(report_path.is_file())

    def test_preflight_blocks_occupied_ck3_slot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, repo = self._fixture(root)
            report = PREFLIGHT.run_preflight(
                root / "manifest.json",
                root / "preflight.json",
                repo_root=repo,
                process_inventory=lambda: {
                    "counts": {"ck3.exe": 1, "xar_ck3_bridge_injector.exe": 0},
                    "all_zero": False,
                },
                open_audit=self._open_audit,
                evaluator_verify=lambda _exe, _contract: [],
            )
            self.assertFalse(report["ok"])
            self.assertFalse(report["checks"]["exclusive_process_slot_empty"])
            self.assertFalse(report["ck3_started"])

    def test_preflight_blocks_hash_or_build_option_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest, repo = self._fixture(root)
            Path(manifest["paths"]["bridge_dll"]).write_bytes(b"changed")
            Path(manifest["paths"]["private_cmake_cache"]).write_text(
                "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1:BOOL=OFF\n",
                encoding="utf-8",
            )
            report = PREFLIGHT.run_preflight(
                root / "manifest.json",
                root / "preflight.json",
                repo_root=repo,
                process_inventory=lambda: {"counts": {}, "all_zero": True},
                open_audit=self._open_audit,
                evaluator_verify=lambda _exe, _contract: [],
            )
            self.assertFalse(report["ok"])
            self.assertFalse(report["checks"]["all_input_hashes"])
            self.assertFalse(report["checks"]["private_option_on"])

    def test_preflight_report_cannot_be_inside_future_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest, repo = self._fixture(root)
            attempt = Path(manifest["paths"]["fresh_attempt"])
            with self.assertRaisesRegex(ValueError, "outside the future attempt"):
                PREFLIGHT.run_preflight(
                    root / "manifest.json",
                    attempt / "preflight.json",
                    repo_root=repo,
                    process_inventory=lambda: {"counts": {}, "all_zero": True},
                    open_audit=self._open_audit,
                    evaluator_verify=lambda _exe, _contract: [],
                )

    def test_preflight_source_has_no_launch_or_profile_import(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "NativeHeadlessGameplayDriver",
            "native_session(",
            "prepare_profile(",
            "CreateProcess",
            "Start-Process",
            "Popen(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
