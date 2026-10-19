import ast,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import checkpoint6397_saved_frontier_v1 as contract
OLD='''    item=admission['old_sdk_closed']
    if sha(item['path'])!=item['sha256']:raise ValueError('actual old C5 signaled closure changed')
    proof=read(item['path'])
    if (proof.get('normal') is not True or [r['exit_code'] for r in proof['processes']]!=[0,0]
        or not all(r['kernel_exit_observed'] for r in proof['processes'])):
        raise ValueError('actual prior C10B signaled0/0 closure differs')
'''
NEW='''    if admission.get('old_sdk_closure_kind')=='EXACT_C15_INTERRUPTED_F90':
        from MODULE import validate_abnormal_closure
        validate_abnormal_closure(admission)
        ended=read(admission['interruption']['path'])
        proof={'normal':False,'derived_interrupted_source':admission['interruption'],
            'processes':[{'role':r['role'],'pid':r['pid'],'creation_filetime':r['creation_filetime'],
                'exit_code':r['exit_code'],'kernel_exit_observed':True}
                for r in ended['kernel_exit_times'] if r['role'] in ('SDKQueue','SDKApp')]}
    else:
'''
def bind_f90_sdk_owner(source,*,contract_module):
    if not contract_module.isidentifier() or source.count(OLD)!=1:raise ValueError('owner/module')
    new=NEW.replace('MODULE',contract_module)+''.join('    '+line for line in OLD.splitlines(True))
    result=source.replace(OLD,new)
    if result.replace(new,OLD)!=source:raise ValueError('owner changed')
    compile(result,'finite-owner','exec')
    return result

def main():
    t=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
    raw=(t/'launch_sdk_p37c15_owner.py').read_bytes()
    if hashlib.sha256(raw).hexdigest()!='60ba203510d312ab1f0276fab95192b7296008eb11d2a0c3ce297a5a3a819a94':raise ValueError('owner changed')
    result=bind_f90_sdk_owner(raw.decode(),contract_module=contract.__name__)
    node=next(n for n in ast.walk(ast.parse(result)) if isinstance(n,ast.If) and 'old_sdk_closure_kind' in ast.unparse(n.test))
    p=t.parent.parent/'p51-fresh1066-v20261019-prepare01/c15-session-interruption90/FROZEN.json'
    ns={'admission':{'old_sdk_closure_kind':'EXACT_C15_INTERRUPTED_F90','interruption':{'path':str(p),'bytes':13369,'sha256':contract.PINS['interruption'][1]}},'read':lambda q:json.loads(Path(q).read_bytes())}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'F90-owner','exec'),ns)
    if ns['proof']['normal'] is not False or [r['exit_code'] for r in ns['proof']['processes']]!=[1,1]:raise ValueError('wrong derived closure')
    print(json.dumps({'machine_id':contract.MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'case':'F90 PASS; normal branch unchanged','calls':0,'bytes':len(result.encode()),'sha256':hashlib.sha256(result.encode()).hexdigest()}))
if __name__=='__main__':main()
