package org.xar.ck3.control.wave2.development.constructioneconomy;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;

/** Synthetic contract inputs only; these tests do not manufacture original-producer evidence. */
final class ConstructionCashCaptureContractTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test void referenceV2RoundtripRetainsUnexecutedClaimsAndOpaqueJson() throws IOException {
        ObjectNode fixture = reference();
        fixture.putObject("opaque").put("fraction", 1.0).putNull("explicit_null").putArray("empty_rows");
        byte[] raw = bytes(fixture);
        ConstructionCashCaptureContract.Capture parsed = ConstructionCashCaptureContract.decode(raw);
        assertEquals(ConstructionCashCaptureContract.Version.REFERENCE_V2, parsed.version());
        assertArrayEquals(raw, ConstructionCashCaptureContract.encode(parsed));
        JsonNode restored = JSON.readTree(ConstructionCashCaptureContract.encode(parsed));
        assertTrue(restored.path("opaque").path("fraction").isFloatingPointNumber());
        assertTrue(restored.path("opaque").has("explicit_null"));
        assertTrue(restored.path("opaque").path("empty_rows").isArray());
        assertFalse(restored.path("opaque").has("absent"));
        assertEquals("NOT_EXECUTED_REFERENCE_CAPTURE", restored.path("whole_consumer_fixture_output").path("status").textValue());
        assertFalse(restored.path("missing_post_cash_priority_regression").has("completed"));
        assertEquals(parsed.version(), ConstructionCashCaptureContract.decode(ConstructionCashCaptureContract.encode(parsed)).version());
    }

    @Test void legacyV1KeepsHistoricalProvenanceWithoutBecomingV2() throws IOException {
        ObjectNode legacy = reference();
        legacy.put("schema", ConstructionCashCaptureContract.LEGACY_SCHEMA);
        legacy.remove(List.of("producer_role", "current_consumer_validation", "reference_oracle"));
        legacy.putObject("whole_consumer_fixture_output").put("projection_not_original", true);
        legacy.putObject("missing_post_cash_priority_regression").put("completed", true);
        ConstructionCashCaptureContract.Capture parsed = ConstructionCashCaptureContract.decode(bytes(legacy));
        assertEquals(ConstructionCashCaptureContract.Version.LEGACY_V1, parsed.version());
        assertEquals(legacy, JSON.readTree(ConstructionCashCaptureContract.encode(parsed)));
        legacy.put("producer_role", "REFERENCE_ORACLE");
        reject(legacy);
    }

    @Test void referenceEvidenceCannotImportLegacyCompletionOrSuiteCredit() {
        for (String field : List.of("whole_consumer_fixture_output", "missing_post_cash_priority_regression")) {
            for (String credit : List.of("completed", "run", "failures", "errors", "skipped")) {
                ObjectNode fixture = reference();
                ((ObjectNode) fixture.get(field)).putNull(credit);
                reject(fixture);
            }
        }
    }

    @Test void schemaRoleAndValidationRequireExactStringTokens() {
        for (String key : List.of("schema", "producer_role", "current_consumer_validation")) {
            for (JsonNode wrong : List.of(JSON.nullNode(), JSON.getNodeFactory().booleanNode(true),
                    JSON.getNodeFactory().numberNode(2), JSON.getNodeFactory().textNode("unknown"))) {
                ObjectNode fixture = reference(); fixture.set(key, wrong); reject(fixture);
            }
            ObjectNode missing = reference(); missing.remove(key); reject(missing);
        }
        ObjectNode future = reference(); future.put("schema", "xar.construction-cash-original-consumers-golden.v3"); reject(future);
    }

    @Test void hostRequirementsRejectMissingNullWrongModulesAndWrongStatus() {
        for (String field : List.of("whole_consumer_fixture_output", "missing_post_cash_priority_regression")) {
            for (String key : List.of("status", "required_actual_host_modules")) {
                ObjectNode missing = reference(); ((ObjectNode) missing.get(field)).remove(key); reject(missing);
                ObjectNode explicitNull = reference(); ((ObjectNode) explicitNull.get(field)).putNull(key); reject(explicitNull);
            }
            ObjectNode fixture = reference(); ((ObjectNode) fixture.get(field)).put("status", true); reject(fixture);
            fixture = reference(); ((ObjectNode) fixture.get(field)).put("status", "PASS"); reject(fixture);
            fixture = reference(); ((ObjectNode) fixture.get(field)).putArray("required_actual_host_modules").add("other.py"); reject(fixture);
            fixture = reference(); ((ObjectNode) fixture.get(field)).putArray("required_actual_host_modules").add(true); reject(fixture);
            fixture = reference(); ((ObjectNode) fixture.get(field)).putArray("required_actual_host_modules"); reject(fixture);
        }
    }

    @Test void routeCountRejectsEqualBooleanFloatStringAndAbsentTokens() throws IOException {
        for (String token : List.of("true", "4.0", "\"4\"", "null", "3")) {
            ObjectNode fixture = reference();
            ((ObjectNode) fixture.get("whole_consumer_fixture_output")).set("declared_routes", JSON.readTree(token));
            reject(fixture);
        }
        ObjectNode fixture = reference(); ((ObjectNode) fixture.get("whole_consumer_fixture_output")).remove("declared_routes"); reject(fixture);
    }

    @Test void oracleZeroCallsAndRuntimeFlagRejectCoercionAndPositiveClaims() throws IOException {
        for (String key : List.of("Java_calls", "actual_HTTP_calls")) {
            for (String token : List.of("false", "0.0", "\"0\"", "null", "1")) {
                ObjectNode fixture = reference(); ((ObjectNode) fixture.get("reference_oracle")).set(key, JSON.readTree(token)); reject(fixture);
            }
        }
        for (String token : List.of("true", "0", "\"false\"", "null")) {
            ObjectNode fixture = reference();
            ((ObjectNode) fixture.get("reference_oracle")).set("grants_runtime_qualification", JSON.readTree(token)); reject(fixture);
        }
    }

    @Test void allTwelveCasesAndNineSourcePinsStayRequired() {
        ObjectNode fixture = reference(); ((ArrayNode) fixture.get("cases")).remove(11); reject(fixture);
        fixture = reference(); ((ObjectNode) fixture.get("cases").get(0)).put("kind", "unknown"); reject(fixture);
        fixture = reference(); ((ObjectNode) fixture.get("cases").get(0)).put("kind", "m5"); reject(fixture);
        fixture = reference(); ((ObjectNode) fixture.get("cases").get(0)).put("name", "case-1"); reject(fixture);
        fixture = reference(); ((ObjectNode) fixture.get("cases").get(0)).putNull("expected"); reject(fixture);
        fixture = reference(); ((ArrayNode) fixture.get("source_bindings")).remove(8); reject(fixture);
        fixture = reference(); ((ObjectNode) fixture.get("source_bindings").get(0)).put("sha256", true); reject(fixture);
        fixture = reference(); ((ObjectNode) fixture.get("source_bindings").get(0)).put("path", "source-1.py"); reject(fixture);
    }

    @Test void originalBytesAreDefensiveAndMalformedJsonIsRejected() {
        byte[] raw = bytes(reference());
        ConstructionCashCaptureContract.Capture parsed = ConstructionCashCaptureContract.decode(raw);
        byte[] expected = raw.clone(); raw[0] = 0;
        byte[] exposed = parsed.bytes(); exposed[0] = 0;
        assertArrayEquals(expected, parsed.bytes());
        String valid = new String(expected, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ConstructionCashCaptureContract.decode((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionCashCaptureContract.decode(valid.replaceFirst("\\{", "{\"schema\":null,").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionCashCaptureContract.decode(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test void producerGzipBoundaryUsesSameContractAndExpandedBudget() throws IOException {
        byte[] raw = bytes(reference());
        ConstructionCashCaptureContract.Capture parsed = ConstructionCashCaptureContract.decodeGzip(new ByteArrayInputStream(gzip(raw)));
        assertArrayEquals(raw, parsed.bytes());
        assertEquals(ConstructionCashCaptureContract.Version.REFERENCE_V2, parsed.version());
        ObjectNode oversized = reference(); oversized.put("opaque", "x".repeat(ConstructionCashCaptureContract.MAX_BYTES));
        byte[] compressed = gzip(bytes(oversized));
        assertThrows(IllegalArgumentException.class, () -> ConstructionCashCaptureContract.decodeGzip(new ByteArrayInputStream(compressed)));
    }

    private static ObjectNode reference() {
        ObjectNode root = JSON.createObjectNode();
        root.put("schema", ConstructionCashCaptureContract.REFERENCE_SCHEMA);
        root.put("machine_id", "synthetic-contract-test"); root.put("observed_at_utc", "2000-01-01T00:00:00Z");
        root.put("producer_role", "REFERENCE_ORACLE");
        root.put("current_consumer_validation", "REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE");
        ObjectNode whole = requirement(root, "whole_consumer_fixture_output"); whole.put("declared_routes", 4);
        requirement(root, "missing_post_cash_priority_regression");
        ObjectNode oracle = root.putObject("reference_oracle");
        oracle.put("kind", "fixed-original-python-source-ast/v1");
        oracle.put("Java_calls", 0); oracle.put("actual_HTTP_calls", 0); oracle.put("grants_runtime_qualification", false);
        ArrayNode sources = root.putArray("source_bindings");
        for (int i = 0; i < 9; i++) sources.addObject().put("path", "source-" + i + ".py").put("sha256", "a".repeat(64));
        ArrayNode cases = root.putArray("cases");
        for (int i = 0; i < 12; i++) {
            ObjectNode vector = cases.addObject(); vector.put("kind", i < 10 ? "quote" : "m5"); vector.put("name", "case-" + i);
            vector.putObject("request"); vector.putObject("expected");
        }
        return root;
    }
    private static ObjectNode requirement(ObjectNode root, String field) {
        ObjectNode value = root.putObject(field); value.put("status", "NOT_EXECUTED_REFERENCE_CAPTURE");
        value.putArray("required_actual_host_modules").add("test_construction_cash_formal_decision_v1.py"); return value;
    }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); } catch (IOException failure) { throw new IllegalStateException(failure); }
    }
    private static byte[] gzip(byte[] value) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (GZIPOutputStream gzip = new GZIPOutputStream(out)) { gzip.write(value); }
        return out.toByteArray();
    }
    private static void reject(JsonNode value) {
        assertThrows(IllegalArgumentException.class, () -> ConstructionCashCaptureContract.decode(bytes(value)));
    }
}
