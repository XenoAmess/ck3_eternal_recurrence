package org.xar.ck3.control.g2.m2;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** M2 routing only. Embedded legacy/native JSON bytes keep their original number and null tokens. */
public final class M2Payload {
    public static final int MAX_BYTES = 2_097_152;
    public static final String INPUT_SCHEMA = "xar.g2.m2.research-input/v1";
    public static final String RESULT_SCHEMA = "xar.g2.m2.research-result/v1";
    private static final JsonFactory JSON = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private M2Payload() { }

    public enum Operation {
        EVENT_PLAN_CANDIDATE("event_plan_candidate"),
        EVENT_PLAN_SOURCE_REVIEWED("event_plan_source_reviewed"),
        EVENT_BEFORE("event_before"),
        EVENT_AFTER("event_after"),
        INTERACTION_PLAN("interaction_plan"),
        INTERACTION_BEFORE("interaction_before"),
        INTERACTION_AFTER("interaction_after"),
        INTERACTION_REGISTRY_LOOKUP("interaction_registry_lookup"),
        EVENT_REGISTRY_LOOKUP("event_registry_lookup"),
        EVENT_SOURCE_REVIEWED_RECEIPT("event_source_reviewed_receipt");
        private final String wire;
        Operation(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Operation fromWire(String wire) {
            for (Operation operation : values()) if (operation.wire.equals(wire)) return operation;
            throw new IllegalArgumentException("unsupported M2 operation");
        }
    }
    public record Input(Operation operation, ProjectionJson input) {
        public Input { Objects.requireNonNull(operation); Objects.requireNonNull(input); StrictJson.require(input.isObject(), "M2 legacy input object required"); }
    }
    public record Result(Operation operation, ProjectionJson result) {
        public Result { Objects.requireNonNull(operation); Objects.requireNonNull(result); }
    }
    private record Envelope(Operation operation, ProjectionJson body) { }

    public static ProjectionJson input(Operation operation, ProjectionJson input) {
        Input checked = new Input(operation, input);
        return wrap(INPUT_SCHEMA, checked.operation(), "input", checked.input());
    }
    public static Input decode(ProjectionJson payload) {
        Envelope envelope = read(payload, INPUT_SCHEMA, "input", true);
        return new Input(envelope.operation(), envelope.body());
    }
    public static ProjectionJson output(Operation operation, ProjectionJson result) {
        return wrap(RESULT_SCHEMA, Objects.requireNonNull(operation), "result", Objects.requireNonNull(result));
    }
    public static Result decodeResult(ProjectionJson payload) {
        Envelope envelope = read(payload, RESULT_SCHEMA, "result", false);
        return new Result(envelope.operation(), envelope.body());
    }
    public static ProjectionJson unwrapResult(ProjectionJson payload) { return decodeResult(payload).result(); }

    private static ProjectionJson wrap(String schema, Operation operation, String field, ProjectionJson body) {
        byte[] header = ("{\"schema\":\"" + schema + "\",\"operation\":\"" + operation.wire() + "\",\"" + field + "\":").getBytes(StandardCharsets.UTF_8);
        ByteArrayOutputStream output = new ByteArrayOutputStream(header.length + body.size() + 1);
        output.writeBytes(header); output.writeBytes(body.bytes()); output.write('}');
        return ProjectionJson.object(output.toByteArray(), MAX_BYTES);
    }
    private static Envelope read(ProjectionJson payload, String schema, String bodyField, boolean object) {
        Objects.requireNonNull(payload); byte[] raw = payload.bytes();
        StrictJson.require(payload.isObject() && raw.length <= MAX_BYTES, "bounded M2 wrapper object required");
        String actualSchema = null; Operation operation = null; ProjectionJson body = null; Set<String> fields = new HashSet<>();
        try (JsonParser parser = JSON.createParser(raw)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "M2 wrapper object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "M2 wrapper field required");
                String name = parser.currentName(); StrictJson.require(fields.add(name), "duplicate M2 wrapper field");
                JsonToken token = parser.nextToken(); StrictJson.require(token != null, "M2 wrapper value required");
                if ("schema".equals(name)) {
                    StrictJson.require(token == JsonToken.VALUE_STRING, "M2 schema string required"); actualSchema = parser.getText();
                } else if ("operation".equals(name)) {
                    StrictJson.require(token == JsonToken.VALUE_STRING, "M2 operation string required"); operation = Operation.fromWire(parser.getText());
                } else if (bodyField.equals(name)) {
                    StrictJson.require(!object || token == JsonToken.START_OBJECT, "M2 legacy input object required");
                    long start = parser.currentTokenLocation().getByteOffset(); parser.skipChildren(); long end = parser.currentLocation().getByteOffset();
                    StrictJson.require(start >= 0 && end > start && end <= raw.length, "embedded M2 byte range unavailable");
                    byte[] original = Arrays.copyOfRange(raw, Math.toIntExact(start), Math.toIntExact(end));
                    body = object ? ProjectionJson.object(original, MAX_BYTES) : ProjectionJson.value(original, MAX_BYTES);
                } else throw new IllegalArgumentException("unknown M2 wrapper field");
            }
            StrictJson.require(parser.nextToken() == null && schema.equals(actualSchema)
                    && fields.equals(Set.of("schema", "operation", bodyField)) && operation != null && body != null,
                    "exact versioned M2 wrapper required");
            return new Envelope(operation, body);
        } catch (IOException invalid) { throw new IllegalArgumentException("invalid M2 wrapper JSON", invalid); }
    }
}
