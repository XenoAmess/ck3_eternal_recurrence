import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;RUN=BASE/'live-attempt-010'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(d):return hashlib.sha256(json.dumps(d,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(n,d):
    with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
expected={'0182-':'e93a1ba261edc38fc297cd964c4ed36475c71ca37e0af1a09942deefdb932011','0186-':'c7b1103ae9d9bef2290f05354dd3568a7ec217e067947e03d465ebe00ef2e383','0188-':'edeb4598e316d0d92a688b95604ac88cc0ec35561c6bbd95dca02422ccb8a89f'};controls={}
for pref,expected_sha in expected.items():
    paths=list((RUN/'mcp-client-evidence-002').glob(pref+'*.sdk-result.json'));assert len(paths)==1
    p=paths[0];ref=pin(p);assert ref['sha256']==expected_sha;d=read(p);c=d['structuredContent']
    controls[pref]={'original_SDK':ref,'isError':d['isError'],'schema':c['schema'],'status':c['status'],'session_id':c['session_id'],'profile_sha256':c['profile_sha256'],'result':c['result']}
    if 'snapshot_after' in c:controls[pref]['snapshot_after_frame']={k:c['snapshot_after'].get(k) for k in ['revision','native_revision','date_raw','paused','active_event','pending_character_interaction']}
    q=p.with_name(p.name.replace('.sdk-result.json','.request.json'))
    if q.exists():controls[pref]['original_request']={'ref':pin(q),'exact_JSON':read(q)}
write('CONTROL-EVIDENCE.json',{'schema':'lyd.r10.eighth-precommit-original-controls.v1','receipts':controls,'agent_operations':False,'AI_option_or_random_draw_inferred':False})
a=read(HERE/'actual-save-001/STATE.json');old={'open171':BASE/'r10-actual-eighth-open-join-readback-20261006-001/actual-save-001/STATE.json','baseline167':BASE/'r10-actual-seventh-post-cancel-readback-20261006-001/actual-save-001/STATE.json'}
def strip_C2(g):
    rows={sha(v['row_entries']):k for k,v in g['variables'].items() if k.startswith('lyd_c2_')};removed=[]
    def walk(o):
        if isinstance(o,list):
            out=[]
            for n in o:
                if isinstance(n,dict) and isinstance(n.get('value'),list) and sha(n['value']) in rows:removed.append(rows[sha(n['value'])]);continue
                out.append(walk(n))
            return out
        if isinstance(o,dict):return {k:walk(v) for k,v in o.items()}
        return o
    entries=[walk(n) if n['key']=='variables' else n for n in g['entries']]
    return {'entries':entries,'removed_flags':removed,'coverage_exact':sorted(removed)==sorted(rows.values())}
out={'schema':'lyd.r10.precommit-complete-selected-graph-AST-diff.v1','after_STATE':pin(HERE/'actual-save-001/STATE.json'),'comparisons':{},'all_binding_checks':{},'old_save_reparsed':False,'target_yes_qualification_from_sealed171':pin(BASE/'r10-actual-eighth-open-join-readback-20261006-001/TARGET-RITE-BALLOT-QUALIFICATION.json')}
for label,p in old.items():
    b=read(p);diff={'before_STATE':pin(p),'rites':{},'faiths':{cid:{'complete_before_AST':g['entries'],'complete_after_AST':a['source_target_related_graphs']['faiths'][cid]['entries'],'full_AST_equal':g['entries']==a['source_target_related_graphs']['faiths'][cid]['entries']} for cid,g in b['source_target_related_graphs']['faiths'].items()}}
    out['all_binding_checks'][label+'_complete_Faith_AST_unchanged']=all(v['full_AST_equal'] for v in diff['faiths'].values())
    for cid,bg in b['source_target_related_graphs']['rites'].items():
        ag=a['source_target_related_graphs']['rites'][cid];bs=strip_C2(bg);as_=strip_C2(ag);changed={k:{'before':bg['variables'].get(k),'after':ag['variables'].get(k)} for k in sorted(set(bg['variables'])|set(ag['variables'])) if bg['variables'].get(k)!=ag['variables'].get(k)}
        allowed=set() if label=='open171' else {'lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial'}|({'lyd_c2_target_yes'} if cid=='159' else set())
        checks={'exact_C2_row_projection_coverage':bs['coverage_exact'] and as_['coverage_exact'],'full_non_C2_AST_unchanged':bs['entries']==as_['entries'],'all_lists_unchanged':bg['lists']==ag['lists'],'changed_vars_only_phase_bound_rows':set(changed)<=allowed}
        out['all_binding_checks'].update({label+'_Rite'+cid+'_'+k:v for k,v in checks.items()})
        diff['rites'][cid]={'complete_before_AST':bg['entries'],'complete_after_AST':ag['entries'],'before_C2_projection':bs,'after_C2_projection':as_,'changed_variable_rows':changed,'allowed_observed_phase_variable_names':sorted(allowed),'checks':checks}
    out['comparisons'][label]=diff
write('COMPLETE-RITE-FAITH-AST-DIFF.json',out)
print(json.dumps({'controls':{k:{'ref':c['original_SDK'],'frame':c.get('snapshot_after_frame'),'result_keys':list(c['result']),'typed_event':c['result'].get('current_event_window_context')} for k,c in controls.items()},'complete_checks':out['all_binding_checks'],'changed_vars':{label:{cid:list(g['changed_variable_rows']) for cid,g in d['rites'].items()} for label,d in out['comparisons'].items()}},ensure_ascii=False,indent=2))
