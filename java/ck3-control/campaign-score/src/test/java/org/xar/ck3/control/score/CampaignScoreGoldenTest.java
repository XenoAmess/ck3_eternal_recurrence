package org.xar.ck3.control.score;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Frozen real producer outputs; standard verify requires neither Python nor a game installation. */
final class CampaignScoreGoldenTest {
    private static final String RESOURCE = "/org/xar/ck3/control/score/campaign_score_python_golden_v1.jsonl";
    private static final int MAXIMUM_BYTES = 512 * 1024;
    private static final Set<String> ORIGINAL_METHODS = Set.of(
            "test_missing_baseline_is_interval_and_no_weight_redistribution",
            "test_debt_rescue_and_lost_half_reproduce_design",
            "test_gameover_denominator_and_incomplete_interval",
            "test_exported_repeating_decimals_have_exact_weighted_sum",
            "test_interval_display_outwards_and_partial_contribution_not_reweighted");

    @TestFactory
    Stream<DynamicTest> realProducerGoldenCases() throws IOException {
        return corpus().vectors().stream().map(row -> DynamicTest.dynamicTest(
                row.path("ordinal").asText() + ":" + row.path("case").asText() + ":" + row.path("operation").asText(), () -> {
                    if ("invalid_contract".equals(row.path("expected_kind").textValue())) {
                        assertThrows(ContractViolationException.class, () -> evaluate(row));
                    } else {
                        byte[] actual = evaluate(row);
                        assertArrayEquals(StrictJson.canonical(row.get("expected")), actual);
                        assertEquals(StrictJson.parse(actual), StrictJson.parse(StrictJson.canonical(StrictJson.parse(actual))));
                    }
                }));
    }

