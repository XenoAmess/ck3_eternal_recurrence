package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPOutputStream;

/** Shared-owner-only bounded capture of the unchanged complete query and its actual collector. */
public final class CapturePeacetimeAssemblyGolden {
    private CapturePeacetimeAssemblyGolden() { }
    private static final String SCRIPT = """
            import copy, contextlib, datetime, hashlib, json, pathlib, sys, unittest
            from unittest.mock import patch
            repo,scratch,machine=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
            paths=['ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py','ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/player_child_default_formal_consumer.py','ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/tests/unit/test_m5_child_default_pending_commitments.py']
            def source_pins():
                return [{'path':path,'bytes':(repo/path).stat().st_size,'sha256':hashlib.sha256((repo/path).read_bytes()).hexdigest()} for path in paths]
            sources_before=source_pins()
            from xar_autoplayer import m5_peacetime_proposal_sources_v1 as module
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
            from xar_autoplayer.m5_formal_proposal_collector import collect_m5_formal_proposals
            import test_m5_peacetime_proposal_sources_v1 as tests
            import test_m5_child_default_pending_commitments as childtests
            def effective_test_pins():
                path=pathlib.Path(tests.__file__).resolve()
                expected=(scratch/'test-sources'/'ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py').resolve()
                if path!=expected: raise RuntimeError('reviewed shared corrected test-source module was not imported')
                return [{'repository_path':paths[-2],'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]
            effective_tests_before=effective_test_pins()
            suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(tests.M5PeacetimeProposalSourcesTests),unittest.defaultTestLoader.loadTestsFromTestCase(childtests.M5ChildDefaultPendingCommitmentsTests)])
            execution=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
            if not execution.wasSuccessful() or execution.skipped or execution.expectedFailures or execution.unexpectedSuccesses:
                raise RuntimeError('existing complete producer tests failed or did not execute every case normally')
            cases=[]
            definitions=[('two-domains',{}),('gift-disabled',{'gift':False}),('known-empty-faction',{'count':0}),('family-five-choices',{'family':True,'count':0}),('pending-family',{'family':True,'pending_family':True}),('pending-child',{'pending_child':True}),('pending-union',{'family':True,'pending_family':True,'pending_child':True}),('empty-domains',{'gift':False,'construction_empty':True}),('prior-construction-holds-only-building',{'prior':True}),('later-frame-releases-prior-building',{'released':True}),('readback-drift',{'drift':3}),('construction-ledger-changed',{'mutate':'construction'}),('family-ledger-changed',{'mutate':'family'})]
            canonical=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            names=[('construction','read_construction_ledger'),('faction','read_faction_gift_ledger_v1'),('family','read_family_marriage_ledger'),('child_default','read_child_default_ledger')]
            for name,setting in definitions:
                directory=scratch/name
                directory.mkdir(parents=True,exist_ok=False)
                if setting.get('prior'):
                    (directory/'construction-formal-pending-v1.json').write_text(json.dumps({'schema':'xar.ck3.construction_formal_pending_v1','pending':None,'applied':{'episode_run_id':tests._FRAME['episode_run_id']}}),encoding='utf-8')
                if setting.get('released'):
                    applied={'status':'applied','postcondition_verified':True,'episode_run_id':tests._FRAME['episode_run_id'],'actor_character_id':tests._FRAME['played_character_id'],'post_bridge_pid':123,'post_bridge_creation_date':'t1','post_native_revision':tests._FRAME['native_revision']-1,'post_date_raw':tests._FRAME['date_raw']-24}
                    (directory/'construction-formal-pending-v1.json').write_text(json.dumps({'schema':'xar.ck3.construction_formal_pending_v1','pending':None,'applied':applied}),encoding='utf-8')
                if setting.get('pending_family'):
                    pending={'episode_run_id':tests._FRAME['episode_run_id'],'played_character_id':29829,'heir_character_id':38822,'candidate_character_id':38710,'recipient_character_id':41003,'pre_native_revision':16}
                    (directory/'first-heir-marriage-formal-v1.json').write_text(json.dumps({'schema':'xar.ck3.first-heir-marriage-formal.v1','pending':pending,'resolved':None}),encoding='utf-8')
                if setting.get('pending_child'):
                    pending={'episode_run_id':tests._FRAME['episode_run_id'],'played_character_id':29829,'heir_character_id':38988,'candidate_character_id':37909,'recipient_character_id':34332,'selected_value_projection':{'generic_costs':{'gold_raw':0,'application_timing':'on_send'},'possible_alliance_pairs':[{'first_character_id':29829,'second_character_id':37909,'would_attempt_if_accepted':False}]}}
                    (directory/'player-child-default-formal-v1.json').write_text(json.dumps({'schema':'xar.ck3.player-child-default-formal.v1','pending':pending,'resolved':None}),encoding='utf-8')
                count=setting.get('count',1)
                driver=tests._Driver(directory,snapshot=tests._snapshot(faction_count=count),family_enabled=setting.get('family',False),gift_enabled=setting.get('gift',True),drift_on_internal_read=setting.get('drift'))
                building=tests._construction(status='no_legal_budgeted_building' if setting.get('construction_empty') else 'selected')
                if 'candidate' in building: building['candidate']['authored_monthly_income_hundredths']=35
                before=driver.take_snapshot()
                baseline={'policy':'one-life-turn-v1','phase':'peace_growth','selected_step':'life-advance'}
                reads={key:[] for key,method in names}; snapshots=[]; local={}; process_reads=[]
                def observed_process(_driver):
                    observed=(123,'t1'); process_reads.append(observed); return observed
                original_snapshot=driver.take_internal_semantic_snapshot
                def snapshot():
                    observed=original_snapshot(); snapshots.append(copy.deepcopy(observed))
                    if setting.get('mutate') and driver.internal_reads==3:
                        if setting['mutate']=='construction':
                            document={'schema':'xar.ck3.construction_formal_pending_v1','pending':{'episode_run_id':tests._FRAME['episode_run_id']},'applied':None}
                            (directory/'construction-formal-pending-v1.json').write_text(json.dumps(document),encoding='utf-8')
                        else:
                            document={'schema':'xar.ck3.first-heir-marriage-formal.v1','pending':None,'resolved':{'status':'synthetic-changed'}}
                            (directory/'first-heir-marriage-formal-v1.json').write_text(json.dumps(document),encoding='utf-8')
                    return observed
                driver.take_internal_semantic_snapshot=snapshot
                def profiler(frame,event,value):
                    if frame.f_code is module.query_m5_peacetime_proposal_sources_v1.__code__ and event=='return':
                        for key in ('construction','faction','family_status','family_plan','family_plans'):
                            if key in frame.f_locals: local[key]=copy.deepcopy(frame.f_locals[key])
                with contextlib.ExitStack() as stack:
                    stack.enter_context(patch.object(module,'query_construction_private',return_value=building))
                    if setting.get('released'):
                        stack.enter_context(patch.object(module,'construction_process_identity',observed_process))
                        stack.enter_context(patch('xar_autoplayer.bridge.domain_construction_private_transport_v1._identity',observed_process))
                    for role,method in names:
                        original=getattr(module,method)
                        def traced(path,original=original,role=role):
                            observed=original(path); reads[role].append(copy.deepcopy(observed)); return observed
                        stack.enter_context(patch.object(module,method,traced))
                    sys.setprofile(profiler)
                    try:
                        produced=NativeHeadlessGameplayDriver.query_m5_joint_proposal_sources_private_v1(driver,snapshot=before,history=tests._history(count=count),baseline_plan=baseline,expected_revision=tests._FRAME['revision'])
                        accepted=True; failure=None
                    except Exception as error:
                        produced=None; accepted=False; failure={'type':type(error).__name__,'message':str(error)}
                    finally: sys.setprofile(None)
                producer_read_counts={role:len(values) for role,values in reads.items()}
                failure_closure=[]
                if not accepted:
                    for role,method in names:
                        while len(reads[role])<2:
                            reads[role].append(copy.deepcopy(getattr(module,method)(directory)))
                            failure_closure.append(role)
                if any(len(values)!=2 for values in reads.values()):
                    raise RuntimeError('complete initial/final original ledger observations required')
                ledgers_before={role:values[0] for role,values in reads.items()}
                ledgers_after={role:values[-1] for role,values in reads.items()}
                process_observation=({'kind':'observed','pid':process_reads[-1][0],'creation_date':process_reads[-1][1]} if process_reads else {'kind':'unavailable'})
                inputs={'schema':'xar.java.m5-peacetime-assembly.v1','before':before,'expected_revision':tests._FRAME['revision'],'reader':{'kind':'returned','snapshot':snapshots[-1] if snapshots else None},'baseline_plan':baseline,'ledgers_before':ledgers_before,'ledgers_after':ledgers_after,'construction_process':process_observation,'construction':local.get('construction',building),'faction':local.get('faction',driver._faction),'family':{'status':local.get('family_status','opt_in_off'),'plan':local.get('family_plan'),'plans':local.get('family_plans',[])}}
                sample={'name':name,'input':inputs,'accepted':accepted,'actual_native_driver_entry_executed':True,'reader_calls':len(snapshots),'producer_ledger_read_counts':producer_read_counts,'capture_failure_closure_reads':failure_closure,'process_fixture_read_count':len(process_reads),'failure':failure}
                if accepted:
                    sample['source_sha256']=hashlib.sha256(canonical(produced)).hexdigest()
                    sample['domain_order']=list(produced['domains'])
                    collected=collect_m5_formal_proposals(snapshot=before,sources=produced)
                    sample['collector']={key:collected[key] for key in ('collected_domains','collected_candidate_ids')}
                    sample['collector']['analysis_sha256']=hashlib.sha256(canonical(collected['dispatch']['analysis'])).hexdigest()
                    sample['actual_collector_executed']=True
                cases.append(sample)
            if source_pins()!=sources_before: raise RuntimeError('original source graph changed during capture')
            if effective_test_pins()!=effective_tests_before: raise RuntimeError('corrected shared test-source module changed during capture')
            result={'schema':'xar.java.peacetime-assembly-producer-golden.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'sources':sources_before,'source_postcheck':'MATCH','original_tests_run':execution.testsRun,'original_failures':len(execution.failures),'original_errors':len(execution.errors),'original_skipped':len(execution.skipped),'original_expected_failures':len(execution.expectedFailures),'original_unexpected_successes':len(execution.unexpectedSuccesses),'fixture_boundary':'original complete query/NativeDriver method and collector; domain native DTOs and observed process identity are synthetic fixtures; failed-source closure ledger reads are explicit supplemental original-reader observations','effective_test_source_corrections':{'schema':'xar.m5-shared-test-fixture-corrections/v1','sources':effective_tests_before,'normal_full_suite_no_policy_patch':True},'canonical_ledger_write_count':0,'game_rpc_count':0,'production_cutover':False,'cases':cases}
            encoded=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode('utf-8')
            if len(encoded)>1048576: raise RuntimeError('bounded full producer golden exceeds 1MiB raw; no truncation')
            sys.stdout.buffer.write(encoded)
            """;
    public static void main(String[] args) throws Exception {
        if (args.length != 5) throw new IllegalArgumentException("python repo new-output new-fixture-dir machine required");
        Path python = Path.of(args[0]).toAbsolutePath().normalize(), repo = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize(), fixture = Path.of(args[3]).toAbsolutePath().normalize();
        Path rawOutput = output.resolveSibling(output.getFileName() + ".raw.json");
        Path allowed = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch").toAbsolutePath().normalize();
        if (!Files.isRegularFile(python) || Files.exists(output) || Files.exists(rawOutput) || Files.exists(fixture) || !output.startsWith(allowed) || !fixture.startsWith(allowed)
                || !output.getFileName().toString().endsWith(".json.gz") || output.startsWith(fixture) || fixture.startsWith(output)
                || args[4].isBlank()) throw new IllegalArgumentException("fresh bounded disjoint D scratch outputs required");
        Files.createDirectories(output.getParent()); Files.createDirectory(fixture);
        Path correctedTests = materializeSharedTestFixture(repo, fixture);
        Files.createFile(rawOutput);
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-X", "utf8", "-B", "-", repo.toString(), fixture.toString(), args[4]);
        builder.directory(repo.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("TEMP", fixture.toString()); builder.environment().put("TMP", fixture.toString());
        builder.environment().put("PYTHONPATH", correctedTests + ";" + repo.resolve("ck3_autonomous_player/src") + ";" + repo.resolve("ck3_autonomous_player/tests/unit") + ";" + repo.resolve("tools"));
        builder.redirectOutput(rawOutput.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        try (var stdin = process.getOutputStream()) { stdin.write(SCRIPT.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
        if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(); throw new IllegalStateException("capture timed out; evidence retained"); }
        if (process.exitValue() != 0 || Files.size(rawOutput) == 0 || Files.size(rawOutput) > 1_048_576) throw new IllegalStateException("capture failed or exceeded bounded output; evidence retained");
        byte[] raw = Files.readAllBytes(rawOutput); ByteArrayOutputStream compressed = new ByteArrayOutputStream();
        try (GZIPOutputStream stream = new GZIPOutputStream(compressed)) { stream.write(raw); }
        byte[] zipped = compressed.toByteArray();
        if (zipped.length > 65_536) throw new IllegalStateException("compressed full producer golden exceeds 64KiB; raw retained");
        Files.write(output, zipped, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        try (var stream = new java.util.zip.GZIPInputStream(Files.newInputStream(output))) {
            if (!java.util.Arrays.equals(raw, stream.readAllBytes())) throw new IllegalStateException("gzip readback differs; both files retained");
        }
        Files.delete(rawOutput);
        System.out.println("Peacetime complete query/collector raw_bytes=" + raw.length + " gzip_bytes=" + zipped.length + "; verified redundant raw removed");
    }

    private record FixtureEdit(String beforeBase64, String afterBase64) { }
    /** Materialize the reviewed shared test-source correction; no test method or business policy is replaced at runtime. */
    private static Path materializeSharedTestFixture(Path repo, Path fixture) throws Exception {
        Path relative = Path.of("ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py");
        byte[] original = Files.readAllBytes(repo.resolve(relative));
        if (original.length != 70537 || !digest(original).equals("f6c49d48bf9fee0f47a85aba2fc787e4cd9196332baac31814bc59e8fc953e6b"))
            throw new IllegalArgumentException("shared test fixture preimage drift");
        String source = new String(original, java.nio.charset.StandardCharsets.UTF_8);
        for (FixtureEdit edit : java.util.List.of(
                new FixtureEdit("ICAgIGRlZiB0ZXN0X201X3NlbGVjdGVkX2dpZnRfdXNlc19leGlzdGluZ19wcmVfc3VibWl0X2NoZWNrcG9pbnRfZ2F0ZShzZWxmKSAtPiBOb25lOgogICAgICAgIGRyaXZlciA9IF9Ecml2ZXIoc2VsZi5zdGF0ZV9kaXIpCiAgICAgICAgZHJpdmVyLmFsbG93X3ByaXZhdGVfZmFjdGlvbl9naWZ0X2Zvcm1hbF90cmlhbCA9IFRydWUKICAgICAgICBkcml2ZXIuY2FwYWJpbGl0aWVzID0gbGFtYmRhOiB7CiAgICAgICAgICAgICJhY3Rpb25fc3RlcHMiOiBbImxpZmUtYWR2YW5jZSIsICJzYXZlLWNoZWNrcG9pbnQiLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgIEZBQ1RJT05fR0lGVF9TVUJNSVRfU1RFUF0sCg==", "ICAgIGRlZiB0ZXN0X201X3NlbGVjdGVkX2dpZnRfdXNlc19leGlzdGluZ19wcmVfc3VibWl0X2NoZWNrcG9pbnRfZ2F0ZShzZWxmKSAtPiBOb25lOgogICAgICAgIGRyaXZlciA9IF9Ecml2ZXIoc2VsZi5zdGF0ZV9kaXIpCiAgICAgICAgZHJpdmVyLmFsbG93X3ByaXZhdGVfZmFjdGlvbl9naWZ0X2Zvcm1hbF90cmlhbCA9IFRydWUKICAgICAgICAjIFRoaXMgaXMgYSBjdXJyZW50IHNhbWUtZnJhbWUgbmF0aXZlIERUTyBmaXh0dXJlLCBub3QgYSByZWFkaW5lc3MgZmxhZy4KICAgICAgICBkcml2ZXIuX3NuYXBzaG90WyJuYXRpdmVfY29tbWFuZF9oaXN0b3J5Il0uYXBwZW5kKHsKICAgICAgICAgICAgImNvbW1hbmQiOiAicXVlcnktcGxheWVyLWZhY3Rpb24tYWxlcnRzLXYxIiwgIm9rIjogVHJ1ZSwKICAgICAgICAgICAgInJlc3VsdCI6IHsicGxheWVyX2ZhY3Rpb25fYWxlcnRzIjogewogICAgICAgICAgICAgICAgInN0YXR1cyI6ICJhdmFpbGFibGUiLCAic25hcHNob3RfcmV2aXNpb24iOiBfRlJBTUVbIm5hdGl2ZV9yZXZpc2lvbiJdLAogICAgICAgICAgICAgICAgImRhdGVfcmF3IjogX0ZSQU1FWyJkYXRlX3JhdyJdLCAicGxheWVyX2NoYXJhY3Rlcl9pZCI6IDI5ODI5LAogICAgICAgICAgICAgICAgInJlYWRpbmVzcyI6IHsidGFyZ2V0aW5nX3Jvd3NfcmVhZHkiOiBUcnVlLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAic3RvY2tfZGFuZ2Vyb3VzX3ByZWRpY2F0ZV9yZWFkeSI6IFRydWUsICJzYW1lX2ZyYW1lX3JlYWR5IjogVHJ1ZX0sCiAgICAgICAgICAgICAgICAidGFyZ2V0aW5nX2ZhY3Rpb25zIjogW3siZmFjdGlvbl9pZCI6IDgwMSwgInRhcmdldF9jaGFyYWN0ZXJfaWQiOiAyOTgyOSwKICAgICAgICAgICAgICAgICAgICAibGVhZGVyX2NoYXJhY3Rlcl9pZCI6IDQxMDAzLCAiY2hhcmFjdGVyX21lbWJlcl9pZHMiOiBbNDEwMDNdLAogICAgICAgICAgICAgICAgICAgICJkYW5nZXJvdXNfYnlfc3RvY2tfcnVsZSI6IFRydWUsICJmYWN0aW9uX2F0X3dhciI6IEZhbHNlfV0sCiAgICAgICAgICAgIH19LAogICAgICAgIH0pCiAgICAgICAgZHJpdmVyLmNhcGFiaWxpdGllcyA9IGxhbWJkYTogewogICAgICAgICAgICAiYWN0aW9uX3N0ZXBzIjogWyJsaWZlLWFkdmFuY2UiLCAic2F2ZS1jaGVja3BvaW50IiwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICBGQUNUSU9OX0dJRlRfU1VCTUlUX1NURVBdLAo="),
                new FixtureEdit("ICAgICAgICAgICAgcmV0dXJuX3ZhbHVlPWRlZXBjb3B5KGJhc2VsaW5lKSwKICAgICAgICApOgogICAgICAgICAgICBwbGFubmVkID0gR2FtZXBsYXlCcmlkZ2VTZXJ2aWNlKGRyaXZlcikucGxhbl90dXJuKCkKICAgICAgICBzZWxmLmFzc2VydEVxdWFsKHBsYW5uZWRbInBsYW4iXSwgYmFzZWxpbmUpCiAgICAgICAgc2VsZi5hc3NlcnRFcXVhbChkcml2ZXIuc291cmNlX3JlYWRzLCAwKQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwoZHJpdmVyLmZhY3Rpb25fcmVhZHMsIDApCgogICAgZGVmIHRlc3RfcHJpdmF0ZV9jbGlfZmxhZ19pc19leHBsaWNpdF9hbmRfZGVmYXVsdF9vZmYoc2VsZikgLT4gTm9uZToKICAgICAgICBkZWZhdWx0cyA9IGNsaS5wYXJzZXIoKS5wYXJzZV9hcmdzKFsK", "ICAgICAgICAgICAgcmV0dXJuX3ZhbHVlPWRlZXBjb3B5KGJhc2VsaW5lKSwKICAgICAgICApOgogICAgICAgICAgICBwbGFubmVkID0gR2FtZXBsYXlCcmlkZ2VTZXJ2aWNlKGRyaXZlcikucGxhbl90dXJuKCkKICAgICAgICBjb250cm9sID0gX0RyaXZlcihzZWxmLnN0YXRlX2RpciAvICJvcmRpbmFyeS1jb250cm9sIiwgZW5hYmxlZD1GYWxzZSwgZ2lmdF9lbmFibGVkPUZhbHNlKQogICAgICAgIGRlbCBjb250cm9sLmFsbG93X3ByaXZhdGVfbTVfam9pbnRfY29sbGVjdG9yCiAgICAgICAgd2l0aCBtb2NrLnBhdGNoKCJ4YXJfYXV0b3BsYXllci5icmlkZ2Uuc2VydmljZS5jaG9vc2Vfb25lX2xpZmVfdHVybiIsCiAgICAgICAgICAgICAgICAgICAgICAgIHJldHVybl92YWx1ZT1kZWVwY29weShiYXNlbGluZSkpOgogICAgICAgICAgICBvcmRpbmFyeSA9IEdhbWVwbGF5QnJpZGdlU2VydmljZShjb250cm9sKS5wbGFuX3R1cm4oKQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwocGxhbm5lZFsicGxhbiJdLCBvcmRpbmFyeVsicGxhbiJdKQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwoe2tleTogcGxhbm5lZFsicGxhbiJdW2tleV0gZm9yIGtleSBpbiBiYXNlbGluZX0sIGJhc2VsaW5lKQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwoZHJpdmVyLnNvdXJjZV9yZWFkcywgMCkKICAgICAgICBzZWxmLmFzc2VydEVxdWFsKGRyaXZlci5mYWN0aW9uX3JlYWRzLCAwKQogICAgICAgIHNlbGYuYXNzZXJ0RXF1YWwoY29udHJvbC5zb3VyY2VfcmVhZHMsIDApCiAgICAgICAgc2VsZi5hc3NlcnRFcXVhbChjb250cm9sLmZhY3Rpb25fcmVhZHMsIDApCgogICAgZGVmIHRlc3RfcHJpdmF0ZV9jbGlfZmxhZ19pc19leHBsaWNpdF9hbmRfZGVmYXVsdF9vZmYoc2VsZikgLT4gTm9uZToKICAgICAgICBkZWZhdWx0cyA9IGNsaS5wYXJzZXIoKS5wYXJzZV9hcmdzKFsK"))) {
            String before = new String(java.util.Base64.getDecoder().decode(edit.beforeBase64()), java.nio.charset.StandardCharsets.UTF_8);
            String after = new String(java.util.Base64.getDecoder().decode(edit.afterBase64()), java.nio.charset.StandardCharsets.UTF_8);
            int position = source.indexOf(before);
            if (position < 0 || source.indexOf(before, position + before.length()) >= 0)
                throw new IllegalArgumentException("one exact shared test fixture hunk required");
            source = source.substring(0, position) + after + source.substring(position + before.length());
        }
        byte[] corrected = source.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        if (corrected.length != 71945 || !digest(corrected).equals("01644bf52b25ef0b3de5a4cc92e2de7bed4a5d63ad3f6b5cb088d6d21334a6a6"))
            throw new IllegalStateException("shared test fixture final pin differs");
        Path root = fixture.resolve("test-sources").normalize();
        Path target = root.resolve(relative).normalize();
        if (!target.startsWith(root)) throw new IllegalArgumentException("test fixture path escaped");
        Files.createDirectories(target.getParent());
        Files.write(target, corrected, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        return target.getParent();
    }
    private static String digest(byte[] raw) throws Exception {
        return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));
    }
}

