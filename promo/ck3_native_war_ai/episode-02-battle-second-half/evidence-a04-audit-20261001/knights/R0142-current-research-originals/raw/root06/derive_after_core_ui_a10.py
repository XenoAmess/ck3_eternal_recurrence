from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
src=ROOT/'run_active_battle_ui_stage_a09.py';dst=ROOT/'run_after_core_ui_a10.py'
raw=src.read_bytes()
needle=b"    for side in ('left','right'):\n        operations.append((side+'-knights-tooltip',['--mode','hover','--ui-side',side]))\n    operations.append(('save',['--mode','save']))"
assert raw.count(needle)==1
new=raw.replace(needle,b"    require(args.phase=='after','This independent capture stage only collects next-day core UI')")
with dst.open('xb') as stream:stream.write(new)
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
with (ROOT/'after-core-ui-derivation-a10.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump({'original':ident(src),'derived':ident(dst),'only_source_change':'Collect after checkpoint, two角色 pages, combat/fit; mouse fallback tooltips and main-after save are separate audited operations. No failed native hover is retried.',
        'trace_export_stays_RED':True,'no_day_advance':True,'controller_runtime_source_unchanged':True},stream,indent=2);stream.write('\n')
print(str(dst))
