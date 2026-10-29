package org.xar.ck3.control.wave2.runtime.performancewindows;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ContractViolationException;

final class PerformanceWindowsTest {
    private static final ObjectMapper WRITER = new ObjectMapper();

    @Test void matchesCompleteUnchangedOriginalProducerOutputsAndActualRejections() throws IOException {
        JsonNode golden = golden(); assertEquals(7, golden.get("cases").size());
        int accepted = 0;
        for (JsonNode sample : golden.get("cases")) {
            List<HistoricalPerformanceWindows.SourceInput> sources = baselineSources();
            for (JsonNode override : sample.get("overrides")) {
                replace(sources, HistoricalPerformanceWindows.SourceRole.valueOf(override.get("role").textValue()),
                        override.get("raw_json").textValue().getBytes(StandardCharsets.UTF_8));
            }
            if (sample.get("accepted").booleanValue()) {
                JsonNode expected = sample.get("expected");
                HistoricalPerformanceWindows.Context context = context(expected);
                var projection = HistoricalPerformanceWindows.project(PerformanceWindowsCodec.decode(context, sources));
                numericJson(expected, PerformanceWindowsCodec.toJson(projection), sample.get("name").textValue());
                numericJson(expected, PerformanceWindowsCodec.parse(PerformanceWindowsCodec.encode(projection)), "roundtrip");
                accepted++;
            } else {
                assertThrows(ContractViolationException.class, () -> HistoricalPerformanceWindows.project(
                        PerformanceWindowsCodec.decode(baselineContext(), sources)), sample.get("name").textValue());
            }
        }
        assertEquals(3, accepted);
    }

    @Test void rejectsRawFloatingBooleanStringNullAndNegativeIntegerTokens() throws IOException {
        for (String token : List.of("62.0", "true", "\"62\"", "null", "-1")) {
            List<HistoricalPerformanceWindows.SourceInput> sources = baselineSources();
            String original = new String(sources.get(0).bytes(), StandardCharsets.UTF_8);
            String changed = original.replace("\"turns\": 62,", "\"turns\": " + token + ",");
            assertNotEquals(original, changed, "raw-token fixture seam must match actual source");
            replace(sources, HistoricalPerformanceWindows.SourceRole.P49_SETTLED, changed.getBytes(StandardCharsets.UTF_8));
            assertThrows(ContractViolationException.class, () -> PerformanceWindowsCodec.decode(baselineContext(), sources));
        }
    }

    @Test void rejectsMissingRequiredFieldsAndWrongCounterOrDurationTypes() throws IOException {
        for (String field : List.of("game_days", "wall_seconds", "turns", "zero_date_turns", "auto_by_group")) {
            List<HistoricalPerformanceWindows.SourceInput> sources = mutated(HistoricalPerformanceWindows.SourceRole.P49_SETTLED,
                    root -> ((ObjectNode) root.get("5104-5165")).remove(field));
            assertThrows(ContractViolationException.class, () -> PerformanceWindowsCodec.decode(baselineContext(), sources));
        }
        for (JsonNode invalid : List.of(PerformanceWindowsCodec.parse("true".getBytes(StandardCharsets.UTF_8)),
                PerformanceWindowsCodec.parse("\"10\"".getBytes(StandardCharsets.UTF_8)))) {
            List<HistoricalPerformanceWindows.SourceInput> sources = mutated(HistoricalPerformanceWindows.SourceRole.P49_SETTLED,
                    root -> ((ObjectNode) root.get("5104-5165").get("auto_by_group").get("army_query")).set("auto_seconds", invalid));
            assertThrows(ContractViolationException.class, () -> PerformanceWindowsCodec.decode(baselineContext(), sources));
        }
    }

    @Test void extensibleEvidenceContainersAreProjectedAndCopiedFieldsRemainExact() throws IOException {
        List<HistoricalPerformanceWindows.SourceInput> sources = mutated(HistoricalPerformanceWindows.SourceRole.P49_SETTLED,
                root -> {
                    root.putObject("future_source_extension").put("metadata", "allowed");
                    ((ObjectNode) root.get("5104-5165").get("auto_by_group").get("army_query"))
                            .putObject("future_group_extension").put("token", "retained");
                });
        JsonNode result = project(sources);
        assertEquals("retained", result.get("P49_settled").get("zero_date_groups").get("army_query")
                .get("future_group_extension").get("token").textValue());
        assertFalse(result.has("future_source_extension"));
    }

