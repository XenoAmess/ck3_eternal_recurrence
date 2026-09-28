"""Fail-closed projection of the native defender de-jure exit baseline.

This contract deliberately has no material-delta or action constructor.  Its
native producer reads current identities and balances without executing war
effects; title/vassal, signed-resource and truce outcomes remain unavailable.
"""

from __future__ import annotations

from typing import Any


SCHEMA = "xar.ck3.defender-de-jure-exit-terms.v1"
PREFIX = "query-defender-de-jure-exit-terms-v1-"
CAPABILITY = "game.command.query-defender-de-jure-exit-terms-v1-N"
RESOURCES = frozenset(
    {
        "gold",
        "prestige",
        "prestige_experience",
        "piety",
        "piety_experience",
        "legitimacy",
        "stress",
    }
)
UNAVAILABLE_REASONS = {
    "title_vassal_delta": "runtime_target_scope_and_de_jure_change_semantics_unproven",
    "signed_resource_delta": "conditional_effects_and_cb_prestige_factor_unread",
    "directed_truce": "attacker_victory_truce_duration_unread",
}
KEYS = frozenset(
    {
        "schema",
        "native_revision",
        "war_id",
        "date_raw",
        "casus_belli_database_index",
        "casus_belli_key",
        "primary_attacker_character_id",
        "primary_defender_character_id",
        "target_title_ids",
        "target_title_holder_prestate",
        "primary_resource_balances",
        "primary_monthly_gold_income",
        "title_vassal_delta",
        "title_vassal_delta_unavailable_reason",
        "signed_resource_delta",
        "signed_resource_delta_unavailable_reason",
        "directed_truce",
        "directed_truce_unavailable_reason",
        "same_frame_stable",
        "material_complete",
    }
)
TRUCE_INPUT_KEYS = frozenset({
    "schema", "attacker_flexible_truces_perk",
    "attacker_government_is_nomadic", "defender_government_is_nomadic",
    "nomad_both", "short", "long", "border_raid_pair",
    "evaluated_days", "persisted_expiry_date_raw",
})


