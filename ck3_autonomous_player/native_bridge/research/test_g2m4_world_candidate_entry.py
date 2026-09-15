"""No-launch focused world-read candidate result semantics."""

from __future__ import annotations

import unittest

from run_g2m4_player_view_live_candidate import private_read_exit_code


class WorldCandidateEntryTests(unittest.TestCase):
    def test_world_player_sample_and_reclaimed_ck3_control_success(self) -> None:
        self.assertEqual(private_read_exit_code(
            "world_player_legality_observed", True,
            "player-world-definitions"), 0)
        self.assertEqual(private_read_exit_code(
            "world_source_evidence_insufficient", True,
            "player-world-definitions"), 2)
        self.assertEqual(private_read_exit_code(
            "cache_branch_observed", True,
            "player-world-definitions"), 1)
        self.assertEqual(private_read_exit_code(
            "world_player_legality_observed", False,
            "player-world-definitions"), 1)
        self.assertEqual(private_read_exit_code(
            "red", True, "player-world-definitions"), 1)


if __name__ == "__main__":
    unittest.main()
