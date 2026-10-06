"""Source-ordered Province/tier group PCs of following2921350, without writes."""
from __future__ import annotations

from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
from .battle_trait_materialized_prefix_12003 import _fold_property_request
from .battle_trait_numeric_inputs_12003 import native_wrap32_12003

INCOMING_STAGE_FOLLOWING_2921350_12003 = "post2920D60_pre291CD9D"
PROSPECTIVE_STAGE_FOLLOWING_2921350_12003 = "post2921350_pre291CDA8"


def following_2921350_fnv1a_12003(full_id: int) -> int:
    value = 0x811C9DC5
    for byte in full_id.to_bytes(4, "little", signed=False):
        value = ((value ^ byte) * 0x1000193) & 0xFFFFFFFF
    return value


def following_2921350_tier_index_12003(count, thresholds, operand):
    if count is None or operand is None:
        return None
    if count <= 0:
        return native_wrap32_12003(count - 1)
    if thresholds is None:
        return None
    for i, threshold in enumerate(thresholds):
        if operand < threshold:
            return native_wrap32_12003(i - 1)
    return native_wrap32_12003(count - 1) if len(thresholds) == count else None


def following_2921350_group_results_12003(leaf):
    """Only complete source streams can prove that no unseen row targets a group."""
    manager = leaf["manager"]
    if not manager["ready"]:
        raise ValueError("Required native input unavailable: following_2921350.manager")
    count = manager["group_count_raw_i32"]
    groups = [{"native_index": i, "ready": True, "reason": None,
               "property_block": {"keys_count": 0, "values_count": 0,
                                  "keys_u16": [], "values_q64": [], "reason": None},
               "inner_occurrences": [], "updates": []} for i in range(count)]
    title_source, walk = leaf["title_source"], leaf["title_walk"]
    complete_stream = title_source["ready"]
    expected_visits = title_source["count_raw"] if title_source["ready"] else None
    for row in walk:
        if row["tier_raw_i32"] is None or row["reason"] is not None:
            complete_stream = False
        elif row["tier_raw_i32"] > 1:
            children = row["children_count_raw"]
            if children is None or children < 0 or row["child_ids_u32"] is None:
                complete_stream = False
            elif expected_visits is not None:
                expected_visits += children
    complete_stream = complete_stream and len(walk) == expected_visits
    collected = sum(row["collected"] is True for row in leaf["title_walk"])
    complete_stream = complete_stream and len(leaf["provinces"]) == collected
    for province in leaf["provinces"]:
        steps = province["steps"]
        if (not steps or any(step["reason"] is not None for step in steps)
                or steps[-1]["tier_raw_i32"] in {None, 2} or province["province_identity"] is None):
            complete_stream = False
            continue
        if province["admitted"] is False:
            continue
        n = province["source_count_raw"]
        if (province["admitted"] is not True or n is None or n < 0
                or province["source_ids_u32"] is None or len(province["sources"]) != n):
            complete_stream = False
            continue
        for source in province["sources"]:
            index = source["group_index_raw_i32"]
            if index is None or not 0 <= index < count:
                complete_stream = False
                continue
            group = groups[index]
            tiers = source["tiers"]
            if (source["reason"] is not None or source["selection"] is None
                    or source["object_identity"] is None or source["definition_identity"] is None
                    or not source["map"]["ready"] or not tiers["ready"]):
                group["ready"] = False
                group["reason"] = (source["reason"] or source["map"]["reason"] or tiers["reason"]
                                   or "following2921350_source_identity_unavailable")
                continue
            block = tiers["pc"]["property_block"]
            size = block["keys_count"]
            metadata = {"province_native_index": province["native_index"],
                        "source_native_index": source["native_index"],
                        "property_identity": tiers["pc"]["property_identity"]}
            group["inner_occurrences"].append(metadata)
            if size:
                target = group["property_block"]
                _fold_property_request(target["keys_u16"], target["values_q64"],
                                       tuple(block["keys_u16"][:size]), tuple(block["values_q64"][:size]),
                                       100000, metadata, group["updates"])
                target["keys_count"] = len(target["keys_u16"])
                target["values_count"] = len(target["values_q64"])
    if not complete_stream:
        for group in groups:
            group["ready"] = False
            group["reason"] = "following2921350_complete_occurrence_stream_unavailable"
    return tuple(groups)


def emit_following_2921350_requests_12003(leaf):
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: following_2921350")
    return tuple(request for group in following_2921350_group_results_12003(leaf)
                 for request in emit_following_2921350_group_requests_12003(leaf, group))


def emit_following_2921350_group_requests_12003(leaf, group):
    if not group["ready"]:
        raise ValueError("Required native input unavailable: following_2921350.group")
    if group["property_block"]["keys_count"] == 0:
        return ()
    return (NativeWeightedContributionRequest12003(
        0, "following_2921350_group", group["native_index"], 1,
        f"following2921350:{leaf['character_identity']}:group{group['native_index']}",
        group["property_block"], 100000,
    ),)
