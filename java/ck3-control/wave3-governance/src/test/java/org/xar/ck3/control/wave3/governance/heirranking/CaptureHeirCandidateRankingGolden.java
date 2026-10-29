package org.xar.ck3.control.wave3.governance.heirranking;

import java.nio.file.Path;
import org.xar.ck3.control.wave3.governance.capture.ReferenceSourceClosureCapture;
import java.util.concurrent.TimeUnit;

/** Scheduled actual Python oracle capture; never part of default JUnit execution. */
public final class CaptureHeirCandidateRankingGolden {
    private CaptureHeirCandidateRankingGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 5) { throw new IllegalArgumentException("repository, Python executable, new output, exact closure gzip and SHA required"); }
        ReferenceSourceClosureCapture.verify(Path.of(arguments[0]).toRealPath(), Path.of(arguments[3]).toRealPath(), arguments[4]);
        String script = """
                import sys,json,hashlib,datetime,subprocess
                from pathlib import Path
                from copy import deepcopy
                root=Path(sys.argv[1]).resolve()
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
                from test_family_marriage_formal_consumer import family_reads
                from xar_autoplayer.family_marriage_formal_consumer import rank_first_heir_marriage_candidates,_candidate_rejection_reasons
                machine=subprocess.run([sys.executable,'-B',str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
                def base():
                    legality,projection=family_reads()
                    return {'legality':legality,'projection':projection,'rejected_candidate_ids':[]}
                scenes=[('adult-marriage-original-value-costs-and-stable-order',base())]
                ages=base()
                for index,(source,row) in enumerate(zip(ages['legality']['native_legal_candidates'],ages['projection']['rows'])):
                    age=(18,16,17,18,16)[index]
                    source['candidate_adult_measure_raw']=age
                    source['recipient_ai_accept_raw']=(500,100,1000,500,100)[index]
                    row['candidate_adult_measure_raw']=age
                scenes.append(('adult-gap-before-acceptance-and-id-ties',ages))
                minor=base()
                for index,(source,row) in enumerate(zip(minor['legality']['native_legal_candidates'],minor['projection']['rows'])):
                    age=(14,16,13,15,17)[index]
                    source.update(heir_adult_measure_raw=13,candidate_adult_measure_raw=age)
                    row.update(heir_adult_measure_raw=13,candidate_adult_measure_raw=age,
                        heir_is_adult=False,candidate_is_adult=age>=16,predicted_outcome_if_accepted='betrothal')
                minor['projection']['rows'][0]['possible_alliance_pairs']=[{'first_character_id':101,'second_character_id':400,
                    'already_allied':False,'both_have_realm_data':True,'would_attempt_if_accepted':True}]
                minor['legality']['native_legal_candidates'][3]['heir_dynasty_id']=None
                minor['projection']['rows'][4]['played_dynasty_id']=None
                scenes.append(('minor-betrothal-bounds-alliance-and-unknown-ranking',minor))
                rejected=base()
                legal=rejected['legality']['native_legal_candidates']
                rows=rejected['projection']['rows']
                legal[0].update(complete_can_send=False,recipient_answer_allows_send=False,recipient_answer_status_raw=2,recipient_ai_accept_raw=0)
                rows[1].update(actor_character_id=999,heir_character_id=998,recipient_character_id=997)
                rows[2].update(heir_betrothed_character_id=888,heir_primary_spouse_character_id=889,heir_spouse_character_ids=[889])
                rows[3].update(candidate_sex_selector_raw=0,effective_matrilineal_if_accepted=True)
                rows[4].update(predicted_outcome_if_accepted='betrothal',grand_wedding_option_selected=True,
                    candidate_dynasty_id=20,possible_alliance_pairs=None,candidate_adult_measure_raw=19)
                legal[4].update(realm_backed_actor_recipient=False)
                scenes.append(('ordered-rejection-reasons-shared-with-diagnostics',rejected))
                identities=base()
                identities['legality']['native_legal_candidates'][0]['candidate_dynasty_id']=-1
                identities['projection']['rows'][0]['candidate_dynasty_id']=None
                identities['rejected_candidate_ids']=[301]
                for collection in (identities['legality']['native_legal_candidates'],identities['projection']['rows']):
                    collection[2]['candidate_character_id']=9007199254740993
                scenes.append(('compact-absent-dynasty-refusal-and-exact-large-id',identities))
                mismatch=base()
                mismatch['projection']['native_revision']=8
                scenes.append(('different-native-frame-does-not-rank',mismatch))
                short=base()
                short['projection']['rows'].pop()
                scenes.append(('non-five-projection-does-not-rank',short))
                vectors=[]
                for name,request in scenes:
                    original=deepcopy(request)
                    legality=request['legality']
                    projection=request['projection']
                    refused=frozenset(request['rejected_candidate_ids'])
                    choices=rank_first_heir_marriage_candidates(legality,projection,rejected_candidate_ids=refused)
                    reasons=[]
                    if (legality['status']=='available' and projection['status']=='available'
                        and legality['native_revision']==projection['native_revision']
                        and legality['query_sequence']==projection['legality_query_sequence']
                        and len(projection['rows'])==5):
                        by_id={row.get('candidate_character_id'):row for row in legality['native_legal_candidates']}
                        for row in projection['rows']:
                            candidate=row.get('candidate_character_id')
                            reasons.append({'candidate_character_id':candidate,
                                'rejection_reasons':_candidate_rejection_reasons(by_id.get(candidate),row,rejected_candidate_ids=refused)})
                    if request!=original:
                        raise RuntimeError('actual old producer mutated original fixture')
                    vectors.append({'name':name,'input':original,'expected_choices':choices,'expected_rejections':reasons})
                sources=[]
                for relative in ('ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py',
                                 'ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py'):
                    source=root/relative
                    sources.append({'path':relative,'bytes':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
                result={'schema':'xar.ck3.heir-candidate-ranking.actual-producer-golden.v1','machine_id':machine,
                    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_kind':'unchanged-real-ranking-and-rejection-producers-with-source-test-fixtures',
                    'game_or_rpc':False,'native_source_qualification':False,'sources':sources,'cases':vectors}
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
                    raise RuntimeError('aggregate ranking fixture exceeds explicit 98304-byte budget; actual='+str(len(raw)))
                output=Path(sys.argv[2])
                with output.open('xb') as target:
                    target.write(raw)
                print(json.dumps({'path':str(output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'case_count':len(vectors),'machine_id':machine}))
                """;
        Process child = new ProcessBuilder(Path.of(arguments[1]).toRealPath().toString(), "-B", "-X", "utf8", "-c", script,
                Path.of(arguments[0]).toRealPath().toString(), Path.of(arguments[2]).toString(),
                Path.of(arguments[3]).toRealPath().toString(), arguments[4])
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly);
            child.destroyForcibly().waitFor();
            throw new IllegalStateException("actual ranking producer capture timed out");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("actual ranking producer capture failed: " + child.exitValue()); }
        ReferenceSourceClosureCapture.verify(Path.of(arguments[0]).toRealPath(), Path.of(arguments[3]).toRealPath(), arguments[4]);
    }
}
