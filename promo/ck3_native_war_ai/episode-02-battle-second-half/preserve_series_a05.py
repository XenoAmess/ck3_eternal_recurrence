"""Bind the actual recolored media and declared checks to its immutable run.

Human full-speed watching, listening and clean-span approval stay pending.
"""
from __future__ import annotations

import argparse
import mimetypes
import re
from pathlib import Path

from xar_promo.operations import preserve_artifact
from xar_promo.project import load_document
from xar_promo.runlog import append_automated_audit_record, append_phase_record

import review_story_a04 as producer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--quality', type=Path, required=True)
    parser.add_argument('--artifact-prefix', default='a05')
    parser.add_argument('--not-delivered-reason',
                        help='Preserve an intermediate revision without claiming delivery')
    parser.add_argument('--phase-detail', default='Project composer rebuilt 154 boards and all six chapters; 13 raw shots retain their source and timing. Final AAC stream copied from the unchanged a04. No CLI build claim.')
    args = parser.parse_args()
    run = args.run
    prefix = args.artifact_prefix
    if not re.fullmatch(r'[a-z0-9-]+', prefix):
        raise ValueError('artifact prefix must be a plain lower-case identifier')
    manifest = run / 'native-run/run-manifest.json'
    final = producer.read(run / 'final-brown-gold-artifact.json')
    audit, quality = producer.read(args.audit), producer.read(args.quality)
    if audit['machine_condition_status'] != 'PASS' or audit['final_artifact']['sha256'] != final['sha256']:
        raise ValueError('exact final media audit is missing')
    if quality['verdict'] != 'PASS_PENDING_HUMAN_REVIEW' or quality['subject']['sha256'] != final['sha256']:
        raise ValueError('exact final-frame packaging review is missing')
    delivery_path = run / 'delivery/final-delivery.json'
    if not delivery_path.is_file() and not args.not_delivered_reason:
        raise ValueError('actual delivery receipt or explicit not-delivered reason required')
    records = []

    def preserve(path: Path, aid: str, role: str) -> None:
        record = preserve_artifact(manifest, path, artifact_id=aid, collection='derived',
                                   role=role, label=path.name,
                                   media_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        records.append({'source': producer.ref(path), 'preserved': record.to_dict()})

    preserve(Path(final['path']), f'{prefix}-deliverable', 'deliverable')
    preserve(args.audit, f'{prefix}-machine-report', 'machine-audit')
    preserve(args.quality, f'{prefix}-frame-review', 'product-review')
    paths = sorted(run.glob('*.json'))
    if delivery_path.is_file():
        paths.append(delivery_path)
    paths.extend(sorted((run / 'sources').glob('*')))
    paths.extend(sorted((run / 'logs').glob('*.receipt.json')))
    paths.extend(sorted((run / 'chapters').glob('*/chunk-*/subtitles.ass')))
    paths.extend(sorted((run / 'chapters').glob('*/chunk-*/filter.txt')))
    for index, path in enumerate(paths, 1):
        preserve(path, f'{prefix}-retained-{index:03d}', 'process-evidence')
    # Retain a source/hash index for every process file, including partials,
    # intermediate chapter encodes, PNGs and exact argv/stdout/stderr.
    index = {'at_utc': producer.stamp(), 'subject': final,
             'human_signoff': 'not-provided', 'production_clean_admission': False,
             'not_delivered_reason': args.not_delivered_reason,
             'process_files': [producer.ref(path) for path in sorted(run.rglob('*'))
                               if path.is_file() and 'native-run' not in path.parts],
             'external_timeline_inputs': [
                 {key: utterance[key] for key in ['audio', 'tts_raw', 'tts_trimmed']}
                 for chapter in producer.read(run / 'timeline.json')['chapters']
                 for utterance in chapter['utterances']]}
    producer.write(run / 'retained-process-index.json', index)
    preserve(run / 'retained-process-index.json', f'{prefix}-process-index', 'process-index')
    append_phase_record(manifest, phase_id='project-palette-composition', status='succeeded',
                        artifact_ids=[f'{prefix}-deliverable'],
                        detail=args.phase_detail)
    append_automated_audit_record(manifest, check_id='media-and-series-palette', status='passed',
                                  subject_artifact_id=f'{prefix}-deliverable', report_artifact_id=f'{prefix}-machine-report')
    append_phase_record(manifest, phase_id='limited-actual-frame-review', status='succeeded',
                        artifact_ids=[f'{prefix}-deliverable', f'{prefix}-frame-review'],
                        detail='Actual packaging frames and corrected score crops inspected; this does not constitute full 1x review, listening, clean-span certification or signoff.')
    loaded = load_document(manifest, check_files=True)
    report = {'at_utc': producer.stamp(), 'manifest': producer.ref(manifest),
              'artifacts': records, 'human_signoffs': len(loaded.run.signoffs),
              'scope': 'Declared media, palette and local-frame conditions only'}
    producer.write(run / 'native-preservation-complete.json', report)
    print(producer.ref(run / 'native-preservation-complete.json'))


if __name__ == '__main__':
    main()
