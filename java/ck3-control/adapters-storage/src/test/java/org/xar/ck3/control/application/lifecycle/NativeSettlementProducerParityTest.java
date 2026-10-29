package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Random;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;

/** Executes the unchanged pinned original producer; no hand-authored oracle, runtime fallback or Game submission. */
final class NativeSettlementProducerParityTest {
    @TempDir Path temporary;
    private static final String SOURCE_SHA = "647d7f558a18326682817f53d55cbf600ced2754b72b6fdc84d6244c807c6bbd";
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .streamReadConstraints(StreamReadConstraints.builder().maxNumberLength(100_000).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final String ORIGINAL = """
        import hashlib,json,runpy,struct,sys
        from pathlib import Path
        anchor=Path(sys.argv[1]); source=anchor.with_name('settlement_contract.py')
        if hashlib.sha256(anchor.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('native producer anchor drift')
        raw=source.read_bytes()
        if len(raw)!=7694 or hashlib.sha256(raw).hexdigest()!=sys.argv[3]: raise RuntimeError('settlement producer drift')
        producer=runpy.run_path(str(source))['normalize_one_life_settlement']
        rows=[]
        for original in json.loads(Path(sys.argv[4]).read_bytes()):
          try:
            value=producer(original)
          except (ValueError,OverflowError):
            rows.append({'ok':False}); continue
          kinds={}
          if isinstance(value,dict) and value.get('ready') is True:
            for field in ('final_score','score_before_reject'):
              number=value[field]
              kinds[field]={'kind':'int' if type(number) is int else 'float',
                'bits':None if type(number) is int else struct.pack('>d',number).hex()}
          rows.append({'ok':True,'value':value,'kinds':kinds})
        if source.read_bytes()!=raw: raise RuntimeError('settlement producer changed during execution')
        if hashlib.sha256(anchor.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('native producer anchor changed')
        sys.stdout.buffer.write(json.dumps(rows,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'))
        """;

    @Test void originalProducerToSharedLowerAndDeathAdapterPreservesExactJsonTypes() throws Exception {
        ArrayNode inputs = JSON.createArrayNode(); inputs.addNull(); inputs.add(false); inputs.add(1); inputs.add("ready"); inputs.addArray();
        inputs.add(JSON.createObjectNode().put("ready", false));
        inputs.add(JSON.createObjectNode().put("ready", 0).putNull("commit_serial").put("final_score", "ignored while pending"));
        inputs.add(JSON.createObjectNode().put("ready", 0).put("commit_serial", new BigInteger("18446744073709551616")));
        inputs.add(ready()); inputs.add(ready().put("ready", 1).put("record_written", 1).put("outer_extension", true));
        inputs.add(ready().put("record_candidate", 0).put("old_record", 5).put("record_delta", -5).put("record_written", false));
        for (String field : List.of("ready", "commit_serial", "source_character_id", "final_score", "score_before_reject", "record_candidate",
                "old_record", "record_delta", "blessing_count", "refusal_count", "contract_progress", "record_written")) {
            var missing = ready(); missing.remove(field); inputs.add(missing);
            inputs.add(ready().putNull(field));
        }
        for (String field : List.of("commit_serial", "source_character_id", "record_candidate", "old_record", "record_delta", "blessing_count", "refusal_count", "contract_progress")) {
            inputs.add(ready().put(field, true)); inputs.add(ready().put(field, 1.0)); inputs.add(ready().put(field, "1"));
        }
        for (String field : List.of("ready", "record_written")) {
            inputs.add(ready().put(field, 1.0)); inputs.add(ready().put(field, 2)); inputs.add(ready().put(field, "true"));
        }
        inputs.add(ready().put("commit_serial", 2)); inputs.add(ready().put("record_delta", 2));
        inputs.add(ready().put("record_candidate", 4).put("record_delta", 0));
        for (String field : List.of("source_character_id", "record_candidate", "old_record", "blessing_count", "refusal_count", "contract_progress")) inputs.add(ready().put(field, -1));
        for (JsonNode score : scores()) { var row = ready(); row.set("final_score", score); row.set("score_before_reject", score.deepCopy()); inputs.add(row); }
        assertOriginal(inputs);
    }

    @Test void unchangedOriginalProducerDecidesRationalNearestEvenAcrossNormalAndSubnormalRange() throws Exception {
        ArrayNode rows = JSON.createArrayNode(); var random = new Random(0x5e771eL);
        for (int index = 0; index < 180; index++) {
            BigInteger numerator = new BigInteger(1 + random.nextInt(2200), random).add(BigInteger.ONE);
            if (random.nextBoolean()) numerator = numerator.negate();
            BigInteger denominator = new BigInteger(1 + random.nextInt(2200), random).add(BigInteger.ONE);
            var row = ready(); row.set("final_score", fixed(numerator, denominator)); rows.add(row);
        }
        assertOriginal(rows);
    }

    @Test void adapterNormalizedConsumerRetainsSourceFloatLaneAndDefensivelyOwnsItsBytes() {
        var raw = ready(); raw.set("final_score", fixed(BigInteger.ONE.shiftLeft(53).add(BigInteger.ONE), BigInteger.ONE.shiftLeft(53)));
        raw.set("score_before_reject", fixed(BigInteger.ONE.negate(), BigInteger.ONE.shiftLeft(1075)));
        var normalized = NativeOneLifeSettlement.normalize(raw);
        var ready = DeathSettlement.fromNormalized(normalized).orElseThrow();
        assertTrue(ready.scoreJson().isFloatingPointNumber()); assertEquals(1.0, ready.scoreJson().doubleValue());
        assertEquals(Long.MIN_VALUE, Double.doubleToRawLongBits(ready.normalizedJson().get("score_before_reject").doubleValue()));
        byte[] exposed = ready.normalized(); exposed[0] = '!';
        assertEquals(normalized, ready.normalizedJson());
        assertThrows(IllegalArgumentException.class, () -> new DeathSettlement.Ready(ready.sourceCharacterId(), ready.finalScore().add(java.math.BigDecimal.ONE),
                ready.recordCandidate(), ready.recordWritten(), ready.normalized()));
        assertTrue(DeathSettlement.fromNormalized(NullNode.instance).isEmpty());
        assertTrue(DeathSettlement.fromNormalized(NativeOneLifeSettlement.normalize(JSON.createObjectNode().put("ready", false))).isEmpty());
        assertThrows(IllegalArgumentException.class, () -> DeathSettlement.fromNormalized(raw));
    }

    private void assertOriginal(ArrayNode inputs) throws Exception {
        JsonNode expected = original(inputs); assertEquals(inputs.size(), expected.size());
        for (int index = 0; index < inputs.size(); index++) {
            JsonNode input = inputs.get(index), oracle = expected.get(index); final int ordinal = index;
            if (!oracle.get("ok").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> NativeOneLifeSettlement.normalize(input), "original rejection row " + ordinal);
                assertThrows(IllegalArgumentException.class, () -> DeathSettlement.normalize(input), "Death raw rejection row " + ordinal);
                continue;
            }
            var state = NativeOneLifeSettlement.decodeNative(input); JsonNode actual = NativeOneLifeSettlement.encode(state);
            sameJson(oracle.get("value"), actual, "row " + index);
            sameJson(actual, NativeOneLifeSettlement.encode(NativeOneLifeSettlement.decodeNormalized(NativeOneLifeSettlement.encode(state, 1 << 20), 1 << 20)), "serde " + index);
            var adapter = DeathSettlement.normalize(input);
            if (state instanceof NativeOneLifeSettlement.Ready) {
                assertTrue(adapter.isPresent()); sameJson(actual, adapter.orElseThrow().normalizedJson(), "Death " + index);
                sameJson(actual, DeathSettlement.fromNormalized(actual).orElseThrow().normalizedJson(), "SEM " + index);
                for (String field : List.of("final_score", "score_before_reject")) {
                    JsonNode score = actual.get(field), kind = oracle.get("kinds").get(field);
                    assertEquals(score.isIntegralNumber() ? "int" : "float", kind.get("kind").textValue());
                    if (score.isFloatingPointNumber()) assertEquals(kind.get("bits").textValue(), HexFormat.of().toHexDigits(Double.doubleToRawLongBits(score.doubleValue())));
                }
            } else assertTrue(adapter.isEmpty());
        }
    }

