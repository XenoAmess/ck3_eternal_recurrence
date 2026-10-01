from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
NEW = ROOT / 'preparation-attempt-02'
NEW.mkdir(exist_ok=False)
original = ROOT / 'prepare_new_capture.py'
data = original.read_bytes()
needle = b"prelaunch = read(ROOT.parent / 'root-attempt-02/native-research-plan.json')"
replacement = b"prelaunch = read(Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-02/native-research-plan.json'))"
assert data.count(needle) == 1
with (NEW / 'prepare_new_capture_a02.py').open('xb') as stream: stream.write(data.replace(needle, replacement))
sdk = ROOT / 'run_new_capture_sdk.py'
with (NEW / sdk.name).open('xb') as stream: stream.write(sdk.read_bytes())
def ident(p): return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest().upper()}
with (NEW / 'helper-derivation.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump({'original': ident(original), 'derived': ident(NEW / 'prepare_new_capture_a02.py'),
        'only_source_change': 'Explicit original prelaunch plan path because new attempt is nested',
        'sdk_exact_original': ident(sdk), 'sdk_exact_copy': ident(NEW / sdk.name),
        'prior_no_launch_RED_preserved': True, 'next_paths': 'D26 exact source track requires episode02-e2-05-d26 prefix',
        'game_launched': False, 'video_changed': False}, stream, indent=2); stream.write('\n')
print(str(NEW))
