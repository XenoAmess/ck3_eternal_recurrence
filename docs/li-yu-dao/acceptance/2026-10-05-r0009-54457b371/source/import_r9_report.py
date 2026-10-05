"""Root-only future import. Read-only unless --execute is explicit.

Actual terminal RED/lost remains admissible; unresolved runtime ownership does
not. No game/native/desktop/Git/CI calls or raw CK3 save copies are performed.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path,PurePosixPath
import shutil,sys

sys.dont_write_bytecode=True
ROOT=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
REPO=Path('C:/workspace/ck3_eternal_recurrence').resolve()
SOURCE='54457b371e947edb86903c2ebd578034f02695db'
TARGET='docs/li-yu-dao/acceptance/2026-10-05-r0009-54457b371'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def inside(p,root):
 p=p.resolve()
 if p!=root and root not in p.parents:raise ValueError('Path outside designated root')
 return p
def relpath(text):
 text=str(text).replace('\\','/');p=PurePosixPath(text)
 if not text or ':' in text or p.is_absolute() or any(x in {'.','..'} for x in p.parts):raise ValueError('Unsafe relative path')
 return Path(*p.parts)

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--plan-sha256',required=True)
 ap.add_argument('--execute',action='store_true');ap.add_argument('--audit-output',type=Path)
 args=ap.parse_args();plan_path=inside(args.plan,ROOT)
 if sha(plan_path)!=args.plan_sha256:raise ValueError('Changed exact import plan')
 plan=read(plan_path)
 if plan['source_revision']!=SOURCE or plan['target_relative']!=TARGET:raise ValueError('Wrong source or target')
 package=inside(Path(plan['source']),ROOT);index=package/'INDEX.json';report_path=package/'REPORT.json'
 if sha(index)!=plan['index_sha256'] or sha(report_path)!=plan['report_sha256']:raise ValueError('Changed sealed report/index')
 report=read(report_path)
 if report.get('status')!='SEALED_AFTER_ROOT_ACTUAL_CLOSURE' or report.get('source_revision')!=SOURCE:raise ValueError('Preparation is not actual terminal evidence')
 closure=package/'closure/REPORT.raw.json'
 if sha(closure)!=plan['closure_sha256']:raise ValueError('Changed actual closure')
 actual=read(closure)
 head=actual.get('source_revision',actual.get('source_head',actual.get('frozen_head_at_terminal_verification')))
 if head!=SOURCE:raise ValueError('Wrong closure source')
 for key in ['process_absence','lease_released','source_freeze_released']:
  if actual.get(key) is not True:raise ValueError('Unresolved actualruntimeownership: '+key)
 if not actual.get('bindings'):raise ValueError('Unbound terminal observations')
 # Exact copied closurebindings retain true terminal results, including lost/
 # RED. A green SDK close is deliberately not a prerequisite for archival.
 ledger=read(package/'source-projection-map.json')
 bound_copies={str(Path(row['source_path']).resolve()).casefold():row for row in ledger}
 for row in actual['bindings']:
  if Path(row['path']).suffix.lower()=='.ck3':continue
  copied=bound_copies.get(str(Path(row['path']).resolve()).casefold())
  if copied is None or copied['original_sha256']!=row['sha256'] or copied['original_bytes']!=row['bytes']:raise ValueError('Terminalevidence not projectedexactly')
 records=read(index)['files'];expected=set();copies=[]
 for row in records:
  rel=relpath(row['path']);p=inside(package/rel,package);key=rel.as_posix().casefold()
  if key in expected or p.is_symlink() or p.suffix.lower()=='.ck3':raise ValueError('Invalid indexed file')
  expected.add(key)
  if not p.is_file() or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('Changed sealed file')
  copies.append((rel,p,row['bytes'],row['sha256']))
 actual_paths={p.relative_to(package).as_posix().casefold() for p in package.rglob('*') if p.is_file()}
 if actual_paths!=expected|{'index.json'}:raise ValueError('Unindexed or missing files')
 copies.append((Path('INDEX.json'),index,index.stat().st_size,sha(index)))
 result={'schema':'lyd.r9.report-import-receipt.v1','utc':datetime.now(timezone.utc).isoformat(),'source_revision':SOURCE,'source':str(package),'target':str(REPO/relpath(TARGET)),'files':len(copies),'bytes':sum(x[2] for x in copies),'plan_sha256':args.plan_sha256,'terminal_evidence_verified':True,'overall_native_acceptance':report['overall_native_acceptance'],'execute_requested':args.execute,'game_native_git_ci_screen_calls':0}
 if args.execute:
  if args.audit_output is None:raise ValueError('Explicit new external audit directory required')
  audit=inside(args.audit_output,ROOT)
  if audit.exists():raise FileExistsError('Refuse overwrite audit')
  target=inside(REPO/relpath(TARGET),REPO)
  if target.exists():raise FileExistsError('Refuse overwrite historical report')
  target.mkdir(parents=True,exist_ok=False)
  for rel,src,size,digest in copies:
   dst=inside(target/rel,target);dst.parent.mkdir(parents=True,exist_ok=True)
   with src.open('rb') as a,dst.open('xb') as b:shutil.copyfileobj(a,b)
   if dst.stat().st_size!=size or sha(dst)!=digest:raise ValueError('Imported byte mismatch')
  audit.mkdir(parents=True,exist_ok=False)
  with (audit/'receipt.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
 main()
