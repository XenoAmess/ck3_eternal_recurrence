package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.warpolicy.WarOutcomeStakesResult.Reason;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** In-process pure API. No per-war RPC, Game/Driver IO, effect evaluation or action submission. */
public final class WarOutcomeStakesProjector {
    public static final String REQUEST_SCHEMA = "g2.war-outcome-stakes-request/v1";
    private final ReviewedSourceRegistry registry;

    public WarOutcomeStakesProjector(ReviewedSourceRegistry registry) { this.registry = Objects.requireNonNull(registry); }

    /** Strict wrapper around existing SDK objects. Legacy object extensions stay source-bound. */
    public byte[] project(byte[] input) {
        ObjectNode request = StrictJson.object(StrictJson.parse(input), Set.of("schema", "war_id", "snapshot",
            "campaign_root", "current_source_sha256", "observation_context"));
        require(WarJson.textEquals(request.get("schema"), REQUEST_SCHEMA), "war stakes request schema differs");
        return project(request.get("snapshot"), WarJson.positive32(request.get("war_id")),
            request.get("campaign_root"), request.get("current_source_sha256"),
            ObservationContext.fromJson(request.get("observation_context"))).toCanonicalBytes();
    }

    public WarOutcomeStakesResult project(JsonNode snapshotValue, int warId,
            JsonNode rootValue, JsonNode currentSourceHashes, ObservationContext context) {
        require(warId > 0, "positive input WarID required"); Objects.requireNonNull(context);
        ObjectNode snapshot = WarJson.record(snapshotValue, "snapshot");
        WarObservationFrame frame = WarObservationFrame.fromSnapshot(snapshot);
        Partial result = new Partial(frame, warId, context);
        ObjectNode player = WarJson.record(snapshot.get("played_character"), "played_character");
        if (!WarJson.bool(snapshot.get("paused")) || !WarJson.bool(player.get("alive"))) {
            return result.unknown(Reason.PAUSED_LIVING_PLAYER_NOT_OBSERVED);
        }
        List<ObjectNode> wars = new ArrayList<>();
        for (JsonNode row : WarJson.array(snapshot.get("active_wars"), "active_wars")) {
            ObjectNode war = WarJson.record(row, "active war");
            if (WarJson.positive32(war.get("war_id")) == warId) { wars.add(war); }
        }
        if (wars.size() != 1) { return result.unknown(Reason.UNIQUE_ACTIVE_WAR_NOT_OBSERVED); }
        ObjectNode war = wars.getFirst();
        WarSide side = WarSide.fromJson(war.get("player_side")); result.side = Optional.of(side);
        boolean primary = WarJson.bool(war.get("player_is_primary_war_leader"));
        int score = WarJson.signed32(war.get("player_relative_war_score"));
        int opponent = WarJson.positive32(war.get("primary_opponent_character_id"));
        if (war.has("targeted_title_ids")) {
            JsonNode targets = war.get("targeted_title_ids");
            if (targets.isNull()) { result.targets = new JsonPresence.Null<>(); }
            else {
                List<Integer> titles = new ArrayList<>();
                for (JsonNode title : WarJson.array(targets, "targeted_title_ids")) { titles.add(WarJson.positive32(title)); }
                result.targets = new JsonPresence.Value<>(List.copyOf(titles));
            }
        }
        List<ObjectNode> queries = new ArrayList<>();
        if (!snapshot.has("war_termination_options")) { result.collection = WarOutcomeStakesResult.QueryCollection.MISSING; }
        else if (snapshot.get("war_termination_options").isNull()) { result.collection = WarOutcomeStakesResult.QueryCollection.NULL; }
        else {
            List<ObjectNode> all = new ArrayList<>();
            for (JsonNode row : WarJson.array(snapshot.get("war_termination_options"), "war_termination_options")) {
                all.add(WarJson.record(row, "war_termination_options[]"));
            }
            result.collection = all.isEmpty() ? WarOutcomeStakesResult.QueryCollection.EMPTY : WarOutcomeStakesResult.QueryCollection.ROWS;
            for (ObjectNode query : all) { if (WarJson.positive32(query.get("war_id")) == warId) { queries.add(query); } }
        }
        if (queries.size() != 1) { return result.unknown(Reason.UNIQUE_SAME_FRAME_CB_QUERY_NOT_OBSERVED); }
        // Validate the complete native query before considering a stale frame unknown.
        NativeTerminationOptions query = NativeTerminationOptions.fromCache(queries.getFirst(), warId);
        result.sequence = Optional.of(query.binding().sequence());
        if (!query.binding().matches(frame) || query.side() != side || query.primary() != primary || query.relativeScore() != score) {
            return result.unknown(Reason.QUERY_FRAME_OR_WAR_IDENTITY_CHANGED);
        }
        if (query.activeCasusBelli() != NativeTerminationOptions.Truth.TRUE || query.casusBelli().isEmpty()) {
            return result.unknown(Reason.ACTIVE_CB_IDENTITY_NOT_OBSERVED);
        }
        result.cb = query.casusBelli();
        if (!primary) { return result.unknown(Reason.PRIMARY_PLAYER_ROLE_NOT_OBSERVED); }
        String cbKey = result.cb.orElseThrow().canonicalKey();
        Optional<ReviewedSourceRegistry.Profile> matching = registry.profiles().stream()
            .filter(profile -> profile.canonicalKey().equals(cbKey) && profile.side() == side).findFirst();
        if (matching.isEmpty()) { return result.unknown(Reason.CB_SIDE_PROFILE_NOT_REVIEWED); }
        ReviewedSourceRegistry.Profile profile = matching.orElseThrow();
        ObjectNode root = WarJson.nullValue(rootValue) ? StrictJson.object() : WarJson.record(rootValue, "campaign_root");
        if (!rootIsCurrent(root, frame)) { return result.unknown(Reason.EXACT_BUILD_CAMPAIGN_ROOT_NOT_OBSERVED); }
        ObjectNode supplied = WarJson.nullValue(currentSourceHashes) ? StrictJson.object() : WarJson.record(currentSourceHashes, "current_source_sha256");
        Map<String, String> expected = new LinkedHashMap<>();
        for (ReviewedSourceRegistry.Source source : registry.sources()) {
            if (profile.sourcePaths().contains(source.path())) { expected.put(source.path(), source.sha256()); }
        }
        Map<String, String> actual = new LinkedHashMap<>();
        for (String path : expected.keySet()) { if (supplied.has(path)) { actual.put(path, WarJson.sha(supplied.get(path))); } }
        if (!actual.equals(expected)) { return result.unknown(Reason.SOURCE_CONTRACT_NOT_CURRENT); }
        if (profile.requireObservedDefenderLiege()) {
            ObjectNode readiness = WarJson.record(root.get("readiness"), "root.readiness");
            Integer immediate = nullableLiege(root.get("immediate_liege_character_id"));
            Integer top = nullableLiege(root.get("top_liege_character_id"));
            if (!WarJson.actualFalse(root.get("independent")) || !WarJson.actualTrue(readiness.get("lieges_ready"))
                    || opponent == frame.playedCharacterId() || !(Objects.equals(opponent, immediate) || Objects.equals(opponent, top))) {
                return result.unknown(Reason.DEFENDER_LIEGE_RELATION_NOT_OBSERVED);
            }
            result.relation = Optional.of(Objects.equals(opponent, immediate)
                ? WarOutcomeStakesResult.LiegeRelation.IMMEDIATE_LIEGE_CHARACTER_ID
                : WarOutcomeStakesResult.LiegeRelation.TOP_LIEGE_CHARACTER_ID);
        }
        return new WarOutcomeStakesResult(WarOutcomeStakesResult.Status.SOURCE_REVIEWED_CONDITIONAL,
            Reason.SOURCE_REVIEWED_CONDITIONAL_EFFECTS, context, frame, warId, result.side, result.cb,
            Optional.of(profile.profileId()), profile.exposures(), expected, result.collection,
            result.sequence, result.relation, result.targets);
    }

