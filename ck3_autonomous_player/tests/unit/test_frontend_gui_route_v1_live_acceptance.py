from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    PROJECT_ROOT
    / "native_bridge"
    / "research"
    / "run_frontend_gui_route_v1_live_acceptance.py"
)


class FrontendGuiRouteLiveAcceptanceContractTests(unittest.TestCase):
    def test_shared_ck3_slot_wraps_launch_and_cleanup(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        launch_lock = source.index(
            "slot_stack.enter_context(exclusive_launch_lock(spec.game_exe))"
        )
        state_lock = source.index("exclusive_state_lock(", launch_lock)
        launch = source.index("handle = launch(", state_lock)
        cleanup = source.index("cleanup = stop_tracked(", launch)
        release = source.index("slot_stack.close()", cleanup)

        self.assertLess(launch_lock, state_lock)
        self.assertLess(state_lock, launch)
        self.assertLess(launch, cleanup)
        self.assertLess(cleanup, release)


if __name__ == "__main__":
    unittest.main()
