package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual ACTION originals feed deliberately invalid settlement DATA. No installed control
 * observer, independent after observation, canonical settlement or Game success is fabricated. */
final class NativeOutcomeArchiveReconciledControlTest {
    @TempDir Path root;

    private static ActionWriterIntegrationFixture.SoftwareActionScenario scenario() {
        return new ActionWriterIntegrationFixture.SoftwareActionScenario(
                new OperationKey("fixture-archive-late-control-v1"), "fixture.archive-late-control",
                (command, attempt, original) -> new ActionPorts.Pending("independent control observation is absent", List.of()),
                () -> { });
    }
    private record Originals(ActionCommand command, ActionReceipt unknownReceipt,
            ActionState.Attempt attempt, NativeActionPort.Unknown unknown,
            NativeActionPort.AckReceived candidate, PlanningReadReceipt beforeActionRead) { }

    private static Originals receiveActual(ActionWriterIntegrationFixture actual) throws Exception {
        actual.loseActionAckOnce();
        var command = actual.command("archive-late-control");
        var receipt = actual.coordinator.execute(command);
        var unknown = assertInstanceOf(ActionState.Unknown.class, receipt.state());
        var attempt = unknown.attempt().orElseThrow();
        var dispatch = assertInstanceOf(NativeActionPort.Unknown.class, unknown.dispatch().orElseThrow());
        actual.releaseLateActionAck();
        var transport = actual.physicalInputs().transport();
        Instant deadline = Instant.now().plusSeconds(5);
        NativeActionPort.AckReceived received = null;
        for (int i = 0; i < 8 && Instant.now().isBefore(deadline); i++) {
            var retained = transport.pollOriginalOutcome(attempt.requestId());
            if (retained.isPresent()) { received = retained.orElseThrow(); break; }
            transport.observe(deadline);
        }
        if (received == null) received = transport.pollOriginalOutcome(attempt.requestId()).orElseThrow();
        new ReconciledControlAck(received).requireMatches(command, attempt, dispatch);
        assertArrayEquals(dispatch.originalRequestPacket(), received.outbound().orElseThrow().originalPacket());
        assertNotNull(actual.lastNestedRead.get());
        assertEquals(1, actual.nativeActionWrites());
        return new Originals(command, receipt, attempt, dispatch, received, actual.lastNestedRead.get());
    }
    private static ActionReceipt negativeData(Originals original, ActionState.Attempt attempt) {
        // This actual query predates the ACTION. It is intentionally not a valid after-state.
        var control = new ActionState.ControlApplied(original.beforeActionRead(), List.of(),
                "paused/v1", original.command().expected().values(),
                Optional.of(new ReconciledControlAck(original.candidate())));
        return new ActionReceipt(original.unknownReceipt().version(), original.unknownReceipt().sequence(),
                original.command(), ActionCodec.bodySha256(original.command()),
                new ActionState.Settled(attempt, original.unknown(), control));
    }
    private static ExactRef retainData(ActionWriterIntegrationFixture actual, byte[] data) throws Exception {
        return actual.writer.locked(same -> actual.archive.preserveArtifact(same, data, StrictJson.EXPLICIT_MAX_BYTES));
    }
    private static long files(Path path) throws Exception {
        try (var entries = Files.walk(path)) { return entries.filter(Files::isRegularFile).count(); }
    }
    private static void messageContains(Throwable failure, String expected) {
        for (Throwable current = failure; current != null; current = current.getCause())
            if (current.getMessage() != null && current.getMessage().contains(expected)) return;
        fail("expected original-binding rejection containing '" + expected + "', got " + failure);
    }

