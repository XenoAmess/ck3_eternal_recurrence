package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.Optional;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

final class NativeCurrentFull111EventRendererTest {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final CoreFrame.Prefix PREFIX = new CoreFrame.Prefix(53144328, 1, true, 0, true, true, -16777215, true);
    private static final GameGeneration GAME = new GameGeneration(42, new PythonOnlyUInt64(BigInteger.TEN));
    private static final String AVAILABLE = "full111-ordinary-event-renderer.json";
    private static final String UNAVAILABLE = "full111-ordinary-event-renderer-unavailable.json";
    private static final String REQUEST = "full111-ordinary-event-renderer.request.json";

    @Test void cppFixturesKeepStockOrderAndThreeIndependentFlags() throws Exception {
        var result = CurrentFull111EventRenderer.decodeOutcome(ack(read(AVAILABLE)));
        assertEquals(CurrentFull111EventRenderer.Status.AVAILABLE, result.status());
        assertEquals(PREFIX, result.factsBefore().orElseThrow());
        assertEquals(NativeWire.UINT64_MAX, result.owner().orElseThrow().connectionGeneration());
        var source = result.source().orElseThrow();
        assertEquals(7, source.instanceId());
        assertEquals(6, source.authoredOptionCount());
        assertEquals("bookmark.1070", source.definitionKey());
        assertEquals(List.of(
                new CurrentFull111EventRenderer.Option(4, false, false, true, "Native hidden", "Stock\u0015 disabled reason"),
                new CurrentFull111EventRenderer.Option(1, true, true, false, "Native visible", "")), source.options());

        var unavailable = CurrentFull111EventRenderer.decodeOutcome(ack(read(UNAVAILABLE)));
        assertEquals(CurrentFull111EventRenderer.Status.UNAVAILABLE, unavailable.status());
        assertTrue(unavailable.source().isEmpty());
        assertTrue(unavailable.unavailableReason().isPresent());
        assertEquals(BigInteger.ZERO, unavailable.providerGeneration());
        assertEquals(BigInteger.ZERO, unavailable.querySequence());
    }

    @Test void exactRendererWireRejectsAlteredRolesAndIdentity() throws Exception {
        var original = NativeWire.object(NativeWire.parse(read(AVAILABLE)));
        var invalid = original.deepCopy();
        result(invalid).put("schema", CurrentLyd.RESULT_SCHEMA);
        rejects(invalid);
        invalid = original.deepCopy();
        result(invalid).put("effect_attempted", false);
        rejects(invalid);
        invalid = original.deepCopy();
        result(invalid).putNull("owner");
        rejects(invalid);
        invalid = original.deepCopy();
        NativeWire.object(result(invalid).get("source")).put("recipient_character_id", 73);
        rejects(invalid);
        invalid = original.deepCopy();
        row(invalid, 0).put("widget_enabled", 1);
        rejects(invalid);
        invalid = original.deepCopy();
        row(invalid, 0).putNull("widget_visible");
        rejects(invalid);
        invalid = original.deepCopy();
        row(invalid, 1).put("authored_option_index", 4);
        rejects(invalid);
        invalid = original.deepCopy();
        row(invalid, 1).put("authored_option_index", 6);
        rejects(invalid);
        invalid = original.deepCopy();
        result(invalid).put("provider_generation", "0");
        rejects(invalid);
        invalid = original.deepCopy();
        invalid.put("ok", false);
        rejects(invalid);
    }

