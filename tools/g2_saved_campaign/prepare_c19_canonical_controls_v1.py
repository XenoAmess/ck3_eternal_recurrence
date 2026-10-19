"""Future C19 true-custody outer graph; pure in-memory, no deployment API.

Public composition requires the independently qualified Native transition.
Private fixture composition proves Python seams only, never actual Native/H.
"""
import ast,hashlib,importlib,sys
from pathlib import Path

import prepare_canonical_c17_outer_sources_v1 as canonical
import prepare_full_batch_timing_sources_v1 as timing

OWN=Path(__file__).resolve().parent
T=timing.T
MACHINE='xenoamess-full-tower-eb9d2c1186'
NATIVE_TRANSITION_SHA='76b1cc507f2d9600c01d0961c214bd3b9110c26c0784608b27a3ef428610a9e2'
NATIVE_TOOLS={
 'native29_to30_export_contract_v1.py':NATIVE_TRANSITION_SHA,
 'export_native30_immutable_sdk_views_v1.py':'edbe75a62f80d17a0e74998b96834844bcbf75f1caab7ea5468b3caa32dbb709',
 'native30_resume_fixture_chain_v1.py':'d9e5dc3c22f3b1fc58f1ab7b93de4f7ccb480c3ed938fdc6b2375d11a814f555',
 'native30_export_adapter_v1.py':'2d4074379371ed91bc38ff0fc532521e277ba2795faad1fd8e9c6dd2593c5298'}
BUSINESS_PLAN=OWN.parent.parent/'docs/ck3-native-ai/evidence/c19-combined-cold-sdk-source-plan-2026-10-20.json'
BUSINESS_PLAN_SHA='c2e58f17950012ec8717fef262a590b26a117e7523080c179128ba79995a7a84'
PAIR_REF={'path':str(T/'ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37C18.json'),'bytes':464,
 'sha256':'7d4837eaac0c9f09999417641deba18d4e2796e6ef7f96731e37ca13aa404a6a'}
OLD_GAME={'pid':30852,'creation_filetime':134368995759027619}
PINS={
 'prepare_canonical_c17_outer_sources_v1.py':'e0713f8a56e3a2be280d140d4f3246d35af84222990bc353d6b268a7d1049ffe',
 'canonical_c17_outer_binding_v1.py':'e4d45ed0e48f8ed9d30269592bcde5cc64948e983b194320a286316e20a1300a',
 'c17_normal_checkpoint_inputs_v1.py':'bb1ea3b4ec49a96b62d90883477c21d5124214caff030d36198606b8adb03154',
 'prepare_full_batch_timing_sources_v1.py':'112d4154a4ac39261749c2be0be0097f1b8c188b7905cbd97091dc89765ef1a8',
 'full_batch_timing_v1.py':'197e4308b7d0f5a70a8c3474ec0b58581997f3e60bfc2d8414c668dae07c8e0b',
 'full_lifecycle_timing_v1.py':'dcbb92b3852123a24dac29f35f182eea6a731a46104d1837478c2990052a32ca'}
MAP=[('P37C17','P37C19'),('p37c17','p37c19'),('_c17','_c19'),('-C17','-C19'),
 ('SDKC17','SDKC19'),('xar.c17.','xar.c19.'),('C17-canonical-origin','C19-canonical-origin'),
 ('C17-CANONICAL-OWNER','C19-CANONICAL-OWNER'),('ROOT-C17-SDKOWNER','ROOT-C19-SDKOWNER'),
 ('C17 canonical outer binding denied','C19 canonical outer binding denied'),('C17 normal checkpoint input denied','C19 normal checkpoint input denied'),
 ('root_c17_canonical_outer','root_c19_canonical_outer'),('root_c17_normal_checkpoint_inputs','root_c19_normal_checkpoint_inputs'),
 ('EXACT_C16_NORMAL_CHECKPOINT_FOR_C17','EXACT_C18_NORMAL_CHECKPOINT_FOR_C19'),
 ('EXACT_C16_NORMAL_CHECKPOINT_FOR_C19','EXACT_C18_NORMAL_CHECKPOINT_FOR_C19')]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,why):
 if not ok:raise ValueError('C19 canonical source denied: '+why)


