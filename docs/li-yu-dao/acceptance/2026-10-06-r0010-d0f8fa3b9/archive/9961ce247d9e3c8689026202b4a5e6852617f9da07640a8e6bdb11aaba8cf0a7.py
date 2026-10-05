from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
O=Path(__file__).resolve().parent;B=Path('C:/workspace/ck3_lyd_runtime_20261004');E=B/'r10-root-head-export-20261005-001'
SRC=Path('C:/lr10s1/mod_li_yu_dao');HEAD='d0f8fa3b9d444828759443aa018bfd7ad31b398d'
P=O/'review-package-001';P.mkdir(exist_ok=False)
def sha(d):return hashlib.sha256(d).hexdigest()
def ref(p):
    d=p.read_bytes();return {'path':str(p),'bytes':len(d),'sha256':sha(d)}
def save(rel,v):
    p=P/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False);f.write('\n')
def copy(src,rel):
    p=P/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(src.read_bytes())
    assert p.read_bytes()==src.read_bytes()
report_ref=ref(E/'REPORT.json');assert report_ref['sha256']=='f2b0f6d91a565648ecdb0be8c3aec1d88b67c468bc8a5623aba347f58ee7b0e4'
export=json.loads((E/'REPORT.json').read_bytes());assert export['source']['head']==HEAD and export['source_root']=='C:/lr10s1'
manifest_path=Path(export['build']['manifest']['path']);manifest_ref=ref(manifest_path)
assert manifest_ref['sha256']=='8fff14a823c50d2461660676ec3238439027d1a46af5281e5db95af7c9bd945c'
manifest=json.loads(manifest_path.read_bytes());assert manifest['git_sha']==HEAD and len(manifest['files'])==70
manifest_rows={r['path']:r for r in manifest['files']}
snap=json.loads((O/'snapshot-001/RUNTIME-SNAPSHOT.json').read_bytes())
lineage=json.loads((O/'lineage-002/COMPLETE-RUNTIME-LINEAGE.json').read_bytes())
authors=json.loads((O/'production-author-inputs-001/FULL-MOD-PRODUCTION-SOURCE-REVIEW.json').read_bytes())
assert len(snap['before_rows'])==len(snap['after_rows'])==len(manifest_rows)==70
inventory_path=Path(export['source']['inventory']['path']);inventory_ref=ref(inventory_path)
assert inventory_ref==export['source']['inventory']
inventory=json.loads(inventory_path.read_bytes());assert inventory['source_revision']==HEAD
inventory_rows={r['path']:r for r in inventory['files']};assert len(inventory_rows)==147
stage=Path(export['build']['staging']);export_runtime=[]
for row in snap['after_rows']:
    rel=row['path'];expected=Path(row['file']['path']).read_bytes();source=(SRC/rel).read_bytes();staging=(stage/rel).read_bytes()
    assert expected==source==staging,rel
    inv=inventory_rows[rel];man=manifest_rows[rel]
    assert inv=={'path':rel,'bytes':len(expected),'sha256':sha(expected)}
    assert man=={'path':rel,'size':len(expected),'sha256':sha(expected)}
    export_runtime.append({'path':rel,'reviewed_snapshot':row['file'],'final_export':ref(SRC/rel),'formal_staging':ref(stage/rel)})
export_authors=[]
for row in authors['all_rows']:
    rel=row['path'];expected=Path(row['after']['path']).read_bytes();actual=(SRC/rel).read_bytes()
    assert expected==actual and inventory_rows[rel]=={'path':rel,'bytes':len(expected),'sha256':sha(expected)},rel
    export_authors.append({'path':rel,'reviewed_snapshot':row['after'],'final_export':ref(SRC/rel)})
old=json.loads(Path(snap['R9_manifest']['path']).read_bytes())
before={r['path']:r for r in old['files']}
actual_delta=[{'path':p,'before':before[p],'after':manifest_rows[p]} for p in sorted(before) if before[p]!=manifest_rows[p]]
assert actual_delta==lineage['runtime_delta'] and len(actual_delta)==18
assert len(export_authors)==42
final_test_root=B/'root-c3-failed-tests-final-l0-20261005-001'
final_test_result=json.loads((final_test_root/'RESULT.json').read_bytes())
assert final_test_result['status']=='SOURCE_L0_PASS'
for label in ['01','02']:
    r=json.loads((final_test_root/'fixed-tests'/(label+'-result.json')).read_bytes());assert r['exit_code']==0
