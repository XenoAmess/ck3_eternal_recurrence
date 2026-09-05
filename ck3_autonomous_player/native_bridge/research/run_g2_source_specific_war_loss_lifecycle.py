#!/usr/bin/env python3
"""Compose one source-bound Raiktor surrender lifecycle.

This module deliberately owns no CK3 launch.  A future exclusive launch owner
passes the already connected driver from the *same* CK3 process whose six
``bookmark.1071.a`` ``spawn_army`` executions were captured.  The module then
performs the paused dual read, creates a source-bound retention ticket, and
continues through the existing one-surrender cleanup/expiry collector.

The command-line entry is a no-launch dependency preflight only.  It must not
be presented as live evidence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import prepare_g2_postwar_retention_expiry_capture as retention  # noqa: E402
import run_g2_postwar_cleanup_expiry_live_acceptance as postwar  # noqa: E402
import run_war_termination_terms_live_acceptance as terms  # noqa: E402
from xar_autoplayer.bridge.raiktor_source_specific_war_loss_contract import (  # noqa: E402
    CONTRACT as SOURCE_CONTRACT,
    EXPECTED_EXE_SHA256,
    normalize_raiktor_source_specific_capture,
)
from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (  # noqa: E402
    normalize_raiktor_war_bound_regiment,
)


MANIFEST_SCHEMA = "xar.ck3.g2_source_specific_war_loss_lifecycle_manifest.v1"
PREFLIGHT_SCHEMA = "xar.ck3.g2_source_specific_war_loss_lifecycle_preflight.v1"
JOIN_SCHEMA = "xar.ck3.g2_source_specific_war_loss_join.v1"
EXPECTED_STATUS = "GREEN_STATIC_SOURCE_SPECIFIC_LIFECYCLE_RUNNER"


class LifecycleContractError(ValueError):
    """The source/current/action/postwar identity chain is not exact."""


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise LifecycleContractError(f"{name} must be an object")
    return value


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise LifecycleContractError(f"{name} must be an integer >= {minimum}")
    return value


def _sha256_text(value: object, name: str) -> str:
    text = str(value).strip().upper()
    if len(text) != 64 or any(character not in "0123456789ABCDEF" for character in text):
        raise LifecycleContractError(f"{name} must be an uppercase SHA-256")
    return text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _resolve(path_value: object, *, repo_root: Path) -> Path:
    path = Path(str(path_value)).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _source_binding(
    normalized_source: dict[str, object],
    generations: list[dict[str, object]],
) -> dict[str, object]:
    source_set = _object(normalized_source.get("source_set"), "source_set")
    executions = source_set.get("executions")
    if not isinstance(executions, list) or len(executions) != 6:
        raise LifecycleContractError("source_set must contain six executions")

    expected: dict[int, dict[str, object]] = {}
    expected_armies: set[int] = set()
    expected_currents: set[int] = set()
    for execution_value in executions:
        execution = _object(execution_value, "source execution")
        army_id = _integer(execution.get("army_generation_id"), "source army")
        expected_armies.add(army_id)
        persistent_rows = execution.get("persistent_regiments")
        if not isinstance(persistent_rows, list):
            raise LifecycleContractError("source persistent rows are missing")
        for persistent_value in persistent_rows:
            persistent = _object(persistent_value, "source persistent row")
            persistent_id = _integer(
                persistent.get("generation_id"), "source persistent generation"
            )
            current_ids = persistent.get("current_regiment_ids")
            if (
                persistent_id in expected
                or not isinstance(current_ids, list)
                or not current_ids
            ):
                raise LifecycleContractError("source persistent mapping is invalid")
            mapped = {
                _integer(value, "source current generation") for value in current_ids
            }
            if len(mapped) != len(current_ids) or expected_currents.intersection(mapped):
                raise LifecycleContractError("source current mapping is not one-to-one")
            expected_currents.update(mapped)
            expected[persistent_id] = {
                "army_generation_id": army_id,
                "current_generation_ids": mapped,
            }

    actual_persistent: set[int] = set()
    actual_currents: set[int] = set()
    actual_armies: set[int] = set()
    current_soldiers = 0
    for generation_value in generations:
        generation = _object(generation_value, "current generation row")
        persistent_id = _integer(
            generation.get("persistent_regiment_id"), "current persistent generation"
        )
        if persistent_id in actual_persistent or persistent_id not in expected:
            raise LifecycleContractError("current persistent generation is not source-bound")
        actual_persistent.add(persistent_id)
        rows = generation.get("current_rows")
        if not isinstance(rows, list) or not rows:
            raise LifecycleContractError("source current generation disappeared before action")
        row_currents: set[int] = set()
        row_armies: set[int] = set()
        for row_value in rows:
            row = _object(row_value, "current composition row")
            current_id = _integer(
                row.get("current_army_regiment_id"), "current regiment generation"
            )
            army_id = _integer(row.get("raised_carmy_id"), "current army generation")
            if current_id in actual_currents:
                raise LifecycleContractError("current regiment generation is duplicated")
            actual_currents.add(current_id)
            row_currents.add(current_id)
            row_armies.add(army_id)
            current_soldiers += _integer(
                row.get("current_soldiers"), "current soldiers", minimum=0
            )
        source_row = expected[persistent_id]
        if (
            row_currents != source_row["current_generation_ids"]
            or row_armies != {source_row["army_generation_id"]}
        ):
            raise LifecycleContractError("persistent/current/army source mapping drifted")
        actual_armies.update(row_armies)

    expected_persistent = set(expected)
    if (
        actual_persistent != expected_persistent
        or actual_currents != expected_currents
        or actual_armies != expected_armies
    ):
        raise LifecycleContractError("current source generation set is incomplete")
    if current_soldiers <= 0:
        raise LifecycleContractError("source-bound current soldiers must be positive")
    return {
        "persistent_generation_ids": sorted(actual_persistent),
        "current_generation_ids": sorted(actual_currents),
        "army_generation_ids": sorted(actual_armies),
        "current_soldiers": current_soldiers,
    }


def build_source_bound_ticket(
    normalized_source: dict[str, object],
    pre_sequence: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Join the six source executions to the same-process paused current read."""
    if pre_sequence.get("ok") is not True:
        raise LifecycleContractError("pre-termination dual query is not GREEN")
    before = postwar._structured_record(
        pre_sequence.get("before_snapshot"), "pre snapshot"
    )
    second = postwar._structured_record(
        pre_sequence.get("second_query"), "second terms query"
    )
    binding = retention_binding = postwar.adapter._snapshot_binding(
        before, "source-bound pre snapshot"
    )
    terms_value = _object(second.get("war_termination_terms"), "termination terms")
    generic = terms_value.get("generic_war_bound_current")
    source_set = _object(normalized_source.get("source_set"), "source_set")
    war_id = _integer(source_set.get("war_id"), "source WarID")
    active_war = postwar.adapter._war_row(binding, war_id)
    if not isinstance(active_war, dict):
        raise LifecycleContractError("source WarID is absent from the paused current frame")
    character_id = _integer(binding.get("character_id"), "current character", minimum=1)
    opponent_id = _integer(
        active_war.get("primary_opponent_character_id"),
        "primary opponent character",
        minimum=1,
    )
    try:
        normalized_current = normalize_raiktor_war_bound_regiment(
            generic,
            expected_war_id=war_id,
            expected_attacker_character_id=character_id,
            expected_defender_character_id=opponent_id,
            expected_snapshot_revision=_integer(binding["revision"], "revision"),
            expected_native_revision=_integer(
                binding["native_revision"], "native revision", minimum=1
            ),
            expected_date_raw=_integer(binding["date_raw"], "date raw"),
        )
        generations = retention._generation_vector(normalized_current)
    except (KeyError, TypeError, ValueError, retention.PreflightError) as error:
        raise LifecycleContractError(
            f"source-bound current observation was rejected: {error}"
        ) from error
    source_join = _source_binding(normalized_source, generations)
    observed_soldiers = _object(
        normalized_current.get("soldiers"), "current soldiers"
    ).get("observed_current_soldiers")
    if observed_soldiers != source_join["current_soldiers"]:
        raise LifecycleContractError("source-bound soldier aggregate drifted")
    truce = _object(terms_value.get("truce"), "termination truce")
    evaluated_days = _integer(truce.get("evaluated_days"), "evaluated days")
    if (
        truce.get("evaluated_days_observable") is not True
        or truce.get("actual_expiry_observable") is not False
        or truce.get("expiry_date_raw") is not None
    ):
        raise LifecycleContractError("pre-action truce boundary drifted")
    capture_pid = _integer(
        normalized_source.get("capture_pid"), "source capture PID", minimum=1
    )
    if binding.get("ck3_pid") != capture_pid:
        raise LifecycleContractError("source capture and current read use different CK3 PIDs")
    if normalized_source.get("exact_build_sha256") != EXPECTED_EXE_SHA256:
        raise LifecycleContractError("source capture exact-build identity drifted")
    if second.get("war_id") != war_id:
        raise LifecycleContractError("second query WarID differs from source capture")

    generation_sha256 = retention._sha256_json(generations)
    ticket_body = {
        "schema": "xar.ck3.g2_postwar_retention_ticket.v1",
        "exact_build_sha256": EXPECTED_EXE_SHA256,
        "source_report_sha256": _sha256_text(
            normalized_source.get("capture_sha256"), "capture SHA-256"
        ),
        "war_id": war_id,
        "character_id": character_id,
        "opponent_character_id": opponent_id,
        "source_snapshot_id": binding["snapshot_id"],
        "source_revision": binding["revision"],
        "source_native_revision": binding["native_revision"],
        "date_raw": binding["date_raw"],
        "source_connection_generation": binding["connection_generation"],
        "source_episode_run_id": binding["episode_run_id"],
        "source_ck3_pid": capture_pid,
        "pre_termination_soldiers": observed_soldiers,
        "evaluated_days": evaluated_days,
        "frozen_generation_sha256": generation_sha256,
        "frozen_generations": generations,
    }
    ticket = copy.deepcopy(ticket_body)
    ticket["retention_ticket_id"] = retention._sha256_json(ticket_body)
    ticket["source_attribution_ready"] = True
    ticket["source_set_sha256"] = normalized_source["source_set_sha256"]
    ticket["termination_action_bound"] = False
    ticket["actual_expiry_observable"] = False
    ticket["public_readiness_promoted"] = False
    ticket["gen034_closed"] = False
    ticket["pre_observation_backend_id"] = normalized_current.get("backend_id")
    return ticket, {
        "capture_pid": capture_pid,
        "connection_generation": retention_binding["connection_generation"],
        "episode_run_id": retention_binding["episode_run_id"],
        "war_id": war_id,
        "source_set_sha256": normalized_source["source_set_sha256"],
        "generation_join": source_join,
    }


