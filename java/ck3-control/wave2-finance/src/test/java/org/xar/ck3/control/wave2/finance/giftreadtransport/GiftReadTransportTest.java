package org.xar.ck3.control.wave2.finance.giftreadtransport;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.Rejected;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Command;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Diagnostics;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.ExistingOwnedReadPort;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Failure;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.ReadFailure;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.ReadId;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Received;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Request;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Snapshot;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.TimedOut;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Timeout;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.WaitResult;

final class GiftReadTransportTest {
    private static final String FIXED_ID = "faction-gift-read-00000000000000000000000000000000";
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);

    private static JsonNode golden() throws IOException {
        InputStream resource = GiftReadTransportTest.class.getResourceAsStream("/giftreadtransport/producer-golden.json.gz");
        if (resource == null) { throw new IOException("committed producer gzip golden required"); }
        try (InputStream raw = resource; GZIPInputStream gzip = new GZIPInputStream(raw)) {
            byte[] bytes = gzip.readNBytes(180_001);
            if (bytes.length == 0 || bytes.length > 180_000) { throw new IOException("bounded uncompressed artifact required"); }
            return JSON.readTree(bytes);
        }
    }
    private static JsonNode scenario(String name) throws IOException {
        for (JsonNode item : golden().get("cases")) {
            if (name.equals(item.get("name").textValue())) { return item.get("scenario").deepCopy(); }
        }
        throw new IOException("missing producer case " + name);
    }
    private static byte[] bytes(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }

    private static final class Port implements ExistingOwnedReadPort {
        private final JsonNode scenario;
        private int snapshots;
        private int diagnosticReads;
        private int waits;
        private final List<JsonNode> commands = new ArrayList<>();
        Port(JsonNode scenario) { this.scenario = scenario; }
        @Override public Snapshot takeInternalSemanticSnapshot() {
            snapshots++; return GiftReadTransportCodec.decodeSnapshot(bytes(scenario.get(snapshots == 1 ? "before" : "after")));
        }
        @Override public Diagnostics diagnostics() {
            diagnosticReads++; return GiftReadTransportCodec.decodeDiagnostics(bytes(scenario.get("diagnostics")));
        }
        @Override public void send(Command command) {
            try { commands.add(JSON.readTree(GiftReadTransportCodec.encodeCommand(command))); }
            catch (IOException error) { throw new IllegalStateException(error); }
        }
        @Override public WaitResult waitForCommandResult(ReadId requestId, Timeout timeout) {
            waits++;
            assertEquals(0, timeout.seconds().compareTo(scenario.get("request").get("timeout_seconds").decimalValue()));
            if (scenario.get("timeout").booleanValue()) { return new TimedOut(); }
            ObjectNode reply = JSON.createObjectNode(); reply.put("type", "command_result"); reply.put("protocol_version", 1);
            reply.put("request_id", requestId.value()); reply.put("ok", true); reply.set("result", scenario.get("private_result"));
            scenario.get("reply_overrides").properties().forEach(entry -> reply.set(entry.getKey(), entry.getValue()));
            return new Received(GiftReadTransportCodec.decodeEnvelope(bytes(reply)));
        }
    }

    @Test void seventeenOriginalTransportPathsAndEffectsMatchUsingRealJavaCandidatePolicy() throws IOException {
        JsonNode captured = golden(); assertEquals(17, captured.get("cases").size());
        assertEquals(5, captured.get("source_bindings").size());
        assertEquals("xar.gift-read-transport-original-producer-golden.v1", captured.get("schema").textValue());
        for (JsonNode item : captured.get("cases")) {
            JsonNode scenario = item.get("scenario"); Request request = GiftReadTransportCodec.decodeRequest(bytes(scenario.get("request")));
            Port port = new Port(scenario); JsonNode expected = item.get("expected");
            if ("return".equals(expected.get("kind").textValue())) {
                GiftReadTransport.Result actual = GiftReadTransport.query(request, port, () -> FIXED_ID);
                assertEquals(expected.get("result"), JSON.readTree(GiftReadTransportCodec.encodeResult(actual)), item.get("name").textValue());
            } else {
                ReadFailure error = assertThrows(ReadFailure.class, () -> GiftReadTransport.query(request, port, () -> FIXED_ID));
                assertEquals("BridgeUnavailableError", expected.get("error_type").textValue());
                assertEquals(expected.get("message").textValue(), error.getMessage(), item.get("name").textValue());
            }
            JsonNode effects = item.get("effects"); assertEquals(effects.get("snapshots").intValue(), port.snapshots);
            assertEquals(effects.get("diagnostic_reads").intValue(), port.diagnosticReads);
            assertEquals(effects.get("send_count").intValue(), port.commands.size());
            assertEquals(effects.get("wait_count").intValue(), port.waits);
            assertEquals(effects.get("commands"), JSON.valueToTree(port.commands));
        }
    }

    @Test void sourceMismatchAndPrivateRouteOffSendNothing() throws IOException {
        JsonNode changed = scenario("source_changed"); Port changedPort = new Port(changed);
        Request request = GiftReadTransportCodec.decodeRequest(bytes(changed.get("request")));
        ReadFailure error = assertThrows(ReadFailure.class, () -> GiftReadTransport.query(request, changedPort, () -> FIXED_ID));
        assertEquals(Failure.SOURCE_CHANGED, error.failure()); assertEquals(0, changedPort.commands.size());
        assertEquals(0, changedPort.diagnosticReads);
        JsonNode off = scenario("private_route_off"); Port offPort = new Port(off);
        assertTrue(GiftReadTransport.query(GiftReadTransportCodec.decodeRequest(bytes(off.get("request"))), offPort,
                () -> FIXED_ID) instanceof GiftReadTransport.PrivateRouteOff);
        assertEquals(0, offPort.commands.size()); assertEquals(0, offPort.waits);
    }

    @Test void timeoutAndFrameDriftNeverRetryTheReadOrSubmitAGift() throws IOException {
        for (String name : List.of("timed_out", "frame_crossed", "active_event_after", "native_red")) {
            JsonNode source = scenario(name); Port port = new Port(source);
            Request request = GiftReadTransportCodec.decodeRequest(bytes(source.get("request")));
            assertThrows(ReadFailure.class, () -> GiftReadTransport.query(request, port, () -> FIXED_ID));
            assertEquals(1, port.commands.size()); assertEquals(1, port.waits);
            assertEquals("private-query-faction-gift-member-v1", port.commands.getFirst().get("step").textValue());
        }
    }

    @Test void literalIntegerAndBooleanTokensAreNotCoerced() throws IOException {
        JsonNode source = scenario("selected");
        for (String token : List.of("true", "412.0", "\"412\"")) {
            ObjectNode bad = source.get("request").deepCopy();
            ((ObjectNode) bad.get("snapshot")).set("native_revision", JSON.readTree(token));
            assertThrows(ContractViolationException.class, () -> GiftReadTransportCodec.decodeRequest(bytes(bad)));
        }
        ObjectNode diagnostics = JSON.createObjectNode();
        diagnostics.putObject("last_heartbeat").putObject("g2_faction_gift_mitigation_async_glue_v1").put("private_build", 1);
        assertThrows(ContractViolationException.class, () -> GiftReadTransportCodec.decodeDiagnostics(bytes(diagnostics)));
        String duplicate = "{\"schema\":\"xar.gift-read-transport-input.v1\"," + source.get("request").toString().substring(1);
        assertThrows(ContractViolationException.class, () -> GiftReadTransportCodec.decodeRequest(duplicate.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void timeoutDecimalIsExactAndInvalidTimeoutNeverCreatesARequest() throws IOException {
        ObjectNode input = scenario("selected").get("request").deepCopy();
        input.put("timeout_seconds", new BigDecimal("0.125"));
        assertEquals(0, GiftReadTransportCodec.decodeRequest(bytes(input)).timeout().seconds().compareTo(new BigDecimal("0.125")));
        input.put("timeout_seconds", 0);
        assertThrows(IllegalArgumentException.class, () -> GiftReadTransportCodec.decodeRequest(bytes(input)));
        input.put("timeout_seconds", true);
        assertThrows(ContractViolationException.class, () -> GiftReadTransportCodec.decodeRequest(bytes(input)));
    }

    @Test void commandIdentityAndSnapshotCopiesPreserveLargeIntegersAndCannotBeMutated() throws IOException {
        BigInteger identity = new BigInteger("18446744073709551615");
        Command command = new Command(new ReadId(FIXED_ID), identity, identity, identity);
        JsonNode parsed = JSON.readTree(GiftReadTransportCodec.encodeCommand(command));
        assertEquals(identity, parsed.get("expected_revision").bigIntegerValue());
        assertEquals(identity, parsed.get("expected_date_raw").bigIntegerValue());
        Request request = GiftReadTransportCodec.decodeRequest(bytes(scenario("selected").get("request")));
        byte[] exposed = request.expectedSnapshot().original().bytes(); exposed[0] = 0;
        assertEquals((byte) '{', request.expectedSnapshot().original().bytes()[0]);
        assertFalse(request.expectedSnapshot().binding().activeEvent().known());
    }

    @Test void rawEnvelopeFloatingTokensCannotBecomeIntegerAuthorityInRealCandidateConsumer() throws IOException {
        JsonNode selected = scenario("selected");
        Request request = GiftReadTransportCodec.decodeRequest(bytes(selected.get("request")));
        String validNative = selected.get("private_result").toString();
        assertTrue(validNative.contains("\"failure_flags\":0"));
        for (String token : List.of("0.0", "0e0", "0E+0")) {
            // Keep this as raw UTF-8: parsing/canonicalizing in the test before the producer hides the defect.
            String raw = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + FIXED_ID
                    + "\",\"ok\":true,\"result\":"
                    + validNative.replace("\"failure_flags\":0", "\"failure_flags\":" + token) + "}";
            byte[] forwarded = GiftReadTransportCodec.decodeEnvelope(raw.getBytes(StandardCharsets.UTF_8)).result().value().bytes();
            assertTrue(JSON.readTree(forwarded).get("native").get("failure_flags").isFloatingPointNumber());
            assertTrue(FactionCandidateCodec.evaluatePrivateCandidate(request.expectedSnapshot().original().bytes(),
                    request.root(), forwarded, request.minimumGoldReserveRaw()) instanceof Rejected);
        }
        String rawSnapshot = "{\"type\":\"command_result\",\"result\":{\"native_revision\":1e0}}";
        byte[] snapshot = GiftReadTransportCodec.decodeEnvelope(rawSnapshot.getBytes(StandardCharsets.UTF_8)).result().value().bytes();
        assertThrows(ContractViolationException.class, () -> GiftReadTransportCodec.decodeSnapshot(snapshot));
    }
}
