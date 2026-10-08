"""Create-only review import map; ROOT applies it, this helper never writes MAIN."""
from pathlib import Path
import hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');O=B/'r29-business-permanent-archive-sourceonly-20261008-001';A=B/'r29-business-permanent-archive-candidate-20261008-001'
T='docs/li-yu-dao/acceptance/2026-10-08-r0029-487da05f6-native-cache-factory-protection-red'
def rd(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve()
 if p.suffix.lower()in['.ck3','.exe','.dll','.lib','.tar','.bin','.zip']:raise ValueError('inherit original archive/source refs; do not reread body/binary/ZIP')
 v=p.read_bytes();return {'path':p.as_posix(),'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
result=rd(A/'RESULT.actual.json');validation=rd(A/'ARCHIVE-VALIDATION.actual.json');index=rd(A/'INDEX.json')
if result['status']!='R29_EXTERNAL_ARCHIVE_CREATED_ONLY'or not result['runtime_closed']or validation['all_original_bytes_sha_match']is not True:raise ValueError('actual create/ZIP verification required')
report=(A/'REPORT.md').read_text(encoding='utf-8')
anchor='B3→B4 actor仅succession移除'
if report.count(anchor)!=1:raise ValueError('review wording anchor differs')
report=report.replace(anchor,'B3→B4 actor受保护landed投影仅succession移除',1)
with (O/'REPORT.reviewed.final.md').open('x',encoding='utf-8',newline='\n')as f:f.write(report)
files=[]
for row in rd(A/'COMBINED-IMPORT-MANIFEST.source-only.json')['files']:
 x=dict(row)
 if x['target_relative']==T+'/REPORT.md':x['target_relative']=T+'/evidence/REPORT.collector-original.md'
 files.append(x)
def copy(p,name):files.append(pin(p)|{'target_relative':T+'/'+name})
copy(O/'REPORT.reviewed.final.md','REPORT.md')
copy(O/'FACTS.final.original-derived.json','FACTS.original-derived.json')
for name in ['INDEX.json','FIELD-DIFF.actual.json','SUMMARY.actual.json','classify_retained_json.py']:
 copy(B/'r29-factory-field-diff-actual-20261008-001'/name,'fielddiff/'+name)
for name in ['RESULT.actual.json','IMPORT-MANIFEST.source-only.json','COMBINED-IMPORT-MANIFEST.source-only.json']:
 copy(A/name,'evidence/'+name)
for name in ['COLLECTOR-PROJECTION.actual.json','COLLECTOR-ONLY-RUN-LABEL.diff','CURATION-ADDENDUM.actual.json','ARCHIVE-ORIGINAL-EXEC.actual.json','CREATE-ARGV.sealed.actual.json','REQUEST.sealed.actual.json','prepare_selected_archive.py','finalize_selected_request.py','create_one_archive.py','prepare_root_import.py','author_r29_archive.py']:
 copy(O/name,'archive-source/'+name)
summary={'schema':'lyd.r29.original-evidence-archive-delivery.v1','source_head':'487da05f6c1cf231490fd1fe480ccc704ed0a80f','whole_mod':'NOT_GREEN','runtime_closed':True,'business_acceptance':False,'cause':None,'cause_status':'UNKNOWN','B3_independent_formal_pass':True,'B4_typed_true':82,'B4_typed_total':88,'B4_saved_true':43,'B4_saved_total':48,'cache_B3':{'native':45,'saved':45,'ordered_exact_match':True},'cache_B4':{'native':40,'saved':40,'ordered_exact_match':True},'B5_cold_C3_I4':'NOT_RUN','archive_original_files':result['files'],'unique_original_byte_sets':validation['unique_original_sets'],'archive_bytes':result['ZIP']['bytes'],'archive':result['ZIP'],'INDEX':result['INDEX'],'final_REPORT':pin(O/'REPORT.reviewed.final.md'),'closed_boundary':index['closure_refs'][0],'actual_collector_exit':rd(O/'ARCHIVE-ORIGINAL-EXEC.actual.json')['exit_code'],'source_REPORT_wording_revision':'protected landed actor projection scope made explicit; archived collector report retained unchanged','archive_body_binary_SDK_process_game_MAIN_calls':0}
put(O/'DELIVERY.actual.json',summary);copy(O/'DELIVERY.actual.json','DELIVERY.actual.json')
put(O/'ROOT-IMPORT-MANIFEST.source-only.json',{'schema':'lyd.r29.combined-create-only-docs-import-manifest.v1','target_relative':T,'source_head':summary['source_head'],'files':files,'runtime_closed':True,'whole_mod':'NOT_GREEN','original_collector_manifest':pin(A/'COMBINED-IMPORT-MANIFEST.source-only.json'),'new_archive_ZIP_validation_inherited_from_actual_collector':pin(A/'ARCHIVE-VALIDATION.actual.json'),'default_MAIN_apply_authorized':False,'MAIN_writes':0})
put(O/'SEALED-INDEX.json',{'status':'R29_FINAL_EXTERNAL_ORIGINAL_BYTE_ARCHIVE_READY_FOR_ROOT_IMPORT','delivery':pin(O/'DELIVERY.actual.json'),'final_REPORT':pin(O/'REPORT.reviewed.final.md'),'ROOT_import_manifest':pin(O/'ROOT-IMPORT-MANIFEST.source-only.json'),'candidate_INDEX':result['INDEX'],'candidate_ZIP':result['ZIP'],'original_collector_exec':pin(O/'ARCHIVE-ORIGINAL-EXEC.actual.json'),'fielddiff':pin(B/'r29-factory-field-diff-actual-20261008-001/INDEX.json'),'whole_mod':'NOT_GREEN','runtime_closed':True,'save_body_binary_SDK_game_MAIN_calls':0})
print(json.dumps({'sealed_INDEX':pin(O/'SEALED-INDEX.json'),'ROOT_import_manifest':pin(O/'ROOT-IMPORT-MANIFEST.source-only.json'),'final_REPORT':pin(O/'REPORT.reviewed.final.md'),'ZIP':result['ZIP'],'delivery':pin(O/'DELIVERY.actual.json'),'tracked_targets':len(files)}))
