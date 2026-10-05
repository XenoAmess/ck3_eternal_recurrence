import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_remaining_helpers_contract import (
    emit_helper_291f550_family_requests_from_current_source_inputs_12003 as emit_550_family,
    emit_helper_291f550_requests_from_current_source_inputs_12003 as emit_550,
    emit_helper_291f940_family_requests_from_current_source_inputs_12003 as emit_940_family,
    emit_helper_291f940_requests_from_current_source_inputs_12003 as emit_940,
    emit_later_helpers_requests_from_current_source_inputs_12003 as emit_both,
)


FIELD = "later_helpers_291f550_291f940"
MAGIC = 0x4744624F
MAP = "first_full_id_10_mapping"
KEY_A = "qword:0100000000000080"
KEY_B = "qword:0200000000000080"
KEY_C = "qword:0300000000000080"
KEY_DEFAULT = "qword:0000000000000000"


def pc(empty=False):
    return {"keys_count": 0 if empty else 1, "values_count": None if empty else 1,
            "keys_u16": None if empty else [7], "values_q64": None if empty else [-19],
            "reason": None}


def row(index, identity, *, key=None, magic=None, full_id=None,
        mapping=None, selection="direct_pc_pointer", admitted=True, empty=False):
    return {
        "native_index": index, "source_identity": "source:" + str(index),
        "key_identity": key, "key_magic_raw": magic, "key_full_id_raw": full_id,
        "admitted": admitted, "property_selection": selection if admitted else None,
        "mapping_native_index": mapping, "property_identity": identity if admitted else None,
        "property_block": pc(empty) if admitted else None, "reason": None,
    }


def family(rows, *, array=True):
    return {"status": "available", "ready": True, "admitted": True,
            "count": len(rows), "array_present": array, "rows": rows, "reason": None}


def rite():
    return {
        "first_key_b4_raw": -1426063359, "first_selection": "registry_full_id_8",
        "second_key_4b8_raw": None, "second_selection": "native_fallback",
        "third_key_98_raw": -2, "third_selection": "registry_full_id_8",
        "selected_identity": "rite", "membership_count": 3,
        "membership_array_present": True, "membership_identities": [KEY_A, KEY_B, KEY_DEFAULT],
        "reason": None,
    }


def source():
    mapped = [
        row(0, "mapped:first", key=KEY_A, magic=MAGIC, full_id=-2, mapping=0, selection=MAP),
        row(1, "mapped:first", key=KEY_B, magic=MAGIC, full_id=-2, mapping=0, selection=MAP),
        row(2, None, key=KEY_C, admitted=False),
        row(3, "default:550", key=KEY_DEFAULT, magic=0,
            selection="inline_culture_mapped_default_5dc2380", empty=True),
    ]
    helper550 = {
        "status": "available", "ready": True, "culture_key_b0_raw": -1426063359,
        "culture_selection": "registry_full_id", "culture_identity": "culture",
        "culture_magic_raw": 0x43756C74, "culture_full_id_raw": -2, "admitted": True,
        "government_selection": "character_land_1c0_3f8", "government_identity": "government",
        "government_magic_raw": MAGIC, "government_full_id_raw": -2,
        "government_default_guard_raw": None, "mapped_default_guard_raw": -2, "rite": rite(),
        "government_indexed": family([row(0, "government:pc", selection="government_indexed_1c0")], array=None),
        "culture_direct": family([row(0, "direct:pc"), row(1, "direct:pc")]),
        "culture_mapped": family(mapped), "reason": None,
    }
    inner0 = [
        row(0, "nested:first", key=KEY_A, magic=MAGIC, full_id=-2, mapping=0, selection=MAP),
        row(1, "nested:first", key=KEY_B, magic=MAGIC, full_id=-2, mapping=0, selection=MAP),
        row(2, None, key=KEY_C, admitted=False),
    ]
    inner1 = [
        row(0, "default:940", key=KEY_DEFAULT, magic=0,
            selection="inline_nested_mapped_default_5dc21b0", empty=True),
    ]
    helper940 = {
        "status": "available", "ready": True, "direct_ready": True, "mapped_ready": True,
        "first_key_158_raw": -1426063359, "first_selection": "registry_full_id",
        "second_key_2c_raw": None, "second_selection": "native_fallback",
        "selected_identity": "outer:selected", "outer_count": 2, "outer_array_present": True,
        "outer_rows": [
            {"native_index": 0, "source_identity": "outer:0", "direct_gate_raw": 1,
             "direct_admitted": True, "direct_property_identity": "outer:0:pc",
             "direct_property_block": pc(), "direct_reason": None, "inner_mapped": family(inner0)},
            {"native_index": 1, "source_identity": "outer:1", "direct_gate_raw": -7,
             "direct_admitted": True, "direct_property_identity": "outer:1:pc",
             "direct_property_block": pc(), "direct_reason": None, "inner_mapped": family(inner1)},
        ], "mapped_default_guard_raw": -2, "rite": rite(), "reason": None,
    }
    return {
        "status": "partial", "ready": False, "character_id": 29829,
        "branch_291e210": None, "reason": "other_current_source_inputs_unobserved",
        FIELD: {"status": "available", "ready": True, "character_id": 29829,
                "helper_291f550": helper550, "helper_291f940": helper940, "reason": None},
    }


