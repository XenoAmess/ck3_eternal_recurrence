"""One instruction-derived compound reference; no native producer replay."""
from xar_autoplayer.simulation.battle_person_pc_merger_12004 import (
    fold_ordered_pc_contribution_12004,
    native_fixed_mul_q_12004,
)


def test_actual_signed_max_split_ordered_copy_insert_and_wrap() -> None:
    # 23031D3 chooses signed MAX=-1, then remainder*MIN wraps to INT64_MIN.
    # This intentionally differs from decomposing MIN or using an unbounded product.
    minimum, maximum = -(1 << 63), (1 << 63) - 1
    assert native_fixed_mul_q_12004(minimum, -1) == -92233720368547

    def request(ordinal: int, keys: list[int], values: list[int], weight: int) -> dict:
        return {
            "source_ordinal": ordinal,
            "property_block": {
                "keys_count": len(keys), "keys_u16": keys, "values_q64": values,
            },
            "weight_q100000": weight,
        }

    # These are synthetic native-operand references, not claimed paused captures.
    # First copy retains duplicates/FFFF and uses the cold scaler. Subsequent
    # merges update the first equal key, insert7, skipFFFF, and wrap two MAX adds.
    requests = [
        request(0, [2, 9, 9, 65535], [minimum, 200000, 400001, 900000], -1),
        request(3, [9, 7, 65535, 9], [300000, 500001, 999999, -100000], -200000),
        request(10, [2], [maximum], 100000),
        request(11, [2], [maximum], 100000),
    ]
    result = fold_ordered_pc_contribution_12004(requests)
    assert result["keys_u16"] == [2, 7, 9, 9, 65535]
    assert result["values_q64"] == [-92233720368549, -1000002, -400002, -4, -9]
    assert result["source_ordinals"] == [0, 3, 10, 11]
    assert requests[0]["property_block"]["keys_u16"] == [2, 9, 9, 65535]
    assert requests[0]["property_block"]["values_q64"][0] == minimum
    assert result["composition_kind"] == "explicit_empty_baseline_contribution"
    assert result["pre_six_baseline_observed"] is False
    assert result["historical_postimage_ready"] is False
    assert result["actual_model_write_performed"] is False
    assert result["full_person_ready"] is False and result["entry_ready"] is False
