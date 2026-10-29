package org.xar.ck3.control.contracts.semantic;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;

/** Original Python producer differential; absence of its source/configuration is a failure, never a skip. */
final class NativeActiveEventTest {
    @TempDir Path temporary;
    private static final ObjectMapper WIRE = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final String EVENT_SHA = "876d69c1efa7948ebaa157782a688caeeab7954dc550e06dfc8afff1cc5e8970";
    private static final String ORIGINAL = """
        import base64,hashlib,json,runpy,sys
        from pathlib import Path
        native=Path(sys.argv[1])
        if hashlib.sha256(native.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('original native producer source drift')
        source=native.with_name('event_contract.py')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=sys.argv[3]: raise RuntimeError('original active_event source drift')
        normalize=runpy.run_path(str(source))['normalize_active_event']
        rows=[]
        for case in json.loads(base64.b64decode(sys.argv[4])):
          try:
            result=normalize(case.get('input'),default_source=case['default_source'])
            rows.append({'id':case['id'],'ok':True,'value':result,
              'renormalized':normalize(result,default_source='different-unused-default')})
          except ValueError as error:
            rows.append({'id':case['id'],'ok':False,'error':type(error).__name__,'message':str(error)})
        sys.stdout.buffer.write(json.dumps(rows,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'))
        """;

    @Test void realOriginalProducerMatchesAllValidNullDefaultsOptionsAndStrategyBranches() throws Exception {
        JsonNode cases = json("""
            [
              {"id":"outer-missing","default_source":"native"},
              {"id":"outer-null","default_source":"native","input":null},
              {"id":"empty","default_source":"native","input":{}},
              {"id":"source-space","default_source":"native","input":{"source":" "}},
              {"id":"source-override","default_source":"","input":{"source":"native"}},
              {"id":"instance-zero","default_source":"native","input":{"instance_id":0}},
              {"id":"instance-big","default_source":"native","input":{"instance_id":1208925819614629174706176}},
              {"id":"title-kept","default_source":"native","input":{"title":"  Event title  "}},
              {"id":"title-zero-width","default_source":"native","input":{"title":"\\u200b"}},
              {"id":"null-fields","default_source":"native","input":{"instance_id":null,"title":null,"options":null,"option_count":null}},
              {"id":"count-fill","default_source":"native","input":{"instance_id":731,"option_count":3}},
              {"id":"count-zero","default_source":"native","input":{"option_count":0}},
              {"id":"options-empty","default_source":"native","input":{"options":[]}},
              {"id":"options-sequential","default_source":"native","input":{"options":[{},{}]}},
              {"id":"null-number-fallback","default_source":"native","input":{"options":[{"option_number":null}]}},
              {"id":"native-index-number","default_source":"native","input":{"option_count":3,"options":[{"index":2,"label":"third","enabled":false},{"index":0,"option_number":1,"visible_text":"first"}]}},
              {"id":"sparse-sort","default_source":"native","input":{"option_count":4,"options":[{"option_number":4},{"option_number":2}]}},
              {"id":"declared-null-count","default_source":"native","input":{"option_count":null,"options":[{}]}},
              {"id":"explicit-label-null","default_source":"native","input":{"options":[{"label":null,"visible_text":"ignored"}]}},
              {"id":"empty-label","default_source":"native","input":{"options":[{"label":""}]}},
              {"id":"visible-text","default_source":"native","input":{"options":[{"visible_text":"native label"}]}},
              {"id":"score-integer","default_source":"native","input":{"options":[{"strategy_score":1208925819614629174706176}]}},
              {"id":"score-decimal","default_source":"native","input":{"options":[{"strategy_score":-1.25}]}},
              {"id":"score-null-omitted","default_source":"native","input":{"options":[{"strategy_score":null}]}},
              {"id":"reasons-filter","default_source":"native","input":{"options":[{"strategy_reasons":["a",3,true,null,"",{},"a"]}]}},
              {"id":"reasons-empty","default_source":"native","input":{"options":[{"strategy_reasons":[]}]}},
              {"id":"reasons-not-array","default_source":"native","input":{"options":[{"strategy_reasons":"omit"}]}},
              {"id":"unknown-dropped","default_source":"native","input":{"unknown":{"raw":"kept only in original archive"},"options":[{"unknown":4}]}}
            ]
            """);
        JsonNode original = original(cases);
        assertEquals(cases.size(), original.size());
        for (int index = 0; index < cases.size(); index++) {
            JsonNode row = cases.get(index), expected = original.get(index);
            assertEquals(row.get("id"), expected.get("id"));
            assertTrue(expected.path("ok").booleanValue(), row.path("id").asText());
            JsonNode input = row.has("input") ? row.get("input") : MissingNode.getInstance();
            JsonNode preserved = input.deepCopy();
            JsonNode normalized = NativeActiveEvent.normalize(input, row.get("default_source").textValue());
            assertEquals(expected.get("value"), normalized, row.path("id").asText());
            assertEquals(preserved, input, "normalization must not edit archived original material");
            assertEquals(normalized, json(WIRE.writeValueAsBytes(normalized)));
            // The original is intentionally not globally idempotent: an unknown/null count
            // plus absent options becomes null/[] first, then zero/[] on its second pass.
            assertEquals(expected.get("renormalized"), NativeActiveEvent.normalize(normalized,
                    "different-unused-default"), row.path("id").asText());
        }
    }