    @Test void javaRequestMatchesTheActualEmitterWithPositiveTarget() throws Exception {
        var expected = NativeWire.object(NativeWire.parse(read(REQUEST)));
        byte[] query = CurrentFull111EventRenderer.queryPacket(expected.path("request_id").textValue(),
                new CoreFrame.Partial(BUILD, PREFIX), 7, Instant.ofEpochMilli(expected.path("core_control_deadline_unix_ms").longValue()));
        var actual = NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(query, 4, query.length)));
        var actualLyd = NativeWire.object(actual.get("lyd"));
        assertTrue(expected.path("lyd").path("executable_sha256").textValue().equalsIgnoreCase(actualLyd.path("executable_sha256").textValue()));
        actualLyd.set("executable_sha256", expected.path("lyd").path("executable_sha256"));
        assertArrayEquals(StrictJson.canonical(expected), StrictJson.canonical(actual));
        assertThrows(IllegalArgumentException.class, () -> CurrentFull111EventRenderer.queryPacket("zero-foreground",
                new CoreFrame.Partial(BUILD, PREFIX), 0, Instant.now()));
    }

    @Test void actualRendererOnlyTransportNeedsTheOriginalCoreAndNewAdvertisedCapability() throws Exception {
        try (var renderer = new SoftwareEndpoint(true);
                var original = transport(renderer);
                var old = new SoftwareEndpoint(false);
                var other = transport(old)) {
            var deadline = Instant.now().plusSeconds(10);
            var core = assertInstanceOf(NativeGameTransport.CoreReceived.class, original.readCoreFrameReceived(deadline));
            var oldCore = assertInstanceOf(NativeGameTransport.CoreReceived.class, other.readCoreFrameReceived(deadline));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,
                    other.readFull111EventRenderer(oldCore, 7, deadline));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,
                    original.readFull111EventRenderer(oldCore, 7, deadline));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,
                    original.readFull111EventRenderer(core, 0, deadline));
            var observed = assertInstanceOf(AckReceived.class, original.readFull111EventRenderer(core, 7, deadline));
            assertEquals(7, CurrentFull111EventRenderer.decodeOutcome(observed).source().orElseThrow().instanceId());
            var basis = core.original().custody().orElseThrow();
            var custody = observed.custody().orElseThrow();
            assertEquals(basis.custodyEpoch(), custody.custodyEpoch());
            assertEquals(basis.session(), custody.session());
            assertTrue(custody.writeEntered().order().compareTo(basis.responseReceived().order()) > 0);
            custody.verify(observed);
            assertEquals(List.of(CoreFrame.STEP, CurrentFull111EventRenderer.STEP), renderer.writes);
            assertEquals(List.of(CoreFrame.STEP), old.writes);
        }
    }

    @Test void aFreshRendererCanRevalidateThePlanAfterTheOriginalWireCutoff() throws Exception {
        var clock = new SoftwareClock(Instant.ofEpochMilli(Instant.now().toEpochMilli()));
        Instant canonicalDeadline = clock.instant().plusSeconds(60).plusNanos(123456);
        try (var endpoint = new SoftwareEndpoint(true); var actual = transport(endpoint, clock)) {
            endpoint.softwareSelectable = true;
            var target = new CurrentFull111EventOption.Target(7, PREFIX.playedCharacterId(), "bookmark.1070", 1);
            var planned = renderer(actual, clock.instant().plusSeconds(8));
            Instant plannedDeadline = CurrentFull111EventOption.rendererDeadline(planned);
            clock.now = clock.instant().plusMillis(38921);
            assertTrue(clock.instant().isAfter(plannedDeadline));
            assertTrue(clock.instant().isBefore(canonicalDeadline));

            Instant lateDeadline = clock.instant().plusSeconds(8);
            var fresh = renderer(actual, lateDeadline);
            assertNotEquals(fresh.requestId(), planned.requestId());
            assertEquals(plannedDeadline.plusMillis(38921), CurrentFull111EventOption.rendererDeadline(fresh));
            assertEquals(lateDeadline, CurrentFull111EventOption.rendererDeadline(fresh));
            assertTrue(CurrentFull111EventOption.rendererDeadline(fresh).isBefore(canonicalDeadline));
            var plannedModel = CurrentFull111EventRenderer.decodeOutcome(planned);
            var freshModel = CurrentFull111EventRenderer.decodeOutcome(fresh);
            assertTrue(CurrentFull111EventOption.matchesPlannedRenderer(plannedModel, freshModel, target));
            assertFalse(CurrentFull111EventOption.matchesPlannedRenderer(plannedModel, plannedModel, target));
            assertTrue(fresh.custody().orElseThrow().writeEntered().order()
                    .compareTo(planned.custody().orElseThrow().responseReceived().order()) > 0);
            assertEquals(planned.custody().orElseThrow().custodyEpoch(), fresh.custody().orElseThrow().custodyEpoch());

            endpoint.changeRenderer = true;
            var changed = renderer(actual, lateDeadline);
            assertFalse(CurrentFull111EventOption.matchesPlannedRenderer(plannedModel,
                    CurrentFull111EventRenderer.decodeOutcome(changed), target));
            assertEquals(List.of(CoreFrame.STEP, CurrentFull111EventRenderer.STEP, CoreFrame.STEP,
                    CurrentFull111EventRenderer.STEP, CoreFrame.STEP, CurrentFull111EventRenderer.STEP), endpoint.writes);
        }
    }

    private static AckReceived renderer(NativeGameTransport actual, Instant deadline) throws InterruptedException {
        var core = assertInstanceOf(NativeGameTransport.CoreReceived.class, actual.readCoreFrameReceived(deadline));
        return assertInstanceOf(AckReceived.class, actual.readFull111EventRenderer(core, 7, deadline));
    }

    private static final class SoftwareClock extends Clock {
        private Instant now;
        private SoftwareClock(Instant now) { this.now = now; }
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) {
            if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException("UTC expected");
            return this;
        }
        @Override public Instant instant() { return now; }
    }

    private static byte[] read(String file) throws Exception {
        try (var resource = NativeCurrentFull111EventRendererTest.class.getResourceAsStream("/current267-full111-renderer-cpp/" + file)) {
            assertNotNull(resource);
            byte[] original = resource.readAllBytes();
            var digest = switch (file) {
                case AVAILABLE -> "71f4faa706bce86352603d67450c789fc6a731aaa35befbc0d4f018c37bbf8a2";
                case UNAVAILABLE -> "471c576def6dc67d1f59df7d1b6bca5480db787232777a0950d5f4e3f6ebca40";
                case REQUEST -> "ca4cb27980156a42b16f8fd9309fa8a3ce3f6af8479b363a9a2adef78ae4b430";
                default -> throw new IllegalArgumentException("No original C++ fixture: " + file);
            };
            assertEquals(digest, ActionCodec.sha256(original));
            return original;
        }
    }

    private static AckReceived ack(byte[] payload) throws IOException {
        byte[] packet = NativeWire.packet(payload);
        var decoded = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new AckReceived(decoded.requestId(), decoded.nativeOk(), decoded.result().token().map(value -> new RawJson(value.value())),
                new RawJson(payload), packet, Optional.empty());
    }

    private static void rejects(ObjectNode envelope) {
        assertThrows(IOException.class, () -> CurrentFull111EventRenderer.decodeOutcome(ack(StrictJson.canonical(envelope))));
    }

    private static ObjectNode result(ObjectNode envelope) throws IOException {
        return NativeWire.object(envelope.get("result"));
    }

    private static ObjectNode row(ObjectNode envelope, int index) throws IOException {
        return NativeWire.object(result(envelope).path("source").path("options").get(index));
    }

    private static NativeGameTransport transport(SoftwareEndpoint source) {
        return transport(source, Clock.systemUTC());
    }

    private static NativeGameTransport transport(SoftwareEndpoint source, Clock clock) {
        String slash = Character.toString(92);
        var config = new NativePipeEndpoint.Config(slash + slash + "." + slash + "pipe" + slash + "render-fixture",
                "software-renderer", GAME, "render-fixture", "software-renderer", BUILD.executableSha256(), BUILD.coreFrameAdapterId());
        return new NativeGameTransport(source, config, 16, 16, List.of(), clock);
    }

    /** Exact C++ result token returned through a controlled endpoint without a physical Game or snapshot. */
    private static final class SoftwareEndpoint implements NativePacketPort {
        private final ArrayDeque<byte[]> packets = new ArrayDeque<>();
        private final java.util.ArrayList<String> writes = new java.util.ArrayList<>();
        private final byte[] rendererReply;
        private boolean softwareSelectable, changeRenderer;
        private int rendererQueries;

        SoftwareEndpoint(boolean renderer) throws Exception {
            rendererReply = read(AVAILABLE);
            var hello = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", GAME.pid())
                    .put("connection_generation", NativeWire.UINT64_MAX).put("bridge_version", "software-renderer")
                    .put("expected_ck3_version", BUILD.version()).put("expected_ck3_sha256", BUILD.executableSha256())
                    .put("game_adapter_id", BUILD.coreFrameAdapterId()).put("game_adapter_status", "ready").put("ck3_build_match", true);
            var capabilities = hello.putArray("capabilities").add(CoreFrame.CAPABILITY).add("game.state.snapshot")
                    .add(NativeFreshSnapshotPort.CAPABILITY);
            if (renderer) capabilities.add(CurrentFull111EventRenderer.CAPABILITY);
            packets.add(NativeWire.packet(StrictJson.canonical(hello)));
        }

        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException {
            if (packets.isEmpty()) throw new IOException("renderer fixture has no more packets");
            return packets.removeFirst();
        }
        @Override public void writePacket(byte[] original, Instant deadline) throws IOException {
            var read = NativeWire.decodeExecuteRequest(original);
            writes.add(read.step());
            assertEquals(Optional.of(BigInteger.ZERO), read.expectedRevision());
            if (read.step().equals(CoreFrame.STEP)) {
                var reply = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                        .put("request_id", read.requestId()).put("ok", true);
                reply.set("result", NativeWire.parse(CoreFramePublicCodec.encode(new CoreFrame.Partial(BUILD, PREFIX)).bytes()));
                packets.add(NativeWire.packet(StrictJson.canonical(reply)));
                return;
            }
            assertEquals(CurrentFull111EventRenderer.STEP, read.step());
            var body = NativeWire.object(NativeWire.parse(read.normalizedAdditionalFields().value()));
            assertEquals(7, body.path("lyd").path("instance_id").intValue());
            assertTrue(body.path("lyd").path("event_role").isNull());
            var payload = new String(rendererReply, StandardCharsets.UTF_8);
            var rebound = payload.replace("\"request_id\":\"lyd-native-real-producer\"",
                    "\"request_id\":\"" + read.requestId() + "\"");
            assertNotEquals(payload, rebound);
            if (softwareSelectable) {
                var reply = NativeWire.object(NativeWire.parse(rebound.getBytes(StandardCharsets.UTF_8)));
                result(reply).put("query_sequence", Integer.toString(++rendererQueries));
                row(reply, 1).put("widget_enabled", true);
                if (changeRenderer) row(reply, 0).put("text", "Changed stock content");
                packets.add(NativeWire.packet(StrictJson.canonical(reply)));
            } else packets.add(NativeWire.packet(rebound.getBytes(StandardCharsets.UTF_8)));
        }
        @Override public void close() { }
    }
}
