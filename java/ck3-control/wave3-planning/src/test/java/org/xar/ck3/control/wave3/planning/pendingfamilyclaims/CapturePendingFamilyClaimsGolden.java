package org.xar.ck3.control.wave3.planning.pendingfamilyclaims;

import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import java.util.zip.GZIPOutputStream;

/** Original Python producers, explicit source-guarded fixture correction, and real consumers; no native qualification. */
public final class CapturePendingFamilyClaimsGolden {
    private CapturePendingFamilyClaimsGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("root python output required");
        Path root = Path.of(args[0]).toRealPath(), output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) throw new IllegalArgumentException("new capture output required");
        Path fixtureDirectory = output.resolveSibling(output.getFileName().toString() + ".fixtures");
        if (Files.exists(fixtureDirectory)) throw new IllegalArgumentException("new fixture directory required");
        String script = """
                import sys, pathlib, runpy, copy, json, hashlib, datetime, unittest
                root=pathlib.Path(sys.argv[1]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit'),str(root/'tools')]
                from ck3_live_run_id import current_machine_id
                from xar_autoplayer.m5_peacetime_proposal_sources_v1 import _pending_family_commitments as family, _pending_child_default_commitments as child
                from xar_autoplayer.bridge.driver import BridgeUnavailableError
                from xar_autoplayer.m5_formal_proposal_collector import collect_m5_formal_proposals as collect
                t=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_m5_child_default_pending_commitments.py'))
                family_source=root/'ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py'
                family_bytes=family_source.read_bytes()
                if len(family_bytes)!=89022 or hashlib.sha256(family_bytes).hexdigest()!='ab8266d89836d8bd7cbafcc8a6a074b6eab76ca6340594909c1ccd1ca6a8aabc':raise AssertionError('legacy family test source drift')
                fixture_before='                          forecast["unobserved_at_submission"])\\n            self.assertEqual(forecast["missing_preproposal_fields"], [])\\n            claims = _pending_family_commitments(pending, frame)\\n'
                fixture_after='                          forecast["unobserved_at_submission"])\\n            # This retained1.19.0.6 source did not observe the later fertility/scorer getters.\\n            # Keep those native inputs unknown rather than inventing a complete forecast.\\n            missing_fields = [\\n                "heir_native_fertility",\\n                "candidate_native_fertility",\\n                "native_candidate_fertility_floor_raw",\\n                "candidate_native_fertility_floor_comparison_v1",\\n                "heir_native_scorer_age_override_raw",\\n                "candidate_native_scorer_age_override_raw",\\n                "native_candidate_scorer_age_upper_raw",\\n                "heir_native_scorer_effective_age_v1",\\n                "candidate_native_scorer_effective_age_v1",\\n                "candidate_native_scorer_age_branch_v1",\\n            ]\\n            self.assertEqual(forecast["missing_preproposal_fields"], missing_fields)\\n            for field in missing_fields:\\n                self.assertIsNone(forecast[field])\\n            claims = _pending_family_commitments(pending, frame)\\n'
                if family_bytes.count(fixture_before.encode('utf-8'))!=1:raise AssertionError('legacy family fixture hunk mismatch')
                effective_bytes=family_bytes.replace(fixture_before.encode('utf-8'),fixture_after.encode('utf-8'))
                if len(effective_bytes)!=89909 or hashlib.sha256(effective_bytes).hexdigest()!='d575b1bf98cbb07d656c841e93423fc8a96481c0378159d042abf97612fed559':raise AssertionError('effective family fixture source drift')
                fixture_dir=pathlib.Path(sys.argv[2]);fixture_dir.mkdir(exist_ok=False)
                effective_family=fixture_dir/'test_family_marriage_formal_consumer.py'
                with effective_family.open('xb') as target:target.write(effective_bytes)
                effective_test_sources=[{'original_path':str(family_source),'original_bytes':len(family_bytes),'original_sha256':hashlib.sha256(family_bytes).hexdigest(),'effective_path':str(effective_family),'effective_bytes':len(effective_bytes),'effective_sha256':hashlib.sha256(effective_bytes).hexdigest(),'correction':'retained 1.19.0.6 r0255 has ten unobserved native fertility/scorer fields; assert exact missing order and each null; no producer/native edits','governance_patch_sha256':'e7029607359b87f061817e8ea05b837e131b6dee1ca3554262b563da12748d61'}]
                f=runpy.run_path(str(effective_family))
                suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(t['M5ChildDefaultPendingCommitmentsTests']),f['FamilyConsumerTest']('test_r0255_same_age_external_betrothal_has_value_without_realm_alliance')])
                run=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
                if not run.wasSuccessful():raise SystemExit(7)
                frame=copy.deepcopy(t['_FRAME']);actor=frame['played_character_id'];episode=frame['episode_run_id']
                family_base={'played_character_id':actor,'episode_run_id':episode,'heir_character_id':38822,'candidate_character_id':38718,'recipient_character_id':32897}
                child_base={'played_character_id':actor,'episode_run_id':episode,'heir_character_id':38988,'candidate_character_id':37909,'recipient_character_id':34332,'selected_value_projection':{'generic_costs':{'gold_raw':0,'application_timing':'on_send'},'possible_alliance_pairs':[{'first_character_id':actor,'second_character_id':37909,'would_attempt_if_accepted':False}]}}
                cases=[]
                def add(name,operation,pending,observed=None):
                    observed=copy.deepcopy(frame if observed is None else observed);pending=copy.deepcopy(pending)
                    request={'schema':'xar.java.pending-family-claims-request.v1','operation':operation,'frame':observed,'pending':pending}
                    try:cases.append({'name':name,'input':request,'accepted':True,'expected':(family if operation=='family' else child)(copy.deepcopy(pending),observed)})
                    except BridgeUnavailableError as error:cases.append({'name':name,'input':request,'accepted':False,'error_type':type(error).__name__,'error':str(error)})
                add('family-none','family',None)
                add('family-historical-conservative','family',family_base)
                add('family-explicit-attempt','family',{**family_base,'preproposal_realm_alliance_attempt_if_accepted':True})
                add('family-no-alliance-betrothal','family',{**family_base,'preproposal_realm_alliance_attempt_if_accepted':False})
                add('family-recipient-is-candidate','family',{**family_base,'recipient_character_id':family_base['candidate_character_id']})
                add('family-recipient-is-heir','family',{**family_base,'recipient_character_id':family_base['heir_character_id']})
                add('family-exact-large-identity','family',{**family_base,'heir_character_id':2**80,'candidate_character_id':2**80+1,'recipient_character_id':2**80+2})
                later={**frame,'native_revision':frame['native_revision']+10,'revision':frame['revision']+10,'date_raw':frame['date_raw']+1,'snapshot_id':'native:later'}
                add('family-claims-persist-in-next-frame','family',family_base,later)
                add('family-opaque-ledger-extension','family',{**family_base,'future_observation':{'rate':1.5,'missing':None}})
                for key,value in [('played_character_id',actor+1),('episode_run_id','other'),('heir_character_id',True),('candidate_character_id',0),('recipient_character_id',1.0),('preproposal_realm_alliance_attempt_if_accepted',None)]:add('family-invalid-'+key,'family',{**family_base,key:value})
                add('family-same-subject-candidate','family',{**family_base,'candidate_character_id':family_base['heir_character_id']})
                add('family-recipient-is-actor','family',{**family_base,'recipient_character_id':actor})
                missing=copy.deepcopy(family_base);del missing['heir_character_id'];add('family-missing-heir','family',missing)
                add('family-not-object','family',[])
                add('child-none','child_default',None)
                add('child-no-attempt','child_default',child_base)
                add('child-recipient-is-actor','child_default',{**child_base,'recipient_character_id':actor})
                add('child-recipient-is-subject','child_default',{**child_base,'recipient_character_id':child_base['heir_character_id']})
                add('child-claims-persist-in-next-frame','child_default',child_base,later)
                pairs=[{'first_character_id':actor,'second_character_id':34332,'would_attempt_if_accepted':True},{'first_character_id':37909,'second_character_id':actor,'would_attempt_if_accepted':True},{'first_character_id':actor,'second_character_id':34332,'would_attempt_if_accepted':True},{'first_character_id':actor,'second_character_id':actor,'would_attempt_if_accepted':True},{'first_character_id':888,'second_character_id':999,'would_attempt_if_accepted':True},{'first_character_id':actor,'second_character_id':777,'would_attempt_if_accepted':False}]
                allies=copy.deepcopy(child_base);allies['selected_value_projection']['possible_alliance_pairs']=pairs;add('child-current-actor-alliance-union','child_default',allies)
                empty=copy.deepcopy(child_base);empty['selected_value_projection']['possible_alliance_pairs']=[];add('child-observed-empty-pairs','child_default',empty)
                for key,value in [('played_character_id',actor+1),('episode_run_id','other'),('heir_character_id',actor),('candidate_character_id',38988),('recipient_character_id',True)]:add('child-invalid-'+key,'child_default',{**child_base,key:value})
                for key,value in [('application_timing','on_acceptance')]:
                    bad=copy.deepcopy(child_base);bad['selected_value_projection']['generic_costs'][key]=value;add('child-invalid-'+key,'child_default',bad)
                for key,value in [('first_character_id',1.0),('second_character_id',0),('would_attempt_if_accepted',1)]:
                    bad=copy.deepcopy(child_base);bad['selected_value_projection']['possible_alliance_pairs'][0][key]=value;add('child-invalid-pair-'+key,'child_default',bad)
                bad=copy.deepcopy(child_base);del bad['selected_value_projection'];add('child-missing-projection','child_default',bad)
                bad=copy.deepcopy(child_base);bad['selected_value_projection']['possible_alliance_pairs']=None;add('child-null-pairs','child_default',bad)
                consumers=[]
                for clear in (False,True):
                    case=t['M5ChildDefaultPendingCommitmentsTests']('test_pending_claims_survive_disabled_submit_and_leave_actor_available');case.setUp()
                    try:
                        before=copy.deepcopy(case.ledger)
                        if clear:case.ledger['resolved']={'status':'betrothal','source_pending':copy.deepcopy(case.ledger['pending'])};case.ledger['pending']=None;case._write_ledger()
                        ledger_before=case.ledger_path.read_bytes();sources,driver=case._query();snapshot=driver.take_snapshot()
                        original=collect(snapshot=copy.deepcopy(snapshot),sources=copy.deepcopy(sources))
                        if case.ledger_path.read_bytes()!=ledger_before:raise AssertionError('query changed pending ledger')
                        pending=copy.deepcopy(case.ledger['pending']);claims=child(pending,frame)
                        consumers.append({'name':'real-query-cleared'if clear else'real-query-pending','claims_request':{'schema':'xar.java.pending-family-claims-request.v1','operation':'child_default','frame':frame,'pending':pending},'expected_claims':claims,'intake_request':{'schema':'xar.java.m5-formal-intake-request.v1','snapshot':snapshot,'sources':sources},'expected_analysis':original['dispatch']['analysis'],'ledger_unchanged':True,'submission_enabled':driver.allow_private_guy_default_formal_trial})
                    finally:case.tearDown()
                paths=['ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py','ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py','ck3_autonomous_player/tests/unit/test_m5_child_default_pending_commitments.py','ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py','ck3_autonomous_player/tests/unit/test_family_marriage_formal_consumer.py']
                print(json.dumps({'schema':'xar.java.pending-family-claims-producer-golden.v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()}for p in paths],'effective_test_sources':effective_test_sources,'original_tests_run':run.testsRun,'original_test_failures':len(run.failures),'original_test_errors':len(run.errors),'qualification':'unchanged pure producers and real mock-driver query/collector consumer; no native or writer qualification','cases':cases,'consumers':consumers},ensure_ascii=False,separators=(',',':')))
                """;
        Path temporary = Files.createTempFile(Path.of(System.getProperty("java.io.tmpdir")), "pendingclaims-", ".json");
        try {
            ProcessBuilder builder = new ProcessBuilder(args[1], "-B", "-X", "utf8", "-", root.toString(), fixtureDirectory.toString());
            builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
            builder.environment().put("TEMP", System.getProperty("java.io.tmpdir")); builder.environment().put("TMP", System.getProperty("java.io.tmpdir"));
            builder.redirectError(ProcessBuilder.Redirect.INHERIT); builder.redirectOutput(temporary.toFile());
            Process process = builder.start();
            try {
            try (var stdin = process.getOutputStream()) { stdin.write(script.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
            if (!process.waitFor(60, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); throw new IllegalStateException("producer timeout"); }
            if (process.exitValue() != 0 || Files.size(temporary) > 524288) throw new IllegalStateException("producer RED/oversized exit=" + process.exitValue() + " bytes=" + Files.size(temporary));
            ByteArrayOutputStream compressed = new ByteArrayOutputStream();
            try (GZIPOutputStream gzip = new GZIPOutputStream(compressed)) { gzip.write(Files.readAllBytes(temporary)); }
            byte[] golden = compressed.toByteArray(); if (golden.length > 49152) throw new IllegalStateException("compressed golden exceeds 48 KiB");
            Files.createDirectories(output.getParent()); Files.write(output, golden, java.nio.file.StandardOpenOption.CREATE_NEW);
            System.out.println("raw_bytes=" + Files.size(temporary) + " gzip_bytes=" + golden.length);
            } finally {
                if (process.isAlive()) {
                    process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                    process.waitFor(5, TimeUnit.SECONDS);
                }
            }
        } finally { Files.deleteIfExists(temporary); }
    }
}
