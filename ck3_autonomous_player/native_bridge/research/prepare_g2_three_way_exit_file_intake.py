#!/usr/bin/env python3
"""Run the Raiktor three-way exit intake from hash-bound JSON artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.simulation.raiktor_three_way_exit_intake import (  # noqa: E402
    provide_raiktor_three_way_exit_intake,
)


MANIFEST_CONTRACT = "raiktor-three-way-exit-file-intake-manifest-v1"
OUTPUT_SCHEMA = "xar.ck3.g2_three_way_exit_file_intake.v1"
SOURCE_SPECIFIC_INTAKE_SCHEMA = (
    "xar.ck3.g2_source_specific_comparison_intake.v1"
)
SOURCE_SPECIFIC_INTAKE_STATUS = (
    "GREEN_STATIC_SOURCE_SPECIFIC_COMPARISON_INTAKE"
)
POSTWAR_INTAKE_SCHEMA = "xar.ck3.g2_postwar_comparison_intake.v1"
POSTWAR_INTAKE_STATUS = "GREEN_STATIC_R3_COMPARISON_INTAKE"
SOURCE_SPECIFIC_LOSS_PROVIDER = (
    "raiktor-source-specific-war-loss-attribution-provider-v1"
)
SOURCE_SPECIFIC_REMAINING_PROVIDERS = [
    "campaign-dominance-certificate",
    "owner-authored-budget-profile",
    "same-frame-white-peace-comparison-certificate",
]
_INPUT_NAMES = (
    "candidate",
    "surrender_terms",
    "campaign_certificate",
    "owner_budget_source",
    "white_peace_terms_observation",
    "white_peace_utility_evaluation",
    "observed_surrender_outcome",
)
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class FileIntakeError(ValueError):
    """A manifest, bound JSON input, or output path is invalid."""


def run_file_intake(
    manifest_path: Path,
    output_path: Path,
    *,
    expected_manifest_sha256: str,
) -> dict[str, object]:
    """Validate one manifest and write one deterministic offline result."""

    manifest_path = manifest_path.resolve()
    output_path = output_path.resolve()
    if output_path.exists():
        raise FileIntakeError(f"output already exists: {output_path}")
    manifest_bytes = _read_bytes(manifest_path, "manifest")
    manifest_sha = _file_sha256(manifest_bytes)
    if manifest_sha != _sha256(
        expected_manifest_sha256, "expected_manifest_sha256"
    ):
        raise FileIntakeError("manifest hash differs from expected SHA-256")
    manifest = _json_object(manifest_bytes, "manifest")
    if set(manifest) != {"schema_version", "contract", "inputs"}:
        raise FileIntakeError("manifest keys drifted")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("contract") != MANIFEST_CONTRACT
    ):
        raise FileIntakeError("manifest identity drifted")
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != set(_INPUT_NAMES):
        raise FileIntakeError("manifest input names drifted")

    values: dict[str, object | None] = {}
    bindings: dict[str, object] = {}
    for name in _INPUT_NAMES:
        value, binding = _load_bound_input(
            inputs[name], manifest_path.parent, name
        )
        values[name] = value
        bindings[name] = binding

    owner_binding = bindings["owner_budget_source"]
    owner_path = (
        owner_binding["path"]
        if isinstance(owner_binding, dict)
        and owner_binding.get("supplied") is True
        else None
    )
    observed_surrender_outcome = _extract_observed_surrender_outcome(
        values["observed_surrender_outcome"]
    )
    intake = provide_raiktor_three_way_exit_intake(
        candidate_value=values["candidate"],
        surrender_terms_value=values["surrender_terms"],
        campaign_value=values["campaign_certificate"],
        owner_budget_source_path=owner_path,
        white_peace_observation_value=values[
            "white_peace_terms_observation"
        ],
        white_peace_utility_evaluation_value=values[
            "white_peace_utility_evaluation"
        ],
        observed_surrender_outcome_value=observed_surrender_outcome,
    )
    output = {
        "schema": OUTPUT_SCHEMA,
        "status": intake["status"],
        "ok": True,
        "manifest": {
            "path": str(manifest_path),
            "sha256": manifest_sha,
        },
        "input_bindings": bindings,
        "intake_result": intake,
        "boundaries": {
            "ck3_started_or_attached": False,
            "bridge_queried": False,
            "mutation_commands": [],
            "production_recommendation_ready": False,
            "action_ready": False,
            "gen034_closed": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, output_path)
    return output


def _load_bound_input(
    value: object, manifest_root: Path, name: str
) -> tuple[dict[str, object] | None, dict[str, object]]:
    if value is None:
        return None, {"supplied": False, "path": None, "sha256": None}
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise FileIntakeError(f"{name} binding is malformed")
    raw_path = value.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise FileIntakeError(f"{name} path must be nonempty")
    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_root / path
    path = path.resolve()
    payload = _read_bytes(path, name)
    actual_sha = _file_sha256(payload)
    expected_sha = _sha256(value.get("sha256"), f"{name}.sha256")
    if actual_sha != expected_sha:
        raise FileIntakeError(f"{name} hash differs from manifest")
    return _json_object(payload, name), {
        "supplied": True,
        "path": str(path),
        "sha256": actual_sha,
    }


def _extract_observed_surrender_outcome(value: object) -> object:
    """Accept a raw outcome or either complete postwar intake envelope."""

    if not isinstance(value, dict):
        return value
    if value.get("schema") == POSTWAR_INTAKE_SCHEMA:
        return _extract_generic_postwar_outcome(value)
    if value.get("schema") != SOURCE_SPECIFIC_INTAKE_SCHEMA:
        return value
    expected_keys = {
        "schema",
        "status",
        "ok",
        "source_report",
        "source_report_sha256",
        "validation",
        "observed_surrender_outcome",
        "three_way_intake_result",
        "three_way_policy_result",
        "closed_gap",
        "remaining_providers",
        "boundaries",
    }
    if set(value) != expected_keys:
        raise FileIntakeError("source-specific intake keys drifted")
    boundaries = value.get("boundaries")
    expected_boundaries = {
        "ck3_started_or_attached": False,
        "source_specific_loss_comparison_ready": True,
        "three_way_comparison_ready": False,
        "public_readiness_promoted": False,
        "action_readiness_promoted": False,
        "decision_ready": False,
        "automatic_surrender_ready": False,
        "gen034_closed": False,
    }
    projection = value.get("observed_surrender_outcome")
    composed = value.get("three_way_intake_result")
    policy = value.get("three_way_policy_result")
    policy_observed = (
        policy.get("observed_surrender_outcome")
        if isinstance(policy, dict)
        else None
    )
    if (
        value.get("status") != SOURCE_SPECIFIC_INTAKE_STATUS
        or value.get("ok") is not True
        or value.get("remaining_providers")
        != SOURCE_SPECIFIC_REMAINING_PROVIDERS
        or boundaries != expected_boundaries
        or not isinstance(projection, dict)
        or projection.get("source_report_sha256")
        != value.get("source_report_sha256")
        or not isinstance(composed, dict)
        or composed.get("assessment") != policy
        or composed.get("production_recommendation_ready") is not False
        or composed.get("action_ready") is not False
        or composed.get("action_literal") is not None
        or not isinstance(policy, dict)
        or not isinstance(policy_observed, dict)
        or policy_observed.get("normalized") != projection
    ):
        raise FileIntakeError("source-specific intake boundary drifted")
    return projection


def _extract_generic_postwar_outcome(
    value: dict[str, object],
) -> dict[str, object]:
    expected_keys = {
        "schema",
        "status",
        "ok",
        "manifest",
        "manifest_sha256",
        "source_report",
        "source_report_sha256",
        "source_report_elapsed_seconds",
        "source_commit",
        "ck3_started_or_attached",
        "process_inventory_not_required_for_offline_artifact_read",
        "receipt_validation",
        "observed_surrender_outcome",
        "three_way_intake_result",
        "three_way_policy_result",
        "closed_gap",
        "remaining_gap",
        "boundaries",
    }
    expected_boundaries = {
        "r3_generic_boundary_used_as_source_specific_loss": False,
        "three_way_outcome_compared": False,
        "public_readiness_promoted": False,
        "action_readiness_promoted": False,
        "decision_ready": False,
        "automatic_surrender_ready": False,
        "gen034_closed": False,
    }
    projection = value.get("observed_surrender_outcome")
    composed = value.get("three_way_intake_result")
    policy = value.get("three_way_policy_result")
    policy_observed = (
        policy.get("observed_surrender_outcome")
        if isinstance(policy, dict)
        else None
    )
    validation = value.get("receipt_validation")
    receipt_validation = (
        validation.get("receipt") if isinstance(validation, dict) else None
    )
    outer_validation = (
        validation.get("outer") if isinstance(validation, dict) else None
    )
    receipt_checks = (
        receipt_validation.get("checks")
        if isinstance(receipt_validation, dict)
        else None
    )
    remaining = value.get("remaining_gap")
    if (
        set(value) != expected_keys
        or value.get("status") != POSTWAR_INTAKE_STATUS
        or value.get("ok") is not True
        or value.get("ck3_started_or_attached") is not False
        or value.get("process_inventory_not_required_for_offline_artifact_read")
        is not True
        or value.get("boundaries") != expected_boundaries
        or not isinstance(projection, dict)
        or projection.get("source_report_sha256")
        != value.get("source_report_sha256")
        or not isinstance(composed, dict)
        or composed.get("assessment") != policy
        or composed.get("status") != "evidence_required"
        or composed.get("production_recommendation_ready") is not False
        or composed.get("action_ready") is not False
        or composed.get("action_literal") is not None
        or not isinstance(policy_observed, dict)
        or policy_observed.get("normalized") != projection
        or not isinstance(receipt_validation, dict)
        or receipt_validation.get("ok") is not True
        or not isinstance(receipt_checks, dict)
        or not receipt_checks
        or not all(check is True for check in receipt_checks.values())
        or not isinstance(outer_validation, dict)
        or not outer_validation
        or not all(check is True for check in outer_validation.values())
        or not isinstance(remaining, dict)
        or remaining.get("reason")
        != "source_specific_war_loss_attribution_unavailable"
        or remaining.get("provider") != SOURCE_SPECIFIC_LOSS_PROVIDER
        or remaining.get("native_entry")
        != "spawn_army_post_finalize_rva_0x2e7f951"
    ):
        raise FileIntakeError("generic postwar intake boundary drifted")
    return projection


def _read_bytes(path: Path, name: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise FileIntakeError(f"cannot read {name}: {path}") from error


def _json_object(payload: bytes, name: str) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise FileIntakeError(f"{name} must be valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise FileIntakeError(f"{name} must be a JSON object")
    return value


def _file_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise FileIntakeError(f"{name} must be an uppercase SHA-256")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        result = run_file_intake(
            arguments.manifest,
            arguments.output,
            expected_manifest_sha256=arguments.manifest_sha256,
        )
    except (FileIntakeError, ValueError) as error:
        print(f"RED: {error}")
        return 2
    print(
        f"G2_THREE_WAY_FILE_INTAKE status={result['status']} "
        f"action_ready={str(result['boundaries']['action_ready']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
