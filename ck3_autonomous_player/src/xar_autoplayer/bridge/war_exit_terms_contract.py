"""Strict claim-CB exit-terms v2 wire contract.

This module deliberately accepts only the complete available union.  The
exact-build adapter must not advertise the capability until every dry-preview
collector and same-frame lifecycle gate can construct this object without
nulls, partial domains, or formula-derived substitutes.
"""

from __future__ import annotations


QUERY_WAR_TERMINATION_EXIT_TERMS_CAPABILITY = (
    "game.command.query-war-termination-exit-terms-v2-N"
)
QUERY_WAR_TERMINATION_EXIT_TERMS_STEP_PREFIX = (
    "query-war-termination-exit-terms-v2-"
)
SUPPORTED_SLICE = "claim_cb_exit_terms_v2"
FIXED_POINT_SCALE = 100_000

# Two paused live reads (final18/final19) reproduced the same native access
# violation at CK3 RVA 0x334C668 while resolving the projected truce scope.
# Keep the offline schema/fixtures, but do not project or dispatch this query
# in production until the exact visitor/scope ABI is closed and revalidated.
WAR_TERMINATION_EXIT_TERMS_PRODUCTION_ENABLED = False

RESOURCE_KINDS = (
    "prestige",
    "prestige_experience",
    "piety",
    "piety_experience",
    "legitimacy",
    "stress",
)
BALANCE_RESOURCE_KINDS = (
    "gold",
    "prestige",
    "prestige_experience",
    "piety",
    "piety_experience",
    "legitimacy",
    "stress",
)

_GAME_VERSION = "1.19.0.6"
_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
_CLAIM_SCRIPT_SHA256 = (
    "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
)
_WAR_EFFECTS_SHA256 = (
    "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D"
)
_WAR_VALUES_SHA256 = (
    "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B"
)
_EP3_EFFECTS_SHA256 = (
    "D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D"
)

_READINESS = {
    "same_frame_stable": True,
    "claim_temporary_lifecycle_verified": True,
    "white_peace_complete": True,
    "attacker_defeat_complete": True,
    "exit_terms_ready": True,
}

_ATTACKER_DEFEAT_DISPOSITION = {
        "declared_title_disposition": "unchanged",
        "claim_disposition": "remove_declared_target_claims",
}


def query_war_termination_exit_terms_step(war_id: int) -> str:
    """Build the one canonical v2 query literal."""
    return (
        QUERY_WAR_TERMINATION_EXIT_TERMS_STEP_PREFIX
        + str(_positive_int32(war_id, "war_id"))
    )


def parse_query_war_termination_exit_terms_step(
    step: object,
) -> int | None:
    """Parse a canonical positive full-generation WarID literal."""
    if not isinstance(step, str) or not step.startswith(
        QUERY_WAR_TERMINATION_EXIT_TERMS_STEP_PREFIX
    ):
        return None
    raw = step[len(QUERY_WAR_TERMINATION_EXIT_TERMS_STEP_PREFIX) :]
    if (
        not raw
        or not raw.isascii()
        or not raw.isdecimal()
        or raw.startswith("0")
    ):
        return None
    war_id = int(raw)
    return war_id if 0 < war_id <= 2**31 - 1 else None


