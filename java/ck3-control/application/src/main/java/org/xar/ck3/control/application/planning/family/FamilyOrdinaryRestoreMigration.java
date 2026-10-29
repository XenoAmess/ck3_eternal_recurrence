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

/** Pure same-episode physical rebind. Only the original private ORDINARY restore and writer may persist it. */
public final class FamilyOrdinaryRestoreMigration {
    public static final String SCHEMA = "xar.java.family-ordinary-restore-binding/v1";
    public static final String HISTORY = "ordinary_restore_history";
    private FamilyOrdinaryRestoreMigration() { }

    /** Saved source, actually replaced owner, and replacement are distinct roles, including on repeat restore. */
    public record Transition(SessionIdentity savedOwner, SessionIdentity beforeOwner, SessionIdentity afterOwner,
            Episode episode, ExactRef savedMaterial, ExactRef restorationBasis, ExactRef savedBody, ExactRef previousBody) {
        public Transition {
            Objects.requireNonNull(savedOwner); Objects.requireNonNull(beforeOwner); Objects.requireNonNull(afterOwner);
            Objects.requireNonNull(episode);
            for (ExactRef reference : List.of(savedMaterial, restorationBasis, savedBody, previousBody))
                StrictJson.require(Objects.requireNonNull(reference).bytes() > 0, "full ordinary restore originals required");
            StrictJson.require(savedOwner.machineId().equals(beforeOwner.machineId())
                    && beforeOwner.machineId().equals(afterOwner.machineId())
                    && !beforeOwner.game().equals(afterOwner.game())
                    && !beforeOwner.sessionId().equals(afterOwner.sessionId()),
                    "ordinary Family restore requires the actual same-machine replacement Game/session");
        }
        public ObjectNode toJson() {
            ObjectNode value = StrictJson.object().put("schema", SCHEMA);
            value.set("saved_owner", OrdinaryCycleTransitions.sessionToJson(savedOwner));
            value.set("before_owner", OrdinaryCycleTransitions.sessionToJson(beforeOwner));
            value.set("after_owner", OrdinaryCycleTransitions.sessionToJson(afterOwner));
            value.set("episode", StrictJson.object().put("episode_run_id", episode.runId()).put("played_character_id", episode.player()));
            value.set("saved_material", savedMaterial.toJson()); value.set("restoration_basis", restorationBasis.toJson());
            value.set("saved_body", savedBody.toJson()); value.set("previous_body", previousBody.toJson());
            return value;
        }
        public static Transition fromJson(JsonNode original) {
            ObjectNode value = StrictJson.object(original, Set.of("schema", "saved_owner", "before_owner", "after_owner",
                    "episode", "saved_material", "restoration_basis", "saved_body", "previous_body"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact ordinary Family restore schema required");
            ObjectNode episode = StrictJson.object(value.get("episode"), Set.of("episode_run_id", "played_character_id"));
            return new Transition(OrdinaryCycleTransitions.sessionFromJson(value.get("saved_owner")),
                    OrdinaryCycleTransitions.sessionFromJson(value.get("before_owner")),
                    OrdinaryCycleTransitions.sessionFromJson(value.get("after_owner")),
                    new Episode(StrictJson.text(episode.get("episode_run_id")),
                            FamilyNextEpisodeMigration.preservedPlayer(episode.get("played_character_id"))),
                    ExactRef.fromJson(value.get("saved_material")), ExactRef.fromJson(value.get("restoration_basis")),
                    ExactRef.fromJson(value.get("saved_body")), ExactRef.fromJson(value.get("previous_body")));
        }
    }

    /** A retry may observe its exact predecessor or exact output, never another pending mutation. */
    public static void requireCompatibleCurrent(Slot slot, byte[] saved, byte[] previous, byte[] current, Transition transition) {
        FamilyDomainSource.validate(slot, current);
        byte[] expected = derive(slot, saved, previous, transition);
        StrictJson.require(Arrays.equals(current, previous) || Arrays.equals(current, expected),
                "ordinary Family restore cannot overwrite a different canonical body or replay a pending mutation");
    }

    public static byte[] derive(Slot slot, byte[] saved, byte[] previous, Transition transition) {
        Objects.requireNonNull(transition);
        ObjectNode savedBody = object(DriverJson.toNode(FamilyDomainSource.validate(slot, saved)));
        ObjectNode before = object(DriverJson.toNode(FamilyDomainSource.validate(slot, previous)));
        requirePin(saved, transition.savedBody()); requirePin(previous, transition.previousBody());
        FamilyNaturalEpisodeMigration.requireBeforeBinding(savedBody, transition.savedOwner(), transition.episode());
        FamilyNaturalEpisodeMigration.requireBeforeBinding(before, transition.beforeOwner(), transition.episode());
        requireActiveEpisode(savedBody, transition.episode()); requireActiveEpisode(before, transition.episode());
        // Original ledgers without an episode marker acquire this current-owner guard from the retained restore entry.
        requireUnmarkedOwner(before, transition.beforeOwner(), transition.episode());
        ObjectNode after = before.deepCopy();
        ArrayNode history;
        if (before.has(HISTORY)) {
            StrictJson.require(before.get(HISTORY) instanceof ArrayNode, "ordinary Family restore history must be an array");
            history = (ArrayNode)after.get(HISTORY);
            for (JsonNode entry : history) requireHistoryEntry(entry);
        } else history = after.putArray(HISTORY);
        ObjectNode entry = history.addObject().put("ck3_command_submitted", false).put("relation_completion_credit", false);
        entry.set("transition", transition.toJson());
        entry.set("previous_next_episode_binding", before.has(FamilyNextEpisodeMigration.FIELD)
                ? before.get(FamilyNextEpisodeMigration.FIELD).deepCopy() : com.fasterxml.jackson.databind.node.NullNode.instance);
        entry.set("previous_natural_episode_binding", before.has(FamilyNaturalEpisodeMigration.FIELD)
                ? before.get(FamilyNaturalEpisodeMigration.FIELD).deepCopy() : com.fasterxml.jackson.databind.node.NullNode.instance);
        if (before.has(FamilyNaturalEpisodeMigration.FIELD)) {
            ObjectNode marker = object(before.get(FamilyNaturalEpisodeMigration.FIELD)).deepCopy();
            marker.set("owner", OrdinaryCycleTransitions.sessionToJson(transition.afterOwner()));
            FamilyNaturalEpisodeMigration.Transition.fromJson(marker); after.set(FamilyNaturalEpisodeMigration.FIELD, marker);
        }
        if (before.has(FamilyNextEpisodeMigration.FIELD)) {
            ObjectNode marker = object(before.get(FamilyNextEpisodeMigration.FIELD)).deepCopy();
            marker.set("after_owner", OrdinaryCycleTransitions.sessionToJson(transition.afterOwner()));
            FamilyNextEpisodeMigration.Transition.fromJson(marker); after.set(FamilyNextEpisodeMigration.FIELD, marker);
        }
        FamilyNaturalEpisodeMigration.requireBeforeBinding(after, transition.afterOwner(), transition.episode());
        // No business token, original pending/resolved record or earlier episode history is rewritten.
        for (String field : List.of("pending", "resolved", "episode_history"))
            StrictJson.require(Objects.equals(before.get(field), after.get(field)), "ordinary restore changed Family business state");
        byte[] result = StrictJson.canonical(after, ContinuityJson.DOMAIN_MAX_BYTES);
        FamilyDomainSource.validate(slot, result); return result;
    }

    /** Existing natural/NEXT guards remain authoritative; the restore entry guards previously unmarked originals. */
    public static void requireCurrent(Obj body, PlanningRequest actual) {
        ObjectNode value = object(DriverJson.toNode(body));
        if (!value.has(HISTORY)) return;
        StrictJson.require(value.get(HISTORY) instanceof ArrayNode, "ordinary Family restore history must be an array");
        for (JsonNode entry : value.get(HISTORY)) requireHistoryEntry(entry);
        if (value.has(FamilyNaturalEpisodeMigration.FIELD) || value.has(FamilyNextEpisodeMigration.FIELD)) return;
        Transition latest = latest(value);
        latest.afterOwner().require(actual);
        JsonNode snapshot = DriverJson.toNode(actual.observations().snapshot());
        StrictJson.require(latest.episode().runId().equals(actual.before().frame().episodeRunId())
                && latest.episode().player().equals(actual.before().frame().identity().player())
                && latest.episode().runId().equals(StrictJson.text(snapshot.get("episode_run_id")))
                && latest.episode().player().equals(FamilyNextEpisodeMigration.currentPlayer(snapshot.path("played_character").get("character_id"))),
                "ordinary Family restored body crossed its actual same episode/player");
    }
    private static void requireUnmarkedOwner(ObjectNode body, SessionIdentity owner, Episode episode) {
        if (body.has(FamilyNaturalEpisodeMigration.FIELD) || body.has(FamilyNextEpisodeMigration.FIELD) || !body.has(HISTORY)) return;
        Transition latest = latest(body);
        StrictJson.require(latest.afterOwner().equals(owner) && latest.episode().equals(episode),
                "unmarked Family body belongs to another actual restored owner/episode");
    }
    private static Transition latest(ObjectNode body) {
        StrictJson.require(body.get(HISTORY) instanceof ArrayNode && !body.get(HISTORY).isEmpty(),
                "nonempty ordinary Family restore history required");
        JsonNode latest = body.get(HISTORY).get(body.get(HISTORY).size() - 1); requireHistoryEntry(latest);
        return Transition.fromJson(latest.get("transition"));
    }
    private static void requireHistoryEntry(JsonNode original) {
        ObjectNode entry = StrictJson.object(original, Set.of("transition", "previous_next_episode_binding",
                "previous_natural_episode_binding", "ck3_command_submitted", "relation_completion_credit"));
        Transition.fromJson(entry.get("transition"));
        StrictJson.require(entry.get("ck3_command_submitted").isBoolean() && !entry.get("ck3_command_submitted").booleanValue()
                && entry.get("relation_completion_credit").isBoolean() && !entry.get("relation_completion_credit").booleanValue(),
                "ordinary Family bookkeeping cannot acquire submission or relationship credit");
        JsonNode next = entry.get("previous_next_episode_binding"), natural = entry.get("previous_natural_episode_binding");
        if (!next.isNull()) FamilyNextEpisodeMigration.Transition.fromJson(next);
        if (!natural.isNull()) FamilyNaturalEpisodeMigration.Transition.fromJson(natural);
        StrictJson.require(next.isNull() || natural.isNull(), "original Family episode markers are mutually exclusive");
    }
    private static void requireActiveEpisode(ObjectNode body, Episode episode) {
        for (String field : List.of("pending", "resolved")) {
            JsonNode value = body.get(field);
            StrictJson.require(value != null && (value.isNull() || value.isObject()), "explicit complete active Family records required");
            if (!value.isObject()) continue;
            StrictJson.require(episode.runId().equals(StrictJson.text(value.get("episode_run_id"))),
                    "ordinary restore cannot relabel another episode's active Family commitment");
            if (value.has("played_character_id")) StrictJson.require(episode.player().equals(
                    FamilyNextEpisodeMigration.preservedPlayer(value.get("played_character_id"))),
                    "ordinary restore cannot relabel another player's active Family commitment");
        }
    }
    private static void requirePin(byte[] bytes, ExactRef original) {
        StrictJson.require(bytes.length == original.bytes() && ActionCodec.sha256(bytes).equals(original.sha256()),
                "ordinary Family restore full original body pin differs");
    }
    private static ObjectNode object(JsonNode value) {
        if (!(value instanceof ObjectNode object)) throw new IllegalArgumentException("Family JSON object required");
        return object;
    }
}
