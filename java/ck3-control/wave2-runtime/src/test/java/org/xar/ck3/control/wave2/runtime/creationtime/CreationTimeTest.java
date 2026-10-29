package org.xar.ck3.control.wave2.runtime.creationtime;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class CreationTimeTest {
    private record Corpus(JsonNode header, List<JsonNode> vectors) { }
    @TestFactory
    Stream<DynamicTest> actualOriginalProducerAndConsumerCalls() throws IOException {
        return corpus().vectors().stream().map(vector -> DynamicTest.dynamicTest(vector.path("ordinal") + " " + vector.path("test_case").asText(), () -> {
            byte[] request = vector.path("input").textValue().getBytes(StandardCharsets.UTF_8);
            if (vector.path("expected_kind").asText().equals("invalid_contract")) {
                assertThrows(ContractViolationException.class, () -> CreationTimeCodec.evaluate(request));
            } else {
                byte[] actual = CreationTimeCodec.evaluate(request);
                assertArrayEquals(StrictJson.canonical(vector.get("expected")), actual);
                assertArrayEquals(actual, StrictJson.canonical(StrictJson.parse(actual)));
            }
        }));
    }
    @Test
    void committedCaptureHasActualFullConsumerSuitesAndNoSkippedPass() throws IOException {
        Corpus corpus = corpus(); JsonNode h = corpus.header();
        assertEquals("g2.wave2-runtime.creationtime-golden/v1", h.path("schema").asText());
        assertTrue(h.path("original_tests").intValue() >= 11); assertEquals(0, h.path("skips").intValue());
        assertEquals(3, h.path("scope").size()); assertEquals(7, h.path("source_sha256").size());
        h.path("source_sha256").elements().forEachRemaining(value -> assertTrue(value.textValue().matches("[0-9a-f]{64}")));
        StrictJson.text(h.get("machine_id")); StrictJson.text(h.get("observed_at_utc"));
        assertEquals(0, h.path("native_game_rpc_count").intValue()); assertFalse(h.path("live_adoption").booleanValue());
        assertEquals(corpus.vectors().size(), h.path("vector_count").intValue());
        Set<String> operations = new HashSet<>(); int ordinal = 0;
        for (JsonNode vector : corpus.vectors()) { assertEquals(++ordinal, vector.path("ordinal").intValue()); operations.add(StrictJson.parse(vector.path("input").textValue().getBytes(StandardCharsets.UTF_8)).path("operation").asText()); }
        assertEquals(Set.of("process_creation_utc", "same_process_creation_time"), operations);
    }
    @Test
    void originalEvidenceIsRetainedWhileNormalizedInstantComparesEqual() {
        String raw = "\u0085 20260822090033.870978+480\u3000";
        var first = ProcessCreationTime.parse(raw); var second = ProcessCreationTime.parse("2026-08-22T01:00:33.8709780Z");
        assertEquals(raw, first.original()); assertEquals(first, second); assertEquals(first.hashCode(), second.hashCode());
        assertEquals(Instant.parse("2026-08-22T01:00:33.870978Z"), first.instant());
        assertEquals("2026-08-22T01:00:33.870978+00:00", first.utcIsoformat());
        assertEquals("2026-08-22T09:00:33+00:00", ProcessCreationTime.parse("20260822090033.000000+000").utcIsoformat());
    }
    @Test
    void noHundredNanosecondTruncationOrMalformedInequalityCanGrantReplacedProcess() {
        String dmtf = "20260822090033.870978+480";
        assertEquals(ProcessCreationTime.Comparison.SAME, ProcessCreationTime.compare(dmtf, "2026-08-22T01:00:33.8709780Z"));
        assertEquals(ProcessCreationTime.Comparison.DIFFERENT, ProcessCreationTime.compare(dmtf, "2026-08-22T01:00:33.8709790Z"));
        for (String invalid : List.of("2026-08-22T01:00:33.8709781Z", "historic-process-marker", "20260822090033.870978+841", "20230229090033.870978+480")) {
            assertThrows(IllegalArgumentException.class, () -> ProcessCreationTime.parse(invalid));
            assertEquals(ProcessCreationTime.Comparison.UNAVAILABLE, ProcessCreationTime.compare(dmtf, invalid));
            assertFalse(ProcessCreationTime.same(invalid, invalid));
        }
        assertEquals(ProcessCreationTime.Comparison.UNAVAILABLE, ProcessCreationTime.compare(null, dmtf));
    }
    @Test
    void pythonDatetimeYearBoundaryIncludesOffsetOverflow() {
        assertEquals("0001-01-01T00:00:00+00:00", ProcessCreationTime.parse("00010101000000.000000+000").utcIsoformat());
        assertEquals("9999-12-31T23:59:59.999999+00:00", ProcessCreationTime.parse("99991231235959.999999-000").utcIsoformat());
        assertThrows(IllegalArgumentException.class, () -> ProcessCreationTime.parse("00010101000000.000000+001"));
        assertThrows(IllegalArgumentException.class, () -> ProcessCreationTime.parse("99991231235959.999999-001"));
    }
    @Test
    void strictWrapperRejectsFieldsUtf8AndWrongParseValueType() {
        String prefix = "{\"schema\":\"" + CreationTimeCodec.SCHEMA + "\",\"operation\":\"process_creation_utc\",\"arguments\":";
        for (String args : List.of("{}", "{\"value\":null}", "{\"value\":true}", "{\"value\":1.0}", "{\"value\":[]}", "{\"value\":\"x\",\"extra\":0}")) {
            assertThrows(ContractViolationException.class, () -> CreationTimeCodec.evaluate((prefix + args + "}").getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(ContractViolationException.class, () -> CreationTimeCodec.evaluate(new byte[] {(byte) 0xff}));
        assertThrows(ContractViolationException.class, () -> CreationTimeCodec.evaluate((prefix + "{\"value\":\"x\",\"value\":\"y\"}}").getBytes(StandardCharsets.UTF_8)));
        byte[] raw = ("{\"schema\":\"" + CreationTimeCodec.SCHEMA + "\",\"operation\":\"same_process_creation_time\",\"arguments\":{\"first\":null,\"second\":true}}").getBytes(StandardCharsets.UTF_8);
        assertFalse(StrictJson.parse(CreationTimeCodec.evaluate(raw)).path("same").booleanValue());
        assertThrows(ContractViolationException.class, () -> CreationTimeCodec.evaluate((new String(raw, StandardCharsets.UTF_8) + "null").getBytes(StandardCharsets.UTF_8)));
    }
    private static Corpus corpus() throws IOException {
        try (InputStream input = CreationTimeTest.class.getResourceAsStream("/creationtime/original-v1.jsonl.gz")) {
            if (input == null) { throw new AssertionError("committed actual original corpus missing; not a skipped pass"); }
            try (GZIPInputStream gzip = new GZIPInputStream(input)) {
                byte[] raw = gzip.readNBytes(2 * 1024 * 1024 + 1); assertTrue(raw.length <= 2 * 1024 * 1024);
                String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
                String[] lines = text.split("\n", -1); assertEquals("", lines[lines.length - 1]);
                List<JsonNode> vectors = new ArrayList<>(); for (int i = 1; i < lines.length - 1; i++) { vectors.add(StrictJson.parse(lines[i].getBytes(StandardCharsets.UTF_8))); }
                return new Corpus(StrictJson.parse(lines[0].getBytes(StandardCharsets.UTF_8)), List.copyOf(vectors));
            }
        }
    }
}
