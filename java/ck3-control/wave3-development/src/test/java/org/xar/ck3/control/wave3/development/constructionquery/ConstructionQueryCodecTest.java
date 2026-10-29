package org.xar.ck3.control.wave3.development.constructionquery;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryModel.*;

final class ConstructionQueryCodecTest {
    @TestFactory
    Stream<DynamicTest> comparesEveryFullOriginalQueryOutputAndPreDispatchFailure() throws IOException {
        JsonNode root = golden(); assertEquals(38, root.get("cases").size());
        return StreamSupport.stream(root.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            byte[] raw = utf8(row.get("input_json").textValue());
            if (row.get("java_strict_reject").booleanValue()) { assertThrows(IllegalArgumentException.class, () -> ConstructionQueryCodec.finalizeObservation(raw)); return; }
            assertEquals(row.get("expected"), StrictJson.parse(ConstructionQueryCodec.finalizeObservation(raw), ConstructionQueryCodec.MAX_BYTES));
            assertTrue(row.get("actual_native_request_count").intValue() <= 1);
            for (JsonNode step : row.get("actual_native_steps")) { assertEquals(ConstructionQueryPolicy.QUERY_NATIVE, step.textValue()); }
        }));
    }

    @Test
    void keepsMaterialSourceSeparateFromNewQuoteSelectionAndPostconditions() throws IOException {
        Result material = ConstructionQueryPolicy.finalizeObservation(ConstructionQueryCodec.decode(input("material_no_new_samples")));
        assertEquals(ReadyKind.MATERIAL_SOURCE, assertInstanceOf(Ready.class, material).kind());
        Result ordinary = ConstructionQueryPolicy.finalizeObservation(ConstructionQueryCodec.decode(input("ordinary_cost_not_evaluated")));
        assertInstanceOf(SourceRed.class, ordinary);
        assertEquals("material_source", output("material_no_new_samples").get("status").textValue());
        assertFalse(output("material_no_new_samples").has("candidate"));
        assertFalse(output("material_no_new_samples").has("postcondition_verified"));
        assertFalse(output("material_no_new_samples").has("formal_action_ready"));
    }

    @Test
    void doesNotDowngradeMissingSourceEvidenceToNoLegalBuilding() throws IOException {
        assertEquals("source_red", output("unknown_wallet_source_red").get("status").textValue());
        assertTrue(output("unknown_wallet_source_red").has("native_result"));
        assertEquals("no_legal_budgeted_building", output("covered_no_candidate").get("status").textValue());
        assertEquals("evidence_insufficient", output("incomplete_no_candidate").get("status").textValue());
        assertEquals("positive_income_candidate_coverage_incomplete", output("incomplete_no_candidate").get("reason").textValue());
    }

    @Test
    void preservesIndependentMode3RejectionWithoutChangingOrdinarySelectedCandidate() throws IOException {
        JsonNode clean = output("independent_mode3_available");
        JsonNode bad = output("independent_mode3_bad_claim_keeps_candidate");
        JsonNode numeric = output("independent_mode3_float_keeps_candidate");
        assertEquals("selected", clean.get("status").textValue()); assertEquals(clean.get("candidate"), bad.get("candidate"));
        assertEquals(clean.get("candidate"), numeric.get("candidate"));
        assertEquals("source_red", bad.get("native_mode3_inputs_status").textValue());
        assertEquals("source_red", numeric.get("native_mode3_inputs_status").textValue());
        assertTrue(numeric.get("world").get("native_mode3_inputs").get("holdings").get(0).get("inputs").get("context_factor_raw").isFloatingPointNumber());
    }

    @Test
    void retainsEnvelopeIdentityEndingFrameAndEpisodeGuards() throws IOException {
        for (String name : List.of("envelope_failed", "envelope_wrong_request", "envelope_wrong_type", "unpaused_before_dispatch", "invalid_combined_modes")) {
            assertEquals("read_rejected", output(name).get("status").textValue(), name);
        }
        for (String name : List.of("changed_ending_snapshot", "changed_ending_public_revision", "changed_ending_episode", "wrong_actor_source_red", "stale_world_revision")) {
            assertEquals("source_red", output(name).get("status").textValue(), name);
        }
        JsonNode wartime = output("missing_episode_wartime_observation");
        assertEquals("selected", wartime.get("status").textValue()); assertTrue(wartime.get("source_frame").get("episode_run_id").isNull());
        assertEquals("read_rejected", output("missing_episode_ordinary").get("status").textValue());
    }

    @Test
    void rejectsRawFloatExponentBoolAndStringBeforeAnyRoundTripCanCoerceThem() throws IOException {
        String raw = new String(input("legacy_original_source"), StandardCharsets.UTF_8);
        for (String token : List.of("3.0", "3e0", "true", "\"3\"")) {
            assertThrows(IllegalArgumentException.class, () -> ConstructionQueryCodec.decode(utf8(raw.replace("\"expected_revision\":3", "\"expected_revision\":" + token))), token);
        }
        for (String token : List.of("1.0", "1e0", "true", "\"1\"")) {
            assertThrows(IllegalArgumentException.class, () -> ConstructionQueryCodec.finalizeObservation(utf8(raw.replace("\"protocol_version\":1", "\"protocol_version\":" + token))), token);
        }
        assertThrows(IllegalArgumentException.class, () -> ConstructionQueryCodec.decode(utf8(raw + " {}")));
        assertThrows(IllegalArgumentException.class, () -> ConstructionQueryCodec.decode(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ConstructionQueryCodec.decode(new byte[ConstructionQueryCodec.MAX_BYTES + 1]));
    }

    @Test
    void retainsSdkFractionExtensionAsAFloatWhileNativeFieldsStayIntegerOnly() throws IOException {
        JsonNode result = output("sdk_fraction_extension");
        assertTrue(result.get("world").get("unconsumed").get("fraction").isFloatingPointNumber());
        assertEquals(row("sdk_fraction_extension").get("expected"), result);
    }

    @Test
    void bindsActualCaptureAndExplicitConsumerRegressionScope() throws IOException {
        JsonNode root = golden();
        boolean referenceV2 = referenceCaptureV2(root, "xar.construction-query-original-producer-golden");
        assertEquals("xenoamess-full-tower-eb9d2c1186", root.get("machine_id").textValue()); StrictJson.utc(root.get("observed_at_utc").textValue());
        assertEquals("c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e", root.get("source_refs").get(0).get("sha256").textValue());
        if (referenceV2) {
            requiresActualHostModule(root, "consumer_regressions", "test_construction_formal_private_consumer.py");
            assertEquals(8, root.get("consumer_regressions").get("declared_test_names").size());
        } else {
            assertEquals(8, root.get("consumer_regressions").get("run").intValue());
            for (String field : List.of("failures", "errors", "skipped")) { assertEquals(0, root.get("consumer_regressions").get(field).intValue()); }
        }
        assertTrue(root.get("capture_scope").textValue().contains("not complete Python CI"));
    }

    private static JsonNode output(String name) throws IOException { return StrictJson.parse(ConstructionQueryCodec.finalizeObservation(input(name)), ConstructionQueryCodec.MAX_BYTES); }
    private static byte[] input(String name) throws IOException { return utf8(row(name).get("input_json").textValue()); }
    private static JsonNode row(String name) throws IOException {
        for (JsonNode row : golden().get("cases")) { if (row.get("name").textValue().equals(name)) { return row; } }
        throw new IOException("required original query producer case missing: " + name);
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden() throws IOException {
        try (InputStream resource = ConstructionQueryCodecTest.class.getResourceAsStream("/constructionquery/original-producer-golden-v1.json.gz")) {
            if (resource == null) { throw new IOException("required actual query golden missing; no default capture fallback or skip"); }
            try (GZIPInputStream input = new GZIPInputStream(resource)) {
                byte[] raw = input.readNBytes(786_433); if (raw.length > 786_432) { throw new IOException("decompressed query golden cap exceeded"); }
                return StrictJson.parse(raw, 786_432);
            }
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
