package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.IntNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Controlled boundary values prove the wire domain only, not a negative-ID live observation or action qualification. */
final class NativeCharacterIdTest {
    @Test void signedNativeDomainPreservesEveryBoundaryAndTheFullGenerationBits() {
        for(int value:new int[]{Integer.MIN_VALUE,-16777217,-2,0,1,16777217,Integer.MAX_VALUE}) {
            var actual=new NativeCharacterId(value);
            assertEquals(actual,NativeCharacterId.of((long)value));
            assertEquals(actual,NativeCharacterId.of(BigInteger.valueOf(value)));
            assertEquals(value,actual.value());assertEquals(BigInteger.valueOf(value),actual.asBigInteger());
            assertEquals(IntNode.valueOf(value),actual.toJson());assertTrue(actual.toJson().isIntegralNumber());
        }
        assertNotEquals(new NativeCharacterId(-2),new NativeCharacterId(16777214),"full native identity is not the low24 storage index");
        assertNotEquals(new NativeCharacterId(-2),new NativeCharacterId(2),"negative identity never aliases its absolute value");
    }
    @Test void sentinelAndAllWiderNumericInputsRefuseBeforeNarrowing() {
        assertThrows(IllegalArgumentException.class,()->new NativeCharacterId(-1));
        for(long value:new long[]{-1,((long)Integer.MIN_VALUE)-1,((long)Integer.MAX_VALUE)+1,Long.MIN_VALUE,Long.MAX_VALUE})
            assertThrows(IllegalArgumentException.class,()->NativeCharacterId.of(value));
        for(BigInteger value:List.of(BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE),BigInteger.ONE.shiftLeft(128),BigInteger.ONE.shiftLeft(128).negate()))
            assertThrows(IllegalArgumentException.class,()->NativeCharacterId.of(value));
        assertThrows(IllegalArgumentException.class,()->NativeCharacterId.of((BigInteger)null));
    }
    @Test void soleStrictJsonWireRoundtripRetainsSignedIntegerTokens() {
        for(int value:new int[]{Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE}) {
            var expected=new NativeCharacterId(value);byte[] encoded=StrictJson.canonical(expected.toJson());
            assertEquals(Integer.toString(value),new String(encoded,StandardCharsets.UTF_8));
            assertEquals(expected,NativeCharacterId.fromJson(StrictJson.parse(encoded)));
            assertEquals(expected,NativeCharacterId.fromJson(JsonNodeFactory.instance.numberNode((long)value)));
            assertEquals(expected,NativeCharacterId.fromJson(JsonNodeFactory.instance.numberNode(BigInteger.valueOf(value))));
        }
    }
    @Test void missingNullBooleanTextFloatDecimalAndOutOfDomainIntegersAreDifferentJsonTypes() {
        var factory=JsonNodeFactory.instance;
        for(JsonNode value:List.of(MissingNode.getInstance(),NullNode.getInstance(),factory.booleanNode(false),factory.booleanNode(true),
                factory.textNode("-2"),factory.numberNode(-2.0),factory.numberNode(new BigDecimal("-2.0")),factory.arrayNode(),factory.objectNode(),
                factory.numberNode(-1),factory.numberNode(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                factory.numberNode(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE))))
            assertThrows(IllegalArgumentException.class,()->NativeCharacterId.fromJson(value));
        for(String value:List.of("true","false","null","\"-2\"","-2.0","-2e0","2147483648","-2147483649","-1"))
            assertThrows(IllegalArgumentException.class,()->NativeCharacterId.fromJson(StrictJson.parse(value.getBytes(StandardCharsets.UTF_8))));
        assertThrows(IllegalArgumentException.class,()->NativeCharacterId.fromJson(null));
    }
}
