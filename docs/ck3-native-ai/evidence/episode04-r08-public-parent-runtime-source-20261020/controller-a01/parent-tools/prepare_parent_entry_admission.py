"""Prepare a distinct parent-entry admission from exact retained same-client inputs. Never launch."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,sys
import owner_binding as owner
from parent_entry_execution_contract import MODE,PREFIX_SHA,digest,need
def read(path,limit=3*1024*1024):
 need(path.stat().st_size<=limit,"input stat cap")
 b=path.read_bytes();need(len(b)<=limit,"input cap after read");return json.loads(b),b
def verify_pin(pin,limit=5*1024*1024):
 p=Path(pin["path"]);need(p.stat().st_size==pin["bytes"]<=limit,"pin size")
 b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==pin["sha256"],"pin SHA");return p
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--prepare-parent-entry",action="store_true")
 for key in ("repo","snapshot","cash","root-scope","qualification","observer","output-root"):p.add_argument("--"+key,type=Path,required=True)
 a=p.parse_args();need(a.prepare_parent_entry,"default OFF")
 scope,sb=read(a.root_scope,65536);q,qb=read(a.qualification,65536)
 need(q.get("schema")=="xar.maintenance.parent_entry.execution-qualification.v1" and q.get("status")=="SELECTED_EXECUTION_COLD_PASS" and q.get("mode")==MODE,"new execution qualification required; A08/ASM/dispatch not eligible")
 need(scope.get("schema")=="xar.maintenance.parent_entry.root-scope.v1" and scope.get("mode")==MODE and scope.get("execution_authorized") is True,"separate Root scope")
 current=dt.datetime.now(dt.timezone.utc);issued=dt.datetime.fromisoformat(scope["observed_at_utc"].replace("Z","+00:00"));expires=dt.datetime.fromisoformat(scope["expires_at_utc"].replace("Z","+00:00"))
 need(issued<=current<expires and (expires-issued).total_seconds()<=300,"fresh finite source scope")
 need(scope["qualification_sha256"]==hashlib.sha256(qb).hexdigest(),"scope/Q pin")
 need(q["observer_pin"]["sha256"]==scope["observer_sha256"] and verify_pin(q["observer_pin"]).resolve()==a.observer.resolve(),"exact observer/Q")
 for pin in q["source_pins"]:verify_pin(pin,1024*1024)
 source={Path(pin["path"]).name:pin["sha256"] for pin in q["source_pins"]}
 for name in ("cold_observer.cpp","parent_entry_execution_once.inc"):
  need(source.get(name)==hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest(),"current mode source differs from Q")
 for key in ("SYSTEM_receipt_pin","cold_suite_pin","Root_acceptance_pin"):verify_pin(q[key])
 system,_=read(Path(q["SYSTEM_receipt_pin"]["path"]));cold,_=read(Path(q["cold_suite_pin"]["path"]));accept,_=read(Path(q["Root_acceptance_pin"]["path"]))
 need(system.get("status")=="verified" and system.get("system_token_sid")=="S-1-5-18" and system.get("admin_token") is True and system.get("missing_requested_paths")==[],"actual SYSTEM")
 need(str(a.observer) in system.get("verified_requested_paths",[]) and any(x.get("sha256")==scope["observer_sha256"] and Path(x["path"]).resolve()==a.observer.resolve() for x in system.get("files",[])),"SYSTEM exact observer")
 required={"foreign257_then_target","created_thread","foreign4096_limit","timeout","cancel_late","restore-fault","readback-fault","continue-fault","default-off","occupied-dr","occupied-tf","context-drift","fullid-drift","magic-drift","session-drift","missing-ack","bad-schema"}
 need(cold.get("schema")=="xar.maintenance.parent_entry.cold.suite.v1" and cold.get("mode")==MODE and cold.get("machine_id")==q["machine_id"] and required<=set(cold.get("selected_cases",[])),"actual required cold suite; selected guard alone is not qualification")
 case_rows=[]
 for case_pin in cold["cases"]:
  case_path=verify_pin(case_pin);case,_=read(case_path)
  need(case.get("schema")=="xar.maintenance.parent_entry.cold.case.v1" and case.get("status")=="PASS" and case.get("machine_id")==q["machine_id"],"actual case proof")
  case_rows.append(case["case"])
 need(set(case_rows)==set(cold["selected_cases"]) and len(case_rows)==len(set(case_rows)),"exact selected case pins")
 need(accept.get("mode")==MODE and accept.get("accepted") is True and accept.get("observer_sha256")==q["observer_pin"]["sha256"] and accept.get("source_pins")==q["source_pins"] and accept.get("cold_suite_sha256")==q["cold_suite_pin"]["sha256"] and required<=set(accept.get("accepted_cases",[])),"independent Root positive/RF/cleanup adoption")
 repo=a.repo.resolve();sys.path[:0]=[str(repo/"tools"),str(repo/"ck3_autonomous_player/src")]
 from ck3_live_run_id import current_machine_id
 from xar_autoplayer.bridge import war_payment_observations_v1 as payment
 from xar_autoplayer.bridge.war_cash_current_raw_context_v1 import validate_current_raw_context_v1
 from xar_autoplayer.bridge.war_cash_private_transport_v1 import normalize_war_cash_current_resources_v1
 from xar_autoplayer.bridge.nonwar_private_build import private_native_build_identity
 from xar_autoplayer.bridge.version_identity import CK3_12004
 machine=current_machine_id();need(machine==scope["machine_id"]==q["machine_id"]==accept["machine_id"],"machine")
 snapshot_packet,snap_bytes=read(a.snapshot);cash_packet,cash_bytes=read(a.cash)
 common_output=Path(scope["common_output"]).resolve()
 for packet,view_path,view_bytes,role in ((snapshot_packet,a.snapshot,snap_bytes,"snapshot"),(cash_packet,a.cash,cash_bytes,"cash")):
  view_pin=scope[role+"_view_pin"]
  need(verify_pin(view_pin).resolve()==view_path.resolve() and view_pin["sha256"]==hashlib.sha256(view_bytes).hexdigest(),"Root exact common view pin")
  need(packet["machine_id"]==machine and packet["is_error"] is False and packet["common_row_ok"] is True and not packet["common_row_error"],"original common error/machine")
  original_pin=packet["common_original"];original=verify_pin(original_pin,3*1024*1024)
  need(original_pin["pointer"]=="/rows/0/result" and original.resolve().is_relative_to(common_output),"original common output/pointer")
  saved,_=read(original);rows=saved["rows"]
  need(len(rows)==1 and rows[0]["id"]==packet["request"]["request_id"] and rows[0]["ok"] is True and rows[0]["result"]==packet["body"],"actual original common row/body")
 need(snapshot_packet["request"]["tool"]=="ck3_take_snapshot" and cash_packet["request"]["tool"]=="ck3_query_war_cash_current_resources_private_v1" and cash_packet["request"]["arguments"]["payment_sampling"]=="query","paired original readonly inputs")
 snapshot=snapshot_packet["body"];cash=cash_packet["body"]
 need(private_native_build_identity(snapshot)==CK3_12004,"exact native version")
 validate_current_raw_context_v1(cash,snapshot=snapshot);normalize_war_cash_current_resources_v1(cash,snapshot=snapshot)
 extras=payment.normalize_payment_extras(cash,snapshot=snapshot,payment_sampling="query");journal=extras[payment.JOURNAL_KEY]
 expected_owner=owner.validate(scope["owner_binding"])
 actual_owner=owner.qualify(owner.ORDINARY,None,snapshot,journal,cash["current_raw_context_v1"],expected_game_state=expected_owner["game_state_identity_witness"],expected_local_player_id=expected_owner["local_player_id"])
 need(actual_owner==expected_owner,"independent Root owner join")
 need(scope["module_base"]>0 and scope["module_size"]==102518784 and scope["foreign_limit"]==4096 and scope["capture_ms"]==30000,"exact module/finite limits")
 expected=dict(machine_id=machine,synthetic=False,pid=actual_owner["pid"],created=actual_owner["process_create_time_100ns"],entry=scope["module_base"]+0x28f7840,character=actual_owner["character"],full_id=actual_owner["player_character_full_id"],context=actual_owner["context"],local_player_id=actual_owner["local_player_id"],game_state=actual_owner["game_state_identity_witness"],date_raw=actual_owner["date_raw"],absolute_day=actual_owner["absolute_day_raw"],foreign_limit=4096,capture_ms=30000,admission_id="",owner_binding=actual_owner)
 aid=digest(dict(expected=expected,root_scope_sha256=hashlib.sha256(sb).hexdigest(),cash_sha256=hashlib.sha256(cash_bytes).hexdigest(),snapshot_sha256=hashlib.sha256(snap_bytes).hexdigest()))
 expected["admission_id"]=aid
 meta=dict(parent_schema="xar.maintenance.parent_entry.admission.v1",pid=expected["pid"],tid=0,created=expected["created"],character=expected["character"],context=expected["context"],full_id=expected["full_id"],module_base=scope["module_base"],module_size=scope["module_size"],parent_mode_qualified=1,prefix_sha256=PREFIX_SHA,qualified_exe_sha256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",game_version="1.20.0.4",steam_build_id=25734779,controlled_window_id=actual_owner["controlled_window_id"],payment_epoch=actual_owner["payment_epoch"],connection_generation=actual_owner["connection_generation"],native_revision=actual_owner["native_revision"],date_raw=expected["date_raw"],source_cash_sha256=hashlib.sha256(cash_bytes).hexdigest(),admission_id=aid,foreign_limit=4096,cancel_event=scope["cancel_event"])
 meta.update(owner.metadata(actual_owner))
 metadata="".join(k+"="+str(v)+"\n" for k,v in meta.items()).encode("ascii")
 binding=(json.dumps(dict(schema="xar.maintenance.parent_entry.binding.v1",machine_id=machine,expected=expected,root_scope_sha256=hashlib.sha256(sb).hexdigest(),qualification_sha256=hashlib.sha256(qb).hexdigest(),meta_sha256=hashlib.sha256(metadata).hexdigest(),prepared_only=True),indent=2)+"\n").encode()
 need(len(metadata)+len(binding)<=32768 and not a.output_root.exists(),"bounded exclusive output")
 a.output_root.mkdir(parents=True)
 for name,b in (("PARENT-ENTRY.meta.txt",metadata),("BINDING.prepared.json",binding)):
  with (a.output_root/name).open("xb") as f:f.write(b)
 return 0
if __name__=="__main__":
 try:raise SystemExit(main())
 except (ValueError,KeyError,TypeError,OSError) as e:print(str(e),file=sys.stderr);raise SystemExit(2)
