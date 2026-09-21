"""Focused no-launch tests for durable Council candidate projection."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from materialize_council_native_gate_scene_candidate_v1 import (
    derive_checkpoint_projection,
    materialize,
    replace_strings,
    resolve_source_state,
)


def root_context(date_raw: int = 53149872) -> dict[str, object]:
    return {
        "date_raw": date_raw,
        "player_character_id": 31853,
        "snapshot_revision": 22,
        "government": {"key": "feudal_government"},
        "council": {
            "owner_character_id": 31853,
            "positions": [{
                "position_key": "councillor_steward",
                "incumbent_character_id": 31507,
                "task_key": "task_collect_taxes",
            }],
        },
    }


def driver() -> dict[str, object]:
    return {
        "format_version": 2,
        "pipe_name": "old",
        "last_checkpoint": {
            "sha256": "A" * 64,
            "date_raw": 53149872,
            "history_index": 2,
            "episode_character_id": 31853,
        },
        "command_history": [
            {"index": 1, "command": "query-campaign-root-context-v1",
             "result": {"campaign_root_context": root_context()}},
            {"index": 2, "command": "save-checkpoint", "result": {}},
            {"index": 3, "command": "offer-white-peace-5", "result": {}},
        ],
        "managed_restore_transaction": {"status": "tail"},
        "succession_expectation": {"binding": "tail"},
    }


class MaterializeCouncilCandidateTests(unittest.TestCase):
    def test_accepts_zero_padded_source_round_before_any_output(self) -> None:
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaisesRegex(ValueError, "durable source pair/profile is absent"):
                materialize(Path("candidate"), Path("static"), Path("source-state"),
                            Path("source-pair"), Path("game"), Path("python"),
                            Path("repo"), "R0050", "a" * 40)
            with self.assertRaisesRegex(ValueError, "source round is not monotonic"):
                materialize(Path("candidate"), Path("static"), Path("source-state"),
                            Path("source-pair"), Path("game"), Path("python"),
                            Path("repo"), "R0000", "a" * 40)

    def test_projects_exactly_through_durable_checkpoint(self) -> None:
        projected, frame = derive_checkpoint_projection(
            driver(), "A" * 64, Path("C:/candidate/xar_checkpoint.ck3"),
            r"\\.\pipe\new")
        self.assertEqual(len(projected["command_history"]), 2)
        self.assertEqual(projected["command_history"][-1]["command"], "save-checkpoint")
        self.assertIsNone(projected["managed_restore_transaction"])
        self.assertIsNone(projected["succession_expectation"])
        self.assertEqual(projected["pipe_name"], r"\\.\pipe\new")
        self.assertEqual(frame["steward_incumbent_character_id"], 31507)
        self.assertFalse(frame["steward_vacant"])

    def test_rejects_vacant_replacement_scene(self) -> None:
        value = driver()
        value["command_history"][0]["result"]["campaign_root_context"]["council"][
            "positions"][0]["incumbent_character_id"] = None
        with self.assertRaisesRegex(ValueError, "vacant"):
            derive_checkpoint_projection(value, "A" * 64, Path("save.ck3"), "pipe")

    def test_rejects_noncontiguous_source_history(self) -> None:
        value = driver()
        value["command_history"][1]["index"] = 4
        with self.assertRaisesRegex(ValueError, "contiguous"):
            derive_checkpoint_projection(value, "A" * 64, Path("save.ck3"), "pipe")

    def test_relocates_nested_strings_without_mutating_nonstrings(self) -> None:
        source = {"path": "C:/old/state", "nested": ["C:/old/profile", 3]}
        self.assertEqual(replace_strings(source, (("C:/old", "D:/new"),)), {
            "path": "D:/new/state", "nested": ["D:/new/profile", 3]})

    def test_resolves_legacy_stage_or_direct_state_root(self) -> None:
        stage = Path("C:/preview")
        state = Path("D:/preview-runtime-state")
        self.assertEqual(resolve_source_state(stage, None),
                         (stage.resolve() / "state"))
        self.assertEqual(resolve_source_state(None, state), state.resolve())
        with self.assertRaisesRegex(ValueError, "exactly one"):
            resolve_source_state(None, None)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            resolve_source_state(stage, state)


if __name__ == "__main__":
    unittest.main()
