"""Minimum relationship-search projection over campaign-root v1."""

from __future__ import annotations

import copy
from typing import Final

from .campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
)


ENTITY_DIRECTORY_V1_SCHEMA: Final = "xar.ck3.entity-directory/v1"
SEARCH_ENTITIES_V1_TOOL: Final = "ck3_search_entities_v1"
_RELATION_FILTERS: Final = {
    "any",
    "self",
    "direct_landed_vassal",
    "adjacent_external_province_holder",
}
def _component(
    status: str,
    value: object = None,
    reason: str | None = None,
) -> dict[str, object]:
    if status not in {"available", "unavailable", "not_applicable"}:
        raise ValueError("entity component status is invalid")
    if status == "available":
        if value is None or reason is not None:
            raise ValueError("available entity component must carry a value")
    elif value is not None or not isinstance(reason, str) or not reason:
        raise ValueError("non-available entity component must carry a reason")
    return {
        "status": status,
        "value": copy.deepcopy(value),
        "unavailable_reason": reason,
    }


def _positive_int(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _source_root(result: object) -> tuple[dict[str, object], int]:
    if not isinstance(result, dict):
        raise ValueError("campaign-root result must be an object")
    context = result.get("campaign_root_context")
    if not isinstance(context, dict):
        raise ValueError("campaign-root result lacks its context")
    query_sequence = result.get("query_sequence")
    if (
        isinstance(query_sequence, bool)
        or not isinstance(query_sequence, int)
        or not 1 <= query_sequence <= 2**64 - 1
    ):
        raise ValueError("campaign-root result lacks a positive query sequence")
    if result.get("status") != context.get("status"):
        raise ValueError("campaign-root envelope and context status disagree")
    return context, query_sequence


def _self_entity(context: dict[str, object]) -> dict[str, object]:
    character_id = _positive_int(
        context.get("player_character_id"), "player_character_id"
    )
    primary_title = context.get("primary_title")
    capital = context.get("capital_province_id")
    immediate_liege = context.get("immediate_liege_character_id")
    top_liege = _positive_int(
        context.get("top_liege_character_id"), "top_liege_character_id"
    )
    return {
        "entity_kind": "character",
        "character_id": character_id,
        "relationship_roles": ["self"],
        "primary_title": (
            _component("available", primary_title)
            if primary_title is not None
            else _component(
                "not_applicable", reason="landless_or_no_primary_title"
            )
        ),
        "capital_province_id": (
            _component("available", _positive_int(capital, "capital_province_id"))
            if capital is not None
            else _component("not_applicable", reason="no_current_capital")
        ),
        "immediate_liege_character_id": (
            _component(
                "available",
                _positive_int(immediate_liege, "immediate_liege_character_id"),
            )
            if immediate_liege is not None
            else _component("not_applicable", reason="independent")
        ),
        "top_liege_character_id": _component("available", top_liege),
    }


def _related_entity(
    related: object,
) -> dict[str, object]:
    if not isinstance(related, dict):
        raise ValueError("related character context must be an object")
    character_id = _positive_int(
        related.get("character_id"), "related character_id"
    )
    relationship_role = related.get("relationship_role")
    if relationship_role not in {
        "direct_landed_vassal",
        "adjacent_external_province_holder",
    }:
        raise ValueError("related relationship_role is invalid")
    primary_title = related.get("primary_title")
    if not isinstance(primary_title, dict):
        raise ValueError("related primary_title is missing")
    capital = related.get("capital_province_id")
    immediate_liege = related.get("immediate_liege_character_id")
    top_liege = _positive_int(
        related.get("top_liege_character_id"),
        "related top_liege_character_id",
    )
    return {
        "entity_kind": "character",
        "character_id": character_id,
        "relationship_roles": [relationship_role],
        "primary_title": _component("available", primary_title),
        "capital_province_id": (
            _component("available", _positive_int(capital, "related capital"))
            if capital is not None
            else _component("not_applicable", reason="no_current_capital")
        ),
        "immediate_liege_character_id": (
            _component(
                "available",
                _positive_int(immediate_liege, "related immediate_liege"),
            )
            if immediate_liege is not None
            else _component("not_applicable", reason="independent")
        ),
        "top_liege_character_id": _component("available", top_liege),
    }


def build_entity_directory_v1(
    campaign_root_result: object,
    *,
    relation_filter: str = "any",
    after_character_id: int | None = None,
    limit: int = 50,
) -> dict[str, object]:
    """Build a deterministic identity search without inventing entity state."""

    if relation_filter not in _RELATION_FILTERS:
        raise ValueError("relation_filter is invalid")
    if after_character_id is not None:
        after_character_id = _positive_int(
            after_character_id, "after_character_id"
        )
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer in [1, 100]")

    context, query_sequence = _source_root(campaign_root_result)
    snapshot_revision = context.get("snapshot_revision")
    date_raw = context.get("date_raw")
    if (
        isinstance(snapshot_revision, bool)
        or not isinstance(snapshot_revision, int)
        or snapshot_revision <= 0
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not -(2**31) <= date_raw <= 2**31 - 1
    ):
        raise ValueError("campaign-root binding is invalid")
    provenance = context.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("campaign-root provenance is missing")
    source = {
        "capability": QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
        "query_sequence": query_sequence,
        "game_version": provenance.get("game_version"),
        "executable_sha256": provenance.get("executable_sha256"),
    }

    if context.get("status") == "unavailable":
        reason = context.get("unavailable_reason")
        if not isinstance(reason, str) or not reason:
            raise ValueError("unavailable campaign root lacks a reason")
        return {
            "schema": ENTITY_DIRECTORY_V1_SCHEMA,
            "status": "unavailable",
            "snapshot_revision": snapshot_revision,
            "date_raw": date_raw,
            "relation_filter": relation_filter,
            "after_character_id": after_character_id,
            "limit": limit,
            "entities": [],
            "next_after_character_id": None,
            "total_matching_count": 0,
            "readiness": {
                "identity_ready": False,
                "relationship_ready": False,
                "primary_title_components_complete": False,
                "realm_identity_components_complete": False,
                "ready": False,
            },
            "unavailable_reason": reason,
            "source": source,
        }
    if context.get("status") != "available":
        raise ValueError("campaign-root status is invalid")

    entities = [_self_entity(context)]
    related_contexts = context.get("related_character_contexts")
    if not isinstance(related_contexts, list):
        raise ValueError("campaign-root related_character_contexts is missing")
    entities.extend(_related_entity(related) for related in related_contexts)
    entities.sort(key=lambda row: int(row["character_id"]))
    if len({row["character_id"] for row in entities}) != len(entities):
        raise ValueError("campaign-root relationship identities overlap")

    matching = [
        row
        for row in entities
        if relation_filter == "any"
        or relation_filter in row["relationship_roles"]
    ]
    total_matching_count = len(matching)
    remaining = [
        row
        for row in matching
        if after_character_id is None
        or int(row["character_id"]) > after_character_id
    ]
    page = remaining[:limit]
    next_after = (
        int(page[-1]["character_id"])
        if page and len(remaining) > len(page)
        else None
    )
    title_complete = all(
        row["primary_title"]["status"] != "unavailable" for row in entities
    )
    realm_complete = all(
        row["top_liege_character_id"]["status"] != "unavailable"
        for row in entities
    )
    return {
        "schema": ENTITY_DIRECTORY_V1_SCHEMA,
        "status": "available",
        "snapshot_revision": snapshot_revision,
        "date_raw": date_raw,
        "relation_filter": relation_filter,
        "after_character_id": after_character_id,
        "limit": limit,
        "entities": copy.deepcopy(page),
        "next_after_character_id": next_after,
        "total_matching_count": total_matching_count,
        "readiness": {
            "identity_ready": True,
            "relationship_ready": True,
            "primary_title_components_complete": title_complete,
            "realm_identity_components_complete": realm_complete,
            "ready": True,
        },
        "unavailable_reason": None,
        "source": source,
    }
