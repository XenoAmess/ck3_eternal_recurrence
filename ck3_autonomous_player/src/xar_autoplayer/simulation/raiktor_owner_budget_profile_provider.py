"""Strict file provider for an owner-authored Raiktor budget profile.

The three-way exit policy intentionally has no built-in preference values.
This provider turns one explicitly supplied owner source artifact into the
existing ``raiktor-owner-budget-profile-v1`` input, binding the result to the
SHA-256 of the exact source bytes.  Missing input and draft input stay typed
RED; this module never substitutes fixture values or inferred thresholds.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    OWNER_BUDGET_PROFILE_CONTRACT,
    OWNER_BUDGET_PROVIDER,
    normalize_raiktor_owner_budget_profile,
)


SOURCE_CONTRACT = "raiktor-owner-budget-profile-source-v1"
PROVIDER_SCHEMA = "xar.ck3.raiktor_owner_budget_profile_provider.v1"

_SOURCE_KEYS = {
    "schema_version",
    "contract",
    "approval",
    "profile_id",
    "profile_provenance",
    "pairwise_limits",
    "white_peace_limits",
}
_APPROVAL_KEYS = {"status", "approved_by", "approved_at_utc"}
_PAIRWISE_SOURCE_KEYS = {
    "maximum_surrender_gold_transfer_raw",
    "maximum_surrender_prestige_loss_raw",
    "maximum_surrender_claims_removed",
    "allow_surrender_favor_hook",
    "maximum_surrender_truce_days",
    "maximum_continue_tail_loss_raw",
    "minimum_switch_margin_raw",
}
_WHITE_LIMIT_KEYS = {
    "maximum_gold_transfer_raw",
    "maximum_prestige_loss_raw",
    "maximum_claims_removed",
    "allow_favor_hook",
    "maximum_truce_days",
}
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")
_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)


class OwnerBudgetProfileError(ValueError):
    """The owner-authored source is absent, malformed, or ambiguous."""


def render_raiktor_owner_budget_profile(
    source_value: object,
    *,
    source_sha256: str,
) -> dict[str, object]:
    """Render one strict source object into the policy's profile contract."""

    source = _exact_dict(source_value, _SOURCE_KEYS, "source")
    if source["schema_version"] != 1:
        raise OwnerBudgetProfileError("source schema_version must be 1")
    if source["contract"] != SOURCE_CONTRACT:
        raise OwnerBudgetProfileError("source contract drifted")
    profile_id = _nonempty_string(source["profile_id"], "profile_id")
    provenance = _nonempty_string(
        source["profile_provenance"], "profile_provenance"
    )
    approval = _normalize_approval(source["approval"])
    source_hash = _sha256(source_sha256, "source_sha256")

    pairwise_source = _exact_dict(
        source["pairwise_limits"],
        _PAIRWISE_SOURCE_KEYS,
        "pairwise_limits",
    )
    white_source = _exact_dict(
        source["white_peace_limits"],
        _WHITE_LIMIT_KEYS,
        "white_peace_limits",
    )
    approved = approval["status"] == "approved"
    profile = {
        "schema_version": 1,
        "contract": OWNER_BUDGET_PROFILE_CONTRACT,
        "status": "complete" if approved else "incomplete",
        "profile_id": profile_id,
        "profile_provenance": provenance,
        "profile_source_sha256": source_hash,
        "profile_production_eligible": approved,
        "pairwise_limits": {
            "schema_version": 1,
            "profile_id": profile_id,
            "profile_provenance": provenance,
            "profile_production_eligible": approved,
            **dict(pairwise_source),
        },
        "white_peace_limits": dict(white_source),
    }
    try:
        return normalize_raiktor_owner_budget_profile(profile)
    except ValueError as exc:
        raise OwnerBudgetProfileError(str(exc)) from exc


def provide_raiktor_owner_budget_profile(
    source_path: str | Path | None,
) -> dict[str, object]:
    """Load one source file or return a typed unavailable provider result."""

    if source_path is None:
        return {
            "schema": PROVIDER_SCHEMA,
            "provider": OWNER_BUDGET_PROVIDER,
            "status": "unavailable",
            "source": None,
            "profile_available": False,
            "profile_production_eligible": False,
            "owner_budget_profile": None,
            "blockers": ["owner_budget_profile_unavailable"],
            "boundaries": _boundaries(),
        }

    path = Path(source_path).resolve()
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise OwnerBudgetProfileError(
            f"cannot read owner budget source: {path}"
        ) from exc
    try:
        source = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OwnerBudgetProfileError(
            "owner budget source must be valid UTF-8 JSON"
        ) from exc

    source_hash = hashlib.sha256(payload).hexdigest().upper()
    profile = render_raiktor_owner_budget_profile(
        source, source_sha256=source_hash
    )
    production_eligible = profile["profile_production_eligible"] is True
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": OWNER_BUDGET_PROVIDER,
        "status": "available" if production_eligible else "incomplete",
        "source": {"path": str(path), "sha256": source_hash},
        "profile_available": True,
        "profile_production_eligible": production_eligible,
        "owner_budget_profile": profile,
        "blockers": (
            []
            if production_eligible
            else ["owner_budget_profile_not_owner_approved"]
        ),
        "boundaries": _boundaries(),
    }


def _normalize_approval(value: object) -> dict[str, object]:
    approval = _exact_dict(value, _APPROVAL_KEYS, "approval")
    status = approval["status"]
    if status not in {"draft", "approved"}:
        raise OwnerBudgetProfileError(
            "approval.status must be draft or approved"
        )
    if status == "draft":
        if approval["approved_by"] is not None:
            raise OwnerBudgetProfileError(
                "draft approval.approved_by must be null"
            )
        if approval["approved_at_utc"] is not None:
            raise OwnerBudgetProfileError(
                "draft approval.approved_at_utc must be null"
            )
        return {
            "status": "draft",
            "approved_by": None,
            "approved_at_utc": None,
        }

    approved_by = _nonempty_string(
        approval["approved_by"], "approval.approved_by"
    )
    approved_at = _utc_timestamp(
        approval["approved_at_utc"], "approval.approved_at_utc"
    )
    return {
        "status": "approved",
        "approved_by": approved_by,
        "approved_at_utc": approved_at,
    }


def _boundaries() -> list[str]:
    return [
        "no_default_or_fixture_thresholds",
        "approval_is_declared_by_the_explicit_source_artifact",
        "source_sha256_binds_exact_file_bytes",
        "profile_is_policy_input_not_campaign_evidence",
        "profile_is_policy_input_not_white_peace_evidence",
        "profile_does_not_authorize_an_action",
    ]


def _exact_dict(
    value: object, keys: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise OwnerBudgetProfileError(f"{name} has a malformed schema")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OwnerBudgetProfileError(f"{name} must be a nonempty string")
    return value


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise OwnerBudgetProfileError(f"{name} must be an uppercase SHA-256")
    return value


def _utc_timestamp(value: object, name: str) -> str:
    if not isinstance(value, str) or _UTC_TIMESTAMP_RE.fullmatch(value) is None:
        raise OwnerBudgetProfileError(
            f"{name} must be a second-precision UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OwnerBudgetProfileError(f"{name} is not a valid timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise OwnerBudgetProfileError(f"{name} must use UTC")
    return value


__all__ = [
    "OwnerBudgetProfileError",
    "PROVIDER_SCHEMA",
    "SOURCE_CONTRACT",
    "provide_raiktor_owner_budget_profile",
    "render_raiktor_owner_budget_profile",
]
