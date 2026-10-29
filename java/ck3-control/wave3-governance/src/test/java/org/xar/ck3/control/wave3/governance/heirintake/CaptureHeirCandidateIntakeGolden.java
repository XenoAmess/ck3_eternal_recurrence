package org.xar.ck3.control.wave3.governance.heirintake;

import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit centrally scheduled old intake plus actual planning-consumer capture. */
public final class CaptureHeirCandidateIntakeGolden {
    private CaptureHeirCandidateIntakeGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository, Python executable, new output required"); }
        String script = """
                import sys,json,hashlib,datetime,subprocess,tempfile
                from pathlib import Path
                from copy import deepcopy
                root=Path(sys.argv[1]).resolve()
                output=Path(sys.argv[2]).resolve()
                scratch=(output.parent.parent/'scratch').resolve()
                if not scratch.is_dir():
                    raise RuntimeError('shared scratch directory is required')
                sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
                from test_family_marriage_formal_consumer import FamilyConsumerTest,scene
                from xar_autoplayer.family_marriage_formal_consumer import _rank_five_family_candidates,plan_family_marriage_private
                machine=subprocess.run([sys.executable,'-B',str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
                def base():
                    return FamilyConsumerTest._c9_rank_driver(scratch/'unused-no-io-fixture')
                scenes=[]
                normal=base()
                scenes.append(('c9-lower-acceptance-peer-precedes-old-top-five',normal,[],True))
                absence=base()
                source=deepcopy(absence.legality['native_legal_candidates'][-1])
                rich=deepcopy(absence.projection['rows'][-1])
                for candidate,dynasty,acceptance in ((999,-1,10000),(1000,None,94)):
                    new_source={**source,'candidate_character_id':candidate,'candidate_dynasty_id':dynasty,'recipient_ai_accept_raw':acceptance}
                    absence.legality['native_legal_candidates'].append(new_source)
                    absence.projection['rows'].append({**rich,'candidate_character_id':candidate,
                        'candidate_dynasty_id':None,'candidate_house_id':None})
                scenes.append(('minus-one-absence-and-null-unknown-remain-distinct',absence,[],True))
                nopeer=base()
                for index,age in ((5,1),(6,60)):
                    nopeer.legality['native_legal_candidates'][index]['candidate_adult_measure_raw']=age
                    nopeer.projection['rows'][index].update(candidate_adult_measure_raw=age,candidate_is_adult=age>=16)
                scenes.append(('no-peer-still-uses-original-fresh-fallback',nopeer,[],True))
                unknown=base()
                for row in unknown.legality['native_legal_candidates']:
                    row['candidate_dynasty_id']=None
                scenes.append(('all-unknown-counts-and-fallback-are-observable',unknown,[],True))
                refused=base()
                scenes.append(('refused-rows-fill-diagnostics-after-fresh-candidates',refused,[300,301,302,303,304],False))
                short=base()
                short.legality['native_legal_candidates']=short.legality['native_legal_candidates'][:2]
                short.projection['rows']=short.projection['rows'][:2]
                scenes.append(('fewer-than-five-stops-before-rich-query',short,[],True))
                allrefused=base()
                scenes.append(('all-refused-are-diagnostic-fallback-not-new-eligibility',allrefused,list(range(300,307)),False))
                vectors=[]
                for name,driver,refused_ids,run_consumer in scenes:
                    request={'legal_rows':deepcopy(driver.legality['native_legal_candidates']),'rejected_candidate_ids':refused_ids}
                    before=deepcopy(request)
                    picked,ranking=_rank_five_family_candidates(request['legal_rows'],rejected_candidate_ids=frozenset(refused_ids))
                    vector={'name':name,'input':before,'expected':{'picked':picked,'ranking':ranking},
                        'consumer_executed':run_consumer}
                    if run_consumer:
                        directory=Path(tempfile.mkdtemp(prefix='heir-intake-consumer-',dir=str(scratch))).resolve()
                        if directory.parent!=scratch:
                            raise RuntimeError('temporary consumer directory escaped shared scratch')
                        try:
                            driver.state_dir=directory
                            requests=[]
                            original_read=driver.query_first_heir_candidate_alliance_projection_private_v1
                            def record_read(*,legality,candidate_character_ids):
                                requests.append({'candidate_character_ids':deepcopy(candidate_character_ids)})
                                return original_read(legality=legality,candidate_character_ids=candidate_character_ids)
                            driver.query_first_heir_candidate_alliance_projection_private_v1=record_read
                            planned=plan_family_marriage_private(driver,{'plan':{'selected_step':'life-advance'}},scene())['plan']
                            if any(call in ('submit','result','alliance') for call in driver.calls):
                                raise RuntimeError('pure planning consumer executed an action/result path')
                            diagnostic=planned.get('family_marriage_private_diagnostic')
                            vector['consumer']={'calls':driver.calls,'rich_requests':requests,
                                'ranking':diagnostic['ranking'] if diagnostic is not None else None,
                                'family_marriage_status':planned.get('family_marriage_status'),
                                'selected_step':planned.get('selected_step'),'game_action':False}
                        finally:
                            directory.rmdir()
                    if request!=before:
                        raise RuntimeError('actual intake producer mutated its input')
                    vectors.append(vector)
                sources=[]
                for relative in ('ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py',
                                 'ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py'):
                    source=root/relative
                    sources.append({'path':relative,'bytes':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
                result={'schema':'xar.ck3.heir-candidate-intake.actual-producer-consumer-golden.v1','machine_id':machine,
                    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_kind':'actual-original-intake-and-plan-consumer-with-existing-offline-read-fixtures',
                    'game_or_rpc':False,'ledger_written':False,'native_source_qualification':False,'sources':sources,'cases':vectors}
                raw=(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>65536:
                    raise RuntimeError('bounded intake golden exceeds 65536 bytes; actual='+str(len(raw)))
                with output.open('xb') as target:
                    target.write(raw)
                print(json.dumps({'path':str(output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'case_count':len(vectors),
                    'actual_plan_consumer_count':sum(value['consumer_executed'] for value in vectors),'machine_id':machine}))
                """;
        Process child = new ProcessBuilder(Path.of(arguments[1]).toRealPath().toString(), "-B", "-X", "utf8", "-c", script,
                Path.of(arguments[0]).toRealPath().toString(), Path.of(arguments[2]).toString())
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly);
            child.destroyForcibly().waitFor();
            throw new IllegalStateException("actual intake/consumer capture timed out");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("actual intake/consumer capture failed: " + child.exitValue()); }
    }
}
