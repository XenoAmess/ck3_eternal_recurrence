package org.xar.ck3.control.wave2.military.armyqueue;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
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
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyId;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyMagic;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Available;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ExplicitNull;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.InitialResolution;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Missing;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Observed;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Unavailable;

final class ArmyDailyQueueInputsTest {
    @TestFactory Stream<DynamicTest> actualProducerAndAllConsumerInputGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.army-daily-queue-golden/v1", golden.get("schema").textValue());
        assertEquals(4, golden.get("original_tests").intValue());
        assertEquals(0, golden.get("original_skipped").intValue());
        assertTrue(golden.get("machine_id").isTextual());
        assertTrue(golden.get("captured_at_utc").isTextual());
        assertTrue(golden.get("source_pins").size() >= 17);
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                // Raw float tokens must reach the strict parser without canonical re-encoding.
                byte[] raw = vector.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                if (!vector.get("accepted").booleanValue()) {
                    assertThrows(IllegalArgumentException.class, () -> ArmyDailyQueueInputsCodec.decode(raw));
                    return;
                }
                ArmyDailyQueueInputs value = ArmyDailyQueueInputsCodec.decode(raw);
                JsonNode encoded = StrictJson.parse(ArmyDailyQueueInputsCodec.encode(value));
                assertEquals(vector.get("normalized"), encoded);
                assertEquals(value, ArmyDailyQueueInputsCodec.decode(ArmyDailyQueueInputsCodec.encode(value)));
                if (vector.has("normalized_strength_family")) {
                    assertEquals(vector.get("normalized_strength_family"), encoded);
                }
                if (value == null) { assertNull(value); return; }
                if (value.initialRows().isPresent()) {
                    JsonNode consistent = vector.get("identity_consistent");
                    for (int index = 0; index < value.initialRows().orElseThrow().size(); index++) {
                        assertEquals(consistent.get(index).booleanValue(),
                                value.initialRows().orElseThrow().get(index).identityPredicateConsistent());
                    }
                }
                if (value.orderedIds().isPresent()) {
                    JsonNode pending = vector.get("append_pending_ids");
                    assertEquals(encoded.get("manager_army_id_list_2a5a8"), pending);
                    assertTrue(vector.get("removal_pending_complete").booleanValue());
                    JsonNode rawPending = vector.get("removal_pending_raw_ids");
                    assertEquals(pending.size(), rawPending.size());
                    for (int index = 0; index < pending.size(); index++) {
                        assertEquals(Integer.toUnsignedLong(value.orderedIds().orElseThrow().get(index).value()),
                                rawPending.get(index).longValue());
                    }
                } else {
                    assertTrue(vector.get("append_pending_ids").isNull());
                    assertFalse(vector.get("removal_pending_complete").booleanValue());
                }
            }));
        }
        return tests.stream();
    }

    @Test void missingNullEmptyAndPartialAreDistinctAndSnapshotsStayExtensible() throws IOException {
        ObjectNode strength = StrictJson.object();
        strength.put("native_extra_field", "allowed");
        assertInstanceOf(Missing.class, ArmyDailyQueueInputsCodec.projectFamily(strength));
        strength.putNull(ArmyDailyQueueInputsCodec.FAMILY_FIELD);
        assertInstanceOf(ExplicitNull.class, ArmyDailyQueueInputsCodec.projectFamily(strength));
        strength.set(ArmyDailyQueueInputsCodec.FAMILY_FIELD, input("empty-observed"));
        ArmyDailyQueueInputs empty = assertInstanceOf(Observed.class,
                ArmyDailyQueueInputsCodec.projectFamily(strength)).value();
        assertTrue(empty.ready());
        assertTrue(empty.orderedIds().orElseThrow().isEmpty());
        ArmyDailyQueueInputs unknown = ArmyDailyQueueInputsCodec.decodeNullable(input("unavailable-queue"));
        assertFalse(unknown.ready());
        assertTrue(unknown.orderedIds().isEmpty());
        ArmyDailyQueueInputs partial = ArmyDailyQueueInputsCodec.decodeNullable(input("ids-without-rows"));
        assertFalse(partial.ready());
        assertEquals(List.of(new ArmyId(7)), partial.orderedIds().orElseThrow());
        assertTrue(partial.initialRows().isEmpty());
        assertNotEquals(empty, unknown);
        assertNotEquals(partial, unknown);
        assertThrows(IllegalArgumentException.class, () -> ArmyDailyQueueInputsCodec.decodeNullable(null));
    }

    @Test void orderedDuplicateOccurrencesAreCopiedAndCannotBeMutated() throws IOException {
        ArmyDailyQueueInputs value = ArmyDailyQueueInputsCodec.decodeNullable(input("ordered-invalid-prefix-duplicates"));
        assertEquals(List.of(new ArmyId(19), new ArmyId(23), new ArmyId(7), new ArmyId(7), new ArmyId(8)),
                value.orderedIds().orElseThrow());
        assertEquals(2, value.initialRows().orElseThrow().get(2).storedIndex());
        assertEquals(3, value.initialRows().orElseThrow().get(3).storedIndex());
        assertThrows(UnsupportedOperationException.class, () -> value.orderedIds().orElseThrow().clear());
        assertThrows(UnsupportedOperationException.class, () -> value.initialRows().orElseThrow().clear());
        List<ArmyId> mutableIds = new ArrayList<>(List.of(new ArmyId(5)));
        ArmyDailyQueueInputs copied = new ArmyDailyQueueInputs(new Unavailable("rows absent"),
                Optional.of(mutableIds), Optional.empty());
        mutableIds.clear();
        assertEquals(List.of(new ArmyId(5)), copied.orderedIds().orElseThrow());
    }

    @Test void statusCompletenessDoesNotGrantIdentityOrRemovalQualification() throws IOException {
        ArmyDailyQueueInputs value = ArmyDailyQueueInputsCodec.decodeNullable(input("schema-accepted-inconsistent-identity"));
        assertTrue(value.ready());
        assertFalse(value.initialRows().orElseThrow().getFirst().identityPredicateConsistent());
        ArmyDailyQueueInputs invalid = ArmyDailyQueueInputsCodec.decodeNullable(input("ordered-invalid-prefix-duplicates"));
        assertTrue(invalid.initialRows().orElseThrow().getFirst().identityPredicateConsistent());
        assertFalse(invalid.initialRows().orElseThrow().getFirst().nativeIdentityValid().orElseThrow());
        assertTrue(invalid.initialRows().orElseThrow().get(2).nativeIdentityValid().orElseThrow());
    }

    @Test void publicConstructorsEnforceCompletenessOrderAndUnsignedWidth() {
        assertThrows(IllegalArgumentException.class, () -> new ArmyMagic(-1));
        assertThrows(IllegalArgumentException.class, () -> new ArmyMagic(0x1_0000_0000L));
        assertThrows(IllegalArgumentException.class, () -> new Unavailable(""));
        assertThrows(IllegalArgumentException.class, () -> new InitialResolution(new Available(), 0, new ArmyId(7),
                Optional.empty(), Optional.of(false), Optional.of(new ArmyMagic(0)), Optional.of(false)));
        assertThrows(IllegalArgumentException.class, () -> new ArmyDailyQueueInputs(new Available(),
                Optional.of(List.of()), Optional.empty()));
        InitialResolution wrongOrder = new InitialResolution(new Unavailable("unknown"), 1, new ArmyId(7),
                Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> new ArmyDailyQueueInputs(new Unavailable("unknown"),
                Optional.of(List.of(new ArmyId(7))), Optional.of(List.of(wrongOrder))));
    }

    @Test void strictBytesRejectDuplicateTrailingMalformedUtf8AndOversize() {
        for (String raw : List.of("{\"status\":1,\"status\":2}", "null null", "", "[]", "true")) {
            assertThrows(IllegalArgumentException.class,
                    () -> ArmyDailyQueueInputsCodec.decode(raw.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(IllegalArgumentException.class, () -> ArmyDailyQueueInputsCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ArmyDailyQueueInputsCodec.decode(new byte[65_537]));
    }

    private static JsonNode input(String name) throws IOException {
        for (JsonNode vector : golden().get("cases")) {
            if (name.equals(vector.get("name").textValue())) {
                return StrictJson.parse(vector.get("input_json").textValue().getBytes(StandardCharsets.UTF_8));
            }
        }
        throw new IOException("required actual producer case missing: " + name);
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = ArmyDailyQueueInputsTest.class.getResourceAsStream("/armyqueue/producer-golden.json")) {
            if (stream == null) { throw new IOException("required committed army queue producer golden missing"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }

    private static JsonNode requiredCompiledConsumerProof() throws IOException {
        try (InputStream raw = ArmyDailyQueueInputsTest.class.getResourceAsStream("/armyqueue/java-consumer-probe.json.gz")) {
            if (raw == null) throw new IOException("required actual compiled Java to original consumer proof missing");
            byte[] packed = raw.readNBytes(24 * 1024 + 1);
            assertTrue(packed.length > 0 && packed.length <= 24 * 1024, "actual consumer proof gzip profile");
            byte[] bytes;
            try (java.util.zip.GZIPInputStream gzip = new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(packed))) {
                bytes = gzip.readNBytes(256 * 1024 + 1);
            }
            assertTrue(bytes.length > 0 && bytes.length <= 256 * 1024, "actual consumer proof raw profile");
            JsonNode proof = org.xar.ck3.control.contracts.StrictJson.parse(bytes, 256 * 1024);
            assertEquals("xar.armyqueue.compiled-java-consumer-probe/v1", proof.path("schema").asText());
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
        assertEquals(4, proof.path("original_tests").intValue()); assertEquals(0, proof.path("original_skipped").intValue());
        java.util.Set<JsonNode> results = new java.util.HashSet<>();
        for (JsonNode invocation : proof.path("consumer_inputs")) {
            byte[] exactTokens = invocation.path("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            if (invocation.path("accepted").booleanValue()) {
                byte[] actual = ArmyDailyQueueInputsCodec.encode(ArmyDailyQueueInputsCodec.decode(exactTokens));
                JsonNode value = org.xar.ck3.control.contracts.StrictJson.parse(actual, 262_144);
                assertEquals(org.xar.ck3.control.contracts.StrictJson.parse(invocation.path("output_json").textValue().getBytes(StandardCharsets.UTF_8), 262_144), value, "actual Java full return transport");
                results.add(value);
            } else {
                assertTrue(invocation.path("output_json").isNull());
                assertThrows(IllegalArgumentException.class, () -> { ArmyDailyQueueInputsCodec.decode(exactTokens); });
            }
        }
        
        assertTrue(proof.path("actual_service_consumers").isArray() && !proof.path("actual_service_consumers").isEmpty());
        boolean completed = false;
        for (JsonNode consumer : proof.path("actual_service_consumers")) {
            int queries = consumer.path("native_query_delta").intValue();
            assertTrue(queries >= 0 && queries <= 1, "unknown/rejected query is never retried");
            if (!"complete".equals(consumer.path("status").asText())) continue;
            completed = true; assertEquals(1, queries);
            assertTrue(consumer.path("declared_consumer_fields_sha256").asText().matches("[0-9a-f]{64}"));
            assertTrue(consumer.path("consumer_field_names").size() >= 3, "loss transfer plus append and removal consumers ran");
            for (JsonNode family : consumer.path("normalized_families")) {
                if (family.path("present").booleanValue()) assertTrue(results.contains(family.get("value")), "actual Java family reached native normalizer and full Service");
            }
        }
        assertTrue(completed);

    }

}
