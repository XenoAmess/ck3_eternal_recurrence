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

    def test_runner_requires_and_checks_the_coat_of_arms_route(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")

        self.assertIn(
            '"game.command.activate-frontend-coat-of-arms-designer-v1"',
            source,
        )
        self.assertIn(
            '"ck3_activate_frontend_coat_of_arms_designer_v1"', source
        )
        self.assertIn('== "coat_of_arms_designer"', source)
        self.assertIn('row.get("runtime_name") == "coat_of_arms_page"', source)


if __name__ == "__main__":
    unittest.main()
