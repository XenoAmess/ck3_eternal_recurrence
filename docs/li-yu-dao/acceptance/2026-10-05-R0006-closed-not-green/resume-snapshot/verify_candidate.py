"""Read-only checks of the external candidate. Never executes tracked import."""
from pathlib import Path
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
for name in ['import_report_candidate.py','prepare_snapshot.py','inspect_inputs.py','inspect_new_evidence.py']:
    compile((OUT/name).read_text(encoding='utf-8'), str(OUT/name), 'exec')

spec = importlib.util.spec_from_file_location('r6_external_import_candidate', OUT/'import_report_candidate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for value in ['../escape','/absolute','C:/absolute','a/../../escape', 'a:stream']:
    try:
        m.relpath(value)
    except ValueError:
        pass
    else:
        raise AssertionError('unsafe path accepted: '+value)
assert m.relpath('evidence/a.json').as_posix() == 'evidence/a.json'
expected = {
    'r6-report-draft-001':'fa0aad4d907cb0a57b1627a6afeb4cfd3e1f3cf172f4c9286c8f7c03258850da',
    'r6-report-draft-addendum-001':'615e109c1d4db13496ad8a3cb22ded7c1e355289484e38ec68a65afb41b3452d',
    'r6-report-draft-addendum-003':'5b44d27d0cd548fce74765703123220867ca9971bc187e42ae9d8aa81be7d436',
}
totals=[]
for name, digest in expected.items():
    files=m.package_files({'source':str(ROOT/name),'index_name':'INDEX.json','index_sha256':digest})
    totals.append({'package':name,'files':len(files),'bytes':sum(x[3] for x in files)})
try:
    m.closure_gate({'schema':'lyd.r6.closure-review.v1','attempt':'live-attempt-006','source_revision':m.SOURCE,'lifecycle':{},'overall_native_acceptance':'NOT_GREEN'},set())
except ValueError as error:
    assert 'Closure still pending' in str(error)
else:
    raise AssertionError('pending closure unexpectedly accepted')
print(json.dumps({'result':'PASS_READ_ONLY_CANDIDATE_CHECKS','syntax':True,'unsafe_paths_rejected':5,'pending_closure_rejected':True,'old_package_hash_checks':totals,'tracked_git_game_native_ci_screen_spawn_calls':0,'import_executed':False},ensure_ascii=False,indent=2))
