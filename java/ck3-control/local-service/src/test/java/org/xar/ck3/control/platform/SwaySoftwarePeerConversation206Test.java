package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Explicit opt-in software process test; no Core, Root issuer, actual CK3 process or natural Sway outcome. */
@EnabledIfSystemProperty(named = "xar.m6.software206.settings", matches = ".+")
public final class SwaySoftwarePeerConversation206Test {
    @Test
    void dynamicChain() throws Exception {
        var settings = settings();
        var result = SwaySoftwarePeerConversation206.run(settings, SwayPeer206Contract.Scenario.DYNAMIC_CHAIN);
        common(settings, result);
        assertEquals(SwayPeer206Contract.Scenario.DYNAMIC_CHAIN, result.scenario());
        assertEquals(List.of("query0", "start", "receipt", "post-start", "finish-target", "finish-completion",
                "finish-opinion", "stop", "post-stop"), result.exchanges().stream().map(SwayPeer206Contract.Exchange::label).toList());
        Set<String> ids = new HashSet<>();
        ids.add(result.before().acknowledgement().requestId()); ids.add(result.after().acknowledgement().requestId());
        String target = "query-active-scheme-sway-target-v1-private-" + settings.target();
        List<String> steps = List.of(target, "submit-active-scheme-sway-v1-private-" + settings.target(),
                "receipt-active-scheme-sway-v1-private-" + settings.target(), target, target,
                "query-sway-completion-v1-private", "query-sway-outcome-opinion-v1-private",
                "stop-active-scheme-sway-v1-private", "query-sway-completion-v1-private");
        for (int index = 0; index < result.exchanges().size(); index++) {
            var exchange = result.exchanges().get(index);
            var request = original(result, exchange);
            assertTrue(ids.add(request.requestId()), "each direct write has a distinct actual request ID");
            assertEquals(steps.get(index), request.step());
            assertEquals(result.before().originalFrame().nativeRevision(), request.expectedRevision().orElseThrow());
            assertTrue(exchange.originalResult().nativeOk());
            var envelope = token(exchange.originalResult().result());
            assertEquals(request.step(), envelope.path("step").textValue());
            assertTrue(bool(envelope, "accepted")); assertTrue(bool(envelope, "private_build"));
            assertFalse(bool(envelope, "advertised"));
        }
        JsonNode query = body(result, 0, "active_scheme_sway");
        assertEquals(0, integer(query, "active_scheme_count")); assertTrue(bool(query, "native_legal_now"));
        assertFalse(bool(query, "matching_sway_active")); assertEquals(37, integer(query, "target_opinion_of_actor"));
        JsonNode startFields = fields(result, 1);
        assertEquals(query.get("capture_epoch"), startFields.get("expected_capture_epoch"));
        assertEquals(query.get("container_generation"), startFields.get("expected_container_generation"));
        assertEquals("37", startFields.path("expected_target_opinion_of_actor").textValue());
        String action = StrictJson.text(startFields.get("action_id"));
        assertFalse(ids.contains(action)); assertTrue(action.startsWith("sway-live206-"));
        JsonNode start = body(result, 1, "active_scheme_sway_formal");
        assertEquals("submitted_verification_pending", start.path("stage").textValue());
        assertEquals(action, start.path("action_id").textValue()); assertTrue(bool(start, "receipt_pending"));
        assertEquals(1, integer(start, "submit_call_count"));
        assertTrue(wide(start, "pre_capture_epoch").compareTo(wide(query, "capture_epoch")) > 0);
        JsonNode receipt = body(result, 2, "active_scheme_sway_formal");
        assertEquals(action, fields(result, 2).path("action_id").textValue());
        assertEquals("applied", receipt.path("stage").textValue()); assertTrue(bool(receipt, "postcondition_verified"));
        assertTrue(wide(receipt, "post_capture_epoch").compareTo(wide(start, "pre_capture_epoch")) > 0);
        long instance = integer(receipt, "scheme_instance_id"), generation = integer(receipt, "scheme_instance_generation");
        assertEquals(0, instance); assertEquals(0, generation); // The controlled source really creates fullScheme0.
        for (int index : List.of(3, 4)) {
            JsonNode current = body(result, index, "active_scheme_sway");
            assertTrue(bool(current, "matching_sway_active")); assertEquals(73, integer(current, "target_opinion_of_actor"));
            assertTrue(wide(current, "capture_epoch").compareTo(wide(receipt, "post_capture_epoch")) > 0);
            JsonNode rows = current.get("active_sway_instances"); assertTrue(rows.isArray()); assertEquals(1, rows.size());
            assertEquals(instance, integer(rows.get(0), "scheme_instance_id"));
            assertEquals(generation, integer(rows.get(0), "scheme_instance_generation"));
        }
        for (int index : List.of(5, 8)) {
            JsonNode completion = body(result, index, "sway_completion");
            assertTrue(bool(completion, "available")); assertTrue(bool(completion, "exact_instance_join_ready"));
            assertTrue(bool(completion, "owner_matches_actor")); assertEquals(0, integer(completion, "native_status_raw"));
            assertEquals(instance, integer(completion, "scheme_instance_id"));
            assertFalse(bool(completion, "native_terminal_state_observed")); assertFalse(bool(completion, "terminal_cause_observed"));
            assertEquals(instance, integer(fields(result, index), "scheme_instance_id"));
        }
        JsonNode opinion = body(result, 6, "sway_outcome_opinion");
        assertTrue(bool(opinion, "available")); assertEquals(73, integer(opinion, "target_opinion_of_actor"));
        JsonNode named = opinion.get("scheme_sway_opinion");
        assertTrue(bool(named, "observed")); assertTrue(bool(named, "present")); assertEquals(12, integer(named, "value"));
        assertFalse(bool(opinion, "instance_terminal_outcome_observed")); assertFalse(bool(opinion, "cancel_outcome_observed"));
        JsonNode stopFields = fields(result, 7), stop = body(result, 7, "sway_stop");
        assertEquals(instance, integer(stopFields, "scheme_instance_id"));
        assertEquals(generation, integer(stopFields, "scheme_instance_generation"));
        assertEquals("submitted_verification_pending", stop.path("status").textValue());
        assertEquals(stopFields.get("action_id"), stop.get("action_id")); assertNotEquals(action, stop.path("action_id").textValue());
        assertFalse(ids.contains(stop.path("action_id").textValue()));
        assertFalse(bool(stop, "postcondition_verified")); assertFalse(bool(stop, "terminal_observed"));
        assertFalse(bool(stop, "terminal_cause_observed")); assertEquals("unknown", stop.path("terminal_cause").textValue());
        for (int index : List.of(5, 6, 7, 8)) {
            assertEquals(settings.actor(), integer(fields(result, index), "actor_character_id"));
            assertEquals(settings.target(), integer(fields(result, index), "target_character_id"));
        }
        Path transition = result.evidenceDirectory().resolve("native-originals/software-opinion-transition.json");
        JsonNode source = StrictJson.parse(Files.readAllBytes(transition));
        assertEquals(73, integer(source, "opinion")); assertEquals(12, integer(source, "named_sum"));
        assertFalse(bool(source, "native_execute"));
        assertTrue(Files.readString(result.evidenceDirectory().resolve("peer.stdout.raw")).contains("LIVE_PEER_END requests=11 "));
    }

