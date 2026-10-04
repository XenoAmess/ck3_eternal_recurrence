"""Root-owned exact-byte import. Terminal RED/lost evidence is admissible.

This command does not run Git, the game, native tooling, CI or a screen probe.
It writes tracked files only when root supplies --execute after real closure.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib,json
from pathlib import Path,PurePosixPath
import shutil,sys

sys.dont_write_bytecode=True
EXTERNAL=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
REPO=Path('C:/workspace/ck3_eternal_recurrence').resolve()
SOURCE='3d3305e75cf642a7a82bef5f9aee03dc76b3c10e'
TARGET='docs/li-yu-dao/acceptance/2026-10-05-R0006-closed-not-green'
TERMINAL_REPORT_SHA='4a17e35841bb2758be8369cc1ffc162bc194d809dd0cb745b6f6ce7510eb1873'

def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))

def inside(path,root):
 p=path.resolve()
 if p!=root and root not in p.parents:raise ValueError('Outside designated root: '+str(path))
 return p

def relative(value):
 text=str(value).replace('\\','/');p=PurePosixPath(text)
 if p.is_absolute() or not text or ':' in text or any(x in {'.','..'} for x in p.parts):raise ValueError('Unsafe path: '+text)
 return Path(*p.parts)

def package_files(row):
 root=inside(Path(row['source']),EXTERNAL);index=inside(root/relative(row['index_name']),root)
 if sha(index)!=row['index_sha256']:raise ValueError('Changed index: '+str(index))
 records=read(index)['files'];result=[];expected=set()
 for r in records:
  rel=relative(r['path']);p=inside(root/rel,root);key=rel.as_posix().casefold()
  if key in expected:raise ValueError('Duplicate indexed path')
  expected.add(key)
  if p.is_symlink() or not p.is_file() or p.suffix.lower()=='.ck3' or r['bytes']>50_000_000:raise ValueError('Unacceptable tracked asset: '+str(p))
  if p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:raise ValueError('Changed package content: '+str(p))
  result.append((rel,p,r['bytes'],r['sha256']))
 actual={p.relative_to(root).as_posix().casefold() for p in root.rglob('*') if p.is_file()}
 if actual!=expected|{index.relative_to(root).as_posix().casefold()}:raise ValueError('Unindexed or missing package files')
 result.append((index.relative_to(root),index,index.stat().st_size,sha(index)))
 return result

def terminal_gate(final_root,indexed):
 report=read(final_root/'FINAL-REPORT.json')
 if report.get('source_revision')!=SOURCE or report.get('overall_native_acceptance')!='NOT_GREEN':raise ValueError('Wrong final report identity/boundary')
 if not report.get('terminal_evidence_complete'):raise ValueError('Terminal observations still pending')
 allowed={
  'ck3_exit':{'OBSERVED_NORMAL_GUI_EXIT','OBSERVED_ABNORMAL_EXIT_RED'},
  'process_absence':{'VERIFIED_ABSENT'},
  'old_sdk':{'LOST_ABSENT_ORDERLY_CLOSE_NOT_OBSERVED','ORDERLY_CLOSE_OBSERVED_ABSENT'},
  'old_keeper':{'INTERRUPTED_ABSENT_FINAL_NOT_OBSERVED','FINAL_OBSERVED_ABSENT'},
  'recovery_keeper':{'STOP_FINAL_NORMAL_EXIT','TERMINAL_FAILURE_ABSENT_RED'},
  'screen_lease':{'FRESH_CAS_RELEASED'},
  'source_freeze':{'RELEASED_AFTER_ACTUAL_ABSENCE_AND_CAS'},
 }
 for key,choices in allowed.items():
  item=report.get('terminal_observations',{}).get(key,{})
  if item.get('result') not in choices or not item.get('evidence'):raise ValueError('Missing or inaccurate terminal outcome: '+key)
  for r in item['evidence']:
   p=inside(final_root/relative(r['path']),final_root)
   if p.relative_to(final_root).as_posix().casefold() not in indexed:raise ValueError('Unindexed terminal evidence')
   if p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:raise ValueError('Changed terminal evidence')
 actual=final_root/'closure/REPORT.raw.json'
 if sha(actual)!=TERMINAL_REPORT_SHA:raise ValueError('Actual root terminal receipt mismatch')
 terminal=read(actual)
 # Safety closure depends on observed absence and released ownership. An
 # orderly old SDK shutdown is not required for preserving this RED report.
 if terminal.get('process_absence') is not True or terminal.get('sdk_processes_absent') is not True or terminal.get('lease_released') is not True or terminal.get('source_freeze_released') is not True:raise ValueError('Runtime ownership still unresolved')
 if terminal.get('overall_acceptance')!='NOT_GREEN':raise ValueError('Historical RED boundary changed')
 if report['terminal_observations']['old_sdk']['result']=='LOST_ABSENT_ORDERLY_CLOSE_NOT_OBSERVED' and terminal.get('old_sdk_orderly_close_observed') is not False:raise ValueError('SDK lost/close contradiction')
 return report

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--plan',required=True,type=Path);parser.add_argument('--plan-sha256',required=True)
 parser.add_argument('--audit-output',type=Path);parser.add_argument('--execute',action='store_true')
 args=parser.parse_args();plan_path=inside(args.plan,EXTERNAL)
 if sha(plan_path)!=args.plan_sha256:raise ValueError('Frozen plan mismatch')
 plan=read(plan_path)
 if plan.get('source_revision')!=SOURCE or plan.get('target_relative')!=TARGET:raise ValueError('Changed import identity or target')
 copies=[];final_root=None;final_indexed=None
 for row in plan['packages']:
  prefix=relative(row['target_prefix']);files=package_files(row)
  if row.get('terminal_package'):
   if final_root is not None:raise ValueError('Multiple terminal report packages')
   final_root=inside(Path(row['source']),EXTERNAL);final_indexed={rel.as_posix().casefold() for rel,_,_,_ in files}
  copies += [(prefix/rel,p,size,digest) for rel,p,size,digest in files]
 if final_root is None:raise ValueError('No terminal report package')
 report=terminal_gate(final_root,final_indexed)
 names=[rel.as_posix().casefold() for rel,_,_,_ in copies]
 if len(set(names))!=len(names):raise ValueError('Import target collision')
 receipt={'schema':'lyd.r6.permanent-report-import.v2','utc':datetime.now(timezone.utc).isoformat(),'source_revision':SOURCE,'target':str(REPO/relative(TARGET)),'files':len(copies),'bytes':sum(x[2] for x in copies),'plan_sha256':args.plan_sha256,'terminal_evidence_complete':True,'overall_native_acceptance':report['overall_native_acceptance'],'old_sdk':'LOST_ABSENT_ORDERLY_CLOSE_NOT_OBSERVED','execute_requested':args.execute,'game_native_git_ci_screen_calls':0}
 if args.execute:
  if args.audit_output is None:raise ValueError('Explicit new external audit directory required')
  audit=inside(args.audit_output,EXTERNAL)
  if audit.exists():raise FileExistsError('Refuse overwrite external import audit')
  target=inside(REPO/relative(TARGET),REPO)
  if target.exists():raise FileExistsError('Refuse overwrite permanent report')
  target.mkdir(parents=True,exist_ok=False)
  for rel,src,size,digest in copies:
   dst=inside(target/rel,target);dst.parent.mkdir(parents=True,exist_ok=True)
   with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)
   if dst.stat().st_size!=size or sha(dst)!=digest:raise ValueError('Imported byte mismatch')
  audit.mkdir(parents=True,exist_ok=False)
  with (audit/'receipt.json').open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
 print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 main()
