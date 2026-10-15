"""User-authorized continuation of uncovered, currently rendered event cards."""

from __future__ import annotations

import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import uuid

from ..bridge.event_contract import event_option_step


SCHEMA = "xar.unhandled-event-first-rendered/v1"


def plan_unhandled_event_fallback_v1(
    *, snapshot, event_context, event_summary, registry_decision, action_steps,
):
    """Keep source evidence, then choose the first shown rendered option.

    This is the owner's continuation policy, not a semantic optimum or a
    registry-contract acceptance. Disabled rows are skipped; all-disabled stays a diagnosis.
    """
    if not isinstance(snapshot, dict) or not isinstance(event_context, dict):
        return None
    options = event_context.get("options")
    if not isinstance(options, list):
        return None
    shown = [row for row in options if isinstance(row, dict) and row.get("shown") is True]
    if not shown or any(type(row.get("rendered_index")) is not int
                        or row["rendered_index"] < 0 for row in shown):
        return None
    if len({row["rendered_index"] for row in shown}) != len(shown):
        return None
    enabled_shown = [row for row in shown if row.get("enabled") is True]
    first = min(enabled_shown or shown, key=lambda row: row["rendered_index"])
    native = first.get("native_option_index")
    active = snapshot.get("active_event", snapshot.get("current_event"))
    if not isinstance(active, dict):
        return None
    instance = active.get("instance_id")
    count = active.get("option_count")
    if (type(instance) is not int or instance <= 0 or type(count) is not int
            or type(native) is not int or not 0 <= native < count
            or event_context.get("current_event_instance_id") != instance
            or event_context.get("snapshot_revision") != snapshot.get("native_revision")
            or event_context.get("date_raw") != snapshot.get("date_raw")):
        return None
    selected = event_option_step(native + 1)
    actor = snapshot.get("played_character")
    binding = {key: snapshot.get(key) for key in (
        "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id",
        "connection_generation", "bridge_pid", "paused", "map_ready",
    )}
    binding["actor_character_id"] = actor.get("character_id") if isinstance(actor, dict) else None
    diagnostics = snapshot.get("diagnostics")
    if isinstance(diagnostics, dict):
        for key in ("connection_generation", "bridge_pid"):
            if binding.get(key) is None:
                binding[key] = diagnostics.get(key)
    capture = {
        "schema": SCHEMA,
        "policy": "user-authorized-capture-then-first-rendered-option",
        "event_definition_key": event_context.get("event_definition_key"),
        "current_event_instance_id": instance,
        "binding": binding,
        "snapshot_option_count": count,
        "window_context": copy.deepcopy({key: event_context.get(key) for key in (
            "schema", "schema_version", "status", "unavailable_reason", "window_match_count",
            "event_definition_key", "calculated_event_id", "runtime_stats_ordinal",
            "current_event_instance_id", "snapshot_revision", "date_raw", "root_scope",
            "saved_scopes", "readiness", "options", "provenance",
        )}),
        "original_registry_decision": copy.deepcopy(registry_decision),
        "selection": {"rendered_index": first["rendered_index"],
                      "native_option_index": native, "option_number": native + 1,
                      "resolved_name": first.get("resolved_name"), "enabled": first.get("enabled"),
                      "selected_step": selected,
                      "selection_order": "native_rendered_index_after_shown_enabled_filter",
                      "excluded_disabled_rendered_indices": [row["rendered_index"] for row in shown if row.get("enabled") is not True]},
        "semantic_optimal": False,
        "native_ai_equivalent": False,
        "offline_followup_required": True,
    }
    summary = copy.deepcopy(event_summary)
    summary.update(selected_option_number=native + 1, selected_native_option_index=native,
                   selected_rendered_index=first["rendered_index"], semantic_optimal=False)
    enabled = first.get("enabled") is True
    advertised = selected in set(action_steps or ())
    return {
        "policy": "one-life-turn-v1",
        "phase": ("active_event_unhandled_first_rendered_option" if enabled and advertised
                  else "active_event_unhandled_first_rendered_disabled" if not enabled
                  else "active_event_unhandled_first_rendered_unsupported"),
        "selected_step": selected if enabled and advertised else None,
        "reason": ("Uncovered event: capture the current card, select its first enabled rendered option under the owner's continuation instruction, then review offline."
                   if enabled and advertised else "No shown native event option is enabled."
                   if not enabled else "The first rendered option has no advertised native selection step."),
        "active_event": summary,
        "event_decision": {"status": "user_authorized_fallback", "event_definition_key": capture["event_definition_key"],
                           "selected_native_option_index": native, "selected_option_number": native + 1,
                           "selected_rendered_index": first["rendered_index"], "semantic_optimal": False},
        "unhandled_event_fallback": capture,
    }


