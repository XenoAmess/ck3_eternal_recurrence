"""Only new A phase wiring; synthetic transport, no process/game/SDK probe."""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import importlib.util, json, sys, tempfile, unittest

HERE=Path(__file__).resolve().parent
import r10_compare as c
import strategy_a as a
import strategy_a_route_inputs as ri
from test_r10_compare import Fixture
import strategy_a_stages as phases
h=phases.load_module(HERE/'sources/locked_routes_root_1463.frozen.py','existing_relay_for_new_A_tests')
Live=phases.make_live_class(h,c,a,ri)


class WiringTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.f=Fixture(self.root);self.e=c.Evidence(self.root)
        self.arm=self.f.results['arms'][0]
        for ep in (self.f.plan['baseline'],self.arm['cold_start'],*self.arm['observations']):
            ep['snapshot']=self.f.edit(ep['snapshot'],lambda x:x['body']['player_armies'][0].update(controllable=True))
        self.f.plan['strategies']['A']['route_preview']=self.preview(self.f.plan['baseline'])
        self.preview_pin=self.preview(self.arm['cold_start'])
        self.initial=a.admit(self.f.plan,self.arm['runtime'],'c'*64,self.arm['cold_start'],self.preview_pin,self.e)
        self.live=Live.__new__(Live);v=self.live
        v.plan=self.f.plan;v.runtime=self.arm['runtime'];v.e=self.e;v.case=self.root/'case';v.case.mkdir()
        v.attempt=v.case/'try1';v.attempt.mkdir();v.machine='synthetic-A';v.serial=0
        v.binding={'army_id':1};v.meta={'machine_id':'synthetic-A','case':'R10-A','stage':'synthetic-only'}
        v.args=SimpleNamespace(loaded_save_sha256='c'*64,days=30,attempt='try1')
        v.run=self.root/'run';(v.run/'requests').mkdir(parents=True);(v.run/'responses').mkdir()

    def preview(self,ep):
        s=c.body(self.e.json(ep['snapshot']))
        return self.f.put('synthetic-preview',{'accepted':True,'status':'available','step':'preview-move-army-1-to-30',
            'route_preview':{'status':'available','army_id':1,'origin_province_id':10,'target_province_id':30,
                             'route_province_ids':[30],'previewed_date_raw':1000},
            **{'queried_'+k:s[k] for k in ('snapshot_id','revision','native_revision','episode_run_id')},
            'queried_connection_generation':1})

    def moving(self):
        post=deepcopy(self.arm['cold_start'])
        def edit(x):
            s=x['body'];s.update(snapshot_id='A:post',revision=11,native_revision=10,speed=5)
            s['player_armies'][0].update(army_state='moving',route_province_ids=[30],route_read_status='complete_nonempty',move_target_province_id=30)
        post['snapshot']=self.f.edit(post['snapshot'],edit)
        post['army_result']=self.f.edit(post['army_result'],lambda x:x.update(queried_snapshot_id='A:post',queried_revision=11,queried_native_revision=10))
        return a.observe_move(self.initial,post,self.e)

    def test_baseline_is_readonly_and_uses_actual_A_admission(self):
        v=self.live;v.endpoint=lambda _:self.arm['cold_start'];v.fresh_preview=lambda _:self.preview_pin
        v.action=lambda *x:self.fail('baseline must not submit Move')
        out=v.baseline()
        self.assertFalse(out['Move_submitted'])
        state=h.load(out['state']['path'])
        self.assertIsNone(state['move_postcondition']);self.assertEqual(state['days'],[])
        self.assertEqual(out['decision']['proposed_call']['tool'],'ck3_move_army')

    def test_exact_day_wires_a0_speed5_full_DATA_to_A_update(self):
        v=self.live;s=self.moving();before=s['move_postcondition'];after=self.arm['observations'][0]
        v.endpoint=lambda name:after if name.startswith('post-status') else before
        stopped=c.body(self.e.json(after['snapshot']));v.snap=lambda *x,**k:(stopped,{})
        calls=[]
        def request(name,tool,args):
            calls.append((tool,deepcopy(args)));v.serial+=1
            body={'accepted':True}
            if name=='arm-one-date-day':body['tactical_daily_sentinel']={'state':'armed','generation':1}
            if name=='date-only-status':body=self.e.json(self.arm['days'][0]['clock_source'])
            envelope={'machine_id':'synthetic-A','body':body,'is_error':False}
            path=h.write_new(self.root/f'new-A-phase-response-{v.serial}.json',envelope)
            return envelope,{},h.pin(path)
        # Fixture source wraps the clock directly; expose the existing status key.
        def wrapped(name,tool,args):
            row,rp,sp=request(name,tool,args)
            if name=='date-only-status':
                row['body']={'tactical_daily_sentinel':row['body']['clock']}
                path=h.write_new(self.root/'new-A-actual-shaped-status.json',row);sp=h.pin(path)
            return row,rp,sp
        v.request=wrapped
        out=v.exact_day(s)
        self.assertEqual(len(out['days']),1);self.assertEqual(out['actual']['cohort_current'],100)
        self.assertEqual(calls,[('ck3_execute_step',{'step':'research-arm-tactical-daily-sentinel-v1-1000-to-1024-speed-5-mode-terminal-a-0','expected_revision':11}),
            ('ck3_execute_step',{'step':'resume-map','expected_revision':None}),
            ('ck3_execute_step',{'step':'research-query-tactical-daily-sentinel-v1','expected_revision':None})])

    def test_unknown_Move_keeps_global_claim_across_new_attempt(self):
        v=self.live;v.state=lambda:self.initial;v.endpoint=lambda _:self.arm['cold_start'];v.fresh_preview=lambda _:self.preview_pin
        calls=[]
        def pending(*args):calls.append(args);raise TimeoutError('same original response remains pending')
        v.request=pending
        with self.assertRaises(TimeoutError):v.move_once()
        self.assertTrue((v.case/'initial-move.once.claim.json').is_file())
        v.args.attempt='try2';v.attempt=v.case/'try2';v.attempt.mkdir()
        with self.assertRaises(FileExistsError):v.move_once()
        self.assertEqual(len(calls),1)

    def test_advance_stops_on_first_observed_arrival(self):
        v=self.live;s=self.moving();v.state=lambda:s
        after=deepcopy(s);after['first_arrival_day']=1;after['last_not_arrived_day']=0
        after['days']=[self.arm['days'][0]];after['actual']=deepcopy(s['actual']);after['actual']['day']=1
        after['arrival_actual']=deepcopy(after['actual']);count=[]
        v.exact_day=lambda state:(count.append(1) or after)
        result=v.advance()
        self.assertEqual(count,[1]);self.assertEqual(result['report']['first_arrival_day'],1)
        self.assertFalse(result['Move_submitted'])

    def test_common_args_file_binds_independent_phase_and_public_zero(self):
        fields=['--'+x+'\nSYNTHETIC_ONLY\n' for x in ('repo','relay-source','consumer-root','consumer-manifest',
            'plan','runtime','features-binding','evidence-root','context','request-helper','relay-sha256',
            'request-helper-sha256','loaded-save-sha256','case-id','deadline-utc')]
        path=self.root/'common.SYNTHETIC.args';path.write_text(''.join(fields)+'--army-id\n0\n--native-carmy-id\n77\n',encoding='utf-8')
        parsed=phases.parser().parse_args(['advance','@'+str(path),'--attempt','separate-stage','--days','1','--state','EXPLICIT_STATE'])
        self.assertEqual((parsed.stage,parsed.army_id,parsed.native_carmy_id,parsed.days),('advance',0,77,1))
        self.assertEqual(str(parsed.state),'EXPLICIT_STATE')


if __name__=='__main__':unittest.main()
