package org.xar.ck3.control.wave3.planning.scorestate;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.score.CampaignScoreCodec;
import org.xar.ck3.control.score.CampaignScoreCore;
import org.xar.ck3.control.score.DomainScores;
import org.xar.ck3.control.score.ScoreDecimal;

final class StateScoreTest {
    private static final Set<String> METHODS = Set.of(
            "test_missing_baseline_is_interval_and_no_weight_redistribution",
            "test_debt_rescue_and_lost_half_reproduce_design",
            "test_exported_repeating_decimals_have_exact_weighted_sum",
            "test_interval_display_outwards_and_partial_contribution_not_reweighted",
            "test_complete_explanations_negative_cash_and_strict_date",
            "test_cli_main_single_projection_scan_auto_map_and_export");
    private static final Map<String, String> PINS = Map.of(
            "ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py",
            "ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d",
            "ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py",
            "ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e",
            "ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py",
            "749742086fa8977c2eafa0593801fe4328228a485ebe5f9178006ee823bb0006",
            "ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py",
            "0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2",
            "ck3_autonomous_player/tools/score_ck3_campaign.py",
            "ba6493478872ee6c100360b689d1eed4c8aca6aee40463b44a7bf1b3f849b212");


    @Test void javaOutputsContinueAllOriginalReportAndCliConsumers() throws Exception {
        JsonNode result = StateScoreGoldenExporter.verifyOriginalConsumers();
        assertEquals("PASS", result.path("status").textValue());
        assertEquals(6, result.path("tests").intValue());
        assertTrue(result.path("complete_consumer_comparisons").intValue() > 0);
    }

