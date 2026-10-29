package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Configuration entry validation only; Root's actual lease/private-CROWN path requires its full integration fixture. */
final class RootAdvanceRuntimeFactsSettingsTest {
    private static ObjectNode body() {
        return StrictJson.object().put("schema",RootAdvanceRuntimeFacts.SETTINGS_SCHEMA)
                .put("crown_query_enabled",true).put("crown_paused_query_enabled",false).put("war_daily_watch_enabled",false);
    }
    private static RawJson raw(ObjectNode body) {return new RawJson(StrictJson.canonical(body));}
    private static ExactRef ref(RawJson original) {
        return new ExactRef("fixture/actual-life-settings.json",original.bytes().length,DriverJson.sha256(original.bytes()));
    }
    @Test void exactOriginalFlagsRoundTripWithoutDefaultsOrAuthority() {
        RawJson original=raw(body());var settings=RootAdvanceRuntimeFacts.Settings.decode(ref(original),original);
        assertEquals(ref(original),settings.original());assertTrue(settings.crownQueryEnabled());
        assertFalse(settings.crownPausedQueryEnabled());assertFalse(settings.warDailyWatchEnabled());
        RawJson roundtrip=raw((ObjectNode)StrictJson.parse(original.bytes()));
        assertEquals(settings.original(),RootAdvanceRuntimeFacts.Settings.decode(ref(original),roundtrip).original());
    }
    @Test void soleTypedEncoderFeedsTheStrictOriginalConsumerForEveryExplicitFlagCombination() {
        for(boolean query:List.of(false,true))for(boolean paused:List.of(false,true))for(boolean watch:List.of(false,true)) {
            RawJson original=RootAdvanceRuntimeFacts.Settings.encode(query,paused,watch);
            var settings=RootAdvanceRuntimeFacts.Settings.decode(ref(original),original);
            assertEquals(query,settings.crownQueryEnabled());assertEquals(paused,settings.crownPausedQueryEnabled());
            assertEquals(watch,settings.warDailyWatchEnabled());assertArrayEquals(original.bytes(),
                    RootAdvanceRuntimeFacts.Settings.encode(settings.crownQueryEnabled(),settings.crownPausedQueryEnabled(),settings.warDailyWatchEnabled()).bytes());
        }
    }
    @Test void missingNullWrongTypeAndUnknownFlagsCannotBecomeFalseDefaults() {
        for(String key:List.of("crown_query_enabled","crown_paused_query_enabled","war_daily_watch_enabled")) {
            ObjectNode missing=body();missing.remove(key);RawJson absent=raw(missing);
            assertThrows(IllegalArgumentException.class,()->RootAdvanceRuntimeFacts.Settings.decode(ref(absent),absent));
            ObjectNode nullable=body().putNull(key);RawJson nil=raw(nullable);
            assertThrows(IllegalArgumentException.class,()->RootAdvanceRuntimeFacts.Settings.decode(ref(nil),nil));
            ObjectNode number=body().put(key,0);RawJson numeric=raw(number);
            assertThrows(IllegalArgumentException.class,()->RootAdvanceRuntimeFacts.Settings.decode(ref(numeric),numeric));
        }
        RawJson unknown=raw(body().put("enabled",true));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceRuntimeFacts.Settings.decode(ref(unknown),unknown));
    }
    @Test void changedOriginalAndDuplicateFlagsRemainRejected() {
        RawJson actual=raw(body());RawJson changed=raw(body().put("war_daily_watch_enabled",true));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceRuntimeFacts.Settings.decode(ref(actual),changed));
        RawJson duplicate=new RawJson(("{\"schema\":\""+RootAdvanceRuntimeFacts.SETTINGS_SCHEMA
                +"\",\"crown_query_enabled\":true,\"crown_query_enabled\":false,\"crown_paused_query_enabled\":false,\"war_daily_watch_enabled\":false}").getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceRuntimeFacts.Settings.decode(ref(duplicate),duplicate));
    }
}