def normalize_war_termination_exit_terms(
    value: object,
    *,
    expected_war_id: int | None = None,
) -> dict[str, object]:
    """Validate and normalize one complete claim-CB exit-terms observation."""
    expected_keys = {
        "schema_version",
        "status",
        "war_id",
        "date_raw",
        "casus_belli",
        "supported_slice",
        "player_side",
        "primary_attacker_character_id",
        "primary_defender_character_id",
        "claimant_character_id",
        "target_title_ids",
        "claims",
        "primary_resource_balances",
        "primary_monthly_gold_income",
        "outcomes",
        "readiness",
        "provenance",
    }
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("schema_version") != 2
        or value.get("status") != "available"
        or value.get("supported_slice") != SUPPORTED_SLICE
        or value.get("player_side") != "attacker"
    ):
        raise ValueError("native war_termination_exit_terms schema is malformed")

    war_id = _positive_int32(value.get("war_id"), "war_id")
    if expected_war_id is not None and war_id != _positive_int32(
        expected_war_id, "expected_war_id"
    ):
        raise ValueError("native exit-terms WarID mismatch")
    date_raw = _signed_int32(value.get("date_raw"), "date_raw")
    casus_belli = value.get("casus_belli")
    if (
        not isinstance(casus_belli, dict)
        or set(casus_belli) != {"database_index", "canonical_key"}
        or casus_belli.get("canonical_key") != "claim_cb"
    ):
        raise ValueError("native exit-terms CB identity is malformed")
    database_index = _non_negative_int32(
        casus_belli.get("database_index"), "casus_belli.database_index"
    )

    attacker_id = _positive_int32(
        value.get("primary_attacker_character_id"),
        "primary_attacker_character_id",
    )
    defender_id = _positive_int32(
        value.get("primary_defender_character_id"),
        "primary_defender_character_id",
    )
    if attacker_id == defender_id:
        raise ValueError("native exit-terms primary characters must differ")
    claimant_id = _positive_int32(
        value.get("claimant_character_id"), "claimant_character_id"
    )
    target_title_ids = _positive_id_list(
        value.get("target_title_ids"), "target_title_ids", nonempty=True
    )
    claims = _normalize_claims(value.get("claims"), target_title_ids)
    if any(row.get("present") is not True for row in claims):
        raise ValueError(
            "native claim-CB exit terms require every declared target claim"
        )
    primary_resource_balances = _normalize_resource_matrix(
        value.get("primary_resource_balances"),
        name="primary_resource_balances",
        attacker_id=attacker_id,
        defender_id=defender_id,
        resource_kinds=BALANCE_RESOURCE_KINDS,
    )
    primary_monthly_gold_income = _normalize_monthly_gold_income(
        value.get("primary_monthly_gold_income"),
        attacker_id=attacker_id,
        defender_id=defender_id,
    )

    outcomes = value.get("outcomes")
    expected_dispositions = {
        "white_peace": _white_peace_disposition(claims),
        "attacker_defeat": _ATTACKER_DEFEAT_DISPOSITION,
    }
    if not isinstance(outcomes, dict) or set(outcomes) != set(
        expected_dispositions
    ):
        raise ValueError("native exit-terms outcomes are malformed")
    normalized_outcomes = {
        outcome: _normalize_outcome(
            outcomes.get(outcome),
            outcome=outcome,
            expected_disposition=disposition,
            attacker_id=attacker_id,
            defender_id=defender_id,
            date_raw=date_raw,
        )
        for outcome, disposition in expected_dispositions.items()
    }
    if (
        normalized_outcomes["white_peace"]["cb_prestige_factor"]
        != normalized_outcomes["attacker_defeat"]["cb_prestige_factor"]
    ):
        raise ValueError("native exit-terms CB prestige factor drifted by outcome")

    readiness = value.get("readiness")
    if readiness != _READINESS:
        raise ValueError("native exit-terms readiness is not complete")
    provenance = _normalize_provenance(value.get("provenance"))
    return {
        "schema_version": 2,
        "status": "available",
        "war_id": war_id,
        "date_raw": date_raw,
        "casus_belli": {
            "database_index": database_index,
            "canonical_key": "claim_cb",
        },
        "supported_slice": SUPPORTED_SLICE,
        "player_side": "attacker",
        "primary_attacker_character_id": attacker_id,
        "primary_defender_character_id": defender_id,
        "claimant_character_id": claimant_id,
        "target_title_ids": target_title_ids,
        "claims": claims,
        "primary_resource_balances": {
            "values": primary_resource_balances
        },
        "primary_monthly_gold_income": {
            "values": primary_monthly_gold_income
        },
        "outcomes": normalized_outcomes,
        "readiness": dict(_READINESS),
        "provenance": provenance,
    }


