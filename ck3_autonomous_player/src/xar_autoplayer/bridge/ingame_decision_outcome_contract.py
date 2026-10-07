"""Generic selected-player decision outcomes, never product business acceptance.

The native command proves sole receiver admission and one attempted dispatch.
Only independent later native reads can prove the requested UI outcome. An
unknown claim survives every revision/reconnect and is never replayed.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .ingame_decision_item_action_contract import CONFIRM_STEP, normalize_decision_action
from .event_window_context_contract import normalize_current_event_window_context_v1

STEP = "confirm-ingame-decision-outcome-v1"
CAPABILITY = "game.command.confirm-ingame-decision-outcome-v1"
SCHEMA = "ck3-ingame-decision-outcome-confirm-v1"
OUTCOMES = {"event_window", "decision_closed"}


def validate_expected_outcome(outcome: object, event_key: object) -> str:
    if not isinstance(outcome, str) or outcome not in OUTCOMES:
        raise ValueError("unsupported typed decision outcome")
    if outcome == "decision_closed":
        if event_key is not None:
            raise ValueError("decision_closed must not request an event definition")
        return ""
    if (not isinstance(event_key, str) or len(event_key) > 192
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[0-9]{1,10}", event_key) is None):
        raise ValueError("event_window requires an exact namespace.numeric event key")
    return event_key


def normalize_outcome_ack(raw: object, binding: dict[str, object], decision_key: str,
                          outcome: str, event_key: str) -> dict[str, object]:
    if (not isinstance(raw, dict) or raw.get("schema") != SCHEMA
            or raw.get("step") != STEP or raw.get("action") != "confirm_outcome"
            or raw.get("expected_outcome") != outcome
            or raw.get("expected_event_definition_key") != event_key
            or raw.get("postcondition_verified") is not False
            or raw.get("verification_pending") is not True
            or raw.get("status") != "acknowledged_verification_pending"
            or raw.get("no_blocking_modal_verified") is not True):
        raise ValueError("malformed generic decision dispatch acknowledgement")
    # Same actual exact-build receiver/selected model proof as the existing
    # fixed Confirm. The projection is solely validation, not fabricated proof.
    normalize_decision_action({**raw, "schema": "ck3-ingame-decision-item-action-v1",
                               "step": CONFIRM_STEP, "action": "confirm"},
                              binding, decision_key, "confirm")
    return dict(raw)


def outcome_frame_matches(before: dict[str, object], after: dict[str, object],
                          binding: dict[str, object]) -> bool:
    from .ingame_decisions_open_contract import opening_binding
    try:
        later = opening_binding(after)
    except ValueError:
        return False
    # Events/resources can legitimately alter the actual snapshot. Revision
    # equality is deliberately not a postcondition, and a new revision by
    # itself does not prove that any business effect happened.
    invariants = ("connection_generation", "game_pid", "played_character_id",
                  "date_raw", "episode_run_id")
    return (all(later[key] == binding[key] for key in invariants)
            and later["native_revision"] >= binding["native_revision"]
            and after.get("speed") == before.get("speed"))


def actual_expected_event(raw: object, snapshot: dict[str, object], binding: dict[str, object],
                          expected_key: str) -> bool:
    active = snapshot.get("active_event")
    instance = active.get("instance_id") if isinstance(active, dict) else None
    if (type(instance) is not int or not 1 <= instance <= 2**31 - 1
            or not isinstance(raw, dict)
            or raw.get("current_event_window_context_ready") is not True
            or raw.get("queried_revision") != snapshot.get("revision")
            or raw.get("queried_native_revision") != snapshot.get("native_revision")):
        return False
    try:
        context = normalize_current_event_window_context_v1(
            raw.get("current_event_window_context"),
            expected_event_instance_id=instance,
            expected_date_raw=binding["date_raw"],
            expected_snapshot_revision=snapshot["native_revision"])
    except (ValueError, KeyError):
        return False
    root = context.get("root_scope")
    identity = root.get("typed_identity") if isinstance(root, dict) else None
    ready = context.get("readiness")
    return (context.get("status") == "available"
            and context.get("event_definition_key") == expected_key
            and isinstance(identity, dict)
            and identity.get("status") == "available"
            and identity.get("kind") == "character"
            and type(identity.get("character_id")) is int
            and identity["character_id"] == binding["played_character_id"]
            and isinstance(ready, dict)
            and ready.get("event_definition_identity_ready") is True
            and ready.get("root_scope_ready") is True
            and ready.get("option_presentation_ready") is True)


def actual_closed_decision_detail(raw: object) -> bool:
    if (not isinstance(raw, dict)
            or raw.get("schema") != "ck3-native-gui-window-tree-inspection-v1"
            or raw.get("window_kind") != "decision_detail"
            or raw.get("scope_root_name") != "decisiondetail_view"
            or raw.get("read_only") is not True
            or raw.get("root_available") is not True or raw.get("truncated") is not False):
        return False
    rows = raw.get("widgets")
    if (not isinstance(rows, list) or type(raw.get("widget_count")) is not int
            or raw["widget_count"] != len(rows) or not 1 <= len(rows) <= 2048):
        return False
    roots = [row for row in rows if isinstance(row, dict) and row.get("child_path") == ""]
    return (len(roots) == 1 and roots[0].get("runtime_name") == "decisiondetail_view"
            and roots[0].get("effective_visible") is False)


def reject_unresolved_claims(directory: Path, identity: dict[str, object], *,
                             current_binding: dict[str, object] | None = None) -> None:
    """Unknown results block all later revisions for the same semantic action."""
    base = {key: identity[key] for key in ("game_pid", "actor_id", "episode_run_id",
                                          "decision_key", "action")}
    # Both APIs dispatch the same real Confirm receiver. Changing from the
    # fixed modal route to the generic outcome route cannot bypass an unknown
    # submission, or vice versa.
    if base["action"] == "confirm_outcome":
        base["action"] = "confirm"
    for claim in directory.glob("*.claim.json"):
        try:
            value = json.loads(claim.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ValueError("decision action claim evidence is unreadable") from error
        previous = value.get("action_identity")
        if not isinstance(previous, dict):
            # Historical claims carried binding/key/action rather than the
            # explicit identity. They must not become retryable after upgrade.
            bound = value.get("binding", {})
            previous = {"game_pid": bound.get("game_pid"),
                        "actor_id": bound.get("played_character_id"),
                        "episode_run_id": bound.get("episode_run_id"),
                        "decision_key": value.get("decision_key", ""),
                        "action": value.get("action", "open")}
        if previous.get("action") == "confirm_outcome":
            previous = {**previous, "action": "confirm"}
        if any(previous.get(key) != val for key, val in base.items()):
            continue
        verified_path = claim.with_suffix(".verified.json")
        try:
            verified = json.loads(verified_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            from .ingame_decision_predispatch_contract import allows_later_select
            if allows_later_select(claim, value, identity, current_binding):
                continue
            raise ValueError("decision action already claimed with an unresolved result; no retry at any revision") from error
        except (OSError, ValueError) as error:
            raise ValueError("decision action already claimed with an unresolved result; no retry at any revision") from error
        result = verified.get("result")
        if (verified.get("request_id") != value.get("request_id")
                or not isinstance(result, dict) or result.get("postcondition_verified") is not True
                or result.get("verification_pending") is not False
                or result.get("action_claim_path") != str(claim)):
            raise ValueError("decision action verification evidence is invalid; no retry")


def preserve_verified_claim(claim: Path, request_id: str, result: dict[str, object]) -> None:
    with claim.with_suffix(".verified.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"schema": "ck3-ingame-decision-action-independent-verification-v1",
                   "request_id": request_id, "result": result}, stream,
                  ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
