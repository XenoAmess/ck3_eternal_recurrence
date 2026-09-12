"""Conservative planner consumption of exact-build vanilla-event knowledge."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final

from .registry import (
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
    materialize_vanilla_timeline_contract,
    query_vanilla_event_knowledge_v1,
)


VANILLA_EVENT_REGISTRY_CHOICE_SCHEMA: Final = (
    "xar.ck3.vanilla-event-registry-choice"
)
VANILLA_EVENT_REGISTRY_CHOICE_SCHEMA_VERSION: Final = 1
VANILLA_EVENT_REGISTRY_CHOICE_POLICY: Final = (
    "exact-build-vanilla-event-registry-direct-projection-v1"
)
_CHOICE_EFFECT_PROFILE_SCHEMA: Final = "xar.ck3.vanilla-event-choice-effect"
_CHOICE_EFFECT_PROFILE_SCHEMA_VERSION: Final = 1

# These fields need a context-aware resolver. The first consumer stays on the
# direct projection that closed the real tgp_travel_events.0030 blocker.
_UNSUPPORTED_FIELDS: Final = frozenset(
    {
        "boolean_scope_name_sets",
        "boolean_scopes",
        "character_scope_differs_from",
        "character_scope_matches_any",
        "character_scopes",
        "handling_policy",
        "max_occurrences",
        "native_option_prefix_range",
        "native_option_suffix",
        "option_variants",
        "optional_character_scope_differs_from",
        "optional_character_scope_matches_any",
        "optional_character_scopes",
        "optional_scope_types",
        "optional_unique_character_scope_excludes",
        "scope_variants",
        "selection_deferred",
        "unavailable_character_scopes",
        "unique_character_scope_excludes",
    }
)


def _sequence(value: object) -> tuple[object, ...] | None:
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return tuple(value)
    return None


def _integer(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _typed_character_id(value: object) -> int | None:
    if not isinstance(value, Mapping):
        return None
    identity = value.get("typed_identity")
    if not isinstance(identity, Mapping):
        return None
    character_id = _integer(identity.get("character_id"))
    if (
        value.get("status") == "available"
        and value.get("type_key") == "character"
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
        and character_id is not None
        and character_id > 0
    ):
        return character_id
    return None


def _active(value: object) -> bool:
    return value not in (None, False, (), [], {})


def _selected_choice_effect_profile(
    knowledge: Mapping[str, object], native_index: int
) -> dict[str, object] | None:
    analysis = knowledge.get("analysis")
    if not isinstance(analysis, Mapping):
        return None
    profile = analysis.get("selected_choice_effect_profile")
    if not isinstance(profile, Mapping):
        return None
    if not (
        profile.get("schema") == _CHOICE_EFFECT_PROFILE_SCHEMA
        and profile.get("schema_version")
        == _CHOICE_EFFECT_PROFILE_SCHEMA_VERSION
        and _integer(profile.get("selected_native_option_index"))
        == native_index
        and isinstance(profile.get("selected_option_effects"), list)
        and isinstance(profile.get("common_after_effects"), list)
    ):
        return None
    return dict(profile)


def _response(
    *,
    status: str,
    event_key: object,
    reason: str | None,
    checks: Mapping[str, bool] | None = None,
    option_number: int | None = None,
    native_index: int | None = None,
    rendered_index: int | None = None,
    option_variant_index: int | None = None,
    choice_effect_profile: Mapping[str, object] | None = None,
) -> dict[str, object]:
    checked = dict(checks or {})
    return {
        "schema": VANILLA_EVENT_REGISTRY_CHOICE_SCHEMA,
        "schema_version": VANILLA_EVENT_REGISTRY_CHOICE_SCHEMA_VERSION,
        "status": status,
        "policy": VANILLA_EVENT_REGISTRY_CHOICE_POLICY,
        "source": "shared_vanilla_event_registry",
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "event_definition_key": (
            event_key if isinstance(event_key, str) else None
        ),
        "recommendation_scope": "bounded_timeline_continuation",
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "semantic_decision_ready": False,
        "selected_option_number": option_number,
        "selected_native_option_index": native_index,
        "selected_rendered_index": rendered_index,
        "matched_option_variant_index": option_variant_index,
        "option_projection_source": (
            "registered_option_variant"
            if option_variant_index is not None
            else "base_contract"
            if status == "recommended"
            else None
        ),
        "choice_effect_profile": (
            dict(choice_effect_profile)
            if choice_effect_profile is not None
            else None
        ),
        "checks": checked,
        "failed_checks": sorted(
            name for name, passed in checked.items() if not passed
        ),
        "unavailable_reason": reason,
    }


def _scope_projection_checks(
    context: Mapping[str, object],
    contract: Mapping[str, object],
    played_character_id: int,
) -> dict[str, bool]:
    raw_scopes = context.get("saved_scopes")
    scopes = raw_scopes if isinstance(raw_scopes, list) else []
    named_scopes = {
        row.get("name"): row.get("scope")
        for row in scopes
        if isinstance(row, Mapping) and isinstance(row.get("name"), str)
    }
    raw_name_sets = _sequence(contract.get("saved_scope_name_sets"))
    name_sets = []
    for value in raw_name_sets or ():
        names = _sequence(value)
        if names is not None:
            name_sets.append(set(names))
    scope_types = contract.get("scope_types")

    checks = {
        "root_character_id": (
            _typed_character_id(context.get("root_scope"))
            == played_character_id
            == contract.get("root_character_id")
        ),
        "saved_scope_rows_named_unique": len(named_scopes) == len(scopes),
        "saved_scope_names_exact": bool(
            name_sets
            and len(named_scopes) == len(scopes)
            and set(named_scopes) in name_sets
        ),
        "scope_types_cover_projection": bool(
            isinstance(scope_types, Mapping)
            and set(scope_types) == set(named_scopes)
        ),
    }
    if "saved_scope_count" in contract:
        checks["saved_scope_count"] = (
            _integer(contract.get("saved_scope_count")) == len(scopes)
        )
    else:
        counts = _sequence(contract.get("saved_scope_counts"))
        checks["saved_scope_count"] = bool(
            counts
            and all(_integer(value) is not None for value in counts)
            and len(scopes) in counts
        )
    if isinstance(scope_types, Mapping):
        for name, expected_type in scope_types.items():
            scope = named_scopes.get(name)
            checks[f"scope:{name}:type"] = bool(
                isinstance(scope, Mapping)
                and scope.get("status") == "available"
                and scope.get("type_key") == expected_type
            )
    return checks


def _option_projection_checks(
    context: Mapping[str, object],
    contract: Mapping[str, object],
    snapshot_option_count: int,
) -> tuple[dict[str, bool], dict[str, object] | None]:
    raw_options = context.get("options")
    options = raw_options if isinstance(raw_options, list) else []
    option_count = _integer(contract.get("option_count"))
    native_indices = _sequence(contract.get("native_option_indices"))
    selected_native = _integer(contract.get("selected_native_option_index"))
    selected_number = _integer(contract.get("selected_option_number"))
    disabled = _sequence(contract.get("disabled_native_option_indices", ()))
    disabled_set = set(disabled or ())
    snapshot_counts = _sequence(contract.get("snapshot_option_counts"))
    if snapshot_counts is None:
        one_count = _integer(
            contract.get("snapshot_option_count", option_count)
        )
        snapshot_counts = (one_count,) if one_count is not None else ()

    actual_native = tuple(
        row.get("native_option_index") if isinstance(row, Mapping) else None
        for row in options
    )
    native_typed = bool(
        native_indices is not None
        and all(_integer(value) is not None for value in native_indices)
        and len(set(native_indices)) == len(native_indices)
    )
    disabled_typed = bool(
        disabled is not None
        and all(_integer(value) is not None for value in disabled)
        and len(set(disabled)) == len(disabled)
    )
    checks = {
        "snapshot_option_count": snapshot_option_count in snapshot_counts,
        "rendered_option_count": option_count == len(options),
        "native_option_indices_exact": bool(
            native_typed and actual_native == native_indices
        ),
        "disabled_option_contract": bool(
            native_typed
            and disabled_typed
            and disabled_set.issubset(set(native_indices or ()))
            and selected_native not in disabled_set
        ),
        "selected_option_mapping": bool(
            selected_native is not None
            and selected_number == selected_native + 1
        ),
    }

    selected = None
    for rendered_index, value in enumerate(options):
        option = value if isinstance(value, Mapping) else {}
        native_index = _integer(option.get("native_option_index"))
        expected_enabled = native_index not in disabled_set
        checks[f"option:{rendered_index}:projection"] = bool(
            option.get("rendered_index") == rendered_index
            and option.get("shown") is True
            and option.get("enabled") is expected_enabled
            and option.get("fallback") is False
            and option.get("cancel") is False
        )
        if native_index == selected_native:
            selected = dict(option) if selected is None else None
    checks["selected_native_option_unique"] = selected is not None
    checks["selected_native_option_enabled"] = bool(
        selected is not None and selected.get("enabled") is True
    )
    return checks, selected


_OPTION_VARIANT_FIELDS: Final = frozenset(
    {
        "disabled_native_option_indices",
        "native_option_indices",
        "option_count",
        "selected_native_option_index",
        "selected_option_number",
        "snapshot_option_count",
        "snapshot_option_counts",
    }
)
_DIRECT_OPTION_VARIANT_EVENT_KEYS: Final = frozenset({"natural_disaster.7031"})


def _option_projection_signature(contract: Mapping[str, object]) -> tuple[object, ...]:
    snapshot_counts = _sequence(contract.get("snapshot_option_counts"))
    if snapshot_counts is None:
        snapshot_counts = (contract.get("snapshot_option_count"),)
    return (
        contract.get("option_count"),
        tuple(_sequence(contract.get("native_option_indices")) or ()),
        tuple(snapshot_counts),
        tuple(_sequence(contract.get("disabled_native_option_indices")) or ()),
        contract.get("selected_option_number"),
        contract.get("selected_native_option_index"),
    )


def _resolve_option_variant_contract(
    context: Mapping[str, object],
    contract: Mapping[str, object],
    snapshot_option_count: int,
) -> tuple[dict[str, object] | None, int | None, str | None]:
    raw_variants = _sequence(contract.get("option_variants"))
    if raw_variants is None:
        return dict(contract), None, None

    candidates: list[tuple[int | None, dict[str, object]]] = []
    for index, value in enumerate(raw_variants):
        if not isinstance(value, Mapping) or not set(value).issubset(
            _OPTION_VARIANT_FIELDS
        ):
            return None, None, "registered_option_variant_contract_unsupported"
        effective = dict(contract)
        effective.pop("option_variants", None)
        effective.update(value)
        candidates.append((index, effective))
    base = dict(contract)
    base.pop("option_variants", None)
    candidates.append((None, base))

    matches: list[tuple[int | None, dict[str, object]]] = []
    for index, effective in candidates:
        checks, selected = _option_projection_checks(
            context, effective, snapshot_option_count
        )
        if selected is not None and all(checks.values()):
            matches.append((index, effective))
    if not matches:
        return None, None, "registered_option_variant_projection_drift"

    signatures = {
        _option_projection_signature(effective) for _index, effective in matches
    }
    if len(signatures) != 1:
        return None, None, "registered_option_variant_projection_ambiguous"
    return matches[0][1], matches[0][0], None


def recommend_registered_vanilla_event_option_v1(
    event_context: Mapping[str, object],
    *,
    played_character_id: object,
    snapshot_option_count: object,
) -> dict[str, object]:
    """Return one direct registry choice or a typed non-action result."""

    event_key = event_context.get("event_definition_key")
    knowledge = query_vanilla_event_knowledge_v1(
        event_key if isinstance(event_key, str) else ""
    )
    if knowledge.get("status") != "available":
        return _response(
            status="not_registered",
            event_key=event_key,
            reason=str(knowledge.get("unavailable_reason")),
        )

    raw_contract = knowledge.get("contract")
    character_id = _integer(played_character_id)
    option_count = _integer(snapshot_option_count)
    if (
        not isinstance(raw_contract, Mapping)
        or character_id is None
        or character_id <= 0
        or option_count is None
    ):
        return _response(
            status="blocked",
            event_key=event_key,
            reason="played_character_or_contract_projection_unavailable",
        )
    contract = materialize_vanilla_timeline_contract(
        raw_contract, character_id
    )
    option_variant_index = None
    if (
        event_key in _DIRECT_OPTION_VARIANT_EVENT_KEYS
        and _active(contract.get("option_variants"))
    ):
        resolved, option_variant_index, variant_error = (
            _resolve_option_variant_contract(
                event_context, contract, option_count
            )
        )
        if resolved is None:
            return _response(
                status="blocked",
                event_key=event_key,
                reason=variant_error,
                checks={"option_variant_projection": False},
            )
        contract = resolved
    unsupported = sorted(
        field
        for field in _UNSUPPORTED_FIELDS
        if _active(contract.get(field))
    )
    if unsupported:
        return _response(
            status="blocked",
            event_key=event_key,
            reason="registered_contract_requires_extended_consumer",
            checks={
                f"direct_projection_support:{field}": False
                for field in unsupported
            },
        )

    checks = {
        "context_schema": event_context.get("schema")
        == "current-event-window-context-v1",
        "context_schema_version": event_context.get("schema_version") == 1,
        "context_available": event_context.get("status") == "available",
        "unique_window": event_context.get("window_match_count") == 1,
        "event_definition_key": event_key
        == knowledge.get("event_definition_key"),
    }
    checks.update(
        _scope_projection_checks(event_context, contract, character_id)
    )
    option_checks, selected = _option_projection_checks(
        event_context, contract, option_count
    )
    checks.update(option_checks)
    if not all(checks.values()) or selected is None:
        return _response(
            status="blocked",
            event_key=event_key,
            reason="registered_contract_projection_drift",
            checks=checks,
        )

    selected_native = _integer(contract.get("selected_native_option_index"))
    selected_number = _integer(contract.get("selected_option_number"))
    selected_rendered = _integer(selected.get("rendered_index"))
    assert selected_native is not None
    assert selected_number is not None
    assert selected_rendered is not None
    return _response(
        status="recommended",
        event_key=event_key,
        reason=None,
        checks=checks,
        option_number=selected_number,
        native_index=selected_native,
        rendered_index=selected_rendered,
        option_variant_index=option_variant_index,
        choice_effect_profile=_selected_choice_effect_profile(
            knowledge, selected_native
        ),
    )


__all__ = [
    "VANILLA_EVENT_REGISTRY_CHOICE_POLICY",
    "VANILLA_EVENT_REGISTRY_CHOICE_SCHEMA",
    "VANILLA_EVENT_REGISTRY_CHOICE_SCHEMA_VERSION",
    "recommend_registered_vanilla_event_option_v1",
]