def _normalize_claims(
    value: object, target_title_ids: list[int]
) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) != len(target_title_ids):
        raise ValueError("native exit-terms claims do not match target titles")
    rows: list[dict[str, object]] = []
    for index, (row, title_id) in enumerate(
        zip(value, target_title_ids, strict=True)
    ):
        name = f"claims[{index}]"
        if not isinstance(row, dict):
            raise ValueError(f"native {name} is malformed")
        present = _strict_bool(row.get("present"), f"{name}.present")
        expected_keys = (
            {"title_id", "present", "strong", "implicit", "state"}
            if present
            else {"title_id", "present", "state"}
        )
        if set(row) != expected_keys or _positive_int32(
            row.get("title_id"), f"{name}.title_id"
        ) != title_id:
            raise ValueError(f"native {name} schema/order is malformed")
        if not present:
            if row.get("state") != "absent":
                raise ValueError(f"native {name} absent state is malformed")
            rows.append({"title_id": title_id, "present": False, "state": "absent"})
            continue
        strong = _strict_bool(row.get("strong"), f"{name}.strong")
        implicit = _strict_bool(row.get("implicit"), f"{name}.implicit")
        state = (
            ("strong_" if strong else "weak_")
            + ("implicit" if implicit else "explicit")
        )
        if row.get("state") != state:
            raise ValueError(f"native {name} claim state is inconsistent")
        rows.append(
            {
                "title_id": title_id,
                "present": True,
                "strong": strong,
                "implicit": implicit,
                "state": state,
            }
        )
    return rows


def _normalize_outcome(
    value: object,
    *,
    outcome: str,
    expected_disposition: dict[str, str],
    attacker_id: int,
    defender_id: int,
    date_raw: int,
) -> dict[str, object]:
    expected_keys = {
        "claim_disposition",
        "recipient_response",
        "cb_prestige_factor",
        "primary_gold_transfers",
        "primary_resource_deltas",
        "truce",
        "prisoner_releases",
        "complete",
    }
    if (
        not isinstance(value, dict)
        or set(value) != expected_keys
        or value.get("complete") is not True
        or value.get("claim_disposition") != expected_disposition
    ):
        raise ValueError(f"native exit-terms {outcome} schema is malformed")
    factor = _fixed_point(
        value.get("cb_prestige_factor"),
        f"{outcome}.cb_prestige_factor",
        non_negative=True,
    )
    response = _normalize_recipient_response(
        value.get("recipient_response"), outcome=outcome
    )
    gold = _normalize_gold_transfers(
        value.get("primary_gold_transfers"),
        outcome=outcome,
        attacker_id=attacker_id,
        defender_id=defender_id,
    )
    resources = _normalize_resource_deltas(
        value.get("primary_resource_deltas"),
        outcome=outcome,
        attacker_id=attacker_id,
        defender_id=defender_id,
    )
    truce = _normalize_truce(
        value.get("truce"),
        outcome=outcome,
        attacker_id=attacker_id,
        defender_id=defender_id,
        date_raw=date_raw,
    )
    prisoners = _normalize_prisoner_releases(
        value.get("prisoner_releases"), outcome=outcome
    )
    return {
        "claim_disposition": dict(expected_disposition),
        "recipient_response": response,
        "cb_prestige_factor": factor,
        "primary_gold_transfers": {"values": gold},
        "primary_resource_deltas": {"values": resources},
        "truce": truce,
        "prisoner_releases": {"values": prisoners},
        "complete": True,
    }


