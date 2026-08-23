"""Planner-facing service shared by MCP tools and direct autonomous mode."""

from __future__ import annotations

from .driver import GameplayBridgeDriver
from ..strategy import choose_one_life_turn


class GameplayBridgeService:
    def __init__(self, driver: GameplayBridgeDriver) -> None:
        self.driver = driver

    def capabilities(self) -> dict[str, object]:
        return self.driver.capabilities()

    def snapshot(self) -> dict[str, object]:
        return self.driver.take_snapshot()

    def plan_turn(self) -> dict[str, object]:
        snapshot = self.snapshot()
        raw_history = snapshot.get("history")
        history = (
            [row for row in raw_history if isinstance(row, dict)]
            if isinstance(raw_history, list)
            else []
        )
        return {
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "plan": choose_one_life_turn(history),
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        return self.driver.execute_step(step, expected_revision=expected_revision)

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        return self.driver.wait_for_change(
            after_revision, timeout_seconds=timeout_seconds
        )
