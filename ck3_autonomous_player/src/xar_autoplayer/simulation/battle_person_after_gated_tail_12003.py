"""Pure source-ordered numeric requests for 326A8E0 then 2920310."""
from __future__ import annotations

from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
from .battle_person_gated_temporary_tail_12003 import literal_named_source_value_12003
from .battle_trait_materialized_prefix_12003 import _fold_property_request
from .battle_trait_numeric_inputs_12003 import native_wrap32_12003

FAMILIES_AFTER_GATED_12003 = (
    "composition_326a8e0", "current_1b8_court_positions",
    "current_1c0_court_positions", "related_court_positions",
)
# Exact cached365B tables:444C340 SHA49cfa773;444C4B0 SHA218539a9.
_DAY_TABLE = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e")
_MONTH_TABLE = bytes.fromhex("000000000000000000000000000000000000000000000000000000000000000101010101010101010101010101010101010101010101010101010102020202020202020202020202020202020202020202020202020202020202030303030303030303030303030303030303030303030303030303030303040404040404040404040404040404040404040404040404040404040404040505050505050505050505050505050505050505050505050505050505050606060606060606060606060606060606060606060606060606060606060607070707070707070707070707070707070707070707070707070707070707080808080808080808080808080808080808080808080808080808080808090909090909090909090909090909090909090909090909090909090909090a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b")


def _trunc(value, divisor):
    return -(abs(value) // divisor) if value < 0 else value // divisor


def decode_after_gated_date_12003(date: dict) -> tuple[int, int, int] | None:
    day, month, year = (date[key] for key in ("day_cache_i8", "month_cache_i8", "year_cache_i16"))
    if any(value is None for value in (day, month, year)):
        return None
    if min(day, month, year) < 0:
        raw = date["raw_i32"]
        if raw is None:
            return None
        hours = native_wrap32_12003(raw - 43800000)
        day_index = _trunc(hours, 24) % 365
        if day < 0:
            day = _DAY_TABLE[day_index]
        if month < 0:
            month = _MONTH_TABLE[day_index]
        if year < 0:
            year = _trunc(hours, 8760)
    return day, month, year


def completed_after_gated_months_12003(current: dict, chosen: dict) -> int | None:
    a, b = decode_after_gated_date_12003(current), decode_after_gated_date_12003(chosen)
    if a is None or b is None:
        return None
    months = native_wrap32_12003(12 * native_wrap32_12003(a[2] - b[2]) + a[1] - b[1])
    return native_wrap32_12003(months - (a[0] < b[0]))


def definition_600_literal_value_12003(rule: dict) -> int | None:
    mode = rule["mode_raw"]
    if mode is None:
        return None
    if mode == 0:
        return rule["raw_98_q64"]
    if rule["tree_present"] is not False:
        return None
    if rule["named_present"] is True:
        return literal_named_source_value_12003(rule["named"])
    if rule["named_present"] is False and rule["target_count_raw"] == 0:
        return rule["raw_98_q64"]
    return None


def quantized_court_position_kind_12003(kind: dict) -> int | None:
    played = kind["owner_played"]
    if played is None:
        return None
    if played is False:
        raw = kind["raw_a0_u8"]
        if raw is None:
            return None
        if raw != 5:
            return raw
    count = kind["threshold_count_raw"]
    if count is None:
        return None
    if count < 4:
        return 4
    value, thresholds = definition_600_literal_value_12003(kind["rule"]), kind["thresholds_i32"]
    if value is None or thresholds is None or len(thresholds) != 4:
        return None
    return next((i for i, threshold in enumerate(thresholds) if value < threshold * 100000), 4)


def fold_after_gated_blocks_12003(blocks) -> dict:
    keys, values, updates = [], [], []
    for block in blocks:
        count = block["keys_count"]
        if count:
            _fold_property_request(keys, values, tuple(block["keys_u16"][:count]),
                                   tuple(block["values_q64"][:count]), 100000, {}, updates)
    return {"keys_count": len(keys), "values_count": len(values),
            "keys_u16": keys, "values_q64": values, "reason": None}


def composed_after_gated_group_12003(group: dict) -> dict:
    blocks = [group["base_property_block"]]
    blocks.extend(row["property_block"] for family in ("conditional_b_rows", "conditional_a_rows")
                  for row in group[family] if row["admitted"])
    return fold_after_gated_blocks_12003(blocks)


def emit_after_gated_tail_family_requests_12003(leaf: dict, family: str, *, actual_leaf: dict | None = None) -> tuple:
    if family not in FAMILIES_AFTER_GATED_12003:
        raise ValueError("Unknown after-gated tail family")
    current = leaf[family]
    if not current["ready"]:
        raise ValueError("Required native input unavailable: after_gated_tail." + family)
    ordinal = FAMILIES_AFTER_GATED_12003.index(family)
    if ordinal == 0:
        if current["admitted"] is not True:
            return ()
        blocks = [row["pc"]["property_block"] for rowset in ("level_rows", "month_rows")
                  for row in current[rowset]["rows"] if row["admitted"]]
        block = fold_after_gated_blocks_12003(blocks)
        return (NativeWeightedContributionRequest12003(0, "326a8e0_composed_temporary", 0, 1,
                "modeled_temporary:326a8e0", block, 100000),)
    requests = []
    raw = leaf if actual_leaf is None else actual_leaf
    for position in current["rows"]:
        index = position["native_index"]
        actual = raw[family]["rows"][index]

        def pc(field, label):
            item = position[field]
            requests.append(NativeWeightedContributionRequest12003(ordinal, label, index, 1,
                            item["property_identity"], actual[field]["property_block"], 100000))

        def composite():
            block = composed_after_gated_group_12003(position["composite_group"])
            if block["keys_count"]:
                requests.append(NativeWeightedContributionRequest12003(ordinal, "291b8d0_" + family, index, 1,
                                "modeled_composite:" + position["position_identity"], block, 100000))

        if ordinal == 1:
            pc("base_pc", "2920310_current_1b8_base2748")
            composite()
            if position["other_admitted"]:
                pc("other_base_pc", "2920310_current_1b8_other1940")
        elif ordinal == 2:
            pc("base_pc", "2920310_current_1c0_base2908")
            pc("tier_pc", "2920310_current_1c0_tier2cb8")
            composite()
            if position["other_admitted"]:
                pc("other_base_pc", "2920310_current_1c0_other1b00")
                pc("other_tier_pc", "2920310_current_1c0_other_tier1cc0")
        else:
            if position["definition_pair_admitted"]:
                pc("base_pc", "2920310_related_base3658")
                pc("tier_pc", "2920310_related_tier3818")
            if position["other_admitted"] and position["other_pair_admitted"]:
                pc("other_base_pc", "2920310_related_other2580")
                pc("other_tier_pc", "2920310_related_other_tier2740")
    return tuple(requests)


def emit_after_gated_tail_requests_12003(leaf: dict, *, actual_leaf: dict | None = None) -> tuple:
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: after_gated_tail_326a8e0_2920310")
    return tuple(request for family in FAMILIES_AFTER_GATED_12003
                 for request in emit_after_gated_tail_family_requests_12003(leaf, family, actual_leaf=actual_leaf))
