"""Verify small historical records; no game, process or deployment qualification."""
import argparse
import hashlib
import json
from pathlib import Path

INDEX = 'docs/ck3-native-ai/evidence/episode04-r218-worker-admission-failures-12004/source-index.json'


def check_records(root, records):
    root = Path(root).resolve()
    for record in records:
        path = (root / record['repo_path']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Record escaped repository root')
        data = path.read_bytes()
        if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Historical record pin mismatch: ' + record['repo_path'])
        if path.suffix == '.json':
            json.loads(data.decode('utf-8-sig'))
    return len(records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    index = json.loads((args.repo_root / INDEX).read_text(encoding='utf-8-sig'))
    count = check_records(args.repo_root, index['records'])
    print(json.dumps({'record_integrity_passed': True, 'records': count,
                      'machine_id': 'unknown',
                      'scope': 'Portable historical bytes only; observer machine not established, no runtime qualification.'}))


if __name__ == '__main__':
    main()
