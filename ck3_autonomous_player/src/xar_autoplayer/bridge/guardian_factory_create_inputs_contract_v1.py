"""Validate copied factory creation inputs from the same private paused job.

The DWORD and QWORD stay raw. This decoder neither calls a factory nor assigns
the QWORD a pointer role, relation kind, membership or outcome.
"""
from __future__ import annotations

from copy import deepcopy

LEAF = "factory_create_inputs_v1"
DISCOVERY = "xar.ck3.guardian-factory-discovery.v1"
EXACT_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
KEYS = ("has_relation_guardian", "has_relation_ward")


def _uint(value: object, bits: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < 2**bits:
        raise ValueError(f"{name}: unsigned {bits}-bit value required")
    return value


def _flag(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name}: boolean required")
    return value


def _optional_u32(value: object, name: str) -> int | None:
    return None if value is None else _uint(value, 32, name)


def _raw_field(value: object, bits: int, name: str) -> int | None:
    if not isinstance(value, dict) or set(value) != {"available", "raw_value"}:
        raise ValueError(f"{name}: malformed availability/value pair")
    available = _flag(value["available"], name + ".available")
    if available:
        return _uint(value["raw_value"], bits, name + ".raw_value")
    if value["raw_value"] is not None:
        raise ValueError(f"{name}: unavailable read must retain null")
    return None


def validate_guardian_factory_create_inputs_v1(
    value: object, *, command_result: object, snapshot: dict[str, object],
    family_result: dict[str, object],
) -> dict[str, object] | None:
    """Return an owned native sidecar, or None for the legacy absent sibling.

    A malformed new sibling raises ValueError. The ordinary family result has
    already been retained by the capture wrapper and is independent of it.
    """
    if not isinstance(value, dict):
        raise ValueError("guardian discovery must be an object")
    rows = value.get("factories")
    if not isinstance(rows, list) or len(rows) != 2 or any(
        not isinstance(row, dict) for row in rows
    ) or tuple(row.get("key") for row in rows) != KEYS:
        raise ValueError("guardian discovery requires two fixed ordered keys")
    present = [LEAF in row for row in rows]
    if not any(present):
        if CURRENT_RELATION in value:
            raise ValueError("current relation lacks its same-query factory input version")
        return None
    if not all(present):
        raise ValueError("guardian discovery has mixed factory input versions")
    if (value.get("schema") != DISCOVERY
            or type(value.get("schema_version")) is not int
            or value["schema_version"] != 1):
        raise ValueError("guardian discovery schema changed")
    for key, expected in (("read_only", True), ("advertised", False),
                          ("source_discovery_only", True),
                          ("guardian_membership_observed", False), ("paused", True)):
        if value.get(key) is not expected:
            raise ValueError(f"guardian discovery {key} changed")
    if snapshot.get("paused") is not True:
        raise ValueError("guardian inputs lack the original paused snapshot")
    qualified = _flag(value.get("qualified"), "qualified")
    if (value.get("status") != ("captured" if qualified else "unavailable")
            or not isinstance(value.get("unavailable_reason"), str)
            or (value["unavailable_reason"] != "" if qualified
                else value["unavailable_reason"] == "")):
        raise ValueError("guardian discovery qualification is inconsistent")
    if not isinstance(command_result, dict) or (
        command_result.get("type") != "command_result"
        or type(command_result.get("protocol_version")) is not int
        or command_result["protocol_version"] != 1
        or command_result.get("ok") is not True
    ):
        raise ValueError("guardian inputs lack the retained original command result")
    request = command_result.get("request_id")
    if not isinstance(request, str) or not request or value.get("request_id") != request:
        raise ValueError("guardian input request differs from the actual family job")
    result = command_result.get("result")
    if not isinstance(result, dict) or (
        result.get("step") != "query-current-first-heir-relationship-v1-private"
        or result.get("accepted") is not True
        or result.get("private_build") is not True
        or result.get("read_only") is not True
        or result.get("advertised") is not False
    ):
        raise ValueError("guardian inputs lack the original private family result")
    revision = _uint(snapshot.get("native_revision"), 64, "snapshot.native_revision")
    if revision == 0 or any(type(container.get("native_revision")) is not int
        or container["native_revision"] != revision
        for container in (value, result, family_result)):
        raise ValueError("guardian input native revision changed")
    date = snapshot.get("date_raw")
    if type(date) is not int or type(value.get("date_raw")) is not int or value["date_raw"] != date:
        raise ValueError("guardian input date changed")
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, dict) else snapshot.get("played_character_id")
    if type(actor) is not int or not 0 < actor < 2**31 or value.get("played_character_id") != actor:
        raise ValueError("guardian input played character changed")
    if type(value.get("played_character_id")) is not int:
        raise ValueError("guardian input played character must be an integer")
    sha = value.get("executable_sha256")
    family_sha = family_result.get("exe_sha256")
    if (not isinstance(sha, str) or sha.upper() != EXACT_SHA
            or not isinstance(family_sha, str) or family_sha.upper() != EXACT_SHA
            or family_result.get("exact_ck3_build") != "1.20.0.4"):
        raise ValueError("guardian inputs lack the same exact native build")
    heir = family_result.get("heir_character_id")
    native_heir = heir if heir is not None else -1
    if type(native_heir) is not int or any(
        type(container.get("heir_character_id")) is not int
        or container["heir_character_id"] != native_heir for container in (value, result)
    ):
        raise ValueError("guardian input heir binding changed")
    base = _uint(value.get("module_base"), 64, "module_base")
    image_size = _uint(value.get("image_size"), 64, "image_size")
    _uint(value.get("pump_epoch"), 64, "pump_epoch")
    _uint(value.get("thread_id"), 32, "thread_id")
    for row in rows:
        child = row[LEAF]
        if not isinstance(child, dict) or set(child) != {
            "schema_version", "field_10_dword", "field_18_qword"
        } or type(child.get("schema_version")) is not int or child["schema_version"] != 1:
            raise ValueError("factory creation input schema changed")
        dword = _raw_field(child["field_10_dword"], 32, "field_10_dword")
        qword = _raw_field(child["field_18_qword"], 64, "field_18_qword")
        record = _optional_u32(row.get("record_name_id"), "record_name_id")
        if dword != record:
            raise ValueError("factory DWORD differs from its original record_name_id")
        name_id = _optional_u32(row.get("name_id"), "name_id")
        map_id = _optional_u32(row.get("map_name_id"), "map_name_id")
        factory = _uint(row.get("factory_address"), 64, "factory_address")
        _uint(row.get("vtable_address"), 64, "vtable_address")
        _uint(row.get("opaque_descriptor_address"), 64, "opaque_descriptor_address")
        status = row.get("status")
        if status not in {"found", "name_missing", "factory_missing", "unavailable"}:
            raise ValueError("factory lookup status changed")
        if not isinstance(row.get("unavailable_reason"), str):
            raise ValueError("factory lookup reason missing")
        if status == "found":
            stored = row.get("stored_name")
            folded = "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in stored) if isinstance(stored, str) else None
            if (not qualified or factory == 0 or name_id is None or map_id != name_id
                    or record is None or folded != row["key"]
                    or row["unavailable_reason"] != ""):
                raise ValueError("factory input row lost its actual key/name/factory association")
        elif qword is not None:
            raise ValueError("factory QWORD is present without a found source factory")
        if not qualified and (dword is not None or qword is not None):
            raise ValueError("unqualified completion cannot retain available factory inputs")
        slots = row.get("virtual_slots")
        if not isinstance(slots, list) or len(slots) != 4:
            raise ValueError("factory input row lost its original virtual slots")
        for index, slot in enumerate(slots):
            if not isinstance(slot, dict) or type(slot.get("slot_index")) is not int or slot["slot_index"] != index:
                raise ValueError("factory virtual-slot order changed")
            available = _flag(slot.get("available"), "virtual_slot.available")
            address, rva = slot.get("address"), slot.get("rva")
            if not available:
                if address is not None or rva is not None:
                    raise ValueError("unavailable virtual slot must retain null")
                continue
            address = _uint(address, 64, "virtual_slot.address")
            in_image = base != 0 and base <= address and address - base < image_size
            if rva is not None:
                _uint(rva, 64, "virtual_slot.rva")
                if not in_image or rva != address - base:
                    raise ValueError("factory virtual-slot RVA/address association changed")
            elif in_image:
                raise ValueError("in-image factory virtual slot lost its native RVA")
    if CURRENT_RELATION in value:
        _validate_current_family_relation_v1(
            value[CURRENT_RELATION], factories=rows, qualified=qualified,
            actor=actor, heir=native_heir,
        )
    return deepcopy(value)


