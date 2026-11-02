package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;

/**
 * Software packet provenance: These packets are DATA constructed by a test Replay, not a C++/Game oracle.
 * This test verifies the transport's passive observation deadline calculation logic (readTimeout vs caller deadline)
 * using the actual public observe API and the NativeGameTransport constructor that accepts a Clock and Duration.
 */
final class NativePassiveObservationBudget309Test {
    private static final String SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String ADAPTER = "ck3-1.19.0.6-msvc-x64";
    private static final String STATE = """
        {"date_raw":53144328,"speed":3,"paused":true,"map_ready":true,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,"one_life_settlement":null,
        "played_character_gold":{"raw":0,"scale":100000},"played_character_prestige":{"raw":0,"scale":100000},"played_character_piety":{"raw":0,"scale":100000},"history":[],
        "active_wars":[],"player_armies":[],"diagnostics":{}}
        """;

    @Test void passiveObservationBudgetsAndCache() throws Exception {
        // Explicit input recipes: cap 60, smaller cap 10, shorter caller 20, legacy caller 600.
        passiveCase(Duration.ofSeconds(60), Duration.ofSeconds(600), Duration.ofSeconds(60), true);
        passiveCase(Duration.ofSeconds(10), Duration.ofSeconds(600), Duration.ofSeconds(10), false);
        passiveCase(Duration.ofSeconds(60), Duration.ofSeconds(20), Duration.ofSeconds(20), false);
        passiveCase(null, Duration.ofSeconds(600), Duration.ofSeconds(600), false);

        var clock = new MutableClock(Instant.now());
        var port = new Replay(clock);
        try (var actual = new NativeGameTransport(port, config(), 16, 64, List.of(), clock, Duration.ofSeconds(60))) {
            var nullFailure = Assertions.assertThrows(UncheckedIOException.class, () -> actual.observe(null));
            Assertions.assertInstanceOf(IOException.class, nullFailure.getCause());
            var expiredFailure = Assertions.assertThrows(UncheckedIOException.class,
                () -> actual.observe(Instant.now().minusSeconds(1)));
            Assertions.assertInstanceOf(IOException.class, expiredFailure.getCause());
            Assertions.assertTrue(port.awaitDeadlines.isEmpty());
            Assertions.assertTrue(port.readDeadlines.isEmpty());
            Assertions.assertEquals(0, port.writes);
            Assertions.assertEquals(0, clock.steps);
        }

        var closedPort = new Replay(new MutableClock(Instant.now()));
        var closed = new NativeGameTransport(closedPort, config(), 16, 64, List.of(),
            closedPort.clock, Duration.ofSeconds(60));
        closed.close();
        var closedFailure = Assertions.assertThrows(UncheckedIOException.class,
            () -> closed.observe(Instant.now().plusSeconds(600)));
        Assertions.assertInstanceOf(IOException.class, closedFailure.getCause());
        Assertions.assertTrue(closedPort.awaitDeadlines.isEmpty());
        Assertions.assertTrue(closedPort.readDeadlines.isEmpty());
        Assertions.assertEquals(0, closedPort.writes);
        Assertions.assertEquals(0, closedPort.clock.steps);
    }

