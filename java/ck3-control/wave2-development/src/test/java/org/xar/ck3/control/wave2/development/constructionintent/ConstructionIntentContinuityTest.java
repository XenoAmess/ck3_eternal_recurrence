package org.xar.ck3.control.wave2.development.constructionintent;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

class ConstructionIntentContinuityTest {
    private static final String SOURCE_SHA = "75d926271a46405b68858ea80df641c1eaf4962c4deb863995ae00c05aaf3a02";

    @Test
    void originalProducerGoldenIncludesActualSelectedAndConsumedConsumers() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.constructionintent-golden/v1", golden.path("schema").textValue());
        assertEquals(SOURCE_SHA, golden.path("source_sha256").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", golden.path("machine_id").textValue());
        assertTrue(golden.path("observed_at_utc").isTextual());
        assertEquals(20, golden.path("cases").size());
        for (JsonNode row : golden.path("cases")) {
            byte[] produced = ConstructionIntentJson.project(request(row));
            assertEquals(row.get("expected"), StrictJson.parse(produced), row.path("name").textValue());
            assertArrayEquals(produced, StrictJson.canonical(StrictJson.parse(produced)),
                    "projection survives canonical JSON roundtrip");
        }
    }

    @Test
    void realProducerOutputIsTheSameInputAcceptedByOriginalColdClassifier() throws IOException {
        try (InputStream stream = ConstructionIntentContinuityTest.class.getResourceAsStream(
                "/constructionintent/cold-consumer.json")) {
            assertNotNull(stream, "original consumer capture must be present");
            JsonNode evidence = StrictJson.parse(stream.readAllBytes());
            assertEquals("xar.ck3.constructionintent-original-consumer/v1", evidence.path("schema").textValue());
            JsonNode selected = StrictJson.parse(ConstructionIntentJson.project(request(named("real-N40-P02-AUTO11-selected"))));
            assertEquals(evidence.get("selected_expected"), selected);
            JsonNode observed = evidence.get("consumer_observation");
            assertEquals("construction_cold_readonly_reconciliation_observed", observed.path("category").textValue());
            assertFalse(observed.path("replay_allowed").booleanValue());
            assertFalse(observed.path("business_success_inferred").booleanValue());
            assertFalse(observed.path("construction_completion_verified").booleanValue());
            assertEquals("unknown", evidence.path("fixture_original_machine_id").textValue());
        }
    }

    @Test
    void selectedReceiptServiceHookPreservesRealResultAndPendingIdentity() throws IOException {
        JsonNode row = named("real-N40-P02-AUTO11-selected");
        ObjectNode plan = StrictJson.object();
        plan.set("construction_pending_action", row.get("pending_action"));
        plan.set("selected_step", row.get("selected_step"));
        plan.set("construction_deferred_selected_step", row.get("deferred_selected_step"));
        plan.put("frame_extension", "retained by original owner");
        byte[] original = StrictJson.canonical(row.get("typed_result"));
        var enriched = ConstructionIntentConsumers.selectedReceipt(StrictJson.canonical(plan), original);
        assertArrayEquals(original, enriched.originalUtf8());
        assertEquals(64, enriched.originalSha256().length());
        assertTrue(enriched.projectionNotOriginal());
        JsonNode body = StrictJson.parse(enriched.enrichedUtf8());
        assertEquals(row.get("expected"), body.get("construction_selected_intent"));
        ObjectNode unmodifiedFields = (ObjectNode) body.deepCopy();
        unmodifiedFields.set("construction_selected_intent", row.get("typed_result").get("construction_selected_intent"));
        assertEquals(row.get("typed_result"), unmodifiedFields);
        ConstructionIntentConsumers.requireColdReadbackIntent(StrictJson.canonical(body.get("construction_selected_intent")),
                StrictJson.canonical(row.get("pending_action")), ConstructionIntentContinuity.RECEIPT_STEP);
        ObjectNode invalid = (ObjectNode) body.get("construction_selected_intent").deepCopy();
        invalid.put("selected_query_performed_new_submission", true);
        assertThrows(ContractViolationException.class, () -> ConstructionIntentConsumers.requireColdReadbackIntent(
                StrictJson.canonical(invalid), StrictJson.canonical(row.get("pending_action")),
                ConstructionIntentContinuity.RECEIPT_STEP));
        byte[] copy = enriched.originalUtf8();
        copy[0] = '[';
        assertArrayEquals(original, enriched.originalUtf8(), "original evidence remains immutable");
    }

    @Test
    void allThreeConsumedPlannerHooksKeepTheOriginalSelectedAction() throws IOException {
        JsonNode row = named("real-N40-P02-AUTO11-consumed");
        byte[] plan = utf8("{\"selected_step\":\"life-advance\",\"snapshot_id\":\"native:3\","
                + "\"extension_decimal\":1.25,\"extension_null\":null,\"extension_empty\":[]}");
        var result = ConstructionIntentConsumers.consumedReceipt(plan, StrictJson.canonical(row.get("receipt")));
        JsonNode body = StrictJson.parse(result.enrichedUtf8());
        assertEquals("life-advance", body.path("selected_step").textValue());
        assertEquals("native:3", body.path("snapshot_id").textValue());
        assertEquals(StrictJson.parse(plan).get("extension_decimal"), body.get("extension_decimal"));
        assertTrue(body.get("extension_null").isNull());
        assertTrue(body.get("extension_empty").isArray());
        assertEquals(row.get("receipt"), body.get("construction_receipt_consumed"));
        assertEquals(row.get("expected"), body.get("construction_consumed_intent"));
        assertFalse(body.get("construction_consumed_intent").has("selected_step"));
        assertFalse(body.get("construction_consumed_intent").has("replay_allowed"));
        assertArrayEquals(plan, result.originalUtf8());
    }

