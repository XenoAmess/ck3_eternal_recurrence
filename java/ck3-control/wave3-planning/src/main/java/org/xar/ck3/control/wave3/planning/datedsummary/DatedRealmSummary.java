package org.xar.ck3.control.wave3.planning.datedsummary;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmObservation;
import org.xar.ck3.control.wave2.planning.scoreinputs.ScoreInputFrame;
import org.xar.ck3.control.wave2.planning.scoreinputs.ScoreInputFrameAssessment.Field;
import org.xar.ck3.control.wave3.planning.realmmembership.RealmMembershipFeedback.VerifiedFeedback;

/** Pure dated planner summary, without service slot/lock/query or a native freshness grant. */
public final class DatedRealmSummary {
    public static final String FEEDBACK_SCHEMA = "xar.ck3.realm-membership-feedback/v1";
    private DatedRealmSummary() { }

    /** Production port: only the complete shared factory creates this verified internal fact. */
    public static Result fromVerified(VerifiedFeedback feedback, byte[] currentSourceFrameBytes) {
        require(feedback != null, "actual complete feedback factory result required");
        RealmObservation observation = feedback.observation();
        RealmDifference.Available delta = feedback.difference() instanceof RealmDifference.Available available
                ? availableDelta(available.toJson(), observation) : null;
        JsonNode current = DatedSummaryCodec.parseValue(currentSourceFrameBytes);
        Status status = current instanceof ObjectNode && current.equals(observation.sourceFrame()) ? Status.CURRENT : Status.HISTORICAL;
        return new Retained(status, observation, delta);
    }

    public sealed interface Result permits NoQualifiedObservation, Retained {
        ObjectNode toJson();
    }
    public static final class NoQualifiedObservation implements Result {
        private NoQualifiedObservation() { }
        @Override public ObjectNode toJson() {
            ObjectNode object = StrictJson.object(); object.put("status", "unavailable");
            object.putNull("current_realm_county_count"); object.putNull("loss_observed");
            object.put("unavailable_reason", "no_qualified_realm_observation"); return object;
        }
    }
    public enum Status {
        CURRENT("current"), HISTORICAL("historical");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public static final class Retained implements Result {
        private final Status status;
        private final RealmObservation observation;
        private final RealmDifference.Available delta;
        private Retained(Status status, RealmObservation observation, RealmDifference.Available delta) {
            this.status = status; this.observation = observation; this.delta = delta;
        }
        public Status status() { return status; }
        public int lastObservedRealmCountyCount() { return observation.component().countyTitleIds().size(); }
        public ScoreInputFrame observedFrame() { return observation.frame(); }
        @Override public ObjectNode toJson() {
            ObjectNode object = StrictJson.object(); object.put("status", status.wire());
            int count = lastObservedRealmCountyCount();
            if (status == Status.CURRENT) { object.put("current_realm_county_count", count); }
            else { object.putNull("current_realm_county_count"); }
            object.put("last_observed_realm_county_count", count);
            object.set("source_frame", observation.sourceFrame()); object.put("query_sequence", observation.querySequence());
            if (delta == null) {
                object.putNull("loss_observed"); object.putNull("lost_county_count"); object.putNull("gained_county_count");
                object.putNull("lost_county_title_ids_first8"); object.put("loss_list_truncated", false);
                object.putNull("before_source_frame");
            } else {
                object.put("loss_observed", !delta.lostCountyTitleIds().isEmpty());
                object.put("lost_county_count", delta.lostCountyTitleIds().size()); object.put("gained_county_count", delta.gainedCountyTitleIds().size());
                ArrayNode first = object.putArray("lost_county_title_ids_first8");
                delta.lostCountyTitleIds().stream().limit(8).forEach(first::add);
                object.put("loss_list_truncated", delta.lostCountyTitleIds().size() > 8);
                object.set("before_source_frame", delta.beforeSourceFrame());
            }
            object.putNull("cause"); object.put("new_RPC_calls", 0); return object;
        }
    }

