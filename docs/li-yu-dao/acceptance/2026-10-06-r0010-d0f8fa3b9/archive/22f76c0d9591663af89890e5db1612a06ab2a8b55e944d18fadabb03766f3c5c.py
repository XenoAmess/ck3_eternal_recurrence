import hashlib
import json
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parent
wrapper = root / 'build_exact_release.py'
report = Path('C:/workspace/ck3_lyd_runtime_20261004/r10-root-head-export-20261005-001/REPORT.json')
expected_wrapper = '3aa48eae47945da61ee25c52d9661f8c5e93773d62f062b5ef56317e0b7a0656'
expected_export = 'f2b0f6d91a565648ecdb0be8c3aec1d88b67c468bc8a5623aba347f58ee7b0e4'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest() == expected_wrapper
assert hashlib.sha256(report.read_bytes()).hexdigest() == expected_export
value = json.loads(report.read_bytes())
assert value['source']['head'] == 'd0f8fa3b9d444828759443aa018bfd7ad31b398d'
assert value['source']['native_tree'] == '789eab5ae1c3015fe210de508fdd730a13bbb8db'
assert Path(value['source_root']).resolve() == Path('C:/lr10s1').resolve()
argv = [sys.executable, '-I', '-B', str(wrapper), '--export-report', str(report),
        '--export-sha256', expected_export, '--expected-head', value['source']['head'],
        '--source-dir', 'C:/lr10s1', '--build-dir', 'C:/lydr10-release-20261005-001',
        '--output', 'C:/workspace/ck3_lyd_runtime_20261004/r10-actual-release-build-20261005-001', '--execute']
receipt = root / 'AUTHORIZED-ONCE-INVOCATION.json'
with receipt.open('xb') as stream:
    stream.write((json.dumps({'actual_root_authorized_HEAD': value['source']['head'], 'native_tree': value['source']['native_tree'], 'wrapper_sha256': expected_wrapper, 'export_sha256': expected_export, 'argv': argv, 'cold_runtime_not_invoked': True}, indent=2) + '\n').encode())
print(json.dumps({'status': 'EXACT_AUTHORIZED_SOURCE_CHECKED_BEGIN_ONCE_BUILD', 'argv': argv}), flush=True)
process = subprocess.run(argv)
raise SystemExit(process.returncode)
