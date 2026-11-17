package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFrame;

/** Pinned C++ result tokens through the actual software receiver; no live process, full frame or action authority. */
final class NativePersonalGoldFrame1210ProducerTest {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_1210;
    private static final String ADAPTER = "ck3-1.21.0-msvc-x64", BRIDGE = "software-personal-gold1210";
    private static final GameGeneration GAME = new GameGeneration(42,
            new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private record Input(String name, int bytes, String sha256) { }
    private record CppOriginal(byte[] envelope, byte[] resultToken) { }
    private static final Input NORMAL = new Input("personal-gold-producer-partial01.json", 1233,
            "06fcc7b418e46dff6a27ab72533ca7b8444077d33ccc7aaeadd07cfbc93d208f");
    private static final Input MINIMUM = new Input("personal-gold-producer-minimum01.json", 1245,
            "a7eb0f993a1093a10951145a9e7d2404be90ccfb9b26ecb8bb1a85cf7d54da87");
    private static final Input UNAVAILABLE = new Input("personal-gold-producer-unavailable01.json", 1262,
            "a8d48e467883f294799909a81951e77fee43797113e9c2fd1a65f0b4c12fe942");

    @Test
    void originalCppPartialAndSignedMinimumReachThePrivateReceiverWithActualCustody() throws Exception {
        for (var input : List.of(NORMAL, MINIMUM)) {
            var producer = original(input);
            try (var fixture = new Fixture(producer, hello())) {
                var received = fixture.received();
                var frame = assertInstanceOf(PersonalGoldFrame.Partial.class, received.frame());
                assertEquals(BUILD, frame.build());
                assertEquals(input == NORMAL ? 12345000L : Long.MIN_VALUE, frame.personalGold().raw());
                assertEquals(100000, frame.personalGold().scale());
                assertTrue(frame.applicationMainObserved());
                var prefix = frame.coreFrame().prefix();
                assertEquals(123456, prefix.dateRaw()); assertEquals(5, prefix.speed());
                assertEquals(7, prefix.localPlayerId()); assertEquals(16777217, prefix.playedCharacterId());
                assertTrue(prefix.paused() && prefix.mapReady() && prefix.hasPlayedCharacter() && prefix.playedCharacterAlive());
                original(received, fixture, producer.resultToken());
                var data = NativeWire.object(NativeWire.parse(received.original().originalResultToken().orElseThrow().bytes()));
                assertFalse(data.get("complete_snapshot").booleanValue());
                assertFalse(data.get("treasury_observed").booleanValue());
                assertFalse(data.get("monthly_flow_observed").booleanValue());
            }
        }
    }

    @Test
    void originalCppUnavailableKeepsItsPositiveAckNullAmountAndOriginalNestedCore() throws Exception {
        var producer = original(UNAVAILABLE);
        try (var fixture = new Fixture(producer, hello())) {
            var received = fixture.received();
            var frame = assertInstanceOf(PersonalGoldFrame.Unavailable.class, received.frame());
            assertEquals(BUILD, frame.build()); assertFalse(frame.applicationMainObserved());
            assertEquals("personal_gold_not_read", frame.reason());
            assertInstanceOf(CoreFrame.Unavailable.class, frame.coreFrame());
            var data = NativeWire.object(NativeWire.parse(received.original().originalResultToken().orElseThrow().bytes()));
            assertTrue(data.get("personal_gold").isNull());
            assertFalse(data.get("personal_gold_available").booleanValue());
            original(received, fixture, producer.resultToken());
        }
    }

    @Test
    void missingCapabilityOldBuildAndForeignHelloRefuseBeforeAnyQueryWrite() throws Exception {
        var producer = original(NORMAL);
        for (String changed : List.of("capability", "old-build", "pid", "version", "hash", "adapter")) {
            var advertised = hello();
            switch (changed) {
                case "capability" -> advertised.putArray("capabilities");
                case "old-build" -> {
                    advertised.put("expected_ck3_version", ExactCk3Build.CK3_12004.version());
                    advertised.put("expected_ck3_sha256", ExactCk3Build.CK3_12004.executableSha256());
                    advertised.put("game_adapter_id", "ck3-1.20.0.4-msvc-x64");
                }
                case "pid" -> advertised.put("pid", GAME.pid() + 1);
                case "version" -> advertised.put("expected_ck3_version", "1.21.0.0");
                case "hash" -> advertised.put("expected_ck3_sha256", ExactCk3Build.CK3_12004.executableSha256());
                case "adapter" -> advertised.put("game_adapter_id", "ck3-1.20.0.4-msvc-x64");
                default -> throw new AssertionError(changed);
            }
            try (var fixture = new Fixture(producer, advertised)) {
                var unavailable = assertInstanceOf(NativeGameTransport.PersonalGoldReadUnavailable.class,
                        fixture.actual.readPersonalGoldFrameReceived(fixture.deadline), changed);
                var rejected = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, unavailable.original(), changed);
                assertEquals(0, rejected.proof().requestBytesWritten());
                assertFalse(unavailable.reason().isBlank());
                assertEquals(0, fixture.source.writes, changed);
                assertEquals(0, fixture.source.fullStateWrites);
            }
        }
    }

