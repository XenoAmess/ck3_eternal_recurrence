package org.xar.ck3.control.wave3.planning.swaystop;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Actual original pure eligibility/consumer routes with existing explicit synthetic source fixtures. */
public final class SwayStopGoldenCapture {
    private SwayStopGoldenCapture() { }
    private static final String SCRIPT = """
            import copy, datetime, hashlib, json, pathlib, sys
            from test_ordinary_sway_lifecycle_observation_v1 import SourceDriver
            from test_sway_selected_stop_compound_12004 import WholePacketSelectedStopDriver, ACTOR, TARGET, INSTANCE, GENERATION, DATE, NATIVE_REVISION
            from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, SCHEMA, read_sway_ledger
            from xar_autoplayer.sway_lifecycle_consumer import record_sway_terminal_observation, record_sway_material_from_completion
            from xar_autoplayer.sway_stop_consumer import should_finish_sway, consume_sway_stop_private_once, _observe_stop
            root, work, machine=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
            work.mkdir(parents=True,exist_ok=False)
            def original_episode():
                return {'status':'applied','postcondition_verified':True,'actor_character_id':ACTOR,'target_character_id':TARGET,'action_id':'sway-original','post_native_revision':NATIVE_REVISION-1,'post_date_raw':DATE-24,'next_turn_consumed':True,'native_receipt':{'scheme_instance_id':INSTANCE,'scheme_instance_generation':GENERATION}}
            def store(directory,resolved,pending=None):
                (directory/LEDGER_FILE).write_text(json.dumps({'schema':SCHEMA,'pending':pending,'resolved':resolved}),encoding='utf-8')
            def driver(directory):
                value=SourceDriver(directory)
                value.frame.update(snapshot_id='selected-sway-fixture',revision=17,native_revision=NATIVE_REVISION,date_raw=DATE)
                return value
            initial=work/'base'
            initial.mkdir()
            native_driver=driver(initial)
            snapshot=native_driver.take_snapshot()
            store(initial,original_episode())
            completion=native_driver.query_active_scheme_sway_completion_private_v1(expected_revision=snapshot['revision'],target_character_id=TARGET,scheme_instance_id=INSTANCE)
            record_sway_terminal_observation(initial,completion_read=completion)
            # Existing synthetic target/opinion producers, never the unavailable native packet corpus.
            readback=WholePacketSelectedStopDriver._target_packet(None)['result']['active_scheme_sway']
            readback.update(queried_snapshot_id=snapshot['snapshot_id'],queried_revision=snapshot['revision'],queried_native_revision=snapshot['native_revision'])
            opinion=WholePacketSelectedStopDriver._opinion_packet(None)['result']['sway_outcome_opinion']
            opinion.update(exact_ck3_build=completion['exact_ck3_build'],exe_sha256=completion['exe_sha256'])
            record_sway_material_from_completion(initial,opinion_read=opinion)
            base={'snapshot':snapshot,'readback':readback,'resolved':read_sway_ledger(initial)['resolved'],'target_character_id':TARGET,'opinion_read':opinion}
            if should_finish_sway(snapshot,readback,base['resolved'],TARGET,opinion) is not True:
                raise RuntimeError('actual original eligibility baseline is not true')
            eligibility=[]
            def change(path,value):
                return {'path':path.split('.'),'value':value}
            def capture(name,mutations,java_reject=False):
                value=copy.deepcopy(base)
                for mutation in mutations:
                    parent=value
                    for key in mutation['path'][:-1]:
                        parent=parent[key]
                    parent[mutation['path'][-1]]=mutation['value']
                try:
                    expected=should_finish_sway(value['snapshot'],value['readback'],value['resolved'],value['target_character_id'],value['opinion_read'])
                    case={'id':name,'mutations':mutations,'expected':expected}
                except ValueError as error:
                    case={'id':name,'mutations':mutations,'expected_error_kind':type(error).__name__}
                if java_reject:
                    case['java_rejects_malformed_numeric_contract']=True
                eligibility.append(case)
            capture('current-positive-named-benefit',[])
            capture('opinion-ceiling-50',[change('readback.target_opinion_of_actor',50),change('opinion_read.target_opinion_of_actor',50)])
            capture('opinion-above-ceiling-51',[change('readback.target_opinion_of_actor',51),change('opinion_read.target_opinion_of_actor',51)])
            capture('fresh-named-zero',[change('opinion_read.scheme_sway_opinion.value',0)])
            capture('fresh-named-negative',[change('opinion_read.scheme_sway_opinion.value',-10)])
            capture('fresh-named-unobserved',[change('opinion_read.scheme_sway_opinion.observed',False)])
            capture('fresh-opinion-stale',[change('opinion_read.date_raw',DATE-24)])
            capture('material-current-fallback',[change('opinion_read',None)])
            capture('material-stale-fallback',[change('opinion_read',None),change('resolved.material_intervention.source_date_raw',DATE-24)])
            capture('native-other-owner',[change('resolved.latest_instance_observation.native_observation.native_owner_raw',ACTOR+1)])
            capture('native-ended',[change('resolved.latest_instance_observation.native_observation.native_status_raw',1)])
            capture('matching-active-false',[change('readback.matching_sway_active',False)])
            capture('unverified-original',[change('resolved.postcondition_verified',False)])
            capture('target-read-wrong-public-revision',[change('readback.queried_revision',18)])
            capture('float-named-points',[change('opinion_read.scheme_sway_opinion.value',45.0)],True)
            capture('bool-native-status',[change('resolved.latest_instance_observation.native_observation.native_status_raw',False)],True)
            capture('float-native-owner',[change('resolved.latest_instance_observation.native_observation.native_owner_raw',float(ACTOR))],True)
            routes=[]
            selected={'expected_revision':snapshot['revision'],'target_character_id':TARGET,'scheme_instance_id':INSTANCE,'scheme_instance_generation':GENERATION}
            original_stop={'status':'stop_submission_unresolved','action_id':'stop-sway-existing-fixture-intent','original_action_id':base['resolved']['action_id'],'actor_character_id':ACTOR,'target_character_id':TARGET,'scheme_instance_id':INSTANCE,'scheme_instance_generation':GENERATION,'pre_native_revision':NATIVE_REVISION,'pre_date_raw':DATE,'pre_target_opinion_of_actor':61,'pre_material_opinion_read':copy.deepcopy(opinion),'decision':'finish_selected_active_relation','postcondition_verified':False}
            for name,pending,previous in [('no-native-entry',None,None),('existing-start-pending',{'action_id':'unknown-start'},None),('existing-stop-pending',None,original_stop),('already-terminal',None,{**original_stop,'postcondition_verified':True})]:
                directory=work/name
                directory.mkdir()
                retained=copy.deepcopy(base['resolved'])
                if previous is not None:
                    retained['stop_intervention']=copy.deepcopy(previous)
                store(directory,retained,pending)
                source_driver=driver(directory)
                before=read_sway_ledger(directory)
                result=consume_sway_stop_private_once(source_driver,target_character_id=TARGET,snapshot=snapshot,readback=readback,opinion_read=opinion)
                routes.append({'id':name,'input':{'ledger':before,'snapshot':snapshot,'selected_request':selected,'readback':readback,'opinion_read':opinion,'native_stop_entry':'unavailable'},'original_status':result['status'],'actual_existing_fixture_read_calls':len(source_driver.calls),'native_stop_calls':0})
            posts=[]
            for name,mode in [('current','current'),('terminal','terminal'),('purged-synthetic-control','purged'),('reused-synthetic-control','reused')]:
                directory=work/('post-'+name)
                directory.mkdir()
                retained=copy.deepcopy(base['resolved'])
                retained['stop_intervention']=copy.deepcopy(original_stop)
                store(directory,retained)
                source_driver=driver(directory)
                source_driver.terminal=mode=='terminal'
                original_query=source_driver.query_active_scheme_sway_completion_private_v1
                captured=[]
                def query(**arguments):
                    value=original_query(**arguments)
                    if mode in ('purged','reused'):
                        value.update(instance_present=False,storage_slot_reused=mode=='reused',exact_instance_join_ready=False,owner_matches_actor=False,native_owner_raw=None,native_status_observed=False,native_status_raw=None,native_status_key='unobserved',native_terminal_state_observed=False)
                    captured.append(copy.deepcopy(value))
                    return value
                source_driver.query_active_scheme_sway_completion_private_v1=query
                result=_observe_stop(source_driver,retained,original_stop)
                if len(captured)!=1:
                    raise RuntimeError('original independent Stop observer did not issue exactly one read')
                posts.append({'id':name,'input':{'resolved':retained,'stop':original_stop,'snapshot':snapshot,'completion_read':captured[0]},'expected':result,'native_inputs':'explicit-synthetic-existing-SourceDriver-control-not-native-packet'})
            paths=['ck3_autonomous_player/src/xar_autoplayer/sway_stop_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_lifecycle_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_material_consumer.py','ck3_autonomous_player/src/xar_autoplayer/sway_end_causal_consumer_12004.py','ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/tests/unit/test_ordinary_sway_lifecycle_observation_v1.py','ck3_autonomous_player/tests/unit/test_sway_selected_stop_compound_12004.py']
            output={'schema':'xar.java.sway-stop-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'sources':[{'path':path,'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()} for path in paths],'base':base,'eligibility_cases':eligibility,'route_cases':routes,'postcondition_cases':posts,'game_rpc_count':0,'canonical_ledger_write_count':0,'native_stop_calls':0,'full_actual4_packet_compound_executed':False,'full_actual4_packet_compound_reason':'required-five-role-original-source-manifest-not-bound; no replacement fabricated','production_cutover':False}
            text=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            if len(text.encode('utf-8'))>262144:
                raise RuntimeError(f'finite Stop producer golden exceeds 256 KiB: {len(text.encode())} bytes')
            print(text)
            """;

