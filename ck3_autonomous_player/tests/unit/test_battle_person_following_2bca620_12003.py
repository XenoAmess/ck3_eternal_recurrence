from copy import deepcopy

import pytest

from xar_autoplayer.bridge.battle_context_source_inputs_contract import normalize_current_context_source_inputs
from xar_autoplayer.bridge.battle_person_following_2bca620_contract import (
    emit_following_2bca620_requests_from_current_source_inputs_12003 as emit,
)

FIELD = "following_2bca620"
Q = 100000


def availability(ready=True, reason=None):
    return {"status": "available" if ready else "partial", "ready": ready, "reason": reason}


def pc(*rows):
    return {"keys_count": len(rows), "values_count": len(rows), "keys_u16": [key for key, _ in rows],
            "values_q64": [value for _, value in rows], "reason": None}


def operand(identity=None, *rows):
    return {"property_identity": identity, "property_block": pc(*rows) if identity else None, "reason": None}


def following2bca620_source():
    """Reusable real main-normalizer input; importing this module runs no case."""
    leaf = {**availability(), "character_id": 29829,
        "balance_source": {"component_present": True, "balance_raw_q64": Q, "numeric_balance_q64": Q, "reason": None},
        "classifier": {**availability(), "selection": "nonnegative_balance_minus_one", "index_raw_i32": -1},
        "provider_selection": {**availability(), "provider_loaded": True, "count_raw": -1,
            "selection": "provider_1690_equality_sentinel", "definition_identity": "provider1690",
            "definition_magic_u32": 0x4744624F, "admitted": True,
            "pc": operand("provider1690:inline40", (11, -2 * Q), (65535, 0))}}
    return {"status": "partial", "ready": False, "character_id": 29829, "branch_291e210": None,
            "reason": "other_person_stages_unobserved", FIELD: leaf}


def test_following2bca620_nonnegative_balance_equality_empty_magic_negative_partial_and_actor():
    raw = following2bca620_source()
    before = deepcopy(raw)
    source = normalize_current_context_source_inputs(raw)
    requests = emit(source)
    assert raw == before and len(requests) == 1
    assert requests[0].weight_q64 == Q and requests[0].source_ordinal == 0 and requests[0].first_row_index == 0
    assert requests[0].base_property_block is source[FIELD]["provider_selection"]["pc"]["property_block"]
    assert requests[0].base_property_block == pc((11, -2 * Q), (65535, 0))

    for present, balance in ((True, 0), (True, 2**63 - 1), (False, None)):
        observed = following2bca620_source()
        observed[FIELD]["balance_source"].update(component_present=present, balance_raw_q64=balance,
                                                numeric_balance_q64=balance if present else 0)
        for count in (-1, -2, 0, 10, 2**31 - 1):
            selected = deepcopy(observed)
            sentinel = count == -1
            selected[FIELD]["provider_selection"].update(count_raw=count,
                selection="provider_1690_equality_sentinel" if sentinel else "global_fallback_5d1e0b0",
                definition_identity="sentinel" if sentinel else "global_fallback", pc=operand("actual:empty40"))
            normalized = normalize_current_context_source_inputs(selected)
            assert normalized[FIELD]["classifier"]["index_raw_i32"] == -1
            assert emit(normalized)[0].base_property_block == pc()

    skipped = following2bca620_source()
    skipped[FIELD]["provider_selection"].update(definition_magic_u32=0, admitted=False, pc=operand())
    assert emit(normalize_current_context_source_inputs(skipped)) == ()
    bad_empty = deepcopy(skipped)
    bad_empty[FIELD]["provider_selection"]["pc"] = operand("invented:magicfalse")
    with pytest.raises(ValueError, match="undemanded PC40"):
        normalize_current_context_source_inputs(bad_empty)
    wrong_equality = following2bca620_source()
    wrong_equality[FIELD]["provider_selection"]["selection"] = "global_fallback_5d1e0b0"
    with pytest.raises(ValueError, match="equality-before-fallback"):
        normalize_current_context_source_inputs(wrong_equality)

    for balance in (-1, -(2**63)):
        negative = following2bca620_source()
        leaf = negative[FIELD]
        leaf.update(availability(False, "negative_balance_income_2bca4e0"))
        leaf["balance_source"].update(balance_raw_q64=balance, numeric_balance_q64=balance)
        leaf["classifier"].update(availability(False, "negative_balance_income_2bca4e0"),
                                 selection="negative_balance_income_unobserved", index_raw_i32=None)
        leaf["provider_selection"].update(availability(False, "classifier_unavailable"), count_raw=None,
            selection=None, definition_identity=None, definition_magic_u32=None, admitted=None, pc=operand())
        normalized = normalize_current_context_source_inputs(negative)
        assert normalized[FIELD]["classifier"]["selection"] == "negative_balance_income_unobserved"
        with pytest.raises(ValueError, match="Required native input unavailable"):
            emit(normalized)
        cached = deepcopy(negative)
        cached[FIELD]["balance_source"]["cached_income_q64"] = 123456
        with pytest.raises(ValueError, match="must contain exactly"):
            normalize_current_context_source_inputs(cached)

    for missing in ("provider", "definition", "pc"):
        partial = following2bca620_source()
        leaf = partial[FIELD]
        leaf.update(availability(False, missing + "_unavailable"))
        provider = leaf["provider_selection"]
        provider.update(availability(False, missing + "_unavailable"))
        if missing == "provider":
            provider.update(provider_loaded=False, count_raw=None, selection=None, definition_identity=None,
                            definition_magic_u32=None, admitted=None, pc=operand())
        elif missing == "definition":
            provider.update(definition_identity=None, definition_magic_u32=None, admitted=None, pc=operand())
        else:
            provider["pc"].update(property_block=None, reason="property_container_unavailable")
        normalized = normalize_current_context_source_inputs(partial)
        assert normalized[FIELD]["classifier"]["ready"]
        with pytest.raises(ValueError, match="Required native input unavailable"):
            emit(normalized)

    missing_balance = following2bca620_source()
    leaf = missing_balance[FIELD]
    leaf.update(availability(False, "balance_unavailable"))
    leaf["balance_source"].update(component_present=None, balance_raw_q64=None, numeric_balance_q64=None, reason="balance_unavailable")
    leaf["classifier"].update(availability(False, "balance_unavailable"), selection=None, index_raw_i32=None)
    leaf["provider_selection"].update(availability(False, "classifier_unavailable"), count_raw=None,
        selection=None, definition_identity=None, definition_magic_u32=None, admitted=None, pc=operand())
    with pytest.raises(ValueError, match="Required native input unavailable"):
        emit(normalize_current_context_source_inputs(missing_balance))
    wrong_actor = following2bca620_source()
    wrong_actor[FIELD]["character_id"] = 29830
    with pytest.raises(ValueError, match="character"):
        normalize_current_context_source_inputs(wrong_actor)
