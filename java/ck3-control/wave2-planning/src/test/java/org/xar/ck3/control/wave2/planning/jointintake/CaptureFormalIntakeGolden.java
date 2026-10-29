package org.xar.ck3.control.wave2.planning.jointintake;

import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPOutputStream;

/** Original Python producers with explicit source-guarded fixture corrections; no native qualification. */
public final class CaptureFormalIntakeGolden {
    private CaptureFormalIntakeGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("root python output required");
        Path root = Path.of(args[0]).toRealPath(), output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("new capture output required");
        Path fixtureDirectory = output.resolveSibling(output.getFileName().toString() + ".fixtures");
        if (Files.exists(fixtureDirectory)) throw new IllegalArgumentException("new fixture directory required");
        String script = """
                import sys, pathlib, runpy, copy, json, hashlib, datetime, unittest
                root=pathlib.Path(sys.argv[1]); sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit'),str(root/'tools')]
                from ck3_live_run_id import current_machine_id
                collector_source=root/'ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py'
                collector_bytes=collector_source.read_bytes()
                if len(collector_bytes)!=47732 or hashlib.sha256(collector_bytes).hexdigest()!='3aa8746189ad1c3013a0c2d7e2ea090612b5556627a5bdf2e5f15476c57ee07f':raise AssertionError('legacy collector test source drift')
                fixture_edits=[('        driver.state_dir = Path("Z:/fa98-tmp")\\n        driver.allow_private_faction_gift_formal_trial = True\\n        driver._session_bridge_pid = 12345\\n        pending = {\\n            "request_id": "gift-pending-same-date",\\n            "source_bridge_pid": 12345,\\n            "source_bridge_creation_date": "old-process",\\n            "episode_run_id": peace["episode_run_id"],\\n            "pre_snapshot_revision": peace["native_revision"],\\n            "pre_date_raw": peace["date_raw"],\\n        }\\n        fresh = {**peace, "revision": peace["revision"] + 1,\\n', '        driver.state_dir = Path("Z:/fa98-tmp")\\n        driver.allow_private_faction_gift_formal_trial = True\\n        driver._session_bridge_pid = 12345\\n        peace["played_character"] = {**peace["played_character"], "alive": True}\\n        peace["diagnostics"] = {"bridge_pid": 12345, "connection_generation": 7}\\n        driver._snapshot = deepcopy(peace)\\n        pending = {\\n            "request_id": "gift-pending-same-date",\\n            "source_bridge_pid": 12345,\\n            "source_bridge_creation_date": "old-process",\\n            "episode_run_id": peace["episode_run_id"],\\n            "pre_native_snapshot_revision": peace["native_revision"],\\n            "pre_player_character_id": peace["played_character"]["character_id"],\\n            "pre_date_raw": peace["date_raw"],\\n        }\\n        fresh = {**peace, "revision": peace["revision"] + 1,\\n'), ('            return_value=deepcopy(baseline),\\n        ):\\n            planned = GameplayBridgeService(driver).plan_turn()\\n        self.assertEqual(planned["plan"], baseline)\\n        self.assertEqual(driver.source_reads, 0)\\n\\n    def test_opt_in_preserves_non_life_advance_formal_step(self) -> None:\\n        driver = _ServiceDriver(\\n', '            return_value=deepcopy(baseline),\\n        ):\\n            planned = GameplayBridgeService(driver).plan_turn()\\n        control = _ServiceDriver(enabled=False)\\n        del control.allow_private_m5_joint_collector\\n        with mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn",\\n                        return_value=deepcopy(baseline)):\\n            ordinary = GameplayBridgeService(control).plan_turn()\\n        self.assertEqual(planned["plan"], ordinary["plan"])\\n        self.assertEqual({key: planned["plan"][key] for key in baseline}, baseline)\\n        self.assertEqual(driver.source_reads, 0)\\n        self.assertEqual(control.source_reads, 0)\\n\\n    def test_opt_in_preserves_non_life_advance_formal_step(self) -> None:\\n        driver = _ServiceDriver(\\n')]
                effective_bytes=collector_bytes
                for fixture_before,fixture_after in fixture_edits:
                    if effective_bytes.count(fixture_before.encode('utf-8'))!=1:raise AssertionError('legacy collector fixture hunk mismatch')
                    effective_bytes=effective_bytes.replace(fixture_before.encode('utf-8'),fixture_after.encode('utf-8'))
                if len(effective_bytes)!=48471 or hashlib.sha256(effective_bytes).hexdigest()!='6afa4d23ada4b14bf42021649be788361199f7be177f5b886059410fa38f0a1a':raise AssertionError('effective collector fixture source drift')
                fixture_dir=pathlib.Path(sys.argv[2]);fixture_dir.mkdir(exist_ok=False)
                effective_collector=fixture_dir/'test_m5_formal_proposal_collector.py'
                with effective_collector.open('xb') as target:target.write(effective_bytes)
                effective_test_sources=[{'original_path':str(collector_source),'original_bytes':len(collector_bytes),'original_sha256':hashlib.sha256(collector_bytes).hexdigest(),'effective_path':str(effective_collector),'effective_bytes':len(effective_bytes),'effective_sha256':hashlib.sha256(effective_bytes).hexdigest(),'correction':'current Service default-off plan compared with ordinary Service plan; actual gift pre_native_snapshot_revision/player/bridge/generation fields; no producer/policy edits','assembly_fixture_patch_sha256':'ab9a4f4bb33fe47d23edcc356647a09c1243dffe6278324715592ff389d9268d'}]
                t=runpy.run_path(str(effective_collector))
                b=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_current_betrothal_fulfillment_proposal.py'))
                from xar_autoplayer.m5_formal_proposal_collector import collect_m5_formal_proposals as collect
                suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(t['M5FormalProposalCollectorTests']),unittest.defaultTestLoader.loadTestsFromTestCase(b['CurrentBetrothalFulfillmentProposalTests'])])
                run=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
                if not run.wasSuccessful(): raise SystemExit(7)
                cases=[]
                def add(name,snapshot=None,sources=None):
                    snapshot=t['_snapshot']() if snapshot is None else snapshot
                    sources=t['_sources']() if sources is None else sources
                    request={'schema':'xar.java.m5-formal-intake-request.v1','snapshot':snapshot,'sources':sources}
                    try:
                        result=collect(snapshot=copy.deepcopy(snapshot),sources=copy.deepcopy(sources))
                        expected={key:result[key] for key in ('frame','collected_domains','collected_candidate_ids')}
                        expected['analysis']=result['dispatch']['analysis']
                        for key in ('war_cash_resource','producer_family_status','producer_faction_status','incomplete_domains'):
                            if key in result: expected[key]=result[key]
                        cases.append({'name':name,'input':request,'accepted':True,'expected':expected})
                    except ValueError as error: cases.append({'name':name,'input':request,'accepted':False,'error_type':type(error).__name__,'error':str(error)})
                add('three-active-domains')
                add('only-building',sources=t['_sources'](domains={'building':t['_building_source']()}))
                add('only-gift',sources=t['_sources'](domains={'diplomacy':t['_diplomacy_source']()}))
                add('empty-domain-map',sources=t['_sources'](domains={}))
                for key,values in [('army_ids',[71]),('ally_character_ids',[30098]),('character_ids',[30097]),('commitment_keys',['active-war:16777231'])]:
                    add('occupied-'+key,sources=t['_sources'](commitments=t['_commitments'](**{key:values})))
                pending=t['_sources'](commitments=t['_commitments'](gold_raw=2000000)); pending['war_cash_resource']=t['_war_cash'](2000000); pending['domains']['war']['observation']['war_cash_resource']=copy.deepcopy(pending['war_cash_resource'])
                add('pending-war-cash-counted-once',sources=pending)
                multi=t['_sources'](domains={'building':t['_building_source'](),'diplomacy':t['_diplomacy_source']()}); multi['war_cash_resource']=t['_multiwar_cash'](); multi['max_active_wars']=2
                multi['existing_commitments'].update(copy.deepcopy(multi['war_cash_resource']['existing_resource_claims'])); multi['existing_commitments']['gold_raw']=multi['war_cash_resource']['existing_shared_gold_commitment_raw']; multi['gold_reserve_raw']=multi['war_cash_resource']['joint_gold_reserve_raw']
                add('aggregate-all-war-occupation',snapshot=t['_multiwar_snapshot'](),sources=multi)
                peace=t['_snapshot'](); peace['active_wars']=[]; peace['player_armies']=[]
                add('peace-building-gift',snapshot=peace,sources=t['_sources'](domains={'building':t['_building_source'](),'diplomacy':t['_diplomacy_source']()}))
                frame=t['_FRAME']; actor=frame['played_character_id']; heir=38822
                plans=[]
                native=[]; rows=[]
                for index in range(5):
                    candidate=61001+index; recipient=62001+index
                    native.append({'candidate_character_id':candidate,'played_character_id':actor,'subject_character_id':heir,'recipient_matchmaker_character_id':recipient,'complete_can_send':True,'recipient_answer_allows_send':True,'recipient_answer_status_raw':1,'recipient_ai_accept_raw':9000000-index*100000})
                    rows.append({'candidate_character_id':candidate,'heir_character_id':heir,'recipient_character_id':recipient,'status':'available','actor_character_id':actor,'rejection_reasons':[],'heir_spouse_count':0,'heir_betrothed_character_id':None,'heir_primary_spouse_character_id':None,'grand_wedding_option_selected':False,'predicted_outcome_if_accepted':'betrothal','heir_adult_measure_raw':6,'candidate_adult_measure_raw':6+index,'possible_alliance_pairs':[{'first_character_id':actor,'second_character_id':recipient,'already_allied':False,'both_have_realm_data':True,'would_attempt_if_accepted':True}]})
                for index in range(5):
                    choice={'candidate_character_id':61001+index,'predicted_outcome_if_accepted':'betrothal','recipient_ai_accept_raw':9000000-index*100000,'value':'bounded_first_heir_betrothal_and_realm_alliance_attempt','realm_alliance_attempt_if_accepted':True,'unpriced':['child_dynasty_result','alliance_result','alliance_war_obligation','betrothal_break_cost'],'immediate_generic_costs':None}
                    plans.append({'selected_step':'submit-observed-first-heir-marriage-v1-private','family_marriage_choice':choice,'family_marriage_legality':{'status':'available','native_revision':frame['native_revision'],'query_sequence':9,'observed_first_heir_character_id':heir,'native_legal_candidates':copy.deepcopy(native)},'family_marriage_private_diagnostic':{'native_revision':frame['native_revision'],'date_raw':frame['date_raw'],'episode_run_id':frame['episode_run_id'],'legality_query_sequence':9,'selected_candidate_character_id':61001+index,'observed_first_heir_character_id':heir,'rows':copy.deepcopy(rows)}})
                family={'plan':plans[0],'plans':plans}
                add('five-family-proposals-original-rank',snapshot=peace,sources=t['_sources'](domains={'marriage':family}))
                current=b['_snapshot'](); relation=b['_relation'](); plan=b['_plan'](current,relation)
                add('existing-betrothal-adapter',snapshot=current,sources=b['_sources'](current,plan))
                council={'observation':{'snapshot':{'snapshot_id':frame['snapshot_id'],'public_revision':frame['revision'],'native_revision':frame['native_revision'],'date_raw':frame['date_raw'],'paused':True},'owner_character_id':actor,'position':{'incumbent_character_id':41001,'incumbent_main_skill':{'key':'stewardship','value':8}},'candidate_collection_complete':True,'candidates':[{'character_id':41002,'main_skill':{'key':'stewardship','value':17}}]},'decision':{'policy':'council-composition-steward-v1','outcome':'REPLACE_REQUIRED','action_routable':True,'required_capability':'game.action.assign-councillor-v1','incumbent_character_id':41001,'incumbent_main_skill':{'key':'stewardship','value':8},'selected_candidate':{'character_id':41002,'main_skill':{'key':'stewardship','value':17}}}}
                add('real-council-adapter',sources=t['_sources'](domains={'council':council}))
                o=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_m5_observed_opportunity_selector.py'))
                query,_=o['_wartime_lifestyle']()
                def reframe(value):
                    if isinstance(value,list): return [reframe(item) for item in value]
                    if not isinstance(value,dict): return value
                    result={key:reframe(item) for key,item in value.items()}
                    for key in ('native_revision','public_revision','proof_epoch'):
                        if key in result: result[key]=frame['native_revision']
                    for key in ('snapshot_id','episode_run_id','date_raw','revision'):
                        if key in result: result[key]=frame[key]
                    return result
                query=reframe(query)
                from xar_autoplayer.lifestyle_min_policy import choose_min_feudal_lifestyle_action
                decision=choose_min_feudal_lifestyle_action(query['snapshot'],feudal_scope_admitted=True,at_peace=False,allow_wartime_perk=True)
                lifestyle={'query':query,'decision':decision,'current_war_plan':t['_war_source']()['plan']}
                add('real-lifestyle-adapter',sources=t['_sources'](domains={'lifestyle':lifestyle}))
                allsix=t['_sources'](); allsix['domains'].update({'council':council,'marriage':family,'lifestyle':lifestyle})
                add('all-six-domain-order',sources=allsix)
                add('domain-null-is-omitted',sources=t['_sources'](domains={'council':None,'building':t['_building_source']()}))
                diagnostic=t['_sources'](domains={}); diagnostic['producer']={'family_status':'no_positive','faction_status':'unknown','incomplete_domains':[{'domain':'family','reason':'native gap'}]}
                add('producer-missingness-preserved',sources=diagnostic)
                bad=t['_sources'](); bad['frame']['revision']+=1; add('stale-source-frame',sources=bad)
                bad=t['_sources'](); bad['domains']['not-a-domain']={}; add('unknown-domain-rejected',sources=bad)
                bad=t['_sources'](); bad['gold_reserve_raw']=0; add('missing-war-reserve',sources=bad)
                bad=copy.deepcopy(multi); bad['existing_commitments']['army_ids']=[]; add('missing-aggregate-occupation',snapshot=t['_multiwar_snapshot'](),sources=bad)
                bad=t['_sources'](); bad['war_cash_resource']['joint_gold_reserve_raw']+=1; add('tampered-war-cash-header',sources=bad)
                bad=t['_sources'](domains={'marriage':copy.deepcopy(family)}); bad['domains']['marriage']['plans'][1]=copy.deepcopy(bad['domains']['marriage']['plans'][0]); add('duplicate-family-proposal',snapshot=peace,sources=bad)
                bad=t['_sources'](domains={'marriage':copy.deepcopy(family)}); bad['domains']['marriage']['plan']=plans[1]; add('first-plan-mismatch',snapshot=peace,sources=bad)
                paths=['ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py','ck3_autonomous_player/src/xar_autoplayer/m5_war_cash_resource_v1.py','ck3_autonomous_player/src/xar_autoplayer/lifestyle_min_policy.py','ck3_autonomous_player/src/xar_autoplayer/current_betrothal_fulfillment_proposal.py','ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py','ck3_autonomous_player/tests/unit/test_m5_formal_proposal_collector.py','ck3_autonomous_player/tests/unit/test_current_betrothal_fulfillment_proposal.py','ck3_autonomous_player/tests/unit/test_m5_observed_opportunity_selector.py']
                print(json.dumps({'schema':'xar.java.m5-formal-intake-producer-golden.v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()}for p in paths],'effective_test_sources':effective_test_sources,'original_tests_run':run.testsRun,'original_test_failures':len(run.failures),'original_test_errors':len(run.errors),'fixtures':'synthetic same-frame inputs through unchanged real producer and dispatcher; no native qualification','cases':cases},ensure_ascii=False,separators=(',',':')))
                """;
        Path temporary = Files.createTempFile(Path.of(System.getProperty("java.io.tmpdir")), "jointintake-", ".json");
        try {
            ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-", root.toString(), fixtureDirectory.toString());
            builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
            builder.environment().put("TEMP", System.getProperty("java.io.tmpdir")); builder.environment().put("TMP", System.getProperty("java.io.tmpdir"));
            builder.redirectError(ProcessBuilder.Redirect.INHERIT); builder.redirectOutput(temporary.toFile());
            Process process = builder.start();
            try {
            try (var stdin = process.getOutputStream()) { stdin.write(script.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
            if (!process.waitFor(60, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); throw new IllegalStateException("producer timeout"); }
            if (process.exitValue() != 0 || Files.size(temporary) > 1048576) throw new IllegalStateException("producer RED/oversized exit=" + process.exitValue() + " bytes=" + Files.size(temporary));
            byte[] raw = Files.readAllBytes(temporary); ByteArrayOutputStream compressed = new ByteArrayOutputStream();
            try (GZIPOutputStream gzip = new GZIPOutputStream(compressed)) { gzip.write(raw); }
            byte[] golden = compressed.toByteArray(); if (golden.length > 65536) throw new IllegalStateException("compressed golden exceeds 64 KiB");
            Files.createDirectories(output.getParent()); Files.write(output, golden, java.nio.file.StandardOpenOption.CREATE_NEW);
            System.out.println("raw_bytes=" + raw.length + " gzip_bytes=" + golden.length);
            } finally {
                if (process.isAlive()) {
                    process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                    process.waitFor(5, TimeUnit.SECONDS);
                }
            }
        } finally { Files.deleteIfExists(temporary); }
    }
}