    @Test
    void staleQuery() throws Exception {
        var settings = settings();
        var result = SwaySoftwarePeerConversation206.run(settings, SwayPeer206Contract.Scenario.STALE_QUERY);
        common(settings, result);
        assertEquals(SwayPeer206Contract.Scenario.STALE_QUERY, result.scenario()); assertEquals(1, result.exchanges().size());
        var exchange = result.exchanges().get(0); assertEquals("stale-query", exchange.label());
        var request = original(result, exchange);
        assertEquals(result.before().originalFrame().nativeRevision().add(BigInteger.ONE), request.expectedRevision().orElseThrow());
        assertEquals("query-active-scheme-sway-target-v1-private-" + settings.target(), request.step());
        assertFalse(exchange.originalResult().nativeOk());
        assertEquals("stale_snapshot_revision", StrictJson.text(token(exchange.originalResult().error())));
        assertArrayEquals(result.before().originalFrame().state().bytes(), result.after().originalFrame().state().bytes());
        assertFalse(Files.exists(result.evidenceDirectory().resolve("native-originals/software-opinion-transition.json")));
        assertTrue(Files.readString(result.evidenceDirectory().resolve("peer.stdout.raw")).contains("LIVE_PEER_END requests=3 "));
    }

    private static SwayPeer206Contract.Settings settings() throws Exception {
        return SwaySoftwarePeerConversation206.readSettings(Path.of(System.getProperty("xar.m6.software206.settings")));
    }
    private static void common(SwayPeer206Contract.Settings settings, SwayPeer206Contract.Result result) throws Exception {
        assertTrue(result.terminal().passed()); assertEquals(result.peer(), result.terminal().identity());
        assertEquals(0, result.terminal().accounting().activeProcesses());
        assertEquals(settings.executable().toRealPath(), Path.of(result.peer().executable()).toRealPath());
        assertEquals(result.peer().pid(), result.session().game().pid());
        assertEquals(result.peer().creationFiletimeDecimal(), result.session().game().creationFiletime().value().toString());
        for (var sample : List.of(result.before(), result.after())) {
            NativeFreshSnapshotPort.verifyOriginal(sample.acknowledgement(), sample.originalFrame(), sample.snapshotReceived());
            assertEquals(result.session(), sample.originalFrame().session());
            assertEquals(result.session(), sample.acknowledgement().custody().orElseThrow().session());
            assertEquals(BigInteger.valueOf(7), sample.originalFrame().nativeRevision());
        }
        assertNotEquals(result.before().acknowledgement().requestId(), result.after().acknowledgement().requestId());
        NativeFreshSnapshotPort.verifyAfter(result.before().acknowledgement(), result.after());
        Path dir = result.evidenceDirectory().resolve("java-original-packets");
        var hello = (NativeWire.Hello) NativeWire.decode(Files.readAllBytes(dir.resolve("hello.packet")));
        assertEquals(result.peer().pid(), hello.pid()); assertEquals(settings.bridgeVersion(), hello.bridgeVersion());
        assertEquals(settings.helloExecutableSha256().toUpperCase(java.util.Locale.ROOT), hello.gameSha256().toUpperCase(java.util.Locale.ROOT));
        assertEquals(settings.adapterId(), hello.adapterId());
        assertEquals(result.session().connectionGeneration(), hello.connectionGeneration());
        assertArrayEquals(result.after().originalFrame().originalPacket(), Files.readAllBytes(dir.resolve("after.snapshot.packet")));
        Path nativeDir = result.evidenceDirectory().resolve("native-originals");
        samePayload(hello.packet().value(), nativeDir.resolve("1.out-sent.json"));
        samePayload(result.before().acknowledgement().outbound().orElseThrow().originalPacket(), nativeDir.resolve("3.in.json"));
        samePayload(result.before().originalFrame().originalPacket(), nativeDir.resolve("4.out-sent.json"));
        samePayload(result.before().acknowledgement().originalPacket(), nativeDir.resolve("5.out-sent.json"));
        int afterOrdinal = 6 + 2 * result.exchanges().size();
        samePayload(result.after().acknowledgement().outbound().orElseThrow().originalPacket(), nativeDir.resolve(afterOrdinal + ".in.json"));
        samePayload(result.after().originalFrame().originalPacket(), nativeDir.resolve((afterOrdinal + 1) + ".out-sent.json"));
        samePayload(result.after().acknowledgement().originalPacket(), nativeDir.resolve((afterOrdinal + 2) + ".out-sent.json"));
    }
    private static NativeWire.ExecuteRequest original(SwayPeer206Contract.Result result, SwayPeer206Contract.Exchange exchange) throws Exception {
        var request = NativeWire.decodeExecuteRequest(exchange.originalRequest());
        var response = (NativeWire.CommandResult) NativeWire.decode(exchange.originalResult().packet().value());
        assertEquals(request.requestId(), response.requestId()); assertEquals(response.requestId(), exchange.originalResult().requestId());
        assertEquals(response.nativeOk(), exchange.originalResult().nativeOk());
        assertArrayEquals(response.payload().value(), exchange.originalResult().payload().value());
        assertArrayEquals(Arrays.copyOfRange(response.packet().value(), 4, response.packet().value().length), response.payload().value());
        if (response.result().token().isPresent()) assertArrayEquals(response.result().token().orElseThrow().value(), exchange.originalResult().result().token().orElseThrow().value());
        Path dir = result.evidenceDirectory().resolve("java-original-packets");
        assertArrayEquals(exchange.originalRequest(), Files.readAllBytes(dir.resolve(exchange.label() + ".outgoing.packet")));
        assertArrayEquals(response.packet().value(), Files.readAllBytes(dir.resolve(exchange.label() + ".incoming-0.packet")));
        int nativeOrdinal = 6 + 2 * result.exchanges().indexOf(exchange);
        Path nativeDir = result.evidenceDirectory().resolve("native-originals");
        samePayload(exchange.originalRequest(), nativeDir.resolve(nativeOrdinal + ".in.json"));
        samePayload(response.packet().value(), nativeDir.resolve((nativeOrdinal + 1) + ".out-sent.json"));
        return request;
    }
    private static void samePayload(byte[] packet, Path nativeOriginal) throws Exception {
        assertArrayEquals(Arrays.copyOfRange(packet, 4, packet.length), Files.readAllBytes(nativeOriginal));
    }
    private static JsonNode fields(SwayPeer206Contract.Result result, int index) throws Exception {
        return StrictJson.parse(NativeWire.decodeExecuteRequest(result.exchanges().get(index).originalRequest()).normalizedAdditionalFields().value());
    }
    private static JsonNode body(SwayPeer206Contract.Result result, int index, String field) {
        JsonNode value = token(result.exchanges().get(index).originalResult().result()).get(field);
        assertNotNull(value); assertTrue(value.isObject()); return value;
    }
    private static JsonNode token(NativeWire.Field field) { return StrictJson.parse(field.token().orElseThrow().value(), 1024 * 1024); }
    private static boolean bool(JsonNode row, String key) {
        assertNotNull(row.get(key), key); assertTrue(row.get(key).isBoolean(), key); return row.get(key).booleanValue();
    }
    private static long integer(JsonNode row, String key) { return StrictJson.integer(row.get(key), Long.MIN_VALUE, Long.MAX_VALUE); }
    private static BigInteger wide(JsonNode row, String key) { return StrictJson.integer(row.get(key), BigInteger.ZERO, NativeWire.UINT64_MAX); }
}
