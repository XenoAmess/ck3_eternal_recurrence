"""Exact .4 populist ultimatum: prefer refusal to an independent land grant.

This choice accepts a faction-war risk. It does not predict war or victory.
"""
from __future__ import annotations

from copy import deepcopy

from .faction_demand1001_context import recognize_faction_demand1001_projection_v1

EVENT_KEY = "faction_demand.1001"
EVENT_ID = 3551001
FINGERPRINT = "f41794487b9ed31454e9687052b9b84b761104f61db412ae76c5c0518ecdf96c"
BACKEND = "ck3-1.20.0.4-native-event-window-v1"
REFUSE_STEP = "select-event-option-4"


def _positive(value):
    return type(value) is int and value > 0


def _scope_id(row, kind, type_key, field):
    scope = row.get("scope") if isinstance(row, dict) else None
    identity = scope.get("typed_identity") if isinstance(scope, dict) else None
    if (not isinstance(identity, dict) or scope.get("status") != "available"
            or scope.get("type_key") != type_key
            or identity.get("status") != "available" or identity.get("kind") != kind
            or not _positive(identity.get(field))):
        return None
    return identity[field]


def choose_source_reviewed_populist_refusal_v1(plan, *, snapshot, action_steps):
    """Change only the currently bound two-button, exact-source event."""
    if not isinstance(plan, dict) or not isinstance(snapshot, dict):
        return plan
    capture = plan.get("unhandled_event_fallback")
    audit = capture.get("source_knowledge") if isinstance(capture, dict) else None
    context = capture.get("window_context") if isinstance(capture, dict) else None
    selection = capture.get("selection") if isinstance(capture, dict) else None
    binding = capture.get("binding") if isinstance(capture, dict) else None
    decision = plan.get("event_decision")
    if not (plan.get("phase") == "active_event_source_reviewed_first_rendered_option"
            and isinstance(capture, dict) and isinstance(audit, dict)
            and isinstance(context, dict) and isinstance(selection, dict)
            and isinstance(binding, dict) and isinstance(decision, dict)
            and capture.get("event_definition_key") == EVENT_KEY
            and context.get("event_definition_key") == EVENT_KEY
            and context.get("calculated_event_id") == EVENT_ID
            and isinstance(context.get("provenance"), dict)
            and context["provenance"].get("backend_id") == BACKEND
            and context.get("status") == "available"
            and context.get("window_match_count") == 1
            and capture.get("snapshot_option_count") == 4
            and audit.get("status") == "offline-source-reviewed"
            and audit.get("binding_mode") == "exact"
            and audit.get("fingerprint") == FINGERPRINT
            # The registry entry is validated by annotate_source_reviewed_event_plan_v1.
            # Its bytes may change when republished under a new evidence root.
            and isinstance(audit.get("entry_sha256"), str)
            and len(audit["entry_sha256"]) == 64
            and capture.get("registry_known") is True
            and decision.get("status") == "source_reviewed_known"
            and decision.get("material_effects_verified") is False
            and plan.get("selected_step") == "select-event-option-3"
            and selection.get("native_option_index") == 2
            and selection.get("rendered_index") == 0
            and selection.get("enabled") is True
            and selection.get("selected_step") == plan["selected_step"]
            and REFUSE_STEP in set(action_steps or ())):
        return plan
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or any(snapshot.get(key) != binding.get(key) for key in (
                "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
            or binding.get("snapshot_id") != "native:" + str(binding.get("native_revision"))
            or context.get("snapshot_revision") != snapshot.get("native_revision")
            or context.get("date_raw") != snapshot.get("date_raw")):
        return plan
    diagnostics = snapshot.get("diagnostics")
    actor = snapshot.get("played_character")
    active = snapshot.get("active_event")
    if not (isinstance(diagnostics, dict) and isinstance(actor, dict)
            and isinstance(active, dict) and actor.get("alive") is True
            and actor.get("character_id") == binding.get("actor_character_id")
            and diagnostics.get("bridge_pid") == binding.get("bridge_pid")
            and diagnostics.get("connection_generation") == binding.get("connection_generation")
            and active.get("instance_id") == capture.get("current_event_instance_id")
            and active.get("option_count") == 4
            and context.get("current_event_instance_id") == active.get("instance_id")):
        return plan
    recognized = recognize_faction_demand1001_projection_v1(
        context, played_character_id=actor["character_id"], snapshot_option_count=4)
    if recognized.get("status") != "recognized":
        return plan
    options = context.get("options")
    by_native = {row.get("native_option_index"): row for row in options}
    if (set(by_native) != {2, 3}
            or by_native[2].get("rendered_index") != 0
            or by_native[3].get("rendered_index") != 1):
        return plan
    roles = {row["name"]: row for row in context["saved_scopes"]}
    faction = _scope_id(roles["faction"], "faction", "faction", "faction_id")
    target_title = _scope_id(roles["target_title"], "landed_title", "landed_title", "title_id")
    leader = _scope_id(roles["peasant_leader"], "character", "character", "character_id")
    county = _scope_id(roles["peasant_county"], "landed_title", "landed_title", "title_id")
    if not all(_positive(v) for v in (faction, target_title, leader, county)):
        return plan
    result = deepcopy(plan)
    result.update(
        phase="active_event_source_reviewed_populist_refusal",
        selected_step=REFUSE_STEP,
        reason=("Exact .4 source: native 2 grants populist independence; enabled native 3 "
                "refuses and starts a faction war. Preserve land; victory is unverified."),
        faction_demand_source_outcome={
            "status": "source_reviewed_expected_only", "event_definition_key": EVENT_KEY,
            "saved_faction_id": faction, "saved_target_title_id": target_title,
            "saved_peasant_leader_character_id": leader,
            "expected_effect": "faction_start_war", "war_started_verified": False,
            "victory_verified": False, "title_retention_verified": False})
    summary = result.get("active_event")
    if not isinstance(summary, dict):
        return plan
    summary.update(selected_option_number=4, selected_native_option_index=3,
                   selected_rendered_index=1, semantic_optimal=False)
    result["event_decision"].update(
        selected_option_number=4, selected_native_option_index=3,
        selected_rendered_index=1, semantic_optimal=False,
        classification="offline-source-reviewed-populist-refusal-policy",
        source_reviewed_policy="populist_refuse_preserve_realm_accept_war_risk",
        material_effects_verified=False, registry_contract_accepted=False)
    result["unhandled_event_fallback"].update(
        policy="exact-source-reviewed-populist-refuse-preserve-realm",
        offline_followup_required=False)
    result["unhandled_event_fallback"]["selection"].update(
        rendered_index=1, native_option_index=3, option_number=4,
        resolved_name=by_native[3].get("resolved_name"), enabled=True,
        selected_step=REFUSE_STEP,
        selection_order="exact_source_reviewed_populist_refuse_preserve_realm")
    return result


def verify_source_reviewed_populist_refusal_result_v1(body):
    """Verify the selected native option and captured UI readback, with zero war credit.

    Return ``None`` for every other plan. A mismatch after submission is an
    unresolved action; callers must retain its original response without replay.
    """
    if not isinstance(body, dict):
        return None
    plan = body.get("plan")
    if not isinstance(plan, dict) or plan.get("phase") != "active_event_source_reviewed_populist_refusal":
        return None
    capture = plan.get("unhandled_event_fallback")
    selection = capture.get("selection") if isinstance(capture, dict) else None
    knowledge = capture.get("source_knowledge") if isinstance(capture, dict) else None
    decision = plan.get("event_decision")
    summary = plan.get("active_event")
    binding = capture.get("binding") if isinstance(capture, dict) else None
    inner = body.get("result")
    post = inner.get("event_selection") if isinstance(inner, dict) else None
    evidence = body.get("unhandled_event_fallback_evidence")
    before = evidence.get("before") if isinstance(evidence, dict) else None
    after = evidence.get("after") if isinstance(evidence, dict) else None
    if not (body.get("status") == "executed"
            and body.get("selected_step") == plan.get("selected_step") == REFUSE_STEP
            and isinstance(capture, dict) and isinstance(selection, dict)
            and isinstance(knowledge, dict) and isinstance(decision, dict)
            and isinstance(summary, dict) and isinstance(binding, dict)
            and capture.get("policy") == "exact-source-reviewed-populist-refuse-preserve-realm"
            and capture.get("event_definition_key") == EVENT_KEY
            and knowledge.get("status") == "offline-source-reviewed"
            and knowledge.get("binding_mode") == "exact"
            and knowledge.get("fingerprint") == FINGERPRINT
            and capture.get("registry_known") is True
            and selection.get("selected_step") == REFUSE_STEP
            and selection.get("native_option_index") == 3
            and selection.get("option_number") == 4
            and selection.get("rendered_index") == 1
            and selection.get("enabled") is True
            and summary.get("selected_native_option_index") == 3
            and summary.get("selected_option_number") == 4
            and summary.get("selected_rendered_index") == 1
            and decision.get("selected_native_option_index") == 3
            and decision.get("selected_option_number") == 4
            and decision.get("selected_rendered_index") == 1
            and decision.get("material_effects_verified") is False
            and isinstance(inner, dict) and inner.get("accepted") is True
            and inner.get("step") == REFUSE_STEP
            and inner.get("option_number") == 4
            and inner.get("option_index") == 3
            and inner.get("event_instance_id") == capture.get("current_event_instance_id")
            and isinstance(post, dict)
            and post.get("status") == "event_instance_advanced"
            and post.get("postcondition_verified") is True
            and post.get("old_event_instance_id") == capture.get("current_event_instance_id")
            and post.get("new_event_instance_id") != capture.get("current_event_instance_id")
            and post.get("selected_option_number") == 4
            and post.get("selected_native_option_index") == 3
            and post.get("starting_snapshot_id") == binding.get("snapshot_id")
            and type(binding.get("revision")) is int
            and type(post.get("starting_revision")) is int
            and post.get("starting_revision") == binding.get("revision")
            and post.get("ending_snapshot_id") == inner.get("snapshot_id")
            and post.get("ending_revision") == inner.get("revision")
            and type(post.get("ending_revision")) is int
            and post["ending_revision"] > post["starting_revision"]
            and all(post.get(key) == binding.get(key) for key in (
                "episode_run_id", "connection_generation", "bridge_pid"))
            and isinstance(evidence, dict)
            and evidence.get("command_acknowledged") is True
            and evidence.get("event_instance_advanced_verified") is True
            and evidence.get("replay_allowed") is False
            and isinstance(evidence.get("incident_id"), str) and bool(evidence["incident_id"])
            and all(isinstance(row, dict)
                    and isinstance(row.get("path"), str) and bool(row["path"])
                    and isinstance(row.get("sha256"), str) and len(row["sha256"]) == 64
                    for row in (before, after))):
        raise ValueError("source-reviewed populist refusal receipt/selection differs; retain without replay")
    return {
        "schema": "g2.queue.ordinary-result-credit/v1",
        "selected_step": REFUSE_STEP,
        "service_status": "executed",
        "result_status": inner.get("status"),
        "category": "source_reviewed_populist_refusal_ui_advanced",
        "primitive_accepted": True,
        "submitted_pending": False,
        "typed_nonmaterial_observation": False,
        "business_success_inferred": False,
        "war_started_verified": False,
        "victory_verified": False,
        "title_retention_verified": False,
        "replay_allowed": False,
    }
