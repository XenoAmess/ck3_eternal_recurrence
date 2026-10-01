"""Commit only the four reviewed source files on the existing private branch."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/w/e2research1001')
OLD_HEAD = 'fda53e7b3e83053f235be3d5725a6238b89db9f0'
READY = Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-ui-hidden-modal-repair-other-a01/source-freeze-ui-hidden-modal-a02/source-ready-and-test-receipt.json')
READY_SHA = 'BED9386BAD72A03160BBDFC2BCA0C6B4268BC8C3274580EACEBA6A6018FC334F'
FILES = (
 'ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp',
 'ck3_autonomous_player/native_bridge/tests/ingame_ui_navigation_v1_test.cpp',
 'ck3_autonomous_player/native_bridge/research/ingame_ui_navigation_v1_abi.json',
)
def require(ok, msg):
    if not ok: raise RuntimeError(msg)
def ident(path):
    path = Path(path).resolve()
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest().upper()}
def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE).decode('utf-8').strip()
def main():
    require(git('rev-parse', 'HEAD') == OLD_HEAD, 'Private predecessor changed')
    require(git('branch', '--show-current') == 'codex/war-e2-mechanism-closure-20261001', 'Wrong private branch')
    rows = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=SOURCE).decode('utf-8').splitlines()
    require(len(rows) == 4 and all(row.startswith(' M ') for row in rows) and {row[3:] for row in rows} == set(FILES), 'Unexpected source/index changes')
    require(ident(READY)['sha256'] == READY_SHA, 'Ready receipt changed')
    body = json.loads(READY.read_text(encoding='utf-8'))
    bound = {}
    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str) and 'bytes' in value and 'sha256' in value:
                path = Path(value['path']).resolve()
                if path in {(SOURCE / name).resolve() for name in FILES}:
                    current = ident(path)
                    require(current['bytes'] == value['bytes'] and current['sha256'] == value['sha256'].upper(), 'Reviewed source changed')
                    bound[str(path)] = current
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(body)
    require(len(bound) == 4, 'Ready receipt missing source pins')
    write('private-hidden-modal-freeze-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
          'predecessor': OLD_HEAD, 'source_inputs': list(bound.values()), 'ready': ident(READY),
          'ready_body': body, 'live_pending': True, 'master_intake': False, 'video_changed': False})
    for index, argv in enumerate((['git', 'diff', '--check'], ['git', 'add', '--', *FILES],
        ['git', 'diff', '--cached', '--check'], ['git', 'commit', '-m', 'Honor original effective-hidden modal receiver admission for scoped UI research'])):
        result = subprocess.run(argv, cwd=SOURCE, capture_output=True)
        for suffix, data in [('stdout', result.stdout), ('stderr', result.stderr)]:
            with (ROOT / f'private-source-step-{index+1}-{suffix}.bin').open('xb') as stream: stream.write(data)
        write(f'private-source-step-{index+1}.json', {'argv': argv, 'returncode': result.returncode,
              'stdout': ident(ROOT / f'private-source-step-{index+1}-stdout.bin'),
              'stderr': ident(ROOT / f'private-source-step-{index+1}-stderr.bin')})
        require(result.returncode == 0, 'Private commit command failed; raw output retained')
    require(not git('status', '--porcelain=v1'), 'Committed source dirty')
    require(set(git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines()) == set(FILES), 'Commit scope differs')
    write('private-source-commit.json', {'source_commit': git('rev-parse', 'HEAD'), 'source': str(SOURCE),
          'branch': git('branch', '--show-current'), 'no_master_intake': True, 'live_pending': True})
    print(git('rev-parse', 'HEAD'))
if __name__ == '__main__': main()
