"""Native pilgrimage offers, activity-only quotes and local candidate routes.

These are independent read-only terms. A quote includes no journey cost and
neither candidate selection nor a valid outbound route establishes CanStart.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


_ACTIVITY_SCHEMA = "ck3_12003_player_pilgrimage_headless_activity_terms_v1"
_ROUTE_SCHEMA = "ck3_12003_pilgrimage_candidate_route_v1"
_QUOTE_SCOPE = "activity_host_phase_and_selected_options"


def _object(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native pilgrimage {label} fields are malformed")
    return value


def _integer(value: object, bits: int, label: str, *, nullable: bool = False,
             unsigned: bool = False) -> None:
    if value is None and nullable:
        return
    lower, upper = (0, 1 << bits) if unsigned else (-(1 << (bits - 1)), 1 << (bits - 1))
    if type(value) is not int or not lower <= value < upper:
        raise ValueError(f"native pilgrimage {label} integer is malformed")


def _boolean(value: object, label: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if type(value) is not bool:
        raise ValueError(f"native pilgrimage {label} predicate is malformed")


def _reasons(available: object, reasons: object, label: str) -> None:
    _boolean(available, label + " reasons availability")
    if (available is True and not isinstance(reasons, str)) or (
            available is False and reasons is not None):
        raise ValueError(f"native pilgrimage {label} literal reasons are malformed")


def _frame(value: Mapping[str, object], current_context: Mapping[str, object]) -> None:
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native pilgrimage terms differ from the current context")
    _boolean(value["available"], "availability")
    if value["read_only"] is not True:
        raise ValueError("native pilgrimage terms lost their read-only identity")
    reason = value["unavailable_reason"]
    if value["available"]:
        if reason is not None:
            raise ValueError("available native pilgrimage terms have an unavailable reason")
    elif not isinstance(reason, str) or not reason:
        raise ValueError("unavailable native pilgrimage terms lost their native reason")


def _predicate(value: object, label: str) -> None:
    value = _object(value, {"value", "reasons_available", "reasons"}, label)
    _boolean(value["value"], label)
    _reasons(value["reasons_available"], value["reasons"], label)


def _options(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("native pilgrimage default options are malformed")
    for option in value:
        option = _object(option, {
            "category_definition_index", "option_definition_index", "selected_special",
        }, "default option")
        for key in ("category_definition_index", "option_definition_index"):
            _integer(option[key], 32, key)
        _boolean(option["selected_special"], "selected special")


def _phases(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("native pilgrimage configured phases are malformed")
    for phase in value:
        phase = _object(phase, {
            "phase_definition_index", "province_id", "native_default_phase", "native_phase_order_raw",
        }, "configured phase")
        _integer(phase["province_id"], 32, "configured phase province")
        for key in ("phase_definition_index", "native_phase_order_raw"):
            _integer(phase[key], 32, key, nullable=True)
        _boolean(phase["native_default_phase"], "native default phase", nullable=True)


def _quote(value: object) -> None:
    value = _object(value, {
        "native_config_date_raw", "quote_scope", "journey_cost_included",
        "activity_cost_raw_slots", "activity_gold_cost_raw", "activity_treasury_cost_raw",
        "gold_treasury_scale", "affordable", "affordability_reasons_available",
        "affordability_reasons", "default_options_used", "configured_phases",
    }, "activity quote")
    if (value["quote_scope"] != _QUOTE_SCOPE or value["journey_cost_included"] is not False
            or type(value["gold_treasury_scale"]) is not int
            or value["gold_treasury_scale"] != 100000):
        raise ValueError("native pilgrimage quote lost its activity-only scope or raw scale")
    _integer(value["native_config_date_raw"], 32, "native config date raw")
    slots = value["activity_cost_raw_slots"]
    if not isinstance(slots, list) or len(slots) != 10:
        raise ValueError("native pilgrimage activity quote lost its ten native cost slots")
    for raw in slots:
        _integer(raw, 64, "activity cost raw")
    for key, slot in (("activity_gold_cost_raw", 0), ("activity_treasury_cost_raw", 6)):
        _integer(value[key], 64, key)
        if value[key] != slots[slot]:
            raise ValueError("native pilgrimage activity quote cost alias differs from its native slot")
    _boolean(value["affordable"], "activity affordability")
    _reasons(value["affordability_reasons_available"], value["affordability_reasons"],
             "activity affordability")
    _options(value["default_options_used"])
    _phases(value["configured_phases"])


def normalize_player_pilgrimage_headless_activity_terms_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    """Retain native offers, separate cap results and original configuration order."""
    if value is None:
        return None
    value = _object(value, {
        "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
        "date_raw", "played_character_id", "activity_id", "quote_scope",
        "journey_cost_included", "default_options_provenance", "phase_choice_provenance",
        "rite_id", "faith_id", "native_filter", "configured_phase_count", "total_phase_cap",
        "single_location", "resolved_location_phase_count", "selected_special_definition_index",
        "default_options", "initial_configured_phases", "candidates",
    }, "headless activity terms")
    if (value["schema"] != _ACTIVITY_SCHEMA or value["activity_id"] != "activity_pilgrimage"
            or value["quote_scope"] != _QUOTE_SCOPE or value["journey_cost_included"] is not False
            or value["default_options_provenance"] != "native_actual_actor_default"
            or value["phase_choice_provenance"] != "native_mode1_offers_independent_predicates"):
        raise ValueError("native pilgrimage headless activity terms identity is malformed")
    _frame(value, current_context)
    for key in ("rite_id", "faith_id"):
        _integer(value[key], 32, key, nullable=True, unsigned=True)
    for key in ("native_filter", "configured_phase_count", "total_phase_cap",
                "resolved_location_phase_count", "selected_special_definition_index"):
        _integer(value[key], 32, key, nullable=True)
    _boolean(value["single_location"], "single location", nullable=True)
    _options(value["default_options"])
    _phases(value["initial_configured_phases"])
    candidates = value["candidates"]
    if not isinstance(candidates, list):
        raise ValueError("native pilgrimage factory candidate array is malformed")
    for candidate in candidates:
        candidate = _object(candidate, {
            "holy_site_id", "title_id", "province_id", "location_predicate",
            "same_province_phase_count", "same_province_cap_applies", "same_province_phase_cap",
            "same_province_cap_allows", "total_cap_applies", "total_cap_allows", "can_select",
            "phase_choices",
        }, "factory candidate")
        for key in ("holy_site_id", "title_id"):
            _integer(candidate[key], 32, key, unsigned=True)
        for key in ("province_id", "same_province_phase_count"):
            _integer(candidate[key], 32, key)
        _integer(candidate["same_province_phase_cap"], 32, "same province phase cap", nullable=True)
        for key in ("same_province_cap_applies", "same_province_cap_allows", "total_cap_applies"):
            _boolean(candidate[key], key)
        for key in ("total_cap_allows", "can_select"):
            _boolean(candidate[key], key, nullable=True)
        _predicate(candidate["location_predicate"], "destination location")
        if not isinstance(candidate["phase_choices"], list):
            raise ValueError("native pilgrimage phase choices are malformed")
        for phase in candidate["phase_choices"]:
            phase = _object(phase, {
                "phase_definition_index", "province_id", "native_ai_choice_score_raw", "shown",
                "location", "can_select_phase", "quote_unavailable_reason", "activity_quote",
            }, "phase choice")
            for key in ("phase_definition_index", "province_id", "native_ai_choice_score_raw"):
                _integer(phase[key], 32, key)
            _predicate(phase["shown"], "phase shown")
            _predicate(phase["location"], "phase location")
            _boolean(phase["can_select_phase"], "phase selection")
            if phase["activity_quote"] is None:
                if not isinstance(phase["quote_unavailable_reason"], str) or not phase["quote_unavailable_reason"]:
                    raise ValueError("unavailable native pilgrimage activity quote lost its reason")
            else:
                if phase["quote_unavailable_reason"] is not None:
                    raise ValueError("native pilgrimage activity quote has an unavailable reason")
                _quote(phase["activity_quote"])
    # None, False, empty reason text and signed costs all remain native values.
    # Counts, cap gates, selections and configured phase order are not inferred.
    return deepcopy(value)


def normalize_player_pilgrimage_candidate_routes_v1(
    value: object, *, current_context: Mapping[str, object],
    activity_terms: Mapping[str, object] | None,
) -> list[dict[str, object]] | None:
    """Keep native route validity and arrival DateRaw for genuine factory offers."""
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("native pilgrimage candidate routes array is malformed")
    offered_provinces = {
        candidate["province_id"] for candidate in activity_terms["candidates"]
    } if activity_terms is not None else set()
    for route in value:
        route = _object(route, {
            "schema", "configuration_source", "read_only", "available", "unavailable_reason",
            "capture_epoch", "date_raw", "played_character_id", "candidate_province_id",
            "native_start_province_id", "route_valid", "outbound_arrival_date_raw",
        }, "candidate route")
        if (route["schema"] != _ROUTE_SCHEMA
                or route["configuration_source"] != "native_local_candidate"):
            raise ValueError("native pilgrimage candidate route identity is malformed")
        _frame(route, current_context)
        _integer(route["candidate_province_id"], 32, "candidate route province")
        if route["candidate_province_id"] not in offered_provinces:
            raise ValueError("native pilgrimage route province is absent from its actual factory offers")
        for key in ("native_start_province_id", "outbound_arrival_date_raw"):
            _integer(route[key], 32, key, nullable=True)
        _boolean(route["route_valid"], "route validity", nullable=True)
        if route["available"] and (route["native_start_province_id"] is None or route["route_valid"] is None
                or (route["route_valid"] is True and route["outbound_arrival_date_raw"] is None)):
            raise ValueError("available native pilgrimage route lost its actual values")
        if route["route_valid"] is False and route["outbound_arrival_date_raw"] is not None:
            raise ValueError("invalid native pilgrimage route has an evaluated arrival date")
    # DateRaw is the engine representation; subtracting raw values is not a
    # duration. Local route defaults do not supply journey cost or CanStart.
    return deepcopy(value)
