"""Fixed protected broker OS adapters. Import performs no COM/security calls."""
from contextlib import ExitStack
from pathlib import Path
import hashlib
import json
import ntpath
import os
import sys
import time
import uuid

from installer_core import INSTALL_ROOT, TASK_FOLDER, TASK_NAME, OWNER, SYSTEM, ADMINS, sha, strict_json, relative_path

TRUSTED_INSTALLER = 'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'

def verify_outer_parent_security(security):
    trusted = {SYSTEM, ADMINS, TRUSTED_INSTALLER}
    if security.get('owner_sid') not in trusted or security.get('dacl_present') is not True:
        raise ValueError('outer parent owner/null DACL not trusted')
    # Creating sibling names is permitted; deleting/replacing an existing
    # protected component or changing its security/attributes is refused.
    dangerous = 0x520D0150
    for ace in security.get('aces', []):
        if ace.get('type') not in (0, 1):
            raise ValueError('unsupported outer parent ACE')
        if ace['type'] == 1 or ace.get('flags', 0) & 8:
            continue
        if type(ace.get('mask')) is not int or not isinstance(ace.get('sid'), str):
            raise ValueError('malformed outer parent ACL')
        if ace['sid'] not in trusted and ace['mask'] & dangerous:
            raise ValueError('ordinary principal can replace/change outer ancestor')
    return {'outer_parent_replacement_protected': True, 'security': security}

def verify_outer_parents(safety):
    rows = []
    for path in ('C:\\', r'C:\Program Files'):
        with safety.lock_dir(path):
            proof = safety.inspect_descriptor(path)
            rows.append({'path': path, **verify_outer_parent_security(proof['security'])})
    return rows

def _modules():
    import pythoncom
    import win32api
    import win32con
    import win32security
    import win32com.client
    return pythoncom, win32api, win32con, win32security, win32com.client

def _full_sddl(owner_sid, kind='protected', directory=False):
    # Every node is explicitly protected; inherited defaults are never trusted.
    base = 'O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)'
    if kind == 'private':
        return base
    if kind == 'inbox':
        # List/traverse/create files on root; only files inherit owner modify.
        return ('O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)'
            '(A;;0x1200ab;;;' + owner_sid + ')(A;OIIO;0x1301bf;;;' + owner_sid + ')')
    if kind == 'request':
        return 'O:' + owner_sid + 'G:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;0x1301bf;;;' + owner_sid + ')'
    return base + '(A;;FRFX;;;' + owner_sid + ')'

def _ace_rows(sd, security):
    dacl = sd.GetSecurityDescriptorDacl()
    if dacl is None:
        raise ValueError('null DACL refused')
    rows = []
    for index in range(dacl.GetAceCount()):
        ace = dacl.GetAce(index)
        if len(ace) != 3 or ace[0][0] not in (0, 1):
            raise ValueError('unsupported permission ACE')
        rows.append({'type': ace[0][0], 'flags': ace[0][1], 'mask': ace[1],
                     'sid': security.ConvertSidToStringSid(ace[2])})
    return rows

def verify_task_descriptor(sddl, owner_sid):
    _, _, _, security, _ = _modules()
    sd = security.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, 1)
    if security.ConvertSidToStringSid(sd.GetSecurityDescriptorOwner()) not in (SYSTEM, ADMINS):
        raise ValueError('task owner outside SYSTEM/Administrators')
    control, _ = sd.GetSecurityDescriptorControl()
    if not control & 0x1000:
        raise ValueError('task protected DACL required')
    rows = _ace_rows(sd, security)
    # Task object grants may be rendered as generic or mapped file rights.
    write = 0x520D0156
    read_execute = 0xA0000000
    owner_rows = []
    privileged = {SYSTEM: [], ADMINS: []}
    for row in rows:
        if row['type'] != 0 or row['flags'] & 8:
            raise ValueError('unexpected task deny/inherit-only ACE')
        sid, mask = row['sid'], row['mask']
        if sid not in (SYSTEM, ADMINS, owner_sid):
            raise ValueError('unexpected task principal')
        if sid == owner_sid:
            if mask not in (0xA0000000, 0x1200A9) or mask & write:
                raise ValueError('owner task permission must be read/run only')
            owner_rows.append(row)
        else:
            if not (mask & 0x10000000 or mask & 0x1F01FF == 0x1F01FF):
                raise ValueError('SYSTEM/Administrators full control required')
            privileged[sid].append(row)
    if len(owner_rows) != 1 or any(len(rows) != 1 for rows in privileged.values()):
        raise ValueError('exact three task principals required')
    return {'owner_sid': security.ConvertSidToStringSid(sd.GetSecurityDescriptorOwner()),
            'dacl_protected': True, 'aces': rows, 'sddl': sddl}

