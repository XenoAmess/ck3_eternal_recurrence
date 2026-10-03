"""Read-only hypothetical arrival against the target's current native state."""

from __future__ import annotations

from .public_unit_contract import (
    canonical_public_cunit_token,
    public_cunit_id,
    public_cunit_ids,
)

QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY = (
    "game.command.query-projected-contact-scope-v1-N"
)
QUERY_PROJECTED_CONTACT_SCOPE_V1_STEP_PREFIX = "query-projected-contact-scope-v1-"
PROJECTED_CONTACT_SCOPE_KIND = "hypothetical_arrival_against_current_target_state"

_KEYS = {
    "status", "scope_kind", "snapshot_revision", "date_raw", "subject_army_id",
    "subject_native_carmy_id", "subject_owner_character_id",
    "subject_current_province_id", "target_province_id", "incoming_entry_province_id",
    "observed_target_public_cunit_ids", "observed_target_combat_ids", "transition_kind",
    "selected_current_combat_id", "selected_current_combat_array_index",
    "projected_subject_side", "projected_initiator_is_defender_observable",
    "projected_initiator_is_defender", "incoming_adjacency_kind_raw",
    "projected_attacker_army_ids", "projected_defender_army_ids",
    "contact_projection_inputs_complete",
}


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _province(value: object, name: str) -> int:
    return _integer(value, name, 1, 2**31 - 1)


def _positive_token(value: str) -> int | None:
    if not value or not value.isascii() or not value.isdigit() or value[0] == "0":
        return None
    parsed = int(value)
    return parsed if parsed <= 2**31 - 1 else None


def query_projected_contact_scope_v1_step(
    subject_army_id: int, target_province_id: int, incoming_entry_province_id: int,
) -> str:
    subject = public_cunit_id(subject_army_id, "subject_army_id")
    target = _province(target_province_id, "target_province_id")
    entry = _province(incoming_entry_province_id, "incoming_entry_province_id")
    if target == entry:
        raise ValueError("incoming_entry_province_id must differ from target_province_id")
    return f"{QUERY_PROJECTED_CONTACT_SCOPE_V1_STEP_PREFIX}{subject}-to-{target}-from-{entry}"


def parse_query_projected_contact_scope_v1_step(step: object) -> tuple[int, int, int] | None:
    if not isinstance(step, str) or not step.startswith(QUERY_PROJECTED_CONTACT_SCOPE_V1_STEP_PREFIX):
        return None
    subject_text, to_marker, rest = step.removeprefix(
        QUERY_PROJECTED_CONTACT_SCOPE_V1_STEP_PREFIX
    ).partition("-to-")
    target_text, from_marker, entry_text = rest.partition("-from-")
    if not to_marker or not from_marker:
        return None
    subject = canonical_public_cunit_token(subject_text)
    target = _positive_token(target_text)
    entry = _positive_token(entry_text)
    if subject is None or target is None or entry is None or target == entry:
        return None
    return subject, target, entry


def projected_contact_subject_scope(snapshot: dict[str, object], subject_army_id: int) -> dict[str, object]:
    """Resolve the actual controllable subject; no hypothetical position is inserted."""
    subject = public_cunit_id(subject_army_id, "subject_army_id")
    armies = snapshot.get("player_armies")
    if not isinstance(armies, list):
        raise ValueError("projected contact requires current player_armies")
    matches = [row for row in armies if isinstance(row, dict)
               and type(row.get("army_id")) is int and row.get("army_id") == subject
               and row.get("controllable") is True]
    if len(matches) != 1:
        raise ValueError("projected contact subject is outside the controllable player scope")
    row = matches[0]
    _province(row.get("current_province_id"), "subject_current_province_id")
    _province(row.get("owner_character_id"), "subject_owner_character_id")
    return row


