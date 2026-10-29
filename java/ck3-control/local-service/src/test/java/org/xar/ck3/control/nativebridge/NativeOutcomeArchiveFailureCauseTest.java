package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Java transport failure -> canonical receipt/archive/DATA/cold continuation.
 * The extra enum cases are explicitly serialization DATA, not live Endpoint or Game evidence. */
final class NativeOutcomeArchiveFailureCauseTest {
    @TempDir Path root;
    private static final String V1 = "xar.native-dispatch-archive/v1";
    private static final String V4 = "xar.native-dispatch-archive/v4";
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode metadata(ExactRef ref) throws Exception {
        return (ObjectNode) StrictJson.parse(Files.readAllBytes(Path.of(ref.path())), StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static ExactRef altered(ActionWriterIntegrationFixture actual, ObjectNode value) {
        return actual.archive.preserveMaterial(new RawJson(StrictJson.canonical(value, StrictJson.EXPLICIT_MAX_BYTES)));
    }
    private static void rejects(ActionWriterIntegrationFixture actual, ObjectNode value) {
        ExactRef ref = altered(actual, value);
        assertThrows(RuntimeException.class, () -> actual.archive.load(ref));
    }

    private void actualIoFailure(boolean afterWriteReturned) throws Exception {
        var dispatched = new AtomicInteger();
        ActionWriterIntegrationFixture actual;
        if (afterWriteReturned) {
            var action = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),
                    "game.command.pause-map",
                    (command, attempt, dispatch) -> { throw new AssertionError("a receive failure cannot produce a postcondition"); },
                    () -> dispatched.incrementAndGet());
            actual = new ActionWriterIntegrationFixture(root.resolve("actual-response-wait"), false, action);
            actual.loseActionAckOnce();
        } else actual = new ActionWriterIntegrationFixture(root.resolve("actual-write"), true);
        try (actual) {
            ActionCommand command = actual.command("original-typed-io-failure");
            ActionReceipt receipt = actual.coordinator.execute(command);
            var pending = assertInstanceOf(ActionState.Unknown.class, receipt.state());
            var original = assertInstanceOf(NativeActionPort.Unknown.class, pending.dispatch().orElseThrow());
            var cause = original.failureCause().orElseThrow();
            assertEquals(NativeActionPort.FailureKind.IO_FAILURE, cause.kind());
            assertEquals(afterWriteReturned ? NativeActionPort.FailureStage.RESPONSE_WAIT : NativeActionPort.FailureStage.WRITE, cause.stage());
            assertEquals("java.io.IOException", cause.originalException().orElseThrow().javaType());
            assertTrue(cause.deadline().isEmpty(), "ordinary IO failure never acquires deadline evidence from its reason");
            ExactRef ref = actual.archive.referenceOf(original);
            assertEquals(V4, StrictJson.text(metadata(ref).get("schema")));
            assertEquals(cause, NativeFailureCauseCodec.decodeValue(metadata(ref).get("failure_cause")));
            assertEquals(original, actual.archive.load(ref));
            assertEquals(ref, actual.archive.preserve(original));
            assertEquals(original, NativeArchiveDataCodec.retainedFiles().decodeDispatchData(ref));
            ExactRef receiptRef = actual.archive.receiptReferenceOf(receipt);
            assertEquals(receipt, actual.archive.loadReceipt(receiptRef));
            byte[] encoded = ActionReceiptCodec.encodeReceipt(receipt, actual.archive);
            assertEquals(receipt, ActionReceiptCodec.decodeReceipt(encoded, actual.archive));
            actual.writer.locked(same -> {
                ExactRef record = ContinuityActionJournal.recordHead(same.head().state()).orElseThrow();
                assertEquals(receipt, actual.archive.loadRecord(record).receipt());
                return null;
            });
            byte[] ledger = actual.ledgerBytes();
            ActionReceipt cold = actual.reopenAndReturnExisting(command);
            assertEquals(receipt, cold);
            var retained = assertInstanceOf(NativeActionPort.Unknown.class, ActionTransitions.dispatch(cold.state()).orElseThrow());
            assertEquals(cause, retained.failureCause().orElseThrow());
            assertArrayEquals(original.originalRequestPacket(), retained.originalRequestPacket());
            assertEquals(original.rawReturn(), retained.rawReturn());
            assertEquals(ref, actual.archive.referenceOf(retained));
            assertEquals(1, actual.nativeActionWrites());
            if (afterWriteReturned) assertEquals(1, dispatched.get());
            assertArrayEquals(ledger, actual.ledgerBytes());
        }
    }
    @Test void actualWriteIoUnknownCauseSurvivesAllArchiveReadersAndColdContinuationWithoutReplay() throws Exception {
        actualIoFailure(false);
    }
    @Test void actualResponseWaitIoUnknownCauseSurvivesAllArchiveReadersAndColdContinuationWithoutReplay() throws Exception {
        actualIoFailure(true);
    }

