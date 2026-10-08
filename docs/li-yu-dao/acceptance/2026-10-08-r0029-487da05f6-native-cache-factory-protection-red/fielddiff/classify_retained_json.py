from pathlib import Path
from hashlib import sha256
from collections import Counter
import ast,json,re
B=Path('C:/workspace/ck3_lyd_runtime_20261004');R=B/'live-attempt-029';OUT=Path(__file__).parent
refs={}
def need(ok,message):
    if not ok:raise ValueError(message)
def read(key,path,expected=None):
    need(path.suffix.lower()=='.json'and 0<path.stat().st_size<=8*1024*1024,'bounded retained JSON only')
    raw=path.read_bytes();descriptor={'path':path.as_posix(),'bytes':len(raw),'sha256':sha256(raw).hexdigest()}
    if expected:need(descriptor['sha256']==expected,'original retained SHA differs '+key)
    refs[key]=descriptor;return json.loads(raw)
def fields(rows):
    answer = {}
    for row in rows:
        answer.setdefault(row['key'], []).append(row['value'])
    return answer
def changed(old, new):
    a, c = fields(old), fields(new)
    return {str(k): {'before': a.get(k), 'after': c.get(k)} for k in a.keys() | c.keys() if a.get(k) != c.get(k)}
def write(name,value):
    with(OUT/name).open('x',encoding='utf-8',newline='\n')as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
def ref(path):
    raw=path.read_bytes();return {'path':path.as_posix(),'bytes':len(raw),'sha256':sha256(raw).hexdigest()}
def counts(rows):
    need(all(type(row['matches'])is bool for row in rows),'original bool matches field required')
    return {'total':len(rows),'TRUE':sum(row['matches']is True for row in rows),'FALSE':sum(row['matches']is False for row in rows),'failed':[row for row in rows if row['matches']is False]}
def ids_from_array(rows):
    out=[]
    need(type(rows)is list,'actual complete saved ID array required')
    for row in rows:
        need(type(row)is dict and set(row)=={'key','value'}and row['key']is None and type(row['value'])is str and re.fullmatch('0|[1-9][0-9]*',row['value'])is not None,'actual complete fullID leaf required')
        value=int(row['value']);need(0<=value<2**32-1,'actual uint32 fullID excluding invalid sentinel required');out.append(value)
    return out
def list_change(a,b):
    old,new=Counter(a),Counter(b)
    return {'before_count':len(a),'after_count':len(b),'before_complete_original_order':a,'after_complete_original_order':b,'removed_in_before_order':[value for i,value in enumerate(a)if Counter(a[:i+1])[value]>new[value]],'added_in_after_order':[value for i,value in enumerate(b)if Counter(b[:i+1])[value]>old[value]],'order_and_length_equal':a==b}
before=read('B3_STATE',R/'B3-r3-signed-author-001/STATE.json','9f64e5e54756e0ee07562d1845daf11d033ed52df3edb9773d7a4829ca810753')
after=read('B4_STATE',R/'B4-r3-signed-author-001/STATE.json','b8f28537059e04df4a0a75617017be1e81f6682b35764648ea18d271cee9c596')
typed_before=read('B3_TYPED',R/'B3-r3-signed-author-001/TYPED-PROTECTION.json','ae6e960c9577b9fcadf0eb7bce835d14745ef1a754bc7387c925706f251eb679')
typed_after=read('B4_TYPED',R/'B4-r3-signed-author-001/TYPED-PROTECTION.json','3fe9a040018ff32d55d6510d2aa8b96182acc331d4c9a50456fceebd9828515f')
read('B4_AUTHOR_RESULT',R/'B4-r3-signed-author-001/RESULT.json','62e7a48cd48297f6e317bb2b5334e6f0feb3fb66ef7c263119e6f36c029773e7')
cache_before=read('B3_native_saved_cache_comparison',R/'R3-B3-NATIVE-SAVED-CACHE-COMPARISON-001/RESULT.actual.json')
cache_after=read('B4_native_saved_cache_comparison',R/'R3-B4-NATIVE-SAVED-CACHE-COMPARISON-001/RESULT.actual.json')
need(before['stage']=='signed_precommit'and after['stage']=='success_postcommit'and before['identity']['actor_id']==after['identity']['actor_id']==31254,'exact B3/B4 actual stage/actor required')
for key in ('pid','session_id'):need(before['identity'][key]==after['identity'][key],'retained B3/B4 process/session differs')
pc=counts(typed_after['checks']);sc=counts(after['checks'])
need((pc['total'],pc['TRUE'],pc['FALSE'])==(88,82,6)and(sc['total'],sc['TRUE'],sc['FALSE'])==(48,43,5),'actual original failure counts differ')
actor_check=next(row for row in pc['failed']if row['name']=='actor_complete_protected_landed_projection')
actor_diff=changed(actor_check['expected'],actor_check['observed'])
need(set(actor_diff)=={'succession'},'extra protected actor field change observed; report must not hide it')
a=fields(before['actor']['landed_data'])['succession'];c=fields(after['actor']['landed_data'])['succession'];need(len(a)==len(c)==1,'unique saved cached succession field required')
actor_cache=list_change(ids_from_array(a[0]),ids_from_array(c[0]));need((actor_cache['before_count'],actor_cache['after_count'])==(45,40),'actual saved cache counts differ')
for label,report,stage,state_ref,ids in [('B3',cache_before,'B3',refs['B3_STATE'],actor_cache['before_complete_original_order']),('B4',cache_after,'B4',refs['B4_STATE'],actor_cache['after_complete_original_order'])]:
    need(report['stage']==stage and report['native_to_saved_equality']is True and report['input_artifacts']['state']==state_ref,'original authenticated comparison/state binding differs '+label)
    need(report['complete_native_successor_ids_in_original_order']==report['complete_saved_successor_ids_in_original_order']==ids,'native/saved full ordered cache values differ '+label)
