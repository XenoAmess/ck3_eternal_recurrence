"""One actual public CLI restore and one real Save; no game-state fixture."""
from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
import sys
from typing import Literal, Protocol, TypedDict, runtime_checkable

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[1]
for directory in (TOOLS, REPO, REPO / "tools"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import acceptance_adapter as core
from acceptance_contract import CasePort, Object, Pin, array, field, integer, mapping, object_value, pin, read, require, text, utc_now, write_once
from checkpoint_callback import checked_pin
from checkpoint_producer import stamp
from checkpoint_producer import raw_object
from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2
from cold_persistence_observer import ColdCheckpoint, ObservedCheckpoint, PersistenceCheck, compare_persistence, consume_checkpoint
from independent_mod_release import verify_manifest
from product import spec
from saved_campaign_actor_binding import SavedCampaignActorBinding

CASE = "cold_persistence"
CONTRACT_NAME = "cold_persistence.contract.json"
REGISTRY_NAME = "cold_persistence.registry_stanza.json"
RESULT_NAME = "living-artifacts-cold-persistence-result.json"
CHECKS = ("COLD-GROWTH-STATE", "COLD-ALL-ARTIFACT-VARIABLES", "COLD-SUPPRESSION-DEADLINE",
          "COLD-SUPPRESSION-TIMER-SEQUENCE", "COLD-FEEDING-IMPRINT", "COLD-SURVIVING-MATERIALS")
SOURCES = ("cold_persistence_acceptance_adapter.py", "cold_persistence_observer.py", "saved_campaign_actor_binding.py",
           "acceptance_adapter.py", "acceptance_contract.py", "startup_actor_binding.py", "checkpoint_callback.py",
           "checkpoint_artifacts.py", "checkpoint_producer.py", "living_artifacts_model.py", "prepare_fixture.py",
           "living_artifacts_core.py", "living_artifacts_content.py", "management_event_contract.py",
           "inventory_gui_contract.py", "native_interruption_contract.py", "product.py")
INPUT_FIELDS = {"product_dir", "formal_manifest", "plain_configuration", "source_run_context", "source_runtime_manifest",
                "source_checkpoint_observation", "source_save_native_record", "source_item_native_record"}


@runtime_checkable
class FinishPreparation(Protocol):
    def finish_product_profile(self, context: object, profile: object, *, provenance: object) -> object: ...


@dataclass(frozen=True)
class Origin:
    context: Object
    manifest: Object
    checkpoint: ObservedCheckpoint
    evidence: tuple[Pin, ...]


class ColdResult(TypedDict):
    schema: Literal["living-artifacts-cold-persistence-result-v1"]
    product: Literal["living-artifacts"]
    case: Literal["cold_persistence"]
    run_id: str
    machine_id: str
    reviewer: str
    observed_at_utc: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    checks: list[PersistenceCheck]
    source_observation: Pin
    cold_checkpoint: Pin | None
    startup_binding: Pin | None
    evidence: list[Pin]
    error: str | None
    actual_natural_days: Literal[0]
    actual_saved_observations: int
    actual_public_calls_budgeted: int
    case_contract_qualified: bool
    gui_contract_qualified: bool
    business_pass: Literal[False]
    product_release_pass: Literal[False]
    normal_close_owner: Literal["shared entry/CaseClient"]
    normal_close_pending: Literal[True]


def validate_contract(context: object) -> core.Contract:
    require(field(context, "product") == "living-artifacts" and field(context, "case") == CASE,
            "Select the actual cold_persistence case")
    config = mapping(field(context, "case_contract"), "cold contract")
    require(object_value(config) == read(TOOLS / CONTRACT_NAME) and
            field(context, "case_spec") == read(TOOLS / REGISTRY_NAME), "Exact standalone cold contract/registry required")
    require(config["required_checks"] == list(CHECKS) and config["whole_product_acceptance_credit"] is False,
            "Cold persistence scope differs")
    integer(config["schema_version"], "cold contract version", 1, 1)
    integer(config["maximum_natural_days"], "cold natural day cap", 0, 0)
    integer(config["maximum_checkpoints"], "cold Save cap", 1, 1)
    declared = {text(item, "cold declared tool") for item in array(field(field(context, "case_spec"), "required_mcp_tools"), "cold tools")}
    require({"ck3_take_snapshot", "ck3_save_checkpoint", core.ITEM} <= declared and
            core.ITEM in array(field(field(context, "case_spec"), "opt_in_read_only_mcp_tools"), "cold read-only opt-ins"),
            "Actual snapshot/Save/native item tools must be declared")
    return core.Contract(0, integer(config["max_public_calls"], "cold public call cap", 12, 12), 60, CHECKS, ())


def _read_pin(value: object, label: str) -> tuple[Object, Pin]:
    reference = checked_pin(value, label)
    return read(Path(reference["path"])), reference


def origin(context: object) -> Origin:
    values = mapping(field(context, "case_inputs"), "cold inputs")
    require(set(values) == INPUT_FIELDS, "Closed cold input fields required; expected game state cannot be supplied")
    original, context_pin = _read_pin(values["source_run_context"], "original allocated run context")
    manifest, manifest_pin = _read_pin(values["source_runtime_manifest"], "original runtime manifest")
    current_manifest, _ = _read_pin(field(context, "runtime_manifest"), "selected current runtime manifest")
    require(original.get("schema") == "ck3-mod-acceptance-run-context-v1" and original.get("product") == "living-artifacts",
            "Original allocated Living Artifacts context required")
    source_run = text(field(original, "run_id"), "source run")
    require(source_run != mapping(context, "current case").get("run_id"), "Cold case must use a new allocated run")
    machine = text(field(current_manifest, "machine_id"), "selected machine")
    require(field(manifest, "machine_id") == machine and field(manifest, "game") == field(current_manifest, "game"),
            "Source native provenance belongs to another machine or selected game")
    frozen, frozen_pin = _read_pin(field(original, "frozen_argv"), "original frozen host argv")
    require(field(frozen, "run_id") == source_run and field(frozen, "runtime_manifest") == manifest_pin,
            "Original allocated run is not bound to its selected runtime")
    record, observation_pin = _read_pin(values["source_checkpoint_observation"], "original checkpoint observation")
    save_pin = checked_pin(values["source_save_native_record"], "original Save native record")
    item_pin = checked_pin(values["source_item_native_record"], "original item native record")
    run_root = Path(text(field(original, "run_dir"), "original live directory")).resolve()
    require(all(Path(reference["path"]).is_relative_to(run_root) for reference in (observation_pin, save_pin, item_pin)),
            "Original checkpoint/native files are not from their allocated live run")
    response = record.get("readback_response", record.get("response"))
    reviewer = text(field(response, "reviewer"), "original checkpoint reviewer")
    checkpoint = consume_checkpoint(record, run_id=source_run, machine_id=machine, reviewer=reviewer, manifest=manifest,
        save_native=save_pin, item_native=item_pin)
    seed = mapping(field(context, "saved_campaign"), "public saved campaign")
    require(set(seed) in ({"save", "bytes", "sha256", "player_id", "date_raw"},
                         {"save", "bytes", "sha256", "player_id", "date_raw", "product_inventory"}), "Closed public saved-input contract required")
    require(Path(text(seed["save"], "selected immutable Save")).resolve() == Path(checkpoint.load_save["path"]) and
            integer(seed["bytes"], "selected save bytes", 1, 2**63 - 1) == checkpoint.load_save["bytes"] and
            text(seed["sha256"], "selected save SHA") == checkpoint.load_save["sha256"] and
            integer(seed["player_id"], "selected save actor", 1, 2**32 - 2) == checkpoint.frame.player_id and
            integer(seed["date_raw"], "selected save date", 1, 2**31 - 1) == checkpoint.frame.date_raw,
            "Selected cold input is not this verified actual original Save")
    return Origin(original, manifest, checkpoint, (context_pin, manifest_pin, frozen_pin, observation_pin, save_pin, item_pin, *checkpoint.evidence))


def prepare_case(context: object) -> Object:
    validate_contract(context)
    source = origin(context)
    values = field(context, "case_inputs")
    formal = checked_pin(field(values, "formal_manifest"), "formal release manifest")
    product = Path(text(field(values, "product_dir"), "formal product staging")).resolve()
    verify_manifest(spec(), product, Path(formal["path"]))
    profile = materialize_saved_profile_v2(context, product, field(values, "plain_configuration"), source_role="formal_product")
    module: object = importlib.import_module("ck3_mod_acceptance_prepare")
    if not isinstance(module, FinishPreparation):
        raise ValueError("Actual shared profile finish API unavailable")
    finished = object_value(module.finish_product_profile(context, profile, provenance={
        "kind": "actual-source-checkpoint-cold-persistence", "source_observation": field(values, "source_checkpoint_observation"),
        "source_run_id": source.checkpoint.run_id, "source_checkpoint": source.checkpoint.load_save,
        "fixture_mounted": False, "actual_restore_observed": False, "business_pass": False}))
    output = Path(text(field(context, "output"), "cold prepare output"))
    write_once(output / "cold-source-preparation.json", {"schema": "living-artifacts-cold-source-preparation-v1",
        "source_evidence": list(source.evidence), "caller_sources": {name: pin(TOOLS / name) for name in SOURCES},
        "contract": pin(TOOLS / CONTRACT_NAME), "formal_manifest": formal, "profile": profile,
        "runtime_status": "NOT_RUN", "actual_restore_observed": False})
    seed: Object = {"save": source.checkpoint.load_save["path"], "bytes": source.checkpoint.load_save["bytes"],
        "sha256": source.checkpoint.load_save["sha256"], "player_id": source.checkpoint.frame.player_id,
        "date_raw": source.checkpoint.frame.date_raw, "product_inventory": profile["product_inventory"]["path"]}
    return object_value({"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"], "saved_campaign": seed},
        "initial_plan": write_once(output / "initial-plan.json", {"steps": []}), "profile_preparation": finished,
        "runtime_status": "NOT_RUN", "fixture_mounted": False, "business_pass": False, "product_release_pass": False})


