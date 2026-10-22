"""One public CaseClient scene for actual core growth/equipment observations.

The public host owns launch, progression transport, normal Quit and resources.
Feeding uses the ordinary management decision and native event choices. Seven
actual saved checkpoints are paired with native owner/equipment/material reads;
fixture effects and navigation ACKs cannot grant business credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
from pathlib import Path
import re
import sys
from typing import Literal, Protocol, TypedDict, runtime_checkable

PRODUCT_TOOLS = Path(__file__).resolve().parent
if str(PRODUCT_TOOLS) not in sys.path:
    sys.path.insert(0, str(PRODUCT_TOOLS))

from acceptance_contract import (ArtifactSample, CasePort, CheckResult, Frame, INPUT_PREFIX, OBSERVATION_PREFIX,
                                 Object, Pin, RESULT_NAME, array, decimal_id, field, integer, json_value, mapping,
                                 native_id, object_value, pin, read, require, text, utc_now, write_once)
from prepare_fixture import emit_fixture
from startup_actor_binding import StartupActorBinding
from checkpoint_artifacts import SavedInputs
from checkpoint_callback import CheckpointSample, ReadbackRequestBody, verify_readback
from inventory_gui_contract import InventoryOpenRequest, REFUSAL, parse_opening, pre_intent_source
from native_interruption_contract import NativeInterruptionRequest, parse_completed_interruption
from living_artifacts_model import CORE_CHECKPOINT_LIMIT, FEEDING_XP, Rarity
from management_event_contract import ManagementChoice, management_choice

ITEM = "ck3_query_player_artifact_personal_use_v1"
EQUIP = "ck3_submit_player_artifact_personal_use_v1"
EQUIP_POST = "ck3_query_player_artifact_personal_use_action_post_v1"
OPEN = "ck3_open_player_inventory_window_v1"
OPEN_POST = "ck3_query_player_inventory_window_open_post_v1"
WINDOW = "ck3_query_ingame_ui_window_v1"
INTERACTION_QUERY = "ck3_query_character_interaction_ordinary_v1"
DECISIONS_OPEN = "ck3_open_ingame_decisions_v1"
DECISION_SELECT = "ck3_select_ingame_decision_item_v1"
DECISION_CONFIRM = "ck3_confirm_ingame_decision_outcome_v1"
REQUIRED_TOOLS: tuple[str, ...] = (
    "ck3_take_snapshot", "ck3_execute_step", ITEM, EQUIP, EQUIP_POST, OPEN, OPEN_POST, WINDOW,
    INTERACTION_QUERY, "ck3_query_current_event_window_context_v1", "ck3_select_event_option",
    "ck3_query_pending_character_interaction_context_v1", "ck3_reply_pending_character_interaction", "ck3_save_checkpoint",
    DECISIONS_OPEN, DECISION_SELECT, DECISION_CONFIRM,
)
REQUIRED_OPT_INS: dict[str, bool] = {
    "opt_in_player_artifact_personal_use_actions": True,
    "opt_in_player_inventory_window_open": True,
}


class CaseBlocked(RuntimeError):
    """An actual dependency or unknown original intent prevents this subcase."""


class CaseFailed(RuntimeError):
    """Independent actual evidence contradicts the declared product behavior."""


class CaseCallUnavailable(CaseBlocked):
    def __init__(self, tool: str, message: str, record: Pin | None, *, result_present: bool) -> None:
        super().__init__(message)
        self.tool = tool
        self.record = record
        self.result_present = result_present


@runtime_checkable
class Preparation(Protocol):
    def materialize_fixture_profile(self, context: object, fixture_dir: Path, product_dir: Path,
                                    plain_configuration: object) -> object: ...


@dataclass(frozen=True)
class Contract:
    maximum_days: int
    max_calls: int
    day_timeout: int
    required_checks: tuple[str, ...]
    deferred_checks: tuple[str, ...]


def validate_contract(context: object) -> Contract:
    require(field(context, "product") == "living-artifacts" and field(context, "case") == "core_continuous",
            "Adapter only accepts the selected canonical product/core case")
    config = mapping(field(context, "case_contract"), "core contract")
    expected = {"schema", "schema_version", "product", "case_id", "acceptance_scope", "maximum_natural_days", "max_public_calls",
                "day_timeout_seconds", "post_start", "required_startup", "forbidden_startup", "required_checks", "deferred_checks",
                "observer_authority", "artifact_picker_boundary", "whole_product_acceptance_credit", "actor_binding_authority", "startup_source_guard"}
    require(set(config) == expected and config["schema"] == "living-artifacts-core-continuous-case-v3" and
            integer(config["schema_version"], "schema version") == 3 and config["product"] == "living-artifacts" and
            config["case_id"] == "core_continuous" and config["whole_product_acceptance_credit"] is False,
            "Core contract fields/version/credit differ")
    required = tuple(text(item, "required check") for item in array(config["required_checks"], "required checks"))
    deferred = tuple(text(item, "deferred check") for item in array(config["deferred_checks"], "deferred checks"))
    require(len(required) == len(set(required)) and len(deferred) == len(set(deferred)) and not set(required) & set(deferred),
            "Required/deferred checks must remain unique and separate")
    spec = mapping(field(context, "case_spec"), "selected public case specification")
    declared = {text(item, "declared MCP tool") for item in array(field(spec, "required_mcp_tools"), "declared MCP tools")}
    require(set(REQUIRED_TOOLS) <= declared, "Declare every actual core tool on the shared case")
    for option, expected_value in REQUIRED_OPT_INS.items():
        require(spec.get(option) is expected_value, "Original public action opt-in is missing: " + option)
    readers = {text(item, "opt-in read-only tool") for item in array(field(spec, "opt_in_read_only_mcp_tools"), "explicit read-only declarations")}
    require(ITEM in readers, "Explicit original personal-artifact read-only opt-in required")
    require(config["actor_binding_authority"] == "original-source-bound-frontend-start-and-two-native-root-observations",
            "Runtime actor must be bound from this scene's original frontend Start and native root")
    require(config["observer_authority"] == "seven-actual-checkpoints-strict-melt-and-independent-native-owner-equipment-crosscheck",
            "V3 requires actual checkpoint/native observation; hidden dynamic logs cannot qualify")
    source_guard = mapping(config["startup_source_guard"], "source-derived startup guard")
    require(set(source_guard) == {"bookmark_key", "character_name_key", "history_id", "start_date", "post_start_authority", "sources"} and
            source_guard["bookmark_key"] == "bm_1066_rags_to_riches" and source_guard["character_name_key"] == "bookmark_rags_to_riches_duke_robert" and
            source_guard["history_id"] == "1128" and source_guard["start_date"] == "1066.9.15", "Source startup actor/date differs")
    source_paths: set[str] = set()
    for value in array(source_guard["sources"], "startup source bindings"):
        source = mapping(value, "startup source")
        require(set(source) == {"path", "sha256", "lines", "supports"} and re.fullmatch("[0-9a-f]{64}", text(source["sha256"], "startup source SHA")) is not None,
                "Exact source hash binding required")
        source_paths.add(text(source["path"], "startup source path"))
        text(source["lines"], "source lines")
        text(source["supports"], "source interpretation")
    require(source_paths == {"common/bookmarks/bookmarks/00_bookmarks.txt", "history/characters/norman.txt", "history/titles/k_sicily.txt"},
            "Original startup source set differs")
    return Contract(integer(config["maximum_natural_days"], "day cap", 35, 90), integer(config["max_public_calls"], "public call cap", 64, 600),
                    integer(config["day_timeout_seconds"], "day timeout", 10, 120), required, deferred)


def _bound_config(context: object) -> dict[str, object]:
    values = mapping(context, "public preparation context")
    config = mapping(field(values, "case_contract"), "contract")
    inputs = mapping(field(values, "case_inputs"), "selected inputs")
    post = mapping(config["post_start"], "post-start contract")
    actual = mapping(field(inputs, "post_start"), "actual selected bookmark")
    require(set(post) == set(actual) == {"government_key", "primary_title_tier_key", "independent"}, "Exact original bookmark fields required")
    resolved: dict[str, object] = {}
    for key, value in post.items():
        require(value is None or value == actual[key], "Cannot overwrite an explicit bookmark guard")
        resolved[key] = actual[key] if value is None else value
    require(type(resolved["independent"]) is bool and all(type(resolved[key]) is str and bool(resolved[key])
            for key in ("government_key", "primary_title_tier_key")), "Actual bookmark government/tier and strict independence required")
    amended_config = dict(config)
    amended_config["post_start"] = resolved
    return amended_config


def _write_fixture_contract(fixture_root: Path, config: dict[str, object], fixture: object) -> Pin:
    return write_once(fixture_root / "_case_contract.json", {"product": "living-artifacts", "case": "core_continuous",
               "config": config, "fixture_emission": fixture, "business_pass": False,
               "caller_sources": [pin(PRODUCT_TOOLS / name) for name in (
                    "acceptance_adapter.py", "acceptance_contract.py", "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py", "startup_actor_binding.py", "checkpoint_artifacts.py", "checkpoint_callback.py", "inventory_gui_contract.py", "native_interruption_contract.py", "management_event_contract.py")],
               "contract_source": pin(PRODUCT_TOOLS / "core_continuous.contract.json")})


def _checked_pin(value: object, label: str, expected_path: Path | None = None) -> Pin:
    reference = mapping(value, label)
    require(set(reference) == {"path", "bytes", "sha256"}, label + ": exact pin fields required")
    path = Path(text(reference["path"], label + " path")).resolve()
    integer(reference["bytes"], label + " bytes", 1)
    digest = text(reference["sha256"], label + " digest")
    require(re.fullmatch("[0-9a-f]{64}", digest) is not None, label + ": canonical digest required")
    require(expected_path is None or path == expected_path.resolve(), label + ": source path changed")
    actual = pin(path)
    require(actual == reference, label + ": original file bytes changed")
    return actual


def _prepared_sources(context: object, state: Path) -> tuple[Pin, ...]:
    require(Path(text(field(context, "state_dir"), "allocated state")).resolve() == state.resolve(),
            "Actual CaseClient state differs from the allocated state")
    root = state / "profile/mod-content/fixture"
    manifest = root / "_case_contract.json"
    frozen = read(manifest)
    require(set(frozen) == {"product", "case", "config", "fixture_emission", "business_pass", "caller_sources", "contract_source"} and
            frozen["product"] == "living-artifacts" and frozen["case"] == "core_continuous" and frozen["business_pass"] is False and
            frozen["config"] == json_value(_bound_config(context)), "Prepared fixture contract differs from the allocated case")
    expected_sources = ("acceptance_adapter.py", "acceptance_contract.py", "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py", "startup_actor_binding.py", "checkpoint_artifacts.py", "checkpoint_callback.py", "inventory_gui_contract.py", "native_interruption_contract.py", "management_event_contract.py")
    sources = array(frozen["caller_sources"], "frozen caller sources")
    require(len(sources) == len(expected_sources), "Prepared caller source set differs")
    refs = [_checked_pin(value, "prepared caller source", PRODUCT_TOOLS / name) for name, value in zip(expected_sources, sources)]
    refs.append(_checked_pin(frozen["contract_source"], "prepared contract source", PRODUCT_TOOLS / "core_continuous.contract.json"))
    emission = mapping(frozen["fixture_emission"], "frozen fixture emission")
    require(set(emission) == {"schema_version", "fixture_root", "files", "input_origin", "business_acceptance", "game_started"} and
            integer(emission["schema_version"], "fixture schema version", 2, 2) == 2 and emission["input_origin"] == "fixture_generated" and
            emission["business_acceptance"] == "NOT_ASSESSED" and emission["game_started"] is False, "Prepared fixture provenance differs")
    original_root = Path(text(emission["fixture_root"], "original fixture root")).resolve()
    files = mapping(emission["files"], "frozen fixture files")
    require(bool(files), "Empty fixture has no live input authority")
    require({item.relative_to(root).as_posix() for item in root.rglob("*") if item.is_file()} == set(files) | {"_case_contract.json"},
            "Prepared runtime fixture contains missing or unexpected files")
    for relative, value in files.items():
        original = (original_root / relative).resolve()
        copied = (root / relative).resolve()
        require(original.is_relative_to(original_root) and copied.is_relative_to(root.resolve()), "Prepared fixture relative path escaped its root")
        source = _checked_pin(value, "prepared fixture source", original)
        actual = pin(copied)
        require(actual["bytes"] == source["bytes"] and actual["sha256"] == source["sha256"], "Copied runtime fixture differs from its frozen emitter")
        refs.append(actual)
    refs.append(pin(manifest))
    return tuple(refs)


def prepare_case(context: object) -> Object:
    validate_contract(context)
    values = mapping(context, "public preparation context")
    inputs = mapping(field(values, "case_inputs"), "selected inputs")
    amended_config = _bound_config(context)
    amended_context = dict(values)
    amended_context["case_contract"] = amended_config
    output = Path(text(field(values, "output"), "prepare output")).resolve()
    fixture = emit_fixture(output / "external-core-fixture")
    fixture_root = Path(fixture["fixture_root"])
    _write_fixture_contract(fixture_root, amended_config, fixture)
    product = Path(text(field(inputs, "product_dir"), "formal staging")).resolve()
    require((product / "descriptor.mod").is_file(), "Build the exact formal staging before prepare")
    preparation = importlib.import_module("ck3_mod_acceptance_prepare")
    require(isinstance(preparation, Preparation), "Selected shared preparation API unavailable")
    if not isinstance(preparation, Preparation):
        raise ValueError("Shared preparation API unavailable")
    prepared = object_value(preparation.materialize_fixture_profile(amended_context, fixture_root, product, field(inputs, "plain_configuration")))
    initial = write_once(output / "initial-plan.json", {"steps": []})
    return {"startup": {"mode": "fixture", "state_dir": prepared["state_dir"], "fixture_start_policy": prepared["fixture_start_policy"]},
            "initial_plan": json_value(initial), "profile_preparation": prepared, "fixture_emission": json_value(fixture),
            "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False}


def _inputs(raw: bytes) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for line in raw.decode("utf-8-sig", errors="strict").splitlines():
        if INPUT_PREFIX not in line:
            continue
        body = line[line.index(INPUT_PREFIX) + len(INPUT_PREFIX):].strip()
        entries: dict[str, str] = {}
        for part in body.split(";"):
            key, separator, value = part.partition("=")
            require(bool(separator) and key not in entries, "Malformed/duplicate actual input getter field")
            entries[key] = value
        require(set(entries) == {"role", "owner", "artifact", "rarity"}, "Input getter contract differs")
        role = entries["role"]
        require(role in ("target", "common", "masterwork", "famed", "illustrious") and role not in result, "Duplicate/unknown fixture role")
        owner = decimal_id(entries["owner"], "input owner")
        artifact = decimal_id(entries["artifact"], "input artifact", allow_zero=True)
        require(entries["rarity"] == ("masterwork" if role == "target" else role), "Actual native rarity differs from required input")
        result[role] = owner, artifact
    require(set(result) == {"target", "common", "masterwork", "famed", "illustrious"} and len({item[1] for item in result.values()}) == 5,
            "Five distinct actual input references required")
    return result


class Session:
    def __init__(self, context: object, client: CasePort, contract: Contract) -> None:
        self.client = client
        self.contract = contract
        self.context = mapping(context, "public case context")
        self.run_id = text(field(self.context, "run_id"), "public run ID")
        self.machine_id = text(field(client.manifest, "machine_id"), "runtime machine ID")
        self.calls = 0
        self.days = 0
        self.sequence = 0
        self.interruption_sequence = 0
        self.owner: Frame | None = None
        self.startup_actor: StartupActorBinding | None = None
        self.last_frame: object = None
        self.start: Frame | None = None
        self.first_sample: CheckpointSample | None = None
        self.last_sample: CheckpointSample | None = None
        self.last_saved_inputs: SavedInputs | None = None
        self.checkpoint_observations = 0
        self.refs: list[Pin] = []
        self.original_action_unknown = False
        self.last_native_record: Pin | None = None

    def budget(self, calls: int) -> None:
        if self.calls + calls > self.contract.max_calls:
            raise CaseBlocked("Finite declared public call budget reached")
        self.client.guard(reserve=180)

    def bind(self, value: object) -> Frame:
        frame = Frame.parse(value, run_id=self.run_id, machine_id=self.machine_id, manifest=self.client.manifest)
        if self.startup_actor is None:
            self.startup_actor = StartupActorBinding.parse(self.client.guard(reserve=180), frozen=self.client.frozen,
                run_id=self.run_id, machine_id=self.machine_id, manifest=self.client.manifest)
            self.refs.append(write_once(self.client.output / "startup-actor-binding.json", self.startup_actor.to_json()))
        self.startup_actor.validate_frame(frame)
        if self.owner is not None:
            require((frame.pid, frame.generation_decimal, frame.player_id) ==
                    (self.owner.pid, self.owner.generation_decimal, self.owner.player_id) and frame.date_raw >= self.owner.date_raw,
                    "Actual native process/generation/actor drifted or calendar reversed")
        self.owner = frame
        self.last_frame = value
        if self.start is None:
            self.start = frame
        return frame

    def snapshot(self) -> Frame:
        self.budget(1)
        self.calls += 1
        prior = set(self.client.output.glob("case-snapshot-*.actual-results.json"))
        value = self.client.snapshot(require_event_free=False)
        produced = set(self.client.output.glob("case-snapshot-*.actual-results.json")) - prior
        if len(produced) != 1:
            raise CaseBlocked("Actual public snapshot lacks its unique retained original row")
        self.last_native_record = pin(produced.pop())
        self.refs.append(self.last_native_record)
        return self.bind(value)

    def current(self) -> Frame:
        if self.owner is None:
            raise CaseBlocked("Fresh actual owner frame unavailable")
        return self.owner

    def call(self, tool: str, args: Object | None = None) -> dict[str, object]:
        # Raw transport boundary: original rows may contain native Q64/mtime
        # integers. Keep them in Python's exact integer domain and validate only
        # consumed fields; never route the whole native result through JS JSON.
        require(tool in REQUIRED_TOOLS, "This case cannot call an undeclared arbitrary tool")
        self.budget(1)
        self.sequence += 1
        name = f"xalw-core-{self.sequence:04d}"
        step: Object = {"id": name, "tool": tool, "args": {} if args is None else args, "fresh_revision": True,
                        "continue_on_error": True, "timeout": 30}
        self.calls += 1
        reference: Pin | None = None
        try:
            actual = self.client.execute_plan([step], name, timeout=35)
        finally:
            path = self.client.output / (name + ".actual-results.json")
            if path.is_file():
                reference = pin(path)
                self.refs.append(reference)
        rows = array(actual, "actual public response rows")
        require(len(rows) == 1, "Exactly one original public response is required")
        row = mapping(rows[0], "actual public row")
        if row.get("ok") is not True or row.get("error") is not None:
            if row.get("after_snapshot") is not None:
                self.bind(row["after_snapshot"])
            error = row.get("error")
            message = error if type(error) is str else "Original public call unavailable: " + tool
            raise CaseCallUnavailable(tool, message, reference, result_present="result" in row)
        self.bind(field(row, "after_snapshot"))
        return mapping(field(row, "result"), "actual native tool result")

    def observer(self, target: str | None, *, expected_material_rarities: tuple[Rarity, ...] = tuple(FEEDING_XP)) -> tuple[CheckpointSample, Pin]:
        if self.checkpoint_observations >= CORE_CHECKPOINT_LIMIT:
            raise CaseBlocked("This core case permits only seven budgeted saved-state observations")
        before = self.current()
        result = self.call("ck3_save_checkpoint")
        checkpoint = field(result, "checkpoint")
        require(field(checkpoint, "status") == "saved" and field(field(result, "materialization"), "available") is True and
                integer(field(checkpoint, "date_raw"), "actual checkpoint date") == before.date_raw == self.current().date_raw,
                "Actual MCP checkpoint did not materialize at the retained paused native date")
        live = Path(text(field(checkpoint, "path"), "actual checkpoint path")).resolve()
        require(live.is_relative_to((self.client.state / "profile").resolve()), "Actual checkpoint escaped the allocated profile")
        source = pin(live)
        require(source["bytes"] == integer(field(checkpoint, "size"), "actual checkpoint bytes", 1) and
                source["sha256"] == text(field(checkpoint, "sha256"), "actual checkpoint SHA"), "Actual saved file differs from the original MCP receipt")
        self.checkpoint_observations += 1
        if self.last_native_record is None:
            raise CaseBlocked("Original native snapshot source is unavailable")
        request: ReadbackRequestBody = {
            "schema": "living-artifacts-checkpoint-readback-request-v1", "run_id": self.run_id, "machine_id": self.machine_id,
            "pid": before.pid, "connection_generation": before.generation_decimal, "actor_character_id": before.player_id,
            "date_raw": before.date_raw, "actual_source_save": source, "expected_target_id": target,
            "required_response_schema": "living-artifacts-checkpoint-readback-v1", "required_unknown_token_policy": "error",
            "original_native_frame_record": self.last_native_record, "observation_number": self.checkpoint_observations,
            "storage_policy": "docs/storage-retention-policy.json", "business_pass": False}
        response = self.client.root_checkpoint(f"checkpoint-readback-{self.checkpoint_observations:02d}", object_value(request), reserve=180)
        inputs, references = verify_readback(response, run_id=self.run_id, machine_id=self.machine_id,
            reviewer=self.client.operator_reviewer, frame=before, source_save=source,
            expected_material_rarities=expected_material_rarities)
        require(target is None or inputs.target_id == target, "Actual saved target reference changed")
        native = self.observe_item(inputs.target_id)
        require(self.current().date_raw == before.date_raw and type(native.get("equipped")) is bool,
                "Native owner/equipment crosscheck is unavailable or from another date")
        actual_equipped = native["equipped"]
        if type(actual_equipped) is not bool:
            raise CaseBlocked("Native equipment predicate is unavailable")
        target_item = [item for item in inputs.artifacts if item.artifact_id == inputs.target_id]
        require(len(target_item) == 1, "Actual saved target artifact is not unique")
        selected = CheckpointSample.from_saved(target_item[0], inputs, native_equipped=actual_equipped)
        self.last_saved_inputs = inputs
        self.refs.extend(references)
        if self.first_sample is None:
            self.first_sample = selected
        self.last_sample = selected
        reference = write_once(self.client.output / f"observer-checkpoint-{self.checkpoint_observations:02d}.json", {
            "schema_version": 2, "run_id": self.run_id, "machine_id": self.machine_id, "observed_at_utc": utc_now(),
            "native_date_raw": before.date_raw, "sample": selected.to_json(), "saved_inputs": inputs.to_json(),
            "readback_response": json_value(response), "original_native_frame_record": json_value(self.last_native_record),
            "expected_material_rarities": list(expected_material_rarities),
            "current_native_artifact_variable_query": False})
        self.refs.append(reference)
        return selected, reference

    def observe_item(self, target: str) -> dict[str, object]:
        reference = int(decimal_id(target, "target", allow_zero=True))
        require(reference <= 2**32 - 2, "Native numeric artifact API requires a safe full uint32 reference")
        result = self.call(ITEM, {"artifact_id": reference})
        current = self.current()
        if result.get("available") is not True:
            raise CaseBlocked("Actual native personal artifact query unavailable")
        require(result.get("read_only") is True and result.get("loaded_source_pins_verified") is True and
                result.get("personally_owned") is True and result.get("inventory_artifact") is True and
                native_id(result.get("requested_artifact_id"), "returned item", allow_zero=True) == reference and
                native_id(result.get("played_character_id"), "returned item owner") == current.player_id and
                integer(result.get("date_raw"), "returned item date") == current.date_raw,
                "Native item read crossed identity/date/source")
        return result

    def open_inventory(self, target: str) -> None:
        if self.original_action_unknown:
            raise CaseBlocked("Original action result is unknown; no second inventory-opening intent is permitted")
        item = self.observe_item(target)
        if item.get("inventory_view_available") is True and item.get("inventory_view_visible") is True:
            return
        require(item.get("inventory_view_visible") is False, "Actual ITEM does not prove a closed inventory view")
        self.original_action_unknown = True
        try:
            submitted = self.call(OPEN)
        except CaseCallUnavailable as failure:
            # This exact pinned Python guard raises before its native frame,
            # once claim or dispatch (source lines25-49). A bare ACK/error from
            # any other stage cannot authorize a second opening route.
            if failure.tool != OPEN or str(failure) != REFUSAL or failure.result_present or failure.record is None:
                raise
            source = pre_intent_source(self.client.frozen)
            self.original_action_unknown = False
            frame = self.current()
            request: InventoryOpenRequest = {"schema": "living-artifacts-inventory-gui-open-request-v1", "run_id": self.run_id,
                "machine_id": self.machine_id, "pid": frame.pid, "connection_generation": frame.generation_decimal,
                "actor_character_id": frame.player_id, "date_raw": frame.date_raw, "target_artifact_id": target,
                "original_native_refusal": failure.record, "refusal_source": source, "original_open_intent_not_admitted": True,
                "action": "open-inventory-only", "required_route": "desktop_coordinate_map", "business_pass": False}
            self.refs.append(source)
            self.original_action_unknown = True
            response = self.client.root_checkpoint(f"inventory-gui-open-{self.sequence:04d}", object_value(request), reserve=180)
            opened = parse_opening(response, frame=frame, run_id=self.run_id, machine_id=self.machine_id,
                reviewer=self.client.operator_reviewer, target=target, refusal=failure.record)
            self.refs.extend(opened.evidence)
            if opened.status != "completed":
                self.original_action_unknown = opened.submitted
                raise CaseBlocked(opened.reason or "Original GUI inventory opening did not complete")
            self.snapshot()
            actual = self.observe_item(target)
            require(self.current().date_raw == frame.date_raw and actual.get("inventory_view_available") is True and
                    actual.get("inventory_view_visible") is True, "Independent current ITEM did not confirm GUI inventory visibility")
            self.original_action_unknown = False
            return
        if submitted.get("once_intent_consumed") is not True:
            raise CaseBlocked("Original inventory-open intent was not admitted")
        sequence = integer(field(submitted, "intent_sequence"), "actual inventory sequence", 1)
        for _ in range(3):
            after = self.call(OPEN_POST, {"expected_intent_sequence": sequence})
            if after.get("desired_window_observed") is True:
                verify = self.observe_item(target)
                require(verify.get("inventory_view_available") is True and verify.get("inventory_view_visible") is True,
                        "Independent native ITEM did not confirm inventory opening")
                self.original_action_unknown = False
                return
        raise CaseBlocked("Original inventory-open result unknown; do not submit again")

    def equip(self, target: str, desired: bool) -> Object:
        self.open_inventory(target)
        before = self.observe_item(target)
        require(before.get("native_equipped_observed") is True and type(before.get("equipped")) is bool and before["equipped"] is not desired,
                "Native initial equipment predicate differs; no toggle or borrowed action is permitted")
        slot_value = before["effective_slot_index"] if desired else before["equipped_slot_index"]
        slot = integer(slot_value, "actual destination slot", 0, 63)
        replacement = before["replacing_artifact_id"] if desired else None
        if replacement is not None:
            replacement = native_id(replacement, "actual replacing item", allow_zero=True)
        permission = before["can_equip_in_effective_slot"] if desired else before["can_unequip"]
        if permission is not True:
            raise CaseBlocked("Original native equipment permission is unavailable or refused")
        self.original_action_unknown = True
        submitted = self.call(EQUIP, {"artifact_id": int(target), "desired_equipped": desired, "expected_slot_index": slot,
                                     "expected_replacing_artifact_id": replacement, "policy_positive": True})
        require(submitted.get("once_intent_consumed") is True, "No original owned once-only equip intent was consumed")
        sequence = integer(field(submitted, "intent_sequence"), "original equip sequence", 1)
        for _ in range(3):
            post = self.call(EQUIP_POST, {"artifact_id": int(target), "expected_intent_sequence": sequence})
            if post.get("desired_inventory_state_observed") is True:
                actual = self.observe_item(target)
                require(actual.get("equipped") is desired and (actual.get("equipped_slot_index") == slot if desired else actual.get("equipped_slot_index") is None),
                        "Independent native equipment read does not confirm the original action")
                self.original_action_unknown = False
                return {"artifact_id": target, "desired_equipped": desired, "intent_sequence_decimal": str(sequence),
                        "native_owner_slot_observed": True, "actor_net_modifier_attribution": False}
        raise CaseBlocked("Original equip intent remains unknown; preserve it without replay")

    def continue_native_interruption(self) -> None:
        seen: set[tuple[str, int]] = set()
        for _ in range(16):
            frame = self.last_frame
            active = field(frame, "active_event")
            pending = field(frame, "pending_character_interaction")
            if active is None and pending is None:
                return
            kind: Literal["event", "interaction"] = "event" if active is not None else "interaction"
            selected = active if active is not None else pending
            identity = (kind, integer(field(selected, "instance_id"), "actual native interruption", 1))
            require(identity not in seen, "Original native interruption remains; never replay its choice")
            seen.add(identity)
            before = self.current()
            self.interruption_sequence += 1
            if self.last_native_record is None:
                raise CaseBlocked("Original interruption frame source is unavailable")
            request: NativeInterruptionRequest = {
                "schema":"living-artifacts-native-interruption-request-v1", "run_id":self.run_id,
                "machine_id":self.machine_id, "kind":kind, "instance_id":identity[1], "date_raw":before.date_raw,
                "original_native_frame_record":self.last_native_record, "existing_specialist_policy_priority":True,
                "unknown_event_first_displayed_or_interaction_legal_left":True, "no_replay_of_unknown":True}
            response = self.client.root_checkpoint(f"xalw-native-interruption-{self.interruption_sequence:04d}",
                object_value(request), reserve=180)
            parse_completed_interruption(response, request=request, reviewer=self.client.operator_reviewer)
            self.snapshot()
            require(self.current().date_raw == before.date_raw, "Root interruption handling changed the paused date")
        raise CaseBlocked("Finite native interruption handling budget reached")

    def management_choice(self, event_key: str, option_key: str) -> ManagementChoice:
        active = field(self.last_frame, "active_event")
        if active is None:
            raise CaseBlocked("The expected real management event is absent")
        instance = integer(field(active, "instance_id"), "actual management instance", 1, 2**31 - 1)
        context = self.call("ck3_query_current_event_window_context_v1", {"event_instance_id": instance})
        require(integer(field(field(self.last_frame, "active_event"), "instance_id"), "retained management instance", 1) == instance,
                "Actual management window changed during the native query")
        return management_choice(context, frame=self.current(), instance_id=instance, event_key=event_key, option_key=option_key)

    def select_management(self, event_key: str, option_key: str, *, next_event: str | None, next_option: str = "xalw.10.close") -> None:
        if self.original_action_unknown:
            raise CaseBlocked("An original management action remains unknown; never replay")
        choice = self.management_choice(event_key, option_key)
        before = self.current()
        self.refs.append(write_once(self.client.output / f"management-choice-{self.sequence:04d}.json", {
            "run_id": self.run_id, "machine_id": self.machine_id, "event_key": choice.event_key,
            "option_key": choice.option_key, "instance_id": choice.instance_id, "native_option_index": choice.native_option_index,
            "rendered_index": choice.rendered_index, "resolved_name": choice.resolved_name, "date_raw": before.date_raw,
            "source_option_derived_from_frozen_generator": True, "business_pass": False}))
        self.original_action_unknown = True
        self.call("ck3_select_event_option", choice.arguments())
        self.snapshot()
        require(self.current().date_raw == before.date_raw, "Management choice changed the paused date")
        if next_event is None:
            require(field(self.last_frame, "active_event") is None, "Original management event is still present")
        else:
            require(next_event != event_key, "Next management definition must independently replace the original")
            self.management_choice(next_event, next_option)
        self.original_action_unknown = False

    def open_management(self, target: str) -> None:
        if self.original_action_unknown:
            raise CaseBlocked("Original action unknown; management cannot be opened")
        self.snapshot()
        self.continue_native_interruption()
        before = self.current()
        decimal_id(target, "management target", allow_zero=True)
        self.original_action_unknown = True
        opened = self.call(DECISIONS_OPEN)
        require(opened.get("schema") == "ck3-ingame-decisions-open-v1" and opened.get("postcondition_verified") is True and
                opened.get("verification_pending") is False, "Actual Decisions visibility was not independently confirmed")
        selected = self.call(DECISION_SELECT, {"decision_key": "xalw_manage_decision"})
        require(selected.get("schema") == "ck3-ingame-decision-item-action-v1" and selected.get("action") == "select" and
                selected.get("decision_key") == "xalw_manage_decision" and selected.get("postcondition_verified") is True,
                "Actual player management decision detail was not independently confirmed")
        confirmed = self.call(DECISION_CONFIRM, {"decision_key": "xalw_manage_decision", "expected_outcome": "event_window",
                                               "expected_event_definition_key": "xalw.12"})
        require(confirmed.get("schema") == "ck3-ingame-decision-outcome-confirm-v1" and confirmed.get("postcondition_verified") is True and
                confirmed.get("verification_pending") is False and confirmed.get("expected_event_definition_key") == "xalw.12",
                "Original management confirmation lacks its actual event outcome")
        self.snapshot()
        require(self.current().date_raw == before.date_raw, "Management opening changed the paused date")
        self.management_choice("xalw.12", "xalw.12.open")
        self.original_action_unknown = False
        self.select_management("xalw.12", "xalw.12.open", next_event="xalw.10")

    def advance_one(self) -> None:
        if self.days >= self.contract.maximum_days:
            raise CaseBlocked("Finite declared natural-day budget reached")
        self.continue_native_interruption()
        self.budget(3)
        row = self.client.advance_day(timeout=float(self.contract.day_timeout), allow_event_boundary=True)
        self.calls += 3
        result = field(row, "result")
        after = field(result, "after")
        self.bind(after)
        self.snapshot()
        if self.start is None:
            raise CaseBlocked("Native opening frame absent")
        self.days = (self.current().date_raw - self.start.date_raw) // 24
        self.continue_native_interruption()


def _check(case_id: str, status: Literal["PASS", "FAIL", "BLOCKED"], reason: str | None, refs: list[Pin], observed: Object) -> CheckResult:
    return {"case_id": case_id, "status": status, "evidence_scope": "fixture_live", "reason": reason,
            "evidence": list(refs), "observed": observed}


def run_case(context: object, client: object) -> Object:
    contract = validate_contract(context)
    require(isinstance(client, CasePort), "The real public CaseClient interface is required")
    if not isinstance(client, CasePort):
        raise ValueError("Actual public CaseClient unavailable")
    session = Session(context, client, contract)
    checks: list[CheckResult] = []
    active_check = "CORE-NATIVE-EQUIP-01"
    error: str | None = None
    try:
        session.refs.extend(_prepared_sources(context, client.state))
        session.snapshot()
        initial, initial_ref = session.observer(None)
        inputs = session.last_saved_inputs
        if inputs is None:
            raise CaseBlocked("Actual saved fixture input references are unavailable")
        target_owner, target = inputs.player_id, inputs.target_id
        input_bindings: dict[str, tuple[str, str]] = {"target": (target_owner, target)}
        for item in inputs.artifacts:
            if item.artifact_id != target:
                require(item.rarity not in input_bindings, "Actual saved material rarities are not unique")
                input_bindings[item.rarity] = item.owner_id, item.artifact_id
        require(set(input_bindings) == {"target", "common", "masterwork", "famed", "illustrious"} and
                target_owner == str(session.current().player_id) and all(owner == target_owner for owner, _ in input_bindings.values()),
                "Actual saved fixture inputs do not belong to the native player")
        target_item = next(item for item in inputs.artifacts if item.artifact_id == target)
        require("xalw_diet" in target_item.variables and target_item.variables["xalw_diet"].flag == "armor" and
                all(item.artifact_type == "sword" for item in inputs.artifacts if item.artifact_id != target),
                "The actual target diet and four material types must prove the non-diet feeding precondition")
        require(not initial.equipped and (initial.level, initial.xp, initial.growth_sequence) == (1, 92, 0),
                "Observed initial inputs differ from frozen G01 precondition")
        require(initial.date_literal == "1066.9.15", "This source-bound Robert case must start at actual saved 1066.9.15")
        actual = session.observe_item(target)
        owned = {str(native_id(item, "owned input artifact", allow_zero=True)) for item in array(field(actual, "owned_ids"), "actual owned inventory")}
        require({item[1] for item in input_bindings.values()} <= owned, "Native actual inventory lacks one of the five observed inputs")
        equipment = session.equip(target, True)
        checks.append(_check(active_check, "PASS", None, session.refs, equipment))
        active_check = "LW-G01"
        before = initial
        current = initial
        # The first actual monthly boundary after the pinned Sep15 bookmark is
        # Oct1, sixteen real public daily advances. Save only at checkpoints.
        growth_date = session.current().date_raw + 16 * 24
        while session.current().date_raw < growth_date:
            session.advance_one()
            require(session.current().date_raw <= growth_date, "Actual progression overshot the pinned monthly observation")
            native = session.observe_item(target)
            require(native.get("equipped") is True, "Actual target ceased being equipped during G01")
        current, _ = session.observer(target)
        require(current.date_literal == "1066.10.1" and current.month == before.month + 1,
                "Actual saved/native daily progression did not reach the first monthly boundary")
        if (current.level, current.xp, current.growth_sequence) != (2, 0, 1):
            raise CaseFailed("Actual +8 monthly G01 did not automatically resolve 1/92 to 2/0 with one growth")
        checks.append(_check(active_check, "PASS", None, session.refs, {"before": before.to_json(), "after": current.to_json(),
                              "growth_notification_was_not_opened": True, "native_equipped_crosscheck": True}))
        active_check = "CORE-UNEQUIP-01"
        unequip = session.equip(target, False)
        frozen = current
        unequipped_date = session.current().date_raw + 31 * 24
        while session.current().date_raw < unequipped_date:
            session.advance_one()
            require(session.current().date_raw <= unequipped_date, "Actual progression overshot the unequipped monthly observation")
            native = session.observe_item(target)
            require(native.get("equipped") is False, "Native equipment predicate changed during unequipped month")
        current, _ = session.observer(target)
        require(current.date_literal == "1066.11.1" and current.month == frozen.month + 1, "Actual saved unequipped month boundary differs")
        if (current.level, current.xp, current.growth_sequence) != (frozen.level, frozen.xp, frozen.growth_sequence):
            raise CaseFailed("Unequipped artifact gained XP or evolved during an actual unoccupied month")
        checks.append(_check(active_check, "PASS", None, session.refs, {"native_unequip": unequip, "before": frozen.to_json(),
                              "after": current.to_json(), "scope": "monthly-XP-and-evolution-stop-only; aggregate modifiers require separate evidence"}))
        active_check = "CORE-FEED-01"
        session.equip(target, True)
        session.open_management(target)
        feeding_date = session.current().date_raw
        before_feed = current
        consumed: set[Rarity] = set()
        feed_rows: list[Object] = []
        for rarity, experience in FEEDING_XP.items():
            session.select_management("xalw.10", f"xalw.10.feed_{rarity}", next_event="xalw.11", next_option="xalw.11.confirm")
            session.select_management("xalw.11", "xalw.11.confirm", next_event="xalw.10")
            native = session.observe_item(target)
            owned = {str(native_id(item, "post-feed owned artifact", allow_zero=True)) for item in array(field(native, "owned_ids"), "post-feed inventory")}
            consumed.add(rarity)
            require(all(input_bindings[eaten][1] not in owned for eaten in consumed), "A supposedly consumed material remains in actual native inventory")
            require(all(input_bindings[remaining][1] in owned for remaining in FEEDING_XP if remaining not in consumed),
                    "A different material disappeared during feeding")
            expected_level, expected_xp = before_feed.level, before_feed.xp + experience
            expected_growth = before_feed.growth_sequence
            while expected_xp >= 100 * expected_level:
                expected_xp -= 100 * expected_level
                expected_level += 1
                expected_growth += 1
            current, _ = session.observer(target, expected_material_rarities=tuple(item for item in FEEDING_XP if item not in consumed))
            require(session.current().date_raw == feeding_date and current.equipped and
                    (current.level, current.xp, current.growth_sequence) == (expected_level, expected_xp, expected_growth),
                    "Actual saved feeding XP/automatic level sequence differs at the same paused date")
            feed_rows.append({"rarity": rarity, "material_id": input_bindings[rarity][1], "base_experience": experience,
                              "before": before_feed.to_json(), "after": current.to_json(), "native_material_absent": True})
            before_feed = current
        session.select_management("xalw.10", "xalw.10.close", next_event=None)
        checks.append(_check(active_check, "PASS", None, session.refs, {"feedings": json_value(feed_rows), "same_paused_date": feeding_date,
            "four_actual_native_rarities": True, "no_game_day_or_cooldown_wait": True, "fixture_feed_submitted": False}))
    except CaseFailed as failure:
        error = str(failure)
        checks.append(_check(active_check, "FAIL", error, session.refs, {}))
    except (CaseBlocked, ValueError, OSError, TimeoutError) as failure:
        error = type(failure).__name__ + ": " + str(failure)
        checks.append(_check(active_check, "BLOCKED", error, session.refs, {}))
    finished = {check["case_id"] for check in checks}
    for required in contract.required_checks:
        if required not in finished:
            checks.append(_check(required, "BLOCKED", "Dependent earlier stage did not complete; no action or business outcome inferred", [], {}))
    complete = all(check["status"] == "PASS" for check in checks)
    result: Object = {"schema": "living-artifacts-core-case-result-v2", "schema_version": 2, "run_id": session.run_id,
        "product": "living-artifacts", "case": "core_continuous", "machine_id": session.machine_id, "observed_at_utc": utc_now(),
        "status": "PASS" if complete else "FAIL" if any(check["status"] == "FAIL" for check in checks) else "BLOCKED",
        "checks": json_value(checks), "deferred_checks": list(contract.deferred_checks), "actual_natural_days": session.days,
        "actual_public_calls_budgeted": session.calls, "original_action_unknown": session.original_action_unknown,
        "case_contract_qualified": complete, "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False,
        "current_native_artifact_variable_query": False, "fixture_getter_log_credit": False,
        "actual_checkpoint_readback_credit": session.first_sample is not None, "error": error,
        "normal_close_owner": "shared entry/CaseClient", "normal_close_pending": True}
    write_once(client.output / RESULT_NAME, result)
    return result


def verify_case(context: object) -> Object:
    contract = validate_contract(context)
    output = Path(text(field(context, "output"), "public output"))
    path = output / RESULT_NAME
    if not path.is_file():
        return {"status": "NOT_RUN", "case_contract_qualified": False, "gui_contract_qualified": False,
                "business_pass": False, "product_release_pass": False}
    result = read(path)
    _prepared_sources(context, Path(text(field(context, "state_dir"), "allocated state")))
    require(result.get("schema") == "living-artifacts-core-case-result-v2" and integer(field(result, "schema_version"), "result schema version", 2, 2) == 2,
            "Actual retained result schema differs")
    require(result["run_id"] == field(context, "run_id") and result["product"] == "living-artifacts" and result["case"] == "core_continuous",
            "Actual retained result crossed the public run/product/case")
    seen: set[str] = set()
    passed: set[str] = set()
    for check_value in array(result["checks"], "actual checks"):
        check = mapping(check_value, "check")
        require(set(check) == {"case_id", "status", "evidence_scope", "reason", "evidence", "observed"}, "Actual check field contract differs")
        check_id = text(check["case_id"], "actual check ID")
        require(check_id in contract.required_checks and check_id not in seen, "Unknown or duplicate actual check")
        seen.add(check_id)
        require(check["status"] in ("PASS", "FAIL", "BLOCKED") and check["evidence_scope"] == "fixture_live", "Actual check status/scope differs")
        if check["status"] == "PASS":
            passed.add(check_id)
            require(check["reason"] is None and bool(array(check["evidence"], "PASS evidence")), "PASS requires real retained evidence")
        else:
            text(check["reason"], "specific incomplete-check reason")
        for reference_value in array(field(check, "evidence"), "check evidence"):
            reference = mapping(reference_value, "evidence pin")
            require(set(reference) == {"path", "bytes", "sha256"} and
                    pin(Path(text(field(reference, "path"), "evidence path"))) == reference, "Original business evidence bytes changed")
    require(seen == set(contract.required_checks), "Missing declared actual checks")
    complete = passed == seen
    failed = any(field(check, "status") == "FAIL" for check in array(result["checks"], "actual checks"))
    require(result["status"] == ("PASS" if complete else "FAIL" if failed else "BLOCKED"), "Actual status contradicts retained check outcomes")
    require(result["case_contract_qualified"] is complete and result["business_pass"] is False and result["product_release_pass"] is False and
            result["gui_contract_qualified"] is False and result["deferred_checks"] == list(contract.deferred_checks),
            "Do not promote partial core observations to full product, GUI, or publication acceptance")
    return result
