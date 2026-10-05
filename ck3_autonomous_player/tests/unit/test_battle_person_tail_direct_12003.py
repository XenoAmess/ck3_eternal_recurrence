import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_tail_direct_contract import (
    emit_tail_direct_family_requests_from_current_source_inputs_12003 as emit_family,
    emit_tail_direct_requests_from_current_source_inputs_12003 as emit_sparse,
    normalize_tail_direct_291c5b7_291cc49,
)


FIELD = "tail_direct_291c5b7_291cc49"
GOVERNMENT = "government_870_a30"
WEIGHTED = "carrier_weighted630"
GOVERNMENT_MAGIC = 0x4744624F
SUBCARRIER_MAGIC = 0x5362436F


def pc(empty=False):
    return {"keys_count": 0 if empty else 1, "values_count": None,
            "keys_u16": None if empty else [7], "values_q64": None if empty else [-19],
            "reason": None}


def government():
    return {
        "status": "available", "ready": True, "land_present": True,
        "government_selection": "character_land_1c0_3f8", "government_identity": "government",
        "government_magic_raw": GOVERNMENT_MAGIC, "admitted": True,
        "property_870_identity": "government:870", "property_870": pc(True),
        "second_land_present": True, "subcarrier_magic_raw": SUBCARRIER_MAGIC,
        "subcarrier_full_id_raw": -1, "additional_a30_admitted": True,
        "property_a30_identity": "government:a30", "property_a30": pc(), "reason": None,
    }


def weighted():
    return {
        "status": "available", "ready": True, "carrier_present": True,
        "key_274_raw": -2147483648, "selection": "registry_full_id_8",
        "selected_identity": "weighted:carrier", "count_63c": 3, "array_present": True,
        "rows": [
            {"native_index": index, "property_identity": "weighted:duplicate" if index < 2 else "weighted:last",
             "property_block": pc(), "weight_q64": weight, "reason": None}
            for index, weight in enumerate((0, -170, 2**63 - 1))
        ], "reason": None,
    }


def source():
    return {
        "status": "partial", "ready": False, "character_id": 29829,
        "branch_291e210": None, "reason": "other_person_tail_stages_unobserved",
        FIELD: {"status": "available", "ready": True, "character_id": 29829,
                GOVERNMENT: government(), WEIGHTED: weighted(), "reason": None},
    }


def partial(raw, family, reason):
    leaf = raw[FIELD]
    leaf.update(status="partial", ready=False, reason="tail_direct_families_partial")
    branch = leaf[family]
    branch.update(status="partial", ready=False, reason=reason)
    return branch


def skip_government(branch, *, land=False):
    for key in (
        "government_selection", "government_identity", "government_magic_raw",
        "property_870_identity", "property_870", "second_land_present",
        "subcarrier_magic_raw", "subcarrier_full_id_raw", "additional_a30_admitted",
        "property_a30_identity", "property_a30",
    ):
        branch[key] = None
    branch.update(land_present=land, admitted=False)
    if land:
        branch.update(government_selection="native_government_fallback",
                      government_identity="government:fallback", government_magic_raw=0)


def skip_weighted(branch, *, carrier=False, key=None):
    branch.update(carrier_present=carrier, key_274_raw=key, selection=None,
                  selected_identity=None, count_63c=None, array_present=None, rows=[])


