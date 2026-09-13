from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


from xar_autoplayer.simulation.raiktor_checkpoint_replay_recommendation_provider import (  # noqa: E402
    CheckpointReplayRecommendationError,
    provide_raiktor_checkpoint_replay_recommendation,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_action_gate import (  # noqa: E402
    provide_raiktor_three_way_exit_action_gate,
)
from test_raiktor_three_way_exit_action_gate import _capabilities  # noqa: E402
from test_raiktor_three_way_exit_recommendation import _provide  # noqa: E402
from test_raiktor_white_peace_narrow_projection_provider import (  # noqa: E402
    _snapshot,
)


def _replay() -> tuple[dict[str, object], dict[str, object]]:
    source = _provide(production_live=True)
    target = _snapshot()
    target["diagnostics"]["bridge_pid"] += 1
    replay = provide_raiktor_checkpoint_replay_recommendation(
        source,
        target,
        source_checkpoint_sha256="A" * 64,
        target_checkpoint_sha256="A" * 64,
        source_driver_state_sha256="B" * 64,
        target_driver_state_sha256="B" * 64,
    )
    return replay, target


class CheckpointReplayRecommendationProviderTests(unittest.TestCase):
    def test_rebinds_continue_and_enters_the_existing_action_gate(self) -> None:
        replay, target = _replay()

        self.assertEqual(replay["recommended_outcome"], "continue")
        self.assertEqual(replay["action_literal"], "resume-map")
        evidence = replay["recommendation_certificate"]["checkpoint_replay"]
        self.assertFalse(evidence["same_runtime_frame"])
        self.assertNotEqual(
            evidence["source_runtime_frame"]["ck3_pid"],
            evidence["target_runtime_frame"]["ck3_pid"],
        )
        gate = provide_raiktor_three_way_exit_action_gate(
            replay, target, _capabilities("resume-map")
        )
        self.assertTrue(gate["action_ready"])
        self.assertEqual(gate["action_literal"], "resume-map")

    def test_rejects_state_or_immutable_input_drift(self) -> None:
        source = _provide(production_live=True)
        target = _snapshot()
        target["diagnostics"]["bridge_pid"] += 1
        target["date_raw"] += 24
        with self.assertRaisesRegex(
            CheckpointReplayRecommendationError, "date_raw"
        ):
            provide_raiktor_checkpoint_replay_recommendation(
                source,
                target,
                source_checkpoint_sha256="A" * 64,
                target_checkpoint_sha256="A" * 64,
                source_driver_state_sha256="B" * 64,
                target_driver_state_sha256="B" * 64,
            )

        target["date_raw"] -= 24
        with self.assertRaisesRegex(
            CheckpointReplayRecommendationError, "checkpoint identity"
        ):
            provide_raiktor_checkpoint_replay_recommendation(
                source,
                target,
                source_checkpoint_sha256="A" * 64,
                target_checkpoint_sha256="C" * 64,
                source_driver_state_sha256="B" * 64,
                target_driver_state_sha256="B" * 64,
            )

    def test_rejects_non_continue_source(self) -> None:
        source = _provide(production_live=True, allow_white_favor=True)
        target = deepcopy(_snapshot())
        target["diagnostics"]["bridge_pid"] += 1
        with self.assertRaisesRegex(
            CheckpointReplayRecommendationError,
            "production continue recommendation",
        ):
            provide_raiktor_checkpoint_replay_recommendation(
                source,
                target,
                source_checkpoint_sha256="A" * 64,
                target_checkpoint_sha256="A" * 64,
                source_driver_state_sha256="B" * 64,
                target_driver_state_sha256="B" * 64,
            )


if __name__ == "__main__":
    unittest.main()
