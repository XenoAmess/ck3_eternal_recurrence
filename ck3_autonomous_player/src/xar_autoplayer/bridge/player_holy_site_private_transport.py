"""Exact .4 HolySite model reads through the existing religion owner mailbox."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build


STEP = "query-player-holy-site-v1"
PERMISSION = "allow_private_player_holy_site_query"


def _ref(value: object, field: str, *, nullable: bool = True) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or not 0 <= value < 0xFFFFFFFF:
        raise ValueError(f"native HolySite full reference is malformed: {field}")
    return value


def _availability(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or type(value.get("available")) is not bool:
        raise ValueError(f"native HolySite availability is malformed: {field}")
    reason = value.get("unavailable_reason")
    if value["available"]:
        if reason is not None:
            raise ValueError(f"native HolySite observed component has failure reason: {field}")
    elif not isinstance(reason, str) or not reason:
        raise ValueError(f"native HolySite unavailable component lacks reason: {field}")
    return dict(value)


def _ids(value: object, field: str) -> list[int]:
    if not isinstance(value, list) or len(value) > 8192:
        raise ValueError(f"native HolySite ID array is malformed: {field}")
    return [_ref(item, field, nullable=False) for item in value]


def _site(value: object) -> dict[str, object]:
    site = _availability(value, "site")
    site_id = _ref(site.get("holy_site_id"), "holy_site_id", nullable=False)
    key = site.get("type_key")
    if key is not None and (not isinstance(key, str) or not key or len(key) > 1024):
        raise ValueError("native HolySite type key is malformed")
    _ref(site.get("barony_title_id"), "barony_title_id")
    faiths = site.get("associated_faiths")
    if not isinstance(faiths, list) or len(faiths) > 8192:
        raise ValueError("native HolySite Faith relations are malformed")
    rows = []
    for raw in faiths:
        relation = _availability(raw, "faith relation")
        _ref(relation.get("faith_id"), "faith_id", nullable=False)
        for name in ("faith_lists_site", "eminent"):
            actual = relation.get(name)
            if relation["available"]:
                if type(actual) is not bool:
                    raise ValueError(f"native observed Faith membership is malformed: {name}")
            elif actual is not None:
                raise ValueError("unavailable Faith membership is not observed false")
        rows.append(relation)
    inventory = _availability(site.get("inventory"), "inventory")
    if (inventory.get("identity_kind") != "embedded_holy_site_inventory"
            or inventory.get("owner_kind") != "holy_site"
            or inventory.get("owner_holy_site_id") != site_id
            or inventory.get("artifact_objects_resolved") is not False):
        raise ValueError("native HolySite embedded inventory identity differs from its site")
    for name in ("native_holy_site_owner_id", "native_character_owner_id"):
        _ref(inventory.get(name), name)
    if inventory["available"]:
        inventory["artifact_ids"] = _ids(inventory.get("artifact_ids"), "artifact_ids")
    elif inventory.get("artifact_ids") is not None:
        raise ValueError("unavailable inventory has an invented empty artifact array")
    if site["available"] and (key is None or not inventory["available"]):
        raise ValueError("available HolySite lacks its type/inventory read")
    return {**site, "associated_faiths": rows, "inventory": inventory}


def normalize_player_holy_site_v1(value: object, *, snapshot: Mapping[str, object],
                                  requested_holy_site_id: int | None) -> dict[str, object]:
    result = _availability(value, "snapshot")
    if (result.get("schema") != "ck3_12004_player_holy_site_v1"
            or require_exact_native_build(result.get("game_version"), result.get("executable_sha256")) != CK3_12004
            or private_native_build_identity(snapshot) != CK3_12004):
        raise ValueError("native HolySite query requires exact 1.20.0.4")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping) or result.get("played_character_id") != actor.get("character_id")
            or result.get("date_raw") != snapshot.get("date_raw")
            or type(result.get("capture_epoch")) is not int or result["capture_epoch"] <= 0
            or result.get("requested_holy_site_id") != requested_holy_site_id):
        raise ValueError("native HolySite query crossed its player/frame/request")
    for name in ("player_rite_id", "player_faith_id"):
        _ref(result.get(name), name)
    # An unavailable owner capture has no observed inner collections. Keep its
    # native diagnostic, rather than recasting an unattempted child as malformed.
    if not result["available"]:
        return {**result, "current_faith_holy_site_ids": None, "current_faith_sites": None,
                "window_model": None, "selected_holy_site": None, "loaded_registry_roster": None}
    ids = _ids(result.get("current_faith_holy_site_ids"), "current_faith_holy_site_ids")
    raw_sites = result.get("current_faith_sites")
    if not isinstance(raw_sites, list) or len(raw_sites) != len(ids):
        raise ValueError("native HolySite current-Faith sites omit source rows")
    sites = [_site(site) for site in raw_sites]
    if [site["holy_site_id"] for site in sites] != ids:
        raise ValueError("native HolySite current-Faith order/identities changed")
    window = _availability(result.get("window_model"), "registered window model")
    for name in ("holy_site_id", "holy_site_item_raw"):
        _ref(window.get(name), name)
    for name in ("present", "root_present"):
        actual = window.get(name)
        if (window["available"] and type(actual) is not bool) or (not window["available"] and actual is not None):
            raise ValueError("native HolySite window model availability is malformed")
    if window.get("rendered_visibility_observed") is not False:
        raise ValueError("registered HolySite model does not prove rendered visibility")
    selected = result.get("selected_holy_site")
    selected_id = requested_holy_site_id if requested_holy_site_id is not None else window["holy_site_id"]
    if (selected is None) != (selected_id is None):
        raise ValueError("native HolySite selected source identity is absent")
    if selected is not None:
        selected = _site(selected)
        if selected["holy_site_id"] != selected_id:
            raise ValueError("native HolySite selected full reference changed")
    source = "explicit_full_reference" if requested_holy_site_id is not None else "registered_window_model"
    if result.get("selection_source") != source:
        raise ValueError("native HolySite selection source differs from request")
    roster = result.get("loaded_registry_roster")
    if (not isinstance(roster, list) or len(roster) > 8192
            or type(result.get("loaded_registry_roster_available")) is not bool
            or result.get("registry_roster_is_native_adoption_candidates") is not False):
        raise ValueError("native HolySite loaded registry is not an adoption-candidate result")
    for name in ("loaded_registry_slot_count", "loaded_registry_unreadable_slots"):
        if type(result.get(name)) is not int or not 0 <= result[name] <= 8192:
            raise ValueError("native HolySite registry count is malformed")
    if len(roster) + result["loaded_registry_unreadable_slots"] > result["loaded_registry_slot_count"]:
        raise ValueError("native HolySite registry rows exceed source slots")
    roster_rows = []
    for raw in roster:
        if not isinstance(raw, dict):
            raise ValueError("native HolySite registry entry is malformed")
        _ref(raw.get("holy_site_id"), "roster holy_site_id", nullable=False)
        _ref(raw.get("barony_title_id"), "roster barony_title_id")
        if not isinstance(raw.get("type_key"), str) or not raw["type_key"]:
            raise ValueError("native HolySite registry entry lacks type")
        roster_rows.append(dict(raw))
    for name in ("active_state_observed", "relic_recognition_observed", "beneficiaries_observed", "adoption_legality_observed"):
        if result.get(name) is not False:
            raise ValueError("HolySite identity/collection observation cannot grant unimplemented semantics")
    if result.get("read_only") is not True:
        raise ValueError("native HolySite query lost read-only identity")
    return {**result, "current_faith_holy_site_ids": ids, "current_faith_sites": sites,
            "window_model": window, "selected_holy_site": selected, "loaded_registry_roster": roster_rows}


def query_player_holy_site_private_v1(driver: object, *, expected_revision: int,
                                    holy_site_id: int | None = None) -> dict[str, object]:
    _ref(holy_site_id, "requested holy_site_id")
    fields = {} if holy_site_id is None else {"holy_site_id": holy_site_id}
    before, envelope = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields=fields, include_native_command_history=False)
    try:
        if (require_exact_native_backend(envelope.get("game_version"), envelope.get("executable_sha256"),
                envelope.get("backend_id"), suffix="player-holy-site-v1") != CK3_12004
                or envelope.get("domain_key") != "player_holy_site_v1"
                or envelope.get("snapshot_revision") != before.get("native_revision")
                or envelope.get("date_raw") != before.get("date_raw")):
            raise ValueError("native HolySite envelope differs from its exact build/frame")
        value = normalize_player_holy_site_v1(envelope.get("player_holy_site"),
            snapshot=before, requested_holy_site_id=holy_site_id)
        if envelope.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native HolySite envelope lost source availability")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": envelope["snapshot_revision"], "backend_id": envelope["backend_id"],
            "domain_key": "player_holy_site_v1", "status": envelope["status"], "advertised": False}
