package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PersonalGoldFrame;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** Configuration/codec DATA only. No descriptor, physical owner, retained process or session is invented. */
final class NativeOwnerPersonalGoldSelectionTest {
    private PersonalGoldFrame frame(String resource)throws IOException {
        try(var input=getClass().getResourceAsStream(resource)){
            if(input==null)throw new IOException("actual C++ gold resource missing: "+resource);
            var envelope=NativeWire.decode(NativeWire.packet(input.readNBytes(4096)));
            var result=assertInstanceOf(NativeWire.CommandResult.class,envelope);
            return PersonalGoldFrame.decode(new RawJson(result.result().token().orElseThrow().value()));
        }
    }
    private static NativeLaunchPlan selection(ExactCk3Build build,String adapter)throws IOException {
        Path root=Path.of("D:/software-gold-owner-selection-DATA-only");
        var game=new FileRef(root.resolve("ck3.exe").toString(),1,build.executableSha256());
        var bridge=new FileRef(root.resolve("bridge-DATA.bin").toString(),1,"a".repeat(64));
        var injector=new FileRef(root.resolve("injector-DATA.bin").toString(),1,"b".repeat(64));
        var steam=new FileRef(root.resolve("steam.exe").toString(),1,"c".repeat(64));
        var review=new LaunchSourceBinding.Review("software-gold-owner",null,game,bridge,injector,null,null,List.of());
        return new NativeLaunchPlanCodec.Configuration("gold-owner-selection","gold-owner-selection-session",review,
                root.resolve("profile"),root.resolve("state"),root.resolve("evidence"),"\\\\.\\pipe\\gold-owner-selection",
                "software-bridge",adapter,new NativeLaunchPlan.NewGame(),false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of(),1L<<30,64L<<20,Instant.now().plusSeconds(60),Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan("software-gold-owner",steam,Instant.now().plusSeconds(60)),NativeLaunchPlan.PreparedProfile.vanilla(),16).accept();
    }
    @Test void unchangedReadOnlyOwnerModeAcceptsBothVersionedDataSelectionsWithoutGrantingActualOwnership()throws Exception {
        var config=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v5").put("mode","personal_gold_frame");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.PERSONAL_GOLD,NativeOwnerSnapshotMain268.observationMode(config));
        for(var value:List.of(frame("/newnative/personal-gold121003-v2/personal-gold-v2-partial.json"),
                frame("/newnative/personal-gold121003-v2/personal-gold-v2-unavailable.json"),
                frame("/newnative/personal-gold1210/personal-gold-producer-partial01.json"))){
            var plan=selection(value.build(),value.version().adapter());
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requirePersonalGoldSelection(plan,value));
            assertThrows(IllegalStateException.class,()->plan.sources().nativeProof());
        }
    }
    @Test void frameCannotCrossTheOwnersSelectedExecutableOrAdapter()throws Exception {
        var v2=frame("/newnative/personal-gold121003-v2/personal-gold-v2-partial.json");
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requirePersonalGoldSelection(
                selection(ExactCk3Build.CK3_1210,PersonalGoldFrame.ADAPTER),v2));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requirePersonalGoldSelection(
                selection(v2.build(),PersonalGoldFrame.ADAPTER),v2));
        var v1=frame("/newnative/personal-gold1210/personal-gold-producer-partial01.json");
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requirePersonalGoldSelection(
                selection(v2.build(),v2.version().adapter()),v1));
    }
}