def _prepared_sources(context: object, state: Path) -> tuple[Pin, ...]:
    preparation = read(state / "preparation.json")
    profile_ref = checked_pin(field(preparation, "preparation"), "actual profile preparation")
    output = Path(profile_ref["path"]).parent
    document = read(output / "cold-source-preparation.json")
    require(field(document, "schema") == "living-artifacts-cold-source-preparation-v1" and
            field(document, "runtime_status") == "NOT_RUN" and field(document, "actual_restore_observed") is False,
            "Original cold source preparation required")
    sources = mapping(field(document, "caller_sources"), "original cold caller sources")
    require(set(sources) == set(SOURCES), "Complete cold caller source set required")
    refs = [checked_pin(sources[name], "original cold caller " + name) for name in SOURCES]
    require(all(Path(reference["path"]).resolve() == (TOOLS / name).resolve() for name, reference in zip(SOURCES, refs, strict=True)),
            "Cold caller source route differs")
    require(field(document, "contract") == pin(TOOLS / CONTRACT_NAME), "Original cold contract changed")
    source = origin(context)
    require(field(document, "source_evidence") == list(source.evidence), "Prepared source evidence differs from allocated cold input")
    return (*refs, profile_ref, *source.evidence)


def observe_cold(session: core.Session, source: ObservedCheckpoint) -> tuple[ObservedCheckpoint, Pin]:
    session.snapshot()
    frame_ref = session.last_native_record
    if frame_ref is None:
        raise core.CaseBlocked("Actual cold snapshot source unavailable")
    saved = session.checkpoint_readback(source.inputs.target_id)
    save_ref = pin(session.client.output / f"xalw-core-{session.sequence:04d}.actual-results.json")
    native = session.observe_item(source.inputs.target_id)
    item_ref = pin(session.client.output / f"xalw-core-{session.sequence:04d}.actual-results.json")
    require(type(native.get("equipped")) is bool, "Actual cold native equipment state unavailable")
    row: ColdCheckpoint = {"schema": "living-artifacts-cold-checkpoint-v1", "run_id": session.run_id,
        "machine_id": session.machine_id, "reviewer": session.client.operator_reviewer, "source_save": saved.source_save,
        "response": object_value(saved.response), "frame_native": frame_ref, "save_native": save_ref, "item_native": item_ref,
        "expected_material_rarities": list(source.remaining), "projection": {}}
    # The real callback/parser derives the projection. The final closed record
    # is then consumed again; an authored projection never supplies final state.
    from checkpoint_callback import CheckpointSample, verify_readback
    inputs, _ = verify_readback(saved.response, run_id=session.run_id, machine_id=session.machine_id, reviewer=session.client.operator_reviewer,
        frame=saved.frame, source_save=saved.source_save, expected_material_rarities=source.remaining)
    target = next(item for item in inputs.artifacts if item.artifact_id == inputs.target_id)
    row["projection"] = {"sample": CheckpointSample.from_saved(target, inputs, native_equipped=native["equipped"] is True).to_json(),
        "saved_inputs": inputs.to_json(), "current_native_artifact_variable_query": False, "cold_reload_qualification": False}
    reference = write_once(session.client.output / "cold-checkpoint-01.json", row)
    actual = consume_checkpoint(read(Path(reference["path"])), run_id=session.run_id, machine_id=session.machine_id,
        reviewer=session.client.operator_reviewer, manifest=session.client.manifest, save_native=save_ref, item_native=item_ref)
    session.refs.extend((*actual.evidence, reference))
    return actual, reference


