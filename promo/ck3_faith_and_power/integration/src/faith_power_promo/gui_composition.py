"""Original GUI layers inside the existing cue prepare/ASS/map chain.

No new image/video files, providers, renderer, timeline or media qualification.
Metadata plans stat binaries; normal prepare also checks actual still headers.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math

from PIL import Image, ImageFont
from xar_promo.layout import FontSpec, WrapPolicy, wrap_text
from xar_promo.subtitles import AssCue, AssStyleConfig, SubtitleTrackConfig

KIND = 'gui-composition'
DISCLOSURE = '组合画面｜原版界面＋讲解'
ZONE = [64, 96, 2432, 1024]
SLOTS = {
    'A': {'primary_GUI': [64, 96, 2432, 1024],
          'detail_inset': [960, 120, 1480, 984]},
    'B': {'left_GUI': [64, 120, 1184, 840], 'right_GUI': [1312, 120, 1184, 840]},
    'C': {'GUI_anchor': [64, 120, 1080, 984], 'logic_inset': [1192, 120, 1304, 984]},
}
REQUIRED = {'A': ['primary_GUI'], 'B': ['left_GUI', 'right_GUI'], 'C': ['GUI_anchor']}


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _rect(value):
    if (not isinstance(value, list) or len(value) != 4
        or any(type(v) is not int for v in value)
        or value[0] < 0 or value[1] < 0 or min(value[2:]) <= 0):
        raise ValueError('GUI rectangles require finite integer xywh, positive size and nonnegative origin')
    return value


def _within(inner, outer):
    x, y, w, h = _rect(inner)
    a, b, width, height = _rect(outer)
    return a <= x and b <= y and x + w <= a + width and y + h <= b + height


def _interval(value, duration):
    if (not isinstance(value, list) or len(value) != 2
        or not all(_number(v) and abs(v * 30 - round(v * 30)) < 1e-4 for v in value)
        or not 0 <= value[0] < value[1] <= duration + 1e-7):
        raise ValueError('Layer/annotation interval must be positive, 30fps aligned and within its composition')
    return value


def _text(value, maximum=96):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\r' in value:
        raise ValueError('Composition text needs a short nonempty player-facing annotation')
    return value


def display_title(part):
    """A scene may name its topic while metadata keeps its derived identity."""
    return _text(part.get('topic_title', DISCLOSURE), 80)


def _pin(value):
    if (not isinstance(value, dict) or set(value) != {'path', 'bytes', 'sha256'}
        or not isinstance(value['path'], str) or not value['path']
        or type(value['bytes']) is not int or value['bytes'] <= 0
        or not isinstance(value['sha256'], str) or len(value['sha256']) != 64
        or any(v not in '0123456789abcdefABCDEF' for v in value['sha256'])):
        raise ValueError('Each actual composition source needs an exact path/bytes/SHA256 pin')
    return value


def _json(reference, bound, *, allow_stdout=False):
    _pin(reference)
    allowed = ('.json', '.stdout') if allow_stdout else ('.json',)
    if not reference['path'].lower().endswith(allowed):
        raise ValueError('Pinned JSON required; only source-frame PTS also accepts .stdout')
    return json.loads(bound(reference).read_text(encoding='utf-8-sig'))


def _pointer(value, pointer):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith('/')):
        raise ValueError('Explicit evidence JSON pointer required')
    for key in pointer.split('/')[1:]:
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def _cover(intervals, duration):
    cursor = 0.
    for start, end in sorted(intervals):
        if start > cursor + 1e-7:
            return False
        cursor = max(cursor, end)
    return cursor >= duration - 1e-7


def _source_ref(reference, bound):
    file = reference['file']
    _pin(file)
    if file['path'].lower().endswith('.json'):
        _pointer(_json(file, bound), reference['json_pointer'])
    else:
        rows = bound(file).read_text(encoding='utf-8-sig').splitlines()
        first, last = reference.get('first_line'), reference.get('last_line')
        if type(first) is not int or type(last) is not int or not 1 <= first <= last <= len(rows):
            raise ValueError('Mechanism annotation needs a real pinned source line span')


def inspect(part, bound, machine_id, *, metadata_only=False):
    """Validate authored layout and actual lineage. Null assets remain gaps."""
    if (part.get('kind') != KIND or part.get('template') not in SLOTS
        or part.get('machine_id') != machine_id or part.get('disclosure') != DISCLOSURE
        or not part.get('scene_id') or part.get('burned_in_disclosure') is not None):
        raise ValueError('Declare an exact same-machine derived GUI composition and persistent ASS disclosure')
    topic_title = display_title(part)
    duration = part.get('duration_seconds')
    if not _number(duration) or duration <= 0 or abs(duration * 30 - round(duration * 30)) > 1e-4:
        raise ValueError('Composition uses the existing positive 30fps cue clock')
    layers, notes = part.get('layers'), part.get('annotations', [])
    if not isinstance(layers, list) or not isinstance(notes, list) or len(layers) > 6 or len(notes) > 12:
        raise ValueError('One composition supports at most6 actual GUI layers and12 short annotations')
    gaps, checked, covered = [], [], {}
    ids = set()
    for layer in layers:
        if not isinstance(layer, dict) or not layer.get('id') or layer['id'] in ids:
            raise ValueError('Actual GUI layers need distinct stable IDs')
        ids.add(layer['id'])
        role = layer.get('role')
        if role not in SLOTS[part['template']]:
            raise ValueError('GUI layer does not belong to the selected A/B/C layout')
        display = _interval(layer.get('display_interval_seconds'), duration)
        destination = _rect(layer.get('canvas_rect'))
        expected = SLOTS[part['template']][role]
        if not _within(destination, expected):
            raise ValueError('GUI layer differs from its selected template slot')
        _text(layer.get('display_label'), 64)
        _text(layer.get('object_context'), 160)
        _text(layer.get('object_name'), 80)
        if not isinstance(layer.get('required_context'), list) or not layer['required_context']:
            raise ValueError('Actual GUI ROI must declare the object name and necessary visible context')
        for field in layer['required_context']:
            _text(field, 80)
        kind = layer.get('kind')
        if kind not in {'raw', 'game-still'}:
            raise ValueError('Original GUI slots accept only original gameplay pixels, never diagram/native JSON cards')
        reference = layer.get('raw' if kind == 'raw' else 'image')
        if reference is None:
            gaps.append(part['scene_id'] + '/' + layer['id'] + ': original GUI asset unbound')
            continue
        crop = _rect(layer.get('crop_rect'))
        _pin(reference)
        path = bound(reference)  # MetadataBindings stats this binary, never hashes/opens it.
        record = {key: deepcopy(layer[key]) for key in ('id', 'role', 'kind',
                  'display_interval_seconds', 'canvas_rect', 'crop_rect', 'display_label', 'object_context',
                  'object_name', 'required_context')}
        record['file'] = reference
        record['source_geometry_checked_from_binary'] = False
        record['coverage_credit'] = 'embedded-original-GUI-layer; never full-frame raw'
        if kind == 'raw':
            audit = _json(layer['raw_audit'], bound)
            if (audit.get('machine_id') != machine_id or audit.get('raw') != reference
                or audit.get('full_decode_exit_code') != 0):
                raise ValueError('Embedded raw needs the same existing exact-machine full-decode audit')
            if audit.get('capture_was_aborted') and layer.get('original_RED_disclosed') is not True:
                raise ValueError('Interrupted original source retains its RED qualification boundary')
            index = _json(layer['source_index'], bound)
            geometry_ref = layer['geometry_evidence']
            if geometry_ref.get('file') not in [layer['raw_audit'], layer['source_index']]:
                raise ValueError('Raw geometry must come from this exact qualified audit or source index')
            geometry = _pointer(audit if geometry_ref['file'] == layer['raw_audit'] else index,
                                geometry_ref['json_pointer'])
            if not isinstance(geometry, dict):
                raise ValueError('Actual raw geometry pointer must select width/height metadata')
            width, height = geometry.get('width'), geometry.get('height')
            frames = _json(layer['source_frame_pts'], bound, allow_stdout=True)['frames']
            start = layer.get('raw_start_seconds')
            if not _number(start) or start < 0:
                raise ValueError('Embedded clip requires its actual nonnegative source PTS')
            end = start + display[1] - display[0]
            if end > audit['pts']['last_pts'] + 1 / 30 + 1e-6:
                raise ValueError('Embedded raw exceeds the same qualified decoded source')
            chosen = [(i, float(f['best_effort_timestamp_time'])) for i, f in enumerate(frames)
                      if start <= float(f['best_effort_timestamp_time']) < end]
            if not chosen:
                raise ValueError('Embedded raw selection contains no actually indexed source frame')
            record.update(raw_audit=layer['raw_audit'], source_index=layer['source_index'],
                          source_frame_pts=layer['source_frame_pts'], source_interval_seconds=[start, end],
                          selected_source_frame_indices_exclusive=[chosen[0][0], chosen[-1][0] + 1],
                          actual_selected_source_first_pts=chosen[0][1], actual_selected_source_last_pts=chosen[-1][1],
                          source_timing='Actual VFR; 30fps display conversion is not extra game time')
        else:
            receipt = _json(layer['still_receipt'], bound)
            if (receipt.get('schema') != 'ck3-faith-power-original-gui-still-v1'
                or receipt.get('machine_id') != machine_id or receipt.get('image') != reference):
                raise ValueError('Original GUI still needs its exact capture/extraction identity receipt')
            identity = receipt.get('source_identity', {})
            if (identity.get('kind') not in {'gameplay-screenshot', 'gameplay-frame-extract'}
                or not identity.get('id') or not identity.get('observed_at_utc')
                or not identity.get('context') or not receipt.get('capture_checks')):
                raise ValueError('Still cannot acquire original GUI identity from a native readback or drawn card')
            for check in receipt['capture_checks']:
                capture = _json(check['file'], bound)
                if (capture.get('machine_id') != machine_id or 'equals' not in check
                    or _pointer(capture, check['json_pointer']) != check['equals']):
                    raise ValueError('Original still capture provenance differs from its source')
            if not any(check['equals'] == reference for check in receipt['capture_checks']):
                raise ValueError('Original capture/extraction receipt must bind this exact still image pin')
            geometry = receipt.get('source_geometry')
            if not isinstance(geometry, list) or len(geometry) != 2:
                raise ValueError('Original still needs actual capture geometry metadata')
            width, height = geometry
            if not metadata_only:
                with Image.open(path) as image:
                    if image.format not in {'PNG', 'JPEG'} or list(image.size) != geometry:
                        raise ValueError('Original still differs from its real image header')
                record['source_geometry_checked_from_binary'] = True
            record.update(still_receipt=layer['still_receipt'], source_identity=identity,
                          verification='binary stat only; geometry header deferred' if metadata_only else 'actual still header; source receipt chain')
        if type(width) is not int or type(height) is not int or min(width, height) <= 0:
            raise ValueError('Qualified source geometry must be positive integer width/height')
        if not _within(crop, [0, 0, width, height]):
            raise ValueError('GUI crop is outside its actual qualified source geometry')
        record['source_geometry'] = [width, height]
        checked.append(record)
        covered.setdefault(role, []).append(display)
    for role in REQUIRED[part['template']]:
        if not _cover(covered.get(role, []), duration):
            gaps.append(part['scene_id'] + '/' + role + ': actual GUI must remain visible throughout the composition')
    for note in notes:
        if not isinstance(note, dict) or not note.get('id') or note['id'] in ids:
            raise ValueError('Composition annotations need distinct stable IDs')
        ids.add(note['id'])
        _interval(note.get('display_interval_seconds'), duration)
        _text(note.get('text'))
        rect = _rect(note.get('canvas_rect'))
        allowed = ([64, 980, 2432, 140] if part['template'] == 'B' else
                   [1192, 120, 1304, 984] if part['template'] == 'C' else ZONE)
        if not _within(rect, allowed) or rect[3] < 48:
            raise ValueError('Annotation must stay in its template area above narration subtitles')
        if not note.get('claim_ids') or not note.get('source_refs'):
            raise ValueError('Short mechanism annotation retains explicit claim/source provenance')
        for source in note['source_refs']:
            _source_ref(source, bound)
    return {'scene_id': part['scene_id'], 'template': part['template'],
            'duration_seconds': duration, 'outer_source_class': 'derived-composition',
            'display_topic_title': topic_title,
            'layers': checked, 'annotations': deepcopy(notes), 'gaps': gaps,
            'content_ready': not gaps, 'pixel_legibility_review_pending': True,
            'metadata_only': metadata_only, 'full_frame_raw_seconds': 0,
            'still_or_native_readback_is_not_live_action': True}


def filters(part, bound, first_input, output_label):
    """Return existing prepare argv/filter fragments, never execute or emit media."""
    checked = inspect(part, bound, part['machine_id'])
    if checked['gaps']:
        raise ValueError('Composition not ready: ' + '; '.join(checked['gaps']))
    duration = part['duration_seconds']
    argv, result = [], [f'color=c=0x211813:s=2560x1440:r=30:d={duration:.9f}[{output_label}base]']
    previous = output_label + 'base'
    for offset, layer in enumerate(part['layers']):
        start, end = layer['display_interval_seconds']
        seconds = end - start
        if layer['kind'] == 'raw':
            argv += ['-ss', f"{layer['raw_start_seconds']:.9f}", '-t', f'{seconds:.9f}', '-i', str(bound(layer['raw']))]
        else:
            argv += ['-loop', '1', '-framerate', '30', '-t', f'{seconds:.9f}', '-i', str(bound(layer['image']))]
        x, y, width, height = layer['canvas_rect']
        a, b, crop_width, crop_height = layer['crop_rect']
        label, combined = output_label + 'layer' + str(offset), output_label + 'mix' + str(offset)
        result.append(f'[{first_input+offset}:v]setpts=PTS-STARTPTS,crop={crop_width}:{crop_height}:{a}:{b},'
                      f'scale={width}:{height}:force_original_aspect_ratio=decrease:flags=lanczos,'
                      f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x211813,setsar=1,'
                      f'fps=30:round=near,trim=duration={seconds:.9f},setpts=PTS-STARTPTS+{start:.9f}/TB[{label}]')
        result.append(f'[{previous}][{label}]overlay=x={x}:y={y}:eof_action=pass:repeatlast=0:'
                      f"enable='gte(t,{start:.9f})*lt(t,{end:.9f})'[{combined}]")
        previous = combined
    result.append(f'[{previous}]trim=duration={duration:.9f},setpts=PTS-STARTPTS,format=yuv420p[{output_label}]')
    return argv, result, first_input + len(part['layers'])


def ass(part, cursor, font_path, font_name, tracks, cues, *, prefix):
    """Position short plain-text notes using existing ASS styles, not PNG cards."""
    notes = deepcopy(part.get('annotations', []))
    for layer in part['layers']:
        x, y, width, height = layer['canvas_rect']
        notes.append({'text': layer['display_label'], 'display_interval_seconds': layer['display_interval_seconds'],
                      'canvas_rect': [x + 12, y + 12, width - 24, 88], 'label': True})
    for index, note in enumerate(notes):
        track = prefix + '.note' + str(index)
        x, y, width, height = note['canvas_rect']
        size = 26 if note.get('label') else 36
        face = ImageFont.truetype(str(font_path), size)
        layout = wrap_text(note['text'], font=FontSpec(track, font_name, size),
                           measure=lambda text, chosen: face.getlength(text),
                           max_width=width, max_lines=2, policy=WrapPolicy())
        if len(layout.lines) * (size + 10) > height:
            raise ValueError('Short composition note exceeds its actual measured ASS safety rectangle')
        style = AssStyleConfig(track, font_name, size, primary_colour='&H00CFE5F0',
                               outline_colour='&H00131821', back_colour='&H40131821',
                               border_style=3, outline=2, shadow=0, alignment=7,
                               margin_left=x, margin_right=2560 - x - width, margin_vertical=y)
        tracks.append(SubtitleTrackConfig(track, 'zh-CN', 4, style))
        start, end = note['display_interval_seconds']
        cues.append(AssCue(track, track, cursor + start, cursor + end, '\n'.join(layout.lines)))


def slice_scene(scene, first_seconds, last_seconds):
    """Reuse one long GUI scene across measured cues; never create per-cue PNGs."""
    _interval([first_seconds, last_seconds], scene['duration_seconds'])
    part = deepcopy(scene)
    part['duration_seconds'] = last_seconds - first_seconds
    for field in ('layers', 'annotations'):
        part[field] = []
        for original in scene.get(field, []):
            low, high = original['display_interval_seconds']
            start, end = max(low, first_seconds), min(high, last_seconds)
            if start >= end:
                continue
            item = deepcopy(original)
            item['display_interval_seconds'] = [start - first_seconds, end - first_seconds]
            if field == 'layers' and item['kind'] == 'raw':
                item['raw_start_seconds'] += start - low
            part[field].append(item)
    return part


def coverage(rows):
    """Separate outer derived duration from embedded layer identity/spatial/time data."""
    records, uses, last_identity = [], [], {}
    global_cursor = 0.
    for row in rows:
        part_cursor = global_cursor
        for part in row.get('visual_parts') or []:
            duration = part['duration_seconds']
            if part['kind'] == 'raw':
                uses.append((part['raw']['sha256'], part['raw_start_seconds'],
                             part['raw_start_seconds'] + duration, part_cursor - part['raw_start_seconds']))
            if part['kind'] == KIND:
                layers = []
                for layer in part['layers']:
                    low, high = layer['display_interval_seconds']
                    first, last = part_cursor + low, part_cursor + high
                    reference = layer.get('raw' if layer['kind'] == 'raw' else 'image')
                    identity = (reference, layer['crop_rect'], layer['canvas_rect'], layer['role'])
                    key = part['scene_id'], layer['id']
                    previous = last_identity.get(key)
                    if previous and abs(previous[0] - first) < 1e-6:
                        if previous[1] != identity:
                            raise ValueError('A continuing GUI layer changed its source/crop/slot without a new layer ID')
                        if layer['kind'] == 'raw' and abs(previous[2] - layer['raw_start_seconds']) > 1e-6:
                            raise ValueError('A continuing raw GUI layer must follow source PTS without replay or jumps')
                    last_identity[key] = (last, identity, layer['raw_start_seconds'] + high - low if layer['kind'] == 'raw' else None)
                    value = deepcopy(layer)
                    value['authored_final_interval_seconds'] = [first, last]
                    value['coverage_credit'] = 'embedded layer only, not full-frame raw'
                    if layer['kind'] == 'raw' and reference is not None:
                        start = layer['raw_start_seconds']
                        uses.append((reference['sha256'], start, start + high - low, first - start))
                    layers.append(value)
                records.append({'cue_id': row['id'], 'scene_id': part['scene_id'], 'template': part['template'],
                                'outer_source_class': 'derived-composition',
                                'display_topic_title': display_title(part),
                                'authored_final_interval_seconds': [part_cursor, part_cursor + duration],
                                'embedded_layers': layers, 'annotations': deepcopy(part.get('annotations', []))})
            part_cursor += duration
        global_cursor += row['duration_seconds']
    for i, left in enumerate(uses):
        for right in uses[i + 1:]:
            if (left[0] == right[0] and min(left[2], right[2]) > max(left[1], right[1]) + 1e-7
                and abs(left[3] - right[3]) > 1e-6):
                raise ValueError('Raw source would repeat in a different final time; simultaneous inset projection alone is allowed')
    totals = {kind: sum(layer['display_interval_seconds'][1] - layer['display_interval_seconds'][0]
                       for entry in records for layer in entry['embedded_layers'] if layer['kind'] == kind)
              for kind in ['raw', 'game-still']}

    def union_seconds(intervals):
        total, previous = 0., None
        for start, end in sorted(intervals):
            if previous is None or start > previous:
                total += end - start
            elif end > previous:
                total += end - previous
            previous = max(end, previous if previous is not None else end)
        return total

    raw_layers = [layer for entry in records for layer in entry['embedded_layers']
                  if layer['kind'] == 'raw' and layer.get('raw') is not None]
    source_spans = {}
    for layer in raw_layers:
        start = layer['raw_start_seconds']
        low, high = layer['display_interval_seconds']
        source_spans.setdefault(layer['raw']['sha256'], []).append((start, start + high - low))
    return {'derived_composition_seconds': sum(r['authored_final_interval_seconds'][1] - r['authored_final_interval_seconds'][0] for r in records),
            'full_frame_raw_seconds_from_compositions': 0,
            'embedded_raw_layer_display_seconds': totals['raw'],
            'embedded_still_layer_display_seconds': totals['game-still'],
            'embedded_raw_visible_final_time_union_seconds': union_seconds([layer['authored_final_interval_seconds'] for layer in raw_layers]),
            'embedded_raw_unique_source_PTS_seconds': sum(union_seconds(spans) for spans in source_spans.values()),
            'measures_authored_layer_intervals_not_actual_pixel_coverage': True,
            'layer_seconds_sum_multiple_simultaneous_layers_not_final_raw_coverage': True,
            'still_display_seconds_are_not_new_game_time': True,
            'embedded_layers_are_not_full_frame_raw': True, 'entries': records,
            'pixel_legibility_or_semantic_result_verified': False}


def actual_map_layers(part, actual_part_first_pts, actual_part_first_frame):
    """Called only after final PTS validation; this maps, not requalifies, sources."""
    values = []
    checked = {layer['id']: layer for layer in part.get('composition_source_check', {}).get('layers', [])}
    for layer in part['layers']:
        value = deepcopy(layer)
        value.update(deepcopy(checked.get(layer['id'], {})))
        low, high = layer['display_interval_seconds']
        value['actual_final_first_pts'] = actual_part_first_pts + low
        value['actual_final_end_pts_exclusive'] = actual_part_first_pts + high
        value['actual_final_frame_indices_exclusive'] = [actual_part_first_frame + round(low * 30),
                                                        actual_part_first_frame + round(high * 30)]
        value['outer_source_class'] = 'derived-composition'
        value['coverage_credit'] = 'embedded-original-GUI-layer; never full-frame raw'
        values.append(value)
    return values
