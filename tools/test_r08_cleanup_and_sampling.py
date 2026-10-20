"""Source helper behavior; real normalizers, simulated owned queue, no native calls."""
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,importlib.util,json,sys,unittest
p=argparse.ArgumentParser(add_help=False)
p.add_argument('--repo',type=Path)
p.add_argument('--actor-path',type=Path)
opts,rest=p.parse_known_args();sys.argv=[sys.argv[0],*rest]
repo=(opts.repo or Path(__file__).resolve().parents[1]).resolve()
sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
import ck3_mod_acceptance_cases
name='ck3_mod_acceptance_cases.r08_writer_one_day'
spec=importlib.util.spec_from_file_location(name,opts.actor_path or repo/'tools/ck3_mod_acceptance_cases/r08_writer_one_day.py')
actor=importlib.util.module_from_spec(spec);sys.modules[name]=actor;spec.loader.exec_module(actor)
from xar_autoplayer.bridge.army_observer_research_sampling_control import FAMILIES,STATE_KEY

# Literal actual R0222 pre-arm leaf; source pin recorded by the audit index.
# This is independent retained data, not obtained from candidate implementation.
IDLE=json.loads('''{"state":"idle","generation":0,"starting_date_raw":0,"target_date_raw":0,
"last_observed_date_raw":0,"trigger_date_raw":0,"speed":0,"mode":"decision_epoch",
"army_count":0,"combat_count":0,"completed_daily_ticks":0,"intermediate_pause_count":0,
"trigger_flags":0,"trigger_reasons":[],"signed_date_delta_from_target_raw":0,
"overshoot_days":-1,"pause_wrapper_called":false,"pause_observed":false,
"terminal_observed":false,"abnormal":false}''')

def row(on=False,busy=False):
    return dict(installed=True,available=True,capture_enabled=on,busy=busy,
        clear_completed=not on and not busy,epoch=1,active_captures=int(busy),
        retained_records=0,qualified_records=0,status='enabled' if on else 'busy' if busy else 'disabled',
        readiness='inflight' if on and busy else 'awaiting_sample' if on else 'off')

class Queue:
    def __init__(self,*,clock_bad=False,unknown_enable=False,busy=False,payment_available=True):
        self.calls=[];self.payment_calls=[];self.clock_bad=clock_bad
        self.natural=False;self.unknown_enable=unknown_enable;self.busy=busy
        self.payment_available=payment_available
    def snapshot(self,label):return dict(revision=3,date_raw=100,paused=True,map_ready=True)
    def call(self,label,tool,args):
        self.calls.append((tool,copy.deepcopy(args)))
        if tool=='ck3_execute_step':
            if args['step']=='pause-map':return {'accepted':True}
            if args['step']=='research-query-tactical-daily-sentinel-v1':
                return {'tactical_daily_sentinel':{**IDLE,**({'generation':True} if self.clock_bad else {})}}
            raise AssertionError('Unexpected clock action: '+repr(args))
        if tool=='ck3_save_checkpoint':return {'checkpoint':{'status':'saved','date_raw':100}}
        if tool not in ('ck3_set_army_observer_research_sampling_v1','ck3_query_army_observer_research_sampling_v1'):
            raise AssertionError('Unexpected queue tool '+tool)
        setting='enabled' in args
        if setting and args['enabled'] is True:
            if self.unknown_enable:raise TimeoutError('recorded unknown enable, no automatic replay')
            self.natural=True
        if setting and args['enabled'] is False:self.natural=False
        families=FAMILIES if args['observer_family']=='all' else (args['observer_family'],)
        on=self.natural if args['observer_family']=='natural_phase' else False
        step=('enable' if args.get('enabled') else 'disable') if setting else 'query'
        return dict(step=step+'-army-observer-research-sampling-v1',accepted=True,status='completed',
            backend_id='native-headless',**{STATE_KEY:{x:row(on,self.busy if on else False) for x in families}})
    def payment(self,label,mode):
        self.payment_calls.append(mode)
        return {'sampling':dict(available=self.payment_available,capture_enabled=False,busy=False,clear_completed=True,active_captures=0,retained_records=0)}

