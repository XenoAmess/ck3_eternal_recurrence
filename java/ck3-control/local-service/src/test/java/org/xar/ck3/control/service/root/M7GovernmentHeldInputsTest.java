package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure DATA comparison only. No Root context, installed READ, private issuer or Native completion is fabricated. */
final class M7GovernmentHeldInputsTest {
    private static final Instant AT=Instant.parse("2026-11-03T00:00:00Z");
    private static final String HEAD="a".repeat(64);
    private static final long DATE=53_169_072;

    @Test void onlyOriginalOrdinaryObjectGoalIsEligibleForTheOptionalRead() {
        var empty=new OpportunityJson.Obj(Map.of());
        var ordinary=new OpportunityJson.Obj(Map.of("lifecycle",new OpportunityJson.Text("ordinary_campaign_succession")));
        assertFalse(RootDriverGovernancePublicService.m7GovernmentEligible(empty));
        assertFalse(RootDriverGovernancePublicService.m7GovernmentEligible(empty.with("campaign_goal",OpportunityJson.Nil.INSTANCE).with("succession_lifecycle",ordinary)));
        assertFalse(RootDriverGovernancePublicService.m7GovernmentEligible(empty.with("campaign_goal",empty)));
        assertFalse(RootDriverGovernancePublicService.m7GovernmentEligible(empty.with("campaign_goal",empty).with("succession_lifecycle",new OpportunityJson.Text("ordinary_campaign_succession"))));
        assertFalse(RootDriverGovernancePublicService.m7GovernmentEligible(empty.with("campaign_goal",empty).with("succession_lifecycle",ordinary.with("lifecycle",new OpportunityJson.Text("one_life_pact")))));
        assertTrue(RootDriverGovernancePublicService.m7GovernmentEligible(empty.with("campaign_goal",empty).with("succession_lifecycle",ordinary)));
        // Eligibility is only a shape gate. The real producer still needs its actual guard/receipt/goal decode.
        assertFalse(RootDriverGovernancePublicService.m7GovernmentEligible(empty.with("campaign_goal",new OpportunityJson.Text("{}")) .with("succession_lifecycle",ordinary)));
    }

    @Test void equalRebuiltFrameDriverAndAnotherScopeCannotReplaceHeldObjects() {
        var f=new Fixture();
        assertTrue(f.matches(f.scope,f.request,f.frame,f.driver,HEAD));
        var rebuilt=new Complete(f.frame.identity(),f.frame.source(),f.frame.sessionId(),f.frame.connectionGeneration(),
                f.frame.semantic(),f.frame.originalEvidence(),f.frame.observedAt(),f.frame.fullBindingSha256());
        assertEquals(f.frame,rebuilt);assertNotSame(f.frame,rebuilt);
        assertFalse(f.matches(f.scope,f.request,rebuilt,f.driver,HEAD));
        var copied=new DriverSnapshotFacts.Known(f.driver.driver(),f.driver.stamp(),f.driver.originalHistoryBasis(),
                f.driver.actionRows(),f.driver.auxiliary(),f.driver.loop(),f.driver.observation());
        assertEquals(f.driver,copied);assertNotSame(f.driver,copied);
        assertFalse(f.matches(f.scope,f.request,f.frame,copied,HEAD));
        assertFalse(f.matches(new InertScope(),f.request,f.frame,f.driver,HEAD));
        assertFalse(f.matches(f.scope,f.request,f.frame,f.driver,"b".repeat(64)));
    }

