"""Strict pure contract for the Raiktor six-domain same-frame aggregate.

Claims are the base surrender semantics.  The six dynamic domains are gold,
prestige, prisoners of war, favor hook, truce, and the honestly generic
war-bound current-regiment observation.  A later cleanup proof may be attached
to the frozen regiment payload, but it is not mislabeled as a pre-action frame.
"""

from __future__ import annotations

from xar_autoplayer.bridge.raiktor_surrender_truce_contract import (
    normalize_raiktor_surrender_truce,
)
from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (
    normalize_raiktor_war_bound_regiment,
)


BACKEND_ID = "ck3-1.19.0.6-native-raiktor-surrender-six-domain-v1"

_ROOT_KEYS = {
    "schema_version",
    "backend_id",
    "status",
    "failure",
    "frame",
    "claims_base",
    "domains",
    "missing_domains",
    "readiness",
}
_FRAME_KEYS = {
    "snapshot_revision",
    "native_revision",
    "date_raw",
    "paused",
    "war_id",
    "active_casus_belli_database_index",
    "active_casus_belli_key",
    "primary_attacker_character_id",
    "primary_defender_character_id",
    "claimant_character_id",
}
_DOMAIN_KEYS = {
    "gold",
    "prestige",
    "prisoner_release",
    "favor_hook",
    "truce",
    "generic_war_bound_current",
}
_DOMAIN_ORDER = (
    "claims_base",
    "gold",
    "prestige",
    "prisoner_release",
    "favor_hook",
    "truce",
    "generic_war_bound_current",
)
_READINESS_KEYS = {
    "claims_base_ready",
    "gold_ready",
    "prestige_ready",
    "prisoner_release_ready",
    "favor_hook_ready",
    "truce_ready",
    "generic_war_bound_current_ready",
    "postwar_cleanup_ready",
    "source_specific_war_bound_ready",
    "pre_soldiers_ready",
    "proven_soldier_loss_ready",
    "six_dynamic_domains_ready",
    "same_frame_stable",
    "action_terms_ready",
    "automatic_surrender_ready",
}
_CLAIMS_KEYS = {
    "target_title_ids",
    "claims",
    "attacker_defeat",
    "target_order_stable",
    "claim_rows_stable",
}
_GOLD_KEYS = {
    "attacker_current_gold",
    "defender_current_gold",
    "attacker_authoritative_monthly_gold_income",
    "defender_authoritative_monthly_gold_income",
    "actual_transfer",
    "exact_primary_transfer_observed",
    "same_frame_stable",
}
_PRESTIGE_KEYS = {
    "attacker_current_prestige",
    "cb_prestige_factor",
    "attacker_prestige_delta",
    "exact_factor_and_attacker_delta_observed",
    "same_frame_stable",
}
_PRISONER_KEYS = {
    "attacker_participant_ids",
    "defender_participant_ids",
    "attacker_release_candidate_ids",
    "defender_release_candidate_ids",
    "release_pairs",
    "full_participant_scan",
    "primary_and_first_three_successors_scanned",
    "same_frame_stable",
}
_FAVOR_KEYS = {
    "claimant_distinct_from_attacker",
    "original_visible_root_traversed",
    "will_apply",
    "same_frame_stable",
}


