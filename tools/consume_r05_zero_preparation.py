"""Read existing compact query/preview packets and run the R05 decision consumer."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ck3_autonomous_player/src'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--army-query', required=True, type=Path)
    parser.add_argument('--sites', required=True, type=Path)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--commands', type=Path)
    parser.add_argument('--wars', type=Path)
    parser.add_argument('--commander-query', action='append', type=Path, default=[])
    parser.add_argument('--army-id', action='append', type=int)
    parser.add_argument('--available-step', action='append', default=[])
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    from xar_autoplayer.strategy import plan_r05_zero_stock_preparation

    pins = []
    machines = []
    def read(path, fallback=None):
        if path is None:
            return fallback
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError('use the existing named compact packet; this consumer does not reopen large raw history')
        data = path.read_bytes()
        payload = json.loads(data.decode('utf-8-sig'))
        pins.append(dict(path=str(path.resolve()), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        if isinstance(payload, dict):
            machines.append(dict(path=str(path.resolve()), machine_id=payload.get('machine_id', 'unknown')))
        return payload
    query = read(args.army_query)
    sites = read(args.sites)
    snapshot = read(args.snapshot)
    commands = read(args.commands, [])
    wars = read(args.wars)
    commanders = [read(path) for path in args.commander_query]
    machine_tool = REPO / 'tools/ck3_live_run_id.py'
    machine = subprocess.run([sys.executable, '-B', str(machine_tool), 'machine'],
                             capture_output=True, text=True, check=True).stdout.strip()
    if any(value['machine_id'] not in {'unknown', machine} for value in machines):
        raise ValueError('source packet belongs to another machine')
    decision = plan_r05_zero_stock_preparation(
        army_query=query, sites=sites, snapshot=snapshot, commands=commands,
        active_wars=wars, commander_queries=commanders,
        available_steps=args.available_step or ['query-army-strengths-v1'],
        army_ids=tuple(args.army_id or [18, 93]))
    record = dict(machine_id=machine, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        scope='offline_existing_packet_R05_decision_consumer', source_pins=pins,
        source_machine_id_records=machines, decision=decision,
        SDK_calls=0, EXE_reads=0, game_actions_executed=0, new_live_evidence=False)
    encoded = json.dumps(record, ensure_ascii=False, indent=2) + '\n'
    if len(encoded.encode('utf-8')) > 1024 * 1024:
        raise ValueError('decision record exceeds one MiB within the two MiB work packet')
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        output.write(encoded)
    result = decision['r05_zero_stock_preparation_v1']
    print(json.dumps(dict(machine_id=machine, candidate_count=len(result['candidates']),
        selected=result['selected'], selected_step=decision['selected_step'],
        required_field_count=len(result['required_fields']), output=str(args.output)), ensure_ascii=False))


if __name__ == '__main__':
    main()