    @Test
    void badTupleAndBroaderClaimsKeepTheirOriginalPositiveAckAndNeverBecomeZeroDispatch() throws Exception {
        var producer = original(NORMAL);
        for (String changed : List.of("version", "hash", "backend", "full", "nested-full", "treasury", "monthly")) {
            var data = NativeWire.object(NativeWire.parse(producer.resultToken())).deepCopy();
            switch (changed) {
                case "version" -> data.put("game_version", ExactCk3Build.CK3_12004.version());
                case "hash" -> data.put("executable_sha256", ExactCk3Build.CK3_12004.executableSha256());
                case "backend" -> data.put("backend", "ck3-1.20.0.4-native-headless-main-thread");
                case "full" -> data.put("complete_snapshot", true);
                case "nested-full" -> ((ObjectNode) data.get("core_frame")).put("complete_snapshot", true);
                case "treasury" -> data.put("treasury_observed", true);
                case "monthly" -> data.put("monthly_flow_observed", true);
                default -> throw new AssertionError(changed);
            }
            // Explicit negative public DATA; the pinned C++ original is retained rather than edited.
            byte[] invalid = StrictJson.canonical(data);
            try (var fixture = new Fixture(producer, hello(), invalid)) {
                var unavailable = assertInstanceOf(NativeGameTransport.PersonalGoldReadUnavailable.class,
                        fixture.actual.readPersonalGoldFrameReceived(fixture.deadline), changed);
                var ack = assertInstanceOf(NativeActionPort.AckReceived.class, unavailable.original(), changed);
                assertTrue(ack.nativeOk()); assertFalse(unavailable.reason().isBlank());
                assertArrayEquals(invalid, ack.originalResultToken().orElseThrow().bytes());
                assertArrayEquals(fixture.source.response, ack.originalPacket());
                assertArrayEquals(fixture.source.request, ack.outbound().orElseThrow().originalPacket());
                ack.custody().orElseThrow().verify(ack);
                counts(fixture, 1);
                assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
            }
        }
    }

    @Test
    void sameSessionForeignIssuerExtendedDeadlineAndExpiredReceiptCannotBorrowReadCustody() throws Exception {
        var producer = original(NORMAL);
        try (var owner = new Fixture(producer, hello()); var foreign = new Fixture(producer, hello())) {
            var received = owner.received();
            assertEquals(owner.actual.awaitHello(received.validUntil()), foreign.actual.awaitHello(received.validUntil()));
            received.requireOriginal(owner.actual, received.validUntil());
            assertThrows(IOException.class, () -> received.requireOriginal(foreign.actual, received.validUntil()));
            assertThrows(IOException.class, () -> received.requireOriginal(owner.actual, received.validUntil().plusNanos(1)));
            counts(owner, 1); counts(foreign, 0);
            owner.clock.set(received.validUntil());
            assertThrows(IOException.class, () -> received.requireOriginal(owner.actual, received.validUntil()));
            counts(owner, 1); counts(foreign, 0);
        }
    }

