package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class PublicTypedDataJsonTest {
    @Test void typedArgumentsKeepDecimalTokensOpaqueArraysAndOriginalUnicodeBytes() {
        var fields=new LinkedHashMap<String,OpportunityJson.Value>();
        fields.put("\ue000",new OpportunityJson.Text("last"));
        fields.put("\ud83d\ude00",new OpportunityJson.Text("emoji \ud83d\ude00"));
        fields.put("arguments",new OpportunityJson.Arr(List.of(
                new OpportunityJson.DecimalValue("-0.0"),new OpportunityJson.DecimalValue("0.0"),
                new OpportunityJson.DecimalValue("1.0"),new OpportunityJson.DecimalValue("1e10000"),
                new OpportunityJson.Arr(List.of(OpportunityJson.Nil.INSTANCE,new OpportunityJson.Text("unchanged"))))));
        var original=new OpportunityJson.Obj(fields);RawJson encoded=PublicDataJson.encodeTyped(original);
        assertEquals(original,DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES));
        String text=new String(encoded.bytes(),StandardCharsets.UTF_8);
        assertTrue(text.contains("emoji \ud83d\ude00"));assertFalse(text.contains("\\uD83D"));assertFalse(text.contains("\\ud83d"));
        assertTrue(text.indexOf("\ud83d\ude00")<text.indexOf("\ue000"),"retain existing Java natural field order");
        assertTrue(text.contains("[-0.0,0.0,1.0,1e10000,"));
        assertArrayEquals(encoded.bytes(),PublicDataJson.encodeTyped(DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES)).bytes());
    }

    @Test void typedEncoderRejectsMalformedJavaTextInsteadOfReplacingItsBytes() {
        var malformed=new OpportunityJson.Obj(java.util.Map.of("argument",new OpportunityJson.Text("\ud800")));
        assertThrows(IllegalArgumentException.class,()->PublicDataJson.encodeTyped(malformed));
    }
}
