"""Pure offline model checks, never native/cold/game qualification."""
import copy
import unittest
from dispatch_contract import CALL_RVA,SOURCE_SHA,project

def fixture():
    base=0x140000000
    owner=dict(mode='native_campaign_owned_no_load_v2',episode_run_id=None,pid=321,
        process_create_time_100ns=123,game_state_identity_witness=0x10000,date_raw=100,absolute_day_raw=10)
    start=dict(kind='start',schema='xar.maintenance.dispatch_call.v1',mode='single_pre_call_execution_breakpoint',
        source_sha256=SOURCE_SHA,callsite_rva=CALL_RVA,maximum_records=1,DR7_execution_mask=1,
        owner_binding=owner,pid=321,created=123,module_base=base,module_size=102518784,job_is_payer=False)
    saved=[0,0,0,0,0,0]
    arm=dict(kind='arm',thread_id=7,thread_generation=1,success=True,saved_debug=saved,
        armed_debug=[base+CALL_RVA,0,0,0,0,1])
    trap=dict(kind='dispatch_call_pre_instruction',thread_id=7,thread_generation=1,RIP=base+CALL_RVA,
        RIP_rva=CALL_RVA,DR6=1,qpc=123,
        registers=dict(rbx=0x20000,rcx=0x30000,rax=0x40000,rdx=9,r8=10,r9=11,rsp=0x50000),
        reads=dict(job_plus38_first=0x30000,job_plus38_second=0x30000,dispatch_vptr_first=0x40000,
            dispatch_vptr_second=0x40000,vtable_plus10_first=base+0x1234,vtable_plus10_second=base+0x1234),
        first_read_complete=True,second_read_complete=True,target_same_image=True,target_rva=0x1234,
        source_anchor_matches=True,owner_identity_stable=True,
        clock=dict(read_complete=True,state_before=0x10000,state_after=0x10000,
            date_before=100,date_after=100,day_before=10,day_after=10),
        physical_dispatch_source_qualified=True,payer=None,calendar_producer=None,cadence=None,paid_maintenance_raw=None)
    restore=dict(kind='restore',thread_id=7,thread_generation=1,readback=True,debug=saved)
    terminal=dict(kind='terminal',restored=True,detached=True,pending_event=False,process_exited=False,
        cleanup_complete=True,observation_thread_admission_complete=True,capture_count=1,known_payer_or_cadence=False)
    return [start,arm,trap,restore,terminal],owner

class ContractChecks(unittest.TestCase):
    def test_full_model_only_source_input_no_business_credit(self):
        rows,owner=fixture();result=project(rows,owner)
        self.assertTrue(result['source_decode_target_candidate_available'])
        self.assertIsNone(result['payer']);self.assertFalse(result['binary_or_live_qualification_granted'])
    def test_task_cursor_is_not_dispatch_object(self):
        rows,owner=fixture();rows[2]['reads']['job_plus38_first']=99
        with self.assertRaises(ValueError):project(rows,owner)
    def test_unknown_target_retained_without_candidate(self):
        rows,owner=fixture();rows[2].update(first_read_complete=False,target_same_image=False,target_rva=None,physical_dispatch_source_qualified=False)
        self.assertFalse(project(rows,owner)['source_decode_target_candidate_available'])
    def test_foreign_target_not_made_thunk(self):
        rows,owner=fixture();rows[2]['reads'].update(vtable_plus10_first=0x123,vtable_plus10_second=0x123)
        rows[2].update(target_same_image=False,target_rva=None,physical_dispatch_source_qualified=False)
        self.assertFalse(project(rows,owner)['source_decode_target_candidate_available'])
    def test_missing_restore_and_pending_hold_withhold_source_ready(self):
        rows,owner=fixture();rows.pop(3);rows.insert(-1,dict(kind='unresolved_cleanup_hold'))
        rows[-1].update(restored=False,detached=False,pending_event=True,cleanup_complete=False)
        self.assertFalse(project(rows,owner)['cleanup_proved'])
    def test_old_tid_generation_rejected(self):
        rows,owner=fixture();rows[2]['thread_generation']=2
        with self.assertRaises(ValueError):project(rows,owner)
    def test_tid_reuse_uses_new_saved_state(self):
        rows,owner=fixture();old_arm=copy.deepcopy(rows[1]);rows.insert(2,dict(kind='thread_exited',thread_id=7,thread_generation=1))
        new_arm=copy.deepcopy(old_arm);new_arm['thread_generation']=2;rows.insert(3,new_arm)
        rows[4]['thread_generation']=2;rows[5]['thread_generation']=2
        self.assertTrue(project(rows,owner)['cleanup_proved'])
    def test_wrong_instruction_or_data_DR_rejected(self):
        for mutate in (lambda r:r[2].update(RIP=r[2]['RIP']+3),lambda r:r[1]['armed_debug'].__setitem__(5,0x99990055)):
            rows,owner=fixture();mutate(rows)
            with self.assertRaises(ValueError):project(rows,owner)
    def test_second_capture_and_business_relabel_refused(self):
        for kind in ('second','payer'):
            rows,owner=fixture()
            if kind=='second':rows.insert(3,copy.deepcopy(rows[2]))
            else:rows[2]['payer']=33388
            with self.assertRaises(ValueError):project(rows,owner)
    def test_clock_or_owner_relabel_refused(self):
        rows,owner=fixture();rows[2]['clock']['date_after']=124
        with self.assertRaises(ValueError):project(rows,owner)
        rows,owner=fixture();wrong=copy.deepcopy(owner);wrong['pid']=322
        with self.assertRaises(ValueError):project(rows,wrong)

if __name__=='__main__':unittest.main()
