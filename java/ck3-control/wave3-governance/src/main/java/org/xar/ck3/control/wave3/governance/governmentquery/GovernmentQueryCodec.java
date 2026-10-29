package org.xar.ck3.control.wave3.governance.governmentquery;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Set;
import java.util.function.UnaryOperator;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;
import org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryPort.NativeRequest;
import org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryPort.Rejection;
import org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryPort.SourceFrame;

/** Pure adapter boundary; never opens a pipe, sends a request or waits on CK3. */
public final class GovernmentQueryCodec {
    public static final String PREPARE_SCHEMA = "xar.java-government-query-prepare/v1";
    public static final String CONSUME_SCHEMA = "xar.java-government-query-consume/v1";
    public static final String VALIDATE_RESPONSE_SCHEMA = "xar.java-government-query-validate-response/v1";
    public static final String VALIDATED_RESPONSE_SCHEMA = "xar.java-government-query-response-validated/v1";
    private enum ValidationStage { RESPONSE_ONLY, COMPLETE_QUERY }
    private GovernmentQueryCodec() { }

    public static byte[] prepare(byte[] body) {
        ObjectNode root = parseRequest(body, Set.of("schema", "query_enabled", "expected_revision", "request_id", "before_snapshot"));
        requireInput(PREPARE_SCHEMA.equals(inputText(root.get("schema"))), "government prepare schema differs");
        NativeRequest request = GovernmentQueryPort.prepare(bool(root.get("query_enabled")), integer(root.get("expected_revision")),
                inputText(root.get("request_id")), frame(inputObject(root.get("before_snapshot"))));
        ObjectNode result = StrictJson.object();
        result.put("type", "execute_step"); result.put("protocol_version", 1); result.put("request_id", request.requestId());
        result.put("step", GovernmentQueryPort.STEP); result.put("expected_revision", request.expectedNativeRevision());
        return StrictJson.canonical(result);
    }

    public static byte[] consume(byte[] body) {
        ObjectNode root = parseRequest(body, Set.of("schema", "expected_revision", "request_id", "before_snapshot", "after_snapshot", "command_result"));
        requireInput(CONSUME_SCHEMA.equals(inputText(root.get("schema"))), "government consume schema differs");
        return validateAndConsume(root, ValidationStage.COMPLETE_QUERY);
    }

    /** Admit a response before the original caller reads the actual after frame. */
    public static byte[] validateResponse(byte[] body) {
        ObjectNode root = parseRequest(body, Set.of("schema", "expected_revision", "request_id", "before_snapshot", "command_result"));
        requireInput(VALIDATE_RESPONSE_SCHEMA.equals(inputText(root.get("schema"))), "government response validation schema differs");
        return validateAndConsume(root, ValidationStage.RESPONSE_ONLY);
    }

    private static byte[] validateAndConsume(ObjectNode root, ValidationStage stage) {
        BigInteger expectedRevision = integer(root.get("expected_revision"));
        String requestId = inputText(root.get("request_id"));
        ObjectNode beforeNode = inputObject(root.get("before_snapshot"));
        SourceFrame before = frame(beforeNode);
        // Revalidate the held source frame, without pretending this performs a fresh read.
        GovernmentQueryPort.prepare(true, expectedRevision, requestId, before);
        JsonNode command = root.get("command_result");
        GovernmentQueryPort.require(command.isObject() && "command_result".equals(optionalText(command.get("type")))
                && requestId.equals(optionalText(command.get("request_id"))) && actualTrue(command.get("ok")),
                Rejection.COMMAND_RESULT_UNAVAILABLE, "government runtime adapter command_result unavailable");
        // Historic caller packets omit this field. When present, its actual token
        // must be integer version 1; no bool/float equality alias is accepted.
        if (command.has("protocol_version")) {
            GovernmentQueryPort.require(BigInteger.ONE.equals(integer(command.get("protocol_version"))),
                    Rejection.COMMAND_RESULT_UNAVAILABLE, "government runtime adapter command_result unavailable");
        }
        JsonNode envelope = command.get("result");
        GovernmentQueryPort.require(envelope != null && envelope.isObject()
                && GovernmentQueryPort.STEP.equals(optionalText(envelope.get("step")))
                && actualTrue(envelope.get("accepted")) && actualTrue(envelope.get("private_build"))
                && actualTrue(envelope.get("read_only")) && actualFalse(envelope.get("advertised")),
                Rejection.ENVELOPE_MALFORMED, "government runtime adapter envelope is malformed");
        ObjectNode normalization = StrictJson.object();
        normalization.put("schema", GovernmentContextCodec.NORMALIZE_SCHEMA);
        normalization.set("snapshot", beforeNode);
        normalization.set("government_observation", envelope.get("government_runtime_adapter"));
        byte[] normalized;
        try { normalized = GovernmentContextCodec.normalizeAdapterProjection(raw(normalization)); }
        catch (ProjectionDomainRejection error) {
            throw new GovernmentQueryPort.QueryRejectedException(Rejection.SOURCE_UNAVAILABLE, error.getMessage());
        }
        if (stage == ValidationStage.RESPONSE_ONLY) {
            ObjectNode response = StrictJson.object();
            response.put("schema", VALIDATED_RESPONSE_SCHEMA).put("status", "validated").put("request_id", requestId);
            response.put("expected_revision", expectedRevision);
            return StrictJson.canonical(response);
        }
        ObjectNode afterNode = inputObject(root.get("after_snapshot"));
        // The original transport compares the entire played-character object.
        // Known IDs/booleans retain strict token admission; numeric-valued opaque
        // metadata compares by exact decimal value, matching legacy dict equality
        // without allowing a JSON boolean to equal an integer.
        validateActorTokens(afterNode.get("played_character"));
        boolean sameActor = sameJson(beforeNode.get("played_character"), afterNode.get("played_character"));
        GovernmentQueryPort.require(actualTrue(afterNode.get("paused"))
                && Objects.equals(optionalInteger(afterNode.get("date_raw")), before.dateRaw()) && sameActor,
                Rejection.CROSSED_PAUSED_FRAME, "government runtime adapter crossed its paused player frame");
        ObjectNode result = object(StrictJson.parse(normalized));
        result.put("queried_revision", expectedRevision); result.put("queried_native_revision", before.nativeRevision());
        text(result, "queried_snapshot_id", before.snapshotId()); text(result, "post_snapshot_id", optionalText(afterNode.get("snapshot_id")));
        return raw(result);
    }

