"""Deliver only the corrected episode MP4 through the existing OneDrive folder.

Reuse the frozen single-file transfer and no-recall client metadata probe.
No settings changes, cloud downloads, replacements or manual approvals.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import sys
import time
from pathlib import Path

import review_story_a04 as producer
from recolor_series_a05 import NEW_NAME

TRANSFER = Path('D:/workspace/ck3_native_war_ai_promo_work/episode02-five-raw-onedrive-transfer-20260930-a01/transfer_one.py')
TRANSFER_SHA = '346BB245ECEF307BBD8480F1FF655414B107D347493DDF085C62C22EA9613DB6'
PROBE = Path('D:/ck3-research-artifacts/onedrive-cloud-status-probe-20260930-a01/probe.py')
PROBE_SHA = '8488B9A4BC152825A6664C762CD842288348AD4B80271DF153E4C6F81CF03E85'
DELIVERY_FOLDER = Path('C:/Users/1/OneDrive/CK3-War-AI-20260923')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--quality', required=True, type=Path)
    parser.add_argument('--name', default=NEW_NAME,
                        help='Exact requested video basename; default is the palette-only a05')
    args = parser.parse_args()
    run = args.run
    final = producer.read(run / 'final-brown-gold-artifact.json')
    audit = producer.read(args.audit)
    quality = producer.read(args.quality)
    if audit['machine_condition_status'] != 'PASS' or audit['final_artifact']['sha256'] != final['sha256']:
        raise ValueError('fresh exact-byte media audit must pass before copying')
    if quality['verdict'] != 'PASS_PENDING_HUMAN_REVIEW' or quality['subject']['sha256'] != final['sha256']:
        raise ValueError('actual final-frame packaging review must pass before copying')
    if producer.ref(TRANSFER)['sha256'] != TRANSFER_SHA or producer.ref(PROBE)['sha256'] != PROBE_SHA:
        raise ValueError('frozen transfer/probe source changed')
    source = Path(final['path'])
    if Path(args.name).name != args.name or not args.name.endswith('.mp4'):
        raise ValueError('delivery name must be a single MP4 basename')
    target = DELIVERY_FOLDER / args.name
    if source.name != args.name or producer.ref(source) != {key: final[key] for key in ['path', 'bytes', 'sha256']}:
        raise ValueError('final producer MP4 changed')
    delivery = run / 'delivery'
    delivery.mkdir(exist_ok=False)
    producer.write(delivery / 'input.json', {
        'at_utc': producer.stamp(), 'source': final, 'target': str(target),
        'audit': producer.ref(args.audit), 'quality': producer.ref(args.quality),
        'transfer': producer.ref(TRANSFER), 'probe': producer.ref(PROBE),
        'authorization': 'User requested Episode 2 palette/evidence corrections; existing fixed-folder video delivery authorization applies.',
        'files_transferred': 1, 'human_signoff': 'not-provided',
    })
    spec = importlib.util.spec_from_file_location('series_single_transfer', TRANSFER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.FILES = (('series-video', source, final['bytes'], final['sha256']),)
    module.ATTEMPT_ROOT = delivery
    stdout, stderr = io.StringIO(), io.StringIO()
    old_args = sys.argv
    try:
        sys.argv = [str(TRANSFER), '1']
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = module.main()
    finally:
        sys.argv = old_args
    producer.write(delivery / 'copy-execution.json', {
        'at_utc': producer.stamp(), 'exit_code': code,
        'stdout': stdout.getvalue(), 'stderr': stderr.getvalue(),
    })
    if code:
        raise RuntimeError('single-file transfer failed; partial and logs retained')
    samples = []
    for index in range(1, 61):
        output = producer.command(run, f'client-sync-{index:02d}', [sys.executable, str(PROBE), str(target)])
        raw = json.loads(output.read_text(encoding='utf-8'))
        checks = {
            'exact_path': raw.get('path') == str(target),
            'exact_size': raw.get('size') == final['bytes'],
            'stable_size_mtime': raw.get('stable_size_mtime') is True,
            'sync_root_success': raw.get('sync_root_hresult') == '0x00000000',
            'placeholder_success': raw.get('placeholder_hresult') == '0x00000000',
            'sync_root_id': raw.get('sync_root_file_id') == 5910974510929700,
            'in_sync': raw.get('in_sync_state') == 1,
            'validated_full_size': raw.get('validated') == final['bytes'],
            'modified_zero': raw.get('modified') == 0,
        }
        record = {'at_utc': producer.stamp(), 'raw': raw, 'checks': checks}
        producer.write(delivery / f'client-sample-{index:02d}.json', record)
        samples.append(record)
        if all(checks.values()):
            break
        time.sleep(10)
    success = all(samples[-1]['checks'].values())
    report = {'at_utc': producer.stamp(),
              'status': 'CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED' if success else 'CLIENT_SYNC_PENDING',
              'final_artifact': final, 'target': str(target), 'files_transferred': 1,
              'local_copy': producer.read(delivery / 'file-01-series-video/04-local-copy-verified.json'),
              'last_client_sample': samples[-1], 'sample_count': len(samples),
              'remote_independent_readback_performed': False, 'human_signoff': 'not-provided',
              'other_cloud_files_downloaded': False, 'old_outputs_changed': False}
    producer.write(delivery / 'final-delivery.json', report)
    print(json.dumps({'status': report['status'], 'target': str(target), 'sha256': final['sha256']}))
    if not success:
        raise SystemExit(3)


if __name__ == '__main__':
    main()