class WindowsInstallerAdapter:
    def __init__(self, safety):
        self.safety = safety
        self._service = None
        self._folder = None

    def token_identity(self):
        return self.safety.token_identity()

    def path_exists(self, path):
        return self.safety.exists(path)

    def _scheduler(self):
        if self._service is None:
            pythoncom, _, _, _, client = _modules()
            pythoncom.CoInitialize()
            self._service = client.Dispatch('Schedule.Service')
            self._service.Connect()
        return self._service

    @staticmethod
    def _not_found(error):
        outer = getattr(error, 'hresult', None)
        if type(outer) is not int:
            return False
        missing = (-2147024894, -2147024893)  # ERROR_FILE/PATH_NOT_FOUND HRESULT
        if outer in missing:
            return True
        if outer != -2147352567:  # DISP_E_EXCEPTION only
            return False
        info = getattr(error, 'excepinfo', None)
        return (isinstance(info, tuple) and len(info) == 6 and
                type(info[5]) is int and info[5] in missing)

    def task_exists(self, spec):
        service = self._scheduler()
        try:
            service.GetFolder(spec['folder'])
        except Exception as error:
            if self._not_found(error):
                return False
            raise
        # Existing folder also refuses installation, even if task is absent.
        return True

    def _security_attributes(self, owner_sid, kind='protected', directory=False):
        import pywintypes
        _, _, _, security, _ = _modules()
        sddl = _full_sddl(owner_sid, kind, directory)
        sd = security.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, 1)
        attributes = pywintypes.SECURITY_ATTRIBUTES()
        attributes.bInheritHandle = False
        attributes.SECURITY_DESCRIPTOR = sd
        return attributes, sd, sddl

    def _verify_acl(self, path, owner_sid, kind='protected', directory=False):
        _, _, _, security, _ = _modules()
        _, sd, sddl = self._security_attributes(owner_sid, kind, directory)
        proof = self.safety.inspect_descriptor(str(path))
        from native_safety import descriptor_proof
        allowed = (SYSTEM, ADMINS, owner_sid) if kind in ('inbox', 'request') else (SYSTEM, ADMINS)
        descriptor_proof(proof['security'],
            expected_owner=owner_sid if kind == 'request' else ADMINS,
            allowed_writers=allowed, require_protected=True,
            allowed_readers=(SYSTEM, ADMINS) if kind == 'private' else (SYSTEM, ADMINS, owner_sid))
        # Compare actual complete DACL to the requested DACL, including every ACE.
        actual = security.GetNamedSecurityInfo(str(path), security.SE_FILE_OBJECT, 0x1 | 0x4)
        expected_rows = _ace_rows(sd, security)
        actual_rows = _ace_rows(actual, security)
        if actual_rows != expected_rows:
            raise ValueError('actual complete ACL differs from approved node ACL')
        return {'path': str(path), 'kind': kind, 'actual': proof, 'sddl': sddl}

    def _create_directory_secure(self, path, owner_sid, kind='protected'):
        import win32file
        attributes, _, _ = self._security_attributes(owner_sid, kind, True)
        # Final owner/protected DACL exists at the creation syscall. No ordinary
        # writer can obtain an earlier handle during a later ACL-hardening gap.
        win32file.CreateDirectory(str(path), attributes)
        return self._verify_acl(path, owner_sid, kind, True)

    def _create_file_secure(self, path, data, owner_sid, kind='protected'):
        import win32file
        attributes, _, _ = self._security_attributes(owner_sid, kind, False)
        handle = win32file.CreateFile(str(path), 0x40000000, 0, attributes,
                                     1, 0x80 | 0x00200000, None)  # CREATE_NEW, OPEN_REPARSE_POINT
        try:
            error, written = win32file.WriteFile(handle, data)
            if error != 0 or written != len(data):
                raise OSError('incomplete protected file write')
            win32file.FlushFileBuffers(handle)
        finally:
            handle.Close()
        return self._verify_acl(path, owner_sid, kind, False)

    def create_fresh_protected_root(self, path, owner_sid):
        if ntpath.normcase(path) != ntpath.normcase(INSTALL_ROOT):
            raise ValueError('installation root is fixed')
        verify_outer_parents(self.safety)
        parent = ntpath.dirname(path)
        with self.safety.lock_dir(parent):
            self._create_directory_secure(path, owner_sid)

    def _create_parents(self, root, relative, owner_sid):
        current = Path(root)
        for part in relative_path(relative).split('/')[:-1]:
            current = current / part
            if not self.safety.exists(str(current)):
                with self.safety.lock_dir(str(current.parent)):
                    self._create_directory_secure(current, owner_sid)
            self.safety.verify_protected_path(str(current))

    def copy_new_protected_file(self, root, relative, data, expected_sha, owner_sid):
        self._create_parents(root, relative, owner_sid)
        path = Path(root) / relative
        with self.safety.lock_dir(str(path.parent)):
            self.safety.verify_protected_path(str(path.parent))
            self._create_file_secure(path, data, owner_sid)
        with self.safety.lock_file(str(path)) as lease:
            actual = lease.read_bytes(max(len(data), 1))
            if sha(actual) != expected_sha:
                raise ValueError('copied protected bytes differ')

    def create_fixed_data_directories(self, root, owner_sid):
        for name, kind in (('inbox', 'inbox'), ('private-frozen', 'private'), ('receipts', 'protected')):
            path = Path(root) / name
            with self.safety.lock_dir(root):
                self._create_directory_secure(path, owner_sid, kind)

    def verify_complete_install(self, plan):
        result = verify_outer_parents(self.safety)
        all_dirs = {INSTALL_ROOT}
        for row, data in plan['frozen']:
            path = Path(INSTALL_ROOT) / row['path']
            result.append(self.safety.verify_protected_path(str(path)))
            with self.safety.lock_file(str(path)) as lease:
                if sha(lease.read_bytes(max(row['size'], 1))) != row['sha256']:
                    raise ValueError('installed file SHA changed')
            current = path.parent
            while ntpath.normcase(str(current)).startswith(ntpath.normcase(INSTALL_ROOT)):
                all_dirs.add(str(current))
                if ntpath.normcase(str(current)) == ntpath.normcase(INSTALL_ROOT):
                    break
                current = current.parent
        for path in sorted(all_dirs):
            result.append(self.safety.verify_protected_path(path))
        result.append(self.safety.verify_protected_path(ntpath.join(INSTALL_ROOT, 'private-frozen'), private=True))
        result.append(self.safety.verify_protected_path(ntpath.join(INSTALL_ROOT, 'receipts')))
        inbox = self.safety.inspect_descriptor(ntpath.join(INSTALL_ROOT, 'inbox'))
        from native_safety import descriptor_proof
        descriptor_proof(inbox['security'], expected_owner=ADMINS,
            allowed_writers=(SYSTEM, ADMINS, OWNER), require_protected=True,
            allowed_readers=(SYSTEM, ADMINS, OWNER))
        result.append(inbox)
        return result

    def register_task_new(self, spec):
        service = self._scheduler()
        if self.task_exists(spec):
            raise FileExistsError('existing task folder refused')
        root = service.GetFolder('\\')
        folder = root.CreateFolder(spec['folder'].lstrip('\\'), spec['sddl'])
        definition = service.NewTask(0)
        definition.RegistrationInfo.Description = 'Only declared local CK3 project executable Defender path exclusions.'
        definition.Principal.UserId = spec['principal']['user_id']
        definition.Principal.LogonType = spec['principal']['logon_type']
        definition.Principal.RunLevel = spec['principal']['run_level']
        settings = definition.Settings
        settings.Enabled = True
        settings.AllowDemandStart = True
        settings.StartWhenAvailable = False
        settings.DisallowStartIfOnBatteries = False
        settings.StopIfGoingOnBatteries = False
        settings.RunOnlyIfIdle = False
        settings.RunOnlyIfNetworkAvailable = False
        settings.MultipleInstances = 1  # queue concurrent finite demand requests
        settings.ExecutionTimeLimit = spec['execution_time_limit']
        action = definition.Actions.Create(0)
        action.Path = spec['action']['path']
        action.Arguments = spec['action']['arguments']
        action.WorkingDirectory = spec['action']['working_directory']
        if definition.Triggers.Count != 0 or definition.Actions.Count != 1:
            raise ValueError('fixed no-trigger single-action definition required')
        folder.RegisterTaskDefinition(spec['name'], definition, 2 | 16,
            SYSTEM, None, 5, spec['sddl'])
        self._folder = folder

    def verify_task(self, spec):
        folder = self._scheduler().GetFolder(spec['folder'])
        task = folder.GetTask(spec['name'])
        definition = task.Definition
        if definition.Actions.Count != 1 or definition.Triggers.Count != 0:
            raise ValueError('actual task action/trigger count differs')
        action = definition.Actions.Item(1)
        actual_action = {'path': action.Path, 'arguments': action.Arguments,
                         'working_directory': action.WorkingDirectory}
        actual_user = definition.Principal.UserId
        if actual_user != SYSTEM:
            _, _, _, security, _ = _modules()
            resolved_sid, _, _ = security.LookupAccountName(None, actual_user)
            actual_user = security.ConvertSidToStringSid(resolved_sid)
        actual_principal = {'user_id': actual_user,
            'logon_type': definition.Principal.LogonType, 'run_level': definition.Principal.RunLevel}
        if actual_action != spec['action'] or actual_principal != spec['principal']:
            raise ValueError('actual task action/principal differs')
        if (definition.Settings.AllowDemandStart is not True or definition.Settings.Enabled is not True
                or definition.Settings.MultipleInstances != 1
                or definition.Settings.ExecutionTimeLimit != spec['execution_time_limit']):
            raise ValueError('actual demand/queue/time limit differs')
        return {'task_xml': task.Xml, 'action': actual_action, 'principal': actual_principal,
                'task_acl': verify_task_descriptor(task.GetSecurityDescriptor(0x1 | 0x4), OWNER),
                'folder_acl': verify_task_descriptor(folder.GetSecurityDescriptor(0x1 | 0x4), OWNER),
                'triggers_count': 0, 'allow_demand_start': True, 'multiple_instances': 1}

    def verify_initial_outputs(self, outputs):
        for row in outputs:
            with self.safety.lock_file(row['path']) as lease:
                raw = lease.read_bytes(max(row['size'], 1))
                if len(raw) != row['size'] or sha(raw) != row['sha256']:
                    raise ValueError('current initial output identity changed')

    def publish_owner_request(self, request_id, data, owner_sid):
        if str(uuid.UUID(request_id)) != request_id:
            raise ValueError('canonical request UUID required')
        inbox = Path(INSTALL_ROOT) / 'inbox'
        final = inbox / (request_id + '.request.json')
        temporary = inbox / ('.install-' + request_id + '.tmp')
        with self.safety.lock_dir(str(inbox)):
            self._create_file_secure(temporary, data, owner_sid, kind='request')
            os.rename(temporary, final)  # Windows no replacement
        with self.safety.lock_file(str(final), owner_sid=owner_sid) as lease:
            if lease.read_bytes(2 * 1024 * 1024) != data or lease.owner_write_scope_verified is not True:
                raise ValueError('actual owner request identity differs')

    def run_fixed_task(self, spec):
        self.verify_task(spec)
        return self._scheduler().GetFolder(spec['folder']).GetTask(spec['name']).Run(None)

    def wait_fixed_receipt(self, request_id, timeout):
        path = ntpath.join(INSTALL_ROOT, 'receipts', request_id + '.receipt.json')
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.safety.exists(path):
                self.safety.verify_protected_path(path)
                with self.safety.lock_file(path) as lease:
                    return lease.read_bytes(16 * 1024 * 1024)
            time.sleep(0.25)
        raise TimeoutError('actual SYSTEM receipt not observed; Task.Run ACK insufficient')

    def write_new_external_receipt(self, path, data):
        path = Path(path)
        # Root creates the fresh ordinary evidence directory before elevation.
        # No administrator recursive mkdir, junction-following or replacement.
        if not self.safety.is_dir(str(path.parent)):
            raise FileNotFoundError('external receipt parent must already exist')
        with self.safety.lock_dir(str(path.parent)):
            with path.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())

