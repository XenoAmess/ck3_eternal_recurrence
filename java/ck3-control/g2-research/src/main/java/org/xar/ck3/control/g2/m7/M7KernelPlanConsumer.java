package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer.Publication;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Context;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** Current PLAN/checkpoint/successor reader. The legacy microsecond observation remains historical. */
public final class M7KernelPlanConsumer {
    public static final String SCHEMA = "xar.g2.m7.kernel-plan-consumption/v1";
    private M7KernelPlanConsumer() { }
    public record Consumed(Publication publication, KernelCheckpointContinuity.Observation observation,
            String selectedStep, OrdinaryCampaignGoal.GoalPlan campaignGoalPlanUsed, Optional<Context> government) {
        public Consumed {
            Objects.requireNonNull(publication); Objects.requireNonNull(observation); StrictJson.text(selectedStep);
            Objects.requireNonNull(campaignGoalPlanUsed); Objects.requireNonNull(government);
            StrictJson.require(campaignGoalPlanUsed.equals(OrdinaryCampaignGoal.plan(observation.goal())),
                    "kernel publication consumes the complete original current-ruler goal");
            government.ifPresent(value -> {
                GovernmentContextCodec.requireCurrentPlayerBinding(value, BigInteger.valueOf(observation.actorCharacterId()));
                StrictJson.require(Objects.equals(value.campaignId(), observation.goal().campaignId())
                        && Objects.equals(value.currentCharacterId(), BigInteger.valueOf(observation.actorCharacterId()))
                        && Objects.equals(value.snapshotRevision(), observation.nativeRevision())
                        && Objects.equals(value.dateRaw(), BigInteger.valueOf(observation.dateRaw())), "kernel government observation crossed its current frame");
                if (value.governmentKey() != null || value.identityObservationReady())
                    StrictJson.require(Objects.equals(value.governmentKey(), observation.governmentKey()), "kernel government key differs");
                if (value.adapterFamily() != null || value.identityObservationReady())
                    StrictJson.require(Objects.equals(value.adapterFamily(), observation.adapterFamily()), "kernel government adapter differs");
            });
        }
        public boolean gameActionsSubmitted() { return false; }
        public boolean coldAuthorityGranted() { return false; }
        public boolean replayAuthorized() { return false; }
        public int savedDayCredit() { return 0; }
    }
    public static Consumed consume(Publication publication, KernelCheckpointContinuity.Observation observation,
            String selectedStep, Optional<Context> government) {
        return new Consumed(publication, observation, selectedStep, OrdinaryCampaignGoal.plan(observation.goal()), government);
    }
    public static byte[] encode(Consumed value) {
        Objects.requireNonNull(value); ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        row.put("publication", value.publication().wire());
        row.set("observation", KernelCheckpointContinuity.toJson(value.observation())); row.put("selected_step", value.selectedStep());
        row.set("campaign_goal_plan_used", StrictJson.parse(GoalCodec.encodePlan(value.campaignGoalPlanUsed())));
        if (value.government().isPresent()) row.set("government_context", StrictJson.parse(GovernmentContextCodec.encode(value.government().orElseThrow())));
        else row.putNull("government_context");
        row.put("game_actions_submitted", false); row.put("cold_authority_granted", false); row.put("replay_authorized", false); row.put("saved_day_credit", 0);
        // Government metadata can contain decimal metrics; identity fields retain strict integer/string codecs.
        byte[] raw = row.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(raw.length > 0 && raw.length <= M7OrdinaryPlanConsumer.MAX_BYTES, "kernel plan exceeds its explicit byte budget");
        return raw;
    }
    public static Consumed decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, M7OrdinaryPlanConsumer.MAX_BYTES), Set.of("schema", "publication", "observation", "selected_step",
                "campaign_goal_plan_used", "government_context", "game_actions_submitted", "cold_authority_granted", "replay_authorized", "saved_day_credit"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "exact kernel plan schema required");
        for (String field : Set.of("game_actions_submitted", "cold_authority_granted", "replay_authorized")) {
            JsonNode value = row.get(field); StrictJson.require(value.isBoolean() && !value.booleanValue(), "kernel plan data cannot grant authority");
        }
        StrictJson.integer(row.get("saved_day_credit"), 0, 0);
        return new Consumed(Publication.fromWire(StrictJson.text(row.get("publication"))), KernelCheckpointContinuity.fromJson(row.get("observation")),
                StrictJson.text(row.get("selected_step")), GoalCodec.parsePlan(row.get("campaign_goal_plan_used")),
                row.get("government_context").isNull() ? Optional.empty() : Optional.of(GovernmentContextCodec.parseContext(row.get("government_context"))));
    }
}
