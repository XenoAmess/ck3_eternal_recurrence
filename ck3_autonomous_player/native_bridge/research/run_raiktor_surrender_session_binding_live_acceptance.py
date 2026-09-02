#!/usr/bin/env python3
"""Accept the public Raiktor aggregate session wrapper on one paused frame.

The default live mode reuses the frozen read-only terms harness and adds strict
connection/episode/PID/revision/cache assertions.  ``--preflight-only`` checks
the immutable inputs and exact build identity without preparing a profile or
starting CK3, leaving the same command ready for the exclusive launch slot.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
import time
from typing import Any


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = RESEARCH_ROOT.parents[1] / "src"
for path in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run_war_termination_terms_live_acceptance as terms_live  # noqa: E402
from xar_autoplayer.bridge import (  # noqa: E402
    raiktor_surrender_session_binding_contract as session_contract,
)
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    query_war_termination_terms_step,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.runtime import utc_now  # noqa: E402


REPORT_KIND = "ck3_raiktor_surrender_session_binding_live_acceptance"
SESSION_BACKEND_ID = session_contract.BACKEND_ID
SESSION_CONTRACT = (
    RESEARCH_ROOT
    / "fixtures"
    / "raiktor_surrender_session_binding_v1_contract.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = terms_live._parser()
    parser.description = __doc__
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate immutable inputs and exit without preparing or launching CK3",
    )
    parser.add_argument(
        "--preflight-report",
        type=Path,
        help="no-launch report path (defaults beside --attempt-dir)",
    )
    return parser


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _record_content(value: object) -> dict[str, object]:
    return _mapping(_mapping(value).get("structured_content"))


def _cache_row(snapshot: dict[str, object], war_id: int) -> dict[str, object]:
    rows = snapshot.get("war_termination_terms")
    if not isinstance(rows, list):
        return {}
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("war_id") == war_id
    ]
    return matches[0] if len(matches) == 1 else {}


def _session_binding_checks(
    *,
    before: dict[str, object],
    query: dict[str, object],
    cached_snapshot: dict[str, object],
    war_id: int,
    expected_character_id: int,
) -> dict[str, object]:
    diagnostics = _mapping(before.get("diagnostics"))
    connection_generation = diagnostics.get("connection_generation")
    process_id = diagnostics.get("bridge_pid")
    episode_run_id = before.get("episode_run_id")
    wrapper = _mapping(query.get("raiktor_surrender_aggregate_session"))
    aggregate = _mapping(wrapper.get("aggregate"))
    domains = _mapping(aggregate.get("domains"))
    readiness = _mapping(aggregate.get("readiness"))
    cached = _cache_row(cached_snapshot, war_id)
    normalization_error: str | None = None
    normalized: dict[str, object] | None = None
    try:
        normalize = (
            session_contract.normalize_raiktor_surrender_aggregate_session_binding
        )
        normalized = normalize(
            wrapper,
            expected_snapshot_id=str(before.get("snapshot_id", "")),
            expected_snapshot_revision=before.get("revision"),
            expected_native_revision=before.get("native_revision"),
            expected_date_raw=before.get("date_raw"),
            expected_connection_generation=connection_generation,
            expected_episode_run_id=episode_run_id,
            expected_episode_character_id=expected_character_id,
            expected_process_id=process_id,
            expected_war_id=war_id,
        )
    except (TypeError, ValueError) as error:
        normalization_error = f"{type(error).__name__}: {error}"

    checks = {
        "wrapper_strictly_normalized": normalized is not None,
        "query_receipt_connection_generation": query.get(
            "queried_connection_generation"
        )
        == connection_generation,
        "query_receipt_episode_run": query.get("episode_run_id")
        == episode_run_id,
        "query_receipt_public_revision": query.get("queried_revision")
        == before.get("revision"),
        "query_receipt_native_revision": query.get("queried_native_revision")
        == before.get("native_revision"),
        "query_receipt_snapshot_id": query.get("queried_snapshot_id")
        == before.get("snapshot_id"),
        "cache_row_present": bool(cached),
        "cache_wrapper_equal": cached.get(
            "raiktor_surrender_aggregate_session"
        )
        == wrapper,
        "cache_query_sequence_equal": cached.get("query_sequence")
        == query.get("query_sequence"),
        "cache_connection_generation_equal": cached.get(
            "queried_connection_generation"
        )
        == connection_generation,
        "cache_episode_run_equal": cached.get("episode_run_id")
        == episode_run_id,
        "cache_public_revision_equal": cached.get("queried_revision")
        == before.get("revision"),
        "cache_native_revision_equal": cached.get("queried_native_revision")
        == before.get("native_revision"),
        "aggregate_incomplete": aggregate.get("status") == "incomplete",
        "missing_domains_exact": aggregate.get("missing_domains")
        == ["truce", "generic_war_bound_current"],
        "truce_typed_unavailable": domains.get("truce")
        == {"available": False},
        "war_bound_typed_unavailable": domains.get(
            "generic_war_bound_current"
        )
        == {"available": False},
        "four_observed_domains_available": all(
            _mapping(domains.get(name)).get("available") is True
            for name in (
                "gold",
                "prestige",
                "prisoner_release",
                "favor_hook",
            )
        ),
        "action_terms_closed": readiness.get("action_terms_ready") is False,
        "automatic_surrender_closed": readiness.get(
            "automatic_surrender_ready"
        )
        is False,
    }
    return {
        "backend_id": wrapper.get("backend_id"),
        "binding": copy.deepcopy(wrapper.get("binding")),
        "normalization_error": normalization_error,
        "checks": checks,
        "ok": all(checks.values()),
    }


async def _run_session_binding_mcp_sequence(
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
    first_binding = _session_binding_checks(
        before=before,
        query=first,
        cached_snapshot=between,
        war_id=war_id,
        expected_character_id=expected_character_id,
    )
    second_binding = _session_binding_checks(
        before=before,
        query=second,
        cached_snapshot=after,
        war_id=war_id,
        expected_character_id=expected_character_id,
    )
    checks = {
        "first_session_binding": first_binding["ok"] is True,
        "second_session_binding": second_binding["ok"] is True,
        "session_binding_repeat_equal": first_binding.get("binding")
        == second_binding.get("binding"),
        "read_only_command_boundary": sequence.get("allowed_gameplay_commands")
        == [
            query_war_termination_terms_step(war_id),
            query_war_termination_terms_step(war_id),
        ]
        and sequence.get("mutation_commands") == [],
    }
    return {
        **sequence,
        "session_binding": {
            "first": first_binding,
            "second": second_binding,
            "legacy_base_sequence_ok": sequence.get("ok") is True,
            "checks": checks,
            "ok": all(checks.values()),
        },
        "ok": all(checks.values()),
    }


def _load_session_contract() -> dict[str, object]:
    try:
        value = json.loads(SESSION_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"session-binding contract is unavailable: {error}") from error
    if not isinstance(value, dict):
        raise AgentError("session-binding contract root is malformed")
    return value


def _preflight_report_path(args: argparse.Namespace) -> Path:
    requested = getattr(args, "preflight_report", None)
    if isinstance(requested, Path):
        return requested.expanduser().resolve()
    attempt = args.attempt_dir.expanduser().resolve()
    base = attempt.with_name(attempt.name + "-no-launch-preflight.json")
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = base.with_name(f"{base.stem}-{suffix}{base.suffix}")
        suffix += 1
    return candidate


def _no_launch_preflight(
    args: argparse.Namespace,
) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    report_path = _preflight_report_path(args)
    attempt_path = args.attempt_dir.expanduser().resolve()
    if report_path == attempt_path or report_path.is_relative_to(attempt_path):
        raise AgentError("preflight report must be outside the future attempt")
    if report_path.exists():
        raise AgentError(f"preflight report already exists: {report_path}")
    expected_checkpoint = terms_live._expected_sha256(
        args.expected_checkpoint_sha256, "expected checkpoint SHA-256"
    )
    expected_driver = terms_live._expected_sha256(
        args.expected_driver_state_sha256, "expected driver-state SHA-256"
    )
    source_checkpoint = args.source_checkpoint.expanduser().resolve()
    source_driver = args.source_driver_state.expanduser().resolve()
    game_exe = args.game_dir.expanduser().resolve() / "binaries" / "ck3.exe"
    bridge_dll = args.bridge_dll.expanduser().resolve()
    bridge_injector = args.bridge_injector.expanduser().resolve()
    error: str | None = None
    anchor: dict[str, object] = {}
    contract: dict[str, object] = {}
    identities: dict[str, object] = {}
    try:
        identities = {
            "checkpoint_sha256": terms_live._sha256_file(source_checkpoint),
            "driver_state_sha256": terms_live._sha256_file(source_driver),
            "game_executable_sha256": terms_live._sha256_file(game_exe),
            "bridge_dll_sha256": terms_live._sha256_file(bridge_dll),
            "bridge_injector_sha256": terms_live._sha256_file(bridge_injector),
        }
        anchor = terms_live._driver_anchor(source_driver)
        contract = _load_session_contract()
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"

    checkpoint_anchor = _mapping(anchor.get("last_checkpoint"))
    hard_boundaries = _mapping(contract.get("hard_boundaries"))
    readiness = _mapping(contract.get("readiness"))
    run_id = anchor.get("episode_run_id")
    checks = {
        "attempt_dir_unused": not attempt_path.exists(),
        "checkpoint_hash": identities.get("checkpoint_sha256")
        == expected_checkpoint,
        "driver_state_hash": identities.get("driver_state_sha256")
        == expected_driver,
        "exact_game_executable": identities.get("game_executable_sha256")
        == terms_live.EXPECTED_EXECUTABLE_SHA256,
        "bridge_dll_present": bool(
            re.fullmatch(
                r"[0-9A-F]{64}",
                str(identities.get("bridge_dll_sha256", "")),
            )
        ),
        "bridge_injector_present": bool(
            re.fullmatch(
                r"[0-9A-F]{64}",
                str(identities.get("bridge_injector_sha256", "")),
            )
        ),
        "driver_character": anchor.get("episode_character_id")
        == args.expected_character_id,
        "driver_episode_run": isinstance(run_id, str) and bool(run_id.strip()),
        "driver_pipe": isinstance(anchor.get("pipe_name"), str)
        and bool(str(anchor.get("pipe_name")).strip()),
        "checkpoint_anchor_hash": str(
            checkpoint_anchor.get("sha256", "")
        ).upper()
        == expected_checkpoint,
        "checkpoint_anchor_date": checkpoint_anchor.get("date_raw")
        == args.expected_date_raw,
        "war_id_positive": isinstance(args.war_id, int)
        and not isinstance(args.war_id, bool)
        and args.war_id > 0,
        "session_contract_backend": contract.get("backend_id")
        == SESSION_BACKEND_ID,
        "public_wrapper_frozen": hard_boundaries.get(
            "public_terms_query_wrapper"
        )
        == "raiktor_surrender_aggregate_session",
        "public_query_wiring_ready": readiness.get("public_query_wiring")
        is True,
        "cached_snapshot_projection_ready": readiness.get(
            "cached_snapshot_projection"
        )
        is True,
        "automatic_surrender_closed": readiness.get(
            "automatic_surrender_ready"
        )
        is False,
        "preflight_did_not_launch_ck3": True,
    }
    ok = error is None and all(checks.values())
    payload = {
        "format_version": 1,
        "kind": "ck3_raiktor_surrender_session_binding_no_launch_preflight",
        "started_at": utc_now(),
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "status": "ready-to-run" if ok else "red",
        "ok": ok,
        "ck3_started": False,
        "profile_prepared": False,
        "attempt_dir": str(args.attempt_dir.expanduser().resolve()),
        "report_path": str(report_path),
        "requested_identity": {
            "war_id": args.war_id,
            "character_id": args.expected_character_id,
            "date_raw": args.expected_date_raw,
        },
        "identities": identities,
        "driver_anchor": anchor,
        "session_contract": {
            "path": str(SESSION_CONTRACT),
            "backend_id": contract.get("backend_id"),
            "readiness": copy.deepcopy(readiness),
        },
        "checks": checks,
        "error": error,
    }
    terms_live._write_json_atomic(report_path, payload)
    return payload, 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        preflight, preflight_exit = _no_launch_preflight(args)
        if args.preflight_only or preflight_exit != 0:
            payload = preflight
            exit_code = preflight_exit
        else:
            payload, exit_code = terms_live._run(
                args,
                sequence_runner=_run_session_binding_mcp_sequence,
                report_kind=REPORT_KIND,
            )
            payload["no_launch_preflight"] = preflight
            terms_live._write_json_atomic(
                Path(str(payload["report_path"])), payload
            )
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "status": payload.get("status"),
                "report_path": payload.get("report_path"),
                "ck3_started": payload.get("ck3_started"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
