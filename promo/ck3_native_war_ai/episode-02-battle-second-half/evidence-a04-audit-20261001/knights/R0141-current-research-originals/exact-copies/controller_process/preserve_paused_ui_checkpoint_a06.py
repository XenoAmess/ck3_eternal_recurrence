"""Preserve an extra same-process checkpoint before a paused UI window, without replacing the main pair."""
import argparse
from datetime import datetime, timezone
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
CONTROLLER = ROOT / 'scoped_ui_research_a08.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings', required=True, type=Path)
    parser.add_argument('--phase', required=True, choices=['before', 'after'])
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    with CONTROLLER.open('rb') as stream:
        actual_hash = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    if actual_hash != '169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640':
        raise RuntimeError('Reviewed controller bytes changed; no module execution')
    spec = importlib.util.spec_from_file_location('_reviewed_scoped_ui_a08', CONTROLLER)
    controller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controller)
    controller.require(controller.identity(CONTROLLER)['sha256'] == '169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640', 'Reviewed controller changed')
    controller.require(args.label == args.phase + '-pre-ui-checkpoint', 'Only declared extra pre-UI checkpoint allowed')
    config = controller.read(args.bindings)
    live, output, evidence, transport, steps = controller.bind(config)
    controller.require((evidence / 'variable-monitor-begin.json').is_file() and not (evidence / 'variable-monitor-finish-intent.json').exists(), 'Independent writer monitor must be armed')
    controller.require(not (evidence / (args.phase + '-saved-pair.json')).exists(), 'Main post-UI save already exists')
    if args.phase == 'before':
        controller.require(not (evidence / 'one-day-intent.json').exists(), 'Pre-day UI checkpoint too late')
    else:
        controller.require((evidence / 'one-day-finished.json').is_file(), 'Daily original trace must finish before after-day checkpoint')
    intent = evidence / (args.label + '-intent.json')
    controller.write(intent, {'at_utc': datetime.now(timezone.utc).isoformat(), 'phase': args.phase,
          'bindings': controller.identity(args.bindings), 'purpose': 'UI-window comparison with main post-UI phase save',
          'role': 'extra pre-UI checkpoint', 'day_advance_requested': False})
    date = config['before_date_raw'] if args.phase == 'before' else config['after_date_raw']
    body, receipt, values = controller.snapshot(output, transport, steps, args.label + '-source', date)
    saved, save_receipt = transport.call(output, args.label + '-save', 'ck3_save_checkpoint', {'expected_revision': values['revision']}, 120)
    checkpoint = saved.get('checkpoint', {})
    controller.require(saved.get('accepted') is True and checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == date, 'Actual native checkpoint refused')
    original = controller.identity(checkpoint['path'])
    controller.require(original['bytes'] == checkpoint['size'] and original['sha256'] == checkpoint['sha256'].upper(), 'Extra checkpoint native receipt mismatch')
    target = evidence / (args.label + '-immutable.ck3')
    with Path(original['path']).open('rb') as source, target.open('xb') as dest:
        shutil.copyfileobj(source, dest)
    controller.require(controller.identity(target)['sha256'] == original['sha256'], 'Extra immutable copy differs')
    post, post_receipt, post_values = controller.snapshot(output, transport, steps, args.label + '-post-source', date)
    # Native checkpoint updates the public revision. Compare the actual paused
    # subject/date fields without pretending the save is a presentation action.
    controller.require(all(post_values[key] == values[key] for key in ('date_raw', 'paused', 'actor', 'war_ids', 'army_id', 'army_state', 'episode_run_id',
                                                                      'connection_generation', 'native_hello_session_generation', 'bridge_pid')),
                       'Paused source/owner changed during extra checkpoint')
    record = {'at_utc': datetime.now(timezone.utc).isoformat(), 'phase': args.phase, 'role': 'extra pre-UI checkpoint',
              'source_binding': controller.identity(args.bindings), 'source_values': values, 'snapshot': receipt,
              'save': save_receipt, 'save_body': saved, 'immutable': controller.identity(target),
              'post_snapshot': post_receipt, 'post_values': post_values,
              'order_proof': 'Actual root stage argv/results before UI actions; independent comparison still required',
              'ui_window_unchanged_or_rng_unchanged_proven': False}
    controller.write(evidence / (args.label + '-saved-pair.json'), record)
    print(json.dumps({'result': 'EXTRA_PRE_UI_CHECKPOINT_PRESERVED_COMPARISON_PENDING', 'immutable': record['immutable']}))


if __name__ == '__main__':
    main()