    @Test void actualLateAckCannotHideChangedDurablePreparedFieldsInProducerOrColdReader() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("prepared"), false, scenario())) {
            Originals original = receiveActual(actual);
            actual.archive.preserve(original.candidate());
            byte[] ledger = actual.ledgerBytes();
            for (boolean snapshot : List.of(false, true)) {
                var fields = StrictJson.object();
                if (snapshot) fields.put("expected_snapshot_revision", original.attempt().guard().origin().expectedRevision().add(java.math.BigInteger.ONE));
                else fields.put("not_in_actual_outgoing", true);
                NativeRequest prepared = original.attempt().preparedRequest();
                var changed = new NativeRequest(prepared.step(), prepared.requiredCapability(),
                        new RawJson(fields.toString().getBytes(StandardCharsets.UTF_8)));
                actual.archive.preserveRequest(changed); // Explicitly retained negative DATA, never substituted in the canonical ledger.
                var attempt = new ActionState.Attempt(original.attempt().requestId(), original.attempt().submittedAt(),
                        original.attempt().guard(), changed);
                var data = negativeData(original, attempt);
                new ReconciledControlAck(original.candidate()).requireMatches(original.command(), attempt, original.unknown());
                String rejection = snapshot ? "prepared explicit snapshot revision" : "actual outbound execute fields";
                long count = files(actual.root);
                messageContains(assertThrows(RuntimeException.class, () -> actual.archive.preserveReceipt(data)), rejection);
                assertEquals(count, files(actual.root));
                byte[] encoded = ActionReceiptCodec.encodeReceipt(data, actual.archive);
                assertEquals(data, ActionReceiptCodec.decodeReceipt(encoded, actual.archive)); // Typed DATA only.
                ExactRef metadata = retainData(actual, encoded);
                messageContains(assertThrows(RuntimeException.class, () -> actual.archive.loadReceipt(metadata)), rejection);
            }
            assertArrayEquals(ledger, actual.ledgerBytes());
            assertEquals(original.unknownReceipt(), actual.reopenAndReturnExisting(original.command()));
            assertEquals(1, actual.nativeActionWrites());
        }
    }

    @Test void missingActualUnknownPreparedCandidateAndReadOriginalsAreNeverRecreated() throws Exception {
        for (String role : List.of("unknown", "prepared", "candidate", "read")) {
            try (var actual = new ActionWriterIntegrationFixture(root.resolve("missing-" + role), false, scenario())) {
                Originals original = receiveActual(actual);
                var data = negativeData(original, original.attempt());
                long before = files(actual.root);
                assertThrows(RuntimeException.class, () -> actual.archive.preserveReceipt(data));
                assertThrows(RuntimeException.class, () -> actual.archive.referenceOf(original.candidate()));
                assertEquals(before, files(actual.root)); // Missing candidate is not minted by preserveReceipt.
                ExactRef candidate = actual.archive.preserve(original.candidate());
                ExactRef metadata = retainData(actual, ActionReceiptCodec.encodeReceipt(data, actual.archive));
                ExactRef missing = switch (role) {
                    case "unknown" -> actual.archive.referenceOf(original.unknown());
                    case "prepared" -> actual.archive.requestReferenceOf(original.attempt().preparedRequest());
                    case "candidate" -> candidate;
                    case "read" -> actual.archive.readReferenceOf(original.beforeActionRead());
                    default -> throw new AssertionError(role);
                };
                Path path = Path.of(missing.path());
                assertTrue(path.normalize().startsWith(actual.root.normalize()));
                Files.delete(path); // Only this isolated test's actual archived original.
                long after = files(actual.root); byte[] ledger = actual.ledgerBytes();
                assertThrows(RuntimeException.class, () -> actual.archive.loadReceipt(metadata));
                assertThrows(RuntimeException.class, () -> actual.archive.preserveReceipt(data));
                assertThrows(RuntimeException.class, () -> actual.archive.receiptReferenceOf(data));
                assertFalse(Files.exists(path)); assertEquals(after, files(actual.root));
                assertArrayEquals(ledger, actual.ledgerBytes()); assertEquals(1, actual.nativeActionWrites());
            }
        }
    }

    @Test void actualOriginalsUseStrictV6SerdeAndOldVersionsCannotAcceptTheSidecar() throws Exception {
        try (var actual = new ActionWriterIntegrationFixture(root.resolve("serde"), false, scenario())) {
            Originals original = receiveActual(actual); actual.archive.preserve(original.candidate());
            var data = negativeData(original, original.attempt());
            byte[] bytes = ActionReceiptCodec.encodeReceipt(data, actual.archive);
            var row = (ObjectNode) StrictJson.parse(bytes, StrictJson.EXPLICIT_MAX_BYTES);
            assertEquals(ActionReceiptCodec.RECONCILED_CONTROL_SCHEMA, row.get("schema").textValue());
            assertEquals(data, ActionReceiptCodec.decodeReceipt(bytes, actual.archive));
            assertInstanceOf(NativeActionPort.Unknown.class,
                    ((ActionState.Settled) ActionReceiptCodec.decodeReceipt(bytes, actual.archive).state()).dispatch());
            var oldControl = new ActionState.ControlApplied(original.beforeActionRead(), List.of(),
                    "paused/v1", original.command().expected().values());
            var oldData = new ActionReceipt(data.version(), data.sequence(), data.command(), data.bodySha256(),
                    new ActionState.Settled(original.attempt(), original.unknown(), oldControl));
            byte[] oldBytes = ActionReceiptCodec.encodeReceipt(oldData, actual.archive);
            assertNotEquals(ActionReceiptCodec.RECONCILED_CONTROL_SCHEMA,
                    StrictJson.parse(oldBytes, StrictJson.EXPLICIT_MAX_BYTES).get("schema").textValue());
            assertEquals(oldData, ActionReceiptCodec.decodeReceipt(oldBytes, actual.archive));
            long count = files(actual.root);
            for (String field : List.of("reconciled_ack_ref", "read_ref", "supporting_reads", "observation")) {
                var bad = row.deepCopy(); ((ObjectNode) bad.get("state").get("settlement")).remove(field);
                assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(bad.toString().getBytes(StandardCharsets.UTF_8), actual.archive));
            }
            var wrong = row.deepCopy(); ((ObjectNode) wrong.get("state").get("settlement")).put("reconciled_ack_ref", true);
            assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(wrong.toString().getBytes(StandardCharsets.UTF_8), actual.archive));
            for (String schema : List.of(ActionReceiptCodec.SCHEMA, ActionReceiptCodec.EVOLVED_SCHEMA,
                    ActionReceiptCodec.PROVENANCE_SCHEMA, ActionReceiptCodec.FAMILY_SEND_SCHEMA, ActionReceiptCodec.PHYSICAL_SCHEMA)) {
                var historical = row.deepCopy(); historical.put("schema", schema);
                assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(historical.toString().getBytes(StandardCharsets.UTF_8), actual.archive));
            }
            String json = new String(bytes, StandardCharsets.UTF_8);
            byte[] duplicate = (json.substring(0, json.length() - 1) + ",\"schema\":\""
                    + ActionReceiptCodec.RECONCILED_CONTROL_SCHEMA + "\"}").getBytes(StandardCharsets.UTF_8);
            assertThrows(RuntimeException.class, () -> ActionReceiptCodec.decodeReceipt(duplicate, actual.archive));
            assertEquals(count, files(actual.root)); // Every decode is read-only.
            ExactRef metadata = retainData(actual, bytes);
            assertThrows(RuntimeException.class, () -> actual.archive.loadReceipt(metadata)); // Pre-ACTION read is not independent post-state.
            assertEquals(original.unknownReceipt(), actual.reopenAndReturnExisting(original.command()));
            assertEquals(1, actual.nativeActionWrites());
        }
    }
}
