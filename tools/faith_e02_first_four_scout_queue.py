"""Finite public-control validator for C2 first-four READONLY scouting."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
QUERY="ck3_query_player_holy_site_creation_context_v1"
READONLY=frozenset({
 "ck3_query_player_religion_context_v1","ck3_query_player_holy_site_v1",QUERY,
 "ck3_query_player_holy_site_relic_permissions_v1","ck3_query_player_holy_site_relic_action_context_v1",
 "ck3_query_player_holy_site_relic_context_v1"})
SELECTORS=frozenset({"ck3_open_holy_site_creation_window_v1","ck3_select_holy_site_creation_type_v1",
 "ck3_select_holy_site_creation_barony_v1","ck3_set_holy_site_creation_artifact_selection_v1"})
TOOLS=READONLY|SELECTORS|{"ck3_get_capabilities","ck3_take_snapshot","ck3_open_holy_site_window_v1",
 "ck3_query_ingame_ui_window_v1"}
TYPES=frozenset({"site_of_wisdom","site_of_martyrs","site_of_miracles"})
def require(v,m):
 if not v:raise ValueError(m)
def ref(v):return type(v)is int and 0<=v<2**32-1
def step(name,tool,args=None):
 return {"id":name,"tool":tool,"args":args or {},"fresh_revision":True,
         "continue_on_error":True,"timeout":20}
def validate(plan):
 require(type(plan)is dict and set(plan)=={"steps"} and type(plan["steps"])is list and 1<=len(plan["steps"])<=8,"Finite original plan required")
 rows=plan["steps"];ids=[]
 for i,s in enumerate(rows):
  require(type(s)is dict and set(s)<={"id","tool","args","fresh_revision","continue_on_error","timeout"},"No lifecycle/day/raw operations")
  require(type(s.get("id"))is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}",s["id"]),"Portable explicit step ID required")
  ids.append(s["id"]);t=s.get("tool");a=s.get("args",{})
  require(t in TOOLS and type(a)is dict and s.get("fresh_revision")is True and s.get("continue_on_error")is True,"Finite readonly tools with fresh revisions required")
  require(type(s.get("timeout",20))in(int,float)and 0<s.get("timeout",20)<=20,"Scout call timeout exceeds20s")
  required=set();optional={"expected_revision"}
  if t in {"ck3_take_snapshot","ck3_get_capabilities"}:
   optional=set()
   if t=="ck3_take_snapshot":optional={"include_native_command_history"}
   require(a.get("include_native_command_history",False)is False,"No command-history export")
  elif t=="ck3_query_player_holy_site_v1":optional.add("holy_site_id")
  elif t in {"ck3_open_holy_site_window_v1","ck3_query_player_holy_site_relic_context_v1","ck3_query_player_holy_site_relic_permissions_v1"}:
   required={"holy_site_id"}
   if t.endswith("permissions_v1"):optional.add("artifact_id")
  elif t=="ck3_query_player_holy_site_relic_action_context_v1":required={"holy_site_id","artifact_id"}
  elif t=="ck3_query_ingame_ui_window_v1":
   required={"window_kind"};require(a.get("window_kind")in{"holy_site","holy_site_creation"},"Only current site/creation page queries")
  elif t=="ck3_select_holy_site_creation_type_v1":
   required={"type_key"};require(a.get("type_key")in TYPES,"Only current episode type candidates")
  elif t=="ck3_select_holy_site_creation_barony_v1":required={"barony_title_id"}
  elif t=="ck3_set_holy_site_creation_artifact_selection_v1":
   required={"artifact_id","selected"};require(type(a.get("selected"))is bool,"Explicit selected state required")
  require(required<=set(a)<=required|optional,"Unexpected/missing tool args")
  require("expected_revision"not in a or type(a["expected_revision"])is int and a["expected_revision"]>0,"Only observed positive revision")
  for k in ("holy_site_id","artifact_id","barony_title_id"):
   require(k not in a or ref(a[k]),"Complete native fullID required")
  if t in SELECTORS or t=="ck3_open_holy_site_window_v1":
   require(i+1<len(rows),"Presentation needs immediate independent readback")
   nxt=rows[i+1];expected="ck3_query_ingame_ui_window_v1"if t=="ck3_open_holy_site_window_v1"else QUERY
   require(nxt.get("tool")==expected and nxt.get("fresh_revision")is True,"Presentation readback differs")
   if t=="ck3_open_holy_site_window_v1":require(nxt.get("args",{}).get("window_kind")=="holy_site","Site page readback differs")
 require(len(ids)==len(set(ids)),"Duplicate step ID; never replay")
 return {"schema":"faith-e02-firstfour-scout-queue-v1","steps":len(rows),"validated":True,
         "world_confirmation_allowed":False,"submitted":False,"native_legality_inferred":False}
if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--plan",type=Path,required=True)
 args=p.parse_args();print(json.dumps(validate(json.loads(args.plan.read_text(encoding="utf-8-sig")))))

