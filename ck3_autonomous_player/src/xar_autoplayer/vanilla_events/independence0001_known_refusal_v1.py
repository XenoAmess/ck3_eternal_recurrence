"""Source-learned .4 independence ultimatum; refuse an immediate vassal release.

The static review has no invented incident or calculated definition ID. The
native option is selected only after binding the current displayed window. A
refusal accepts faction-war risk; no war, victory or land-retention credit is
inferred. This does not change the owner's first-displayed unknown-event rule.
"""
from __future__ import annotations

from copy import deepcopy

from ..bridge.event_contract import event_option_step
from .builds import SUPPORTED_CK3_EXE_SHA256
from .event_offline_analysis import _fingerprint, _native_binding


EVENT_KEY = "faction_demand.0001"
SOURCE_SHA256 = "eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd"
# Produced by the existing source reviewer from all three complete option blocks.
OPTION_CATALOGUE_SHA256 = "6237b0c9f4e27ba6f1197d8cad68d41b58bfd64112cdb8705d80b626759f9192"
BACKEND = "ck3-1.20.0.4-native-event-window-v1"
REVIEW = {
    "schema": "xar.independence0001-static-source-review/v1",
    "event_definition_key": EVENT_KEY, "ck3_build": "1.20.0.4",
    "required_ck3_exe_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.4"],
    "source_relative": "events/factions/faction_demands.txt",
    "source_sha256": SOURCE_SHA256,
    "definition_block_sha256": "cd59166f6becea0e42f07d12c77a5a4fdfb5a3dccb55b3131d3ad62245a639f0",
    "source_dependencies": {
        "common/scripted_effects/00_war_effects.txt": "f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b"},
    "option_catalogue_sha256": OPTION_CATALOGUE_SHA256,
    "readiness": "static-ready", "new_live_evidence": False, "observations": [],
    "authored_options": [
        {"native_option_index": 0, "source_name_key": "FACTION_DEMAND_ACCEPT",
         "effect": "every_faction_member_change_liege_or_become_independent",
         "add_claim_on_loss": False, "truce_days": 1825},
        {"native_option_index": 1, "source_name_key": "FACTION_DEMAND_BRIBE_CO_EMPEROR",
         "effect": "offer_co_emperorship_via_faction_demand.0006",
         "visibility_and_legality": "conditional_native_presentation"},
        {"native_option_index": 2, "source_name_key": "FACTION_DEMAND_REFUSE",
         "effect": "reject_demand_then_faction_demand.0003_faction_start_war"},
    ],
    "source_review": "docs/ck3-native-ai/g2-m5-independence-ultimatum-policy-2026-10-19.md",
    "complete_source_options_and_effects": "docs/ck3-native-ai/evidence/g2-m5-independence-ultimatum-policy-2026-10-19.json",
    "material_effects_verified": False, "live_qualification": False,
}


def _positive(value):
    return type(value) is int and value > 0


def _identity(scope, kind, field):
    identity = scope.get("typed_identity") if isinstance(scope, dict) else None
    if (not isinstance(identity, dict) or scope.get("status") != "available"
            or scope.get("type_key") != kind or identity.get("status") != "available"
            or identity.get("kind") != kind or not _positive(identity.get(field))):
        return None
    return identity[field]


def _reviewed_binding(capture):
    """Bind source knowledge to an observed ID without forging a registry entry."""
    try:
        current = _native_binding(capture)
    except (ValueError, TypeError, KeyError):
        return None
    if (current["ck3_build"] != "1.20.0.4"
            or current["event_definition_key"] != EVENT_KEY
            or current["native_backend_id"] != BACKEND
            or current["native_option_count"] != 3
            or REVIEW.get("event_definition_key") != EVENT_KEY
            or REVIEW.get("ck3_build") != current["ck3_build"]
            or REVIEW.get("required_ck3_exe_sha256") != current["required_ck3_exe_sha256"]
            or REVIEW.get("source_sha256") != SOURCE_SHA256
            or REVIEW.get("option_catalogue_sha256") != OPTION_CATALOGUE_SHA256
            or REVIEW.get("readiness") != "static-ready"):
        return None
    current.update(source_sha256=SOURCE_SHA256,
                   option_catalogue_sha256=OPTION_CATALOGUE_SHA256)
    # A durable review of this current definition takes precedence. Never mask
    # a changed source, stale calculated ID or an explicitly rejected exact entry.
    audit = capture.get("source_knowledge")
    if isinstance(audit, dict):
        if audit.get("status") == "offline-source-reviewed":
            if (audit.get("binding_mode") != "exact"
                    or audit.get("fingerprint") != _fingerprint(current)):
                return None
        elif audit.get("status") != "unknown" or audit.get("rejected_entries"):
            return None
    return current


