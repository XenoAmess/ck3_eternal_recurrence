"""Preserved eight offline provider checks; native wire is a synthetic reader fixture."""
from pathlib import Path
import ast,copy,importlib.util,json,sys,types,unittest
BASE=Path(__file__).resolve().parents[1]
P=BASE/'src/xar_autoplayer/bridge'
spec=importlib.util.spec_from_file_location('appointment_window_contract',P/'appointment_window_contract.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
native_source=Path(__file__).parent/'fixtures/appointment_window_snapshot_v1_synthetic.json'
native=json.loads(native_source.read_text())
raw={'schema':'ck3-ingame-ui-window-v1','accepted':True,'available':True,'status':'observed',
 'window_kind':'title_appointment','window_name':'title_appointment','window_exists':True,'effective_visible':True,
 'enabled':True,'dispatch_invoked':False,'verification_pending':False,'paused':True,'native_revision':77,'date_raw':45,
 'played_character_id':12,'application_owner_thread_verified':True,'gui_owner_binding_verified':True,
 'game_version':'1.20.0.4','executable_sha256':contract.EXE_SHA256,'pump_epoch':100,'thread_id':51,
 'subject_id_available':True,'current_subject_id':native['current_window_title_id'],
 'owner_character_id_available':True,'owner_character_id':native['current_holder_character_id'],'title_appointment':native}
fields=contract.validate_request(11,native['requested_title_id'],0,1,native['breakdown_character_id'])
def normalized(value):return contract.normalize_result(value,fields=fields,native_revision=77,date_raw=45,actor_id=12)
parsed={}
for file in [P/name for name in ('appointment_window_contract.py','native_driver.py','service.py','mcp_server.py')]:
 source=file.read_text(encoding='utf-8');tree=ast.parse(source);compile(tree,str(file),'exec');parsed[file.name]=tree

# Execute the actual new driver method AST with explicit offline doubles for
# pre-existing mailbox/snapshot dependencies. No service or game is started.
method=next(n for n in ast.walk(parsed['native_driver.py']) if isinstance(n,ast.FunctionDef) and n.name=='query_current_title_appointment_v1')
module=ast.Module(body=[copy.deepcopy(method)],type_ignores=[]);ast.fix_missing_locations(module)
class Unavailable(RuntimeError):pass
pkg=types.ModuleType('appointment_offline');pkg.__path__=[];sys.modules[pkg.__name__]=pkg
sys.modules['appointment_offline.appointment_window_contract']=contract
ui=types.ModuleType('appointment_offline.ingame_ui_contract')
identity=types.SimpleNamespace(game_version='1.20.0.4',executable_sha256=contract.EXE_SHA256)
ui.ingame_ui_build_binding=lambda s:(identity,True)
sys.modules[ui.__name__]=ui
ns={'__package__':'appointment_offline','copy':copy,'BridgeUnavailableError':Unavailable,
 'PreSubmissionRevisionMismatchError':Unavailable,'UnsupportedStepError':Unavailable,
 '_title_camera_navigation_binding_from_snapshot':lambda s:{'connection_generation':s['generation']},
 '_same_paused_native_frame':lambda a,b: all(a[k]==b[k] for k in ('paused','date_raw','native_revision'))}
exec(compile(module,str(P/'native_driver.py'),'exec'),ns)
class Driver:
 query_current_title_appointment_v1=ns['query_current_title_appointment_v1']
 def __init__(self):self.calls=[];self.snapshots=0;self.changed=False
 def take_snapshot(self):
  self.snapshots+=1
  return {'paused':True,'map_ready':True,'revision':11,'native_revision':77,'date_raw':45,
   'played_character':{'character_id':12},'generation':6 if self.changed and self.snapshots>1 else 5}
 def _execute_primitive_step(self,step,**kwargs):
  self.calls.append((step,kwargs));return copy.deepcopy(raw)
 def _record_command(self,*args,**kwargs):self.calls.append((args,kwargs))

class ContractTests(unittest.TestCase):
 def test_native_compiled_wire(self):
  self.assertEqual(normalized(raw)['title_appointment']['resolved_title_id'],native['current_window_title_id'])
 def test_driver_exact_common_mailbox(self):
  d=Driver();v=d.query_current_title_appointment_v1(expected_revision=11,requested_title_id=native['requested_title_id'],candidate_limit=1,breakdown_character_id=native['breakdown_character_id'])
  self.assertEqual(d.calls[0][0],'query-ingame-ui-window-v1');self.assertEqual(d.calls[0][1]['required_capability'],contract.CAPABILITY)
  self.assertEqual(v['queried_connection_generation'],5)
 def test_driver_session_change_rejected(self):
  d=Driver();d.changed=True
  with self.assertRaises(Unavailable):d.query_current_title_appointment_v1(expected_revision=11,requested_title_id=native['requested_title_id'],candidate_limit=1,breakdown_character_id=native['breakdown_character_id'])
 def test_input_validation(self):
  for values in ((True,None,0,1,None),(1,2**32-1,0,1,None),(1,None,0,65,None),(1,None,-1,1,None)):
   with self.assertRaises(ValueError):contract.validate_request(*values)
 def test_negative_packets(self):
  mutations=[('native_revision',78),('application_owner_thread_verified',False),('effective_visible',False),('dispatch_invoked',True),('current_subject_id',native['requested_title_id'])]
  for key,value in mutations:
   v=copy.deepcopy(raw);v[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):normalized(v)
 def test_candidate_negative_packets(self):
  for key,value in (('character_id',True),('is_ai',None),('is_ai',False),('score_raw',True),('candidate_pool_member',False)):
   v=copy.deepcopy(raw);v['title_appointment']['candidates'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):normalized(v)
 def test_scope_pool_and_breakdown_negative_packets(self):
  for key,value in (('source_pool_count',1),('group_first_title_id',native['requested_title_id']),('requested_resolves_to_current',False),('score_fixed_point_scale',1000),('next_offset',2)):
   v=copy.deepcopy(raw);v['title_appointment'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):normalized(v)
  v=copy.deepcopy(raw);v['title_appointment']['breakdown']['value_raw']=1
  with self.assertRaises(ValueError):normalized(v)
 def test_mcp_and_service_method_exist(self):
  self.assertEqual(sum(isinstance(n,ast.FunctionDef) and n.name=='ck3_query_current_title_appointment_v1' for n in ast.walk(parsed['mcp_server.py'])),1)
  self.assertEqual(sum(isinstance(n,ast.FunctionDef) and n.name=='query_current_title_appointment_v1' for n in ast.walk(parsed['service.py'])),1)

if __name__=='__main__': unittest.main()
