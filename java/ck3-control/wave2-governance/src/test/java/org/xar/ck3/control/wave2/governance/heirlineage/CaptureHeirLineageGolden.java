package org.xar.ck3.control.wave2.governance.heirlineage;

import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit scheduled oracle capture. Default tests only read the committed result. */
public final class CaptureHeirLineageGolden {
    private CaptureHeirLineageGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) {
            throw new IllegalArgumentException("repository, Python executable, new output path required");
        }
        String script = """
                import sys,json,hashlib,datetime,subprocess
                from copy import deepcopy
                from pathlib import Path
                root=Path(sys.argv[1]).resolve()
                sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.first_heir_native_lineage_policy import choose_native_lineage_opportunity
                machine=subprocess.run([sys.executable,'-B',str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
                def base():
                    rows=[]
                    choices=[]
                    previews=[]
                    for candidate in (50331651,50331652,50331653):
                        floor={'ready':True,'passes':candidate!=50331651}
                        age={'ready':candidate==50331653,'passes':True if candidate==50331653 else None}
                        rows.append({'candidate_character_id':candidate,'heir_character_id':50331650,
                            'matrilineal_option_selected':False,'effective_matrilineal_if_accepted':False,
                            'played_dynasty_id':200,'candidate_native_fertility_floor_comparison_v1':floor,
                            'candidate_native_scorer_age_branch_v1':age})
                        choices.append({'candidate_character_id':candidate,'recipient_ai_accept_raw':100000000-candidate,
                            'unpriced':['future_child_identity_and_dynasty']})
                        previews.append({'queried_native_revision':7,'frame':{'date_raw':53220000},
                            'native_child_house_preview':{'status':'available','reason':'','subject_character_id':50331650,
                            'candidate_character_id':candidate,'requested_matrilineal_option':False,
                            'selected_matrilineal_option':False,'effective_matrilineal_if_accepted':False,
                            'complete_can_send':True,'native_selected_parent_character_id':50331650,
                            'house_id':100,'dynasty_id':200}})
                    return {'snapshot':{'revision':9,'native_revision':7,'date_raw':53220000,
                        'episode_run_id':'offline-lineage-fixture','played_character':{'character_id':50331649}},
                        'legality':{'observed_first_heir_character_id':50331650},
                        'projection':{'rows':rows},'choices':choices,'previews':previews}
                scenes=[]
                scenes.append(('observed-pass-first-no-extra-query',base()))
                fallback=base()
                fallback['previews'][2]['native_child_house_preview']['complete_can_send']=False
                fallback['previews'][1]['native_child_house_preview']['dynasty_id']=201
                scenes.append(('failed-send-and-other-dynasty-continue-to-floor-fail-fallback',fallback))
                unavailable=base()
                for observation in unavailable['previews']:
                    preview=observation['native_child_house_preview']
                    for key in ('selected_matrilineal_option','effective_matrilineal_if_accepted','complete_can_send','native_selected_parent_character_id','house_id','dynasty_id'):
                        preview.pop(key)
                    preview.update(status='unavailable',reason='native_observation_unavailable')
                scenes.append(('all-unavailable-preserves-original-reasons',unavailable))
                allfail=base()
                for row in allfail['projection']['rows']:
                    row['candidate_native_fertility_floor_comparison_v1']={'ready':True,'passes':False}
                scenes.append(('all-fail-stable-does-not-remove-opportunities',allfail))
                nullable=base()
                nullable['projection']['rows'][2]['played_dynasty_id']=None
                nullable['previews'][2]['native_child_house_preview']['dynasty_id']=None
                scenes.append(('observed-null-dynasty-comparison-keeps-old-semantics',nullable))
                empty=base()
                empty['choices']=[]
                empty['projection']['rows']=[]
                empty['previews']=[]
                scenes.append(('empty-does-not-read-native-preview',empty))
                stale=base()
                stale['previews'][2]['queried_native_revision']=8
                scenes.append(('changed-native-revision-rejects',stale))
                changed=base()
                changed['previews'][2]['native_child_house_preview']['selected_matrilineal_option']=True
                scenes.append(('changed-selected-option-rejects',changed))
                class Driver:
                    def __init__(self,request):
                        self.request=request
                        self.queries=[]
                    def query_family_obligations_private_v1(self,**query):
                        self.queries.append(deepcopy(query))
                        candidate=query['candidate_character_id']
                        return deepcopy(next(value for value in self.request['previews'] if value['native_child_house_preview']['candidate_character_id']==candidate))
                vectors=[]
                for name,request in scenes:
                    original=deepcopy(request)
                    driver=Driver(request)
                    try:
                        choice,observations=choose_native_lineage_opportunity(driver,
                            snapshot=request['snapshot'],legality=request['legality'],
                            projection=request['projection'],choices=request['choices'])
                        expected={'choice':choice,'observations':observations}
                        vector={'name':name,'input':original,'expected':expected,'expected_queries':driver.queries}
                    except ValueError as error:
                        vector={'name':name,'input':original,'expected_error':str(error),'expected_queries':driver.queries}
                    if request!=original:
                        raise RuntimeError('old producer mutated input')
                    vectors.append(vector)
                sources=[]
                for relative in ('ck3_autonomous_player/src/xar_autoplayer/first_heir_native_lineage_policy.py',
                                 'ck3_autonomous_player/src/xar_autoplayer/first_heir_native_reproductive_preference.py'):
                    source=root/relative
                    sources.append({'path':relative,'bytes':source.stat().st_size,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
                result={'schema':'xar.ck3.heir-lineage.actual-producer-golden.v1','machine_id':machine,
                    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_kind':'actual-unchanged-producer-with-offline-preview-fixtures',
                    'game_or_rpc':False,'native_source_qualification':False,'sources':sources,'cases':vectors}
                raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\\n').encode('utf-8')
                if len(raw)>65536:
                    raise RuntimeError('bounded golden exceeds 65536 bytes')
                output=Path(sys.argv[2])
                with output.open('xb') as target:
                    target.write(raw)
                print(json.dumps({'path':str(output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'case_count':len(vectors),'machine_id':machine}))
                """;
        Process child = new ProcessBuilder(Path.of(arguments[1]).toRealPath().toString(), "-B", "-X", "utf8",
                "-c", script, Path.of(arguments[0]).toRealPath().toString(), Path.of(arguments[2]).toString())
                .directory(Path.of(arguments[0]).toFile()).inheritIO().start();
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly);
            child.destroyForcibly().waitFor();
            throw new IllegalStateException("bounded old producer capture timed out");
        }
        if (child.exitValue() != 0) {
            throw new IllegalStateException("old producer capture failed: " + child.exitValue());
        }
    }
}
