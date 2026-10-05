from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;B=Path('C:/workspace/ck3_lyd_runtime_20261004')
M=Path('C:/workspace/ck3_eternal_recurrence/mod_li_yu_dao')
SNAP=json.loads((O/'snapshot-001/RUNTIME-SNAPSHOT.json').read_bytes())
BEFORE={r['path']:r for r in SNAP['before_rows']};AFTER={r['path']:r for r in SNAP['after_rows']}
P=O/'lineage-001';P.mkdir(exist_ok=False)
def sha(data):return hashlib.sha256(data).hexdigest()
def ref(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':sha(data)}
def bind(path,expected=None):
    value=ref(path)
    if expected:assert value['sha256']==expected,path
    raw=path.read_bytes();out=P/'inputs'/path.relative_to(B)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('xb') as f:f.write(raw)
    return value
def exact(path,size,digest):
    value=ref(path);assert value['bytes']==size and value['sha256']==digest,str(path)
    return value
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def index_rows(value):
    if 'payload' in value:return value['payload']
    if 'files' in value:return value['files']
    if 'artifacts' in value:return value['artifacts']
    return [{'path':k,**v} for k,v in value.items()]
C2=B/'c2-preview-scopefix-full-candidate-20261005-003'
C3=B/'c3-i3b-detached-authority-implementation-20261005-001'
APP=B/'c3-i3b-current-main-delta-applicability-20261005-001'
GUARD=B/'c3-i3b-optional-target-guard-candidate-20261005-001'
index_refs={
 'C2':bind(C2/'INDEX.json','2cae12ec173758b5c81f8cda98bccf4a3e7777ac35348aee2d1e9357e513edea'),
 'C3_I3b':bind(C3/'INDEX.json','d95def5e0be15aad12eef35049f3aa3c8f3b8fed7553bafc4175c010be0bafc5'),
 'current_applicability':bind(APP/'INDEX.json','2404ddbbc5003d8a8fb3379a32208ac22a729360fd77e29cdd64dc80c463cafc'),
 'guards':bind(GUARD/'INDEX.json','44f0e25545d824e0dd72d13012b698bb73658f80b9b855a51aa3fbd739a4bcfb')}
appidx=json.loads((APP/'INDEX.json').read_bytes());app_payload={r['path']:r for r in index_rows(appidx)}
root26path=B/'root-c3-i3b-apply-20261005-001/APPLIED.json';root26=json.loads(root26path.read_bytes())
root26ref=bind(root26path);plan=root26['plan'];planpath=APP/'CURRENT-TARGETBEFORE-SHA.json'
assert plan==json.loads(planpath.read_bytes());bind(planpath)
rootguardpath=B/'root-c3-optional-guards-apply-20261005-001/APPLIED.json';rootguard=json.loads(rootguardpath.read_bytes())
rootguardref=bind(rootguardpath)
handoffpath=GUARD/'handoff-001/ROOT-APPLY-INPUTS.json';handoff=json.loads(handoffpath.read_bytes())
handoffref=bind(handoffpath,'efbec80d601c2f7452c50e6c1010913caf29251c63d8d72c16a1ac84e5e229b0')
assert rootguard['inputs']==handoff['inputs']
assert len(plan['files'])==26 and rootguard['generator_exit_code']==0
plans={r['path']:r for r in plan['files']};guardinputs={r['target'].removeprefix('mod_li_yu_dao/'):r for r in rootguard['inputs']}
original_authored=[];planned_payload_refs={}
for row in plan['files']:
    rel=row['path'];payload=APP/'delta-current-files/mod_li_yu_dao'/rel
    planned=exact(payload,row['after_bytes'],row['after_sha256'])
    idx=app_payload[payload.relative_to(APP).as_posix()]
    assert idx['bytes']==planned['bytes'] and idx['sha256']==planned['sha256']
    original=C3/'delta-final002-files/mod_li_yu_dao'/rel
    assert payload.read_bytes()==original.read_bytes()
    planned_payload_refs[rel]=planned
    if row['kind']=='generated':
        assert BEFORE[rel]['file']['bytes']==row['before_bytes'] and BEFORE[rel]['file']['sha256']==row['before_sha256']
        if rel in guardinputs:
            assert guardinputs[rel]['before_sha256']==row['after_sha256']
            assert AFTER[rel]['file']['sha256']==guardinputs[rel]['after_sha256']
        else:assert AFTER[rel]['file']['sha256']==row['after_sha256']
    elif not Path(rel).name.startswith('test_'):
        current=ref(M/rel)
        expected=guardinputs[rel]['after_sha256'] if rel in guardinputs else row['after_sha256']
        assert current['sha256']==expected,rel
        if rel in guardinputs:assert guardinputs[rel]['before_sha256']==row['after_sha256']
        original_authored.append({'path':rel,'initial_root26':planned,'current':current,'guard_successor':guardinputs.get(rel)})
for rel,row in guardinputs.items():
    src=Path(row['source']);exact(src,row['after_bytes'],row['after_sha256'])
    assert ref(M/rel)['sha256']==row['after_sha256'],rel
assert set(rootguard['changed_runtime'])=={'mod_li_yu_dao/common/scripted_triggers/lyd_c3_leadership_triggers.txt','mod_li_yu_dao/common/scripted_triggers/lyd_i3b_institution_triggers.txt'}
for full,digest in rootguard['after_runtime'].items():
    rel=full.removeprefix('mod_li_yu_dao/');assert AFTER[rel]['file']['sha256']==digest
for row in root26['retained_c2']:
    rel=row['path'].removeprefix('mod_li_yu_dao/');assert ref(M/rel)['sha256']==row['sha256'],rel
c2delta_path=C2/'DELTA.json';c2ref=bind(c2delta_path,'fe2c2321f2e967767f5e27c2a22654883238274a5a6390be446d06fde38e5a03')
c2delta=json.loads(c2delta_path.read_bytes());c2rows={r['path']:r for r in c2delta['complete_runtime_relative_to_frozen_544']}
assert len(c2rows)==4
c2idx=json.loads((C2/'INDEX.json').read_bytes())
for rel,row in c2rows.items():
    assert BEFORE[rel]['file']['bytes']==row['before']['bytes'] and BEFORE[rel]['file']['sha256']==row['before']['sha256']
    assert AFTER[rel]['file']['bytes']==row['after']['bytes'] and AFTER[rel]['file']['sha256']==row['after']['sha256']
    exact(Path(row['frozen_before_ref']),row['before']['bytes'],row['before']['sha256'])
    path=Path(row['after_ref']);value=exact(path,row['after']['bytes'],row['after']['sha256'])
    assert c2idx[path.relative_to(C2).as_posix()]=={'bytes':value['bytes'],'sha256':value['sha256']}
c2authored=[]
for row in c2delta['scope_relative_to_ready_candidate']['authored']:
    if not Path(row['path']).name.startswith('test_'):
        src=Path(row['after_ref']);exact(src,row['after']['bytes'],row['after']['sha256'])
        current=ref(M/row['path']);assert current['sha256']==row['after']['sha256']
        c2authored.append({'path':row['path'],'source':ref(src),'current':current,'basis':'C2 complete candidate003 production author'})
C3REVIEW=B/'lyd-c3-native-primitives-independent-review-20261005-001/variant002-source-review-003'
c3reviewpath=C3REVIEW/'REPORT.json';c3review=json.loads(c3reviewpath.read_bytes())
c3reviewref=bind(c3reviewpath,'7b867ae81dd29135df7c79e63375b6f9fac0031d65e3eba5cdd2a1f1ec31d3c0')
c3_runtime_refs=[]
for row in c3review['runtime_projection']:
    rel=row['path'];src=C3REVIEW/'runtime'/rel
    exact(src,row['bytes'],row['sha256'])
    if rel in guardinputs:assert row['sha256']==guardinputs[rel]['before_sha256']
    else:assert row['sha256']==AFTER[rel]['file']['sha256'],rel
    c3_runtime_refs.append({'path':rel,'reviewed_file':ref(src),'later_guard':guardinputs.get(rel)})
I3REVIEW=B/'lyd-i3b-detached-authority-source-review-20261005-001/review-package-002'
i3idxref=bind(I3REVIEW/'INDEX.json','33ed711277972b83c6f3bfbcf9e005a09827ff461fab7954b4d0a300bb305af7')
i3idx=json.loads((I3REVIEW/'INDEX.json').read_bytes())
for row in i3idx['files']:exact(I3REVIEW/row['path'],row['bytes'],row['sha256'])
i3reviewref=bind(I3REVIEW/'REPORT.json');i3review=json.loads((I3REVIEW/'REPORT.json').read_bytes())
for rel in ['common/scripted_triggers/lyd_i3b_institution_triggers.txt','common/scripted_effects/lyd_i3b_setup_effects.txt',
            'common/scripted_effects/lyd_i3b_response_effects.txt','common/scripted_effects/lyd_i3b_commit_effects.txt','events/lyd_i3b_institution_events.txt','tools/gen_institution.py']:
    assert ref(I3REVIEW/'source'/rel)['sha256']==plans[rel]['after_sha256'],rel
previewpath=B/'root-c3-guards-final-l0-20261005-001/policy/preview.json';preview=json.loads(previewpath.read_bytes())
previewref=bind(previewpath)
assert preview['result']=='PASS_SOURCE_ONLY' and len(preview['cases'])==50 and len(preview['guard_removal_mutants'])==19
assert all(row['accepted']==row['expected'] and row['undefined_reads']==0 for row in preview['cases'])
assert all(row['without_guards']=='UndefinedRead' for row in preview['guard_removal_mutants'])
guardindex=json.loads((GUARD/'INDEX.json').read_bytes())
assert guardindex['cases']==50 and guardindex['mutants']==19 and handoff['cases']==50 and handoff['guard_removal_mutants']==19
root_global_ref=bind(B/'root-c3-guards-final-l0-20261005-001/RESULT.json')
root_global=json.loads((B/'root-c3-guards-final-l0-20261005-001/RESULT.json').read_bytes())
assert root_global['status']=='SOURCE_L0_RED'
bind(APP/'COMPOSITION-CHECK.json');bind(C2/'REPORT.json')
lineage=[];approval=[]
for row in SNAP['runtime_delta']:
    rel=row['path'];steps=[]
    if rel in c2rows:
        source=c2rows[rel]
        steps=[{'stage':'C2 candidate003 complete four-path delta from actual544','author_index':index_refs['C2'],'author_delta':c2ref,
                'frozen_original':ref(Path(source['frozen_before_ref'])),'source_output':ref(Path(source['after_ref'])),
                'ROOT_actual_retention_after_application':root26ref}]
        category='C2'
    else:
        assert rel in plans and plans[rel]['kind']=='generated'
        steps=[{'stage':'C3/I3b exact 26-target application','author_index':index_refs['C3_I3b'],
                'current_applicability_index':index_refs['current_applicability'],'ROOT_application':root26ref,'initial_output':planned_payload_refs[rel],
                'independent_review':c3reviewref if 'lyd_c3_' in rel else i3reviewref}]
        category='C3' if 'lyd_c3_' in rel else 'I3b'
        if rel in guardinputs:
            steps.append({'stage':'Optional-target guard successor','author_index':index_refs['guards'],'handoff':handoffref,
                         'ROOT_application':rootguardref,'before_sha256':guardinputs[rel]['before_sha256'],'after_source':ref(Path(guardinputs[rel]['source'])),
                         'independent_actual_guard50_and_mutants19_receipt':previewref})
    lineage.append({'path':rel,'category':category,'before':row['before'],'after':row['after'],'complete_diff':row['diff'],'source_chain':steps})
    approval.append({'path':rel,'before':{'path':rel,'size':row['before']['bytes'],'sha256':row['before']['sha256']},
                     'after':{'path':rel,'size':row['after']['bytes'],'sha256':row['after']['sha256']}})
assert len(lineage)==18 and sum(r['category']=='C2' for r in lineage)==4
for row in AFTER.values():assert ref(M/row['path'])['sha256']==row['file']['sha256']
result={'schema':'lyd.r10.complete-runtime-source-lineage.v1','status':'SOURCE_ONLY_LINEAGE_EXACT',
 'runtime_delta':approval,'runtime_delta_refs':lineage,'runtime70_snapshot':ref(O/'snapshot-001/RUNTIME-SNAPSHOT.json'),
 'all18_source_chains_complete':True,'C2_count':4,'C3_I3b_initial_generated_count':14,'guard_generated_successors':2,
 'ROOT26_authored12_generated14':root26ref,'ROOTguard_authored3_generated2':rootguardref,
 'production_authored_current_exact_bound':original_authored+c2authored,
 'C3_independent_source_review':c3reviewref,'C3_reviewed_outputs_actual_refs':c3_runtime_refs,
 'I3b_independent_source_review_INDEX':i3idxref,'I3b_independent_source_review_REPORT':i3reviewref,
 'guard50_and19_actual_receipt':previewref,'guard50_and19_not_rerun':True,
 'ROOT_guard_after_runtime_covered_count':len(rootguard['after_runtime']),
 'ROOT_guard_suite_original_global_RED':root_global_ref,
 'ROOT_guard_suite_scope':'The original overall RESULT stays SOURCE_L0_RED while two historical tests are being adapted. Preview50/19 and product/static each pass independently; no overall GREEN invented.',
 'test_only_authored_followups':'Original root26/guard test inputs retained as provenance. Two current tests may be adapted; no runtime change and no old tests run here.',
 'full_source_review_scope':'mod_li_yu_dao production70 plus exact production-author source chains; not ROOT entire native/Python/full-export source review.',
 'final_Git_export':None,'native':'NOT_RUN','tests_executed':0,'main_mutations':0,'Git_calls':0}
save(P/'COMPLETE-RUNTIME-LINEAGE.json',result)
save(P/'APPROVED-RUNTIME-DELTA-18.json',approval)
print(json.dumps({'status':result['status'],'runtime_delta_count':len(lineage),'C2':4,'C3_I3b':14,'later_guard2':True,
                 'production_author_files_bound':len(original_authored+c2authored),'lineage':ref(P/'COMPLETE-RUNTIME-LINEAGE.json'),
                 'runtime_approval_exact_manifest_row_schema':ref(P/'APPROVED-RUNTIME-DELTA-18.json'),
                 'ROOT_global_RED_preserved':True},ensure_ascii=False))
