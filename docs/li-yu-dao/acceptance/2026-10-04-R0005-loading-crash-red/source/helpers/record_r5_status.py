from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent
RUN = BASE / 'live-attempt-005'
REPO = Path('C:/workspace/ck3_eternal_recurrence')
assert json.loads((RUN / 'screen-release-completed.json').read_text(encoding='utf-8'))['task']['resources'] == []
argv = [sys.executable, str(REPO / 'tools/ck3_live_run_id.py'), 'status', '--run-id', 'bf-202609141645-5434332d4d--li-yu-dao--R0005', '--mod', 'li-yu-dao', '--status', 'completed-red', '--reason', 'R0005-C3-loading-errors-crash-observed-after-WM-close-no-campaign-no-native-attach-reporter-closed']
result = subprocess.run(argv, cwd=REPO, capture_output=True, check=False)
for kind in ('stdout', 'stderr'):
    with (RUN / ('allocator-completed-red.' + kind + '.txt')).open('xb') as stream:
        stream.write(getattr(result, kind))
assert result.returncode == 0
print(result.stdout.decode('utf-8-sig'))