def _normalize_border_raid_storage_candidate(value: Any) -> dict[str, Any]:
    keys = {
        "schema", "status", "candidate", "storage_capacity",
        "active_war_count", "matching_war_count", "unavailable_reason",
        "native_condition_observed",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("malformed border-raid storage candidate")
    if (value["schema"] != "xar.ck3.h2743-border-raid-storage-candidate.v1"
            or value["native_condition_observed"] is not False):
        raise ValueError("border-raid storage candidate claims stock condition")
    capacity = _native_int(value["storage_capacity"])
    active = _native_int(value["active_war_count"])
    matches = _native_int(value["matching_war_count"])
    if value["status"] == "unavailable":
        if (value["candidate"] is not None or capacity != 0 or active != 0
                or matches != 0 or not isinstance(value["unavailable_reason"], str)
                or not value["unavailable_reason"]):
            raise ValueError("unavailable storage scan was laundered")
    elif value["status"] == "structural_candidate_only":
        if (type(value["candidate"]) is not bool or not 0 < capacity <= 1_000_000
                or not 1 <= active <= capacity or not 0 <= matches <= active
                or value["candidate"] != (matches > 0)
                or value["unavailable_reason"] is not None):
            raise ValueError("inconsistent border-raid storage candidate")
    else:
        raise ValueError("invalid border-raid storage candidate status")
    return dict(value)


def _normalize_truce_inputs(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != TRUCE_INPUT_KEYS:
        raise ValueError("malformed partial truce input wire")
    if value["schema"] != "xar.ck3.defender-de-jure-truce-inputs.v1":
        raise ValueError("unexpected partial truce input schema")
    normalized = {"schema": value["schema"]}
    for key in (
        "attacker_flexible_truces_perk", "attacker_government_is_nomadic",
        "defender_government_is_nomadic", "nomad_both", "short", "long",
        "border_raid_pair",
    ):
        field = value[key]
        if not isinstance(field, dict) or set(field) != {
            "status", "value", "unavailable_reason"
        }:
            raise ValueError(f"malformed {key} truce input")
        if field["status"] == "observed":
            if type(field["value"]) is not bool or field["unavailable_reason"] is not None:
                raise ValueError(f"invalid observed {key} truce input")
        elif field["status"] == "unavailable":
            if (field["value"] is not None or
                    not isinstance(field["unavailable_reason"], str) or
                    not field["unavailable_reason"]):
                raise ValueError(f"unavailable {key} truce input was laundered")
        else:
            raise ValueError(f"invalid {key} truce input status")
        normalized[key] = dict(field)
    for key in ("short", "long", "border_raid_pair"):
        if normalized[key] != {
            "status": "unavailable", "value": None,
            "unavailable_reason": "stock_condition_reader_unavailable",
        }:
            raise ValueError(f"{key} truce condition was laundered")
    attacker = normalized["attacker_government_is_nomadic"]
    defender = normalized["defender_government_is_nomadic"]
    both = normalized["nomad_both"]
    if attacker["status"] == defender["status"] == "observed":
        if both != {"status": "observed",
                    "value": attacker["value"] and defender["value"],
                    "unavailable_reason": None}:
            raise ValueError("nomad conjunction disagrees with both parties")
    elif both != {"status": "unavailable", "value": None,
                  "unavailable_reason": "party_government_flag_unavailable"}:
        raise ValueError("nomad conjunction lacks a party")
    if value["evaluated_days"] is not None or value["persisted_expiry_date_raw"] is not None:
        raise ValueError("partial truce inputs cannot contain a duration")
    normalized["evaluated_days"] = None
    normalized["persisted_expiry_date_raw"] = None
    return normalized


def query_defender_dejure_exit_terms_v1_step(war_id: int) -> str:
    if type(war_id) is not int or war_id <= 0 or war_id > 2**31 - 1:
        raise ValueError("WarID must be a positive signed native ID")
    return f"{PREFIX}{war_id}"


def parse_query_defender_dejure_exit_terms_v1_step(step: str) -> int | None:
    if not isinstance(step, str) or not step.startswith(PREFIX):
        return None
    suffix = step[len(PREFIX) :]
    if not suffix.isascii() or not suffix.isdecimal() or suffix.startswith("0"):
        return None
    war_id = int(suffix)
    return war_id if 0 < war_id <= 2**31 - 1 else None


def _native_int(value: Any, *, positive: bool = False) -> int:
    if type(value) is not int or not -(2**63) <= value <= 2**63 - 1:
        raise ValueError("invalid native integer")
    if positive and value <= 0:
        raise ValueError("native ID/revision must be positive")
    return value


def _fixed(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError("malformed fixed-point value")
    raw = _native_int(value["raw"])
    if _native_int(value["scale"]) != 100_000:
        raise ValueError("unexpected fixed-point scale")
    return {"raw": raw, "scale": 100_000}


def normalize_defender_dejure_exit_terms_v1(
    value: Any,
    *,
    expected_war_id: int,
    expected_native_revision: int,
    expected_date_raw: int,
    expected_defender_id: int,
    expected_attacker_id: int,
    expected_target_title_ids: list[int],
) -> dict[str, Any]:
    """Accept only a same-frame baseline with all material terms unavailable."""
    if not isinstance(value, dict) or set(value) not in (
        KEYS, KEYS | {"truce_inputs_v1"},
        KEYS | {"truce_inputs_v1", "border_raid_storage_candidate_v1"},
    ):
        raise ValueError("defender de-jure baseline schema is malformed")
    if value["schema"] != SCHEMA:
        raise ValueError("defender de-jure baseline schema version differs")
    for key, expected in (
        ("war_id", expected_war_id),
        ("native_revision", expected_native_revision),
        ("date_raw", expected_date_raw),
        ("primary_defender_character_id", expected_defender_id),
        ("primary_attacker_character_id", expected_attacker_id),
    ):
        if _native_int(value[key], positive=key != "date_raw") != expected:
            raise ValueError(f"defender de-jure baseline {key} changed")
    if (
        value["casus_belli_database_index"] != 17
        or value["casus_belli_key"] != "individual_county_de_jure_cb"
        or expected_defender_id == expected_attacker_id
    ):
        raise ValueError("defender de-jure baseline CB/side differs")
    titles = value["target_title_ids"]
    if (
        not isinstance(titles, list)
        or not titles
        or titles != expected_target_title_ids
        or len(titles) != len(set(titles))
        or any(_native_int(title, positive=True) != title for title in titles)
    ):
        raise ValueError("defender de-jure baseline target titles differ")
    prestate = value["target_title_holder_prestate"]
    if not isinstance(prestate, list) or len(prestate) != len(titles):
        raise ValueError("defender de-jure title-holder prestate is incomplete")
    normalized_prestate = []
    for title_id, row in zip(titles, prestate, strict=True):
        if not isinstance(row, dict) or set(row) != {
            "title_id", "holder_character_id", "holder_immediate_liege_character_id"
        }:
            raise ValueError("malformed title-holder prestate row")
        holder_id = _native_int(row["holder_character_id"], positive=True)
        liege_id = row["holder_immediate_liege_character_id"]
        if (
            _native_int(row["title_id"], positive=True) != title_id
            or (liege_id is not None and
                (_native_int(liege_id, positive=True) == holder_id))
        ):
            raise ValueError("title-holder prestate identity differs")
        normalized_prestate.append({
            "title_id": title_id,
            "holder_character_id": holder_id,
            "holder_immediate_liege_character_id": liege_id,
        })
    if value["same_frame_stable"] is not True or value["material_complete"] is not False:
        raise ValueError("defender de-jure baseline readiness was laundered")
    for field, reason in UNAVAILABLE_REASONS.items():
        if (
            value[field] is not None
            or value[f"{field}_unavailable_reason"] != reason
        ):
            raise ValueError(f"defender de-jure {field} is not unavailable")
    expected_ids = {expected_attacker_id, expected_defender_id}
    balances = value["primary_resource_balances"]
    if not isinstance(balances, list) or len(balances) != 14:
        raise ValueError("defender de-jure baseline requires 14 balances")
    seen: set[tuple[int, str]] = set()
    normalized_balances = []
    for row in balances:
        if not isinstance(row, dict) or set(row) != {"character_id", "resource", "value"}:
            raise ValueError("malformed baseline resource row")
        character_id = _native_int(row["character_id"], positive=True)
        resource = row["resource"]
        identity = (character_id, resource)
        if character_id not in expected_ids or resource not in RESOURCES or identity in seen:
            raise ValueError("unexpected or repeated baseline resource row")
        seen.add(identity)
        normalized_balances.append(
            {"character_id": character_id, "resource": resource, "value": _fixed(row["value"])}
        )
    if seen != {(character_id, resource) for character_id in expected_ids for resource in RESOURCES}:
        raise ValueError("incomplete baseline resource matrix")
    income = value["primary_monthly_gold_income"]
    if not isinstance(income, list) or len(income) != 2:
        raise ValueError("defender de-jure baseline requires both monthly incomes")
    normalized_income = []
    for row in income:
        if not isinstance(row, dict) or set(row) != {"character_id", "value"}:
            raise ValueError("malformed monthly income row")
        character_id = _native_int(row["character_id"], positive=True)
        normalized_income.append({"character_id": character_id, "value": _fixed(row["value"])})
    if {row["character_id"] for row in normalized_income} != expected_ids:
        raise ValueError("monthly income identities differ")
    return {
        "schema": SCHEMA,
        "war_id": expected_war_id,
        "native_revision": expected_native_revision,
        "date_raw": expected_date_raw,
        "primary_attacker_character_id": expected_attacker_id,
        "primary_defender_character_id": expected_defender_id,
        "target_title_ids": list(titles),
        "target_title_holder_prestate": normalized_prestate,
        "primary_resource_balances": normalized_balances,
        "primary_monthly_gold_income": normalized_income,
        "truce_inputs_v1": (
            _normalize_truce_inputs(value["truce_inputs_v1"])
            if "truce_inputs_v1" in value else None
        ),
        "border_raid_storage_candidate_v1": (
            _normalize_border_raid_storage_candidate(
                value["border_raid_storage_candidate_v1"])
            if "border_raid_storage_candidate_v1" in value else None
        ),
        "title_vassal_delta": None,
        "title_vassal_delta_unavailable_reason": UNAVAILABLE_REASONS["title_vassal_delta"],
        "signed_resource_delta": None,
        "signed_resource_delta_unavailable_reason": UNAVAILABLE_REASONS["signed_resource_delta"],
        "directed_truce": None,
        "directed_truce_unavailable_reason": UNAVAILABLE_REASONS["directed_truce"],
        "material_complete": False,
        "recommended_outcome": None,
        "action_literal": None,
    }
