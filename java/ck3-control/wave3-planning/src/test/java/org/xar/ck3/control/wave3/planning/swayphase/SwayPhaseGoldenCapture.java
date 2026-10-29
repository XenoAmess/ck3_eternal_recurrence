package org.xar.ck3.control.wave3.planning.swayphase;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit historical-contract software capture; never current-profile FIRST qualification. */
public final class SwayPhaseGoldenCapture {
    private SwayPhaseGoldenCapture() { }
    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, sys
            from test_ck3_12002_sway_completion_execution_wire import ProtocolSwayExecutionDriver, query, load_fixture
            from xar_autoplayer.bridge.active_scheme_sway_completion_execution_private_transport import normalize_active_scheme_sway_completion_execution_v1
            from xar_autoplayer.sway_lifecycle_consumer import record_sway_phase_observation, has_pending_sway_following_turn
            from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger, consume_sway_following_turn
            root, work, machine=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
            work.mkdir(parents=True,exist_ok=False)
            fixture_path=root/'ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_sway_completion_execution/hidden-good-command-result.json'
            provenance=load_fixture('provenance.json')
            expected=provenance['payload_sha256']['hidden-good-command-result.json']
            if hashlib.sha256(fixture_path.read_bytes()).hexdigest()!=expected:
                raise RuntimeError('historical compatibility fixture SHA drifted')
            source_driver=ProtocolSwayExecutionDriver(load_fixture('hidden-good-command-result.json'))
            observed=query(source_driver)
            if source_driver.last_ingest!='command_result' or len(source_driver.sent)!=1:
                raise RuntimeError('actual historical protocol/query producer chain did not execute')
            actor,target,instance=observed['actor_character_id'],observed['target_character_id'],observed['scheme_instance_id']
            original={'status':'applied','postcondition_verified':True,'action_id':'phase-original-compatibility-episode','actor_character_id':actor,'target_character_id':target,'post_native_revision':observed['snapshot_revision']-1,'post_date_raw':observed['date_raw'],'next_turn_consumed':True,'native_receipt':{'scheme_instance_id':instance,'scheme_instance_generation':instance>>24}}
            stages=[]
            pending=[]
            def store(directory,resolved):
                (directory/LEDGER_FILE).write_text(json.dumps({'schema':SCHEMA,'pending':None,'resolved':resolved}),encoding='utf-8')
            def run_stage(name,resolved,read,java_reject=False):
                directory=work/name
                directory.mkdir()
                store(directory,resolved)
                before=(directory/LEDGER_FILE).read_bytes()
                result=record_sway_phase_observation(directory,execution_read=read)
                after=read_sway_ledger(directory)['resolved']
                row={'id':name,'input':{'resolved':copy.deepcopy(resolved),'execution_read':copy.deepcopy(read)},'expected':copy.deepcopy(result),'expected_write':before!=(directory/LEDGER_FILE).read_bytes()}
                if java_reject:
                    row['java_rejects_malformed_contract']=True
                stages.append(row)
                return directory,after
            directory,staged=run_stage('new-phase',original,observed)
            pending.append({'id':'new-phase-due','input':{'resolved':copy.deepcopy(staged)},'expected':has_pending_sway_following_turn(directory)})
            frame={'paused':True,'map_ready':True,'revision':19,'native_revision':observed['snapshot_revision']+1,'date_raw':observed['date_raw'],'played_character':{'character_id':actor,'alive':True}}
            followed=consume_sway_following_turn(directory,frame)
            if followed is None or followed['phase_intervention']['next_turn_consumed'] is not True:
                raise RuntimeError('actual following consumer did not consume the source phase')
            consumed=read_sway_ledger(directory)['resolved']
            pending.append({'id':'phase-consumed','input':{'resolved':copy.deepcopy(consumed)},'expected':has_pending_sway_following_turn(directory)})
            newer=copy.deepcopy(observed)
            newer['snapshot_revision']+=100
            run_stage('same-source-after-cold-consumption',consumed,newer)
            bad=load_fixture('hidden-bad-unresolved-wire.json')
            normalized=normalize_active_scheme_sway_completion_execution_v1(bad,snapshot={'played_character':{'character_id':actor}},target_character_id=target,scheme_instance_id=instance,after_sequence=bad['after_sequence'])
            normalized.update(exact_ck3_build=observed['exact_ck3_build'],exe_sha256=observed['exe_sha256'],snapshot_revision=observed['snapshot_revision']+1,date_raw=observed['date_raw'])
            run_stage('later-failure-phase',consumed,normalized)
            empty=copy.deepcopy(observed); empty['records']=[]
            run_stage('no-record',original,empty)
            unavailable=copy.deepcopy(observed); unavailable['available']=False
            run_stage('unavailable',original,unavailable)
            wrong=copy.deepcopy(observed); wrong['actor_character_id']+=1
            run_stage('other-actor',original,wrong)
            wrong=copy.deepcopy(observed); wrong['scheme_instance_id']+=1
            run_stage('other-full-instance',original,wrong)
            wrong=copy.deepcopy(observed); wrong['records'][-1]['scheme_instance_generation']+=1
            run_stage('wrong-record-generation',original,wrong)
            wrong=copy.deepcopy(observed); wrong['records'][-1]['sequence']=float(wrong['records'][-1]['sequence'])
            run_stage('float-source-sequence',original,wrong,True)
            wrong=copy.deepcopy(observed); wrong['records'][-1]['material_effect_observed']=True
            run_stage('hidden-branch-cannot-prove-material',original,wrong,True)
            base=copy.deepcopy(consumed)
            def pending_case(name,change,java_reject=False):
                row=copy.deepcopy(base)
                change(row)
                directory=work/('pending-'+name)
                directory.mkdir()
                store(directory,row)
                result=has_pending_sway_following_turn(directory)
                value={'id':name,'input':{'resolved':row},'expected':result}
                if java_reject:
                    value['java_rejects_malformed_contract']=True
                pending.append(value)
            pending_case('start-unconsumed',lambda row:row.update(next_turn_consumed=False))
            pending_case('start-missing',lambda row:row.pop('next_turn_consumed'))
            pending_case('start-null',lambda row:row.update(next_turn_consumed=None))
            pending_case('start-bool-alias-number',lambda row:row.update(next_turn_consumed=1),True)
            pending_case('material-unconsumed',lambda row:row.update(material_intervention={'next_turn_consumed':False}))
            pending_case('terminal-unconsumed',lambda row:row.update(terminal_intervention={'next_turn_consumed':False}))
            pending_case('unknown-stop-not-following',lambda row:row.update(stop_intervention={'postcondition_verified':False,'next_turn_consumed':False}))
            pending_case('verified-stop-following',lambda row:row.update(stop_intervention={'postcondition_verified':True,'next_turn_consumed':False}))
            gain={'action_id':original['action_id'],'actor_character_id':actor,'target_character_id':target,'scheme_instance_id':instance,'scheme_instance_generation':instance>>24,'incremental_named_gain_observed':True,'next_turn_consumed':False}
            pending_case('same-original-first-gain',lambda row:row.update(first_named_gain_intervention=copy.deepcopy(gain)))
            pending_case('foreign-first-gain',lambda row:row.update(first_named_gain_intervention={**gain,'action_id':'another-episode'}))
            previous=copy.deepcopy(original); previous['action_id']='retained-older-episode'; previous['next_turn_consumed']=False
            pending_case('previous-episode-pending',lambda row:row.update(previous_interventions=[previous]))
            paths=['ck3_autonomous_player/src/xar_autoplayer/sway_lifecycle_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_material_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/active_scheme_sway_completion_execution_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/tests/unit/test_ck3_12002_sway_completion_execution_wire.py','ck3_autonomous_player/tests/unit/test_sway_execution_lifecycle_12004.py']
            output={'schema':'xar.java.sway-phase-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'sources':[{'path':path,'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()} for path in paths],'compatibility_fixture':{'path':str(fixture_path.relative_to(root)).replace(chr(92),'/'),'sha256':expected,'game_version':provenance['game_version'],'native_origin_machine_id':'unknown','qualification':'historical-contract-software-compatibility-only-not-current-native-FIRST'},'stage_cases':stages,'pending_cases':pending,'actual_original_protocol_query_count':len(source_driver.sent),'actual_original_following_consumer_executed':True,'current_actual4_first_packet_compound_executed':False,'current_actual4_first_packet_compound_reason':'fresh current-profile FIRST packet source not bound; historical packet is not substituted','game_rpc_count':0,'canonical_ledger_write_count':0,'production_cutover':False}
            text=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            if len(text.encode())>98304:
                raise RuntimeError('bounded phase producer golden exceeds 96 KiB')
            print(text)
            """;

    public static void main(String[] args) throws Exception {
        if (args.length!=5) { throw new IllegalArgumentException("python-exe repo-root new-output new-fixture-dir machine-id required"); }
        Path python=Path.of(args[0]).toAbsolutePath().normalize(), root=Path.of(args[1]).toAbsolutePath().normalize();
        Path output=Path.of(args[2]).toAbsolutePath().normalize(), fixture=Path.of(args[3]).toAbsolutePath().normalize();
        Path allowed=Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch").toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || Files.exists(fixture) || !output.startsWith(allowed)
                || !fixture.startsWith(allowed) || args[4].isBlank()) { throw new IllegalArgumentException("new finite D scratch outputs required"); }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-c",SCRIPT,root.toString(),fixture.toString(),args[4]);
        builder.directory(root.toFile()); builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src")+";"+root.resolve("ck3_autonomous_player/tests/unit")+";"+root.resolve("tools")+";"+root.resolve("ck3_workshop_mcp/src"));
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1"); builder.environment().put("TEMP",output.getParent().toString()); builder.environment().put("TMP",output.getParent().toString());
        builder.redirectOutput(output.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process=builder.start();
        if (!process.waitFor(20,TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IllegalStateException("original phase software capture timed out; evidence retained"); }
        if (process.exitValue()!=0 || Files.size(output)==0 || Files.size(output)>98304) { throw new IllegalStateException("original phase software capture failed; output retained"); }
        System.out.println("Original phase/pending software producers captured "+Files.size(output)+" bytes; no current FIRST qualification");
    }
}
