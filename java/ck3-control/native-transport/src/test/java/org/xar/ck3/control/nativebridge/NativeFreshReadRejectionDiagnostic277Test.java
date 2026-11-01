package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Pure packet fixtures: no pipe, Native process, Game query, file or action authority. */
final class NativeFreshReadRejectionDiagnostic277Test {
    @Test void zeroWriteRejectionRetainsActualProofAndBoundedReason() throws Exception {
        var replay = new Replay((port, request) -> {
            throw new NativePipeEndpoint.TransferFailure("fixture zero write: " + "\uD83D\uDD25".repeat(400),
                    port.outbound, 0, false, null);
        });
        try (var transport = transport(replay)) {
            transport.observe(deadline());
            var result = assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    transport.readFreshFullState(deadline()));
            var rejected = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, result.dispatch());
            assertEquals(1, replay.writeEntries);
            assertEquals(0, replay.packets.size());
            assertTrue(rejected.proof().reason().startsWith("fixture zero write:"));
            assertEquals(replay.id(), rejected.requestId());
            assertTrue(result.reason().contains("rejected before write; request_id=" + replay.id()));
            assertTrue(result.reason().contains("; reason=fixture zero write:"));
            assertBounded(result.reason());
            assertTrue(result.originalFrame().isEmpty());
            assertTrue(result.snapshotReceived().isEmpty());
        }
    }

    @Test void negativeAcknowledgementKeepsOriginalErrorKindsAndPacket() throws Exception {
        for (String field : new String[] {"", ",\"error\":null", ",\"error\":\"fresh_full_state_native_read_unavailable\"",
                ",\"error\":{\"code\":\"read_failed\",\"message\":\"actual failure\"}",
                ",\"error\":\"" + "\uD83D\uDD25".repeat(400) + "\""}) {
            var replay = new Replay((port, request) -> port.add(negative(port.id(), field)));
            try (var transport = transport(replay)) {
                transport.observe(deadline());
                var result = assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                        transport.readFreshFullState(deadline()), field);
                var ack = assertInstanceOf(NativeActionPort.AckReceived.class, result.dispatch());
                assertFalse(ack.nativeOk());
                assertEquals(replay.id(), ack.requestId());
                assertArrayEquals(replay.ackPacket, ack.originalPacket());
                assertEquals(1, replay.writeEntries);
                assertTrue(result.reason().contains("received negative Native ACK; request_id=" + replay.id()));
                String error = field.isEmpty() ? "<absent>" : field.substring(",\"error\":".length());
                assertTrue(result.reason().startsWith("original fresh READ received negative Native ACK; request_id="
                        + replay.id() + "; error="));
                if (error.length() < 300) assertTrue(result.reason().endsWith(error));
                assertBounded(result.reason());
                assertTrue(result.originalFrame().isEmpty());
                assertTrue(result.snapshotReceived().isEmpty());
            }
        }
    }

    @Test void unknownCollectionAndIndependentStateProofRemainStrict() throws Exception {
        var replay = new Replay((port, request) -> {});
        try (var transport = transport(replay)) {
            transport.observe(deadline());
            var first = assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    transport.readFreshFullState(deadline()));
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class, first.dispatch());
            assertSame(unknown, assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    transport.readFreshFullState(deadline())).dispatch());
            assertEquals(1, replay.writeEntries);
            replay.add(negative(replay.id(), ",\"error\":\"late actual refusal\""));
            var collected = assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    transport.collectFreshFullState(unknown.requestId(), deadline()));
            var ack = assertInstanceOf(NativeActionPort.AckReceived.class, collected.dispatch());
            assertFalse(ack.nativeOk());
            assertArrayEquals(replay.ackPacket, ack.originalPacket());
            assertEquals(unknown.requestId(), ack.requestId());
            assertTrue(collected.reason().endsWith("; error=\"late actual refusal\""));
            assertEquals(1, replay.writeEntries);
        }
        var missing = new Replay((port, request) -> port.add(positive(port.id())));
        try (var transport = transport(missing)) {
            transport.observe(deadline());
            var rejected = assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    transport.readFreshFullState(deadline()));
            assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class, rejected.dispatch()).nativeOk());
            assertTrue(rejected.reason().contains("no independently received matching original state packet"));
            assertTrue(rejected.originalFrame().isEmpty());
            assertEquals(1, missing.writeEntries);
        }
        var paired = new Replay((port, request) -> {
            port.add(snapshot("native:6", 6, port.id()));
            port.add(positive(port.id()));
        });
        try (var transport = transport(paired)) {
            transport.observe(deadline());
            var received = assertInstanceOf(NativeFreshSnapshotPort.Received.class,
                    transport.readFreshFullState(deadline()));
            assertTrue(received.acknowledgement().nativeOk());
            assertEquals(paired.id(), received.acknowledgement().requestId());
            assertArrayEquals(paired.ackPacket, received.acknowledgement().originalPacket());
            NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(), received.originalFrame(),
                    received.snapshotReceived());
            assertEquals(1, paired.writeEntries);
        }
    }

    private static void assertBounded(String text) {
        assertTrue(text.length() <= 512);
        for (int i = 0; i < text.length(); i++) {
            char next = text.charAt(i);
            if (Character.isHighSurrogate(next)) {
                assertTrue(i + 1 < text.length() && Character.isLowSurrogate(text.charAt(++i)));
            } else assertFalse(Character.isLowSurrogate(next));
        }
    }
    @FunctionalInterface private interface Producer {
        void write(Replay port, ObjectNode request) throws IOException;
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets = new ArrayDeque<>();
        final Producer producer;
        int writeEntries;
        ObjectNode request;
        byte[] outbound, ackPacket;
        Replay(Producer producer) throws IOException {
            this.producer = producer;
            add(hello());
            add(snapshot("old", 5, null));
        }
        void add(ObjectNode payload) throws IOException {
            byte[] packet = NativeWire.packet(StrictJson.canonical(payload));
            if ("command_result".equals(payload.path("type").textValue())) ackPacket = packet;
            packets.add(packet);
        }
        String id() { return request.get("request_id").textValue(); }
        @Override public void verify() {}
        @Override public void awaitConnection(Instant deadline) {}
        @Override public byte[] readPacket(Instant deadline) throws IOException {
            if (packets.isEmpty()) throw new IOException("fixture has no original ACK");
            return packets.remove();
        }
        @Override public void writePacket(byte[] packet, Instant deadline) throws IOException {
            writeEntries++;
            outbound = packet.clone();
            request = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length)));
            assertEquals(NativeFreshSnapshotPort.STEP, request.path("step").textValue());
            assertEquals(BigInteger.ZERO, request.get("expected_revision").bigIntegerValue());
            producer.write(this, request);
        }
        @Override public void close() {}
    }
    private static final String SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ADAPTER = "ck3-1.19.0.6-msvc-x64";
    private static ObjectNode object(String json) throws IOException {
        return NativeWire.object(NativeWire.parse(json.getBytes(StandardCharsets.UTF_8)));
    }
    private static ObjectNode hello() throws IOException {
        var row = object("{}");
        row.put("type", "hello").put("protocol_version", 1).put("pid", 42).put("connection_generation", 1)
                .put("bridge_version", "source-test").put("expected_ck3_sha256", SHA)
                .put("expected_ck3_version", "1.19.0.6").put("game_adapter_id", ADAPTER)
                .put("game_adapter_status", "ready").put("ck3_build_match", true);
        row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);
        return row;
    }
    private static ObjectNode snapshot(String id, int revision, String request) throws IOException {
        var row = object("""
                {"type":"state_snapshot","protocol_version":1,"state":{"date_raw":53144328,"speed":3,
                "paused":true,"map_ready":true,"played_character":{"character_id":73,"alive":true},
                "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
                "one_life_settlement":null,"played_character_gold":{"raw":0,"scale":100000},
                "played_character_prestige":{"raw":0,"scale":100000},"played_character_piety":{"raw":0,"scale":100000},
                "history":[],"active_wars":[],"player_armies":[],"diagnostics":{}}}
                """);
        row.put("snapshot_id", id).put("revision", revision);
        if (request != null) row.put("read_request_id", request);
        return row;
    }
    private static ObjectNode negative(String id, String errorField) throws IOException {
        return object("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id
                + "\",\"ok\":false" + errorField + "}");
    }
    private static ObjectNode positive(String id) throws IOException {
        var row = object("{}");
        row.put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", true);
        row.putObject("result").put("schema", NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id", id)
                .put("snapshot_id", "native:6").put("revision", 6);
        return row;
    }
    private static NativeGameTransport transport(Replay replay) throws IOException {
        String slash = Character.toString(92);
        var config = new NativePipeEndpoint.Config(slash + slash + "." + slash + "pipe" + slash + "diagnostic277-only",
                "software-only", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)),
                "actual-held-session", "source-test", SHA, ADAPTER);
        return new NativeGameTransport(replay, config, 16, 64);
    }
    private static Instant deadline() { return Instant.now().plusSeconds(20); }
}