    @Test void finalRequestMustPreserveSourceSessionIdentityAndWholeSemanticSnapshot() {
        var f=new Fixture();
        var equalRequest=new PlanningRequest(f.request.before(),f.request.source(),f.request.sessionId(),f.request.deadline(),f.request.observations());
        assertTrue(f.matches(f.scope,equalRequest,f.frame,f.driver,HEAD));
        var otherSource=new G2Source("m7-government-data",AT.toString(),"data-v1",ref("other-source"));
        assertFalse(f.matches(f.scope,new PlanningRequest(f.request.before(),otherSource,f.request.sessionId(),f.request.deadline(),f.request.observations()),f.frame,f.driver,HEAD));
        assertFalse(f.matches(f.scope,new PlanningRequest(f.request.before(),f.source,"different-session",f.request.deadline(),f.request.observations()),f.frame,f.driver,HEAD));
        var changed=f.observations(f.frame.semantic().with("campaign_goal",OpportunityJson.Nil.INSTANCE));
        assertFalse(f.matches(f.scope,new PlanningRequest(f.request.before(),f.source,f.request.sessionId(),f.request.deadline(),changed),f.frame,f.driver,HEAD));
        var otherActor=new Fixture(74);
        assertFalse(f.matches(f.scope,otherActor.request,f.frame,f.driver,HEAD));
    }

