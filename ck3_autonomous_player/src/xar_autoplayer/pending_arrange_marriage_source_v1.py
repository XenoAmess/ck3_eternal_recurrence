"""Exact .4 source metadata for the existing marriage reject-only rule.

This updates knowledge, not reply eligibility. Native accept legality does not
provide a secondary-pair outcome, and no material effect is inferred from ACK.
"""
from copy import deepcopy

from .bridge.version_identity import CK3_12004


KEY = "arrange_marriage_interaction"
KEY_HASH = 1_298_930_137
SOURCE_SHA256 = "9481FD44A078F2D06034DD4A2107FE183F231D2B49D8B90F106C1D54F7A501F0"
DEFINITION_SHA256 = "5927c5d4e719bb04a645d47c4e79544bf3e72f76be5c60e8bd6ad5ad59b0301a"
DECLINE_SHA256 = "8390846f7a5c14848079abcd079d2fca1d801214011e80da44786d4788c1ace1"
SEND_OPTIONS_SHA256 = "c462de92849c534ab85391b020e288470de75a1b65693a313051493827ae5731"


def source_reviewed_arrange_marriage_evidence_v1(context, historical_evidence):
    """Preserve historical entries; attach current source only to exact .4 input.

    The caller still runs the original roles/deadline/options/legality guards.
    This function emits no action and does not validate loaded definition bytes.
    """
    if not isinstance(historical_evidence, dict) or not isinstance(context, dict):
        return historical_evidence
    build = context.get("build", {})
    definition = context.get("definition", {})
    provenance = context.get("provenance", {})
    if (not all(isinstance(v, dict) for v in (build, definition, provenance))
            or build.get("version") != CK3_12004.game_version
            or build.get("exe_sha256") != CK3_12004.executable_sha256
            or definition.get("canonical_key") != KEY
            or type(definition.get("deterministic_key_hash")) is not int
            or definition["deterministic_key_hash"] != KEY_HASH
            or provenance.get("backend_id") != CK3_12004.backend_id("pending-character-interaction-context-v1")):
        return historical_evidence
    result = deepcopy(historical_evidence)
    result.update(source_sha256=SOURCE_SHA256,
        source_policy="ck3-1.20.0.4-explicit-marriage-special-reject-only-v1",
        build={"version": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256},
        native_backend_id=provenance["backend_id"],
        source_knowledge={
            "schema": "xar.arrange-marriage-reject-only-source-review/v1",
            "status": "offline-source-reviewed", "action_scope": "existing_reject_only",
            "canonical_key": KEY, "deterministic_key_hash": KEY_HASH,
            "source_relative": "common/character_interactions/00_marriage_interactions.txt",
            "source_sha256": SOURCE_SHA256, "definition_sha256": DEFINITION_SHA256,
            "on_decline_sha256": DECLINE_SHA256,
            "send_option_count": 6, "send_option_catalogue_sha256": SEND_OPTIONS_SHA256,
            "decline_event_source": "events/interaction_events/marriage_interaction_events.txt",
            "decline_event_source_sha256": "78c367ba0b32a374e5be5d88f7660e7898ef9dbc44412049521f64a472e4dca5",
            "decline_event_definition_sha256": "6f21ff04501d9ba75caf19e1274b772749e1fd00d748fd29a610feb08029e86f",
            "historical_source_sha256": historical_evidence.get("source_sha256"),
            "loaded_definition_bytes_verified": False, "accept_outcome_qualified": False,
            "material_effects_verified": False,
        })
    result["known_decline_effects"] = [
        "puppet_or_actor!=recipient:marriage_interaction.0011",
        "puppet_or_actor:if_grand_wedding_promise_pending:remove_variable",
        "secondary_actor:player_declined_marriage:5y",
    ]
    return result


def is_blocked_arrange_marriage_reply_v1(plan):
    """A dedicated reject-only diagnosis cannot be replaced by generic accept."""
    decision = plan.get("decision")
    return (plan.get("selected_step") is None
            and plan.get("phase") == "pending_character_interaction_degraded_blocked"
            and isinstance(decision, dict)
            and (decision.get("classification") == "known_marriage_special"
                 or decision.get("classification") == "evidence_invalid"
                 and decision.get("interaction_key") == KEY
                 and bool(decision.get("marriage_contract_gaps")))
            and isinstance(decision.get("definition_classification"), dict)
            and decision["definition_classification"].get("definition_key") == KEY)


def continue_without_blocked_marriage_reply_v1(plan, *, snapshot, action_steps, choose_ordinary):
    """Defer only this notification; preserve the diagnosis and full core policy.

    The caller has already applied lifecycle, mandatory-window and event priority.
    No observed frame is changed and no pending interaction command is offered to
    the ordinary core. A projection is planning input, not a cleared-window claim.
    """
    if not is_blocked_arrange_marriage_reply_v1(plan) or not isinstance(snapshot, dict):
        return plan
    pending = snapshot.get("pending_character_interaction")
    modal = snapshot.get("top_exclusive_modal_choice_hint")
    if (not isinstance(pending, dict) or pending.get("auto_accept_notification") is not False
            or pending.get("instance_id") != plan["decision"].get("pending_interaction_id")
            or isinstance(modal, dict) and modal.get("status") == "present"
            or snapshot.get("active_event") is not None or snapshot.get("current_event") is not None):
        return plan
    pending_steps = {f"{action}-pending-character-interaction"
                     for action in ("accept", "reject", "block", "acknowledge")}
    pending_steps.add("query-pending-character-interaction-context-v1")
    ordinary_steps = tuple(step for step in action_steps if step not in pending_steps)
    ordinary = choose_ordinary({**snapshot, "pending_character_interaction": None}, ordinary_steps)
    selected = ordinary.get("selected_step")
    if (not isinstance(selected, str) or selected not in ordinary_steps
            or selected in pending_steps or str(ordinary.get("phase", "")).startswith("pending_")):
        return plan
    return {**ordinary, "deferred_pending_interaction": deepcopy(plan),
            "notification_continuation": {"policy": "blocked-marriage-reply-ordinary-continuation-v1",
                "pending_interaction_id": pending["instance_id"], "interaction_submission": False,
                "observed_notification_cleared": False, "planning_projection_only": True}}
