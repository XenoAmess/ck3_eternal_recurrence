package org.xar.ck3.control.wave3.planning.warpriorityfocus;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

import static org.junit.jupiter.api.Assertions.*;

final class WarCashFocusProjectionTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void originalCompleteProducerProjectionMatchesEveryGoldenAndRoundtrips() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.war-cash-focus.golden.v1", golden.path("schema").textValue());
        assertEquals("projection_not_original_priority_receipt", golden.path("scope").textValue());
        assertEquals(0, golden.path("producer_exit_code").intValue());
        assertFalse(golden.path("machine_id").textValue().isBlank());
        assertEquals("d9f32c208fa47a0b2007f4a5194462a9929fac2f636c8e58ba25a8cffb1a089c",
                golden.path("producer_refs").get(0).path("sha256").textValue());
        int cases = 0;
        for (JsonNode sample : golden.get("cases")) {
            byte[] wire = bytes(sample.get("request_json").textValue());
            WarCashFocusProjectionCodec.Request request = WarCashFocusProjectionCodec.decode(wire);
            Optional<WarCashFocusProjection.FocusedWar> result = WarCashFocusProjection.observe(request);
            assertEquals(sample.get("expected_result"), StrictJson.parse(WarCashFocusProjectionCodec.encode(result), 4_096), sample.path("name").textValue());
            assertEquals(result, WarCashFocusProjectionCodec.decodeResult(WarCashFocusProjectionCodec.encode(result)));
            assertArrayEquals(wire, WarCashFocusProjectionCodec.encodeRequest(request));
            assertEquals(result, WarCashFocusProjection.observe(WarCashFocusProjectionCodec.decode(WarCashFocusProjectionCodec.encodeRequest(request))));
            cases++;
        }
        assertEquals(18, cases);
    }

    @Test
    void integerIdentityAndCountsRejectBooleanFloatStringTokensWithoutNormalizing() throws IOException {
        String source = sample("primary-title-loss-and-deficit").path("request_json").textValue();
        for (String key : new String[]{"war_id", "revision", "army_id", "soldiers", "player_relative_war_score", "title_id"}) {
            String needle = switch (key) {
                case "war_id" -> "\"war_id\":99";
                case "revision" -> "\"revision\":7";
                case "army_id" -> "\"army_id\":1";
                case "soldiers" -> "\"soldiers\":800";
                case "title_id" -> "\"title_id\":2230";
                default -> "\"player_relative_war_score\":-40";
            };
            for (String token : new String[]{"true", "1.0", "\"1\""}) {
                assertTrue(source.contains(needle));
                byte[] raw = bytes(source.replace(needle, "\"" + key + "\":" + token));
                assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(raw), key + ":" + token);
            }
        }
    }

    @Test
    void missingRequiredFieldsAndCallerSuppliedGreenAreRejected() throws IOException {
        for (String field : new String[]{"schema", "snapshot", "campaign_root"}) {
            ObjectNode request = request("primary-title-loss-and-deficit"); request.remove(field);
            byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(raw));
        }
        for (String field : new String[]{"active_wars", "snapshot_id", "revision"}) {
            ObjectNode request = request("primary-title-loss-and-deficit"); ((ObjectNode) request.get("snapshot")).remove(field);
            byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(raw));
        }
        ObjectNode request = request("primary-title-loss-and-deficit"); request.put("political_ready_green", true);
        byte[] raw = JSON.writeValueAsBytes(request);
        assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(raw));
    }

    @Test
    void unknownStrengthNeverBecomesZeroAndKnownEmptyRemainsZero() throws IOException {
        WarCashFocusProjection.FocusedWar unknown = observe(request("unknown-own-count-is-not-zero")).orElseThrow();
        assertTrue(unknown.observedPlayerRaisedSoldiers().isEmpty());
        ObjectNode missing = request("primary-title-loss-and-deficit"); ((ObjectNode) missing.get("snapshot")).remove("player_armies");
        assertTrue(observe(missing).orElseThrow().observedPlayerRaisedSoldiers().isEmpty());
        ObjectNode nil = request("primary-title-loss-and-deficit"); ((ObjectNode) nil.get("snapshot")).putNull("player_armies");
        assertTrue(observe(nil).orElseThrow().observedPlayerRaisedSoldiers().isEmpty());
        ObjectNode empty = request("primary-title-loss-and-deficit"); ((ObjectNode) empty.get("snapshot")).putArray("player_armies");
        assertEquals(Optional.of(BigInteger.ZERO), observe(empty).orElseThrow().observedPlayerRaisedSoldiers());
    }

    @Test
    void historicalActualCacheOnlyWorksInSameSnapshotAndRevision() throws IOException {
        ObjectNode historical = request("historical-p50-operational-strength-projection");
        WarCashFocusProjection.FocusedWar current = observe(historical).orElseThrow();
        assertEquals(new BigInteger("100663323"), current.warId());
        assertEquals(Optional.of(BigInteger.valueOf(1351)), current.observedPlayerRaisedSoldiers());
        assertEquals(Optional.of(BigInteger.valueOf(1575)), current.observedEnemyRaisedSoldiers());
        for (String field : new String[]{"army_strengths_queried_snapshot_id", "army_strengths_queried_revision"}) {
            ObjectNode stale = historical.deepCopy(); ((ObjectNode) stale.get("snapshot")).remove(field);
            assertTrue(observe(stale).isEmpty(), field);
        }
    }

    @Test
    void sharedPoliticalAndRealmQualifiersRejectActualSourceBindingDrift() throws IOException {
        assertTrue(observe(request("source-bound-political-survival")).isPresent());
        assertTrue(observe(request("political-query-wrong-generation")).isEmpty());
        assertTrue(observe(request("qualified-nonleading-realm-siege")).isPresent());
        assertTrue(observe(request("nonleading-unqualified-frame-keeps-no-focus")).isEmpty());
        ObjectNode malformed = request("qualified-nonleading-realm-siege");
        ((ObjectNode) malformed.path("snapshot").path("active_wars").get(0)).put("player_is_primary_war_leader", 0);
        byte[] raw = JSON.writeValueAsBytes(malformed);
        assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(raw));
    }

    @Test
    void unknownExtensionsKeepFloatTokensAndUnicodeByteOffsetsAcrossOpaqueRequest() throws IOException {
        String ordinary = sample("source-bound-political-survival").path("request_json").textValue();
        String withExtensions = ordinary.replace("\"snapshot\":{", "\"snapshot\":{\"extension_雪\":1.0,")
                .replace("\"campaign_root\":{", "\"campaign_root\":{\"extension_火\":2.25,");
        byte[] raw = bytes(withExtensions); WarCashFocusProjectionCodec.Request request = WarCashFocusProjectionCodec.decode(raw);
        assertTrue(WarCashFocusProjection.observe(request).isPresent());
        assertArrayEquals(raw, WarCashFocusProjectionCodec.encodeRequest(request));
        raw[0] = '['; byte[] firstEncoding = WarCashFocusProjectionCodec.encodeRequest(request); firstEncoding[0] = '[';
        assertEquals((byte) '{', WarCashFocusProjectionCodec.encodeRequest(request)[0]);
        assertTrue(WarCashFocusProjection.observe(request).isPresent());
    }

    @Test
    void duplicateWarIdPreservesOriginalConsumerFirstRowLookup() throws IOException {
        ObjectNode request = request("winning-current-advantage-no-protected-focus");
        ArrayNode wars = (ArrayNode) request.path("snapshot").path("active_wars");
        ObjectNode protectedLater = ((ObjectNode) wars.get(0)).deepCopy(); protectedLater.put("player_relative_war_score", -40);
        ((ObjectNode) protectedLater.path("enemy_armies").get(0)).put("soldiers", 2500); wars.add(protectedLater);
        assertEquals(Optional.of(BigInteger.valueOf(1500)), observe(request).orElseThrow().observedEnemyRaisedSoldiers());
    }

    @Test
    void primarySiegeAndUniqueHostileUnionProtectCashWithoutInventingIndividualDeficit() throws IOException {
        ObjectNode siege = request("winning-current-advantage-no-protected-focus");
        ObjectNode enemy = (ObjectNode) siege.path("snapshot").path("active_wars").get(0).path("enemy_armies").get(0);
        enemy.put("army_state", "sieging"); enemy.put("siege_province_in_player_subrealm", true);
        assertTrue(observe(siege).isPresent());

        ObjectNode union = request("winning-current-advantage-no-protected-focus");
        ArrayNode wars = (ArrayNode) union.path("snapshot").path("active_wars");
        ObjectNode first = (ObjectNode) wars.get(0);
        first.put("player_side", "attacker"); first.put("player_relative_war_score", -1); first.putArray("targeted_title_ids");
        assertTrue(observe(union).isEmpty()); // 2,000 own versus this war's 1,500, no other protection reason.
        ObjectNode second = first.deepCopy(); second.put("war_id", 100);
        ((ObjectNode) second.path("enemy_armies").get(0)).put("army_id", 3); wars.add(second);
        assertTrue(observe(union).isPresent()); // Unique primary-hostile union is 3,000, not either individual deficit.
        ((ObjectNode) second.path("enemy_armies").get(0)).put("army_id", 2);
        assertTrue(observe(union).isEmpty()); // The same hostile army in two wars is counted once.
    }

    @Test
    void strictBoundaryRejectsDuplicateKeysInvalidUtf8OversizeAndMalformedResults() {
        assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(bytes("{\"schema\":1,\"schema\":2}")));
        assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decode(new byte[65_537]));
        for (String invalid : new String[]{"{}", "true", "{\"war_id\":1,\"observed_player_raised_soldiers\":1.0,\"observed_enemy_raised_soldiers\":null}",
                "{\"war_id\":1,\"observed_player_raised_soldiers\":-1,\"observed_enemy_raised_soldiers\":0}",
                "{\"war_id\":1,\"observed_player_raised_soldiers\":0,\"observed_enemy_raised_soldiers\":0,\"ready\":true}"}) {
            assertThrows(IllegalArgumentException.class, () -> WarCashFocusProjectionCodec.decodeResult(bytes(invalid)));
        }
    }

    private static Optional<WarCashFocusProjection.FocusedWar> observe(ObjectNode value) throws IOException {
        return WarCashFocusProjection.observe(WarCashFocusProjectionCodec.decode(JSON.writeValueAsBytes(value)));
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = WarCashFocusProjectionTest.class.getResourceAsStream("/warpriorityfocus/golden.json")) {
            if (stream == null) { throw new IllegalStateException("actual complete producer projection capture not executed"); }
            return StrictJson.parse(stream.readAllBytes(), 98_304);
        }
    }
    private static JsonNode sample(String name) throws IOException {
        for (JsonNode row : golden().get("cases")) { if (name.equals(row.path("name").textValue())) { return row; } }
        throw new IllegalStateException("actual producer golden sample missing: " + name);
    }
    private static ObjectNode request(String name) throws IOException {
        return (ObjectNode) JSON.readTree(sample(name).path("request_json").textValue());
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
