package org.xar.ck3.control.g2.m7;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.CheckpointContinuity.Observation;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.GoalPlan;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext.Context;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** In-process publication/reader port. It performs no query, action, file, or writer operation. */
public final class M7OrdinaryPlanConsumer {
    public static final String INPUT_SCHEMA = "xar.g2.m7.ordinary-plan-input/v1";
    public static final String OUTPUT_SCHEMA = "xar.g2.m7.ordinary-plan-consumption/v1";
    public static final int MAX_BYTES = 262_144;
    private M7OrdinaryPlanConsumer() { }

    /** Publication locations share one consumer, rather than separate goal rules. */
    public enum Publication {
        ORDINARY_PLAN("ordinary_plan"), CHECKPOINT_READER("checkpoint_reader"),
        SUCCESSOR_PLAN("successor_plan");
        private final String wire;
        Publication(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Publication fromWire(String wire) {
            for (Publication value : values()) if (value.wire.equals(wire)) return value;
            throw new IllegalArgumentException("unknown M7 publication location");
        }
    }

    public record Consumed(Publication publication, Observation observation, String selectedStep,
            GoalPlan campaignGoalPlanUsed, Optional<Context> campaignGovernmentContextUsed) {
        public Consumed {
            Objects.requireNonNull(publication); Objects.requireNonNull(observation);
            StrictJson.text(selectedStep); Objects.requireNonNull(campaignGoalPlanUsed);
            Objects.requireNonNull(campaignGovernmentContextUsed);
            StrictJson.require(campaignGoalPlanUsed.equals(OrdinaryCampaignGoal.plan(observation.goal())),
                    "published ordinary plan must consume the exact retained goal");
            StrictJson.require(observation.actorCharacterId() == observation.goal().currentCharacterId(),
                    "ordinary plan goal must belong to the observed current ruler");
            campaignGovernmentContextUsed.ifPresent(context -> bindContext(observation, context));
        }
        public boolean gameActionsSubmitted() { return false; }
        public boolean coldAuthorityGranted() { return false; }
        public boolean replayAuthorized() { return false; }
    }

    /** The original planner owns selectedStep. An absent government observation adds no query gate. */
    public static Consumed consume(Publication publication, Observation observation, String selectedStep,
            Optional<Context> governmentContext) {
        return new Consumed(publication, observation, selectedStep,
                OrdinaryCampaignGoal.plan(observation.goal()), governmentContext);
    }

    /** Host route: independently validated producer Context and domain Observation enter one consumer. */
    public static byte[] compose(byte[] originalInput) {
        ObjectNode row = StrictJson.object(StrictJson.parse(originalInput, MAX_BYTES), Set.of(
                "schema", "publication", "observation", "selected_step", "government_context"));
        StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "M7 consumer input schema differs");
        Optional<Context> context = context(row.get("government_context"));
        return encode(consume(Publication.fromWire(StrictJson.text(row.get("publication"))),
                CheckpointContinuity.parseObservation(row.get("observation")),
                StrictJson.text(row.get("selected_step")), context));
    }

    /** Explicit JSON value-domain serialization, with the domain codecs as the only field authorities. */
    public static byte[] encode(Consumed value) {
        ObjectNode row = StrictJson.object();
        row.put("schema", OUTPUT_SCHEMA); row.put("publication", value.publication().wire());
        row.set("observation", StrictJson.parse(CheckpointContinuity.encodeObservation(value.observation()), MAX_BYTES));
        row.put("selected_step", value.selectedStep());
        row.set("campaign_goal_plan_used", StrictJson.parse(GoalCodec.encodePlan(value.campaignGoalPlanUsed()), MAX_BYTES));
        if (value.campaignGovernmentContextUsed().isPresent()) {
            row.set("campaign_government_context_used", StrictJson.parse(
                    GovernmentContextCodec.encode(value.campaignGovernmentContextUsed().orElseThrow()), MAX_BYTES));
        } else row.putNull("campaign_government_context_used");
        row.put("game_actions_submitted", false); row.put("cold_authority_granted", false); row.put("replay_authorized", false);
        return raw(row);
    }

    /** Fresh persistence reader: replays no action and rejects drift in the goal-derived plan. */
    public static Consumed decode(byte[] persisted) {
        ObjectNode row = StrictJson.object(StrictJson.parse(persisted, MAX_BYTES), Set.of(
                "schema", "publication", "observation", "selected_step", "campaign_goal_plan_used",
                "campaign_government_context_used", "game_actions_submitted", "cold_authority_granted", "replay_authorized"));
        StrictJson.require(OUTPUT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "M7 consumer output schema differs");
        falseValue(row.get("game_actions_submitted")); falseValue(row.get("cold_authority_granted")); falseValue(row.get("replay_authorized"));
        return new Consumed(Publication.fromWire(StrictJson.text(row.get("publication"))),
                CheckpointContinuity.parseObservation(row.get("observation")),
                StrictJson.text(row.get("selected_step")), GoalCodec.parsePlan(row.get("campaign_goal_plan_used")),
                context(row.get("campaign_government_context_used")));
    }

    private static Optional<Context> context(JsonNode value) {
        StrictJson.require(value != null, "explicit nullable government context required");
        return value.isNull() ? Optional.empty() : Optional.of(GovernmentContextCodec.parseContext(value));
    }

    private static void bindContext(Observation frame, Context context) {
        GovernmentContextCodec.requireCurrentPlayerBinding(context, BigInteger.valueOf(frame.actorCharacterId()));
        StrictJson.require(Objects.equals(context.campaignId(), frame.goal().campaignId())
                && Objects.equals(context.currentCharacterId(), BigInteger.valueOf(frame.actorCharacterId()))
                && Objects.equals(context.snapshotRevision(), BigInteger.valueOf(frame.nativeRevision()))
                && Objects.equals(context.dateRaw(), BigInteger.valueOf(frame.dateRaw())),
                "government context and retained goal belong to the same current ruler frame");
        if (context.governmentKey() != null || context.identityObservationReady()) {
            StrictJson.require(Objects.equals(context.governmentKey(), frame.governmentKey()),
                    "observed government key differs from the consumer frame");
        }
        if (context.adapterFamily() != null || context.identityObservationReady()) {
            StrictJson.require(Objects.equals(context.adapterFamily(), frame.adapterFamily()),
                    "adapter family differs from the consumer frame");
        }
    }

    private static void falseValue(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean() && !value.booleanValue(),
                "M7 plan consumption never grants action, replay, or cold authority");
    }

    private static byte[] raw(JsonNode value) {
        StrictJson.require(value != null, "missing JSON value cannot be serialized");
        // Preserved native metadata may contain decimals; it is not a canonical identity document.
        byte[] encoded = value.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(encoded.length > 0 && encoded.length <= MAX_BYTES, "M7 consumer JSON exceeds explicit budget");
        return encoded;
    }
}