old={row['title_id']:row for row in before['protected_titles']};new={row['title_id']:row for row in after['protected_titles']}
need(set(old)==set(new)=={2230,2231,2232,2235,2262,2263,2264},'original seven political title universe differs')
title_diff={};title_summary={}
for title_id in sorted(old):
    before_rows=old[title_id]['entries'];after_rows=new[title_id]['entries'];delta=changed(before_rows,after_rows)
    title_summary[str(title_id)]={'complete_AST_equal':before_rows==after_rows,'changed_field_names':sorted(delta),'laws_changed_fields':{key:value for key,value in delta.items()if 'law'in key.lower()},'other_changed_fields':{key:value for key,value in delta.items()if 'heir'not in key.lower()and 'law'not in key.lower()}}
    if delta:
        title_diff[str(title_id)]=delta
        for key,value in delta.items():
            if 'heir'in key.lower()and value['before']is not None and value['after']is not None:
                need(len(value['before'])==len(value['after'])==1,'unique complete title heir field required')
                title_summary[str(title_id)][key+'_ordered_ID_changes']=list_change(ids_from_array(value['before'][0]),ids_from_array(value['after'][0]))
need(set(title_diff)=={'2230','2231','2235','2262','2264'},'exact original five changed political titles differ')
reuse=B/'r27-root-factory-field-diff-20261008-001.py';reuse_text=reuse.read_text(encoding='utf-8');own_text=Path(__file__).read_text(encoding='utf-8')
old_functions={node.name:node for node in ast.parse(reuse_text).body if isinstance(node,ast.FunctionDef)}
new_functions={node.name:node for node in ast.parse(own_text).body if isinstance(node,ast.FunctionDef)}
need(all(ast.dump(old_functions[name],include_attributes=False)==ast.dump(new_functions[name],include_attributes=False)for name in ('fields','changed')),'R27 field classifier AST changed')
report={'schema':'lyd.r29.retained-B3-B4-protected-field-diff.v1','status':'OBSERVED_PROTECTION_MISMATCH_RETAINED_JSON_ONLY','inputs':refs,'R27_classifier_source':ref(reuse),'R27_fields_changed_AST_reused_exact':True,'B3_typed_counts':counts(typed_before['checks']),'B4_typed_protection_counts':pc,'B4_saved_check_counts':sc,'actor_protected_landed_field_changes':actor_diff,'actor_cached_succession':actor_cache,'political_title_field_changes':title_diff,'all_seven_political_title_summary':title_summary,'existing_native_saved_comparisons':{'B3':{'result_ref':refs['B3_native_saved_cache_comparison'],'native_to_saved_equality':True,'count':45},'B4':{'result_ref':refs['B4_native_saved_cache_comparison'],'native_to_saved_equality':True,'count':40}},'classification_scope':'Only exact retained saved JSON field changes and already authenticated per-stage native/saved cache equality; no engine intermediate trace or broader realm law inference','new_religious_title':typed_after['actual_added_religious_title'],'cause':None,'cause_status':'UNKNOWN','business_acceptance':False,'C3_credit':None,'I4_credit':None,'cold_success_credit':None,'actual_pass':None,'SDK_calls':0,'process_calls':0,'save_body_reads':0,'binary_reads':0,'main_writes':0,'tests_rerun':False}
write('FIELD-DIFF.actual.json',report)
compact={'inputs':refs,'B4_typed_counts':{key:pc[key]for key in('total','TRUE','FALSE')},'B4_saved_counts':{key:sc[key]for key in('total','TRUE','FALSE')},'failed_protection_names':[row['name']for row in pc['failed']],'failed_saved_names':[row['name']for row in sc['failed']],'actor_cache':actor_cache,'titles':title_summary,'cause':None,'cause_status':'UNKNOWN','business_acceptance':False,'actual_pass':None,'save_body_reads':0,'SDK_calls':0,'main_writes':0}
write('SUMMARY.actual.json',compact)
write('INDEX.json',{'schema':'lyd.r29.retained-field-diff-index.v1','status':report['status'],'files':[ref(OUT/'FIELD-DIFF.actual.json'),ref(OUT/'SUMMARY.actual.json'),ref(Path(__file__))],'original_inputs':refs,'cause':None,'actual_pass':None,'save_body_reads':0,'SDK_calls':0,'process_calls':0,'binary_reads':0,'main_writes':0,'tests_rerun':False})
print(json.dumps({'INDEX':ref(OUT/'INDEX.json'),'report':ref(OUT/'FIELD-DIFF.actual.json'),'summary':ref(OUT/'SUMMARY.actual.json'),'actor_removed':actor_cache['removed_in_before_order'],'actor_added':actor_cache['added_in_after_order'],'title_changed_keys':{key:value['changed_field_names']for key,value in title_summary.items()},'typed_counts':{key:pc[key]for key in('total','TRUE','FALSE')},'saved_counts':{key:sc[key]for key in('total','TRUE','FALSE')}}))
