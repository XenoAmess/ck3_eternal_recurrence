package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.warpolicy.NativeTerminationTerms;

/** Actual source-bound producer composition. This class cannot submit or authorize an action. */
public final class RaiktorActualRecommendationFactory {
    private RaiktorActualRecommendationFactory() { }
    public enum Blocker {
        CURRENT_SNAPSHOT_UNAVAILABLE, TERMINATION_OPTIONS_QUERY_UNAVAILABLE, RAIKTOR_TERMS_QUERY_UNAVAILABLE,
        POWER_DOUBLE_SAMPLE_UNAVAILABLE, NATIVE_TERMS_UNSUPPORTED, SURRENDER_AGGREGATE_SESSION_UNAVAILABLE,
        WHITE_PEACE_OBSERVATION_UNAVAILABLE, AGGREGATE_DYNAMIC_DOMAINS_UNAVAILABLE, THREE_WAY_RECOMMENDATION_UNREADY
    }
    public sealed interface Result permits Available, Unavailable { }
    public record Available(JsonNode recommendation, RaiktorUtilityComparisonTrace.Trace trace) implements Result {
        public Available { recommendation = Objects.requireNonNull(recommendation).deepCopy(); Objects.requireNonNull(trace); }
        @Override public JsonNode recommendation() { return recommendation.deepCopy(); }
    }
    public record Unavailable(List<Blocker> blockers, List<String> diagnostics) implements Result {
        public Unavailable {
            blockers = List.copyOf(blockers); diagnostics = List.copyOf(diagnostics);
            require(!blockers.isEmpty(), "unavailable result requires a blocker");
        }
    }
    public record Inputs(JsonNode currentSnapshot, JsonNode optionsQuery, JsonNode termsQuery,
            JsonNode beforePowerSnapshot, JsonNode firstPowerQuery, JsonNode betweenPowerSnapshot,
            JsonNode secondPowerQuery, JsonNode afterPowerSnapshot, int warId, int opponentCharacterId,
            boolean productionLive) {
        public Inputs {
            require(warId > 0 && opponentCharacterId != -1, "actual selected war and opponent IDs required");
            currentSnapshot = copy(currentSnapshot); optionsQuery = copy(optionsQuery); termsQuery = copy(termsQuery);
            beforePowerSnapshot = copy(beforePowerSnapshot); firstPowerQuery = copy(firstPowerQuery);
            betweenPowerSnapshot = copy(betweenPowerSnapshot); secondPowerQuery = copy(secondPowerQuery);
            afterPowerSnapshot = copy(afterPowerSnapshot);
        }
        @Override public JsonNode currentSnapshot() { return copy(currentSnapshot); }
        @Override public JsonNode optionsQuery() { return copy(optionsQuery); }
        @Override public JsonNode termsQuery() { return copy(termsQuery); }
        @Override public JsonNode beforePowerSnapshot() { return copy(beforePowerSnapshot); }
        @Override public JsonNode firstPowerQuery() { return copy(firstPowerQuery); }
        @Override public JsonNode betweenPowerSnapshot() { return copy(betweenPowerSnapshot); }
        @Override public JsonNode secondPowerQuery() { return copy(secondPowerQuery); }
        @Override public JsonNode afterPowerSnapshot() { return copy(afterPowerSnapshot); }
    }
    public record FileRef(Path path, long bytes, String sha256) {
        public FileRef {
            path = Objects.requireNonNull(path).toAbsolutePath().normalize();
            require(bytes > 0 && bytes <= StrictJson.EXPLICIT_MAX_BYTES, "bounded configuration FileRef required");
            require(sha256 != null && sha256.matches("[0-9a-fA-F]{64}"), "configuration SHA-256 required");
        }
    }
    public record ConfigurationSources(FileRef defaultBudget, FileRef defaultModel,
            Optional<FileRef> budgetOverride, Optional<FileRef> modelOverride) {
        public ConfigurationSources {
            Objects.requireNonNull(defaultBudget); Objects.requireNonNull(defaultModel);
            Objects.requireNonNull(budgetOverride); Objects.requireNonNull(modelOverride);
        }
    }
    public static final class Configuration {
        private final ObjectNode budget;
        private final ObjectNode model;
        private final ConfigurationSources sources;
        Configuration(ObjectNode budget, ObjectNode model, ConfigurationSources sources) {
            this.budget = budget.deepCopy(); this.model = model.deepCopy(); this.sources = Objects.requireNonNull(sources);
        }
        public JsonNode budgetProvider() { return budget.deepCopy(); }
        public JsonNode modelProvider() { return model.deepCopy(); }
        public ConfigurationSources sources() { return sources; }
    }
    public static final class InputRejected extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        InputRejected(String message, IllegalArgumentException cause) { super(message, cause); }
    }

    public static M0Frame decodeFrame(JsonNode value) {
        return RaiktorRecommendationInputCodec.decodeFrame(value);
    }

    public static Configuration loadConfiguration(ConfigurationSources sources) {
        return RaiktorStrategyConfiguration.load(Objects.requireNonNull(sources));
    }

    public static Result produce(Inputs input, Configuration configuration) {
        Objects.requireNonNull(input); Objects.requireNonNull(configuration);
        if (missing(input.currentSnapshot())) return unavailable(Blocker.CURRENT_SNAPSHOT_UNAVAILABLE, "paused_snapshot_unavailable");
        if (missing(input.optionsQuery())) return unavailable(Blocker.TERMINATION_OPTIONS_QUERY_UNAVAILABLE,
                "termination_options_query_unavailable");
        if (missing(input.termsQuery())) return unavailable(Blocker.RAIKTOR_TERMS_QUERY_UNAVAILABLE, "raiktor_terms_query_unavailable");
        try {
            ObjectNode termsEnvelope = object(input.termsQuery(), "terms query");
            String queryStatus = text(termsEnvelope.get("status"), "terms query status");
            require(bool(termsEnvelope.get("accepted"), "terms query accepted")
                    && (queryStatus.equals("available") || queryStatus.equals("unsupported")),
                    "terms query status is not a supported original envelope");
            ObjectNode terms = NativeTerminationTerms.normalize(termsEnvelope.get("war_termination_terms"), input.warId());
            if (text(terms.get("status"), "terms status").equals("unsupported")) {
                return unavailable(Blocker.NATIVE_TERMS_UNSUPPORTED, "native_raiktor_terms_unsupported");
            }
            require(queryStatus.equals("available"), "available terms disagree with unsupported query envelope");
            for (JsonNode value : new JsonNode[] {input.beforePowerSnapshot(), input.firstPowerQuery(),
                        input.betweenPowerSnapshot(), input.secondPowerQuery(), input.afterPowerSnapshot()}) {
                if (missing(value)) return unavailable(Blocker.POWER_DOUBLE_SAMPLE_UNAVAILABLE, "power_double_sample_unavailable");
            }
            ObjectNode termsQuery = object(input.termsQuery(), "terms query");
            JsonNode sessionInput = termsQuery.get("raiktor_surrender_aggregate_session");
            if (sessionInput == null || sessionInput.isNull()) {
                // This pure projection has no passive-native truce proof to invent.
                termsQuery = RaiktorSurrenderAggregateProducer.attachSession(input.currentSnapshot(), termsQuery, null);
            }
            ObjectNode white = object(RaiktorWhitePeaceProjectionProducer.produce(input.currentSnapshot(),
                    input.optionsQuery(), termsQuery, input.productionLive()), "white projection");
            if (!bool(white.get("observation_ready"), "observation_ready")) {
                List<String> diagnostics = strings(white.get("blockers"), "projection blockers");
                Blocker blocker = diagnostics.stream().anyMatch(value -> value.startsWith("surrender_aggregate_session_"))
                        ? Blocker.SURRENDER_AGGREGATE_SESSION_UNAVAILABLE : Blocker.WHITE_PEACE_OBSERVATION_UNAVAILABLE;
                return new Unavailable(List.of(blocker), diagnostics);
            }
            ObjectNode actualSession = object(termsQuery.get("raiktor_surrender_aggregate_session"), "surrender session");
            ObjectNode aggregate = RaiktorSurrenderAggregateProducer.validateAggregate(actualSession.get("aggregate"));
            if (!bool(aggregate.path("readiness").get("action_terms_ready"), "aggregate action terms ready")) {
                return new Unavailable(List.of(Blocker.AGGREGATE_DYNAMIC_DOMAINS_UNAVAILABLE),
                        strings(aggregate.get("missing_domains"), "missing aggregate domains"));
            }
            ObjectNode dominance = object(RaiktorCampaignDominanceProducer.produce(input.beforePowerSnapshot(),
                    input.firstPowerQuery(), input.betweenPowerSnapshot(), input.secondPowerQuery(), input.afterPowerSnapshot(),
                    input.warId(), input.opponentCharacterId()), "dominance");
            ObjectNode terminalInput = StrictJson.object(); terminalInput.set("snapshot", input.currentSnapshot());
            terminalInput.put("war_id", input.warId()); terminalInput.put("opponent_character_id", input.opponentCharacterId());
            terminalInput.set("options_query", input.optionsQuery()); terminalInput.set("white_peace_projection", white);
            JsonNode terminal = RaiktorExitObservationCodec.parseWire(RaiktorTerminalInputProjection.executeFromSnapshot(
                    RaiktorExitObservationCodec.encodeWire(terminalInput)));
            ObjectNode request = StrictJson.object(); request.put("operation", RaiktorRecommendationComposer.OPERATION);
            request.set("white_peace_projection", white);
            request.set("surrender_session", actualSession);
            request.set("normalized_power", dominance.get("campaign_dominance_certificate"));
            request.set("budget_provider", configuration.budgetProvider()); request.set("model_provider", configuration.modelProvider());
            request.set("terminal_control", terminal);
            ObjectNode recommendation = object(RaiktorExitObservationCodec.parseWire(
                    RaiktorRecommendationComposer.executeOperation(RaiktorExitObservationCodec.encodeWire(request))), "recommendation");
            if (!bool(recommendation.get("production_recommendation_ready"), "production recommendation ready")) {
                return new Unavailable(List.of(Blocker.THREE_WAY_RECOMMENDATION_UNREADY),
                        strings(recommendation.get("blockers"), "recommendation blockers"));
            }
            return new Available(recommendation, RaiktorUtilityComparisonTrace.fromCertificate(
                    recommendation.get("recommendation_certificate")));
        } catch (IllegalArgumentException failure) {
            throw new InputRejected(failure.getMessage(), failure);
        }
    }
    private static boolean missing(JsonNode value) { return value == null || value.isNull(); }
    private static Unavailable unavailable(Blocker blocker, String detail) {
        return new Unavailable(List.of(blocker), List.of(detail));
    }
}
