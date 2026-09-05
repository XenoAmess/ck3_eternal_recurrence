#!/usr/bin/env python3
"""Consume the retained G2 R3 postwar receipt in the three-way policy.

This is a no-launch, read-only artifact adapter.  It verifies the immutable
R3 report and the pre-existing retention ticket, projects only the measured
postwar facts, and passes that projection to the production three-way policy
core.  Generic war-bound cleanup remains ineligible as a source-specific loss
comparison input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
RESEARCH_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(RESEARCH_ROOT))

import prepare_g2_postwar_retention_expiry_capture as retention  # noqa: E402
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (  # noqa: E402
    OBSERVED_SURRENDER_OUTCOME_CONTRACT,
    SOURCE_SPECIFIC_LOSS_PROVIDER,
    assess_raiktor_three_way_exit,
)


DEFAULT_MANIFEST = (
    RESEARCH_ROOT
    / "fixtures"
    / "g2_postwar_comparison_intake_r3_manifest.json"
)
EXPECTED_MANIFEST_SCHEMA = (
    "xar.ck3.g2_postwar_comparison_intake_r3_manifest.v1"
)
EXPECTED_REPORT_KIND = (
    "ck3_g2_postwar_cleanup_expiry_private_live_acceptance"
)
EXPECTED_REPORT_STATUS = "green"
EXPECTED_OUTPUT_SCHEMA = "xar.ck3.g2_postwar_comparison_intake.v1"
EXPECTED_OUTPUT_STATUS = "GREEN_STATIC_R3_COMPARISON_INTAKE"
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class IntakeError(RuntimeError):
    """Immutable input, live boundary, or no-launch condition drifted."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise IntakeError(f"{name} must be an object")
    return value


