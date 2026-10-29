package org.xar.ck3.control.wave2.development.constructioneconomy;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashSet;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Shared capture boundary. Reference vectors never attest a current consumer or host run. */
public final class ConstructionCashCaptureContract {
    public static final String LEGACY_SCHEMA = "xar.construction-cash-original-consumers-golden.v1";
    public static final String REFERENCE_SCHEMA = "xar.construction-cash-original-consumers-golden.v2";
    public static final int MAX_BYTES = 160_000;
    private static final String HOST_MODULE = "test_construction_cash_formal_decision_v1.py";
    private static final ObjectMapper JSON = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    public enum Version { LEGACY_V1, REFERENCE_V2 }

    /** Retains validated original JSON, including opaque extensions and exact numeric token kinds. */
    public static final class Capture {
        private final Version version;
        private final ProjectionJson original;
        private Capture(Version version, ProjectionJson original) {
            this.version = version;
            this.original = original;
        }
        public Version version() { return version; }
        public byte[] bytes() { return original.bytes(); }
    }

    private ConstructionCashCaptureContract() { }

    public static Capture decode(byte[] raw) {
        ProjectionJson original = ProjectionJson.object(raw, MAX_BYTES);
        try {
            return new Capture(validate(JSON.readTree(original.bytes())), original);
        } catch (IOException failure) {
            throw new IllegalArgumentException("invalid cash capture JSON", failure);
        }
    }

    public static Capture decodeGzip(InputStream compressed) throws IOException {
        try (GZIPInputStream gzip = new GZIPInputStream(compressed)) {
            return decode(gzip.readNBytes(MAX_BYTES + 1));
        }
    }

    public static byte[] encode(Capture capture) { return capture.bytes(); }

    public static Version validate(JsonNode root) {
        object(root, "cash capture");
        String schema = text(root.get("schema"), "schema");
        Version version;
        if (REFERENCE_SCHEMA.equals(schema)) {
            version = Version.REFERENCE_V2;
            equalText(root.get("producer_role"), "REFERENCE_ORACLE", "producer_role");
            equalText(root.get("current_consumer_validation"), "REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE",
                    "current_consumer_validation");
            requirement(root.get("whole_consumer_fixture_output"), true);
            requirement(root.get("missing_post_cash_priority_regression"), false);
            JsonNode oracle = root.get("reference_oracle");
            object(oracle, "reference_oracle");
            equalText(oracle.get("kind"), "fixed-original-python-source-ast/v1", "reference_oracle.kind");
            exactInteger(oracle.get("Java_calls"), 0, "reference_oracle.Java_calls");
            exactInteger(oracle.get("actual_HTTP_calls"), 0, "reference_oracle.actual_HTTP_calls");
            exactBoolean(oracle.get("grants_runtime_qualification"), false, "grants_runtime_qualification");
        } else if (LEGACY_SCHEMA.equals(schema)) {
            version = Version.LEGACY_V1;
            exactBoolean(field(root, "missing_post_cash_priority_regression", "completed"), true,
                    "legacy missing-post-cash completed");
            exactBoolean(field(root, "whole_consumer_fixture_output", "projection_not_original"), true,
                    "legacy projection_not_original");
            if (root.has("producer_role") || root.has("current_consumer_validation")) {
                throw invalid("legacy evidence must retain its historical provenance");
            }
        } else {
            throw invalid("unsupported cash capture schema");
        }
        text(root.get("machine_id"), "machine_id");
        text(root.get("observed_at_utc"), "observed_at_utc");
        JsonNode sources = array(root.get("source_bindings"), 9, "source_bindings");
        Set<String> paths = new HashSet<>();
        for (JsonNode source : sources) {
            object(source, "source binding");
            if (!paths.add(text(source.get("path"), "source.path"))) throw invalid("duplicate source pin");
            if (!text(source.get("sha256"), "source.sha256").matches("[0-9a-f]{64}")) {
                throw invalid("invalid source SHA-256");
            }
        }
        JsonNode cases = array(root.get("cases"), 12, "cases");
        Set<String> names = new HashSet<>();
        int quotes = 0;
        for (JsonNode vector : cases) {
            object(vector, "case");
            if (!names.add(text(vector.get("name"), "case.name"))) throw invalid("duplicate case name");
            switch (text(vector.get("kind"), "case.kind")) {
                case "quote" -> quotes++;
                case "m5" -> { }
                default -> throw invalid("unsupported cash capture case kind");
            }
            object(vector.get("request"), "case.request");
            object(vector.get("expected"), "case.expected");
        }
        if (quotes != 10) throw invalid("cash capture requires ten quote and two M5 cases");
        return version;
    }

    private static void requirement(JsonNode evidence, boolean wholeConsumer) {
        object(evidence, "actual-host requirement");
        Set<String> fields = wholeConsumer ? Set.of("status", "required_actual_host_modules", "declared_routes")
                : Set.of("status", "required_actual_host_modules");
        Set<String> actual = new HashSet<>();
        evidence.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(fields)) throw invalid("reference evidence cannot claim consumer completion");
        equalText(evidence.get("status"), "NOT_EXECUTED_REFERENCE_CAPTURE", "status");
        JsonNode modules = array(evidence.get("required_actual_host_modules"), 1, "required_actual_host_modules");
        equalText(modules.get(0), HOST_MODULE, "required_actual_host_modules[0]");
        if (wholeConsumer) exactInteger(evidence.get("declared_routes"), 4, "declared_routes");
    }

    private static JsonNode field(JsonNode root, String parent, String child) {
        JsonNode value = root.get(parent);
        object(value, parent);
        return value.get(child);
    }
    private static void object(JsonNode value, String field) {
        if (value == null || !value.isObject()) throw invalid(field + " requires an object");
    }
    private static JsonNode array(JsonNode value, int size, String field) {
        if (value == null || !value.isArray() || value.size() != size) throw invalid(field + " has wrong shape");
        return value;
    }
    private static String text(JsonNode value, String field) {
        if (value == null || !value.isTextual() || value.textValue().isBlank()) throw invalid(field + " requires text");
        return value.textValue();
    }
    private static void equalText(JsonNode value, String expected, String field) {
        if (!expected.equals(text(value, field))) throw invalid("unsupported " + field);
    }
    private static void exactInteger(JsonNode value, int expected, String field) {
        if (value == null || !value.isIntegralNumber() || !value.bigIntegerValue().equals(java.math.BigInteger.valueOf(expected))) {
            throw invalid(field + " requires exact integer " + expected);
        }
    }
    private static void exactBoolean(JsonNode value, boolean expected, String field) {
        if (value == null || !value.isBoolean() || value.booleanValue() != expected) throw invalid(field + " requires boolean " + expected);
    }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
