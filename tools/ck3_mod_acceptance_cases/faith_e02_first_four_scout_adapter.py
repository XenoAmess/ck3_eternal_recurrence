"""C2 dynamic first-four scout on public profile/CaseClient; no world commits."""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json
import faith_e02_first_four_scout_queue as queue
from ck3_mod_acceptance_client import write_once
from ck3_mod_acceptance_cases.faith_e02_d1_readonly_adapter import shared_opening_binding

CASE="faith-engine-e02-first-four-scout-v1"
PRODUCT="faith-engine"
SAVE={"bytes":50210503,"sha256":"7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e",
      "player_id":15893,"date_raw":51394920}
LIMITS={"max_public_calls":40,"max_sites":2,"max_artifacts":4,"max_types":3,
        "max_baronies_per_type":1,"call_timeout":20,"quit_reserve_seconds":120}
READONLY_TOOLS=queue.READONLY
LIFECYCLE={"ck3_query_campaign_root_context_v1","ck3_query_current_event_window_context_v1",
 "ck3_query_normal_exit_context_v1","ck3_request_normal_exit_v1","ck3_observe_normal_exit_v1"}
REQUIRED_TOOLS=queue.TOOLS|LIFECYCLE
CLOSED=("opt_in_holy_site_creation_create_once","opt_in_holy_site_relic_actions",
        "opt_in_player_rite_creation_actions","opt_in_player_pilgrimage_execution")
SCOPE={"world_confirmation_allowed":False,"day_advance_allowed":False,"new_save_allowed":False,
       "actor_change_allowed":False,"ordinary_campaign_credit":False,"preparation_mod_mounted":False}
require=queue.require

def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def pin(p):
 p=Path(p).resolve();h=hashlib.sha256()
 with p.open("rb")as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return {"path":str(p),"bytes":p.stat().st_size,"sha256":h.hexdigest()}
def validate_contract(context):
 c=context["case_contract"];saved=c.get("saved_input",{})
 require(c.get("schema")=="faith-engine-e02-first-four-scout-case-v1"
  and c.get("case")==context.get("case")==CASE and c.get("product")==context.get("product")==PRODUCT,"Scout case identity differs")
 require(set(saved)=={"save",*SAVE} and type(saved.get("save"))is str and bool(saved["save"])
  and all(type(saved.get(k))is type(v)and saved[k]==v for k,v in SAVE.items()),"Original C2 bytes/actor expectation differs")
 require(c.get("scope")==SCOPE and c.get("profile")=={"enabled_mods":[],"product_files":[]}
  and c.get("limits")==LIMITS,"Scout scope/profile/budgets differ")
 require(type(c.get("machine_id"))is str and c["machine_id"]not in{"","unknown"},"Explicit machine required")
 spec=context["case_spec"]
 require(spec.get("opt_in_holy_site_creation_ui")is True and all(spec.get(k)is False for k in CLOSED),
  "Only independent creation presentation flag may be enabled")
 for key,wanted in (("required_mcp_tools",REQUIRED_TOOLS),("opt_in_read_only_mcp_tools",READONLY_TOOLS)):
  actual=spec.get(key);require(type(actual)is list and len(actual)==len(set(actual))and set(actual)==wanted,"Finite scout tools differ: "+key)
 budgets=spec.get("budgets",{})
 require(budgets.get("command_timeout")==20 and budgets.get("hold_seconds",0)>=900
  and budgets.get("timeout",0)>=1200,"Enough bounded calls/Root review/Quit reserve required")
 require(Path(queue.__file__).resolve()==Path(__file__).resolve().parent.parent/"faith_e02_first_four_scout_queue.py",
  "Scout queue import escaped candidate source")
 deps=c.get("dependencies",[])
 require(type(deps)is list and len(deps)==3 and {Path(x["path"]).resolve()for x in deps}=={
  Path(__file__).resolve(),Path(queue.__file__).resolve(),Path(shared_opening_binding.__code__.co_filename).resolve()},"Adapter, finite queue and public binding helper must be pinned")
 for dep in deps:require(pin(dep["path"])==dep,"Scout source dependency changed")
 qualification=c.get("native_qualification",{})
 require(qualification.get("dll_sha256")=="ad68db54342113267654c2f108e6a4db1db8af0178e232542db638a0f40667d6"
  and qualification.get("new_relic_live_qualification")is False,"Do not promote tool registration to ad68 live qualification")
 for name in("cache","closure"):
  ref=qualification.get(name,{})
  require(type(ref)is dict and set(ref)=={"path","bytes","sha256"}and pin(ref["path"])==ref,"Retained ad68 qualification source changed: "+name)
 return c

