package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

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
        private final NativeSavedGameClone.Observation savedClone;
        private final SharedSourceFiles.Witness cloneEvidence;
        private final ExactRef evidence;
        private final SharedSourceFiles.Witness evidenceWitness;
        private final ColdBootstrapJson.PhysicalData data;
        private Win32Host.Mutex mutex;
        private SteamOfflineProbe.QualifiedOffline offline;
        private boolean released,closed;
        private Custody(JavaGameLifecycle issuer,JavaGameLifecycle.Started started,CheckpointPair pair,Path directory,
                Instant deadline,SharedSourceFiles.Witness save,NativeSavedGameClone.Observation savedClone,
                SharedSourceFiles.Witness cloneEvidence,ExactRef evidence,SharedSourceFiles.Witness evidenceWitness,
                ColdBootstrapJson.PhysicalData data,Win32Host.Mutex mutex,SteamOfflineProbe.QualifiedOffline offline) {
            this.issuer=issuer;this.started=started;this.pair=pair;this.directory=directory;this.deadline=deadline;
            this.thread=Thread.currentThread();this.save=save;this.savedClone=savedClone;this.cloneEvidence=cloneEvidence;
            this.evidence=evidence;this.evidenceWitness=evidenceWitness;
            this.data=data;this.mutex=mutex;this.offline=offline;
        }
        public ManagedGameSession game(){return started.session();}
        public CheckpointPair pair(){return pair;}
        public NativeSavedGameClone.Observation savedClone(){return savedClone;}
        public Path evidenceDirectory(){return directory;}
        public Instant deadline(){return deadline;}
        public ExactRef evidence(){return evidence;}
        public ColdBootstrapJson.PhysicalData data(){return data;}
        /** Historical file facts do not grant current transport or process authority. */
        public synchronized void requireEvidence()throws IOException {
            requireWitness(evidenceWitness);requireWitness(cloneEvidence);requireExact(started.nativeHello());requireExact(started.launchEvidence());
        }
        public synchronized void requireCurrent()throws IOException {
            if(closed)throw new IOException("Cold creator custody was closed");
            issuer.requireColdStarted(started,deadline);sources(game());requireEvidence();
            new NativeCheckpointFiles().verify(pair);requireWitness(save);requireLoadedSave(game(),pair);
            savedClone.requireCurrent(game().launchPlan(),pair.save());
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
            var savedClone=NativeSavedGameClone.observe(game.launchPlan(),pair.save());
            Path clonePath=freshEvidenceRoot.resolve("saved-source-clone.json");
            write(clonePath,StrictJson.canonical(savedClone.toJson(),ColdBootstrapJson.MAX_BYTES));
            var cloneEvidence=SharedSourceFiles.observe(clonePath);
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
            Custody result=new Custody(issuer,originalStart,pair,freshEvidenceRoot,deadline,save,savedClone,cloneEvidence,exact(witness.source()),witness,data,mutex,offline);
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
        private final NativeSavedGameClone.Observation savedClone;
        private final ImportedLoadedOriginals imported;
        private final SharedSourceFiles.Witness cloneEvidence;
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
                SharedSourceFiles.Witness currentHello,SharedSourceFiles.Witness receipt,
                NativeSavedGameClone.Observation savedClone,SharedSourceFiles.Witness cloneEvidence,ImportedLoadedOriginals imported,Instant deadline,Path directory,
                WindowsJobProcess.ReadOnlyProcessHandle ownerHandle,Win32Host.Mutex mutex,SteamOfflineProbe.QualifiedOffline offline) {
            this.attached=attached;this.pair=pair;this.owner=owner;this.descriptorRef=descriptorRef;this.descriptor=descriptor;
            this.save=save;this.currentHello=currentHello;this.receipt=receipt;this.savedClone=savedClone;
            this.cloneEvidence=cloneEvidence;this.imported=imported;this.deadline=deadline;this.directory=directory;
            this.ownerHandle=ownerHandle;this.mutex=mutex;this.offline=offline;
        }
        public ManagedGameSession game(){return attached;}
        public CheckpointPair pair(){return pair;}
        public NativeSavedGameClone.Observation savedClone(){return savedClone;}
        public Path evidenceDirectory(){return directory;}
        public Instant deadline(){return deadline;}
        public ExactRef evidence(){return exact(receipt.source());}
        /** Lexical custody only; it neither rereads evidence nor queries a process. */
        synchronized void requireMembership(Instant until)throws IOException {
            if(closed||released||Thread.currentThread()!=thread||mutex==null||until==null||until.isAfter(deadline)
                    ||!Instant.now().isBefore(until)||!Instant.now().isBefore(deadline))throw new IOException("Loaded custody lost its original thread or finite source membership");
            mutex.requireHeld();
        }
        public synchronized void requireEvidence()throws IOException {
            requireWitness(descriptor);requireWitness(currentHello);requireWitness(receipt);requireWitness(cloneEvidence);
            readLoaded(owner.nativeHello(),ColdBootstrapJson.MAX_BYTES);readLoaded(owner.launchEvidence(),ColdBootstrapJson.MAX_BYTES);
        }
        public synchronized void requireCurrent()throws IOException {
            if(closed||released)throw new IOException("Loaded saved preparation is closed or already released");
            Win32Host.deadline(deadline);
            if(Thread.currentThread()!=thread)throw new IOException("Loaded saved preparation escaped its actual mutex thread");
            mutex.requireHeld();offline.verify();requireEvidence();
            byte[] descriptorBytes=readLoaded(descriptorRef,GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
            requireLoadedOwner(attached,owner,ownerHandle,deadline,imported!=null);
            var reread=GameSupervisorControl.readCapturedDescriptor(descriptorRef,descriptorBytes);
            if(!reread.equals(owner))throw new IOException("Original saved owner descriptor changed");
            new NativeCheckpointFiles().verify(pair);requireWitness(save);
            if(imported==null)requireLoadedSave(attached,pair);
            else imported.requireClone(attached.launchPlan(),savedClone);
            savedClone.requireCurrent(attached.launchPlan(),pair.save());
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

    /** Closed actual replacement-control wire. Its decoded value is evidence, never a process capability. */
    record LoadedReplacementControl(String parentId,GameGeneration previous,ExactRef save,ExactRef stopped,ExactRef launched){ }
    static LoadedReplacementControl decodeLoadedReplacementControl(byte[] bytes)throws IOException {
        try{
            var row=StrictJson.object(StrictJson.parse(bytes,65536),java.util.Set.of("schema","parent_lifecycle_intent_id","phase","old_pid","old_birth_decimal","save","stop_evidence","launch_evidence"));
            if(!"xar.java-game-replacement/v1".equals(StrictJson.text(row.get("schema")))
                    ||!"EXITED_SOURCE_NEW_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED".equals(StrictJson.text(row.get("phase"))))throw new IOException("original exited replacement has not retained its genuine new HELLO");
            String parent=StrictJson.text(row.get("parent_lifecycle_intent_id"));if(parent.length()>256)throw new IOException("bounded original replacement parent required");
            return new LoadedReplacementControl(parent,new GameGeneration(StrictJson.integer(row.get("old_pid"),1,4294967295L),GameGeneration.parseCreationFiletime(row.get("old_birth_decimal"))),
                    ExactRef.fromJson(row.get("save")),ExactRef.fromJson(row.get("stop_evidence")),ExactRef.fromJson(row.get("launch_evidence")));
        }catch(IllegalArgumentException invalid){throw new IOException("invalid original snake-case replacement control",invalid);}
    }
    record ImportedLoadedControl(LoadedReplacementControl replacement,ExactRef transferProof) { }

    static ImportedLoadedControl decodeImportedLoadedControl(byte[] parent,byte[] generation)throws IOException {
        if(!Arrays.equals(parent,generation))throw new IOException("Imported parent control and generation claim have different original bytes");
        try {
            var row=StrictJson.object(StrictJson.parse(parent,65536),Set.of("schema","parent_lifecycle_intent_id","phase",
                    "old_pid","old_birth_decimal","save","stop_evidence","launch_evidence","imported_save_transfer"));
            if(!RestoreCheckpointService.IMPORTED_REPLACEMENT_SCHEMA.equals(StrictJson.text(row.get("schema")))
                    ||!"EXITED_SOURCE_NEW_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED".equals(StrictJson.text(row.get("phase"))))
                throw new IOException("Imported replacement must have its original accepted HELLO in both controls");
            var parentId=StrictJson.text(row.get("parent_lifecycle_intent_id"));
            if(parentId.length()>256)throw new IOException("Bounded original imported replacement parent required");
            var old=new GameGeneration(StrictJson.integer(row.get("old_pid"),1,4294967295L),
                    GameGeneration.parseCreationFiletime(row.get("old_birth_decimal")));
            var replacement=new LoadedReplacementControl(parentId,old,ExactRef.fromJson(row.get("save")),
                    ExactRef.fromJson(row.get("stop_evidence")),ExactRef.fromJson(row.get("launch_evidence")));
            return new ImportedLoadedControl(replacement,ExactRef.fromJson(row.get("imported_save_transfer")));
        } catch(IllegalArgumentException invalid) {
            throw new IOException("Invalid original imported replacement control",invalid);
        }
    }

    /** Exact pre-attachment DATA. This carries no process handle, launch, STOP or submission authority. */
    public static final class ImportedLoadedOriginals {
        private final ExactRef ownerRef,parentRef,generationRef;
        private final CheckpointPair pair;
        private final SessionIdentity departed;
        private final GameSupervisorControl.Descriptor owner;
        private final ImportedLoadedControl control;
        private final ExitedGameSource.Historical old;
        private final RestoreCheckpointService.ImportedSaveTransfer transfer;
        private final List<SharedSourceFiles.Witness> originals;

        private ImportedLoadedOriginals(ExactRef ownerRef,ExactRef parentRef,ExactRef generationRef,CheckpointPair pair,
                SessionIdentity departed,GameSupervisorControl.Descriptor owner,ImportedLoadedControl control,
                ExitedGameSource.Historical old,RestoreCheckpointService.ImportedSaveTransfer transfer,
                List<SharedSourceFiles.Witness> originals) {
            this.ownerRef=ownerRef;this.parentRef=parentRef;this.generationRef=generationRef;this.pair=pair;
            this.departed=departed;this.owner=owner;this.control=control;this.old=old;this.transfer=transfer;
            this.originals=List.copyOf(originals);
        }
        public GameSupervisorControl.Descriptor owner(){return owner;}
        public SessionIdentity departed(){return departed;}
        public CheckpointPair pair(){return pair;}
        public RestoreCheckpointService.ImportedSaveTransfer transfer(){return transfer;}
        public ExactRef oldSourceEvidence(){return old.source().currentObservation();}
        public ExactRef oldOwner(){return old.source().descriptorReference();}
        public void requireOriginals()throws IOException {
            for(var witness:originals){
                var ref=exact(witness.source());
                if(!captureLoaded(ref,(int)ref.bytes()).witness().equals(witness))
                    throw new IOException("Imported replacement original native file identity changed");
            }
            old.requireOriginals();
        }
        private void requireClone(NativeLaunchPlan plan,NativeSavedGameClone.Observation clone)throws IOException {
            if(!transfer.original().equals(clone.originalSave())||!transfer.staged().equals(clone.actualSave())
                    ||!NativeLaunchPlanCodec.describe(plan).equals(owner.configuration()))
                throw new IOException("Current imported LOAD does not retain the original pair and staged file identities");
            var raw=readLoaded(transfer.proof(),32*1024);
            if(!clone.toJson().equals(StrictJson.parse(raw,32*1024).get("clone")))
                throw new IOException("Current imported LOAD directory or file identity differs from original transfer");
        }
    }

    /** Reads only the finite producer originals. The caller supplies the parent derived from its unchanged journal. */
    public static ImportedLoadedOriginals readImportedLoadedOriginals(ExactRef ownerRef,ExactRef parentRef,
            ExactRef generationRef,CheckpointPair pair,SessionIdentity departed,String expectedParent)throws IOException {
        Objects.requireNonNull(pair);Objects.requireNonNull(departed);
        var control=decodeImportedLoadedControl(readLoaded(parentRef,65536),readLoaded(generationRef,65536));
        var replacement=control.replacement();
        if(!replacement.parentId().equals(expectedParent)||!replacement.previous().equals(departed.game()))
            throw new IOException("Imported replacement differs from the exact journal parent or departed owner");
        var owner=GameSupervisorControl.readCapturedDescriptor(ownerRef,readLoaded(ownerRef,GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES));
        var child=owner.configuration().accept();
        String oldKey=departed.machineId()+":"+departed.game().pid()+":"+departed.game().creationFiletime().value();
        Path controls=child.stateDirectory().resolve("control");
        if(!owner.machineId().equals(departed.machineId())||owner.generation().equals(departed.game())
                ||owner.generation().equals(pair.frame().game())||!owner.launchEvidence().equals(replacement.launched())
                ||!child.requestId().equals(JavaGameLifecycle.replacementRequestId(expectedParent))
                ||!Path.of(parentRef.path()).equals(controls.resolve(child.requestId()+"-parent.json"))
                ||!Path.of(generationRef.path()).equals(controls.resolve("exited-generation-"+JavaGameLifecycle.replacementRequestId(oldKey)+".json")))
            throw new IOException("Imported replacement owner, Game birth or original control paths differ");
        Path staged=ImportedSavedGameTransfer.stagedPath(child,expectedParent);
        if(!Path.of(control.transferProof().path()).equals(staged.resolveSibling(staged.getFileName()+".transfer.json")))
            throw new IOException("Imported transfer proof did not come from the staged load producer path");
        var transfer=ImportedSavedGameTransfer.decodeOriginal(readLoaded(control.transferProof(),32*1024),control.transferProof(),
                expectedParent,departed.game(),child);
        if(!transfer.original().equals(pair.save())||!transfer.staged().reference().equals(replacement.save()))
            throw new IOException("Imported control crossed the historical SAVE and staged LOAD roles");
        var old=ExitedGameSource.readHistorical(replacement.stopped(),departed.game());
        var oldOwner=old.source().descriptor();
        var expectedPlan=oldOwner.configuration().accept().savedReplacement(expectedParent,new ControlBuild.FileRef(
                replacement.save().path(),replacement.save().bytes(),replacement.save().sha256()),child.deadline());
        if(!oldOwner.machineId().equals(departed.machineId())||!oldOwner.sessionId().equals(departed.sessionId())
                ||!NativeLaunchPlanCodec.describe(expectedPlan).equals(owner.configuration()))
            throw new IOException("Imported replacement crossed its exact departed owner or Saved child plan");
        requireLoadedLaunchEvidence(owner);
        var hello=org.xar.ck3.control.nativebridge.NativeWire.decode(readLoaded(owner.nativeHello(),ColdBootstrapJson.MAX_BYTES));
        if(!(hello instanceof org.xar.ck3.control.nativebridge.NativeWire.Hello launchHello)||!launchHello.buildMatch()
                ||launchHello.pid()!=owner.gameIdentity().pid()||!launchHello.bridgeVersion().equals(child.bridgeVersion())
                ||!launchHello.gameSha256().equals(child.sources().review().gameExecutable().sha256())
                ||!launchHello.adapterId().equals(child.adapterId()))throw new IOException("Original imported launch HELLO differs from its exact owner build and child plan");
        var originals=new ArrayList<SharedSourceFiles.Witness>();
        for(var ref:List.of(ownerRef,parentRef,generationRef,owner.launchEvidence(),owner.nativeHello(),control.transferProof()))
            originals.add(captureLoaded(ref,(int)ref.bytes()).witness());
        return new ImportedLoadedOriginals(ownerRef,parentRef,generationRef,pair,departed,owner,control,old,transfer,originals);
    }

    /** A fresh Native attachment can read from the already-created successor only. No lifecycle call is made. */
    public static LoadedReplacement retainImportedLoadedReplacement(ManagedGameSession attached,ImportedLoadedOriginals imported,
            Path freshEvidenceRoot,Instant readDeadline)throws IOException,InterruptedException {
        Objects.requireNonNull(imported);Win32Host.deadline(readDeadline);
        Instant observed=Instant.now();
        if(readDeadline.isAfter(observed.plus(Duration.ofMinutes(45))))throw new IOException("Imported loaded source window must not exceed forty-five minutes");
        imported.requireOriginals();
        var custody=retainLoadedSaved(attached,imported.ownerRef,imported.pair,freshEvidenceRoot,readDeadline,imported);
        try {
            var result=new LoadedReplacement(custody,imported.control.replacement(),imported.old,imported.parentRef,
                    imported.generationRef,List.of(),observed,readDeadline);
            result.requireCurrent(readDeadline);return result;
        } catch(IOException|RuntimeException failure) {
            try{custody.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
            throw failure;
        }
    }

    /** Read-only existing occurrence. It never registers Started/Replaced or acquires Job/STOP/CREATE authority. */
    public static final class LoadedReplacement implements AutoCloseable {
        private final LoadedCustody custody;
        private final LoadedReplacementControl control;
        private final ExitedGameSource.Historical old;
        private final ExactRef parentControl,generationClaim;
        private final List<SharedSourceFiles.Witness> witnesses;
        private final Instant observedAt,deadline;
        private final Thread thread=Thread.currentThread();
        private final RestoreCheckpointService.ReplacementAck acknowledgement;
        private final SourceWindow window;
        private boolean closed;
        private LoadedReplacement(LoadedCustody custody,LoadedReplacementControl control,ExitedGameSource.Historical old,
                ExactRef parentControl,ExactRef generationClaim,List<SharedSourceFiles.Witness> witnesses,Instant observedAt,Instant deadline){
            this.custody=custody;this.control=control;this.old=old;this.parentControl=parentControl;this.generationClaim=generationClaim;
            this.witnesses=List.copyOf(witnesses);this.observedAt=observedAt;this.deadline=deadline;
            acknowledgement=new RestoreCheckpointService.ReplacementAck(control.parentId(),control.previous(),custody.game().generation(),control.save(),parentControl,
                    Optional.ofNullable(custody.imported).map(ImportedLoadedOriginals::transfer));window=new SourceWindow(this);
        }
        public ManagedGameSession attached(){return custody.game();}
        public CheckpointPair pair(){return custody.pair();}
        public String originalParentId(){return control.parentId();}
        public Instant originalDeadline(){return custody.owner.configuration().deadline();}
        public SessionIdentity previousOwner(){var descriptor=old.source().descriptor();return new SessionIdentity(descriptor.machineId(),descriptor.generation(),descriptor.sessionId());}
        public NativeLaunchPlanCodec.Configuration originalConfiguration(){return old.source().descriptor().configuration();}
        public String originalPipe(){return originalConfiguration().pipeName();}
        public ExactRef oldSourceEvidence(){return old.source().currentObservation();}
        public ExactRef oldOwner(){return old.source().descriptorReference();}
        public ExactRef parentControl(){return parentControl;}
        public ExactRef generationClaim(){return generationClaim;}
        public ExactRef ownerDescriptor(){return custody.descriptorRef;}
        public ExactRef launchEvidence(){return custody.owner.launchEvidence();}
        public ExactRef originalLaunchHello(){return custody.owner.nativeHello();}
        public ExactRef currentAttachedHello(){return exact(custody.currentHello.source());}
        /** Data only. Both Native receiver and private ReadWindow must requalify this exact instance. */
        public RestoreCheckpointService.ReplacementAck cachedAck(){return acknowledgement;}
        public Instant deadline(){return deadline;}
        public SourceWindow sourceWindow(){return window;}
        public List<ExactRef> originalReferences(){
            var refs=new java.util.LinkedHashSet<ExactRef>(old.references());refs.addAll(List.of(parentControl,generationClaim,ownerDescriptor(),launchEvidence(),originalLaunchHello(),currentAttachedHello(),custody.evidence()));
            acknowledgement.importedSaveTransfer().ifPresent(transfer->refs.add(transfer.proof()));return List.copyOf(refs);
        }
        public synchronized void requireMembership(Instant until)throws IOException {
            if(closed||Thread.currentThread()!=thread||window.owner!=this||until==null||until.isAfter(deadline)||!Instant.now().isBefore(until)||!Instant.now().isBefore(deadline))throw new IOException("Loaded replacement lost its exact finite source membership");
            custody.requireMembership(until);
        }
        /** Historical originals only: no submission-window renewal, process query or active-custody requirement. */
        public void requireOriginals()throws IOException {
            for(var witness:witnesses)requireWitness(witness);custody.requireEvidence();
            if(custody.imported!=null){custody.imported.requireOriginals();return;}
            old.requireOriginals();
            var parent=decodeLoadedReplacementControl(readLoaded(parentControl,65536));var generation=decodeLoadedReplacementControl(readLoaded(generationClaim,65536));
            if(!parent.equals(control)||!generation.equals(control))throw new IOException("original replacement control or generation claim changed");
        }
        public void requireCurrent()throws IOException {requireCurrent(deadline);}
        public synchronized void requireCurrent(Instant until)throws IOException {
            requireMembership(until);custody.requireCurrent();requireOriginals();ExitedGameSource.requireOldGenerationExited(old,until);requireMembership(until);
        }
        public void requireAck(RestoreCheckpointService.ReplacementAck actual,Instant until)throws IOException {
            if(actual!=acknowledgement)throw new IOException("Loaded replacement requires its privately retained exact ACK instance");requireCurrent(until);
        }
        /** Original lifecycle body only. A fresh READ window never edits these historical request fields. */
        public void requireOriginalRequest(RestoreCheckpointService.Request request)throws IOException {
            Objects.requireNonNull(request);SessionIdentity previous=previousOwner();
            if(!request.requestId().equals(originalParentId())||!request.deadline().equals(originalDeadline())||!request.pair().equals(pair())
                    ||!request.current().observed().game().equals(previous.game())||!request.current().observed().machineId().equals(previous.machineId())
                    ||!request.current().sessionId().equals(previous.sessionId()))throw new IOException("existing replacement changed its original request ID, deadline, previous owner or physical pair");
        }
        @Override public synchronized void close()throws IOException {if(Thread.currentThread()!=thread)throw new IOException("Loaded replacement close changed owning thread");if(!closed){closed=true;custody.close();}}
        /** Opaque current observation/adoption source; the historical launch/configuration deadlines remain unchanged. */
        public static final class SourceWindow {
            private final LoadedReplacement owner;
            private SourceWindow(LoadedReplacement owner){this.owner=owner;}
            public String machineId(){return owner.attached().machineId();}
            public GameGeneration game(){return owner.attached().generation();}
            public String sessionId(){return owner.attached().sessionId();}
            public Instant observedAt(){return owner.observedAt;}
            public Instant deadline(){return owner.deadline;}
            public List<ExactRef> refs(){return owner.originalReferences();}
            public void requireOwner(LoadedReplacement expected,Instant until)throws IOException {
                if(expected!=owner||owner.window!=this)throw new IOException("Loaded source window belongs to another physical role");owner.requireMembership(until);
            }
        }
    }
    public static LoadedReplacement qualifyLoadedReplacement(LoadedCustody actual,ExactRef parentControl,
            ExactRef generationClaim,CheckpointPair pair,Instant readDeadline)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(pair);Objects.requireNonNull(parentControl);Objects.requireNonNull(generationClaim);Win32Host.deadline(readDeadline);
        Instant observed=Instant.now();if(readDeadline.isAfter(observed.plus(Duration.ofMinutes(45))))throw new IOException("finite loaded source/adoption window must not exceed forty-five minutes");
        actual.requireMembership(readDeadline);actual.requireCurrent();
        if(actual.imported!=null||!actual.pair().equals(pair))throw new IOException("loaded replacement changed its exact physical saved pair or source role");
        LoadedReplacementControl control=decodeLoadedReplacementControl(readLoaded(parentControl,65536)),generation=decodeLoadedReplacementControl(readLoaded(generationClaim,65536));
        if(!control.equals(generation)||!control.save().equals(pair.save().reference())||!control.previous().equals(pair.frame().game())||!control.launched().equals(actual.owner.launchEvidence())
                ||!JavaGameLifecycle.replacementRequestId(control.parentId()).equals(actual.owner.configuration().requestId()))throw new IOException("loaded replacement changed its original parent, SAVE, old birth or new launch source");
        Path controls=actual.game().launchPlan().stateDirectory().resolve("control");
        String oldKey=actual.game().machineId()+":"+control.previous().pid()+":"+control.previous().creationFiletime().value();
        if(!Path.of(parentControl.path()).equals(controls.resolve(JavaGameLifecycle.replacementRequestId(control.parentId())+"-parent.json"))
                ||!Path.of(generationClaim.path()).equals(controls.resolve("exited-generation-"+JavaGameLifecycle.replacementRequestId(oldKey)+".json")))throw new IOException("loaded replacement control did not come from the exact original producer paths");
        var old=ExitedGameSource.readHistorical(control.stopped(),control.previous());var before=old.source().descriptor().configuration();var now=actual.owner.configuration();
        if(!before.profileDirectory().equals(now.profileDirectory())||!before.stateDirectory().equals(now.stateDirectory())
                ||!before.review().gameExecutable().equals(now.review().gameExecutable())||!old.source().descriptor().machineId().equals(actual.game().machineId()))throw new IOException("loaded replacement crossed the original profile/state/executable lineage");
        var witnesses=new java.util.ArrayList<SharedSourceFiles.Witness>();for(ExactRef ref:List.of(parentControl,generationClaim,actual.descriptorRef,actual.owner.launchEvidence(),actual.owner.nativeHello())){
            var witness=SharedSourceFiles.observe(Path.of(ref.path()));if(!exact(witness.source()).equals(ref))throw new IOException("loaded original witness differs from its exact reference");witnesses.add(witness);
        }
        LoadedReplacement result=new LoadedReplacement(actual,control,old,parentControl,generationClaim,witnesses,observed,readDeadline);result.requireCurrent(readDeadline);return result;
    }

    public static LoadedCustody retainLoadedSaved(ManagedGameSession attached,ExactRef ownerDescriptor,
            CheckpointPair pair,Path freshEvidenceRoot,Instant readDeadline)throws IOException,InterruptedException {
        return retainLoadedSaved(attached,ownerDescriptor,pair,freshEvidenceRoot,readDeadline,null);
    }

    private static LoadedCustody retainLoadedSaved(ManagedGameSession attached,ExactRef ownerDescriptor,
            CheckpointPair pair,Path freshEvidenceRoot,Instant readDeadline,ImportedLoadedOriginals imported)throws IOException,InterruptedException {
        Objects.requireNonNull(attached);Objects.requireNonNull(ownerDescriptor);Objects.requireNonNull(pair);
        Objects.requireNonNull(freshEvidenceRoot);Objects.requireNonNull(readDeadline);Win32Host.deadline(readDeadline);
        if(attached.mode()!=ManagedGameSession.Mode.ATTACHED||attached.generation().equals(pair.frame().game()))
            throw new IOException("Loaded saved admission requires a genuine attached new Game generation");
        byte[] descriptorBytes=readLoaded(ownerDescriptor,GameSupervisorControl.MAXIMUM_DESCRIPTOR_BYTES);
        var descriptor=SharedSourceFiles.observe(Path.of(ownerDescriptor.path()));
        if(descriptor.source().bytes()!=ownerDescriptor.bytes()||!descriptor.source().sha256().equals(ownerDescriptor.sha256()))
            throw new IOException("Actual owner descriptor witness differs from the exact input reference");
        var owner=GameSupervisorControl.readCapturedDescriptor(ownerDescriptor,descriptorBytes);
        if(imported!=null&&(!owner.equals(imported.owner)||!pair.equals(imported.pair)))
            throw new IOException("Imported loaded custody changed its qualified owner or historical pair");
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
            requireLoadedOwner(attached,owner,ownerHandle,readDeadline,imported!=null);
            var steam=attached.launchPlan().steam();
            offline=SteamOfflineProbe.observe(new SteamOfflineProbe.Plan(steam.machineId(),steam.steamExecutable(),readDeadline),freshEvidenceRoot.resolve("steam-offline.json"));
            offline.verify();var observed=Instant.parse(offline.observation().common().observedAtUtc());
            if(observed.isAfter(Instant.now())||Duration.between(observed,Instant.now()).compareTo(Duration.ofSeconds(10))>0)
                throw new IOException("Fresh background Steam observation required for loaded saved admission");
            new NativeCheckpointFiles().verify(pair);
            if(imported==null)requireLoadedSave(attached,pair);
            var save=SharedSourceFiles.observe(Path.of(pair.save().reference().path()));
            var savedClone=NativeSavedGameClone.observe(attached.launchPlan(),pair.save(),imported!=null);
            if(imported!=null)imported.requireClone(attached.launchPlan(),savedClone);
            Path clonePath=freshEvidenceRoot.resolve("saved-source-clone.json");
            write(clonePath,StrictJson.canonical(savedClone.toJson(),ColdBootstrapJson.MAX_BYTES));
            var cloneEvidence=SharedSourceFiles.observe(clonePath);
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
            row.set("save",pair.save().reference().toJson());
            if(imported!=null){
                row.put("schema","xar.java-imported-loaded-saved-physical/v2");
                row.set("staged_save",imported.transfer.staged().reference().toJson());
                row.set("imported_save_transfer",imported.transfer.proof().toJson());
            }
            row.put("observed_at_utc",Instant.now().toString());
            row.put("read_admission_deadline_utc",readDeadline.toString());row.put("original_launch_deadline_utc",attached.launchPlan().deadline().toString());
            row.put("job_or_launch_permission",false);
            Path receiptPath=freshEvidenceRoot.resolve("loaded-saved-physical.json");write(receiptPath,org.xar.ck3.control.contracts.StrictJson.canonical(row,ColdBootstrapJson.MAX_BYTES));
            LoadedCustody result=new LoadedCustody(attached,pair,owner,ownerDescriptor,descriptor,save,helloWitness,
                    SharedSourceFiles.observe(receiptPath),savedClone,cloneEvidence,imported,readDeadline,freshEvidenceRoot,ownerHandle,mutex,offline);
            result.requireCurrent();return result;
        }catch(IOException|RuntimeException|InterruptedException failure) {
            if(offline!=null)try{offline.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
            if(mutex!=null)try{mutex.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
            if(ownerHandle!=null)try{ownerHandle.close();}catch(RuntimeException cleanup){failure.addSuppressed(cleanup);}
            throw failure;
        }
    }

    private static void requireLoadedOwner(ManagedGameSession game,GameSupervisorControl.Descriptor owner,
            WindowsJobProcess.ReadOnlyProcessHandle handle,Instant readDeadline,boolean requireNewConnection)throws IOException {
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
                ||now.connectionGeneration().compareTo(before.connectionGeneration())<(requireNewConnection?1:0))
            throw new IOException("Original launch HELLO and actual reconnected Native custody differ");
        requireLoadedLaunchEvidence(owner);
        game.verify();
    }
    private static void requireLoadedLaunchEvidence(GameSupervisorControl.Descriptor owner)throws IOException {
        byte[] launch=readLoaded(owner.launchEvidence(),65536);
        var event=ControlBuild.strictMapper().readTree(launch);var birth=event.path("game");
        if(!"xar.java-game-lifecycle-event/v1".equals(event.path("schema").asText())||!"HELLO".equals(event.path("event").asText())
                ||!owner.machineId().equals(event.path("machine_id").asText())||!owner.sessionId().equals(event.path("session_id").asText())
                ||!owner.configuration().requestId().equals(event.path("request_id").asText())||birth.path("pid").longValue()!=owner.gameIdentity().pid()
                ||!owner.gameIdentity().creationFiletimeDecimal().equals(birth.path("creation_filetime_decimal").asText())
                ||!owner.gameIdentity().executable().equals(birth.path("executable").asText()))
            throw new IOException("Original loaded Saved launch evidence differs from actual parented Game");
    }
    private record LoadedOriginal(byte[] bytes,SharedSourceFiles.Witness witness) { }
    private static byte[] readLoaded(ExactRef reference,int maximum)throws IOException {
        return captureLoaded(reference,maximum).bytes();
    }
    private static LoadedOriginal captureLoaded(ExactRef reference,int maximum)throws IOException {
        if(reference.bytes()<1||reference.bytes()>maximum)throw new IOException("Finite loaded saved original required");
        Path path=Path.of(reference.path());
        var before=SharedSourceFiles.nativeFile(path);
        if(before.logicalBytes()!=reference.bytes())throw new IOException("Loaded saved original size differs");
        byte[] raw;try(var input=Files.newInputStream(path)){raw=input.readNBytes(maximum+1);}
        String digest=org.xar.ck3.control.application.action.ActionCodec.sha256(raw);
        if(raw.length!=reference.bytes()||!digest.equals(reference.sha256())||!before.equals(SharedSourceFiles.nativeFile(path)))
            throw new IOException("Loaded saved original changed during bounded read");
        return new LoadedOriginal(raw,new SharedSourceFiles.Witness(new ControlBuild.FileRef(path.normalize().toString(),raw.length,digest),before));
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
                ColdBootstrapJson.AdoptionData.class,NativeSavedGameClone.class,NativeSavedGameClone.Observation.class,Failure.class))game.launchPlan().sources().requireLoadedClass(type);
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
