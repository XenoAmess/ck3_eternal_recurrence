"""Commit the exact independently reviewed two-line local integration correction."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/w/e2research1001')
EVIDENCE = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
BRIDGE = 'ck3_autonomous_player/native_bridge/src/bridge.cpp'

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE).decode('utf-8').strip()

def main():
    require(git('rev-parse', 'HEAD') == 'bfec9e22e48be16677014f0466f7b7cf9f9984c7', 'Unexpected private source HEAD')
    require(git('branch', '--show-current') == 'codex/war-e2-mechanism-closure-20261001', 'Wrong private branch')
    require(git('status', '--porcelain=v1').strip() == 'M ' + BRIDGE, 'Unrelated changes')
    require(git('diff', '--numstat') == '0\t2\t' + BRIDGE, 'Not the reviewed minimal correction')
    bridge = identity(SOURCE / BRIDGE)
    require(bridge['bytes'] == 1092626 and bridge['sha256'] == 'CA9687A443FFDBE668F947C7BD3EFC60C1FF08720991BFC3D98698DEB8D80445', 'Bridge bytes changed')
    freeze = EVIDENCE / 'mechanism-native-bundle-attempt-01/scoped-publisher-source-freeze-a04/source-freeze-and-test-receipt.json'
    require(identity(freeze)['sha256'] == 'E34912B4BC442CD05CF5C9390EA77858051ABDA1A799F11824B3193E6FB5683B', 'Ready freeze changed')
    for row in json.loads(freeze.read_text(encoding='utf-8'))['source_inputs']:
        current = identity(row['path'])
        require(current['bytes'] == row['bytes'] and current['sha256'] == row['sha256'], 'Frozen input changed')
    review = EVIDENCE / 'scoped-observer-residency-compile-review-other-a01/independent-two-line-residency-review-a01.json'
    require(identity(review)['sha256'] == 'E0344FF8FACB57031047A04FD6CF685C2BAEC1355DE22D2693B98E328C71C23B', 'Review changed')
    tu = EVIDENCE / 'mechanism-native-bundle-attempt-01/build-attempt-13-managed-parent-residency-bridge-tu/actual-bridge-tu-receipt.json'
    require(identity(tu)['sha256'] == 'A127A3267CC9E696D7F9F97D1584224BFDFB588B507C443FE4D3BB8C3067584B', 'Actual TU receipt changed')
    require(json.loads(tu.read_text(encoding='utf-8'))['status'] == 'ACTUAL_RELEASE_BRIDGE_CPP_TU_COMPILED_PASS_DLL_LINK_NOT_RUN', 'Actual TU not passed')
    write('private-residency-fix-intent.json', {'source': str(SOURCE), 'bridge': bridge,
        'freeze': identity(freeze), 'review': identity(review), 'actual_tu': identity(tu),
        'prior_full_build_RED_preserved': True, 'full_new_build_and_live_pending': True, 'remote_or_master_operation': False})
    for index, argv in enumerate((['git', 'diff', '--check'], ['git', 'add', '--', BRIDGE],
        ['git', 'diff', '--cached', '--check'], ['git', 'commit', '-m', 'Fix observer parent residency integration using real managed detour ownership'])):
        result = subprocess.run(argv, cwd=SOURCE, capture_output=True, text=True, encoding='utf-8')
        write(f'private-residency-fix-step-{index + 1}.json', {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        require(result.returncode == 0, 'Private correction commit step failed')
    require(not git('status', '--porcelain=v1'), 'Committed source not clean')
    write('private-source-commit.json', {'source_commit': git('rev-parse', 'HEAD'),
        'source': str(SOURCE), 'branch': git('branch', '--show-current'), 'no_master_intake': True, 'live_pending': True})
    print(git('rev-parse', 'HEAD'))

if __name__ == '__main__':
    main()
