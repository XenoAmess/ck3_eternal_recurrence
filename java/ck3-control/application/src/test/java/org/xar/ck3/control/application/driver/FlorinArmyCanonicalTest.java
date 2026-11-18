package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.FlorinPlayerArmies;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.nativebridge.capabilities.army.NativeArmiesCodec;

/** Actual C++ Full packets; synthetic transport identities are DATA only, never live/source/action authority. */
final class FlorinArmyCanonicalTest {
    @Test void actualCppSignedUnitAndOwnerPacketsReachThePublicCanonicalPipelineUnchanged() throws Exception {
        for (int variant : new int[] {0, 1}) {
            byte[] original = packet(variant);
            ObjectNode body = (ObjectNode) StrictJson.parse(original);
            ObservedFrame frame = dataFrame(original);
            JsonNode canonical = DriverJson.parsedNode(DriverObservationAssembler.canonicalNativeState(frame).semantic(), DriverJson.MAX_NATIVE_BYTES);
            JsonNode army = canonical.path("player_armies").get(0);
            assertEquals(-2080374784, army.path("army_id").intValue());
            assertEquals(variant == 0 ? 1 : -2130706431, army.path("owner_character_id").intValue());
            assertEquals(body.path("state").path("played_character").path("character_id").intValue(),
                    canonical.path("played_character").path("character_id").intValue());
            assertEquals(StrictJson.parse("[1,2]".getBytes(java.nio.charset.StandardCharsets.UTF_8)), army.path("route_province_ids"));
            assertEquals("complete_nonempty", army.path("route_read_status").textValue());
            assertEquals(2, army.path("route_source_count").intValue());
            assertEquals(2, army.path("move_target_province_id").intValue());
            assertTrue(army.path("move_target_observable").booleanValue());
            assertEquals("moving", army.path("army_state").textValue());
            assertEquals(7, army.path("army_state_code").intValue());
            assertTrue(army.get("soldiers").isNull());
            for (String key : List.of("siege_days_left", "siege_province_holder_character_id", "siege_province_in_player_subrealm"))
                assertTrue(army.has(key) && army.get(key).isNull());
            assertArrayEquals(original, unframe(frame.originalPacket()));
            assertArrayEquals(DriverJson.encode(DriverJson.fromNode(body.get("state"))), frame.state().bytes());
        }
    }

    @Test void actualCppZeroUnitAndNoArmyFallbackKeepCompleteEmptyRouteAndUnknownSidecars() throws Exception {
        JsonNode canonical = DriverJson.parsedNode(DriverObservationAssembler.canonicalNativeState(dataFrame(packet(2))).semantic(), DriverJson.MAX_NATIVE_BYTES);
        JsonNode army = canonical.path("player_armies").get(0);
        assertEquals(0, army.path("army_id").intValue());
        assertEquals(1, army.path("army_state_code").intValue());
        assertEquals("regular", army.path("army_state").textValue());
        assertEquals("complete_empty", army.path("route_read_status").textValue());
        assertEquals(0, army.path("route_source_count").intValue());
        assertTrue(army.path("route_province_ids").isArray() && army.path("route_province_ids").isEmpty());
        assertFalse(army.path("move_target_observable").booleanValue());
        assertTrue(army.get("move_target_province_id").isNull());
        assertTrue(army.get("soldiers").isNull());
        assertTrue(canonical.path("active_wars").isEmpty());
    }

