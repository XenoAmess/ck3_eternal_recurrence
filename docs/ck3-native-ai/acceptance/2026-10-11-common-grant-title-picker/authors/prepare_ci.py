"""Create a separate one-path CI delta; preserve the qualified production/test patch."""
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path('C:/workspace/ck3_eternal_recurrence')
RELATIVE = '.github/workflows/static-ci.yml'
before = (REPO/RELATIVE).read_bytes()
newline = b'\r\n' if b'\r\n' in before else b'\n'
text = before.decode('utf-8').replace('\r\n','\n')
old = '          python -B -X utf8 tools/test_ck3_mod_acceptance.py\n          if not "%errorlevel%"=="0" exit /b %errorlevel%\n'
new = old + '          python -B -X utf8 tools/test_ck3_mod_acceptance_grant_title_picker.py -v\n          if not "%errorlevel%"=="0" exit /b %errorlevel%\n'
if text.count(old) != 1 or 'python -m pip install mcp==2.0.0' not in text:
    raise ValueError('Reviewed shared-acceptance CI entry/dependency preimage changed')
after = text.replace(old,new,1).replace('\n', newline.decode('ascii')).encode('utf-8')
diff = ''.join(difflib.unified_diff(before.decode('utf-8').replace('\r\n','\n').splitlines(True),
    after.decode('utf-8').replace('\r\n','\n').splitlines(True),
    fromfile='a/'+RELATIVE, tofile='b/'+RELATIVE)).encode('utf-8')
def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
out = HERE/'ci-001'
out.mkdir(exist_ok=False)
(out/'PUBLIC-GRANT-CI.incremental.patch').write_bytes(diff)
manifest = {'schema':'lyd.common-grant-public-ci-source-only.v1', 'status':'SOURCE_ONLY_NOT_RUN',
    'relative_path':RELATIVE, 'before':pin(before), 'after':pin(after),
    'patch': {'path':str(out/'PUBLIC-GRANT-CI.incremental.patch'), **pin(diff)},
    'entry': ['python','-B','-X','utf8','tools/test_ck3_mod_acceptance_grant_title_picker.py','-v'],
    'same_existing_shared_acceptance_job':True, 'existing_mcp_2_dependency':True,
    'production_and_test_bytes_unchanged':True, 'CI_or_tests_executed':False,
    'MAIN_mutations':0, 'future_CI_result':None}
(out/'INTEGRATION-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(manifest))
