"""Validate optional recognition observations; no benefit or per-Faith Active inference."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

SCHEMA = "ck3_12004_holy_site_relic_recognition_matrix_v1"
LIMITS = {"faiths": 64, "slots": 64, "candidates": 64, "artifacts": 64}
MAX_CALLS = 256
MATRIX_KEYS = set("""schema available complete source_arrays_stable evaluation_atomic benefits_observed
    world_cache_written read_only holy_site_id capture_epoch date_raw played_character_id faith_sources
    artifact_sources faiths artifacts cells faith_deduplication artifact_deduplication native_getter_calls
    max_native_getter_calls limits unavailable_reason""".split())
FAITH_SOURCE_KEYS = set("associated_available associated_faith_ids player_faith_id county_holder_faith_id".split())
ARTIFACT_SOURCE_KEYS = set("""slots_available slot_artifact_ids window_candidates_available
    window_candidate_artifact_ids requested_action_artifact_id""".split())
FAITH_KEYS = set("faith_id source_associated source_player source_county_holder object_resolved unavailable_reason".split())
ARTIFACT_KEYS = set("artifact_id slot_indices candidate_indices source_action_request object_resolved unavailable_reason".split())
CELL_KEYS = set("artifact_id faith_id available value unavailable_reason".split())


def _require(value: bool, message: str) -> None:
    if not value:
        raise ValueError("native relic recognition matrix " + message)


def _shape(value: object, keys: set[str], field: str) -> dict:
    _require(isinstance(value, dict) and set(value) == keys, "has malformed " + field + " shape")
    return dict(value)


def _integer(value: object, field: str, *, low: int = 0, high: int = 0xFFFFFFFE) -> int:
    _require(type(value) is int and low <= value <= high, "has malformed " + field)
    return value


def _ref(value: object, field: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    return _integer(value, field)


def _boolean(value: object, field: str) -> bool:
    _require(type(value) is bool, "has malformed " + field)
    return value


def _reason(value: object, *, required: bool, field: str) -> None:
    _require((value is None and not required) or isinstance(value, str) and 0 < len(value) <= 65536,
             "has malformed " + field + " reason")


def _array(value: object, field: str, *, limit: int) -> list:
    _require(isinstance(value, list) and len(value) <= limit, "has malformed " + field)
    return value


def _source_ids(source: Mapping[str, object], available: str, ids: str, *, nullable_items: bool = False) -> list | None:
    observed = _boolean(source[available], available)
    value = source[ids]
    if not observed:
        _require(value is None, "unavailable " + ids + " must remain null")
        return None
    rows = _array(value, ids, limit=4096)
    for item in rows:
        _ref(item, ids, nullable=nullable_items)
    return rows


def _resolved(row: Mapping[str, object], field: str) -> bool:
    resolved = _boolean(row["object_resolved"], field + ".object_resolved")
    _reason(row["unavailable_reason"], required=not resolved, field=field)
    _require(not resolved or row["unavailable_reason"] is None, "resolved " + field + " retains a failure reason")
    return resolved


def normalize_holy_site_relic_recognition_matrix_v1(
    value: object, *, parent: Mapping[str, object], holy_site_id: int,
    requested_action_artifact_id: int | None = None,
) -> dict[str, object] | None:
    """Validate present extension fields, preserving absence in the legacy callers.

    Source arrays retain original duplicates and ordering. Only deduplicated rows
    and their exact Cartesian product are bounded by the evaluation limits.
    Unavailability is never interpreted as an observed negative recognition.
    """
    if value is None:
        _require(parent.get("available") is False, "may be null only with an unavailable parent")
        return None
    result = _shape(value, MATRIX_KEYS, "root")
    _require(result["schema"] == SCHEMA, "has an unknown schema")
    for field in ("available", "complete", "source_arrays_stable"):
        _boolean(result[field], field)
    for field in ("evaluation_atomic", "benefits_observed", "world_cache_written"):
        _require(result[field] is False, "cannot assert " + field)
    _require(result["read_only"] is True, "lost read-only identity")
    _require(result["limits"] == LIMITS and isinstance(result["limits"], dict) and
             all(type(item) is int for item in result["limits"].values()), "changed its fixed limits")
    _integer(result["max_native_getter_calls"], "max_native_getter_calls", low=MAX_CALLS, high=MAX_CALLS)
    calls = _integer(result["native_getter_calls"], "native_getter_calls", high=MAX_CALLS)
    _ref(holy_site_id, "requested holy_site_id")
    _ref(result["holy_site_id"], "holy_site_id")
    _ref(requested_action_artifact_id, "requested action artifact", nullable=True)
    _ref(result["played_character_id"], "played_character_id")
    _integer(result["capture_epoch"], "capture_epoch", low=1, high=2**64 - 1)
    _integer(result["date_raw"], "date_raw", low=-(2**31), high=2**31 - 1)
    _require(result["holy_site_id"] == holy_site_id and all(result[field] == parent.get(field)
             for field in ("played_character_id", "capture_epoch", "date_raw")), "crossed its parent site/player/capture/date")
    _require(not result["available"] or parent.get("available") is True, "cannot be available under an unavailable parent")
    _reason(result["unavailable_reason"], required=not result["available"], field="root")
    _require(not result["complete"] or result["unavailable_reason"] is None, "complete observation retains a partial/failure reason")
    _require(result["faith_deduplication"] == "first_seen_full_id_associated_player_county_holder" and
             result["artifact_deduplication"] == "first_seen_full_id_slots_window_candidates_action_request",
             "changed its first-seen full-reference contract")
    faith_source = _shape(result["faith_sources"], FAITH_SOURCE_KEYS, "faith_sources")
    artifact_source = _shape(result["artifact_sources"], ARTIFACT_SOURCE_KEYS, "artifact_sources")
    associated = _source_ids(faith_source, "associated_available", "associated_faith_ids")
    slots = _source_ids(artifact_source, "slots_available", "slot_artifact_ids", nullable_items=True)
    candidates = _source_ids(artifact_source, "window_candidates_available", "window_candidate_artifact_ids")
    for field in ("player_faith_id", "county_holder_faith_id"):
        _ref(faith_source[field], field, nullable=True)
    _ref(artifact_source["requested_action_artifact_id"], "requested_action_artifact_id", nullable=True)
    _require(artifact_source["requested_action_artifact_id"] == requested_action_artifact_id,
             "invented or changed the existing action artifact request")
    faith_ids = list(dict.fromkeys(item for item in [*(associated or []), faith_source["player_faith_id"],
        faith_source["county_holder_faith_id"]] if item is not None))
    artifact_ids = list(dict.fromkeys(item for item in [*(slots or []), *(candidates or []),
        requested_action_artifact_id] if item is not None))
    overflow = (len(faith_ids) > LIMITS["faiths"] or len(slots or []) > LIMITS["slots"] or
        len(candidates or []) > LIMITS["candidates"] or len(artifact_ids) > LIMITS["artifacts"] or
        len(faith_ids) * len(artifact_ids) > MAX_CALLS)
    faiths = _array(result["faiths"], "faiths", limit=LIMITS["faiths"])
    artifacts = _array(result["artifacts"], "artifacts", limit=LIMITS["artifacts"])
    cells = _array(result["cells"], "cells", limit=MAX_CALLS)
    if overflow:
        _require(result["available"] is False and result["complete"] is False and
                 not faiths and not artifacts and not cells and calls == 0,
                 "overflow must fail before any added getter and retain only raw source arrays")
        return deepcopy(result)
    if not result["source_arrays_stable"]:
        _require(result["available"] is False and result["complete"] is False,
                 "changed source arrays cannot remain available or complete")
    expected_faith_ids = [row.get("faith_id") if isinstance(row, dict) else None for row in faiths]
    expected_artifact_ids = [row.get("artifact_id") if isinstance(row, dict) else None for row in artifacts]
    _require(expected_faith_ids == faith_ids or not result["available"] and not faiths,
             "faith rows lost exact first-seen identities/order")
    _require(expected_artifact_ids == artifact_ids or not result["available"] and not artifacts,
             "artifact rows lost exact first-seen identities/order")
    faith_resolution, artifact_resolution = {}, {}
    for raw in faiths:
        row = _shape(raw, FAITH_KEYS, "faith row")
        identity = _ref(row["faith_id"], "faith row identity")
        for field, expected in (("source_associated", identity in (associated or [])),
                ("source_player", identity == faith_source["player_faith_id"]),
                ("source_county_holder", identity == faith_source["county_holder_faith_id"])):
            _require(_boolean(row[field], field) is expected, "changed faith source provenance")
        faith_resolution[identity] = _resolved(row, "faith row")
    for raw in artifacts:
        row = _shape(raw, ARTIFACT_KEYS, "artifact row")
        identity = _ref(row["artifact_id"], "artifact row identity")
        for field, source in (("slot_indices", slots or []), ("candidate_indices", candidates or [])):
            indices = _array(row[field], field, limit=4096)
            for index in indices:
                _integer(index, field, high=4095)
            _require(indices == [index for index, item in enumerate(source) if item == identity],
                     "changed original raw source indices")
        _require(_boolean(row["source_action_request"], "source_action_request") is (identity == requested_action_artifact_id),
                 "changed artifact action provenance")
        artifact_resolution[identity] = _resolved(row, "artifact row")
    grid = [(artifact, faith) for artifact in artifact_ids for faith in faith_ids]
    actual_grid = [(row.get("artifact_id"), row.get("faith_id")) if isinstance(row, dict) else None for row in cells]
    _require(actual_grid == grid or not result["available"] and not cells,
             "cells lost exact artifact-major/faith-minor full-reference grid")
    observed_cells = 0
    for raw in cells:
        row = _shape(raw, CELL_KEYS, "cell")
        artifact, faith = _ref(row["artifact_id"], "cell artifact_id"), _ref(row["faith_id"], "cell faith_id")
        available = _boolean(row["available"], "cell.available")
        _reason(row["unavailable_reason"], required=not available, field="cell")
        if available:
            _require(result["available"] and result["source_arrays_stable"] and
                     artifact_resolution.get(artifact) is True and faith_resolution.get(faith) is True,
                     "observed recognition lacks stable resolved source objects")
            _boolean(row["value"], "cell.value")
            _require(row["unavailable_reason"] is None, "observed cell retains a failure reason")
            observed_cells += 1
        else:
            _require(row["value"] is None, "unavailable recognition must remain null, not false")
    _require(observed_cells <= calls <= len(grid), "added getter calls differ from the bounded recognition grid")
    if result["complete"]:
        _require(result["available"] and result["source_arrays_stable"] and associated is not None and
                 slots is not None and candidates is not None and faith_source["player_faith_id"] is not None and
                 faith_source["county_holder_faith_id"] is not None and
                 all(faith_resolution.get(identity) is True for identity in faith_ids) and
                 all(artifact_resolution.get(identity) is True for identity in artifact_ids) and
                 len(faiths) == len(faith_ids) and len(artifacts) == len(artifact_ids) and observed_cells == len(grid),
                 "complete observation lacks all known sources, resolved player/holder objects or observed cells")
    return deepcopy(result)
