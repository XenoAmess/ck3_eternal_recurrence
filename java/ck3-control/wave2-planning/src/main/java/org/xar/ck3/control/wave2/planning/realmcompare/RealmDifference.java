package org.xar.ck3.control.wave2.planning.realmcompare;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.wave2.planning.scoreinputs.ScoreInputFrame;

/** Closed pure previous/current county-set comparison from the original producer. */
public sealed interface RealmDifference {
    ObjectNode toJson();

    /** Immutable existing observation plus its complete county index; no parse, query or cache authority. */
    final class PreparedCurrent {
        private final RealmObservation observation;
        private final Set<Integer> countyTitleIds;
        private PreparedCurrent(RealmObservation observation) {
            require(observation != null, "current_complete_observation_unavailable");
            this.observation = observation;
            this.countyTitleIds = java.util.Collections.unmodifiableSet(new TreeSet<>(observation.component().countyTitleIds()));
        }
        public RealmObservation observation() { return observation; }
    }
    static PreparedCurrent prepare(RealmObservation observation) { return new PreparedCurrent(observation); }

    record Unavailable(String reason) implements RealmDifference {
        public Unavailable {
            StrictJson.text(reason);
            require(reason.codePointCount(0, reason.length()) <= 256, "bounded rejection reason required");
        }
        @Override public ObjectNode toJson() {
            ObjectNode object = StrictJson.object(); object.put("status", "unavailable");
            object.putNull("lost_county_title_ids"); object.putNull("gained_county_title_ids");
            object.put("unavailable_reason", reason);
            return object;
        }
    }
    record Available(List<Integer> lostCountyTitleIds, List<Integer> gainedCountyTitleIds,
            ObjectNode beforeSourceFrame, ObjectNode afterSourceFrame) implements RealmDifference {
        public Available {
            require(lostCountyTitleIds != null && gainedCountyTitleIds != null
                    && beforeSourceFrame != null && afterSourceFrame != null, "actual difference and original frames required");
            lostCountyTitleIds = List.copyOf(lostCountyTitleIds); gainedCountyTitleIds = List.copyOf(gainedCountyTitleIds);
            validateSet(lostCountyTitleIds); validateSet(gainedCountyTitleIds);
            require(java.util.Collections.disjoint(lostCountyTitleIds, gainedCountyTitleIds), "lost/gained sets cannot overlap");
            beforeSourceFrame = beforeSourceFrame.deepCopy(); afterSourceFrame = afterSourceFrame.deepCopy();
        }
        @Override public ObjectNode beforeSourceFrame() { return beforeSourceFrame.deepCopy(); }
        @Override public ObjectNode afterSourceFrame() { return afterSourceFrame.deepCopy(); }
        @Override public ObjectNode toJson() {
            ObjectNode object = StrictJson.object(); object.put("status", "available");
            ArrayNode lost = object.putArray("lost_county_title_ids"); lostCountyTitleIds.forEach(lost::add);
            ArrayNode gained = object.putArray("gained_county_title_ids"); gainedCountyTitleIds.forEach(gained::add);
            object.putNull("unavailable_reason"); object.set("before_source_frame", beforeSourceFrame.deepCopy());
            object.set("after_source_frame", afterSourceFrame.deepCopy()); object.putNull("cause");
            return object;
        }
        private static void validateSet(List<Integer> ids) {
            require(ids.size() <= 16_384, "difference count exceeds actual component bound");
            int previous = 0;
            for (int identity : ids) { require(identity > previous, "sorted unique positive full county IDs required"); previous = identity; }
        }
    }

    static RealmDifference compare(JsonNode previous, JsonNode observation) {
        return compareSupplied(previous, () -> prepare(RealmObservation.parse(observation)));
    }

    /** Reuses the exact already-validated observation from RealmMembershipFeedback. */
    static RealmDifference compareObservation(JsonNode previous, RealmObservation observation) {
        return compareSupplied(previous, () -> prepare(observation));
    }

