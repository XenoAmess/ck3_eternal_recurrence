package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
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
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Software packet boundary tests. A submitted ACK proves neither an engine effect nor a completed SAVE. */
final class NativeCoreClockControlPortTest {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_1210;
    private static final String ADAPTER = "ck3-1.21.0-msvc-x64", BRIDGE = "software-core-control1210";
    private static final GameGeneration GAME = new GameGeneration(42,
            new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final byte[] SUBMITTED = "{\"submitted\":true}".getBytes(StandardCharsets.UTF_8);
    private static final Set<String> CONTROL_FIELDS = Set.of("schema", "game_version", "executable_sha256",
            "adapter_id", "backend", "date_raw", "speed", "paused", "local_player_id", "map_ready",
            "has_played_character", "played_character_id", "played_character_alive");

    @Test
    void eachFixedControlUsesThePrivateReceiptExactWireAndEarlierDeadlineWithoutAFullSnapshot() throws Exception {
        for (var step : CoreClockControl.Step.values()) {
            try (var fixture = new Fixture(partial(), true, false)) {
                var before = fixture.received();
                var until = before.validUntil().minusSeconds(5);
                var ack = assertInstanceOf(NativeActionPort.AckReceived.class,
                        fixture.actual.submitCoreClockControl(before, step, until));
                assertTrue(ack.nativeOk());
                assertArrayEquals(SUBMITTED, ack.originalResultToken().orElseThrow().bytes());
                ack.custody().orElseThrow().verify(ack);
                assertEquals(1, fixture.source.controls.size());
                byte[] packet = fixture.source.controls.getFirst();
                assertArrayEquals(packet, ack.outbound().orElseThrow().originalPacket());
                var command = NativeWire.decodeExecuteRequest(packet);
                assertEquals(ack.requestId(), command.requestId());
                assertEquals(step.wire(), command.step());
                assertEquals(Optional.of(BigInteger.ZERO), command.expectedRevision());
                assertTrue(command.expectedSnapshotRevision().isEmpty());
                var fields = StrictJson.parse(command.normalizedAdditionalFields().value());
                assertEquals(Set.of("core_clock_control", "core_control_deadline_unix_ms"), fields(fields));
                assertTrue(fields.get("core_control_deadline_unix_ms").isIntegralNumber());
                assertEquals(until.toEpochMilli(), fields.get("core_control_deadline_unix_ms").longValue());
                var body = fields.get("core_clock_control");
                assertEquals(CONTROL_FIELDS, fields(body));
                assertEquals(StrictJson.parse(CoreClockControl.request(step,
                        assertInstanceOf(CoreFrame.Partial.class, before.frame())).additionalFields().bytes())
                        .get("core_clock_control"), body);
                assertEquals("ck3_1210_core_clock_control_v1", body.get("schema").textValue());
                assertEquals("1.21.0", body.get("game_version").textValue());
                assertEquals(BUILD.executableSha256(), body.get("executable_sha256").textValue());
                assertFalse(body.has("expected_revision"));
                assertFalse(body.has("core_control_deadline_unix_ms"));
                assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
                assertCounts(fixture, 1);
            }
        }
    }

    @Test
    void anAttemptedReceiptCannotWriteAnotherControlEvenAfterItsPositiveSubmittedAck() throws Exception {
        try (var fixture = new Fixture(partial(), true, false)) {
            var before = fixture.received();
            var until = before.validUntil().minusSeconds(5);
            assertInstanceOf(NativeActionPort.AckReceived.class,
                    fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP, until));
            zero(fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.RESUME_MAP, until));
            assertCounts(fixture, 1);
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
        }
    }

    @Test
    void sameSessionForeignIssuerAndMissingControlCapabilityCannotWriteAControl() throws Exception {
        try (var owner = new Fixture(partial(), true, false);
                var foreign = new Fixture(partial(), true, false)) {
            var before = owner.received();
            assertEquals(owner.actual.awaitHello(before.validUntil()), foreign.actual.awaitHello(before.validUntil()));
            zero(foreign.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP,
                    before.validUntil().minusSeconds(5)));
            assertCounts(owner, 0);
            assertEquals(0, foreign.source.queries);
            assertTrue(foreign.source.controls.isEmpty());
            assertEquals(0, foreign.source.fullStateWrites);
        }
        try (var missing = new Fixture(partial(), false, false)) {
            var before = missing.received();
            zero(missing.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP,
                    before.validUntil().minusSeconds(5)));
            assertCounts(missing, 0);
        }
    }

    @Test
    void anUnknownControlRetainsItsOriginalIdentityAndPacketAndNeverWritesAReplacement() throws Exception {
        try (var fixture = new Fixture(partial(), true, true)) {
            var before = fixture.received();
            var until = before.validUntil().minusSeconds(5);
            var unknown = assertInstanceOf(NativeActionPort.Unknown.class,
                    fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.RESUME_MAP, until));
            byte[] packet = fixture.source.controls.getFirst();
            assertEquals(NativeWire.decodeExecuteRequest(packet).requestId(), unknown.requestId());
            assertArrayEquals(packet, unknown.originalRequestPacket());
            var repeated = fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP, until);
            assertSame(unknown, repeated);
            assertEquals(unknown.requestId(), repeated.requestId());
            assertArrayEquals(packet, assertInstanceOf(NativeActionPort.Unknown.class, repeated).originalRequestPacket());
            assertCounts(fixture, 1);
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
        }
    }

    @Test
    void laterAndExpiredDeadlinesCannotExtendTheOriginalReceiptOrEnterAControlWrite() throws Exception {
        try (var fixture = new Fixture(partial(), true, false)) {
            var before = fixture.received();
            zero(fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP,
                    before.validUntil().plusNanos(1)));
            assertCounts(fixture, 0);
            fixture.clock.set(before.validUntil());
            zero(fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP, before.validUntil()));
            assertCounts(fixture, 0);
        }
    }

    @Test
    void theOriginalUnavailableAndNegativeNonlivingOrUnreadyPrefixesCannotEnterAControlWrite() throws Exception {
        var prefix = assertInstanceOf(CoreFrame.Partial.class, CoreFrame.decode(new RawJson(partial()))).prefix();
        // Deliberate negative public DATA, not claims that C++ observed these alternate prefixes.
        var negative = List.of(
                new CoreFrame.Prefix(prefix.dateRaw(), prefix.speed(), true, prefix.localPlayerId(), false,
                        true, prefix.playedCharacterId(), true),
                new CoreFrame.Prefix(prefix.dateRaw(), prefix.speed(), true, prefix.localPlayerId(), true,
                        false, -1, false),
                new CoreFrame.Prefix(prefix.dateRaw(), prefix.speed(), true, prefix.localPlayerId(), true,
                        true, prefix.playedCharacterId(), false));
        var payloads = new ArrayList<byte[]>();
        payloads.add(unavailable());
        for (var candidate : negative) payloads.add(encoded(candidate));
        for (byte[] payload : payloads) {
            try (var fixture = new Fixture(payload, true, false)) {
                var before = fixture.received();
                zero(fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP,
                        before.validUntil().minusSeconds(5)));
                assertCounts(fixture, 0);
                assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
            }
        }
    }

    @Test
    void saveRequiresAnActuallyPausedPrefixAndItsRejectionDoesNotConsumeTheReceipt() throws Exception {
        var prefix = assertInstanceOf(CoreFrame.Partial.class, CoreFrame.decode(new RawJson(partial()))).prefix();
        // Negative DATA derived from the original prefix, explicitly running rather than a new C++ observation.
        var running = new CoreFrame.Prefix(prefix.dateRaw(), prefix.speed(), false, prefix.localPlayerId(),
                prefix.mapReady(), prefix.hasPlayedCharacter(), prefix.playedCharacterId(), prefix.playedCharacterAlive());
        try (var fixture = new Fixture(encoded(running), true, false)) {
            var before = fixture.received();
            var until = before.validUntil().minusSeconds(5);
            zero(fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.SAVE_CHECKPOINT, until));
            assertCounts(fixture, 0);
            var submitted = assertInstanceOf(NativeActionPort.AckReceived.class,
                    fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP, until));
            assertArrayEquals(SUBMITTED, submitted.originalResultToken().orElseThrow().bytes());
            assertCounts(fixture, 1);
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
        }
    }

    private static byte[] partial() throws Exception {
        return payload("core-producer-partial.json", 599,
                "1d7df534e64680a88b4a40665b175c15b1928c47f0cdd0c5058ef381063d9ec6");
    }

    private static byte[] unavailable() throws Exception {
        return payload("core-producer-unavailable.json", 620,
                "4a1c50df66540be46f59d210ae53eaf318ae0f7089b3663a6eed0cd4bdf2c38d");
    }

    private static byte[] payload(String name, int bytes, String sha) throws Exception {
        String root = System.getProperty("xar.native.core1210.fixtures");
        byte[] original;
        if(root==null||root.isBlank()) {
            try(var input=NativeCoreClockControlPortTest.class.getResourceAsStream("/native1210/"+name)) {
                if(input==null)throw new IOException("exact C++ producer test resource missing: "+name);
                original=input.readNBytes(bytes+1);
            }
        } else {
            if(!Path.of(root).isAbsolute())throw new IOException("exact absolute xar.native.core1210.fixtures required");
            original=Files.readAllBytes(Path.of(root).resolve(name));
        }
        assertEquals(bytes, original.length);
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        return original;
    }

    private static byte[] encoded(CoreFrame.Prefix prefix) {
        return CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD, prefix)).bytes();
    }

    private static NativePipeEndpoint.Config config() {
        return new NativePipeEndpoint.Config("\\\\.\\pipe\\core-control1210-software", "core-control1210-software",
                GAME, "core-control1210-session", BRIDGE, BUILD.executableSha256(), ADAPTER);
    }

    private static ObjectNode hello(boolean controls) {
        var row = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", GAME.pid())
                .put("connection_generation", 1).put("bridge_version", BRIDGE)
                .put("expected_ck3_version", BUILD.version()).put("expected_ck3_sha256", BUILD.executableSha256())
                .put("game_adapter_id", ADAPTER).put("game_adapter_status", "ready").put("ck3_build_match", true);
        var capabilities = row.putArray("capabilities").add(CoreFrame.CAPABILITY);
        if (controls) for (var step : CoreClockControl.Step.values()) capabilities.add(step.requiredCapability());
        return row;
    }

    private static void zero(NativeActionPort.DispatchOutcome outcome) {
        var rejected = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, outcome);
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, rejected.proof().stage());
        assertEquals(0, rejected.proof().requestBytesWritten());
        assertFalse(rejected.proof().reason().isBlank());
    }

    private static void assertCounts(Fixture fixture, int controls) {
        assertEquals(1, fixture.source.queries);
        assertEquals(controls, fixture.source.controls.size());
        assertEquals(1 + controls, fixture.source.writes);
        assertEquals(0, fixture.source.fullStateWrites);
    }

    private static Set<String> fields(JsonNode node) {
        assertTrue(node.isObject());
        var names = new HashSet<String>();
        node.fieldNames().forEachRemaining(names::add);
        return names;
    }

    private static final class Fixture implements AutoCloseable {
        final MutableClock clock = new MutableClock(Instant.now());
        final Replay source;
        final NativeGameTransport actual;
        final Instant deadline = clock.instant().plusSeconds(120);

        Fixture(byte[] result, boolean controlCapabilities, boolean unknownControl) throws IOException {
            source = new Replay(result, hello(controlCapabilities), clock, unknownControl);
            actual = new NativeGameTransport(source, config(), 16, 32, List.of(), clock);
        }

        NativeGameTransport.CoreReceived received() throws InterruptedException {
            var received = assertInstanceOf(NativeGameTransport.CoreReceived.class, actual.readCoreFrameReceived(deadline));
            assertEquals(deadline, received.validUntil());
            var ack = received.original();
            assertTrue(ack.nativeOk());
            assertArrayEquals(source.result, ack.originalResultToken().orElseThrow().bytes());
            ack.custody().orElseThrow().verify(ack);
            return received;
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
        final List<byte[]> controls = new ArrayList<>();
        final byte[] result;
        final MutableClock clock;
        final boolean unknownControl;
        int queries, writes, fullStateWrites;
        boolean closed;

        Replay(byte[] result, ObjectNode hello, MutableClock clock, boolean unknownControl) throws IOException {
            this.result = result.clone(); this.clock = clock; this.unknownControl = unknownControl;
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }

        @Override public void verify() throws IOException { if (closed) throw new IOException("software source closed"); }
        @Override public void awaitConnection(Instant until) throws IOException { check(until); }
        private void check(Instant until) throws IOException {
            verify(); if (!clock.instant().isBefore(until)) throw new IOException("software operation deadline expired");
        }

        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);
            if (packets.isEmpty()) throw new IOException("software control response absent after the actual write");
            return packets.removeFirst();
        }

        @Override public void writePacket(byte[] original, Instant until) throws IOException {
            check(until);
            var command = NativeWire.decodeExecuteRequest(original);
            writes++;
            if (command.step().equals(NativeFreshSnapshotPort.STEP)) fullStateWrites++;
            byte[] response;
            if (command.step().equals(CoreFrame.STEP)) {
                queries++;
                assertEquals(Optional.of(BigInteger.ZERO), command.expectedRevision());
                assertTrue(command.expectedSnapshotRevision().isEmpty());
                assertEquals(0, NativeWire.object(NativeWire.parse(command.normalizedAdditionalFields().value())).size());
                response = result;
            } else {
                CoreClockControl.Step.fromWire(command.step());
                controls.add(original.clone());
                if (unknownControl) return;
                response = SUBMITTED;
            }
            var output = new ByteArrayOutputStream();
            output.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + command.requestId() + "\",\"ok\":true,\"result\":").getBytes(StandardCharsets.UTF_8));
            output.writeBytes(response); output.write('}');
            packets.add(NativeWire.packet(output.toByteArray()));
        }

        @Override public void close() { closed = true; }
    }
}
