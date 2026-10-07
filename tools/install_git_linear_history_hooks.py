"""Root-operated local hook installer. Default is read-only planning."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def git(repo, *args, optional=False):
    r = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, encoding='utf-8')
    if r.returncode and not optional:
        raise ValueError(r.stderr.strip())
    return r.stdout.strip()


def quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', required=True, type=Path)
    ap.add_argument('--guard-script', type=Path)
    ap.add_argument('--execute', action='store_true')
    a = ap.parse_args()
    repo = a.repo.resolve()
    guard = (a.guard_script or repo / 'tools/check_git_linear_history.py').resolve()
    if not guard.is_file():
        raise ValueError('Adopt the reviewed guard source first, or pass its explicit candidate path.')
    common = Path(git(repo, 'rev-parse', '--git-common-dir'))
    common = common if common.is_absolute() else repo / common
    target = common.resolve() / 'linear-history-hooks-v1'
    configured = git(repo, 'config', '--get', 'core.hooksPath', optional=True)
    if configured:
        raise ValueError('Existing core.hooksPath must be reviewed/composed rather than overwritten: ' + configured)
    default_hooks = common.resolve() / 'hooks'
    if any((default_hooks / name).exists() for name in ['pre-merge-commit', 'pre-commit', 'pre-push']):
        raise ValueError('Existing active hooks must be reviewed/composed; this installer does not replace them.')
    if target.exists():
        raise ValueError('Target exists; preserve it and review before installing again.')
    hooks = {}
    for name in ['pre-merge-commit', 'pre-commit', 'pre-push']:
        hooks[name] = '#!/bin/sh\nexec ' + quote(Path(sys.executable).as_posix()) + ' ' + quote(guard.as_posix()) + ' --' + name + '\n'
    result = {'repo': repo.as_posix(), 'guard': guard.as_posix(), 'hooks_path': target.as_posix(),
              'hooks': list(hooks), 'executed': a.execute}
    if a.execute:
        target.mkdir()
        for name, body in hooks.items():
            p = target / name
            p.write_text(body, encoding='utf-8', newline='\n')
            p.chmod(0o755)
        git(repo, 'config', '--local', 'core.hooksPath', target.as_posix())
        result['actual_config_readback'] = git(repo, 'config', '--local', '--get', 'core.hooksPath')
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
