#!/usr/bin/env python3
"""Accept generic war-bound current soldiers on one paused public frame.

``--verify-only`` hashes the frozen checkpoint, driver state, exact CK3 build,
fresh bridge binaries, production sources, manifest and this runner.  It never
prepares a profile or starts CK3.  Live mode is deliberately a separate branch
and performs exactly two read-only war-termination terms queries.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
import time
from typing import Any


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = RESEARCH_ROOT.parents[1] / "src"
REPO_ROOT = RESEARCH_ROOT.parents[2]
for path in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run_raiktor_surrender_session_binding_live_acceptance as session_live  # noqa: E402
import run_war_termination_terms_live_acceptance as terms_live  # noqa: E402
from xar_autoplayer.bridge import (  # noqa: E402
    raiktor_surrender_session_binding_contract as session_contract,
)
from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (  # noqa: E402
    normalize_raiktor_war_bound_regiment,
)
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    query_war_termination_terms_step,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.runtime import utc_now  # noqa: E402


REPORT_KIND = "ck3_raiktor_generic_war_bound_rbx_guarded_live_acceptance"
DEFAULT_MANIFEST = (
    RESEARCH_ROOT
    / "fixtures"
    / "raiktor_generic_war_bound_rbx_guarded_current_live_manifest.json"
)
# Filled only after the manifest has reached its final byte representation.
EXPECTED_MANIFEST_SHA256 = (
    "E3DA9CB61322730F00E9C772779D94F5060032723FEE4E0156756EA01D3BA0A5"
)


def _parser() -> argparse.ArgumentParser:
    parser = terms_live._parser()
    parser.description = __doc__
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST,
        help="frozen acceptance manifest",
    )
    parser.add_argument(
        "--verify-only", action="store_true",
        help="verify all frozen inputs and exit before the launch boundary",
    )
    parser.add_argument(
        "--verify-report", type=Path, required=True,
        help="fresh no-launch verification report outside --attempt-dir",
    )
    return parser


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _record_content(value: object) -> dict[str, object]:
    return _mapping(_mapping(value).get("structured_content"))


def _load_manifest(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"generic war-bound manifest unavailable: {error}") from error
    if not isinstance(value, dict):
        raise AgentError("generic war-bound manifest root is malformed")
    return value


def _active_war(snapshot: dict[str, object], war_id: int) -> dict[str, object]:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return {}
    matches = [
        row for row in wars
        if isinstance(row, dict) and row.get("war_id") == war_id
    ]
    return matches[0] if len(matches) == 1 else {}


def _generic_frame_checks(
    *,
    before: dict[str, object],
    query: dict[str, object],
    cached_snapshot: dict[str, object],
    war_id: int,
    expected_character_id: int,
) -> dict[str, object]:
    terms = _mapping(query.get("war_termination_terms"))
    child = terms.get("generic_war_bound_current")
    casus_belli = _mapping(terms.get("casus_belli"))
    active_war = _active_war(before, war_id)
    defender_id = active_war.get("primary_opponent_character_id")
    wrapper = _mapping(query.get("raiktor_surrender_aggregate_session"))
    aggregate = _mapping(wrapper.get("aggregate"))
    domains = _mapping(aggregate.get("domains"))
    readiness = _mapping(aggregate.get("readiness"))
    cached = session_live._cache_row(cached_snapshot, war_id)
    cached_terms = _mapping(cached)

    child_error: str | None = None
    normalized_child: dict[str, object] | None = None
    try:
        normalized_child = normalize_raiktor_war_bound_regiment(
            child,
            expected_war_id=war_id,
            expected_attacker_character_id=expected_character_id,
            expected_defender_character_id=defender_id,
            expected_snapshot_revision=before.get("revision"),
            expected_native_revision=before.get("native_revision"),
            expected_date_raw=before.get("date_raw"),
        )
    except (TypeError, ValueError) as error:
        child_error = f"{type(error).__name__}: {error}"

    binding_error: str | None = None
    normalized_wrapper: dict[str, object] | None = None
    diagnostics = _mapping(before.get("diagnostics"))
    try:
        normalized_wrapper = (
            session_contract.normalize_raiktor_surrender_aggregate_session_binding(
                wrapper,
                expected_snapshot_id=str(before.get("snapshot_id", "")),
                expected_snapshot_revision=before.get("revision"),
                expected_native_revision=before.get("native_revision"),
                expected_date_raw=before.get("date_raw"),
                expected_connection_generation=diagnostics.get(
                    "connection_generation"
                ),
                expected_episode_run_id=before.get("episode_run_id"),
                expected_episode_character_id=expected_character_id,
                expected_process_id=diagnostics.get("bridge_pid"),
                expected_war_id=war_id,
            )
        )
    except (TypeError, ValueError) as error:
        binding_error = f"{type(error).__name__}: {error}"

    generic_domain = _mapping(domains.get("generic_war_bound_current"))
    generic_payload = generic_domain.get("payload")
    checks = {
        "child_strictly_normalized": normalized_child is not None,
        "child_cb_identity": _mapping(_mapping(child).get("active_frame")).get(
            "active_casus_belli_database_index"
        ) == casus_belli.get("database_index"),
        "aggregate_session_strictly_normalized": normalized_wrapper is not None,
        "aggregate_incomplete_only_truce": aggregate.get("status") == "incomplete"
        and aggregate.get("missing_domains") == ["truce"],
        "aggregate_generic_payload_equals_child": generic_domain.get("available")
        is True and generic_payload == normalized_child,
        "generic_current_only_ready": readiness.get(
            "generic_war_bound_current_ready"
        ) is True
        and readiness.get("source_specific_war_bound_ready") is False
        and readiness.get("pre_soldiers_ready") is False
        and readiness.get("proven_soldier_loss_ready") is False,
        "action_and_automatic_closed": readiness.get("action_terms_ready") is False
        and readiness.get("automatic_surrender_ready") is False,
        "cache_row_unique": bool(cached),
        "cache_child_exact": cached_terms.get("generic_war_bound_current")
        == normalized_child,
        "cache_aggregate_session_exact": cached.get(
            "raiktor_surrender_aggregate_session"
        ) == wrapper,
        "cache_query_sequence_exact": cached.get("query_sequence")
        == query.get("query_sequence"),
        "cache_receipt_exact": all(
            cached.get(key) == query.get(key)
            for key in (
                "queried_snapshot_id",
                "queried_revision",
                "queried_native_revision",
                "queried_connection_generation",
                "episode_run_id",
            )
        ),
    }
    return {
        "normalized_child": normalized_child,
        "normalized_wrapper": normalized_wrapper,
        "child_error": child_error,
        "binding_error": binding_error,
        "checks": checks,
        "ok": all(checks.values()),
    }


async def _run_generic_mcp_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    sequence = await terms_live._run_mcp_sequence(
        driver,
        war_id=war_id,
        expected_character_id=expected_character_id,
        expected_date_raw=expected_date_raw,
    )
    before = _record_content(sequence.get("before_snapshot"))
    first = _record_content(sequence.get("first_query"))
    between = _record_content(sequence.get("between_snapshot"))
    second = _record_content(sequence.get("second_query"))
    after = _record_content(sequence.get("after_snapshot"))
    first_frame = _generic_frame_checks(
        before=before,
        query=first,
        cached_snapshot=between,
        war_id=war_id,
        expected_character_id=expected_character_id,
    )
    second_frame = _generic_frame_checks(
        before=before,
        query=second,
        cached_snapshot=after,
        war_id=war_id,
        expected_character_id=expected_character_id,
    )
    exact_commands = [
        query_war_termination_terms_step(war_id),
        query_war_termination_terms_step(war_id),
    ]
    base_checks = _mapping(sequence.get("checks"))
    required_base_checks = (
        "official_tools_listed",
        "mcp_results_not_errors",
        "initial_paused",
        "expected_character",
        "expected_date",
        "between_same_paused_binding",
        "after_same_paused_binding",
        "query_sequence_successor",
        "normalized_payloads_equal",
        "binding_matches_revision",
    )
    checks = {
        # The legacy four-domain/truce gates are deliberately independent:
        # this acceptance proves only the new generic-current observation.
        "base_paused_query_identity": all(
            base_checks.get(name) is True for name in required_base_checks
        ),
        "first_child_aggregate_session_cache": first_frame["ok"] is True,
        "second_child_aggregate_session_cache": second_frame["ok"] is True,
        "strict_child_repeat_equal": first_frame.get("normalized_child")
        == second_frame.get("normalized_child"),
        "strict_aggregate_repeat_equal": _mapping(
            first_frame.get("normalized_wrapper")
        ).get("aggregate")
        == _mapping(second_frame.get("normalized_wrapper")).get("aggregate"),
        "strict_session_repeat_equal": _mapping(
            first_frame.get("normalized_wrapper")
        ).get("binding")
        == _mapping(second_frame.get("normalized_wrapper")).get("binding"),
        "exactly_two_terms_queries": sequence.get("allowed_gameplay_commands")
        == exact_commands,
        "no_mutation_commands": sequence.get("mutation_commands") == [],
    }
    return {
        **sequence,
        "generic_war_bound_current": {
            "first": first_frame,
            "second": second_frame,
            "legacy_base_sequence_ok": sequence.get("ok") is True,
            "checks": checks,
            "ok": all(checks.values()),
        },
        "ok": all(checks.values()),
    }


def _verify_only(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    report_path = args.verify_report.expanduser().resolve()
    attempt_path = args.attempt_dir.expanduser().resolve()
    manifest_path = args.manifest.expanduser().resolve()
    if report_path.exists():
        raise AgentError(f"verify report already exists: {report_path}")
    if report_path == attempt_path or report_path.is_relative_to(attempt_path):
        raise AgentError("verify report must be outside the future attempt")

    manifest = _load_manifest(manifest_path)
    frozen = _mapping(manifest.get("frozen_inputs"))
    expected = _mapping(manifest.get("expected_identity"))
    source_hashes = _mapping(manifest.get("production_source_sha256"))
    query_contract = _mapping(manifest.get("query_contract"))
    readiness = _mapping(manifest.get("readiness_boundary"))
    runner_path = Path(__file__).resolve()
    game_exe = args.game_dir.expanduser().resolve() / "binaries" / "ck3.exe"
    source_checkpoint = args.source_checkpoint.expanduser().resolve()
    source_driver = args.source_driver_state.expanduser().resolve()
    bridge_dll = args.bridge_dll.expanduser().resolve()
    bridge_injector = args.bridge_injector.expanduser().resolve()
    identities: dict[str, object] = {}
    anchor: dict[str, object] = {}
    error: str | None = None
    try:
        identities = {
            "manifest_sha256": terms_live._sha256_file(manifest_path),
            "runner_sha256": terms_live._sha256_file(runner_path),
            "checkpoint_sha256": terms_live._sha256_file(source_checkpoint),
            "driver_state_sha256": terms_live._sha256_file(source_driver),
            "game_executable_sha256": terms_live._sha256_file(game_exe),
            "bridge_dll_sha256": terms_live._sha256_file(bridge_dll),
            "bridge_injector_sha256": terms_live._sha256_file(bridge_injector),
            "production_source_sha256": {
                relative: terms_live._sha256_file(REPO_ROOT / relative)
                for relative in source_hashes
            },
        }
        anchor = terms_live._driver_anchor(source_driver)
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"

    checkpoint_anchor = _mapping(anchor.get("last_checkpoint"))
    checks = {
        "attempt_dir_absent": not attempt_path.exists(),
        "manifest_hash": identities.get("manifest_sha256")
        == EXPECTED_MANIFEST_SHA256,
        "manifest_source_freeze": manifest.get("source_commit")
        == "3c378569d65794bd1ec9dceda25f0cd6a364f3ca",
        "checkpoint_hash": identities.get("checkpoint_sha256")
        == frozen.get("checkpoint_sha256")
        == terms_live._expected_sha256(
            args.expected_checkpoint_sha256, "expected checkpoint SHA-256"
        ),
        "driver_state_hash": identities.get("driver_state_sha256")
        == frozen.get("driver_state_sha256")
        == terms_live._expected_sha256(
            args.expected_driver_state_sha256, "expected driver-state SHA-256"
        ),
        "exact_game_executable": identities.get("game_executable_sha256")
        == frozen.get("game_executable_sha256")
        == terms_live.EXPECTED_EXECUTABLE_SHA256,
        "fresh_bridge_dll": identities.get("bridge_dll_sha256")
        == frozen.get("bridge_dll_sha256"),
        "fresh_bridge_injector": identities.get("bridge_injector_sha256")
        == frozen.get("bridge_injector_sha256"),
        "production_sources_exact": identities.get("production_source_sha256")
        == source_hashes,
        "driver_character": anchor.get("episode_character_id")
        == expected.get("character_id") == args.expected_character_id,
        "checkpoint_anchor_hash": str(
            checkpoint_anchor.get("sha256", "")
        ).upper() == frozen.get("checkpoint_sha256"),
        "checkpoint_anchor_date": checkpoint_anchor.get("date_raw")
        == expected.get("date_raw") == args.expected_date_raw,
        "war_identity": expected.get("war_id") == args.war_id,
        "query_count_exactly_two": query_contract.get("terms_query_count") == 2
        and query_contract.get("allowed_gameplay_commands")
        == [
            query_war_termination_terms_step(args.war_id),
            query_war_termination_terms_step(args.war_id),
        ],
        "strict_identity_layers": query_contract.get("strict_equal_layers")
        == ["child", "aggregate", "session", "cache"],
        "read_only_boundary": query_contract.get("mutation_commands") == [],
        "honest_readiness_boundary": readiness
        == {
            "generic_war_bound_current_ready": True,
            "source_specific_war_bound_ready": False,
            "pre_soldiers_ready": False,
            "proven_soldier_loss_ready": False,
            "action_terms_ready": False,
            "automatic_surrender_ready": False,
        },
        "verify_did_not_prepare_or_launch": True,
    }
    ok = error is None and all(checks.values())
    payload = {
        "format_version": 1,
        "kind": "ck3_raiktor_generic_war_bound_current_verify_only",
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "status": "ready-to-run" if ok else "red",
        "ok": ok,
        "ck3_started": False,
        "profile_prepared": False,
        "attempt_dir": str(attempt_path),
        "report_path": str(report_path),
        "manifest_path": str(manifest_path),
        "requested_identity": {
            "war_id": args.war_id,
            "character_id": args.expected_character_id,
            "date_raw": args.expected_date_raw,
        },
        "identities": identities,
        "driver_anchor": anchor,
        "query_contract": copy.deepcopy(query_contract),
        "readiness_boundary": copy.deepcopy(readiness),
        "checks": checks,
        "error": error,
    }
    terms_live._write_json_atomic(report_path, payload)
    return payload, 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        verified, verify_exit = _verify_only(args)
        if args.verify_only or verify_exit != 0:
            payload = verified
            exit_code = verify_exit
        else:
            payload, exit_code = terms_live._run(
                args,
                sequence_runner=_run_generic_mcp_sequence,
                report_kind=REPORT_KIND,
            )
            payload["verify_only"] = verified
            terms_live._write_json_atomic(Path(str(payload["report_path"])), payload)
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps({
        "ok": payload.get("ok"),
        "status": payload.get("status"),
        "report_path": payload.get("report_path"),
        "ck3_started": payload.get("ck3_started"),
        "error": payload.get("error"),
    }, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
