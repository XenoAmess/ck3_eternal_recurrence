"""The production helper omits only history; typed outputs and drift gates remain."""

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import MethodType

from xar_autoplayer.bridge.marriage_matchmaking_private_transport import (
    OBSERVED_FIRST_HEIR_MARRIAGE_LEGALITY_STEP_V1,
    query_observed_first_heir_marriage_legality_v1,
)
from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import (
    query_first_heir_candidate_alliance_projection_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError


HERE = Path(__file__).resolve().parent

def fixture_module(name):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location("fixture_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def only_history_free(driver):
    calls = []
    def read(self):
        calls.append(1)
        return self.frames.pop(0)
    def full(self):
        raise AssertionError("full command-history copy is unnecessary")
    driver.take_snapshot_without_native_command_history = MethodType(read, driver)
    driver.take_snapshot = MethodType(full, driver)
    return calls


def test_legal_query_uses_three_history_free_frames_with_equal_output():
    f = fixture_module("test_marriage_matchmaking_private_transport")
    reply = f.PrivateObservedHeirMarriageTransportTests._family_reply(answer=True)
    reply["result"]["step"] = OBSERVED_FIRST_HEIR_MARRIAGE_LEGALITY_STEP_V1
    base = f._Driver(deepcopy(reply), [f._paused_frame() for _ in range(3)])
    expected = query_observed_first_heir_marriage_legality_v1(
        base, expected_native_revision=693)
    candidate = f._Driver(deepcopy(reply), [f._paused_frame() for _ in range(3)])
    calls = only_history_free(candidate)
    actual = query_observed_first_heir_marriage_legality_v1(
        candidate, expected_native_revision=693)
    assert actual == expected and calls == [1, 1, 1]


def test_projection_uses_two_history_free_frames_and_keeps_drift_rejection():
    f = fixture_module("test_marriage_candidate_alliance_private_transport")
    base = f._Driver(f._reply(), [f._frame(), f._frame()])
    expected = query_first_heir_candidate_alliance_projection_private_v1(
        base, legality=f._legality(), candidate_character_ids=f.IDS)
    candidate = f._Driver(f._reply(), [f._frame(), f._frame()])
    calls = only_history_free(candidate)
    actual = query_first_heir_candidate_alliance_projection_private_v1(
        candidate, legality=f._legality(), candidate_character_ids=f.IDS)
    assert actual == expected and calls == [1, 1]
    changed = f._frame()
    changed["date_raw"] += 24
    drifted = f._Driver(f._reply(), [f._frame(), changed])
    only_history_free(drifted)
    try:
        query_first_heir_candidate_alliance_projection_private_v1(
            drifted, legality=f._legality(), candidate_character_ids=f.IDS)
    except BridgeUnavailableError as error:
        assert "frame changed" in str(error)
    else:
        raise AssertionError("a changed date must not pass the history-free read")