def _integer(value: object, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise IntakeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise IntakeError(f"{name} must be >= {minimum}")
    return value


def _sha256(value: object, name: str) -> str:
    result = str(value).upper()
    if _SHA256_RE.fullmatch(result) is None:
        raise IntakeError(f"{name} must be an uppercase SHA-256")
    return result


def _load_object(path: Path, name: str) -> dict[str, object]:
    try:
        return _object(json.loads(path.read_text(encoding="utf-8")), name)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IntakeError(f"could not read {name}: {error}") from error


def _resolve(path_value: object, *, repo_root: Path) -> Path:
    path = Path(str(path_value))
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _checked_file(
    path_value: object,
    hash_value: object,
    *,
    repo_root: Path,
    name: str,
) -> Path:
    path = _resolve(path_value, repo_root=repo_root)
    if not path.is_file():
        raise IntakeError(f"{name} is missing: {path}")
    expected_hash = _sha256(hash_value, f"{name} hash")
    actual_hash = _sha256_file(path)
    if actual_hash != expected_hash:
        raise IntakeError(
            f"{name} hash differs: {actual_hash} != {expected_hash}"
        )
    return path


def _all_true(value: object, name: str) -> bool:
    checks = _object(value, name)
    return bool(checks) and all(item is True for item in checks.values())


def build_observed_surrender_outcome(
    report: dict[str, object],
    *,
    report_sha256: str,
    ticket: dict[str, object],
    expected: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate R3 and project the exact facts consumed by the policy."""

    sequence = _object(report.get("mcp_sequence"), "mcp_sequence")
    receipt = _object(sequence.get("postwar_receipt"), "postwar_receipt")
    validation = retention.validate_postwar_receipt(receipt, ticket)
    if validation.get("ok") is not True:
        raise IntakeError("R3 postwar receipt does not consume its ticket")
    recorded_validation = _object(
        receipt.get("ticket_validation"), "ticket_validation"
    )
    if (
        recorded_validation.get("ok") is not True
        or not _all_true(recorded_validation.get("checks"), "ticket checks")
    ):
        raise IntakeError("R3 recorded ticket validation is not all GREEN")

    policy = _object(report.get("policy"), "policy")
    cleanup_proof = _object(report.get("cleanup"), "cleanup")
    source_invariant = _object(
        report.get("source_invariant"), "source_invariant"
    )
    session = _object(report.get("session"), "session")
    report_identity = _object(report.get("identity"), "report identity")
    formal = _object(
        report.get("formal_private_capture"), "formal_private_capture"
    )
    exact_build = _object(receipt.get("exact_build"), "exact_build")
    binding = _object(receipt.get("session_binding"), "session_binding")
    pre = _object(receipt.get("pre"), "pre")
    termination = _object(receipt.get("termination"), "termination")
    post = _object(receipt.get("post"), "post")
    cleanup = _object(post.get("war_bound_cleanup"), "war_bound_cleanup")
    truce = _object(post.get("truce_expiry"), "truce_expiry")
    boundaries = _object(receipt.get("boundaries"), "receipt boundaries")

    expected_action = f"surrender-war-{expected['war_id']}"
    expected_false_boundaries = (
        "source_specific_attribution_ready",
        "public_readiness_promoted",
        "action_readiness_promoted",
        "decision_ready",
        "automatic_surrender_ready",
        "gen034_closed",
    )
    outer_checks = {
        "report_identity": report.get("kind") == EXPECTED_REPORT_KIND
        and report.get("status") == EXPECTED_REPORT_STATUS
        and report.get("ok") is True,
        "report_hash": report_sha256
        == _sha256(expected["source_report_sha256"], "source_report_sha256"),
        "exact_build": exact_build.get("game_executable_sha256")
        == expected["ck3_exe_sha256"],
        "candidate_binaries": report_identity.get("bridge_dll_sha256")
        == expected["bridge_dll_sha256"]
        and report_identity.get("bridge_injector_sha256")
        == expected["bridge_injector_sha256"],
        "ticket": receipt.get("retention_ticket_id")
        == expected["retention_ticket_id"],
        "binding": binding.get("character_id") == expected["character_id"]
        and binding.get("war_id") == expected["war_id"]
        and binding.get("ck3_pid") == session.get("pid")
        and truce.get("to_character_id") == expected["opponent_character_id"],
        "one_mutation": sequence.get("mutation_commands") == [expected_action]
        and policy.get("mutation_commands") == [expected_action]
        and receipt.get("mutation_commands") == [expected_action],
        "formal_capture": formal.get("retention_ticket_id")
        == expected["retention_ticket_id"]
        and formal.get("only_mutation") == expected_action
        and formal.get("cleanup_destroyed_must_come_from_exact_store_reader")
        is True
        and formal.get("war_id_absence_is_admission_only") is True,
        "sequence": sequence.get("ok") is True
        and _all_true(sequence.get("checks"), "sequence checks"),
        "session": session.get("ok") is True
        and session.get("mode") == "native-headless"
        and session.get("restart_count") == 0,
        "cleanup": cleanup_proof.get("ok") is True
        and cleanup_proof.get("shutdown_ok") is True
        and cleanup_proof.get("tree_gone") is True
        and cleanup_proof.get("cleanup_proven") is True
        and cleanup_proof.get("driver_closed") is True,
        "source_immutable": source_invariant.get("unchanged") is True
        and source_invariant.get("before") == source_invariant.get("after"),
        "boundaries": boundaries.get("private_default_off") is True
        and all(boundaries.get(name) is False for name in expected_false_boundaries),
    }
    if not all(outer_checks.values()):
        failed = [name for name, ready in outer_checks.items() if not ready]
        raise IntakeError(f"R3 outer report checks failed: {failed}")

    generations = pre.get("frozen_generations")
    if not isinstance(generations, list) or not generations:
        raise IntakeError("R3 frozen generations are unavailable")
    current_rows: list[dict[str, object]] = []
    army_ids: set[int] = set()
    for index, value in enumerate(generations):
        generation = _object(value, f"frozen_generations[{index}]")
        rows = generation.get("current_rows")
        if not isinstance(rows, list) or not rows:
            raise IntakeError("R3 frozen current rows are unavailable")
        for row_value in rows:
            row = _object(row_value, "current row")
            army_id = _integer(
                row.get("raised_carmy_id"), "raised_carmy_id", minimum=1
            )
            current_rows.append(row)
            army_ids.add(army_id)

    projection = {
        "schema_version": 1,
        "contract": OBSERVED_SURRENDER_OUTCOME_CONTRACT,
        "status": "partial",
        "source_report_sha256": report_sha256,
        "production_live": True,
        "private_default_off": True,
        "binding": {
            "exact_build_sha256": exact_build["game_executable_sha256"],
            "ck3_pid": binding["ck3_pid"],
            "connection_generation": binding["connection_generation"],
            "episode_run_id": binding["episode_run_id"],
            "character_id": binding["character_id"],
            "opponent_character_id": truce["to_character_id"],
            "war_id": binding["war_id"],
            "pre_snapshot_id": pre["snapshot_id"],
            "pre_revision": pre["revision"],
            "pre_native_revision": pre["native_revision"],
            "pre_date_raw": pre["date_raw"],
            "post_revision": post["revision"],
            "post_native_revision": post["native_revision"],
            "post_date_raw": post["date_raw"],
        },
        "termination": {
            "action_literal": termination["step"],
            "accepted": termination["accepted"],
            "receipt_id": termination["receipt_id"],
        },
        "war_bound_cleanup": {
            "status": cleanup["status"],
            "frozen_generation_sha256": pre["frozen_generation_sha256"],
            "frozen_persistent_regiment_count": len(generations),
            "frozen_current_regiment_count": len(current_rows),
            "frozen_army_count": len(army_ids),
            "pre_termination_soldiers": pre["pre_termination_soldiers"],
            "post_termination_soldiers": cleanup[
                "post_termination_soldiers"
            ],
            "proven_boundary_soldiers_lost": cleanup[
                "proven_boundary_soldiers_lost"
            ],
            "source_specific_attribution_ready": boundaries[
                "source_specific_attribution_ready"
            ],
        },
        "truce": {
            "source": truce["source"],
            "formula_derived": truce["formula_derived"],
            "evaluated_days": truce["evaluated_days"],
            "queried_at_date_raw": truce["queried_at_date_raw"],
            "expiry_date_raw": truce["expiry_date_raw"],
        },
        "boundaries": {
            name: boundaries[name]
            for name in expected_false_boundaries
            if name != "source_specific_attribution_ready"
        },
    }
    expected_counts = _object(expected.get("counts"), "expected counts")
    observed_counts = {
        "frozen_persistent_regiments": len(generations),
        "frozen_current_regiments": len(current_rows),
        "frozen_armies": len(army_ids),
        "pre_termination_soldiers": pre["pre_termination_soldiers"],
        "post_termination_soldiers": cleanup["post_termination_soldiers"],
        "proven_boundary_soldiers_lost": cleanup[
            "proven_boundary_soldiers_lost"
        ],
        "evaluated_days": truce["evaluated_days"],
    }
    if observed_counts != expected_counts:
        raise IntakeError(
            f"R3 observed counts drifted: {observed_counts} != {expected_counts}"
        )
    return projection, {"receipt": validation, "outer": outer_checks}


def run_preflight(
    manifest_path: Path,
    output_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    output_path = output_path.resolve()
    if output_path.exists():
        raise IntakeError(f"output already exists: {output_path}")
    manifest_path = manifest_path.resolve()
    manifest = _load_object(manifest_path, "manifest")
    if (
        manifest.get("schema") != EXPECTED_MANIFEST_SCHEMA
        or manifest.get("default_off") is not True
        or manifest.get("live_authorized") is not False
        or manifest.get("public_readiness_promoted") is not False
        or manifest.get("action_readiness_promoted") is not False
        or manifest.get("decision_ready") is not False
        or manifest.get("automatic_surrender_ready") is not False
        or manifest.get("gen034_closed") is not False
    ):
        raise IntakeError("comparison intake manifest boundary drifted")
    paths = _object(manifest.get("paths"), "paths")
    hashes = _object(manifest.get("sha256"), "sha256")
    expected = _object(manifest.get("expected"), "expected")
    source_report_path = _checked_file(
        paths["source_report"],
        hashes["source_report"],
        repo_root=repo_root,
        name="source report",
    )
    retention_manifest_path = _checked_file(
        paths["retention_manifest"],
        hashes["retention_manifest"],
        repo_root=repo_root,
        name="retention manifest",
    )
    current_pin_path = _checked_file(
        paths["current_pin_manifest"],
        hashes["current_pin_manifest"],
        repo_root=repo_root,
        name="current-pin manifest",
    )
    current_pin = _load_object(current_pin_path, "current-pin manifest")
    if current_pin.get("candidate_source_commit") != expected["source_commit"]:
        raise IntakeError("current-pin source commit drifted")
    current_pin_sha256 = _object(current_pin.get("sha256"), "current-pin hashes")
    if (
        current_pin_sha256.get("game_executable")
        != expected["ck3_exe_sha256"]
        or current_pin_sha256.get("bridge_dll")
        != expected["bridge_dll_sha256"]
        or current_pin_sha256.get("bridge_injector")
        != expected["bridge_injector_sha256"]
    ):
        raise IntakeError("current-pin exact-build identity drifted")
    retention_manifest = _load_object(
        retention_manifest_path, "retention manifest"
    )
    ticket = retention.build_retention_ticket(
        retention_manifest, repo_root=repo_root
    )
    source_report_sha256 = _sha256_file(source_report_path)
    if source_report_path.stat().st_size != expected["source_report_size_bytes"]:
        raise IntakeError("source report size drifted")
    source_report = _load_object(source_report_path, "source report")
    projection, validation = build_observed_surrender_outcome(
        source_report,
        report_sha256=source_report_sha256,
        ticket=ticket,
        expected=expected,
    )
    policy_result = assess_raiktor_three_way_exit(
        None,
        None,
        None,
        None,
        None,
        observed_surrender_outcome_value=projection,
    )
    observed_result = _object(
        policy_result.get("observed_surrender_outcome"),
        "observed_surrender_outcome",
    )
    if (
        observed_result.get("status")
        != "observed_generic_boundary_source_attribution_required"
        or observed_result.get("observed_checkpoint_boundary_ready") is not True
        or observed_result.get("source_specific_loss_comparison_ready")
        is not False
        or observed_result.get("comparison_input_ready") is not False
        or observed_result.get("blockers")
        != ["source_specific_war_loss_attribution_unavailable"]
        or observed_result.get("next_provider") != SOURCE_SPECIFIC_LOSS_PROVIDER
        or observed_result.get("next_native_entry")
        != "spawn_army_post_finalize_rva_0x2e7f951"
        or policy_result.get("recommended_outcome") is not None
        or policy_result.get("action_ready") is not False
        or policy_result.get("automatic_surrender_ready") is not False
    ):
        raise IntakeError("three-way policy did not preserve the R3 boundary")

    output = {
        "schema": EXPECTED_OUTPUT_SCHEMA,
        "status": EXPECTED_OUTPUT_STATUS,
        "ok": True,
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "source_report": str(source_report_path),
        "source_report_sha256": source_report_sha256,
        "source_report_elapsed_seconds": source_report["elapsed_seconds"],
        "source_commit": expected["source_commit"],
        "ck3_started_or_attached": False,
        "process_inventory_not_required_for_offline_artifact_read": True,
        "receipt_validation": validation,
        "observed_surrender_outcome": projection,
        "three_way_policy_result": policy_result,
        "closed_gap": (
            "R3 action-bound postwar facts are now consumed by the existing "
            "three-way policy core"
        ),
        "remaining_gap": {
            "reason": "source_specific_war_loss_attribution_unavailable",
            "provider": SOURCE_SPECIFIC_LOSS_PROVIDER,
            "native_entry": "spawn_army_post_finalize_rva_0x2e7f951",
            "required_observation": (
                "bind each bookmark.1071.a spawn_army execution to the "
                "selected loaded node and exact raiktor_claim_cb WarID, then "
                "freeze all six source-created persistent/current/CArmy "
                "generations before gameplay advances"
            ),
        },
        "boundaries": {
            "r3_generic_boundary_used_as_source_specific_loss": False,
            "three_way_outcome_compared": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        result = run_preflight(arguments.manifest, arguments.output)
    except (IntakeError, retention.PreflightError, ValueError) as error:
        print(f"RED: {error}")
        return 2
    observed = _object(
        _object(result["three_way_policy_result"], "policy result")[
            "observed_surrender_outcome"
        ],
        "observed surrender outcome",
    )
    print(
        f"{EXPECTED_OUTPUT_STATUS} "
        f"observation={observed['observation_sha256']} "
        "source_specific_loss_comparison_ready=false "
        "gen034_closed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
