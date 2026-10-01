"""Regress proven full CDate, invalid artifact ID and sparse expiry semantics.

Inputs are existing R0144 original DTO and original saved-block audit. Mutants
are explicitly synthetic. This test never launches CK3, a provider, Git or a
decoder; the separate strict evaluator performs real saved-file decoding.
"""
from __future__ import annotations
import argparse,copy,datetime,hashlib,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from xar_autoplayer.simulation.knight_causal_save_projection import (
    validate_scoped_journal,validate_slain_side_knights_saved,decode_historical_date,
    decode_sparse_int32_vector,classify_death_artifact_tuple,saved_death_artifact_evidence,one,DATE_CONTRACT_PATH)

def require(ok,why):
    if not ok:raise ValueError(why)
def identity(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace',type=Path,required=True)
    parser.add_argument('--saved-audit',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    pins={}
    for label,p in [('trace',args.trace),('saved',args.saved_audit),('pure',ROOT/'src/xar_autoplayer/simulation/knight_causal_save_projection.py'),('date-contract',DATE_CONTRACT_PATH),('test',Path(__file__))]:
        q=args.output_dir/(label+'-exact'+p.suffix)
        with q.open('xb') as f:f.write(p.read_bytes())
        pins[label]={'original':identity(p),'exact_copy':identity(q)}
    w=json.loads(args.trace.read_text());m=w['body']['managed_trace'];journal,cp,trace=(m[k] for k in ('scoped_transition_chain','managed_checkpoint','trace'))
    audit=json.loads(args.saved_audit.read_text());saved=copy.deepcopy(audit['saved_states'][1]['projection']['characters'][0]);saved.setdefault('death_artifact_id',None)
    before=audit['saved_states'][0]['projection']['objects']['matched_combat_blocks'];after=audit['saved_states'][1]['projection']['objects']['matched_combat_blocks']
    require(audit['trace_original']['original']['sha256']==identity(args.trace)['sha256'],'audit original trace same bytes')
    original=validate_scoped_journal(journal,cp,33437,34120,trace,saved_victim=saved)
    require(original['death_commit_tuple_closed'] is True and original['death_artifact_tuple_closed'] is True and original['death_artifact_tuple_kind']=='nonnull-invalid-reference' and original['case_native_death_execution_path_closed'] is True,'original proven full64 invalid-reference case projection')
    slain=validate_slain_side_knights_saved(journal,before,after,33437)
    require(slain['closed'] is True and slain['after']['decoded_expiry_values']==[-1] and slain['duration_count_is_ttl'] is False,'original default expiry decode')
    cases=[{'name':'R0144 unmodified actual DTO and same-run saved block projection','pass':True,'kind':'ORIGINAL_R0144_OFFLINE_REPLAY_ONLY'}]
    def rejected(name,operation):
        try:operation()
        except (ValueError,KeyError,TypeError,struct.error) as e:
            cases.append({'name':name,'pass':True,'kind':'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH','rejection_type':type(e).__name__,'rejection':str(e)})
        else:raise ValueError('negative admitted: '+name)
    def journal_case(name,change,throws=True):
        j,c,t,s=copy.deepcopy((journal,cp,trace,saved));change(j,c,t,s)
        op=lambda:validate_scoped_journal(j,c,33437,34120,t,saved_victim=s)
        if throws:rejected(name,op)
        else:
            r=op();require(r['death_commit_tuple_closed'] is False or r['death_artifact_tuple_closed'] is False,name)
            cases.append({'name':name,'pass':True,'kind':'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH','closed':False,'artifact_kind':r['death_artifact_evidence']['kind']})
    raw=journal['records'][164]['requested_death_date_raw']
    for name,value in [('bool',True),('string',str(raw)),('missing-as-None',None),('int64overflow',1<<63),('old-date32-scalar',53146872),('wrong-day-full-word',raw+24),('wrong-day-cache',raw+(1<<32)),('wrong-month-cache',raw+(1<<40)),('wrong-year-cache',raw+(1<<48))]:
        rejected('HistoricalDate '+name,lambda v=value:decode_historical_date(v,expected_ticks=53146872,saved_calendar='1066.12.30'))
    rejected('HistoricalDate wrong saved calendar',lambda:decode_historical_date(raw,expected_ticks=53146872,saved_calendar='1066.12.29'))
    table=json.loads(DATE_CONTRACT_PATH.read_text());table['day_table']['hex']='FF'+table['day_table']['hex'][2:]
    rejected('HistoricalDate wrong original constructor table',lambda:decode_historical_date(raw,contract=table))
    journal_case('full word differs only on commit-return',lambda j,c,t,s:j['records'][182].update(requested_death_date_raw=raw+1),False)
    journal_case('missing original full word',lambda j,c,t,s:j['records'][164].pop('requested_death_date_raw'))
    journal_case('native final full object mismatch',lambda j,c,t,s:j['records'][-1]['characters'][0].update(death_date_raw=raw+1),False)
    journal_case('saved wrong civil day',lambda j,c,t,s:s.update(death_date='1066.12.29'))
    edges=[r for r in journal['records'] if r['boundary'].startswith(('death_request','death_enqueue','death_commit'))]
    def artifact(name,change,final=-1,saved_id=None,closed=False,kind=None,raises=False):
        trial=copy.deepcopy(edges);change(trial)
        op=lambda:classify_death_artifact_tuple(trial,final,saved_id,saved_verified=True)
        if raises:rejected(name,op);return
        r=op();require(r['closed'] is closed and (kind is None or r['kind']==kind),name)
        require(r.get('fallback_pointer_identity_proven',False) is False,name+' must not infer fallback pointer')
        cases.append({'name':name,'pass':True,'kind':'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH','actual_classification':r})
    artifact('actual nonnull original invalid ID',lambda rows:None,closed=True,kind='nonnull-invalid-reference')
    artifact('synthetic true null tuple independently retained',lambda rows:[r.update(requested_death_artifact_token='process-local-0x0',requested_death_artifact_id=-1,requested_artifact_id_read=False) for r in rows],closed=True,kind='verified-null')
    artifact('synthetic valid ID and saved ID match',lambda rows:[r.update(requested_death_artifact_id=51) for r in rows],final=51,saved_id=51,closed=True,kind='verified-full-id')
    artifact('positive ID missing saved object identity',lambda rows:[r.update(requested_death_artifact_id=51) for r in rows],final=51)
    journal_case('unproven artifact Save key must remain unsupported',lambda j,c,t,s:one(s['entries'],'dead_data').append({'key':'artifact','value':'51'}),False)
    journal_case('unproven nested artifact Save key must reject',lambda j,c,t,s:one(s['entries'],'dead_data').append({'key':'artifact','value':[]}))
    journal_case('duplicate known death Save key must reject',lambda j,c,t,s:one(s['entries'],'dead_data').append({'key':'date','value':'1066.12.30'}))
    journal_case('positive native ID plus guessed Save key cannot close',lambda j,c,t,s:([r.update(requested_death_artifact_id=51) for r in j['records'] if r['boundary'].startswith(('death_request','death_enqueue','death_commit'))],j['records'][-1]['characters'][0].update(death_artifact_id=51),one(s['entries'],'dead_data').append({'key':'artifact','value':'51'}),s.update(death_artifact_id=51)),False)
    journal_case('spoofed saved artifact projection cannot replace exact entries',lambda j,c,t,s:(s.update(death_artifact_id=51,death_artifact_saved_fields={'complete_known_fields_without_artifact':True}),one(s['entries'],'dead_data').append({'key':'unknown_new_key','value':'51'})),False)
    require(saved_death_artifact_evidence(one(saved['entries'],'dead_data'))['saved_id'] is None,'actual no guessed positive Save decoder')
    artifact('fake null keeps true read marker',lambda rows:[r.update(requested_death_artifact_token='process-local-0x0') for r in rows],kind='unknown-inconsistent-null')
    artifact('nonnull failed ID read stays unknown',lambda rows:[r.update(requested_artifact_id_read=False) for r in rows],kind='unknown-artifact-read')
    artifact('one pointer differs',lambda rows:rows[-1].update(requested_death_artifact_token='process-local-0x1234'),kind='unknown-mismatching-artifact-tuple')
    artifact('missing read marker',lambda rows:rows[-1].pop('requested_artifact_id_read'),kind='unknown-missing-artifact-fields')
    artifact('invalid reference contradicts saved valid ID',lambda rows:None,saved_id=51)
    artifact('invalid reference contradicts final valid ID',lambda rows:None,final=51)
    artifact('final ID bool is not actual integer sentinel',lambda rows:None,final=True,raises=True)
    artifact('saved ID bool is not actual integer',lambda rows:None,saved_id=True,raises=True)
    artifact('noncanonical false null token',lambda rows:[r.update(requested_death_artifact_token='process-local-0x000',requested_death_artifact_id=-1,requested_artifact_id_read=False) for r in rows],raises=True)
    for key,value in [('requested_artifact_id_read',1),('requested_death_artifact_id',True),('requested_death_artifact_id',-2),('requested_death_artifact_id',1<<31),('requested_death_artifact_token','UNKNOWN')]:
        artifact('typed artifact field '+key+' '+repr(value),lambda rows,k=key,v=value:rows[0].update({k:v}),raises=True)
    sparse=lambda entries:decode_sparse_int32_vector(entries)
    for name,value in [('missing-count',[]),('bool-count',[{'key':None,'value':True}]),('negative-count',[{'key':None,'value':'-1'}]),('large-count',[{'key':None,'value':'257'}]),('missing-header',[{'key':'0','value':'1'}]),('duplicate-index',[{'key':None,'value':'1'},{'key':'0','value':'7'},{'key':'0','value':'8'}]),('out-of-bounds-index',[{'key':None,'value':'1'},{'key':'1','value':'7'}]),('anonymous-second-header',[{'key':None,'value':'1'},{'key':None,'value':'7'}]),('bool-index',[{'key':None,'value':'1'},{'key':True,'value':'7'}]),('bool-value',[{'key':None,'value':'1'},{'key':'0','value':True}]),('int32-overflow',[{'key':None,'value':'1'},{'key':'0','value':str(1<<31)}]),('noncanonical-index',[{'key':None,'value':'1'},{'key':'00','value':'7'}])]:
        rejected('sparse '+name,lambda v=value:sparse(v))
    require(sparse([{'key':None,'value':'0'}])==[] and sparse([{'key':None,'value':'2'},{'key':'1','value':'7'}])==[-1,7],'complete default and explicit sparse vectors')
    cases.append({'name':'synthetic zero and mixed sparse defaults','pass':True,'kind':'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH'})
    def list_case(name,change,closed=False):
        j,b,a=copy.deepcopy((journal,before,after));change(j,b,a)
        op=lambda:validate_slain_side_knights_saved(j,b,a,33437)
        if closed:
            require(op()['closed'] is True,name);cases.append({'name':name,'pass':True,'kind':'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH'})
        else:rejected(name,op)
    list_case('native bool requested expiry',lambda j,b,a:j['records'][130].update(requested_expiry=True))
    list_case('wrong typed owner combat',lambda j,b,a:[j['records'][i].update(variable_owner_scope_words=[65547,16777219]) for i in (129,130)])
    list_case('wrong full victim list item',lambda j,b,a:j['records'][130]['variable_list_values'][0].update(scope_word1=33438))
    list_case('TTL1 masquerades as native sentinel',lambda j,b,a:j['records'][130]['variable_list_values'][0].update(expiration_raw=1))
    journal_case('sequence0 boolean alias',lambda j,c,t,s:j['records'][0].update(sequence=False))
    journal_case('native phase flags0 boolean alias',lambda j,c,t,s:t['records'][2].update(capture_failure_flags=False))
    for name,indices in [('filter-materializer',(22,23,24,101)),('predicate',(25,26)),('casualty',(177,178))]:
        journal_case('allocated crosskind collision '+name,lambda j,c,t,s,ids=indices:[j['records'][i].update(invocation=2) for i in ids])
    for name,mutate in [('checkpoint owner bool',lambda j,c,t,s:c['before'].update(thread_id=True)),('checkpoint pump bool',lambda j,c,t,s:c['before'].update(pump_epoch=True)),('endpoint invocation bool',lambda j,c,t,s:j['records'][0].update(invocation=False)),('phase owner bool',lambda j,c,t,s:[r['global_rng'].update(owner_thread_token=True) for r in t['records'][2:6]])]:
        journal_case(name,mutate)
    require(original['global_bundle_complete'] is False and original['sole_cause_proven'] is False,'global/sole unchanged false')
    result={'schema_version':1,'status':'PASS','kind':'OFFLINE_PROVEN_ABI_SEMANTICS_NOT_NEW_GAME_TRUTH','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_pins':pins,'original_projection':original,'original_saved_slain_list':slain,'pass_count':len(cases),'cases':cases,'interpreter':sys.executable,'argv':sys.argv,'limits':['Runtime/source remains frozen bba; evaluator changed source bytes are separately identified and commit pending.','Case tuple and list decode do not close monitor/whole13/global/sole cause.','No native/game/Git/decoder/movie operation occurred in this fixture.']}
    target=args.output_dir/'death-abi-semantics-offline-verification-a01.json'
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'receipt':identity(target),'cases':len(cases),'status':'PASS'}));return 0
if __name__=='__main__':raise SystemExit(main())