def test_sparse_tail_native_order_skips_signed_weights_independent_families_and_actor():
    normalized = normalize_current_context_source_inputs(source())
    leaf = normalized[FIELD]
    requests = emit_sparse(normalized)
    assert normalized["ready"] is False and leaf["ready"] is True
    assert [(r.source_name, r.source_ordinal, r.first_row_index) for r in requests] == [
        ("291c5e4_government870", 0, 0), ("291c61b_governmenta30", 1, 0),
        ("291cc49_carrier_weighted630", 2, 0), ("291cc49_carrier_weighted630", 2, 1),
        ("291cc49_carrier_weighted630", 2, 2),
    ]
    assert [r.weight_q64 for r in requests] == [100000, 100000, 0, -170, 2**63 - 1]
    assert all(r.row_count == 1 for r in requests)
    assert requests[0].definition_identity == "government:870"
    assert requests[0].base_property_block is leaf[GOVERNMENT]["property_870"]
    assert requests[0].base_property_block["keys_count"] == 0
    assert requests[1].base_property_block is leaf[GOVERNMENT]["property_a30"]
    assert requests[2].definition_identity == requests[3].definition_identity == "weighted:duplicate"
    assert requests[2].base_property_block is leaf[WEIGHTED]["rows"][0]["property_block"]
    assert requests[3].base_property_block is leaf[WEIGHTED]["rows"][1]["property_block"]
    assert emit_family(normalized, GOVERNMENT) + emit_family(normalized, WEIGHTED) == requests
    assert leaf[WEIGHTED]["key_274_raw"] == -2147483648

    # An absent or null optional leaf remains compatible with old producers.
    assert normalize_tail_direct_291c5b7_291cc49(None) is None
    old = source()
    del old[FIELD]
    assert FIELD not in normalize_current_context_source_inputs(old)
    with pytest.raises(ValueError, match="unavailable"):
        emit_sparse(old)
    old[FIELD] = None
    assert normalize_current_context_source_inputs(old)[FIELD] is None
    with pytest.raises(ValueError, match="unavailable"):
        emit_sparse(old)
    mismatch = source()
    mismatch[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="source actor"):
        normalize_current_context_source_inputs(mismatch)
    with pytest.raises(ValueError, match="source actor"):
        emit_sparse(mismatch)

    # Actual null land and wrong government magic are known empty government
    # families. No second-land or subcarrier predicate is manufactured.
    for land in (False, True):
        skipped = source()
        skip_government(skipped[FIELD][GOVERNMENT], land=land)
        actual = normalize_current_context_source_inputs(skipped)
        assert emit_family(actual, GOVERNMENT) == ()
        assert len(emit_family(actual, WEIGHTED)) == 3
        assert actual[FIELD][GOVERNMENT]["additional_a30_admitted"] is None
    # The second land gate only controls A30; bad subcarrier magic admits A30
    # without demanding its full ID. Good magic consumes the exact signed ID.
    for second_land, magic, full_id, admitted in (
        (False, None, None, False), (True, 0, None, True),
        (True, SUBCARRIER_MAGIC, -2, False), (True, SUBCARRIER_MAGIC, 9, False),
    ):
        changed = source()
        gov = changed[FIELD][GOVERNMENT]
        gov.update(second_land_present=second_land, subcarrier_magic_raw=magic,
                   subcarrier_full_id_raw=full_id, additional_a30_admitted=admitted)
        if not admitted:
            gov.update(property_a30_identity=None, property_a30=None)
        assert len(emit_family(normalize_current_context_source_inputs(changed), GOVERNMENT)) == 1 + admitted

    # Null carrier, -1 key and exact zero count skip their undemanded headers.
    for carrier, key in ((False, None), (True, -1)):
        skipped = source()
        skip_weighted(skipped[FIELD][WEIGHTED], carrier=carrier, key=key)
        actual = normalize_current_context_source_inputs(skipped)
        assert emit_family(actual, WEIGHTED) == ()
        assert actual[FIELD][WEIGHTED]["array_present"] is None
        assert len(emit_sparse(actual)) == 2
    zero = source()
    zero[FIELD][WEIGHTED].update(selection="native_fallback", count_63c=0,
                                array_present=None, rows=[])
    actual = normalize_current_context_source_inputs(zero)
    assert emit_family(actual, WEIGHTED) == ()
    minimum = source()
    minimum[FIELD][WEIGHTED]["rows"][0]["weight_q64"] = -(2**63)
    assert emit_family(normalize_current_context_source_inputs(minimum), WEIGHTED)[0].weight_q64 == -(2**63)

    # A missing demanded subcarrier ID is unknown, while the already captured
    # 870 block and the independent weighted family retain their own evidence.
    failed = source()
    gov = partial(failed, GOVERNMENT, "tail_government_subcarrier_id_unavailable")
    gov.update(subcarrier_full_id_raw=None, additional_a30_admitted=None,
               property_a30_identity=None, property_a30=None)
    actual = normalize_current_context_source_inputs(failed)
    assert actual[FIELD][GOVERNMENT]["property_870"]["keys_count"] == 0
    assert len(emit_family(actual, WEIGHTED)) == 3
    with pytest.raises(ValueError, match="unavailable"):
        emit_family(actual, GOVERNMENT)
    with pytest.raises(ValueError, match="unavailable"):
        emit_sparse(actual)
    # A demanded-null subcarrier likewise does not become a false predicate.
    gov.update(subcarrier_magic_raw=None, reason="tail_government_subcarrier_unavailable")
    assert len(emit_family(normalize_current_context_source_inputs(failed), WEIGHTED)) == 3

    # Missing weight/current PC, native null fallback and a raw negative count
    # keep weighted unavailable while government remains independently usable.
    for mode in ("weight", "pc", "fallback", "negative"):
        failed = source()
        branch = partial(failed, WEIGHTED, "tail_weighted_rows_partial")
        if mode in {"weight", "pc"}:
            row = branch["rows"][1]
            row["reason"] = "tail_weighted_row_operands_unavailable"
            if mode == "weight":
                row["weight_q64"] = None
            else:
                row.update(property_identity=None, property_block=None)
        elif mode == "fallback":
            branch.update(selection="native_fallback", selected_identity=None,
                          count_63c=None, array_present=None, rows=None,
                          reason="tail_weighted_native_fallback_null")
        else:
            branch.update(count_63c=-2, array_present=None, rows=None,
                          reason="tail_weighted_negative_count")
        actual = normalize_current_context_source_inputs(failed)
        assert len(emit_family(actual, GOVERNMENT)) == 2
        if mode == "negative":
            assert actual[FIELD][WEIGHTED]["count_63c"] == -2
        with pytest.raises(ValueError, match="unavailable"):
            emit_family(actual, WEIGHTED)

    # Native word widths, booleans and stored order are checked strictly.
    for family, key, value in (
        (GOVERNMENT, "government_magic_raw", True),
        (GOVERNMENT, "government_magic_raw", 2**32),
        (GOVERNMENT, "subcarrier_magic_raw", -1),
        (GOVERNMENT, "subcarrier_full_id_raw", 2**31),
        (WEIGHTED, "key_274_raw", True),
        (WEIGHTED, "key_274_raw", 2**31),
        (WEIGHTED, "carrier_present", 1),
        (WEIGHTED, "count_63c", -(2**31) - 1),
    ):
        malformed = source()
        malformed[FIELD][family][key] = value
        with pytest.raises(ValueError):
            normalize_current_context_source_inputs(malformed)
    for key, value in (("native_index", 1), ("weight_q64", True),
                       ("weight_q64", 2**63), ("weight_q64", -(2**63) - 1)):
        malformed = source()
        malformed[FIELD][WEIGHTED]["rows"][0][key] = value
        with pytest.raises(ValueError):
            normalize_current_context_source_inputs(malformed)
    malformed = source()
    malformed[FIELD][WEIGHTED]["count_63c"] = 2
    with pytest.raises(ValueError, match="native count"):
        normalize_current_context_source_inputs(malformed)
    malformed = source()
    skip_government(malformed[FIELD][GOVERNMENT])
    malformed[FIELD][GOVERNMENT]["additional_a30_admitted"] = False
    with pytest.raises(ValueError, match="undemanded"):
        normalize_current_context_source_inputs(malformed)
    malformed = source()
    malformed[FIELD][GOVERNMENT].update(subcarrier_magic_raw=0, subcarrier_full_id_raw=-1)
    with pytest.raises(ValueError, match="undemanded"):
        normalize_current_context_source_inputs(malformed)
    malformed = source()
    malformed[FIELD][WEIGHTED].update(count_63c=0, array_present=False, rows=[])
    with pytest.raises(ValueError, match="undemanded"):
        normalize_current_context_source_inputs(malformed)
    malformed = source()
    malformed[FIELD]["unknown_stage"] = None
    with pytest.raises(ValueError, match="exactly"):
        normalize_current_context_source_inputs(malformed)
    with pytest.raises(ValueError, match="Unknown tail"):
        emit_family(normalized, "intervening_unknown")
