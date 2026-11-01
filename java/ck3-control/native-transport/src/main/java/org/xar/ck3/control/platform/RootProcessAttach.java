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
    /** Real current saved-owner attachment proof. It carries no Job, launch or Started capability. */
    public static final class LoadedCustody implements AutoCloseable {
        private final ManagedGameSession attached;
        private final CheckpointPair pair;
        private final GameSupervisorControl.Descriptor owner;
        private final SharedSourceFiles.Witness descriptor, save, currentHello, receipt;
        private final ExactRef descriptorRef;
        private final Instant deadline;
        private final Path directory;
        private final Thread thread=Thread.currentThread();
        private WindowsJobProcess.ReadOnlyProcessHandle ownerHandle;
        private Win32Host.Mutex mutex;
        private SteamOfflineProbe.QualifiedOffline offline;
        private boolean released,closed;
        private LoadedCustody(ManagedGameSession attached,CheckpointPair pair,GameSupervisorControl.Descriptor owner,
                ExactRef descriptorRef,SharedSourceFiles.Witness descriptor,SharedSourceFiles.Witness save,
                SharedSourceFiles.Witness currentHello,SharedSourceFiles.Witness receipt,Instant deadline,Path directory,
                WindowsJobProcess.ReadOnlyProcessHandle ownerHandle,Win32Host.Mutex mutex,SteamOfflineProbe.QualifiedOffline offline) {
            this.attached=attached;this.pair=pair;this.owner=owner;this.descriptorRef=descriptorRef;this.descriptor=descriptor;
            this.save=save;this.currentHello=currentHello;this.receipt=receipt;this.deadline=deadline;this.directory=directory;
            this.ownerHandle=ownerHandle;this.mutex=mutex;this.offline=offline;
        }
        public ManagedGameSession game(){return attached;}
        public CheckpointPair pair(){return pair;}
        public Path evidenceDirectory(){return directory;}
        public Instant deadline(){return deadline;}
        public ExactRef evidence(){return exact(receipt.source());}
        public synchronized void requireEvidence()throws IOException {
            requireWitness(descriptor);requireWitness(currentHello);requireWitness(receipt);
            readLoaded(owner.nativeHello(),ColdBootstrapJson.MAX_BYTES);readLoaded(owner.launchEvidence(),ColdBootstrapJson.MAX_BYTES);
        }
        public synchronized void requireCurrent()throws IOException {
            if(closed||released)throw new IOException("Loaded saved preparation is closed or already released");
            Win32Host.deadline(deadline);
            if(Thread.currentThread()!=thread)throw new IOException("Loaded saved preparation escaped its actual mutex thread");
            mutex.requireHeld();offline.verify();requireEvidence();
            readLoaded(descriptorRef,GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
            requireLoadedOwner(attached,owner,ownerHandle,deadline);
            var reread=GameSupervisorControl.readDescriptor(Path.of(descriptorRef.path()));
            if(!reread.equals(owner))throw new IOException("Original saved owner descriptor changed");
            new NativeCheckpointFiles().verify(pair);requireWitness(save);requireLoadedSave(attached,pair);
            var expected=readLoaded(exact(currentHello.source()),ColdBootstrapJson.MAX_BYTES);
            if(!Arrays.equals(expected,attached.nativeTransport().originalHello().packet().value()))
                throw new IOException("Actual attached HELLO changed during saved admission");
        }
        public synchronized void releasePreparation()throws IOException {
            requireCurrent();release();released=true;
        }
        private void release()throws IOException {
            IOException failure=null;
            if(offline!=null){try{offline.close();}catch(IOException ex){failure=ex;}finally{offline=null;}}
            if(mutex!=null){try{mutex.close();}catch(IOException ex){if(failure==null)failure=ex;else failure.addSuppressed(ex);}finally{mutex=null;}}
            if(ownerHandle!=null){try{ownerHandle.close();}catch(RuntimeException ex){var io=new IOException("Loaded owner observer close failed",ex);if(failure==null)failure=io;else failure.addSuppressed(io);}finally{ownerHandle=null;}}
            if(failure!=null)throw failure;
        }
        @Override public synchronized void close()throws IOException {if(!closed){closed=true;release();}}
    }

    public static LoadedCustody retainLoadedSaved(ManagedGameSession attached,ExactRef ownerDescriptor,
            CheckpointPair pair,Path freshEvidenceRoot,Instant readDeadline)throws IOException,InterruptedException {
        Objects.requireNonNull(attached);Objects.requireNonNull(ownerDescriptor);Objects.requireNonNull(pair);
        Objects.requireNonNull(freshEvidenceRoot);Objects.requireNonNull(readDeadline);Win32Host.deadline(readDeadline);
        if(attached.mode()!=ManagedGameSession.Mode.ATTACHED||attached.generation().equals(pair.frame().game()))
            throw new IOException("Loaded saved admission requires a genuine attached new Game generation");
        readLoaded(ownerDescriptor,GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
        var descriptor=SharedSourceFiles.observe(Path.of(ownerDescriptor.path()));
        if(descriptor.source().bytes()!=ownerDescriptor.bytes()||!descriptor.source().sha256().equals(ownerDescriptor.sha256()))
            throw new IOException("Actual owner descriptor witness differs from the exact input reference");
        var owner=GameSupervisorControl.readDescriptor(Path.of(ownerDescriptor.path()));
        if(!Path.of(ownerDescriptor.path()).toAbsolutePath().normalize().getParent().equals(owner.stopRequestPath().getParent()))
            throw new IOException("Actual saved owner descriptor/control roots differ");
        Path parent=attached.launchPlan().evidenceRoot().toRealPath();
        if(!freshEvidenceRoot.isAbsolute()||!freshEvidenceRoot.normalize().equals(freshEvidenceRoot)
                ||!freshEvidenceRoot.getParent().toRealPath().equals(parent))
            throw new IOException("Loaded saved evidence must be a fresh immediate approved child");
        SharedSourceFiles.plainAncestors(freshEvidenceRoot);Files.createDirectory(freshEvidenceRoot);
        WindowsJobProcess.ReadOnlyProcessHandle ownerHandle=null;Win32Host.Mutex mutex=null;
        SteamOfflineProbe.QualifiedOffline offline=null;
        try {
            ownerHandle=WindowsJobProcess.retainReadOnlyProcess(owner.supervisorIdentity().pid());
            mutex=Win32Host.mutex("Local\\XarJavaGameLifecycle-v1",readDeadline);
            requireLoadedOwner(attached,owner,ownerHandle,readDeadline);
            var steam=attached.launchPlan().steam();
            offline=SteamOfflineProbe.observe(new SteamOfflineProbe.Plan(steam.machineId(),steam.steamExecutable(),readDeadline),freshEvidenceRoot.resolve("steam-offline.json"));
            offline.verify();var observed=Instant.parse(offline.observation().common().observedAtUtc());
            if(observed.isAfter(Instant.now())||Duration.between(observed,Instant.now()).compareTo(Duration.ofSeconds(10))>0)
                throw new IOException("Fresh background Steam observation required for loaded saved admission");
            new NativeCheckpointFiles().verify(pair);requireLoadedSave(attached,pair);
            var save=SharedSourceFiles.observe(Path.of(pair.save().reference().path()));
            byte[] hello=attached.nativeTransport().originalHello().packet().value();
            Path helloPath=freshEvidenceRoot.resolve("attached-hello.packet");write(helloPath,hello);
            var helloWitness=SharedSourceFiles.observe(helloPath);
            write(freshEvidenceRoot.resolve("process-inventory.json"),ControlBuild.strictMapper().writeValueAsBytes(Win32Host.processInventory("ck3.exe",readDeadline)));
            var row=org.xar.ck3.control.contracts.StrictJson.object();
            row.put("schema","xar.java-loaded-saved-physical/v1");row.put("machine_id",attached.machineId());
            row.put("request_id",attached.launchPlan().requestId());row.put("session_id",attached.sessionId());
            row.set("owner_descriptor",ownerDescriptor.toJson());row.set("owner",GameSupervisorControl.identity(owner.supervisorIdentity()));
            row.set("game",GameSupervisorControl.identity(attached.identity()));row.set("original_native_hello",owner.nativeHello().toJson());
            row.set("launch_evidence",owner.launchEvidence().toJson());row.set("actual_native_hello",exact(helloWitness.source()).toJson());
            row.set("save",pair.save().reference().toJson());row.put("observed_at_utc",Instant.now().toString());
            row.put("read_admission_deadline_utc",readDeadline.toString());row.put("original_launch_deadline_utc",attached.launchPlan().deadline().toString());
            row.put("job_or_launch_permission",false);
            Path receiptPath=freshEvidenceRoot.resolve("loaded-saved-physical.json");write(receiptPath,org.xar.ck3.control.contracts.StrictJson.canonical(row,ColdBootstrapJson.MAX_BYTES));
            LoadedCustody result=new LoadedCustody(attached,pair,owner,ownerDescriptor,descriptor,save,helloWitness,
                    SharedSourceFiles.observe(receiptPath),readDeadline,freshEvidenceRoot,ownerHandle,mutex,offline);
            result.requireCurrent();return result;
        }catch(IOException|RuntimeException|InterruptedException failure) {
            if(offline!=null)try{offline.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
            if(mutex!=null)try{mutex.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
            if(ownerHandle!=null)try{ownerHandle.close();}catch(RuntimeException cleanup){failure.addSuppressed(cleanup);}
            throw failure;
        }
    }

    private static void requireLoadedOwner(ManagedGameSession game,GameSupervisorControl.Descriptor owner,
            WindowsJobProcess.ReadOnlyProcessHandle handle,Instant readDeadline)throws IOException {
        Win32Host.deadline(readDeadline);game.verify();sources(game);
        if(handle==null||handle.waitZero()!=258L||!handle.identity().equals(owner.supervisorIdentity())
                ||!game.identity().equals(owner.gameIdentity())||!game.machineId().equals(owner.machineId())
                ||!game.sessionId().equals(owner.sessionId())
                ||new java.math.BigInteger(owner.supervisorIdentity().creationFiletimeDecimal()).compareTo(new java.math.BigInteger(game.identity().creationFiletimeDecimal()))>=0
                ||!NativeLaunchPlanCodec.toJson(owner.configuration()).equals(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(game.launchPlan()))))
            throw new IOException("Loaded saved owner, Game birth, complete plan or source identity differs");
        requireInventory(Win32Host.processInventory("ck3.exe",readDeadline),game.identity(),owner.supervisorIdentity().pid());
        byte[] original=readLoaded(owner.nativeHello(),ColdBootstrapJson.MAX_BYTES);
        var decoded=org.xar.ck3.control.nativebridge.NativeWire.decode(original);
        if(!(decoded instanceof org.xar.ck3.control.nativebridge.NativeWire.Hello before))throw new IOException("Original saved owner HELLO is absent");
        var transport=game.nativeTransport();var now=transport.originalHello();var diagnostic=transport.diagnostics();
        var session=diagnostic.session().orElseThrow(()->new IOException("Actual loaded saved Native session absent"));
        var access=game.presentationAccess();access.requireOwner(game);access.actualGuard().verify(game.generation());
        var config=access.actualConfig();
        if(diagnostic.receivedState()!=org.xar.ck3.control.nativebridge.NativeGameTransport.ReceivedState.HELLO_VERIFIED
                ||diagnostic.terminalFailure().isPresent()||!session.game().equals(game.generation())
                ||!session.machineId().equals(game.machineId())||!session.sessionId().equals(game.sessionId())
                ||!config.pipeName().equals(game.launchPlan().pipeName())||before.pid()!=now.pid()||now.pid()!=game.identity().pid()
                ||!before.buildMatch()||!now.buildMatch()||!before.bridgeVersion().equals(now.bridgeVersion())
                ||!before.gameSha256().equals(now.gameSha256())||!before.adapterId().equals(now.adapterId())
                ||!before.adapterStatus().equals(now.adapterStatus())||!before.capabilities().equals(now.capabilities())
                ||now.connectionGeneration().compareTo(before.connectionGeneration())<0)
            throw new IOException("Original launch HELLO and actual reconnected Native custody differ");
        byte[] launch=readLoaded(owner.launchEvidence(),ColdBootstrapJson.MAX_BYTES);
        var event=ControlBuild.strictMapper().readTree(launch);var birth=event.path("game");
        if(!"xar.java-game-lifecycle-event/v1".equals(event.path("schema").asText())||!"HELLO".equals(event.path("event").asText())
                ||!game.machineId().equals(event.path("machine_id").asText())||!game.sessionId().equals(event.path("session_id").asText())
                ||!game.launchPlan().requestId().equals(event.path("request_id").asText())||birth.path("pid").longValue()!=game.identity().pid()
                ||!game.identity().creationFiletimeDecimal().equals(birth.path("creation_filetime_decimal").asText())
                ||!game.identity().executable().equals(birth.path("executable").asText()))
            throw new IOException("Original loaded Saved launch evidence differs from actual parented Game");
        game.verify();
    }
    private static byte[] readLoaded(ExactRef reference,int maximum)throws IOException {
        if(reference.bytes()<1||reference.bytes()>maximum)throw new IOException("Finite loaded saved original required");
        Path path=Path.of(reference.path());var before=SharedSourceFiles.observe(path);
        if(before.source().bytes()!=reference.bytes()||!before.source().sha256().equals(reference.sha256())
                ||!Path.of(before.source().path()).toAbsolutePath().normalize().equals(path.toAbsolutePath().normalize()))
            throw new IOException("Loaded saved original bytes/SHA/path differ");
        byte[] raw;try(var input=Files.newInputStream(path)){raw=input.readNBytes(maximum+1);}
        String digest;try{digest=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IOException(impossible);}
        if(raw.length!=reference.bytes()||!digest.equals(reference.sha256())||!before.equals(SharedSourceFiles.observe(path)))
            throw new IOException("Loaded saved original changed during bounded read");
        return raw;
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
