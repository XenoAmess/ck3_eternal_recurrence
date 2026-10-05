from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_following_312a950_contract import (
    emit_following_312a950_requests_from_current_source_inputs_12003 as emit,
)

FIELD = "following_government_land_312a950"
MASK = 0x20000000


def availability(ready=True, reason=None):
    return {"status": "available" if ready else "partial", "ready": ready, "reason": reason}


def operand():
    return {"property_identity": None, "property_block": None, "reason": None}


def following312a950_source():
    """Reusable real source input; importing this file does not run the case."""
    full_id = 0xAA000001 - 2**32
    leaf = {**availability(), "character_id": 29829,
        "government_source": {**availability(), "selection": "death_1d0_88",
            "selected_character_identity": "character:29829", "selection_native_index": 0,
            "government_identity": "government:death", "flags_raw_u32": MASK},
        "character_state_present": True,
        "first_land_source": {**availability(), "selection": "living_1c0", "living_present": True,
            "death_present": None, "count_raw": 1, "array_present": True, "full_id_raw": full_id},
        "land_resolution": {**availability(), "selection": "registry_full_id_10", "requested_full_id_raw": full_id,
            "selected_full_id_raw": full_id, "object_identity": "land:first", "magic_u32": 0x4C616E64,
            "full_id_raw": full_id, "admitted": True, "balance_raw_q64": 0},
        "mode3_classifier": None, "provider_selection": None, "stage_selection": "first_land_nonnegative"}
    return {"status": "partial", "ready": False, "character_id": 29829, "branch_291e210": None,
            "reason": "other_person_stages_unobserved", FIELD: leaf}


