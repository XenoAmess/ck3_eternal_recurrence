"""Portable, explicitly synthetic accounting fixtures; no game/tool actions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import root_continuity_window as w

RAW = 53328720
GAME = {"pid":249712,"creation_date":"20261015150508.297017+000"}
FRAME = {"date_raw":RAW,"actor_character_id":40526,
    "episode_run_id":"native-40526-c7a6edcc32b8","snapshot_id":"native:144","native_revision":144,"revision":2}

def details(key="p08-auto18", date=RAW, cycles=6143):
    return {"evidence_id":key,"source":{"fixture":"synthetic:"+key},
        "machine_id":"test-machine","game":GAME,"frame":{**FRAME,"date_raw":date},
        "completed_cycles":cycles,"date_raw":date,"reason":"blocked readonly step requires a human source fix"}

def opened():
    prepared=w.transition(None,"repair_required",details())
    return w.transition(prepared,"attach_verified",details("p09-actual-bootstrap"))

class ContinuityTests(unittest.TestCase):
    def test_prepared_is_not_running_or_old_campaign_credit(self):
        state=w.transition(None,"repair_required",details())
        self.assertEqual(state["status"],"prepared")
        self.assertIsNone(state["start_date_raw"])
        self.assertFalse(w.summary(state)["target_reached"])
        state=w.transition(state,"attach_verified",details("p09-ready"))
        self.assertEqual(state["start_date_raw"],RAW)
        self.assertEqual(state["target_date_raw"],53591712)
        self.assertEqual(state["last_settled_cycles"],6143)

    def test_old_total_thirty_years_cannot_end_new_window(self):
        state=opened()
        old_target=53144328+w.TARGET_RAW
        state=w.transition(state,"settled_batch",details("batch",old_target,6200))
        self.assertFalse(w.summary(state)["target_reached"])
        self.assertEqual(state["status"],"running")

    def test_ceiling_game_day_boundary(self):
        self.assertEqual(w.TARGET_DAYS,10958)
        for delta,complete in ((w.TARGET_RAW-24,False),(w.TARGET_RAW-1,False),(w.TARGET_RAW,True)):
            state=w.transition(opened(),"settled_batch",details(str(delta),RAW+delta,7000))
            self.assertEqual(w.summary(state)["target_reached"],complete)

    def test_manual_query_strategy_classifier_and_harness_repairs_reset_even_zero_actions(self):
        for cause in ("query","strategy","classifier","harness"):
            with self.subTest(cause=cause):
                state=w.transition(opened(),"settled_batch",details("before",RAW+240,6200))
                failed=details(cause,RAW+240,6200)
                state=w.transition(state,"repair_required",failed)
                self.assertEqual(state["status"],"repair_required")
                self.assertFalse(w.summary(state)["target_reached"])
                state=w.transition(state,"attach_verified",details("repair-"+cause,RAW+240,6200))
                self.assertEqual(state["window_id"],2)
                self.assertEqual(state["start_date_raw"],RAW+240)
                self.assertEqual(state["target_date_raw"],RAW+240+w.TARGET_RAW)

    def test_automatic_fallback_retry_save_and_planned_clean_attach_keep_window(self):
        state=opened()
        for index,kind in enumerate(("settled_batch","automatic_recovery","settled_batch","attach_verified"),1):
            state=w.transition(state,kind,details("auto-"+str(index),RAW+index*24,6143+index))
        self.assertEqual(state["window_id"],1)
        self.assertEqual(state["start_date_raw"],RAW)
        self.assertEqual(state["automatic_recovery_count"],1)

    def test_natural_successor_episode_lineage_does_not_reset(self):
        state=opened()
        heir=details("natural-successor",RAW+240,6200)
        heir["frame"].update(actor_character_id=777,episode_run_id="native-777-successor")
        state=w.transition(state,"automatic_recovery",heir)
        self.assertEqual(state["binding_lineage_count"],1)
        self.assertEqual(state["latest_binding"]["actor_character_id"],777)
        self.assertEqual(state["start_date_raw"],RAW)
        self.assertEqual(state["window_id"],1)

    def test_pending_observation_is_not_settled_credit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            state={"before":FRAME,"completed_cycles":6143,
                "pending_cycle":{"global_turn":6144,"unsettled_observed_date_raw":RAW+999}}
            (root/"state.json").write_text(json.dumps(state),encoding="utf-8")
            (root/"launch.json").write_text(json.dumps(GAME),encoding="utf-8")
            (root/"error.json").write_text('{"status":"blocked"}',encoding="utf-8")
            result=w.initialize_repair(root/"ROOT-CONTINUITY-WINDOW.json",root/"state.json",root/"error.json",root/"launch.json","test-machine","real blocked")
            self.assertEqual(result["last_settled_date_raw"],RAW)
            self.assertEqual(result["last_settled_cycles"],6143)

    def test_cross_prefix_store_and_duplicate_evidence_no_reset_or_double_count(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"ROOT-CONTINUITY-WINDOW.json"
            p09=w.WindowLedger(path);p10=w.WindowLedger(path)
            p09.apply("repair_required",details())
            p09.apply("attach_verified",details("p09-ready"))
            automatic=details("p09-readonly-recovery",RAW+24,6144)
            p09.apply("automatic_recovery",automatic)
            p10.apply("automatic_recovery",automatic)
            state=p10.apply("attach_verified",details("p10-ready",RAW+24,6144))
            self.assertEqual(state["automatic_recovery_count"],1)
            self.assertEqual(state["window_id"],1)
            self.assertEqual(state["start_date_raw"],RAW)
            with self.assertRaisesRegex(ValueError,"changed contents"):
                p10.apply("automatic_recovery",{**automatic,"reason":"rewritten evidence"})

    def test_committed_receipt_survives_snapshot_write_failure_without_double_reset(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=w.WindowLedger(Path(d)/"ROOT-CONTINUITY-WINDOW.json")
            original=w._atomic
            def fail_snapshot(path,value,replace=False):
                if path==ledger.path:raise OSError("synthetic snapshot write failure")
                return original(path,value,replace)
            with patch.object(w,"_atomic",side_effect=fail_snapshot),self.assertRaises(OSError):
                ledger.apply("repair_required",details())
            state=ledger.apply("repair_required",details())
            self.assertEqual(state["sequence"],1)
            state=ledger.apply("attach_verified",details("p09-ready"))
            self.assertEqual(state["window_id"],1)

    def test_stale_replayed_batch_cannot_rewind_or_credit_current_window(self):
        state=w.transition(opened(),"settled_batch",details("new",RAW+240,6200))
        self.assertEqual(w.transition(state,"settled_batch",details("old",RAW,6143)),state)
        with self.assertRaises(ValueError):w.transition(state,"settled_batch",details("broken",RAW,6201))

    def test_wrong_game_machine_and_bool_date_are_rejected(self):
        for mutate in (lambda x:x.update(game={**GAME,"pid":999}),
                       lambda x:x.update(machine_id="wrong-machine"),
                       lambda x:x["frame"].update(date_raw=True)):
            bad=details("bad");mutate(bad)
            with self.assertRaises(ValueError):w.transition(opened(),"attach_verified",bad)

if __name__=="__main__":unittest.main(verbosity=2)
