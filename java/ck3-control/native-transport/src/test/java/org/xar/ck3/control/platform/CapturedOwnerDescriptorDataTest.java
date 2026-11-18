package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Tiny descriptor DATA, not a real supervisor, process, Game or attach permission. */
final class CapturedOwnerDescriptorDataTest {
    @TempDir Path root;
    private ControlBuild.FileRef ref(String name){return new ControlBuild.FileRef(root.resolve(name).toString(),1,"a".repeat(64));}
    private GameSupervisorControl.Descriptor data()throws Exception {
        Instant until=Instant.parse("2030-01-01T00:00:00Z");
        var review=new LaunchSourceBinding.Review("software-only",until,ref("ck3.exe"),ref("bridge.dll"),ref("injector.exe"),
                new NativeLaunchEvidence.Inputs(ref("env.json"),ref("build.json"),ref("registration.json")),root,List.of());
        String slash=String.valueOf((char)92);
        var configuration=new NativeLaunchPlanCodec.Configuration("request","session",review,root,root.resolve("state"),root.resolve("evidence"),
                slash.repeat(2)+"."+slash+"pipe"+slash+"captured-data","fixture-bridge","fixture-adapter",new NativeLaunchPlan.NewGame(),false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1L<<30,64L<<20,until,Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan("software-only",ref("steam.exe"),until),NativeLaunchPlan.PreparedProfile.vanilla(),32);
        var identity=new WindowsJobProcess.ProcessIdentity(42,"134376718582643410",root.resolve("software.exe").toString());
        return new GameSupervisorControl.Descriptor("software-only","session",identity,identity,configuration,
                new ExactRef(ref("hello.json").path(),1,"a".repeat(64)),new ExactRef(ref("launch.json").path(),1,"b".repeat(64)),
                root.resolve(GameSupervisorControl.STOP_FILE),root.resolve(GameSupervisorControl.TERMINAL_FILE));
    }
    private ExactRef write(GameSupervisorControl.Descriptor value)throws Exception {
        Path file=root.resolve(GameSupervisorControl.DESCRIPTOR_FILE);GameSupervisorControl.writeDescriptor(file,value);
        var actual=ControlBuild.FileRef.measure(file);return new ExactRef(actual.path(),actual.bytes(),actual.sha256());
    }
    @Test void exactCapturedOwnerDataRoundTripsWithoutRereadingAnUnboundPath()throws Exception {
        var value=data();var source=write(value);byte[] raw=Files.readAllBytes(Path.of(source.path()));
        assertEquals(value,GameSupervisorControl.readCapturedDescriptor(source,raw));
        assertEquals(value,GameSupervisorControl.readDescriptor(Path.of(source.path())));
        assertFalse(Files.exists(root.resolve("ck3.exe")));
    }
    @Test void restoredOwnerARejectsOtherSameLengthCapturedGameIdentityB()throws Exception {
        var value=data();var source=write(value);byte[] a=Files.readAllBytes(Path.of(source.path()));
        var b=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(a,GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
        ((com.fasterxml.jackson.databind.node.ObjectNode)b.get("game")).put("pid",43);byte[] other=StrictJson.canonical(b);
        assertEquals(a.length,other.length);new ControlBuild.FileRef(source.path(),source.bytes(),source.sha256()).verify();
        assertThrows(IOException.class,()->GameSupervisorControl.readCapturedDescriptor(source,other));
        assertArrayEquals(a,Files.readAllBytes(Path.of(source.path())));
    }
    @Test void capturedDescriptorKeepsItsBoundAndActualControlSiblingContract()throws Exception {
        var value=data();var source=write(value);byte[] raw=Files.readAllBytes(Path.of(source.path()));
        var crossed=new ExactRef(root.resolve("different/owner.json").toString(),source.bytes(),source.sha256());
        assertThrows(IOException.class,()->GameSupervisorControl.readCapturedDescriptor(crossed,raw));
        var tooLarge=new ExactRef(source.path(),(long)GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES+1,source.sha256());
        assertThrows(IOException.class,()->GameSupervisorControl.readCapturedDescriptor(tooLarge,raw));
        assertThrows(IOException.class,()->GameSupervisorControl.readCapturedDescriptor(source,new byte[0]));
    }
}
