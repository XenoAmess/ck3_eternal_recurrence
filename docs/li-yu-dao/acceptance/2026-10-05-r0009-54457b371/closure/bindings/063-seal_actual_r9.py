"""External-only runner; requires actual ROOT gate evidence and final whole-log.

It normalizes the actual closure schema without modifying original bytes, then
runs the frozen v2 writer. No process probe, native/game/Git/CI or main write.
"""
from datetime import datetime,timezone
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve();RUN=ROOT/'live-attempt-009'
PREP=Path(__file__).resolve().parent
TOOLKIT=ROOT/'r9-failure-report-preparation-20261005-001'
SOURCE='54457b371e947edb86903c2ebd578034f02695db'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ext(p):
 p=p.resolve()
 if ROOT not in p.parents:raise ValueError('External ROOT boundary')
 return p
def bind(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def fresh(p,raw):
 with p.open('xb') as f:f.write(raw)
def js(p,o):fresh(p,(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--gate-evidence',type=Path,required=True)
ap.add_argument('--gate-sha256',required=True)
ap.add_argument('--whole-root',type=Path,required=True)
ap.add_argument('--whole-report',type=Path,required=True)
ap.add_argument('--whole-report-sha256',required=True)
ap.add_argument('--whole-index',type=Path,required=True)
ap.add_argument('--whole-index-sha256',required=True)
ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args()
gate_path=ext(args.gate_evidence);whole_root=ext(args.whole_root)
whole_report=ext(args.whole_report);whole_index=ext(args.whole_index)
out=ext(args.output)
if out.exists():raise FileExistsError('New seal attempt required')
if sha(TOOLKIT/'TOOLS-INDEX.json')!='f0f79b3089ab89d0cfa1a7073eb629223d599122d8058a23047adda51cde0f15':raise ValueError('Frozen v2 toolkit drift')
if sha(TOOLKIT/'prepare_r9_report_v2.py')!='20d3aefb1a22c542112c1e7478a8cba90b5ede02df6aca8801edb46558d226df':raise ValueError('Frozen writer drift')
for p,digest in [(gate_path,args.gate_sha256),(whole_report,args.whole_report_sha256),(whole_index,args.whole_index_sha256)]:
 if sha(p)!=digest:raise ValueError('Actual final input SHA drift: '+str(p))
whole=read(whole_report);whole_manifest=read(whole_index)
if whole.get('capture_result')!='PASS_STABLE_COMPLETE_FILES' or whole.get('captured_log_count')!=16 or whole.get('source_directory_inventory_unchanged') is not True:raise ValueError('Actual stable final whole-log capture not established')
indexed_paths=set()
for rel,row in whole_manifest.items():
 p=ext(whole_root/rel)
 if whole_root not in p.parents or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('Changed actual whole-log indexed file')
 indexed_paths.add(p)
if {p.resolve() for p in whole_root.rglob('*') if p.is_file()}!=indexed_paths|{whole_index}:raise ValueError('Unindexed whole-log file')
gate=read(gate_path)
if gate.get('source_revision',gate.get('source_head',gate.get('frozen_head')))!=SOURCE:raise ValueError('Wrong gate source')
if gate.get('source_freeze_released') is not True:raise ValueError('Actual ROOT policy source gate unresolved')
gate_bindings=[gate['actual_closure'],gate['process_absence']]
for row in gate_bindings:
 p=ext(Path(row['path']))
 if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('Changed ROOT release linked evidence')
census=read(ext(Path(gate['process_absence']['path'])))
if census.get('all_ck3_processes_absent') is not True or census.get('ck3_processes')!=[] or census.get('original_pid_matches')!=[] or census.get('opened_individual_process_handles')!=0:raise ValueError('Actual OS census absence unresolved')
if gate.get('screen_release_sequence')!=2981 or gate.get('screen_release_state')!='waiting' or gate.get('screen_release_business_status')!='unresolved_red':raise ValueError('Root release/task facts changed')
original=RUN/'root-closure-release-002/CLOSURE.json'
if sha(original)!='8abaf2c9ac75ce6e004d4d80a80554beda410cd0d14766703d37625997d55714':raise ValueError('Original closure drift')
c=read(original);terminal_notes=read(PREP/'ACTUAL-TERMINAL-BUSINESS-NOTES.json')
if c['exit_code']!=0 or c['typed_normal_exit_observed'] is not True:raise ValueError('Actual normal terminal not verified')
if c['screen_release']['task']['resources']!=[] or c['screen_release']['task']['last_sequence']!=2981:raise ValueError('Actual CAS release unresolved')
bindings={}
for row in terminal_notes['bindings']+gate_bindings:
 p=ext(Path(row['path']));b=bind(p)
 if b['bytes']!=row['bytes'] or b['sha256']!=row['sha256']:raise ValueError('Actual bound terminal bytes changed')
 bindings[str(p).casefold()]=b
for p in [original,gate_path,whole_report,whole_index,PREP/'ACTUAL-TERMINAL-BUSINESS-NOTES.json',PREP/'R9-ACTUAL-RESULTS-ZH.md',Path(__file__).resolve()]:bindings[str(p).casefold()]=bind(p)
final_zh=PREP/'R9-FINAL-ROOT-REVIEW-ZH.md'
primary=whole['primary_error_log'];cats=primary['category_counts']
zh=(PREP/'R9-ACTUAL-RESULTS-ZH.md').read_text(encoding='utf-8')
zh=zh[:zh.index('本说明编写时最终 whole-log')]
zh+='最终 whole-log 已实际完成并逐件复核 INDEX bytes/SHA：16 文件两次完整读取稳定，结果 '+whole['result']+'。primary error.log '+str(primary['bytes'])+'字节，SHA '+primary['sha256']+'；100000E中578 fixture、99422产品错误，含1 native dynamic-localization。debug/game镜像不重计；日志上限未证，后段零增长不授通过信用。ROOT OS census实际ck3_processes[]、original_pid_matches[]，未重新打开个别进程HANDLE；ROOT policy note实际解除source-freeze逻辑政策门禁，没有单独物理source-lock字段，原冻结输入记录仍保留。原闭合/失败/准备包不修改。大原存档永久外置，最终封存仅作无损证据保存，整体NOT_GREEN，JOIN2/fullcycle NOT_RUN。\n'
fresh(final_zh,zh.encode('utf-8'));bindings[str(final_zh).casefold()]=bind(final_zh)
# Explicit native reader failure/review branches stay intact; toy and real .ck3
# originals remain external. Every included file gets an exact hash binding.
reader_root=ROOT/'r9-native-save-receipt-reader-20261005-001'
for p in sorted(reader_root.rglob('*')):
 if p.is_file() and p.suffix.lower()!='.ck3':bindings[str(p.resolve()).casefold()]=bind(p)
actual_whole_files=[]
for p in sorted(whole_root.rglob('*')):
 if not p.is_file():continue
 row=bind(p);actual_whole_files.append(row)
 if p.suffix.lower()!='.ck3':bindings[str(p.resolve()).casefold()]=row
normalized=PREP/'CLOSURE-NORMALIZED.actual.json'
norm=dict(c)
norm.update(schema='lyd.r9.actual-closure-schema-view.v1',run='R0009',source_revision=SOURCE,process_absence=True,lease_released=True,source_freeze_released=True,bindings=list(bindings.values()),overall_native_acceptance='NOT_GREEN_FULL_CYCLE_INCOMPLETE_AND_FAILURES_RETAINED',normalization={'writer':str(Path(__file__).resolve()),'original_closure':bind(original),'runtime_gate_evidence':bind(gate_path),'original_terminal_bytes_modified':False,'overall_status_basis':'Actual native FACTS full_cycle_credit=false; SDK failures retained; actual task retirement unresolved_red. Derived overall archival classification, not falsely attributed to a field in original closure.','source_freeze_and_absence_basis':'Exact ROOT actual policy note and OS census above; this is logical policy release, no fictitious physical lock field; no new process query by report writer'},final_whole_log={'report':bind(whole_report),'index':bind(whole_index),'raw_files':actual_whole_files,'whole_report_result':whole['result'],'whole_capture_result':whole['capture_result'],'primary_error':primary,'log_cap':whole['log_cap'],'whole_report_interpretation':'Exact actual report preserved; no automatic GREEN/cap/callback inference by runner'})
js(normalized,norm)
argv=[sys.executable,str(TOOLKIT/'prepare_r9_report_v2.py'),'--seal','--closure',str(normalized),'--closure-sha256',sha(normalized),'--output',str(out),'--context-evidence',str(ROOT/'r9-report-preparation-20261005-001/ACTUAL-FIRST-JOIN-NOTES.json'),'--context-evidence',str(TOOLKIT/'ACTUAL-FAILURE-PREPARATION-NOTES.json'),'--context-evidence',str(PREP/'ACTUAL-TERMINAL-BUSINESS-NOTES.json'),'--context-evidence',str(PREP/'R9-ACTUAL-RESULTS-ZH.md'),'--context-evidence',str(ROOT/'r9-c2-readback-20261005-001/facts-through-0058-native-002/FACTS.json'),'--context-evidence',str(whole_report),'--context-evidence',str(final_zh),'--sdk-include','0064-','--sdk-include','0065-']
js(PREP/'SEAL-ARGV.json',{'argv':argv,'normalized_closure':bind(normalized),'no_main_import':True})
r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
fresh(PREP/'seal.stdout.log',r.stdout);fresh(PREP/'seal.stderr.log',r.stderr)
js(PREP/'SEAL-RESULT.json',{'utc':datetime.now(timezone.utc).isoformat(),'exit_code':r.returncode,'stdout':bind(PREP/'seal.stdout.log'),'stderr':bind(PREP/'seal.stderr.log'),'main_import':False,'original_packages_modified':False})
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr)
if r.returncode:raise SystemExit(r.returncode)
