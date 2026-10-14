"""Source-bound MCP left-reply continuation and offline incident evidence."""

from __future__ import annotations

import copy
import datetime
import json
from pathlib import Path
import uuid

from .bridge.pending_character_interaction_context_contract import normalize_pending_interaction_id
from .vanilla_events.unhandled_fallback import _write_new_json


SCHEMA = "xar.pending-interaction-left-reply/v1"
GUI_LEFT_REPLY = {
    "game_version": "1.20.0.4",
    "source": "gui/interaction_notification_window.gui",
    "sha256": "a3c946a98346de2f57c5c3408a24bf298329df24a6ab25ec88d893befa1fe6e0",
    "lines": "58-76",
    "normal_channel": [
        {"position": "left", "rendered_index": 0, "button": "reject_button", "action": "reject",
         "onclick": "CharacterInteractionNotificationWindow.Reject", "enabled": "CharacterInteractionNotificationWindow.CanReject",
         "step": "reject-pending-character-interaction"},
        {"position": "right", "rendered_index": 1, "button": "accept_button", "action": "accept",
         "onclick": "CharacterInteractionNotificationWindow.Accept", "enabled": "CharacterInteractionNotificationWindow.CanAccept",
         "step": "accept-pending-character-interaction"},
    ],
    "auto_accept_channel": {"position": "only", "rendered_index": 0, "button": "acknowledge_button",
                            "action": "acknowledge", "step": "acknowledge-pending-character-interaction"},
    "same_order_stock_variants": {
        "gui/interaction_marriage_notification_window.gui": "cb31a53b90b4cfd68145068a0d43780d9287249a6dbe20566c2459610cd07398",
        "gui/interaction_call_ally_notification_window.gui": "79986b774e6ca8957353da4973b0e329ab3424ae8eee0952c9d3b652eaa591bb",
        "gui/interaction_interfere_in_war_notification.gui": "e71c670b16639236349cae33ef92805829eb623f77854fe434a3774e1782729e",
    },
}

# Reviewed entries are added offline after completed batches. This is separate
# from the old nonwar/nonreligious allowlist: clerical chastity IS religious.
PENDING_INTERACTION_REPLY_REGISTRY_V1 = {
    "request_clerical_chastity_interaction": {
        "classification": "reviewed_religious_clerical_chastity_request",
        "preferred_action": "reject",
        "deterministic_key_hash": 1409884230,
        "source": "common/character_interactions/clerical_chastity_interaction.txt",
        "source_sha256": "9a7470b42d2f9bfed8a71932014a4c2f8d6fdcc24277f99f79238c5703010b8a",
        "source_lines": "1-14; on_accept132-221; on_decline223-262",
        "reason": "Owner chooses the source-authored left decline. Acceptance starts a five-year chastity vow path; decline has authored piety/stress/opinion penalties, whose material application is not inferred from reply ACK.",
    },
}


