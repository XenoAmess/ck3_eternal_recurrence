"""One fixed approved continuation of the retained a05 installation; no UAC."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
PACKAGE=HERE/'package'
sys.path.insert(0,str(PACKAGE))
from protected_runtime import activate_sealed_paths
activate_sealed_paths(PACKAGE)
from contextlib import ExitStack, contextmanager
import argparse
import hashlib
import json
import ntpath
import time
import traceback
import uuid
from installer_core import (INSTALL_ROOT, OWNER, SYSTEM, ADMINS, prepare_plan,
                            strict_json, raw_json, sha, make_request, verify_receipt)
from windows_adapter import WindowsInstallerAdapter, verify_task_descriptor
from native_safety import NativeSafety, canonical_path

OLD_BUNDLE_SHA='3a65d3186ddbee3eb9d7ff3882d7ec58ece4362a0da84fb7fa925a4921bd7ef4'
INSTALLATION_ID='83b30886-8dbc-4c9c-8177-d575be46a925'
LEAVES={'deps/win32com/client/__init__.py','runtime-seal.json','policy.json','installation-manifest.json'}

def prepare_resume(expected_authority_sha, safety):
    with ExitStack() as stack:
        authority_lease=stack.enter_context(safety.lock_file(str(HERE/'resume-authority.json')))
        authority_raw=authority_lease.read_bytes(2*1024*1024)
        if sha(authority_raw)!=expected_authority_sha:
            raise ValueError('approved resume authority changed')
        authority=strict_json(authority_raw)
        if set(authority)!={'schema','installation_id','owner_sid','old_bundle_sha256','new_bundle_sha256',
              'old_partial_receipt_sha256','changed_leaves','new_paths','task_continuation','source_entry'}:
            raise ValueError('unexpected resume authority keys')
        if (authority['schema']!='xar.project-exe-broker.resume-authority.v1' or authority['installation_id']!=INSTALLATION_ID
                or authority['owner_sid']!=OWNER or authority['old_bundle_sha256']!=OLD_BUNDLE_SHA
                or authority['old_partial_receipt_sha256']!='89952704c6ead5e2b323e8cde424a87b6e89169cf96c95ecbd6a387bdafb02dc'
                or authority['new_paths']!=[] or authority['task_continuation']!='missing-folder-create-or-exact-empty-folder-create-only'):
            raise ValueError('resume must retain exact a05 identity and scope')
        entry=authority['source_entry']
        with safety.lock_file(str(Path(__file__))) as lease:
            data=lease.read_bytes(1024*1024)
        if entry!={'path':'resume_project_exe_broker.py','size':len(data),'sha256':sha(data)}:
            raise ValueError('fixed approved external resume entry changed')
        old_lease=stack.enter_context(safety.lock_file(str(HERE/'expected-old-bundle-manifest.json')))
        old_raw=old_lease.read_bytes(2*1024*1024)
        if sha(old_raw)!=OLD_BUNDLE_SHA:raise ValueError('approved old bundle changed')
        old=strict_json(old_raw)
        new=prepare_plan(PACKAGE,authority['new_bundle_sha256'],safety)
        if old['installation_id']!=INSTALLATION_ID or new['manifest']['installation_id']!=INSTALLATION_ID:
            raise ValueError('installation UUID changed')
        before={row['path']:row for row in old['files']}
        after={row['path']:row for row in new['manifest']['files']}
        if len(before)!=734 or set(before)!=set(after):raise ValueError('installed 734 path set must be unchanged')
        actual=[{'path':path,'before':before[path],'after':after[path]} for path in sorted(before) if before[path]!=after[path]]
        if actual!=authority['changed_leaves'] or {row['path'] for row in actual}!=LEAVES:
            raise ValueError('only exact four approved leaves may change')
        if old['initial_manifests']!=new['manifest']['initial_manifests']:
            raise ValueError('initial four project outputs must be unchanged')
        old_data={}
        for path in sorted(LEAVES):
            target=HERE/'expected-old-leaves'/path
            with safety.lock_file(str(target)) as lease:
                data=lease.read_bytes(max(before[path]['size'],1))
            if len(data)!=before[path]['size'] or sha(data)!=before[path]['sha256']:
                raise ValueError('expected old leaf bytes changed')
            old_data[path]=data
        new_data={row['path']:data for row,data in new['frozen']}
        old_policy=strict_json(old_data['policy.json'])
        new_policy=strict_json(new_data['policy.json'])
        old_policy['runtime_manifest_sha256']=new_policy['runtime_manifest_sha256']
        if old_policy!=new_policy:raise ValueError('policy scope/identity must remain unchanged')
        old_seal=strict_json(old_data['runtime-seal.json'])
        new_seal=strict_json(new_data['runtime-seal.json'])
        old_seal['files']=[after[row['path']] for row in old_seal['files']]
        if old_seal!=new_seal:raise ValueError('seal may only repin declared code leaf')
        old_installed=strict_json(old_data['installation-manifest.json'])
        new_installed=strict_json(new_data['installation-manifest.json'])
        for field in ('policy','runtime_seal'):old_installed[field]=new_installed[field]
        if old_installed!=new_installed:raise ValueError('task/installation identity must remain unchanged')
        with safety.lock_file(str(HERE/'stock-VARIANT-class.py')) as lease:
            variant=lease.read_bytes(4096)
        if sha(variant)!='1da88287ae4fc9f78aecc8388d0a7bb2af53142ed2595bec5945d849979cfc9d':
            raise ValueError('stock VARIANT extraction changed')
        if new_data['deps/win32com/client/__init__.py']!=old_data['deps/win32com/client/__init__.py']+b'\r\n'+variant+b'\r\n':
            raise ValueError('only exact stock VARIANT class append is approved')
    new['old_manifest']=old
    new['old_manifest_raw']=old_raw
    new['old_leaf_data']=old_data
    new['authority_raw']=authority_raw
    new['authority']=authority
    new['summary'].update(status='prepared_exact_partial_continuation_only',installation_id=INSTALLATION_ID,
        changed_leaves=sorted(LEAVES),installed_new_paths=[],old_bundle_sha256=OLD_BUNDLE_SHA)
    return new

class ResumeAdapter(WindowsInstallerAdapter):
    def inspect_task_continuation(self,spec):
        service=self._scheduler()
        try:folder=service.GetFolder(spec['folder'])
        except Exception as error:
            if self._not_found(error):return {'folder':'missing','task':'missing'}
            raise
        proof=verify_task_descriptor(folder.GetSecurityDescriptor(0x1|0x4),OWNER)
        try:folder.GetTask(spec['name'])
        except Exception as error:
            if not self._not_found(error):raise
        else:raise FileExistsError('actual task already exists; no update/restart permitted')
        if folder.GetTasks(1).Count!=0 or folder.GetFolders(0).Count!=0:
            raise ValueError('only an exact empty retained task folder can continue')
        return {'folder':'exact_empty_retained_folder','task':'missing','folder_acl':proof}

    def verify_empty_data(self):
        for name,kind in [('private-frozen','private'),('receipts','protected'),('inbox','inbox')]:
            path=ntpath.join(INSTALL_ROOT,name)
            self._verify_acl(path,OWNER,kind,True)
            if self.safety.list_files(path):raise ValueError('initial broker data directory is not empty: '+name)

    def verify_exact_tree(self,plan,archive=None):
        expected_files={ntpath.normcase(ntpath.join(INSTALL_ROOT,row['path'].replace('/','\\'))) for row,_ in plan['frozen']}
        expected_dirs={ntpath.normcase(INSTALL_ROOT)}
        for path in expected_files:
            parent=ntpath.dirname(path)
            while parent.startswith(ntpath.normcase(INSTALL_ROOT)):
                expected_dirs.add(parent)
                if parent==ntpath.normcase(INSTALL_ROOT):break
                parent=ntpath.dirname(parent)
        for name in ('private-frozen','receipts','inbox'):expected_dirs.add(ntpath.normcase(ntpath.join(INSTALL_ROOT,name)))
        pending=[INSTALL_ROOT]
        seen=set()
        while pending:
            directory=pending.pop()
            key=ntpath.normcase(directory)
            if key in seen:raise ValueError('duplicate directory traversal')
            seen.add(key)
            if archive is not None and key==ntpath.normcase(archive):continue
            if key not in expected_dirs:raise ValueError('undeclared installed directory')
            for row in self.safety.list_files(directory):
                path=row['path']; child=ntpath.normcase(path)
                if row['is_file']:
                    if child not in expected_files:raise ValueError('undeclared installed file: '+path)
                elif archive is not None and child==ntpath.normcase(archive):
                    self._verify_acl(path,OWNER,'private',True)
                else:
                    if child not in expected_dirs or not self.safety.is_dir(path):raise ValueError('undeclared/reparse installed directory')
                    pending.append(path)

    @contextmanager
    def hold_old_install(self,plan):
        old_plan={'frozen':[(row,b'') for row in plan['old_manifest']['files']]}
        with ExitStack() as stable:
            stable.enter_context(self.safety.lock_dir(INSTALL_ROOT))
            inventory=self.verify_complete_install(old_plan)
            self.verify_empty_data()
            self.verify_exact_tree(old_plan)
            # All unchanged leaves remain immutable through update/register/actual receipt.
            for row in plan['old_manifest']['files']:
                path=ntpath.join(INSTALL_ROOT,row['path'].replace('/','\\'))
                self._verify_acl(path,OWNER)
                if row['path'] not in LEAVES:
                    lease=stable.enter_context(self.safety.lock_file(path))
                    if sha(lease.read_bytes(max(row['size'],1)))!=row['sha256']:raise ValueError('unchanged installed leaf drift')
            yield inventory

    def archive_old_leaves(self,plan,inventory):
        archive=ntpath.join(INSTALL_ROOT,'private-frozen','resume-'+str(uuid.uuid4()))
        with self.safety.lock_dir(ntpath.join(INSTALL_ROOT,'private-frozen')):
            self._create_directory_secure(archive,OWNER,'private')
        archived=[]
        for index,path in enumerate(sorted(LEAVES)):
            expected=plan['old_leaf_data'][path]
            actual_path=ntpath.join(INSTALL_ROOT,path.replace('/','\\'))
            with self.safety.lock_file(actual_path) as lease:
                actual=lease.read_bytes(max(len(expected),1))
                if actual!=expected:raise ValueError('old declared leaf changed before archive')
                acl=self._verify_acl(actual_path,OWNER)
                destination=ntpath.join(archive,f'{index:02d}-old.bin')
                self._create_file_secure(destination,actual,OWNER,'private')
            with self.safety.lock_file(destination) as archived_lease:
                if archived_lease.read_bytes(max(len(actual),1))!=actual:raise ValueError('archived old bytes differ')
            archived.append({'path':path,'archive_path':destination,'size':len(actual),'sha256':sha(actual),'old_acl':acl})
        metadata={'schema':'xar.project-exe-broker.partial-resume-archive.v1','installation_id':INSTALLATION_ID,
                  'old_bundle_sha256':OLD_BUNDLE_SHA,'old_manifest':plan['old_manifest'],
                  'authority':plan['authority'],'old_acl_inventory':inventory,'archived_leaves':archived}
        self._create_file_secure(ntpath.join(archive,'metadata.json'),raw_json(metadata),OWNER,'private')
        return {'path':archive,'leaves':archived,'history_preserved':True}

    def replace_declared_leaf(self,change,data,attempt_id):
        import win32file
        path=ntpath.join(INSTALL_ROOT,change['path'].replace('/','\\'))
        with self.safety.lock_dir(ntpath.dirname(path)):
            self._verify_acl(path,OWNER)
            with self.safety.lock_file(path) as lease:
                current=lease.read_bytes(max(change['before']['size'],1))
                if len(current)!=change['before']['size'] or sha(current)!=change['before']['sha256']:
                    raise ValueError('declared old leaf no longer matches admission')
            temp=path+'.resume-'+attempt_id+'.tmp'
            self._create_file_secure(temp,data,OWNER)
            with self.safety.lock_file(temp) as lease:
                if sha(lease.read_bytes(max(len(data),1)))!=change['after']['sha256']:raise ValueError('replacement staging bytes changed')
            # Only the four exact approved targets, same-volume, immediate move.
            # Final protected SA is already installed on the staging file.
            win32file.MoveFileEx(temp,path,1|8)
            self._verify_acl(path,OWNER)
            with self.safety.lock_file(path) as lease:
                if sha(lease.read_bytes(max(len(data),1)))!=change['after']['sha256']:raise ValueError('replacement actual bytes differ')

    def build_memory_definition(self,spec):
        definition=self._scheduler().NewTask(0)
        definition.RegistrationInfo.Description='Only declared local CK3 project executable Defender path exclusions.'
        definition.Principal.UserId=spec['principal']['user_id']
        definition.Principal.LogonType=spec['principal']['logon_type']
        definition.Principal.RunLevel=spec['principal']['run_level']
        settings=definition.Settings
        for name,value in [('Enabled',True),('AllowDemandStart',True),('StartWhenAvailable',False),
             ('DisallowStartIfOnBatteries',False),('StopIfGoingOnBatteries',False),('RunOnlyIfIdle',False),
             ('RunOnlyIfNetworkAvailable',False),('MultipleInstances',1),('ExecutionTimeLimit',spec['execution_time_limit'])]:
            setattr(settings,name,value)
            if getattr(settings,name)!=value:raise ValueError('actual task setter did not read back: '+name)
        action=definition.Actions.Create(0)
        for name,key in [('Path','path'),('Arguments','arguments'),('WorkingDirectory','working_directory')]:
            setattr(action,name,spec['action'][key])
            if getattr(action,name)!=spec['action'][key]:raise ValueError('actual action setter did not read back')
        if definition.Triggers.Count!=0 or definition.Actions.Count!=1:raise ValueError('fixed action/trigger count required')
        return definition

    def register_continuation_task(self,spec):
        state=self.inspect_task_continuation(spec)
        service=self._scheduler()
        definition=self.build_memory_definition(spec)
        if state['folder']=='missing':
            folder=service.GetFolder('\\').CreateFolder(spec['folder'].lstrip('\\'),spec['sddl'])
        else:folder=service.GetFolder(spec['folder'])
        verify_task_descriptor(folder.GetSecurityDescriptor(0x1|0x4),OWNER)
        folder.RegisterTaskDefinition(spec['name'],definition,2|16,SYSTEM,None,5,spec['sddl'])
        self._folder=folder

    def diagnostics(self,spec):
        result={'task_ack_does_not_prove_completion':True}
        try:
            task=self._scheduler().GetFolder(spec['folder']).GetTask(spec['name'])
            result.update(state=task.State,last_task_result=task.LastTaskResult,running_instances=task.GetInstances(0).Count)
        except Exception as exc:result['task_query_error']=type(exc).__name__+': '+str(exc)
        for name in ('receipts','private-frozen','inbox'):
            try:
                result[name]=self.safety.list_files(ntpath.join(INSTALL_ROOT,name))
                if name=='receipts':
                    result['observed_receipts']=[]
                    for row in result[name][:8]:
                        if row['is_file'] and row['path'].endswith('.receipt.json'):
                            self.safety.verify_protected_path(row['path'])
                            with self.safety.lock_file(row['path']) as lease:raw=lease.read_bytes(16*1024*1024)
                            result['observed_receipts'].append({'path':row['path'],'sha256':sha(raw),'actual':strict_json(raw)})
            except Exception as exc:result[name]={'read_error':type(exc).__name__+': '+str(exc)}
        return result

def resume(plan,adapter,safety,output_receipt):
    facts=dict(plan['summary'])
    facts.update(status='resuming_fixed_partial_installation',settings_status='not_started',phases=[],initial_results=[])
    try:
        if adapter.token_identity()!={'sid':OWNER,'admin':True}:raise ValueError('actual elevated authorized owner token required')
        state=adapter.inspect_task_continuation(plan['task'])
        facts['task_before']=state
        with adapter.hold_old_install(plan) as inventory:
            facts['phases'].append('all_old_734_leaf_bytes_complete_acl_empty_data_and_task_missing_verified')
            facts['archive']=adapter.archive_old_leaves(plan,inventory)
            facts['phases'].append('all_four_replaced_old_leaves_archived_protected_append_only')
            data={row['path']:raw for row,raw in plan['frozen']}
            attempt_id=str(uuid.uuid4())
            for change in plan['authority']['changed_leaves']:
                adapter.replace_declared_leaf(change,data[change['path']],attempt_id)
                facts['phases'].append('replaced_declared_leaf:'+change['path'])
            facts['acl_inventory']=adapter.verify_complete_install(plan)
            adapter.verify_exact_tree(plan,facts['archive']['path'])
            facts['phases'].append('all_new_734_leaf_bytes_and_acl_verified')
            adapter.register_continuation_task(plan['task'])
            facts['task_readback']=adapter.verify_task(plan['task'])
            facts['phases'].append('fixed_create_only_SYSTEM_task_actual_definition_acl_verified')
            pending=[]
            for baseline,manifest_bytes in plan['initial']:
                request_id=str(uuid.uuid4())
                request_bytes=make_request(plan['policy_bytes'],manifest_bytes,request_id)
                adapter.verify_initial_outputs(baseline['outputs'])
                adapter.publish_owner_request(request_id,request_bytes,OWNER)
                pending.append((baseline,manifest_bytes,request_id,request_bytes))
            adapter.run_fixed_task(plan['task'])
            facts['settings_status']='pending_actual_SYSTEM_receipts'
            deadline=time.monotonic()+180
            for baseline,manifest_bytes,request_id,request_bytes in pending:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError('shared initial receipt window elapsed')
                raw=adapter.wait_fixed_receipt(request_id,remaining)
                receipt=verify_receipt(raw,request_bytes,manifest_bytes,plan['policy_bytes'],baseline['outputs'])
                facts['initial_results'].append({'request_id':request_id,'request_sha256':sha(request_bytes),
                    'receipt_sha256':sha(raw),'status':receipt['status'],'files':baseline['outputs']})
            facts['status']='installed_initial_outputs_verified'
            facts['settings_status']='verified'
            facts['ordinary_token_future_no_uac_status']='pending_actual_ordinary_token_new_path_and_SYSTEM_receipt'
    except Exception as exc:
        facts.update(status='resume_failed_or_partial',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),retained_partial_installation=True)
        facts['diagnostics']=adapter.diagnostics(plan['task'])
    adapter.write_new_external_receipt(output_receipt,raw_json(facts))
    return facts

def main():
    if sys.flags.isolated!=1 or sys.flags.no_site!=1:raise RuntimeError('use copied Python -I -S -B')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-authority-sha256',required=True)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--receipt')
    args=parser.parse_args()
    safety=NativeSafety(OWNER,INSTALL_ROOT+r'\private-frozen',INSTALL_ROOT+r'\receipts')
    plan=prepare_resume(args.expected_authority_sha256,safety)
    if not args.resume:
        print(json.dumps(plan['summary'],indent=2));return 0
    if not args.receipt:parser.error('--resume requires a new external receipt under CROOT')
    receipt=canonical_path(args.receipt)
    allowed=r'C:\ck3-war-episode04-research-20261004-a01'+'\\'
    if not ntpath.normcase(receipt).startswith(ntpath.normcase(allowed)) or not receipt.lower().endswith('.json'):
        parser.error('fixed external evidence root receipt required')
    adapter=ResumeAdapter(safety)
    result=resume(plan,adapter,safety,receipt)
    print(json.dumps({'status':result['status'],'receipt':receipt},indent=2))
    return 0 if result['status']=='installed_initial_outputs_verified' else 1

if __name__=='__main__':raise SystemExit(main())