    @Test void realOriginalProducerAndSharedNormalizerBothRejectWrongTypesAndInconsistentNativeOptions() throws Exception {
        JsonNode cases = WIRE.readTree("""
            [
              {"id":"array","default_source":"native","input":[]},
              {"id":"bool","default_source":"native","input":true},
              {"id":"integer","default_source":"native","input":1},
              {"id":"instance-bool","default_source":"native","input":{"instance_id":true}},
              {"id":"instance-float","default_source":"native","input":{"instance_id":1.0}},
              {"id":"instance-text","default_source":"native","input":{"instance_id":"1"}},
              {"id":"instance-negative","default_source":"native","input":{"instance_id":-1}},
              {"id":"title-empty","default_source":"native","input":{"title":""}},
              {"id":"title-blank","default_source":"native","input":{"title":" \\t"}},
              {"id":"title-nbsp","default_source":"native","input":{"title":"\\u00a0"}},
              {"id":"title-nel","default_source":"native","input":{"title":"\\u0085"}},
              {"id":"title-number","default_source":"native","input":{"title":2}},
              {"id":"source-null","default_source":"native","input":{"source":null}},
              {"id":"source-empty","default_source":"native","input":{"source":""}},
              {"id":"source-bool","default_source":"native","input":{"source":true}},
              {"id":"bad-default","default_source":"","input":{}},
              {"id":"options-object","default_source":"native","input":{"options":{}}},
              {"id":"option-null","default_source":"native","input":{"options":[null]}},
              {"id":"number-zero","default_source":"native","input":{"options":[{"option_number":0}]}},
              {"id":"number-bool","default_source":"native","input":{"options":[{"option_number":true}]}},
              {"id":"number-float","default_source":"native","input":{"options":[{"option_number":1.0}]}},
              {"id":"index-null","default_source":"native","input":{"options":[{"index":null}]}},
              {"id":"index-negative","default_source":"native","input":{"options":[{"index":-1}]}},
              {"id":"index-bool","default_source":"native","input":{"options":[{"index":false}]}},
              {"id":"index-float","default_source":"native","input":{"options":[{"index":0.0}]}},
              {"id":"index-number-disagree","default_source":"native","input":{"options":[{"index":1,"option_number":1}]}},
              {"id":"duplicate","default_source":"native","input":{"options":[{"option_number":1},{"index":0}]}},
              {"id":"duplicate-before-label","default_source":"native","input":{"options":[{"option_number":1},{"index":0,"label":3}]}},
              {"id":"label-number","default_source":"native","input":{"options":[{"label":3}]}},
              {"id":"visible-text-number","default_source":"native","input":{"options":[{"visible_text":3}]}},
              {"id":"enabled-null","default_source":"native","input":{"options":[{"enabled":null}]}},
              {"id":"enabled-integer","default_source":"native","input":{"options":[{"enabled":1}]}},
              {"id":"score-bool","default_source":"native","input":{"options":[{"strategy_score":true}]}},
              {"id":"score-text","default_source":"native","input":{"options":[{"strategy_score":"1"}]}},
              {"id":"count-bool","default_source":"native","input":{"option_count":true}},
              {"id":"count-float","default_source":"native","input":{"option_count":1.0}},
              {"id":"count-negative","default_source":"native","input":{"option_count":-1}},
              {"id":"count-too-small","default_source":"native","input":{"option_count":1,"options":[{"index":1}]}},
              {"id":"inferred-count-too-small","default_source":"native","input":{"options":[{"index":2}]}}
            ]
            """);
        assertTrue(WIRE.readTree(WIRE.writeValueAsBytes(cases)).get(4).path("input").path("instance_id").isFloatingPointNumber(),
                "float negative case must reach the original producer as a float");
        JsonNode original = original(cases);
        assertEquals(cases.size(), original.size());
        for (int index = 0; index < cases.size(); index++) {
            JsonNode row = cases.get(index), expected = original.get(index);
            assertFalse(expected.path("ok").booleanValue(), row.path("id").asText());
            assertEquals("ValueError", expected.path("error").textValue());
            IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                    () -> NativeActiveEvent.normalize(row.get("input"), row.get("default_source").textValue()), row.path("id").asText());
            assertEquals(expected.path("message").textValue(), error.getMessage(), row.path("id").asText());
        }
    }

    @Test void explicitNullAndMissingBranchesRetainTheOriginalJsonContractWithoutAliases() {
        assertSame(NullNode.getInstance(), NativeActiveEvent.normalize(MissingNode.getInstance(), null));
        assertSame(NullNode.getInstance(), NativeActiveEvent.normalize(NullNode.getInstance(), null));
        JsonNode absent = NativeActiveEvent.normalize(json("{}"), "native");
        assertTrue(absent.get("option_count").isNull());
        assertEquals(0, absent.get("options").size());
        JsonNode empty = NativeActiveEvent.normalize(json("{\"options\":[]}"), "native");
        assertEquals(0, empty.get("option_count").intValue());
        JsonNode nullLabel = NativeActiveEvent.normalize(json("{\"options\":[{\"label\":null,\"visible_text\":\"ignored\",\"strategy_score\":null,\"strategy_reasons\":null}]}"), "native");
        JsonNode option = nullLabel.get("options").get(0);
        assertTrue(option.get("label").isNull());
        assertFalse(option.has("visible_text"));
        assertFalse(option.has("strategy_score"));
        assertFalse(option.has("strategy_reasons"));
        assertThrows(IllegalArgumentException.class, () -> NativeActiveEvent.normalize(json("{\"source\":null}"), "native"));
        assertThrows(IllegalArgumentException.class, () -> json("{\"instance_id\":1,\"instance_id\":2}"));
    }

    @Test void originalRawFloatInputsMatchPythonBinary64BeforeTheSingleLeafWithoutRoundingIntegerIds() throws Exception {
        byte[] rawCases = """
            [
              {"id":"long-decimal","default_source":"native","input":{"instance_id":1208925819614629174706176,"options":[{"strategy_score":1.2345678901234567890123456789}]}},
              {"id":"negative-zero","default_source":"native","input":{"options":[{"strategy_score":-0.0}]}},
              {"id":"large-exponent","default_source":"native","input":{"options":[{"strategy_score":1e23}]}},
              {"id":"subnormal","default_source":"native","input":{"options":[{"strategy_score":1e-320}]}}
            ]
            """.getBytes(StandardCharsets.UTF_8);
        // This is the agreed native raw interop input domain: original floats are binary64,
        // while integer identity tokens remain BigInteger. The semantic leaf is not a second serializer.
        JsonNode cases = WIRE.readTree(rawCases), expected = WIRE.readTree(originalRaw(rawCases));
        for (int index = 0; index < cases.size(); index++) {
            JsonNode row = cases.get(index), result = expected.get(index);
            assertTrue(result.path("ok").booleanValue());
            JsonNode normalized = NativeActiveEvent.normalize(row.get("input"), row.get("default_source").textValue());
            assertEquals(result.get("value"), normalized, row.path("id").asText());
            assertEquals(result.get("renormalized"), NativeActiveEvent.normalize(normalized, "different-unused-default"));
            assertEquals(normalized, WIRE.readTree(WIRE.writeValueAsBytes(normalized)));
        }
        JsonNode originalIdentity = cases.get(0).get("input").get("instance_id");
        JsonNode actualIdentity = NativeActiveEvent.normalize(cases.get(0).get("input"), "native").get("instance_id");
        assertTrue(actualIdentity.isIntegralNumber());
        assertEquals(originalIdentity.bigIntegerValue(), actualIdentity.bigIntegerValue());
        JsonNode negativeZero = NativeActiveEvent.normalize(cases.get(1).get("input"), "native")
                .get("options").get(0).get("strategy_score");
        assertEquals(Long.MIN_VALUE, Double.doubleToRawLongBits(negativeZero.doubleValue()));
    }

    private JsonNode original(JsonNode cases) throws Exception {
        return json(originalRaw(WIRE.writeValueAsBytes(cases)));
    }
    private byte[] originalRaw(byte[] rawCases) throws Exception {
        String python = required("xar.native.producer.python"), source = required("xar.native.producer.source"), sha = required("xar.native.producer.sha256");
        if (!Path.of(python).isAbsolute() || !Path.of(source).isAbsolute() || !sha.matches("[a-f0-9]{64}"))
            throw new IllegalStateException("NOT EXECUTED: pinned original producer fixture required");
        Path output = temporary.resolve("active-event-original.json"), error = temporary.resolve("active-event-original.stderr");
        var process = new ProcessBuilder(python, "-X", "utf8", "-c", ORIGINAL, source, sha, EVENT_SHA,
                Base64.getEncoder().encodeToString(rawCases))
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if (!process.waitFor(20, TimeUnit.SECONDS)) {
            process.destroyForcibly(); throw new IOException("original active_event producer timeout");
        }
        if (process.exitValue() != 0) throw new IOException("original active_event producer failed: " + Files.readString(error, StandardCharsets.UTF_8));
        return Files.readAllBytes(output);
    }
    private static String required(String key) {
        String value = System.getProperty(key);
        if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: required original fixture property missing: " + key);
        return value;
    }
    private static JsonNode json(String value) { return json(value.getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode json(byte[] value) { return StrictJson.parse(value); }
}
