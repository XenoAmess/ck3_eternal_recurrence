from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parent
PRODUCER=Path('C:/w/ep2a04/promo/ck3_native_war_ai/episode-02-battle-second-half/review_story_a04.py')
p=argparse.ArgumentParser();p.add_argument('phase');p.add_argument('--run',required=True,type=Path);p.add_argument('--story',type=Path);p.add_argument('--previous',type=Path);p.add_argument('--edit',type=Path);a=p.parse_args()
token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');log=ROOT/'phase-invocations'/f'{token}-{a.phase}';log.parent.mkdir(exist_ok=True)
argv=[sys.executable,str(PRODUCER),a.phase,'--run',str(a.run)]
if a.story:argv+=['--story',str(a.story),'--environment',str(ROOT/'environment.json')]
if a.previous:argv+=['--previous',str(a.previous)]
if a.edit:argv+=['--edit',str(a.edit)]
with log.with_suffix('.argv.json').open('x',encoding='utf-8') as f:json.dump(argv,f,indent=2)
started=datetime.now(timezone.utc).isoformat();begin=time.monotonic()
with log.with_suffix('.stdout.txt').open('xb') as out,log.with_suffix('.stderr.txt').open('xb') as err:
    process=subprocess.Popen(argv,stdout=out,stderr=err)
    with log.with_suffix('.start.json').open('x',encoding='utf-8') as f:json.dump({'at_utc':started,'pid':process.pid,'argv':argv},f,indent=2)
    print(json.dumps({'pid':process.pid,'phase':a.phase,'run':str(a.run),'log':str(log)}),flush=True)
    rc=process.wait()
with log.with_suffix('.receipt.json').open('x',encoding='utf-8') as f:json.dump({'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':rc,'elapsed_seconds':time.monotonic()-begin,'pid':process.pid,'argv':argv},f,indent=2)
print(log.with_suffix('.stdout.txt').read_text(encoding='utf-8',errors='replace'),flush=True)
if rc:print(log.with_suffix('.stderr.txt').read_text(encoding='utf-8',errors='replace'),flush=True)
raise SystemExit(rc)
