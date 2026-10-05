"""Run the single new 291E210 emitter case with explicit -B -O checks."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import traceback


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, required=True)
    arguments = parser.parse_args()
    output = arguments.artifacts.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    test = root/'ck3_autonomous_player/tests/test_battle_context_preparation_291e210_12003.py'
    result: dict[str, object] = {'status':'HARNESS RED', 'unique_new_cases':1,
                                'old_tests_run':0, 'public_emitter_invocations':0}
    try:
        if not sys.dont_write_bytecode or sys.flags.optimize != 1:
            raise RuntimeError('Focused runner requires Python -B -O')
        sys.path.insert(0, str(root/'ck3_autonomous_player/src'))
        spec = importlib.util.spec_from_file_location('native_291e210_focused_case', test)
        if spec is None or spec.loader is None:
            raise RuntimeError('Focused case loader unavailable')
        fixture = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = fixture
        spec.loader.exec_module(fixture)
        result['status'] = 'CAPABILITY RED'
        result['public_emitter_invocations'] = 1
        result.update(fixture.run_focused_case(output))
    except Exception as error:
        result['error'] = repr(error)
        (output/'ERROR.txt').write_text(traceback.format_exc(), encoding='utf-8', newline='\n')
    result.update(python=sys.executable, optimized=sys.flags.optimize,
                  bytecode_disabled=sys.dont_write_bytecode)
    (output/'RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',
                                    encoding='utf-8', newline='\n')
    print(json.dumps({'status':result['status'], 'checks':result.get('explicit_check_count'),
                      'result':str(output/'RESULT.json'), 'error':result.get('error')}))
    return 0 if result['status'] == 'FIRST GREEN' else 1


if __name__ == '__main__':
    raise SystemExit(main())
