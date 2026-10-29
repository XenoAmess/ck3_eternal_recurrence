package org.xar.ck3.control.application.planning.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.Episode;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Pure full-body bookkeeping after the actual same-Game natural successor publication.
 * A decoded transition is DATA only; persistence still requires the original private lifecycle proof and writer. */
public final class FamilyNaturalEpisodeMigration {
    public static final String FIELD = "java_natural_episode";
    public static final String SCHEMA = "xar.java.family-natural-episode-binding/v1";
    private FamilyNaturalEpisodeMigration() { }

    public record Transition(SessionIdentity owner, Episode before, Episode after,
            ExactRef lifecycleMaterial, ExactRef previousBody) {
        public Transition {
            Objects.requireNonNull(owner); Objects.requireNonNull(before); Objects.requireNonNull(after);
            Objects.requireNonNull(lifecycleMaterial); Objects.requireNonNull(previousBody);
            StrictJson.require(!before.runId().equals(after.runId()) && !before.player().equals(after.player())
                    && lifecycleMaterial.bytes() > 0 && previousBody.bytes() > 0,
                    "natural succession requires distinct actual episodes/players and full original materials");
        }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object().put("schema", SCHEMA);
            value.set("owner", OrdinaryCycleTransitions.sessionToJson(owner));
            value.set("before_episode", episode(before)); value.set("after_episode", episode(after));
            value.set("lifecycle_material", lifecycleMaterial.toJson()); value.set("previous_body", previousBody.toJson());
            return value;
        }
        public static Transition fromJson(JsonNode original) {
            ObjectNode value = StrictJson.object(original, Set.of("schema", "owner", "before_episode", "after_episode",
                    "lifecycle_material", "previous_body"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact natural Family binding schema required");
            return new Transition(OrdinaryCycleTransitions.sessionFromJson(value.get("owner")), readEpisode(value.get("before_episode")),
                    readEpisode(value.get("after_episode")), ExactRef.fromJson(value.get("lifecycle_material")), ExactRef.fromJson(value.get("previous_body")));
        }
    }

    /** The only accepted retry states are the retained full predecessor and its exact deterministic output. */
    public static void requireCompatibleCurrent(Slot slot, byte[] original, byte[] current, Transition transition) {
        FamilyDomainSource.validate(slot, current);
        byte[] expected = derive(slot, original, transition);
        StrictJson.require(Arrays.equals(original, current) || Arrays.equals(expected, current),
                "natural Family migration cannot replace another body or post-publication business mutation");
    }

    public static byte[] derive(Slot slot, byte[] original, Transition transition) {
        Objects.requireNonNull(transition);
        Obj validated = FamilyDomainSource.validate(slot, original);
        StrictJson.require(transition.previousBody().bytes() == original.length
                && transition.previousBody().sha256().equals(ActionCodec.sha256(original)), "natural Family predecessor pin differs");
        ObjectNode before = requireObject(DriverJson.toNode(validated)), after = before.deepCopy();
        requireBeforeBinding(before, transition.owner(), transition.before());
        for (String key : List.of("pending", "resolved")) {
            JsonNode value = before.get(key);
            StrictJson.require(value != null && (value.isNull() || value.isObject()), "full explicit Family records required");
            if (value.isObject()) {
                StrictJson.require(transition.before().runId().equals(StrictJson.text(value.get("episode_run_id"))),
                        "unrelated episode records cannot become natural clear state");
                if (value.has("played_character_id")) StrictJson.require(transition.before().player().equals(
                        FamilyNextEpisodeMigration.preservedPlayer(value.get("played_character_id"))), "natural Family record has another actual player");
            }
        }
        ArrayNode history;
        if (before.has("episode_history")) {
            StrictJson.require(before.get("episode_history") instanceof ArrayNode, "original Family episode history must be an array");
            history = (ArrayNode)after.get("episode_history");
            for (JsonNode entry : history) StrictJson.require(entry.isObject(), "complete original Family history entries required");
        } else history = after.putArray("episode_history");
        ObjectNode entry = history.addObject().put("source", "committed_natural_successor_publication")
                .put("source_episode_run_id", transition.before().runId()).put("successor_episode_run_id", transition.after().runId())
                .put("predecessor_character_id", transition.before().player()).put("successor_character_id", transition.after().player())
                .put("pending_status", before.get("pending").isObject() ? "retained_original_unresolved_no_replay" : "no_active_predecessor_pending")
                .put("ck3_command_submitted", false).put("relation_completion_credit", false);
        entry.set("pending", before.get("pending").deepCopy()); entry.set("resolved", before.get("resolved").deepCopy());
        entry.set("previous_body", transition.previousBody().toJson()); entry.set("lifecycle_material", transition.lifecycleMaterial().toJson());
        if (before.has(FamilyNextEpisodeMigration.FIELD)) entry.set("previous_next_episode_binding", before.get(FamilyNextEpisodeMigration.FIELD).deepCopy());
        if (before.has(FIELD)) entry.set("previous_natural_episode_binding", before.get(FIELD).deepCopy());
        after.putNull("pending"); after.putNull("resolved"); after.remove(FamilyNextEpisodeMigration.FIELD); after.set(FIELD, transition.toJson());
        byte[] result = StrictJson.canonical(after, ContinuityJson.DOMAIN_MAX_BYTES);
        FamilyDomainSource.validate(slot, result); return result;
    }

    /** Shared identity check also used by the later physical NEXT producer before it archives a natural binding. */
    public static void requireBeforeBinding(ObjectNode body, SessionIdentity owner, Episode before) {
        Objects.requireNonNull(body); Objects.requireNonNull(owner); Objects.requireNonNull(before);
        StrictJson.require(!(body.has(FIELD) && body.has(FamilyNextEpisodeMigration.FIELD)), "Family episode bindings are mutually exclusive");
        if (body.has(FIELD)) {
            Transition prior = Transition.fromJson(body.get(FIELD));
            StrictJson.require(prior.owner().equals(owner) && prior.after().equals(before), "previous natural Family body belongs to another actual owner/episode");
        }
        if (body.has(FamilyNextEpisodeMigration.FIELD)) {
            var prior = FamilyNextEpisodeMigration.Transition.fromJson(body.get(FamilyNextEpisodeMigration.FIELD));
            StrictJson.require(prior.afterOwner().equals(owner) && prior.after().equals(before), "previous NEXT Family body belongs to another actual owner/episode");
        }
    }

    public static void requireCurrent(Obj body, PlanningRequest actual) {
        ObjectNode value = requireObject(DriverJson.toNode(body));
        StrictJson.require(!value.has(FamilyNextEpisodeMigration.FIELD), "natural and NEXT Family bindings cannot both be current");
        Transition binding = Transition.fromJson(value.get(FIELD)); binding.owner().require(actual);
        Episode after = binding.after(); JsonNode snapshot = DriverJson.toNode(actual.observations().snapshot());
        StrictJson.require(after.runId().equals(actual.before().frame().episodeRunId())
                && after.player().equals(actual.before().frame().identity().player())
                && after.runId().equals(StrictJson.text(snapshot.get("episode_run_id")))
                && after.player().equals(FamilyNextEpisodeMigration.currentPlayer(snapshot.path("played_character").get("character_id"))),
                "natural Family body crossed actual successor episode/player");
    }
    private static ObjectNode requireObject(JsonNode value) {
        if (!(value instanceof ObjectNode object)) throw new IllegalArgumentException("Family JSON object required"); return object;
    }
    private static ObjectNode episode(Episode value) { return StrictJson.object().put("episode_run_id", value.runId()).put("played_character_id", value.player()); }
    private static Episode readEpisode(JsonNode original) {
        ObjectNode value = StrictJson.object(original, Set.of("episode_run_id", "played_character_id"));
        return new Episode(StrictJson.text(value.get("episode_run_id")), FamilyNextEpisodeMigration.preservedPlayer(value.get("played_character_id")));
    }
}
