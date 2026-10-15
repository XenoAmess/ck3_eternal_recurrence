from pathlib import Path
import copy,hashlib,json,tempfile
from unittest import mock
import pytest
from xar_autoplayer.bridge.army_query_history_store import ArmyQueryHistoryStore
from xar_autoplayer.bridge.army_query_history_reference import read_army_query_history_reference



def test_success_receipt_and_real_failed_budget_partial_are_distinct(tmp_path):
    # Dedicated temporary synthetic evidence only, peak <=8MiB and removed when
    # this new offline focus ends; existing live sidecars are never read/written.
    with tempfile.TemporaryDirectory(prefix='synthetic-',dir=tmp_path) as temporary:
        folder=Path(temporary);store=ArmyQueryHistoryStore(folder,2*1024*1024)
        full=dict(step='query-army-strengths-v1',accepted=True,status='completed',backend_id='native-headless',
            query_sequence=1,queried_snapshot_id='test:1',queried_revision=4,queried_native_revision=3,
            army_strengths_profile='observed_history_full_v1',army_strengths=[dict(army_id=18,status='available')])
        summary=store.record(full)
        actual,ref=read_army_query_history_reference(summary,evidence_dir=folder,maximum_bytes=2*1024*1024)
        assert actual==full and ref==summary['raw_result_reference']
        # The next real writer hits its finite quota after exactly one 1MiB
        # buffer. It leaves a named partial with no complete-result reference.
        huge={**full,'query_sequence':2,'synthetic_payload':'x'*(3*1024*1024)}
        failed=store.record(huge)
        assert failed['full_result_preserved'] is False and 'raw_result_reference' not in failed
        assert failed['unavailable_reason']=='sidecar_budget_exhausted'
        files=list(folder.iterdir());partials=[p for p in files if str(p.resolve())!=ref['path']]
        assert len(partials)==1 and partials[0].stat().st_size==1024*1024
        with mock.patch.object(Path,'open',side_effect=AssertionError('failed receipt must not open/glob files')):
            with pytest.raises(ValueError):read_army_query_history_reference(failed,evidence_dir=folder,maximum_bytes=2*1024*1024)
        # Even after a later failed partial exists, the exact earlier success is
        # read by receipt, without discovery heuristics or selecting newest.
        assert read_army_query_history_reference(summary,evidence_dir=folder,maximum_bytes=2*1024*1024)[0]==full
        mutations=[
            lambda x:x.update(full_result_preserved=False),
            lambda x:x['raw_result_reference'].update(bytes=True),
            lambda x:x['raw_result_reference'].update(bytes=1024*1024*3),
            lambda x:x['raw_result_reference'].update(sha256='0'*64),
            lambda x:x['raw_result_reference'].update(bytes=x['raw_result_reference']['bytes']+1),
            lambda x:x['raw_result_reference'].update(wire_bytes_preserved=True),
            lambda x:x['raw_result_reference'].update(path=str(partials[0])),
            lambda x:x.update(query_sequence=2),
            lambda x:x.update(queried_native_revision=99),
            lambda x:x.update(army_count=2),
        ]
        for mutation in mutations:
            bad=copy.deepcopy(summary);mutation(bad)
            with pytest.raises(ValueError):read_army_query_history_reference(bad,evidence_dir=folder,maximum_bytes=2*1024*1024)
