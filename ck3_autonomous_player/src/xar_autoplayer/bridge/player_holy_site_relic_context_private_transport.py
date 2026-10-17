"""Independent exact-build relic read; no existing HolySite DTO is expanded."""

from __future__ import annotations

from collections.abc import Mapping

from .driver import BridgeUnavailableError
from .g2_private_query_transport import private_g2_query_metadata_v1, read_private_g2_native_query_v1
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .player_holy_site_private_transport import _availability, _ref
from .version_identity import CK3_12004, require_exact_native_backend, require_exact_native_build


STEP = "query-player-holy-site-relic-context-v1"
PERMISSION = "allow_private_player_holy_site_relic_context_query"
DOMAIN = "player_holy_site_relic_context_v1"
RESULT_KEY = "player_holy_site_relic_context"


def _integer(value: object, field: str, *, nullable: bool = False,
             low: int = -(2**31), high: int = 2**31 - 1) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"native relic integer is malformed: {field}")
    return value


def _boolean(value: object, field: str, *, nullable: bool = False) -> bool | None:
    if value is None and nullable:
        return None
    if type(value) is not bool:
        raise ValueError(f"native relic boolean is malformed: {field}")
    return value


def _array(value: object, field: str, *, limit: int = 8192) -> list:
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"native relic collection is malformed: {field}")
    return value


def _unobserved_fields(component: Mapping[str, object], fields: tuple[str, ...]) -> None:
    if not component["available"] and any(component.get(name) is not None for name in fields):
        raise ValueError("unavailable native relic component contains an invented observed value")


def _recognition(value: object, field: str, faith_id: int | None) -> dict[str, object]:
    result = _availability(value, field)
    _ref(result.get("faith_id"), field + ".faith_id")
    if result["available"]:
        if result.get("faith_id") != faith_id or faith_id is None:
            raise ValueError("native relic recognition crossed its faith identity")
        _boolean(result.get("value"), field + ".value")
    elif result.get("value") is not None:
        raise ValueError("unavailable recognition is not an observed false")
    return result


