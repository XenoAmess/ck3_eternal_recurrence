package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.Value;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.AfterAssessment;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.ExistingPlan;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Plan;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback.Request;

final class UnhandledEventFallbackTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode golden() throws IOException {
        try (InputStream input = UnhandledEventFallbackTest.class.getResourceAsStream("/unhandledevent/unhandled-event-golden-v1.json.gz")) {
            assertNotNull(input, "committed actual producer fixture is required; no skipped verification");
            try (GZIPInputStream uncompressed = new GZIPInputStream(input)) { return JSON.readTree(uncompressed); }
        }
    }
    private static Request request(JsonNode row) throws IOException { return UnhandledEventCodec.decodePlan(JSON.writeValueAsBytes(row.get("request"))); }
    private static Value json(JsonNode node) throws IOException { return RetainedJson.parse(JSON.writeValueAsBytes(node)); }
    private static Request baseline() throws IOException { return request(golden().get("plan_cases").get(0)); }

    @Test void fullProposalsMatchTheActualOldProducerForAllTwentyOnePlanCases() throws IOException {
        JsonNode corpus = golden();
        assertEquals("xar.ck3.unhandled-event-golden/v1", corpus.get("schema").textValue());
        assertEquals(21, corpus.get("plan_cases").size());
        for (JsonNode row : corpus.get("plan_cases")) {
            Optional<Plan> plan = UnhandledEventFallback.plan(request(row));
            assertEquals(json(row.get("expected_plan")), RetainedJson.parse(UnhandledEventCodec.encode(plan)), row.get("name").textValue());
            plan.ifPresent(value -> { assertFalse(value.actionAuthorized()); assertTrue(value.offlineFollowupRequired()); });
        }
    }

    @Test void afterAssessmentMatchesOriginalBeforeAfterProducerAndNeverAllowsReplay() throws IOException {
        assertEquals(11, golden().get("after_cases").size());
        for (JsonNode row : golden().get("after_cases")) {
            UnhandledEventCodec.AfterInput input = UnhandledEventCodec.decodeAfter(JSON.writeValueAsBytes(row.get("request")));
            Optional<AfterAssessment> result = UnhandledEventFallback.assessAfter(input.ticket(), input.observation());
            assertEquals(json(row.get("expected")), RetainedJson.parse(UnhandledEventCodec.encodeAfter(result)), row.get("name").textValue());
            result.ifPresent(value -> assertFalse(value.replayAllowed()));
        }
    }

    @Test void immutableTypedProjectionRoundTripsIncludingOpaqueDiagnosticFloatAndWideInteger() throws IOException {
        for (JsonNode row : golden().get("plan_cases")) {
            Request input = request(row);
            assertEquals(input, UnhandledEventCodec.decodePlan(UnhandledEventCodec.encodeRequest(input)), row.get("name").textValue());
            assertThrows(UnsupportedOperationException.class, () -> input.eventSummary().fields().clear());
        }
        ObjectValue retained = RetainedJson.object(RetainedJson.parse("{\"floating\":1.0,\"integer\":9007199254740993,\"negative_zero\":-0.0}".getBytes(StandardCharsets.UTF_8)));
        assertTrue(retained.get("floating") instanceof RetainedJson.FloatingValue);
        assertEquals(new RetainedJson.IntegerValue(new BigInteger("9007199254740993")), retained.get("integer"));
        assertEquals(retained, RetainedJson.parse(RetainedJson.encode(retained)));
    }

    @Test void actualDedicatedStrategyAndExistingFallbackAreKeptByTheConsumerPort() throws IOException {
        JsonNode dedicated = golden().get("dedicated_strategy");
        assertEquals("active_event_registry_choice", dedicated.get("phase").textValue());
        assertEquals("select-event-option-4", dedicated.get("selected_step").textValue());
        Request input = baseline();
        ExistingPlan known = new ExistingPlan(dedicated.get("phase").textValue(), dedicated.get("selected_step").textValue(), null);
        assertEquals(Optional.empty(), UnhandledEventFallback.proposeForUnhandledPhase(known, input));
        Plan fallback = UnhandledEventFallback.plan(input).orElseThrow();
        ObjectValue capture = RetainedJson.object(UnhandledEventCodec.legacyPlan(fallback).get("unhandled_event_fallback"));
        assertEquals(Optional.empty(), UnhandledEventFallback.proposeForUnhandledPhase(new ExistingPlan("active_event_unhandled_first_rendered_disabled", null, capture), input));
        assertEquals(Optional.empty(), UnhandledEventFallback.proposeForUnhandledPhase(new ExistingPlan("ordinary_government", null, null), input));
        assertEquals(Optional.of(fallback), UnhandledEventFallback.proposeForUnhandledPhase(new ExistingPlan("active_event_registry_contract_blocked", null, null), input));
    }

    @Test void missingAndExplicitNullActiveEventRetainDifferentFallbackBehavior() throws IOException {
        boolean missingSeen = false, nullSeen = false;
        for (JsonNode row : golden().get("plan_cases")) {
            if (row.get("name").textValue().equals("active-null-does-not-use-current-event")) {
                assertEquals(Optional.empty(), UnhandledEventFallback.plan(request(row))); nullSeen = true;
            }
            if (row.get("name").textValue().equals("active-missing-uses-current-event")) {
                assertEquals("select-event-option-7", UnhandledEventFallback.plan(request(row)).orElseThrow().selectedStep()); missingSeen = true;
            }
        }
        assertTrue(missingSeen && nullSeen);
    }

    @Test void rawBoolFloatAndStringIdentitiesRejectWhileIntegerPublicAndNativeFramesStayDistinct() throws IOException {
        String raw = new String(JSON.writeValueAsBytes(golden().get("plan_cases").get(0).get("request")), StandardCharsets.UTF_8);
        assertTrue(raw.contains("\"native_revision\":7"));
        for (String wrong : List.of("7.0", "true", "\"7\"")) {
            byte[] malformed = raw.replace("\"native_revision\":7", "\"native_revision\":" + wrong).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> UnhandledEventCodec.decodePlan(malformed));
        }
        byte[] versionFloat = raw.replace("\"schema_version\":1", "\"schema_version\":1.0").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventCodec.decodePlan(versionFloat));
        Plan plan = UnhandledEventFallback.plan(baseline()).orElseThrow();
        assertEquals(BigInteger.valueOf(3), plan.binding().revision()); assertEquals(BigInteger.valueOf(7), plan.binding().nativeRevision());
        assertEquals("synthetic-event-episode", plan.binding().episodeRunId());
    }

    @Test void duplicateUnknownAndMalformedInputCannotCreateAnActionProposal() throws IOException {
        String raw = new String(JSON.writeValueAsBytes(golden().get("plan_cases").get(0).get("request")), StandardCharsets.UTF_8);
        String duplicate = raw.replace("\"schema\":\"xar.ck3.unhandled-event-plan-input/v1\"", "\"schema\":\"xar.ck3.unhandled-event-plan-input/v1\",\"schema\":\"xar.ck3.unhandled-event-plan-input/v1\"");
        assertTrue(duplicate.length() > raw.length());
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventCodec.decodePlan(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventCodec.decodePlan((raw.substring(0, raw.length() - 1) + ",\"unsafe_override\":true}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> UnhandledEventCodec.decodePlan((raw + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> RetainedJson.parse("1e9999".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> RetainedJson.parse(new byte[] {(byte) 0xc3, 0x28}));
    }
}
