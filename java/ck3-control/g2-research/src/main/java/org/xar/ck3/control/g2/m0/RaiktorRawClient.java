package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.ConfigurationSources;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory.FileRef;
import org.xar.ck3.control.g2.m0.RaiktorRawOperations.Operation;

/** Borrowed SDK consumer for the existing M0 route. One call, strict echo and result, no retry. */
public final class RaiktorRawClient {
    @FunctionalInterface public interface Evaluation { G2Response evaluate(G2Request request); }
    private final Evaluation evaluation;
    public RaiktorRawClient(G2JavaClient client) { this(Objects.requireNonNull(client)::evaluate); }
    public RaiktorRawClient(Evaluation evaluation) { this.evaluation = Objects.requireNonNull(evaluation); }

    /** JSON operands are retained immutable values at the native/SDK boundary, not mutable caller objects. */
    public static final class Operand {
        private final byte[] encoded;
        private Operand(JsonNode value) {
            encoded = RaiktorExitObservationCodec.encodeWire(Objects.requireNonNull(value, "explicit JSON operand required"));
            StrictJson.parse(encoded, StrictJson.EXPLICIT_MAX_BYTES);
        }
        public static Operand of(JsonNode value) { return new Operand(value); }
        public JsonNode value() { return StrictJson.parse(encoded, StrictJson.EXPLICIT_MAX_BYTES); }
        public byte[] bytes() { return encoded.clone(); }
    }
    /** Raw M0 hashes are uppercase; configuration FileRef hashes retain their original spelling. */
    public record Sha256(String value) {
        public Sha256 { StrictJson.require(value != null && value.matches("[0-9A-F]{64}"), "exact SHA-256 required"); }
    }
    public record FullId(int value) {
        public FullId { StrictJson.require(value != -1, "full DWORD identity excludes invalid sentinel"); }
    }
    public sealed interface Request permits Campaign, NormalizePower, ReplayPower, WhitePeace, ProjectSurrender,
            BindSurrender, AttachSurrender, RenderBudget, RenderModel, ProvideBudget, ProvideModel,
            LoadConfiguration, ActualRecommendation {
        Operation operation();
        ObjectNode payload();
    }
    public record Campaign(Operand before, Operand first, Operand between, Operand second, Operand after,
            FullId warId, FullId opponentCharacterId, Sha256 sourceArtifactSha256) implements Request {
        public Campaign { required(before, first, between, second, after, warId, opponentCharacterId, sourceArtifactSha256); }
        public Operation operation() { return Operation.CAMPAIGN; }
        public ObjectNode payload() {
            var n = start(operation()); put(n, "before", before); put(n, "first", first); put(n, "between", between);
            put(n, "second", second); put(n, "after", after); n.put("war_id", warId.value());
            n.put("opponent_character_id", opponentCharacterId.value()); n.put("source_artifact_sha256", sourceArtifactSha256.value()); return n;
        }
    }
    public record NormalizePower(Operand certificate) implements Request {
        public NormalizePower { required(certificate); }
        public Operation operation() { return Operation.NORMALIZE_POWER; }
        public ObjectNode payload() { var n = start(operation()); put(n, "certificate", certificate); return n; }
    }
    public record ReplayPower(Operand sourceCertificate, Operand targetFrame, Sha256 sourceCheckpointSha256,
            Sha256 targetCheckpointSha256, Sha256 sourceDriverStateSha256, Sha256 targetDriverStateSha256) implements Request {
        public ReplayPower { required(sourceCertificate, targetFrame, sourceCheckpointSha256, targetCheckpointSha256, sourceDriverStateSha256, targetDriverStateSha256); }
        public Operation operation() { return Operation.REPLAY_POWER; }
        public ObjectNode payload() {
            var n = start(operation()); put(n, "source_certificate", sourceCertificate); put(n, "target_frame", targetFrame);
            n.put("source_checkpoint_sha256", sourceCheckpointSha256.value()); n.put("target_checkpoint_sha256", targetCheckpointSha256.value());
            n.put("source_driver_state_sha256", sourceDriverStateSha256.value()); n.put("target_driver_state_sha256", targetDriverStateSha256.value()); return n;
        }
    }
    public record WhitePeace(Operand snapshot, Operand optionsQuery, Operand termsQuery, boolean productionLive) implements Request {
        public WhitePeace { required(snapshot, optionsQuery, termsQuery); }
        public Operation operation() { return Operation.WHITE; }
        public ObjectNode payload() {
            var n = start(operation()); put(n, "snapshot", snapshot); put(n, "options_query", optionsQuery);
            put(n, "terms_query", termsQuery); n.put("production_live", productionLive); return n;
        }
    }
    public record ProjectSurrender(Operand snapshot, Operand terms, Operand passiveTruce, Operand genericWarBoundCurrent) implements Request {
        public ProjectSurrender { required(snapshot, terms, passiveTruce, genericWarBoundCurrent); }
        public Operation operation() { return Operation.PROJECT; }
        public ObjectNode payload() {
            var n = start(operation()); put(n, "snapshot", snapshot); put(n, "terms", terms); put(n, "passive_truce", passiveTruce);
            put(n, "generic_war_bound_current", genericWarBoundCurrent); return n;
        }
    }
    public record BindSurrender(Operand snapshot, Operand queryReceipt, Operand aggregate) implements Request {
        public BindSurrender { required(snapshot, queryReceipt, aggregate); }
        public Operation operation() { return Operation.BIND; }
        public ObjectNode payload() {
            var n = start(operation()); put(n, "snapshot", snapshot); put(n, "query_receipt", queryReceipt); put(n, "aggregate", aggregate); return n;
        }
    }
    public record AttachSurrender(Operand snapshot, Operand termsQuery, Operand passiveTruce) implements Request {
        public AttachSurrender { required(snapshot, termsQuery, passiveTruce); }
        public Operation operation() { return Operation.ATTACH; }
        public ObjectNode payload() {
            var n = start(operation()); put(n, "snapshot", snapshot); put(n, "terms_query", termsQuery); put(n, "passive_truce", passiveTruce); return n;
        }
    }
    public record RenderBudget(Operand source, Sha256 sourceSha256, Operand repositoryDefault) implements Request {
        public RenderBudget { required(source, sourceSha256, repositoryDefault); }
        public Operation operation() { return Operation.BUDGET; }
        public ObjectNode payload() {
            var n = start(operation()); put(n, "source", source); n.put("source_sha256", sourceSha256.value()); put(n, "repository_default", repositoryDefault); return n;
        }
    }
    public record RenderModel(Operand source, Sha256 sourceSha256) implements Request {
        public RenderModel { required(source, sourceSha256); }
        public Operation operation() { return Operation.MODEL; }
        public ObjectNode payload() { var n = start(operation()); put(n, "source", source); n.put("source_sha256", sourceSha256.value()); return n; }
    }
    public record ProvideBudget(FileRef defaultBudget, Optional<FileRef> budgetOverride) implements Request {
        public ProvideBudget { required(defaultBudget, budgetOverride); }
        public Operation operation() { return Operation.PROVIDE_BUDGET; }
        public ObjectNode payload() {
            var n = start(operation()); n.set("default_budget", ref(defaultBudget)); n.set("budget_override", optionalRef(budgetOverride)); return n;
        }
    }
    public record ProvideModel(FileRef defaultBudget, FileRef defaultModel, Optional<FileRef> modelOverride) implements Request {
        public ProvideModel { required(defaultBudget, defaultModel, modelOverride); }
        public Operation operation() { return Operation.PROVIDE_MODEL; }
        public ObjectNode payload() {
            var n = start(operation()); n.set("default_budget", ref(defaultBudget)); n.set("default_model", ref(defaultModel));
            n.set("model_override", optionalRef(modelOverride)); return n;
        }
    }
    public record LoadConfiguration(ConfigurationSources configurationSources) implements Request {
        public LoadConfiguration { required(configurationSources); }
        public Operation operation() { return Operation.CONFIGURATION; }
        public ObjectNode payload() { var n = start(operation()); n.set("configuration_sources", sources(configurationSources)); return n; }
    }
    public record ActualRecommendation(RaiktorActualRecommendationFactory.Inputs inputs,
            ConfigurationSources configurationSources) implements Request {
        public ActualRecommendation { required(inputs, configurationSources); }
        public Operation operation() { return Operation.ACTUAL; }
        public ObjectNode payload() {
            var n = start(operation()); n.set("current_snapshot", explicit(inputs.currentSnapshot()));
            n.set("options_query", explicit(inputs.optionsQuery())); n.set("terms_query", explicit(inputs.termsQuery()));
            n.set("before_power_snapshot", explicit(inputs.beforePowerSnapshot())); n.set("first_power_query", explicit(inputs.firstPowerQuery()));
            n.set("between_power_snapshot", explicit(inputs.betweenPowerSnapshot())); n.set("second_power_query", explicit(inputs.secondPowerQuery()));
            n.set("after_power_snapshot", explicit(inputs.afterPowerSnapshot())); n.put("war_id", inputs.warId());
            n.put("opponent_character_id", inputs.opponentCharacterId()); n.put("production_live", inputs.productionLive());
            n.set("configuration_sources", sources(configurationSources)); return n;
        }
    }

