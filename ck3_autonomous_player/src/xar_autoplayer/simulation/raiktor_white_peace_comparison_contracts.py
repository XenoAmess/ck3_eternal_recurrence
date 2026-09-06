"""Input contracts for the Raiktor white-peace comparison provider."""

from __future__ import annotations

import re


OBSERVATION_CONTRACT = "raiktor-white-peace-terms-observation-v1"
UTILITY_CONTRACT = "raiktor-white-peace-owner-utility-evaluation-v1"
OBSERVATION_COMPLETENESS_KEYS = {
    "final_recipient_response_ready",
    "claim_disposition_ready",
    "gold_transfer_ready",
    "prestige_delta_ready",
    "truce_ready",
    "prisoner_release_ready",
    "favor_hook_ready",
}

_OBSERVATION_KEYS = {
    "schema_version",
    "contract",
    "status",
    "frame",
    "evaluated_candidate_sha256",
    "evaluated_surrender_terms_sha256",
    "producer",
    "completeness",
    "option",
    "terms",
    "same_frame_stable",
}
_OBSERVATION_PRODUCER_KEYS = {
    "producer_id",
    "producer_version",
    "source_artifact_sha256",
    "production_live",
}
_UTILITY_KEYS = {
    "schema_version",
    "contract",
    "status",
    "frame",
    "evaluated_observation_sha256",
    "evaluated_campaign_sha256",
    "evaluated_owner_budget_sha256",
    "producer",
    "utility_bounds",
    "hard_budget_breaches",
    "model_risk_included",
}
_UTILITY_PRODUCER_KEYS = {
    "producer_id",
    "producer_version",
    "source_artifact_sha256",
    "utility_unit",
    "production_live",
}
_UTILITY_BOUND_KEYS = {
    "white_peace_lower_raw",
    "white_peace_upper_raw",
}
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class WhitePeaceComparisonProviderError(ValueError):
    """A supplied provider input has malformed or ambiguous semantics."""


def normalize_white_peace_terms_observation(
    value: object,
) -> dict[str, object]:
    item = _exact_dict(value, _OBSERVATION_KEYS, "observation")
    if item["schema_version"] != 1:
        raise WhitePeaceComparisonProviderError(
            "observation schema_version must be 1"
        )
    if item["contract"] != OBSERVATION_CONTRACT:
        raise WhitePeaceComparisonProviderError(
            "observation contract drifted"
        )
    if item["status"] not in {"complete", "incomplete"}:
        raise WhitePeaceComparisonProviderError(
            "observation status must be complete or incomplete"
        )
    frame = _object(item["frame"], "observation.frame")
    producer_item = _exact_dict(
        item["producer"],
        _OBSERVATION_PRODUCER_KEYS,
        "observation.producer",
    )
    producer = {
        "producer_id": _nonempty_string(
            producer_item["producer_id"], "observation.producer_id"
        ),
        "producer_version": _nonempty_string(
            producer_item["producer_version"],
            "observation.producer_version",
        ),
        "source_artifact_sha256": _sha256(
            producer_item["source_artifact_sha256"],
            "observation.source_artifact_sha256",
        ),
        "production_live": _strict_bool(
            producer_item["production_live"],
            "observation.production_live",
        ),
    }
    completeness_item = _exact_dict(
        item["completeness"],
        OBSERVATION_COMPLETENESS_KEYS,
        "observation.completeness",
    )
    completeness = {
        key: _strict_bool(
            completeness_item[key], f"observation.completeness.{key}"
        )
        for key in sorted(OBSERVATION_COMPLETENESS_KEYS)
    }
    return {
        "schema_version": 1,
        "contract": OBSERVATION_CONTRACT,
        "status": item["status"],
        "frame": dict(frame),
        "evaluated_candidate_sha256": _sha256(
            item["evaluated_candidate_sha256"],
            "observation.evaluated_candidate_sha256",
        ),
        "evaluated_surrender_terms_sha256": _sha256(
            item["evaluated_surrender_terms_sha256"],
            "observation.evaluated_surrender_terms_sha256",
        ),
        "producer": producer,
        "completeness": completeness,
        "option": dict(_object(item["option"], "observation.option")),
        "terms": dict(_object(item["terms"], "observation.terms")),
        "same_frame_stable": _strict_bool(
            item["same_frame_stable"],
            "observation.same_frame_stable",
        ),
    }


