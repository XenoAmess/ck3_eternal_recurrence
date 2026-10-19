"""Create-only C3 view of the existing clean classifier installer (four paths)."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

SOURCE_SHA = '38dca9aac1fdb40a56ef3308fb8adb80e6d9c917c0d968b347e69b85a0d1cca6'
CHANGES = {
    'ROOT-P37-KNOWN-OWNER-LIFECYCLE-PIN.json': 'ROOT-P37C3-KNOWN-OWNER-LIFECYCLE-PIN.json',
    'ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37.json': 'ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37C3.json',
    'ROOT-FINAL-SDK-FREEZE-P37.json': 'ROOT-FINAL-SDK-FREEZE-P37C.json',
    'ROOT-ACTUAL-DRIVER-MODE-P37.json': 'ROOT-ACTUAL-DRIVER-MODE-P37C3.json',
}


def transform(raw):
    if len(raw) > 16384 or hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError('Exact original clean installer required')
    text = raw.decode('utf-8')
    for previous, current in CHANGES.items():
        if text.count(previous) != 1:
            raise ValueError('One occurrence of each expected path required')
        text = text.replace(previous, current)

    class Literals(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in CHANGES:
                node.value = CHANGES[node.value]
            return node

    if ast.dump(Literals().visit(ast.parse(raw))) != ast.dump(ast.parse(text)):
        raise AssertionError('A guard changed outside the four path literals')
    return text.encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    with source.open('rb') as stream:
        raw = stream.read(16385)
    candidate = transform(raw)
    args.output_root.mkdir(parents=True, exist_ok=False)
    path = args.output_root / 'root_p37_clean_classifier_install.py'
    with path.open('xb') as stream:
        stream.write(candidate)
    proof = {'schema': 'xar.c3-clean-classifier-install-four-literals/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'source': {'path': str(source), 'bytes': len(raw), 'sha256': SOURCE_SHA},
        'candidate': {'path': str(path.resolve()), 'bytes': len(candidate),
            'sha256': hashlib.sha256(candidate).hexdigest()},
        'changes': CHANGES, 'AST_except_four_path_literals_identical': True,
        'new_RPC_calls': 0, 'runtime_mutations': 0}
    with (args.output_root / 'QUALIFICATION.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(proof['candidate']))


if __name__ == '__main__':
    main()
