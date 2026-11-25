package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2;
import org.xar.ck3.control.nativebridge.CurrentZg361Ae2Source;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFramePublicCodec;

/** Self-owned Java DATA; never an actual Core, private lease or GUI result. */
class NativeOwnerSnapshotCurrentZg361ScoreboardSelectionTest {
    private static com.fasterxml.jackson.databind.node.ObjectNode config(int version,String mode,int overall) {
        var c=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v"+version).put("mode",mode)
                .put("overall_timeout_seconds",overall).put("read_timeout_seconds",60).put("maximum_frames_per_operation",65536);
        c.putObject("owner_descriptor").put("path","D:/java-data/scoreboard/owner.json").put("bytes",1).put("sha256","0".repeat(64));return c;
    }
    private static CurrentZg361Ae2Source source(boolean visible,boolean admissible) {
        var s=new CurrentZg361Ae2Source.Scoreboard(true,true,true,true,visible,visible,visible,7,visible?3:0,
                Optional.of("zg361_scoreboard_entry_managed"),!visible&&admissible,visible&&admissible);
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.SCOREBOARD,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(s));
    }
    @Test void strictV52CommonSixAndTwelveDoNotExpandAnyOriginalMode() {
        var c=config(52,"current_zg361_scoreboard_open_close_once",600);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_ZG361_SCOREBOARD,NativeOwnerSnapshotMain268.observationMode(c));
        assertEquals(12,NativeOwnerSnapshotMain268.currentZg361ScoreboardConfig(c).submissions());
        assertEquals(600,NativeOwnerSnapshotMain268.currentZg361OverallTimeoutLimit(NativeOwnerSnapshotMain268.observationMode(c)));
        for(String key:List.of("window_name","open_entry","actor","pay","combined","phase_bound","maximum_status_polls","days","text")) {
            var extra=c.deepCopy();extra.put(key,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361ScoreboardConfig(extra),key);
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentZg361ScoreboardConfig(c.deepCopy().put("overall_timeout_seconds",601)));
        assertEquals(24,NativeOwnerSnapshotMain268.currentZg361Ae2Config(config(49,"current_zg361_ae2_case_once",600)).submissions());
        assertEquals(8,NativeOwnerSnapshotMain268.currentZg361ReviewConfig(config(50,"current_zg361_review_requirements_once",600)).submissions());
        assertEquals(32,NativeOwnerSnapshotMain268.currentZg361CombinedConfig(config(51,"current_zg361_review_ae2_case_once",900)).submissions());
    }
    @Test void actualAdmissibilityAndObservedFlagsStayDataWithoutInventingSuccess()throws IOException {
        NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardAction(source(false,true),CurrentZg361Ae2.Action.OPEN_SCOREBOARD);
        NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardAction(source(true,true),CurrentZg361Ae2.Action.CLOSE_SCOREBOARD);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardAction(source(false,false),CurrentZg361Ae2.Action.OPEN_SCOREBOARD));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardAction(source(true,false),CurrentZg361Ae2.Action.CLOSE_SCOREBOARD));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardAction(source(false,true),CurrentZg361Ae2.Action.CONFIRM_PRESENT));
        assertFalse(NativeOwnerSnapshotMain268.currentZg361ScoreboardSource(source(false,false)).modalVisible());
        assertTrue(NativeOwnerSnapshotMain268.currentZg361ScoreboardSource(source(true,false)).modalVisible());
        var r=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentZg361ScoreboardResult(r,"java-data");
        for(String flag:List.of("scoreboard_open_close_pass","heap_or_memory_fix_pass","business_contract_pass","wholeproduct_pass","new_date_observed","physical_save_confirmed"))assertFalse(r.path(flag).booleanValue(),flag);
        assertEquals(0,r.path("date_calls").intValue());assertEquals(0,r.path("save_calls").intValue());
    }
    @Test void legitimatePartialMiddleAbsenceIsRetainedButFullCoreOrConnectionDriftRefuses()throws IOException {
        var prefix=new CoreFrame.Prefix(-240,3,true,1,true,true,-2,true);
        var core=new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,prefix);
        var witness=new GuiRootIndexFrame.OwnerWitness(BigInteger.TWO,BigInteger.valueOf(20),BigInteger.valueOf(30),7);
        var missingWindow=new GuiWindowFrame.Partial(core,"zg361_scoreboard_window",List.of(),Optional.empty(),witness);
        assertSame(missingWindow,NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardMiddle(missingWindow,prefix,BigInteger.TWO));
        assertFalse(missingWindow.windowAvailable());assertEquals(missingWindow,GuiWindowFrame.decode(GuiWindowFramePublicCodec.encode(missingWindow)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardMiddle(missingWindow,prefix,BigInteger.ONE));
        var drift=new CoreFrame.Prefix(-239,3,true,1,true,true,-2,true);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardMiddle(missingWindow,drift,BigInteger.TWO));
        var layer=new GuiWindowFrame.Partial(core,"middle",List.of(),Optional.empty(),witness);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardMiddle(layer,prefix,BigInteger.TWO));
        var root=new GuiWindowFrame.Node(0,java.util.OptionalInt.empty(),0,0,"zg361_scoreboard_window",1,true,true);
        var modal=new GuiWindowFrame.Node(1,java.util.OptionalInt.of(0),0,1,"zg361_scoreboard_modal",0,false,false);
        var complete=new GuiWindowFrame.Partial(core,"zg361_scoreboard_window",List.of(new GuiWindowFrame.TopLevel("zg361_scoreboard_window",true,true)),Optional.of(new GuiWindowFrame.Window(List.of(root,modal))),witness);
        assertSame(complete,NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardMiddle(complete,prefix,BigInteger.TWO));
        assertEquals(complete,GuiWindowFrame.decode(GuiWindowFramePublicCodec.encode(complete)));
        var truncated=new GuiWindowFrame.Node(0,java.util.OptionalInt.empty(),0,0,"zg361_scoreboard_window",2,true,true);
        assertThrows(IllegalArgumentException.class,()->new GuiWindowFrame.Window(List.of(truncated,modal)));
        var other=new GuiWindowFrame.Partial(core,"other_window",List.of(),Optional.empty(),witness);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentZg361ScoreboardMiddle(other,prefix,BigInteger.TWO));
    }
}
