"""Exact-build, separately opted-in relic candidates and native permission reads."""
from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_holy_site_private_transport import _availability, _ref
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build

STEP = "query-player-holy-site-relic-permissions-v1"
PERMISSION = "allow_private_player_holy_site_relic_permissions_query"
DOMAIN = "player_holy_site_relic_permissions_v1"
RESULT_KEY = "player_holy_site_relic_permissions"


def _shape(value: object, field: str, keys: str, *, availability: bool = True) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError(f"native relic permissions component shape differs: {field}")
    return _availability(value, field) if availability else dict(value)


def _integer(value: object, field: str, *, nullable: bool = False,
             low: int = -(2**31), high: int = 2**31 - 1) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native relic permissions integer is malformed: {field}")
    return value


def _boolean(value: object, field: str, *, nullable: bool = False) -> bool | None:
    if value is None and nullable:
        return None
    if type(value) is not bool:
        raise ValueError(f"native relic permissions boolean is malformed: {field}")
    return value


def _array(value: object, field: str) -> list:
    if not isinstance(value, list) or len(value) > 8192:
        raise ValueError(f"native relic permissions array is malformed: {field}")
    return value


def _ids(value: object, field: str) -> list[int]:
    return [_ref(item, field, nullable=False) for item in _array(value, field)]


def _observed_bool(value: object, field: str) -> dict[str, object]:
    result = _shape(value, field, "available value unavailable_reason")
    _boolean(result["value"], field + ".value", nullable=not result["available"])
    if not result["available"] and result["value"] is not None:
        raise ValueError("unobserved permission cannot become an observed false")
    return result