def test_following312a950_separate_precedence_first_id_full_generation_knownzero_mode3_gap_and_actor():
    raw = following312a950_source()
    before = deepcopy(raw)
    source = normalize_current_context_source_inputs(raw)
    assert raw == before and emit(source) == ()
    assert source[FIELD]["government_source"]["selection"] == "death_1d0_88"
    assert source[FIELD]["first_land_source"]["selection"] == "living_1c0"

    for flags in (0, 0x400, 1 << 28, 1 << 30):
        skipped = following312a950_source()
        leaf = skipped[FIELD]
        leaf["government_source"]["flags_raw_u32"] = flags
        leaf.update(character_state_present=None, first_land_source=None, land_resolution=None,
                    stage_selection="government_bit29_false")
        assert emit(normalize_current_context_source_inputs(skipped)) == ()
    absent = following312a950_source()
    absent[FIELD].update(character_state_present=False, first_land_source=None, land_resolution=None,
                        stage_selection="character_1b0_absent")
    assert emit(normalize_current_context_source_inputs(absent)) == ()
    bad_demand = deepcopy(absent)
    bad_demand[FIELD]["first_land_source"] = raw[FIELD]["first_land_source"]
    with pytest.raises(ValueError, match="undemanded later groups"):
        normalize_current_context_source_inputs(bad_demand)

    for count in (-1, -(2**31), 2):
        selected = following312a950_source()
        selected[FIELD]["first_land_source"]["count_raw"] = count
        assert emit(normalize_current_context_source_inputs(selected)) == ()
    zero = following312a950_source()
    zero[FIELD]["first_land_source"].update(count_raw=0, array_present=None, full_id_raw=-1)
    zero[FIELD]["land_resolution"].update(selection="native_fallback", requested_full_id_raw=None,
                                        selected_full_id_raw=None, full_id_raw=17)
    assert emit(normalize_current_context_source_inputs(zero)) == ()
    death_undemanded = deepcopy(zero)
    death_undemanded[FIELD]["first_land_source"]["death_present"] = True
    with pytest.raises(ValueError, match="undemanded death"):
        normalize_current_context_source_inputs(death_undemanded)
    death = following312a950_source()
    death[FIELD]["government_source"].update(selection="living_1c0_3f8", government_identity="government:related_live",
                                            selected_character_identity="related_character", selection_native_index=2)
    death[FIELD]["first_land_source"].update(selection="death_1d0", living_present=False, death_present=True)
    assert emit(normalize_current_context_source_inputs(death)) == ()
    neither = deepcopy(zero)
    neither[FIELD]["first_land_source"].update(selection="none", living_present=False, death_present=False, count_raw=None)
    assert emit(normalize_current_context_source_inputs(neither)) == ()

    invalid_magic = following312a950_source()
    invalid_magic[FIELD]["land_resolution"].update(magic_u32=0, full_id_raw=None, admitted=False, balance_raw_q64=None)
    invalid_magic[FIELD]["stage_selection"] = "first_land_invalid"
    assert emit(normalize_current_context_source_inputs(invalid_magic)) == ()
    invalid_id = deepcopy(invalid_magic)
    invalid_id[FIELD]["land_resolution"].update(selection="native_fallback", selected_full_id_raw=None,
                                               magic_u32=0x4C616E64, full_id_raw=-1)
    assert emit(normalize_current_context_source_inputs(invalid_id)) == ()
    nonnegative = following312a950_source()
    nonnegative[FIELD]["land_resolution"]["balance_raw_q64"] = 2**63 - 1
    assert emit(normalize_current_context_source_inputs(nonnegative)) == ()
    bad_generation = following312a950_source()
    bad_generation[FIELD]["land_resolution"]["selected_full_id_raw"] = 1
    with pytest.raises(ValueError, match="full-generation"):
        normalize_current_context_source_inputs(bad_generation)

    for loaded in (True, False, None):
        negative = following312a950_source()
        leaf = negative[FIELD]
        leaf.update(availability(False, "mode3_income_2bca580"), stage_selection="negative_land_mode3_income_unobserved")
        leaf["land_resolution"]["balance_raw_q64"] = -1
        leaf["mode3_classifier"] = {**availability(False, "mode3_income_2bca580"), "income_q64": None, "index_raw_i32": None}
        leaf["provider_selection"] = {**availability(False, "mode3_income_2bca580"), "provider_loaded": loaded,
            "count_raw": None, "selection": None, "definition_identity": None, "definition_magic_u32": None,
            "admitted": None, "pc": operand()}
        normalized = normalize_current_context_source_inputs(negative)
        assert normalized[FIELD]["provider_selection"]["provider_loaded"] is loaded
        assert normalized[FIELD]["mode3_classifier"]["reason"] == "mode3_income_2bca580"
        with pytest.raises(ValueError, match="Required native input unavailable"):
            emit(normalized)
        fake_income = deepcopy(negative)
        fake_income[FIELD]["mode3_classifier"]["income_q64"] = 0
        with pytest.raises(ValueError, match="precise unobserved mode3"):
            normalize_current_context_source_inputs(fake_income)
        fake_empty = deepcopy(negative)
        fake_empty[FIELD]["provider_selection"]["pc"].update(property_identity="invented:empty", property_block={
            "keys_count": 0, "values_count": 0, "keys_u16": [], "values_q64": [], "reason": None})
        with pytest.raises(ValueError, match="downstream provider inputs undemanded"):
            normalize_current_context_source_inputs(fake_empty)

    missing_flags = following312a950_source()
    leaf = missing_flags[FIELD]
    leaf.update(availability(False, "government_flags_unavailable"), character_state_present=None,
                first_land_source=None, land_resolution=None, stage_selection=None)
    leaf["government_source"].update(availability(False, "government_flags_unavailable"), flags_raw_u32=None)
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit(normalize_current_context_source_inputs(missing_flags))
    missing_resolver = following312a950_source()
    leaf = missing_resolver[FIELD]
    leaf.update(availability(False, "land_registry_unavailable"), stage_selection=None)
    leaf["land_resolution"].update(availability(False, "land_registry_unavailable"), selection=None,
        selected_full_id_raw=None, object_identity=None, magic_u32=None, full_id_raw=None, admitted=None, balance_raw_q64=None)
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit(normalize_current_context_source_inputs(missing_resolver))
    wrong_actor = following312a950_source()
    wrong_actor[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="character"):
        normalize_current_context_source_inputs(wrong_actor)
