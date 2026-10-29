package org.xar.ck3.control.wave3.governance.marriagenotice;

import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

/** Explicit capture of the unchanged legacy source and all its existing pytest consumers. */
public final class CaptureMarriageNoticeGolden {
    private CaptureMarriageNoticeGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository python-executable new-output required"); }
        String program = """
import copy, datetime, hashlib, json, os, pathlib, runpy, subprocess, sys, tempfile
root=pathlib.Path(sys.argv[1]); output=pathlib.Path(sys.argv[2])
if output.exists(): raise RuntimeError('capture output already exists')
sys.dont_write_bytecode=True
sys.path.insert(0,str(root/'ck3_autonomous_player/src')); sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
import pytest
machine_id=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True,timeout=30).stdout.strip()
class Reports:
    def __init__(self): self.reports=[]
    def pytest_runtest_logreport(self,report):
        if report.when=='call': self.reports.append(report.outcome)
reports=Reports()
unit=root/'ck3_autonomous_player/tests/unit'; test=unit/'test_pending_arrange_marriage_source_v1.py'
result=pytest.main([str(test),'-q','-p','no:cacheprovider','-o','addopts=','--basetemp',tempfile.mkdtemp(prefix='marriagenotice-pytest-')],plugins=[reports])
if result != 0 or len(reports.reports)!=13 or any(item!='passed' for item in reports.reports): raise RuntimeError('actual original 13 producer/consumer tests failed or skipped')
helper=runpy.run_path(str(test))
from xar_autoplayer.pending_arrange_marriage_source_v1 import source_reviewed_arrange_marriage_evidence_v1, is_blocked_arrange_marriage_reply_v1, continue_without_blocked_marriage_reply_v1, KEY
context,historical=helper['case']()
review_base={'schema':'xar.ck3.marriage-notice-review-request.v1','context':context,'historical_evidence':historical}
def put(path,value): return {'path':path,'value':value}
def remove(path): return {'path':path,'remove':True}
def apply(base,patches):
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
reviews=[]
def review(name,patches):
    req=apply(review_base,patches)
    expected=source_reviewed_arrange_marriage_evidence_v1(req['context'],req['historical_evidence'])
    reviews.append({'name':name,'patches':patches,'expected':expected,'applied':expected is not req['historical_evidence']})
review('exact-build-offline-review-only',[])
review('other-version',[put(['context','build','version'],'1.19.0.6')])
review('other-exe',[put(['context','build','exe_sha256'],'0'*64)])
review('lowercase-exe-remains-unmatched',[put(['context','build','exe_sha256'],context['build']['exe_sha256'].lower())])
review('other-definition',[put(['context','definition','canonical_key'],'unknown_interaction')])
review('other-key-hash',[put(['context','definition','deterministic_key_hash'],1298930138)])
review('other-backend',[put(['context','provenance','backend_id'],'unknown')])
review('historical-null',[put(['historical_evidence'],None)])
review('historical-array',[put(['historical_evidence'],[])])
review('context-null',[put(['context'],None)])
review('context-array',[put(['context'],[])])
review('null-build-container',[put(['context','build'],None)])
review('missing-definition',[remove(['context','definition'])])
review('historical-source-missing',[remove(['historical_evidence','source_sha256'])])
review('history-opaque-extension',[put(['historical_evidence','retained_extension'],{'rows':[None,[],{'x':'保留'}]})])
blocked={'phase':'pending_character_interaction_degraded_blocked','selected_step':None,'decision':{'classification':'known_marriage_special','pending_interaction_id':-123,'definition_classification':{'definition_key':KEY}}}
snapshot={'pending_character_interaction':{'instance_id':-123,'auto_accept_notification':False},'date_raw':53279400,'episode_run_id':'fixture-episode','retained':{'paused':True}}
steps=['life-advance','accept-pending-character-interaction','reject-pending-character-interaction','block-pending-character-interaction','acknowledge-pending-character-interaction','query-pending-character-interaction-context-v1']
continue_base={'schema':'xar.ck3.marriage-notice-continue-request.v1','plan':blocked,'snapshot':snapshot,'action_steps':steps}
ordinary={'phase':'ordinary','selected_step':'life-advance','retained_ordinary_payload':{'cash':1}}
continuations=[]
def continuation(name,patches,ordinary_plan=None):
    req=apply(continue_base,patches); callback=copy.deepcopy(ordinary if ordinary_plan is None else ordinary_plan); calls=[]
    def choose(projection,steps):
        calls.append({'snapshot':copy.deepcopy(projection),'action_steps':list(steps),'scope':'planning_only'})
        return copy.deepcopy(callback)
    expected=continue_without_blocked_marriage_reply_v1(req['plan'],snapshot=req['snapshot'],action_steps=tuple(req['action_steps']),choose_ordinary=choose)
    continuations.append({'name':name,'patches':patches,'ordinary_plan':callback,'expected':expected,'expected_blocked':is_blocked_arrange_marriage_reply_v1(req['plan']),'callback_calls':calls})
continuation('ordinary-plan-keeps-notification-diagnosis',[])
continuation('active-event-never-hidden',[put(['snapshot','active_event'],{'instance_id':7})])
continuation('current-event-never-hidden',[put(['snapshot','current_event'],{'instance_id':7})])
continuation('exclusive-modal-never-hidden',[put(['snapshot','top_exclusive_modal_choice_hint'],{'status':'present'})])
continuation('empty-active-event-still-present',[put(['snapshot','active_event'],[])])
continuation('notification-instance-mismatch',[put(['snapshot','pending_character_interaction','instance_id'],-124)])
continuation('auto-accept-is-not-this-path',[put(['snapshot','pending_character_interaction','auto_accept_notification'],True)])
continuation('auto-accept-unknown',[put(['snapshot','pending_character_interaction','auto_accept_notification'],None)])
continuation('original-selected-step-preserved',[put(['plan','selected_step'],'save-checkpoint')])
continuation('unrelated-definition-preserved',[put(['plan','decision','definition_classification','definition_key'],'unrelated')])
continuation('wrong-blocked-phase',[put(['plan','phase'],'ordinary')])
continuation('evidence-invalid-with-gap',[put(['plan','decision','classification'],'evidence_invalid'),put(['plan','decision','interaction_key'],KEY),put(['plan','decision','marriage_contract_gaps'],['unpriced'])])
continuation('evidence-invalid-without-gap',[put(['plan','decision','classification'],'evidence_invalid'),put(['plan','decision','interaction_key'],KEY),put(['plan','decision','marriage_contract_gaps'],[])])
continuation('chooser-cannot-accept-notification',[],{'phase':'ordinary','selected_step':'accept-pending-character-interaction'})
continuation('chooser-cannot-query-notification',[],{'phase':'ordinary','selected_step':'query-pending-character-interaction-context-v1'})
continuation('chooser-cannot-leave-provided-actions',[],{'phase':'ordinary','selected_step':'unknown-step'})
continuation('chooser-cannot-return-pending-phase',[],{'phase':'pending_other','selected_step':'life-advance'})
continuation('chooser-without-step-preserves-original',[],{'phase':'ordinary','selected_step':None})
continuation('ordinary-step-order-and-duplicates-preserved',[put(['action_steps'],['save-checkpoint','life-advance','save-checkpoint','reject-pending-character-interaction'])],{'phase':'ordinary','selected_step':'save-checkpoint'})
continuation('absent-modal-status-is-not-present',[put(['snapshot','top_exclusive_modal_choice_hint'],{'status':'absent'})])
continuation('null-snapshot-preserves-original',[put(['snapshot'],None)])
paths=[root/'ck3_autonomous_player/src/xar_autoplayer/pending_arrange_marriage_source_v1.py',root/'ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py',root/'ck3_autonomous_player/src/xar_autoplayer/strategy.py',test,unit/'test_gameplay_bridge.py',root/'tools/ck3_live_run_id.py']
refs=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
golden={'schema':'xar.ck3.marriage-notice-python-golden.v1','machine_id':machine_id,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_refs':refs,'original_tests_run':len(reports.reports),'original_failures':0,'original_skipped':0,'base_review_request':review_base,'review_cases':reviews,'base_continue_request':continue_base,'continue_cases':continuations}
raw=(json.dumps(golden,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
if len(raw)>65536: raise RuntimeError('golden exceeds finite 64 KiB estimate')
output.parent.mkdir(parents=True,exist_ok=True)
with output.open('xb') as stream: stream.write(raw)
print(json.dumps({'output_path':str(output),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'review_cases':len(reviews),'continue_cases':len(continuations),'original_tests':len(reports.reports)}))
""";
        Process process = new ProcessBuilder(args[1], "-c", program, args[0], args[2]).directory(Path.of(args[0]).toFile()).inheritIO().start();
        if (!process.waitFor(Duration.ofSeconds(100).toMillis(), TimeUnit.MILLISECONDS)) { process.destroyForcibly(); throw new IllegalStateException("legacy notice capture timeout"); }
        if (process.exitValue() != 0) { throw new IllegalStateException("legacy notice capture failed: " + process.exitValue()); }
    }
}
