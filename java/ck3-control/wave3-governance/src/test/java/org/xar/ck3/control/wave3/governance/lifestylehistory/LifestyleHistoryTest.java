package org.xar.ck3.control.wave3.governance.lifestylehistory;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory.*;

final class LifestyleHistoryTest {
    private static final LifestyleHistoryProjectionPort PORT = new LifestyleHistoryProjectionPort();
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static JsonNode golden() throws IOException {
        try (InputStream input = LifestyleHistoryTest.class.getResourceAsStream("/lifestylehistory/original-producer-golden-v1.json")) {
            assertNotNull(input, "committed actual original producer golden is mandatory; no skipped or dynamic Python tests");
            byte[] raw = input.readAllBytes(); assertTrue(raw.length <= 105000); JsonNode golden = JSON.readTree(raw);
            assertEquals("lifestyle-history-original-producer-golden-v1", golden.path("schema").textValue());
            assertFalse(golden.path("native_business_qualification").booleanValue()); assertEquals(6, golden.path("sources").size());
            assertEquals(3, golden.path("original_methods_executed").intValue()); return golden;
        }
    }
    private static JsonNode sample(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) { if (name.equals(row.path("name").textValue())) { return row; } }
        throw new AssertionError("missing original history sample " + name);
    }
    private static Input decode(JsonNode sample) { return LifestyleHistoryCodec.decode(StrictJson.canonical(sample.get("request"))); }
    private static LifestyleMinPolicy.Request minimum() throws IOException { return LifestyleMinCodec.decode(StrictJson.canonical(golden().get("minimum_request"))); }
    @TestFactory Stream<DynamicTest> actualProducerParityAndExplicitUnsafeAcceptanceCorrections() throws IOException {
        List<DynamicTest> tests = new ArrayList<>(); JsonNode cases = golden().get("cases"); assertTrue(cases.size() >= 23);
        for (JsonNode sample : cases) {
            tests.add(DynamicTest.dynamicTest(sample.path("name").textValue(), () -> {
                Input input = decode(sample); Selection selected = PORT.project(PORT.decode(StrictJson.canonical(sample.get("request"))));
                assertEquals(input, LifestyleHistoryCodec.decode(LifestyleHistoryCodec.encode(input)), "full result JSON bytes round trip");
                assertEquals(input.episodeRunId(), selected.episodeRunId());
                if ("parity".equals(sample.path("mode").textValue())) {
                    JsonNode pending = sample.get("legacy_unresolved");
                    if (pending.isNull()) { assertEquals(Status.CLEAR, selected.status()); assertTrue(selected.pendingActions().isEmpty()); }
                    else {
                        assertEquals(Status.VERIFY_ORIGINAL_RECEIPT, selected.status()); assertEquals(1, selected.pendingActions().size());
                        assertEquals(pending, JSON.readTree(selected.pendingActions().getFirst().originalJson().bytes()));
                    }
                    JsonNode applied = sample.get("legacy_latest_applied");
                    assertEquals(!applied.isNull(), selected.latestApplied().isPresent());
                    if (!applied.isNull()) { assertEquals(applied, LifestyleHistoryCodec.appliedNode(selected.latestApplied().orElseThrow())); }
                } else {
                    assertEquals("intentional_correction", sample.path("mode").textValue());
                    assertNotEquals(Status.CLEAR, selected.status(), "old unsafe acceptance must not settle an UNKNOWN action");
                    assertFalse(selected.pendingActions().isEmpty(), "preserve the original request and source receipt");
                    JsonNode originalIntent = sample.get("request").get("history").get(0).get("result_json");
                    JsonNode original = JSON.readTree(originalIntent.textValue());
                    assertTrue(selected.pendingActions().stream().anyMatch(value -> value.actionRequestId().equals(original.path("action_request_id").textValue())));
                    var decision = LifestyleHistoryConsumer.chooseMinimum(minimum(), selected);
                    assertNull(decision.selectedAction(), "real typed minimum consumer must not issue a second submit");
                    assertTrue(decision.status() == LifestyleMinPolicy.Status.VERIFY_PENDING_RECEIPT || decision.status() == LifestyleMinPolicy.Status.ACTION_STATE_UNKNOWN);
                }
                JsonNode wire = StrictJson.parse(PORT.encode(selected));
                assertFalse(wire.path("replay_authorized").booleanValue()); assertFalse(wire.path("native_business_qualification").booleanValue());
            }));
        }
        return tests.stream();
    }
    @Test void statusOnlyAppliedAndBadMaterialAreRecordedAsOldUnsafeDifferences() throws IOException {
        for (String name : List.of("status_only_applied", "receipt_row_not_ok", "postcondition_not_verified", "perk_not_materially_owned")) {
            JsonNode source = sample(name); assertTrue(source.path("legacy_unresolved").isNull(), "original Python actually cleared this bad input");
            Selection selection = LifestyleHistory.select(decode(source)); assertFalse(selection.pendingActions().isEmpty());
            assertTrue(selection.latestApplied().isEmpty()); assertFalse(selection.unverifiedReceipts().isEmpty());
        }
    }
    @Test void mechanicalOriginalPendingProjectionUsesTheUniqueTypedGuardAndOpaqueBytes() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            Selection selected = LifestyleHistory.select(decode(row));
            JsonNode wire = StrictJson.parse(LifestyleHistoryCodec.encodeSelection(selected));
            JsonNode original = wire.get("original_pending_action_json");
            var pending = LifestyleHistoryConsumer.pendingGuard(selected);
            if (!pending.present()) { assertTrue(original.isNull()); }
            else if (selected.status() == Status.VERIFY_ORIGINAL_RECEIPT) {
                assertArrayEquals(selected.pendingActions().getFirst().originalJson().bytes(), original.textValue().getBytes(StandardCharsets.UTF_8));
            } else {
                assertEquals(pending.value().status().value(), JSON.readTree(original.textValue()).get("status").textValue());
            }
        }
        JsonNode opaque = StrictJson.parse(LifestyleHistoryCodec.evaluate(StrictJson.canonical(sample("opaque_unknown_float_and_null_preserved").get("request"))));
        assertTrue(opaque.get("original_pending_action_json").textValue().contains("1.0"));
        Selection absent = LifestyleHistory.select(new Input(null, List.of()));
        assertEquals("action_state_unknown", JSON.readTree(StrictJson.parse(LifestyleHistoryCodec.encodeSelection(absent)).get("original_pending_action_json").textValue()).get("status").textValue());
    }
    @Test void publicAndNativeRevisionStampsAreNotMixed() throws IOException {
        Selection pending = LifestyleHistory.select(decode(sample("public_ahead_of_native_pending")));
        ReceiptData original = pending.pendingActions().getFirst();
        assertTrue(original.prePublicRevision().compareTo(original.sourceNativeRevision()) > 0);
        Selection applied = LifestyleHistory.select(decode(sample("public_ahead_of_native_material_applied")));
        assertEquals(Status.CLEAR, applied.status()); assertTrue(applied.latestApplied().isPresent());
        Selection sameFrame = LifestyleHistory.select(decode(sample("same_native_frame_is_not_independent")));
        assertFalse(sameFrame.pendingActions().isEmpty()); assertTrue(sameFrame.latestApplied().isEmpty());
    }
    @Test void sourceDriftKeepsBothReceiptsAndTwoActionsDoNotShadowUnknown() throws IOException {
        for (String name : List.of("two_unresolved_actions_are_conflict", "same_request_source_binding_drift_is_conflict")) {
            Selection selected = LifestyleHistory.select(decode(sample(name))); assertEquals(Status.CONFLICT, selected.status());
            assertTrue(selected.pendingActions().size() >= 2);
            assertNull(LifestyleHistoryConsumer.chooseMinimum(minimum(), selected).selectedAction());
        }
    }
    @Test void completedRequestIdCannotBeReusedAfterAnotherActionCompleted() throws IOException {
        Selection reused = LifestyleHistory.select(decode(sample("completed_id_reused_after_other_applied")));
        assertEquals(Status.CONFLICT, reused.status(), "A applied, B applied, then A reused must retain all completed IDs");
        assertFalse(reused.pendingActions().isEmpty());
        assertNull(LifestyleHistoryConsumer.chooseMinimum(minimum(), reused).selectedAction());
    }
    @Test void unknownDiagnosticFloatsNullAndCollectionsStayByteExactAndImmutable() throws IOException {
        Input original = decode(sample("opaque_unknown_float_and_null_preserved")); Selection selected = LifestyleHistory.select(original);
        RetainedJson retained = selected.pendingActions().getFirst().originalJson(); byte[] expected = retained.bytes(); byte[] changed = retained.bytes();
        changed[0] = '['; assertArrayEquals(expected, retained.bytes()); assertTrue(new String(expected, StandardCharsets.UTF_8).contains("1.0"));
        assertThrows(UnsupportedOperationException.class, () -> selected.pendingActions().clear());
        assertThrows(UnsupportedOperationException.class, () -> original.history().clear());
        assertEquals(original, LifestyleHistoryCodec.decode(LifestyleHistoryCodec.encode(original)));
    }
    @Test void wrongNumericTokensReachRawReceiptParserWithoutTreeNormalization() throws IOException {
        ObjectNode request = (ObjectNode) sample("perk_pending").get("request").deepCopy();
        ObjectNode row = (ObjectNode) request.get("history").get(0); String valid = row.path("result_json").textValue();
        for (String value : List.of("3.0", "true", "\"3\"")) {
            String raw = valid.replace("\"pre_public_revision\":3", "\"pre_public_revision\":" + value);
            assertNotEquals(valid, raw); ObjectNode bad = request.deepCopy(); ((ObjectNode) bad.get("history").get(0)).put("result_json", raw);
            assertThrows(ContractViolationException.class, () -> LifestyleHistoryCodec.decode(StrictJson.canonical(bad)), value);
        }
    }
    @Test void wrapperAndOriginalReceiptRejectDuplicatesMissingAndTrailingJson() throws IOException {
        ObjectNode unknown = (ObjectNode) sample("perk_pending").get("request").deepCopy(); unknown.put("already_applied", true);
        assertThrows(ContractViolationException.class, () -> LifestyleHistoryCodec.decode(StrictJson.canonical(unknown)));
        ObjectNode missing = (ObjectNode) sample("perk_pending").get("request").deepCopy(); missing.remove("episode_run_id");
        assertThrows(ContractViolationException.class, () -> LifestyleHistoryCodec.decode(StrictJson.canonical(missing)));
        ObjectNode trailing = (ObjectNode) sample("perk_pending").get("request").deepCopy();
        ObjectNode row = (ObjectNode) trailing.get("history").get(0); String result = row.path("result_json").textValue();
        row.put("result_json", result + " {}"); assertThrows(ContractViolationException.class, () -> LifestyleHistoryCodec.decode(StrictJson.canonical(trailing)));
        row.put("result_json", result.replaceFirst("\\{", "{\"status\":\"duplicate\","));
        assertThrows(ContractViolationException.class, () -> LifestyleHistoryCodec.decode(StrictJson.canonical(trailing)));
        assertThrows(ContractViolationException.class, () -> LifestyleHistoryCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
    @Test void currentEpisodeBindingAndNoSecondPendingSourceAreRequiredByRealConsumer() throws IOException {
        Input input = decode(sample("perk_pending")); Selection selected = LifestyleHistory.select(input);
        ObjectNode current = (ObjectNode) golden().get("minimum_request").deepCopy();
        ((ObjectNode) current.get("snapshot")).put("episode_run_id", "native-40526-foreign");
        LifestyleMinPolicy.Request foreign = LifestyleMinCodec.decode(StrictJson.canonical(current));
        assertThrows(ContractViolationException.class, () -> LifestyleHistoryConsumer.applyPendingGuard(foreign, selected));
        ObjectNode additional = (ObjectNode) golden().get("minimum_request").deepCopy(); additional.putObject("pending_action").put("status", "action_state_unknown");
        LifestyleMinPolicy.Request secondSource = LifestyleMinCodec.decode(StrictJson.canonical(additional));
        assertThrows(ContractViolationException.class, () -> LifestyleHistoryConsumer.applyPendingGuard(secondSource, selected));
    }
    @Test void appliedMetadataDoesNotBlockAllLaterRecommendationsOrGrantCredit() throws IOException {
        Selection settled = LifestyleHistory.select(decode(sample("perk_material_applied"))); assertEquals(Status.CLEAR, settled.status());
        assertTrue(settled.latestApplied().isPresent());
        // This is a new synthetic final-legal observation, not an actual second Game submit.
        assertEquals(LifestyleMinPolicy.Status.RECOMMEND_ACTION, LifestyleHistoryConsumer.chooseMinimum(minimum(), settled).status());
        Selection absentEpisode = LifestyleHistory.select(new Input(null, List.of()));
        assertEquals(Status.EPISODE_UNAVAILABLE, absentEpisode.status());
        assertEquals(LifestyleMinPolicy.Status.ACTION_STATE_UNKNOWN, LifestyleHistoryConsumer.chooseMinimum(minimum(), absentEpisode).status());
    }
}
