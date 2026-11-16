package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.channels.OverlappingFileLockException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Real ordinary Core/storage cleanup and finite callbacks only; no Prepared, Game, Native transport or agent. */
final class RootOwnerWaitBusinessDrainTest {
    @TempDir Path directory;
    private static final long CAP=8L*1024*1024;
    private record Original(SharedSourceFiles.Witness witness,byte[] body){
        private void verify()throws IOException {
            SharedSourceFiles.assertUnchanged(witness);
            assertArrayEquals(body,Files.readAllBytes(Path.of(witness.source().path())));
            SharedSourceFiles.assertUnchanged(witness);
        }
    }
    /** Empty byte-range-locked files are checked by full native metadata without opening their body for hashing. */
    private record EmptyLock(Path path,SharedSourceFiles.NativeFile original){
        private void verify()throws IOException {
            assertEquals(0,original.logicalBytes());assertEquals(1,original.linkCount());
            assertEquals(original,SharedSourceFiles.nativeFile(path));
        }
    }
    private record Fixture(RootApplicationAssembly.Core core,RootRuntimeStorageGuard guard,WriterContracts.Layout layout,
            WriterContracts.Head before,Path allocationLock,List<Original> originals,List<EmptyLock> locks,
            SharedSourceFiles.DirectoryIdentity events)implements AutoCloseable {
        private void requireReleasedUnchanged()throws IOException {
            assertTrue(core.closeCompletion().toCompletableFuture().isDone(),"business drain must finish before transport and owner wait");
            core.closeCompletion().toCompletableFuture().join();
            assertThrows(IOException.class,guard::requireCompleteAdmission,"the original business guard must reject another admission");
            assertAllocationLock(allocationLock,true);
            for(Original original:originals)original.verify();for(EmptyLock lock:locks)lock.verify();
            assertEquals(events,SharedSourceFiles.nativeDirectory(layout.events()));
            try(var children=Files.list(layout.events())){assertTrue(children.findAny().isEmpty(),"business cleanup cannot publish a canonical edge");}
            var after=core.writer().locked(same->same.head());
            assertEquals(before.state().sequence(),after.state().sequence());assertEquals(before.digest(),after.digest());
        }
        @Override public void close()throws IOException {
            try{core.close();core.closeCompletion().toCompletableFuture().join();}finally{guard.close();}
        }
    }
    private Fixture fixture()throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(),"actual Windows ordinary storage and allocation lock required");
        Path root=Files.createDirectory(directory.resolve("real-core")),control=Files.createDirectory(root.resolve("control"));
        Path managed=Files.createDirectory(root.resolve("managed")),ledger=Files.createDirectory(managed.resolve("continuity"));
        Path archive=Files.createDirectory(ledger.resolve("archive"));String machine=WindowsJobProcess.currentMachineId();
        var plan=new FreshContinuityGenesis.Plan(machine,1,OriginalWindowReducer.TARGET_DAYS);
        Path request=control.resolve("fresh-genesis-request.json");Files.write(request,FreshContinuityGenesis.encode(plan),StandardOpenOption.CREATE_NEW);
        var initial=new WriterContracts.InitialLayout(ledger.resolve("ROOT-CONTINUITY-WINDOW.json"),ledger.resolve("anchor.json"),machine);
        var current=new AtomicReference<RootApplicationAssembly.Core>();
        var guard=RootRuntimeStorageGuard.ordinary(initial,archive,()->{
            var core=current.get();if(core==null)throw new IOException("Core writer not constructed before actual genesis");return core.writer();
        },List.of(managed),CAP,Clock.systemUTC());
        RootApplicationAssembly.Core core=null;
        try{
            var initialized=ContinuityWriter.initializeFresh(plan,exact(request),initial,guard);
            Path noLaunch=control.resolve("no-game-launch-data.json");Files.writeString(noLaunch,"{\"purpose\":\"no-Game business drain regression\"}",StandardOpenOption.CREATE_NEW);
            var configuration=new RootApplicationConfiguration(machine,HostMode.MCP_STDIO,Instant.now().plusSeconds(120),exact(noLaunch),
                    initialized.layout(),List.of(exact(request)),archive,CAP);
            core=RootApplicationAssembly.open(configuration,Clock.systemUTC(),List.of(),Optional.empty(),guard);current.set(core);
            guard.requireCompleteAdmission();var before=core.writer().locked(same->same.head());
            assertEquals(0,before.state().sequence());assertEquals(ContinuityState.Status.AWAITING_INITIAL_ENTRY,before.state().status());
            assertFalse(before.state().toJson().has("game_binding"));
            List<Path> allocation;
            try(var files=Files.list(ledger)){
                allocation=files.filter(path->path.getFileName().toString().startsWith(".runtime-storage-")&&path.getFileName().toString().endsWith(".lock")).toList();
            }
            assertEquals(1,allocation.size());Path lock=allocation.getFirst();assertAllocationLock(lock,false);
            var originals=new ArrayList<Original>();
            for(Path path:List.of(initial.snapshot(),initial.anchor(),request,noLaunch)){
                var witness=SharedSourceFiles.observe(path);byte[] body=Files.readAllBytes(path);SharedSourceFiles.assertUnchanged(witness);originals.add(new Original(witness,body));
            }
            var locks=new ArrayList<EmptyLock>();
            for(Path path:List.of(initial.lock(),lock)){
                var original=new EmptyLock(path,SharedSourceFiles.nativeFile(path));original.verify();locks.add(original);
            }
            return new Fixture(core,guard,initialized.layout(),before,lock,List.copyOf(originals),List.copyOf(locks),SharedSourceFiles.nativeDirectory(initial.events()));
        }catch(Exception|Error failure){
            if(core!=null)try{core.close();core.closeCompletion().toCompletableFuture().join();}catch(RuntimeException|Error closing){failure.addSuppressed(closing);}
            try{guard.close();}catch(IOException|RuntimeException closing){failure.addSuppressed(closing);}throw failure;
        }
    }
    @Test void realBusinessCoreAndAllocationOwnerAreReleasedBeforeTransportAndOwnerWait()throws Exception {
        try(var actual=fixture()){
            var calls=new ArrayList<String>();
            RootOrdinaryRuntimeAssembly.awaitOwnerAfterBusinessRelease(()->{
                calls.add("business");RootOrdinaryRuntimeAssembly.closeBusinessResources(actual.core(),actual.guard());
            },()->{
                calls.add("transport");actual.requireReleasedUnchanged();
            },()->{
                calls.add("owner");actual.requireReleasedUnchanged();
            });
            assertEquals(List.of("business","transport","owner"),calls);actual.requireReleasedUnchanged();
        }
    }
    @Test void businessAndTransportFailuresEachStillEnterTheOwnerWait()throws Exception {
        for(String failedPhase:List.of("business","transport")){
            var calls=new ArrayList<String>();var original=new IOException("original "+failedPhase+" failure");
            IOException actual=assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.awaitOwnerAfterBusinessRelease(()->{
                calls.add("business");if(failedPhase.equals("business"))throw original;
            },()->{
                calls.add("transport");if(failedPhase.equals("transport"))throw original;
            },()->calls.add("owner")));
            assertSame(original,actual);assertEquals(List.of("business","transport","owner"),calls);
            assertEquals(0,actual.getSuppressed().length);
        }
    }
    @Test void firstFailureAndInterruptedOwnerKeepTheirExactIdentityAndPhaseSuppressionOrder()throws Exception {
        boolean wasInterrupted=Thread.currentThread().isInterrupted();
        try{
            var calls=new ArrayList<String>();IOException business=new IOException("business original"),transport=new IOException("transport original");
            var interrupted=new InterruptedException("owner original");
            IOException actual=assertThrows(IOException.class,()->RootOrdinaryRuntimeAssembly.awaitOwnerAfterBusinessRelease(()->{
                calls.add("business");throw business;
            },()->{
                calls.add("transport");throw transport;
            },()->{
                calls.add("owner");throw interrupted;
            }));
            assertSame(business,actual);assertEquals(List.of("business","transport","owner"),calls);
            assertEquals(List.of(transport,interrupted),Arrays.asList(actual.getSuppressed()));
            var onlyOwner=new InterruptedException("owner-only original");
            InterruptedException returned=assertThrows(InterruptedException.class,()->RootOrdinaryRuntimeAssembly.awaitOwnerAfterBusinessRelease(
                    ()->{},()->{},()->{throw onlyOwner;}));
            assertSame(onlyOwner,returned);assertEquals(0,returned.getSuppressed().length);
        }finally{if(!wasInterrupted)Thread.interrupted();}
    }
    private static ExactRef exact(Path path)throws IOException {
        var measured=ControlBuild.FileRef.measure(path);return new ExactRef(measured.path(),measured.bytes(),measured.sha256());
    }
    /** OPEN_EXISTING plus tryLock, without writing lock contents. */
    private static void assertAllocationLock(Path path,boolean available)throws IOException {
        boolean actual=false;
        try(var channel=FileChannel.open(path,StandardOpenOption.WRITE)){
            try(FileLock acquired=channel.tryLock()){actual=acquired!=null;}
            catch(OverlappingFileLockException held){actual=false;}
        }
        assertEquals(available,actual,"original allocation lock must reflect actual business storage ownership");
    }
}
