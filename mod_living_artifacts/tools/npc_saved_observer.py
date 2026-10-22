"""Historical NPC fixture bindings and native saved inventory; never AI credit.

JSON parsing validates the closed data contract and retained source file pins.
It does not re-run the save projection or authenticate an arbitrary caller's
projection. Only observe_npc_saved reads the actual selected records. A baseline
means complete saved fixture inputs, not native legality or AI qualification.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import re
from typing import Literal, TypeAlias

from acceptance_contract import Object, Pin, array, decimal_id, field, integer, json_value, mapping, object_value, pin, read, require, text, utc_now, write_once
from checkpoint_artifacts import Entry, SavedArtifact, SavedVariable, one, parse_block, records, scalar, structured, variables
from checkpoint_callback import checked_pin
from living_artifacts_model import FEEDING_XP, Rarity
from prepare_npc_fixture import NpcFixtureSpec, Role

HEALTHY_ROLES: tuple[Role, ...] = ("landed", "baron", "courtier")
InputKind: TypeAlias = Literal["target"] | Rarity
INPUTS: tuple[InputKind, ...] = ("target", *FEEDING_XP)
Phase: TypeAlias = Literal["initial", "post"]
InventoryStatus: TypeAlias = Literal["missing", "equipped_absent", "equipped_empty", "equipped_present"]
RoleStatus: TypeAlias = Literal["candidate_missing", "owner_reference_missing", "character_missing", "inventory_missing", "observed"]
ReferenceStatus: TypeAlias = Literal["present", "missing", "unresolved"]
ItemStatus: TypeAlias = Literal["reference_missing", "reference_unresolved", "owned", "owner_changed", "gone", "inventory_missing"]
VariableRows: TypeAlias = tuple[tuple[str, SavedVariable], ...]


def _closed(value: object, fields: tuple[str, ...], label: str) -> dict[str, object]:
    result = mapping(value, label)
    require(set(result) == set(fields), "Closed " + label + " fields required")
    return result


def _role(value: object) -> Role:
    for role in HEALTHY_ROLES:
        if type(value) is str and value == role:
            return role
    raise ValueError("Only healthy landed/baron/courtier roles are supported; fragile/queue are unavailable")


def _roles(value: object) -> tuple[Role, ...]:
    require(type(value) is tuple and bool(value), "Explicit nonempty role tuple required")
    if not isinstance(value, tuple):
        raise ValueError("Role tuple required")
    result = tuple(_role(role) for role in value)
    require(len(set(result)) == len(result), "Unique healthy roles required")
    return result


def _input(value: object) -> InputKind:
    for kind in INPUTS:
        if type(value) is str and value == kind:
            return kind
    raise ValueError("Unknown NPC input kind")


def _phase(value: object) -> Phase:
    if type(value) is str and value == "initial":
        return "initial"
    if type(value) is str and value == "post":
        return "post"
    raise ValueError("Explicit initial/post phase required")


def _date(value: object) -> str:
    result = text(value, "saved date")
    require(re.fullmatch(r"[1-9][0-9]*\.(?:[1-9]|1[0-2])\.(?:[1-9]|[12][0-9]|3[01])", result) is not None, "Canonical saved calendar date required")
    return result


def _variable(value: object) -> SavedVariable:
    row = _closed(value, ("type", "raw_identity_decimal", "flag"), "saved variable")
    kind = None if row["type"] is None else text(row["type"], "saved variable type")
    identity = None if row["raw_identity_decimal"] is None else text(row["raw_identity_decimal"], "raw saved identity")
    flag = None if row["flag"] is None else text(row["flag"], "saved variable flag")
    require(identity is None or re.fullmatch(r"-?(0|[1-9][0-9]*)", identity) is not None, "Canonical raw saved identity string required")
    return SavedVariable(kind, identity, flag)


def _variable_json(value: SavedVariable | None) -> Object | None:
    if value is None:
        return None
    require(type(value) is SavedVariable, "Typed saved variable required")
    result = value.to_json()
    _variable(result)
    return result


def _variable_rows(value: object) -> VariableRows:
    row = mapping(value, "saved variable table")
    require(all(key.startswith("xalw_") for key in row), "Selected variable names must retain their xalw prefix")
    return tuple((key, _variable(item)) for key, item in row.items())


def _reference(value: SavedVariable, kind: Literal["char", "artifact"], label: str) -> str | None:
    require(type(value) is SavedVariable and value.kind == kind and value.flag is None, "Exact saved " + kind + " reference required: " + label)
    return None if value.raw_identity is None else decimal_id(value.raw_identity, label, allow_zero=kind == "artifact")


def saved_character_reference(value: SavedVariable, label: str) -> str:
    """Decode the actual Rakaly ``type=char`` tag; no authored type aliases."""
    identity = _reference(value, "char", label)
    require(identity is not None, "Actual saved character reference is unresolved: " + label)
    if identity is None:
        raise ValueError("Actual saved character reference is unresolved: " + label)
    return identity


def _artifact(value: object) -> SavedArtifact:
    row = _closed(value, ("artifact_id", "owner_id", "name", "rarity", "artifact_type", "durability_decimal", "variables"), "saved artifact")
    durability = text(row["durability_decimal"], "durability decimal")
    require(re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{5}", durability) is not None and Decimal(durability).is_finite(), "Canonical Q100000 durability required")
    return SavedArtifact(decimal_id(row["artifact_id"], "artifact", allow_zero=True), decimal_id(row["owner_id"], "owner"),
        text(row["name"], "artifact name"), text(row["rarity"], "artifact rarity"), text(row["artifact_type"], "artifact type"),
        durability, dict(_variable_rows(row["variables"])))


@dataclass(frozen=True)
class SavedInventory:
    character_id: str
    status: InventoryStatus
    owner_id: str | None
    owned_ids: tuple[str, ...] | None
    equipped_slots: tuple[tuple[str, str], ...] | None

    def to_json(self) -> Object:
        return object_value({"character_id": self.character_id, "status": self.status, "owner_id": self.owner_id,
            "owned_ids": self.owned_ids, "equipped_slots": self.equipped_slots})

    @classmethod
    def parse(cls, value: object) -> SavedInventory:
        row = _closed(value, ("character_id", "status", "owner_id", "owned_ids", "equipped_slots"), "native saved inventory")
        actor = decimal_id(row["character_id"], "inventory actor")
        if row["status"] == "missing":
            require(all(row[key] is None for key in ("owner_id", "owned_ids", "equipped_slots")), "Missing inventory cannot claim empty/available slots")
            return cls(actor, "missing", None, None, None)
        owned = tuple(decimal_id(item, "owned artifact", allow_zero=True) for item in array(row["owned_ids"], "owned artifacts"))
        slots: list[tuple[str, str]] = []
        for raw in array(row["equipped_slots"], "native equipped slots"):
            pair = array(raw, "slot pair")
            require(len(pair) == 2, "Exactly one slot key/artifact pair required")
            slots.append((text(pair[0], "native slot key"), decimal_id(pair[1], "equipped artifact", allow_zero=True)))
        require(decimal_id(row["owner_id"], "inventory owner") == actor and len(set(owned)) == len(owned) and
            len({key for key, _ in slots}) == len(slots) and len({identity for _, identity in slots}) == len(slots) and
            all(identity in owned for _, identity in slots), "Native inventory owner/list/slot identities disagree")
        if row["status"] == "equipped_absent":
            require(not slots, "Absent equipped field cannot claim a slot")
            return cls(actor, "equipped_absent", actor, owned, ())
        if row["status"] == "equipped_empty":
            require(not slots, "Empty equipped block cannot claim a slot")
            return cls(actor, "equipped_empty", actor, owned, ())
        require(row["status"] == "equipped_present" and bool(slots), "Available equipped block needs actual entries")
        return cls(actor, "equipped_present", actor, owned, tuple(slots))

    def slots_for(self, artifact_id: str) -> tuple[str, ...] | None:
        artifact_id = decimal_id(artifact_id, "queried saved artifact", allow_zero=True)
        return None if self.equipped_slots is None else tuple(key for key, identity in self.equipped_slots if identity == artifact_id)


def parse_saved_inventory(character_id: str, block: str) -> SavedInventory:
    """Read native character inventory, not any product variable or modifier."""
    character_id = decimal_id(character_id, "selected saved character")
    text(block, "selected character record")
    entries = parse_block(block[block.index("{"):])
    alive = structured(one(entries, "alive_data"), "living actor alive_data")
    raw = one(alive, "inventory", required=False)
    if raw is None:
        return SavedInventory(character_id, "missing", None, None, None)
    inventory = structured(raw, "native inventory")
    owned: list[str] = []
    for entry in structured(one(inventory, "artifacts"), "native owned artifacts"):
        require(entry.key is None, "Native owned-artifact list must be anonymous")
        owned.append(decimal_id(scalar(entry.value, "native owned artifact"), "native owned artifact", allow_zero=True))
    raw_slots = one(inventory, "equipped", required=False)
    slots: list[tuple[str, str]] = []
    if raw_slots is not None:
        for entry in structured(raw_slots, "native equipped slots"):
            require(entry.key is not None, "Native equipped slot key is missing")
            if entry.key is None:
                raise ValueError("Missing native slot key")
            slots.append((entry.key, decimal_id(scalar(entry.value, "native slot artifact"), "native slot artifact", allow_zero=True)))
    return SavedInventory.parse(object_value({"character_id": character_id,
        "status": "equipped_absent" if raw_slots is None else "equipped_present" if slots else "equipped_empty",
        "owner_id": scalar(one(inventory, "owner"), "native inventory owner"), "owned_ids": owned, "equipped_slots": slots}))


@dataclass(frozen=True)
class NpcSavedItem:
    kind: InputKind
    reference_status: ReferenceStatus
    raw_reference: SavedVariable | None
    artifact_id: str | None
    status: ItemStatus
    artifact: SavedArtifact | None
    equipped_slots: tuple[str, ...] | None

    def to_json(self) -> Object:
        return object_value({"kind": self.kind, "reference_status": self.reference_status,
            "raw_reference": _variable_json(self.raw_reference), "artifact_id": self.artifact_id, "status": self.status,
            "artifact": None if self.artifact is None else self.artifact.to_json(), "equipped_slots": self.equipped_slots})


@dataclass(frozen=True)
class NpcSavedRole:
    role: Role
    status: RoleStatus
    owner_id: str | None
    raw_owner_reference: SavedVariable | None
    missing_candidate_marker: SavedVariable | None
    inventory: SavedInventory | None
    saved_variables: VariableRows
    items: tuple[NpcSavedItem, ...]

    def to_json(self) -> Object:
        return object_value({"role": self.role, "status": self.status, "owner_id": self.owner_id,
            "raw_owner_reference": _variable_json(self.raw_owner_reference), "missing_candidate_marker": _variable_json(self.missing_candidate_marker),
            "inventory": None if self.inventory is None else self.inventory.to_json(),
            "saved_variables": {key: value.to_json() for key, value in self.saved_variables}, "items": [item.to_json() for item in self.items]})


def initial_owner_lifecycle_issues(role: NpcSavedRole, saved_date: str) -> tuple[str, ...]:
    """Initial ordinary scheduling eligibility, never an equipment/AI success.

    Inventory completeness stays separate: historical R9/R10 input inventories
    remain real even when their owners never entered the normal product loop.
    Raw fields already travel in the single saved_variables JSON contract.
    """
    require(type(role) is NpcSavedRole, "Typed actual saved NPC role required")
    date = _date(saved_date)
    year, month, _ = (int(part) for part in date.split("."))
    expected_month = year * 12 + month
    if role.status != "observed" or role.owner_id is None:
        return ("owner state unavailable: " + role.status,)
    values = dict(role.saved_variables)
    issues: list[str] = []
    for name in ("xalw_monthly_chain", "xalw_last_owner_month", "xalw_ai_review_queued"):
        value = values.get(name)
        if value is None:
            issues.append(name + ": missing actual saved scheduling field")
            continue
        try:
            _variable_json(value)
            if name == "xalw_last_owner_month":
                actual = value.integer_value(name)
                if actual != expected_month:
                    issues.append(name + ": saved cursor " + str(actual) + " differs from initial month " + str(expected_month))
            elif value != SavedVariable("boolean", "1", None):
                issues.append(name + ": actual saved true boolean required")
        except ValueError:
            issues.append(name + ": invalid exact saved scheduling encoding")
    return tuple(issues)


@dataclass(frozen=True)
class NpcSavedObservation:
    machine_id: str
    observed_at_utc: str
    melted_source: Pin
    saved_date: str
    player_id: str
    spec: NpcFixtureSpec
    phase: Phase
    baseline_source: Pin | None
    roles: tuple[NpcSavedRole, ...]

    @property
    def initial_inputs_complete(self) -> bool:
        return self.phase == "initial" and bool(self.roles) and all(role.status == "observed" and
            tuple(item.kind for item in role.items) == INPUTS and
            all(item.status == "owned" and item.reference_status == "present" for item in role.items) for role in self.roles)

    @property
    def initial_lifecycle_ready(self) -> bool:
        return self.phase == "initial" and bool(self.roles) and all(not initial_owner_lifecycle_issues(role, self.saved_date) for role in self.roles)

    def to_json(self) -> Object:
        return object_value({"schema": "living-artifacts-npc-saved-observation-v1", "schema_version": 1,
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc, "melted_source": self.melted_source,
            "saved_date": self.saved_date, "player_id": self.player_id, "spec": self.spec.to_json(), "phase": self.phase,
            "baseline_source": self.baseline_source, "roles": [role.to_json() for role in self.roles],
            "initial_inputs_complete": self.initial_inputs_complete, "authority": "historical-saved-state-only",
            "role_eligibility_independently_observed": False, "current_native_observed": False, "ai_business_pass": False})

    @classmethod
    def parse(cls, value: object) -> NpcSavedObservation:
        return parse_npc_observation(value)


@dataclass(frozen=True)
class NpcInitialBaseline:
    observation: NpcSavedObservation

    def __post_init__(self) -> None:
        require(type(self.observation) is NpcSavedObservation and parse_npc_observation(self.observation.to_json()).initial_inputs_complete,
            "Only complete initial NPC fixture inputs can become a baseline")

    def to_json(self) -> Object:
        return {"schema": "living-artifacts-npc-initial-baseline-v1", "observation": self.observation.to_json()}

    @classmethod
    def parse(cls, value: object) -> NpcInitialBaseline:
        row = _closed(value, ("schema", "observation"), "initial NPC baseline")
        require(row["schema"] == "living-artifacts-npc-initial-baseline-v1", "Initial baseline schema differs")
        return cls(parse_npc_observation(row["observation"]))


def _input_variable(kind: InputKind) -> str:
    return "xalw_npc_fixture_target" if kind == "target" else "xalw_npc_fixture_material_" + kind


def _item(kind: InputKind, current: SavedVariable | None, baseline_id: str | None,
          owner: str, inventory: SavedInventory, artifacts: dict[str, SavedArtifact]) -> NpcSavedItem:
    reference_status: ReferenceStatus = "missing" if current is None else "present"
    current_id = None if current is None else _reference(current, "artifact", _input_variable(kind))
    if current is not None and current_id is None:
        reference_status = "unresolved"
    require(current_id is None or baseline_id is None or current_id == baseline_id, "Post input reference changed from its initial actual artifact")
    identity = current_id if baseline_id is None else baseline_id
    if identity is None:
        return NpcSavedItem(kind, reference_status, current, None,
            "reference_missing" if current is None else "reference_unresolved", None, None)
    artifact = artifacts.get(identity)
    if artifact is None:
        return NpcSavedItem(kind, reference_status, current, identity, "gone", None, None)
    if artifact.owner_id != owner:
        return NpcSavedItem(kind, reference_status, current, identity, "owner_changed", artifact, None)
    if inventory.status == "missing":
        return NpcSavedItem(kind, reference_status, current, identity, "inventory_missing", artifact, None)
    require(inventory.owned_ids is not None and identity in inventory.owned_ids, "Artifact owner and native inventory membership disagree")
    require(artifact.artifact_type == "sword" and (kind == "target" or artifact.rarity == kind), "Actual NPC input type/rarity differs from its source role")
    return NpcSavedItem(kind, reference_status, current, identity, "owned", artifact, inventory.slots_for(identity))


def _validate_role(role: NpcSavedRole) -> None:
    _role(role.role)
    if role.missing_candidate_marker is not None:
        require(role.missing_candidate_marker == SavedVariable("boolean", "1", None), "Missing candidate marker must be saved true")
    if role.status in ("candidate_missing", "owner_reference_missing"):
        require(role.owner_id is None and role.raw_owner_reference is None and role.inventory is None and not role.saved_variables and not role.items,
            "Unbound role cannot claim a character/inventory/input")
        require((role.status == "candidate_missing") == (role.missing_candidate_marker is not None), "Missing candidate and missing reference differ")
        return
    require(role.missing_candidate_marker is None and role.raw_owner_reference is not None and role.owner_id is not None,
        "Bound role needs its actual owner reference and no missing-candidate marker")
    if role.raw_owner_reference is None or role.owner_id is None:
        raise ValueError("Actual owner binding missing")
    require(saved_character_reference(role.raw_owner_reference, "NPC owner") == role.owner_id, "NPC owner reference differs")
    if role.status == "character_missing":
        require(role.inventory is None and not role.saved_variables and not role.items, "Missing living character record cannot claim inputs")
        return
    require(role.status in ("observed", "inventory_missing") and role.inventory is not None and tuple(item.kind for item in role.items) == INPUTS,
        "Observed healthy NPC requires exactly target and four rarity rows")
    if role.inventory is None:
        raise ValueError("NPC inventory observation absent")
    checked = SavedInventory.parse(role.inventory.to_json())
    require(checked.character_id == role.owner_id and (role.status == "inventory_missing") == (checked.status == "missing"), "NPC role/inventory availability differs")
    values = dict(role.saved_variables)
    require(len(values) == len(role.saved_variables), "Duplicate saved NPC variable")
    for key, value in role.saved_variables:
        _variable_rows({key: value.to_json()})
    identities: list[str] = []
    for item in role.items:
        _input(item.kind)
        require(item.raw_reference == values.get(_input_variable(item.kind)), "Input raw reference differs from the saved variable table")
        if item.reference_status == "missing":
            require(item.raw_reference is None, "Missing reference must stay absent")
        elif item.reference_status == "unresolved":
            require(item.raw_reference is not None and _reference(item.raw_reference, "artifact", "input") is None, "Unresolved artifact reference differs")
        else:
            require(item.reference_status == "present" and item.raw_reference is not None and
                _reference(item.raw_reference, "artifact", "input") == item.artifact_id, "Present artifact reference differs")
        if item.artifact_id is None:
            require(item.status == ("reference_missing" if item.reference_status == "missing" else "reference_unresolved") and
                item.artifact is None and item.equipped_slots is None, "Unresolved input cannot claim an actual artifact")
            continue
        identities.append(decimal_id(item.artifact_id, "input ID", allow_zero=True))
        if item.status == "gone":
            require(item.artifact is None and item.equipped_slots is None, "Gone artifact cannot claim an owner/slot")
            continue
        require(item.artifact is not None and item.artifact.artifact_id == item.artifact_id, "Existing input artifact identity differs")
        if item.artifact is None:
            raise ValueError("Existing input is absent")
        _artifact(item.artifact.to_json())
        if item.status == "owner_changed":
            require(item.artifact.owner_id != role.owner_id and item.equipped_slots is None and
                (checked.owned_ids is None or item.artifact_id not in checked.owned_ids), "Changed owner still appears in original NPC inventory")
        elif item.status == "inventory_missing":
            require(item.artifact.owner_id == role.owner_id and checked.status == "missing" and item.equipped_slots is None,
                "Missing inventory cannot claim known equipped state")
        else:
            require(item.status == "owned" and item.artifact.owner_id == role.owner_id and checked.owned_ids is not None and
                item.artifact_id in checked.owned_ids and item.equipped_slots == checked.slots_for(item.artifact_id), "Owned input/actual inventory slots disagree")
            require(item.artifact.artifact_type == "sword" and (item.kind == "target" or item.artifact.rarity == item.kind), "Input type/rarity differs")
    require(len(set(identities)) == len(identities), "NPC inputs cannot reuse one artifact")


def parse_npc_observation(value: object) -> NpcSavedObservation:
    row = _closed(value, ("schema", "schema_version", "machine_id", "observed_at_utc", "melted_source", "saved_date", "player_id", "spec", "phase",
        "baseline_source", "roles", "initial_inputs_complete", "authority", "role_eligibility_independently_observed", "current_native_observed", "ai_business_pass"), "NPC saved observation")
    require(row["schema"] == "living-artifacts-npc-saved-observation-v1" and integer(row["schema_version"], "observer version", 1, 1) == 1 and
        row["authority"] == "historical-saved-state-only" and all(row[key] is False for key in
        ("role_eligibility_independently_observed", "current_native_observed", "ai_business_pass")), "Saved observation grants no current native/AI qualification")
    phase = _phase(row["phase"])
    baseline = None if row["baseline_source"] is None else checked_pin(row["baseline_source"], "actual initial saved source")
    require((phase == "initial") == (baseline is None), "Post observation requires the explicit initial source")
    roles: list[NpcSavedRole] = []
    for raw in array(row["roles"], "healthy NPC role observations"):
        item = _closed(raw, ("role", "status", "owner_id", "raw_owner_reference", "missing_candidate_marker", "inventory", "saved_variables", "items"), "NPC role")
        role_status: RoleStatus | None = None
        for candidate in ("candidate_missing", "owner_reference_missing", "character_missing", "inventory_missing", "observed"):
            if item["status"] == candidate:
                if candidate == "candidate_missing": role_status = "candidate_missing"
                elif candidate == "owner_reference_missing": role_status = "owner_reference_missing"
                elif candidate == "character_missing": role_status = "character_missing"
                elif candidate == "inventory_missing": role_status = "inventory_missing"
                else: role_status = "observed"
        require(role_status is not None, "Unknown NPC role state")
        if role_status is None:
            raise ValueError("Unknown role state")
        inputs: list[NpcSavedItem] = []
        for raw_input in array(item["items"], "NPC input observations"):
            source = _closed(raw_input, ("kind", "reference_status", "raw_reference", "artifact_id", "status", "artifact", "equipped_slots"), "NPC input")
            reference_status: ReferenceStatus
            if source["reference_status"] == "present": reference_status = "present"
            elif source["reference_status"] == "missing": reference_status = "missing"
            elif source["reference_status"] == "unresolved": reference_status = "unresolved"
            else: raise ValueError("Unknown reference state")
            status: ItemStatus
            if source["status"] == "reference_missing": status = "reference_missing"
            elif source["status"] == "reference_unresolved": status = "reference_unresolved"
            elif source["status"] == "owned": status = "owned"
            elif source["status"] == "owner_changed": status = "owner_changed"
            elif source["status"] == "gone": status = "gone"
            elif source["status"] == "inventory_missing": status = "inventory_missing"
            else: raise ValueError("Unknown input state")
            inputs.append(NpcSavedItem(_input(source["kind"]), reference_status,
                None if source["raw_reference"] is None else _variable(source["raw_reference"]),
                None if source["artifact_id"] is None else decimal_id(source["artifact_id"], "input artifact", allow_zero=True), status,
                None if source["artifact"] is None else _artifact(source["artifact"]),
                None if source["equipped_slots"] is None else tuple(text(key, "native equipped key") for key in array(source["equipped_slots"], "equipped keys"))))
        selected = NpcSavedRole(_role(item["role"]), role_status,
            None if item["owner_id"] is None else decimal_id(item["owner_id"], "NPC owner"),
            None if item["raw_owner_reference"] is None else _variable(item["raw_owner_reference"]),
            None if item["missing_candidate_marker"] is None else _variable(item["missing_candidate_marker"]),
            None if item["inventory"] is None else SavedInventory.parse(item["inventory"]),
            _variable_rows(item["saved_variables"]), tuple(inputs))
        _validate_role(selected)
        roles.append(selected)
    _roles(tuple(role.role for role in roles))
    owners = [role.owner_id for role in roles if role.owner_id is not None]
    player = decimal_id(row["player_id"], "actual saved player")
    require(len(set(owners)) == len(owners) and player not in owners, "Healthy NPC owners must be distinct from each other/player")
    stamp = text(row["observed_at_utc"], "observation UTC")
    require(datetime.fromisoformat(stamp).utcoffset() == timezone.utc.utcoffset(None), "Observation must carry UTC")
    result = NpcSavedObservation(text(row["machine_id"], "machine ID"), stamp, checked_pin(row["melted_source"], "actual melted saved source"),
        _date(row["saved_date"]), player, NpcFixtureSpec.parse(row["spec"]), phase, baseline, tuple(roles))
    require(type(row["initial_inputs_complete"]) is bool and row["initial_inputs_complete"] is result.initial_inputs_complete,
        "Initial input completeness must be derived from the full explicit state")
    return result


def observe_npc_saved(melted: Path, *, player_id: str, machine_id: str, spec: NpcFixtureSpec,
                      roles: tuple[Role, ...] = HEALTHY_ROLES, phase: Phase = "initial",
                      baseline: NpcInitialBaseline | None = None) -> NpcSavedObservation:
    """Project selected historical saved actors/items. Post needs complete inputs."""
    require(isinstance(melted, Path) and type(spec) is NpcFixtureSpec, "Actual source Path and shared typed spec required")
    player_id, machine_id, roles, phase = decimal_id(player_id, "player"), text(machine_id, "machine ID"), _roles(roles), _phase(phase)
    if phase == "initial":
        require(baseline is None, "Initial phase cannot borrow a baseline")
    else:
        require(type(baseline) is NpcInitialBaseline, "Post phase requires a complete explicit initial baseline")
        if baseline is None:
            raise ValueError("Initial baseline missing")
        baseline = NpcInitialBaseline.parse(baseline.to_json())
        prior = baseline.observation
        require(prior.player_id == player_id and prior.machine_id == machine_id and prior.spec == spec and
            tuple(role.role for role in prior.roles) == roles, "Initial baseline crossed player/machine/spec/roles")
    source_pin = pin(melted)
    players = [body for identity, body in records(melted, ("living",)) if identity == player_id]
    require(len(players) == 1, "Exactly one actual saved living player record required")
    player_entries = parse_block(players[0][players[0].index("{"):])
    player_variables = variables(structured(one(player_entries, "alive_data"), "actual player alive_data"))
    bindings: dict[Role, tuple[SavedVariable | None, SavedVariable | None, str | None]] = {}
    for role in roles:
        reference = player_variables.get("xalw_npc_fixture_owner_" + role)
        marker = player_variables.get("xalw_npc_fixture_missing_" + role)
        require(marker is None or marker == SavedVariable("boolean", "1", None), "Actual missing candidate marker must be true")
        require(reference is None or marker is None, "Candidate missing marker contradicts actual owner reference")
        owner = None if reference is None else saved_character_reference(reference, "NPC owner " + role)
        require(reference is None or owner is not None, "Actual NPC character reference is unresolved")
        if phase == "post" and baseline is not None and owner is not None:
            expected_owner = next(item.owner_id for item in baseline.observation.roles if item.role == role)
            require(owner == expected_owner, "Post NPC owner binding changed from its actual initial actor")
        bindings[role] = reference, marker, owner
    owners = [binding[2] for binding in bindings.values() if binding[2] is not None]
    require(len(set(owners)) == len(owners) and player_id not in owners, "NPC bindings reused another role or actual player")
    actors: dict[str, tuple[str, VariableRows, SavedInventory]] = {}
    for identity, body in records(melted, ("living",)):
        if identity not in owners:
            continue
        require(identity not in actors, "Duplicate actual NPC living record")
        entries = parse_block(body[body.index("{"):])
        values = tuple(variables(structured(one(entries, "alive_data"), "NPC alive_data")).items())
        actors[identity] = body, values, parse_saved_inventory(identity, body)
    wanted: set[str] = set()
    for owner, (_, values, inventory) in actors.items():
        if inventory.owned_ids is not None:
            wanted.update(inventory.owned_ids)
        for kind in INPUTS:
            raw = dict(values).get(_input_variable(kind))
            input_identity = None if raw is None else _reference(raw, "artifact", _input_variable(kind))
            if input_identity is not None:
                wanted.add(input_identity)
    if baseline is not None:
        wanted.update(item.artifact_id for role in baseline.observation.roles for item in role.items if item.artifact_id is not None)
    artifacts: dict[str, SavedArtifact] = {}
    seen: set[str] = set()
    for identity, body in records(melted, ("artifacts", "artifacts")):
        entries = parse_block(body[body.index("{"):])
        owner_field = one(entries, "owner", required=False)
        if owner_field is None:
            require(identity not in wanted, "Selected actual artifact exists without owner; ownerless post-state is unsupported and is not gone")
            continue
        owner = scalar(owner_field, "native artifact owner")
        if identity not in wanted and owner not in owners:
            continue
        require(identity not in seen, "Duplicate selected actual artifact record")
        seen.add(identity)
        artifacts[identity] = SavedArtifact.parse(identity, body)
    for owner, (_, _, inventory) in actors.items():
        if inventory.owned_ids is None:
            continue
        require(all(identity in artifacts and artifacts[identity].owner_id == owner for identity in inventory.owned_ids) and
            all(item.artifact_id in inventory.owned_ids for item in artifacts.values() if item.owner_id == owner),
            "Native saved inventory and actual artifact ownership are not bidirectionally consistent")
    selected_roles: list[NpcSavedRole] = []
    for role in roles:
        reference, marker, bound_owner = bindings[role]
        if bound_owner is None:
            selected_roles.append(NpcSavedRole(role, "candidate_missing" if marker is not None else "owner_reference_missing", None, reference, marker, None, (), ()))
        elif bound_owner not in actors:
            selected_roles.append(NpcSavedRole(role, "character_missing", bound_owner, reference, marker, None, (), ()))
        else:
            _, values, inventory = actors[bound_owner]
            prior_items = {} if baseline is None else {item.kind: item.artifact_id for initial in baseline.observation.roles if initial.role == role for item in initial.items}
            items = tuple(_item(kind, dict(values).get(_input_variable(kind)), prior_items.get(kind), bound_owner, inventory, artifacts) for kind in INPUTS)
            selected_roles.append(NpcSavedRole(role, "inventory_missing" if inventory.status == "missing" else "observed", bound_owner, reference, marker, inventory, values, items))
    dates: list[str] = []
    with melted.open(encoding="utf-8", errors="strict") as stream:
        for line in stream:
            if line.startswith("date="):
                dates.append(_date(line.strip().removeprefix("date=")))
    require(len(dates) == 1, "Exactly one actual saved date required")
    if baseline is not None:
        require(tuple(map(int, dates[0].split("."))) >= tuple(map(int, baseline.observation.saved_date.split("."))), "Post observation predates initial inputs")
    result = NpcSavedObservation(machine_id, utc_now(), source_pin, dates[0], player_id, spec, phase,
        None if baseline is None else baseline.observation.melted_source, tuple(selected_roles))
    return parse_npc_observation(result.to_json())


def calibrate_inventory(comparison: Path, output: Path) -> Pin:
    """Manual only: re-read the two pinned R8 saves; no local paths in CI."""
    require(isinstance(comparison, Path) and isinstance(output, Path) and not output.exists(), "Use actual comparison and fresh calibration output")
    proof = read(comparison)
    require(field(proof, "schema") == "xalw.r8-saved-native-equipment-comparison/v1" and field(proof, "business_pass") is False,
        "Existing explicit saved/native calibration comparison required")
    discovery_ref = checked_pin(field(proof, "actual_saved_discovery"), "original saved record discovery")
    discovery = read(Path(discovery_ref["path"]))
    observations = array(field(discovery, "observations"), "original observations")
    comparisons = array(field(proof, "checkpoints"), "actual saved/native comparisons")
    require(len(observations) == len(comparisons) == 2, "Exactly two original calibration observations required")
    results: list[Object] = []
    for index, (observation, expected) in enumerate(zip(observations, comparisons), 1):
        require(integer(field(observation, "checkpoint"), "original checkpoint", 1, 2) == index and
            integer(field(expected, "checkpoint"), "comparison checkpoint", 1, 2) == index, "Calibration checkpoint ordering differs")
        source = checked_pin(field(observation, "melted"), "actual pinned melted save")
        native = field(expected, "native")
        actor = decimal_id(field(native, "actual_actor_id_decimal"), "native calibrated actor")
        target = decimal_id(field(native, "actual_artifact_id_decimal"), "native calibrated artifact", allow_zero=True)
        original_native = checked_pin(field(native, "original_reply"), "original native equipment query")
        native_rows = array(field(read(Path(original_native["path"])), "rows"), "actual native rows")
        require(len(native_rows) == 1 and field(native_rows[0], "ok") is True and
            field(field(native_rows[0], "plan"), "tool") == "ck3_query_player_artifact_personal_use_v1", "Actual native equipment query must have succeeded")
        actual_native = field(native_rows[0], "result")
        expected_equipped = field(native, "equipped")
        require(type(expected_equipped) is bool and field(actual_native, "equipped") is expected_equipped and
            field(actual_native, "native_equipped_observed") is True and field(actual_native, "read_only") is True and
            field(actual_native, "loaded_source_pins_verified") is True and field(actual_native, "available") is True and
            field(actual_native, "exact_ck3_build") == field(native, "exact_ck3_build") and
            field(actual_native, "exe_sha256") == field(native, "exe_sha256") and
            str(integer(field(actual_native, "played_character_id"), "native actor", 1)) == actor and
            str(integer(field(actual_native, "requested_artifact_id"), "native artifact", 0)) == target and
            integer(field(actual_native, "date_raw"), "native date", 1) == integer(field(native, "native_date_raw"), "comparison date", 1),
            "Calibration native actor/item/date/equipment differs")
        found = [body for identity, body in records(Path(source["path"]), ("living",)) if identity == actor]
        require(len(found) == 1, "Exactly one original calibration actor required")
        inventory = parse_saved_inventory(actor, found[0])
        slots = inventory.slots_for(target)
        require(slots is not None and bool(slots) is expected_equipped and (not slots or slots == ("weapon",)), "New native saved inventory parser disagrees with actual player weapon calibration")
        results.append(object_value({"checkpoint": index, "melted": source, "original_native_query": original_native,
            "native_original_started_at_utc": field(native, "started_at_utc"), "native_original_finished_at_utc": field(native, "finished_at_utc"),
            "inventory": inventory.to_json(), "target_id": target, "saved_equipped_slots": slots, "native_equipped": expected_equipped}))
    return write_once(output, {"schema": "living-artifacts-saved-inventory-parser-calibration-v1", "machine_id": text(field(proof, "machine_id"), "source machine"),
        "observed_at_utc": utc_now(), "comparison": pin(comparison), "observer_source": pin(Path(__file__)), "observations": results,
        "scope": "two-historical-player-weapon-slot-calibrations-only", "npc_ai_business_pass": False, "current_native_observed": False})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration-comparison", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    result = calibrate_inventory(arguments.calibration_comparison, arguments.output)
    print(result["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
