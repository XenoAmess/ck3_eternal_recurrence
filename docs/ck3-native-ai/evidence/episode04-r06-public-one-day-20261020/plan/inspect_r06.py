from __future__ import annotations
import hashlib, json, pathlib, shutil, subprocess, sys
from datetime import datetime, timezone

REPO = pathlib.Path('D:/workspace/ck3_eternal_recurrence')
OUT = pathlib.Path(__file__).resolve().parent
BUS = pathlib.Path('D:/workspace/.codex-task-bus/bin/codex_task_bus.py')
TASK = 'e04-r06-minimal-plan-20261020-a01'

def command(args):
    if args[0] == sys.executable:
        args = [args[0], '-X', 'utf8', *args[1:]]
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding='utf-8')
    return {'returncode': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}

def read(rel):
    p = REPO / rel
    b = p.read_bytes()
    print(json.dumps({'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}, ensure_ascii=False))
    print(b.decode('utf-8-sig'))

if sys.argv[1] == 'start':
    records = {
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'machine': command([sys.executable, 'tools/ck3_live_run_id.py', 'machine']),
        'head': command(['git', 'rev-parse', 'HEAD']),
        'status': command(['git', 'status', '--short']),
        'bus_register': command([sys.executable, str(BUS), 'register', '--task', TASK, '--summary', 'Read-only R06 minimal single-day plan', '--next-step', 'Inspect R215 baseline and current producer contracts', '--repo', str(REPO)]),
        'capacity_observation': {v: dict(zip(('total','used','free'),shutil.disk_usage(v))) for v in ('C:/','D:/')},
        'write_budget_bytes': 262144,
        'reservation_scope': 'parent-managed next-r06-a01 C only; no independent reservation',
    }
    (OUT / 'START.actual.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(records, ensure_ascii=False, indent=2))
elif sys.argv[1] == 'read':
    for rel in sys.argv[2:]:
        read(rel)
elif sys.argv[1] == 'names':
    print('\n'.join(str(p) for p in (REPO / sys.argv[2]).iterdir() if any(s in p.name.lower() for s in sys.argv[3:])))
elif sys.argv[1] == 'lines':
    p = REPO / sys.argv[2]
    b=p.read_bytes(); lines=b.decode('utf-8-sig').splitlines()
    print(json.dumps({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
    for span in sys.argv[3:]:
        a,z=map(int,span.split(':'))
        print('\n'.join(f'{i}: {lines[i-1]}' for i in range(a,min(z,len(lines))+1)))
elif sys.argv[1] == 'bus':
    results={}
    for name,args in [('poll',['poll','--task',TASK,'--ack','--limit','30']),('list',['list','--require-existing'])]:
        r=command([sys.executable,str(BUS),*args]); value=json.loads(r['stdout'])
        if name=='list':
            value={k:v for k,v in value.items() if k!='tasks'} | {'tasks':[t for t in value.get('tasks',[]) if t.get('last_sequence',0)>=7250 and t.get('state') not in ('done','blocked')]}
        else:
            value={k:v for k,v in value.items() if k!='events'} | {'recent_relevant_events':[e for e in value.get('events',[]) if e.get('sequence',0)>=7250]}
        results[name]=value
    (OUT/'BUS-CHECK.actual.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))
