package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.NativeActiveWarsCodec;

/** Actual C++ Full packets prove only empty War scope. Mutations are invalid DATA, never a positive War oracle or live permit. */
final class FlorinWarScopeCanonicalTest {
    private static final String EMPTY_SCOPE_MESSAGE =
            "Florin full-state requires an explicitly observed empty active_wars array";

    @Test void actualCppFullPacketsKeepTheirExplicitEmptyWarScopeAndOriginalBytes() throws Exception {
        for (int variant : new int[] {0, 1, 2}) {
            byte[] packet = packet(variant);
            ObjectNode original = (ObjectNode) StrictJson.parse(packet);
            assertTrue(original.path("state").path("active_wars").isArray());
            assertTrue(original.path("state").path("active_wars").isEmpty());
            ObservedFrame frame = dataFrame(packet);
            JsonNode canonical = DriverJson.parsedNode(
                    DriverObservationAssembler.canonicalNativeState(frame).semantic(), DriverJson.MAX_NATIVE_BYTES);
            assertTrue(canonical.path("active_wars").isArray());
            assertTrue(canonical.path("active_wars").isEmpty());
            assertArrayEquals(packet, Arrays.copyOfRange(frame.originalPacket(), 4, frame.originalPacket().length));
        }
    }

    @Test void missingAndNullFlorinWarDomainsCannotNormalizeIntoObservedEmpty() throws Exception {
        ObjectNode missing = state(); missing.remove("active_wars");
        rejectScope(missing);
        ObjectNode explicitNull = state(); explicitNull.putNull("active_wars");
        rejectScope(explicitNull);
    }

    @Test void malformedAndEveryNonemptyFlorinWarDomainFailBeforeTheLegacyCodec() throws Exception {
        for (String token : List.of("{}", "0", "1.0", "true", "\"[]\"", "[null]", "[{}]")) {
            ObjectNode malformed = state();
            malformed.set("active_wars", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            rejectScope(malformed);
        }
        // Deliberately synthetic positive probes: neither rich-looking legacy rows nor internal identity fields
        // are the frozen positive Florin Full producer, even when its ID happens to fit the legacy domain.
        ObjectNode richLooking = state(); richLooking.putArray("active_wars").add(legacyRow(0));
        rejectScope(richLooking);
        ObjectNode internalLooking = state();
        ObjectNode row = internalLooking.putArray("active_wars").addObject();
        row.put("war_id", -2130706431).put("actual_player_character_id", -2113929214)
                .put("player_side", "defender").put("primary_attacker_character_id", 0)
                .put("primary_defender_character_id", -2113929214)
                .put("primary_opponent_character_id", 0).put("player_is_primary_war_leader", true);
        row.putArray("attacker_participant_ids").add(0).add(0);
        row.putArray("defender_participant_ids").add(-2113929214);
        row.putNull("player_relative_war_score");
        rejectScope(internalLooking);
    }

    @Test void legacyCodecRetainsItsIndependentNullEmptyAndNonnegativeIdentityRules() {
        assertTrue(NativeActiveWarsCodec.normalize((JsonNode) null).isEmpty());
        assertTrue(NativeActiveWarsCodec.normalize(JsonNodeFactory.instance.nullNode()).isEmpty());
        assertTrue(NativeActiveWarsCodec.normalize(JsonNodeFactory.instance.arrayNode()).isEmpty());
        assertEquals(BigInteger.ZERO, NativeActiveWarsCodec.normalize(
                JsonNodeFactory.instance.arrayNode().add(legacyRow(0))).getFirst().warId());
        assertThrows(IllegalArgumentException.class, () -> NativeActiveWarsCodec.normalize(
                JsonNodeFactory.instance.arrayNode().add(legacyRow(-2))));
    }

    private static ObjectNode legacyRow(int warId) {
        return JsonNodeFactory.instance.objectNode().put("war_id", warId)
                .put("player_side", "attacker").put("player_relative_war_score", 0);
    }

    private static void rejectScope(ObjectNode root) {
        IllegalArgumentException failure = assertThrows(IllegalArgumentException.class,
                () -> DriverObservationAssembler.canonicalNativeState(mutatedData(root)));
        assertEquals(EMPTY_SCOPE_MESSAGE, failure.getMessage(),
                "the explicit Florin root must reject its War domain before legacy decoding or defaulting");
    }

    private static byte[] packet(int variant) throws IOException {
        try (InputStream input = FlorinWarScopeCanonicalTest.class.getResourceAsStream(
                "/florinarmy/full-army-producer-" + variant + ".json")) {
            assertNotNull(input, "existing actual C++ FullArmy17 packet required");
            byte[] result = input.readNBytes(8193); assertTrue(result.length <= 8192); return result;
        }
    }

    private static ObjectNode state() throws IOException { return (ObjectNode) StrictJson.parse(packet(0)).get("state"); }

    private static ObservedFrame mutatedData(ObjectNode root) {
        ObjectNode body = JsonNodeFactory.instance.objectNode().put("type", "state_snapshot")
                .put("protocol_version", 1).put("snapshot_id", "native:10").put("revision", 10);
        body.set("state", root);
        return dataFrame(org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson.encode(body));
    }

    private static ObservedFrame dataFrame(byte[] originalPacket) {
        ObjectNode body = (ObjectNode) StrictJson.parse(originalPacket);
        byte[] state = org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson.encode(body.get("state"));
        byte[] framed = ByteBuffer.allocate(originalPacket.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(originalPacket.length).put(originalPacket).array();
        var session = new TransportSession("war-scope-software-data-only", new GameGeneration(1,
                new PythonOnlyUInt64(BigInteger.ONE)), BigInteger.ONE, "war-scope-software-data-only");
        return new ObservedFrame(session, body.get("snapshot_id").textValue(), body.get("revision").bigIntegerValue(),
                new RawJson(state), framed, Instant.EPOCH);
    }
}