def source_inputs():
 for name,digest in PINS.items():require(sha((OWN/name).read_bytes())==digest,'frozen source changed: '+name)
 import json
 raw=BUSINESS_PLAN.read_bytes();require(sha(raw)==BUSINESS_PLAN_SHA,'complete then-source15 SDK composition plan changed')
 plan=json.loads(raw)
 require(plan['machine_id']==MACHINE and plan['output']['complete_manifest']['file_count']==1454
  and plan['base']['business_commit']=='0e8a190bf3e5ec187e7bc30d76310585922a0b50'
  and plan['base']['family_fix']['sha256']=='d8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf',
  'whole then-source15 SDK/family baseline differs')


def port_name(name):
 for old,new in MAP:name=name.replace(old,new)
 return name


def port_source(source):
 # Existing reviewed port edits actual AST string/import/name spans and checks
 # its inverse. It protects machine/episode/hash constants from bare replacement.
 return canonical.prior.prior.port(source,MAP)


def _swap(text,old,new,records):
 require(text.count(old)==1,'unique C19 outer seam missing: '+old[:80]);records.append((old,new))
 return text.replace(old,new,1)


def outer_helper(source):
 text=source;records=[]
 old='        self.owner = self.server_thread = None\n'
 new='''        self.wal_enabled = self.policy.get('enable_driver_state_wal_v1', False)
        require(type(self.wal_enabled) is bool, 'WAL policy requires an explicit boolean')
        self.owner = self.server_thread = None
'''
 text=_swap(text,old,new,records)
 old="        env['PYTHONDONTWRITEBYTECODE'] = '1'\n        return env\n"
 new="""        env['PYTHONDONTWRITEBYTECODE'] = '1'
        if self.wal_enabled:
            env['XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1'] = '1'
        else:
            env.pop('XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1', None)
        return env
"""
 text=_swap(text,old,new,records)
 old='''            self.factory.origin.revoke_before_close()
            self.revoked = True
'''
 new='''            self.factory.origin.revoke_before_close()
            if self.server_thread is not None:
                self.server_thread.join(timeout=10)
                require(not self.server_thread.is_alive(),
                    'origin server join unproved; retain custody and do not close the holder')
            self.revoked = True
'''
 text=_swap(text,old,new,records)
 inverse=text
 for old,new in reversed(records):inverse=inverse.replace(new,old,1)
 require(inverse==source,'unreviewed canonical helper change')
 return text,records


def _current_pair():
 import json
 raw=Path(PAIR_REF['path']).read_bytes()
 require(len(raw)==PAIR_REF['bytes'] and sha(raw)==PAIR_REF['sha256'],'actual C18 creator pair changed')
 pair=json.loads(raw)
 require(pair['application_creator']=='actual_mcp_stdio_factory_return' and len(pair['processes'])==2,'actual creator pair required')
 values={(r['role'],r['pid'],r['creation_filetime']) for r in pair['processes']}
 require(values=={('sdk_queue',153792,134369092460097880),('sdk_application',64328,134369092487102977)},'actual C18 pair differs')
 return values


def _normal_inputs(source):
 tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OLD_PAIR' for t in n.targets))
 old=ast.get_source_segment(source,node);new='OLD_PAIR = {'+', '.join(repr(row) for row in sorted(_current_pair()))+'}'
 require(old is not None and source.count(old)==1,'normal old-pair constant unavailable')
 result=source.replace(old,new,1)
 require(result.replace(new,old,1)==source,'normal guard inverse differs')
 return result


