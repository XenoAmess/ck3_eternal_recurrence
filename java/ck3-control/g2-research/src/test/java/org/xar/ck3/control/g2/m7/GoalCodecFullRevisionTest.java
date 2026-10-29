package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionPolicy;

/** Actual pure M3 freeze/reconcile/codec -> M7 goal continuation. Synthetic frames grant no Game credit. */
final class GoalCodecFullRevisionTest {
    private static final BigInteger MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);

    @Test void fullUint64RevisionSurvivesActualM3ProducerAndGoalPersistence() {
        byte[] produced = produced();
        ObjectNode original = assertInstanceOf(ObjectNode.class, StrictJson.parse(produced));
        assertEquals(MAX, original.get("successor_binding").get("revision").bigIntegerValue());
        assertEquals(MAX.subtract(BigInteger.ONE), original.get("predecessor_binding").get("revision").bigIntegerValue());
        var reconciliation = GoalCodec.decodeReconciliation(produced);
        var continued = OrdinaryCampaignGoal.continueGoal(OrdinaryCampaignGoal.newGoal("full-revision", 100), reconciliation);
        assertEquals(200, continued.currentCharacterId());
        assertEquals(100, continued.originCharacterId());
        assertEquals(1, continued.progress().reconciledSuccessions());
        assertEquals(continued, GoalCodec.decodeGoal(GoalCodec.encodeGoal(continued)));
        assertEquals(OrdinaryCampaignGoal.plan(continued), GoalCodec.decodePlan(GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(continued))));
        assertEquals(reconciliation, GoalCodec.decodeReconciliation(StrictJson.canonical(original)));
        assertArrayEquals(produced, produced(), "goal consumer must leave original M3 numeric JSON untouched");
    }

    @Test void everyBindingRevisionRequiresExactNonnegativeUint64JsonInteger() {
        for (String binding : List.of("predecessor_binding", "successor_binding")) {
            for (String field : List.of("revision", "native_revision")) {
                for (String token : List.of("true", "1.0", "\"1\"", "null", "-1", "18446744073709551616")) {
                    ObjectNode changed = assertInstanceOf(ObjectNode.class, StrictJson.parse(produced()));
                    ((ObjectNode) changed.get(binding)).set(field, StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
                    assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(StrictJson.canonical(changed)), binding + "/" + field + ": " + token);
                }
                ObjectNode missing = assertInstanceOf(ObjectNode.class, StrictJson.parse(produced())); ((ObjectNode) missing.get(binding)).remove(field);
                assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(StrictJson.canonical(missing)));
            }
        }
    }

    @Test void ordinaryBoundedFieldsRemainNumericAndRejectFull64AndWrongTypes() {
        for (String token : List.of("true", "1.0", "\"100\"", "18446744073709551615", "-1", "-2147483649", "2147483648")) {
            ObjectNode changed = assertInstanceOf(ObjectNode.class, StrictJson.parse(produced()));
            changed.set("predecessor_character_id", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(changed.toString().getBytes(StandardCharsets.UTF_8)));
        }
        for (String token : List.of("-2147483648", "-2", "0", "2147483647")) {
            ObjectNode changed = assertInstanceOf(ObjectNode.class, StrictJson.parse(produced()));
            changed.set("predecessor_character_id", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            ((ObjectNode) changed.get("predecessor_binding")).set("episode_character_id", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            var reconciliation = GoalCodec.decodeReconciliation(StrictJson.canonical(changed));
            assertEquals(Integer.parseInt(token), reconciliation.predecessorCharacterId());
        }
    }

    @Test void widePositiveCharacterIdsFailModernCodec() {
        // Modern GoalCodec rejects >INT_MAX character IDs
        for (String token : List.of("2147483648", "4294967294", "1208925819614629174706176")) {
            ObjectNode changed = assertInstanceOf(ObjectNode.class, StrictJson.parse(produced()));
            changed.set("predecessor_character_id", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(StrictJson.canonical(changed)), "wide positive " + token);
        }
    }

    @Test void signedReconciliationLoopPreservesPredecessorAndDistinctSuccessor() {
        byte[] produced = produced();
        var reconciliation = GoalCodec.decodeReconciliation(produced);
        var goal = OrdinaryCampaignGoal.newGoal("signed-loop", 100);
        for (long actor : new long[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var fresh = OrdinaryCampaignGoal.newGoal("signed-fresh", actor);
            assertEquals(fresh, GoalCodec.decodeGoal(GoalCodec.encodeGoal(fresh)));
            assertEquals(OrdinaryCampaignGoal.plan(fresh),
                    GoalCodec.decodePlan(GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(fresh))));
        }
        var continued = OrdinaryCampaignGoal.continueGoal(goal, reconciliation);
        
        // Verify predecessor binding matches signed predecessor
        assertEquals(reconciliation.predecessorCharacterId(), goal.currentCharacterId());
        assertEquals(200, continued.currentCharacterId());
        assertNotEquals(reconciliation.predecessorCharacterId(), reconciliation.actualSuccessorCharacterId());
        
        // Verify goal/plan serde roundtrip
        assertEquals(continued, GoalCodec.decodeGoal(GoalCodec.encodeGoal(continued)));
        assertEquals(OrdinaryCampaignGoal.plan(continued), GoalCodec.decodePlan(GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(continued))));
    }

    @Test void codecTitleRejectionWithConsistentArrays() {
        var goal = OrdinaryCampaignGoal.newGoal("title-test", 100);
        var reconciliation = new OrdinaryCampaignGoal.Reconciliation(
                OrdinaryCampaignGoal.Verdict.MATCHED, 100, 200,
                List.of(1L, 2147483647L), List.of(), List.of());
        var continued = OrdinaryCampaignGoal.continueGoal(goal, reconciliation);
        assertEquals(continued, GoalCodec.decodeGoal(GoalCodec.encodeGoal(continued)));
        // The record retains its original positive safe-integer Title domain.
        for (long title : new long[] {-2, -1, 0, StrictJson.MAX_SAFE_INTEGER + 1}) {
            assertThrows(IllegalArgumentException.class, () -> new OrdinaryCampaignGoal.Succession(
                    100, 200, List.of(title), List.of(), List.of()));
        }
        assertDoesNotThrow(() -> new OrdinaryCampaignGoal.Succession(100, 200, List.of(2147483648L), List.of(), List.of()));
        // The persisted Title wire remains positive int32, separate from signed character IDs.
        for (long title : new long[] {-2, -1, 0, 2147483648L}) {
            ObjectNode changed = assertInstanceOf(ObjectNode.class, StrictJson.parse(GoalCodec.encodeGoal(continued)));
            ObjectNode progress = assertInstanceOf(ObjectNode.class, changed.get("progress"));
            ObjectNode last = assertInstanceOf(ObjectNode.class, progress.get("last_succession"));
            last.putArray("matched_inherited_title_ids").add(title);
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(
                    changed.toString().getBytes(StandardCharsets.UTF_8)), "title " + title);
        }
    }

    private static byte[] produced() {
        Frame before = new Frame("before-full64", MAX.subtract(BigInteger.ONE), MAX.subtract(BigInteger.TWO), 53_327_184);
        Frame after = new Frame("after-full64", MAX, MAX, 53_327_208);
        Title title = new Title(1, BigInteger.TWO, new WireObject("{\"title_id\":1,\"tier_raw\":2}".getBytes(StandardCharsets.UTF_8)));
        var rows = List.of(new TitleRow(title, 200, true));
        var frozen = SuccessionPolicy.freeze(new TurnBundle(before, new Actor(100, true), rows, 200, RiskState.SINGLE_SUCCESSOR), "original-life", 100);
        // Round-trip the real persistent producer before the independent post-transition comparison.
        var retained = SuccessionCodec.decodeExpectation(SuccessionCodec.encodeExpectation(frozen));
        Snapshot post = new Snapshot(after, "original-life", 100, true, true, true, "played_character_changed", new Actor(200, true), false, false, Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION);
        return SuccessionCodec.encodeReconciliation(SuccessionPolicy.reconcile(retained, post,
                new TurnBundle(after, new Actor(200, true), rows, 200, RiskState.SINGLE_SUCCESSOR)));
    }
}