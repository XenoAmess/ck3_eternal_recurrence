"""Four fixed HolySite decision cooldowns, independent of an open detail window."""
from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .holy_site_decision_action_v1 import (
    HolySiteDecisionActionV1, holy_site_decision_key_v1, normalize_holy_site_decision_action_v1,
)
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_holy_site_private_transport import _availability, _ref
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

STEP = "query-player-holy-site-decision-cooldown-v1"
PERMISSION = "allow_private_holy_site_adoption_detail_query"


def normalize_holy_site_decision_cooldown_v1(
    value: object, *, snapshot: Mapping[str, object], action: HolySiteDecisionActionV1,
) -> dict[str, object]:
    action = normalize_holy_site_decision_action_v1(action)
    expected_key = holy_site_decision_key_v1(action)
    result = _availability(value, "HolySite decision cooldown")
    if (result.get("schema") != "ck3_12004_holy_site_decision_cooldown_v1"
            or require_exact_native_build(result.get("game_version"), result.get("executable_sha256")) != CK3_12004
            or private_native_build_identity(snapshot) != CK3_12004):
        raise ValueError("HolySite decision cooldown requires exact 1.20.0.4")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping) or type(result.get("played_character_id")) is not int
            or result["played_character_id"] != actor.get("character_id")
            or type(result.get("date_raw")) is not int or result["date_raw"] != snapshot.get("date_raw")
            or type(result.get("capture_epoch")) is not int or result["capture_epoch"] <= 0):
        raise ValueError("HolySite decision cooldown crossed its current player/frame")
    _ref(result["played_character_id"], "cooldown player", nullable=False)
    if result.get("action") != action or result.get("decision_key") != expected_key:
        raise ValueError("HolySite decision cooldown differs from its fixed requested action")
    if result.get("read_only") is not True:
        raise ValueError("HolySite cooldown query lost readonly semantics")
    for field in ("detail_open_required", "action_ready", "decision_confirm_invoked", "adoption_completed_observed"):
        if result.get(field) is not False:
            raise ValueError("HolySite cooldown read claimed a detail/action/postcondition")
    observed = result.get("native_decision_cooldown_observed")
    cooldown = result.get("native_decision_cooldown")
    if type(observed) is not bool or observed != result["available"]:
        raise ValueError("HolySite cooldown source availability differs")
    if not observed:
        if cooldown is not None:
            raise ValueError("unobserved HolySite cooldown must remain unknown")
        return result
    fields = {"decision_key", "present", "expiry_raw", "current_counter_raw", "active", "counter_unit", "calendar_conversion_observed"}
    if (not isinstance(cooldown, dict) or set(cooldown) != fields or cooldown["decision_key"] != expected_key
            or type(cooldown["present"]) is not bool or type(cooldown["active"]) is not bool
            or cooldown["counter_unit"] != "native_decision_clock_counter"
            or cooldown["calendar_conversion_observed"] is not False
            or type(cooldown["current_counter_raw"]) is not int
            or not -(1 << 31) <= cooldown["current_counter_raw"] < (1 << 31)):
        raise ValueError("native HolySite cooldown raw fields are malformed")
    expiry = cooldown["expiry_raw"]
    if cooldown["present"]:
        if (type(expiry) is not int or not -(1 << 31) <= expiry < (1 << 31)
                or cooldown["active"] != (cooldown["current_counter_raw"] < expiry)):
            raise ValueError("native HolySite cooldown lost its original signed comparison")
    elif expiry is not None or cooldown["active"] is not False:
        raise ValueError("absent HolySite cooldown acquired an expiry")
    return result


def query_holy_site_decision_cooldown_private_v1(
    driver: object, *, expected_revision: int, action: HolySiteDecisionActionV1,
) -> dict[str, object]:
    action = normalize_holy_site_decision_action_v1(action)
    before, envelope = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"action": action}, include_native_command_history=False,
    )
    try:
        if (require_exact_native_backend(envelope.get("game_version"), envelope.get("executable_sha256"),
                envelope.get("backend_id"), suffix="player-holy-site-decision-cooldown-v1") != CK3_12004
                or envelope.get("domain_key") != "player_holy_site_decision_cooldown_v1"
                or envelope.get("snapshot_revision") != before.get("native_revision")
                or envelope.get("date_raw") != before.get("date_raw")):
            raise ValueError("native HolySite cooldown envelope differs from exact frame")
        value = normalize_holy_site_decision_cooldown_v1(
            envelope.get("player_holy_site_decision_cooldown"), snapshot=before, action=action,
        )
        if envelope.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native HolySite cooldown envelope loses source availability")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": envelope["snapshot_revision"], "backend_id": envelope["backend_id"],
            "domain_key": envelope["domain_key"], "status": envelope["status"], "advertised": False}
