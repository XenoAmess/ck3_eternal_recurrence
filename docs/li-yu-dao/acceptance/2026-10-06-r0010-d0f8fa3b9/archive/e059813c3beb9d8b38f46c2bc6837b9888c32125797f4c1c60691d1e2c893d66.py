import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
a=read(HERE/'actual-save-001/STATE.json');old={'before167':BASE/'r10-actual-seventh-post-cancel-readback-20261006-001/actual-save-001/STATE.json'}
def strip_observed_C2_variable_rows(graph):
    rows={sha(v['row_entries']):k for k,v in graph['variables'].items() if k.startswith('lyd_c2_')};removed=[]
    def walk(obj,path):
        if isinstance(obj,list):
            output=[]
            for i,node in enumerate(obj):
                if isinstance(node,dict) and isinstance(node.get('value'),list) and sha(node['value']) in rows:
                    removed.append({'path':path+[i],'flag':rows[sha(node['value'])],'exact_node':node});continue
                output.append(walk(node,path+[i]))
            return output
        if isinstance(obj,dict):return {k:walk(v,path+[k]) for k,v in obj.items()}
        return obj
    entries=[]
    for i,node in enumerate(graph['entries']):entries.append(walk(node,[i]) if node['key']=='variables' else node)
    return {'entries':entries,'removed_rows':removed,'removed_flags':[r['flag'] for r in removed],'coverage_exact':sorted(r['flag'] for r in removed)==sorted(rows.values())}
out={'schema':'lyd.r10.eighth-open-complete-selected-graph-AST-diff.v1','after_STATE':pin(HERE/'actual-save-001/STATE.json'),'complete_Rite_AST_diffs':{},'all_binding_checks':{},'old_save_reparsed':False}
for label,p in old.items():
    before=read(p);out['complete_Rite_AST_diffs'][label]={'before_STATE':pin(p),'rites':{},'full_faith_AST_unchanged':{cid:row['entries']==a['source_target_related_graphs']['faiths'][cid]['entries'] for cid,row in before['source_target_related_graphs']['faiths'].items()}}
    out['all_binding_checks'][label+'_full_faith_AST_unchanged']=all(out['complete_Rite_AST_diffs'][label]['full_faith_AST_unchanged'].values())
    for cid in ['159','169']:
        bg=before['source_target_related_graphs']['rites'][cid];ag=a['source_target_related_graphs']['rites'][cid];bs=strip_observed_C2_variable_rows(bg);as_=strip_observed_C2_variable_rows(ag);changed={k:{'before':bg['variables'].get(k),'after':ag['variables'].get(k)} for k in sorted(set(bg['variables'])|set(ag['variables'])) if bg['variables'].get(k)!=ag['variables'].get(k)}
        checks={'C2_rows_removal_exact_coverage':bs['coverage_exact'] and as_['coverage_exact'],'full_AST_except_exact_observed_C2_variable_rows_unchanged':bs['entries']==as_['entries'],'changed_variables_only_expected_C2_owner_lock_serial':set(changed)<={'lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_proposal_serial'},'all_parsed_lists_unchanged':bg['lists']==ag['lists']}
        for k,v in checks.items():out['all_binding_checks'][label+'_Rite'+cid+'_'+k]=v
        out['complete_Rite_AST_diffs'][label]['rites'][cid]={'complete_before_AST':bg['entries'],'complete_after_AST':ag['entries'],'complete_before_AST_sha256':sha(bg['entries']),'complete_after_AST_sha256':sha(ag['entries']),'before_exact_C2_row_projection':bs,'after_exact_C2_row_projection':as_,'changed_variable_rows':changed,'checks':checks}
with (HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':pin(HERE/'COMPLETE-RITE-FAITH-AST-DIFF.json'),'checks':out['all_binding_checks'],'changed_variable_keys':{label:{cid:list(row['changed_variable_rows']) for cid,row in diff['rites'].items()} for label,diff in out['complete_Rite_AST_diffs'].items()}},ensure_ascii=False,indent=2))
