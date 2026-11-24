package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Exact self-owned C++ software originals, never a live exchange or business proof. */
class NativeCurrentLivingInventory26785313ProducerTest {
    static final BigInteger MAX_U64 = new BigInteger("18446744073709551615");
    static byte[] original(String family, String name, int size, String sha) throws Exception {
        try (var in = NativeCurrentLivingInventory26785313ProducerTest.class.getResourceAsStream(
                "/current267-living-" + family + "-cpp-a03/" + name)) {
            if (in == null) throw new IOException("Original C++ resource absent: " + name);
            byte[] bytes = in.readAllBytes(); assertEquals(size, bytes.length, name);
            assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), name);
            return bytes;
        }
    }
    static ObjectNode envelope(byte[] raw) throws IOException { return NativeWire.object(NativeWire.parse(raw)); }
    static RawJson result(byte[] raw) throws IOException {
        var outer = StrictJson.object(envelope(raw), Set.of("type", "protocol_version", "request_id", "ok", "result"));
        assertEquals("command_result", outer.get("type").textValue());
        assertEquals(1, outer.get("protocol_version").intValue());
        assertTrue(outer.get("request_id").isTextual()); assertTrue(outer.get("ok").isBoolean());
        assertEquals(22, outer.get("result").size());
        assertArrayEquals(raw, Arrays.copyOfRange(NativeWire.packet(raw), 4, raw.length + 4));
        return new RawJson(NativeWire.token(raw, "result"));
    }
    static void responseIdentity(byte[] raw, RawJson encoded, boolean success) throws IOException {
        var outer = envelope(raw); var original = NativeWire.object(outer.get("result"));
        var regenerated = NativeWire.object(NativeWire.parse(encoded.bytes()));
        assertEquals(original, regenerated); assertEquals(outer.get("ok").booleanValue(), success);
        for (String key : List.of("native_handled", "new_date_observed", "physical_save_confirmed"))
            assertFalse(original.get(key).booleanValue(), key);
        assertTrue(original.get("addresses_redacted").booleanValue());
    }
    static CoreFrame.Partial core(ObjectNode claim) throws IOException {
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                CurrentLivingEntry.readCore(claim.get("expected_core")));
    }
    static void factory(String family, ObjectNode original, NativeRequest request, byte[] packet) throws Exception {
        assertEquals(8, original.size());
        assertEquals("execute_step", original.get("type").textValue());
        assertEquals(1, original.get("protocol_version").intValue());
        assertEquals(original.get("step").textValue(), request.step());
        int length = ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        assertEquals(packet.length - 4, length);
        byte[] body = Arrays.copyOfRange(packet, 4, packet.length);
        assertArrayEquals(packet, NativeWire.packet(body));
        var actual = envelope(body); var comparable = actual.deepCopy();
        ObjectNode actualClaim = NativeWire.object(family.equals("inventory") ? comparable.get("living_inventory")
                : comparable.get("arguments").get("living_" + family));
        ObjectNode expectedClaim = NativeWire.object(family.equals("inventory") ? original.get("living_inventory")
                : original.get("arguments").get("living_" + family));
        assertEquals(expectedClaim.get("executable_sha256").textValue().toLowerCase(java.util.Locale.ROOT),
                actualClaim.get("executable_sha256").textValue().toLowerCase(java.util.Locale.ROOT));
        actualClaim.set("executable_sha256", expectedClaim.get("executable_sha256"));
        assertEquals(original, comparable, "Only legal executable-hash casing may differ from the original request");
        var decoded = NativeWire.decodeExecuteRequest(packet);
        assertEquals(original.get("request_id").textValue(), decoded.requestId());
        assertEquals(request.step(), decoded.step()); assertTrue(decoded.expectedSnapshotRevision().isEmpty());
        if (family.equals("inventory")) assertEquals(BigInteger.ZERO, decoded.expectedRevision().orElseThrow());
        else { assertTrue(decoded.expectedRevision().isEmpty()); assertEquals("local_player", actual.get("actor").textValue()); }
        String deadline = family.equals("inventory") ? "core_control_deadline_unix_ms" : "deadline_unix_ms";
        assertTrue(actual.get(deadline).isIntegralNumber()); assertEquals(MAX_U64, actual.get(deadline).bigIntegerValue());
        String out = System.getProperty("xar.living.java.requests.output.directory");
        if (out != null) {
            Path dir = Path.of(out); Files.createDirectories(dir);
            String stem = "java-" + family + "-" + expectedClaim.get("action").textValue();
            Files.write(dir.resolve(stem + ".body.json"), body, StandardOpenOption.CREATE_NEW);
            Files.write(dir.resolve(stem + ".packet.bin"), packet, StandardOpenOption.CREATE_NEW);
        }
    }
    private static byte[] raw(String name) throws Exception {
        return switch (name) {
            case "original-inventory-query.body.json" -> original("inventory", name, 700, "eb0ffbaaceeff5ad5bbe9514e9d849b78907907d8316b24b5c83138a7c912dff");
            case "response-inventory-available.body.json" -> original("inventory", name, 2031, "e1bb3a0c4011c2197355d34a693bf6e49d97b2685c76d5985af1c0b469470732");
            case "response-inventory-unavailable.body.json" -> original("inventory", name, 1009, "1bb37b25e4c37cc86e0c809be2a64f502575bb0bffbea331d78c743a99fda87b");
            case "response-inventory-unknown.body.json" -> original("inventory", name, 1016, "f5c8d53cef67c0efc8b99605b912a9d5182082ae53d0dfe3c218a13e666ef5f1");
            default -> throw new IllegalArgumentException("Unknown original resource: " + name);
        };
    }

    @Test void originalAvailablePreservesCompleteInventoryPhysicalIdsAndFourRawValues() throws Exception {
        byte[] raw = raw("response-inventory-available.body.json");
        var frame = CurrentLivingInventoryQueryResult.decode(result(raw));
        assertEquals(frame, CurrentLivingInventoryQueryResult.decode(frame.encode()));
        responseIdentity(raw, frame.encode(), frame.successful());
        var source = frame.source().orElseThrow(); assertEquals(0L, source.actorFullId());
        assertEquals(100000L, source.numericDenominator()); assertTrue(source.completeInventory()); assertTrue(source.sampledTwice());
        assertEquals(1, source.artifacts().size()); var artifact = source.artifacts().get(0);
        assertEquals(0L, artifact.fullId()); assertEquals(0L, artifact.ownerFullId()); assertEquals("sword", artifact.typeKey());
        assertFalse(artifact.equipped()); assertEquals(4, artifact.numeric().size());
        for (var numeric : artifact.numeric()) { assertEquals(CurrentLivingInventoryQuerySource.NumericState.NUMERIC, numeric.state());
            assertEquals(1, numeric.scopeKind()); assertEquals(0L, numeric.raw().orElseThrow().longValue()); }
        assertEquals(6, source.fixedReferences().size()); assertEquals(0L, source.fixedReferences().get(0).artifactFullId().orElseThrow().longValue());
        assertEquals(0, source.weaponSlot().orElseThrow().intValue()); assertTrue(source.slots().get(0).artifactFullId().isEmpty());
        assertFalse(frame.effectAttempted()); assertFalse(frame.nativeReturned()); assertEquals(BigInteger.ZERO, frame.claimSequence());
    }
    @Test void originalUnavailableIsSourceNullWithoutAnInformationalQueryIdentity() throws Exception {
        byte[] raw = raw("response-inventory-unavailable.body.json"); var frame = CurrentLivingInventoryQueryResult.decode(result(raw));
        assertEquals(frame, CurrentLivingInventoryQueryResult.decode(frame.encode())); responseIdentity(raw, frame.encode(), frame.successful());
        assertEquals(CurrentLivingInventoryQueryResult.Status.UNAVAILABLE, frame.status()); assertTrue(frame.cleanupKnown());
        assertTrue(frame.source().isEmpty()); assertEquals(BigInteger.ZERO, frame.providerGeneration());
        assertEquals(BigInteger.ZERO, frame.querySequence()); assertFalse(frame.unavailableReason().orElseThrow().isEmpty());
    }
    @Test void originalCleanupUnknownStaysIndeterminateAndCannotGrantInventoryAuthority() throws Exception {
        byte[] raw = raw("response-inventory-unknown.body.json"); var frame = CurrentLivingInventoryQueryResult.decode(result(raw));
        assertEquals(frame, CurrentLivingInventoryQueryResult.decode(frame.encode())); responseIdentity(raw, frame.encode(), frame.successful());
        assertEquals(CurrentLivingInventoryQueryResult.Status.INDETERMINATE, frame.status()); assertFalse(frame.cleanupKnown());
        assertTrue(frame.source().isEmpty()); assertFalse(frame.effectAttempted()); assertEquals(BigInteger.ZERO, frame.claimSequence());
    }
    @Test void originalInventoryFactoryExercisesLegacyEnvelopeAndMaximumOriginalDeadline() throws Exception {
        var original = StrictJson.object(envelope(raw("original-inventory-query.body.json")), Set.of("type", "protocol_version",
                "request_id", "step", "expected_revision", "arguments", "living_inventory", "core_control_deadline_unix_ms"));
        var claim = NativeWire.object(original.get("living_inventory")); assertEquals(7, claim.size());
        var request = CurrentLivingInventoryQuery.request(core(claim));
        assertEquals(CurrentLivingInventoryQuery.CAPABILITY, request.requiredCapability().orElseThrow());
        var fields = NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));
        fields.put("core_control_deadline_unix_ms", original.get("core_control_deadline_unix_ms").bigIntegerValue());
        factory("inventory", original, request, NativeWire.execute(original.get("request_id").textValue(), request.step(),
                BigInteger.ZERO, StrictJson.canonical(fields)));
    }
}
