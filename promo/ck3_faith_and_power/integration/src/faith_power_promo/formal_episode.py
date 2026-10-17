"""Formal episode assembly from selected measured voices and explicit source cuts.

The 158-cue research inventory is a source, not a required formal cut. This
adapter keeps the existing bounded renderer, without impersonating its old
input schema or inherited research visuals. No TTS, screen, or game access.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

SCHEMA = 'ck3-faith-power-formal-edit-v1'


def pointer(value, path):
    for component in path.split('/')[1:]:
        component = component.replace('~1', '/').replace('~0', '~')
        value = value[int(component)] if isinstance(value, list) else value[component]
    return value


def apply_delta(base, operations):
    result = deepcopy(base)
    for operation in operations:
        path, kind = operation['path'], operation['op']
        if kind == 'test':
            if pointer(result, path) != operation['value']:
                raise ValueError('Formal source delta test differs: ' + path)
            continue
        parent_path, leaf = path.rsplit('/', 1)
        parent = pointer(result, parent_path)
        key = int(leaf) if isinstance(parent, list) and leaf != '-' else leaf.replace('~1', '/').replace('~0', '~')
        if kind == 'remove':
            del parent[key]
        elif kind in {'add', 'replace'}:
            if kind == 'replace':
                parent[key]
            value = deepcopy(operation['value'])
            if isinstance(parent, list) and kind == 'add':
                parent.append(value) if leaf == '-' else parent.insert(key, value)
            else:
                parent[key] = value
        else:
            raise ValueError('Unsupported formal source delta operation')
    return result


class FormalInputs:
    def __init__(self, document, common):
        self.document = document
        self.common = common
        self.bindings = common.Inputs({})
        self.bound = self.bindings.bound

    def load(self, declared):
        return self.common.read(self.bound(declared))

    def inspect(self):
        common, doc = self.common, self.document
        if doc.get('schema') != SCHEMA or not doc.get('machine_id'):
            raise ValueError('Explicit formal schema and machine required')
        if doc.get('scope') not in {'episode01-formal-review', 'episode01-P-relic-review-scene'}:
            raise ValueError('Declare formal episode or independent P/relic scene')
        delta = self.load(doc['existing_voice_delta'])
        base = self.load(delta['base_input'])
        projected = apply_delta(base, delta['json_patch_suggestions'])
        old = {row['id']: row for row in projected['retained_cues']}
        new = {}
        claims, checks = {}, {}
        batches = doc['new_voice_batches']
        if not batches:
            raise ValueError('At least one measured new voice batch required')
        for batch in batches:
            frozen_new = self.load(batch['text_freeze'])
            measured_new = self.load(batch['measured_voices'])
            result_evidence = self.load(batch['result_evidence'])
            for item in (frozen_new, measured_new, result_evidence):
                if item['machine_id'] != doc['machine_id']:
                    raise ValueError('Measured voice/result catalog crossed machine')
            if measured_new['text_freeze'] != batch['text_freeze'] or measured_new['failures']:
                raise ValueError('New voices need exact independent text freeze and no failed requests')
            new_text = {row['id']: row for row in frozen_new['cues']}
            new_audio = {row['id']: row for row in measured_new['cues']}
            if set(old) & set(new_text) or set(new) & set(new_text) or set(new_text) != set(new_audio):
                raise ValueError('Old/new voice inventory overlap or mismatch')
            new.update({key: {**text, **new_audio[key]} for key, text in new_text.items()})
            for check in result_evidence['native_checks']:
                if check['id'] in checks and checks[check['id']] != check:
                    raise ValueError('Different observations share a check identifier')
                checks[check['id']] = check
            for claim in result_evidence['claims']:
                if claim['id'] in claims and claims[claim['id']] != claim:
                    raise ValueError('Different claims share an identifier')
                claims[claim['id']] = claim
        inventory = {**old, **new}
        selected = [row['id'] for row in doc['cues']]
        if len(set(selected)) != len(selected) or not set(selected) <= set(inventory):
            raise ValueError('Duplicate or unknown selected voice')
        if doc['scope'] == 'episode01-formal-review':
            excluded = doc['excluded_cues']
            excluded_ids = {row['id'] for row in excluded if row.get('reason')}
            if len(excluded_ids) != len(excluded) or set(selected) & excluded_ids or set(selected) | excluded_ids != set(inventory):
                raise ValueError('Formal inventory needs explicit reasoned exclusions')
        by_id = {row['id']: row for row in doc['cues']}
        order = doc['sequence']
        if len(order) != len(set(order)) or set(order) != set(by_id):
            raise ValueError('Sequence must contain every selected voice once')
        rows = [by_id[key] for key in order]
        gaps, intervals, raw_seconds, graphic_seconds = [], {}, 0.0, 0.0
        max_graphic_run = graphic_run = 0.0
        motion_seconds = explanation_run = max_explanation_run = 0.0
        motion_intervals = {}
        for check in checks.values():
            if pointer(self.load(check['file']), check['json_pointer']) != check['equals']:
                raise ValueError('Actual native observation differs: ' + check['id'])
        for row in rows:
            source = inventory[row['id']]
            for key in ('zh', 'en', 'claim_ids', 'shot_ids', 'audio', 'provider_request', 'speech_duration_seconds', 'duration_seconds'):
                if row[key] != source[key]:
                    raise ValueError('Selected measured source field changed: ' + row['id'] + '/' + key)
            self.bound(row['audio'])
            request = self.load(row['provider_request'])
            if request['request']['text'] != row['zh']:
                raise ValueError('Audio request text differs')
            if abs(common.cue_duration(row['speech_duration_seconds']) - row['duration_seconds']) > 1e-6:
                raise ValueError('Measured voice clock differs')
            if not 0 <= float(row.get('subtitle_start_seconds', 0)) < row['speech_duration_seconds']:
                raise ValueError('Subtitle onset must precede the unchanged measured speech end')
            if row['id'] in new:
                for key in row['claim_ids']:
                    if key not in claims:
                        raise ValueError('New result sentence lacks its explicit source claim')
                    if any(check_id not in checks for check_id in claims[key]['native_check_ids']):
                        raise ValueError('Result claim references an absent observation')
            parts = row.get('visual_parts')
            if parts is None:
                gaps.append(row['id'] + ': formal visual parts unbound')
                graphic_run = 0
                continue
            if not parts or abs(sum(part['duration_seconds'] for part in parts) - row['duration_seconds']) > 1e-6:
                raise ValueError('Visual parts must cover the exact measured cue')
            for part in parts:
                duration = part['duration_seconds']
                if duration <= 0 or abs(duration * 30 - round(duration * 30)) > 1e-4 or not part.get('disclosure'):
                    raise ValueError('Visual needs positive frame-aligned duration and source disclosure')
                kind = part['kind']
                if kind in {'diagram', 'native-readback'}:
                    if duration > 6.4:
                        raise ValueError('One source graphic focus exceeds existing renderer limit')
                    self.bound(part['image'])
                    graphic_seconds += duration
                    explanation_run += duration
                    max_explanation_run = max(max_explanation_run, explanation_run)
                    graphic_run += duration
                    max_graphic_run = max(max_graphic_run, graphic_run)
                    if kind == 'diagram':
                        if part.get('live_result_depicted') is not False:
                            raise ValueError('Mechanism graphic cannot assert a live observation')
                    else:
                        receipt = self.load(part['native_card_receipt'])
                        if receipt.get('schema') != 'ck3-faith-power-native-readback-card-v1' or receipt['machine_id'] != doc['machine_id'] or receipt['image'] != part['image']:
                            raise ValueError('Native graphic receipt binding differs')
                        for field in receipt['rows']:
                            if pointer(self.load(field['file']), field['json_pointer']) != field['observed_value']:
                                raise ValueError('Native graphic field differs from original')
                elif kind == 'mechanism-motion':
                    self.bound(part['video'])
                    receipt = self.load(part['source_motion_receipt'])
                    if (receipt.get('schema') != 'ck3-faith-power-source-motion-v1'
                        or receipt['machine_id'] != doc['machine_id'] or receipt['video'] != part['video']
                        or receipt.get('live_result_depicted') is not False or part.get('live_result_depicted') is not False
                        or receipt['full_decode_exit_code'] != 0 or receipt['frames']['cfr_fps'] != 30
                        or receipt['frames']['count'] != round(receipt['frames']['duration_seconds'] * 30)):
                        raise ValueError('Mechanism motion needs exact same-machine source-only decode/PTS receipt')
                    for key in ('producer', 'spec', 'source_catalog', 'toolchain_qualification'):
                        self.bound(receipt[key])
                    source_catalog = self.load(receipt['source_catalog'])
                    if source_catalog.get('machine_id') != doc['machine_id']:
                        raise ValueError('Source-motion catalog crossed machine')
                    for item in source_catalog['sources']:
                        path = self.bound(item['file'])
                        lines = path.read_text(encoding='utf-8-sig').splitlines()
                        first, last = item['first_line'], item['last_line']
                        text = '\n'.join(lines[first - 1:last]) + '\n'
                        if (not 1 <= first <= last <= len(lines) or text != item['excerpt']
                            or hashlib.sha256(text.encode()).hexdigest() != item['excerpt_sha256']):
                            raise ValueError('Actual source-motion source excerpt differs')
                    if not receipt['steps'] or not set(part['claim_ids']) <= set(row['claim_ids']):
                        raise ValueError('Source motion lacks explicit matching cue claims')
                    if not set(part['claim_ids']) <= set(receipt['claim_ids']):
                        raise ValueError('Motion receipt claims differ from selected part')
                    start = part['source_start_seconds']
                    end = start + duration
                    if start < 0 or end > receipt['frames']['duration_seconds'] + 1e-6:
                        raise ValueError('Motion selection exceeds actual decoded source')
                    motion_intervals.setdefault(part['video']['sha256'], []).append((start, end, row['id']))
                    motion_seconds += duration
                    graphic_run = 0
                    explanation_run += duration
                    max_explanation_run = max(max_explanation_run, explanation_run)
                elif kind == 'raw':
                    self.bound(part['raw'])
                    audit = self.load(part['raw_audit'])
                    if audit['machine_id'] != doc['machine_id'] or audit['raw'] != part['raw'] or audit['full_decode_exit_code'] != 0:
                        raise ValueError('Raw needs same-machine full decode evidence')
                    start, end = part['raw_start_seconds'], part['raw_start_seconds'] + duration
                    if start < 0 or end > audit['pts']['last_pts'] + 1/30 + 1e-6:
                        raise ValueError('Raw selection exceeds actually decoded source')
                    if audit['capture_was_aborted'] and part.get('original_RED_disclosed') is not True:
                        raise ValueError('Interrupted source needs explicit RED disclosure')
                    self.bound(part['source_index'])
                    frames = self.load(part['source_frame_pts'])['frames']
                    chosen = [(index, float(frame['best_effort_timestamp_time'])) for index, frame in enumerate(frames) if start <= float(frame['best_effort_timestamp_time']) < end]
                    if not chosen:
                        raise ValueError('Raw cut contains no actual source frames')
                    part.update(selected_source_frame_indices_exclusive=[chosen[0][0], chosen[-1][0] + 1],
                        actual_selected_source_first_pts=chosen[0][1], actual_selected_source_last_pts=chosen[-1][1],
                        actual_selected_source_frame_count=len(chosen),
                        source_timing='Actual VFR source; nearest-frame 30fps delivery conversion is not extra game time')
                    intervals.setdefault(part['raw']['sha256'], []).append((start, end, row['id']))
                    raw_seconds += duration
                    graphic_run = 0
                    explanation_run = 0
                else:
                    raise ValueError('Unsupported visual source kind')
        for spans in list(intervals.values()) + list(motion_intervals.values()):
            spans.sort()
            if any(right[0] < left[1] - 1e-7 for left, right in zip(spans, spans[1:])):
                raise ValueError('Actual raw intervals repeat or overlap')
        total = sum(row['duration_seconds'] for row in rows)
        states = doc['pending_result_slots']
        warnings = []
        for key, value in states.items():
            if value is None:
                if doc['scope'] == 'episode01-formal-review':
                    gaps.append(key + ': result still unbound')
            elif value.get('status') == 'omitted':
                if not value.get('reason'):
                    raise ValueError('An omitted result needs its explicit reason')
            elif value.get('status') == 'observed-bound':
                if not value.get('cue_ids') or not set(value['cue_ids']) <= set(selected):
                    raise ValueError('An observed result must bind actual selected measured cues')
            else:
                raise ValueError('Result slot needs observed-bound or explicit omitted status')
        if doc['scope'] == 'episode01-formal-review' and not 1200 <= total <= 2400:
            warnings.append('Outside director 20–40 minute preference; an honest shorter review may build. No padding or raw loops.')
        self.load(doc['assembly_plan'])  # Only supplies the real ProjectConfig source, never a synthetic cue inventory.
        return {'rows': rows, 'seconds': total, 'gaps': gaps, 'ready_to_build': not gaps,
            'budget': common.peak_budget(total, len(rows)), 'scope': doc['scope'], 'editorial_warnings': warnings,
            'selected_existing_voice_count': sum(row['id'] in old for row in rows),
            'selected_new_voice_count': sum(row['id'] in new for row in rows),
            'bound_raw_seconds': raw_seconds, 'bound_graphic_seconds': graphic_seconds,
            'bound_source_motion_seconds': motion_seconds, 'maximum_contiguous_explanation_seconds': max_explanation_run,
            'maximum_contiguous_graphic_seconds': max_graphic_run,
            'unbound_visual_seconds': sum(row['duration_seconds'] for row in rows if row.get('visual_parts') is None),
            'new_TTS_requested': False, 'human_1x_signoff': False, 'pending_result_slots': states}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('plan', 'build'))
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    for name in ('repo', 'input', 'runtime', 'reservation', 'package-root', 'output', 'v3-helper', 'allocation-reader'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    sys.path.insert(0, str(args.repo / 'promo/ck3_faith_and_power/integration/src'))
    from faith_power_promo import full_episode as common
    document = common.read(args.input)
    machine = subprocess.check_output([sys.executable, '-B', args.repo / 'tools/ck3_live_run_id.py', 'machine'], text=True).strip()
    if machine != document['machine_id']:
        raise ValueError('Formal input belongs to another machine')
    inputs = FormalInputs(document, common)
    inspected = inputs.inspect()
    required_sources = {str(Path(__file__).resolve()), str(args.v3_helper.resolve())}
    snapshots = document['producer_source_snapshots']
    if {str(Path(item['file']['path']).resolve()) for item in snapshots} != required_sources:
        raise ValueError('Preserved input must embed both actual adapter and v3 helper source')
    for item in snapshots:
        path = inputs.bound(item['file'])
        if path.read_bytes() != item['utf8'].encode('utf-8'):
            raise ValueError('Embedded producer source bytes differ')
    spec = importlib.util.spec_from_file_location('explicit_faith_v3_admission', args.v3_helper)
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)
    admission = storage.admit_v3(args.repo, args.reservation, args.package_root, args.output, machine,
        inspected['budget']['peak_new_bytes'], args.allocation_reader)
    if args.operation == 'plan':
        args.output.mkdir(parents=True, exist_ok=False)
        report = {key: value for key, value in inspected.items() if key != 'rows'}
        report.update(machine_id=machine, observed_at_utc=datetime.now(timezone.utc).isoformat(),
            evidence_source='Actual formal selected source/audio/native/visual checks; no inherited research visuals',
            input=common.pin(args.input), source=common.pin(__file__), common_renderer=common.pin(common.__file__),
            v3_helper=common.pin(args.v3_helper), storage_admission=admission, media_written=False)
        target = common.write(args.output / 'formal-build-plan.json', report)
        print(json.dumps({'plan': common.pin(target), 'ready_to_build': inspected['ready_to_build'],
            'seconds': inspected['seconds'], 'gaps': inspected['gaps']}, ensure_ascii=False))
        return 0
    result = common.build(args, document, inspected, inputs, admission)
    from xar_promo.project import load_document
    run = Path(result['run']['path'])
    # The exact small source snapshots are already inside preserved full-edit-input.
    # Avoid mutating the manifest after the common renderer records its final pin.
    load_document(run, check_files=True)
    common.write(args.output / 'formal-native-run-final-snapshot.json', {'machine_id': machine,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'manifest': common.pin(run), 'human_signoff': 'pending'})
    result['run'] = common.pin(run)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
