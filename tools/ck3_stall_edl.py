"""CK3 receipt adapter for the external metadata-only stall EDL library.

No media probing, hashing, encoder or runtime API. The supplied wallclock
endpoints remain estimates until separately bound PTS and visual review.
"""
import hashlib
import json
from pathlib import Path
import time

if __package__:
    from .promo_toolchain_loader import ensure_promo_toolchain
    from .g2_saved_campaign.shared_harness_reads import read_bytes
    from .g2_saved_campaign.runtime_repair_auto_applied import clock_receipt
else:
    from promo_toolchain_loader import ensure_promo_toolchain
    from g2_saved_campaign.shared_harness_reads import read_bytes
    from g2_saved_campaign.runtime_repair_auto_applied import clock_receipt
ensure_promo_toolchain()
from xar_promo.stall_edl import build, as_config, rebuild, stamp, utc

def read(path):
    path = Path(path)
    # Live status files use atomic replace. Retry only transient sharing errors;
    # never turn a malformed receipt or an absent file into an empty success.
    for attempt in range(6):
        try:
            if path.stat().st_size > 8 * 1024 * 1024:
                raise ValueError('Metadata read exceeds bounded receipt size')
            return json.loads(read_bytes(path))
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.02)


def pin(path):
    path = Path(path).resolve(strict=True)
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Only bounded metadata receipts may be pinned')
    return {'path': str(path), 'sha256': hashlib.sha256(read_bytes(path)).hexdigest()}


