package org.xar.ck3.control.wave2.planning.swaylifecycle;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.core.JsonGenerator;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class SwayLifecycleObservationTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = SwayLifecycleObservationTest.class.getResourceAsStream("/swaylifecycle/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed original producer golden missing; no fallback or skip"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode input(String id) throws IOException {
        for (JsonNode row : golden().get("cases")) {
            if (row.get("id").textValue().equals(id)) { return row.get("input").deepCopy(); }
        }
        throw new IllegalArgumentException("required captured producer case missing: " + id);
    }
    private static byte[] bytes(JsonNode value) {
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (JsonGenerator generator = new ObjectMapper().getFactory().createGenerator(output)) { token(value, generator); }
            return output.toByteArray();
        }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static void token(JsonNode value, JsonGenerator generator) throws IOException {
        if (value.isObject()) {
            generator.writeStartObject();
            for (var field : value.properties()) { generator.writeFieldName(field.getKey()); token(field.getValue(), generator); }
            generator.writeEndObject();
        } else if (value.isArray()) {
            generator.writeStartArray(); for (JsonNode item : value) { token(item, generator); } generator.writeEndArray();
        } else if (value.isFloatingPointNumber()) {
            String raw = value.decimalValue().toString();
            if (!raw.contains(".") && !raw.contains("E") && !raw.contains("e")) { raw += ".0"; }
            generator.writeNumber(raw);
        } else { generator.writeTree(value); }
    }
    private static byte[] preparation(ObjectNode input) {
        ObjectNode projected = StrictJson.object();
        for (String key : List.of("resolved", "before", "permissions", "target_character_id")) { projected.set(key, input.get(key)); }
        return bytes(projected);
    }

    @Test
    void actualOriginalObserverAndRegisteredServiceGoldenMatches() throws IOException {
        JsonNode samples = golden();
        assertEquals("xar.java.sway-lifecycle-producer-golden.v1", samples.get("schema").textValue());
        assertEquals(19, samples.get("cases").size());
        assertEquals(0, samples.get("game_rpc_count").intValue());
        assertEquals(0, samples.get("canonical_ledger_write_count").intValue());
        assertFalse(samples.get("production_cutover").booleanValue());
        for (JsonNode row : samples.get("cases")) {
            assertTrue(row.get("producer_and_registered_service_executed").booleanValue());
            byte[] originalInput = bytes(row.get("input"));
            JsonNode result = StrictJson.parse(SwayLifecycleObservation.evaluate(originalInput));
            assertEquals(row.get("expected"), result, row.get("id").textValue());
            assertArrayEquals(originalInput, bytes(row.get("input")), "pure evaluator must not mutate original fixture");
        }
    }

    @Test
    void fixedReaderOrderUsesPublicRevisionAndIndependentTerminationSequence() throws IOException {
        ObjectNode sample = input("ordinary-registered-service");
        ((ObjectNode) sample.get("permissions")).put("termination", true);
        SwayLifecycleObservation.Plan plan = SwayLifecycleObservation.prepare(preparation(sample)).orElseThrow();
        assertEquals(List.of(SwayLifecycleObservation.Reader.COMPLETION, SwayLifecycleObservation.Reader.OPINION,
                SwayLifecycleObservation.Reader.TERMINATION), plan.commands().stream().map(SwayLifecycleObservation.ReadCommand::reader).toList());
        assertEquals(BigInteger.valueOf(17), plan.commands().getFirst().expectedRevision());
        assertNotEquals(BigInteger.valueOf(7), plan.commands().getFirst().expectedRevision());
        assertTrue(plan.commands().get(1).schemeInstanceId().isEmpty());
        assertEquals(0, plan.commands().getLast().afterSequence().orElseThrow());
        assertThrows(UnsupportedOperationException.class, () -> plan.commands().clear());
    }

    @Test
    void firstFailureIsVisibleAndSubsequentReadersAreNotRequestedOrRetried() throws IOException {
        ObjectNode failed = input("completion-read-fails");
        JsonNode outcome = StrictJson.parse(SwayLifecycleObservation.evaluate(bytes(failed)));
        assertEquals("query_failed", outcome.get("status").textValue());
        assertTrue(outcome.get("reads").get("completion").get("requested").booleanValue());
        assertEquals("query_failed", outcome.get("reads").get("completion").get("status").textValue());
        assertFalse(outcome.get("reads").get("opinion").get("requested").booleanValue());
        assertFalse(outcome.get("reads").get("termination").get("requested").booleanValue());
        assertFalse(outcome.get("request_retried").booleanValue());
        ((ObjectNode) failed.get("after")).put("revision", 18);
        JsonNode crossed = StrictJson.parse(SwayLifecycleObservation.evaluate(bytes(failed)));
        assertEquals("query_failed", crossed.get("status").textValue());
        assertFalse(crossed.get("same_frame").booleanValue());
    }

    @Test
    void commandArgumentsAndSequenceCannotBeReplayedReorderedOrTruncated() throws IOException {
        ObjectNode reordered = input("ordinary-registered-service");
        ArrayNode rows = (ArrayNode) reordered.get("reads");
        JsonNode first = rows.get(0); rows.set(0, rows.get(1)); rows.set(1, first);
        assertThrows(ContractViolationException.class, () -> SwayLifecycleObservation.evaluate(bytes(reordered)));
        ObjectNode truncated = input("ordinary-registered-service");
        ((ArrayNode) truncated.get("reads")).remove(1);
        assertThrows(ContractViolationException.class, () -> SwayLifecycleObservation.evaluate(bytes(truncated)));
        ObjectNode retried = input("completion-read-fails");
        ((ArrayNode) retried.get("reads")).add(retried.get("reads").get(0).deepCopy());
        assertThrows(ContractViolationException.class, () -> SwayLifecycleObservation.evaluate(bytes(retried)));
        ObjectNode drift = input("ordinary-registered-service");
        ((ObjectNode) drift.get("reads").get(0).get("arguments")).put("expected_revision", 7);
        assertThrows(ContractViolationException.class, () -> SwayLifecycleObservation.evaluate(bytes(drift)));
    }

    @Test
    void rawFloatBooleanAndStringTokensCannotAliasNativeIdsOrPublicRevision() throws IOException {
        for (JsonNode bad : List.of(new ObjectMapper().getNodeFactory().numberNode(17.0),
                new ObjectMapper().getNodeFactory().booleanNode(true), new ObjectMapper().getNodeFactory().textNode("17"))) {
            ObjectNode sample = input("ordinary-registered-service");
            ((ObjectNode) sample.get("reads").get(0).get("arguments")).set("expected_revision", bad);
            assertThrows(ContractViolationException.class, () -> SwayLifecycleObservation.evaluate(bytes(sample)));
        }
        ObjectNode before = input("ordinary-registered-service");
        ((ObjectNode) before.get("before")).put("revision", 17.0);
        ((ArrayNode) before.get("reads")).removeAll();
        assertTrue(StrictJson.parse(SwayLifecycleObservation.evaluate(bytes(before))).isNull());
        ObjectNode target = input("ordinary-registered-service");
        target.put("target_character_id", 34333.0);
        assertTrue(SwayLifecycleObservation.prepare(preparation(target)).isEmpty());
    }

    @Test
    void inputEnvelopeAndOriginalSourceRemainStrictWithoutFreezingSdkExtensions() throws IOException {
        ObjectNode sample = input("ordinary-registered-service");
        JsonNode baseline = StrictJson.parse(SwayLifecycleObservation.evaluate(bytes(sample)));
        ((ObjectNode) sample.get("before")).put("unrelated_sdk_extension", true);
        ((ObjectNode) sample.get("resolved")).put("unrelated_original_history", "retained");
        assertEquals(baseline, StrictJson.parse(SwayLifecycleObservation.evaluate(bytes(sample))));
        sample.put("already_qualified", true);
        assertThrows(ContractViolationException.class, () -> SwayLifecycleObservation.evaluate(bytes(sample)));
        for (String invalid : List.of("{\"reads\":[],\"reads\":[]}", "{} {}", "null", "[]")) {
            assertThrows(ContractViolationException.class,
                    () -> SwayLifecycleObservation.evaluate(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> SwayLifecycleObservation.evaluate(new byte[] {(byte) 0xc3, 0x28}));
    }

    @Test
    void fieldPresenceRemainsDistinctAndOnlyExplicitLegacyBindingComparisonMergesGetDefaults() {
        SwayLifecycleObservation.Field<String> missing = new SwayLifecycleObservation.Field<>(SwayLifecycleObservation.Presence.MISSING, null);
        SwayLifecycleObservation.Field<String> nullable = new SwayLifecycleObservation.Field<>(SwayLifecycleObservation.Presence.NULL, null);
        assertNotEquals(missing, nullable);
        assertTrue(missing.sameLegacyGet(nullable));
        assertFalse(missing.sameLegacyGet(new SwayLifecycleObservation.Field<>(SwayLifecycleObservation.Presence.VALUE, "episode")));
        assertThrows(ContractViolationException.class,
                () -> new SwayLifecycleObservation.Field<>(SwayLifecycleObservation.Presence.VALUE, null));
    }

    @Test
    void resultCannotGrantTerminalOrSubmissionAndPublicModelRejectsDuplicateReads() throws IOException {
        ObjectNode sample = input("ordinary-registered-service");
        SwayLifecycleObservation.Plan plan = SwayLifecycleObservation.prepare(preparation(sample)).orElseThrow();
        SwayLifecycleObservation.Failed failure = new SwayLifecycleObservation.Failed(plan.commands().getFirst(),
                SwayLifecycleObservation.FailureKind.BRIDGE_UNAVAILABLE, "read unavailable");
        SwayLifecycleObservation.Result result = SwayLifecycleObservation.complete(plan, List.of(failure), plan.before());
        assertFalse(result.requestRetried()); assertFalse(result.submissionAuthorized()); assertFalse(result.terminalOutcomeGranted());
        assertThrows(ContractViolationException.class, () -> new SwayLifecycleObservation.Result(
                SwayLifecycleObservation.Status.QUERY_FAILED, plan.original(), true, List.of(failure, failure)));
    }
    @Test
    void retainedTerminalSeedUsesOriginalWriterAndActualNativeFrame() throws IOException {
        String id = "original-already-applied-terminal-stays-observable";
        ObjectNode sample = input(id);
        JsonNode seed = null;
        for (JsonNode row : golden().get("cases")) {
            if (row.get("id").textValue().equals(id)) { seed = row.get("fixture_seed"); }
        }
        if (seed == null || !seed.isObject()) { throw new IOException("actual original terminal seed provenance missing"); }
        JsonNode terminal = sample.get("resolved").get("terminal_intervention");
        assertEquals("sway_lifecycle_consumer.record_sway_terminal_observation", seed.get("producer").textValue());
        assertEquals(1, seed.get("query_count").intValue());
        assertEquals(sample.get("before").get("native_revision"), seed.get("frame_native_revision"));
        assertEquals(sample.get("before").get("revision"), seed.get("frame_public_revision"));
        assertEquals(seed.get("completion_snapshot_revision"), terminal.get("source_native_revision"));
        assertEquals(sample.get("before").get("native_revision"), terminal.get("source_native_revision"));
        assertNotEquals(sample.get("before").get("revision"), terminal.get("source_native_revision"));
        assertEquals(sample.get("before").get("date_raw"), terminal.get("source_date_raw"));
        assertTrue(terminal.get("instance_terminal_outcome_observed").booleanValue());
        assertEquals("terminated_unattributed", terminal.get("native_status_key").textValue());
        assertFalse(terminal.get("terminal_cause_observed").booleanValue());
        assertEquals("unknown", terminal.get("terminal_cause").textValue());
        assertEquals(BigInteger.valueOf(17),
                SwayLifecycleObservation.prepare(preparation(sample)).orElseThrow().commands().getFirst().expectedRevision());
    }

}

