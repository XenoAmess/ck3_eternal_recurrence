"""Reusable source-shaped inputs; imported by the parent's sole compound case."""
from copy import deepcopy


def following2921020_property(keys=(), values=()):
    return {"keys_count": len(keys), "values_count": len(values) if keys else None,
            "keys_u16": list(keys), "values_q64": list(values), "reason": None}


def build_following2921020_positive_leaf(*, character_id=29829, wrap_edge=False):
    def pc(identity, keys, values):
        return {"property_identity": identity, "property_block": following2921020_property(keys, values), "reason": None}
    weights = [(1 << 63) - 1, 1, -200000, 0] if wrap_edge else [200000, -100000, -200000, 0]
    return {
        "status": "available", "ready": True, "reason": None, "character_id": character_id,
        "component_present": True, "requested_full_id_raw": -1442840575,
        "resolution_selection": "registry_full_id_8", "selected_full_id_raw": -1442840575,
        "object_identity": "lege:actual-1", "magic_u32": 0x4C656765, "full_id_raw": -1442840575,
        "admitted": True, "character_full_id_raw": character_id, "owner_full_id_raw": character_id,
        "owner_matches": True, "table_identity": "lege:table70", "definition_identity": "lege:def78",
        "rank_raw_i8": 1, "tier_selection": "direct_rank_0_2", "selected_row_identity": "lege:actual-row1",
        "owner_weighted_header": {"selected_source": "selected_28", "count": 4,
            "rows": [{"native_index": i, "definition_identity": identity, "weight_q64": weight}
                     for i, (identity, weight) in enumerate(zip(("pointer:A", "pointer:A", "pointer:B", "pointer:A"), weights))],
            "reason": None},
        "owner_definition_blocks": [
            {"definition_identity": "pointer:A", "properties": following2921020_property((0,), (100000,))},
            {"definition_identity": "pointer:B", "properties": following2921020_property((5,), (-100000,))}],
        "owner_header_ready": True,
        "base_pc": pc("lege:def78+420", (1, 5), (100000, 200000)),
        "tier_pc": pc("lege:row1+2bf8", (4, 5), (-100000, -100000)),
        "composite_ready": True,
    }


def build_following2921020_nonowner_leaf(*, character_id=29829):
    leaf = deepcopy(build_following2921020_positive_leaf(character_id=character_id))
    leaf.update(owner_full_id_raw=character_id + 1, owner_matches=False,
                owner_weighted_header=None, owner_definition_blocks=[], owner_header_ready=None)
    leaf["base_pc"] = {"property_identity": "lege:def78+5e0",
        "property_block": following2921020_property((5,), (0,)), "reason": None}
    leaf["tier_pc"] = {"property_identity": "lege:row1+2db8",
        "property_block": following2921020_property(), "reason": None}
    return leaf
