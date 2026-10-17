from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
MACHINE = 'desktop-3fevhd2-1c74096080'
HEAD = 'dc031358981450ae3f8e40c6234b7f27fd4662ef'

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def main() -> int:
    index = json.loads((HERE / 'source-index.json').read_text(encoding='utf-8'))
    require(index['schema'] == 'xar.e04.post-r197-native-portable-index.v1', 'schema')
    require(index['machine_id'] == MACHINE and index['source_head'] == HEAD, 'identity')
    archive = HERE / index['archive']['path']
    raw_archive = archive.read_bytes()
    require(len(raw_archive) == index['archive']['bytes'] and sha(raw_archive) == index['archive']['sha256'], 'archive pin')
    names = [r['member'] for r in index['members']]
    require(len(names) == len(set(names)) == 20, 'membership')
    with ZipFile(archive) as z:
        require(set(z.namelist()) == set(names), 'archive members')
        for row in index['members']:
            raw = z.read(row['member'])
            require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], row['member'])
        q = json.loads(z.read(index['qualification_member']))
        c = json.loads(z.read(index['build_completion_member']))
        require(q['machine_id'] == c['machine_id'] == MACHINE, 'qualification machine')
        require(all(q[k] == c[k] == HEAD for k in ('source_head','runtime_source_head','native_build_source_head')), 'qualification source')
        require(q['status'] == index['qualification_status'] == 'PRODUCTION_BYTES_ADMISSION_AND_SHARED_V3_COLD_VERIFIED', 'qualification status')
        require(q['build_completion']['sha256'] == sha(z.read('build-completion.json')), 'completion binding')
        require([r['label'] for r in q['fixture_results']] == ['military-reinforcement-admission','shared-v3-normal'], 'fixtures')
        require(all(r['exit_code'] == 0 for r in q['fixture_results']), 'fixture outcomes')
        require(q['fixture_results'][0]['result'] == q['prior_admission_reused_from_A04'], 'reused admission binding')
        require(q['focused_case_count'] == 2 and q['old_matrices_reexecuted'] is False, 'focused scope')
        for key in ('live_runtime_qualified','gameplay_result_qualified','capture_qualified','actual_toggle_qualified','natural_refill_ADD_qualified','R04_county_loss_positive'):
            require(q[key] is False, f'unsupported credit {key}')
        require(q['main_production']['SYSTEM_actual_receipt'] == index['system_receipts']['main_not_included'], 'main SYSTEM original pin')
        require(q['cold_production']['SYSTEM_actual_receipt'] == index['system_receipts']['cold_original'], 'cold SYSTEM original pin')
        require(sha(z.read(index['system_receipts']['cold_compressed_member'])) == q['cold_production']['SYSTEM_actual_receipt']['sha256'], 'cold SYSTEM archive pin')
    print('PASS: 20 exact originals; source/machine/completion/admission reuse/cold SYSTEM and live-boundary contracts')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f'FAIL: {e}', file=sys.stderr)
        sys.exit(1)
