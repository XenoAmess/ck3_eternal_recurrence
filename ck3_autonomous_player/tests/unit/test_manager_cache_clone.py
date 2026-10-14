from unittest import mock

from xar_autoplayer.bridge import war_contract


def test_shared_manager_validates_once_and_preserves_independent_aliases():
    calls = []

    def normalize(value):
        calls.append(value)
        nested = {"items": [1, 2]}
        return {"left": nested, "right": nested}

    raw = {"valid": True}
    cache = {}
    first = war_contract._normalize_manager_input_once(raw, normalize, cache)
    second = war_contract._normalize_manager_input_once(raw, normalize, cache)
    assert len(calls) == 1
    assert first == second and first is not second
    assert second["left"] is second["right"]
    second["left"]["items"].append(3)
    assert first["left"]["items"] == [1, 2]
    assert raw == {"valid": True}
    war_contract._normalize_manager_input_once({"valid": True}, normalize, cache)
    assert len(calls) == 2


def test_unpicklable_manager_retains_independent_fallback():
    raw, cache = {}, {}
    # Use the same normalizer identity for its actual shared-input cache.
    normalizer = lambda value: {"nested": []}
    first = war_contract._normalize_manager_input_once(raw, normalizer, cache)
    with mock.patch.object(war_contract.pickle, "dumps", side_effect=TypeError("unsupported")):
        second = war_contract._normalize_manager_input_once(raw, normalizer, cache)
    assert second == first and second is not first
    second["nested"].append(1)
    assert first["nested"] == []
