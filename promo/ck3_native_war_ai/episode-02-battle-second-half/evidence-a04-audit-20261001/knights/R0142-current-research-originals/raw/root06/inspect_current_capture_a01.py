"""Concise readonly process/run/assets summary, never advances or approves."""
from pathlib import Path
import argparse
import json
import psutil

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-root', type=Path, required=True)
    args = parser.parse_args()
    live = args.live_root
    summary = {'processes': [p.info for p in psutil.process_iter(['pid', 'name', 'create_time']) if (p.info['name'] or '').lower() in ('ck3.exe', 'ffmpeg.exe', 'obs64.exe', 'xar_ck3_bridge_injector.exe')],
               'live_exists': live.exists()}
    for name in ('live-run-identity.json', 'native-start-readback.json'):
        path = live / 'ck3-output' / name
        if not path.is_file(): continue
        body = json.loads(path.read_text(encoding='utf-8-sig'))
        if name.startswith('live-run'):
            summary['allocated'] = body.get('identities')
        else:
            snap = body.get('snapshot', {})
            summary['native_start'] = {'postcondition_verified': body.get('postcondition_verified'),
                'date_raw': snap.get('date_raw'), 'paused': snap.get('paused'),
                'episode_run_id': snap.get('episode_run_id'),
                'played_character': snap.get('played_character'),
                'diagnostics': {k: snap.get('diagnostics', {}).get(k) for k in ('bridge_pid', 'connection_generation')}}
    evidence = live / 'scoped-ui-research-attempt-01'
    assets = []
    for path in sorted(evidence.glob('*binding.json')):
        body = json.loads(path.read_text(encoding='utf-8'))
        native = body.get('readback_body', {})
        assets.append({'record': str(path), 'phase': body.get('phase'), 'source_values': body.get('source_values'),
                       'image': body.get('image'), 'window_kind': native.get('window_kind'),
                       'subject_id': native.get('subject_id'), 'available': native.get('available'),
                       'left_knight_count': native.get('left_knight_count'), 'right_knight_count': native.get('right_knight_count'),
                       'left_knight_breakdown': native.get('left_knight_breakdown'), 'right_knight_breakdown': native.get('right_knight_breakdown')})
    summary['ui_assets'] = assets
    print(json.dumps(summary, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
