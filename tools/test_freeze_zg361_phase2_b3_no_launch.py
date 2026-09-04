#!/usr/bin/env python3
"""Regression tests for the B3 no-launch projection freezer."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import freeze_zg361_phase2_b3_no_launch as freeze


BOM = b"\xef\xbb\xbf"


def write_effects(root: Path, name: str, body: str) -> None:
    directory = root / "common" / "scripted_effects"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(BOM + body.encode("utf-8"))


def write_events(root: Path, name: str, body: str) -> None:
    directory = root / "events"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(BOM + body.encode("utf-8"))


def write_triggers(root: Path, name: str, body: str) -> None:
    directory = root / "common" / "scripted_triggers"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(BOM + body.encode("utf-8"))


class CentralEffectCallClosureTests(unittest.TestCase):
    def test_recursive_custom_effect_calls_are_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    zg361_probe_helper_effect = yes\n"
                "}\n",
            )
            write_effects(
                root,
                "dispatch_effects.txt",
                "zg361_probe_helper_effect = {\n"
                "    zg361_probe_leaf_effect = yes\n"
                "}\n\n"
                "zg361_probe_leaf_effect = {\n"
                "    set_variable = { name = probe value = 1 }\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset({"dispatch_effects.txt"}),
                required_event_provider_files=frozenset(),
            )
            self.assertTrue(result["green"])
            self.assertEqual(3, result["reachable_effect_count"])
            self.assertEqual([], result["missing_effects"])

    def test_recursive_missing_callee_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    zg361_probe_helper_effect = yes\n"
                "}\n",
            )
            write_effects(
                root,
                "dispatch_effects.txt",
                "zg361_probe_helper_effect = {\n"
                "    zg361_probe_missing_effect = yes\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset({"dispatch_effects.txt"}),
                required_event_provider_files=frozenset(),
            )
            self.assertFalse(result["green"])
            self.assertEqual(
                ["zg361_probe_missing_effect"], result["missing_effects"]
            )

    def test_effect_event_effect_and_event_closure_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    trigger_event = { id = zg361probe.1 days = 1 }\n"
                "}\n",
            )
            write_effects(
                root,
                "leaf_effects.txt",
                "zg361_probe_leaf_effect = {\n"
                "    set_variable = { name = probe value = 1 }\n"
                "}\n",
            )
            write_events(
                root,
                "probe_events.txt",
                "namespace = zg361probe\n\n"
                "zg361probe.1 = {\n"
                "    immediate = {\n"
                "        zg361_probe_leaf_effect = yes\n"
                "        trigger_event = zg361probe.2\n"
                "    }\n"
                "}\n\n"
                "zg361probe.2 = { hidden = yes }\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset({"leaf_effects.txt"}),
                required_event_provider_files=frozenset({"probe_events.txt"}),
            )
            self.assertTrue(result["green"])
            self.assertEqual(2, result["reachable_effect_count"])
            self.assertEqual(2, result["reachable_event_count"])
            self.assertEqual([], result["missing_effects"])
            self.assertEqual([], result["missing_events"])

    def test_recursive_missing_event_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    trigger_event = { id = zg361probe.1 days = 1 }\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset(),
                required_event_provider_files=frozenset(),
            )
            self.assertFalse(result["green"])
            self.assertEqual(["zg361probe.1"], result["missing_events"])

    def test_parameterized_event_argument_is_in_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    zg361_probe_schedule_effect = {\n"
                "        EVENT = zg361probe.7\n"
                "    }\n"
                "}\n\n"
                "zg361_probe_schedule_effect = {\n"
                "    trigger_event = { id = $EVENT$ days = 1 }\n"
                "}\n",
            )
            write_events(
                root,
                "probe_events.txt",
                "namespace = zg361probe\n\n"
                "zg361probe.7 = { hidden = yes }\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset(),
                required_event_provider_files=frozenset({"probe_events.txt"}),
            )
            self.assertTrue(result["green"])
            self.assertEqual(["zg361probe.7"], result["reachable_events"])

    def test_material_projection_rejects_missing_parameterized_event(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    zg361_probe_schedule_effect = {\n"
                "        EVENT = zg361probe.9\n"
                "    }\n"
                "}\n\n"
                "zg361_probe_schedule_effect = {\n"
                "    trigger_event = { id = $EVENT$ days = 1 }\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset(),
                required_event_provider_files=frozenset(),
            )
            self.assertEqual(["zg361probe.9"], result["missing_events"])
            self.assertEqual(
                ["zg361probe.9"],
                result["material_projection"]["missing_events"],
            )
            self.assertFalse(result["green"])

    def test_material_projection_rejects_missing_event_from_sibling_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    trigger_event = { id = zg361probe.1 days = 1 }\n"
                "}\n\n"
                "zg361_probe_sibling_effect = {\n"
                "    trigger_event = { id = zg361probe.2 days = 1 }\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset(),
                required_event_provider_files=frozenset(),
            )
            self.assertEqual(["zg361probe.1"], result["missing_events"])
            self.assertEqual(
                ["zg361probe.1", "zg361probe.2"],
                result["material_projection"]["missing_events"],
            )
            self.assertFalse(result["material_projection"]["green"])

    def test_recursive_and_parameterized_custom_triggers_are_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    if = {\n"
                "        limit = {\n"
                "            zg361_probe_root_trigger = {\n"
                "                CHILD_TRIGGER = zg361_probe_leaf_trigger\n"
                "            }\n"
                "        }\n"
                "    }\n"
                "}\n",
            )
            write_triggers(
                root,
                "probe_triggers.txt",
                "zg361_probe_root_trigger = {\n"
                "    zg361_probe_middle_trigger = yes\n"
                "}\n\n"
                "zg361_probe_middle_trigger = {\n"
                "    zg361_probe_leaf_trigger = yes\n"
                "}\n\n"
                "zg361_probe_leaf_trigger = {\n"
                "    always = yes\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset(),
                required_event_provider_files=frozenset(),
            )
            self.assertTrue(result["green"])
            self.assertEqual(3, result["reachable_trigger_count"])
            self.assertEqual([], result["missing_triggers"])
            self.assertEqual([], result["material_projection"]["missing_triggers"])

    def test_material_projection_rejects_missing_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_effects(
                root,
                "root_effects.txt",
                "zg361_probe_root_effect = {\n"
                "    if = { limit = { zg361_probe_missing_trigger = yes } }\n"
                "}\n",
            )
            result = freeze.central_effect_call_closure(
                root,
                roots=("zg361_probe_root_effect",),
                required_effect_provider_files=frozenset(),
                required_event_provider_files=frozenset(),
            )
            self.assertEqual(
                ["zg361_probe_missing_trigger"], result["missing_triggers"]
            )
            self.assertEqual(
                ["zg361_probe_missing_trigger"],
                result["material_projection"]["missing_triggers"],
            )
            self.assertFalse(result["green"])

    def test_predecessor_material_red_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cell").mkdir()
            (root / "report.json").write_text(
                json.dumps({"result": "RED"}), encoding="utf-8"
            )
            (root / "cell" / "report.json").write_text(
                json.dumps(
                    {
                        "result": "RED",
                        "native_cleanup": {
                            "result": "GREEN",
                            "failed_checks": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            caller = freeze.PREDECESSOR_CALLER_FILE
            (root / "cell" / "final_error.log").write_text(
                "Unknown effect: zg361_p2c_record_stage_effect " + caller + "\n"
                "Unknown effect: zg361_p2c_record_red_effect " + caller + "\n",
                encoding="utf-8",
            )
            (root / "evidence-index.json").write_text("{}\n", encoding="utf-8")
            result = freeze.predecessor_live_red_evidence(root)
            self.assertEqual("material-projection-closure-red", result["classification"])
            self.assertFalse(result["loader_performance_claimed"])
            self.assertEqual(2, result["unknown_effect_line_count"])
            self.assertTrue(result["cleanup_green"])

    def test_predecessor_event_material_red_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cell").mkdir()
            (root / "report.json").write_text(
                json.dumps({"result": "RED"}), encoding="utf-8"
            )
            (root / "cell" / "report.json").write_text(
                json.dumps(
                    {
                        "result": "RED",
                        "native_cleanup": {
                            "result": "GREEN",
                            "failed_checks": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            caller = freeze.EVENT_PREDECESSOR_CALLER_FILE
            (root / "cell" / "final_error.log").write_text(
                "Error: trigger_event effect [ Event [zg361p2c.2] not found ]\n"
                f"Script location: file: {caller} line: 31\n"
                "Error: trigger_event effect [ Event [zg361p2c.1] not found ]\n"
                f"Script location: file: {caller} line: 21\n",
                encoding="utf-8",
            )
            (root / "evidence-index.json").write_text("{}\n", encoding="utf-8")
            result = freeze.predecessor_event_live_red_evidence(root)
            self.assertEqual(
                "material-projection-event-closure-red", result["classification"]
            )
            self.assertFalse(result["loader_performance_claimed"])
            self.assertFalse(result["size_ab_triggered"])
            self.assertEqual(2, result["missing_event_line_count"])
            self.assertTrue(result["cleanup_green"])

    def test_predecessor_parameterized_event_red_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cell").mkdir()
            (root / "report.json").write_text(
                json.dumps({"result": "RED"}), encoding="utf-8"
            )
            (root / "cell" / "report.json").write_text(
                json.dumps(
                    {
                        "result": "RED",
                        "error_reason": (
                            "CK3 reached frontend but did not enter "
                            "Load Save/In Game"
                        ),
                        "duration_seconds": 312.77,
                        "loader_gate_executed": False,
                        "gameplay_acceptance_executed": False,
                        "native_cleanup": {
                            "result": "GREEN",
                            "failed_checks": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            lines = []
            for event in sorted(
                freeze.EXPECTED_PARAMETERIZED_EVENT_PREDECESSOR_MISSING_EVENTS
            ):
                lines.append(f"Event [{event}] not found")
            lines.append(freeze.PARAMETERIZED_EVENT_PREDECESSOR_CALLER_FILE)
            log_text = "\n".join(lines) + "\n"
            (root / "cell" / "final_error.log").write_text(
                log_text, encoding="utf-8"
            )
            (root / "cell" / "final_game.log").write_text(
                log_text, encoding="utf-8"
            )
            (root / "evidence-index.json").write_text("{}\n", encoding="utf-8")
            result = freeze.predecessor_parameterized_event_live_red_evidence(
                root
            )
            self.assertEqual(
                "material-projection-parameterized-event-closure-red",
                result["classification"],
            )
            self.assertEqual(14, result["missing_event_line_count"])
            self.assertFalse(result["loader_performance_claimed"])
            self.assertFalse(result["size_ab_triggered"])
            self.assertTrue(result["cleanup_green"])

    def test_predecessor_trigger_red_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cell").mkdir()
            (root / "report.json").write_text(
                json.dumps({"result": "RED"}), encoding="utf-8"
            )
            (root / "cell" / "report.json").write_text(
                json.dumps(
                    {
                        "result": "RED",
                        "error_reason": (
                            "CK3 reached frontend but did not enter "
                            "Load Save/In Game"
                        ),
                        "duration_seconds": 317.408,
                        "loader_gate_executed": False,
                        "gameplay_acceptance_executed": False,
                        "native_cleanup": {
                            "result": "GREEN",
                            "failed_checks": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            lines = []
            for trigger, count in freeze.EXPECTED_TRIGGER_PREDECESSOR_COUNTS.items():
                lines.extend([f"Unknown trigger: {trigger}"] * count)
            lines.append(freeze.TRIGGER_PREDECESSOR_CALLER_FILE)
            (root / "cell" / "final_error.log").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
            (root / "cell" / "final_game.log").write_text("", encoding="utf-8")
            (root / "evidence-index.json").write_text("{}\n", encoding="utf-8")
            result = freeze.predecessor_trigger_live_red_evidence(root)
            self.assertEqual(
                "material-projection-trigger-closure-red",
                result["classification"],
            )
            self.assertEqual(6, result["unknown_trigger_line_count"])
            self.assertFalse(result["loader_performance_claimed"])
            self.assertFalse(result["size_ab_triggered"])
            self.assertTrue(result["cleanup_green"])

    def test_closure_expansion_evidence_is_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "closure-expansion.json").write_text(
                json.dumps(
                    {
                        "kind": (
                            "zg361_phase2_b3_material_custom_call_"
                            "closure_expansion"
                        ),
                        "green": True,
                        "rounds": [{"round": 1}],
                        "added_file_count": 1,
                        "added_files": ["events/probe.txt"],
                        "final_effect_definition_count": 2,
                        "final_event_definition_count": 1,
                        "final_trigger_definition_count": 1,
                        "final_missing_effects": [],
                        "final_missing_events": [],
                        "final_missing_triggers": [],
                        "localization_closure": {
                            "green": True,
                            "applicable": True,
                            "updated_files": [
                                "localization/english/probe_l_english.yml"
                            ],
                            "final_missing_by_language": {},
                            "placeholder_values_match_english": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "canonical-release.manifest.json").write_text(
                "{}\n", encoding="utf-8"
            )
            result = freeze.closure_expansion_evidence(root)
            self.assertTrue(result["green"])
            self.assertEqual(1, result["round_count"])
            self.assertEqual(1, result["added_file_count"])
            self.assertEqual(64, len(result["expansion"]["sha256"]))


if __name__ == "__main__":
    unittest.main()
