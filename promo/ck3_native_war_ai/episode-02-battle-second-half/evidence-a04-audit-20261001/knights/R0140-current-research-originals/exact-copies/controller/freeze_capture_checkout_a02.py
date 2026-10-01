"""Create a separate clean capture branch from the explicitly reviewed local commit."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PATTERNS = ['/ck3_autonomous_player/', '/docs/ck3-native-ai/', '/promo/ck3_native_war_ai/integration/',
            '/promo/ck3_native_war_ai/episode-02-battle-second-half/*.py', '/tools/*.py', '/tools/requirements*.txt']

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args()
    source, checkout = args.source.resolve(), args.checkout.resolve()
    require(not checkout.exists(), 'Frozen capture checkout already exists')
    require(args.branch.startswith('codex/war-e2-') and all(c.isalnum() or c in '/-_' for c in args.branch), 'Private capture branch required')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == args.source_commit,
            'Reviewed local source commit differs')
    require(not subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=source, text=True).strip(),
            'Research source is not clean and frozen')
    steps = []
    def run(argv, cwd, standard_input=None):
        completed = subprocess.run(argv, cwd=cwd, input=standard_input, capture_output=True, text=True, encoding='utf-8')
        row = {'argv': argv, 'cwd': str(cwd), 'stdin': standard_input, 'returncode': completed.returncode,
               'stdout': completed.stdout, 'stderr': completed.stderr, 'at_utc': datetime.now(timezone.utc).isoformat()}
        steps.append(row)
        with (ROOT / ('freeze-checkout-step-' + str(len(steps)) + '.json')).open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(row, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        require(completed.returncode == 0, 'Capture checkout preparation failed; retain existing state and receipts')
        return completed.stdout.strip()
    run(['git', 'worktree', 'add', '--no-checkout', '-b', args.branch, str(checkout), args.source_commit], source)
    run(['git', 'sparse-checkout', 'set', '--no-cone', '--stdin'], checkout, '\n'.join(PATTERNS) + '\n')
    run(['git', 'read-tree', '-mu', 'HEAD'], checkout)
    require(run(['git', 'rev-parse', 'HEAD'], checkout) == args.source_commit, 'Frozen capture HEAD differs')
    require(run(['git', 'branch', '--show-current'], checkout) == args.branch, 'Capture branch is not the requested private branch')
    require(not run(['git', 'status', '--porcelain=v1'], checkout), 'New frozen capture checkout is dirty')
    pins = [identity(checkout / relative) for relative in (
        'ck3_autonomous_player/native_bridge/CMakeLists.txt',
        'promo/ck3_native_war_ai/integration/capture_session.py',
        'ck3_autonomous_player/native_bridge/research/ingame_ui_navigation_v1_abi.json')]
    ledger = {'schema': 'ck3.e2.clean-private-capture-checkout/v1', 'source': str(source), 'source_commit': args.source_commit,
              'checkout': str(checkout), 'branch': args.branch, 'sparse_patterns': PATTERNS, 'pins': pins,
              'owner': '/root', 'reason': 'Keep admitted runtime source immutable while independent verification proceeds',
              'acceptance': 'Exact-build six-gap causal and original UI evidence before any video revision',
              'deadline': 'Retain branch until user explicitly authorizes integration',
              'master_intake_or_merge': False, 'no_game_launch': True, 'steps': steps}
    with (ROOT / 'frozen-capture-checkout.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(ledger, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'result': 'CLEAN_PRIVATE_CAPTURE_CHECKOUT_CREATED', 'branch': args.branch, 'source_commit': args.source_commit}))

if __name__ == '__main__':
    main()
