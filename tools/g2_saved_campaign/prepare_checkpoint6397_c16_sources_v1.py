"""Pure C16 port of the closed C15 graph; no writes, processes or Game calls."""
import ast,copy,hashlib,importlib.util,json,re,sys,types
from datetime import datetime,timezone
from pathlib import Path
import prepare_checkpoint6322_cold_v1 as prior
import prepare_checkpoint6397_sdk_owner_v1 as owner_binder

T=prior.T
OWN=Path(__file__).resolve().parent
CONTRACT='root_checkpoint6397_cold_contract_c16'
PINS={
 'root_p37c15_sdk_queue.py':'30823cafc946b846fefd851b1ad65b9601fd8ba0d8d9cd388ecc1ae9867c236f',
 'root_p37c15_mcp_entry.py':'b0a52546bd1639b75f5957dff8c81d7fec73df2d527f81ae93a549d138bb505f',
 'root_native_build_binding_p37c15.py':'6bd0b40792dcbd37f67f692190e9317ec8c60a425f148795b50d5acc876c2fe2',
 'root_p37c15_automatic_natural_succession_handoff.py':'a95e9f7d099db0ded85093b2237125d277a26d2fbbb1e94618437f3ad12d9073',
 'p51_resident_successor_adoption_c15.py':'6381a99e2f5efe870d4527ea416b1204c8a3612b1625329e11a3c83e16ad6cba',
 'launch_sdk_p37c15_owner.py':'60ba203510d312ab1f0276fab95192b7296008eb11d2a0c3ce297a5a3a819a94',
 'root_p37c15_cold_resume.py':'2db2f72ada9e059156ca5a199d1ad846721946eaff6269f3a317cdb7b37d87dc',
 'root_checkpoint_bootstrap_c15.py':'f30d09028c8c9f0284e45c6f27d78431e5c2bcb27ec97961f8633ca33c8a4dbc',
 'root_native29_supervisor_c15.py':'fb1c665b49b82b1424400a04224961f91c4a68621c9a3a6232637ebc02836611',
 'root_record_shutdown_c15.py':'5d2f399c056915133e8c7f78645388f089850e23630144e3ff664fae1f01c271',
 'root_score_month_samples_c15.py':'80bf40298d70d7667e37748343b837e15c515cacdcdf5b0b3ecfbdfe5be7df73',
 'root_c15_control_timing_adapter.py':'8de977bf27ff0f9c4dd325845daca5b60908d4ccebedd730a7048e1e10a5f3be',
 'root_c15_queue_control_timing.py':'3950b3ce7ca1d4de401ba8e176d962c92187c2ad6fd280621e57d1f8f205d96c',
 'root_screen_bus_lease_c15.py':'012bb0a2aec9475ca8689bf42adc2e6c2431161814f7531f0710dbb633348780',
}
DEPS={
 'prepare_checkpoint6322_cold_v1.py':'8b22aaaef03c8b9ce0f1b64758d2acab22d92e46579b5dd2018f008a5a218bef',
 'prepare_checkpoint6397_sdk_owner_v1.py':'261d4baf95f81ce562b282d690657de7e6ae7d80a4a9da926548a5b4ad9e87de',
 'checkpoint6397_saved_frontier_v1.py':'d844c5b0f6e399f039b48f58f852bbf65c159386a068da207a261bba8458df90',
}
MAP=[('P37C15','P37C16'),('p37c15','p37c16'),('_c15','_c16'),('-C15','-C16'),('SDKC15','SDKC16'),('xar.c15.','xar.c16.')]
SDK_HELPER='''
def validate_sdk_interruption(admission,sdk):
    validate_abnormal_closure(admission)
    require(admission.get('old_sdk_closure_kind')=='EXACT_C15_INTERRUPTED_F90'
        and admission.get('old_Game')=={'pid':115472,'creation_filetime':134368932806525787},'finite old Game differs')
    require(sdk.get('machine_id')==MACHINE and sdk.get('normal') is False
        and sdk.get('interruption_source')==admission['interruption']
        and len(sdk.get('processes',[]))==2,'finite derived SDK closure differs')
    expected={(188716,134368947981891115),(15156,134368948030748335)}
    require({(p.get('pid'),p.get('creation_filetime')) for p in sdk['processes']}==expected
        and all(p.get('exit_code')==1 and p.get('kernel_exit_observed') is True
            and p.get('observation_error') is None for p in sdk['processes']),'finite SDK kernel exits differ')
    return True
'''
BOOT_OLD='''    require(sdk.get('normal') is True and sdk.get('machine_id') == MACHINE
        and sdk.get('launcher_exit_code') == 0 and len(sdk.get('processes', [])) == 2
        and all(p.get('exit_code') == 0 and p.get('kernel_exit_observed') is True
            and p.get('observation_error') is None for p in sdk['processes']), 'normal actual SDK kernel closure required')'''
