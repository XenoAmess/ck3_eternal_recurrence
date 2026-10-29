package org.xar.ck3.control.wave3.governance.marriagenotice;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.governance.marriagenotice.MarriageNoticeModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalCodec;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.NullValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.ObjectValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.WireValue;

class MarriageNoticePolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = MarriageNoticePolicyTest.class.getResourceAsStream("/marriagenotice/python-golden-v1.json")) {
            assertNotNull(input, "committed original producer golden is mandatory");
            JsonNode result = BetrothalCodec.readJson(input.readAllBytes());
            assertEquals("xar.ck3.marriage-notice-python-golden.v1", result.path("schema").textValue());
            assertFalse(result.path("machine_id").textValue().isEmpty()); assertFalse(result.path("observed_at_utc").textValue().isEmpty());
            assertEquals(13, result.path("original_tests_run").intValue()); assertEquals(0, result.path("original_failures").intValue()); assertEquals(0, result.path("original_skipped").intValue());
            assertEquals(15, result.path("review_cases").size()); assertEquals(21, result.path("continue_cases").size()); return result;
        }
    }
    private static byte[] raw(JsonNode node) { return node.toString().getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode patched(JsonNode base, JsonNode patches) {
        ObjectNode result = (ObjectNode) base.deepCopy();
        for (JsonNode patch : patches) {
            JsonNode path = patch.get("path"), parent = result;
            for (int index = 0; index < path.size() - 1; index++) { JsonNode key = path.get(index); parent = key.isIntegralNumber() ? parent.get(key.intValue()) : parent.get(key.textValue()); }
            JsonNode key = path.get(path.size() - 1);
            if (parent instanceof ObjectNode object) {
                if (patch.path("remove").asBoolean(false)) { object.remove(key.textValue()); } else { object.set(key.textValue(), patch.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (patch.path("remove").asBoolean(false)) { array.remove(key.intValue()); } else { array.set(key.intValue(), patch.get("value").deepCopy()); }
            } else { fail("invalid mandatory golden patch"); }
        }
        return result;
    }

    @Test
    void offlineReviewExactlyMatchesTheActualProducerCorpus() throws IOException {
        JsonNode golden = golden();
        for (JsonNode testCase : golden.get("review_cases")) {
            ReviewInput input = MarriageNoticeCodec.decodeReview(raw(patched(golden.get("base_review_request"), testCase.get("patches"))));
            ReviewResult result = MarriageNoticePolicy.reviewSource(input);
            assertEquals(testCase.get("applied").booleanValue(), result instanceof ReviewedEvidence, testCase.get("name").textValue());
            assertEquals(testCase.get("expected"), BetrothalCodec.readJson(MarriageNoticeCodec.encodeReview(result)), testCase.get("name").textValue());
            if (result instanceof UnchangedEvidence unchanged) { assertSame(input.historicalEvidence(), unchanged.evidence()); }
        }
    }

    @Test
    void blockedReplyAndWholeOrdinaryContinuationMatchOriginalProducer() throws IOException {
        JsonNode golden = golden();
        for (JsonNode testCase : golden.get("continue_cases")) {
            ContinueInput input = MarriageNoticeCodec.decodeContinue(raw(patched(golden.get("base_continue_request"), testCase.get("patches"))));
            assertEquals(testCase.get("expected_blocked").booleanValue(), MarriageNoticePolicy.isBlockedReply(input.blockedPlan()), testCase.get("name").textValue());
            List<JsonNode> calls = new ArrayList<>();
            ContinuationResult result = MarriageNoticePolicy.continueOrdinary(input, projection -> {
                calls.add(BetrothalCodec.readJson(MarriageNoticeCodec.encodeProjection(projection)));
                return MarriageNoticeCodec.decodePlan(raw(testCase.get("ordinary_plan")));
            });
            assertEquals(testCase.get("expected"), BetrothalCodec.readJson(MarriageNoticeCodec.encodeContinuation(result)), testCase.get("name").textValue());
            assertEquals(testCase.get("callback_calls").size(), calls.size(), testCase.get("name").textValue());
            for (int index = 0; index < calls.size(); index++) { assertEquals(testCase.get("callback_calls").get(index), calls.get(index)); }
            if (result instanceof UnchangedPlan unchanged) { assertSame(input.blockedPlan(), unchanged.plan()); }
        }
    }

    @Test
    void sourceAnnotationNeverQualifiesLoadedDefinitionAcceptOrMaterialResult() throws IOException {
        ReviewResult result = MarriageNoticePolicy.reviewSource(MarriageNoticeCodec.decodeReview(raw(golden().get("base_review_request"))));
        JsonNode knowledge = BetrothalCodec.readJson(MarriageNoticeCodec.encodeReview(result)).get("source_knowledge");
        assertFalse(knowledge.get("loaded_definition_bytes_verified").booleanValue()); assertFalse(knowledge.get("accept_outcome_qualified").booleanValue()); assertFalse(knowledge.get("material_effects_verified").booleanValue());
        assertEquals("existing_reject_only", knowledge.get("action_scope").textValue());
    }

    @Test
    void planningProjectionKeepsOriginalNotificationAndNeverOffersNotificationActions() throws IOException {
        ContinueInput input = MarriageNoticeCodec.decodeContinue(raw(golden().get("base_continue_request")));
        ObjectValue observed = (ObjectValue) input.snapshot().original();
        assertNotEquals(NullValue.INSTANCE, observed.values().get("pending_character_interaction"));
        ContinuationResult result = MarriageNoticePolicy.continueOrdinary(input, projection -> {
            assertEquals(ProjectionScope.PLANNING_ONLY, projection.scope());
            assertEquals(NullValue.INSTANCE, projection.snapshot().values().get("pending_character_interaction"));
            assertEquals(List.of("life-advance"), projection.actionSteps());
            return MarriageNoticeCodec.decodePlan("{\"phase\":\"ordinary\",\"selected_step\":\"life-advance\"}".getBytes(StandardCharsets.UTF_8));
        });
        assertInstanceOf(ContinuedPlan.class, result);
        assertNotEquals(NullValue.INSTANCE, observed.values().get("pending_character_interaction"));
        JsonNode continuation = BetrothalCodec.readJson(MarriageNoticeCodec.encodeContinuation(result)).get("notification_continuation");
        assertFalse(continuation.get("interaction_submission").booleanValue()); assertFalse(continuation.get("observed_notification_cleared").booleanValue()); assertTrue(continuation.get("planning_projection_only").booleanValue());
    }

    @Test
    void allNewEnvelopeFieldsAreRequiredAndUnknownFieldsReject() throws IOException {
        JsonNode golden = golden();
        for (boolean review : List.of(true, false)) {
            ObjectNode base = (ObjectNode) golden.get(review ? "base_review_request" : "base_continue_request").deepCopy();
            List<String> keys = new ArrayList<>(); base.fieldNames().forEachRemaining(keys::add);
            for (String key : keys) { ObjectNode missing = base.deepCopy(); missing.remove(key); assertThrows(IllegalArgumentException.class, () -> { if (review) { MarriageNoticeCodec.decodeReview(raw(missing)); } else { MarriageNoticeCodec.decodeContinue(raw(missing)); } }, key); }
            ObjectNode unknown = base.deepCopy(); unknown.put("accept_permission", true);
            assertThrows(IllegalArgumentException.class, () -> { if (review) { MarriageNoticeCodec.decodeReview(raw(unknown)); } else { MarriageNoticeCodec.decodeContinue(raw(unknown)); } });
        }
    }

    @Test
    void rawFloatBooleanAndStringTokensCannotBecomeHashesOrNativeInstanceIds() throws IOException {
        String review = golden().get("base_review_request").toString();
        for (String token : List.of("true", "1298930137.0", "\"1298930137\"")) {
            String changed = review.replace("\"deterministic_key_hash\":1298930137", "\"deterministic_key_hash\":" + token);
            assertNotEquals(review, changed); assertThrows(IllegalArgumentException.class, () -> MarriageNoticeCodec.decodeReview(changed.getBytes(StandardCharsets.UTF_8)), token);
        }
        String continuation = golden().get("base_continue_request").toString();
        for (String token : List.of("false", "-123.0", "\"-123\"", "2147483648", "-2147483649", "-1")) {
            String changed = continuation.replace("\"instance_id\":-123", "\"instance_id\":" + token);
            assertNotEquals(continuation, changed); assertThrows(IllegalArgumentException.class, () -> MarriageNoticeCodec.decodeContinue(changed.getBytes(StandardCharsets.UTF_8)), token);
        }
    }

    @Test
    void duplicateKeysMalformedUtf8AndOutputEvidenceRoundTripAreChecked() throws IOException {
        String base = golden().get("base_review_request").toString();
        assertThrows(IllegalArgumentException.class, () -> MarriageNoticeCodec.decodeReview(("{\"context\":null," + base.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MarriageNoticeCodec.decodeReview((base + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MarriageNoticeCodec.decodeReview(new byte[] {(byte) 0xc3, 0x28}));
        ReviewResult reviewed = MarriageNoticePolicy.reviewSource(MarriageNoticeCodec.decodeReview(base.getBytes(StandardCharsets.UTF_8)));
        byte[] first = MarriageNoticeCodec.encodeReview(reviewed); WireValue restored = BetrothalCodec.decodeEvidence(first);
        assertArrayEquals(first, BetrothalCodec.encodeEvidence(restored));
        String decimalHistory = base.replace("\"historical_evidence\":{", "\"historical_evidence\":{\"opaque_decimal\":1.0,");
        assertNotEquals(base, decimalHistory);
        ReviewResult withDecimal = MarriageNoticePolicy.reviewSource(MarriageNoticeCodec.decodeReview(decimalHistory.getBytes(StandardCharsets.UTF_8)));
        JsonNode wire = BetrothalCodec.readJson(MarriageNoticeCodec.encodeReview(withDecimal));
        assertTrue(wire.get("opaque_decimal").isFloatingPointNumber());
    }

    @Test
    void nativeGenerationIdentityUsesSigned32RatherThanCharacterOrFileTimeDomain() throws IOException {
        String base = golden().get("base_continue_request").toString();
        for (String identity : List.of("-2147483648", "0", "2147483647")) {
            String changed = base.replace("\"instance_id\":-123", "\"instance_id\":" + identity)
                    .replace("\"pending_interaction_id\":-123", "\"pending_interaction_id\":" + identity);
            ContinueInput input = MarriageNoticeCodec.decodeContinue(changed.getBytes(StandardCharsets.UTF_8));
            ContinuationResult result = MarriageNoticePolicy.continueOrdinary(input, projection -> MarriageNoticeCodec.decodePlan(
                    "{\"phase\":\"ordinary\",\"selected_step\":\"life-advance\"}".getBytes(StandardCharsets.UTF_8)));
            ContinuedPlan continued = assertInstanceOf(ContinuedPlan.class, result);
            assertEquals(new java.math.BigInteger(identity), continued.pendingInteractionId());
        }
    }
}
