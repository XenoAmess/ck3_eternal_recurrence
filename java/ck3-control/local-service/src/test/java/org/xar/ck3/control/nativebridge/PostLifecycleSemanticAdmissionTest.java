package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Negative admission consumes the actual ordinary producer fixture; it never fabricates a qualified lifecycle result. */
final class PostLifecycleSemanticAdmissionTest {
    @TempDir Path temporary;

    private static ActionReceipt uncommittedOrdinary(ActionWriterIntegrationFixture actual) throws Exception {
        var command = actual.command("ordinary-is-not-an-episode-parent");
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
    }

    @Test void anOrdinaryReceiptConstructorCannotAcquireLifecycleSemanticOrChangeNativeAndWriterState() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("ordinary-parent"), false)) {
            ActionReceipt parent = uncommittedOrdinary(actual);
            int nativeReads = actual.nativePacketReads(), queryWrites = actual.nativeReadWrites();
            actual.writer.locked(same -> {
                String head = same.head().digest();
                assertThrows(IllegalArgumentException.class, () -> actual.collector.semanticAfterLifecycle(
                        same, actual.observationIdentity(), parent, Instant.now().plusSeconds(10)));
                assertEquals(head, same.head().digest());
                assertEquals(nativeReads, actual.nativePacketReads());
                assertEquals(queryWrites, actual.nativeReadWrites());
                return null;
            });
        }
    }

    @Test void escapedAndForeignOriginalWriterSessionsFailBeforeAnyPostLifecycleNativeIo() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("owned"), false);
             var foreign = new ActionWriterIntegrationFixture(temporary.resolve("foreign"), false)) {
            ActionReceipt parent = uncommittedOrdinary(actual);
            int nativeReads = actual.nativePacketReads(), queryWrites = actual.nativeReadWrites();
            var escaped = new AtomicReference<ContinuityStorePort.Session>();
            actual.writer.locked(same -> { escaped.set(same); return null; });
            assertThrows(IllegalArgumentException.class, () -> actual.collector.semanticAfterLifecycle(
                    escaped.get(), actual.observationIdentity(), parent, Instant.now().plusSeconds(10)));
            foreign.writer.locked(other -> {
                assertThrows(IOException.class, () -> actual.collector.semanticAfterLifecycle(
                        other, actual.observationIdentity(), parent, Instant.now().plusSeconds(10)));
                return null;
            });
            assertEquals(nativeReads, actual.nativePacketReads());
            assertEquals(queryWrites, actual.nativeReadWrites());
        }
    }

    @Test void crossThreadAndAnotherPhysicalOwnerCannotUseTheOriginalBorrowedScope() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(temporary.resolve("thread-owner"), false)) {
            ActionReceipt parent = uncommittedOrdinary(actual);
            int nativeReads = actual.nativePacketReads(), queryWrites = actual.nativeReadWrites();
            actual.writer.locked(same -> {
                var failure = new AtomicReference<Throwable>();
                Thread other = new Thread(() -> {
                    try {
                        actual.collector.semanticAfterLifecycle(same, actual.observationIdentity(), parent, Instant.now().plusSeconds(10));
                    } catch (Throwable rejected) { failure.set(rejected); }
                }, "post-lifecycle-foreign-thread");
                other.setDaemon(true); other.start();
                try { other.join(5000); }
                catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    throw new java.io.InterruptedIOException("cross-thread admission regression interrupted");
                }
                assertFalse(other.isAlive(), "the writer authority must reject another thread without waiting for a new lock");
                assertInstanceOf(IllegalArgumentException.class, failure.get());
                var owner = actual.observationIdentity();
                var wrong = new SessionPorts.SessionIdentity(owner.machineId(), owner.game(), owner.sessionId() + "-other");
                assertThrows(IllegalArgumentException.class, () -> actual.collector.semanticAfterLifecycle(
                        same, wrong, parent, Instant.now().plusSeconds(10)));
                assertEquals(nativeReads, actual.nativePacketReads());
                assertEquals(queryWrites, actual.nativeReadWrites());
                return null;
            });
        }
    }
}