    @Test
    void strictBoundaryRejectsOriginalRawFloatBooleanAndStringIntegerTokens() throws IOException {
        String base = new String(request(named("legacy-applied-without-explicit-flags")), StandardCharsets.UTF_8);
        for (String replacement : new String[]{"31254.0", "true", "\"31254\""}) {
            // Pass the original token; no JSON-tree normalization may convert 31254.0 to an integer.
            String invalid = base.replace("\"actor_character_id\":31254", "\"actor_character_id\":" + replacement);
            assertThrows(ProjectionDomainRejection.class,
                    () -> ConstructionIntentJson.project(utf8(invalid)), replacement);
        }
        assertThrows(ContractViolationException.class,
                () -> ConstructionIntentJson.project(utf8(base.replace("\"postcondition_verified\":true",
                        "\"postcondition_verified\":1"))));
        assertThrows(ProjectionDomainRejection.class,
                () -> ConstructionIntentJson.project(utf8(base.replace("\"slot_index\":2", "\"slot_index\":2.0"))));
    }

    @Test
    void strictWrapperAndMalformedInputCannotFallThroughToUnknown() throws IOException {
        String base = new String(request(named("legacy-applied-without-explicit-flags")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> ConstructionIntentJson.project(utf8(base + " {}")));
        assertThrows(ProjectionDomainRejection.class, () -> ConstructionIntentJson.project(utf8(
                base.replaceFirst("\\{", "{\"unexpected\":true,"))));
        assertThrows(ContractViolationException.class, () -> ConstructionIntentJson.project(utf8(
                base.replaceFirst("\\{", "{\"operation\":\"selected\","))));
        ObjectNode missing = (ObjectNode) StrictJson.parse(utf8(base));
        missing.remove("deferred_selected_step");
        assertThrows(ProjectionDomainRejection.class,
                () -> ConstructionIntentJson.project(StrictJson.canonical(missing)));
        ObjectNode malformed = (ObjectNode) StrictJson.parse(utf8(base));
        malformed.put("pending_action", false);
        assertThrows(ContractViolationException.class,
                () -> ConstructionIntentJson.project(StrictJson.canonical(malformed)));
        assertThrows(ContractViolationException.class, () -> ConstructionIntentJson.project(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(ContractViolationException.class,
                () -> ConstructionIntentJson.project(new byte[ConstructionIntentJson.MAX_INPUT_BYTES + 1]));
    }

    @Test
    void missingNullAndEmptyCandidateHaveTheOriginalDistinctMaterialProjection() throws IOException {
        JsonNode empty = StrictJson.parse(ConstructionIntentJson.project(request(named("consumed-empty-candidate-distinct-from-null"))));
        JsonNode absent = StrictJson.parse(ConstructionIntentJson.project(request(named("consumed-null-candidate"))));
        assertTrue(empty.get("observed_material_candidate").isObject());
        assertTrue(empty.get("observed_material_candidate").get("barony_title_id").isNull());
        assertTrue(absent.get("observed_material_candidate").isNull());
        assertTrue(empty.get("requested_construction_verified").isNull());
        ObjectNode request = (ObjectNode) StrictJson.parse(request(named("consumed-null-candidate")));
        ((ObjectNode) request.get("receipt")).remove("candidate");
        assertEquals(absent, StrictJson.parse(ConstructionIntentJson.project(StrictJson.canonical(request))));
    }

    @Test
    void legacyUnboundedExactIntDomainDoesNotRoundAtJavaLongOrJavascriptNumber() throws IOException {
        ObjectNode request = (ObjectNode) StrictJson.parse(request(named("legacy-applied-without-explicit-flags")));
        BigInteger large = new BigInteger("18446744073709551616");
        ((ObjectNode) request.get("pending_action")).put("actor_character_id", large);
        ((ObjectNode) request.get("typed_result")).put("actor_character_id", large);
        JsonNode output = StrictJson.parse(ConstructionIntentJson.project(StrictJson.canonical(request)));
        assertEquals(large, output.path("original_action").path("actor_character_id").bigIntegerValue());
        assertTrue(output.path("actor_identity_matches").booleanValue());
    }

    private static byte[] request(JsonNode row) {
        ObjectNode request = (ObjectNode) row.deepCopy();
        request.remove("name");
        request.remove("expected");
        request.put("schema", ConstructionIntentJson.REQUEST_SCHEMA);
        return StrictJson.canonical(request);
    }

    private static JsonNode named(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (name.equals(row.path("name").textValue())) { return row; }
        }
        throw new IllegalStateException("missing golden case: " + name);
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = ConstructionIntentContinuityTest.class.getResourceAsStream("/constructionintent/golden.json")) {
            assertNotNull(stream, "original-producer capture must be present; missing golden is a failure");
            return StrictJson.parse(stream.readAllBytes());
        }
    }

    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
