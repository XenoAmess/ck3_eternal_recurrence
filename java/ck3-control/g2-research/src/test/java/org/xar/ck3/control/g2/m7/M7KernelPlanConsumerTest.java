package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;

final class M7KernelPlanConsumerTest {
    @Test void allRealPublicationReadersRetainTheExactFullKernelBirthAndGoal() {
        for (M7OrdinaryPlanConsumer.Publication publication : M7OrdinaryPlanConsumer.Publication.values()) {
            var consumed = M7KernelPlanConsumer.consume(publication, observation("18446744073709551615"), "life-advance", Optional.empty());
            var fresh = M7KernelPlanConsumer.decode(M7KernelPlanConsumer.encode(consumed));
            assertEquals(consumed, fresh);
            assertEquals("18446744073709551615", fresh.observation().game().creationFiletime());
            assertEquals(OrdinaryCampaignGoal.plan(fresh.observation().goal()), fresh.campaignGoalPlanUsed());
            assertFalse(fresh.gameActionsSubmitted()); assertFalse(fresh.coldAuthorityGranted()); assertFalse(fresh.replayAuthorized()); assertEquals(0, fresh.savedDayCredit());
            assertTrue(new String(M7KernelPlanConsumer.encode(consumed), StandardCharsets.UTF_8).contains("\"creation_filetime\":\"18446744073709551615\""));
        }
        assertFalse(KernelCheckpointContinuity.sameGameIdentity(observation("134370144000000001"), observation("134370144000000002")));
    }
    @Test void wrongBirthTokenGoalDriftMissingFieldAndInventedCreditsAreRefused() {
        var consumed = M7KernelPlanConsumer.consume(M7OrdinaryPlanConsumer.Publication.CHECKPOINT_READER,
                observation("134370144000000001"), "save-checkpoint", Optional.empty());
        byte[] original = M7KernelPlanConsumer.encode(consumed);
        var numeric = StrictJson.parse(original);
        ((com.fasterxml.jackson.databind.node.ObjectNode) numeric.path("observation").path("game_identity"))
                .put("creation_filetime", 134370144000000001L);
        assertThrows(IllegalArgumentException.class, () -> M7KernelPlanConsumer.decode(numeric.toString().getBytes(StandardCharsets.UTF_8)));
        var missing = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(original); missing.remove("government_context");
        assertThrows(IllegalArgumentException.class, () -> M7KernelPlanConsumer.decode(missing.toString().getBytes(StandardCharsets.UTF_8)));
        var changed = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(original); changed.put("saved_day_credit", 1);
        assertThrows(IllegalArgumentException.class, () -> M7KernelPlanConsumer.decode(changed.toString().getBytes(StandardCharsets.UTF_8)));
        var drift = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(original);
        ((com.fasterxml.jackson.databind.node.ObjectNode) drift.path("campaign_goal_plan_used")).put("current_character_id", 200);
        assertThrows(IllegalArgumentException.class, () -> M7KernelPlanConsumer.decode(drift.toString().getBytes(StandardCharsets.UTF_8)));
        assertEquals(consumed, M7KernelPlanConsumer.decode(original));
    }
    private static KernelCheckpointContinuity.Observation observation(String birth) {
        return new KernelCheckpointContinuity.Observation("m7-kernel-software-fixture", "a".repeat(64), new GameIdentity(123, birth),
                new ExactRef("software-fixture/ck3.exe", 1, "b".repeat(64)), "native:2", 3, 2, "software-episode", 100,
                org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.9.15"),
                OrdinaryCampaignGoal.newGoal("software-campaign", 100), null, null);
    }
}
