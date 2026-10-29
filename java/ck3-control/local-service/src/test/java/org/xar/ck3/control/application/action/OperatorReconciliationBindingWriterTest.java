package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual writer pin/escape and same-producer routing. Pending DATA never qualifies a Root operator result. */
final class OperatorReconciliationBindingWriterTest {
    @TempDir Path temporary;
    private static ExactRef reference(Path file) throws Exception {
        byte[] bytes=Files.readAllBytes(file);
        return new ExactRef(file.toAbsolutePath().normalize().toString(),bytes.length,
                HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static final class PendingOnlySource implements RootExecutableBindings.OperatorSourceOriginProof {
        final ExactRef source; int preparations,oldPreflights,reconciliations;
        ContinuityStorePort.Session receivedSession; ActionReceipt receivedReceipt;
        Instant receivedDeadline; ActionPorts.OperatorReconciliationWork receivedObserver;
        Path changeSource;
        PendingOnlySource(ExactRef source){this.source=source;}
        @Override public ExactRef operatorDefinitionSource(){return source;}
        @Override public void requireOperatorOrigin(ContinuityStorePort.Session same,ActionCommand exact){
            oldPreflights++;throw new AssertionError("read-only reconciliation must not rerun the original before preflight");
        }
        @Override public NativeRequest prepare(ActionCommand exact){
            preparations++;throw new AssertionError("read-only reconciliation cannot prepare or submit a native setter");
        }
        @Override public ActionPorts.PostconditionResult observeOperatorReconciliation(ContinuityStorePort.Session same,
                ActionReceipt original,Instant deadline,ActionPorts.OperatorReconciliationWork observer) throws IOException {
            reconciliations++;receivedSession=same;receivedReceipt=original;receivedDeadline=deadline;receivedObserver=observer;
            if(changeSource!=null)Files.writeString(changeSource,"changed source");
            return new ActionPorts.Pending("descriptor fixture has no actual Root private operator authority",List.of());
        }
    }
    private static NativeEffectRegistry.Binding effect(ExactRef source,ActionPorts.PreparationPort preparation){
        return new NativeEffectRegistry.Binding(new OperationKey("set-played-character-v1-7"),source,preparation,
                (command,attempt,dispatch)->{throw new AssertionError("descriptor fixture cannot confirm an operator result");});
    }
    private static RootExecutableBindings catalog(PendingOnlySource source){
        return RootExecutableBindings.freeze(List.of(RootExecutableBindings.ActionBinding.operatorSource(effect(source.source,source),source.source,source)),
                RootReadContractCatalog.staticOnly(List.of()),List.of(),4);
    }
    private static ActionReceipt dataReceipt(ActionCommand basis){
        var request=new OperatorPlayerSwitch.Request(7,basis.before().frame().revision());
        var expected=new CommandExpectation.OperatorRebind(new OperatorRebindExpectation(basis.origin(),basis.source(),request,
                basis.before().frame().episodeRunId(),0,basis.source().sourceRef()));
        var command=new ActionCommand("operator-routing-data",basis.origin(),basis.source(),basis.sessionId(),
                new OperationKey(request.step()),new OpportunityJson.Obj(Map.of()),expected,basis.claims(),basis.deadline());
        // Not a canonical pending receipt: the central coordinator and private installed source must reject it for settlement.
        return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());
    }
    @Test void sameActualProducerReceivesTheOriginalArgumentsUnderTheRealWriterWithoutOldPreflightOrSubmission() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("routing"),false)){
            Path file=temporary.resolve("routing-source.java");Files.writeString(file,"original source");
            var source=new PendingOnlySource(reference(file));var bindings=catalog(source);var receipt=dataReceipt(fixture.command("basis"));
            var deadline=Instant.now().plusSeconds(20);var observerCalls=new java.util.concurrent.atomic.AtomicInteger();
            ActionPorts.OperatorReconciliationWork observer=()->{observerCalls.incrementAndGet();throw new AssertionError("no private Root scope");};
            fixture.writer.locked(same->{
                var before=same.head();
                var result=assertDoesNotThrow(()->bindings.observeOperatorReconciliation(same,receipt,deadline,observer));
                assertInstanceOf(ActionPorts.Pending.class,result);assertSame(same,source.receivedSession);
                assertSame(receipt,source.receivedReceipt);assertSame(deadline,source.receivedDeadline);assertSame(observer,source.receivedObserver);
                assertEquals(before.digest(),same.head().digest());
                fixture.archive.inSession(same,archive->{
                    byte[] encoded=ActionReceiptCodec.encodeReceipt(receipt,archive);
                    assertArrayEquals(encoded,ActionReceiptCodec.encodeReceipt(ActionReceiptCodec.decodeReceipt(encoded,archive),archive));
                    return null;
                });
                return null;
            });
            assertEquals(1,source.reconciliations);assertEquals(0,source.preparations);assertEquals(0,source.oldPreflights);
            assertEquals(0,observerCalls.get());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void missingFiniteSourceProfileAndDefaultPreparationCannotOpenAnOperatorObservation() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("default"),false)){
            Path file=temporary.resolve("default-source.java");Files.writeString(file,"ordinary source");var source=reference(file);
            var ordinaryPreparations=new java.util.concurrent.atomic.AtomicInteger();
            ActionPorts.PreparationPort ordinary=command->{ordinaryPreparations.incrementAndGet();throw new AssertionError("no submission");};
            var bindings=RootExecutableBindings.freeze(List.of(new RootExecutableBindings.ActionBinding(effect(source,ordinary),
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(OperatorPlayerSwitch.CAPABILITY),source)),
                    RootReadContractCatalog.staticOnly(List.of()),List.of(),4);
            var receipt=dataReceipt(fixture.command("basis-default"));var observerCalls=new java.util.concurrent.atomic.AtomicInteger();
            ActionPorts.OperatorReconciliationWork observer=()->{observerCalls.incrementAndGet();return new ActionPorts.Pending("unqualified",List.of());};
            fixture.writer.locked(same->{
                assertThrows(IOException.class,()->ordinary.observeOperatorReconciliation(same,receipt,Instant.now().plusSeconds(20),observer));
                assertThrows(IOException.class,()->bindings.observeOperatorReconciliation(same,receipt,Instant.now().plusSeconds(20),observer));
                return null;
            });
            assertEquals(0,ordinaryPreparations.get());assertEquals(0,observerCalls.get());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void sourceMutationAndEscapedActualWriterSessionCannotReturnEvenPendingObservationData() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("pins"),false)){
            Path file=temporary.resolve("pin-source.java");Files.writeString(file,"original source");
            var source=new PendingOnlySource(reference(file));var bindings=catalog(source);var receipt=dataReceipt(fixture.command("basis-pins"));
            var escaped=new AtomicReference<ContinuityStorePort.Session>();source.changeSource=file;
            ActionPorts.OperatorReconciliationWork never=()->{throw new AssertionError("no private scope");};
            fixture.writer.locked(same->{
                escaped.set(same);assertThrows(Exception.class,()->bindings.observeOperatorReconciliation(same,receipt,Instant.now().plusSeconds(20),never));
                return null;
            });
            assertEquals(1,source.reconciliations);source.changeSource=null;
            assertThrows(IllegalArgumentException.class,()->bindings.observeOperatorReconciliation(escaped.get(),receipt,Instant.now().plusSeconds(20),never));
            assertEquals(1,source.reconciliations);assertEquals(0,source.preparations);assertEquals(0,source.oldPreflights);
            assertEquals(0,fixture.nativeActionWrites());
        }
    }
}

