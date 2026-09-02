"""Project existing public Raiktor terms into the six-domain aggregate.

This adapter is deliberately read-only.  It only promotes domains whose
values are already present in the normalized war-termination terms response;
truce and generic war-bound data require their strict observer contracts on
the same paused frame.
"""

from __future__ import annotations

import copy

from xar_autoplayer.bridge.raiktor_surrender_six_domain_contract import (
    BACKEND_ID,
    normalize_raiktor_surrender_six_domain,
)
from xar_autoplayer.bridge.raiktor_surrender_truce_contract import (
    project_raiktor_surrender_truce_from_passive_observer,
)
from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (
    normalize_raiktor_war_bound_regiment,
)


_RAIKTOR_SLICE = "raiktor_claim_cb_attacker_defeat_disposition"
_DOMAIN_ORDER = (
    "claims_base",
    "gold",
    "prestige",
    "prisoner_release",
    "favor_hook",
    "truce",
    "generic_war_bound_current",
)


def project_raiktor_surrender_six_domain(
    snapshot_value: object,
    terms_value: object,
    *,
    passive_truce_postprocess_value: object | None = None,
    generic_war_bound_current_value: object | None = None,
) -> dict[str, object] | None:
    """Return the identity-bound observed aggregate, or ``None`` if invalid."""

    if not isinstance(snapshot_value, dict) or not isinstance(terms_value, dict):
        return None
    if (
        terms_value.get("status") != "available"
        or terms_value.get("supported_slice") != _RAIKTOR_SLICE
    ):
        return None
    war_id = terms_value.get("war_id")
    war = _war_by_id(snapshot_value, war_id)
    played_character = snapshot_value.get("played_character")
    played_character_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    attacker_id = snapshot_value.get("episode_character_id")
    defender_id = (
        war.get("primary_opponent_character_id")
        if isinstance(war, dict)
        else None
    )
    casus_belli = terms_value.get("casus_belli")
    claimant_id = terms_value.get("claimant_character_id")
    frame_values = (
        snapshot_value.get("revision"),
        snapshot_value.get("native_revision"),
        war_id,
        attacker_id,
        defender_id,
        claimant_id,
    )
    if (
        snapshot_value.get("paused") is not True
        or not isinstance(war, dict)
        or war.get("player_side") != "attacker"
        or war.get("player_is_primary_war_leader") is not True
        or played_character_id != attacker_id
        or any(not _positive_int(value) for value in frame_values)
        or not _signed_int32(snapshot_value.get("date_raw"))
        or not isinstance(casus_belli, dict)
        or casus_belli.get("canonical_key") != "raiktor_claim_cb"
        or not _non_negative_int(casus_belli.get("database_index"))
    ):
        return None

    frame = {
        "snapshot_revision": snapshot_value["revision"],
        "native_revision": snapshot_value["native_revision"],
        "date_raw": snapshot_value["date_raw"],
        "paused": True,
        "war_id": war_id,
        "active_casus_belli_database_index": casus_belli["database_index"],
        "active_casus_belli_key": "raiktor_claim_cb",
        "primary_attacker_character_id": attacker_id,
        "primary_defender_character_id": defender_id,
        "claimant_character_id": claimant_id,
    }
    claims = {
        "target_title_ids": copy.deepcopy(terms_value.get("target_title_ids")),
        "claims": copy.deepcopy(terms_value.get("claims")),
        "attacker_defeat": copy.deepcopy(terms_value.get("attacker_defeat")),
        "target_order_stable": True,
        "claim_rows_stable": True,
    }
    gold = terms_value.get("gold_reparations")
    prestige = terms_value.get("attacker_fame")
    prisoners = terms_value.get("prisoner_release")
    favor = terms_value.get("conditional_favor_hook")
    diagnostics = snapshot_value.get("diagnostics")
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    passive_truce = project_raiktor_surrender_truce_from_passive_observer(
        passive_truce_postprocess_value,
        expected_snapshot_id=snapshot_value.get("snapshot_id"),
        expected_snapshot_revision=snapshot_value["revision"],
        expected_native_revision=snapshot_value["native_revision"],
        expected_date_raw=snapshot_value["date_raw"],
        expected_connection_generation=diagnostics.get(
            "connection_generation"
        ),
        expected_episode_run_id=snapshot_value.get("episode_run_id"),
        expected_process_id=diagnostics.get("bridge_pid"),
        expected_war_id=war_id,
        expected_casus_belli_database_index=casus_belli["database_index"],
        expected_attacker_character_id=attacker_id,
        expected_defender_character_id=defender_id,
    )
    generic_war_bound = _project_generic_war_bound_current(
        generic_war_bound_current_value,
        frame=frame,
    )
    domain_payloads: dict[str, dict[str, object] | None] = {
        "gold": (
            {
                **{
                    key: copy.deepcopy(gold.get(key))
                    for key in (
                        "attacker_current_gold",
                        "defender_current_gold",
                        "attacker_authoritative_monthly_gold_income",
                        "defender_authoritative_monthly_gold_income",
                        "actual_transfer",
                    )
                },
                "exact_primary_transfer_observed": True,
                "same_frame_stable": True,
            }
            if isinstance(gold, dict)
            and gold.get("actual_amount_observable") is True
            else None
        ),
        "prestige": (
            {
                **{
                    key: copy.deepcopy(prestige.get(key))
                    for key in (
                        "attacker_current_prestige",
                        "cb_prestige_factor",
                        "attacker_prestige_delta",
                    )
                },
                "exact_factor_and_attacker_delta_observed": True,
                "same_frame_stable": True,
            }
            if isinstance(prestige, dict)
            and prestige.get("actual_delta_observable") is True
            else None
        ),
        "prisoner_release": (
            {
                **{
                    key: copy.deepcopy(prisoners.get(key))
                    for key in (
                        "attacker_participant_ids",
                        "defender_participant_ids",
                        "attacker_release_candidate_ids",
                        "defender_release_candidate_ids",
                        "release_pairs",
                        "full_participant_scan",
                        "primary_and_first_three_successors_scanned",
                    )
                },
                "same_frame_stable": True,
            }
            if isinstance(prisoners, dict)
            and prisoners.get("actual_pairs_observable") is True
            else None
        ),
        "favor_hook": (
            {
                **{
                    key: copy.deepcopy(favor.get(key))
                    for key in (
                        "claimant_distinct_from_attacker",
                        "original_visible_root_traversed",
                        "will_apply",
                    )
                },
                "same_frame_stable": True,
            }
            if isinstance(favor, dict)
            and favor.get("actual_applies_observable") is True
            else None
        ),
        # A bare public evaluated_days leaf is insufficient.  Only the frozen
        # passive postprocessor's session-bound two-return GREEN may fill v1.
        "truce": passive_truce,
        # Only the frozen generic observer contract may fill this domain.  It
        # proves current soldiers, never source attribution, pre soldiers, or
        # loss from the authored 3000.
        "generic_war_bound_current": generic_war_bound,
    }
    domains = {
        name: _wrap(frame, payload)
        for name, payload in domain_payloads.items()
    }
    missing = [
        name
        for name in _DOMAIN_ORDER
        if name != "claims_base" and domain_payloads[name] is None
    ]
    six_dynamic_domains_ready = not missing
    postwar_cleanup_ready = bool(
        generic_war_bound is not None
        and generic_war_bound["cleanup"]["observable"] is True
    )
    aggregate = {
        "schema_version": 1,
        "backend_id": BACKEND_ID,
        "status": (
            "complete" if six_dynamic_domains_ready else "incomplete"
        ),
        "failure": None,
        "frame": frame,
        "claims_base": _wrap(frame, claims),
        "domains": domains,
        "missing_domains": missing,
        "readiness": {
            "claims_base_ready": True,
            "gold_ready": domain_payloads["gold"] is not None,
            "prestige_ready": domain_payloads["prestige"] is not None,
            "prisoner_release_ready": (
                domain_payloads["prisoner_release"] is not None
            ),
            "favor_hook_ready": domain_payloads["favor_hook"] is not None,
            "truce_ready": domain_payloads["truce"] is not None,
            "generic_war_bound_current_ready": (
                generic_war_bound is not None
            ),
            "postwar_cleanup_ready": postwar_cleanup_ready,
            "source_specific_war_bound_ready": False,
            "pre_soldiers_ready": False,
            "proven_soldier_loss_ready": False,
            "six_dynamic_domains_ready": six_dynamic_domains_ready,
            "same_frame_stable": six_dynamic_domains_ready,
            "action_terms_ready": six_dynamic_domains_ready,
            "automatic_surrender_ready": False,
        },
    }
    try:
        return normalize_raiktor_surrender_six_domain(
            aggregate,
            expected_war_id=war_id,
            expected_snapshot_revision=snapshot_value["revision"],
            expected_native_revision=snapshot_value["native_revision"],
            expected_date_raw=snapshot_value["date_raw"],
            expected_attacker_character_id=attacker_id,
            expected_defender_character_id=defender_id,
            expected_claimant_character_id=claimant_id,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _project_generic_war_bound_current(
    value: object,
    *,
    frame: dict[str, object],
) -> dict[str, object] | None:
    """Return a strict generic current-regiment payload for ``frame``."""

    if not isinstance(value, dict):
        return None
    active_frame = value.get("active_frame")
    if (
        not isinstance(active_frame, dict)
        or active_frame.get("active_casus_belli_database_index")
        != frame["active_casus_belli_database_index"]
    ):
        return None
    try:
        normalized = normalize_raiktor_war_bound_regiment(
            value,
            expected_war_id=frame["war_id"],
            expected_attacker_character_id=frame[
                "primary_attacker_character_id"
            ],
            expected_defender_character_id=frame[
                "primary_defender_character_id"
            ],
            expected_snapshot_revision=frame["snapshot_revision"],
            expected_native_revision=frame["native_revision"],
            expected_date_raw=frame["date_raw"],
        )
    except (KeyError, TypeError, ValueError):
        return None
    return copy.deepcopy(normalized)


def _wrap(
    frame: dict[str, object], payload: dict[str, object] | None
) -> dict[str, object]:
    if payload is None:
        return {"available": False}
    return {
        "available": True,
        "frame": copy.deepcopy(frame),
        "payload": payload,
    }


def _war_by_id(
    snapshot: dict[str, object], war_id: object
) -> dict[str, object] | None:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    return next(
        (
            war
            for war in wars
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _non_negative_int(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= 2**31 - 1
    )


def _signed_int32(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and -(2**31) <= value <= 2**31 - 1
    )
