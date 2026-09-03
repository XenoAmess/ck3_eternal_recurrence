"""Planner-facing service shared by MCP tools and direct autonomous mode."""

from __future__ import annotations

import copy

from .driver import (
    BridgeUnavailableError,
    GameplayBridgeDriver,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
    UnsupportedStepError,
)
from .event_contract import (
    action_step_set,
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
    parse_event_option_step,
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
from .actual_contact_contract import query_actual_contact_scope_step
from .battle_control_contract import (
    QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY,
    normalize_battle_control_snapshot_v1,
    query_battle_control_snapshot_v1_step,
)
from .battle_transition_contract import (
    QUERY_BATTLE_TRANSITION_V1_CAPABILITY,
    normalize_battle_transition_v1,
    query_battle_transition_v1_step,
)
from .battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    normalize_battle_terminal_transition_v1,
    parse_query_battle_terminal_transition_v1_step,
    query_battle_terminal_transition_v1_step,
)
from .battle_reinforcement_assignment_contract import (
    QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY,
    normalize_battle_reinforcement_assignment_v1,
    query_battle_reinforcement_assignment_v1_step,
)
from .campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
    normalize_campaign_root_context_v1,
)
from .zhongguo_case_snapshot_contract import (
    QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP,
    ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID,
    normalize_native_zhongguo_case_snapshot_v1,
    normalize_zhongguo_case_snapshot_v1_response,
    parse_query_zhongguo_case_snapshot_v1_step,
    query_zhongguo_case_snapshot_v1_step,
)
from .zhongguo_ai_owned_case_snapshot_contract import (
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP,
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID,
    normalize_native_zhongguo_ai_owned_case_snapshot_v1,
    normalize_zhongguo_ai_owned_case_snapshot_v1_response,
    parse_query_zhongguo_ai_owned_case_snapshot_v1_step,
    query_zhongguo_ai_owned_case_snapshot_v1_step,
)
from .zhongguo_result_case_snapshot_contract import (
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP,
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID,
    normalize_native_zhongguo_result_case_snapshot_v1,
    normalize_zhongguo_result_case_snapshot_v1_response,
    parse_query_zhongguo_result_case_snapshot_v1_step,
    query_zhongguo_result_case_snapshot_v1_step,
)
from .zhongguo_b2_pip_snapshot_contract import (
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP,
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID,
    normalize_native_zhongguo_b2_pip_snapshot_v1,
    normalize_zhongguo_b2_pip_snapshot_v1_response,
    parse_query_zhongguo_b2_pip_snapshot_v1_step,
    query_zhongguo_b2_pip_snapshot_v1_step,
)
from .zhongguo_promotion_compensation_postcondition_contract import (
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP,
    normalize_native_zhongguo_promotion_compensation_v1,
    parse_query_zhongguo_promotion_compensation_v1_step,
    query_zhongguo_promotion_compensation_v1_step,
)
from .zhongguo_projects_metrics_postcondition_contract import (
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY,
    QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP,
    normalize_native_zhongguo_projects_metrics_v1,
    parse_query_zhongguo_projects_metrics_v1_step,
    query_zhongguo_projects_metrics_v1_step,
)
from .zhongguo_workforce_collective_snapshot_contract import (
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP,
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID,
    normalize_native_zhongguo_workforce_collective_snapshot_v1,
    normalize_zhongguo_workforce_collective_snapshot_v1_response,
    parse_query_zhongguo_workforce_collective_snapshot_v1_step,
    query_zhongguo_workforce_collective_snapshot_v1_step,
)
from .zhongguo_workforce_normal_exit_snapshot_contract import (
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1,
    normalize_native_zhongguo_workforce_normal_exit_snapshot_v1,
    normalize_zhongguo_workforce_normal_exit_snapshot_v1_response,
    parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step,
    query_zhongguo_workforce_normal_exit_snapshot_v1_step,
)
from .zhongguo_incident_snapshot_contract import (
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY,
    QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP,
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID,
    normalize_native_zhongguo_incident_snapshot_v1,
    normalize_zhongguo_incident_snapshot_v1_response,
    parse_query_zhongguo_incident_snapshot_v1_step,
    query_zhongguo_incident_snapshot_v1_step,
)
from .zhongguo_scoreboard_state_contract import (
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY,
    QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP,
    ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID,
    normalize_native_zhongguo_scoreboard_state_v1,
    parse_query_zhongguo_scoreboard_state_v1_step,
    query_zhongguo_scoreboard_state_v1_step,
)
from .zhongguo_scoreboard_action_contract import (
    ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY,
    ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP,
    ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY,
    build_zhongguo_scoreboard_action_v1_request,
    normalize_native_zhongguo_scoreboard_action_v1_result,
)
from .title_map_navigation_contract import (
    CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY,
    CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
    TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
    TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
    normalize_title_map_navigation_v1_binding,
    normalize_title_map_navigation_v1_result,
    validate_landed_title_key,
)
from .loaded_feature_manifest_contract import (
    QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
    QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
    normalize_loaded_feature_manifest_v1,
)
from .event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from .pending_character_interaction_context_contract import (
    ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
    normalize_pending_interaction_id,
    normalize_pending_character_interaction_context_v1,
)
from .active_combat_retreat_contract import (
    normalize_active_combat_retreat_v1_order_ack,
    normalize_active_combat_retreat_v1_preview,
    order_active_combat_retreat_v1_step,
    preview_active_combat_retreat_v1_step,
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
    BATTLE_DECISION_EPOCH_ADVANCE_STEP,
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
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
    parse_battle_decision_epoch_advance_step,
    parse_committed_route_sentinel_advance_step,
    parse_war_objective_hold_sentinel_advance_step,
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

    def bridge_diagnostics(self) -> dict[str, object]:
        """Return transport/private observer diagnostics without advertising capability."""
        diagnostics = getattr(self.driver, "diagnostics", None)
        if callable(diagnostics):
            value = diagnostics()
            if isinstance(value, dict):
                return value
        capabilities = self.capabilities()
        nested = capabilities.get("diagnostics")
        if isinstance(nested, dict):
            return nested
        return {
            "backend_id": capabilities.get("backend_id"),
            "connected": capabilities.get("connected"),
            "private_observers": {},
        }

    def plan_turn(self) -> dict[str, object]:
        internal_snapshot = getattr(
            self.driver, "take_internal_semantic_snapshot", None
        )
        internal_planning_view = getattr(
            self.driver, "_with_internal_planning_view", None
        )
        use_internal_view = callable(internal_snapshot) and callable(
            internal_planning_view
        )
        snapshot = (
            internal_snapshot() if use_internal_view else self.snapshot()
        )
        capabilities = self.capabilities()
        available_steps = action_step_set(capabilities)
        bridge_capabilities = (
            capabilities.get("bridge_capabilities")
            if isinstance(capabilities.get("bridge_capabilities"), list)
            else []
        )
        battle_speed_readiness = (
            capabilities.get("battle_speed_readiness")
            if isinstance(capabilities.get("battle_speed_readiness"), dict)
            else None
        )
        cross_run_plan = None
        state_dir = self._strategy_state_dir()
        if state_dir is not None:
            strategy = read_one_life_strategy(state_dir)
            if strategy.get("episodes"):
                candidate = strategy.get("next_run_plan")
                if isinstance(candidate, dict):
                    cross_run_plan = candidate

        def plan_from_view(
            planning_snapshot: dict[str, object],
            native_history: list[dict[str, object]],
        ) -> dict[str, object]:
            raw_history = planning_snapshot.get("history")
            history = (
                [row for row in raw_history if isinstance(row, dict)]
                if isinstance(raw_history, list)
                else []
            )
            history.extend(
                row for row in native_history if isinstance(row, dict)
            )
            plan = choose_one_life_turn(
                history,
                snapshot=planning_snapshot,
                action_steps=available_steps,
                bridge_capabilities=bridge_capabilities,
                next_run_plan=cross_run_plan,
                battle_speed_readiness=battle_speed_readiness,
            )
            if cross_run_plan is not None:
                plan = {**plan, "cross_run_plan_used": cross_run_plan}
            routable_steps = set(available_steps)
            selected_step = plan.get("selected_step")
            if (
                parse_query_battle_terminal_transition_v1_step(
                    selected_step
                )
                is not None
                and QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
                in bridge_capabilities
            ):
                routable_steps.add(str(selected_step))
            if (
                parse_battle_decision_epoch_advance_step(selected_step)
                is not None
                and BATTLE_DECISION_EPOCH_ADVANCE_STEP in available_steps
            ):
                routable_steps.add(str(selected_step))
            if (
                parse_committed_route_sentinel_advance_step(selected_step)
                is not None
                and COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP in available_steps
            ):
                routable_steps.add(str(selected_step))
            if (
                parse_war_objective_hold_sentinel_advance_step(selected_step)
                is not None
                and WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP
                in available_steps
            ):
                routable_steps.add(str(selected_step))
            return {
                "snapshot_id": planning_snapshot["snapshot_id"],
                "revision": planning_snapshot["revision"],
                "plan": _route_plan_to_available_step(
                    plan, routable_steps
                ),
            }

        if use_internal_view:
            return internal_planning_view(snapshot, plan_from_view)
        public_native_history = snapshot.get("native_command_history")
        return plan_from_view(
            snapshot,
            (
                public_native_history
                if isinstance(public_native_history, list)
                else []
            ),
        )

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
        planned_event = (
            plan.get("active_event") if isinstance(plan, dict) else None
        )
        planned_event_id = (
            planned_event.get("instance_id")
            if isinstance(planned_event, dict)
            else None
        )
        event_option_number = parse_event_option_step(selected_step)
        try:
            if (
                event_option_number is not None
                and isinstance(planned_event_id, int)
                and not isinstance(planned_event_id, bool)
                and 1 <= planned_event_id <= 2**31 - 1
            ):
                result = self.select_event_option(
                    event_option_number,
                    event_instance_id=planned_event_id,
                    expected_revision=int(planned["revision"]),
                )
            else:
                result = self.execute_step(
                    selected_step,
                    expected_revision=int(planned["revision"]),
                )
        except BridgeUnavailableError as error:
            # Preserve the exact planner context for every bridge failure.
            # The concrete exception type remains the sole authority on
            # whether a request was sent; plan attachment only proves which
            # step was selected, allowing a non-save failure to retain the
            # previous durable checkpoint.
            error.selected_step = selected_step
            error.plan = copy.deepcopy(plan)
            raise
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
        """Select one authored native option by its public 1-based number."""
        step = event_option_step(option_number)
        if event_instance_id is not None and (
            isinstance(event_instance_id, bool)
            or not isinstance(event_instance_id, int)
            or not 1 <= event_instance_id <= 2**31 - 1
        ):
            raise ValueError("event_instance_id must be a positive full int32")

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
        if step == CENTER_MAP_ON_LANDED_TITLE_V1_STEP:
            raise UnsupportedStepError(
                "title-map navigation requires its typed MCP facade"
            )
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

    def restore_phase2_span_source_checkpoint_v1(
        self,
        *,
        checkpoint_path: str,
        expected_checkpoint_bytes: int,
        expected_checkpoint_sha256: str,
        expected_save_lineage_id: str,
        expected_event_definition_key: str,
        expected_owner_character_id: int,
        expected_player_character_id: int,
        expected_date_raw: int,
        allow_generic_character_rebind: bool,
        allow_fixture: bool,
        allow_console: bool,
    ) -> dict[str, object]:
        """Restore one canonical Phase2 source through the managed lifecycle."""

        if not (
            allow_generic_character_rebind is False
            and allow_fixture is False
            and allow_console is False
        ):
            raise BridgeUnavailableError(
                "Phase2 source restore forbids generic rebind, fixture, and console"
            )
        restore = getattr(
            self.driver, "restore_phase2_span_source_checkpoint_v1", None
        )
        if not callable(restore):
            raise UnsupportedStepError(
                "selected backend does not implement the canonical Phase2 "
                "source-checkpoint restore"
            )
        result = restore(
            checkpoint_path=checkpoint_path,
            expected_checkpoint_bytes=expected_checkpoint_bytes,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
            expected_save_lineage_id=expected_save_lineage_id,
            expected_event_definition_key=expected_event_definition_key,
            expected_owner_character_id=expected_owner_character_id,
            expected_player_character_id=expected_player_character_id,
            expected_date_raw=expected_date_raw,
            allow_generic_character_rebind=False,
            allow_fixture=False,
            allow_console=False,
        )
        expected_sha256 = (
            expected_checkpoint_sha256.upper()
            if isinstance(expected_checkpoint_sha256, str)
            else None
        )
        lifecycle = result.get("lifecycle") if isinstance(result, dict) else None
        if not (
            isinstance(result, dict)
            and result.get("result") == "GREEN"
            and result.get("provider_observed") is True
            and result.get("restore_materialized") is True
            and result.get("checkpoint_sha256") == expected_sha256
            and result.get("checkpoint_bytes") == expected_checkpoint_bytes
            and result.get("save_lineage_id") == expected_save_lineage_id
            and result.get("event_definition_key")
            == expected_event_definition_key
            and result.get("owner_character_id")
            == expected_owner_character_id
            and result.get("player_character_id")
            == expected_player_character_id
            and result.get("date_raw") == expected_date_raw
            and result.get("fixture_used") is False
            and result.get("console_used") is False
            and result.get("generic_character_rebind_used") is False
            and isinstance(lifecycle, dict)
            and lifecycle.get("lifecycle_intent") == "restore"
            and isinstance(lifecycle.get("previous_pid"), int)
            and not isinstance(lifecycle.get("previous_pid"), bool)
            and lifecycle.get("previous_pid") > 0
            and isinstance(lifecycle.get("pid"), int)
            and not isinstance(lifecycle.get("pid"), bool)
            and lifecycle.get("pid") > 0
            and lifecycle.get("pid") != lifecycle.get("previous_pid")
            and isinstance(
                lifecycle.get("previous_connection_generation"), int
            )
            and not isinstance(
                lifecycle.get("previous_connection_generation"), bool
            )
            and lifecycle.get("previous_connection_generation") > 0
            and lifecycle.get("connection_generation")
            == lifecycle.get("previous_connection_generation") + 1
        ):
            raise BridgeUnavailableError(
                "canonical Phase2 source restore returned an incomplete typed ACK"
            )
        return result

    def phase2_span_source_checkpoint_restore_available_v1(self) -> bool:
        """Report whether this concrete backend owns the narrow restore."""

        return callable(
            getattr(
                self.driver,
                "restore_phase2_span_source_checkpoint_v1",
                None,
            )
        )

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
        if interaction_instance_id is not None:
            interaction_instance_id = normalize_pending_interaction_id(
                interaction_instance_id, "interaction_instance_id"
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

    def acknowledge_pending_character_interaction(
        self,
        *,
        interaction_instance_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Acknowledge one exact generation-bearing auto-accept notification."""
        interaction_instance_id = normalize_pending_interaction_id(
            interaction_instance_id, "interaction_instance_id"
        )
        snapshot = self.snapshot()
        pending = snapshot.get("pending_character_interaction")
        if not isinstance(pending, dict):
            raise BridgeUnavailableError(
                "CK3 has no pending character interaction"
            )
        actual_instance_id = pending.get("instance_id")
        if actual_instance_id != interaction_instance_id:
            raise BridgeUnavailableError(
                "pending character interaction instance mismatch: "
                f"expected {interaction_instance_id}, current "
                f"{actual_instance_id}"
            )
        if pending.get("auto_accept_notification") is not True:
            raise BridgeUnavailableError(
                "pending character interaction is not an ACK notification"
            )
        if (
            ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP
            not in action_step_set(self.capabilities())
        ):
            raise UnsupportedStepError(
                "selected backend does not implement gameplay step "
                f"{ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP}"
            )
        result = self.execute_step(
            ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
            expected_revision=(
                expected_revision
                if expected_revision is not None
                else int(snapshot["revision"])
            ),
        )
        interaction_result = result.get("interaction_result")
        if (
            not isinstance(interaction_result, dict)
            or interaction_result.get("status") != "acknowledged"
            or interaction_result.get("instance_id")
            != interaction_instance_id
        ):
            raise BridgeUnavailableError(
                "native ACK did not prove pending interaction advancement"
            )
        return {
            **result,
            "interaction_instance_id": interaction_instance_id,
            "sender_character_id": pending.get("sender_character_id"),
            "acknowledged": True,
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

    def query_campaign_root_context_v1(
        self,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read the exact-build local-player campaign root while paused."""
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "campaign-root queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise BridgeUnavailableError(
                "campaign-root query lacks a valid snapshot revision"
            )
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
                "campaign-root revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "campaign-root query lacks a positive native revision"
            )
        date_raw = snapshot.get("date_raw")
        if (
            isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "campaign-root query lacks a signed int32 date"
            )
        snapshot_id = snapshot.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "campaign-root query lacks a snapshot identity"
            )
        snapshot_backend_id = snapshot.get("backend_id")
        if not isinstance(snapshot_backend_id, str) or not snapshot_backend_id:
            raise BridgeUnavailableError(
                "campaign-root query lacks a source backend identity"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY
            in bridge_capabilities
            and QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
            in action_step_set(capabilities)
        ):
            raise UnsupportedStepError(
                "selected backend cannot query the campaign root context"
            )
        result = self.execute_step(
            QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            expected_revision=expected_revision,
        )
        mirror_keys = {
            "schema_version",
            "date_raw",
            "local_player_id",
            "player_character_id",
            "player_character_alive",
            "primary_title",
            "capital_province_id",
            "immediate_liege_character_id",
            "top_liege_character_id",
            "independent",
            "government",
            "selected_game_rule_tokens",
            "native_selected_game_rule_token_count",
            "readiness",
            "unavailable_reason",
            "provenance",
        }
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "campaign_root_context",
            "backend_id",
            "campaign_root_context_ready",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            *mirror_keys,
        }
        if (
            not isinstance(result, dict)
            or set(result) != required_result_keys
            or result.get("step") != QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "campaign-root backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "campaign-root result lacks query_sequence"
            )
        backend_id = result.get("backend_id")
        if not isinstance(backend_id, str) or not backend_id:
            raise BridgeUnavailableError(
                "campaign-root result lacks backend_id"
            )
        try:
            normalized = normalize_campaign_root_context_v1(
                result.get("campaign_root_context"),
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"campaign-root result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "campaign-root envelope status disagrees with its frame"
            )
        expected_mirrors = {
            key: copy.deepcopy(normalized[key]) for key in mirror_keys
        }
        if any(
            result.get(key) != expected
            for key, expected in expected_mirrors.items()
        ) or result.get("campaign_root_context_ready") is not normalized[
            "readiness"
        ]["ready"]:
            raise BridgeUnavailableError(
                "campaign-root result mirrors disagree with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "campaign-root result is bound to another snapshot"
            )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        provenance = normalized["provenance"]
        assert isinstance(provenance, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get(
                "expected_ck3_sha256", hello.get("executable_sha256")
            )
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
        ):
            raise BridgeUnavailableError(
                "campaign-root build mirror disagrees with bridge hello"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot_id
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "campaign-root query crossed a snapshot revision"
            )
        build = {
            "version": provenance["game_version"],
            "exe_sha256": provenance["executable_sha256"],
        }
        source = {
            "game_version": observed_version,
            "executable_sha256": observed_sha256.upper(),
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "paused": True,
            "backend_id": snapshot_backend_id,
        }
        binding = {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "expected_revision": expected_revision,
        }
        return {
            **result,
            "schema_version": 1,
            "status": normalized["status"],
            "scope": "exact-campaign-root-context",
            "build": build,
            "source": source,
            "binding": binding,
            **expected_mirrors,
            "campaign_root_context_ready": normalized["readiness"][
                "ready"
            ],
            "campaign_root_context": normalized,
        }

    def query_zhongguo_case_snapshot_v1(
        self,
        case_kind: str,
        request_nonce: str,
        *,
        expected_revision: int,
        subject_character_id: int | None = None,
        owner_character_id: int | None = None,
    ) -> dict[str, object]:
        """Read one allowlisted ZhongGuo case from one paused exact frame."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError(
                "expected_revision must be a non-negative uint64"
            )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo case queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or not 0 <= revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case query lacks a valid public revision"
            )
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "ZhongGuo case revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case query lacks a stable native snapshot binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case query lacks the played character identity"
            )
        selected_subject_character_id = (
            player_character_id
            if subject_character_id is None
            else subject_character_id
        )
        step = query_zhongguo_case_snapshot_v1_step(
            case_kind,
            selected_subject_character_id,
            owner_character_id,
            request_nonce,
        )
        query = parse_query_zhongguo_case_snapshot_v1_step(step)
        assert query is not None
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version")
                if isinstance(hello, dict)
                else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id")
            if isinstance(hello, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case query lacks its bridge connection binding"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query allowlisted ZhongGuo cases"
            )
        result = self.execute_step(
            step,
            expected_revision=expected_revision,
        )
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_case_snapshot",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step")
            != QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case result lacks its native query identity"
            )
        try:
            normalized = normalize_native_zhongguo_case_snapshot_v1(
                result.get("zhongguo_case_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo case result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo case envelope status disagrees with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case result is bound to another snapshot"
            )
        provenance = normalized["provenance"]
        assert isinstance(provenance, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get(
                "expected_ck3_sha256", hello.get("executable_sha256")
            )
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case build mirror disagrees with bridge hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo case query crossed its paused snapshot binding"
            )
        actual_owner_character_id: int | None = None
        if normalized["status"] == "available":
            case = normalized["case"]
            assert isinstance(case, dict)
            owner = case["owner_character_id"]
            assert isinstance(owner, dict)
            if owner.get("status") != "available":
                raise BridgeUnavailableError(
                    "available ZhongGuo case lacks its owner identity"
                )
            owner_value = owner.get("value")
            if (
                isinstance(owner_value, bool)
                or not isinstance(owner_value, int)
                or not 1 <= owner_value <= 2**31 - 1
            ):
                raise BridgeUnavailableError(
                    "available ZhongGuo case has an invalid owner identity"
                )
            actual_owner_character_id = owner_value
        response = {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": query.subject_character_id,
                "owner_character_id": actual_owner_character_id,
                "expected_revision": expected_revision,
            },
        }
        try:
            return normalize_zhongguo_case_snapshot_v1_response(
                response,
                expected_query=query,
                expected_snapshot_id=snapshot_id,
                expected_revision=revision,
                expected_native_revision=native_revision,
                expected_connection_generation=connection_generation,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo case response projection is malformed: {error}"
            ) from error

    def query_zhongguo_ai_owned_case_snapshot_v1(
        self,
        owner_character_id: int,
        subject_character_id: int,
        request_nonce: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read one AI manager's B1 case from one paused exact frame."""
        if expected_revision is not None and (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError(
                "expected_revision must be None or a non-negative uint64"
            )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or not 0 <= revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case query lacks a valid public revision"
            )
        selected_revision = (
            revision if expected_revision is None else expected_revision
        )
        if selected_revision != revision:
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case revision mismatch: expected "
                f"{selected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case query lacks a stable native snapshot "
                "binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case query lacks the played character "
                "identity"
            )
        step = query_zhongguo_ai_owned_case_snapshot_v1_step(
            owner_character_id,
            subject_character_id,
            request_nonce,
        )
        query = parse_query_zhongguo_ai_owned_case_snapshot_v1_step(step)
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError("AI-owned case query builder violated v1")
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version")
                if isinstance(hello, dict)
                else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id")
            if isinstance(hello, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case query lacks its bridge connection "
                "binding"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query AI-owned ZhongGuo cases"
            )
        result = self.execute_step(
            step,
            expected_revision=selected_revision,
        )
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_ai_owned_case_snapshot",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step")
            != QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case result lacks its native query identity"
            )
        try:
            normalized = normalize_native_zhongguo_ai_owned_case_snapshot_v1(
                result.get("zhongguo_ai_owned_case_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo AI-owned case result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case envelope status disagrees with its "
                "frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case result is bound to another snapshot"
            )
        provenance = normalized.get("provenance")
        if not isinstance(provenance, dict):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case lacks exact-build provenance"
            )
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case build mirror disagrees with bridge "
                "hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case query crossed its paused snapshot "
                "binding"
            )
        response = {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "owner_character_id": query.owner_character_id,
                "subject_character_id": query.subject_character_id,
                "expected_revision": selected_revision,
            },
        }
        try:
            return normalize_zhongguo_ai_owned_case_snapshot_v1_response(
                response,
                expected_query=query,
                expected_snapshot_id=snapshot_id,
                expected_revision=revision,
                expected_native_revision=native_revision,
                expected_connection_generation=connection_generation,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo AI-owned case response projection is malformed: "
                f"{error}"
            ) from error

    def query_zhongguo_result_case_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the paused player's received result from one expected owner."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError(
                "expected_revision must be a non-negative uint64"
            )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo result-case queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or not 0 <= revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case query lacks a valid public revision"
            )
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "ZhongGuo result-case revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case query lacks a stable native snapshot "
                "binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case query lacks the played character "
                "identity"
            )
        step = query_zhongguo_result_case_snapshot_v1_step(
            owner_character_id,
            request_nonce,
        )
        query = parse_query_zhongguo_result_case_snapshot_v1_step(step)
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError("result-case query builder violated v1")
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version")
                if isinstance(hello, dict)
                else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id")
            if isinstance(hello, dict)
            else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case query lacks its bridge connection "
                "binding"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query received-self ZhongGuo "
                "result cases"
            )
        result = self.execute_step(
            step,
            expected_revision=expected_revision,
        )
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_result_case_snapshot",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step")
            != QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case result lacks its native query identity"
            )
        try:
            normalized = normalize_native_zhongguo_result_case_snapshot_v1(
                result.get("zhongguo_result_case_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo result-case result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo result-case envelope status disagrees with its "
                "frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case result is bound to another snapshot"
            )
        provenance = normalized["provenance"]
        assert isinstance(provenance, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get(
                "expected_ck3_sha256", hello.get("executable_sha256")
            )
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case build mirror disagrees with bridge hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo result-case query crossed its paused snapshot "
                "binding"
            )
        actual_owner_character_id: int | None = None
        if normalized["status"] == "available":
            case = normalized["case"]
            assert isinstance(case, dict)
            owner = case["owner_character_id"]
            assert isinstance(owner, dict)
            owner_value = owner.get("value")
            if (
                owner.get("status") != "available"
                or isinstance(owner_value, bool)
                or not isinstance(owner_value, int)
                or not 1 <= owner_value <= 2**31 - 1
            ):
                raise BridgeUnavailableError(
                    "available ZhongGuo result-case lacks its owner identity"
                )
            actual_owner_character_id = owner_value
        response = {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": player_character_id,
                "owner_character_id": actual_owner_character_id,
                "expected_revision": expected_revision,
            },
        }
        try:
            return normalize_zhongguo_result_case_snapshot_v1_response(
                response,
                expected_query=query,
                expected_snapshot_id=snapshot_id,
                expected_revision=revision,
                expected_native_revision=native_revision,
                expected_connection_generation=connection_generation,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo result-case response projection is malformed: "
                f"{error}"
            ) from error

    def query_zhongguo_b2_pip_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the paused player's strict received-self B2 PIP projection."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError("expected_revision must be a non-negative uint64")
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or not 0 <= revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP query lacks a valid public revision"
            )
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP query lacks a stable native snapshot binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP query lacks the played character identity"
            )
        step = query_zhongguo_b2_pip_snapshot_v1_step(
            owner_character_id, request_nonce
        )
        query = parse_query_zhongguo_b2_pip_snapshot_v1_step(step)
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError("B2 PIP query builder violated v1")
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version") if isinstance(hello, dict) else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id") if isinstance(hello, dict) else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP query lacks its bridge connection binding"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query received-self ZhongGuo B2 PIP"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_b2_pip_snapshot",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step") != QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP result lacks its native query identity"
            )
        try:
            normalized = normalize_native_zhongguo_b2_pip_snapshot_v1(
                result.get("zhongguo_b2_pip_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo B2 PIP result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP envelope status disagrees with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP result is bound to another snapshot"
            )
        provenance = normalized["provenance"]
        assert isinstance(provenance, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP build mirror disagrees with bridge hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id") == snapshot.get("episode_run_id")
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP query crossed its paused snapshot binding"
            )
        actual_owner_character_id: int | None = None
        if normalized["status"] == "available":
            gate = normalized["gate"]
            assert isinstance(gate, dict)
            owner = gate["owner_character_id"]
            assert isinstance(owner, dict)
            owner_value = owner.get("value")
            if (
                owner.get("status") != "available"
                or isinstance(owner_value, bool)
                or not isinstance(owner_value, int)
                or not 1 <= owner_value <= 2**31 - 1
            ):
                raise BridgeUnavailableError(
                    "available ZhongGuo B2 PIP lacks its owner identity"
                )
            actual_owner_character_id = owner_value
        response = {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": player_character_id,
                "owner_character_id": actual_owner_character_id,
                "expected_revision": expected_revision,
            },
        }
        try:
            return normalize_zhongguo_b2_pip_snapshot_v1_response(
                response,
                expected_query=query,
                expected_snapshot_id=snapshot_id,
                expected_revision=revision,
                expected_native_revision=native_revision,
                expected_connection_generation=connection_generation,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo B2 PIP response projection is malformed: "
                f"{error}"
            ) from error

    def query_zhongguo_promotion_compensation_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read the paused player's correlated promotion/compensation receipt."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError("expected_revision must be a non-negative uint64")
        snapshot = self.snapshot()
        revision = snapshot.get("revision")
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        played = snapshot.get("played_character")
        player_character_id = (
            played.get("character_id") if isinstance(played, dict) else None
        )
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        hello = (
            diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        )
        if (
            snapshot.get("paused") is not True
            or revision != expected_revision
            or isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
            or isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo promotion/compensation query lacks one stable "
                "paused player binding"
            )
        step = query_zhongguo_promotion_compensation_v1_step(
            player_character_id, request_nonce
        )
        query = parse_query_zhongguo_promotion_compensation_v1_step(step)
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError(
                "promotion/compensation query builder violated v1"
            )
        capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(capabilities, list)
            and QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
            in capabilities
        ):
            raise UnsupportedStepError(
                "selected backend does not advertise the ZhongGuo "
                "promotion/compensation postcondition query"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        expected_keys = {
            "step", "accepted", "status", "query_sequence",
            "snapshot_revision", "zhongguo_promotion_compensation_postcondition",
            "backend_id", "queried_snapshot_id", "queried_revision",
            "queried_native_revision", "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
            or result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo promotion/compensation backend result is not bound "
                "to the requested paused frame"
            )
        try:
            normalized = normalize_native_zhongguo_promotion_compensation_v1(
                result.get(
                    "zhongguo_promotion_compensation_postcondition"
                ),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo promotion/compensation result is malformed: "
                f"{error}"
            ) from error
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played = current.get("played_character")
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and isinstance(current_played, dict)
            and current_played.get("character_id") == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo promotion/compensation query crossed its paused "
                "snapshot binding"
            )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version") if isinstance(hello, dict) else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id") if isinstance(hello, dict) else None
        )
        return {
            **normalized,
            "source_backend_id": "native-headless",
            "build": {
                "version": "1.19.0.6",
                "exe_sha256": (
                    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
                ),
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": result.get("backend_id"),
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": normalized["subject_character_id"],
                "owner_character_id": player_character_id,
                "expected_revision": expected_revision,
            },
        }

    def query_zhongguo_projects_metrics_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the paused player's correlated projects/metrics receipt."""
        if (
            isinstance(owner_character_id, bool)
            or not isinstance(owner_character_id, int)
            or not 1 <= owner_character_id <= 2**31 - 1
        ):
            raise ValueError("owner_character_id must be a positive int32")
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError("expected_revision must be a non-negative uint64")
        snapshot = self.snapshot()
        revision = snapshot.get("revision")
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        played = snapshot.get("played_character")
        player_character_id = (
            played.get("character_id") if isinstance(played, dict) else None
        )
        diagnostics = snapshot.get("diagnostics")
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        hello = (
            diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        )
        if (
            snapshot.get("paused") is not True
            or revision != expected_revision
            or isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
            or isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo projects/metrics query lacks one stable "
                "paused player binding"
            )
        step = query_zhongguo_projects_metrics_v1_step(
            owner_character_id, request_nonce
        )
        query = parse_query_zhongguo_projects_metrics_v1_step(step)
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError(
                "projects/metrics query builder violated v1"
            )
        capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(capabilities, list)
            and QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
            in capabilities
        ):
            raise UnsupportedStepError(
                "selected backend does not advertise the ZhongGuo "
                "projects/metrics postcondition query"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        expected_keys = {
            "step", "accepted", "status", "query_sequence",
            "snapshot_revision", "zhongguo_projects_metrics_postcondition",
            "backend_id", "queried_snapshot_id", "queried_revision",
            "queried_native_revision", "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_keys
            or result.get("step")
            != QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
            or result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo projects/metrics backend result is not bound "
                "to the requested paused frame"
            )
        try:
            normalized = normalize_native_zhongguo_projects_metrics_v1(
                result.get(
                    "zhongguo_projects_metrics_postcondition"
                ),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo projects/metrics result is malformed: "
                f"{error}"
            ) from error
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played = current.get("played_character")
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and isinstance(current_played, dict)
            and current_played.get("character_id") == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo projects/metrics query crossed its paused "
                "snapshot binding"
            )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version") if isinstance(hello, dict) else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id") if isinstance(hello, dict) else None
        )
        return {
            **normalized,
            "source_backend_id": "native-headless",
            "build": {
                "version": "1.19.0.6",
                "exe_sha256": (
                    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
                ),
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": result.get("backend_id"),
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": player_character_id,
                "owner_character_id": owner_character_id,
                "expected_revision": expected_revision,
            },
        }

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the player's received Workforce collective and owner ledger."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError("expected_revision must be a non-negative uint64")
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective queries require a paused CK3 "
                "snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or not 0 <= revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective query lacks a valid public "
                "revision"
            )
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective query lacks a stable native "
                "snapshot binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective query lacks the played "
                "character identity"
            )
        step = query_zhongguo_workforce_collective_snapshot_v1_step(
            owner_character_id, request_nonce
        )
        query = parse_query_zhongguo_workforce_collective_snapshot_v1_step(
            step
        )
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError("Workforce collective query builder violated v1")
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version") if isinstance(hello, dict) else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id") if isinstance(hello, dict) else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective query lacks its bridge "
                "connection binding"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query received-self ZhongGuo "
                "Workforce collective state"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_workforce_collective_snapshot",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step")
            != QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective backend returned a malformed "
                "result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective result lacks its native query "
                "identity"
            )
        try:
            normalized = (
                normalize_native_zhongguo_workforce_collective_snapshot_v1(
                    result.get("zhongguo_workforce_collective_snapshot"),
                    expected_query=query,
                    expected_snapshot_revision=native_revision,
                    expected_date_raw=date_raw,
                    expected_player_character_id=player_character_id,
                )
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo Workforce collective result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective envelope status disagrees "
                "with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective result is bound to another "
                "snapshot"
            )
        provenance = normalized["provenance"]
        assert isinstance(provenance, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective build mirror disagrees with "
                "bridge hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id") == snapshot.get("episode_run_id")
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective query crossed its paused "
                "snapshot binding"
            )
        actual_owner_character_id = (
            query.owner_character_id
            if normalized["status"] == "available"
            else None
        )
        response = {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": player_character_id,
                "owner_character_id": actual_owner_character_id,
                "expected_revision": expected_revision,
            },
        }
        try:
            return normalize_zhongguo_workforce_collective_snapshot_v1_response(
                response,
                expected_query=query,
                expected_snapshot_id=snapshot_id,
                expected_revision=revision,
                expected_native_revision=native_revision,
                expected_connection_generation=connection_generation,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce collective response projection is "
                f"malformed: {error}"
            ) from error

    def query_zhongguo_workforce_normal_exit_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        """Read the player's received Workforce normal-exit/HC lifecycle."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError("expected_revision must be a non-negative uint64")
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit queries require a paused "
                "CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or not 0 <= revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit query lacks a valid public "
                "revision"
            )
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit query lacks a stable native "
                "snapshot binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit query lacks the played "
                "character identity"
            )
        step = query_zhongguo_workforce_normal_exit_snapshot_v1_step(
            owner_character_id, request_nonce
        )
        query = parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step(
            step
        )
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError("Workforce normal-exit query builder violated v1")
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version") if isinstance(hello, dict) else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id") if isinstance(hello, dict) else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit query lacks its bridge "
                "connection binding"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query received-self ZhongGuo "
                "Workforce normal-exit state"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_workforce_normal_exit_snapshot",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step")
            != QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit backend returned a malformed "
                "result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit result lacks its native "
                "query identity"
            )
        try:
            normalized = (
                normalize_native_zhongguo_workforce_normal_exit_snapshot_v1(
                    result.get("zhongguo_workforce_normal_exit_snapshot"),
                    expected_query=query,
                    expected_snapshot_revision=native_revision,
                    expected_date_raw=date_raw,
                    expected_player_character_id=player_character_id,
                )
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo Workforce normal-exit result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit envelope status disagrees "
                "with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit result is bound to another "
                "snapshot"
            )
        provenance = normalized.get("provenance")
        if not isinstance(provenance, dict):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit result lacks provenance"
            )
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance.get("game_version")
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance.get("executable_sha256")).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit build mirror disagrees with "
                "bridge hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id") == snapshot.get("episode_run_id")
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit query crossed its paused "
                "snapshot binding"
            )
        response = {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "bridge_source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": player_character_id,
                "owner_character_id": query.owner_character_id,
                "expected_revision": expected_revision,
            },
        }
        try:
            return normalize_zhongguo_workforce_normal_exit_snapshot_v1_response(
                response,
                expected_query=query,
                expected_snapshot_id=snapshot_id,
                expected_revision=revision,
                expected_native_revision=native_revision,
                expected_connection_generation=connection_generation,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo Workforce normal-exit response projection is "
                f"malformed: {error}"
            ) from error

    def query_zhongguo_incident_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
        profile: str,
    ) -> dict[str, object]:
        """Read one paused fixed-profile incident projection for the player."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError("expected_revision must be a non-negative uint64")
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo incident queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or not 0 <= revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident query lacks a valid public revision"
            )
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "ZhongGuo incident revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident query lacks a stable native snapshot binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident query lacks the played character identity"
            )
        step = query_zhongguo_incident_snapshot_v1_step(
            owner_character_id, profile, request_nonce
        )
        query = parse_query_zhongguo_incident_snapshot_v1_step(step)
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError("incident query builder violated v1")
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version") if isinstance(hello, dict) else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id") if isinstance(hello, dict) else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident query lacks its bridge connection binding"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query received-self ZhongGuo incidents"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_incident_snapshot",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step")
            != QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident result lacks its native query identity"
            )
        try:
            normalized = normalize_native_zhongguo_incident_snapshot_v1(
                result.get("zhongguo_incident_snapshot"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo incident result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo incident envelope status disagrees with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
            or result.get("queried_connection_generation")
            != connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident result is bound to another snapshot"
            )
        provenance = normalized["provenance"]
        assert isinstance(provenance, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident build mirror disagrees with bridge hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id") == snapshot.get("episode_run_id")
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo incident query crossed its paused snapshot binding"
            )
        actual_owner_character_id: int | None = None
        if normalized["status"] == "available":
            probe = normalized["probe"]
            assert isinstance(probe, dict)
            owner = probe["owner_character_id"]
            assert isinstance(owner, dict)
            owner_value = owner.get("value")
            if (
                owner.get("status") != "available"
                or isinstance(owner_value, bool)
                or not isinstance(owner_value, int)
                or not 1 <= owner_value <= 2**31 - 1
            ):
                raise BridgeUnavailableError(
                    "available ZhongGuo incident lacks its owner identity"
                )
            actual_owner_character_id = owner_value
        response = {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "profile": query.profile,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "subject_character_id": player_character_id,
                "owner_character_id": actual_owner_character_id,
                "expected_revision": expected_revision,
            },
        }
        try:
            return normalize_zhongguo_incident_snapshot_v1_response(
                response,
                expected_query=query,
                expected_snapshot_id=snapshot_id,
                expected_revision=revision,
                expected_native_revision=native_revision,
                expected_connection_generation=connection_generation,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                "ZhongGuo incident response projection is malformed: "
                f"{error}"
            ) from error

    def query_zhongguo_scoreboard_state_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read fixed scoreboard instances and current-player frozen ACL."""
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or not 0 <= expected_revision <= 2**64 - 1
        ):
            raise ValueError("expected_revision must be a non-negative uint64")
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision != expected_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard revision mismatch"
            )
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard query lacks a stable native binding"
            )
        played_character = snapshot.get("played_character")
        player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        if (
            isinstance(player_character_id, bool)
            or not isinstance(player_character_id, int)
            or not 1 <= player_character_id <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard query lacks the played character"
            )
        step = query_zhongguo_scoreboard_state_v1_step(request_nonce)
        query = parse_query_zhongguo_scoreboard_state_v1_step(step)
        if query is None:  # pragma: no cover - builder/parser invariant
            raise AssertionError("scoreboard query builder violated v1")
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        )
        connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        bridge_version = (
            diagnostics.get("bridge_version")
            if isinstance(diagnostics, dict)
            else None
        )
        if not isinstance(bridge_version, str) or not bridge_version:
            bridge_version = (
                hello.get("bridge_version")
                if isinstance(hello, dict)
                else None
            )
        game_adapter_id = (
            hello.get("game_adapter_id") if isinstance(hello, dict) else None
        )
        if (
            isinstance(connection_generation, bool)
            or not isinstance(connection_generation, int)
            or not 1 <= connection_generation <= 2**64 - 1
            or not isinstance(bridge_version, str)
            or not bridge_version
            or not isinstance(game_adapter_id, str)
            or not game_adapter_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard query lacks its bridge binding"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query ZhongGuo scoreboard state"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "zhongguo_scoreboard_state",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if (
            not isinstance(result, dict)
            or set(result) != expected_result_keys
            or result.get("step")
            != QUERY_ZHONGGUO_SCOREBOARD_STATE_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        backend_id = result.get("backend_id")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
            or not isinstance(backend_id, str)
            or not backend_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard result lacks its native query identity"
            )
        try:
            normalized = normalize_native_zhongguo_scoreboard_state_v1(
                result.get("zhongguo_scoreboard_state"),
                expected_query=query,
                expected_snapshot_revision=native_revision,
                expected_date_raw=date_raw,
                expected_player_character_id=player_character_id,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo scoreboard result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard envelope status disagrees with frame"
            )
        provenance = normalized["provenance"]
        assert isinstance(provenance, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != provenance["game_version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(provenance["executable_sha256"]).upper()
            or provenance.get("consumer_id")
            != ZHONGGUO_SCOREBOARD_STATE_V1_CONSUMER_ID
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard build mirror disagrees with hello"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        current_player_character_id = (
            current_played_character.get("character_id")
            if isinstance(current_played_character, dict)
            else None
        )
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot_id
            and current.get("revision") == revision
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current_player_character_id == player_character_id
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == connection_generation
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard query crossed its paused binding"
            )
        return {
            **normalized,
            "build": {
                "version": provenance["game_version"],
                "exe_sha256": provenance["executable_sha256"],
            },
            "source": {
                "bridge_version": bridge_version,
                "game_adapter_id": game_adapter_id,
                "backend_id": backend_id,
                "consumer_id": provenance["consumer_id"],
                "connection_generation": connection_generation,
                "query_sequence": query_sequence,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
            },
            "binding": {
                "request_nonce": query.request_nonce,
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "connection_generation": connection_generation,
                "date_raw": date_raw,
                "paused": True,
                "player_character_id": player_character_id,
                "expected_revision": expected_revision,
            },
        }

    def activate_zhongguo_scoreboard_v1(
        self,
        request_nonce: str,
        action: str,
        *,
        expected_revision: int,
        expected_native_revision: int,
        expected_connection_generation: int,
        expected_player_character_id: int,
        expected_provider_session_id: str,
        expected_observation_sequence: int,
        expected_observed_state_revision: int,
        expected_tree_fingerprint_v1: str,
        expected_semantic_fingerprint_v1: str,
        expected_window_instance_pointer: str,
        expected_target_instance_pointer: str,
        expected_target_vtable_pointer: str,
    ) -> dict[str, object]:
        """Cross the typed scoreboard action transport without promotion.

        The exact dispatcher returns an ACK only. Production capability stays
        unadvertised until a paused live run proves the independent
        provider-owned observation transition and explicit postcondition.
        """

        request = build_zhongguo_scoreboard_action_v1_request(
            request_nonce=request_nonce,
            action=action,
            expected_revision=expected_revision,
            expected_native_revision=expected_native_revision,
            expected_connection_generation=expected_connection_generation,
            expected_player_character_id=expected_player_character_id,
            expected_provider_session_id=expected_provider_session_id,
            expected_observation_sequence=expected_observation_sequence,
            expected_observed_state_revision=(
                expected_observed_state_revision
            ),
            expected_tree_fingerprint_v1=expected_tree_fingerprint_v1,
            expected_semantic_fingerprint_v1=(
                expected_semantic_fingerprint_v1
            ),
            expected_window_instance_pointer=expected_window_instance_pointer,
            expected_target_instance_pointer=expected_target_instance_pointer,
            expected_target_vtable_pointer=expected_target_vtable_pointer,
        )
        snapshot = self.snapshot()
        diagnostics = snapshot.get("diagnostics")
        played_character = snapshot.get("played_character")
        actual_player_character_id = (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        actual_connection_generation = (
            diagnostics.get("connection_generation")
            if isinstance(diagnostics, dict)
            else None
        )
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard actions require a paused snapshot"
            )
        if not (
            snapshot.get("revision") == expected_revision
            and snapshot.get("native_revision") == expected_native_revision
            and actual_connection_generation
            == expected_connection_generation
            and actual_player_character_id == expected_player_character_id
        ):
            raise PreSubmissionRevisionMismatchError(
                "ZhongGuo scoreboard action source binding is stale"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend lacks the fail-closed ZhongGuo scoreboard "
                "action transport"
            )
        executor = getattr(
            self.driver, "activate_zhongguo_scoreboard_v1", None
        )
        if not callable(executor):
            raise UnsupportedStepError(
                "selected backend has no typed ZhongGuo scoreboard action "
                "executor"
            )
        result = executor(request, expected_revision=expected_revision)
        expected_result_keys = {
            "step",
            "accepted",
            "status",
            "request_nonce",
            "action",
            "action_sequence",
            "snapshot_revision",
            "rejection_reason",
            "action_ack",
            "production_capability_advertised",
            "backend_id",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            "queried_connection_generation",
        }
        if not isinstance(result, dict) or set(result) != expected_result_keys:
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard action backend returned unexpected fields"
            )
        try:
            normalized = normalize_native_zhongguo_scoreboard_action_v1_result(
                {
                    key: result[key]
                    for key in (
                        "step",
                        "accepted",
                        "status",
                        "request_nonce",
                        "action",
                        "action_sequence",
                        "snapshot_revision",
                        "rejection_reason",
                        "action_ack",
                        "production_capability_advertised",
                        "backend_id",
                    )
                },
                expected_request=request,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"ZhongGuo scoreboard action result is malformed: {error}"
            ) from error
        if not (
            normalized["step"] == ACTIVATE_ZHONGGUO_SCOREBOARD_V1_STEP
            and result["queried_snapshot_id"] == snapshot.get("snapshot_id")
            and result["queried_revision"] == expected_revision
            and result["queried_native_revision"]
            == expected_native_revision
            and result["queried_connection_generation"]
            == expected_connection_generation
            and normalized["snapshot_revision"]
            == expected_native_revision
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard action result crossed its source binding"
            )
        advertised_by_capability = (
            isinstance(bridge_capabilities, list)
            and ACTIVATE_ZHONGGUO_SCOREBOARD_V1_CAPABILITY
            in bridge_capabilities
        )
        if (
            normalized["production_capability_advertised"]
            is not advertised_by_capability
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard production capability mirror drifted"
            )
        current = self.snapshot()
        current_diagnostics = current.get("diagnostics")
        current_played_character = current.get("played_character")
        if not (
            current.get("paused") is True
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("revision") == expected_revision
            and current.get("native_revision") == expected_native_revision
            and isinstance(current_diagnostics, dict)
            and current_diagnostics.get("connection_generation")
            == expected_connection_generation
            and isinstance(current_played_character, dict)
            and current_played_character.get("character_id")
            == expected_player_character_id
        ):
            raise BridgeUnavailableError(
                "ZhongGuo scoreboard action crossed its paused binding"
            )
        return {
            **normalized,
            "queried_snapshot_id": result["queried_snapshot_id"],
            "queried_revision": result["queried_revision"],
            "queried_native_revision": result["queried_native_revision"],
            "queried_connection_generation": result[
                "queried_connection_generation"
            ],
        }

    def center_map_on_landed_title_v1(
        self,
        title_key: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Center the native map without exposing the step to the planner."""
        key = validate_landed_title_key(title_key)
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or expected_revision < 0
            or expected_revision > 2**64 - 1
        ):
            raise ValueError(
                "expected_revision must be a non-negative uint64"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        typed_command = getattr(
            self.driver, "center_map_on_landed_title_v1", None
        )
        if not (
            isinstance(bridge_capabilities, list)
            and CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
            in bridge_capabilities
            and callable(typed_command)
        ):
            raise UnsupportedStepError(
                "capability_not_available: selected backend cannot center "
                "the map on a landed title"
            )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "title-map navigation requires a paused CK3 snapshot"
            )
        if snapshot.get("map_ready") is not True:
            raise BridgeUnavailableError(
                "title-map navigation requires a map-ready CK3 snapshot"
            )
        try:
            binding = _title_map_navigation_binding(snapshot)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"title-map navigation lacks a complete binding: {error}"
            ) from error
        if binding["revision"] != expected_revision:
            raise BridgeUnavailableError(
                "title-map navigation revision mismatch: expected "
                f"{expected_revision}, current {binding['revision']}"
            )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get(
                "expected_ck3_sha256", hello.get("executable_sha256")
            )
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != TITLE_MAP_NAVIGATION_V1_GAME_VERSION
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
        ):
            raise BridgeUnavailableError(
                "title-map navigation build mirror disagrees with bridge hello"
            )
        result = typed_command(key, expected_revision=expected_revision)
        try:
            normalized = normalize_title_map_navigation_v1_result(
                result,
                expected_title_key=key,
                expected_binding=binding,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"title-map navigation result is malformed: {error}"
            ) from error
        current = self.snapshot()
        try:
            current_binding = _title_map_navigation_binding(current)
        except ValueError as error:
            raise BridgeUnavailableError(
                f"title-map navigation lost its session binding: {error}"
            ) from error
        if not (
            current.get("paused") is True
            and current.get("map_ready") is True
            and current_binding == binding
            and current.get("played_character")
            == snapshot.get("played_character")
        ):
            raise BridgeUnavailableError(
                "title-map navigation crossed its paused session binding"
            )
        return normalized

    def query_loaded_feature_manifest_v1(
        self,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read exact-build effective flags and script DLC keys while paused."""
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "loaded-feature queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise BridgeUnavailableError(
                "loaded-feature query lacks a valid snapshot revision"
            )
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
                "loaded-feature revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "loaded-feature query lacks a positive native revision"
            )
        date_raw = snapshot.get("date_raw")
        if (
            isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "loaded-feature query lacks a signed int32 date"
            )
        snapshot_id = snapshot.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "loaded-feature query lacks a snapshot identity"
            )
        snapshot_backend_id = snapshot.get("backend_id")
        if not isinstance(snapshot_backend_id, str) or not snapshot_backend_id:
            raise BridgeUnavailableError(
                "loaded-feature query lacks a source backend identity"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
            in bridge_capabilities
            and QUERY_LOADED_FEATURE_MANIFEST_V1_STEP
            in action_step_set(capabilities)
        ):
            raise UnsupportedStepError(
                "selected backend cannot query the loaded feature manifest"
            )
        result = self.execute_step(
            QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
            expected_revision=expected_revision,
        )
        mirror_keys = {
            "schema",
            "schema_version",
            "date_raw",
            "unavailable_reason",
            "build",
            "effective_feature_flags",
            "script_dlc_keys",
            "entitlements",
            "readiness",
            "provenance",
        }
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "loaded_feature_manifest",
            "backend_id",
            "loaded_feature_manifest_ready",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            *mirror_keys,
        }
        if (
            not isinstance(result, dict)
            or set(result) != required_result_keys
            or result.get("step") != QUERY_LOADED_FEATURE_MANIFEST_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "loaded-feature backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "loaded-feature result lacks query_sequence"
            )
        backend_id = result.get("backend_id")
        if not isinstance(backend_id, str) or not backend_id:
            raise BridgeUnavailableError(
                "loaded-feature result lacks backend_id"
            )
        try:
            normalized = normalize_loaded_feature_manifest_v1(
                result.get("loaded_feature_manifest"),
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"loaded-feature result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "loaded-feature envelope status disagrees with its frame"
            )
        expected_mirrors = {
            key: copy.deepcopy(normalized[key]) for key in mirror_keys
        }
        if any(
            result.get(key) != expected
            for key, expected in expected_mirrors.items()
        ) or result.get("loaded_feature_manifest_ready") is not normalized[
            "readiness"
        ]["actionable_ready"]:
            raise BridgeUnavailableError(
                "loaded-feature result mirrors disagree with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "loaded-feature result is bound to another snapshot"
            )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        build = normalized["build"]
        assert isinstance(build, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get(
                "expected_ck3_sha256", hello.get("executable_sha256")
            )
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != build["version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(build["exe_sha256"]).upper()
        ):
            raise BridgeUnavailableError(
                "loaded-feature build mirror disagrees with bridge hello"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot_id
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "loaded-feature query crossed a snapshot revision"
            )
        source = {
            "game_version": observed_version,
            "executable_sha256": observed_sha256.upper(),
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "paused": True,
            "backend_id": snapshot_backend_id,
        }
        binding = {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "expected_revision": expected_revision,
        }
        return {
            **result,
            "schema_version": 1,
            "status": normalized["status"],
            "scope": "exact-loaded-feature-manifest",
            "source": source,
            "binding": binding,
            **expected_mirrors,
            "loaded_feature_manifest_ready": normalized["readiness"][
                "actionable_ready"
            ],
            "loaded_feature_manifest": normalized,
        }

    def query_current_event_window_context_v1(
        self,
        event_instance_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read exact identity, presentation, and lossy effect indicators."""
        if (
            isinstance(event_instance_id, bool)
            or not isinstance(event_instance_id, int)
            or not 1 <= event_instance_id <= 2**31 - 1
        ):
            raise ValueError("event_instance_id must be a positive full int32")
        snapshot = self.snapshot()
        revision = snapshot.get("revision")
        native_revision = snapshot.get("native_revision")
        date_raw = snapshot.get("date_raw")
        snapshot_id = snapshot.get("snapshot_id")
        active_event = snapshot.get("active_event")
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "event-window queries require a paused CK3 snapshot"
            )
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
            or isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or expected_revision < 0
        ):
            raise ValueError("expected_revision must be a non-negative integer")
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "event-window revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
            or isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
            or not isinstance(snapshot_id, str)
            or not snapshot_id
        ):
            raise BridgeUnavailableError(
                "event-window query lacks a stable native snapshot binding"
            )
        if (
            not isinstance(active_event, dict)
            or active_event.get("instance_id") != event_instance_id
        ):
            raise BridgeUnavailableError(
                "event instance ID does not match the active event"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
            in bridge_capabilities
            and QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
            in action_step_set(capabilities)
        ):
            raise UnsupportedStepError(
                "selected backend cannot query the current event window"
            )
        result = self.execute_step(
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            expected_revision=expected_revision,
        )
        mirror_keys = {
            "schema",
            "schema_version",
            "date_raw",
            "current_event_instance_id",
            "window_match_count",
            "unavailable_reason",
            "event_definition_key",
            "calculated_event_id",
            "runtime_stats_ordinal",
            "root_scope",
            "saved_scopes",
            "options",
            "readiness",
            "provenance",
        }
        required_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "current_event_window_context",
            "backend_id",
            "current_event_window_context_ready",
            "current_event_effect_indicators_ready",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            *mirror_keys,
        }
        if (
            not isinstance(result, dict)
            or set(result) != required_keys
            or result.get("step")
            != QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "event-window backend returned a malformed result"
            )
        try:
            normalized = normalize_current_event_window_context_v1(
                result.get("current_event_window_context"),
                expected_event_instance_id=event_instance_id,
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"event-window result is malformed: {error}"
            ) from error
        expected_mirrors = {
            key: copy.deepcopy(normalized[key]) for key in mirror_keys
        }
        if (
            result.get("status") != normalized["status"]
            or any(
                result.get(key) != expected
                for key, expected in expected_mirrors.items()
            )
            or result.get("current_event_window_context_ready")
            is not normalized["readiness"]["option_presentation_ready"]
            or result.get("current_event_effect_indicators_ready")
            is not normalized["readiness"]["effect_indicators_ready"]
            or result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "event-window result mirrors disagree with its snapshot"
            )
        current = self.snapshot()
        current_event = current.get("active_event")
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot_id
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and isinstance(current_event, dict)
            and current_event.get("instance_id") == event_instance_id
        ):
            raise BridgeUnavailableError(
                "event-window query crossed a snapshot revision"
            )
        return {
            **result,
            "schema_version": 1,
            "status": normalized["status"],
            "scope": "exact-current-event-window",
            "source": {
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            "binding": {
                "snapshot_id": snapshot_id,
                "revision": revision,
                "native_revision": native_revision,
                "date_raw": date_raw,
                "expected_revision": expected_revision,
                "event_instance_id": event_instance_id,
            },
            **expected_mirrors,
            "current_event_window_context_ready": normalized["readiness"][
                "option_presentation_ready"
            ],
            "current_event_effect_indicators_ready": normalized["readiness"][
                "effect_indicators_ready"
            ],
            "current_event_window_context": normalized,
        }

    def query_pending_character_interaction_context_v1(
        self,
        pending_interaction_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one exact pending interaction with costs and war binding."""
        pending_interaction_id = normalize_pending_interaction_id(
            pending_interaction_id
        )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "pending-interaction queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise BridgeUnavailableError(
                "pending-interaction query lacks a valid snapshot revision"
            )
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
                "pending-interaction revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        pending = snapshot.get("pending_character_interaction")
        if (
            not isinstance(pending, dict)
            or pending.get("instance_id") != pending_interaction_id
        ):
            raise BridgeUnavailableError(
                "pending interaction ID does not match the current snapshot"
            )
        native_revision = snapshot.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "pending-interaction query lacks a positive native revision"
            )
        date_raw = snapshot.get("date_raw")
        if (
            isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "pending-interaction query lacks a signed int32 date"
            )
        snapshot_id = snapshot.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise BridgeUnavailableError(
                "pending-interaction query lacks a snapshot identity"
            )
        snapshot_backend_id = snapshot.get("backend_id")
        if not isinstance(snapshot_backend_id, str) or not snapshot_backend_id:
            raise BridgeUnavailableError(
                "pending-interaction query lacks a source backend identity"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY
            in bridge_capabilities
            and QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
            in action_step_set(capabilities)
        ):
            raise UnsupportedStepError(
                "selected backend cannot query pending interaction context"
            )
        typed_query = getattr(
            self.driver,
            "query_pending_character_interaction_context_v1",
            None,
        )
        if not callable(typed_query):
            raise UnsupportedStepError(
                "selected backend lacks the parameterized pending query"
            )
        result = typed_query(
            pending_interaction_id,
            expected_revision=expected_revision,
        )
        mirror_keys = {
            "schema",
            "schema_version",
            "date_raw",
            "pending_interaction_id",
            "reason",
            "build",
            "definition",
            "roles",
            "target",
            "send_options",
            "routing",
            "deadline",
            "auto_accept",
            "legality",
            "terms",
            "readiness",
            "provenance",
        }
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "pending_character_interaction_context",
            "backend_id",
            "pending_character_interaction_context_ready",
            "queried_snapshot_id",
            "queried_revision",
            "queried_native_revision",
            *mirror_keys,
        }
        if (
            not isinstance(result, dict)
            or set(result) != required_result_keys
            or result.get("step")
            != QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
            or result.get("accepted") is not True
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "pending-interaction backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "pending-interaction result lacks query_sequence"
            )
        backend_id = result.get("backend_id")
        if not isinstance(backend_id, str) or not backend_id:
            raise BridgeUnavailableError(
                "pending-interaction result lacks backend_id"
            )
        try:
            normalized = normalize_pending_character_interaction_context_v1(
                result.get("pending_character_interaction_context"),
                expected_pending_interaction_id=pending_interaction_id,
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"pending-interaction result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "pending-interaction envelope status disagrees with its frame"
            )
        expected_mirrors = {
            key: copy.deepcopy(normalized[key]) for key in mirror_keys
        }
        readiness = normalized["readiness"]
        assert isinstance(readiness, dict)
        if any(
            result.get(key) != expected
            for key, expected in expected_mirrors.items()
        ) or result.get(
            "pending_character_interaction_context_ready"
        ) is not readiness["interaction_semantic_decision_ready"]:
            raise BridgeUnavailableError(
                "pending-interaction result mirrors disagree with its frame"
            )
        if (
            result.get("queried_snapshot_id") != snapshot_id
            or result.get("queried_revision") != revision
            or result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "pending-interaction result is bound to another snapshot"
            )
        if normalized["status"] == "available":
            routing = normalized["routing"]
            roles = normalized["roles"]
            assert isinstance(routing, dict)
            assert isinstance(roles, dict)
            if (
                routing.get("auto_accept_notification")
                is not pending.get("auto_accept_notification")
                or roles.get("actor_character_id")
                != pending.get("sender_character_id")
            ):
                raise BridgeUnavailableError(
                    "pending-interaction frame disagrees with snapshot mirror"
                )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        build = normalized["build"]
        assert isinstance(build, dict)
        observed_version = (
            hello.get("expected_ck3_version", hello.get("game_version"))
            if isinstance(hello, dict)
            else None
        )
        observed_sha256 = (
            hello.get(
                "expected_ck3_sha256", hello.get("executable_sha256")
            )
            if isinstance(hello, dict)
            else None
        )
        if (
            observed_version != build["version"]
            or not isinstance(observed_sha256, str)
            or observed_sha256.upper()
            != str(build["exe_sha256"]).upper()
        ):
            raise BridgeUnavailableError(
                "pending-interaction build mirror disagrees with bridge hello"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot_id
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
            and current.get("pending_character_interaction") == pending
        ):
            raise BridgeUnavailableError(
                "pending-interaction query crossed a snapshot revision"
            )
        source = {
            "game_version": observed_version,
            "executable_sha256": observed_sha256.upper(),
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "paused": True,
            "backend_id": snapshot_backend_id,
        }
        binding = {
            "snapshot_id": snapshot_id,
            "revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "pending_interaction_id": pending_interaction_id,
            "expected_revision": expected_revision,
        }
        return {
            **result,
            "schema_version": 1,
            "status": normalized["status"],
            "scope": "exact-pending-character-interaction-context",
            "source": source,
            "binding": binding,
            **expected_mirrors,
            "pending_character_interaction_context_ready": readiness[
                "interaction_semantic_decision_ready"
            ],
            "pending_character_interaction_context": normalized,
        }

    def query_actual_contact_scope(
        self,
        subject_army_id: int,
        target_province_id: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Predict contact or read its actual CombatID and ordered sides."""
        step = query_actual_contact_scope_step(
            subject_army_id, target_province_id
        )
        result = self._execute_typed_war_step(
            step, expected_revision=expected_revision
        )
        scope = result.get("actual_contact_scope")
        if not (
            isinstance(scope, dict)
            and scope.get("subject_army_id") == subject_army_id
            and scope.get("target_province_id") == target_province_id
            and scope.get("scope_kind")
            in {"pre_contact_prediction", "post_contact_observation"}
            and scope.get("actual_contact_scope_ready") is True
        ):
            raise BridgeUnavailableError(
                "native actual-contact query lacks its exact ordered scope"
            )
        return result

    def query_battle_control_snapshot_v1(
        self,
        subject_public_cunit_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one selected full public CUnitID's battle frame while paused."""
        step = query_battle_control_snapshot_v1_step(
            subject_public_cunit_id
        )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "battle-control queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise BridgeUnavailableError(
                "battle-control query lacks a valid snapshot revision"
            )
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
                "battle-control revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-control query lacks a positive native revision"
            )
        date_raw = snapshot.get("date_raw")
        if (
            isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**63) <= date_raw <= 2**63 - 1
        ):
            raise BridgeUnavailableError(
                "battle-control query lacks a signed int64 date"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_BATTLE_CONTROL_SNAPSHOT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query ongoing battle control frames"
            )
        result = self.execute_step(
            step,
            expected_revision=expected_revision,
        )
        if not isinstance(result, dict):
            raise BridgeUnavailableError(
                "battle-control backend returned a non-object result"
            )
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "battle_control_snapshot",
            "selected_public_cunit_id",
            "selected_native_carmy_id",
            "selected_owner_character_id",
            "combat_province_id",
            "side_index",
            "side_scope",
            "affected_public_cunit_ids_in_stored_order",
            "unaffected_same_side_public_cunit_ids_in_stored_order",
            "side_flags",
            "legality",
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
            or result.get("status") != "available"
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-control backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-control result lacks query_sequence"
            )
        try:
            normalized = normalize_battle_control_snapshot_v1(
                result.get("battle_control_snapshot"),
                expected_subject_public_cunit_id=(
                    subject_public_cunit_id
                ),
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"battle-control result is malformed: {error}"
            ) from error
        retreat_mirrors = {
            "selected_public_cunit_id": normalized[
                "selected_public_cunit_id"
            ],
            "selected_native_carmy_id": normalized[
                "selected_native_carmy_id"
            ],
            "selected_owner_character_id": normalized[
                "selected_owner_character_id"
            ],
            "combat_province_id": normalized["combat_province_id"],
            "side_index": normalized["side_index"],
            "side_scope": normalized["side_scope"],
            "affected_public_cunit_ids_in_stored_order": normalized[
                "affected_public_cunit_ids_in_stored_order"
            ],
            "unaffected_same_side_public_cunit_ids_in_stored_order": (
                normalized[
                    "unaffected_same_side_public_cunit_ids_in_stored_order"
                ]
            ),
            "side_flags": normalized["side_flags"],
            "legality": normalized["legality"],
        }
        if any(
            result.get(key) != expected
            for key, expected in retreat_mirrors.items()
        ):
            raise BridgeUnavailableError(
                "battle-control active-retreat mirror disagrees with its frame"
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
            and result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-control result is bound to another snapshot"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "battle-control query crossed a snapshot revision"
            )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        return {
            **result,
            "schema_version": 1,
            "status": "available",
            "scope": "exact-ongoing-battle",
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
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            "subject_army_id": subject_public_cunit_id,
            **copy.deepcopy(retreat_mirrors),
            "battle_control_ready": True,
            "battle_control_snapshot": normalized,
        }

    def query_battle_transition_v1(
        self,
        combat_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one full CombatID's lifecycle without an army-state gate."""
        step = query_battle_transition_v1_step(combat_id)
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "battle-transition queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise BridgeUnavailableError(
                "battle-transition query lacks a valid snapshot revision"
            )
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
                "battle-transition revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-transition query lacks a positive native revision"
            )
        date_raw = snapshot.get("date_raw")
        if (
            isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**63) <= date_raw <= 2**63 - 1
        ):
            raise BridgeUnavailableError(
                "battle-transition query lacks a signed int64 date"
            )
        capabilities = self.capabilities()
        bridge_capabilities = capabilities.get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_BATTLE_TRANSITION_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query exact combat lifecycle"
            )
        result = self.execute_step(
            step,
            expected_revision=expected_revision,
        )
        if not isinstance(result, dict):
            raise BridgeUnavailableError(
                "battle-transition backend returned a non-object result"
            )
        mirror_keys = {
            "combat_id",
            "province_id",
            "phase",
            "phase_raw",
            "phase_day",
            "winner_side",
            "winner_raw",
            "forced_winner_side",
            "forced_winner_raw",
            "finalized",
            "battle_result_id",
            "attacker_public_cunit_ids_in_stored_order",
            "defender_public_cunit_ids_in_stored_order",
            "battle_transition_ready",
        }
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "battle_transition_snapshot",
            "backend_id",
            *mirror_keys,
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
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-transition backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-transition result lacks query_sequence"
            )
        try:
            normalized = normalize_battle_transition_v1(
                result.get("battle_transition_snapshot"),
                expected_combat_id=combat_id,
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"battle-transition result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "battle-transition envelope status disagrees with its frame"
            )
        lifecycle_mirrors = {
            key: copy.deepcopy(normalized[key]) for key in mirror_keys
        }
        if any(
            result.get(key) != expected
            for key, expected in lifecycle_mirrors.items()
        ):
            raise BridgeUnavailableError(
                "battle-transition lifecycle mirror disagrees with its frame"
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
            and result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-transition result is bound to another snapshot"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "battle-transition query crossed a snapshot revision"
            )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        return {
            **result,
            "schema_version": 1,
            "status": normalized["status"],
            "scope": "exact-combat-lifecycle",
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
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            **lifecycle_mirrors,
            "battle_transition_snapshot": normalized,
        }

    def query_battle_terminal_transition_v1(
        self,
        prior_combat_id: int,
        subject_public_cunit_id: int,
        *,
        expected_revision: int,
        after_terminal_sequence: int | None = None,
    ) -> dict[str, object]:
        """Read terminal history and the subject's same-frame successor state."""
        step = query_battle_terminal_transition_v1_step(
            prior_combat_id,
            subject_public_cunit_id,
            after_terminal_sequence,
        )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "battle-terminal transition queries require a paused CK3 "
                "snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition query lacks a valid snapshot "
                "revision"
            )
        if (
            isinstance(expected_revision, bool)
            or not isinstance(expected_revision, int)
            or expected_revision < 0
        ):
            raise ValueError("expected_revision must be a non-negative integer")
        if expected_revision != revision:
            raise BridgeUnavailableError(
                "battle-terminal transition revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition query lacks a positive native "
                "revision"
            )
        date_raw = snapshot.get("date_raw")
        if (
            isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**31) <= date_raw <= 2**31 - 1
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition query lacks a signed int32 date"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query journal-backed battle "
                "transitions"
            )
        result = self.execute_step(step, expected_revision=expected_revision)
        if not isinstance(result, dict):
            raise BridgeUnavailableError(
                "battle-terminal transition backend returned a non-object "
                "result"
            )
        mirror_keys = {
            "prior_combat_id",
            "subject_public_cunit_id",
            "terminal_journal",
            "prior",
            "removal",
            "subject",
            "successor",
            "battle_terminal_transition_ready",
            "unavailable_reason",
        }
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "battle_terminal_transition",
            "backend_id",
            *mirror_keys,
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
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition backend returned a malformed "
                "result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition result lacks query_sequence"
            )
        try:
            normalized = normalize_battle_terminal_transition_v1(
                result.get("battle_terminal_transition"),
                expected_prior_combat_id=prior_combat_id,
                expected_subject_public_cunit_id=subject_public_cunit_id,
                expected_after_terminal_sequence=after_terminal_sequence,
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"battle-terminal transition result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "battle-terminal transition envelope status disagrees with "
                "its frame"
            )
        mirrors = {
            key: copy.deepcopy(normalized[key]) for key in mirror_keys
        }
        if any(
            result.get(key) != expected
            for key, expected in mirrors.items()
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition mirror disagrees with its frame"
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
            and result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition result is bound to another "
                "snapshot"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "battle-terminal transition query crossed a snapshot revision"
            )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        return {
            **result,
            "schema_version": 1,
            "status": normalized["status"],
            "scope": "journal-backed-battle-terminal-transition",
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
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            **mirrors,
            "battle_terminal_transition": normalized,
        }

    def query_battle_reinforcement_assignment_v1(
        self,
        selected_public_cunit_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one native AI help signal, assignment, route and contact view."""
        step = query_battle_reinforcement_assignment_v1_step(
            selected_public_cunit_id
        )
        snapshot = self.snapshot()
        if snapshot.get("paused") is not True:
            raise BridgeUnavailableError(
                "battle-reinforcement queries require a paused CK3 snapshot"
            )
        revision = snapshot.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement query lacks a valid snapshot revision"
            )
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
                "battle-reinforcement revision mismatch: expected "
                f"{expected_revision}, current {revision}"
            )
        native_revision = snapshot.get("native_revision")
        if (
            isinstance(native_revision, bool)
            or not isinstance(native_revision, int)
            or not 1 <= native_revision <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement query lacks a positive native revision"
            )
        date_raw = snapshot.get("date_raw")
        if (
            isinstance(date_raw, bool)
            or not isinstance(date_raw, int)
            or not -(2**63) <= date_raw <= 2**63 - 1
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement query lacks a signed int64 date"
            )
        bridge_capabilities = self.capabilities().get("bridge_capabilities")
        if not (
            isinstance(bridge_capabilities, list)
            and QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY
            in bridge_capabilities
        ):
            raise UnsupportedStepError(
                "selected backend cannot query native AI reinforcement state"
            )
        result = self.execute_step(
            step,
            expected_revision=expected_revision,
        )
        if not isinstance(result, dict):
            raise BridgeUnavailableError(
                "battle-reinforcement backend returned a non-object result"
            )
        mirror_keys = {
            "selected_public_cunit_id",
            "selected_native_carmy_id",
            "coordinator_id",
            "unit_stack_stored_index",
            "subunit_stored_index",
            "signal",
            "assignment",
            "route",
            "native_order",
            "contact_projection",
            "battle_reinforcement_assignment_ready",
            "unavailable_reason",
        }
        required_result_keys = {
            "step",
            "accepted",
            "status",
            "query_sequence",
            "snapshot_revision",
            "battle_reinforcement_assignment",
            "backend_id",
            *mirror_keys,
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
            or result.get("snapshot_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement backend returned a malformed result"
            )
        query_sequence = result.get("query_sequence")
        if (
            isinstance(query_sequence, bool)
            or not isinstance(query_sequence, int)
            or not 1 <= query_sequence <= 2**64 - 1
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement result lacks query_sequence"
            )
        try:
            normalized = normalize_battle_reinforcement_assignment_v1(
                result.get("battle_reinforcement_assignment"),
                expected_selected_public_cunit_id=selected_public_cunit_id,
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"battle-reinforcement result is malformed: {error}"
            ) from error
        if result.get("status") != normalized["status"]:
            raise BridgeUnavailableError(
                "battle-reinforcement envelope status disagrees with frame"
            )
        mirrors = {
            key: copy.deepcopy(normalized[key]) for key in mirror_keys
        }
        if any(
            result.get(key) != expected
            for key, expected in mirrors.items()
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement mirror disagrees with its frame"
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
            and result.get("queried_native_revision") != native_revision
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement result is bound to another snapshot"
            )
        current = self.snapshot()
        if not (
            current.get("paused") is True
            and current.get("revision") == revision
            and current.get("snapshot_id") == snapshot.get("snapshot_id")
            and current.get("native_revision") == native_revision
            and current.get("date_raw") == date_raw
            and current.get("episode_run_id")
            == snapshot.get("episode_run_id")
        ):
            raise BridgeUnavailableError(
                "battle-reinforcement query crossed a snapshot revision"
            )
        diagnostics = snapshot.get("diagnostics")
        hello = (
            diagnostics.get("hello")
            if isinstance(diagnostics, dict)
            else None
        )
        return {
            **result,
            "schema_version": 1,
            "status": normalized["status"],
            "scope": "native-ai-reinforcement-assignment",
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
                "native_revision": native_revision,
                "date_raw": date_raw,
                "paused": True,
                "backend_id": snapshot.get("backend_id"),
            },
            **mirrors,
            "battle_reinforcement_assignment": normalized,
        }

    def preview_active_combat_retreat_v1(
        self,
        selected_public_cunit_id: int,
        target_province_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        """Prove one legal same-frame retreat route and issue a short token."""
        step = preview_active_combat_retreat_v1_step(
            selected_public_cunit_id, target_province_id
        )
        capabilities = self.capabilities()
        if not (
            capabilities.get(
                "active_combat_retreat_v1_composition_supported"
            )
            is True
            or step in action_step_set(capabilities)
        ):
            raise UnsupportedStepError(
                "selected backend cannot compose active-combat retreat"
            )
        result = self.execute_step(
            step, expected_revision=expected_revision
        )
        try:
            return normalize_active_combat_retreat_v1_preview(
                result,
                expected_selected_public_cunit_id=(
                    selected_public_cunit_id
                ),
                expected_target_province_id=target_province_id,
                expected_snapshot_revision=expected_revision,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"active-combat retreat preview is malformed: {error}"
            ) from error

    def order_active_combat_retreat_v1(
        self,
        selected_public_cunit_id: int,
        *,
        expected_revision: int,
        expected_combat_id: int,
        expected_side_index: int,
        expected_scope: str,
        target_province_id: int,
        candidate_token: str,
    ) -> dict[str, object]:
        """Consume one preview token and submit the existing player move."""
        step = order_active_combat_retreat_v1_step(
            selected_public_cunit_id,
            expected_snapshot_revision=expected_revision,
            expected_combat_id=expected_combat_id,
            expected_side_index=expected_side_index,
            expected_scope=expected_scope,
            target_province_id=target_province_id,
            candidate_token=candidate_token,
        )
        capabilities = self.capabilities()
        if capabilities.get(
            "active_combat_retreat_v1_composition_supported"
        ) is not True:
            raise UnsupportedStepError(
                "selected backend cannot compose active-combat retreat"
            )
        result = self.execute_step(
            step, expected_revision=expected_revision
        )
        try:
            return normalize_active_combat_retreat_v1_order_ack(
                result,
                expected_selected_public_cunit_id=(
                    selected_public_cunit_id
                ),
                expected_snapshot_revision=expected_revision,
                expected_combat_id=expected_combat_id,
                expected_side_index=expected_side_index,
                expected_scope=expected_scope,
                expected_target_province_id=target_province_id,
                expected_candidate_token=candidate_token,
            )
        except ValueError as error:
            raise BridgeUnavailableError(
                f"active-combat retreat order ACK is malformed: {error}"
            ) from error

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


def _title_map_navigation_binding(
    snapshot: object,
) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    return normalize_title_map_navigation_v1_binding(
        {
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
            "date_raw": snapshot.get("date_raw"),
            "episode_run_id": snapshot.get("episode_run_id"),
            "connection_generation": connection_generation,
        }
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
