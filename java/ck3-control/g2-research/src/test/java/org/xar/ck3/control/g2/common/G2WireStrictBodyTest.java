package org.xar.ck3.control.g2.common;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Shared production constructors and wire codec; these checks grant no domain or native qualification. */
class G2WireStrictBodyTest {
    private static final G2Source SOURCE=new G2Source("fixture-machine-01","2026-10-23T00:00:00Z",
        "1.20.0.4",new ExactRef("fixture/input.json",2,"a".repeat(64)));

    @Test void rejectsProducerPayloadWhitespaceBeforeTokenSpanCanLoseIt() {
        // Historical G2JavaClientProtocolTest supplied this padded object and accepted a changed result.
        for(String padding:List.of(" ","\t","\r","\n"," \n")) {
            for(String raw:List.of(padding+"{}","{}"+padding,padding+"{}"+padding)) {
                ProjectionJson payload=ProjectionJson.object(utf8(raw),8192);
                assertArrayEquals(utf8(raw),payload.bytes());
                G2Exception error=assertThrows(G2Exception.class,
                    ()->new G2Request("padded",Milestone.M0,SOURCE,payload));
                assertEquals(G2HttpError.Code.MALFORMED_REQUEST,error.code());
            }
        }
    }

    @Test void rejectsProducerResultWhitespaceForEveryJsonKind() {
        for(String value:List.of("{}","[]","null","true","false","1","1.2300","-0.0","\" \"")) {
            for(String raw:List.of(" "+value,value+"\n")) {
                ProjectionJson result=ProjectionJson.value(utf8(raw),8192);
                assertThrows(G2Exception.class,()->new G2Response("padded",Milestone.M0,SOURCE,result));
            }
        }
    }

    @Test void allEightMilestoneEnvelopesRetainBodyTokensAndSourceWithoutCanonicalization() {
        byte[] raw=utf8("{ \"float\" : 1.2300, \"negative_zero\":-0.0, \"exponent\":1e+2, "
            +"\"file_id\":\"18446744073709551615\",\"mtime_ns\":\"9223372036854775807\","
            +"\"present_null\":null,\"present_empty\":[],\"text\":\"  保留 \\t \" }");
        for(Milestone milestone:Milestone.values()) {
            G2Request produced=new G2Request("strict:"+milestone,milestone,SOURCE,ProjectionJson.object(raw,8192));
            byte[] requestBytes=G2Wire.encodeRequest(produced);
            G2Request consumed=G2Wire.decodeRequest(requestBytes);
            assertEquals(produced,consumed);
            assertEquals(SOURCE,consumed.source());
            assertArrayEquals(raw,consumed.payload().bytes());
            assertArrayEquals(requestBytes,G2Wire.encodeRequest(consumed));
            G2Response result=new G2Response(consumed.requestId(),milestone,consumed.source(),consumed.payload());
            byte[] responseBytes=G2Wire.encodeResponse(result);
            G2Response reloaded=G2Wire.decodeResponse(responseBytes);
            assertEquals(result,reloaded);
            assertArrayEquals(raw,reloaded.result().bytes());
            assertArrayEquals(responseBytes,G2Wire.encodeResponse(reloaded));
        }
    }

    @Test void missingNullAndEmptyCollectionRemainThreeDistinctJsonStates() {
        for(String raw:List.of("{}","{\"field\":null}","{\"field\":[]}")) {
            G2Request request=new G2Request("presence",Milestone.M0,SOURCE,ProjectionJson.object(utf8(raw),8192));
            JsonNode consumed=StrictJson.parse(G2Wire.decodeRequest(G2Wire.encodeRequest(request)).payload().bytes());
            if(raw.equals("{}")) assertFalse(consumed.has("field"));
            else if(raw.contains("null")) assertTrue(consumed.get("field").isNull());
            else assertTrue(consumed.get("field").isArray()&&consumed.get("field").isEmpty());
        }
        assertNotEquals(request("{}"),request("{\"field\":null}"));
        assertNotEquals(request("{\"field\":null}"),request("{\"field\":[]}"));
    }

