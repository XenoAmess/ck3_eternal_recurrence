package org.xar.ck3.control.wave2.military.realmsiege;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Same current-siege document feeds every actual shared scope consumer, including public Army slot zero. */
final class RealmSiegePublicUnitZeroTest {
    @Test void actualRetainedProducerDocumentQualifiesPublicUnitZeroAcrossAllConsumersAndSerde() throws Exception {
        ObjectNode input=base();ObjectNode enemy=(ObjectNode)input.get("snapshot").get("active_wars").get(0).get("enemy_armies").get(0);enemy.put("army_id",0);
        var request=RealmSiegeCodec.decode(StrictJson.canonical(input));var snapshot=request.snapshot();var war=request.candidateWar();var selected=request.candidateEnemy();
        assertEquals(BigInteger.ZERO,selected.armyId());assertTrue(RealmSiegePolicy.qualifies(snapshot,war,selected));assertTrue(RealmSiegePolicy.warQualifies(snapshot,war));
        var assessment=RealmSiegePolicy.assess(request);assertTrue(assessment.candidateEnemyScopeObserved());assertTrue(assessment.candidateWarScopeObserved());assertTrue(assessment.currentWarScopesInStoredOrder().getFirst().enemyScopesInStoredOrder().getFirst());
        var restored=RealmSiegeCodec.decode(RealmSiegeCodec.encodeRequest(request));assertEquals(assessment,RealmSiegePolicy.assess(restored));assertSame(restored.candidateEnemy(),restored.candidateWar().enemyArmies().getFirst());
        for(String privateId:List.of("owner_character_id","current_province_id")) {
            ObjectNode invalid=input.deepCopy();((ObjectNode)invalid.get("snapshot").get("active_wars").get(0).get("enemy_armies").get(0)).put(privateId,0);
            assertFalse(RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(invalid))).candidateEnemyScopeObserved(),privateId);
        }
        for(BigInteger invalid:List.of(BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE))) {
            enemy.put("army_id",invalid);assertFalse(RealmSiegePolicy.assess(RealmSiegeCodec.decode(StrictJson.canonical(input))).candidateEnemyScopeObserved());
        }
        enemy.put("army_id",true);assertThrows(IllegalArgumentException.class,()->RealmSiegeCodec.decode(StrictJson.canonical(input)));
        enemy.put("army_id",0.0);byte[] floating=input.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);assertThrows(IllegalArgumentException.class,()->RealmSiegeCodec.decode(floating));
    }
    private static ObjectNode base() throws Exception {
        try(InputStream raw=RealmSiegePublicUnitZeroTest.class.getResourceAsStream("/realmsiege/original-producer-golden-v1.json.gz")) {
            assertNotNull(raw,"the existing actual producer fixture must be present; absence is RED");
            try(InputStream input=new GZIPInputStream(raw)) {
                for(JsonNode row:StrictJson.parse(input.readNBytes(131073),131072).get("cases"))if("synthetic_current_realm_siege".equals(row.get("name").textValue()))return row.get("request").deepCopy();
            }
        }
        throw new IllegalStateException("actual retained source vector missing");
    }
}
