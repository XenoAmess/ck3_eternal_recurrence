"""Detached exact d804 cold-bind qualification; no Game/process/SAVE body I/O.

Uses only a pinned closed small projection. Original Driver methods execute
with synthetic history; file signature/hash, persistence and OS lineage hook
are explicitly mocked. No actual restore/sidecar token is awarded.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import threading
from unittest.mock import patch

DRIVER_SHA = "db9f8fb05483146abe1bea7c00d5ec4c53e5fc6a9c370133ba7e8ff7ebedb3da"
PROJECTION_SHA = "a0b050138486f458f5e4e6963389fc09fcdcf443c8f8abfd630d116d0e791495"

def pin(p):
    data=p.read_bytes()
    return dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def run(source_root, projection):
    driver_path=source_root/'xar_autoplayer/bridge/native_driver.py'
    assert pin(driver_path)['sha256']==DRIVER_SHA
    assert pin(projection)['sha256']==PROJECTION_SHA
    small=json.loads(projection.read_bytes())
    assert small['closed_source_only'] is True
    fields=small['fields']
    checkpoint=fields['last_checkpoint']['value']
    goal=fields['campaign_goal']['value']
    assert checkpoint['history_index']==2056 and checkpoint['date_raw']==53202384
    assert small['history_rows_from_existing_post_close']==2078
    assert small['succession_expectation']['binding']['value']['date_raw']==53202696
    assert 'date_raw' not in json.dumps(goal)
    sys.path.insert(0,str(source_root))
    nd=importlib.import_module('xar_autoplayer.bridge.native_driver')
    lineage=importlib.import_module('xar_autoplayer.successor_ui_checkpoint_lineage_v1')
    assert Path(nd.__file__).resolve()==driver_path.resolve()
    actor,episode=checkpoint['episode_character_id'],checkpoint['episode_run_id']
    history=[dict(index=i+1,command='query-fixture-readonly',ok=True,
                  result={'fixture':True}) for i in range(2078)]
    history[2055]=dict(index=2056,command='save-checkpoint',ok=True,
                       result={'checkpoint':copy.deepcopy(checkpoint)})
    # The exact count and original bytes come from the sealed small projection;
    # these substitute rows do not purport to reproduce14actual feeder events.
    candidate=dict(format_version=nd._NATIVE_DRIVER_STATE_VERSION,
        bridge_pid=fields['bridge_pid']['value'],episode_character_id=actor,
        episode_run_id=episode,last_checkpoint=copy.deepcopy(checkpoint),
        command_history=history,campaign_goal=copy.deepcopy(goal),
        succession_expectation={'binding':copy.deepcopy(
            small['succession_expectation']['binding']['value'])},
        rollback_war_failures=[],rollback_war_failures_migration_required=False)
    original=copy.deepcopy(candidate)
    rows=[]
    def fixture(case,*,date=None,current=None,sha=None,signature=True):
        d=object.__new__(nd.NativeHeadlessGameplayDriver)
        d._driver_state_lock=threading.RLock()
        d._pending_cold_candidate=copy.deepcopy(candidate)
        d.save_dir=Path('offline-fixture-no-save-directory')
        d._session_bridge_pid=999991 # Synthetic replacement, never observed PID.
        d._command_history=[]
        d._succession_expectation=copy.deepcopy(candidate['succession_expectation'])
        d._succession_reconciliation={'fixture_future':True}
        d._campaign_goal=None
        d._managed_restore_transaction=None
        d._driver_state_error=None
        d._succession_lifecycle=copy.deepcopy(checkpoint['succession_lifecycle'])
        d._bind_new_episode_from_seed_snapshot=lambda *a,**kw:False
        d._checkpoint_path=lambda:Path('offline-fixture-no-save.ck3')
        persisted=[]
        d._persist_driver_state=lambda **kw:persisted.append(kw)
        observed=[]
        snapshot=dict(map_ready=True,paused=True,date_raw=date or checkpoint['date_raw'],
            played_character={'character_id':current or actor,'alive':True})
        with patch.object(nd,'_checkpoint_signature',return_value=(checkpoint['size'],0) if signature else None),\
             patch.object(nd,'_sha256_file',return_value=sha or checkpoint['sha256']),\
             patch.object(lineage,'capture_native_cold_projection_v1',
                 side_effect=lambda *a,**kw:observed.append(copy.deepcopy(kw['snapshot'])) or {'synthetic_projection':True}):
            assert d._cold_candidate_ready(candidate) is True
            d._bind_episode_from_playable_snapshot(snapshot,current_character_id=current or actor)
        assert candidate==original # Old raw history/estate/goal is never mutated.
        assert d._succession_expectation is None and d._succession_reconciliation is None
        if case=='accepted':
            assert d._driver_state_restore_kind=='cold_checkpoint'
            assert d._driver_state_restored is True and d._cold_candidate_rejection is None
            assert d._campaign_goal==goal and d._episode_run_id==episode
            assert len(d._command_history)==2057
            assert d._command_history[:2056]==history[:2056]
            assert d._command_history[-1]['result']['restored_date_raw']==checkpoint['date_raw']
            assert len(observed)==1
        else:
            assert d._driver_state_restore_kind=='new_episode' and d._driver_state_restored is False
            assert d._cold_candidate_rejection==case and d._campaign_goal is None
            assert not observed
        assert len(persisted)==1
        rows.append(dict(case=case,status='PASS',restored=d._driver_state_restored,
            current_history_rows=len(d._command_history),old_input_rows=len(candidate['command_history']),
            expectation=None,reconciliation=None,sidecar_hook='synthetic only'))
    fixture('accepted')
    fixture('checkpoint_date_mismatch',date=53202696)
    fixture('played_character_mismatch',current=actor+1)
    fixture('checkpoint_sha256_mismatch',sha='b'*64)
    fixture('checkpoint_size_mismatch',signature=False)
    d=object.__new__(nd.NativeHeadlessGameplayDriver)
    d.save_dir=Path('offline-fixture-no-save-directory')
    invalid=copy.deepcopy(candidate);invalid['last_checkpoint']['history_index']=2079
    assert not d._cold_candidate_ready(invalid)
    rows.append(dict(case='history_index_gt_length',status='PASS'))
    return dict(schema='xar.c15-cold-estate-exact-method-qualification.v1',
        status='SIX_DETACHED_CASES_PASS_NO_PRODUCTION_CHANGE',
        observed_at_utc=datetime.now(timezone.utc).isoformat(),
        machine_id=subprocess.check_output(['py','-B',str(Path(__file__).resolve().parents[2]/'tools/ck3_live_run_id.py'),'machine'],text=True).strip(),
        exact_driver=pin(driver_path),closed_projection=pin(projection),producer=pin(Path(__file__).resolve()),
        cases=rows,source_gap_for_actual_case=False,
        conclusion='Existing actual d804 cold path clears late estate before ordinary root. Goal is semantic prior succession intent, no date2432. Cold accepts exact checkpoint only; no date/actor/hash guard relaxation. Preserve original C14 raw2078rows; new current history is checkpoint prefix+proven restore lineage, never future query/clock facts.',
        limitations='Synthetic history substitutes actual rows; signature/hash/persist/OS lineage explicitly mocked. Does not prove real SAVE bytes, cold Game loading, actual lineage capsule or C15 continuation. Runtime/harness own those readbacks.',
        operations=dict(Game_RPC=0,process_reads=0,SAVE_body_reads=0,active_Driver_reads=0,
            old_closed_Driver_body_reads=0,shared_source_edits=0),
        actual_adoption=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--projection',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.source_root,args.projection)
    with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,separators=(',',':'));f.write('\n')
    print(json.dumps(pin(args.output)))
