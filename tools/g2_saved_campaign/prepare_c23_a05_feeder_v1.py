"""A05 feeder bytes from the actual closed A04 graph; RAM outputs only.

The existing feeder already runs successive <=30-turn batches to the original
10950-day endpoint. Preserve its first-FULL HOLD, timing and ledger algorithms.
Source26 controls retain the helper module/API and verify its new anchor.
"""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

T04 = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime-a04')
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
MAIN = 'root_p37c23_same_game_loop_feeder100.py'
PINS = {
    MAIN: (41720, 'd8809157b5c4d5f3b4f413eaf3aab956de3ebce253cf36117beb6a589f0e9c13'),
    'root_continuity_window_c23_100.py': (34988, '6b0ece99075e425f84ad732e3112cf5ccdc883bbb09a884aa94e0df411e9ff6e'),
    'launch_c23_feeder100.py': (2451, 'e3105fec484e9f2f10e8f7e0b4e5f24db7f81142d86ee656553dab43a064add5'),
}
OLD = b'ROOT-FINAL-SDK-FREEZE-P37C23-A04.json'
NEW = b'ROOT-FINAL-SDK-FREEZE-P37C23-A05.json'
PRIOR = ('c23_a03_feeder_qualification_20261020.json', 3098,
         '05ab210a385b78e7ed2c0b116ca628c29586ac3eb18622d3ed25bd7c5d2582c5')


def require(ok, why):
    if not ok:
        raise ValueError('A05 thin feeder denied: ' + why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_exact(path, pin):
    with Path(path).open('rb') as stream:
        raw = stream.read(pin[0] + 1)
    require((len(raw), sha(raw)) == pin, 'actual source pin differs: ' + str(path))
    return raw


def bind_main(raw):
    require((len(raw), sha(raw)) == PINS[MAIN], 'actual A04 main required')
    require(raw.count(OLD) == 1 and NEW not in raw, 'one A04-to-A05 final seam required')
    result = raw.replace(OLD, NEW, 1)
    require(result.replace(NEW, OLD, 1) == raw, 'whole-byte A04 inverse differs')
    def functions(value):
        return [ast.dump(n, include_attributes=False) for n in ast.parse(value).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    require(functions(result) == functions(raw), 'original feeder algorithms changed')
    require(b'2026-10-20T06:30:00+00:00' in result
        and b'from root_c23_a03_source_abort_checkpoint_inputs import (' in result,
        'original deadline and Source26-controls helper alias required')
    return result


def build_sources(*, source_runtime=T04):
    root = Path(source_runtime).resolve(strict=True)
    before = {name: read_exact(root / name, pin) for name, pin in PINS.items()}
    graph = {**before, MAIN: bind_main(before[MAIN])}
    for name, raw in graph.items():
        compile(raw, name, 'exec')
    prior = Path(__file__).resolve().with_name(PRIOR[0])
    read_exact(prior, PRIOR[1:])
    return graph, {
        'schema': 'xar.C23-A05-thin-feeder-source/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'RAM_ONLY_NOT_INSTALLED', 'target_runtime': str(root.with_name('runtime-a05')),
        'generated': {n: {'bytes': len(b), 'sha256': sha(b)} for n, b in graph.items()},
        'generated_bytes': sum(map(len, graph.values())), 'runtime_cap_bytes': 98304,
        'exact_inverse': True, 'all_function_ASTs_unchanged': True,
        'first_FULL_zero_RPC_HOLD_preserved': True, 'no_100_cycle_stop_added': True,
        'original_target_date_raw': 53407128, 'original_target_days': 10950,
        'review_deadline_utc': '2026-10-20T06:30:00+00:00',
        'previous_qualification': {'path': str(prior), 'bytes': PRIOR[1], 'sha256': PRIOR[2]},
        'previous_four_tests_rerun': False, 'Source26_anchor_validation_owner': 'A05 controls',
        'runtime_writes': 0, 'Task_Game_SDK_Native_OBS_desktop_calls': 0,
    }


if __name__ == '__main__':
    print(json.dumps(build_sources()[1], separators=(',', ':')))
