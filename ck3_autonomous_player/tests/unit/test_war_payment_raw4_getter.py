"""New raw4 optional child checks: synthetic wire only, no native/live claim."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

REPO=Path(__file__).resolve().parents[3]
# Overlay only the two candidate Python modules, then use real production deps.
if not (REPO/'tools').is_dir():
    REPO=Path(os.environ.get('XAR_RAW4_REPO_ROOT',Path.cwd())).resolve()
if not (REPO/'tools').is_dir():raise RuntimeError('Set XAR_RAW4_REPO_ROOT to the explicit repository dependency root')
sys.path[:0]=[str(REPO/'ck3_autonomous_player/src'),str(REPO)]
from xar_autoplayer.bridge import war_payment_observations_v1 as legacy
from xar_autoplayer.bridge.version_identity import CK3_12004
CAND=Path(__file__).resolve().parents[2]/'src/xar_autoplayer/bridge'
if not CAND.exists():CAND=REPO/'ck3_autonomous_player/src/xar_autoplayer/bridge'
def module(name):
    spec=importlib.util.spec_from_file_location('xar_autoplayer.bridge.'+name,CAND/(name+'.py'))
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    setattr(sys.modules['xar_autoplayer.bridge'],name,m);return m
payment=module('war_payment_observations_v1');raw4=module('war_payment_raw4_getter_v1')
FIX=REPO/'ck3_autonomous_player/tests/unit/fixtures/war_payment_generic_context_12004_a04.json'
cases=json.loads(FIX.read_bytes())
BASE=next(r['value'].get(payment.JOURNAL_KEY,r['value']) for r in cases if r['case']=='positive')
def make():
    j=deepcopy(BASE);s=j['current_session'];a=dict(character_full_id=s['player_character_full_id'],character_magic=0x43686172,
        extension=0x50000,context=0x60000,physical_4a0_bits=(1<<64)-7,failed_reads=0)
    event=dict(clock_identity=55,sequence=10,thread_id=99)
    natural=deepcopy(j['records'][0]['natural_parent_metadata'])
    r=dict(journal_sequence=1,raw_selector=4,character=0x40000,out_pointer=0x70000,
        caller_return_absolute=0x140001234,module_base=0x140000000,caller_return_rva=0x1234,
        entry_event=event,returned_event=dict(event,sequence=11),session_entry=deepcopy(s),session_return=deepcopy(s),
        natural_parent_metadata=natural,natural_return_metadata=deepcopy(natural),before=a,after=deepcopy(a),
        out64_bits=(1<<64)-7,output_failed_reads=0,original_called=True,original_returned=True,raw_return_bits=0x70000)
    j[raw4.KEY]=dict(schema_version=1,source_entry_rva=raw4.ENTRY,capture_origin='native_entry_detour',
        resource_name='unknown',payment_attribution='unclosed',read_complete=True,latest_sequence=1,oldest_sequence=1,
        overwritten=0,publication_failures=0,records=[r])
    return j,r
def snapshot(j):
    s=j['current_session'];return dict(paused=True,map_ready=True,native_revision=s['snapshot_revision'],date_raw=s['native_date_raw']&0xffffffff,
        played_character=dict(character_id=s['player_character_full_id']),diagnostics=dict(bridge_pid=s['pid'],
        connection_generation=s['connection_generation'],hello=dict(expected_ck3_version=CK3_12004.game_version,
        expected_ck3_sha256=CK3_12004.executable_sha256)))
def normalized(j):return payment.normalize_journal(j,snapshot=snapshot(j),machine_id=j['machine_id'])

class Raw4Checks(unittest.TestCase):
    def test_connected_optional_child_and_signed_physical_read(self):
        j,r=make();n=normalized(j);self.assertEqual(n,j);self.assertIsNot(n,j)
        result=raw4.consume_raw4_getter_observations(j,snapshot=snapshot(j),machine_id=j['machine_id'])
        self.assertEqual(result['journal'],n)
        q=result['qualified_raw4_reads'];self.assertEqual(len(q),1);self.assertEqual(q[0]['out64_signed'],-7)
        self.assertEqual(q[0]['read_branch'],'physical_context_4a0')
        self.assertEqual(n['qualified_boarding_debits'],BASE['qualified_boarding_debits'])
        self.assertEqual(normalized(deepcopy(BASE)),BASE)
    def test_default_zero_is_not_physical_zero(self):
        j,r=make()
        for f in (r['before'],r['after']):f.update(context=0,physical_4a0_bits=None)
        r['out64_bits']=0;q=raw4.qualified_reads(normalized(j));self.assertEqual(len(q),1)
        self.assertEqual(q[0]['read_branch'],'default_zero_missing_extension_or_context')
        for f in (r['before'],r['after']):f.update(context=0x60000,physical_4a0_bits=0)
        q=raw4.qualified_reads(normalized(j));self.assertEqual(q[0]['read_branch'],'physical_context_4a0')
    def test_diagnostic_mismatches_preserved_without_read_qualification(self):
        for variant in ('return','changed_context','session','unreadable','external_pc','busy'):
            j,r=make()
            if variant=='return':r['raw_return_bits']^=8
            if variant=='changed_context':r['after']['context']+=8
            if variant=='session':r['session_return']['connection_generation']+=1
            if variant=='unreadable':r.update(out64_bits=None,output_failed_reads=1)
            if variant=='external_pc':r.update(caller_return_absolute=1,caller_return_rva=None)
            if variant=='busy':j['sampling'].update(busy=True,active_captures=1)
            n=normalized(j);self.assertEqual(n,j);self.assertEqual(raw4.qualified_reads(n),[],variant)
    def test_rejects_fabricated_selector_name_pointer_and_ring(self):
        for variant in ('selector','name','pc','field','count','clear'):
            j,r=make();v=j[raw4.KEY]
            if variant=='selector':r['raw_selector']=0
            if variant=='name':v['resource_name']='gold'
            if variant=='pc':r['caller_return_rva']=0x1235
            if variant=='field':r['paid']=True
            if variant=='count':v['latest_sequence']=2
            if variant=='clear':j['sampling'].update(capture_enabled=False,clear_completed=True,retained_records=0)
            with self.assertRaises(ValueError,msg=variant):normalized(j)
if __name__=='__main__':unittest.main()
