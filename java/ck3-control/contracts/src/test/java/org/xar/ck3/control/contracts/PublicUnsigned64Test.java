package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import static org.xar.ck3.control.contracts.PublicUnsigned64.*;

final class PublicUnsigned64Test {
    @Test void publicTokenKindsAndFullWidthAreValidatedBeforeTypedConstruction() {
        assertEquals(MAXIMUM,parse(token("\"18446744073709551615\""),Minimum.ZERO,NumericInput.SAFE_INTEGER_OR_DECIMAL));
        assertEquals(MAXIMUM_SAFE_NUMBER,parse(token("9007199254740991"),Minimum.ZERO,NumericInput.SAFE_INTEGER_OR_DECIMAL));
        for(String bad:new String[]{"true","1.0","9007199254740992","-1","null","\"01\"","\"+1\"","\"1\\n\"","\"18446744073709551616\""}) {
            assertThrows(IllegalArgumentException.class,()->parse(token(bad),Minimum.ZERO,NumericInput.SAFE_INTEGER_OR_DECIMAL),bad);
        }
        assertThrows(IllegalArgumentException.class,()->parse(token("1"),Minimum.ONE,NumericInput.DECIMAL_ONLY));
        assertThrows(IllegalArgumentException.class,()->parse(token("\"0\""),Minimum.ONE,NumericInput.DECIMAL_ONLY));
        assertEquals(BigInteger.ZERO,parse(token("\"0\""),Minimum.ZERO,NumericInput.DECIMAL_ONLY));
    }

    @Test void optionalOwnerPolicyReceivesThreeDistinctSyntaxBranches() {
        var object=StrictJson.object();
        assertInstanceOf(Missing.class,read(object,"revision",Minimum.ZERO,NumericInput.SAFE_INTEGER_OR_DECIMAL));
        object.putNull("revision");assertInstanceOf(NullValue.class,read(object,"revision",Minimum.ZERO,NumericInput.SAFE_INTEGER_OR_DECIMAL));
        object.put("revision",MAXIMUM.toString());
        var value=assertInstanceOf(Value.class,read(object,"revision",Minimum.ZERO,NumericInput.SAFE_INTEGER_OR_DECIMAL));
        assertEquals(MAXIMUM.toString(),canonical(value.value(),Minimum.ZERO));
        object.put("revision",true);assertThrows(IllegalArgumentException.class,()->read(object,"revision",Minimum.ZERO,NumericInput.SAFE_INTEGER_OR_DECIMAL));
    }

    private static com.fasterxml.jackson.databind.JsonNode token(String json) {
        return StrictJson.parse(json.getBytes(StandardCharsets.UTF_8));
    }
}