def normalize_player_holy_site_relic_permissions_v1(
    value: object, *, snapshot: Mapping[str, object], holy_site_id: int,
    artifact_id: int | None,
) -> dict[str, object]:
    result = _shape(value, "relic permissions", """
        schema game_version executable_sha256 available unavailable_reason capture_epoch date_raw
        played_character_id player_faith_id requested_holy_site_id holy_site_id requested_artifact_id
        loaded_source_pins_verified site_inventory_slots window_context player_inventory
        current_candidates artifact_permissions current_buttons evaluation_context action_ready
        beneficiaries_observed beneficiaries read_only
    """)
    if (result["schema"] != "ck3_12004_player_holy_site_relic_permissions_v1"
            or require_exact_native_build(result["game_version"], result["executable_sha256"]) != CK3_12004
            or private_native_build_identity(snapshot) != CK3_12004):
        raise ValueError("native relic permissions requires exact 1.20.0.4")
    actor = snapshot.get("played_character")
    _integer(result["played_character_id"], "played_character_id", low=0, high=2**32 - 2)
    _integer(result["date_raw"], "date_raw")
    _integer(result["capture_epoch"], "capture_epoch", low=1, high=2**64 - 1)
    _ref(result["requested_holy_site_id"], "requested_holy_site_id", nullable=False)
    _ref(result["requested_artifact_id"], "requested_artifact_id")
    if (not isinstance(actor, Mapping)
            or result["played_character_id"] != actor.get("character_id")
            or result["date_raw"] != snapshot.get("date_raw")
            or result["requested_holy_site_id"] != holy_site_id
            or result["requested_artifact_id"] != artifact_id):
        raise ValueError("native relic permissions crossed its player/frame/request")
    _ref(result["player_faith_id"], "player_faith_id")
    _ref(result["holy_site_id"], "holy_site_id")
    if (result["available"] and result["holy_site_id"] != holy_site_id
            or result["holy_site_id"] not in (None, holy_site_id)):
        raise ValueError("native relic permissions changed its target full reference")
    _boolean(result["loaded_source_pins_verified"], "loaded_source_pins_verified")
    if (result["action_ready"] is not False or result["beneficiaries_observed"] is not False
            or result["beneficiaries"] is not None or result["read_only"] is not True):
        raise ValueError("native relic permissions invented action readiness or benefits")

    evaluation = _shape(result["evaluation_context"], "evaluation_context", """
        native_getter_calls getter_backend owner_thread_requirement gameplay_command_submitted
        world_cache_written window_selection_written window_candidate_cache_written
        script_evaluation_allocates_and_uses_tls inventory_getter_may_initialize_static_context
        script_rng_effects_verified script_rng_effects
    """, availability=False)
    _integer(evaluation["native_getter_calls"], "native_getter_calls", low=0, high=2**32 - 1)
    if (evaluation["getter_backend"] not in {
            "source_bound_native_getter", "owned_fixture_injected_getter", "unavailable"}
            or evaluation["owner_thread_requirement"] != "existing_religion_owner_callback"
            or any(evaluation[name] is not False for name in (
                "gameplay_command_submitted", "world_cache_written", "window_selection_written",
                "window_candidate_cache_written", "script_rng_effects_verified"))
            or evaluation["script_evaluation_allocates_and_uses_tls"] is not True
            or evaluation["inventory_getter_may_initialize_static_context"] is not True
            or evaluation["script_rng_effects"] != "unknown"
            or evaluation["getter_backend"] == "source_bound_native_getter"
                and result["loaded_source_pins_verified"] is not True):
        raise ValueError("native relic permissions lost its evaluation/source boundaries")

    slots = _shape(result["site_inventory_slots"], "site_inventory_slots", "available slots unavailable_reason")
    if slots["available"]:
        for index, raw in enumerate(_array(slots["slots"], "site slots")):
            slot = _shape(raw, "site slot", "slot_index artifact_id", availability=False)
            if _integer(slot["slot_index"], "slot_index", low=0, high=2**32 - 1) != index:
                raise ValueError("native relic permissions changed native site slot order")
            _ref(slot["artifact_id"], "site slot artifact_id")
    elif slots["slots"] is not None:
        raise ValueError("unavailable site slots must remain null")

    window = _shape(result["window_context"], "window_context", """
        available root_present selected_holy_site_id selected_artifact_id slot_mode
        selected_slot_index selected_slot_artifact_id cached_candidates unavailable_reason
    """)
    _boolean(window["root_present"], "window root_present", nullable=not window["available"])
    for name in ("selected_holy_site_id", "selected_artifact_id", "selected_slot_artifact_id"):
        _ref(window[name], name)
    _integer(window["selected_slot_index"], "selected_slot_index", nullable=True, low=0, high=8191)
    if window["slot_mode"] not in {"unknown", "native_automatic", "explicit_inventory_slot"}:
        raise ValueError("native relic permissions slot context is malformed")
    if window["available"]:
        if (window["root_present"] is not True or window["selected_holy_site_id"] != holy_site_id
                or window["slot_mode"] == "unknown"):
            raise ValueError("available relic window does not identify this site and root")
        if window["slot_mode"] == "explicit_inventory_slot":
            index = window["selected_slot_index"]
            if (not slots["available"] or index is None or index >= len(slots["slots"])
                    or slots["slots"][index]["artifact_id"] != window["selected_slot_artifact_id"]):
                raise ValueError("explicit relic slot is not an observed row of this same site")
    if window["slot_mode"] != "explicit_inventory_slot" and (
            window["selected_slot_index"] is not None or window["selected_slot_artifact_id"] is not None):
        raise ValueError("native automatic/unknown slot cannot invent an explicit slot")
    cache = _shape(window["cached_candidates"], "cached_candidates", """
        available artifact_ids refresh_time_known producer_invoked unavailable_reason
    """)
    if cache["refresh_time_known"] is not False or cache["producer_invoked"] is not False:
        raise ValueError("cached window candidates cannot claim refresh or producer execution")
    if cache["available"]:
        _ids(cache["artifact_ids"], "cached candidate artifact_id")
        if not window["available"]:
            raise ValueError("candidate cache lacks same-site current window context")
    elif cache["artifact_ids"] is not None:
        raise ValueError("unavailable cached candidates must remain null")

    inventory = _shape(result["player_inventory"], "player_inventory", """
        available artifact_ids native_character_owner_id native_holy_site_owner_id
        owner_matches_player unavailable_reason
    """)
    for name in ("native_character_owner_id", "native_holy_site_owner_id"):
        _ref(inventory[name], name)
    _boolean(inventory["owner_matches_player"], "owner_matches_player", nullable=True)
    if inventory["owner_matches_player"] is True and inventory["native_character_owner_id"] != result["played_character_id"]:
        raise ValueError("relic inventory claims another character as current player")
    if inventory["available"]:
        _ids(inventory["artifact_ids"], "player inventory artifact_id")
    elif inventory["artifact_ids"] is not None:
        raise ValueError("unavailable player inventory cannot become an empty collection")

    candidates = _shape(result["current_candidates"], "current_candidates", """
        available artifact_ids evaluations method producer_invoked unavailable_reason
    """)
    if (candidates["method"] != "original_native_candidate_predicate_over_current_player_inventory"
            or candidates["producer_invoked"] is not False):
        raise ValueError("current candidate query cannot rebuild the native window cache")
    if inventory["available"]:
        rows = _array(candidates["evaluations"], "candidate evaluations")
        if [row.get("artifact_id") if isinstance(row, dict) else None for row in rows] != inventory["artifact_ids"]:
            raise ValueError("native candidate evaluations changed raw inventory order or duplicates")
        known = True
        expected_ids = []
        for raw in rows:
            row = _shape(raw, "candidate evaluation", """
                artifact_id object_resolved available predicate_called can_be_candidate unavailable_reason
            """)
            _ref(row["artifact_id"], "candidate evaluation artifact_id", nullable=False)
            for name in ("object_resolved", "predicate_called"):
                _boolean(row[name], name)
            _boolean(row["can_be_candidate"], "can_be_candidate", nullable=not row["available"])
            if row["available"]:
                if not row["object_resolved"] or not row["predicate_called"]:
                    raise ValueError("known candidate has no resolved original predicate evaluation")
                if row["can_be_candidate"]:
                    expected_ids.append(row["artifact_id"])
            else:
                known = False
                if row["can_be_candidate"] is not None:
                    raise ValueError("unknown candidate cannot become false")
                if not row["object_resolved"] and row["predicate_called"]:
                    raise ValueError("unresolved artifact cannot have a native predicate invocation")
        if candidates["available"] != known:
            raise ValueError("partial candidate evaluation cannot claim a complete candidate list")
        if known:
            if _ids(candidates["artifact_ids"], "current candidate artifact_id") != expected_ids:
                raise ValueError("native current candidates differ from ordered original predicate results")
        elif candidates["artifact_ids"] is not None:
            raise ValueError("unknown candidate membership must keep final candidate list null")
    elif candidates["available"] or candidates["evaluations"] is not None or candidates["artifact_ids"] is not None:
        raise ValueError("current candidates lack an actually observed player inventory")

    permissions = _shape(result["artifact_permissions"], "artifact_permissions", """
        available object_resolved artifact_id native_holy_site_owner_id rarity_level
        player_inventory_contains_reference can_enshrine can_remove slot_context unavailable_reason
    """)
    _boolean(permissions["object_resolved"], "artifact object_resolved")
    for name in ("artifact_id", "native_holy_site_owner_id"):
        _ref(permissions[name], name)
    # Resolving an object does not itself prove its optional rarity field read.
    _integer(permissions["rarity_level"], "rarity_level", nullable=True)
    _boolean(permissions["player_inventory_contains_reference"], "player_inventory_contains_reference", nullable=True)
    if permissions["slot_context"] != "current_holy_site_window" or permissions["artifact_id"] != artifact_id:
        raise ValueError("explicit relic permission crossed its requested artifact/window semantics")
    if not permissions["object_resolved"] and any(permissions[name] is not None for name in ("rarity_level", "native_holy_site_owner_id")):
        raise ValueError("unresolved artifact permissions contain invented object fields")
    if artifact_id is None and (permissions["available"] or permissions["object_resolved"]
                               or permissions["unavailable_reason"] != "artifact_id_not_requested"):
        raise ValueError("unspecified artifact permissions must remain explicitly unrequested")
    if inventory["available"] and artifact_id is not None:
        if permissions["player_inventory_contains_reference"] != (artifact_id in inventory["artifact_ids"]):
            raise ValueError("relic inventory membership differs from actual raw inventory")
    elif permissions["player_inventory_contains_reference"] is not None:
        raise ValueError("unobserved relic inventory membership must remain null")
    explicit_flags = [_observed_bool(permissions[name], "artifact " + name) for name in ("can_enshrine", "can_remove")]
    if permissions["available"] and (not permissions["object_resolved"] or not window["available"]
                                       or not all(flag["available"] for flag in explicit_flags)):
        raise ValueError("available explicit permissions lack current native window/observations")

    buttons = _shape(result["current_buttons"], "current_buttons", """
        available selected_artifact_id context_matches_requested_artifact can_enshrine can_remove unavailable_reason
    """)
    _ref(buttons["selected_artifact_id"], "button selected_artifact_id")
    _boolean(buttons["context_matches_requested_artifact"], "context_matches_requested_artifact", nullable=True)
    expected_match = (buttons["selected_artifact_id"] == artifact_id
                      if artifact_id is not None and window["available"] else None)
    if buttons["context_matches_requested_artifact"] != expected_match:
        raise ValueError("current-button requested-artifact comparison differs from actual selection")
    button_flags = [_observed_bool(buttons[name], "button " + name) for name in ("can_enshrine", "can_remove")]
    if buttons["available"] and (not window["available"]
            or buttons["selected_artifact_id"] != window["selected_artifact_id"]
            or not all(flag["available"] for flag in button_flags)):
        raise ValueError("current-button permissions lost actual current selection/observations")
    if any(flag["available"] for flag in explicit_flags + button_flags) and not window["available"]:
        raise ValueError("native permission observation lacks a verified same-site window")
    return result


