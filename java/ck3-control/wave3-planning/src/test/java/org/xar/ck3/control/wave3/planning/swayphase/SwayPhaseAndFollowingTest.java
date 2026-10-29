package org.xar.ck3.control.wave3.planning.swayphase;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
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

final class SwayPhaseAndFollowingTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = SwayPhaseAndFollowingTest.class.getResourceAsStream("/swayphase/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed actual phase/following/pending software producer golden required; no oracle or skip"); }
            byte[] raw = stream.readAllBytes(); if (raw.length == 0 || raw.length > 98_304) { throw new IOException("bounded 96 KiB golden required"); }
            return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                    .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
                    .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).readTree(raw);
        }
    }
    private static byte[] bytes(JsonNode node) {
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (JsonGenerator writer = new ObjectMapper().getFactory().createGenerator(output)) { token(node, writer); }
            return output.toByteArray();
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private static void token(JsonNode node, JsonGenerator writer) throws IOException {
        if (node.isObject()) { writer.writeStartObject(); for (var field : node.properties()) { writer.writeFieldName(field.getKey()); token(field.getValue(), writer); } writer.writeEndObject(); }
        else if (node.isArray()) { writer.writeStartArray(); for (JsonNode item : node) { token(item, writer); } writer.writeEndArray(); }
        else if (node.isFloatingPointNumber()) {
            String raw = node.decimalValue().toString(); if (!raw.contains(".") && !raw.contains("E") && !raw.contains("e")) { raw += ".0"; } writer.writeNumber(raw);
        } else { writer.writeTree(node); }
    }
    private static ObjectNode stageInput() throws IOException { return golden().get("stage_cases").get(0).get("input").deepCopy(); }

    @Test
    void actualOriginalProtocolWriterFollowingAndPhaseVectorsMatchWithoutCurrentNativeCredit() throws IOException {
        JsonNode fixture = golden();
        assertEquals("xar.java.sway-phase-producer-golden.v1", fixture.get("schema").textValue());
        assertEquals(10, fixture.get("stage_cases").size()); assertEquals(1, fixture.get("actual_original_protocol_query_count").intValue());
        assertTrue(fixture.get("actual_original_following_consumer_executed").booleanValue());
        assertEquals("unknown", fixture.get("compatibility_fixture").get("native_origin_machine_id").textValue());
        assertFalse(fixture.get("current_actual4_first_packet_compound_executed").booleanValue());
        assertEquals(0, fixture.get("game_rpc_count").intValue()); assertEquals(0, fixture.get("canonical_ledger_write_count").intValue());
        assertFalse(fixture.get("production_cutover").booleanValue());
        for (JsonNode row : fixture.get("stage_cases")) {
            byte[] source = bytes(row.get("input"));
            if (row.path("java_rejects_malformed_contract").asBoolean(false)) {
                assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(source), row.get("id").textValue());
                if (row.get("id").textValue().equals("float-source-sequence")) {
                    assertTrue(new String(source, StandardCharsets.UTF_8).contains("\"sequence\":1.0"));
                }
                continue;
            }
            var result = SwayPhaseAndFollowing.stage(source);
            assertEquals(row.get("expected").isNull(), result.isEmpty(), row.get("id").textValue());
            if (result.isPresent()) {
                var stage = result.orElseThrow();
                assertEquals(row.get("expected"), StrictJson.parse(stage.phase().toJson()), row.get("id").textValue());
                assertEquals(row.get("expected_write").booleanValue(), stage.updatedResolved().isPresent());
                assertFalse(stage.writerCommitted()); assertFalse(stage.materialEffectGranted()); assertFalse(stage.terminalOutcomeGranted());
                if (stage.updatedResolved().isPresent()) {
                    ObjectNode expected = row.get("input").get("resolved").deepCopy(); expected.set("phase_intervention", row.get("expected"));
                    assertEquals(expected, StrictJson.parse(stage.updatedResolved().orElseThrow().toJson()));
                }
            }
            assertArrayEquals(source, bytes(row.get("input")));
        }
    }

    @Test
    void actualOriginalPendingGateMatchesCurrentHistoryFirstGainAndUnknownStop() throws IOException {
        JsonNode fixture = golden(); assertEquals(13, fixture.get("pending_cases").size());
        for (JsonNode row : fixture.get("pending_cases")) {
            if (row.path("java_rejects_malformed_contract").asBoolean(false)) {
                assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.pending(bytes(row.get("input"))));
                continue;
            }
            var result = SwayPhaseAndFollowing.pending(bytes(row.get("input")));
            assertEquals(row.get("expected").booleanValue(), result.pending(), row.get("id").textValue());
            assertFalse(result.snapshotTaken()); assertFalse(result.submissionAuthorized());
            assertThrows(UnsupportedOperationException.class, () -> result.work().clear());
        }
    }

    @Test
    void sameSequenceDateAndBranchRetainEntireConsumedHistoryEvenWithNewOuterFrame() throws IOException {
        for (JsonNode row : golden().get("stage_cases")) {
            if (row.get("id").textValue().equals("same-source-after-cold-consumption")) {
                var result = SwayPhaseAndFollowing.stage(bytes(row.get("input"))).orElseThrow();
                assertEquals(SwayPhaseAndFollowing.StageTransition.RETAINED_SAME_SOURCE, result.transition());
                assertTrue(result.updatedResolved().isEmpty());
                JsonNode phase = StrictJson.parse(result.phase().toJson());
                assertTrue(phase.get("next_turn_consumed").booleanValue());
                assertEquals(row.get("input").get("resolved").get("phase_intervention"), phase);
                assertFalse(phase.get("source_native_revision").equals(row.get("input").get("execution_read").get("snapshot_revision")));
                return;
            }
        }
        throw new IllegalStateException("actual cold same-source replay case required");
    }

    @Test
    void phaseCannotInventNamedMaterialTerminalOrAQualifiedSourceFromWrongFlags() throws IOException {
        ObjectNode input = stageInput(); ObjectNode record = (ObjectNode) input.get("execution_read").get("records").get(0);
        record.put("native_terminal_state_observed", true);
        assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(bytes(input)));
        record.put("native_terminal_state_observed", false); record.put("executing_input_observed", false);
        assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(bytes(input)));
        record.put("executing_input_observed", true); record.put("source_branch", "authored_sway_complete_100_source");
        assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(bytes(input)));
    }

    @Test
    void uint64SequenceAndSignedDatesAreExactAndOverflowOrBoolIsRejected() throws IOException {
        ObjectNode input = stageInput(); ObjectNode read = (ObjectNode) input.get("execution_read");
        ObjectNode record = (ObjectNode) read.get("records").get(0);
        record.put("sequence", StrictJson.UINT64_MAX); record.put("date_raw", Integer.MIN_VALUE);
        read.put("snapshot_revision", StrictJson.UINT64_MAX); read.put("date_raw", Integer.MIN_VALUE);
        JsonNode staged = StrictJson.parse(SwayPhaseAndFollowing.stage(bytes(input)).orElseThrow().phase().toJson());
        assertEquals(StrictJson.UINT64_MAX, staged.get("source_sequence").bigIntegerValue());
        assertEquals(BigInteger.valueOf(Integer.MIN_VALUE), staged.get("execution_date_raw").bigIntegerValue());
        record.put("sequence", StrictJson.UINT64_MAX.add(BigInteger.ONE));
        assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(bytes(input)));
        record.put("sequence", true);
        assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(bytes(input)));
    }

    @Test
    void missingAndNullConsumptionStayDistinctWhileBothRequestOnlyFollowingAssessment() throws IOException {
        boolean missing = false, nullable = false;
        for (JsonNode row : golden().get("pending_cases")) {
            if (row.get("id").textValue().equals("start-missing")) {
                missing = true; assertTrue(SwayPhaseAndFollowing.pending(bytes(row.get("input"))).work().stream()
                        .anyMatch(work -> work.kind() == SwayPhaseAndFollowing.PendingKind.ORIGINAL_START && work.consumption() == SwayPhaseAndFollowing.Consumption.MISSING));
            }
            if (row.get("id").textValue().equals("start-null")) {
                nullable = true; assertTrue(SwayPhaseAndFollowing.pending(bytes(row.get("input"))).work().stream()
                        .anyMatch(work -> work.kind() == SwayPhaseAndFollowing.PendingKind.ORIGINAL_START && work.consumption() == SwayPhaseAndFollowing.Consumption.NULL));
            }
        }
        assertTrue(missing && nullable);
    }

    @Test
    void exactByteEnvelopeAndImmutableSnapshotsRejectMalformedOrUnknownContract() throws IOException {
        ObjectNode input = stageInput(); var result = SwayPhaseAndFollowing.stage(bytes(input)).orElseThrow();
        byte[] original = result.phase().toJson(), exposed = result.phase().toJson(); exposed[0] = 0;
        assertArrayEquals(original, result.phase().toJson()); input.put("already_qualified", true);
        assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(bytes(input)));
        for (String bad : List.of("{\"resolved\":{},\"resolved\":{}}", "{} {}", "[]", "null")) {
            assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(bad.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> SwayPhaseAndFollowing.stage(new byte[] {(byte) 0xc3, 0x28}));
    }
}
