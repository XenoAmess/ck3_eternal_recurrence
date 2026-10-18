"""Adapt one same-process Crown receipt schema to a complete host consumer.

This leaf performs no I/O, SDK import, action, or queue mutation. ``None``
delegates to the unchanged host route, including cold recovery. The callback
must be the host's complete original Crown validator, not an ACK classifier.
"""


def classify_pending_material_crown_schema_v1(
    body, *, classify_original, state=None, initial_frame=None, game_pid=None
):
    """Return the original ``(credit, state)`` with explicit schema provenance."""
    import hashlib
    import json

    plan = body.get("plan") if isinstance(body, dict) else None
    if (not isinstance(plan, dict)
            or plan.get("policy") != "pending-material-publication-v1"
            or plan.get("phase") != "pending_material_independent_receipt"
            or body.get("selected_step") != "verify-realm-law-crown-v1-private"
            or "crown_cold_recovery" in plan):
        return None
    material = plan.get("pending_material")
    # A cold receipt belongs to the original host recovery. It must never be
    # recast as the same-process, tracked receipt handled here.
    if isinstance(material, dict) and material.get("status") == "cold_receipt":
        return None

    def require(condition, reason):
        if not condition:
            raise ValueError("pending-material Crown schema denied: " + reason)

    pending = plan.get("crown_pending_action")
    tracked = state.get("crown_pending") if isinstance(state, dict) else None
    source = body.get("planning_source_frame")
    receipt = body.get("result")
    require(callable(classify_original), "complete original consumer absent")
    require(body.get("status") == "executed"
            and plan.get("selected_step") == body["selected_step"],
            "typed independent receipt absent")
    require(isinstance(pending, dict) and isinstance(tracked, dict)
            and isinstance(material, dict), "original tracked action absent")
    require(isinstance(initial_frame, dict) and isinstance(source, dict)
            and isinstance(receipt, dict), "current campaign binding absent")
    require(material.get("status") == "ready"
            and material.get("domain") == "crown"
            and material.get("pending") == pending
            and material.get("same_process") is True
            and material.get("business_credit") is False,
            "same-process pending-material contract differs")
    require(pending.get("stage") == "receipt_pending"
            and pending.get("source_context") == {
                "bridge_pid": game_pid,
                "episode_run_id": initial_frame.get("episode_run_id")},
            "original process context differs")
    require(tracked.get("game_pid") == game_pid
            and tracked.get("actor_character_id")
            == initial_frame.get("actor_character_id")
            == source.get("actor_character_id")
            and tracked.get("episode_run_id")
            == initial_frame.get("episode_run_id")
            == source.get("episode_run_id"), "actor or episode differs")
    require(all(pending.get(key) == tracked.get(key) for key in (
        "action_id", "law_key", "readback", "choice", "ack",
        "pre_native_revision", "pre_date_raw", "actor_character_id",
        "episode_run_id")), "original tracked action fields differ")
    choice = tracked.get("choice")
    require(isinstance(choice, dict)
            and isinstance(choice.get("budgets_raw"), (list, tuple)),
            "original quote absent")
    require(pending.get("budgets") == dict(choice["budgets_raw"])
            and material.get("pre_native_revision")
            == pending.get("pre_native_revision")
            and material.get("observed_native_revision")
            == source.get("native_revision")
            and source.get("bridge_pid") == game_pid,
            "budget or observation binding differs")

    # Only the validation view receives this legacy discriminator. The
    # original plan and full Native receipt are left unchanged. The complete
    # host consumer still checks IDs, source quote, exact debit, native build,
    # independent frame, law and successor proof before producing any credit.
    view = {**body, "plan": {**plan, "crown_cold_recovery": False}}
    credit, updated_state = classify_original(
        view, state=state, initial_frame=initial_frame, game_pid=game_pid)
    require(isinstance(credit, dict), "original consumer returned no record")
    provenance = {
        "schema": "xar.queue.pending-material-crown-schema-adapter/v1",
        "original_body_sha256": hashlib.sha256(json.dumps(
            body, ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest(),
        "derived_validation_view_only": True,
        "derived_legacy_discriminator": {"crown_cold_recovery": False},
        "original_plan_or_Native_receipt_changed": False,
        "complete_original_consumer_called": True,
        "paired_after_metrics_still_required": True,
        "replay_allowed": False,
    }
    return {
        **credit, "pending_material_crown_schema_adapter": provenance
    }, updated_state