def normalize_white_peace_utility_evaluation(
    value: object,
) -> dict[str, object]:
    item = _exact_dict(value, _UTILITY_KEYS, "utility_evaluation")
    if item["schema_version"] != 1:
        raise WhitePeaceComparisonProviderError(
            "utility schema_version must be 1"
        )
    if item["contract"] != UTILITY_CONTRACT:
        raise WhitePeaceComparisonProviderError("utility contract drifted")
    if item["status"] not in {"complete", "incomplete"}:
        raise WhitePeaceComparisonProviderError(
            "utility status must be complete or incomplete"
        )
    producer_item = _exact_dict(
        item["producer"],
        _UTILITY_PRODUCER_KEYS,
        "utility_evaluation.producer",
    )
    utility_unit = _nonempty_string(
        producer_item["utility_unit"], "utility.producer.utility_unit"
    )
    if utility_unit != "owner_utility_q100000":
        raise WhitePeaceComparisonProviderError("utility unit drifted")
    producer = {
        "producer_id": _nonempty_string(
            producer_item["producer_id"], "utility.producer_id"
        ),
        "producer_version": _nonempty_string(
            producer_item["producer_version"], "utility.producer_version"
        ),
        "source_artifact_sha256": _sha256(
            producer_item["source_artifact_sha256"],
            "utility.source_artifact_sha256",
        ),
        "utility_unit": utility_unit,
        "production_live": _strict_bool(
            producer_item["production_live"], "utility.production_live"
        ),
    }
    bounds_item = _exact_dict(
        item["utility_bounds"],
        _UTILITY_BOUND_KEYS,
        "utility_evaluation.utility_bounds",
    )
    bounds = {
        key: _signed_int64(bounds_item[key], f"utility_bounds.{key}")
        for key in sorted(_UTILITY_BOUND_KEYS)
    }
    if bounds["white_peace_lower_raw"] > bounds["white_peace_upper_raw"]:
        raise WhitePeaceComparisonProviderError(
            "white-peace utility interval is inverted"
        )
    return {
        "schema_version": 1,
        "contract": UTILITY_CONTRACT,
        "status": item["status"],
        "frame": dict(_object(item["frame"], "utility.frame")),
        "evaluated_observation_sha256": _sha256(
            item["evaluated_observation_sha256"],
            "utility.evaluated_observation_sha256",
        ),
        "evaluated_campaign_sha256": _sha256(
            item["evaluated_campaign_sha256"],
            "utility.evaluated_campaign_sha256",
        ),
        "evaluated_owner_budget_sha256": _sha256(
            item["evaluated_owner_budget_sha256"],
            "utility.evaluated_owner_budget_sha256",
        ),
        "producer": producer,
        "utility_bounds": bounds,
        "hard_budget_breaches": _string_list(
            item["hard_budget_breaches"], "hard_budget_breaches"
        ),
        "model_risk_included": _strict_bool(
            item["model_risk_included"], "model_risk_included"
        ),
    }


def _exact_dict(
    value: object, keys: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise WhitePeaceComparisonProviderError(
            f"{name} has a malformed schema"
        )
    return value


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise WhitePeaceComparisonProviderError(f"{name} must be an object")
    return value


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise WhitePeaceComparisonProviderError(f"{name} must be a boolean")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WhitePeaceComparisonProviderError(
            f"{name} must be a nonempty string"
        )
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise WhitePeaceComparisonProviderError(
            f"{name} must be an uppercase SHA-256"
        )
    return value


def _signed_int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < -(2**63)
        or value > 2**63 - 1
    ):
        raise WhitePeaceComparisonProviderError(
            f"{name} must be a signed int64"
        )
    return value


def _string_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list):
        raise WhitePeaceComparisonProviderError(f"{name} must be a list")
    result = [_nonempty_string(item, f"{name}[]") for item in value]
    if len(result) != len(set(result)):
        raise WhitePeaceComparisonProviderError(
            f"{name} contains duplicates"
        )
    return result


__all__ = [
    "OBSERVATION_COMPLETENESS_KEYS",
    "OBSERVATION_CONTRACT",
    "UTILITY_CONTRACT",
    "WhitePeaceComparisonProviderError",
    "normalize_white_peace_terms_observation",
    "normalize_white_peace_utility_evaluation",
]
