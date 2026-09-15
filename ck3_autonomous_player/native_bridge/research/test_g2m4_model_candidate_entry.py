"""Focused candidate source and model-read exit semantics without launching CK3."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from run_g2m4_player_view_live_candidate import private_read_exit_code
from seal_g2m4_player_view_live_candidate import seal


class ModelCandidateEntryTests(unittest.TestCase):
    def test_model_source_receipt_not_cache_branch_controls_success(self) -> None:
        self.assertEqual(private_read_exit_code("model_sources_observed", True,
                                                 "player-model-sources"), 0)
        self.assertEqual(private_read_exit_code("cache_branch_observed", True,
                                                 "player-model-sources"), 1)
        self.assertEqual(private_read_exit_code("model_sources_evidence_insufficient",
                                                 True, "player-model-sources"), 2)
        self.assertEqual(private_read_exit_code("red", True,
                                                 "player-model-sources"), 1)
        self.assertEqual(private_read_exit_code("model_sources_observed", False,
                                                 "player-model-sources"), 1)
        self.assertEqual(private_read_exit_code("cache_branch_observed", True,
                                                 "cache-view"), 0)

    def test_freezer_rejects_non_exact_source_commit_before_profile_operations(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            args = SimpleNamespace(candidate_root=Path(name), source_commit="c318",
                                   read_kind="player-model-sources")
            with self.assertRaisesRegex(RuntimeError, "full Git SHA"):
                seal(args)


if __name__ == "__main__":
    unittest.main()
