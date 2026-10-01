"""Add separately scoped R0127 save and a real paused-UI pair to a06.

`plan` is read-only. `prepare` requires an exact before/after capture-run pair,
original-PNG hashes and a recorded direct crop review before creating a run.
Only k025/r022/r029 change; 21 chunks, all subtitles and the original AAC
remain exact. This composer never records human signoff or uploads anything.
"""
from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import mimetypes
import re
import shutil
import sys
from pathlib import Path

import compose_review_boards_a04 as boards
import review_story_a04 as producer
from war_ai_promo import series_palette

ROOT = Path(__file__).resolve().parent
PREVIOUS = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-evidence-20261001-a01')
PREVIOUS_NAME = 'CK3-War-AI-Episode02-BrownGold-Evidence-20261001-a06.mp4'
PREVIOUS_SHA = 'F716D9F4FA79F3471941FF7FC4860A2D8F3D8EA103B73502D5C724609DB598D2'
PREVIOUS_BYTES = 239659692
A04 = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04')
A04_NAME = 'CK3-War-AI-Episode02-Review-20260930-a04.mp4'
A04_SHA = 'CB141C63966D86BDC8E267B4D958A79C1BB06A8EF69814DC0D6788F0345B8C7E'
OUTPUT_NAME = 'CK3-War-AI-Episode02-BrownGold-Supplement-20261001-a07.mp4'
TARGETS = ('knights-k025', 'reinforcement-r022', 'reinforcement-r029')
EXPECTED_CHUNKS = {('knights', 4), ('reinforcement', 3), ('reinforcement', 4)}
CHAPTERS = ['opening', 'pursuit', 'knights', 'reinforcement', 'terminal', 'closing']
PAUSE_FIELDS = ('revision', 'native_revision', 'snapshot_id', 'date_raw', 'paused', 'actor', 'army_id', 'army_state')
LEFT_RECT = (40, 164, 970, 815)
K025_LINES = (
    '1066.12.29存活 → 1066.12.30战死',
    '人物33437；基础勇武2→2',
    '后档：战死；击杀者34120',
    '本次选择器与唯一因果仍未证',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def pointer(document: object, location: str) -> object:
    require(location.startswith('/'), f'not a JSON pointer: {location}')
    for token in location[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


class RefChecks:
    """Hash each small receipt/PNG at most once per phase; never scan raw video."""

    def __init__(self) -> None:
        self.verified: dict[Path, dict] = {}

    def check(self, expected: dict, *, within: Path | None = None) -> dict:
        require(isinstance(expected, dict) and all(k in expected for k in ('path', 'bytes', 'sha256')),
                'input requires an explicit path/bytes/sha256 receipt')
        path = Path(expected['path']).resolve()
        if within is not None:
            require(path.is_relative_to(within.resolve()), f'cross-run source refused: {path}')
        if path not in self.verified:
            self.verified[path] = producer.ref(path)
        actual = self.verified[path]
        require(actual['bytes'] == expected['bytes'] and actual['sha256'] == expected['sha256'].upper(),
                f'input identity differs: {path}')
        return actual


def native_call_body(receipt: dict, checks: RefChecks, live_root: Path,
                     tool: str, arguments: dict) -> dict:
    """Verify the original transport envelope and its exact bound request."""
    request_ref = checks.check(receipt['request'], within=live_root)
    response_ref = checks.check(receipt['response'], within=live_root)
    request_path, response_path = Path(request_ref['path']), Path(response_ref['path'])
    require(request_path.parent.resolve() == (live_root / 'ck3-output/interactive-requests').resolve()
            and response_path.parent.resolve() == (live_root / 'ck3-output/interactive-requests-responses').resolve()
            and request_path.name == response_path.name, 'native request/response pair path differs')
    request = producer.read(request_path)
    require(request == {'action': 'mcp', 'tool': tool, 'arguments': arguments},
            'original native request tool/arguments differ')
    response = producer.read(response_path)
    require(receipt.get('result') == response.get('result') == 'CALL_COMPLETED'
            and receipt.get('error') is None and response.get('error') is None,
            'original native response transport did not complete')
    envelope_request = response.get('request')
    require(isinstance(envelope_request, dict), 'native response lacks original request binding')
    checks.check(envelope_request, within=live_root)
    require(Path(envelope_request['path']).resolve() == request_path.resolve()
            and envelope_request['bytes'] == request_ref['bytes']
            and envelope_request['sha256'].upper() == request_ref['sha256'],
            'native response envelope binds another original request')
    require(isinstance(response.get('body'), dict), 'native response lacks JSON body')
    return response['body']


def original_snapshot_values(body: dict) -> dict:
    """Recompute identity and paused revisions from the actual snapshot body."""
    require(body.get('format_version') == 1 and body.get('backend_id') == 'native-headless'
            and body.get('source') == 'injected-dll-named-pipe', 'original snapshot backend/provenance differs')
    actor = body.get('played_character') or {}
    require(actor.get('character_id') == 29829 and actor.get('source') == 'native'
            and actor.get('alive') is True, 'original snapshot Actor29829 identity differs')
    wars = body.get('active_wars')
    require(isinstance(wars, list) and all(isinstance(w, dict) for w in wars), 'original active wars missing')
    target_wars = [war for war in wars if war.get('war_id') == 4]
    require(len(target_wars) == 1 and target_wars[0].get('source') == 'native', 'original snapshot War4 identity differs')
    allied = [army for army in target_wars[0].get('allied_armies', []) if army.get('army_id') == 18]
    player = [army for army in body.get('player_armies', []) if army.get('army_id') == 18]
    require(len(allied) == len(player) == 1, 'original snapshot Army18 census differs')
    for army in (allied[0], player[0]):
        require(army.get('owner_character_id') == 29829 and army.get('source') == 'native'
                and army.get('army_state') == 'combat' and army.get('in_combat') is True
                and army.get('current_province_id') == 2633, 'original snapshot Army18 combat identity differs')
    values = {'date_raw': body.get('date_raw'), 'paused': body.get('paused'),
              'actor': actor['character_id'], 'revision': body.get('revision'),
              'native_revision': body.get('native_revision'), 'snapshot_id': body.get('snapshot_id'),
              'war_ids': [war['war_id'] for war in wars], 'army_id': allied[0]['army_id'],
              'army_state': allied[0]['army_state']}
    require(type(values['date_raw']) is int and values['paused'] is True
            and type(values['revision']) is int and type(values['native_revision']) is int
            and values['revision'] >= values['native_revision'] > 0
            and values['snapshot_id'] == f"native:{values['native_revision']}",
            'original snapshot date/paused/revision provenance differs')
    return values


def original_control_values(body: dict, snapshot: dict) -> dict:
    """Recompute wrapper and DTO provenance, including selected combat identity."""
    dto = body.get('battle_control_snapshot') or {}
    source = body.get('source') or {}
    require(body.get('backend_id') == source.get('backend_id') == 'native-headless'
            and body.get('schema_version') == dto.get('schema_version') == 1
            and body.get('scope') == 'exact-ongoing-battle'
            and dto.get('contract_stage') == 'production_exact_ongoing_combat', 'original control DTO contract differs')
    values = {'accepted': body.get('accepted'), 'status': body.get('status'),
              'root_native_revision': body.get('snapshot_revision'),
              'snapshot_native_revision': dto.get('snapshot_revision'),
              'queried_revision': body.get('queried_revision'),
              'queried_native_revision': body.get('queried_native_revision'),
              'queried_snapshot_id': body.get('queried_snapshot_id'),
              'source_revision': source.get('revision'), 'source_native_revision': source.get('native_revision'),
              'source_snapshot_id': source.get('snapshot_id'), 'source_date_raw': source.get('date_raw'),
              'source_paused': source.get('paused'), 'observed_date_raw': dto.get('observed_date_raw'),
              'subject_army_id': dto.get('subject_public_cunit_id'), 'native_army_id': dto.get('subject_native_carmy_id'),
              'owner_character_id': dto.get('selected_owner_character_id'), 'combat_id': dto.get('combat_id'),
              'combat_province_id': dto.get('combat_province_id'), 'battle_control_ready': dto.get('battle_control_ready')}
    require(values['accepted'] is True and values['status'] == dto.get('status') == 'available'
            and body.get('battle_control_ready') is True and values['battle_control_ready'] is True,
            'original control was not accepted/ready')
    require(values['queried_revision'] == values['source_revision'] == snapshot['revision']
            and values['root_native_revision'] == values['snapshot_native_revision']
            == values['queried_native_revision'] == values['source_native_revision'] == snapshot['native_revision']
            and values['queried_snapshot_id'] == values['source_snapshot_id'] == snapshot['snapshot_id']
            and values['observed_date_raw'] == values['source_date_raw'] == snapshot['date_raw']
            and values['source_paused'] is True, 'original control revision/date provenance differs from original snapshot')
    require(values['subject_army_id'] == values['native_army_id'] == body.get('subject_army_id') == 18
            and values['owner_character_id'] == body.get('selected_owner_character_id') == 29829
            and values['combat_id'] == 16777218
            and values['combat_province_id'] == dto.get('province_id') == body.get('combat_province_id') == 2633,
            'original control Actor/Army/Combat/Province identity differs')
    require(body.get('selected_public_cunit_id') == body.get('selected_native_carmy_id')
            == dto.get('selected_public_cunit_id') == dto.get('selected_native_carmy_id') == 18
            and body.get('side_index') == dto.get('side_index') == 1
            and body.get('side_scope') == dto.get('side_scope') == 'full_side',
            'original control selected-side provenance differs')
    selected = [army for army in (dto.get('defender') or {}).get('ordered_armies', [])
                if army.get('public_cunit_id') == 18]
    require(len(selected) == 1 and selected[0].get('native_carmy_id') == 18
            and selected[0].get('owner_character_id') == 29829
            and selected[0].get('combat_backlink_id') == 16777218,
            'original DTO selected Army18 combat backlink differs')
    return values


def chunk_mapping(timeline: dict) -> list[dict]:
    require([c['id'] for c in timeline['chapters']] == CHAPTERS, 'six chapters/order changed')
    require(sum(len(c['utterances']) for c in timeline['chapters']) == 167, '167-cue coverage changed')
    mapping = []
    for chapter in timeline['chapters']:
        old_receipts = producer.read(PREVIOUS / 'chapters' / chapter['id'] / 'chunk-receipts.json')
        groups = [chapter['utterances'][n:n+8] for n in range(0, len(chapter['utterances']), 8)]
        require(len(groups) == len(old_receipts), 'a06 chunk coverage differs')
        for index, (items, receipt) in enumerate(zip(groups, old_receipts), 1):
            mapping.append({
                'chapter': chapter['id'], 'chunk_index': index,
                'keys': [u['key'] for u in items],
                'duration_expected': sum(u['duration'] for u in items),
                'global_start': items[0]['global_start'],
                'local_start': items[0]['local_start'],
                'previous_receipt': receipt,
                'affected_keys': [u['key'] for u in items if u['key'] in TARGETS],
            })
    require(len(mapping) == 24, '24-chunk coverage changed')
    affected = {(r['chapter'], r['chunk_index']) for r in mapping if r['affected_keys']}
    require(affected == EXPECTED_CHUNKS, 'revision exceeds the three allowed chunks')
    require(all('knights-k035' not in r['keys'] for r in mapping if r['affected_keys']),
            'existing timed death-notice inset must be exact-copied')
    return mapping


def validate_k025(binding: dict, checks: RefChecks, old_edit: dict) -> dict:
    contract_ref = checks.check(binding['r0127_contract'])
    contract = producer.read(contract_ref['path'])
    require(contract['schema'] == 'ck3.a07.proposed-independent-R0127-left-card.v1', 'R0127 contract schema changed')
    require(contract['cue'] == TARGETS[0] and tuple(contract['replacement_rectangle_xyxy']) == LEFT_RECT,
            'only the declared k025 left region is permitted')
    require(tuple(contract['display_lines']) == K025_LINES, 'R0127 display claims changed')
    require(contract['heading'] == '独立补采R0127｜保存态，非020续帧', 'R0127 scope heading changed')
    base = checks.check(contract['base_board'])
    require(Path(base['path']).resolve() == Path(old_edit['utterances'][TARGETS[0]]['image']).resolve(),
            'k025 base is not the current a06 board')
    require(base['sha256'] == old_edit['utterances'][TARGETS[0]]['rendered_image']['sha256'], 'k025 base board changed')
    claims = contract['new_input_bindings']['independent_R0127_sources']
    require(len(claims) == 4, 'four independent R0127 claim objects are required')
    for claim in claims:
        checks.check(claim['source'])
        document = producer.read(claim['source']['path'])
        require(set(claim['json_pointers']) == set(claim['actual_resolved_values']), 'R0127 pointer coverage differs')
        for location, expected in claim['actual_resolved_values'].items():
            require(pointer(document, location) == expected, f'R0127 actual source value differs: {location}')
    saved = producer.read(claims[0]['source']['path'])
    before, after = [row['state'] for row in saved['states']]
    require(before['character_id'] == after['character_id'] == 33437, 'R0127 target identity changed')
    require(before['alive_data_present'] is True and before['dead_data_present'] is False,
            'R0127 before saved state is not alive')
    require(after['alive_data_present'] is False and after['dead_data_present'] is True,
            'R0127 after saved state is not dead')
    require(before['base_skill_values'][5] == after['base_skill_values'][5] == 2, 'R0127 base prowess changed')
    require(after['death_date'] == '1066.12.30' and after['death_reason'] == 'death_battle'
            and after['killer_character_id'] == 34120, 'R0127 saved death attribution changed')
    dates = producer.read(claims[3]['source']['path'])
    require(dates['actual_saved_and_ui_dates'] == ['1066.12.29', '1066.12.30']
            and dates['native_raw_date_pair'] == [53146848, 53146872], 'R0127 date pair changed')
    return {'contract': contract, 'receipt': contract_ref, 'base_board': base, 'claims': claims}


def validate_stage(stage: str, row: dict, checks: RefChecks, capture: dict) -> dict:
    """Admit a root-reviewed original paused frame; no OCR or assumed values."""
    import hashlib
    from PIL import Image
    live_root, controller = Path(capture['live_root']), Path(capture['sdk_controller'])
    sample_ref = checks.check(row['sample'], within=controller)
    require(Path(sample_ref['path']).name == f'{stage}-sample.json', 'sample stage filename differs')
    sample = producer.read(sample_ref['path'])
    require(sample['schema'] == 'xar.jd11.scoped-top-width.sample/v1' and sample['stage'] == stage,
            'sample schema or stage differs')
    for field in ('same_paused_frame_verified', 'battle_width_ui_observed', 'actor_army_native_bound_only'):
        require(sample.get(field) is True, f'{stage} gate not verified: {field}')
    for field in ('battle_width_ui_gap', 'full_battle_panel', 'whole_G2_complete',
                  'hook_instant_same_frame_claimed', 'numeric_UI_actor_army_claimed', 'historical_number_substitution'):
        require(sample.get(field) is False, f'{stage} scope boundary differs: {field}')
    review = sample['actual_visual_review']
    require(review.get('root_actually_viewed') is True and review.get('approved_for_current_action') is True,
            f'{stage} original pixels require root direct review')
    require(review['scope_mode'] == 'paused-battle-top-counts-and-width-tooltip', 'UI scope changed')
    for field in ('full_battle_panel', 'ui_actor_numeric_id_visible', 'ui_army_numeric_id_visible'):
        require(review.get(field) is False, f'{stage} review scope boundary differs: {field}')
    for gate in ('required_regions_visible', 'battle_context_visible', 'current_date_and_pause_visible',
                 'top_counts_visible', 'required_regions_unobscured', 'relative_soldiers_tooltip_visible',
                 'width_tooltip_numeric_visible', 'counts_sources_bound_to_this_battle'):
        require(review.get(gate) is True, f'{stage} original review gate missing: {gate}')
    values = sample['receipts']['values']
    after_pixels = sample['after_pixels_values']
    require(values['paused'] is True and all(values[k] == after_pixels[k] for k in PAUSE_FIELDS),
            f'{stage} state changed around the original screenshot')
    control_values = sample['receipts']['control_values']
    require(control_values['accepted'] is True and control_values['battle_control_ready'] is True
            and control_values['status'] == 'available', f'{stage} native control was rejected')
    paired = {'revision': 'source_revision', 'native_revision': 'source_native_revision',
              'snapshot_id': 'source_snapshot_id', 'date_raw': 'source_date_raw', 'paused': 'source_paused',
              'actor': 'owner_character_id', 'army_id': 'native_army_id'}
    require(all(values[k] == control_values[v] for k, v in paired.items()), f'{stage} native context is from another pause')
    for kind in ('snapshot', 'control'):
        for direction in ('request', 'response'):
            checks.check(sample['receipts'][kind][direction], within=live_root)
        require(sample['receipts'][kind]['result'] == 'CALL_COMPLETED'
                and sample['receipts'][kind]['error'] is None, f'{stage} native receipt failed')
    for direction in ('request', 'response'):
        checks.check(sample['after_pixels_snapshot'][direction], within=live_root)
    require(sample['after_pixels_snapshot']['result'] == 'CALL_COMPLETED'
            and sample['after_pixels_snapshot']['error'] is None, 'after-pixels native receipt failed')
    snapshot_body = native_call_body(sample['receipts']['snapshot'], checks, live_root, 'ck3_take_snapshot', {})
    original_values = original_snapshot_values(snapshot_body)
    require(original_values == values, f'{stage} summary differs from original snapshot JSON body')
    after_body = native_call_body(sample['after_pixels_snapshot'], checks, live_root, 'ck3_take_snapshot', {})
    original_after = original_snapshot_values(after_body)
    require(original_after == after_pixels and all(original_after[k] == original_values[k] for k in PAUSE_FIELDS),
            f'{stage} after-pixels summary/body differs from original paused snapshot')
    control_body = native_call_body(sample['receipts']['control'], checks, live_root,
                                   'ck3_query_battle_control_snapshot_v1',
                                   {'subject_army_id': 18, 'expected_revision': original_values['revision']})
    original_control = original_control_values(control_body, original_values)
    require(original_control == control_values, f'{stage} control summary differs from original control JSON/DTO')
    if 'post_visible_review_receipts' in sample or 'post_visible_review_values' in sample:
        require('post_visible_review_receipts' in sample and 'post_visible_review_values' in sample,
                'post-visible-review original native receipt/value binding incomplete')
        post = sample['post_visible_review_receipts']
        post_snapshot = original_snapshot_values(native_call_body(post['snapshot'], checks, live_root, 'ck3_take_snapshot', {}))
        require(post_snapshot == post['values'] == sample['post_visible_review_values']
                and all(post_snapshot[k] == original_values[k] for k in PAUSE_FIELDS),
                'post-visible-review snapshot summary/body differs from original same pause')
        post_control_body = native_call_body(post['control'], checks, live_root, 'ck3_query_battle_control_snapshot_v1',
                                            {'subject_army_id': 18, 'expected_revision': post_snapshot['revision']})
        post_control = original_control_values(post_control_body, post_snapshot)
        require(post_control == post['control_values'] and post_control_body['battle_control_snapshot']['final_combat_width']
                == control_body['battle_control_snapshot']['final_combat_width'],
                'post-visible-review control summary/body/width differs from original same pause')
    context_ref = checks.check(sample['scoped_native_context'], within=controller)
    require(review['scoped_native_context'] == sample['scoped_native_context'], 'review context binding differs')
    context = producer.read(context_ref['path'])
    require(context['schema'] == 'xar.jd11.scoped-top-width-native-context/v1', 'native context schema differs')
    require(all(context['values'][k] == values[k] for k in PAUSE_FIELDS), 'native context state differs')
    require(context['receipts'] == sample['receipts'] and context['not_UI_transcription'] is True
            and context['numeric_UI_actor_army_claimed'] is False, 'native context receipt/scope differs')
    visible = review['visible_values']
    require(visible['battle_title'] == '墨西拿之战' and visible['paused'] is True
            and visible['tooltip_title'] == '相对军力' and '战线宽度' in visible['width_label_text'],
            'required battle/paused/relative-soldier/width UI labels missing')
    width = visible['battle_width']
    require(type(width) is int and width > 0 and context['native_width'] == width,
            'actual tooltip and same-pause native width differ')
    require(control_body['battle_control_snapshot']['final_combat_width'] == width,
            'actual control JSON final_combat_width differs from UI')
    screenshots = []
    pixel_hashes = {}
    for kind in ('panel', 'tooltip'):
        frame = sample[kind]
        image_ref = checks.check(frame['screenshot'], within=controller)
        require(frame['current_run_only'] is True, 'frame does not declare current run only')
        require(image_ref in review['frames'], 'original screenshot is not bound by root visual review')
        with Image.open(image_ref['path']) as image:
            require(list(image.size) == frame['image_size'], 'original PNG dimensions differ')
            pixel_hashes[kind] = hashlib.sha256(image.convert('RGB').tobytes()).hexdigest().upper()
        for edge in ('before', 'after'):
            require(frame[edge]['expected_ck3_pid'] == review['expected_ck3_pid']
                    and frame[edge]['focus']['foreground_pid'] == review['expected_ck3_pid'],
                    'sample original PNG belongs to another CK3 process')
        screenshots.append(image_ref)
    tooltip_ref = checks.check(row['tooltip'], within=controller)
    require(tooltip_ref == screenshots[1], 'explicit PNG binding differs from the admitted tooltip')
    crop = row['crop_xyxy']
    require(isinstance(crop, list) and len(crop) == 4 and all(type(v) is int for v in crop),
            'root must provide four integer original-PNG crop coordinates')
    w, h = sample['tooltip']['image_size']
    require(0 <= crop[0] < crop[2] <= w and 0 <= crop[1] < crop[3] <= h, 'crop outside original image dimensions')
    crop_review = row['crop_review']
    require(crop_review['direct_original_pixel_review'] is True and crop_review['contains_width_tooltip'] is True
            and crop_review['source_sha256'].upper() == tooltip_ref['sha256']
            and crop_review['crop_xyxy'] == crop and bool(crop_review['reviewer']) and bool(crop_review['reviewed_at']),
            'root direct crop review must bind this exact PNG and rectangle')
    return {'stage': stage, 'run_id': capture['run_id'], 'sample_ref': sample_ref, 'sample': sample, 'context_ref': context_ref,
            'tooltip': tooltip_ref, 'panel': screenshots[0], 'crop_xyxy': crop, 'visible_values': visible,
            'width': width, 'pause_values': original_values, 'crop_review': crop_review,
            'original_PNG_RGB_sha256': pixel_hashes}


def validate_capture_identity(pair: dict, stages: dict, checks: RefChecks) -> dict:
    """Bind the caption to the real completed controller and capture receipts."""
    live_root, controller_root = Path(pair['live_root']).resolve(), Path(pair['sdk_controller']).resolve()
    capture_ref = checks.check(pair['capture_report'], within=live_root)
    controller_ref = checks.check(pair['controller_result'], within=controller_root)
    require(Path(capture_ref['path']).resolve() == (live_root / 'ck3-output/capture-report.json').resolve()
            and Path(controller_ref['path']).resolve() == (controller_root / 'controller-result.json').resolve(),
            'actual capture/controller result path differs from this same run')
    capture = producer.read(capture_ref['path'])
    controller = producer.read(controller_ref['path'])
    actual_run_id = capture.get('run_id')
    require(isinstance(actual_run_id, str) and bool(actual_run_id)
            and actual_run_id == controller.get('actual_run_id') == pair['actual_run_id']
            and actual_run_id.endswith('--' + pair['run_id']),
            'caption run-id differs from actual capture-report/controller run-id')
    require(capture.get('schema') == 'ck3-native-war-ai-raw-capture/v1'
            and capture.get('environment_session_complete') is True and bool(capture.get('finished_at'))
            and capture.get('result') == 'ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO'
            and (capture.get('worker') or {}).get('ok') is True,
            'actual capture environment session did not complete')
    require(controller.get('schema') == 'xar.jd11.scoped-top-width.controller-result/v1'
            and controller.get('scope_mode') == 'paused-battle-top-counts-and-width-tooltip'
            and controller.get('samples_completed') == 2 and controller.get('maximum_native_days') == 1
            and controller.get('date_advance_requested') is True
            and controller.get('one_day_proven_by_actual_paused_native_readback') is True,
            'actual controller did not complete two samples and one real date advance')
    require(controller.get('result') in ('SCOPED_TOP_WIDTH_PAIR_OBTAINED_UNREVIEWED',
                                        'SCOPED_TOP_WIDTH_PAIR_TRACE_INCOMPLETE_UNREVIEWED')
            and controller.get('error') is None and controller.get('cleanup_error') is None,
            'actual controller remains RED; cannot admit an invented pair')
    require(controller.get('capture_report') == pair['capture_report'], 'controller binds another capture-report identity')
    for stage in ('before', 'after'):
        require(controller.get(stage) == stages[stage]['sample'],
                f'actual controller {stage} sample differs from the explicit admitted sample')
    before, after = stages['before']['pause_values'], stages['after']['pause_values']
    require((controller.get('binding') or {}).get('track') == 'e2-06-d11'
            and (controller['binding'].get('spec') or {}).get('date') == before['date_raw'],
            'actual controller checkpoint/date binding differs from original before snapshot')
    checkpoint = capture.get('checkpoint_source') or {}
    require(checkpoint.get('actor') == before['actor'] == 29829
            and checkpoint.get('date_raw') == before['date_raw']
            and (checkpoint.get('source_lifecycle') or {}).get('xar_enabled') == 'xar_off',
            'actual capture checkpoint actor/date/vanilla scope differs')
    returned_date = controller.get('advance_returned_ending_date_raw')
    require(returned_date is None or returned_date == after['date_raw'], 'actual advance reply date differs from original after snapshot')
    if controller.get('one_day') is not None:
        advance = controller['one_day']
        request_ref = checks.check(advance['request'], within=live_root)
        response_ref = checks.check(advance['response'], within=live_root)
        request = producer.read(request_ref['path'])
        require(request.get('action') == 'mcp' and request.get('tool') == 'ck3_execute_step'
                and request.get('arguments', {}).get('step') == 'life-advance'
                and type(request.get('arguments', {}).get('expected_revision')) is int,
                'actual one-day request is not the bound life-advance action')
        reply = producer.read(response_ref['path'])
        require(reply.get('request') == advance['request'], 'actual one-day response binds another request')
        if advance.get('result') == 'CALL_COMPLETED':
            require(reply.get('result') == 'CALL_COMPLETED' and (reply.get('body') or {}).get('ending_date_raw') == after['date_raw'],
                    'actual one-day response date differs from original after snapshot')
        else:
            require(controller.get('one_day_reply_missing_or_ambiguous') is True,
                    'failed one-day response lacks separately retained ambiguity boundary')
    else:
        require(controller.get('one_day_reply_missing_or_ambiguous') is True,
                'actual controller lacks original one-day action receipt or recorded ambiguity')
    for kind in ('panel', 'tooltip'):
        require(stages['before'][kind]['sha256'] != stages['after'][kind]['sha256'],
                f'original before/after {kind} PNG bytes are identical; stale/date-substitution refused')
        require(stages['before']['original_PNG_RGB_sha256'][kind] != stages['after']['original_PNG_RGB_sha256'][kind],
                f'original before/after {kind} PNG decoded pixels are identical; metadata/re-encoding cannot substitute a new frame')
    response_sets = {}
    for stage in ('before', 'after'):
        sample = stages[stage]['sample']
        responses = [sample['receipts']['snapshot']['response'], sample['receipts']['control']['response'],
                     sample['after_pixels_snapshot']['response']]
        if 'post_visible_review_receipts' in sample:
            responses.extend(sample['post_visible_review_receipts'][kind]['response'] for kind in ('snapshot', 'control'))
        response_sets[stage] = {ref['sha256'].upper() for ref in responses}
    require(response_sets['before'].isdisjoint(response_sets['after']),
            'same original native JSON bytes reused across different dates')
    for document, label in ((capture, 'capture'), (controller, 'controller')):
        inventory = document.get('cleanup_process_inventory') if label == 'capture' else document.get('cleanup_inventory')
        require(isinstance(inventory, dict) and inventory.get('processes') == []
                and inventory.get('native_pids') == [] and inventory.get('tasklist_pids') == [],
                f'actual {label} cleanup inventory is not empty')
    require(controller.get('cleanup_inventory_empty') is True, 'actual controller cleanup is not proven')
    return {'actual_run_id': actual_run_id, 'capture_report': capture_ref, 'controller_result': controller_ref}


def validate_inputs(binding_path: Path, *, final_hash: bool = False) -> dict:
    checks = RefChecks()
    binding_ref = producer.ref(binding_path)
    binding = producer.read(binding_path)
    require(binding['schema'] == 'ck3.a07.explicit-evidence-bindings/v1', 'input binding schema differs')
    require(Path(binding['previous_run']).resolve() == PREVIOUS.resolve(), 'a07 must derive from exact a06 run')
    final_ref = binding['previous_final']
    require(Path(final_ref['path']).resolve() == (PREVIOUS / PREVIOUS_NAME).resolve()
            and final_ref['bytes'] == PREVIOUS_BYTES and final_ref['sha256'].upper() == PREVIOUS_SHA,
            'a06 final identity differs')
    require((PREVIOUS / PREVIOUS_NAME).stat().st_size == PREVIOUS_BYTES, 'a06 final size changed')
    if final_hash:
        checks.check(final_ref)
    timeline = producer.read(PREVIOUS / 'timeline.json')
    old_edit = producer.read(PREVIOUS / 'edit.json')
    mapping = chunk_mapping(timeline)
    require(len(old_edit['utterances']) == 167
            and sum(s['kind'] == 'raw-excerpt' for s in old_edit['utterances'].values()) == 13,
            '167 shots/13 raw excerpts changed')
    for key in TARGETS:
        checks.check(old_edit['utterances'][key]['rendered_image'])
    k025 = validate_k025(binding, checks, old_edit)
    pair = binding['reinforcement']
    require(re.fullmatch(r'R[0-9]{4}', pair['run_id']) is not None, 'actual capture run-id must be explicit')
    live_root, controller = Path(pair['live_root']).resolve(), Path(pair['sdk_controller']).resolve()
    require(Path(pair['live_root']).is_absolute() and Path(pair['sdk_controller']).is_absolute()
            and controller.name == 'paused-pair-controller', 'absolute actual live/controller roots are required')
    require(live_root.is_relative_to(Path('C:/Users/1/AppData/Local/ck3-capture-preparation').resolve())
            and controller.is_relative_to(Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001').resolve()),
            'capture sources must belong to the explicit external capture roots')
    require(pair.get('before') is not None and pair.get('after') is not None,
            'same-run before and after actual samples are required; after cannot be prefilled')
    stages = {stage: validate_stage(stage, pair[stage], checks, pair) for stage in ('before', 'after')}
    before, after = [stages[stage]['pause_values'] for stage in ('before', 'after')]
    require(before['actor'] == after['actor'] and before['army_id'] == after['army_id'], 'pair actor/army differ')
    require(after['date_raw'] - before['date_raw'] == 24, 'actual before/after native raw date difference must be exactly +24')
    require(stages['before']['visible_values']['date_text'] != stages['after']['visible_values']['date_text'],
            'actual before/after visible dates did not advance')
    identity = validate_capture_identity(pair, stages, checks)
    for stage in stages.values():
        stage['capture_identity'] = identity
    require(pair.get('session_cleanup') is not None, 'same real run must be cleaned before prepare; exact session-result receipt required')
    cleanup_ref = checks.check(pair['session_cleanup'], within=live_root)
    require(Path(cleanup_ref['path']).resolve() == (live_root / 'ck3-output/session-result.json').resolve(),
            'cleanup must be the same live-run session-result.json')
    cleanup = producer.read(cleanup_ref['path'])
    shutdown = cleanup['shutdown']
    require(cleanup['kind'] == 'ck3_native_headless_session' and bool(cleanup['finished_at'])
            and shutdown['cleanup_proven'] is True and shutdown['tree_gone'] is True
            and shutdown['job_active_processes_final'] == 0 and shutdown['ok'] is True,
            'same capture-run cleanup is not proven')
    require(shutdown['contract_errors'] == [] and shutdown['final_ck3_inventory']['native_pids'] == []
            and shutdown['final_ck3_inventory']['tasklist_pids'] == []
            and shutdown['final_ck3_inventory']['processes'] == [] and shutdown['watchdog_state_after'] == 'absent',
            'same capture-run process/watchdog cleanup is incomplete')
    require(all(s['sample']['actual_visual_review']['expected_ck3_pid'] == cleanup['pid'] for s in stages.values()),
            'before/after originals and cleanup belong to different CK3 processes')
    return {'binding': binding, 'binding_ref': binding_ref, 'verified_refs': list(checks.verified.values()),
            'timeline': timeline, 'old_edit': old_edit, 'mapping': mapping, 'k025': k025, 'stages': stages,
            'capture_identity': identity}


def plan(binding_path: Path) -> dict:
    state = validate_inputs(binding_path)
    return {'status': 'READY_FOR_PREPARE_PENDING_FRESH_TOOLCHAIN_RELEASE_QUERY',
            'read_only': True, 'new_run_created': False, 'binding': state['binding_ref'],
            'source_identity_method': 'small receipts and PNG hashes; a06 final size/declared identity; full a06 hash deferred to prepare',
            'target_keys': list(TARGETS), 'recompile_chunks': [r for r in state['mapping'] if r['affected_keys']],
            'exact_copy_chunk_count': 21, 'timed_k035_inset_exact_copy': True,
            'capture_run_id': state['binding']['reinforcement']['run_id'],
            'capture_identity': state['capture_identity'],
            'actual_paused_widths': {stage: row['width'] for stage, row in state['stages'].items()},
            'actual_paused_dates': {stage: {'visible_date': row['visible_values']['date_text'],
                                          'native_date_raw': row['pause_values']['date_raw'],
                                          'sample': row['sample_ref']} for stage, row in state['stages'].items()},
            'native_date_delta': 24,
            'human_signoff': 'not-provided', 'production_clean_admission': False}


def draw_k025(run: Path, old: dict, validated: dict) -> tuple[dict, dict]:
    from PIL import Image, ImageChops, ImageDraw
    contract = validated['contract']
    with Image.open(old['image']) as opened:
        before = opened.convert('RGB')
    after = before.copy()
    draw = ImageDraw.Draw(after)
    draw.rectangle((40, 164, 969, 814), fill=series_palette.BG)
    boards.fit_text(draw, (40, 167), contract['heading'], 920, 30, series_palette.GOLD)
    draw.rounded_rectangle((40, 220, 965, 775), radius=16, fill=series_palette.PANEL,
                           outline=series_palette.FAINT_RULE, width=2)
    for index, line in enumerate(K025_LINES):
        boards.fit_text(draw, (65, 265 + index * 106), line, 875, 35,
                        series_palette.MUTED if index == 3 else series_palette.INK)
    boards.fit_text(draw, (65, 718), '保存态读回；不代替角色UI或名单差分', 875, 25, series_palette.MUTED)
    path = run / 'boards/visuals/knights-k025.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as out:
        after.save(out, format='PNG')
    delta = ImageChops.difference(before, after)
    bbox = delta.getbbox()
    ImageDraw.Draw(delta).rectangle((40, 164, 969, 814), fill=(0, 0, 0))
    require(delta.getbbox() is None and bbox is not None, 'k025 changed outside the left card')
    spec = copy.deepcopy(old['spec'])
    for field in ('source_image', 'crop_xyxy', 'extra_ui'):
        spec.pop(field, None)
    spec.update({'source_kind': 'independent-saved-state-evidence-card', 'ui_label': contract['heading'],
                 'left_card': {'lines': list(K025_LINES), 'source_refs': [c['source'] for c in validated['claims']],
                               'scope': 'R0127 saved states; not an 020 continuation; selector and sole cause unverified'}})
    shot = {'kind': 'still', 'image': str(path), 'case': old['case'], 'source_kind': spec['source_kind'],
            'source_binding': validated['receipt'], 'source_bindings': [c['source'] for c in validated['claims']],
            'rendered_image': producer.ref(path), 'spec': spec, 'base_board': validated['base_board'],
            'replaced_historical_left_input': old['source_binding']}
    return shot, {'key': TARGETS[0], 'allowed_rectangles_xyxy': [list(LEFT_RECT)], 'difference_bbox': bbox,
                  'all_other_pixels_identical': True, 'original_board': validated['base_board'],
                  'revised_board': shot['rendered_image']}


def draw_width(run: Path, key: str, old: dict, validated: dict) -> tuple[dict, dict]:
    from PIL import Image, ImageChops, ImageDraw
    row = copy.deepcopy(old['spec'])
    stage_zh = '推进前' if validated['stage'] == 'before' else '推进后'
    run_id = validated['run_id']
    row.update({'source_image': validated['tooltip']['path'], 'crop_xyxy': validated['crop_xyxy'],
                'extra_ui': [], 'source_kind': f'{run_id}-original-paused-UI-with-independent-native-context',
                'ui_label': f"{run_id} {stage_zh}暂停UI｜战宽{validated['width']}｜非A01 hook帧",
                'footer': f'左：独立{run_id}暂停UI与同暂停原生快照；右：历史A01 hook记录／复算，非同一瞬时帧。'})
    fresh = boards.board(run / 'boards', key, row)
    require(fresh['source_binding'] == validated['tooltip'], 'new displayed UI binding differs from actual original PNG')
    for field in ('title', 'case', 'diagram_title', 'diagram_lines', 'highlight_line'):
        require(row[field] == old['spec'][field], f'old A01 field changed: {key}/{field}')
    fresh.update({'sample_binding': validated['sample_ref'], 'scoped_native_context': validated['context_ref'],
                  'root_crop_review': validated['crop_review'], 'old_A01_rhs_source_binding': old['source_binding'],
                  'capture_identity': validated['capture_identity'],
                  'new_UI_is_hook_instant': False})
    with Image.open(old['image']) as before, Image.open(fresh['image']) as after:
        delta = ImageChops.difference(before.convert('RGB'), after.convert('RGB'))
    bbox = delta.getbbox()
    allowed = ((40, 164, 970, 815), (40, 825, 1880, 895))
    for x1, y1, x2, y2 in allowed:
        ImageDraw.Draw(delta).rectangle((x1, y1, x2-1, y2-1), fill=(0, 0, 0))
    require(delta.getbbox() is None and bbox is not None, f'{key} changed outside left UI and explicit scope footer')
    return fresh, {'key': key, 'difference_bbox': bbox, 'allowed_rectangles_xyxy': allowed,
                   'all_other_pixels_identical': True, 'original_board': old['rendered_image'],
                   'revised_board': fresh['rendered_image'], 'original_PNG': validated['tooltip'],
                   'crop_xyxy': validated['crop_xyxy'], 'root_crop_review': validated['crop_review']}


def extend_catalog(state: dict) -> tuple[dict, list[dict]]:
    catalog = producer.read(PREVIOUS / 'claim-catalog.json')
    updated = copy.deepcopy(catalog)
    additions = []
    for chapter in updated['chapters']:
        for cue in chapter['utterances']:
            key = chapter['id'] + '-' + cue['id']
            new_facts = []
            if key == 'knights-k025':
                for claim in state['k025']['claims']:
                    new_facts.append({'claim': claim['claim'], 'source_path': claim['source']['path'],
                                      'source_field_or_line': claim['json_pointers'], 'source_binding': claim['source'],
                                      'evidence_layer': claim['evidence_layer'], 'confidence': 'verified',
                                      'scope': 'independent R0127; saved state/date evidence, not 020 continuation or selector/sole-cause proof'})
            elif key in ('reinforcement-r022', 'reinforcement-r029'):
                stage = 'before' if key == 'reinforcement-r022' else 'after'
                row = state['stages'][stage]
                new_facts = [
                    {'claim': f"独立{row['run_id']} {stage}暂停原版相对军力tooltip战线宽度{row['width']}",
                     'source_path': row['sample_ref']['path'], 'source_field_or_line': '/actual_visual_review/visible_values/battle_width',
                     'source_binding': row['sample_ref'], 'original_PNG': row['tooltip'],
                     'evidence_layer': 'direct-original-paused-UI-review', 'confidence': 'verified',
                     'scope': f"{row['run_id']} paused UI; not historical A01 hook instant; not full G2"},
                    {'claim': f"同一{row['run_id']} {stage}暂停原生control最终战宽{row['width']}",
                     'source_path': row['sample']['receipts']['control']['response']['path'],
                     'source_field_or_line': '/body/battle_control_snapshot/final_combat_width',
                     'source_binding': row['sample']['receipts']['control']['response'],
                     'evidence_layer': 'same-paused-native-control', 'confidence': 'verified',
                     'scope': 'native current paused state; not A01 entry/return/damage hook proof'},
                ]
                for fact in new_facts:
                    fact['capture_identity'] = row['capture_identity']
            if new_facts:
                old_count = len(cue['facts'])
                cue['facts'].extend(new_facts)
                additions.append({'key': key, 'old_fact_count': old_count, 'appended_facts': new_facts})
    require({a['key'] for a in additions} == set(TARGETS), 'catalog target coverage differs')
    restored = copy.deepcopy(updated)
    for chapter in restored['chapters']:
        for cue in chapter['utterances']:
            key = chapter['id'] + '-' + cue['id']
            for addition in additions:
                if addition['key'] == key:
                    cue['facts'] = cue['facts'][:addition['old_fact_count']]
    require(restored == catalog, 'old catalog/narration/visual metadata changed')
    return updated, additions


def prepare(run: Path, binding_path: Path, wheel_path: Path) -> None:
    require(not run.exists(), f'new run required; existing run refused: {run}')
    state = validate_inputs(binding_path, final_hash=True)  # no output or network until both samples pass
    wheel_ref = producer.ref(wheel_path)
    run.mkdir(parents=True, exist_ok=False)
    for name in ('sources', 'logs', 'boards', 'audit'):
        (run / name).mkdir()
    latest_out = producer.command(run, 'latest-formal-release', ['gh', 'release', 'view', '--repo',
        'XenoAmess/xar_promo_toolchain', '--json', 'tagName,name,publishedAt,url,assets,isDraft,isPrerelease'])
    latest = producer.read(latest_out)
    installed = importlib.metadata.version('xar-promo-toolchain')
    require(not latest['isDraft'] and not latest['isPrerelease'] and latest['tagName'].lstrip('v') == installed,
            'install the freshly queried latest formal wheel with the selected interpreter before prepare')
    asset = next(a for a in latest['assets'] if a['name'] == wheel_path.name)
    require(asset['digest'].split(':')[-1].upper() == wheel_ref['sha256'], 'supplied wheel SHA differs from latest formal release')
    distribution = importlib.metadata.distribution('xar-promo-toolchain')
    direct_url_text = distribution.read_text('direct_url.json')
    require(direct_url_text is not None, 'installed wheel lacks direct_url provenance; reinstall the exact formal wheel')
    direct_url = json.loads(direct_url_text)
    archive = direct_url.get('archive_info') or {}
    installed_hash = (archive.get('hashes') or {}).get('sha256')
    if installed_hash is None and archive.get('hash', '').startswith('sha256='):
        installed_hash = archive['hash'].split('=', 1)[1]
    require(isinstance(installed_hash, str) and installed_hash.upper() == wheel_ref['sha256'],
            'installed distribution provenance SHA differs from supplied latest formal wheel')
    producer.write(run / 'release-query.json', {'queried_at_utc': producer.stamp(), 'release': latest, 'wheel': wheel_ref})
    branch_out = producer.command(run, 'source-branch', ['git', '-C', str(ROOT), 'branch', '--show-current'])
    branch = branch_out.read_text(encoding='utf-8').strip()
    require(branch and branch != 'master', 'independent branch required; master run refused')
    head_out = producer.command(run, 'source-head', ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'])
    producer.write(run / 'sources/environment.json', {'at_utc': producer.stamp(), 'python': sys.executable,
        'python_version': sys.version, 'promo_version': installed, 'wheel': wheel_ref,
        'installed_wheel_provenance': direct_url,
        'pillow_version': importlib.metadata.version('Pillow'), 'edge_tts_version': importlib.metadata.version('edge-tts'),
        'ffmpeg': str(producer.FFMPEG), 'ffprobe': str(producer.FFPROBE), 'branch': branch,
        'source_head': head_out.read_text(encoding='utf-8').strip(), 'no_TTS_game_desktop_cloud': True})
    for name, argv in [('version', ['--version']), ('help', ['--help']), ('start-help', ['start-run', '--help']),
                       ('preserve-help', ['preserve', '--help']), ('validate-help', ['validate', '--help'])]:
        producer.command(run, 'toolchain-' + name, [sys.executable, '-X', 'utf8', '-m', 'xar_promo', *argv])
    config = producer.read(PREVIOUS / 'project-config.json')
    config['project'].update({'id': 'ck3-war-ai-episode02-brown-gold-supplement-a07',
                              'title': '战斗后半笔账：独立保存态与暂停战宽补证'})
    producer.write(run / 'project-config.json', config)
    producer.command(run, 'start-run', [sys.executable, '-X', 'utf8', '-m', 'xar_promo', 'start-run',
        str(run / 'project-config.json'), '--run-id', run.name, '--run-directory', str(run / 'native-run')])
    producer.command(run, 'validate-config', [sys.executable, '-X', 'utf8', '-m', 'xar_promo', 'validate', str(run / 'project-config.json')])
    frozen_sources = []
    source_paths = [Path(__file__), Path(boards.__file__), Path(producer.__file__), Path(series_palette.__file__)]
    for path in source_paths:
        shutil.copyfile(path, run / 'sources' / path.name)
        frozen_sources.append(producer.ref(path))
    shutil.copyfile(binding_path, run / 'evidence-bindings.json')
    shutil.copyfile(state['k025']['receipt']['path'], run / 'sources/R0127-left-card-contract.json')
    for index, item in enumerate(state['verified_refs'], 1):
        source = Path(item['path'])
        if source.resolve() == (PREVIOUS / PREVIOUS_NAME).resolve():
            continue  # retained a06 video referenced by exact identity, not duplicated as an evidence blob
        target = run / 'sources/accepted-inputs' / f'{index:03d}-{source.name}'
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
        require(producer.sha(target) == item['sha256'], 'frozen accepted source copy differs')
    for source, target in [('timeline.json', 'timeline.json'), ('claim-catalog.json', 'sources/a06-claim-catalog.json'),
                           ('edit.json', 'sources/a06-edit.json'), ('final-artifact.json', 'sources/a06-final-artifact.json')]:
        shutil.copyfile(PREVIOUS / source, run / target)
    new_edit = copy.deepcopy(state['old_edit'])
    pixel_checks = []
    shot, check = draw_k025(run, state['old_edit']['utterances'][TARGETS[0]], state['k025'])
    new_edit['utterances'][TARGETS[0]] = shot
    pixel_checks.append(check)
    for key, stage in [('reinforcement-r022', 'before'), ('reinforcement-r029', 'after')]:
        shot, check = draw_width(run, key, state['old_edit']['utterances'][key], state['stages'][stage])
        new_edit['utterances'][key] = shot
        pixel_checks.append(check)
    require(all(shot == new_edit['utterances'][key] for key, shot in state['old_edit']['utterances'].items()
                if key not in TARGETS), 'unapproved shot changed')
    catalog, additions = extend_catalog(state)
    producer.write(run / 'edit.json', new_edit)
    producer.write(run / 'claim-catalog.json', catalog)
    producer.write(run / 'claim-additions.json', additions)
    producer.write(run / 'card-pixel-checks.json', pixel_checks)
    producer.write(run / 'chunk-plan.json', state['mapping'])
    producer.write(run / 'input-freeze.json', {'at_utc': producer.stamp(), 'previous_final': state['binding']['previous_final'],
        'binding': state['binding_ref'], 'wheel': wheel_ref, 'project_sources': frozen_sources,
        'verified_evidence_refs': state['verified_refs'],
        'previous_documents': [producer.ref(PREVIOUS / name) for name in
                               ('timeline.json', 'edit.json', 'claim-catalog.json', 'chapters.ffmetadata')]})
    producer.write(run / 'edit-input-freeze.json', {'edit': producer.ref(run / 'edit.json'),
        'claim_catalog': producer.ref(run / 'claim-catalog.json'), 'claim_additions': producer.ref(run / 'claim-additions.json'),
        'new_boards': [new_edit['utterances'][key]['rendered_image'] for key in TARGETS],
        'all_original_raw_shots': [shot for shot in new_edit['utterances'].values() if shot['kind'] == 'raw-excerpt'],
        'raw_binding_method': 'retained original exact receipt and current size; no repeated full raw hashing',
        'timeline_audio': [{k: u[k] for k in ('key', 'audio', 'tts_raw', 'tts_trimmed')}
                           for chapter in state['timeline']['chapters'] for u in chapter['utterances']]})
    producer.write(run / 'revision-intent.json', {'at_utc': producer.stamp(), 'target_keys': list(TARGETS),
        'recompiled_chunks': 3, 'exact_copy_chunks': 21, 'output_name': OUTPUT_NAME,
        'R0127_scope': 'independent saved-state card; not 020 continuation; selector and sole cause unverified',
        'capture_run_id': state['binding']['reinforcement']['run_id'],
        'capture_identity': state['capture_identity'],
        'paused_pair_scope': 'same cleaned run before/after original paused UI and native control; dates +24; historical A01 hook remains separate',
        'actual_paused_widths': {stage: row['width'] for stage, row in state['stages'].items()},
        'actual_paused_dates': {stage: {'visible_date': row['visible_values']['date_text'], 'native_date_raw': row['pause_values']['date_raw'],
                                      'sample': row['sample_ref']} for stage, row in state['stages'].items()},
        'cleanup_receipt': state['binding']['reinforcement']['session_cleanup'],
        'narration_subtitle_timing_AAC_unchanged': True, 'old_fact_objects_unchanged': True,
        'timed_k035_notice_chunk_exact_copy': True, 'human_signoff': 'not-provided', 'production_clean_admission': False})
    print(json.dumps({'phase': 'prepared', 'run': str(run), 'recompile_chunks': 3, 'exact_copy_chunks': 21}))


def verify_prepared(run: Path) -> dict:
    freeze = producer.read(run / 'input-freeze.json')
    checks = RefChecks()
    checks.check(freeze['binding'])
    for item in freeze['project_sources']:
        checks.check(item)  # fail if implementation changed after prepare
    for item in freeze['verified_evidence_refs']:
        checks.check(item)
    for item in freeze['previous_documents']:
        checks.check(item)
    require((run / 'timeline.json').read_bytes() == (PREVIOUS / 'timeline.json').read_bytes(), 'timeline bytes changed')
    edit_freeze = producer.read(run / 'edit-input-freeze.json')
    checks.check(edit_freeze['edit'])
    checks.check(edit_freeze['claim_catalog'])
    checks.check(edit_freeze['claim_additions'])
    for item in edit_freeze['new_boards']:
        checks.check(item)
    for shot in edit_freeze['all_original_raw_shots']:
        require(Path(shot['source_binding']['path']).stat().st_size == shot['source_binding']['bytes'], 'raw source size differs')
    timeline = producer.read(run / 'timeline.json')
    edit = producer.read(run / 'edit.json')
    selected = {key for row in producer.read(run / 'chunk-plan.json') if row['affected_keys'] for key in row['keys']}
    for key in selected:
        shot = edit['utterances'][key]
        if shot['kind'] != 'raw-excerpt':
            checks.check(shot['rendered_image'])
    for chapter in timeline['chapters']:
        for cue in chapter['utterances']:
            checks.check(cue['tts_trimmed'])
            require(Path(cue['audio']).resolve() == Path(cue['tts_trimmed']['path']).resolve(), 'audio path differs from exact trimmed narration')
    mapping = producer.read(run / 'chunk-plan.json')
    require(mapping == chunk_mapping(timeline), 'prepared chunk plan differs')
    return {'timeline': timeline, 'edit': producer.read(run / 'edit.json'), 'mapping': mapping}


def render(run: Path) -> None:
    state = verify_prepared(run)
    timeline, edit, mapping = [state[key] for key in ('timeline', 'edit', 'mapping')]
    require(not (run / 'chapters').exists(), 'render is append-only; use a fresh run after any partial render')
    checks = RefChecks()
    receipts = {}
    for row in mapping:
        cid, index = row['chapter'], row['chunk_index']
        previous_root = PREVIOUS / 'chapters' / cid / f'chunk-{index:02d}'
        checks.check(row['previous_receipt'])
        if row['affected_keys']:
            chapter = next(c for c in timeline['chapters'] if c['id'] == cid)
            items = [u for u in chapter['utterances'] if u['key'] in row['keys']]
            require(all(not edit['utterances'][u['key']].get('raw_notice_inset') for u in items),
                    'shared renderer cannot replace existing timed raw inset')
            receipts[cid, index] = producer.render_chunk(run, chapter, edit, items, index)
        else:
            target = run / 'chapters' / cid / f'chunk-{index:02d}'
            shutil.copytree(previous_root, target)
            copied = producer.ref(target / 'chunk.mp4')
            require(copied['sha256'] == row['previous_receipt']['sha256']
                    and copied['bytes'] == row['previous_receipt']['bytes'], 'exact chunk copy differs')
            receipts[cid, index] = {**copied, 'duration_expected': row['duration_expected']}
    chunk_diff = []
    for row in mapping:
        cid, index = row['chapter'], row['chunk_index']
        name = f'chapters/{cid}/chunk-{index:02d}/subtitles.ass'
        require((run / name).read_bytes() == (PREVIOUS / name).read_bytes(), f'ASS bytes changed: {name}')
        chunk_diff.append({**row, 'new_receipt': receipts[cid, index], 'subtitle_bytes_identical': True,
                           'action': 'recompiled-authorized-left-evidence' if row['affected_keys'] else 'exact-byte-copy',
                           'chunk_bytes_identical': receipts[cid, index]['sha256'] == row['previous_receipt']['sha256']})
    producer.write(run / 'a06-to-a07-chunk-diff.json', chunk_diff)
    chapters = []
    for chapter in timeline['chapters']:
        cid = chapter['id']
        root = run / 'chapters' / cid
        chunks = [receipts[cid, row['chunk_index']] for row in mapping if row['chapter'] == cid]
        producer.write(root / 'chunk-receipts.json', chunks)
        concat = root / 'concat.txt'
        producer.text_once(concat, ''.join("file '" + r['path'].replace(chr(92), '/') + "'\n"
                            + f"duration {r['duration_expected']:.9f}\n" for r in chunks))
        output = root / 'chapter.mp4'
        producer.command(run, cid + '-chapter-join', [str(producer.FFMPEG), '-hide_banner', '-nostdin', '-n',
            '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', '-movflags', '+faststart', str(output)])
        chapters.append({**producer.ref(output), 'duration_expected': chapter['duration']})
    producer.write(run / 'chapter-render-receipts.json', chapters)
    concat = run / 'concat.txt'
    producer.text_once(concat, ''.join("file '" + r['path'].replace(chr(92), '/') + "'\n"
                        + f"duration {r['duration_expected']:.9f}\n" for r in chapters))
    metadata = run / 'chapters.ffmetadata'
    shutil.copyfile(PREVIOUS / 'chapters.ffmetadata', metadata)
    joined = run / 'rendered-supplement-with-chunk-audio.mp4'
    producer.command(run, 'final-join', [str(producer.FFMPEG), '-hide_banner', '-nostdin', '-n', '-f', 'concat',
        '-safe', '0', '-i', str(concat), '-f', 'ffmetadata', '-i', str(metadata), '-map', '0', '-map_metadata', '1',
        '-map_chapters', '1', '-c', 'copy', '-movflags', '+faststart', str(joined)])
    original = producer.ref(A04 / A04_NAME)
    require(original['sha256'] == A04_SHA, 'original a04 AAC source identity changed')
    output = run / OUTPUT_NAME
    producer.command(run, 'final-original-AAC-copy', [str(producer.FFMPEG), '-hide_banner', '-nostdin', '-n',
        '-i', str(joined), '-i', original['path'], '-map', '0:v:0', '-map', '1:a:0', '-map_metadata', '0',
        '-map_chapters', '0', '-c', 'copy', '-movflags', '+faststart', str(output)])
    probe = producer.probe(run, 'final-probe', output)
    producer.write(run / 'final-probe.json', probe)
    identity = producer.ref(output)
    final = {**identity, 'duration_expected': timeline['total_duration'], 'previous': producer.read(run / 'input-freeze.json')['previous_final'],
             'original_aac_source': original, 'recompiled_chunks': 3, 'copied_chunks': 21,
             'timeline_unchanged': True, 'subtitle_bytes_identical_in_all_chunks': True,
             'final_aac_stream_copied': True, 'human_signoff': 'not-provided', 'production_clean_admission': False,
             'status': 'pending-independent-machine-and-frame-review'}
    for name in ('final-artifact.json', 'final-brown-gold-artifact.json'):
        producer.write(run / name, final)
    producer.write(run / 'a06-to-a07-diff.json', {'at_utc': producer.stamp(), 'a06': final['previous'], 'a07': identity,
        'target_keys': list(TARGETS), 'card_pixel_checks': producer.read(run / 'card-pixel-checks.json'),
        'claim_additions': producer.read(run / 'claim-additions.json'), 'chunk_diff': chunk_diff,
        'chapter_metadata_identical': (run / 'chapters.ffmetadata').read_bytes() == (PREVIOUS / 'chapters.ffmetadata').read_bytes(),
        'timeline_bytes_identical': True, 'all_ASS_bytes_identical': True, 'final_AAC_copied_from_a04': True,
        'human_signoff': 'not-provided', 'production_clean_admission': False})
    print(json.dumps(identity))


def preserve(run: Path, *, failed: bool = False) -> None:
    """Native preservation includes partial/failure outputs; no audit or approval."""
    from xar_promo.operations import preserve_artifact
    from xar_promo.project import load_document
    from xar_promo.runlog import append_phase_record
    manifest = run / 'native-run/run-manifest.json'
    require(manifest.is_file(), 'native run must exist before preservation')
    require(not (run / 'native-preservation-complete.json').exists(), 'preservation already completed; do not reuse IDs')
    paths = [p for p in sorted(run.rglob('*')) if p.is_file() and 'native-run' not in p.parts]
    records = []
    final_path = run / OUTPUT_NAME
    final = producer.read(run / 'final-artifact.json') if (run / 'final-artifact.json').is_file() else None
    if not failed:
        require(final is not None and producer.ref(final_path) == {k: final[k] for k in ('path', 'bytes', 'sha256')},
                'final exact identity is required for successful build preservation')
        paths = [final_path, *[p for p in paths if p != final_path]]
    for index, path in enumerate(paths, 1):
        deliverable = not failed and path == final_path
        record = preserve_artifact(manifest, path, artifact_id='a07-deliverable' if deliverable else f'a07-retained-{index:04d}',
            collection='derived', role='deliverable' if deliverable else 'process-evidence', label=path.name,
            media_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        records.append({'source': producer.ref(path), 'preserved': record.to_dict()})
    producer.write(run / 'retained-process-index.json', {'at_utc': producer.stamp(), 'subject': final,
        'process_files': [producer.ref(path) for path in paths], 'human_signoff': 'not-provided',
        'production_clean_admission': False, 'failed_attempt_preserved': failed})
    preserve_artifact(manifest, run / 'retained-process-index.json', artifact_id='a07-process-index', collection='derived',
                      role='process-index', label='retained-process-index.json', media_type='application/json')
    append_phase_record(manifest, phase_id='project-independent-evidence-supplement',
        status='failed' if failed else 'succeeded', artifact_ids=[] if failed else ['a07-deliverable'],
        detail='All partial/failure evidence retained.' if failed else
        'R0127 save card and explicitly bound same cleaned capture-run paused UI in 3 chunks; other 21 exact-copy; original AAC copy. No machine audit, human signoff or upload.')
    loaded = load_document(manifest, check_files=True)
    producer.write(run / 'native-preservation-complete.json', {'at_utc': producer.stamp(), 'manifest': producer.ref(manifest),
        'artifacts': records, 'human_signoffs': len(loaded.run.signoffs), 'failed_attempt_preserved': failed})
    producer.command(run, 'validate-preserved-run', [sys.executable, '-X', 'utf8', '-m', 'xar_promo', 'validate', str(manifest)])
    print(json.dumps(producer.ref(run / 'native-preservation-complete.json')))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['plan', 'prepare', 'render', 'preserve'])
    parser.add_argument('--bindings', type=Path, help='exact receipt/PNG and direct crop review JSON; required for plan/prepare')
    parser.add_argument('--run', type=Path, help='new external run; prepare refuses existing directories')
    parser.add_argument('--wheel', type=Path, help='actual latest formal wheel file; required for prepare')
    parser.add_argument('--failed', action='store_true', help='preserve partial/failed native run; preserve phase only')
    args = parser.parse_args()
    if args.phase in ('plan', 'prepare') and args.bindings is None:
        parser.error('--bindings is required for plan/prepare')
    if args.phase != 'plan' and args.run is None:
        parser.error('--run is required for prepare/render/preserve')
    if args.phase == 'prepare' and args.wheel is None:
        parser.error('--wheel is required for prepare')
    if args.failed and args.phase != 'preserve':
        parser.error('--failed is accepted only by preserve')
    if args.run:
        if not args.run.is_absolute() or any(args.run.resolve().is_relative_to(p.resolve()) for p in (ROOT, PREVIOUS, A04)):
            parser.error('--run must be an absolute external a07 directory, separate from all historical inputs')
        if args.phase in ('render', 'preserve'):
            config_path = args.run / 'project-config.json'
            if not config_path.is_file() or producer.read(config_path)['project']['id'] != 'ck3-war-ai-episode02-brown-gold-supplement-a07':
                parser.error('render/preserve require an existing run created by this a07 composer')
    existed = args.run.exists() if args.run else False
    try:
        if args.phase == 'plan':
            print(json.dumps(plan(args.bindings), ensure_ascii=False, indent=2))
        elif args.phase == 'prepare':
            prepare(args.run, args.bindings, args.wheel)
        elif args.phase == 'render':
            render(args.run)
        else:
            preserve(args.run, failed=args.failed)
    except Exception as error:
        failure = {'at_utc': producer.stamp(), 'phase': args.phase, 'error_type': type(error).__name__,
                   'error': str(error), 'human_signoff': 'not-provided'}
        print(json.dumps(failure, ensure_ascii=False), file=sys.stderr)
        if args.run and args.run.exists() and not (args.phase == 'prepare' and existed):
            failure_path = args.run / f'{args.phase}-failure.json'
            if not failure_path.exists():
                producer.write(failure_path, failure)
                manifest = args.run / 'native-run/run-manifest.json'
                if manifest.is_file():
                    from xar_promo.runlog import append_phase_record
                    append_phase_record(manifest, phase_id='project-' + args.phase, status='failed', artifact_ids=[],
                        detail=f'{type(error).__name__}: {error}; all partial outputs retained; preserve --failed is available.')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
