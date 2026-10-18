"""Consume frame-bound semantic storyboards inside the existing graphic prepare.

One terminal reference PNG per cue. The existing prepare command masks future
values before its focus crop; there is no external animation or per-state PNG.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math

from PIL import ImageFont
from .mechanism_motion import Painter, LABEL

SCHEMA = 'faith-power-v5-semantic-storyboard-authoring-v1'
COLUMNS = ['start_frame', 'end_frame', 'panel_index',
    'row_index_or_null_for_role_overview', 'overlapping_authored_subtitle_group_indices']
SOURCE_LABEL = '机制图解'
GEOMETRY = [2560, 1440]


def _integer(value):
    return type(value) is int


def _focus_row_height(cue):
    # Extra bottom margin stays before the next fixed-layout row label.
    height = cue.get('focus_row_height', 100)
    if not _integer(height) or not 100 <= height <= 116:
        raise ValueError('Semantic row focus height must be an integer from 100 to 116')
    return height


def checked_cue(storyboard, cue_id):
    if storyboard.get('schema') != SCHEMA or storyboard.get('focus_state_columns') != COLUMNS:
        raise ValueError('Unknown semantic storyboard/frame column contract')
    layout=storyboard.get('reference_layout_geometry',{})
    expected={'panel_x_origin':100,'panel_x_stride':825,'panel_y':405,'panel_width':710,'panel_height':560,
        'row_focus_bbox_formula':'[x+24,620+103*j,x+686,720+103*j]','caption_y':990,'subtitle_safe_region_begins_y':1140}
    if any(layout.get(key)!=value for key,value in expected.items()):
        raise ValueError('Semantic reference layout differs from the actual Painter geometry')
    matches = [cue for cue in storyboard['cues'] if cue['id'] == cue_id]
    if len(matches) != 1:
        raise ValueError('Semantic cue is missing or duplicated')
    cue = matches[0]
    _focus_row_height(cue)
    if cue.get('source_class') != 'rule' or cue.get('native_fields') is not None:
        raise ValueError('This source-rule consumer cannot award native-readback provenance')
    if len(cue['steps']) != 3 or cue.get('connectors') not in {'none', 'sequence'}:
        raise ValueError('Use the existing three-panel layout and declared relationship')
    frames = round(cue['duration_seconds'] * 30)
    if (not math.isfinite(cue['duration_seconds']) or frames <= 0
        or abs(frames - cue['duration_seconds'] * 30) > 1e-4):
        raise ValueError('Semantic cue clock must be positive and frame aligned')
    cursor = 0
    for state in cue['focus_states']:
        if len(state) != 5:
            raise ValueError('Expected exact frame/panel/row/subtitle overlap state')
        low, high, panel, row, groups = state
        if (not all(_integer(value) for value in (low, high, panel))
            or low != cursor or high <= low or not 0 <= panel < 3
            or high - low > 192 or not isinstance(groups, list)
            or any(not _integer(value) or value < 0 for value in groups)):
            raise ValueError('Semantic states need contiguous positive bounded frame intervals')
        rows = cue['steps'][panel]['panel']['rows']
        if not 1 <= len(rows) <= 3 or (row is not None and (not _integer(row) or not 0 <= row < len(rows))):
            raise ValueError('Semantic state selects an absent panel row')
        cursor = high
    if cursor != frames:
        raise ValueError('Semantic focus states do not cover the measured cue')
    note = cue.get('persistent_condition_note', '')
    if not isinstance(note, str) or '\n' in note or '\r' in note:
        raise ValueError('Persistent condition needs one player-facing line')
    if note and not cue.get('focus_condition_contract'):
        raise ValueError('Persistent condition must have its authored focus contract')
    return cue


def state_layout(cue, index):
    if not _integer(index) or not 0 <= index < len(cue['focus_states']):
        raise ValueError('Unknown semantic state')
    low, high, panel, row, groups = cue['focus_states'][index]
    x = 100 + 825 * panel
    rect = [x, 405, 710, 560] if row is None else [x + 24, 620 + 103 * row, 662, _focus_row_height(cue)]
    hidden = []
    # Role overview shows all row labels but none of their values. Each row
    # state reveals that row and earlier values, never a later value.
    for future in range(0 if row is None else row + 1, len(cue['steps'][panel]['panel']['rows'])):
        hidden.append([x + 28, 670 + 103 * future, 654, 62])
    filters = [f'drawbox=x={a}:y={b}:w={w}:h={h}:color=0x2c2825:t=fill' for a, b, w, h in hidden]
    if row is not None:
        a, b, w, h = rect
        filters.append(f'drawbox=x={a}:y={b}:w={w}:h={h}:color=0xd6a960:t=3')
    note = cue.get('persistent_condition_note', '')
    return {'interval_frames': [low, high], 'panel_index': panel, 'row_index': row,
        'focus_rect': rect, 'hidden_value_rectangles': hidden, 'prepare_prefix': ','.join(filters),
        'disclosure': SOURCE_LABEL + (' · ' + note if note else ''),
        'persistent_condition_note': note,
        'subtitle_overlap_indices': groups, 'terminal_reference_required': True}


def semantic_reveal_plan(part, bound, *, cue_id=None, storyboard_pin=None):
    reference = part.get('semantic_reveal')
    if reference is None:
        return None
    if part.get('kind') != 'diagram' or part.get('live_result_depicted') is not False:
        raise ValueError('Semantic rule reveal is allowed only for disclosed source diagrams')
    if (not isinstance(reference, dict)
        or set(reference) != {'storyboard', 'cue_id', 'state_index', 'interval_frames'}):
        raise ValueError('Bind the exact storyboard, cue, state and selected frame interval')
    if cue_id is not None and reference['cue_id'] != cue_id:
        raise ValueError('Semantic graphic belongs to another measured cue')
    if storyboard_pin is not None and reference['storyboard'] != storyboard_pin:
        raise ValueError('Semantic part differs from the selected graphic storyboard')
    storyboard = json.loads(bound(reference['storyboard']).read_text(encoding='utf-8'))
    cue = checked_cue(storyboard, reference['cue_id'])
    layout = state_layout(cue, reference['state_index'])
    interval = reference['interval_frames']
    if (not isinstance(interval, list) or len(interval) != 2 or not all(_integer(v) for v in interval)
        or not layout['interval_frames'][0] <= interval[0] < interval[1] <= layout['interval_frames'][1]
        or abs(part['duration_seconds'] * 30 - (interval[1] - interval[0])) > 1e-4):
        raise ValueError('Selected reveal interval must stay within its authored state')
    if part.get('focus_rect') != layout['focus_rect'] or part.get('disclosure') != layout['disclosure']:
        raise ValueError('Focus or persistent on-screen condition differs from semantic state')
    if part.get('burned_in_disclosure') is not None:
        raise ValueError('Cropped semantic graphics require their single persistent ASS disclosure')
    return {**layout, 'interval_frames': interval, 'storyboard': reference['storyboard'],
        'cue_id': cue['id'], 'state_index': reference['state_index']}


def semantic_parts(storyboard, storyboard_pin, cue_id, image, *, first_frame=0, last_frame=None):
    """Compile only the requested graphic span; raw cuts can replace other spans."""
    cue = checked_cue(storyboard, cue_id)
    end = round(cue['duration_seconds'] * 30) if last_frame is None else last_frame
    if not _integer(first_frame) or not _integer(end) or not 0 <= first_frame < end <= round(cue['duration_seconds'] * 30):
        raise ValueError('Graphic span must stay within the unchanged measured cue')
    parts = []
    for index, state in enumerate(cue['focus_states']):
        low, high = max(first_frame, state[0]), min(end, state[1])
        if low >= high:
            continue
        layout = state_layout(cue, index)
        parts.append({'kind': 'diagram', 'image': deepcopy(image), 'duration_seconds': (high-low)/30,
            'focus_rect': layout['focus_rect'], 'disclosure': layout['disclosure'], 'live_result_depicted': False,
            'semantic_reveal': {'storyboard': deepcopy(storyboard_pin), 'cue_id': cue_id,
                'state_index': index, 'interval_frames': [low, high]}})
    return parts


class SemanticReferencePainter(Painter):
    """Existing Painter layout; Chinese header, no report reminder or false order."""
    def __init__(self, cue, font):
        super().__init__(cue, font)

    def _font(self, size):
        if size not in self.fonts:
            self.fonts[size] = ImageFont.truetype(self.fontpath, size)
        return self.fonts[size]

    def _wrap(self, value, width, size):
        lines, current = [], ''
        for char in value:
            if char == '\n' or self._font(size).getlength(current + char) > width:
                lines.append(current)
                current = '' if char == '\n' else char
            else:
                current += char
        if current:
            lines.append(current)
        return lines

    def text(self, draw, xy, text, size=36, fill=None):
        if xy == (100, 32) and text == 'FAITH & POWER':
            text = '信仰与权力'
        if xy == (1960, 32) and text == LABEL:
            text = SOURCE_LABEL
        if size == 28 and text == self.spec.get('proof_label', ''):
            return
        if (size == 40 and text in {'01','02','03'}
            and xy[0] in {134,959,1784} and 433 <= xy[1] <= 501):
            return
        if xy == (100, 145):
            while size > 48 and self._font(size).getlength(text) > 2360:
                size -= 1
            if self._font(size).getlength(text) > 2360:
                raise ValueError('Chinese graphic title exceeds layout')
        elif xy in {(104,250),(104,310)}:
            while size > 22 and self._font(size).getlength(text) > 2340:
                size -= 1
            if self._font(size).getlength(text) > 2340:
                raise ValueError('Chinese graphic subtitle/scope exceeds layout')
        draw.text(xy, text, font=self._font(size), fill=fill or self.ink)

    def wrapped(self, draw, xy, text, width, size=36, fill=None, max_lines=3):
        while size > 22 and len(self._wrap(text, width, size)) > max_lines:
            size -= 1
        lines = self._wrap(text, width, size)
        if len(lines) > max_lines:
            raise ValueError('Chinese semantic panel exceeds existing layout')
        for index, line in enumerate(lines):
            self.text(draw, (xy[0],xy[1]+index*(size+15)), line, size, fill)

    def terminal_frame(self):
        return self.frame(self.spec['duration_seconds'] - 1/3000)
