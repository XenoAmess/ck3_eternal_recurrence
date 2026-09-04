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


if __name__ == "__main__":
    unittest.main()
