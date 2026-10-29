package org.xar.ck3.control.contracts.projection;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.io.JsonStringEncoder;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;

/** The projection transport has an independent role budget; StrictJson's existing limits remain unchanged. */
public final class ProjectionWire {
    public static final int MAX_ENVELOPE_BYTES = ProjectionJson.MAX_BYTES + 4096;
    private static final Set<String> CALL_FIELDS = Set.of("schema", "schema_version", "request_id", "operation", "payload");
    private static final Set<String> RESULT_FIELDS = Set.of("schema", "schema_version", "request_id", "operation", "status", "result", "error");
    private static final Set<String> SUCCEEDED_FIELDS = Set.of("schema", "schema_version", "request_id", "operation", "status", "result");
    private static final Set<String> REJECTED_FIELDS = Set.of("schema", "schema_version", "request_id", "operation", "status", "error");
    private static final Set<String> ERROR_FIELDS = Set.of("code", "message");
    private ProjectionWire() { }

    public static ProjectionCall decodeCall(byte[] raw) {
        boundedEnvelope(raw); ProjectionJson.requireUtf8(raw);
        String schema = null; String id = null; ProjectionOperation operation = null; ProjectionJson payload = null;
        boolean version = false; Set<String> fields = new HashSet<>();
        try (JsonParser parser = ProjectionJson.FACTORY.createParser(raw)) {
            if (parser.nextToken() != JsonToken.START_OBJECT) { throw ProjectionJson.invalid("projection call object required"); }
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                if (parser.currentToken() != JsonToken.FIELD_NAME) { throw ProjectionJson.invalid("projection call field required"); }
                long fieldStart = parser.currentTokenLocation().getByteOffset();
                String field = parser.currentName();
                if (!CALL_FIELDS.contains(field) || !fields.add(field)) { throw ProjectionJson.invalid("exact projection call fields required"); }
                JsonToken token = parser.nextToken();
                switch (field) {
                    case "schema" -> schema = text(parser);
                    case "schema_version" -> {
                        if (token != JsonToken.VALUE_NUMBER_INT || !parser.getBigIntegerValue().equals(java.math.BigInteger.ONE)) {
                            throw new ProjectionProtocolException(ProjectionError.Code.UNSUPPORTED_VERSION, "exact projection schema_version integer 1 required");
                        }
                        version = true;
                    }
                    case "request_id" -> id = text(parser);
                    case "operation" -> operation = ProjectionOperation.fromWire(text(parser));
                    case "payload" -> {
                        if (token != JsonToken.START_OBJECT) { throw ProjectionJson.invalid("projection payload object required"); }
                        long start = callValueStart(raw, fieldStart); parser.skipChildren();
                        long end = parser.currentLocation().getByteOffset();
                        if (end < start || end > raw.length) throw ProjectionJson.invalid("original payload token span unavailable");
                        while (end < raw.length && jsonWhitespace(raw[Math.toIntExact(end)])) end++;
                        if (start < 0 || end < start || end > raw.length || end - start > ProjectionJson.MAX_BYTES) {
                            throw ProjectionJson.invalid("projection payload span or role budget invalid");
                        }
                        payload = ProjectionJson.object(Arrays.copyOfRange(raw, Math.toIntExact(start), Math.toIntExact(end)), ProjectionJson.MAX_BYTES);
                    }
                    default -> throw ProjectionJson.invalid("unrecognized projection field");
                }
            }
            if (parser.nextToken() != null || !fields.equals(CALL_FIELDS) || !ProjectionCall.SCHEMA.equals(schema) || !version) {
                throw ProjectionJson.invalid("exact versioned projection call required");
            }
            return new ProjectionCall(new ProjectionCall.Identity(id, operation), payload);
        } catch (IOException error) { throw ProjectionJson.invalid("invalid or duplicate projection call JSON"); }
    }

    /** Payload budgets include its supplied JSON bytes, including value-leading/trailing JSON whitespace. */
    private static long callValueStart(byte[] raw, long fieldStart) {
        if (fieldStart < 0 || fieldStart >= raw.length || raw[Math.toIntExact(fieldStart)] != '"') throw ProjectionJson.invalid("original payload field span unavailable");
        int cursor = Math.toIntExact(fieldStart) + 1; boolean closed = false;
        while (cursor < raw.length) {
            byte value = raw[cursor++];
            if (value == '\\') { if (cursor >= raw.length) throw ProjectionJson.invalid("incomplete payload field escape"); cursor++; }
            else if (value == '"') { closed = true; break; }
        }
        while (cursor < raw.length && jsonWhitespace(raw[cursor])) cursor++;
        if (!closed || cursor >= raw.length || raw[cursor] != ':') throw ProjectionJson.invalid("original payload field separator unavailable");
        return cursor + 1L;
    }
    private static boolean jsonWhitespace(byte value) { return value == 32 || value == 9 || value == 10 || value == 13; }

    public static byte[] encodeCall(ProjectionCall call) {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        append(output, "{\"schema\":\"" + ProjectionCall.SCHEMA + "\",\"schema_version\":1,");
        identity(output, call.identity()); append(output, ",\"payload\":"); output.writeBytes(call.payload().bytes()); append(output, "}");
        byte[] raw = output.toByteArray(); boundedEnvelope(raw); return raw;
    }

    /** Decode the exact response envelope while retaining the original result JSON token bytes. */
    public static ProjectionResult decodeResult(byte[] raw) {
        boundedEnvelope(raw); ProjectionJson.requireUtf8(raw);
        String schema = null; String id = null; String status = null; ProjectionOperation operation = null;
        ProjectionJson result = null; ProjectionError error = null; boolean version = false;
        Set<String> fields = new HashSet<>();
        try (JsonParser parser = ProjectionJson.FACTORY.createParser(raw)) {
            if (parser.nextToken() != JsonToken.START_OBJECT) { throw ProjectionJson.invalid("projection result object required"); }
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                if (parser.currentToken() != JsonToken.FIELD_NAME) { throw ProjectionJson.invalid("projection result field required"); }
                String field = parser.currentName();
                if (!RESULT_FIELDS.contains(field) || !fields.add(field)) { throw ProjectionJson.invalid("exact projection result fields required"); }
                JsonToken token = parser.nextToken();
                switch (field) {
                    case "schema" -> schema = text(parser);
                    case "schema_version" -> {
                        if (token != JsonToken.VALUE_NUMBER_INT || !parser.getBigIntegerValue().equals(java.math.BigInteger.ONE)) {
                            throw new ProjectionProtocolException(ProjectionError.Code.UNSUPPORTED_VERSION, "exact projection schema_version integer 1 required");
                        }
                        version = true;
                    }
                    case "request_id" -> { if (token != JsonToken.VALUE_NULL) { id = text(parser); } }
                    case "operation" -> { if (token != JsonToken.VALUE_NULL) { operation = ProjectionOperation.fromWire(text(parser)); } }
                    case "status" -> status = text(parser);
                    case "result" -> result = resultValue(parser, raw);
                    case "error" -> error = error(parser);
                    default -> throw ProjectionJson.invalid("unrecognized projection result field");
                }
            }
            if (parser.nextToken() != null || !ProjectionResult.SCHEMA.equals(schema) || !version) {
                throw ProjectionJson.invalid("exact versioned projection result required");
            }
            if ("succeeded".equals(status) && fields.equals(SUCCEEDED_FIELDS) && id != null && operation != null && result != null) {
                return new ProjectionResult.Succeeded(new ProjectionCall.Identity(id, operation), result);
            }
            if ("rejected".equals(status) && fields.equals(REJECTED_FIELDS) && error != null && (id == null) == (operation == null)) {
                Optional<ProjectionCall.Identity> identity = id == null ? Optional.empty() : Optional.of(new ProjectionCall.Identity(id, operation));
                return new ProjectionResult.Rejected(identity, error);
            }
            throw ProjectionJson.invalid("exact succeeded or rejected projection result required");
        } catch (ProjectionProtocolException failure) { throw failure; }
        catch (IOException failure) { throw ProjectionJson.invalid("invalid or duplicate projection result JSON"); }
        catch (IllegalArgumentException failure) { throw ProjectionJson.invalid("invalid projection result fields"); }
    }

    public static byte[] encodeResult(ProjectionResult result) {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        append(output, "{\"schema\":\"" + ProjectionResult.SCHEMA + "\",\"schema_version\":1,");
        switch (result) {
            case ProjectionResult.Succeeded succeeded -> {
                identity(output, succeeded.identity()); append(output, ",\"status\":\"succeeded\",\"result\":");
                output.writeBytes(succeeded.result().bytes());
            }
            case ProjectionResult.Rejected rejected -> {
                if (rejected.identity().isPresent()) { identity(output, rejected.identity().orElseThrow()); }
                else { append(output, "\"request_id\":null,\"operation\":null"); }
                append(output, ",\"status\":\"rejected\",\"error\":{\"code\":");
                quote(output, rejected.error().code().name().toLowerCase(Locale.ROOT).replace('_', '-'));
                append(output, ",\"message\":"); quote(output, rejected.error().message()); append(output, "}");
            }
        }
        append(output, "}"); byte[] raw = output.toByteArray(); boundedEnvelope(raw); return raw;
    }

    private static String text(JsonParser parser) throws IOException {
        if (parser.currentToken() != JsonToken.VALUE_STRING) { throw ProjectionJson.invalid("projection string field required"); }
        return parser.getText();
    }
    private static ProjectionJson resultValue(JsonParser parser, byte[] raw) throws IOException {
        JsonToken token = parser.currentToken();
        if (token == null || (!token.isScalarValue() && !token.isStructStart())) {
            throw ProjectionJson.invalid("projection result JSON value required");
        }
        long start = parser.currentTokenLocation().getByteOffset(); parser.skipChildren(); parser.finishToken();
        long end = parser.currentLocation().getByteOffset();
        if (start < 0 || end < start || end > raw.length || end - start > ProjectionJson.MAX_BYTES) {
            throw ProjectionJson.invalid("projection result span or role budget invalid");
        }
        return ProjectionJson.value(Arrays.copyOfRange(raw, Math.toIntExact(start), Math.toIntExact(end)), ProjectionJson.MAX_BYTES);
    }
    private static ProjectionError error(JsonParser parser) throws IOException {
        if (parser.currentToken() != JsonToken.START_OBJECT) { throw ProjectionJson.invalid("projection error object required"); }
        ProjectionError.Code code = null; String message = null; Set<String> fields = new HashSet<>();
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            if (parser.currentToken() != JsonToken.FIELD_NAME) { throw ProjectionJson.invalid("projection error field required"); }
            String field = parser.currentName();
            if (!ERROR_FIELDS.contains(field) || !fields.add(field)) { throw ProjectionJson.invalid("exact projection error fields required"); }
            parser.nextToken();
            switch (field) {
                case "code" -> code = ProjectionError.Code.fromWire(text(parser));
                case "message" -> message = text(parser);
                default -> throw ProjectionJson.invalid("unrecognized projection error field");
            }
        }
        if (!fields.equals(ERROR_FIELDS) || code == null || message == null) { throw ProjectionJson.invalid("complete projection error required"); }
        return new ProjectionError(code, message);
    }
    private static void identity(ByteArrayOutputStream output, ProjectionCall.Identity identity) {
        append(output, "\"request_id\":"); quote(output, identity.requestId()); append(output, ",\"operation\":"); quote(output, identity.operation().wire());
    }
    private static void quote(ByteArrayOutputStream output, String value) {
        append(output, "\""); output.writeBytes(JsonStringEncoder.getInstance().quoteAsUTF8(value)); append(output, "\"");
    }
    private static void append(ByteArrayOutputStream output, String value) { output.writeBytes(value.getBytes(StandardCharsets.UTF_8)); }
    private static void boundedEnvelope(byte[] raw) {
        if (raw == null || raw.length == 0 || raw.length > MAX_ENVELOPE_BYTES) { throw ProjectionJson.invalid("projection envelope exceeds transport role budget"); }
    }
}
