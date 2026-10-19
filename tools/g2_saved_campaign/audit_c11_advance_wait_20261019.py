"""Recheck the frozen C11 source audit; no Game, profile, original trace or writes."""
from pathlib import Path
import hashlib
import json

REPO=Path(__file__).resolve().parents[2]
REPORT=REPO/'docs/ck3-native-ai/evidence/c11-exact-day-wait-source-audit01.json'


def checked(pin,path=None):
    path=Path(path or pin['path'])
    raw=path.read_bytes()
    assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],str(path)
    return raw


def main():
    data=json.loads(REPORT.read_bytes())
    roots={k:Path(v) for k,v in data['roots'].items()}
    source=lambda p:roots[p['root']]/p['relative'] if 'root' in p else Path(p['path'])
    ledger=json.loads(checked(data['timing_inputs'][0],REPO/data['timing_inputs'][0]['path']))
    owner=json.loads(checked(data['timing_inputs'][1],REPO/data['timing_inputs'][1]['path']))
    assert ledger['machine_id']==owner['machine_id']==data['machine_id']
    byseq={row[0]:row for row in ledger['advance_rows']}
    col={name:i for i,name in enumerate(owner['columns'])}
    owners={(row[0],row[1]):row for row in owner['rows']}
    totals=[0.,0.,0.,0.]
    for expected in data['phase_difference_rows']:
        seq=expected[0]; row=byseq[seq]; obs=row[-1]
        delta=[(obs[i+1][0]-obs[i][0])/1e9 for i in range(4)]
        assert row[6]==expected[1]==1 and all(abs(a-b)<1e-9 for a,b in zip(delta,expected[2:6]))
        epoch=lambda phase:owners[seq,phase][col['owner_pump_epochs']]
        assert epoch('first_date_seen')-epoch('resume_observed')==expected[6]
        totals=[a+b for a,b in zip(totals,delta)]
    for key,total in zip(('begin_to_running','running_to_first_date','first_date_to_paused','paused_to_final'),totals):
        assert abs(total-data['phase_difference_totals_s'][key])<1e-9
    inventory=data['C11_identity']['SDK_inventory']
    freeze=json.loads(checked(inventory,source(inventory)))
    for pin in data['actual_SDK_source_pins']:
        checked(pin,source(pin))
        entry=next(e for e in freeze['files'] if e.get('relative')==pin['relative'])
        assert entry['sha256']==pin['sha256'] and entry['bytes']==pin['bytes']
    checked(data['stock_speed_source'])
    chain=data['native_source_chain']
    for name,pin in chain.items():
        checked(pin,source(pin))
        if 'compile_receipt' in pin:
            receipt=roots['R26']/pin['compile_receipt'].split('R26/',1)[1]
            raw=receipt.read_bytes(); assert hashlib.sha256(raw).hexdigest()==pin['compile_receipt_sha256']
            assert json.loads(raw)['source']['sha256']==pin['sha256']
    sentinel=data['Native29_watch_boundary']['sentinel_source']; checked(sentinel,source(sentinel))
    rsp=(roots['R29']/'build/native29-link.rsp').read_text(encoding='utf-8-sig').splitlines()
    assert rsp[190].replace('\\','/').lower()==data['Native29_watch_boundary']['retained_direct_object']['path'].lower()
    assert REPORT.stat().st_size+Path(__file__).stat().st_size<=data['storage']['repo_package_limit_bytes']
    print(json.dumps({'status':'PASS_SOURCE_PINS_AND_PHASE_ARITHMETIC','phase_totals_s':totals,'files':2,'logical_bytes':REPORT.stat().st_size+Path(__file__).stat().st_size,'Game_RPC_build_calls':0}))


if __name__=='__main__':
    main()
