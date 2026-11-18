package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Tiny physical test inputs; no Game, source qualification, canonical writer or production ENV. */
final class NativeSavedGamePreparationTest {
    @TempDir Path temporary;
    private final NativeCheckpointFiles nativeFiles=new NativeCheckpointFiles();
    private final class AdmittedFiles implements CheckpointFiles {
        int copies;boolean rejectCopy;
        public Optional<FileWitness> observe(Path path)throws IOException{return nativeFiles.observe(path);}
        public byte[] read(FileWitness expected,int maximum)throws IOException{return nativeFiles.read(expected,maximum);}
        public FileWitness createNew(Path target,byte[] bytes)throws IOException{throw new IOException("unused operation");}
        public FileWitness replace(Path target,byte[] bytes)throws IOException{throw new IOException("replace must never be requested");}
        public FileWitness copyNew(FileWitness source,Path target)throws IOException {
            copies++;if(rejectCopy)throw new IOException("actual storage owner denied the copy");return nativeFiles.copyNew(source,target);
        }
    }
    private FileRef metadata(String name){return new FileRef(temporary.resolve(name).toString(),1,"c".repeat(64));}
    private NativeLaunchPlan plan()throws IOException {
        Path source=temporary.resolve("original/checkpoint.ck3");Files.createDirectories(source.getParent());
        Files.writeString(source,"SAV0100\nmeta_data={slot29_source=yes}\n");
        Path profile=Files.createDirectory(temporary.resolve("profile"));
        String machine=WindowsJobProcess.currentMachineId();Instant end=Instant.now().plusSeconds(180);
        var review=new LaunchSourceBinding.Review(machine,end,metadata("ck3.exe"),metadata("bridge.dll"),metadata("injector.exe"),
                new NativeLaunchEvidence.Inputs(metadata("ENV.json"),metadata("build.json"),metadata("registration.json")),temporary,List.of());
        return new NativeLaunchPlan("slot29-preparation","slot29-session",LaunchSourceBinding.accept(review),profile,
                temporary.resolve("native-state"),temporary.resolve("evidence"),"\\\\.\\pipe\\slot29-preparation","fixture-bridge","fixture-adapter",
                new NativeLaunchPlan.SavedGame("checkpoint",FileRef.measure(source)),false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1L<<30,64L<<20,end,
                Duration.ofSeconds(5),Duration.ofSeconds(30),new SteamOfflineProbe.Plan(machine,metadata("steam.exe"),end),
                NativeLaunchPlan.PreparedProfile.vanilla(),32);
    }
    private FileWitness original(NativeLaunchPlan plan)throws IOException {
        return nativeFiles.observe(Path.of(((NativeLaunchPlan.SavedGame)plan.load()).save().path())).orElseThrow();
    }
    private void directory(NativeLaunchPlan plan)throws IOException{Files.createDirectory(plan.profileDirectory().resolve("save games"));}

    @Test void precreateCopyUsesTheSuppliedAdapterAndKeepsOriginalPlanAndPair()throws Exception {
        var plan=plan();var source=original(plan);var declared=((NativeLaunchPlan.SavedGame)plan.load()).save();directory(plan);
        var files=new AdmittedFiles();
        var observed=NativeSavedGamePreparation.prepare(plan,source,files,Clock.systemUTC());
        assertEquals(1,files.copies);assertSame(declared,((NativeLaunchPlan.SavedGame)plan.load()).save());
        assertEquals(source,observed.originalSave());assertFalse(observed.inPlace());
        assertEquals(NativeSavedGameClone.actualPath(plan).toString(),observed.actualSave().reference().path());
        assertEquals(source.reference().sha256(),observed.actualSave().reference().sha256());
        assertNotEquals(source.identity().fileId(),observed.actualSave().identity().fileId());
        observed.requireCurrent(plan,source);nativeFiles.verify(source);
        assertFalse(Files.exists(plan.stateDirectory()));assertFalse(Files.exists(plan.evidenceRoot()));
    }
    @Test void storageRefusalLeavesNoTargetAndNeverFallsBackToRawCopy()throws Exception {
        var plan=plan();var source=original(plan);directory(plan);var files=new AdmittedFiles();files.rejectCopy=true;
        assertThrows(IOException.class,()->NativeSavedGamePreparation.prepare(plan,source,files,Clock.systemUTC()));
        assertEquals(1,files.copies);assertFalse(Files.exists(NativeSavedGameClone.actualPath(plan)));nativeFiles.verify(source);
    }
    @Test void missingSaveDirectoryRequiresTheActualOwnerToPrepareIt()throws Exception {
        var plan=plan();var source=original(plan);var files=new AdmittedFiles();
        assertThrows(IOException.class,()->NativeSavedGamePreparation.prepare(plan,source,files,Clock.systemUTC()));
        assertEquals(0,files.copies);assertFalse(Files.exists(plan.profileDirectory().resolve("save games")));nativeFiles.verify(source);
    }
    @Test void existingExactTargetStillRevalidatesTheOriginalBeforeReturningMapping()throws Exception {
        var plan=plan();var source=original(plan);directory(plan);Path target=NativeSavedGameClone.actualPath(plan);
        nativeFiles.copyNew(source,target);var files=new AdmittedFiles();
        var observed=NativeSavedGamePreparation.prepare(plan,source,files,Clock.systemUTC());
        assertEquals(0,files.copies);observed.requireCurrent(plan,source);
        Path old=Path.of(source.reference().path());Files.move(old,old.resolveSibling("retained-original.ck3"));
        Files.writeString(old,"changed source after target preparation");
        byte[] targetBefore=Files.readAllBytes(target);
        assertThrows(IOException.class,()->NativeSavedGamePreparation.prepare(plan,source,files,Clock.systemUTC()));
        assertEquals(0,files.copies);assertArrayEquals(targetBefore,Files.readAllBytes(target));
    }
    @Test void conflictingTargetAndUnrelatedSourceCannotTriggerCopyOrReplacement()throws Exception {
        var plan=plan();var source=original(plan);directory(plan);Path target=NativeSavedGameClone.actualPath(plan);
        Files.writeString(target,"retained conflicting target");byte[] targetBefore=Files.readAllBytes(target);var files=new AdmittedFiles();
        assertThrows(IOException.class,()->NativeSavedGamePreparation.prepare(plan,source,files,Clock.systemUTC()));
        Path unrelated=temporary.resolve("unrelated.ck3");Files.writeString(unrelated,"unrelated original");
        var other=nativeFiles.observe(unrelated).orElseThrow();
        assertThrows(IOException.class,()->NativeSavedGamePreparation.prepare(plan,other,files,Clock.systemUTC()));
        assertEquals(0,files.copies);assertArrayEquals(targetBefore,Files.readAllBytes(target));nativeFiles.verify(source);
    }
    @Test void exactOriginalDeadlineRejectsBeforeTheCopyCallback()throws Exception {
        var plan=plan();var source=original(plan);directory(plan);var files=new AdmittedFiles();
        var exactEnd=Clock.fixed(plan.deadline(),ZoneOffset.UTC);
        assertThrows(IOException.class,()->NativeSavedGamePreparation.prepare(plan,source,files,exactEnd));
        assertEquals(0,files.copies);assertFalse(Files.exists(NativeSavedGameClone.actualPath(plan)));nativeFiles.verify(source);
    }

