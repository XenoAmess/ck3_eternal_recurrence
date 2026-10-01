"""Read-only concise build/lifecycle status with actual heterogeneous receipt schemas."""
from pathlib import Path
import argparse
import json
import psutil

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-root', type=Path)
    args = parser.parse_args()
    result = {'build':{},'processes':[]}
    build = ROOT / 'frozen-release-build-attempt-01'
    for path in sorted(build.glob('*-result.json')):
        body = json.loads(path.read_text(encoding='utf-8'))
        result['build'][path.name] = {'returncode':body.get('returncode'),
            'test_count':body.get('test_count'),'all_ran_without_failure_or_skip':body.get('all_ran_without_failure_or_skip')}
    for process in psutil.process_iter(['pid','name','create_time','cmdline']):
        try:
            info = process.info
            if (info['name'] or '').lower() in {'ck3.exe','xar_ck3_bridge_injector.exe','cl.exe','ninja.exe','cmake.exe','ffmpeg.exe','obs64.exe'}:
                result['processes'].append(info)
        except (psutil.NoSuchProcess,psutil.AccessDenied):
            pass
    if args.live_root:
        output = args.live_root / 'ck3-output'
        result['live_output_files'] = [path.name for path in output.glob('*') if path.is_file()]
        for name in ('native-start-readback.json','live-run-identity.json','capture-report.json','runtime-cleanup.json'):
            path = output / name
            if path.is_file():
                body = json.loads(path.read_text(encoding='utf-8-sig'))
                if name == 'native-start-readback.json':
                    snapshot = body.get('snapshot',{})
                    body = {'postcondition_verified':body.get('postcondition_verified'),
                            'date_raw':snapshot.get('date_raw'),'paused':snapshot.get('paused'),
                            'played_character':snapshot.get('played_character'),
                            'episode_run_id':snapshot.get('episode_run_id')}
                result[name] = body
        result['interactive_requests'] = [path.name for path in (output / 'interactive-requests').glob('*.json')]
    print(json.dumps(result,ensure_ascii=False))

if __name__ == '__main__':
    main()
