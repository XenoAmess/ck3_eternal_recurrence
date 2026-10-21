"""Typed cold-contract qualification and fail-closed request admission.

Offline qualification grants only a new read-only readiness attempt. Historical
SEM replay never supplies live readiness, a warm binding, or business credit.
Request permits remain inside one call stack and have no JSON decoder.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Callable, Literal, Protocol

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, ExactRefV1, JsonObject, JsonValue, decode_current_saved_basis_v1,
    exact_read, integer, json_object, need, parse_ref, record, rows, text, utc,
)
from tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1 import (
    ColdPlanV1, ColdQuoteV1, parse_plan_v1, parse_quote_v1,
)
from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
    LocalBasisReaderV1, WarmCurrentSavedFeederInputsV1,
    load_current_saved_warm_inputs_v1, validate_campaign_score_junction_physical_v1,
    validate_campaign_score_junction_source_v1,
    validate_current_saved_cold_inputs_v1, validate_current_saved_cold_owner_v1,
)

PREFLIGHT_SCHEMA = "xar.current-saved-campaign-preflight/v1"
OFFLINE_PHASE = "OfflineColdContractQualified"
SEMANTIC_TOOL = "ck3_take_semantic_snapshot_private_v1"
CAPABILITIES_TOOL = "ck3_get_capabilities"
_PHASES = ("semantic", "capabilities", "ready")
_ISSUER = object()
_MAX_SMALL = 1048576
_CORE_NAME = "current_saved_campaign_preflight_v1.py"


def _same_path(left: str | Path, right: str | Path) -> bool:
    return Path(left).resolve() == Path(right).resolve()


def _json_bytes(value: object) -> bytes:
    return json.dumps(json_object(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _small(reader: BasisReaderV1, reference: ExactRefV1,
           limit: int = _MAX_SMALL) -> dict[str, object]:
    return record(json.loads(exact_read(reader, reference, limit)))


def _nonce(value: object) -> str:
    result = text(value)
    need(re.fullmatch("[0-9a-f]{32}", result) is not None, "exact current attempt nonce")
    return result


def _phase(queue: object) -> Literal["semantic", "capabilities", "ready"]:
    cold = record(_attribute(queue, "_normal_cold"))
    value = text(cold.get("phase"))
    if value == "semantic":
        return "semantic"
    if value == "capabilities":
        return "capabilities"
    need(value == "ready", "unknown cold phase is not readiness admission")
    return "ready"


def _attribute(value: object, name: str) -> object:
    result: object = getattr(value, name, None)
    return result


def _actual_ref(path: Path, reader: BasisReaderV1,
                limit: int = _MAX_SMALL) -> ExactRefV1:
    before = reader.stat(str(path))
    need(0 < before.bytes <= limit, "bounded actual small evidence")
    with path.open("rb") as stream:
        payload = stream.read(limit + 1)
    need(len(payload) == before.bytes and reader.stat(str(path)) == before,
         "small evidence changed during read")
    return ExactRefV1(str(path.resolve()), len(payload), hashlib.sha256(payload).hexdigest())


def _runtime_sources(quote: ColdQuoteV1) -> tuple[ExactRefV1, ...]:
    names = set(quote.canonical_entry_paths)
    required_basenames = {
        _CORE_NAME, "root_p37c23_cold_resume.py", "startup_readiness_v1.py",
        "root_score_month_samples_c23.py",
    }
    by_name: dict[str, list[ExactRefV1]] = {name: [] for name in required_basenames}
    selected: dict[str, ExactRefV1] = {}
    for row in quote.files:
        if row.relative_path is not None and row.relative_path in names:
            selected[row.path] = ExactRefV1(row.path, row.bytes, row.sha256)
        if Path(row.path).name in required_basenames:
            by_name[Path(row.path).name].append(ExactRefV1(row.path, row.bytes, row.sha256))
    need(len(selected) == len(names) == 8, "all eight actual canonical source pins")
    for name, references in by_name.items():
        need(len(references) == 1, "one actual runtime source: " + name)
        selected[references[0].path] = references[0]
    return tuple(selected[key] for key in sorted(selected))


def _method_ast(payload: bytes, name: str) -> str:
    tree = ast.parse(payload)
    methods = [node for node in ast.walk(tree)
               if isinstance(node, ast.FunctionDef) and node.name == name]
    need(len(methods) == 1, "one original cold method: " + name)
    return ast.dump(methods[0], include_attributes=False)


@dataclass(frozen=True)
class HistoricalSemanticReplayV1:
    receipt_ref: ExactRefV1
    helper_ref: ExactRefV1
    semantic_ref: ExactRefV1
    launch_ref: ExactRefV1
    original_cold_ref: ExactRefV1
    original_queue_ref: ExactRefV1
    score_ref: ExactRefV1
    anchor_ref: ExactRefV1
    historical_sequence: int
    check_after_ast_sha256: str

    def to_wire(self) -> JsonObject:
        return {
            "receipt_ref": self.receipt_ref.to_wire(), "helper_ref": self.helper_ref.to_wire(),
            "semantic_ref": self.semantic_ref.to_wire(), "launch_ref": self.launch_ref.to_wire(),
            "original_cold_ref": self.original_cold_ref.to_wire(),
            "original_queue_ref": self.original_queue_ref.to_wire(),
            "score_ref": self.score_ref.to_wire(), "anchor_ref": self.anchor_ref.to_wire(),
            "historical_sequence": self.historical_sequence,
            "check_after_ast_sha256": self.check_after_ast_sha256,
            "historical_outer_context_reconstructed": True,
            "historical_row_modified": False, "actual_rpc_calls": 0,
            "canonical_score_writes": 0, "fresh_native_readiness_claimed": False,
        }


def parse_historical_semantic_replay_v1(value: object) -> HistoricalSemanticReplayV1:
    row = record(value)
    reference_fields = (
        "receipt_ref", "helper_ref", "semantic_ref", "launch_ref",
        "original_cold_ref", "original_queue_ref", "score_ref", "anchor_ref",
    )
    expected = set(reference_fields) | {
        "historical_sequence", "check_after_ast_sha256",
        "historical_outer_context_reconstructed", "historical_row_modified",
        "actual_rpc_calls", "canonical_score_writes", "fresh_native_readiness_claimed",
    }
    need(set(row) == expected, "exact historical replay fields")
    need(row["historical_outer_context_reconstructed"] is True
         and row["historical_row_modified"] is False
         and row["fresh_native_readiness_claimed"] is False
         and integer(row["actual_rpc_calls"]) == 0
         and integer(row["canonical_score_writes"]) == 0, "offline historical replay scope")
    digest = text(row["check_after_ast_sha256"])
    need(re.fullmatch("[0-9a-f]{64}", digest) is not None, "exact method digest")
    references = tuple(parse_ref(row[name]) for name in reference_fields)
    return HistoricalSemanticReplayV1(
        references[0], references[1], references[2], references[3], references[4],
        references[5], references[6], references[7], integer(row["historical_sequence"], 1), digest)


def _archive_historical_replay_v1(
    reference: ExactRefV1, full: HistoricalStartupDispatchReplayV1,
    fixture: dict[str, object], plan: ColdPlanV1, quote: ColdQuoteV1,
    reader: BasisReaderV1,
) -> HistoricalSemanticReplayV1:
    """Bind the full public replay to immutable originals; partial reports are provenance only."""
    payloads = record(fixture.get("payloads"))
    need(set(payloads) == {"anchor", "checkpoint_cadence", "halted_observer", "launch",
         "material_cold_resume", "pending_requests", "queue", "score", "sdk_lifecycle_contract",
         "seed", "semantic_response", "startup_readiness"}, "exact approved archive payload roles")
    def original(name: str) -> tuple[ExactRefV1, bytes]:
        return decode_current_saved_historical_payload_v1(payloads.get(name))
    cold_ref, cold_raw = original("material_cold_resume")
    queue_ref, _ = original("queue")
    score_ref, _ = original("score")
    semantic_ref, semantic_raw = original("semantic_response")
    launch_ref, launch_raw = original("launch")
    anchor_ref, _ = original("anchor")
    request = record(record(json.loads(semantic_raw)).get("request"))
    sequence = integer(request.get("sequence"), 1)
    need(sequence == full.historical_sequence and request.get("tool") == SEMANTIC_TOOL
         and record(request.get("arguments")) == {}, "unaltered original historical SEM request")
    need(record(json.loads(launch_raw)).get("machine_id") == full.historical_subject_machine_id,
         "historical launch belongs to the explicitly historical subject")
    method = _method_ast(cold_raw, "check_after")
    cold_rows = [row for row in quote.files if Path(row.path).name == "root_p37c23_cold_resume.py"]
    score_rows = [row for row in quote.files if Path(row.path).name == "root_score_month_samples_c23.py"]
    need(len(cold_rows) == len(score_rows) == 1, "one actual current replay receiver and observer")
    current = cold_rows[0]
    need(_method_ast(exact_read(reader, ExactRefV1(current.path, current.bytes, current.sha256),
                                _MAX_SMALL), "check_after") == method,
         "current receiver retains the exact original SEM postcheck")
    need((score_rows[0].bytes, score_rows[0].sha256) == (score_ref.bytes, score_ref.sha256)
         and anchor_ref == quote.campaign_score_junction.anchor_ref,
         "actual current observer and canonical anchor retain immutable original bytes")
    exact_read(reader, anchor_ref, 65536)
    return HistoricalSemanticReplayV1(
        reference, full.harness_ref, semantic_ref, launch_ref, cold_ref, queue_ref,
        score_ref, anchor_ref, sequence, hashlib.sha256(method.encode()).hexdigest())


@dataclass(frozen=True)
class CurrentSavedCampaignPreflightV1:
    machine_id: str
    observed_at_utc: str
    runtime_root: str
    attempt_nonce: str
    task_nonce: str
    plan_ref: ExactRefV1
    quote_ref: ExactRefV1
    basis_ref: ExactRefV1
    validation_ref: ExactRefV1
    core_source_ref: ExactRefV1
    runtime_source_refs: tuple[ExactRefV1, ...]
    replay: HistoricalSemanticReplayV1
    startup_dispatch_replay_ref: ExactRefV1
    consumer_probe_ref: ExactRefV1
    current_next_sequence: int
    files_verified: int
    canonical_entry_count: Literal[8]
    closure_count: int

    def to_wire(self) -> JsonObject:
        return {
            "schema": PREFLIGHT_SCHEMA, "machine_id": self.machine_id,
            "observed_at_utc": self.observed_at_utc, "phase": OFFLINE_PHASE,
            "runtime_root": self.runtime_root, "attempt_nonce": self.attempt_nonce,
            "task_nonce": self.task_nonce, "plan_ref": self.plan_ref.to_wire(),
            "quote_ref": self.quote_ref.to_wire(), "basis_ref": self.basis_ref.to_wire(),
            "validation_ref": self.validation_ref.to_wire(),
            "core_source_ref": self.core_source_ref.to_wire(),
            "runtime_source_refs": [item.to_wire() for item in self.runtime_source_refs],
            "historical_replay": self.replay.to_wire(),
            "startup_dispatch_replay_ref": self.startup_dispatch_replay_ref.to_wire(),
            "consumer_probe_ref": self.consumer_probe_ref.to_wire(),
            "current_next_sequence": self.current_next_sequence,
            "files_verified": self.files_verified,
            "canonical_entry_count": self.canonical_entry_count,
            "closure_count": self.closure_count,
            "read_only_game_start_permitted": True, "full_loop_permitted": False,
            "ordinary_cycle_credit": 0, "game_day_credit": 0,
            "original_actions_replayed": False, "live_semantic_accepted": False,
            "live_warm_bound": False,
        }



def parse_current_saved_campaign_preflight_v1(value: object) -> CurrentSavedCampaignPreflightV1:
    row = record(value)
    expected = {
        "schema", "machine_id", "observed_at_utc", "phase", "runtime_root",
        "attempt_nonce", "task_nonce", "plan_ref", "quote_ref", "basis_ref", "validation_ref",
        "core_source_ref", "runtime_source_refs", "historical_replay", "current_next_sequence",
        "files_verified", "canonical_entry_count", "closure_count",
        "startup_dispatch_replay_ref", "consumer_probe_ref",
        "read_only_game_start_permitted", "full_loop_permitted", "ordinary_cycle_credit",
        "game_day_credit", "original_actions_replayed", "live_semantic_accepted", "live_warm_bound",
    }
    need(set(row) == expected and row["schema"] == PREFLIGHT_SCHEMA
         and row["phase"] == OFFLINE_PHASE, "exact offline preflight contract")
    need(row["read_only_game_start_permitted"] is True
         and row["full_loop_permitted"] is False and row["original_actions_replayed"] is False
         and row["live_semantic_accepted"] is False and row["live_warm_bound"] is False
         and integer(row["ordinary_cycle_credit"]) == 0
         and integer(row["game_day_credit"]) == 0, "offline never grants live or business credit")
    observed = text(row["observed_at_utc"]); utc(observed)
    need(integer(row["canonical_entry_count"]) == 8, "canonical eight retained")
    closure = integer(row["closure_count"], 1)
    need(closure <= 64, "original finite active closure limit")
    runtime = text(row["runtime_root"])
    need(Path(runtime).is_absolute(), "absolute actual runtime root")
    sources = tuple(parse_ref(item) for item in rows(row["runtime_source_refs"]))
    need(8 <= len(sources) <= 64 and len({item.path for item in sources}) == len(sources),
         "finite unique receiver source pins")
    result = CurrentSavedCampaignPreflightV1(
        text(row["machine_id"]), observed, runtime, _nonce(row["attempt_nonce"]),
        _nonce(row["task_nonce"]), parse_ref(row["plan_ref"]), parse_ref(row["quote_ref"]),
        parse_ref(row["basis_ref"]), parse_ref(row["validation_ref"]),
        parse_ref(row["core_source_ref"]), sources,
        parse_historical_semantic_replay_v1(row["historical_replay"]),
        parse_ref(row["startup_dispatch_replay_ref"]), parse_ref(row["consumer_probe_ref"]),
        integer(row["current_next_sequence"], 1), integer(row["files_verified"], 1), 8, closure)
    need(result.replay.historical_sequence < result.current_next_sequence,
         "historical and current request sequence remain distinct")
    return result


def preflight_current_saved_campaign_v1(
    plan_ref: ExactRefV1, quote_ref: ExactRefV1, *,
    replay_ref: ExactRefV1, consumer_probe_ref: ExactRefV1,
    expected_machine_id: str, expected_runtime_root: Path,
    expected_attempt_nonce: str, expected_task_nonce: str, reader: BasisReaderV1,
) -> CurrentSavedCampaignPreflightV1:
    plan_wire = _small(reader, plan_ref)
    quote_wire = _small(reader, quote_ref)
    plan, quote = parse_plan_v1(plan_wire), parse_quote_v1(quote_wire)
    need(_json_bytes(plan.to_wire()) == _json_bytes(plan_wire)
         and _json_bytes(quote.to_wire()) == _json_bytes(quote_wire),
         "serialized Plan and Quote roundtrip")
    need(plan.machine_id == quote.machine_id == expected_machine_id == current_execution_machine_id_v1()
         and _same_path(plan.runtime_root, expected_runtime_root)
         and _same_path(quote.runtime_root, expected_runtime_root)
         and plan.attempt_nonce == _nonce(expected_attempt_nonce)
         and plan.task_nonce == _nonce(expected_task_nonce)
         and quote.plan_ref == plan_ref and quote.basis_ref == plan.basis_ref
         and quote.validation_ref == plan.validation_ref, "actual preflight run binding")
    post = validate_current_saved_cold_owner_v1(
        plan_ref, quote_ref, reader=reader, expected_machine_id=expected_machine_id)
    basis = decode_current_saved_basis_v1(exact_read(reader, plan.basis_ref, 65536),
                                         expected_machine_id=expected_machine_id)
    inputs = validate_current_saved_cold_inputs_v1(
        basis, basis_ref=plan.basis_ref, validation_ref=plan.validation_ref, reader=reader)
    validate_campaign_score_junction_source_v1(
        quote.campaign_score_junction, inputs.basis, runtime_root=expected_runtime_root, reader=reader)
    validate_campaign_score_junction_physical_v1(
        quote.campaign_score_junction, runtime_root=expected_runtime_root, reader=reader)
    sources = _runtime_sources(quote)
    for reference in sources:
        exact_read(reader, reference, _MAX_SMALL)
    source_rows = [row for row in plan.source_rows if Path(row.relative_path).name == _CORE_NAME]
    need(len(source_rows) == 1, "core actual source row")
    core = source_rows[0].source_ref
    need(_same_path(core.path, __file__) or any(
        _same_path(item.path, __file__) and (item.bytes, item.sha256) == (core.bytes, core.sha256)
        for item in sources), "executed preflight core source origin")
    exact_read(reader, core, 147456)
    _, replay = _full_historical_replay(replay_ref, plan, quote, core, reader)
    _validate_consumer_probe(consumer_probe_ref, plan_ref, quote_ref, plan, reader)
    result = CurrentSavedCampaignPreflightV1(
        expected_machine_id, datetime.now(timezone.utc).isoformat(),
        str(expected_runtime_root.resolve()), plan.attempt_nonce, plan.task_nonce,
        plan_ref, quote_ref, plan.basis_ref, plan.validation_ref, core, sources,
        replay, replay_ref, consumer_probe_ref, basis.next_sequence, integer(post.get("files_verified"), 1), 8,
        integer(post.get("closure_count"), 1))
    wire = result.to_wire()
    need(parse_current_saved_campaign_preflight_v1(json.loads(_json_bytes(wire))) == result,
         "actual public preflight serialized roundtrip")
    return result


def verify_current_saved_preflight_receipt_v1(
    preflight_ref: ExactRefV1, *, plan_ref: ExactRefV1, quote_ref: ExactRefV1,
    runtime_root: Path, expected_machine_id: str, expected_attempt_nonce: str,
    expected_task_nonce: str, reader: BasisReaderV1,
) -> CurrentSavedCampaignPreflightV1:
    sealed = parse_current_saved_campaign_preflight_v1(_small(reader, preflight_ref))
    need(sealed.plan_ref == plan_ref and sealed.quote_ref == quote_ref,
         "Prepared must pin this Plan, Quote, and offline receipt")
    actual = preflight_current_saved_campaign_v1(
        plan_ref, quote_ref, replay_ref=sealed.startup_dispatch_replay_ref,
        consumer_probe_ref=sealed.consumer_probe_ref,
        expected_machine_id=expected_machine_id, expected_runtime_root=runtime_root,
        expected_attempt_nonce=expected_attempt_nonce, expected_task_nonce=expected_task_nonce,
        reader=reader)
    left, right = sealed.to_wire(), actual.to_wire()
    left.pop("observed_at_utc"); right.pop("observed_at_utc")
    need(_json_bytes(left) == _json_bytes(right), "launch revalidated actual offline contract")
    return sealed


def current_execution_machine_id_v1() -> str:
    import os
    from tools.ck3_live_run_id import MACHINE_ENV, current_machine_id
    need(not os.environ.get(MACHINE_ENV), "production machine identity override is forbidden")
    return current_machine_id()


@dataclass(frozen=True)
class CurrentSavedRequestPermitV1:
    runtime_root: str
    machine_id: str
    attempt_nonce: str
    task_nonce: str
    sequence: int
    phase: Literal["semantic", "capabilities", "ready"]
    request_json: bytes
    config_ref: ExactRefV1
    game_ref: ExactRefV1
    sdk_pair_ref: ExactRefV1
    control_ref: ExactRefV1 | None
    _issuer: object = field(repr=False, compare=False)


def _read_actual(path: Path, reader: BasisReaderV1,
                 limit: int = 65536) -> tuple[ExactRefV1, dict[str, object]]:
    reference = _actual_ref(path, reader, limit)
    return reference, _small(reader, reference, limit)


def _request(value: object) -> JsonObject:
    row = json_object(value)
    integer(row.get("sequence"), 1)
    tool, command = row.get("tool"), row.get("command")
    need((isinstance(tool, str) and bool(tool) and command is None)
         or (tool is None and command == "full_loop"), "one actual tool or FULL control request")
    if tool is not None:
        need("arguments" in row and record(row["arguments"]) == json_object(row["arguments"]),
             "explicit request argument object")
    else:
        arguments = record(row.get("arguments", {}))
        need(set(arguments) <= {"max_turns"}, "finite ordinary FULL arguments")
        maximum = integer(arguments.get("max_turns", 30), 1)
        need(maximum <= 30, "ordinary FULL batch remains at most thirty cycles")
    return row


def _clean_flags(queue: object | None, root: Path) -> None:
    if queue is not None:
        need(hasattr(queue, "halted") and _attribute(queue, "halted") is None,
             "explicit nullable original halted state is required before new RPC")
    for name in (
        "ROOT-CURRENT-HALT-P37.json", "ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json",
        "ROOT-GUARD-FAILURE-P37.json", "REQUEST-ADMISSION-CLOSED-C23",
        "EXIT-SDK-P37C23",
    ):
        need(not (root / name).exists(), "retained terminal evidence forbids new RPC: " + name)
    q = root / "p37-queue"
    need(not (q / "EXIT-SDK-P37C23").exists()
         and not any(q.glob("ROOT-REQUEST-HALTED-*.json")),
         "retained Queue halt evidence forbids new RPC")


def _settled(sequence: int, root: Path, reader: BasisReaderV1) -> bool:
    after = root / "p37-queue" / f"{sequence:04d}-after-result.json"
    response = root / "p37-responses" / f"{sequence:04d}-1-result.json"
    if not response.is_file():
        return False
    key = (str(root.resolve()), sequence)
    cached = _ACCEPTED_RESPONSES.get(key)
    if cached is not None:
        need(after.is_file() and reader.stat(str(after)) == cached.after_identity
             and reader.stat(str(response)) == cached.response_identity,
             "accepted postcheck response/marker FileID or stat drift")
        return True
    if not after.is_file():
        inflight = root / "p37-queue" / f"INFLIGHT-{sequence:04d}.json"
        if not inflight.is_file():
            return False
        _, context = _read_actual(inflight, reader, 16384)
        if context.get("control_only") is not True:
            return False
        _, completed = _read_actual(response, reader, 16384)
        result = record(completed.get("result"))
        body = record(result.get("structured_content"))
        request = record(completed.get("request"))
        return (request.get("command") == "full_loop"
                and _json_bytes(context.get("request")) == _json_bytes(request)
                and integer(request.get("sequence"), 1) == sequence
                and completed.get("client_error") is None and result.get("is_error") is False
                and body.get("status") == "bounded_loop_finished"
                and 0 <= integer(body.get("actual_turns")) <= 30
                and integer(body.get("next_sequence"), 1) > sequence)
    _, marker = _read_actual(after, reader, 65536)
    # The original protocol allows a 512 MiB response plus its envelope.
    # Normal installed calls record acceptance from the original in-memory row,
    # so subsequent guards use FileID/stat and never reread those large bodies.
    _, row = _read_actual(response, reader, 512 * 1024**2 + 65536)
    result = record(row.get("result"))
    request = record(row.get("request"))
    return (integer(request.get("sequence"), 1) == sequence
            and row.get("client_error") is None
            and result.get("result_type") == "complete" and result.get("is_error") is False
            and _same_path(text(marker.get("response")), response))


def _held_full_control(queue: object, root: Path, phase: str,
                       reader: BasisReaderV1) -> ExactRefV1 | None:
    held = _attribute(queue, "held_control")
    if held is None:
        return None
    name = text(held)
    need(phase == "ready" and re.fullmatch("[0-9]+-1-result[.]json", name) is not None,
         "only the existing ordinary FULL may hold control")
    path = root / "p37-requests" / name
    reference, row = _read_actual(path, reader, 16384)
    request = _request(row)
    need(request.get("command") == "full_loop" and request.get("tool") is None
         and integer(request["sequence"], 1) < integer(_attribute(queue, "next_sequence"), 1),
         "held control must be the actual consumed FULL request")
    inflight = root / "p37-queue" / f"{integer(request['sequence'], 1):04d}.json"
    # Ordinary FULL retains a separate control-only INFLIGHT while its own
    # generated Queue calls proceed through their unchanged per-tool guards.
    inflight = inflight.with_name("INFLIGHT-" + inflight.name)
    _, context = _read_actual(inflight, reader, 16384)
    need(context.get("control_only") is True and
         _json_bytes(context.get("request")) == _json_bytes(request),
         "actual ordinary FULL control-only holder")
    return reference


def _inflight_guard(root: Path, queue: object, request: JsonObject,
                    active: CurrentSavedRequestPermitV1 | None,
                    control: ExactRefV1 | None, reader: BasisReaderV1) -> None:
    sequence = integer(request["sequence"], 1)
    next_sequence = integer(_attribute(queue, "next_sequence"), 1)
    control_sequence: int | None = None
    if control is not None:
        control_sequence = integer(_small(reader, control, 16384).get("sequence"), 1)
    for path in (root / "p37-queue").glob("INFLIGHT-*.json"):
        match = re.fullmatch("INFLIGHT-([0-9]+)[.]json", path.name)
        need(match is not None, "unknown INFLIGHT identity")
        if match is None:
            raise ValueError("unreachable invalid INFLIGHT")
        number = int(match.group(1))
        need(number > 0, "positive INFLIGHT sequence")
        if control_sequence is not None and number == control_sequence:
            continue
        if active is not None and number == sequence:
            _, context = _read_actual(path, reader, 16384)
            if context.get("scope") == "cold-start-readiness-only":
                need(active.phase == "semantic" and request.get("tool") == SEMANTIC_TOOL
                     and integer(context.get("sequence"), 1) == sequence
                     and context.get("tool") == request.get("tool")
                     and record(context.get("arguments")) == record(request.get("arguments"))
                     and context.get("outer_sequence_consumed") is False,
                     "only this exact active startup request owns its INFLIGHT")
            else:
                flat = parse_current_saved_queue_tool_inflight_v1(context)
                _registered_permit(queue, active)
                request_file = root / "p37-requests" / f"{sequence:04d}-1-result.json"
                need(active.request_json == _json_bytes(request)
                     and flat.sequence == sequence == active.sequence
                     and flat.tool == request.get("tool")
                     and _json_bytes(flat.arguments) == _json_bytes(request.get("arguments"))
                     and Path(flat.request_file).is_absolute()
                     and _same_path(flat.request_file, request_file)
                     and path.name == f"INFLIGHT-{sequence:04d}.json",
                     "only the exact registered active request owns the original flat INFLIGHT")
                _, original_request = _read_actual(request_file, reader, 16384)
                need(_json_bytes(_request(original_request)) == active.request_json,
                     "active Queue INFLIGHT binds the actual immutable original request file")
            continue
        need(number < next_sequence and _settled(number, root, reader),
             "unsettled original INFLIGHT forbids another request")


def validate_current_saved_live_readiness_v1(
    *, queue: object, runtime_root: Path, expected_machine_id: str,
) -> CurrentSavedLiveReadinessV1:
    need(current_execution_machine_id_v1() == expected_machine_id,
         "live readiness belongs to the actual execution machine")
    _clean_flags(queue, runtime_root)
    epoch = _REQUEST_EPOCHS.get(id(queue))
    need(epoch is not None and epoch.queue is queue
         and epoch.machine_id == expected_machine_id and _same_path(epoch.root, runtime_root),
         "live readiness belongs to this once-bound Queue epoch")
    if epoch is None:
        raise ValueError("unreachable missing live Queue epoch")
    accepted = _INITIAL_WARM_ACCEPTANCES.get(id(queue))
    if accepted is None:
        warm = load_current_saved_warm_inputs_v1(
            runtime_root=runtime_root, expected_machine_id=expected_machine_id)
        accepted = _InitialWarmAcceptanceV1(queue, epoch, warm, _ISSUER)
        _INITIAL_WARM_ACCEPTANCES[id(queue)] = accepted
        return CurrentSavedLiveReadinessV1(
            "initial_warm", warm, warm.inputs.basis.checkpoint,
            warm.warm_proof.driver_identity, warm.inputs.basis.save_identity,
            tuple(ref for _, ref in warm.warm_proof.sources.items()))
    need(accepted.queue is queue and accepted.epoch is epoch and accepted.issuer is _ISSUER,
         "initial warm acceptance cannot be supplied or rebased by a caller")
    return _validate_same_epoch_continuation_v1(
        queue, accepted, runtime_root=runtime_root, reader=LocalBasisReaderV1())


def guard_current_saved_request_v1(
    queue: object, request: object, *, runtime_root: Path,
    active: CurrentSavedRequestPermitV1 | None = None,
) -> CurrentSavedRequestPermitV1:
    root = runtime_root.resolve(strict=True)
    row = _request(request)
    phase = _phase(queue)
    _clean_flags(queue, root)
    reader = LocalBasisReaderV1()
    config_ref, configuration = _read_actual(root / "ROOT-LAUNCH-CONFIG-C23-A15.json", reader)
    config = record(configuration.get("cold_attempt"))
    machine = text(config.get("machine_id"))
    need(machine == current_execution_machine_id_v1()
         and _same_path(text(config.get("runtime_root")), root), "actual current request machine/root")
    attempt, task = _nonce(config.get("attempt_nonce")), _nonce(config.get("task_nonce"))
    game_ref = _actual_ref(root / "ROOT-ACTUAL-GAME-LAUNCH-C23.json", reader, 65536)
    sdk_ref = _actual_ref(root / "ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json", reader, 65536)
    epoch = _REQUEST_EPOCHS.get(id(queue))
    need(epoch is not None and epoch.queue is queue and epoch.machine_id == machine
         and _same_path(epoch.root, root) and epoch.config_ref == config_ref
         and epoch.game_ref == game_ref and epoch.sdk_pair_ref == sdk_ref,
         "Queue request epoch was bound once and cannot drift")
    if epoch is None:
        raise ValueError("unreachable unbound request epoch")
    exact_read(reader, epoch.generations_ref, 65536)
    sequence = integer(row["sequence"], 1)
    current = integer(_attribute(queue, "next_sequence"), 1)
    encoded = _json_bytes(row)
    if active is None:
        need(sequence == current, "one current unused request sequence")
    else:
        _registered_permit(queue, active)
        need(active._issuer is _ISSUER and active.request_json == encoded
             and active.sequence == sequence and active.phase == phase
             and _same_path(active.runtime_root, root) and active.machine_id == machine
             and active.attempt_nonce == attempt and active.task_nonce == task
             and active.config_ref == config_ref and active.game_ref == game_ref
             and active.sdk_pair_ref == sdk_ref, "same-call permit, request, epoch, phase and source pins")
        need(current in (sequence, sequence + 1), "active call can consume only its own sequence")
    next_path = root / "NEXT-SEQUENCE-P37.json"
    if next_path.exists():
        _, next_row = _read_actual(next_path, reader, 16384)
        need(integer(next_row.get("next_sequence"), 1) == current, "actual NEXT equals current Queue")
        if "failed_request_registered_without_readmission" in next_row:
            need(next_row["failed_request_registered_without_readmission"] is False,
                 "failed request registration never grants readmission")
    else:
        need(phase == "semantic" and sequence == current
             and (active is not None or (_attribute(queue, "current_attempt") is None
                  and not any((root / "p37-queue").glob("INFLIGHT-*.json")))),
             "only the first same-call semantic may have no NEXT receipt")
    if phase != "ready":
        expected = SEMANTIC_TOOL if phase == "semantic" else CAPABILITIES_TOOL
        need(row.get("tool") == expected and row.get("arguments") == {}
             and row.get("command") is None, "fresh SEM then CAP; unknown phase never selects CAP")
        admission = record(record(_attribute(queue, "_normal_cold")).get("admission"))
        first_sequence = integer(admission.get("next_sequence"), 1)
        need(sequence == first_sequence + (1 if phase == "capabilities" else 0),
             "cold readiness consumes only its original SEM then CAP numbers")
        if phase == "capabilities":
            need(_settled(first_sequence, root, reader), "CAP follows real successful first SEM postcheck")
            _, accepted = _read_actual(
                root / "p37-queue" / f"{first_sequence:04d}-after-result.json", reader)
            need(accepted.get("actual_status") == "cold_readiness_verified",
                 "CAP requires original startup acceptance marker")
    control = _held_full_control(queue, root, phase, reader)
    if active is not None:
        need(active.control_ref == control, "ordinary FULL parent control cannot change")
    _inflight_guard(root, queue, row, active, control, reader)
    attempt_value = _attribute(queue, "current_attempt")
    if attempt_value is not None:
        previous = record(attempt_value)
        previous_request = record(previous.get("request"))
        previous_sequence = integer(previous_request.get("sequence"), 1)
        same_active = active is not None and previous_sequence == sequence
        need(same_active or _settled(previous_sequence, root, reader),
             "unsettled or failed previous attempt forbids a new call")
    if row.get("command") == "full_loop":
        need(phase == "ready" and _attribute(queue, "checkpoint_bootstrap_verified") is True
             and _attribute(queue, "capabilities_verified") is True
             and _attribute(queue, "cold_readiness_verified") is True,
             "FULL requires real accepted SEM and CAP")
        validate_current_saved_live_readiness_v1(
            queue=queue, runtime_root=root, expected_machine_id=machine)
    if active is not None:
        return active
    previous_state = _PERMIT_STATES.get(id(queue))
    if previous_state is not None and previous_state.queue is queue:
        previous_permit = previous_state.permit
        if previous_permit.request_json == encoded:
            need(not previous_state.revoked and previous_state.calls == 0
                 and previous_permit.phase == phase and previous_permit.config_ref == config_ref
                 and previous_permit.game_ref == game_ref and previous_permit.sdk_pair_ref == sdk_ref,
                 "a used or revoked request cannot acquire another permit")
            return previous_permit
    permit = CurrentSavedRequestPermitV1(
        str(root), machine, attempt, task, sequence, phase, encoded, config_ref,
        game_ref, sdk_ref, control, _ISSUER)
    _PERMIT_STATES[id(queue)] = _PermitStateV1(queue, permit)
    return permit


def submit_queue_readiness_request_v1(
    queue: object, request: object, *, runtime_root: Path,
    publish: Callable[[JsonObject], None],
) -> CurrentSavedRequestPermitV1:
    row = _request(request)
    need(row.get("tool") in (SEMANTIC_TOOL, CAPABILITIES_TOOL)
         and row.get("arguments") == {} and row.get("command") is None,
         "only one new read-only readiness request")
    permit = guard_current_saved_request_v1(queue, row, runtime_root=runtime_root)
    publish(json_object(json.loads(permit.request_json)))
    return permit


class CurrentSavedToolResultV1(Protocol):
    def model_dump(self, *, mode: Literal["json"]) -> JsonObject: ...


class CurrentSavedToolCallV1(Protocol):
    async def __call__(self, tool: str, arguments: JsonObject,
                       budget: float) -> CurrentSavedToolResultV1: ...


class GuardedCurrentSavedSessionV1:
    def __init__(
        self, queue: object, request: object, *, runtime_root: Path,
        call: CurrentSavedToolCallV1, permit: CurrentSavedRequestPermitV1,
    ) -> None:
        self._queue = queue
        self._request = _request(request)
        self._root = runtime_root
        self._call = call
        self._permit = permit

    async def call_tool(
        self, name: str, arguments: JsonObject, *, read_timeout_seconds: float,
    ) -> CurrentSavedToolResultV1:
        need(name == self._request.get("tool")
             and _json_bytes(arguments) == _json_bytes(self._request.get("arguments")),
             "session transport must match its exact current permitted tool and arguments")
        need(type(read_timeout_seconds) in (int, float) and read_timeout_seconds > 0,
             "positive actual request timeout")
        state = _registered_permit(self._queue, self._permit)
        try:
            need(not state.in_transport, "one actual transport at a time")
            if state.calls:
                _loading_retry_grant(state, self._root)
            guard_current_saved_request_v1(
                self._queue, self._request, runtime_root=self._root, active=self._permit)
            _clean_flags(self._queue, self._root)
            state.calls += 1
            state.in_transport = True
            try:
                result = await self._call(name, arguments, float(read_timeout_seconds))
            finally:
                state.in_transport = False
            state.last_result_json = _json_bytes(result.model_dump(mode="json"))
            return result
        except BaseException:
            state.revoked = True
            raise


@dataclass
class _PermitStateV1:
    queue: object
    permit: CurrentSavedRequestPermitV1
    calls: int = 0
    in_transport: bool = False
    revoked: bool = False
    last_result_json: bytes | None = None


@dataclass(frozen=True)
class _RequestEpochV1:
    queue: object
    root: str
    machine_id: str
    config_ref: ExactRefV1
    game_ref: ExactRefV1
    sdk_pair_ref: ExactRefV1
    generations_ref: ExactRefV1
    startup_ref: ExactRefV1


_PERMIT_STATES: dict[int, _PermitStateV1] = {}
_REQUEST_EPOCHS: dict[int, _RequestEpochV1] = {}


def _identity_tuple(value: object) -> tuple[int, str]:
    row = record(value)
    birth = row.get("creation_filetime")
    if isinstance(birth, str):
        need(re.fullmatch("0|[1-9][0-9]*", birth) is not None, "canonical FILETIME string")
        normalized = birth
    else:
        need(type(birth) is int, "legacy Python-only FILETIME must be exact integer")
        if type(birth) is not int:
            raise ValueError("exact legacy Python FILETIME integer required")
        need(0 < birth <= 18446744073709551615, "uint64 Python FILETIME")
        normalized = str(birth)
    need(0 < int(normalized) <= 18446744073709551615, "uint64 FILETIME")
    return integer(row.get("pid"), 1, 4294967295), normalized


def _sdk_identities(value: object) -> tuple[tuple[str, int, str, str], ...]:
    process_rows = rows(record(value).get("processes"))
    result: list[tuple[str, int, str, str]] = []
    for item in process_rows:
        process = record(item)
        pid, birth = _identity_tuple(process)
        result.append((text(process.get("role")), pid, birth, text(process.get("executable"))))
    need(len(result) == 2 and {item[0] for item in result} ==
         {"sdk_queue", "sdk_application"}, "the two actual retained SDK roles")
    need(len({(item[1], item[2]) for item in result}) == 2, "two distinct SDK process generations")
    return tuple(sorted(result))


def bind_current_saved_request_epoch_v1(
    queue: object, *, runtime_root: Path, expected_machine_id: str,
) -> None:
    root = runtime_root.resolve(strict=True)
    need(expected_machine_id == current_execution_machine_id_v1(),
         "current request epoch actual machine")
    _clean_flags(queue, root)
    need(_phase(queue) == "semantic", "bind request epoch before first semantic transport")
    reader = LocalBasisReaderV1()
    config_ref, configuration = _read_actual(root / "ROOT-LAUNCH-CONFIG-C23-A15.json", reader)
    config = record(configuration.get("cold_attempt"))
    need(config.get("machine_id") == expected_machine_id
         and _same_path(text(config.get("runtime_root")), root), "qualified config epoch")
    _nonce(config.get("attempt_nonce")); _nonce(config.get("task_nonce"))
    game_ref, launch = _read_actual(root / "ROOT-ACTUAL-GAME-LAUNCH-C23.json", reader)
    cold = record(_attribute(queue, "_normal_cold"))
    admission = record(cold.get("admission"))
    identity = _identity_tuple(launch)
    need(identity == _identity_tuple(_attribute(queue, "launch"))
         == _identity_tuple(admission.get("new_Game")),
         "retained Queue and admitted actual Game epoch")
    sdk_ref, pair = _read_actual(root / "ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json", reader)
    generations_ref, generations = _read_actual(
        root / "ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37C23.json", reader)
    need(_sdk_identities(pair) == _sdk_identities(generations),
         "pinned SDK pair equals the actual retained factory generations")
    epoch = _RequestEpochV1(queue, str(root), expected_machine_id,
                            config_ref, game_ref, sdk_ref, generations_ref,
                            _actual_ref(root / "startup_readiness_v1.py", reader, 65536))
    previous = _REQUEST_EPOCHS.get(id(queue))
    need(previous is None or previous == epoch, "request epoch cannot rebind after source drift")
    _REQUEST_EPOCHS[id(queue)] = epoch


def _registered_permit(queue: object, permit: CurrentSavedRequestPermitV1) -> _PermitStateV1:
    state = _PERMIT_STATES.get(id(queue))
    need(state is not None and state.queue is queue and state.permit is permit
         and not state.revoked, "one registered same-queue permit object")
    if state is None:
        raise ValueError("unreachable missing registered permit")
    return state


def _loading_retry_grant(state: _PermitStateV1, root: Path) -> None:
    need(state.permit.phase == "semantic" and state.calls > 0
         and state.last_result_json is not None, "only a completed original loading attempt may retry")
    reader = LocalBasisReaderV1()
    stem = f"READINESS-{state.permit.sequence:04d}-{state.calls:06d}"
    response = root / "p37-queue" / (stem + "-result.json")
    marker_path = root / "p37-queue" / (stem + "-loading.json")
    _, marker = _read_actual(marker_path, reader, 16384)
    _, row = _read_actual(response, reader, _MAX_SMALL)
    need(_original_exact_loading_v1(row, state.queue, reader),
         "actual original exact_loading classifier must grant a retry")
    need(marker.get("status") == "startup_readiness_unavailable"
         and marker.get("outer_sequence_consumed") is False
         and integer(marker.get("new_business_credit")) == 0
         and marker.get("retry_only_tool") == SEMANTIC_TOOL
         and _same_path(text(marker.get("source_response")), response)
         and integer(row.get("startup_readiness_attempt"), 1) == state.calls
         and _json_bytes(row.get("request")) == state.permit.request_json
         and _json_bytes(row.get("result")) == state.last_result_json
         and row.get("client_error") is None,
         "original exact_loading branch must grant this next read-only attempt")


@dataclass(frozen=True)
class CurrentSavedReadinessSubmissionV1:
    machine_id: str
    observed_at_utc: str
    runtime_root: str
    request_ref: ExactRefV1
    basis_ref: ExactRefV1
    config_ref: ExactRefV1

    def to_wire(self) -> JsonObject:
        return {
            "schema": "xar.current-saved-readiness-submission/v1",
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "runtime_root": self.runtime_root, "request_ref": self.request_ref.to_wire(),
            "basis_ref": self.basis_ref.to_wire(), "config_ref": self.config_ref.to_wire(),
            "ordinary_cycle_credit": 0, "game_day_credit": 0,
            "original_actions_replayed": False,
        }


def validate_current_saved_readiness_request_v1(
    request: object, *, runtime_root: Path, expected_machine_id: str,
) -> tuple[ExactRefV1, ExactRefV1]:
    """Root publisher: derive readiness from persisted evidence, without a Queue stand-in."""
    import os
    root = runtime_root.resolve(strict=True)
    need(expected_machine_id == current_execution_machine_id_v1(),
         "external readiness publisher actual machine")
    row = _request(request)
    need(set(row) == {"sequence", "tool", "arguments"}
         and row.get("tool") in (SEMANTIC_TOOL, CAPABILITIES_TOOL)
         and row.get("arguments") == {}, "one exact read-only startup request")
    _clean_flags(None, root)
    reader = LocalBasisReaderV1()
    _, entry = _read_actual(root / "ROOT-CURRENT-SAVED-INPUTS01.json", reader, 16384)
    need(entry.get("schema") == "xar.current-saved-cold-inputs/v1"
         and entry.get("machine_id") == expected_machine_id, "actual saved-input entry")
    basis_ref = parse_ref(entry.get("basis_ref"))
    basis = decode_current_saved_basis_v1(
        exact_read(reader, basis_ref, 65536), expected_machine_id=expected_machine_id)
    config_ref, configuration = _read_actual(root / "ROOT-LAUNCH-CONFIG-C23-A15.json", reader)
    config = record(configuration.get("cold_attempt"))
    need(config.get("machine_id") == expected_machine_id
         and _same_path(text(config.get("runtime_root")), root)
         and parse_ref(config.get("basis_ref")) == basis_ref
         and parse_ref(config.get("validation_ref")) == parse_ref(entry.get("validation_ref")),
         "publisher current config/basis/qualification binding")
    _nonce(config.get("attempt_nonce")); _nonce(config.get("task_nonce"))
    next_path = root / "NEXT-SEQUENCE-P37.json"
    next_sequence = basis.next_sequence
    if next_path.exists():
        _, next_row = _read_actual(next_path, reader, 16384)
        next_sequence = integer(next_row.get("next_sequence"), 1)
        if "failed_request_registered_without_readmission" in next_row:
            need(next_row["failed_request_registered_without_readmission"] is False,
                 "failed sequence registration does not grant external readmission")
    sequence = integer(row["sequence"], 1)
    need(sequence == next_sequence, "external request requires actual current unused NEXT")
    first_after = root / "p37-queue" / f"{basis.next_sequence:04d}-after-result.json"
    if row["tool"] == SEMANTIC_TOOL:
        need(sequence == basis.next_sequence and not first_after.exists(),
             "only untouched first SEM may be published")
    else:
        need(sequence == basis.next_sequence + 1 and _settled(basis.next_sequence, root, reader),
             "CAP requires settled original first SEM postcheck")
        _, accepted = _read_actual(first_after, reader, 65536)
        need(accepted.get("tool") == SEMANTIC_TOOL
             and accepted.get("actual_status") == "cold_readiness_verified",
             "CAP requires the original startup accepted marker")
    for path in (root / "p37-queue").glob("INFLIGHT-*.json"):
        match = re.fullmatch("INFLIGHT-([0-9]+)[.]json", path.name)
        need(match is not None, "known original INFLIGHT sequence")
        if match is None:
            raise ValueError("unreachable malformed INFLIGHT")
        number = int(match.group(1))
        need(number < sequence and _settled(number, root, reader),
             "external publisher cannot bypass unresolved INFLIGHT")
    response = root / "p37-responses" / f"{sequence:04d}-1-result.json"
    need(not response.exists(), "original response cannot be replayed")
    return basis_ref, config_ref


def submit_readiness_request_v1(
    request: object, *, runtime_root: Path, expected_machine_id: str,
) -> CurrentSavedReadinessSubmissionV1:
    """Publish a complete create-only request after checking persisted readiness."""
    import os
    import uuid
    root = runtime_root.resolve(strict=True)
    row = _request(request)
    basis_ref, config_ref = validate_current_saved_readiness_request_v1(
        row, runtime_root=root, expected_machine_id=expected_machine_id)
    sequence = integer(row["sequence"], 1)
    destination = root / "p37-requests" / f"{sequence:04d}-1-result.json"
    need(destination.parent.is_dir() and destination.resolve().is_relative_to(root),
         "existing exact owned inbox")
    for directory in (root, destination.parent):
        need(not directory.is_symlink()
             and not (getattr(directory.stat(), "st_file_attributes", 0) & 1024),
             "no reparse publication path")
    payload = _json_bytes(row) + b"\n"
    need(len(payload) <= 16384 and not destination.exists() and not destination.is_symlink(),
         "bounded unused startup request")
    pending = destination.with_name("." + destination.name + "." + uuid.uuid4().hex + ".pending")
    reader = LocalBasisReaderV1()
    owned_inode: tuple[int, int] | None = None
    try:
        with pending.open("xb") as stream:
            identity = os.fstat(stream.fileno())
            owned_inode = (identity.st_dev, identity.st_ino)
            need(stream.write(payload) == len(payload), "complete pending request")
            stream.flush(); os.fsync(stream.fileno())
        need(validate_current_saved_readiness_request_v1(
            row, runtime_root=root, expected_machine_id=expected_machine_id)
             == (basis_ref, config_ref), "request evidence remained unchanged before publication")
        os.link(pending, destination)
        need(os.path.samefile(pending, destination), "published request shares pending FileID")
        reference = ExactRefV1(str(destination), len(payload), hashlib.sha256(payload).hexdigest())
        exact_read(reader, reference, 16384)
    finally:
        if owned_inode is not None and pending.exists():
            actual = pending.stat()
            need(not pending.is_symlink() and not (getattr(actual, "st_file_attributes", 0) & 1024)
                 and (actual.st_dev, actual.st_ino) == owned_inode,
                 "cleanup only this call's owned pending file")
            pending.unlink()
    return CurrentSavedReadinessSubmissionV1(
        expected_machine_id, datetime.now(timezone.utc).isoformat(), str(root),
        reference, basis_ref, config_ref)


@dataclass(frozen=True)
class HistoricalReplayCaseV1:
    case: Literal["missing_anchor", "original_anchor_copy"]
    phase_after: Literal["semantic", "capabilities"]
    local_recorded_reply_calls: int
    exception_type: str | None
    exception_message: str | None
    score_observer_calls: int
    anchor_copy_present: bool

    def to_wire(self) -> JsonObject:
        return {
            "case": self.case, "phase_after": self.phase_after,
            "local_recorded_reply_calls": self.local_recorded_reply_calls,
            "exception_type": self.exception_type, "exception_message": self.exception_message,
            "score_observer_calls": self.score_observer_calls,
            "anchor_copy_present": self.anchor_copy_present,
        }


@dataclass(frozen=True)
class HistoricalPreservedEvidenceV1:
    role: Literal["original_halt", "original_inflight", "first_exception"]
    before: ExactRefV1
    after: ExactRefV1

    def to_wire(self) -> JsonObject:
        return {"role": self.role, "before": self.before.to_wire(), "after": self.after.to_wire()}


@dataclass(frozen=True)
class HistoricalBlockedFollowupV1:
    kind: Literal["SEM", "CAP", "AUTO", "FULL"]
    request: JsonObject
    before_local_recorded_reply_calls: int
    after_local_recorded_reply_calls: int
    preserved: tuple[HistoricalPreservedEvidenceV1, ...]

    def to_wire(self) -> JsonObject:
        return {
            "kind": self.kind, "request": self.request,
            "before_local_recorded_reply_calls": self.before_local_recorded_reply_calls,
            "after_local_recorded_reply_calls": self.after_local_recorded_reply_calls,
            "preserved": [item.to_wire() for item in self.preserved],
        }



@dataclass(frozen=True)
class CurrentSavedColdQueueReplayV1:
    governance_ref: ExactRefV1
    receiver_ref: ExactRefV1
    capability_source_ref: ExactRefV1
    governance_resume: JsonObject
    completed_cycles: int

    def to_wire(self) -> JsonObject:
        return {
            "schema": "xar.current-saved-complete-cold-queue-replay/v1",
            "governance_ref": self.governance_ref.to_wire(),
            "receiver_ref": self.receiver_ref.to_wire(),
            "capability_source_ref": self.capability_source_ref.to_wire(),
            "governance_resume": self.governance_resume,
            "completed_cycles": self.completed_cycles,
            "phase_after": "ready", "recorded_sem_calls": 1, "recorded_cap_calls": 1,
            "original_postchecks": 2, "original_persist_executed": True,
            "original_classifier_loader_executed": True,
            "bound_after_original_persistence": True, "raw_unprojected_failure_reproduced": True,
            "closed_inputs_reloaded_after_sem": False,
            "actual_rpc_calls": 0, "ordinary_cycle_credit": 0, "game_day_credit": 0,
            "fresh_native_readiness_claimed": False,
        }


_A33_CAP_REF = ExactRefV1(
    "D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/"
    "robert30-v20261019-campaign01/runtime-a33/p37-responses/11378-1-result.json",
    62772, "e1dd6791c613468979f1fceb0d286c6ebb579be6869767f0a0530374b0cf9f64")


def parse_current_saved_cold_queue_replay_v1(value: object) -> CurrentSavedColdQueueReplayV1:
    row = record(value, {
        "schema", "governance_ref", "receiver_ref", "capability_source_ref",
        "governance_resume", "completed_cycles", "phase_after", "recorded_sem_calls",
        "recorded_cap_calls", "original_postchecks", "original_persist_executed",
        "bound_after_original_persistence", "raw_unprojected_failure_reproduced",
        "original_classifier_loader_executed",
        "closed_inputs_reloaded_after_sem", "actual_rpc_calls", "ordinary_cycle_credit",
        "game_day_credit", "fresh_native_readiness_claimed"})
    need(row["schema"] == "xar.current-saved-complete-cold-queue-replay/v1"
         and row["phase_after"] == "ready", "complete offline cold receiver contract")
    for key in ("original_persist_executed", "original_classifier_loader_executed", "bound_after_original_persistence",
                "raw_unprojected_failure_reproduced"):
        need(row[key] is True, "original cold producer executed: " + key)
    for key in ("closed_inputs_reloaded_after_sem", "fresh_native_readiness_claimed"):
        need(row[key] is False, "offline cold replay does not grant live identity")
    for key in ("actual_rpc_calls", "ordinary_cycle_credit", "game_day_credit"):
        need(integer(row[key]) == 0, "offline cold replay zero: " + key)
    need(integer(row["recorded_sem_calls"]) == integer(row["recorded_cap_calls"]) == 1
         and integer(row["original_postchecks"]) == 2, "exact SEM and CAP postchecks")
    cycles = integer(row["completed_cycles"])
    resume = record(row["governance_resume"],
                    {"state", "pending_focus", "completed_cycles", "pending_cycle"})
    need(resume["pending_cycle"] is None and integer(resume["completed_cycles"]) == cycles,
         "settled governance cycle identity")
    for key in ("state", "pending_focus"):
        need(resume[key] is None or isinstance(resume[key], dict), "nullable governance object")
    capability = parse_ref(row["capability_source_ref"])
    need(capability == _A33_CAP_REF, "unaltered historical CAP11378 provenance")
    return CurrentSavedColdQueueReplayV1(parse_ref(row["governance_ref"]),
        parse_ref(row["receiver_ref"]), capability, json_object(resume), cycles)

@dataclass(frozen=True)
class HistoricalStartupDispatchReplayV1:
    fixture_ref: ExactRefV1
    harness_ref: ExactRefV1
    core_source_ref: ExactRefV1
    semantic_postcheck_ref: ExactRefV1
    historical_subject_machine_id: str
    execution_machine_id: str
    observed_at_utc: str
    historical_sequence: int
    current_next_sequence: int
    cases: tuple[HistoricalReplayCaseV1, ...]
    blocked_followups: tuple[HistoricalBlockedFollowupV1, ...]
    cold_queue_contract: CurrentSavedColdQueueReplayV1
    peak_allocation_upper_bytes: int

    def to_wire(self) -> JsonObject:
        return {
            "schema": "xar.current-saved-historical-startup-dispatch-replay/v2",
            "fixture_ref": self.fixture_ref.to_wire(), "harness_ref": self.harness_ref.to_wire(),
            "core_source_ref": self.core_source_ref.to_wire(),
            "semantic_postcheck_ref": self.semantic_postcheck_ref.to_wire(),
            "historical_subject_machine_id": self.historical_subject_machine_id,
            "execution_machine_id": self.execution_machine_id,
            "observed_at_utc": self.observed_at_utc,
            "historical_sequence": self.historical_sequence,
            "current_next_sequence": self.current_next_sequence,
            "cases": [item.to_wire() for item in self.cases],
            "blocked_followups": [item.to_wire() for item in self.blocked_followups],
            "cold_queue_contract": self.cold_queue_contract.to_wire(),
            "factory_executed": True, "dispatch_installed": True, "startup_executed": True,
            "check_after_executed": True, "score_observer_executed": True,
            "original_inputs_unchanged": True, "fixture_cleaned": True,
            "actual_rpc_calls": 0, "sdk_processes_started": 0, "game_processes_started": 0,
            "tasks_started": 0, "ordinary_cycle_credit": 0, "game_day_credit": 0,
            "canonical_score_writes": 0,
            "peak_allocation_upper_bytes": self.peak_allocation_upper_bytes,
        }


def _parse_replay_case(value: object) -> HistoricalReplayCaseV1:
    row = record(value)
    need(set(row) == {"case", "phase_after", "local_recorded_reply_calls", "exception_type",
                      "exception_message", "score_observer_calls", "anchor_copy_present"},
         "exact historical replay case fields")
    calls = integer(row["local_recorded_reply_calls"], 1)
    observed = integer(row["score_observer_calls"], 1)
    need(type(row["anchor_copy_present"]) is bool, "exact anchor-presence boolean")
    if row["case"] == "missing_anchor":
        need(row["phase_after"] == "semantic" and row["anchor_copy_present"] is False
             and row["exception_type"] == "ValueError"
             and row["exception_message"] == "founding score anchor requires actual paused1066 frame",
             "real original missing-anchor failure")
        return HistoricalReplayCaseV1("missing_anchor", "semantic", calls, "ValueError",
                                      text(row["exception_message"]), observed, False)
    need(row["case"] == "original_anchor_copy" and row["phase_after"] == "capabilities"
         and row["anchor_copy_present"] is True and row["exception_type"] is None
         and row["exception_message"] is None, "real original-anchor postcheck success")
    return HistoricalReplayCaseV1(
        "original_anchor_copy", "capabilities", calls, None, None, observed, True)


def _parse_preserved(value: object) -> HistoricalPreservedEvidenceV1:
    row = record(value)
    need(set(row) == {"role", "before", "after"}, "exact retained historical evidence")
    before, after = parse_ref(row["before"]), parse_ref(row["after"])
    need(before == after, "original halt, INFLIGHT and first exception remain byte-identical")
    if row["role"] == "original_halt":
        return HistoricalPreservedEvidenceV1("original_halt", before, after)
    if row["role"] == "original_inflight":
        return HistoricalPreservedEvidenceV1("original_inflight", before, after)
    need(row["role"] == "first_exception", "one explicit retained evidence role")
    return HistoricalPreservedEvidenceV1("first_exception", before, after)


def _parse_blocked_followup(value: object) -> HistoricalBlockedFollowupV1:
    row = record(value)
    need(set(row) == {"kind", "request", "before_local_recorded_reply_calls",
                      "after_local_recorded_reply_calls", "preserved"},
         "exact blocked followup fields")
    before = integer(row["before_local_recorded_reply_calls"])
    after = integer(row["after_local_recorded_reply_calls"])
    need(before == after, "failed postcheck permits zero additional transport calls")
    request = _request(row["request"])
    preserved = tuple(_parse_preserved(item) for item in rows(row["preserved"]))
    need(len(preserved) == 3 and {item.role for item in preserved} ==
         {"original_halt", "original_inflight", "first_exception"}, "all original failure evidence retained")
    if row["kind"] == "FULL":
        need(request.get("command") == "full_loop", "actual original FULL dispatch request")
        return HistoricalBlockedFollowupV1("FULL", request, before, after, preserved)
    if row["kind"] == "SEM":
        need(request.get("tool") == SEMANTIC_TOOL, "actual SEM followup")
        return HistoricalBlockedFollowupV1("SEM", request, before, after, preserved)
    if row["kind"] == "CAP":
        need(request.get("tool") == CAPABILITIES_TOOL, "actual CAP followup")
        return HistoricalBlockedFollowupV1("CAP", request, before, after, preserved)
    need(row["kind"] == "AUTO" and request.get("tool") == "ck3_auto_turn", "actual ordinary AUTO followup")
    return HistoricalBlockedFollowupV1("AUTO", request, before, after, preserved)


def parse_historical_startup_dispatch_replay_v1(value: object) -> HistoricalStartupDispatchReplayV1:
    row = record(value)
    positive = {
        "factory_executed", "dispatch_installed", "startup_executed", "check_after_executed",
        "score_observer_executed", "original_inputs_unchanged", "fixture_cleaned",
    }
    zero = {"actual_rpc_calls", "sdk_processes_started", "game_processes_started", "tasks_started",
            "ordinary_cycle_credit", "game_day_credit", "canonical_score_writes"}
    expected = positive | zero | {
        "schema", "fixture_ref", "harness_ref", "core_source_ref", "semantic_postcheck_ref",
        "historical_subject_machine_id", "execution_machine_id", "observed_at_utc",
        "historical_sequence", "current_next_sequence", "cases", "blocked_followups",
        "peak_allocation_upper_bytes", "cold_queue_contract",
    }
    need(set(row) == expected and row["schema"] ==
         "xar.current-saved-historical-startup-dispatch-replay/v2", "exact full historical replay contract")
    for name in positive:
        need(row[name] is True, "actual original path executed: " + name)
    for name in zero:
        need(integer(row[name]) == 0, "offline historical replay zero: " + name)
    observed = text(row["observed_at_utc"]); utc(observed)
    historical, current = integer(row["historical_sequence"], 1), integer(row["current_next_sequence"], 1)
    need(historical < current, "historical and current request epochs are distinct")
    cases = tuple(_parse_replay_case(item) for item in rows(row["cases"]))
    need(len(cases) == 2 and [item.case for item in cases] ==
         ["missing_anchor", "original_anchor_copy"], "both real original-score outcomes")
    blocked = tuple(_parse_blocked_followup(item) for item in rows(row["blocked_followups"]))
    need(len(blocked) == 4 and {item.kind for item in blocked} == {"SEM", "CAP", "AUTO", "FULL"},
         "postcheck failure blocks all four production followups")
    peak = integer(row["peak_allocation_upper_bytes"], 1)
    need(peak <= 524288, "approved finite isolated replay allocation")
    return HistoricalStartupDispatchReplayV1(
        parse_ref(row["fixture_ref"]), parse_ref(row["harness_ref"]),
        parse_ref(row["core_source_ref"]), parse_ref(row["semantic_postcheck_ref"]),
        text(row["historical_subject_machine_id"]), text(row["execution_machine_id"]),
        observed, historical, current, cases, blocked,
        parse_current_saved_cold_queue_replay_v1(row["cold_queue_contract"]), peak)


def _full_historical_replay(
    reference: ExactRefV1, plan: ColdPlanV1, quote: ColdQuoteV1,
    core_ref: ExactRefV1, reader: BasisReaderV1,
) -> tuple[HistoricalStartupDispatchReplayV1, HistoricalSemanticReplayV1]:
    full = parse_historical_startup_dispatch_replay_v1(_small(reader, reference, 131072))
    need(full.execution_machine_id == current_execution_machine_id_v1()
         and (full.core_source_ref.bytes, full.core_source_ref.sha256) ==
         (core_ref.bytes, core_ref.sha256), "full replay executed with these exact core bytes")
    exact_read(reader, full.core_source_ref, 147456)
    exact_read(reader, full.harness_ref, 131072)
    fixture = _small(reader, full.fixture_ref, 135168)
    need(fixture.get("schema") == "xar.current-saved-historical-sem11373-fixture/v1"
         and fixture.get("historical_subject_machine_id") == full.historical_subject_machine_id
         and fixture.get("fresh_native_qualification") is False
         and fixture.get("historical_payloads_modified") is False,
         "source-pinned immutable historical fixture identity")
    core_sources = [row.source_ref for row in plan.source_rows
                    if Path(row.relative_path).name == _CORE_NAME]
    need(len(core_sources) == 1, "one approved canonical core source")
    canonical = Path(core_sources[0].path).parent
    need(_same_path(full.harness_ref.path,
                    canonical / "test_current_saved_campaign_preflight_v1.py")
         and _same_path(full.fixture_ref.path,
                        canonical / "test_data/current_saved_sem11373_postcheck_v1.json"),
         "full replay uses this public harness and repository corpus")
    original = _archive_historical_replay_v1(reference, full, fixture, plan, quote, reader)
    basis = decode_current_saved_basis_v1(exact_read(reader, plan.basis_ref, 65536),
                                         expected_machine_id=plan.machine_id)
    need(full.historical_sequence == original.historical_sequence
         and full.current_next_sequence == basis.next_sequence,
         "full historical original sequence and current saved-basis sequence")
    contract = full.cold_queue_contract
    from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
        project_current_saved_governance_resume_v1)
    actual_governance = _small(reader, basis.refs.governance)
    projected = project_current_saved_governance_resume_v1(
        actual_governance, expected_completed_cycles=basis.completed_cycles)
    receiver = [row for row in quote.files if row.relative_path == "root_p37c23_cold_resume.py"]
    need(len(receiver) == 1 and contract.receiver_ref ==
         ExactRefV1(receiver[0].path, receiver[0].bytes, receiver[0].sha256)
         and contract.governance_ref == basis.refs.governance
         and contract.completed_cycles == basis.completed_cycles
         and _json_bytes(contract.governance_resume) == _json_bytes(projected.to_wire()),
         "complete cold replay binds the actual raw governance and final quoted receiver")
    return full, original


@dataclass(frozen=True)
class CurrentSavedPreparedV1:
    machine_id: str
    runtime_root: str
    observed_at_utc: str
    review_at_utc: str
    attempt_nonce: str
    task_nonce: str
    basis_ref: ExactRefV1
    validation_ref: ExactRefV1
    plan_ref: ExactRefV1
    quote_ref: ExactRefV1
    preflight_ref: ExactRefV1

    def to_wire(self) -> JsonObject:
        return {
            "schema": "xar.current-saved-prepared/v1",
            "stage": "OFFLINE_CONTRACT_PREPARED", "machine_id": self.machine_id,
            "runtime_root": self.runtime_root, "observed_at_utc": self.observed_at_utc,
            "review_at_utc": self.review_at_utc,
            "attempt_nonce": self.attempt_nonce, "task_nonce": self.task_nonce,
            "basis_ref": self.basis_ref.to_wire(), "validation_ref": self.validation_ref.to_wire(),
            "plan_ref": self.plan_ref.to_wire(), "quote_ref": self.quote_ref.to_wire(),
            "preflight_ref": self.preflight_ref.to_wire(),
            "fresh_native_qualification": False, "full_loop_permitted": False,
            "ordinary_cycle_credit": 0, "game_day_credit": 0, "original_actions_replayed": False,
        }


def parse_current_saved_prepared_v1(value: object) -> CurrentSavedPreparedV1:
    row = record(value)
    need(set(row) == {
        "schema", "stage", "machine_id", "runtime_root", "observed_at_utc", "review_at_utc",
        "attempt_nonce", "task_nonce", "basis_ref", "validation_ref", "plan_ref", "quote_ref",
        "preflight_ref", "fresh_native_qualification", "full_loop_permitted",
        "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed",
    } and row["schema"] == "xar.current-saved-prepared/v1"
         and row["stage"] == "OFFLINE_CONTRACT_PREPARED", "exact Prepared-last contract")
    need(row["fresh_native_qualification"] is False and row["full_loop_permitted"] is False
         and row["original_actions_replayed"] is False
         and integer(row["ordinary_cycle_credit"]) == 0
         and integer(row["game_day_credit"]) == 0, "Prepared does not grant live or business credit")
    observed, review = text(row["observed_at_utc"]), text(row["review_at_utc"])
    utc(observed); utc(review)
    need(_timepoint(observed) < _timepoint(review), "Prepared observed before its actual review boundary")
    runtime = text(row["runtime_root"])
    need(Path(runtime).is_absolute(), "absolute actual Prepared runtime root")
    return CurrentSavedPreparedV1(
        text(row["machine_id"]), runtime, observed, review,
        _nonce(row["attempt_nonce"]), _nonce(row["task_nonce"]),
        parse_ref(row["basis_ref"]), parse_ref(row["validation_ref"]),
        parse_ref(row["plan_ref"]), parse_ref(row["quote_ref"]), parse_ref(row["preflight_ref"]))


def build_current_saved_prepared_v1(
    preflight: CurrentSavedCampaignPreflightV1, preflight_ref: ExactRefV1, *,
    reader: BasisReaderV1,
) -> CurrentSavedPreparedV1:
    actual = parse_current_saved_campaign_preflight_v1(_small(reader, preflight_ref))
    need(actual == preflight, "Prepared pins actual serialized completed preflight")
    plan = parse_plan_v1(_small(reader, preflight.plan_ref))
    need(plan.machine_id == preflight.machine_id == current_execution_machine_id_v1()
         and _same_path(plan.runtime_root, preflight.runtime_root)
         and plan.basis_ref == preflight.basis_ref and plan.validation_ref == preflight.validation_ref
         and plan.attempt_nonce == preflight.attempt_nonce and plan.task_nonce == preflight.task_nonce,
         "Prepared actual Plan and qualification binding")
    need(datetime.now(timezone.utc) < _timepoint(plan.review_at_utc), "Prepared actual review has not expired")
    result = CurrentSavedPreparedV1(
        preflight.machine_id, preflight.runtime_root, datetime.now(timezone.utc).isoformat(),
        plan.review_at_utc, preflight.attempt_nonce, preflight.task_nonce,
        preflight.basis_ref, preflight.validation_ref, preflight.plan_ref, preflight.quote_ref, preflight_ref)
    need(parse_current_saved_prepared_v1(json.loads(_json_bytes(result.to_wire()))) == result,
         "Prepared actual serialized roundtrip")
    return result


def verify_current_saved_prepared_v1(
    *, runtime_root: Path, expected_machine_id: str, expected_attempt_nonce: str,
    expected_task_nonce: str, reader: BasisReaderV1,
) -> CurrentSavedPreparedV1:
    need(current_execution_machine_id_v1() == expected_machine_id,
         "pre-Game Prepared validation actual execution machine")
    reference = _actual_ref(runtime_root / "ROOT-CURRENT-SAVED-PREPARED01.json", reader, 65536)
    prepared = parse_current_saved_prepared_v1(_small(reader, reference, 65536))
    need(prepared.machine_id == expected_machine_id
         and _same_path(prepared.runtime_root, runtime_root)
         and prepared.attempt_nonce == _nonce(expected_attempt_nonce)
         and prepared.task_nonce == _nonce(expected_task_nonce)
         and datetime.now(timezone.utc) < _timepoint(prepared.review_at_utc),
         "actual current Prepared machine/root/nonces/review")
    preflight = verify_current_saved_preflight_receipt_v1(
        prepared.preflight_ref, plan_ref=prepared.plan_ref, quote_ref=prepared.quote_ref,
        runtime_root=runtime_root, expected_machine_id=expected_machine_id,
        expected_attempt_nonce=expected_attempt_nonce, expected_task_nonce=expected_task_nonce,
        reader=reader)
    need(prepared.basis_ref == preflight.basis_ref
         and prepared.validation_ref == preflight.validation_ref,
         "Prepared references the exact current validated saved inputs")
    return prepared


def _timepoint(value: str) -> datetime:
    return datetime.fromisoformat(utc(value).replace("Z", "+00:00"))


def check_current_saved_tool_v1(
    queue: object, tool: object, arguments: object, *, runtime_root: Path,
) -> None:
    active = _attribute(queue, "_current_saved_active_permit_v1")
    if active is None:
        request: JsonObject = {
            "sequence": integer(_attribute(queue, "next_sequence"), 1),
            "tool": text(tool), "arguments": json_object(arguments),
        }
        guard_current_saved_request_v1(queue, request, runtime_root=runtime_root)
        return
    need(isinstance(active, CurrentSavedRequestPermitV1), "typed active request permit")
    if not isinstance(active, CurrentSavedRequestPermitV1):
        raise ValueError("unreachable invalid active request permit")
    _registered_permit(queue, active)
    original = _request(json.loads(active.request_json))
    need(original.get("tool") == text(tool)
         and _json_bytes(original.get("arguments")) == _json_bytes(arguments),
         "check_before tool and arguments equal this exact active request")
    guard_current_saved_request_v1(queue, original, runtime_root=runtime_root, active=active)


def _original_exact_loading_v1(
    row: dict[str, object], queue: object, reader: BasisReaderV1,
) -> bool:
    from types import FunctionType
    epoch = _REQUEST_EPOCHS.get(id(queue))
    need(epoch is not None and epoch.queue is queue, "actual registered startup source epoch")
    if epoch is None:
        raise ValueError("unreachable unbound startup epoch")
    tree = ast.parse(exact_read(reader, epoch.startup_ref, 65536))
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == "exact_loading"]
    constants = [node.value for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "LOADING_ERROR"
                         for target in node.targets)]
    need(len(functions) == len(constants) == 1 and not functions[0].decorator_list,
         "one exact original pure loading classifier and its constant")
    constant: object = ast.literal_eval(constants[0])
    namespace: dict[str, object] = {"LOADING_ERROR": text(constant)}
    exec(compile(ast.Module(body=[functions[0]], type_ignores=[]),
                 epoch.startup_ref.path, "exec"), namespace)
    function = namespace.get("exact_loading")
    need(isinstance(function, FunctionType), "original compiled loading classifier")
    if not isinstance(function, FunctionType):
        raise ValueError("unreachable missing original loading classifier")
    result: object = function(row, SEMANTIC_TOOL)
    if type(result) is not bool:
        raise ValueError("original loading classifier must return exact bool")
    return result


@dataclass(frozen=True)
class CurrentSavedConsumerProbeCallV1:
    operation: str
    execution_kind: Literal["original_function", "original_ast_projection"]
    source_ref: ExactRefV1
    function_qualname: str
    function_ast_sha256: str
    projection_ast_sha256: str | None
    projection_source: str | None
    call_count: int
    observed: JsonObject

    def to_wire(self) -> JsonObject:
        return {
            "operation": self.operation, "execution_kind": self.execution_kind,
            "source_ref": self.source_ref.to_wire(), "function_qualname": self.function_qualname,
            "function_ast_sha256": self.function_ast_sha256,
            "projection_ast_sha256": self.projection_ast_sha256,
            "projection_source": self.projection_source,
            "call_count": self.call_count, "observed": self.observed,
        }


_PROBE_OPERATIONS = {
    "canonical_outer_constructor", "task_spec_validation", "supervisor_prepared_business",
    "supervisor_make_spec", "supervisor_verify_cold_profile", "frozen_mcp_safe_boundary",
}


@dataclass(frozen=True)
class CurrentSavedConsumerProbeV1:
    machine_id: str
    observed_at_utc: str
    runtime_root: str
    attempt_nonce: str
    task_nonce: str
    plan_ref: ExactRefV1
    quote_ref: ExactRefV1
    harness_ref: ExactRefV1
    calls: tuple[CurrentSavedConsumerProbeCallV1, ...]

    def to_wire(self) -> JsonObject:
        return {
            "schema": "xar.current-saved-startup-consumer-probe/v1",
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "runtime_root": self.runtime_root, "attempt_nonce": self.attempt_nonce,
            "task_nonce": self.task_nonce, "plan_ref": self.plan_ref.to_wire(),
            "quote_ref": self.quote_ref.to_wire(), "harness_ref": self.harness_ref.to_wire(),
            "calls": [item.to_wire() for item in self.calls],
            "actual_rpc_calls": 0, "game_processes_started": 0, "sdk_processes_started": 0,
            "keeper_processes_started": 0, "tasks_started": 0, "ordinary_cycle_credit": 0,
            "game_day_credit": 0, "fresh_native_qualification": False,
        }


def _parse_probe_call(value: object) -> CurrentSavedConsumerProbeCallV1:
    row = record(value)
    need(set(row) == {"operation", "execution_kind", "source_ref", "function_qualname",
                      "function_ast_sha256", "projection_ast_sha256", "projection_source",
                      "call_count", "observed"}, "exact startup consumer call evidence")
    operation = text(row["operation"])
    need(operation in _PROBE_OPERATIONS, "one named actual consumer operation")
    function_digest = text(row["function_ast_sha256"])
    need(re.fullmatch("[0-9a-f]{64}", function_digest) is not None, "actual function AST digest")
    observed = json_object(row["observed"])
    need(bool(observed), "consumer probe requires actual captured observations")
    if row["execution_kind"] == "original_function":
        need(row["projection_ast_sha256"] is None and row["projection_source"] is None,
             "full function is not a projected main call")
        return CurrentSavedConsumerProbeCallV1(
            operation, "original_function", parse_ref(row["source_ref"]),
            text(row["function_qualname"]), function_digest, None, None,
            integer(row["call_count"], 1), observed)
    need(row["execution_kind"] == "original_ast_projection", "explicit actual execution kind")
    digest = text(row["projection_ast_sha256"])
    need(re.fullmatch("[0-9a-f]{64}", digest) is not None, "actual projected statement digest")
    return CurrentSavedConsumerProbeCallV1(
        operation, "original_ast_projection", parse_ref(row["source_ref"]),
        text(row["function_qualname"]), function_digest, digest,
        text(row["projection_source"]), integer(row["call_count"], 1), observed)


def parse_current_saved_consumer_probe_v1(value: object) -> CurrentSavedConsumerProbeV1:
    row = record(value)
    zero = {"actual_rpc_calls", "game_processes_started", "sdk_processes_started",
            "keeper_processes_started", "tasks_started", "ordinary_cycle_credit", "game_day_credit"}
    need(set(row) == zero | {
        "schema", "machine_id", "observed_at_utc", "runtime_root", "attempt_nonce",
        "task_nonce", "plan_ref", "quote_ref", "harness_ref", "calls", "fresh_native_qualification",
    } and row["schema"] == "xar.current-saved-startup-consumer-probe/v1",
         "exact granular actual startup consumer probe")
    for name in zero:
        need(integer(row[name]) == 0, "software-only startup consumer probe: " + name)
    need(row["fresh_native_qualification"] is False, "consumer software probe is not Native qualification")
    observed = text(row["observed_at_utc"]); utc(observed)
    calls = tuple(_parse_probe_call(item) for item in rows(row["calls"]))
    need(len(calls) == 6 and {item.operation for item in calls} == _PROBE_OPERATIONS,
         "all six actual startup consumer operations")
    return CurrentSavedConsumerProbeV1(
        text(row["machine_id"]), observed, text(row["runtime_root"]),
        _nonce(row["attempt_nonce"]), _nonce(row["task_nonce"]),
        parse_ref(row["plan_ref"]), parse_ref(row["quote_ref"]), parse_ref(row["harness_ref"]), calls)


def _qualified_function(payload: bytes, qualname: str) -> ast.AST:
    found: list[ast.AST] = []
    def visit(node: ast.AST, parents: tuple[str, ...]) -> None:
        current = parents
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            current = parents + (node.name,)
            name = ".".join(current)
            if qualname == name or qualname.endswith("." + name):
                found.append(node)
        for child in ast.iter_child_nodes(node):
            visit(child, current)
    visit(ast.parse(payload), ())
    need(len(found) == 1, "one source-bound actual consumer callable: " + qualname)
    return found[0]


def _validate_consumer_probe(
    reference: ExactRefV1, plan_ref: ExactRefV1, quote_ref: ExactRefV1,
    plan: ColdPlanV1, reader: BasisReaderV1,
) -> CurrentSavedConsumerProbeV1:
    probe = parse_current_saved_consumer_probe_v1(_small(reader, reference, _MAX_SMALL))
    need(probe.machine_id == plan.machine_id == current_execution_machine_id_v1()
         and probe.plan_ref == plan_ref and probe.quote_ref == quote_ref
         and _same_path(probe.runtime_root, plan.runtime_root)
         and probe.attempt_nonce == plan.attempt_nonce and probe.task_nonce == plan.task_nonce,
         "startup probes bind this exact actual Plan/Quote/receiver namespace")
    need(probe.harness_ref == plan.producer_ref, "actual approved public probe producer")
    exact_read(reader, probe.harness_ref, _MAX_SMALL)
    quote = parse_quote_v1(_small(reader, quote_ref))
    for call in probe.calls:
        _bind_consumer_probe_call_v1(call, plan, quote, reader)
        function = _qualified_function(exact_read(reader, call.source_ref, _MAX_SMALL),
                                       call.function_qualname)
        dumped = ast.dump(function, include_attributes=False)
        need(hashlib.sha256(dumped.encode()).hexdigest() == call.function_ast_sha256,
             "probe executed this exact original consumer source")
        if call.execution_kind == "original_ast_projection":
            need(call.projection_source is not None and call.projection_ast_sha256 is not None,
                 "explicit original statement projection")
            if call.projection_source is None:
                raise ValueError("unreachable missing projection")
            projected = ast.parse(call.projection_source)
            need(bool(projected.body), "nonempty original consumer statement projection")
            nodes = list(ast.walk(function))
            ordered: list[int] = []
            for statement in projected.body:
                statement_dump = ast.dump(statement, include_attributes=False)
                matches = [node for node in nodes
                           if isinstance(node, ast.stmt) and ast.dump(node, include_attributes=False) ==
                           statement_dump]
                need(len(matches) == 1, "projection consists of original consumer statements")
                ordered.append(matches[0].lineno)
            need(ordered == sorted(ordered) and len(set(ordered)) == len(ordered)
                 and hashlib.sha256(ast.dump(projected, include_attributes=False).encode()).hexdigest()
                 == call.projection_ast_sha256, "original projection order and exact digest")
    return probe


class CurrentSavedOriginalSessionV1(Protocol):
    async def call_tool(
        self, name: str, arguments: JsonObject, *, read_timeout_seconds: float,
    ) -> CurrentSavedToolResultV1: ...


def install_current_saved_queue_guard_v1(
    queue_type: type[object], *, runtime_root: Path,
) -> type[object]:
    """Wrap the original factory methods at the single legacy dynamic boundary."""
    from collections.abc import Awaitable
    from types import FunctionType
    marker: object = getattr(queue_type, "_current_saved_guard_installed_v1", None)
    if marker is _ISSUER:
        return queue_type
    need(marker is None, "Queue class cannot carry a foreign guard installer")
    original_call = queue_type.__dict__.get("call")
    original_check = queue_type.__dict__.get("check_before")
    need(isinstance(original_call, FunctionType) and isinstance(original_check, FunctionType),
         "actual original cold factory call and check_before functions")
    if not isinstance(original_call, FunctionType) or not isinstance(original_check, FunctionType):
        raise ValueError("unreachable invalid original Queue functions")

    def check_before(self: object, tool: object, arguments: object) -> None:
        check_current_saved_tool_v1(self, tool, arguments, runtime_root=runtime_root)
        outcome: object = original_check(self, tool, arguments)
        need(outcome is None, "unchanged original check_before returns no admission token")

    async def call(
        self: object, session: CurrentSavedOriginalSessionV1, request: object, path: Path,
    ) -> object:
        need(_attribute(self, "_current_saved_active_permit_v1") is None,
             "no overlapping Queue tool call")
        permit = guard_current_saved_request_v1(self, request, runtime_root=runtime_root)

        async def transport(
            tool: str, arguments: JsonObject, budget: float,
        ) -> CurrentSavedToolResultV1:
            return await session.call_tool(tool, arguments, read_timeout_seconds=budget)

        guarded = GuardedCurrentSavedSessionV1(
            self, request, runtime_root=runtime_root, call=transport, permit=permit)
        setattr(self, "_current_saved_active_permit_v1", permit)
        try:
            pending: object = original_call(self, guarded, request, path)
            need(isinstance(pending, Awaitable), "original actual Queue call remains asynchronous")
            if not isinstance(pending, Awaitable):
                raise ValueError("unreachable invalid original Queue coroutine")
            outcome: object = await pending
            _record_current_saved_acceptance_v1(self, request, runtime_root)
            return outcome
        finally:
            need(_attribute(self, "_current_saved_active_permit_v1") is permit,
                 "this call retains its own active permit")
            setattr(self, "_current_saved_active_permit_v1", None)

    setattr(queue_type, "check_before", check_before)
    setattr(queue_type, "call", call)
    setattr(queue_type, "_current_saved_guard_installed_v1", _ISSUER)
    return queue_type


def validate_current_saved_dispatch_v1(
    queue: object, request: object, *, runtime_root: Path,
) -> None:
    """Validate gameplay tool/FULL dispatch; reviewed local diagnostics stay independent."""
    guard_current_saved_request_v1(queue, request, runtime_root=runtime_root)


from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1


@dataclass(frozen=True)
class _AcceptedResponseV1:
    after_identity: FileStatIdentityV1
    response_identity: FileStatIdentityV1


_ACCEPTED_RESPONSES: dict[tuple[str, int], _AcceptedResponseV1] = {}


def _record_current_saved_acceptance_v1(
    queue: object, request: object, root: Path,
) -> None:
    original = _request(request)
    sequence = integer(original["sequence"], 1)
    attempt = record(_attribute(queue, "current_attempt"))
    row = record(attempt.get("row"))
    result = record(row.get("result"))
    response = root / "p37-responses" / f"{sequence:04d}-1-result.json"
    after = root / "p37-queue" / f"{sequence:04d}-after-result.json"
    need(_json_bytes(attempt.get("request")) == _json_bytes(original)
         and _json_bytes(row.get("request")) == _json_bytes(original)
         and _same_path(text(attempt.get("response")), response)
         and row.get("client_error") is None and result.get("is_error") is False
         and result.get("result_type") == "complete",
         "unchanged original call accepted its actual persisted response")
    reader = LocalBasisReaderV1()
    _, marker = _read_actual(after, reader, 65536)
    need(_same_path(text(marker.get("response")), response),
         "original postcheck-completed marker for this response")
    _ACCEPTED_RESPONSES[(str(root.resolve()), sequence)] = _AcceptedResponseV1(
        reader.stat(str(after)), reader.stat(str(response)))


def _bind_consumer_probe_call_v1(
    call: CurrentSavedConsumerProbeCallV1, plan: ColdPlanV1, quote: ColdQuoteV1,
    reader: BasisReaderV1,
) -> None:
    def output(path: Path) -> ExactRefV1:
        matches = [row for row in quote.files if _same_path(row.path, path)]
        need(len(matches) == 1, "one current quoted consumer source/output")
        row = matches[0]
        return ExactRefV1(row.path, row.bytes, row.sha256)
    root = Path(plan.runtime_root)
    config = output(root / "ROOT-LAUNCH-CONFIG-C23-A15.json")
    spec_ref = output(Path(plan.supervisor_spec_path))
    spec = _small(reader, spec_ref, 65536)
    observed = call.observed
    basis = decode_current_saved_basis_v1(exact_read(reader, plan.basis_ref, 65536),
                                         expected_machine_id=plan.machine_id)
    state = Path(basis.refs.driver.path).parent.parent
    expected_name: str
    if call.operation == "canonical_outer_constructor":
        expected = output(root / "root_c23_canonical_outer.py")
        expected_name = "OuterBindingV1.__init__"
        need(set(observed) == {"runtime_root", "canonical_entry_count"}
             and _same_path(text(observed["runtime_root"]), root)
             and integer(observed["canonical_entry_count"]) == 8, "actual canonical constructor result")
    elif call.operation == "task_spec_validation":
        expected = output(Path(text(spec.get("bootstrap"))))
        expected_name = "checked_spec"
        need(expected.sha256 == text(spec.get("bootstrap_sha256"))
             and set(observed) == {"spec_path", "spec_sha256", "task_nonce", "stage"}
             and _same_path(text(observed["spec_path"]), plan.supervisor_spec_path)
             and observed["spec_sha256"] == spec_ref.sha256
             and observed["task_nonce"] == plan.task_nonce and observed["stage"] == spec.get("stage"),
             "actual checked_spec accepted this exact current SPEC")
    elif call.operation == "supervisor_prepared_business":
        expected = output(root / "tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py")
        expected_name = "validate_current_saved_supervisor_business_v1"
        need(set(observed) == {"config_ref", "basis_ref", "validation_ref", "business_schema"}
             and parse_ref(observed["config_ref"]) == config
             and parse_ref(observed["basis_ref"]) == plan.basis_ref
             and parse_ref(observed["validation_ref"]) == plan.validation_ref
             and observed["business_schema"] == "xar.current-saved-supervisor-business/v1",
             "actual original supervisor business acceptance")
    elif call.operation in ("supervisor_make_spec", "supervisor_verify_cold_profile"):
        expected = output(root / "root_native30_supervisor_c23.py")
        expected_name = "main"
        need(set(observed) == {"state_dir", "manifest_path", "environment_sha256", "config_ref"}
             and _same_path(text(observed["state_dir"]), state)
             and _same_path(text(observed["manifest_path"]),
                            state / "profile/xar-autoplayer-environment.json")
             and observed["environment_sha256"] ==
             record(basis.checkpoint.get("succession_lifecycle")).get("environment_sha256")
             and parse_ref(observed["config_ref"]) == config,
             "actual make_spec and profile validator use the saved shared state/manifest")
        need(call.execution_kind == "original_ast_projection"
             and call.projection_source is not None, "original pre-CreateProcess main statements")
        projected = ast.parse(text(call.projection_source))
        need(len(projected.body) == 3 and isinstance(projected.body[0], ast.ImportFrom)
             and isinstance(projected.body[1], ast.Assign) and isinstance(projected.body[2], ast.Assign),
             "exact original import plus make_spec/profile assignments")
        dump = ast.dump(projected, include_attributes=False)
        need("make_spec" in dump and "verify_cold_profile" in dump,
             "both actual business consumers remain in their original projection")
    else:
        need(call.operation == "frozen_mcp_safe_boundary", "known current consumer operation")
        base = _small(reader, plan.sdk_base_ref)
        sdk_root = Path(text(base.get("source_root")))
        pins = [record(item) for item in rows(base.get("files"))
                if record(item).get("relative") == "xar_autoplayer/bridge/mcp_server.py"]
        need(len(pins) == 1, "current SDK BASE exact MCP source")
        pin = pins[0]
        expected = ExactRefV1(str(sdk_root / "xar_autoplayer/bridge/mcp_server.py"),
                              integer(pin.get("bytes"), 1), text(pin.get("sha256")))
        expected_name = "load_driver"
        keys = {
            "machine_id", "runtime_root", "entry_source_ref", "sdk_factory_source_ref",
            "runtime_DTO_source_ref", "actual_runtime_module_path", "queue_source_ref",
            "queue_argv_AST_sha256", "actual_imports_executed", "actual_factory_code_executed",
            "factory_positive_calls", "wrapper_negative_rejections", "actual_parser_executed",
            "actual_SDK_main_factory_projection_executed", "main_factory_positive_calls",
            "main_factory_argument_count", "main_factory_AST_sha256",
            "main_factory_projection_AST_sha256", "actual_constructor_arguments",
            "lifecycle_binding_scope", "live_lifecycle_binding_qualified",
            "parser_argument_scope", "parser_argv_sha256", "actual_native_launch_DTO_constructed",
            "software_only", "native_constructor_replaced", "route_window_clock",
            "global_timeline_speed", "global_high_speed_ab", "Native_driver_or_endpoint_constructed",
            "Game_RPC_Native_pipe_process_launch_calls", "Driver_SAVE_body_reads",
        }
        need(set(observed) == keys and observed["machine_id"] == plan.machine_id
             and _same_path(text(observed["runtime_root"]), root)
             and parse_ref(observed["entry_source_ref"]) == output(root / "root_p37c23_mcp_entry.py")
             and parse_ref(observed["sdk_factory_source_ref"]) == expected
             and parse_ref(observed["queue_source_ref"]) ==
             output(root / "root_p37c23_sdk_queue.py"),
             "safe factory observations bind this exact generated entry, Queue and SDK")
        for key in ("actual_imports_executed", "actual_factory_code_executed",
                    "actual_parser_executed", "actual_SDK_main_factory_projection_executed",
                    "actual_native_launch_DTO_constructed", "software_only", "native_constructor_replaced"):
            need(observed[key] is True, "actual software consumer executed: " + key)
        need(integer(observed["factory_positive_calls"]) == 2
             and integer(observed["main_factory_positive_calls"]) == 1
             and integer(observed["wrapper_negative_rejections"]) == 5
             and integer(observed["main_factory_argument_count"]) == 14
             and integer(observed["global_timeline_speed"]) == 3
             and observed["global_high_speed_ab"] is False
             and observed["Native_driver_or_endpoint_constructed"] is False
             and observed["live_lifecycle_binding_qualified"] is False
             and integer(observed["Game_RPC_Native_pipe_process_launch_calls"]) == 0
             and integer(observed["Driver_SAVE_body_reads"]) == 0,
             "software factory forwarding and zero Native scope")
        clock = record(observed["route_window_clock"])
        need(set(clock) == {"timeline_speed", "research_high_speed_ab"}
             and integer(clock["timeline_speed"]) == 4 and clock["research_high_speed_ab"] is True
             and observed["parser_argument_scope"] == "original_queue_argv_projection"
             and observed["lifecycle_binding_scope"] == "unqualified_software_forwarding_marker",
             "scoped4/global3 and explicitly unqualified lifecycle fixture")
        for key in ("queue_argv_AST_sha256", "parser_argv_sha256", "main_factory_AST_sha256",
                    "main_factory_projection_AST_sha256"):
            need(re.fullmatch("[0-9a-f]{64}", text(observed[key])) is not None,
                 "exact executed original projection digest")
        runtime_pin = [record(item) for item in rows(base.get("files"))
                       if record(item).get("relative") == "xar_autoplayer/runtime.py"]
        need(len(runtime_pin) == 1, "current SDK runtime DTO source")
        dto = ExactRefV1(str(sdk_root / "xar_autoplayer/runtime.py"),
                         integer(runtime_pin[0].get("bytes"), 1), text(runtime_pin[0].get("sha256")))
        need(parse_ref(observed["runtime_DTO_source_ref"]) == dto, "actual frozen runtime DTO pin")
        actual_dto = Path(text(observed["actual_runtime_module_path"]))
        freeze_rows = [row for row in quote.files if Path(row.path).name == "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json"]
        need(len(freeze_rows) == 1, "one quoted SDK freeze")
        freeze_row = freeze_rows[0]
        frozen = _small(reader, ExactRefV1(freeze_row.path, freeze_row.bytes, freeze_row.sha256))
        host_dto = Path(text(frozen.get("runtime_source_repo"))) / "ck3_autonomous_player/src/xar_autoplayer/runtime.py"
        need(actual_dto.resolve() in {Path(dto.path).resolve(), host_dto.resolve()}
             and _actual_ref(actual_dto, reader) == ExactRefV1(str(actual_dto.resolve()), dto.bytes, dto.sha256),
             "actual SDK or exact same-byte Host DTO origin")
        forwarded = record(observed["actual_constructor_arguments"])
        need(set(forwarded) == {
            "allow_private_current_timeline_blocker_query", "allow_private_death_succession_modal_continue",
            "allow_private_faction_gift_formal_trial", "allow_private_lifestyle_formal_trial",
            "allow_route_contact_high_speed_ab", "allow_war_daily_watch_v1", "pipe_name",
            "private_faction_round_id", "route_contact_timeline_speed", "route_window_clock_v1",
            "save_dir", "state_dir", "succession_lifecycle_binding", "war31_one_shot_surrender_gate",
        } and
             _json_bytes(forwarded.get("route_window_clock_v1")) == _json_bytes(clock)
             and integer(forwarded.get("route_contact_timeline_speed")) == 3
             and forwarded.get("allow_route_contact_high_speed_ab") is False
             and _same_path(text(forwarded.get("state_dir")), state)
             and _same_path(text(forwarded.get("save_dir")), state / "profile/save games")
             and forwarded.get("pipe_name") == _small(reader, config).get("pipe_name"),
             "real complete factory arguments preserve the scoped/global clock contract")
        marker = record(forwarded.get("succession_lifecycle_binding"))
        need(marker.get("schema") ==
             "xar.current-saved-preflight-unqualified-lifecycle-forwarding-marker/v1"
             and marker.get("fresh_native_qualification") is False
             and integer(marker.get("ordinary_cycle_credit")) == integer(marker.get("game_day_credit")) == 0,
             "lifecycle forwarding is a software marker, not a Native qualification")
    need(call.source_ref == expected and call.function_qualname == expected_name,
         "operation must execute this attempt's exact original consumer")
    if call.operation not in ("supervisor_make_spec", "supervisor_verify_cold_profile"):
        need(call.execution_kind == "original_function", "actual original consumer function call")


def _create_offline_metadata_v1(
    path: Path, value: object, *, approved_root: Path, reader: BasisReaderV1,
) -> ExactRefV1:
    import os
    root = approved_root.resolve(strict=True)
    need(path.parent.resolve(strict=True) == root and not path.exists() and not path.is_symlink(),
         "new metadata directly inside the explicitly approved root")
    current = root
    while True:
        need(not current.is_symlink()
             and not (getattr(current.stat(), "st_file_attributes", 0) & 1024),
             "metadata output ancestor cannot be a reparse point")
        if current.parent == current:
            break
        current = current.parent
    payload = _json_bytes(value) + b"\n"
    limits = {
        "ROOT-CURRENT-SAVED-HISTORICAL-REPLAY01.json": 12288,
        "ROOT-CURRENT-SAVED-CONSUMER-PROBE01.json": 16384,
        "ROOT-CURRENT-SAVED-PREFLIGHT01.json": 32768,
        "ROOT-CURRENT-SAVED-PREPARED01.json": 4096,
    }
    limit = limits.get(path.name, 0)
    need(0 < len(payload) <= limit, "exact per-output qualification budget")
    with path.open("xb") as stream:
        need(stream.write(payload) == len(payload), "complete bounded qualification metadata")
        stream.flush(); os.fsync(stream.fileno())
    reference = ExactRefV1(str(path.resolve()), len(payload), hashlib.sha256(payload).hexdigest())
    exact_read(reader, reference, limit)
    return reference


def _run_frozen_consumer_probe_v1(
    plan_ref: ExactRefV1, quote_ref: ExactRefV1, plan: ColdPlanV1,
) -> CurrentSavedConsumerProbeV1:
    import os
    import subprocess
    import sys
    script = (
        "import io,json,sys\n"
        "from pathlib import Path\n"
        "root=Path(sys.argv[1]).resolve(strict=True)\n"
        "sys.path.insert(0,str(root))\n"
        "from tools.g2_saved_campaign.current_saved_basis_v1 import parse_ref\n"
        "from tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1 import run_current_saved_startup_consumer_probe_v1\n"
        "output=sys.stdout\n"
        "captured=io.StringIO()\n"
        "sys.stdout=captured\n"
        "result=run_current_saved_startup_consumer_probe_v1(parse_ref(json.loads(sys.argv[2])),parse_ref(json.loads(sys.argv[3])),expected_machine_id=sys.argv[4])\n"
        "sys.stdout=output\n"
        "print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))\n"
    )
    command = [
        str(Path(text(getattr(sys, '_base_executable', None))).resolve(strict=True)), "-I", "-B", "-X", "utf8", "-c", script,
        plan.runtime_root, _json_bytes(plan_ref.to_wire()).decode(),
        _json_bytes(quote_ref.to_wire()).decode(), plan.machine_id,
    ]
    completed = subprocess.run(
        command, cwd=plan.runtime_root, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    need(completed.returncode == 0, "fresh frozen consumer probe failed: " +
         completed.stderr[-16384:].decode("utf-8", errors="replace"))
    need(0 < len(completed.stdout) <= 16384, "bounded actual frozen probe report")
    return parse_current_saved_consumer_probe_v1(json.loads(completed.stdout))


def prepare_current_saved_offline_v1(
    plan_ref: ExactRefV1, quote_ref: ExactRefV1, *,
    approved_runtime_root: Path, approved_metadata_root: Path,
    historical_fixture_root: Path, historical_fixture_ref: ExactRefV1,
    expected_machine_id: str, expected_attempt_nonce: str, expected_task_nonce: str,
    reader: BasisReaderV1,
) -> CurrentSavedPreparedV1:
    """Run real software consumers, publish proof, then create Prepared last.

    The three owned roots are explicit caller authorization. Plan/Quote cannot
    supply write authority. The historical runner owns a finite isolated fixture;
    it never supplies live SEM/CAP, Native readiness, or ordinary business credit.
    """
    from tools.g2_saved_campaign.test_current_saved_campaign_preflight_v1 import (
        run_historical_startup_dispatch_replay_v1,
    )
    need(expected_machine_id == current_execution_machine_id_v1(),
         "public physical prepare actual execution machine")
    runtime = approved_runtime_root.resolve(strict=True)
    metadata = approved_metadata_root.resolve(strict=True)
    plan = parse_plan_v1(_small(reader, plan_ref))
    quote = parse_quote_v1(_small(reader, quote_ref))
    need(plan.machine_id == expected_machine_id and quote.plan_ref == plan_ref
         and _same_path(plan.runtime_root, runtime) and _same_path(quote.runtime_root, runtime)
         and plan.attempt_nonce == _nonce(expected_attempt_nonce)
         and plan.task_nonce == _nonce(expected_task_nonce),
         "public physical prepare exact approved run")
    final_path = runtime / "ROOT-CURRENT-SAVED-PREPARED01.json"
    names = (
        "ROOT-CURRENT-SAVED-CONSUMER-PROBE01.json",
        "ROOT-CURRENT-SAVED-HISTORICAL-REPLAY01.json",
        "ROOT-CURRENT-SAVED-PREFLIGHT01.json",
    )
    need(not final_path.exists() and all(not (metadata / name).exists() for name in names),
         "one fresh create-only qualification bundle")
    validate_current_saved_cold_owner_v1(
        plan_ref, quote_ref, reader=reader, expected_machine_id=expected_machine_id)
    basis = decode_current_saved_basis_v1(exact_read(reader, plan.basis_ref, 65536),
                                         expected_machine_id=expected_machine_id)
    validate_campaign_score_junction_physical_v1(
        quote.campaign_score_junction, runtime_root=runtime, reader=reader)
    probe = _run_frozen_consumer_probe_v1(plan_ref, quote_ref, plan)
    probe_ref = _create_offline_metadata_v1(
        metadata / names[0], probe.to_wire(), approved_root=metadata, reader=reader)
    _validate_consumer_probe(probe_ref, plan_ref, quote_ref, plan, reader)
    inputs = validate_current_saved_cold_inputs_v1(
        basis, basis_ref=plan.basis_ref, validation_ref=plan.validation_ref, reader=reader)
    cold_rows = [row for row in quote.files if row.relative_path == "root_p37c23_cold_resume.py"]
    need(len(cold_rows) == 1, "one final quoted complete cold receiver")
    cold_row = cold_rows[0]
    cold_ref = ExactRefV1(cold_row.path, cold_row.bytes, cold_row.sha256)
    replay = run_historical_startup_dispatch_replay_v1(
        fixture_root=historical_fixture_root, historical_fixture_ref=historical_fixture_ref,
        expected_execution_machine_id=expected_machine_id, current_next_sequence=basis.next_sequence,
        raw_governance=inputs.governance, governance_source_ref=basis.refs.governance,
        governance_source=exact_read(reader, basis.refs.governance, _MAX_SMALL),
        cold_receiver_source=exact_read(reader, cold_ref, 65536), cold_receiver_ref=cold_ref)
    need(replay.execution_machine_id == expected_machine_id
         and replay.fixture_ref == historical_fixture_ref
         and replay.current_next_sequence == basis.next_sequence,
         "actual public historical runner and current saved basis")
    replay_ref = _create_offline_metadata_v1(
        metadata / names[1], replay.to_wire(), approved_root=metadata, reader=reader)
    preflight = preflight_current_saved_campaign_v1(
        plan_ref, quote_ref, replay_ref=replay_ref, consumer_probe_ref=probe_ref,
        expected_machine_id=expected_machine_id, expected_runtime_root=runtime,
        expected_attempt_nonce=expected_attempt_nonce, expected_task_nonce=expected_task_nonce,
        reader=reader)
    preflight_ref = _create_offline_metadata_v1(
        metadata / names[2], preflight.to_wire(), approved_root=metadata, reader=reader)
    prepared = build_current_saved_prepared_v1(preflight, preflight_ref, reader=reader)
    _create_offline_metadata_v1(
        final_path, prepared.to_wire(), approved_root=runtime, reader=reader)
    need(verify_current_saved_prepared_v1(
        runtime_root=runtime, expected_machine_id=expected_machine_id,
        expected_attempt_nonce=expected_attempt_nonce, expected_task_nonce=expected_task_nonce,
        reader=reader) == prepared, "actual public prepare-to-launch serialized consumer chain")
    return prepared


@dataclass(frozen=True)
class CurrentSavedLiveReadinessV1:
    phase: Literal["initial_warm", "same_epoch_continuation"]
    initial_warm: WarmCurrentSavedFeederInputsV1
    checkpoint: JsonObject
    driver_identity: FileStatIdentityV1
    save_identity: FileStatIdentityV1
    sources: tuple[ExactRefV1, ...]


@dataclass(frozen=True)
class _InitialWarmAcceptanceV1:
    queue: object
    epoch: _RequestEpochV1
    warm: WarmCurrentSavedFeederInputsV1
    issuer: object


_INITIAL_WARM_ACCEPTANCES: dict[int, _InitialWarmAcceptanceV1] = {}


def _continuation_checkpoint_v1(value: object) -> JsonObject:
    from tools.g2_saved_campaign.current_saved_basis_v1 import checkpoint_anchor
    raw = record(value, {"status", "date_raw", "episode_character_id", "episode_run_id",
                         "history_index", "name", "overwrite_confirmed", "path", "sha256",
                         "size", "strategy", "succession_lifecycle"})
    need(raw.get("status") == "saved" and type(raw["overwrite_confirmed"]) is bool,
         "exact actual raw SAVE checkpoint shape")
    integer(raw["episode_character_id"], 1)
    text(raw["episode_run_id"]); text(raw["strategy"])
    name = text(raw.get("name"))
    need(name.endswith(".ck3"), "canonical native SAVE filename")
    return checkpoint_anchor({
        "name": name, "load_save_name": name[:-4], "path": text(raw.get("path")),
        "size": integer(raw.get("size"), 1), "sha256": text(raw.get("sha256")),
        "saved_date_raw": integer(raw.get("date_raw")),
        "history_index": integer(raw.get("history_index"), 1),
        "succession_lifecycle": raw.get("succession_lifecycle"),
    })


def _validate_same_epoch_continuation_v1(
    queue: object, initial: _InitialWarmAcceptanceV1, *, runtime_root: Path,
    reader: LocalBasisReaderV1,
) -> CurrentSavedLiveReadinessV1:
    from types import MethodType
    from tools.g2_saved_campaign.current_saved_basis_v1 import completed_body
    from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
        parse_current_driver_header_v1,
    )
    warm = initial.warm
    proof, inputs = warm.warm_proof, warm.inputs
    basis = inputs.basis
    sources: list[ExactRefV1] = []
    for _, ref in proof.sources.items():
        exact_read(reader, ref, _MAX_SMALL)
        sources.append(ref)
    actual_game = _small(reader, proof.sources.actual_game_ref, 65536)
    now_game = reader.process_identity(proof.game.pid)
    need(_identity_tuple(now_game) == (proof.game.pid, proof.game.creation_filetime)
         and _same_path(text(now_game.get("executable")),
                        text(rows(actual_game.get("command"))[0])),
         "continuation retains the actual original warm Game kernel generation")
    for process in proof.sdk_generations:
        now_process = reader.process_identity(process.pid)
        need(_identity_tuple(now_process) == (process.pid, process.creation_filetime)
             and _same_path(text(now_process.get("executable")), process.executable),
             "continuation retains both actual warm SDK kernel generations")
    state = record(_attribute(queue, "full_loop_state"))
    completed = integer(state.get("completed_cycles"))
    need(completed >= basis.completed_cycles, "continuation cannot rewind settled cycles")
    for name in ("pending_cycle", "pending_checkpoint", "terminal"):
        need(name in state and state[name] is None, "only settled original FULL state: " + name)
    state_ref, disk = _read_actual(
        runtime_root / "p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json", reader, 65536)
    gov_ref, gov = _read_actual(
        runtime_root / "p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json", reader, 262144)
    need(integer(disk.get("completed_cycles")) == completed
         and all(name in disk and disk[name] is None
                 for name in ("pending_cycle", "pending_checkpoint", "terminal"))
         and gov.get("schema") == "g2.queue.governance-sidecar/v1"
         and integer(gov.get("completed_cycles")) == completed
         and "pending_cycle" in gov and gov["pending_cycle"] is None
         and _json_bytes({"state": gov.get("state")}) ==
             _json_bytes({"state": _attribute(queue, "governance_result_state")}),
         "original persisted Queue and governance state agree with this exact Queue")
    sources.extend((state_ref, gov_ref))
    current = record(state.get("before"))
    need(_json_bytes(current) == _json_bytes(disk.get("before")), "actual settled current frame")
    checkpoint = _continuation_checkpoint_v1(state.get("actual_saved_checkpoint"))
    need(_json_bytes(checkpoint) ==
         _json_bytes(_continuation_checkpoint_v1(disk.get("actual_saved_checkpoint")))
         and _json_bytes(state.get("actual_saved_checkpoint")) ==
             _json_bytes(disk.get("actual_saved_checkpoint")),
         "original persisted and in-process successful checkpoint agree")
    driver_before = reader.stat(basis.refs.driver.path)
    save_before = reader.stat(basis.refs.save.path)
    header_raw = reader.read_driver_header(basis.refs.driver.path, 16384)
    header = parse_current_driver_header_v1(header_raw)
    need(header.get("pipe_name") == inputs.closed_epoch.pipe_name
         and integer(header.get("bridge_pid"), 1) == proof.game.pid
         and integer(header.get("episode_character_id"), 1) ==
             integer(current.get("actor_character_id"), 1)
         and header.get("episode_run_id") == text(current.get("episode_run_id"))
         and _json_bytes(_continuation_checkpoint_v1(header.get("last_checkpoint"))) ==
             _json_bytes(checkpoint)
         and _json_bytes(header.get("last_checkpoint")) ==
             _json_bytes(state.get("actual_saved_checkpoint"))
         and _same_path(text(checkpoint.get("path")), basis.refs.save.path)
         and integer(checkpoint.get("size"), 1) == save_before.bytes
         and integer(checkpoint.get("saved_date_raw")) <= integer(current.get("date_raw")),
         "bounded current Driver header matches the actual settled current epoch/checkpoint")
    if _json_bytes(checkpoint) == _json_bytes(basis.checkpoint):
        need(save_before == basis.save_identity
             and _json_bytes(state.get("actual_saved_checkpoint")) == _json_bytes(inputs.checkpoint),
             "unchanged initial checkpoint retains its exact original raw source and SAVE identity")
    else:
        origin = record(state.get("actual_saved_checkpoint_source"))
        need(_json_bytes(origin) == _json_bytes(disk.get("actual_saved_checkpoint_source")),
             "the original successful checkpoint source was persisted unchanged")
        turn = integer(origin.get("global_turn"), 1)
        need(basis.completed_cycles < turn <= completed, "SAVE belongs to a settled continuation cycle")
        event_ref, event = _read_actual(
            runtime_root / "p37-queue" / f"CUMULATIVE-SAVE-{turn:06d}.json", reader, 16384)
        need(event.get("status") == "saved" and integer(event.get("global_turn"), 1) == turn
             and _json_bytes(event.get("checkpoint")) ==
                 _json_bytes(state.get("actual_saved_checkpoint")),
             "original finish_cumulative_checkpoint successful SAVE event")
        response_refs: list[ExactRefV1] = []
        response_rows: list[dict[str, object]] = []
        for key in ("semantic_response", "save_response"):
            path = Path(text(origin.get(key)))
            need(path.parent.resolve() == (runtime_root / "p37-responses").resolve()
                 and re.fullmatch(r"[0-9]+-1-result\.json", path.name) is not None
                 and _same_path(text(event.get(key)), path),
                 "only this runtime's original successful SEM/SAVE source responses")
            ref, row = _read_actual(path, reader, 536936448)
            response_refs.append(ref); response_rows.append(row)
        sem_row, save_row = response_rows
        sem_request, save_request = record(sem_row.get("request")), record(save_row.get("request"))
        sem_sequence = integer(sem_request.get("sequence"), 1)
        save_sequence = integer(save_request.get("sequence"), 1)
        need(basis.next_sequence + 1 < sem_sequence < save_sequence <
             integer(_attribute(queue, "next_sequence"), 1),
             "continuation SEM then successful SAVE follow the original warm readiness")
        semantic = record(completed_body(sem_row, SEMANTIC_TOOL))
        saved = record(completed_body(save_row, "ck3_save_checkpoint"))
        raw_checkpoint = record(state.get("actual_saved_checkpoint"))
        need(_json_bytes(saved.get("checkpoint")) == _json_bytes(raw_checkpoint)
             and integer(raw_checkpoint.get("date_raw")) == integer(semantic.get("date_raw"))
             and raw_checkpoint.get("episode_run_id") == text(semantic.get("episode_run_id"))
             and integer(raw_checkpoint.get("episode_character_id"), 1) ==
                 integer(record(semantic.get("played_character")).get("character_id"), 1)
             and record(sem_request.get("arguments")) == {}
             and _json_bytes(save_request.get("arguments")) ==
                 _json_bytes({"expected_revision": integer(semantic.get("revision"), 1)}),
             "the actual successful SAVE is paired with its own original semantic frame")
        method = _attribute(queue, "checkpoint_lifecycle_matches")
        need(isinstance(method, MethodType), "original Queue lifecycle predicate remains bound")
        if not isinstance(method, MethodType):
            raise ValueError("unreachable missing original lifecycle consumer")
        matched: object = method(raw_checkpoint.get("succession_lifecycle"))
        need(matched is True, "original Queue accepted the saved checkpoint lifecycle")
        sources.extend((event_ref, *response_refs))
    need(reader.stat(basis.refs.driver.path) == driver_before
         and reader.stat(basis.refs.save.path) == save_before,
         "continuation bounded Driver header and SAVE stat remain stable")
    _clean_flags(queue, runtime_root)
    return CurrentSavedLiveReadinessV1(
        "same_epoch_continuation", warm, checkpoint, driver_before, save_before, tuple(sources))

def decode_current_saved_historical_payload_v1(value: object) -> tuple[ExactRefV1, bytes]:
    """Decode one explicitly bounded archive field without the short-text interface."""
    import base64
    import zlib
    item = record(value, {"encoding", "encoded", "source_ref"})
    ref = parse_ref(item["source_ref"])
    encoded = item["encoded"]
    need(item["encoding"] == "zlib-base64" and 0 < ref.bytes <= _MAX_SMALL
         and type(encoded) is str, "exact bounded archive encoding")
    if not isinstance(encoded, str):
        raise ValueError("unreachable archive string type")
    need(0 < len(encoded) <= 131072 and len(encoded) % 4 == 0, "archive base64 field bound")
    compressed = base64.b64decode(encoded, validate=True)
    need(0 < len(compressed) <= 98304
         and base64.b64encode(compressed).decode("ascii") == encoded,
         "bounded canonical base64 compressed payload")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, ref.bytes + 1)
    need(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
         and len(raw) == ref.bytes and hashlib.sha256(raw).hexdigest() == ref.sha256,
         "archived source exact original bytes")
    return ref, raw



@dataclass(frozen=True)
class CurrentSavedQueueToolInflightV1:
    sequence: int
    tool: str
    arguments: JsonObject
    request_file: str
    at_utc: str
    replay_allowed: Literal[False] = False


def parse_current_saved_queue_tool_inflight_v1(value: object) -> CurrentSavedQueueToolInflightV1:
    row = record(value, {"sequence", "tool", "arguments", "request_file", "at_utc", "replay_allowed"})
    need(row["replay_allowed"] is False, "original Queue INFLIGHT forbids replay")
    return CurrentSavedQueueToolInflightV1(
        integer(row["sequence"], 1), text(row["tool"]), json_object(row["arguments"]),
        text(row["request_file"]), utc(row["at_utc"]))