    @Test void missingNullAndExplicitMachineLabelsRemainDifferent() throws IOException {
        JsonNode baseline = project(baselineSources());
        assertEquals("unknown", baseline.get("historical_window").get("source_machine_ids").get("P49_settled").textValue());
        List<HistoricalPerformanceWindows.SourceInput> explicitNull = mutated(HistoricalPerformanceWindows.SourceRole.P49_SETTLED,
                root -> root.putNull("machine_id"));
        assertTrue(project(explicitNull).get("historical_window").get("source_machine_ids").get("P49_settled").isNull());
        List<HistoricalPerformanceWindows.SourceInput> explicitName = mutated(HistoricalPerformanceWindows.SourceRole.P49_SETTLED,
                root -> root.put("machine_id", "other-source-machine"));
        assertEquals("other-source-machine", project(explicitName).get("historical_window").get("source_machine_ids")
                .get("P49_settled").textValue());
        var context = baselineContext();
        var different = new HistoricalPerformanceWindows.Context("different-executing-machine", context.observedUtc(), context.reviewUtc());
        JsonNode result = PerformanceWindowsCodec.toJson(HistoricalPerformanceWindows.project(
                PerformanceWindowsCodec.decode(different, baselineSources())));
        assertFalse(result.get("historical_window").get("P63_same_as_executing_machine").booleanValue());
    }

    @Test void nestedStagesAreSeparateAndNoSavedPerformanceGoalIsInvented() throws IOException {
        JsonNode result = project(baselineSources()); JsonNode p49 = result.get("P49_settled");
        assertEquals(134.92461, p49.get("wall_seconds").doubleValue());
        assertEquals(29.275382, p49.get("plan_unique_wall_seconds").doubleValue());
        assertFalse(result.get("P63").get("same_state_AB").booleanValue());
        assertFalse(result.get("source_candidate").get("live_accepted").booleanValue());
        assertTrue(result.get("source_candidate").get("predicted_seconds_saved").isNull());
        assertFalse(result.has("phase_goal_reached_in_window")); assertFalse(result.has("saved_day_credit"));
        for (JsonNode sample : golden().get("cases")) {
            if (sample.get("name").textValue().equals("all_zero_day_groups")) {
                assertEquals(BigInteger.ZERO, sample.get("expected").get("P49_settled").get("game_days").bigIntegerValue());
                assertEquals(0.0, sample.get("expected").get("P49_settled").get("progress_auto_seconds").doubleValue());
                assertTrue(sample.get("expected").get("P49_settled").get("wall_seconds").doubleValue() > 0);
                assertFalse(sample.get("expected").has("phase_goal_reached_in_window"));
            }
        }
    }

