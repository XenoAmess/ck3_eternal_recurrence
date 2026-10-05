import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def row(v):return None if v is None else {k:v.get(k) for k in ['present','tick','type','identity','number']}
def change(d1,d2):return {k:{'before':d1.get(k),'after':d2.get(k)} for k in sorted(set(d1)|set(d2)) if d1.get(k)!=d2.get(k)}
def entries(d):return {n['key']:n['value'] for n in d}
a=read(HERE/'actual-save-001/STATE.json');b=read(BASE/'r10-actual-eighth-precommit-readback-20261006-001/actual-save-001/STATE.json')
out={'schema':'lyd.r10.post-JOIN-actual-incremental-inspection.v1','after_STATE':pin(HERE/'actual-save-001/STATE.json'),'before187_STATE':pin(BASE/'r10-actual-eighth-precommit-readback-20261006-001/actual-save-001/STATE.json'),'summary':{k:v for k,v in a['summary'].items() if k.startswith('current_') or k in ['wallet','stress_saved','learning_XP_saved','cooldown']},'actor_C2':{k:row(v) for k,v in a['all_actor_LYD_variables'].items() if k.startswith('lyd_c2_')},'Faith_main_changes':change(b['all_faith_mains'],a['all_faith_mains']),'Rite_parent_changes':change(b['all_rite_parents'],a['all_rite_parents']),'selected_graphs':{},'persons':{},'political7_equal':b['summary']['political7']==a['summary']['political7'],'landed_equal':b['actor_protected_landed']==a['actor_protected_landed'],'graph_link_issues':a['all_graph_link_issues_observed'],'C2_list_changes':change(b['all_actor_LYD_lists'],a['all_actor_LYD_lists'])}
for kind,gs in a['source_target_related_graphs'].items():
    out['selected_graphs'][kind]={}
    for cid,g in gs.items():
        bg=b['source_target_related_graphs'][kind].get(cid);delta=None if bg is None else change(entries(bg['entries']),entries(g['entries']))
        out['selected_graphs'][kind][cid]={'parent_faith':g['parent_faith'],'main_rite':g['main_rite'],'heads':g['heads'],'C2_variables':{k:row(v) for k,v in g['variables'].items() if k.startswith('lyd_c2_')},'changed_top_keys':None if delta is None else list(delta),'top_AST_changes':delta,'tenet_doctrine_rows':g['tenet_doctrine_rows'],'lists':g['lists']}
for cid,g in a['character_roles'].items():
    bg=b['character_roles'].get(cid);out['persons'][cid]={'before_rite':None if bg is None else bg['rite'],'after_rite':g['rite'],'top_protected_equal':None if bg is None else bg['protected_top']==g['protected_top'],'alive_protected_equal':None if bg is None else bg['protected_alive']==g['protected_alive'],'C2_variables':{k:row(v) for k,v in g['variables'].items() if k.startswith('lyd_c2_')}}
with (HERE/'INCREMENTAL-INSPECTION.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
small={k:v for k,v in out.items() if k not in ['selected_graphs','C2_list_changes','actor_C2']};small['actor_C2']={k:v for k,v in out['actor_C2'].items() if k in ['lyd_c2_result','lyd_c2_callback_nonce','lyd_c2_serial','lyd_c2_active','lyd_c2_completed_joins','lyd_c2_completed_detaches','lyd_c2_source_signed','lyd_c2_target_requested','lyd_c2_target_signed','lyd_c2_source_head_retired']};small['graph_changes']={kind:{cid:{k:v for k,v in g.items() if k in ['parent_faith','main_rite','heads','changed_top_keys','C2_variables']} for cid,g in gs.items()} for kind,gs in out['selected_graphs'].items()};small['list_changed_keys']=list(out['C2_list_changes'])
print(json.dumps(small,ensure_ascii=False,indent=2))
