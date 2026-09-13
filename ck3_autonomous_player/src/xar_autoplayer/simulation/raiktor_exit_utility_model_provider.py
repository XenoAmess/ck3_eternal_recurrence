"""Versioned strategy utility model provider for Raiktor war exits.

The checked-in default makes the bounded G2 policy runnable without a
machine-local approval artifact.  An operator can supply a complete override
bound to the default model identity.  The model is planner configuration; it
does not constitute CK3 observation, native-AI semantics, or action evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


SOURCE_CONTRACT = "raiktor-strategy-exit-utility-model-source-v2"
MODEL_CONTRACT = "raiktor-strategy-exit-utility-model-v2"
PROVIDER_SCHEMA = "xar.ck3.raiktor_exit_utility_model_provider.v1"
PROVIDER_ID = "raiktor-exit-utility-model-file-provider-v1"
UTILITY_UNIT = "strategy_utility_q100000"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_PATH = (
    REPOSITORY_ROOT / "strategies" / "raiktor_exit_utility_v1.json"
)
DEFAULT_BUDGET_PATH = (
    REPOSITORY_ROOT / "strategies" / "raiktor_exit_budget_v1.json"
)

_SOURCE_KEYS = {
    "schema_version",
    "contract",
    "model_version",
    "activation",
    "model_id",
    "model_provenance",
    "utility_unit",
    "budget_profile_binding",
    "domain_coefficients_q100000",
    "nonlinear_policy",
    "uncertainty_policy",
    "tail_risk_policy",
}
_ACTIVATION_KEYS = {
    "kind",
    "source",
    "base_model_id",
    "base_model_version",
}
_BUDGET_BINDING_KEYS = {
    "profile_id",
    "profile_version",
    "profile_source_sha256",
}
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
_SEMVER_RE = re.compile(r"^[1-9]\d*\.\d+\.\d+$")
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1


class ExitUtilityModelError(ValueError):
    """The strategy utility source is absent, malformed, or ambiguous."""


def render_raiktor_exit_utility_model(
    source_value: object,
    *,
    source_sha256: str,
) -> dict[str, object]:
    """Validate one complete versioned source and normalize its model."""

    source = _exact_dict(source_value, _SOURCE_KEYS, "source")
    if source["schema_version"] != 2:
        raise ExitUtilityModelError("source schema_version must be 2")
    if source["contract"] != SOURCE_CONTRACT:
        raise ExitUtilityModelError("source contract drifted")
    if source["utility_unit"] != UTILITY_UNIT:
        raise ExitUtilityModelError(f"utility_unit must be {UTILITY_UNIT}")

    activation = _normalize_activation(source["activation"])
    binding = _normalize_budget_binding(source["budget_profile_binding"])
    coefficients_source = _exact_dict(
        source["domain_coefficients_q100000"],
        _DOMAIN_COEFFICIENT_KEYS,
        "domain_coefficients_q100000",
    )
    coefficients = {
        key: _int64(
            coefficients_source[key],
            f"domain_coefficients_q100000.{key}",
        )
        for key in sorted(_DOMAIN_COEFFICIENT_KEYS)
    }

    return {
        "schema_version": 2,
        "contract": MODEL_CONTRACT,
        "status": "complete",
        "model_id": _nonempty_string(source["model_id"], "model_id"),
        "model_version": _semantic_version(
            source["model_version"], "model_version"
        ),
        "model_provenance": _nonempty_string(
            source["model_provenance"], "model_provenance"
        ),
        "utility_unit": UTILITY_UNIT,
        "model_source_sha256": _sha256(source_sha256, "source_sha256"),
        "activation": activation,
        "budget_profile_binding": binding,
        "domain_coefficients_q100000": coefficients,
        "nonlinear_policy": _normalize_policy(
            source["nonlinear_policy"], "nonlinear_policy"
        ),
        "uncertainty_policy": _normalize_policy(
            source["uncertainty_policy"], "uncertainty_policy"
        ),
        "tail_risk_policy": _normalize_policy(
            source["tail_risk_policy"], "tail_risk_policy"
        ),
        "model_production_eligible": True,
    }


def provide_raiktor_exit_utility_model(
    source_path: str | Path | None = None,
) -> dict[str, object]:
    """Load the repository default or a complete versioned override."""

    default_source_used = source_path is None
    path = DEFAULT_MODEL_PATH if default_source_used else Path(source_path).resolve()
    payload = _read_payload(path)
    source = _decode_source(payload)
    activation = _normalize_activation(
        _exact_dict(source, _SOURCE_KEYS, "source")["activation"]
    )
    if default_source_used:
        if activation["kind"] != "repository_default":
            raise ExitUtilityModelError(
                "repository default must declare repository_default activation"
            )
    else:
        if activation["kind"] != "operator_override":
            raise ExitUtilityModelError(
                "explicit source must declare operator_override activation"
            )
        _require_default_base_identity(activation)

    source_hash = hashlib.sha256(payload).hexdigest().upper()
    model = render_raiktor_exit_utility_model(
        source, source_sha256=source_hash
    )
    _require_repository_budget_binding(model["budget_profile_binding"])
    return {
        "schema": PROVIDER_SCHEMA,
        "provider": PROVIDER_ID,
        "status": "available",
        "source": {"path": str(path), "sha256": source_hash},
        "source_kind": activation["kind"],
        "source_model_version": model["model_version"],
        "default_source_used": default_source_used,
        "model_available": True,
        "model_production_eligible": True,
        "exit_utility_model": model,
        "provider_blockers": [],
        "downstream_readiness": {
            "same_frame_utility_evaluation_ready": False,
            "white_peace_comparison_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
        "boundaries": [
            "versioned_repository_default_is_active",
            "operator_override_must_bind_default_model_identity",
            "model_binds_exact_repository_budget_bytes",
            "source_sha256_binds_exact_model_bytes",
            "model_is_strategy_configuration_not_ck3_observation",
            "model_is_not_native_ai_semantics",
            "model_alone_does_not_authorize_an_action",
        ],
    }


def _normalize_activation(value: object) -> dict[str, object]:
    activation = _exact_dict(value, _ACTIVATION_KEYS, "activation")
    kind = activation["kind"]
    if kind not in {"repository_default", "operator_override"}:
        raise ExitUtilityModelError(
            "activation.kind must be repository_default or operator_override"
        )
    source = _nonempty_string(activation["source"], "activation.source")
    base_id = activation["base_model_id"]
    base_version = activation["base_model_version"]
    if kind == "repository_default":
        if base_id is not None or base_version is not None:
            raise ExitUtilityModelError(
                "repository default cannot declare a base model"
            )
    else:
        base_id = _nonempty_string(base_id, "activation.base_model_id")
        base_version = _semantic_version(
            base_version, "activation.base_model_version"
        )
    return {
        "kind": kind,
        "source": source,
        "base_model_id": base_id,
        "base_model_version": base_version,
    }


def _normalize_budget_binding(value: object) -> dict[str, str]:
    binding = _exact_dict(value, _BUDGET_BINDING_KEYS, "budget_profile_binding")
    return {
        "profile_id": _nonempty_string(
            binding["profile_id"], "budget_profile_binding.profile_id"
        ),
        "profile_version": _semantic_version(
            binding["profile_version"], "budget_profile_binding.profile_version"
        ),
        "profile_source_sha256": _sha256(
            binding["profile_source_sha256"],
            "budget_profile_binding.profile_source_sha256",
        ),
    }


def _normalize_policy(value: object, name: str) -> dict[str, object]:
    policy = _exact_dict(value, _POLICY_KEYS, name)
    parameters = policy["parameters_raw"]
    if not isinstance(parameters, dict):
        raise ExitUtilityModelError(f"{name}.parameters_raw must be an object")
    normalized: dict[str, int] = {}
    for key, item in sorted(parameters.items()):
        if not isinstance(key, str) or not key.strip():
            raise ExitUtilityModelError(
                f"{name}.parameters_raw keys must be nonempty strings"
            )
        normalized[key] = _int64(item, f"{name}.parameters_raw.{key}")
    return {
        "rule_id": _nonempty_string(policy["rule_id"], f"{name}.rule_id"),
        "parameters_raw": normalized,
    }


def _require_default_base_identity(activation: dict[str, object]) -> None:
    default = _decode_source(_read_payload(DEFAULT_MODEL_PATH))
    if (
        activation["base_model_id"] != default.get("model_id")
        or activation["base_model_version"] != default.get("model_version")
    ):
        raise ExitUtilityModelError("operator override base model identity drifted")


def _require_repository_budget_binding(binding: object) -> None:
    normalized = _normalize_budget_binding(binding)
    budget_payload = _read_payload(DEFAULT_BUDGET_PATH)
    budget = _decode_source(budget_payload)
    expected = {
        "profile_id": budget.get("profile_id"),
        "profile_version": budget.get("profile_version"),
        "profile_source_sha256": hashlib.sha256(budget_payload).hexdigest().upper(),
    }
    if normalized != expected:
        raise ExitUtilityModelError("repository budget profile binding drifted")


def _read_payload(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ExitUtilityModelError(f"cannot read utility model source: {path}") from exc


def _decode_source(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExitUtilityModelError(
            "utility model source must be valid UTF-8 JSON"
        ) from exc
    if not isinstance(value, dict):
        raise ExitUtilityModelError("source has a malformed schema")
    return value


def _exact_dict(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ExitUtilityModelError(f"{name} has a malformed schema")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExitUtilityModelError(f"{name} must be a nonempty string")
    return value


def _semantic_version(value: object, name: str) -> str:
    result = _nonempty_string(value, name)
    if _SEMVER_RE.fullmatch(result) is None:
        raise ExitUtilityModelError(f"{name} must be semantic version")
    return result


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ExitUtilityModelError(f"{name} must be an uppercase SHA-256")
    return value


def _int64(value: object, name: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not _INT64_MIN <= value <= _INT64_MAX
    ):
        raise ExitUtilityModelError(f"{name} must be a signed int64")
    return value


__all__ = [
    "DEFAULT_BUDGET_PATH",
    "DEFAULT_MODEL_PATH",
    "ExitUtilityModelError",
    "MODEL_CONTRACT",
    "PROVIDER_ID",
    "PROVIDER_SCHEMA",
    "SOURCE_CONTRACT",
    "UTILITY_UNIT",
    "provide_raiktor_exit_utility_model",
    "render_raiktor_exit_utility_model",
]
