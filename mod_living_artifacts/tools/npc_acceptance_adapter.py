"""One ordinary shared scene observes NPC fixture inputs and natural changes.

No NPC business effect is invoked. Real checkpoint files use the same verifier
as the player case. Saved inventory is historical; marker/source evidence is
required in addition to disappearance before feeding receives any credit.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import importlib
from pathlib import Path
import re
import sys
from typing import Literal

PRODUCT_TOOLS = Path(__file__).resolve().parent
if str(PRODUCT_TOOLS) not in sys.path:
    sys.path.insert(0, str(PRODUCT_TOOLS))

import acceptance_adapter as core
from acceptance_contract import CasePort, CheckResult, Frame, Object, Pin, array, decimal_id, field, integer, json_value, mapping, object_value, pin, read, require, text, utc_now, write_once
from checkpoint_artifacts import SavedArtifact, SavedVariable, one, parse_block, records, structured, variables
from checkpoint_callback import VerifiedCheckpoint, checked_pin, verify_checkpoint
from checkpoint_producer import declared_pin
from ck3_text_projection import blocks, masked
from npc_saved_observer import HEALTHY_ROLES, NpcInitialBaseline, NpcSavedObservation, NpcSavedRole, initial_owner_lifecycle_issues, observe_npc_saved, saved_character_reference
from prepare_npc_fixture import SOURCES, NpcFixtureEmission, NpcFixtureSpec, Role, emit_npc_fixture

RESULT_NAME = "living-artifacts-npc-result.json"
CONTRACT_NAME = "npc_continuous.contract.json"
RESULT_FIELDS = {"schema", "schema_version", "run_id", "machine_id", "observed_at_utc", "product", "case", "status", "checks", "errors",
    "actual_natural_days", "actual_public_calls_budgeted", "actual_saved_observations", "case_contract_qualified", "gui_contract_qualified",
    "business_pass", "product_release_pass", "current_native_npc_equipment", "normal_close_owner", "normal_close_pending"}
TOOLS = Path(__file__).resolve().parent
CANDIDATES: tuple[Role, ...] = (*HEALTHY_ROLES, "fragile")
REQUIRED_TOOLS = ("ck3_take_snapshot", "ck3_execute_step", "ck3_save_checkpoint", "ck3_select_event_option",
    "ck3_query_current_event_window_context_v1", "ck3_query_pending_character_interaction_context_v1", "ck3_reply_pending_character_interaction")
SOURCE_NAMES = ("npc_acceptance_adapter.py", "npc_saved_observer.py", "prepare_npc_fixture.py", "acceptance_adapter.py", "acceptance_contract.py",
    "checkpoint_callback.py", "checkpoint_artifacts.py", "checkpoint_producer.py", "startup_actor_binding.py", "native_interruption_contract.py",
    "living_artifacts_core.py", "living_artifacts_model.py", "inventory_gui_contract.py", "management_event_contract.py")


@dataclass(frozen=True)
class NpcContract:
    transport: core.Contract
    maximum_checkpoints: int
    observation_days: tuple[int, ...]
    observation_dates: tuple[str, ...]
    fixture_spec: NpcFixtureSpec


def validate_contract(context: object) -> NpcContract:
    require(field(context, "product") == "living-artifacts" and field(context, "case") == "npc_continuous", "Select the actual living-artifacts NPC case")
    actual = mapping(field(context, "case_contract"), "NPC contract")
    canonical = read(TOOLS / CONTRACT_NAME)
    require(actual == canonical, "NPC contract must equal the source-frozen declared contract")
    integer(field(actual, "schema_version"), "NPC contract version", 1, 1)
    require(field(actual, "whole_product_acceptance_credit") is False, "Partial NPC case grants no release credit")
    case = field(context, "case_spec")
    declared = {text(item, "declared actual tool") for item in array(field(case, "required_mcp_tools"), "NPC tool declarations")}
    require(set(REQUIRED_TOOLS) <= declared, "Declare every actual NPC transport tool")
    days = tuple(integer(item, "observation day", 0, 47) for item in array(field(actual, "observation_days"), "observation days"))
    dates = tuple(text(item, "observation date") for item in array(field(actual, "observation_dates"), "observation dates"))
    maximum = integer(field(actual, "maximum_checkpoints"), "NPC checkpoint count", 4, 4)
    require(days == (0, 1, 16, 47) and len(dates) == len(days) == maximum, "Exactly four source-bound natural observation dates required")
    spec = NpcFixtureSpec.parse(field(actual, "fixture_spec"))
    require(spec.queue_count == 0, "This scene does not qualify the queue fixture")
    required = tuple(text(item, "check ID") for item in array(field(actual, "required_checks"), "required checks"))
    deferred = tuple(text(item, "deferred ID") for item in array(field(actual, "deferred_checks"), "deferred checks"))
    return NpcContract(core.Contract(integer(field(actual, "maximum_natural_days"), "NPC day limit", 47, 47),
        integer(field(actual, "max_public_calls"), "NPC call limit", 320, 320), integer(field(actual, "day_timeout_seconds"), "NPC day timeout", 60, 60), required, deferred), maximum, days, dates, spec)


def _files(root: Path) -> dict[str, Pin]:
    require(root.is_dir(), "Actual directory required")
    result: dict[str, Pin] = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "Fixture/formal deployment cannot contain a link")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = pin(path)
    return result


def prepare_case(context: object) -> Object:
    contract = validate_contract(context)
    values = mapping(context, "actual public preparation context")
    inputs = field(values, "case_inputs")
    output = Path(text(field(values, "output"), "NPC prepare output")).resolve()
    fixture = emit_npc_fixture(output / "external-npc-fixture", game=Path(text(field(values, "game_dir"), "actual game directory")) / "game", spec=contract.fixture_spec)
    fixture_root = Path(fixture["fixture_root"])
    product = Path(text(field(inputs, "product_dir"), "formal staging")).resolve()
    require((product / "descriptor.mod").is_file(), "Actual formal staging required")
    write_once(fixture_root / "_case_contract.json", {"product": "living-artifacts", "case": "npc_continuous",
        "config": field(values, "case_contract"), "fixture_emission": fixture, "business_pass": False,
        "caller_sources": {name: pin(TOOLS / name) for name in SOURCE_NAMES}, "contract_source": pin(TOOLS / CONTRACT_NAME),
        "formal_files": _files(product)})
    preparation = importlib.import_module("ck3_mod_acceptance_prepare")
    require(isinstance(preparation, core.Preparation), "Actual shared fixture preparation interface required")
    if not isinstance(preparation, core.Preparation):
        raise ValueError("Shared fixture preparation unavailable")
    prepared = object_value(preparation.materialize_fixture_profile(values, fixture_root, product, field(inputs, "plain_configuration")))
    initial = write_once(output / "initial-plan.json", {"steps": []})
    return object_value({"startup": {"mode": "fixture", "state_dir": prepared["state_dir"], "fixture_start_policy": prepared["fixture_start_policy"]},
        "initial_plan": initial, "profile_preparation": prepared, "fixture_emission": fixture,
        "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False})


def prepared_sources(context: object, state: Path) -> tuple[Pin, ...]:
    contract = validate_contract(context)
    require(state.resolve() == Path(text(field(context, "state_dir"), "allocated state")).resolve(), "NPC case crossed allocated state")
    root = state / "profile/mod-content/fixture"
    manifest_path = root / "_case_contract.json"
    manifest = read(manifest_path)
    require(set(manifest) == {"product", "case", "config", "fixture_emission", "business_pass", "caller_sources", "contract_source", "formal_files"} and
        manifest["product"] == "living-artifacts" and manifest["case"] == "npc_continuous" and manifest["business_pass"] is False and
        manifest["config"] == field(context, "case_contract"), "Actual deployed NPC case contract differs")
    callers = mapping(manifest["caller_sources"], "NPC caller source table")
    require(set(callers) == set(SOURCE_NAMES), "NPC complete caller source table differs")
    refs = [core._checked_pin(callers[name], "NPC caller source", TOOLS / name) for name in SOURCE_NAMES]
    refs.append(core._checked_pin(manifest["contract_source"], "NPC contract source", TOOLS / CONTRACT_NAME))
    emission = mapping(manifest["fixture_emission"], "NPC fixture emission")
    require(set(emission) == set(NpcFixtureEmission.__required_keys__) and emission["input_origin"] == "fixture_generated" and
        emission["runtime_status"] == "NOT_RUN" and emission["business_acceptance"] == "NOT_ASSESSED" and
        NpcFixtureSpec.parse(emission["spec"]) == contract.fixture_spec, "NPC emission contract/status differs")
    source_bindings = mapping(emission["source_bindings"], "exact original source bindings")
    require(set(source_bindings) == {source.relative for source in SOURCES} | {
        "binaries/ck3.exe", "product/prepare_npc_fixture.py", "product/living_artifacts_core.py", "product/living_artifacts_model.py"},
        "NPC outer original source table is incomplete")
    for source in source_bindings.values():
        refs.append(checked_pin(source, "NPC original source"))
    original_root = Path(text(emission["fixture_root"], "original NPC fixture root")).resolve()
    emitted = mapping(emission["files"], "NPC emitted file table")
    require(set(_files(root)) == set(emitted) | {"_case_contract.json"}, "NPC deployed fixture file closure differs")
    for relative, raw in emitted.items():
        source = (original_root / relative).resolve()
        copied = (root / relative).resolve()
        require(source.is_relative_to(original_root) and copied.is_relative_to(root.resolve()), "NPC fixture source escaped root")
        expected = core._checked_pin(raw, "original NPC fixture input", source)
        actual = pin(copied)
        require((actual["bytes"], actual["sha256"]) == (expected["bytes"], expected["sha256"]), "NPC fixture deployed bytes differ")
        refs.append(actual)
    product = state / "profile/mod-content/product"
    formal = mapping(manifest["formal_files"], "formal product file table")
    require(set(_files(product)) == set(formal), "NPC product deployment closure differs")
    for relative, raw in formal.items():
        expected = checked_pin(raw, "original formal staging input")
        actual = pin(product / relative)
        require((actual["bytes"], actual["sha256"]) == (expected["bytes"], expected["sha256"]), "NPC deployed formal product bytes differ")
        refs.append(actual)
    enabled = read(state / "profile/dlc_load.json")
    require(enabled.get("enabled_mods") == ["mod/product.mod", "mod/fixture.mod"] and enabled.get("disabled_dlcs") == [], "NPC scene must mount exactly formal product and initial fixture")
    refs.extend((pin(manifest_path), pin(state / "profile/dlc_load.json")))
    startup = read(state / "preparation.json")
    preparation_pin = checked_pin(field(startup, "preparation"), "original shared profile preparation")
    preparation = read(Path(preparation_pin["path"]))
    require(field(preparation, "schema") == "ck3-mod-acceptance-prepared-fixture-v1" and
        Path(text(field(preparation, "state_dir"), "prepared state")).resolve() == state.resolve(), "NPC shared preparation crossed state/schema")
    prepared_files = mapping(field(preparation, "files"), "complete shared prepared file table")
    loaded_paths = {"mod/product.mod", "mod/fixture.mod", "dlc_load.json"}
    loaded_paths.update("mod-content/product/" + relative for relative in formal)
    loaded_paths.update("mod-content/fixture/" + relative for relative in set(emitted) | {"_case_contract.json"})
    require(loaded_paths <= set(prepared_files), "NPC shared deployment closure lacks a loaded input")
    for relative in sorted(loaded_paths):
        refs.append(core._checked_pin(prepared_files[relative], "actual shared prepared loaded input", state / "profile" / relative))
    refs.append(preparation_pin)
    return tuple(refs)


@dataclass(frozen=True)
class Candidate:
    role: Role
    status: Literal["bound", "candidate_missing", "reference_missing", "character_missing"]
    owner_id: str | None
    raw_reference: SavedVariable | None
    missing_marker: SavedVariable | None

    def to_json(self) -> Object:
        return object_value({"role": self.role, "status": self.status, "owner_id": self.owner_id,
            "raw_reference": None if self.raw_reference is None else self.raw_reference.to_json(),
            "missing_marker": None if self.missing_marker is None else self.missing_marker.to_json()})


def candidates(melted: Path, player_id: str) -> tuple[Candidate, ...]:
    player_id = decimal_id(player_id, "actual saved player")
    players = [body for identity, body in records(melted, ("living",)) if identity == player_id]
    require(len(players) == 1, "Exactly one actual saved player required")
    body = players[0]
    values = variables(structured(one(parse_block(body[body.index("{"):]), "alive_data"), "actual player alive_data"))
    pending: list[Candidate] = []
    for role in CANDIDATES:
        raw = values.get("xalw_npc_fixture_owner_" + role)
        marker = values.get("xalw_npc_fixture_missing_" + role)
        require(marker is None or marker == SavedVariable("boolean", "1", None), "Missing NPC candidate marker differs")
        if raw is None:
            pending.append(Candidate(role, "candidate_missing" if marker is not None else "reference_missing", None, None, marker))
        else:
            require(marker is None, "Actual NPC candidate has a conflicting missing marker")
            owner = saved_character_reference(raw, "NPC candidate owner")
            pending.append(Candidate(role, "bound", owner, raw, None))
    owners = [item.owner_id for item in pending if item.owner_id is not None]
    require(len(set(owners)) == len(owners) and player_id not in owners, "Candidate IDs must be distinct actual NPCs")
    found: list[str] = [identity for identity, _ in records(melted, ("living",)) if identity in owners]
    require(len(found) == len(set(found)), "Duplicate actual candidate character record")
    return tuple(replace(item, status="character_missing") if item.owner_id is not None and item.owner_id not in found else item for item in pending)


def consume_npc_readback(value: object, *, run_id: str, machine_id: str, reviewer: str,
                         frame: Frame, source_save: Pin, spec: NpcFixtureSpec,
                         baseline: NpcInitialBaseline | None = None) -> tuple[NpcSavedObservation, VerifiedCheckpoint]:
    verified = verify_checkpoint(value, run_id=run_id, machine_id=machine_id, reviewer=reviewer, frame=frame, source_save=source_save)
    roles = HEALTHY_ROLES if baseline is None else tuple(role.role for role in baseline.observation.roles)
    observed = observe_npc_saved(Path(verified.melted_save["path"]), player_id=str(frame.player_id), machine_id=machine_id, spec=spec,
        roles=roles, phase="initial" if baseline is None else "post", baseline=baseline)
    return observed, verified


def action_sources(product: Path) -> tuple[Pin, ...]:
    """Check actual loaded script writers and their existing AI call chain."""
    scripts = [(path, path.read_text(encoding="utf-8-sig")) for path in sorted(product.rglob("*.txt"))]
    wanted = {"xalw_feed_material_effect", "xalw_train_effect", "xalw_ai_cultivate_effect"}
    definitions: dict[str, tuple[Path, str]] = {}
    for path, source in scripts:
        for block in blocks(source):
            if block.key in wanted:
                require(block.key not in definitions, "Duplicate actual production action effect")
                definitions[block.key] = path, source[block.start:block.end]
    require(set(definitions) == wanted, "Actual production AI/feed/train effect chain is incomplete")
    for marker, effect in (("xalw_feeding_imprint", "xalw_feed_material_effect"), ("xalw_training_cooldown", "xalw_train_effect")):
        writer = re.compile(r"set_variable\s*=\s*\{\s*name\s*=\s*" + marker + r"\b")
        require(sum(len(writer.findall(masked(source))) for _, source in scripts) == 1 and len(writer.findall(masked(definitions[effect][1]))) == 1,
            "Actual production marker writer is not exclusive: " + marker)
    feed = definitions["xalw_feed_material_effect"][1]
    clean_feed = masked(feed)
    destroy = re.search(r"destroy_artifact\s*=\s*scope:xalw_material", clean_feed)
    feed_writer = re.search(r"set_variable\s*=\s*\{\s*name\s*=\s*xalw_feeding_imprint\b", clean_feed)
    guarded_feed = [block for block in blocks(feed) if block.key == "if" and
        re.match(r"\s*limit\s*=\s*\{\s*NOT\s*=\s*\{\s*exists\s*=\s*scope:xalw_material", clean_feed[block.opening + 1:block.end]) is not None and
        feed_writer is not None and block.opening < feed_writer.start() < block.end and
        re.search(r"change_variable\s*=\s*\{\s*name\s*=\s*xalw_pending_xp\s+add\s*=\s*scope:xalw_feed_xp", clean_feed[block.opening:block.end]) is not None and
        re.search(r"xalw_settle_xp_effect\s*=\s*yes", clean_feed[block.opening:block.end]) is not None]
    require(destroy is not None and len(guarded_feed) == 1 and destroy.start() < guarded_feed[0].start,
        "Feed marker must stay inside the actual post-destruction success/XP settlement branch")
    train = definitions["xalw_train_effect"][1]
    clean_train = masked(train)
    train_writer = re.search(r"set_variable\s*=\s*\{\s*name\s*=\s*xalw_training_cooldown\b", clean_train)
    guarded_train = [block for block in blocks(train) if block.key == "if" and train_writer is not None and
        block.opening < train_writer.start() < block.end and
        re.search(r"add_prestige\s*=\s*-50\b", clean_train[block.opening:block.end]) is not None and
        re.search(r"change_variable\s*=\s*\{\s*name\s*=\s*xalw_pending_xp\s+add\s*=\s*25\b", clean_train[block.opening:block.end]) is not None]
    require(len(guarded_train) == 1, "Training marker must retain its guarded actual training action/XP branch")
    ai = masked(definitions["xalw_ai_cultivate_effect"][1])
    require(all(re.search(name + r"\s*=\s*yes", ai) is not None for name in
        ("xalw_feed_material_effect", "xalw_train_effect", "equip_artifact_to_owner_replace")),
        "Actual AI action chain is missing")
    return tuple(pin(path) for path in sorted({path for path, _ in definitions.values()}))


def _total_xp(artifact: SavedArtifact) -> int:
    values = artifact.variables
    required = ("xalw_level", "xalw_xp_in_level", "xalw_pending_xp", "xalw_growth_sequence")
    require(all(name in values for name in required), "Actual NPC growth variables are incomplete")
    level, xp, pending, growth = (values[name].integer_value(name) for name in required)
    require(level >= 1 and 0 <= xp < 100 * level and pending == 0 and growth >= 0, "Actual NPC settled growth state differs")
    return 50 * level * (level - 1) + xp


def _target(role: NpcSavedRole) -> SavedArtifact | None:
    return next((item.artifact for item in role.items if item.kind == "target" and item.status == "owned"), None)


def _complete_roles(initial: NpcSavedObservation) -> tuple[NpcSavedRole, ...]:
    return tuple(role for role in initial.roles if replace(initial, roles=(role,)).initial_inputs_complete and
        not initial_owner_lifecycle_issues(role, initial.saved_date))


def evaluate(initial: NpcSavedObservation, later: tuple[NpcSavedObservation, ...], bindings: tuple[Candidate, ...], *, refs: list[Pin],
             production_sources: tuple[Pin, ...]) -> list[CheckResult]:
    """State differences and exclusive actual markers; absence alone never feeds."""
    checks: list[CheckResult] = []
    for candidate in bindings:
        current = next((role for role in initial.roles if role.role == candidate.role), None)
        lifecycle = initial_owner_lifecycle_issues(current, initial.saved_date) if current is not None else ()
        complete = candidate.status == "bound" and (candidate.role == "fragile" or
            current is not None and replace(initial, roles=(current,)).initial_inputs_complete and not lifecycle)
        binding_details = candidate.to_json()
        binding_details["initial_owner_lifecycle_issues"] = list(lifecycle)
        binding_reason = "Actual initial candidate/input state is " + candidate.status
        if lifecycle:
            binding_reason += "; " + "; ".join(lifecycle)
        elif current is not None:
            binding_reason += "; healthy inputs incomplete"
        checks.append(core._check("NPC-BIND-" + candidate.role, "PASS" if complete else "BLOCKED", None if complete else
            binding_reason, refs, binding_details))
    for role_name in HEALTHY_ROLES:
        before = next(role for role in initial.roles if role.role == role_name)
        after = tuple(role for observation in later for role in observation.roles if role.role == role_name)
        target_before = _target(before)
        lifecycle = initial_owner_lifecycle_issues(before, initial.saved_date)
        ready = replace(initial, roles=(before,)).initial_inputs_complete and target_before is not None and not lifecycle
        observations: Object = {"initial": before.to_json(), "later": [role.to_json() for role in after],
            "current_native_npc_equipment": False, "health_secret_cost_credit": False, "initial_owner_lifecycle_issues": list(lifecycle)}
        initial_item = next((item for item in before.items if item.kind == "target"), None)
        later_items = tuple(item for role in after for item in role.items if item.kind == "target" and item.status == "owned")
        equipped = ready and initial_item is not None and initial_item.equipped_slots == () and any(bool(item.equipped_slots) for item in later_items)
        any_growth = ready and target_before is not None and any(item.artifact is not None and _total_xp(item.artifact) > _total_xp(target_before) for item in later_items)
        monthly = tuple(role for observation in later if observation.saved_date in ("1066.10.1", "1066.11.1") for role in observation.roles if role.role == role_name)
        month_targets = tuple(_target(role) for role in monthly)
        grown = (ready and len(month_targets) == 2 and all(target is not None for target in month_targets) and all(
            any(item.kind == "target" and bool(item.equipped_slots) for item in role.items) for role in monthly) and
            month_targets[0] is not None and month_targets[1] is not None and _total_xp(month_targets[1]) > _total_xp(month_targets[0]))
        trained = ready and "xalw_training_cooldown" not in dict(before.saved_variables) and any(
            dict(role.saved_variables).get("xalw_training_cooldown") == SavedVariable("boolean", "1", None) for role in after) and any_growth and bool(production_sources)
        fed = ready and target_before is not None and "xalw_feeding_imprint" not in target_before.variables and any_growth and bool(production_sources) and any(
            _target(role) is not None and any(item.kind != "target" and item.status == "gone" for item in role.items) and
            any(item.kind == "target" and item.artifact is not None and
                item.artifact.variables.get("xalw_feeding_imprint") is not None and
                item.artifact.variables["xalw_feeding_imprint"].kind == "flag" and
                item.artifact.variables["xalw_feeding_imprint"].flag == "primary_armament" for item in role.items) for role in after)
        for name, passed, reason in (("EQUIP", equipped, "No initial-unequipped to actual saved equipped transition; existing equipment is not a new action"),
                ("GROW", grown, "No retained same-owner equipped Oct1-to-Nov1 settled growth increase"), ("TRAIN", trained, "No new exclusive training marker with growth evidence"),
                ("FEED", fed, "Disappearance/owner change alone cannot prove feeding; require new exclusive feed imprint and growth")):
            unavailable = "Initial production lifecycle scheduling unavailable: " + "; ".join(lifecycle) if lifecycle else reason
            checks.append(core._check("NPC-" + name + "-" + role_name, "PASS" if passed else "BLOCKED", None if passed else
                unavailable, refs, observations))
    return checks


def _frame_json(frame: Frame) -> Object:
    return {"revision": frame.revision, "native_revision": frame.native_revision, "date_raw": frame.date_raw,
        "player_id": frame.player_id, "pid": frame.pid, "generation_decimal": frame.generation_decimal}


def _frame(value: object) -> Frame:
    row = mapping(value, "retained observation frame")
    require(set(row) == {"revision", "native_revision", "date_raw", "player_id", "pid", "generation_decimal"}, "Exact retained frame fields required")
    return Frame(integer(row["revision"], "revision", 1), integer(row["native_revision"], "native revision", 1), integer(row["date_raw"], "date", 1),
        integer(row["player_id"], "player", 1, 2**32 - 2), integer(row["pid"], "PID", 1, 2**32 - 1), decimal_id(row["generation_decimal"], "generation"))


def run_case(context: object, client: object) -> Object:
    config = validate_contract(context)
    require(isinstance(client, CasePort), "Actual shared CaseClient required")
    if not isinstance(client, CasePort):
        raise ValueError("Actual shared CaseClient missing")
    session = core.Session(context, client, config.transport)
    observations: list[NpcSavedObservation] = []
    bindings: tuple[Candidate, ...] = ()
    baseline: NpcInitialBaseline | None = None
    errors: list[str] = []
    sources: tuple[Pin, ...] = ()
    try:
        session.refs.extend(prepared_sources(context, client.state))
        sources = action_sources(client.state / "profile/mod-content/product")
        session.refs.extend(sources)
        session.snapshot()
        first = session.current().date_raw
        for number, (days, saved_date) in enumerate(zip(config.observation_days, config.observation_dates), 1):
            while session.current().date_raw < first + days * 24:
                session.advance_one()
                require(session.current().date_raw <= first + days * 24, "Actual NPC observation date overshot")
            require(session.checkpoint_observations < config.maximum_checkpoints, "NPC saved observation budget exhausted")
            readback = session.checkpoint_readback(None)
            observed, verified = consume_npc_readback(readback.response, run_id=session.run_id, machine_id=session.machine_id,
                reviewer=client.operator_reviewer, frame=readback.frame, source_save=readback.source_save, spec=config.fixture_spec, baseline=baseline)
            require(observed.saved_date == saved_date and session.current().date_raw == readback.frame.date_raw,
                "NPC actual saved/native date differs from its declared natural checkpoint")
            if number == 1:
                bindings = candidates(Path(verified.melted_save["path"]), str(readback.frame.player_id))
                complete_roles = _complete_roles(observed)
                if complete_roles:
                    baseline = NpcInitialBaseline(replace(observed, roles=complete_roles))
                else:
                    errors.append("No healthy role has complete initial inputs and actual production lifecycle scheduling; later NPC business observations unavailable")
            observations.append(observed)
            session.refs.extend(verified.evidence)
            record = write_once(client.output / f"npc-observer-checkpoint-{number:02d}.json", {
                "schema": "living-artifacts-npc-checkpoint-envelope-v1", "run_id": session.run_id, "machine_id": session.machine_id,
                "reviewer": client.operator_reviewer, "frame": _frame_json(readback.frame), "source_save": readback.source_save,
                "response": readback.response, "observation": observed.to_json(), "business_pass": False})
            session.refs.append(record)
            if baseline is None:
                break
    except (core.CaseBlocked, ValueError, OSError, TimeoutError) as failure:
        errors.append(type(failure).__name__ + ": " + str(failure))
    checks = evaluate(observations[0], tuple(observations[1:]), bindings, refs=session.refs, production_sources=sources) if observations else []
    seen = {check["case_id"] for check in checks}
    for required in config.transport.required_checks:
        if required not in seen:
            checks.append(core._check(required, "BLOCKED", "; ".join(errors) or "No actual required initial/source observation", session.refs, {}))
    complete = len(observations) == config.maximum_checkpoints and all(check["status"] == "PASS" for check in checks)
    result = object_value({"schema": "living-artifacts-npc-case-result-v1", "schema_version": 1, "run_id": session.run_id,
        "machine_id": session.machine_id, "observed_at_utc": utc_now(), "product": "living-artifacts", "case": "npc_continuous",
        "status": "PASS" if complete else "BLOCKED", "checks": checks, "errors": errors, "actual_natural_days": session.days,
        "actual_public_calls_budgeted": session.calls, "actual_saved_observations": len(observations), "case_contract_qualified": complete,
        "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False, "current_native_npc_equipment": False,
        "normal_close_owner": "shared entry/CaseClient", "normal_close_pending": True})
    write_once(client.output / RESULT_NAME, result)
    return result


def verify_case(context: object) -> Object:
    config = validate_contract(context)
    output = Path(text(field(context, "output"), "actual case output"))
    path = output / RESULT_NAME
    if not path.is_file():
        return {"status": "NOT_RUN", "case_contract_qualified": False, "gui_contract_qualified": False, "business_pass": False, "product_release_pass": False}
    result = read(path)
    require(set(result) == RESULT_FIELDS, "NPC result fields differ")
    state = Path(text(field(context, "state_dir"), "actual allocated state"))
    selected_runtime = checked_pin(field(context, "runtime_manifest"), "selected actual runtime")
    selected_machine = text(field(read(Path(selected_runtime["path"])), "machine_id"), "selected runtime machine")
    refs = list(prepared_sources(context, state))
    sources = action_sources(state / "profile/mod-content/product")
    refs.extend(sources)
    actual: list[NpcSavedObservation] = []
    verified_empty_streams: list[Pin] = []
    bound: tuple[Candidate, ...] = ()
    baseline: NpcInitialBaseline | None = None
    first_frame: Frame | None = None
    for number in range(1, config.maximum_checkpoints + 1):
        record_path = output / f"npc-observer-checkpoint-{number:02d}.json"
        if not record_path.is_file():
            break
        envelope = read(record_path)
        require(set(envelope) == {"schema", "run_id", "machine_id", "reviewer", "frame", "source_save", "response", "observation", "business_pass"} and
            envelope["schema"] == "living-artifacts-npc-checkpoint-envelope-v1" and envelope["run_id"] == field(context, "run_id") and envelope["business_pass"] is False,
            "NPC retained envelope crossed scene/schema")
        require(envelope["machine_id"] == selected_machine, "NPC retained envelope crossed selected machine")
        frame = _frame(envelope["frame"])
        if first_frame is None:
            first_frame = frame
        require((frame.pid, frame.generation_decimal, frame.player_id) == (first_frame.pid, first_frame.generation_decimal, first_frame.player_id) and
            frame.date_raw == first_frame.date_raw + config.observation_days[number - 1] * 24, "NPC retained frame identity/calendar drifted")
        observed, verified = consume_npc_readback(envelope["response"], run_id=text(envelope["run_id"], "run ID"), machine_id=text(envelope["machine_id"], "machine ID"),
            reviewer=text(envelope["reviewer"], "actual reviewer"), frame=frame, source_save=declared_pin(envelope["source_save"], "original MCP save pin"), spec=config.fixture_spec, baseline=baseline)
        retained = NpcSavedObservation.parse(envelope["observation"])
        left, right = retained.to_json(), observed.to_json()
        left.pop("observed_at_utc"); right.pop("observed_at_utc")
        require(left == right and observed.saved_date == config.observation_dates[number - 1], "Retained NPC projection differs from re-reading actual saved source")
        if number == 1:
            bound = candidates(Path(verified.melted_save["path"]), str(frame.player_id))
            complete_roles = _complete_roles(observed)
            if complete_roles:
                baseline = NpcInitialBaseline(replace(observed, roles=complete_roles))
        actual.append(observed)
        verified_empty_streams.extend(reference for reference in verified.log_streams if reference["bytes"] == 0)
        refs.extend(verified.evidence)
        refs.append(pin(record_path))
        if baseline is None:
            break
    expected_checks = evaluate(actual[0], tuple(actual[1:]), bound, refs=refs, production_sources=sources) if actual else []
    expected = {check["case_id"]: check for check in expected_checks}
    seen: set[str] = set()
    for raw in array(field(result, "checks"), "retained NPC checks"):
        check = mapping(raw, "retained check")
        identity = text(field(check, "case_id"), "NPC check ID")
        require(identity in config.transport.required_checks and identity not in seen and set(check) == set(CheckResult.__required_keys__), "NPC check set/fields differ")
        seen.add(identity)
        require(check["evidence_scope"] == "fixture_live", "NPC check scope differs")
        if identity in expected:
            projected = expected[identity]
            require(check["status"] == projected["status"] and check["observed"] == projected["observed"] and check["reason"] == projected["reason"],
                "Retained NPC action claim differs from actual saved re-projection")
        else:
            require(check["status"] == "BLOCKED", "Unobserved NPC check cannot pass")
            text(check["reason"], "specific unobserved-check reason")
        evidence = array(check["evidence"], "actual NPC check evidence")
        require(all(reference in evidence for reference in refs), "NPC check lacks its actual re-verified source evidence")
        if check["status"] == "PASS":
            require(bool(evidence) and check["reason"] is None, "NPC PASS requires actual evidence and no failure reason")
        for reference in evidence:
            checked_pin(reference, "actual NPC evidence", allow_empty=reference in verified_empty_streams)
    complete = len(actual) == config.maximum_checkpoints and len(seen) == len(config.transport.required_checks) and all(check["status"] == "PASS" for check in expected_checks)
    saved_count = integer(result["actual_saved_observations"], "retained saved observation count", 0, config.maximum_checkpoints)
    natural_days = integer(result["actual_natural_days"], "retained natural day count", 0, config.transport.maximum_days)
    integer(result["actual_public_calls_budgeted"], "retained public call count", saved_count, config.transport.max_calls)
    require(saved_count == len(actual) and (not actual or natural_days >= config.observation_days[len(actual) - 1]), "NPC retained counters contradict saved observations")
    text(result["observed_at_utc"], "NPC result observation UTC")
    for error in array(result["errors"], "retained actual errors"):
        text(error, "specific actual error")
    require(seen == set(config.transport.required_checks) and result["run_id"] == field(context, "run_id") and result["product"] == "living-artifacts" and
        result["machine_id"] == selected_machine and result["normal_close_owner"] == "shared entry/CaseClient" and result["normal_close_pending"] is True and
        result["case"] == "npc_continuous" and result["schema"] == "living-artifacts-npc-case-result-v1" and integer(result["schema_version"], "NPC result version", 1, 1) == 1 and
        result["case_contract_qualified"] is complete and result["status"] == ("PASS" if complete else "BLOCKED") and
        all(result[key] is False for key in ("gui_contract_qualified", "business_pass", "product_release_pass", "current_native_npc_equipment")), "NPC result scope/status differs from actual observations")
    return result
