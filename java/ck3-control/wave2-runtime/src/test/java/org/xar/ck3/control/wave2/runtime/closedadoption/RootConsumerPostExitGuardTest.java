package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.closedpartial.ClosedPartialAdmissionVerifier;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Real original writer/consumer Jobs; the inherited SDK prerequisite fixture remains synthetic. */
class RootConsumerPostExitGuardTest {
    private record Context(ClosedAdoptionTransactionTest.Fixture fixture,
            OriginalWriterTransaction.Committed committed, RecoveryEvidence basis,
            RecoveryEvidence qualification) { }

    private static Context context() throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture();
        var settings = ClosedAdoptionTransactionTest.settings(fixture);
        var committed = OriginalWriterTransaction.execute(fixture.target(),fixture::material,
                ignored -> WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER));
        var prepared = ClosedColdInputsConsumer.prepare(fixture::material,committed,fixture::canonical);
        var basis = ClosedAdoptionTransactionTest.publish(fixture.root().resolve("post-exit-basis.json"),prepared.basisBytes());
        var qualification = ClosedAdoptionTransactionTest.publish(fixture.root().resolve("post-exit-qualification.json"),
                prepared.qualificationBytes(basis.reference()));
        return new Context(fixture,committed,basis,qualification);
    }

    /** Alters only the owning Java context after the real consumer's actual kernel exit was observed. */
    private static OriginalWriterTransaction.ManagedProcess afterActualExit(
            WindowsFileWriterSession actual, Runnable afterExit) {
        return new OriginalWriterTransaction.ManagedProcess() {
            private boolean observed;
            @Override public InputStream stdout() { return actual.stdout(); }
            @Override public OutputStream stdin() { return actual.stdin(); }
            @Override public void closeOwnedInput() throws IOException { actual.closeOwnedInput(); }
            @Override public OriginalWriterTransaction.ActualExit awaitActualExit() throws IOException, InterruptedException {
                var exit = actual.awaitActualExit();
                assertTrue(exit.kernelExitObserved());
                assertEquals(0,exit.exitCode());
                if (!observed) { observed = true; afterExit.run(); }
                return exit;
            }
        };
    }

    @Test void lossOfOriginalSdkScopeDuringActualExitRejectsTheConsumerResult() throws Exception {
        var context = context(); var fixture = context.fixture();
        var settings = ClosedAdoptionTransactionTest.settings(fixture);
        AtomicBoolean unavailable = new AtomicBoolean();
        var original = fixture.material();
        var missing = new ClosedAdoptionMaterial(original.input(),original.sources(),original.publishedEpoch(),
                original.publishedPrefix(),original.business(),original.sourceVerifier(),
                ClosedPartialAdmissionVerifier.unavailableOriginalSdk());
        ClosedAdoptionMaterial.CurrentSource current = () -> unavailable.get() ? missing : original;
        AtomicReference<WindowsFileWriterSession> child = new AtomicReference<>();
        try (var authority = ClosedInputsSessionAuthority.open(current,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),settings.leaseDeadline())) {
            assertThrows(ContractViolationException.class,() ->
                    OriginalColdConsumerSession.runOperation(authority,new OriginalColdConsumerSession.ColdInputs(),() -> {
                        var actual = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.ROOT_OPERATION);
                        child.set(actual);
                        return afterActualExit(actual,() -> unavailable.set(true));
                    }));
            assertTrue(unavailable.get(),"failure must occur after the real successful original consumer exit");
            assertNotNull(child.get());
            assertTrue(child.get().actualCommandResult().orElseThrow().passed());
            assertFalse(authority.grantsWarmAttachment());
            assertEquals(ClosedColdInputsConsumer.SCOPE,authority.qualificationScope());
        }
    }

    @Test void closureDuringActualExitRejectsTheConsumerResultOnTheSameOwningThread() throws Exception {
        var context = context(); var fixture = context.fixture();
        var settings = ClosedAdoptionTransactionTest.settings(fixture);
        AtomicReference<WindowsFileWriterSession> child = new AtomicReference<>();
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),Instant.now().plusSeconds(30))) {
            assertThrows(ContractViolationException.class,() ->
                    OriginalColdConsumerSession.runOperation(authority,new OriginalColdConsumerSession.ColdInputs(),() -> {
                        var actual = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.ROOT_OPERATION);
                        child.set(actual);
                        return afterActualExit(actual,authority::close);
                    }));
            assertTrue(authority.isClosed(),"the exact live session was closed after its real consumer exit");
            assertNotNull(child.get());
            assertTrue(child.get().actualCommandResult().orElseThrow().passed());
            assertFalse(authority.grantsWarmAttachment());
        }
    }

    @Test void inputCloseFailureStillAwaitsTheActualChildAndPreservesThePrimaryFailure() throws Exception {
        var context = context(); var fixture = context.fixture();
        var settings = ClosedAdoptionTransactionTest.settings(fixture);
        AtomicReference<WindowsFileWriterSession> child = new AtomicReference<>();
        AtomicInteger closes = new AtomicInteger(), awaits = new AtomicInteger();
        IOException primary = new IOException("input EOF publication failed after original input was closed");
        IOException cleanup = new IOException("second input close publication failed");
        try (var authority = ClosedInputsSessionAuthority.open(fixture::material,context.committed(),fixture::canonical,
                context.basis(),context.qualification(),settings.leaseDeadline())) {
            IOException rejected = assertThrows(IOException.class,() ->
                    OriginalColdConsumerSession.runOperation(authority,new OriginalColdConsumerSession.ColdInputs(),() -> {
                        var actual = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.ROOT_OPERATION);
                        child.set(actual);
                        return new OriginalWriterTransaction.ManagedProcess() {
                            @Override public InputStream stdout() { return actual.stdout(); }
                            @Override public OutputStream stdin() { return actual.stdin(); }
                            @Override public void closeOwnedInput() throws IOException {
                                actual.closeOwnedInput();
                                throw closes.incrementAndGet() == 1 ? primary : cleanup;
                            }
                            @Override public OriginalWriterTransaction.ActualExit awaitActualExit() throws IOException, InterruptedException {
                                awaits.incrementAndGet(); return actual.awaitActualExit();
                            }
                        };
                    }));
            assertSame(primary,rejected);
            assertEquals(2,closes.get());
            assertEquals(1,awaits.get(),"cleanup must await the actual child even when its independent close attempt fails");
            assertEquals(1,rejected.getSuppressed().length);
            assertSame(cleanup,rejected.getSuppressed()[0]);
            assertNotNull(child.get());
            assertTrue(child.get().actualCommandResult().orElseThrow().passed());
        } finally {
            // The regression must also release its real Job if the cleanup implementation regresses.
            if (child.get() != null) { child.get().closeOwnedInput(); child.get().awaitActualExit(); }
        }
    }
}