    private JsonNode original(ArrayNode inputs) throws Exception {
        Path python = Path.of(required("xar.native.producer.python")), anchor = Path.of(required("xar.native.producer.source"));
        String anchorSha = required("xar.native.producer.sha256");
        if (!python.isAbsolute() || !anchor.isAbsolute() || !anchorSha.matches("[a-f0-9]{64}")) throw new IllegalStateException("NOT EXECUTED: explicit pinned original fixture required");
        assertEquals(anchorSha, sha(Files.readAllBytes(anchor)), "actual original native producer anchor drift");
        Path source = anchor.resolveSibling("settlement_contract.py"); byte[] retained = Files.readAllBytes(source);
        assertEquals(7694, retained.length); assertEquals(SOURCE_SHA, sha(retained));
        Path request = temporary.resolve("settlement-input.json"), output = temporary.resolve("settlement-original.json"), error = temporary.resolve("settlement-original.stderr");
        Files.write(request, JSON.writeValueAsBytes(inputs));
        var process = new ProcessBuilder(python.toString(), "-X", "utf8", "-c", ORIGINAL, anchor.toString(), anchorSha, SOURCE_SHA, request.toString())
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original settlement producer timeout"); }
        if (process.exitValue() != 0) throw new IOException("original settlement producer failed: " + Files.readString(error, StandardCharsets.UTF_8));
        assertArrayEquals(retained, Files.readAllBytes(source)); assertEquals(anchorSha, sha(Files.readAllBytes(anchor)));
        return JSON.readTree(Files.readAllBytes(output));
    }
    private static List<JsonNode> scores() {
        var values = new ArrayList<JsonNode>();
        values.add(JSON.getNodeFactory().numberNode(1.0)); values.add(JSON.getNodeFactory().numberNode(-0.0));
        values.add(JSON.getNodeFactory().numberNode(1.5)); values.add(JSON.getNodeFactory().numberNode(1e30));
        values.add(JSON.getNodeFactory().numberNode(BigInteger.TEN.pow(400)));
        values.add(JSON.getNodeFactory().booleanNode(true)); values.add(JSON.getNodeFactory().textNode("1")); values.add(NullNode.instance);
        values.add(fixed(BigInteger.TEN.pow(400), BigInteger.ONE)); values.add(fixed(BigInteger.ONE, BigInteger.valueOf(3)));
        values.add(fixed(BigInteger.ONE.negate(), BigInteger.valueOf(3))); values.add(fixed(BigInteger.ONE, BigInteger.ZERO));
        values.add(fixed(BigInteger.ONE, BigInteger.ONE).put("extra", true)); values.add(JSON.createObjectNode().put("raw", true).put("scale", 1));
        values.add(JSON.createObjectNode().put("raw", 1).put("scale", 1.0)); values.add(JSON.createObjectNode().put("raw", 1));
        for (int offset : new int[]{1, 3, 5}) {
            values.add(fixed(BigInteger.ONE.shiftLeft(53).add(BigInteger.valueOf(offset)), BigInteger.ONE.shiftLeft(53)));
            values.add(fixed(BigInteger.valueOf(offset), BigInteger.ONE.shiftLeft(1075)));
            values.add(fixed(BigInteger.valueOf(-offset), BigInteger.ONE.shiftLeft(1075)));
        }
        values.add(fixed(BigInteger.ONE.shiftLeft(2200).add(BigInteger.ONE), BigInteger.valueOf(3)));
        return List.copyOf(values);
    }
    private static void sameJson(JsonNode expected, JsonNode actual, String location) {
        if (expected.isIntegralNumber()) { assertTrue(actual.isIntegralNumber(), location); assertEquals(expected.bigIntegerValue(), actual.bigIntegerValue(), location); }
        else if (expected.isFloatingPointNumber()) { assertTrue(actual.isFloatingPointNumber(), location); assertEquals(Double.doubleToRawLongBits(expected.doubleValue()), Double.doubleToRawLongBits(actual.doubleValue()), location); }
        else if (expected.isObject()) {
            assertTrue(actual.isObject(), location); var expectedKeys = new java.util.HashSet<String>(); var actualKeys = new java.util.HashSet<String>();
            expected.fieldNames().forEachRemaining(expectedKeys::add); actual.fieldNames().forEachRemaining(actualKeys::add); assertEquals(expectedKeys, actualKeys, location);
            expected.fields().forEachRemaining(field -> sameJson(field.getValue(), actual.get(field.getKey()), location + "/" + field.getKey()));
        } else assertEquals(expected, actual, location);
    }
    private static String sha(byte[] raw) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
    private static String required(String name) { String value = System.getProperty(name); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: missing original fixture " + name); return value; }
    private static ObjectNode fixed(BigInteger raw, BigInteger scale) { return JSON.createObjectNode().put("raw", raw).put("scale", scale); }
    private static ObjectNode ready() {
        return JSON.createObjectNode().put("ready", true).put("commit_serial", 1).put("source_character_id", 73)
                .put("final_score", 5).put("score_before_reject", 6).put("record_candidate", 5).put("old_record", 4).put("record_delta", 1)
                .put("blessing_count", 0).put("refusal_count", 0).put("contract_progress", 0).put("record_written", true);
    }
}
