"""Observe the exact4 current creation model without selecting or creating."""
from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_holy_site_private_transport import _availability, _ref
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

STEP = "query-player-holy-site-creation-context-v1"
PERMISSION = "allow_private_player_holy_site_creation_context_query"
DOMAIN = "player_holy_site_creation_context_v1"
RESULT_KEY = "player_holy_site_creation_context"


def _integer(value: object, field: str, low: int, high: int, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native creation context integer is malformed: {field}")
    return value


def _boolean(value: object, field: str, *, nullable: bool = False) -> bool | None:
    if value is None and nullable:
        return None
    if type(value) is not bool:
        raise ValueError(f"native creation context boolean is malformed: {field}")
    return value


def _array(value: object, field: str) -> list:
    if not isinstance(value, list) or len(value) > 8192:
        raise ValueError(f"native creation context collection is malformed: {field}")
    return value


def _ids(value: object, field: str) -> list[int]:
    return [_ref(item, field, nullable=False) for item in _array(value, field)]


def _key(value: object, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError(f"native creation context definition key is malformed: {field}")
    return value


def _observed(result: Mapping[str, object], observed: str, value: str, *, integer: bool = False) -> None:
    flag = _boolean(result[observed], observed)
    if integer:
        _integer(result[value], value, -(2**63), 2**63 - 1, nullable=not flag)
    else:
        _boolean(result[value], value, nullable=not flag)
    if not flag and result[value] is not None:
        raise ValueError(f"unobserved native creation value must remain null: {value}")


def _tooltip(result: Mapping[str, object], observed: str, value: str) -> None:
    flag = _boolean(result[observed], observed)
    if flag:
        if not isinstance(result[value], str):
            raise ValueError(f"native creation tooltip is malformed: {value}")
    elif result[value] is not None:
        raise ValueError(f"unobserved native creation tooltip must remain null: {value}")


def normalize_player_holy_site_creation_context_v1(
    value: object, *, snapshot: Mapping[str, object],
) -> dict[str, object]:
    keys = """
        schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw
        played_character_id player_faith_id window_present root_present window_faith_id
        player_faith_matches models_available models_complete available_holy_site_types
        potential_barony_title_ids enshrinable_artifact_ids selection_available selected_type_key
        selected_barony_title_id selected_artifact_ids native_rarity_sum_observed native_rarity_sum_raw
        raw_scale native_enabled_observed native_create_button_enabled bypass_requirements_observed
        bypass_requirements_raw normal_requirements_legality_observed normal_requirements_can_create
        create_tooltip_available create_tooltip cached_resource_quote_available cached_resource_vector_raw
        cached_quote_freshness_observed native_affordability_observed native_affordable
        rendered_visibility_observed read_only action_ready create_invoked
    """
    required = set(keys.split())
    if not isinstance(value, dict) or set(value) not in (required, required | {"preview_identity_sha256"}):
        raise ValueError("native creation context root shape differs")
    result = dict(_availability(value, "creation context"))
    result.setdefault("preview_identity_sha256", None)
    preview = result["preview_identity_sha256"]
    if preview is not None:
        import re
        if not isinstance(preview, str) or re.fullmatch(r"[0-9a-f]{64}", preview) is None:
            raise ValueError("creation preview identity must be lowercase SHA-256 or null")
        if result["available"] is not True:
            raise ValueError("unavailable creation context cannot invent a preview identity")
    if (result["schema"] != "ck3_12004_player_holy_site_creation_context_v1"
            or require_exact_native_build(result["game_version"], result["executable_sha256"]) != CK3_12004
            or private_native_build_identity(snapshot) != CK3_12004):
        raise ValueError("native creation context requires exact 1.20.0.4")
    _integer(result["played_character_id"], "played_character_id", -(2**31), 2**31 - 1)
    _integer(result["date_raw"], "date_raw", -(2**31), 2**31 - 1)
    _integer(result["capture_epoch"], "capture_epoch", 1, 2**64 - 1)
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or result["played_character_id"] != actor.get("character_id")
            or result["date_raw"] != snapshot.get("date_raw")):
        raise ValueError("native creation context crossed its player/frame")
    for name in ("player_faith_id", "window_faith_id"):
        _ref(result[name], name)
    for name in ("window_present", "root_present", "player_faith_matches"):
        _boolean(result[name], name, nullable=not result["available"])
        if not result["available"] and result[name] is not None:
            raise ValueError("unavailable creation context cannot invent window observations")
    if result["player_faith_matches"] is True and (
            result["player_faith_id"] is None or result["window_faith_id"] != result["player_faith_id"]):
        raise ValueError("native creation context claims another faith as the player faith")
    if result["root_present"] is True and result["window_present"] is not True:
        raise ValueError("native creation root lacks its window")
    if (type(result["raw_scale"]) is not int or result["raw_scale"] != 100000
            or result["read_only"] is not True
            or any(result[name] is not False for name in (
                "action_ready", "create_invoked", "cached_quote_freshness_observed",
                "native_affordability_observed", "rendered_visibility_observed"))
            or result["native_affordable"] is not None):
        raise ValueError("native creation context invented a create action, visibility, or fresh affordability")

    for name in ("models_available", "models_complete", "selection_available",
                 "cached_resource_quote_available"):
        _boolean(result[name], name)
    if result["models_available"] != result["models_complete"]:
        raise ValueError("native creation context cannot promote partial models to a complete collection")
    if result["available"] and result["models_available"] is not True:
        raise ValueError("available native creation context lacks complete observed models")
    if result["models_available"]:
        for raw in _array(result["available_holy_site_types"], "available_holy_site_types"):
            if not isinstance(raw, dict) or set(raw) != {
                    "type_key", "is_selected", "native_can_pick_observed", "native_can_pick",
                    "tooltip_available", "tooltip"}:
                raise ValueError("native creation type candidate shape differs")
            _key(raw["type_key"], "type_key")
            _boolean(raw["is_selected"], "type candidate is_selected")
            _observed(raw, "native_can_pick_observed", "native_can_pick")
            _tooltip(raw, "tooltip_available", "tooltip")
        _ids(result["potential_barony_title_ids"], "potential_barony_title_ids")
        _ids(result["enshrinable_artifact_ids"], "enshrinable_artifact_ids")
    elif any(result[name] is not None for name in (
            "available_holy_site_types", "potential_barony_title_ids", "enshrinable_artifact_ids")):
        raise ValueError("unobserved native creation models must remain null, including collections")

    if result["selection_available"]:
        _key(result["selected_type_key"], "selected_type_key", nullable=True)
        _ref(result["selected_barony_title_id"], "selected_barony_title_id")
        _ids(result["selected_artifact_ids"], "selected_artifact_ids")
    elif any(result[name] is not None for name in (
            "selected_type_key", "selected_barony_title_id", "selected_artifact_ids")):
        raise ValueError("unobserved native creation selection must remain null")

    _observed(result, "native_rarity_sum_observed", "native_rarity_sum_raw", integer=True)
    _observed(result, "native_enabled_observed", "native_create_button_enabled")
    _observed(result, "normal_requirements_legality_observed", "normal_requirements_can_create")
    _boolean(result["bypass_requirements_observed"], "bypass_requirements_observed")
    _integer(result["bypass_requirements_raw"], "bypass_requirements_raw", 0, 255,
             nullable=not result["bypass_requirements_observed"])
    if not result["bypass_requirements_observed"] and result["bypass_requirements_raw"] is not None:
        raise ValueError("unobserved native bypass requirements must remain null")
    if result["normal_requirements_legality_observed"] and (
            result["native_enabled_observed"] is not True
            or result["bypass_requirements_observed"] is not True
            or result["bypass_requirements_raw"] != 0
            or result["normal_requirements_can_create"] != result["native_create_button_enabled"]):
        raise ValueError("normal creation requirements require an observed native result with bypass zero")
    _tooltip(result, "create_tooltip_available", "create_tooltip")
    if result["cached_resource_quote_available"]:
        quote = _array(result["cached_resource_vector_raw"], "cached_resource_vector_raw")
        if len(quote) != 10:
            raise ValueError("native creation cached resource vector must have ten raw values")
        for raw in quote:
            _integer(raw, "cached resource raw", -(2**63), 2**63 - 1)
    elif result["cached_resource_vector_raw"] is not None:
        raise ValueError("unobserved native cached quote must remain null")
    if not result["available"] and any(result[name] is not False for name in (
            "models_available", "models_complete", "selection_available",
            "native_rarity_sum_observed", "native_enabled_observed", "bypass_requirements_observed",
            "normal_requirements_legality_observed", "create_tooltip_available",
            "cached_resource_quote_available")):
        raise ValueError("unavailable native creation root cannot invent component observations")
    return result


def query_player_holy_site_creation_context_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    before, envelope = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        timeout_seconds=timeout_seconds, include_native_command_history=False)
    try:
        if (require_exact_native_backend(envelope.get("game_version"), envelope.get("executable_sha256"),
                envelope.get("backend_id"), suffix="player-holy-site-creation-context-v1") != CK3_12004
                or envelope.get("domain_key") != DOMAIN
                or envelope.get("snapshot_revision") != before.get("native_revision")
                or envelope.get("date_raw") != before.get("date_raw")):
            raise ValueError("native creation context envelope differs from its build/frame")
        value = normalize_player_holy_site_creation_context_v1(envelope.get(RESULT_KEY), snapshot=before)
        if envelope.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native creation context envelope lost root availability")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": envelope["snapshot_revision"], "backend_id": envelope["backend_id"],
            "domain_key": DOMAIN, "status": envelope["status"], "advertised": False}