def create(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def decode(row):
    wrapper = row.get('result')
    if not isinstance(wrapper, dict) or wrapper.get('is_error', wrapper.get('isError')):
        return None
    body = wrapper.get('structured_content', wrapper.get('structuredContent'))
    if isinstance(body, dict):
        return body
    for item in wrapper.get('content') or []:
        if item.get('type') == 'text':
            try:
                body = json.loads(item.get('text', ''))
            except (ValueError, TypeError):
                continue
            if isinstance(body, dict):
                return body
    return None


def progress(row):
    body = decode(row)
    result = (body or {}).get('result') or {}
    start, end = result.get('starting_date_raw'), result.get('ending_date_raw')
    if (row.get('request', {}).get('tool') != 'ck3_auto_turn'
            or (body or {}).get('status') != 'executed'
            or not isinstance((body or {}).get('selected_step'), str)
            or type(start) is not int or type(end) is not int or end <= start):
        raise ValueError('Recovery endpoint requires actual executed AUTO calendar progress')
    stamp(row['ended_at_utc'])
    return {'at_utc': row['ended_at_utc'], 'starting_date_raw': start,
            'ending_date_raw': end, 'date_delta_raw': end - start,
            'source': 'actual_AUTO_calendar_advance_receipt', 'frame_exact': False}


def resolve(old, interval_id, response_path):
    config = as_config(old)
    candidates = [i for i in config['intervals'] if i['id'] == interval_id]
    if len(candidates) != 1 or candidates[0].get('end_at_utc'):
        raise ValueError('Exactly one open wait is required')
    actual = progress(clock_receipt(response_path))
    if stamp(actual['at_utc']) < stamp(candidates[0]['start_at_utc']):
        raise ValueError('Progress receipt predates the wait')
    candidates[0].update(end_at_utc=actual['at_utc'], recovery_evidence=actual,
        recovery_receipt=pin(response_path))
    return rebuild(config, old)


def sync_status(old, status_path):
    """Consume Root status metadata; v5 progress timestamp prevents late badges
    from extending the waiting edit across already resumed normal gameplay.
    """
    state = read(status_path)
    if state.get('schema') != 'xar.runtime-repair-status/v1':
        raise ValueError('Unknown repair status')
    binding = state.get('source_binding', state['binding'])
    compatible = [s for s in old['segments'] if s.get('game_pid') == binding.get('game_pid')
                  and s.get('game_creation_filetime') == binding.get('game_creation_filetime')]
    if not compatible:
        raise ValueError('Status Game generation is outside supplied recording sources')
    config = as_config(old)
    identity = 'repair-incident-' + state['incident_id']
    matches = [i for i in config['intervals'] if i.get('incident_id') == state['incident_id'] or i['id'] == identity]
    if not matches:
        # Older manually seeded waits carry their original AUTO sequence.
        sequence = state.get('original_request', {}).get('sequence')
        namespace = binding.get('sdk_prefix')
        # Missing sequences are not an AUTO identity. Only a positive integer
        # in the same known SDK namespace can claim a legacy seeded wait.
        if type(sequence) is int and sequence > 0 and isinstance(namespace, str) and namespace:
            matches = [i for i in config['intervals']
                       if type(i.get('original_auto_sequence')) is int
                       and i['original_auto_sequence'] == sequence
                       and i.get('game_pid') == binding['game_pid']
                       and i.get('source_sdk_prefix') == namespace]
    if len(matches) > 1:
        raise ValueError('Incident ambiguously matches multiple waits')
    if state.get('withdrawn') is True or state.get('EDL_wait_interval_allowed') is False:
        # A display-only false incident is not footage to compress and is not
        # a recovery. Preserve the withdrawal as metadata, without inventing
        # an endpoint or removing another incident's genuine closed wait.
        removed = [i for i in config['intervals'] if i.get('incident_id') == state['incident_id']]
        config['intervals'] = [i for i in config['intervals'] if i not in removed]
        marker_id = state['incident_id'] + '-withdrawn-no-edit'
        if not any(m.get('id') == marker_id for m in config['markers']):
            config['markers'].append({'id': marker_id, 'kind': 'withdrawn_false_incident_no_edit',
                'at_utc': state.get('withdrawn_at_utc', state.get('opened_at_utc')),
                'incident_id': state['incident_id'], 'recovery_claimed': False,
                'removed_interval_ids': [i['id'] for i in removed],
                'normal_footage_must_not_be_compressed': True})
        config['evidence_pins']['status-' + state['incident_id']] = pin(status_path)
        return rebuild(config, old)
    if (matches and matches[0].get('end_at_utc')
            and matches[0].get('incident_id') not in (None, state['incident_id'])):
        # One SDK request cannot be a second waiting interval after its real
        # progress was already recorded, even if a restarted observer gives
        # the old HALT a new display incident ID.
        config['evidence_pins']['duplicate-status-' + state['incident_id']] = pin(status_path)
        return rebuild(config, old)
    if matches:
        item = matches[0]
    else:
        original = state.get('halt_receipt') or {}
        halt = read(original['path'])
        if pin(original['path']) != original:
            raise ValueError('Immutable halt changed')
        response_path = halt.get('original_response')
        response = read(response_path) if response_path else {}
        ended = response.get('ended_at_utc') or state['opened_at_utc']
        item = {'id': identity, 'incident_id': state['incident_id'],
            'game_pid': binding['game_pid'], 'start_at_utc': ended, 'end_at_utc': None,
            'start_basis': 'actual_failed_response_end' if response.get('ended_at_utc') else 'status_detection_time_only',
            'halt_receipt': original, 'original_auto_sequence': state.get('original_request', {}).get('sequence'),
            'source_sdk_prefix': binding.get('sdk_prefix')}
        config['intervals'].append(item)
    item.update(incident_id=state['incident_id'], brief_reason=state['pause_reason'])
    proof = state.get('recovery_proof') or {}
    if not item.get('end_at_utc') and proof.get('kind') == 'actual_settled_AUTO_and_paired_MET_calendar_progress':
        source_pin = proof['AUTO']
        if pin(source_pin['path']) != source_pin:
            raise ValueError('Actual AUTO progress source changed')
        actual = progress(clock_receipt(source_pin['path']))
        if actual['at_utc'] != proof.get('actual_progress_ended_at_utc'):
            raise ValueError('Status differs from original actual progress timestamp')
        if proof.get('Game_pid') != binding['game_pid'] or actual['date_delta_raw'] != proof.get('actual_date_delta_raw'):
            raise ValueError('Progress binding mismatch')
        item.update(end_at_utc=actual['at_utc'], recovery_evidence=actual, recovery_receipt=source_pin)
    if state.get('phase') in ('resolved', 'expired') and state.get('resolved_at_utc'):
        marker_id = state['incident_id'] + '-repair-notice'
        if not any(m.get('id') == marker_id for m in config['markers']):
            config['markers'].append({'id': marker_id, 'at_utc': state['resolved_at_utc'],
                'kind': 'repair_notice_separate_from_first_progress', 'interval_id': item['id'],
                'does_not_extend_wait_end': True})
    config['evidence_pins']['status-' + state['incident_id']] = pin(status_path)
    return rebuild(config, old)
