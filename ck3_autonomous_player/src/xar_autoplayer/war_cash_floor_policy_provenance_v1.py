"""Candidate provenance gate for a player-authored wartime cash floor.

No policy is embedded here. A passing candidate is not a formal M5 amount:
the owner must separately prove the policy document is published and pinned,
the future/risk cash sources are complete, and the live frame is current.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .m5_observed_opportunity_selector import observed_frame


SCHEMA = "xar.ck3.war-cash-floor-policy.v1"
_DATE_RAW_PER_GAME_DAY = 24


def _nonnegative(value: object) -> bool:
    return type(value) is int and value >= 0


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789ABCDEF" for character in value
    )


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("war cash policy document repeats a JSON key")
        result[key] = value
    return result


def _claims(value: object, *, name: str) -> set[str]:
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item for item in value
    ) or len(value) != len(set(value)):
        raise ValueError(f"{name} needs distinct explicit claim identities")
    return set(value)


def assess_war_cash_floor_policy_candidate_v1(
    *, frame: Mapping[str, object], war_id: int, horizon_days: int,
    policy_document_bytes: bytes | None, pinned_policy_sha256: str | None,
    future_spend_claim_ids: list[str] | None,
    risk_spend_claim_ids: list[str] | None,
) -> dict[str, object]:
    """Validate one candidate policy floor and disjoint cash uses, fail closed.

    ``pinned_policy_sha256`` must come from a separately trusted reviewed
    configuration, never be calculated from the supplied document by caller.
    ``future_spend_claim_ids`` and ``risk_spend_claim_ids`` must come from
    separately checked same-frame source receipts, not from prose labels.
    """
    if not isinstance(frame, Mapping) or dict(frame) != observed_frame(frame):
        raise ValueError("war cash policy needs an exact observed source frame")
    if not _positive(war_id) or not _positive(horizon_days):
        raise ValueError("war cash policy needs a scoped frame and horizon")
    base = {
        "schema": SCHEMA, "source_frame": dict(frame), "war_id": war_id,
        "candidate_policy_floor_raw": None, "policy_sha256": None,
        "formal_cash_receipt_eligible": False,
    }
    if policy_document_bytes is None or pinned_policy_sha256 is None:
        return {**base, "status": "policy_source_unavailable_unknown"}
    if not isinstance(policy_document_bytes, bytes) or not _sha256(pinned_policy_sha256):
        raise ValueError("war cash policy needs pinned document bytes")
    document_sha = hashlib.sha256(policy_document_bytes).hexdigest().upper()
    if document_sha != pinned_policy_sha256:
        raise ValueError("war cash policy bytes differ from reviewed pin")
    try:
        policy = json.loads(policy_document_bytes.decode("utf-8"),
                            object_pairs_hook=_no_duplicates)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("war cash policy is not valid UTF-8 JSON") from error
    expected_keys = {
        "schema", "policy_id", "policy_version", "played_character_id",
        "episode_run_id", "war_id", "valid_from_date_raw",
        "valid_until_date_raw", "valid_through_horizon_days",
        "floor_raw", "gold_scale", "floor_purpose", "floor_claim_ids",
        "amount_basis", "reviewer_evidence_sha256",
    }
    if not isinstance(policy, dict) or set(policy) != expected_keys:
        raise ValueError("war cash policy document shape is incomplete")
    if (
        policy["schema"] != SCHEMA
        or not isinstance(policy["policy_id"], str) or not policy["policy_id"]
        or not isinstance(policy["policy_version"], str) or not policy["policy_version"]
        or policy["played_character_id"] != frame["played_character_id"]
        or policy["episode_run_id"] != frame["episode_run_id"]
        or policy["war_id"] != war_id
        or not _nonnegative(policy["valid_from_date_raw"])
        or not _nonnegative(policy["valid_until_date_raw"])
        or not (policy["valid_from_date_raw"] <= frame["date_raw"]
                <= policy["valid_until_date_raw"])
        or not _positive(policy["valid_through_horizon_days"])
        or policy["valid_through_horizon_days"] < horizon_days
        or policy["valid_until_date_raw"] < (
            frame["date_raw"] + horizon_days * _DATE_RAW_PER_GAME_DAY
        )
        or not _nonnegative(policy["floor_raw"])
        or policy["gold_scale"] != 100_000
        or policy["floor_purpose"] != "terminal_liquidity_after_horizon"
        or not isinstance(policy["amount_basis"], str) or not policy["amount_basis"]
        or not _sha256(policy["reviewer_evidence_sha256"])
    ):
        raise ValueError("war cash policy is stale, foreign or lacks reviewed basis")
    floor_claims = _claims(policy["floor_claim_ids"], name="floor")
    future_claims = _claims(future_spend_claim_ids, name="future spend")
    risk_claims = _claims(risk_spend_claim_ids, name="risk spend")
    if (floor_claims & future_claims or floor_claims & risk_claims
            or future_claims & risk_claims):
        raise ValueError("war cash floor, future and risk duplicate a cash use")
    return {
        **base, "status": "candidate_document_and_claims_valid",
        "candidate_policy_floor_raw": policy["floor_raw"],
        "policy_sha256": document_sha,
        "policy_id": policy["policy_id"],
        "policy_version": policy["policy_version"],
        "floor_claim_ids": sorted(floor_claims),
    }
