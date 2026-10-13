"""Ordinary-planner adapter for the observed seven-role populist ultimatum.

The existing context builder owns scope identity and surrender consequences.
This adapter supplies the two candidates to the ordinary strategy owner; it
does not derive executable troop strength or invent a separate war policy.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from ..bridge.player_faction_alerts_contract import QUERY_PLAYER_FACTION_ALERTS_V1_STEP
from .faction_demand1001_context import build_faction_demand1001_decision_context_v1
from .records_faction_demand1001_12003 import EVENT_KEY


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def plan_faction_demand1001_ordinary_v1(
    event_context: Mapping[str, object],
    snapshot: Mapping[str, object],
    *,
    faction_alerts: Mapping[str, object] | None,
    war_entry_assessments: Mapping[int, Mapping[str, object]],
    action_steps: set[str],
    selection: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    """Build exact candidates and consume a separately owned strategy choice.

    ``faction_alerts`` is the caller's validated observation of this paused
    date. Event and faction queries retain their own native revisions, as in
    the existing context builder; the caller must discard observations across
    an action, connection change, actor change or event change. The current
    event query must match the current snapshot before calling this adapter.

    A strategy selection must echo ``event_decision.binding`` and include its
    policy and reason. This prevents a prior event's decision from selecting
    the currently presented option. The caller executes the returned step
    through the existing typed event command and verifies its postconditions.
    """
    if event_context.get("event_definition_key") != EVENT_KEY:
        return None
    decision: dict[str, object] = {
        "schema": "xar.ck3.ordinary-faction-demand1001.v1",
        "status": "blocked",
        "selected_option_number": None,
        "selected_native_option_index": None,
        "semantic_optimal": False,
        "campaign_utility_ready": False,
        "candidates": [],
        "binding": None,
    }
    plan: dict[str, object] = {
        "policy": "one-life-turn-v1",
        "phase": "active_event_populist_context_blocked",
        "selected_step": None,
        "reason": "current paused populist event observation required",
        "event_decision": decision,
        "active_event": {
            "instance_id": event_context.get("current_event_instance_id"),
            "event_definition_key": EVENT_KEY,
        },
    }
    actor = snapshot.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    event = snapshot.get("active_event", snapshot.get("current_event"))
    diagnostics = snapshot.get("diagnostics")
    generation = diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None
    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and isinstance(actor, Mapping) and actor.get("alive") is True
        and _integer(actor_id) and 0 < actor_id <= 2**31 - 1
        and isinstance(event, Mapping) and event.get("option_count") == 4
        and _integer(event.get("instance_id"))
        and event.get("instance_id") == event_context.get("current_event_instance_id")
        and _integer(snapshot.get("native_revision"))
        and snapshot.get("native_revision") == event_context.get("snapshot_revision")
        and _integer(snapshot.get("revision"))
        and snapshot.get("date_raw") == event_context.get("date_raw")
        and _integer(generation) and generation > 0
    ):
        decision["unavailable_reason"] = "current_event_snapshot_binding_required"
        return plan
    if faction_alerts is None:
        step = QUERY_PLAYER_FACTION_ALERTS_V1_STEP
        plan.update(
            phase="active_event_populist_faction_query",
            selected_step=step if step in action_steps else None,
            required_step=step,
            reason="read the saved faction's current identity and surrender impact",
        )
        decision.update(status="query_required", unavailable_reason="current_faction_alert_required")
        return plan
    faction_revision = faction_alerts.get("snapshot_revision")
    if not (_integer(faction_revision) and 0 <= faction_revision <= snapshot["native_revision"]):
        decision["unavailable_reason"] = "faction_observation_revision_invalid"
        return plan
    context = build_faction_demand1001_decision_context_v1(
        event_context, faction_alerts,
        played_character_id=actor_id,
        expected_event_instance_id=event["instance_id"],
        expected_date_raw=snapshot["date_raw"],
        expected_event_snapshot_revision=snapshot["native_revision"],
        expected_faction_snapshot_revision=faction_revision,
    )
    decision["context"] = context
    if context.get("binding_ready") is not True:
        decision["unavailable_reason"] = context.get("unavailable_reason")
        plan["reason"] = "the saved faction and current faction observation do not yet bind"
        return plan
    binding = {
        **context["binding"],
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot["revision"],
        "connection_generation": generation,
        "episode_run_id": snapshot.get("episode_run_id"),
    }
    decision["binding"] = binding
    leader = binding["leader_character_id"]
    assessment = war_entry_assessments.get(leader)
    strategic_inputs = None
    if isinstance(assessment, Mapping) and (
        assessment.get("target_character_id") == leader
        and assessment.get("effective_target_character_id") == leader
        and all(_integer(assessment.get(key)) and assessment[key] >= 0
                for key in ("actor_power_base_raw", "target_power_total_raw"))
    ):
        strategic_inputs = deepcopy(dict(assessment))
    acceptance = context.get("acceptance")
    refusal = context.get("refusal")
    if not isinstance(acceptance, Mapping) or not isinstance(refusal, Mapping):
        decision["unavailable_reason"] = "bound_candidate_effects_unavailable"
        return plan
    decision.update(
        status="comparison_required",
        unavailable_reason="ordinary_strategy_choice_required",
        value_inputs={
            "acceptance_outcome_complete": context["complete_acceptance_outcome_ready"],
            "county_loss_ready": acceptance["county_loss_ready"],
            "faction_material": deepcopy(context["faction_material"]),
            "strategic_power_assessment": strategic_inputs,
            "executable_force_coverage_ready": False,
            "active_wars": deepcopy(snapshot.get("active_wars")),
            "played_character_gold": deepcopy(snapshot.get("played_character_gold")),
        },
        candidates=[
            {"native_option_index": 2, "api_option_number": 3,
             "effects": deepcopy(dict(acceptance)),
             "effect_coverage_ready": context["complete_acceptance_outcome_ready"],
             "postcondition": "old_event_gone_and_independent_transferred_titles"},
            {"native_option_index": 3, "api_option_number": 4,
             "effects": deepcopy(dict(refusal)), "effect_coverage_ready": True,
             "postcondition": "old_event_gone_and_bound_faction_defensive_war"},
        ],
    )
    plan.update(phase="active_event_populist_comparison",
                reason="compare observed surrender losses with the source-bound defensive-war choice")
    if selection is None:
        return plan
    native = selection.get("selected_native_option_index")
    if not (
        _integer(native) and native in (2, 3)
        and selection.get("binding") == binding
        and isinstance(selection.get("policy"), str) and selection["policy"]
        and isinstance(selection.get("reason"), str) and selection["reason"]
    ):
        decision.update(status="blocked", unavailable_reason="ordinary_strategy_selection_binding_invalid")
        return plan
    if native == 2 and context["complete_acceptance_outcome_ready"] is not True:
        decision.update(status="blocked", unavailable_reason="complete_acceptance_outcome_required")
        return plan
    step = f"select-event-option-{native + 1}"
    decision.update(status="recommended", unavailable_reason=None,
                    selected_native_option_index=native, selected_option_number=native + 1,
                    selection_policy=selection["policy"], reason=selection["reason"])
    plan.update(phase="active_event_populist_choice", selected_step=step if step in action_steps else None,
                required_step=step, reason=selection["reason"],
                faction_demand_postcondition={
                    "binding": deepcopy(binding), "selected_native_option_index": native,
                    "kind": "transferred_titles" if native == 2 else "new_faction_defensive_war",
                    "verification_ready": False,
                })
    return plan


__all__ = ["plan_faction_demand1001_ordinary_v1"]
