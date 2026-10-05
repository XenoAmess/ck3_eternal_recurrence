import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(d):return hashlib.sha256(json.dumps(d,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
def pin(p):
    p=Path(p);r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def diff(b,a):return {k:{'before':b.get(k),'after':a.get(k)} for k in sorted(set(b)|set(a)) if b.get(k)!=a.get(k)}
def project(g,drop):
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
    entries=[walk(n) if n['key']=='variables' else n for n in g['entries'] if n['key'] not in drop]
    return {'entries':entries,'C2_removed_flags':removed,'C2_exact_coverage':sorted(removed)==sorted(rows.values()),'explicit_phase_top_keys_removed':drop}
a=read(HERE/'actual-save-001/STATE.json');out={'schema':'lyd.r10.actual-successful-JOIN-complete-selected-graph-projection.v1','after_STATE':pin(HERE/'actual-save-001/STATE.json'),'comparisons':{},'all_binding_checks':{},'whole_world_characters_or_heads_scanned':False,'all_Faith_main_and_Rite_parent_registry_links_read':True,'old_save_reparsed':False}
for label,name in [('precommit187','r10-actual-eighth-precommit-readback-20261006-001'),('open171','r10-actual-eighth-open-join-readback-20261006-001'),('baseline167','r10-actual-seventh-post-cancel-readback-20261006-001')]:
    p=BASE/name/'actual-save-001/STATE.json';b=read(p);d={'before_STATE':pin(p),'Faith_main_changes':diff(b['all_faith_mains'],a['all_faith_mains']),'Rite_parent_changes':diff(b['all_rite_parents'],a['all_rite_parents']),'existing_graphs':{},'new_Rite187_complete_AST':a['source_target_related_graphs']['rites']['187']['entries']};checks={}
    checks['only_Faith106_main169_to187']=d['Faith_main_changes']=={'106':{'before':'169','after':'187'}}
    checks['only_Rite169_moves104_and_new187_retains106']=d['Rite_parent_changes']=={'169':{'before':'106','after':'104'},'187':{'before':None,'after':'106'}}
    checks['all_graph_link_consistency']=not a['all_graph_link_issues_observed']
    for kind,gs in b['source_target_related_graphs'].items():
        d['existing_graphs'][kind]={}
        for cid,bg in gs.items():
            ag=a['source_target_related_graphs'][kind][cid];drop=['faith'] if kind=='rites' and cid=='169' else ['main_rite'] if kind=='faiths' and cid=='106' else []
            bp=project(bg,drop);ap=project(ag,drop);changed=diff(bg['variables'],ag['variables']);allowed=set()
            if kind=='rites' and cid=='159':allowed={'lyd_c2_proposal_owner'} if label!='baseline167' else {'lyd_c2_proposal_owner','lyd_c2_lock_serial','lyd_c2_target_yes'}
            if kind=='rites' and cid=='169':allowed={'lyd_c2_proposal_owner','lyd_c2_transition_cooldown'} if label!='baseline167' else {'lyd_c2_lock_serial','lyd_c2_proposal_serial','lyd_c2_transition_cooldown'}
            cs={'projection_exact_C2_row_coverage':bp['C2_exact_coverage'] and ap['C2_exact_coverage'],'full_AST_except_phase_parent_and_exact_C2_rows_unchanged':bp['entries']==ap['entries'],'all_lists_unchanged':bg['lists']==ag['lists'],'complete_tenets_doctrines_unchanged':bg['tenet_doctrine_rows']==ag['tenet_doctrine_rows'],'heads_unchanged':bg['heads']==ag['heads'],'C2_changes_only_bound_phase_rows':set(changed)<=allowed}
            checks.update({kind+cid+'_'+k:v for k,v in cs.items()});d['existing_graphs'][kind][cid]={'complete_before_AST':bg['entries'],'complete_after_AST':ag['entries'],'before_projection':bp,'after_projection':ap,'changed_variable_rows':changed,'allowed_observed_phase_variables':sorted(allowed),'checks':cs}
    backup=a['source_target_related_graphs']['rites']['187'];checks['new_backup187_source106_invalid_HoR']=backup['parent_faith']=='106' and backup['heads']['head_of_rite']=='4294967295'
    checks['new_backup187_complete_tenets_equal_source169_before']=backup['tenet_doctrine_rows']==b['source_target_related_graphs']['rites']['169']['tenet_doctrine_rows']
    d['checks']=checks;out['comparisons'][label]=d;out['all_binding_checks'].update({label+'_'+k:v for k,v in checks.items()})
with (HERE/'COMPLETE-JOIN-GRAPH-AST-DIFF.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':pin(HERE/'COMPLETE-JOIN-GRAPH-AST-DIFF.json'),'checks':len(out['all_binding_checks']),'failed':[k for k,v in out['all_binding_checks'].items() if not v],'actual_registry_changes':{label:{k:d[k] for k in ['Faith_main_changes','Rite_parent_changes']} for label,d in out['comparisons'].items()}},ensure_ascii=False,indent=2))
