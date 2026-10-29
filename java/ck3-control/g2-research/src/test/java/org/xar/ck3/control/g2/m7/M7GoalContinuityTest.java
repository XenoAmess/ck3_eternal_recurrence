package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.GameIdentity;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.Observation;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Reconciliation;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Verdict;

/** All frames/processes are synthetic. This exercises no OS, Driver, SAVE, Game or writer operation. */
class M7GoalContinuityTest {
    private static final String EPOCH = "a".repeat(64);
    private static Reconciliation matched(long before, long after) {
        return new Reconciliation(Verdict.MATCHED, before, after, List.of(2191L, 2204L), List.of(2262L), List.of());
    }
    private static Observation observation(Goal goal, long pid, String birth, String key, String family) {
        return new Observation("synthetic-machine", EPOCH, new GameIdentity(pid, birth, "D:\\game\\ck3.exe"),
                "native:8", 9, 8, "native-" + goal.currentCharacterId() + "-fixture", goal.currentCharacterId(),
                53_327_184, goal, key, family);
    }
    private static String json(byte[] raw) { return new String(raw, StandardCharsets.UTF_8); }
    private static byte[] raw(String text) { return text.getBytes(StandardCharsets.UTF_8); }

    @Test void singleGoalAndOrdinaryPlanRoundtripWithoutLosingTitleArrayDomain() {
        Goal original = OrdinaryCampaignGoal.newGoal("native-31254-synthetic", 31254);
        assertEquals(original, GoalCodec.decodeGoal(GoalCodec.encodeGoal(original)));
        Goal successor = OrdinaryCampaignGoal.continueGoal(original, matched(31254, 40526));
        assertEquals(successor, GoalCodec.decodeGoal(GoalCodec.encodeGoal(successor)));
        assertEquals(original.campaignId(), successor.campaignId()); assertEquals(31254, successor.originCharacterId());
        assertEquals(40526, successor.currentCharacterId()); assertEquals(1, successor.progress().reconciledSuccessions());
        var plan = OrdinaryCampaignGoal.plan(successor);
        assertEquals(plan, GoalCodec.decodePlan(GoalCodec.encodePlan(plan)));
        assertEquals(List.of(100, 60), plan.priorities().stream().map(OrdinaryCampaignGoal.Priority::priority).toList());
        assertTrue(StrictJson.parse(GoalCodec.encodeGoal(successor)).get("progress").get("last_succession")
                .get("matched_inherited_title_ids").isArray());
    }

    @Test void repeatedVerifiedSuccessionsKeepTheSameOriginWithoutAFixedGenerationGate() {
        Goal goal = OrdinaryCampaignGoal.newGoal("independent-synthetic-seed", 100);
        for (long actor = 100; actor < 105; actor++) { goal = OrdinaryCampaignGoal.continueGoal(goal, matched(actor, actor + 1)); }
        assertEquals(100, goal.originCharacterId()); assertEquals(105, goal.currentCharacterId());
        assertEquals(5, goal.progress().reconciledSuccessions());
    }

