package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Loaded;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Rejected;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Verifies legacy normalization accepts wide positive BigInteger character IDs while modern codec rejects them. */
final class LegacyResumeGoalCharacterDomainTest {
    private static final String PIPE = "test-pipe";
    private static final BigInteger INT_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger INT_MIN = BigInteger.valueOf(Integer.MIN_VALUE);

    private static Obj buildLegacyDriver(BigInteger originId, BigInteger currentId) {
        Map<String, Value> members = new LinkedHashMap<>();
        members.put("format_version", new IntegerValue(BigInteger.TWO));
        members.put("pipe_name", new Text(PIPE));
        members.put("bridge_pid", new IntegerValue(BigInteger.valueOf(42)));
        members.put("episode_character_id", new IntegerValue(BigInteger.valueOf(7)));
        members.put("episode_run_id", new Text("run-1"));
        members.put("command_history", new Arr(List.of()));
        members.put("last_checkpoint", Nil.INSTANCE);
        members.put("rollback_war_failure", Nil.INSTANCE);
        members.put("rollback_war_failures", new Arr(List.of()));
        members.put("managed_restore_transaction", Nil.INSTANCE);
        members.put("succession_expectation", Nil.INSTANCE);
        // succession_lifecycle omitted to allow default legacy binding
        
        // Build goal with wide IDs using GoalCodec
        var goal = OrdinaryCampaignGoal.newGoal("test-campaign", 7);
        // Override character IDs in the encoded goal
        byte[] encoded = GoalCodec.encodeGoal(goal);
        JsonNode node = StrictJson.parse(encoded);
        assertTrue(node instanceof ObjectNode);
        ObjectNode obj = (ObjectNode) node;
        obj.set("origin_character_id", StrictJson.parse(originId.toString().getBytes()));
        obj.set("current_character_id", StrictJson.parse(currentId.toString().getBytes()));
        byte[] modified = StrictJson.canonical(obj);
        
        Value goalValue = DriverJson.object(modified, 4 << 20);
        members.put("campaign_goal", goalValue);
        return new Obj(members);
    }

    @Test void legacyNormalizerAcceptsWidePositiveCharacterIds() {
        BigInteger[] wideIds = {BigInteger.valueOf(2147483648L), BigInteger.valueOf(4294967294L), BigInteger.ONE.shiftLeft(80)};
        for (BigInteger id : wideIds) {
            Obj driver = buildLegacyDriver(id, id);
            var result = LegacyResumeNormalizer.normalize(driver, PIPE);
            assertTrue(result instanceof Loaded, "legacy normalizer should accept wide positive ID: " + id);
            Loaded loaded = (Loaded) result;
            Obj payload = loaded.normalizedPayload();
            Value goal = payload.get("campaign_goal");
            assertTrue(goal instanceof Obj);
            Obj goalObj = (Obj) goal;
            assertEquals(id, ((IntegerValue) goalObj.get("origin_character_id")).value());
            assertEquals(id, ((IntegerValue) goalObj.get("current_character_id")).value());
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(OpportunityJson.encode(goalObj)),
                    "legacy DATA must not silently become a modern bound actor");
        }
    }

    @Test void modernCodecRejectsWidePositiveCharacterIds() {
        BigInteger[] wideIds = {BigInteger.valueOf(2147483648L), BigInteger.valueOf(4294967294L), BigInteger.ONE.shiftLeft(80)};
        for (BigInteger id : wideIds) {
            var goal = OrdinaryCampaignGoal.newGoal("test-campaign", 7);
            byte[] encoded = GoalCodec.encodeGoal(goal);
            JsonNode node = StrictJson.parse(encoded);
            assertTrue(node instanceof ObjectNode);
            ObjectNode obj = (ObjectNode) node;
            obj.set("origin_character_id", StrictJson.parse(id.toString().getBytes()));
            obj.set("current_character_id", StrictJson.parse(id.toString().getBytes()));
            byte[] modified = StrictJson.canonical(obj);
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(modified), "modern codec should reject wide ID: " + id);
        }
    }

    @Test void legacyNormalizerAcceptsSignedInt32Boundaries() {
        BigInteger[] validIds = {INT_MIN, BigInteger.valueOf(-2), BigInteger.ZERO, INT_MAX};
        for (BigInteger id : validIds) {
            Obj driver = buildLegacyDriver(id, id);
            var result = LegacyResumeNormalizer.normalize(driver, PIPE);
            assertTrue(result instanceof Loaded, "legacy normalizer should accept signed int32: " + id);
        }
    }

    @Test void legacyNormalizerRejectsInvalidCharacterIds() {
        BigInteger[] invalidIds = {BigInteger.valueOf(-1), INT_MIN.subtract(BigInteger.ONE)};
        for (BigInteger id : invalidIds) {
            Obj driver = buildLegacyDriver(id, id);
            var result = LegacyResumeNormalizer.normalize(driver, PIPE);
            assertTrue(result instanceof Rejected, "legacy normalizer should reject invalid ID: " + id);
        }
    }

    @Test void legacyNormalizerRejectsNonIntegerCharacterIds() {
        Obj valid = buildLegacyDriver(BigInteger.valueOf(7), BigInteger.valueOf(7));
        Obj originalGoal = (Obj) valid.get("campaign_goal");
        for (String field : List.of("origin_character_id", "current_character_id")) {
            for (String token : List.of("true", "1.0", "\"7\"", "null")) {
                Obj changedGoal = originalGoal.with(field,
                        OpportunityJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertInstanceOf(Rejected.class, LegacyResumeNormalizer.normalize(
                        valid.with("campaign_goal", changedGoal), PIPE), field + ": " + token);
                byte[] wire = OpportunityJson.encode(changedGoal);
                assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(wire),
                        "modern " + field + ": " + token);
            }
            Map<String, Value> missing = new LinkedHashMap<>(originalGoal.members());
            missing.remove(field);
            assertInstanceOf(Rejected.class, LegacyResumeNormalizer.normalize(
                    valid.with("campaign_goal", new Obj(missing)), PIPE), "missing " + field);
            byte[] wire = OpportunityJson.encode(new Obj(missing));
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(wire), "modern missing " + field);
        }
    }

    @Test void legacyNormalizerPreservesWideIdsInPayload() {
        BigInteger wideId = BigInteger.ONE.shiftLeft(80);
        Obj driver = buildLegacyDriver(wideId, wideId);
        var result = LegacyResumeNormalizer.normalize(driver, PIPE);
        assertTrue(result instanceof Loaded);
        Loaded loaded = (Loaded) result;
        byte[] encoded = loaded.encode();
        Value parsed = OpportunityJson.parse(encoded);
        Obj payload = (Obj) parsed;
        Value goal = payload.get("campaign_goal");
        Obj goalObj = (Obj) goal;
        assertEquals(wideId, ((IntegerValue) goalObj.get("origin_character_id")).value());
        assertEquals(wideId, ((IntegerValue) goalObj.get("current_character_id")).value());
    }
}