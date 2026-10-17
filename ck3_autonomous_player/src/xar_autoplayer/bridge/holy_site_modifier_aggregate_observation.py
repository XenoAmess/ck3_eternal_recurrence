"""Validate actual Type fixed-PC keys and recipient aggregate observations only.

No property names, per-site attribution, scaled HolySite effects or benefits
are inferred from these Character totals. Engine functions are never invoked.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

SCHEMA = "ck3_12004_holy_site_modifier_aggregate_v1"
LIMITS = {"definition_entries_per_block": 32, "unique_keys": 64, "recipients": 2}
ROOT_KEYS = set("""schema available complete source_arrays_stable capture_epoch date_raw played_character_id
    holy_site_id county_holder_character_id definition_blocks recipients read_only native_functions_called
    evaluation_atomic names_bound site_attribution_observed scaled_effects_observed limits unavailable_reason""".split())
BLOCK_KEYS = set("kind available count_raw entries unavailable_reason".split())
ENTRY_KEYS = set("key_raw_u16 definition_raw_q64 property_name".split())
RECIPIENT_KEYS = set("""character_id source_player source_county_holder rite_id faith_id available
    owned_aggregate_observed values unavailable_reason""".split())
VALUE_KEYS = set("key_raw_u16 available aggregate_raw_q64 unavailable_reason".split())
OWNED_UNAVAILABLE = "actual_owned_character_aggregate_unavailable"


def _require(value: bool, message: str) -> None:
    if not value:
        raise ValueError("native HolySite modifier aggregate " + message)


def _shape(value: object, keys: set[str], field: str) -> dict:
    _require(isinstance(value, dict) and set(value) == keys, "has malformed " + field + " shape")
    return dict(value)


def _integer(value: object, field: str, *, low: int, high: int, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    _require(type(value) is int and low <= value <= high, "has malformed " + field)
    return value


def _ref(value: object, field: str, *, nullable: bool = False) -> int | None:
    return _integer(value, field, low=0, high=0xFFFFFFFE, nullable=nullable)


def _boolean(value: object, field: str) -> bool:
    _require(type(value) is bool, "has malformed " + field)
    return value


def _reason(value: object, *, required: bool, field: str) -> None:
    _require((value is None and not required) or isinstance(value, str) and 0 < len(value) <= 65536,
             "has malformed " + field + " reason")


def _array(value: object, field: str, *, limit: int) -> list:
    _require(isinstance(value, list) and len(value) <= limit, "has malformed " + field)
    return value


def normalize_holy_site_modifier_aggregate_v1(
    value: object, *, parent: Mapping[str, object], holy_site_id: int,
) -> dict[str, object] | None:
    """Accept only the optional site Type fixed-PC/actual owned-cache contract."""
    if value is None:
        _require(parent.get("available") is False, "may be null only with an unavailable parent")
        return None
    result = _shape(value, ROOT_KEYS, "root")
    _require(result["schema"] == SCHEMA, "has an unknown schema")
    for field in ("available", "complete", "source_arrays_stable"):
        _boolean(result[field], field)
    _require(result["read_only"] is True, "lost read-only identity")
    for field in ("native_functions_called", "evaluation_atomic", "names_bound", "site_attribution_observed", "scaled_effects_observed"):
        _require(result[field] is False, "cannot assert " + field)
    _require(isinstance(result["limits"], dict) and result["limits"] == LIMITS and
             all(type(item) is int for item in result["limits"].values()), "changed its fixed limits")
    _ref(holy_site_id, "requested holy_site_id")
    _ref(result["holy_site_id"], "holy_site_id")
    actor = _ref(result["played_character_id"], "played_character_id")
    holder = _ref(result["county_holder_character_id"], "county_holder_character_id", nullable=True)
    _integer(result["capture_epoch"], "capture_epoch", low=1, high=2**64 - 1)
    _integer(result["date_raw"], "date_raw", low=-(2**31), high=2**31 - 1)
    _require(result["holy_site_id"] == holy_site_id and all(result[field] == parent.get(field)
             for field in ("capture_epoch", "date_raw", "played_character_id")), "crossed its parent site/player/capture/date")
    _require(not result["available"] or parent.get("available") is True, "cannot be available under an unavailable parent")
    _reason(result["unavailable_reason"], required=not result["available"], field="root")
    _require(not result["complete"] or result["unavailable_reason"] is None, "complete observation retains a partial/failure reason")

    blocks = _array(result["definition_blocks"], "definition_blocks", limit=2)
    _require(len(blocks) == 2, "requires both actual fixed definition blocks")
    key_union = []
    for raw, kind in zip(blocks, ("faith_fixed", "local_fixed"), strict=True):
        block = _shape(raw, BLOCK_KEYS, "definition block")
        _require(block["kind"] == kind, "changed fixed-block provenance/order")
        available = _boolean(block["available"], "definition block.available")
        count = _integer(block["count_raw"], "count_raw", low=-(2**31), high=2**31 - 1, nullable=True)
        entries = _array(block["entries"], "definition entries", limit=LIMITS["definition_entries_per_block"])
        _reason(block["unavailable_reason"], required=not available, field="definition block")
        if available:
            _require(count is not None and 0 <= count <= LIMITS["definition_entries_per_block"] and
                     count == len(entries) and block["unavailable_reason"] is None,
                     "available fixed-PC count/rows disagree")
        else:
            _require(not entries, "unavailable definition block retained observed entries")
        for raw_entry in entries:
            entry = _shape(raw_entry, ENTRY_KEYS, "definition entry")
            key = _integer(entry["key_raw_u16"], "definition key_raw_u16", low=0, high=0xFFFF)
            _integer(entry["definition_raw_q64"], "definition_raw_q64", low=-(2**63), high=2**63 - 1)
            _require(entry["property_name"] is None, "invented a property name without a loaded name binding")
            if key != 0xFFFF and key not in key_union:
                key_union.append(key)
    _require(len(key_union) <= LIMITS["unique_keys"], "exceeded the fixed-PC key union limit")
    arrays_ready = all(block["available"] is True for block in blocks)
    if not result["source_arrays_stable"] or not arrays_ready:
        _require(result["available"] is False and result["complete"] is False and
                 result["source_arrays_stable"] is False and all(block["available"] is False and not block["entries"] for block in blocks),
                 "unavailable/drifting fixed PCs must invalidate both blocks before aggregate reading")

    recipients = _array(result["recipients"], "recipients", limit=LIMITS["recipients"])
    expected_ids = list(dict.fromkeys(item for item in (actor, holder) if item is not None))
    actual_ids = [row.get("character_id") if isinstance(row, dict) else None for row in recipients]
    _require(actual_ids == expected_ids or result["available"] is False and not recipients,
             "recipient identities lost player-then-derived-holder full-reference order/deduplication")
    all_values_available = True
    for raw in recipients:
        recipient = _shape(raw, RECIPIENT_KEYS, "recipient")
        character_id = _ref(recipient["character_id"], "recipient character_id")
        _require(_boolean(recipient["source_player"], "source_player") is (character_id == actor) and
                 _boolean(recipient["source_county_holder"], "source_county_holder") is (holder is not None and character_id == holder),
                 "changed actual recipient source flags")
        for field in ("rite_id", "faith_id"):
            _ref(recipient[field], "recipient " + field, nullable=True)
        available = _boolean(recipient["available"], "recipient.available")
        owned = _boolean(recipient["owned_aggregate_observed"], "owned_aggregate_observed")
        _reason(recipient["unavailable_reason"], required=not available, field="recipient")
        if recipient["unavailable_reason"] == OWNED_UNAVAILABLE:
            _require(owned is False and available is False, "fallback cannot claim an actually owned aggregate")
        if available:
            _require(owned and recipient["rite_id"] is not None and recipient["faith_id"] is not None and
                     recipient["unavailable_reason"] is None and result["available"] and result["source_arrays_stable"],
                     "available recipient lacks actual owned/source observations")
        values = _array(recipient["values"], "recipient values", limit=LIMITS["unique_keys"])
        _require([item.get("key_raw_u16") if isinstance(item, dict) else None for item in values] == key_union,
                 "recipient value grid differs from first-seen consumed fixed-PC keys")
        if not result["source_arrays_stable"]:
            _require(not values and not available and not owned, "source drift must clear all recipient values and owned claims")
        for raw_value in values:
            entry = _shape(raw_value, VALUE_KEYS, "aggregate value")
            _integer(entry["key_raw_u16"], "aggregate key_raw_u16", low=0, high=0xFFFE)
            value_available = _boolean(entry["available"], "aggregate value.available")
            _reason(entry["unavailable_reason"], required=not value_available, field="aggregate value")
            _require(value_available is available, "partial recipient key failure must invalidate every value")
            if value_available:
                _integer(entry["aggregate_raw_q64"], "aggregate_raw_q64", low=-(2**63), high=2**63 - 1)
                _require(owned and entry["unavailable_reason"] is None, "aggregate value lacks owned-cache provenance")
            else:
                _require(entry["aggregate_raw_q64"] is None, "unavailable aggregate is not an observed zero")
                all_values_available = False
    if result["complete"]:
        _require(result["available"] and result["source_arrays_stable"] and arrays_ready and holder is not None and
                 len(recipients) == len(expected_ids) and all(row["available"] and row["owned_aggregate_observed"] for row in recipients)
                 and all_values_available, "complete observation lacks fixed PCs, known county holder or actual owned recipient totals")
    return deepcopy(result)
