"""Planner-facing service shared by MCP tools and direct autonomous mode."""

from __future__ import annotations

import copy

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
from .combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    combat_simulation_encounter_scope,
    combat_simulation_inputs_status,
    normalize_combat_simulation_inputs,
    normalize_combat_simulation_request,
    query_combat_simulation_inputs_step,
)
from .combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    combat_simulation_inputs_v3_status,
    normalize_combat_simulation_inputs_v3,
    query_combat_simulation_inputs_v3_step,
)
from .war_exit_terms_contract import (
    WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED,
    query_war_termination_exit_terms_step,
)
from .war_entry_contract import (
    QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
    normalize_war_entry_assessments,
    normalize_war_entry_target_ids,
    query_war_entry_assessments_step,
    require_declarable_war_targets,
)
from ..simulation.loaded_playset_proof import (
    LoadedPlaysetProofError,
    build_loaded_playset_proof,
    unavailable_loaded_playset_proof,
)
from .settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
    normalize_fixed_score,
    normalize_one_life_settlement,
    settlement_ready_for_episode,
)
from .war_contract import (
    QUERY_ARMY_STRENGTHS_STEP,
    RAISE_TROOPS_STEP,
    army_strength_query_status,
    army_strength_scope,
    disband_army_step,
    enforce_demands_step,
    move_army_step,
    normalize_active_wars,
    normalize_army_strength_request_ids,
    normalize_army_strengths,
    offer_white_peace_step,
    player_armies_from_state,
    query_war_termination_options_step,
    query_war_termination_terms_step,
    start_assault_step,
    stop_assault_step,
    surrender_war_step,
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

    def _loaded_playset_proof_for_snapshot(
        self, snapshot: dict[str, object]
    ) -> dict[str, object]:
        """Attest the managed loaded playset without changing static manifest truth."""
        episode_run_id = snapshot.get("episode_run_id")
        state_dir = self._strategy_state_dir()
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        snapshot_binding = {
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
        }
        if state_dir is None:
            return unavailable_loaded_playset_proof(
                episode_run_id=episode_run_id,
                reason="managed_state_dir_unavailable",
            )
        try:
            proof = build_loaded_playset_proof(
                state_dir,
                episode_run_id=episode_run_id,
                snapshot_binding=snapshot_binding,
                native_hello=hello,
            )
            latest = self.snapshot()
            latest_binding = {
                "snapshot_id": latest.get("snapshot_id"),
                "revision": latest.get("revision"),
                "native_revision": latest.get("native_revision"),
            }
            if not (
                latest.get("paused") is True
                and latest.get("episode_run_id") == episode_run_id
                and latest_binding == snapshot_binding
            ):
                return unavailable_loaded_playset_proof(
                    episode_run_id=episode_run_id,
                    reason="snapshot_changed_during_loaded_playset_proof",
                )
            return proof
        except (LoadedPlaysetProofError, OSError, UnicodeError) as error:
            return unavailable_loaded_playset_proof(
                episode_run_id=episode_run_id,
                reason=f"{type(error).__name__}: {error}",
            )

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
            "war_termination_options": (
                snapshot.get("war_termination_options")
                if isinstance(snapshot.get("war_termination_options"), list)
                else []
            ),
            "war_termination_terms": (
                snapshot.get("war_termination_terms")
                if isinstance(snapshot.get("war_termination_terms"), list)
                else []
            ),
            "war_termination_exit_terms": (
                snapshot.get("war_termination_exit_terms")
                if isinstance(
                    snapshot.get("war_termination_exit_terms"), list
                )
                else []
            ),
            "army_strengths": (
                snapshot.get("army_strengths")
                if isinstance(snapshot.get("army_strengths"), list)
                else []
            ),
            "army_strengths_status": snapshot.get("army_strengths_status"),
            "army_strengths_query_sequence": snapshot.get(
                "army_strengths_query_sequence"
            ),
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

    def query_war_termination_options(
        self,
        war_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read CK3's exact termination contexts for one active WarID."""
        step = query_war_termination_options_step(war_id)
        result = self._execute_typed_war_step(
            step, expected_revision=expected_revision
        )
        options = result.get("war_termination_options")
        if not isinstance(options, dict) or options.get("war_id") != war_id:
            raise BridgeUnavailableError(
                "native termination query lacks matching war_termination_options"
            )
        return {**result, "war_id": war_id}

    def query_war_termination_terms(
        self,
        war_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read the complete claim-CB disposition slice for one WarID."""
        step = query_war_termination_terms_step(war_id)
        result = self._execute_typed_war_step(
            step, expected_revision=expected_revision
        )
        terms = result.get("war_termination_terms")
        if not isinstance(terms, dict) or terms.get("war_id") != war_id:
            raise BridgeUnavailableError(
                "native terms query lacks matching war_termination_terms"
            )
        return {**result, "war_id": war_id}

    def query_war_termination_exit_terms(
        self,
        war_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read the complete dry-preview claim-CB exit slice for one WarID."""
        if not WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED:
            raise BridgeUnavailableError(
                "war-termination exit-terms v2 is disabled after a "
                "reproducible native loaded-effect preview crash"
            )
        step = query_war_termination_exit_terms_step(war_id)
        result = self._execute_typed_war_step(
            step, expected_revision=expected_revision
        )
        terms = result.get("war_termination_exit_terms")
        if not isinstance(terms, dict) or terms.get("war_id") != war_id:
            raise BridgeUnavailableError(
                "native exit-terms query lacks matching "
                "war_termination_exit_terms"
            )
        return {**result, "war_id": war_id}

    def query_army_strengths(
        self,
        army_ids: list[int],
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read a requested subset of native base aggregates atomically.

        This is deliberately not a combat prediction: soldier totals and the
        AI regiment base-power lane omit terrain, commanders, counters, and
        other encounter context.
        """
        requested_ids = normalize_army_strength_request_ids(army_ids)
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "army-strength queries require a paused CK3 snapshot"
            )
        try:
            scope = army_strength_scope(snapshot)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"army-strength scope is malformed: {error}"
            ) from error
        scope_ids = [int(row["army_id"]) for row in scope]
        outside_scope = [
            army_id for army_id in requested_ids if army_id not in scope_ids
        ]
        if outside_scope:
            raise BridgeUnavailableError(
                "army_ids are outside the current published player/war "
                f"scope: {outside_scope}"
            )
        if QUERY_ARMY_STRENGTHS_STEP not in action_step_set(
            self.capabilities()
        ):
            raise UnsupportedStepError(
                "selected backend cannot query native army strengths"
            )
        selected_revision = (
            expected_revision
            if expected_revision is not None
            else int(snapshot["revision"])
        )
        result = self.execute_step(
            QUERY_ARMY_STRENGTHS_STEP,
            expected_revision=selected_revision,
        )
        try:
            rows = normalize_army_strengths(
                result.get("army_strengths"), expected_scope=scope
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native army-strength result is malformed: {error}"
            ) from error
        scope_status = army_strength_query_status(rows)
        if result.get("status") != scope_status:
            raise BridgeUnavailableError(
                "native army-strength status disagrees with its full scope"
            )
        by_id = {int(row["army_id"]): row for row in rows}
        selected_rows = [by_id[army_id] for army_id in requested_ids]
        status = army_strength_query_status(selected_rows)
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        return {
            **result,
            "schema_version": 1,
            "status": status,
            "scope_status": scope_status,
            "scope": "player-and-active-war-participants",
            "source": {
                "game_version": (
                    hello.get("game_version")
                    if isinstance(hello, dict)
                    else None
                ),
                "executable_sha256": (
                    hello.get("executable_sha256")
                    if isinstance(hello, dict)
                    else None
                ),
                "snapshot_id": snapshot.get("snapshot_id"),
                "revision": snapshot.get("revision"),
                "native_revision": snapshot.get("native_revision"),
                "date_raw": snapshot.get("date_raw"),
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            "army_ids": requested_ids,
            "scope_army_ids": scope_ids,
            "army_strengths": selected_rows,
        }

    def query_combat_simulation_inputs(
        self,
        target_province_id: int,
        attacker_entry_province_id: int,
        attacker_army_ids: list[int],
        defender_army_ids: list[int],
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read exact-build inputs for one hypothetical contact scenario.

        ``available`` means only that all native observation domains needed by
        the documented combat model are present.  It never means that Monte
        Carlo simulation is ready.
        """
        target, entry, attackers, defenders = normalize_combat_simulation_request(
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
        )
        step = query_combat_simulation_inputs_step(
            target, entry, attackers, defenders
        )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "combat simulation input queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int):
            raise BridgeUnavailableError(
                "combat simulation input query lacks a valid snapshot revision"
            )
        if expected_revision is not None:
            if (
                isinstance(expected_revision, bool)
                or not isinstance(expected_revision, int)
                or expected_revision < 0
            ):
                raise ValueError(
                    "expected_revision must be a non-negative integer"
                )
            if expected_revision != revision:
                raise BridgeUnavailableError(
                    "combat simulation input revision mismatch: expected "
                    f"{expected_revision}, current {revision}"
                )
        try:
            encounter_scope = combat_simulation_encounter_scope(
                snapshot, attackers, defenders
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"combat simulation encounter scope is malformed: {error}"
            ) from error
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query combat simulation inputs"
            )
        result = self.execute_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else revision
            ),
        )
        if not isinstance(result, dict):
            raise BridgeUnavailableError(
                "combat simulation input backend returned a non-object result"
            )
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "combat_simulation_inputs",
            "backend_id",
        }
        optional_result_keys = {
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
        }
        if (
            not required_result_keys <= set(result)
            or set(result) - required_result_keys - optional_result_keys
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") not in {"available", "partial"}
        ):
            raise BridgeUnavailableError(
                "combat simulation input backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "combat simulation input result lacks query_sequence"
            )
        try:
            normalized = normalize_combat_simulation_inputs(
                result.get("combat_simulation_inputs"),
                expected_target_province_id=target,
                expected_attacker_entry_province_id=entry,
                expected_encounter_scope=encounter_scope,
            )
            status = combat_simulation_inputs_status(normalized)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"combat simulation input result is malformed: {error}"
            ) from error
        if result.get("status") != status:
            raise BridgeUnavailableError(
                "combat simulation input status disagrees with "
                "input_observation_ready"
            )
        if (
            "queried_snapshot_id" in result
            and result.get("queried_snapshot_id")
            != snapshot.get("snapshot_id")
        ) or (
            "queried_revision" in result
            and result.get("queried_revision") != revision
        ) or (
            "queried_native_revision" in result
            and result.get("queried_native_revision")
            != snapshot.get("native_revision")
        ):
            raise BridgeUnavailableError(
                "combat simulation input result is bound to another snapshot"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("native_revision")
            == snapshot.get("native_revision")
        ):
            raise BridgeUnavailableError(
                "combat simulation input query crossed a snapshot revision"
            )
        try:
            if combat_simulation_encounter_scope(
                current, attackers, defenders
            ) != encounter_scope:
                raise BridgeUnavailableError(
                    "combat simulation encounter scope changed during query"
                )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"combat simulation encounter scope became malformed: {error}"
            ) from error
        completeness = normalized["completeness"]
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        return {
            **result,
            "schema_version": 2,
            "status": status,
            "scope": "explicit-hypothetical-active-war-contact",
            "source": {
                "game_version": (
                    hello.get("game_version")
                    if isinstance(hello, dict)
                    else None
                ),
                "executable_sha256": (
                    hello.get("executable_sha256")
                    if isinstance(hello, dict)
                    else None
                ),
                "snapshot_id": snapshot.get("snapshot_id"),
                "revision": revision,
                "native_revision": snapshot.get("native_revision"),
                "date_raw": snapshot.get("date_raw"),
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            "target_province_id": target,
            "attacker_entry_province_id": entry,
            "attacker_army_ids": attackers,
            "defender_army_ids": defenders,
            "attacker_side": encounter_scope["attacker_side"],
            "defender_side": encounter_scope["defender_side"],
            "common_war_ids": encounter_scope["common_war_ids"],
            "input_observation_ready": completeness[
                "input_observation_ready"
            ],
            "monte_carlo_ready": completeness["monte_carlo_ready"],
            "missing_required_domains": copy.deepcopy(
                completeness["missing_required_domains"]
            ),
            "combat_simulation_inputs": normalized,
        }

    def query_combat_simulation_inputs_v3(
        self,
        target_province_id: int,
        attacker_entry_province_id: int,
        attacker_army_ids: list[int],
        defender_army_ids: list[int],
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read and offline-normalize the exact 132-ref phase-event slice."""
        target, entry, attackers, defenders = normalize_combat_simulation_request(
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
        )
        step = query_combat_simulation_inputs_v3_step(
            target, entry, attackers, defenders
        )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "production combat phase queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int):
            raise BridgeUnavailableError(
                "production combat phase query lacks a valid snapshot revision"
            )
        if expected_revision is not None:
            if (
                isinstance(expected_revision, bool)
                or not isinstance(expected_revision, int)
                or expected_revision < 0
            ):
                raise ValueError(
                    "expected_revision must be a non-negative integer"
                )
            if expected_revision != revision:
                raise BridgeUnavailableError(
                    "production combat phase revision mismatch: expected "
                    f"{expected_revision}, current {revision}"
                )
        try:
            encounter_scope = combat_simulation_encounter_scope(
                snapshot, attackers, defenders
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"production combat phase encounter scope is malformed: {error}"
            ) from error
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query production combat phase inputs"
            )
        result = self.execute_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else revision
            ),
        )
        if not isinstance(result, dict):
            raise BridgeUnavailableError(
                "production combat phase backend returned a non-object result"
            )
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "combat_simulation_inputs",
            "backend_id",
        }
        optional_result_keys = {
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
        }
        if (
            not required_result_keys <= set(result)
            or set(result) - required_result_keys - optional_result_keys
            or result.get("step") != step
            or result.get("accepted") is not True
            or result.get("status") not in {"available", "unavailable"}
        ):
            raise BridgeUnavailableError(
                "production combat phase backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "production combat phase result lacks query_sequence"
            )
        try:
            normalized = normalize_combat_simulation_inputs_v3(
                result.get("combat_simulation_inputs"),
                expected_target_province_id=target,
                expected_attacker_entry_province_id=entry,
                expected_encounter_scope=encounter_scope,
            )
            status = combat_simulation_inputs_v3_status(normalized)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"production combat phase result is malformed: {error}"
            ) from error
        if result.get("status") != status:
            raise BridgeUnavailableError(
                "production combat phase status disagrees with "
                "phase_event_inputs_ready"
            )
        if (
            "queried_snapshot_id" in result
            and result.get("queried_snapshot_id")
            != snapshot.get("snapshot_id")
        ) or (
            "queried_revision" in result
            and result.get("queried_revision") != revision
        ) or (
            "queried_native_revision" in result
            and result.get("queried_native_revision")
            != snapshot.get("native_revision")
        ):
            raise BridgeUnavailableError(
                "production combat phase result is bound to another snapshot"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("native_revision")
            == snapshot.get("native_revision")
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "production combat phase query crossed a snapshot revision"
            )
        try:
            if combat_simulation_encounter_scope(
                current, attackers, defenders
            ) != encounter_scope:
                raise BridgeUnavailableError(
                    "production combat phase encounter scope changed during query"
                )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"production combat phase scope became malformed: {error}"
            ) from error
        completeness = normalized["completeness"]
        loaded_playset_proof = self._loaded_playset_proof_for_snapshot(
            current
        )
        loaded_playset_verified = (
            loaded_playset_proof.get("status") == "verified"
            and isinstance(loaded_playset_proof.get("claims"), dict)
            and loaded_playset_proof["claims"].get(
                "loaded_playset_verified"
            )
            is True
        )
        phase_event_manifest_fidelity = copy.deepcopy(
            completeness["phase_event_manifest_fidelity"]
        )
        phase_event_manifest_fidelity["loaded_playset_verified"] = (
            loaded_playset_verified
        )
        phase_event_manifest_fidelity["fidelity_gate"] = all(
            phase_event_manifest_fidelity.get(key) is True
            for key in (
                "loaded_playset_verified",
                "ast_evaluator_ready",
                "original_trace_ready",
            )
        )
        missing_fidelity_gates = [
            key
            for key in completeness["missing_fidelity_gates"]
            if key != "loaded_playset_verified" or not loaded_playset_verified
        ]
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        return {
            **result,
            "schema_version": 3,
            "status": status,
            "scope": "explicit-hypothetical-active-war-contact",
            "source": {
                "game_version": (
                    hello.get("game_version")
                    if isinstance(hello, dict)
                    else None
                ),
                "executable_sha256": (
                    hello.get("executable_sha256")
                    if isinstance(hello, dict)
                    else None
                ),
                "snapshot_id": snapshot.get("snapshot_id"),
                "revision": revision,
                "native_revision": snapshot.get("native_revision"),
                "date_raw": snapshot.get("date_raw"),
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            "target_province_id": target,
            "attacker_entry_province_id": entry,
            "attacker_army_ids": attackers,
            "defender_army_ids": defenders,
            "attacker_side": encounter_scope["attacker_side"],
            "defender_side": encounter_scope["defender_side"],
            "common_war_ids": encounter_scope["common_war_ids"],
            "base_input_observation_ready": completeness[
                "base_input_observation_ready"
            ],
            "phase_raw_observation_ready": completeness[
                "phase_raw_observation_ready"
            ],
            "offline_exact_state_refs_ready": completeness[
                "offline_exact_state_refs_ready"
            ],
            "phase_event_inputs_ready": completeness[
                "phase_event_inputs_ready"
            ],
            "input_observation_ready": completeness[
                "input_observation_ready"
            ],
            "monte_carlo_ready": completeness["monte_carlo_ready"],
            "transition_fidelity_gate": completeness[
                "transition_fidelity_gate"
            ],
            "planner_usable": completeness["planner_usable"],
            "active_attack_allowed": completeness[
                "active_attack_allowed"
            ],
            "phase_event_manifest_fidelity": phase_event_manifest_fidelity,
            "loaded_playset_proof": loaded_playset_proof,
            "missing_observation_domains": copy.deepcopy(
                completeness["missing_observation_domains"]
            ),
            "missing_fidelity_gates": missing_fidelity_gates,
            "missing_required_domains": copy.deepcopy(
                completeness["missing_required_domains"]
            ),
            "combat_simulation_inputs": normalized,
        }

    def query_war_entry_assessments(
        self,
        target_character_ids: list[int],
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read exact native strategic power for one declaration target."""
        # Reject an over-broad public request before reading a snapshot or
        # entering any driver/pipe path. The first production contract is
        # one-target end to end.
        targets = normalize_war_entry_target_ids(target_character_ids)
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "war-entry assessment queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int):
            raise BridgeUnavailableError(
                "war-entry assessment query lacks a valid snapshot revision"
            )
        if expected_revision is not None:
            if (
                isinstance(expected_revision, bool)
                or not isinstance(expected_revision, int)
                or expected_revision < 0
            ):
                raise ValueError(
                    "expected_revision must be a non-negative integer"
                )
            if expected_revision != revision:
                raise BridgeUnavailableError(
                    "war-entry assessment revision mismatch: expected "
                    f"{expected_revision}, current {revision}"
                )
        try:
            targets = require_declarable_war_targets(
                snapshot, targets
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"war-entry assessment target scope is malformed: {error}"
            ) from error
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query native war-entry assessments"
            )
        step = query_war_entry_assessments_step(targets)
        result = self.execute_step(
            step,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else revision
            ),
        )
        played_character = snapshot.get("played_character")
        actor_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        native_revision = snapshot.get("native_revision")
        try:
            normalized = normalize_war_entry_assessments(
                result.get("war_entry_assessments"),
                expected_target_character_ids=targets,
                expected_actor_character_id=actor_id,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"native war-entry assessment result is malformed: {error}"
            ) from error
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "war-entry assessment query crossed a snapshot revision"
            )
        try:
            require_declarable_war_targets(current, targets)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"war-entry declarations changed during query: {error}"
            ) from error
        return {
            **result,
            "schema_version": 1,
            "status": "available",
            "target_character_ids": targets,
            "war_entry_assessments": normalized,
            "queried_snapshot_id": snapshot.get("snapshot_id"),
            "queried_revision": revision,
            "queried_native_revision": native_revision,
        }

    def surrender_war(
        self,
        war_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit a query-proven surrender; never infer it from war score."""
        step = surrender_war_step(war_id)
        return {
            **self._execute_typed_war_step(
                step, expected_revision=expected_revision
            ),
            "war_id": war_id,
        }

    def offer_white_peace(
        self,
        war_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit white peace only when native support and query both prove it."""
        step = offer_white_peace_step(war_id)
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
    fail_closed_prefixes = (
        "declare-war-",
        "war-declare-",
        "offer-white-peace-",
        "surrender-war-",
        "query-war-termination-options-",
        "query-war-termination-terms-v1-",
        "query-war-termination-exit-terms-v2-",
        "query-combat-simulation-inputs-v2-",
        "query-combat-simulation-inputs-v3-",
        "query-war-entry-assessments-v1-",
        "enforce-demands-",
    )
    if (
        selected
        in {"death-terminal", "strategy-review", "resolve-current-event"}
        or selected.startswith(fail_closed_prefixes)
    ):
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