    @Test
    void personalGoldAndItsNestedCoreDataNeverBecomeACoreControlReceiptOrFullSnapshot() throws Exception {
        var producer = original(NORMAL);
        try (var fixture = new Fixture(producer, hello())) {
            var received = fixture.received();
            Object resourceRole = received;
            assertFalse(resourceRole instanceof NativeGameTransport.CoreRead);
            assertFalse(resourceRole instanceof NativeGameTransport.CoreReceived);
            assertInstanceOf(CoreFrame.Partial.class, received.frame().coreFrame());
            // The real original outbound is the resource query. A nested public Core cannot change that custody.
            assertThrows(IOException.class, () -> CoreFramePublicCodec.decodeOutcome(received.original()));
            assertEquals(PersonalGoldFrame.STEP,
                    NativeWire.decodeExecuteRequest(received.original().outbound().orElseThrow().originalPacket()).step());
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
            original(received, fixture, producer.resultToken());
        }
    }

    private static void original(NativeGameTransport.PersonalGoldReceived received, Fixture fixture, byte[] cppToken)
            throws Exception {
        var ack = received.original();
        assertTrue(ack.nativeOk()); assertEquals(fixture.source.requestId, ack.requestId());
        assertArrayEquals(cppToken, ack.originalResultToken().orElseThrow().bytes());
        assertArrayEquals(fixture.source.response, ack.originalPacket());
        assertArrayEquals(fixture.source.request, ack.outbound().orElseThrow().originalPacket());
        var custody = ack.custody().orElseThrow(); custody.verify(ack);
        assertEquals(fixture.actual.awaitHello(received.validUntil()), custody.session());
        assertTrue(custody.writeEntered().order().compareTo(custody.writeCompleted().order()) < 0);
        assertTrue(custody.writeCompleted().order().compareTo(custody.responseReceived().order()) < 0);
        assertFalse(custody.responseReceived().observedAt().isAfter(received.validUntil()));
        received.requireOriginal(fixture.actual, received.validUntil());
        assertEquals(fixture.deadline, received.validUntil());
        assertEquals(1, fixture.source.helloReads);
        counts(fixture, 1);
        assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
    }

    private static void counts(Fixture fixture, int writes) {
        assertEquals(writes, fixture.source.writes);
        assertEquals(0, fixture.source.fullStateWrites);
        assertEquals(0, fixture.source.controlWrites);
    }

