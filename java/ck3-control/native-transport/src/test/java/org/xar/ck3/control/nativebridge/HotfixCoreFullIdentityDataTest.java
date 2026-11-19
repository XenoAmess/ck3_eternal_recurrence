package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;

/** Hand-authored identity DATA; no Native packet, RAM, IPC, installed Root or action authority. */
final class HotfixCoreFullIdentityDataTest {
    private static final ExactCk3Build HOTFIX=ExactCk3Build.CK3_1210_STEAM_26757580;
    private static final ExactCk3Build OLD=ExactCk3Build.CK3_1210;
    private static ObjectNode identity(String schema,ExactCk3Build build) {
        return StrictJson.object().put("schema",schema).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFullAdapterId())
                .put("backend","ck3-1.21.0-native-headless-main-thread");
    }
    private static ObjectNode state(ExactCk3Build rootBuild,ExactCk3Build actorBuild) {
        var root=identity("ck3_1210_full_state_v1",rootBuild).put("date_raw",24000)
                .put("paused",true).put("map_ready",true).putNull("active_event");
        root.putArray("active_wars");root.putArray("player_armies");root.putArray("history");
        var actor=identity("ck3_1210_played_character_v1",actorBuild).put("character_id",-2130706431)
                .put("alive",true).put("stress_points",42).put("has_heir",true)
                .put("primary_heir_id",Integer.MIN_VALUE).put("betrothed_id",0).putNull("primary_spouse_id");
        actor.putArray("spouse_ids");root.set("played_character",actor);return root;
    }
    private static ObjectNode normalize(ObjectNode raw) {
        return NativeSemanticNormalizer.normalize(NativeSemanticNormalizer.original(raw),"identity-data",BigInteger.TEN).semantic();
    }
    @Test void aHotfixFullKeepsSignedIdentityAndItsDistinctTupleAcrossReplay() {
        var raw=state(HOTFIX,HOTFIX);var result=normalize(raw);
        assertEquals(-2130706431,result.path("played_character").path("character_id").intValue());
        assertEquals(Integer.MIN_VALUE,result.path("played_character").path("primary_heir_id").intValue());
        assertEquals(0,result.path("played_character").path("betrothed_id").intValue());
        assertEquals(HOTFIX.executableSha256(),result.path("executable_sha256").textValue());
        assertEquals(HOTFIX.coreFullAdapterId(),result.path("adapter_id").textValue());
        assertArrayEquals(StrictJson.canonical(result),StrictJson.canonical(normalize(result)));
        assertEquals(OLD.executableSha256(),normalize(state(OLD,OLD)).path("executable_sha256").textValue());
    }
    @Test void rootActorAndAdapterCannotMixTheTwoExactProfiles() {
        assertThrows(IllegalArgumentException.class,()->normalize(state(HOTFIX,OLD)));
        assertThrows(IllegalArgumentException.class,()->normalize(state(OLD,HOTFIX)));
        var crossedNew=state(HOTFIX,HOTFIX).put("adapter_id",OLD.coreFullAdapterId());
        assertThrows(IllegalArgumentException.class,()->normalize(crossedNew));
        var crossedOld=state(OLD,OLD).put("adapter_id",HOTFIX.coreFullAdapterId());
        assertThrows(IllegalArgumentException.class,()->normalize(crossedOld));
    }
    @Test void hotfixMilitaryAndEventRestrictionsDoNotRewriteTheLegacyDomain() {
        for(String field:List.of("active_wars","player_armies")) {
            var nonempty=state(HOTFIX,HOTFIX);nonempty.withArray(field).addObject().put("identity_data",0);
            assertThrows(IllegalArgumentException.class,()->normalize(nonempty));
            var missing=state(HOTFIX,HOTFIX);missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->normalize(missing));
            var wrong=state(HOTFIX,HOTFIX).put(field,false);
            assertThrows(IllegalArgumentException.class,()->normalize(wrong));
            var old=state(OLD,OLD);old.withArray(field).addObject().put("identity_data",0);
            assertEquals(1,normalize(old).path(field).size());
        }
        var event=state(HOTFIX,HOTFIX);event.putObject("active_event").put("identity_data",0);
        assertThrows(IllegalArgumentException.class,()->normalize(event));
        var absent=state(HOTFIX,HOTFIX);absent.remove("active_event");
        assertThrows(IllegalArgumentException.class,()->normalize(absent));
        assertFalse(normalize(state(HOTFIX,HOTFIX)).has("event_queue"),"no queue proof is invented from the event presentation");
    }
    @Test void coreRoundTripAndExitKeepTheHotfixTupleWhileSaveStaysClosed() {
        var prefix=new CoreFrame.Prefix(24000,1,true,0,true,true,-2130706431,true);
        var frame=new CoreFrame.Partial(HOTFIX,prefix);
        var decoded=assertInstanceOf(CoreFrame.Partial.class,CoreFrame.decode(CoreFramePublicCodec.encode(frame)));
        assertEquals(frame,decoded);
        var pause=StrictJson.parse(CoreClockControl.request(CoreClockControl.Step.PAUSE_MAP,decoded).additionalFields().bytes());
        assertEquals(HOTFIX.coreFullAdapterId(),pause.path("core_clock_control").path("adapter_id").textValue());
        var exit=StrictJson.parse(CoreApplicationExit.request(decoded).additionalFields().bytes());
        assertEquals(HOTFIX.executableSha256(),exit.path("core_application_exit").path("executable_sha256").textValue());
        assertThrows(IllegalArgumentException.class,()->CoreClockControl.request(CoreClockControl.Step.SAVE_CHECKPOINT,decoded));
        assertEquals("save-checkpoint",CoreClockControl.request(CoreClockControl.Step.SAVE_CHECKPOINT,new CoreFrame.Partial(OLD,prefix)).step());
        assertThrows(IllegalArgumentException.class,()->CoreClockControl.request(CoreClockControl.Step.PAUSE_MAP,new CoreFrame.Partial(ExactCk3Build.CK3_12004,prefix)));
    }
    @Test void configuredBuildIdentityDoesNotGrantUnmigratedFrontendLayouts() {
        var build=FrontendRulesData.Build.require(HOTFIX.version(),HOTFIX.executableSha256());
        assertEquals("ck3-1.21.0-26757580-msvc-x64",build.adapterId());
        assertEquals(HOTFIX.executableSha256(),build.sha256().toLowerCase(java.util.Locale.ROOT));
        assertThrows(IllegalArgumentException.class,build::requireRules);
        assertThrows(IllegalArgumentException.class,build::requireFrontend);
        assertThrows(IllegalArgumentException.class,build::requireLoadedFeatures);
        assertDoesNotThrow(FrontendRulesData.Build.CK3_12004::requireRules);
        assertDoesNotThrow(FrontendRulesData.Build.CK3_12004::requireFrontend);
        assertDoesNotThrow(FrontendRulesData.Build.CK3_12004::requireLoadedFeatures);
    }
}
