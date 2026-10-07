"""Consume the observed commander quality before an ordinary war turn."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Protocol

from .bridge.army_commander_assignment import ASSIGN_ARMY_COMMANDER_V1_CAPABILITY
from .bridge.army_commander_candidates import QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY
from .bridge.driver import BridgeUnavailableError, UnsupportedStepError


class CommanderQueryService(Protocol):
    def query_army_commander_candidates_v1(
        self, army_id: int, *, expected_revision: int | None = None,
    ) -> dict[str, object]: ...


def plan_commander_quality_formal_v1(
    service: CommanderQueryService, *, planned: dict[str, object],
    snapshot: Mapping[str, object], bridge_capabilities: list[str],
) -> dict[str, object]:
    """Prefer a strictly better legal commander on the existing formal path.

    Mandatory lifecycle, battle, response, retreat and postwar work retains
    its existing priority. An exact-objective hold can improve its commander
    independently while the original movement decision remains deferred.
    The native group's multi-Army allocation remains separate.
    """
    plan = planned.get("plan")
    if not isinstance(plan, Mapping):
        return planned
    phase = plan.get("phase")
    if phase not in {
        "native_war_reconnaissance", "native_war_pursuit",
        "native_war_pursuit_progress", "native_war_counterpolicy_hold",
    }:
        return planned
    if phase == "native_war_counterpolicy_hold":
        if plan.get("selected_step") is not None:
            return planned
    elif phase != "native_war_pursuit" and plan.get("selected_step") != "life-advance":
        return planned
    required = {
        QUERY_ARMY_COMMANDER_CANDIDATES_V1_CAPABILITY,
        ASSIGN_ARMY_COMMANDER_V1_CAPABILITY,
    }
    if not required <= set(bridge_capabilities):
        return planned

    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        return planned
    pursuit = plan.get("pursuit")
    if isinstance(pursuit, Mapping):
        army_id = pursuit.get("army_id")
    else:
        army_id = next((row.get("army_id") for row in armies
                        if isinstance(row, Mapping)
                        and row.get("controllable") is True), None)
    if type(army_id) is not int:
        return planned

    try:
        queried = service.query_army_commander_candidates_v1(
            army_id, expected_revision=planned["revision"],
        )
    except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
        return {**planned, "plan": {**plan, "commander_quality_selection": {
            "schema": "xar.ck3.commander-quality-formal-consumer.v1",
            "status": "input_unavailable", "formal_action_ready": False,
            "selected_step": None, "baseline_selected_step": plan.get("selected_step"),
            "assignment_executed": False, "reason": str(error),
        }}}

    proposal = queried["commander_quality_proposal"]
    step = proposal["selected_step"]
    selection = {
        "schema": "xar.ck3.commander-quality-formal-consumer.v1",
        "status": proposal["status"],
        "automatic_consumption": True,
        "formal_action_ready": isinstance(step, str),
        "selected_step": step,
        "baseline_selected_step": plan.get("selected_step"),
        "assignment_executed": False,
        "proposal": deepcopy(proposal),
    }
    if not isinstance(step, str):
        return {**planned, "plan": {**plan, "commander_quality_selection": selection}}
    action_plan = dict(plan)
    action_plan.pop("required_step", None)
    return {**planned, "plan": {
        **action_plan,
        "phase": "native_commander_quality_assignment",
        "selected_step": step,
        "reason": (
            "a native-eligible commander improves the observed current native quality"
            if proposal["status"] == "assign_better_candidate"
            else "a native-eligible commander fills the observed empty commander role"
        ),
        "commander_quality_selection": selection,
        "deferred_commander_baseline_plan": deepcopy(dict(plan)),
    }}