def build_source_specific_loss_join(
    normalized_source: dict[str, object],
    ticket: dict[str, object],
    sequence: dict[str, object],
) -> dict[str, object]:
    """Promote only the private source-specific loss input after full join."""
    receipt = _object(sequence.get("postwar_receipt"), "postwar receipt")
    validation = retention.validate_postwar_receipt(receipt, ticket)
    session = _object(receipt.get("session_binding"), "receipt session")
    post = _object(receipt.get("post"), "receipt post")
    cleanup = _object(post.get("war_bound_cleanup"), "receipt cleanup")
    source_set = _object(normalized_source.get("source_set"), "source_set")
    expected_action = f"surrender-war-{ticket['war_id']}"
    checks = {
        "sequence_green": sequence.get("ok") is True,
        "ticket_green": validation.get("ok") is True,
        "same_source_pid": session.get("ck3_pid")
        == normalized_source.get("capture_pid")
        == ticket.get("source_ck3_pid"),
        "same_bridge_generation": session.get("connection_generation")
        == ticket.get("source_connection_generation"),
        "same_episode": session.get("episode_run_id")
        == ticket.get("source_episode_run_id"),
        "same_war": session.get("war_id") == source_set.get("war_id"),
        "same_source_set": ticket.get("source_set_sha256")
        == normalized_source.get("source_set_sha256"),
        "one_action": sequence.get("mutation_commands") == [expected_action]
        and receipt.get("mutation_commands") == [expected_action],
        "destroyed_source_set": cleanup.get("status") == "destroyed"
        and cleanup.get("post_termination_soldiers") == 0
        and cleanup.get("proven_boundary_soldiers_lost")
        == ticket.get("pre_termination_soldiers"),
        "persisted_expiry": _object(
            post.get("truce_expiry"), "receipt expiry"
        ).get("source")
        == retention.EXPECTED_EXPIRY_SOURCE,
    }
    if not all(checks.values()):
        raise LifecycleContractError(f"source-specific lifecycle join failed: {checks}")
    creation = _integer(
        source_set.get("measured_initial_soldiers"), "creation soldiers"
    )
    current = _integer(
        ticket.get("pre_termination_soldiers"), "pre-termination soldiers"
    )
    return {
        "schema": JOIN_SCHEMA,
        "status": "qualified_private_source_specific_loss_input",
        "source_contract": SOURCE_CONTRACT,
        "source_set_sha256": normalized_source["source_set_sha256"],
        "retention_ticket_id": ticket["retention_ticket_id"],
        "identity": {
            "ck3_pid": ticket["source_ck3_pid"],
            "connection_generation": ticket["source_connection_generation"],
            "episode_run_id": ticket["source_episode_run_id"],
            "war_id": ticket["war_id"],
        },
        "soldiers": {
            "measured_at_creation": creation,
            "measured_before_termination": current,
            "measured_creation_minus_current": creation - current,
            "post_termination": 0,
            "proven_surrender_boundary_loss": current,
        },
        "checks": checks,
        "readiness": {
            "private_live_evidence_classified": True,
            "action_bound_current_ready": True,
            "postwar_cleanup_ready": True,
            "source_specific_loss_ready": True,
            "comparison_input_ready": True,
            "three_way_comparison_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
        "remaining_providers": [
            "campaign-dominance-certificate",
            "owner-authored-budget-profile",
            "same-frame-white-peace-comparison-certificate",
        ],
    }


async def run_same_lifecycle_sequence(
    driver: Any,
    *,
    source_capture: dict[str, object],
    capture_sha256: str,
    expected_character_id: int,
    expected_date_raw: int,
    postwar_timeout: float,
) -> dict[str, object]:
    """Run the source/current/action/post stages on one caller-owned driver."""
    normalized_source = normalize_raiktor_source_specific_capture(
        source_capture, capture_sha256=capture_sha256
    )
    war_id = _integer(
        _object(normalized_source["source_set"], "source_set")["war_id"],
        "source WarID",
    )
    pre_sequence = await terms._run_mcp_sequence(
        driver,
        war_id=war_id,
        expected_character_id=expected_character_id,
        expected_date_raw=expected_date_raw,
    )
    ticket, handoff = build_source_bound_ticket(normalized_source, pre_sequence)
    sequence = await postwar._continue_private_sequence(
        driver,
        war_id=war_id,
        ticket=ticket,
        postwar_timeout=postwar_timeout,
        pre_sequence=pre_sequence,
    )
    joined = build_source_specific_loss_join(normalized_source, ticket, sequence)
    joined_checks = _object(joined.get("checks"), "source-specific join checks")
    return {
        "schema": "xar.ck3.g2_source_specific_war_loss_lifecycle_run.v1",
        "status": "green" if all(joined_checks.values()) else "red",
        "source_normalization": normalized_source,
        "handoff": handoff,
        "retention_ticket": ticket,
        "sequence": sequence,
        "source_specific_loss_join": joined,
        "mutation_commands": sequence.get("mutation_commands"),
        "ok": True,
    }


def run_no_launch_preflight(
    manifest_path: Path,
    output_path: Path,
    *,
    repo_root: Path = REPOSITORY_ROOT,
    process_inventory: Callable[[], object] = postwar._process_inventory,
) -> dict[str, object]:
    if output_path.exists():
        raise LifecycleContractError(f"output path already exists: {output_path}")
    manifest = _object(
        json.loads(manifest_path.read_text(encoding="utf-8-sig")), "manifest"
    )
    boundaries = _object(manifest.get("boundaries"), "manifest boundaries")
    if (
        manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("status") != "static-ready-no-launch"
        or manifest.get("default_off") is not True
        or manifest.get("live_authorized") is not False
        or any(
            boundaries.get(name) is not False
            for name in (
                "live_executed",
                "public_readiness_promoted",
                "action_readiness_promoted",
                "decision_ready",
                "automatic_surrender_ready",
                "gen034_closed",
            )
        )
    ):
        raise LifecycleContractError("manifest readiness boundary drifted")
    paths = _object(manifest.get("paths"), "manifest paths")
    hashes = _object(manifest.get("sha256"), "manifest hashes")
    required = {
        "runner",
        "source_capture_runner",
        "source_provider",
        "source_contract",
        "postwar_runner",
        "postwar_adapter",
        "terms_runner",
        "capture_executable",
        "bridge_dll",
        "bridge_injector",
        "game_executable",
        "bookmark_events",
    }
    checked: dict[str, dict[str, object]] = {}
    for name in sorted(required):
        if name not in paths or name not in hashes:
            raise LifecycleContractError(f"manifest dependency is missing: {name}")
        path = _resolve(paths[name], repo_root=repo_root)
        expected = _sha256_text(hashes[name], f"{name} SHA-256")
        if not path.is_file():
            raise LifecycleContractError(f"manifest dependency is absent: {path}")
        actual = _sha256_file(path)
        if actual != expected:
            raise LifecycleContractError(
                f"manifest dependency drifted: {name} {actual} != {expected}"
            )
        checked[name] = {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": actual,
        }
    if checked["game_executable"]["sha256"] != EXPECTED_EXE_SHA256:
        raise LifecycleContractError("game executable is not exact CK3 1.19.0.6")
    source_contract = _object(
        json.loads(
            Path(str(checked["source_contract"]["path"])).read_text(
                encoding="utf-8-sig"
            )
        ),
        "source contract",
    )
    if (
        source_contract.get("contract") != SOURCE_CONTRACT
        or source_contract.get("default_off") is not True
        or source_contract.get("live_authorized") is not False
    ):
        raise LifecycleContractError("source provider contract drifted")
    before = copy.deepcopy(process_inventory())
    after = copy.deepcopy(process_inventory())
    if before != after:
        raise LifecycleContractError("process inventory changed during no-launch preflight")
    report = {
        "schema": PREFLIGHT_SCHEMA,
        "status": EXPECTED_STATUS,
        "manifest_sha256": _sha256_file(manifest_path),
        "dependencies": checked,
        "process_inventory_before": before,
        "process_inventory_after": after,
        "contract": {
            "same_ck3_pid_from_capture_through_receipt": True,
            "same_bridge_connection_generation_for_current_action_post": True,
            "same_episode_for_current_action_post": True,
            "six_source_execution_generation_join_required": True,
            "one_surrender_mutation_required": True,
            "destroyed_exact_generation_cleanup_required": True,
            "two_equal_persisted_expiry_reads_required": True,
        },
        "boundaries": {
            "ck3_started_or_attached": False,
            "fixture_or_schema_claimed_as_live": False,
            "source_specific_loss_ready": False,
            "comparison_input_ready": False,
            "three_way_comparison_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, output_path)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = run_no_launch_preflight(args.manifest, args.output)
    except (OSError, UnicodeError, json.JSONDecodeError, LifecycleContractError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(
        f"{report['status']} live=false source_specific_loss_ready=false "
        "comparison_input_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