    private static CppOriginal original(Input input) throws Exception {
        String directory = System.getProperty("xar.native.personalGold1210.fixtures");
        byte[] body;
        if (directory == null || directory.isBlank()) {
            try (var stream = NativePersonalGoldFrame1210ProducerTest.class.getResourceAsStream(
                    "/newnative/personal-gold1210/" + input.name())) {
                if (stream == null) throw new IOException("exact C++ personal-gold resource missing: " + input.name());
                body = stream.readNBytes(input.bytes() + 1);
            }
        } else {
            var root = Path.of(directory);
            if (!root.isAbsolute()) throw new IOException("absolute actual personal-gold fixture directory required");
            try (var stream = Files.newInputStream(root.resolve(input.name()))) { body = stream.readNBytes(input.bytes() + 1); }
        }
        assertEquals(input.bytes(), body.length);
        assertEquals(input.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));
        var packet = NativeWire.packet(body);
        assertArrayEquals(body, Arrays.copyOfRange(packet, 4, packet.length));
        var nativeResult = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(packet));
        assertTrue(nativeResult.nativeOk());
        return new CppOriginal(body, nativeResult.result().token().orElseThrow().value());
    }

    private static NativePipeEndpoint.Config config() {
        return new NativePipeEndpoint.Config("\\\\.\\pipe\\personal-gold1210-software", "personal-gold1210-software",
                GAME, "personal-gold1210-session", BRIDGE, BUILD.executableSha256(), ADAPTER);
    }

    private static ObjectNode hello() {
        var row = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", GAME.pid())
                .put("connection_generation", 1).put("bridge_version", BRIDGE)
                .put("expected_ck3_version", BUILD.version()).put("expected_ck3_sha256", BUILD.executableSha256())
                .put("game_adapter_id", ADAPTER).put("game_adapter_status", "ready").put("ck3_build_match", true);
        row.putArray("capabilities").add(PersonalGoldFrame.CAPABILITY);
        return row;
    }

    private static final class Fixture implements AutoCloseable {
        final MutableClock clock = new MutableClock(Instant.now());
        final Replay source;
        final NativeGameTransport actual;
        final Instant deadline = clock.instant().plusSeconds(120);
        Fixture(CppOriginal producer, ObjectNode hello) throws IOException { this(producer, hello, producer.resultToken()); }
        Fixture(CppOriginal producer, ObjectNode hello, byte[] result) throws IOException {
            source = new Replay(producer.envelope(), result, hello, clock);
            actual = new NativeGameTransport(source, config(), 16, 8, List.of(), clock);
        }
        NativeGameTransport.PersonalGoldReceived received() throws InterruptedException {
            return assertInstanceOf(NativeGameTransport.PersonalGoldReceived.class,
                    actual.readPersonalGoldFrameReceived(deadline));
        }
        @Override public void close() throws IOException { actual.close(); }
    }

    private static final class MutableClock extends Clock {
        private Instant now;
        MutableClock(Instant now) { this.now = now; }
        void set(Instant next) { assertFalse(next.isBefore(now)); now = next; }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) {
            if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException("UTC software replay only");
            return this;
        }
        @Override public Instant instant() { return now; }
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets = new ArrayDeque<>();
        final byte[] originalCppEnvelope, result;
        final MutableClock clock;
        int writes, helloReads, fullStateWrites, controlWrites;
        boolean closed;
        String requestId;
        byte[] request, response;
        Replay(byte[] cppEnvelope, byte[] result, ObjectNode hello, MutableClock clock) throws IOException {
            originalCppEnvelope = cppEnvelope.clone(); this.result = result.clone(); this.clock = clock;
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify() throws IOException { if (closed) throw new IOException("software source closed"); }
        @Override public void awaitConnection(Instant until) throws IOException { check(until); }
        private void check(Instant until) throws IOException {
            verify(); if (!clock.instant().isBefore(until)) throw new IOException("software operation deadline expired");
        }
        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);
            if (packets.isEmpty()) throw new IOException("software source has no unsolicited packet or full snapshot");
            byte[] packet = packets.removeFirst();
            if (NativeWire.decode(packet) instanceof NativeWire.Hello) helloReads++;
            return packet;
        }
        @Override public void writePacket(byte[] original, Instant until) throws IOException {
            check(until); var decoded = NativeWire.decodeExecuteRequest(original); writes++;
            if (decoded.step().equals(NativeFreshSnapshotPort.STEP)) fullStateWrites++;
            if (!decoded.step().equals(PersonalGoldFrame.STEP)) controlWrites++;
            assertEquals(PersonalGoldFrame.STEP, decoded.step());
            assertEquals(Optional.of(BigInteger.ZERO), decoded.expectedRevision());
            assertTrue(decoded.expectedSnapshotRevision().isEmpty());
            assertEquals(0, NativeWire.object(NativeWire.parse(decoded.normalizedAdditionalFields().value())).size());
            requestId = decoded.requestId(); request = original.clone();
            // Only the software correlation ID is new. The pinned C++ result token is copied byte for byte.
            // This response is never represented as the original fixed-ID C++ command_result envelope.
            var output = new ByteArrayOutputStream();
            output.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + requestId + "\",\"ok\":true,\"result\":").getBytes(StandardCharsets.UTF_8));
            output.writeBytes(result); output.write('}'); response = NativeWire.packet(output.toByteArray());
            packets.add(response.clone());
        }
        @Override public void close() { closed = true; }
    }
}
