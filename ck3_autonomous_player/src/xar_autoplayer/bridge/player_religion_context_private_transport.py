"""Read the current player's native Rite/Faith/Religion context; no action."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .player_spiritual_fulfillment_type import (
    normalize_player_spiritual_fulfillment_type_v1,
)
from .player_church_tax_inputs import normalize_player_church_tax_inputs_v1
from .player_pilgrimage_headless_activity_terms import (
    normalize_player_pilgrimage_candidate_routes_v1,
    normalize_player_pilgrimage_headless_activity_terms_v1,
)
from .player_confession_rite_permission import (
    normalize_player_confession_rite_permission_v1,
)
from .player_devotion_virtues import (
    normalize_player_piety_devotion_profile_v1,
    normalize_player_rite_virtue_sin_profile_v1,
    normalize_player_vow_of_poverty_terms_v1,
)
from .g2_private_query_transport import (
    private_g2_query_metadata_v1, read_private_g2_native_query_v1,
)
from .nonwar_private_build import (
    private_native_schema,
    private_native_build_identity, private_native_provenance,
)
from .version_identity import (
    CK3_12002, CK3_12003, CK3_12004, require_exact_native_backend, require_exact_native_build,
)


STEP = "query-player-religion-context-v1"
DOMAIN_KEY = "player_religion_context_v1"
SCHEMA = "ck3_12002_religion_context_v1"
PERMISSION = "allow_private_player_religion_context_query"
_CONTEXT_KEYS = {
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "rite_id", "faith_id", "religion_id", "faith_main_rite_id",
    "faith_key", "religion_key", "faith_fervor_raw",
    "spiritual_fulfillment_raw", "raw_scale",
}
_REFERENCE_KEYS = ("rite_id", "faith_id", "religion_id", "faith_main_rite_id")
_TAG_KEYS = ("faith_key", "religion_key")
_RESOURCE_KEYS = ("faith_fervor_raw", "spiritual_fulfillment_raw")


def normalize_player_religion_context_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Preserve native nulls, full references, strings and signed raw resources."""
    if not isinstance(value, dict) or set(value) != _CONTEXT_KEYS or value["schema"] != private_native_schema(SCHEMA, snapshot):
        raise ValueError("native player religion context schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    if build not in (CK3_12002, CK3_12003, CK3_12004) or build != private_native_build_identity(snapshot):
        raise ValueError("native player religion context belongs to another build")
    if (type(value["available"]) is not bool
            or type(value["capture_epoch"]) is not int
            or not 0 < value["capture_epoch"] <= 0xFFFFFFFFFFFFFFFF
            or type(value["date_raw"]) is not int
            or type(value["played_character_id"]) is not int
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000):
        raise ValueError("native player religion context scalar fields are malformed")
    for key in _REFERENCE_KEYS:
        reference = value[key]
        if reference is not None and (type(reference) is not int or not 0 <= reference <= 0xFFFFFFFF):
            raise ValueError(f"native player religion context full reference is malformed: {key}")
    for key in _TAG_KEYS:
        if value[key] is not None and not isinstance(value[key], str):
            raise ValueError(f"native player religion context tag is malformed: {key}")
    for key in _RESOURCE_KEYS:
        resource = value[key]
        if resource is not None and (type(resource) is not int or not -(1 << 63) <= resource < (1 << 63)):
            raise ValueError(f"native player religion context signed resource is malformed: {key}")
    if value["available"]:
        actor = snapshot.get("played_character")
        if (not isinstance(actor, Mapping)
                or value["played_character_id"] != actor.get("character_id")
                or value["date_raw"] != snapshot.get("date_raw")
                or value["unavailable_reason"] is not None
                or value["spiritual_fulfillment_raw"] is None):
            raise ValueError("native player religion context differs from its queried player frame")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("native player religion context lost its unavailable reason")
    # The provider's capture epoch is an owner-pump identity, not the bridge
    # snapshot revision. Neither it nor zero/native-null values are rewritten.
    return dict(value)


def normalize_player_spiritual_fulfillment_progress_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    """Preserve the optional native progress component; this is not a rate."""
    if value is None:
        return None
    keys = {
        "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
        "date_raw", "played_character_id", "current_fulfillment_raw",
        "active_level_index", "level_count", "level_lower_bound_raw",
        "level_upper_bound_raw", "progress_percent_raw", "highest_level",
        "runtime_minimum_raw", "runtime_maximum_raw", "raw_scale",
        "progress_unit", "is_monthly_change",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_spiritual_fulfillment_progress_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000
            or value["progress_unit"] != "percent" or value["is_monthly_change"] is not False):
        raise ValueError("native spiritual fulfillment progress schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native spiritual fulfillment progress differs from its current context")
    raw_keys = (
        "current_fulfillment_raw", "level_lower_bound_raw", "level_upper_bound_raw",
        "progress_percent_raw", "runtime_minimum_raw", "runtime_maximum_raw",
    )
    for key in raw_keys:
        if value[key] is not None and (type(value[key]) is not int
                or not -(1 << 63) <= value[key] < (1 << 63)):
            raise ValueError(f"native spiritual fulfillment progress signed raw is malformed: {key}")
    for key in ("active_level_index", "level_count"):
        if value[key] is not None and (type(value[key]) is not int
                or not -(1 << 31) <= value[key] < (1 << 31)):
            raise ValueError(f"native spiritual fulfillment progress level field is malformed: {key}")
    if value["highest_level"] is not None and type(value["highest_level"]) is not bool:
        raise ValueError("native spiritual fulfillment progress highest-level flag is malformed")
    if value["available"]:
        observed_keys = (*raw_keys, "active_level_index", "level_count", "highest_level")
        if (value["unavailable_reason"] is not None
                or any(value[key] is None for key in observed_keys)
                or value["current_fulfillment_raw"] != current_context["spiritual_fulfillment_raw"]):
            raise ValueError("available native spiritual fulfillment progress lost its actual values")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native spiritual fulfillment progress lost its reason")
    return dict(value)


def normalize_player_mystical_communion_decision_terms_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    """Publish the independent native final terms for the fixed decision."""
    if value is None:
        return None
    keys = {
        "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
        "date_raw", "played_character_id", "decision_id", "is_shown", "can_take",
        "affordable", "costs_raw", "raw_scale", "reasons_available", "can_take_reasons",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_mystical_communion_decision_terms_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or value["decision_id"] != "hold_mystical_communion_decision"
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000
            or type(value["reasons_available"]) is not bool):
        raise ValueError("native mystical communion decision terms schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native mystical communion decision terms differ from the current context")
    for key in ("is_shown", "can_take", "affordable"):
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native mystical communion decision predicate is malformed: {key}")
    costs = value["costs_raw"]
    if not isinstance(costs, dict) or set(costs) != {"gold", "treasury", "prestige", "piety"}:
        raise ValueError("native mystical communion evaluated costs are malformed")
    for key, raw in costs.items():
        if raw is not None and (type(raw) is not int or not -(1 << 63) <= raw < (1 << 63)):
            raise ValueError(f"native mystical communion evaluated signed cost is malformed: {key}")
    if value["reasons_available"]:
        if not isinstance(value["can_take_reasons"], str):
            raise ValueError("native mystical communion final reason text is malformed")
    elif value["can_take_reasons"] is not None:
        raise ValueError("unavailable native mystical communion final reasons lost their null")
    if value["available"]:
        if (value["unavailable_reason"] is not None
                or any(value[key] is None for key in ("is_shown", "can_take", "affordable"))
                or any(raw is None for raw in costs.values())):
            raise ValueError("available native mystical communion terms lost actual final values")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native mystical communion terms lost their reason")
    return {**value, "costs_raw": dict(costs)}


def normalize_player_pilgrimage_activity_type_terms_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    """Preserve fixed-type CanPlan and literal reasons; not a Start/quote."""
    if value is None:
        return None
    keys = {
        "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
        "date_raw", "played_character_id", "activity_id", "can_plan",
        "reasons_available", "can_plan_reasons",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_pilgrimage_activity_type_terms_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or value["activity_id"] != "activity_pilgrimage"
            or type(value["reasons_available"]) is not bool):
        raise ValueError("native pilgrimage activity type terms schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native pilgrimage type terms differ from the current context")
    if value["can_plan"] is not None and type(value["can_plan"]) is not bool:
        raise ValueError("native pilgrimage CanPlan predicate is malformed")
    if value["reasons_available"]:
        if not isinstance(value["can_plan_reasons"], str):
            raise ValueError("native pilgrimage CanPlan literal reasons are malformed")
    elif value["can_plan_reasons"] is not None:
        raise ValueError("unavailable native pilgrimage reasons lost their null")
    if value["available"]:
        if (value["unavailable_reason"] is not None or value["can_plan"] is None
                or value["reasons_available"] is not True):
            raise ValueError("available native pilgrimage type terms lost actual values")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native pilgrimage type terms lost their reason")
    return dict(value)


def normalize_player_confession_decision_terms_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    """Publish the independent native final terms for the fixed decision."""
    if value is None:
        return None
    keys = {
        "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
        "date_raw", "played_character_id", "decision_id", "is_shown", "can_take",
        "affordable", "costs_raw", "raw_scale", "reasons_available", "can_take_reasons",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_confession_decision_terms_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or value["decision_id"] != "pam_decision_confession"
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000
            or type(value["reasons_available"]) is not bool):
        raise ValueError("native confession decision terms schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native confession decision terms differ from the current context")
    for key in ("is_shown", "can_take", "affordable"):
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native confession decision predicate is malformed: {key}")
    costs = value["costs_raw"]
    if not isinstance(costs, dict) or set(costs) != {"gold", "treasury", "prestige", "piety"}:
        raise ValueError("native confession evaluated costs are malformed")
    for key, raw in costs.items():
        if raw is not None and (type(raw) is not int or not -(1 << 63) <= raw < (1 << 63)):
            raise ValueError(f"native confession evaluated signed cost is malformed: {key}")
    if value["reasons_available"]:
        if not isinstance(value["can_take_reasons"], str):
            raise ValueError("native confession final reason text is malformed")
    elif value["can_take_reasons"] is not None:
        raise ValueError("unavailable native confession final reasons lost their null")
    if value["available"]:
        if (value["unavailable_reason"] is not None
                or any(value[key] is None for key in ("is_shown", "can_take", "affordable"))
                or any(raw is None for raw in costs.values())):
            raise ValueError("available native confession terms lost actual final values")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native confession terms lost their reason")
    return {**value, "costs_raw": dict(costs)}


def normalize_player_church_income_profile_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    """Preserve independent native current and maximum monthly income."""
    if value is None:
        return None
    keys = {
        "schema", "read_only", "available", "unavailable_reason", "capture_epoch",
        "date_raw", "played_character_id", "current_monthly_income_raw",
        "maximum_monthly_income_raw", "raw_scale",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_player_church_income_profile_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000):
        raise ValueError("native church income profile schema is malformed")
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current_context[key]:
            raise ValueError("native church income profile differs from its current context")
    raw_keys = ("current_monthly_income_raw", "maximum_monthly_income_raw")
    for key in raw_keys:
        if value[key] is not None and (type(value[key]) is not int
                or not -(1 << 63) <= value[key] < (1 << 63)):
            raise ValueError(f"native church income signed raw is malformed: {key}")
    if value["available"]:
        if (value["unavailable_reason"] is not None
                or any(value[key] is None for key in raw_keys)):
            raise ValueError("available native church income lost actual values")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native church income lost its reason")
    return dict(value)


def query_player_religion_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, result = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP,
        expected_revision=expected_revision, timeout_seconds=timeout_seconds,
    )
    try:
        build = require_exact_native_backend(
            result.get("game_version"), result.get("executable_sha256"),
            result.get("backend_id"), suffix="player-religion-context-v1",
        )
        if (build not in (CK3_12002, CK3_12003) or build != private_native_build_identity(before)
                or result.get("domain_key") != DOMAIN_KEY
                or result.get("snapshot_revision") != before["native_revision"]
                or result.get("date_raw") != before.get("date_raw")):
            raise ValueError("native player religion context envelope differs from the queried build/frame")
        value = normalize_player_religion_context_v1(
            result.get("player_religion_context"), snapshot=before,
        )
        progress_fields = {}
        if "player_spiritual_fulfillment_progress" in result:
            progress_fields["player_spiritual_fulfillment_progress"] = (
                normalize_player_spiritual_fulfillment_progress_v1(
                    result["player_spiritual_fulfillment_progress"], current_context=value,
                )
            )
        decision_fields = {}
        if "player_mystical_communion_decision_terms" in result:
            decision_fields["player_mystical_communion_decision_terms"] = (
                normalize_player_mystical_communion_decision_terms_v1(
                    result["player_mystical_communion_decision_terms"], current_context=value,
                )
            )
        pilgrimage_fields = {}
        if "player_pilgrimage_activity_type_terms" in result:
            pilgrimage_fields["player_pilgrimage_activity_type_terms"] = (
                normalize_player_pilgrimage_activity_type_terms_v1(
                    result["player_pilgrimage_activity_type_terms"], current_context=value,
                )
            )
        if "player_pilgrimage_headless_activity_terms" in result:
            pilgrimage_fields["player_pilgrimage_headless_activity_terms"] = (
                normalize_player_pilgrimage_headless_activity_terms_v1(
                    result["player_pilgrimage_headless_activity_terms"], current_context=value,
                )
            )
        if "player_pilgrimage_candidate_routes" in result:
            pilgrimage_fields["player_pilgrimage_candidate_routes"] = (
                normalize_player_pilgrimage_candidate_routes_v1(
                    result["player_pilgrimage_candidate_routes"], current_context=value,
                    activity_terms=pilgrimage_fields.get("player_pilgrimage_headless_activity_terms"),
                )
            )
        confession_fields = {}
        if "player_confession_decision_terms" in result:
            confession_fields["player_confession_decision_terms"] = (
                normalize_player_confession_decision_terms_v1(
                    result["player_confession_decision_terms"], current_context=value,
                )
            )
        confession_permission_fields = {}
        if "player_confession_rite_permission" in result:
            confession_permission_fields["player_confession_rite_permission"] = (
                normalize_player_confession_rite_permission_v1(
                    result["player_confession_rite_permission"], current_context=value,
                )
            )
        church_income_fields = {}
        if "player_church_income_profile" in result:
            church_income_fields["player_church_income_profile"] = (
                normalize_player_church_income_profile_v1(
                    result["player_church_income_profile"], current_context=value,
                )
            )
        fulfillment_type_fields = {}
        if "player_spiritual_fulfillment_type" in result:
            fulfillment_type_fields["player_spiritual_fulfillment_type"] = (
                normalize_player_spiritual_fulfillment_type_v1(
                    result["player_spiritual_fulfillment_type"], current_context=value,
                )
            )
        church_tax_fields = {}
        if "player_church_tax_inputs" in result:
            church_tax_fields["player_church_tax_inputs"] = (
                normalize_player_church_tax_inputs_v1(
                    result["player_church_tax_inputs"], current_context=value,
                )
            )
        devotion_virtues_fields = {}
        for field, normalizer in (
            ("player_piety_devotion_profile", normalize_player_piety_devotion_profile_v1),
            ("player_rite_virtue_sin_profile", normalize_player_rite_virtue_sin_profile_v1),
            ("player_vow_of_poverty_terms", normalize_player_vow_of_poverty_terms_v1),
        ):
            if field in result:
                devotion_virtues_fields[field] = normalizer(result[field], current_context=value)
        expected_status = "observed" if value["available"] else "unavailable"
        if result.get("status") != expected_status:
            raise ValueError("native player religion context envelope lost its source status")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **value, **progress_fields, **decision_fields, **pilgrimage_fields,
        **confession_fields, **confession_permission_fields, **church_income_fields,
        **fulfillment_type_fields, **church_tax_fields,
        **devotion_virtues_fields,
        **private_native_provenance(before),
        **private_g2_query_metadata_v1(before),
        "snapshot_revision": result["snapshot_revision"],
        "query_date_raw": result["date_raw"],
        "backend_id": result["backend_id"], "domain_key": DOMAIN_KEY,
        "status": result["status"], "read_only": True, "advertised": False,
    }
