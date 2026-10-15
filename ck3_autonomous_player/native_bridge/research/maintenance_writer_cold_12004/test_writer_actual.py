"""Four focused offline reader behaviors. Every input is a synthetic contract fixture."""
from pathlib import Path
import argparse
import copy
import datetime as dt
import importlib.util
import json
import shutil
import sys

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def write(path, value, raw=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x",encoding="utf-8",newline="\n") as f:
        if raw:
            for row in value:
                f.write(json.dumps(row)+"\n")
        else:
            json.dump(value,f,indent=2)
            f.write("\n")

def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value
    spec.loader.exec_module(value)
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-repo",type=Path,required=True)
    parser.add_argument("--sealed-root",type=Path)
    parser.add_argument("--cash-candidate-root",type=Path)
    parser.add_argument("--output-root",type=Path,required=True)
    args=parser.parse_args()
    need(not args.output_root.exists(),"Append-only focused test attempt exists")
    args.output_root.mkdir(parents=True)
    sys.path[:0]=[str(args.main_repo),str(args.main_repo/"ck3_autonomous_player/src")]
    import xar_autoplayer.bridge
    # One sealed optional leaf module overlays the frozen main imports for this
    # offline test. No main file is changed or old test matrix executed.
    if args.cash_candidate_root is not None:
        leaf=args.cash_candidate_root/"candidate/ck3_autonomous_player/src/xar_autoplayer/bridge/war_cash_current_raw_context_v1.py"
        module("xar_autoplayer.bridge.war_cash_current_raw_context_v1",leaf)
    reader=module("_actual_writer_reader",Path(__file__).with_name("consume_writer_actual.py"))
    relative=Path("ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_cold.py")
    existing=(args.sealed_root/"delivery-a01/candidate"/relative if args.sealed_root is not None
              else args.main_repo/relative)
    test_repo=args.output_root/"strict-source-assembly"
    strict=test_repo/"ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_cold.py"
    strict.parent.mkdir(parents=True)
    shutil.copyfile(existing,strict)
    compiled=args.main_repo/"ck3_autonomous_player/tests/unit/fixtures/war_payment_compiled_12004_a06.json"
    selected=next(row["value"] for row in json.loads(compiled.read_bytes())
                  if row["case"]=="controlled_window_personal")
    journal=copy.deepcopy(selected.get("war_payment_observations_v1",selected))
    s=journal["current_session"]
    legacy=args.main_repo/"ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_war_cash_current-resources-normal.json"
    cash=json.loads(legacy.read_bytes())
    cash.update(game_version=journal["game_version"],executable_sha256=journal["executable_sha256"],
                played_character_id=s["player_character_full_id"],snapshot_revision=s["snapshot_revision"],
                date_raw=s["native_date_raw"],war_payment_observations_v1=journal)
    cash["readiness"]["same_frame_ready"]=True
    values=dict(context_identity_before=0x300000,context_identity_after=0x300000,
                value_2c0=0,value_2c8=0,value_28=0,value_30=0,
                capture_complete=True,context_stable=True,failed_reads=0)
    leaf_value=dict(schema_version=1,observation_kind="paused_current_raw_context",
                    attribution_scope="current_raw_context_only",maintenance_attribution="unclosed",
                    character=0x100000,character_full_id=s["player_character_full_id"],
                    snapshot_revision=s["snapshot_revision"],date_raw=s["native_date_raw"],
                    actor_identity_stable=True,same_frame_ready=True,values=values,
                    admission_ready=True,unavailable_reason=None)
    cash["current_raw_context_v1"]=leaf_value
    before=dict(paused=True,map_ready=True,revision=s["snapshot_revision"]+1,
                native_revision=s["snapshot_revision"],date_raw=s["native_date_raw"],
                episode_run_id="synthetic-actual-reader-contract",
                played_character=dict(character_id=s["player_character_full_id"],alive=True),
                diagnostics=dict(bridge_pid=s["pid"],connection_generation=s["connection_generation"],
                    hello=dict(expected_ck3_version=journal["game_version"],
                               expected_ck3_sha256=journal["executable_sha256"])))
    def envelope(tool,body,arguments):
        return dict(machine_id=journal["machine_id"],is_error=False,body=body,
                    request=dict(request_id="synthetic-reader-"+tool,tool=tool,arguments=arguments),
                    sdk_result=dict(structured_content=copy.deepcopy(body)))
    fixture=args.output_root/"synthetic-inputs"
    cash_path=fixture/"cash.json"
    before_path=fixture/"before.json"
    write(cash_path,envelope("ck3_query_war_cash_current_resources_private_v1",cash,
                            dict(payment_sampling="query",expected_revision=before["revision"])))
    write(before_path,envelope("ck3_take_snapshot",before,dict(include_native_command_history=False)))
    expected={key:s[key] for key in ["pid","process_create_time_100ns","connection_generation",
                                     "controlled_window_id","player_character_full_id"]}
    admission=dict(schema="xar.maintenance.writer_pc.future-admission.v1",machine_id=journal["machine_id"],
                   expected_root_identity=expected,expected_payment_epoch=journal["sampling"]["epoch"],
                   expected_episode=before["episode_run_id"],raw_leaf=leaf_value,
                   source_packet_pins=[dict(path=str(p),sha256=reader.digest(p.read_bytes()))
                                       for p in [cash_path,before_path]],
                   known_producer=False,maintenance_attribution="unclosed")
    admission_path=fixture/"ADMISSION.synthetic-contract.json"
    write(admission_path,admission)
    reader.configure(test_repo)
    binding=reader.bind_inputs(admission,cash_path.read_bytes(),before_path.read_bytes())
    start={key:value for key,value in binding.items() if key!="current_raw_cache"}
    start.update(kind="start",schema="xar.maintenance.writer_pc.cold.v1",synthetic=False,
                 CK3_observed=True,maintenance_attribution="unclosed",
                 module_base=0x140000000,module_size=102518784,actual_writer_game_date=None,
                 DR7_write_len8_mask=0x99990055,field_offsets=list(reader.OFFSETS),initial_values=[0]*4)
    saved=[0,0,0,0,0xffff0ff0,0x400]
    def arm(tid):
        return dict(kind="arm",thread_id=tid,success=True,saved_debug=list(saved),
                    armed_debug=[0x300000+x for x in reader.OFFSETS]+[0,0x99990455])
    def restore(tid):
        return dict(kind="restore",thread_id=tid,readback=True,debug=list(saved))
    def terminal(count):
        return dict(kind="terminal",reason="timeout",restored=True,detached=True,pending_event=False,
                    cleanup_complete=True,hit_count=count,data_event_count=count,writer_thread_count=int(count>0),
                    created_thread_events=1,restore_readback_rows=2,process_exited=False,
                    observation_thread_admission_complete=True,full_window_all_writes_covered=False,
                    CK3_observed=True,known_producer=False,military_attribution="unclosed")
    def hit(slot):
        after=0 if slot==0 else slot+10
        return dict(kind="raw_field_write_trap",event_ordinal=slot+1,slot_hit_ordinal=slot+1,
                    thread_id=901,qpc=1000+slot,slot=slot,offset=reader.OFFSETS[slot],
                    address=0x300000+reader.OFFSETS[slot],full_id=s["player_character_full_id"],
                    character=0x100000,context=0x300000,context_identity_stable=True,before_raw=0,
                    before_basis="last_observed_sample_not_atomic_preinstruction",after_raw=after,
                    after_read_complete=True,same_value_write=after==0,RIP_after=0x140010010+slot*16,
                    RIP_after_rva=0x10010+slot*16,writer_instruction_start=None,DR6=1<<slot,
                    registers={key:0 for key in reader.REGISTERS},synthetic=False,known_producer=False,
                    military_attribution="unclosed")
    results=[]
    base=[copy.deepcopy(start),arm(900),arm(901)]
    def run(name,rows):
        case=args.output_root/name
        case.mkdir()
        raw=case/"writer.synthetic-contract.ndjson"
        output=case/"PROJECTION.synthetic-contract.json"
        write(raw,rows,raw=True)
        argv=["--repo",str(test_repo),"--raw",str(raw),"--admission",str(admission_path),
              "--cash-response",str(cash_path),"--before-response",str(before_path),"--output",str(output)]
        rc=reader.main(argv)
        need(rc==0,"Reader invocation failed")
        return json.loads(output.read_bytes())
    value=run("four_fields_timeout",base+[hit(n) for n in range(4)]+[restore(900),restore(901),terminal(4)])
    need(value["qualified_slot_count"]==4 and value["cleanup_proved"] is True
         and value["finite_window_reason"]=="timeout" and value["same_value_write_count"]==1,
         "Actual-shaped source-unknown timeout projection failed")
    need(all(row["writer_instruction_start"] is None and row["known_producer"] is False
             and row["source_status"]=="unknown" for row in value["qualified_writers"]),
         "Writer PC was converted into known source/instruction")
    results.append(dict(case="four_fields_timeout",pass_=True,fixture_game_credit=False))
    value=run("clean_zero_timeout",base+[restore(900),restore(901),terminal(0)])
    need(value["qualified_slot_count"]==0 and value["cleanup_proved"] is True
         and value["status"]=="NO_QUALIFIED_WRITER_IN_FINITE_WINDOW"
         and value["maintenance_attribution"]=="unclosed","Zero-hit finite window misclassified")
    results.append(dict(case="clean_zero_timeout",pass_=True,fixture_game_credit=False))
    bad=hit(0);bad["after_read_complete"]=False
    value=run("unknown_read_missing_restore",base+[bad,restore(900),terminal(1)])
    need(value["qualified_slot_count"]==0 and value["unknown_slot_count"]==1
         and value["unknown_traps"][0]["after_raw"] is None and value["cleanup_proved"] is False,
         "Unknown value or missing restore falsely qualified")
    results.append(dict(case="unknown_read_missing_restore",pass_=True,fixture_game_credit=False))
    cold=copy.deepcopy(base+[restore(900),restore(901),terminal(0)])
    cold[0].update(synthetic=True,CK3_observed=False)
    rejected=False
    try:
        run("cold_fixture_no_game_credit",cold)
    except ValueError as exc:
        rejected="Synthetic/cold fixture" in str(exc)
    need(rejected,"Cold fixture received actual CK3 credit")
    results.append(dict(case="cold_fixture_no_game_credit",pass_=True,fixture_game_credit=False))
    report=dict(status="PASS_4_FOCUSED_SYNTHETIC_READER_CASES",
                recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                python=sys.version,optimization=sys.flags.optimize,cases=results,
                actual_game_evidence=False,SDK_game_desktop_actions=0,EXE_executions=0,
                reused_existing_normalizers=True,cold_matrix_rerun=False,
                known_producer=False,maintenance_attribution="unclosed")
    write(args.output_root/"RESULT.actual.json",report)
    print(json.dumps(report))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
