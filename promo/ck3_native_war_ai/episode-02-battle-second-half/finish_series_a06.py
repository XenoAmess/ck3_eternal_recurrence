"""Append actual a06 audit/review/delivery receipts to an already preserved run."""
from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path
import shutil

from xar_promo.operations import preserve_artifact
from xar_promo.project import load_document
from xar_promo.runlog import append_automated_audit_record, append_phase_record

import review_story_a04 as producer

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--quality', required=True, type=Path)
    args = parser.parse_args()
    run = args.run
    manifest = run / 'native-run/run-manifest.json'
    final = producer.read(run / 'final-brown-gold-artifact.json')
    audit, quality = producer.read(args.audit), producer.read(args.quality)
    delivery = producer.read(run / 'delivery/final-delivery.json')
    if audit['machine_condition_status'] != 'PASS' or audit['final_artifact']['sha256'] != final['sha256']:
        raise ValueError('Exact final-byte media audit is missing')
    if quality['verdict'] != 'PASS_PENDING_HUMAN_REVIEW' or quality['subject']['sha256'] != final['sha256']:
        raise ValueError('Exact final-byte limited frame review is missing')
    if delivery['final_artifact']['sha256'] != final['sha256'] or delivery['files_transferred'] != 1:
        raise ValueError('Single-video delivery receipt belongs to another output')
    if delivery['status'] != 'CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED':
        raise ValueError('Client metadata does not show completed synchronization')
    frozen = run / 'finishing-sources'
    frozen.mkdir(exist_ok=False)
    for source in (Path(__file__), Path(__file__).with_name('deliver_series_a05.py')):
        shutil.copyfile(source, frozen / source.name)
    records = []
    paths = [(args.audit, 'a06-machine-report', 'machine-audit'),
             (args.quality, 'a06-frame-review', 'product-review'),
             (run / 'delivery/final-delivery.json', 'a06-delivery-receipt', 'delivery-evidence')]
    extras = [*sorted(frozen.glob('*')), *sorted((run / 'delivery').rglob('*')),
              *sorted((run / 'logs').glob('client-sync-*'))]
    paths.extend((path, f'a06-finish-{index:03d}', 'process-evidence')
                 for index, path in enumerate(extras, 1)
                 if path.is_file() and path.name != 'final-delivery.json')
    for path, aid, role in paths:
        record = preserve_artifact(manifest, path, artifact_id=aid, collection='derived',
                                   role=role, label=path.name,
                                   media_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        records.append({'source': producer.ref(path), 'preserved': record.to_dict()})
    append_automated_audit_record(manifest, check_id='a06-media-and-evidence-layout', status='passed',
                                  subject_artifact_id='a06-deliverable', report_artifact_id='a06-machine-report')
    append_phase_record(manifest, phase_id='a06-limited-actual-frame-review', status='succeeded',
                        artifact_ids=['a06-deliverable', 'a06-frame-review'],
                        detail='Confirmed label, glyph and time-bounded same-frame inset inspected. No full 1x viewing, listening, clean-span certification or human signoff.')
    append_phase_record(manifest, phase_id='a06-single-video-client-sync', status='succeeded',
                        artifact_ids=['a06-deliverable', 'a06-delivery-receipt'],
                        detail='One MP4 copied into the existing authorized folder; local SHA verified and client metadata InSync. No independent remote readback and no human approval.')
    loaded = load_document(manifest, check_files=True)
    if loaded.run.signoffs:
        raise ValueError('No human signoff was performed in this task')
    report = {'at_utc': producer.stamp(), 'final_artifact': final,
              'manifest': producer.ref(manifest), 'artifacts': records, 'human_signoffs': 0,
              'full_human_review': 'pending', 'remote_readback': 'not-performed',
              'scope': 'Declared a06 media/layout conditions and actual client synchronization only'}
    producer.write(run / 'finish-receipt.json', report)
    print(producer.ref(run / 'finish-receipt.json'))

if __name__ == '__main__':
    main()
