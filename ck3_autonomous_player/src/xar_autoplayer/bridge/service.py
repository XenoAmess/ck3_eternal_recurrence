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
from .declaration_contract import (
    QUERY_DECLARABLE_WARS_STEP,
    declare_war_step,
)
from .marriage_contract import (
    QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
    arrange_marriage_step,
)
from .settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
    normalize_fixed_score,
    normalize_one_life_settlement,
    settlement_ready_for_episode,
)
from .war_contract import (
    RAISE_TROOPS_STEP,
    disband_army_step,
    enforce_demands_step,
    move_army_step,
    normalize_active_wars,
    player_armies_from_state,
    start_assault_step,
    stop_assault_step,
)
from ..strategy import choose_one_life_turn, read_one_life_strategy


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
        available_steps = action_step_set(capabilities)
        raw_history = snapshot.get("history")
        history = (
            [row for row in raw_history if isinstance(row, dict)]
            if isinstance(raw_history, list)
            else []
        )
        native_history = snapshot.get("native_command_history")
        if isinstance(native_history, list):
            history.extend(
                row for row in native_history if isinstance(row, dict)
            )
        cross_run_plan = None
        state_dir = self._strategy_state_dir()
        if state_dir is not None:
            strategy = read_one_life_strategy(state_dir)
            if strategy.get("episodes"):
                candidate = strategy.get("next_run_plan")
                if isinstance(candidate, dict):
                    cross_run_plan = candidate
        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps=available_steps,
            next_run_plan=cross_run_plan,
        )
        if cross_run_plan is not None:
            plan = {**plan, "cross_run_plan_used": cross_run_plan}
        return {
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "plan": _route_plan_to_available_step(plan, available_steps),
        }

    def _strategy_state_dir(self):
        state_dir = getattr(self.driver, "state_dir", None)
        if state_dir is not None:
            return state_dir
        native = getattr(self.driver, "native", None)
        return getattr(native, "state_dir", None)

    def auto_turn(self) -> dict[str, object]:
        """Plan and execute exactly one backend-supported gameplay turn."""
        planned = self.plan_turn()
        plan = planned.get("plan")
        selected_step = plan.get("selected_step") if isinstance(plan, dict) else None
        if not isinstance(selected_step, str) or not selected_step:
            return {
                "status": (
                    "terminal"
                    if isinstance(plan, dict)
                    and plan.get("phase") == "terminal_complete"
                    else "blocked"
                ),
                "plan": plan,
                "snapshot_id": planned.get("snapshot_id"),
                "revision": planned.get("revision"),
            }
        result = self.execute_step(
            selected_step,
            expected_revision=int(planned["revision"]),
        )
        return {
            "status": "executed",
            "selected_step": selected_step,
            "plan": plan,
            "result": result,
        }

    def one_life_settlement(self) -> dict[str, object]:
        """Return the terminal settlement state without scheduling heir play."""
        snapshot = self.snapshot()
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        supported = bool(
            isinstance(bridge_capabilities, list)
            and ONE_LIFE_SETTLEMENT_CAPABILITY in bridge_capabilities
        )
        settlement = normalize_one_life_settlement(
            snapshot.get("one_life_settlement")
        )
        episode_character_id = snapshot.get("episode_character_id")
        terminal = snapshot.get("one_life_terminal") is True or isinstance(
            snapshot.get("one_life_terminal_reason"), str
        )
        if not terminal:
            status = "not_terminal"
        elif not supported:
            status = "settlement_unavailable"
        elif settlement_ready_for_episode(settlement, episode_character_id):
            status = "ready"
        elif isinstance(settlement, dict) and settlement.get("ready") is True:
            status = "source_mismatch"
        else:
            status = "pending"
        return {
            "status": status,
            "supported": supported,
            "terminal": terminal,
            "terminal_reason": snapshot.get("one_life_terminal_reason"),
            "episode_character_id": episode_character_id,
            "one_life_settlement": settlement,
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "backend_id": snapshot.get("backend_id"),
        }

    def settle_one_life(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Wait for and record the current episode's bounded terminal handoff."""
        snapshot = self.snapshot()
        if not (
            snapshot.get("one_life_terminal") is True
            or isinstance(snapshot.get("one_life_terminal_reason"), str)
            or (
                isinstance(snapshot.get("played_character"), dict)
                and snapshot["played_character"].get("alive") is False
            )
        ):
            raise BridgeUnavailableError(
                "CK3 has not reached a one-life terminal"
            )
        if "death-terminal" not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                "selected backend cannot finalize the one-life terminal"
            )
        result = self.execute_step(
            "death-terminal",
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(snapshot["revision"])
            ),
        )
        if (
            result.get("terminal") is not True
            or result.get("continue_as_heir_after_death") is not False
            or result.get("heir_gameplay_actions", 0) != 0
        ):
            raise BridgeUnavailableError(
                "one-life terminal result violates the no-heir contract"
            )
        if result.get("settlement_status") != "settlement_unavailable":
            result = {
                **result,
                "score": normalize_fixed_score(result.get("score"), "score"),
            }
        return result

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

    def restore_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Restart the managed pure-native session at its latest checkpoint."""
        if "restore-checkpoint" not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                "selected backend does not implement gameplay step "
                "restore-checkpoint"
            )
        result = self.execute_step(
            "restore-checkpoint", expected_revision=expected_revision
        )
        if (
            not isinstance(result.get("checkpoint"), dict)
            or not isinstance(result.get("restored_date"), dict)
        ):
            raise BridgeUnavailableError(
                "restore-checkpoint result lacks checkpoint or restored date"
            )
        return result

    def start_next_episode(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Start a fresh one-life run from the immutable native seed."""
        if "start-next-episode" not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                "selected backend cannot start the next pure-native episode"
            )
        result = self.execute_step(
            "start-next-episode", expected_revision=expected_revision
        )
        if (
            result.get("status") != "started"
            or result.get("lifecycle_intent") != "new_episode"
            or not isinstance(result.get("episode_run_id"), str)
            or not isinstance(result.get("cross_run_plan_used"), dict)
        ):
            raise BridgeUnavailableError(
                "start-next-episode result lacks new-run lifecycle data"
            )
        return result

    def reply_pending_character_interaction(
        self,
        *,
        accept: bool,
        interaction_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Accept or reject the exact pending native character interaction."""
        if not isinstance(accept, bool):
            raise ValueError("accept must be a boolean")
        if interaction_instance_id is not None and (
            isinstance(interaction_instance_id, bool)
            or not isinstance(interaction_instance_id, int)
            or interaction_instance_id < 0
        ):
            raise ValueError(
                "interaction_instance_id must be a non-negative integer"
            )
        snapshot = self.snapshot()
        pending = snapshot.get("pending_character_interaction")
        if not isinstance(pending, dict):
            raise BridgeUnavailableError(
                "CK3 has no pending character interaction"
            )
        actual_instance_id = pending.get("instance_id")
        if (
            interaction_instance_id is not None
            and actual_instance_id != interaction_instance_id
        ):
            raise BridgeUnavailableError(
                "pending character interaction instance mismatch: "
                f"expected {interaction_instance_id}, current {actual_instance_id}"
            )
        step = (
            "accept-pending-character-interaction"
            if accept
            else "reject-pending-character-interaction"
        )
        if step not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                f"selected backend does not implement gameplay step {step}"
            )
        result = self.execute_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(snapshot["revision"])
            ),
        )
        return {
            **result,
            "interaction_instance_id": actual_instance_id,
            "sender_character_id": pending.get("sender_character_id"),
            "accepted": accept,
        }

    def war_state(self) -> dict[str, object]:
        """Return the canonical native war/army slice without visual reads."""
        snapshot = self.snapshot()
        active_wars = normalize_active_wars(snapshot.get("active_wars"))
        player_armies = player_armies_from_state(
            active_wars, snapshot.get("player_armies")
        )
        return {
            "status": (
                "active"
                if active_wars
                else "postwar_armies"
                if player_armies
                else "idle"
            ),
            "active_wars": active_wars,
            "player_armies": player_armies,
            "snapshot_id": snapshot["snapshot_id"],
            "revision": snapshot["revision"],
            "backend_id": snapshot.get("backend_id"),
        }

    def query_arrange_marriage_choices(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Enumerate exact native marriage choices for the played character."""
        if QUERY_ARRANGE_MARRIAGE_CHOICES_STEP not in action_step_set(
            self.capabilities()
        ):
            raise UnsupportedStepError(
                "selected backend cannot query native marriage choices"
            )
        snapshot = self.snapshot()
        result = self.execute_step(
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(snapshot["revision"])
            ),
        )
        if not isinstance(result.get("arrange_marriage_choices"), list):
            raise BridgeUnavailableError(
                "native marriage query lacks arrange_marriage_choices"
            )
        return result

    def arrange_marriage(
        self,
        choice_id: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit one exact choice returned by the latest marriage query."""
        step = arrange_marriage_step(choice_id)
        snapshot = self.snapshot()
        if step not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                f"selected backend cannot execute native marriage {choice_id}"
            )
        return self.execute_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(snapshot["revision"])
            ),
        )

    def query_declarable_wars(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Run CK3's native declaration evaluator on demand."""
        if QUERY_DECLARABLE_WARS_STEP not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                "selected backend cannot query native war declarations"
            )
        snapshot = self.snapshot()
        result = self.execute_step(
            QUERY_DECLARABLE_WARS_STEP,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(snapshot["revision"])
            ),
        )
        if not isinstance(result.get("declarable_wars"), list):
            raise BridgeUnavailableError(
                "native declaration query lacks declarable_wars"
            )
        return result

    def declare_war(
        self,
        declaration_id: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit one exact choice returned by the latest native query."""
        step = declare_war_step(declaration_id)
        snapshot = self.snapshot()
        if step not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                f"selected backend cannot execute native declaration {declaration_id}"
            )
        return self.execute_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(snapshot["revision"])
            ),
        )

    def raise_troops_default(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Raise troops for the current war at CK3's native default point."""
        return self._execute_typed_war_step(
            RAISE_TROOPS_STEP, expected_revision=expected_revision
        )

    def move_army(
        self,
        army_id: int,
        target_province_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Move one exact native army to one exact CK3 province."""
        step = move_army_step(army_id, target_province_id)
        return {
            **self._execute_typed_war_step(
                step, expected_revision=expected_revision
            ),
            "army_id": army_id,
            "target_province_id": target_province_id,
        }

    def start_assault(
        self,
        siege_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Start Assault on one exact full-generation native SiegeID."""
        step = start_assault_step(siege_id)
        return {
            **self._execute_typed_war_step(
                step, expected_revision=expected_revision
            ),
            "siege_id": siege_id,
        }

    def stop_assault(
        self,
        siege_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Stop Assault on one exact full-generation native SiegeID."""
        step = stop_assault_step(siege_id)
        return {
            **self._execute_typed_war_step(
                step, expected_revision=expected_revision
            ),
            "siege_id": siege_id,
        }

    def disband_army(
        self,
        army_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Disband one exact native player army."""
        step = disband_army_step(army_id)
        return {
            **self._execute_typed_war_step(
                step, expected_revision=expected_revision
            ),
            "army_id": army_id,
        }

    def enforce_demands(
        self,
        war_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Enforce victory in one exact native war at 100% war score."""
        step = enforce_demands_step(war_id)
        return {
            **self._execute_typed_war_step(
                step, expected_revision=expected_revision
            ),
            "war_id": war_id,
        }

    def _execute_typed_war_step(
        self, step: str, *, expected_revision: int | None
    ) -> dict[str, object]:
        if step not in action_step_set(self.capabilities()):
            raise UnsupportedStepError(
                f"selected backend does not implement native war step {step}"
            )
        snapshot = self.snapshot()
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(snapshot["revision"])
        )
        return self.execute_step(step, expected_revision=selected_revision)

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        return self.driver.wait_for_change(
            after_revision, timeout_seconds=timeout_seconds
        )


def _route_plan_to_available_step(
    plan: dict[str, object], available_steps: set[str]
) -> dict[str, object]:
    """Keep a partial native backend playing instead of dispatching unsupported work."""
    selected = plan.get("selected_step")
    if not isinstance(selected, str) or selected in available_steps:
        return plan
    if selected in {"death-terminal", "strategy-review", "resolve-current-event"}:
        return {
            **plan,
            "selected_step": None,
            "required_step": selected,
            "reason": f"selected backend does not implement required step {selected}",
        }
    if "life-advance" in available_steps:
        return {
            **plan,
            "phase": "capability_progress",
            "deferred_phase": plan.get("phase"),
            "selected_step": "life-advance",
            "required_step": selected,
            "reason": (
                f"selected backend does not yet implement {selected}; "
                "continue the current life through native events"
            ),
        }
    return {
        **plan,
        "selected_step": None,
        "required_step": selected,
        "reason": f"selected backend does not implement gameplay step {selected}",
    }