detached=json.loads((final_test_root/'fixed-tests/detached.json').read_bytes())
assert detached['status']=='SOURCE_L0_PASS' and detached['runtime_sha256']==manifest_rows['common/scripted_triggers/lyd_i3b_institution_triggers.txt']['sha256']
binding={'schema':'lyd.r10.independent-final-export-byte-binding.v1','status':'SOURCE_ONLY_REVIEWED','source_head':HEAD,
 'actual_ROOT_export_report':report_ref,'actual_product_inventory':inventory_ref,'actual_production_manifest':manifest_ref,
 'source_inventory_reported_mod_count':147,'reviewed_production_runtime_count':70,'reviewed_non_test_source_input_count':42,
 'all70_runtime_source_and_stage_equal_prior_reviewed_snapshot':True,'all42_non_test_author_sources_equal_prior_reviewed_snapshot':True,
 'no_runtime_or_author_logic_change_since_independent_snapshot':True,'runtime_rows':export_runtime,'non_test_author_rows':export_authors,
 'actual_runtime_delta_from_final_manifest':actual_delta,'unchanged_runtime_count':52,'added_runtime_paths':[],'removed_runtime_paths':[],
 'ROOT_final_test_correction_receipt':ref(final_test_root/'RESULT.json'),'ROOT_final_detached_policy_receipt':ref(final_test_root/'fixed-tests/detached.json'),
 'test_receipts_only_not_rerun':True,'all_other_export_source_count6066_scope':'ROOT/observer separate review; not independently hashed all6066 here.',
 'native_Release_and_engine_acceptance':'NOT_RUN_BY_THIS_REVIEW','game_pipe_claim_Git_main_write_operations':0}
save('FINAL-EXPORT-READBACK.json',binding)
save('APPROVED-RUNTIME-DELTA-18.json',actual_delta)
full_source={'schema':'lyd.r10.independent-mod-production-source-review.v1','status':'SOURCE_ONLY_REVIEWED','source_head':HEAD,
 'scope':'mod_li_yu_dao production70 and all42 non-test tools inputs; complete changed author set12 and runtime delta18. ROOT full6066 export/native/Python source and mod test/docs/fixtures outside this scope are separately reviewed.',
 'reviewed_total_files':112,'complete_non_test_author_source_before_after':authors,'complete_runtime_source_lineage':lineage,
 'actual_final_export_binding':ref(P/'FINAL-EXPORT-READBACK.json'),'native':'NOT_RUN','tests_executed':0,'main_mutations':0,'Git_calls':0}
save('FULL-SOURCE-REVIEW.json',full_source)
review={'schema':'lyd.r10.independent-runtime-and-source-review.v1','status':'SOURCE_ONLY_REVIEWED','source_head':HEAD,
 'sealed_utc':datetime.now(timezone.utc).isoformat(),'actual_final_export_binding':ref(P/'FINAL-EXPORT-READBACK.json'),
 'full_source_review':ref(P/'FULL-SOURCE-REVIEW.json'),
 'scope':'Complete production70 runtime comparison to actual R9 clean544 export plus all production-author chains. No native/game acceptance. Full ROOT6066 source review is separate.',
 'before_rows':snap['before_rows'],'after_rows':export_runtime,'runtime_delta':actual_delta,'runtime_delta_refs':lineage['runtime_delta_refs'],
 'runtime_counts':{'before':70,'after':70,'changed':18,'unchanged':52,'added':0,'removed':0},
 'runtime_change_origin_counts':{'C2':4,'C3_I3b_initial14':14,'guard_successors_within_the14':2},
 'source_lineage':ref(O/'lineage-002/COMPLETE-RUNTIME-LINEAGE.json'),'production_author_closure':ref(O/'production-author-inputs-001/FULL-MOD-PRODUCTION-SOURCE-REVIEW.json'),
 'verified_production_author_inputs':42,'production_author_changes':12,'C2_author_raw_exception':'Exactly392 CRLF lines to LF in consent trigger template; entire normalized bytes equal and all generated runtime bytes raw exact.',
 'ROOT26_actual_apply':lineage['ROOT26_authored12_generated14'],'ROOTguard_actual_apply':lineage['ROOTguard_authored3_generated2'],
 'C3_independent_source_review':lineage['C3_independent_source_review'],'I3b_independent_source_review':lineage['I3b_independent_source_review_REPORT'],
 'actual_guard50_and19_report':lineage['guard50_and19_actual_receipt'],'guard_execution_scope':'Previously executed bounded AST test doubles. 50 outcomes and19 undefined-read guard-removal mutants inspected; not reexecuted and not CK3 field evaluation.',
 'original_ROOT_global_RED_retained':lineage['ROOT_guard_suite_original_global_RED'],'actual_later_ROOT_corrected_test_receipt':ref(final_test_root/'RESULT.json'),
 'corrected_test_observation':'Read actual final PASS/exit0 receipts and detached source SHA bound to final trigger. No old tests rerun. Earlier overallRED remains unchanged.',
 'reviewer_failure_preserved':{'path':str(O/'verify_complete_runtime_lineage.py'),'reason':'Original lineage001 raw-exact assertion rejected C2 CRLF/LF author template. lineage002 verifies ONLY exact392-line normalization; current runtime remains raw-exact.'},
 'final_production_manifest':manifest_ref,'final_ROOT_export_report':report_ref,
 'no_runtime_logic_change_after_review':True,'native':'NOT_RUN','native_save_reload':'NOT_RUN','native_C3_I3b_positive':'NOT_RUN',
 'tests_executed':0,'main_mutations':0,'Git_calls':0,'game_calls':0,'pipe_calls':0,'claim_operations':0,
 'business_or_MCP_exit_PASS':False}
