"""Thin A02-to-A03 feeder composition; bounded reads and RAM outputs only.

The already timed A02 graph is the authority. Do not invoke the old timing
extractor: the A03 controls expose its reviewed timing entry as an alias.
"""
import argparse
import ast
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
OLD_DEADLINE = '2026-10-20T03:48:56.993837Z'
FEEDER = 'root_p37c23_same_game_loop_feeder100.py'
LEDGER = 'root_continuity_window_c23_100.py'
LAUNCHER = 'launch_c23_feeder100.py'
PINS = {
    FEEDER: (41718, '6147cbc020f4e4c44a6b991d54f3a73830dc1f7b39feba4a002933bb7d045913'),
    LEDGER: (34988, '6b0ece99075e425f84ad732e3112cf5ccdc883bbb09a884aa94e0df411e9ff6e'),
    LAUNCHER: (2451, 'e3105fec484e9f2f10e8f7e0b4e5f24db7f81142d86ee656553dab43a064add5'),
}
RUNTIME_CAP = 98304


def require(ok, message):
    if not ok:
        raise ValueError('A03 thin feeder denied: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_bytes(raw, pin, name):
    require(type(raw) is bytes and (len(raw), sha(raw)) == pin,
            'exact actual A02 preimage differs: ' + name)
    return raw


def read_source(path, pin):
    with Path(path).open('rb') as stream:
        raw = stream.read(pin[0] + 1)
    return checked_bytes(raw, pin, str(path))


def ref(path, raw):
    return {'path': str(Path(path).resolve()), 'bytes': len(raw), 'sha256': sha(raw)}


def validate_deadline(value):
    require(type(value) is str and 0 < len(value) <= 64, 'explicit finite UTC review required')
    try:
        at = datetime.fromisoformat(value.replace('Z', '+00:00'))
        old = datetime.fromisoformat(OLD_DEADLINE.replace('Z', '+00:00'))
        require(at.tzinfo is not None and at.utcoffset() == timedelta(0)
                and at > old and at > datetime.now(timezone.utc),
                'new unexpired UTC review must replace the historical deadline')
    except (TypeError, OverflowError) as error:
        raise ValueError('A03 thin feeder denied: invalid UTC review') from error
    return value


def change(text, old, new, changes):
    require(text.count(old) == 1 and old != new, 'one exact thin seam required: ' + old[:80])
    changes.append((old, new))
    return text.replace(old, new, 1)


def inverse(raw, changes, original):
    text = raw.decode('utf-8')
    for old, new in reversed(changes):
        require(text.count(new) == 1, 'ambiguous A03 inverse seam')
        text = text.replace(new, old, 1)
    require(text.encode('utf-8') == original, 'A02 whole-byte inverse differs')
    return text.encode('utf-8')


def function_asts(raw):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(raw).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def build_sources(*, review_deadline_utc, runtime_root=T):
    deadline = validate_deadline(review_deadline_utc)
    root = Path(runtime_root).resolve(strict=True)
    before = {name: read_source(root / name, pin) for name, pin in PINS.items()}
    text = before[FEEDER].decode('utf-8')
    changes = []
    text = change(text, 'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json',
                  'ROOT-FINAL-SDK-FREEZE-P37C23-A03.json', changes)
    text = change(text, OLD_DEADLINE, deadline, changes)
    text = change(text, 'from root_c23_source_abort_checkpoint_inputs import (',
                  'from root_c23_a03_source_abort_checkpoint_inputs import (', changes)
    graph = {**before, FEEDER: text.encode('utf-8')}
    for name, raw in graph.items():
        compile(raw, name, 'exec')
        restored = inverse(raw, changes if name == FEEDER else [], before[name])
        checked_bytes(restored, PINS[name], name)
    old_functions = function_asts(before[FEEDER])
    new_functions = function_asts(graph[FEEDER])
    require(set(old_functions) == set(new_functions), 'feeder function closure changed')
    require(all(value == new_functions[name] for name, value in old_functions.items()
                if name != 'admitted'), 'timing, first-FULL HOLD or ordinary algorithms changed')
    generated = sum(map(len, graph.values()))
    require(generated <= RUNTIME_CAP, 'single feeder materialization exceeds 96 KiB')
    report = {
        'schema': 'xar.C23-A03-thin-feeder-source-graph/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'review_deadline_utc': deadline, 'status': 'SOURCE_ONLY_NOT_INSTALLED',
        'source_bases': [ref(root / name, raw) for name, raw in before.items()],
        'generated': {name: {'bytes': len(raw), 'sha256': sha(raw)} for name, raw in graph.items()},
        'generated_bytes': generated, 'runtime_single_materialization_cap': RUNTIME_CAP,
        'whole_byte_inverse_pass': True, 'thin_seams': len(changes),
        'ledger_and_launcher_identical': True,
        'unchanged_feeder_function_ASTs': sorted(set(old_functions) - {'admitted'}),
        'timing_transform_reapplied': False, 'old_FuncDef_extractor_called': False,
        'five_actual_refs_required_at_runtime': True, 'RootFinal_contents_not_preclaimed': True,
        'first_batch_gate': 'same producer timed first FULL; validated receipt; zero-RPC Root HOLD',
        'new_helper_module': 'root_c23_a03_source_abort_checkpoint_inputs',
        'runtime_writes': 0, 'scratch_bytes': 0, 'Task_Game_SDK_Native_OBS_desktop_calls': 0,
        'ordinary_cycle_or_speed_credit': 0,
    }
    return graph, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-deadline-utc', required=True)
    args = parser.parse_args()
    _, report = build_sources(review_deadline_utc=args.review_deadline_utc)
    print(json.dumps(report, separators=(',', ':')))