    public sealed interface Result permits DocumentResult, AggregateResult, AttachmentResult, ConfigurationResult, RecommendationAvailable, RecommendationUnavailable {
        Operation operation();
    }
    /** Operation-specific document contracts are checked by the single producer-owned result codec. */
    public record DocumentResult(Operation operation, Operand document) implements Result {
        public DocumentResult {
            required(operation, document);
            StrictJson.require(operation != Operation.PROJECT && operation != Operation.CONFIGURATION && operation != Operation.ACTUAL && operation != Operation.ATTACH,
                    "special result requires its sealed branch");
            RaiktorRawOperations.validateResult(operation, document.value());
        }
    }
    public record AttachmentResult(AttachSurrender request, Operand document) implements Result {
        public AttachmentResult {
            required(request, document); RaiktorRawOperations.validateResult(Operation.ATTACH, request.payload(), document.value());
        }
        public Operation operation() { return Operation.ATTACH; }
    }
    public record AggregateResult(Optional<Operand> aggregate) implements Result {
        public AggregateResult {
            required(aggregate); RaiktorRawOperations.validateResult(Operation.PROJECT,
                    aggregate.map(Operand::value).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));
        }
        public Operation operation() { return Operation.PROJECT; }
    }
    public record ConfigurationResult(Operand budgetProvider, Operand modelProvider) implements Result {
        public ConfigurationResult {
            required(budgetProvider, modelProvider); var n = StrictJson.object();
            put(n, "budget_provider", budgetProvider); put(n, "model_provider", modelProvider);
            RaiktorRawOperations.validateResult(Operation.CONFIGURATION, n);
        }
        public Operation operation() { return Operation.CONFIGURATION; }
    }
    public record RecommendationAvailable(Operand recommendation) implements Result {
        public RecommendationAvailable {
            required(recommendation); var n = actualResult("available"); put(n, "recommendation", recommendation);
            RaiktorRawOperations.validateResult(Operation.ACTUAL, n);
        }
        public Operation operation() { return Operation.ACTUAL; }
    }
    public record RecommendationUnavailable(List<RaiktorActualRecommendationFactory.Blocker> blockers,
            List<String> diagnostics) implements Result {
        public RecommendationUnavailable {
            blockers = List.copyOf(blockers); diagnostics = List.copyOf(diagnostics);
            StrictJson.require(!blockers.isEmpty(), "unavailable recommendation requires actual blocker");
            diagnostics.forEach(StrictJson::text);
            var n = actualResult("unavailable"); n.putNull("recommendation");
            blockers.forEach(value -> n.withArray("blockers").add(value.name()));
            diagnostics.forEach(value -> n.withArray("diagnostics").add(value));
            RaiktorRawOperations.validateResult(Operation.ACTUAL, n);
        }
        public Operation operation() { return Operation.ACTUAL; }
    }

    public Result evaluate(String requestId, G2Source source, Request input) {
        Objects.requireNonNull(input); var request = new G2Request(requestId, Milestone.M0, source,
                ProjectionJson.object(RaiktorExitObservationCodec.encodeWire(input.payload()), ProjectionJson.MAX_BYTES));
        G2Response response = Objects.requireNonNull(evaluation.evaluate(request), "SDK response is absent");
        StrictJson.require(request.requestId().equals(response.requestId()) && response.milestone() == Milestone.M0
                && request.source().equals(response.source()), "M0 SDK response identity/provenance differs");
        return consume(input, StrictJson.parse(response.result().bytes(), StrictJson.EXPLICIT_MAX_BYTES));
    }

    /** Shared success path used by the existing generic SDK client as well as the typed consumer. */
    public static void validateResponse(G2Request request, G2Response response) {
        if (request.milestone() != Milestone.M0) return;
        JsonNode root = StrictJson.parse(request.payload().bytes(), StrictJson.EXPLICIT_MAX_BYTES);
        JsonNode key = root.get("operation");
        if (key == null || !key.isTextual()) return; // Existing non-raw M0 contracts remain owned by their codecs.
        Operation.find(key.textValue()).ifPresent(operation ->
                RaiktorRawOperations.validateResult(operation, root, StrictJson.parse(response.result().bytes(), StrictJson.EXPLICIT_MAX_BYTES)));
    }

    public static Result consume(Request request, JsonNode original) {
        Objects.requireNonNull(request); Objects.requireNonNull(original);
        JsonNode value = RaiktorRawOperations.validateResult(request.operation(), request.payload(), original);
        if (request instanceof AttachSurrender attachment) return new AttachmentResult(attachment, Operand.of(value));
        return consume(request.operation(), value);
    }
    public static Result consume(Operation operation, JsonNode original) {
        StrictJson.require(operation != Operation.ATTACH, "attachment result requires its original typed query request");
        JsonNode value = RaiktorRawOperations.validateResult(Objects.requireNonNull(operation), Objects.requireNonNull(original));
        return switch (operation) {
            case PROJECT -> new AggregateResult(value.isNull() ? Optional.empty() : Optional.of(Operand.of(value)));
            case CONFIGURATION -> new ConfigurationResult(Operand.of(value.get("budget_provider")), Operand.of(value.get("model_provider")));
            case ACTUAL -> {
                if (StrictJson.text(value.get("status")).equals("available")) yield new RecommendationAvailable(Operand.of(value.get("recommendation")));
                List<RaiktorActualRecommendationFactory.Blocker> blockers = new java.util.ArrayList<>();
                for (JsonNode item : value.get("blockers")) blockers.add(RaiktorActualRecommendationFactory.Blocker.valueOf(StrictJson.text(item)));
                List<String> diagnostics = new java.util.ArrayList<>();
                for (JsonNode item : value.get("diagnostics")) diagnostics.add(StrictJson.text(item));
                yield new RecommendationUnavailable(blockers, diagnostics);
            }
            default -> new DocumentResult(operation, Operand.of(value));
        };
    }
    private static void required(Object... values) { for (Object value : values) Objects.requireNonNull(value); }
    private static ObjectNode start(Operation operation) { var n = StrictJson.object(); n.put("operation", operation.wire()); return n; }
    private static void put(ObjectNode n, String name, Operand value) { n.set(name, value.value()); }
    private static JsonNode explicit(JsonNode value) {
        return value == null ? com.fasterxml.jackson.databind.node.NullNode.instance : value.deepCopy();
    }
    private static ObjectNode ref(FileRef ref) {
        var n = StrictJson.object(); n.put("path", ref.path().toString()); n.put("bytes", ref.bytes()); n.put("sha256", ref.sha256()); return n;
    }
    private static JsonNode optionalRef(Optional<FileRef> ref) {
        return ref.<JsonNode>map(RaiktorRawClient::ref).orElse(com.fasterxml.jackson.databind.node.NullNode.instance);
    }
    private static ObjectNode sources(ConfigurationSources sources) {
        var n = StrictJson.object(); n.set("default_budget", ref(sources.defaultBudget())); n.set("default_model", ref(sources.defaultModel()));
        n.set("budget_override", optionalRef(sources.budgetOverride())); n.set("model_override", optionalRef(sources.modelOverride())); return n;
    }
    private static ObjectNode actualResult(String status) {
        var n = StrictJson.object(); n.put("schema", "xar.ck3.raiktor-actual-recommendation-result/v1");
        n.put("status", status); n.putArray("blockers"); n.putArray("diagnostics"); n.put("action_authority", false); return n;
    }
}
