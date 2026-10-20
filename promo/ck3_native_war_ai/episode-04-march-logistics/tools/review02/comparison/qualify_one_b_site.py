"""Read-only single-site wrapper around the adjacent B stock-growth validator.

A first actual site can be retained before a second site or a formal A/B/C plan
exists. Source truth, native deployment and live readiness remain separate.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[6]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=REPO,
                        help='Optional compatibility argument; must be this checkout.')
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--site-input', type=Path, required=True)
    parser.add_argument('--site-input-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.repo.resolve() != REPO:
        raise ValueError('single-site CLI uses the consumers in its own checkout')
    root = args.evidence_root.resolve()
    site = args.site_input.resolve()
    if not site.is_relative_to(root):
        raise ValueError('site input outside evidence root')
    if site.stat().st_size > 1048576:
        raise ValueError('site input exceeds 1MiB')
    raw = site.read_bytes()
    if digest(raw) != args.site_input_sha256:
        raise ValueError('site input SHA mismatch')
    sys.path[:0] = [str(HERE), str(REPO / 'ck3_autonomous_player/src')]
    import r10_compare as comparison
    import strategy_b
    import strategy_b_site_growth

    ref = {'path': site.relative_to(root).as_posix(),
           'bytes': len(raw), 'sha256': digest(raw)}
    result = strategy_b_site_growth.qualify_site(
        comparison.Evidence(root), ref, strategy_b)
    machine = subprocess.run(
        [sys.executable, str(REPO / 'tools/ck3_live_run_id.py'), 'machine'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True,
    ).stdout.strip()
    record = {
        'schema': 'xar.e04.B-one-rest-site-qualified.v1',
        'review_machine_id': machine,
        'reviewed_at_utc': datetime.datetime.now(datetime.UTC).isoformat(),
        'site': result,
        'two_sites_qualified': False,
        'formal_ABC_completed_arms': 0,
        'B_live_readiness_granted': False,
        'source_truth_or_native_deployment_granted': False,
    }
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({
        'output': str(args.output), 'province_id': result['province_id'],
        'actual_stock_delta_raw': result['actual_stock_delta_raw'],
        'two_sites_qualified': False,
    }))


if __name__ == '__main__':
    main()
