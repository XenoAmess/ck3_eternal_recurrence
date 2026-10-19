"""Emit the paired P51 callback/publisher fix; never modify a running session."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path


def pin(path):
    data = path.read_bytes()
    if len(data) > 131072:
        raise ValueError('Bounded producer source only')
    return {'path': str(path.resolve()), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def transform_feed(source):
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'publish_before_submit']
    if len(functions) != 1:
        raise ValueError('Exact actual callback producer required')
    function = functions[0]
    starts = [node for node in function.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'payload' for target in node.targets)]
    if len(starts) != 1 or "if output.exists(): raise FileExistsError('this decision was already published; no action replay')" not in source:
        raise ValueError('Exact old single-slot publication tail required')
    lines = source.splitlines(True)
    replacement = [
        '    from root_decision_text_api import load_api, started_reference\n',
        '    api=load_api(N)\n',
        '    api.publish_callback_observation(row,started_reference(N,api),actual_observation=observation)\n',
        '    return None\n',
    ]
    result = ''.join(lines[:starts[0].lineno - 1] + replacement + lines[function.end_lineno:])
    ast.parse(result)
    return result


def emit(runtime, output, machine_id):
    runtime, output = runtime.resolve(strict=True), output.resolve()
    if output.exists() or output == runtime or output.is_relative_to(runtime):
        raise ValueError('New independent source review directory required')
    publisher = Path(__file__).with_name('decision_text_publisher.py')
    old_publisher = runtime / 'presentation/g2_saved_campaign/decision_text_publisher.py'
    old_feed = runtime / 'root_p37_compact_decision_feed.py'
    if 'def publish_callback_observation(' not in publisher.read_text(encoding='utf-8'):
        raise ValueError('The paired publisher source does not support actual subdecisions')
    values = {'root_p37_compact_decision_feed.py': transform_feed(old_feed.read_text(encoding='utf-8-sig')).encode(),
              'presentation/g2_saved_campaign/decision_text_publisher.py': publisher.read_bytes()}
    inputs = [pin(old_feed), pin(old_publisher), pin(publisher)]
    output.mkdir(); files = []; diffs = []
    for relative, data in values.items():
        ast.parse(data, filename=relative)
        target = output / relative; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        files.append(pin(target) | {'relative_path': relative})
        old = (runtime / relative).read_text(encoding='utf-8-sig')
        diffs.extend(difflib.unified_diff(old.splitlines(True), data.decode().splitlines(True),
                     fromfile='input/' + relative, tofile='review/' + relative))
    (output / 'changes.diff').write_text(''.join(diffs), encoding='utf-8')
    record = {'schema': 'xar.p51-subdecisions-source-review/v1', 'machine_id': machine_id,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'SOURCE_ONLY_FUTURE_PAIRED_ADOPTION',
        'inputs': inputs, 'files': files, 'AST_checks': len(files), 'runtime_mutations': 0,
        'Game_OBS_Desktop_Native_calls': 0, 'source_process_launches': 0,
        'scope': 'Actual per-parent callback ordinal and observation fingerprint; same-decision guard retained. Existing stage ordering, pending-input ACK gate and view are unchanged.',
        'adoption': ['Never copy over the frozen live publisher source or restart the current session for this review.',
                     'At a normal future publisher/recording lifecycle adopt both producer and publisher, freeze new source pins and obtain a new actual publisher STARTED binding.',
                     'Do not replay historical143 or reinterpret its partial result. Same-parent callback files and ACKs remain immutable.',
                     'A source fixture is not live Game/OBS/before-submit business qualification.']}
    (output / 'REVIEW.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--machine-id', required=True)
    args = parser.parse_args()
    result = emit(args.runtime, args.output, args.machine_id)
    print(json.dumps({'status': result['status'], 'files': len(result['files']), 'output': str(args.output)}))
