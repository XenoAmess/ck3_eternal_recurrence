from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_person_diac_literal_numeric_contract import normalize_diac_literal_numeric_inputs_12003 as normalize
from xar_autoplayer.simulation.battle_person_diac_literal_numeric_12003 import (
    emit_diac_literal_numeric_requests_12003 as emit,
    emit_diac_literal_numeric_row_requests_12003 as emit_row,
)

Q = 100000
MIN64 = -(2**63)
MAX64 = 2**63 - 1


def availability(ready=True, reason=None):
    return {"status": "available" if ready else "partial", "ready": ready, "reason": reason}


def properties(*rows):
    return {"keys_count": len(rows), "values_count": len(rows), "keys_u16": [key for key, _ in rows],
            "values_q64": [value for _, value in rows]}


def declaration(index, identity, pairs, flags):
    return {**availability(), "native_index": index, "declaration_identity": identity, "scale_gate_280_raw": 0,
        "properties": properties(*pairs), "metadata_provider_loaded": True,
        "metadata_rows": [{"native_index": i, "key_u16": pair[0],
            "selection": "static_5451f40" if pair[0] == 65535 else "provider_50_c8",
            "metadata_identity": "0x5451f40" if pair[0] == 65535 else "metadata:" + str(pair[0]),
            "byte_ba_raw": flags[i][0], "byte_b8_raw": flags[i][1]} for i, pair in enumerate(pairs)]}


def diac_literal_numeric_source():
    """Actual independent full-ID-address/declaration raw shape; import runs no case."""
    pairs = [(5, 150000), (6, -150000), (7, MAX64), (65535, MIN64),
             (8, 214748364899999), (9, -214748364999999), (10, -199999)]
    flags = [(0, 0), (7, None), (0, 3), (0, 0), (0, 2), (0, 0), (0, 0)]
    rows = [declaration(0, "0x10002000", pairs, flags), declaration(1, "0x10002000", pairs, flags),
            declaration(2, "0x10003000", [(11, MAX64), (11, 0)], [(0, 0), (0, 0)]),
            declaration(3, "0x10004000", [], [])]
    return {**availability(), "scope_character_full_id": 0xAA000001 - 2**32,
        "scope_id_address_identity": "0x10001024", "definition_block_identity": "0x10000620",
        "declaration_count_raw": len(rows), "declaration_array_present": True, "declarations": rows}