CURRENT_RELATION = "current_family_relation_v1"
DECISION_INPUTS = "guardian_family_decision_inputs_v1"
_RELATION_TRUE_BASES = {"entry_raw_equal", "tag2_row_raw_equal", "fallback_raw_equal"}
_RELATION_FALSE_BASES = {
    "target_tag_rejected", "root_state_rejected", "target_state_rejected",
    "root_peer_extension_absent", "peer_absent", "relation_entries_empty",
    "relation_entries_exhausted",
}


def project_guardian_family_decision_inputs_v1(
    owned_native_sidecar: dict[str, object] | None, *,
    family_result: dict[str, object],
) -> dict[str, object]:
    """Expose independent facts from the already validated same-query results.

    Callers supply the owned result of validate_guardian_factory_create_inputs_v1
    and the existing normalized family query. This adapter reads no native data.
    The named relation rows describe played -> current first heir; they do not
    identify a child's guardian, choose an educator or authorize an interaction.
    """
    from .current_first_heir_descendants_v1 import LEAF as DESCENDANTS
    from ..family_generation_education_inputs_v1 import (
        derive_family_generation_education_inputs_v1,
    )

    revision = _uint(family_result.get("native_revision"), 64, "family.native_revision")
    if revision == 0:
        raise ValueError("decision inputs require the normalized native revision")
    heir = family_result.get("heir_character_id")
    native_heir = -1 if heir is None else heir
    if type(native_heir) is not int or not -(2**31) <= native_heir < 2**31:
        raise ValueError("decision inputs require the normalized full heir identity")
    descendants = family_result.get(DESCENDANTS)
    if descendants is not None and not isinstance(descendants, dict):
        raise ValueError("decision inputs require normalized descendants")

    actor = descendants.get("played_character_id") if descendants is not None else None
    date = descendants.get("date_raw") if descendants is not None else None
    relation = None
    if owned_native_sidecar is not None:
        if (not isinstance(owned_native_sidecar, dict)
                or owned_native_sidecar.get("schema") != DISCOVERY
                or type(owned_native_sidecar.get("native_revision")) is not int
                or owned_native_sidecar["native_revision"] != revision
                or type(owned_native_sidecar.get("heir_character_id")) is not int
                or owned_native_sidecar["heir_character_id"] != native_heir):
            raise ValueError("decision inputs lost the owned family query binding")
        sidecar_actor = owned_native_sidecar["played_character_id"]
        sidecar_date = owned_native_sidecar["date_raw"]
        if (actor is not None and actor != sidecar_actor
                or date is not None and date != sidecar_date):
            raise ValueError("decision inputs combine different descendant frames")
        actor, date = sidecar_actor, sidecar_date
        relation = owned_native_sidecar.get(CURRENT_RELATION)

    if descendants is not None and (
            type(descendants.get("native_revision")) is not int
            or descendants["native_revision"] != revision
            or descendants.get("heir_character_id") not in (None, heir)):
        raise ValueError("decision inputs lost the normalized descendant binding")

    relation_rows = []
    if relation is not None:
        for row in relation["rows"]:
            relation_rows.append({
                "key": row["key"], "available": row["available"],
                "value": row["raw_value"], "basis": row["basis"],
                "unavailable_reason": row["unavailable_reason"],
            })
    else:
        relation_rows = [{
            "key": key, "available": False, "value": None,
            "basis": "", "unavailable_reason": "current_relation_not_observed",
        } for key in KEYS]

    return {
        "schema": "xar.guardian-family-decision-inputs.v1", "schema_version": 1,
        "read_only": True, "source_projection_only": True,
        "native_trigger_invoked": False,
        "frame": {
            "native_revision": revision, "played_character_id": actor,
            "heir_character_id": heir, "date_raw": date,
        },
        "relation": {
            "direction": "played_to_current_first_heir",
            "ready": relation["ready"] if relation is not None else False,
            "rows": relation_rows,
        },
        # Aggregate completeness is diagnostic; callers consume individual
        # leaf_availability entries, including available focus absence.
        "children": derive_family_generation_education_inputs_v1(descendants),
    }


