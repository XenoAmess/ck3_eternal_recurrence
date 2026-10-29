package org.xar.ck3.control.planning.opportunity;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import java.io.ByteArrayOutputStream;
import java.util.zip.GZIPOutputStream;

/** Explicit one-time producer capture, outside default JUnit; invokes existing Python code unchanged. */
public final class CaptureOpportunityGolden {
    private CaptureOpportunityGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) throw new IllegalArgumentException("root python output required");
        Path root = Path.of(arguments[0]).toRealPath(); Path output = Path.of(arguments[2]).toAbsolutePath();
        String script = """
                import sys, runpy, json, copy, hashlib, pathlib, datetime, unittest
                root=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(root/'ck3_autonomous_player/src')); sys.path.insert(0,str(root/'tools'))
                from ck3_live_run_id import current_machine_id
                t=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_m5_observed_opportunity_selector.py'))
                z=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_m5_public_army_zero_claims.py'))
                from xar_autoplayer.m5_observed_opportunity_selector import select_observed_m5_opportunity as select
                suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(t['M5ObservedOpportunitySelectorTests']),unittest.defaultTestLoader.loadTestsFromTestCase(z['PublicArmyZeroClaimsTests'])])
                result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
                if not result.wasSuccessful(): raise SystemExit(7)
                cases=[]
                def add(name, proposals, snapshot=None, commitments=None, reserve=0, cap=1):
                    args={'snapshot':t['_snapshot']() if snapshot is None else snapshot,'proposals':proposals,'commitments':t['_commitments']() if commitments is None else commitments,'gold_reserve_raw':reserve,'max_active_wars':cap}
                    cases.append({'name':name,'input':args,'expected':select(**copy.deepcopy(args))})
                council=t['_council']; building=t['_construction']; gift=t['_gift']
                add('formal-three', [council(),building(),gift()],reserve=5000000)
                add('seat-conflict',[council(),building(),gift()],commitments=t['_commitments'](commitment_keys=['council-seat:councillor_steward']),reserve=5000000)
                expensive=building(); expensive['gold_cost_raw']=16000001
                add('gold-boundary-over',[expensive,gift()],snapshot=t['_snapshot'](gold_raw=36000000),reserve=5000000)
                add('empty',[])
                a=t['_heir_betrothal'](38710,32266,9300000,alliance_attempt=True)
                b=t['_heir_betrothal'](38718,32897,5500000,alliance_attempt=False)
                add('family-acceptance-before-ally-count',[b,a],cap=0)
                add('family-ally-conflict',[a,b],commitments=t['_commitments'](ally_character_ids=[32266]),cap=0)
                add('family-cross-domain',[b,building(),a],cap=0)
                c=copy.deepcopy(a); c['candidate_id']='marriage:unknown'; c['evidence'].pop('heir_adult_measure_raw')
                add('family-unknown-not-zero',[c,b],cap=0)
                defensive=t['_defensive_snapshot']()
                continuation=t['active_defensive_war_continuation_proposal'](frame=t['_FRAME'],snapshot=defensive,plan=t['_defensive_plan'](),observation=t['_continuation_observation']())
                add('defender-existing-slot',[continuation],snapshot=defensive)
                deficit=copy.deepcopy(continuation); deficit['projected_supply_margin_raw']=-1
                add('negative-supply',[deficit],snapshot=defensive)
                entry=copy.deepcopy(continuation); entry['war_slot_claim']=1; entry.pop('war_operation')
                add('entry-normalized-capacity',[entry],snapshot=defensive)
                blocked=copy.deepcopy(defensive); blocked['player_armies'][0]['controllable']=False
                add('army-not-controllable',[continuation],snapshot=blocked)
                add('zero-public-army',[z['continuation']()],snapshot=z['snapshot'](),commitments=z['commitments']())
                query,decision=t['_wartime_lifestyle']()
                perk=t['wartime_lifestyle_perk_proposal'](frame=t['_FRAME'],query=query,decision=decision,current_war_plan=t['_defensive_plan']())
                add('wartime-perk',[perk],snapshot=defensive)
                peace=t['_snapshot'](); peace['player_armies']=[]
                income=building(); income['evidence']['authored_monthly_income_hundredths']=1
                danger=gift(); danger['evidence']['stock_threat_response']={'status':'observed','dangerous_response_ready':True}
                add('peace-danger-before-income',[income,danger],snapshot=peace)
                watch=copy.deepcopy(danger); watch['evidence']['stock_threat_response']['dangerous_response_ready']=False
                add('peace-income-before-watch',[income,watch],snapshot=peace)
                unknown=copy.deepcopy(income); unknown['evidence']['authored_monthly_income_hundredths']=None
                add('income-null-not-positive',[unknown,watch],snapshot=peace)
                decimal=copy.deepcopy(income); decimal['evidence']['authored_monthly_income_hundredths']=1.5
                add('income-float-not-integer',[decimal,watch],snapshot=peace)
                extension=gift(); extension['future_domain_evidence']={'null':None,'empty':[],'unicode':'漢字😀'}; extension.pop('war_operation')
                extension['character_ids']=[41004,41003]
                add('extension-and-sorted-claims',[extension])
                huge=gift(); huge['gold_cost_raw']=2**80
                add('arbitrary-precision-budget',[huge],snapshot=t['_snapshot'](gold_raw=2**81),commitments=t['_commitments'](gold_raw=2**79),reserve=2**78)
                exact=gift(); add('gold-exact-boundary',[exact],snapshot=t['_snapshot'](gold_raw=12000000))
                low=t['_snapshot'](gold_raw=-1); add('negative-treasury-rejects-choice',[gift()],snapshot=low)
                tie1=gift(); tie2=copy.deepcopy(tie1); tie1['candidate_id']='diplomacy:😀'; tie2['candidate_id']='diplomacy:￿'
                add('unicode-scalar-order',[tie1,tie2])
                add('first-conflict-reason-before-slot',[entry],snapshot=defensive,commitments=t['_commitments'](army_ids=[71]),cap=0)
                paths=['ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py','ck3_autonomous_player/src/xar_autoplayer/m5_war_cash_resource_v1.py','ck3_autonomous_player/src/xar_autoplayer/lifestyle_min_policy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py','ck3_autonomous_player/tests/unit/test_m5_observed_opportunity_selector.py','ck3_autonomous_player/tests/unit/test_m5_public_army_zero_claims.py']
                provenance=[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths]
                print(json.dumps({'schema':'xar.java.m5-opportunity-producer-golden.v1','machine_id':current_machine_id(),'machine_identity_source':'tools/ck3_live_run_id.py current_machine_id','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':provenance,'original_tests_run':result.testsRun,'original_test_failures':len(result.failures),'original_test_errors':len(result.errors),'cases':cases},ensure_ascii=False,separators=(',',':')))
                """;
        ProcessBuilder builder = new ProcessBuilder(arguments[1], "-X", "utf8", "-c", script, root.toString());
        builder.directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Path temporary = Files.createTempFile(Path.of(System.getProperty("java.io.tmpdir")), "opportunity-producer-", ".json");
        try {
            builder.redirectOutput(temporary.toFile()); Process process = builder.start();
            if (!process.waitFor(30, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                process.waitFor(5, TimeUnit.SECONDS);
                throw new IllegalStateException("producer timeout");
            }
            if (process.exitValue() != 0 || Files.size(temporary) > 524288)
                throw new IllegalStateException("producer capture failed/raw corpus exceeds 512 KiB: exit="
                        + process.exitValue() + " raw_bytes=" + Files.size(temporary));
            byte[] captured = Files.readAllBytes(temporary);
            if (new String(captured, StandardCharsets.UTF_8).isBlank()) throw new IllegalStateException("empty producer output");
            ByteArrayOutputStream compressed = new ByteArrayOutputStream();
            try (GZIPOutputStream gzip = new GZIPOutputStream(compressed)) { gzip.write(captured); }
            byte[] golden = compressed.toByteArray();
            if (golden.length > 131072) throw new IllegalStateException("compressed corpus exceeds 128 KiB");
            Files.createDirectories(output.getParent()); Files.write(output, golden);
            System.out.println("producer golden raw_bytes=" + captured.length + " compressed_bytes=" + golden.length + " output=" + output);
        } finally { Files.deleteIfExists(temporary); }
    }
}
