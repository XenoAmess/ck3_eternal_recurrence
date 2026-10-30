package org.xar.ck3.control.wave2.finance.factionthreat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatObserver.*;

/** Actual Native .4 reader/serializer rows; software selection context grants no submit. */
final class FactionThreatNativeCharacterConsumerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final ExistingAlertReader HISTORY_ONLY = new ExistingAlertReader() {
        @Override public boolean supportsExistingObserver() { throw new AssertionError("must reuse original history DATA"); }
        @Override public ReadResult readExistingObserver(BigInteger revision) { throw new AssertionError("no Native call or mutation"); }
    };

    @Test
    void actualSignedNativeMemberRetainsSignedPublicIdAndExactNativeRow() throws IOException {
        assertNativeCase("signed-negative-member", -2147483646);
    }

    @Test
    void actualZeroNativeMemberRemainsPresentRatherThanAbsent() throws IOException {
        assertNativeCase("zero-member", 0);
    }

    @Test
    void authoredSignedAndZeroActorsUseTheSamePublicContract() throws IOException {
        for (int actor : new int[]{Integer.MIN_VALUE, -2147483646, 0, Integer.MAX_VALUE}) {
            ObjectNode request = request(nativeCase("positive-leader-member"));
            ((ObjectNode)request.path("snapshot").path("played_character")).put("character_id", actor);
            ObjectNode alert = alert(request);
            alert.put("player_character_id", actor);
            ((ObjectNode)alert.path("targeting_factions").get(0)).put("target_character_id", actor);
            Observed actual = assertInstanceOf(Observed.class, observe(FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request)), HISTORY_ONLY));
            assertEquals(BigInteger.valueOf(actor), actual.frame().playerCharacterId());
            assertTrue(actual.dangerousResponseReady());
        }
    }

    @Test
    void absentAndWrongTokenOrUnsignedAliasNeverBecomePublicCharacterIds() throws IOException {
        for (String token : List.of("-1", "2147483650", "4294967295", "-2147483649", "true", "0.0", "\"0\"")) {
            JsonNode invalid = JSON.readTree(token);
            for (String path : List.of("choice", "snapshot", "frame", "target", "leader", "member")) {
                ObjectNode request = request(nativeCase("positive-leader-member"));
                ObjectNode row = (ObjectNode)alert(request).path("targeting_factions").get(0);
                switch (path) {
                    case "choice" -> ((ObjectNode)request.path("candidate").path("choice")).set("recipient_character_id", invalid);
                    case "snapshot" -> ((ObjectNode)request.path("snapshot").path("played_character")).set("character_id", invalid);
                    case "frame" -> alert(request).set("player_character_id", invalid);
                    case "target" -> row.set("target_character_id", invalid);
                    case "leader" -> row.set("leader_character_id", invalid);
                    case "member" -> row.putArray("character_member_ids").add(invalid);
                    default -> throw new AssertionError(path);
                }
                assertThrows(IllegalArgumentException.class, () -> FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request)), path + "=" + token);
            }
        }
    }

    @Test
    void optionalNullOrMissingRoleStaysAbsentAndFactionIdsStayPositive() throws IOException {
        ObjectNode original = (ObjectNode)nativeCase("positive-leader-member").path("alerts_receipt").deepCopy();
        ObjectNode row = (ObjectNode)original.path("targeting_factions").get(0);
        row.putNull("leader_character_id");
        row.remove("target_character_id");
        ObjectNode result = JSON.createObjectNode();
        result.set("player_faction_alerts", original);
        Alert projected = FactionThreatCodec.decodeExistingObserverResult(JSON.writeValueAsBytes(result));
        assertTrue(projected.targetingRows().getFirst().leaderId().isEmpty());
        assertTrue(projected.targetingRows().getFirst().targetId().isEmpty());
        for (long invalid : new long[]{-2147483646L, -1L, 0L, 4294967296L}) {
            ObjectNode request = request(nativeCase("positive-leader-member"));
            ((ObjectNode)request.path("candidate").path("choice")).put("source_faction_id", invalid);
            assertThrows(IllegalArgumentException.class, () -> FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request)));
        }
    }

    @Test
    void publicRecordConstructorsPreserveCharacterDomainWithoutSubmitAuthority() {
        for (int id : new int[]{Integer.MIN_VALUE, -2147483646, 0, Integer.MAX_VALUE}) {
            assertEquals(BigInteger.valueOf(id), new SelectedGift(BigInteger.ONE, BigInteger.valueOf(id)).recipientCharacterId());
            assertEquals(BigInteger.valueOf(id), new Frame(BigInteger.ONE, 53169072, BigInteger.valueOf(id)).playerCharacterId());
        }
        for (long id : new long[]{-1L, -2147483649L, 2147483648L, 4294967295L}) {
            assertThrows(IllegalArgumentException.class, () -> new SelectedGift(BigInteger.ONE, BigInteger.valueOf(id)));
            assertThrows(IllegalArgumentException.class, () -> new Frame(BigInteger.ONE, 53169072, BigInteger.valueOf(id)));
        }
    }

    private static void assertNativeCase(String name, int signed) throws IOException {
        JsonNode vector = nativeCase(name);
        assertTrue(vector.path("actual_available").booleanValue());
        assertTrue(vector.path("actual_select").booleanValue());
        assertEquals(Integer.toUnsignedLong(signed), vector.path("recipient_raw_bits").longValue());
        ObjectNode request = request(vector);
        Observed actual = assertInstanceOf(Observed.class, observe(FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request)), HISTORY_ONLY));
        assertEquals(BigInteger.valueOf(signed), actual.gift().recipientCharacterId());
        assertEquals(vector.path("alerts_receipt").path("targeting_factions").get(0), JSON.readTree(actual.nativeRow().originalJson()));
        JsonNode wire = JSON.readTree(FactionThreatCodec.encode(actual));
        assertEquals(signed, wire.path("recipient_character_id").intValue());
        assertTrue(wire.path("recipient_character_id").isIntegralNumber());
        assertTrue(wire.path("dangerous_response_ready").booleanValue());
        assertFalse(wire.path("exact_ultimatum_timing_ready").booleanValue());
        assertEquals("not_inferred", wire.path("faction_departure_or_threat_resolution").textValue());
        assertFalse(wire.has("gift_submission_enabled"));
    }

    private static ObjectNode request(JsonNode vector) {
        JsonNode receipt = vector.path("alerts_receipt");
        ObjectNode request = JSON.createObjectNode();
        ObjectNode snapshot = request.putObject("snapshot");
        snapshot.set("native_revision", receipt.get("snapshot_revision"));
        snapshot.set("date_raw", receipt.get("date_raw"));
        snapshot.putObject("played_character").set("character_id", receipt.get("player_character_id"));
        ObjectNode candidate = request.putObject("candidate");
        candidate.put("status", "selected");
        ObjectNode choice = candidate.putObject("choice");
        choice.set("source_faction_id", vector.get("source_faction_id"));
        choice.set("recipient_character_id", vector.get("requested_member_id"));
        request.set("expected_revision", receipt.get("snapshot_revision"));
        request.putArray("history").addObject().put("command", STEP).put("ok", true)
                .putObject("result").set("player_faction_alerts", receipt.deepCopy());
        return request;
    }

    private static ObjectNode alert(ObjectNode request) {
        return (ObjectNode)request.path("history").get(0).path("result").path("player_faction_alerts");
    }

    private static JsonNode nativeCase(String name) throws IOException {
        try (InputStream input = FactionThreatNativeCharacterConsumerTest.class.getResourceAsStream("/factionthreat/native-member-selection-md-v1.json")) {
            assertNotNull(input, "actual Native reader/serializer fixture required");
            JsonNode root = JSON.readTree(input);
            assertEquals("xenoamess-full-tower-eb9d2c1186", root.path("machine_id").textValue());
            for (JsonNode vector : root.path("cases")) if (name.equals(vector.path("case").textValue())) return vector;
            throw new IllegalArgumentException("missing actual Native case " + name);
        }
    }
}
