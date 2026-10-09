"""Append one reviewed plan; errored hosts admit only failure finish_hold transport."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def failure_finish_only(steps):
    if len(steps) != 1 or not isinstance(steps[0], dict):
        return False
    step = steps[0]
    expected = step.get('expect')
    return (step.get('kind') == 'finish_hold' and step.get('failure_shutdown') is True
            and isinstance(expected, dict)
            and set(expected) == {'hold_finished', 'failure_preserved', 'business_pass', 'normal_close_qualified'}
            and expected['hold_finished'] is True and expected['failure_preserved'] is True
            and expected['business_pass'] is False and expected['normal_close_qualified'] is False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--live', required=True, type=Path)
    p.add_argument('--plan', required=True, type=Path)
    p.add_argument('--name', required=True)
    args = p.parse_args()
    require(Path(args.name).name == args.name and args.name.endswith('.json'), 'Invalid once-only plan name')
    for attempt in range(15):
        try:
            report = json.loads((args.live / 'native-report.json').read_bytes())
            break
        except (PermissionError, json.JSONDecodeError):
            if attempt == 14:
                raise
            time.sleep(0.1)
    require(report['phase'] == 'hold' and not report.get('finished_at'), 'Host must be in its original unfinished hold')
    require(not report.get('hold_finished_by_control_plan'), 'Original hold was already finished')
    require(all(row.get('finished_at') for row in report.get('steps', [])), 'Original step is incomplete')
    raw = args.plan.read_bytes()
    plan = json.loads(raw)
    require(isinstance(plan['steps'], list) and plan['steps'], 'A nonempty step list is required')
    lifecycle_only = report.get('error') is not None
    require(not lifecycle_only or failure_finish_only(plan['steps']),
            'Failed host admits only one preserved-failure finish_hold lifecycle request')
    new_ids = [row['id'] for row in plan['steps']]
    require(len(new_ids) == len(set(new_ids)), 'Duplicate step IDs in plan')
    require(not set(new_ids) & {row['id'] for row in report['steps']}, 'Step ID already consumed; never replay')
    frozen = json.loads((args.live / 'frozen-argv.json').read_bytes())
    argv = frozen['argv']
    controls = Path(argv[argv.index('--control-plan-dir') + 1]).resolve()
    require(controls == (args.live / 'controls').resolve(), 'Frozen controls binding changed')
    target = controls / args.name
    temp = target.with_suffix('.tmp')
    require(not target.exists() and not temp.exists(), 'Already dispatched; inspect, never replay')
    with temp.open('xb') as stream:
        stream.write(raw)
    os.rename(temp, target)
    receipt = {'submitted_once': str(target), 'bytes': len(raw),
               'sha256': hashlib.sha256(raw).hexdigest(),
               'step_ids': new_ids, 'business_result_pending': not lifecycle_only}
    if lifecycle_only:
        receipt.update(failure_lifecycle_transport_only=True, host_error_preserved=report['error'],
                       business_pass=False, normal_close_qualified=False)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
