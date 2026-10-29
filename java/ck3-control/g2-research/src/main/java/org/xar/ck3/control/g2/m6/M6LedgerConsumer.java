package org.xar.ck3.control.g2.m6;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Stamp;
import org.xar.ck3.control.wave2.planning.swaymaterial.SwayMaterialReducer;

/** Immutable ordinary-turn proposal over the current and archived original episodes. */
public final class M6LedgerConsumer {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final List<String> OBSERVATIONS = List.of("phase_intervention", "material_intervention",
            "first_named_gain_intervention", "terminal_intervention", "stop_intervention");
    private M6LedgerConsumer() { }

    public enum TurnKind { ORDINARY_AUTO, OBSERVATION_ONLY }

    public record Result(ProjectionJson ledger, int episodesChanged,
            int observationsConsumed) {
        public Result {
            Objects.requireNonNull(ledger);
            StrictJson.require(episodesChanged >= 0 && observationsConsumed >= 0, "negative consumer accounting");
        }
        public boolean ledgerCommitted() { return false; }
        public boolean actionAuthorized() { return false; }
    }

    /** Uses the existing material following reducer; this method performs no I/O or submission. */
    public static Result followingTurn(byte[] originalLedger, G2Source source, long currentActor,
            Stamp following, TurnKind kind) {
        Objects.requireNonNull(source); Objects.requireNonNull(following); Objects.requireNonNull(kind);
        StrictJson.require(currentActor > 0 && currentActor <= 0xffff_ffffL, "full current actor required");
        M6SourceProducer.fromClosedLedger(originalLedger, source);
        ProjectionJson original = ProjectionJson.object(originalLedger, ProjectionJson.MAX_BYTES);
        if (kind != TurnKind.ORDINARY_AUTO) { return new Result(original, 0, 0); }
        ObjectNode ledger = object(StrictJson.parse(originalLedger));
        JsonNode resolvedValue = ledger.get("resolved");
        if (resolvedValue == null || resolvedValue.isNull()) { return new Result(original, 0, 0); }
        ObjectNode resolved = object(resolvedValue);
        Counts counts = consumeTree(resolved, currentActor, following);
        if (counts.episodes() == 0) { return new Result(original, 0, 0); }
        byte[] encoded = bytes(ledger);
        return new Result(ProjectionJson.object(encoded, ProjectionJson.MAX_BYTES), counts.episodes(), counts.observations());
    }

    private record Counts(int episodes, int observations) { }

    private static Counts consumeTree(ObjectNode episode, long actor, Stamp following) {
        int count = consumeEpisode(episode, actor, following);
        int episodes = count == 0 ? 0 : 1;
        JsonNode previous = episode.get("previous_interventions");
        if (previous != null && !previous.isNull()) {
            StrictJson.require(previous.isArray(), "archived episode list required");
            for (JsonNode value : (ArrayNode) previous) {
                Counts child = consumeTree(object(value), actor, following);
                episodes += child.episodes(); count += child.observations();
            }
        }
        return new Counts(episodes, count);
    }

    private static int consumeEpisode(ObjectNode episode, long actor, Stamp following) {
        if (StrictJson.integer(episode.get("actor_character_id"), 1, 0xffff_ffffL) != actor) { return 0; }
        int consumed = 0;
        JsonNode startConsumed = episode.get("next_turn_consumed");
        if (startConsumed != null && !startConsumed.isNull()) {
            StrictJson.require(startConsumed.isBoolean(), "start consumption must retain a boolean token");
        }
        if (startConsumed == null || !startConsumed.isBoolean() || !startConsumed.booleanValue()) {
            BigInteger startRevision = integer(episode.get("post_native_revision"));
            int startDate = Math.toIntExact(StrictJson.integer(episode.get("post_date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE));
            if (following.nativeRevision().compareTo(startRevision) > 0 || following.dateRaw() > startDate) {
                episode.put("next_turn_consumed", true);
                episode.put("following_native_revision", following.nativeRevision());
                episode.put("following_date_raw", following.dateRaw());
                consumed++;
            }
        }
        for (String key : OBSERVATIONS) {
            JsonNode value = episode.get(key);
            if (value == null || value.isNull()) { continue; }
            ObjectNode observation = object(value);
            if (key.equals("stop_intervention") && !isTrue(observation.get("postcondition_verified"))) { continue; }
            if (key.equals("first_named_gain_intervention") && !matchingFirstGain(episode, observation)) { continue; }
            ObjectNode input = StrictJson.object();
            input.set("material", observation.deepCopy()); input.put("actor_character_id", actor);
            input.put("native_revision", following.nativeRevision()); input.put("date_raw", following.dateRaw());
            var result = SwayMaterialReducer.following(bytes(input));
            if (result.isPresent()) {
                episode.set(key, StrictJson.parse(result.orElseThrow().toJson()));
                consumed++;
            }
        }
        return consumed;
    }

    private static boolean matchingFirstGain(ObjectNode episode, ObjectNode gain) {
        if (!isTrue(gain.get("incremental_named_gain_observed"))) { return false; }
        for (String key : List.of("action_id", "actor_character_id", "target_character_id")) {
            if (!Objects.equals(episode.get(key), gain.get(key))) { return false; }
        }
        JsonNode identity = episode.get("native_receipt");
        if (identity == null || identity.isNull()) { identity = episode.get("recovered_instance_observation"); }
        if (identity == null || !identity.isObject()) { return false; }
        return Objects.equals(identity.get("scheme_instance_id"), gain.get("scheme_instance_id"))
                && Objects.equals(identity.get("scheme_instance_generation"), gain.get("scheme_instance_generation"));
    }

    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact source integer required");
        return value.bigIntegerValue();
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "source object required");
        return (ObjectNode) value;
    }
    private static boolean isTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); }
        catch (IOException failure) { throw new ContractViolationException("consumer JSON serialization failed", failure); }
    }
}