def _write_new_json(path, value):
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if path.exists():
        temporary.unlink()
        raise FileExistsError(str(path))
    os.replace(temporary, path)
    return {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def capture_unhandled_event_before_v1(state_dir, planned):
    plan = planned.get("plan") if isinstance(planned, dict) else None
    capture = plan.get("unhandled_event_fallback") if isinstance(plan, dict) else None
    if not isinstance(capture, dict):
        return None
    if state_dir is None:
        raise ValueError("unhandled event capture requires the managed state directory")
    selected = plan.get("selected_step")
    selection = capture.get("selection")
    binding = capture.get("binding")
    if (capture.get("schema") != SCHEMA or not isinstance(selection, dict)
            or (selected is not None and selected != selection.get("selected_step"))
            or (selected is not None and selection.get("enabled") is not True) or not isinstance(binding, dict)
            or planned.get("snapshot_id") != binding.get("snapshot_id")
            or planned.get("revision") != binding.get("revision")):
        raise ValueError("unhandled event capture lost its original planned selection/frame")
    directory = Path(state_dir) / "evidence" / "unhandled-events"
    directory.mkdir(parents=True, exist_ok=True)
    incident = uuid.uuid4().hex
    before = {**copy.deepcopy(capture), "incident_id": incident, "stage": "before_submission",
              "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "dispatch_attempted": False}
    receipt = _write_new_json(directory / (incident + ".before.json"), before)
    return {"incident_id": incident, "before": receipt, "directory": str(directory),
            "current_event_instance_id": capture["current_event_instance_id"],
            "selected_native_option_index": selection["native_option_index"]}


def capture_unhandled_event_after_v1(ticket, *, outcome=None, error=None):
    if ticket is None:
        return None
    result = outcome.get("result") if isinstance(outcome, dict) else None
    selection = result.get("event_selection") if isinstance(result, dict) else None
    verified = bool(
        isinstance(result, dict) and result.get("accepted") is True
        and isinstance(selection, dict) and selection.get("status") == "event_instance_advanced"
        and selection.get("postcondition_verified") is True
        and selection.get("old_event_instance_id") == ticket["current_event_instance_id"]
        and selection.get("new_event_instance_id") != ticket["current_event_instance_id"]
        and selection.get("selected_native_option_index") == ticket["selected_native_option_index"]
    )
    after = {"schema": SCHEMA, "incident_id": ticket["incident_id"], "stage": "after_response",
             "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "before": ticket["before"], "command_acknowledged": isinstance(result, dict) and result.get("accepted") is True,
             "event_instance_advanced_verified": verified,
             "result_status": outcome.get("status") if isinstance(outcome, dict) else None,
             "event_selection": copy.deepcopy(selection),
             "action_receipt": copy.deepcopy({key: result.get(key) for key in (
                 "step", "accepted", "status", "query_sequence", "request_id", "native_request_id",
                 "snapshot_id", "revision", "progress_status",
             )}) if isinstance(result, dict) else None,
             "error": {"type": type(error).__name__, "message": str(error)} if error is not None else None,
             "replay_allowed": False}
    receipt = _write_new_json(Path(ticket["directory"]) / (ticket["incident_id"] + ".after.json"), after)
    return {"incident_id": ticket["incident_id"], "before": ticket["before"], "after": receipt,
            "command_acknowledged": after["command_acknowledged"],
            "event_instance_advanced_verified": verified, "replay_allowed": False}
