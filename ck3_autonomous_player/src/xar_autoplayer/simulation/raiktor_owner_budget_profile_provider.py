"""Strict file provider for the versioned Raiktor strategy budget profile.

The repository carries one versioned default so GEN-034 is runnable without a
machine-local input file.  An operator may supply a complete versioned override
whose base identity matches that default.  Both paths render the existing
``raiktor-owner-budget-profile-v1`` policy input and bind it to the exact source
bytes.  These values are planner configuration, never CK3 observations.
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
VERSIONED_SOURCE_CONTRACT = "raiktor-strategy-budget-profile-source-v2"
PROVIDER_SCHEMA = "xar.ck3.raiktor_owner_budget_profile_provider.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILE_PATH = (
    REPOSITORY_ROOT / "strategies" / "raiktor_exit_budget_v1.json"
)

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
_VERSIONED_SOURCE_KEYS = {
    "schema_version",
    "contract",
    "profile_version",
    "activation",
    "profile_id",
    "profile_provenance",
    "pairwise_limits",
    "white_peace_limits",
}
_ACTIVATION_KEYS = {
    "kind",
    "source",
    "base_profile_id",
    "base_profile_version",
}
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
    """The strategy source is absent, malformed, or ambiguous."""


def render_raiktor_owner_budget_profile(
    source_value: object,
    *,
    source_sha256: str,
) -> dict[str, object]:
    """Render one strict source object into the policy's profile contract."""

    if not isinstance(source_value, dict):
        raise OwnerBudgetProfileError("source has a malformed schema")
    identity = (
        source_value.get("schema_version"),
        source_value.get("contract"),
    )
    if identity == (1, SOURCE_CONTRACT):
        source = _exact_dict(source_value, _SOURCE_KEYS, "source")
        approval = _normalize_approval(source["approval"])
        production_eligible = approval["status"] == "approved"
    elif identity == (2, VERSIONED_SOURCE_CONTRACT):
        source = _exact_dict(
            source_value, _VERSIONED_SOURCE_KEYS, "source"
        )
        _semantic_version(source["profile_version"], "profile_version")
        activation = _normalize_activation(source["activation"])
        if activation["kind"] == "operator_override":
            _require_default_base_identity(activation)
        production_eligible = True
    else:
        raise OwnerBudgetProfileError("source identity drifted")
    profile_id = _nonempty_string(source["profile_id"], "profile_id")
    provenance = _nonempty_string(
        source["profile_provenance"], "profile_provenance"
    )
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
    profile = {
        "schema_version": 1,
        "contract": OWNER_BUDGET_PROFILE_CONTRACT,
        "status": "complete" if production_eligible else "incomplete",
        "profile_id": profile_id,
        "profile_provenance": provenance,
        "profile_source_sha256": source_hash,
        "profile_production_eligible": production_eligible,
        "pairwise_limits": {
            "schema_version": 1,
            "profile_id": profile_id,
            "profile_provenance": provenance,
            "profile_production_eligible": production_eligible,
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
    """Load the repository default or one complete operator override."""

    default_source_used = source_path is None
    path = (
        DEFAULT_PROFILE_PATH
        if default_source_used
        else Path(source_path).resolve()
    )
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
    source_kind = _source_kind(source)
    if default_source_used and source_kind != "repository_default":
        raise OwnerBudgetProfileError(
            "repository default must declare repository_default activation"
        )
    if not default_source_used:
        _require_operator_override_base(source)
    profile = render_raiktor_owner_budget_profile(
        source, source_sha256=source_hash
    )
    production_eligible = profile["profile_production_eligible"] is True
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": OWNER_BUDGET_PROVIDER,
        "status": "available" if production_eligible else "incomplete",
        "source": {"path": str(path), "sha256": source_hash},
        "source_kind": source_kind,
        "source_profile_version": source.get("profile_version"),
        "default_source_used": default_source_used,
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


def _normalize_activation(value: object) -> dict[str, object]:
    activation = _exact_dict(value, _ACTIVATION_KEYS, "activation")
    kind = activation["kind"]
    if kind not in {"repository_default", "operator_override"}:
        raise OwnerBudgetProfileError(
            "activation.kind must be repository_default or operator_override"
        )
    source = _nonempty_string(activation["source"], "activation.source")
    base_profile_id = activation["base_profile_id"]
    base_profile_version = activation["base_profile_version"]
    if kind == "repository_default":
        if base_profile_id is not None or base_profile_version is not None:
            raise OwnerBudgetProfileError(
                "repository default cannot declare a base profile"
            )
    else:
        _nonempty_string(base_profile_id, "activation.base_profile_id")
        _semantic_version(
            base_profile_version, "activation.base_profile_version"
        )
    return {
        "kind": kind,
        "source": source,
        "base_profile_id": base_profile_id,
        "base_profile_version": base_profile_version,
    }


def _source_kind(source: object) -> str:
    if not isinstance(source, dict):
        raise OwnerBudgetProfileError("source has a malformed schema")
    if (
        source.get("schema_version"), source.get("contract")
    ) == (1, SOURCE_CONTRACT):
        return "legacy_owner_artifact"
    if (
        source.get("schema_version"), source.get("contract")
    ) == (2, VERSIONED_SOURCE_CONTRACT):
        activation = _normalize_activation(source.get("activation"))
        return str(activation["kind"])
    raise OwnerBudgetProfileError("source identity drifted")


def _require_operator_override_base(source: object) -> None:
    if not isinstance(source, dict):
        raise OwnerBudgetProfileError("override source is malformed")
    identity = (source.get("schema_version"), source.get("contract"))
    if identity == (1, SOURCE_CONTRACT):
        return
    if identity != (2, VERSIONED_SOURCE_CONTRACT):
        raise OwnerBudgetProfileError("override source identity drifted")
    activation = _normalize_activation(source.get("activation"))
    if activation["kind"] != "operator_override":
        raise OwnerBudgetProfileError(
            "explicit versioned source must declare operator_override"
        )
    _require_default_base_identity(activation)


def _require_default_base_identity(activation: dict[str, object]) -> None:
    try:
        default = json.loads(DEFAULT_PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OwnerBudgetProfileError(
            "cannot read repository default profile"
        ) from exc
    if (
        activation["base_profile_id"] != default.get("profile_id")
        or activation["base_profile_version"]
        != default.get("profile_version")
    ):
        raise OwnerBudgetProfileError(
            "operator override base profile identity drifted"
        )


def _boundaries() -> list[str]:
    return [
        "versioned_repository_default_is_active",
        "explicit_versioned_operator_override_binds_default_profile_identity",
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


def _semantic_version(value: object, name: str) -> str:
    result = _nonempty_string(value, name)
    if re.fullmatch(r"[1-9]\d*\.\d+\.\d+", result) is None:
        raise OwnerBudgetProfileError(f"{name} must be semantic version")
    return result


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
    "DEFAULT_PROFILE_PATH",
    "PROVIDER_SCHEMA",
    "SOURCE_CONTRACT",
    "VERSIONED_SOURCE_CONTRACT",
    "provide_raiktor_owner_budget_profile",
    "render_raiktor_owner_budget_profile",
]
