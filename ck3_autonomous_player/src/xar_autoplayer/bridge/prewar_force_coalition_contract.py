"""Pure validation of the partial, declaration-bound prewar observation.

This v1 DTO does not contain a complete initial coalition or an enemy force
upper bound.  Its observed rows cannot authorize a declaration.  The caller
must supply the binding from the current response envelope's independent
top-level execution receipt, after matching that envelope's fresh request ID.
Copying the domain's ticket fields or combining historical cache fields is
not a request binding.  The caller need not predict a native ticket or issue a
second admission query.  Connection and ruler-episode identity remain the
outer driver's responsibility.
"""

from __future__ import annotations

from collections.abc import Mapping
import re

from .public_unit_contract import public_cunit_id
from .version_identity import CK3_12004, require_exact_native_build


SCHEMA_VERSION = 1
STATUS = "available_partial"
_UINT64_MAX = (1 << 64) - 1
_INT64_MAX = (1 << 63) - 1
_INT32_MAX = (1 << 31) - 1
_DECLARATION_ID = re.compile(r"([1-9][0-9]*)-(0|[1-9][0-9]*)-(-1|0|[1-9][0-9]*)")
_FIELDS = frozenset({
    "schema_version", "status", "read_only", "game_version",
    "executable_sha256", "capture_epoch", "native_revision",
    "public_revision", "date_raw", "actor_character_id", "declaration_id",
    "selected_declaration", "effective_target_character_id", "ticket",
    "query_sequence", "current_allies", "owner_forces",
    "actor_ready_unraised_lower_soldiers", "enemy_upper_soldiers",
    "enemy_force_coverage_complete", "complete_initial_participants_ready",
    "automatic_declaration_enabled",
})
_SELECTED_FIELDS = frozenset({
    "target_character_id", "casus_belli_index", "casus_belli_key",
    "configuration_index", "claimant_character_id", "target_title_ids",
})
_REQUEST_FIELDS = frozenset({"ticket", "query_sequence", "capture_epoch"})
_ALLIES_FIELDS = frozenset({
    "owner_character_id", "available", "unavailable_reason",
    "collection_complete", "ally_character_ids",
    "unresolved_source_character_ids", "dead_source_character_ids",
})
_FORCE_FIELDS = frozenset({
    "owner_character_id", "raised_available", "raised_unavailable_reason",
    "raised_armies", "raised_current_soldiers", "raised_maximum_soldiers",
    "unraised_available", "unraised_unavailable_reason", "unraised_soldiers",
    "native_raise_legal",
})
_ARMY_FIELDS = frozenset({"army_id", "current_soldiers", "maximum_soldiers"})


def _object(value: object, fields: frozenset[str], name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ValueError(f"prewar force/coalition {name} has unexpected fields")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"prewar force/coalition {name} is outside [{minimum}, {maximum}]")
    return value


def _character(value: object, name: str) -> int:
    # Primary roles retain the existing public declaration/assessment scope.
    # Native ally/owner handles and declaration claimant fields differ.
    return _integer(value, name, 1, _INT32_MAX)


def _native_character(value: object, name: str) -> int:
    # The resolver indexes low bits, then verifies the complete signed ID.
    # Slot zero and high-bit generations are valid; only -1 is absent.
    result = _integer(value, name, -(1 << 31), _INT32_MAX)
    if result == -1:
        raise ValueError(f"prewar force/coalition {name} cannot be the absent CharacterID")
    return result


def _title(value: object, name: str) -> int:
    # The canonical declaration tuple permits TitleID zero.
    return _integer(value, name, 0, _INT32_MAX)


def _count(value: object, name: str, *, nullable: bool = False) -> int | None:
    return None if nullable and value is None else _integer(value, name, 0, _INT64_MAX)


def _leaf_count(value: object, name: str) -> int | None:
    # The current soldier getters return int32; only sums use int64.
    return None if value is None else _integer(value, name, 0, _INT32_MAX)


