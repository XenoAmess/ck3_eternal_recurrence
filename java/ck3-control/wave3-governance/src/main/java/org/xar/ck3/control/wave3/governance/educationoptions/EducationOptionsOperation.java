package org.xar.ck3.control.wave3.governance.educationoptions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsAssembly.Attempt;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsAssembly.Observation;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsAssembly.RequestIntent;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel.*;

/** Single bounded typed operation port for the existing two helpers and actual Service option/request consumers. */
public final class EducationOptionsOperation {
    public static final String SCHEMA = "xar.java.education-options.operation/v1";
    private EducationOptionsOperation() { }
    public sealed interface Request permits RowsRequest, MaterializationRequest, IntentRequest, AttemptsRequest { }
    public record RowsRequest(RowsValidation validation) implements Request { public RowsRequest { Objects.requireNonNull(validation); } }
    public record MaterializationRequest(MaterializationValidation validation) implements Request { public MaterializationRequest { Objects.requireNonNull(validation); } }
    public record IntentRequest(Optional<Pair> observedPair, Optional<Rows> optionRows) implements Request {
        public IntentRequest { observedPair = Objects.requireNonNull(observedPair); optionRows = Objects.requireNonNull(optionRows); }
    }
    public record AttemptsRequest(List<Observation> observations, List<Integer> orderedIndices) implements Request {
        public AttemptsRequest { observations = List.copyOf(observations); orderedIndices = List.copyOf(orderedIndices); }
    }
    public sealed interface Result permits RowsResult, MaterializationResult, IntentResult, AttemptsResult { }
    public record RowsResult(Rows rows) implements Result { public RowsResult { Objects.requireNonNull(rows); } }
    public record MaterializationResult(Materialization materialization) implements Result { public MaterializationResult { Objects.requireNonNull(materialization); } }
    public record IntentResult(Optional<RequestIntent> intent) implements Result { public IntentResult { intent = Objects.requireNonNull(intent); } }
    public record AttemptsResult(List<Attempt> attempts) implements Result {
        public AttemptsResult { attempts = List.copyOf(attempts); }
    }
    public static byte[] apply(byte[] input) { return encode(execute(decode(input))); }
    public static Result execute(Request request) {
        return switch (request) {
            case RowsRequest value -> new RowsResult(value.validation().rows());
            case MaterializationRequest value -> new MaterializationResult(value.validation().materialization());
            case IntentRequest value -> new IntentResult(EducationOptionsAssembly.selectedIntent(value.observedPair(), value.optionRows()));
            case AttemptsRequest value -> new AttemptsResult(EducationOptionsAssembly.attempts(value.observations(), value.orderedIndices()));
        };
    }
    /** JSON nodes remain inside the validated byte boundary. Shared host registers apply(byte[]) without interpreting business fields. */
    static Request decode(byte[] bytes) {
        JsonNode root = EducationOptionsCodec.parseBoundary(bytes);
        StrictJson.object(root, Set.of("schema", "operation", "payload"));
        StrictJson.require(SCHEMA.equals(text(root, "schema")), "education option operation schema");
        JsonNode payload = EducationOptionsCodec.object(field(root, "payload"));
        return switch (text(root, "operation")) {
            case "validate_rows" -> {
                StrictJson.object(payload, Set.of("context", "interaction_key", "context_status"));
                JsonNode context = EducationOptionsCodec.object(field(payload, "context"));
                yield new RowsRequest(new RowsValidation(text(context, "exact_build"), text(payload, "interaction_key"),
                        availability(field(payload, "context_status")), EducationOptionsCodec.rows(field(context, "education_option_rows"))));
            }
            case "validate_materialization" -> {
                StrictJson.object(payload, Set.of("context", "interaction_key", "context_status"));
                JsonNode context = EducationOptionsCodec.object(field(payload, "context"));
                Materialization materialization = EducationOptionsCodec.materialization(field(context, "education_request_materialization"));
                Optional<Availability> rows = Optional.empty(); Optional<Pair> roles = Optional.empty();
                if (materialization.status() == Availability.AVAILABLE) {
                    rows = Optional.of(EducationOptionsCodec.status(EducationOptionsCodec.object(field(context, "education_option_rows"))));
                    if (materialization.pair().isPresent()) {
                        JsonNode role = EducationOptionsCodec.object(field(context, "effective_roles"));
                        roles = Optional.of(new Pair(EducationOptionsCodec.id(role, "secondary_recipient_id"), EducationOptionsCodec.id(role, "secondary_actor_id")));
                    }
                }
                yield new MaterializationRequest(new MaterializationValidation(text(context, "exact_build"), text(payload, "interaction_key"),
                        availability(field(payload, "context_status")), materialization, rows, roles));
            }
            case "selected_intent" -> {
                StrictJson.object(payload, Set.of("candidate", "option_rows"));
                JsonNode candidate = EducationOptionsCodec.object(field(payload, "candidate")), flag = field(candidate, "available");
                StrictJson.require(flag.isBoolean(), "candidate availability requires Boolean token");
                Optional<Pair> pair = flag.booleanValue() ? Optional.of(pair(candidate)) : Optional.empty();
                Optional<Rows> rows = Optional.empty(); JsonNode rawRows = field(payload, "option_rows");
                if (pair.isPresent() && rawRows.isObject() && rawRows.has("status") && rawRows.get("status").isTextual()
                        && "available".equals(rawRows.get("status").textValue())) { rows = Optional.of(EducationOptionsCodec.rows(rawRows)); }
                yield new IntentRequest(pair, rows);
            }
            case "request_attempts" -> {
                StrictJson.object(payload, Set.of("observations", "ordered_observation_indices"));
                List<Observation> observations = new ArrayList<>(); JsonNode entries = field(payload, "observations");
                StrictJson.require(entries.isArray(), "actual observations array required");
                for (JsonNode raw : entries) {
                    EducationOptionsCodec.object(raw); JsonNode rawPair = field(raw, "request_preference_pair"), rawIntent = field(raw, "default_request_intent");
                    observations.add(new Observation(rawPair.isNull() ? Optional.empty() : Optional.of(pair(rawPair)),
                            rawIntent.isNull() ? Optional.empty() : Optional.of(intent(rawIntent))));
                }
                List<Integer> indices = new ArrayList<>(); JsonNode order = field(payload, "ordered_observation_indices");
                StrictJson.require(order.isArray(), "actual preference order array required");
                for (JsonNode index : order) { indices.add((int) StrictJson.integer(index, 0, Integer.MAX_VALUE)); }
                yield new AttemptsRequest(observations, indices);
            }
            default -> throw new IllegalArgumentException("known education option operation required");
        };
    }
    static byte[] encode(Result value) {
        JsonNode node = switch (value) {
            case RowsResult rows -> EducationOptionsCodec.rowsNode(rows.rows());
            case MaterializationResult materialization -> EducationOptionsCodec.materializationNode(materialization.materialization());
            case IntentResult intent -> intent.intent().map(EducationOptionsOperation::intentNode).orElse(null);
            case AttemptsResult attempts -> {
                ArrayNode array = StrictJson.object().putArray("rows");
                for (Attempt attempt : attempts.attempts()) {
                    ArrayNode row = array.addArray(); row.add(attempt.observationIndex()); row.add(intentNode(attempt.intent())); row.add(attempt.variant().wire());
                }
                yield array;
            }
        };
        return EducationOptionsCodec.encode(node == null ? com.fasterxml.jackson.databind.node.NullNode.getInstance() : node);
    }
    private static Pair pair(JsonNode value) {
        EducationOptionsCodec.object(value); return new Pair(EducationOptionsCodec.id(value, "child_full_id"), EducationOptionsCodec.id(value, "guardian_full_id"));
    }
    private static RequestIntent intent(JsonNode value) {
        StrictJson.object(value, Set.of("interaction_key", "recipient_id", "child_full_id", "guardian_full_id", "requested_option_keys"));
        Pair pair = pair(value);
        StrictJson.require(EducationOptionsAssembly.INTERACTION.equals(text(value, "interaction_key"))
                && EducationOptionsCodec.id(value, "recipient_id") == pair.childFullId(), "intent interaction or recipient differs from actual child pair");
        JsonNode keys = field(value, "requested_option_keys"); StrictJson.require(keys.isArray(), "original selected option key array required");
        List<String> result = new ArrayList<>(); for (JsonNode key : keys) { result.add(EducationOptionsModel.key(StrictJson.text(key))); }
        return new RequestIntent(pair, result);
    }
    private static ObjectNode intentNode(RequestIntent value) {
        ObjectNode node = StrictJson.object(); node.put("interaction_key", EducationOptionsAssembly.INTERACTION).put("recipient_id", value.pair().childFullId())
                .put("child_full_id", value.pair().childFullId()).put("guardian_full_id", value.pair().guardianFullId());
        ArrayNode keys = node.putArray("requested_option_keys"); value.requestedOptionKeys().forEach(keys::add); return node;
    }
    private static Availability availability(JsonNode value) {
        ObjectNode node = StrictJson.object(); node.set("status", value); return EducationOptionsCodec.status(node);
    }
    private static JsonNode field(JsonNode node, String key) { return EducationOptionsCodec.required(node, key); }
    private static String text(JsonNode node, String key) { return EducationOptionsCodec.text(node, key); }
}
