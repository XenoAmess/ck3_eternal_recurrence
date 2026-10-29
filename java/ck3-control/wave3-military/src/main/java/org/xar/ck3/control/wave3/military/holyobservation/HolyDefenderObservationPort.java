package org.xar.ck3.control.wave3.military.holyobservation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter;
import org.xar.ck3.control.wave2.military.projection.HolyInputValidation;
import org.xar.ck3.control.wave2.military.projection.HolySdkJson;
import org.xar.ck3.control.wave3.military.holyobservation.HolyDefenderObservation.Observation;
import org.xar.ck3.control.wave3.military.holyobservation.HolyDefenderObservation.Preparation;
import org.xar.ck3.control.wave3.military.holyobservation.HolyDefenderObservation.Query;

/** Four pure stages in the existing projection host. Original Service retains the single native query. */
public final class HolyDefenderObservationPort implements ProjectionPort<HolyDefenderObservationPort.Input, HolyDefenderObservationPort.Reply> {
    public static final String NORMALIZE_SCHEMA = "xar.ck3.holy-defender-normalize-input.v1";
    public static final String PROJECT_SCHEMA = "xar.ck3.holy-defender-project-input.v1";
    public static final String PLAN_SCHEMA = "xar.ck3.holy-defender-plan-input.v1";
    public sealed interface Input permits Normalize, Project, Prepare, Fold { HolySdkJson.Source source(); }
    public record Normalize(HolySdkJson.Source source, HolyDefenderInputs value) implements Input { }
    public record Project(HolySdkJson.Source source, Observation observation) implements Input { }
    public record Prepare(HolySdkJson.Source source, Preparation preparation) implements Input { }
    public record Fold(HolySdkJson.Source source, Preparation preparation, Observation observation, String queryError) implements Input { }
    public record Reply(byte[] bytes) {
        public Reply { bytes = org.xar.ck3.control.contracts.projection.ProjectionJson.value(bytes, HolySdkJson.LIMIT).bytes(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    private final ProjectionOperation operation;
    public HolyDefenderObservationPort(ProjectionOperation operation) { this.operation = Objects.requireNonNull(operation); }
    @Override public ProjectionOperation operation() { return operation; }
    @Override public int inputMaximumBytes() { return HolySdkJson.LIMIT; }
    @Override public int outputMaximumBytes() { return HolySdkJson.LIMIT; }

    @Override public Input decode(byte[] raw) {
        HolySdkJson.Source outer = new HolySdkJson.Source(raw);
        ObjectNode envelope = HolyInputValidation.object(outer.tree(), Set.of("operation", "request"));
        String stage = HolyInputValidation.text(envelope.get("operation"));
        HolySdkJson.Source source = outer.select("/request"); JsonNode root = source.tree();
        if (stage.equals("normalize")) {
            schema(root, NORMALIZE_SCHEMA, Set.of("schema", "value", "current_context", "snapshot"));
            JsonNode core = HolyCostJsonAdapter.projectCore(root.get("current_context"));
            var owner = HolyCostJsonAdapter.normalize(core, root.get("snapshot"), StrictJson.text(core.get("declaration_id")), core.get("selected_declaration"));
            return new Normalize(source, HolyDefenderInputsCodec.normalize(root.get("value"), owner, root.get("snapshot")));
        }
        if (stage.equals("project")) {
            schema(root, PROJECT_SCHEMA, Set.of("schema", "normalized_query", "snapshot"));
            return new Project(source, HolyDefenderObservation.observe(root.get("normalized_query"), root.get("snapshot")));
        }
        HolyInputValidation.require(stage.equals("prepare") || stage.equals("fold"), "unknown exact defender stage");
        schema(root, PLAN_SCHEMA, Set.of("schema", "planned", "snapshot", "permission", "query_available", "normalized_query", "query_error"));
        HolyInputValidation.require(root.get("planned").isObject() && root.get("snapshot").isObject(), "original planner containers required");
        boolean permission = bool(root.get("permission")), available = bool(root.get("query_available"));
        JsonNode error = root.get("query_error");
        HolyInputValidation.require(error.isNull() || error.isTextual(), "explicit null or original query error required");
        Preparation prepared = HolyDefenderObservation.prepare(root.get("planned"), root.get("snapshot"), permission, available);
        if (stage.equals("prepare")) { return new Prepare(source, prepared); }
        Observation observed = null;
        if (prepared instanceof Query query && error.isNull()) {
            observed = HolyDefenderObservation.observe(root.get("normalized_query"), root.get("snapshot"));
            HolyInputValidation.require(observed.owner().selectedDeclaration().equals(query.candidate().choice()),
                    "observed declaration differs from the first current ordinary candidate");
        }
        return new Fold(source, prepared, observed, error.isNull() ? null : error.textValue());
    }

    @Override public Reply project(Input input) {
        HolySdkJson.Source source = input.source(); JsonNode root = source.tree();
        return switch (input) {
            case Normalize ignored -> new Reply(source.token("/value"));
            case Project projected -> new Reply(source.merge(HolyDefenderObservation.project(projected.observation(),
                    root.get("normalized_query"), root.get("snapshot")), "/absent", aliases("")));
            case Prepare prepared -> {
                Preparation preparation = prepared.preparation(); ObjectNode directive = StrictJson.object();
                directive.put("query_current_candidate", preparation instanceof Query);
                if (preparation instanceof Query query) {
                    directive.put("expected_revision", query.expectedRevision()).put("declaration_id", query.candidate().choice().declarationId())
                            .put("source_ordinal", query.candidate().sourceOrdinal()).putNull("result");
                } else {
                    directive.putNull("expected_revision").putNull("declaration_id").putNull("source_ordinal");
                    directive.set("result", HolyDefenderObservation.fold(root.get("planned"), root.get("snapshot"), preparation, null, null, null));
                }
                Map<String, String> aliases = aliases("/result/plan/" + HolyDefenderObservation.ANNOTATION);
                aliases.put("/result", "/planned"); yield new Reply(source.merge(directive, "/absent", aliases));
            }
            case Fold folded -> {
                ObjectNode result = HolyDefenderObservation.fold(root.get("planned"), root.get("snapshot"), folded.preparation(),
                        root.get("normalized_query"), folded.observation(), folded.queryError());
                yield new Reply(source.merge(result, "/planned", aliases("/plan/" + HolyDefenderObservation.ANNOTATION)));
            }
        };
    }
    @Override public byte[] encode(Reply reply) { return reply.bytes(); }

    private static void schema(JsonNode value, String expected, Set<String> fields) {
        ObjectNode root = HolyInputValidation.object(value, fields);
        HolyInputValidation.require(expected.equals(HolyInputValidation.text(root.get("schema"))), "exact defender request schema required");
    }
    private static boolean bool(JsonNode value) {
        HolyInputValidation.require(value != null && value.isBoolean(), "actual boolean required"); return value.booleanValue();
    }
    private static Map<String, String> aliases(String prefix) {
        Map<String, String> aliases = new LinkedHashMap<>();
        for (String field : new String[]{"snapshot_id", "revision", "native_revision", "date_raw"}) {
            aliases.put(prefix + "/source_frame/" + field, "/snapshot/" + field);
        }
        aliases.put(prefix + "/source_frame/played_character_id", "/snapshot/played_character/character_id");
        aliases.put(prefix + "/query_backend_id", "/normalized_query/backend_id");
        aliases.put(prefix + "/query_status", "/normalized_query/query_status");
        aliases.put(prefix + "/declaration_context_available", "/normalized_query/available");
        aliases.put(prefix + "/declaration_context_unavailable_reason", "/normalized_query/unavailable_reason");
        aliases.put(prefix + "/cb_cost", "/normalized_query/cb_cost");
        aliases.put(prefix + "/selected_declaration", "/normalized_query/selected_declaration");
        aliases.put(prefix + "/" + HolyDefenderObservation.CHILD, "/normalized_query/" + HolyDefenderObservation.CHILD);
        return aliases;
    }
}
