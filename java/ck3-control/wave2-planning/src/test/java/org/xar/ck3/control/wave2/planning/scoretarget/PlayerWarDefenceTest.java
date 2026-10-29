package org.xar.ck3.control.wave2.planning.scoretarget;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
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

final class PlayerWarDefenceTest {
    private static final String RESOURCE = "/scoretarget/player_war_defence_python_v1.jsonl";
    private static final String ORIGINAL_METHOD = "test_explicit_player_wars_ignore_unrelated_shells_but_not_missing_or_conflicts";

    @TestFactory
    Stream<DynamicTest> originalProducerAndRealConsumerRegressionGolden() throws IOException {
        return corpus().vectors().stream().map(row -> DynamicTest.dynamicTest(
                row.path("ordinal").asText() + ":" + row.path("case").asText(), () -> {
                    // Preserve original raw 1.0 tokens; never roundtrip through a JSON tree first.
                    JsonNode input = row.get("input_json");
                    assertTrue(input != null && input.isTextual());
                    byte[] request = utf8(input.textValue());
                    assertTrue(request.length > 0 && request.length <= StrictJson.INPUT_MAX_BYTES);
                    if ("invalid_contract".equals(row.path("expected_kind").textValue())) {
                        assertThrows(ContractViolationException.class, () -> PlayerWarDefenceCodec.evaluate(request));
                    } else {
                        byte[] actual = PlayerWarDefenceCodec.evaluate(request);
                        assertArrayEquals(StrictJson.canonical(row.get("expected")), actual);
                        assertEquals(StrictJson.parse(actual), StrictJson.parse(StrictJson.canonical(StrictJson.parse(actual))));
                    }
                }));
    }