    @Test
    void corpusContainsFiveRealRegressionLineagesAndFrozenProducerPins() throws IOException {
        Corpus corpus = corpus();
        JsonNode header = corpus.header();
        assertEquals("g2.campaign-score-python-golden/v1", header.path("schema").textValue());
        assertEquals(5, header.path("original_tests_run").intValue());
        assertEquals(0, header.path("original_skips").intValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue());
        assertEquals(28, header.path("decimal_default_precision").intValue());
        assertFalse(StrictJson.text(header.get("machine_id")).isEmpty());
        StrictJson.utc(StrictJson.text(header.get("observed_at_utc")));
        assertEquals("ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d",
                header.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py").textValue());
        assertEquals("0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2",
                header.path("source_sha256").path("ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py").textValue());
        Set<String> captured = new HashSet<>();
        Set<String> operations = new HashSet<>();
        int ordinal = 0;
        for (ObjectNode row : corpus.vectors()) {
            assertEquals(++ordinal, row.path("ordinal").intValue());
            captured.add(StrictJson.text(row.get("case")));
            operations.add(StrictJson.text(row.get("operation")));
        }
        assertTrue(captured.containsAll(ORIGINAL_METHODS));
        assertEquals(Set.of("aggregate", "score360", "display", "roundtrip"), operations);
        assertEquals(ordinal, header.path("vector_count").intValue());
        assertTrue(ordinal >= 30);
    }

    @Test
    void intervalContractDistinguishesMissingNullUnknownAndEmpty() {
        ObjectNode valid = CampaignScoreCodec.json(ScoreInterval.UNKNOWN);
        assertTrue(valid.get("value").isNull());
        assertFalse(valid.get("known").booleanValue());
        for (String field : List.of("lower", "upper", "known", "value")) {
            ObjectNode row = valid.deepCopy(); row.remove(field); invalid(row);
        }
        for (String field : List.of("lower", "upper", "known")) {
            ObjectNode row = valid.deepCopy(); row.putNull(field); invalid(row);
        }
        ObjectNode row = valid.deepCopy(); row.putArray("value"); invalid(row);
        row = valid.deepCopy(); row.put("extra", "ignored"); invalid(row);
        row = valid.deepCopy(); row.put("known", true); invalid(row);
        row = valid.deepCopy(); row.put("value", "50"); invalid(row);
        row = CampaignScoreCodec.json(ScoreInterval.exact("0")); row.putNull("value"); invalid(row);
        assertThrows(ContractViolationException.class, () -> CampaignScoreCodec.history(StrictJson.parse(utf8("{\"samples\":[],\"endpoint\":null}"))));
    }

    @Test
    void decimalTokensRejectBooleanFloatIntegerNullAndWrongLexicalForms() {
        for (String raw : List.of("true", "1.0", "1", "null", "[]", "{}")) {
            assertThrows(ContractViolationException.class, () -> CampaignScoreCodec.decimal(StrictJson.parse(utf8(raw))));
        }
        for (String raw : List.of("NaN", "Infinity", "-Infinity", "", "1e9999999999")) {
            assertThrows(ContractViolationException.class, () -> ScoreDecimal.parse(raw));
        }
        assertEquals(ScoreDecimal.parse("1.00"), ScoreDecimal.parse("1"));
        assertEquals(ScoreDecimal.parse("-0"), ScoreDecimal.ZERO);
        assertEquals("-0", ScoreDecimal.parse("-0.00").lexical());
        assertEquals("1E+2", ScoreDecimal.parse("1E+2").lexical());
        assertEquals("0.0000001", ScoreDecimal.parse("1e-7").lexical());
    }

    @Test
    void rejectsDuplicateTrailingMalformedUtf8AndInconsistentIntervalBounds() {
        for (String raw : List.of("{\"lower\":\"0\",\"lower\":\"1\"}", "{} null", "[]")) {
            assertThrows(ContractViolationException.class, () -> CampaignScoreCodec.decodeInterval(utf8(raw)));
        }
        assertThrows(ContractViolationException.class, () -> CampaignScoreCodec.decodeInterval(new byte[] {(byte) 0xff}));
        assertThrows(ContractViolationException.class, () -> CampaignScoreCodec.decodeInterval(new byte[65537]));
        assertThrows(ContractViolationException.class, () -> new ScoreInterval(ScoreDecimal.integer(2), ScoreDecimal.integer(1)));
        assertThrows(ContractViolationException.class, () -> ScoreInterval.UNKNOWN.scale(ScoreDecimal.integer(-1)));
        assertThrows(ContractViolationException.class, () -> CampaignScoreCore.intervalText(ScoreDecimal.parse("1E+80"), ScoreDecimal.parse("1E+80"), 2));
    }

    @Test
    void historyIsDetachedAndGameOverDoesNotShortenTheDenominator() {
        List<ScoreInterval> samples = new ArrayList<>();
        for (int index = 0; index < 360; index++) { samples.add(ScoreInterval.exact(index < 180 ? "70" : "0")); }
        MonthlyHistory history = new MonthlyHistory(samples, ScoreInterval.exact("0"));
        samples.clear();
        assertEquals(360, history.samples().size());
        assertThrows(UnsupportedOperationException.class, () -> history.samples().clear());
        assertEquals(ScoreInterval.exact("70"), CampaignScoreCore.score360(history));
        assertThrows(ContractViolationException.class, () -> new MonthlyHistory(List.of(), ScoreInterval.exact("70")));
    }

    private static byte[] evaluate(ObjectNode row) {
        JsonNode request = row.get("input");
        return switch (StrictJson.text(row.get("operation"))) {
            case "aggregate" -> CampaignScoreCodec.encodeInterval(CampaignScoreCore.aggregateState(CampaignScoreCodec.domainScores(request)));
            case "score360" -> CampaignScoreCodec.encodeInterval(CampaignScoreCore.score360(CampaignScoreCodec.history(request)));
            case "roundtrip" -> CampaignScoreCodec.encodeInterval(CampaignScoreCodec.interval(request));
            case "display" -> {
                ObjectNode fields = StrictJson.object(request, Set.of("lower", "upper", "places"));
                String text = CampaignScoreCore.intervalText(CampaignScoreCodec.decimal(fields.get("lower")),
                        CampaignScoreCodec.decimal(fields.get("upper")), (int) StrictJson.integer(fields.get("places"), 0, 80));
                yield StrictJson.canonical(new com.fasterxml.jackson.databind.node.TextNode(text));
            }
            default -> throw new AssertionError("unknown golden operation");
        };
    }

    private static void invalid(ObjectNode row) {
        assertThrows(ContractViolationException.class, () -> CampaignScoreCodec.decodeInterval(StrictJson.canonical(row)));
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private record Corpus(ObjectNode header, List<ObjectNode> vectors) { }
    private static Corpus corpus() throws IOException {
        try (InputStream stream = CampaignScoreGoldenTest.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) { throw new AssertionError("real producer golden absent; do not skip default JUnit"); }
            byte[] raw = stream.readNBytes(MAXIMUM_BYTES + 1);
            assertTrue(raw.length > 0 && raw.length <= MAXIMUM_BYTES);
            String content = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            String[] lines = content.split("\n", -1);
            assertEquals("", lines[lines.length - 1]);
            List<ObjectNode> vectors = new ArrayList<>();
            for (int index = 1; index < lines.length - 1; index++) {
                JsonNode parsed = StrictJson.parse(utf8(lines[index]));
                assertTrue(parsed instanceof ObjectNode);
                vectors.add((ObjectNode) parsed);
            }
            JsonNode header = StrictJson.parse(utf8(lines[0]));
            assertTrue(header instanceof ObjectNode);
            return new Corpus((ObjectNode) header, List.copyOf(vectors));
        }
    }
}
