"""Strict read-only .4 standard-click target observations; no method-name inference."""
from __future__ import annotations

SOURCE_12004 = {
    "executable_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
    "button_base_slot13_rva": 0x3AA0D20,
    "group_dispatch_rva": 0x3A9FA30,
    "input_modifier": 0,
}
SOURCE_INDIRECT_12004 = {
    **SOURCE_12004,
    "indirect_target_thunk_rva": 0x3AA30E0,
    "indirect_target_thunk_bytes_sha256": "7a37683abfa5cb9317164e719bc14ba7cc067f79fee8e086267a11d8b18f3563",
}
IMAGE_BYTES_12004 = 0x61C5000

def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high

def normalize_callback_binding_rows_12004(raw: dict, projected: dict) -> dict:
    source = raw.get("callback_binding_source_12004")
    profile = SOURCE_INDIRECT_12004 if isinstance(source, dict) and set(source) == set(SOURCE_INDIRECT_12004) else SOURCE_12004
    if not isinstance(source, dict) or set(source) != set(profile) or any(
        type(source[key]) is not type(value) or source[key] != value
        for key, value in profile.items()
    ):
        raise ValueError("standard click binding has no exact .4 source identity")
    if raw.get("truncated") is not False:
        raise ValueError("military callback census is incomplete")
    if raw.get("root_available") is False and raw["widgets"]:
        raise ValueError("missing military window cannot contain callback targets")
    rows = []
    for native, clean in zip(raw["widgets"], projected["widgets"], strict=True):
        if not _integer(clean["vtable_rva"], 1, IMAGE_BYTES_12004 - 112):
            raise ValueError("military widget vtable is outside the exact image")
        binding = native.get("standard_click_binding_12004")
        if not isinstance(binding, dict) or set(binding) != {"button_base_slot13", "group", "callbacks"}:
            raise ValueError("standard click binding is missing or malformed")
        button, group, callbacks = binding["button_base_slot13"], binding["group"], binding["callbacks"]
        if type(button) is not bool or not isinstance(callbacks, list) or len(callbacks) > 256:
            raise ValueError("standard click binding exceeds its source bounds")
        if (not button and (group != "not_button_base" or callbacks)) or (
            button and (group not in {"primary", "fallback"} or (group == "primary" and not callbacks))
        ):
            raise ValueError("standard click group does not match observed source selection")
        targets = []
        for index, target in enumerate(callbacks):
            indirect = profile is SOURCE_INDIRECT_12004 and isinstance(target, dict) and target.get("callback_slot2_rva") == 0x3AA30E0
            expected_keys = {"index", "callback_vtable_rva", "callback_slot2_rva"} | ({"indirect_target_3aa30e0"} if indirect else set())
            if not isinstance(target, dict) or set(target) != expected_keys or (
                type(target["index"]) is not int or target["index"] != index or
                not _integer(target["callback_vtable_rva"], 1, IMAGE_BYTES_12004 - 24) or
                not _integer(target["callback_slot2_rva"], 1, IMAGE_BYTES_12004 - 1)
            ):
                raise ValueError("callback target is outside its exact image or row order")
            clean_target = dict(target)
            if indirect:
                payload = target["indirect_target_3aa30e0"]
                if not isinstance(payload, dict) or set(payload) != {"native_target_8_rva", "receiver_f0_present"} or (
                    not _integer(payload["native_target_8_rva"], 1, IMAGE_BYTES_12004 - 1) or
                    type(payload["receiver_f0_present"]) is not bool
                ):
                    raise ValueError("indirect callback target does not match the source-backed thunk")
                clean_target["indirect_target_3aa30e0"] = dict(payload)
            targets.append(clean_target)
        rows.append({**clean, "standard_click_binding_12004": {
            "button_base_slot13": button, "group": group, "callbacks": targets,
        }})
    return {**projected, "widgets": rows, "callback_binding_source_12004": dict(profile),
            "callback_method_name_available": False, "click_action_available": False}
