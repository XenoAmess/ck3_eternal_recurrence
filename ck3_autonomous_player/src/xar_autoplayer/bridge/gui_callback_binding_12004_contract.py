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
SOURCE_EXPRESSION_12004 = {
    **SOURCE_INDIRECT_12004,
    "expression_target_bridge_rva": 0x3A9F960,
    "expression_builder_rva": 0x3AC38C0,
    "expression_eval_rva": 0x3E4C090,
    "expression_layout_bytes_sha256": "7412efd136e722993b71a8810f5d585347cde53104ba0a107551eb324ff18963",
}
SOURCE_RECEIVER_12004 = {
    **SOURCE_EXPRESSION_12004,
    "receiver_definition_parent_rva": 0x3AC3EF0,
    "receiver_typed_entry_rva": 0x3AC1C00,
    "receiver_definition_parent_bytes_sha256": "476ac96745e7088e7dd2073cfc00e023d8a1102a8d154a51434886d6d5b5a2a7",
    "receiver_typed_entry_bytes_sha256": "8efccb736158d04c2847d98e8aa6d3400ae8591467d2628726a1f1c396e43cfc",
}
IMAGE_BYTES_12004 = 0x61C5000

def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high

def _expression_descriptor(raw: object, *, receiver_candidates: bool = False) -> dict:
    fields = {"chain_count_24_raw", "final_type_id_30", "final_kind_34_raw", "final_target_38_rva",
              "final_user_data_40_present", "receiver_type_id_48", "receiver_flag_4c_raw", "chain_calls"}
    has_candidates = isinstance(raw,dict) and "receiver_entry_candidates_12004" in raw
    if has_candidates:
        if not receiver_candidates:raise ValueError("receiver candidates lack exact source pins")
        fields = fields | {"receiver_entry_candidates_12004"}
    if not isinstance(raw, dict) or set(raw) != fields or not all(
        _integer(raw[k], 0, 0xFFFFFFFF) for k in ("final_type_id_30", "final_kind_34_raw", "receiver_type_id_48")
    ) or not _integer(raw["receiver_flag_4c_raw"], 0, 255) or type(raw["final_user_data_40_present"]) is not bool:
        raise ValueError("expression descriptor has invalid raw fields")
    chain = raw["chain_calls"]
    if not isinstance(chain, list) or not _integer(raw["chain_count_24_raw"], 0, 16) or len(chain) != raw["chain_count_24_raw"]:
        raise ValueError("expression receiver-chain is incomplete or exceeds source bounds")
    callable_kind = raw["final_kind_34_raw"] in {3, 4}
    if not _integer(raw["final_target_38_rva"], 1 if callable_kind else 0, IMAGE_BYTES_12004 - 1 if callable_kind else 0):
        raise ValueError("expression final target conflicts with the source callable kind")
    clean = []
    for index, row in enumerate(chain):
        if not isinstance(row, dict) or set(row) != {"index", "type_id_0", "kind_4_raw", "native_target_8_rva", "user_data_10_present"} or (
            not _integer(row["index"], index, index) or not _integer(row["type_id_0"], 0, 0xFFFFFFFF) or
            not _integer(row["kind_4_raw"], 0, 0xFFFFFFFF) or not _integer(row["native_target_8_rva"], 1, IMAGE_BYTES_12004 - 1) or
            type(row["user_data_10_present"]) is not bool
        ):
            raise ValueError("expression receiver-chain target or ordinal is invalid")
        clean.append(dict(row))
    result = {**raw,"chain_calls":clean}
    if has_candidates:
        from .gui_refill_receiver_candidates_12004_contract import normalize_receiver_candidates
        if (raw['receiver_type_id_48']!=635 or raw['receiver_flag_4c_raw']!=0 or
                raw['chain_count_24_raw']!=0 or raw['final_kind_34_raw']!=3 or raw['final_target_38_rva']!=0x1303D40):
            raise ValueError("receiver candidates not on the fixed refill callback")
        result['receiver_entry_candidates_12004']=normalize_receiver_candidates(raw['receiver_entry_candidates_12004'])
    return result

def normalize_callback_binding_rows_12004(raw: dict, projected: dict) -> dict:
    source = raw.get("callback_binding_source_12004")
    profile = next((p for p in (SOURCE_RECEIVER_12004, SOURCE_EXPRESSION_12004, SOURCE_INDIRECT_12004, SOURCE_12004) if isinstance(source, dict) and set(source) == set(p)), SOURCE_12004)
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
            indirect = profile is not SOURCE_12004 and isinstance(target, dict) and target.get("callback_slot2_rva") == 0x3AA30E0
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
                expression = profile in (SOURCE_EXPRESSION_12004,SOURCE_RECEIVER_12004) and isinstance(payload, dict) and payload.get("native_target_8_rva") == 0x3A9F960
                payload_fields = {"native_target_8_rva", "receiver_f0_present"} | ({"expression_3a9f960"} if expression else set())
                if not isinstance(payload, dict) or set(payload) != payload_fields or (
                    not _integer(payload["native_target_8_rva"], 1, IMAGE_BYTES_12004 - 1) or
                    type(payload["receiver_f0_present"]) is not bool
                ):
                    raise ValueError("indirect callback target does not match the source-backed thunk")
                clean_target["indirect_target_3aa30e0"] = dict(payload)
                if expression:
                    clean_target["indirect_target_3aa30e0"]["expression_3a9f960"] = _expression_descriptor(payload["expression_3a9f960"],receiver_candidates=profile is SOURCE_RECEIVER_12004)
            targets.append(clean_target)
        rows.append({**clean, "standard_click_binding_12004": {
            "button_base_slot13": button, "group": group, "callbacks": targets,
        }})
    if profile is SOURCE_RECEIVER_12004:
        from .gui_refill_receiver_candidates_12004_contract import normalize_receiver_frame
        projected={**projected,'refill_receiver_frame_12004':normalize_receiver_frame(raw.get('refill_receiver_frame_12004'))}
    elif 'refill_receiver_frame_12004' in raw:
        raise ValueError('receiver frame lacks exact new source pins')
    return {**projected, "widgets": rows, "callback_binding_source_12004": dict(profile),
            "callback_method_name_available": False, "click_action_available": False}
