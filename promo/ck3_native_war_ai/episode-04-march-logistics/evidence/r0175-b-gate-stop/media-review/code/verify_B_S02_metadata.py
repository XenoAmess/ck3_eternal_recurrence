"""Read only this relative small-source package; never open referenced media."""
import argparse
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), 'relative source leaves package')
    return json.loads(path.read_bytes())


def derive(root):
    delivery = read_json(root, 'inputs/media-delivery.json')
    audit = read_json(root, 'inputs/media-audit-report.json')
    review = read_json(root, 'inputs/Root-encoded-review.json')
    terminal = read_json(root, 'inputs/B-S02-sealed-result.json')
    disposition = read_json(root, 'inputs/B-formal-terminal.json')
    require(audit['state'] == 'PASS' and audit['errors'] == [], 'audit did not pass')
    require(audit['source_identity'] == delivery['source_identity_terminal_reused'], 'media source pin disagrees')
    require(audit['terminal_result_identity'] == delivery['terminal_result_identity'] == review['actual_closed_terminal'], 'sealed terminal pin disagrees')
    require(delivery['media_machine_audit'] == review['media_audit'], 'audit pin disagrees')
    require(audit['audit_raw_sha_reads'] == 0 and audit['sealed_terminal_hash_reused'] is True, 'unexpected raw hash policy')
    require(audit['decoded_frames'] == audit['video_packets'] == 62400, 'frame/packet counts disagree')
    require(audit['actual_duration_seconds'] == '2080.000000', 'unexpected duration')
    require(audit['video_stream']['r_frame_rate'] == '30/1', 'unexpected fps')
    require(audit['stream_counts'] == {'video': 1, 'audio': 0, 'all': 1}, 'unexpected streams')
    require([audit['video_stream'][key] for key in ('width', 'height')] == [1920, 1080], 'unexpected dimensions')
    require(all(item['returncode'] == 0 and item['stderr_identity']['bytes'] == 0 for item in audit['probe_receipts'].values()), 'probe failure')
    require(audit['strict_full_decode']['reached_progress_end'] is True and audit['strict_full_decode']['final_decoded_frames'] == 62400 and audit['strict_full_decode']['errors_on_stderr'] == 0, 'strict decode did not complete')
    for name in ('packet_pts', 'packet_dts', 'frame_pts', 'frame_best_effort_timestamp', 'frame_packet_dts'):
        stamp = audit['timestamps'][name]
        require(stamp['count'] == stamp['present'] == 62400 and stamp['missing'] == 0 and stamp['strictly_increasing'] is True, 'timestamp audit failed: ' + name)
    require(review['same_B_clock_no_reset'] is True and review['B_status'] == 'STOPPED_GATE_INCOMPLETE', 'Root disposition changed')
    require(review['B_London_or_winner_credit'] == 0 and review['continuous_clean_span'] is None and review['human_1x_complete_watch'] is False and review['human_signoff'] is False, 'unsupported review credit')
    require(len(delivery['encoded_candidates']) == len(review['reviewed_encoded_stills']) == 3, 'expected three reviewed stills')
    for candidate, observed in zip(delivery['encoded_candidates'], review['reviewed_encoded_stills']):
        require(candidate['encoded_png_identity'] == observed['actual_encoded_frame'], 'reviewed PNG pin disagrees')
        require(candidate['actual_decoded_frame_zero_based'] == observed['frame_ordinal'] and candidate['actual_pts'] == observed['PTS_ms'] and candidate['time_base'] == '1/1000', 'encoded ordinal/PTS disagrees')
        require(0 <= observed['frame_ordinal'] < audit['decoded_frames'], 'still outside actual tape')
        require(observed['native_exact_event_PTS'] is None and observed['hypothetical_hover_Sea_ETA_is_not_actual_route'] is True, 'event/route boundary lost')
    # Terminal shape is validated below from the original record, never a raw path.
    require(terminal['state'] == 'NORMAL_TREE_EMPTY', 'S02 did not seal normally')
    require(disposition['status'] == 'STOPPED_GATE_INCOMPLETE', 'formal B stop changed')
    relation = delivery['experiment_relation']
    require(relation['same_episode_run_id'] == 'native-33388-23726fbd8a80' and relation['same_B_as_S01'] is True and relation['checkpoint_reload'] is False and relation['experiment_date_and_budget_reset'] is False, 'same experiment boundary failed')
    require(relation['stopped_relative_day'] == 38 and relation['London_comparable_arrival'] is False and relation['strategy_winner'] is None, 'arrival/winner boundary failed')
    return {
        'schema': 'ck3.e04.B.S02.media-review-metadata.v1',
        'status': 'PASS_PINNED_SMALL_MEDIA_AUDIT_AND_ROOT_THREE_STILL_REVIEW',
        'B_disposition': 'STOPPED_GATE_INCOMPLETE',
        'B_stopped_day': 38,
        'B_London_endpoint': None,
        'winner': None,
        'media_audit_state': 'PASS',
        'raw_pin_from_owned_terminal_only': audit['source_identity'],
        'actual_duration_seconds': audit['actual_duration_seconds'],
        'decoded_frames': audit['decoded_frames'],
        'video_packets': audit['video_packets'],
        'fps': audit['video_stream']['r_frame_rate'],
        'resolution': [1920, 1080],
        'audio_streams': 0,
        'Root_reviewed_stills': [
            {'frame_ordinal': item['frame_ordinal'], 'PTS_ms': item['PTS_ms'], 'observed_original_pixels': item['observed_original_pixels'], 'image_pin': item['actual_encoded_frame']}
            for item in review['reviewed_encoded_stills']
        ],
        'per_segment_PTS_independent': True,
        'exact_native_event_PTS': None,
        'continuous_clean_span': None,
        'human_1x_complete_watch': False,
        'human_signoff': False,
        'raw_or_PNG_read_by_this_consumer': False,
        'native_source_body_rescan': False,
        'original_delivery_Root_review_pending_retained': True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if not args.verify:
        print(json.dumps({'status': 'PLAN_ONLY', 'reads_media': False}))
        return 0
    root = Path(__file__).resolve().parents[1]
    manifest = read_json(root, 'manifest.json')
    require(manifest['schema'] == 'ck3.e04.B.S02.small-media-package.v1', 'unsupported manifest')
    for pin in manifest['files']:
        relative = Path(pin['path'])
        require(not relative.is_absolute() and '..' not in relative.parts and ':' not in pin['path'], 'unsafe relative pin')
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()), 'pin leaves package')
        require(path.suffix in ('.json', '.py', '.md'), 'media or unsupported file in small package')
        raw = path.read_bytes()
        require(len(raw) <= 1000000 and len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'relative byte pin mismatch: ' + pin['path'])
    actual = derive(root)
    require(actual == read_json(root, 'B-S02-media-review-values.json'), 'derived summary differs')
    print(json.dumps(actual, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(json.dumps({'status': 'FAIL_SMALL_METADATA_VALIDATION', 'error': str(error)}, ensure_ascii=False))
        raise SystemExit(1)
