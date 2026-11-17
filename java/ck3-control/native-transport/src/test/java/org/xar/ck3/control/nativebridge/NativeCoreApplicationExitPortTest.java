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

/** Real private-receipt software packet tests. Requested ACK DATA does not prove a process exit. */
final class NativeCoreApplicationExitPortTest {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_1210;
    private static final String STEP = "normal-exit-application-v1";
    private static final String CAPABILITY = "game.command." + STEP;
    private static final String ADAPTER = "ck3-1.21.0-msvc-x64", BRIDGE = "software-core-exit1210";
    private static final GameGeneration GAME = new GameGeneration(42,
            new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final byte[] REQUESTED = "{\"requested\":true,\"normal_exit_confirmed\":false}"
            .getBytes(StandardCharsets.UTF_8);
    private static final byte[] SUBMITTED = "{\"submitted\":true}".getBytes(StandardCharsets.UTF_8);
    private static final Set<String> CLAIM_FIELDS = Set.of("schema", "game_version", "executable_sha256",
            "adapter_id", "backend", "date_raw", "speed", "paused", "local_player_id", "map_ready",
            "has_played_character", "played_character_id", "played_character_alive");

    private static byte[] recordedExitResult()throws Exception {
        byte[] packet=payload("application-exit-producer-ack01.json",533,
                "3fe5153d80540f848ec18b4c37fefccbcd4664216aefcfddc550c8c2be3ad6a6");
        var result=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(packet)));
        assertTrue(result.nativeOk());return result.result().token().orElseThrow().value();
    }
    @Test void theActualCppExitResultPassesTheOriginalReceiverWithoutAnExitEffectClaim()throws Exception {
        try(var fixture=new Fixture(partial(),true,false)) {
            fixture.source.exitResponse=recordedExitResult();var before=fixture.received();
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,fixture.actual.submitCoreNormalExit(before,before.validUntil().minusSeconds(5)));
            assertArrayEquals(recordedExitResult(),ack.originalResultToken().orElseThrow().bytes());
            var token=StrictJson.parse(ack.originalResultToken().orElseThrow().bytes());
            assertEquals("ck3_1210_application_exit_result_v1",token.get("schema").textValue());
            assertEquals("requested",token.get("dispatch_status").textValue());assertFalse(token.get("normal_exit_confirmed").booleanValue());
            ack.custody().orElseThrow().verify(ack);counts(fixture,1,1,0);
        }
    }
    @Test void anIndeterminateNativeExitAckBecomesStickyUnknownWithTheOriginalAckRetained()throws Exception {
        try(var fixture=new Fixture(partial(),true,false)) {
            var negative=(ObjectNode)StrictJson.parse(recordedExitResult()); // Deliberate negative DATA, not another observed producer result.
            negative.put("dispatch_status","indeterminate").put("accepted",false).put("effect_attempted",true);
            fixture.source.exitResponse=StrictJson.canonical(negative);fixture.source.exitOk=false;
            var before=fixture.received();var until=before.validUntil().minusSeconds(5);
            var unknown=assertInstanceOf(NativeActionPort.Unknown.class,fixture.actual.submitCoreNormalExit(before,until));
            var ack=fixture.actual.originalIndeterminateCoreAcknowledgement(unknown.requestId()).orElseThrow();
            assertFalse(ack.nativeOk());ack.custody().orElseThrow().verify(ack);
            assertArrayEquals(ack.outbound().orElseThrow().originalPacket(),unknown.originalRequestPacket());
            assertEquals(ack.originalFrame(),unknown.rawReturn().orElseThrow());
            assertSame(unknown,fixture.actual.submitCoreClockControl(before,CoreClockControl.Step.PAUSE_MAP,until));
            assertSame(unknown,fixture.actual.submitCoreNormalExit(before,until));counts(fixture,1,1,0);
        }
    }

    @Test
    void originalPrivateReceiptSubmitsOnlyTheExactExitClaimAndEarlierFiniteDeadline() throws Exception {
        try (var fixture = new Fixture(partial(), true, false)) {
            var before = fixture.received();
            var frame = assertInstanceOf(CoreFrame.Partial.class, before.frame());
            var request = CoreApplicationExit.request(frame);
            assertEquals(STEP, request.step());
            assertEquals(Optional.of(CAPABILITY), request.requiredCapability());
            assertTrue(request.preparationEvidence().isEmpty());
            var pure = StrictJson.parse(request.additionalFields().bytes());
            assertEquals(Set.of("core_application_exit"), fields(pure));
            assertClaim(frame, pure.get("core_application_exit"));
            var until = before.validUntil().minusSeconds(5);
            var ack = requested(fixture.actual.submitCoreNormalExit(before, until));
            var packet = fixture.source.exits.getFirst();
            assertArrayEquals(packet, ack.outbound().orElseThrow().originalPacket());
            var command = NativeWire.decodeExecuteRequest(packet);
            assertEquals(STEP, command.step());
            assertEquals(ack.requestId(), command.requestId());
            assertEquals(Optional.of(BigInteger.ZERO), command.expectedRevision());
            assertTrue(command.expectedSnapshotRevision().isEmpty());
            var additional = StrictJson.parse(command.normalizedAdditionalFields().value());
            assertEquals(Set.of("core_application_exit", "core_control_deadline_unix_ms"), fields(additional));
            assertTrue(additional.get("core_control_deadline_unix_ms").isIntegralNumber());
            assertEquals(until.toEpochMilli(), additional.get("core_control_deadline_unix_ms").longValue());
            assertEquals(pure.get("core_application_exit"), additional.get("core_application_exit"));
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
            counts(fixture, 1, 1, 0);
        }
    }

    @Test
    void aPartialRunningPrefixWithoutAMapOrPlayedActorCanRequestApplicationExit() throws Exception {
        var prefix = actualPrefix();
        // Deliberate alternate public DATA; no claim that C++ observed this synthetic negative-world prefix.
        var withoutWorld = new CoreFrame.Prefix(prefix.dateRaw(), prefix.speed(), false, -1, false, false, -1, false);
        try (var fixture = new Fixture(encoded(withoutWorld), true, false)) {
            var before = fixture.received();
            requested(fixture.actual.submitCoreNormalExit(before, before.validUntil().minusSeconds(5)));
            var command = NativeWire.decodeExecuteRequest(fixture.source.exits.getFirst());
            var body = StrictJson.parse(command.normalizedAdditionalFields().value()).get("core_application_exit");
            assertClaim(assertInstanceOf(CoreFrame.Partial.class, before.frame()), body);
            assertFalse(body.get("paused").booleanValue());
            assertFalse(body.get("map_ready").booleanValue());
            assertFalse(body.get("has_played_character").booleanValue());
            assertEquals(-1, body.get("played_character_id").intValue());
            counts(fixture, 1, 1, 0);
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
        }
    }
    @Test
    void failedBackgroundPolicyRejectsExitBeforeItsTokenOrLifetimeClaimIsConsumed() throws Exception {
        try(var fixture=new Fixture(partial(),true,false)) {
            var before=fixture.received();var until=before.validUntil().minusSeconds(5);
            fixture.source.backgroundReady=false;
            zero(fixture.actual.submitCoreNormalExit(before,until));counts(fixture,1,0,0);
            fixture.source.backgroundReady=true;
            requested(fixture.actual.submitCoreNormalExit(before,until));counts(fixture,1,1,0);
        }
    }

    @Test
    void unavailableIsNotAPartialExitReceiptAndOldBuildDataCannotAcquireTheNewClaim() throws Exception {
        try (var fixture = new Fixture(unavailable(), true, false)) {
            var before = fixture.received();
            assertInstanceOf(CoreFrame.Unavailable.class, before.frame());
            zero(fixture.actual.submitCoreNormalExit(before, before.validUntil().minusSeconds(5)));
            counts(fixture, 1, 0, 0);
        }
        assertThrows(IllegalArgumentException.class, () -> CoreApplicationExit.request(
                new CoreFrame.Partial(ExactCk3Build.CK3_12004, actualPrefix())));
    }

    @Test
    void foreignIssuerAndMissingExitCapabilityCannotEnterAnExitWrite() throws Exception {
        try (var owner = new Fixture(partial(), true, false);
                var foreign = new Fixture(partial(), true, false)) {
            var before = owner.received();
            assertEquals(owner.actual.awaitHello(before.validUntil()), foreign.actual.awaitHello(before.validUntil()));
            zero(foreign.actual.submitCoreNormalExit(before, before.validUntil().minusSeconds(5)));
            counts(owner, 1, 0, 0);
            counts(foreign, 0, 0, 0);
        }
        try (var missing = new Fixture(partial(), false, false)) {
            var before = missing.received();
            zero(missing.actual.submitCoreNormalExit(before, before.validUntil().minusSeconds(5)));
            counts(missing, 1, 0, 0);
        }
    }

    @Test
    void laterAndExpiredDeadlinesCannotExtendTheOriginalQueryWindow() throws Exception {
        try (var fixture = new Fixture(partial(), true, false)) {
            var before = fixture.received();
            zero(fixture.actual.submitCoreNormalExit(before, before.validUntil().plusNanos(1)));
            counts(fixture, 1, 0, 0);
            fixture.clock.set(before.validUntil());
            zero(fixture.actual.submitCoreNormalExit(before, before.validUntil()));
            counts(fixture, 1, 0, 0);
        }
    }

    @Test
    void clockControlAndExitConsumeTheSameReceiptRatherThanIndependentPublicDataClaims() throws Exception {
        try (var fixture = new Fixture(partial(), true, false)) {
            var before = fixture.received();
            var until = before.validUntil().minusSeconds(5);
            assertInstanceOf(NativeActionPort.AckReceived.class,
                    fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP, until));
            zero(fixture.actual.submitCoreNormalExit(before, until));
            counts(fixture, 1, 0, 1);
            // A successful clock write consumes that receipt, not the transport's eventual exit claim.
            var fresh = fixture.received();
            requested(fixture.actual.submitCoreNormalExit(fresh, fresh.validUntil().minusSeconds(5)));
            counts(fixture, 2, 1, 1);
        }
        try (var fixture = new Fixture(partial(), true, false)) {
            var before = fixture.received();
            var until = before.validUntil().minusSeconds(5);
            requested(fixture.actual.submitCoreNormalExit(before, until));
            zero(fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP, until));
            counts(fixture, 1, 1, 0);
        }
    }

    @Test
    void aNewReceiptCannotBypassTheTransportExitWriteLatchForExitOrClockControl() throws Exception {
        try (var fixture = new Fixture(partial(), true, false)) {
            var before = fixture.received();
            var first = requested(fixture.actual.submitCoreNormalExit(before, before.validUntil().minusSeconds(5)));
            var fresh = fixture.received();
            assertNotEquals(before.original().requestId(), fresh.original().requestId());
            assertNotEquals(first.requestId(), fresh.original().requestId());
            var until = fresh.validUntil().minusSeconds(5);
            zero(fixture.actual.submitCoreNormalExit(fresh, until));
            zero(fixture.actual.submitCoreClockControl(fresh, CoreClockControl.Step.RESUME_MAP, until));
            counts(fixture, 2, 1, 0);
            assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
        }
    }

    @Test
    void unknownExitAndUnknownClockShareTheOriginalIdentityAndPacketFenceInBothDirections() throws Exception {
        for (boolean exitFirst : new boolean[] {true, false}) {
            try (var fixture = new Fixture(partial(), true, true)) {
                var before = fixture.received();
                var until = before.validUntil().minusSeconds(5);
                var first = assertInstanceOf(NativeActionPort.Unknown.class, exitFirst
                        ? fixture.actual.submitCoreNormalExit(before, until)
                        : fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.PAUSE_MAP, until));
                byte[] original = exitFirst ? fixture.source.exits.getFirst() : fixture.source.clocks.getFirst();
                assertEquals(NativeWire.decodeExecuteRequest(original).requestId(), first.requestId());
                assertArrayEquals(original, first.originalRequestPacket());
                assertSame(first, fixture.actual.submitCoreNormalExit(before, until));
                var clock = fixture.actual.submitCoreClockControl(before, CoreClockControl.Step.RESUME_MAP, until);
                assertSame(first, clock);
                assertEquals(first.requestId(), clock.requestId());
                assertArrayEquals(original, assertInstanceOf(NativeActionPort.Unknown.class, clock).originalRequestPacket());
                counts(fixture, 1, exitFirst ? 1 : 0, exitFirst ? 0 : 1);
                assertTrue(fixture.actual.latestObservedSnapshot().isEmpty());
            }
        }
    }

    private static void assertClaim(CoreFrame.Partial frame, JsonNode claim) {
        assertEquals(CLAIM_FIELDS, fields(claim));
        assertEquals("ck3_1210_application_exit_v1", claim.get("schema").textValue());
        assertEquals("1.21.0", claim.get("game_version").textValue());
        assertEquals(BUILD.executableSha256(), claim.get("executable_sha256").textValue());
        assertEquals(ADAPTER, claim.get("adapter_id").textValue());
        assertEquals("ck3-1.21.0-native-headless-main-thread", claim.get("backend").textValue());
        var prefix = frame.prefix();
        assertEquals(prefix.dateRaw(), claim.get("date_raw").intValue());
        assertEquals(prefix.speed(), claim.get("speed").intValue());
        assertEquals(prefix.paused(), claim.get("paused").booleanValue());
        assertEquals(prefix.localPlayerId(), claim.get("local_player_id").intValue());
        assertEquals(prefix.mapReady(), claim.get("map_ready").booleanValue());
        assertEquals(prefix.hasPlayedCharacter(), claim.get("has_played_character").booleanValue());
        assertEquals(prefix.playedCharacterId(), claim.get("played_character_id").intValue());
        assertEquals(prefix.playedCharacterAlive(), claim.get("played_character_alive").booleanValue());
        assertFalse(claim.has("expected_revision"));
        assertFalse(claim.has("core_control_deadline_unix_ms"));
    }

    private static NativeActionPort.AckReceived requested(NativeActionPort.DispatchOutcome outcome) {
        var ack = assertInstanceOf(NativeActionPort.AckReceived.class, outcome);
        assertTrue(ack.nativeOk());
        assertArrayEquals(REQUESTED, ack.originalResultToken().orElseThrow().bytes());
        var result = StrictJson.parse(ack.originalResultToken().orElseThrow().bytes());
        assertTrue(result.get("requested").booleanValue());
        assertFalse(result.get("normal_exit_confirmed").booleanValue());
        ack.custody().orElseThrow().verify(ack);
        return ack;
    }

    private static void zero(NativeActionPort.DispatchOutcome outcome) {
        var rejected = assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class, outcome);
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, rejected.proof().stage());
        assertEquals(0, rejected.proof().requestBytesWritten());
        assertFalse(rejected.proof().reason().isBlank());
    }

    private static void counts(Fixture fixture, int queries, int exits, int clocks) {
        assertEquals(queries, fixture.source.queries);
        assertEquals(exits, fixture.source.exits.size());
        assertEquals(clocks, fixture.source.clocks.size());
        assertEquals(queries + exits + clocks, fixture.source.writes);
        assertEquals(0, fixture.source.fullStateWrites);
    }

    private static Set<String> fields(JsonNode node) {
        assertTrue(node.isObject());
        var names = new HashSet<String>(); node.fieldNames().forEachRemaining(names::add); return names;
    }

    private static CoreFrame.Prefix actualPrefix() throws Exception {
        return assertInstanceOf(CoreFrame.Partial.class, CoreFrame.decode(new RawJson(partial()))).prefix();
    }

    private static byte[] encoded(CoreFrame.Prefix prefix) {
        return CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD, prefix)).bytes();
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
        if (root == null || root.isBlank()) {
            try (var input = NativeCoreApplicationExitPortTest.class.getResourceAsStream("/native1210/" + name)) {
                if (input == null) throw new IOException("exact C++ producer test resource missing: " + name);
                original = input.readNBytes(bytes + 1);
            }
        } else {
            if (!Path.of(root).isAbsolute()) throw new IOException("exact absolute xar.native.core1210.fixtures required");
            original = Files.readAllBytes(Path.of(root).resolve(name));
        }
        assertEquals(bytes, original.length);
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        return original;
    }

    private static NativePipeEndpoint.Config config() {
        return new NativePipeEndpoint.Config("\\\\.\\pipe\\core-exit1210-software", "core-exit1210-software",
                GAME, "core-exit1210-session", BRIDGE, BUILD.executableSha256(), ADAPTER);
    }

    private static ObjectNode hello(boolean exitCapability) {
        var row = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", GAME.pid())
                .put("connection_generation", 1).put("bridge_version", BRIDGE)
                .put("expected_ck3_version", BUILD.version()).put("expected_ck3_sha256", BUILD.executableSha256())
                .put("game_adapter_id", ADAPTER).put("game_adapter_status", "ready").put("ck3_build_match", true);
        var capabilities = row.putArray("capabilities").add(CoreFrame.CAPABILITY);
        for (var step : CoreClockControl.Step.values()) capabilities.add(step.requiredCapability());
        if (exitCapability) capabilities.add(CAPABILITY);
        return row;
    }

    private static final class Fixture implements AutoCloseable {
        final MutableClock clock = new MutableClock(Instant.now());
        final Replay source;
        final NativeGameTransport actual;
        final Instant deadline = clock.instant().plusSeconds(120);

        Fixture(byte[] result, boolean exitCapability, boolean unknownMutation) throws IOException {
            source = new Replay(result, hello(exitCapability), clock, unknownMutation);
            actual = new NativeGameTransport(source, config(), 16, 32, List.of(), clock);
        }

        NativeGameTransport.CoreReceived received() throws InterruptedException {
            var received = assertInstanceOf(NativeGameTransport.CoreReceived.class, actual.readCoreFrameReceived(deadline));
            assertEquals(deadline, received.validUntil());
            assertTrue(received.original().nativeOk());
            assertArrayEquals(source.result, received.original().originalResultToken().orElseThrow().bytes());
            received.original().custody().orElseThrow().verify(received.original());
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
        final List<byte[]> exits = new ArrayList<>(), clocks = new ArrayList<>();
        final byte[] result;
        final MutableClock clock;
        final boolean unknownMutation;
        int queries, writes, fullStateWrites;
        boolean closed;
        byte[] exitResponse=REQUESTED.clone();boolean exitOk=true;

        Replay(byte[] result, ObjectNode hello, MutableClock clock, boolean unknownMutation) throws IOException {
            this.result = result.clone(); this.clock = clock; this.unknownMutation = unknownMutation;
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }

        @Override public void verify() throws IOException { if (closed) throw new IOException("software source closed"); }
        boolean backgroundReady=true;
        @Override public void verifyCoreControlWindowPolicy()throws IOException {
            verify();if(!backgroundReady)throw new IOException("software background policy is unavailable");
        }
        @Override public void awaitConnection(Instant until) throws IOException { check(until); }
        private void check(Instant until) throws IOException {
            verify(); if (!clock.instant().isBefore(until)) throw new IOException("software operation deadline expired");
        }

        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);
            if (packets.isEmpty()) throw new IOException("software response absent after the actual mutation write");
            return packets.removeFirst();
        }

        @Override public void writePacket(byte[] original, Instant until) throws IOException {
            check(until);
            var command = NativeWire.decodeExecuteRequest(original); writes++;
            if (command.step().equals(NativeFreshSnapshotPort.STEP)) fullStateWrites++;
            byte[] response;
            if (command.step().equals(CoreFrame.STEP)) {
                queries++;
                assertEquals(Optional.of(BigInteger.ZERO), command.expectedRevision());
                assertTrue(command.expectedSnapshotRevision().isEmpty());
                assertEquals(0, NativeWire.object(NativeWire.parse(command.normalizedAdditionalFields().value())).size());
                response = result;
            } else if (command.step().equals(STEP)) {
                exits.add(original.clone());
                if (unknownMutation) return;
                response = exitResponse;
            } else {
                CoreClockControl.Step.fromWire(command.step()); clocks.add(original.clone());
                if (unknownMutation) return;
                response = SUBMITTED;
            }
            var output = new ByteArrayOutputStream();
            output.writeBytes(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""
                    + command.requestId() + "\",\"ok\":"+(!command.step().equals(STEP)||exitOk)+",\"result\":").getBytes(StandardCharsets.UTF_8));
            output.writeBytes(response); output.write('}'); packets.add(NativeWire.packet(output.toByteArray()));
        }

        @Override public void close() { closed = true; }
    }
}
