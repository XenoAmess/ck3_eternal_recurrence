#!/usr/bin/env python3
"""Project one qualified source-specific G2 lifecycle into policy intake.

The concrete lifecycle runner intentionally stops after proving source-bound
loss, cleanup and persisted expiry.  This offline adapter consumes that final
report without changing the frozen live runner.  It projects the observed
surrender outcome into the existing three-way policy while preserving the
remaining campaign, owner-budget and white-peace provider gaps.

No CK3 process, bridge pipe, launcher or input surface is used here.
"""

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
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import prepare_g2_postwar_retention_expiry_capture as retention  # noqa: E402
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (  # noqa: E402
    CAMPAIGN_PROVIDER,
    OBSERVED_SURRENDER_OUTCOME_CONTRACT,
    OWNER_BUDGET_PROVIDER,
    WHITE_PEACE_PROVIDER,
    assess_raiktor_three_way_exit,
)


REPORT_SCHEMA = "xar.ck3.g2_source_specific_war_loss_live_adapter_run.v1"
PREFLIGHT_STATUS = "READY_TO_RUN_G2_SOURCE_SPECIFIC_LIFECYCLE"
OUTER_SCHEMA = "xar.ck3.g2_source_specific_war_loss_outer_owner_run.v1"
LIFECYCLE_SCHEMA = "xar.ck3.g2_source_specific_war_loss_lifecycle_run.v1"
JOIN_SCHEMA = "xar.ck3.g2_source_specific_war_loss_join.v1"
OUTPUT_SCHEMA = "xar.ck3.g2_source_specific_comparison_intake.v1"
OUTPUT_STATUS = "GREEN_STATIC_SOURCE_SPECIFIC_COMPARISON_INTAKE"
EXPECTED_TRACE = [
    "exclusive-slot-acquired",
    "normal-event-process-started",
    "observer-breakpoint-restored",
    "observer-detached-without-kill",
    "same-process-alive-after-observer",
    "same-process-paused",
    "bridge-attached-to-capture-pid",
    "same-driver-lifecycle-continuation-complete",
    "outer-owner-final-cleanup",
    "exclusive-slot-released",
]
REMAINING_PROVIDERS = [
    "campaign-dominance-certificate",
    "owner-authored-budget-profile",
    "same-frame-white-peace-comparison-certificate",
]
_REPORT_BOUNDARY_KEYS = {
    "source_specific_loss_ready",
    "comparison_input_ready",
    "three_way_comparison_ready",
    "decision_ready",
    "automatic_surrender_ready",
    "gen034_closed",
}
_JOIN_READINESS_KEYS = {
    "private_live_evidence_classified",
    "action_bound_current_ready",
    "postwar_cleanup_ready",
    "source_specific_loss_ready",
    "comparison_input_ready",
    "three_way_comparison_ready",
    "decision_ready",
    "automatic_surrender_ready",
    "gen034_closed",
}
_NO_PROMOTION_KEYS = (
    "public_readiness_promoted",
    "action_readiness_promoted",
    "decision_ready",
    "automatic_surrender_ready",
    "gen034_closed",
)
_SHA256_RE = re.compile(r"^[0-9A-F]{64}$")


class IntakeError(ValueError):
    """The live report or its source-specific identity chain drifted."""


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise IntakeError(f"{name} must be an object")
    return value


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise IntakeError(f"{name} must be a positive integer")
    return value


def _nonnegative_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise IntakeError(f"{name} must be a nonnegative integer")
    return value


def _sha256(value: object, name: str) -> str:
    text = str(value).strip().upper()
    if _SHA256_RE.fullmatch(text) is None:
        raise IntakeError(f"{name} must be an uppercase SHA-256")
    return text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _exact_keys(
    value: dict[str, object], expected: set[str], name: str
) -> None:
    if set(value) != expected:
        raise IntakeError(
            f"{name} keys drifted: {sorted(value)} != {sorted(expected)}"
        )


def _all_true(value: object, name: str) -> bool:
    checks = _object(value, name)
    return bool(checks) and all(item is True for item in checks.values())


def _frozen_counts(
    generations_value: object,
) -> tuple[list[dict[str, object]], int, int]:
    if not isinstance(generations_value, list) or not generations_value:
        raise IntakeError("frozen generations must be a nonempty list")
    generations: list[dict[str, object]] = []
    current_count = 0
    army_ids: set[int] = set()
    for index, generation_value in enumerate(generations_value):
        generation = _object(
            generation_value, f"frozen_generations[{index}]"
        )
        rows = generation.get("current_rows")
        if not isinstance(rows, list) or not rows:
            raise IntakeError("each frozen generation needs current rows")
        for row_value in rows:
            row = _object(row_value, "frozen current row")
            army_ids.add(
                _positive_integer(row.get("raised_carmy_id"), "raised CArmy")
            )
            _positive_integer(
                row.get("current_army_regiment_id"),
                "current regiment generation",
            )
            current_count += 1
        generations.append(generation)
    return generations, current_count, len(army_ids)


