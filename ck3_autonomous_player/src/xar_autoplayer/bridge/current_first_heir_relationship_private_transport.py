"""Unadvertised current first-heir relationship read for the selected native build.

This query binds the heir through the public campaign-root observation. It
does not enumerate final-legal candidates, accept an arbitrary CharacterID,
or use a proposal pending record.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from .driver import BridgeUnavailableError, UnsupportedStepError
from .current_first_heir_reproductive_inputs_v1 import (
    LEAF as REPRODUCTIVE_INPUTS_LEAF,
    validate_current_first_heir_reproductive_inputs_v1,
)
from .current_first_heir_descendants_v1 import (
    LEAF as DESCENDANTS_LEAF, SUMMARY as DESCENDANTS_SUMMARY,
    summarize_current_first_heir_descendants_v1,
    validate_current_first_heir_descendants_v1,
)
from .marriage_matchmaking_private_transport import _require_same_paused_frame
from .nonwar_private_build import private_native_provenance


STEP = "query-current-first-heir-relationship-v1-private"
SCHEMA = "xar.ck3.current-first-heir-relationship.v1"


def _same_frame_campaign_root_result(
    result: object, snapshot: dict[str, object],
) -> dict[str, object] | None:
    """Reuse a full successful observation only within its planning frame."""
    if not isinstance(result, dict):
        return None
    root = result.get("campaign_root_context")
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, dict) else None
    if not (result.get("status") == "available" and isinstance(root, dict)
            and root.get("status") == "available"
            and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision") == snapshot.get("native_revision")
            and root.get("snapshot_revision") == snapshot.get("native_revision")
            and root.get("date_raw") == snapshot.get("date_raw")
            and root.get("player_character_id") == actor
            and type(result.get("query_sequence")) is int
            and result["query_sequence"] > 0):
        return None
    return result

_PAIR_IDS = ("actor_character_id", "heir_character_id", "partner_character_id",
             "recipient_character_id", "intermediary_character_id")
_ADULT_FIELDS = ("heir_is_adult", "partner_is_adult", "heir_adult_measure_raw",
                 "partner_adult_measure_raw", "heir_adult_threshold_raw",
                 "partner_adult_threshold_raw")
_COST_FIELDS = ("gold_raw", "prestige_raw", "piety_raw", "renown_raw",
                "influence_raw", "herd_raw", "treasury_raw",
                "treasury_or_gold_raw", "merit_raw", "barter_goods_raw")


def _current_child_house_preview(
    value: object, *, heir: int | None, partner: int | None,
    selected: bool | None, effective: bool | None, complete: bool | None,
) -> dict[str, object] | None:
    """Validate an optional prospective lineage from this finalized pair."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise BridgeUnavailableError("current pair child House preview is malformed")
    status = value.get("status")
    reason = value.get("reason")
    fields = ("selected_matrilineal_option", "effective_matrilineal_if_accepted",
              "complete_can_send", "native_selected_parent_character_id",
              "house_id", "dynasty_id")
    if (status not in {"available", "unavailable", "not_applicable"}
            or not isinstance(reason, str)
            or (reason != "" if status == "available" else not reason)
            or any(value.get(key) is not None and (
                type(value[key]) is not int or not 0 < value[key] < 2**31)
                   for key in ("subject_character_id", "candidate_character_id"))
            or value.get("subject_character_id") != heir
            or value.get("candidate_character_id") != partner
            or value.get("requested_matrilineal_option") is not False):
        raise BridgeUnavailableError("current pair child House preview identity changed")
    if status == "available":
        if (partner is None or type(selected) is not bool
                or any(type(value.get(key)) is not bool for key in fields[:3])
                or value["selected_matrilineal_option"] is not selected
                or value["effective_matrilineal_if_accepted"] is not effective
                or value["complete_can_send"] is not complete
                or type(value.get("native_selected_parent_character_id")) is not int
                or value["native_selected_parent_character_id"] not in (heir, partner)
                or any(value.get(key) is not None and (
                    type(value[key]) is not int or not 0 <= value[key] < 2**31)
                       for key in fields[4:])):
            raise BridgeUnavailableError("current pair child House preview values are malformed")
    elif (any(value.get(key) is not None for key in fields)
          or (status == "not_applicable" and partner is not None)):
        raise BridgeUnavailableError("unavailable current pair child House preview is malformed")
    return dict(value)


