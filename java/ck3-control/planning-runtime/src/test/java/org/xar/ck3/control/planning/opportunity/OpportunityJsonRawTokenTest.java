package org.xar.ck3.control.planning.opportunity;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;

final class OpportunityJsonRawTokenTest {
    @Test void floatingLexemesRemainOriginalAcrossTheSharedWireCodec() {
        byte[] raw = "{\"exponent\":1.2300e+4,\"negative_zero\":-0.0,\"integer_valued_float\":1E+0,\"integer\":1,\"nil\":null}".getBytes(StandardCharsets.UTF_8);
        OpportunityJson.Obj value = OpportunityJson.object(OpportunityJson.parse(raw), "original opaque object");
        assertEquals(new OpportunityJson.DecimalValue("1.2300e+4"), value.get("exponent"));
        assertEquals(new OpportunityJson.DecimalValue("-0.0"), value.get("negative_zero"));
        assertEquals(new OpportunityJson.DecimalValue("1E+0"), value.get("integer_valued_float"));
        assertInstanceOf(OpportunityJson.IntegerValue.class, value.get("integer"));
        assertArrayEquals(raw, OpportunityJson.encode(value));
        assertEquals(value, OpportunityJson.parse(OpportunityJson.encode(value)));
    }

    @Test void rawEmissionAcceptsOnlyValidatedFloatingJsonTokensAndKeepsTheExistingBudget() {
        for (String token : List.of("1", "NaN", "Infinity", "01.0", "1e", "1.0,\"injected\":true", "1.0 "))
            assertThrows(IllegalArgumentException.class, () -> new OpportunityJson.DecimalValue(token));
        assertThrows(IllegalArgumentException.class, () -> OpportunityJson.parse(new byte[131_073]));
        assertThrows(IllegalArgumentException.class, () -> OpportunityJson.parse("{\"x\":1,\"x\":1.0}".getBytes(StandardCharsets.UTF_8)));
    }
}
