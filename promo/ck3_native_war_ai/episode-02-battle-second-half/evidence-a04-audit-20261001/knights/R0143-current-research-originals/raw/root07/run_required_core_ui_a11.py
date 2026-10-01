"""Collect finite-case original UI outside the single-day monitor window."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys
ROOT = Path(__file__).resolve().parent
CONSUMER = ROOT / 'scoped_ui_research_a08.py'
SHA = '169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640'
def ident(p):
    b = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest().upper()}
def require(ok, msg):
    if not ok: raise RuntimeError(msg)
def write(p, v):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--bindings', type=Path, required=True)
p.add_argument('--phase', choices=['before', 'after'], required=True)
p.add_argument('--output-dir', type=Path, required=True)
a = p.parse_args()
require(ident(CONSUMER)['sha256'] == SHA, 'Original UI controller changed')
cfg = json.loads(a.bindings.read_text(encoding='utf-8'))
evidence = Path(cfg['live_root']) / 'scoped-ui-research-attempt-01'
if a.phase == 'before':
    require(not (evidence / 'one-day-intent.json').exists() and not (evidence / 'variable-monitor-begin-intent.json').exists(), 'Before UI must precede day observer')
else:
    require((evidence / 'one-day-finished.json').is_file() and (evidence / 'variable-monitor-finish.json').is_file(), 'After UI requires actual day and observer finish')
    monitor = json.loads((evidence / 'variable-monitor-finish.json').read_text(encoding='utf-8'))
    require(monitor['scoped_variable_monitor']['detours_uninstalled'] is True, 'Monitor hooks remain installed')
ops = [('pre-ui-checkpoint', []), ('victim-character', ['--mode', 'ui', '--window-kind', 'character', '--character-role', 'victim']), ('killer-character', ['--mode', 'ui', '--window-kind', 'character', '--character-role', 'killer']), ('combat', ['--mode', 'ui', '--window-kind', 'combat']), ('combat-fit', ['--mode', 'fit'])]
a.output_dir.mkdir(exist_ok=False)
write(a.output_dir / 'intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'bindings': ident(a.bindings), 'controller': ident(CONSUMER), 'helper': ident(Path(__file__)), 'operations': ops, 'game_days_advanced': 0, 'UI_outside_daily_monitor': True, 'knight_scope': 'Active combat tooltips, not unrelated eligible military list'})
receipts = []
for i, (label, flags) in enumerate(ops, 1):
    helper = ROOT / 'preserve_paused_ui_checkpoint_a06.py' if label == 'pre-ui-checkpoint' else CONSUMER
    argv = [sys.executable, '-X', 'utf8=0', '-B', str(helper), '--bindings', str(a.bindings.resolve()), *flags, '--phase', a.phase, '--label', a.phase + '-' + label]
    prefix = f'{i:02d}-{a.phase}-{label}'
    out, err = a.output_dir / (prefix + '-stdout.bin'), a.output_dir / (prefix + '-stderr.bin')
    write(a.output_dir / (prefix + '-argv.json'), {'argv': argv})
    print('start ' + prefix, flush=True)
    with out.open('xb') as stdout, err.open('xb') as stderr:
        result = subprocess.run(argv, stdout=stdout, stderr=stderr)
    receipt = {'argv': argv, 'returncode': result.returncode, 'stdout': ident(out), 'stderr': ident(err)}
    write(a.output_dir / (prefix + '-result.json'), receipt)
    receipts.append(receipt)
    print('complete ' + prefix + ' exit=' + str(result.returncode), flush=True)
    require(result.returncode == 0, 'Original UI refused; preserve and diagnose, no retry')
write(a.output_dir / 'completion.json', {'phase': a.phase, 'processes': receipts, 'original_pixels_actually_reviewed': False, 'human_movie_signoff': False})
