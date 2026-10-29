package org.xar.ck3.control.wave2.military.wardeclaredoverview;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.warresults.WarResultsPolicy.WindowPresence;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class WarDeclaredOverviewTest {
    @TestFactory Stream<DynamicTest> independentOldProducerAndActualOldConsumerGolden() throws IOException {
        JsonNode golden = golden(); assertEquals(15, golden.get("original_tests").intValue());
        assertEquals(0, golden.get("original_skipped").intValue());
        assertEquals("xar.ck3.war-declared-overview-priority-golden/v1", golden.get("schema").textValue());
        assertTrue(golden.get("source_pins").size() >= 5); assertTrue(golden.get("input_corpus_ref").get("sha256").isTextual());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : golden.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                var request = WarDeclaredOverviewPolicy.decode(StrictJson.canonical(vector.get("input")));
                assertEquals(vector.get("plan"), StrictJson.parse(WarDeclaredOverviewPolicy.encodePlan(WarDeclaredOverviewPolicy.plan(request))));
                WindowPresence presence = request.snapshot().flatMap(frame -> frame.observation().value())
                        .map(WarDeclaredOverviewPolicy::presence).orElse(WindowPresence.UNKNOWN);
                assertEquals(vector.get("presence").textValue(), presence.name().toLowerCase(Locale.ROOT));
                if (request.snapshot().isPresent()) {
                    assertEquals(vector.get("query_frame"), StrictJson.parse(WarDeclaredOverviewPolicy.encodeQueryFrame(
                            WarDeclaredOverviewPolicy.queryFrame(request.snapshot().orElseThrow()))));
                } else { assertTrue(vector.get("query_frame").isNull()); }
                assertEquals(request, WarDeclaredOverviewPolicy.decode(WarDeclaredOverviewPolicy.encodeRequest(request)));
            }));
        }
        return tests.stream();
    }

    @Test void resultsCheckDueNeverSuppressesTheSeparateDeclaredOverviewRead() throws IOException {
        ObjectNode input = input("check-not-due");
        var request = WarDeclaredOverviewPolicy.decode(StrictJson.canonical(input));
        JsonNode plan = StrictJson.parse(WarDeclaredOverviewPolicy.encodePlan(WarDeclaredOverviewPolicy.plan(request)));
        assertEquals("query-war-declared-overview-v1", plan.get("selected_step").textValue());
        assertFalse(plan.get("war_declared_overview").has("check_due"));
        assertFalse(plan.get("war_declared_overview").has("next_check_date_raw"));
        ObjectNode snapshot = object(input.get("snapshot")); snapshot.put("war_results_window_v1_check_due", "unrelated metadata");
        assertEquals(request, WarDeclaredOverviewPolicy.decode(StrictJson.canonical(input)));
    }

    @Test void resultsSourceSchemaCannotBeAnOverviewCurrentObservation() throws IOException {
        ObjectNode input = input("visible");
        object(input.get("snapshot").get("war_declared_overview_v1_observation")).put("sdk_validation_schema", "war-results-window-source-v1");
        JsonNode plan = StrictJson.parse(WarDeclaredOverviewPolicy.encodePlan(WarDeclaredOverviewPolicy.plan(
                WarDeclaredOverviewPolicy.decode(StrictJson.canonical(input)))));
        assertEquals("query-war-declared-overview-v1", plan.get("selected_step").textValue());
        assertEquals("unknown", plan.get("war_declared_overview").get("presence").textValue());
        assertFalse(plan.get("war_declared_overview").get("close_action_credit").booleanValue());
    }

    @Test void distinctInputSchemaAndRawNativeFloatAreRejectedWithoutAliasFallback() throws IOException {
        ObjectNode input = input("unknown-query"); input.put("schema", "xar.ck3.war-results-priority-input/v1");
        assertThrows(IllegalArgumentException.class, () -> WarDeclaredOverviewPolicy.decode(StrictJson.canonical(input)));
        String raw = "{\"schema\":\"" + WarDeclaredOverviewPolicy.SCHEMA + "\",\"snapshot\":{\"native_revision\":1.0},\"action_steps\":[],\"bridge_capabilities\":[]}";
        assertThrows(IllegalArgumentException.class, () -> WarDeclaredOverviewPolicy.decode(raw.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void pendingOriginalRemainsUncreditedAndNeverSelectsASecondClose() throws IOException {
        var request = WarDeclaredOverviewPolicy.decode(StrictJson.canonical(input("pending-visible-never-resubmit")));
        JsonNode plan = StrictJson.parse(WarDeclaredOverviewPolicy.encodePlan(WarDeclaredOverviewPolicy.plan(request)));
        assertEquals("pending", plan.get("status").textValue()); assertTrue(plan.get("selected_step").isNull());
        assertTrue(plan.get("pending_actions").isEmpty()); assertTrue(plan.get("war_declared_overview").get("close_pending").booleanValue());
        assertFalse(plan.get("war_declared_overview").get("close_action_credit").booleanValue());
    }

    private static ObjectNode input(String name) throws IOException {
        for (JsonNode vector : golden().get("cases")) { if (name.equals(vector.get("name").textValue())) { return object(vector.get("input")).deepCopy(); } }
        throw new IOException("required producer vector missing: " + name);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = WarDeclaredOverviewTest.class.getResourceAsStream("/wardeclaredoverview/producer-golden.json")) {
            if (stream == null) { throw new IOException("required committed independent producer golden missing"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode object(JsonNode value) { return (ObjectNode) value; }
}
