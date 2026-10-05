"""Focused delegation/creation safety checks. No real COM/security/Task/WMI."""
from contextlib import contextmanager
from pathlib import Path
import copy
import json
import sys
import types
import unittest

sys.path.insert(0, str(Path(__file__).parent.parent))
import installer_core as core
import windows_adapter as adapters

class FakeSD:
    def __init__(self, rows, owner=core.ADMINS, protected=True):
        self.rows, self.owner, self.protected = rows, owner, protected
    def GetSecurityDescriptorOwner(self): return self.owner
    def GetSecurityDescriptorControl(self): return (0x1000 if self.protected else 0, 1)
    def GetSecurityDescriptorDacl(self): return self
    def GetAceCount(self): return len(self.rows)
    def GetAce(self, index):
        row = self.rows[index]
        return ((row['type'], row.get('flags', 0)), row['mask'], row['sid'])

def sd(rows=None, owner=core.ADMINS, protected=True):
    return FakeSD(rows if rows is not None else [
        {'type': 0, 'mask': 0x10000000, 'sid': core.SYSTEM},
        {'type': 0, 'mask': 0x10000000, 'sid': core.ADMINS},
        {'type': 0, 'mask': 0xA0000000, 'sid': core.OWNER}], owner, protected)

class FakeSecurity:
    @staticmethod
    def ConvertSidToStringSid(value): return value
    @staticmethod
    def ConvertStringSecurityDescriptorToSecurityDescriptor(value, revision):
        if isinstance(value, FakeSD): return value
        assert 'D:P' in value
        # This creation seam records final SD, not a real Windows conversion.
        return types.SimpleNamespace(sddl=value)

class FakeSafety:
    def __init__(self): self.locks=[]
    @contextmanager
    def lock_dir(self, path):
        self.locks.append(path)
        yield None
    def inspect_descriptor(self, path):
        return {'security': {'owner_sid': core.ADMINS, 'dacl_present': True,
            'aces': [{'type': 0, 'mask': 0x1F01FF, 'sid': core.ADMINS}]}}

class CreationFakeAdapter(adapters.WindowsInstallerAdapter):
    def _verify_acl(self, path, owner_sid, kind='protected', directory=False):
        self.calls.append(('readback', str(path), kind))
        return {'actual': True}

class TaskFakeAdapter:
    def __init__(self, existing=False, receipt_error=None, acl_error=False):
        self.existing, self.receipt_error, self.acl_error = existing, receipt_error, acl_error
        self.calls=[]
        self.receipts=[]
    def token_identity(self): return {'sid': core.OWNER, 'admin': True}
    def path_exists(self, path): return self.existing
    def task_exists(self, spec): return self.existing
    def create_fresh_protected_root(self, *args): self.calls.append('root_secure_create')
    def copy_new_protected_file(self, *args): self.calls.append('leaf_secure_create')
    def create_fixed_data_directories(self, *args): self.calls.append('data_dirs')
    def verify_complete_install(self, plan):
        if self.acl_error: raise ValueError('bad runtime leaf ACL')
        self.calls.append('complete_acl_verified')
        return [{'actual': True}]
    def register_task_new(self, spec): self.calls.append('register_fixed_task')
    def verify_task(self, spec):
        self.calls.append('task_actual_readback')
        return {'verified': True}
    def verify_initial_outputs(self, outputs): self.calls.append('actual_outputs_verified')
    def publish_owner_request(self, request_id, data, owner_sid):
        self.last_request = data
        self.calls.append('owner_request')
    def run_fixed_task(self, spec): self.calls.append('Run_None_ACK')
    def wait_fixed_receipt(self, request_id, timeout):
        if self.receipt_error: raise self.receipt_error
        raise TimeoutError('fake no actual receipt')
    def write_new_external_receipt(self, path, data): self.receipts.append(data)

