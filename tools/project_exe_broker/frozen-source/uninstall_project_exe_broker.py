"""Prepare exact uninstall scope and preservation steps; never delete anything."""
from pathlib import Path
import sys

def main():
    sys.path.insert(0, str(Path(__file__).parent))
    from protected_runtime import activate_sealed_paths
    activate_sealed_paths(Path(__file__).parent)
    from installer_core import INSTALL_ROOT, OWNER, task_spec
    import json
    plan = {'status': 'uninstall_prepared_only', 'settings_mutation': False,
        'deletion_executed': False, 'fixed_task': task_spec(OWNER),
        'fixed_protected_bundle': INSTALL_ROOT,
        'exact_execution_order': [
            'Require separately authorized elevated owner token and exact installed UUID/policy/seal/current task action and ACL.',
            'Disable only this exact task; stop its actual instances and wait for actual non-running state.',
            'Revoke inbox ordinary writes; refuse any existing reparse or changed file identity.',
            'Freeze and preserve every runtime/config/inbox/private/receipt file into a fresh external archive with exact source identities and copy SHA inventory.',
            'Require complete archive verification before deleting the exact named task, then exact named empty folder.',
            'Remove only the exact protected bundle after checking absolute path, volume/file identity and no reparse; preserve failures and never traverse a new junction.'
        ],
        'defender_exclusions': 'Prior and project ExclusionPath entries remain; uninstall never removes settings.',
        'execution_implemented': False}
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
