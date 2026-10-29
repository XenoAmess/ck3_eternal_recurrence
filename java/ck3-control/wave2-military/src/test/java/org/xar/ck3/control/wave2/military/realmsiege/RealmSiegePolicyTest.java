package org.xar.ck3.control.wave2.military.realmsiege;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Enemy;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Request;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.Snapshot;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy.War;

final class RealmSiegePolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream compressed = RealmSiegePolicyTest.class.getResourceAsStream("/realmsiege/original-producer-golden-v1.json.gz")) {
            assertNotNull(compressed, "committed real producer fixture is required; absence is not a skipped test");
            try (InputStream input = new GZIPInputStream(compressed)) {
                byte[] raw = input.readNBytes(131_073);
                return StrictJson.parse(raw, 131_072);
            }
        }
    }

    private static ObjectNode base() throws IOException {
        for (JsonNode vector : golden().get("cases")) {
            if (vector.get("name").textValue().equals("synthetic_current_realm_siege")) {
                return vector.get("request").deepCopy();
            }
        }
        throw new IllegalStateException("required synthetic comparison vector is absent");
    }

    @TestFactory
    Stream<DynamicTest> unchangedOriginalProducerAndFullProjectionRoundTrip() throws IOException {
        JsonNode fixture = golden();
        assertFalse(fixture.get("actual_live_qualification").booleanValue());
        assertEquals(32, fixture.get("cases").size());
        List<DynamicTest> result = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            result.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                byte[] raw = StrictJson.canonical(vector.get("request"));
                Request request = RealmSiegeCodec.decode(raw);
                assertEquals(vector.get("expected"), StrictJson.parse(RealmSiegeCodec.evaluate(raw)));
                Request roundTrip = RealmSiegeCodec.decode(RealmSiegeCodec.encodeRequest(request));
                assertEquals(request, roundTrip);
                assertEquals(RealmSiegePolicy.assess(request), RealmSiegePolicy.assess(roundTrip));
            }));
        }
        return result.stream();
    }

    @Test
    void equalDetachedObjectsNeverBecomeCurrentMembers() throws IOException {
        Request request = RealmSiegeCodec.decode(StrictJson.canonical(base()));
        Snapshot snapshot = request.snapshot(); War war = request.candidateWar(); Enemy enemy = request.candidateEnemy();
        assertSame(war, snapshot.activeWars().getFirst()); assertSame(enemy, war.enemyArmies().getFirst());
        assertTrue(RealmSiegePolicy.qualifies(snapshot, war, enemy));
        War detachedWar = new War(war.source(), war.warId(), war.playerSide(), war.playerIsPrimaryWarLeader(),
                war.playerRelativeWarScore(), war.enemyArmies());
        Enemy detachedEnemy = new Enemy(enemy.source(), enemy.armyId(), enemy.ownerCharacterId(), enemy.controllable(),
                enemy.armyState(), enemy.armyStateCode(), enemy.inCombat(), enemy.retreating(), enemy.currentProvinceId(),
                enemy.siegeProvinceInPlayerSubrealm(), enemy.moveTargetProvinceId(), enemy.routeProvinceIds(), enemy.routeReadStatus());
        assertEquals(war, detachedWar); assertNotSame(war, detachedWar);
        assertEquals(enemy, detachedEnemy); assertNotSame(enemy, detachedEnemy);
        assertFalse(RealmSiegePolicy.qualifies(snapshot, detachedWar, enemy));
        assertFalse(RealmSiegePolicy.qualifies(snapshot, war, detachedEnemy));
        assertFalse(RealmSiegePolicy.warQualifies(snapshot, detachedWar));
    }

    @Test
    void aSecondQualifyingEnemyDoesNotQualifyAnUnknownFirstEnemy() throws IOException {
        ObjectNode input = base();
        ArrayNode enemies = (ArrayNode) input.get("snapshot").get("active_wars").get(0).get("enemy_armies");
        ObjectNode qualifying = enemies.get(0).deepCopy();
        for (JsonNode enemy : enemies) { ((ObjectNode) enemy).putNull("siege_province_in_player_subrealm"); }
        enemies.add(qualifying);
        var assessment = RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(input)));
        assertFalse(assessment.candidateEnemyScopeObserved()); assertTrue(assessment.candidateWarScopeObserved());
        List<Boolean> rows = assessment.currentWarScopesInStoredOrder().getFirst().enemyScopesInStoredOrder();
        assertFalse(rows.getFirst()); assertTrue(rows.getLast());
    }

    @Test
    void missingNullAndEmptyRouteRemainDifferent() throws IOException {
        ObjectNode input = base(); ObjectNode enemy = (ObjectNode) input.get("snapshot").get("active_wars").get(0).get("enemy_armies").get(0);
        enemy.remove("move_target_province_id");
        Request missing = RealmSiegeCodec.decode(StrictJson.canonical(input));
        assertEquals(RealmSiegePolicy.Presence.MISSING, missing.candidateEnemy().moveTargetProvinceId().presence());
        assertFalse(RealmSiegePolicy.assess(missing).candidateEnemyScopeObserved());
        enemy.putNull("move_target_province_id");
        assertTrue(RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(input))).candidateEnemyScopeObserved());
        enemy.putNull("route_province_ids");
        assertFalse(RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(input))).candidateEnemyScopeObserved());
        enemy.putArray("route_province_ids");
        assertTrue(RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(input))).candidateEnemyScopeObserved());
    }

    @Test
    void rawFloatAndBooleanIdentityTokensReachTheActualDecoderAndAreRejected() throws IOException {
        String canonical = new String(StrictJson.canonical(base()), StandardCharsets.UTF_8);
        for (String field : List.of("native_revision", "revision", "date_raw", "character_id", "bridge_pid",
                "connection_generation", "war_id", "player_relative_war_score", "army_id", "owner_character_id",
                "army_state_code", "current_province_id")) {
            String key = "\"" + field + "\":";
            int start = canonical.indexOf(key) + key.length();
            assertTrue(start >= key.length(), field);
            int end = start;
            while (end < canonical.length() && (canonical.charAt(end) == '-' || Character.isDigit(canonical.charAt(end)))) { end++; }
            String original = canonical.substring(start, end);
            for (String replacement : List.of("true", original + ".0", "\"" + original + "\"")) {
                byte[] raw = (canonical.substring(0, start) + replacement + canonical.substring(end)).getBytes(StandardCharsets.UTF_8);
                assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(raw), field + "=" + replacement);
            }
        }
        ObjectNode input = base(); ((ObjectNode) input.get("snapshot")).put("paused", 1);
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(StrictJson.canonical(input)));
    }

    @Test
    void wrapperAndLocalReferencesAreStrictWhileSdkExtensionsRemainAProjection() throws IOException {
        ObjectNode input = base(); input.put("qualified_current_scope", true);
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(StrictJson.canonical(input)));
        ObjectNode missing = base(); missing.remove("candidate_war_ref");
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(StrictJson.canonical(missing)));
        ObjectNode badReference = base(); ((ObjectNode) badReference.get("candidate_war_ref")).put("collection", "external.json");
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(StrictJson.canonical(badReference)));
        ObjectNode outside = base(); ((ObjectNode) outside.get("candidate_enemy_ref")).put("index", Integer.MAX_VALUE);
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(StrictJson.canonical(outside)));
        ObjectNode sdkExtension = base(); ((ObjectNode) sdkExtension.get("snapshot")).putObject("future_sdk_domain").put("new_value", 3);
        assertTrue(RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(sdkExtension))).candidateEnemyScopeObserved());
        String rawExtension = new String(StrictJson.canonical(base()), StandardCharsets.UTF_8)
                .replace("\"snapshot\":{", "\"snapshot\":{\"future_sdk_fraction\":1.0,");
        assertTrue(RealmSiegePolicy.assess(RealmSiegeCodec.decode(rawExtension.getBytes(StandardCharsets.UTF_8))).candidateEnemyScopeObserved());
        ((ObjectNode) sdkExtension.get("snapshot")).put("source", "unknown").put("qualified_current_scope", true);
        assertFalse(RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(sdkExtension))).candidateEnemyScopeObserved());
    }

    @Test
    void malformedUtf8DuplicateKeysAndUnboundedInputsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode("{\"schema\":1,\"schema\":1}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> RealmSiegeCodec.decode(new byte[65_537]));
    }
}
