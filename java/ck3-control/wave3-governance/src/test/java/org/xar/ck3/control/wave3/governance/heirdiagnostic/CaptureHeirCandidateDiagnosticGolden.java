package org.xar.ck3.control.wave3.governance.heirdiagnostic;

import java.nio.file.Path;
import org.xar.ck3.control.wave3.governance.capture.ReferenceSourceClosureCapture;
import java.util.concurrent.TimeUnit;

/** Centrally scheduled actual old helper and submit-consumer pre-write-boundary capture. */
public final class CaptureHeirCandidateDiagnosticGolden {
    private CaptureHeirCandidateDiagnosticGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 5) { throw new IllegalArgumentException("repository, Python executable, new output, exact closure gzip and SHA required"); }
        ReferenceSourceClosureCapture.verify(Path.of(arguments[0]).toRealPath(), Path.of(arguments[3]).toRealPath(), arguments[4]);
        String script = """
                import sys,json,hashlib,datetime,subprocess,tempfile
                from pathlib import Path
                from copy import deepcopy
                from unittest.mock import patch
                root=Path(sys.argv[1]).resolve()
                output=Path(sys.argv[2]).resolve()
                scratch=(output.parent.parent/'scratch').resolve()
                if not scratch.is_dir():
                    raise RuntimeError('shared scratch directory required')
                import gzip,io,re
                closure_path=Path(sys.argv[3]).resolve()
                closure_bytes=closure_path.read_bytes()
                if len(closure_bytes)>131072 or hashlib.sha256(closure_bytes).hexdigest()!=sys.argv[4]:
                    raise RuntimeError('exact bounded external source closure bytes changed')
                with gzip.GzipFile(fileobj=io.BytesIO(closure_bytes),mode='rb') as closure_file:
                    expanded=closure_file.read(1048577)
                if len(expanded)>1048576:
                    raise RuntimeError('external source closure decompression budget exceeded')
                def unique_object(pairs):
                    result={}
                    for key,value in pairs:
                        if key in result: raise RuntimeError('duplicate external closure field')
                        result[key]=value
                    return result
                closure=json.loads(expanded,object_pairs_hook=unique_object)
                if (type(closure) is not dict or closure.get('schema')!='xar.education-service-source-pins/v2'
                    or closure.get('machine_id')!='xenoamess-full-tower-eb9d2c1186'
                    or Path(closure.get('repository','')).resolve()!=root or type(closure.get('files')) is not list
                    or not 1<=len(closure['files'])<=4096):
                    raise RuntimeError('qualified complete original source closure profile required')
                source_rows=[]
                seen_sources=set()
                for row in closure['files']:
                    if (type(row) is not dict or set(row)!={'path','bytes','sha256','role'} or type(row['path']) is not str
                        or type(row['bytes']) is not int or row['bytes']<0 or type(row['sha256']) is not str
                        or re.fullmatch('[0-9a-f]{64}',row['sha256']) is None
                        or row['role'] not in ('PRODUCTION','REFERENCE','INTERPRETER_BOOTSTRAP')):
                        raise RuntimeError('strict original source reference required')
                    path=Path(row['path']).resolve()
                    if not path.is_relative_to(root) or path in seen_sources:
                        raise RuntimeError('unique original repository-contained source path required')
                    seen_sources.add(path)
                    source_rows.append((path,row['bytes'],row['sha256']))
                extra_rows=[]
                for relative in ('ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py',
                                 'ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py',
                                 'tools/ck3_live_run_id.py'):
                    path=(root/relative).resolve()
                    raw=path.read_bytes()
                    extra_rows.append((path,len(raw),hashlib.sha256(raw).hexdigest()))
                def verify_complete_sources():
                    for path,size,digest in source_rows+extra_rows:
                        raw=path.read_bytes()
                        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest:
                            raise RuntimeError('actual original source drift: '+str(path))
                    production=root/'ck3_autonomous_player/src/xar_autoplayer'
                    expected={path for path,size,digest in source_rows if path.is_relative_to(production) and path.suffix=='.py'}
                    if {path.resolve() for path in production.rglob('*.py')}!=expected:
                        raise RuntimeError('the complete original production module inventory changed')
                verify_complete_sources()
                
                sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
                from test_family_marriage_formal_consumer import FakeDriver,scene
                from xar_autoplayer import family_marriage_formal_consumer as original
                machine=subprocess.run([sys.executable,'-B',str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
                class StopBeforeWrite(Exception):
                    pass
                def consumer(driver,plan,snapshot,mutator=None):
                    plan=deepcopy(plan)
                    if mutator is not None:
                        mutator(plan['family_marriage_private_diagnostic'])
                    calls=[]
                    def stop_before_write(state_dir,value):
                        calls.append(deepcopy(value['pending']['selected_value_projection']))
                        raise StopBeforeWrite()
                    try:
                        with patch.object(original,'bridge_process_identity',return_value=(55,'created')):
                            with patch.object(original,'_write',side_effect=stop_before_write):
                                original.submit_family_marriage_private(driver,plan=plan,snapshot=snapshot)
                    except StopBeforeWrite:
                        if len(calls)!=1:
                            raise RuntimeError('unexpected write-boundary count')
                        return {'stage':'stopped_before_first_write','write_callback_count':1,
                            'selected_value_projection':calls[0],'native_submit_count':driver.calls.count('submit'),
                            'pending_written':False}
                    except ValueError as error:
                        if calls:
                            raise RuntimeError('rejection occurred after write boundary')
                        return {'stage':'rejected_before_write','message':str(error),'write_callback_count':0,
                            'native_submit_count':driver.calls.count('submit'),'pending_written':False}
                    raise RuntimeError('original submit unexpectedly returned')
                vectors=[]
                for index,name in enumerate(('base-five-selected-with-missing-optional-native-fields',
                        'native-facts-relations-and-pair-projection','unknown-partner-and-nonpositive-send-remain-unselected')):
                    directory=Path(tempfile.mkdtemp(prefix='heir-diagnostic-consumer-',dir=str(scratch))).resolve()
                    if directory.parent!=scratch:
                        raise RuntimeError('fixture directory escaped shared scratch')
                    try:
                        driver=FakeDriver(directory)
                        snapshot=scene()
                        if index==1:
                            for ordinal,row in enumerate(driver.projection['rows']):
                                row.update(candidate_betrothed_character_id=None,candidate_primary_spouse_character_id=None,
                                    candidate_spouse_character_ids=[],native_candidate_fertility_floor_raw=10000,
                                    heir_native_fertility={'effective_raw':15000,'extension_present':True,'native_gate_allows':True,
                                        'native_gate_evaluated':True,'source':'native_marriage_fertility_input'},
                                    candidate_native_fertility={'effective_raw':-1 if ordinal==1 else 50000,'extension_present':True,
                                        'native_gate_allows':None,'native_gate_evaluated':False,'source':'native_marriage_fertility_input'},
                                    candidate_native_fertility_floor_comparison_v1={'ready':ordinal!=1,'passes':None if ordinal==1 else True},
                                    heir_native_scorer_age_override_raw=-1,candidate_native_scorer_age_override_raw=-1,
                                    native_candidate_scorer_age_upper_raw=45,
                                    heir_native_scorer_effective_age_v1={'effective_raw':16,'ready':True},
                                    candidate_native_scorer_effective_age_v1={'effective_raw':16,'ready':True},
                                    candidate_native_scorer_age_branch_v1={'ready':True,'passes':True,'selector_zero_bypass':False,
                                        'first_comparison':{'ready':False,'passes':None},
                                        'second_comparison':{'ready':True,'passes':True,'adjusted_candidate_age_raw':16,'subject_adult_deficit_raw':0}},
                                    possible_alliance_pairs=[{'first_character_id':101,'second_character_id':400+ordinal,
                                        'already_allied':False,'both_have_realm_data':True,'would_attempt_if_accepted':True,
                                        'sdk_extension_omitted_by_diagnostic':True}])
                        if index==2:
                            for source,row in zip(driver.legality['native_legal_candidates'],driver.projection['rows']):
                                row['heir_spouse_character_ids']=None
                                source['recipient_ai_accept_raw']=0
                                row['candidate_spouse_character_ids']=None
                        planned=original.plan_family_marriage_private(driver,{'plan':{'selected_step':'life-advance'}},snapshot)['plan']
                        diagnostic=planned['family_marriage_private_diagnostic']
                        request={'legality':deepcopy(driver.legality),'projection':deepcopy(driver.projection),
                            'snapshot':deepcopy(snapshot),'choice':deepcopy(planned.get('family_marriage_choice')),
                            'ranking':deepcopy(diagnostic['ranking']),'rejected_candidate_ids':[]}
                        before=deepcopy(request)
                        expected=original._private_five_candidate_diagnostic(request['legality'],request['projection'],
                            request['snapshot'],request['choice'],request['ranking'],rejected_candidate_ids=frozenset())
                        if diagnostic!=expected or request!=before:
                            raise RuntimeError('original plan consumer/helper mismatch or mutated input')
                        vector={'name':name,'input':before,'expected':expected,
                            'plan_consumer':{'diagnostic_matches':True,'calls':deepcopy(driver.calls),'selected_step':planned['selected_step']}}
                        if request['choice'] is not None:
                            normal=consumer(driver,planned,snapshot)
                            if normal['stage']!='stopped_before_first_write' or normal['native_submit_count']!=0:
                                raise RuntimeError('original submit did not stop before pending write')
                            vector['submit_consumer']=normal
                            if index==0:
                                mutations=(('selected-id',lambda d:d.update(selected_candidate_character_id=999)),
                                    ('native-revision',lambda d:d.update(native_revision=8)),
                                    ('query-sequence',lambda d:d.update(legality_query_sequence=3)),
                                    ('date',lambda d:d.update(date_raw=53215921)),
                                    ('episode',lambda d:d.update(episode_run_id='other')),
                                    ('build',lambda d:d.update(exact_ck3_build='other')),
                                    ('projection-schema',lambda d:d.update(source_projection_schema='other')),
                                    ('selected-rejection',lambda d:d['rows'][0].update(rejection_reasons=['candidate_previously_refused'])),
                                    ('recipient-role',lambda d:d['rows'][0].update(recipient_character_id=999)))
                                refusals=[]
                                for label,mutate in mutations:
                                    result=consumer(driver,planned,snapshot,mutate)
                                    if result['stage']!='rejected_before_write' or result['native_submit_count']!=0:
                                        raise RuntimeError('original consumer accepted diagnostic drift: '+label)
                                    refusals.append({'mutation':label,**result})
                                vector['submit_drift_rejections']=refusals
                        else:
                            vector['submit_consumer']={'stage':'unselected-no-submit','native_submit_count':0,'pending_written':False}
                        if any(call in ('submit','result','alliance') for call in driver.calls) or list(directory.iterdir()):
                            raise RuntimeError('diagnostic capture touched native action or ledger')
                        vectors.append(vector)
                    finally:
                        directory.rmdir()
                sources=[]
                for relative in ('ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py',
                                 'ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py'):
                    source=root/relative
                    sources.append({'path':relative,'bytes':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
                result={'schema':'xar.ck3.heir-candidate-diagnostic.actual-producer-consumer-golden.v1','machine_id':machine,
                    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_kind':'actual-original-helper-plan-and-submit-prewrite-consumers-with-offline-fixture-io-boundaries',
                    'game_or_rpc':False,'ledger_written':False,'native_source_qualification':False,'sources':sources,'cases':vectors}
                verify_complete_sources()
                bound_paths=seen_sources|{path for path,size,digest in extra_rows}
                for module in list(sys.modules.values()):
                    filename=getattr(module,'__file__',None)
                    if isinstance(filename,str):
                        loaded=Path(filename).resolve()
                        if loaded.is_relative_to(root) and loaded.suffix=='.py' and loaded not in bound_paths:
                            raise RuntimeError('actual imported local source escaped qualified closure: '+str(loaded))
                if machine!=closure['machine_id']:
                    raise RuntimeError('actual machine differs from qualified original source closure')
                result['source_closure']={'profile':'xar.education-service-source-pins/v2',
                    'path':str(closure_path),'bytes':len(closure_bytes),'sha256':hashlib.sha256(closure_bytes).hexdigest(),
                    'reference_count':len(source_rows),'external_reference_count':len(extra_rows),
                    'verified_before_import':True,'verified_after_producer':True,'actual_loaded_modules_bound':True}
                raw=(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>98304:
                    raise RuntimeError('aggregate diagnostic fixture exceeds explicit 98304-byte budget; actual='+str(len(raw)))
                with output.open('xb') as target:
                    target.write(raw)
                print(json.dumps({'path':str(output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                    'case_count':len(vectors),'actual_plan_consumers':3,'submit_prewrite_boundaries':2,
                    'original_consumer_drift_rejections':9,'machine_id':machine}))
                """;
        Process child = new ProcessBuilder(Path.of(arguments[1]).toRealPath().toString(), "-B", "-X", "utf8", "-c", script,
                Path.of(arguments[0]).toRealPath().toString(), Path.of(arguments[2]).toString(),
                Path.of(arguments[3]).toRealPath().toString(), arguments[4])
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly);
            child.destroyForcibly().waitFor();
            throw new IllegalStateException("actual diagnostic/consumer capture timed out");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("actual diagnostic/consumer capture failed: " + child.exitValue()); }
        ReferenceSourceClosureCapture.verify(Path.of(arguments[0]).toRealPath(), Path.of(arguments[3]).toRealPath(), arguments[4]);
    }
}
