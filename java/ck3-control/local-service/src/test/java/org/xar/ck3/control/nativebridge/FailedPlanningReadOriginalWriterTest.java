package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual software native READ/guards/archive, not a constructed failure receipt or granted history authority. */
final class FailedPlanningReadOriginalWriterTest {
    @TempDir Path root;
    private enum Failure { DECODE, PREPARE, NATIVE_REJECTED, UNKNOWN, KNOWN_OBSERVER }
    private static final OperationKey OP = new OperationKey("fixture-failed-read-v1");
    private static final String CAP = "fixture.failed-read";
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static ReadContract<RawJson> contract(ExactRef source, Failure failure) {
        java.util.function.Function<PlanningReadReceipt,RawJson> decode = receipt -> {
            if (failure==Failure.DECODE) throw new IllegalArgumentException("actual source decoder rejects its received result");
            return receipt.original().originalResultToken().orElseThrow();
        };
        return new ReadContract<>("fixture-failed-read50/v1",OP,Optional.of(CAP),CAP,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(request,id)-> {
                    if (failure==Failure.PREPARE) throw new IllegalArgumentException("actual source rejects preparation before permit");
                    return new NativeRequest(OP.value(),Optional.of(CAP),raw("{}"));
                },decode,decode);
    }
    private void actualFailure(Failure mode) throws Exception {
        var installed=new AtomicReference<ReadContract<RawJson>>();
        var observed=new AtomicReference<PlanningReadResult.Unavailable<?>>();
        var token=new AtomicReference<PlanningReadCoordinator.FailedReadAttempt>();
        var callbackRequest=new AtomicReference<PlanningReadRequest>();
        var producedKnown=new AtomicReference<PlanningReadResult.Known<?>>();
        var input=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"fixture-adapter",source->{
            var actual=contract(source,mode);installed.set(actual);return List.of(actual);
        },request->raw("{}"),Optional.empty(),Set.of(CAP));
        try(var actual=new ActionWriterIntegrationFixture(root.resolve(mode.name()),false,input)) {
            actual.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver() {
                @Override public void afterKnown(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                        ReadContract<?> identical,PlanningReadResult.Known<?> known) {
                    if(identical==installed.get()&&mode==Failure.KNOWN_OBSERVER){producedKnown.set(known);throw new IllegalStateException("actual Known publication observer failure");}
                }
                @Override public void afterUnavailable(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                        ReadContract<?> identical,PlanningReadRequest request,PlanningReadResult.Unavailable<?> unavailable,
                        Optional<PlanningReadCoordinator.FailedReadAttempt> original) {
                    if(identical!=installed.get())return;
                    assertNull(observed.getAndSet(unavailable));
                    if(mode!=Failure.DECODE && mode!=Failure.NATIVE_REJECTED && mode!=Failure.UNKNOWN){assertTrue(original.isEmpty());return;}
                    var retained=original.orElseThrow();token.set(retained);callbackRequest.set(request);
                    try{retained.requireOriginal(same,identical,request,unavailable,actual.archive);assertEquals(same.head().digest(),retained.headDigest());}
                    catch(IOException missing){throw new UncheckedIOException(missing);}
                    assertEquals(request.origin(),retained.before().binding().origin());
                    assertEquals(retained.original(),actual.archive.load(retained.originalRef()));
                    assertEquals(retained.prepared(),actual.archive.loadRequest(retained.preparedRef()));
                    assertEquals(retained.requestId(),retained.original().requestId());
                    var bound=actual.archive.withSession(same);
                    long filesBefore=countFiles(actual.root);
                    bound.verifyReadAttemptOriginals(request,retained.requestId(),retained.before(),retained.prepared(),retained.original());
                    // Cold history supplies equal typed DATA, not the private live callback token.
                    var equalRequest=new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),request.operation(),request.arguments(),request.deadline());
                    bound.verifyReadAttemptOriginals(equalRequest,retained.requestId(),retained.before(),retained.prepared(),retained.original());
                    assertThrows(RuntimeException.class,()->bound.verifyReadAttemptOriginals(request,retained.requestId()+"-foreign",retained.before(),retained.prepared(),retained.original()));
                    var foreignRequest=new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),new OperationKey("foreign-read-v1"),request.arguments(),request.deadline());
                    assertThrows(RuntimeException.class,()->bound.verifyReadAttemptOriginals(foreignRequest,retained.requestId(),retained.before(),retained.prepared(),retained.original()));
                    if(retained.original() instanceof NativeActionPort.AckReceived ack) {
                        var deadline=ack.custody().orElseThrow().writeEntered().observedAt();
                        var wrongDeadline=new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),request.operation(),request.arguments(),deadline);
                        assertThrows(RuntimeException.class,()->bound.verifyReadAttemptOriginals(wrongDeadline,retained.requestId(),retained.before(),retained.prepared(),retained.original()));
                    }
                    assertEquals(filesBefore,countFiles(actual.root)); // The shared matcher is read-only.
                    var changed=new NativeRequest(retained.prepared().step(),retained.prepared().requiredCapability(),
                            raw("{\"different_from_actual_outgoing\":true}"),retained.prepared().preparationEvidence());
                    actual.archive.preserveRequest(changed); // Explicit negative DATA; never repair it in the matcher.
                    long filesAfter=countFiles(actual.root);
                    var mismatch=assertThrows(RuntimeException.class,()->bound.verifyReadAttemptOriginals(request,retained.requestId(),retained.before(),changed,retained.original()));
                    messageContains(mismatch,"actual outbound execute fields");
                    assertEquals(filesAfter,countFiles(actual.root));
                    var copy=new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
                    assertThrows(IllegalArgumentException.class,()->retained.requireOriginal(same,identical,request,copy,actual.archive));
                    var copiedRequest=new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),request.operation(),request.arguments(),request.deadline());
                    assertThrows(IllegalArgumentException.class,()->retained.requireOriginal(same,identical,copiedRequest,unavailable,actual.archive));
                }
            });
            if(mode==Failure.UNKNOWN)actual.loseReadAckOnce();
            if(mode==Failure.NATIVE_REJECTED)actual.rejectNextScenarioRead();
            var ready=actual.ready();
            var request=new PlanningReadRequest(ready.request().before(),actual.observationSource(),actual.observationIdentity().sessionId(),
                    OP,new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(10));
            var result=assertInstanceOf(PlanningReadResult.Unavailable.class,actual.reads.read(installed.get(),request));
            assertSame(observed.get(),result); assertEquals(mode==Failure.PREPARE?0:1,actual.scenarioReadWrites());
            assertEquals(0,actual.nativeActionWrites()); assertEquals(0,actual.snapshot().ledgerSequence());
            if(mode==Failure.DECODE || mode==Failure.NATIVE_REJECTED || mode==Failure.UNKNOWN){assertNotNull(token.get());assertTrue(result.original().isPresent());}
            else assertNull(token.get());
            if(mode==Failure.KNOWN_OBSERVER)assertNotNull(producedKnown.get());else assertNull(producedKnown.get());
            if(mode==Failure.UNKNOWN)assertInstanceOf(NativeActionPort.Unknown.class,result.original().orElseThrow());
            if(token.get()!=null) {
                var retained=token.get();Path missing=Path.of(retained.preparedRef().path());
                assertTrue(missing.normalize().startsWith(actual.root.normalize()));
                Files.delete(missing);long count=countFiles(actual.root);
                actual.writer.locked(same->{
                    var bound=actual.archive.withSession(same);
                    assertThrows(RuntimeException.class,()->bound.verifyReadAttemptOriginals(callbackRequest.get(),
                            retained.requestId(),retained.before(),retained.prepared(),retained.original()));
                    return null;
                });
                assertFalse(Files.exists(missing));assertEquals(count,countFiles(actual.root));
                assertEquals(0,actual.snapshot().ledgerSequence());assertEquals(0,actual.nativeActionWrites());
            }
        }
    }
    @Test void actualConsumedReadAndRejectedDecodeRetainsOnlyItsOriginalFailureCustody() throws Exception { actualFailure(Failure.DECODE); }
    @Test void actualEndpointRejectionRetainsItsConsumedReadFailureOriginal() throws Exception { actualFailure(Failure.NATIVE_REJECTED); }
    @Test void actualWriteCompletedReadIoUnknownUsesTheSameOriginalPacketMatcherWithoutAnAck() throws Exception { actualFailure(Failure.UNKNOWN); }
    @Test void preparationFailureHasNoAttemptTokenOrScenarioNativeWrite() throws Exception { actualFailure(Failure.PREPARE); }
    @Test void alreadyProducedKnownCallbackFailureCannotBecomeAnotherFailedNativeRead() throws Exception { actualFailure(Failure.KNOWN_OBSERVER); }
    private static long countFiles(Path root) {
        try(var entries=Files.walk(root)){return entries.filter(Files::isRegularFile).count();}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static void messageContains(Throwable failure,String expected) {
        for(Throwable current=failure;current!=null;current=current.getCause())
            if(current.getMessage()!=null&&current.getMessage().contains(expected))return;
        fail("expected original protocol mismatch containing '"+expected+"', got "+failure);
    }
}
