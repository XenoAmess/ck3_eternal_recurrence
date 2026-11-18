package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Synthetic DATA tests exercise production split/adapter paths, and mint no Root or live qualification. */
final class RootGuardianCurrentArchiveSplitTest {
    private static final Instant NOW=Instant.parse("2026-11-18T00:00:00Z");
    private static final ExactRef REF=new ExactRef("synthetic-source",1,"a".repeat(64));
    @TempDir Path temporary;
    private static G2Source source(String build){return new G2Source("synthetic-guardian",NOW.toString(),build,REF);}
    private static ObservationIdentity identity(){
        var game=new GameGeneration(991,new PythonOnlyUInt64(BigInteger.valueOf(19)));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(17),BigInteger.ONE,BigInteger.TEN),
                "synthetic-frame",BigInteger.TWO,"synthetic-episode");
        return new ObservationIdentity("synthetic-guardian",game,frame,1);
    }
    private static Context context(){return new Context(identity(),source(Build.CROZIER4.sha256()),"synthetic-session",BigInteger.ONE,
            Build.CROZIER4,NOW.plusSeconds(30),new ControlFrame(true,true,true,1,17L,17,"synthetic-episode",false,null,null,List.of()));}
    private static PlanningReadRequest request(){var c=context();return new PlanningReadRequest(c.before(),c.source(),c.sessionId(),
            new OperationKey(OrdinaryInteractionCodec.QUERY_STEP),new OpportunityJson.Obj(java.util.Map.of()),c.deadline());}
    private static PlanningReadGuard guard(){var r=request();var binding=new GuardEvidence(r.before(),r.source(),r.sessionId(),BigInteger.ONE,
            r.operation(),REF,REF,"synthetic-authority",NOW,NOW.plusSeconds(30));
        return new PlanningReadGuard(binding,true,true,true,"b".repeat(64));}
    private static ReadContract<OrdinaryContext> ordinary(){return new ReadContract<>("interactions:ordinary-query",
            new OperationKey(OrdinaryInteractionCodec.QUERY_STEP),Optional.of(OrdinaryInteractionCodec.QUERY_CAPABILITY),
            OrdinaryInteractionCodec.QUERY_CAPABILITY,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
            ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,REF,
            (r,id)->{throw new AssertionError("no Native preparation in this split test");},
            r->{throw new AssertionError("no live decode in this split test");},
            r->{throw new AssertionError("no borrowed ordinary replay in this split test");});}
    private ExactRef profile()throws Exception {var p=temporary.resolve("profile.java");var bytes="synthetic profile".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(p,bytes);return new ExactRef(p.toString(),bytes.length,ActionCodec.sha256(bytes));}
    private static GuardianReconciliationQueries.CanonicalAdmission noAdmission(){return new GuardianReconciliationQueries.CanonicalAdmission(){
        @Override public void verifyCurrent(PlanningReadRequest r){throw new AssertionError("archive profile cannot admit a current read");}
        @Override public void verifyOriginal(PlanningReadReceipt r){throw new AssertionError("this test has no original Root authority");}
    };}
    private GuardianReconciliationQueries selected(String version,String sha)throws Exception {return RootGuardianReconciliationReads.createQueries(
            ordinary(),KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(version,sha),profile(),noAdmission());}

    @Test void exact1210SelectsActualArchiveProductWithoutQualifyingTheCurrentBuild()throws Exception {
        var build=ExactCk3Build.CK3_1210;var configured=KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(build.version(),build.executableSha256());
        assertFalse(configured.qualified());assertThrows(IllegalStateException.class,configured::requireQualified);
        var queries=selected(build.version(),build.executableSha256());assertFalse(queries.liveReadsEnabled());
        assertTrue(queries.contract().hasPureReplay());assertSame(REF,queries.contract().sourceRef());
        assertEquals(ReadContract.GuardMode.RECONCILIATION_OBSERVATION,queries.contract().guardMode());
        assertThrows(IllegalStateException.class,queries::requireLiveReads);
        assertThrows(IllegalArgumentException.class,()->selected(build.version(),"0".repeat(64)));
    }
    @Test void originalCurrentFourRemainsLiveAndOtherLegacyProfilesRemainRejected()throws Exception {
        assertTrue(selected(Build.CROZIER4.version(),Build.CROZIER4.sha256()).liveReadsEnabled());
        for(var build:List.of(Build.WANDERER6,Build.CROZIER2,Build.CROZIER3))
            assertThrows(IllegalArgumentException.class,()->selected(build.version(),build.sha256()));
    }
    @Test void unavailableCannotCallTheNativeReadAndRetainsTheActualNegativeResultFields(){
        var build=ExactCk3Build.CK3_1210;var status=KnownPendingInteractionPolicy.unavailableForSource(
                build.version(),build.executableSha256(),source(build.executableSha256()));
        var calls=new AtomicInteger();var result=RootGuardianReconciliationReads.currentResult(status,c->{calls.incrementAndGet();throw new AssertionError("no read");});
        var unavailable=assertInstanceOf(PlanningReadResult.Unavailable.class,result);
        assertEquals(0,calls.get());assertEquals(status.result().reason(),unavailable.reason());
        assertSame(status.result().original(),unavailable.original());assertSame(status.result().decodeFailure(),unavailable.decodeFailure());
        assertSame(status.result().observedFailure(),unavailable.observedFailure());
    }
    @Test void realAvailableReadResultAndItsReceiptPassThroughWithoutReplacement(){
        var c=context();var r=request();var ack=new NativeActionPort.AckReceived("synthetic-read",true,Optional.empty(),new RawJson(new byte[]{'{','}'}),new byte[]{1});
        var receipt=new PlanningReadReceipt(r,"interactions:ordinary-query","synthetic-read",guard(),guard(),ack);
        var value=new OrdinaryContext(new Frame(c.revision(),c.date(),c.actor(),c.build(),BigInteger.ONE),
                new OrdinaryRequest(new InteractionKey("educate_child_interaction"),new CharacterId(18),Optional.empty()),
                new Availability(false,"synthetic-domain-unavailable"),null,null,null,false,false,false,false,false,
                "synthetic-domain-unavailable",Optional.empty(),Optional.empty());
        var known=new PlanningReadResult.Known<>(value,receipt,REF);var calls=new AtomicInteger();
        var result=RootGuardianReconciliationReads.currentResult(new KnownPendingInteractionPolicy.Available(c),actual->{
            calls.incrementAndGet();assertSame(c,actual);return known;});
        assertSame(known,result);assertEquals(1,calls.get());assertSame(receipt,((PlanningReadResult.Known<?>)result).receipt());
    }
    @Test void originalUnknownAndObservedFailedReadRemainAttachedToTheTypedNegative(){
        var cause=new NativeActionPort.FailureCause(NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED,
                NativeActionPort.FailureStage.RESPONSE_WAIT,Optional.empty(),Optional.empty(),Optional.empty());
        var unknown=new NativeActionPort.Unknown("synthetic-read","source-owned-negative",new byte[]{1},Optional.empty(),Optional.of(cause));
        var prepared=new NativeRequest(OrdinaryInteractionCodec.QUERY_STEP,OrdinaryInteractionCodec.QUERY_CAPABILITY,new RawJson(new byte[]{'{','}'}));
        var observed=new PlanningReadFailure(request(),"interactions:ordinary-query","synthetic-read",guard(),guard(),prepared,unknown,REF,REF,3,"c".repeat(64));
        var missing=new PlanningReadResult.Unavailable<Context>("source-owned-negative",Optional.of(unknown),Optional.empty(),Optional.of(observed));
        var mapped=RootGuardianReconciliationReads.unavailable(missing);
        assertSame(missing.original(),mapped.original());assertSame(missing.decodeFailure(),mapped.decodeFailure());
        assertSame(missing.observedFailure(),mapped.observedFailure());assertEquals(missing.reason(),mapped.reason());
    }
    @Test void sourceOwnedDecodeFailureIdentityAlsoSurvivesTheTypeAdapter(){
        var ack=new NativeActionPort.AckReceived("synthetic-read",true,Optional.empty(),new RawJson(new byte[]{'{','}'}),new byte[]{1});
        OriginalReadDecodeFailure original=(contract,request,receipt)->{throw new AssertionError("adapter cannot requalify failure custody");};
        var missing=new PlanningReadResult.Unavailable<Context>("decode-rejected",Optional.of(ack),Optional.of(original),Optional.empty());
        var mapped=RootGuardianReconciliationReads.unavailable(missing);
        assertSame(original,mapped.decodeFailure().orElseThrow());assertSame(ack,mapped.original().orElseThrow());
        assertEquals("decode-rejected",mapped.reason());assertTrue(mapped.observedFailure().isEmpty());
    }
    private static Complete frame(String version,String sha){
        var n=StrictJson.object().put("paused",true).put("map_ready",true).put("speed",1).put("local_player_id",17)
                .put("episode_character_id",17).put("episode_run_id","synthetic-episode");
        n.putObject("diagnostics").putObject("hello").put("game_version",version).put("executable_sha256",sha);
        var player=n.putObject("played_character").put("character_id",17).put("alive",true).putNull("betrothed_id");
        player.putArray("spouse_ids");n.putNull("active_event").putNull("pending_character_interaction");
        return new Complete(identity(),source(sha),"synthetic-session",BigInteger.ONE,OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(n)),"synthetic frame"),REF,NOW,"d".repeat(64));
    }
    @Test void historicalProjectionAcceptsOriginalFourAndRejectsTheRealFlorinTuple()throws Exception {
        var current=ExactCk3Build.CK3_1210;var queries=selected(current.version(),current.executableSha256());
        var historical=queries.historicalProjection();var original=frame(Build.CROZIER4.version(),Build.CROZIER4.sha256());
        assertEquals(Build.CROZIER4,historical.project(original,NOW.plusSeconds(30)).build());
        assertThrows(IllegalArgumentException.class,()->historical.project(frame(current.version(),current.executableSha256()),NOW.plusSeconds(30)));
        assertThrows(IllegalArgumentException.class,()->historical.project(frame(Build.CROZIER4.version(),current.executableSha256()),NOW.plusSeconds(30)));
    }
}
