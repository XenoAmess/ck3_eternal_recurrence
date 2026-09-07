"""Strict provider for an owner-authored Raiktor exit utility model.

The repository intentionally carries no default utility coefficients.  This
provider validates one explicit owner source artifact, binds it to the exact
source-file bytes, and keeps all downstream live/readiness claims false.  A
model source is configuration only: it is not a same-frame utility evaluation
and cannot authorize an in-game action.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


SOURCE_CONTRACT = "raiktor-owner-exit-utility-model-source-v1"
MODEL_CONTRACT = "raiktor-owner-exit-utility-model-v1"
PROVIDER_SCHEMA = "xar.ck3.raiktor_owner_exit_utility_model_provider.v1"
PROVIDER_ID = "raiktor-owner-exit-utility-model-file-provider-v1"
UTILITY_UNIT = "owner_utility_q100000"

_SOURCE_KEYS = {
    "schema_version",
    "contract",
    "approval",
    "model_id",
    "model_version",
    "utility_unit",
    "budget_profile_binding",
    "domain_coefficients_q100000",
    "nonlinear_policy",
    "uncertainty_policy",
    "tail_risk_policy",
}
_APPROVAL_KEYS = {"status", "approved_by", "approved_at_utc"}
_BUDGET_BINDING_KEYS = {"profile_id", "profile_source_sha256"}
_DOMAIN_COEFFICIENT_KEYS = {
    "primary_gold_transfer_raw",
    "attacker_prestige_delta_raw",
    "declared_claim_removed_count",
    "favor_hook_applied",
    "truce_day_count",
    "pow_release_count",
    "title_holder_change_count",
    "hostage_transfer_count",
    "war_bound_soldier_loss_count",
}
_POLICY_KEYS = {"rule_id", "parameters_raw"}
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")
_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1


class OwnerExitUtilityModelError(ValueError):
    """The owner utility source is absent, malformed, or ambiguous."""


def render_raiktor_owner_exit_utility_model(
    source_value: object,
    *,
    source_sha256: str,
) -> dict[str, object]:
    """Validate and normalize one owner-authored utility-model source."""

    source = _exact_dict(source_value, _SOURCE_KEYS, "source")
    if source["schema_version"] != 1:
        raise OwnerExitUtilityModelError("source schema_version must be 1")
    if source["contract"] != SOURCE_CONTRACT:
        raise OwnerExitUtilityModelError("source contract drifted")
    if source["utility_unit"] != UTILITY_UNIT:
        raise OwnerExitUtilityModelError(
            f"utility_unit must be {UTILITY_UNIT}"
        )

    approval = _normalize_approval(source["approval"])
    model_id = _nullable_nonempty_string(source["model_id"], "model_id")
    model_version = _nullable_nonempty_string(
        source["model_version"], "model_version"
    )
    source_hash = _sha256(source_sha256, "source_sha256")

    binding_source = _exact_dict(
        source["budget_profile_binding"],
        _BUDGET_BINDING_KEYS,
        "budget_profile_binding",
    )
    binding = {
        "profile_id": _nullable_nonempty_string(
            binding_source["profile_id"],
            "budget_profile_binding.profile_id",
        ),
        "profile_source_sha256": _nullable_sha256(
            binding_source["profile_source_sha256"],
            "budget_profile_binding.profile_source_sha256",
        ),
    }

    coefficient_source = _exact_dict(
        source["domain_coefficients_q100000"],
        _DOMAIN_COEFFICIENT_KEYS,
        "domain_coefficients_q100000",
    )
    coefficients = {
        key: _nullable_int64(
            coefficient_source[key], f"domain_coefficients_q100000.{key}"
        )
        for key in sorted(_DOMAIN_COEFFICIENT_KEYS)
    }
    policies = {
        name: _normalize_policy(source[name], name)
        for name in (
            "nonlinear_policy",
            "uncertainty_policy",
            "tail_risk_policy",
        )
    }

    choices = {
        "model_id": model_id,
        "model_version": model_version,
        "budget_profile_binding": binding,
        "domain_coefficients_q100000": coefficients,
        **policies,
    }
    missing_choices = _missing_leaf_paths(choices)
    approved = approval["status"] == "approved"
    if approved and missing_choices:
        joined = ", ".join(missing_choices)
        raise OwnerExitUtilityModelError(
            f"approved source has unresolved owner choices: {joined}"
        )

    return {
        "schema_version": 1,
        "contract": MODEL_CONTRACT,
        "status": "complete" if approved else "incomplete",
        "approval": approval,
        "model_id": model_id,
        "model_version": model_version,
        "utility_unit": UTILITY_UNIT,
        "model_source_sha256": source_hash,
        "budget_profile_binding": binding,
        "domain_coefficients_q100000": coefficients,
        **policies,
        "owner_approved_source_ready": approved,
        "missing_owner_choices": missing_choices,
    }


def provide_raiktor_owner_exit_utility_model(
    source_path: str | Path | None,
) -> dict[str, object]:
    """Load one source file or return a typed unavailable provider result."""

    if source_path is None:
        return _provider_result(
            status="unavailable",
            source=None,
            model=None,
            provider_blockers=["owner_exit_utility_model_source_unavailable"],
        )

    path = Path(source_path).resolve()
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise OwnerExitUtilityModelError(
            f"cannot read owner utility model source: {path}"
        ) from exc
    try:
        source_value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OwnerExitUtilityModelError(
            "owner utility model source must be valid UTF-8 JSON"
        ) from exc

    source_hash = hashlib.sha256(payload).hexdigest().upper()
    model = render_raiktor_owner_exit_utility_model(
        source_value,
        source_sha256=source_hash,
    )
    owner_ready = model["owner_approved_source_ready"] is True
    return _provider_result(
        status="available" if owner_ready else "incomplete",
        source={"path": str(path), "sha256": source_hash},
        model=model,
        provider_blockers=(
            []
            if owner_ready
            else ["owner_exit_utility_model_not_owner_approved"]
        ),
    )


def _provider_result(
    *,
    status: str,
    source: dict[str, str] | None,
    model: dict[str, object] | None,
    provider_blockers: list[str],
) -> dict[str, object]:
    owner_ready = bool(
        model is not None
        and model.get("owner_approved_source_ready") is True
    )
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": status,
        "source": source,
        "model_source_available": model is not None,
        "owner_approved_source_ready": owner_ready,
        "owner_exit_utility_model": model,
        "provider_blockers": provider_blockers,
        "downstream_readiness": {
            "production_live": False,
            "same_frame_utility_evaluation_ready": False,
            "white_peace_comparison_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
        "boundaries": [
            "no_default_or_fixture_utility_coefficients",
            "approval_is_declared_only_by_the_explicit_source_artifact",
            "source_sha256_binds_exact_file_bytes",
            "model_source_is_not_a_same_frame_utility_evaluation",
            "model_source_is_not_campaign_evidence",
            "model_source_does_not_authorize_an_action",
        ],
    }


def _normalize_approval(value: object) -> dict[str, object]:
    approval = _exact_dict(value, _APPROVAL_KEYS, "approval")
    status = approval["status"]
    if status not in {"draft", "approved"}:
        raise OwnerExitUtilityModelError(
            "approval.status must be draft or approved"
        )
    if status == "draft":
        if approval["approved_by"] is not None:
            raise OwnerExitUtilityModelError(
                "draft approval.approved_by must be null"
            )
        if approval["approved_at_utc"] is not None:
            raise OwnerExitUtilityModelError(
                "draft approval.approved_at_utc must be null"
            )
        return {
            "status": "draft",
            "approved_by": None,
            "approved_at_utc": None,
        }

    return {
        "status": "approved",
        "approved_by": _nonempty_string(
            approval["approved_by"], "approval.approved_by"
        ),
        "approved_at_utc": _utc_timestamp(
            approval["approved_at_utc"], "approval.approved_at_utc"
        ),
    }


def _normalize_policy(value: object, name: str) -> dict[str, object]:
    policy = _exact_dict(value, _POLICY_KEYS, name)
    rule_id = _nullable_nonempty_string(
        policy["rule_id"], f"{name}.rule_id"
    )
    parameters_value = policy["parameters_raw"]
    if parameters_value is None:
        parameters: dict[str, int] | None = None
    else:
        if not isinstance(parameters_value, dict):
            raise OwnerExitUtilityModelError(
                f"{name}.parameters_raw must be an object or null"
            )
        parameters = {}
        for key, parameter_value in sorted(parameters_value.items()):
            if not isinstance(key, str) or not key.strip():
                raise OwnerExitUtilityModelError(
                    f"{name}.parameters_raw keys must be nonempty strings"
                )
            parameters[key] = _int64(
                parameter_value, f"{name}.parameters_raw.{key}"
            )
    if (rule_id is None) != (parameters is None):
        raise OwnerExitUtilityModelError(
            f"{name}.rule_id and parameters_raw must be supplied together"
        )
    return {"rule_id": rule_id, "parameters_raw": parameters}


def _missing_leaf_paths(value: object, prefix: str = "") -> list[str]:
    if value is None:
        return [prefix]
    if isinstance(value, dict):
        missing: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            missing.extend(_missing_leaf_paths(child, child_prefix))
        return missing
    return []


def _exact_dict(
    value: object, keys: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise OwnerExitUtilityModelError(f"{name} has a malformed schema")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OwnerExitUtilityModelError(f"{name} must be a nonempty string")
    return value


def _nullable_nonempty_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _nonempty_string(value, name)


def _int64(value: object, name: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not _INT64_MIN <= value <= _INT64_MAX
    ):
        raise OwnerExitUtilityModelError(f"{name} must be a signed int64")
    return value


def _nullable_int64(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _int64(value, name)


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise OwnerExitUtilityModelError(
            f"{name} must be an uppercase SHA-256"
        )
    return value


def _nullable_sha256(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _sha256(value, name)


def _utc_timestamp(value: object, name: str) -> str:
    if not isinstance(value, str) or _UTC_TIMESTAMP_RE.fullmatch(value) is None:
        raise OwnerExitUtilityModelError(
            f"{name} must be a second-precision UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OwnerExitUtilityModelError(
            f"{name} is not a valid timestamp"
        ) from exc
    if parsed.tzinfo != timezone.utc:
        raise OwnerExitUtilityModelError(f"{name} must use UTC")
    return value


__all__ = [
    "MODEL_CONTRACT",
    "OwnerExitUtilityModelError",
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "SOURCE_CONTRACT",
    "UTILITY_UNIT",
    "provide_raiktor_owner_exit_utility_model",
    "render_raiktor_owner_exit_utility_model",
]
