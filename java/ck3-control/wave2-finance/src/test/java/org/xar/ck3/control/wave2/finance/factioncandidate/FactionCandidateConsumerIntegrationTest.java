package org.xar.ck3.control.wave2.finance.factioncandidate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransportCodec;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.*;

/** Synthetic existing-owner endpoint; no pipe, Game, receipt or pending writer is constructed. */
final class FactionCandidateConsumerIntegrationTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String READ_ID = "faction-gift-read-00000000000000000000000000000001";

    @Test
    void actualRootAndCandidateConsumersUseOneOwnedReadAndSharedJavaGiftLeaf() throws IOException {
        JsonNode rootInput = vector("latest-root-targeting-present").path("input");
        RootView root = latestSameFrameRoot(FactionCandidateCodec.decodeRootSearch(JSON.writeValueAsBytes(rootInput)));
        assertEquals(RootStatus.TARGETING_PRESENT, root.status());
        JsonNode candidateVector = vector("private-native-selected");
        JsonNode candidateInput = candidateVector.path("input");
        GiftReadTransport.Snapshot snapshot = GiftReadTransportCodec.decodeSnapshot(JSON.writeValueAsBytes(candidateInput.path("snapshot")));
        OwnedFixturePort port = new OwnedFixturePort(snapshot, snapshot, candidateInput.path("private_result"));
        GiftReadTransport.Request request = new GiftReadTransport.Request(snapshot, root.root().orElseThrow(),
                candidateInput.path("minimum_gold_reserve_raw").bigIntegerValue(),
                new GiftReadTransport.Timeout(new BigDecimal("30.0")));
        GiftReadTransport.Result result = GiftReadTransport.query(request, port, () -> READ_ID);
        JsonNode actual = JSON.readTree(GiftReadTransportCodec.encodeResult(result));
        assertEquals(candidateVector.path("expected"), actual);
        assertEquals(2, port.snapshotReads);
        assertEquals(1, port.commands.size());
        assertEquals(1, port.resultWaits);
        JsonNode command = JSON.readTree(GiftReadTransportCodec.encodeCommand(port.commands.get(0)));
        assertEquals(PRIVATE_STEP, command.path("step").textValue());
        assertEquals(412, command.path("expected_revision").intValue());
        assertFalse(actual.path("gift_submission_enabled").booleanValue());
        assertFalse(actual.path("public_capability_advertised").booleanValue());
    }

    @Test
    void crossedFrameDoesNotBecomeCandidateAndDoesNotReplayOwnedRead() throws IOException {
        JsonNode input = vector("private-native-selected").path("input");
        GiftReadTransport.Snapshot before = GiftReadTransportCodec.decodeSnapshot(JSON.writeValueAsBytes(input.path("snapshot")));
        ObjectNode changed = (ObjectNode) input.path("snapshot").deepCopy();
        changed.put("native_revision", 413);
        GiftReadTransport.Snapshot after = GiftReadTransportCodec.decodeSnapshot(JSON.writeValueAsBytes(changed));
        RootProjection root = FactionCandidateCodec.decodeRootProjection(JSON.writeValueAsBytes(input.path("root")));
        OwnedFixturePort port = new OwnedFixturePort(before, after, input.path("private_result"));
        GiftReadTransport.Request request = new GiftReadTransport.Request(before, root, BigInteger.valueOf(10_000_000),
                new GiftReadTransport.Timeout(BigDecimal.valueOf(30)));
        GiftReadTransport.ReadFailure failure = assertThrows(GiftReadTransport.ReadFailure.class,
                () -> GiftReadTransport.query(request, port, () -> READ_ID));
        assertEquals(GiftReadTransport.Failure.FRAME_CROSSED, failure.failure());
        assertEquals(1, port.commands.size());
        assertEquals(1, port.resultWaits);
    }

    private static final class OwnedFixturePort implements GiftReadTransport.ExistingOwnedReadPort {
        private final GiftReadTransport.Snapshot before;
        private final GiftReadTransport.Snapshot after;
        private final JsonNode result;
        private final List<GiftReadTransport.Command> commands = new ArrayList<>();
        private int snapshotReads;
        private int resultWaits;

        OwnedFixturePort(GiftReadTransport.Snapshot before, GiftReadTransport.Snapshot after, JsonNode result) {
            this.before = before;
            this.after = after;
            this.result = result;
        }
        @Override public GiftReadTransport.Snapshot takeInternalSemanticSnapshot() {
            snapshotReads++;
            return snapshotReads == 1 ? before : after;
        }
        @Override public GiftReadTransport.Diagnostics diagnostics() {
            return GiftReadTransportCodec.decodeDiagnostics(("{\"last_heartbeat\":{"
                    + "\"g2_faction_gift_mitigation_async_glue_v1\":{\"private_build\":true}}}")
                    .getBytes(StandardCharsets.UTF_8));
        }
        @Override public void send(GiftReadTransport.Command command) {
            assertEquals(0, commands.size(), "there is one read and no retry path");
            commands.add(command);
        }
        @Override public GiftReadTransport.WaitResult waitForCommandResult(GiftReadTransport.ReadId id, GiftReadTransport.Timeout timeout) {
            resultWaits++;
            assertEquals(READ_ID, id.value());
            ObjectNode envelope = JSON.createObjectNode();
            envelope.put("type", "command_result");
            envelope.put("protocol_version", 1);
            envelope.put("request_id", id.value());
            envelope.put("ok", true);
            envelope.set("result", result);
            try {
                return new GiftReadTransport.Received(GiftReadTransportCodec.decodeEnvelope(JSON.writeValueAsBytes(envelope)));
            } catch (IOException failure) { throw new IllegalStateException(failure); }
        }
    }

    private static JsonNode vector(String name) throws IOException {
        try (InputStream input = FactionCandidateConsumerIntegrationTest.class.getResourceAsStream("/factioncandidate/python-golden-v1.json")) {
            assertNotNull(input, "mandatory original producer golden");
            JsonNode root = JSON.readTree(input);
            for (JsonNode candidate : root.path("cases")) if (candidate.path("name").textValue().equals(name)) return candidate;
            throw new IllegalArgumentException("missing original producer vector " + name);
        }
    }
}
