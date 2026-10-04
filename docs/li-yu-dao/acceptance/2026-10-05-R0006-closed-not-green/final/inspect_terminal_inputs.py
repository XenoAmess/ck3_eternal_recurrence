from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent.parent
names=['r6-terminal-closure-20261005-001','r6-resource-and-elector-origin-resume-20261005-003','r6-elector-court-origin-supplement-20261005-001','r6-managed-exit-recovery-20261005-001','r6-managed-exit-recovery-20261005-002','screen-lease-live-r0006-exit-20261005','r6-normal-exit-watcher-20261005-001','runtime-state-review-20261005-001','live-attempt-006/log-observations/final-before-normal-exit-20261005-001','live-attempt-006/log-observations/final-after-normal-exit-20261005-001']
for name in names:
 p=ROOT/name
 print(json.dumps({'directory':name,'exists':p.exists(),'direct_children':[x.name+('/' if x.is_dir() else '') for x in sorted(p.iterdir())] if p.exists() else []},ensure_ascii=False))
 if p.exists():
  for index_name in ['INDEX.json','INDEX-final.json']:
   f=p/index_name
   if f.exists():
    raw=f.read_bytes();obj=json.loads(raw);rows=obj['files']
    print(json.dumps({'index':str(f),'sha256':hashlib.sha256(raw).hexdigest(),'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'large_files':[r for r in rows if r['bytes']>1000000]},ensure_ascii=False))
for rel in ['r6-resource-and-elector-origin-resume-20261005-003/REPORT.md','r6-normal-exit-watcher-20261005-001/RESULT.json','screen-lease-live-r0006-exit-20261005/FINAL.json','r6-terminal-closure-20261005-001/PROCESSES-ABSENT.json']:
 p=ROOT/rel
 print(json.dumps({'file':rel,'content':p.read_text(encoding='utf-8-sig')},ensure_ascii=False))
