package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original C++ NoGame software DATA. Samples are not actual popup identities or a Transport exchange. */
final class NativeCurrentRmtmPostSuccessionEvent26785313ProducerTest {
    private record Original(String name, int bytes, String sha256) { }
    private static final List<Original> ORIGINALS = List.of(
            new Original("post-query.original.json", 1987, "ea5f10eff5b765123834262abf150c74cdf0c2e8fda1e4b34d7ea5bc1015020a"),
            new Original("post-dispatched.original.json", 2019, "076e491f035090bad8bfd1508b81a25116631feb53e62d5491d6660e6e0d5ebc"),
            new Original("post-unknown.original.json", 1116, "2532766b28f3296c82bee4372da6bbd7f415aac37bdb095d84e1b02e0a96556a"),
            new Original("post-select-original.body.json", 819, "34034d5cf2119a80588046f2bb5de885d38fcbe21c333e2d3146399faf8ebd66"));
    private static byte[] raw(String name) throws Exception {
        var original = ORIGINALS.stream().filter(row -> row.name().equals(name)).findFirst().orElseThrow();
        try (var in = NativeCurrentRmtmPostSuccessionEvent26785313ProducerTest.class.getResourceAsStream("/current267-rmtm-post-event-cpp-a01/" + name)) {
            if (in == null) throw new IOException("Original post-succession C++ resource absent");
            byte[] bytes = in.readAllBytes();
            assertEquals(original.bytes(), bytes.length, name);
            assertEquals(original.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), name);
            return bytes;
        }
    }
    private static ObjectNode envelope(String name) throws Exception {
        return StrictJson.object(NativeWire.parse(raw(name)), Set.of("type", "protocol_version", "request_id", "ok", "result"));
    }
    private static CurrentRmtmEventResult frame(String name) throws Exception {
        var e = envelope(name); assertEquals("command_result", e.get("type").textValue());
        assertEquals(BigInteger.ONE, e.get("protocol_version").bigIntegerValue());
        var result = CurrentRmtmEventResult.decode(new RawJson(NativeWire.token(raw(name), "result")));
        assertEquals(e.get("ok").booleanValue(), result.successful());
        assertEquals(result, CurrentRmtmEventResult.decode(result.encode()));
        assertEquals(24, NativeWire.parse(result.encode().bytes()).size());
        if (result.source().isPresent()) {
            var source = result.source().orElseThrow(); assertEquals(6, source.encode().size());
            assertEquals(source, CurrentRmtmEventSource.decode(source.encode()));
        }
        return result;
    }

    @Test void originalQueryDecodesCompleteUnfamiliarCensusWithoutBorrowingFixedAckPermission() throws Exception {
        var result = frame("post-query.original.json");
        assertEquals(CurrentRmtmEvent.Action.QUERY_SUMMARY, result.action());
        assertEquals(CurrentRmtmEventResult.Status.AVAILABLE, result.status());
        assertEquals(BigInteger.ZERO, result.claimSequence()); assertFalse(result.effectAttempted());
        var source = result.source().orElseThrow(); assertTrue(source.caseBound());
        assertFalse(source.ackAdmissible()); assertTrue(source.fixedInstanceId().isEmpty());
        var choice = CurrentRmtmEvent.postSuccessionChoice(source, result.factsBefore().orElseThrow().playedCharacterId(), 41).orElseThrow();
        assertEquals(41, choice.instanceId()); assertEquals(1, choice.authoredOptionIndex());
        assertEquals(2, source.eventCensus().events().get(0).options().get(0).authoredOptionIndex());
        assertEquals("test_unfamiliar.1", source.eventCensus().events().get(0).definitionKey()); // Only this NoGame sample, not the actual blocker.
    }

    @Test void originalDispatchPreservesImmutableBeforeSourceAndAllBusinessFlagsRemainFalse() throws Exception {
        var result = frame("post-dispatched.original.json");
        assertEquals(CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE, result.action());
        assertEquals(CurrentRmtmEventResult.Status.SELECTION_DISPATCHED, result.status());
        assertTrue(result.effectAttempted()); assertTrue(result.nativeReturned()); assertTrue(result.cleanupKnown());
        assertEquals(BigInteger.ONE, result.claimSequence()); assertEquals(Optional.of(41), result.instanceId());
        assertEquals(frame("post-query.original.json").source(), result.source());
        assertFalse(result.source().orElseThrow().ackAdmissible()); assertFalse(result.nativeHandled());
        assertFalse(result.eventClosed()); assertFalse(result.newDateObserved()); assertFalse(result.physicalSaveConfirmed());
        assertNotEquals("rmtm-post-original-select-01", envelope("post-dispatched.original.json").get("request_id").textValue());
        // These independent producer IDs are not paired into a real request/response exchange.
    }

    @Test void originalUnknownRetainsEnteredClaimAndStickyUnknownCleanupWithoutSource() throws Exception {
        var result = frame("post-unknown.original.json");
        assertEquals(CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE, result.action());
        assertEquals(CurrentRmtmEventResult.Status.INDETERMINATE, result.status());
        assertFalse(result.successful()); assertTrue(result.effectAttempted()); assertFalse(result.nativeReturned());
        assertFalse(result.cleanupKnown()); assertTrue(result.source().isEmpty());
        assertEquals(BigInteger.valueOf(7), result.providerGeneration()); assertEquals(BigInteger.valueOf(9), result.querySequence());
        assertEquals(BigInteger.ONE, result.claimSequence()); assertEquals(Optional.of(41), result.instanceId());
        assertEquals("explicit_NoGame_partial_choice_UNKNOWN", result.unavailableReason().orElseThrow());
    }

    @Test void actualFactoryPreservesOriginalIdMaxDeadlineAndNativeWireLengthPrefix() throws Exception {
        var original = StrictJson.object(NativeWire.parse(raw("post-select-original.body.json")), Set.of("type", "protocol_version",
                "request_id", "step", "expected_revision", "arguments", "rmtm_event", "core_control_deadline_unix_ms"));
        var claim = StrictJson.object(original.get("rmtm_event"), Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                "backend", "action", "expected_core", "provider_generation", "query_sequence", "instance_id"));
        var actual = new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313, CurrentRmtmActorTransition.readCore(claim.get("expected_core")));
        var action = CurrentRmtmEvent.Action.parse(claim.get("action").textValue());
        assertEquals(CurrentRmtmEvent.Action.CHOOSE_POST_SUCCESSION_FIRST_AVAILABLE, action);
        var request = CurrentRmtmEvent.request(actual, action,
                NativeWire.integer(claim.get("provider_generation"), BigInteger.ONE, NativeWire.UINT64_MAX),
                NativeWire.integer(claim.get("query_sequence"), BigInteger.ONE, NativeWire.UINT64_MAX),
                Optional.of(CurrentRmtmEvent.i32(claim.get("instance_id"))));
        assertEquals(original.get("step").textValue(), request.step()); assertEquals(Optional.of(action.capability()), request.requiredCapability());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "rmtm_event"));
        var generatedClaim = NativeWire.object(fields.get("rmtm_event"));
        assertEquals(10, generatedClaim.size()); assertTrue(generatedClaim.get("provider_generation").isIntegralNumber());
        assertTrue(generatedClaim.get("query_sequence").isIntegralNumber()); assertEquals(0, fields.get("arguments").size());
        var normalized = generatedClaim.deepCopy();
        assertEquals(claim.get("executable_sha256").textValue().toUpperCase(Locale.ROOT), normalized.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
        normalized.set("executable_sha256", claim.get("executable_sha256")); assertEquals(claim, normalized); // Legal hash case only.
        assertEquals("rmtm-post-original-select-01", original.get("request_id").textValue());
        assertEquals(NativeWire.UINT64_MAX, original.get("core_control_deadline_unix_ms").bigIntegerValue());
        fields.set("core_control_deadline_unix_ms", original.get("core_control_deadline_unix_ms"));
        byte[] packet = NativeWire.execute(original.get("request_id").textValue(), request.step(),
                original.get("expected_revision").bigIntegerValue(), StrictJson.canonical(fields));
        assertEquals(packet.length - 4, ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        byte[] body = Arrays.copyOfRange(packet, 4, packet.length);
        var decoded = NativeWire.decodeExecuteRequest(packet);
        assertEquals(original.get("request_id").textValue(), decoded.requestId()); assertEquals(request.step(), decoded.step());
        assertEquals(BigInteger.ZERO, decoded.expectedRevision().orElseThrow());
        var expected = original.deepCopy(); ((ObjectNode) expected.get("rmtm_event")).set("executable_sha256", generatedClaim.get("executable_sha256"));
        assertEquals(expected, NativeWire.parse(body)); assertArrayEquals(packet, NativeWire.packet(body));
        String directory = System.getProperty("xar.rmtm.post.java.requests.output.directory");
        if (directory != null) {
            assertFalse(directory.isBlank()); var output = Path.of(directory).toAbsolutePath(); Files.createDirectories(output);
            assertFalse(Files.isSymbolicLink(output));
            Files.write(output.resolve("java-post-select.body.json"), body, StandardOpenOption.CREATE_NEW);
            Files.write(output.resolve("java-post-select.packet.bin"), packet, StandardOpenOption.CREATE_NEW);
        }
    }
}
