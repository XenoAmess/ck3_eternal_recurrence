package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;

/** Real Win32 filesystem-only sharing regressions. No Game, Steam, SDK, quote grant or canonical writer is created. */
final class QualifiedCloneCustodyTest {
    @TempDir Path temporary;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    private ControlBuild.FileRef metadata(String name){return new ControlBuild.FileRef(temporary.resolve(name).toString(),1,"c".repeat(64));}
    private NativeLaunchPlan plan(Path profile,NativeLaunchPlan.SavedGame saved,Instant deadline)throws IOException {
        String machine="xenoamess-full-tower-eb9d2c1186";
        var sources=LaunchSourceBinding.accept(new LaunchSourceBinding.Review(machine,deadline,metadata("ck3.exe"),metadata("bridge.dll"),metadata("injector.exe"),
                new NativeLaunchEvidence.Inputs(metadata("environment.json"),metadata("build.json"),metadata("registration.json")),temporary,List.of()));
        return new NativeLaunchPlan("clone-handle-fixture","fixture-session",sources,profile,temporary.resolve("state"),temporary.resolve("evidence"),
                "\\\\.\\pipe\\clone-handle-fixture","fixture-bridge","fixture-adapter",saved,false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of(),1L<<30,64L<<20,deadline,Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan(machine,metadata("steam.exe"),deadline),NativeLaunchPlan.PreparedProfile.vanilla(),32);
    }
    private record Fixture(NativeLaunchPlan plan,FileWitness original,Path source,Path actual,List<Path> directories){ }
    private Fixture fixture(boolean inPlace)throws Exception {
        Path profile=Files.createDirectory(temporary.resolve("profile"));Path saves=Files.createDirectory(profile.resolve("save games"));
        Path source=inPlace?saves.resolve("checkpoint.ck3"):temporary.resolve("original/checkpoint.ck3");
        Files.createDirectories(source.getParent());Files.writeString(source,"tiny software-only preserved original SAVE");
        var plan=plan(profile,new NativeLaunchPlan.SavedGame("checkpoint",ControlBuild.FileRef.measure(source)),Instant.now().plusSeconds(60));
        var original=files.observe(source).orElseThrow();NativeSavedGameFiles.materialize(profile,(NativeLaunchPlan.SavedGame)plan.load());
        Path actual=NativeSavedGameClone.actualPath(plan);
        return new Fixture(plan,original,source,actual,List.of(profile,saves,source.getParent()).stream().distinct().toList());
    }
    private static void directoryWriteDenied(Path path)throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(path.toString(),0x40000000,7,null,3,0x02000000,null);
        if(!WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            Kernel32.INSTANCE.CloseHandle(handle);fail("directory GENERIC_WRITE unexpectedly acquired while retained: "+path);
        }
        assertEquals(32,Native.getLastError(),"a real share-mode conflict must reject directory writes");
    }
    private static void directoryWriteAvailable(Path path)throws IOException {
        HANDLE handle=Kernel32.INSTANCE.CreateFile(path.toString(),0x40000000,7,null,3,0x02000000,null);
        assertNotEquals(WinBase.INVALID_HANDLE_VALUE,handle,"directory write access must return after close");
        assertTrue(Kernel32.INSTANCE.CloseHandle(handle));
    }

    @Test void trueSourceCloneAndDirectoryHandlesBlockWritesDeleteRenameUntilCloseThenSdkTargetIsWritable()throws Exception {
        var f=fixture(false);NativeSavedGameClone.Observation historical;
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            historical=held.observation();held.requireCurrent(f.plan(),f.original());
            for(Path path:List.of(f.source(),f.actual())) {
                assertThrows(IOException.class,()->Files.writeString(path,"blocked",StandardOpenOption.WRITE));
                assertThrows(IOException.class,()->Files.delete(path));
                assertThrows(IOException.class,()->Files.move(path,path.resolveSibling("moved-"+path.getFileName()),StandardCopyOption.ATOMIC_MOVE));
            }
            for(Path directory:f.directories())directoryWriteDenied(directory);
            assertThrows(IOException.class,()->Files.move(f.plan().profileDirectory(),temporary.resolve("moved-profile"),StandardCopyOption.ATOMIC_MOVE));
            held.requireCurrent(f.plan(),f.original());
            held.releaseBeforeCreate(f.plan(),f.original());
            assertThrows(IOException.class,held::observation);
        }
        for(Path directory:f.directories())directoryWriteAvailable(directory);
        Files.writeString(f.actual(),"new synthetic SDK SAVE after quote/CREATE preparation scope ended",StandardOpenOption.WRITE,StandardOpenOption.TRUNCATE_EXISTING);
        files.verify(f.original());
        assertThrows(IOException.class,()->historical.requireCurrent(f.plan(),f.original()));
    }

    @Test void partialCloneAcquisitionFailureReleasesEveryEarlierSourceAndDirectoryHandle()throws Exception {
        var f=fixture(false);
        try(var writer=FileChannel.open(f.actual(),StandardOpenOption.WRITE)) {
            assertTrue(writer.isOpen());
            assertThrows(IOException.class,()->NativeSavedGameClone.qualify(f.plan(),f.original()));
            for(Path directory:f.directories())directoryWriteAvailable(directory);
            try(var sourceWriter=FileChannel.open(f.source(),StandardOpenOption.WRITE)){assertTrue(sourceWriter.isOpen());}
            files.verify(f.original());
        }
    }

    @Test void expiredOrOversizedPreparationCannotAcquireOrLeaveLocks()throws Exception {
        var f=fixture(false);
        assertThrows(IOException.class,()->NativeSavedGameClone.qualify(f.plan(),f.original(),1, f.plan().deadline(),Clock.systemUTC()));
        var clone=files.observe(f.actual()).orElseThrow();assertThrows(IOException.class,()->NativeSavedGameClone.qualify(f.plan(),clone));
        assertThrows(IOException.class,()->NativeSavedGameClone.qualify(f.plan(),f.original(),1<<20,Instant.EPOCH,Clock.systemUTC()));
        assertThrows(IOException.class,()->NativeSavedGameClone.qualify(f.plan(),f.original(),1<<20,f.plan().deadline().plusSeconds(1),Clock.systemUTC()));
        for(Path directory:f.directories())directoryWriteAvailable(directory);
        try(var sourceWriter=FileChannel.open(f.source(),StandardOpenOption.WRITE)){assertTrue(sourceWriter.isOpen());}
    }

    @Test void expiryDuringQuoteCannotBeRenewedByResettingTheClockAndOwnerCloseStillReleases()throws Exception {
        var f=fixture(false);Instant initial=Instant.now(),until=initial.plusSeconds(5);var time=new AtomicReference<>(initial);
        Clock clock=new Clock(){
            @Override public ZoneId getZone(){return ZoneOffset.UTC;}
            @Override public Clock withZone(ZoneId zone){return this;}
            @Override public Instant instant(){return time.get();}
        };
        var held=NativeSavedGameClone.qualify(f.plan(),f.original(),1<<20,until,clock);
        try {
            held.observation();time.set(until);
            assertThrows(IOException.class,()->held.requireCurrent(f.plan(),f.original()));
            time.set(initial);assertThrows(IOException.class,held::observation);
        }finally{held.close();}
        for(Path directory:f.directories())directoryWriteAvailable(directory);
        try(var cloneWriter=FileChannel.open(f.actual(),StandardOpenOption.WRITE)){assertTrue(cloneWriter.isOpen());}
    }

    @Test void wrongThreadCannotUseOrReleaseTheOwnersRealHandleScope()throws Exception {
        var f=fixture(false);var held=NativeSavedGameClone.qualify(f.plan(),f.original());
        try {
            var failures=new AtomicReference<Throwable[]>();
            Thread foreign=new Thread(()->{
                Throwable[] actual=new Throwable[2];
                try{held.observation();}catch(Throwable problem){actual[0]=problem;}
                try{held.close();}catch(Throwable problem){actual[1]=problem;}
                failures.set(actual);
            });
            foreign.start();foreign.join(5000);assertFalse(foreign.isAlive());
            assertInstanceOf(IOException.class,failures.get()[0]);assertInstanceOf(IOException.class,failures.get()[1]);
            held.requireCurrent(f.plan(),f.original());directoryWriteDenied(f.plan().profileDirectory());
        }finally{held.close();}
        for(Path directory:f.directories())directoryWriteAvailable(directory);
    }

    @Test void closedScopeNeverQuotesAgainAndItsDetachedJsonRemainsDataOnly()throws Exception {
        var f=fixture(false);var held=NativeSavedGameClone.qualify(f.plan(),f.original());
        var data=held.observation();held.close();held.close();
        assertThrows(IOException.class,held::observation);
        assertThrows(IOException.class,()->held.requireCurrent(f.plan(),f.original()));
        assertEquals(NativeSavedGameClone.SCHEMA,data.toJson().get("schema").textValue());
        for(Path directory:f.directories())directoryWriteAvailable(directory);
        try(var cloneWriter=FileChannel.open(f.actual(),StandardOpenOption.WRITE)){assertTrue(cloneWriter.isOpen());}
    }

    @Test void legacyInPlaceModeUsesOneRealFileHoldAndReleasesItBeforeSave()throws Exception {
        var f=fixture(true);
        try(var held=NativeSavedGameClone.qualify(f.plan(),f.original())) {
            assertTrue(held.observation().inPlace());held.requireCurrent(f.plan(),f.original());
            assertThrows(IOException.class,()->Files.writeString(f.actual(),"blocked",StandardOpenOption.WRITE));
            for(Path directory:f.directories())directoryWriteDenied(directory);
        }
        for(Path directory:f.directories())directoryWriteAvailable(directory);
        Files.writeString(f.actual(),"new synthetic in-place SAVE after preparation close",StandardOpenOption.WRITE,StandardOpenOption.TRUNCATE_EXISTING);
    }

    @Test void nativeCloseFailureCannotBecomeSuccessfulOnRepeatedCleanupOrCreateHandoff()throws Exception {
        var f=fixture(false);var held=NativeSavedGameClone.qualify(f.plan(),f.original());
        IOException expectedCloseFailure=null;
        try {
            // Read actual owned test handles; never replace private fields or manufacture custody.
            var leasesField=QualifiedCloneCustody.class.getDeclaredField("fileLeases");leasesField.setAccessible(true);
            var leases=(org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.ReadOnlyLease[])leasesField.get(held);
            var handleField=org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.ReadOnlyLease.class.getDeclaredField("handle");
            handleField.setAccessible(true);HANDLE cloneHandle=(HANDLE)handleField.get(leases[1]);
            assertTrue(Kernel32.INSTANCE.CloseHandle(cloneHandle),"invalidate one genuinely acquired software test handle");
            expectedCloseFailure=assertThrows(IOException.class,held::close);
            IOException first=expectedCloseFailure;
            assertTrue(first.getMessage().contains("read lease close Win32="));
            var repeated=assertThrows(IOException.class,held::close);
            assertNotSame(first,repeated);assertSame(first,repeated.getCause(),"unknown release remains observable");
            assertSame(first,assertThrows(IOException.class,()->{try(held){throw first;}}),
                    "automatic cleanup must not replace the primary with self-suppression IllegalArgumentException");
            assertThrows(IOException.class,held::observation);
            var handoff=assertThrows(IOException.class,()->held.releaseBeforeCreate(f.plan(),f.original()));
            assertTrue(java.util.Arrays.stream(handoff.getSuppressed()).anyMatch(problem->problem.getCause()==first));
            // All other owned handles still get their actual close attempt despite the failed clone close.
            for(Path directory:f.directories())directoryWriteAvailable(directory);
            try(var sourceWriter=FileChannel.open(f.source(),StandardOpenOption.WRITE)){assertTrue(sourceWriter.isOpen());}
            try(var cloneWriter=FileChannel.open(f.actual(),StandardOpenOption.WRITE)){assertTrue(cloneWriter.isOpen());}
            files.verify(f.original());
        }finally{
            try{held.close();}catch(IOException closing){if(closing!=expectedCloseFailure&&closing.getCause()!=expectedCloseFailure)throw closing;}
        }
    }
}