def normalize_raiktor_surrender_six_domain(
    value: object,
    *,
    expected_war_id: int,
    expected_snapshot_revision: int,
    expected_native_revision: int,
    expected_date_raw: int,
    expected_attacker_character_id: int,
    expected_defender_character_id: int,
    expected_claimant_character_id: int,
) -> dict[str, object]:
    """Validate a complete or honestly incomplete aggregate."""
    root = _exact_dict(value, _ROOT_KEYS, "six-domain root")
    if (
        root["schema_version"] != 1
        or root["backend_id"] != BACKEND_ID
        or root["failure"] is not None
        or root["status"] not in {"complete", "incomplete"}
    ):
        raise ValueError("Raiktor six-domain aggregate is unavailable")

    expected_frame = {
        "snapshot_revision": _positive_uint64(
            expected_snapshot_revision, "expected_snapshot_revision"
        ),
        "native_revision": _positive_uint64(
            expected_native_revision, "expected_native_revision"
        ),
        "date_raw": _signed_int32(expected_date_raw, "expected_date_raw"),
        "paused": True,
        "war_id": _full_id(expected_war_id, "expected_war_id"),
        "active_casus_belli_database_index": None,
        "active_casus_belli_key": "raiktor_claim_cb",
        "primary_attacker_character_id": _full_id(
            expected_attacker_character_id,
            "expected_attacker_character_id",
        ),
        "primary_defender_character_id": _full_id(
            expected_defender_character_id,
            "expected_defender_character_id",
        ),
        "claimant_character_id": _full_id(
            expected_claimant_character_id,
            "expected_claimant_character_id",
        ),
    }
    frame = _normalize_frame(root["frame"], "frame")
    expected_frame["active_casus_belli_database_index"] = frame[
        "active_casus_belli_database_index"
    ]
    if frame != expected_frame:
        raise ValueError("Raiktor six-domain root frame disagrees")

    claims = _available_payload(root["claims_base"], frame, "claims_base")
    if claims is not None:
        _normalize_claims(claims)

    domains = _exact_dict(root["domains"], _DOMAIN_KEYS, "domains")
    payloads: dict[str, dict[str, object] | None] = {}
    for name in _DOMAIN_ORDER[1:]:
        payloads[name] = _available_payload(domains[name], frame, name)

    if payloads["gold"] is not None:
        _normalize_gold(payloads["gold"], frame)
    if payloads["prestige"] is not None:
        _normalize_prestige(payloads["prestige"], frame)
    if payloads["prisoner_release"] is not None:
        _normalize_prisoners(payloads["prisoner_release"], frame)
    if payloads["favor_hook"] is not None:
        _normalize_favor(payloads["favor_hook"], frame)
    if payloads["truce"] is not None:
        normalize_raiktor_surrender_truce(
            payloads["truce"],
            expected_war_id=frame["war_id"],
            expected_snapshot_revision=frame["snapshot_revision"],
            expected_native_revision=frame["native_revision"],
            expected_date_raw=frame["date_raw"],
            expected_attacker_character_id=frame[
                "primary_attacker_character_id"
            ],
            expected_defender_character_id=frame[
                "primary_defender_character_id"
            ],
        )
    war_bound = payloads["generic_war_bound_current"]
    if war_bound is not None:
        normalize_raiktor_war_bound_regiment(
            war_bound,
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

    available = {
        "claims_base": claims is not None,
        **{name: payloads[name] is not None for name in _DOMAIN_ORDER[1:]},
    }
    missing = [name for name in _DOMAIN_ORDER if not available[name]]
    if root["missing_domains"] != missing:
        raise ValueError("Raiktor six-domain missing-domain list drifted")
    six_ready = all(available[name] for name in _DOMAIN_ORDER[1:])
    action_ready = available["claims_base"] and six_ready
    expected_status = "complete" if action_ready else "incomplete"
    if root["status"] != expected_status:
        raise ValueError("Raiktor six-domain status disagrees with readiness")

    cleanup_ready = False
    if war_bound is not None:
        cleanup = _exact_dict(
            war_bound["cleanup"], {"observable", "status"}, "cleanup"
        )
        cleanup_ready = cleanup["observable"] is True
    readiness = _exact_dict(root["readiness"], _READINESS_KEYS, "readiness")
    expected_readiness = {
        "claims_base_ready": available["claims_base"],
        "gold_ready": available["gold"],
        "prestige_ready": available["prestige"],
        "prisoner_release_ready": available["prisoner_release"],
        "favor_hook_ready": available["favor_hook"],
        "truce_ready": available["truce"],
        "generic_war_bound_current_ready": available[
            "generic_war_bound_current"
        ],
        "postwar_cleanup_ready": cleanup_ready,
        "source_specific_war_bound_ready": False,
        "pre_soldiers_ready": False,
        "proven_soldier_loss_ready": False,
        "six_dynamic_domains_ready": six_ready,
        "same_frame_stable": action_ready,
        "action_terms_ready": action_ready,
        "automatic_surrender_ready": False,
    }
    if readiness != expected_readiness:
        raise ValueError("Raiktor six-domain readiness overclaims evidence")
    return dict(root)


def _available_payload(
    value: object, frame: dict[str, object], name: str
) -> dict[str, object] | None:
    if not isinstance(value, dict) or "available" not in value:
        raise ValueError(f"{name} availability wrapper is malformed")
    available = _strict_bool(value["available"], f"{name}.available")
    if not available:
        if value != {"available": False}:
            raise ValueError(f"{name} unavailable wrapper invented payload")
        return None
    if set(value) != {"available", "frame", "payload"}:
        raise ValueError(f"{name} available wrapper is malformed")
    if _normalize_frame(value["frame"], f"{name}.frame") != frame:
        raise ValueError(f"{name} belongs to a different paused frame")
    payload = value["payload"]
    if not isinstance(payload, dict):
        raise ValueError(f"{name}.payload must be an object")
    return payload


def _normalize_frame(value: object, name: str) -> dict[str, object]:
    frame = _exact_dict(value, _FRAME_KEYS, name)
    normalized = {
        "snapshot_revision": _positive_uint64(
            frame["snapshot_revision"], f"{name}.snapshot_revision"
        ),
        "native_revision": _positive_uint64(
            frame["native_revision"], f"{name}.native_revision"
        ),
        "date_raw": _signed_int32(frame["date_raw"], f"{name}.date_raw"),
        "paused": _strict_bool(frame["paused"], f"{name}.paused"),
        "war_id": _full_id(frame["war_id"], f"{name}.war_id"),
        "active_casus_belli_database_index": _non_negative_int32(
            frame["active_casus_belli_database_index"],
            f"{name}.active_casus_belli_database_index",
        ),
        "active_casus_belli_key": frame["active_casus_belli_key"],
        "primary_attacker_character_id": _full_id(
            frame["primary_attacker_character_id"],
            f"{name}.primary_attacker_character_id",
        ),
        "primary_defender_character_id": _full_id(
            frame["primary_defender_character_id"],
            f"{name}.primary_defender_character_id",
        ),
        "claimant_character_id": _full_id(
            frame["claimant_character_id"],
            f"{name}.claimant_character_id",
        ),
    }
    if (
        normalized["paused"] is not True
        or normalized["active_casus_belli_key"] != "raiktor_claim_cb"
        or normalized["primary_attacker_character_id"]
        == normalized["primary_defender_character_id"]
    ):
        raise ValueError(f"{name} is not an exact paused Raiktor frame")
    return normalized


def _normalize_claims(value: object) -> None:
    claims = _exact_dict(value, _CLAIMS_KEYS, "claims_base.payload")
    if (
        claims["target_order_stable"] is not True
        or claims["claim_rows_stable"] is not True
        or claims["attacker_defeat"]
        != {
            "declared_title_disposition": "unchanged",
            "claim_disposition": "remove_declared_target_claims",
        }
    ):
        raise ValueError("claims base surrender disposition drifted")
    title_ids = _id_list(
        claims["target_title_ids"], "claims_base.target_title_ids", True
    )
    rows = claims["claims"]
    if not isinstance(rows, list) or len(rows) != len(title_ids):
        raise ValueError("claims base rows do not match target order")
    for index, (row_value, title_id) in enumerate(
        zip(rows, title_ids, strict=True)
    ):
        row = row_value
        if not isinstance(row, dict):
            raise ValueError(f"claims[{index}] must be an object")
        present = _strict_bool(row.get("present"), f"claims[{index}].present")
        keys = (
            {"title_id", "present", "strong", "implicit", "state"}
            if present
            else {"title_id", "present", "state"}
        )
        if set(row) != keys or _positive_int32(
            row.get("title_id"), f"claims[{index}].title_id"
        ) != title_id:
            raise ValueError(f"claims[{index}] schema/order drifted")
        if not present:
            if row["state"] != "absent":
                raise ValueError(f"claims[{index}] absent state drifted")
            continue
        strong = _strict_bool(row["strong"], f"claims[{index}].strong")
        implicit = _strict_bool(
            row["implicit"], f"claims[{index}].implicit"
        )
        expected = (
            ("strong_" if strong else "weak_")
            + ("implicit" if implicit else "explicit")
        )
        if row["state"] != expected:
            raise ValueError(f"claims[{index}] state drifted")


def _normalize_gold(value: object, frame: dict[str, object]) -> None:
    gold = _exact_dict(value, _GOLD_KEYS, "gold.payload")
    attacker = frame["primary_attacker_character_id"]
    defender = frame["primary_defender_character_id"]
    _character_value(gold["attacker_current_gold"], attacker, "attacker gold")
    _character_value(gold["defender_current_gold"], defender, "defender gold")
    _character_value(
        gold["attacker_authoritative_monthly_gold_income"],
        attacker,
        "attacker monthly income",
    )
    _character_value(
        gold["defender_authoritative_monthly_gold_income"],
        defender,
        "defender monthly income",
    )
    transfer = _exact_dict(
        gold["actual_transfer"],
        {"from_character_id", "to_character_id", "value"},
        "actual_transfer",
    )
    if (
        _full_id(transfer["from_character_id"], "transfer.from") != attacker
        or _full_id(transfer["to_character_id"], "transfer.to") != defender
        or _fixed_point(transfer["value"], "transfer.value") < 0
        or gold["exact_primary_transfer_observed"] is not True
        or gold["same_frame_stable"] is not True
    ):
        raise ValueError("gold domain disagrees")


def _normalize_prestige(value: object, frame: dict[str, object]) -> None:
    prestige = _exact_dict(value, _PRESTIGE_KEYS, "prestige.payload")
    attacker = frame["primary_attacker_character_id"]
    _character_value(
        prestige["attacker_current_prestige"], attacker, "attacker prestige"
    )
    factor = _fixed_point(prestige["cb_prestige_factor"], "prestige factor")
    delta = _character_value(
        prestige["attacker_prestige_delta"], attacker, "prestige delta"
    )
    if (
        factor < 0
        or factor > (2**63 - 1) // 10
        or delta != -min(factor * 10, 1_000 * 100_000)
        or prestige["exact_factor_and_attacker_delta_observed"] is not True
        or prestige["same_frame_stable"] is not True
    ):
        raise ValueError("prestige domain disagrees")


def _normalize_prisoners(value: object, frame: dict[str, object]) -> None:
    prisoners = _exact_dict(value, _PRISONER_KEYS, "prisoner payload")
    attacker_participants = _id_list(
        prisoners["attacker_participant_ids"], "attacker participants", True
    )
    defender_participants = _id_list(
        prisoners["defender_participant_ids"], "defender participants", True
    )
    attacker_candidates = _id_list(
        prisoners["attacker_release_candidate_ids"],
        "attacker candidates",
        True,
    )
    defender_candidates = _id_list(
        prisoners["defender_release_candidate_ids"],
        "defender candidates",
        True,
    )
    attacker = frame["primary_attacker_character_id"]
    defender = frame["primary_defender_character_id"]
    if (
        attacker not in attacker_participants
        or defender not in defender_participants
        or attacker_candidates[0] != attacker
        or defender_candidates[0] != defender
        or set(attacker_participants) & set(defender_participants)
        or set(attacker_candidates) & set(defender_candidates)
        or prisoners["full_participant_scan"] is not True
        or prisoners["primary_and_first_three_successors_scanned"] is not True
        or prisoners["same_frame_stable"] is not True
    ):
        raise ValueError("prisoner domain scan disagrees")
    pairs = prisoners["release_pairs"]
    if not isinstance(pairs, list):
        raise ValueError("prisoner release pairs must be a list")
    seen: set[tuple[int, int]] = set()
    for index, pair_value in enumerate(pairs):
        pair = _exact_dict(
            pair_value,
            {"jailer_character_id", "prisoner_character_id", "reason"},
            f"release_pairs[{index}]",
        )
        jailer = _full_id(pair["jailer_character_id"], "pair.jailer")
        prisoner = _full_id(pair["prisoner_character_id"], "pair.prisoner")
        forward = jailer in attacker_participants and prisoner in defender_candidates
        reverse = jailer in defender_participants and prisoner in attacker_candidates
        if (
            jailer == prisoner
            or forward == reverse
            or (jailer, prisoner) in seen
            or pair["reason"]
            != "opposite_primary_or_first_three_successors"
        ):
            raise ValueError(f"release_pairs[{index}] disagrees")
        seen.add((jailer, prisoner))


def _normalize_favor(value: object, frame: dict[str, object]) -> None:
    favor = _exact_dict(value, _FAVOR_KEYS, "favor payload")
    distinct = _strict_bool(
        favor["claimant_distinct_from_attacker"], "favor.distinct"
    )
    traversed = _strict_bool(
        favor["original_visible_root_traversed"], "favor.traversed"
    )
    applies = _strict_bool(favor["will_apply"], "favor.will_apply")
    if (
        distinct
        != (
            frame["claimant_character_id"]
            != frame["primary_attacker_character_id"]
        )
        or favor["same_frame_stable"] is not True
        or (distinct and not traversed)
        or (not distinct and (traversed or applies))
    ):
        raise ValueError("favor domain disagrees")


def _character_value(value: object, expected_id: object, name: str) -> int:
    item = _exact_dict(value, {"character_id", "value"}, name)
    if _full_id(item["character_id"], f"{name}.character_id") != expected_id:
        raise ValueError(f"{name} identity disagrees")
    return _fixed_point(item["value"], f"{name}.value")


def _fixed_point(value: object, name: str) -> int:
    point = _exact_dict(value, {"raw", "scale"}, name)
    raw = _signed_int64(point["raw"], f"{name}.raw")
    if point["scale"] != 100_000:
        raise ValueError(f"{name}.scale disagrees")
    return raw


def _id_list(value: object, name: str, require_nonempty: bool) -> list[int]:
    if not isinstance(value, list) or (require_nonempty and not value):
        raise ValueError(f"{name} must be a nonempty list")
    result = [_full_id(item, f"{name}[]") for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicate generations")
    return result


def _exact_dict(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} has a malformed schema")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _full_id(value: object, name: str) -> int:
    result = _signed_int32(value, name)
    if result == -1:
        raise ValueError(f"{name} is the invalid sentinel")
    return result


def _positive_int32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value <= 0 or value > 2**31 - 1:
        raise ValueError(f"{name} is outside positive int32")
    return value


def _non_negative_int32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < 0 or value > 2**31 - 1:
        raise ValueError(f"{name} is outside non-negative int32")
    return value


def _signed_int32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < -(2**31) or value > 2**31 - 1:
        raise ValueError(f"{name} is outside int32")
    return value


def _signed_int64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < -(2**63) or value > 2**63 - 1:
        raise ValueError(f"{name} is outside int64")
    return value


def _positive_uint64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value <= 0 or value > 2**64 - 1:
        raise ValueError(f"{name} is outside positive uint64")
    return value
