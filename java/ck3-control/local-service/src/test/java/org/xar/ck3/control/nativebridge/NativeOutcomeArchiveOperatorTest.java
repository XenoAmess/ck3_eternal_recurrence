package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootOperatorGuardEvidence;

/** Actual readiness READ/packet/archive originals feed untrusted Operator DATA only.
 * No ordinary guard is promoted to operator authority; no Root, writer, ACK or private permit is forged. */
final class NativeOutcomeArchiveOperatorTest {
    @TempDir Path root;
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private record Data(ActionCommand command, GuardEvidence guard, NativeRequest prepared, ActionReceipt receipt) { }

    private static Data untrustedData(ActionWriterIntegrationFixture actual, List<ExactRef> supporting) throws Exception {
        // This is the existing genuine software readiness producer, not a new Root or guard factory.
        var base = actual.command("unqualified-operator-guard-data");
        var original = actual.lastNestedRead.get().before().binding();
        var request = new OperatorPlayerSwitch.Request(99, base.origin().expectedRevision());
        ExactRef unqualifiedDriver = actual.archive.preserveMaterial(raw("{\"unqualified_operator_driver_DATA\":true}"));
        var expectation = new OperatorRebindExpectation(base.origin(), base.source(), request,
                base.before().frame().episodeRunId(), 0, unqualifiedDriver);
        var command = new ActionCommand(base.actionId(), base.origin(), base.source(), base.sessionId(),
                new OperationKey(request.step()), base.arguments(), new CommandExpectation.OperatorRebind(expectation),
                base.claims(), base.deadline(), base.protocolIdentity());
        // An untrusted caller can construct DATA; these copied readiness bytes do not mint the
        // actual source-owned operator guard. The archive must reject them before publication.
        var guard = new GuardEvidence(command.origin(), command.source(), command.sessionId(), original.connectionGeneration(),
                command.operation(), original.nativeEvidence(), original.capabilityEvidence(), original.authorityId(),
                original.observedAt(), original.validUntil(), supporting);
        var prepared = new NativeRequest(request.step(), Optional.of(OperatorPlayerSwitch.CAPABILITY), raw("{}"));
        actual.archive.preserveRequest(prepared); // Explicit untrusted request DATA; no consumed permit or dispatch.
        var attempt = new ActionState.Attempt(RequestIds.forCommand(command), original.observedAt(), guard, prepared);
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Submitting(attempt));
        assertEquals(0, actual.nativeActionWrites());
        return new Data(command, guard, prepared, receipt);
    }
    private static ExactRef retainBytes(ActionWriterIntegrationFixture actual, byte[] bytes) throws Exception {
        return actual.writer.locked(same -> actual.archive.preserveArtifact(same, bytes, StrictJson.EXPLICIT_MAX_BYTES));
    }
    private static ExactRef metadata(ActionWriterIntegrationFixture actual, Data data) throws Exception {
        byte[] bytes = ActionReceiptCodec.encodeReceipt(data.receipt(), actual.archive);
        assertEquals(data.receipt(), ActionReceiptCodec.decodeReceipt(bytes, actual.archive)); // Strict untrusted DATA, not qualification.
        return retainBytes(actual, bytes);
    }
    private static long files(Path path) throws Exception {
        try (var tree = Files.walk(path)) { return tree.filter(Files::isRegularFile).count(); }
    }
    private static Throwable deepest(Throwable failure) {
        while (failure.getCause() != null) failure = failure.getCause();
        return failure;
    }
    private static void sameRootFailure(Throwable expected, Throwable actual) {
        assertEquals(deepest(expected).getClass(), deepest(actual).getClass());
        assertEquals(deepest(expected).getMessage(), deepest(actual).getMessage());
    }
    private static void rejectThroughActualCodecAndArchive(ActionWriterIntegrationFixture actual, Data data, ExactRef metadata) throws Exception {
        byte[] ledger = actual.ledgerBytes(); long count = files(actual.root);
        actual.writer.locked(same -> {
            var archive = actual.archive.withSession(same);
            var codecFailure = assertThrows(Exception.class,
                    () -> RootOperatorGuardEvidence.requireHistorical(same, data.command(), data.guard(), archive));
            sameRootFailure(codecFailure, assertThrows(RuntimeException.class, () -> archive.preserveReceipt(data.receipt())));
            sameRootFailure(codecFailure, assertThrows(RuntimeException.class, () -> archive.loadReceipt(metadata)));
            sameRootFailure(codecFailure, assertThrows(RuntimeException.class, () -> archive.receiptReferenceOf(data.receipt())));
            return null;
        });
        assertEquals(count, files(actual.root)); assertArrayEquals(ledger, actual.ledgerBytes());
        assertEquals(0, actual.nativeActionWrites()); assertEquals(0, actual.snapshot().ledgerSequence());
    }

    @Test void ordinaryReadinessOriginalsNeverBecomeAnOperatorGuardByChangingTheExpectation() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("ordinary"), false)) {
            Data data = untrustedData(actual, List.of());
            ExactRef metadata = metadata(actual, data);
            rejectThroughActualCodecAndArchive(actual, data, metadata);
            assertTrue(actual.nativeReadWrites() > 0); // Existing real readiness producer ran; no fabricated Ready was supplied.
        }
    }
    @Test void missingSourceOwnedGuardOriginalIsNeverRecreatedByProducerOrColdRead() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("missing"), false)) {
            ExactRef basis = actual.archive.preserveMaterial(raw("{\"untrusted_operator_guard_DATA\":true}"));
            Data data = untrustedData(actual, List.of(basis)); ExactRef metadata = metadata(actual, data);
            Path missing = Path.of(basis.path()); assertTrue(missing.normalize().startsWith(actual.root.normalize()));
            Files.delete(missing);
            rejectThroughActualCodecAndArchive(actual, data, metadata);
            assertFalse(Files.exists(missing));
        }
    }
    @Test void malformedOperatorGuardDataUsesTheSameSoleCodecAndColdArchiveWithoutAnOrdinaryFallback() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("malformed"), false)) {
            for (String invalid : List.of("{\"schema\":\"ordinary-readiness/v1\"}", "[]",
                    "{\"schema\":\"xar.java.operator-current-guard/v1\",\"schema\":\"duplicate\"}")) {
                // The actual bounded raw artifact producer may retain invalid bytes for diagnosis.
                // Neither that custody nor a matching schema string makes them an operator guard.
                ExactRef basis = retainBytes(actual, invalid.getBytes(StandardCharsets.UTF_8));
                Data data = untrustedData(actual, List.of(basis)); ExactRef metadata = metadata(actual, data);
                rejectThroughActualCodecAndArchive(actual, data, metadata);
            }
        }
    }
    @Test void actualSoftwareHeartbeatOriginalUsesTheSoleClosedPacketReaderAndMissingBytesAreNotRepaired() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("heartbeat"), false)) {
            actual.ready();
            var transport = actual.physicalInputs().transport(); Instant deadline = Instant.now().plusSeconds(5);
            var originalSnapshot = transport.observe(deadline);
            byte[] priorHeartbeat = transport.diagnostics().latestHeartbeat()
                    .map(received -> received.original().packet().value()).orElseGet(() -> new byte[0]);
            // The existing endpoint itself emits heartbeat mailbox facts from this exact original
            // snapshot. The test supplies neither a heartbeat body nor an ACK/chronology.
            actual.enqueueSoftwareNativePacket(originalSnapshot.originalPacket());
            for (int i = 0; i < 8 && Instant.now().isBefore(deadline)
                    && transport.diagnostics().latestHeartbeat().map(received -> Arrays.equals(
                            priorHeartbeat, received.original().packet().value())).orElse(true); i++)
                transport.observe(deadline);
            byte[] heartbeat = transport.diagnostics().latestHeartbeat().orElseThrow().original().packet().value();
            assertFalse(Arrays.equals(priorHeartbeat, heartbeat), "the actual queued heartbeat must be newly consumed");
            var notice = assertInstanceOf(NativeWire.Notice.class, NativeWire.decode(heartbeat));
            assertEquals(NativeWire.NoticeKind.HEARTBEAT, notice.kind());
            ExactRef retained = retainBytes(actual, heartbeat);
            byte[] ledger = actual.ledgerBytes(); long count = files(actual.root);
            actual.writer.locked(same -> {
                assertArrayEquals(heartbeat, actual.archive.withSession(same).readOriginalPacket(retained));
                return null;
            });
            assertEquals(count, files(actual.root)); assertArrayEquals(ledger, actual.ledgerBytes());
            // A real READ command_result remains an ACK, not another accepted original-packet role.
            ExactRef ackPacket = retainBytes(actual, actual.lastNestedRead.get().original().originalPacket());
            assertThrows(RuntimeException.class, () -> actual.archive.readOriginalPacket(ackPacket));
            Path missing = Path.of(retained.path()); assertTrue(missing.normalize().startsWith(actual.root.normalize()));
            Files.delete(missing); long after = files(actual.root);
            assertThrows(RuntimeException.class, () -> actual.archive.readOriginalPacket(retained));
            assertFalse(Files.exists(missing)); assertEquals(after, files(actual.root));
            assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(0, actual.nativeActionWrites());
        }
    }
}
