"""Prepare exact read-only verifier inputs; never read unfinished live results."""
import datetime,hashlib,json,pathlib,shutil,subprocess,sys
sys.dont_write_bytecode=True
B=pathlib.Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
ROOT=B/'knight-R0141-readonly-verification-attempt-01'
OUT=ROOT/'preparation-attempt-01'
S=pathlib.Path('C:/w/e2cap1001c/ck3_autonomous_player')
H=pathlib.Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-05-scoped-ui')
LIVE=pathlib.Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a05')
E=LIVE/'scoped-ui-research-attempt-01'
OLD=B/'knight-selector-causality-research-attempt-01'
RAKALY=pathlib.Path('D:/workspace/ck3_native_war_ai_promo_work/episode01-effect-save-attempt-008/rakaly-0.8.19-x86_64-pc-windows-msvc/rakaly.exe')
def identity(p):
    p=pathlib.Path(p)
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest().upper()
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha}
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    c=S/'native_bridge/research/verify_knight_causal_run.py';m=S/'native_bridge/research/verify_knight_variable_monitor_run.py'
    a=OLD/'verify_signature_commit_correlation_run_a01.py';rng=OLD/'saved_rng_endpoint_inventory_a01.py'
    copies=[];helps=[]
    for p in (c,m,a,rng,OLD/'signature_commit_correlation_a02.py',S/'src/xar_autoplayer/simulation/knight_variable_monitor_projection.py',H/'scoped_ui_research_a08.py',H/'prepare_runtime_binding_and_plan_a08.py',pathlib.Path(__file__)):
        dest=OUT/p.name;shutil.copyfile(p,dest);copies.append({'original':identity(p),'exact_copy':identity(dest)})
    for p in (c,m,a,rng):
        argv=[sys.executable,'-B',str(p),'--help'];process=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        stdout,stderr=OUT/(p.stem+'-help.stdout.bin'),OUT/(p.stem+'-help.stderr.bin')
        stdout.write_bytes(process.stdout);stderr.write_bytes(process.stderr)
        assert process.returncode==0 and not process.stderr
        helps.append({'argv':argv,'returncode':process.returncode,'stdout':identity(stdout),'stderr':identity(stderr)})
    manifest=H/'frozen-release-build-attempt-01/candidate-manifest.json';candidate=json.loads(manifest.read_text(encoding='utf-8'))
    dll=identity(candidate['dll']['path']);injector=identity(candidate['injector']['path'])
    assert dll['sha256']=='1B3AC08147D86D34D69390331D2AD7C486B64C07D4F795E10DA4A3E5DE2CE324' and dll['bytes']==3553792
    assert injector['sha256']=='2CA0E8889E7CC2AA59517F038B731ECD0C535E410A512C3A62BE8EC772627DB8' and injector['bytes']==39936
    assert candidate['source_commit']=='fda53e7b3e83053f235be3d5725a6238b89db9f0'
    assert identity(RAKALY)['sha256']=='E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D'
    causal=ROOT/'causal-run-attempt-01';monitor=ROOT/'variable-monitor-attempt-01';addon=ROOT/'signature-commit-attempt-01'
    causal_argv=[sys.executable,'-B',str(c),'--before-pair',str(E/'before-saved-pair.json'),'--after-pair',str(E/'after-saved-pair.json'),'--before-save',str(E/'before-immutable.ck3'),'--after-save',str(E/'after-immutable.ck3'),'--trace',str(LIVE/'ck3-output/interactive-requests-responses/scoped-chain-finish-once.json'),'--rakaly',str(RAKALY),'--output-dir',str(causal),'--expected-source-head',candidate['source_commit'],'--expected-dll-sha256',dll['sha256'],'--episode-character-id','29829','--victim','33437','--related','34120','--day-finished',str(E/'one-day-finished.json')]
    monitor_argv=[sys.executable,'-B',str(m),'--begin',str(E/'variable-monitor-begin.json'),'--finish',str(E/'variable-monitor-finish.json'),'--causal-projection',str(causal/'knight-causal-run-verification.json'),'--output-dir',str(monitor)]
    addon_argv=[sys.executable,'-B',str(a),'--monitor-verification',str(monitor/'knight-variable-monitor-run-verification.json'),'--causal-verification',str(causal/'knight-causal-run-verification.json'),'--output-dir',str(addon)]
    report={'schema_version':1,'kind':'R0141_READONLY_VERIFICATION_PREPARATION_NOT_RUN',
        'created_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),'sources':copies,'actual_helps':helps,
        'frozen_candidate_manifest':identity(manifest),'exact_DLL':dll,'exact_injector':injector,'decoder':identity(RAKALY),
        'root_reported_expected_run':'R0141','root_reported_expected_PID':6320,
        'same_PID_session_admission':'pending actual current-run-bindings/native receipt/hello reading after root finish notice',
        'raw_run_bindings_expected_path':str(H/'current-run-bindings.json'),
        'commands_not_executed':[{'phase':'main causal save/trace/selector', 'argv':causal_argv},{'phase':'monitor receipt/lifecycle/operations','argv':monitor_argv},{'phase':'original-current-commit signature ancestry','argv':addon_argv}],
        'four_save_windows':[{ 'phase':phase,'pre_UI_pair':str(E/(phase+'-pre-ui-checkpoint-saved-pair.json')),'post_UI_pair':str(E/(phase+'-saved-pair.json')),'new_output':str(ROOT/('ui-window-'+phase+'-attempt-01')),'time_scope':'same-date serialized endpoints, not a second day or all RNG proof'} for phase in ('before','after')],
        'required_future_semantic_verdict':{'six_gaps':['next-day character original UI','same-ID combat roster/list change','complete original battle panel','selector materializer/filter/RNG/return','case-specific unique correlated death request/queue/commit cause','13 case write domains with time resolution'],
                                          'verdict_status':'NOT_RUN_NO_CURRENT_ORIGINAL_FACTS_READ','global_bundle_complete':False,'signoff':False},
        'old_run_values_filled':False,'unfinished_live_result_files_read':False,'game_calls':0,'desktop_inputs':0,'git_operations':0,'master_intake':False}
    p=OUT/'R0141-readonly-verifier-preparation-a01.json'
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'receipt':identity(p),'actual_help_count':len(helps),'verification_status':'NOT_RUN'}))
if __name__=='__main__':main()