    @Test
    void frozenCorpusIdentifiesTheUnchangedActualProducerAndConsumer() throws IOException {
        Corpus corpus = corpus(); JsonNode header = corpus.header();
        assertEquals("g2.scoretarget-player-war-golden/v1", header.path("schema").textValue());
        assertEquals(1, header.path("original_tests_run").intValue());
        assertEquals(0, header.path("original_skips").intValue());
        assertEquals(0, header.path("native_game_rpc_count").intValue());
        assertFalse(header.path("production_consumer_switched").booleanValue());
        assertEquals("campaign_score_save_reader._project_metrics:825", header.path("consumer").textValue());
        assertEquals("pure_saved_player_war_defence_only", header.path("scope").textValue());
        StrictJson.utc(StrictJson.text(header.get("observed_at_utc")));
        StrictJson.text(header.get("machine_id"));
        assertEquals("ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e",
                header.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py").textValue());
        assertEquals("0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2",
                header.path("source_sha256").path("ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py").textValue());
        Set<String> cases = new HashSet<>(); int ordinal = 0;
        for (ObjectNode row : corpus.vectors()) {
            assertEquals(++ordinal, row.path("ordinal").intValue());
            cases.add(StrictJson.text(row.get("case")));
        }
        assertEquals(ordinal, header.path("vector_count").intValue());
        assertTrue(cases.containsAll(Set.of(ORIGINAL_METHOD, "complete-1024-ids", "over-1024-ids-rejects-before-lookup",
                "verify-all-after-positive-match", "python-integer-above-uint64-exact", "unicode-digits-and-whitespace")));
    }

    @Test
    void actorNeverCoercesRawBooleanFractionStringOrNull() {
        for (String token : List.of("true", "false", "3.0", "3e0", "\"3\"", "null", "[]", "{}")) {
            byte[] raw = utf8("{\"actor\":" + token + ",\"character_fields\":{},\"wars\":{}}");
            assertThrows(ContractViolationException.class, () -> PlayerWarDefenceCodec.evaluate(raw));
        }
        for (String raw : List.of("{\"actor\":3,\"wars\":{}}", "{\"actor\":3,\"character_fields\":{},\"wars\":{},\"extra\":true}",
                "{\"actor\":3,\"character_fields\":null,\"wars\":{}}", "{\"actor\":3,\"character_fields\":{},\"wars\":[]}")) {
            assertThrows(ContractViolationException.class, () -> PlayerWarDefenceCodec.evaluate(utf8(raw)));
        }
    }

    @Test
    void absenceNullEmptyAndMarkerPresenceRemainDifferent() {
        assertEquals("MISSING_LIST", audit(request("{}", "{}")).path("reason").textValue());
        assertEquals("EMPTY_WITHOUT_PRESENCE", audit(request("{\"landed_data.wars\":\"\"}", "{}")).path("reason").textValue());
        JsonNode known = result(request("{\"present:landed_data.wars\":\"true\"}", "{}"));
        assertFalse(known.path("own_defence").booleanValue()); assertTrue(known.path("audit").path("known").booleanValue());
        assertEquals("INVALID_LIST_TYPE", audit(request("{\"present:landed_data.wars\":\"true\",\"landed_data.wars\":null}", "{}")).path("reason").textValue());
        assertEquals("MISSING_LIST", audit(request("{\"present:landed_data.wars\":true}", "{}")).path("reason").textValue());
        assertEquals("CONFLICT_OR_TRUNCATED_LIST", audit(request("{\"landed_data.wars\":\"9\",\"nonunique:landed_data.wars\":false}",
                "{\"9\":{\"casus_belli.defender\":\"3\"}}")).path("reason").textValue());
        PlayerWarInput empty = PlayerWarDefenceCodec.decode(request("{}", "{}"));
        assertTrue(empty.character().list() instanceof ScalarField.Missing);
        PlayerWarInput explicitNull = PlayerWarDefenceCodec.decode(request("{\"landed_data.wars\":null}", "{}"));
        assertTrue(explicitNull.character().list() instanceof ScalarField.NullValue);
    }

    @Test
    void noEarlyKnownAnswerAndNoIntegerFloatOrKeyAliasShortcuts() {
        JsonNode incomplete = audit(request("{\"landed_data.wars\":\"9 10\"}", "{\"9\":{\"casus_belli.defender\":\"3\"}}"));
        assertFalse(incomplete.path("known").booleanValue());
        assertEquals("MISSING_OR_CONFLICTING_WAR", incomplete.path("reason").textValue());
        assertEquals(2, incomplete.path("listed_war_ids").size());
        for (String token : List.of("true", "3", "3.0", "null", "[]", "{}")) {
            assertEquals("MISSING_CB_DEFENDER", audit(request("{\"landed_data.wars\":\"9\"}",
                    "{\"9\":{\"casus_belli.defender\":" + token + "}}")).path("reason").textValue());
        }
        assertEquals("MISSING_OR_CONFLICTING_WAR", audit(request("{\"landed_data.wars\":\"9\"}",
                "{\"09\":{\"casus_belli.defender\":\"3\"}}")).path("reason").textValue());
        assertEquals("INVALID_OR_DUPLICATE_WAR_IDS", audit(request("{\"landed_data.wars\":\"9 009\"}", "{}")).path("reason").textValue());
    }

    @Test
    void integerIdentityDoesNotPassThroughLongOrJavaScriptNumber() {
        BigInteger identity = new BigInteger("18446744073709551617");
        byte[] raw = utf8("{\"actor\":" + identity + ",\"character_fields\":{\"landed_data.wars\":\"" + identity
                + "\"},\"wars\":{\"" + identity + "\":{\"casus_belli.defender\":\"" + identity + "\"}}}");
        JsonNode output = result(raw);
        assertTrue(output.path("own_defence").booleanValue());
        assertEquals(identity, output.path("audit").path("listed_war_ids").get(0).bigIntegerValue());
    }

    @Test
    void typedInputAndAuditAreDetachedAndSdkExtensionsAreAcceptedAsProjections() {
        Map<String, PlayerWarInput.WarEntry> wars = new HashMap<>();
        wars.put("9", new PlayerWarInput.ObservedWar(new ScalarField.Text("7"), false));
        PlayerWarInput input = new PlayerWarInput(BigInteger.valueOf(3),
                new PlayerWarInput.CharacterWars(new ScalarField.Text("9"), false, false, false), wars);
        wars.clear();
        PlayerWarDefenceResult output = PlayerWarDefence.project(input);
        assertTrue(output instanceof PlayerWarDefenceResult.Known known && !known.ownDefence());
        assertThrows(UnsupportedOperationException.class, () -> input.wars().clear());
        assertThrows(UnsupportedOperationException.class, () -> output.listedWarIds().clear());
        JsonNode extension = audit(request("{\"landed_data.wars\":\"9\",\"new_field\":{\"nested\":null}}",
                "{\"9\":{\"casus_belli.defender\":\"7\",\"new_war_field\":[true]}}"));
        assertTrue(extension.path("known").booleanValue());
    }

    @Test
    void duplicateTrailingAndMalformedUtf8CannotMasqueradeAsSavedEvidence() {
        for (String raw : List.of("{\"actor\":3,\"actor\":4,\"character_fields\":{},\"wars\":{}}",
                "{\"actor\":3,\"character_fields\":{},\"wars\":{}} null")) {
            assertThrows(ContractViolationException.class, () -> PlayerWarDefenceCodec.evaluate(utf8(raw)));
        }
        assertThrows(ContractViolationException.class, () -> PlayerWarDefenceCodec.evaluate(new byte[] {(byte) 0xff}));
        assertThrows(ContractViolationException.class, () -> PlayerWarDefenceCodec.evaluate(new byte[65537]));
    }

    private static JsonNode audit(byte[] request) { return result(request).path("audit"); }
    private static JsonNode result(byte[] request) { return StrictJson.parse(PlayerWarDefenceCodec.evaluate(request)); }
    private static byte[] request(String fields, String wars) { return utf8("{\"actor\":3,\"character_fields\":" + fields + ",\"wars\":" + wars + "}"); }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private record Corpus(ObjectNode header, List<ObjectNode> vectors) { }
    private static Corpus corpus() throws IOException {
        try (InputStream stream = PlayerWarDefenceTest.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) { throw new AssertionError("committed real producer golden required; do not skip"); }
            byte[] raw = stream.readNBytes(96 * 1024 + 1);
            assertTrue(raw.length > 0 && raw.length <= 96 * 1024);
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            String[] lines = text.split("\n", -1); assertEquals("", lines[lines.length - 1]);
            JsonNode header = StrictJson.parse(utf8(lines[0])); assertTrue(header instanceof ObjectNode);
            List<ObjectNode> vectors = new ArrayList<>();
            for (int index = 1; index < lines.length - 1; index++) {
                JsonNode row = StrictJson.parse(utf8(lines[index])); assertTrue(row instanceof ObjectNode);
                vectors.add((ObjectNode) row);
            }
            return new Corpus((ObjectNode) header, List.copyOf(vectors));
        }
    }
}
