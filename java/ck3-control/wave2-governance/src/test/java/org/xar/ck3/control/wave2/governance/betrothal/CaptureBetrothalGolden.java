package org.xar.ck3.control.wave2.governance.betrothal;

import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

/** Explicit legacy producer data capture; never part of default JUnit or production. */
public final class CaptureBetrothalGolden {
    private CaptureBetrothalGolden() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-executable new-output fixture-bindings required"); }
        String program = """
import copy, datetime, hashlib, json, os, pathlib, runpy, subprocess, sys, unittest
root=pathlib.Path(sys.argv[1]); output=pathlib.Path(sys.argv[2])
if output.exists(): raise RuntimeError('capture output already exists')
sys.dont_write_bytecode=True
machine_id=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True,timeout=30).stdout.strip()
binding_path=pathlib.Path(sys.argv[3]); bindings=json.loads(binding_path.read_text(encoding='utf-8'))
if bindings.get('schema')!='xar.ck3.betrothal-native-fixture-bindings/v1' or bindings.get('machine_id')!=machine_id: raise RuntimeError('fixture binding identity invalid')
for ref in bindings['input_refs']:
    raw=pathlib.Path(ref['path']).read_bytes()
    if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']: raise RuntimeError('retained native fixture changed')
for key,value in bindings['environment'].items():
    if not key.startswith('XAR_') or not key.endswith('_WIRE_DIR'): raise RuntimeError('unexpected fixture environment key')
    os.environ[key]=value
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
from xar_autoplayer.current_betrothal_fulfillment_proposal import build_current_betrothal_fulfillment_proposal, current_betrothal_fulfillment_m5_proposal, SUBMIT_STEP
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
unit=root/'ck3_autonomous_player/tests/unit'
helpers=runpy.run_path(str(unit/'test_current_betrothal_fulfillment_proposal.py'))
modules=[helpers,runpy.run_path(str(unit/'test_current_betrothal_prospective_lineage_service.py')),runpy.run_path(str(unit/'test_current_first_heir_descendants_registered_service.py'))]
suite=unittest.TestSuite()
for module in modules:
    for item in module.values():
        if isinstance(item,type) and issubclass(item,unittest.TestCase) and item.__module__=='<run_path>': suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(item))
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful() or result.skipped or result.testsRun < 3: raise RuntimeError('actual original producer/consumer tests failed or skipped')
snapshot=helpers['_snapshot'](); relation=helpers['_relation']()
base={'schema':'xar.ck3.betrothal-build-request.v1','snapshot':snapshot,'relation':relation,'selected':True,'reasons':[]}
def patch_copy(base,patches):
    value=copy.deepcopy(base)
    for patch in patches:
        parent=value
        for key in patch['path'][:-1]: parent=parent[key]
        key=patch['path'][-1]
        if patch.get('remove',False):
            if isinstance(parent,list): parent.pop(key)
            else: del parent[key]
        else: parent[key]=copy.deepcopy(patch['value'])
    return value
def put(path,value): return {'path':path,'value':value}
def remove(path): return {'path':path,'remove':True}
builds=[]
def build_case(name,patches):
    req=patch_copy(base,patches)
    resource=build_current_betrothal_fulfillment_proposal(req['relation'],req['snapshot'],selected=req['selected'],reasons=req['reasons'])
    builds.append({'name':name,'patches':patches,'expected_resource':resource})
build_case('selected-fixed-pair',[])
build_case('hold-unknown-costs',[put(['selected'],False),put(['reasons'],['policy_hold']),put(['relation','betrothal_actionability','generic_costs'],None)])
build_case('hold-signed-costs',[put(['selected'],False),put(['reasons'],['policy_hold']),put(['relation','betrothal_actionability','generic_costs','gold_raw'],3000000),put(['relation','betrothal_actionability','generic_costs','prestige_raw'],-100000)])
build_case('signed-int64-cost-extremes',[put(['selected'],False),put(['relation','betrothal_actionability','generic_costs','gold_raw'],-9223372036854775808),put(['relation','betrothal_actionability','generic_costs','prestige_raw'],9223372036854775807)])
build_case('missing-actionability-held',[put(['selected'],False),remove(['relation','betrothal_actionability'])])
build_case('null-native-revision-held',[put(['selected'],False),put(['relation','native_revision'],None)])
build_case('actor-and-child-overridden-from-observed-relation',[put(['relation','betrothal_actionability','actor_character_id'],123),put(['relation','betrothal_actionability','heir_character_id'],124),put(['relation','betrothal_actionability','partner_character_id'],125)])
build_case('duplicate-role-claims-deduplicated',[put(['relation','betrothal_actionability','intermediary_character_id'],38822)])
build_case('unpriced-preview-and-descendants-preserved',[put(['relation','betrothal_actionability','native_child_house_preview'],{'status':'unavailable','house_id':None,'reason':'unknown'}),put(['relation','current_first_heir_descendants_v1'],{'status':'available','children':[],'complete':False}),put(['relation','current_first_heir_descendants_summary_v1'],{'unknown':[None,[],{'x':'尚未证明'}]})])
build_case('source-cost-extension-preserved',[put(['relation','betrothal_actionability','generic_costs','source_extension'],{'native_quote':None,'proven':False})])
build_case('unknown-ready-has-no-benefit',[put(['selected'],False),put(['relation','betrothal_actionability','ready_to_marry_betrothed'],None)])
build_case('missing-cost-term-is-not-zero',[put(['selected'],False),remove(['relation','betrothal_actionability','generic_costs','merit_raw'])])
frame=observed_frame(snapshot)
resource=builds[0]['expected_resource']
adapt_base={'schema':'xar.ck3.betrothal-adapt-request.v1','frame':frame,'plan':{'selected_step':SUBMIT_STEP,'current_betrothal_choice':{'resource_proposal':resource}}}
adapts=[]
def adapt_case(name,patches):
    req=patch_copy(adapt_base,patches)
    try: outcome={'accepted':True,'proposal':current_betrothal_fulfillment_m5_proposal(frame=req['frame'],plan=req['plan'])}
    except ValueError as error: outcome={'accepted':False,'error_message':str(error)}
    adapts.append({'name':name,'patches':patches,'expected':outcome})
R=['plan','current_betrothal_choice','resource_proposal']
adapt_case('same-frame-zero-cost-existing-commitment',[])
adapt_case('episode-changed',[put(['frame','episode_run_id'],'other-episode')])
adapt_case('source-native-revision-changed',[put(R+['source_native_revision'],10)])
adapt_case('selected-false',[put(R+['selected'],False)])
adapt_case('formal-ready-false',[put(R+['formal_action_ready'],False)])
adapt_case('typed-step-changed',[put(R+['typed_step'],'other-step')])
adapt_case('plan-step-changed',[put(['plan','selected_step'],'life-advance')])
adapt_case('nonzero-cost',[put(R+['immediate_generic_costs','gold_raw'],1)])
adapt_case('missing-cost',[remove(R+['immediate_generic_costs','merit_raw'])])
adapt_case('null-costs',[put(R+['immediate_generic_costs'],None)])
adapt_case('raw-scale-changed',[put(R+['immediate_generic_costs','raw_scale'],1000)])
adapt_case('payer-changed',[put(R+['immediate_generic_costs','payer_role'],'recipient')])
adapt_case('commitment-not-bilateral',[put(R+['existing_commitment','bilateral_verified'],False)])
adapt_case('new-commitment-forbidden',[put(R+['existing_commitment','new_betrothal_commitment'],True)])
adapt_case('commitment-key-changed',[put(R+['existing_commitment','commitment_key'],'first-heir-marriage:1')])
adapt_case('claims-unsorted',[put(R+['character_claims'],[38822,38718,32897,29829])])
adapt_case('claims-duplicate',[put(R+['character_claims'],[29829,32897,38718,38822,38822])])
adapt_case('claims-negative',[put(R+['character_claims'],[-1,29829,32897,38718,38822])])
adapt_case('claims-incomplete',[put(R+['character_claims'],[29829,32897,38822])])
adapt_case('actor-changed',[put(R+['actor_character_id'],123)])
adapt_case('recipient-missing',[remove(R+['recipient_character_id'])])
adapt_case('uninterpreted-resource-extension-preserved',[put(R+['native_extension'],{'unpriced':True,'data':[]})])
paths=[root/'ck3_autonomous_player/src/xar_autoplayer/current_betrothal_fulfillment_proposal.py',root/'ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py',root/'ck3_autonomous_player/src/xar_autoplayer/current_first_heir_betrothal_formal_consumer.py',unit/'test_current_betrothal_fulfillment_proposal.py',unit/'test_current_betrothal_prospective_lineage_service.py',unit/'test_current_first_heir_descendants_registered_service.py']
refs=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
for ref in bindings['input_refs']:
    raw=pathlib.Path(ref['path']).read_bytes()
    if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']: raise RuntimeError('retained native fixture changed during tests')
golden={'schema':'xar.ck3.betrothal-python-golden.v1','machine_id':machine_id,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_refs':refs,'native_fixture_refs':bindings['input_refs'],'original_tests_run':result.testsRun,'original_failures':len(result.failures),'original_errors':len(result.errors),'original_skipped':len(result.skipped),'base_build_request':base,'build_cases':builds,'base_adapt_request':adapt_base,'adapt_cases':adapts}
raw=(json.dumps(golden,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
if len(raw)>98304: raise RuntimeError('golden exceeds finite 96 KiB estimate')
output.parent.mkdir(parents=True,exist_ok=True)
with output.open('xb') as stream: stream.write(raw)
print(json.dumps({'output_path':str(output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'build_cases':len(builds),'adapt_cases':len(adapts),'original_tests':result.testsRun}))
""";
        Process process = new ProcessBuilder(args[1], "-c", program, args[0], args[2], args[3])
                .directory(Path.of(args[0]).toFile()).inheritIO().start();
        if (!process.waitFor(Duration.ofSeconds(100).toMillis(), TimeUnit.MILLISECONDS)) {
            process.destroyForcibly(); throw new IllegalStateException("legacy golden capture timed out");
        }
        if (process.exitValue() != 0) { throw new IllegalStateException("legacy golden capture failed: " + process.exitValue()); }
    }
}