def _normalize_monthly_gold_income(
    value: object, *, attacker_id: int, defender_id: int
) -> list[dict[str, int]]:
    if not isinstance(value, dict) or set(value) != {"values"}:
        raise ValueError(
            "native exit-terms primary_monthly_gold_income wrapper malformed"
        )
    rows = value.get("values")
    expected_ids = [attacker_id, defender_id]
    if not isinstance(rows, list) or len(rows) != len(expected_ids):
        raise ValueError(
            "native exit-terms primary_monthly_gold_income matrix incomplete"
        )
    normalized: list[dict[str, int]] = []
    for index, (row, expected_id) in enumerate(
        zip(rows, expected_ids, strict=True)
    ):
        if not isinstance(row, dict) or set(row) != {
            "character_id",
            "raw",
            "scale",
        }:
            raise ValueError(
                f"native monthly gold income row {index} malformed"
            )
        character_id = _positive_int32(
            row.get("character_id"), "monthly_gold_income.character_id"
        )
        if character_id != expected_id:
            raise ValueError(
                "native monthly gold income order is malformed"
            )
        fixed = _fixed_point(
            {"raw": row.get("raw"), "scale": row.get("scale")},
            f"monthly_gold_income[{index}]",
        )
        normalized.append({"character_id": character_id, **fixed})
    return normalized