    @Test void explicitRootIdentitySelectsFlorinAndCannotBroadenLegacyUnitOrOwnerDomains() throws Exception {
        ObjectNode root = state(0);
        assertTrue(FlorinPlayerArmies.selects(root));
        assertThrows(IllegalArgumentException.class, () -> NativeArmiesCodec.normalize(root.get("player_armies")));
        assertThrows(IllegalArgumentException.class, () -> new ArmyTypes.PublicUnitId(-2080374784));
        assertEquals(0, new ArmyTypes.PublicUnitId(0).value());
        ObjectNode row = army(root); row.put("army_id", 1); row.put("owner_character_id", -2130706431);
        assertThrows(IllegalArgumentException.class, () -> NativeArmiesCodec.normalize(root.get("player_armies")));
        for (String key : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend")) {
            ObjectNode wrong = state(0); wrong.put(key, "wrong");
            assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(wrong), key);
        }
        ObjectNode noMarker = state(0); noMarker.remove("schema");
        assertFalse(FlorinPlayerArmies.selects(noMarker));
        assertThrows(IllegalArgumentException.class, () -> DriverObservationAssembler.canonicalNativeState(mutatedData(noMarker)));
    }

    @Test void signedIntegerIdentityTokensRejectSentinelsNarrowingAndOwnerDrift() throws Exception {
        for (String token : List.of("-1", "2147483648", "-2147483649", "true", "1.0", "\"1\"", "null")) {
            for (String key : List.of("army_id", "owner_character_id")) {
                ObjectNode root = state(0); army(root).set(key, StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(root), key + token);
            }
        }
        ObjectNode changedOwner = state(0); army(changedOwner).put("owner_character_id", 2);
        assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(changedOwner));
        ObjectNode sameIndexDifferentGeneration = state(0); ObjectNode second = army(sameIndexDifferentGeneration).deepCopy();
        second.put("army_id", -2063597568);
        ((ArrayNode) sameIndexDifferentGeneration.get("player_armies")).add(second);
        JsonNode result = FlorinPlayerArmies.normalize(sameIndexDifferentGeneration);
        assertEquals(2, result.size());
        assertEquals(-2080374784, result.get(0).path("army_id").intValue());
        assertEquals(-2063597568, result.get(1).path("army_id").intValue());
        second.put("army_id", -2080374784);
        assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(sameIndexDifferentGeneration));
    }

    @Test void routeAndNativeStateContradictionsCannotBecomeACompleteObservedBase() throws Exception {
        for (String field : List.of("route_source_count", "move_target_observable", "move_target_province_id")) {
            ObjectNode root = state(2);
            if (field.equals("route_source_count")) army(root).put(field, 1);
            else if (field.equals("move_target_observable")) army(root).put(field, true);
            else army(root).put(field, 2);
            assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(root), field);
        }
        ObjectNode badTarget = state(0); army(badTarget).put("move_target_province_id", 1);
        assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(badTarget));
        ObjectNode badState = state(0); army(badState).put("army_state", "regular");
        assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(badState));
        ObjectNode badCombat = state(0); army(badCombat).put("in_combat", true);
        assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(badCombat));
        ObjectNode soldiers = state(0); army(soldiers).put("soldiers", 0);
        assertThrows(IllegalArgumentException.class, () -> FlorinPlayerArmies.normalize(soldiers));
    }

    private static byte[] packet(int variant) throws IOException {
        try (InputStream input = FlorinArmyCanonicalTest.class.getResourceAsStream("/florinarmy/full-army-producer-" + variant + ".json")) {
            assertNotNull(input, "actual original C++ full packet required");
            byte[] result = input.readNBytes(8193); assertTrue(result.length <= 8192); return result;
        }
    }
    private static ObjectNode state(int variant) throws IOException { return (ObjectNode) StrictJson.parse(packet(variant)).get("state"); }
    private static ObjectNode army(ObjectNode root) { return (ObjectNode) root.path("player_armies").get(0); }
    private static ObservedFrame mutatedData(ObjectNode root) {
        ObjectNode body = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
        body.put("type", "state_snapshot"); body.put("protocol_version", 1); body.put("snapshot_id", "native:10");
        body.put("revision", 10); body.set("state", root);
        return dataFrame(DriverJson.encode(DriverJson.fromNode(body)));
    }
    private static ObservedFrame dataFrame(byte[] originalPacket) {
        ObjectNode body = (ObjectNode) StrictJson.parse(originalPacket);
        BigInteger revision = body.get("revision").bigIntegerValue();
        byte[] state = DriverJson.encode(DriverJson.fromNode(body.get("state")));
        byte[] framed = ByteBuffer.allocate(originalPacket.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(originalPacket.length).put(originalPacket).array();
        var session = new TransportSession("software-cpp-data-only", new GameGeneration(1,
                new PythonOnlyUInt64(BigInteger.ONE)), BigInteger.ONE, "software-cpp-data-only");
        return new ObservedFrame(session, body.get("snapshot_id").textValue(), revision, new RawJson(state), framed, Instant.EPOCH);
    }
    private static byte[] unframe(byte[] packet) { return java.util.Arrays.copyOfRange(packet, 4, packet.length); }
}
