"""Opt-in, fail-closed stop after one exact war move and independent readback."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .errors import AgentError
from .strategy import _normalized_remaining_route


SCHEMA = "xar.ck3.exact-war-move-stop.v1"
PHASE = "native_war_general_battle_distant_route_start"
FIELDS = frozenset({
    "schema", "date_raw", "war_id", "army_id", "origin_province_id",
    "target_province_id", "source_save_sha256", "source_driver_sha256",
})


def validate_contract(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != FIELDS or value.get("schema") != SCHEMA:
        raise AgentError("exact war move stop contract has an unexpected schema or fields")
    for key in ("date_raw", "war_id", "army_id", "origin_province_id", "target_province_id"):
        number = value.get(key)
        if isinstance(number, bool) or not isinstance(number, int) or number <= 0:
            raise AgentError(f"exact war move stop contract has invalid {key}")
    if value["origin_province_id"] == value["target_province_id"]:
        raise AgentError("exact war move stop target equals origin")
    for key in ("source_save_sha256", "source_driver_sha256"):
        digest = value.get(key)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
            raise AgentError(f"exact war move stop contract has invalid {key}")
    return dict(value)


def read_contract(path: Path, expected_sha256: str) -> dict[str, object]:
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in expected_sha256):
        raise AgentError("exact war move stop contract requires a SHA-256 binding")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256.lower():
        raise AgentError("exact war move stop contract SHA-256 changed")
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise AgentError("exact war move stop contract is not valid UTF-8 JSON") from error
    return validate_contract(value)


def expected_step(contract: dict[str, object]) -> str:
    return f"move-army-{contract['army_id']}-to-{contract['target_province_id']}"


def _army_membership(snapshot: dict[str, object], contract: dict[str, object], *, origin: int) -> dict[str, object]:
    armies = snapshot.get("player_armies")
    wars = snapshot.get("active_wars")
    if not isinstance(armies, list) or not isinstance(wars, list) or len(wars) != 1:
        raise AgentError("exact war move lacks one complete player army and war roster")
    matching = [army for army in armies if isinstance(army, dict) and army.get("army_id") == contract["army_id"]]
    war = wars[0]
    allies = war.get("allied_armies") if isinstance(war, dict) else None
    if not isinstance(war, dict) or war.get("war_id") != contract["war_id"] or not isinstance(allies, list):
        raise AgentError("exact war move lost its bound WarID")
    war_matching = [army for army in allies if isinstance(army, dict) and army.get("army_id") == contract["army_id"]]
    if not (len(matching) == len(war_matching) == 1
            and matching[0].get("controllable") is True
            and war_matching[0].get("controllable") is True
            and matching[0].get("current_province_id") == origin
            and war_matching[0].get("current_province_id") == origin):
        raise AgentError("exact war move ArmyID, control, or origin differs from war roster")
    return matching[0]


def check_before(candidate: dict[str, object], before: dict[str, object], contract: dict[str, object]) -> bool:
    """Allow read-only discovery; authorize only the exact formal planner move."""
    selected = candidate.get("selected_step")
    plan = candidate.get("plan")
    if not isinstance(selected, str) or candidate.get("snapshot_id") != before.get("snapshot_id") or candidate.get("revision") != before.get("revision"):
        raise AgentError("exact war move candidate is not bound to the current frame")
    if not (before.get("date_raw") == contract["date_raw"] and before.get("paused") is True
            and before.get("map_ready") is True and before.get("one_life_terminal") is not True):
        raise AgentError("exact war move pre-submit frame changed date or readiness")
    semantic = before.get("_semantic")
    if not isinstance(semantic, dict):
        raise AgentError("exact war move pre-submit semantic roster is absent")
    _army_membership(semantic, contract, origin=contract["origin_province_id"])
    if selected.startswith("query-") or selected.startswith(f"preview-move-army-{contract['army_id']}-to-"):
        return False
    if selected != expected_step(contract):
        raise AgentError(f"exact war move refuses other action {selected!r}")
    if not (isinstance(plan, dict) and plan.get("phase") == PHASE
            and plan.get("source_war_id") == contract["war_id"]
            and plan.get("selected_step") == selected
            and plan.get("contact_recheck_required_before_each_day") is True
            and plan.get("future_contact_authorized") is False
            and plan.get("general_battle_forecast_used_for_decision") is True):
        raise AgentError("exact war move formal planner gate is incomplete")
    return True


def check_poststate(before: dict[str, object], result: object, after: dict[str, object], contract: dict[str, object]) -> dict[str, object]:
    if not isinstance(result, dict) or result.get("step") != expected_step(contract) or result.get("status") != "submitted" or result.get("accepted") is not True:
        raise AgentError("exact war move typed submission was not accepted")
    action = result.get("war_action")
    if not (isinstance(action, dict) and action.get("status") == "moving"
            and action.get("army_id") == contract["army_id"]
            and action.get("target_province_id") == contract["target_province_id"]
            and action.get("submitted_date_raw") == contract["date_raw"]):
        raise AgentError("exact war move typed ACK differs from its bound action")
    if not (after.get("snapshot_id") != before.get("snapshot_id")
            and isinstance(after.get("native_revision"), int)
            and isinstance(before.get("native_revision"), int)
            and after["native_revision"] > before["native_revision"]
            and after.get("date_raw") == contract["date_raw"]
            and after.get("paused") is True and after.get("map_ready") is True
            and after.get("episode_run_id") == before.get("episode_run_id")
            and after.get("episode_character_id") == before.get("episode_character_id")
            and after.get("one_life_terminal") is not True):
        raise AgentError("exact war move lacks an independent same-date paused postframe")
    army = _army_membership(after, contract, origin=contract["origin_province_id"])
    route = _normalized_remaining_route(army)
    if army.get("move_target_province_id") != contract["target_province_id"] or route != [contract["target_province_id"]]:
        raise AgentError("exact war move postframe lacks the exact single-hop route")
    return {
        "status": "independent_poststate_verified",
        "step": expected_step(contract),
        "war_id": contract["war_id"],
        "army_id": contract["army_id"],
        "date_raw": contract["date_raw"],
        "snapshot_id": after["snapshot_id"],
        "native_revision": after["native_revision"],
        "origin_province_id": contract["origin_province_id"],
        "move_target_province_id": contract["target_province_id"],
        "remaining_route_province_ids": route,
    }


def check_checkpoint(checkpoint: dict[str, object], snapshot: dict[str, object], contract: dict[str, object]) -> dict[str, object]:
    if checkpoint.get("date_raw") != contract["date_raw"] or snapshot.get("date_raw") != contract["date_raw"] or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise AgentError("exact war move checkpoint changed date or readiness")
    army = _army_membership(snapshot, contract, origin=contract["origin_province_id"])
    route = _normalized_remaining_route(army)
    if army.get("move_target_province_id") != contract["target_province_id"] or route != [contract["target_province_id"]]:
        raise AgentError("exact war move checkpoint lost the single-hop route")
    return {"status": "checkpoint_verified", "date_raw": contract["date_raw"], "snapshot_id": snapshot.get("snapshot_id"), "move_target_province_id": contract["target_province_id"], "remaining_route_province_ids": route}
