package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Executes the actual original pure producers in a separate process; no generated Python module or production fallback. */
final class MercenaryProcurementProducerParityTest {
    private static final String EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String SCRIPT="""
import json,sys
from xar_autoplayer.war_strategic_reserve_v1 import observe_post_hire_inventory_v1,observe_first_raised_inventory_v1
from xar_autoplayer.war_emergency_budget_v1 import observe_emergency_recovery_v1
p=json.load(sys.stdin)
result=[]
for c in p:
    result.append({'post':observe_post_hire_inventory_v1(c['snapshot'],c['claim']),
        'first':observe_first_raised_inventory_v1(c['snapshot'],c['claim']),
        'recovery':observe_emergency_recovery_v1(c['snapshot'],{'pending':c['claim'],'observed':[]},None)})
json.dump(result,sys.stdout,separators=(',',':'))
""";
    private static Obj row(String json) { return object(parse(json.getBytes(StandardCharsets.UTF_8)),"test original"); }
    private static Obj snapshot() {
        return row("""
{"played_character":{"character_id":1,"alive":true},"native_revision":11,"date_raw":100,"snapshot_id":"native-11","revision":11,"episode_run_id":"actual-episode",
"paused":true,"map_ready":true,"active_wars":[],"player_armies":[{"army_id":1,"soldiers":50,"current_province_id":12,"controllable":true},
{"army_id":4294967294,"soldiers":100,"current_province_id":12,"controllable":true}],"played_character_gold":{"raw":49000000,"scale":100000}}
""");
    }
    private static Obj claim() {
        return row("""
{"action_request_id":"native-original-request","company_id":0,"status":"submission_unresolved","pre_capture_epoch":18446744073709551615,
"pre_player_army_ids":[1],"source_frame":{"played_character_id":1,"native_revision":10,"date_raw":100,"snapshot_id":"native-10","revision":10,"episode_run_id":"actual-episode"},
"decision":{"selected_candidate":{"company_id":0,"gold_cost_raw":1000000,"predicted_auto_raise_province_id":12,"purpose_war_ids":[],"finance":{"observed_treasury_raw":50000000}}}}
""");
    }
    private static MercenaryProcurement.Ledger ledger(Obj claim) {
        return MercenaryProcurement.decode(encode(OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",claim,"observed",new Arr(List.of()))));
    }
    @Test void actualOriginalInventoryFirstMilestoneAndRecoveryMatchFullIdJavaConsumer()throws Exception {
        Obj actual=snapshot(),pending=claim();var initial=ledger(pending);var original=initial.pending().orElseThrow();
        var first=MercenaryProcurement.firstRaised(actual,original).orElseThrow();
        Obj saved=pending.with("first_raised_inventory_observation_v1",first);
        Obj moved=actual.with("native_revision",new IntegerValue(BigInteger.valueOf(12))).with("revision",new IntegerValue(BigInteger.valueOf(12)))
                .with("snapshot_id",new Text("native-12")).with("player_armies",new Arr(List.of(row("{\"army_id\":4294967294,\"soldiers\":80,\"current_province_id\":88,\"controllable\":true}"))));
        Obj zero=actual.with("player_armies",new Arr(List.of(row("{\"army_id\":0,\"soldiers\":20,\"current_province_id\":12,\"controllable\":true}"))));
        Obj wrongCount=actual.with("player_armies",new Arr(List.of(row("{\"army_id\":4294967294,\"soldiers\":true,\"current_province_id\":12,\"controllable\":true}"))));
        List<Obj> snapshots=List.of(actual,moved,zero,wrongCount);List<Obj> claims=List.of(pending,saved,pending,pending);
        var inputs=new java.util.ArrayList<Value>();for(int i=0;i<snapshots.size();i++)inputs.add(OrdinaryFinanceCollector.obj("snapshot",snapshots.get(i),"claim",claims.get(i)));
        JsonNode oracle=original(new Arr(inputs));assertEquals(4,oracle.size());
        for(int i=0;i<snapshots.size();i++) {
            var c=ledger(claims.get(i));var p=c.pending().orElseThrow();
            assertEquals(oracle.get(i).get("post"),toNode(MercenaryProcurement.postInventory(snapshots.get(i),p)));
            assertEquals(oracle.get(i).get("first"),toNode(MercenaryProcurement.firstRaised(snapshots.get(i),p).<Value>map(value->value).orElse(Nil.INSTANCE)));
            assertEquals(oracle.get(i).get("recovery"),toNode(MercenaryProcurement.recovery(snapshots.get(i),c,java.util.Optional.empty()).<Value>map(value->value).orElse(Nil.INSTANCE)));
        }
        assertEquals(first,MercenaryProcurement.firstRaised(moved,ledger(saved).pending().orElseThrow()).orElseThrow());
        var updated=MercenaryProcurement.refreshInventory(initial,actual);assertEquals(updated.original(),MercenaryProcurement.decode(MercenaryProcurement.encode(updated)).original());
        assertFalse(bool(MercenaryProcurement.postInventory(actual,original).get("payment_verified"),"payment"));
        assertFalse(bool(first.get("company_to_new_army_binding_verified"),"company attribution"));
    }
    @Test void retainedFirstInventoryCannotAssertCreationOrCompanyAttribution() {
        Obj actual=snapshot();Obj originalClaim=claim();
        Obj prior=MercenaryProcurement.firstRaised(actual,ledger(originalClaim).pending().orElseThrow()).orElseThrow();
        assertEquals(new Bool(false),prior.get("army_creation_verified"));
        assertEquals(new Bool(false),prior.get("company_to_new_army_binding_verified"));
        Obj moved=actual.with("native_revision",new IntegerValue(BigInteger.valueOf(12))).with("revision",new IntegerValue(BigInteger.valueOf(12)))
                .with("snapshot_id",new Text("native-12")).with("player_armies",new Arr(List.of(row("{\"army_id\":4294967294,\"soldiers\":80,\"current_province_id\":88,\"controllable\":true}"))));
        List<Obj> corrupted=List.of(prior.with("army_creation_verified",new Bool(true)),
                prior.with("company_to_new_army_binding_verified",new Bool(true)),
                prior.with("army_creation_verified",new Bool(true)).with("company_to_new_army_binding_verified",new Bool(true)));
        Obj decision=object(originalClaim.get("decision"),"original decision");
        Obj selected=object(decision.get("selected_candidate"),"original selected company");
        Obj settledBase=originalClaim.with("status",new Text("employment_observed")).with("decision",decision.with("selected_candidate",
                selected.with("purpose_war_ids",new Arr(List.of(new IntegerValue(BigInteger.ONE))))));
        var checks=new java.util.ArrayList<org.junit.jupiter.api.function.Executable>();
        for(Obj current:List.of(actual,moved))for(Obj unsupported:corrupted) {
            var pending=ledger(originalClaim.with("first_raised_inventory_observation_v1",unsupported));
            var returned=MercenaryProcurement.firstRaised(current,pending.pending().orElseThrow());
            var refreshed=MercenaryProcurement.refreshInventory(pending,current);
            var restored=MercenaryProcurement.decode(MercenaryProcurement.encode(refreshed));
            Obj retained=object(restored.pending().orElseThrow().original().get("first_raised_inventory_observation_v1"),"retained real first inventory");
            Obj post=object(restored.pending().orElseThrow().original().get("post_hire_observations_v1"),"independent current inventory");
            // Pure barrier DATA: these objects never issue an Applied receipt or actual Root permission.
            Obj relevant=current.with("active_wars",new Arr(List.of(OrdinaryFinanceCollector.obj("war_id",new IntegerValue(BigInteger.ONE)))));
            var observedControl=MercenaryProcurement.decode(encode(OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",Nil.INSTANCE,
                    "observed",new Arr(List.of(settledBase.with("first_raised_inventory_observation_v1",prior))))));
            var observedMetadata=MercenaryProcurement.decode(encode(OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",Nil.INSTANCE,
                    "observed",new Arr(List.of(settledBase.with("first_raised_inventory_observation_v1",unsupported))))));
            checks.add(()->assertAll("unsupported positive facts cannot be promoted by retained inventory",
                    ()->assertTrue(returned.isPresent(),"real retained inventory milestone remains present without causal proof"),
                    ()->assertEquals(new Bool(false),returned.map(value->value.get("army_creation_verified")).orElse(Nil.INSTANCE)),
                    ()->assertEquals(new Bool(false),returned.map(value->value.get("company_to_new_army_binding_verified")).orElse(Nil.INSTANCE)),
                    ()->assertEquals(prior.get("source_frame"),returned.map(value->value.get("source_frame")).orElse(Nil.INSTANCE)),
                    ()->assertEquals(new Bool(false),retained.get("army_creation_verified")),
                    ()->assertEquals(new Bool(false),retained.get("company_to_new_army_binding_verified")),
                    ()->assertEquals(new Bool(false),post.get("payment_verified")),
                    ()->assertEquals(MercenaryProcurement.Status.SUBMISSION_UNRESOLVED,restored.pending().orElseThrow().status()),
                    ()->assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(current,restored)),
                    ()->assertEquals(MercenaryProcurement.NewHireBarrier.CLEAR,MercenaryProcurement.barrier(relevant,observedControl)),
                    ()->assertEquals(MercenaryProcurement.barrier(relevant,observedControl),MercenaryProcurement.barrier(relevant,observedMetadata))));
        }
        assertAll(checks);
    }
    @Test void retainedFirstInventoryPreservesAbsentAndNullOptionalFacts() {
        Obj actual=snapshot();Obj originalClaim=claim();
        Obj prior=MercenaryProcurement.firstRaised(actual,ledger(originalClaim).pending().orElseThrow()).orElseThrow();
        Obj moved=actual.with("native_revision",new IntegerValue(BigInteger.valueOf(12))).with("revision",new IntegerValue(BigInteger.valueOf(12)))
                .with("snapshot_id",new Text("native-12")).with("player_armies",new Arr(List.of(row("{\"army_id\":4294967294,\"soldiers\":80,\"current_province_id\":88,\"controllable\":true}"))));
        for(String flag:List.of("army_creation_verified","company_to_new_army_binding_verified")) {
            var absent=new java.util.LinkedHashMap<String,Value>(prior.members());absent.remove(flag);
            for(Obj unknown:List.of(new Obj(absent),prior.with(flag,Nil.INSTANCE))) {
                var pending=ledger(originalClaim.with("first_raised_inventory_observation_v1",unknown));
                Obj returned=MercenaryProcurement.firstRaised(moved,pending.pending().orElseThrow()).orElseThrow();
                assertEquals(unknown,returned);assertEquals(unknown.members().containsKey(flag),returned.members().containsKey(flag));
                var refreshed=MercenaryProcurement.refreshInventory(pending,moved);
                var restored=MercenaryProcurement.decode(MercenaryProcurement.encode(refreshed));
                Obj retained=object(restored.pending().orElseThrow().original().get("first_raised_inventory_observation_v1"),"retained unknown metadata");
                assertEquals(unknown,retained);assertEquals(unknown.members().containsKey(flag),retained.members().containsKey(flag));
                assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(moved,restored));
            }
        }
    }
    @Test void unknownSurvivesOtherEpisodeAndExactFrameRejectionPreventsRetry() {
        var pending=ledger(claim());Obj other=snapshot().with("episode_run_id",new Text("replacement-episode"));
        assertEquals(pending.original(),MercenaryProcurement.refreshInventory(pending,other).original());
        assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(other,pending));
        Obj rejection=claim().with("status",new Text("native_rejected"));
        Obj rejected=OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",Nil.INSTANCE,"observed",new Arr(List.of(rejection)));
        Obj exact=snapshot().with("native_revision",new IntegerValue(BigInteger.TEN)).with("revision",new IntegerValue(BigInteger.TEN)).with("snapshot_id",new Text("native-10"));
        assertEquals(MercenaryProcurement.NewHireBarrier.SAME_FRAME_REJECTION,MercenaryProcurement.barrier(exact,MercenaryProcurement.decode(encode(rejected))));
        assertThrows(IllegalArgumentException.class,()->ledger(claim().with("pre_capture_epoch",new Bool(true))));
        assertThrows(IllegalArgumentException.class,()->ledger(claim().with("company_id",new IntegerValue(new BigInteger("4294967295")))));
        assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.decode(encode(rejected.with("pending",new Bool(false)))));
    }
    @Test void postInventoryDistinguishesAbsentNullAndMalformedPresentWallets() {
        Obj actual=snapshot();var pending=ledger(claim()).pending().orElseThrow();
        var members=new java.util.LinkedHashMap<String,Value>(actual.members());members.remove("played_character_gold");
        for(Obj unknown:List.of(new Obj(members),actual.with("played_character_gold",Nil.INSTANCE))) {
            Obj post=MercenaryProcurement.postInventory(unknown,pending);
            assertEquals(Nil.INSTANCE,post.get("post_treasury_raw"));assertEquals(Nil.INSTANCE,post.get("treasury_delta_raw"));
            var refreshed=MercenaryProcurement.refreshInventory(ledger(claim()),unknown);
            assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(unknown,refreshed));
            assertEquals(refreshed.original(),MercenaryProcurement.decode(MercenaryProcurement.encode(refreshed)).original());
        }
        Obj wallet=object(actual.get("played_character_gold"),"original wallet");
        List<Value> malformed=List.of(new Bool(true),new Arr(List.of()),
                wallet.with("scale",new IntegerValue(BigInteger.ONE)),wallet.with("scale",new Bool(true)),
                wallet.with("raw",new Bool(true)),row("{\"raw\":1.0,\"scale\":100000}"),wallet.with("raw",new Text("100")),
                new Obj(java.util.Map.of("scale",new IntegerValue(BigInteger.valueOf(100000)))),wallet.with("raw",Nil.INSTANCE),
                new Obj(java.util.Map.of("raw",new IntegerValue(BigInteger.ONE))),
                wallet.with("raw",new IntegerValue(BigInteger.ONE.shiftLeft(63))),
                wallet.with("raw",new IntegerValue(BigInteger.ONE.shiftLeft(63).negate().subtract(BigInteger.ONE))));
        var checks=new java.util.ArrayList<org.junit.jupiter.api.function.Executable>();
        for(Value invalid:malformed)checks.add(()->assertThrows(IllegalArgumentException.class,
                ()->MercenaryProcurement.postInventory(actual.with("played_character_gold",invalid),pending)));
        assertAll("present malformed native wallet must not become unavailable or unchecked cash",checks);
    }
    @Test void postInventoryRetainsSignedInt64WalletAndExactBigIntegerDelta() {
        Obj actual=snapshot();var pending=ledger(claim()).pending().orElseThrow();
        for(BigInteger raw:List.of(BigInteger.valueOf(1000000),BigInteger.valueOf(-1000000),
                BigInteger.valueOf(Long.MIN_VALUE),BigInteger.valueOf(Long.MAX_VALUE))) {
            Obj wallet=OrdinaryFinanceCollector.obj("raw",new IntegerValue(raw),"scale",new IntegerValue(BigInteger.valueOf(100000)));
            Obj post=MercenaryProcurement.postInventory(actual.with("played_character_gold",wallet),pending);
            assertEquals(new IntegerValue(raw),post.get("post_treasury_raw"));
            assertEquals(new IntegerValue(raw.subtract(BigInteger.valueOf(50000000))),post.get("treasury_delta_raw"));
        }
    }
    @Test void exactQuoteAndFreshControllableArmyRemainUnqualifiedAfterRefreshAndSerde() {
        Obj actual=snapshot();var original=ledger(claim());
        Obj post=MercenaryProcurement.postInventory(actual,original.pending().orElseThrow());
        assertEquals(new IntegerValue(BigInteger.valueOf(-1000000)),post.get("treasury_delta_raw"));
        assertEquals(new IntegerValue(BigInteger.valueOf(1000000)),post.get("quoted_contract_gold_raw"));
        var armies=array(post.get("new_observed_player_armies"),"new independent inventory");assertEquals(1,armies.size());
        Obj army=object(armies.getFirst(),"new inventory row");
        assertEquals(new IntegerValue(new BigInteger("4294967294")),army.get("army_id"));assertEquals(new Bool(true),army.get("controllable"));
        assertEquals(new IntegerValue(BigInteger.valueOf(12)),army.get("current_province_id"));
        var refreshed=MercenaryProcurement.refreshInventory(original,actual);
        var restored=MercenaryProcurement.decode(MercenaryProcurement.encode(refreshed));assertEquals(refreshed.original(),restored.original());
        var retained=restored.pending().orElseThrow();assertEquals(MercenaryProcurement.Status.SUBMISSION_UNRESOLVED,retained.status());
        assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(actual,restored));
        Obj persisted=object(retained.original().get("post_hire_observations_v1"),"retained independent wallet and inventory");
        assertEquals(post,persisted);
        for(String flag:List.of("payment_verified","army_creation_verified","company_to_new_army_binding_verified"))
            assertEquals(new Bool(false),persisted.get(flag));
        Obj first=object(retained.original().get("first_raised_inventory_observation_v1"),"retained first independent army milestone");
        assertEquals(new Bool(false),first.get("army_creation_verified"));
        assertEquals(new Bool(false),first.get("company_to_new_army_binding_verified"));
    }
    @Test void actualHireAckTermsRemainAdmissionAndRejectWrongFrameMirrorAndBooleanIdentity() {
        Obj actual=snapshot().with("diagnostics",row("{\"hello\":{\"expected_ck3_version\":\"1.20.0.4\",\"expected_ck3_sha256\":\""+EXE+"\"}}"));
        Obj result=ack();var accepted=HireMercenaryAck.decodeNativeResult(result,actual,BigInteger.ZERO);
        assertEquals(HireMercenaryAck.Status.SUBMITTED,accepted.status());assertFalse(accepted.employmentVerified());assertFalse(accepted.paymentVerified());assertFalse(accepted.availableArmyVerified());
        assertThrows(IllegalArgumentException.class,()->HireMercenaryAck.decodeNativeResult(result.with("date_raw",new IntegerValue(BigInteger.valueOf(101))),actual,BigInteger.ZERO));
        Obj action=object(result.get("mercenary_hire"),"action");
        Obj rejected=action.with("status",new Text("rejected")).with("command_submitted",new Bool(false)).with("verification_pending",new Bool(false));
        assertTrue(HireMercenaryAck.decodeNativeResult(result.with("mercenary_hire",rejected).with("accepted",new Bool(false)).with("status",new Text("rejected")),actual,BigInteger.ZERO).knownRejectedWithoutSubmission());
        Obj ambiguous=rejected.with("command_submitted",new Bool(true));
        assertFalse(HireMercenaryAck.decodeNativeResult(result.with("mercenary_hire",ambiguous).with("accepted",new Bool(false)).with("status",new Text("rejected")),actual,BigInteger.ZERO).knownRejectedWithoutSubmission());
        assertThrows(IllegalArgumentException.class,()->HireMercenaryAck.decodeNativeResult(result.with("mercenary_hire",action.with("company_id",new Bool(false))),actual,BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class,()->HireMercenaryAck.decodeNativeResult(result.with("mercenary_hire",action.with("after_state_observed",new Bool(true))),actual,BigInteger.ZERO));
        Obj terms=object(action.get("final_terms"),"terms");assertThrows(IllegalArgumentException.class,()->NativeMercenaryMarket.decodeTerms(terms.with("resource_costs_raw",new Arr(List.of(new IntegerValue(BigInteger.ZERO))))));
    }
    @Test void originalReducersRetireOnlyTheExplicitlyMatchedZeroDispatchCandidate() {
        var pending=ledger(claim());var source=new org.xar.ck3.control.contracts.ExactRef(Path.of("target","original-zero-dispatch.json").toAbsolutePath().toString(),1,"a".repeat(64));
        var zero=new org.xar.ck3.control.application.action.NativeActionPort.ZeroDispatchProof(org.xar.ck3.control.application.action.NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"actual original transport refused before write",java.util.Optional.empty());
        var evidence=new MercenaryProcurement.ZeroDispatchEvidence(source,zero);
        assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.rejectBeforeDispatch(pending,"other-request",evidence));
        var rejected=MercenaryProcurement.rejectBeforeDispatch(pending,"native-original-request",evidence);
        assertTrue(rejected.pending().isEmpty());assertEquals(MercenaryProcurement.Status.NATIVE_REJECTED,rejected.observed().getFirst().status());
        assertEquals(BigInteger.ZERO,integer(object(rejected.observed().getFirst().original().get("zero_dispatch_proof"),"actual zero source").get("request_bytes_written"),"written bytes"));
        assertThrows(IllegalArgumentException.class,()->new org.xar.ck3.control.application.action.NativeActionPort.ZeroDispatchProof(org.xar.ck3.control.application.action.NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,1,"partially sent is UNKNOWN",java.util.Optional.empty()));
        var baseline=new org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Baseline(BigInteger.valueOf(44),BigInteger.valueOf(55),BigInteger.TEN,BigInteger.TEN,BigInteger.valueOf(100),BigInteger.ONE,
                BigInteger.valueOf(50000000),BigInteger.ZERO,BigInteger.valueOf(150000),BigInteger.valueOf(75000),List.of(BigInteger.valueOf(55)),BigInteger.valueOf(1000000),BigInteger.valueOf(25));
        var begin=new org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.BeginRequest("gift-zero","episode","R10",
                new org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity(BigInteger.ONE,"2026-10-23T00:00:00Z"),baseline,BigInteger.valueOf(10000000),"a".repeat(64));
        var gift=org.xar.ck3.control.wave2.finance.giftpending.GiftPendingReducer.begin(org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger.empty(),begin);
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.wave2.finance.giftpending.GiftPendingReducer.rejectBeforeDispatch(gift,"other-request"));
        var complete=org.xar.ck3.control.wave2.finance.giftpending.GiftPendingReducer.rejectBeforeDispatch(gift,"gift-zero");assertTrue(complete.pending().isEmpty());
        assertEquals(org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ResolvedOutcome.UNCHANGED,complete.resolvedRequestOutcomes().get("gift-zero"));
        assertEquals(complete,org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec.decodeLedger(org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec.encodeLedger(complete)));
    }
    private static Obj ack() { return row(("""
{"step":"hire-mercenary-v1","game_version":"1.20.0.4","executable_sha256":"%s","read_only":false,"command_sequence":18446744073709551615,
"snapshot_revision":11,"date_raw":100,"accepted":true,"status":"submitted_verification_pending","mercenary_hire":{"schema":"ck3_12004_mercenary_hire_action_v1","status":"submitted",
"snapshot_revision":11,"date_raw":100,"company_id":0,"native_hire_mode":1,"actor_character_id":1,"company_resolved":true,"native_command_validation_observable":true,
"native_command_valid":true,"command_submitted":true,"verification_pending":true,"prior_employer_character_id":null,"unavailable_reason":null,"after_state_observed":false,
"final_terms":{"available":true,"unavailable_reason":null,"can_hire":true,"can_afford":true,"payment_status":2,"resource_scale":100000,"resource_costs_raw":[1000000,0,0,0,0,0,0,0,0,0],
"hire_duration_months":36,"can_hire_reasons_available":true,"can_hire_reason_literal":"","can_afford_reasons_available":true,"can_afford_reason_literal":""}}}
""").formatted(EXE)); }
    private static JsonNode original(Arr input)throws Exception {
        String configured=System.getProperty("xar.repository.root");assertNotNull(configured,"actual Python producer required; missing environment is not a skip");
        Path root=Path.of(configured).toAbsolutePath().normalize();Path source=root.resolve("ck3_autonomous_player/src/xar_autoplayer/war_strategic_reserve_v1.py");
        assertEquals("75abecd194804000e4595c899f3c788bb66a90fb0cbb9622ee6fa07b473b992c",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source))));
        for(var pin:java.util.Map.of("war_emergency_budget_v1.py","e85888d3167c8069c78812a1fad644b9d9f7400e349b191453f3cc16714b8614",
                "war_reinforcement_tradeoff_v1.py","d9f32c208fa47a0b2007f4a5194462a9929fac2f636c8e58ba25a8cffb1a089c").entrySet())
            assertEquals(pin.getValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(root.resolve("ck3_autonomous_player/src/xar_autoplayer/").resolve(pin.getKey())))));
        var builder=new ProcessBuilder(System.getProperty("xar.python","python"),"-c",SCRIPT).directory(root.toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        Process process=builder.start();
        try(var reader=java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            var originalOutput=reader.submit(()->process.getInputStream().readNBytes(1048577));
            try {
                try(var stdin=process.getOutputStream()) { stdin.write(encode(input)); }
                assertTrue(process.waitFor(45,TimeUnit.SECONDS),"actual original producer timed out");
                byte[] output=originalOutput.get(5,TimeUnit.SECONDS);
                assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8));assertTrue(output.length<=1048576,"bounded original fixture result required");return StrictJson.parse(output);
            } finally { if(process.isAlive()){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);} }
        }
    }
}