def choose_source_reviewed_independence_refusal_v1(plan, *, snapshot, action_steps):
    """Use the known source and the *currently shown* legal refusal row.

    The optional co-emperor row may be absent, disabled or enabled. Its presence
    does not turn authored native index 2 into a fixed rendered position.
    """
    if not isinstance(plan, dict) or not isinstance(snapshot, dict):
        return plan
    capture = plan.get("unhandled_event_fallback")
    if not isinstance(capture, dict) or capture.get("event_definition_key") != EVENT_KEY:
        return plan
    if plan.get("phase") not in {"active_event_unhandled_first_rendered_option",
                                 "active_event_source_reviewed_first_rendered_option"}:
        return plan
    current = _reviewed_binding(capture)
    context, frame = capture.get("window_context"), capture.get("binding")
    selection, decision = capture.get("selection"), plan.get("event_decision")
    summary, diagnostics = plan.get("active_event"), snapshot.get("diagnostics")
    actor, active = snapshot.get("played_character"), snapshot.get("active_event")
    prior_audit = capture.get("source_knowledge")
    if (isinstance(prior_audit, dict) and prior_audit.get("status") == "offline-source-reviewed"
            and (capture.get("registry_known") is not True
                 or not isinstance(decision, dict) or decision.get("status") != "source_reviewed_known")):
        return plan
    if (current is None or not all(isinstance(v, dict) for v in (
            context, frame, selection, decision, summary, diagnostics, actor, active))
            or context.get("status") != "available" or context.get("window_match_count") != 1
            or context.get("schema_version") != 1
            or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or actor.get("alive") is not True
            or not _positive(actor.get("character_id"))
            or frame.get("actor_character_id") != actor["character_id"]
            or frame.get("paused") is not True or frame.get("map_ready") is not True
            or not _positive(frame.get("native_revision"))
            or frame.get("snapshot_id") != "native:" + str(frame.get("native_revision"))
            or not isinstance(frame.get("episode_run_id"), str) or not frame["episode_run_id"]
            or any(snapshot.get(k) != frame.get(k) for k in (
                "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
            or any(not _positive(frame.get(k)) or diagnostics.get(k) != frame[k]
                   for k in ("bridge_pid", "connection_generation"))
            or context.get("snapshot_revision") != frame["native_revision"]
            or context.get("date_raw") != frame.get("date_raw")
            or not _positive(active.get("instance_id"))
            or active.get("instance_id") != capture.get("current_event_instance_id")
            or context.get("current_event_instance_id") != active["instance_id"]
            or active.get("option_count") != 3):
        return plan
    readiness = context.get("readiness")
    if (not isinstance(readiness, dict) or any(readiness.get(k) is not True for k in (
            "event_definition_identity_ready", "root_scope_ready", "saved_scopes_ready",
            "option_presentation_ready"))
            or _identity(context.get("root_scope"), "character", "character_id") != actor["character_id"]):
        return plan
    saved = context.get("saved_scopes")
    if (not isinstance(saved, list) or not all(isinstance(row, dict) for row in saved)
            or any(not isinstance(row.get("name"), str) for row in saved)
            or len({row["name"] for row in saved}) != len(saved)):
        return plan
    roles = {row["name"]: row.get("scope") for row in saved}
    faction = _identity(roles.get("faction"), "faction", "faction_id")
    leader = _identity(roles.get("faction_leader"), "character", "character_id")
    if (faction is None or leader is None or leader == actor["character_id"]
            or _identity(roles.get("faction_target"), "character", "character_id") != actor["character_id"]):
        return plan
    options = context.get("options")
    if not isinstance(options, list) or not all(isinstance(row, dict) for row in options):
        return plan
    shown = [row for row in options if row.get("shown") is True]
    if (not shown or any(type(row.get("native_option_index")) is not int
            or not 0 <= row["native_option_index"] < 3
            or type(row.get("rendered_index")) is not int or row["rendered_index"] < 0
            for row in shown)
            or len({row["native_option_index"] for row in shown}) != len(shown)
            or {row["rendered_index"] for row in shown} != set(range(len(shown)))):
        return plan
    catalogue = REVIEW.get("authored_options")
    if not isinstance(catalogue, list):
        return plan
    refusal = [row for row in catalogue if isinstance(row, dict)
               and row.get("source_name_key") == "FACTION_DEMAND_REFUSE"]
    if len(refusal) != 1 or refusal[0].get("native_option_index") != 2:
        return plan
    by_native = {row["native_option_index"]: row for row in shown}
    refuse = by_native.get(refusal[0]["native_option_index"])
    enabled = [row for row in shown if row.get("enabled") is True]
    first = min(enabled, key=lambda row: row["rendered_index"]) if enabled else None
    step = event_option_step(refusal[0]["native_option_index"] + 1)
    if (refuse is None or refuse.get("enabled") is not True
            or not isinstance(refuse.get("resolved_name"), str) or not refuse["resolved_name"]
            or first is None or first["native_option_index"] != 0
            or selection.get("native_option_index") != first["native_option_index"]
            or selection.get("rendered_index") != first["rendered_index"]
            or selection.get("enabled") is not True or selection.get("option_number") != 1
            or selection.get("selected_step") != plan.get("selected_step")
            or plan.get("selected_step") != event_option_step(first["native_option_index"] + 1)
            or step not in set(action_steps or ())):
        return plan
    result = deepcopy(plan)
    rendered, native = refuse["rendered_index"], refuse["native_option_index"]
    result.update(phase="active_event_source_reviewed_independence_refusal", selected_step=step,
        reason=("Known .4 independence ultimatum: accepting releases faction members without "
                "claims on loss. Choose the currently enabled refusal; it triggers the faction-war "
                "chain. War outcome and land retention remain unverified."),
        faction_demand_source_outcome={
            "status": "source_reviewed_expected_only", "event_definition_key": EVENT_KEY,
            "saved_faction_id": faction, "saved_faction_leader_character_id": leader,
            "expected_effect": "faction_demand.0003_faction_start_war",
            "rejected_effect": "every_faction_member_change_liege_or_become_independent",
            "exact_lost_titles": None, "war_started_verified": False,
            "victory_verified": False, "title_retention_verified": False,
            "decision_basis": "preserve_realm_accept_faction_war_risk",
            "same_frame_faction_strength": "not_available_in_bound_event_context",
            "counterfactual_optimality_verified": False})
    result["active_event"].update(selected_option_number=native + 1,
        selected_native_option_index=native, selected_rendered_index=rendered,
        source_registry_known=True, source_knowledge_status="source_reviewed_known", semantic_optimal=False)
    result["event_decision"].update(status="source_reviewed_known", registry_known=True,
        source_registry_known=True, selected_option_number=native + 1,
        selected_native_option_index=native, selected_rendered_index=rendered,
        classification="source-analyzed-independence-refusal-policy",
        source_reviewed_policy="independence_refuse_preserve_realm_accept_war_risk",
        semantic_optimal=False, material_effects_verified=False, registry_contract_accepted=False)
    result["unhandled_event_fallback"].update(
        policy="source-analyzed-independence-refuse-preserve-realm", registry_known=True,
        offline_followup_required=False,
        source_knowledge={
            "status": "independence0001_source_reviewed_current_binding",
            "binding": current, "binding_fingerprint": _fingerprint(current),
            "source_review_fingerprint": _fingerprint(REVIEW),
            "prior_source_knowledge": deepcopy(prior_audit),
            "review_kind": "static_source_without_invented_incident",
            "loaded_definition_bytes_verified": False, "live_qualification": False,
            "material_effects_verified": False, "registry_contract_accepted": False})
    result["unhandled_event_fallback"]["selection"].update(
        rendered_index=rendered, native_option_index=native, option_number=native + 1,
        resolved_name=refuse["resolved_name"], enabled=True, selected_step=step,
        selection_order="source_analyzed_independence_refuse_preserve_realm")
    return result
