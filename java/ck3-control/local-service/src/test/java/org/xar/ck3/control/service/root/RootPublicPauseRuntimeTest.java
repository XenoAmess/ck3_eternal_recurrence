package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.*;
import java.util.function.LongSupplier;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Pure metadata tests plus mandatory real Root entry points. No reflection, synthetic Ready or replacement native submitter. */
public final class RootPublicPauseRuntimeTest {
    private static final Instant T=Instant.parse("2026-10-24T12:00:00Z");
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef ref(String text){byte[] bytes=text.getBytes(StandardCharsets.UTF_8);return new ExactRef("software/"+text,bytes.length,ActionCodec.sha256(bytes));}
    private static GuardEvidence guard(){
        var identity=new ObservationIdentity("pause-envelope-software",new GameGeneration(33,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,new BigInteger("9007199254740993"),BigInteger.valueOf(1000)),
                        "原始帧",new BigInteger("9007199254740993"),"software-episode"),1);
        var source=new G2Source(identity.machineId(),T.toString(),"1.20.0.4",ref("source"));
        return new GuardEvidence(identity,source,"software-session",new BigInteger("9007199254740993"),ControlSequenceObservation.OPERATION,
                ref("native"),ref("hello"),RootPublicPauseRuntime.HANDLER,T,T.plusSeconds(30),List.of(ref("root-basis")));
    }
    @Test void actualSharedGuardCodecRoundTripRetainsNativeDriverRolesWithoutGrantingAnIssuer(){
        var original=new RootPublicPauseRuntime.RecordedRecovery(ref("decision"),List.of(guard()),Optional.empty());
        RawJson bytes=original.encode();assertEquals(original,RootPublicPauseRuntime.RecordedRecovery.decode(bytes));
        assertArrayEquals(bytes.bytes(),RootPublicPauseRuntime.RecordedRecovery.decode(bytes).encode().bytes());
        assertEquals(guard(),ActionReceiptCodec.decodeGuard(ActionReceiptCodec.encodeGuard(guard())));
        assertThrows(UnsupportedOperationException.class,()->original.guards().clear());
        assertThrows(IllegalArgumentException.class,()->new RootPublicPauseRuntime.RecordedRecovery(ref("decision"),List.of(guard(),guard()),Optional.empty()));
        var changed=(ObjectNode)StrictJson.parse(bytes.bytes());changed.put("authority",true);
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.RecordedRecovery.decode(new RawJson(StrictJson.canonical(changed))));
        var missing=(ObjectNode)StrictJson.parse(bytes.bytes());missing.remove("phase_guards");
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.RecordedRecovery.decode(new RawJson(StrictJson.canonical(missing))));
        var nullList=(ObjectNode)StrictJson.parse(bytes.bytes());nullList.putNull("phase_guards");
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.RecordedRecovery.decode(new RawJson(StrictJson.canonical(nullList))));
        var missingDiagnostic=(ObjectNode)StrictJson.parse(bytes.bytes());missingDiagnostic.remove("wait_failure");
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.RecordedRecovery.decode(new RawJson(StrictJson.canonical(missingDiagnostic))));
        var wrongDiagnostic=(ObjectNode)StrictJson.parse(bytes.bytes());wrongDiagnostic.put("wait_failure",false);
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.RecordedRecovery.decode(new RawJson(StrictJson.canonical(wrongDiagnostic))));
        var withDiagnostic=new RootPublicPauseRuntime.RecordedRecovery(ref("decision"),List.of(guard()),Optional.of(ref("diagnostic")));
        assertEquals(withDiagnostic,RootPublicPauseRuntime.RecordedRecovery.decode(withDiagnostic.encode()));
        assertThrows(IllegalArgumentException.class,()->new RootPublicPauseRuntime.RecordedRecovery(ref("decision"),List.of(),Optional.empty()));
    }
    @Test void actualWaitDiagnosticCodecRetainsCaughtPhaseAndRejectsOversizeInput(){
        var diagnostic=new RootPublicPauseRuntime.WaitFailure(RootPublicPauseRuntime.WaitPhase.REFRESH,T,
                "java.io.IOException","actual wait expired","java.io.IOException: actual wait expired\n\tat original.Driver.read(Driver.java:12)",ref("runtime"));
        assertEquals(diagnostic,RootPublicPauseRuntime.WaitFailure.decode(diagnostic.encode()));
        var missing=(ObjectNode)StrictJson.parse(diagnostic.encode().bytes());missing.remove("original_trace");
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.WaitFailure.decode(new RawJson(StrictJson.canonical(missing))));
        var unknownPhase=(ObjectNode)StrictJson.parse(diagnostic.encode().bytes());unknownPhase.put("phase","REPLACEMENT");
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.WaitFailure.decode(new RawJson(StrictJson.canonical(unknownPhase))));
        var oversized=new RootPublicPauseRuntime.WaitFailure(RootPublicPauseRuntime.WaitPhase.ENDING,T,"java.io.IOException",
                "actual wait expired","界".repeat(32768),ref("runtime"));
        assertThrows(IllegalArgumentException.class,oversized::encode);
        var oversizedWire=(ObjectNode)StrictJson.parse(diagnostic.encode().bytes());oversizedWire.put("original_trace","x".repeat(RootPublicPauseRuntime.WaitFailure.MAX_BYTES));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.WaitFailure.decode(new RawJson(StrictJson.canonical(oversizedWire))));
    }
    @Test void originalNumericReportUsesOnlyDeclaredPublicCounterRolesAndPreservesDecimalTokens(){
        var numeric=raw("{\"revision\":9007199254740993,\"snapshot_revision\":9007199254740993,\"date_raw\":-12,\"ratio\":-0.0,\"map_control_recovery\":{\"starting_revision\":18446744073709551615,\"ending_native_revision\":9007199254740993,\"ending_date_raw\":1001}}");
        var publicWire=RootPublicPauseRuntime.Installed.publicResult(numeric);
        var row=StrictJson.parse(publicWire.bytes());assertEquals("9007199254740993",row.get("revision").textValue());assertEquals("9007199254740993",row.get("snapshot_revision").textValue());
        assertEquals("18446744073709551615",row.get("map_control_recovery").get("starting_revision").textValue());
        assertEquals(-12,row.get("date_raw").intValue());assertEquals(1001,row.get("map_control_recovery").get("ending_date_raw").intValue());
        assertTrue(new String(publicWire.bytes(),StandardCharsets.UTF_8).contains("-0.0"));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.Installed.publicResult(raw("{\"map_control_recovery\":{\"starting_revision\":18446744073709551616}}")));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.Installed.publicResult(raw("{\"map_control_recovery\":{\"starting_revision\":-1}}")));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.Installed.publicResult(raw("{\"starting_revision\":9007199254740993}")));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.Installed.publicResult(raw("{\"revision\":true}")));
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseRuntime.Installed.publicResult(raw("{\"revision\":1.0}")));
    }
    public enum Scenario { DIRECT,ALREADY_PAUSED_AFTER_REJECTION,ONE_RETRY,KNOWN_RECOVERY_FAILURE,UNKNOWN,RESTORED_ORIGINAL,
            NATIVE_ORIGINAL_REJECTION,ZERO_DISPATCH_ORIGINAL }
    public interface InputsProducer { Inputs open(Scenario scenario)throws Exception; }
    public record Inputs(RootInstalledCatalog catalog,PublicPlanningCodec.ExecuteRequest caller,String parentActionId,Instant deadline,
            LongSupplier actualNativePausePacketsWritten,Optional<RootInstalledCatalog> restoredCatalog) {
        public Inputs {Objects.requireNonNull(catalog);Objects.requireNonNull(caller);Objects.requireNonNull(parentActionId);
            Objects.requireNonNull(deadline);Objects.requireNonNull(actualNativePausePacketsWritten);restoredCatalog=Objects.requireNonNull(restoredCatalog);}
    }
    private static Inputs actual(Scenario scenario)throws Exception{
        var providers=ServiceLoader.load(InputsProducer.class).stream().toList();
        if(providers.size()!=1)throw new IllegalStateException("MISSING_ACTUAL_ROOT_PUBLIC_PAUSE_INPUTS_NOT_RUN: "+scenario);
        var input=Objects.requireNonNull(providers.getFirst().get().open(scenario));
        assertEquals(RootPublicPauseRuntime.PUBLIC_STEP,input.caller().step());assertFalse(input.caller().h2743());
        assertEquals(input.caller(),PublicPlanningCodec.decodeExecute(
                org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings.present(PublicPlanningCodec.encodeExecute(input.caller()))));
        return input;
    }
    private static RootApplicationSession root(RootInstalledCatalog catalog){
        return assertInstanceOf(RootApplicationSession.class,catalog.context().actions());
    }
    private static ActionReceipt canonical(Inputs input,RootInstalledCatalog catalog)throws Exception{
        var root=root(catalog);var context=catalog.context();
        return root.withPublicStandaloneRead(input.deadline(),same->{
            context.core().requireCurrentForAccess(same,root);
            return context.core().actions().withFrozen(same,lease->lease.find(input.parentActionId()).orElseThrow());
        });
    }
    private static RawJson invoke(Inputs input)throws Exception{
        return RootPublicStepExecution.execute(root(input.catalog()),input.catalog(),input.caller(),input.deadline());
    }
    private static List<ActionReceipt> verifyOriginal(Inputs input,RootInstalledCatalog catalog,ActionReceipt parent)throws Exception{
        var root=root(catalog);var context=catalog.context();
        return root.withPublicStandaloneRead(input.deadline(),same->{
            var archive=context.archive().withSession(same);context.core().requireCurrentForAccess(same,root);
            context.bindings().actualArchivedVerifier(parent.command().operation()).orElseThrow().verifier().verify(same.head(),parent,archive);
            RootPublicPausePlanningAssertions.requireZeroBusiness(catalog.planningDomainCatalog(),same,archive,parent);
            var execution=ActionTransitions.composite(parent.state()).orElseThrow();
            var children=execution.children().stream().map(child->{
                try{return ContinuityActionJournal.lookup(same.head().state(),child.actionId(),archive).orElseThrow();}
                catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            }).toList();
            assertFalse(parent.visibleGameplay());assertFalse(parent.eligibleAdvance());assertTrue(parent.applied().isEmpty());
            assertTrue(catalog.publicPause().matchesParent(parent.command()));
            if(!(parent.state() instanceof ActionState.CompositeSettled settled
                    &&settled.settlement() instanceof ActionState.CompositeRejected rejected&&rejected.evidence().isEmpty())){
                var numeric=catalog.publicPause().recordedResult(parent,archive);
                assertTrue(StrictJson.parse(numeric.bytes()).isObject());
            }
            return children;
        });
    }
    private static void completed(Inputs input,ControlSequenceObservation.Mode mode,int childCount)throws Exception{
        long before=input.actualNativePausePacketsWritten().getAsLong();RawJson result=invoke(input);
        assertTrue(StrictJson.parse(result.bytes()).get("accepted").booleanValue());
        var parent=canonical(input,input.catalog());var settled=assertInstanceOf(ActionState.CompositeSettled.class,parent.state());
        assertEquals(mode,assertInstanceOf(ActionState.ControlSequenceCompleted.class,settled.settlement()).observation().mode());
        var children=verifyOriginal(input,input.catalog(),parent);assertEquals(childCount,children.size());
        assertEquals(childCount,input.actualNativePausePacketsWritten().getAsLong()-before);
        children.forEach(child->assertEquals("pause-map",child.command().operation().value()));
        if(childCount==2){ControlSequenceObservation.requireMapUnavailable(children.getFirst());assertNotEquals(children.getFirst().command().actionId(),children.getLast().command().actionId());
            assertTrue(children.getLast().command().before().frame().identity().nativeRevision().compareTo(children.getFirst().command().before().frame().identity().nativeRevision())>0);}
    }
    @Test void actualPublicDirectPauseRunsOneRealPrimitiveAndNoGameplayDayCredit()throws Exception{
        completed(actual(Scenario.DIRECT),ControlSequenceObservation.Mode.DIRECT_PAUSE,1);
    }
    @Test void actualInstalledClassifierRejectsMissingOrDuplicatedInventory()throws Exception{
        var input=actual(Scenario.DIRECT);var catalog=input.catalog();
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.install(
                catalog.context(),catalog.bindings(),List.of(),catalog.publicPause()));
        var duplicated=new ArrayList<>(catalog.domains());duplicated.add(catalog.publicPause().installation());
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.install(
                catalog.context(),catalog.bindings(),duplicated,catalog.publicPause()));
    }
    @Test void actualFirstNativeRejectionThenPausedFrameNeedsNoSecondSubmit()throws Exception{
        completed(actual(Scenario.ALREADY_PAUSED_AFTER_REJECTION),ControlSequenceObservation.Mode.ALREADY_PAUSED_AFTER_REJECTION,1);
    }
    @Test void actualFreshSameOwnerRecoveryRunsExactlyOneCanonicalRetry()throws Exception{
        completed(actual(Scenario.ONE_RETRY),ControlSequenceObservation.Mode.RETRIED_PAUSE,2);
    }
    @Test void actualKnownFailureRetainsOriginalReportAndOriginalPublicError()throws Exception{
        var input=actual(Scenario.KNOWN_RECOVERY_FAILURE);long before=input.actualNativePausePacketsWritten().getAsLong();
        var failure=assertThrows(PublicServiceFailure.class,()->invoke(input));
        assertEquals(PublicServiceFailure.Kind.STEP_POSTCONDITION_ERROR,failure.kind());assertTrue(failure.originalCandidate().isPresent());
        var parent=canonical(input,input.catalog());var rejected=assertInstanceOf(ActionState.CompositeRejected.class,
                assertInstanceOf(ActionState.CompositeSettled.class,parent.state()).settlement());
        assertEquals(List.of(failure.originalCandidate().orElseThrow()),rejected.evidence());assertTrue(rejected.reason().startsWith("native pause-map recovery stopped: "));
        var children=verifyOriginal(input,input.catalog(),parent);assertEquals(children.size(),input.actualNativePausePacketsWritten().getAsLong()-before);
        assertTrue(children.size()<=2);
    }
    private static void originalRejection(Scenario scenario,long expectedPackets)throws Exception{
        var input=actual(scenario);long before=input.actualNativePausePacketsWritten().getAsLong();
        var failure=assertThrows(PublicServiceFailure.class,()->invoke(input));
        assertEquals(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,failure.kind());
        var parent=canonical(input,input.catalog());
        var rejected=assertInstanceOf(ActionState.CompositeRejected.class,
                assertInstanceOf(ActionState.CompositeSettled.class,parent.state()).settlement());
        assertTrue(rejected.evidence().isEmpty());
        assertEquals(Optional.of(input.catalog().context().archive().receiptReferenceOf(parent)),failure.originalCandidate());
        var children=verifyOriginal(input,input.catalog(),parent);assertEquals(1,children.size());
        assertEquals(RootPublicPauseRuntime.Installed.originalRejectionReason(children.getFirst()).orElseThrow(),rejected.reason());
        assertEquals("native gameplay step failed: "+rejected.reason(),failure.getMessage());
        assertEquals(expectedPackets,input.actualNativePausePacketsWritten().getAsLong()-before);
    }
    @Test void actualOriginalNativeRejectionRetainsCauseWithoutRecovery()throws Exception{
        originalRejection(Scenario.NATIVE_ORIGINAL_REJECTION,1);
    }
    @Test void actualOriginalZeroDispatchRejectionSettlesWithoutSendingOrRetrying()throws Exception{
        originalRejection(Scenario.ZERO_DISPATCH_ORIGINAL,0);
    }
    @Test void actualUnknownReentryOnlyReconcilesOriginalAndNeverSubmitsAgain()throws Exception{
        var input=actual(Scenario.UNKNOWN);assertThrows(Exception.class,()->invoke(input));
        var original=canonical(input,input.catalog());assertFalse(original.settled());long count=input.actualNativePausePacketsWritten().getAsLong();
        RootPublicPausePlanningAssertions.requireUnresolvedBlocked(original);
        assertThrows(Exception.class,()->invoke(input));var after=canonical(input,input.catalog());
        assertEquals(count,input.actualNativePausePacketsWritten().getAsLong());assertEquals(original.command(),after.command());
        assertEquals(original.bodySha256(),after.bodySha256());assertEquals(ActionTransitions.composite(original.state()).orElseThrow().children(),
                ActionTransitions.composite(after.state()).orElseThrow().children());
    }
    @Test void actualColdRootReplaysSameParentAndPhaseOriginalsWithNoReplacementCommand()throws Exception{
        var input=actual(Scenario.RESTORED_ORIGINAL);invoke(input);var original=canonical(input,input.catalog());
        var restored=input.restoredCatalog().orElseThrow(()->new IllegalStateException("MISSING_ACTUAL_COLD_ROOT_PAUSE_INPUTS_NOT_RUN"));
        assertNotSame(input.catalog().context(),restored.context());
        assertNotSame(input.catalog().bindings(),restored.bindings());
        assertThrows(IllegalArgumentException.class,()->RootPublicPauseArchiveClassifier.install(input.catalog().context(),
                restored.bindings(),input.catalog().domains(),input.catalog().publicPause()));
        long count=input.actualNativePausePacketsWritten().getAsLong();var retained=canonical(input,restored);
        assertEquals(original,retained);verifyOriginal(input,restored,retained);
        assertEquals(count,input.actualNativePausePacketsWritten().getAsLong());
    }
}
