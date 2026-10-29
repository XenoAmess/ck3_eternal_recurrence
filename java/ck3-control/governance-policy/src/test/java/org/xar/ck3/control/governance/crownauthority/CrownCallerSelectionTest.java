package org.xar.ck3.control.governance.crownauthority;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Unchanged historical producer material is DATA, never current native qualification. */
final class CrownCallerSelectionTest {
    private CrownAuthorityPolicy.Readback original()throws Exception {
        try(var stream=getClass().getResourceAsStream("/crownauthority/original-producer-golden.json")) {
            assertNotNull(stream,"actual retained producer golden is mandatory");return CrownAuthorityCodec.decodeReadback(StrictJson.canonical(StrictJson.parse(stream.readAllBytes()).get("cases").get(0).get("input").get("readback")));
        }
    }
    @Test void nativeFinalCallerLawDoesNotBecomeTheOrdinaryNextUpgrade()throws Exception {
        var data=original();assertEquals("crown_authority_1",CrownAuthorityPolicy.choose(data).lawKey());
        var explicit=CrownCallerSelection.select(data,"crown_authority_2");assertEquals("crown_authority_2",explicit.lawKey());
        assertEquals(data,CrownAuthorityCodec.decodeReadback(CrownAuthorityCodec.encodeReadback(data)));
    }
    @Test void callerMissingZeroAndUnusedLimitsRemainExactNativeInputs()throws Exception {
        var data=original();assertEquals(List.of(),CrownCallerSelection.limits(StrictJson.object()));
        var args=StrictJson.object().put("law_key","crown_authority_2").put("caller_request_id","original-native-id");args.set("readback",StrictJson.parse(CrownAuthorityCodec.encodeReadback(data)));args.set("caller_budgets",StrictJson.object().put("gold",0));
        assertEquals("crown_authority_2",CrownCallerSelection.callerChoice(data,args).lawKey());assertEquals("0",CrownCallerSelection.callerChoice(data,args).budgetsRaw().getFirst().amountRaw().toString());
        assertEquals(CrownCallerSelection.select(data,"crown_authority_2").quotedCosts(),CrownCallerSelection.quotedCosts(args,data));
    }
    @Test void activeAbsentAndWrongTypedLimitsCannotGainCallerQualification()throws Exception {
        var data=original();for(String law:List.of("crown_authority_0","crown_authority_99"))assertThrows(IllegalArgumentException.class,()->CrownCallerSelection.select(data,law));
        assertThrows(IllegalArgumentException.class,()->CrownCallerSelection.limits(StrictJson.object().put("gold",true)));
        assertThrows(IllegalArgumentException.class,()->CrownCallerSelection.limits(StrictJson.object().put("unknown",1)));
    }
}