def prepare_case(context):
 from ck3_mod_acceptance_prepare import materialize_product_profile,finish_product_profile
 from ck3_live_run_id import current_machine_id
 c=validate_contract(context);require(current_machine_id()==c["machine_id"],"Executing machine differs")
 ref=context["case_inputs"]["storage_admission"]
 require(type(ref)is dict and set(ref)=={"path","bytes","sha256"},"Materialize with a fresh storage admission before public prepare")
 require(pin(ref["path"])==ref,"Storage admission changed")
 grant=read(ref["path"]);expiry=datetime.fromisoformat(grant["expires_at_utc"].replace("Z","+00:00"))
 require(grant.get("active")is True and grant.get("machine_id")==c["machine_id"]and expiry.tzinfo
  and datetime.now(timezone.utc)<expiry,"Fresh matching parent admission required")
 saved=dict(context["saved_campaign"]);require(saved==c["saved_input"],"Prepared C2 input differs")
 p=Path(saved["save"]);require(p.is_file()and not p.is_symlink()and p.suffix.casefold()==".ck3","Immutable original C2 required")
 before=p.stat();actual=pin(p);after=p.stat()
 require(actual["bytes"]==saved["bytes"]and actual["sha256"]==saved["sha256"]
  and(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),"Original C2 bytes changed")
 profile=materialize_product_profile(context,None,context["case_inputs"]["configuration"])
 profile=finish_product_profile(context,profile,provenance={"machine_id":c["machine_id"],
  "kind":"C2-first-four-readonly-scout","saved_input":saved,"storage_admission":ref,
  "preparation_mod_mounted":False,"world_actions_performed":False,"actual_restore_observed":False})
 return {"startup":{"mode":"saved_campaign","state_dir":profile["state_dir"],
  "saved_campaign":{**saved,"product_inventory":profile["product_inventory"]["path"]}},
  "profile":profile,"initial_plan":context["case_spec"]["initial_plan"],
  "runtime_status":"NOT_RUN","business_pass":False,"product_release_pass":False}

def same_scene(frame,binding,reader):
 now=reader(frame)
 for k in("played_character_id","date_raw","game_pid","connection_generation","episode_run_id"):
  require(now[k]==binding[k],"Scout scene changed "+k)
 require(frame.get("active_event")is None,"Real event requires ordinary event policy; scout cannot synthesize a choice")
 return now

def observed_bool(v):
 require(type(v)is dict and type(v.get("available"))is bool,"Observed Boolean availability missing")
 require(v.get("value")is None if not v["available"]else type(v.get("value"))is bool,"Unknown Boolean must remain null")
 return v.get("value")if v["available"]else None

