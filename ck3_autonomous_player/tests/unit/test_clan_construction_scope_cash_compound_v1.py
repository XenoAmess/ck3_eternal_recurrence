"""Portable synthetic Clan construction scene/quote/cash compound.

The seven Clan/Tribal cases preserve the passed external compound's inputs.
Feudal uses its retained qualified result projection plus exact scope delegation.
No CK3, process lookup, desktop, real pipe, native producer or gameplay action.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

from test_construction_formal_private_consumer import Driver, root
from test_construction_monthly_budget_v1 import cash_fixture
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP
from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
from xar_autoplayer import construction_formal_consumer as candidate
from xar_autoplayer.construction_scene_scope_v1 import same_frame_construction_scope_v1
from xar_autoplayer.lifestyle_formal_consumer import _same_frame_feudal_scope

class ControlledDriver(Driver):
 query_construction_cash_outcome_private_v1=NativeHeadlessGameplayDriver.query_construction_cash_outcome_private_v1
 query_war_cash_current_resources_private_v1=NativeHeadlessGameplayDriver.query_war_cash_current_resources_private_v1

 def take_internal_semantic_snapshot(self):
  return self.take_snapshot()

 def wait_for_command_result(self,request_id,timeout):
  request=self.requests[-1]
  if request["step"]==CURRENT_STEP:
   return {"type":"command_result","protocol_version":1,"request_id":request_id,"ok":True,
    "result":{"step":CURRENT_STEP,"accepted":True,"status":"available","private_build":True,
      "read_only":True,"advertised":False,"backend_id":"native-headless",
      "war_cash_current_resources":deepcopy(self.cash)}}
  result=super().wait_for_command_result(request_id,timeout)
  if request["step"]==transport.QUERY_NATIVE:
   world=result["result"]["private_probe"]["player_world_building_sources"]
   if self.non_gold:
    world["legal_samples"][0]["cost_raw_native"][1]=100_000
   if self.illegal:
    world["native_final_legality_evaluated"]=False
  return result


def test_clan_construction_scope_cash_compound_v1(tmp_path):
    OUT = tmp_path
    qualified_feudal_projection = {'feudal-peace': {'selected_step': 'private-submit-player-construction-v1', 'request_steps': ['query-war-cash-current-resources-v1', 'g2_player_construction_view_probe_v1']}, 'feudal-war': {'selected_step': 'private-submit-player-construction-v1', 'request_steps': ['query-war-cash-current-resources-v1', 'g2_player_construction_view_probe_v1']}, 'feudal-net-burn': {'selected_step': 'life-advance', 'request_steps': ['query-war-cash-current-resources-v1', 'g2_player_construction_view_probe_v1']}}

    def configured(name,government="clan_government",*,expenses=380_000,wartime=False,missing_net=False,wrong_actor=False,non_gold=False,illegal=False):
     directory=OUT/"fixture-state"/name
     directory.mkdir(parents=True,exist_ok=False)
     d=ControlledDriver(directory)
     d.non_gold=non_gold;d.illegal=illegal
     d.allow_private_construction_formal_trial=True
     d.snapshot["diagnostics"]={"hello":{
       "expected_ck3_version":CK3_12004.game_version,
       "expected_ck3_sha256":CK3_12004.executable_sha256}}
     if wartime:d.snapshot["active_wars"]=[{"war_id":117440524}]
     d.cash=cash_fixture(gold=50_000_000,gross=450_000,expenses=expenses,current=200_000,all_raised=500_000)
     d.cash.update(snapshot_revision=d.snapshot["native_revision"],date_raw=d.snapshot["date_raw"])
     if missing_net:
      d.cash.update(status="partial",player_monthly_net_income=None,
        monthly_net_income_unavailable_reason="controlled_native_net_missing")
      d.cash["readiness"]["monthly_net_income_ready"]=False
     if wrong_actor:d.cash["played_character_id"]=33441
     history=root()
     flags={"feudal_government":["government_is_feudal"],"clan_government":["government_is_clan"],
            "tribal_government":["government_is_tribal","government_uses_tribal_authority"]}
     history[0]["result"]["campaign_root_context"]["government"]={
      "key":government,"flags":flags[government]}
     return d,history

    def run(module,name,government="clan_government",**options):
     d,history=configured(name,government,**options)
     baseline={"revision":3,"plan":{"policy":"one-life-turn-v1","selected_step":"life-advance"}}
     before=deepcopy(baseline)
     selected=module.plan_construction_private(d,baseline,d.take_snapshot(),history,
       {"life-advance","query-campaign-root-context-v1",module.SUBMIT_STEP})
     if baseline!=before:raise ValueError("Input baseline mutated")
     steps=[r["step"] for r in d.requests]
     if transport.ACTION_NATIVE in steps:raise ValueError("Probe submitted a gameplay action")
     return selected,steps

    observations = []
    for label, options in [
        ("feudal-peace", {}),
        ("feudal-war", {"wartime": True}),
        ("feudal-net-burn", {"expenses": 20_450_000}),
    ]:
        scope_driver, history = configured(label + "-scope", "feudal_government", **options)
        snapshot = scope_driver.take_snapshot()
        if same_frame_construction_scope_v1(snapshot, history) != _same_frame_feudal_scope(
                snapshot, history, require_peace=False):
            raise ValueError(f"Existing feudal scene result changed: {label}")
        selected, steps = run(candidate, label, "feudal_government", **options)
        actual = {"selected_step": selected["plan"]["selected_step"], "request_steps": steps}
        if actual != qualified_feudal_projection[label]:
            raise ValueError(f"Qualified feudal result/query projection changed: {label}")
        observations.append({"case": label, "result": "QUALIFIED_PROJECTION_AND_SCOPE",
                             **actual})

    for label,government,options,expected,expected_queries in [
     ("clan-positive","clan_government",{},candidate.SUBMIT_STEP,2),
     ("clan-net-burn","clan_government",{"expenses":20_450_000},"life-advance",2),
     ("clan-net-missing","clan_government",{"missing_net":True},"life-advance",1),
     ("clan-wrong-cash-actor","clan_government",{"wrong_actor":True},"life-advance",1),
     ("clan-non-gold","clan_government",{"non_gold":True},"life-advance",2),
     ("clan-native-legality-missing","clan_government",{"illegal":True},"life-advance",2),
     ("tribal-non-gold","tribal_government",{"non_gold":True},"life-advance",0),
    ]:
     selected,steps=run(candidate,label,government,**options)
     plan=selected["plan"]
     if plan["selected_step"]!=expected or len(steps)!=expected_queries:
      raise ValueError(f"{label}: expected {expected}/{expected_queries}; got {plan['selected_step']}/{steps}")
     quote=plan.get("construction_private_query")
     if label=="clan-positive":
      if not (quote["world"]["native_final_legality_evaluated"] is True
              and quote["candidate"]["stock_gold_cost_raw"]==15_000_000
              and quote["candidate"]["authored_monthly_income_delta_hundredths"]==35):
       raise ValueError("Clan positive choice bypassed original native quote/value selector")
      budget=quote["construction_monthly_budget"]
      if not (budget["scenarios"]["current"]["net_monthly_gold_raw"]==70_000
              and budget["scenarios"]["current"]["cash_after_construction_and_commitments_raw"]==35_000_000
              and budget["reserve_gold_raw"]==20_000_000
              and budget["scenarios"]["current"]["scenario_floor_ready"] is True):
       raise ValueError("Clan NET/reserve projection changed or did not execute")
      if "pre_cash_v2" not in quote:raise ValueError("Actual cash-v2 packet not retained")
     observations.append({"case":label,"result":"EXPECTED_SCOPE_AND_BUDGET","selected_step":plan["selected_step"],
                          "phase":plan.get("phase"),"request_steps":steps})
    if len(observations) != 10:
        raise ValueError("The new portable compound lost a case")
