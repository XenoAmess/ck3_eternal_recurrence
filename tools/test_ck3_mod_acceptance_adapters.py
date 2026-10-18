"""Focused source-only checks for new common adapter/allocation seams."""
from __future__ import annotations
import argparse,ast,contextlib,copy,hashlib,importlib.util,io,json,os,re,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_allocate as allocation
import ck3_live_run_id as live_ids
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
            selected.opt_in_read_only_mcp_tools=[]
            # This pure build_argv fixture bypasses __init__; retain every
            # explicitly initialized opt-in added by the holy-site provider.
            selected.opt_in_player_rite_creation_actions=False
            selected.opt_in_holy_site_relic_actions=False
            selected.opt_in_holy_site_creation_ui=False
            selected.opt_in_holy_site_creation_create_once=False
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
            self.assertNotIn('--private-holy-site-relic-actions',actual_argv)
            self.assertNotIn('--private-player-holy-site-creation-ui',actual_argv)
            selected.opt_in_holy_site_relic_actions=True
            selected.opt_in_holy_site_creation_ui=True
            opted_argv=selected.build_argv()
            self.assertEqual(opted_argv.count('--private-holy-site-relic-actions'),1)
            self.assertEqual(opted_argv.count('--private-player-holy-site-creation-ui'),1)
            selected.opt_in_holy_site_relic_actions=False
            selected.opt_in_holy_site_creation_ui=False
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
            tree=ast.parse(source,filename=str(path))
            checked_source=source
            if path.name=='ck3_mod_acceptance_allocate.py':
                # One frozen legacy keeper bus is an identity guard, not a runtime selector.
                assignments={n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign)
                    and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
                legacy=assignments['LEGACY_KEEPER_BUS']
                self.assertEqual(ast.unparse(legacy.value),"Path('C:/workspace/.codex-task-bus')")
                self.assertEqual(ast.literal_eval(assignments['LEGACY_KEEPER_SHA'].value),
                    '2afdf264b509a045c878fd1ee94426cf418cd747a5773ded43a83001a3813def')
                self.assertEqual(ast.literal_eval(assignments['LEGACY_KEEPER_BUS_SHA'].value),
                    'B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE')
                command=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='keeper_command')
                branch=next(n for n in command.body if isinstance(n,ast.If))
                self.assertEqual(ast.unparse(branch.test),
                    'hashlib.sha256(Path(keeper).read_bytes()).hexdigest() == LEGACY_KEEPER_SHA')
                self.assertEqual(ast.unparse(branch.body[0].value.args[0]),
                    'Path(bus_dir).resolve() == LEGACY_KEEPER_BUS.resolve() and bus_sha.upper() == LEGACY_KEEPER_BUS_SHA')
                self.assertEqual(ast.unparse(branch.body[1]),'return argv')
                self.assertEqual(sum(isinstance(n,ast.Name) and n.id=='LEGACY_KEEPER_BUS'
                    and isinstance(n.ctx,ast.Load) for n in ast.walk(tree)),1)
                lines=source.splitlines(keepends=True)
                lines[legacy.lineno-1:legacy.end_lineno]=['\n']
                checked_source=''.join(lines)
            self.assertNotIn('C:/workspace/',checked_source,str(path))
            self.assertNotIn('C:\\workspace\\',source,str(path))
            self.assertNotIn('98702f88',source.lower(),str(path))
        ui=ast.parse((HERE/'ck3_mod_acceptance_cases/xqol_ui.py').read_text())
        cls=next(n for n in ui.body if isinstance(n,ast.ClassDef))
        record=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='record')
        self.assertIn('1000000',ast.unparse(record))
        self.assertIn('pending_naturally_completed',ast.unparse(record))

    def test_religion_verify_requires_exact_initial_prefix_and_stable_scope(self):
        from ck3_mod_acceptance_cases import xqol_religion_adapter as religion
        # Synthetic append-only natural-day log; actual parser/verifier, no client or game.
        framed=('\n'.join([religion.MARKERS['begin'],
            '[00:00:00][D][effectimpl.cpp:1]: Synthetic (Internal ID: 34422 - Historical ID han_8052)',
            'Saved event targets:',
            'xqol_startup_actor: Synthetic (Internal ID: 34422 - Historical ID han_8052)',
            religion.MARKERS['pass'],religion.MARKERS['end']])+'\n').encode()
        prefix=b'SYNTHETIC INITIAL LOG\n'+framed
        appended=b'SYNTHETIC RITE OUTCOME PASS\n'
        proof=religion.scope(prefix)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw_path=root/'religion-debug-original.raw'
            result_path=root/'xqol-religion-result.json'
            context={'output':str(root),'run_id':'SYNTHETIC_ONLY_RITES',
                'case_contract':{'case':'religion_rite_outcomes',
                    'required':['SYNTHETIC RITE OUTCOME PASS'],
                    'forbidden':['SYNTHETIC RITE OUTCOME FAIL']}}
            def save(raw,scope_proof):
                raw_path.write_bytes(raw)
                result={'run_id':context['run_id'],'case':'religion_rite_outcomes',
                    'actual_actor_scope':copy.deepcopy(scope_proof),'debug_original':religion.pin(raw_path),
                    'case_contract_qualified':True,'gui_contract_qualified':True,
                    'business_pass':False,'product_release_pass':False}
                result_path.write_text(json.dumps(result),encoding='utf-8')
                return result
            original=save(prefix+appended,proof)
            accepted=religion.verify_case(context)
            self.assertTrue(accepted['case_contract_qualified'])
            self.assertEqual(accepted['actual_actor_scope'],proof)
            self.assertFalse(accepted['business_pass'])
            self.assertFalse(accepted['product_release_pass'])
            self.assertEqual(entry.read_json(result_path),original)
            for label,raw,changed in [
                ('changed-initial-prefix',prefix.replace(b'SYNTHETIC INITIAL',b'SYNTHETIC ALTERED')+appended,proof),
                ('duplicate-scope',prefix+appended+framed,proof),
                ('forbidden-append',prefix+appended+b'SYNTHETIC RITE OUTCOME FAIL\n',proof),
                ('boolean-prefix-length',prefix+appended,{**proof,'log_bytes':True}),
                ('oversized-prefix-length',prefix+appended,{**proof,'log_bytes':len(prefix+appended)+1}),
                *[('changed-proof-'+key,prefix+appended,{**proof,key:value}) for key,value in (
                    ('runtime_character_id',34423),('historical_character_id','wrong'),
                    ('raw_scope_block_hex','00'),('raw_scope_block_sha256','0'*64),
                    ('byte_start',proof['byte_start']+1),('root_scope_used',True),
                    ('schema','different'),('log_sha256','0'*64))],
            ]:
                with self.subTest(label=label):
                    save(raw,changed)
                    with self.assertRaises(ValueError):religion.verify_case(context)
            save(prefix+appended,proof)
            raw_path.write_bytes(prefix+appended+b'late change\n')
            with self.assertRaises(ValueError):religion.verify_case(context)

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
        # predicate. Mock native route metadata and Selection: no file or runtime I/O.
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
                with (patch.object(entry,'read_json',side_effect=[
                        {'manifest':{'path':'synthetic-manifest.json'}}, {'execution_mode':'native'}]),
                      patch.object(entry,'Selection',return_value=selection) as constructor,
                      contextlib.redirect_stdout(output)):
                    status=entry.main([mode,'--runtime','synthetic-runtime.json','--products','synthetic-products.json',
                                       '--product','synthetic','--case','synthetic-case'])
                self.assertEqual(status,expected)
                self.assertEqual(json.loads(output.getvalue()),answer)
                constructor.assert_called_once_with(Path('synthetic-runtime.json'),Path('synthetic-products.json'),
                    'synthetic','synthetic-case',None,None)

    def test_mocked_allocation_register_immediately_starts_original_keeper(self):
        # Machine binding, predecessor closure and the admission chain run for
        # real against temporary synthetic files. Only external OS/bus/process
        # providers and ID allocation are mocked; no workstation state is used.
        import ck3_mod_acceptance_prepare as prep
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();repo=root/'repo';(repo/'tools').mkdir(parents=True)
            lease=root/'lease';(lease/'tools').mkdir(parents=True);(lease/'promo/ck3_native_war_ai/integration').mkdir(parents=True)
            for path in (repo/'tools/ck3_live_run_id.py',lease/'tools/codex_task_bus.py',lease/'promo/ck3_native_war_ai/integration/screen_bus_lease.py'):
                path.write_text('synthetic-source')
            config=root/'runtime.json';products=root/'products.json';prepared=root/'prepared.json'
            bus=root/'bus/bin/bus.py';bus.parent.mkdir(parents=True);bus.write_text('synthetic-bus')
            (bus.parents[1]/'events.jsonl').write_text('')
            keeper=root/'keeper.py';keeper.write_text('synthetic-keeper');launcher=root/'launcher.py';launcher.write_text('synthetic-launcher')
            queue=root/'queue.py';queue.write_text('synthetic-queue')
            for path in (config,products,prepared):path.write_text('{}')
            state=root/'input/state';profile=state/'profile';profile.mkdir(parents=True)
            file=profile/'synthetic.txt';file.write_text('synthetic-only')
            prior=root/'previous';prior.mkdir()
            machine_token='machine-id:synthetic-ci-fixture-only'
            machine=live_ids.derive_machine_id('synthetic-ci-host',machine_token)
            binding={'machine_id':machine,'state_root':str(root/'ids'),
                'admission_root':str(root/'ids'/machine/'.shared-runtime-admissions-v1')}
            admission=Path(binding['admission_root']);prior_admission=admission/'000001'
            prior_admission.mkdir(parents=True)
            prep.write_json(admission/'machine.json',binding)
            prep.write_json(prior_admission/'allocation.json',{'run_id':'synthetic-R0000','live':str(prior)})
            report={'finished_at':'actual','managed_session_thread_finished':True,'cleanup_ok':True,'session':{'report':{'finished_at':'actual',
                'shutdown':{'ok':True,'cleanup_proven':True,'tree_gone':True,'job_active_processes_final':0,'contract_errors':[],
                'final_ck3_inventory':{'tasklist_returncode':0,'tasklist_pids':[],'wmi_pids':[],'native_pids':[],'processes':[]},
                'control_files_absent':{'ck3.json':True}}}}}
            prep.write_json(prior/'frozen-argv.json',{'screen_task':'old','run_id':'synthetic-R0000',
                'identity_allocation':{'machine_id':machine,'state_root':binding['state_root']}})
            prep.write_json(prior/'native-report.json',report)
            previous_keeper=root/'prior-keeper';previous_keeper.mkdir();prep.write_json(previous_keeper/'report.json',{'task_id':'old','thread_exited':True,'last_sequence':2})
            release=root/'release.json';prep.write_json(release,{'ok':True,'schema':'codex.task_bus.v1','task':{'task_id':'old','state':'done','resources':[],'last_sequence':3}})
            events=[{'schema':'codex.task_bus.v1','sequence':1,'kind':'registered',
                     'summary':'synthetic basic shared runtime acceptance','task_id':'old','resources':['ck3-screen:acquired']},
                    {'schema':'codex.task_bus.v1','sequence':3,'kind':'completed','task_id':'old','resources':[]}]
            (bus.parents[1]/'events.jsonl').write_text('\n'.join(json.dumps(row) for row in events)+'\n',encoding='utf-8')
            selected=SimpleNamespace(prepared_path=prepared,context={},runtime_path=config,manifest_path=config,products_path=products,
                product_key='synthetic',product={'runtime_mod_key':'synthetic'},case={'id':'basic'},state_dir=state,adapter_path=None,
                locations={'python':Path(sys.executable),'repo_root':repo,'artifacts_root':root/'live'},
                runtime={'allocation':{'task_bus':entry.pin(bus),'screen_keeper':entry.pin(keeper),'lease_repo':str(lease),'task_prefix':'test-'},
                         'reviewed_launcher':entry.pin(launcher),'control_queue':entry.pin(queue)},
                prepared={'case_inputs':{},'startup':{'mode':'fixture'},'preparation':{'profile':{'files':{'synthetic.txt':entry.pin(file)}}}})
            selected.preflight=lambda:{'blockers':[],'checked_inputs':[entry.pin(prepared)]}
            actual=SimpleNamespace(argv=['one-shared-host'],state_dir=state,manifest={'source_root':{}},manifest_path=config,
                manifest_path_key=lambda row:root/'shared-source',runtime_environment={'PYTHONUTF8':'1'})
            args=SimpleNamespace(attempt='a999',keeper_output=root/'keeper-output',previous_live=prior,previous_keeper=previous_keeper,
                                  previous_release=release,latest_screen_release=None,first_machine_bootstrap=None)
            identity=SimpleNamespace(run_id='synthetic-R0001',mod_key='synthetic',execution_id='synthetic-exec')
            sequence=[]
            def call_bus(script,bus_dir,sha,*argv,**kwargs):
                self.assertEqual(script,lease/'tools/codex_task_bus.py')
                self.assertEqual(bus_dir,bus.parents[1])
                self.assertEqual(sha,entry.pin(bus)['sha256'].upper())
                self.assertEqual(argv,('list','--stale-after','600'))
                sequence.append('FRESH_BUS_LIST')
                return {'ok':True,'schema':'codex.task_bus.v1','tasks':[entry.read_json(release)['task']]}
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
            with (patch.dict(sys.modules,{'psutil':process_provider}),
                 patch.dict(os.environ,{live_ids.MACHINE_ENV:'',live_ids.STATE_ROOT_ENV:''}),
                 patch.object(live_ids.platform,'node',return_value='synthetic-ci-host'),
                 patch.object(live_ids,'_automatic_machine_token',return_value=machine_token),
                 patch.object(live_ids,'default_state_root',return_value=root/'ids'),
                 patch.object(live_ids,'allocate_live_run_id',return_value=identity) as allocate_id,
                 patch('ck3_mod_acceptance_keeper.load_lease_module',return_value=SimpleNamespace(call_bus=call_bus)),
                 patch.object(allocation,'Selection',return_value=actual),
                 patch.object(allocation.subprocess,'run',side_effect=run),
                 patch.object(allocation.subprocess,'Popen',side_effect=popen)):
                answer=allocation.allocate_and_keep(selected,args)
            allocate_id.assert_called_once_with('synthetic',state_root=root/'ids',machine_id=machine,external_mod=False)
            self.assertEqual(sequence,['FRESH_BUS_LIST','REGISTER','KEEPER_POPEN','WAIT_REAL_CHILD'])
            self.assertEqual(answer['keeper_actual_exit_code'],0)
            self.assertFalse(answer['game_started'])
            record=admission/'000002'
            self.assertEqual(entry.read_json(record/'allocation.json')['run_id'],identity.run_id)
            closure=entry.read_json(record/'intent.json')['closure']
            self.assertEqual(closure['mode'],'previous-shared-managed-session')
            self.assertEqual(closure['run_id'],'synthetic-R0000')
            self.assertEqual(closure['machine'],binding)