BOOT_NEW='''    if close.get('old_sdk_closure_kind') == 'EXACT_C15_INTERRUPTED_F90':
        from root_checkpoint6397_cold_contract_c16 import validate_sdk_interruption
        validate_sdk_interruption(close, sdk)
    else:
'''+''.join('    '+line+'\n' for line in BOOT_OLD.splitlines()).rstrip('\n')
FACT_OLD="            require(env['sdk_pair_closed'](old) and close['sdk_closed'] == admission['old_sdk_closed']"
FACT_NEW="""            from root_checkpoint6397_cold_contract_c16 import validate_sdk_interruption
            sdk_closed = (validate_sdk_interruption(admission, old)
                if admission.get('old_sdk_closure_kind') == 'EXACT_C15_INTERRUPTED_F90'
                else env['sdk_pair_closed'](old))
            require(sdk_closed and close['sdk_closed'] == admission['old_sdk_closed']"""

def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(path,sha):return prior.text(path,sha)
def swap(value,a,b):return prior.replace_once(value,a,b)
def name16(name):
    for a,b in MAP:name=name.replace(a,b)
    return name

def build_sources():
    for name,sha in DEPS.items():read(OWN/name,sha)
    original={name:read(T/name,sha) for name,sha in PINS.items()}
    out={name16(name):prior.port(value,MAP) for name,value in original.items()}
    old_contracts=('root_checkpoint6322_cold_contract_c16','root_checkpoint6322_queue_contract_c16')
    boot='root_checkpoint_bootstrap_c16.py';factory='root_p37c16_cold_resume.py';owner='launch_sdk_p37c16_owner.py'
    out[boot]=swap(out[boot],old_contracts[0],CONTRACT)
    out[factory]=swap(out[factory],old_contracts[1],CONTRACT)
    before_boot=out[boot];before_factory=out[factory]
    out[boot]=swap(out[boot],BOOT_OLD,BOOT_NEW)
    out[factory]=swap(out[factory],FACT_OLD,FACT_NEW)
    if out[boot].replace(BOOT_NEW,BOOT_OLD)!=before_boot or out[factory].replace(FACT_NEW,FACT_OLD)!=before_factory:
        raise ValueError('finite hunks not reversible')
    out[owner]=owner_binder.bind_f90_sdk_owner(out[owner],contract_module=CONTRACT)
    out[CONTRACT+'.py']=read(OWN/'checkpoint6397_saved_frontier_v1.py',DEPS['checkpoint6397_saved_frontier_v1.py'])+SDK_HELPER
    for name,source in out.items():
        compile(source,name,'exec')
        if name!=CONTRACT+'.py':
            for n in ast.walk(ast.parse(source)):
                value=n.value if isinstance(n,ast.Constant) and isinstance(n.value,str) else n.module if isinstance(n,ast.ImportFrom) else ''
                if any(a in value for a,b in MAP):raise ValueError('old namespace '+name+': '+value[:100])
    if len(out)!=15:raise ValueError('control graph count differs')
    return {name:source.encode() for name,source in out.items()}

