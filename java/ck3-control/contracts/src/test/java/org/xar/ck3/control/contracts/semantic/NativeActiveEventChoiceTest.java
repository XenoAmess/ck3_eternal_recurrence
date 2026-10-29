package org.xar.ck3.control.contracts.semantic;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Executes the pinned original chooser only when Root runs this regression; no fixture absence skip. */
final class NativeActiveEventChoiceTest {
    @TempDir Path temporary;
    private static final ObjectMapper WIRE=new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final String EVENT_SHA="876d69c1efa7948ebaa157782a688caeeab7954dc550e06dfc8afff1cc5e8970";
    private static final String ORIGINAL="""
        import base64,hashlib,json,runpy,sys
        from pathlib import Path
        native=Path(sys.argv[1])
        if hashlib.sha256(native.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('original native producer source drift')
        source=native.with_name('event_contract.py')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=sys.argv[3]: raise RuntimeError('original event contract source drift')
        api=runpy.run_path(str(source)); rows=[]
        for case in json.loads(base64.b64decode(sys.argv[4])):
          try:
            value=case.get('input')
            if case.get('normalize'): value=api['normalize_active_event'](value,default_source='native')
            rows.append({'id':case['id'],'ok':True,'value':api['choose_event_option_number'](value)})
          except (ValueError,OverflowError) as error:
            rows.append({'id':case['id'],'ok':False,'error':type(error).__name__,'message':str(error)})
        sys.stdout.buffer.write(json.dumps(rows,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'))
        """;

    @Test void actualOriginalChooserMatchesRawTypesRankingTieBreakingAndNormalizedDefaults()throws Exception {
        ArrayNode cases=(ArrayNode)json("""
            [
             {"id":"missing"},{"id":"null","input":null},{"id":"boolean","input":true},{"id":"array","input":[]},
             {"id":"empty","input":{}},{"id":"null-options","input":{"options":null}},{"id":"object-options","input":{"options":{}}},
             {"id":"all-invalid","input":{"options":[null,true,{},1,{"enabled":1,"option_number":1},{"enabled":true,"option_number":true},{"enabled":true,"option_number":1.0},{"enabled":true,"option_number":0},{"enabled":true,"option_number":-1},{"enabled":true,"option_number":"1"}]}},
             {"id":"disabled-high","input":{"options":[{"enabled":false,"option_number":1,"strategy_score":500},{"enabled":true,"option_number":2,"strategy_score":-2}]}},
             {"id":"score-high","input":{"options":[{"enabled":true,"option_number":1,"strategy_score":2},{"enabled":true,"option_number":2,"strategy_score":3}]}},
             {"id":"equal-small-number","input":{"options":[{"enabled":true,"option_number":8,"strategy_score":2},{"enabled":true,"option_number":2,"strategy_score":2}]}},
             {"id":"negative-score","input":{"options":[{"enabled":true,"option_number":2,"strategy_score":-3},{"enabled":true,"option_number":1,"strategy_score":-2}]}},
             {"id":"invalid-score-zero","input":{"options":[{"enabled":true,"option_number":4,"strategy_score":true},{"enabled":true,"option_number":3,"strategy_score":"100"},{"enabled":true,"option_number":2,"strategy_score":{}},{"enabled":true,"option_number":1,"strategy_score":null}]}},
             {"id":"signed-zero","input":{"options":[{"enabled":true,"option_number":2,"strategy_score":0.0},{"enabled":true,"option_number":1,"strategy_score":-0.0}]}},
             {"id":"double-rounding-tie","input":{"options":[{"enabled":true,"option_number":2,"strategy_score":9007199254740993},{"enabled":true,"option_number":1,"strategy_score":9007199254740992}]}},
             {"id":"option-identity-big","input":{"options":[{"enabled":true,"option_number":1208925819614629174706176,"strategy_score":1}]}},
             {"id":"long-decimal","input":{"options":[{"enabled":true,"option_number":2,"strategy_score":0.123456789012345678901234567890},{"enabled":true,"option_number":1,"strategy_score":0.1234567890123456789}]}},
             {"id":"subnormal","input":{"options":[{"enabled":true,"option_number":2,"strategy_score":5e-324},{"enabled":true,"option_number":1,"strategy_score":0.0}]}},
             {"id":"normalized-count","normalize":true,"input":{"option_count":3}},
             {"id":"normalized-order","normalize":true,"input":{"option_count":2,"options":[{"option_number":2,"strategy_score":1.0},{"option_number":1,"strategy_score":2.0}]}},
             {"id":"normalized-empty","normalize":true,"input":{}},
             {"id":"normalized-enabled-null","normalize":true,"input":{"options":[{"enabled":null}]}}
            ]
            """);
        ObjectNode overflow=cases.addObject().put("id","integer-score-overflow");
        overflow.putObject("input").putArray("options").addObject().put("enabled",true).put("option_number",1).put("strategy_score",BigInteger.TEN.pow(400));
        JsonNode expected=original(cases); assertEquals(cases.size(),expected.size());
        for(int index=0;index<cases.size();index++) {
            JsonNode entry=cases.get(index),result=expected.get(index),input=entry.has("input")?entry.get("input"):MissingNode.getInstance();
            JsonNode retained=input.deepCopy();
            if(result.path("ok").booleanValue()) {
                JsonNode selectedInput=entry.path("normalize").asBoolean()?NativeActiveEvent.normalize(input,"native"):input;
                Optional<BigInteger> actual=NativeActiveEvent.chooseOptionNumber(selectedInput);
                Optional<BigInteger> wanted=result.get("value").isNull()?Optional.empty():Optional.of(result.get("value").bigIntegerValue());
                assertEquals(wanted,actual,entry.path("id").asText());
                assertEquals(actual,NativeActiveEvent.chooseOptionNumber(json(WIRE.writeValueAsBytes(selectedInput))),"JSON round trip must retain the original selected identity");
            } else if("OverflowError".equals(result.path("error").textValue())) {
                ArithmeticException error=assertThrows(ArithmeticException.class,()->NativeActiveEvent.chooseOptionNumber(input));
                assertEquals(result.path("message").textValue(),error.getMessage());
            } else {
                assertEquals("ValueError",result.path("error").textValue());
                var error=assertThrows(IllegalArgumentException.class,()->NativeActiveEvent.normalize(input,"native"));
                assertEquals(result.path("message").textValue(),error.getMessage());
            }
            assertEquals(retained,input,"original native material is immutable");
        }
    }
    private JsonNode original(JsonNode cases)throws Exception {
        String python=required("xar.native.producer.python"),source=required("xar.native.producer.source"),sha=required("xar.native.producer.sha256");
        if(!Path.of(python).isAbsolute()||!Path.of(source).isAbsolute()||!sha.matches("[a-f0-9]{64}"))throw new IllegalStateException("NOT EXECUTED: pinned original producer fixture required");
        Path output=temporary.resolve("event-choice-original.json"),error=temporary.resolve("event-choice-original.stderr");
        var process=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL,source,sha,EVENT_SHA,Base64.getEncoder().encodeToString(WIRE.writeValueAsBytes(cases)))
            .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original event chooser timeout");}
        if(process.exitValue()!=0)throw new IOException("original event chooser failed: "+Files.readString(error,StandardCharsets.UTF_8));
        return json(Files.readAllBytes(output));
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: required original fixture property missing: "+key);return value;}
    private static JsonNode json(String value)throws IOException{return json(value.getBytes(StandardCharsets.UTF_8));}
    private static JsonNode json(byte[] value)throws IOException{return WIRE.readTree(value);}
}