def build_observed_surrender_outcome(
    report: dict[str, object], *, report_sha256: str
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate one GREEN lifecycle and project its policy observation."""

    report_hash = _sha256(report_sha256, "report_sha256")
    preflight = _object(report.get("preflight"), "report preflight")
    preflight_boundaries = _object(
        preflight.get("boundaries"), "preflight boundaries"
    )
    boundaries = _object(report.get("boundaries"), "report boundaries")
    _exact_keys(boundaries, _REPORT_BOUNDARY_KEYS, "report boundaries")
    outer = _object(report.get("outer_owner"), "outer owner")
    cleanup_proof = _object(report.get("cleanup"), "outer cleanup")
    ownership = _object(outer.get("ownership"), "outer ownership")
    handoff = _object(outer.get("observer_handoff"), "observer handoff")
    process_identity = _object(
        outer.get("process_identity"), "process identity"
    )
    lifecycle = _object(outer.get("lifecycle_result"), "lifecycle result")
    source = _object(lifecycle.get("source_normalization"), "source")
    ticket = _object(lifecycle.get("retention_ticket"), "retention ticket")
    sequence = _object(lifecycle.get("sequence"), "postwar sequence")
    join = _object(
        lifecycle.get("source_specific_loss_join"), "source-specific join"
    )
    join_identity = _object(join.get("identity"), "join identity")
    join_readiness = _object(join.get("readiness"), "join readiness")
    join_soldiers = _object(join.get("soldiers"), "join soldiers")
    receipt = _object(sequence.get("postwar_receipt"), "postwar receipt")
    receipt_binding = _object(
        receipt.get("session_binding"), "receipt session binding"
    )
    receipt_exact = _object(receipt.get("exact_build"), "receipt exact build")
    pre = _object(receipt.get("pre"), "receipt pre")
    termination = _object(receipt.get("termination"), "termination")
    post = _object(receipt.get("post"), "receipt post")
    post_cleanup = _object(
        post.get("war_bound_cleanup"), "postwar cleanup"
    )
    truce = _object(post.get("truce_expiry"), "persisted truce")
    receipt_boundaries = _object(
        receipt.get("boundaries"), "receipt boundaries"
    )
    source_set = _object(source.get("source_set"), "source set")

    pid = _positive_integer(join_identity.get("ck3_pid"), "lifecycle PID")
    war_id = _positive_integer(join_identity.get("war_id"), "WarID")
    expected_action = f"surrender-war-{war_id}"
    measured_at_creation = _positive_integer(
        join_soldiers.get("measured_at_creation"), "creation soldiers"
    )
    measured_before_termination = _positive_integer(
        join_soldiers.get("measured_before_termination"),
        "pre-termination soldiers",
    )
    measured_delta = _nonnegative_integer(
        join_soldiers.get("measured_creation_minus_current"),
        "creation-to-current loss",
    )
    post_termination_soldiers = _nonnegative_integer(
        join_soldiers.get("post_termination"), "post-termination soldiers"
    )
    surrender_boundary_loss = _positive_integer(
        join_soldiers.get("proven_surrender_boundary_loss"),
        "surrender-boundary loss",
    )
    _exact_keys(
        process_identity,
        {
            "normal_event_pid",
            "observer_pid",
            "bridge_pid",
            "lifecycle_pid",
        },
        "process identity",
    )
    process_pids = {
        _positive_integer(value, f"process_identity.{name}")
        for name, value in process_identity.items()
    }
    _exact_keys(join_readiness, _JOIN_READINESS_KEYS, "join readiness")
    receipt_validation = retention.validate_postwar_receipt(receipt, ticket)
    recorded_validation = _object(
        receipt.get("ticket_validation"), "recorded ticket validation"
    )
    generations, current_count, army_count = _frozen_counts(
        pre.get("frozen_generations")
    )

    positive_join_keys = (
        "private_live_evidence_classified",
        "action_bound_current_ready",
        "postwar_cleanup_ready",
        "source_specific_loss_ready",
        "comparison_input_ready",
    )
    negative_join_keys = (
        "three_way_comparison_ready",
        "decision_ready",
        "automatic_surrender_ready",
        "gen034_closed",
    )
    checks = {
        "report_green": report.get("schema") == REPORT_SCHEMA
        and report.get("status") == "GREEN",
        "preflight_green": preflight.get("status") == PREFLIGHT_STATUS
        and preflight_boundaries.get("ck3_started_or_attached") is False
        and preflight_boundaries.get("source_specific_loss_ready") is False
        and preflight_boundaries.get("comparison_input_ready") is False,
        "report_boundaries": boundaries["source_specific_loss_ready"] is True
        and boundaries["comparison_input_ready"] is True
        and all(
            boundaries[name] is False
            for name in (
                "three_way_comparison_ready",
                "decision_ready",
                "automatic_surrender_ready",
                "gen034_closed",
            )
        ),
        "outer_green": outer.get("schema") == OUTER_SCHEMA
        and outer.get("status") == "green-orchestration"
        and outer.get("ok") is True,
        "one_process": process_pids == {pid},
        "observer_handoff": handoff
        == {
            "breakpoint_restored": True,
            "debugger_detached": True,
            "process_terminated": False,
            "process_alive_after_detach": True,
        },
        "outer_ownership": ownership.get("exclusive_launch_owner")
        == "outer-owner"
        and ownership.get("same_driver_handoff") is True
        and ownership.get("final_cleanup_owner") == "outer-owner"
        and ownership.get("final_cleanup_calls") == 1,
        "stage_trace": outer.get("stage_trace") == EXPECTED_TRACE,
        "cleanup": cleanup_proof.get("ok") is True
        and cleanup_proof.get("driver_closed") is True
        and cleanup_proof.get("target_pid") == pid
        and cleanup_proof.get("remaining_ck3") == []
        and cleanup_proof.get("errors") == [],
        "lifecycle_green": lifecycle.get("schema") == LIFECYCLE_SCHEMA
        and lifecycle.get("status") == "green"
        and lifecycle.get("ok") is True,
        "source_normalized": source.get("status")
        == "normalized_private_capture"
        and source.get("capture_pid") == pid,
        "source_join_green": join.get("schema") == JOIN_SCHEMA
        and join.get("status")
        == "qualified_private_source_specific_loss_input"
        and _all_true(join.get("checks"), "source join checks"),
        "source_join_readiness": all(
            join_readiness[name] is True for name in positive_join_keys
        )
        and all(join_readiness[name] is False for name in negative_join_keys),
        "remaining_providers": join.get("remaining_providers")
        == REMAINING_PROVIDERS,
        "source_identity": source.get("source_set_sha256")
        == _sha256_json(source_set)
        == ticket.get("source_set_sha256")
        == join.get("source_set_sha256")
        and source.get("capture_sha256")
        == ticket.get("source_report_sha256"),
        "source_ticket": ticket.get("source_attribution_ready") is True
        and ticket.get("source_ck3_pid") == pid
        and ticket.get("war_id") == war_id
        and ticket.get("retention_ticket_id")
        == join.get("retention_ticket_id")
        == receipt.get("retention_ticket_id"),
        "session_binding": receipt_binding.get("ck3_pid") == pid
        and receipt_binding.get("connection_generation")
        == join_identity.get("connection_generation")
        and receipt_binding.get("episode_run_id")
        == join_identity.get("episode_run_id")
        and receipt_binding.get("war_id") == war_id,
        "one_mutation": lifecycle.get("mutation_commands") == [expected_action]
        and sequence.get("mutation_commands") == [expected_action]
        and receipt.get("mutation_commands") == [expected_action]
        and termination.get("step") == expected_action
        and termination.get("accepted") is True,
        "receipt_green": sequence.get("ok") is True
        and receipt_validation.get("ok") is True
        and recorded_validation.get("ok") is True
        and _all_true(
            recorded_validation.get("checks"), "recorded receipt checks"
        ),
        "receipt_stays_private": receipt_boundaries.get(
            "private_default_off"
        )
        is True
        and receipt_boundaries.get("source_specific_attribution_ready")
        is False
        and all(
            receipt_boundaries.get(name) is False
            for name in _NO_PROMOTION_KEYS
        ),
        "source_soldiers": measured_at_creation
        == source_set.get("measured_initial_soldiers")
        and measured_before_termination
        == ticket.get("pre_termination_soldiers")
        == pre.get("pre_termination_soldiers")
        and post_termination_soldiers == 0
        and surrender_boundary_loss
        == pre.get("pre_termination_soldiers")
        and measured_delta
        == measured_at_creation - measured_before_termination,
        "cleanup_destroyed": post_cleanup.get("status") == "destroyed"
        and post_cleanup.get("post_termination_soldiers") == 0
        and post_cleanup.get("proven_boundary_soldiers_lost")
        == pre.get("pre_termination_soldiers"),
    }
    if not all(checks.values()):
        failed = [name for name, ready in checks.items() if not ready]
        raise IntakeError(f"source-specific report checks failed: {failed}")

    projection = {
        "schema_version": 1,
        "contract": OBSERVED_SURRENDER_OUTCOME_CONTRACT,
        "status": "complete",
        "source_report_sha256": report_hash,
        "production_live": True,
        "private_default_off": True,
        "binding": {
            "exact_build_sha256": receipt_exact["game_executable_sha256"],
            "ck3_pid": pid,
            "connection_generation": receipt_binding[
                "connection_generation"
            ],
            "episode_run_id": receipt_binding["episode_run_id"],
            "character_id": receipt_binding["character_id"],
            "opponent_character_id": truce["to_character_id"],
            "war_id": war_id,
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
            "status": post_cleanup["status"],
            "frozen_generation_sha256": pre["frozen_generation_sha256"],
            "frozen_persistent_regiment_count": len(generations),
            "frozen_current_regiment_count": current_count,
            "frozen_army_count": army_count,
            "pre_termination_soldiers": pre["pre_termination_soldiers"],
            "post_termination_soldiers": post_cleanup[
                "post_termination_soldiers"
            ],
            "proven_boundary_soldiers_lost": post_cleanup[
                "proven_boundary_soldiers_lost"
            ],
            "source_specific_attribution_ready": True,
        },
        "truce": {
            "source": truce["source"],
            "formula_derived": truce["formula_derived"],
            "evaluated_days": truce["evaluated_days"],
            "queried_at_date_raw": truce["queried_at_date_raw"],
            "expiry_date_raw": truce["expiry_date_raw"],
        },
        "boundaries": {
            name: False for name in _NO_PROMOTION_KEYS
        },
    }
    return projection, {
        "report": checks,
        "receipt": receipt_validation,
        "source_set_sha256": source["source_set_sha256"],
    }


def run_intake(
    report_path: Path,
    output_path: Path,
    *,
    expected_report_sha256: str,
) -> dict[str, object]:
    """Read a frozen report and emit a deterministic offline intake."""

    report_path = report_path.resolve()
    output_path = output_path.resolve()
    if output_path.exists():
        raise IntakeError(f"output already exists: {output_path}")
    if not report_path.is_file():
        raise IntakeError(f"report is missing: {report_path}")
    expected_hash = _sha256(
        expected_report_sha256, "expected_report_sha256"
    )
    actual_hash = _sha256_file(report_path)
    if actual_hash != expected_hash:
        raise IntakeError(
            f"report hash differs: {actual_hash} != {expected_hash}"
        )
    try:
        report = _object(
            json.loads(report_path.read_text(encoding="utf-8")), "report"
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise IntakeError(f"could not read report: {error}") from error
    projection, validation = build_observed_surrender_outcome(
        report, report_sha256=actual_hash
    )
    policy = assess_raiktor_three_way_exit(
        None,
        None,
        None,
        None,
        None,
        observed_surrender_outcome_value=projection,
    )
    observed = _object(
        policy.get("observed_surrender_outcome"), "policy observation"
    )
    provider_names = {
        row.get("provider")
        for row in policy.get("provider_blockers", [])
        if isinstance(row, dict)
    }
    if (
        observed.get("status") != "source_specific_outcome_observed"
        or observed.get("source_specific_loss_comparison_ready") is not True
        or observed.get("comparison_input_ready") is not True
        or observed.get("blockers") != []
        or observed.get("next_provider") is not None
        or provider_names
        != {CAMPAIGN_PROVIDER, OWNER_BUDGET_PROVIDER, WHITE_PEACE_PROVIDER}
        or policy.get("three_way_comparison_ready") is not False
        or policy.get("recommended_outcome") is not None
        or policy.get("action_ready") is not False
        or policy.get("automatic_surrender_ready") is not False
    ):
        raise IntakeError("three-way policy did not preserve provider gaps")

    output = {
        "schema": OUTPUT_SCHEMA,
        "status": OUTPUT_STATUS,
        "ok": True,
        "source_report": str(report_path),
        "source_report_sha256": actual_hash,
        "validation": validation,
        "observed_surrender_outcome": projection,
        "three_way_policy_result": policy,
        "closed_gap": "source-specific live outcome is policy-consumable",
        "remaining_providers": list(REMAINING_PROVIDERS),
        "boundaries": {
            "ck3_started_or_attached": False,
            "source_specific_loss_comparison_ready": True,
            "three_way_comparison_ready": False,
            "public_readiness_promoted": False,
            "action_readiness_promoted": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--report-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        result = run_intake(
            arguments.report,
            arguments.output,
            expected_report_sha256=arguments.report_sha256,
        )
    except (IntakeError, retention.PreflightError, ValueError) as error:
        print(f"RED: {error}")
        return 2
    observation = _object(
        _object(result["three_way_policy_result"], "policy result")[
            "observed_surrender_outcome"
        ],
        "observed outcome",
    )
    print(
        f"{OUTPUT_STATUS} "
        f"observation={observation['observation_sha256']} "
        "source_specific_loss_comparison_ready=true "
        "three_way_comparison_ready=false gen034_closed=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
