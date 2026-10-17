"""Fixed stock reinforcement control; source candidates are not selected receivers."""
from __future__ import annotations

from .gui_refill_receiver_candidates_12004_contract import (
    bind_receiver_frame, normalize_static_direct_owner_switch,
)
from .gui_window_tree_contract import normalize_gui_window_tree_v1
from .ingame_military_open_12004 import _binding as reinforcement_binding
from .version_identity import CK3_12004, require_exact_native_build

ENABLE_STEP = "enable-military-reinforcement-v1"
DISABLE_STEP = "disable-military-reinforcement-v1"
STEPS = {ENABLE_STEP, DISABLE_STEP}
SCHEMA = "ck3-military-reinforcement-set-12004-v1"
GUI_SHA256 = "4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac"
PROFILES = {
    "0/0/0/2/3/0/0/0": ("0/0/0/2", "tab_your_armies", "0/0/0/2/3"),
    "0/0/0/3/5/0/0/0": ("0/0/0/3", "imperial_armies_ra_uses_this", "0/0/0/3/5"),
}
UNKNOWN_OBSERVATIONS = ("current_variable_table_observed", "native_receiver_selected", "provider_invoked")
SWITCH_FIELDS = {
    "source", "scope", "status", "unavailable_reason", *UNKNOWN_OBSERVATIONS,
    "ancestor_depth", "owner_full_id", "military_component_present", "raw_byte_4a9",
    "enabled", "value_basis", "stable_double_read",
}
ACK_FIELDS = {
    "schema", "step", "accepted", "status", "unavailable_reason", "desired_enabled", "game_version", "executable_sha256",
    "native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw",
    "owner_thread_verified", "frame_verified", "source_abi_pins_verified", "gui_owner_binding_verified",
    "source_profile_verified", "current_tree_complete", "no_blocking_modal_verified",
    "source_child_path", "source_gui_sha256", "before_switch", "dispatch_attempted", "dispatch_invoked",
    "native_handled", "postcondition_verified", "verification_pending", *UNKNOWN_OBSERVATIONS,
}
ACK_DIAGNOSTICS = {"native_after_tree_complete", "before_after_same_source", "native_after_switch"}
ACK_TRANSPORT_FIELDS = {"backend_id"}


def step_for_desired(desired_enabled: object) -> str:
    if type(desired_enabled) is not bool:
        raise ValueError("reinforcement desired_enabled must be a boolean")
    return ENABLE_STEP if desired_enabled else DISABLE_STEP


def require_same_frame(starting: dict, current: dict, binding: dict) -> None:
    if (reinforcement_binding(current) != binding
            or any(starting.get(k) != current.get(k) or starting.get(k) is None
                   for k in ("snapshot_id", "revision", "native_revision", "episode_run_id"))):
        raise ValueError("reinforcement observation crossed the actual paused episode/frame")


def normalize_switch_observation(raw: object, owner: int) -> dict:
    """Validate native ACK scalars without inventing an entry or receiver join."""
    if (type(raw) is not dict or raw.keys() != SWITCH_FIELDS
            or raw["source"] != "native_gui_type635_static_direct_owner_switch_12004"
            or raw["scope"] != "static_direct_source_candidate"
            or raw["status"] != "available" or raw["unavailable_reason"] is not None
            or any(raw[k] is not False for k in UNKNOWN_OBSERVATIONS)
            or raw["stable_double_read"] is not True
            or type(raw["ancestor_depth"]) is not int or not 8 <= raw["ancestor_depth"] <= 11
            or type(raw["owner_full_id"]) is not int or raw["owner_full_id"] != owner
            or type(raw["military_component_present"]) is not bool or type(raw["enabled"]) is not bool):
        raise ValueError("reinforcement switch lacks its available stable source owner")
    if raw["military_component_present"]:
        if (type(raw["raw_byte_4a9"]) is not int or not 0 <= raw["raw_byte_4a9"] <= 255
                or raw["value_basis"] != "raw_military_byte"
                or raw["enabled"] is not (raw["raw_byte_4a9"] != 0)):
            raise ValueError("reinforcement raw switch byte/derived value disagree")
    elif (raw["raw_byte_4a9"] is not None or raw["enabled"] is not False
            or raw["value_basis"] != "native_null_military_zero"):
        raise ValueError("reinforcement null military component basis is inconsistent")
    return dict(raw)