    @Test void rejectsDuplicateKeysDuplicateStagesRolesAndInvalidUtf8() throws IOException {
        assertThrows(ContractViolationException.class, () -> PerformanceWindowsCodec.parse("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> PerformanceWindowsCodec.parse(new byte[] {(byte) 0xc3, 0x28}));
        List<HistoricalPerformanceWindows.SourceInput> duplicates = baselineSources(); duplicates.set(1, duplicates.get(0));
        assertThrows(ContractViolationException.class, () -> PerformanceWindowsCodec.decode(baselineContext(), duplicates));
        List<HistoricalPerformanceWindows.SourceInput> stages = mutated(HistoricalPerformanceWindows.SourceRole.P49_STAGES,
                root -> ((com.fasterxml.jackson.databind.node.ArrayNode) root.get("stages")).add(root.get("stages").get(0).deepCopy()));
        assertThrows(ContractViolationException.class, () -> PerformanceWindowsCodec.decode(baselineContext(), stages));
    }

    @Test void rawSourceReferencesAndPublicPayloadsAreDefensivelyCopied() throws IOException {
        List<HistoricalPerformanceWindows.SourceInput> sources = baselineSources(); byte[] original = sources.get(0).bytes();
        var stored = new HistoricalPerformanceWindows.SourceInput(HistoricalPerformanceWindows.SourceRole.P49_SETTLED, original);
        original[0] = 0; assertNotEquals(0, stored.bytes()[0]);
        var equalBytes = new HistoricalPerformanceWindows.SourceInput(stored.role(), stored.bytes());
        assertEquals(stored, equalBytes); assertEquals(stored.hashCode(), equalBytes.hashCode());
        var input = PerformanceWindowsCodec.decode(baselineContext(), sources);
        String originalHash = input.sources().get(0).sha256(); sources.get(0).bytes()[0] = 0;
        assertEquals(originalHash, input.sources().get(0).sha256());
        ObjectNode rate = input.r6().sourceValue(); rate.put("actual_days", -1);
        assertEquals(13.0, input.r6().sourceValue().get("actual_days").doubleValue());
        ObjectNode group = input.settled().groups().get("army_query").sourceValue(); group.put("count", true);
        assertEquals(19, input.settled().groups().get("army_query").sourceValue().get("count").intValue());
    }

    @Test void readsTheActualFourSourcePathsAndFailsMissingOrOversizedInputs(@TempDir Path root) throws IOException {
        Path evidence = root.resolve("docs/ck3-native-ai/evidence"); Files.createDirectories(evidence);
        for (HistoricalPerformanceWindows.SourceInput source : baselineSources()) {
            Files.write(evidence.resolve(source.role().filename()), source.bytes());
        }
        var read = HistoricalPerformanceSourceReader.read(root);
        numericJson(project(baselineSources()), project(read), "read-only adapter");
        numericJson(project(baselineSources()), PerformanceWindowsCodec.parse(
                HistoricalPerformanceSourceReader.project(root, baselineContext())), "complete Java producer entry");
        Files.write(evidence.resolve(HistoricalPerformanceWindows.SourceRole.P49_SETTLED.filename()),
                new byte[HistoricalPerformanceWindows.SOURCE_MAX_BYTES + 1]);
        assertThrows(ContractViolationException.class, () -> HistoricalPerformanceSourceReader.read(root));
        Files.delete(evidence.resolve(HistoricalPerformanceWindows.SourceRole.P49_SETTLED.filename()));
        assertThrows(ContractViolationException.class, () -> HistoricalPerformanceSourceReader.read(root));
    }

    private static List<HistoricalPerformanceWindows.SourceInput> baselineSources() throws IOException {
        List<HistoricalPerformanceWindows.SourceInput> inputs = new ArrayList<>();
        for (HistoricalPerformanceWindows.SourceRole role : HistoricalPerformanceWindows.SourceRole.values()) {
            inputs.add(new HistoricalPerformanceWindows.SourceInput(role, resource("sources/" + role.filename())));
        }
        return inputs;
    }
    private static List<HistoricalPerformanceWindows.SourceInput> mutated(HistoricalPerformanceWindows.SourceRole role,
                                                                          Consumer<ObjectNode> mutation) throws IOException {
        List<HistoricalPerformanceWindows.SourceInput> sources = baselineSources();
        for (HistoricalPerformanceWindows.SourceInput source : List.copyOf(sources)) {
            if (source.role() == role) {
                ObjectNode value = (ObjectNode) PerformanceWindowsCodec.parse(source.bytes()); mutation.accept(value);
                replace(sources, role, WRITER.writeValueAsBytes(value));
            }
        }
        return sources;
    }
    private static void replace(List<HistoricalPerformanceWindows.SourceInput> inputs,
                                HistoricalPerformanceWindows.SourceRole role, byte[] bytes) {
        for (int index = 0; index < inputs.size(); index++) {
            if (inputs.get(index).role() == role) { inputs.set(index, new HistoricalPerformanceWindows.SourceInput(role, bytes)); return; }
        }
        throw new IllegalArgumentException("source role absent");
    }
    private static JsonNode project(List<HistoricalPerformanceWindows.SourceInput> sources) throws IOException {
        return PerformanceWindowsCodec.toJson(HistoricalPerformanceWindows.project(PerformanceWindowsCodec.decode(baselineContext(), sources)));
    }
    private static HistoricalPerformanceWindows.Context baselineContext() throws IOException { return context(golden().get("cases").get(0).get("expected")); }
    private static HistoricalPerformanceWindows.Context context(JsonNode expected) {
        return new HistoricalPerformanceWindows.Context(expected.get("machine_id").textValue(), expected.get("observed_utc").textValue(),
                expected.get("storage").get("record_review_at_utc").textValue());
    }
    private static JsonNode golden() throws IOException { return PerformanceWindowsCodec.parse(resource("producer-golden.json")); }
    private static byte[] resource(String name) throws IOException {
        try (InputStream stream = PerformanceWindowsTest.class.getResourceAsStream("/performancewindows/" + name)) {
            if (stream == null) { throw new IOException("required committed performance-window resource missing; no skip: " + name); }
            return stream.readAllBytes();
        }
    }
    private static void numericJson(JsonNode expected, JsonNode actual, String context) {
        if (expected.isNumber() && actual.isNumber()) {
            if (expected.isIntegralNumber() && actual.isIntegralNumber()) { assertEquals(expected.bigIntegerValue(), actual.bigIntegerValue(), context); }
            else { assertEquals(expected.doubleValue(), actual.doubleValue(), context); }
        } else if (expected.isObject() && actual.isObject()) {
            assertEquals(expected.size(), actual.size(), context);
            expected.properties().forEach(field -> {
                assertTrue(actual.has(field.getKey()), context + "/" + field.getKey());
                numericJson(field.getValue(), actual.get(field.getKey()), context + "/" + field.getKey());
            });
        } else if (expected.isArray() && actual.isArray()) {
            assertEquals(expected.size(), actual.size(), context);
            for (int index = 0; index < expected.size(); index++) { numericJson(expected.get(index), actual.get(index), context + "/" + index); }
        } else { assertEquals(expected, actual, context); }
    }
}