    static RealmDifference comparePrepared(JsonNode previous, PreparedCurrent observation) {
        return compareSupplied(previous, () -> observation);
    }

    private static RealmDifference compareSupplied(JsonNode previous, java.util.function.Supplier<PreparedCurrent> supplied) {
        if (!(previous instanceof ObjectNode oldObservation)
                || !SubrealmCounties.text(oldObservation.get("schema"), RealmObservation.SCHEMA)) {
            return new Unavailable("previous_complete_observation_missing");
        }
        try {
            PreparedCurrent prepared = supplied.get();
            require(prepared != null, "current_complete_observation_unavailable");
            RealmObservation current = prepared.observation;
            if (!(oldObservation.get("source_frame") instanceof ObjectNode old)
                    || !SubrealmCounties.text(old.get("schema"), "xar.ck3.planning-source-frame/v1")
                    || !SubrealmCounties.text(old.get("status"), "complete")
                    || !sameJson(oldObservation.get("provenance"), current.provenance())) {
                return new Unavailable("previous_source_scope_unqualified");
            }
            ObjectNode now = current.sourceFrame();
            for (String key : new String[] {"actor_character_id", "episode_run_id", "bridge_pid", "connection_generation"}) {
                if (!sameOwnerField(old.get(key), now.get(key), key)) {
                    return new Unavailable("previous_owner_continuity_unqualified:" + key);
                }
            }
            ScoreInputFrame before = RealmObservation.frame(old, "previous_frame_incomplete");
            ScoreInputFrame after = current.frame();
            JsonNode query = oldObservation.get("query_sequence");
            if (before.dateRaw() > after.dateRaw() || before.nativeRevision().compareTo(after.nativeRevision()) >= 0
                    || before.revision().compareTo(after.revision()) >= 0 || query == null || !query.isIntegralNumber()
                    || query.bigIntegerValue().signum() < 1 || query.bigIntegerValue().compareTo(current.querySequence()) >= 0) {
                return new Unavailable("previous_source_not_strictly_earlier");
            }
            if (!SubrealmCounties.text(oldObservation.get("status"), "available")) { return new Unavailable("previous_observation_unavailable"); }
            SubrealmCounties oldComponent = SubrealmCounties.parse(oldObservation.get("component"), before.actorCharacterId().intValueExact(),
                    before.nativeRevision(), before.dateRaw());
            if (!oldComponent.complete()) { return new Unavailable("previous_membership_incomplete"); }
            Set<Integer> oldIds = new TreeSet<>(oldComponent.countyTitleIds());
            Set<Integer> newIds = prepared.countyTitleIds;
            Set<Integer> lost = new TreeSet<>(oldIds); lost.removeAll(newIds);
            Set<Integer> gained = new TreeSet<>(newIds); gained.removeAll(oldIds);
            return new Available(List.copyOf(lost), List.copyOf(gained), old, now);
        } catch (ContractViolationException | org.xar.ck3.control.contracts.projection.ProjectionDomainRejection error) {
            String message = error.getMessage();
            if (message == null || message.isEmpty()) { message = "realm_membership_comparison_invalid"; }
            int end = message.offsetByCodePoints(0, Math.min(256, message.codePointCount(0, message.length())));
            return new Unavailable(message.substring(0, end));
        }
    }

    private static boolean sameJson(JsonNode left, JsonNode right) { return left != null && right != null && left.equals(right); }
    private static boolean sameOwnerField(JsonNode left, JsonNode right, String field) {
        if (left == null || right == null || left.isNull() || right.isNull()) { return false; }
        if (field.equals("episode_run_id")) { return left.isTextual() && right.isTextual() && left.textValue().equals(right.textValue()); }
        return left.isIntegralNumber() && right.isIntegralNumber() && left.bigIntegerValue().equals(right.bigIntegerValue());
    }
}