def _current_pair_actionability(
    value: object, *, actor: int, heir: int | None, partner: int | None,
) -> dict[str, object]:
    if value is None:
        return {"status": "unavailable",
                "unavailable_reason": "native_readback_not_supplied",
                "actor_character_id": actor, "heir_character_id": heir,
                "partner_character_id": partner,
                "adult_readback_available": False,
                "ready_to_marry_betrothed": None,
                "final_legality_sampled": False, "complete_can_send": None,
                "recipient_acceptance_ready": False,
                "recipient_ai_accept_raw": None,
                "recipient_answer_status_raw": None, "generic_costs": None,
                "matrilineal_option_selected": None,
                "native_child_house_preview": None,
                "effective_matrilineal_if_accepted": None,
                "predicted_outcome_if_accepted": None,
                **{key: None for key in (*_ADULT_FIELDS,
                                        "recipient_character_id",
                                        "intermediary_character_id")}}
    if not isinstance(value, dict):
        raise BridgeUnavailableError("current pair actionability is malformed")
    status = value.get("status")
    reason = value.get("unavailable_reason")
    if (status not in {"available", "unavailable", "not_applicable"}
            or (reason is not None if status == "available"
                else not isinstance(reason, str) or not reason)
            or any(value.get(key) is not None and
                   (type(value[key]) is not int or not 0 < value[key] < 2**31)
                   for key in _PAIR_IDS)
            or value.get("actor_character_id") not in (None, actor)
            or value.get("heir_character_id") not in (None, heir)
            or value.get("partner_character_id") not in (None, partner)
            or any(type(value.get(key)) is not bool for key in (
                "adult_readback_available", "final_legality_sampled",
                "recipient_acceptance_ready"))):
        raise BridgeUnavailableError("current pair actionability identity changed")
    adult = value["adult_readback_available"]
    ready = value.get("ready_to_marry_betrothed")
    if adult:
        if (partner is None
                or any(type(value.get(key)) is not bool
                       for key in _ADULT_FIELDS[:2])
                or any(type(value.get(key)) is not int or not -2**15 <= value[key] < 2**15
                       for key in _ADULT_FIELDS[2:4])
                or any(type(value.get(key)) is not int or not -2**31 <= value[key] < 2**31
                       for key in _ADULT_FIELDS[4:])
                or value["heir_is_adult"] is not
                   (value["heir_adult_measure_raw"] >= value["heir_adult_threshold_raw"])
                or value["partner_is_adult"] is not
                   (value["partner_adult_measure_raw"] >= value["partner_adult_threshold_raw"])
                or ready is not (value["heir_is_adult"] and value["partner_is_adult"])):
            raise BridgeUnavailableError("current pair adulthood is malformed")
    elif ready is not None or any(value.get(key) is not None for key in _ADULT_FIELDS):
        raise BridgeUnavailableError("unavailable current pair adulthood is malformed")
    sampled = value["final_legality_sampled"]
    complete = value.get("complete_can_send")
    acceptance = value["recipient_acceptance_ready"]
    score = value.get("recipient_ai_accept_raw")
    answer = value.get("recipient_answer_status_raw")
    costs = value.get("generic_costs")
    outcome = value.get("predicted_outcome_if_accepted")
    lineality = value.get("effective_matrilineal_if_accepted")
    selected = value.get("matrilineal_option_selected")
    if ((type(complete) is not bool if sampled else complete is not None)
            or (type(score) is not int or not -2**63 <= score < 2**63
                or type(answer) is not int or answer not in (0, 1, 2)
                if acceptance else score is not None or answer is not None)
            or (lineality is not None and type(lineality) is not bool)
            or (selected is not None and type(selected) is not bool)
            or outcome not in (None, "marriage", "betrothal")
            or (costs is not None and (
                not isinstance(costs, dict) or costs.get("raw_scale") != 100000
                or costs.get("payer_role") != "actor"
                or costs.get("application_timing") != "on_send"
                or any(type(costs.get(key)) is not int or not -2**63 <= costs[key] < 2**63
                       for key in _COST_FIELDS)))):
        raise BridgeUnavailableError("current pair native value is malformed")
    if status == "available" and (
            not adult or not sampled or not acceptance or costs is None
            or lineality is None or outcome is None
            or any(value.get(key) is None for key in _PAIR_IDS[:4])):
        raise BridgeUnavailableError("available current pair value is incomplete")
    if status == "not_applicable" and (
            partner is not None or adult or sampled or acceptance or costs is not None
            or lineality is not None or selected is not None or outcome is not None):
        raise BridgeUnavailableError("inapplicable current pair value is malformed")
    _current_child_house_preview(
        value.get("native_child_house_preview"), heir=heir, partner=partner,
        selected=selected, effective=lineality, complete=complete)
    return dict(value)