    private static void passiveCase(Duration configured, Duration callerOffset,
            Duration expectedOffset, boolean checkCache) throws Exception {
        Instant start = Instant.now();
        var clock = new MutableClock(start);
        var port = new Replay(clock);
        port.add(hello());
        port.add(heartbeat());
        port.add(snapshot("native:6", 6));
        Instant caller = start.plus(callerOffset);
        Instant expected = start.plus(expectedOffset);
        NativeGameTransport transport = configured == null
            ? new NativeGameTransport(port, config(), 16, 64, List.of(), clock)
            : new NativeGameTransport(port, config(), 16, 64, List.of(), clock, configured);
        try (transport) {
            var result = transport.observe(caller);
            Assertions.assertEquals("native:6", result.snapshotId());
            Assertions.assertEquals(BigInteger.valueOf(6), result.nativeRevision());
            Assertions.assertEquals(List.of(expected), port.awaitDeadlines);
            Assertions.assertEquals(List.of(expected, expected, expected), port.readDeadlines);
            Assertions.assertEquals(List.of(start, start.plusSeconds(1), start.plusSeconds(2)), port.readInstants);
            Assertions.assertEquals(3, clock.steps);
            Assertions.assertEquals(start.plusSeconds(3), clock.instant());
            Assertions.assertEquals(0, port.writes);
            Assertions.assertTrue(port.packets.isEmpty());

            if (checkCache) {
                // A new cached invocation has its own cap, with no additional packet read.
                Instant cachedExpected = start.plusSeconds(63);
                Assertions.assertSame(result, transport.observe(caller, Duration.ofMinutes(1)));
                Assertions.assertEquals(List.of(expected, cachedExpected), port.awaitDeadlines);
                Assertions.assertEquals(List.of(expected, expected, expected), port.readDeadlines);
                Assertions.assertEquals(3, clock.steps);
                Assertions.assertEquals(0, port.writes);

                var awaitsBeforeNull = List.copyOf(port.awaitDeadlines);
                var readsBeforeNull = List.copyOf(port.readDeadlines);
                var nullCached = Assertions.assertThrows(UncheckedIOException.class,
                    () -> transport.observe(null, Duration.ofMinutes(1)));
                Assertions.assertInstanceOf(IOException.class, nullCached.getCause());
                Assertions.assertEquals(awaitsBeforeNull, port.awaitDeadlines);
                Assertions.assertEquals(readsBeforeNull, port.readDeadlines);
                Assertions.assertEquals(3, clock.steps);
                Assertions.assertEquals(0, port.writes);
            }
        }
    }

    private static NativePipeEndpoint.Config config() {
        String slash = Character.toString(92);
        return new NativePipeEndpoint.Config(
            slash + slash + "." + slash + "pipe" + slash + "passive-observation-test",
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
        row.putArray("capabilities").add("game.state.snapshot");
        return row;
    }

    private static ObjectNode heartbeat() throws IOException {
        var row = object("{}");
        row.put("type", "heartbeat").put("protocol_version", 1).put("sequence", 1);
        return row;
    }

    private static ObjectNode snapshot(String id, int revision) throws IOException {
        var row = object("{}");
        row.put("type", "state_snapshot").put("protocol_version", 1).put("snapshot_id", id).put("revision", revision)
            .set("state", NativeWire.parse(STATE.getBytes(StandardCharsets.UTF_8)));
        return row;
    }

    private static ObjectNode object(String json) throws IOException {
        return NativeWire.object(NativeWire.parse(json.getBytes(StandardCharsets.UTF_8)));
    }

    private static final class MutableClock extends Clock {
        private Instant current;
        private int steps;
        MutableClock(Instant start) { current = Objects.requireNonNull(start); }
        @Override public Instant instant() { return current; }
        @Override public ZoneOffset getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(java.time.ZoneId zone) {
            if (!ZoneOffset.UTC.equals(Objects.requireNonNull(zone)))
                throw new IllegalArgumentException("controlled UTC clock only");
            return this;
        }
        void advancePacket() { current = current.plusSeconds(1); steps++; }
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets = new ArrayDeque<>();
        int writes;
        final MutableClock clock;
        final List<Instant> readInstants = new ArrayList<>();
        Replay(MutableClock clock) { this.clock = Objects.requireNonNull(clock); }
        final List<Instant> awaitDeadlines = new ArrayList<>();
        final List<Instant> readDeadlines = new ArrayList<>();

        @Override public void verify() {}
        @Override public void awaitConnection(Instant deadline) throws IOException {
            awaitDeadlines.add(deadline);
        }

        @Override public byte[] readPacket(Instant deadline) throws IOException {
            readDeadlines.add(Objects.requireNonNull(deadline));
            if (packets.isEmpty()) throw new IOException("software original read deadline/error");
            readInstants.add(clock.instant());
            clock.advancePacket();
            byte[] packet = packets.remove();
            return packet;
        }

        @Override public void writePacket(byte[] packet, Instant deadline) throws IOException {
            writes++;
            throw new IOException("passive observation must not write");
        }

        @Override public void close() {}

        void add(ObjectNode row) throws IOException {
            byte[] packet = NativeWire.packet(StrictJson.canonical(row));
            packets.add(packet);
        }
    }
}