def _boolean(value: object, name: str, *, nullable: bool = False) -> bool | None:
    if nullable and value is None:
        return None
    if type(value) is not bool:
        raise ValueError(f"prewar force/coalition {name} must be a boolean")
    return value


def _reason(value: object, name: str, available: bool) -> str | None:
    if available:
        if value is not None:
            raise ValueError(f"prewar force/coalition {name} must be null when available")
    elif not isinstance(value, str) or not value.strip():
        raise ValueError(f"prewar force/coalition {name} must describe the unavailable stage")
    return value


def _characters(value: object, name: str, *, nullable: bool = False) -> list[int] | None:
    if nullable and value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"prewar force/coalition {name} must be a character array")
    result = [_native_character(item, f"{name}[{index}]") for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise ValueError(f"prewar force/coalition {name} repeats a CharacterID")
    return result


def _selected(value: object, name: str) -> dict[str, object]:
    row = _object(value, _SELECTED_FIELDS, name)
    target = _character(row["target_character_id"], f"{name}.target_character_id")
    cb_index = _integer(row["casus_belli_index"], f"{name}.casus_belli_index", 0, _INT32_MAX)
    configuration = _integer(row["configuration_index"], f"{name}.configuration_index", -1, _INT32_MAX)
    claimant = _integer(row["claimant_character_id"], f"{name}.claimant_character_id", -1, _INT32_MAX)
    key = row["casus_belli_key"]
    if not isinstance(key, str) or not key or key != key.strip():
        raise ValueError(f"prewar force/coalition {name}.casus_belli_key is malformed")
    titles = row["target_title_ids"]
    if not isinstance(titles, list):
        raise ValueError(f"prewar force/coalition {name}.target_title_ids must be an ordered array")
    normalized_titles = [
        _title(title, f"{name}.target_title_ids[{index}]")
        for index, title in enumerate(titles)
    ]
    return {
        "target_character_id": target, "casus_belli_index": cb_index,
        "casus_belli_key": key, "configuration_index": configuration,
        "claimant_character_id": claimant, "target_title_ids": normalized_titles,
    }


def _declaration(value: object, name: str) -> tuple[str, dict[str, object]]:
    if not isinstance(value, Mapping):
        raise ValueError(f"prewar force/coalition {name} must be a declaration")
    declaration_id = value.get("declaration_id")
    match = _DECLARATION_ID.fullmatch(declaration_id) if isinstance(declaration_id, str) else None
    if match is None:
        raise ValueError(f"prewar force/coalition {name}.declaration_id is not canonical")
    if not _SELECTED_FIELDS.issubset(value):
        raise ValueError(f"prewar force/coalition {name} lost the selected declaration tuple")
    selected = _selected({key: value[key] for key in _SELECTED_FIELDS}, name)
    identity = tuple(int(part) for part in match.groups())
    if identity != (
        selected["target_character_id"], selected["casus_belli_index"],
        selected["configuration_index"],
    ):
        raise ValueError(f"prewar force/coalition {name} declaration ID and tuple disagree")
    return declaration_id, selected


def _allies(value: object, primary_owners: tuple[int, int]) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) != len(primary_owners):
        raise ValueError("prewar force/coalition current_allies must contain both primary owners")
    result: list[dict[str, object]] = []
    for index, expected_owner in enumerate(primary_owners):
        name = f"current_allies[{index}]"
        row = _object(value[index], _ALLIES_FIELDS, name)
        owner = _native_character(row["owner_character_id"], f"{name}.owner_character_id")
        if owner != expected_owner:
            raise ValueError("prewar force/coalition current_allies owner/order drifted")
        available = _boolean(row["available"], f"{name}.available")
        complete = _boolean(row["collection_complete"], f"{name}.collection_complete")
        reason = _reason(row["unavailable_reason"], f"{name}.unavailable_reason", available)
        allies = _characters(row["ally_character_ids"], f"{name}.ally_character_ids", nullable=True)
        unresolved = _characters(row["unresolved_source_character_ids"], f"{name}.unresolved_source_character_ids", nullable=True)
        dead = _characters(row["dead_source_character_ids"], f"{name}.dead_source_character_ids", nullable=True)
        if available is not complete:
            raise ValueError("prewar force/coalition ally availability must describe a complete collection")
        if complete and (allies is None or unresolved is None or dead is None or unresolved):
            raise ValueError("prewar force/coalition complete allies lost a collection or retain unresolved sources")
        if allies is not None and owner in allies:
            raise ValueError("prewar force/coalition owner cannot be its own ally")
        if allies is None and (unresolved is not None or dead is not None):
            raise ValueError("prewar force/coalition unread allies cannot claim observed source arrays")
        if allies is not None and (unresolved is None or dead is None):
            raise ValueError("prewar force/coalition observed allies require source diagnostic arrays")
        if (
            set(allies or ()) & set(unresolved or ())
            or set(allies or ()) & set(dead or ())
            or set(unresolved or ()) & set(dead or ())
        ):
            raise ValueError("prewar force/coalition observed, unresolved and dead ally sources overlap")
        result.append({
            "owner_character_id": owner, "available": available,
            "unavailable_reason": reason, "collection_complete": complete,
            "ally_character_ids": allies,
            "unresolved_source_character_ids": unresolved,
            "dead_source_character_ids": dead,
        })
    return result