def minimal_plan():
    return {'summary': {'status': 'prepared_only'}, 'frozen': [({'path': 'a', 'sha256': 'f'*64}, b'a')],
        'task': core.task_spec(core.OWNER), 'policy_bytes': core.raw_json({
            'installation_id': '00000000-0000-4000-8000-000000000000'}),
        'initial': [({'outputs': []}, b'{}')]}

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.original_modules = adapters._modules
        adapters._modules=lambda: (None,None,None,FakeSecurity,None)
    def tearDown(self): adapters._modules=self.original_modules

    def test_exact_task_read_run_and_mapped_acl(self):
        proof=adapters.verify_task_descriptor(sd(), core.OWNER)
        self.assertTrue(proof['dacl_protected'])
        mapped=sd()
        mapped.rows[2]['mask']=0x1200A9
        mapped.rows[0]['mask']=mapped.rows[1]['mask']=0x1F01FF
        adapters.verify_task_descriptor(mapped,core.OWNER)

    def test_task_bad_owner_protection_or_extra_rights_rejected(self):
        for bad in (sd(owner=core.OWNER),sd(protected=False)):
            with self.assertRaises(ValueError): adapters.verify_task_descriptor(bad,core.OWNER)
        for extra in (0x40,0x10000,0x40000,0x80000,0x02000000,0x10):
            bad=sd();bad.rows[2]['mask']|=extra
            with self.assertRaises(ValueError): adapters.verify_task_descriptor(bad,core.OWNER)
        bad=sd();bad.rows.append({'type':0,'mask':0xA0000000,'sid':'S-1-1-0'})
        with self.assertRaises(ValueError): adapters.verify_task_descriptor(bad,core.OWNER)

    def test_outer_parent_create_only_allowed_replace_rejected(self):
        raw={'owner_sid':adapters.TRUSTED_INSTALLER,'dacl_present':True,'aces':[
            {'type':0,'mask':4,'sid':'S-1-5-11'},
            {'type':0,'mask':0x1F01FF,'sid':'S-1-3-0','flags':8}]}
        adapters.verify_outer_parent_security(raw)
        for mask in (0x40,0x10000,0x40000,0x80000,0x40000000):
            bad=copy.deepcopy(raw);bad['aces'][0]['mask']=mask
            with self.assertRaises(ValueError): adapters.verify_outer_parent_security(bad)

    def test_final_security_attributes_used_at_each_creation(self):
        calls=[]
        class Handle:
            def Close(self): calls.append(('close',))
        def create_directory(path, attributes):
            self.assertIn('O:BAG:BAD:P',attributes.SECURITY_DESCRIPTOR.sddl)
            self.assertNotIn(core.OWNER+'G:',attributes.SECURITY_DESCRIPTOR.sddl)
            calls.append(('CreateDirectory_final_SD',path))
        def create_file(path, access, share, attributes, disposition, flags, template):
            self.assertEqual(share,0);self.assertEqual(disposition,1)
            self.assertIn('O:BAG:BAD:P',attributes.SECURITY_DESCRIPTOR.sddl)
            calls.append(('CreateFile_final_SD',path))
            return Handle()
        def write(handle,data):calls.append(('write',));return (0,len(data))
        fakefile=types.SimpleNamespace(CreateDirectory=create_directory,CreateFile=create_file,
            WriteFile=write,FlushFileBuffers=lambda handle:calls.append(('flush',)))
        fakeattributes=types.SimpleNamespace(SECURITY_ATTRIBUTES=lambda:types.SimpleNamespace())
        old={name:sys.modules.get(name) for name in ('win32file','pywintypes')}
        try:
            sys.modules['win32file']=fakefile;sys.modules['pywintypes']=fakeattributes
            adapter=CreationFakeAdapter(FakeSafety());adapter.calls=calls
            adapter._create_directory_secure(r'C:\fake',core.OWNER)
            adapter._create_file_secure(r'C:\fake\code.py',b'code',core.OWNER)
        finally:
            for name,value in old.items():
                if value is None:sys.modules.pop(name,None)
                else:sys.modules[name]=value
        self.assertEqual(calls[0][0],'CreateDirectory_final_SD')
        self.assertEqual(calls[2][0],'CreateFile_final_SD')
        self.assertNotIn('SetNamedSecurityInfo',[row[0] for row in calls])

    def test_existing_installation_refused_before_changes(self):
        adapter=TaskFakeAdapter(existing=True)
        result=core.install(minimal_plan(),adapter,None,'new.json')
        self.assertEqual(result['status'],'installation_failed_or_partial')
        self.assertEqual(adapter.calls,[])

    def test_invalid_leaf_acl_prevents_task_registration(self):
        adapter=TaskFakeAdapter(acl_error=True)
        result=core.install(minimal_plan(),adapter,None,'new.json')
        self.assertEqual(result['status'],'installation_failed_or_partial')
        self.assertNotIn('register_fixed_task',adapter.calls)

    def test_task_ack_without_system_receipt_never_success(self):
        adapter=TaskFakeAdapter(receipt_error=TimeoutError('no SYSTEM receipt'))
        result=core.install(minimal_plan(),adapter,None,'new.json')
        self.assertEqual(result['status'],'installation_failed_or_partial')
        self.assertEqual(result['settings_status'],'pending_actual_SYSTEM_receipts')
        self.assertIn('Run_None_ACK',adapter.calls)

    def test_initial_requests_publish_before_one_run(self):
        plan=minimal_plan();plan['initial']=plan['initial']*2
        adapter=TaskFakeAdapter(receipt_error=TimeoutError('no SYSTEM receipt'))
        core.install(plan,adapter,None,'new.json')
        self.assertEqual(adapter.calls.count('Run_None_ACK'),1)
        index=adapter.calls.index('Run_None_ACK')
        self.assertEqual(adapter.calls[:index].count('owner_request'),2)

    def test_fixed_action_never_accepts_request_parameters(self):
        spec=core.task_spec(core.OWNER)
        self.assertNotIn('$(Arg',spec['action']['arguments'])
        self.assertEqual(spec['principal'],{'user_id':core.SYSTEM,'logon_type':5,'run_level':1})
        self.assertEqual(spec['triggers_count'],0)
        self.assertEqual(spec['multiple_instances'],1)

    def test_real_adapter_fixed_registration_contract_against_fake_scheduler(self):
        calls=[]
        class Missing(Exception):hresult=-2147024894
        class Collection:
            def __init__(self):self.rows=[]
            @property
            def Count(self):return len(self.rows)
            def Create(self, kind):
                self.assert_kind=kind
                action=types.SimpleNamespace();self.rows.append(action);return action
            def Item(self,index):return self.rows[index-1]
        class Folder:
            def CreateFolder(self,name,sddl):
                self.created=(name,sddl);service.folder=Folder();return service.folder
            def RegisterTaskDefinition(self,name,definition,flags,user,password,logon,sddl):
                calls.append((name,flags,user,password,logon,sddl))
                self.task=types.SimpleNamespace(Definition=definition,Xml='<fixed-fake-task/>',
                    GetSecurityDescriptor=lambda flags:sd(),Run=lambda parameters:calls.append(('Run',parameters)))
            def GetTask(self,name):return self.task
            def GetSecurityDescriptor(self, flags):return sd()
        class Service:
            folder=None
            def GetFolder(self,name):
                if name=='\\':return Folder()
                if self.folder is None:raise Missing()
                return self.folder
            def NewTask(self,flags):
                return types.SimpleNamespace(RegistrationInfo=types.SimpleNamespace(),
                    Principal=types.SimpleNamespace(),Settings=types.SimpleNamespace(),
                    Actions=Collection(),Triggers=Collection())
        service=Service()
        adapter=adapters.WindowsInstallerAdapter(FakeSafety())
        adapter._service=service
        spec=core.task_spec(core.OWNER)
        adapter.register_task_new(spec)
        self.assertEqual(calls[0][1:5],(18,core.SYSTEM,None,5))
        adapter.verify_task(spec)
        adapter.run_fixed_task(spec)
        self.assertEqual(calls[-1],('Run',None))
        service.folder.task.Definition.Actions.Item(1).Arguments += ' --other'
        with self.assertRaises(ValueError):adapter.verify_task(spec)

if __name__=='__main__':unittest.main(verbosity=2)
