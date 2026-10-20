"""One C23 a02 value-path check; real algorithms, RAM resources, no process API."""
import ast
import builtins
import copy
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import time
import types
import unittest

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prepare_c23_full_enabled_cold_controls_v1 as p

T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
POLICY_SHA='28d879d547d3cd02e766fa4867ad5863dc2ebe13f460a7183bc98f6587b87bf5'
CHAIN_SHA='54475da0a10dce93fe306880df502e977cd41c056195b3a429bd7465e79a1ef4'


def nodes(raw,names):
    result=[n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    if {n.name for n in result}!=set(names):raise ValueError('one actual source definition per requested name required')
    return ast.Module(body=result,type_ignores=[])


class A02CreatorContract(unittest.TestCase):
    def test_actual_factory_to_child_receiver_and_limits(self):
        graph,_=p._compose_source_graph()
        policy_raw=(T/'ROOT-C23-CANONICAL-PRELOAD-POLICY.json').read_bytes()
        self.assertEqual(p.sha(policy_raw),POLICY_SHA)
        policy=json.loads(policy_raw)
        self.assertEqual(len(policy['entry_source_pins']),44)
        names={'root_native30_supervisor_c23.py','root_checkpoint_bootstrap_c23.py',
            'launch_sdk_p37c23_owner.py','root_p37c23_sdk_queue.py',
            'root_p37c23_mcp_entry.py','root_c23_canonical_outer.py'}
        policy['canonical_entry_source_pins']=[r for r in policy['entry_source_pins'] if Path(r[0]).name in names]
        outer_scope={'Path':Path,'hashlib':hashlib,'sys':sys,'require':p.require,'MACHINE':p.MACHINE}
        exec(p.external_import_guard_source(),outer_scope)
        # Full predecessor44 actual source values are checked without writing
        # candidate files. Their old SHA is fixture input, not a02 adoption.
        outer_scope['_check_c23_external_imports'](T,policy)
        chain_path=p.OWN/'canonical_native_provider_chain_v1.py';chain_raw=chain_path.read_bytes()
        self.assertEqual(p.sha(chain_raw),CHAIN_SHA)
        selected=['consume_private_bootstrap_args_v1','_verified_entry_sources','_creator_digest',
            '_require_direct_entry_command_v1','CanonicalPreloadFactoryV1','_ChildPlanV1',
            'prepare_child_v1','receive_child_bootstrap_v1']
        calls=[];seal=object()

        class Holder:
            def __init__(self,facade):
                self.facade=facade;self.closed=False;self.seal=seal
                self.machine_id=p.MACHINE;self.pipe_name='XARG2Native_'+('a'*48)
                self.process_handle=11;self.dll_handle=12;self._creation_role_v1='supervisor'
                self._creation_attempted_v1=False
            def close(self):self.closed=True

        class IO:
            counter=1000
            def __init__(self,facade,enabled=False):
                self.facade=facade;self.api=types.SimpleNamespace(PROCESS_READ_ACCESS=0x101000,current=lambda:7)
            def server(self,holder):return 20,'XARG2ChildBootstrap_'+('b'*48)
            def duplicate(self,*args,**kwargs):
                IO.counter+=1;return IO.counter
            def client(self,name):return 21
            def adopt_inherited(self,*args,**kwargs):pass
            def send(self,handle,value):self.last=value
            def recv(self,handle):return {'kind':'parent_accepted','epoch':self.last['epoch'],'creator':self.last['creator']}

        facade=types.SimpleNamespace(_received_preloads_v1={},observe_process=lambda h:'RAM-peer')
        def prepare(**kw):
            calls.append('custody');return Holder(kw['os_facade'])
        def origin(custody,enabled=False):
            value=types.SimpleNamespace(origin_handle=13,pipe_name='XARG2CanonicalOrigin_'+('c'*48),revoke_handle=14)
            custody._canonical_origin_v1=value;custody._canonical_chain_io_v1=IO(custody.facade,enabled=True)
            return value
        def receive(**kw):
            holder=Holder(kw['facade']);kw['facade']._received_preloads_v1[holder]=types.SimpleNamespace(revoke_handle=15)
            return types.SimpleNamespace(available=True,reason=None,holder=holder)
        contract=types.SimpleNamespace(_require=p.require,_sha=lambda v:isinstance(v,str) and len(v)==64,
            prepare_canonical_cold_custody_v1=prepare,_PreloadCustodyV1=Holder,_RESOURCE_SEAL=seal,
            _process=lambda v:v,_same_process=lambda a,b:a==b)
        scope={'__file__':str(chain_path),'Path':Path,'hashlib':hashlib,'json':json,'contract':contract,
            'OriginKernelIOV1':IO,'prepare_canonical_origin_v1':origin,
            'receive_inherited_preload_v1':receive,'_epoch':lambda:'RAM_SOURCE_ONLY',
            'subprocess':types.SimpleNamespace(STARTUPINFO=lambda **kw:types.SimpleNamespace(**kw))}
        exec(compile(nodes(chain_raw,selected),str(chain_path),'exec'),scope)
        chain=types.SimpleNamespace(**{k:scope[k] for k in selected})
        entries=outer_scope['_c23_canonical_entries'](T,policy,chain)
        self.assertEqual(len(entries),6)
        outer_tree=ast.parse(graph['root_c23_canonical_outer.py'])
        cls=next(n for n in outer_tree.body if isinstance(n,ast.ClassDef) and n.name=='OuterBindingV1')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_factory')
        windows=types.SimpleNamespace(WindowsNativeCustodyFacadeV1=lambda enabled:facade)
        def importer(name,*args,**kwargs):
            if name=='xar_autoplayer.bridge.native_loaded_provider_windows_v1':return windows
            return builtins.__import__(name,*args,**kwargs)
        factory_scope={**outer_scope,'__builtins__':dict(vars(builtins),__import__=importer)}
        exec(compile(ast.Module(body=[method],type_ignores=[]),'actual-Outer.prepare_factory','exec'),factory_scope)
        outer=types.SimpleNamespace(root=T,policy=policy,tools=lambda:chain)
        # Real controller method first invokes the original verifier; no process
        # creation/custody is attempted before it returns a valid factory.
        factory=factory_scope['prepare_factory'](outer,'d'*64)
        self.assertEqual(factory.entry_source_pins,entries);self.assertEqual(calls,[])
        holder=factory.pre_native_resume(object(),types.SimpleNamespace(dll_path='RAM/not-read.dll',pipe_name='RAM'))
        self.assertEqual(calls,['custody']);self.assertEqual(holder._entry_source_pins_v1,entries)
        suffix_max=0
        for role,name in [('owner','launch_sdk_p37c23_owner.py'),('Queue','root_p37c23_sdk_queue.py'),('MCPApp','root_p37c23_mcp_entry.py')]:
            command=[sys.executable,'-B','-S','-X','utf8',str(T/name)]
            plan=chain.prepare_child_v1(holder,role=role,command=command,env={'XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1':'1'},cwd=str(T),entry_source=str(T/name),enabled=True)
            suffix=plan.command[-1];suffix_max=max(suffix_max,len(suffix.encode()))
            self.assertLessEqual(len(suffix.encode()),16384)
            clean,hints=chain.consume_private_bootstrap_args_v1(list(plan.command),enabled=True)
            self.assertEqual(clean,command);self.assertEqual(hints['entry_sources'],[list(r) for r in entries])
            received,io,control=chain.receive_child_bootstrap_v1(hints,facade=facade,enabled=True)
            holder=received.holder
            self.assertEqual(holder._entry_source_pins_v1,entries)
            self.assertEqual(holder._creator_source_digest_v1,scope['_creator_digest'](entries))
        # These checks occur before another callback/create, not after a Game.
        for bad in [policy['entry_source_pins'],entries+entries[:3],[],entries[:-1]]:
            wrong=copy.deepcopy(policy);wrong['canonical_entry_source_pins']=bad
            outer.policy=wrong
            with self.assertRaises(ValueError):factory_scope['prepare_factory'](outer,'d'*64)
        wrong=copy.deepcopy(policy);wrong['canonical_entry_source_pins'][0][1]='0'*64;outer.policy=wrong
        with self.assertRaises(ValueError):factory_scope['prepare_factory'](outer,'d'*64)
        self.assertEqual(calls,['custody'])
        with self.assertRaises(ValueError):factory.pre_native_resume(object(),None)
        for bad in [policy['entry_source_pins'],entries+entries[:3]]:
            with self.assertRaises(ValueError):chain._verified_entry_sources(bad)
        with self.assertRaises(ValueError):chain.consume_private_bootstrap_args_v1(['python','--xar-private-preload','x'*16385],enabled=True)
        wrong=copy.deepcopy(hints);wrong['entry_sources']=policy['entry_source_pins']
        with self.assertRaises(ValueError):chain.receive_child_bootstrap_v1(wrong,facade=facade,enabled=True)
        # Original IO serializer limits are exercised with memory-only read/write.
        io_path=Path(policy['sdk_source_root'])/'xar_autoplayer/bridge/native_loaded_provider_origin_io_v1.py'
        io_tree=ast.parse(io_path.read_bytes());io_cls=next(n for n in io_tree.body if isinstance(n,ast.ClassDef) and n.name=='OriginKernelIOV1')
        io_methods=[n for n in io_cls.body if isinstance(n,ast.FunctionDef) and n.name in {'send','recv'}]
        io_scope={'json':json,'ctypes':ctypes,'time':time,'w':types.SimpleNamespace(DWORD=ctypes.c_uint32),'contract':contract}
        exec(compile(ast.Module(body=io_methods,type_ignores=[]),'actual-OriginIO.send.recv','exec'),io_scope)
        memory=types.SimpleNamespace(rx={},timeout=1,api=types.SimpleNamespace(_ok=lambda ok,why:p.require(ok,why)))
        memory._write=lambda h,raw,size,count,other:setattr(count._obj,'value',size) or True
        io_scope['send'](memory,1,hints)
        with self.assertRaises(ValueError):io_scope['send'](memory,1,{'x':'z'*16384})
        memory._peek=lambda h,a,b,c,count,d:setattr(count._obj,'value',16385) or True
        with self.assertRaises(ValueError):io_scope['recv'](memory,2)
        # The actual finite a02 guard binds the known failure, not a claim that
        # no suspended process was ever created. All inputs are existing small JSON.
        sup=graph['root_native30_supervisor_c23.py'];attempt_scope={'Path':Path,'hashlib':hashlib,'json':json,'re':__import__('re')}
        exec(compile(nodes(sup,['_validate_a02_attempt']),'actual-a02-admission','exec'),attempt_scope)
        prior=T.parent.parent/'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/C23-FIRST-SUPERVISOR-LAUNCH-FAILED-CLOSED.json'
        raw=prior.read_bytes();ref={'path':str(prior),'bytes':len(raw),'sha256':p.sha(raw)}
        args=types.SimpleNamespace(attempt='a02',attempt_nonce='2'*32)
        config={'cold_attempt':{'attempt_id':'a02','nonce':args.attempt_nonce,'execution_owner':'Root','root_direct_execution_release':True,'prior_failure':ref}}
        attempt_scope['_validate_a02_attempt'](args,config)
        config['cold_attempt']['root_direct_execution_release']=False
        with self.assertRaises(ValueError):attempt_scope['_validate_a02_attempt'](args,config)
        for name,raw in graph.items():self.assertNotIn(b'ROOT-FINAL-SDK-FREEZE-P37C23.json',raw)
        sup_text=sup.decode()
        for name in ['ROOT-SUPERVISOR-ADMITTED','ROOT-FRESH-PROFILE-PREPARED','ROOT-NATIVE30-GAME-ENVIRONMENT-BOUND','ROOT-SCREEN-KEEPER','ROOT-FRESH-SUPERVISOR-CLOSED']:
            self.assertIn(name+'-C23-A02.',sup_text)
        self.assertIn('ROOT-ACTUAL-GAME-LAUNCH-C23.json',sup_text)
        print('SOURCE_ONLY full44/required6 verified; factory->holder->three ChildPlans/hints/receivers exact; max8 and16KiB negatives refused; suffix_max_bytes='+str(suffix_max))


if __name__=='__main__':unittest.main(verbosity=2)