class FailedLaunchPredecessor(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.previous=Path(self.temp.name)/'previous';self.previous.mkdir()
        self.state=Path(self.temp.name)/'played-state';(self.state/'control').mkdir(parents=True)
        self.freeze={'run_id':'synthetic-R0041','state_dir':str(self.state)}
        self.report={'status':'RED','finished_at':'actual','managed_session_thread_finished':True,
            'cleanup_ok':False,'steps':[],'state_dir':str(self.state),'session':{'report':None,
            'error':'AgentError: native-session failed after 601.543s (launch_error): '
                    'CK3 launch contract failed safely: saved startup Setup completion marker missed the original readiness deadline'}}
        self.started={'run_id':self.freeze['run_id'],'pid':71,'actual_popen_retained':True}
        self.exited={'run_id':self.freeze['run_id'],'pid':71,'returncode':1,
            'actual_original_popen_wait':True,'normal_ck3_exit_inferred':False}
        self.save()

    def save(self):
        for name,value in (('native-report.json',self.report),('host-started.json',self.started),
                           ('host-original-process-exit.json',self.exited)):
            (self.previous/name).write_text(json.dumps(value),encoding='utf-8')

    def check(self):
        self.save()
        return allocation.previous_session_closure(self.previous,self.freeze,self.report)

    def test_safe_failed_launch_has_separate_credit_without_changing_original_red(self):
        # The early-start receipt is historical and is allowed to remain.
        (self.state/'control/ck3.synthetic.watchdog_start.json').write_text('{}')
        result=self.check()
        self.assertEqual(result['mode'],'previous-shared-failed-launch')
        proof=result['failure_cleanup']
        self.assertFalse(proof['original_cleanup_ok'])
        self.assertIsNone(proof['original_ck3_exit_code'])
        self.assertIsNone(proof['original_job_active_processes_final'])
        self.assertFalse(proof['typed_normal_exit_proven'])
        self.assertFalse(proof['business_pass'])
        self.assertEqual(proof['report'],entry.pin(self.previous/'native-report.json'))
        self.assertFalse(allocation.closed_session(self.report))
        self.assertIsNone(self.report['session']['report'])

    def test_unsafe_pid_or_ready_marker_still_blocks(self):
        for name in ('unsafe-cleanup.json','ck3.json','watchdog-synthetic.ready.json'):
            with self.subTest(marker=name):
                path=self.state/'control'/name;path.write_text('{}')
                with self.assertRaisesRegex(ValueError,'controls remain'):self.check()
                path.unlink()

    def test_nonterminal_or_executed_case_cannot_use_failed_launch_route(self):
        original=copy.deepcopy(self.report)
        changes=({'finished_at':None},{'managed_session_thread_finished':False},
                 {'steps':[{'ok':False}]},{'readiness':{'ready':True}},{'cleanup_ok':None})
        for changeset in changes:
            with self.subTest(changes=changeset):
                self.report={**copy.deepcopy(original),**changeset}
                with self.assertRaisesRegex(ValueError,'exact safe failed launch'):self.check()
        self.report=original
        self.report['session']['error']=self.report['session']['error'].replace('launch_error','readiness_timeout')
        with self.assertRaisesRegex(ValueError,'exact safe failed launch'):self.check()

    def test_original_host_wait_and_run_pid_binding_are_required(self):
        original=copy.deepcopy(self.exited)
        for change in ({'returncode':0},{'returncode':True},{'actual_original_popen_wait':False},
                       {'run_id':'other'},{'pid':72}):
            with self.subTest(change=change):
                self.exited={**original,**change}
                with self.assertRaisesRegex(ValueError,'original host Popen failure'):self.check()

    def test_current_control_state_cannot_come_from_another_profile(self):
        self.report['state_dir']=str(self.state.parent/'unrelated-state')
        with self.assertRaisesRegex(ValueError,'state differs'):self.check()

    def test_returned_native_session_with_incomplete_cleanup_never_falls_back(self):
        self.report['session']['report']={'finished_at':'actual','shutdown':{'ok':False}}
        with self.assertRaisesRegex(ValueError,'exact safe failed launch'):self.check()
        self.report['cleanup_ok']=True
        with self.assertRaisesRegex(ValueError,'no OS0 inference'):self.check()

class FailedRuntimeClosureTests(unittest.TestCase):
    """Actual public failure-admission functions, with no game/Steam/bus mutation."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.previous=self.root/'synthetic-live';self.previous.mkdir()
        self.state=self.root/'state';(self.state/'control').mkdir(parents=True)
        self.keeper_root=self.root/'keeper';self.keeper_root.mkdir()
        self.run_id='SYNTHETIC_ONLY-R0076';self.task='SYNTHETIC_ONLY-a179'
        self.freeze={'run_id':self.run_id,'cell':'administrative_appointments','state_dir':str(self.state),
            'source_root':str(self.root/'source'),'argv':['SYNTHETIC_ONLY-host'],'screen_task':self.task,
            'runtime_manifest':{'path':str(self.root/'SYNTHETIC_ONLY-manifest'),'bytes':1,'sha256':'a'*64}}
        self.report={'status':'RUNNING','phase':'hold','finished_at':None,'state_dir':str(self.state),
            'agent_source_root':self.freeze['source_root'],'steps':[{'ok':True}],'readiness':{'ready':True}}
        self.save(self.previous/'frozen-argv.json',self.freeze)
        self.save(self.previous/'native-report.json',self.report)
        (self.previous/'harness-stderr.log').write_text(
            'PermissionError: [WinError 5] SYNTHETIC_ONLY replace-report-from-partial\n',encoding='utf-8')
        self.launch={'harness_pid':71,'create_time':1.5,'argv':self.freeze['argv']}
        self.save(self.previous/'launch.json',self.launch)
        self.save(self.previous/'keeper-process.json',{'pid':72,'create_time':2.5})
        (self.previous/'case-output').mkdir()
        self.identity={'pid':73,'create_time':3.5,'retained_synchronize_query_handle_acquired':True}
        self.game_exit={**self.identity,'signaled':True,'exit_code':1,'actual_retained_os0':False}
        self.save(self.previous/'case-output/retained-current-process-identity.json',self.identity)
        self.save(self.previous/'case-output/actual-retained-handle-os-exit.json',self.game_exit)
        self.keeper={'task_id':self.task,'thread_exited':True,'last_sequence':11}
        self.save(self.keeper_root/'report.json',self.keeper)
        self.save(self.previous/'keeper-actual-parent-exit.json',{'run_id':self.run_id,
            'keeper_actual_exit_code':0,'keeper_report':self.keeper})
        runtime=self.save(self.root/'runtime.json',{'manifest':{**self.freeze['runtime_manifest'],
            'path':(self.root/'SYNTHETIC_ONLY-manifest').as_posix()}})
        prepared=self.save(self.root/'prepared.json',{'runtime_manifest':self.freeze['runtime_manifest'],
            'startup':{'state_dir':str(self.state)}})
        self.save(self.root/'context.json',{'run_id':self.run_id,'run_dir':str(self.previous)})
        def waited(mode,code):
            argv=[sys.executable,str(HERE/'ck3_mod_acceptance.py'),mode,'--runtime',runtime['path'],
                  '--prepared-case',prepared['path']]
            argv+=['--run-context',str(self.root/'context.json')] if mode=='run' else [
                '--attempt','a179','--keeper-output',str(self.keeper_root)]
            operation=self.save(self.root/(mode+'-operation.json'),{'argv':argv})
            stdout=self.root/(mode+'.stdout');stdout.write_text('SYNTHETIC_ONLY',encoding='utf-8')
            stderr=self.root/(mode+'.stderr');stderr.write_text('',encoding='utf-8')
            return self.save(self.root/(mode+'-exit.json'),{'schema':'xar-root-exact-public-command-exit-v1',
                'returncode':code,'operation':operation,'stdout':entry.pin(stdout),'stderr':entry.pin(stderr),
                'business_or_release_pass_claimed':False})
        self.release_path=self.root/'release.json'
        task={'task_id':self.task,'state':'done','resources':[],'last_sequence':12}
        event={'task_id':self.task,'state':'done','resources':[],'sequence':12}
        task_pin=self.save(self.root/'actual-task.json',task)
        raw=(json.dumps(event)+'\n').encode('utf-8');stream=self.root/'bus-events.jsonl';stream.write_bytes(raw)
        self.save(self.release_path,{'schema':'xar-screen-release-canonical-reconstruction-v1',
            'source_event_raw_utf8':raw.decode('utf-8'),'source_event_byte_offset':0,'source_event_bytes':len(raw),
            'source_event_raw_sha256':hashlib.sha256(raw).hexdigest(),'source_event_stream':str(stream),
            'actual_task_pin':task_pin,'task':task,'event':event,'release_confirmed_by_canonical_readback':True})
        self.bundle={'schema':'xar-failed-report-writer-attempt-resource-closed-v1',
            'status':'FAILED_ATTEMPT_RESOURCE_CLOSED','run_id':self.run_id,'case':self.freeze['cell'],
            'attempt':'a179','next_previous_live':str(self.previous),'normal_close_qualified':False,
            'business_pass':False,'release_pass':False,'original_evidence_not_rewritten':True,
            'native_report_unfinished':True,'native_report':entry.pin(self.previous/'native-report.json'),
            'harness_stderr':entry.pin(self.previous/'harness-stderr.log'),
            'original_launch_pin':entry.pin(self.previous/'launch.json'),'prepared_case':prepared,'runtime':runtime,
            'run_process_exit':waited('run',2),'allocator_actual_exit':waited('allocate',0),
            'keeper_actual_exit':entry.pin(self.previous/'keeper-actual-parent-exit.json'),
            'canonical_screen_release_pin':entry.pin(self.release_path)}
        self.close_path=self.root/'failure-close.json';self.bus_packet={'tasks':[]};self.present={}
        class Gone(Exception):pass
        def process(pid):
            if pid not in self.present:raise Gone()
            return SimpleNamespace(create_time=lambda:self.present[pid])
        self.psutil=SimpleNamespace(Process=process,NoSuchProcess=Gone,process_iter=lambda fields:[])

    @staticmethod
    def save(path,value):
        path.write_text(json.dumps(value),encoding='utf-8');return entry.pin(path)

    def check(self,correction=False):
        self.save(self.close_path,self.bundle);path=self.close_path
        if correction:
            path=self.root/'correction.json'
            self.save(path,{'schema':'xar-failed-report-writer-retained-exit-correction-v1','run_id':self.run_id,
                'original_resource_close_pin':entry.pin(self.close_path),'host_exit_code':None,'host_wait_proven':False,
                'normal_close_qualified':False,'business_pass':False,'release_pass':False,
                'actual_retained_exit_pin':entry.pin(self.previous/'case-output/actual-retained-handle-os-exit.json'),
                'retained_identity_pin':entry.pin(self.previous/'case-output/retained-current-process-identity.json'),
                'frozen_argv_pin':entry.pin(self.previous/'frozen-argv.json'),
                'original_launch_pin':entry.pin(self.previous/'launch.json'),'retained_process':self.game_exit,
                'original_ck3_exit_code':1,'retained_actual_OS0':False,'host_pid':71,'host_create_time':1.5})
        with patch.dict(sys.modules,{'psutil':self.psutil}):
            return allocation.previous_runtime_failure_closure(self.previous,self.freeze,self.report,path,
                self.keeper_root,self.release_path,self.bus_packet)

    def test_actual_failure_functions_admit_only_resources_and_preserve_original_report(self):
        original=(self.previous/'native-report.json').read_bytes()
        result=self.check(correction=True);proof=result['failure_cleanup']
        self.assertEqual(result['mode'],'previous-shared-failed-report-writer-runtime')
        self.assertTrue(proof['administrative_resource_admission_only'])
        self.assertEqual(proof['original_ck3_exit_code'],1)
        self.assertIsNone(proof['original_host_exit_code'])
        for key in ('original_host_wait_proven','actual_retained_os0','normal_close_qualified',
                    'typed_normal_exit_proven','business_pass','release_pass'):
            self.assertIs(proof[key],False)
        self.assertEqual((self.previous/'native-report.json').read_bytes(),original)
        self.assertEqual(result['actual_process_inventory']['blockers'],[])
        with self.assertRaisesRegex(ValueError,'exact safe failed launch'):
            allocation.previous_session_closure(self.previous,self.freeze,self.report)

    def test_crossed_run_is_not_an_administrative_close(self):
        self.bundle['run_id']='SYNTHETIC_ONLY-other'
        with self.assertRaisesRegex(ValueError,'crossed run/case/live'):self.check()

    def test_changed_original_report_pin_is_rejected(self):
        (self.previous/'native-report.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Pinned input changed'):self.check()

    def test_host_same_pid_and_creation_time_still_alive_is_rejected(self):
        self.present[71]=1.5
        with self.assertRaisesRegex(ValueError,'original host identity still present'):self.check()

    def test_pid_reuse_is_not_the_original_host_identity(self):
        self.present[71]=99.5
        self.assertEqual(self.check()['failure_cleanup']['original_host_exit_code'],None)

    def test_retained_ck3_exit_zero_is_not_claimed_by_failure_route(self):
        self.game_exit.update(exit_code=0,actual_retained_os0=True)
        self.save(self.previous/'case-output/actual-retained-handle-os-exit.json',self.game_exit)
        with self.assertRaisesRegex(ValueError,'retained CK3 nonzero exit proof differs'):self.check()

    def test_actual_screen_owner_or_unresolved_control_still_blocks(self):
        self.bus_packet={'tasks':[{'resources':['ck3-screen:acquired']}]}
        with self.assertRaisesRegex(ValueError,'still has a screen owner'):self.check()
        self.bus_packet={'tasks':[]}
        (self.state/'control/unsafe-cleanup.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'controls remain'):self.check()

    def test_canonical_reconstruction_must_match_actual_event_stream(self):
        (self.root/'bus-events.jsonl').write_text('SYNTHETIC_ONLY-wrong',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'actual canonical event stream'):self.check()

    def test_failure_flag_cannot_be_used_as_first_machine_bootstrap(self):
        selected=SimpleNamespace(prepared_path=Path('prepared'),context=None)
        args=SimpleNamespace(first_machine_bootstrap=Path('bootstrap'),previous_failure_close=Path('failure'),
            attempt='a179',keeper_output=Path('keeper'),previous_release=Path('release'),
            previous_live=None,previous_keeper=None)
        with self.assertRaisesRegex(ValueError,'mutually exclusive'):
            allocation.allocate_and_keep(selected,args)

if __name__=='__main__':unittest.main()
