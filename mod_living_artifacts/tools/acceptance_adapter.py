"""One public CaseClient scene for actual core growth/equipment observations.

The public host owns launch, progression transport, normal Quit and resources.
An unsupported artifact picker blocks feeding instead of invoking a fixture
effect or crediting an ACK. Scope-variable logs are auxiliary fixture evidence,
paired with actual native owner/equipment reads, never a generic native getter.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
from pathlib import Path
import re
import sys
from typing import Literal, Protocol, runtime_checkable

PRODUCT_TOOLS = Path(__file__).resolve().parent
if str(PRODUCT_TOOLS) not in sys.path:
    sys.path.insert(0, str(PRODUCT_TOOLS))

from acceptance_contract import (ArtifactSample, CasePort, CheckResult, Frame, INPUT_PREFIX, OBSERVATION_PREFIX,
                                 Object, Pin, RESULT_NAME, array, decimal_id, field, integer, json_value, mapping,
                                 native_id, object_value, pin, read, require, text, utc_now, write_once)
from prepare_fixture import emit_fixture

ITEM = "ck3_query_player_artifact_personal_use_v1"
EQUIP = "ck3_submit_player_artifact_personal_use_v1"
EQUIP_POST = "ck3_query_player_artifact_personal_use_action_post_v1"
OPEN = "ck3_open_player_inventory_window_v1"
OPEN_POST = "ck3_query_player_inventory_window_open_post_v1"
WINDOW = "ck3_query_ingame_ui_window_v1"
INTERACTION_QUERY = "ck3_query_character_interaction_ordinary_v1"
REQUIRED_TOOLS: tuple[str, ...] = (
    "ck3_take_snapshot", "ck3_execute_step", ITEM, EQUIP, EQUIP_POST, OPEN, OPEN_POST, WINDOW,
    INTERACTION_QUERY, "ck3_query_current_event_window_context_v1", "ck3_select_event_option",
    "ck3_query_pending_character_interaction_context_v1", "ck3_reply_pending_character_interaction", "ck3_save_checkpoint",
)
REQUIRED_OPT_INS: dict[str, bool] = {
    "opt_in_player_artifact_personal_use_actions": True,
    "opt_in_player_inventory_window_open": True,
}


class CaseBlocked(RuntimeError):
    """An actual dependency or unknown original intent prevents this subcase."""


class CaseFailed(RuntimeError):
    """Independent actual evidence contradicts the declared product behavior."""


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
    expected_actor: int


def validate_contract(context: object) -> Contract:
    require(field(context, "product") == "living-artifacts" and field(context, "case") == "core_continuous",
            "Adapter only accepts the selected canonical product/core case")
    config = mapping(field(context, "case_contract"), "core contract")
    expected = {"schema", "schema_version", "product", "case_id", "acceptance_scope", "maximum_natural_days", "max_public_calls",
                "day_timeout_seconds", "post_start", "required_startup", "forbidden_startup", "required_checks", "deferred_checks",
                "observer_authority", "artifact_picker_boundary", "whole_product_acceptance_credit", "expected_actor_character_id", "startup_source_guard"}
    require(set(config) == expected and config["schema"] == "living-artifacts-core-continuous-case-v1" and
            integer(config["schema_version"], "schema version") == 1 and config["product"] == "living-artifacts" and
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
    actor = native_id(config["expected_actor_character_id"], "expected original actor")
    require(actor == 29829, "This prototype requires the selected original Robert actor")
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
                    integer(config["day_timeout_seconds"], "day timeout", 10, 120), required, deferred, actor)


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
                   "acceptance_adapter.py", "acceptance_contract.py", "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py")],
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
    expected_sources = ("acceptance_adapter.py", "acceptance_contract.py", "prepare_fixture.py", "living_artifacts_core.py", "living_artifacts_model.py")
    sources = array(frozen["caller_sources"], "frozen caller sources")
    require(len(sources) == len(expected_sources), "Prepared caller source set differs")
    refs = [_checked_pin(value, "prepared caller source", PRODUCT_TOOLS / name) for name, value in zip(expected_sources, sources)]
    refs.append(_checked_pin(frozen["contract_source"], "prepared contract source", PRODUCT_TOOLS / "core_continuous.contract.json"))
    emission = mapping(frozen["fixture_emission"], "frozen fixture emission")
    require(set(emission) == {"schema_version", "fixture_root", "files", "input_origin", "business_acceptance", "game_started"} and
            integer(emission["schema_version"], "fixture schema version", 1, 1) == 1 and emission["input_origin"] == "fixture_generated" and
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
        self.owner: Frame | None = None
        self.last_frame: object = None
        self.start: Frame | None = None
        self.first_sample: ArtifactSample | None = None
        self.last_sample: ArtifactSample | None = None
        self.refs: list[Pin] = []
        self.original_action_unknown = False
        self.last_native_record: Pin | None = None

    def budget(self, calls: int) -> None:
        if self.calls + calls > self.contract.max_calls:
            raise CaseBlocked("Finite declared public call budget reached")
        self.client.guard(reserve=180)

    def bind(self, value: object) -> Frame:
        frame = Frame.parse(value, run_id=self.run_id, machine_id=self.machine_id, manifest=self.client.manifest)
        require(frame.player_id == self.contract.expected_actor, "Actual scene does not contain the selected original Robert actor")
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

    def call(self, tool: str, args: Object | None = None) -> Object:
        require(tool in REQUIRED_TOOLS, "This case cannot call an undeclared arbitrary tool")
        self.budget(1)
        self.sequence += 1
        name = f"xalw-core-{self.sequence:04d}"
        step: Object = {"id": name, "tool": tool, "args": {} if args is None else args, "fresh_revision": True,
                        "continue_on_error": True, "timeout": 30}
        self.calls += 1
        try:
            actual = self.client.execute_plan([step], name, timeout=35)
        finally:
            path = self.client.output / (name + ".actual-results.json")
            if path.is_file():
                self.refs.append(pin(path))
        rows = array(actual, "actual public response rows")
        require(len(rows) == 1, "Exactly one original public response is required")
        row = mapping(rows[0], "actual public row")
        self.bind(field(row, "after_snapshot"))
        if row.get("ok") is not True or row.get("error") is not None:
            raise CaseBlocked("Original public call unavailable; preserve its row and never replay: " + tool)
        return object_value(field(row, "result"))

    def observer(self, target: str) -> tuple[ArtifactSample, Pin]:
        raw = self.client.log_bytes()
        sample_lines = [line for line in raw.decode("utf-8-sig", errors="strict").splitlines() if OBSERVATION_PREFIX in line]
        if not sample_lines:
            raise CaseBlocked("Read-only fixture getter logger has no actual sample; unevaluated/native unsupported logging cannot pass")
        samples = [ArtifactSample.parse(line) for line in sample_lines]
        require(len({sample.sequence for sample in samples}) == len(samples), "Duplicate actual observer sequence")
        selected = samples[-1]
        owner = self.current()
        require(selected.owner_id == str(owner.player_id) and selected.artifact_id == target, "Actual observer artifact/owner differs from native scene")
        if self.first_sample is None:
            self.first_sample = selected
        first = self.first_sample
        start = self.start
        if start is None:
            raise CaseBlocked("Native opening frame absent")
        # Join the two observed day counters, never an assumed global epoch.
        # Native day advancement's public contract uses 24 raw calendar hours.
        require(owner.date_raw // 24 - start.date_raw // 24 == selected.game_day - first.game_day,
                "Getter sample is not from the current native day; do not credit stale logs")
        require(selected.pending == 0 and selected.xp < 100 * selected.level, "Actual post-settlement XP invariant violated")
        self.last_sample = selected
        reference = write_once(self.client.output / f"observer-{selected.sequence:04d}-{self.sequence:04d}.json", {
            "schema_version": 1, "run_id": self.run_id, "machine_id": self.machine_id, "observed_at_utc": utc_now(),
            "authority": "fixture-readonly-getter-log-auxiliary", "native_date_raw": owner.date_raw,
            "actual_log_sha256_at_capture": hashlib.sha256(raw).hexdigest(), "sample": selected.to_json(),
            "actual_line": sample_lines[-1], "source_log_path": str(self.client.state / "profile/logs/debug.log"),
            "original_native_frame_record": json_value(self.last_native_record),
            "current_native_artifact_variable_query": False})
        self.refs.append(reference)
        return selected, reference

    def observe_item(self, target: str) -> Object:
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

    def open_inventory(self) -> None:
        query = self.call(WINDOW, {"window_kind": "inventory"})
        if field(query, "available") is not True:
            raise CaseBlocked("Current original inventory window context unavailable")
        current = field(query, "current")
        if field(current, "available") is True and field(current, "native_visible") is True and field(current, "effective_visible") is True:
            return
        self.original_action_unknown = True
        submitted = self.call(OPEN)
        if submitted.get("once_intent_consumed") is not True:
            raise CaseBlocked("Original inventory-open intent was not admitted")
        sequence = integer(field(submitted, "intent_sequence"), "actual inventory sequence", 1)
        for _ in range(3):
            after = self.call(OPEN_POST, {"expected_intent_sequence": sequence})
            if after.get("desired_window_observed") is True:
                verify = self.call(WINDOW, {"window_kind": "inventory"})
                state = field(verify, "current")
                require(field(state, "native_visible") is True and field(state, "effective_visible") is True,
                        "Independent native inventory view did not confirm opening")
                self.original_action_unknown = False
                return
        raise CaseBlocked("Original inventory-open result unknown; do not submit again")

    def equip(self, target: str, desired: bool) -> Object:
        self.open_inventory()
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

    def advance_one(self) -> None:
        if self.days >= self.contract.maximum_days:
            raise CaseBlocked("Finite declared natural-day budget reached")
        self.budget(3)
        frame = self.last_frame
        if field(frame, "active_event") is not None or field(frame, "pending_character_interaction") is not None:
            response = self.client.root_checkpoint(f"xalw-native-interruption-{self.sequence:04d}", {
                "original_native_frame_record": json_value(self.last_native_record), "mandatory_original_first_displayed_or_legal_left_action": True,
                "health_1015_specialist_priority": True, "no_replay_of_unknown": True}, reserve=180)
            if field(response, "native_interruption_continued") is not True or field(response, "original_instance_independently_absent") is not True:
                raise CaseBlocked("Original native interruption not resolved with independent window absence")
            self.snapshot()
        row = self.client.advance_day(timeout=float(self.contract.day_timeout), allow_event_boundary=True)
        self.calls += 3
        result = field(row, "result")
        after = field(result, "after")
        self.bind(after)
        self.snapshot()
        if self.start is None:
            raise CaseBlocked("Native opening frame absent")
        self.days = (self.current().date_raw - self.start.date_raw) // 24


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
        raw = client.log_bytes()
        input_bindings = _inputs(raw)
        target_owner, target = input_bindings["target"]
        require(target_owner == str(session.current().player_id) and all(owner == target_owner for owner, _ in input_bindings.values()),
                "Actual fixture inputs do not belong to the native player")
        initial, initial_ref = session.observer(target)
        require(not initial.equipped and (initial.level, initial.xp, initial.growth_sequence) == (1, 92, 0),
                "Observed initial inputs differ from frozen G01 precondition")
        actual = session.observe_item(target)
        owned = {str(native_id(item, "owned input artifact", allow_zero=True)) for item in array(field(actual, "owned_ids"), "actual owned inventory")}
        require({item[1] for item in input_bindings.values()} <= owned, "Native actual inventory lacks one of the five observed inputs")
        equipment = session.equip(target, True)
        checks.append(_check(active_check, "PASS", None, session.refs, equipment))
        active_check = "LW-G01"
        before = initial
        current = initial
        while current.month == before.month or (current.level, current.xp) == (1, 92):
            session.advance_one()
            current, _ = session.observer(target)
            native = session.observe_item(target)
            require(native.get("equipped") is True and current.equipped, "Actual target ceased being equipped during G01")
            if current.month > before.month + 1:
                raise CaseFailed("G01 did not settle at the first actual monthly boundary")
        if (current.level, current.xp, current.growth_sequence) != (2, 0, 1):
            raise CaseFailed("Actual +8 monthly G01 did not automatically resolve 1/92 to 2/0 with one growth")
        checks.append(_check(active_check, "PASS", None, session.refs, {"before": before.to_json(), "after": current.to_json(),
                              "growth_notification_was_not_opened": True, "native_equipped_crosscheck": True}))
        active_check = "CORE-UNEQUIP-01"
        unequip = session.equip(target, False)
        frozen = current
        while current.month == frozen.month:
            session.advance_one()
            current, _ = session.observer(target)
            native = session.observe_item(target)
            require(native.get("equipped") is False and not current.equipped, "Native/log equipment predicates disagree after unequip")
            if (current.level, current.xp, current.growth_sequence) != (frozen.level, frozen.xp, frozen.growth_sequence):
                raise CaseFailed("Unequipped artifact gained XP or evolved during an actual unoccupied month")
        checks.append(_check(active_check, "PASS", None, session.refs, {"native_unequip": unequip, "before": frozen.to_json(),
                              "after": current.to_json(), "scope": "monthly-XP-and-evolution-stop-only; aggregate modifiers require separate evidence"}))
        active_check = "CORE-FEED-01"
        # Real query exposes whether the production artifact-target interaction
        # is supported. There is no fixture button or fallback effect invocation.
        query = session.call(INTERACTION_QUERY, {"interaction_key": "xalw_manage_interaction", "recipient_id": session.current().player_id})
        payload = mapping(field(query, "character_interaction_ordinary_context"), "actual interaction support")
        checks.append(_check(active_check, "BLOCKED", "Existing ordinary MCP interaction accepts no artifact target/picker; native source-bound picker action is required before real feeding can be credited",
                             session.refs, {"ordinary_context_supported": json_value(payload.get("ordinary_context_supported")),
                             "unsupported_reason": json_value(payload.get("unsupported_reason")), "production_feed_submitted": False,
                             "fixture_feed_submitted": False, "required_actual_material_ids": [input_bindings[rarity][1] for rarity in ("common", "masterwork", "famed", "illustrious")]}))
        session.call("ck3_save_checkpoint")
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
    result: Object = {"schema": "living-artifacts-core-case-result-v1", "schema_version": 1, "run_id": session.run_id,
        "product": "living-artifacts", "case": "core_continuous", "machine_id": session.machine_id, "observed_at_utc": utc_now(),
        "status": "PASS" if complete else "FAIL" if any(check["status"] == "FAIL" for check in checks) else "BLOCKED",
        "checks": json_value(checks), "deferred_checks": list(contract.deferred_checks), "actual_natural_days": session.days,
        "actual_public_calls_budgeted": session.calls, "original_action_unknown": session.original_action_unknown,
        "case_contract_qualified": complete, "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False,
        "current_native_artifact_variable_query": False, "fixture_getter_log_credit": session.first_sample is not None, "error": error,
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
    require(result.get("schema") == "living-artifacts-core-case-result-v1" and integer(field(result, "schema_version"), "result schema version", 1, 1) == 1,
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
