#!/usr/bin/env python3
"""Tests for the one-off B3 trigger-body diagnostic materializer."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import materialize_zg361_b3_trigger_body_diagnostic as diagnostic


def _block(name: str, parameters: tuple[str, ...]) -> str:
    checks = "\n".join(f"    always = ${parameter}$" for parameter in parameters)
    return f"{name} = {{\n{checks}\n}}\n"


def _call(name: str, parameters: tuple[str, ...]) -> str:
    values = "\n".join(f"            {parameter} = root" for parameter in parameters)
    return f"        {name} = {{\n{values}\n        }}"


class TriggerDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        trigger = self.source / diagnostic.TARGET_RELATIVE
        trigger.parent.mkdir(parents=True)
        payload = "# generated fixture\n\n" + "\n".join(
            _block(name, diagnostic.EXPECTED_ABI[name])
            for name in diagnostic.TARGETS
        )
        trigger.write_bytes(diagnostic.BOM + payload.encode("utf-8"))
        effect = self.source / "common/scripted_effects/caller.txt"
        effect.parent.mkdir(parents=True)
        caller = (
            "fixture_effect = {\n"
            + "\n".join(
                _call(name, diagnostic.EXPECTED_ABI[name])
                for name in diagnostic.TARGETS
            )
            + "\n}\n"
        )
        effect.write_bytes(diagnostic.BOM + caller.encode("utf-8"))
        (self.source / "descriptor.mod").write_text('name="fixture"\n', encoding="utf-8")
        (self.source / "thumbnail.png").write_bytes(b"png-fixture")
        self.dependencies = self.root / "dependencies"
        self.dependencies.mkdir()
        for name in ("python.exe", "runner.py", "bridge.dll", "injector.exe", "seed.json"):
            (self.dependencies / name).write_bytes(b"fixture")

    @staticmethod
    def _parser_runner(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "result": "GREEN",
            "jar_sha256": "1" * 64,
            "exit_code": 1,
            "checks": {
                "parser_green": True,
                "root_parser_green": True,
                "offline_provenance": True,
            },
        }

    @staticmethod
    def _closure(_root: Path) -> dict[str, object]:
        return {
            "green": True,
            "missing_effects": [],
            "missing_events": [],
            "missing_triggers": [],
            "reachable_effect_count": 1,
            "reachable_event_count": 0,
            "reachable_trigger_count": 2,
        }

    def _materialize(self) -> dict[str, object]:
        return diagnostic.materialize_candidate(
            source_root=self.source,
            output_root=self.root / "candidate",
            manifest_path=self.root / "diagnostic.json",
            projection_manifest=self.root / "projection.json",
            parser_report_path=self.root / "parser.json",
            projection_name="fixture-trigger-false",
            artifacts_dir=self.root / "artifacts-live",
            open_kaishek_jar=self.root / "unused.jar",
            profile="fixture-profile",
            fixture="fixture-id",
            runner_python=self.dependencies / "python.exe",
            runner=self.dependencies / "runner.py",
            bridge_dll=self.dependencies / "bridge.dll",
            bridge_injector=self.dependencies / "injector.exe",
            seed_contract=self.dependencies / "seed.json",
            bridge_pipe=r"\\.\pipe\xar_ck3_bridge_zg361_0123456789abcdef0123456789abcdef",
            expected_source=None,
            expected_calls={name: 1 for name in diagnostic.TARGETS},
            parser_runner=self._parser_runner,
            closure_builder=self._closure,
        )

    def test_materialization_changes_only_the_trigger_owner(self) -> None:
        source_before = diagnostic._tree_rows(self.source)
        receipt = self._materialize()
        self.assertEqual("GREEN", receipt["result"])
        self.assertEqual(1, receipt["file_diff"]["changed_count"])
        self.assertEqual(0, receipt["file_diff"]["added_count"])
        self.assertEqual(0, receipt["file_diff"]["removed_count"])
        self.assertEqual(source_before, diagnostic._tree_rows(self.source))
        self.assertTrue(all(receipt["checks"].values()))
        self.assertFalse(receipt["ck3_started"])
        self.assertFalse(receipt["launch"]["executed"])
        self.assertEqual(
            diagnostic._sha256(self.dependencies / "runner.py"),
            receipt["launch"]["runner"]["sha256"],
        )
        self.assertEqual(
            str((self.dependencies / "runner.py").resolve()),
            receipt["launch"]["runner"]["path"],
        )

    def test_candidate_keeps_names_calls_bom_and_abi_consuming_false_bodies(self) -> None:
        receipt = self._materialize()
        target = self.root / "candidate" / diagnostic.TARGET_RELATIVE
        self.assertTrue(target.read_bytes().startswith(diagnostic.BOM))
        entries = diagnostic.top_level_effect_entries(target.read_bytes())
        self.assertEqual(diagnostic.TARGETS, tuple(entry.name for entry in entries))
        self.assertTrue(all("always = no" in entry.block for entry in entries))
        for entry in entries:
            self.assertEqual(
                diagnostic.EXPECTED_ABI[entry.name],
                tuple(sorted(set(diagnostic.PARAM_TOKEN_RE.findall(entry.block)))),
            )
        self.assertIn(
            "zg361_p2c_m360_candidate_ready_trigger = {",
            entries[1].block,
        )
        self.assertTrue(receipt["checks"]["caller_surface_byte_identical"])
        self.assertTrue(receipt["checks"]["caller_parameter_abi_preserved"])
        self.assertTrue(
            receipt["checks"]["provider_parameter_inference_abi_preserved"]
        )

    def test_manifest_and_projection_are_external_and_hash_bound(self) -> None:
        receipt = self._materialize()
        manifest = json.loads((self.root / "diagnostic.json").read_text(encoding="utf-8"))
        projection = json.loads((self.root / "projection.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["candidate"]["tree_sha256"], projection["source_tree_sha256"])
        self.assertEqual("fixture-trigger-false", projection["projection"])
        self.assertEqual(4, len(projection["files"]))
        self.assertFalse((self.root / "artifacts-live").exists())
        self.assertTrue(manifest["diagnostic_only"])
        self.assertFalse(manifest["production_ready"])

    def test_wrong_caller_abi_fails_before_copy(self) -> None:
        caller = self.source / "common/scripted_effects/caller.txt"
        caller.write_bytes(
            diagnostic.BOM
            + (
                "fixture_effect = {\n"
                "    zg361_p2c_m360_candidate_ready_trigger = { WRONG = root }\n"
                "}\n"
            ).encode("utf-8")
        )
        with self.assertRaises(diagnostic.TriggerDiagnosticError):
            self._materialize()
        self.assertFalse((self.root / "candidate").exists())

    def test_source_identity_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(diagnostic.TriggerDiagnosticError, "frozen r5 A identity"):
            diagnostic.materialize_candidate(
                source_root=self.source,
                output_root=self.root / "candidate",
                manifest_path=self.root / "diagnostic.json",
                projection_manifest=self.root / "projection.json",
                parser_report_path=self.root / "parser.json",
                projection_name="fixture-trigger-false",
                artifacts_dir=self.root / "artifacts-live",
                open_kaishek_jar=self.root / "unused.jar",
                profile="fixture-profile",
                fixture="fixture-id",
                runner_python=self.dependencies / "python.exe",
                runner=self.dependencies / "runner.py",
                bridge_dll=self.dependencies / "bridge.dll",
                bridge_injector=self.dependencies / "injector.exe",
                seed_contract=self.dependencies / "seed.json",
                bridge_pipe=r"\\.\pipe\xar_ck3_bridge_zg361_0123456789abcdef0123456789abcdef",
                expected_source={"file_count": 999},
                expected_calls={name: 1 for name in diagnostic.TARGETS},
                parser_runner=self._parser_runner,
                closure_builder=self._closure,
            )

    def test_runner_identity_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            diagnostic.TriggerDiagnosticError,
            "runner does not match the A2 git-head runner content",
        ):
            diagnostic.materialize_candidate(
                source_root=self.source,
                output_root=self.root / "candidate",
                manifest_path=self.root / "diagnostic.json",
                projection_manifest=self.root / "projection.json",
                parser_report_path=self.root / "parser.json",
                projection_name="fixture-trigger-false",
                artifacts_dir=self.root / "artifacts-live",
                open_kaishek_jar=self.root / "unused.jar",
                profile="fixture-profile",
                fixture="fixture-id",
                runner_python=self.dependencies / "python.exe",
                runner=self.dependencies / "runner.py",
                bridge_dll=self.dependencies / "bridge.dll",
                bridge_injector=self.dependencies / "injector.exe",
                seed_contract=self.dependencies / "seed.json",
                bridge_pipe=r"\\.\pipe\xar_ck3_bridge_zg361_0123456789abcdef0123456789abcdef",
                expected_runner_sha256="0" * 64,
                expected_source=None,
                expected_calls={name: 1 for name in diagnostic.TARGETS},
                parser_runner=self._parser_runner,
                closure_builder=self._closure,
            )

    def test_invalid_bridge_pipe_fails_before_launch_contract(self) -> None:
        with self.assertRaisesRegex(
            diagnostic.TriggerDiagnosticError,
            "bridge pipe must match the formal runner contract",
        ):
            diagnostic.materialize_candidate(
                source_root=self.source,
                output_root=self.root / "candidate",
                manifest_path=self.root / "diagnostic.json",
                projection_manifest=self.root / "projection.json",
                parser_report_path=self.root / "parser.json",
                projection_name="fixture-trigger-false",
                artifacts_dir=self.root / "artifacts-live",
                open_kaishek_jar=self.root / "unused.jar",
                profile="fixture-profile",
                fixture="fixture-id",
                runner_python=self.dependencies / "python.exe",
                runner=self.dependencies / "runner.py",
                bridge_dll=self.dependencies / "bridge.dll",
                bridge_injector=self.dependencies / "injector.exe",
                seed_contract=self.dependencies / "seed.json",
                bridge_pipe=r"\\.\pipe\xar_ck3_bridge_zg361_not_hex",
                expected_source=None,
                expected_calls={name: 1 for name in diagnostic.TARGETS},
                parser_runner=self._parser_runner,
                closure_builder=self._closure,
            )

    def test_prior_zero_argument_provider_error_is_bound_as_material_red(self) -> None:
        game_log = self.root / "final_game.log"
        game_log.write_text(
            "\n".join(
                f"Error: {name} trigger [ {diagnostic.CK3_ARGUMENT_ERROR} ]"
                for name in diagnostic.TARGETS
                for _ in range(3)
            ),
            encoding="utf-8",
        )
        with mock.patch.object(
            diagnostic,
            "EXPECTED_PRIOR_ABI_RED_GAME_LOG_SHA256",
            diagnostic._sha256(game_log),
        ):
            row = diagnostic._bind_prior_material_abi_red(game_log)
        self.assertEqual(6, row["total_count"])
        self.assertEqual(
            "material_provider_parameter_inference_red",
            row["classification"],
        )


if __name__ == "__main__":
    unittest.main()
