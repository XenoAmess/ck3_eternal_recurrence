#!/usr/bin/env python3
"""Run one private action-bound G2 cleanup/expiry short path.

This runner restores the frozen in-war checkpoint directly; it does not replay
the lobby or use OCR.  The only mutation is one explicitly authorized native
``surrender-war-N`` submission.  Cleanup and persisted expiry remain private,
default-OFF capture inputs and do not advertise public decision readiness.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


RESEARCH_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = RESEARCH_ROOT.parents[2]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
for candidate in (RESEARCH_ROOT, PACKAGE_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import prepare_g2_postwar_retention_expiry_capture as retention  # noqa: E402
import run_g2_postwar_cleanup_expiry_receipt as adapter  # noqa: E402
import run_war_termination_terms_live_acceptance as base  # noqa: E402
from xar_autoplayer.bridge.raiktor_actual_truce_expiry_contract import (  # noqa: E402
    QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
)
from xar_autoplayer.bridge.raiktor_war_bound_loss_cleanup_contract import (  # noqa: E402
    QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
)
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
)
from xar_autoplayer.errors import AgentError  # noqa: E402


REPORT_KIND = "ck3_g2_postwar_cleanup_expiry_private_live_acceptance"
SURRENDER_CAPABILITY = "game.command.surrender-war-N"


def _parser() -> argparse.ArgumentParser:
    parser = base._parser()
    parser.description = __doc__
    parser.add_argument("--retention-manifest", type=Path, required=True)
    parser.add_argument(
        "--expected-retention-manifest-sha256", required=True
    )
    parser.add_argument("--expected-retention-ticket-id", required=True)
    parser.add_argument("--expected-bridge-dll-sha256", required=True)
    parser.add_argument("--expected-bridge-injector-sha256", required=True)
    parser.add_argument("--postwar-timeout", type=float, default=45.0)
    parser.add_argument("--authorize-private-live", action="store_true")
    return parser


def _process_inventory() -> dict[str, object]:
    completed = subprocess.run(
        ["tasklist.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise AgentError("could not inventory CK3/injector processes")
    targets = {"ck3.exe", "xar_ck3_bridge_injector.exe"}
    counts = {name: 0 for name in sorted(targets)}
    for row in csv.reader(io.StringIO(completed.stdout)):
        if row and row[0].strip().lower() in targets:
            counts[row[0].strip().lower()] += 1
    return {"counts": counts, "all_zero": all(count == 0 for count in counts.values())}


def _structured_record(value: object, name: str) -> dict[str, object]:
    record = value if isinstance(value, dict) else {}
    payload = record.get("structured_content")
    if record.get("is_error") is not False or not isinstance(payload, dict):
        raise AgentError(f"{name} is not a successful structured MCP result")
    return copy.deepcopy(payload)


def _load_ticket(args: argparse.Namespace) -> dict[str, object]:
    manifest_path = args.retention_manifest.expanduser().resolve()
    expected_manifest = base._expected_sha256(
        args.expected_retention_manifest_sha256,
        "expected retention-manifest SHA-256",
    )
    if (
        not manifest_path.is_file()
        or base._sha256_file(manifest_path) != expected_manifest
    ):
        raise AgentError("retention manifest is missing or hash-drifted")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"retention manifest is unreadable: {error}") from error
    ticket = retention.build_retention_ticket(
        manifest, repo_root=REPOSITORY_ROOT
    )
    if ticket.get("retention_ticket_id") != args.expected_retention_ticket_id:
        raise AgentError("retention ticket identity drifted")
    return ticket


def _verify_binary(path: Path, expected: object, name: str) -> None:
    expected_hash = base._expected_sha256(expected, f"expected {name} SHA-256")
    path = path.expanduser().resolve()
    if not path.is_file() or base._sha256_file(path) != expected_hash:
        raise AgentError(f"{name} is missing or hash-drifted")


def _same_postwar_candidate(
    pre: dict[str, object], current: dict[str, object], war_id: int
) -> bool:
    return bool(
        adapter._same_session(pre, current)
        and current["paused"] is True
        and current["revision"] > pre["revision"]
        and current["native_revision"] > pre["native_revision"]
        and current["date_raw"] >= pre["date_raw"]
        and adapter._war_row(current, war_id) is None
    )


async def _wait_for_stable_postwar(
    driver: Any,
    *,
    pre_binding: dict[str, object],
    war_id: int,
    timeout_seconds: float,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    deadline = time.monotonic() + timeout_seconds
    previous: dict[str, object] | None = None
    samples: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        snapshot = driver.take_snapshot()
        current = adapter._snapshot_binding(snapshot, "postwar wait snapshot")
        samples.append(copy.deepcopy(current))
        if len(samples) > 64:
            samples.pop(0)
        if _same_postwar_candidate(pre_binding, current, war_id):
            if previous is not None and adapter._same_paused_frame(
                previous, current
            ):
                return snapshot, samples
            previous = current
        else:
            previous = None
        await asyncio.sleep(0.1)
    raise AgentError(
        "native surrender did not reach two stable paused postwar samples"
    )


async def _run_private_sequence(
    driver: Any,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
    ticket: dict[str, object],
    postwar_timeout: float,
) -> dict[str, object]:
    pre_sequence = await base._run_mcp_sequence(
        driver,
        war_id=war_id,
        expected_character_id=expected_character_id,
        expected_date_raw=expected_date_raw,
    )
    if pre_sequence.get("ok") is not True:
        raise AgentError("pre-termination paused dual query is not GREEN")
    before = _structured_record(
        pre_sequence.get("before_snapshot"), "pre snapshot"
    )
    second = _structured_record(
        pre_sequence.get("second_query"), "second terms query"
    )
    terms = second.get("war_termination_terms")
    if not isinstance(terms, dict):
        raise AgentError("second terms query lacks war_termination_terms")
    pre = {
        "snapshot": before,
        "war_bound_observation": copy.deepcopy(
            terms.get("generic_war_bound_current")
        ),
        "terms_query_sequence": 2,
        "receipt_sequence": 2,
    }
    pre_binding, _observation, _generations = adapter._normalize_pre(
        ticket, pre
    )
    capabilities_record = _structured_record(
        pre_sequence.get("capabilities"), "capabilities"
    )
    advertised = set(capabilities_record.get("bridge_capabilities", []))
    required = {
        QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
        QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_CAPABILITY,
        QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY,
        SURRENDER_CAPABILITY,
    }
    action_steps = set(capabilities_record.get("action_steps", []))
    cleanup_step = (
        adapter.QUERY_RAIKTOR_WAR_BOUND_LOSS_CLEANUP_V1_STEP_PREFIX
        + str(war_id)
    )
    if not required <= advertised or cleanup_step in action_steps:
        raise AgentError("private cleanup/expiry capability boundary drifted")

    revision = pre_sequence.get("public_revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise AgentError("pre-termination public revision is invalid")
    action_step = f"surrender-war-{war_id}"
    submit = getattr(driver, "_execute_primitive_step", None)
    if not callable(submit):
        raise AgentError("private native submission seam is unavailable")

    from mcp import Client

    server = base.create_server(driver)
    async with Client(server) as client:
        termination = submit(action_step, expected_revision=revision)
        if termination != {
            "step": action_step,
            "accepted": True,
            "status": "submitted",
            "backend_id": "native-headless",
        }:
            raise AgentError("private native surrender returned a malformed ACK")
        stable_postwar, wait_samples = await _wait_for_stable_postwar(
            driver,
            pre_binding=pre_binding,
            war_id=war_id,
            timeout_seconds=postwar_timeout,
        )
        receipt = await adapter.collect_after_surrender(
            client,
            ticket=ticket,
            pre=pre,
            termination_result=termination,
            authorize_private_live=True,
        )

    validation = receipt.get("ticket_validation")
    boundaries = receipt.get("boundaries")
    checks = {
        "pre_dual_query_green": pre_sequence.get("ok") is True,
        "private_capabilities_present": required <= advertised,
        "cleanup_not_public_action": cleanup_step not in action_steps,
        "one_native_surrender_ack": termination.get("status") == "submitted",
        "stable_postwar_observed": bool(stable_postwar),
        "ticket_validation_green": isinstance(validation, dict)
        and validation.get("ok") is True,
        "no_readiness_promotion": isinstance(boundaries, dict)
        and all(
            boundaries.get(name) is False
            for name in (
                "source_specific_attribution_ready",
                "public_readiness_promoted",
                "action_readiness_promoted",
                "decision_ready",
                "automatic_surrender_ready",
                "gen034_closed",
            )
        ),
    }
    return {
        "allowed_gameplay_commands": [
            f"query-war-termination-terms-v1-{war_id}",
            f"query-war-termination-terms-v1-{war_id}",
            action_step,
            cleanup_step,
            adapter.QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX
            + str(ticket["opponent_character_id"]),
            adapter.QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX
            + str(ticket["opponent_character_id"]),
        ],
        "mutation_commands": [action_step],
        "pre_sequence": pre_sequence,
        "private_termination_result": termination,
        "stable_postwar_snapshot": stable_postwar,
        "postwar_wait_samples": wait_samples,
        "postwar_receipt": receipt,
        "checks": checks,
        "ok": all(checks.values()),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.authorize_private_live is not True:
            raise AgentError("private G2 action-bound live remains default-OFF")
        if args.postwar_timeout <= 0 or args.postwar_timeout > 120:
            raise AgentError("postwar timeout must be in (0, 120]")
        inventory = _process_inventory()
        if inventory.get("all_zero") is not True:
            raise AgentError("CK3/injector process inventory is not empty")
        _verify_binary(
            args.bridge_dll, args.expected_bridge_dll_sha256, "bridge DLL"
        )
        _verify_binary(
            args.bridge_injector,
            args.expected_bridge_injector_sha256,
            "bridge injector",
        )
        ticket = _load_ticket(args)

        async def sequence_runner(
            driver: Any,
            *,
            war_id: int,
            expected_character_id: int,
            expected_date_raw: int,
        ) -> dict[str, object]:
            return await _run_private_sequence(
                driver,
                war_id=war_id,
                expected_character_id=expected_character_id,
                expected_date_raw=expected_date_raw,
                ticket=ticket,
                postwar_timeout=float(args.postwar_timeout),
            )

        action_step = f"surrender-war-{args.war_id}"
        policy = {
            "mcp_first": True,
            "production_non_debug": True,
            "cold_checkpoint_short_path": True,
            "ocr_used": False,
            "visual_input_used": False,
            "time_advanced": False,
            "mutation_commands": [action_step],
            "private_default_off_authorization": True,
            "public_action_readiness_promoted": False,
            "automatic_surrender_ready": False,
            "gen034_closed": False,
        }
        payload, exit_code = base._run(
            args,
            sequence_runner=sequence_runner,
            report_kind=REPORT_KIND,
            policy_override=policy,
        )
        payload["formal_private_capture"] = {
            "retention_ticket_id": ticket["retention_ticket_id"],
            "only_mutation": action_step,
            "cleanup_destroyed_must_come_from_exact_store_reader": True,
            "war_id_absence_is_admission_only": True,
        }
        base._write_json_atomic(Path(str(payload["report_path"])), payload)
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "status": payload.get("status"),
                "report_path": payload.get("report_path"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
