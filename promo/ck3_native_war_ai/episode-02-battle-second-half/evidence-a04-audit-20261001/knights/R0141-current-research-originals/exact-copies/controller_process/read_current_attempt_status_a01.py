"""Read-only concise build/lifecycle status; never infer semantic completion."""
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
        result['build'][path.name] = json.loads(path.read_text(encoding='utf-8'))['returncode']
    out = build / 'build-stdout.bin'
    if out.is_file():
        data = out.read_bytes()
        result['build_stdout_bytes'] = len(data)
        result['build_stdout_tail'] = data.decode('utf-8', errors='replace').splitlines()[-8:]
    candidate = build / 'candidate-manifest.json'
    if candidate.is_file():
        result['candidate'] = json.loads(candidate.read_text(encoding='utf-8'))
    for process in psutil.process_iter(['pid','name','create_time','cmdline']):
        try:
            info = process.info
            if (info['name'] or '').lower() in {'ck3.exe','xar_ck3_bridge_injector.exe','cl.exe','ninja.exe','cmake.exe','ffmpeg.exe','obs64.exe'}:
                result['processes'].append(info)
        except (psutil.NoSuchProcess,psutil.AccessDenied):
            pass
    if args.live_root:
        output = args.live_root / 'ck3-output'
        result['live_output_files'] = [str(path.relative_to(output)) for path in output.glob('*') if path.is_file()]
        for name in ('native-start-readback.json','live-run-identity.json','capture-report.json','runtime-cleanup.json'):
            path = output / name
            if path.is_file():
                body = json.loads(path.read_text(encoding='utf-8-sig'))
                if name == 'native-start-readback.json':
                    body = {key:body.get(key) for key in ('postcondition_verified','result','error','snapshot')}
                    snap = body.get('snapshot')
                    if isinstance(snap,dict):
                        body['snapshot'] = {key:snap.get(key) for key in ('date_raw','paused','played_character','episode_run_id','diagnostics')}
                result[name] = body
        requests = output / 'interactive-requests'
        result['interactive_requests'] = [path.name for path in requests.glob('*.json')]
    print(json.dumps(result,ensure_ascii=False))

if __name__ == '__main__':
    main()