class SameAdminDefenderClient:
    """Only ExclusionPath Add; same COM client fresh complete readback."""
    def __init__(self):
        pythoncom, _, _, _, client = _modules()
        pythoncom.CoInitialize()
        self.service = client.GetObject(r'winmgmts:{impersonationLevel=impersonate}!\\.\root\Microsoft\Windows\Defender')

    def read_settings(self):
        rows = list(self.service.ExecQuery('SELECT * FROM MSFT_MpPreference'))
        if len(rows) != 1:
            raise ValueError('exact current Defender preference instance required')
        result = {}
        for key in ('ExclusionPath', 'ExclusionExtension', 'ExclusionProcess'):
            value = getattr(rows[0], key)
            if value is None:
                value = []
            value = list(value)
            if any(not isinstance(item, str) for item in value):
                raise ValueError('invalid actual Defender setting array')
            result[key] = value
        return result

    def add_path(self, path):
        cls = self.service.Get('MSFT_MpPreference')
        params = cls.Methods_('Add').InParameters.SpawnInstance_()
        params.Properties_('ExclusionPath').Value = [path]
        output = cls.ExecMethod_('Add', params)
        if output is None:
            return None
        try:
            return int(output.Properties_('ReturnValue').Value)
        except Exception as error:
            return {'return_value': None, 'return_decode_error': type(error).__name__ + ': ' + str(error)}