def action_startpoint(value,actor,date,site,artifact):
 require(value.get("read_only")is True and value.get("played_character_id")==actor
  and value.get("date_raw")==date and value.get("requested_holy_site_id")==site
  and value.get("requested_artifact_id")==artifact,"Action-context crossed actual query identity")
 if value.get("available")is not True:
  return {"artifact_id":artifact,"site_id":site,"available":False,"reason":value.get("unavailable_reason"),
          "equipped":None,"can_enshrine":None,"owned_by_player":None,"quote_observed":False}
 own=value.get("artifact_ownership",{});require(own.get("artifact_id")==artifact,"Ownership artifact differs")
 equipped=observed_bool(own.get("player_equipped_slot_member",{}))
 permission=observed_bool(value.get("permissions",{}).get("artifact_permissions",{}).get("can_enshrine",{}))
 owned=own.get("character_owner_matches_player")
 require(owned is None or type(owned)is bool,"Unknown ownership must remain nullable")
 if own.get("available")is True:
  require(owned==(own.get("character_owner_id")==actor)
   and own.get("player_owned_reference_member")is True,"Owned-ref/owner mismatch")
 text=value.get("selected_action_effect_description",{})
 quote=(value.get("selected_artifact_matches_request")is True and text.get("available")is True
        and value.get("preview_identity_available")is True)
 return {"artifact_id":artifact,"site_id":site,"available":True,"equipped":equipped,
  "can_enshrine":permission,"owned_by_player":owned,
  "quote_observed":quote,"quote_text":text.get("text")if quote else None,
  "preview_sha256":value.get("preview_identity_sha256")if quote else None,
  "independent_equip_action_observed":False,"personal_net_effect_observed":False}

def slot_settlement(evidence):
 items=evidence.get("artifact_samples",[])
 equipped=[x["artifact_id"]for x in items if x.get("equipped")is True]
 candidates=[x["artifact_id"]for x in items if x.get("owned_by_player")is True and x.get("can_enshrine")is True]
 starts=evidence.get("creation_samples",[]);refusals=evidence.get("native_refusals",[])
 return {
 "E2-A1":{"required_closed":False,"filmable_startpoint":bool(evidence.get("religion_observed")and evidence.get("site_ids")),
  "missing":["two-recipient skill/devotion/source attribution","ordinary-major actual change"],"aggregate_is_site_contribution":False},
 "E2-A2":{"required_closed":False,"filmable_startpoint":bool(starts or refusals),
  "native_creation_samples":len(starts),"explicit_native_refusals":refusals,
  "location_specific_refusal_proven":False,"root_must_review_original_reason_scope":True},
 "E2-B1-personal":{"required_closed":False,"filmable_startpoint":bool(equipped),
  "actually_equipped_sample_ids":equipped,"independent_equip_action_observed":False,"personal_net_effect_observed":False},
 "E2-B1-enshrine":{"required_closed":False,"filmable_startpoint":bool(candidates),
  "actual_player_owned_can_enshrine_sample_ids":candidates,
  "same_equipped_and_enshrinable_ids":[x for x in equipped if x in candidates],
  "actual_current_quote_sample_ids":[x["artifact_id"]for x in items if x.get("quote_observed")is True],
  "enshrine_submitted":False,"owner_slot_wallet_poststate_observed":False},
 "E2-B2":{"required":False,"required_closed":False,"omitted":True}}