    @Test void existingOnlyCensusHasPhysicalCustodyAndZeroNewOutputGrowth()throws Exception {
        var plan=plan();var source=original(plan);directory(plan);nativeFiles.copyNew(source,NativeSavedGameClone.actualPath(plan));
        var existing=NativeSavedGamePreparation.requirePrepared(plan,source,Clock.systemUTC());
        var census=existing.census();assertEquals(0,census.newGrowthBytes());assertEquals(source,census.originalSave());
        assertEquals(existing.observation().actualSave(),census.actualSave());
        assertEquals(Math.max(census.actualNativeFile().logicalBytes(),census.actualNativeFile().allocatedBytes()),census.existingAllocatedUpperBytes());
        assertEquals(plan.requestId(),census.requestId());assertEquals(plan.sessionId(),census.sessionId());
        existing.requireCurrent();nativeFiles.verify(source);
        assertFalse(Files.exists(plan.stateDirectory()));assertFalse(Files.exists(plan.evidenceRoot()));
        try(var files=Files.list(NativeSavedGameClone.actualPath(plan).getParent())){assertEquals(1,files.count());}
        assertThrows(IllegalArgumentException.class,()->new NativeSavedGamePreparation.ExistingCensus(census.schema(),
                census.machineId(),census.requestId(),census.sessionId(),census.observedAt(),census.originalSave(),census.actualSave(),
                census.actualNativeFile(),census.existingAllocatedUpperBytes(),1));
    }
    @Test void existingOnlyMissingTargetNeverFallsBackToPreparingACopy()throws Exception {
        var plan=plan();var source=original(plan);directory(plan);
        assertThrows(IOException.class,()->NativeSavedGamePreparation.requirePrepared(plan,source,Clock.systemUTC()));
        assertFalse(Files.exists(NativeSavedGameClone.actualPath(plan)));nativeFiles.verify(source);
        try(var files=Files.list(NativeSavedGameClone.actualPath(plan).getParent())){assertEquals(0,files.count());}
    }
    @Test void existingOnlyCensusCannotSurviveEqualBytesAtAnotherNativeFileId()throws Exception {
        var plan=plan();var source=original(plan);directory(plan);Path target=NativeSavedGameClone.actualPath(plan);nativeFiles.copyNew(source,target);
        var existing=NativeSavedGamePreparation.requirePrepared(plan,source,Clock.systemUTC());var actual=existing.census().actualSave();
        byte[] bytes=Files.readAllBytes(target);var stamp=Files.getLastModifiedTime(target);
        Files.move(target,target.resolveSibling("retained-clone.ck3"));Files.write(target,bytes);Files.setLastModifiedTime(target,stamp);
        assertEquals(actual.reference(),nativeFiles.observe(target).orElseThrow().reference());
        assertThrows(IOException.class,existing::requireCurrent);assertThrows(IOException.class,existing::census);nativeFiles.verify(source);
    }
}
