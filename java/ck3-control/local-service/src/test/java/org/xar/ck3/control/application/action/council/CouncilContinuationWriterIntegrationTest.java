package org.xar.ck3.control.application.action.council;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;

/** Actual original writer, artifact store, root guards/collector, native wire and continuation issuer. No Game qualification. */
final class CouncilContinuationWriterIntegrationTest {
    @TempDir Path temporary;
    @Test void eachStatusIsDurablyIssuedAndActualOutboundAckHasItsOwnCanonicalEvents() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(temporary.resolve("two-status"), false, true)) {
            f.requestedContinuations = 2; var parent = f.command("council-two-status");
            assertInstanceOf(ActionState.Unknown.class, f.executeCouncil(parent).state());
            assertEquals(1, f.nativeActionWrites()); assertEquals(2, f.continuationWrites());
            assertEquals(2, f.continuationReceipts.size()); var first = f.continuationReceipts.getFirst(); var last = f.continuationReceipts.getLast();
            assertNotEquals(first.request().requestId(), last.request().requestId());
            for (var receipt : f.continuationReceipts) {
                assertEquals(Status.ACK, receipt.status()); var ack = assertInstanceOf(NativeActionPort.AckReceived.class, receipt.outcome().orElseThrow());
                assertEquals(receipt.request().requestId(), ack.outbound().orElseThrow().requestId());
                assertTrue(receipt.request().issuedSequence() < CouncilContinuationCodec.decodeEntry(f.archive.loadMaterial(receipt.latestRecord()).bytes()).resultSequence());
                assertNotEquals(receipt.issued().event(), receipt.resultEvent());
            }
            f.writer.locked(same -> { assertDoesNotThrow(() -> f.continuations.verifyCanonicalChain(same, same.head(), f.continuationReceipts)); return null; });
            long sequence = f.sequence(); var restoredFirst = f.recoverContinuationAfterWriterReopen(first.request().requestId());
            assertEquals(first, restoredFirst, "old result must retain its original historical payload, rather than the latest manifest");
            assertEquals(sequence, f.sequence()); assertEquals(2, f.continuationWrites());
        }
    }
    @Test void failureAfterIssuedCommitBeforeWriteRestoresOnlyExactIdAsUnknown() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(temporary.resolve("before-write"), false, true)) {
            f.failContinuationAt.set(CouncilContinuationCoordinator.Boundary.ISSUED_COMMITTED);
            var command = f.command("council-before-write"); assertInstanceOf(ActionState.Unknown.class, f.executeCouncil(command).state());
            assertEquals(0, f.continuationWrites());
            AtomicReference<Retained> issued = new AtomicReference<>();
            f.writer.locked(same -> { issued.set(assertDoesNotThrow(() -> f.continuations.retained(same)).getLast()); return null; });
            assertEquals(Status.ISSUED, issued.get().status());
            var restored = f.recoverContinuationAfterWriterReopen(issued.get().request().requestId());
            assertEquals(Status.UNKNOWN, restored.status()); assertEquals(0, f.continuationWrites()); assertEquals(1, f.nativeActionWrites());
            byte[] persisted = f.ledgerBytes(); assertEquals(restored, f.recoverContinuationAfterWriterReopen(restored.request().requestId()));
            assertArrayEquals(persisted, f.ledgerBytes()); assertEquals(0, f.continuationWrites());
        }
    }
    @Test void outcomeArchiveFailureLeavesOriginalIssuedAndRecoveryNeverResends() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(temporary.resolve("after-archive"), false, true)) {
            f.failContinuationAt.set(CouncilContinuationCoordinator.Boundary.OUTCOME_ARCHIVED);
            assertInstanceOf(ActionState.Unknown.class, f.executeCouncil(f.command("council-after-archive")).state());
            AtomicReference<Retained> retained = new AtomicReference<>();
            f.writer.locked(same -> { retained.set(assertDoesNotThrow(() -> f.continuations.retained(same)).getLast()); return null; });
            assertEquals(Status.ISSUED, retained.get().status()); assertEquals(1, f.continuationWrites());
            assertEquals(Status.UNKNOWN, f.recoverContinuationAfterWriterReopen(retained.get().request().requestId()).status());
            assertEquals(1, f.continuationWrites());
        }
    }
    @Test void committedAckSurvivesReturnFailureAndIsRecoveredWithoutReadingOrWritingNative() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(temporary.resolve("after-commit"), false, true)) {
            f.failContinuationAt.set(CouncilContinuationCoordinator.Boundary.OUTCOME_COMMITTED);
            assertInstanceOf(ActionState.Unknown.class, f.executeCouncil(f.command("council-after-commit")).state());
            AtomicReference<Retained> retained = new AtomicReference<>();
            f.writer.locked(same -> { retained.set(assertDoesNotThrow(() -> f.continuations.retained(same)).getLast()); return null; });
            assertEquals(Status.ACK, retained.get().status()); long sequence = f.sequence(); int reads = f.nativePacketReads();
            assertEquals(Status.ACK, f.recoverContinuationAfterWriterReopen(retained.get().request().requestId()).status());
            assertEquals(sequence, f.sequence()); assertEquals(reads, f.nativePacketReads()); assertEquals(1, f.continuationWrites());
        }
    }
    @Test void unknownBlocksSecondStatusAndRetainsActualPacketWithoutNewNonceOnRecovery() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(temporary.resolve("unknown"), false, true)) {
            f.loseContinuationAck(); f.requestedContinuations = 2; var command = f.command("council-unknown");
            assertInstanceOf(ActionState.Unknown.class, f.executeCouncil(command).state());
            assertEquals(1, f.continuationWrites()); assertEquals(1, f.continuationReceipts.size());
            var retained = f.continuationReceipts.getFirst(); assertEquals(Status.UNKNOWN, retained.status());
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, retained.outcome().orElseThrow()); assertTrue(unknown.originalRequestPacket().length > 0);
            var recovered = f.recoverContinuationAfterWriterReopen(retained.request().requestId()); assertEquals(retained, recovered);
            assertEquals(1, f.continuationWrites()); assertEquals(1, f.nativeActionWrites());
        }
    }
    @Test void canonicalVerifierRejectsChangedEventBytesAndForeignWriterSession() throws Exception {
        try (var f = new ActionWriterIntegrationFixture(temporary.resolve("original"), false, true);
                var other = new ActionWriterIntegrationFixture(temporary.resolve("other"), false)) {
            f.executeCouncil(f.command("council-integrity")); var receipt = f.continuationReceipts.getFirst();
            other.writer.locked(same -> { assertThrows(RuntimeException.class, () -> f.continuations.verifyCanonicalChain(same, same.head(), List.of(receipt))); return null; });
            Path event = Path.of(receipt.resultEvent().path()); byte[] original = Files.readAllBytes(event); byte[] changed = original.clone(); changed[changed.length - 1] ^= 1;
            Files.write(event, changed);
            assertThrows(Exception.class, () -> f.writer.locked(same -> { try { f.continuations.verifyCanonicalChain(same, same.head(), List.of(receipt)); } catch (IOException failure) { throw new java.io.UncheckedIOException(failure); } return null; }));
            assertEquals(1, f.continuationWrites());
        }
    }
}
