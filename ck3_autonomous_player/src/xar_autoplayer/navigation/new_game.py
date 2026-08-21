"""First Phase B transition: main menu to the historical bookmark screen."""

from __future__ import annotations

from ..control.executor import VisibleUiDriver
from ..errors import AgentError


def probe_main_menu_to_bookmarks(
    driver: VisibleUiDriver, timeout_seconds: float
) -> dict[str, object]:
    before = driver.observe_stable(
        "main_menu", timeout_seconds, stable_frames=2
    )
    controls = [
        control for control in before.controls if control.control_id == "main_menu.new_game"
    ]
    if len(controls) != 1:
        raise AgentError("main menu did not expose exactly one New Game capability")
    transition = driver.click_visible_control(
        controls[0].token,
        timeout_seconds=min(timeout_seconds, 30),
    )
    registered = sorted(driver.registered_capabilities)
    return {
        "claim": "visible_main_menu_to_bookmark_lobby_only",
        "start_observation": before.to_policy_json(),
        "transition": transition,
        "registered_capabilities": registered,
        "forbidden_capabilities": sorted(
            driver.contract.forbidden_capabilities
        ),
        "start_game_capability_registered": (
            "bookmark_lobby.start_game" in driver.registered_capabilities
        ),
    }
