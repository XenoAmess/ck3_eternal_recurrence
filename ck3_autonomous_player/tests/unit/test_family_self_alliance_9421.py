"""Original F93 pair; outer snapshot/chooser/ordinary execution are synthetic."""
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from xar_autoplayer import family_marriage_formal_consumer as family
from xar_autoplayer.bridge import observed_heir_marriage_private_action_v1 as transport
from xar_autoplayer.bridge.driver import BridgeUnavailableError, CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


PAIR = json.loads((Path(__file__).parent / "fixtures" /
                   "alliance9421_closed_pair_v1.json").read_text(encoding="utf-8"))["resolved"]
IDENTITY = (PAIR["post_bridge_pid"], PAIR["post_bridge_creation_date"])
BASE = {"policy": "one-life-turn-v1", "phase": "ordinary_fixture",
        "selected_step": "life-advance", "reason": "synthetic ordinary admission"}


def frame():
    return {"snapshot_id": "native:2668", "revision": 883, "native_revision": 2668,
            "date_raw": 53244000, "episode_run_id": PAIR["episode_run_id"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 40526, "alive": True},
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "player_armies": []}


def plan_pair(pair, snapshot=None, identity=IDENTITY):
    with patch.object(family, "bridge_process_identity", return_value=identity):
        return family._plan_existing_resolution(object(), {"plan": deepcopy(BASE)},
            deepcopy(BASE), pair, snapshot or frame())["plan"]


def test_actual_self_recipient_consumes_original_material_without_alliance_credit():
    pair = deepcopy(PAIR)
    result = plan_pair(pair)
    assert result["selected_step"] == "life-advance"
    assert result["family_marriage_alliance_status"] == "not_applicable_self_recipient"
    assert result["family_marriage_result_consumed"] == PAIR == pair
    assert "alliance_result" not in pair


@pytest.mark.parametrize("where,key,value", [
    ("pending", "schema", "foreign"),
    ("pending", "played_character_id", 31254),
    ("pending", "episode_run_id", "foreign"),
    ("pending", "heir_character_id", 999),
    ("pending", "candidate_character_id", 999),
    ("resolved", "episode_run_id", "foreign"),
    ("resolved", "material_result", False),
    ("snapshot", "episode_run_id", "foreign"),
    ("snapshot", "played_character", {"character_id": 31254, "alive": True}),
])
def test_unknown_bindings_never_claim_self_not_applicable(where, key, value):
    pair, snapshot = deepcopy(PAIR), frame()
    target = (pair["source_pending"] if where == "pending" else
              snapshot if where == "snapshot" else pair)
    target[key] = value
    result = plan_pair(pair, snapshot)
    assert result.get("family_marriage_alliance_status") != "not_applicable_self_recipient"
    assert result["selected_step"] == family.ALLIANCE_RESULT_STEP
    assert "alliance_result" not in pair


def test_external_recipient_still_queries_and_cold_pair_rechecks_material():
    pair = deepcopy(PAIR)
    pair["source_pending"]["recipient_character_id"] = 111
    assert plan_pair(pair)["selected_step"] == family.ALLIANCE_RESULT_STEP
    assert plan_pair(PAIR, identity=(999, "different"))["selected_step"] == family.RESULT_STEP


def test_existing_transport_still_rejects_self_before_any_native_send():
    class Driver:
        def take_snapshot_without_native_command_history(self):
            return frame()
        @property
        def endpoint(self):
            raise AssertionError("no Native send admitted")
    with pytest.raises(BridgeUnavailableError, match="bound material proposal"):
        transport.query_observed_first_heir_marriage_alliance_result_private_v1(
            Driver(), resolved=deepcopy(PAIR), recipient_character_id=40526)


def test_real_service_auto_keeps_ordinary_action_and_exact_ledger(tmp_path):
    ledger = {"schema": "xar.ck3.first-heir-marriage-formal.v1",
              "pending": None, "resolved": deepcopy(PAIR)}
    family._write(tmp_path, ledger)
    path = tmp_path / family._LEDGER
    original = path.read_bytes()
    calls, displays = [], []
    driver = CallbackGameplayDriver(backend_id="native-headless", snapshot=frame,
        execute=lambda step, revision: calls.append((step, revision)) or {"accepted": True},
        action_steps=("life-advance",))
    driver.state_dir = tmp_path
    driver.allow_private_family_marriage_formal_trial = True
    driver.query_observed_first_heir_marriage_alliance_result_private_v1 = (
        lambda **kwargs: transport.query_observed_first_heir_marriage_alliance_result_private_v1(
            driver, **kwargs))
    with patch.object(family, "bridge_process_identity", return_value=IDENTITY), \
            patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=deepcopy(BASE)):
        result = GameplayBridgeService(driver).auto_turn(before_submit=lambda item: displays.append(item))
    assert result["status"] == "executed" and result["selected_step"] == "life-advance"
    assert calls == [("life-advance", 883)] and len(displays) == 1
    assert displays[0]["plan"]["family_marriage_alliance_status"] == "not_applicable_self_recipient"
    assert path.read_bytes() == original
