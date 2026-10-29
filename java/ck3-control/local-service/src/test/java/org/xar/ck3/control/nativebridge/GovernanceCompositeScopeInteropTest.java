package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionScope;

/** Actual Scope -> original writer/journal -> actual central refusal. DATA tokens never fake a source positive. */
final class GovernanceCompositeScopeInteropTest {
    @TempDir Path root;
    private record DataToken(ActionCommand originalParent) implements CompositeContinuationToken {
        @Override public Instant deadline() { return originalParent.deadline(); }
        @Override public Kind kind() { return Kind.SUCCESSOR_UI_CLOSE; }
    }
    private static Path lock(ActionWriterIntegrationFixture actual) {
        return actual.writer.originalLockPath();
    }
    private static GovernanceActionScope scope(ActionWriterIntegrationFixture actual, ActionCommand parent,
            AtomicInteger opened) {
        return new GovernanceActionScope(actual.coordinator, actual.journal, actual.physicalInputs().transport(),
                new GovernanceActionScope.SessionAccess() {
                    @Override public <T> T withSession(ActionCommand command, GovernanceActionScope.SessionWork<T> work)
                            throws IOException, InterruptedException {
                        assertSame(parent, command); opened.incrementAndGet();
                        return actual.writer.locked(same -> {
                            try { return work.run(same); }
                            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
                        });
                    }
                }, lock(actual));
    }
    private static void centralRefusal(GovernanceActionScope scope, CompositeContinuationToken token,
            ContinuityStorePort.Session same) {
        var rejected = assertThrows(IllegalArgumentException.class,
                () -> { if (same == null) scope.continueOriginalComposite(token); else scope.continueOriginalComposite(same, token); });
        assertEquals("original continuation parent is absent", rejected.getMessage(),
                "This is the actual central original-parent check, not the inherited unavailable interface default");
        assertThrows(IllegalStateException.class, () -> GovernanceActionScope.current(token.originalParent()));
    }
    @Test void bothActualEntrypointsReachCentralUnderSameWriterWithoutDispatchOrOpeningGovernanceMailbox() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("same"), false)) {
            var parent = actual.command("absent-original-parent"); var token = new DataToken(parent);
            var opened = new AtomicInteger(); var wrapped = scope(actual, parent, opened);
            var before = actual.writer.persistedHead(); int reads = actual.nativeReadWrites();
            centralRefusal(wrapped, token, null); assertEquals(1, opened.get());
            actual.writer.locked(same -> { centralRefusal(wrapped, token, same); return null; });
            assertEquals(1, opened.get(), "Borrowed path must not reacquire a Session");
            assertEquals(before, actual.writer.persistedHead()); assertEquals(reads, actual.nativeReadWrites());
            assertEquals(0, actual.nativeActionWrites()); assertEquals(0, actual.continuationWrites());
        }
    }
    @Test void actualEscapedAndForeignWriterSessionsRejectBeforeAnyContinuationWork() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("owned"), false);
                var foreign = new ActionWriterIntegrationFixture(root.resolve("foreign"), false)) {
            var parent = actual.command("unissued-parent"); var token = new DataToken(parent);
            var opened = new AtomicInteger(); var wrapped = scope(actual, parent, opened);
            var escaped = new AtomicReference<ContinuityStorePort.Session>();
            actual.writer.locked(same -> { escaped.set(same); return null; });
            assertThrows(ContractViolationException.class, () -> wrapped.continueOriginalComposite(escaped.get(), token));
            foreign.writer.locked(same -> { assertThrows(ContractViolationException.class,
                    () -> wrapped.continueOriginalComposite(same, token)); return null; });
            assertEquals(0, opened.get()); assertEquals(0, actual.nativeActionWrites()); assertEquals(0, foreign.nativeActionWrites());
        }
    }
    @Test void interruptionIsCheckedFailureAndRestoresInterruptWithoutDispatch() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("interrupted"), false)) {
            var parent = actual.command("interrupted-unissued-parent");
            var wrapped = new GovernanceActionScope(actual.coordinator, actual.journal, actual.physicalInputs().transport(),
                    new GovernanceActionScope.SessionAccess() {
                        @Override public <T> T withSession(ActionCommand command, GovernanceActionScope.SessionWork<T> work)
                                throws InterruptedException { assertSame(parent, command); throw new InterruptedException("original Session interrupted"); }
                    }, lock(actual));
            try {
                var failure = assertThrows(IOException.class, () -> wrapped.continueOriginalComposite(new DataToken(parent)));
                assertInstanceOf(InterruptedException.class, failure.getCause()); assertTrue(Thread.currentThread().isInterrupted());
                assertEquals(0, actual.nativeActionWrites());
            } finally { Thread.interrupted(); }
        }
    }
}
