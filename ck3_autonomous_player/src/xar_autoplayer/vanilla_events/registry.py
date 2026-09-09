"""Generic registry for exact-build vanilla-event timeline contracts.

The registry owns defensive structural copies of migrated contracts.  It
deliberately does not import any particular event group; production composition
can supply one mapping or an iterable of mappings when those groups are ready.
Tuple-valued legacy contracts remain tuples internally and during materializing;
only the query boundary projects them to JSON arrays.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import math
from typing import Final


EXACT_CK3_BUILD: Final = "1.19.0.6"
EXACT_CK3_EXE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
VANILLA_EVENT_KNOWLEDGE_SCHEMA: Final = "xar.ck3.vanilla-event-knowledge"
VANILLA_EVENT_KNOWLEDGE_SCHEMA_VERSION: Final = 1
PLAYER_SENTINEL: Final = "$player"

JsonValue = type(None) | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
ContractValue = (
    type(None)
    | bool
    | int
    | float
    | str
    | list["ContractValue"]
    | tuple["ContractValue", ...]
    | dict[str, "ContractValue"]
)
TimelineContract = dict[str, ContractValue]

_registry_by_event_key: dict[str, TimelineContract] = {}
_analysis_by_event_key: dict[str, dict[str, JsonValue]] = {}
_observations_by_event_key: dict[str, dict[str, JsonValue]] = {}


def _clone_contract(value: object, *, path: str) -> ContractValue:
    """Validate and clone one legacy contract value, preserving sequences."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must not contain NaN or infinity")
        return value
    if isinstance(value, list):
        return [
            _clone_contract(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, tuple):
        return tuple(
            _clone_contract(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        )
    if isinstance(value, Mapping):
        cloned: dict[str, ContractValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string object key")
            cloned[key] = _clone_contract(item, path=f"{path}.{key}")
        return cloned
    raise ValueError(
        f"{path} contains an unsupported contract value: {type(value).__name__}"
    )


def _clone_json(value: object, *, path: str) -> JsonValue:
    """Project a validated contract value to a detached JSON-safe shape."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must not contain NaN or infinity")
        return value
    if isinstance(value, (list, tuple)):
        return [
            _clone_json(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        cloned: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string object key")
            cloned[key] = _clone_json(item, path=f"{path}.{key}")
        return cloned
    raise ValueError(f"{path} contains a non-JSON value: {type(value).__name__}")


def _contract_copy(value: object, *, path: str) -> TimelineContract:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be a JSON object")
    cloned = _clone_contract(value, path=path)
    assert isinstance(cloned, dict)
    return cloned


def _metadata_copy(value: object, *, path: str) -> dict[str, JsonValue]:
    """Clone metadata to its JSON transport shape, including integer keys."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be a JSON object")

    def clone(item: object, *, item_path: str) -> JsonValue:
        if item is None or isinstance(item, (bool, int, str)):
            return item
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError(f"{item_path} must not contain NaN or infinity")
            return item
        if isinstance(item, (list, tuple)):
            return [
                clone(child, item_path=f"{item_path}[{index}]")
                for index, child in enumerate(item)
            ]
        if isinstance(item, Mapping):
            result: dict[str, JsonValue] = {}
            for raw_key, child in item.items():
                if isinstance(raw_key, str):
                    key = raw_key
                elif isinstance(raw_key, int) and not isinstance(raw_key, bool):
                    key = str(raw_key)
                else:
                    raise ValueError(
                        f"{item_path} contains an unsupported metadata key"
                    )
                if key in result:
                    raise ValueError(
                        f"{item_path} contains colliding JSON object keys"
                    )
                result[key] = clone(child, item_path=f"{item_path}.{key}")
            return result
        raise ValueError(
            f"{item_path} contains a non-JSON value: {type(item).__name__}"
        )

    copied = clone(value, item_path=path)
    assert isinstance(copied, dict)
    return copied


def _metadata_table_copy(
    value: Mapping[str, Mapping[str, object]] | None,
    *,
    name: str,
    registered_keys: set[str],
) -> dict[str, dict[str, JsonValue]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    result: dict[str, dict[str, JsonValue]] = {}
    for event_definition_key, metadata in value.items():
        if event_definition_key not in registered_keys:
            raise ValueError(
                f"{name} contains unregistered event key {event_definition_key!r}"
            )
        result[event_definition_key] = _metadata_copy(
            metadata,
            path=f"{name}[{event_definition_key!r}]",
        )
    return result


def _iter_contract_groups(
    groups: Mapping[str, Mapping[str, object]]
    | Iterable[Mapping[str, Mapping[str, object]]],
) -> Iterable[Mapping[str, Mapping[str, object]]]:
    if isinstance(groups, Mapping):
        yield groups
        return
    if isinstance(groups, (str, bytes)):
        raise ValueError("groups must be a contract group or iterable of groups")
    try:
        iterator = iter(groups)
    except TypeError as exc:
        raise ValueError(
            "groups must be a contract group or iterable of groups"
        ) from exc
    for index, group in enumerate(iterator):
        if not isinstance(group, Mapping):
            raise ValueError(f"groups[{index}] must be a mapping")
        yield group


def _canonical_contract(contract: TimelineContract) -> str:
    return json.dumps(
        _clone_json(contract, path="contract"),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def build_vanilla_event_registry(
    groups: Mapping[str, Mapping[str, object]]
    | Iterable[Mapping[str, Mapping[str, object]]],
    *,
    analysis: Mapping[str, Mapping[str, object]] | None = None,
    observations: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, TimelineContract]:
    """Replace the active registry with validated migrated contract groups.

    Repeating an event key with byte-equivalent canonical JSON is harmless and
    deduplicated.  Reusing a key for different content raises ``ValueError``;
    the prior active registry remains untouched.
    """
    candidate: dict[str, TimelineContract] = {}
    canonical_by_key: dict[str, str] = {}
    for group_index, group in enumerate(_iter_contract_groups(groups)):
        for event_definition_key, contract in group.items():
            if (
                not isinstance(event_definition_key, str)
                or not event_definition_key.strip()
            ):
                raise ValueError(
                    f"groups[{group_index}] contains an invalid event definition key"
                )
            cloned = _contract_copy(
                contract,
                path=f"groups[{group_index}][{event_definition_key!r}]",
            )
            canonical = _canonical_contract(cloned)
            previous = canonical_by_key.get(event_definition_key)
            if previous is not None:
                if previous != canonical:
                    raise ValueError(
                        "conflicting vanilla event contract for "
                        f"{event_definition_key!r}"
                    )
                continue
            candidate[event_definition_key] = cloned
            canonical_by_key[event_definition_key] = canonical

    registered_keys = set(candidate)
    candidate_analysis = _metadata_table_copy(
        analysis,
        name="analysis",
        registered_keys=registered_keys,
    )
    candidate_observations = _metadata_table_copy(
        observations,
        name="observations",
        registered_keys=registered_keys,
    )

    global _analysis_by_event_key, _observations_by_event_key
    global _registry_by_event_key
    _registry_by_event_key = candidate
    _analysis_by_event_key = candidate_analysis
    _observations_by_event_key = candidate_observations
    return {
        key: _contract_copy(contract, path=f"registry[{key!r}]")
        for key, contract in candidate.items()
    }


def _knowledge_response(
    *,
    status: str,
    event_definition_key: object,
    ck3_build: object,
    contract: TimelineContract | None,
    analysis: Mapping[str, object] | None,
    observations: Mapping[str, object] | None,
    unavailable_reason: str | None,
) -> dict[str, JsonValue]:
    return {
        "schema": VANILLA_EVENT_KNOWLEDGE_SCHEMA,
        "schema_version": VANILLA_EVENT_KNOWLEDGE_SCHEMA_VERSION,
        "status": status,
        "event_definition_key": (
            event_definition_key if isinstance(event_definition_key, str) else None
        ),
        "ck3_build": ck3_build if isinstance(ck3_build, str) else None,
        "ck3_exe_sha256": (
            EXACT_CK3_EXE_SHA256 if ck3_build == EXACT_CK3_BUILD else None
        ),
        "contract": (
            _clone_json(contract, path="knowledge.contract")
            if contract is not None
            else None
        ),
        "analysis": (
            _clone_json(analysis, path="knowledge.analysis")
            if analysis is not None
            else None
        ),
        "observations": (
            _clone_json(observations, path="knowledge.observations")
            if observations is not None
            else None
        ),
        "unavailable_reason": unavailable_reason,
    }


def query_vanilla_event_knowledge_v1(
    event_definition_key: str,
    ck3_build: str = EXACT_CK3_BUILD,
) -> dict[str, JsonValue]:
    """Return a JSON-safe, detached knowledge record or typed unavailable row."""
    if not isinstance(ck3_build, str) or ck3_build != EXACT_CK3_BUILD:
        return _knowledge_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            ck3_build=ck3_build,
            contract=None,
            analysis=None,
            observations=None,
            unavailable_reason="unsupported_ck3_build",
        )
    if not isinstance(event_definition_key, str) or not event_definition_key.strip():
        return _knowledge_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            ck3_build=ck3_build,
            contract=None,
            analysis=None,
            observations=None,
            unavailable_reason="invalid_event_definition_key",
        )
    contract = _registry_by_event_key.get(event_definition_key)
    if contract is None:
        return _knowledge_response(
            status="unavailable",
            event_definition_key=event_definition_key,
            ck3_build=ck3_build,
            contract=None,
            analysis=None,
            observations=None,
            unavailable_reason="event_definition_key_not_registered",
        )
    return _knowledge_response(
        status="available",
        event_definition_key=event_definition_key,
        ck3_build=ck3_build,
        contract=contract,
        analysis=_analysis_by_event_key.get(event_definition_key),
        observations=_observations_by_event_key.get(event_definition_key),
        unavailable_reason=None,
    )


def materialize_vanilla_timeline_contract(
    contract: Mapping[str, object],
    player: object,
) -> TimelineContract:
    """Return a detached contract with every value sentinel bound to ``player``."""
    player_value = _clone_contract(player, path="player")

    def replace(value: object, *, path: str) -> ContractValue:
        if value == PLAYER_SENTINEL:
            return _clone_contract(player_value, path="player")
        if isinstance(value, list):
            return [
                replace(item, path=f"{path}[{index}]")
                for index, item in enumerate(value)
            ]
        if isinstance(value, tuple):
            return tuple(
                replace(item, path=f"{path}[{index}]")
                for index, item in enumerate(value)
            )
        if isinstance(value, Mapping):
            replaced: dict[str, ContractValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError(f"{path} contains a non-string object key")
                replaced[key] = replace(item, path=f"{path}.{key}")
            return replaced
        return _clone_contract(value, path=path)

    materialized = replace(contract, path="contract")
    if not isinstance(materialized, dict):
        raise ValueError("contract must be a JSON object")
    return materialized