def run_case(context: object, client: object) -> Object:
    contract = validate_contract(context)
    if not isinstance(client, CasePort):
        raise ValueError("The actual public CaseClient interface is required")
    session = core.Session(context, client, contract, actor_binding_factory=SavedCampaignActorBinding.parse)
    checkpoint_ref: Pin | None = None
    binding_ref: Pin | None = None
    checks: tuple[PersistenceCheck, ...] = ()
    error: str | None = None
    status: Literal["PASS", "FAIL", "BLOCKED"] = "BLOCKED"
    try:
        source = origin(context)
        session.refs.extend(_prepared_sources(context, client.state))
        session.snapshot()
        require(session.current().date_raw == source.checkpoint.frame.date_raw, "Actually restored date differs from source Save")
        binding_ref = pin(client.output / "startup-actor-binding.json")
        cold, checkpoint_ref = observe_cold(session, source.checkpoint)
        checks = compare_persistence(source.checkpoint, cold)
        status = "FAIL" if any(check["status"] == "FAIL" for check in checks) else "BLOCKED" if any(check["status"] == "BLOCKED" for check in checks) else "PASS"
        error = None if status == "PASS" else "Actual persistence differs" if status == "FAIL" else "Source lacks some requested persistence features"
    except (ValueError, core.CaseBlocked, OSError, TimeoutError, KeyError, StopIteration) as failure:
        error = type(failure).__name__ + ": " + str(failure)
    result: ColdResult = {"schema": "living-artifacts-cold-persistence-result-v1", "product": "living-artifacts", "case": "cold_persistence",
        "run_id": session.run_id, "machine_id": session.machine_id, "reviewer": client.operator_reviewer, "observed_at_utc": utc_now(),
        "status": status, "checks": list(checks), "source_observation": checked_pin(field(field(context, "case_inputs"), "source_checkpoint_observation"), "source observation"),
        "cold_checkpoint": checkpoint_ref, "startup_binding": binding_ref, "evidence": session.refs, "error": error,
        "actual_natural_days": 0, "actual_saved_observations": session.checkpoint_observations, "actual_public_calls_budgeted": session.calls,
        "case_contract_qualified": status == "PASS", "gui_contract_qualified": status == "PASS", "business_pass": False, "product_release_pass": False,
        "normal_close_owner": "shared entry/CaseClient", "normal_close_pending": True}
    write_once(client.output / RESULT_NAME, result)
    return object_value(result)


