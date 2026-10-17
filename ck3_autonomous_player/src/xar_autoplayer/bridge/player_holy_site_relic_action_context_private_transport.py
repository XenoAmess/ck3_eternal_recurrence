"""Strict exact-build relic action-context observation; no action submission."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_holy_site_private_transport import _ref
from .player_holy_site_relic_permissions_private_transport import (
    _boolean, _integer, _observed_bool, _shape,
    normalize_player_holy_site_relic_permissions_v1,
)
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

STEP = "query-player-holy-site-relic-action-context-v1"
PERMISSION = "allow_private_player_holy_site_relic_action_context_query"
DOMAIN = "player_holy_site_relic_action_context_v1"
RESULT_KEY = "player_holy_site_relic_action_context"
OWNER_KEYS = """available object_resolved artifact_id character_owner_id holy_site_owner_id rarity_level
    character_owner_matches_player holy_site_owner_matches_requested player_owned_reference_member
    player_equipped_slot_member site_equipped_slot_member unavailable_reason""".split()
DESTINATION_KEYS = """available action_kind selected_slot_index explicit_slot_type_compatible
    original_picker_called effective_slot_index replacing_artifact_id replacing_artifact method
    effective_slot_script_permission_independently_observed unavailable_reason""".split()
TEXT_KEYS = "available text unavailable_reason".split()
TEXT_FIELDS = ("selected_action_effect_description", "enshrine_disabled_tooltip", "remove_disabled_tooltip")


def _q(value: str) -> str:
    """Native Q: retain UTF-8, escape every control as lowercase \\u00xx."""
    return '"' + ''.join('\\' + c if c in {'"', '\\'} else
                          '\\u%04x' % ord(c) if ord(c) < 32 else c for c in value) + '"'


def _literal(value: object) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    if isinstance(value, str):
        return _q(value)
    raise ValueError("unsupported value in native relic action preview canonical form")


def _observed_json(value: Mapping[str, object]) -> str:
    return '{' + ','.join(_q(k) + ':' + _literal(value[k])
                          for k in ("available", "value", "unavailable_reason")) + '}'


def _owner_json(value: Mapping[str, object]) -> str:
    return '{' + ','.join(_q(k) + ':' + (_observed_json(value[k])
        if k in {"player_equipped_slot_member", "site_equipped_slot_member"} else _literal(value[k]))
        for k in OWNER_KEYS) + '}'


def _destination_json(value: Mapping[str, object]) -> str:
    return '{' + ','.join(_q(k) + ':' + (_owner_json(value[k]) if k == "replacing_artifact" else _literal(value[k]))
                           for k in DESTINATION_KEYS) + '}'


def _text_json(value: Mapping[str, object]) -> str:
    return '{' + ','.join(_q(k) + ':' + _literal(value[k]) for k in TEXT_KEYS) + '}'


def relic_action_preview_canonical_v1(value: Mapping[str, object]) -> str:
    permissions = value["permissions"]
    return '|'.join(["ck3-relic-action-preview-v1", str(value["date_raw"]),
        str(value["played_character_id"]), _literal(permissions["player_faith_id"]), str(value["requested_holy_site_id"]),
        str(value["requested_artifact_id"]), _owner_json(value["artifact_ownership"]),
        _destination_json(value["destination"]), *[_text_json(value[key]) for key in TEXT_FIELDS],
        _observed_json(permissions["artifact_permissions"]["can_enshrine"]),
        _observed_json(permissions["artifact_permissions"]["can_remove"]),
        _observed_json(permissions["current_buttons"]["can_enshrine"]),
        _observed_json(permissions["current_buttons"]["can_remove"])])


def _ownership(value: object, *, expected_artifact: int | None, actor: int, site: int,
               permissions: Mapping[str, object]) -> dict[str, object]:
    result = _shape(value, "artifact ownership", ' '.join(OWNER_KEYS))
    _boolean(result["object_resolved"], "ownership object_resolved")
    for name in ("artifact_id", "character_owner_id", "holy_site_owner_id"):
        _ref(result[name], "ownership " + name)
    if result["artifact_id"] != expected_artifact:
        raise ValueError("native ownership crossed its artifact full reference")
    _integer(result["rarity_level"], "ownership rarity_level", nullable=True)
    for name in ("character_owner_matches_player", "holy_site_owner_matches_requested", "player_owned_reference_member"):
        _boolean(result[name], "ownership " + name, nullable=True)
    player_equipped = _observed_bool(result["player_equipped_slot_member"], "player equipped membership")
    site_equipped = _observed_bool(result["site_equipped_slot_member"], "site equipped membership")
    if not result["object_resolved"] and (any(result[name] is not None for name in (
            "character_owner_id", "holy_site_owner_id", "rarity_level", "character_owner_matches_player",
            "holy_site_owner_matches_requested", "player_owned_reference_member"))
            or player_equipped["available"] or site_equipped["available"]):
        raise ValueError("unresolved relic ownership contains invented object observations")
    if result["character_owner_matches_player"] is not None and result["character_owner_matches_player"] != (result["character_owner_id"] == actor):
        raise ValueError("native character ownership comparison differs from its actual full ID")
    if result["holy_site_owner_matches_requested"] is not None and result["holy_site_owner_matches_requested"] != (result["holy_site_owner_id"] == site):
        raise ValueError("native holy-site ownership comparison differs from its actual full ID")
    inventory = permissions["player_inventory"]
    if result["player_owned_reference_member"] is not None:
        if (not inventory["available"] or inventory["owner_matches_player"] is not True
                or result["player_owned_reference_member"] != (expected_artifact in inventory["artifact_ids"])):
            raise ValueError("native owned-reference membership differs from current player inventory")
    if result["available"] and (not result["object_resolved"] or expected_artifact is None
            or result["rarity_level"] is None or result["character_owner_matches_player"] is None
            or result["holy_site_owner_matches_requested"] is None
            or result["character_owner_id"] is not None and result["holy_site_owner_id"] is not None):
        raise ValueError("available ownership lacks resolved, exclusive native owner channels")
    return result


def normalize_player_holy_site_relic_action_context_v1(
    value: object, *, snapshot: Mapping[str, object], holy_site_id: int, artifact_id: int,
) -> dict[str, object]:
    result = _shape(value, "relic action context", """
        schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw played_character_id
        requested_holy_site_id requested_artifact_id loaded_source_pins_verified permissions artifact_ownership
        destination selected_artifact_matches_request selected_action_effect_description enshrine_disabled_tooltip
        remove_disabled_tooltip preview_identity_available preview_identity_sha256 evaluation_context action_ready
        business_outcome_observed beneficiaries_observed beneficiaries read_only
    """)
    if (result["schema"] != "ck3_12004_player_holy_site_relic_action_context_v1"
            or require_exact_native_build(result["game_version"], result["executable_sha256"]) != CK3_12004
            or private_native_build_identity(snapshot) != CK3_12004):
        raise ValueError("native relic action context requires exact 1.20.0.4")
    actor = snapshot.get("played_character")
    _integer(result["played_character_id"], "played_character_id", low=0, high=2**32 - 2)
    _integer(result["date_raw"], "date_raw")
    _integer(result["capture_epoch"], "capture_epoch", low=1, high=2**64 - 1)
    _ref(result["requested_holy_site_id"], "requested_holy_site_id", nullable=False)
    _ref(result["requested_artifact_id"], "requested_artifact_id", nullable=False)
    if (not isinstance(actor, Mapping) or result["played_character_id"] != actor.get("character_id")
            or result["date_raw"] != snapshot.get("date_raw")
            or result["requested_holy_site_id"] != holy_site_id or result["requested_artifact_id"] != artifact_id):
        raise ValueError("native relic action context crossed its request/player/frame")
    _boolean(result["loaded_source_pins_verified"], "loaded_source_pins_verified")
    if (result["read_only"] is not True or result["action_ready"] is not False
            or result["business_outcome_observed"] is not False or result["beneficiaries_observed"] is not False
            or result["beneficiaries"] is not None):
        raise ValueError("native relic action context invented action readiness, outcome or benefits")
    permissions = normalize_player_holy_site_relic_permissions_v1(result["permissions"], snapshot=snapshot,
                         holy_site_id=holy_site_id, artifact_id=artifact_id)
    if permissions["capture_epoch"] != result["capture_epoch"]:
        raise ValueError("nested relic permissions crossed this owner capture")
    evaluation = _shape(result["evaluation_context"], "action evaluation context", """
        getter_backend native_getter_calls owner_thread_requirement gameplay_command_submitted window_selection_written
        world_cache_written original_effect_description_evaluates_script_context script_rng_effects_verified script_rng_effects
    """, availability=False)
    _integer(evaluation["native_getter_calls"], "native_getter_calls", low=0, high=2**32 - 1)
    if (evaluation["getter_backend"] not in {"source_bound_native_getter", "owned_fixture_injected_getter", "unavailable"}
            or evaluation["owner_thread_requirement"] != "existing_religion_owner_callback"
            or any(evaluation[name] is not False for name in ("gameplay_command_submitted", "window_selection_written",
                                                            "world_cache_written", "script_rng_effects_verified"))
            or evaluation["original_effect_description_evaluates_script_context"] is not True
            or evaluation["script_rng_effects"] != "unknown"
            or evaluation["getter_backend"] == "source_bound_native_getter" and not result["loaded_source_pins_verified"]):
        raise ValueError("native relic action context lost its getter/source/evaluation boundaries")
    ownership = _ownership(result["artifact_ownership"], expected_artifact=artifact_id,
                          actor=result["played_character_id"], site=holy_site_id, permissions=permissions)
    destination = _shape(result["destination"], "action destination", ' '.join(DESTINATION_KEYS))
    if (destination["action_kind"] not in {"unknown", "enshrine", "remove"}
            or destination["method"] != "source_bound_explicit_slot_branch_then_original_native_picker"
            or destination["effective_slot_script_permission_independently_observed"] is not False):
        raise ValueError("native effective slot cannot claim an independently observed script permission")
    for name in ("selected_slot_index", "effective_slot_index"):
        _integer(destination[name], name, nullable=True, low=0, high=8191)
    _ref(destination["replacing_artifact_id"], "replacing_artifact_id")
    _boolean(destination["explicit_slot_type_compatible"], "explicit_slot_type_compatible", nullable=True)
    _boolean(destination["original_picker_called"], "original_picker_called")
    _ownership(destination["replacing_artifact"], expected_artifact=destination["replacing_artifact_id"],
               actor=result["played_character_id"], site=holy_site_id, permissions=permissions)
    window = permissions["window_context"]
    if destination["available"]:
        if (not window["available"] or not ownership["available"]
                or destination["selected_slot_index"] != window["selected_slot_index"]):
            raise ValueError("available native destination lacks the actual current site/slot/owner")
        if destination["action_kind"] == "remove":
            if (ownership["holy_site_owner_matches_requested"] is not True
                    or destination["effective_slot_index"] is not None or destination["replacing_artifact_id"] is not None
                    or destination["original_picker_called"] or destination["explicit_slot_type_compatible"] is not None):
                raise ValueError("native remove destination invented a replacement/picker")
        elif destination["action_kind"] == "enshrine":
            index = destination["effective_slot_index"]
            slots = permissions["site_inventory_slots"]
            if (ownership["holy_site_owner_matches_requested"] is not False or index is None
                    or not slots["available"] or index >= len(slots["slots"])
                    or slots["slots"][index]["artifact_id"] != destination["replacing_artifact_id"]):
                raise ValueError("native effective destination does not bind an actual same-site slot")
            if destination["explicit_slot_type_compatible"] is True:
                if destination["selected_slot_index"] != index or destination["original_picker_called"]:
                    raise ValueError("compatible explicit slot cannot silently become an automatic destination")
            elif not destination["original_picker_called"]:
                raise ValueError("fallback destination lacks its original native picker call")
        else:
            raise ValueError("available native destination has no observed action kind")
    _boolean(result["selected_artifact_matches_request"], "selected_artifact_matches_request")
    if result["available"] and result["selected_artifact_matches_request"] != (
            window["available"] and window["selected_artifact_id"] == artifact_id):
        raise ValueError("native selected-action text binding differs from actual current selection")
    texts = []
    for name in TEXT_FIELDS:
        text = _shape(result[name], name, ' '.join(TEXT_KEYS))
        if text["available"]:
            if (not isinstance(text["text"], str) or len(text["text"].encode('utf-8')) > 65536
                    or not result["selected_artifact_matches_request"]):
                raise ValueError("native action text lacks a matching actual current selection or valid UTF-8 bound")
        elif text["text"] is not None:
            raise ValueError("unavailable native action text must remain null, not empty")
        texts.append(text)
    _boolean(result["preview_identity_available"], "preview_identity_available")
    if result["preview_identity_available"]:
        digest = result["preview_identity_sha256"]
        if (not isinstance(digest, str) or re.fullmatch('[0-9a-f]{64}', digest) is None
                or not result["available"] or not result["selected_artifact_matches_request"]
                or not ownership["available"] or not destination["available"] or not all(text["available"] for text in texts)
                or not permissions["current_buttons"]["available"] or ownership["player_owned_reference_member"] is None
                or not ownership["player_equipped_slot_member"]["available"]
                or not ownership["site_equipped_slot_member"]["available"]
                or destination["replacing_artifact_id"] is not None and not destination["replacing_artifact"]["available"]):
            raise ValueError("native preview identity lacks its independently observed prerequisites")
        if hashlib.sha256(relic_action_preview_canonical_v1(result).encode('utf-8')).hexdigest() != digest:
            raise ValueError("native relic preview identity does not match its actual canonical components")
    elif result["preview_identity_sha256"] is not None:
        raise ValueError("unavailable native preview identity must remain null")
    return result


def query_player_holy_site_relic_action_context_private_v1(
    driver: object, *, expected_revision: int, holy_site_id: int, artifact_id: int,
) -> dict[str, object]:
    _ref(holy_site_id, "requested holy_site_id", nullable=False)
    _ref(artifact_id, "requested artifact_id", nullable=False)
    before, envelope = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"holy_site_id": holy_site_id, "artifact_id": artifact_id}, include_native_command_history=False)
    try:
        if (require_exact_native_backend(envelope.get("game_version"), envelope.get("executable_sha256"),
                envelope.get("backend_id"), suffix="player-holy-site-relic-action-context-v1") != CK3_12004
                or envelope.get("domain_key") != DOMAIN or envelope.get("snapshot_revision") != before.get("native_revision")
                or envelope.get("date_raw") != before.get("date_raw")):
            raise ValueError("native relic action context envelope differs from its build/frame")
        value = normalize_player_holy_site_relic_action_context_v1(envelope.get(RESULT_KEY), snapshot=before,
                                                holy_site_id=holy_site_id, artifact_id=artifact_id)
        if envelope.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native relic action context envelope lost root availability")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": envelope["snapshot_revision"], "backend_id": envelope["backend_id"],
            "domain_key": DOMAIN, "status": envelope["status"], "advertised": False}