def normalize_projected_contact_scope(
    value: object, *, expected_subject_army_id: int, expected_target_province_id: int,
    expected_incoming_entry_province_id: int, expected_date_raw: int,
    expected_snapshot_revision: int, expected_subject_current_province_id: int | None = None,
    expected_subject_owner_character_id: int | None = None,
) -> dict[str, object]:
    """Preserve actual source fields and the native projection's ordered side arrays."""
    query_projected_contact_scope_v1_step(expected_subject_army_id, expected_target_province_id,
                                         expected_incoming_entry_province_id)
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native projected_contact_scope has a malformed schema")
    if (value["status"] != "available" or value["scope_kind"] != PROJECTED_CONTACT_SCOPE_KIND
            or value["contact_projection_inputs_complete"] is not True):
        raise ValueError("native projected_contact_scope inputs are unavailable")
    subject = public_cunit_id(value["subject_army_id"], "subject_army_id")
    native_army = _province(value["subject_native_carmy_id"], "subject_native_carmy_id")
    owner = _province(value["subject_owner_character_id"], "subject_owner_character_id")
    current = _province(value["subject_current_province_id"], "subject_current_province_id")
    target = _province(value["target_province_id"], "target_province_id")
    entry = _province(value["incoming_entry_province_id"], "incoming_entry_province_id")
    date = _integer(value["date_raw"], "date_raw", -(2**31), 2**31 - 1)
    revision = _integer(value["snapshot_revision"], "snapshot_revision", 1, 2**64 - 1)
    if (subject != expected_subject_army_id or target != expected_target_province_id
            or entry != expected_incoming_entry_province_id or target == entry
            or date != expected_date_raw or revision != expected_snapshot_revision
            or (expected_subject_current_province_id is not None and current != expected_subject_current_province_id)
            or (expected_subject_owner_character_id is not None and owner != expected_subject_owner_character_id)):
        raise ValueError("native projected_contact_scope source binding disagrees")
    observed_units = public_cunit_ids(value["observed_target_public_cunit_ids"], "observed_target_public_cunit_ids")
    combat_values = value["observed_target_combat_ids"]
    if not isinstance(combat_values, list):
        raise ValueError("observed_target_combat_ids must be a list")
    combats = [_province(item, "observed_target_combat_ids") for item in combat_values]
    if len(set(combats)) != len(combats):
        raise ValueError("observed_target_combat_ids contains duplicates")
    attackers = public_cunit_ids(value["projected_attacker_army_ids"], "projected_attacker_army_ids")
    defenders = public_cunit_ids(value["projected_defender_army_ids"], "projected_defender_army_ids")
    if set(attackers) & set(defenders):
        raise ValueError("projected contact sides overlap")
    selected_value = value["selected_current_combat_id"]
    selected = None if selected_value is None else _province(selected_value, "selected_current_combat_id")
    index_value = value["selected_current_combat_array_index"]
    index = None if index_value is None else _integer(index_value, "selected_current_combat_array_index", 0, 2**31 - 1)
    observable = value["projected_initiator_is_defender_observable"]
    initiator = value["projected_initiator_is_defender"]
    if type(observable) is not bool or (observable and type(initiator) is not bool) or (not observable and initiator is not None):
        raise ValueError("projected initiator role availability disagrees")
    adjacency = _integer(value["incoming_adjacency_kind_raw"], "incoming_adjacency_kind_raw", 0, 3)
    transition = value["transition_kind"]
    side = value["projected_subject_side"]
    if transition == "none":
        if selected is not None or index is not None or side != "none" or observable or attackers or defenders:
            raise ValueError("complete none projection has contact participants")
    elif transition in {"join_existing", "create_new"}:
        own = attackers if side == "attacker" else defenders if side == "defender" else []
        other = defenders if side == "attacker" else attackers
        if not own or not other or subject not in own or subject in other:
            raise ValueError("projected subject side membership disagrees")
        if transition == "join_existing":
            if (selected is None or index is None or index >= len(combats) or combats[index] != selected
                    or observable or own[-1] != subject):
                raise ValueError("join projection lacks selected current combat or native side append")
        elif (selected is not None or index is not None or not observable or own != [subject]
              or initiator != (side == "defender") or any(item not in observed_units for item in other)):
            raise ValueError("new contact projection role or current target participants disagree")
    else:
        raise ValueError("projected contact transition_kind is unknown")
    return {**value, "subject_army_id": subject, "subject_native_carmy_id": native_army,
            "subject_owner_character_id": owner, "subject_current_province_id": current,
            "target_province_id": target, "incoming_entry_province_id": entry,
            "snapshot_revision": revision, "date_raw": date,
            "observed_target_public_cunit_ids": observed_units, "observed_target_combat_ids": combats,
            "selected_current_combat_id": selected, "selected_current_combat_array_index": index,
            "incoming_adjacency_kind_raw": adjacency,
            "projected_attacker_army_ids": attackers, "projected_defender_army_ids": defenders}
