"""Reusable raw positive builder; this module executes no tests."""
from __future__ import annotations

from copy import deepcopy

Q = 100000
PROVINCE_ID = 0xCA000009
TITLE_IDS = (0xA0000001, 0xA0000002, 0xA0000003)
SOURCE_IDS = (0xB0000001, 0xB0000002)


def _available(**fields):
    return {"status": "available", "ready": True, "reason": None, **fields}


def _pc(identity, keys, values):
    return {"property_identity": identity, "reason": None,
            "property_block": {"keys_count": len(keys), "values_count": len(values),
                               "keys_u16": keys, "values_q64": values, "reason": None}}


def _walk(index, title, parent, tier, collected, children=None):
    return {"native_index": index, "root_index": 0, "parent_index": parent,
            "requested_full_id_u32": TITLE_IDS[title], "selection": "registry_full_id",
            "selected_full_id_u32": TITLE_IDS[title], "title_identity": f"title-{title}",
            "definition_identity": f"title-definition-{title}", "tier_raw_i32": tier,
            "children_count_raw": None if children is None else len(children),
            "children_array_present": None if children is None or not children else True,
            "child_ids_u32": children, "collected": collected, "reason": None}


def _source(index, kind):
    # FNV(PROVINCE_ID)&0 is0. Found distance1 reads the operand; distance0
    # returns a genuine absent0 without reading key/payload.
    found = kind == 0
    probe = {"native_index": 0, "bucket_index_i64": 0, "distance_raw_u8": 1 if found else 0,
             "key_raw_u32": PROVINCE_ID if found else None,
             "operand_q64": 0 if found else None, "reason": None}
    return {"native_index": index, "requested_full_id_u32": SOURCE_IDS[kind],
            "selection": "registry_full_id", "selected_full_id_u32": SOURCE_IDS[kind],
            "object_identity": f"source-{kind}", "definition_identity": f"source-definition-{kind}",
            "group_index_raw_i32": kind, "reason": None,
            "map": _available(data_identity=f"source-map-{kind}", mask_raw_i32=0, overflow_raw_u8=0,
                              probes=[probe], found=found, operand_q64=0),
            "tiers": _available(count_raw_i32=2, data_identity=f"tier-rows-{kind}",
                thresholds_q64=[0, 10 * Q], selected_index_raw_i32=0, selection="indexed_tier",
                default_guard_raw_i32=None,
                pc=_pc(f"tier-pc-{kind}", [0, 5, 65535] if kind == 0 else [4],
                       [-Q, 2 * Q, -3 * Q] if kind == 0 else [0]))}


def following2921350_positive_leaf(character_id=29829):
    walk = [_walk(0, 0, None, 3, False, [TITLE_IDS[1], TITLE_IDS[1], TITLE_IDS[2]]),
            _walk(1, 1, 0, 1, True), _walk(2, 1, 0, 1, False), _walk(3, 2, 0, 1, True)]
    provinces = []
    for index, title_index in enumerate((1, 3)):
        title = 1 if index == 0 else 2
        step = {"native_index": 0, "title_identity": f"title-{title}",
                "definition_identity": f"title-definition-{title}", "tier_raw_i32": 1,
                "requested_full_id_u32": None, "selection": None, "selected_full_id_u32": None,
                "first_child_count_raw": None, "first_child_array_present": None,
                "first_child_full_id_u32": None, "reason": None}
        provinces.append({"native_index": index, "title_walk_index": title_index, "steps": [step],
                          "province_identity": "province-shared", "magic_u32": 0x50726F76,
                          "admitted": True, "full_id_u32": PROVINCE_ID, "source_count_raw": 3,
                          "source_array_present": True,
                          "source_ids_u32": [SOURCE_IDS[0], SOURCE_IDS[0], SOURCE_IDS[1]],
                          "sources": [_source(0, 0), _source(1, 0), _source(2, 1)], "reason": None})
    return _available(character_id=character_id, character_identity=f"character-{character_id}",
        source_scope="held_current_native_inputs",
        title_source=_available(carrier_present=True, selection="current_1c0_1e0",
                                header_identity="living-title-header", count_raw=1,
                                array_present=True, full_ids_u32=[TITLE_IDS[0]]),
        title_walk=walk, provinces=provinces,
        manager=_available(loaded=True, identity="loaded-manager", group_count_raw_i32=3))


def following2921350_cold_leaf(character_id=29829):
    leaf = deepcopy(following2921350_positive_leaf(character_id))
    # Every occurrence of the same source object sees the same paused map.
    for province in leaf["provinces"]:
        source = province["sources"][2]
        source["map"]["found"] = True
        source["map"]["operand_q64"] = -1
        source["map"]["probes"][0].update(distance_raw_u8=1, key_raw_u32=PROVINCE_ID, operand_q64=-1)
        source["tiers"].update(status="partial", ready=False, reason="tier_default_2560620_result",
                               thresholds_q64=[0], selected_index_raw_i32=-1,
                               selection="cold_default_5d65b00", default_guard_raw_i32=0,
                               pc={"property_identity": None, "property_block": None,
                                   "reason": "tier_default_2560620_result"})
        source["reason"] = province["reason"] = "tier_default_2560620_result"
    leaf.update(status="partial", ready=False, reason="tier_default_2560620_result")
    return leaf


def following2921350_zero_leaf(character_id=29829):
    leaf = following2921350_positive_leaf(character_id)
    leaf["title_source"].update(count_raw=0, array_present=None, full_ids_u32=[])
    leaf.update(title_walk=[], provinces=[])
    return leaf