    @Test void sourceAndEnvelopeRequireActualIntegerTokens() {
        String valid=new String(G2Wire.encodeRequest(request("{}")),StandardCharsets.UTF_8);
        for(String token:List.of("true","false","1.0","1e0","\"1\"","null","[]")) {
            assertMalformed(valid.replace("\"schema_version\":1","\"schema_version\":"+token));
        }
        for(String token:List.of("true","false","2.0","2e0","\"2\"","null","[]")) {
            assertMalformed(valid.replace("\"bytes\":2","\"bytes\":"+token));
        }
    }

    @Test void sourceMissingNullAndUnknownFieldsAreRejectedBeforeDomainDispatch() {
        String valid=new String(G2Wire.encodeRequest(request("{}")),StandardCharsets.UTF_8);
        assertMalformed(valid.replace("\"source\":", "\"unknown_source\":"));
        assertMalformed(valid.replace("\"source_ref\":", "\"unknown_ref\":"));
        assertMalformed(valid.replace("\"machine_id\":\"fixture-machine-01\",", ""));
        assertMalformed(valid.replace("\"machine_id\":\"fixture-machine-01\"", "\"machine_id\":null"));
        assertMalformed(valid.replace("\"source_ref\":{", "\"source_ref\":{\"extra\":null,"));
        assertMalformed(valid.replace("\"payload\":{}", "\"payload\":null"));
        assertMalformed(valid.replace("\"payload\":{}", "\"payload\":[]"));
        assertMalformed(valid.replace(",\"payload\":{}", ""));
    }

    @Test void uint64DecimalIdentityKeepsStringTokensAcrossWireAndTypedConsumer() {
        String largest="18446744073709551615";
        G2Request request=request("{\"file_id\":\""+largest+"\"}");
        JsonNode payload=StrictJson.parse(G2Wire.decodeRequest(G2Wire.encodeRequest(request)).payload().bytes());
        CrossJsDecimalUInt64 identity=new CrossJsDecimalUInt64(StrictJson.text(payload.get("file_id")));
        assertEquals(largest,identity.decimal());
        for(String invalid:List.of("00","01","+1","-0","-1","1.0","1e0","18446744073709551616"))
            assertThrows(IllegalArgumentException.class,()->new CrossJsDecimalUInt64(invalid));
        for(String token:List.of(largest,"true","1.0","null","[]")) {
            G2Request opaque=request("{\"file_id\":"+token+"}");
            JsonNode raw=StrictJson.parse(G2Wire.decodeRequest(G2Wire.encodeRequest(opaque)).payload().bytes());
            assertThrows(IllegalArgumentException.class,()->new CrossJsDecimalUInt64(StrictJson.text(raw.get("file_id"))));
        }
    }

    @Test void responseScalarsAndMultibyteTokenSpansRemainExact() {
        for(String value:List.of("null","[]","{}","true","false","1.2300","-0.0","1E+9",
                "\"保留\\u0020中间 \\\" 引号\"","\"18446744073709551615\"")) {
            byte[] raw=utf8(value);
            G2Response response=new G2Response("span",Milestone.M7,SOURCE,ProjectionJson.value(raw,8192));
            assertArrayEquals(raw,G2Wire.decodeResponse(G2Wire.encodeResponse(response)).result().bytes());
        }
    }

    @Test void outerEnvelopeFormattingDoesNotBecomePartOfTheOpaqueBody() {
        byte[] encoded=G2Wire.encodeRequest(request("{ \"a\" : [null, [], {}] }"));
        byte[] formatted=utf8(" \n"+new String(encoded,StandardCharsets.UTF_8)+"\t\r\n");
        assertEquals(G2Wire.decodeRequest(encoded),G2Wire.decodeRequest(formatted));
        assertTrue(Arrays.equals(encoded,G2Wire.encodeRequest(G2Wire.decodeRequest(formatted))));
    }

    private static G2Request request(String body) {
        return new G2Request("body",Milestone.M0,SOURCE,ProjectionJson.object(utf8(body),8192));
    }
    private static void assertMalformed(String raw) {
        G2Exception error=assertThrows(G2Exception.class,()->G2Wire.decodeRequest(utf8(raw)));
        assertEquals(G2HttpError.Code.MALFORMED_REQUEST,error.code());
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}
