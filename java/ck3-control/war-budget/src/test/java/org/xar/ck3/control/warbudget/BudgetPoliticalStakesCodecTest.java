package org.xar.ck3.control.warbudget;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class BudgetPoliticalStakesCodecTest {
    private record Source(ObjectNode snapshot, JsonNode root, JsonNode expected, int ordinal) { }
    @Test
    void sharedPortMatchesActualPoliticalSubresultsFromOriginalEmergencyProducer() throws IOException {
        List<Source> sources = sources(); assertFalse(sources.isEmpty(), "original producer must actually expose political subresults");
        boolean qualifiedObserved = false;
        for (Source source : sources) {
            var context = BudgetPoliticalStakesCodec.parseContext(StrictJson.canonical(source.snapshot()), StrictJson.canonical(source.root()));
            var result = BudgetPoliticalStakesCodec.observe(context, source.ordinal());
            assertTrue(BudgetJson.equal(source.expected(), StrictJson.parse(result.toJsonBytes())));
            boolean qualified = BudgetPoliticalStakesCodec.qualify(result.toJsonBytes());
            assertEquals(qualified, BudgetPoliticalStakesCodec.qualified(result)); qualifiedObserved |= qualified;
            byte[] changedCopy = result.toJsonBytes(); changedCopy[0] = 0;
            assertTrue(BudgetJson.equal(source.expected(), StrictJson.parse(result.toJsonBytes())));
        }
        assertTrue(qualifiedObserved, "a real original positive must exist; no fallback fixture or skip");
    }
    @Test
    void originalRowOrdinalAndUniqueWarCheckCannotSelectAnotherWar() throws IOException {
        Source source = sources().stream().filter(row -> row.expected().path("status").asText().equals("available")).findFirst().orElseThrow();
        ObjectNode snapshot = source.snapshot().deepCopy();
        JsonNode war = snapshot.path("active_wars").get(source.ordinal()).deepCopy();
        snapshot.putArray("active_wars").addNull().add(war);
        var context = BudgetPoliticalStakesCodec.parseContext(StrictJson.canonical(snapshot), StrictJson.canonical(source.root()));
        assertEquals(2, context.activeWarCount());
        assertThrows(ContractViolationException.class, () -> BudgetPoliticalStakesCodec.observe(context, 0));
        assertTrue(BudgetPoliticalStakesCodec.qualified(BudgetPoliticalStakesCodec.observe(context, 1)));
        ((com.fasterxml.jackson.databind.node.ArrayNode) snapshot.get("active_wars")).add(war);
        var duplicate = BudgetPoliticalStakesCodec.parseContext(StrictJson.canonical(snapshot), StrictJson.canonical(source.root()));
        assertFalse(BudgetPoliticalStakesCodec.qualified(BudgetPoliticalStakesCodec.observe(duplicate, 1)));
        assertThrows(ContractViolationException.class, () -> BudgetPoliticalStakesCodec.observe(context, -1));
        assertThrows(ContractViolationException.class, () -> BudgetPoliticalStakesCodec.observe(context, 2));
    }
    @Test
    void staleRootAndAlteredProfileCannotBeCallerQualified() throws IOException {
        Source source = sources().stream().filter(row -> row.expected().path("status").asText().equals("available")).findFirst().orElseThrow();
        ObjectNode stale = ((ObjectNode) source.root()).deepCopy(); stale.put("snapshot_revision", 0);
        var context = BudgetPoliticalStakesCodec.parseContext(StrictJson.canonical(source.snapshot()), StrictJson.canonical(stale));
        assertFalse(BudgetPoliticalStakesCodec.qualified(BudgetPoliticalStakesCodec.observe(context, source.ordinal())));
        var absent = BudgetPoliticalStakesCodec.parseContext(StrictJson.canonical(source.snapshot()), "null".getBytes(StandardCharsets.UTF_8));
        assertFalse(BudgetPoliticalStakesCodec.qualified(BudgetPoliticalStakesCodec.observe(absent, source.ordinal())));
        ObjectNode altered = ((ObjectNode) source.expected()).deepCopy(); ((ObjectNode) altered.get("source_contract")).put("common/casus_belli_types/00_civil_war.txt", "bad");
        assertFalse(BudgetPoliticalStakesCodec.qualify(StrictJson.canonical(altered)));
        String original = new String(StrictJson.canonical(source.expected()), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "\"1\"")) {
            String raw = original.replaceFirst("\"database_index\":\\d+", "\"database_index\":" + java.util.regex.Matcher.quoteReplacement(token));
            assertFalse(BudgetPoliticalStakesCodec.qualify(raw.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test
    void fullCbExtensionKeepsFloatingJsonTypeAndObservedContextDoesNotLeakMutableTrees() throws IOException {
        Source source = sources().stream().filter(row -> row.expected().path("status").asText().equals("available")).findFirst().orElseThrow();
        ObjectNode snapshot = source.snapshot().deepCopy();
        for (JsonNode row : snapshot.get("war_termination_options")) {
            if (row.path("war_id").equals(source.expected().path("war_id"))) { ((ObjectNode) row.get("active_casus_belli_identity")).put("opaque_future_value", 1.0); }
        }
        byte[] bytes = snapshot.toString().getBytes(StandardCharsets.UTF_8);
        var context = BudgetPoliticalStakesCodec.parseContext(bytes, StrictJson.canonical(source.root())); bytes[0] = 0; snapshot.removeAll();
        var result = BudgetPoliticalStakesCodec.observe(context, source.ordinal()); assertTrue(BudgetPoliticalStakesCodec.qualified(result));
        JsonNode extension = StrictJson.parse(result.toJsonBytes()).path("active_casus_belli_identity").path("opaque_future_value");
        assertTrue(extension.isFloatingPointNumber()); assertEquals(0, extension.decimalValue().compareTo(java.math.BigDecimal.ONE));
        assertTrue(BudgetPoliticalStakesCodec.qualify(result.toJsonBytes()));
        ObjectNode root = ((ObjectNode) source.root()).deepCopy(); root.putObject("primary_title").put("title_id", 2230.0);
        var rootContext = BudgetPoliticalStakesCodec.parseContext(StrictJson.canonical(source.snapshot()), root.toString().getBytes(StandardCharsets.UTF_8));
        assertTrue(StrictJson.parse(rootContext.currentRootJsonBytes()).path("primary_title").path("title_id").isFloatingPointNumber());
    }
    private static List<Source> sources() throws IOException {
        try (InputStream input = BudgetPoliticalStakesCodecTest.class.getResourceAsStream("/org/xar/ck3/control/warbudget/budget_golden_v1.jsonl.gz")) {
            if (input == null) { throw new AssertionError("committed real original budget corpus missing"); }
            try (GZIPInputStream gzip = new GZIPInputStream(input)) {
                byte[] raw = gzip.readNBytes(8 * 1024 * 1024 + 1); assertTrue(raw.length <= 8 * 1024 * 1024);
                String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
                String[] lines = text.split("\n", -1); assertEquals("", lines[lines.length - 1]); assertEquals(0, (lines.length - 2) % 3);
                List<Source> result = new ArrayList<>();
                for (int i = 1; i < lines.length - 1; i += 3) {
                    JsonNode metadata = StrictJson.parse(lines[i].getBytes(StandardCharsets.UTF_8));
                    JsonNode request = StrictJson.parse(lines[i + 1].getBytes(StandardCharsets.UTF_8)), expected = StrictJson.parse(lines[i + 2].getBytes(StandardCharsets.UTF_8));
                    if (!metadata.path("expected_kind").asText().equals("result") || !request.path("operation").asText().equals("observe_emergency_policy_v1")) { continue; }
                    JsonNode profile = expected.path("trigger_evidence").path("political_survival_stakes_v1");
                    if (!profile.isObject()) { continue; }
                    ObjectNode snapshot = (ObjectNode) request.path("arguments").get("snapshot");
                    JsonNode wars = snapshot.path("active_wars");
                    for (int ordinal = 0; ordinal < wars.size(); ordinal++) {
                        if (wars.get(ordinal).path("war_id").equals(expected.path("war_id"))) {
                            result.add(new Source(snapshot, request.path("arguments").get("root"), profile, ordinal)); break;
                        }
                    }
                }
                return List.copyOf(result);
            }
        }
    }
}
