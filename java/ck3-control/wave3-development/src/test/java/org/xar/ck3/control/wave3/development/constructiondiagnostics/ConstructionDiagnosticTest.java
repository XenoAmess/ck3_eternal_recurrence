package org.xar.ck3.control.wave3.development.constructiondiagnostics;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.zip.GZIPInputStream;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.development.constructiondiagnostics.ConstructionDiagnosticModel.*;

final class ConstructionDiagnosticTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void originalProducerScalarAttachmentAndRegisteredConsumerEvidenceMatch() throws IOException {
        JsonNode golden = golden();
        boolean referenceV2 = referenceCaptureV2(golden, "xar.construction-diagnostic-original-producer-golden");
        assertFalse(golden.path("machine_id").asText().isBlank()); assertFalse(golden.path("observed_at_utc").asText().isBlank());
        assertEquals(6, golden.path("source_bindings").size());
        if (referenceV2) {
            requiresActualHostModule(golden, "registered_consumer_regression", "test_construction_failure_diagnostic_registered_consumer.py");
            assertEquals(3, golden.path("registered_consumer_regression").path("declared_failure_modes").intValue());
        } else { assertEquals("executed_complete_existing_fixture", golden.path("registered_consumer_regression").asText()); }
        assertEquals(40, golden.path("cases").size());
        for (JsonNode vector : golden.path("cases")) {
            switch (vector.path("kind").asText()) {
                case "projection" -> {
                    byte[] actual = ConstructionDiagnosticCodec.project(vector.path("request_json").textValue().getBytes(StandardCharsets.UTF_8));
                    assertTrue(actual.length <= LIMIT); JsonNode result = JSON.readTree(actual);
                    if (vector.path("intentional_strict_protocol_change").booleanValue()) {
                        assertTrue(vector.path("expected").path("gate_protocol").booleanValue(), "retain the actual legacy type bug");
                        assertFalse(result.path("gate_protocol").booleanValue()); assertEquals("invalid_envelope", result.path("classification").asText());
                        assertFalse(result.has("native_error")); assertFalse(result.has("definition_identity_stage"));
                    } else assertEquals(vector.get("expected"), result, vector.path("name").asText());
                }
                case "scalar" -> assertEquals(vector.get("expected"), scalarNode(ConstructionDiagnosticProjection.scalar(
                        value(vector.get("value")), vector.path("text_limit").intValue())), vector.path("name").asText());
                case "nonfinite_scalar" -> {
                    double number = switch (vector.path("label").asText()) {
                        case "nan" -> Double.NaN; case "positive_infinity" -> Double.POSITIVE_INFINITY;
                        case "negative_infinity" -> Double.NEGATIVE_INFINITY; default -> throw new IllegalArgumentException("nonfinite label");
                    };
                    assertEquals(new Nil(), ConstructionDiagnosticProjection.scalar(new FloatingValue(number), 128));
                    assertTrue(vector.get("expected").isNull());
                }
                case "attachment" -> {
                    Projection projection = ConstructionDiagnosticCodec.decodeProjection(JSON.writeValueAsBytes(vector.get("value")));
                    var error = new ConstructionDiagnosticAttachments.TransportFailure("offline fixture", projection, null);
                    assertEquals(vector.get("expected"), JSON.readTree(ConstructionDiagnosticCodec.encode(ConstructionDiagnosticAttachments.extract(error).orElseThrow())));
                }
                default -> throw new IllegalArgumentException("unknown diagnostic golden kind");
            }
        }
    }

    @Test void streamedLargeUnknownRowsDoNotEnterProjectionOrExceptionAttachment() throws IOException {
        JsonNode vector = named("large_unknown_world_rows_not_retained"); byte[] raw = vector.path("request_json").asText().getBytes(StandardCharsets.UTF_8);
        assertTrue(raw.length > 600000); Request request = ConstructionDiagnosticCodec.decode(raw);
        assertTrue(request.frame().probeFields().size() <= 17);
        byte[] output = ConstructionDiagnosticCodec.project(raw); assertTrue(output.length <= LIMIT);
        String encoded = new String(output, StandardCharsets.UTF_8);
        assertFalse(encoded.contains("unknown_rows")); assertFalse(encoded.contains("payload"));
        assertFalse(encoded.contains("not diagnostic truth"));
        Projection parsed = ConstructionDiagnosticCodec.decodeProjection(output);
        assertEquals(JSON.readTree(output), JSON.readTree(ConstructionDiagnosticCodec.encode(parsed)));
        assertThrows(UnsupportedOperationException.class, () -> parsed.fields().put(Field.SOURCE, new Text("modified")));
    }

    @Test void actualRequestIdentityIsComparedBeforeDiagnosticTextIsClipped() throws IOException {
        JsonNode vector = named("long_identity_matches_before_output_clipping");
        JsonNode result = JSON.readTree(ConstructionDiagnosticCodec.project(vector.path("request_json").asText().getBytes(StandardCharsets.UTF_8)));
        assertTrue(result.path("gate_request_id").booleanValue());
        assertEquals("matched_native_rejected", result.path("classification").asText());
        assertTrue(result.path("request_id").asText().getBytes(StandardCharsets.UTF_8).length <= 160);
        assertTrue(result.path("step").asText().getBytes(StandardCharsets.UTF_8).length <= 96);
        JsonNode maximum = named("maximum_scalar_text_bounded_mapping_types");
        byte[] bounded = ConstructionDiagnosticCodec.project(maximum.path("request_json").asText().getBytes(StandardCharsets.UTF_8));
        assertTrue(bounded.length <= LIMIT); assertEquals(maximum.get("expected"), JSON.readTree(bounded));
    }

    @Test void strictRequestVersionNumericIdentityAndJsonSyntaxRejectMalformedInputs() throws IOException {
        ObjectNode base = (ObjectNode) JSON.readTree(named("matched_native_rejected").path("request_json").asText());
        for (String token : new String[]{"true", "3.0", "\"3\""}) {
            String raw = JSON.writeValueAsString(base); assertTrue(raw.contains("\"revision\":3"));
            byte[] malformed = raw.replace("\"revision\":3", "\"revision\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decode(malformed));
        }
        ObjectNode extra = base.deepCopy(); extra.put("ready", true);
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decode(JSON.writeValueAsBytes(extra)));
        ObjectNode missing = base.deepCopy(); missing.remove("frame");
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decode(JSON.writeValueAsBytes(missing)));
        ObjectNode version = base.deepCopy(); version.put("schema", "xar.construction-diagnostic-input.v2");
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decode(JSON.writeValueAsBytes(version)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decode("{\"frame\":null,\"frame\":null}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decode("{} {}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decodeProjection(new byte[LIMIT + 1]));
    }

    @Test void unknownExceptionAndCauseDoNotSupplyTransportEvidence() throws IOException {
        Projection projection = ConstructionDiagnosticCodec.decodeProjection(ConstructionDiagnosticCodec.project(
                named("matched_native_rejected").path("request_json").asText().getBytes(StandardCharsets.UTF_8)));
        var transport = new ConstructionDiagnosticAttachments.TransportFailure("fixture", projection, null);
        assertEquals(Optional.of(projection), ConstructionDiagnosticAttachments.extract(transport));
        assertTrue(ConstructionDiagnosticAttachments.extract(new RuntimeException("outer", transport)).isEmpty());
        ObjectNode wrong = JSON.readTree(ConstructionDiagnosticCodec.encode(projection)).deepCopy(); wrong.put("source", "foreign");
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decodeProjection(JSON.writeValueAsBytes(wrong)));
        ObjectNode flag = JSON.readTree(ConstructionDiagnosticCodec.encode(projection)).deepCopy(); flag.put("diagnostic_only", false);
        assertThrows(IllegalArgumentException.class, () -> ConstructionDiagnosticCodec.decodeProjection(JSON.writeValueAsBytes(flag)));
    }

    private static JsonNode scalarNode(Value value) {
        if (value instanceof Nil) return JSON.getNodeFactory().nullNode();
        if (value instanceof Flag flag) return JSON.getNodeFactory().booleanNode(flag.value());
        if (value instanceof IntegerValue integer) return JSON.getNodeFactory().numberNode(integer.value());
        if (value instanceof FloatingValue number) return JSON.getNodeFactory().numberNode(number.value());
        if (value instanceof Text text) return JSON.getNodeFactory().textNode(text.value());
        throw new IllegalArgumentException("not a projected scalar");
    }
    private static Value value(JsonNode node) {
        if (node.isNull()) return new Nil(); if (node.isBoolean()) return new Flag(node.booleanValue());
        if (node.isIntegralNumber()) return new IntegerValue(node.bigIntegerValue()); if (node.isFloatingPointNumber()) return new FloatingValue(node.doubleValue());
        if (node.isTextual()) return new Text(node.textValue()); return new Container(node.isArray() ? PythonType.LIST : PythonType.DICT);
    }
    private static JsonNode named(String name) throws IOException {
        for (JsonNode vector : golden().path("cases")) if (vector.path("name").asText().equals(name)) return vector;
        throw new IllegalArgumentException("missing original vector " + name);
    }
    private static JsonNode golden() throws IOException {
        InputStream resource = ConstructionDiagnosticTest.class.getResourceAsStream("/constructiondiagnostics/original-producer-golden.json.gz");
        assertNotNull(resource, "actual original diagnostic golden is required; no skip");
        try (InputStream input = resource; GZIPInputStream gzip = new GZIPInputStream(input)) {
            byte[] raw = gzip.readNBytes(1572865); assertTrue(raw.length <= 1572864, "bounded diagnostic golden expansion"); return JSON.readTree(raw);
        }
    }
    private static boolean referenceCaptureV2(JsonNode root, String baseSchema) {
        String schema = root.path("schema").asText();
        if ((baseSchema + ".v1").equals(schema)) { return false; }
        assertEquals(baseSchema + ".v2", schema, "unsupported reference capture version");
        assertEquals("REFERENCE_ORACLE", root.path("producer_role").asText());
        assertEquals("REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE", root.path("current_consumer_validation").asText());
        return true;
    }

    private static void requiresActualHostModule(JsonNode root, String field, String module) {
        JsonNode evidence = root.path(field);
        assertTrue(evidence.isObject());
        assertEquals("NOT_EXECUTED_REFERENCE_CAPTURE", evidence.path("status").asText());
        assertEquals(1, evidence.path("required_actual_host_modules").size());
        assertEquals(module, evidence.path("required_actual_host_modules").get(0).asText());
        for (String oldCredit : new String[]{"completed", "run", "failures", "errors", "skipped"}) {
            assertFalse(evidence.has(oldCredit), "reference producer cannot claim a current consumer run");
        }
    }

}