def plan_pending_interaction_left_reply_v1(*, snapshot, context, original_plan, action_steps, registry_state_dir=None):
    """Use current native legality with authored GUI order, never accept by default."""
    if not isinstance(snapshot, dict) or not isinstance(context, dict):
        return None
    pending = snapshot.get("pending_character_interaction")
    if not isinstance(pending, dict):
        return None
    try:
        pending_id = normalize_pending_interaction_id(pending.get("instance_id"))
    except ValueError:
        return None
    if (context.get("status") != "available" or context.get("pending_interaction_id") != pending_id
            or context.get("snapshot_revision") != snapshot.get("native_revision")
            or context.get("date_raw") != snapshot.get("date_raw")):
        return None
    definition = context.get("definition")
    key = definition.get("canonical_key") if isinstance(definition, dict) else None
    known = PENDING_INTERACTION_REPLY_REGISTRY_V1.get(key)
    if (isinstance(known, dict)
            and definition.get("deterministic_key_hash") != known["deterministic_key_hash"]):
        known = None
    offline_registry_audit = {"status": "not_needed"}
    if known is None and registry_state_dir is not None:
        from .pending_interaction_source_registry import load_source_reviewed_interaction_v1
        known, offline_registry_audit = load_source_reviewed_interaction_v1(registry_state_dir, context, GUI_LEFT_REPLY)
    notification = pending.get("auto_accept_notification")
    selected = (GUI_LEFT_REPLY["auto_accept_channel"] if notification is True
                else GUI_LEFT_REPLY["normal_channel"][0] if notification is False else None)
    if selected is None:
        return None
    action, step = selected["action"], selected["step"]
    legality = context.get("legality")
    legal = legality.get(action) if isinstance(legality, dict) else None
    enabled = isinstance(legal, dict) and legal.get("status") == "available" and legal.get("allowed") is True
    reachable = step in set(action_steps or ())
    actor = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    binding = {field: snapshot.get(field) for field in (
        "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "paused", "map_ready",
    )}
    binding["actor_character_id"] = actor.get("character_id") if isinstance(actor, dict) else None
    for field in ("connection_generation", "bridge_pid"):
        binding[field] = snapshot.get(field, diagnostics.get(field) if isinstance(diagnostics, dict) else None)
    capture = {"schema": SCHEMA, "kind": "pending_character_interaction",
        "policy": "user-authorized-native-gui-left-reply", "pending_interaction_id": pending_id,
        "interaction_definition_key": key, "binding": binding, "context": copy.deepcopy(context),
        "gui_binding": copy.deepcopy(GUI_LEFT_REPLY),
        "reply_options": [{**row, "native_legality": copy.deepcopy(legality.get(row["action"])) if isinstance(legality, dict) else None}
                          for row in GUI_LEFT_REPLY["normal_channel"]],
        "selection": {**copy.deepcopy(selected), "native_legal": enabled, "action_reachable": reachable},
        "registry_known": known is not None, "reviewed_rule": copy.deepcopy(known),
        "offline_registry_audit": offline_registry_audit,
        "offline_followup_required": known is None, "original_plan": copy.deepcopy(original_plan),
        "semantic_optimal": False, "native_ai_equivalent": False}
    classification = known["classification"] if known is not None else "uncovered_pending_character_interaction"
    return {"policy": "one-life-turn-v1",
        "phase": ("pending_character_interaction_reviewed_left_reply" if known is not None
                  else "pending_character_interaction_left_fallback") if enabled and reachable
                 else "pending_character_interaction_left_disabled" if not enabled
                 else "pending_character_interaction_left_unsupported",
        "selected_step": step if enabled and reachable else None,
        "reason": (known["reason"] if known is not None else "Capture this unfamiliar native request, then choose the source-authored left reply through MCP under the owner's continuation policy.")
                  if enabled and reachable else "The authored left reply is not currently natively legal or executable; do not substitute the right accept button.",
        "pending_character_interaction": copy.deepcopy(pending),
        "decision": {"classification": classification, "registry_known": known is not None,
                     "selected_action": action if enabled and reachable else None,
                     "selected_step": step if enabled and reachable else None,
                     "display_position": selected["position"], "semantic_optimal": False},
        "unhandled_interaction_fallback": capture}