    public static void main(String[] args) throws Exception {
        if (args.length!=5) { throw new IllegalArgumentException("python-exe repo-root new-output new-fixture-dir machine-id required"); }
        Path python=Path.of(args[0]).toAbsolutePath().normalize(), root=Path.of(args[1]).toAbsolutePath().normalize();
        Path output=Path.of(args[2]).toAbsolutePath().normalize(), fixture=Path.of(args[3]).toAbsolutePath().normalize();
        Path allowed=Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch").toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || Files.exists(fixture) || !output.startsWith(allowed)
                || !fixture.startsWith(allowed) || args[4].isBlank()) { throw new IllegalArgumentException("new bounded D scratch outputs required"); }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-c",SCRIPT,root.toString(),fixture.toString(),args[4]);
        builder.directory(root.toFile()); builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src")+";"+root.resolve("ck3_autonomous_player/tests/unit")+";"+root.resolve("tools")+";"+root.resolve("ck3_workshop_mcp/src"));
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1"); builder.environment().put("TEMP",output.getParent().toString()); builder.environment().put("TMP",output.getParent().toString());
        builder.redirectOutput(output.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process=builder.start();
        if (!process.waitFor(20,TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IllegalStateException("original Stop producer capture timed out; evidence retained"); }
        if (process.exitValue()!=0 || Files.size(output)==0 || Files.size(output)>65536) { throw new IllegalStateException("original Stop producer capture failed; output retained"); }
        System.out.println("Original Stop software producers captured "+Files.size(output)+" bytes; full packet compound not executed");
    }
}