def observe_fixed_reinforcement(tree: object, before: dict, after: dict) -> dict:
    """Consume a fresh complete source census, including its existing owner join."""
    binding = reinforcement_binding(before)
    require_same_frame(before, after, binding)
    clean = normalize_gui_window_tree_v1(tree, "military")
    if (clean["root_available"] is not True or clean["truncated"] is not False
            or clean.get("read_only") is not True):
        raise ValueError("reinforcement needs a complete actual military census")
    public = bind_receiver_frame(clean.get("refill_receiver_frame_12004"), before, after)
    by_path = {}
    for row in clean["widgets"]:
        if row["child_path"] in by_path:
            raise ValueError("reinforcement military census has duplicate child paths")
        by_path[row["child_path"]] = row
    root = by_path.get("")
    if not root or root["runtime_name"] != "military_view" or root["effective_visible"] is not True:
        raise ValueError("reinforcement military root is not actually visible")
    matches = []
    for row in clean["widgets"]:
        if not row["effective_visible"] or not row["enabled"]:
            continue
        for callback in row["standard_click_binding_12004"]["callbacks"]:
            payload = callback.get("indirect_target_3aa30e0", {})
            expression = payload.get("expression_3a9f960", {})
            if expression.get("final_target_38_rva") != 0x1303D40:
                continue
            if (row["child_path"] not in PROFILES or row["runtime_name"] != ""
                    or callback["callback_slot2_rva"] != 0x3AA30E0
                    or payload.get("native_target_8_rva") != 0x3A9F960
                    or payload.get("receiver_f0_present") is not True
                    or expression.get("chain_count_24_raw") != 0
                    or expression.get("final_kind_34_raw") != 3
                    or expression.get("receiver_type_id_48") != 635
                    or expression.get("receiver_flag_4c_raw") != 0
                    or expression.get("final_user_data_40_present") is not True):
                raise ValueError("reinforcement final target is outside the fixed source profile")
            tab_path, tab_name, footer_path = PROFILES[row["child_path"]]
            if (by_path.get(tab_path, {}).get("runtime_name") != tab_name
                    or by_path.get(footer_path, {}).get("runtime_name") != "footer"):
                raise ValueError("reinforcement source ancestors do not match the fixed profile")
            candidates = expression.get("receiver_entry_candidates_12004", {})
            tail = candidates.get("definition_frontier_continuation_depth8_12", {})
            switch = tail.get("static_direct_owner_switch_12004")
            # The whole census consumer already checks source parent entries,
            # including the mode1 owner join. Reuse the child validator with
            # those real rows rather than fabricating a synthetic source row.
            switch = normalize_static_direct_owner_switch(switch, tail.get("rows", []))
            switch = normalize_switch_observation(switch, binding["played_character_id"])
            matches.append({"source_child_path": row["child_path"], "switch": switch})
    if len(matches) != 1:
        raise ValueError("reinforcement requires exactly one visible enabled stock source control")
    return {**matches[0], "frame": clean["refill_receiver_frame_12004"], "public_binding": public}


def normalize_reinforcement_ack(raw: object, binding: dict, desired_enabled: bool,
                                before_observation: dict) -> dict:
    step = step_for_desired(desired_enabled)
    if (type(raw) is not dict or not ACK_FIELDS <= raw.keys() or raw.keys() - ACK_FIELDS - ACK_DIAGNOSTICS - ACK_TRANSPORT_FIELDS
            or raw["schema"] != SCHEMA or raw["step"] != step or raw["accepted"] is not True
            or raw["unavailable_reason"] is not None
            or ("backend_id" in raw and (type(raw["backend_id"]) is not str or raw["backend_id"] != "native-headless"))
            or type(raw["desired_enabled"]) is not bool or raw["desired_enabled"] is not desired_enabled
            or raw["source_gui_sha256"] != GUI_SHA256
            or raw["source_child_path"] != before_observation["source_child_path"]
            or require_exact_native_build(raw["game_version"], raw["executable_sha256"]) != CK3_12004
            or raw["postcondition_verified"] is not False or raw["verification_pending"] is not True
            or any(raw[k] is not False for k in UNKNOWN_OBSERVATIONS)):
        raise ValueError("reinforcement native acknowledgement lacks its exact source/profile")
    for key in ("native_revision", "connection_generation", "game_pid", "played_character_id", "date_raw"):
        if type(raw[key]) is not int or raw[key] != binding[key]:
            raise ValueError("reinforcement native acknowledgement crossed binding: " + key)
    for key in ("owner_thread_verified", "frame_verified", "source_abi_pins_verified", "gui_owner_binding_verified",
                "source_profile_verified", "current_tree_complete", "no_blocking_modal_verified"):
        if raw[key] is not True:
            raise ValueError("reinforcement native source admission unavailable: " + key)
    before_switch = normalize_switch_observation(raw["before_switch"], binding["played_character_id"])
    if before_switch != before_observation["switch"]:
        raise ValueError("reinforcement source switch changed before native admission")
    if any(type(raw[k]) is not bool for k in ("dispatch_attempted", "dispatch_invoked", "native_handled")):
        raise ValueError("reinforcement dispatch diagnostics must be actual booleans")
    if before_switch["enabled"] is desired_enabled:
        if (raw["status"] != "noaction_already_desired" or raw["dispatch_attempted"]
                or raw["dispatch_invoked"] or raw["native_handled"]):
            raise ValueError("reinforcement already-desired result attempted a toggle")
    elif (raw["status"] != "acknowledged_verification_pending"
          or raw["dispatch_attempted"] is not True or raw["dispatch_invoked"] is not True):
        raise ValueError("reinforcement desired transition lacks one actual native dispatch")
    for key in ("native_after_tree_complete", "before_after_same_source"):
        if key in raw and type(raw[key]) is not bool:
            raise ValueError("reinforcement optional native diagnostic must be boolean")
    if raw.get("native_after_switch") is not None:
        normalize_switch_observation(raw["native_after_switch"], binding["played_character_id"])
    return dict(raw)