    /** Translate only this core's declared refusal; serializer and programming failures stay technical. */
    public static byte[] prepareProjection(byte[] body) { return projectKnownQueryRefusal(GovernmentQueryCodec::prepare, body); }
    public static byte[] validateResponseProjection(byte[] body) { return projectKnownQueryRefusal(GovernmentQueryCodec::validateResponse, body); }
    public static byte[] consumeProjection(byte[] body) { return projectKnownQueryRefusal(GovernmentQueryCodec::consume, body); }
    private static byte[] projectKnownQueryRefusal(UnaryOperator<byte[]> operation, byte[] body) {
        try { return operation.apply(body); }
        catch (GovernmentQueryPort.QueryRejectedException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static ObjectNode parseRequest(byte[] body, Set<String> fields) {
        try { return StrictJson.object(StrictJson.parse(body), fields); }
        catch (IllegalArgumentException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static String inputText(JsonNode value) {
        try { return StrictJson.text(value); }
        catch (IllegalArgumentException rejected) { throw new ProjectionDomainRejection(rejected.getMessage()); }
    }
    private static ObjectNode inputObject(JsonNode value) {
        requireInput(value != null && value.isObject(), "JSON object required"); return (ObjectNode) value;
    }
    private static void requireInput(boolean admitted, String reason) {
        if (!admitted) { throw new ProjectionDomainRejection(reason); }
    }

    private static SourceFrame frame(ObjectNode snapshot) {
        JsonNode actor = snapshot.get("played_character");
        boolean actorObject = actor != null && actor.isObject();
        // Character IDs are not used by the historical admission predicate, but
        // any present ID is still checked as an exact integer at this boundary.
        validateActorTokens(actor);
        return new SourceFrame(optionalInteger(snapshot.get("revision")), optionalInteger(snapshot.get("native_revision")),
                optionalInteger(snapshot.get("date_raw")), actualTrue(snapshot.get("paused")), actualTrue(snapshot.get("map_ready")),
                actorObject, actorObject && actualTrue(actor.get("alive")), optionalText(snapshot.get("snapshot_id")));
    }

    private static void validateActorTokens(JsonNode actor) {
        if (actor == null || !actor.isObject()) { return; }
        if (actor.has("character_id")) { optionalInteger(actor.get("character_id")); }
        JsonNode alive = actor.get("alive");
        if (alive != null && !alive.isNull()) { bool(alive); }
    }
    private static boolean sameJson(JsonNode left, JsonNode right) {
        if (left == null || right == null) { return left == right; }
        if (left.isNumber() && right.isNumber()) { return left.decimalValue().compareTo(right.decimalValue()) == 0; }
        if (left.isObject() && right.isObject()) {
            if (left.size() != right.size()) { return false; }
            for (var entry : ((ObjectNode) left).properties()) {
                if (!right.has(entry.getKey()) || !sameJson(entry.getValue(), right.get(entry.getKey()))) { return false; }
            }
            return true;
        }
        if (left.isArray() && right.isArray()) {
            if (left.size() != right.size()) { return false; }
            for (int index = 0; index < left.size(); index++) { if (!sameJson(left.get(index), right.get(index))) { return false; } }
            return true;
        }
        return left.equals(right);
    }

    private static ObjectNode object(JsonNode row) {
        StrictJson.require(row != null && row.isObject(), "JSON object required"); return (ObjectNode) row;
    }
    private static BigInteger integer(JsonNode row) {
        requireInput(row != null && row.isIntegralNumber(), "actual integer token required"); return row.bigIntegerValue();
    }
    private static BigInteger optionalInteger(JsonNode row) { return row == null || row.isNull() ? null : integer(row); }
    private static boolean bool(JsonNode row) {
        requireInput(row != null && row.isBoolean(), "actual boolean token required"); return row.booleanValue();
    }
    private static boolean actualTrue(JsonNode row) { return row != null && !row.isNull() && bool(row); }
    private static boolean actualFalse(JsonNode row) { return row != null && !row.isNull() && !bool(row); }
    private static String optionalText(JsonNode row) {
        if (row == null || row.isNull()) { return null; }
        requireInput(row.isTextual(), "actual string token required");
        return row.textValue().isEmpty() ? "" : inputText(row);
    }
    private static void text(ObjectNode row, String name, String value) { if (value == null) { row.putNull(name); } else { row.put(name, value); } }
    private static byte[] raw(JsonNode row) {
        byte[] result = row.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(result.length <= StrictJson.INPUT_MAX_BYTES, "government query payload exceeds byte budget"); return result;
    }
}