def test_diac_literal_actual_quantization_flags_extremes_duplicates_empty_dynamic_and_scope_address():
    raw = diac_literal_numeric_source()
    before = deepcopy(raw)
    normalized = normalize(raw)
    requests = emit(normalized)
    expected = [100000, -150000, MAX64, 70231305300000, -214748364800000, 214748364700000, -100000]
    assert raw == before and len(requests) == 4 and all(item.weight_q64 == Q for item in requests)
    assert [item.first_row_index for item in requests] == [0, 1, 2, 3]
    assert requests[0].base_property_block["keys_u16"] == [5, 6, 7, 65535, 8, 9, 10]
    assert requests[0].base_property_block["values_q64"] == expected
    assert requests[1].base_property_block == requests[0].base_property_block
    assert requests[2].base_property_block["values_q64"] == [-70231305300000, 0]
    assert requests[2].base_property_block["keys_u16"] == [11, 11]
    assert requests[3].base_property_block == {"keys_count": 0, "values_count": 0, "keys_u16": [], "values_q64": [], "reason": None}
    assert requests[0].definition_identity == requests[1].definition_identity == "derived:325b080:0x10002000"
    assert requests[0].base_property_block is not normalized["declarations"][0]["properties"]
    assert normalized["declarations"][0]["properties"]["values_q64"][0] == 150000
    assert normalized["scope_character_full_id"] == 0xAA000001 - 2**32
    current_scope = diac_literal_numeric_source()
    current_scope.update(scope_character_full_id=29829, scope_id_address_identity="0x20000018",
                         definition_block_identity="0x10000658")
    assert len(emit(normalize(current_scope))) == 4

    bad_b8 = diac_literal_numeric_source()
    bad_b8["declarations"][0]["metadata_rows"][1]["byte_b8_raw"] = 0
    with pytest.raises(ValueError, match="BA branch skips"):
        normalize(bad_b8)
    bad_mapper = diac_literal_numeric_source()
    bad_mapper["declarations"][0]["metadata_rows"][3]["selection"] = "provider_50_c8"
    with pytest.raises(ValueError, match="mapper selection"):
        normalize(bad_mapper)
    supplied_scale = diac_literal_numeric_source()
    supplied_scale["declarations"][0]["effective_scale_q64"] = Q
    with pytest.raises(ValueError, match="must contain exactly"):
        normalize(supplied_scale)
    supplied_quantizer = diac_literal_numeric_source()
    supplied_quantizer["declarations"][0]["metadata_rows"][0]["quantize"] = True
    with pytest.raises(ValueError, match="must contain exactly"):
        normalize(supplied_quantizer)

    dynamic = diac_literal_numeric_source()
    dynamic.update(availability(False, "dynamic_scale_9d7060"))
    row = dynamic["declarations"][1]
    row.update(availability(False, "dynamic_scale_9d7060"), scale_gate_280_raw=7,
               properties=None, metadata_provider_loaded=None, metadata_rows=[])
    normalized = normalize(dynamic)
    assert emit_row(normalized, 0)[0].base_property_block["values_q64"] == expected
    assert emit_row(normalized, 2)[0].base_property_block["values_q64"] == [-70231305300000, 0]
    assert emit_row(normalized, 3)[0].base_property_block["keys_count"] == 0
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_row(normalized, 1)
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit(normalized)
    dynamic_pc = deepcopy(dynamic)
    dynamic_pc["declarations"][1]["properties"] = properties()
    with pytest.raises(ValueError, match="dynamic scale keeps"):
        normalize(dynamic_pc)

    prefix = diac_literal_numeric_source()
    prefix.update(availability(False, "declaration_pointer_unread"), declarations=prefix["declarations"][:1])
    normalized = normalize(prefix)
    assert len(emit_row(normalized, 0)) == 1
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit(normalized)
    for provider_loaded in (False, None):
        missing_provider = diac_literal_numeric_source()
        missing_provider.update(availability(False, "metadata_provider_c85860_unavailable"))
        row = missing_provider["declarations"][0]
        row.update(availability(False, "metadata_provider_c85860_unavailable"),
                   metadata_provider_loaded=provider_loaded, metadata_rows=[])
        normalized = normalize(missing_provider)
        assert normalized["declarations"][0]["properties"]["keys_count"] == 7
        assert len(emit_row(normalized, 2)) == 1
        with pytest.raises(ValueError, match="Required native input unavailable"):
            emit_row(normalized, 0)
    missing_empty_provider = diac_literal_numeric_source()
    missing_empty_provider.update(availability(False, "metadata_provider_c85860_unavailable"))
    missing_empty_provider["declarations"][3].update(availability(False, "metadata_provider_c85860_unavailable"),
                                                   metadata_provider_loaded=False)
    normalized = normalize(missing_empty_provider)
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit_row(normalized, 3)

    missing_flags = diac_literal_numeric_source()
    missing_flags.update(availability(False, "metadata_b8_unavailable"))
    row = missing_flags["declarations"][0]
    row.update(availability(False, "metadata_b8_unavailable"))
    row["metadata_rows"][0]["byte_b8_raw"] = None
    assert len(emit_row(normalize(missing_flags), 1)) == 1
    mismatch = diac_literal_numeric_source()
    mismatch.update(availability(False, "source_property_count_mismatch"))
    mismatch["declarations"][0].update(availability(False, "source_property_count_mismatch"), metadata_rows=[])
    mismatch["declarations"][0]["properties"]["values_count"] = 6
    assert len(emit_row(normalize(mismatch), 2)) == 1
    zero = diac_literal_numeric_source()
    zero.update(declaration_count_raw=0, declaration_array_present=False, declarations=[])
    assert emit(normalize(zero)) == ()
    negative_count = diac_literal_numeric_source()
    negative_count.update(availability(False, "negative_declaration_count"), declaration_count_raw=-1, declarations=[])
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit(normalize(negative_count))
    unread_header_pointer = diac_literal_numeric_source()
    unread_header_pointer.update(availability(False, "declaration_array_unread"), declaration_count_raw=0,
                                 declaration_array_present=None, declarations=[])
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit(normalize(unread_header_pointer))