class Scout:
 def __init__(self,context,client,binding,reader):
  self.context,self.client,self.binding,self.reader=context,client,binding,reader
  self.calls=1 # first explicit CaseClient.snapshot
  self.sequence=0;self.rows=[]
 def guard(self,n=1):
  require(self.calls+n<=LIMITS["max_public_calls"],"Finite scout public-call budget exhausted")
  self.client.guard(120+20*n+10)
 def submit(self,steps,name):
  self.guard(len(steps));queue.validate({"steps":steps});self.calls+=len(steps)
  rows=self.client.execute_plan(steps,name,timeout=20*len(steps))
  require(type(rows)is list and len(rows)==len(steps),"Actual public result rows missing")
  for s,row in zip(steps,rows):
   self.rows.append({"step":s,"row":row})
   for key in("before_snapshot","after_snapshot"):
    require(type(row.get(key))is dict,"Independent public frame missing: "+key)
    same_scene(row[key],self.binding,self.reader)
  return rows
 def call(self,tool,args=None):
  self.sequence+=1;name="firstfour-"+str(self.sequence).zfill(3)
  return self.submit([queue.step(name,tool,args)],name)[0]
 def pair(self,tool,args,query_tool=queue.QUERY,query_args=None):
  self.sequence+=1;name="firstfour-"+str(self.sequence).zfill(3)
  return self.submit([queue.step(name+"-present",tool,args),queue.step(name+"-read",query_tool,query_args)],name)[-1]
 def value(self,row):
  if row.get("ok")is not True or row.get("error")or type(row.get("result"))is not dict:return None
  v=row["result"]
  if "played_character_id"in v:
   require(v["played_character_id"]==self.binding["played_character_id"]and v.get("date_raw")==self.binding["date_raw"],
    "Native domain crossed actual player/date")
  return v
 def domain(self,tool,args=None):
  value=self.value(self.call(tool,args))
  if value is not None and tool in queue.READONLY:
   require(value.get("read_only")is True,"Native query lost readonly identity")
   if args and "holy_site_id"in args:
    require(value.get("requested_holy_site_id")==args["holy_site_id"],"Native domain crossed requested site")
   if args and "artifact_id"in args:
    require(value.get("requested_artifact_id")==args["artifact_id"],"Native domain crossed requested artifact")
  return value
 def presentation(self,tool,args,query_tool=queue.QUERY,query_args=None):
  return self.value(self.pair(tool,args,query_tool,query_args))

def _creation_refusals(v,stage):
 found=[]
 if type(v)is not dict or v.get("available")is not True:return found
 for t in v.get("available_holy_site_types")or[]:
  if t.get("native_can_pick_observed")is True and t.get("native_can_pick")is False and t.get("tooltip_available")is True:
   found.append({"scope":"type_CanPick_not_automatically_location","stage":stage,"type_key":t.get("type_key"),"original_text":t.get("tooltip")})
 if v.get("normal_requirements_legality_observed")is True and v.get("normal_requirements_can_create")is False and v.get("create_tooltip_available")is True:
  found.append({"scope":"current_Create_combination_not_automatically_location","stage":stage,
    "type_key":v.get("selected_type_key"),"barony_title_id":v.get("selected_barony_title_id"),
    "artifact_ids":v.get("selected_artifact_ids"),"original_text":v.get("create_tooltip")})
 return found

