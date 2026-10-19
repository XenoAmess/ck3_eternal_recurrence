"""Three portable full-Service compounds; every Native/OS boundary is synthetic."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
from threading import Lock
import types
import unittest
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
from xar_autoplayer.bridge import service as production
from xar_autoplayer.bridge import ordinary_sway_service_v1 as adapter
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as identity_boundary
from xar_autoplayer.bridge import declaration_opportunity_cooldown_v1 as declaration_cd
from xar_autoplayer.ordinary_war_declared_overview_v1 import _binding as overview_binding
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger
from xar_autoplayer.environment import write_json_atomic

FIXTURE = json.loads((PACKAGE_ROOT / "tests" / "fixtures" /
                      "ordinary_sway_fullplanner_v1.json").read_text(encoding="utf-8"))
ACTUAL_SEM = FIXTURE["semantic"]
ACTUAL_ROOT = FIXTURE["root_result"]
ACTUAL_CAPS = FIXTURE["capabilities"]
ACTUAL_PLAN = FIXTURE["baseline_plan"]
ACTUAL_SAVE = FIXTURE["checkpoint_result"]
ACTOR = ACTUAL_SEM["played_character"]["character_id"]
EXE = ACTUAL_ROOT["campaign_root_context"]["provenance"]["executable_sha256"]
STEP = adapter.STEP

class DriverBase:
    allow_private_active_scheme_sway_query=True
    allow_private_active_scheme_sway_action=True
    allow_private_active_scheme_sway_completion_query=True
    allow_private_active_scheme_sway_completion_termination_query=False
    allow_private_active_scheme_sway_outcome_opinion_query=False
    def __init__(self,path,target=9,opinion=5):
        self.state_dir=path;self.target=target;self.opinion=opinion
        self.revision=11;self.native_revision=21;self.date=1000
        self.capture=1;self.active=False;self.in_planning=False
        self.queries=0;self.submits=0;self.receipts=0;self.completions=0
        self.snapshots=0;self.advances=0;self.fail_once=False
        self.selected="life-advance";self.hooks=[]
    def take_snapshot(self):
        self.snapshots+=1
        return {"snapshot_id":str(self.revision),"revision":self.revision,
            "native_revision":self.native_revision,"date_raw":self.date,
            "paused":True,"map_ready":True,"episode_run_id":"synthetic",
            "episode_character_id":7,"one_life_terminal_reason":None,
            "played_character":{"character_id":7,"alive":True},
            "active_context":{"active_event":None,"pending_character_interaction":None}}
    def query_active_scheme_sway_target_private_v1(self,*,expected_revision,target_character_id):
        if self.in_planning: raise RuntimeError("Native query under plan lock")
        if expected_revision!=self.revision: raise ValueError("wrong source revision")
        self.queries+=1
        if self.fail_once:
            self.fail_once=False;self.revision+=1
            raise BridgeUnavailableError("synthetic optional query failure")
        self.capture+=1
        return {"schema":"active-scheme-sway-private-read-v1","exact_ck3_build":"1.20.0.4",
            "exe_sha256":EXE,"queried_snapshot_id":str(self.revision),
            "queried_revision":self.revision,"queried_native_revision":self.native_revision,
            "snapshot_revision":self.native_revision,"date_raw":self.date,
            "post_snapshot_id":str(self.revision),"actor_character_id":7,
            "target_character_id":target_character_id,"capture_epoch":self.capture,
            "container_generation":1,"target_opinion_of_actor":self.opinion,
            "active_scheme_count":int(self.active),"matching_sway_active":self.active,
            "native_complete_can_send":not self.active,"native_legal_now":not self.active,
            "active_sway_instances":([{"scheme_instance_id":16777233,
                "scheme_instance_generation":1,"target_character_id":target_character_id}] if self.active else [])}
    def submit_active_scheme_sway_private_v1(self,*,readback,action_id):
        if self.in_planning: raise RuntimeError("submit under plan lock")
        self.submits+=1;self.active=True;self.action_id=action_id
        return {"status":"accepted_pending_only"}
    def query_active_scheme_sway_receipt_private_v1(self,*,target_character_id,action_id,expected_revision,pre_capture_epoch):
        self.receipts+=1
        return {"schema":"active-scheme-sway-formal-private-v1","stage":"applied",
            "postcondition_verified":True,"action_id":action_id,"actor_character_id":7,
            "target_character_id":target_character_id,"scheme_instance_id":16777233,
            "scheme_instance_generation":1}
    def completion(self,**arguments):
        if self.in_planning: raise RuntimeError("completion under plan lock")
        self.completions+=1
        if arguments["target_character_id"]!=self.target: raise ValueError("wrong target")
        return {"status":"available","queried_snapshot_id":str(self.revision),
            "queried_revision":self.revision,"queried_native_revision":self.native_revision,
            "date_raw":self.date}
    def execute(self,step,*,expected_revision):
        if expected_revision!=self.revision: raise ValueError("wrong actual execution frame")
        if step not in {"life-advance","synthetic-war-mandatory"}: raise ValueError(step)
        self.advances+=1;self.date+=24;self.native_revision+=1;self.revision+=1
        return {"status":"applied","actual_step":step,"date_raw":self.date}

def overlay_for(driver):
    def before_submit(job):
        driver.hooks.append(copy.deepcopy(job))
        return None
    return before_submit

class ClosedShapeDriver(DriverBase):
    """No Native/OS access; actual closed shape plus explicit synthetic deltas."""
    def __init__(self,path,*,peace=True,opinion=5):
        super().__init__(path,target=ACTUAL_ROOT["campaign_root_context"]["direct_landed_vassal_character_ids"][0],opinion=opinion)
        self.base=copy.deepcopy(ACTUAL_SEM)
        # Strip unrelated diagnostic telemetry only. Keep exact build identity.
        diag=self.base["diagnostics"]
        self.base["diagnostics"]={k:copy.deepcopy(diag[k]) for k in ("bridge_pid","connection_generation","hello")}
        self.revision=self.base["revision"];self.native_revision=self.base["native_revision"]
        self.date=self.base["date_raw"]
        # Reconstructed historical row anchored to actual closed SAVE13, not
        # a claim that this transcript was present in the fresh SEM.
        self.history=[{"index":1,"command":"save-checkpoint","ok":True,
                       "result":copy.deepcopy(ACTUAL_SAVE)}]
        self.trace=[];self.root_publications=0
        self.family_retry=False;self.family_calls=0;self.waits=0
        self._session_bridge_pid=self.base["diagnostics"]["bridge_pid"]
        self.peace=peace;self.planning_entries=0;self.root_enabled=True
        if peace:
            # This is an explicitly synthetic peaceful opportunity, not live.
            self.base.update(active_wars=[],player_armies=[],
                war_results_window_v1_check_due=False,
                war_results_window_v1_observation=None,
                war_results_window_v1_query_attempt=None,
                war_results_window_v1_close_pending=None,
                war_declared_overview_v1_observation=None,
                war_declared_overview_v1_query_attempt=None,
                war_declared_overview_v1_close_pending=None)
            frame=production.GameplayBridgeService._observed_planning_source_frame(self.base)
            state=declaration_cd._new(frame)
            state.update(consecutive_no_war_rounds=2,cooldown_until_date_raw=self.date+720)
            write_json_atomic(path/declaration_cd.FILENAME,state)
        self.publish_root(initial=True)
    def publish_root(self,*,initial=False):
        # Initial row is the actual same-frame closed Root. Later rows are
        # explicitly synthetic new-frame observations from this test Driver.
        result=copy.deepcopy(ACTUAL_ROOT)
        if not initial:
            result.update(queried_snapshot_id=f"native:{self.native_revision}",
                queried_revision=self.revision,queried_native_revision=self.native_revision,
                snapshot_revision=self.native_revision,date_raw=self.date)
            result["campaign_root_context"].update(snapshot_revision=self.native_revision,date_raw=self.date)
            result["query_sequence"]+=self.root_publications
        self.history.append({"index":len(self.history)+1,"command":"query-campaign-root-context-v1",
                             "ok":True,"result":result})
        self.root_publications+=1
    def frame(self,*,history=False):
        frame=copy.deepcopy(self.base)
        frame.update(snapshot_id=f"native:{self.native_revision}",revision=self.revision,
                     native_revision=self.native_revision,date_raw=self.date)
        if self.peace:
            frame["war_declared_overview_v1_observation"]={**overview_binding(frame),
                "sdk_validation_schema":"war-declared-overview-source-v1","available":True,
                "post_observed":True,"scope_unchanged":True,
                "post_window_present":False,"post_effective_visible":False}
        if history:frame["native_command_history"]=copy.deepcopy(self.history)
        return frame
    def take_snapshot(self):
        self.snapshots+=1;return self.frame(history=True)
    def take_snapshot_without_native_command_history(self):
        self.snapshots+=1;return self.frame()
    def take_internal_semantic_snapshot(self):
        self.snapshots+=1;return self.frame()
    def _with_internal_planning_view(self,snapshot,callback):
        self.in_planning=True;self.planning_entries+=1
        try:return callback(snapshot,self.history if self.root_enabled else [
                row for row in self.history if row.get("command")!="query-campaign-root-context-v1"])
        finally:self.in_planning=False
    def _history_snapshot(self):return copy.deepcopy(self.history)
    def capabilities(self):return copy.deepcopy(ACTUAL_CAPS)
    def query_active_scheme_sway_target_private_v1(self,**arguments):
        self.trace.append(("sway-query",self.revision,self.in_planning))
        result=super().query_active_scheme_sway_target_private_v1(**arguments)
        result["actor_character_id"]=ACTOR
        return result
    def query_active_scheme_sway_receipt_private_v1(self,**arguments):
        result=super().query_active_scheme_sway_receipt_private_v1(**arguments)
        result["actor_character_id"]=ACTOR
        return result
    def query_active_scheme_sway_completion_private_v1(self,**arguments):
        self.trace.append(("completion",self.revision,self.in_planning))
        basic=self.completion(**arguments)
        return {**basic,"schema":"xar.ck3.sway_completion.v1","available":True,
            "exact_ck3_build":"1.20.0.4","exe_sha256":EXE,
            "snapshot_revision":self.native_revision,"actor_character_id":ACTOR,
            "target_character_id":arguments["target_character_id"],
            "scheme_instance_id":arguments["scheme_instance_id"],"scheme_instance_generation":1,
            "native_terminal_state_observed":False,"exact_instance_join_ready":True,
            "owner_matches_actor":True,"native_status_observed":True,"native_status_raw":0,
            "native_status_key":"active","terminal_cause_observed":False,"terminal_cause":None,
            "instance_source_observed":True,"instance_present":True,"storage_slot_reused":False,
            "native_owner_raw":ACTOR}
    def execute_step(self,step,*,expected_revision):
        self.trace.append(("execute",step,expected_revision,self.in_planning))
        result=self.execute(step,expected_revision=expected_revision)
        self.history.append({"index":len(self.history)+1,"command":step,"ok":True,"result":result})
        self.publish_root()
        return result
    def query_current_first_heir_relationship_private_v1(self,*,expected_native_revision,**kwargs):
        self.family_calls+=1
        if self.family_retry and self.family_calls==1:
            error=BridgeUnavailableError("synthetic rejected Root read")
            error.native_error="campaign-root snapshot changed or is not ready"
            self.history.append({"index":len(self.history)+1,"command":"query-campaign-root-context-v1",
                                 "ok":False,"error":str(error)})
            raise error
        if expected_native_revision!=self.native_revision:raise ValueError("family stale native")
        return {"schema":"xar.ck3.current-first-heir-relationship.v1",
            "status":"unavailable","read_only":True,"advertised":False,
            "native_revision":self.native_revision,"exact_ck3_build":"1.20.0.4",
            "exe_sha256":EXE,"heir_character_id":None,"betrothed_character_id":None,
            "primary_spouse_character_id":None,"spouse_character_ids":[]}
    def wait_for_change(self,revision,*,timeout_seconds):
        if not self.family_retry or revision!=self.revision:raise ValueError("unexpected retry wait")
        self.waits+=1;self.revision+=1;self.native_revision+=1
        # Deliberately no refreshed Root row: the original production retry
        # requires exactly one failed Root row after the old history prefix.
        return self.frame(history=True)

def service(driver):
    result=object.__new__(production.GameplayBridgeService)
    result.driver=driver
    result._war_overview_query_lock_v1=Lock()
    result._war_overview_query_frame_v1=None
    result._last_war_lifestyle_observation=None
    result._last_war_family_observation=None
    result._opening_martial_episode_v1=None
    result._opening_martial_observation_v1=None
    result._auto_camera_worker=types.SimpleNamespace(schedule=lambda _:{"status":"synthetic-no-presentation"})
    # No replacement of plan_turn, _plan_turn_internal, strategy, execution,
    # following, lifecycle, family/arbitration, or cooldown consumers.
    return result

class NamedBaselineDriver(ClosedShapeDriver):
    allow_private_active_scheme_sway_outcome_opinion_query=True
    def __init__(self,path,*,fail=False):
        super().__init__(path)
        self.opinion_reads=0;self.fail_opinion=fail
        self.named_points=0;self.ended=False
    def query_active_scheme_sway_receipt_private_v1(self,**arguments):
        # Explicit synthetic endpoint upgrade to the complete .4 source pair;
        # the older fixture receipt lacks build fields needed by common-end.
        return {**super().query_active_scheme_sway_receipt_private_v1(**arguments),
                "exact_ck3_build":"1.20.0.4","exe_sha256":EXE,
                "post_capture_epoch":self.capture,"post_date_raw":self.date}
    def query_active_scheme_sway_completion_private_v1(self,**arguments):
        result={**super().query_active_scheme_sway_completion_private_v1(**arguments),
                "native_status_key":"continue","owner_cleared":False,"terminal_cause":"unknown"}
        if self.ended:
            result.update(native_status_key="terminated_unattributed",owner_cleared=True,
                owner_matches_actor=False,native_owner_raw=0xFFFFFFFF,native_status_raw=1,
                native_terminal_state_observed=True)
        return result
    def query_active_scheme_sway_outcome_opinion_private_v1(self,*,expected_revision,target_character_id):
        assert expected_revision==self.revision and target_character_id==self.target
        assert not self.in_planning
        self.opinion_reads+=1
        if self.fail_opinion:raise BridgeUnavailableError("synthetic early baseline read failed")
        return {"schema":"xar.ck3.sway-outcome-opinion-v1","available":True,
            "actor_character_id":ACTOR,"target_character_id":self.target,
            "exact_ck3_build":"1.20.0.4","exe_sha256":EXE,
            "snapshot_revision":self.native_revision,"date_raw":self.date,
            "target_opinion_of_actor":self.opinion,
            "scheme_sway_opinion":{"observed":True,"present":bool(self.named_points),
                "value":self.named_points or None},
            "sway_blocker_opinion":{"observed":True,"present":False,"value":None},
            "instance_terminal_outcome_observed":False,"cancel_outcome_observed":False}


class FullPlannerIntegration(unittest.TestCase):
    def test_monthly_named_gain_reaches_real_consumers_before_termination_red(self):
        # Real full planner/Service/ledger consumers; Native and OS are synthetic.
        class TerminationRedDriver(NamedBaselineDriver):
            def __init__(self, path):
                super().__init__(path)
                self.termination_reads = 0
            def query_active_scheme_sway_outcome_opinion_private_v1(self, **arguments):
                return {**super().query_active_scheme_sway_outcome_opinion_private_v1(**arguments),
                        "status": "available", "queried_revision": self.revision,
                        "queried_native_revision": self.native_revision}
            def query_active_scheme_sway_completion_termination_private_v1(self, **arguments):
                self.termination_reads += 1
                self.trace.append(("termination", self.revision, self.in_planning))
                assert arguments == {"expected_revision": self.revision,
                    "target_character_id": self.target, "scheme_instance_id": 16777233,
                    "after_sequence": 0}
                raise BridgeUnavailableError("sway_termination_executor_unavailable")

        with tempfile.TemporaryDirectory(prefix="sway-monthly-red-") as temp:
            d = TerminationRedDriver(Path(temp)); s = service(d)
            s.auto_turn(before_submit=overlay_for(d))
            s.auto_turn()
            original = copy.deepcopy(read_sway_ledger(d.state_dir)["resolved"])
            baseline = original["material_intervention"]
            self.assertFalse(baseline["scheme_sway_opinion"]["present"])
            d.allow_private_active_scheme_sway_completion_termination_query = True
            d.named_points = 25
            d.date += 30 * 24; d.native_revision += 1; d.revision += 1
            d.publish_root()
            # Keep the fixture's peaceful declaration cooldown on this new frame.
            frame = production.GameplayBridgeService._observed_planning_source_frame(d.frame())
            cooldown = declaration_cd._new(frame)
            cooldown.update(consecutive_no_war_rounds=2, cooldown_until_date_raw=d.date+720)
            write_json_atomic(d.state_dir/declaration_cd.FILENAME, cooldown)
            current_date, current_native = d.date, d.native_revision
            previous_reads, previous_submits = d.opinion_reads, d.submits
            refreshed = s.auto_turn(before_submit=overlay_for(d))
            optional = refreshed["ordinary_sway_optional"]
            observation = optional["result"]
            self.assertEqual(optional["job"], "observe_applied")
            self.assertEqual(observation["status"], "query_failed")
            self.assertTrue(observation["same_frame"])
            self.assertEqual(observation["reads"]["opinion"]["status"], "available")
            self.assertEqual(observation["reads"]["opinion"]["read_date_raw"], current_date)
            self.assertIn("sway_termination_executor_unavailable",
                          observation["reads"]["termination"]["error"])
            self.assertEqual((d.opinion_reads, d.termination_reads, d.submits),
                             (previous_reads+1, 1, previous_submits))
            final = read_sway_ledger(d.state_dir)["resolved"]
            gain = final["first_named_gain_intervention"]
            self.assertEqual(gain["source_date_raw"], current_date)
            self.assertEqual(gain["source_native_revision"], current_native)
            self.assertEqual(gain["baseline_source_date_raw"], baseline["source_date_raw"])
            self.assertTrue(final["material_intervention"]["incremental_named_gain_observed"])
            self.assertTrue(gain["next_turn_consumed"])
            self.assertGreater(gain["following_native_revision"], current_native)
            self.assertEqual(refreshed["sway_following_turn"]["first_named_gain_intervention"], gain)
            for key in ("action_id", "native_receipt", "applied_instance_observation",
                        "pre_capture_epoch", "post_capture_epoch", "post_date_raw"):
                self.assertEqual(final[key], original[key])
            self.assertFalse(final["terminal_intervention"]["instance_terminal_outcome_observed"])
            self.assertIsNone(read_sway_ledger(d.state_dir)["pending"])

    def test_early_baseline_named_gain_and_exact_terminal_reach_ordinary_following(self):
        # Synthetic Native endpoints; later explicit reads do not qualify
        # automatic cadence, retained common-end capture or a natural outcome.
        with tempfile.TemporaryDirectory(prefix="sway-chain-") as temp:
            d=NamedBaselineDriver(Path(temp));s=service(d)
            first=s.auto_turn(before_submit=overlay_for(d))
            action=first["result"]["action_id"]
            s.auto_turn()
            def read_pair():
                args={"expected_revision":d.revision,"target_character_id":d.target}
                s.query_active_scheme_sway_completion_private_v1(**args,scheme_instance_id=16777233)
                s.query_active_scheme_sway_outcome_opinion_private_v1(**args)
                return read_sway_ledger(d.state_dir)["resolved"]
            d.named_points=25
            gain=read_pair()["first_named_gain_intervention"]
            self.assertFalse(gain["next_turn_consumed"])
            gained=s.auto_turn()["sway_following_turn"]
            self.assertTrue(gained["first_named_gain_intervention"]["next_turn_consumed"])
            d.ended=True;d.active=False
            terminal=read_pair()
            self.assertFalse(terminal["material_intervention"]["incremental_named_gain_observed"])
            self.assertFalse(terminal["terminal_intervention"]["next_turn_consumed"])
            retarget=s.auto_turn()
            self.assertEqual(retarget["selected_step"],STEP)
            self.assertNotEqual(retarget["result"]["action_id"],action)
            self.assertNotIn("sway_following_turn",retarget)
            d.ended=False;d.named_points=0
            following=s.auto_turn()["sway_following_turn"]
            final=next(row for row in following["previous_interventions"] if row["action_id"]==action)
            end=final["terminal_intervention"]
            self.assertTrue(end["next_turn_consumed"])
            self.assertTrue(end["instance_terminal_outcome_observed"])
            self.assertFalse(end["terminal_cause_observed"])
            self.assertEqual(end["terminal_cause"],"unknown")
            self.assertEqual((end["action_id"],end["scheme_instance_id"]),(action,16777233))
            self.assertEqual(final["first_named_gain_intervention"],gained["first_named_gain_intervention"])
            self.assertEqual(d.submits,2)

    def test_post_start_ack_or_foreign_action_cannot_observe(self):
        from xar_autoplayer.bridge.ordinary_sway_quiet_observation_v1 import observe_sway_after_applied_start_v1
        with tempfile.TemporaryDirectory(prefix="sway-early-guard-") as temp:
            d=NamedBaselineDriver(Path(temp));d.allow_private_active_scheme_sway_outcome_opinion_query=False
            s=service(d);planned=s.plan_turn();original=s.auto_turn()
            d.allow_private_active_scheme_sway_outcome_opinion_query=True
            before=d.snapshots
            for change in ("pending","foreign"):
                outcome=copy.deepcopy(original)
                if change=="pending":outcome["result"]["status"]="receipt_pending"
                else:
                    outcome["result"]["action_id"]="foreign-start"
                    outcome["ordinary_sway_optional"]["result"]["action_id"]="foreign-start"
                self.assertIs(observe_sway_after_applied_start_v1(s,planned,outcome),outcome)
            self.assertEqual((d.submits,d.opinion_reads,d.snapshots),(1,0,before))

    def test_full_planner_early_baseline_after_start_and_read_failure_never_replays_start(self):
        for fail in (False,True):
            with self.subTest(fail=fail),tempfile.TemporaryDirectory(prefix="sway-early-") as temp:
                d=NamedBaselineDriver(Path(temp),fail=fail);s=service(d)
                date=d.date
                first=s.auto_turn(before_submit=overlay_for(d))
                self.assertEqual(first["selected_step"],STEP)
                self.assertTrue(first["result"]["postcondition_verified"])
                self.assertEqual(first["ordinary_sway_optional"]["outcome"],"applied")
                observation=first["ordinary_sway_post_start_observation"]
                self.assertEqual(observation["schedule_window"],"after_completed_ordinary_sway_start")
                self.assertFalse(observation["submit_attempted"])
                self.assertEqual(observation["new_game_days"],0)
                self.assertEqual((d.submits,d.opinion_reads,d.advances,d.date),(1,1,0,date))
                resolved=read_sway_ledger(d.state_dir)["resolved"]
                if fail:
                    self.assertNotIn("material_intervention",resolved)
                    self.assertIn("synthetic early baseline read failed",str(observation))
                else:
                    baseline=resolved["material_intervention"]
                    self.assertEqual(baseline["source_date_raw"],date)
                    self.assertFalse(baseline["incremental_named_gain_observed"])
                    self.assertFalse(baseline["next_turn_consumed"])
                second=s.auto_turn(before_submit=overlay_for(d))
                self.assertEqual(second["selected_step"],"life-advance")
                self.assertEqual((d.submits,d.opinion_reads,d.advances),(1,1,1))
                self.assertNotIn("ordinary_sway_post_start_observation",second)
                if not fail:
                    self.assertTrue(read_sway_ledger(d.state_dir)["resolved"]["material_intervention"]["next_turn_consumed"])

    def test_closed_root_war_priority_and_full_normal_once_only_following_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix="sway-fixture-") as temp:
            d=ClosedShapeDriver(Path(temp),peace=False);s=service(d)
            actual=s.plan_turn()
            self.assertEqual(actual["plan"]["selected_step"],ACTUAL_PLAN["plan"]["selected_step"])
            self.assertEqual(actual["plan"]["policy"],ACTUAL_PLAN["plan"]["policy"])
            self.assertEqual(actual[adapter.INPUT]["root"]["direct_landed_vassal_character_ids"],
                ACTUAL_ROOT["campaign_root_context"]["direct_landed_vassal_character_ids"])
            self.assertEqual((d.queries,d.submits),(0,0))
        with tempfile.TemporaryDirectory(prefix="sway-fixture-") as temp:
            d=ClosedShapeDriver(Path(temp));s=service(d)
            planned=s.plan_turn()
            self.assertEqual(planned["plan"]["selected_step"],STEP)
            self.assertEqual(planned[adapter.INPUT]["root"]["direct_landed_vassal_character_ids"],
                ACTUAL_ROOT["campaign_root_context"]["direct_landed_vassal_character_ids"])
            self.assertEqual(planned["plan"]["ordinary_sway_job_v1"]["target_character_id"],d.target)
            self.assertEqual((d.queries,d.submits),(0,0))
            first=s.auto_turn(before_submit=overlay_for(d))
            self.assertEqual(first["selected_step"],STEP)
            self.assertTrue(first["result"]["postcondition_verified"])
            original=first["result"]["action_id"]
            self.assertEqual((d.submits,d.queries,d.receipts),(1,2,1))
            second=s.auto_turn(before_submit=overlay_for(d))
            self.assertEqual(second["selected_step"],"life-advance")
            self.assertEqual(second["ordinary_sway_optional"]["result"]["original_action_id"],original)
            self.assertEqual(second["sway_following_turn"]["action_id"],original)
            self.assertTrue(second["sway_following_turn"]["next_turn_consumed"])
            retained=read_sway_ledger(d.state_dir)["resolved"]
            self.assertEqual(retained["native_receipt"]["action_id"],original)
            self.assertTrue(retained["latest_instance_observation"]["tracked_instance_active"])
            s.auto_turn(before_submit=overlay_for(d))
            self.assertEqual((d.submits,d.completions),(1,1))
            self.assertGreaterEqual(d.planning_entries,4)
            self.assertTrue(all(row[-1] is False for row in d.trace))
            self.assertEqual(d.hooks[0]["plan"]["ordinary_sway_job_v1"]["target_character_id"],d.target)

    def test_full_planner_noop_fallback_root_absence_and_real_monthly_cd(self):
        with tempfile.TemporaryDirectory(prefix="sway-fixture-") as temp:
            d=ClosedShapeDriver(Path(temp),opinion=80);s=service(d)
            one=s.auto_turn(before_submit=overlay_for(d))
            self.assertEqual(one["selected_step"],"life-advance")
            self.assertEqual(one["ordinary_sway_optional"]["outcome"],"no_operation")
            two=s.auto_turn()
            self.assertEqual(two["ordinary_sway_optional"]["scheduler_state"]["no_operation_count"],2)
            s.auto_turn()
            self.assertEqual((d.submits,d.queries,d.advances),(0,2,3))
            self.assertGreaterEqual(d.planning_entries,5)
        with tempfile.TemporaryDirectory(prefix="sway-fixture-") as temp:
            d=ClosedShapeDriver(Path(temp));d.root_enabled=False;s=service(d)
            result=s.auto_turn()
            self.assertEqual(result["selected_step"],"life-advance")
            self.assertEqual((d.queries,d.submits,d.advances),(0,0,1))

    def test_full_production_family_retry_skips_old_optional_frame_without_cd(self):
        with tempfile.TemporaryDirectory(prefix="sway-fixture-") as temp:
            d=ClosedShapeDriver(Path(temp));d.family_retry=True
            d.allow_private_family_marriage_formal_trial=True
            d.allow_private_current_first_heir_betrothal_fulfillment=True
            d.allow_private_current_first_heir_relationship_query=True
            s=service(d)
            pending={"stage":"receipt_pending","action_id":"retained-original",
                "actor_character_id":ACTOR,"target_character_id":d.target,
                "ack":{"receipt":"retained-receipt"}}
            write_json_atomic(d.state_dir/LEDGER_FILE,
                {"schema":SCHEMA,"pending":pending,"resolved":None})
            before=(d.state_dir/LEDGER_FILE).read_bytes()
            # Explicit synthetic OS identity boundary; no kernel/WMI/process
            # query is reachable. All actual family planner/retry code stays.
            with patch.object(identity_boundary,"read_construction_process_identity_v1",
                    return_value={"pid":d._session_bridge_pid,"creation_date":"synthetic-retained-birth"}), \
                 patch.object(adapter,"_inputs",wraps=adapter._inputs) as optional_io:
                outcome=s.auto_turn(before_submit=overlay_for(d))
            self.assertEqual(optional_io.call_count,0)
            self.assertEqual(d.waits,1)
            self.assertGreaterEqual(d.family_calls,2)
            self.assertEqual(outcome["selected_step"],"life-advance")
            retry=outcome["plan"]["read_only_query_retry"]
            self.assertEqual(retry["fresh_revision"],ACTUAL_SEM["revision"]+1)
            self.assertEqual(d.hooks[0]["revision"],ACTUAL_SEM["revision"]+1)
            self.assertEqual((d.queries,d.submits,d.advances),(0,0,1))
            self.assertEqual(before,(d.state_dir/LEDGER_FILE).read_bytes())
            self.assertFalse((d.state_dir/adapter.STATE_FILE).exists())

if __name__=="__main__":unittest.main(verbosity=2)