    static Result project(JsonNode feedback, JsonNode currentSourceFrame) {
        if (!(feedback instanceof ObjectNode object) || !text(object.get("status"), "available")) { return new NoQualifiedObservation(); }
        require(text(object.get("schema"), FEEDBACK_SCHEMA), "retained feedback schema unavailable");
        RealmObservation observation = RealmObservation.parse(object.get("observation"));
        RealmDifference.Available delta = null;
        if (object.get("difference") instanceof ObjectNode difference && text(difference.get("status"), "available")) {
            delta = availableDelta(difference, observation);
        }
        Status status = currentSourceFrame instanceof ObjectNode && currentSourceFrame.equals(observation.sourceFrame())
                ? Status.CURRENT : Status.HISTORICAL;
        return new Retained(status, observation, delta);
    }

    private static RealmDifference.Available availableDelta(ObjectNode input, RealmObservation observation) {
        ObjectNode difference = StrictJson.object(input, Set.of("status", "lost_county_title_ids", "gained_county_title_ids",
                "unavailable_reason", "before_source_frame", "after_source_frame", "cause"));
        require(difference.get("unavailable_reason").isNull() && difference.get("cause").isNull(), "unavailable reason/cause cannot masquerade as a proven difference");
        require(difference.get("before_source_frame") instanceof ObjectNode && difference.get("after_source_frame") instanceof ObjectNode,
                "actual before/after frame metadata required");
        ObjectNode before = (ObjectNode) difference.get("before_source_frame");
        ObjectNode after = (ObjectNode) difference.get("after_source_frame");
        require(after.equals(observation.sourceFrame()), "dated difference belongs to another observed source frame");
        require(text(before.get("schema"), observation.sourceFrame().path("schema").textValue())
                && text(before.get("status"), "complete"), "before difference frame scope incomplete");
        ObjectNode beforeProjection = StrictJson.object();
        for (Field field : Field.values()) {
            require(before.get(field.wire()) != null, "before difference frame missing identity");
            beforeProjection.set(field.wire(), before.get(field.wire()));
        }
        ScoreInputFrame old = ScoreInputFrame.fromJson(beforeProjection), now = observation.frame();
        require(old.actorCharacterId().equals(now.actorCharacterId()) && old.episodeRunId().equals(now.episodeRunId())
                && old.bridgePid() == now.bridgePid() && old.connectionGeneration().equals(now.connectionGeneration()),
                "dated difference owner continuity changed");
        require(old.nativeRevision().signum() > 0 && old.nativeRevision().compareTo(now.nativeRevision()) < 0
                && old.revision().compareTo(now.revision()) < 0 && old.dateRaw() <= now.dateRaw(), "dated difference source is not strictly earlier");
        RealmDifference.Available delta = new RealmDifference.Available(ids(difference.get("lost_county_title_ids")),
                ids(difference.get("gained_county_title_ids")), before, after);
        Set<Integer> currentIds = new HashSet<>(observation.component().countyTitleIds());
        require(currentIds.containsAll(delta.gainedCountyTitleIds())
                && java.util.Collections.disjoint(currentIds, delta.lostCountyTitleIds()), "dated difference contradicts the observed complete set");
        int previousCount = currentIds.size() - delta.gainedCountyTitleIds().size() + delta.lostCountyTitleIds().size();
        require(previousCount >= 0 && previousCount <= 16_384, "dated difference implies an over-cap previous set");
        return delta;
    }

    private static List<Integer> ids(JsonNode input) {
        require(input instanceof ArrayNode && input.size() <= 16_384, "bounded full county ID list required");
        List<Integer> values = new ArrayList<>(input.size());
        int previous = 0;
        for (JsonNode value : input) {
            int identity = (int) StrictJson.integer(value, 1, Integer.MAX_VALUE);
            require(identity > previous, "sorted unique full county ID list required");
            values.add(identity); previous = identity;
        }
        return List.copyOf(values);
    }
    private static boolean text(JsonNode node, String value) { return node != null && node.isTextual() && node.textValue().equals(value); }
}
