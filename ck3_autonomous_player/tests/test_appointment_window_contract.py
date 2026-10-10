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

# These are offline DTO/driver boundary cases. The diagnostic ID below is
# synthetic and deliberately outside the existing candidate-pool fixture.
class CharacterNativeLevelContractTests(unittest.TestCase):
 DIAGNOSTIC_ID=0x0200007B
 DERIVED=('resource_extension_present','accumulated_raw','level_cap_raw',
          'native_level','title_tier','required_native_level','meets_native_level_floor')

 def request_fields(self,diagnostic_id=None):
  return contract.validate_request(11,native['requested_title_id'],0,1,
   native['breakdown_character_id'],self.DIAGNOSTIC_ID if diagnostic_id is None else diagnostic_id)

 def packet(self):
  value=copy.deepcopy(raw)
  value['title_appointment'].update({'diagnostic_character_id':self.DIAGNOSTIC_ID,
   'character_level_diagnostic':{'schema':'ck3-appointment-character-native-level-v1',
    'available':True,'character_id':self.DIAGNOSTIC_ID,
    'title_id':native['current_window_title_id'],'native_level_source_ordinal':0,
    'unavailable_reason':None,'resource_extension_present':True,
    'accumulated_raw':200000,'level_cap_raw':-1,'native_level':2,'title_tier':4,
    'required_native_level':2,'meets_native_level_floor':True}})
  return value

 def normalize(self,value,request_fields=None):
  return contract.normalize_result(value,fields=self.request_fields() if request_fields is None else request_fields,
   native_revision=77,date_raw=45,actor_id=12)

 def unavailable_packet(self,ordinal=1):
  value=self.packet();diagnostic=value['title_appointment']['character_level_diagnostic']
  diagnostic.update({'available':False,'native_level_source_ordinal':ordinal,
   'unavailable_reason':'synthetic_unsupported_level_source'})
  diagnostic.update(dict.fromkeys(self.DERIVED))
  return value

 def test_diagnostic_outside_pool_is_independent_of_breakdown(self):
  value=self.packet();result=self.normalize(value)['title_appointment']
  self.assertNotIn(self.DIAGNOSTIC_ID,[candidate['character_id'] for candidate in result['candidates']])
  self.assertNotEqual(self.DIAGNOSTIC_ID,result['breakdown_character_id'])
  self.assertEqual(self.request_fields()['diagnostic_character_id'],self.DIAGNOSTIC_ID)
  self.assertEqual(result['character_level_diagnostic']['character_id'],self.DIAGNOSTIC_ID)
  self.assertEqual(result['candidates'],native['candidates'])
  self.assertEqual(result['breakdown'],native['breakdown'])
  self.assertIsNot(result['character_level_diagnostic'],value['title_appointment']['character_level_diagnostic'])

 def test_driver_forwards_independent_diagnostic_id_through_common_mailbox(self):
  packet=self.packet()
  class DiagnosticDriver(Driver):
   def _execute_primitive_step(self,step,**kwargs):
    self.calls.append((step,kwargs));return copy.deepcopy(packet)
  driver=DiagnosticDriver()
  result=driver.query_current_title_appointment_v1(expected_revision=11,
   requested_title_id=native['requested_title_id'],candidate_limit=1,
   breakdown_character_id=native['breakdown_character_id'],diagnostic_character_id=self.DIAGNOSTIC_ID)
  step,kwargs=driver.calls[0]
  self.assertEqual(step,'query-ingame-ui-window-v1')
  self.assertEqual(kwargs['required_capability'],contract.CAPABILITY)
  self.assertEqual(kwargs['request_fields']['diagnostic_character_id'],self.DIAGNOSTIC_ID)
  self.assertEqual(kwargs['request_fields']['breakdown_character_id'],native['breakdown_character_id'])
  self.assertEqual(result['queried_connection_generation'],5)

 def test_diagnostic_request_rejects_noninteger_and_invalid_full_ids(self):
  for value in (True,False,1.0,'1',0,-1,2**32-1):
   with self.subTest(value=value,type=type(value).__name__),self.assertRaises(ValueError):
    self.request_fields(value)

 def test_diagnostic_request_echo_full_id_and_title_must_match(self):
  for value in (0,self.DIAGNOSTIC_ID+1):
   packet=self.packet();packet['title_appointment']['diagnostic_character_id']=value
   with self.subTest(echo=value),self.assertRaises(ValueError):self.normalize(packet)
  for key,values in (('character_id',(self.DIAGNOSTIC_ID+1,True,float(self.DIAGNOSTIC_ID),str(self.DIAGNOSTIC_ID))),
                     ('title_id',(native['requested_title_id'],True,float(native['current_window_title_id']),str(native['current_window_title_id'])))):
   for value in values:
    packet=self.packet();packet['title_appointment']['character_level_diagnostic'][key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.normalize(packet)

 def test_requested_diagnostic_requires_typed_payload(self):
  for value in (None,[],True,'diagnostic'):
   packet=self.packet();packet['title_appointment']['character_level_diagnostic']=value
   with self.subTest(value=value),self.assertRaises(ValueError):self.normalize(packet)
  for key,value in (('schema','unknown'),('available',1),('available',None)):
   packet=self.packet();packet['title_appointment']['character_level_diagnostic'][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.normalize(packet)

 def test_unavailable_diagnostic_preserves_null_derived_fields(self):
  for ordinal in (None,1):
   with self.subTest(ordinal=ordinal):
    diagnostic=self.normalize(self.unavailable_packet(ordinal))['title_appointment']['character_level_diagnostic']
    self.assertFalse(diagnostic['available'])
    for name in self.DERIVED:self.assertIsNone(diagnostic[name])
    self.assertEqual(diagnostic['character_id'],self.DIAGNOSTIC_ID)

 def test_unavailable_diagnostic_rejects_derived_data_or_missing_reason(self):
  for name in self.DERIVED:
   packet=self.unavailable_packet();packet['title_appointment']['character_level_diagnostic'][name]=0
   with self.subTest(field=name),self.assertRaises(ValueError):self.normalize(packet)
  for value in (None,'',False):
   packet=self.unavailable_packet();packet['title_appointment']['character_level_diagnostic']['unavailable_reason']=value
   with self.subTest(reason=value),self.assertRaises(ValueError):self.normalize(packet)

 def test_available_diagnostic_rejects_unsupported_or_invalid_ordinal(self):
  for ordinal in (None,1,255,True,0.0,'0',-1,256):
   packet=self.packet();packet['title_appointment']['character_level_diagnostic']['native_level_source_ordinal']=ordinal
   with self.subTest(ordinal=ordinal,type=type(ordinal).__name__),self.assertRaises(ValueError):self.normalize(packet)

 def test_null_resource_extension_has_zero_level_and_null_raw_data(self):
  packet=self.packet();packet['title_appointment']['character_level_diagnostic'].update({
   'resource_extension_present':False,'accumulated_raw':None,'level_cap_raw':None,
   'native_level':0,'required_native_level':0,'meets_native_level_floor':True})
  result=self.normalize(packet)['title_appointment']['character_level_diagnostic']
  self.assertIsNone(result['accumulated_raw']);self.assertIsNone(result['level_cap_raw'])
  self.assertEqual(result['native_level'],0)
  for key,value in (('accumulated_raw',0),('level_cap_raw',0),('native_level',1)):
   invalid=copy.deepcopy(packet);invalid['title_appointment']['character_level_diagnostic'][key]=value
   with self.subTest(field=key),self.assertRaises(ValueError):self.normalize(invalid)

 def test_native_level_floor_comparison_matches_including_equality(self):
  for level,floor,meets in ((1,2,False),(2,2,True),(3,2,True),(0,-1,True)):
   packet=self.packet();packet['title_appointment']['character_level_diagnostic'].update({
    'native_level':level,'required_native_level':floor,'meets_native_level_floor':meets})
   with self.subTest(level=level,floor=floor):
    result=self.normalize(packet)['title_appointment']['character_level_diagnostic']
    self.assertIs(result['meets_native_level_floor'],meets)
    for invalid_meets in (not meets,0,1,None):
     invalid=copy.deepcopy(packet);invalid['title_appointment']['character_level_diagnostic']['meets_native_level_floor']=invalid_meets
     with self.subTest(invalid=invalid_meets,type=type(invalid_meets).__name__),self.assertRaises(ValueError):self.normalize(invalid)

 def test_available_diagnostic_numeric_types_and_ranges_are_strict(self):
  for name in ('accumulated_raw','level_cap_raw','native_level','title_tier','required_native_level'):
   for value in (True,False,1.0,'1',None):
    packet=self.packet();packet['title_appointment']['character_level_diagnostic'][name]=value
    with self.subTest(field=name,value=value,type=type(value).__name__),self.assertRaises(ValueError):self.normalize(packet)
  for name,value in (('accumulated_raw',2**63),('level_cap_raw',2**31),
                     ('native_level',257),('native_level',-1),('title_tier',7),
                     ('required_native_level',-2**31-1),('resource_extension_present',0)):
   packet=self.packet();packet['title_appointment']['character_level_diagnostic'][name]=value
   with self.subTest(field=name,value=value),self.assertRaises(ValueError):self.normalize(packet)

 def test_candidate_tier_extension_preserves_source17_and_level_floor(self):
  legacy=self.packet()
  self.assertEqual(self.normalize(legacy)['title_appointment']['character_level_diagnostic'],
                   legacy['title_appointment']['character_level_diagnostic'])
  extended=copy.deepcopy(legacy)
  observed=extended['title_appointment']['character_level_diagnostic']
  observed.update(current_rule_allowed_candidate_tier_ordinal=1,candidate_tier=5)
  result=self.normalize(extended)['title_appointment']['character_level_diagnostic']
  self.assertEqual(result,observed)
  for name in self.DERIVED:
   self.assertEqual(result[name],legacy['title_appointment']['character_level_diagnostic'][name])
  self.assertNotIn('eligible',result)

 def test_candidate_tier_extension_rejects_partial_and_unavailable_data(self):
  keys=('current_rule_allowed_candidate_tier_ordinal','candidate_tier')
  for key in keys:
   packet=self.packet();packet['title_appointment']['character_level_diagnostic'][key]=1
   with self.subTest(partial=key),self.assertRaises(ValueError):self.normalize(packet)
  unavailable=self.unavailable_packet()
  unavailable['title_appointment']['character_level_diagnostic'].update(dict.fromkeys(keys))
  self.assertFalse(self.normalize(unavailable)['title_appointment']['character_level_diagnostic']['available'])
  for key in keys:
   invalid=copy.deepcopy(unavailable);invalid['title_appointment']['character_level_diagnostic'][key]=0
   with self.subTest(unavailable=key),self.assertRaises(ValueError):self.normalize(invalid)
  for key,values in ((keys[0],(True,1.0,'1',None,-1,256)),
                     (keys[1],(True,1.0,'5',None,-1,7))):
   for value in values:
    packet=self.packet();diagnostic=packet['title_appointment']['character_level_diagnostic']
    diagnostic.update(zip(keys,(1,5)));diagnostic[key]=value
    with self.subTest(field=key,value=value),self.assertRaises(ValueError):self.normalize(packet)

 def test_legacy_omitted_diagnostic_fields_remain_compatible(self):
  legacy_fields=contract.validate_request(11,native['requested_title_id'],0,1,native['breakdown_character_id'])
  self.assertEqual(legacy_fields['diagnostic_character_id'],0)
  self.assertNotIn('diagnostic_character_id',raw['title_appointment'])
  self.assertNotIn('character_level_diagnostic',raw['title_appointment'])
  self.assertEqual(self.normalize(copy.deepcopy(raw),legacy_fields)['title_appointment'],native)
  explicit=copy.deepcopy(raw);explicit['title_appointment'].update({
   'diagnostic_character_id':0,'character_level_diagnostic':None})
  self.assertIsNone(self.normalize(explicit,legacy_fields)['title_appointment']['character_level_diagnostic'])
  unrequested=self.packet();unrequested['title_appointment']['diagnostic_character_id']=0
  with self.assertRaises(ValueError):self.normalize(unrequested,legacy_fields)

if __name__=='__main__': unittest.main()