def _forces(value: object, expected_owners: set[int]) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("prewar force/coalition owner_forces must be an array")
    owners: set[int] = set()
    armies_seen: set[int] = set()
    result: list[dict[str, object]] = []
    for index, raw in enumerate(value):
        name = f"owner_forces[{index}]"
        row = _object(raw, _FORCE_FIELDS, name)
        owner = _native_character(row["owner_character_id"], f"{name}.owner_character_id")
        if owner in owners or owner not in expected_owners:
            raise ValueError("prewar force/coalition owner_forces repeats or invents an owner")
        owners.add(owner)
        raised_available = _boolean(row["raised_available"], f"{name}.raised_available")
        raised_reason = _reason(row["raised_unavailable_reason"], f"{name}.raised_unavailable_reason", raised_available)
        raw_armies = row["raised_armies"]
        if raw_armies is not None and not isinstance(raw_armies, list):
            raise ValueError(f"prewar force/coalition {name}.raised_armies must be an array or null")
        armies: list[dict[str, object]] | None = None if raw_armies is None else []
        current_total = maximum_total = 0
        counts_complete = raw_armies is not None
        for ordinal, raw_army in enumerate(raw_armies or ()):
            army_name = f"{name}.raised_armies[{ordinal}]"
            army = _object(raw_army, _ARMY_FIELDS, army_name)
            army_id = public_cunit_id(army["army_id"], f"{army_name}.army_id")
            if army_id in armies_seen:
                raise ValueError("prewar force/coalition raised armies repeat a public CUnit ID")
            armies_seen.add(army_id)
            current = _leaf_count(army["current_soldiers"], f"{army_name}.current_soldiers")
            maximum = _leaf_count(army["maximum_soldiers"], f"{army_name}.maximum_soldiers")
            counts_complete = counts_complete and current is not None and maximum is not None
            current_total += current if current is not None else 0
            maximum_total += maximum if maximum is not None else 0
            if current_total > _INT64_MAX or maximum_total > _INT64_MAX:
                raise ValueError("prewar force/coalition raised soldier totals overflow")
            assert armies is not None
            armies.append({"army_id": army_id, "current_soldiers": current, "maximum_soldiers": maximum})
        current = _count(row["raised_current_soldiers"], f"{name}.raised_current_soldiers", nullable=True)
        maximum = _count(row["raised_maximum_soldiers"], f"{name}.raised_maximum_soldiers", nullable=True)
        if raised_available:
            if not counts_complete or current != current_total or maximum != maximum_total:
                raise ValueError("prewar force/coalition ready raised aggregates lack complete matching rows")
        elif current is not None or maximum is not None:
            raise ValueError("prewar force/coalition partial raised observations cannot claim aggregates")
        unraised_available = _boolean(row["unraised_available"], f"{name}.unraised_available")
        unraised_reason = _reason(row["unraised_unavailable_reason"], f"{name}.unraised_unavailable_reason", unraised_available)
        unraised = _leaf_count(row["unraised_soldiers"], f"{name}.unraised_soldiers")
        if unraised_available is not (unraised is not None):
            raise ValueError("prewar force/coalition unraised readiness and observed count disagree")
        raise_legal = _boolean(row["native_raise_legal"], f"{name}.native_raise_legal", nullable=True)
        result.append({
            "owner_character_id": owner, "raised_available": raised_available,
            "raised_unavailable_reason": raised_reason, "raised_armies": armies,
            "raised_current_soldiers": current, "raised_maximum_soldiers": maximum,
            "unraised_available": unraised_available,
            "unraised_unavailable_reason": unraised_reason,
            "unraised_soldiers": unraised, "native_raise_legal": raise_legal,
        })
    if owners != expected_owners:
        raise ValueError("prewar force/coalition owner_forces omitted a primary or observed ally owner")
    return result