    private boolean rootIsCurrent(ObjectNode root, WarObservationFrame frame) {
        if (!WarJson.textEquals(root.get("status"), "available")) { return false; }
        int actor = WarJson.positive32(root.get("player_character_id"));
        BigInteger revision = WarJson.positive64(root.get("snapshot_revision"));
        int date = WarJson.signed32(root.get("date_raw"));
        ObjectNode provenance = WarJson.record(root.get("provenance"), "root.provenance");
        return actor == frame.playedCharacterId() && revision.equals(frame.nativeRevision()) && date == frame.dateRaw()
            && WarJson.actualTrue(root.get("player_character_alive"))
            && WarJson.textEquals(provenance.get("game_version"), registry.gameVersion())
            // Preserve the oracle's exact uppercase root-provenance contract.
            && WarJson.textEquals(provenance.get("executable_sha256"), WarJson.EXECUTABLE_SHA256)
            && WarJson.textEquals(provenance.get("backend_id"), WarJson.ROOT_BACKEND);
    }

    private static Integer nullableLiege(JsonNode value) { return WarJson.nullValue(value) ? null : WarJson.positive32(value); }

    private static final class Partial {
        final WarObservationFrame frame; final int warId; final ObservationContext context;
        Optional<WarSide> side = Optional.empty(); Optional<NativeTerminationOptions.CasusBelli> cb = Optional.empty();
        WarOutcomeStakesResult.QueryCollection collection = WarOutcomeStakesResult.QueryCollection.NOT_EVALUATED;
        Optional<BigInteger> sequence = Optional.empty(); Optional<WarOutcomeStakesResult.LiegeRelation> relation = Optional.empty();
        JsonPresence<List<Integer>> targets = new JsonPresence.Missing<>();
        Partial(WarObservationFrame frame, int warId, ObservationContext context) {
            this.frame = frame; this.warId = warId; this.context = context;
        }
        WarOutcomeStakesResult unknown(Reason reason) {
            return new WarOutcomeStakesResult(WarOutcomeStakesResult.Status.UNKNOWN, reason, context,
                frame, warId, side, cb, Optional.empty(), List.of(), Map.of(), collection, sequence, relation, targets);
        }
    }
}
