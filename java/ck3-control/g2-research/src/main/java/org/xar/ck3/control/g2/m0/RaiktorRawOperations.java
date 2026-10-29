package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m0.RaiktorRawJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.ConfigurationSources;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.FileRef;

/** Single strict wire boundary for the original raw M0 producers. Reads configuration; never submits. */
public final class RaiktorRawOperations {
    private RaiktorRawOperations() { }

    public enum Operation {
        CAMPAIGN("produce-campaign-dominance"), NORMALIZE_POWER("normalize-campaign-dominance"),
        REPLAY_POWER("produce-checkpoint-replay-dominance"),
        WHITE("produce-white-peace-narrow-projection"), PROJECT("project-surrender-six-domain"),
        BIND("bind-surrender-aggregate-session"), ATTACH("attach-surrender-aggregate-session"),
        BUDGET("render-owner-budget-profile"), MODEL("render-exit-utility-model"),
        PROVIDE_BUDGET("provide-owner-budget-profile"), PROVIDE_MODEL("provide-exit-utility-model"),
        CONFIGURATION("load-strategy-configuration"), ACTUAL("produce-actual-recommendation");
        private final String wire;
        Operation(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Optional<Operation> find(String value) {
            return Arrays.stream(values()).filter(item -> item.wire.equals(value)).findFirst();
        }
    }

    public static boolean supports(String operation) { return Operation.find(operation).isPresent(); }

    /** Strict result boundary for transport consumers; never executes a producer or reads a file. */
    public static JsonNode validateResult(Operation operation, JsonNode raw) {
        return RaiktorRawResultCodec.validate(operation, null, raw);
    }

    /** The original request is required for ATTACH, which preserves the complete query receipt. */
    public static JsonNode validateResult(Operation operation, JsonNode request, JsonNode raw) {
        return RaiktorRawResultCodec.validate(operation, object(request, "original raw M0 request"), raw);
    }