def runtime_guard(policy, policy_sha256):
    """Every code/config leaf is hash/ACL checked; no external import origin."""
    from native_safety import NativeSafety
    from protected_runtime import require_fixed_protected_root
    require_fixed_protected_root(policy['runtime_root'])
    root = Path(INSTALL_ROOT)
    safety = NativeSafety(policy['owner_sid'], policy['frozen_dir'], policy['receipts_dir'])
    verify_outer_parents(safety)
    with safety.lock_dir(INSTALL_ROOT):
        safety.verify_protected_path(INSTALL_ROOT)
        for name in ('policy.json', 'runtime-seal.json', 'installation-manifest.json'):
            safety.verify_protected_path(str(root / name))
        with safety.lock_file(str(root / 'policy.json')) as lease:
            if sha(lease.read_bytes(2 * 1024 * 1024)) != policy_sha256:
                raise ValueError('actual protected policy changed')
        with safety.lock_file(str(root / 'runtime-seal.json')) as lease:
            raw = lease.read_bytes(2 * 1024 * 1024)
        if sha(raw) != policy['runtime_manifest_sha256']:
            raise ValueError('actual runtime seal changed')
        seal = strict_json(raw)
        if set(seal) != {'schema', 'installation_id', 'python_version', 'files'} or seal['schema'] != 'xar.project-exe-broker.runtime-seal.v1':
            raise ValueError('invalid protected seal schema')
        if seal['installation_id'] != policy['installation_id'] or seal['python_version'] != sys.version.split()[0]:
            raise ValueError('runtime/installation identity mismatch')
        origins = {}
        seen = set()
        for row in seal['files']:
            if set(row) != {'path', 'size', 'sha256'} or type(row['size']) is not int:
                raise ValueError('invalid runtime inventory')
            relative = relative_path(row['path'])
            if relative.casefold() in seen:
                raise ValueError('duplicate runtime inventory path')
            seen.add(relative.casefold())
            path = root / relative
            safety.verify_protected_path(str(path))
            with safety.lock_file(str(path)) as lease:
                data = lease.read_bytes(max(row['size'], 1))
                if len(data) != row['size'] or sha(data) != row['sha256']:
                    raise ValueError('protected runtime file changed: ' + relative)
            origins[ntpath.normcase(str(path))] = row
        if ntpath.normcase(sys.executable) not in origins:
            raise ValueError('unsealed executable')
        for module in list(sys.modules.values()):
            path = getattr(module, '__file__', None)
            if path is None:
                continue
            if ntpath.normcase(str(Path(path))) not in origins:
                raise ValueError('unsealed loaded module origin: ' + str(path))
    return {'runtime_verified': True, 'protected_code': True,
            'runtime_manifest_sha256': policy['runtime_manifest_sha256']}
