package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeSavedGameClone;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** Executes only the private physical DATA phase check; no Custody/Loaded, Admission, token or Game is created. */
final class SavedInitialClonePhaseTest {
    @TempDir Path temporary;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    private ControlBuild.FileRef metadata(String name){return new ControlBuild.FileRef(temporary.resolve(name).toString(),1,"c".repeat(64));}
    private record Fixture(NativeLaunchPlan plan,FileWitness original,NativeSavedGameClone.Observation captured,Path actual){ }
    private Fixture fixture()throws Exception {
        Path source=temporary.resolve("original/checkpoint.ck3");Files.createDirectories(source.getParent());
        Files.writeString(source,"tiny original checkpoint software-only");
        Path profile=Files.createDirectory(temporary.resolve("profile"));Files.createDirectory(profile.resolve("save games"));
        Instant deadline=Instant.now().plusSeconds(60);String machine="xenoamess-full-tower-eb9d2c1186";
        var sources=LaunchSourceBinding.accept(new LaunchSourceBinding.Review(machine,deadline,metadata("ck3.exe"),metadata("bridge.dll"),metadata("injector.exe"),
                new NativeLaunchEvidence.Inputs(metadata("env.json"),metadata("build.json"),metadata("registration.json")),temporary,List.of()));
        var saved=new NativeLaunchPlan.SavedGame("checkpoint",ControlBuild.FileRef.measure(source));
        var plan=new NativeLaunchPlan("clone-phase-fixture","fixture-session",sources,profile,temporary.resolve("state"),temporary.resolve("evidence"),
                "\\\\.\\pipe\\clone-phase-fixture","fixture-bridge","fixture-adapter",saved,false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of(),1L<<30,64L<<20,deadline,Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan(machine,metadata("steam.exe"),deadline),NativeLaunchPlan.PreparedProfile.vanilla(),32);
        var original=files.observe(source).orElseThrow();Path actual=NativeSavedGameClone.actualPath(plan);files.copyNew(original,actual);
        NativeSavedGameClone.Observation captured;
        try(var initial=NativeSavedGameClone.qualify(plan,original)){captured=initial.observation();}
        return new Fixture(plan,original,captured,actual);
    }
    private static void check(Fixture f)throws Exception {
        var method=RootJavaSavedBootstrap.class.getDeclaredMethod("requireInitialClone",NativeLaunchPlan.class,FileWitness.class,NativeSavedGameClone.Observation.class);
        method.setAccessible(true);
        try{method.invoke(null,f.plan(),f.original(),f.captured());}
        catch(InvocationTargetException failed){
            if(failed.getCause() instanceof Exception cause)throw cause;
            if(failed.getCause() instanceof Error cause)throw cause;
            throw new AssertionError(failed.getCause());
        }
    }
    private static void replaceEqual(Path target)throws IOException {
        Path replacement=target.resolveSibling("replacement-"+target.getFileName());Files.copy(target,replacement);
        Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(target));
        Files.move(target,target.resolveSibling("retained-"+target.getFileName()),StandardCopyOption.ATOMIC_MOVE);
        Files.move(replacement,target,StandardCopyOption.ATOMIC_MOVE);
    }
    @Test void currentPhysicalCloneCanBeRecheckedAfterPreparationHandlesAreReleased()throws Exception {
        var f=fixture();check(f);
        // A write open succeeds after preparation release, while the snapshot still has no Game permission.
        try(var writer=java.nio.channels.FileChannel.open(f.actual(),StandardOpenOption.WRITE)){assertTrue(writer.isOpen());}
        check(f);files.verify(f.original());
    }
    @Test void equalBytesAndMtimeWithNewCloneFileIdFailsThePrelivePhysicalCheck()throws Exception {
        var f=fixture();var originalMetadata=f.captured().toJson().deepCopy();check(f);replaceEqual(f.actual());
        var replacement=files.observe(f.actual()).orElseThrow();assertEquals(f.captured().actualSave().reference(),replacement.reference());
        assertNotEquals(f.captured().actualSave().identity().fileId(),replacement.identity().fileId());
        assertThrows(IOException.class,()->check(f));files.verify(f.original());
        assertEquals(originalMetadata,f.captured().toJson(),"failed current check never rewrites original mapping DATA");
    }
    @Test void changedCloneContentRejectsPreliveProjectionWithoutRebasingOriginalSource()throws Exception {
        var f=fixture();check(f);Files.writeString(f.actual(),"new software-only SAVE bytes",StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class,()->check(f));files.verify(f.original());
        assertEquals(f.original(),f.captured().originalSave());
    }
    @Test void changedSourceFileIdCannotRefreshTheOriginalPairWitness()throws Exception {
        var f=fixture();check(f);Path source=Path.of(f.original().reference().path());replaceEqual(source);
        assertEquals(f.original().reference(),files.observe(source).orElseThrow().reference());
        assertThrows(IOException.class,()->check(f));assertEquals(f.original(),f.captured().originalSave());
    }
}
