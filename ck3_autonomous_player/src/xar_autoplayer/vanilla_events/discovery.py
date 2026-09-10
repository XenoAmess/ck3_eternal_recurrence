"""Offline discovery over the exact-build vanilla-event knowledge catalog.

The single-event query remains the authority for full records.  This module
provides a small, deterministic index for finding those records without CK3,
machine-local paths, or a dependency on the optional portable-evidence bundle.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
import hashlib
import json
from typing import Final

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256, JsonValue


VANILLA_EVENT_KNOWLEDGE_INDEX_SCHEMA: Final = (
    "xar.ck3.vanilla-event-knowledge-index"
)
VANILLA_EVENT_KNOWLEDGE_INDEX_SCHEMA_VERSION: Final = 1
_EVIDENCE_CLASSES: Final = frozenset({"any", "source-reviewed", "migration-only"})


def _default_catalogs() -> tuple[
    Mapping[str, Mapping[str, object]],
    Mapping[str, Mapping[str, object]],
    Mapping[str, Mapping[str, object]],
]:
    # Delayed package import avoids a cycle while ``vanilla_events.__init__``
    # composes the canonical default registry.
    from . import (  # pylint: disable=import-outside-toplevel
        DEFAULT_VANILLA_EVENT_ANALYSIS,
        DEFAULT_VANILLA_EVENT_OBSERVATIONS,
        DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
    )

    return (
        DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
        DEFAULT_VANILLA_EVENT_ANALYSIS,
        DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    )


def _namespace(event_definition_key: str) -> str:
    return event_definition_key.rsplit(".", 1)[0]


def _source_file_count(analysis: Mapping[str, object]) -> int:
    source_sha256 = analysis.get("source_sha256")
    if not isinstance(source_sha256, Mapping):
        return 0
    return sum(
        1
        for path, digest in source_sha256.items()
        if isinstance(path, str)
        and bool(path)
        and isinstance(digest, str)
        and bool(digest)
    )


def _observation_count(observations: Mapping[str, object] | None) -> int:
    if not observations:
        return 0
    exemplars = observations.get("exemplars")
    if isinstance(exemplars, (list, tuple)):
        return len(exemplars)
    return 1


def _portable_keys(
    portable_event_keys: Mapping[str, object] | Collection[str] | None,
) -> frozenset[str]:
    if portable_event_keys is None:
        return frozenset()
    values = (
        portable_event_keys.keys()
        if isinstance(portable_event_keys, Mapping)
        else portable_event_keys
    )
    if isinstance(values, (str, bytes)):
        raise ValueError("portable_event_keys must be a collection of event keys")
    keys = frozenset(values)
    if any(not isinstance(key, str) or not key for key in keys):
        raise ValueError("portable_event_keys contains an invalid event key")
    return keys


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _record_digest(value: Mapping[str, object] | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(_canonical(value)).hexdigest().upper()


def _summary(
    event_key: str,
    *,
    analysis: Mapping[str, object],
    observations: Mapping[str, object] | None,
    portable: bool,
) -> dict[str, JsonValue]:
    source_count = _source_file_count(analysis)
    raw_summary = analysis.get("review_summary")
    review_summary = raw_summary if isinstance(raw_summary, str) else ""
    return {
        "event_definition_key": event_key,
        "namespace": _namespace(event_key),
        "evidence_class": (
            "source-reviewed" if source_count else "migration-only"
        ),
        "review_summary": review_summary,
        "source_file_count": source_count,
        "observation_count": _observation_count(observations),
        "portable_evidence_count": 1 if portable else 0,
    }


def _catalog_summary(rows: list[dict[str, JsonValue]]) -> dict[str, JsonValue]:
    return {
        "total_events": len(rows),
        "source_reviewed_events": sum(
            row["evidence_class"] == "source-reviewed" for row in rows
        ),
        "migration_only_events": sum(
            row["evidence_class"] == "migration-only" for row in rows
        ),
        "events_with_observations": sum(
            isinstance(row["observation_count"], int)
            and row["observation_count"] > 0
            for row in rows
        ),
        "portable_events": sum(
            row["portable_evidence_count"] == 1 for row in rows
        ),
    }


def _response(
    *,
    status: str,
    build: object,
    query: str | None,
    namespace: str | None,
    evidence_class: object,
    has_observations: bool | None,
    after_key: str | None,
    limit: object,
    dataset_sha256: str | None,
    dataset_summary: Mapping[str, JsonValue],
    match_summary: Mapping[str, JsonValue],
    total_matches: int,
    items: list[dict[str, JsonValue]],
    next_after_key: str | None,
    unavailable_reason: str | None,
    invalid_parameter: str | None,
) -> dict[str, JsonValue]:
    return {
        "schema": VANILLA_EVENT_KNOWLEDGE_INDEX_SCHEMA,
        "schema_version": VANILLA_EVENT_KNOWLEDGE_INDEX_SCHEMA_VERSION,
        "status": status,
        "ck3_build": build if isinstance(build, str) else None,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256 if build == EXACT_CK3_BUILD else None,
        "query": query,
        "namespace": namespace,
        "evidence_class": (
            evidence_class
            if isinstance(evidence_class, str)
            and evidence_class in _EVIDENCE_CLASSES
            else None
        ),
        "has_observations": has_observations,
        "after_key": after_key,
        "limit": (
            limit
            if isinstance(limit, int)
            and not isinstance(limit, bool)
            and 1 <= limit <= 100
            else None
        ),
        "dataset_sha256": dataset_sha256,
        "dataset_summary": dict(dataset_summary),
        "match_summary": dict(match_summary),
        "total_matches": total_matches,
        "items": items,
        "next_after_key": next_after_key,
        "unavailable_reason": unavailable_reason,
        "invalid_parameter": invalid_parameter,
    }


def _empty_summary() -> dict[str, JsonValue]:
    return {
        "total_events": 0,
        "source_reviewed_events": 0,
        "migration_only_events": 0,
        "events_with_observations": 0,
        "portable_events": 0,
    }


def ck3_list_vanilla_event_knowledge_v1(
    build: object = EXACT_CK3_BUILD,
    query: object = None,
    namespace: object = None,
    evidence_class: object = "any",
    has_observations: object = None,
    after_key: object = None,
    limit: object = 50,
    *,
    contracts: Mapping[str, Mapping[str, object]] | None = None,
    analysis: Mapping[str, Mapping[str, object]] | None = None,
    observations: Mapping[str, Mapping[str, object]] | None = None,
    portable_event_keys: Mapping[str, object] | Collection[str] | None = None,
) -> dict[str, JsonValue]:
    """List or search exact-build knowledge with stable keyset pagination.

    ``portable_event_keys`` is deliberately optional.  Its absence means no
    evidence is claimed to be packaged; a later bundler can inject either a
    key collection or a manifest mapping without coupling this index to it.
    """
    normalized_query = query.strip() if isinstance(query, str) else None
    normalized_namespace = namespace.strip() if isinstance(namespace, str) else None
    normalized_after_key = after_key.strip() if isinstance(after_key, str) else None

    invalid_parameter: str | None = None
    unavailable_reason: str | None = None
    if not isinstance(build, str) or build != EXACT_CK3_BUILD:
        unavailable_reason = "unsupported_ck3_build"
        invalid_parameter = "build"
    elif query is not None and not isinstance(query, str):
        unavailable_reason = "invalid_filter"
        invalid_parameter = "query"
    elif namespace is not None and (
        not isinstance(namespace, str) or not normalized_namespace
    ):
        unavailable_reason = "invalid_filter"
        invalid_parameter = "namespace"
    elif not isinstance(evidence_class, str) or evidence_class not in _EVIDENCE_CLASSES:
        unavailable_reason = "invalid_filter"
        invalid_parameter = "evidence_class"
    elif has_observations is not None and not isinstance(has_observations, bool):
        unavailable_reason = "invalid_filter"
        invalid_parameter = "has_observations"
    elif isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        unavailable_reason = "invalid_limit"
        invalid_parameter = "limit"
    elif after_key is not None and (
        not isinstance(after_key, str) or not normalized_after_key
    ):
        unavailable_reason = "invalid_cursor"
        invalid_parameter = "after_key"

    if unavailable_reason is not None:
        empty = _empty_summary()
        return _response(
            status="unavailable",
            build=build,
            query=normalized_query,
            namespace=normalized_namespace,
            evidence_class=evidence_class,
            has_observations=(
                has_observations if isinstance(has_observations, bool) else None
            ),
            after_key=normalized_after_key,
            limit=limit,
            dataset_sha256=None,
            dataset_summary=empty,
            match_summary=empty,
            total_matches=0,
            items=[],
            next_after_key=None,
            unavailable_reason=unavailable_reason,
            invalid_parameter=invalid_parameter,
        )

    if contracts is None or analysis is None or observations is None:
        default_contracts, default_analysis, default_observations = _default_catalogs()
        contracts = default_contracts if contracts is None else contracts
        analysis = default_analysis if analysis is None else analysis
        observations = default_observations if observations is None else observations

    assert isinstance(evidence_class, str)
    assert isinstance(limit, int)
    portable_keys = _portable_keys(portable_event_keys)
    all_keys = sorted(contracts)
    if any(not isinstance(key, str) or not key for key in all_keys):
        raise ValueError("contracts contains an invalid event key")
    if normalized_after_key is not None and normalized_after_key not in contracts:
        empty = _empty_summary()
        return _response(
            status="unavailable",
            build=build,
            query=normalized_query,
            namespace=normalized_namespace,
            evidence_class=evidence_class,
            has_observations=has_observations,
            after_key=normalized_after_key,
            limit=limit,
            dataset_sha256=None,
            dataset_summary=empty,
            match_summary=empty,
            total_matches=0,
            items=[],
            next_after_key=None,
            unavailable_reason="invalid_cursor",
            invalid_parameter="after_key",
        )

    rows: list[dict[str, JsonValue]] = []
    digest_rows: list[dict[str, object]] = []
    searchable_by_key: dict[str, str] = {}
    for event_key in all_keys:
        event_analysis = analysis.get(event_key, {})
        event_observations = observations.get(event_key)
        if not isinstance(event_analysis, Mapping):
            raise ValueError(f"analysis[{event_key!r}] must be a mapping")
        if event_observations is not None and not isinstance(
            event_observations, Mapping
        ):
            raise ValueError(f"observations[{event_key!r}] must be a mapping")
        row = _summary(
            event_key,
            analysis=event_analysis,
            observations=event_observations,
            portable=event_key in portable_keys,
        )
        rows.append(row)
        source_sha256 = event_analysis.get("source_sha256")
        source_paths = (
            [str(path) for path in source_sha256]
            if isinstance(source_sha256, Mapping)
            else []
        )
        searchable_by_key[event_key] = "\n".join((
            event_key,
            str(row["namespace"]),
            str(row["review_summary"]),
            *source_paths,
        )).casefold()
        digest_rows.append({
            **row,
            "contract_sha256": _record_digest(contracts[event_key]),
            "analysis_sha256": _record_digest(event_analysis),
            "observations_sha256": _record_digest(event_observations),
        })

    dataset_sha256 = hashlib.sha256(_canonical(digest_rows)).hexdigest().upper()
    query_needle = normalized_query.casefold() if normalized_query else None

    matches: list[dict[str, JsonValue]] = []
    for row in rows:
        if normalized_namespace is not None and row["namespace"] != normalized_namespace:
            continue
        if evidence_class != "any" and row["evidence_class"] != evidence_class:
            continue
        row_has_observations = bool(row["observation_count"])
        if has_observations is not None and row_has_observations != has_observations:
            continue
        if query_needle is not None and query_needle not in searchable_by_key[
            str(row["event_definition_key"])
        ]:
            continue
        matches.append(row)

    page_candidates = (
        matches
        if normalized_after_key is None
        else [
            row
            for row in matches
            if str(row["event_definition_key"]) > normalized_after_key
        ]
    )
    items = page_candidates[:limit]
    has_more = len(page_candidates) > limit
    next_after_key = (
        str(items[-1]["event_definition_key"])
        if has_more and items
        else None
    )
    return _response(
        status="available",
        build=build,
        query=normalized_query,
        namespace=normalized_namespace,
        evidence_class=evidence_class,
        has_observations=has_observations,
        after_key=normalized_after_key,
        limit=limit,
        dataset_sha256=dataset_sha256,
        dataset_summary=_catalog_summary(rows),
        match_summary=_catalog_summary(matches),
        total_matches=len(matches),
        items=items,
        next_after_key=next_after_key,
        unavailable_reason=None,
        invalid_parameter=None,
    )


__all__ = [
    "VANILLA_EVENT_KNOWLEDGE_INDEX_SCHEMA",
    "VANILLA_EVENT_KNOWLEDGE_INDEX_SCHEMA_VERSION",
    "ck3_list_vanilla_event_knowledge_v1",
]