def normalize_player_holy_site_relic_context_v1(
    value: object, *, snapshot: Mapping[str, object], holy_site_id: int,
) -> dict[str, object]:
    result = _availability(value, "relic context")
    if (result.get("schema") != "ck3_12004_player_holy_site_relic_context_v1"
            or require_exact_native_build(result.get("game_version"), result.get("executable_sha256")) != CK3_12004
            or private_native_build_identity(snapshot) != CK3_12004):
        raise ValueError("native relic context requires exact 1.20.0.4")
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or result.get("played_character_id") != actor.get("character_id")
            or result.get("date_raw") != snapshot.get("date_raw")
            or type(result.get("capture_epoch")) is not int or result["capture_epoch"] <= 0
            or result.get("requested_holy_site_id") != holy_site_id):
        raise ValueError("native relic context crossed its player/frame/request")
    for name in ("player_rite_id", "player_faith_id", "holy_site_id"):
        _ref(result.get(name), name)
    if result["available"] and result.get("holy_site_id") != holy_site_id:
        raise ValueError("native relic context changed its target full reference")
    if result.get("holy_site_id") not in (None, holy_site_id):
        raise ValueError("native relic context returned a different target full reference")

    evaluation = result.get("evaluation_context")
    if not isinstance(evaluation, dict):
        raise ValueError("native relic evaluation disclosure is missing")
    _integer(evaluation.get("native_getter_calls"), "native_getter_calls", low=0, high=2**32 - 1)
    if (evaluation.get("getter_backend") not in {
            "source_bound_native_getter", "owned_fixture_injected_getter", "unavailable"}
            or evaluation.get("owner_thread_requirement") != "existing_religion_owner_callback"
            or evaluation.get("gameplay_command_submitted") is not False
            or evaluation.get("world_cache_written") is not False
            or evaluation.get("script_evaluation_allocates_and_uses_tls") is not True
            or evaluation.get("script_rng_effects_verified") is not False
            or evaluation.get("script_rng_effects") != "unknown"):
        raise ValueError("native relic query lost its evaluation boundaries")
    for name in ("beneficiaries_observed", "can_enshrine_observed", "window_candidates_observed"):
        if result.get(name) is not False:
            raise ValueError("native relic query claimed unimplemented semantics")
    if result.get("beneficiaries") is not None or result.get("can_enshrine") is not None:
        raise ValueError("unobserved native relic semantics must remain null")
    if result.get("read_only") is not True:
        raise ValueError("native relic context lost read-only identity")

    _boolean(result.get("associated_faith_ids_available"), "associated_faith_ids_available")
    if result["associated_faith_ids_available"]:
        faiths = _array(result.get("associated_faith_ids"), "associated_faith_ids")
        for faith in faiths:
            _ref(faith, "associated_faith_id", nullable=False)
    elif result.get("associated_faith_ids") is not None:
        raise ValueError("unavailable associated faiths must not become an empty array")

    # Root availability identifies the site; each child carries independent
    # availability. Do not promote partial observations to a complete business result.
    cached = _availability(result.get("cached_world_state"), "cached_world_state")
    for name in ("refresh_time_known", "world_effects_applied_observed"):
        if cached.get(name) is not False:
            raise ValueError("cached native fields cannot prove refresh time or applied modifiers")
    if cached["available"]:
        _boolean(cached.get("is_active"), "cached is_active")
        _integer(cached.get("total_active_artifact_rarity"), "cached rarity")
    _unobserved_fields(cached, ("is_active", "total_active_artifact_rarity"))

    county = _availability(result.get("county_context"), "county_context")
    county_fields = ("barony_title_id", "county_title_id", "county_holder_id",
                     "county_holder_rite_id", "county_holder_faith_id")
    for name in county_fields:
        _ref(county.get(name), name, nullable=not county["available"])
    # Native county reads can stop after resolving the barony/county/holder.
    # Preserve those source identities while later Rite/Faith reads are missing.

    inventory = _availability(result.get("inventory"), "inventory")
    _unobserved_fields(inventory, ("artifact_ids", "slots", "artifact_objects"))
    if inventory["available"]:
        ids = _array(inventory.get("artifact_ids"), "artifact_ids")
        for artifact_id in ids:
            _ref(artifact_id, "inventory artifact_id", nullable=False)
        slots = _array(inventory.get("slots"), "slots")
        slot_ids = []
        for expected_index, slot in enumerate(slots):
            if not isinstance(slot, dict):
                raise ValueError("native relic slot is malformed")
            if _integer(slot.get("slot_index"), "slot_index", low=0, high=2**32 - 1) != expected_index:
                raise ValueError("native relic slots lost their original sequential indices")
            slot_ids.append(_ref(slot.get("artifact_id"), "slot artifact_id"))
        objects = _array(inventory.get("artifact_objects"), "artifact_objects", limit=16384)
        expected = list(dict.fromkeys(ids + [item for item in slot_ids if item is not None]))
        if [item.get("artifact_id") if isinstance(item, dict) else None for item in objects] != expected:
            raise ValueError("native relic object union lost raw collection order/identities")
        for item in objects:
            obj = _availability(item, "artifact_object")
            _ref(obj.get("artifact_id"), "artifact_object.artifact_id", nullable=False)
            _integer(obj.get("rarity_level"), "rarity_level", nullable=not obj["available"])
            _ref(obj.get("native_holy_site_owner_id"), "native_holy_site_owner_id")
            _unobserved_fields(obj, ("rarity_level", "native_holy_site_owner_id"))
            _boolean(obj.get("sanctified_faith_ids_available"), "sanctified_faith_ids_available")
            if obj["sanctified_faith_ids_available"]:
                for faith in _array(obj.get("sanctified_faith_ids"), "sanctified_faith_ids"):
                    _ref(faith, "sanctified_faith_id", nullable=False)
            elif obj.get("sanctified_faith_ids") is not None:
                raise ValueError("unavailable sanctification collection must remain null")
            if (obj.get("template_trigger_evaluated_separately") is not False
                    or obj.get("recognition_semantics") != "native_dynamic_sanctification_or_template_trigger"):
                raise ValueError("combined native recognition cannot prove a separately evaluated template branch")
            _recognition(obj.get("recognition_for_player_faith"), "player recognition", result.get("player_faith_id"))
            _recognition(obj.get("recognition_for_county_holder_faith"), "holder recognition", county.get("county_holder_faith_id"))

    current = _availability(result.get("current_relic_evaluation"), "current_relic_evaluation")
    current_fields = ("active_artifact_rarity_sum", "is_active", "cache_evaluation_disagreement")
    if current.get("method") != "original_native_rarity_producer":
        raise ValueError("native relic current evaluation method is malformed")
    _unobserved_fields(current, current_fields)
    _integer(current.get("inventory_artifact_count_raw"), "inventory_artifact_count_raw",
             nullable=not current["available"], low=0, high=8192)
    _boolean(current.get("county_holder_faith_associated"), "county_holder_faith_associated", nullable=True)
    if current["available"]:
        _integer(current.get("active_artifact_rarity_sum"), "active_artifact_rarity_sum")
        _boolean(current.get("is_active"), "current is_active")
        disagreement = _boolean(current.get("cache_evaluation_disagreement"), "cache_evaluation_disagreement", nullable=not cached["available"])
        if not cached["available"] and disagreement is not None:
            raise ValueError("comparison with unavailable cached state must remain null")
    return result


def query_player_holy_site_relic_context_private_v1(
    driver: object, *, expected_revision: int, holy_site_id: int,
) -> dict[str, object]:
    _ref(holy_site_id, "requested holy_site_id", nullable=False)
    before, envelope = read_private_g2_native_query_v1(
        driver, permission=PERMISSION, step=STEP, expected_revision=expected_revision,
        request_fields={"holy_site_id": holy_site_id}, include_native_command_history=False)
    try:
        if (require_exact_native_backend(envelope.get("game_version"), envelope.get("executable_sha256"),
                envelope.get("backend_id"), suffix="player-holy-site-relic-context-v1") != CK3_12004
                or envelope.get("domain_key") != DOMAIN
                or envelope.get("snapshot_revision") != before.get("native_revision")
                or envelope.get("date_raw") != before.get("date_raw")):
            raise ValueError("native relic context envelope differs from its build/frame")
        value = normalize_player_holy_site_relic_context_v1(
            envelope.get(RESULT_KEY), snapshot=before, holy_site_id=holy_site_id)
        if envelope.get("status") != ("observed" if value["available"] else "unavailable"):
            raise ValueError("native relic context envelope lost availability")
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**value, **private_native_provenance(before), **private_g2_query_metadata_v1(before),
            "snapshot_revision": envelope["snapshot_revision"], "backend_id": envelope["backend_id"],
            "domain_key": DOMAIN, "status": envelope["status"], "advertised": False}
