"""Root metadata -> existing R10 runtime schema. No SDK/transport/native IO.

The actual process creation FILETIME supplies started_at_utc. A proof's later
recorded_at is not a cold-load start. This projector grants no runtime credit.
"""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import argparse,hashlib,json,re

def need(ok,message):
    if not ok:raise ValueError(message)

def filetime_utc(value):
    need(type(value)is int and 0<value<2**64,'actual positive unsigned64 creation FILETIME required')
    seconds,ticks=divmod(value,10_000_000)
    try:base=datetime(1601,1,1,tzinfo=timezone.utc)+timedelta(seconds=seconds)
    except OverflowError as error:raise ValueError('creation FILETIME outside representable UTC date')from error
    return base.strftime('%Y-%m-%dT%H:%M:%S')+f'.{ticks:07d}+00:00'

def project(proof,prepared,context,proof_pin,evidence_root,*,plan=None):
    """Return the canonical runtime object only; use existing guards before IO."""
    need(proof.get('schema')=='xar.e04.robert-identity-source-chain.actual.v1','original Root identity proof schema required')
    source=proof.get('source_head');machine=proof.get('machine_id')
    need(type(source)is str and re.fullmatch('[0-9a-f]{40}',source),'actual runtime source_head required')
    identity=context.get('identity')or{}
    need(type(machine)is str and machine and prepared.get('machine_id')==context.get('machine_id')==identity.get('machine_id')==machine,'Root proof/prepared/context machine differs')
    need(type(proof.get('run_id'))is str and proof['run_id']and context.get('source_head')==source and identity.get('run_id')==proof['run_id']and identity.get('mod_key')=='vanilla','actual context source/run/vanilla binding differs')
    for k in ('pid','process_creation_filetime_100ns','connection_generation','actual_runtime_character_full_id'):
        need(type(proof.get(k))is int and proof[k]>0,'missing strict actual proof integer: '+k)
    episode=proof.get('episode_run_id');need(type(episode)is str and episode,'actual episode required')
    dll=(prepared.get('bridge_dll')or{}).get('sha256')
    need(type(dll)is str and re.fullmatch('[0-9a-fA-F]{64}',dll),'qualified prepared DLL metadata SHA required')
    need((prepared.get('target_build')or{}).get('version')=='1.20.0.4','exact4 prepared metadata required')
    started=filetime_utc(proof['process_creation_filetime_100ns'])
    if plan is not None:
        need(plan.get('status')=='frozen','formal plan must already be frozen')
        frozen=datetime.fromisoformat(plan['frozen_at_utc'].replace('Z','+00:00'))
        need(frozen.tzinfo is not None and frozen<datetime.fromisoformat(started),'process actually started before plan freeze; later proof recording cannot qualify cold arm')
        need(plan['build']['source_head']==source and plan['build']['native_dll_sha256']==dll.lower(),'plan actual source/DLL differs')
    p=Path(proof_pin['path']).resolve();root=Path(evidence_root).resolve()
    need(p.is_relative_to(root),'source proof must be inside explicit evidence root')
    need(type(proof_pin.get('bytes'))is int and proof_pin['bytes']>0 and type(proof_pin.get('sha256'))is str and re.fullmatch('[0-9a-f]{64}',proof_pin['sha256']),'exact actual proof bytes/SHA required')
    # Native build provenance is retained in the original proof. No requirement
    # equates a Python-only runtime revision with a new native rebuild revision.
    return {'machine_id':machine,'started_at_utc':started,'pid':proof['pid'],
        'process_create_time_100ns':proof['process_creation_filetime_100ns'],
        'connection_generation':proof['connection_generation'],'episode':episode,
        'player_character_id':proof['actual_runtime_character_full_id'],'source_head':source,
        'native_dll_sha256':dll.lower(),'source_proof':{'path':p.relative_to(root).as_posix(),
        'bytes':proof_pin['bytes'],'sha256':proof_pin['sha256']}}

def read_pinned(path,expected):
    p=Path(path).resolve();need(p.is_file()and 0<p.stat().st_size<=1024*1024,'bounded actual metadata JSON required')
    raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==expected,'actual metadata exact SHA differs')
    def pairs(rows):
        d={}
        for k,v in rows:need(k not in d,'duplicate JSON key');d[k]=v
        return d
    return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=pairs),{'path':str(p),'bytes':len(raw),'sha256':expected}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('proof','prepared','context'):p.add_argument('--'+key,nargs=2,required=True,metavar=('PATH','SHA256'))
    p.add_argument('--plan',nargs=2,metavar=('PATH','SHA256'))
    p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv);proof,ref=read_pinned(*a.proof);prepared,_=read_pinned(*a.prepared);context,_=read_pinned(*a.context)
    plan=read_pinned(*a.plan)[0]if a.plan else None
    result=project(proof,prepared,context,ref,a.evidence_root,plan=plan)
    with a.output.open('x',encoding='utf-8',newline='\n')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'output':str(a.output),'runtime_fact_source':'Root proof process creation FILETIME','SDK_calls':0,'runtime_qualification_granted':False}));return 0
if __name__=='__main__':raise SystemExit(main())