    @Test void unknownAndUnavailableNeverAdvanceIntentOrReplayAnAction() {
        Goal original = OrdinaryCampaignGoal.newGoal("unknown-synthetic", 100); byte[] before = GoalCodec.encodeGoal(original);
        for (Verdict verdict : Verdict.values()) {
            if (verdict == Verdict.MATCHED) { continue; }
            Reconciliation unknown = new Reconciliation(verdict, 100, 200, List.of(1L), List.of(), List.of());
            assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.continueGoal(original, unknown));
            assertArrayEquals(before, GoalCodec.encodeGoal(original));
        }
    }

    @Test void wrongPredecessorAndMutableListsCannotRewriteTheOriginalGoal() {
        Goal goal = OrdinaryCampaignGoal.newGoal("immutable-synthetic", 100);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.continueGoal(goal, matched(99, 200)));
        ArrayList<Long> titles = new ArrayList<>(List.of(1L));
        Reconciliation transition = new Reconciliation(Verdict.MATCHED, 100, 200, titles, List.of(), List.of()); titles.clear();
        assertEquals(List.of(1L), OrdinaryCampaignGoal.continueGoal(goal, transition).progress().lastSuccession().orElseThrow().matchedInheritedTitleIds());
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.newGoal("bad", StrictJson.MAX_SAFE_INTEGER + 1));
    }

    @Test void goalControlTokensRejectBoolFloatMissingNullWrongAndExtraFields() {
        String valid = json(GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal("strict-synthetic", 100)));
        for (String token : List.of("true", "1.0", "\"1\"", "null")) {
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(raw(valid.replace("\"format_version\":1", "\"format_version\":" + token))));
        }
        for (String token : List.of("true", "100.0", "null", "0")) {
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(raw(valid.replace("\"current_character_id\":100", "\"current_character_id\":" + token))));
        }
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(raw(valid.replace("\"last_succession\":null,", ""))));
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(raw(valid.replace("{", "{\"extra\":0,"))));
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(raw(valid.replace("\"format_version\":1", "\"format_version\":1,\"format_version\":1"))));
    }

    @Test void persistedPlanCannotDriftAwayFromTheSharedGoalProducer() {
        byte[] original = GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(OrdinaryCampaignGoal.newGoal("plan-synthetic", 100)));
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodePlan(raw(json(original).replace("\"priority\":100", "\"priority\":101"))));
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodePlan(raw(json(original).replace("\"focus\":\"marriage\"", "\"focus\":\"war\""))));
    }

    @Test void fullM3ReconciliationIsConsumedWithoutAHiddenSixFieldAlias() {
        ObjectNode reconciliation = originalReconciliation();
        Reconciliation projected = GoalCodec.decodeReconciliation(StrictJson.canonical(reconciliation));
        assertEquals(200, OrdinaryCampaignGoal.continueGoal(OrdinaryCampaignGoal.newGoal("m3-synthetic", 100), projected).currentCharacterId());
        ObjectNode wrong = reconciliation.deepCopy(); wrong.put("successor_match", false);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(StrictJson.canonical(wrong)));
        ObjectNode incomplete = reconciliation.deepCopy(); incomplete.remove("predecessor_binding");
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(StrictJson.canonical(incomplete)));
        ObjectNode wrongToken = reconciliation.deepCopy(); wrongToken.put("actual_successor_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(StrictJson.canonical(wrongToken)));
        ObjectNode wrongTitles = reconciliation.deepCopy(); wrongTitles.withArray("matched_inherited_title_ids").add(2);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(StrictJson.canonical(wrongTitles)));
    }

    @Test void dmtfOffsetAndIsoBirthEqualityRemainExactAndUnknownIsNeverAnExitProof() {
        var dmtf = new GameIdentity(10, "20261023123045.123456+480", "D:\\Game\\ck3.exe");
        var iso = new GameIdentity(10, "2026-10-23T04:30:45.1234560Z", "d:/game/ck3.exe");
        assertTrue(CheckpointContinuity.sameGameIdentity(dmtf, iso));
        assertFalse(CheckpointContinuity.sameGameIdentity(dmtf, new GameIdentity(10, "2026-10-23T04:30:45.1234570Z", "D:\\Game\\ck3.exe")));
        for (String birth : List.of("unknown", "", "null", "2026-10-23T04:30:45.1234561Z", "20261023123045.123456+841")) {
            assertThrows(IllegalArgumentException.class, () -> new GameIdentity(10, birth, "D:\\game\\ck3.exe"));
        }
    }

    @Test void feudalAndClanAreSeparateKeysInTheSameFamilyAndNoFixtureGetsLiveCredit() {
        Goal goal = OrdinaryCampaignGoal.newGoal("synthetic-clan-seed", 100);
        Observation feudal = observation(goal, 10, "20261023123045.123456+480", "feudal_government", "core_landed");
        Observation clan = observation(goal, 10, "20261023123045.123456+480", "clan_government", "core_landed");
        var comparison = CheckpointContinuity.compare(feudal, clan);
        assertTrue(comparison.governmentKeyChanged()); assertFalse(comparison.adapterFamilyChanged());
        assertFalse(comparison.grantsColdAuthority()); assertFalse(comparison.actionReplayAuthorized());
        Observation tribal = observation(goal, 10, "20261023123045.123456+480", "tribal_government", "core_tribal");
        assertTrue(CheckpointContinuity.compare(feudal, tribal).adapterFamilyChanged());
    }

    @Test void checkpointObservationRoundtripKeepsIntentButReplacementBirthGrantsNoColdAuthority() {
        Goal goal = OrdinaryCampaignGoal.continueGoal(OrdinaryCampaignGoal.newGoal("checkpoint-synthetic", 100), matched(100, 200));
        Observation saved = observation(goal, 10, "20261023123045.123456+480", "feudal_government", "core_landed");
        Observation cold = observation(goal, 20, "20261023133045.123456+480", "feudal_government", "core_landed");
        assertEquals(saved, CheckpointContinuity.decodeObservation(CheckpointContinuity.encodeObservation(saved)));
        var result = CheckpointContinuity.compare(saved, cold);
        assertTrue(result.sameGoal()); assertTrue(result.sameCampaignOrigin()); assertTrue(result.sameRulerEpisode());
        assertTrue(result.replacementBirthKnown()); assertFalse(result.sameGameIdentity()); assertFalse(result.grantsColdAuthority());
        ObjectNode wrong = (ObjectNode) StrictJson.parse(CheckpointContinuity.encodeObservation(cold)); wrong.put("actor_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> CheckpointContinuity.decodeObservation(StrictJson.canonical(wrong)));
    }

    @Test void signedActorsSurviveLegacyObservationAndOrdinaryPlanPersistence() {
        for (long actor : new long[]{Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            Goal goal = OrdinaryCampaignGoal.newGoal("signed-synthetic", actor);
            Observation value = observation(goal, 10, "20261023123045.123456+480", null, null);
            assertEquals(value, CheckpointContinuity.decodeObservation(CheckpointContinuity.encodeObservation(value)));
            var consumed = M7OrdinaryPlanConsumer.consume(M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN,
                    value, "query", java.util.Optional.empty());
            assertEquals(consumed, M7OrdinaryPlanConsumer.decode(M7OrdinaryPlanConsumer.encode(consumed)));
            assertEquals(actor, consumed.observation().actorCharacterId());
            assertFalse(consumed.gameActionsSubmitted()); assertFalse(consumed.coldAuthorityGranted());
            assertFalse(consumed.replayAuthorized());
        }
    }

    @Test void legacyActorDecoderRejectsSentinelUnsignedAliasesAndWrongLiteralTokens() {
        Observation value = observation(OrdinaryCampaignGoal.newGoal("actor-boundary-synthetic", 1),
                10, "20261023123045.123456+480", null, null);
        String encoded = json(CheckpointContinuity.encodeObservation(value));
        for (String token : List.of("-1", "-2147483649", "2147483648", "2147483649", "4294967295",
                "true", "1.0", "\"1\"", "null")) {
            byte[] altered = raw(encoded.replace("\"actor_character_id\":1", "\"actor_character_id\":" + token));
            var error = assertThrows(IllegalArgumentException.class, () -> CheckpointContinuity.decodeObservation(altered), token);
            String reason = token.equals("-1") ? "absent-character sentinel"
                    : token.matches("-?[0-9]+") ? "integer outside contract range" : "exact JSON integer required";
            assertTrue(error.getMessage().contains(reason), error.getMessage());
        }
        ObjectNode missing = (ObjectNode) StrictJson.parse(CheckpointContinuity.encodeObservation(value));
        missing.remove("actor_character_id");
        assertThrows(IllegalArgumentException.class, () -> CheckpointContinuity.decodeObservation(StrictJson.canonical(missing)));
    }

    private static ObjectNode originalReconciliation() {
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.ck3.succession-reconciliation/v1"); row.put("status", "available");
        ObjectNode before = row.putObject("predecessor_binding"); binding(before); before.put("episode_run_id", "native-100-fixture"); before.put("episode_character_id", 100);
        binding(row.putObject("successor_binding")); row.put("predecessor_character_id", 100); row.put("expected_successor_character_id", 200);
        row.put("actual_successor_character_id", 200); row.put("successor_match", true); row.putArray("expected_inherited_title_ids").add(1);
        row.putArray("matched_inherited_title_ids").add(1); row.putArray("missing_expected_inherited_title_ids");
        row.putArray("unexpected_retained_predecessor_title_ids"); row.putArray("expected_other_heir_title_ids");
        row.putArray("expected_without_heir_title_ids"); row.putArray("observed_additional_successor_title_ids");
        row.put("title_distribution_match", true); row.put("verdict", "matched"); row.putNull("unavailable_reason"); return row;
    }
    private static void binding(ObjectNode row) { row.put("snapshot_id", "native:8"); row.put("revision", 9); row.put("native_revision", 8); row.put("date_raw", 53_327_184); }
}
