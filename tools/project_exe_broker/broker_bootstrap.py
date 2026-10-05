"""Only fixed protected SYSTEM entry; no request-selected code/commands."""
from pathlib import Path
import os
import sys

ROOT = r'C:\Program Files\XAR CK3 Project EXE Broker'
CONFIG = ROOT + r'\policy.json'

def main():
    # Do not resolve links before the Win32 no-follow proof.
    import ntpath
    if ntpath.normcase(str(Path(__file__).parent)) != ntpath.normcase(ROOT):
        raise RuntimeError('broker refuses unprotected external installation')
    if sys.argv[1:] != ['--config', CONFIG]:
        raise RuntimeError('fixed protected policy only; no arbitrary arguments')
    if sys.flags.isolated != 1 or sys.flags.no_site != 1:
        raise RuntimeError('isolated no-site Python required')
    os.chdir(ROOT)
    sys.path.insert(0, ROOT)
    from protected_runtime import activate_sealed_paths, require_fixed_protected_root
    require_fixed_protected_root(ROOT)
    activate_sealed_paths(ROOT)
    os.environ['PATH'] = ';'.join([ROOT + r'\runtime', ROOT + r'\runtime\DLLs',
                                  ROOT + r'\deps\pywin32_system32', r'C:\Windows\System32'])
    from native_safety import NativeSafety
    from installer_core import strict_json
    safety = NativeSafety('S-1-5-21-4063940640-1897558599-686929869-1001',
        ROOT + r'\private-frozen', ROOT + r'\receipts')
    identity = safety.token_identity()
    if identity != {'sid': 'S-1-5-18', 'admin': True}:
        raise RuntimeError('actual SYSTEM token required')
    safety.verify_protected_path(CONFIG)
    with safety.lock_file(CONFIG) as lease:
        policy_bytes = lease.read_bytes(2 * 1024 * 1024)
    policy = strict_json(policy_bytes)
    if policy['runtime_root'].replace('/', '\\') != ROOT:
        raise RuntimeError('fixed installation required')
    from windows_adapter import runtime_guard, SameAdminDefenderClient
    from worker_core import run_once
    return run_once(policy_bytes, safety, SameAdminDefenderClient, runtime_guard)

if __name__ == '__main__':
    main()
