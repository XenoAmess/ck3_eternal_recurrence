"""Explicit one-time owner-approved administrator installation; no auto UAC."""
from pathlib import Path
import sys

def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).parent,
                        help='Approved external package for a read-only plan; existing installs are refused.')
    parser.add_argument('--expected-bundle-sha256', required=True)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--receipt')
    args = parser.parse_args()
    package = args.package
    sys.path.insert(0, str(Path(__file__).parent))
    if args.install:
        if sys.flags.isolated != 1 or sys.flags.no_site != 1:
            raise RuntimeError('actual install requires bundled Python with -I -S -B')
        from protected_runtime import activate_sealed_paths
        activate_sealed_paths(package)
    from native_safety import NativeSafety
    from installer_core import OWNER, INSTALL_ROOT, prepare_plan, install
    safety = NativeSafety(OWNER, INSTALL_ROOT + r'\private-frozen', INSTALL_ROOT + r'\receipts')
    plan = prepare_plan(package, args.expected_bundle_sha256, safety)
    if not args.install:
        print(json.dumps(plan['summary'], ensure_ascii=False, indent=2))
        return 0
    if args.receipt is None:
        parser.error('--install requires a new external --receipt')
    import ntpath
    from native_safety import canonical_path
    receipt = canonical_path(args.receipt)
    allowed = 'C:\\ck3-war-episode04-research-20261004-a01\\'
    if not ntpath.normcase(receipt).startswith(ntpath.normcase(allowed)) or not receipt.lower().endswith('.json'):
        parser.error('receipt must be a new JSON file below the project external evidence root')
    from windows_adapter import WindowsInstallerAdapter
    adapter = WindowsInstallerAdapter(safety)
    result = install(plan, adapter, safety, receipt)
    print(json.dumps({'status': result['status'], 'receipt': receipt}, indent=2))
    return 0 if result['status'] == 'installed_initial_outputs_verified' else 1

if __name__ == '__main__':
    raise SystemExit(main())
