package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** Selection DATA only. Never calls main/run, attaches to a process or manufactures a CoreReceived. */
final class NativeOwnerRiteDraftCostsSelectionTest {
    @Test void onlyExplicitV12SelectsTheReadOnlyModeWithoutCallerCoreOrControlFields() {
        var config=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v12").put("mode","rite_draft_costs").put("expected_source_rite_id",152);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.RITE_DRAFT_COSTS,NativeOwnerSnapshotMain268.observationMode(config));
        for(String forbidden:List.of("window_name","core_prefix_only","control_step","maximum_status_polls","status_poll_interval_ms","expected_core","connection_generation")) {
            var altered=config.deepCopy();altered.put(forbidden,"not-a-source");
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(altered));
        }
        for(int prior:new int[]{1,2,5,9,10,11}) {
            var altered=config.deepCopy();altered.put("schema","xar.native-owner-snapshot-config/v"+prior);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(altered));
        }
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.PERSONAL_GOLD,NativeOwnerSnapshotMain268.observationMode(
                StrictJson.object().put("schema","xar.native-owner-snapshot-config/v5").put("mode","personal_gold_frame")));
    }
    private static NativeLaunchPlan selection(ExactCk3Build build,String adapter)throws IOException {
        Path root=Path.of("D:/software-root-index-selection-DATA-only");
        var game=new FileRef(root.resolve("ck3.exe").toString(),1,build.executableSha256());
        var bridge=new FileRef(root.resolve("bridge-DATA.bin").toString(),1,"a".repeat(64));
        var injector=new FileRef(root.resolve("injector-DATA.bin").toString(),1,"b".repeat(64));
        var steam=new FileRef(root.resolve("steam.exe").toString(),1,"c".repeat(64));
        var review=new LaunchSourceBinding.Review("root-index-owner-DATA",null,game,bridge,injector,null,null,List.of());
        return new NativeLaunchPlanCodec.Configuration("root-index-owner-DATA","root-index-session-DATA",review,
                root.resolve("profile"),root.resolve("state"),root.resolve("evidence"),"\\\\.\\pipe\\root-index-owner-DATA",
                "root-index-bridge-DATA",adapter,new NativeLaunchPlan.NewGame(),false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of(),1L<<30,64L<<20,Instant.now().plusSeconds(60),Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan("root-index-owner-DATA",steam,Instant.now().plusSeconds(60)),NativeLaunchPlan.PreparedProfile.vanilla(),16).accept();
    }
    @Test void exactSelectionStillGrantsNoOwnerOrNativeProofAndMixedTupleIsRejected()throws IOException {
        var frame=new RiteDraftCostsFrameV2.Partial(new CoreFrame.Partial(RiteDraftCostsFrameV2.BUILD,
                new CoreFrame.Prefix(53176992,3,true,1,true,true,-16777215,true)),new RiteDraftCostsFrameV2.Draft(152,-16777215,false,Long.MAX_VALUE,Long.MIN_VALUE,true),
                new org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFrame.OwnerWitness(java.math.BigInteger.ONE,java.math.BigInteger.ONE,java.math.BigInteger.ONE,1));
        var selected=selection(RiteDraftCostsFrameV2.BUILD,RiteDraftCostsFrameV2.BUILD.coreFrameAdapterId());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireRiteDraftCostsSelection(selected,frame));
        assertThrows(IllegalStateException.class,()->selected.sources().nativeProof());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireRiteDraftCostsSelection(
                selection(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210.coreFrameAdapterId()),frame));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireRiteDraftCostsSelection(
                selection(RiteDraftCostsFrameV2.BUILD,ExactCk3Build.CK3_1210.coreFrameAdapterId()),frame));
    }
}