def partial(raw, helper_name):
    leaf = raw[FIELD]
    leaf.update(status="partial", ready=False, reason="remaining_person_helper_families_partial")
    helper = leaf[helper_name]
    helper.update(status="partial", ready=False, reason="current_family_partial")
    return helper


def unused_rite(reason=None):
    value = dict.fromkeys(rite())
    value["reason"] = reason
    return value


def test_remaining_helpers_native_order_same_actor_partial_families_and_legal_zero():
    normalized = normalize_current_context_source_inputs(source())
    leaf = normalized[FIELD]
    h550, h940 = leaf["helper_291f550"], leaf["helper_291f940"]
    r550, r940 = emit_550(normalized), emit_940(normalized)
    assert [(r.source_ordinal, r.first_row_index, r.definition_identity) for r in r550] == [
        (0, 0, "government:pc"), (1, 0, "direct:pc"), (1, 1, "direct:pc"),
        (2, 0, "mapped:first"), (2, 1, "mapped:first"), (2, 3, "default:550"),
    ]
    assert [(r.source_name, r.source_ordinal, r.first_row_index) for r in r940] == [
        ("291f940_direct160", 0, 0), ("291f940_inner450", 0, 0),
        ("291f940_inner450", 0, 1), ("291f940_direct160", 1, 0),
        ("291f940_inner450", 1, 0),
    ]
    assert r550[3].definition_identity == r550[4].definition_identity
    assert r550[3].base_property_block is h550["culture_mapped"]["rows"][0]["property_block"]
    assert r550[4].base_property_block is h550["culture_mapped"]["rows"][1]["property_block"]
    assert r940[0].base_property_block is h940["outer_rows"][0]["direct_property_block"]
    assert r940[2].base_property_block is h940["outer_rows"][0]["inner_mapped"]["rows"][1]["property_block"]
    assert r940[4].base_property_block is h940["outer_rows"][1]["inner_mapped"]["rows"][0]["property_block"]
    assert emit_both(normalized) == r550 + r940
    assert all(r.weight_q64 == 100000 and r.row_count == 1 for r in emit_both(normalized))
    assert r550[-1].base_property_block["keys_count"] == r940[-1].base_property_block["keys_count"] == 0
    assert normalized["ready"] is False
    assert h550["culture_mapped"]["rows"][1]["mapping_native_index"] == 0
    assert h550["culture_mapped"]["rows"][2]["key_magic_raw"] is None

    mismatch = source()
    mismatch[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="source actor"):
        normalize_current_context_source_inputs(mismatch)
    with pytest.raises(ValueError, match="source actor"):
        emit_both(mismatch)
    old = source()
    del old[FIELD]
    assert FIELD not in normalize_current_context_source_inputs(old)
    old[FIELD] = None
    assert normalize_current_context_source_inputs(old)[FIELD] is None
    with pytest.raises(ValueError, match="unavailable"):
        emit_both(old)

    # Current zero bytes in an uninitialized government default stay partial;
    # the direct and mapped culture families retain their independent value.
    lazy = source()
    h550 = partial(lazy, "helper_291f550")
    h550.update(government_magic_raw=0, government_full_id_raw=None, government_default_guard_raw=0)
    govt = h550["government_indexed"]
    govt.update(status="partial", ready=False, reason="remaining_government_default_not_initialized")
    govt["rows"][0].update(property_selection="inline_government_default_5d65890",
                          property_block=pc(True), reason="remaining_government_default_not_initialized")
    actual = normalize_current_context_source_inputs(lazy)
    assert len(emit_550_family(actual, "culture_direct")) == 2
    assert len(emit_550_family(actual, "culture_mapped")) == 3
    with pytest.raises(ValueError, match="unavailable"):
        emit_550(actual)

    # A 940 mapped failure preserves direct160; a direct160 failure preserves
    # the ordered mapped occurrences, without presenting either as full 940.
    lazy = source()
    h940 = partial(lazy, "helper_291f940")
    h940.update(mapped_ready=False, mapped_default_guard_raw=0)
    inner = h940["outer_rows"][1]["inner_mapped"]
    inner.update(status="partial", ready=False, reason="remaining_mapped_default_not_initialized")
    inner["rows"][0]["reason"] = "remaining_mapped_default_not_initialized"
    actual = normalize_current_context_source_inputs(lazy)
    assert len(emit_940_family(actual, "direct")) == 2
    with pytest.raises(ValueError, match="unavailable"):
        emit_940(actual)
    failed_direct = source()
    h940 = partial(failed_direct, "helper_291f940")
    h940["direct_ready"] = False
    h940["outer_rows"][0].update(direct_gate_raw=None, direct_admitted=None,
                               direct_property_identity=None, direct_property_block=None,
                               direct_reason="remaining_940_direct_gate_unavailable")
    actual = normalize_current_context_source_inputs(failed_direct)
    assert len(emit_940_family(actual, "mapped")) == 3
    with pytest.raises(ValueError, match="unavailable"):
        emit_940(actual)

    # Valid mapped PCs remain useful with an observed unused default guard 0.
    mapped_only = source()
    h550 = mapped_only[FIELD]["helper_291f550"]
    h550["mapped_default_guard_raw"] = 0
    h550["culture_mapped"]["rows"].pop()
    h550["culture_mapped"]["count"] = 3
    actual = normalize_current_context_source_inputs(mapped_only)
    assert len(emit_550_family(actual, "culture_mapped")) == 2

    # Genuine empty lists do not consume Rite selectors or its failure reason.
    zero = source()
    h550 = zero[FIELD]["helper_291f550"]
    h550.update(culture_direct=family([], array=False), culture_mapped=family([], array=False),
                rite=unused_rite("unused_rite_selector_unavailable"), mapped_default_guard_raw=None)
    h940 = zero[FIELD]["helper_291f940"]
    h940.update(rite=unused_rite("unused_rite_selector_unavailable"), mapped_default_guard_raw=None)
    for outer in h940["outer_rows"]:
        outer.update(direct_gate_raw=0, direct_admitted=False, direct_property_identity=None,
                     direct_property_block=None, inner_mapped=family([], array=False))
    actual = normalize_current_context_source_inputs(zero)
    assert len(emit_550(actual)) == 1
    assert emit_940(actual) == ()
    h940.update(outer_count=0, outer_array_present=False, outer_rows=[])
    assert emit_940(normalize_current_context_source_inputs(zero)) == ()

    # Both native whole-Culture skip predicates return three known skips.
    for magic, culture_id in ((0, None), (0x43756C74, -1)):
        skipped = source()
        h550 = skipped[FIELD]["helper_291f550"]
        h550.update(culture_magic_raw=magic, culture_full_id_raw=culture_id, admitted=False,
                    government_selection=None, government_identity=None, government_magic_raw=None,
                    government_full_id_raw=None, government_default_guard_raw=None,
                    mapped_default_guard_raw=None, rite=unused_rite())
        for name in ("government_indexed", "culture_direct", "culture_mapped"):
            h550[name].update(admitted=False, count=None, array_present=None, rows=[])
        assert emit_550(normalize_current_context_source_inputs(skipped)) == ()

    # Native order, signed/u32 word types and full pointer membership stay exact.
    for key, value in (("native_index", 1), ("key_magic_raw", True),
                       ("key_full_id_raw", 2**31), ("mapping_native_index", 4),
                       ("key_identity", KEY_C)):
        malformed = source()
        malformed[FIELD]["helper_291f550"]["culture_mapped"]["rows"][0][key] = value
        with pytest.raises(ValueError):
            normalize_current_context_source_inputs(malformed)
    malformed = source()
    malformed[FIELD]["helper_291f550"]["culture_mapped"]["rows"][2]["property_block"] = pc()
    with pytest.raises(ValueError, match="undemanded"):
        normalize_current_context_source_inputs(malformed)
