"""Focused offline source-binding guards; no game/consumption acceptance."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r10_offline_flow',ROOT/'prepare_r10_join_flow.py')
flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)

class Guards(unittest.TestCase):
    def setUp(self):self.template=json.loads((ROOT/'R10-PREPARATION-REQUEST.template.json').read_bytes())

    def test_future_inputs_remain_null(self):
        pending=flow.shape(self.template)
        self.assertIn('source_revision',pending);self.assertIn('process_identity.process_create_filetime',pending)
        self.assertIn('source_ready.provider.path',pending);self.assertIn('current_query_sdk.path',pending)
        with self.assertRaisesRegex(ValueError,'remain NULL'):flow.validate(self.template)

    def test_caller_release_boolean_rejected(self):
        self.template['consumed']=True
        with self.assertRaisesRegex(ValueError,'closed R10'):flow.shape(self.template)

    def test_old_r9_head_cannot_qualify_new_source(self):
        request={key:1 for key in flow.FIELDS};request['schema']=self.template['schema'];request['source_revision']=flow.OLD_HEAD
        request.update(native_result=None,unknown=None,first_query_frame_sdk=None,current_query_frame_sdk=None)
        with self.assertRaisesRegex(ValueError,'new reviewed R10 HEAD'):flow.validate(request)

    def test_duplicate_json_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):flow.jread(b'{"source_revision":null,"source_revision":"new"}')

    def test_immutable_reference_sha_mismatch(self):
        ref={'path':str(ROOT/'R10-PREPARATION-REQUEST.template.json'),'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'immutable bytes differ'):flow.readref(ref,{})

    def test_original_consumption_functions_are_the_ast_baseline(self):
        constants=flow.unchanged_consumption_functions(flow.BASE_PROVIDER.read_bytes())
        self.assertIsNone(constants['PINNED_ROOT_BINDING'])

    def test_removing_fresh_cansend_changes_protected_function(self):
        tree=ast.parse(flow.BASE_PROVIDER.read_bytes())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='actual_query')
        node.body=[ast.Return(value=ast.Constant(value=True))]
        with self.assertRaisesRegex(ValueError,'functions changed'):flow.unchanged_consumption_functions(ast.unparse(tree).encode())

    def test_epoch_unlock_function_cannot_replace_actual_consumption(self):
        tree=ast.parse(flow.BASE_PROVIDER.read_bytes())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_verify')
        node.body=[ast.Return(value=ast.Constant(value=True))]
        with self.assertRaisesRegex(ValueError,'functions changed'):flow.unchanged_consumption_functions(ast.unparse(tree).encode())

    def test_changed_key_or_prebound_process_rejected(self):
        for key,value in [('KEY','different_interaction'),('PINNED_ROOT_BINDING',{'epoch':'new'})]:
            tree=ast.parse(flow.BASE_PROVIDER.read_bytes())
            node=next(n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id==key)
            node.value=ast.parse(repr(value),mode='eval').body
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'protected provider constant'):flow.unchanged_consumption_functions(ast.unparse(tree).encode())

    def test_episode_is_not_a_seventh_stable_identity(self):
        value={name:1 for name in flow.IDENTITY_FIELDS};value['episode_run_id']='new'
        with self.assertRaisesRegex(ValueError,'six stable'):flow.exact(value,flow.IDENTITY_FIELDS,'six stable once identity')

    def test_filetime_bool_missing_and_wrong_actual_receipt_rejected(self):
        value={'game_pid':991,'process_create_time':1791179349.2116988,'process_create_filetime':134356529492116988,
            'receipt':{'path':'offline-unused','sha256':'0'*64},'receipt_fields':{k:'/target/'+k for k in ('game_pid','process_create_time','process_create_filetime')}}
        receipt={'target':{k:value[k] for k in value['receipt_fields']}}
        self.assertEqual(flow.process_values(value,receipt),value) # Synthetic metadata-only positive.
        changed=copy.deepcopy(value);changed['process_create_filetime']=True
        with self.assertRaisesRegex(ValueError,'FILETIME'):flow.process_values(changed,receipt)
        for item in ({'target':{'game_pid':991,'process_create_time':value['process_create_time']}},
                     {'target':dict(receipt['target'],process_create_filetime=value['process_create_filetime']+1)}):
            with self.assertRaises(ValueError):flow.process_values(value,item)

    def test_unknown_sdk_and_nonfinite_process_never_success(self):
        fixture=ROOT/'offline-sdk-red.fixture.json'
        ref={'path':str(fixture),'sha256':hashlib.sha256(fixture.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(ValueError,'error/unknown'):flow.sdk(ref,{})
        with self.assertRaises(ValueError):flow.jread(b'{"process_create_time":NaN}')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Guards)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'schema':'ck3-r10-flow-focused-offline-tests-v1','tests_run':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'scope':'source-binding/immutable-reference negative controls only',
        'synthetic_metadata_only':True,'actual_R10_source_ready':None,'actual_consumption_verified':False,
        'binder_executed':False,'registry_enabled':False,'host_release_called':False,'MCP_calls':0}
    with (ROOT/'FOCUSED-TEST-RESULT-002.json').open('x',encoding='utf-8',newline='\n') as file:json.dump(report,file,indent=2);file.write('\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
