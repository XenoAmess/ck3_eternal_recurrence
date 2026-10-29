package org.xar.ck3.control.wave3.development.constructiondiagnostics;

import java.math.BigInteger;
import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Finite diagnostic projection only; none of these gates is a gameplay or source qualification. */
public final class ConstructionDiagnosticModel {
    public static final String MARKER = "construction_transport_v1";
    public static final int LIMIT = 4096;
    private ConstructionDiagnosticModel() { }
    public sealed interface Value permits Nil, Flag, IntegerValue, FloatingValue, Text, Container { }
    public record Nil() implements Value { }
    public record Flag(boolean value) implements Value { }
    public record IntegerValue(BigInteger value) implements Value { public IntegerValue { Objects.requireNonNull(value); } }
    public record FloatingValue(double value) implements Value { }
    public record Text(String value) implements Value { public Text { Objects.requireNonNull(value); } }
    public record Container(PythonType type) implements Value {
        public Container { if (type != PythonType.DICT && type != PythonType.LIST) throw new IllegalArgumentException("container type"); }
    }
    public enum PythonType {
        NONE("NoneType"), BOOL("bool"), INT("int"), FLOAT("float"), STR("str"), DICT("dict"), LIST("list");
        private final String wire;
        PythonType(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Field {
        SCHEMA("schema_version"), SOURCE("source"), DIAGNOSTIC_ONLY("diagnostic_only"), CLASSIFICATION("classification"),
        REQUEST_ID("request_id"), STEP("step"), REVISION("expected_native_revision"), TIMEOUT("effective_timeout_seconds"),
        ELAPSED("wait_elapsed_seconds"), FRAME_TYPE("frame_python_type"), GATE_MAPPING("gate_mapping"), GATE_TYPE("gate_type"),
        GATE_PROTOCOL("gate_protocol"), GATE_REQUEST("gate_request_id"), GATE_OK("gate_ok"), GATE_RESULT("gate_result_mapping"),
        RECEIVED_TYPE("received_type"), RECEIVED_PROTOCOL("received_protocol_version"), RECEIVED_REQUEST("received_request_id"), RECEIVED_OK("received_ok"),
        NATIVE_ERROR("native_error"), RESULT_TYPE("result_python_type"), RESULT_STEP("result_step"), RESULT_ACCEPTED("result_accepted"),
        PROBE_STATUS("probe_status"), PROBE_FAILURE("probe_failure"), PROBE_SCHEMA("probe_schema_version"),
        PROBE_ADVERTISED("probe_advertised"), PROBE_REVISION("probe_snapshot_revision"), PROBE_DATE("probe_date_raw"), PROBE_EPOCH("probe_proof_epoch"),
        MODEL_STATUS("model_status"), MODEL_FAILURE("model_failure"), MODEL_REVISION("model_snapshot_revision"), MODEL_DATE("model_date_raw"),
        MODEL_ACTOR("model_actor_character_id"), WORLD_STATUS("world_status"), WORLD_FAILURE("world_failure"),
        DEFINITION_STAGE("definition_identity_stage"), DEFINITION_INDEX("definition_identity_failed_index"),
        TEXT_TRUNCATED("text_truncated_to_fit"), LIMIT_REACHED("projection_limit_reached");
        private final String wire;
        Field(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Field fromWire(String wire) {
            for (Field field : values()) if (field.wire.equals(wire)) return field;
            throw new IllegalArgumentException("unknown construction diagnostic field " + wire);
        }
    }
    public enum Classification {
        ABSENT("result_absent_cause_unknown"), INVALID_ENVELOPE("invalid_envelope"), REJECTED("matched_native_rejected"), INVALID_RESULT("invalid_result");
        private final String wire;
        Classification(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Frame(PythonType type, String pythonTypeName, Value frameType, Value protocol, Value requestId, Value ok,
            Value error, PythonType resultType, String resultPythonTypeName, Value resultStep, Value resultAccepted,
            Map<Field, Value> probeFields) {
        public Frame { probeFields = Map.copyOf(probeFields); }
        public boolean mapping() { return type == PythonType.DICT; }
        public boolean resultMapping() { return resultType == PythonType.DICT; }
    }
    public record Request(Frame frame, String step, BigInteger revision, String requestId, Value timeout, double elapsed) { }
    public record Projection(Map<Field, Value> fields) {
        public Projection {
            fields = Collections.unmodifiableMap(new LinkedHashMap<>(fields));
            if (!new IntegerValue(BigInteger.ONE).equals(fields.get(Field.SCHEMA))
                    || !new Text(MARKER).equals(fields.get(Field.SOURCE))
                    || !new Flag(true).equals(fields.get(Field.DIAGNOSTIC_ONLY)))
                throw new IllegalArgumentException("construction diagnostic marker and version required");
            for (Map.Entry<Field, Value> entry : fields.entrySet()) {
                Objects.requireNonNull(entry.getKey()); Value value = Objects.requireNonNull(entry.getValue());
                if (value instanceof Container || value instanceof FloatingValue number && !Double.isFinite(number.value())
                        || value instanceof IntegerValue integer && (integer.value().compareTo(BigInteger.ONE.shiftLeft(63).negate()) < 0
                        || integer.value().compareTo(BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE)) > 0))
                    throw new IllegalArgumentException("projected scalar required");
                if (value instanceof Text text && !text.value().isEmpty()) StrictJson.text(text.value());
            }
            Value classification = fields.get(Field.CLASSIFICATION);
            if (!(classification instanceof Text label) || java.util.Arrays.stream(Classification.values()).noneMatch(value -> value.wire().equals(label.value()))
                    || !(fields.get(Field.REQUEST_ID) instanceof Text) || !(fields.get(Field.STEP) instanceof Text))
                throw new IllegalArgumentException("diagnostic classification and request text required");
            boolean fallback = new Flag(true).equals(fields.get(Field.LIMIT_REACHED));
            if (fallback) {
                if (!fields.keySet().equals(Set.of(Field.SCHEMA, Field.SOURCE, Field.DIAGNOSTIC_ONLY, Field.CLASSIFICATION,
                        Field.LIMIT_REACHED, Field.REQUEST_ID, Field.STEP, Field.NATIVE_ERROR, Field.DEFINITION_STAGE,
                        Field.PROBE_REVISION, Field.PROBE_DATE, Field.PROBE_EPOCH))) throw new IllegalArgumentException("diagnostic fallback fields");
            } else {
                if (!fields.keySet().containsAll(Set.of(Field.SCHEMA, Field.SOURCE, Field.DIAGNOSTIC_ONLY, Field.CLASSIFICATION,
                        Field.REQUEST_ID, Field.STEP, Field.REVISION, Field.TIMEOUT, Field.ELAPSED, Field.FRAME_TYPE,
                        Field.GATE_MAPPING, Field.GATE_TYPE, Field.GATE_PROTOCOL, Field.GATE_REQUEST, Field.GATE_OK, Field.GATE_RESULT)))
                    throw new IllegalArgumentException("diagnostic required fields");
                for (Field field : new Field[]{Field.GATE_MAPPING, Field.GATE_TYPE, Field.GATE_PROTOCOL, Field.GATE_REQUEST, Field.GATE_OK, Field.GATE_RESULT})
                    if (!(fields.get(field) instanceof Flag)) throw new IllegalArgumentException("diagnostic gate must be boolean");
                if (!(fields.get(Field.REVISION) instanceof Nil || fields.get(Field.REVISION) instanceof IntegerValue)
                        || !(fields.get(Field.FRAME_TYPE) instanceof Text)) throw new IllegalArgumentException("diagnostic identity projection types");
            }
            if (fields.containsKey(Field.TEXT_TRUNCATED) && !new Flag(true).equals(fields.get(Field.TEXT_TRUNCATED)))
                throw new IllegalArgumentException("diagnostic truncation flag");
        }
    }
    public static Frame absentFrame(PythonType type) {
        return new Frame(type, type.wire(), new Nil(), new Nil(), new Nil(), new Nil(), new Nil(), PythonType.NONE, PythonType.NONE.wire(), new Nil(), new Nil(), new EnumMap<>(Field.class));
    }
}