    @Test void originalNativeTokensPreserveOpaqueDecimalsButCannotInventAnUnavailableActor() {
        var f=new Fixture();
        var snapshot=org.xar.ck3.control.contracts.StrictJson.object();
        snapshot.setAll((com.fasterxml.jackson.databind.node.ObjectNode)DriverJson.toNode(f.frame.semantic()));
        var hello=snapshot.putObject("diagnostics").putObject("hello");
        hello.put("expected_ck3_version","1.20.0.4");
        hello.put("expected_ck3_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        String adapter="{\"schema\":\"government-runtime-adapter-v1\",\"schema_version\":1,"
                +"\"build\":{\"version\":\"1.20.0.4\",\"exe_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\"},"
                +"\"provenance\":{\"backend_id\":\"ck3-1.20.0.4-private-government-runtime-adapter-v1\","
                +"\"campaign_backend_id\":\"ck3-1.20.0.4-native-campaign-root-context-v1\",\"feature_backend_id\":\"ck3-1.20.0.4-native-loaded-feature-manifest-v1\"},"
                +"\"snapshot_revision\":9,\"player_character_id\":73,\"status\":\"unavailable\",\"unavailable_reason\":\"controlled-data-unavailable\","
                +"\"readiness\":{\"same_frame_ready\":false,\"core_adapter_ready\":false},\"opaque_metric\":1.5}";
        var original=new org.xar.ck3.control.application.action.RawJson(bytes(adapter));
        assertTrue(RootDriverGovernancePublicService.m7GovernmentObservedActorMatches(original,BigInteger.valueOf(73)));
        var context=RootDriverGovernancePublicService.m7GovernmentContext(snapshot,original);
        assertEquals(org.xar.ck3.control.wave2.governance.government.GovernmentContext.Status.UNAVAILABLE,context.status());
        assertFalse(context.identityObservationReady());assertFalse(context.ordinaryGoalContextReady());
        var retained=org.xar.ck3.control.contracts.StrictJson.parse(context.governmentRuntimeAdapterWire().getBytes(StandardCharsets.UTF_8));
        assertEquals(new java.math.BigDecimal("1.5"),retained.get("opaque_metric").decimalValue());
        var missingActor=new org.xar.ck3.control.application.action.RawJson(bytes(adapter.replace("\"player_character_id\":73,","")));
        assertFalse(RootDriverGovernancePublicService.m7GovernmentObservedActorMatches(missingActor,BigInteger.valueOf(73)));
        var otherActor=new org.xar.ck3.control.application.action.RawJson(bytes(adapter.replace("\"player_character_id\":73","\"player_character_id\":74")));
        assertFalse(RootDriverGovernancePublicService.m7GovernmentObservedActorMatches(otherActor,BigInteger.valueOf(73)));
        var floatIdentity=new org.xar.ck3.control.application.action.RawJson(bytes(adapter.replace("\"snapshot_revision\":9","\"snapshot_revision\":9.0")));
        assertThrows(IllegalArgumentException.class,()->RootDriverGovernancePublicService.m7GovernmentContext(snapshot,floatIdentity));
        // These are controlled pure codec inputs; no received Native/HELLO/source qualification is claimed.
    }

    private static final class Fixture {
        final InertScope scope=new InertScope();
        final GameGeneration game=new GameGeneration(321,new PythonOnlyUInt64(BigInteger.ONE));
        final G2Source source=new G2Source("m7-government-data",AT.toString(),"data-v1",ref("source"));
        final OrdinaryCampaignGoal.Goal goal;
        final Complete frame;
        final DriverSnapshotFacts.Known driver;
        final PlanningRequest request;
        Fixture() { this(73); }
        Fixture(long actor) {
            goal=OrdinaryCampaignGoal.newGoal("government-data-campaign",actor);
            var rawGoal=new DriverStateSnapshot.Value(GoalCodec.encodeGoal(goal));
            var lifecycle=DriverJson.object(bytes("{\"lifecycle\":\"ordinary_campaign_succession\"}"),65536);
            var originalDriver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-pipe",321,BigInteger.valueOf(actor),"episode-data"),List.of(),
                    new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),
                    new DriverStateSnapshot.Value(OpportunityJson.encode(lifecycle)),rawGoal,new DriverStateSnapshot.Value(bytes("[]")));
            driver=new DriverSnapshotFacts.Known(originalDriver,new DriverSnapshotFacts.Stamp(1,1,game,"episode-data",DriverJson.sha256(originalDriver.encode())),
                    ref("driver-basis"),List.of(),new OpportunityJson.Obj(Map.of()),Optional.empty(),Optional.empty());
            var identity=new ObservationIdentity("m7-government-data",game,new JointBudgetSelector.ProposalFrame(
                    new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(9),BigInteger.valueOf(DATE)),"snapshot-data",BigInteger.valueOf(14),"episode-data"),1);
            var semantic=DriverJson.object(bytes("{\"paused\":true,\"map_ready\":true,\"revision\":14,\"native_revision\":9,\"date_raw\":"+DATE
                    +",\"snapshot_id\":\"snapshot-data\",\"episode_run_id\":\"episode-data\",\"played_character\":{\"character_id\":"+actor
                    +",\"alive\":true},\"active_wars\":[],\"player_armies\":[]}"),65536)
                    .with("campaign_goal",OpportunityJson.parse(GoalCodec.encodeGoal(goal))).with("succession_lifecycle",lifecycle);
            frame=new Complete(identity,source,"session-data",BigInteger.ONE,semantic,ref("native-data"),AT,"c".repeat(64));
            request=new PlanningRequest(identity,source,"session-data",AT.plusSeconds(60),observations(semantic));
        }
        PlanningObservation observations(OpportunityJson.Obj snapshot) {
            return new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.of(goal),Optional.empty(),false);
        }
        boolean matches(ContinuityStorePort.Session current,PlanningRequest actual,Complete full,DriverSnapshotFacts.Known known,String head) {
            return RootDriverGovernancePublicService.m7GovernmentMatches(scope,frame,driver,HEAD,current,actual,full,known,head);
        }
    }
    /** Reference identity token for a pure comparator, not an owned writer or installed Root permission. */
    private static final class InertScope implements ContinuityStorePort.Session {
        public void requireWriter(Path path){throw new AssertionError("no writer permission in DATA test");}
        public WriterContracts.Pin capturePin(ExactRef ref,int max){throw new AssertionError("no file access");}
        public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("no file access");}
        public WriterContracts.Head head(){throw new AssertionError("pure comparator must not access a ledger");}
        public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("no preview");}
        public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("no commit");}
        public ExactRef persistedHead(){throw new AssertionError("no ledger");}
    }
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static ExactRef ref(String value){byte[] raw=bytes(value);return new ExactRef("software-only-"+DriverJson.sha256(raw),raw.length,DriverJson.sha256(raw));}
}
