"""Prepare a distinct parent-pointer-read admission from exact retained same-client inputs. Never launch."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,sys
from pointer_read_wire import wire_json
import pointer_read_owner_binding as owner
from pointer_read_models import FilePin,Expected,JsonObject,file_pin,object_value,expected_value
from pointer_read_admission_models import scope_value,qualification_value,suite_value,acceptance_value,packet_value,objects,strings,text
from parent_pointer_read_contract import MODE,PREFIX_SHA,digest,need
def read(path: Path,limit: int=3*1024*1024) -> tuple[JsonObject,bytes]:
 need(path.stat().st_size<=limit,"input stat cap")
 b=path.read_bytes();need(len(b)<=limit,"input cap after read");return object_value(json.loads(b),"input object"),b
def verify_pin(pin: object,limit: int=5*1024*1024) -> Path:
 pin=file_pin({k:object_value(pin,"pin").get(k) for k in ("path","bytes","sha256")})
 p=Path(pin["path"]);need(p.stat().st_size==pin["bytes"]<=limit,"pin size")
 b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==pin["sha256"],"pin SHA");return p
def main() -> int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--prepare-parent-pointer-read",action="store_true")
 for key in ("repo","snapshot","cash","root-scope","qualification","observer","output-root"):p.add_argument("--"+key,type=Path,required=True)
 a=p.parse_args();need(a.prepare_parent_pointer_read,"default OFF")
 scope_data,sb=read(a.root_scope,65536);q_data,qb=read(a.qualification,65536)
 need(q_data.get("schema")=="xar.maintenance.parent_pointer_read.pointer-read-qualification.v1" and q_data.get("status")=="SELECTED_POINTER_READ_COLD_PASS" and q_data.get("mode")==MODE,"new pointer-read qualification required; execution/A08 not eligible")
 scope=scope_value(scope_data);q=qualification_value(q_data)
 need(q.get("schema")=="xar.maintenance.parent_pointer_read.pointer-read-qualification.v1" and q.get("status")=="SELECTED_POINTER_READ_COLD_PASS" and q.get("mode")==MODE,"new pointer-read qualification required; A08/ASM/dispatch not eligible")
 need(scope.get("schema")=="xar.maintenance.parent_pointer_read.root-scope.v1" and scope.get("mode")==MODE and scope.get("readwatch_authorized") is True,"separate Root scope")
 current=dt.datetime.now(dt.timezone.utc);issued=dt.datetime.fromisoformat(scope["observed_at_utc"].replace("Z","+00:00"));expires=dt.datetime.fromisoformat(scope["expires_at_utc"].replace("Z","+00:00"))
 need(issued<=current<expires and (expires-issued).total_seconds()<=300,"fresh finite source scope")
 need(scope["qualification_sha256"]==hashlib.sha256(qb).hexdigest(),"scope/Q pin")
 need(q["observer_pin"]["sha256"]==scope["observer_sha256"] and verify_pin(q["observer_pin"]).resolve()==a.observer.resolve(),"exact observer/Q")
 for pin in q["source_pins"]:verify_pin(pin,1024*1024)
 source={Path(pin["path"]).name:pin["sha256"] for pin in q["source_pins"]}
 for name in ("cold_observer.cpp","parent_pointer_read_once.inc","parent_pointer_read_capture.inc","pointer_read_decimal64.hpp"):
  need(source.get(name)==hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest(),"current mode source differs from Q")
 for ref in (q["SYSTEM_receipt_pin"],q["cold_suite_pin"],q["Root_acceptance_pin"]):verify_pin(ref)
 system,_=read(Path(q["SYSTEM_receipt_pin"]["path"]));cold_data,_=read(Path(q["cold_suite_pin"]["path"]));accept_data,_=read(Path(q["Root_acceptance_pin"]["path"]))
 cold=suite_value(cold_data);accept=acceptance_value(accept_data)
 need(system.get("status")=="verified" and system.get("system_token_sid")=="S-1-5-18" and system.get("admin_token") is True and system.get("missing_requested_paths")==[],"actual SYSTEM")
 need(str(a.observer) in strings(system.get("verified_requested_paths"),"verified paths") and any(x.get("sha256")==scope["observer_sha256"] and Path(text(x["path"],"SYSTEM path")).resolve()==a.observer.resolve() for x in objects(system.get("files"),"SYSTEM files")),"SYSTEM exact observer")
 required={"foreign257_then_target","created_thread","foreign4096_limit","timeout","cancel_late","restore-fault","readback-fault","continue-fault","default-off","occupied-dr","occupied-tf","context-drift","fullid-drift","magic-drift","session-drift","missing-ack","bad-schema","null-context","other-player-read","other-player-write","null-admission"}
 need(cold.get("schema")=="xar.maintenance.parent_pointer_read.cold.suite.v1" and cold.get("mode")==MODE and cold.get("machine_id")==q["machine_id"] and required<=set(cold.get("selected_cases",[])),"actual required cold suite; selected guard alone is not qualification")
 case_rows=[]
 for case_pin in cold["cases"]:
  case_path=verify_pin(case_pin);case,_=read(case_path)
  need(case.get("schema")=="xar.maintenance.parent_pointer_read.cold.case.v1" and case.get("status")=="PASS" and case.get("machine_id")==q["machine_id"],"actual case proof")
  case_rows.append(text(case["case"],"case"))
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
 snap_data,snap_bytes=read(a.snapshot);cash_data,cash_bytes=read(a.cash)
 snapshot_packet=packet_value(snap_data);cash_packet=packet_value(cash_data)
 common_output=Path(scope["common_output"]).resolve()
 for packet,view_path,view_bytes,role in ((snapshot_packet,a.snapshot,snap_bytes,"snapshot"),(cash_packet,a.cash,cash_bytes,"cash")):
  view_pin=scope["snapshot_view_pin"] if role=="snapshot" else scope["cash_view_pin"]
  need(verify_pin(view_pin).resolve()==view_path.resolve() and view_pin["sha256"]==hashlib.sha256(view_bytes).hexdigest(),"Root exact common view pin")
  need(packet["machine_id"]==machine and packet["is_error"] is False and packet["common_row_ok"] is True and not packet["common_row_error"],"original common error/machine")
  original_pin=packet["common_original"];original=verify_pin(original_pin,3*1024*1024)
  need(original_pin["pointer"]=="/rows/0/result" and original.resolve().is_relative_to(common_output),"original common output/pointer")
  saved,_=read(original);rows=objects(saved["rows"],"original rows")
  need(len(rows)==1 and rows[0]["id"]==packet["request"]["request_id"] and rows[0]["ok"] is True and rows[0]["result"]==packet["body"],"actual original common row/body")
 need(snapshot_packet["request"]["tool"]=="ck3_take_snapshot" and cash_packet["request"]["tool"]=="ck3_query_war_cash_current_resources_private_v1" and cash_packet["request"]["arguments"]["payment_sampling"]=="query","paired original readonly inputs")
 snapshot=snapshot_packet["body"];cash=cash_packet["body"]
 need(private_native_build_identity(snapshot)==CK3_12004,"exact native version")
 # This observer needs the retained primary Character/session, not a nonnull secondary or cash-value availability.
 journal=object_value(cash[payment.JOURNAL_KEY],"payment journal")
 need(type(cash.get("current_raw_context_v1")) is dict,"actual primary pointer DTO required; missing input cannot be invented")
 expected_owner=owner.validate(scope["owner_binding"])
 actual_owner=owner.qualify(owner.ORDINARY,None,snapshot,journal,object_value(cash["current_raw_context_v1"],"primary pointer"),expected_game_state=expected_owner["game_state_identity_witness"],expected_local_player_id=expected_owner["local_player_id"])
 need(actual_owner is not None,"ordinary pointer owner required")
 actual_owner=owner.validate(actual_owner)
 need(actual_owner==expected_owner,"independent Root owner join")
 need(scope["module_base"]>0 and scope["module_size"]==102518784 and scope["foreign_limit"]==4096 and scope["capture_ms"]==30000,"exact module/finite limits")
 expected=Expected(machine_id=machine,synthetic=False,pid=actual_owner["pid"],created=actual_owner["process_create_time_100ns"],entry=scope["module_base"]+0x28f7840,post_pc=scope["module_base"]+0x28f785a,watch_address=actual_owner["character"]+0x1c0,character=actual_owner["character"],full_id=actual_owner["player_character_full_id"],context=actual_owner["context"],local_player_id=actual_owner["local_player_id"],game_state=actual_owner["game_state_identity_witness"],date_raw=actual_owner["date_raw"],absolute_day=actual_owner["absolute_day_raw"],foreign_limit=4096,capture_ms=30000,admission_id="",owner_binding=actual_owner)
 aid=digest(dict(expected=expected,root_scope_sha256=hashlib.sha256(sb).hexdigest(),cash_sha256=hashlib.sha256(cash_bytes).hexdigest(),snapshot_sha256=hashlib.sha256(snap_bytes).hexdigest()))
 expected["admission_id"]=aid
 expected_value(wire_json(expected))
 meta=dict(post_pc=expected["post_pc"],watch_address=expected["watch_address"],parent_schema="xar.maintenance.parent_pointer_read.admission.v1",pid=expected["pid"],tid=0,created=expected["created"],character=expected["character"],context=expected["context"],full_id=expected["full_id"],module_base=scope["module_base"],module_size=scope["module_size"],parent_mode_qualified=1,prefix_sha256=PREFIX_SHA,qualified_exe_sha256="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",game_version="1.20.0.4",steam_build_id=25734779,controlled_window_id=actual_owner["controlled_window_id"],payment_epoch=actual_owner["payment_epoch"],connection_generation=actual_owner["connection_generation"],native_revision=actual_owner["native_revision"],date_raw=expected["date_raw"],source_cash_sha256=hashlib.sha256(cash_bytes).hexdigest(),admission_id=aid,foreign_limit=4096,cancel_event=scope["cancel_event"])
 meta.update(owner.metadata(actual_owner))
 metadata="".join(k+"="+str(v)+"\n" for k,v in meta.items()).encode("ascii")
 binding=(json.dumps(wire_json(dict(schema="xar.maintenance.parent_pointer_read.binding.v2",machine_id=machine,expected=expected,root_scope_sha256=hashlib.sha256(sb).hexdigest(),qualification_sha256=hashlib.sha256(qb).hexdigest(),meta_sha256=hashlib.sha256(metadata).hexdigest(),prepared_only=True)),indent=2)+"\n").encode()
 need(len(metadata)+len(binding)<=32768 and not a.output_root.exists(),"bounded exclusive output")
 a.output_root.mkdir(parents=True)
 for name,b in (("PARENT-POINTER-READ.meta.txt",metadata),("BINDING.prepared.json",binding)):
  with (a.output_root/name).open("xb") as f:f.write(b)
 return 0
if __name__=="__main__":
 try:raise SystemExit(main())
 except (ValueError,KeyError,TypeError,OSError) as e:print(str(e),file=sys.stderr);raise SystemExit(2)
