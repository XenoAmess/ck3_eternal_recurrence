"""Focused checks for the current-pin G2 cleanup/expiry preflight."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "prepare_g2_postwar_cleanup_expiry_current_pin_capture.py"
)
MANIFEST = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "g2_postwar_cleanup_expiry_current_pin_live_manifest.json"
)
SPEC = importlib.util.spec_from_file_location(
    "prepare_g2_postwar_cleanup_expiry_current_pin_capture", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load preflight: {SCRIPT}")
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class G2PostwarCleanupExpiryCurrentPinPreflightTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, str, str]:
        repo = root / "repo"
        repo.mkdir()
        source = repo / "source.txt"
        source.write_text("source", encoding="utf-8")
        files: dict[str, Path] = {}
        for name in (
            "python",
            "preflight",
            "runner",
            "base_runner",
            "adapter",
            "retention_manifest",
            "cleanup_source_contract",
            "expiry_source_contract",
            "source_checkpoint",
            "source_driver_state",
            "game_executable",
            "bridge_dll",
            "bridge_injector",
            "cmake_cache",
            "native_ctest",
            "source_zip",
            "product_manifest",
            "product_zip",
        ):
            files[name] = root / f"{name}.bin"
            files[name].write_bytes(name.encode("ascii"))
        files["cmake_cache"].write_text(
            "\n".join(
                [
                    *(f"{key}:BOOL={value}" for key, value in PREFLIGHT.SELECTED_OPTIONS.items()),
                    *(f"{key}:BOOL=OFF" for key in PREFLIGHT.OFF_OPTIONS),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        files["native_ctest"].write_text(
            "94/94 Test #94: fixture Passed\n"
            "100% tests passed, 0 tests failed out of 94\n",
            encoding="utf-8",
        )
        files["cleanup_source_contract"].write_text(
            json.dumps(
                {
                    "default_enabled": False,
                    "exact_native_store_contract": {
                        "cleanup": (
                            "WarID absence is admission only and never the "
                            "destroyed result"
                        )
                    },
                }
            ),
            encoding="utf-8",
        )
        files["expiry_source_contract"].write_text(
            json.dumps({"default_enabled": False}), encoding="utf-8"
        )
        files["retention_manifest"].write_text("{}", encoding="utf-8")
        staging = root / "product"
        staging.mkdir()
        release_entries = []
        for index in range(86):
            path = staging / f"file-{index:02d}.txt"
            path.write_text(str(index), encoding="ascii")
            release_entries.append(
                {
                    "path": path.name,
                    "size": path.stat().st_size,
                    "sha256": _sha256(path).lower(),
                }
            )
        source_commit = "a" * 40
        files["product_manifest"].write_text(
            json.dumps(
                {
                    "format_version": 2,
                    "git_sha": source_commit,
                    "files": release_entries,
                }
            ),
            encoding="utf-8",
        )
        game_hash = _sha256(files["game_executable"])
        tree_hash, _ = PREFLIGHT._tree_digest(staging)
        manifest = {
            "schema": PREFLIGHT.EXPECTED_SCHEMA,
            "state": "static-ready-live-pending",
            "candidate_source_commit": source_commit,
            "identity": {
                "war_id": 50_331_699,
                "character_id": 29_829,
                "opponent_character_id": 36_769,
                "date_raw": 53_223_936,
            },
            "paths": {
                **{name: str(path) for name, path in files.items()},
                "product_staging": str(staging),
                "fresh_attempt": str(root / "future"),
            },
            "sha256": {name: _sha256(path) for name, path in files.items()},
            "source_sha256": {"source.txt": _sha256(source)},
            "build_contract": {
                "selected_options": copy.deepcopy(PREFLIGHT.SELECTED_OPTIONS),
                "required_off_options": list(PREFLIGHT.OFF_OPTIONS),
                "expected_ctest_count": 94,
            },
            "product_contract": {
                "production_tree_sha256": tree_hash,
                "file_count": 86,
            },
            "b7_dependency": {
                "integrated_commit": "b" * 40,
                "required_as_g2_runtime_input": False,
                "new_freeze_required": False,
            },
            "boundaries": {
                "live_executed": False,
                "public_readiness_promoted": False,
                "action_readiness_promoted": False,
                "automatic_surrender_ready": False,
                "gen034_closed": False,
            },
            "live_command": {
                "unique": True,
                "execute_during_preflight": False,
                "argv": ["python", "runner", "--authorize-private-live"],
            },
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path, repo, game_hash, tree_hash

    def test_committed_manifest_is_bounded_and_current(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        PREFLIGHT.validate_manifest_contract(manifest)
        self.assertEqual(
            manifest["candidate_source_commit"],
            "4da52808301ba16e92f5097c69ab541f4938d587",
        )
        self.assertFalse(manifest["b7_dependency"]["new_freeze_required"])
        self.assertTrue(all(value is False for value in manifest["boundaries"].values()))

    def test_preflight_green_without_launch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path, repo, game_hash, _ = self._fixture(root)
            with (
                mock.patch.object(PREFLIGHT, "EXPECTED_EXE_SHA256", game_hash),
                mock.patch.object(PREFLIGHT, "EXPECTED_TICKET_ID", "ticket"),
                mock.patch.object(
                    PREFLIGHT.retention,
                    "build_retention_ticket",
                    return_value={"retention_ticket_id": "ticket"},
                ),
            ):
                report = PREFLIGHT.run_preflight(
                    manifest_path,
                    root / "preflight.json",
                    repo_root=repo,
                    process_inventory=lambda: {
                        "counts": {"ck3.exe": 0, "xar_ck3_bridge_injector.exe": 0},
                        "all_zero": True,
                    },
                )
            self.assertTrue(report["ok"])
            self.assertEqual(report["status"], "READY_TO_SERIAL_LIVE")
            self.assertFalse(report["ck3_started"])
            self.assertFalse(report["process_attached"])
            self.assertFalse(report["profile_prepared"])

    def test_occupied_slot_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path, repo, game_hash, _ = self._fixture(root)
            with (
                mock.patch.object(PREFLIGHT, "EXPECTED_EXE_SHA256", game_hash),
                mock.patch.object(PREFLIGHT, "EXPECTED_TICKET_ID", "ticket"),
                mock.patch.object(
                    PREFLIGHT.retention,
                    "build_retention_ticket",
                    return_value={"retention_ticket_id": "ticket"},
                ),
            ):
                report = PREFLIGHT.run_preflight(
                    manifest_path,
                    root / "preflight.json",
                    repo_root=repo,
                    process_inventory=lambda: {
                        "counts": {"ck3.exe": 1},
                        "all_zero": False,
                    },
                )
            self.assertFalse(report["ok"])
            self.assertEqual(report["status"], "RED")
            self.assertFalse(report["ck3_started"])

    def test_source_has_no_runtime_or_profile_entrypoint(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "NativeHeadlessGameplayDriver",
            "native_session(",
            "prepare_profile(",
            "Start-Process",
            "Popen(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
