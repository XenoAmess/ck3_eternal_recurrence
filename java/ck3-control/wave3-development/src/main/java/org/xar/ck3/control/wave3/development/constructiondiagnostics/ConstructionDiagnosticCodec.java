package org.xar.ck3.control.wave3.development.constructiondiagnostics;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.xar.ck3.control.contracts.StrictJson;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import static org.xar.ck3.control.wave3.development.constructiondiagnostics.ConstructionDiagnosticModel.*;

/** Streaming fixed-path projection: skipped world rows never become retained DTOs. */
public final class ConstructionDiagnosticCodec {
    public static final int MAX_INPUT_BYTES = 1_048_576;
    private static final JsonFactory FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64).maxNumberLength(1024).maxStringLength(MAX_INPUT_BYTES).build()).build();
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final Set<String> INPUT_FIELDS = Set.of("schema", "frame", "step", "revision", "request_id", "timeout_seconds", "wait_elapsed_seconds", "frame_python_type", "result_python_type");
    private ConstructionDiagnosticCodec() { }

    public static Request decode(byte[] bytes) {
        try (JsonParser parser = parser(bytes, MAX_INPUT_BYTES)) {
            require(parser.nextToken() == JsonToken.START_OBJECT, "diagnostic input object");
            Set<String> fields = new HashSet<>(); String schema = null, step = null, request = null, framePythonType = null, resultPythonType = null;
            BigInteger revision = null; Frame frame = null; Value timeout = null; Double elapsed = null;
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); require(INPUT_FIELDS.contains(name), "unknown diagnostic input field"); fields.add(name); parser.nextToken();
                switch (name) {
                    case "schema" -> schema = string(parser);
                    case "step" -> step = string(parser);
                    case "request_id" -> request = string(parser);
                    case "frame_python_type" -> framePythonType = string(parser);
                    case "result_python_type" -> resultPythonType = string(parser);
                    case "revision" -> {
                        require(parser.currentToken() == JsonToken.VALUE_NUMBER_INT, "revision requires integer token"); revision = parser.getBigIntegerValue();
                        require(revision.signum() > 0 && revision.bitLength() <= 64, "revision must be uint64");
                    }
                    case "frame" -> frame = frame(parser);
                    case "timeout_seconds" -> timeout = value(parser);
                    case "wait_elapsed_seconds" -> { require(parser.currentToken().isNumeric(), "elapsed numeric measurement required"); elapsed = parser.getDoubleValue(); }
                    default -> throw new IllegalStateException("unhandled diagnostic field");
                }
            }
            require(fields.equals(INPUT_FIELDS) && "xar.construction-diagnostic-input.v1".equals(schema), "exact diagnostic input schema");
            require(parser.nextToken() == null, "trailing diagnostic JSON");
            Frame typed = new Frame(frame.type(), framePythonType, frame.frameType(), frame.protocol(), frame.requestId(), frame.ok(), frame.error(),
                    frame.resultType(), resultPythonType, frame.resultStep(), frame.resultAccepted(), frame.probeFields());
            return new Request(typed, step, revision, request, timeout, elapsed);
        } catch (IOException failure) { throw new IllegalArgumentException("invalid construction diagnostic JSON", failure); }
    }

    public static byte[] project(byte[] bytes) {
        Request request = decode(bytes);
        return encode(ConstructionDiagnosticProjection.project(request, value -> uncheckedEncode(value).length));
    }
    public static byte[] encode(Projection projection) {
        byte[] encoded = uncheckedEncode(projection); require(encoded.length <= LIMIT, "bounded diagnostic exceeds 4096 bytes"); return encoded;
    }
    public static Projection decodeProjection(byte[] bytes) {
        try (JsonParser parser = parser(bytes, LIMIT)) {
            require(parser.nextToken() == JsonToken.START_OBJECT, "diagnostic attachment object");
            Map<Field, Value> fields = new LinkedHashMap<>();
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                Field field = Field.fromWire(parser.currentName()); parser.nextToken(); Value value = value(parser);
                require(!(value instanceof Container), "diagnostic attachment must contain only scalars"); fields.put(field, value);
            }
            require(parser.nextToken() == null, "trailing diagnostic attachment");
            Projection result = new Projection(fields); encode(result); return result;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid diagnostic attachment", failure); }
    }

    private static Frame frame(JsonParser parser) throws IOException {
        PythonType type = type(parser.currentToken());
        if (type != PythonType.DICT) { parser.skipChildren(); return absentFrame(type); }
        Value frameType = new Nil(), protocol = new Nil(), request = new Nil(), ok = new Nil(), error = new Nil();
        Result result = new Result(PythonType.NONE, new Nil(), new Nil()); Map<Field, Value> probe = new EnumMap<>(Field.class);
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            String name = parser.currentName(); parser.nextToken();
            switch (name) {
                case "type" -> frameType = value(parser);
                case "protocol_version" -> protocol = value(parser);
                case "request_id" -> request = value(parser);
                case "ok" -> ok = value(parser);
                case "error" -> error = value(parser);
                case "result" -> result = result(parser);
                case "private_probe" -> probe(parser, probe);
                default -> parser.skipChildren();
            }
        }
        return new Frame(type, type.wire(), frameType, protocol, request, ok, error, result.type(), result.type().wire(), result.step(), result.accepted(), probe);
    }
    private record Result(PythonType type, Value step, Value accepted) { }
    private static Result result(JsonParser parser) throws IOException {
        PythonType type = type(parser.currentToken());
        if (type != PythonType.DICT) { parser.skipChildren(); return new Result(type, new Nil(), new Nil()); }
        Value step = new Nil(), accepted = new Nil();
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            String name = parser.currentName(); parser.nextToken();
            if (name.equals("step")) step = value(parser); else if (name.equals("accepted")) accepted = value(parser); else parser.skipChildren();
        }
        return new Result(type, step, accepted);
    }
    private static void probe(JsonParser parser, Map<Field, Value> values) throws IOException {
        if (parser.currentToken() != JsonToken.START_OBJECT) { parser.skipChildren(); return; }
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            String name = parser.currentName(); parser.nextToken();
            Field field = switch (name) {
                case "status" -> Field.PROBE_STATUS; case "failure" -> Field.PROBE_FAILURE; case "schema_version" -> Field.PROBE_SCHEMA;
                case "advertised" -> Field.PROBE_ADVERTISED; case "snapshot_revision" -> Field.PROBE_REVISION; case "date_raw" -> Field.PROBE_DATE;
                case "proof_epoch" -> Field.PROBE_EPOCH; default -> null;
            };
            if (field != null) values.put(field, value(parser));
            else if (name.equals("player_model_sources")) model(parser, values);
            else if (name.equals("player_world_building_sources")) world(parser, values);
            else parser.skipChildren();
        }
    }
    private static void model(JsonParser parser, Map<Field, Value> values) throws IOException {
        if (parser.currentToken() != JsonToken.START_OBJECT) { parser.skipChildren(); return; }
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            String name = parser.currentName(); parser.nextToken();
            Field field = switch (name) {
                case "status" -> Field.MODEL_STATUS; case "failure" -> Field.MODEL_FAILURE; case "snapshot_revision" -> Field.MODEL_REVISION;
                case "date_raw" -> Field.MODEL_DATE; case "player_character_id" -> Field.MODEL_ACTOR; default -> null;
            };
            if (field != null) values.put(field, value(parser)); else parser.skipChildren();
        }
    }
    private static void world(JsonParser parser, Map<Field, Value> values) throws IOException {
        if (parser.currentToken() != JsonToken.START_OBJECT) { parser.skipChildren(); return; }
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            String name = parser.currentName(); parser.nextToken();
            if (name.equals("status")) values.put(Field.WORLD_STATUS, value(parser));
            else if (name.equals("failure")) values.put(Field.WORLD_FAILURE, value(parser));
            else if (name.equals("definition_identity_diagnostic")) definition(parser, values); else parser.skipChildren();
        }
    }
    private static void definition(JsonParser parser, Map<Field, Value> values) throws IOException {
        if (parser.currentToken() != JsonToken.START_OBJECT) { parser.skipChildren(); return; }
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            String name = parser.currentName(); parser.nextToken();
            if (name.equals("stage")) values.put(Field.DEFINITION_STAGE, value(parser));
            else if (name.equals("failed_index")) values.put(Field.DEFINITION_INDEX, value(parser)); else parser.skipChildren();
        }
    }
    private static Value value(JsonParser parser) throws IOException {
        return switch (parser.currentToken()) {
            case VALUE_NULL -> new Nil(); case VALUE_TRUE -> new Flag(true); case VALUE_FALSE -> new Flag(false);
            case VALUE_NUMBER_INT -> new IntegerValue(parser.getBigIntegerValue()); case VALUE_NUMBER_FLOAT -> new FloatingValue(parser.getDoubleValue());
            case VALUE_STRING -> new Text(parser.getText());
            case START_OBJECT -> { parser.skipChildren(); yield new Container(PythonType.DICT); }
            case START_ARRAY -> { parser.skipChildren(); yield new Container(PythonType.LIST); }
            default -> throw new IllegalArgumentException("JSON diagnostic value required");
        };
    }
    private static PythonType type(JsonToken token) {
        return switch (token) {
            case VALUE_NULL -> PythonType.NONE; case VALUE_TRUE, VALUE_FALSE -> PythonType.BOOL; case VALUE_NUMBER_INT -> PythonType.INT;
            case VALUE_NUMBER_FLOAT -> PythonType.FLOAT; case VALUE_STRING -> PythonType.STR; case START_OBJECT -> PythonType.DICT; case START_ARRAY -> PythonType.LIST;
            default -> throw new IllegalArgumentException("JSON frame value required");
        };
    }
    private static String string(JsonParser parser) throws IOException {
        require(parser.currentToken() == JsonToken.VALUE_STRING, "diagnostic request text required"); return StrictJson.text(parser.getText());
    }
    private static JsonParser parser(byte[] raw, int limit) throws IOException {
        require(raw != null && raw.length > 0 && raw.length <= limit, "bounded diagnostic input required");
        String utf8 = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString(); return FACTORY.createParser(utf8);
    }
    private static byte[] uncheckedEncode(Projection projection) {
        StringBuilder result = new StringBuilder("{"); boolean first = true;
        for (Map.Entry<Field, Value> field : projection.fields().entrySet()) {
            if (!first) result.append(','); first = false; result.append(quote(field.getKey().wire())).append(':');
            Value value = field.getValue();
            if (value instanceof Nil) result.append("null");
            else if (value instanceof Flag flag) result.append(flag.value());
            else if (value instanceof IntegerValue integer) result.append(integer.value());
            else if (value instanceof FloatingValue number) result.append(pythonFloat(number.value()));
            else if (value instanceof Text text) result.append(quote(text.value()));
            else throw new IllegalArgumentException("scalar diagnostic output required");
        }
        return result.append('}').toString().getBytes(StandardCharsets.UTF_8);
    }
    private static String pythonFloat(double value) {
        require(Double.isFinite(value), "finite diagnostic float required");
        if (value == 0.0) return Double.doubleToRawLongBits(value) < 0 ? "-0.0" : "0.0";
        BigDecimal decimal = BigDecimal.valueOf(value).stripTrailingZeros(); int exponent = decimal.precision() - decimal.scale() - 1;
        if (exponent < -4 || exponent >= 16) {
            String coefficient = decimal.movePointLeft(exponent).toPlainString();
            int absolute = Math.abs(exponent); return coefficient + "e" + (exponent < 0 ? "-" : "+") + (absolute < 10 ? "0" : "") + absolute;
        }
        String plain = decimal.toPlainString(); return plain.indexOf('.') < 0 ? plain + ".0" : plain;
    }
    private static String quote(String value) {
        try { return JSON.writeValueAsString(value); } catch (IOException failure) { throw new IllegalStateException("diagnostic text encoding", failure); }
    }
    private static void require(boolean condition, String reason) { if (!condition) throw new IllegalArgumentException(reason); }
}