def query_player_holy_site_relic_permissions_private_v1(
    driver: object, *, expected_revision: int, holy_site_id: int,
    artifact_id: int | None = None,
) -> dict[str, object]:
    _ref(holy_site_id, "requested holy_site_id", nullable=False)
    _ref(artifact_id, "requested artifact_id")
    fields = {"holy_site_id": holy_site_id}
    if artifact_id is not None:
        fields["artifact_id"] = artifact_id
    before, envelope = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields=fields, include_native_command_history=False)
    try:
        if (require_exact_native_backend(envelope.get("game_version"), envelope.get("executable_sha256"),
                envelope.get("backend_id"), suffix="player-holy-site-relic-permissions-v1") != CK3_12004
                or envelope.get("domain_key") != DOMAIN
                or envelope.get("snapshot_revision") != before.get("native_revision")
                or envelope.get("date_raw") != before.get("date_raw")):
            raise ValueError("native relic permissions envelope differs from its build/frame")
        value = normalize_player_holy_site_relic_permissions_v1(
            envelope.get(RESULT_KEY), snapshot=before, holy_site_id=holy_site_id, artifact_id=artifact_id)
        if envelope.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native relic permissions envelope lost root availability")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": envelope["snapshot_revision"], "backend_id": envelope["backend_id"],
            "domain_key": DOMAIN, "status": envelope["status"], "advertised": False}
