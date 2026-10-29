package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Wire regressions execute the same formatter selected by the installed public product. */
public final class RootPublicPausePublicResultTest {
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}

    @Test void directPrimitiveAndRecoveryAttemptsKeepOnlyDeclaredCountersAsDecimalStrings(){
        var wire=RootPublicPausePublicResult.present(raw("{\"accepted\":true,\"native_revision\":18446744073709551615,\"date_raw\":-12,\"map_control_recovery\":{\"starting_revision\":9007199254740993,\"ending_date_raw\":1001,\"attempts\":[{\"accepted\":false,\"error\":\"map unavailable\"},{\"revision\":9007199254740993,\"map_control_postcondition\":{\"ending_native_revision\":18446744073709551615,\"ending_date_raw\":1001}}]}}"));
        var row=StrictJson.parse(wire.bytes());
        assertEquals("18446744073709551615",row.get("native_revision").textValue());
        assertEquals(-12,row.get("date_raw").intValue());
        var recovery=row.get("map_control_recovery");
        assertEquals("9007199254740993",recovery.get("starting_revision").textValue());
        assertEquals(1001,recovery.get("ending_date_raw").intValue());
        assertEquals("map unavailable",recovery.get("attempts").get(0).get("error").textValue());
        assertEquals("9007199254740993",recovery.get("attempts").get(1).get("revision").textValue());
        assertEquals("18446744073709551615",recovery.get("attempts").get(1).get("map_control_postcondition").get("ending_native_revision").textValue());
    }

    @Test void absenceAndExplicitNullKeepDifferentWireMeaning(){
        var absent=StrictJson.parse(RootPublicPausePublicResult.present(raw("{}" )).bytes());
        var present=StrictJson.parse(RootPublicPausePublicResult.present(raw("{\"revision\":null}" )).bytes());
        assertFalse(absent.has("revision"));assertTrue(present.has("revision"));assertTrue(present.get("revision").isNull());
    }

    @Test void exactDecimalTokensAndUnknownSafeValuesSurviveTheActualFormatter(){
        String original="{\"revision\":0,\"ratio\":-0.0,\"nested\":{\"ratio\":1.2300e-2,\"revision\":42}}";
        String wire=new String(RootPublicPausePublicResult.present(raw(original)).bytes(),StandardCharsets.UTF_8);
        assertTrue(wire.contains("-0.0"));assertTrue(wire.contains("1.2300e-2"));
        assertEquals(42,StrictJson.parse(wire.getBytes(StandardCharsets.UTF_8)).get("nested").get("revision").intValue());
    }

    @Test void booleansDecimalsStringsNegativeAndOverflowAreNotCounterIntegers(){
        for(String token:new String[]{"true","false","1.0","\"1\"","-1","18446744073709551616"}){
            assertThrows(IllegalArgumentException.class,()->RootPublicPausePublicResult.present(raw("{\"revision\":"+token+"}")));
            assertThrows(IllegalArgumentException.class,()->RootPublicPausePublicResult.present(raw("{\"map_control_recovery\":{\"starting_revision\":"+token+"}}")));
        }
    }

    @Test void unrelatedNestedRevisionNeverAcquiresTheCounterRole(){
        assertThrows(IllegalArgumentException.class,()->RootPublicPausePublicResult.present(raw("{\"other\":{\"revision\":9007199254740993}}")));
        assertThrows(IllegalArgumentException.class,()->RootPublicPausePublicResult.present(raw("{\"starting_revision\":9007199254740993}")));
    }

    @Test void malformedRecoveryOrAttemptContainersFailAtThePublicBoundary(){
        for(String text:new String[]{"{\"map_control_recovery\":null}","{\"map_control_recovery\":[]}",
                "{\"map_control_recovery\":{\"attempts\":null}}","{\"map_control_recovery\":{\"attempts\":{}}}",
                "{\"map_control_recovery\":{\"attempts\":[null]}}","{\"map_control_postcondition\":false}"})
            assertThrows(IllegalArgumentException.class,()->RootPublicPausePublicResult.present(raw(text)));
    }
}