def _normalize_recipient_response(
    value: object, *, outcome: str
) -> dict[str, object]:
    expected_keys = {
        "native_validator_passed",
        "acceptance_raw",
        "acceptance_scale",
        "decision_status_raw",
        "would_accept_now",
        "auto_accept",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ValueError(
            f"native exit-terms {outcome} recipient response malformed"
        )
    validator = _strict_bool(
        value.get("native_validator_passed"),
        f"{outcome}.recipient_response.native_validator_passed",
    )
    if not validator:
        raise ValueError(
            f"native exit-terms {outcome} validator did not pass"
        )
    acceptance = _fixed_point(
        {
            "raw": value.get("acceptance_raw"),
            "scale": value.get("acceptance_scale"),
        },
        f"{outcome}.recipient_response.acceptance",
    )
    status = _non_negative_int32(
        value.get("decision_status_raw"),
        f"{outcome}.recipient_response.decision_status_raw",
    )
    if status > 3:
        raise ValueError(
            f"native exit-terms {outcome} decision status is invalid"
        )
    auto_accept = _strict_bool(
        value.get("auto_accept"),
        f"{outcome}.recipient_response.auto_accept",
    )
    would_accept = _strict_bool(
        value.get("would_accept_now"),
        f"{outcome}.recipient_response.would_accept_now",
    )
    if status == 3:
        raise ValueError(
            f"native exit-terms {outcome} recipient decision unavailable"
        )
    expected_would_accept = validator and status != 2
    if would_accept != expected_would_accept:
        raise ValueError(
            f"native exit-terms {outcome} recipient response inconsistent"
        )
    return {
        "native_validator_passed": True,
        "acceptance_raw": acceptance["raw"],
        "acceptance_scale": FIXED_POINT_SCALE,
        "decision_status_raw": status,
        "would_accept_now": would_accept,
        "auto_accept": auto_accept,
    }


def _normalize_gold_transfers(
    value: object,
    *,
    outcome: str,
    attacker_id: int,
    defender_id: int,
) -> list[dict[str, int]]:
    if not isinstance(value, dict) or set(value) != {"values"}:
        raise ValueError(f"native exit-terms {outcome} gold wrapper malformed")
    rows = value.get("values")
    expected_count = 0 if outcome == "white_peace" else 1
    if not isinstance(rows, list) or len(rows) != expected_count:
        raise ValueError(f"native exit-terms {outcome} gold rows malformed")
    normalized: list[dict[str, int]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "from_character_id",
            "to_character_id",
            "raw",
            "scale",
        }:
            raise ValueError(f"native {outcome} gold row {index} malformed")
        if (
            _positive_int32(
                row.get("from_character_id"), "gold.from_character_id"
            )
            != attacker_id
            or _positive_int32(
                row.get("to_character_id"), "gold.to_character_id"
            )
            != defender_id
        ):
            raise ValueError(f"native {outcome} gold direction is malformed")
        fixed = _fixed_point(
            {"raw": row.get("raw"), "scale": row.get("scale")},
            f"{outcome}.gold[{index}]",
            non_negative=True,
        )
        normalized.append(
            {
                "from_character_id": attacker_id,
                "to_character_id": defender_id,
                **fixed,
            }
        )
    return normalized


def _normalize_resource_deltas(
    value: object,
    *,
    outcome: str,
    attacker_id: int,
    defender_id: int,
) -> list[dict[str, object]]:
    return _normalize_resource_matrix(
        value,
        name=f"{outcome}.primary_resource_deltas",
        attacker_id=attacker_id,
        defender_id=defender_id,
        resource_kinds=RESOURCE_KINDS,
    )


def _normalize_resource_matrix(
    value: object,
    *,
    name: str,
    attacker_id: int,
    defender_id: int,
    resource_kinds: tuple[str, ...],
) -> list[dict[str, object]]:
    if not isinstance(value, dict) or set(value) != {"values"}:
        raise ValueError(f"native exit-terms {name} wrapper malformed")
    rows = value.get("values")
    expected_pairs = [
        (character_id, resource_kind)
        for character_id in (attacker_id, defender_id)
        for resource_kind in resource_kinds
    ]
    if not isinstance(rows, list) or len(rows) != len(expected_pairs):
        raise ValueError(f"native exit-terms {name} matrix incomplete")
    normalized: list[dict[str, object]] = []
    for index, (row, expected) in enumerate(
        zip(rows, expected_pairs, strict=True)
    ):
        if not isinstance(row, dict) or set(row) != {
            "character_id",
            "resource_kind",
            "raw",
            "scale",
        }:
            raise ValueError(f"native {name} row {index} malformed")
        character_id = _positive_int32(
            row.get("character_id"), f"{name}.character_id"
        )
        resource_kind = row.get("resource_kind")
        if (character_id, resource_kind) != expected:
            raise ValueError(
                f"native {name} matrix order is malformed"
            )
        fixed = _fixed_point(
            {"raw": row.get("raw"), "scale": row.get("scale")},
            f"{name}[{index}]",
        )
        normalized.append(
            {
                "character_id": character_id,
                "resource_kind": resource_kind,
                **fixed,
            }
        )
    return normalized


def _normalize_truce(
    value: object,
    *,
    outcome: str,
    attacker_id: int,
    defender_id: int,
    date_raw: int,
) -> dict[str, int]:
    expected_keys = {
        "owner_character_id",
        "toward_character_id",
        "evaluated_days",
        "current_date_raw",
        "expiry_date_raw",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ValueError(f"native exit-terms {outcome} truce malformed")
    owner = _positive_int32(value.get("owner_character_id"), "truce.owner")
    toward = _positive_int32(
        value.get("toward_character_id"), "truce.toward"
    )
    days = _non_negative_int32(value.get("evaluated_days"), "truce.days")
    current = _signed_int32(value.get("current_date_raw"), "truce.current")
    expiry = _signed_int32(value.get("expiry_date_raw"), "truce.expiry")
    expected_expiry = current + 24 * days
    if (
        owner != attacker_id
        or toward != defender_id
        or current != date_raw
        or not -(2**31) <= expected_expiry <= 2**31 - 1
        or expiry != expected_expiry
    ):
        raise ValueError(f"native exit-terms {outcome} truce is inconsistent")
    return {
        "owner_character_id": owner,
        "toward_character_id": toward,
        "evaluated_days": days,
        "current_date_raw": current,
        "expiry_date_raw": expiry,
    }


def _normalize_prisoner_releases(
    value: object, *, outcome: str
) -> list[dict[str, object]]:
    if not isinstance(value, dict) or set(value) != {"values"}:
        raise ValueError(
            f"native exit-terms {outcome} prisoner wrapper malformed"
        )
    rows = value.get("values")
    if not isinstance(rows, list) or len(rows) > 64:
        raise ValueError(
            f"native exit-terms {outcome} prisoner rows malformed"
        )
    normalized: list[dict[str, object]] = []
    seen: set[tuple[int, int, str]] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {
            "jailer_character_id",
            "prisoner_character_id",
            "reason",
        }:
            raise ValueError(f"native {outcome} prisoner row {index} malformed")
        jailer = _positive_int32(
            row.get("jailer_character_id"), "prisoner.jailer"
        )
        prisoner = _positive_int32(
            row.get("prisoner_character_id"), "prisoner.character"
        )
        reason = row.get("reason")
        if (
            jailer == prisoner
            or not isinstance(reason, str)
            or not reason
            or len(reason) > 80
            or not reason.isascii()
            or any(
                not (char.islower() or char.isdigit() or char == "_")
                for char in reason
            )
            or (jailer, prisoner, reason) in seen
        ):
            raise ValueError(f"native {outcome} prisoner row {index} invalid")
        seen.add((jailer, prisoner, reason))
        normalized.append(
            {
                "jailer_character_id": jailer,
                "prisoner_character_id": prisoner,
                "reason": reason,
            }
        )
    return normalized


def _normalize_provenance(value: object) -> dict[str, str]:
    expected_keys = {
        "game_version",
        "executable_sha256",
        "claim_script_sha256",
        "war_effects_sha256",
        "war_values_sha256",
        "ep3_effects_sha256",
        "native_contract_sha256",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ValueError("native exit-terms provenance is malformed")
    expected = {
        "game_version": _GAME_VERSION,
        "executable_sha256": _EXECUTABLE_SHA256,
        "claim_script_sha256": _CLAIM_SCRIPT_SHA256,
        "war_effects_sha256": _WAR_EFFECTS_SHA256,
        "war_values_sha256": _WAR_VALUES_SHA256,
        "ep3_effects_sha256": _EP3_EFFECTS_SHA256,
    }
    if any(
        value.get(key) != expected_value
        for key, expected_value in expected.items()
    ):
        raise ValueError("native exit-terms source provenance drifted")
    contract_hash = value.get("native_contract_sha256")
    if not _sha256(contract_hash):
        raise ValueError("native exit-terms native contract hash malformed")
    return {**expected, "native_contract_sha256": contract_hash}


def _fixed_point(
    value: object, name: str, *, non_negative: bool = False
) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"native {name} fixed point malformed")
    raw = value.get("raw")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or not -(2**63) <= raw <= 2**63 - 1
        or (non_negative and raw < 0)
        or value.get("scale") != FIXED_POINT_SCALE
    ):
        raise ValueError(f"native {name} fixed point invalid")
    return {"raw": raw, "scale": FIXED_POINT_SCALE}


def _positive_id_list(
    value: object, name: str, *, nonempty: bool
) -> list[int]:
    if not isinstance(value, list) or (nonempty and not value) or len(value) > 4096:
        raise ValueError(f"native {name} list malformed")
    rows = [_positive_int32(item, f"{name}[]") for item in value]
    if len(set(rows)) != len(rows):
        raise ValueError(f"native {name} list contains duplicates")
    return rows


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 < value <= 2**31 - 1
    ):
        raise ValueError(f"native {name} must be a positive int32")
    return value


def _non_negative_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 2**31 - 1
    ):
        raise ValueError(f"native {name} must be a non-negative int32")
    return value


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
    ):
        raise ValueError(f"native {name} must be a signed int32")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"native {name} must be boolean")
    return value


def _sha256(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789ABCDEF" for char in value)
    )


def _white_peace_disposition(
    claims: list[dict[str, object]],
) -> dict[str, str]:
    """Project the exact claim_cb WP effect over the observed claim rows."""
    any_weak = any(
        row.get("present") is True and row.get("strong") is False
        for row in claims
    )
    return {
        "declared_title_disposition": "unchanged",
        "claim_disposition": (
            "retain_and_strengthen_weak"
            if any_weak
            else "retain_no_strength_change_already_strong"
        ),
    }