def query_current_first_heir_relationship_private_v1(
    driver: object, *, expected_native_revision: int,
    timeout_seconds: float = 360.0,
    campaign_root_result: dict[str, object] | None = None,
    guardian_factory_sidecar_path: str | Path | None = None,
) -> dict[str, object]:
    """Read the normal family result; optionally write Root's discovery sidecar.

    The explicit private path adds no family response fields or public MCP tool.
    Its parent directory must already exist; the caller owns that output file.
    """
    sidecar_fields: dict[str, object] = {}
    if guardian_factory_sidecar_path is not None:
        if not isinstance(guardian_factory_sidecar_path, (str, Path)):
            raise ValueError("guardian_factory_sidecar_path must be a path")
        sidecar = Path(guardian_factory_sidecar_path)
        if not str(guardian_factory_sidecar_path) or not sidecar.is_absolute():
            raise ValueError("guardian_factory_sidecar_path must be absolute")
        sidecar_fields["guardian_factory_sidecar_path"] = str(sidecar)
    if getattr(driver, "allow_private_current_first_heir_relationship_query", False) is not True:
        raise UnsupportedStepError("private current first-heir relationship query is disabled")
    read = (getattr(driver, "take_internal_semantic_snapshot", None)
            or getattr(driver, "take_snapshot"))
    before = read()
    played = before.get("played_character")
    played_id = played.get("character_id") if isinstance(played, dict) else None
    if (
        type(expected_native_revision) is not int
        or expected_native_revision <= 0
        or before.get("native_revision") != expected_native_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not isinstance(played, dict)
        or played.get("alive") is not True
        or type(played_id) is not int or played_id <= 0
        or type(before.get("revision")) is not int
        or type(before.get("date_raw")) is not int
    ):
        raise BridgeUnavailableError(
            "current heir relationship needs a paused living-player map frame"
        )
    if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    root = _same_frame_campaign_root_result(campaign_root_result, before)
    if root is None:
        root = driver._execute_campaign_root_context_v1_query(
            expected_revision=before["revision"]
        )
    partition = root.get("held_title_partition")
    primary = [row for row in partition if isinstance(row, dict)
               and row.get("primary") is True] if isinstance(partition, list) else []
    if (root.get("status") != "available" or len(primary) != 1
            or type(root.get("query_sequence")) is not int
            or root["query_sequence"] <= 0):
        raise BridgeUnavailableError("public primary first-heir binding unavailable")
    heir_id = primary[0].get("first_heir_character_id")
    if heir_id is not None and (type(heir_id) is not int or heir_id <= 0):
        raise BridgeUnavailableError("public primary first-heir ID malformed")
    _require_same_paused_frame(
        read(), before, expected_native_revision, played_id
    )
    request_id = "family-relation-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": expected_native_revision,
        **sidecar_fields,
    })
    frame = driver.state.wait_for_command_result(
        request_id, float(timeout_seconds)
    )
    if frame is None:
        raise BridgeUnavailableError("current heir relationship query timed out")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "current heir relationship query RED: " +
            str(frame.get("error") or "unknown")
        )
    result = frame.get("result")
    if (
        not isinstance(result, dict)
        or result.get("step") != STEP
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
        or result.get("native_revision") != expected_native_revision
        or result.get("subject_source") !=
           "public_campaign_root_primary_first_heir"
        or result.get("heir_character_id") !=
           (heir_id if heir_id is not None else -1)
    ):
        raise BridgeUnavailableError("current heir relationship identity changed")
    _require_same_paused_frame(
        read(), before, expected_native_revision, played_id
    )
    base = {
        "schema": SCHEMA, "schema_version": 1,
        **private_native_provenance(before), "read_only": True,
        "advertised": False, "native_revision": expected_native_revision,
        "root_query_sequence": root["query_sequence"],
        "heir_character_id": heir_id,
    }
    if DESCENDANTS_LEAF in result:
        # The optional nested child inputs share this roster's bound frame.
        # Legacy wires without that nested leaf keep their original shape.
        descendants = validate_current_first_heir_descendants_v1(
            result[DESCENDANTS_LEAF], actor=played_id, heir=heir_id,
            native_revision=expected_native_revision, date_raw=before["date_raw"])
        base[DESCENDANTS_LEAF] = descendants
        base[DESCENDANTS_SUMMARY] = summarize_current_first_heir_descendants_v1(descendants)
    if result.get("status") == "unavailable":
        reason = result.get("unavailable_reason")
        if (not isinstance(reason, str) or not reason
                or result.get("bilateral_verified") is not False
                or result.get("betrothed_character_id") is not None
                or result.get("primary_spouse_character_id") is not None
                or result.get("spouse_character_ids") is not None):
            raise BridgeUnavailableError("unavailable heir relationship is malformed")
        if REPRODUCTIVE_INPUTS_LEAF in result:
            base[REPRODUCTIVE_INPUTS_LEAF] = validate_current_first_heir_reproductive_inputs_v1(
                result[REPRODUCTIVE_INPUTS_LEAF], actor=played_id, heir=heir_id,
                native_revision=expected_native_revision, date_raw=before["date_raw"],
                relation=result)
        return {**base, "status": "unavailable", "unavailable_reason": reason,
                "betrothal_actionability": _current_pair_actionability(
                    result.get("betrothal_actionability"), actor=played_id,
                    heir=heir_id, partner=None)}
    if result.get("status") != "available" or heir_id is None:
        raise BridgeUnavailableError("current heir relationship status is invalid")
    betrothed = result.get("betrothed_character_id")
    primary_spouse = result.get("primary_spouse_character_id")
    spouses = result.get("spouse_character_ids")
    if (
        result.get("unavailable_reason") is not None
        or result.get("bilateral_verified") is not True
        or any(value is not None and
               (type(value) is not int or value <= 0 or value == heir_id)
               for value in (betrothed, primary_spouse))
        or not isinstance(spouses, list)
        or any(type(value) is not int or value <= 0 or value == heir_id
               for value in spouses)
        or len(set(spouses)) != len(spouses)
        or (betrothed is not None and
            (betrothed == primary_spouse or betrothed in spouses))
    ):
        raise BridgeUnavailableError("available heir relationship is malformed")
    if REPRODUCTIVE_INPUTS_LEAF in result:
        base[REPRODUCTIVE_INPUTS_LEAF] = validate_current_first_heir_reproductive_inputs_v1(
            result[REPRODUCTIVE_INPUTS_LEAF], actor=played_id, heir=heir_id,
            native_revision=expected_native_revision, date_raw=before["date_raw"],
            relation=result)
    return {**base, "status": "available", "unavailable_reason": None,
            "bilateral_verified": True,
            "betrothed_character_id": betrothed,
            "primary_spouse_character_id": primary_spouse,
            "spouse_character_ids": spouses,
            "betrothal_actionability": _current_pair_actionability(
                result.get("betrothal_actionability"), actor=played_id,
                heir=heir_id, partner=betrothed)}