    @TestFactory Stream<DynamicTest> actualProducerAndAllScoreConsumers() throws IOException {
        List<JsonNode> corpus = corpus();
        JsonNode header = corpus.getFirst();
        assertEquals("g2.score-state-python-golden/v1", header.path("schema").asText());
        assertEquals("xenoamess-full-tower-eb9d2c1186", header.path("machine_id").asText());
        StrictJson.utc(StrictJson.text(header.get("observed_at_utc")));
        assertEquals(6, header.path("original_tests_run").intValue());
        assertEquals(0, header.path("original_skips").intValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue());
        assertFalse(header.path("production_consumer_switched").booleanValue());
        Set<String> methods = new HashSet<>();
        header.path("original_test_methods").forEach(value -> methods.add(StrictJson.text(value)));
        assertEquals(METHODS, methods);
        PINS.forEach((path, sha) -> assertEquals(sha, header.path("source_sha256").path(path).asText()));
        assertEquals(PINS.size(), header.path("source_sha256").size());
        assertEquals(corpus.size() - 1, header.path("vector_count").intValue());
        Set<String> observedMethods = new HashSet<>();
        Set<String> observedCallers = new HashSet<>();
        for (JsonNode row : corpus.subList(1, corpus.size())) {
            row.path("captured_in").forEach(value -> observedMethods.add(StrictJson.text(value)));
            row.path("callers").forEach(value -> observedCallers.add(StrictJson.text(value)));
        }
        assertTrue(observedMethods.containsAll(METHODS));
        assertTrue(observedCallers.containsAll(Set.of("build_report", "main")), "must include actual report and CLI call sites");
        List<String> packets = new ArrayList<>();
        header.path("packet_json").forEach(value -> packets.add(StrictJson.text(value)));
        assertFalse(packets.isEmpty());
        return corpus.subList(1, corpus.size()).stream().map(row -> DynamicTest.dynamicTest(
                "original-state-" + row.path("ordinal").intValue() + "-" + row.path("captured_in").get(0).textValue(), () -> {
                    int current = Math.toIntExact(StrictJson.integer(row.get("current_packet"), 0, packets.size() - 1));
                    int baseline = Math.toIntExact(StrictJson.integer(row.get("baseline_packet"), 0, packets.size() - 1));
                    byte[] request = bytes("{\"current\":" + packets.get(current) + ",\"baseline\":" + packets.get(baseline) + "}");
                    ProjectionResult registered = org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.registeredResult(
                            new ScoreStateProjectionPortCatalog().registrations().getFirst(), request);
                    if (row.path("expected_kind").textValue().equals("invalid_contract")) {
                        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, registered);
                        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
                        assertThrows(ContractViolationException.class, () -> StateScore.evaluate(StateScoreCodec.decode(request)));
                    } else {
                        DomainScores result = StateScore.evaluate(StateScoreCodec.decode(request));
                        ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, registered);
                        assertArrayEquals(StateScoreCodec.encode(result), succeeded.result().bytes());
                        assertEquals(row.get("expected"), StateScoreCodec.json(result));
                        assertEquals(row.get("aggregate"), CampaignScoreCodec.json(CampaignScoreCore.aggregateState(result)));
                        assertEquals(result, CampaignScoreCodec.domainScores(StrictJson.parse(StateScoreCodec.encode(result))));
                    }
                }));
    }

    @Test void strictEnvelopeDoesNotAcceptAliasesOrCoercions() {
        for (String raw : List.of("{\"current\":{},\"baseline\":{},\"alias\":{}}", "{\"current\":{}}",
                "{\"current\":null,\"baseline\":{}}", "{\"current\":[],\"baseline\":{}}")) {
            assertThrows(ContractViolationException.class, () -> StateScoreCodec.decode(bytes(raw)));
        }
        for (String value : List.of("true", "1.0", "null", "[]", "{}", "\"NaN\"")) {
            String raw = "{\"current\":{\"house_anchor_id\":{\"availability\":\"observed\",\"unit\":\"id\",\"value\":"
                    + value + "}},\"baseline\":{}}";
            assertThrows(ContractViolationException.class, () -> StateScore.evaluate(StateScoreCodec.decode(bytes(raw))));
        }
    }

    @Test void missingNullEmptyAndUnusedValuesRemainDifferent() {
        StateScoreInput input = StateScoreCodec.decode(bytes("{\"current\":{\"gross_income\":null,\"Q_realm\":{},"
                + "\"K_dynasty\":[]},\"baseline\":{}}"));
        assertInstanceOf(MetricRow.NullValue.class, input.current().row(MetricName.INCOME));
        assertInstanceOf(MetricRow.Missing.class, input.current().row(MetricName.REBELS));
        assertInstanceOf(MetricRow.Fields.class, input.current().row(MetricName.REALM));
        assertEquals(MetricScalar.TokenKind.ARRAY, ((MetricRow.NonObject) input.current().row(MetricName.DYNASTY)).kind());
        assertTrue(StateScore.metric(input.current(), MetricName.INCOME).isEmpty());
        assertThrows(ContractViolationException.class, () -> StateScore.boundedMetric(input.current(), MetricName.INCOME));
        String unknown = "{\"current\":{\"Q_realm\":{\"availability\":\"unknown\",\"unit\":false,\"value\":1.0},"
                + "\"sdk_extension\":{\"value\":1.0}},\"baseline\":{}}";
        assertEquals("0", StateScore.evaluate(StateScoreCodec.decode(bytes(unknown))).land().lower().lexical());
    }

    @Test void immutableTypedBoundaryAndCanonicalRoundtrip() {
        StateScoreInput parsed = StateScoreCodec.decode(bytes("{\"current\":{},\"baseline\":{}}"));
        assertThrows(UnsupportedOperationException.class,
                () -> parsed.current().rows().put(MetricName.GOLD, new MetricRow.NullValue()));
        ObjectNode body = StrictJson.object(); body.set("current", StrictJson.object()); body.set("baseline", StrictJson.object());
        assertEquals(parsed, StateScoreCodec.decode(StrictJson.canonical(body)));
        assertThrows(NullPointerException.class, () -> new StateScoreInput(null, parsed.baseline()));
        assertThrows(NullPointerException.class, () -> new MetricPacket(Map.of(MetricName.GOLD, new MetricRow.Fields(
                new MetricScalar.Text("observed"), new MetricScalar.Text("gold"), null,
                new MetricScalar.Missing(), new MetricScalar.Missing()))));
    }

    @Test void normalizationRejectsInvalidDomainAndKeepsExplicitFortyDigitContext() {
        assertThrows(ContractViolationException.class, () -> StateScore.normalize(d("-1"), d("1"), d("1")));
        assertThrows(ContractViolationException.class, () -> StateScore.normalize(d("1"), d("-1"), d("1")));
        assertThrows(ContractViolationException.class, () -> StateScore.normalize(d("1"), d("1"), d("0")));
        assertEquals(40, StateScore.normalize(d("1"), d("2"), d("1")).value().precision());
    }

    private static ScoreDecimal d(String value) { return ScoreDecimal.parse(value); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static List<JsonNode> corpus() throws IOException {
        try (InputStream stream = StateScoreTest.class.getResourceAsStream("/scorestate/state_python_v1.jsonl")) {
            assertNotNull(stream, "committed original-producer corpus is mandatory; never skip missing oracle");
            byte[] raw = stream.readAllBytes();
            assertTrue(raw.length > 0 && raw.length <= 96 * 1024 && raw[raw.length - 1] == 10);
            List<JsonNode> rows = new ArrayList<>();
            for (String line : new String(raw, StandardCharsets.UTF_8).split("\n")) { rows.add(StrictJson.parse(bytes(line))); }
            assertTrue(rows.size() > 30);
            return List.copyOf(rows);
        }
    }
}