def normalize_prewar_force_coalition_v1(
    value: object, *, snapshot: Mapping[str, object],
    expected_declaration: Mapping[str, object],
    expected_request_binding: Mapping[str, object],
    expected_capture_epoch: int | None = None,
) -> dict[str, object]:
    """Validate partial rows against the actual request and current paused map.

    ``expected_request_binding`` contains exactly ``ticket``,
    ``query_sequence`` and ``capture_epoch`` from the current envelope's
    independent top-level execution receipt.  The outer caller must first
    match its fresh request ID; a domain payload or historical cache cannot
    supply this expectation.  No predicted ticket or second query is needed.
    This function neither reconstructs the receipt from the domain nor
    checks connection/episode leases.  Those leases must be checked outside.
    ``expected_declaration`` must also carry the externally bound
    ``effective_target_character_id`` alongside its current declaration tuple.
    """
    root = _object(value, _FIELDS, "observation")
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ValueError("prewar force/coalition schema_version is malformed")
    if root["status"] != STATUS or root["read_only"] is not True:
        raise ValueError("prewar force/coalition must remain a read-only partial observation")
    if not isinstance(snapshot, Mapping) or snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise ValueError("prewar force/coalition requires the current paused map")
    build = require_exact_native_build(root["game_version"], root["executable_sha256"])
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    if not isinstance(hello, Mapping) or build != CK3_12004 or build != require_exact_native_build(
        hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"),
    ):
        raise ValueError("prewar force/coalition does not match the frozen exact .4 snapshot build")
    binding = _object(expected_request_binding, _REQUEST_FIELDS, "expected_request_binding")
    for key in _REQUEST_FIELDS:
        actual = _integer(root[key], key, 1, _UINT64_MAX)
        expected = _integer(binding[key], f"expected_request_binding.{key}", 1, _UINT64_MAX)
        if actual != expected:
            raise ValueError(f"prewar force/coalition request {key} mismatch")
    if expected_capture_epoch is not None and root["capture_epoch"] != _integer(
        expected_capture_epoch, "expected_capture_epoch", 1, _UINT64_MAX,
    ):
        raise ValueError("prewar force/coalition expected capture epoch mismatch")
    if "capture_epoch" in snapshot and root["capture_epoch"] != _integer(
        snapshot["capture_epoch"], "snapshot.capture_epoch", 1, _UINT64_MAX,
    ):
        raise ValueError("prewar force/coalition snapshot capture epoch mismatch")
    for wire_key, snapshot_key in (("native_revision", "native_revision"), ("public_revision", "revision")):
        actual = _integer(root[wire_key], wire_key, 1, _UINT64_MAX)
        expected = _integer(snapshot.get(snapshot_key), f"snapshot.{snapshot_key}", 1, _UINT64_MAX)
        if actual != expected:
            raise ValueError(f"prewar force/coalition current {wire_key} mismatch")
    date = _integer(root["date_raw"], "date_raw", -(1 << 31), _INT32_MAX)
    if date != _integer(snapshot.get("date_raw"), "snapshot.date_raw", -(1 << 31), _INT32_MAX):
        raise ValueError("prewar force/coalition current date mismatch")
    played = snapshot.get("played_character")
    if not isinstance(played, Mapping) or played.get("alive") is not True:
        raise ValueError("prewar force/coalition requires the current living played character")
    actor = _character(root["actor_character_id"], "actor_character_id")
    if actor != _character(played.get("character_id"), "snapshot.played_character.character_id"):
        raise ValueError("prewar force/coalition current actor mismatch")
    declaration_id, selected = _declaration(expected_declaration, "expected_declaration")
    if root["declaration_id"] != declaration_id or _selected(root["selected_declaration"], "selected_declaration") != selected:
        raise ValueError("prewar force/coalition selected declaration mismatch")
    current = snapshot.get("declarable_wars")
    if not isinstance(current, list):
        raise ValueError("prewar force/coalition snapshot lost current declarations")
    matches = [row for row in current if isinstance(row, Mapping) and row.get("declaration_id") == declaration_id]
    if len(matches) != 1 or _declaration(matches[0], "snapshot.declarable_wars")[1] != selected:
        raise ValueError("prewar force/coalition declaration is absent, ambiguous or stale")
    effective = _character(root["effective_target_character_id"], "effective_target_character_id")
    if effective == actor:
        raise ValueError("prewar force/coalition primary sides collapse to the actor")
    if effective != _character(
        expected_declaration.get("effective_target_character_id"),
        "expected_declaration.effective_target_character_id",
    ):
        raise ValueError("prewar force/coalition effective defender mismatch")
    allies = _allies(root["current_allies"], (actor, effective))
    owners = {actor, effective}
    for row in allies:
        owners.update(row["ally_character_ids"] or ())
    forces = _forces(root["owner_forces"], owners)
    actor_force = next(row for row in forces if row["owner_character_id"] == actor)
    expected_lower = (
        actor_force["unraised_soldiers"]
        if actor_force["unraised_available"] is True and actor_force["native_raise_legal"] is True
        else None
    )
    lower = _count(root["actor_ready_unraised_lower_soldiers"], "actor_ready_unraised_lower_soldiers", nullable=True)
    if lower != expected_lower:
        raise ValueError("prewar force/coalition actor lower lacks a ready count and native raise legality")
    if root["enemy_upper_soldiers"] is not None or any(root[key] is not False for key in (
        "enemy_force_coverage_complete", "complete_initial_participants_ready", "automatic_declaration_enabled",
    )):
        raise ValueError("prewar force/coalition partial observation cannot claim an enemy upper or authorize declaration")
    return {
        **dict(root), "executable_sha256": build.executable_sha256,
        "selected_declaration": selected, "current_allies": allies,
        "owner_forces": forces,
    }


def is_prewar_force_coalition_current_v1(
    value: object, *, snapshot: Mapping[str, object],
    expected_declaration: Mapping[str, object],
    expected_request_binding: Mapping[str, object],
    expected_capture_epoch: int | None = None,
) -> bool:
    """Check the DTO's frame/request binding, without granting gameplay use."""
    try:
        normalize_prewar_force_coalition_v1(
            value, snapshot=snapshot, expected_declaration=expected_declaration,
            expected_request_binding=expected_request_binding,
            expected_capture_epoch=expected_capture_epoch,
        )
    except ValueError:
        return False
    return True