save('REPORT.json',review)
md='''Complete R10 mod production SOURCE_ONLY review passes for d0f8fa3b9d444828759443aa018bfd7ad31b398d.

All 70 final exported runtime files and formal staging bytes equal the independently reviewed snapshot. Relative to actual R9 clean544 export, exactly18 paths changed and52 did not; no paths were added or removed. The full delta comprises C2 four paths plus C3/I3b fourteen, including two later guard successors.

Every changed path binds its exact R9 before bytes, author output, ROOT26 application and applicable guard successor. C3 and I3b independent source reviews, actual guard50/19 and ROOT static70 receipts are retained. All42 non-test tool inputs also match the final export; their complete12 changed authors map to the same sources. The C2 trigger template differs from its author candidate only by392 CRLF lines normalized to LF, with no generated runtime byte difference.

Original ROOT suiteRED and author/reviewer failures remain preserved. The later ROOT corrected test receipts pass and bind the final I3b trigger, but no tests were rerun here. This review covers112 mod production/input files; ROOT6066 source, native/Python and remaining mod documentation/fixtures/tests are separate scopes.

Release compilation, actual native C3/I3b operation, save reload and business/MCP acceptance are not established by this source-only review.
'''
with (P/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(md)
for folder in ['snapshot-001','production-author-inputs-001','lineage-002']:
    root=O/folder
    for path in sorted(root.rglob('*')):
        if path.is_file():copy(path,'evidence/'+folder+'/'+path.relative_to(root).as_posix())
copy(E/'REPORT.json','evidence/final-export/REPORT.json');copy(manifest_path,'evidence/final-export/mod_li_yu_dao.manifest.json')
copy(inventory_path,'evidence/final-export/MOD-SOURCE-INVENTORY.json')
for path in sorted(final_test_root.rglob('*')):
    if path.is_file():copy(path,'evidence/ROOT-later-corrected-tests/'+path.relative_to(final_test_root).as_posix())
for name in ['discover_current_runtime_inputs.py','read_provenance_inputs.py','read_provenance_schema.py','read_review_reports_compact.py','read_index_links.py',
 'read_source007_delta_contract.py','read_runtime_row_schema.py','inspect_lineage_shapes.py','inspect_runtime_logic_diff.py','inspect_c2_author_newlines.py',
 'snapshot_all70_runtime.py','verify_complete_runtime_lineage.py','verify_complete_runtime_lineage_v2.py','review_production_author_closure.py',
 'read_actual_export_metadata.py','seal_final_export_runtime_review.py']:
    copy(O/name,'reviewer/'+name)
rows=[]
for path in sorted(P.rglob('*')):
    if path.is_file():
        d=path.read_bytes();rows.append({'path':path.relative_to(P).as_posix(),'bytes':len(d),'sha256':sha(d)})
save('INDEX.json',{'schema':'lyd.r10.independent-source-review-index.v1','root':str(P),'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'files':rows})
for row in rows:
    d=(P/row['path']).read_bytes();assert len(d)==row['bytes'] and sha(d)==row['sha256']
receipt={'status':'SOURCE_ONLY_REVIEWED','HEAD':HEAD,'INDEX':ref(P/'INDEX.json'),'independent_runtime_review':ref(P/'REPORT.json'),
 'full_source_review':ref(P/'FULL-SOURCE-REVIEW.json'),'runtime_delta':ref(P/'APPROVED-RUNTIME-DELTA-18.json'),
 'final_export_binding':ref(P/'FINAL-EXPORT-READBACK.json'),'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),
 'runtime70_final_export_exact':True,'runtime_delta_count':18,'author42_final_export_exact':True,'native':'NOT_RUN'}
with (O/'FINAL-SEALED-RECEIPT.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt),flush=True)
