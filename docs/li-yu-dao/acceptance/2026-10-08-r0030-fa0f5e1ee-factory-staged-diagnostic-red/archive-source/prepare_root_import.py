"""Create one ROOT import map from actual verified archive JSON; no ZIP/body recheck."""
from pathlib import Path
import hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');A=B/'r30-permanent-archive-candidate-20261008-001';F=B/'r30-permanent-archive-frozen-source-20261008-001';D=B/'r30-final-report-sourceonly-20261008-001'
R=B/'live-attempt-030';S=B/'r30-permanent-archive-plan-sourceonly-20261008-002';O=B/'r30-permanent-archive-import-ready-20261008-001'
T='docs/li-yu-dao/acceptance/2026-10-08-r0030-fa0f5e1ee-factory-staged-diagnostic-red';HEAD='fa0f5e1ee098ab6fab4635bedce939eab857610a'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p).resolve()
 if p.suffix.lower()in ['.ck3','.exe','.dll','.lib','.obj','.pdb','.tar','.bin','.zip','.png']:raise ValueError('archive ZIP/body/binary refs inherited; not reread')
 v=p.read_bytes();return {'path':p.as_posix(),'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
def put(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
if O.exists():raise FileExistsError(O)
original=B/'r30-root-permanent-archive-original-exec-20261008-001/RESULT.actual.json'
if pin(original)['sha256']!='6e96d88c2dceb3e8c7f7fe10f2e7731915df6ec23cfe040cf53dd0fb45e62e90' or read(original).get('exit_code')!=0:raise ValueError('exact ROOT original once-only archive execution0 required')
result=read(A/'RESULT.actual.json');validation=read(A/'ARCHIVE-VALIDATION.actual.json');index=read(A/'INDEX.json');combined=read(A/'COMBINED-IMPORT-MANIFEST.source-only.json');facts=read(D/'FACTS.final.actual.json')
if result['status']!='R30_EXTERNAL_ARCHIVE_CREATED_ONLY' or result['runtime_closed']is not True or validation['all_original_bytes_sha_match']is not True:raise ValueError('ROOT actual archive and inherited ZIP entry verification required')
if index['source_head']!=HEAD or index['whole_mod']!='NOT_GREEN' or combined['source_head']!=HEAD:raise ValueError('exact FA0/NOT_GREEN archive binding differs')
files=[dict(x)for x in combined['files']]
if any(not x['target_relative'].startswith(T+'/')for x in files):raise ValueError('permanent target differs')
def copy(p,rel):files.append(pin(p)|{'target_relative':T+'/'+rel})
O.mkdir()
copy(D/'FACTS.final.actual.json','FACTS.actual.json')
copy(R/'ROOT-D0-SIGNED-COMPARISON-INPUTS-001/D0-comparison-001/RESULT.actual.json','diagnostic/D0-CONTROL.actual.json')
copy(R/'ROOT-D0-CACHE-INPUTS-001/cache-comparison-001/RESULT.actual.json','diagnostic/D0-NATIVE-SAVED-CACHE.actual.json')
for row in facts['stages']:
 stage=row['stage'];p=O/(stage+'-SUMMARY.actual.json');put(p,row);copy(p,'diagnostic/'+p.name)
 if stage!='D0':copy(R/(stage+'-comparison-001')/'RESULT.actual.json','diagnostic/'+stage+'-COMPARISON.actual.json')
for name in ['D6-TERMINAL-STATE.observed.json','D6-TERMINAL-TYPED-PROTECTION.observed.json']:
 copy(R/'D6-diagnostic-author-001'/name,'diagnostic/'+name)
for name in ['RESULT.actual.json','IMPORT-MANIFEST.source-only.json','COMBINED-IMPORT-MANIFEST.source-only.json']:
 copy(A/name,'evidence/'+name)
for name in ['author_r30_archive.py','COLLECTOR-LABEL-ONLY.diff','COLLECTOR-PROJECTION.actual.json','INDEX.json','ROOT-CREATE-ARGV.actual.json']:
 copy(F/name,'archive-source/frozen/'+name)
for name in ['prepare_closed_r30_archive.py','SOURCE-PROJECTION.actual.json','EXPLICIT-REF3-ONLY.diff','INDEX.json']:
 copy(S/name,'archive-source/constructor/'+name)
for name in ['FREEZE-ARGV.final.actual.json','FREEZE-ORIGINAL-EXEC.actual.json','PACKROOTS.final.closed.actual.json','author_report_and_freeze_inputs.py','finalize_file_only_freeze.py']:
 copy(D/name,'archive-source/report-freeze/'+name)
copy(Path(__file__),'archive-source/prepare_root_import.py')
copy(original,'evidence/ROOT-ARCHIVE-ORIGINAL-EXEC.actual.json')
for name in ['stdout','stderr']:
 p=original.parent/name
 if p.is_file():copy(p,'evidence/ROOT-ARCHIVE-'+name)
copy(B/'r30-root-ci-bom-import-20261008-002/RESULT.actual.json','evidence/ROOT-POSTCLOSE-CI-BOM-IMPORT.actual.json')
copy(B/'r30-root-actual-typed-closed-boundary-20261008-001/PREVIOUS-BOUNDARY.actual.json','evidence/PREVIOUS-BOUNDARY.actual.json')
for action in ['check','create']:
 copy(B/f'r30-root-typed-close-{action}-original-exec-20261008-001/RESULT.actual.json','evidence/ROOT-TYPED-CLOSE-'+action+'-ORIGINAL-EXEC.actual.json')
summary={'schema':'lyd.r30.actual-closed-archive-delivery.v1','source_head':HEAD,'whole_mod':'NOT_GREEN','runtime_closed':True,'original_archive_exec':pin(original),'original_archive_files':result['files'],'unique_original_byte_sets':validation['unique_original_sets'],'all_original_bytes_sha_match_inherited':True,'ZIP':result['ZIP'],'INDEX':result['INDEX'],'REPORT':result['REPORT'],'FACTS':pin(D/'FACTS.final.actual.json'),'diagnostic_body_reads_original_total':facts['diagnostic_unique_author_body_reads'],'extra_body_reads_by_archiver':0,'native_binary_priorZIP_reads_by_importer':0,'D0_diagnostic_control_status':facts['D0_status'],'D2_first_cache_political_delta_before_SAVE':True,'terminal_saved_checks':facts['terminal_STATE_checks'],'terminal_typed_checks':facts['terminal_TYPED_checks'],'formal_mandate_credit':None,'whole_product_pass':None,'C3_credit':None,'I4_credit':None,'cold_new_T_credit':None,'factory_internal_cause_inferred':False,'new_tests_SDK_process_game_MAIN_calls':0}
put(O/'DELIVERY.actual.json',summary);copy(O/'DELIVERY.actual.json','DELIVERY.actual.json')
targets=[x['target_relative']for x in files]
if len(set(targets))!=len(targets):raise ValueError('create-only duplicate targets')
put(O/'ROOT-IMPORT-MANIFEST.source-only.json',{'schema':'lyd.r30.combined-create-only-docs-import-manifest.v1','target_relative':T,'source_head':HEAD,'files':files,'runtime_closed':True,'whole_mod':'NOT_GREEN','original_collector_manifest':pin(A/'COMBINED-IMPORT-MANIFEST.source-only.json'),'ZIP_verification_inherited_from_original_ROOT_once_exec':pin(original),'no_repeat_archive_validation':True,'default_MAIN_apply_authorized':False,'MAIN_writes':0})
put(O/'INDEX.json',{'status':'R30_ACTUAL_CLOSED_PERMANENT_ARCHIVE_READY_FOR_ROOT_CREATE_ONLY_IMPORT','manifest':pin(O/'ROOT-IMPORT-MANIFEST.source-only.json'),'delivery':pin(O/'DELIVERY.actual.json'),'candidate_INDEX':result['INDEX'],'REPORT':result['REPORT'],'ZIP':result['ZIP'],'files':len(files),'runtime_closed':True,'whole_mod':'NOT_GREEN','ZIP_body_binary_tests_SDK_MAIN_actions':0})
print(json.dumps({'INDEX':pin(O/'INDEX.json'),'manifest':pin(O/'ROOT-IMPORT-MANIFEST.source-only.json'),'delivery':pin(O/'DELIVERY.actual.json'),'REPORT':result['REPORT'],'ZIP':result['ZIP'],'targets':len(files)}))
