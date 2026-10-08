"""Focused source-only checks for new common adapter/allocation seams."""
from __future__ import annotations
import argparse,ast,contextlib,copy,hashlib,importlib.util,io,json,re,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_allocate as allocation
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import xqol_adapter as qol
from ck3_mod_acceptance_cases import xqol_ui
import ck3_mod_acceptance_prepare as prep
# Resolve checked-in inputs from the imported entry, including an external review candidate.
HERE=Path(entry.__file__).resolve().parent
REPO=HERE.parent

class Focused(unittest.TestCase):
    def test_saved_flag_matches_actual_shared_validator(self):
        # Execute only these checked-in pure functions; importing the host would
        # load unrelated MCP/runtime dependencies and never belongs in this test.
        host=REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
        tree=ast.parse(host.read_text(encoding='utf-8-sig'))
        names={'validate_saved_campaign_options','saved_campaign_expected',
               'load_plan','allocated_managed_campaign_run_binding'}
        functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        self.assertEqual({n.name for n in functions},names)
        namespace={'argparse':argparse,'re':re,'json':json,'Path':Path,
                   'hashlib':hashlib,'__file__':str(host)}
        exec(compile(ast.Module(body=functions,type_ignores=[]),str(host),'exec'),namespace)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);run=root/'live/synthetic-R0001';run.mkdir(parents=True)
            state=root/'prepared/state';state.mkdir(parents=True)
            plan=root/'readonly.json'
            prep.write_json(plan,{'steps':[{'tool':'ck3_take_snapshot'}]})
            selected=object.__new__(entry.Selection)
            selected.manifest={'host':{},'source_root':{},'source_index':{},'native_source_index':{},'native':{'dll':{},'injector':{}}}
            selected.shared_file=lambda row,label=None:host if label=='host' else root/'shared-input'
            selected.manifest_path_key=lambda *a:root/'shared-source'
            selected.locations={'python':Path(sys.executable),'game_dir':root/'game'}
            selected.case_path=lambda value:Path(value)
            selected.values={'run_id':run.name};selected.run_dir=run;selected.context={};selected.blockers=[]
            selected.case={'startup':{'mode':'saved_campaign','state_dir':str(state),
                'saved_campaign':{'save':str(root/'original.ck3'),'bytes':1,'sha256':'1'*64,
                    'player_id':1,'date_raw':1,'product_inventory':str(root/'inventory.json')}},
                'initial_plan':str(plan),'budgets':{'command_timeout':300,'readiness_timeout':900,
                    'timeout':4800,'poll_interval':.05,'hold_seconds':3600}}
            actual_argv=selected.build_argv()
            self.assertEqual(actual_argv.count('--fixture-profile'),1)
            self.assertNotIn('--frontend-robert-bootstrap',actual_argv)
            self.assertEqual(selected.blockers,[])
            option=lambda flag:actual_argv[actual_argv.index(flag)+1]
            args=SimpleNamespace(saved_campaign_server=False,server=False,
                saved_campaign_save=Path(option('--saved-campaign-save')),
                saved_campaign_save_bytes=int(option('--saved-campaign-save-bytes')),
                saved_campaign_save_sha256=option('--saved-campaign-save-sha256'),
                saved_campaign_player_id=int(option('--saved-campaign-player-id')),
                saved_campaign_date_raw=int(option('--saved-campaign-date-raw')),
                saved_campaign_product_inventory=Path(option('--saved-campaign-product-inventory')),
                fixture_profile='--fixture-profile' in actual_argv,plan=Path(option('--plan')),
                state_dir=Path(option('--state-dir')),output=Path(option('--output')),
                bridge_pipe=option('--bridge-pipe'),agent_source_root=Path(option('--agent-source-root')),
                sdk_smoke_test=False,sdk_error_smoke_test=False,fixture_server=False,
                frontend_robert_bootstrap=False,frontend_fixture_start_policy=None,frontend_rules_plan=None,
                frontend_rules_diagnostic=False,frontend_rules_diagnostic_new_game=False,frontend_diagnostic_only=False,
                allow_verified_direct_bookmarks=False,cold_start_checkpoint=False,turns=0,
                native_fixture_inbox=None,print_default_plan=False)
            namespace['validate_saved_campaign_options'](args)
            args.fixture_profile=False
            with self.assertRaises(SystemExit):namespace['validate_saved_campaign_options'](args)
            args.fixture_profile=True
            prep.write_json(root/'mutating.json',{'steps':[{'tool':'ck3_execute_step','args':{'step':'pause-map'}}]})
            args.plan=root/'mutating.json'
            with self.assertRaises(SystemExit):namespace['validate_saved_campaign_options'](args)
            args.plan=plan
            # The actual allocated output is authoritative; preparation stays
            # outside the run directory, as in the unified public allocator.
            frozen={'run_id':run.name,'state_dir':str(state),'argv':actual_argv}
            prep.write_json(run/'frozen-argv.json',frozen)
            args.saved_campaign_server=True
            binding=namespace['allocated_managed_campaign_run_binding'](args)
            self.assertEqual(binding['run_id'],run.name)
            self.assertEqual(Path(binding['state_dir']),state.resolve())
            wrong=copy.copy(args);wrong.state_dir=root/'another/state'
            with self.assertRaises(ValueError):namespace['allocated_managed_campaign_run_binding'](wrong)
            wrong=copy.copy(args);wrong.output=run/'different-report.json'
            with self.assertRaises(ValueError):namespace['allocated_managed_campaign_run_binding'](wrong)
            wrong=copy.copy(args);wrong.bridge_pipe=args.bridge_pipe+'-different'
            with self.assertRaises(ValueError):namespace['allocated_managed_campaign_run_binding'](wrong)

    def test_original_business_parsers_and_plans(self):
        raw=entry.read_json(HERE/'ck3_mod_acceptance_cases/xqol_original_plans.json')
        self.assertEqual([len(raw[k]['steps']) for k in ('initial','d0','final6','readonly9')],[2,4,6,9])
        produced={step['id'] for key in ('initial','d0','final6','readonly9') for step in raw[key]['steps']}
        produced.add('qol-defense-song-ui-map')
        def refs(value):
            if isinstance(value,dict):
                if '$ref' in value:
                    self.assertIn(value['$ref'].split('.')[1],produced)
                for v in value.values():refs(v)
            elif isinstance(value,list):
                for v in value:refs(v)
        refs(raw)
        self.assertEqual(raw['startup_contract']['post_start'],{'government_key':'steppe_admin_government','primary_title_tier_key':'empire','independent':True})
        # Framed synthetic identities exercise the real parsers, including a
        # distinct Steppe actor and rejection of duplicate/failing scope proof.
        def scope(markers,alias,actor,historical):
            return ('\n'.join([markers['begin'],
                f'[00:00:00][D][effectimpl.cpp:1]: Synthetic (Internal ID: {actor} - Historical ID {historical})',
                'Saved event targets:',
                f'{alias}: Synthetic (Internal ID: {actor} - Historical ID {historical})',
                markers['pass'],markers['end']])+'\n').encode()
        song=scope(qol.SONG_MARKERS,'xqol_startup_actor',10,'han_8052')
        steppe=scope(qol.STEPPE_MARKERS,'xqol_steppe_startup_actor',20,'194333')
        proof=qol.scope_proof(song+steppe)
        self.assertEqual([proof[k]['runtime_character_id'] for k in ('song','steppe')],[10,20])
        self.assertFalse(proof['song']['root_scope_used'])
        self.assertFalse(proof['steppe']['root_scope_used'])
        for malformed in (song+song+steppe,song+steppe+qol.STEPPE_MARKERS['fail'].encode(),
                          song+steppe.replace(b'Internal ID: 20',b'Internal ID: 21',1)):
            with self.assertRaises(ValueError):qol.scope_proof(malformed)
        # This inventory is entirely temporary SYNTHETIC_ONLY data, not a copy
        # of game output or a dependency on any workstation's private history.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);snapshot=root/'beforelaunch'
            payloads={name:b'SYNTHETIC_ONLY configuration\n' for name in prep.CONFIG_NAMES}
            payloads.update({'mod/fixture.mod':b'name="Synthetic fixture"\npath="original-fixture"\n',
                'mod/product.mod':b'name="Synthetic product"\npath="original-product"\n',
                'dlc_load.json':b'{"enabled_mods":["mod/product.mod","mod/fixture.mod"]}\n'})
            payloads.update({'mod-content/product/descriptor.mod':b'name="Synthetic product"\n',
                             'mod-content/fixture/descriptor.mod':b'name="Synthetic fixture"\n'})
            payloads.update({f'mod-content/product/synthetic-{i:02}.txt':f'product synthetic {i}\n'.encode() for i in range(26)})
            payloads.update({f'mod-content/fixture/synthetic-{i:02}.txt':f'fixture synthetic {i}\n'.encode() for i in range(12)})
            before={'schema':'ck3-mod-acceptance-beforelaunch-profile-v1','snapshot_kind':'before-launch',
                'snapshot_root':str(snapshot),'source_run_id':'SYNTHETIC_ONLY','files':{}}
            for relative,payload in payloads.items():
                path=snapshot/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
                before['files'][relative]={k:v for k,v in prep.pin(path).items() if k!='path'}
            self.assertEqual(len(before['files']),47)
            self.assertEqual(sum(p.startswith('mod-content/product/') for p in before['files']),27)
            inventory=root/'inventory.json';prep.write_json(inventory,before)
            context={'state_dir':str(root/'fresh/state'),'output':str(root/'prepared'),
                     'case_contract':raw['startup_contract']}
            # Only game metadata acquisition is mocked; the copy, byte checks,
            # path rewrite, receipts and closed-seven policy writer are real.
            with patch.object(prep,'_engine',return_value=(None,{'game_version':'SYNTHETIC_ONLY'})):
                restored=prep.restore_prepared_profile(context,inventory)
            profile=Path(restored['profile'])
            self.assertEqual(set(restored['files']),set(payloads))
            for relative,payload in payloads.items():
                actual=(profile/relative).read_bytes()
                if relative in ('mod/fixture.mod','mod/product.mod'):
                    target=profile/'mod-content'/Path(relative).stem
                    self.assertIn(b'path="'+target.as_posix().encode()+b'"',actual)
                    self.assertEqual(re.sub(rb'^path\s*=.*$',b'path="original"',actual,flags=re.MULTILINE),
                                     re.sub(rb'^path\s*=.*$',b'path="original"',payload,flags=re.MULTILINE))
                else:self.assertEqual(actual,payload)
            receipt=entry.read_json(Path(restored['preparation']['path']))
            self.assertEqual(receipt['provenance']['byte_exact_count'],45)
            self.assertEqual(set(receipt['provenance']['changed_outer_paths']),{'mod/fixture.mod','mod/product.mod'})
            policy=entry.read_json(Path(restored['fixture_start_policy']['path']))
            self.assertEqual(set(policy),{'schema','schema_version','preparation','profile_input_sha256',
                'post_start','required_log_markers','forbidden_log_markers'})
            self.assertEqual(policy['post_start'],raw['startup_contract']['post_start'])
            with self.assertRaises(ValueError):prep.restore_prepared_profile(context,inventory)
            for index,mutation in enumerate(('played','escape','corrupt')):
                wrong=copy.deepcopy(before)
                if mutation=='played':wrong['snapshot_kind']='after-game'
                elif mutation=='escape':wrong['files']={'../escape':next(iter(before['files'].values()))}
                else:wrong['files']['pdx_settings.txt']['sha256']='0'*64
                bad=root/(mutation+'.json');prep.write_json(bad,wrong)
                bad_context={**context,'state_dir':str(root/f'rejected-{index}/state')}
                with self.assertRaises(ValueError):prep.restore_prepared_profile(bad_context,bad)

    def test_scope_startup_handler_positive_and_owner_negative(self):
        # The original scope parser itself is independently preserved by AST.
        # Exercise the new shared-hook DTO seam with its actual strict fields.
        snapshot={'played_character':{'character_id':20,'alive':True,'source':'native'},'native_revision':7,'date_raw':24,
            'active_event':{'source':'native','instance_id':1,'option_count':1,'options':[{'enabled':True,'option_number':1,'index':0}]}}
        context={'status':'available','current_event_window_context_ready':True,'current_event_window_context':{
            'schema':'current-event-window-context-v1','schema_version':1,'status':'available','window_match_count':1,
            'current_event_instance_id':1,'snapshot_revision':7,'date_raw':24,
            'root_scope':{'typed_identity':{'status':'available','kind':'character','character_id':20}},
            'options':[{'rendered_index':0,'native_option_index':0,'shown':True,'enabled':True,'fallback':False,'cancel':False}]}}
        proof={'song':{'runtime_character_id':10},'steppe':{'runtime_character_id':20}}
        with patch.object(qol,'scope_proof',return_value=proof),patch.object(Path,'read_bytes',return_value=b'original-log'):
            answer=qol.admit_startup_event({'state_dir':'state'},snapshot,context)
            self.assertEqual(set(answer),{'event_instance_id','option_number','proof','business_pass'})
            self.assertIs(answer['business_pass'],False)
            wrong=copy.deepcopy(context);wrong['current_event_window_context']['root_scope']['typed_identity']['character_id']=21
            with self.assertRaises(ValueError):qol.admit_startup_event({'state_dir':'state'},snapshot,wrong)
            wrong=copy.deepcopy(snapshot);wrong['active_event']['instance_id']=2
            with self.assertRaises(ValueError):qol.admit_startup_event({'state_dir':'state'},wrong,context)

    def test_day_requires_full_paused_frame_and_no_replay(self):
        frame={'played_character':{'character_id':20},'diagnostics':{'bridge_pid':2,'connection_generation':3},
               'date_raw':24,'source':'injected-dll-named-pipe','backend_id':'native-headless','paused':True}
        after=copy.deepcopy(frame);after['date_raw']=48
        client=SimpleNamespace(validate_frame=lambda f:f)
        row={'ok':True,'finished_at':'actual','error':None,'result':{'requested_days':1,'requested_interval_complete':True,
             'event_boundary':None,'elapsed_hours':24,'before':frame,'after':after}}
        self.assertEqual(qol.verify_day(row,client,frame),after)
        wrong=copy.deepcopy(row);wrong['result']['elapsed_hours']=23
        with self.assertRaises(ValueError):qol.verify_day(wrong,client,frame)
        wrong=copy.deepcopy(row);wrong['error']='submitted failure';wrong['ok']=False
        with self.assertRaises(ValueError):qol.verify_day(wrong,client,frame)

    def test_predecessor_requires_actual_closed_native_and_cas(self):
        report={'finished_at':'actual','managed_session_thread_finished':True,'cleanup_ok':True,
            'session':{'report':{'finished_at':'actual','shutdown':{'ok':True,'cleanup_proven':True,'tree_gone':True,
             'job_active_processes_final':0,'contract_errors':[],'final_ck3_inventory':{'tasklist_returncode':0,
             'tasklist_pids':[],'wmi_pids':[],'native_pids':[],'processes':[]},'control_files_absent':{'ck3.json':True}}}}}
        self.assertTrue(allocation.closed_session(report));self.assertTrue(allocation.native_cleanup_closed(report))
        wrong=copy.deepcopy(report);wrong['session']['report']['shutdown']['job_active_processes_final']=1
        self.assertFalse(allocation.native_cleanup_closed(wrong))
        keeper={'task_id':'old','thread_exited':True,'last_sequence':2}
        release={'ok':True,'task':{'task_id':'old','state':'done','resources':[],'last_sequence':3}}
        self.assertTrue(allocation.closed_lease(keeper,release,'old'))
        release['task']['last_sequence']=2
        self.assertFalse(allocation.closed_lease(keeper,release,'old'))

    def test_no_product_runtime_paths_and_all_sources_compile(self):
        # The unified entry and its current adapters own runtime selection.
        # Existing independent evidence readers have separately authorized
        # exact-build constants and are not product runtime selectors.
        sources=[HERE/name for name in ('ck3_mod_acceptance.py','ck3_mod_acceptance_allocate.py',
            'ck3_mod_acceptance_client.py','ck3_mod_acceptance_prepare.py','fixture_engine_prepare.py')]
        sources+=sorted((HERE/'ck3_mod_acceptance_cases').rglob('*.py'))
        self.assertGreaterEqual(len(sources),12)
        for path in sources:
            source=path.read_text(encoding='utf-8-sig')
            ast.parse(source,filename=str(path))
            self.assertNotIn('C:/workspace/',source,str(path))
            self.assertNotIn('C:\\workspace\\',source,str(path))
            self.assertNotIn('98702f88',source.lower(),str(path))
        ui=ast.parse((HERE/'ck3_mod_acceptance_cases/xqol_ui.py').read_text())
        cls=next(n for n in ui.body if isinstance(n,ast.ClassDef))
        record=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='record')
        self.assertIn('1000000',ast.unparse(record))
        self.assertIn('pending_naturally_completed',ast.unparse(record))

    def test_title_holder_unwrap_preserves_raw_row_and_other_tools(self):
        # Match the registered service's result.title_holder envelope. The
        # outer status is available even when the nested holder is unavailable.
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            packet={'status':'available','title_id':7,'read_only':True,
                'title_holder':{'schema':'xar.ck3.title-holder.v1','schema_version':1,
                    'available':True,'status':'available','title_id':7,'holder_character_id':20}}
            row={'id':'synthetic-holder','ok':True,'result':packet}
            calls=[]
            def execute(steps,identifier):calls.append(steps);return [copy.deepcopy(row)]
            controller=object.__new__(xqol_ui.Controller)
            controller.client=SimpleNamespace(execute_plan=execute)
            controller.out=out
            holder=controller.typed('title-holder',{'title_id':7},'available')
            self.assertEqual(holder,packet['title_holder'])
            self.assertEqual(entry.read_json(out/'available.actual-result.json'),row)
            self.assertEqual(calls[0][0]['tool'],'ck3_query_title_holder_v1')
            self.assertEqual(calls[0][0]['args'],{'title_id':7})
            row['result']['title_holder']={'available':False,'status':'unavailable'}
            self.assertIs(controller.typed('title-holder',{'title_id':7},'unavailable')['available'],False)
            row['result']={'status':'available'}
            with self.assertRaises(RuntimeError):controller.typed('title-holder',{'title_id':7},'missing')
            row['result']={'available':True,'status':'available'}
            with self.assertRaises(RuntimeError):controller.typed('title-holder',{'title_id':7},'flat')
            row['result']={'current_event_window_context':{'status':'available'}}
            self.assertEqual(controller.typed('event-context',{'event_instance_id':1},'event'),row['result'])

    def test_public_cli_exit_code_requires_strict_qualified_verdict(self):
        # Invoke the real main parser and its verdict gate, never a copied
        # predicate. Selection is the only seam mocked: no file or runtime I/O.
        for mode,answer,expected in [
            *[('verify',{'case_acceptance_pass':value},2) for value in (False,None,1)],
            ('verify',{'case_acceptance_pass':True},0),
            ('verify',{},2),
            *[('run',{'normal_close':{'normal_close_qualified':value}},2) for value in (False,None,1)],
            ('run',{'normal_close':None},2),
            ('run',{'normal_close':{'normal_close_qualified':True}},0),
            ('run',{'normal_close':{'normal_close_qualified':True},'normal_close_error':'synthetic error'},2),
            ('run',{'normal_close':{'normal_close_qualified':True},'case_error':'synthetic error'},2),
            ('run',{'normal_close':{'normal_close_qualified':True},'launcher_exit_code':1},2),
        ]:
            with self.subTest(mode=mode,answer=answer):
                selection=SimpleNamespace(verify=lambda:copy.deepcopy(answer),run=lambda:copy.deepcopy(answer))
                output=io.StringIO()
                with patch.object(entry,'Selection',return_value=selection) as constructor,contextlib.redirect_stdout(output):
                    status=entry.main([mode,'--runtime','synthetic-runtime.json','--products','synthetic-products.json',
                                       '--product','synthetic','--case','synthetic-case'])
                self.assertEqual(status,expected)
                self.assertEqual(json.loads(output.getvalue()),answer)
                constructor.assert_called_once_with(Path('synthetic-runtime.json'),Path('synthetic-products.json'),
                    'synthetic','synthetic-case',None,None)

    def test_mocked_allocation_register_immediately_starts_original_keeper(self):
        # Run the actual new branch once with all external process and bus
        # providers mocked. Synthetic files contain no original game/profile.
        import ck3_mod_acceptance_prepare as prep
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);repo=root/'repo';(repo/'tools').mkdir(parents=True)
            lease=root/'lease';(lease/'tools').mkdir(parents=True);(lease/'promo/ck3_native_war_ai/integration').mkdir(parents=True)
            for path in (repo/'tools/ck3_live_run_id.py',lease/'tools/codex_task_bus.py',lease/'promo/ck3_native_war_ai/integration/screen_bus_lease.py'):
                path.write_text('synthetic-source')
            config=root/'runtime.json';products=root/'products.json';prepared=root/'prepared.json'
            bus=root/'bus/bin/bus.py';bus.parent.mkdir(parents=True);bus.write_text('synthetic-bus')
            keeper=root/'keeper.py';keeper.write_text('synthetic-keeper');launcher=root/'launcher.py';launcher.write_text('synthetic-launcher')
            queue=root/'queue.py';queue.write_text('synthetic-queue')
            for path in (config,products,prepared):path.write_text('{}')
            state=root/'input/state';profile=state/'profile';profile.mkdir(parents=True)
            file=profile/'synthetic.txt';file.write_text('synthetic-only')
            prior=root/'previous';prior.mkdir()
            report={'finished_at':'actual','managed_session_thread_finished':True,'cleanup_ok':True,'session':{'report':{'finished_at':'actual',
                'shutdown':{'ok':True,'cleanup_proven':True,'tree_gone':True,'job_active_processes_final':0,'contract_errors':[],
                'final_ck3_inventory':{'tasklist_returncode':0,'tasklist_pids':[],'wmi_pids':[],'native_pids':[],'processes':[]},
                'control_files_absent':{'ck3.json':True}}}}}
            prep.write_json(prior/'frozen-argv.json',{'screen_task':'old'});prep.write_json(prior/'native-report.json',report)
            previous_keeper=root/'prior-keeper';previous_keeper.mkdir();prep.write_json(previous_keeper/'report.json',{'task_id':'old','thread_exited':True,'last_sequence':2})
            release=root/'release.json';prep.write_json(release,{'ok':True,'schema':'codex.task_bus.v1','task':{'task_id':'old','state':'done','resources':[],'last_sequence':3}})
            selected=SimpleNamespace(prepared_path=prepared,context={},runtime_path=config,products_path=products,
                product_key='synthetic',product={'runtime_mod_key':'synthetic'},case={'id':'basic'},state_dir=state,adapter_path=None,
                locations={'python':Path(sys.executable),'repo_root':repo,'artifacts_root':root/'live'},
                runtime={'allocation':{'task_bus':entry.pin(bus),'screen_keeper':entry.pin(keeper),'lease_repo':str(lease),'task_prefix':'test-'},
                         'reviewed_launcher':entry.pin(launcher),'control_queue':entry.pin(queue)},
                prepared={'case_inputs':{},'startup':{'mode':'fixture'},'preparation':{'profile':{'files':{'synthetic.txt':entry.pin(file)}}}})
            selected.preflight=lambda:{'blockers':[],'checked_inputs':[entry.pin(prepared)]}
            actual=SimpleNamespace(argv=['one-shared-host'],state_dir=state,manifest={'source_root':{}},manifest_path=config,
                manifest_path_key=lambda row:root/'shared-source',runtime_environment={'PYTHONUTF8':'1'})
            args=SimpleNamespace(attempt='a999',keeper_output=root/'keeper-output',previous_live=prior,previous_keeper=previous_keeper,
                                  previous_release=release,latest_screen_release=None)
            identity=SimpleNamespace(run_id='synthetic-R0001',mod_key='synthetic',execution_id='synthetic-exec')
            ids=SimpleNamespace(current_machine_id=lambda:'synthetic-machine',default_state_root=lambda:root/'ids',allocate_live_run_id=lambda *a,**k:identity)
            sequence=[]
            def run(argv,**kwargs):
                if argv[0]=='git':return SimpleNamespace(stdout=b'',returncode=0)
                sequence.append('REGISTER')
                self.assertEqual(argv[argv.index('--expected-cli-sha256')+1],entry.pin(bus)['sha256'].upper())
                return SimpleNamespace(stdout=json.dumps({'task':{'last_sequence':10}}).encode(),stderr=b'',returncode=0)
            class Child:
                pid=1234
                def poll(self):return None
                def wait(self):sequence.append('WAIT_REAL_CHILD');return 0
            def popen(argv,**kwargs):
                sequence.append('KEEPER_POPEN');args.keeper_output.mkdir()
                prep.write_json(args.keeper_output/'ready.json',{'sequence':11})
                prep.write_json(args.keeper_output/'report.json',{'thread_exited':True,'last_sequence':11,'failure':None})
                return Child()
            process_provider=SimpleNamespace(process_iter=lambda fields:[],
                Process=lambda pid:SimpleNamespace(create_time=lambda:1.0))
            with (patch.dict(sys.modules,{'ck3_live_run_id':ids,'psutil':process_provider}),
                 patch.object(allocation,'Selection',return_value=actual),
                 patch.object(allocation.subprocess,'run',side_effect=run),
                 patch.object(allocation.subprocess,'Popen',side_effect=popen)):
                answer=allocation.allocate_and_keep(selected,args)
            self.assertEqual(sequence,['REGISTER','KEEPER_POPEN','WAIT_REAL_CHILD'])
            self.assertEqual(answer['keeper_actual_exit_code'],0)
            self.assertFalse(answer['game_started'])

if __name__=='__main__':unittest.main()
