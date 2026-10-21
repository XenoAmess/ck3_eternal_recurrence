"""Create-only final source patch and bounded evidence copy plan."""
from __future__ import annotations
from datetime import datetime,timezone
import difflib,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def pin(path: Path) -> dict[str,object]:
    raw=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def save(path: Path,value: object) -> None:
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')

def main() -> None:
    if datetime.now(timezone.utc)>=datetime(2026,10,21,2,30,tzinfo=timezone.utc):raise ValueError('Source scope expired')
    frozen=ROOT/'SOURCE-FREEZE.actual-a01.json'
    expected='071879b9f7332dba83f85fe6839e355e36ba7319cee37b9c169b4494bcb415c2'
    if pin(frozen)['sha256']!=expected:raise ValueError('Freeze changed')
    value=json.loads(frozen.read_bytes());patch=[]
    for row in value['production_mapping']:
        source=Path(row['source']['path'])
        if pin(source)!=row['source']:raise ValueError('Frozen production source changed')
        name=row['repository_relative_path']
        patch.extend(difflib.unified_diff([],source.read_text().splitlines(keepends=True),
            fromfile='/dev/null',tofile='b/'+name))
    path=ROOT/'POSTLOAD-PUBLIC-SOURCE.candidate-a01.patch'
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(''.join(patch))
    # The patch only adds this lane's ten new files. Integration must check actual
    # current-tree absence/conflicts; this producer performs no Git operation.
    selected=[ROOT/name for name in ['SOURCE-INPUTS.actual-a01.json','SOURCE-FREEZE.actual-a01.json',
        'PUBLIC-SOURCE-CONTRACT.prepared-a01.json','PUBLIC-SOURCE-INDEX.prepared-a04.json',
        'CASE-INPUTS.source-only-template-a04.json','ROOT-AUTHORIZATION.source-template-a01.json',
        'EXTERNAL-PUBLIC-CASE.source-fragment-a01.json','README.md','test_postload_public.py',
        'assemble_source.py','build_index.py','run_checks.py','seal_source.py','deliver.py',
        'POSTLOAD-PUBLIC-SOURCE.candidate-a01.patch']]
    selected += [Path(row['source']['path']) for row in value['production_mapping']]
    for directory in sorted(ROOT.glob('checks-*')):
        selected += [path for path in sorted(directory.iterdir()) if path.is_file()]
    copyplan={'schema':'xar.e04.postload.public-source-copyplan.v1','machine_id':value['machine_id'],
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'source_freeze':pin(frozen),
        'files':[{'relative_path':path.relative_to(ROOT).as_posix(),'source':pin(path)} for path in selected],
        'payload_bytes':sum(path.stat().st_size for path in selected),
        'pin_only_support_policy':'Unchanged four native typed files and shared common/Save/R10 files are support refs, not overwrite inputs; exact source pins in freeze/index',
        'public_source_only':True,'actual_new_Q_exists':False,'native_scope_closed':False,
        'no_Git_D_W_or_native_execution':True}
    plan=ROOT/'MINIMAL-COPYPLAN.actual-a01.json';save(plan,copyplan)
    delivery={'schema':'xar.e04.postload.public-source-delivery.v1','machine_id':value['machine_id'],
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'source_freeze':pin(frozen),'production_patch':pin(path if False else ROOT/'POSTLOAD-PUBLIC-SOURCE.candidate-a01.patch'),
        'source_contract':value['source_contract'],'bundle_index':value['bundle_index'],
        'production_mapping':value['production_mapping'],'final_checks':value['final_checks'],
        'finite_Python_methods':15,'strict_new_production_files':9,
        'typecheck_scope':'modified sources, strict, follow-imports=skip, no incremental/cache; not whole tree',
        'README':value['README'],'copyplan':pin(plan),
        'qualification':{'actual_new_Q_exists':False,'native_successor_frozen':False,'new_native_build_cold':False,
            'runtime_complete':False,'Game_Steam_SDK':False,'full_R08':False,'paid_maintenance_raw':None},
        'writer_state':'all source and metadata writers stop after this delivery',
        'tmp_remaining':[str(path) for path in (ROOT/'tmp').rglob('*')],
        'lane_hardcap_bytes':2097152,'hard_deadline_utc':'2026-10-21T02:30:00Z'}
    target=ROOT/'DELIVERY.actual-a01.json';save(target,delivery)
    actual=sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file())
    if actual>2097152:raise ValueError('Lane cap exceeded')
    print(json.dumps({'delivery':pin(target),'patch':pin(ROOT/'POSTLOAD-PUBLIC-SOURCE.candidate-a01.patch'),
        'copyplan':pin(plan),'lane_bytes':actual,'writers':0}))

if __name__=='__main__':main()
