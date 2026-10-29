package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Crosses the actual settlement producer and the common lifecycle, Driver and planning serializers. */
final class DriverMaterialSerializationTest {
    @Test void actualNativeRatioAndOpaqueTokensSurviveEveryTreeAndWireBridge() {
        for (String raw : new String[]{"{\"raw\":1,\"scale\":2}",
                "{\"raw\":-1,\"scale\":" + BigInteger.ONE.shiftLeft(2000) + "}"}) {
            var score = NativeOneLifeSettlement.encodeScore(NativeOneLifeSettlement.normalizeScore(
                    FullJsonTree.parse(bytes(raw),FullJsonTree.MAXIMUM_BYTES),"actual ratio"));
            ObjectNode material=LifecycleJson.row(); material.set("actual_native_score",score);
            material.set("opaque",FullJsonTree.parse(bytes("[-0.0,1.0,1e23,1.234567890123456789,{\"nested\":-0.0}]"),512));
            var immutable=LifecycleJson.immutable(material);
            byte[] original=LifecycleJson.bytes(material);
            var parsed=LifecycleJson.parse(original,FullJsonTree.MAXIMUM_BYTES);
            assertEquals(immutable,LifecycleJson.immutable(parsed));
            assertEquals(immutable,DriverJson.fromNormalizedNode(DriverJson.toNormalizedNode(immutable)));
            assertEquals(immutable,DriverJson.object(DriverJson.encode(immutable),FullJsonTree.MAXIMUM_BYTES));
            assertEquals(immutable,OpportunityJson.parse(OpportunityJson.encode(immutable)));
            assertEquals(immutable,DriverJson.fromNormalizedNode(OpportunityJson.toNode(immutable)));
            assertEquals(immutable,DriverJson.fromNormalizedNode(FullJsonTree.parse(
                    FullJsonTree.encode(parsed,FullJsonTree.MAXIMUM_BYTES),FullJsonTree.MAXIMUM_BYTES)));
            assertEquals(Double.doubleToRawLongBits(score.doubleValue()),
                    Double.doubleToRawLongBits(parsed.get("actual_native_score").doubleValue()));
            assertTrue(parsed.get("actual_native_score").isFloatingPointNumber());
            assertFalse(parsed.get("actual_native_score").isIntegralNumber());
            var opaque=OpportunityJson.array(OpportunityJson.object(immutable,"material").get("opaque"),"opaque");
            assertEquals(new OpportunityJson.DecimalValue("-0.0"),opaque.getFirst());
            assertEquals("1.234567890123456789",parsed.get("opaque").get(3).asText());
        }
    }
    @Test void legalSeventyThousandDigitIntegerUsesTheExistingExplicitMaterialLease() {
        String digits="7".repeat(70000); byte[] original=bytes("{\"contract_progress\":"+digits+",\"zero\":-0.0}");
        var model=DriverJson.object(original,FullJsonTree.MAXIMUM_BYTES);
        assertEquals(new BigInteger(digits),OpportunityJson.integer(model.get("contract_progress"),"contract_progress"));
        assertEquals(model,LifecycleJson.immutable(LifecycleJson.parse(DriverJson.encode(model),FullJsonTree.MAXIMUM_BYTES)));
        assertEquals(model,OpportunityJson.parse(OpportunityJson.encode(model)));
        assertEquals(model,DriverJson.fromNormalizedNode(DriverJson.toNormalizedNode(model)));
        assertThrows(IllegalArgumentException.class,()->FullJsonTree.parse(original,original.length-1));
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse(original,1048576));
    }
    @Test void actualNormalizedProducerAndOpaqueTokensCrossTheActualPublicDataSerializer() {
        var original=DriverJson.object(bytes("{\"history\":[-0.0,1.0,1e-400,{\"opaque\":[1.234567890123456789]}]}"),4096);
        var tree=(ObjectNode)DriverJson.toNormalizedNode(original);
        var ratio=NativeOneLifeSettlement.normalizeScore(FullJsonTree.parse(bytes("{\"raw\":-1,\"scale\":"
                +BigInteger.ONE.shiftLeft(2000)+"}"),4096),"actual native ratio");
        tree.set("actual_native_score",NativeOneLifeSettlement.encodeScore(ratio));
        var expected=DriverJson.fromNormalizedNode(tree);
        var wire=PublicDataJson.encode(tree);
        assertEquals(expected,DriverJson.object(wire.bytes(),RawJson.MAXIMUM_BYTES));
        assertEquals(expected,DriverJson.fromNormalizedNode(PublicDataJson.object(wire)));
        assertEquals(expected,DriverJson.object(PublicDataJson.encodePreservingDecimals(
                PublicDataJson.object(wire),wire).bytes(),RawJson.MAXIMUM_BYTES));
        assertEquals("-0.0",PublicDataJson.object(wire).get("actual_native_score").asText());
    }
    @Test void tokenIdentityTypeAndReceiptBoundariesStayStrict() {
        var node=FullJsonTree.parse(bytes("{\"present_null\":null,\"empty\":[],\"one\":1,\"ratio\":1.0,\"zero\":-0.0}"),256);
        assertFalse(node.has("missing")); assertTrue(node.get("present_null").isNull());
        assertTrue(node.get("empty").isArray()); assertTrue(node.get("one").isIntegralNumber());
        assertFalse(node.get("ratio").isIntegralNumber());
        assertEquals("-0.0",node.get("zero").asText());
        for(String bad:new String[]{" ","{\"x\":1,\"x\":2}","{}{}","NaN","Infinity","01","[1,"})
            assertThrows(IllegalArgumentException.class,()->FullJsonTree.parse(bytes(bad),256));
        assertThrows(IllegalArgumentException.class,()->FullJsonTree.parse(new byte[]{(byte)0xc3,(byte)0x28},256));
        assertThrows(IllegalArgumentException.class,()->OpportunityJson.parse(bytes("\""+"a".repeat(131072)+"\"")));
        assertThrows(IllegalArgumentException.class,()->OpportunityJson.parse(bytes("[".repeat(33)+"0"+"]".repeat(33))));
        assertThrows(IllegalArgumentException.class,()->FullJsonTree.parse(bytes("[".repeat(65)+"0"+"]".repeat(65)),1024));
        assertThrows(IllegalArgumentException.class,()->DriverJson.fromNormalizedNode(
                com.fasterxml.jackson.databind.node.DoubleNode.valueOf(Double.NaN)));
    }
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
}
