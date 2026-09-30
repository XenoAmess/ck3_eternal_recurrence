from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,sys,time
ROOT=Path(__file__).resolve().parent;name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
log=ROOT/'board-invocations'/name;log.parent.mkdir(exist_ok=True)
argv=[sys.executable,'C:/w/ep2a04/promo/ck3_native_war_ai/episode-02-battle-second-half/compose_review_boards_a04.py','--run','C:/Users/1/AppData/Local/ck3-review-render/episode02-a04-boards-a02','--story',str(ROOT/'story-final-v2.json'),'--spec',str(ROOT/'visual-spec-final-v1.json')]
with log.with_suffix('.argv.json').open('x',encoding='utf-8') as f:json.dump(argv,f,indent=2)
begin=time.monotonic()
with log.with_suffix('.stdout.txt').open('xb') as out,log.with_suffix('.stderr.txt').open('xb') as err:r=subprocess.run(argv,stdout=out,stderr=err)
with log.with_suffix('.receipt.json').open('x',encoding='utf-8') as f:json.dump({'exit_code':r.returncode,'at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-begin},f,indent=2)
print(log.with_suffix('.stdout.txt').read_text(encoding='utf-8',errors='replace'))
if r.returncode:print(log.with_suffix('.stderr.txt').read_text(encoding='utf-8',errors='replace'))
raise SystemExit(r.returncode)
