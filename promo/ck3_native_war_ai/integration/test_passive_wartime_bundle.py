"""Pure CASE-C semantic boundaries; no CK3, recorder or media access."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.passive_wartime_bundle import (
    START_DATE, END_DATE, validate_observation_semantics,
    partition_preparation_and_recorded_calls)
from war_ai_promo.gameplay_bundle import GameplayBundleError


def _snapshot(date, revision, paused, history, pending=False):
    return {
        "date_raw":date,"revision":revision,"snapshot_id":f"native:{revision-1}",
        "paused":paused,"map_ready":True,
        "played_character":{"character_id":29829},
        "active_event":None,
        "pending_character_interaction":({"instance_id":16777352,
            "sender_character_id":32522,"auto_accept_notification":False} if pending else None),
        "active_wars":[{"war_id":4,"primary_opponent_character_id":31549,
            "player_side":"attacker","player_relative_war_score":0,
            "allied_armies":[{"army_id":18,"in_combat":False}],
            "enemy_armies":[{"army_id":22,"in_combat":False}]}],
        "native_command_history":copy.deepcopy(history),
    }


def _case():
    base = [{"index":30,"command":"save-checkpoint"}]
    history1 = [*base,{"index":31,"command":"set-speed-2"}]
    history2 = [*history1,{"index":32,"command":"resume-map"}]
    history3 = [*history2,{"index":33,"command":"pause-map"}]
    start = _snapshot(START_DATE,1,True,base)
    calls = []

    def sample(date, paused, history, pending=False):
        revision = 1 + sum(row["tool"] == "ck3_take_snapshot" for row in calls)
        calls.append({"tool":"ck3_take_snapshot","body":_snapshot(date,revision,paused,history,pending)})

    def step(name, expected):
        calls.append({"tool":"ck3_execute_step","arguments":{"step":name,"expected_revision":expected},
            "wrapper_result":"CALL_COMPLETED","body":{"accepted":True}})

    sample(START_DATE,True,base)  # c001
    calls.append({"tool":"ck3_get_capabilities","body":{}})
    sample(START_DATE,True,base)  # c003
    step("set-speed-2",2)
    sample(START_DATE,True,history1)  # c005
    step("resume-map",3)
    for index in range(64):  # c007 ... c070
        day = min(30,index//2+1)
        sample(START_DATE+24*day,False,history2,pending=index==63)
    step("pause-map",67)
    sample(END_DATE,True,history3,pending=True)  # c072
    calls.append({"tool":"ck3_get_war_state","body":{"status":"active",
        "active_wars":[{"war_id":4}]}})
    end = calls[-2]["body"]
    started = {"new_orders_submitted":0,"maximum_game_days":120,
        "maximum_wall_seconds":600,"snapshot":calls[2]["body"]}
    outcome = {"reason":"event_or_interaction","candidate":None,
        "observed_days":30.0,"wall_seconds":37.105,
        "paused_snapshot":end,
        "date_observations":[{"date_raw":date} for date in range(START_DATE,END_DATE+1,24)],
        "war_state":{"status":"active","active_wars":[{"war_id":4}]}}
    return start,calls,outcome,started


def _chronology():
    snapshot = _snapshot(START_DATE,2,True,[])
    def row(tool, sent, received, utc_sent, utc_received, body=None):
        return {"tool":tool,"submitted_at":utc_sent,"received_at":utc_received,
            "submitted_monotonic":sent,"received_monotonic":received,"body":body or {}}
    calls = [
        row("ck3_take_snapshot",98,98.2,"2026-09-22T22:12:58Z","2026-09-22T22:12:58.2Z"),
        row("ck3_get_capabilities",98.3,98.5,"2026-09-22T22:12:58.3Z","2026-09-22T22:12:58.5Z"),
        row("ck3_take_snapshot",101,101.2,"2026-09-22T22:13:01Z","2026-09-22T22:13:01.2Z",snapshot),
        row("ck3_execute_step",101.3,101.5,"2026-09-22T22:13:01.3Z","2026-09-22T22:13:01.5Z"),
    ]
    observed = {"at":"2026-09-22T22:13:01.25Z","monotonic":101.25,"snapshot":snapshot}
    return calls, observed


class PassiveWartimeSemanticsTest(unittest.TestCase):
    def test_exact_passive_window_and_pending_stop(self):
        summary = validate_observation_semantics(*_case())
        self.assertEqual((summary["sample_count"],summary["distinct_dates"]),(68,31))
        self.assertEqual(summary["actual_combat_id"],None)

    def test_new_army_order_is_rejected_even_if_call_list_looks_passive(self):
        case = list(_case())
        case[1][-2]["body"]["native_command_history"].append(
            {"index":34,"command":"move-army-18-to-2638"})
        with self.assertRaises(GameplayBundleError):
            validate_observation_semantics(*case)

    def test_combat_publication_cannot_be_a_zero_contact_result(self):
        case = list(_case())
        case[1][8]["body"]["active_wars"][0]["enemy_armies"][0]["in_combat"] = True
        with self.assertRaises(GameplayBundleError):
            validate_observation_semantics(*case)

    def test_unapproved_player_action_tool_is_rejected(self):
        case = list(_case())
        case[1].insert(12,{"tool":"ck3_move_army","body":{"accepted":True}})
        with self.assertRaises(GameplayBundleError):
            validate_observation_semantics(*case)

    def test_pause_ack_requires_matching_revision(self):
        case = list(_case())
        pause = next(row for row in case[1] if row.get("arguments",{}).get("step") == "pause-map")
        pause["arguments"]["expected_revision"] = 66
        with self.assertRaises(GameplayBundleError):
            validate_observation_semantics(*case)

    def test_terminal_or_missing_interaction_is_not_packaged(self):
        case = list(_case())
        case[2]["candidate"] = {"combat_id":9}
        with self.assertRaises(GameplayBundleError):
            validate_observation_semantics(*case)

    def test_earlier_pending_interaction_would_have_stopped_window(self):
        case = list(_case())
        case[1][10]["body"]["pending_character_interaction"] = {
            "instance_id":16777352,"sender_character_id":32522,"auto_accept_notification":False}
        with self.assertRaises(GameplayBundleError):
            validate_observation_semantics(*case)

    def test_pre_record_read_only_preparation_is_preserved_as_distinct_phase(self):
        calls, observed = _chronology()
        phases = partition_preparation_and_recorded_calls(calls,
            "2026-09-22T22:13:00Z", "2026-09-22T22:13:10Z", 100, observed)
        self.assertEqual((phases["pre_record_call_count"],phases["in_record_call_count"]),(2,2))
        self.assertEqual((phases["pre_record_snapshot_count"],phases["in_record_snapshot_count"]),(1,1))

    def test_pre_record_mutation_or_cross_boundary_receipt_is_rejected(self):
        calls, observed = _chronology()
        calls[1]["tool"] = "ck3_move_army"
        with self.assertRaises(GameplayBundleError):
            partition_preparation_and_recorded_calls(calls,
                "2026-09-22T22:13:00Z", "2026-09-22T22:13:10Z",100,observed)
        calls, observed = _chronology()
        calls[0]["received_monotonic"] = 100.1
        with self.assertRaises(GameplayBundleError):
            partition_preparation_and_recorded_calls(calls,
                "2026-09-22T22:13:00Z", "2026-09-22T22:13:10Z",100,observed)


if __name__ == "__main__":
    unittest.main()
