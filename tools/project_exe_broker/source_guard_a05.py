"""Root ordinary source preparation only; no UAC/Task/WMI invocation.

Stage 1 hardens owned nodes without old mutable-target NativeSafety snapshots.
Stage 2 acquires final stable leases, verifies all bytes/ACLs and retains them
through Root's separately authorized installation child.
"""
from contextlib import ExitStack, contextmanager
from pathlib import Path
import hashlib
import json
import sys

CAPSULE=Path(r'C:/ck3-war-episode04-research-20261004-a01/defender-demand-broker-install-candidate-a01/assembly-a06-resume')
PACKAGE=CAPSULE/'package'
EXPECTED='7577eb373feb532122b429b8be09dac28e519615fc23c48128abc1f0aa0fafb9'
OWNER='S-1-5-21-4063940640-1897558599-686929869-1001'
TRUSTED=(OWNER,'S-1-5-18','S-1-5-32-544')

class _ReadOnlySourceBackend:
    def __init__(self, delegate):self.delegate=delegate
    def __getattr__(self,name):return getattr(self.delegate,name)
    def open_existing(self,path,*,directory):
        if directory is not True:return self.delegate.open_existing(path,directory=directory)
        import ctypes
        backend=self.delegate;backend._api()
        handle=backend.CreateFile(backend._extended(path),0x00120080,1,None,3,
            0x00200000|0x02000000,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        return handle

def _source_sd(security,directory):
    flags='OICI' if directory else ''
    sddl='O:'+OWNER+'G:BAD:P'+''.join('(A;'+flags+';FA;;;'+sid+')' for sid in TRUSTED)
    return security.ConvertStringSecurityDescriptorToSecurityDescriptor(sddl,1)

def _exact_scope(proof,directory,descriptor_proof):
    raw=proof['security']
    descriptor_proof(raw,expected_owner=OWNER,allowed_writers=TRUSTED,
        require_protected=True,allowed_readers=TRUSTED)
    rows=raw['aces']
    if (len(rows)!=3 or {row['sid'] for row in rows}!=set(TRUSTED) or
        any(row['type']!=0 or row['mask']!=0x1F01FF or row['flags']!=(3 if directory else 0) for row in rows)):
        raise RuntimeError('actual source DACL differs from exact owner/SY/BA contract')

@contextmanager
def _owned_tree_lease(root,expected_files,native_module):
    """Internal ordinary-only algorithm; tiny-tree tests exercise this same code."""
    import win32security
    NativeSafety=native_module.NativeSafety
    descriptor_proof=native_module.descriptor_proof
    base=NativeSafety(OWNER,r'C:\Program Files\XAR CK3 Project EXE Broker\private-frozen',
        r'C:\Program Files\XAR CK3 Project EXE Broker\receipts')
    safety=NativeSafety(OWNER,base.frozen_dir,base.receipts_dir,
        backend=_ReadOnlySourceBackend(base._backend()))
    if safety.token_identity()!= {'sid':OWNER,'admin':False}:
        raise RuntimeError('actual ordinary authorized owner required')
    root=Path(root)
    directories={root}
    for relative in expected_files:
        if not isinstance(relative,str) or ':' in relative or '\\' in relative or any(p in ('','.','..') for p in relative.split('/')):
            raise RuntimeError('unsafe source inventory relative path')
        current=(root/relative).parent
        while current.is_relative_to(root):
            directories.add(current)
            if current==root:break
            current=current.parent
    flags=win32security.DACL_SECURITY_INFORMATION|win32security.PROTECTED_DACL_SECURITY_INFORMATION
    if type(flags) is not int or not -2147483648<=flags<=2147483647 or flags&0xffffffff!=0x80000004:
        raise RuntimeError('unexpected signed pywin32 security information')
    directory_sd=_source_sd(win32security,True)
    file_sd=_source_sd(win32security,False)
    with ExitStack() as stack:
        # Root must have been repaired/hardened with this exact OICI DACL first.
        # It stays unchanged, so this root/ancestor snapshot remains stable.
        root_lease=stack.enter_context(safety.lock_dir(str(root)))
        _exact_scope(safety.inspect_descriptor(str(root)),True,descriptor_proof)
        # Stage1: each owner query is closed before its target DACL changes.
        # No mutable target snapshot lease survives an intentional change.
        for path,directory in [(path,True) for path in sorted(directories,key=lambda p:len(p.parts)) if path!=root]+[
                (root/relative,False) for relative in expected_files]:
            before=safety.inspect_descriptor(str(path))
            if before['security']['owner_sid']!=OWNER:
                raise RuntimeError('actual source node owner mismatch')
            target_sd=directory_sd if directory else file_sd
            win32security.SetNamedSecurityInfo(str(path),win32security.SE_FILE_OBJECT,
                flags,None,None,target_sd.GetSecurityDescriptorDacl(),None)
            _exact_scope(safety.inspect_descriptor(str(path)),directory,descriptor_proof)
        # Stage2: fresh immutable snapshots all refer to final ACLs. Read-only
        # sharing rejects any old foreign WRITE/DELETE handles before yield.
        facts=[]
        for directory in sorted(directories,key=lambda p:len(p.parts)):
            lease=stack.enter_context(safety.lock_dir(str(directory)))
            proof=safety.inspect_descriptor(str(directory))
            _exact_scope(proof,True,descriptor_proof)
            facts.append({'path':str(directory),'kind':'directory','file_id':lease.file_id,'descriptor':proof})
        for relative,row in expected_files.items():
            path=root/relative
            lease=stack.enter_context(safety.lock_file(str(path),owner_sid=OWNER))
            data=lease.read_bytes(max(row['size'],1))
            if len(data)!=row['size'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
                raise RuntimeError('final held source bytes differ from approved bundle')
            proof=safety.inspect_descriptor(str(path))
            _exact_scope(proof,False,descriptor_proof)
            facts.append({'path':str(path),'kind':'file','file_id':lease.file_id,'descriptor':proof})
        discovered=set()
        for directory in directories:
            for entry in safety.list_files(str(directory)):
                if entry['is_file']:discovered.add(Path(entry['path']).relative_to(root).as_posix())
                elif Path(entry['path']) not in directories:
                    raise RuntimeError('unexpected source directory/import shadow')
        if discovered!=set(expected_files):raise RuntimeError('unexpected source files')
        root_lease.revalidate()
        yield {'source_owner_only_verified':True,'source_files':len(expected_files),
            'actual_owner_sid':OWNER,'directory_sharing':'READ only; no WRITE/DELETE',
            'stages':['owned_node_prehardening_no_old_target_snapshot','fresh_final_readonly_leases_acl_sha'],
            'facts':facts}

@contextmanager
def owner_only_source_lease():
    # Root restores CAPSULE root to exact owner/SY/BA OICI before importing.
    # The tested immutable lease algorithm is unchanged from helper a04.
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(PACKAGE))
    import native_safety
    raw=(CAPSULE/'resume-source-inventory.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:
        raise RuntimeError('exact approved a06 complete source inventory required')
    manifest=json.loads(raw)
    if (set(manifest)!={'schema','installation_id','files'} or
        manifest['schema']!='xar.project-exe-broker.resume-source-inventory.v1' or
        manifest['installation_id']!='83b30886-8dbc-4c9c-8177-d575be46a925'):
        raise RuntimeError('fixed resume source inventory schema required')
    files={row['path']:row for row in manifest['files']}
    if len(files)!=len(manifest['files']) or len(files)!=743:
        raise RuntimeError('exact resume source path set required')
    files['resume-source-inventory.json']={'size':len(raw),'sha256':EXPECTED}
    with _owned_tree_lease(CAPSULE,files,native_safety) as facts:
        facts['source_inventory_sha256']=EXPECTED
        facts['bundle_sha256']='4054437f4a6e18b8feeeab8d2ac91698e82b5006d0b5e49fb1b15afda22ca49e'
        yield facts

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps({'status':'context_only_no_changes','capsule':str(CAPSULE),
        'expected_source_inventory_sha256':EXPECTED,
        'usage':'owner_only_source_lease() is a parent context for this exact historical capsule; no UAC/Task/WMI is invoked.'},indent=2))