def qualify():
    sources=build_sources();mod=types.ModuleType(CONTRACT)
    exec(compile(sources[CONTRACT+'.py'],CONTRACT,'exec'),mod.__dict__)
    p=T.parent.parent/'p51-fresh1066-v20261019-prepare01/c15-session-interruption90/FROZEN.json'
    ref={'path':str(p),'bytes':13369,'sha256':mod.PINS['interruption'][1]}
    admission={'old_sdk_closure_kind':'EXACT_C15_INTERRUPTED_F90','interruption':ref,
        'old_Game':{'pid':115472,'creation_filetime':134368932806525787}}
    proof={'machine_id':prior.MACHINE,'normal':False,'interruption_source':ref,'processes':[
        {'pid':188716,'creation_filetime':134368947981891115,'exit_code':1,'kernel_exit_observed':True,'observation_error':None},
        {'pid':15156,'creation_filetime':134368948030748335,'exit_code':1,'kernel_exit_observed':True,'observation_error':None}]}
    previous=sys.modules.get(CONTRACT);sys.modules[CONTRACT]=mod
    try:
        # Execute exactly the two new closure seams, not a substitute test algorithm.
        tree=ast.parse(sources['root_checkpoint_bootstrap_c16.py'])
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_prelaunch')
        block=next(n for n in fn.body if isinstance(n,ast.If) and 'old_sdk_closure_kind' in ast.unparse(n.test))
        def run_boot(close,sdk):
            exec(compile(ast.Module(body=[block],type_ignores=[]),'actual-bootstrap-seam','exec'),{'close':close,'sdk':sdk,'require':mod.require,'MACHINE':prior.MACHINE})
        run_boot(admission,proof)
        negative=copy.deepcopy(admission);negative['old_Game']['creation_filetime']+=1
        try:run_boot(negative,proof)
        except ValueError:pass
        else:raise ValueError('wrong old identity accepted')
        normal={'machine_id':prior.MACHINE,'normal':True,'launcher_exit_code':0,'processes':[
            {'exit_code':0,'kernel_exit_observed':True,'observation_error':None} for _ in range(2)]}
        run_boot({},normal)
        factory=ast.parse(sources['root_p37c16_cold_resume.py'])
        cls=next(n for n in ast.walk(factory) if isinstance(n,ast.ClassDef) and n.name=='NormalCheckpointColdQueue')
        pre=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='preflight')
        assign=next(n for n in pre.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='sdk_closed' for t in n.targets))
        ns={'admission':admission,'old':proof,'validate_sdk_interruption':mod.validate_sdk_interruption,'env':{'sdk_pair_closed':lambda x:(_ for _ in ()).throw(ValueError('normal path reached'))}}
        exec(compile(ast.Module(body=[assign],type_ignores=[]),'actual-factory-seam','exec'),ns)
        if ns['sdk_closed'] is not True:raise ValueError('factory finite seam failed')
    finally:
        if previous is None:sys.modules.pop(CONTRACT,None)
        else:sys.modules[CONTRACT]=previous
    return {'schema':'xar.c16.finite-control-source-review/v1','machine_id':prior.MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'SOURCE_COMPOSITION_PASS',
        'input_sha256':PINS,'sources':{name:{'bytes':len(raw),'sha256':digest(raw)} for name,raw in sources.items()},
        'source_bytes':sum(map(len,sources.values())),'adoption_copies':1,'D_writes':0,'Driver_SAVE_reads':0,'RPC_calls':0,
        'checks':['15 compile; namespace AST port; protected machine/episode; exact source pins',
            'finite bootstrap/factory inverse bytes; original normal branch positive',
            'actual F90 positive; wrong old Game birth rejected; actual factory finite branch'],
        'current_frontier':{'cycles':3039,'date_raw':53202720,'SAVE':6397,'historical_tail_cycles':234,'unknown_AUTO6874_replayed':False},
        'remaining':['sole runtime metadata cumulative budget','canonical Driver checkpoint validator','durable stage custody','fresh cold SEM/CAP and Root pixels']}

if __name__=='__main__':
    result=qualify()
    if len(sys.argv)==2:
        with Path(sys.argv[1]).open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
