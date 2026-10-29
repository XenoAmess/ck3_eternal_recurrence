package org.xar.ck3.control.wave2.military.armyselector;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ArrayList;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class ArmySelectorTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode golden() throws IOException {
        try (InputStream input = ArmySelectorTest.class.getResourceAsStream("/armyselector/original-producer-golden.json.gz")) {
            assertNotNull(input, "original producer golden must be captured by storage owner; missing environment is not a pass");
            byte[] original;
            try (GZIPInputStream gzip = new GZIPInputStream(input)) {
                original = gzip.readNBytes(128 * 1024 + 1);
            }
            assertTrue(original.length > 0 && original.length <= 128 * 1024, "original golden exceeds bounded raw profile");
            JsonNode node = JSON.readTree(original);
            assertEquals("xar.armyselector.original-producer-golden/v1", node.path("schema").asText());
            assertFalse(node.path("machine_id").asText().isBlank()); assertFalse(node.path("observed_at_utc").asText().isBlank());
            assertTrue(node.path("original_normal_plan_test_executed").booleanValue());
            for (JsonNode source : node.path("source_refs")) assertTrue(source.path("sha256").asText().matches("[0-9a-f]{64}"));
            return node;
        }
    }
    private static ObjectNode input(JsonNode golden, JsonNode vector) {
        ObjectNode input = JSON.createObjectNode(); input.put("schema", ArmySelectorCodec.SCHEMA);
        input.set("armies", vector.get("armies").deepCopy()); input.set("active_war_ids", vector.get("active_war_ids").deepCopy());
        ObjectNode snapshot = vector.get("snapshot").deepCopy(); ArrayNode rows = snapshot.putArray("army_strengths");
        for (JsonNode index : vector.get("row_indices")) rows.add(golden.path("rows").get(index.intValue()).deepCopy());
        input.set("snapshot", snapshot); return input;
    }
    private static JsonNode vector(JsonNode golden, String id) {
        for (JsonNode vector : golden.path("cases")) if (id.equals(vector.path("id").asText())) return vector;
        throw new IllegalArgumentException("missing vector " + id);
    }
    @Test void originalProducerToCodecAndAllSelectorBranches() throws IOException {
        JsonNode golden = golden();
        for (JsonNode vector : golden.path("cases")) {
            byte[] bytes = JSON.writeValueAsBytes(input(golden, vector));
            Input typed = ArmySelectorCodec.decode(bytes);
            Selection selected = CurrentReplenishmentSelector.select(typed);
            assertJsonEquals(vector.get("expected"), JSON.readTree(ArmySelectorCodec.encode(selected)), vector.path("id").asText());
            assertJsonEquals(vector.get("expected"), JSON.readTree(ArmySelectorCodec.select(bytes)), "public codec producer " + vector.path("id").asText());
            Selection persisted = ArmySelectorCodec.decodeReceipt(ArmySelectorCodec.encode(selected), typed.armies());
            assertEquals(selected, persisted, "receipt JSON roundtrip " + vector.path("id").asText());
            assertFalse(selected.actualAfter()); assertFalse(selected.fullMonthlyReady());
            assertThrows(UnsupportedOperationException.class, () -> typed.armies().clear());
        }
    }
    @Test void originalOrderedPhysicalLoopAndRefreshSummary() throws IOException {
        JsonNode golden = golden();
        for (JsonNode projection : golden.path("projections")) {
            ObjectNode request = input(golden, vector(golden, "positive-versus-zero"));
            ArrayNode rows = ((ObjectNode) request.get("snapshot")).putArray("army_strengths");
            rows.add(golden.path("rows").get(projection.path("row_index").intValue()));
            StrengthRow row = ArmySelectorCodec.decode(JSON.writeValueAsBytes(request)).snapshot().strengths().value().getFirst();
            Projection actual = OrderedRefill.project(row); JsonNode expected = projection.get("expected");
            assertEquals(expected.path("ordered_core_ready").booleanValue(), actual.orderedCoreReady());
            assertEquals(expected.path("conditional_raised_current_maximum_ready").booleanValue(), actual.currentMaximumReady());
            assertJsonEquals(expected.get("conditional_current_soldiers"), JSON.valueToTree(actual.conditionalCurrent()));
            assertJsonEquals(expected.get("conditional_maximum_soldiers"), JSON.valueToTree(actual.conditionalMaximum()));
            assertJsonEquals(expected.get("missing_inputs"), JSON.valueToTree(actual.missingInputs()));
        }
    }
    @Test void actualNormalStrategyConsumerReceiptsAndQueryRoute() throws IOException {
        JsonNode golden = golden();
        for (JsonNode consumer : golden.path("consumers")) {
            String id = consumer.path("id").asText();
            String caseId = switch (id) {
                case "current-positive-versus-zero" -> "positive-versus-zero";
                case "actual-force-stays-primary" -> "actual-strength-primary";
                case "missing-current-permission-keeps-legacy" -> "missing-permission";
                case "absent-current-query-is-requested-once" -> "query-status-null";
                default -> throw new IllegalArgumentException("unknown original consumer case");
            };
            Input typed = ArmySelectorCodec.decode(JSON.writeValueAsBytes(input(golden, vector(golden, caseId))));
            var pursuit = QuietPursuitConsumer.choose(typed, List.of(), List.of(), List.of(88L, 99L));
            if (consumer.get("receipt").isNull()) assertEquals(SelectionStatus.NOT_APPLICABLE, pursuit.replenishment().status());
            else assertJsonEquals(consumer.get("receipt"), JSON.readTree(ArmySelectorCodec.encode(pursuit.replenishment())));
            var context = new QuietPursuitConsumer.QueryContext(88L, false, true, Slot.nil(), true,
                    List.of(QuietPursuitConsumer.QUERY_STEP), List.of("regular", "regular"));
            boolean query = QuietPursuitConsumer.queryRequired(pursuit, context);
            var queryPlan = QuietPursuitConsumer.queryPlan(pursuit, context, typed.armies(), List.of());
            if (query) {
                assertNotNull(queryPlan);
                ObjectNode scope = JSON.createObjectNode(); scope.set("player_army_ids", JSON.valueToTree(queryPlan.scope().playerArmyIds()));
                scope.set("enemy_army_ids", JSON.valueToTree(queryPlan.scope().enemyArmyIds()));
                assertJsonEquals(consumer.get("army_strength_scope"), scope);
            } else assertNull(queryPlan);
            String step = query ? QuietPursuitConsumer.QUERY_STEP : "move-army-" + pursuit.selected().armyId() + "-to-2640";
            assertEquals(consumer.path("selected_step").asText(), step);
            if (pursuit.replenishment().status() != SelectionStatus.NOT_APPLICABLE) assertEquals(List.of(88L), pursuit.warReceipts().stream().map(QuietPursuitConsumer.WarReceipt::warId).toList());
            assertFalse(QuietPursuitConsumer.queryRequired(pursuit, new QuietPursuitConsumer.QueryContext(88L, false, true,
                    Slot.nil(), true, List.of(QuietPursuitConsumer.QUERY_STEP), List.of("combat"))));
        }
    }
    @Test void sharedRefreshMatchesOriginalWithAliasesOverflowAndUnknowns() throws IOException {
        JsonNode golden = golden();
        for (JsonNode vector : golden.path("refreshes")) {
            ObjectNode request = input(golden, vector(golden, "positive-versus-zero"));
            ObjectNode row = (ObjectNode) request.path("snapshot").path("army_strengths").get(0);
            row.putArray("regiment_replenishment_records_v1").add(vector.get("data"));
            DataSnapshot data = ArmySelectorCodec.decode(JSON.writeValueAsBytes(request)).snapshot().strengths().value().getFirst().data().getFirst();
            List<RaisedRegimentRefresh.PhysicalChunk> physical = null;
            if (!vector.get("physical_chunks_after").isNull()) {
                physical = new ArrayList<>();
                for (JsonNode chunk : vector.get("physical_chunks_after")) physical.add(new RaisedRegimentRefresh.PhysicalChunk(
                        chunk.path("persistent_regiment_id").intValue(), chunk.path("chunk_index").intValue(),
                        chunk.path("current_soldiers").intValue(), chunk.path("maximum_soldiers").intValue()));
            }
            var refreshed = RaisedRegimentRefresh.project(data, physical);
            assertJsonEquals(vector.get("expected"), JSON.readTree(ArmySelectorCodec.encodeRefresh(refreshed)), vector.path("id").asText());
            assertFalse(refreshed.actualRefresh());
        }
    }
    @Test void absentNullEmptyAndSdkExtensionSemantics() throws IOException {
        JsonNode golden = golden();
        ObjectNode missing = input(golden, vector(golden, "query-status-missing"));
        ObjectNode nil = input(golden, vector(golden, "query-status-null"));
        assertEquals(Presence.MISSING, ArmySelectorCodec.decode(JSON.writeValueAsBytes(missing)).snapshot().strengthsStatus().presence());
        assertEquals(Presence.NULL, ArmySelectorCodec.decode(JSON.writeValueAsBytes(nil)).snapshot().strengthsStatus().presence());
        ObjectNode snapshot = (ObjectNode) missing.get("snapshot"); snapshot.remove("army_strengths");
        assertEquals(Presence.MISSING, ArmySelectorCodec.decode(JSON.writeValueAsBytes(missing)).snapshot().strengths().presence());
        snapshot.putNull("army_strengths");
        assertEquals(Presence.NULL, ArmySelectorCodec.decode(JSON.writeValueAsBytes(missing)).snapshot().strengths().presence());
        snapshot.putArray("army_strengths");
        assertEquals(List.of(), ArmySelectorCodec.decode(JSON.writeValueAsBytes(missing)).snapshot().strengths().value());
        ObjectNode extended = input(golden, vector(golden, "positive-versus-zero"));
        ((ObjectNode) extended.get("snapshot")).put("unrelated_sdk_extension", "preserved upstream, deliberately not projected");
        assertJsonEquals(vector(golden, "positive-versus-zero").get("expected"), JSON.readTree(ArmySelectorCodec.select(JSON.writeValueAsBytes(extended))));
    }
    @Test void rawTokenAndSchemaFailuresCannotBecomeReady() throws IOException {
        JsonNode golden = golden(); String valid = JSON.writeValueAsString(input(golden, vector(golden, "positive-versus-zero")));
        for (String token : List.of("true", "11.0", "\"11\"", "2147483648", "-1")) {
            String bad = valid.replaceFirst("\\\"army_id\\\":11", "\"army_id\":" + token);
            assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decode(bad.getBytes(StandardCharsets.UTF_8)), token);
        }
        for (String bad : List.of(valid + " {}", valid.replace("\"schema\":", "\"schema\":\"duplicate\",\"schema\":"),
                valid.replace("\"revision\":42", "\"revision\":42.0"), valid.replace("\"prepared_fraction_raw\":10000", "\"prepared_fraction_raw\":10000.0"),
                valid.replace("\"native_army_in_combat\":false", "\"native_army_in_combat\":0"))) {
            assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decode(bad.getBytes(StandardCharsets.UTF_8)));
        }
        ObjectNode extra = input(golden, vector(golden, "positive-versus-zero")); extra.put("ready", true);
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decode(JSON.writeValueAsBytes(extra)));
        extra.remove("ready"); extra.remove("active_war_ids");
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decode(JSON.writeValueAsBytes(extra)));
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decode(new byte[ArmySelectorCodec.MAX_BYTES + 1]));
    }
    @Test void persistedReceiptRejectsPartialArithmeticAndChangedMeaning() throws IOException {
        JsonNode golden = golden();
        Input typed = ArmySelectorCodec.decode(JSON.writeValueAsBytes(input(golden, vector(golden, "missing-permission"))));
        ObjectNode receipt = (ObjectNode) JSON.readTree(ArmySelectorCodec.encode(CurrentReplenishmentSelector.select(typed)));
        ObjectNode first = (ObjectNode) receipt.path("candidates").get(0);
        first.put("native_signed_current_delta", 1);
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decodeReceipt(JSON.writeValueAsBytes(receipt), typed.armies()));
        first.putNull("native_signed_current_delta"); first.put("positive_refill_opportunity", 1);
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decodeReceipt(JSON.writeValueAsBytes(receipt), typed.armies()));
        first.putNull("positive_refill_opportunity"); receipt.put("actual_after", true);
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decodeReceipt(JSON.writeValueAsBytes(receipt), typed.armies()));
        Input available = ArmySelectorCodec.decode(JSON.writeValueAsBytes(input(golden, vector(golden, "positive-versus-zero"))));
        ObjectNode changed = (ObjectNode) JSON.readTree(ArmySelectorCodec.encode(CurrentReplenishmentSelector.select(available)));
        changed.put("selected_army_id", 11);
        assertThrows(IllegalArgumentException.class, () -> ArmySelectorCodec.decodeReceipt(JSON.writeValueAsBytes(changed), available.armies()));
    }

    private static JsonNode requiredCompiledConsumerProof() throws IOException {
        try (InputStream raw = ArmySelectorTest.class.getResourceAsStream("/armyselector/java-consumer-probe.json.gz")) {
            if (raw == null) throw new IOException("required actual compiled Java to original consumer proof missing");
            byte[] packed = raw.readNBytes(24 * 1024 + 1);
            assertTrue(packed.length > 0 && packed.length <= 24 * 1024, "actual consumer proof gzip profile");
            byte[] bytes;
            try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(packed))) {
                bytes = gzip.readNBytes(256 * 1024 + 1);
            }
            assertTrue(bytes.length > 0 && bytes.length <= 256 * 1024, "actual consumer proof raw profile");
            JsonNode proof = org.xar.ck3.control.contracts.StrictJson.parse(bytes, 256 * 1024);
            assertEquals("xar.armyselector.compiled-java-consumer-probe/v1", proof.path("schema").asText());
            JsonNode binding = proof.path("compiled_java_input");
            for (String field : List.of("qualified_main_jar_sha256", "qualified_test_class_sha256", "original_golden_sha256", "packet_sha256")) {
                assertTrue(binding.path(field).asText().matches("[0-9a-f]{64}"), field);
            }
            assertTrue(binding.path("qualified_main_jar").asText().endsWith(".jar"));
            assertFalse(binding.path("qualified_test_classes").asText().isBlank());
            assertFalse(proof.path("machine_id").asText().isBlank());
            JsonNode contract = proof.path("transport_contract");
            assertEquals(1, contract.path("native_query_limit_per_service_call").intValue());
            assertEquals(0, contract.path("unknown_result_retries").intValue());
            assertFalse(contract.path("python_fallback_after_java_failure").booleanValue());
            assertTrue(contract.path("all_original_tests_passed").booleanValue());
            assertTrue(proof.path("consumer_inputs").isArray() && !proof.path("consumer_inputs").isEmpty());
            assertEquals(proof.path("consumer_inputs").size(), contract.path("compiled_calls").intValue(), "every compiled result consumed once");
            return proof;
        }
    }

    @Test void actualCompiledReturnBytesReachOriginalCompleteConsumers() throws IOException {
        JsonNode proof = requiredCompiledConsumerProof();
        assertTrue(proof.path("original_normal_plan_test_executed").booleanValue()); assertEquals(4, proof.path("consumer_inputs").size());
        java.util.Set<JsonNode> results = new java.util.HashSet<>();
        for (JsonNode invocation : proof.path("consumer_inputs")) {
            byte[] exactTokens = invocation.path("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            if (invocation.path("accepted").booleanValue()) {
                byte[] actual = ArmySelectorCodec.select(exactTokens);
                JsonNode value = org.xar.ck3.control.contracts.StrictJson.parse(actual, 262_144);
                assertJsonEquals(org.xar.ck3.control.contracts.StrictJson.parse(invocation.path("output_json").textValue().getBytes(StandardCharsets.UTF_8), 262_144), value, "actual Java full return transport");
                results.add(value);
            } else {
                assertTrue(invocation.path("output_json").isNull());
                assertThrows(IllegalArgumentException.class, () -> { ArmySelectorCodec.decode(exactTokens); });
            }
        }
        
        JsonNode baseline = golden();
        JsonNode actualPlans = proof.path("actual_normal_plan_consumers");
        assertTrue(actualPlans.isArray()); assertEquals(4, actualPlans.size());
        assertEquals(baseline.path("consumers").size(), actualPlans.size());
        for (int index = 0; index < actualPlans.size(); index++) {
            JsonNode actual = actualPlans.get(index), expected = baseline.path("consumers").get(index);
            for (String field : List.of("id", "selected_step", "receipt", "army_strength_scope")) {
                assertArrayEquals(org.xar.ck3.control.contracts.StrictJson.canonical(expected.get(field), 262_144),
                        org.xar.ck3.control.contracts.StrictJson.canonical(actual.get(field), 262_144),
                        "actual CallbackGameplayDriver -> Service -> strategy consumed Java return: " + field);
            }
            assertEquals(1, actual.path("java_provider_calls").intValue());
            assertEquals(0, actual.path("native_actions_submitted").intValue());
            assertTrue(actual.path("query_selection_only").booleanValue());
            if (!actual.path("receipt").isNull()) {
                assertTrue(results.contains(actual.get("receipt")), "published original war summary is the complete actual Java receipt");
                assertFalse(actual.path("receipt").path("actual_after").booleanValue());
                assertFalse(actual.path("receipt").path("full_monthly_ready").booleanValue());
            }
        }

    }


    private static void assertJsonEquals(JsonNode expected, JsonNode actual) {
        assertJsonEquals(expected, actual, "same JSON value domain");
    }

    private static void assertJsonEquals(JsonNode expected, JsonNode actual, String message) {
        assertTrue(expected.equals((left, right) -> {
            if (left.isIntegralNumber() && right.isIntegralNumber()) {
                return left.bigIntegerValue().compareTo(right.bigIntegerValue());
            }
            return left.equals(right) ? 0 : 1;
        }, actual), message);
    }
}
