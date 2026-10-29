package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;

/** Revalidates the new daemon's actual Saved creator. A PID, descriptor or old daemon ticket cannot enter. */
public final class RootProcessAttach {
    private RootProcessAttach() { }

    /** A live original creator capability; its private constructor is never a JSON decoder. */
    public static final class Custody implements AutoCloseable {
        private final JavaGameLifecycle issuer;
        private final JavaGameLifecycle.Started started;
        private final CheckpointPair pair;
        private final Path directory;
        private final Instant deadline;
        private final Thread thread;
        private final SharedSourceFiles.Witness save;
        private final ExactRef evidence;
        private final SharedSourceFiles.Witness evidenceWitness;
        private final ColdBootstrapJson.PhysicalData data;
        private Win32Host.Mutex mutex;
        private SteamOfflineProbe.QualifiedOffline offline;
        private boolean released,closed;
        private Custody(JavaGameLifecycle issuer,JavaGameLifecycle.Started started,CheckpointPair pair,Path directory,
                Instant deadline,SharedSourceFiles.Witness save,ExactRef evidence,SharedSourceFiles.Witness evidenceWitness,
                ColdBootstrapJson.PhysicalData data,Win32Host.Mutex mutex,SteamOfflineProbe.QualifiedOffline offline) {
            this.issuer=issuer;this.started=started;this.pair=pair;this.directory=directory;this.deadline=deadline;
            this.thread=Thread.currentThread();this.save=save;this.evidence=evidence;this.evidenceWitness=evidenceWitness;
            this.data=data;this.mutex=mutex;this.offline=offline;
        }
        public ManagedGameSession game(){return started.session();}
        public CheckpointPair pair(){return pair;}
        public Path evidenceDirectory(){return directory;}
        public Instant deadline(){return deadline;}
        public ExactRef evidence(){return evidence;}
        public ColdBootstrapJson.PhysicalData data(){return data;}
        /** Historical file facts do not grant current transport or process authority. */
        public synchronized void requireEvidence()throws IOException {
            requireWitness(evidenceWitness);requireExact(started.nativeHello());requireExact(started.launchEvidence());
        }
        public synchronized void requireCurrent()throws IOException {
            if(closed)throw new IOException("Cold creator custody was closed");
            issuer.requireColdStarted(started,deadline);sources(game());requireEvidence();
            new NativeCheckpointFiles().verify(pair);requireWitness(save);requireLoadedSave(game(),pair);
            requireHello(started);requireInventory(Win32Host.processInventory("ck3.exe",deadline),game().identity(),ProcessHandle.current().pid());
            if(!released){
                if(Thread.currentThread()!=thread)throw new IOException("Cold preparation escaped its original mutex thread");
                mutex.requireHeld();offline.verify();
            }
            issuer.requireColdStarted(started,deadline);
        }
        /** Called only after the canonical writer has committed and the real Driver adopter has returned. */
        public synchronized void releasePreparation()throws IOException {
            if(released||closed)throw new IOException("Cold preparation was already released or closed");
            requireCurrent();release();released=true;
        }
        private void release()throws IOException {
            IOException failure=null;
            if(offline!=null){try{offline.close();}catch(IOException problem){failure=problem;}finally{offline=null;}}
            if(mutex!=null){try{mutex.close();}catch(IOException problem){if(failure==null)failure=problem;else failure.addSuppressed(problem);}finally{mutex=null;}}
            if(failure!=null)throw failure;
        }
        /** Closing this proof never terminates, reopens or adopts a Game process. */
        @Override public synchronized void close()throws IOException {if(!closed){closed=true;release();}}
    }

