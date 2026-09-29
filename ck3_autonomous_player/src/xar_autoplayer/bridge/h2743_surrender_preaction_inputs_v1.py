"""Bind H2743 native read-only observations without predicting war-end effects.

The native bridge already reads the ordered target titles, current holder,
both leaders' resource balances, and partial truce predicates. This module
binds two such reads to one paused snapshot and a native surrender option.
It cannot turn existing balances or script roots into transition deltas.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .defender_dejure_exit_terms_v1 import (
    KEYS as NATIVE_TERMS_KEYS,
    normalize_defender_dejure_exit_terms_v1,
)
from .war_contract import normalize_war_termination_options


SCHEMA = "xar.ck3.h2743-surrender-preaction-inputs.v1"
EPISODE = "native-29829-2bc2d599f7f9"
CHECKPOINT_SHA256 = "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9"
SNAPSHOT_ID = "native:3"
REVISION = 4
NATIVE_REVISION = 3
DATE_RAW = 53217264
CONNECTION_GENERATION = 1
WAR_ID = 16777231
ATTACKER_ID = 30097
DEFENDER_ID = 29829
TARGET_TITLE_IDS = [2128]
CB_KEY = "individual_county_de_jure_cb"
CB_INDEX = 17
RESOURCES = frozenset({"gold", "prestige", "prestige_experience", "piety",
                       "piety_experience", "legitimacy", "stress"})
_PROJECTED_MISSING_RAW_KEYS = frozenset({
    "casus_belli_database_index", "casus_belli_key", "same_frame_stable"})
_PROJECTED_KEYS = ((NATIVE_TERMS_KEYS | {
    "truce_inputs_v1", "recommended_outcome", "action_literal"
}) - _PROJECTED_MISSING_RAW_KEYS)


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _frame(snapshot: Any, checkpoint_sha256: str) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ValueError("native snapshot missing")
    if checkpoint_sha256 != CHECKPOINT_SHA256:
        raise ValueError("H2743 exact checkpoint claim differs")
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    wars = snapshot.get("active_wars")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or snapshot.get("episode_run_id") != EPISODE
            or not isinstance(played, dict) or played.get("character_id") != DEFENDER_ID
            or not isinstance(diagnostics, dict)
            or not _positive_int(diagnostics.get("connection_generation"))
            or not isinstance(wars, list)):
        raise ValueError("H2743 paused map and episode identity unavailable")
    matches = [row for row in wars if isinstance(row, dict) and row.get("war_id") == WAR_ID]
    if (len(matches) != 1 or matches[0].get("player_side") != "defender"
            or matches[0].get("player_is_primary_war_leader") is not True
            or matches[0].get("primary_opponent_character_id") != ATTACKER_ID
            or matches[0].get("targeted_title_ids") != TARGET_TITLE_IDS):
        raise ValueError("H2743 active native war binding differs")
    signature_keys = ("war_id", "player_side", "player_is_primary_war_leader",
                      "primary_opponent_character_id", "player_relative_war_score",
                      "targeted_title_ids")
    signatures = []
    for war in wars:
        if (not isinstance(war, dict) or any(key not in war for key in signature_keys)
                or not _positive_int(war["war_id"])
                or not _positive_int(war["primary_opponent_character_id"])
                or type(war["player_relative_war_score"]) is not int
                or not isinstance(war["targeted_title_ids"], list)):
            raise ValueError("H2743 complete active war signature unavailable")
        signatures.append({key: deepcopy(war[key]) for key in signature_keys})
    signatures.sort(key=lambda row: row["war_id"])
    if len({row["war_id"] for row in signatures}) != len(signatures):
        raise ValueError("H2743 active WarID repeated")
    frame = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "episode_run_id": EPISODE,
        "connection_generation": diagnostics["connection_generation"],
        "checkpoint_sha256": checkpoint_sha256,
        "war_id": WAR_ID,
        "primary_attacker_character_id": ATTACKER_ID,
        "primary_defender_character_id": DEFENDER_ID,
        "casus_belli_key": CB_KEY,
        "casus_belli_database_index": CB_INDEX,
        "target_title_ids": TARGET_TITLE_IDS.copy(),
        "active_war_signature": signatures,
    }
    if (not isinstance(frame["snapshot_id"], str) or not frame["snapshot_id"]
            or any(not _positive_int(frame[key]) for key in (
                "revision", "native_revision", "date_raw"))):
        raise ValueError("H2743 native frame incomplete")
    if (frame["snapshot_id"] != SNAPSHOT_ID
            or frame["revision"] != REVISION
            or frame["native_revision"] != NATIVE_REVISION
            or frame["date_raw"] != DATE_RAW
            or frame["connection_generation"] != CONNECTION_GENERATION):
        raise ValueError("H2743 exact attempt-12 frame differs")
    return frame


def _baseline(result: Any, frame: dict[str, Any]) -> dict[str, Any]:
    if (not isinstance(result, dict)
            or result.get("step") != f"query-defender-de-jure-exit-terms-v1-{WAR_ID}"
            or result.get("backend_id") != "native-headless"
            or result.get("accepted") is not True
            or result.get("status") != "baseline_only"
            or not _positive_int(result.get("query_sequence"))
            or result.get("queried_snapshot_id") != frame["snapshot_id"]
            or result.get("queried_revision") != frame["revision"]
            or result.get("queried_native_revision") != frame["native_revision"]):
        raise ValueError("H2743 native baseline is not bound to the paused frame")
    value = result.get("defender_de_jure_exit_terms_v1")
    if not isinstance(value, dict):
        raise ValueError("H2743 native baseline payload missing")
    # The driver projects the bridge's raw V1 after validating these three
    # fields. Its public MCP result omits them. Reconstruct only for the
    # existing strict schema validator; the separate option validates CB and
    # the surrounding two reads validate stability. Never publish these as
    # independently observed raw fields.
    if set(value) == _PROJECTED_KEYS or set(value) == (_PROJECTED_KEYS | {
            "border_raid_storage_candidate_v1"}):
        if value["recommended_outcome"] is not None or value["action_literal"] is not None:
            raise ValueError("H2743 projected baseline contains an exit recommendation")
        value = {key: item for key, item in value.items()
                 if key not in ("recommended_outcome", "action_literal")}
        value = {**value, "casus_belli_database_index": CB_INDEX,
                 "casus_belli_key": CB_KEY, "same_frame_stable": True}
    return normalize_defender_dejure_exit_terms_v1(
        value, expected_war_id=WAR_ID,
        expected_native_revision=frame["native_revision"],
        expected_date_raw=frame["date_raw"], expected_defender_id=DEFENDER_ID,
        expected_attacker_id=ATTACKER_ID, expected_target_title_ids=TARGET_TITLE_IDS,
    )


def _option(result: Any, frame: dict[str, Any]) -> None:
    if (not isinstance(result, dict)
            or result.get("step") != f"query-war-termination-options-{WAR_ID}"
            or result.get("backend_id") != "native-headless"
            or result.get("accepted") is not True
            or result.get("status") != "available"
            or not _positive_int(result.get("query_sequence"))
            or result.get("queried_snapshot_id") != frame["snapshot_id"]
            or result.get("queried_revision") != frame["revision"]
            or result.get("queried_native_revision") != frame["native_revision"]
            or result.get("queried_connection_generation") != frame["connection_generation"]
            or result.get("queried_episode_run_id") != EPISODE):
        raise ValueError("H2743 native option is not bound to the paused frame")
    context = result.get("termination_query_context")
    if (not isinstance(context, dict)
            or context.get("queried_date_raw") != frame["date_raw"]
            or context.get("queried_connection_generation") != frame["connection_generation"]
            or context.get("queried_episode_run_id") != EPISODE
            or context.get("queried_character_id") != DEFENDER_ID):
        raise ValueError("H2743 option query context differs")
    if context.get("active_war_signature") != frame["active_war_signature"]:
        raise ValueError("H2743 native option active wars differ")
    options = normalize_war_termination_options(
        result.get("war_termination_options"), expected_war_id=WAR_ID)
    identity = options.get("active_casus_belli_identity")
    surrender = options.get("options", {}).get("surrender", {})
    response = surrender.get("recipient_response")
    terms = surrender.get("terms")
    if (options.get("player_side") != "defender"
            or options.get("player_is_primary_war_leader") is not True
            or not isinstance(identity, dict)
            or identity.get("database_index") != CB_INDEX
            or identity.get("canonical_key") != CB_KEY
            or surrender.get("outcome") != "attacker_victory"
            or surrender.get("native_validator_passed") is not True
            or surrender.get("available") is not True
            or not isinstance(response, dict)
            or response.get("would_accept_now") is not True
            or surrender.get("terms_observable") is not False
            or not isinstance(terms, dict)
            or terms.get("status") != "unavailable"):
        raise ValueError("H2743 surrender option changed or claims material terms")


def project_h2743_surrender_preaction_inputs(
    before_snapshot: Any, baseline_first: Any, option_result: Any,
    baseline_second: Any, after_snapshot: Any, *, checkpoint_sha256: str,
) -> dict[str, Any]:
    """Return only the native fields genuinely observed on one paused frame."""
    frame = _frame(before_snapshot, checkpoint_sha256)
    if _frame(after_snapshot, checkpoint_sha256) != frame:
        raise ValueError("H2743 paused frame changed during queries")
    first = _baseline(baseline_first, frame)
    second = _baseline(baseline_second, frame)
    if first != second:
        raise ValueError("H2743 native baseline double-read drift")
    _option(option_result, frame)
    balances = first["primary_resource_balances"]
    if (len(balances) != 14 or {(row["character_id"], row["resource"])
            for row in balances} != {(party, resource) for party in
                                     (ATTACKER_ID, DEFENDER_ID) for resource in RESOURCES}):
        raise ValueError("H2743 two-party resource prestate incomplete")
    gold = [deepcopy(row) for row in balances if row["resource"] == "gold"]
    truce = first.get("truce_inputs_v1")
    if truce is None:
        raise ValueError("H2743 partial truce native input wire absent")
    return {
        "schema": SCHEMA,
        "status": "same_frame_preaction_inputs_only",
        "source_bytes_authenticated_here": False,
        "frame": frame,
        "target_title_ids": deepcopy(first["target_title_ids"]),
        "target_title_holder_prestate": deepcopy(first["target_title_holder_prestate"]),
        "primary_resource_balances": deepcopy(balances),
        "possible_fp2_payer_gold_prestate": gold,
        "fp2_payer_character_id": None,
        "fp2_payer_unavailable_reason": "owed_contract_and_contribution_inputs_unread",
        "truce_predicates": deepcopy(truce),
        "script_candidate_direction": {"owner_character_id": ATTACKER_ID,
                                       "toward_character_id": DEFENDER_ID},
        "script_candidate_days": None,
        "script_candidate_days_unavailable_reason": "short_long_border_raid_stock_predicates_unread",
        "post_surrender_actual_expiry_date_raw": None,
        "post_surrender_expiry_unavailable_reason": "future_persisted_relation_unobservable_preaction",
        "enabled_effect_selector": None,
        "enabled_effect_selector_unavailable_reason": "loaded_effect_tree_dispatch_abi_unproven",
        "runtime_target_scope_title_id": None,
        "cb_prestige_factor_q100000": None,
        "title_vassal_delta": None,
        "signed_resource_delta": None,
        "directed_truce": None,
        "effect_projection_complete": False,
        "material_complete": False,
        "recommended_outcome": None,
        "action_literal": None,
    }


__all__ = ["project_h2743_surrender_preaction_inputs"]