def assert_true_graph(graph):
 expected={
 'root_native30_supervisor_c19.py':'prepare_supervisor',
 'launch_sdk_p37c19_owner.py':'receive_entry',
 'root_p37c19_sdk_queue.py':'receive_entry',
 'root_p37c19_mcp_entry.py':'receive_entry'}
 for name,function in expected.items():
  calls=[n for n in ast.walk(ast.parse(graph[name])) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==function]
  require(len(calls)==1 and any(k.arg=='enabled' and isinstance(k.value,ast.Constant) and k.value.value is True for k in calls[0].keywords),
   'false/missing canonical entry: '+name)
 queue=graph['root_p37c19_sdk_queue.py'].decode();app=graph['root_p37c19_mcp_entry.py'].decode()
 require('owned_stdio(_canonical, stdio,' in queue and '_canonical.install_service(service)' in app,'actual owner/Queue/stock App chain omitted')
 require('canonical.factory.pre_native_resume' in graph['root_native30_supervisor_c19.py'].decode(),'same factory pre-native hook omitted')


def _compose_source_candidate(label,*,full_timing=True):
 """Private detached-source path; caller must not treat fixture label as qualified."""
 source_inputs();require(type(full_timing) is bool,'explicit FULL timing boolean required')
 original,old_records=canonical.build_sources(enabled=True,native_build_label=label)
 # Never call timing.build_sources(): it builds a different, disabled graph.
 graph={port_name(name):port_source(raw.decode()).encode() for name,raw in original.items()}
 records={}
 helper='root_c19_canonical_outer.py'
 graph[helper],records[helper]=outer_helper(graph[helper].decode());graph[helper]=graph[helper].encode()
 normal='root_c19_normal_checkpoint_inputs.py';graph[normal]=_normal_inputs(graph[normal].decode()).encode()
 assert_true_graph(graph)
 queue='root_p37c19_sdk_queue.py';handoff='root_p37c19_automatic_natural_succession_handoff.py'
 graph[queue],records[queue]=timing.transform_queue(graph[queue],enabled=full_timing)
 old="admission_getter=lambda queue: queue._normal_cold['admission'].get('control_timing')"
 new='admission_getter=lambda queue: None'
 text=_swap(graph[queue].decode(),old,new,records[queue]);graph[queue]=text.encode()
 graph[handoff],records[handoff]=timing.transform_handoff(graph[handoff])
 # Timing-only feeder candidate is deliberately separate from the adopted
 # controls graph. The then-actual C19 cold admission cannot be invented now.
 feeder=(T/timing.FEEDER).read_bytes();require(sha(feeder)==timing.FEEDER_SHA,'frozen feeder changed')
 feeder=port_source(feeder.decode()).encode()
 feeder_candidate,records['unapplied_C19_feeder_timing']=timing.transform_feeder(feeder,enabled=full_timing)
 for name in ('full_batch_timing_v1.py','full_lifecycle_timing_v1.py'):graph[name]=(OWN/name).read_bytes()
 assert_true_graph(graph)
 for name,raw in graph.items():compile(raw,name,'exec')
 masks=[n for n in ast.walk(ast.parse(graph['root_p37c19_cold_resume.py'])) if isinstance(n,ast.Assign)
  and any(isinstance(t,ast.Attribute) and t.attr=='flags' for t in n.targets) and isinstance(n.value,ast.ListComp)
  and any(isinstance(c,ast.Constant) and c.value=='--private-active-scheme-sway-completion-execution-query' for c in ast.walk(n.value))]
 require(len(masks)==1,'Native30 unsupported execution-query mask lost')
 policy_entries=tuple((str(T/name),sha(raw)) for name,raw in sorted(graph.items()))
 return graph,dict(source_only=True,source_fixture=True,outputs_materialized=False,canonical_enabled=True,FULL_wall_and_rows=full_timing,
  control_probe_enabled=False,WAL_policy_default=False,WAL_requested_policy={'enable_driver_state_wal_v1':True},
  entry_source_pins_after_all_edits=policy_entries,actual_C18_pair=PAIR_REF,
  old_Game=OLD_GAME,normal_closure_kind='EXACT_C18_NORMAL_CHECKPOINT_FOR_C19',
  original_outer_hunks_reused={n:len(v) for n,v in old_records.items()},new_seams={n:len(v) for n,v in records.items()},
  unapplied_feeder_timing={'bytes':len(feeder_candidate),'sha256':sha(feeder_candidate),
   'not_an_admitted_cold_feeder':True,'source_baseline':timing.FEEDER_SHA},
  business_plan={'path':str(BUSINESS_PLAN),'sha256':BUSINESS_PLAN_SHA,
   'complete_files':1454,'rows_sha256':'a91c8952d863eafbf433b1aa4fedec5ad42f8edfe0da4f14a3b29de972649b10',
   'actual_H':'unknown'},
  remaining=['future Native30 actual qualification transition and exact export card',
   'then-current SAVE/clean seed/normal C18 SDK+Game+record+publisher closure',
   'new Game launch/record/Root pixels; never reuse C16 PID/UUID facts',
   'final C19 cold feeder admission and launcher lineage; current warm admission is not cold authority'])


