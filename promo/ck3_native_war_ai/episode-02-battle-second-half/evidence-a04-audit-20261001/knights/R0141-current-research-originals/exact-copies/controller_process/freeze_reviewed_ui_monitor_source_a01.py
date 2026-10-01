"""Freeze exact reviewed private UI admission and monitor semantics; no remote operations."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/w/e2research1001')
OLD_HEAD = '0bb40ba1495c4bb15f24e152799d1f62eb1a2420'
FILES = (
 'ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/frontend_gui_route_v1.cpp',
 'ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp',
 'ck3_autonomous_player/native_bridge/tests/ingame_ui_navigation_v1_test.cpp',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
 'ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py',
 'ck3_autonomous_player/src/xar_autoplayer/simulation/knight_variable_monitor_projection.py',
 'ck3_autonomous_player/native_bridge/research/verify_knight_variable_monitor_run.py')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest().upper()}

def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE).decode('utf-8').strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ui-freeze', type=Path, required=True)
    parser.add_argument('--ui-freeze-sha', required=True)
    parser.add_argument('--monitor-freeze', type=Path, required=True)
    parser.add_argument('--monitor-freeze-sha', required=True)
    args = parser.parse_args()
    require(git('rev-parse', 'HEAD') == OLD_HEAD, 'Private predecessor differs')
    require(git('branch', '--show-current') == 'codex/war-e2-mechanism-closure-20261001', 'Wrong private branch')
    status = subprocess.check_output(['git','status','--porcelain=v1'], cwd=SOURCE).decode('utf-8')
    rows = status.splitlines()
    require(len(rows) == len(FILES) and all(row.startswith(' M ') for row in rows) and
            {row[3:] for row in rows} == set(FILES), 'Unexpected staged or unrelated source changes')
    receipts = []
    bindings = {}
    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str) and 'bytes' in value and 'sha256' in value:
                path = Path(value['path']).resolve()
                if path in { (SOURCE / name).resolve() for name in FILES }:
                    current = identity(path)
                    require(current['bytes'] == value['bytes'] and current['sha256'] == value['sha256'].upper(),
                            'Reviewed ready source changed: ' + str(path))
                    bindings[str(path)] = current
            for child in value.values():
                visit(child)
        elif isinstance(value,list):
            for child in value:
                visit(child)
    for path, sha in ((args.ui_freeze,args.ui_freeze_sha), (args.monitor_freeze,args.monitor_freeze_sha)):
        pin = identity(path)
        require(pin['sha256'] == sha.upper(), 'Reviewed freeze receipt changed')
        body = json.loads(path.read_text(encoding='utf-8'))
        visit(body)
        receipts.append({'identity': pin, 'contents': body})
    require(set(bindings) == {str((SOURCE / name).resolve()) for name in FILES}, 'Ready receipts do not bind all exact sources')
    write('private-ui-monitor-freeze-intent.json', {'at_utc':datetime.now(timezone.utc).isoformat(),
        'source':str(SOURCE),'predecessor':OLD_HEAD,'exact_source_inputs':list(bindings.values()),
        'ready_receipts':receipts,'R0140_originals_retained':True,'live_evidence_pending':True,
        'movie_changed':False,'master_intake':False,'remote_operations':False})
    for index, argv in enumerate((['git','diff','--check'],['git','add','--',*FILES],
        ['git','diff','--cached','--check'],['git','commit','-m',
         'Fix original GUI owner admission and preserve actual knight observation threads'])):
        result = subprocess.run(argv, cwd=SOURCE, capture_output=True, text=True, encoding='utf-8')
        write(f'private-source-step-{index+1}.json', {'argv':argv,'returncode':result.returncode,
              'stdout':result.stdout,'stderr':result.stderr})
        require(result.returncode == 0, 'Private source freeze command failed')
    require(not git('status','--porcelain=v1'), 'Private committed source is dirty')
    write('private-source-commit.json', {'source_commit':git('rev-parse','HEAD'),'source':str(SOURCE),
        'branch':git('branch','--show-current'),'no_master_intake':True,'live_pending':True})
    print(git('rev-parse','HEAD'))

if __name__ == '__main__':
    main()
