package org.xar.ck3.control.g2.m0.integration;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Exercise static retained-file adapters and the shared Java producer with synthetic files. */
public final class M0LegacyComposerProbe {
    private M0LegacyComposerProbe() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 7) throw new IllegalArgumentException("repository, python, java, compiled-classpath, candidate-composer, static-recommendation-adapter, fresh-output-root required");
        M0FixtureConfig staticConfig = M0FixtureConfig.fromEnvironment();
        Path repository = Path.of(args[0]).toRealPath();
        Path output = Path.of(args[6]).toAbsolutePath().normalize();
        if (Files.exists(output) || !Files.isDirectory(output.getParent())) throw new IllegalArgumentException("fresh admitted probe output required");
        Files.createDirectory(output);
        Path scratch = Files.createDirectory(output.resolve("fixture-temp"));
        Path body = output.resolve("probe-body.py");
        Files.writeString(body, SCRIPT, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", body.toString(),
                repository.toString(), args[2], args[3], args[4], args[5], output.toString(),
                staticConfig.clientAdapter().path(), staticConfig.formalAdapter().path()))
                .directory(repository.toFile()).inheritIO();
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("TMP", scratch.toString()); builder.environment().put("TEMP", scratch.toString());
        builder.environment().put("TMPDIR", scratch.toString());
        builder.environment().put("PYTHONPATH", repository.toString() + java.io.File.pathSeparator + repository.resolve("ck3_autonomous_player/src") + java.io.File.pathSeparator
                + repository.resolve("ck3_workshop_mcp/src") + java.io.File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit") + java.io.File.pathSeparator
                + repository.resolve("ck3_autonomous_player/native_bridge/research"));
        Process child = builder.start();
        if (!child.waitFor(150, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
            throw new IllegalStateException("legacy composer integration timeout; shared Job owner retains terminal custody");
        }
        if (child.exitValue() != 0) throw new IllegalStateException("legacy composer integration RED, exit " + child.exitValue());
    }
    private static final String SCRIPT = """
            import sys,json,hashlib,datetime,subprocess,importlib,importlib.util,traceback,copy,math
            from pathlib import Path
            from unittest.mock import patch
            repo,java,classpath,candidate_path,adapter_path,output,client_path,formal_path=sys.argv[1:]
            repo=Path(repo); candidate_path=Path(candidate_path); adapter_path=Path(adapter_path); output=Path(output); client_path=Path(client_path); formal_path=Path(formal_path)
            sources={path:path.read_bytes() for path in (candidate_path,adapter_path,client_path,formal_path,Path(__file__).resolve())}
            from test_raiktor_white_peace_narrow_projection_provider import _snapshot,_options_query,_terms_query,WAR_ID,DEFENDER_ID
            from test_raiktor_three_way_exit_recommendation import _dominance
            from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import provide_raiktor_white_peace_narrow_projection
            snapshot=_snapshot(); options=_options_query(); terms=_terms_query()
            projection=provide_raiktor_white_peace_narrow_projection(snapshot,options,terms,production_live=True)
            source_projection=copy.deepcopy(projection)
            source_projection['white_peace_observation']['frame']['ck3_pid']+=1
            source_power=_dominance(source_projection)
            direct={'provider_result':{'campaign_dominance_certificate':source_power},'fixture_qualification':'original source factory; synthetic power-report transport'}
            readiness={'_semantic':copy.deepcopy(snapshot)}
            for key in ('snapshot_id','revision','native_revision','date_raw','paused','map_ready','episode_run_id','episode_character_id'):
                readiness[key]=snapshot.get(key)
            readiness['bridge_pid']=snapshot['diagnostics']['bridge_pid']
            readiness['connection_generation']=snapshot['diagnostics']['connection_generation']
            report={'kind':'ck3_gen034_three_way_recommendation_live_acceptance','status':'red','ok':False,'mcp_sequence':None,
                'cleanup':{'cleanup_proven':True},'readiness':readiness}
            fixture_driver={'command_history':[
                {'command':'query-war-termination-options-'+str(WAR_ID),'ok':True,'result':options},
                {'command':'query-war-termination-terms-v1-'+str(WAR_ID),'ok':True,'result':terms},
                {'command':'query-war-entry-assessments-v1-1-'+str(DEFENDER_ID),'ok':False,'error':'application-main war-entry query failed; explicit software fixture'},
            ]}
            def canon(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            def write_fixture(name,value):
                path=output/'fixture-temp'/name
                raw=value if isinstance(value,bytes) else canon(value).encode('utf-8')
                with path.open('xb') as stream:stream.write(raw)
                return path,hashlib.sha256(raw).hexdigest().upper()
            power_path,power_sha=write_fixture('power-report-fixture.json',{'fixture':True})
            class_path,class_sha=write_fixture('power-reclassification-fixture.json',{'fixture':True})
            report_path,report_sha=write_fixture('failed-exit-report-fixture.json',report)
            driver_path,driver_sha=write_fixture('retained-exit-fixture.json',fixture_driver)
            checkpoint_path,checkpoint_sha=write_fixture('immutable-checkpoint-fixture.bin',b'explicit synthetic checkpoint fixture; never a CK3 save')
            source_driver_path,source_driver_sha=write_fixture('source-state-fixture.bin',b'explicit synthetic source-state fixture; never an actual Driver')
            kwargs={'power_report_path':power_path,'power_report_sha256':power_sha,
                'power_reclassification_path':class_path,'power_reclassification_sha256':class_sha,
                'exit_report_path':report_path,'exit_report_sha256':report_sha,
                'exit_driver_state_path':driver_path,'exit_driver_state_sha256':driver_sha,
                'checkpoint_path':checkpoint_path,'checkpoint_sha256':checkpoint_sha,
                'source_driver_state_path':source_driver_path,'source_driver_state_sha256':source_driver_sha,
                'war_id':WAR_ID,'opponent_character_id':DEFENDER_ID}
            old_red=None  # Prior real failure stays immutable in baseline delivery; not reexecuted.
            worker=None; calls=0; decisions=0; terminal_producers=0; normalizations=0; failures=[]; terminal_exit=None
            def evaluate(payload):
                global worker,calls,decisions,terminal_producers,normalizations
                if worker is None:
                    worker=subprocess.Popen([java,'-Xms8m','-Xmx32m','-XX:+UseSerialGC','-XX:ActiveProcessorCount=2',
                        '-XX:MaxMetaspaceSize=48m','-XX:ReservedCodeCacheSize=8m','-XX:MaxDirectMemorySize=8m','-Xss256k','-cp',classpath,
                        'org.xar.ck3.control.g2.m0.integration.M0UnionStdioAdapter','--stdio'],
                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=sys.stderr,text=True,encoding='utf-8',bufsize=1)
                line=canon(payload)
                if len(line.encode())>1048576:raise ValueError('finite M0 request required')
                worker.stdin.write(line+'\\n');worker.stdin.flush();calls+=1
                raw=worker.stdout.readline(1048577)
                if not raw or not raw.endswith('\\n'):raise RuntimeError('actual compiled M0 response unavailable')
                result=json.loads(raw)
                if result.get('rejected') is True:raise ValueError(result['message'])
                if payload.get('operation')=='project-terminal-control-from-snapshot':terminal_producers+=1
                elif payload.get('operation','').startswith('normalize-'):normalizations+=1
                else:decisions+=1
                if json.loads(canon(result))!=result:raise AssertionError('compiled response persisted JSON drift')
                return result
            def load_static(name,path):
                spec=importlib.util.spec_from_file_location(name,path)
                module=importlib.util.module_from_spec(spec);sys.modules[name]=module
                spec.loader.exec_module(module);return module
            import tools.g2_saved_campaign
            client=load_static('tools.g2_saved_campaign.java_map_admission_client_v1',client_path)
            import xar_autoplayer.simulation
            replacement=load_static('xar_autoplayer.simulation.raiktor_three_way_exit_recommendation',adapter_path)
            production_invoke=replacement._invoke_java_m0
            replacement._invoke_java_m0=evaluate
            setattr(xar_autoplayer.simulation,'raiktor_three_way_exit_recommendation',replacement)
            candidate=load_static('m0_candidate_replay',candidate_path)
            results={};success=False
            try:
                observation=copy.deepcopy(projection['white_peace_observation'])
                observation['option']['_software_wire_numeric_probe']=[1,1.0,-0.0]
                session=copy.deepcopy(terms['raiktor_surrender_aggregate_session'])
                session['aggregate']['_software_wire_numeric_probe']=[1,1.0,-0.0]
                normalized_observation=evaluate({'operation':'normalize-white-peace-observation','value':observation})
                normalized_session=evaluate({'operation':'normalize-surrender-session','value':session,'expected':session['binding']})
                for value in (normalized_observation['option']['_software_wire_numeric_probe'],normalized_session['aggregate']['_software_wire_numeric_probe']):
                    if type(value[0]) is not int or type(value[1]) is not float or type(value[2]) is not float or math.copysign(1.0,value[2])!=-1.0:
                        raise AssertionError('normalization G2 request/response wire changed opaque numeric JSON types')
                if normalized_observation!=observation or normalized_session!=session:
                    raise AssertionError('normalization G2 request/response wire changed actual fixture contents')
                results['normalization_common_wire_roundtrips']={'operations':2,'integer_and_float_distinct':True,'negative_zero_preserved':True}
                with patch.object(candidate,'render_direct_dominance_receipt',return_value=copy.deepcopy(direct)):
                    replacement._invoke_java_m0=production_invoke
                    try:candidate.compose_recommendation(**kwargs)
                    except client.ProjectionUnavailable as error:
                        results['missing_root_context']={'type':type(error).__name__,'message':str(error),'actual_http':False}
                    else:raise AssertionError('missing Root context did not remain typed unavailable')
                    finally:replacement._invoke_java_m0=evaluate
                    positive=candidate.compose_recommendation(**kwargs)
                    if positive.get('status')!='GREEN' or positive.get('ok') is not True:
                        raise AssertionError('legitimate six-argument Java composition did not complete its software contract')
                    if positive['decision']['action_submitted'] is not False or positive['decision']['postcondition_verified'] is not False:
                        raise AssertionError('software replay fabricated actual action or poststate')
                    persisted=json.loads(canon(positive))
                    if persisted!=positive:raise AssertionError('full composer report JSON representation drift')
                    cert=positive['recommendation']['recommendation_certificate']
                    unhashed={k:v for k,v in cert.items() if k!='certificate_sha256'}
                    if hashlib.sha256(canon(unhashed).encode()).hexdigest().upper()!=cert['certificate_sha256']:
                        raise AssertionError('Java composition changed original certificate hash')
                    results['java_producer_and_decision']=positive
                    def crossed(payload):
                        wrong=copy.deepcopy(payload)
                        if wrong.get('operation')=='project-terminal-control-from-snapshot':wrong['snapshot']['date_raw']+=24
                        return evaluate(wrong)
                    replacement._invoke_java_m0=crossed
                    try:candidate.compose_recommendation(**kwargs)
                    except ValueError as error:results['crossed_frame_rejected']={'type':type(error).__name__,'message':str(error)}
                    else:raise AssertionError('crossed source snapshot became a terminal-control input')
                    finally:replacement._invoke_java_m0=evaluate
                success=True
            except BaseException:failures.append(traceback.format_exc())
            finally:
                if worker is not None:
                    try:worker.stdin.close()
                    except (BrokenPipeError,OSError) as error:failures.append(str(error))
                    try:terminal_exit=worker.wait(timeout=15)
                    except subprocess.TimeoutExpired:worker.kill();terminal_exit=worker.wait(timeout=15);failures.append('M0 worker finite close failed')
            changed=[str(path) for path,raw in sources.items() if path.read_bytes()!=raw]
            success=success and not failures and not changed and terminal_exit==0 and terminal_producers>=1 and decisions>=1 and normalizations==2
            machine=subprocess.check_output([sys.executable,'-B',str(repo/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
            receipt={'schema':'xar.g2-m0-legacy-composer-adoption/v2','status':'PASS' if success else 'RED',
                'machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_refs':[{'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for path,raw in sources.items()],
                'sources_changed':changed,'original_failure':old_red,'results':results,'failures':failures,
                'actual_java_calls':calls,'actual_java_terminal_producer_calls':terminal_producers,'actual_java_decision_calls':decisions,'actual_java_normalization_calls':normalizations,'java_process_exit':terminal_exit,
                'qualification':{'kind':'software_fixture_only','power_report_transport':'mock returns unchanged original factory-produced certificate',
                    'all_game_state_files':'explicit synthetic test files; no real Driver or SAVE',
                    'actual_http':False,'runtime_takeover':False,'action_authorized':False,'action_submitted':False,'postcondition_verified':False,'cold_restore_verified':False,'new_game_days':0}}
            raw=(canon(receipt)+'\\n').encode('utf-8')
            if len(raw)>262144:raise ValueError('finite replay integration receipt exceeded')
            with (output/'actual.json').open('xb') as stream:stream.write(raw)
            print(json.dumps({'status':receipt['status'],'java_calls':calls,'terminal_producer_calls':terminal_producers,'decision_calls':decisions,'bytes':len(raw)}))
            if not success:raise SystemExit(1)
            """;
}
