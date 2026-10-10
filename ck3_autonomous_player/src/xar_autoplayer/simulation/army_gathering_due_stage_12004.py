"""Actual4 early gathering stage: complete nonpositive/all-combat returns.

This pure leaf preserves an explicit predecessor frame. Noncombat lifecycle and
refresh calls remain source boundaries; it never supplies their postimages.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
ENTRY_KIND = "explicit_post_cleanup_before_gathering_due_12004"
RETURN_KIND = "conditional_post_gathering_before_regular_core_12004"
COMBAT_MAGIC = 0x436F6D62


def _token(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("physical/frame identity is missing")
    return value


def _s32(value: object) -> int:
    if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
        raise ValueError("signed native DWORD is malformed")
    return value


def _u32(value: object) -> int:
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError("unsigned native DWORD is malformed")
    return value


def _resolve(raw: int, registry: object, objects: object) -> tuple[str, bool]:
    """Native low24 slot test, exact generation DWORD, then physical fallback."""
    if not isinstance(registry, Mapping) or not isinstance(objects, Mapping):
        raise LookupError("physical_registry_snapshot")
    fallback = _token(registry.get("fallback_token"))
    if not isinstance(objects.get(fallback), Mapping):
        raise LookupError("materialized_physical_fallback")
    present = registry.get("present")
    if type(present) is not bool:
        raise ValueError("registry presence is malformed")
    if present:
        limit = _u32(registry.get("slot_limit"))
        index = raw & 0xFFFFFF
        if index < limit:
            slots = registry.get("slots")
            if not isinstance(slots, Mapping) or str(index) not in slots:
                raise LookupError("reached_registry_slot")
            token = slots[str(index)]
            if token is not None:
                token = _token(token)
                item = objects.get(token)
                if not isinstance(item, Mapping):
                    raise LookupError("reached_physical_receiver")
                if _s32(item.get("full_id")) == raw:
                    return token, False
    return fallback, True


def project_army_gathering_due_stage_12004(stage: Mapping[str, object]) -> dict:
    result = {
        "projection_kind": RETURN_KIND, "status": "unavailable",
        "source_contract_game_version": "1.20.0.4",
        "complete_returned_frame": False, "actual_post_stage_observed": False,
        "actual_native_stage_executed": False, "full_daily_monthly_ready": False,
        "queue_occurrences": [], "direct_write_effects": [],
        "returned_state": None, "missing_inputs": [],
        "next_native_producer_entrances": [],
    }
    if stage.get("game_version") != "1.20.0.4" or stage.get("exe_sha256") != EXE_SHA256:
        raise ValueError("gathering stage requires the exact actual4 build pin")
    if stage.get("entry_kind") != ENTRY_KIND:
        raise ValueError("gathering stage requires its explicit caller entry")
    frame = _token(stage.get("entry_frame_id"))
    manager = _token(stage.get("manager_identity"))
    capture = _token(stage.get("capture_identity"))
    prior = stage.get("prior_stage_receipt")
    if not isinstance(prior, Mapping) or prior.get("complete_returned_frame") is not True:
        result["missing_inputs"] = ["complete_preceding_cleanup_returned_frame"]
        return result
    if any(prior.get(key) != value for key, value in (
        ("returned_frame_id", frame), ("manager_identity", manager),
        ("capture_identity", capture),
    )):
        raise ValueError("predecessor returned frame identity disagrees")
    state = stage.get("entry_state")
    if not isinstance(state, Mapping) or stage.get("entry_state_complete") is not True:
        result["missing_inputs"] = ["complete_explicit_entry_physical_state"]
        return result
    queue = state.get("primary_queue_158")
    if not isinstance(queue, Mapping) or queue.get("physical_token") != manager:
        raise ValueError("primary158 queue is bound to another manager")
    ids = queue.get("backing_ids")
    if not isinstance(ids, list):
        raise ValueError("queue backing IDs are missing")
    for raw in ids:
        _s32(raw)
    raw_count = queue.get("signed_count")
    normalized_nonpositive = raw_count is None and queue.get("count_basis") == "native_reader_nonpositive"
    if normalized_nonpositive:
        # CallerIdList(Load<signed DWORD>(descriptor,+C)<=0) returns empty.
        # The reader loses zero/negative distinction. Do not reconstruct it.
        if queue.get("normalized_visible_ids") != [] or queue.get("reader_available") is not True:
            raise ValueError("normalized nonpositive source is inconsistent")
        count = None
    else:
        count = _s32(raw_count)
    if count is not None and count > 0:
        if len(ids) < count:
            result["missing_inputs"] = ["all_original_primary158_queue_occurrences"]
            return result
        armies, combats = state.get("army_objects"), state.get("combat_objects")
        try:
            for index, raw in enumerate(ids[:count]):
                army_token, army_fallback = _resolve(raw, state.get("army_registry"), armies)
                army = armies[army_token]
                combat_raw = _s32(army.get("combat_full_id"))
                combat_token, combat_fallback = _resolve(combat_raw, state.get("combat_registry"), combats)
                combat = combats[combat_token]
                valid = _u32(combat.get("magic")) == COMBAT_MAGIC and _s32(combat.get("full_id")) != -1
                result["queue_occurrences"].append({
                    "stored_index": index, "raw_full_id": raw,
                    "army_physical_token": army_token, "army_used_fallback": army_fallback,
                    "combat_raw_full_id": combat_raw, "combat_physical_token": combat_token,
                    "combat_used_fallback": combat_fallback, "valid_native_combat": valid,
                })
                if not valid:
                    result["status"] = "partial"
                    result["missing_inputs"] = ["noncombat_gathering_lifecycle_and_refresh_postimage"]
                    result["next_native_producer_entrances"] = [
                        "2A9B010: resolve Unit/owner and reverse Army50 records",
                        "2A9AB80: bind due physical chunk and optional create/append ArRg",
                        "2633ED0 -> 28B2710: associate Character and placement lifecycle",
                        "24E8100 -> 2633320/24E1190: ArRg cache and Army130..17F statistics",
                    ]
                    return result
        except LookupError as missing:
            result["missing_inputs"] = [str(missing.args[0])]
            return result
    returned = deepcopy(dict(state))
    returned["primary_queue_158"]["signed_count"] = 0
    returned["primary_queue_158"]["count_basis"] = "derived_actual4_return"
    store = None if normalized_nonpositive else count != 0
    if store is not False:
        result["direct_write_effects"] = [{
            "physical_token": manager, "offset": 0x164, "size": 4,
            "value": 0, "store_executed": store,
            "source": "2A9B55F TEST initial/live EAX; 2A9B563 primary164=0",
        }]
    prior_writes = stage.get("prior_physical_writes")
    if not isinstance(prior_writes, list):
        raise ValueError("complete preceding physical write sequence is missing")
    result.update({
        "status": "ready", "complete_returned_frame": True,
        "returned_state": returned, "returned_frame_id": frame + ":gathering-return",
        "manager_identity": manager, "capture_identity": capture,
        "entry_frame_id": frame, "entry_count_exact": count,
        "branch": "all_valid_combat" if count is not None and count > 0 else "nonpositive_queue",
        "backing_queue_ids_preserved": True,
        "prior_physical_writes": deepcopy(prior_writes),
        "physical_write_effects": deepcopy(prior_writes) + deepcopy(result["direct_write_effects"]),
        "unchanged_fields": ["primary30/3C", "prepared148/all chunk bytes", "Army38/44 ArRg rosters", "ArRg current/max caches", "Army130..17F stats", "primaryC8/D4", "Army190"],
        "returned_provenance": {
            "callee": "2A9AF20", "callsite": "2A9A678",
            "predecessor": deepcopy(dict(prior)), "evidence_kind": "conditional_source_return",
            "next_callsite": "2A9A8DD", "next_callee": "2A98AC0",
            "date_predicate_executed": False, "noncombat_refresh_executed": False,
        },
    })
    return result


def reuse_native_empty_gathering_queue(reader: Mapping[str, object], stage: Mapping[str, object]) -> dict:
    """Reuse an explicitly bound existing id_lists158 reader, without new capture.

    The caller must establish that this reader belongs to the same explicit
    predecessor stage. An independent current query cannot pass this binding.
    """
    if any(reader.get(key) != stage.get(key) for key in ("entry_frame_id", "manager_identity", "capture_identity")):
        raise ValueError("existing native queue reader is not this stage frame")
    if reader.get("source") != "monthly_first_removal_cleanup_inputs_v1.id_lists.158":
        raise ValueError("unknown native queue reader")
    if reader.get("available") is not True or reader.get("ids") != []:
        raise ValueError("existing native reader does not prove nonpositive queue")
    adapted = deepcopy(dict(stage))
    queue = adapted["entry_state"]["primary_queue_158"]
    known_count = queue.get("signed_count")
    if known_count is not None and _s32(known_count) > 0:
        raise ValueError("native empty reader contradicts known same-frame positive count")
    queue.update(signed_count=None, normalized_visible_ids=[], count_basis="native_reader_nonpositive", reader_available=True)
    return project_army_gathering_due_stage_12004(adapted)
