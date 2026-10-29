package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.LifecyclePublicResultCodec;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;

/** Actual shared normalized producer -> sole public codec -> tool/resource envelopes -> original DATA parser. */
final class PublicDecimalEnvelopeTest {
    @Test void normalizedNegativeZeroAndIntegralFloatReachBothPublicRepresentationsExactly() {
        var source=McpJson.object().put("ready",true).put("commit_serial",1).put("source_character_id",73)
                .put("record_candidate",0).put("old_record",0).put("record_delta",0).put("blessing_count",0)
                .put("refusal_count",0).put("contract_progress",0).put("record_written",false);
        source.putObject("final_score").put("raw",-1).put("scale",BigInteger.TEN.pow(400));
        source.putObject("score_before_reject").put("raw",BigInteger.TEN.pow(100).add(BigInteger.ONE)).put("scale",BigInteger.TEN.pow(100));
        var inspection=McpJson.object().put("revision",1);
        inspection.set("one_life_settlement",NativeOneLifeSettlement.encode(NativeOneLifeSettlement.decodeNative(source)));
        var actual=LifecyclePublicResultCodec.encodeSettlementInspection(PublicDataJson.encode(inspection));
        var expected=DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES);
        var call=PublicMcpDirectory.CallResult.fromBusinessJson(actual);
        assertEquals(expected,DriverJson.object(McpJson.token(call.bytes(),"structuredContent"),RawJson.MAXIMUM_BYTES));
        String text=McpJson.parse(call.bytes()).path("content").get(0).path("text").textValue();
        assertEquals(expected,DriverJson.object(text.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
        var resource=PublicMcpDirectory.ResourceResult.fromBusinessJson("ck3://state/current",actual);
        String resourceText=McpJson.parse(resource.bytes()).path("contents").get(0).path("text").textValue();
        assertEquals(expected,DriverJson.object(resourceText.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
        assertTrue(text.contains("-0.0"));assertTrue(text.contains("1.0"));
    }
    @Test void opaqueOriginalDecimalTokensSurviveEnvelopeTextAndStructuredContentWithoutAliases() {
        var source=new RawJson("{\"original_metric\":1.0,\"history\":[-0.0,[1.2500e+2]]}".getBytes(StandardCharsets.UTF_8));
        var actual=PublicMcpDirectory.CallResult.fromBusinessJson(source);
        var expected=DriverJson.object(source.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(expected,DriverJson.object(McpJson.token(actual.bytes(),"structuredContent"),RawJson.MAXIMUM_BYTES));
        String text=McpJson.parse(actual.bytes()).path("content").get(0).path("text").textValue();
        assertEquals(expected,DriverJson.object(text.getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
    }
}