    public static Custody retain(JavaGameLifecycle issuer,JavaGameLifecycle.Started originalStart,CheckpointPair pair,
            Path freshEvidenceRoot,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(issuer);Objects.requireNonNull(originalStart);Objects.requireNonNull(pair);
        Objects.requireNonNull(freshEvidenceRoot);Objects.requireNonNull(deadline);
        issuer.requireColdStarted(originalStart,deadline);ManagedGameSession game=originalStart.session();sources(game);
        Path parent=game.launchPlan().evidenceRoot().toRealPath();
        if(!freshEvidenceRoot.isAbsolute()||!freshEvidenceRoot.normalize().equals(freshEvidenceRoot)
                ||!freshEvidenceRoot.getParent().toRealPath().equals(parent))
            throw new IOException("Cold evidence must be a fresh immediate child of the actual approved launch evidence root");
        SharedSourceFiles.plainAncestors(freshEvidenceRoot);Files.createDirectory(freshEvidenceRoot);
        Win32Host.Mutex mutex=null;SteamOfflineProbe.QualifiedOffline offline=null;String stage="creator_mutex";
        try {
            mutex=issuer.retainColdBootstrapMutex(originalStart,deadline);stage="fresh_background_steam";
            var steam=game.launchPlan().steam();
            offline=SteamOfflineProbe.observe(new SteamOfflineProbe.Plan(steam.machineId(),steam.steamExecutable(),deadline),freshEvidenceRoot.resolve("steam-offline.json"));
            offline.verify();Instant now=Instant.now(),observed=Instant.parse(offline.observation().common().observedAtUtc());
            if(observed.isAfter(now)||Duration.between(observed,now).compareTo(Duration.ofSeconds(10))>0)
                throw new IOException("Fresh background Steam offline observation is required for this cold preparation");
            stage="saved_file_identity";new NativeCheckpointFiles().verify(pair);requireLoadedSave(game,pair);
            SharedSourceFiles.Witness save=SharedSourceFiles.observe(Path.of(pair.save().reference().path()));
            stage="actual_process_inventory";Win32Host.ProcessInventory inventory=Win32Host.processInventory("ck3.exe",deadline);
            requireInventory(inventory,game.identity(),ProcessHandle.current().pid());
            write(freshEvidenceRoot.resolve("process-inventory.json"),ControlBuild.strictMapper().writeValueAsBytes(inventory));
            stage="owned_native_hello";requireHello(originalStart);
            var transport=game.nativeTransport().diagnostics().session().orElseThrow(()->new IOException("Original transport session is absent"));
            ColdBootstrapJson.PhysicalData data=new ColdBootstrapJson.PhysicalData("xar.java-cold-physical-bootstrap/v1",
                    game.machineId(),game.launchPlan().requestId(),game.sessionId(),game.identity(),game.launchPlan().pipeName(),
                    transport.connectionGeneration().toString(),originalStart.nativeHello(),exact(offline.evidence()),originalStart.launchEvidence(),
                    pair.save().reference(),pair.save().identity(),save.nativeFile(),Instant.now().toString(),deadline.toString());
            Path receipt=freshEvidenceRoot.resolve("physical-bootstrap.json");write(receipt,ColdBootstrapJson.encodePhysical(data));
            SharedSourceFiles.Witness witness=SharedSourceFiles.observe(receipt);
            Custody result=new Custody(issuer,originalStart,pair,freshEvidenceRoot,deadline,save,exact(witness.source()),witness,data,mutex,offline);
            result.requireCurrent();return result;
        }catch(IOException|RuntimeException|InterruptedException failure){
            try{write(freshEvidenceRoot.resolve("failure.json"),ControlBuild.strictMapper().writeValueAsBytes(new Failure(
                    "xar.java-cold-physical-failure/v1",game.machineId(),game.launchPlan().requestId(),stage,
                    failure.getClass().getName(),bounded(failure.getMessage()),Instant.now().toString())));}catch(IOException proof){failure.addSuppressed(proof);}
            if(offline!=null)try{offline.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
            if(mutex!=null)try{mutex.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
            throw failure;
        }
    }
    private record Failure(String schema,String machineId,String requestId,String stage,String exceptionType,String detail,String observedAtUtc) { }
    static void requireInventory(Win32Host.ProcessInventory inventory,WindowsJobProcess.ProcessIdentity expected,long actualCreatorPid)throws IOException {
        if(!"ck3.exe".equalsIgnoreCase(inventory.exactName()))throw new IOException("Wrong exact Game inventory");
        List<Win32Host.ProcessRow> running=inventory.qualifiedRunning();
        if(running.size()!=1||!running.get(0).identity().equals(expected)||running.get(0).parentPid()!=actualCreatorPid)
            throw new IOException("Cold bootstrap requires the sole exact running Game created and retained by this new Java daemon");
    }
    private static void sources(ManagedGameSession game)throws IOException {
        game.launchPlan().sources().verify();game.launchPlan().preparedProfile().verify(game.launchPlan());
        for(Class<?> type:List.of(RootProcessAttach.class,Custody.class,ColdBootstrapJson.class,ColdBootstrapJson.PhysicalData.class,
                ColdBootstrapJson.AdoptionData.class,Failure.class))game.launchPlan().sources().requireLoadedClass(type);
    }
    private static void requireLoadedSave(ManagedGameSession game,CheckpointPair pair)throws IOException {
        if(!(game.launchPlan().load() instanceof NativeLaunchPlan.SavedGame saved)||!exact(saved.save()).equals(pair.save().reference()))
            throw new IOException("Actual new Java Saved launch does not name the original exact checkpoint SAVE");
    }
    private static void requireHello(JavaGameLifecycle.Started started)throws IOException {
        ManagedGameSession game=started.session();var access=game.presentationAccess();access.requireOwner(game);
        access.actualGuard().verify(game.generation());var config=access.actualConfig();var transport=game.nativeTransport();
        var diagnostic=transport.diagnostics();var session=diagnostic.session().orElseThrow(()->new IOException("Original native session absent"));
        if(diagnostic.receivedState()!=org.xar.ck3.control.nativebridge.NativeGameTransport.ReceivedState.HELLO_VERIFIED
                ||diagnostic.terminalFailure().isPresent()||!session.game().equals(game.generation())
                ||!session.sessionId().equals(game.sessionId())||!session.machineId().equals(game.machineId())
                ||!config.pipeName().equals(game.launchPlan().pipeName()))throw new IOException("Original live owned Native HELLO/session differs");
        requireExact(started.nativeHello());byte[] original=Files.readAllBytes(Path.of(started.nativeHello().path()));
        if(!Arrays.equals(original,transport.originalHello().packet().value()))throw new IOException("Retained launch HELLO differs from actual owned transport");
        access.requireOwner(game);
    }
    private static void requireWitness(SharedSourceFiles.Witness witness)throws IOException {
        if(!witness.equals(SharedSourceFiles.observe(Path.of(witness.source().path()))))throw new IOException("Cold original file identity or content changed");
    }
    private static void requireExact(ExactRef ref)throws IOException {
        if(ref.bytes()<1||ref.bytes()>ColdBootstrapJson.MAX_BYTES||!exact(ControlBuild.FileRef.measure(Path.of(ref.path()))).equals(ref))
            throw new IOException("Bounded original cold evidence changed");
    }
    private static ExactRef exact(ControlBuild.FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static String bounded(String value){String text=value==null?"":value;return text.substring(0,Math.min(text.length(),2048));}
    private static void write(Path path,byte[] bytes)throws IOException {
        if(bytes.length<1||bytes.length>ColdBootstrapJson.MAX_BYTES)throw new IOException("Cold evidence exceeds finite byte limit");
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
    }
}
