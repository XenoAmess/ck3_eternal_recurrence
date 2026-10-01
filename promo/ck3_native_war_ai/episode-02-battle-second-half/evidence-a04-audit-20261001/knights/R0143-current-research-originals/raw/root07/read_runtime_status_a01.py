from pathlib import Path
import json
import psutil
ROOT = Path(__file__).resolve().parent
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-trace-live-20261001-a07')
result = {'processes': [p.info for p in psutil.process_iter(['pid', 'name', 'create_time']) if (p.info['name'] or '').lower() in ('ck3.exe', 'xar_ck3_bridge_injector.exe')], 'live_exists': LIVE.exists()}
for n in ['live-run-identity.json', 'native-start-readback.json', 'interactive-mode-ready.json', 'capture-report.json']:
    p = LIVE / 'ck3-output' / n
    if not p.is_file():
        result[n] = None
        continue
    try:
        v = json.loads(p.read_text(encoding='utf-8'))
        if n == 'native-start-readback.json':
            s = v.get('snapshot', {})
            result[n] = {'postcondition_verified': v.get('postcondition_verified'), 'episode_run_id': s.get('episode_run_id'), 'date_raw': s.get('date_raw'), 'paused': s.get('paused'), 'native_revision': s.get('native_revision'), 'actor': s.get('played_character', {}).get('character_id')}
        elif n == 'live-run-identity.json':
            result[n] = v
        else:
            result[n] = {'result': v.get('result'), 'status': v.get('status')}
    except Exception as e:
        result[n] = {'read_error': repr(e)}
log = ROOT / 'sdk-process-logged-a01/stdout.bin'
result['SDK_stdout_tail'] = log.read_bytes().decode('utf-8', errors='replace')[-1500:] if log.is_file() else None
task = Path('D:/workspace/.codex-task-bus/tasks/war-e2-six-gap-trace-diagnostic-screen-20261001-a06.json')
result['screen'] = json.loads(task.read_text(encoding='utf-8')) if task.is_file() else None
print(json.dumps(result))
