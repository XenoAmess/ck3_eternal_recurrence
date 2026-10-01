"""Meaningful new thread contract tests from actual R0140 and compiled fixtures."""
import copy,datetime,hashlib,importlib.util,json,pathlib,shutil,subprocess,sys
sys.dont_write_bytecode=True
B=pathlib.Path(__file__).resolve().parent
OUT=B/'monitor-thread-semantics-repair-attempt-01/offline-verification-attempt-02'
P=pathlib.Path('C:/w/e2research1001/ck3_autonomous_player/src/xar_autoplayer/simulation/knight_variable_monitor_projection.py')
V=pathlib.Path('C:/w/e2research1001/ck3_autonomous_player/native_bridge/research/verify_knight_variable_monitor_run.py')
R=pathlib.Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a04/scoped-ui-research-attempt-01/failed-ui-monitor-end.json')
F=pathlib.Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/mechanism-native-bundle-attempt-01/build-attempt-12-current-death-commit/offline-monitor-fixture-stdout.bin')
C=B/'signature_commit_correlation_a02.py'

def identity(p):
    p=pathlib.Path(p)
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest().upper()
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha}
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    OUT.mkdir(exist_ok=False);sources=[]
    for p,label in ((P,'new-pure-exact.py'),(V,'new-run-verifier-exact.py'),(R,'R0140-actual-original-end-exact.json'),(F,'compiled-native-OFFLINE-fixtures-exact.bin'),(C,'external-commit-correlator-exact.py'),(pathlib.Path(__file__),'runner-exact.py')):
        dest=OUT/label;shutil.copyfile(p,dest);sources.append({'original':identity(p),'exact_copy':identity(dest)})
    pure=module('new_pure',P);corr=module('same_original_commit',C)
    actual=json.loads(R.read_text(encoding='utf-8'));monitor=actual['scoped_variable_monitor']
    def validate(mon):return pure.validate_variable_monitor(mon,character_ids=mon['character_ids'],expected_monitor_token=mon['monitor_sequence_token'],before_date_raw=mon['begin_date_raw'],after_date_raw=mon['records'][-1]['date_raw'],expected_thread=mon['records'][0]['thread_id'])
    result=validate(monitor);states=result['first_original_owner_observations']
    assert result['actual_observer_thread_ids']==[3900,13000]
    assert states[0]['status']=='OBSERVED_ABSENT_AT_ORIGINAL_GETTER' and states[0]['thread_id']==3900
    assert states[1]['status']=='UNKNOWN_NO_ORIGINAL_GETTER' and states[1]['is_arm_initial_state'] is False
    assert result['actual_write_pairs']==[] and result['producer_closed'] is False
    cases=[{'name':'actual R0140 GUI getter thread3900 allowed; controlled lifecycle13000 retained; missing34120 getter UNKNOWN','pass':True,'kind':'ACTUAL_FAILED_NO_DAY_WINDOW_ONLY'}]
    objects=[json.loads(line) for line in F.read_text(encoding='utf-8').splitlines() if line.startswith('{')]
    scoped=next(o for o in objects if o.get('kind')=='OFFLINE_COMMIT_PRODUCER_FIXTURE_NOT_GAME_TRUTH')
    mon,journal=scoped['scoped_variable_monitor'],scoped['scoped_transition_chain']
    baseline=validate(mon)
    assert len(baseline['actual_write_pairs'])==4
    operation=corr.correlate_signature_commits(mon,journal,victim=mon['character_ids'][0],related=mon['character_ids'][1])
    assert [r['specific_victim_correlation'] for r in operation['writes']]==['closed','pending','pending','closed']
    cases.append({'name':'actual compiled commit/producer/write fixture still passes original per-operation binding','pass':True,'kind':scoped['kind']})
    basic=next(o for o in objects if o.get('kind')=='OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH')['scoped_variable_monitor']
    basic_result=validate(basic)
    assert basic_result['original_house_predicate_pairs']
    cases.append({'name':'actual compiled original house operation fixture passes strict paired arguments','pass':True,'kind':'OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH'})
    def reject(name,original,change,commit=False):
        mutant=copy.deepcopy(original);change(mutant)
        try:
            if commit:corr.correlate_signature_commits(mutant,journal,victim=mon['character_ids'][0],related=mon['character_ids'][1])
            else:validate(mutant)
        except (ValueError,KeyError) as e:
            cases.append({'name':name,'pass':True,'actual_rejection':type(e).__name__+': '+str(e),'kind':'DERIVED_OFFLINE_MUTANT_NOT_GAME_TRUTH'})
        else:raise AssertionError('mutant accepted '+name)
    def edge_field(boundary,field,value):
        def change(m):next(r for r in m['records'] if r['boundary']==boundary)[field]=value
        return change
    reject('actual writer enter/return thread crossover rejected',mon,edge_field('variable_write_return','thread_id',1))
    reject('actual writer context crossover rejected',mon,edge_field('variable_write_return','execution_context_token',1))
    reject('actual writer full ID crossover rejected',mon,edge_field('variable_write_return','observed_character_id',999))
    reject('actual house enter/return thread crossover rejected',basic,edge_field('house_predicate_return','thread_id',1))
    reject('actual house execution context crossover rejected',basic,edge_field('house_predicate_return','execution_context_token',1))
    reject('actual house key crossover rejected',basic,edge_field('house_predicate_return','relation_type_key','not_the_original_key'))
    reject('final lifecycle cannot switch to GUI thread',monitor,edge_field('final_paused','thread_id',3900))
    reject('observer thread must be actual nonzero stamp',monitor,edge_field('original_owner_return','thread_id',0))
    def commit_thread(m):
        for r in m['records']:
            if r['boundary'] in ('variable_write_enter','variable_write_return'):
                for c in (r['current_death_commit_context'],r['event_producer']['activation_death_commit_context']):
                    if c['read']:c['thread_id']+=1
    reject('commit ancestry cannot cross writer thread',mon,commit_thread,commit=True)
    unread=copy.deepcopy(monitor)
    next(r for r in unread['records'] if r['boundary']=='original_owner_return')['value']['read']=False
    unread_result=validate(unread)
    assert unread_result['first_original_owner_observations'][0]['status']=='UNKNOWN_ORIGINAL_GETTER_VALUE_NOT_READ'
    cases.append({'name':'unread original getter value stays UNKNOWN, never absent','pass':True,'kind':'DERIVED_OFFLINE_MUTANT_NOT_GAME_TRUTH'})
    argv=[sys.executable,'-B',str(V),'--help'];completed=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
    stdout,stderr=OUT/'actual-help.stdout.bin',OUT/'actual-help.stderr.bin';stdout.write_bytes(completed.stdout);stderr.write_bytes(completed.stderr)
    assert completed.returncode==0 and not completed.stderr
    report={'schema_version':1,'status':'PASS_NEW_MONITOR_THREAD_CONTRACT','created_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),
            'sources':sources,'cases':cases,'pass_count':len(cases),'actual_R0140_projection':result,
            'compiled_OFFLINE_commit_fixture_projection':operation,
            'help':{'argv':argv,'returncode':completed.returncode,'stdout':identity(stdout),'stderr':identity(stderr)},
            'R0140_research_status':'RED_UI_ADMISSION_NO_DAY_ADVANCE','R0140_day_advance_count':0,'R0140_six_gaps_closed':False,
            'game_calls':0,'desktop_inputs':0,'master_intake':False,'frozen_e2cap_source_changed':False,
            'limits':'R0140 has no day and no writers. Compiled fixtures are not game truth. Complete live commit/selector/13-domain verdict still awaits a new successful run.'}
    path=OUT/'monitor-thread-semantics-verification-a02.json'
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'receipt':identity(path),'pass_count':len(cases),'new_sources':sources[:2]}))

if __name__=='__main__':main()
