"""Restore the actual pre-run display and CAS-release a completed capture screen lease."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import psutil

ROOT = Path(__file__).resolve().parent
BUS = Path('D:/workspace/.codex-task-bus/bin/codex_task_bus.py')
BUS_SHA = 'B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screen-task-id', required=True)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--alignment-receipt', required=True, type=Path)
    parser.add_argument('--sdk-completion', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    require(hashlib.sha256(BUS.read_bytes()).hexdigest().upper() == BUS_SHA, 'Bus CLI bytes changed')
    completion = json.loads(args.sdk_completion.read_text(encoding='utf-8'))
    jobs = completion.get('jobs', [])
    require(jobs and all(row.get('exit_code') is not None for row in jobs), 'Actual SDK completion required before restore/release')
    blocked = [p.info for p in psutil.process_iter(['pid', 'name', 'create_time'])
               if (p.info['name'] or '').lower() in ('ck3.exe', 'ffmpeg.exe', 'obs64.exe', 'xar_ck3_bridge_injector.exe')]
    require(not blocked, 'Game/recorder/injector still active; screen remains acquired')
    task_path = Path('D:/workspace/.codex-task-bus/tasks') / (args.screen_task_id + '.json')
    task = json.loads(task_path.read_text(encoding='utf-8'))
    require(task['state'] == 'running' and task['resources'] == ['ck3-screen:acquired'], 'Actual screen ownership lost')
    require(Path(task['repo']).resolve() == args.source.resolve(), 'Wrong source checkout for screen task')
    args.output_dir.mkdir(exist_ok=False)
    command = [sys.executable, '-X', 'utf8=0', '-B', str(ROOT / 'display_mode_research.py'), '--mode', 'restore',
               '--screen-task-id', args.screen_task_id, '--expected-sequence', str(task['last_sequence']),
               '--alignment-receipt', str(args.alignment_receipt.resolve()), '--output-dir', str(args.output_dir / 'display-restore')]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=45)
    write(args.output_dir / 'display-restore-process.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
          'argv': command, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'Display restore failed; retain acquired lease and inspect originals')
    current = json.loads(task_path.read_text(encoding='utf-8'))
    require(current['last_sequence'] == task['last_sequence'] and current['resources'] == task['resources'], 'Screen CAS changed during restore')
    command = [sys.executable, str(BUS), '--expected-cli-sha256', BUS_SHA, 'release-screen-cas', '--task', args.screen_task_id,
               '--expected-sequence', str(task['last_sequence']), '--summary', 'native_research_capture_stopped_original_display_restored_assets_retained']
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    write(args.output_dir / 'screen-release-CAS.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
          'argv': command, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'Screen CAS release refused; inspect actual owner')
    print(json.dumps({'result': 'ACTUAL_DISPLAY_RESTORED_SCREEN_RELEASED', 'output': str(args.output_dir)}))


if __name__ == '__main__':
    main()
