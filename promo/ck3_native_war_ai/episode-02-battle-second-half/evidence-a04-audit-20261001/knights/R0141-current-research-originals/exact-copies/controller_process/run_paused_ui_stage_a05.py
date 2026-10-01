"""Collect sequential paused original UI assets; stop before review or any day advance."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CONSUMER = ROOT / 'scoped_ui_research_a06.py'
CONSUMER_SHA = 'F77B638232D59594F0344E084B7FCE88DF3EB6BD1A27C99A0A734798BF3B4F52'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings', required=True, type=Path)
    parser.add_argument('--phase', required=True, choices=['before', 'after'])
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    require(identity(CONSUMER)['sha256'] == CONSUMER_SHA, 'Reviewed original GUI owner controller changed')
    config = json.loads(args.bindings.read_text(encoding='utf-8'))
    evidence = Path(config['live_root']) / 'scoped-ui-research-attempt-01'
    if args.phase == 'before':
        require(not (evidence / 'one-day-intent.json').exists(), 'Before UI must precede the original day')
    else:
        require((evidence / 'one-day-finished.json').is_file(), 'After UI requires original trace finished')
    args.output_dir.mkdir(exist_ok=False)
    operations = []
    if args.phase == 'before':
        operations.append(('monitor-begin', ['--mode', 'monitor-begin']))
    operations.append(('pre-ui-checkpoint', ['--mode', 'extra-checkpoint']))
    for role in ('victim', 'killer'):
        operations.append((role + '-character', ['--mode', 'ui', '--window-kind', 'character', '--character-role', role]))
    for kind in ('army', 'knights', 'combat'):
        operations.append((kind, ['--mode', 'ui', '--window-kind', kind]))
    operations.append(('combat-fit', ['--mode', 'fit']))
    for side in ('left', 'right'):
        operations.append((side + '-knights-tooltip', ['--mode', 'hover', '--ui-side', side]))
    operations.append(('save', ['--mode', 'save']))
    write(args.output_dir / 'stage-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'phase': args.phase,
          'bindings': identity(args.bindings), 'controller': identity(CONSUMER),
          'stage_helper': identity(__file__), 'extra_checkpoint_helper': identity(ROOT / 'preserve_paused_ui_checkpoint_a04.py'),
          'operations': operations,
          'never_advances_a_day': True, 'automatic_pixel_review_or_signoff': False})
    receipts = []
    for index, (label, flags) in enumerate(operations, 1):
        prefix = f'{index:02d}-{args.phase}-{label}'
        argv = [sys.executable, '-X', 'utf8=0', '-B', str(CONSUMER), '--bindings', str(args.bindings.resolve()),
                *flags, '--phase', args.phase, '--label', args.phase + '-' + label]
        if label == 'pre-ui-checkpoint':
            argv = [sys.executable, '-X', 'utf8=0', '-B', str(ROOT / 'preserve_paused_ui_checkpoint_a04.py'),
                    '--bindings', str(args.bindings.resolve()), '--phase', args.phase,
                    '--label', args.phase + '-pre-ui-checkpoint']
        write(args.output_dir / (prefix + '-argv.json'), {'argv': argv, 'at_utc': datetime.now(timezone.utc).isoformat()})
        print('start ' + prefix, flush=True)
        stdout_path = args.output_dir / (prefix + '-stdout.bin')
        stderr_path = args.output_dir / (prefix + '-stderr.bin')
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            result = subprocess.run(argv, stdout=stdout, stderr=stderr)
        receipt = {'at_utc': datetime.now(timezone.utc).isoformat(), 'argv': argv, 'returncode': result.returncode,
                   'stdout': identity(stdout_path), 'stderr': identity(stderr_path)}
        write(args.output_dir / (prefix + '-result.json'), receipt)
        receipts.append(receipt)
        print('complete ' + prefix + ' exit=' + str(result.returncode), flush=True)
        require(result.returncode == 0, 'Paused UI stage stopped on failed postcondition; original attempts preserved, no day advance')
    write(args.output_dir / 'completion.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'phase': args.phase,
          'processes': receipts, 'result': 'PAUSED_UI_AND_SAVE_ASSETS_CAPTURED_PENDING_ACTUAL_ROOT_REVIEW',
          'original_pixels_actually_reviewed': False, 'day_advance_count': 0, 'human_movie_signoff': False})
    print('Paused UI assets captured. Root must inspect exact original pixels before the next gated operation.', flush=True)


if __name__ == '__main__':
    main()
