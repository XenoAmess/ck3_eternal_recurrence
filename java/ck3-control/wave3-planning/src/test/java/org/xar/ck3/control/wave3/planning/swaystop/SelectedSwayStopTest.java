package org.xar.ck3.control.wave3.planning.swaystop;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class SelectedSwayStopTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = SelectedSwayStopTest.class.getResourceAsStream("/swaystop/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("committed actual original Stop software producer golden required; no skip or oracle fallback"); }
            return StrictJson.parse(stream.readAllBytes());
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
    private static void mutate(ObjectNode root, JsonNode changes) {
        for (JsonNode change : changes) {
            JsonNode path = change.get("path"); ObjectNode parent = root;
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode child = parent.get(path.get(index).textValue());
                if (!(child instanceof ObjectNode object)) { throw new IllegalArgumentException("golden path is not an object"); }
                parent = object;
            }
            parent.set(path.get(path.size() - 1).textValue(), change.get("value"));
        }
    }

    @Test
    void originalEligibilityVectorsPreserveStrategyAndRejectRealNumericAliases() throws IOException {
        JsonNode fixture = golden();
        assertEquals("xar.java.sway-stop-producer-golden.v1", fixture.get("schema").textValue());
        assertEquals(17, fixture.get("eligibility_cases").size());
        assertEquals(0, fixture.get("game_rpc_count").intValue()); assertEquals(0, fixture.get("canonical_ledger_write_count").intValue());
        assertEquals(0, fixture.get("native_stop_calls").intValue());
        assertFalse(fixture.get("full_actual4_packet_compound_executed").booleanValue());
        assertFalse(fixture.get("production_cutover").booleanValue());
        for (JsonNode row : fixture.get("eligibility_cases")) {
            ObjectNode input = fixture.get("base").deepCopy(); mutate(input, row.get("mutations")); byte[] raw = bytes(input);
            if (row.has("expected_error_kind") || row.path("java_rejects_malformed_numeric_contract").asBoolean(false)) {
                assertThrows(ContractViolationException.class, () -> SelectedSwayStop.shouldFinish(raw), row.get("id").textValue());
            } else { assertEquals(row.get("expected").booleanValue(), SelectedSwayStop.shouldFinish(raw), row.get("id").textValue()); }
            if (row.get("id").textValue().equals("float-named-points")) {
                assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"value\":45.0"), "real float token must reach production decoder");
            }
        }
    }

    @Test
    void actualOriginalConsumerRoutesRetainPendingAndNeverGenerateOrSubmitAnAction() throws IOException {
        JsonNode fixture = golden(); assertEquals(4, fixture.get("route_cases").size());
        for (JsonNode row : fixture.get("route_cases")) {
            SelectedSwayStop.Plan plan = SelectedSwayStop.plan(bytes(row.get("input")));
            SelectedSwayStop.Operation expected = switch (row.get("original_status").textValue()) {
                case "native_stop_entry_required" -> SelectedSwayStop.Operation.REQUIRE_NATIVE_STOP_ENTRY;
                case "start_pending_recovery" -> SelectedSwayStop.Operation.START_PENDING_RECOVERY;
                case "stop_postcondition_pending" -> SelectedSwayStop.Operation.OBSERVE_ORIGINAL_STOP;
                case "already_terminal_observed" -> SelectedSwayStop.Operation.ALREADY_TERMINAL_OBSERVED;
                default -> throw new IllegalArgumentException("unrecorded original consumer status");
            };
            assertEquals(expected, plan.operation(), row.get("id").textValue());
            assertFalse(plan.submissionAuthorized()); assertFalse(plan.requestRetried()); assertFalse(plan.newActionIdGenerated());
            assertEquals(0, row.get("native_stop_calls").intValue());
            if (plan.retainedStop().isPresent()) {
                assertEquals(row.get("input").get("ledger").get("resolved").get("stop_intervention"), StrictJson.parse(plan.retainedStop().orElseThrow().toJson()));
            }
        }
    }

    @Test
    void actualIndependentReadProjectionMatchesOriginalCurrentTerminalPurgedAndReusedCases() throws IOException {
        JsonNode fixture = golden(); assertEquals(4, fixture.get("postcondition_cases").size());
        for (JsonNode row : fixture.get("postcondition_cases")) {
            byte[] source = bytes(row.get("input")); SelectedSwayStop.PostconditionProjection result = SelectedSwayStop.reconcile(source);
            assertEquals(row.get("expected"), StrictJson.parse(result.stop().toJson()), row.get("id").textValue());
            assertEquals(row.get("expected").get("postcondition_verified").booleanValue(), result.originalInstanceTerminalObserved());
            assertFalse(result.nativeQualificationGranted()); assertFalse(result.writerCommitted()); assertFalse(result.submissionAuthorized());
            assertArrayEquals(source, bytes(row.get("input")));
        }
    }

    @Test
    void ackDoesNotConfirmTerminalAndExistingUnknownStopOnlyObserves() throws IOException {
        for (JsonNode row : golden().get("postcondition_cases")) {
            if (row.get("id").textValue().equals("current")) {
                ObjectNode input = row.get("input").deepCopy(); ObjectNode ack = StrictJson.object();
                ack.put("terminal_observed", true); ack.put("postcondition_verified", true);
                ((ObjectNode) input.get("stop")).set("ack", ack);
                SelectedSwayStop.PostconditionProjection result = SelectedSwayStop.reconcile(bytes(input));
                assertFalse(result.originalInstanceTerminalObserved());
                assertFalse(StrictJson.parse(result.stop().toJson()).get("postcondition_verified").booleanValue());
            }
        }
        for (JsonNode row : golden().get("route_cases")) {
            if (row.get("id").textValue().equals("existing-stop-pending")) {
                ObjectNode input = row.get("input").deepCopy(); input.put("native_stop_entry", "present_requires_original_qualification");
                assertEquals(SelectedSwayStop.Operation.OBSERVE_ORIGINAL_STOP, SelectedSwayStop.plan(bytes(input)).operation());
            }
        }
    }

    @Test
    void aSelectedCandidateStillRequiresOriginalAuthorityAndKeepsOpinionBoundary() throws IOException {
        JsonNode route = golden().get("route_cases").get(0); ObjectNode input = route.get("input").deepCopy();
        input.put("native_stop_entry", "present_requires_original_qualification");
        SelectedSwayStop.Plan candidate = SelectedSwayStop.plan(bytes(input));
        assertEquals(SelectedSwayStop.Operation.PROPOSE_SELECTED_STOP, candidate.operation());
        assertFalse(candidate.submissionAuthorized()); assertFalse(candidate.newActionIdGenerated());
        ((ObjectNode) input.get("readback")).put("target_opinion_of_actor", 50);
        ((ObjectNode) input.get("opinion_read")).put("target_opinion_of_actor", 50);
        assertEquals(SelectedSwayStop.Operation.RETAIN_EXISTING_SWAY, SelectedSwayStop.plan(bytes(input)).operation());
    }

    @Test
    void independentReadCannotSettleAnotherIntentFrameInstanceOrAckOnlyFlag() throws IOException {
        ObjectNode foreign = golden().get("postcondition_cases").get(1).get("input").deepCopy();
        ((ObjectNode) foreign.get("stop")).put("original_action_id", "another-original-action");
        assertThrows(ContractViolationException.class, () -> SelectedSwayStop.reconcile(bytes(foreign)));
        ObjectNode reused = golden().get("postcondition_cases").get(1).get("input").deepCopy();
        ((ObjectNode) reused.get("completion_read")).put("storage_slot_reused", true);
        assertThrows(ContractViolationException.class, () -> SelectedSwayStop.reconcile(bytes(reused)));
        ObjectNode stale = golden().get("postcondition_cases").get(1).get("input").deepCopy();
        ((ObjectNode) stale.get("completion_read")).put("snapshot_revision", 18);
        assertThrows(ContractViolationException.class, () -> SelectedSwayStop.reconcile(bytes(stale)));
    }

    @Test
    void strictJsonBoundaryRejectsMissingUnknownDuplicateUtf8AndSelectedRevisionDrift() throws IOException {
        ObjectNode input = golden().get("base").deepCopy(); input.put("admitted", true);
        assertThrows(ContractViolationException.class, () -> SelectedSwayStop.shouldFinish(bytes(input)));
        for (String invalid : List.of("{\"resolved\":{},\"resolved\":{}}", "{} {}", "[]", "null")) {
            assertThrows(ContractViolationException.class, () -> SelectedSwayStop.shouldFinish(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> SelectedSwayStop.shouldFinish(new byte[] {(byte) 0xc3, 0x28}));
        ObjectNode stale = golden().get("route_cases").get(0).get("input").deepCopy();
        ((ObjectNode) stale.get("selected_request")).put("expected_revision", 18);
        assertThrows(ContractViolationException.class, () -> SelectedSwayStop.plan(bytes(stale)));
    }
}
