package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Conditional source knowledge; its serializer never grants material/action credit. */
public record WarOutcomeStakesResult(Status status, Reason reason, ObservationContext context,
        WarObservationFrame frame, int warId, Optional<WarSide> side,
        Optional<NativeTerminationOptions.CasusBelli> casusBelli, Optional<String> profileId,
        List<ReviewedSourceRegistry.Exposure> exposures, Map<String, String> consultedSources,
        QueryCollection queryCollection, Optional<BigInteger> querySequence,
        Optional<LiegeRelation> liegeRelation, JsonPresence<List<Integer>> targetTitles) {
    public static final String SCHEMA = "g2.war-outcome-stakes/v1";
    public enum Status { UNKNOWN, SOURCE_REVIEWED_CONDITIONAL }
    public enum Reason {
        SOURCE_REVIEWED_CONDITIONAL_EFFECTS, PAUSED_LIVING_PLAYER_NOT_OBSERVED,
        UNIQUE_ACTIVE_WAR_NOT_OBSERVED, UNIQUE_SAME_FRAME_CB_QUERY_NOT_OBSERVED,
        QUERY_FRAME_OR_WAR_IDENTITY_CHANGED, ACTIVE_CB_IDENTITY_NOT_OBSERVED,
        PRIMARY_PLAYER_ROLE_NOT_OBSERVED, EXACT_BUILD_CAMPAIGN_ROOT_NOT_OBSERVED,
        SOURCE_CONTRACT_NOT_CURRENT, CB_SIDE_PROFILE_NOT_REVIEWED, DEFENDER_LIEGE_RELATION_NOT_OBSERVED
    }
    public enum QueryCollection { NOT_EVALUATED, MISSING, NULL, EMPTY, ROWS }
    public enum LiegeRelation { IMMEDIATE_LIEGE_CHARACTER_ID, TOP_LIEGE_CHARACTER_ID }

    public WarOutcomeStakesResult {
        Objects.requireNonNull(status); Objects.requireNonNull(reason); Objects.requireNonNull(context);
        Objects.requireNonNull(frame); Objects.requireNonNull(side); Objects.requireNonNull(casusBelli);
        Objects.requireNonNull(profileId); Objects.requireNonNull(queryCollection);
        Objects.requireNonNull(querySequence); Objects.requireNonNull(liegeRelation); Objects.requireNonNull(targetTitles);
        require(warId > 0, "positive output WarID required");
        exposures = List.copyOf(exposures); consultedSources = Map.copyOf(consultedSources);
        profileId.ifPresent(StrictJson::text);
        consultedSources.forEach((path, sha) -> {
            StrictJson.text(path);
            require(path.startsWith("common/") && !path.contains("\\")
                && !List.of(path.split("/", -1)).contains(".."), "output source path differs");
            require(sha.matches("[0-9a-f]{64}"), "canonical output source SHA-256 required");
        });
        if (targetTitles.valueIfPresent().isPresent()) {
            List<Integer> titles = List.copyOf(targetTitles.valueIfPresent().orElseThrow());
            titles.forEach(title -> require(title > 0, "positive output target TitleID required"));
            targetTitles = new JsonPresence.Value<>(titles);
        }
        querySequence.ifPresent(sequence -> require(sequence.signum() > 0
            && sequence.compareTo(StrictJson.UINT64_MAX) <= 0, "output query sequence outside uint64"));
        if (status == Status.SOURCE_REVIEWED_CONDITIONAL) {
            require(reason == Reason.SOURCE_REVIEWED_CONDITIONAL_EFFECTS && profileId.isPresent()
                && !exposures.isEmpty() && !consultedSources.isEmpty() && side.isPresent()
                && casusBelli.isPresent() && querySequence.isPresent() && queryCollection == QueryCollection.ROWS,
                "conditional result is incomplete");
        } else {
            require(reason != Reason.SOURCE_REVIEWED_CONDITIONAL_EFFECTS && profileId.isEmpty()
                && exposures.isEmpty() && consultedSources.isEmpty(), "unknown cannot grant profile exposure");
        }
    }

    public ObjectNode toJson() {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        row.put("status", wire(status)); row.put("reason", wire(reason));
        row.set("observation_context", context.toJson()); row.put("source_registry_sha256", ReviewedSourceRegistry.SHA256);
        row.set("source_frame", frame.toJson()); row.put("war_id", warId);
        if (side.isPresent()) {
            row.put("player_side", side.orElseThrow().wire());
            row.put("absolute_player_defeat_outcome", side.orElseThrow() == WarSide.ATTACKER ? "attacker_defeat" : "attacker_victory");
        } else { row.putNull("player_side"); row.putNull("absolute_player_defeat_outcome"); }
        if (casusBelli.isPresent()) { row.set("active_casus_belli_identity", casusBelli.orElseThrow().toJson()); }
        else { row.putNull("active_casus_belli_identity"); }
        if (profileId.isPresent()) { row.put("profile_id", profileId.orElseThrow()); } else { row.putNull("profile_id"); }
        ArrayNode exposed = row.putArray("conditional_exposures"); exposures.forEach(value -> exposed.add(value.wire()));
        ObjectNode sources = row.putObject("consulted_source_sha256"); consultedSources.forEach(sources::put);
        row.put("termination_query_collection", wire(queryCollection));
        querySequence.ifPresent(value -> row.put("query_sequence", value));
        liegeRelation.ifPresent(value -> row.put("observed_defender_liege_relation", wire(value)));
        if (targetTitles instanceof JsonPresence.Null<?>) { row.putNull("observed_war_target_title_ids"); }
        else if (targetTitles.valueIfPresent().isPresent()) {
            ArrayNode titles = row.putArray("observed_war_target_title_ids");
            targetTitles.valueIfPresent().orElseThrow().forEach(titles::add);
        }
        row.put("actual_effects_verified", false); row.put("material_terms_complete", false);
        row.putNull("resolved_title_changes"); row.putNull("resource_deltas"); row.putNull("actual_war_result");
        row.put("automatic_surrender_qualified", false); row.put("continue_legal_war_processing", true);
        row.putNull("selected_action"); return row;
    }

    public byte[] toCanonicalBytes() { return StrictJson.canonical(toJson(), StrictJson.OUTPUT_MAX_BYTES); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(java.util.Locale.ROOT); }
}
