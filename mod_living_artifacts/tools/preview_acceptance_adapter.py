"""Short, zero-day player preview case; no NPC or suppression-timer credit.

The shared Session owns native actions and Save/Root transport. A direct PNG
review is evidence of displayed text only; independent saved/native observations
decide material consumption and XP. Shared host still owns normal Quit.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
from pathlib import Path
import re
import sys
from typing import Literal, TypedDict

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import acceptance_adapter as core
from acceptance_contract import CasePort, CheckResult, Frame, Object, Pin, array, decimal_id, field, integer, json_value, mapping, native_id, object_value, pin, read, require, text, utc_now, write_once
from checkpoint_artifacts import SavedInputs
from checkpoint_callback import CheckpointSample, checked_pin, verify_readback
from checkpoint_producer import deadline_seconds, declared_pin, raw_object, stamp
from inventory_gui_contract import png_size
from living_artifacts_model import FEEDING_XP, Rarity
from management_event_contract import management_choice, source_option_index
from prepare_fixture import emit_fixture

CONTRACT_NAME = "feeding_preview.contract.json"
RESULT_NAME = "living-artifacts-preview-result.json"
CHECKS = ("PREVIEW-FOUR-RARITIES", "PREVIEW-CANCEL-01", "PREVIEW-TRANSACTIONS-01", "PREVIEW-MOD-SCRIPT-LOG-01")
SOURCES = ("preview_acceptance_adapter.py", "acceptance_adapter.py", "acceptance_contract.py", "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py", "checkpoint_callback.py", "checkpoint_artifacts.py", "checkpoint_producer.py", "startup_actor_binding.py", "management_event_contract.py", "inventory_gui_contract.py", "native_interruption_contract.py")


class PreviewFields(TypedDict):
    run_id: str
    machine_id: str
    pid: int
    connection_generation: str
    actor_character_id: int
    date_raw: int
    event_definition_key: Literal["xalw.11"]
    event_instance_id: int
    target_artifact_id: str
    material_artifact_id: str
    rarity: Rarity
    expected_base_xp: int
    expected_preview_xp: int
    native_event_record: Pin
    requested_at_utc: str
    review_method: Literal["direct-original-png-no-ocr"]
    business_pass: Literal[False]


class PreviewRequest(PreviewFields):
    schema: Literal["living-artifacts-feeding-preview-request-v1"]


class RootPreviewRequest(PreviewRequest):
    original_hold_deadline: float
    reserve_seconds: int
    operator_reviewer: str


class PreviewResponse(PreviewFields):
    schema: Literal["living-artifacts-feeding-preview-review-v1"]
    reviewer: str
    status: Literal["reviewed"]
    reviewed_at_utc: str
    screenshot: Pin
    capture: Pin
    displayed_base_xp: int
    displayed_preview_xp: int
    displayed_material_name: str
    root_request: Pin
    direct_reviewed: Literal[True]


class PreviewCaseResult(TypedDict):
    schema: Literal["living-artifacts-preview-case-result-v1"]
    schema_version: Literal[1]
    product: Literal["living-artifacts"]
    case: Literal["feeding_preview"]
    run_id: str
    machine_id: str
    reviewer: str
    observed_at_utc: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    checks: list[CheckResult]
    journal: Pin
    error: str | None
    actual_natural_days: int
    actual_public_calls_budgeted: int
    actual_saved_observations: int
    original_action_unknown: bool
    case_contract_qualified: bool
    gui_contract_qualified: bool
    business_pass: Literal[False]
    product_release_pass: Literal[False]
    normal_close_owner: Literal["shared entry/CaseClient"]
    normal_close_pending: Literal[True]


@dataclass(frozen=True)
class PreviewContract:
    transport: core.Contract
    maximum_checkpoints: int


def _same_json(left: object, right: object) -> bool:
    # Compare the normalized JSON domain, preserving bool/int/float distinctions.
    return json.dumps(json_value(left), sort_keys=True, separators=(",", ":")) == json.dumps(json_value(right), sort_keys=True, separators=(",", ":"))


def validate_contract(context: object) -> PreviewContract:
    require(field(context, "product") == "living-artifacts" and field(context, "case") == "feeding_preview", "Select the real feeding_preview case")
    config = mapping(field(context, "case_contract"), "preview contract")
    require(_same_json(config, read(TOOLS / CONTRACT_NAME)), "Preview contract must equal source-frozen canonical contract")
    integer(config["schema_version"], "preview version", 1, 1)
    integer(config["maximum_direct_reviews"], "direct review cap", 5, 5)
    require(config["whole_product_acceptance_credit"] is False, "Preview case cannot grant release credit")
    spec = field(context, "case_spec")
    declared = {text(item, "declared tool") for item in array(field(spec, "required_mcp_tools"), "tools")}
    require(set(core.REQUIRED_TOOLS) <= declared, "Declare every shared Session tool")
    for key, value in core.REQUIRED_OPT_INS.items():
        require(field(spec, key) is value, "Required original action opt-in missing")
    require(core.ITEM in array(field(spec, "opt_in_read_only_mcp_tools"), "read-only tools"), "Original personal-item read opt-in required")
    return PreviewContract(core.Contract(integer(config["maximum_natural_days"], "preview days", 0, 0),
        integer(config["max_public_calls"], "preview calls", 180, 180), 60, CHECKS,
        tuple(text(item, "deferred check") for item in array(config["deferred_checks"], "deferred"))),
        integer(config["maximum_checkpoints"], "preview save cap", 5, 5))


def _tree(root: Path) -> dict[str, Pin]:
    require(root.is_dir(), "Actual deployment directory required")
    require(not any(path.is_symlink() for path in root.rglob("*")), "Deployment links are not allowed")
    return {path.relative_to(root).as_posix(): pin(path) for path in sorted(root.rglob("*")) if path.is_file()}


def prepare_case(context: object) -> Object:
    validate_contract(context)
    values = mapping(context, "actual preparation")
    output = Path(text(field(values, "output"), "output")).resolve()
    fixture = emit_fixture(output / "external-preview-fixture")
    root = Path(fixture["fixture_root"])
    product = Path(text(field(field(values, "case_inputs"), "product_dir"), "formal staging")).resolve()
    write_once(root / "_case_contract.json", {"product": "living-artifacts", "case": "feeding_preview", "config": field(values, "case_contract"),
        "fixture_emission": fixture, "caller_sources": {name: pin(TOOLS / name) for name in SOURCES}, "contract_source": pin(TOOLS / CONTRACT_NAME),
        "formal_files": _tree(product), "business_pass": False})
    preparation = importlib.import_module("ck3_mod_acceptance_prepare")
    require(isinstance(preparation, core.Preparation), "Shared fixture preparation required")
    if not isinstance(preparation, core.Preparation):
        raise ValueError("Shared fixture preparation unavailable")
    prepared = object_value(preparation.materialize_fixture_profile(values, root, product, field(field(values, "case_inputs"), "plain_configuration")))
    return object_value({"startup": {"mode": "fixture", "state_dir": prepared["state_dir"], "fixture_start_policy": prepared["fixture_start_policy"]},
        "initial_plan": write_once(output / "initial-plan.json", {"steps": []}), "profile_preparation": prepared,
        "fixture_emission": fixture, "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False})


def prepared_sources(context: object, state: Path) -> tuple[Pin, ...]:
    validate_contract(context)
    require(isinstance(state, Path), "Actual allocated Path required")
    require(state.resolve() == Path(text(field(context, "state_dir"), "state")).resolve(), "Preview crossed allocated state")
    root = state / "profile/mod-content/fixture"
    manifest = read(root / "_case_contract.json")
    require(set(manifest) == {"product", "case", "config", "fixture_emission", "caller_sources", "contract_source", "formal_files", "business_pass"} and
        manifest["product"] == "living-artifacts" and manifest["case"] == "feeding_preview" and manifest["business_pass"] is False and
        _same_json(manifest["config"], field(context, "case_contract")), "Preview fixture contract differs")
    callers = mapping(manifest["caller_sources"], "caller source table")
    require(set(callers) == set(SOURCES), "Preview caller closure differs")
    refs = [core._checked_pin(callers[name], "preview caller", TOOLS / name) for name in SOURCES]
    refs.append(core._checked_pin(manifest["contract_source"], "preview contract", TOOLS / CONTRACT_NAME))
    emission = mapping(manifest["fixture_emission"], "existing fixture emission")
    require(emission["input_origin"] == "fixture_generated" and emission["business_acceptance"] == "NOT_ASSESSED" and emission["game_started"] is False,
        "Initial fixture does not grant gameplay credit")
    emitted = mapping(emission["files"], "initial files")
    for deployed, originals, extra in ((root, emitted, {"_case_contract.json"}), (state / "profile/mod-content/product", mapping(manifest["formal_files"], "formal files"), set())):
        require(set(_tree(deployed)) == set(originals) | extra, "Loaded fixture/product closure differs")
        for relative, raw in originals.items():
            original = checked_pin(raw, "original loaded input")
            copied = pin(deployed / relative)
            require((copied["bytes"], copied["sha256"]) == (original["bytes"], original["sha256"]), "Loaded input differs")
            refs.append(copied)
    require(read(state / "profile/dlc_load.json") == {"enabled_mods": ["mod/product.mod", "mod/fixture.mod"], "disabled_dlcs": []}, "Preview mounts only formal product and input fixture")
    refs.extend((pin(root / "_case_contract.json"), pin(state / "profile/dlc_load.json")))
    prepared_pin = checked_pin(field(read(state / "preparation.json"), "preparation"), "shared prepared profile")
    prepared = read(Path(prepared_pin["path"]))
    require(field(prepared, "schema") == "ck3-mod-acceptance-prepared-fixture-v1" and
        Path(text(field(prepared, "state_dir"), "prepared state")).resolve() == state.resolve(), "Shared preparation crossed profile/schema")
    table = mapping(field(prepared, "files"), "shared loaded-file table")
    loaded = {"mod/product.mod", "mod/fixture.mod", "dlc_load.json"}
    loaded.update("mod-content/product/" + relative for relative in mapping(manifest["formal_files"], "formal file closure"))
    loaded.update("mod-content/fixture/" + relative for relative in set(emitted) | {"_case_contract.json"})
    require(loaded <= set(table), "Shared preparation omits a loaded preview input")
    refs.extend(core._checked_pin(table[relative], "shared prepared loaded input", state / "profile" / relative) for relative in sorted(loaded))
    refs.append(prepared_pin)
    return tuple(refs)


def _native_record(reference: object, *, run_id: str, machine_id: str, manifest: object) -> tuple[Frame, dict[str, object]]:
    source = checked_pin(reference, "original native event/frame")
    rows = array(field(raw_object(Path(source["path"])), "rows"), "original native rows")
    require(len(rows) == 1, "One original native row required")
    row = mapping(rows[0], "native row")
    require(row.get("ok") is True and row.get("error") is None, "Successful original native row required")
    snapshot = field(row, "result") if field(field(row, "plan"), "tool") == "ck3_take_snapshot" else field(row, "after_snapshot")
    frame = Frame.parse(snapshot, run_id=run_id, machine_id=machine_id, manifest=manifest)
    return frame, row


def parse_request(value: object, *, manifest: object) -> PreviewRequest:
    row = mapping(value, "preview request")
    require(set(row) == set(PreviewRequest.__required_keys__) and row["schema"] == "living-artifacts-feeding-preview-request-v1" and
        row["event_definition_key"] == "xalw.11" and row["review_method"] == "direct-original-png-no-ocr" and row["business_pass"] is False, "Closed preview request required")
    run, machine = text(row["run_id"], "run"), text(row["machine_id"], "machine")
    frame, original = _native_record(row["native_event_record"], run_id=run, machine_id=machine, manifest=manifest)
    require(field(field(original, "plan"), "tool") == "ck3_query_current_event_window_context_v1", "Actual native event query required")
    instance = integer(row["event_instance_id"], "event instance", 1, 2**31 - 1)
    require(integer(field(field(field(original, "plan"), "args"), "event_instance_id"), "original event query instance", 1, 2**31 - 1) == instance,
        "Original native query requested a different event instance")
    require(integer(row["pid"], "PID", 1) == frame.pid and decimal_id(row["connection_generation"], "generation") == frame.generation_decimal and
        integer(row["actor_character_id"], "actor", 1) == frame.player_id and integer(row["date_raw"], "date", 1) == frame.date_raw, "Preview request crossed native scene")
    management_choice(field(original, "result"), frame=frame, instance_id=instance, event_key="xalw.11", option_key="xalw.11.confirm")
    rarity_text = text(row["rarity"], "shared rarity")
    rarity: Rarity
    if rarity_text == "common":
        rarity = "common"
    elif rarity_text == "masterwork":
        rarity = "masterwork"
    elif rarity_text == "famed":
        rarity = "famed"
    elif rarity_text == "illustrious":
        rarity = "illustrious"
    else:
        raise ValueError("Unknown rarity")
    base = integer(row["expected_base_xp"], "base XP", 1)
    require(base == FEEDING_XP[rarity] and integer(row["expected_preview_xp"], "preview XP", 1) == base, "This case only qualifies non-diet material")
    stamp(row["requested_at_utc"])
    return PreviewRequest(schema="living-artifacts-feeding-preview-request-v1", run_id=run, machine_id=machine, pid=frame.pid,
        connection_generation=frame.generation_decimal, actor_character_id=frame.player_id, date_raw=frame.date_raw,
        event_definition_key="xalw.11", event_instance_id=instance, target_artifact_id=decimal_id(row["target_artifact_id"], "target", allow_zero=True),
        material_artifact_id=decimal_id(row["material_artifact_id"], "material", allow_zero=True), rarity=rarity, expected_base_xp=base,
        expected_preview_xp=base, native_event_record=checked_pin(row["native_event_record"], "event source"), requested_at_utc=text(row["requested_at_utc"], "request UTC"),
        review_method="direct-original-png-no-ocr", business_pass=False)


def _fields(request: PreviewRequest) -> PreviewFields:
    return PreviewFields(run_id=request["run_id"], machine_id=request["machine_id"], pid=request["pid"], connection_generation=request["connection_generation"],
        actor_character_id=request["actor_character_id"], date_raw=request["date_raw"], event_definition_key=request["event_definition_key"],
        event_instance_id=request["event_instance_id"], target_artifact_id=request["target_artifact_id"], material_artifact_id=request["material_artifact_id"],
        rarity=request["rarity"], expected_base_xp=request["expected_base_xp"], expected_preview_xp=request["expected_preview_xp"],
        native_event_record=request["native_event_record"], requested_at_utc=request["requested_at_utc"], review_method=request["review_method"], business_pass=False)


def _root_request(path: Path, *, manifest: object, reviewer: str, reviewed_at_utc: str) -> PreviewRequest:
    require(isinstance(path, Path) and path.is_file(), "Actual public Root awaiting file Path required")
    raw = read(path)
    require(path.name.endswith("-awaiting.json") and set(raw) == set(RootPreviewRequest.__required_keys__) and raw["operator_reviewer"] == reviewer,
        "Actual closed public Root awaiting request/reviewer required")
    reserve = integer(raw["reserve_seconds"], "original normal-Quit reserve", 180)
    require(stamp(reviewed_at_utc).timestamp() + reserve < deadline_seconds(raw["original_hold_deadline"]), "Direct review consumed original normal-Quit reserve")
    return parse_request({key: raw[key] for key in PreviewRequest.__required_keys__}, manifest=manifest)


def produce_preview_review(request_path: Path, *, manifest: object, reviewer: str, reviewed_at_utc: str, screenshot: Path, capture: Path,
                           displayed_base_xp: int, displayed_preview_xp: int, displayed_material_name: str, direct_reviewed: bool) -> PreviewResponse:
    """Use the actual direct-review operation time, not later dispatch time."""
    reviewed, producing = text(reviewed_at_utc, "actual direct-review operation UTC"), utc_now()
    require(stamp(reviewed) <= stamp(producing), "Actual direct-review UTC cannot be in the future")
    require(direct_reviewed is True, "Root must explicitly attest direct original-PNG review")
    require(isinstance(screenshot, Path) and isinstance(capture, Path) and screenshot.is_file() and capture.is_file(), "Actual original PNG and capture Paths required")
    # The original hold/normal-Quit reserve remains a current production guard.
    # An earlier review operation cannot authorize writing past that deadline.
    body = _root_request(request_path, manifest=manifest, reviewer=text(reviewer, "reviewer"), reviewed_at_utc=producing)
    response = PreviewResponse(**_fields(body), schema="living-artifacts-feeding-preview-review-v1", reviewer=text(reviewer, "reviewer"), status="reviewed", reviewed_at_utc=reviewed,
        screenshot=pin(screenshot), capture=pin(capture), displayed_base_xp=integer(displayed_base_xp, "observed base XP"),
        displayed_preview_xp=integer(displayed_preview_xp, "observed preview XP"), displayed_material_name=text(displayed_material_name, "observed material name"), root_request=pin(request_path), direct_reviewed=True)
    _review_artifacts(response)
    return response


def _review_artifacts(row: PreviewResponse) -> None:
    image, capture = checked_pin(row["screenshot"], "original PNG"), checked_pin(row["capture"], "capture receipt")
    actual = read(Path(capture["path"]))
    require(field(actual, "machine_id") == row["machine_id"] and field(actual, "gameplay_pass_claimed") is False and
        integer(field(field(actual, "foreground"), "pid"), "capture foreground PID", 1) == row["pid"], "Capture crossed machine/process or grants business credit")
    saved_image = mapping(field(actual, "image"), "captured image")
    require(checked_pin({key: saved_image[key] for key in ("path", "bytes", "sha256")}, "capture PNG") == image, "Capture references another PNG")
    size = png_size(Path(image["path"]))
    for value in (saved_image, mapping(field(actual, "desktop"), "captured desktop")):
        require((integer(value["width"], "capture width", 1), integer(value["height"], "capture height", 1)) == size, "Original PNG geometry differs")
    requested, captured, reviewed = stamp(row["requested_at_utc"]), stamp(field(actual, "observed_at_utc")), stamp(row["reviewed_at_utc"])
    # Human review has no business request-age deadline. The original scene
    # hold/close reserve and independent same-event native query own freshness.
    require(requested <= captured <= reviewed, "PNG is outside this event review chronology")


def parse_review(value: object, *, request: object, manifest: object, reviewer: str) -> PreviewResponse:
    expected = parse_request(request, manifest=manifest)
    row = mapping(value, "Root preview review")
    require(set(row) == set(PreviewResponse.__required_keys__), "Closed preview review fields required")
    parse_request({**{key: row[key] for key in PreviewFields.__required_keys__}, "schema": "living-artifacts-feeding-preview-request-v1"}, manifest=manifest)
    require(all(row[key] == val and type(row[key]) is type(val) for key, val in _fields(expected).items()) and
        row["schema"] == "living-artifacts-feeding-preview-review-v1" and row["reviewer"] == reviewer and row["status"] == "reviewed" and row["direct_reviewed"] is True, "Closed preview review crossed original request/reviewer")
    root_pin = checked_pin(row["root_request"], "actual Root awaiting request")
    require(_root_request(Path(root_pin["path"]), manifest=manifest, reviewer=reviewer, reviewed_at_utc=text(row["reviewed_at_utc"], "review UTC")) == expected, "Review belongs to a different original Root request")
    result = PreviewResponse(**_fields(expected), schema="living-artifacts-feeding-preview-review-v1", reviewer=text(row["reviewer"], "reviewer"), status="reviewed", reviewed_at_utc=text(row["reviewed_at_utc"], "review UTC"),
        screenshot=checked_pin(row["screenshot"], "PNG"), capture=checked_pin(row["capture"], "capture"),
        displayed_base_xp=integer(row["displayed_base_xp"], "displayed base XP"), displayed_preview_xp=integer(row["displayed_preview_xp"], "displayed XP"),
        displayed_material_name=text(row["displayed_material_name"], "displayed material"), root_request=root_pin, direct_reviewed=True)
    _review_artifacts(result)
    if (result["displayed_base_xp"], result["displayed_preview_xp"]) != (expected["expected_base_xp"], expected["expected_preview_xp"]):
        raise core.CaseFailed("Direct original PNG review shows incorrect feeding XP")
    return result


def scan_error_log(raw: bytes) -> Object:
    """Scan every record; static reachability messages remain separately counted."""
    require(type(raw) is bytes, "Original full log bytes required")
    records: list[str] = []
    for line in raw.decode("utf-8-sig", errors="strict").splitlines():
        if re.match(r"^\[\d\d:\d\d:\d\d\]", line):
            records.append(line)
        elif records:
            records[-1] += "\n" + line
        else:
            require(not line.strip(), "Unframed original error-log content")
    static = [row for row in records if re.search(r"\[jomini_effect\.cpp:(?:1146|1162)\]: (?:Variable|Event target) '[^']+' is (?:set but is never used|used but is never set)\.", row) is not None]
    business = [row for row in records if row not in static and ("xalw_" in row or "xalw." in row)]
    return object_value({"full_bytes": len(raw), "record_count": len(records), "static_diagnostic_count": len(static), "mod_runtime_error_count": len(business),
        "mod_runtime_errors": business, "unattributed_record_count": len(records) - len(static) - len(business),
        "scope": "All current scene mod script/UI errors; unrelated/unattributed diagnostics do not become whole-log-clean credit"})


def _owned(value: object, *, frame: Frame) -> set[str]:
    require(field(value, "available") is True and field(value, "read_only") is True and field(value, "loaded_source_pins_verified") is True and
        field(value, "personally_owned") is True and field(value, "inventory_artifact") is True and
        integer(field(value, "played_character_id"), "item actor", 1) == frame.player_id and integer(field(value, "date_raw"), "item date", 1) == frame.date_raw,
        "Original inventory read crossed scene/source")
    return {str(native_id(item, "owned material", allow_zero=True)) for item in array(field(value, "owned_ids"), "native inventory")}


def _last_call_record(session: core.Session) -> Pin:
    # last_native_record intentionally denotes the original snapshot, not calls.
    return pin(session.client.output / f"xalw-core-{session.sequence:04d}.actual-results.json")


def _cancel_action(references: list[Pin]) -> Pin:
    matches: list[Pin] = []
    for reference in references:
        if reference["path"].endswith(".actual-results.json"):
            for raw in array(field(raw_object(Path(reference["path"])), "rows"), "action rows"):
                row = mapping(raw, "action row")
                if field(field(row, "plan"), "tool") == "ck3_select_event_option":
                    matches.append(reference)
    require(len(matches) == 1, "One original cancel submission required")
    return matches[0]


def _observe(session: core.Session, target: str | None, remaining: tuple[Rarity, ...]) -> tuple[CheckpointSample, SavedInputs, Pin, set[str]]:
    readback = session.checkpoint_readback(target)
    original = session.last_native_record
    require(original is not None, "Original Save native record missing")
    inputs, refs = verify_readback(readback.response, run_id=session.run_id, machine_id=session.machine_id,
        reviewer=session.client.operator_reviewer, frame=readback.frame, source_save=readback.source_save, expected_material_rarities=remaining)
    native = session.observe_item(inputs.target_id)
    require(type(native["equipped"]) is bool, "Actual equipment predicate required")
    item = next(item for item in inputs.artifacts if item.artifact_id == inputs.target_id)
    sample = CheckpointSample.from_saved(item, inputs, native_equipped=native["equipped"] is True)
    reference = write_once(session.client.output / f"preview-checkpoint-{session.checkpoint_observations:02d}.json", {
        "run_id": session.run_id, "machine_id": session.machine_id, "reviewer": session.client.operator_reviewer,
        "original_save_native": original, "source_save": readback.source_save, "response": readback.response,
        "item_native": _last_call_record(session), "sample": sample.to_json(), "remaining": list(remaining)})
    session.refs.extend((*refs, reference))
    return sample, inputs, reference, _owned(native, frame=session.current())


def _review(session: core.Session, *, target: str, material: str, rarity: Rarity, ordinal: int) -> Pin:
    choice = session.management_choice("xalw.11", "xalw.11.confirm")
    frame = session.current()
    require(session.start is not None and frame.date_raw == session.start.date_raw, "Zero-day preview calendar changed; no feeding permitted")
    request = PreviewRequest(schema="living-artifacts-feeding-preview-request-v1", run_id=session.run_id, machine_id=session.machine_id,
        pid=frame.pid, connection_generation=frame.generation_decimal, actor_character_id=frame.player_id, date_raw=frame.date_raw,
        event_definition_key="xalw.11", event_instance_id=choice.instance_id, target_artifact_id=target, material_artifact_id=material,
        rarity=rarity, expected_base_xp=FEEDING_XP[rarity], expected_preview_xp=FEEDING_XP[rarity], native_event_record=_last_call_record(session),
        requested_at_utc=utc_now(), review_method="direct-original-png-no-ocr", business_pass=False)
    response = session.client.root_checkpoint(f"feeding-preview-review-{ordinal:02d}", object_value(request), reserve=180)
    parsed = parse_review(response, request=request, manifest=session.client.manifest, reviewer=session.client.operator_reviewer)
    after = session.management_choice("xalw.11", "xalw.11.confirm")
    require(after.instance_id == choice.instance_id and session.current().date_raw == frame.date_raw, "Reviewed original event changed; do not submit another intent")
    result = write_once(session.client.output / f"preview-review-{ordinal:02d}.json", {"request": request, "response": parsed, "after_native": _last_call_record(session)})
    session.refs.extend((parsed["screenshot"], parsed["capture"], result))
    return result


def evaluate(context: object, *, manifest: object, reviewer: str, journal: object) -> Object:
    """Re-read actual files and recompute; a Root statement never proves feeding."""
    config = validate_contract(context)
    values = mapping(journal, "preview evidence journal")
    require(set(values) == {"checkpoints", "reviews", "cancellation", "log"}, "Closed preview evidence journal required")
    run, machine = text(field(context, "run_id"), "run"), text(field(manifest, "machine_id"), "machine")
    refs = array(field(values, "checkpoints"), "saved observations")
    require(len(refs) == config.maximum_checkpoints, "Exactly initial plus four actual Save readbacks required")
    samples: list[CheckpointSample] = []
    inventories: list[set[str]] = []
    inputs: list[SavedInputs] = []
    first: Frame | None = None
    for index, reference in enumerate(refs):
        record = read(Path(checked_pin(reference, "saved observation")["path"]))
        require(set(record) == {"run_id", "machine_id", "reviewer", "original_save_native", "source_save", "response", "item_native", "sample", "remaining"} and
            record["run_id"] == run and record["machine_id"] == machine and record["reviewer"] == reviewer, "Saved observation crossed scene/reviewer")
        frame, _ = _native_record(record["original_save_native"], run_id=run, machine_id=machine, manifest=manifest)
        if first is None:
            first = frame
        require((frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) == (first.pid, first.player_id, first.generation_decimal, first.date_raw), "Preview must stay on the identical paused scene/date")
        remaining = tuple(FEEDING_XP)[index:]
        require(record["remaining"] == list(remaining), "Remaining rarity observation differs")
        saved, _ = verify_readback(record["response"], run_id=run, machine_id=machine, reviewer=reviewer, frame=frame,
            source_save=declared_pin(record["source_save"], "original Save"), expected_material_rarities=remaining)
        item_frame, row = _native_record(record["item_native"], run_id=run, machine_id=machine, manifest=manifest)
        require((item_frame.pid, item_frame.player_id, item_frame.generation_decimal, item_frame.date_raw) == (frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) and
            field(field(row, "plan"), "tool") == core.ITEM, "Independent original item read required")
        native = field(row, "result")
        require(type(field(native, "equipped")) is bool and native_id(field(native, "requested_artifact_id"), "observed target", allow_zero=True) == int(saved.target_id), "Native target/equipment differs")
        actual = CheckpointSample.from_saved(next(item for item in saved.artifacts if item.artifact_id == saved.target_id), saved, native_equipped=field(native, "equipped") is True)
        require(_same_json(record["sample"], actual.to_json()), "Retained projection differs from actual saved input")
        samples.append(actual); inputs.append(saved); inventories.append(_owned(native, frame=item_frame))
    initial = samples[0]
    if first is None:
        raise ValueError("Initial saved native frame missing")
    require((initial.level, initial.xp, initial.pending, initial.growth_sequence, initial.equipped, initial.date_literal) == (1, 92, 0, 0, False, "1066.9.15"), "Existing core fixture initial state differs")
    target = inputs[0].target_id
    target_item = next(item for item in inputs[0].artifacts if item.artifact_id == target)
    require(target_item.variables["xalw_diet"].flag == "armor", "Non-diet target precondition missing")
    materials = {item.rarity: item.artifact_id for item in inputs[0].artifacts if item.artifact_id != target and item.artifact_type == "sword"}
    require(set(materials) == set(FEEDING_XP) and {target, *materials.values()} <= inventories[0], "Four actual native/saved material identities required")
    review_refs = array(field(values, "reviews"), "direct PNG reviews")
    require(len(review_refs) == 5, "Canceled common preview plus four actual feeding previews required")
    instances: set[int] = set()
    for reference, rarity in zip(review_refs, ("common", *FEEDING_XP), strict=True):
        record = read(Path(checked_pin(reference, "original review envelope")["path"]))
        require(set(record) == {"request", "response", "after_native"}, "Closed review envelope required")
        request = parse_request(record["request"], manifest=manifest)
        require(request["run_id"] == run and request["machine_id"] == machine and request["date_raw"] == first.date_raw and request["pid"] == first.pid and
            request["actor_character_id"] == first.player_id and request["connection_generation"] == first.generation_decimal and
            request["rarity"] == rarity and request["target_artifact_id"] == target and request["material_artifact_id"] == materials[rarity], "Review crossed actual material/scene")
        parse_review(record["response"], request=request, manifest=manifest, reviewer=reviewer)
        post_frame, post = _native_record(record["after_native"], run_id=run, machine_id=machine, manifest=manifest)
        require((post_frame.pid, post_frame.player_id, post_frame.generation_decimal, post_frame.date_raw) == (first.pid, first.player_id, first.generation_decimal, first.date_raw) and
            field(field(post, "plan"), "tool") == "ck3_query_current_event_window_context_v1", "Post-review original event query crossed scene")
        management_choice(field(post, "result"), frame=post_frame, instance_id=request["event_instance_id"], event_key="xalw.11", option_key="xalw.11.confirm")
        require(request["event_instance_id"] not in instances, "A closed event review cannot be reused")
        instances.add(request["event_instance_id"])
    cancellation = read(Path(checked_pin(field(values, "cancellation"), "cancel evidence")["path"]))
    require(set(cancellation) == {"before_item", "after_item", "management_after", "action_native", "material_id"} and cancellation["material_id"] == materials["common"], "Cancel evidence differs")
    first_review = read(Path(checked_pin(review_refs[0], "canceled original review")["path"]))
    canceled_request = parse_request(first_review["request"], manifest=manifest)
    cancel_frame, action = _native_record(cancellation["action_native"], run_id=run, machine_id=machine, manifest=manifest)
    require((cancel_frame.pid, cancel_frame.player_id, cancel_frame.generation_decimal, cancel_frame.date_raw) == (first.pid, first.player_id, first.generation_decimal, first.date_raw) and
        field(field(action, "plan"), "tool") == "ck3_select_event_option" and
        integer(field(field(field(action, "plan"), "args"), "event_instance_id"), "actual canceled instance", 1, 2**31 - 1) == canceled_request["event_instance_id"] and
        integer(field(field(field(action, "plan"), "args"), "option_number"), "actual cancel option", 1) == source_option_index("xalw.11", "xalw.11.cancel") + 1,
        "The reviewed original confirmation did not receive its source-defined cancel action")
    cancel_sets: list[set[str]] = []
    for key in ("before_item", "after_item"):
        frame, row = _native_record(cancellation[key], run_id=run, machine_id=machine, manifest=manifest)
        require((frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) == (first.pid, first.player_id, first.generation_decimal, first.date_raw) and
            field(field(row, "plan"), "tool") == core.ITEM and native_id(field(field(row, "result"), "requested_artifact_id"), "cancel target", allow_zero=True) == int(target), "Cancel inventory crossed date/actor/tool")
        cancel_sets.append(_owned(field(row, "result"), frame=frame))
    require(cancel_sets[0] == cancel_sets[1] and materials["common"] in cancel_sets[1], "Canceled material or another inventory item was consumed")
    frame, row = _native_record(cancellation["management_after"], run_id=run, machine_id=machine, manifest=manifest)
    require((frame.pid, frame.player_id, frame.generation_decimal, frame.date_raw) == (first.pid, first.player_id, first.generation_decimal, first.date_raw) and
        field(field(row, "plan"), "tool") == "ck3_query_current_event_window_context_v1", "Returned management query crossed the original scene")
    current = field(field(row, "result"), "current_event_window_context")
    management_choice(field(row, "result"), frame=frame, instance_id=integer(field(current, "current_event_instance_id"), "returned management", 1), event_key="xalw.10", option_key="xalw.10.close")
    before = initial
    for index, (rarity, xp) in enumerate(FEEDING_XP.items(), 1):
        actual = samples[index]
        level, total, growth = before.level, before.xp + xp, before.growth_sequence
        while total >= 100 * level:
            total -= 100 * level; level += 1; growth += 1
        require(actual.artifact_id == target and actual.equipped and actual.pending == 0 and
            (actual.level, actual.xp, actual.growth_sequence) == (level, total, growth), "Actual saved feeding XP/growth differs")
        require(all(identity not in inventories[index] for eaten, identity in materials.items() if eaten in tuple(FEEDING_XP)[:index]) and
            all(identity in inventories[index] for remaining_rarity, identity in materials.items() if remaining_rarity in tuple(FEEDING_XP)[index:]), "Actual native material consumption differs")
        before = actual
    log = read(Path(checked_pin(field(values, "log"), "full log scan")["path"]))
    require(set(log) == {"machine_id", "run_id", "observed_at_utc", "original_log", "full_log", "scan"} and log["machine_id"] == machine and log["run_id"] == run,
        "Full log scan crossed scene")
    declared_log = mapping(log["original_log"], "original full log pin")
    require(set(declared_log) == set(Pin.__required_keys__) and re.fullmatch("[0-9a-f]{64}", text(declared_log["sha256"], "log digest")) is not None, "Canonical original full-log pin required")
    original_log = Pin(path=text(declared_log["path"], "original log path"), bytes=integer(declared_log["bytes"], "original log bytes"), sha256=text(declared_log["sha256"], "original log SHA"))
    require(Path(original_log["path"]).resolve() == Path(text(field(context, "state_dir"), "state")).resolve() / "profile/logs/error.log", "Full log source crossed profile")
    stamp(log["observed_at_utc"])
    raw = Path(checked_pin(field(log, "full_log"), "full error log", allow_empty=True)["path"]).read_bytes()
    copied_log = checked_pin(log["full_log"], "full log", allow_empty=True)
    require((original_log["bytes"], original_log["sha256"]) == (copied_log["bytes"], copied_log["sha256"]), "Copied log differs from retained source pin")
    scan = scan_error_log(raw)
    require(_same_json(log["scan"], scan), "Retained log scan differs from complete raw log")
    if scan["mod_runtime_error_count"] != 0:
        raise core.CaseFailed("Full actual error.log contains mod script/UI errors")
    return {"previews": 5, "four_rarities": list(FEEDING_XP), "zero_natural_days": True, "cancel_native_material_preserved": True,
        "cancel_xp_scope": "Included in exact first-feed saved XP; no separate native dynamic-XP query", "actual_saved_observations": 5,
        "final_sample": samples[-1].to_json(), "log_scan": scan, "suppression_expiry_credit": False, "npc_credit": False}


def run_case(context: object, client: object) -> Object:
    config = validate_contract(context)
    require(isinstance(client, CasePort), "Actual shared CaseClient required")
    if not isinstance(client, CasePort):
        raise ValueError("Shared CaseClient unavailable")
    session = core.Session(context, client, config.transport)
    journal: Object = {"checkpoints": [], "reviews": [], "cancellation": None, "log": None}
    status: Literal["PASS", "FAIL", "BLOCKED"] = "BLOCKED"
    observed: Object = {}
    error: str | None = None
    try:
        session.refs.extend(prepared_sources(context, client.state))
        session.snapshot()
        initial_sample, initial, checkpoint, initial_owned = _observe(session, None, tuple(FEEDING_XP))
        target = initial.target_id
        materials = {item.rarity: item.artifact_id for item in initial.artifacts if item.artifact_id != target}
        target_item = next(item for item in initial.artifacts if item.artifact_id == target)
        require((initial_sample.level, initial_sample.xp, initial_sample.pending, initial_sample.growth_sequence, initial_sample.equipped, initial_sample.date_literal) ==
            (1, 92, 0, 0, False, "1066.9.15") and target_item.variables["xalw_diet"].flag == "armor" and
            set(materials) == set(FEEDING_XP) and {target, *materials.values()} <= initial_owned and
            all(item.artifact_type == "sword" for item in initial.artifacts if item.artifact_id != target), "Actual initial non-diet fixture precondition differs")
        saves: list[Pin] = [checkpoint]
        reviews: list[Pin] = []
        journal["checkpoints"] = object_value({"items": saves})["items"]
        session.equip(target, True)
        session.open_management(target)
        session.select_management("xalw.10", "xalw.10.feed_common", next_event="xalw.11", next_option="xalw.11.confirm")
        reviews.append(_review(session, target=target, material=materials["common"], rarity="common", ordinal=1))
        before_cancel_owned = _owned(session.observe_item(target), frame=session.current())
        before_item = _last_call_record(session)
        before_cancel = len(session.refs)
        session.select_management("xalw.11", "xalw.11.cancel", next_event="xalw.10")
        action_native = _cancel_action(session.refs[before_cancel:])
        session.management_choice("xalw.10", "xalw.10.close")
        management_after = _last_call_record(session)
        after_cancel_owned = _owned(session.observe_item(target), frame=session.current())
        journal["cancellation"] = object_value(write_once(client.output / "preview-cancellation.json", {
            "before_item": before_item, "after_item": _last_call_record(session), "management_after": management_after, "action_native": action_native, "material_id": materials["common"]}))
        if before_cancel_owned != after_cancel_owned or materials["common"] not in after_cancel_owned:
            raise core.CaseFailed("Original cancel changed actual inventory; no subsequent feeding permitted")
        before_feed = initial_sample
        for index, rarity in enumerate(FEEDING_XP):
            session.select_management("xalw.10", f"xalw.10.feed_{rarity}", next_event="xalw.11", next_option="xalw.11.confirm")
            reviews.append(_review(session, target=target, material=materials[rarity], rarity=rarity, ordinal=index + 2))
            session.select_management("xalw.11", "xalw.11.confirm", next_event="xalw.10")
            current, _, checkpoint, owned = _observe(session, target, tuple(FEEDING_XP)[index + 1:])
            saves.append(checkpoint)
            expected_level, expected_xp, expected_growth = before_feed.level, before_feed.xp + FEEDING_XP[rarity], before_feed.growth_sequence
            while expected_xp >= 100 * expected_level:
                expected_xp -= 100 * expected_level; expected_level += 1; expected_growth += 1
            if not current.equipped or current.pending != 0 or (current.level, current.xp, current.growth_sequence) != (expected_level, expected_xp, expected_growth):
                raise core.CaseFailed("Actual saved feeding XP differs; no subsequent feeding permitted")
            if any(materials[eaten] in owned for eaten in tuple(FEEDING_XP)[:index + 1]) or any(materials[remaining] not in owned for remaining in tuple(FEEDING_XP)[index + 1:]):
                raise core.CaseFailed("Actual material consumption differs; no subsequent feeding permitted")
            before_feed = current
        journal["checkpoints"] = object_value({"items": saves})["items"]
        journal["reviews"] = object_value({"items": reviews})["items"]
        session.select_management("xalw.10", "xalw.10.close", next_event=None)
        raw = client.log_bytes("error.log")
        source = pin(client.state / "profile/logs/error.log")
        copied = client.output / "preview-error-full.log"
        require(not copied.exists(), "Full log copy already exists")
        copied.write_bytes(raw)
        require((pin(copied)["bytes"], pin(copied)["sha256"]) == (source["bytes"], source["sha256"]), "Actual log changed before full capture")
        journal["log"] = object_value(write_once(client.output / "preview-error-scan.json", {"machine_id": session.machine_id, "run_id": session.run_id,
            "observed_at_utc": utc_now(), "original_log": source, "full_log": pin(copied), "scan": scan_error_log(raw)}))
        observed = evaluate(context, manifest=client.manifest, reviewer=client.operator_reviewer, journal=journal)
        require(session.days == 0 and session.checkpoint_observations == 5, "Preview exceeded declared day/save budget")
        status = "PASS"
    except core.CaseFailed as failure:
        status, error = "FAIL", str(failure)
    except (core.CaseBlocked, ValueError, OSError, TimeoutError, KeyError, StopIteration) as failure:
        error = type(failure).__name__ + ": " + str(failure)
    journal_ref = write_once(client.output / "preview-evidence-journal.json", journal)
    if session.start is not None and session.owner is not None:
        session.days = (session.current().date_raw - session.start.date_raw) // 24
    checks: list[CheckResult] = [core._check(check, status, error, [*session.refs, journal_ref], observed) for check in CHECKS]
    result: PreviewCaseResult = {"schema": "living-artifacts-preview-case-result-v1", "schema_version": 1, "product": "living-artifacts", "case": "feeding_preview",
        "run_id": session.run_id, "machine_id": session.machine_id, "reviewer": client.operator_reviewer, "observed_at_utc": utc_now(), "status": status,
        "checks": checks, "journal": journal_ref, "error": error,
        "actual_natural_days": session.days, "actual_public_calls_budgeted": session.calls, "actual_saved_observations": session.checkpoint_observations,
        "original_action_unknown": session.original_action_unknown, "case_contract_qualified": status == "PASS", "gui_contract_qualified": status == "PASS",
        "business_pass": False, "product_release_pass": False, "normal_close_owner": "shared entry/CaseClient", "normal_close_pending": True}
    write_once(client.output / RESULT_NAME, result)
    return object_value(result)


def verify_case(context: object) -> Object:
    config = validate_contract(context)
    output = Path(text(field(context, "output"), "output"))
    if not (output / RESULT_NAME).is_file():
        return {"status": "NOT_RUN", "case_contract_qualified": False, "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False}
    result = read(output / RESULT_NAME)
    require(set(result) == set(PreviewCaseResult.__required_keys__), "Closed preview result fields required")
    prepared_sources(context, Path(text(field(context, "state_dir"), "state")))
    runtime = read(Path(checked_pin(field(context, "runtime_manifest"), "actual runtime")["path"]))
    require(result["run_id"] == field(context, "run_id") and result["machine_id"] == field(runtime, "machine_id") and result["product"] == "living-artifacts" and
        result["case"] == "feeding_preview" and result["schema"] == "living-artifacts-preview-case-result-v1" and integer(result["schema_version"], "result version", 1, 1) == 1,
        "Retained preview result crossed selected scene/schema")
    natural_days = integer(result["actual_natural_days"], "actual preview days")
    integer(result["actual_public_calls_budgeted"], "actual calls", 1, config.transport.max_calls)
    saves = integer(result["actual_saved_observations"], "actual saves", 0, config.maximum_checkpoints)
    require(result["status"] in ("PASS", "FAIL", "BLOCKED") and result["business_pass"] is False and result["product_release_pass"] is False and
        result["normal_close_owner"] == "shared entry/CaseClient" and result["normal_close_pending"] is True, "Retained preview scope differs")
    complete = result["status"] == "PASS"
    require(not complete or natural_days == 0, "Preview PASS requires zero actual natural days")
    stamp(result["observed_at_utc"])
    require(type(result["original_action_unknown"]) is bool and (not complete or result["original_action_unknown"] is False), "Unknown original action cannot pass")
    if complete:
        require(result["error"] is None, "PASS cannot carry an error")
    else:
        text(result["error"], "specific preview failure")
    journal = read(Path(checked_pin(result["journal"], "original journal")["path"]))
    observed = evaluate(context, manifest=runtime, reviewer=text(result["reviewer"], "reviewer"), journal=journal) if complete else {}
    require(result["case_contract_qualified"] is complete and result["gui_contract_qualified"] is complete and (not complete or saves == 5), "Preview qualification differs from actual observations")
    checks = array(result["checks"], "actual preview checks")
    require(len(checks) == len(CHECKS), "Every scoped preview check required")
    for check, identity in zip(checks, CHECKS, strict=True):
        require(set(mapping(check, "check")) == set(CheckResult.__required_keys__) and field(check, "case_id") == identity and field(check, "status") == result["status"] and
            _same_json(field(check, "observed"), observed) and field(check, "evidence_scope") == "fixture_live" and field(check, "reason") == result["error"], "Preview check differs from re-reading original evidence")
        require(not complete or result["journal"] in array(field(check, "evidence"), "PASS evidence"), "PASS requires its complete original evidence journal")
        for reference in array(field(check, "evidence"), "evidence"):
            checked_pin(reference, "actual preview evidence", allow_empty=True)
    return result
