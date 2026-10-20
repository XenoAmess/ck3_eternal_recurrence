"""Keep the real stronger typecheck RED and compare the unchanged test control."""
import json
import os
import re
from pathlib import Path
import prepare_and_check_a01 as common

def main() -> None:
    root = common.LANE
    mirror = root / 'mirror'
    delivery = json.loads((common.SRC / 'DELIVERY.actual-a02.json').read_bytes())
    old = next(row for row in delivery['copy_to_canonical_repo']
               if row['repo_path'] == 'tools/test_ck3_mod_acceptance_parent_bundle.py')
    control = common.put(root / 'baseline-test' / 'test_ck3_mod_acceptance_parent_bundle.py',
                         common.load_checked(old))
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(common.LIB),
               TMP=str(root / 'scratch'), TEMP=str(root / 'scratch'), GIT_OPTIONAL_LOCKS='0')
    env.pop('XAR_PRODUCTION_SOURCE_TOOLS', None)
    env.pop('XAR_PARENT_ACTOR_SOURCE', None)
    baseline = common.run('test-baseline-mypy-a01', [str(common.PY), '-B', '-X', 'utf8',
        '-m', 'mypy', '--config-file', str(root / 'mypy.ini'), '--no-incremental',
        '--cache-dir', 'nul', '--follow-imports', 'skip', '--check-untyped-defs',
        '--python-version', '3.14', '--platform', 'win32', control['path']], env, mirror)
    changed = json.loads((root / 'test-overlay-mypy-a01/ORIGINAL-WAIT.actual.json').read_bytes())
    canonical = json.loads((root / 'canonical-parent-test-a01/ORIGINAL-WAIT.actual.json').read_bytes())
    def diagnostics(path: str) -> list[str]:
        lines = Path(path).read_text('utf-8-sig').splitlines()
        return [line[line.index(':', re.search(r':\d+:', line).start()):]
                for line in lines if re.search(r':\d+: error:', line)]
    original_errors = diagnostics(baseline['stdout']['path'])
    effective_errors = diagnostics(changed['stdout']['path'])
    assert baseline['returncode'] == changed['returncode'] == 1
    assert original_errors == effective_errors and len(original_errors) == 7
    assert canonical['actual_original_popen_wait'] and canonical['returncode'] == 0
    assert not (mirror / 'tmp').exists() and not list((root / 'scratch').iterdir())
    assert not list(mirror.rglob('__pycache__'))
    result = common.record('CHECKS.actual-a02.json', {
        'schema': 'xar.e04.production-publish.overlay-checks.v2',
        'canonical_test_wait': {
            'path': str(root / 'canonical-parent-test-a01/ORIGINAL-WAIT.actual.json'),
            'returncode': 0, 'actual_original_popen_wait': True,
            'methods': 8, 'duration_seconds_from_unittest': 0.859},
        'mypy_effective_wait': str(root / 'test-overlay-mypy-a01/ORIGINAL-WAIT.actual.json'),
        'mypy_baseline': baseline, 'mypy_baseline_source': control,
        'typecheck_flags_identical': True, 'baseline_diagnostics': original_errors,
        'effective_diagnostics': effective_errors, 'diagnostics_added': [],
        'mypy_exitcodes': [1, 1], 'single_file_typecheck_clean': False,
        'prior_wrapper_failure': 'prepare_and_check_a01 asserted changed-file mypy0; actual wait1 retained; comparison corrects classification without overwriting it.',
        'canonical_test_real_existing_mirrored_file_and_tools': True,
        'environment_source_overrides_removed': ['XAR_PRODUCTION_SOURCE_TOOLS', 'XAR_PARENT_ACTOR_SOURCE'],
        'TMP_TEMP': str(root / 'scratch'), 'repository_tmp_absent_before_after': True,
        'scratch_clean_after': True, 'unchanged_31_second_cases_rerun': False,
        'D_W_Git_game_SDK_Steam_mutation': False})
    print(json.dumps({'status': 'CANONICAL8_PASS_TYPECHECK7_BASELINE_UNCHANGED',
        'checks': result, 'source_test_bytes': common.census(root),
        'root_bytes': common.census(common.ROOT)}))

if __name__ == '__main__':
    main()
