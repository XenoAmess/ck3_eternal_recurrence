import sys,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02/ck3-output')
deadline=time.monotonic()+55
while time.monotonic()<deadline:
    if (OUT/'entry-failure.json').exists() or (OUT/'hot-failure-state.json').exists():raise RuntimeError('Owner failure retained; inspect same process')
    if (OUT/'interactive-requests-responses/service.json').exists():
        r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'capture_gui_census.py')])
        raise SystemExit(r.returncode)
    time.sleep(1)
print('Loaded map observed; owning request service not yet ready. No request submitted.')
