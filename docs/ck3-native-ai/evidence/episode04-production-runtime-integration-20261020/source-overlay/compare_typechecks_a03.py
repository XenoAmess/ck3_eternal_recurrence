"""Resolve both control and candidate against the same real mirror tools."""
import json
import os
import re
from pathlib import Path
import prepare_and_check_a01 as common

def main() -> None:
    root = common.LANE
    mirror = root / 'mirror'
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(common.LIB),
               MYPYPATH=str(mirror / 'tools'), TMP=str(root / 'scratch'),
               TEMP=str(root / 'scratch'), GIT_OPTIONAL_LOCKS='0')
    env.pop('XAR_PRODUCTION_SOURCE_TOOLS', None)
    env.pop('XAR_PARENT_ACTOR_SOURCE', None)
    results = {}
    for kind, path in [('baseline', root / 'baseline-test/test_ck3_mod_acceptance_parent_bundle.py'),
                       ('effective', mirror / 'tools/test_ck3_mod_acceptance_parent_bundle.py')]:
        results[kind] = common.run('mypy-equal-resolution-' + kind + '-a01',
            [str(common.PY), '-B', '-X', 'utf8', '-m', 'mypy', '--config-file', str(root / 'mypy.ini'),
             '--no-incremental', '--cache-dir', 'nul', '--follow-imports', 'skip', '--check-untyped-defs',
             '--python-version', '3.14', '--platform', 'win32', str(path)], env, mirror)
    def errors(result: dict) -> list[str]:
        lines = Path(result['stdout']['path']).read_text('utf-8-sig').splitlines()
        return [line[re.search(r':\d+: error:', line).start():]
                for line in lines if re.search(r':\d+: error:', line)]
    original, effective = errors(results['baseline']), errors(results['effective'])
    assert results['baseline']['returncode'] == results['effective']['returncode'] == 1
    assert original == effective and len(original) == 7
    canonical = json.loads((root / 'canonical-parent-test-a01/ORIGINAL-WAIT.actual.json').read_bytes())
    assert canonical['actual_original_popen_wait'] and canonical['returncode'] == 0
    assert not (mirror / 'tmp').exists() and not list((root / 'scratch').iterdir())
    assert not list(mirror.rglob('__pycache__'))
    result = common.record('CHECKS.actual-a03.json', {
        'schema': 'xar.e04.production-publish.overlay-checks.v3',
        'canonical_test_wait': str(root / 'canonical-parent-test-a01/ORIGINAL-WAIT.actual.json'),
        'canonical_methods': 8, 'canonical_test_pass': True,
        'typecheck_runs': results, 'MYPYPATH_both': str(mirror / 'tools'),
        'identical_flags_and_real_dependency_resolution': True,
        'baseline_diagnostics': original, 'effective_diagnostics': effective,
        'diagnostics_added': [], 'typecheck_exitcodes': [1, 1], 'single_file_clean': False,
        'prior_diagnostics_preserved': [
            'First wrapper asserted mypy0; actual7 retained.',
            'First baseline in isolated directory had same7 plus3 unresolved imports; assertion failure retained; paired rerun binds same mirror tools for both.'],
        'TMP_TEMP': str(root / 'scratch'), 'repository_tmp_absent_before_after': True,
        'scratch_clean_after': True, 'source_environment_overrides_removed': True,
        'unchanged_31_second_cases_rerun': False, 'D_W_Git_game_SDK_Steam_mutation': False})
    print(json.dumps({'status': 'CANONICAL8_PASS_MYPY7_BASELINE_UNCHANGED', 'checks': result,
                      'source_test_bytes': common.census(root), 'root_bytes': common.census(common.ROOT)}))

if __name__ == '__main__':
    main()