def collect_scout(scout,e=None):
 if e is None:e={}
 e.update(site_ids=[],artifact_samples=[],creation_samples=[],native_refusals=[],unknowns=[])
 capabilities=scout.domain("ck3_get_capabilities");e["capabilities"]=capabilities
 religion=scout.domain("ck3_query_player_religion_context_v1");e["religion"]=religion
 e["religion_observed"]=bool(religion and religion.get("available")is True)
 sites=scout.domain("ck3_query_player_holy_site_v1");e["site_query"]=sites
 if sites and sites.get("available")is True:
  rows=sites.get("current_faith_sites")
  require(type(rows)is list,"Actual current-Faith sites absent")
  for r in rows:
   require(queue.ref(r.get("holy_site_id")),"Site fullID invalid")
  selected=[r["holy_site_id"]for r in rows if r.get("available")is True][:LIMITS["max_sites"]]
  e.update(site_ids=selected,site_count_observed=len(rows),site_sample_complete=len(selected)==len(rows))
 inventory=None;inventory_site=None
 for site in e["site_ids"]:
  ui=scout.presentation("ck3_open_holy_site_window_v1",{"holy_site_id":site},"ck3_query_ingame_ui_window_v1",{"window_kind":"holy_site"})
  visible=bool(ui and ui.get("available")is True and ui.get("effective_visible")is True and ui.get("subject_id_available")is True and ui.get("current_subject_id")==site)
  if not visible:e["unknowns"].append({"site_id":site,"reason":"original_site_window_not_independently_visible"});continue
  perms=scout.domain("ck3_query_player_holy_site_relic_permissions_v1",{"holy_site_id":site})
  relic=scout.domain("ck3_query_player_holy_site_relic_context_v1",{"holy_site_id":site})
  e.setdefault("site_observations",[]).append({"site_id":site,"permissions":perms,"relic":relic,"window":ui})
  inv=(perms or{}).get("player_inventory",{})
  if inventory is None and inv.get("available")is True and inv.get("owner_matches_player")is True:
   ids=inv.get("artifact_ids");require(type(ids)is list and all(queue.ref(x)for x in ids),"Actual player inventory IDs malformed")
   require(len(ids)==len(set(ids)),"Duplicate inventory refs; preserve raw source, do not fabricate completeness")
   inventory=list(ids);inventory_site=site
 e["inventory_refs"]=inventory;e["inventory_site_id"]=inventory_site
 if inventory is not None:
  sample=inventory[:LIMITS["max_artifacts"]]
  e.update(inventory_count=len(inventory),artifact_sample_complete=len(sample)==len(inventory))
  # Restore the exact original site window before sampling if another page was shown.
  if e["site_ids"]and inventory_site!=e["site_ids"][-1]:
   scout.presentation("ck3_open_holy_site_window_v1",{"holy_site_id":inventory_site},"ck3_query_ingame_ui_window_v1",{"window_kind":"holy_site"})
  for artifact in sample:
   v=scout.domain("ck3_query_player_holy_site_relic_action_context_v1",{"holy_site_id":inventory_site,"artifact_id":artifact})
   if v is None:
    e["artifact_samples"].append({"artifact_id":artifact,"site_id":inventory_site,"available":False,
      "equipped":None,"can_enshrine":None,"owned_by_player":None,"quote_observed":False,"reason":"native_query_error"})
   else:e["artifact_samples"].append(action_startpoint(v,scout.binding["played_character_id"],scout.binding["date_raw"],inventory_site,artifact))
 creation=scout.presentation("ck3_open_holy_site_creation_window_v1",{})
 if creation is not None:
  e["creation_initial"]=creation;e["native_refusals"]+=_creation_refusals(creation,"initial")
 if creation and creation.get("available")is True and creation.get("models_complete")is True:
  types=[x["type_key"]for x in creation.get("available_holy_site_types",[])if x.get("type_key")in queue.TYPES]
  for key in types[:LIMITS["max_types"]]:
   current=scout.domain(queue.QUERY)
   if current is None or current.get("available")is not True:continue
   e["native_refusals"]+=_creation_refusals(current,"before-type-"+key)
   row=next((x for x in current.get("available_holy_site_types",[])if x.get("type_key")==key),None)
   if not row or row.get("native_can_pick_observed")is not True or row.get("native_can_pick")is not True:continue
   current=scout.presentation("ck3_select_holy_site_creation_type_v1",{"type_key":key})
   if not current or current.get("available")is not True or current.get("selected_type_key")!=key:continue
   baronies=current.get("potential_barony_title_ids")
   if type(baronies)is not list:continue
   if baronies:
    barony=baronies[0];require(queue.ref(barony),"Current native barony fullID invalid")
    current=scout.presentation("ck3_select_holy_site_creation_barony_v1",{"barony_title_id":barony})
    if not current or current.get("selected_barony_title_id")!=barony:continue
   # Artifact setting is deliberately not needed: preserve the current model's
   # actual tuple, do not assume any old item still exists or may be equipped.
   e["creation_samples"].append(current);e["native_refusals"]+=_creation_refusals(current,"selected-"+key)
 return e

def _review(context,client,name,payload,reserve):
 response=client.root_checkpoint(name,payload,reserve=reserve)
 require(response.get("run_id")==context["run_id"]and response.get("reviewer")==client.operator_reviewer
  and response.get("status")=="complete","Scout Root checkpoint is foreign/incomplete")
 return response

