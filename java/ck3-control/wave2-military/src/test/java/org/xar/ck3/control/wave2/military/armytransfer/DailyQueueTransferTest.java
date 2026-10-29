package org.xar.ck3.control.wave2.military.armytransfer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyId;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Available;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Observed;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Unavailable;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.RemainingBasis;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.Status;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.StrengthAvailability;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection.Transfer;

final class DailyQueueTransferTest {
    @TestFactory Stream<DynamicTest> completeActualProducerToConsumerGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.army-daily-transfer-golden/v1", golden.get("schema").textValue());
        assertEquals(1, golden.get("original_tests").intValue());
        assertEquals(0, golden.get("original_skipped").intValue());
        assertTrue(golden.get("source_pins").size() >= 8);
        assertTrue(golden.get("machine_id").isTextual());
        assertTrue(golden.get("captured_at_utc").isTextual());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                assertTrue(vector.get("projection_not_original").booleanValue());
                assertTrue(vector.get("original_input_sha256").textValue().matches("[0-9a-f]{64}"));
                var result = DailyQueueTransferCodec.project(StrictJson.canonical(vector.get("input")));
                JsonNode output = StrictJson.parse(DailyQueueTransferCodec.encode(result));
                assertEquals(vector.get("output"), output);
                assertFalse(output.get("actual_transfer").booleanValue());
                assertFalse(output.get("actual_removal").booleanValue());
                assertFalse(output.get("full_ordered_removal_requests_ready").booleanValue());
                assertFalse(output.get("full_monthly_lifecycle_ready").booleanValue());
                assertTrue(output.get("actual_source_queue_after").isNull());
                assertTrue(output.get("actual_removal_post_state").isNull());
                assertThrows(UnsupportedOperationException.class, () -> result.invalidPrefix().clear());
                assertThrows(UnsupportedOperationException.class, () -> result.remainingOccurrences().clear());
                assertThrows(UnsupportedOperationException.class, () -> result.missingInputs().clear());
            }));
        }
        return tests.stream();
    }

    @Test void duplicateSuffixNeverReusesInitialResolutionAfterFirstRequest() throws IOException {
        var result = DailyQueueTransferCodec.projectStrength(input("ordered-invalid-prefix-duplicates"));
        assertEquals(Status.PARTIAL, result.status());
        assertTrue(result.selectionReady());
        assertEquals(2, result.firstRemovalRequest().orElseThrow().occurrence().storedIndex());
        assertEquals(2, result.remainingOccurrences().size());
        assertEquals(3, result.remainingOccurrences().getFirst().storedIndex());
        assertEquals(new ArmyId(7), result.remainingOccurrences().getFirst().rawArmyReference());
        assertEquals(RemainingBasis.REQUIRES_POST_REMOVAL_STAGE_FRAMES, result.remainingBasis().orElseThrow());
        assertTrue(result.postRemovalStageRequired());
        var unused = DailyQueueTransferCodec.projectStrength(input("later-row-unavailable-never-used"));
        assertTrue(unused.firstRemovalRequestReady());
        assertTrue(unused.postRemovalStageRequired());
        assertEquals(List.of("post_removal_stage_full_id_slot_and_virtual_effects"), unused.missingInputs());
    }

    @Test void unknownFirstResolutionStopsBeforeLaterKnownValidIdentity() throws IOException {
        var result = DailyQueueTransferCodec.projectStrength(input("unknown-middle"));
        assertTrue(result.conditionalTransferReady());
        assertFalse(result.selectionReady());
        assertFalse(result.firstRemovalRequestReady());
        assertEquals(1, result.invalidPrefix().size());
        assertEquals(1, result.remainingOccurrences().getFirst().storedIndex());
        assertEquals(RemainingBasis.UNKNOWN_INITIAL_RESOLUTION, result.remainingBasis().orElseThrow());
        assertFalse(result.postRemovalStageRequired());
    }

    @Test void observedEmptyQueueAndUnavailableQueueRemainDifferent() {
        var empty = DailyQueueTransferProjection.project(StrengthAvailability.AVAILABLE,
                new Observed(new ArmyDailyQueueInputs(new Available(), Optional.of(List.of()), Optional.of(List.of()))));
        var unknown = DailyQueueTransferProjection.project(StrengthAvailability.AVAILABLE,
                new Observed(new ArmyDailyQueueInputs(new Unavailable("unknown"), Optional.empty(), Optional.empty())));
        assertEquals(Status.AVAILABLE, empty.status());
        assertTrue(empty.conditionalTransferReady());
        assertTrue(empty.selectionReady());
        assertFalse(empty.firstRemovalRequestReady());
        assertEquals(Status.UNAVAILABLE, unknown.status());
        assertFalse(unknown.conditionalTransferReady());
        List<ArmyId> ids = new ArrayList<>(List.of(new ArmyId(7)));
        Transfer transfer = new Transfer(ids); ids.clear();
        assertEquals(List.of(new ArmyId(7)), transfer.sourceIds());
        assertThrows(UnsupportedOperationException.class, () -> transfer.sourceIds().clear());
    }

    @Test void strictFullFamilyRejectsRawNumericCoercionWhileUnusedOperandsAreNotRead() throws IOException {
        String original = new String(StrictJson.canonical(input("single-fallback")), StandardCharsets.UTF_8);
        for (String token : List.of("true", "991.0", "991e0", "\"991\"", "2147483648")) {
            String malformed = original.replace("[991]", "[" + token + "]");
            assertThrows(IllegalArgumentException.class,
                    () -> DailyQueueTransferCodec.project(malformed.getBytes(StandardCharsets.UTF_8)), token);
        }
        ObjectNode unavailable = StrictJson.object();
        unavailable.put("status", "unavailable");
        unavailable.put("monthly_daily_queue_inputs_v1", true);
        assertEquals(Status.UNAVAILABLE, DailyQueueTransferCodec.projectStrength(unavailable).status());
        assertThrows(IllegalArgumentException.class,
                () -> DailyQueueTransferCodec.project("{} {}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> DailyQueueTransferCodec.project(new byte[65_537]));
    }

    private static JsonNode input(String name) throws IOException {
        for (JsonNode vector : golden().get("cases")) {
            if (name.equals(vector.get("name").textValue())) { return vector.get("input"); }
        }
        throw new IOException("required producer case missing: " + name);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = DailyQueueTransferTest.class.getResourceAsStream("/armytransfer/producer-golden.json")) {
            if (stream == null) { throw new IOException("required committed army transfer golden missing"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }

    private static JsonNode requiredCompiledConsumerProof() throws IOException {
        try (InputStream raw = DailyQueueTransferTest.class.getResourceAsStream("/armytransfer/java-consumer-probe.json.gz")) {
            if (raw == null) throw new IOException("required actual compiled Java to original consumer proof missing");
            byte[] packed = raw.readNBytes(24 * 1024 + 1);
            assertTrue(packed.length > 0 && packed.length <= 24 * 1024, "actual consumer proof gzip profile");
            byte[] bytes;
            try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(packed))) {
                bytes = gzip.readNBytes(256 * 1024 + 1);
            }
            assertTrue(bytes.length > 0 && bytes.length <= 256 * 1024, "actual consumer proof raw profile");
            JsonNode proof = org.xar.ck3.control.contracts.StrictJson.parse(bytes, 256 * 1024);
            assertEquals("xar.armytransfer.compiled-java-consumer-probe/v1", proof.path("schema").asText());
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
        assertEquals(2, proof.path("original_tests").intValue()); assertEquals(0, proof.path("original_skipped").intValue());
        java.util.Set<JsonNode> results = new java.util.HashSet<>();
        for (JsonNode invocation : proof.path("consumer_inputs")) {
            byte[] exactTokens = invocation.path("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            if (invocation.path("accepted").booleanValue()) {
                byte[] actual = DailyQueueTransferCodec.encode(DailyQueueTransferCodec.project(exactTokens));
                JsonNode value = org.xar.ck3.control.contracts.StrictJson.parse(actual, 262_144);
                assertEquals(org.xar.ck3.control.contracts.StrictJson.parse(invocation.path("output_json").textValue().getBytes(StandardCharsets.UTF_8), 262_144), value, "actual Java full return transport");
                results.add(value);
            } else {
                assertTrue(invocation.path("output_json").isNull());
                assertThrows(IllegalArgumentException.class, () -> { DailyQueueTransferCodec.project(exactTokens); });
            }
        }
        
        boolean completed = false, deepCleanup = false, unknownCleanup = false;
        assertTrue(proof.path("actual_service_consumers").isArray() && !proof.path("actual_service_consumers").isEmpty());
        for (JsonNode consumer : proof.path("actual_service_consumers")) {
            int queries = consumer.path("native_query_delta").intValue();
            assertTrue(queries >= 0 && queries <= 1, "unknown/rejected query is never retried");
            if (!"complete".equals(consumer.path("status").asText())) continue;
            completed = true; assertEquals(1, queries);
            assertTrue(consumer.path("declared_consumer_fields_sha256").asText().matches("[0-9a-f]{64}"));
            for (JsonNode actualTransfer : consumer.path("loss_transfer_results")) {
                assertTrue(results.contains(actualTransfer), "actual Java complete transfer reached original loss-allocation consumer");
                assertFalse(actualTransfer.path("actual_transfer").booleanValue());
                assertFalse(actualTransfer.path("actual_removal").booleanValue());
            }
            for (JsonNode cleanup : consumer.path("manager_cleanup_results")) {
                assertFalse(cleanup.path("actual_cleanup").booleanValue());
                assertFalse(cleanup.path("actual_removal").booleanValue());
                assertTrue(cleanup.path("actual_post_state").isNull());
                assertFalse(cleanup.path("full_monthly_lifecycle_ready").booleanValue());
                deepCleanup |= "cleanup".equals(cleanup.path("conditional_cleanup_branch").asText())
                        && cleanup.path("records_b0_removed_count").intValue() == 3;
                unknownCleanup |= !cleanup.path("candidate_selection_ready").booleanValue();
            }
        }
        assertTrue(completed); assertTrue(deepCleanup, "exact first-removal manager membership consumer ran");
        assertTrue(unknownCleanup, "unknown first identity stays unresolved without later retry");

    }

}