def capture_pending_interaction_before_v1(state_dir, planned):
    plan = planned.get("plan")
    capture = plan.get("unhandled_interaction_fallback") if isinstance(plan, dict) else None
    if not isinstance(capture, dict):
        return None
    if state_dir is None:
        raise ValueError("pending interaction capture requires the managed state directory")
    binding, selection = capture["binding"], capture["selection"]
    selected = plan.get("selected_step")
    if (planned.get("snapshot_id") != binding.get("snapshot_id")
            or planned.get("revision") != binding.get("revision")
            or selected is not None and (selected != selection["step"] or selection["native_legal"] is not True)):
        raise ValueError("pending interaction capture lost its original planned frame/reply")
    directory = Path(state_dir) / "evidence" / "unhandled-interactions"
    directory.mkdir(parents=True, exist_ok=True)
    incident = uuid.uuid4().hex
    before = {**copy.deepcopy(capture), "incident_id": incident, "stage": "before_submission",
              "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "dispatch_attempted": False}
    receipt = _write_new_json(directory / (incident + ".before.json"), before)
    return {"incident_id": incident, "before": receipt, "directory": str(directory),
            "pending_interaction_id": capture["pending_interaction_id"], "action": selection["action"],
            "binding": copy.deepcopy(binding)}


def capture_pending_interaction_after_v1(ticket, *, outcome=None, error=None):
    if ticket is None:
        return None
    result = outcome.get("result") if isinstance(outcome, dict) else None
    interaction = result.get("interaction_result") if isinstance(result, dict) else None
    remaining = result.get("remaining_pending_character_interaction") if isinstance(result, dict) else None
    acknowledged = isinstance(result, dict) and result.get("accepted") is True
    expected = "acknowledged" if ticket["action"] == "acknowledge" else "rejected"
    advanced = bool(acknowledged and isinstance(interaction, dict)
        and interaction.get("instance_id") == ticket["pending_interaction_id"]
        and interaction.get("status") == expected
        and "remaining_pending_character_interaction" in result
        and (remaining is None or isinstance(remaining, dict) and remaining.get("instance_id") != ticket["pending_interaction_id"])
        and result.get("paused") is True)
    after = {"schema": SCHEMA, "kind": "pending_character_interaction", "incident_id": ticket["incident_id"],
        "stage": "after_response", "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "before": ticket["before"], "command_acknowledged": acknowledged,
        "original_pending_advanced_verified": advanced, "interaction_result": copy.deepcopy(interaction),
        "remaining_pending_character_interaction": copy.deepcopy(remaining),
        "action_receipt": copy.deepcopy({key: result.get(key) for key in (
            "step", "accepted", "status", "request_id", "native_request_id", "snapshot_id", "revision", "paused",
        )}) if isinstance(result, dict) else None,
        "error": {"type": type(error).__name__, "message": str(error)} if error is not None else None,
        "replay_allowed": False, "material_effects_verified": False}
    receipt = _write_new_json(Path(ticket["directory"]) / (ticket["incident_id"] + ".after.json"), after)
    return {"kind": "pending_character_interaction", "incident_id": ticket["incident_id"],
            "before": ticket["before"], "after": receipt, "command_acknowledged": acknowledged,
            "original_pending_advanced_verified": advanced, "replay_allowed": False,
            "material_effects_verified": False}


def collect_completed_interaction_incidents_v1(state_dir, seen_incident_ids=()):
    """Offline batch reader: immutable incident pairs only, never Driver state."""
    directory = Path(state_dir) / "evidence" / "unhandled-interactions"
    seen = set(seen_incident_ids)
    incidents = []
    for path in sorted(directory.glob("*.before.json")):
        incident_id = path.name.removesuffix(".before.json")
        after_path = path.with_name(incident_id + ".after.json")
        if incident_id in seen or not after_path.is_file():
            continue
        before, after = json.loads(path.read_bytes()), json.loads(after_path.read_bytes())
        if before.get("schema") != SCHEMA or after.get("incident_id") != incident_id:
            raise ValueError("pending interaction incident pair identity changed")
        import hashlib
        incidents.append({"incident_id": incident_id, "kind": "pending_character_interaction",
            "interaction_definition_key": before.get("interaction_definition_key"),
            "pending_interaction_id": before["pending_interaction_id"], "selection": before["selection"],
            "registry_known": before["registry_known"], "offline_followup_required": before["offline_followup_required"],
            "original_pending_advanced_verified": after["original_pending_advanced_verified"],
            "before": str(path), "before_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "after": str(after_path), "after_sha256": hashlib.sha256(after_path.read_bytes()).hexdigest()})
    return incidents