def _qualified_label(transition):
 require(transition.source_fixture is False,'fixture transition cannot create an adopted graph')
 label=transition.target_native['native_build_label']
 require(isinstance(label,str) and label.startswith('Native30 ')
  and not any(x in label.upper() for x in ('UNQUALIFIED','SOURCE-ONLY','PLACEHOLDER')),
  'qualified Native30 full label required')
 return label


def build_sources(*,native_transition_inputs=None,canonical_enabled=True,full_timing=True):
 """Qualified future source only. No D writer; placeholders and fixture proof fail."""
 require(canonical_enabled is True,'canonical custody cannot be disabled for this graph')
 require(isinstance(native_transition_inputs,dict) and set(native_transition_inputs)==
  {'base_freeze_ref','base_native_ref','capacity_ref','machine_id'},'future true-qualified Native transition references required')
 require(native_transition_inputs['machine_id']==MACHINE,'Native transition machine differs')
 for name,digest in NATIVE_TOOLS.items():
  path=OWN/name;require(sha(path.read_bytes())==digest,'frozen Native transition import changed: '+name)
  for cached_name in (Path(name).stem,'g2_saved_campaign.'+Path(name).stem):
   prior=sys.modules.get(cached_name)
   require(prior is None or Path(prior.__file__).resolve()==path.resolve(),'foreign cached Native transition import')
 path=OWN/'export_native30_immutable_sdk_views_v1.py'
 module=importlib.import_module('export_native30_immutable_sdk_views_v1')
 require(Path(module.__file__).resolve()==path.resolve(),'foreign Native transition module')
 for name in NATIVE_TOOLS:
  for module_name in (Path(name).stem,'g2_saved_campaign.'+Path(name).stem):
   loaded=sys.modules.get(module_name)
   require(loaded is None or Path(loaded.__file__).resolve()==(OWN/name).resolve(),
    'Native transition dependency imported from a foreign package')
 transition=module.read_native_transition_v1(**native_transition_inputs,source_fixture=False)
 for name in NATIVE_TOOLS:
  for module_name in (Path(name).stem,'g2_saved_campaign.'+Path(name).stem):
   loaded=sys.modules.get(module_name)
   require(loaded is None or Path(loaded.__file__).resolve()==(OWN/name).resolve(),
    'Native transition lazy dependency imported from a foreign package')
 label=_qualified_label(transition)
 graph,report=_compose_source_candidate(label,full_timing=full_timing)
 report.update(source_only=True,source_fixture=False,native_transition_metadata=transition.manifest_metadata,
  actual_runtime_admitted=False,Game_Native_MCP_Task_calls=0,external_writes=0)
 return graph,report