def run_case(context,client):
 c=validate_contract(context);out=Path(context["output"])
 first=client.snapshot()
 write_once(out/"firstfour-first-public-snapshot.json",{"machine_id":c["machine_id"],"run_id":context["run_id"],"snapshot":first,"identity_validated":False})
 try:
  reader,source=shared_opening_binding(context)
  binding=reader(first);require(binding["played_character_id"]==15893,"Actual C2 player differs")
  require(first.get("active_event")is None,"Original C2 has an event requiring ordinary policy")
  require(client.manifest.get("native",{}).get("dll",{}).get("sha256")==c["native_qualification"]["dll_sha256"],"Selected global DLL differs from declared ad68 qualification scope")
 except Exception as error:
  write_once(out/"firstfour-first-native-identity-error.json",{"machine_id":c["machine_id"],"run_id":context["run_id"],"error":type(error).__name__+": "+str(error),"business_pass":False})
  raise
 result={"schema":"faith-e02-first-four-scout-result-v1","machine_id":c["machine_id"],"run_id":context["run_id"],
  "case":CASE,"actual_first_snapshot":first,"scene_binding":binding,"binding_sources":source,
  "native_qualification":c["native_qualification"],"world_confirmation_submitted":False,"business_pass":False,
  "case_contract_qualified":False,"gui_contract_qualified":False,"product_release_pass":False,"automatic_retry":False}
 write_once(out/"firstfour-first-native-identity.json",result)
 scout=Scout(context,client,binding,reader);evidence={}
 try:
  result["before_review"]=_review(context,client,"firstfour-before-scout",{
   "machine_id":c["machine_id"],"scene_binding":binding,"scope":SCOPE,"limits":LIMITS,
   "note":"Readonly model/equipment-membership scouting only; no equip/enshrine/Create/major confirm."},180)
  collect_scout(scout,evidence)
  result["status"]="SCOUT_OBSERVATIONS_READY"
 except Exception as error:
  result.update(status="SCOUT_PARTIAL_OR_BLOCKED",error=type(error).__name__+": "+str(error))
 finally:
  result.update(evidence=evidence,submitted_rows=scout.rows,public_calls_used=scout.calls,
   public_calls_cap=LIMITS["max_public_calls"],public_call_scope="all adapter submitted controls plus explicit snapshots; native wrapper reads are disclosed separately",
   required_slots=slot_settlement(evidence))
  client.checkpoint("firstfour-scout-observations",result)
 if client.remaining()>180:
  result["result_review"]=_review(context,client,"firstfour-results-and-filmable-startpoints",{
   "machine_id":c["machine_id"],"status":result["status"],"required_slots":result["required_slots"],
   "public_calls_used":scout.calls,"scope":SCOPE,"no_full_required_slot_closed":True,
   "review_action":"Review actual original pixels/IDs/reasons; retain partials and finish with normal Quit."},160)
 if client.remaining()>150 and scout.calls<LIMITS["max_public_calls"]:
  client.guard(150);last=client.snapshot();scout.calls+=1;same_scene(last,binding,reader)
  result.update(actual_final_snapshot=last,paused_actor_date_preserved=True,public_calls_used=scout.calls)
 write_once(out/"firstfour-scout-result.json",result)
 return result

def verify_case(context):
 c=validate_contract(context);r=read(Path(context["output"])/"firstfour-scout-result.json")
 require(r.get("case")==CASE and r.get("run_id")==context["run_id"]and r.get("machine_id")==c["machine_id"],"Foreign scout result")
 require(r.get("public_calls_used",999)<=LIMITS["max_public_calls"]and r.get("world_confirmation_submitted")is False
  and all(not v.get("required_closed")for v in r.get("required_slots",{}).values()),"Scout cannot grant full business credit")
 return {"status":r["status"],"required_slots":r["required_slots"],"public_calls_used":r["public_calls_used"],
  "research_holder_completed":True,"case_contract_qualified":False,"gui_contract_qualified":False,
  "business_pass":False,"product_release_pass":False,"automatic_retry":False}