class CleanupAndSampling(unittest.TestCase):
    def test_actual_idle0_only_before_observer_claim_and_typed_mutations_refuse(self):
        self.assertEqual(actor.normalize_cleanup_clock(copy.deepcopy(IDLE),observer_claimed=False),IDLE)
        with self.assertRaises(ValueError):actor.normalize_cleanup_clock(IDLE,observer_claimed=True)
        for change in ({'generation':True},{'generation':1},{'starting_date_raw':1},{'overshoot_days':0},{'mode':'terminal_or_sentinel'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                actor.normalize_cleanup_clock({**IDLE,**change},observer_claimed=False)
    def test_real_cleanup_idle0_proceeds_to_independent_offs_then_one_save(self):
        q=Queue();gate=SimpleNamespace(restored=True,off_clear=False)
        result,errors,days=actor.cleanup_writer_window(q.call,q.snapshot,q.payment,gate,
            observer_claimed=False,expected_start_date_raw=100)
        self.assertEqual(errors,[]);self.assertTrue(result['Save']);self.assertTrue(gate.off_clear)
        self.assertEqual(q.payment_calls,['disable','query']);self.assertEqual(days,0)
        self.assertEqual([tool for tool,args in q.calls].count('ck3_save_checkpoint'),1)
        controls=[(tool,args) for tool,args in q.calls if args.get('observer_family')=='all']
        self.assertEqual(len(controls),2);self.assertFalse(controls[0][1]['enabled'])
        self.assertNotIn('enabled',controls[1][1])
    def test_bad_clock_still_attempts_both_off_paths_but_never_save_or_close(self):
        q=Queue(clock_bad=True);gate=SimpleNamespace(restored=True,off_clear=False)
        result,errors,days=actor.cleanup_writer_window(q.call,q.snapshot,q.payment,gate,
            observer_claimed=False,expected_start_date_raw=100)
        self.assertTrue(errors);self.assertFalse(result['Save']);self.assertFalse(gate.off_clear)
        self.assertEqual(q.payment_calls,['disable','query'])
        self.assertEqual(sum(args.get('observer_family')=='all' for tool,args in q.calls),2)
        self.assertFalse(any(tool=='ck3_save_checkpoint' for tool,args in q.calls));self.assertIsNone(days)
    def test_unavailable_empty_payment_is_not_qualified_offclear(self):
        q=Queue(payment_available=False);gate=SimpleNamespace(restored=True,off_clear=False)
        result,errors,days=actor.cleanup_writer_window(q.call,q.snapshot,q.payment,gate,
            observer_claimed=False,expected_start_date_raw=100)
        self.assertTrue(errors);self.assertFalse(result['OFFclear']);self.assertFalse(result['Save'])
        self.assertTrue(result['army_families_OFFclear']);self.assertFalse(gate.off_clear)
        self.assertFalse(any(tool=='ck3_save_checkpoint' for tool,args in q.calls))
    def test_natural_phase_enable_once_and_independent_read_before_payment_prerequisite(self):
        q=Queue();state=actor.prepare_natural_phase(q.call,q.snapshot,enable_once_authorized=True)
        self.assertTrue(state['capture_enabled']);self.assertFalse(state['busy'])
        self.assertEqual([tool for tool,args in q.calls],['ck3_query_army_observer_research_sampling_v1',
            'ck3_set_army_observer_research_sampling_v1','ck3_query_army_observer_research_sampling_v1'])
        self.assertEqual(q.calls[1][1],{'observer_family':'natural_phase','expected_revision':3,'enabled':True})
    def test_natural_phase_missing_authority_unknown_enable_or_busy_never_fakes_ready(self):
        q=Queue()
        with self.assertRaises(ValueError):actor.prepare_natural_phase(q.call,q.snapshot,enable_once_authorized=False)
        self.assertEqual(len(q.calls),1)
        q=Queue(unknown_enable=True)
        with self.assertRaises(TimeoutError):actor.prepare_natural_phase(q.call,q.snapshot,enable_once_authorized=True)
        self.assertEqual(sum(args.get('enabled') is True for tool,args in q.calls),1)
        self.assertEqual(len(q.calls),2)
        q=Queue(busy=True)
        with self.assertRaises(ValueError):actor.prepare_natural_phase(q.call,q.snapshot,enable_once_authorized=True)
        self.assertEqual(sum(args.get('enabled') is True for tool,args in q.calls),1)

if __name__=='__main__':unittest.main()
