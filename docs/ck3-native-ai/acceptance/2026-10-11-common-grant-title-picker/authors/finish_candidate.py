"""Preserve the first test source; correct only the MCP metadata accessor."""
from pathlib import Path
import ast
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TEST = HERE/'test_ck3_mod_acceptance_grant_title_picker.py'
before = TEST.read_bytes()
with (HERE/'focused-001/test-source.original.py').open('xb') as stream:
    stream.write(before)
old = b"            self.assertEqual((annotation.readOnlyHint, annotation.destructiveHint, annotation.idempotentHint), hints)"
new = b"            aliases = annotation.model_dump(by_alias=True)\n            self.assertEqual(tuple(aliases[key] for key in ('readOnlyHint', 'destructiveHint', 'idempotentHint')), hints)"
if before.count(old) != 1:
    raise ValueError('Original metadata accessor is not unique')
after = before.replace(old, new, 1)
ast.parse(after.decode('utf-8'))
TEST.write_bytes(after)
result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(HERE/'prepare_candidate.py'),
    '--repo', 'C:/workspace/ck3_eternal_recurrence', '--output', str(HERE/'candidate-002')], check=False)
raise SystemExit(result.returncode)