    @Test void oldUnclassifiedUnknownRetainsExactV1MetadataAndCannotInferDeadlineFromReason() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("historical-v1"), false)) {
            byte[] packet = new byte[] {1, 0, 2, 0};
            var legacy = new NativeActionPort.Unknown("historical-original", "deadline timeout was mentioned by old diagnostic only", packet, Optional.empty());
            ExactRef ref = actual.archive.preserve(legacy);
            ExactRef packetRef = actual.archive.artifactStore().referenceOf(packet, WriterContracts.MAX_PIN_BYTES).reference();
            ObjectNode expected = StrictJson.object().put("schema", V1).put("request_id", legacy.requestId())
                    .put("kind", "UNKNOWN").put("reason", legacy.reason());
            expected.set("request_packet_ref", packetRef.toJson());
            assertArrayEquals(StrictJson.canonical(expected, StrictJson.EXPLICIT_MAX_BYTES), Files.readAllBytes(Path.of(ref.path())));
            assertEquals(legacy, actual.archive.load(ref));
            assertEquals(ref, actual.archive.referenceOf(legacy));
            assertTrue(((NativeActionPort.Unknown) NativeArchiveDataCodec.retainedFiles().decodeDispatchData(ref)).failureCause().isEmpty());
            var explicitEmpty = new NativeActionPort.Unknown(legacy.requestId(), legacy.reason(), packet, Optional.empty(), Optional.empty());
            assertEquals(ref, actual.archive.preserve(explicitEmpty));
            assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void everyFailureKindAndLegalStageRetainsNullableDiagnosticsAndLargeOriginalBytesAsData() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("typed-data"), false)) {
            byte[] largePacket = new byte[Math.min(1_048_576, RawJson.MAXIMUM_BYTES)];
            java.util.Arrays.fill(largePacket, (byte) 37);
            for (var kind : NativeActionPort.FailureKind.values()) for (var stage : NativeActionPort.FailureStage.values()) {
                if (kind == NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED && stage != NativeActionPort.FailureStage.RESPONSE_WAIT) continue;
                Optional<NativeActionPort.OriginalException> exception = kind == NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED
                        ? Optional.empty() : Optional.of(new NativeActionPort.OriginalException("java.io.IOException", stage == NativeActionPort.FailureStage.WRITE ? null : ""));
                Optional<NativeActionPort.OriginalException> nested = exception.isPresent()
                        ? Optional.of(new NativeActionPort.OriginalException("java.lang.IllegalStateException", "原始原因😀")) : Optional.empty();
                Optional<NativeActionPort.DeadlineObservation> deadline = kind == NativeActionPort.FailureKind.DEADLINE_EXPIRED
                        ? Optional.of(new NativeActionPort.DeadlineObservation(Instant.parse("2026-10-25T01:00:00Z"), Instant.parse("2026-10-25T01:00:01Z"), false)) : Optional.empty();
                var cause = new NativeActionPort.FailureCause(kind, stage, exception, nested, deadline);
                var data = new NativeActionPort.Unknown("data-" + kind + "-" + stage, "serialization DATA; no live timeout qualification", largePacket,
                        Optional.of(raw("{\"tuple_json_domain\":[1,[2,3],null,[],{}]}")), Optional.of(cause));
                ExactRef ref = actual.archive.preserve(data);
                assertEquals(data, actual.archive.load(ref));
                assertEquals(data, NativeArchiveDataCodec.retainedFiles().decodeDispatchData(ref));
                assertEquals(ref, actual.archive.referenceOf(data));
                assertEquals(cause, NativeFailureCauseCodec.decodeValue(metadata(ref).get("failure_cause")));
                assertArrayEquals(largePacket, ((NativeActionPort.Unknown) actual.archive.load(ref)).originalRequestPacket());
            }
            assertEquals(0, actual.nativeActionWrites());
        }
    }

    @Test void v4RequiresStrictUnknownCauseAndOldVersionsRejectNewFieldsInsteadOfLosingThem() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("strict-fields"), false)) {
            var cause = new NativeActionPort.FailureCause(NativeActionPort.FailureKind.IO_FAILURE, NativeActionPort.FailureStage.RESPONSE_WAIT,
                    Optional.of(new NativeActionPort.OriginalException("java.io.IOException", "")), Optional.empty(), Optional.empty());
            var data = new NativeActionPort.Unknown("typed-negative-data", "the reason says timeout but is ordinary IO", new byte[] {9, 8, 7}, Optional.empty(), Optional.of(cause));
            ExactRef ref = actual.archive.preserve(data); ObjectNode original = metadata(ref);
            ObjectNode missing = original.deepCopy(); missing.remove("failure_cause"); rejects(actual, missing);
            ObjectNode nullCause = original.deepCopy(); nullCause.putNull("failure_cause"); rejects(actual, nullCause);
            ObjectNode boolCause = original.deepCopy(); boolCause.put("failure_cause", true); rejects(actual, boolCause);
            ObjectNode legacy = original.deepCopy(); legacy.put("schema", V1); rejects(actual, legacy);
            ObjectNode wrongBranch = original.deepCopy(); wrongBranch.put("kind", "ACK"); rejects(actual, wrongBranch);
            ObjectNode wrongKind = original.deepCopy(); ((ObjectNode) wrongKind.get("failure_cause")).put("kind", "TIMEOUT_BY_REASON"); rejects(actual, wrongKind);
            ObjectNode wrongStage = original.deepCopy(); ((ObjectNode) wrongStage.get("failure_cause")).put("stage", "RETRY"); rejects(actual, wrongStage);
            ObjectNode extra = original.deepCopy(); ((ObjectNode) extra.get("failure_cause")).put("retry_allowed", true); rejects(actual, extra);
            ObjectNode missingMessage = original.deepCopy(); ((ObjectNode) missingMessage.get("failure_cause").get("exception")).remove("message"); rejects(actual, missingMessage);
            ObjectNode wrongMessage = original.deepCopy(); ((ObjectNode) wrongMessage.get("failure_cause").get("exception")).put("message", false); rejects(actual, wrongMessage);
            ObjectNode fakeDeadline = original.deepCopy(); ((ObjectNode) fakeDeadline.get("failure_cause")).put("kind", "DEADLINE_EXPIRED"); rejects(actual, fakeDeadline);
            assertEquals(data, actual.archive.load(ref));
            assertEquals(ref, actual.archive.referenceOf(data));
            assertEquals(0, actual.nativeActionWrites());
        }
    }
}
