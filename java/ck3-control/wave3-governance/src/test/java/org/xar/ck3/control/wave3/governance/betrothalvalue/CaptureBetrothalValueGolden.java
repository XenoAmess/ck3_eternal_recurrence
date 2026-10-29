package org.xar.ck3.control.wave3.governance.betrothalvalue;

import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

/** Explicit unchanged-producer oracle capture; never part of default JUnit execution. */
public final class CaptureBetrothalValueGolden {
    private CaptureBetrothalValueGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository python new-output exact-input-bindings required"); }
        String program = """
import copy, datetime, hashlib, json, os, pathlib, subprocess, sys, unittest
root=pathlib.Path(sys.argv[1]); output=pathlib.Path(sys.argv[2]); bindings_path=pathlib.Path(sys.argv[3])
if output.exists(): raise RuntimeError('capture output already exists')
sys.dont_write_bytecode=True
sys.path.insert(0,str(root/'ck3_autonomous_player/src')); sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
bindings=json.loads(bindings_path.read_text(encoding='utf-8'))
def check_inputs():
    for row in bindings['input_refs']:
        data=pathlib.Path(row['path']).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']: raise RuntimeError('actual retained native input drift: '+row['path'])
check_inputs()
machine_id=subprocess.run([sys.executable,'-X','utf8',str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True,encoding='utf-8',timeout=30).stdout.strip()
import test_current_first_heir_betrothal_formal_consumer as formal
import test_nonwar_private_python_12002 as nonwar
from xar_autoplayer.current_first_heir_betrothal_formal_consumer import evaluate_current_betrothal_fulfillment
from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import _current_pair_actionability, _COST_FIELDS
from xar_autoplayer.bridge.nonwar_private_build import private_native_provenance
from xar_autoplayer.bridge.version_identity import NATIVE_BUILD_IDENTITIES
paths=[root/'ck3_autonomous_player/src/xar_autoplayer/current_first_heir_betrothal_formal_consumer.py',root/'ck3_autonomous_player/src/xar_autoplayer/bridge/current_first_heir_relationship_private_transport.py',root/'ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py',root/'ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py',root/'ck3_autonomous_player/src/xar_autoplayer/current_betrothal_fulfillment_proposal.py',root/'ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py',root/'ck3_autonomous_player/tests/unit/test_current_first_heir_betrothal_formal_consumer.py',root/'ck3_autonomous_player/tests/unit/test_nonwar_private_python_12002.py',root/'tools/ck3_live_run_id.py']
def source_refs(): return [{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
refs=source_refs()
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(formal),unittest.defaultTestLoader.loadTestsFromModule(nonwar)])
result=unittest.TextTestRunner(verbosity=1).run(suite)
if result.testsRun!=14 or not result.wasSuccessful() or result.skipped: raise RuntimeError('actual original 14 producer/consumer tests failed or skipped')
base={'schema':'xar.ck3.betrothal-value-request.v1','snapshot':formal.scene(),'relationship':formal.relation()}
expected_base=evaluate_current_betrothal_fulfillment(copy.deepcopy(base['relationship']),copy.deepcopy(base['snapshot']))
def put(path,value): return {'path':path,'value':value}
def remove(path): return {'path':path,'remove':True}
def apply(base,patches):
    value=copy.deepcopy(base)
    for patch in patches:
        parent=value
        for key in patch['path'][:-1]: parent=parent[key]
        key=patch['path'][-1]
        if patch.get('remove',False): del parent[key]
        else: parent[key]=copy.deepcopy(patch['value'])
    return value
def diff(a,b,path=None):
    path=[] if path is None else path
    if type(a) is not type(b): return [put(path,b)]
    if isinstance(a,dict):
        patches=[remove(path+[key]) for key in sorted(a.keys()-b.keys())]
        for key in sorted(b): patches += [put(path+[key],b[key])] if key not in a else diff(a[key],b[key],path+[key])
        return patches
    if isinstance(a,list) and len(a)==len(b):
        patches=[]
        for i,(left,right) in enumerate(zip(a,b)): patches+=diff(left,right,path+[i])
        return patches
    return [] if a==b else [put(path,b)]
cases=[]
def case(name,patches):
    req=apply(base,patches); row={'name':name,'patches':patches}
    try:
        expected=evaluate_current_betrothal_fulfillment(copy.deepcopy(req['relationship']),copy.deepcopy(req['snapshot']))
        row['expected_patches']=diff(expected_base,expected)
        row['expected_provenance']=private_native_provenance(req['snapshot'])
    except Exception as error:
        row['expected_error']=True; row['original_error_type']=type(error).__name__
    cases.append(row)
R=['relationship']; A=R+['betrothal_actionability']; S=['snapshot']
case('legacy-selected-exact-existing-pair',[])
case('pair-unavailable',[put(R+['status'],'unavailable')])
case('bilateral-unverified',[put(R+['bilateral_verified'],False)])
case('no-heir',[put(R+['heir_character_id'],None),put(A,None)])
case('no-partner',[put(R+['betrothed_character_id'],None),put(A,None)])
case('already-married',[put(R+['spouse_character_ids'],[38718])])
case('spouses-unknown',[remove(R+['spouse_character_ids'])])
case('spouses-explicit-null',[put(R+['spouse_character_ids'],None)])
case('primary-spouse-present',[put(R+['primary_spouse_character_id'],38718)])
case('value-absent',[remove(A)])
case('value-explicit-null',[put(A,None)])
case('actual-heir-not-adult',[put(A+['heir_adult_measure_raw'],18),put(A+['heir_is_adult'],False),put(A+['ready_to_marry_betrothed'],False)])
case('native-final-cannot-send',[put(A+['complete_can_send'],False)])
case('zero-acceptance',[put(A+['recipient_ai_accept_raw'],0)])
case('recipient-answer-yes',[put(A+['recipient_answer_status_raw'],1)])
case('recipient-answer-no',[put(A+['recipient_answer_status_raw'],2)])
case('still-betrothal',[put(A+['predicted_outcome_if_accepted'],'betrothal')])
for field in _COST_FIELDS: case('nonzero-'+field,[put(A+['generic_costs',field],1)])
case('int64-acceptance-min',[put(A+['recipient_ai_accept_raw'],-2**63)])
case('int64-acceptance-max',[put(A+['recipient_ai_accept_raw'],2**63-1)])
case('adult-width-boundaries',[put(A+['heir_adult_measure_raw'],-2**15),put(A+['heir_adult_threshold_raw'],-2**31),put(A+['partner_adult_measure_raw'],2**15-1),put(A+['partner_adult_threshold_raw'],2**31-1),put(A+['partner_is_adult'],False),put(A+['ready_to_marry_betrothed'],False)])
preview={'status':'available','reason':'','subject_character_id':38822,'candidate_character_id':38718,'requested_matrilineal_option':False,'selected_matrilineal_option':False,'effective_matrilineal_if_accepted':False,'complete_can_send':True,'native_selected_parent_character_id':38822,'house_id':100,'dynasty_id':200}
case('selected-false-preview',[put(A+['matrilineal_option_selected'],False),put(A+['native_child_house_preview'],preview)])
selected_preview={**preview,'selected_matrilineal_option':True,'effective_matrilineal_if_accepted':True,'native_selected_parent_character_id':38718,'house_id':300,'dynasty_id':400}
case('selected-true-preview',[put(A+['matrilineal_option_selected'],True),put(A+['effective_matrilineal_if_accepted'],True),put(A+['native_child_house_preview'],selected_preview)])
case('selected-does-not-infer-effective',[put(A+['matrilineal_option_selected'],True),put(A+['native_child_house_preview'],{**selected_preview,'effective_matrilineal_if_accepted':False})])
case('preview-house-zero-dynasty-null',[put(A+['matrilineal_option_selected'],False),put(A+['native_child_house_preview'],{**preview,'house_id':0,'dynasty_id':None})])
case('preview-unavailable-not-guessed',[put(A+['native_child_house_preview'],{'status':'unavailable','reason':'source_unavailable','subject_character_id':38822,'candidate_character_id':38718,'requested_matrilineal_option':False})])
case('preview-selected-mismatch',[put(A+['matrilineal_option_selected'],True),put(A+['native_child_house_preview'],preview)])
case('preview-other-parent',[put(A+['matrilineal_option_selected'],False),put(A+['native_child_house_preview'],{**preview,'native_selected_parent_character_id':29829})])
case('preview-wrong-subject',[put(A+['matrilineal_option_selected'],False),put(A+['native_child_house_preview'],{**preview,'subject_character_id':38823})])
case('actor-mismatch',[put(A+['actor_character_id'],29830)])
case('incomplete-available',[remove(A+['final_legality_sampled'])])
case('crossed-native-frame',[put(R+['native_revision'],8)])
case('not-paused',[put(S+['paused'],False)])
case('map-not-ready',[put(S+['map_ready'],False)])
case('played-character-dead',[put(S+['played_character','alive'],False)])
case('read-only-false',[put(R+['read_only'],False)])
case('advertised-true',[put(R+['advertised'],True)])
case('wrong-relation-schema',[put(R+['schema'],'unknown')])
for build in NATIVE_BUILD_IDENTITIES:
    case('exact-hello-'+build.game_version,[put(S+['diagnostics'],{'hello':{'expected_ck3_version':build.game_version,'expected_ck3_sha256':build.executable_sha256.lower()}}),put(R+['exact_ck3_build'],build.game_version),put(R+['exe_sha256'],build.executable_sha256.lower())])
build=NATIVE_BUILD_IDENTITIES[-1]
hello={'expected_ck3_version':build.game_version,'expected_ck3_sha256':build.executable_sha256}
bound=[put(S+['diagnostics'],{'hello':hello}),put(R+['exact_ck3_build'],build.game_version),put(R+['exe_sha256'],build.executable_sha256)]
case('hello-game-version-fallback',[put(S+['diagnostics'],{'hello':{'game_version':build.game_version,'executable_sha256':build.executable_sha256}}),*bound[1:]])
case('hello-explicit-null-no-fallback',[put(S+['diagnostics'],{'hello':{**hello,'expected_ck3_version':None,'game_version':build.game_version}}),*bound[1:]])
case('hello-mixed-exe',[put(S+['diagnostics'],{'hello':{**hello,'expected_ck3_sha256':'0'*64}}),*bound[1:]])
case('readback-mixed-exe',[*bound,put(R+['exe_sha256'],'0'*64)])
case('legacy-hello-cannot-label-12004',bound[1:])
case('opaque-descendants-retained',[put(R+['current_first_heir_descendants_v1'],{'rows':[None,[],{'opaque':'保留'}]}),put(R+['current_first_heir_descendants_summary_v1'],{'available':False})])
native_cases=[]
native=pathlib.Path(bindings['native_negative']); pair=json.loads(native.read_text(encoding='utf-8'))
def native_case(name,pair):
    actor=pair['actor_character_id']; heir=pair.get('heir_character_id'); partner=pair.get('partner_character_id')
    expected=_current_pair_actionability(copy.deepcopy(pair),actor=actor,heir=heir,partner=partner)
    native_cases.append({'name':name,'input':pair,'actor':actor,'heir':heir,'partner':partner,'expected':expected})
native_case('actual-12002-negative-producer',pair)
for path in bindings['lineage_inputs']:
    wire=pathlib.Path(path); native_case('retained-native-'+wire.stem,json.loads(wire.read_text(encoding='utf-8'))['result']['betrothal_actionability'])
check_inputs()
if source_refs()!=refs: raise RuntimeError('original production or consumer source drift during capture')
golden={'schema':'xar.ck3.betrothal-value-python-golden.v1','machine_id':machine_id,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_refs':refs,'input_refs':bindings['input_refs'],'input_machine_qualification':'retained portable native fixture inputs; historical producer machine unknown; not current live facts','original_tests_run':result.testsRun,'original_failures':len(result.failures),'original_errors':len(result.errors),'original_skipped':len(result.skipped),'base_request':base,'base_expected':expected_base,'cases':cases,'native_action_cases':native_cases}
raw=(json.dumps(golden,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
if len(raw)>65536: raise RuntimeError('actual value golden exceeds 64 KiB finite budget')
output.parent.mkdir(parents=True,exist_ok=True)
with output.open('xb') as stream: stream.write(raw)
print(json.dumps({'output_path':str(output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cases':len(cases),'native_cases':len(native_cases),'original_tests':result.testsRun}))
""";
        ProcessBuilder builder = new ProcessBuilder(args[1], "-X", "utf8", "-c", program, args[0], args[2], args[3]).directory(Path.of(args[0]).toFile()).inheritIO();
        String temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().toString();
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("TEMP", temporary);
        builder.environment().put("TMP", temporary); builder.environment().put("XAR_TEST_TEMP_ROOT", temporary);
        Process process = builder.start();
        if (!process.waitFor(Duration.ofSeconds(100).toMillis(), TimeUnit.MILLISECONDS)) { process.destroyForcibly(); throw new IllegalStateException("original value capture timeout"); }
        if (process.exitValue() != 0) { throw new IllegalStateException("original value capture failed: " + process.exitValue()); }
    }
}
