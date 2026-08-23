"""Planner-facing service shared by MCP tools and direct autonomous mode."""

from __future__ import annotations

from .driver import (
    BridgeUnavailableError,
    GameplayBridgeDriver,
    UnsupportedStepError,
)
from .event_contract import (
    action_step_set,
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
)
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
        capabilities = self.capabilities()
        raw_history = snapshot.get("history")
        history = (
            [row for row in raw_history if isinstance(row, dict)]
            if isinstance(raw_history, list)
            else []
        )
        return {
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "plan": choose_one_life_turn(
                history,
                snapshot=snapshot,
                action_steps=action_step_set(capabilities),
            ),
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Select one rendered event option by its 1-based number."""
        step = event_option_step(option_number)
        if event_instance_id is not None and (
            isinstance(event_instance_id, bool)
            or not isinstance(event_instance_id, int)
            or event_instance_id < 0
        ):
            raise ValueError("event_instance_id must be a non-negative integer")

        snapshot = self.snapshot()
        active_event = normalize_active_event(
            snapshot.get("active_event", snapshot.get("current_event")),
            default_source=str(snapshot.get("source") or "bridge"),
        )
        if active_event is None:
            raise BridgeUnavailableError("CK3 has no active event")
        actual_instance_id = active_event.get("instance_id")
        if event_instance_id is not None:
            if actual_instance_id is None:
                raise BridgeUnavailableError(
                    "the active event backend cannot verify event_instance_id"
                )
            if actual_instance_id != event_instance_id:
                raise BridgeUnavailableError(
                    "active event instance mismatch: "
                    f"expected {event_instance_id}, current {actual_instance_id}"
                )

        option = next(
            (
                row
                for row in active_event["options"]
                if isinstance(row, dict)
                and row.get("option_number") == option_number
            ),
            None,
        )
        if option is None:
            raise BridgeUnavailableError(
                f"active event does not expose option {option_number}"
            )
        if option.get("enabled") is not True:
            raise BridgeUnavailableError(
                f"active event option {option_number} is disabled"
            )
        if step not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                f"selected backend does not implement gameplay step {step}"
            )

        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(snapshot["revision"])
        )
        result = self.execute_step(step, expected_revision=selected_revision)
        return {
            **result,
            "event_instance_id": actual_instance_id,
            "option_number": option_number,
            "option_index": option_number - 1,
        }

    def resolve_active_event(
        self,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Choose and dispatch the best enabled option on the active event."""
        snapshot = self.snapshot()
        active_event = normalize_active_event(
            snapshot.get("active_event", snapshot.get("current_event")),
            default_source=str(snapshot.get("source") or "bridge"),
        )
        option_number = choose_event_option_number(active_event)
        if option_number is None:
            raise BridgeUnavailableError(
                "CK3 has no active event with an enabled option"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(snapshot["revision"])
        )
        selected_instance_id = (
            event_instance_id
            if event_instance_id is not None
            else active_event.get("instance_id")
        )
        result = self.select_event_option(
            option_number,
            event_instance_id=(
                selected_instance_id
                if isinstance(selected_instance_id, int)
                else None
            ),
            expected_revision=selected_revision,
        )
        selected_option = next(
            (
                option
                for option in active_event["options"]
                if isinstance(option, dict)
                and option.get("option_number") == option_number
            ),
            {},
        )
        return {
            **result,
            "ordinary_events": [
                {
                    "event_index": 1,
                    "event_instance_id": active_event.get("instance_id"),
                    "title": active_event.get("title"),
                    "visible_options": active_event.get("options", []),
                    "selected_option_number": option_number,
                    "selected_option_index": option_number - 1,
                    "selected_visible_text": selected_option.get("label"),
                    "strategy": "backend-neutral-event-v1",
                    "source": active_event.get("source"),
                }
            ],
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        return self.driver.execute_step(step, expected_revision=expected_revision)

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Execute the shared checkpoint step and return its materialization."""
        if "save-checkpoint" not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                "selected backend does not implement gameplay step save-checkpoint"
            )
        result = self.execute_step(
            "save-checkpoint", expected_revision=expected_revision
        )
        if not isinstance(result.get("checkpoint"), dict):
            raise BridgeUnavailableError(
                "save-checkpoint result lacks checkpoint materialization"
            )
        return result

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        return self.driver.wait_for_change(
            after_revision, timeout_seconds=timeout_seconds
        )
