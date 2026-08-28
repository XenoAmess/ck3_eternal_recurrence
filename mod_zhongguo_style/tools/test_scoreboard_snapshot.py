#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contract for the immutable 80-slot scoreboard projection."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

from gen_scoreboard_snapshot import MOD_ROOT, SLOT_COUNT, outputs


class ScoreboardSnapshotTests(unittest.TestCase):
    def test_exact_slots_and_no_live_score_reads(self) -> None:
        rendered = outputs()
        effects = rendered[
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_generated_scoreboard_snapshots.txt"
        ].decode("utf-8-sig")
        gui = rendered[MOD_ROOT / "gui" / "zg361_scoreboard.gui"].decode("utf-8-sig")
        for prefix in ("m", "r"):
            for slot in range(1, SLOT_COUNT + 1):
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_char", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_kpi", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_grade", effects)
                self.assertIn(f"zg361_sb_{prefix}_{slot:02d}_char", gui)
        self.assertNotIn("GetList('zg361_scoreboard_managed')", gui)
        self.assertNotIn("Character.MakeScope.Var('zg361_kpi')", gui)
        self.assertNotIn("Character.MakeScope.Var('zg361_rank')", gui)

    def test_checked_in_projection_is_current(self) -> None:
        stale = [
            path.relative_to(MOD_ROOT).as_posix()
            for path, expected in outputs().items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])


if __name__ == "__main__":
    sys.exit(unittest.main())
