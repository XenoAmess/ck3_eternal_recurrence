package org.xar.ck3.control.wave2.military.warexitterms;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.warpolicy.WarSide;

/** In-process migration of the native-driver, service and summary-consumer data path. No RPC port. */
public final class WarExitTermsAdapter {
    private WarExitTermsAdapter() { }

    /** Native query sequence retains the original JSON integer uint64 domain, including values above signed long. */
    public record QuerySequence(BigInteger value) {
        public QuerySequence {
            require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0,
                    "native query_sequence requires positive uint64");
        }
    }
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
                        BigInteger connectionGeneration, String episodeRunId) {
        public Frame {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            require(revision != null && revision.signum() >= 0 && nativeRevision != null && nativeRevision.signum() >= 0
                    && connectionGeneration != null && connectionGeneration.signum() >= 0, "exact nonnegative frame integers required");
        }
        /** Public revision is not part of the original post-query native-frame comparator. It is part of cache binding. */
        public boolean sameNativeFrame(Frame other) {
            return other != null && snapshotId.equals(other.snapshotId) && nativeRevision.equals(other.nativeRevision)
                    && connectionGeneration.equals(other.connectionGeneration) && episodeRunId.equals(other.episodeRunId);
        }
    }
    public record BoundPreview(WarExitTerms terms, QuerySequence querySequence, Frame frame, String backendId) {
        public BoundPreview {
            require(terms != null && querySequence != null && frame != null, "complete bound preview required");
            StrictJson.text(backendId);
        }
    }
    /** The actual comparison consumer still lacks a campaign-outcome forecast. This never recommends an exit. */
    public record ComparisonInput(WarExitTerms structuredExitTerms, List<UnknownField> unknownFields) {
        public ComparisonInput {
            require(structuredExitTerms != null, "structured observed terms required");
            unknownFields = List.copyOf(unknownFields);
            require(unknownFields.equals(List.of(UnknownField.CAMPAIGN_OUTCOME_FORECAST))
                    || unknownFields.equals(List.of(UnknownField.CAMPAIGN_OUTCOME_FORECAST, UnknownField.OPPONENT_ACCEPTANCE)),
                    "campaign forecast remains unknown; all-option acceptance needs its own observation");
        }
        public boolean automaticTerminationEnabled() { return false; }
    }
    public enum UnknownField {
        CAMPAIGN_OUTCOME_FORECAST("campaign_outcome_forecast"), OPPONENT_ACCEPTANCE("opponent_acceptance");
        private final String wire;
        UnknownField(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum ProductionAdmission { DISABLED_NATIVE_PREVIEW_CRASH }

    public static String queryStep(int warId) { WarExitTerms.positive(warId); return WarExitTerms.QUERY_PREFIX + warId; }
    public static OptionalInt parseQueryStep(String step) {
        if (step == null || !step.startsWith(WarExitTerms.QUERY_PREFIX)) { return OptionalInt.empty(); }
        String raw = step.substring(WarExitTerms.QUERY_PREFIX.length());
        if (!raw.matches("[1-9][0-9]{0,9}")) { return OptionalInt.empty(); }
        long id = Long.parseLong(raw);
        return id <= Integer.MAX_VALUE ? OptionalInt.of((int) id) : OptionalInt.empty();
    }
    /** A stale DLL advertising this capability cannot enable the crash-prone collector. */
    public static ProductionAdmission productionAdmission() { return ProductionAdmission.DISABLED_NATIVE_PREVIEW_CRASH; }
    public static List<String> productionQuerySteps() { return List.of(); }
    public static byte[] productionSnapshotProjection() { return StrictJson.canonical(StrictJson.object().putArray("values")); }

    /** Replay/adapter entry for a returned primitive result; this does not call the disabled collector. */
    public static BoundPreview bindReturnedPreview(byte[] rawResult, byte[] rawStartingSnapshot, byte[] rawCurrentSnapshot, int warId) {
        WarExitTerms.positive(warId);
        ObjectNode result = StrictJson.object(StrictJson.parse(rawResult, WarExitTermsCodec.MAX_BYTES),
                Set.of("step", "accepted", "status", "query_sequence", "war_termination_exit_terms", "backend_id"));
        WarExitTermsCodec.literal(result.get("step"), queryStep(warId));
        StrictJson.trueValue(result.get("accepted")); WarExitTermsCodec.literal(result.get("status"), "available");
        WarExitTerms terms = WarExitTermsCodec.decodeNode(result.get("war_termination_exit_terms"));
        require(terms.warId() == warId, "query result WarID mismatch");
        JsonNode before = StrictJson.parse(rawStartingSnapshot, WarExitTermsCodec.MAX_BYTES);
        JsonNode after = StrictJson.parse(rawCurrentSnapshot, WarExitTermsCodec.MAX_BYTES);
        Frame starting = frame(before); Frame current = frame(after);
        JsonNode war = activeWar(before, warId).orElseThrow(() -> invalid("query requires active WarID"));
        require(starting.sameNativeFrame(current) && activeWar(after, warId).isPresent(), "query crossed native frame or ended war");
        require("attacker".equals(text(war, "player_side")) && actualTrue(war.get("player_is_primary_war_leader"))
                && id(before.path("played_character").get("character_id")) == terms.primaryAttackerCharacterId()
                && id(war.get("primary_opponent_character_id")) == terms.primaryDefenderCharacterId()
                && WarExitTermsCodec.ids(war.get("targeted_title_ids")).equals(terms.targetTitleIds()),
                "query identity disagrees with paused war snapshot");
        QuerySequence sequence = new QuerySequence(StrictJson.integer(result.get("query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX));
        return new BoundPreview(terms, sequence, starting, text(result, "backend_id"));
    }

    /** The private cache producer requires exact public/native revision, connection, episode and active WarID. */
    public static Optional<BoundPreview> sameFrameCacheProjection(BoundPreview cached, byte[] rawSnapshot) {
        require(cached != null, "bound preview required");
        JsonNode snapshot = StrictJson.parse(rawSnapshot, WarExitTermsCodec.MAX_BYTES);
        if (!actualTrue(snapshot.get("paused"))) { return Optional.empty(); }
        Frame current = frame(snapshot);
        return cached.frame().equals(current) && activeWar(snapshot, cached.terms().warId()).isPresent()
                ? Optional.of(cached) : Optional.empty();
    }
    public static byte[] encodeSnapshotCache(List<BoundPreview> rows) {
        require(rows != null, "typed preview list required");
        ObjectNode wrapper = StrictJson.object(); ArrayNode values = wrapper.putArray("values");
        rows.stream().sorted(Comparator.comparingInt(row -> row.terms().warId())).forEach(row -> values.add(cacheNode(row)));
        return StrictJson.canonical(values, WarExitTermsCodec.MAX_BYTES);
    }
    public static byte[] encodeDriverResult(BoundPreview preview) {
        ObjectNode result = resultNode(preview);
        result.put("queried_snapshot_id", preview.frame().snapshotId()); result.put("queried_revision", preview.frame().revision());
        result.put("queried_native_revision", preview.frame().nativeRevision());
        return StrictJson.canonical(result, WarExitTermsCodec.MAX_BYTES);
    }
    /** GameplayBridgeService adds the expected WarID after matching the structured result. */
    public static byte[] encodeServiceResult(BoundPreview preview) {
        ObjectNode result = (ObjectNode) StrictJson.parse(encodeDriverResult(preview), WarExitTermsCodec.MAX_BYTES);
        result.put("war_id", preview.terms().warId()); return StrictJson.canonical(result, WarExitTermsCodec.MAX_BYTES);
    }
    public static ComparisonInput comparisonInput(BoundPreview preview) {
        require(preview != null, "bound preview required");
        return new ComparisonInput(preview.terms(), List.of(UnknownField.CAMPAIGN_OUTCOME_FORECAST, UnknownField.OPPONENT_ACCEPTANCE));
    }
    /** Mirror the strategy consumer's acceptance-completeness rule over the independent native options cache. */
    public static ComparisonInput comparisonInput(BoundPreview preview, byte[] rawNativeOptionsCache) {
        require(preview != null, "bound preview required");
        JsonNode raw = StrictJson.parse(rawNativeOptionsCache, WarExitTermsCodec.MAX_BYTES);
        NativeTerminationOptions options = NativeTerminationOptions.fromCache(raw, preview.terms().warId());
        NativeTerminationOptions.QueryBinding binding = options.binding(); Frame frame = preview.frame();
        require(options.side() == WarSide.ATTACKER && options.primary() && binding.snapshotId().equals(frame.snapshotId())
                && binding.revision().equals(frame.revision()) && binding.nativeRevision().equals(frame.nativeRevision())
                && binding.episodeRunId().equals(frame.episodeRunId()) && binding.connectionGeneration().equals(frame.connectionGeneration()),
                "independent option observation must match the preview frame and player side");
        int constructed = 0; boolean acceptanceComplete = true;
        for (JsonNode option : raw.get("options")) {
            if (actualTrue(option.get("context_constructed"))) {
                constructed++;
                acceptanceComplete &= actualTrue(option.get("ai_acceptance_observable")) && actualTrue(option.get("auto_accept_observable"));
            }
        }
        return new ComparisonInput(preview.terms(), constructed > 0 && acceptanceComplete
                ? List.of(UnknownField.CAMPAIGN_OUTCOME_FORECAST)
                : List.of(UnknownField.CAMPAIGN_OUTCOME_FORECAST, UnknownField.OPPONENT_ACCEPTANCE));
    }
    /** Terms-only portion of strategy.war_exit_assessment; option legality/acceptance remains its own observation. */
    public static byte[] encodeComparisonInput(ComparisonInput input) {
        require(input != null, "typed comparison input required");
        ObjectNode result = StrictJson.object(); result.set("structured_exit_terms", WarExitTermsCodec.node(input.structuredExitTerms()));
        ArrayNode unknown = result.putArray("unknown_fields"); input.unknownFields().forEach(field -> unknown.add(field.wire()));
        result.put("automatic_termination_enabled", false); return StrictJson.canonical(result, WarExitTermsCodec.MAX_BYTES);
    }

    private static ObjectNode resultNode(BoundPreview preview) {
        require(preview != null, "bound preview required");
        ObjectNode result = StrictJson.object(); result.put("step", queryStep(preview.terms().warId())); result.put("accepted", true);
        result.put("status", "available"); result.put("query_sequence", preview.querySequence().value());
        result.set("war_termination_exit_terms", WarExitTermsCodec.node(preview.terms())); result.put("backend_id", preview.backendId()); return result;
    }
    private static ObjectNode cacheNode(BoundPreview preview) {
        ObjectNode result = WarExitTermsCodec.node(preview.terms()); result.put("query_sequence", preview.querySequence().value());
        result.put("queried_snapshot_id", preview.frame().snapshotId()); result.put("queried_revision", preview.frame().revision());
        result.put("queried_native_revision", preview.frame().nativeRevision()); result.put("episode_run_id", preview.frame().episodeRunId()); return result;
    }
    private static Frame frame(JsonNode snapshot) {
        require(snapshot != null && snapshot.isObject() && actualTrue(snapshot.get("paused")), "paused SDK snapshot required");
        return new Frame(text(snapshot, "snapshot_id"), nonnegative(snapshot.get("revision")), nonnegative(snapshot.get("native_revision")),
                nonnegative(snapshot.path("diagnostics").get("connection_generation")), text(snapshot, "episode_run_id"));
    }
    private static Optional<JsonNode> activeWar(JsonNode snapshot, int warId) {
        JsonNode rows = snapshot.get("active_wars"); require(rows != null && rows.isArray(), "active war array required");
        for (JsonNode row : rows) {
            JsonNode rawId = row.get("war_id");
            if (row.isObject() && rawId != null && rawId.isIntegralNumber() && rawId.bigIntegerValue().equals(BigInteger.valueOf(warId))) {
                return Optional.of(row);
            }
        }
        return Optional.empty();
    }
    private static BigInteger nonnegative(JsonNode value) {
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() >= 0, "exact nonnegative SDK integer required");
        return value.bigIntegerValue();
    }
    private static boolean actualTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static String text(JsonNode root, String field) { return StrictJson.text(root.get(field)); }
    private static int id(JsonNode value) { return WarExitTermsCodec.id(value); }
    private static org.xar.ck3.control.contracts.ContractViolationException invalid(String reason) {
        return new org.xar.ck3.control.contracts.ContractViolationException(reason);
    }
}
