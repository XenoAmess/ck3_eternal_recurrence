from pathlib import Path
from contextlib import contextmanager
import importlib.util
import json
import sys
import unittest
BASE=Path(__file__).parent.parent
sys.path.insert(0,str(BASE))
ENTRY=BASE/'resume_project_exe_broker.py'
spec=importlib.util.spec_from_file_location('fixed_resume_candidate',ENTRY)
resume_module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume_module)
M=resume_module

class FakeAdapter:
    def __init__(self,fail=None):self.events=[];self.fail=fail;self.output=None;self.requests={}
    def event(self,name):
        self.events.append(name)
        if self.fail==name:raise RuntimeError('injected '+name)
    def token_identity(self):
        self.event('token');return {'sid':M.OWNER,'admin':self.fail!='ordinary'}
    def inspect_task_continuation(self,spec):self.event('task_missing');return {'folder':'missing','task':'missing'}
    @contextmanager
    def hold_old_install(self,plan):
        self.event('old_full_admission');yield [{'all734_and_acl':'fake_verified'}];self.event('leases_exit')
    def archive_old_leaves(self,plan,inventory):self.event('archive_all_four');return {'path':'fixed-private-fake','history_preserved':True}
    def replace_declared_leaf(self,change,data,attempt):self.event('replace:'+change['path'])
    def verify_complete_install(self,plan):self.event('new_full_admission');return []
    def verify_exact_tree(self,plan,archive):self.event('new_exact_tree')
    def register_continuation_task(self,spec):self.event('register_create_only')
    def verify_task(self,spec):self.event('verify_actual_task');return {}
    def verify_initial_outputs(self,outputs):self.event('verify_initial_outputs')
    def publish_owner_request(self,request_id,data,owner):self.event('publish_request');self.requests[request_id]=data
    def run_fixed_task(self,spec):self.event('RunNone_once');return 'fake-ACK-only'
    def wait_fixed_receipt(self,request_id,timeout):
        self.event('wait_actual_receipt')
        request=M.strict_json(self.requests[request_id])
        policy=M.strict_json(PLAN['policy_bytes'])
        before={'ExclusionPath':['prior'],'ExclusionExtension':[],'ExclusionProcess':[]}
        outputs=PLAN['initial'][0][0]['outputs']
        after={**before,'ExclusionPath':['prior']+[x['path'] for x in outputs]}
        identity={'installation_id':policy['installation_id'],'owner_sid':policy['owner_sid'],'request_id':request_id,
            'request_sha256':M.sha(self.requests[request_id]),'manifest_bytes_sha256':request['manifest_sha256'],
            'policy_sha256':M.sha(PLAN['policy_bytes']),'runtime_manifest_sha256':policy['runtime_manifest_sha256'],
            'runtime_verified':True,'protected_code':True,'request_owner_sid':M.OWNER,'actual_token_sid':M.SYSTEM}
        return M.raw_json({'status':'verified' if self.fail!='ACK_without_proof' else 'settings_failed','broker_identity':identity,
            'admin_token':True,'system_token_sid':M.SYSTEM,'observed_prior_settings_preserved':True,
            'observed_extensions_unchanged':True,'observed_processes_unchanged':True,'before_settings':before,
            'after_settings':after,'files':outputs,'verified_requested_paths':[x['path'] for x in outputs]})
    def diagnostics(self,spec):self.events.append('diagnostics_no_Run');return {'fake':True}
    def write_new_external_receipt(self,path,data):self.output=M.strict_json(data)

POLICY=M.raw_json({'installation_id':M.INSTALLATION_ID,'owner_sid':M.OWNER,'runtime_manifest_sha256':'f'*64})
OUTPUT={'path':r'C:\w\declared\one.exe','size':1,'sha256':'e'*64}
CHANGES=[{'path':path} for path in sorted(M.LEAVES)]
PLAN={'summary':{},'task':{},'frozen':[({'path':path},b'new') for path in sorted(M.LEAVES)],
 'authority':{'changed_leaves':CHANGES},'policy_bytes':POLICY,
 'initial':[({'outputs':[OUTPUT]},b'fake-only-manifest')]}

class ResumeDirectedTests(unittest.TestCase):
    def run_case(self,fail=None):
        adapter=FakeAdapter(fail);result=M.resume(PLAN,adapter,None,'fake-only-output');return result,adapter
    def test_archive_precedes_each_exact_replace_and_one_run_requires_proof(self):
        result,adapter=self.run_case()
        self.assertEqual(result['status'],'installed_initial_outputs_verified')
        archive=adapter.events.index('archive_all_four')
        for change in CHANGES:self.assertLess(archive,adapter.events.index('replace:'+change['path']))
        self.assertEqual(adapter.events.count('RunNone_once'),1)
        self.assertIn('leases_exit',adapter.events)
    def test_ordinary_no_mutation(self):
        result,adapter=self.run_case('ordinary');self.assertEqual(result['status'],'resume_failed_or_partial')
        self.assertNotIn('archive_all_four',adapter.events)
    def test_existing_or_unknown_task_failure_no_archive(self):
        result,adapter=self.run_case('task_missing');self.assertNotIn('archive_all_four',adapter.events)
    def test_old_inventory_failure_before_archive(self):
        result,adapter=self.run_case('old_full_admission');self.assertNotIn('archive_all_four',adapter.events)
    def test_archive_failure_no_replace_or_task(self):
        result,adapter=self.run_case('archive_all_four');self.assertFalse(any(x.startswith('replace:') for x in adapter.events))
    def test_replacement_failure_retains_archive_and_does_not_run(self):
        result,adapter=self.run_case('replace:'+CHANGES[0]['path'])
        self.assertIn('archive_all_four',adapter.events);self.assertNotIn('RunNone_once',adapter.events)
    def test_new_full_proof_failure_no_task_registration(self):
        result,adapter=self.run_case('new_full_admission');self.assertNotIn('register_create_only',adapter.events)
    def test_registration_failure_no_run(self):
        result,adapter=self.run_case('register_create_only');self.assertNotIn('RunNone_once',adapter.events)
    def test_run_ACK_without_actual_verified_receipt_does_not_succeed(self):
        result,adapter=self.run_case('ACK_without_proof')
        self.assertEqual(result['status'],'resume_failed_or_partial');self.assertEqual(adapter.events.count('RunNone_once'),1)
    def test_receipt_failure_no_blind_restart(self):
        result,adapter=self.run_case('wait_actual_receipt');self.assertEqual(adapter.events.count('RunNone_once'),1)

if __name__=='__main__':unittest.main()