def verify_case(context: object) -> Object:
    contract = validate_contract(context)
    output = Path(text(field(context, "output"), "case output"))
    if not (output / RESULT_NAME).is_file():
        return {"status": "NOT_RUN", "case_contract_qualified": False, "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False}
    result = read(output / RESULT_NAME)
    require(set(result) == set(ColdResult.__required_keys__) and result["schema"] == "living-artifacts-cold-persistence-result-v1" and
            result["run_id"] == field(context, "run_id") and result["case"] == CASE and result["product"] == "living-artifacts" and
            result["business_pass"] is False and result["product_release_pass"] is False and result["normal_close_pending"] is True,
            "Closed retained cold result/run/credit required")
    runtime, _ = _read_pin(field(context, "runtime_manifest"), "selected runtime")
    require(result["machine_id"] == field(runtime, "machine_id") and result["reviewer"] == field(context, "operator_reviewer") and
            result["normal_close_owner"] == "shared entry/CaseClient", "Retained cold machine/reviewer/close owner differs")
    _prepared_sources(context, Path(text(field(context, "state_dir"), "current state")))
    stamp(result["observed_at_utc"])
    integer(result["actual_natural_days"], "cold natural days", 0, 0)
    integer(result["actual_public_calls_budgeted"], "actual cold public calls", 0, contract.max_calls)
    saves = integer(result["actual_saved_observations"], "actual cold Saves", 0, 1)
    source = origin(context)
    require(result["source_observation"] == field(field(context, "case_inputs"), "source_checkpoint_observation"), "Retained cold source changed")
    allowed_empty_logs = list(source.checkpoint.log_streams)
    if result["cold_checkpoint"] is not None:
        cold_row, _ = _read_pin(result["cold_checkpoint"], "actual cold checkpoint")
        cold = consume_checkpoint(cold_row, run_id=text(result["run_id"], "cold run"), machine_id=text(result["machine_id"], "cold machine"),
            reviewer=text(result["reviewer"], "cold reviewer"), manifest=runtime, save_native=cold_row["save_native"], item_native=cold_row["item_native"])
        allowed_empty_logs.extend(cold.log_streams)
        checks = compare_persistence(source.checkpoint, cold)
        require(result["checks"] == object_value({"checks": list(checks)})["checks"] and saves == 1,
                "Retained cold checks differ from actual saved/native evidence")
        expected_status = "FAIL" if any(check["status"] == "FAIL" for check in checks) else "BLOCKED" if any(check["status"] == "BLOCKED" for check in checks) else "PASS"
        require(result["status"] == expected_status, "Retained cold aggregate status differs")
        binding_record, _ = _read_pin(result["startup_binding"], "actual saved-campaign actor binding")
        live = Path(text(field(context, "run_dir"), "current live run"))
        binding = SavedCampaignActorBinding.parse(raw_object(live / "native-report.json"), frozen=raw_object(live / "frozen-argv.json"),
            run_id=text(result["run_id"], "cold run"), machine_id=text(result["machine_id"], "cold machine"), manifest=runtime)
        require(binding_record == binding.to_json(), "Retained binding differs from actual shared restore proof")
    else:
        require(result["status"] == "BLOCKED" and result["checks"] == [], "No actual cold Save can grant persistence checks")
    for reference in array(result["evidence"], "retained cold evidence"):
        checked_pin(reference, "retained cold evidence", allow_empty=reference in allowed_empty_logs)
    passed = result["status"] == "PASS"
    require(result["case_contract_qualified"] is passed and result["gui_contract_qualified"] is passed and
            (result["error"] is None if passed else type(result["error"]) is str and bool(result["error"])), "Retained cold status/error qualification differs")
    return result
