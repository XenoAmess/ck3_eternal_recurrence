package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

final class CurrentCoreCheckpointSaveDataTest {
    @Test void actualCppResultsRetainSubmittedOnlyAndNeverPhysicalSave()throws Exception {
        for(String name:new String[]{"submitted","rejected","indeterminate","unavailable"}) {
            var result=CurrentCoreCheckpointSaveResult.decode(new RawJson(CurrentCheckpointCppFrames.result(name)));
            assertEquals(name.equals("submitted"),result.accepted());assertEquals(result.accepted(),result.submission().isPresent());
            assertEquals(CurrentCheckpointCppFrames.response(name).nativeOk(),result.accepted());
        }
    }
    @Test void actualCppClaimAndRealJavaFactoryKeepCurrentTupleAndOldClockFullGuards()throws Exception {
        var core=CurrentCheckpointCppFrames.core("request");var request=CurrentCoreCheckpointSave.request(core);
        assertEquals("save-checkpoint",request.step());assertEquals(CurrentCoreCheckpointSave.CAPABILITY,request.requiredCapability().orElseThrow());
        var actual=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));assertEquals(1,actual.size());assertEquals(13,actual.get("core_checkpoint_save").size());
        assertThrows(IllegalArgumentException.class,()->CoreClockControl.request(CoreClockControl.Step.SAVE_CHECKPOINT,core));
        assertThrows(IllegalArgumentException.class,()->CurrentCoreCheckpointSave.request(new CoreFrame.Partial(ExactCk3Build.CK3_12004,core.prefix())));
        assertThrows(IllegalArgumentException.class,()->CurrentCoreCheckpointSave.request(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313_FULL111,core.prefix())));
        var p=core.prefix();assertThrows(IllegalArgumentException.class,()->CurrentCoreCheckpointSave.request(new CoreFrame.Partial(core.build(),new CoreFrame.Prefix(p.dateRaw(),p.speed(),false,p.localPlayerId(),true,true,p.playedCharacterId(),true))));
    }
    @Test void derivedNegativeFieldTypesAndPhysicalTrueCannotBeNativeSuccess()throws Exception {
        String original=new String(CurrentCheckpointCppFrames.result("submitted"),StandardCharsets.UTF_8);
        for(String bad:new String[]{original.replace("\"physical_save_confirmed\":false","\"physical_save_confirmed\":true"),
                original.replace("\"effect_attempted\":true","\"effect_attempted\":1"),original.replace("\"accepted\":true","\"accepted\":null"),
                original.replace(CurrentCoreCheckpointSave.RESULT_SCHEMA,"wrong-schema"),original.replace("\"complete_snapshot\":false","\"complete_snapshot\":true")}) {
            assertNotEquals(original,bad);
            assertThrows(IOException.class,()->CurrentCoreCheckpointSaveResult.decode(new RawJson(bad.getBytes(StandardCharsets.UTF_8))));
        }
        var extra=NativeWire.object(NativeWire.parse(CurrentCheckpointCppFrames.result("submitted"))).put("reason","invented");
        assertThrows(IOException.class,()->CurrentCoreCheckpointSaveResult.decode(new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(extra))));
        var rejected=NativeWire.object(NativeWire.parse(CurrentCheckpointCppFrames.result("rejected"))).putNull("submission");
        assertThrows(IOException.class,()->CurrentCoreCheckpointSaveResult.decode(new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(rejected))));
    }
}