    public static byte[] execute(byte[] raw) {
        ObjectNode request = object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES), "raw M0 request");
        Operation operation = Operation.find(text(request.get("operation"), "operation"))
                .orElseThrow(() -> new IllegalArgumentException("unsupported raw M0 operation"));
        JsonNode result = switch (operation) {
            case CAMPAIGN -> campaign(request);
            case NORMALIZE_POWER -> {
                exact(request, Set.of("operation", "certificate"), "normalize power request");
                yield RaiktorCampaignDominanceProducer.normalizeCertificate(request.get("certificate"));
            }
            case REPLAY_POWER -> {
                exact(request, Set.of("operation", "source_certificate", "target_frame", "source_checkpoint_sha256",
                        "target_checkpoint_sha256", "source_driver_state_sha256", "target_driver_state_sha256"), "power replay request");
                yield RaiktorCampaignDominanceProducer.replay(request.get("source_certificate"), request.get("target_frame"),
                        sha(request.get("source_checkpoint_sha256"), "source checkpoint"),
                        sha(request.get("target_checkpoint_sha256"), "target checkpoint"),
                        sha(request.get("source_driver_state_sha256"), "source driver"),
                        sha(request.get("target_driver_state_sha256"), "target driver"));
            }
            case WHITE -> {
                exact(request, Set.of("operation", "snapshot", "options_query", "terms_query", "production_live"), "white request");
                yield RaiktorWhitePeaceProjectionProducer.produce(request.get("snapshot"), request.get("options_query"),
                        request.get("terms_query"), bool(request.get("production_live"), "production_live"));
            }
            case PROJECT -> {
                exact(request, Set.of("operation", "snapshot", "terms", "passive_truce", "generic_war_bound_current"), "aggregate request");
                yield RaiktorSurrenderAggregateProducer.project(request.get("snapshot"), request.get("terms"),
                        request.get("passive_truce"), request.get("generic_war_bound_current")).<JsonNode>map(value -> value)
                        .orElse(NullNode.instance);
            }
            case BIND -> {
                exact(request, Set.of("operation", "snapshot", "query_receipt", "aggregate"), "session request");
                yield RaiktorSurrenderAggregateProducer.bind(request.get("snapshot"), request.get("query_receipt"), request.get("aggregate"));
            }
            case ATTACH -> {
                exact(request, Set.of("operation", "snapshot", "terms_query", "passive_truce"), "attach request");
                yield RaiktorSurrenderAggregateProducer.attachSession(request.get("snapshot"), request.get("terms_query"), request.get("passive_truce"));
            }
            case BUDGET -> {
                exact(request, Set.of("operation", "source", "source_sha256", "repository_default"), "budget request");
                yield RaiktorStrategyConfiguration.renderBudget(request.get("source"),
                        sha(request.get("source_sha256"), "source SHA"), request.get("repository_default"));
            }
            case MODEL -> {
                exact(request, Set.of("operation", "source", "source_sha256"), "model request");
                yield RaiktorStrategyConfiguration.renderModel(request.get("source"), sha(request.get("source_sha256"), "source SHA"));
            }
            case PROVIDE_BUDGET -> {
                exact(request, Set.of("operation", "default_budget", "budget_override"), "budget provider request");
                yield RaiktorStrategyConfiguration.provideOwnerBudget(ref(request.get("default_budget")),
                        optionalRef(request.get("budget_override")));
            }
            case PROVIDE_MODEL -> {
                exact(request, Set.of("operation", "default_budget", "default_model", "model_override"), "model provider request");
                yield RaiktorStrategyConfiguration.provideExitModel(ref(request.get("default_budget")),
                        ref(request.get("default_model")), optionalRef(request.get("model_override")));
            }
            case CONFIGURATION -> {
                exact(request, Set.of("operation", "configuration_sources"), "configuration request");
                var configuration = RaiktorActualRecommendationFactory.loadConfiguration(sources(request.get("configuration_sources")));
                ObjectNode providers = StrictJson.object();
                providers.set("budget_provider", configuration.budgetProvider());
                providers.set("model_provider", configuration.modelProvider());
                yield providers;
            }
            case ACTUAL -> actual(request);
        };
        return RaiktorExitObservationCodec.encodeWire(validateResult(operation, request, result));
    }

    private static JsonNode campaign(ObjectNode request) {
        exact(request, Set.of("operation", "before", "first", "between", "second", "after", "war_id",
                "opponent_character_id", "source_artifact_sha256"), "campaign request");
        return RaiktorCampaignDominanceProducer.produce(request.get("before"), request.get("first"), request.get("between"),
                request.get("second"), request.get("after"), fullId(request.get("war_id"), "war_id"),
                fullId(request.get("opponent_character_id"), "opponent_character_id"),
                sha(request.get("source_artifact_sha256"), "source artifact"));
    }

    private static JsonNode actual(ObjectNode request) {
        exact(request, Set.of("operation", "current_snapshot", "options_query", "terms_query", "before_power_snapshot",
                "first_power_query", "between_power_snapshot", "second_power_query", "after_power_snapshot", "war_id",
                "opponent_character_id", "production_live", "configuration_sources"), "actual request");
        var input = new RaiktorActualRecommendationFactory.Inputs(request.get("current_snapshot"), request.get("options_query"),
                request.get("terms_query"), request.get("before_power_snapshot"), request.get("first_power_query"),
                request.get("between_power_snapshot"), request.get("second_power_query"), request.get("after_power_snapshot"),
                positive32(request.get("war_id"), "war_id"), fullId(request.get("opponent_character_id"), "opponent_character_id"),
                bool(request.get("production_live"), "production_live"));
        var configuration = RaiktorActualRecommendationFactory.loadConfiguration(sources(request.get("configuration_sources")));
        var produced = RaiktorActualRecommendationFactory.produce(input, configuration);
        ObjectNode result = StrictJson.object(); result.put("schema", "xar.ck3.raiktor-actual-recommendation-result/v1");
        if (produced instanceof RaiktorActualRecommendationFactory.Available available) {
            result.put("status", "available"); result.set("recommendation", available.recommendation());
            result.putArray("blockers"); result.putArray("diagnostics");
        } else if (produced instanceof RaiktorActualRecommendationFactory.Unavailable unavailable) {
            result.put("status", "unavailable"); result.putNull("recommendation");
            strings(result, "blockers", unavailable.blockers().stream().map(Enum::name).toList());
            strings(result, "diagnostics", unavailable.diagnostics());
        } else { throw new IllegalStateException("unhandled sealed M0 result"); }
        result.put("action_authority", false); return result;
    }

    private static ConfigurationSources sources(JsonNode raw) {
        ObjectNode sources = exact(raw, Set.of("default_budget", "default_model", "budget_override", "model_override"),
                "configuration sources");
        return new ConfigurationSources(ref(sources.get("default_budget")), ref(sources.get("default_model")),
                optionalRef(sources.get("budget_override")), optionalRef(sources.get("model_override")));
    }

    private static FileRef ref(JsonNode raw) {
        ObjectNode ref = exact(raw, Set.of("path", "bytes", "sha256"), "configuration FileRef");
        require(ref.get("bytes").isIntegralNumber(), "configuration bytes must be integral");
        return new FileRef(Path.of(text(ref.get("path"), "configuration path")),
                number(ref.get("bytes"), 1, StrictJson.EXPLICIT_MAX_BYTES, "configuration bytes"),
                text(ref.get("sha256"), "configuration SHA"));
    }
    private static Optional<FileRef> optionalRef(JsonNode raw) {
        return raw.isNull() ? Optional.empty() : Optional.of(ref(raw));
    }
}

