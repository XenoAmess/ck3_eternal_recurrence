package org.xar.ck3.control.wave2.finance.giftpendingroute;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Optional;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.CheckpointRead;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ExistingCheckpointPort;
import org.xar.ck3.control.wave2.finance.giftroute.GiftRouteCoordinator.ProcessObservation;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ObjectEvidence;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.Change;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.Command;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.Commit;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.ExistingOwnedReadPort;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.Frame;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.OriginalWriterPort;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.QueryId;
import org.xar.ck3.control.wave2.finance.giftpendingroute.GiftPendingReadRoute.Step;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Envelope;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Read;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransportCodec;

/** Fixture ports prove Java route/reducer integration only, never production lock or native effects. */
final class GiftPendingReadRouteTest {
    private static final String ID = "faction-gift-" + "0".repeat(32);
    private static JsonNode golden() throws IOException {
        try (var stream = GiftPendingReadRouteTest.class.getResourceAsStream("/giftpendingroute/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual original read-route producer/consumer capture required"); }
            return StrictJson.parse(stream.readAllBytes(), 98_304);
        }
    }
    private static byte[] wire(JsonNode node) { return GiftPendingCodec.encodeObjectProjection(node); }
    @Test void actualOriginalRoutesAndTheirPendingReducersMatchAcrossEveryCapturedExit() throws IOException {
        JsonNode golden = golden(); assertEquals(11, golden.path("cases").size());
        for (JsonNode item : golden.get("cases")) {
            FixturePort port = new FixturePort(item); PendingAction pending = port.ledger.pending().orElseThrow();
            boolean cold = item.path("cold").booleanValue(); JsonNode expected = item.get("expected");
            BigInteger revision = item.get("expected_revision").bigIntegerValue();
            if (expected.path("returned").booleanValue()) {
                ObjectEvidence result = cold
                        ? GiftPendingReadRouteCodec.coldEvidence(GiftPendingReadRoute.queryCold(pending, revision, port, () -> ID))
                        : GiftPendingReadRouteCodec.receiptEvidence(GiftPendingReadRoute.queryReceipt(pending, revision, port, () -> ID));
                assertEquals(expected.get("result"), StrictJson.parse(result.json().getBytes(StandardCharsets.UTF_8)), item.path("name").asText());
            } else {
                RuntimeException error = assertThrows(RuntimeException.class, () -> {
                    if (cold) { GiftPendingReadRoute.queryCold(pending, revision, port, () -> ID); }
                    else { GiftPendingReadRoute.queryReceipt(pending, revision, port, () -> ID); }
                });
                assertEquals(expected.get("error").textValue(), error.getMessage(), item.path("name").asText());
                if (error instanceof GiftPendingReadRoute.ColdUnresolved unresolved) {
                    assertEquals(expected.get("step_result"), StrictJson.parse(GiftPendingReadRouteCodec.coldEvidence(unresolved.result()).json().getBytes(StandardCharsets.UTF_8)));
                }
            }
            assertEquals(item.get("sent"), port.sent, item.path("name").asText());
            assertEquals(item.get("recorded"), port.recorded, item.path("name").asText());
            assertEquals(item.get("ledger_after"), StrictJson.parse(GiftPendingCodec.encodeLedger(port.ledger)), item.path("name").asText());
            for (JsonNode command : port.sent) {
                assertTrue(command.path("step").textValue().equals(Step.RECEIPT.wire()) || command.path("step").textValue().equals(Step.COLD.wire()));
                assertFalse(command.path("request_id").textValue().equals(pending.requestId()));
            }
        }
    }
    @Test void rawFloatMaterialCannotBeNormalizedIntoAnIntegerBySharedEnvelopeProducer() throws IOException {
        JsonNode item = golden().path("cases").get(0); FixturePort port = new FixturePort(item);
        PendingAction pending = port.ledger.pending().orElseThrow();
        String integer = pending.baseline().snapshotRevision().add(BigInteger.ONE).toString();
        port.rawEnvelope = port.rawEnvelope.replace("\"post_snapshot_revision\":" + integer, "\"post_snapshot_revision\":" + integer + ".0");
        assertThrows(IllegalArgumentException.class, () -> GiftPendingReadRoute.queryReceipt(pending,
                item.get("expected_revision").bigIntegerValue(), port, () -> ID));
        assertTrue(port.ledger.pending().isPresent()); assertEquals(0, port.writerCalls);
        assertEquals(1, port.sent.size()); assertEquals(0, port.recorded.size());
    }
    @Test void zeroFailureFlagsRequireActualNativeIntegerAndColdTimeoutKeepsRestoreMarker() throws IOException {
        JsonNode item = golden().path("cases").get(5); FixturePort port = new FixturePort(item);
        PendingAction pending = port.ledger.pending().orElseThrow(); port.rawEnvelope = port.rawEnvelope.replace("\"failure_flags\":0", "\"failure_flags\":false");
        assertThrows(IllegalArgumentException.class, () -> GiftPendingReadRoute.queryCold(pending,
                item.get("expected_revision").bigIntegerValue(), port, () -> ID));
        assertTrue(port.ledger.pending().isPresent()); assertEquals(1, port.writerCalls);
        assertEquals(org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingStatus.RESTORE_REQUERY_REQUIRED,
                port.ledger.pending().orElseThrow().status());
    }
    @Test void originalWriterPortMustExecuteTheActualReducerOnceAndReturnItsExactCandidate() throws IOException {
        JsonNode item = golden().path("cases").get(0); FixturePort port = new FixturePort(item); port.skipWriterCallback = true;
        PendingAction pending = port.ledger.pending().orElseThrow();
        assertThrows(RuntimeException.class, () -> GiftPendingReadRoute.queryReceipt(pending,
                item.get("expected_revision").bigIntegerValue(), port, () -> ID));
        assertTrue(port.ledger.pending().isPresent()); assertEquals(0, port.recorded.size());
        FixturePort twice = new FixturePort(item); twice.duplicateWriterCallback = true;
        assertThrows(GiftPendingReadRoute.RouteFailure.class, () -> GiftPendingReadRoute.queryReceipt(twice.ledger.pending().orElseThrow(),
                item.get("expected_revision").bigIntegerValue(), twice, () -> ID));
        assertTrue(twice.ledger.pending().isPresent());
    }
    private static final class FixturePort implements ExistingOwnedReadPort {
        private final JsonNode input;
        private Ledger ledger;
        private final ArrayNode sent = StrictJson.object().arrayNode();
        private final ArrayNode recorded = StrictJson.object().arrayNode();
        private String rawEnvelope;
        private int writerCalls;
        private boolean skipWriterCallback;
        private boolean duplicateWriterCallback;
        FixturePort(JsonNode input) {
            this.input = input; ledger = GiftPendingCodec.decodeLedger(wire(input.get("pending_ledger")));
            rawEnvelope = input.get("raw_envelope_json").isNull() ? null : input.get("raw_envelope_json").textValue();
        }
        @Override public ProcessObservation observeCurrentProcess(PendingAction pending) {
            JsonNode current = input.get("current_process");
            return new ProcessObservation(new ProcessIdentity(current.get("pid").bigIntegerValue(), current.get("creation_date").textValue()), pending.sourceProcess());
        }
        @Override public Frame takeInternalSemanticSnapshot() { return GiftPendingReadRouteCodec.decodeFrame(wire(input.get("snapshot"))); }
        @Override public void sendOriginalRead(Command command) { sent.add(StrictJson.parse(GiftPendingReadRouteCodec.encodeCommand(command))); }
        @Override public Optional<Envelope> waitForOriginalCommandResult(QueryId id, Duration timeout) {
            assertEquals(ID, id.value()); assertEquals(Duration.ofSeconds(30), timeout);
            return rawEnvelope == null ? Optional.empty() : Optional.of(GiftReadTransportCodec.decodeEnvelope(rawEnvelope.getBytes(StandardCharsets.UTF_8)));
        }
        @Override public Read<String> currentPrivateRoundId() { return Read.of(input.get("round_id").textValue()); }
        @Override public ExistingCheckpointPort originalCheckpointReader() {
            return () -> {
                JsonNode checkpoint = input.get("checkpoint");
                if (checkpoint.isNull()) { return Optional.empty(); }
                return Optional.of(new CheckpointRead(checkpoint.get("status").textValue(), Read.of(checkpoint.get("sha256").textValue()),
                        Read.of(checkpoint.get("date_raw").bigIntegerValue()), Read.of(checkpoint.get("episode_run_id").textValue()),
                        new ObjectEvidence(new String(wire(checkpoint), StandardCharsets.UTF_8))));
            };
        }
        @Override public OriginalWriterPort originalPendingWriter() {
            return new OriginalWriterPort() {
                @Override public <T> Commit<T> applyUnderOriginalWriterLock(Function<Ledger, Change<T>> transition) {
                    writerCalls++; if (skipWriterCallback) { return null; }
                    Change<T> changed = transition.apply(ledger);
                    if (duplicateWriterCallback) { transition.apply(ledger); }
                    ledger = GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(changed.candidate()));
                    return new Commit<>(ledger, changed.material());
                }
            };
        }
        @Override public void recordOriginalCommand(Step step, boolean ok, ObjectEvidence result, Optional<String> error) {
            ArrayNode row = recorded.addArray(); row.add(step.wire()); row.add(ok); row.add(StrictJson.parse(result.json().getBytes(StandardCharsets.UTF_8)));
            if (error.isPresent()) { row.add(error.orElseThrow()); } else { row.addNull(); }
        }
    }
}
