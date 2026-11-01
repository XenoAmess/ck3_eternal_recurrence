package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Software packet provenance: These packets are DATA constructed by a test Replay, not a C++/Game oracle.
 * This test verifies the transport's deadline calculation logic (readTimeout vs caller deadline) using
 * the actual public readFreshFullState API and the NativeGameTransport constructor that accepts a Clock.
 */
final class NativeFreshReadDeadline219Test {
    private static final String SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ADAPTER = "ck3-1.19.0.6-msvc-x64";
    private static final String STATE = """
        {"date_raw":53144328,"speed":3,"paused":true,"map_ready":true,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,"one_life_settlement":null,
        "played_character_gold":{"raw":0,"scale":100000},"played_character_prestige":{"raw":0,"scale":100000},"played_character_piety":{"raw":0,"scale":100000},"history":[],
        "active_wars":[],"player_armies":[],"diagnostics":{}}
        """;

    @Test void configuredReadTimeoutCapsCallerDeadlineForFreshRead() throws Exception {
        Instant now = Instant.now();
        Clock fixedClock = Clock.fixed(now, java.time.ZoneOffset.UTC);
        Duration readTimeout = Duration.ofSeconds(60);
        Instant callerDeadline = now.plus(Duration.ofMinutes(10));

        Replay replay = new Replay();
        replay.add(hello());
        replay.add(snapshot("old", 5, null));

        // Configure the transport with the fixed clock and read timeout
        try (var actual = new NativeGameTransport(replay, config(), 16, 64, java.util.List.of(), fixedClock, readTimeout)) {

        // 1. Consume initial snapshot to set state
        actual.observe(callerDeadline);

        // 2. Perform fresh read. The transport should use min(callerDeadline, now + readTimeout) for the endpoint.
        // Since now + 60s < now + 10m, the endpoint deadline should be now + 60s.
        var result = actual.readFreshFullState(callerDeadline);
        assertInstanceOf(NativeFreshSnapshotPort.Received.class, result);

        // Verify the endpoint received the capped deadline
        assertEquals(now.plus(readTimeout), replay.lastWriteDeadline);
        assertEquals(List.of(now.plus(readTimeout), now.plus(readTimeout)), replay.responseReadDeadlines);
        assertEquals(1, replay.writes);
        }
    }

    @Test void callerDeadlineShorterThanReadTimeoutIsRespected() throws Exception {
        Instant now = Instant.now();
        Clock fixedClock = Clock.fixed(now, java.time.ZoneOffset.UTC);
        Duration readTimeout = Duration.ofSeconds(60);
        Instant callerDeadline = now.plus(Duration.ofSeconds(20));

        Replay replay = new Replay();
        replay.add(hello());
        replay.add(snapshot("old", 5, null));

        try (var actual = new NativeGameTransport(replay, config(), 16, 64, java.util.List.of(), fixedClock, readTimeout)) {

        actual.observe(callerDeadline);

        // Perform fresh read. The transport should use min(callerDeadline, now + readTimeout).
        // Since now + 20s < now + 60s, the endpoint deadline should be now + 20s.
        var result = actual.readFreshFullState(callerDeadline);
        assertInstanceOf(NativeFreshSnapshotPort.Received.class, result);

        // Verify the endpoint received the caller deadline (not extended by readTimeout)
        assertEquals(callerDeadline, replay.lastWriteDeadline);
        assertEquals(List.of(callerDeadline, callerDeadline), replay.responseReadDeadlines);
        assertEquals(1, replay.writes);
        }
    }

    private static NativePipeEndpoint.Config config() {
        String slash = Character.toString(92);
        return new NativePipeEndpoint.Config(
            slash + slash + "." + slash + "pipe" + slash + "fresh-full-state-source-test",
            "source-test-machine",
            new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)),
            "actual-held-session",
            "source-test",
            SHA,
            ADAPTER
        );
    }

    private static ObjectNode hello() throws IOException {
        var row = object("{}");
        row.put("type", "hello").put("protocol_version", 1).put("pid", 42).put("connection_generation", 1)
            .put("bridge_version", "source-test").put("expected_ck3_sha256", SHA).put("expected_ck3_version", "1.19.0.6")
            .put("game_adapter_id", ADAPTER).put("game_adapter_status", "ready").put("ck3_build_match", true);
        row.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);
        return row;
    }

    private static ObjectNode snapshot(String id, int revision, String requestId) throws IOException {
        var row = object("{}");
        row.put("type", "state_snapshot").put("protocol_version", 1).put("snapshot_id", id).put("revision", revision)
            .set("state", NativeWire.parse(STATE.getBytes(StandardCharsets.UTF_8)));
        if (requestId != null) row.put("read_request_id", requestId);
        return row;
    }

    private static ObjectNode ack(String id, boolean ok) throws IOException {
        var row = object("{}");
        row.put("type", "command_result").put("protocol_version", 1).put("request_id", id).put("ok", ok);
        if (ok) row.putObject("result").put("schema", NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id", id).put("snapshot_id", "native:6").put("revision", 6);
        else row.put("error", "actual explicit native refusal");
        return row;
    }

    private static ObjectNode object(String json) throws IOException {
        return NativeWire.object(NativeWire.parse(json.getBytes(StandardCharsets.UTF_8)));
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets = new ArrayDeque<>();
        int reads, writes;
        Instant lastWriteDeadline;
        final List<Instant> responseReadDeadlines = new ArrayList<>();

        @Override public void verify() {}
        @Override public void awaitConnection(Instant deadline) {}

        @Override public byte[] readPacket(Instant deadline) throws IOException {
            reads++;
            if (writes > 0) responseReadDeadlines.add(deadline);
            if (packets.isEmpty()) throw new IOException("software original read deadline/error");
            byte[] packet = packets.remove();
            return packet;
        }

        @Override public void writePacket(byte[] packet, Instant deadline) throws IOException {
            writes++;
            lastWriteDeadline = deadline;
            var request = NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(packet, 4, packet.length)));
            var keys = new HashSet<String>();
            for (var field : request.properties()) keys.add(field.getKey());
            if (!keys.equals(Set.of("type", "protocol_version", "request_id", "step", "expected_revision")))
                throw new IOException("unexpected request fields");
            if (!"execute_step".equals(request.get("type").textValue()))
                throw new IOException("unexpected request type");
            if (!NativeFreshSnapshotPort.STEP.equals(request.get("step").textValue()))
                throw new IOException("unexpected request step");
            if (!BigInteger.ZERO.equals(request.get("expected_revision").bigIntegerValue()))
                throw new IOException("unexpected request revision");

            // Simulate the producer responding to the fresh read request
            String id = request.get("request_id").textValue();
            add(snapshot("native:6", 6, id));
            add(ack(id, true));
        }

        @Override public void close() {}

        void add(ObjectNode row) throws IOException {
            byte[] packet = NativeWire.packet(StrictJson.canonical(row));
            packets.add(packet);
        }
    }
}