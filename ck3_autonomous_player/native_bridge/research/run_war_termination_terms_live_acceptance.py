#!/usr/bin/env python3
"""Observe one frozen war-termination terms frame twice through official MCP.

This acceptance runner is intentionally read-only.  It restores one exact v2
checkpoint/driver-state pair into a fresh production profile, launches one
managed non-debug CK3 process, and calls only the public snapshot,
capabilities, and ``ck3_query_war_termination_terms`` MCP tools.  The complete
attempt directory is retained on both GREEN and RED.  The terms contract now
checks the Raiktor truce's evaluated duration on the public wire while keeping
persisted expiry explicitly unobserved; this does not open the six-domain or
surrender action gates.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import time
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.mcp_server import create_server  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
    query_war_termination_terms_step,
)
from xar_autoplayer.bridge.raiktor_truce_probe import (  # noqa: E402
    validate_pointer_contract,
    validate_truce_probe,
)
from xar_autoplayer.environment import (  # noqa: E402
    make_spec,
    prepare_profile,
    verify_profile,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import (  # noqa: E402
    NATIVE_DRIVER_STATE_FILENAME,
    NATIVE_SESSION_CHECKPOINT_FILENAME,
    NATIVE_SESSION_QUEUE_DIRNAME,
    native_session,
    validate_cold_start_checkpoint_for_pipe,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_SUPPORTED_SLICE = "raiktor_claim_cb_attacker_defeat_disposition"
EXPECTED_CB_KEY = "raiktor_claim_cb"
EXPECTED_UNOBSERVED_AFTER_FOUR_DOMAINS = [
    "actual_truce_expiry",
    "targeting_faction_discontent_delta",
    "glory_hound_vassal_opinion_rows",
    "antagonistic_clan_vassal_opinion_rows",
    "existing_house_feud_score_delta",
    "attacker_mandala_piety_experience_delta",
    "defender_mandala_serenity",
    "defender_accolade_glory",
    "laamp_actual_settlement_outside_cb_effect",
    "war_bound_army_losses",
]
TRUCE_SOURCE_CONTRACT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "raiktor_surrender_truce_v1_source_contract.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--source-driver-state", type=Path, required=True)
    parser.add_argument("--expected-checkpoint-sha256", required=True)
    parser.add_argument("--expected-driver-state-sha256", required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--war-id", type=int, required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--expected-date-raw", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--readiness-timeout", type=float, default=300.0)
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: object, name: str) -> str:
    result = str(value).strip().upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise AgentError(f"{name} must be 64 hexadecimal digits")
    return result


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _copy_exact(source: Path, target: Path, expected_sha256: str) -> dict[str, object]:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise AgentError(f"immutable input is missing: {source}")
    before = _sha256_file(source)
    if before != expected_sha256:
        raise AgentError(
            f"immutable input SHA-256 differs: {before} != {expected_sha256}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied = _sha256_file(target)
    after = _sha256_file(source)
    if copied != expected_sha256 or after != before:
        raise AgentError("immutable input changed while it was copied")
    return {
        "source": str(source),
        "copy": str(target.resolve()),
        "size": target.stat().st_size,
        "sha256": copied,
        "source_unchanged": after == before,
    }


def _driver_anchor(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"driver-state JSON is unavailable: {error}") from error
    checkpoint = value.get("last_checkpoint") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or value.get("format_version") != 2
        or not isinstance(value.get("pipe_name"), str)
        or not value.get("pipe_name")
        or not isinstance(checkpoint, dict)
    ):
        raise AgentError("driver-state does not contain a v2 cold checkpoint anchor")
    return {
        "pipe_name": value["pipe_name"],
        "episode_character_id": value.get("episode_character_id"),
        "episode_run_id": value.get("episode_run_id"),
        "command_history_count": len(value.get("command_history", [])),
        "last_checkpoint": copy.deepcopy(checkpoint),
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    if not isinstance(capabilities, dict):
        return {}
    value = capabilities.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _exact_build_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    war_id: int,
) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    hello_value = _diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    observed_sha = hello.get("expected_ck3_sha256", hello.get("executable_sha256"))
    observed_version = hello.get("expected_ck3_version", hello.get("game_version"))
    advertised = raw.get("bridge_capabilities")
    hello_capabilities = hello.get("capabilities")
    action_steps = raw.get("action_steps")
    required_step = query_war_termination_terms_step(war_id)
    checks = {
        "game_version": observed_version == EXPECTED_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": isinstance(observed_sha, str)
        and observed_sha.upper() == EXPECTED_EXECUTABLE_SHA256,
        "managed_executable_sha256": managed_executable_sha256.upper()
        == EXPECTED_EXECUTABLE_SHA256,
        "bridge_capability": isinstance(advertised, list)
        and QUERY_WAR_TERMINATION_TERMS_CAPABILITY in advertised,
        "hello_capability": isinstance(hello_capabilities, list)
        and QUERY_WAR_TERMINATION_TERMS_CAPABILITY in hello_capabilities,
        "action_step_family": isinstance(action_steps, list)
        and required_step in action_steps,
    }
    return {
        "expected_game_version": EXPECTED_GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        "required_capability": QUERY_WAR_TERMINATION_TERMS_CAPABILITY,
        "required_action_step_family": required_step,
        # Preserve the exact terms-query literals (or the adapter template)
        # when the proof stops before the MCP sequence. This keeps an
        # action-step advertisement mismatch diagnosable without retaining the
        # complete capabilities payload or weakening the gate.
        "observed_action_steps": sorted(
            {
                step
                for step in action_steps
                if isinstance(step, str)
                and (
                    step.startswith("query-war-termination-terms-v1-")
                    or step == "query-war-termination-terms-v1-N"
                )
            }
        )
        if isinstance(action_steps, list)
        else None,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _content_record(item: object) -> object:
    dump = getattr(item, "model_dump", None)
    if callable(dump):
        try:
            return dump(mode="json", by_alias=True)
        except (TypeError, ValueError):
            pass
    if isinstance(item, dict):
        return copy.deepcopy(item)
    return {
        "type": type(item).__name__,
        "text": str(getattr(item, "text", item)),
    }


def _mcp_record(result: Any) -> dict[str, object]:
    return {
        "result_type": type(result).__name__,
        "is_error": bool(getattr(result, "is_error", False)),
        "structured_content": copy.deepcopy(
            getattr(result, "structured_content", None)
        ),
        "content": [
            _content_record(item) for item in getattr(result, "content", [])
        ],
    }


class OfficialMcpResultEnvelopeError(RuntimeError):
    """Typed diagnostic for an official MCP result without structured data."""

    def __init__(self, tool_name: str, result: Any) -> None:
        self.tool_name = tool_name
        self.result_record = _mcp_record(result)
        content = self.result_record.get("content")
        content_count = len(content) if isinstance(content, list) else 0
        super().__init__(
            "official MCP tool "
            f"{tool_name} returned no structured_content "
            f"(result_type={self.result_record['result_type']}, "
            f"is_error={self.result_record['is_error']}, "
            f"content_count={content_count})"
        )

    def diagnostic(self) -> dict[str, object]:
        return {
            "status": "official_mcp_envelope_error",
            "ok": False,
            "failed_tool": self.tool_name,
            "result": copy.deepcopy(self.result_record),
        }


def _structured(result: Any, *, tool_name: str) -> dict[str, object]:
    value = getattr(result, "structured_content", None)
    if not isinstance(value, dict):
        raise OfficialMcpResultEnvelopeError(tool_name, result)
    return copy.deepcopy(value)


def _same_paused_binding(before: dict[str, object], after: dict[str, object]) -> bool:
    return bool(
        before.get("paused") is True
        and after.get("paused") is True
        and all(
            before.get(key) == after.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "episode_run_id",
            )
        )
    )


def _without_query_sequence(value: object) -> object:
    result = copy.deepcopy(value)
    if isinstance(result, dict):
        result.pop("query_sequence", None)
    return result


def _pointer_contract_checks() -> dict[str, bool]:
    """Load the frozen pointer-only CAddTruce contract for every attempt."""

    try:
        value = json.loads(TRUCE_SOURCE_CONTRACT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"ok": False}
    return validate_pointer_contract(value)


def _terms_checks(
    payload: dict[str, object],
    *,
    war_id: int,
) -> dict[str, bool]:
    terms_value = payload.get("war_termination_terms")
    terms = terms_value if isinstance(terms_value, dict) else {}
    cb_value = terms.get("casus_belli")
    cb = cb_value if isinstance(cb_value, dict) else {}
    readiness_value = terms.get("readiness")
    readiness = readiness_value if isinstance(readiness_value, dict) else {}
    gold_value = terms.get("gold_reparations")
    gold = gold_value if isinstance(gold_value, dict) else {}
    fame_value = terms.get("attacker_fame")
    fame = fame_value if isinstance(fame_value, dict) else {}
    prisoner_value = terms.get("prisoner_release")
    prisoner = prisoner_value if isinstance(prisoner_value, dict) else {}
    favor_value = terms.get("conditional_favor_hook")
    favor = favor_value if isinstance(favor_value, dict) else {}
    truce_value = terms.get("truce")
    truce = truce_value if isinstance(truce_value, dict) else {}
    claimant = terms.get("claimant_character_id")
    claimant_distinct = favor.get("claimant_distinct_from_attacker")
    evaluated_days = truce.get("evaluated_days")
    truce_duration_observed = (
        truce.get("direction") == "primary_attacker_toward_primary_defender"
        and truce.get("result") == "defeat"
        and truce.get("evaluated_days_observable") is True
        and isinstance(evaluated_days, int)
        and not isinstance(evaluated_days, bool)
        and evaluated_days >= 0
    )
    truce_expiry_unobserved = (
        truce.get("actual_expiry_observable") is False
        and truce.get("expiry_date_raw") is None
    )
    return {
        "typed_available": terms.get("status") == "available",
        "war_id": terms.get("war_id") == war_id,
        "raiktor_cb": cb.get("canonical_key") == EXPECTED_CB_KEY,
        "complete_cb_identity": isinstance(cb.get("database_index"), int)
        and not isinstance(cb.get("database_index"), bool)
        and cb.get("database_index") >= 0,
        "supported_slice": terms.get("supported_slice") == EXPECTED_SUPPORTED_SLICE,
        "claimant_identity": isinstance(claimant, int)
        and not isinstance(claimant, bool)
        and claimant > 0,
        "target_titles": isinstance(terms.get("target_title_ids"), list)
        and bool(terms.get("target_title_ids")),
        "gold_observed": gold.get("actual_amount_observable") is True,
        "prestige_observed": fame.get("actual_delta_observable") is True,
        "prisoners_observed": prisoner.get("actual_pairs_observable") is True,
        "favor_observed": favor.get("actual_applies_observable") is True,
        "favor_outer_gate_coherent": (
            claimant_distinct is True
            and favor.get("original_visible_root_traversed") is True
        )
        or (
            claimant_distinct is False
            and favor.get("original_visible_root_traversed") is False
            and favor.get("will_apply") is False
        ),
        "four_domain_readiness": all(
            readiness.get(key) is True
            for key in (
                "finance_ready",
                "gold_ready",
                "fame_factor_ready",
                "attacker_prestige_delta_ready",
                "prisoner_release_ready",
                "favor_hook_ready",
                "same_frame_stable",
            )
        ),
        "truce_duration_observed": truce_duration_observed
        and readiness.get("truce_ready") is True,
        "truce_expiry_unobserved": truce_expiry_unobserved,
        "war_bound_armies_still_unobserved": readiness.get(
            "war_bound_armies_ready"
        )
        is False,
        "full_decision_still_closed": all(
            readiness.get(key) is False
            for key in (
                "dynamic_deltas_ready",
                "decision_ready",
                "automatic_surrender_ready",
                "ready",
            )
        ),
        "unobserved_dynamic_effects_exact": terms.get(
            "unobserved_dynamic_effects"
        )
        == EXPECTED_UNOBSERVED_AFTER_FOUR_DOMAINS,
    }


async def _run_mcp_sequence(
    driver: NativeHeadlessGameplayDriver,
    *,
    war_id: int,
    expected_character_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    from mcp import Client

    server = create_server(driver)
    async with Client(server) as client:
        listed = await client.list_tools()
        tool_names = sorted(tool.name for tool in listed.tools)
        capabilities_result = await client.call_tool("ck3_get_capabilities", {})
        capabilities = _structured(
            capabilities_result, tool_name="ck3_get_capabilities"
        )
        before_result = await client.call_tool("ck3_take_snapshot", {})
        before = _structured(before_result, tool_name="ck3_take_snapshot:before")
        revision = before.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            raise RuntimeError("paused MCP snapshot lacks a public revision")
        first_result = await client.call_tool(
            "ck3_query_war_termination_terms",
            {"war_id": war_id, "expected_revision": revision},
        )
        first = _structured(
            first_result,
            tool_name="ck3_query_war_termination_terms:first",
        )
        between_result = await client.call_tool("ck3_take_snapshot", {})
        between = _structured(
            between_result, tool_name="ck3_take_snapshot:between"
        )
        second_result = await client.call_tool(
            "ck3_query_war_termination_terms",
            {"war_id": war_id, "expected_revision": revision},
        )
        second = _structured(
            second_result,
            tool_name="ck3_query_war_termination_terms:second",
        )
        after_result = await client.call_tool("ck3_take_snapshot", {})
        after = _structured(after_result, tool_name="ck3_take_snapshot:after")
    first_checks = _terms_checks(first, war_id=war_id)
    second_checks = _terms_checks(second, war_id=war_id)
    pointer_checks = _pointer_contract_checks()
    truce_checks = validate_truce_probe(
        before=before,
        between=between,
        after=after,
        first=first,
        second=second,
        tool_names=tool_names,
        allowed_gameplay_commands=[
            query_war_termination_terms_step(war_id),
            query_war_termination_terms_step(war_id),
        ],
        mutation_commands=[],
        expected_war_id=war_id,
        expected_character_id=expected_character_id,
        expected_date_raw=expected_date_raw,
        pointer_contract_checks=pointer_checks,
    )
    player_value = before.get("played_character")
    player = player_value if isinstance(player_value, dict) else {}
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    checks = {
        "official_tools_listed": all(
            name in tool_names
            for name in (
                "ck3_get_capabilities",
                "ck3_take_snapshot",
                "ck3_query_war_termination_terms",
            )
        ),
        "mcp_results_not_errors": not any(
            bool(getattr(result, "is_error", False))
            for result in (
                capabilities_result,
                before_result,
                first_result,
                between_result,
                second_result,
                after_result,
            )
        ),
        "initial_paused": before.get("paused") is True,
        "expected_character": player.get("character_id") == expected_character_id,
        "expected_date": before.get("date_raw") == expected_date_raw,
        "between_same_paused_binding": _same_paused_binding(before, between),
        "after_same_paused_binding": _same_paused_binding(before, after),
        "first_four_domains": all(first_checks.values()),
        "second_four_domains": all(second_checks.values()),
        "query_sequence_successor": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence == first_sequence + 1,
        "normalized_payloads_equal": _without_query_sequence(first)
        == _without_query_sequence(second),
        "binding_matches_revision": all(
            result.get("queried_revision") == revision
            and result.get("queried_snapshot_id") == before.get("snapshot_id")
            and result.get("queried_native_revision")
            == before.get("native_revision")
            for result in (first, second)
        ),
        # Keep this narrower gate independent from the four-domain terms
        # acceptance.  It is the exact next G2 deliverable and remains
        # read-only even when one of the wider domains is unavailable.
        "truce_probe": truce_checks["ok"],
    }
    return {
        "allowed_gameplay_commands": [
            query_war_termination_terms_step(war_id),
            query_war_termination_terms_step(war_id),
        ],
        "mutation_commands": [],
        "tool_names": tool_names,
        "public_revision": revision,
        "capabilities": _mcp_record(capabilities_result),
        "before_snapshot": _mcp_record(before_result),
        "first_query": _mcp_record(first_result),
        "between_snapshot": _mcp_record(between_result),
        "second_query": _mcp_record(second_result),
        "after_snapshot": _mcp_record(after_result),
        "first_terms_checks": first_checks,
        "second_terms_checks": second_checks,
        "pointer_contract": {
            "path": str(TRUCE_SOURCE_CONTRACT),
            "sha256": (
                _sha256_file(TRUCE_SOURCE_CONTRACT)
                if TRUCE_SOURCE_CONTRACT.is_file()
                else None
            ),
            "checks": pointer_checks,
        },
        "truce_probe_checks": truce_checks,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run(
    args: argparse.Namespace,
    *,
    sequence_runner: Any = _run_mcp_sequence,
    report_kind: str = "ck3_war_termination_terms_four_domain_live_acceptance",
) -> tuple[dict[str, object], int]:
    started_wall = utc_now()
    started = time.monotonic()
    attempt = args.attempt_dir.expanduser().resolve()
    if attempt.exists():
        raise AgentError(f"attempt directory already exists: {attempt}")
    attempt.mkdir(parents=True, exist_ok=False)
    report_path = attempt / "report.json"
    expected_checkpoint_sha = _expected_sha256(
        args.expected_checkpoint_sha256, "expected checkpoint SHA-256"
    )
    expected_driver_sha = _expected_sha256(
        args.expected_driver_state_sha256, "expected driver-state SHA-256"
    )
    source_checkpoint = args.source_checkpoint.expanduser().resolve()
    source_driver_state = args.source_driver_state.expanduser().resolve()
    source_before = {
        "checkpoint": _sha256_file(source_checkpoint),
        "driver_state": _sha256_file(source_driver_state),
    }
    session_state: dict[str, object] = {"report": None, "error": None}
    stop_event = threading.Event()
    session_done = threading.Event()
    session_thread: threading.Thread | None = None
    driver: NativeHeadlessGameplayDriver | None = None
    driver_closed = False
    session_started = False
    preparation: dict[str, object] | None = None
    inputs: dict[str, object] | None = None
    anchor: dict[str, object] | None = None
    cold_validation: dict[str, object] | None = None
    readiness: dict[str, object] | None = None
    mcp_sequence: dict[str, object] | None = None
    exact_build: dict[str, object] | None = None
    primary_error: str | None = None
    cleanup: dict[str, object] = {
        "ok": True,
        "reason": "session was not started",
    }

    try:
        immutable_dir = attempt / "inputs"
        immutable_checkpoint = immutable_dir / NATIVE_SESSION_CHECKPOINT_FILENAME
        immutable_driver = immutable_dir / NATIVE_DRIVER_STATE_FILENAME
        checkpoint_copy = _copy_exact(
            source_checkpoint, immutable_checkpoint, expected_checkpoint_sha
        )
        driver_copy = _copy_exact(
            source_driver_state, immutable_driver, expected_driver_sha
        )
        anchor = _driver_anchor(immutable_driver)
        if anchor.get("episode_character_id") != args.expected_character_id:
            raise AgentError("driver-state CharacterID differs from request")
        checkpoint_anchor = anchor.get("last_checkpoint")
        if not isinstance(checkpoint_anchor, dict):
            raise AgentError("driver-state checkpoint anchor is malformed")
        if (
            str(checkpoint_anchor.get("sha256", "")).upper()
            != expected_checkpoint_sha
            or checkpoint_anchor.get("date_raw") != args.expected_date_raw
        ):
            raise AgentError("driver-state checkpoint identity differs from request")
        inputs = {
            "checkpoint": checkpoint_copy,
            "driver_state": driver_copy,
        }

        state_dir = attempt / "state"
        spec = make_spec(state_dir, args.game_dir.expanduser().resolve())
        prepared = prepare_profile(spec)
        verified = verify_profile(spec)
        state_checkpoint = (
            spec.profile_dir / "save games" / NATIVE_SESSION_CHECKPOINT_FILENAME
        )
        state_driver = (
            spec.state_dir
            / NATIVE_SESSION_QUEUE_DIRNAME
            / NATIVE_DRIVER_STATE_FILENAME
        )
        state_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        state_driver.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(immutable_checkpoint, state_checkpoint)
        shutil.copy2(immutable_driver, state_driver)
        if (
            _sha256_file(state_checkpoint) != expected_checkpoint_sha
            or _sha256_file(state_driver) != expected_driver_sha
        ):
            raise AgentError("projected cold checkpoint bundle differs")
        preparation = {
            "state_dir": str(spec.state_dir),
            "profile_dir": str(spec.profile_dir),
            "environment_sha256": verified.get("environment_sha256"),
            "production_tree_sha256": (
                prepared.get("mod", {}).get("production_tree_sha256")
                if isinstance(prepared.get("mod"), dict)
                else None
            ),
            "checkpoint_path": str(state_checkpoint),
            "driver_state_path": str(state_driver),
        }
        pipe_name = str(anchor["pipe_name"])
        cold_validation = validate_cold_start_checkpoint_for_pipe(spec, pipe_name)
        config = NativeBridgeLaunchConfig(
            mode=PURE_NATIVE_MODE,
            pipe_name=pipe_name,
            dll_path=args.bridge_dll.expanduser().resolve(),
            injector_path=args.bridge_injector.expanduser().resolve(),
        )

        def supervise() -> None:
            try:
                session_state["report"] = native_session(
                    spec,
                    timeout_seconds=float(args.timeout) + 90.0,
                    native_bridge=config,
                    input_stream=None,
                    output_stream=None,
                    poll_interval_seconds=0.05,
                    cold_start_checkpoint=True,
                    stop_event=stop_event,
                )
            except BaseException as error:
                session_state["error"] = f"{type(error).__name__}: {error}"
            finally:
                session_done.set()

        driver = NativeHeadlessGameplayDriver(
            pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        session_thread = threading.Thread(
            target=supervise,
            name="xar-war-termination-terms-live",
            daemon=False,
        )
        session_thread.start()
        session_started = True
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=float(args.readiness_timeout),
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=True,
            allow_terminal=False,
        )
        capabilities = driver.capabilities()
        exact_build = _exact_build_proof(
            capabilities,
            managed_executable_sha256=_sha256_file(spec.game_exe),
            war_id=args.war_id,
        )
        if exact_build.get("ok") is not True:
            raise RuntimeError("exact-build/capability proof failed")
        mcp_sequence = asyncio.run(
            sequence_runner(
                driver,
                war_id=args.war_id,
                expected_character_id=args.expected_character_id,
                expected_date_raw=args.expected_date_raw,
            )
        )
        if mcp_sequence.get("ok") is not True:
            raise RuntimeError("paused double-sample MCP proof failed")
    except BaseException as error:
        if isinstance(error, OfficialMcpResultEnvelopeError):
            mcp_sequence = error.diagnostic()
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None and session_started:
            session_thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )
        cleanup = _cleanup_report(
            session_state.get("report"),
            session_error=session_state.get("error"),
            driver_closed=driver_closed,
            elapsed_seconds=stop_elapsed,
        )
        if cleanup.get("ok") is not True and primary_error is None:
            primary_error = str(
                session_state.get("error")
                or cleanup.get("reason")
                or "managed CK3 cleanup was not proven"
            )

    source_after = {
        "checkpoint": (
            _sha256_file(source_checkpoint) if source_checkpoint.is_file() else None
        ),
        "driver_state": (
            _sha256_file(source_driver_state) if source_driver_state.is_file() else None
        ),
    }
    source_unchanged = source_before == source_after
    if not source_unchanged and primary_error is None:
        primary_error = "immutable source checkpoint bundle changed"
    ok = bool(
        primary_error is None
        and exact_build
        and exact_build.get("ok") is True
        and mcp_sequence
        and mcp_sequence.get("ok") is True
        and cleanup.get("ok") is True
        and source_unchanged
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": report_kind,
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "status": "green" if ok else "red",
        "ok": ok,
        "attempt_dir": str(attempt),
        "report_path": str(report_path),
        "policy": {
            "mcp_first": True,
            "production_non_debug": True,
            "cold_checkpoint": True,
            "ocr_used": False,
            "visual_input_used": False,
            "time_advanced": False,
            "mutation_commands": [],
            "surrender_action_enabled": False,
            "remaining_blockers": [
                "actual_truce_expiry",
                "war_bound_army_losses",
            ],
        },
        "requested_identity": {
            "war_id": args.war_id,
            "character_id": args.expected_character_id,
            "date_raw": args.expected_date_raw,
        },
        "inputs": inputs,
        "driver_anchor": anchor,
        "cold_validation": cold_validation,
        "preparation": preparation,
        "identity": {
            "game_executable": str(
                (args.game_dir.expanduser().resolve() / "binaries" / "ck3.exe")
            ),
            "game_executable_sha256": (
                _sha256_file(
                    args.game_dir.expanduser().resolve() / "binaries" / "ck3.exe"
                )
                if (
                    args.game_dir.expanduser().resolve() / "binaries" / "ck3.exe"
                ).is_file()
                else None
            ),
            "bridge_dll": str(args.bridge_dll.expanduser().resolve()),
            "bridge_dll_sha256": _sha256_file(
                args.bridge_dll.expanduser().resolve()
            ),
            "bridge_injector": str(args.bridge_injector.expanduser().resolve()),
            "bridge_injector_sha256": _sha256_file(
                args.bridge_injector.expanduser().resolve()
            ),
        },
        "readiness": readiness,
        "exact_build_proof": exact_build,
        "mcp_sequence": mcp_sequence,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "source_invariant": {
            "before": source_before,
            "after": source_after,
            "unchanged": source_unchanged,
        },
        "error": primary_error,
    }
    _write_json_atomic(report_path, payload)
    return payload, 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload, exit_code = _run(args)
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
