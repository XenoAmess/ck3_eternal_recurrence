#!/usr/bin/env python3
"""Contract tests for the exact 30-minute Project Causality argument structure."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STRUCTURE_PATH = (
    REPOSITORY_ROOT / "promo" / "project_causality" / "30m" / "structure.json"
)
INTERLUDES_PATH = STRUCTURE_PATH.with_name("chapter-interludes.md")
GATES_PATH = STRUCTURE_PATH.with_name("chapter-gates.json")


class ProjectCausalityThirtyMinuteStructureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.structure = json.loads(STRUCTURE_PATH.read_text(encoding="utf-8"))
        self.segments = self.structure["segments"]
        self.gate_contract = json.loads(GATES_PATH.read_text(encoding="utf-8"))

    def test_timeline_is_contiguous_and_exactly_thirty_minutes(self) -> None:
        self.assertEqual(1800, self.structure["duration_seconds"])
        self.assertEqual(54000, self.structure["frames_at_30_fps"])
        self.assertEqual(31, len(self.segments))
        self.assertEqual(0, self.segments[0]["start"])
        self.assertEqual(1800, self.segments[-1]["end"])
        for current, following in zip(self.segments, self.segments[1:]):
            self.assertEqual(current["end"], following["start"])
            self.assertGreater(current["end"], current["start"])

    def test_four_chapter_gates_are_explicit_twenty_second_segments(self) -> None:
        expected = {
            "03-spell-declaration": (190, 210),
            "10-method-declaration": (820, 840),
            "17-principle-declaration": (1270, 1290),
            "22-vision-declaration": (1510, 1530),
        }
        gates = {row["id"]: row for row in self.segments if row["chapter"] == "章门"}
        self.assertEqual(set(expected), set(gates))
        for gate_id, (start, end) in expected.items():
            self.assertEqual(start, gates[gate_id]["start"])
            self.assertEqual(end, gates[gate_id]["end"])
            self.assertEqual(20, end - start)

    def test_each_gate_has_a_distinct_theme_declaration(self) -> None:
        text = INTERLUDES_PATH.read_text(encoding="utf-8")
        declarations = [row["declaration_zh"] for row in self.gate_contract["gates"]]
        self.assertEqual(4, len(set(declarations)))
        for declaration in declarations:
            self.assertIn(declaration, text)

    def test_gate_contract_matches_timeline_and_has_distinct_identities(self) -> None:
        timeline_gates = {
            row["id"]: row for row in self.segments if row["chapter"] == "章门"
        }
        contract_gates = {row["id"]: row for row in self.gate_contract["gates"]}
        self.assertEqual(set(timeline_gates), set(contract_gates))
        self.assertEqual(20, self.gate_contract["duration_seconds_each"])
        self.assertGreaterEqual(self.gate_contract["near_silence_min_seconds"], 0.8)
        self.assertLessEqual(self.gate_contract["maximum_text_layers"], 2)

        palettes = set()
        audio_signatures = set()
        visual_assets = set()
        expected_beats = [(0, 3), (3, 7), (7, 12), (12, 18), (18, 20)]
        for gate_id, gate in contract_gates.items():
            timeline_gate = timeline_gates[gate_id]
            self.assertEqual(timeline_gate["start"], gate["start"])
            self.assertEqual(timeline_gate["end"], gate["end"])
            self.assertEqual(timeline_gate["argument"], gate["declaration_zh"])
            self.assertEqual(20, gate["end"] - gate["start"])
            self.assertEqual(
                expected_beats,
                [(beat["start"], beat["end"]) for beat in gate["beats"]],
            )

            asset_path = GATES_PATH.parent / gate["visual_asset"]
            self.assertTrue(asset_path.is_file(), asset_path)
            sound_effect_path = GATES_PATH.parent / gate["sound_effect_asset"]
            self.assertTrue(sound_effect_path.is_file(), sound_effect_path)
            palettes.add(gate["palette"])
            audio_signatures.add(gate["audio_signature"])
            visual_assets.add(asset_path.resolve())

        self.assertEqual(4, len(palettes))
        self.assertEqual(4, len(audio_signatures))
        self.assertEqual(4, len(visual_assets))


if __name__ == "__main__":
    unittest.main()