def _optional_uint(value: object, bits: int, name: str) -> int | None:
    return None if value is None else _uint(value, bits, name)


def _optional_i32(value: object, name: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not -(2**31) <= value < 2**31:
        raise ValueError(f"{name}: signed 32-bit value required")
    return value


def _validate_current_family_relation_v1(
    value: object, *, factories: list[dict], qualified: bool, actor: int, heir: int,
) -> None:
    """Check the owned lower relation projection without invoking a trigger."""
    fields = {
        "schema_version", "read_only", "source", "direction",
        "source_projection_only", "native_trigger_invoked", "parsed_target_observed",
        "root_character_id", "target_character_id", "root_address", "target_address",
        "target_tag_raw", "root_death_data_raw", "target_death_data_raw",
        "identity_round_trip", "sample_stable", "ready", "rows",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("current family relation schema changed")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("current family relation schema version changed")
    for key, expected in (
        ("read_only", True), ("source_projection_only", True),
        ("native_trigger_invoked", False), ("parsed_target_observed", False),
        ("source", "actual_4217820_lower_relation_projection"),
        ("direction", "played_to_current_first_heir"),
    ):
        if type(value[key]) is not type(expected) or value[key] != expected:
            raise ValueError(f"current family relation {key} changed")
    root_id = _uint(value["root_character_id"], 32, "relation.root_character_id")
    target_id = _uint(value["target_character_id"], 32, "relation.target_character_id")
    if root_id != actor & 0xFFFFFFFF or target_id != heir & 0xFFFFFFFF:
        raise ValueError("current family relation differs from the same query's full IDs")
    root = _optional_uint(value["root_address"], 64, "relation.root_address")
    target = _optional_uint(value["target_address"], 64, "relation.target_address")
    tag = _optional_uint(value["target_tag_raw"], 32, "relation.target_tag_raw")
    root_state = _optional_uint(value["root_death_data_raw"], 64, "relation.root_death_data_raw")
    target_state = _optional_uint(value["target_death_data_raw"], 64, "relation.target_death_data_raw")
    identity = _flag(value["identity_round_trip"], "relation.identity_round_trip")
    stable = _flag(value["sample_stable"], "relation.sample_stable")
    ready = _flag(value["ready"], "relation.ready")
    if identity and (not root or not target or 0xFFFFFFFF in (root_id, target_id)):
        raise ValueError("current family relation identity lacks resolved full-ID objects")
    rows = value["rows"]
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("current family relation requires the two fixed source keys")
    row_fields = {
        "key", "available", "raw_value", "basis", "unavailable_reason",
        "predicate_mode", "descriptor_reached", "descriptor_raw", "peer_address",
        "peer_count_raw", "relation_count_raw",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != row_fields or row["key"] != KEYS[index]:
            raise ValueError("current family relation key/row schema changed")
        available = _flag(row["available"], "relation.available")
        reached = _flag(row["descriptor_reached"], "relation.descriptor_reached")
        descriptor = _optional_uint(row["descriptor_raw"], 64, "relation.descriptor_raw")
        peer = _optional_uint(row["peer_address"], 64, "relation.peer_address")
        peer_count = _optional_i32(row["peer_count_raw"], "relation.peer_count_raw")
        count = _optional_i32(row["relation_count_raw"], "relation.relation_count_raw")
        if type(row["predicate_mode"]) is not int or row["predicate_mode"] != 0:
            raise ValueError("current family relation predicate mode changed")
        basis, reason = row["basis"], row["unavailable_reason"]
        if not isinstance(basis, str) or not isinstance(reason, str):
            raise ValueError("current family relation source basis/reason missing")
        if descriptor is not None:
            factory = factories[index]
            raw_input = factory[LEAF]["field_18_qword"]
            if (not reached or factory["status"] != "found"
                    or raw_input["available"] is not True
                    or descriptor != raw_input["raw_value"]):
                raise ValueError("current relation descriptor lost its same-key factory input")
        if reached and (count is None or count <= 0 or not peer or peer_count is None or peer_count <= 0):
            raise ValueError("current relation descriptor has no reached positive collection")
        if not reached and descriptor is not None:
            raise ValueError("current relation retained an unreached descriptor")
        if available:
            raw = _flag(row["raw_value"], "relation.raw_value")
            if (not qualified or not identity or not stable or reason != ""
                    or basis not in (_RELATION_TRUE_BASES if raw else _RELATION_FALSE_BASES)):
                raise ValueError("current relation known value lacks its qualified source branch")
            if basis == "target_tag_rejected":
                admitted = tag is not None and tag != 0x43686172
            elif basis == "root_state_rejected":
                admitted = tag == 0x43686172 and root_state is not None and root_state != 0
            elif basis == "target_state_rejected":
                admitted = tag == 0x43686172 and root_state == 0 and target_state is not None and target_state != 0
            else:
                admitted = tag == 0x43686172 and root_state == 0 and target_state == 0
            if not admitted:
                raise ValueError("current relation source branch contradicts copied target/state inputs")
            if basis in _RELATION_TRUE_BASES or basis == "relation_entries_exhausted":
                if not reached or descriptor is None:
                    raise ValueError("current relation comparison lost its reached raw descriptor")
            elif reached or descriptor is not None or count not in (None, 0):
                raise ValueError("current relation early false branch reached an extra descriptor")
            if basis == "peer_absent" and (peer != 0 or peer_count is None or peer_count < 0):
                raise ValueError("current relation absent peer lacks its source-null lookup")
            if basis == "relation_entries_empty" and (not peer or peer_count is None or peer_count <= 0 or count != 0):
                raise ValueError("current relation empty collection lacks its observed zero count")
        elif row["raw_value"] is not None or basis != "" or reason == "":
            raise ValueError("current relation unavailable input became a known value")
        if not qualified and (available or reached or any(raw is not None for raw in
                (descriptor, peer, peer_count, count))):
            raise ValueError("unqualified completion retained stale relation inputs")
    if ready != (qualified and identity and stable and all(row["available"] for row in rows)):
        raise ValueError("current family relation readiness contradicts independent availability")
    if not qualified and (identity or stable or ready or any(raw is not None for raw in
            (root, target, tag, root_state, target_state))):
        raise ValueError("unqualified completion retained stale relation objects")
