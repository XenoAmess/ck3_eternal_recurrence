"""Copy an explicit map of completed JSON sources into a new append-only directory."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-map', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--collect', action='store_true')
    args = parser.parse_args()
    if not args.collect:
        print(json.dumps({'status': 'PLAN_ONLY', 'source_reads': False, 'writes': False, 'Game_SDK_UI_process_bus_raw_calls': False}))
        return 0
    if args.input_map is None or args.output is None:
        raise ValueError('explicit input-map and new output required')
    mapping = json.loads(args.input_map.read_bytes())
    if mapping['schema'] != 'ck3.e04.C.completed-json-collection-map.v1' or args.output.exists():
        raise ValueError('known schema and never-used output required')
    files = mapping['files']
    names = [item['relative'] for item in files]
    if len(names) != len(set(names)) or not files:
        raise ValueError('unique nonempty file list required')
    for item in files:
        relative = Path(item['relative'])
        if relative.is_absolute() or '..' in relative.parts or ':' in item['relative'] or relative.suffix != '.json':
            raise ValueError('unsafe/non-JSON target')
        if item.get('completed') is not True or not 0 < item['bytes'] <= 262144:
            raise ValueError('explicit completed small source required')
    args.output.mkdir(parents=True, exist_ok=False)
    copied = []
    for item in files:
        source = Path(item['source'])
        if source.suffix != '.json' or source.stat().st_size != item['bytes']:
            raise ValueError('source extension/size mismatch; partial output is preserved')
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('source hash mismatch; partial output is preserved')
        json.loads(raw)
        target = args.output / item['relative']
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        copied.append({'path': item['relative'], 'bytes': len(raw), 'sha256': item['sha256']})
    with (args.output / 'collected-inputs.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps({'schema': 'ck3.e04.C.collected-completed-json.v1', 'files': copied, 'not_terminal_or_comparison_credit': True}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'COPIED_COMPLETED_JSON_BYTES_ONLY', 'files': len(copied), 'terminal_or_comparison_credit': False}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(json.dumps({'status': 'FAILED_COLLECTION_PARTIAL_PRESERVED', 'error': str(error)}))
        raise SystemExit(1)
