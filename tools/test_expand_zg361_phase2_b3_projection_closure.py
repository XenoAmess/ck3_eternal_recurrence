"""Tests for deterministic B3 projection closure expansion."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import expand_zg361_phase2_b3_projection_closure as expand


BOM = b"\xef\xbb\xbf"


def write(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(BOM + body.encode("utf-8"))


class ProjectionClosureExpansionTests(unittest.TestCase):
    def test_terminal_event_copies_generated_localization_fanout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            write(
                candidate,
                "events/zg361_feedback_promotion_pip_runtime_events.txt",
                "namespace = zg361pp\n\n"
                "zg361pp.9004 = {\n"
                "    title = zg361pp.9004.t\n"
                "    desc = zg361pp.9004.desc\n"
                "    option = { name = zg361pp.9004.a }\n"
                "}\n",
            )
            english = {
                "zg361pp.9004.t": "361 Case Closed",
                "zg361pp.9004.desc": "The ledger is closed.",
                "zg361pp.9004.a": "File it.",
            }
            chinese = {
                "zg361pp.9004.t": "三六一案卷已结",
                "zg361pp.9004.desc": "账本已经收口。",
                "zg361pp.9004.a": "归档。",
            }
            for language in expand.LOCALIZATION_LANGUAGES:
                values = chinese if language == "simp_chinese" else english
                body = f"l_{language}:\n" + "".join(
                    f' {key}:0 "{value}"\n' for key, value in values.items()
                )
                write(
                    canonical,
                    expand._promotion_localization_relative(language),
                    body,
                )

            result = expand.synchronize_b3_terminal_localization(
                candidate, canonical
            )

            self.assertTrue(result["green"])
            self.assertTrue(result["applicable"])
            self.assertEqual(9, len(result["updated_files"]))
            self.assertEqual({}, result["final_missing_by_language"])
            self.assertTrue(result["placeholder_values_match_english"])
            for language in expand.LOCALIZATION_LANGUAGES:
                target = candidate / expand._promotion_localization_relative(language)
                self.assertTrue(target.read_bytes().startswith(BOM))
                values = expand._localization_values(target)
                self.assertEqual(
                    chinese if language == "simp_chinese" else english,
                    values,
                )

    def test_parameterized_event_and_recursive_effect_are_added(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            canonical = root / "canonical"
            candidate.mkdir()
            canonical.mkdir()
            root_effect = (
                "zg361_p2c_stage_10_manager_governance_effect = {\n"
                "    zg361_probe_schedule_effect = { EVENT = zg361probe.7 }\n"
                "}\n\n"
                "zg361_probe_schedule_effect = {\n"
                "    trigger_event = { id = $EVENT$ days = 1 }\n"
                "}\n"
            )
            root_file = (
                "common/scripted_effects/"
                "zg361_phase2_central_003_dispatch_control_effects.txt"
            )
            write(candidate, root_file, root_effect)
            write(canonical, root_file, root_effect)
            write(
                canonical,
                "events/zg361_phase2_central_001_serial_dispatch_events.txt",
                "namespace = zg361probe\n\n"
                "zg361probe.7 = {\n"
                "    immediate = {\n"
                "        zg361_probe_leaf_effect = yes\n"
                "        if = { limit = { zg361_probe_root_trigger = yes } }\n"
                "    }\n"
                "}\n",
            )
            write(
                canonical,
                "common/scripted_effects/leaf_effects.txt",
                "zg361_probe_leaf_effect = {\n"
                "    set_variable = { name = probe value = 1 }\n"
                "}\n",
            )
            write(
                canonical,
                "common/scripted_triggers/probe_triggers.txt",
                "zg361_probe_root_trigger = {\n"
                "    zg361_probe_leaf_trigger = yes\n"
                "}\n\n"
                "zg361_probe_leaf_trigger = {\n"
                "    always = yes\n"
                "}\n",
            )
            evidence_path = root / "evidence.json"
            result = expand.expand_projection_closure(
                candidate, canonical, evidence_path
            )
            self.assertTrue(result["green"])
            self.assertEqual(["zg361probe.7"], result["initial_missing_events"])
            self.assertEqual(3, result["added_file_count"])
            self.assertEqual(2, len(result["rounds"]))
            self.assertTrue(
                (
                    candidate
                    / "events/zg361_phase2_central_001_serial_dispatch_events.txt"
                ).is_file()
            )
            self.assertTrue(
                (candidate / "common/scripted_effects/leaf_effects.txt").is_file()
            )
            self.assertTrue(
                (candidate / "common/scripted_triggers/probe_triggers.txt").is_file()
            )
            persisted = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual([], persisted["final_missing_events"])
            self.assertEqual([], persisted["final_missing_effects"])
            self.assertEqual([], persisted["final_missing_triggers"])
            self.assertFalse(persisted["localization_closure"]["applicable"])


if __name__ == "__main__":
    unittest.main()
