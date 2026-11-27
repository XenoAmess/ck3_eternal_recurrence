package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import java.util.concurrent.CompletionException;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineObservation;
import org.xar.ck3.control.application.action.CompositeOperatorQuarantineRequest;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.InitialDriverState;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.platform.RootProcessAttach;
import org.xar.ck3.control.service.OfflineAnalysisWorker;
import org.xar.ck3.control.service.OrdinarySessionHost;

/** Ordinary worker composition. The supervisor retains ownership of the living Game. */
public final class RootOrdinaryRuntimeAssembly {
    private RootOrdinaryRuntimeAssembly() { }

    static final int MAX_WORKER_BATCH_LOG_BYTES=8*1024*1024;

    /** Complete history is retained byte-for-byte. Capacity failure never enters the file producer. */
    static void appendWorkerBatchLog(org.xar.ck3.control.continuity.writer.ContinuityWriter writer,
            RootRuntimeStorageGuard storage,CheckpointFiles files,Path stateDirectory,byte[] completeLine,int maximumBytes)throws IOException {
        Objects.requireNonNull(writer);Objects.requireNonNull(storage);Objects.requireNonNull(files);
        Objects.requireNonNull(stateDirectory);byte[] line=Objects.requireNonNull(completeLine).clone();
        if(!stateDirectory.isAbsolute()||!stateDirectory.normalize().equals(stateDirectory)
                ||maximumBytes<=0||maximumBytes>MAX_WORKER_BATCH_LOG_BYTES
                ||line.length==0||line[line.length-1]!=10||line.length>maximumBytes)
            throw new IOException("complete worker batch log exceeds its finite byte budget or has no complete line");
        Path target=stateDirectory.resolve("worker-batches.jsonl");
        writer.locked(same->{
            storage.requireReadScope(same,files);
            // Refuse an already oversized legacy log before the Native observer hashes its whole content.
            try {
                var attributes=Files.readAttributes(target,java.nio.file.attribute.BasicFileAttributes.class,
                        java.nio.file.LinkOption.NOFOLLOW_LINKS);
                if(!attributes.isRegularFile()||attributes.size()>maximumBytes)
                    throw new IOException("retained worker batch log exceeds its finite byte budget or is not a regular file");
            } catch(java.nio.file.NoSuchFileException absent) { /* The same guarded producer creates the first bounded file. */ }
            var previous=files.observe(target);
            long retained=previous.isPresent()?previous.orElseThrow().reference().bytes():0;
            if(retained>maximumBytes||line.length>maximumBytes-retained)
                throw new IOException("complete worker batch log exceeds its finite byte budget; retained history is unchanged");
            byte[] before=previous.isPresent()?files.read(previous.orElseThrow(),maximumBytes):new byte[0];
            byte[] joined=java.util.Arrays.copyOf(before,Math.addExact(before.length,line.length));
            System.arraycopy(line,0,joined,before.length,line.length);
            if(previous.isPresent())files.verify(previous.orElseThrow());
            storage.requireReadScope(same,files);
            var published=files.replace(target,joined);files.verify(published);
            return null;
        });
    }

    /** DATA spelling only; the caller retains all actual loaded-custody and executable qualification checks. */
    static G2Source loadedExecutionSource(String machineId,Instant observedAt,
            org.xar.ck3.control.build.ControlBuild.FileRef reviewedExecutable,G2Source historical,ExactRef implementation)throws IOException {
        Objects.requireNonNull(reviewedExecutable);Objects.requireNonNull(historical);
        String reviewed=reviewedExecutable.sha256(),original=historical.exactBuild();
        if(!reviewed.matches("[0-9a-f]{64}")||!original.matches("[0-9a-fA-F]{64}")
                ||!java.security.MessageDigest.isEqual(java.util.HexFormat.of().parseHex(reviewed),java.util.HexFormat.of().parseHex(original)))
            throw new IOException("loaded exact build differs from the actual reviewed executable SHA-256");
        return new G2Source(machineId,observedAt.toString(),original,implementation);
    }

    @FunctionalInterface
    interface OperationPhase<T> {
        T run(Instant deadline) throws IOException, InterruptedException;
    }

    /** Each installation operation retains its own guards and starts its configured budget when called. */
    static <T> T runOperationPhase(Clock clock, Duration timeout, OperationPhase<T> operation)
            throws IOException, InterruptedException {
        return operation.run(clock.instant().plus(timeout));
    }

    public static Prepared prepare(RootOrdinaryRuntimeConfiguration config,Clock clock)throws IOException {
        return prepare(config,clock,Optional.empty());
    }
    static Path importedCheckpointOutput(NativeLaunchPlan replacement,
            CheckpointPair original)throws IOException {
        Path output=replacement.profileDirectory().resolve("save games/xar_checkpoint.ck3");
        Path source=Path.of(original.save().reference().path());
        if (sameCheckpointFile(output,source))
            throw new IOException("replacement SAVE output overlaps the retained imported physical save");
        if (replacement.load() instanceof NativeLaunchPlan.SavedGame loaded) {
            Path actualLoaded=Path.of(loaded.save().path());
            if (!actualLoaded.equals(source) && sameCheckpointFile(output,actualLoaded))
                throw new IOException("replacement SAVE output overlaps the actual imported load copy");
        }
        return output;
    }
    static RootApplicationAssembly.FreshSessionConfiguration retainImportedCheckpointPaths(
            RootApplicationAssembly.FreshSessionConfiguration base, NativeLaunchPlan game,
            CheckpointPair imported, CheckpointPair latestConfirmed, CheckpointFiles files) throws IOException {
        if (!latestConfirmed.lineageId().equals(imported.lineageId()))
            throw new IOException("successor SAVE crossed the original imported lineage");
        var paths = base.checkpoints();
        var checkpoints = new RootStartupConfiguration.CheckpointPaths(paths.driverCheckpoint(),paths.checkpointEvidence(),
                paths.attachmentEvidence(),latestConfirmed.lineageId(),importedCheckpointOutput(game,imported));
        if (!latestConfirmed.equals(imported)) {
            files.verify(latestConfirmed);
        }
        return new RootApplicationAssembly.FreshSessionConfiguration(base.authorityId(),base.policy(),base.freshness(),
                checkpoints,base.cyclePolicy(),base.deadline());
    }

    private static boolean sameCheckpointFile(Path output,Path source)throws IOException {
        return output.toAbsolutePath().normalize().equals(source.toAbsolutePath().normalize())
                || Files.exists(output) && Files.isSameFile(output,source);
    }

    static void requireImportedLoadedPredecessor(WriterContracts.Head head,
            RootLoadedReplacementRecoveryInputs.ImportedRequest input,CompositeOperatorQuarantineRequest decision,
            SessionIdentity departed)throws IOException {
        var state=head.state();
        var body=state.toJson();
        if(state.status()!=ContinuityState.Status.REPAIR_REQUIRED
                ||state.sequence()!=input.expectedPredecessorSequence()||!head.digest().equals(input.expectedHeadDigest())
                ||state.sequence()!=Math.addExact(decision.expectedHeadSequence(),1)
                ||!state.machineId().equals(input.machineId())||!state.machineId().equals(departed.machineId())
                ||!departed.game().equals(GameGeneration.fromJson(body.get("game_binding")))
                ||decision.exitedLife().filter(exit->exit.ownerSessionId().equals(departed.sessionId())).isEmpty()
                ||!decision.episodeRunId().equals(body.path("latest_binding").path("episode_run_id").asText()))
            throw new IOException("imported loaded recovery requires its exact canonical immediately retired predecessor");
    }

    /** Existing saved-replacement recovery can never initialize a missing or partial canonical writer. */
    public static Prepared prepareLoadedReplacement(RootOrdinaryRuntimeConfiguration config,Clock clock)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);
        var configuredDecision=config.decisionProvider().orElseThrow(()->new IOException("loaded recovery requires its explicit decision provider"));
        if(!configuredDecision.codexFile())throw new IOException("loaded recovery requires the configured direct Codex file provider");
        return prepare(config,clock,Optional.empty(),true);
    }

    /** Saved recovery only reopens its original existing writer. */
    static Prepared prepareExistingSaved(RootOrdinaryRuntimeConfiguration config,Clock clock)throws IOException {
        return prepare(config,clock,Optional.empty(),true);
    }

    /** Source-only reader for an existing old Saved daemon; no allocation, genesis, or write authority. */
    public static Prepared prepareReadOnlySavedSource(RootOrdinaryRuntimeConfiguration config,Clock clock)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);
        var metadata=new RootOrdinaryImplementationMetadata();
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application parent");
        NativeLaunchPlan plan = config.retainBoundLaunchPlan(RootOrdinaryRuntimeConfiguration.readLaunchPlan(config.launchPlanFile()));
        var paths=new WriterContracts.InitialLayout(root.resolve("continuity/continuity.json"),
                root.resolve("continuity/genesis-anchor.json"),config.machineId());
        Path archiveRoot=root.resolve("continuity/artifacts");
        // Strictly require existing layout; never create directories or genesis.
        if(!Files.isRegularFile(paths.snapshot(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isRegularFile(paths.anchor(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isDirectory(paths.events(),java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("source-only reader requires its existing complete pre-entry store");
        var outputRoots=List.of(config.stateDirectory(),archiveRoot,paths.snapshot().getParent(),
                root.resolve("checkpoints"),root.resolve("receipts"),root.resolve("artifacts"),plan.profileDirectory().resolve("save games"),plan.evidenceRoot());
        // Inert storage guard for product composition only; no allocation admission.
        var storage=RootRuntimeStorageGuard.ordinary(paths,archiveRoot,()->{
            throw new IOException("source-only reader has no live writer authority");
        },outputRoots,config.maximumStorageBytes(),clock);
        var noWrites=StorageWriteGuard.noWrites();
        try {
            var layout=new WriterContracts.Layout(paths.snapshot(),metadata.file(paths.anchor()),config.machineId());
            var app=new RootApplicationConfiguration(config.machineId(),HostMode.COMPLETE_MIGRATION,clock.instant(),
                    metadata.file(config.launchPlanFile()),layout,List.of(metadata.implementation(RootOrdinaryRuntimeAssembly.class)),
                    archiveRoot,config.maximumStorageBytes());
            var ports=new RootCoreBoundPorts(app);
            var files=readOnlyFiles(new NativeCheckpointFiles(),noWrites);
            var operator=RootOperatorCharacterAuthority.prepareOrdinary(metadata.file(config.nativeImplementation()),metadata);
            var runtimePorts=new RootRuntimeSourceProducts.OrdinaryRuntimePorts(ports,files,storage,
                    OriginalRuntimeHandoffProof.unavailable(),operator,metadata,clock);
            var products=RootOrdinaryPlainProducts.prepare(config,app,runtimePorts,config.initialPolicy(),plan);
            var catalogs=products.runtime().catalogs();
            List<NativePrivateActionPermission> permissions=List.of();
            var lifecycle=new JavaGameLifecycle(permissions,config.operationTimeout(),config.maximumFramesPerOperation(),config.maximumSubmissions());
            return new Prepared(config,clock,plan,metadata,app,ports,storage,files,products,catalogs,permissions,lifecycle,noWrites);
        }catch(IOException|RuntimeException|Error failure) {
            try{noWrites.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            try{storage.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }

    /** Fresh independent business root for loaded Saved continuation; requires absent root before writes. */
    public static Prepared prepareFreshLoadedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
        return prepareFreshLoadedSaved(config,clock,source,Optional.empty());
    }
    /** Explicit public DATA is checked against this actual ordinary Core; it does not create a Startup or Game. */
    public static Prepared prepareFreshLoadedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source,RootRuntimeDefinitions.Inputs publicInputs)throws IOException {
        return prepareFreshLoadedSaved(config,clock,source,Optional.of(Objects.requireNonNull(publicInputs)));
    }
    /** Bind the actual CDI host before opening this one writer; application publication follows real Saved preentry. */
    public static Prepared prepareFreshLoadedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source,RootRuntimeDefinitions.PublicInputRequest request,
            OrdinarySessionHost actualHost)throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(actualHost);
        return prepareFreshLoadedSaved(config,clock,source,request.bound(),Optional.of(request),Optional.of(actualHost));
    }
    private static Prepared prepareFreshLoadedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source,Optional<RootRuntimeDefinitions.Inputs> publicInputs)throws IOException {
        return prepareFreshLoadedSaved(config,clock,source,publicInputs,Optional.empty(),Optional.empty());
    }
    private static Prepared prepareFreshLoadedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source,Optional<RootRuntimeDefinitions.Inputs> publicInputs,
            Optional<RootRuntimeDefinitions.PublicInputRequest> publicRequest,Optional<OrdinarySessionHost> actualHost)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);Objects.requireNonNull(source);
        var saved=source.savedState();
        if(!saved.machineId().equals(config.machineId()))throw new IOException("confirmed source belongs to another machine");
        var origin=saved.origin();
        var expected=new org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan(
                config.machineId(),origin.windowId(),origin.targetDays());
        // Require fresh root absent BEFORE any writes to avoid mutating retained249 or old843.
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application root");
        if(!Files.notExists(root,java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("fresh loaded Saved continuation requires an absent business root");
        var prepared=prepare(config,clock,Optional.of(expected),false,publicInputs);
        try {
            if(actualHost.isPresent())prepared.bindOrdinaryHost(actualHost.orElseThrow());
            prepared.bindLoadedSavedSource(source);
            if(publicRequest.isPresent()&&publicRequest.orElseThrow().unbound().isPresent())
                prepared.produceLoadedPublicDefinitions(publicRequest.orElseThrow());
            return prepared;
        }catch(IOException|RuntimeException|Error failure) {
            try{prepared.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }

    private static Prepared prepare(RootOrdinaryRuntimeConfiguration config,Clock clock,
            Optional<org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan> savedGenesis)throws IOException {
        return prepare(config,clock,savedGenesis,false);
    }
    private static Prepared prepare(RootOrdinaryRuntimeConfiguration config,Clock clock,
            Optional<org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan> savedGenesis,boolean requireExisting)throws IOException {
        return prepare(config,clock,savedGenesis,requireExisting,Optional.empty());
    }
    private static Prepared prepare(RootOrdinaryRuntimeConfiguration config,Clock clock,
            Optional<org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan> savedGenesis,boolean requireExisting,
            Optional<RootRuntimeDefinitions.Inputs> publicInputs)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);
        var metadata=new RootOrdinaryImplementationMetadata();
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application parent");
        NativeLaunchPlan plan = config.retainBoundLaunchPlan(RootOrdinaryRuntimeConfiguration.readLaunchPlan(config.launchPlanFile()));
        var paths=new WriterContracts.InitialLayout(root.resolve("continuity/continuity.json"),
                root.resolve("continuity/genesis-anchor.json"),config.machineId());
        Path archiveRoot=root.resolve("continuity/artifacts");
        if(requireExisting&&(!Files.isRegularFile(paths.anchor(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isRegularFile(paths.snapshot(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isDirectory(paths.events(),java.nio.file.LinkOption.NOFOLLOW_LINKS)))
            throw new IOException("recovery requires the complete existing canonical writer; no new genesis");
        var outputRoots=List.of(config.stateDirectory(),archiveRoot,paths.snapshot().getParent(),
                root.resolve("checkpoints"),root.resolve("receipts"),root.resolve("artifacts"),plan.profileDirectory().resolve("save games"),plan.evidenceRoot());
        for(Path directory:outputRoots)Files.createDirectories(directory);
        Files.createDirectories(config.stateDirectory().resolve("incidents/inputs"));
        Files.createDirectories(config.stateDirectory().resolve("incidents/scan"));
        Files.createDirectories(plan.profileDirectory().resolve("save games/tutorial"));
        boolean anchor=Files.exists(paths.anchor()),snapshot=Files.exists(paths.snapshot()),events=Files.exists(paths.events());
        if(requireExisting&&!(anchor&&snapshot&&events))throw new IOException("loaded recovery canonical source disappeared; no genesis");
        if((anchor||snapshot||events)&&!(anchor&&snapshot&&events))
            throw new IOException("partial canonical ledger initialization is retained for recovery; it cannot be overwritten");
        if(savedGenesis.isPresent()&&(anchor||snapshot||events))
            throw new IOException("confirmed saved bootstrap requires a distinct uninitialized new writer");
        Path request=paths.snapshot().getParent().resolve("genesis-request.json");
        var genesis=anchor?Optional.<org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan>empty()
                :Optional.of(savedGenesis.isPresent()?genesisRequest(request,savedGenesis.orElseThrow()):genesisRequest(request,config.machineId(),clock));
        var actualPorts=new java.util.concurrent.atomic.AtomicReference<RootCoreBoundPorts>();
        var storage=RootRuntimeStorageGuard.ordinary(paths,archiveRoot,()->{
            var actual=actualPorts.get();
            if(actual==null)throw new IOException("ordinary canonical writer has not been constructed yet");
            return actual.requireWriter();
        },outputRoots,config.maximumStorageBytes(),clock);
        try {
            var layout=genesis.isPresent()
                    ?org.xar.ck3.control.continuity.writer.ContinuityWriter.initializeFresh(genesis.orElseThrow(),metadata.file(request),paths,storage).layout()
                    :new WriterContracts.Layout(paths.snapshot(),metadata.file(paths.anchor()),config.machineId());
            var reviewed=publicInputs.map(RootRuntimeDefinitions.Inputs::application);
            var app=new RootApplicationConfiguration(config.machineId(),HostMode.COMPLETE_MIGRATION,
                    reviewed.map(RootApplicationConfiguration::reviewAt).orElseGet(clock::instant),
                    metadata.file(config.launchPlanFile()),layout,List.of(metadata.implementation(RootOrdinaryRuntimeAssembly.class)),
                    archiveRoot,config.maximumStorageBytes());
            if(reviewed.isPresent()) {
                var original=reviewed.orElseThrow();original.requireCurrent(clock);
                if(!original.equals(app))
                    throw new IOException("public definitions differ from the actual ordinary application, writer, sources or storage budget");
                app=original;
            }
            var ports=new RootCoreBoundPorts(app);actualPorts.set(ports);
            var files=storage.checkpointFiles(new NativeCheckpointFiles());
            var operator=RootOperatorCharacterAuthority.prepareOrdinary(metadata.file(config.nativeImplementation()),metadata);
            var runtimePorts=new RootRuntimeSourceProducts.OrdinaryRuntimePorts(ports,files,storage,
                    OriginalRuntimeHandoffProof.unavailable(),operator,metadata,clock);
            var products=RootOrdinaryPlainProducts.prepare(config,app,runtimePorts,config.initialPolicy(),plan);
            var catalogs=products.runtime().catalogs();
            var permissions=new ArrayList<NativePrivateActionPermission>(catalogs.privatePermissions(ports::qualifyPrivate));
            permissions.add(RootPreparedCleanupScope.permission(metadata.implementation(RootPreparedCleanupScope.class)));
            var lifecycle=new JavaGameLifecycle(permissions,config.operationTimeout(),config.maximumFramesPerOperation(),config.maximumSubmissions());
            var prepared=new Prepared(config,clock,plan,metadata,app,ports,storage,files,products,catalogs,permissions,lifecycle);
            if(publicInputs.isPresent())prepared.preparePublic(publicInputs.orElseThrow());
            return prepared;
        }catch(IOException|RuntimeException|Error failure) {
            try {storage.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }

    private static CheckpointFiles readOnlyFiles(CheckpointFiles actual,StorageWriteGuard guard)throws IOException {
        StorageWriteGuard.requireNoWritesOpen(guard);Objects.requireNonNull(actual);
        return new CheckpointFiles() {
            @Override public Optional<FileWitness> observe(Path path)throws IOException {
                StorageWriteGuard.requireNoWritesOpen(guard);return actual.observe(path);
            }
            @Override public byte[] read(FileWitness expected,int maximumBytes)throws IOException {
                StorageWriteGuard.requireNoWritesOpen(guard);return actual.read(expected,maximumBytes);
            }
            @Override public FileWitness createNew(Path target,byte[] body)throws IOException {
                throw new IOException("source-only checkpoint files cannot create");
            }
            @Override public FileWitness replace(Path target,byte[] body)throws IOException {
                throw new IOException("source-only checkpoint files cannot replace");
            }
            @Override public FileWitness copyNew(FileWitness source,Path target)throws IOException {
                throw new IOException("source-only checkpoint files cannot copy");
            }
        };
    }

    private static org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan genesisRequest(Path request,String machineId,Clock clock)throws IOException {
        if(Files.notExists(request)) {
            try(var channel=java.nio.channels.FileChannel.open(request,java.nio.file.StandardOpenOption.CREATE_NEW,java.nio.file.StandardOpenOption.WRITE)) {
                var plan=new org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan(machineId,Math.max(1,clock.millis()),OriginalWindowReducer.TARGET_DAYS);
                var buffer=java.nio.ByteBuffer.wrap(org.xar.ck3.control.continuity.FreshContinuityGenesis.encode(plan));
                while(buffer.hasRemaining())channel.write(buffer);
                channel.force(true);
            }catch(java.nio.file.FileAlreadyExistsException concurrentCreation) {
                // The original request is reread below, never replaced by a second configured window.
            }
        }
        byte[] raw;
        int maximum=org.xar.ck3.control.continuity.FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES;
        try(InputStream input=Files.newInputStream(request)){raw=input.readNBytes(maximum+1);}
        if(raw.length==0||raw.length>maximum)throw new IOException("bounded genesis request required");
        try {
            var plan=org.xar.ck3.control.continuity.FreshContinuityGenesis.decode(raw);
            if(!plan.machineId().equals(machineId))throw new IOException("genesis request belongs to another machine");
            return plan;
        }catch(IllegalArgumentException invalid){throw new IOException("invalid original genesis request",invalid);}
    }

    /** Source-qualified policy for a new independent saved-load writer; no old state is rewritten. */
    public static Prepared prepareConfirmedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
        Objects.requireNonNull(source);
        var saved=source.savedState();
        if(!saved.machineId().equals(config.machineId()))throw new IOException("confirmed source belongs to another machine");
        var origin=saved.origin();
        var expected=new org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan(
                config.machineId(),origin.windowId(),origin.targetDays());
        return prepare(config,clock,Optional.of(expected));
    }

    /** Reopens only the retained, exact pre-entry writer left by the original Saved launch. */
    public static Prepared prepareLoadedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);Objects.requireNonNull(source);
        var saved=source.savedState();
        if(!saved.machineId().equals(config.machineId()))throw new IOException("confirmed source belongs to another machine");
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application parent");
        var paths=new WriterContracts.InitialLayout(root.resolve("continuity/continuity.json"),
                root.resolve("continuity/genesis-anchor.json"),config.machineId());
        if(!Files.isRegularFile(paths.snapshot(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isRegularFile(paths.anchor(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isDirectory(paths.events(),java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("loaded Saved continuation requires its existing complete pre-entry store");
        var origin=saved.origin();
        var expected=new org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan(
                config.machineId(),origin.windowId(),origin.targetDays());
        byte[] wanted=org.xar.ck3.control.continuity.FreshContinuityGenesis.encode(expected);
        byte[] actual;
        try(var input=Files.newInputStream(paths.snapshot().getParent().resolve("genesis-request.json"))) {
            actual=input.readNBytes(org.xar.ck3.control.continuity.FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES+1);
        }
        if(!java.util.Arrays.equals(wanted,actual))
            throw new IOException("loaded Saved genesis request differs from the actual confirmed source policy");
        var prepared=prepare(config,clock);
        try {
            prepared.bindLoadedSavedSource(source);
            return prepared;
        }catch(IOException|RuntimeException|Error failure) {
            try{prepared.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }

    public static Prepared prepareRetainedLoadedSaved(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);Objects.requireNonNull(source);
        var saved=source.savedState();
        if(!saved.machineId().equals(config.machineId()))throw new IOException("confirmed source belongs to another machine");
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application parent");
        var paths=new WriterContracts.InitialLayout(root.resolve("continuity/continuity.json"),
                root.resolve("continuity/genesis-anchor.json"),config.machineId());
        if(!Files.isRegularFile(paths.snapshot(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isRegularFile(paths.anchor(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isDirectory(paths.events(),java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("loaded Saved continuation requires its existing complete retained store");
        var origin=saved.origin();
        var expected=new org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan(
                config.machineId(),origin.windowId(),origin.targetDays());
        byte[] wanted=org.xar.ck3.control.continuity.FreshContinuityGenesis.encode(expected);
        byte[] actual;
        try(var input=Files.newInputStream(paths.snapshot().getParent().resolve("genesis-request.json"))) {
            actual=input.readNBytes(org.xar.ck3.control.continuity.FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES+1);
        }
        if(!java.util.Arrays.equals(wanted,actual))
            throw new IOException("loaded Saved genesis request differs from the actual confirmed source policy");
        var prepared=prepare(config,clock);
        try {
            prepared.bindRetainedLoadedSavedSource(source);
            return prepared;
        }catch(IOException|RuntimeException|Error failure) {
            try{prepared.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }

    public static Prepared prepareExistingLoadedSavedRecovery(RootOrdinaryRuntimeConfiguration config,Clock clock,
            RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);Objects.requireNonNull(source);
        var saved=source.savedState();
        if(!saved.machineId().equals(config.machineId()))throw new IOException("confirmed source belongs to another machine");
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application parent");
        var paths=new WriterContracts.InitialLayout(root.resolve("continuity/continuity.json"),
                root.resolve("continuity/genesis-anchor.json"),config.machineId());
        if(!Files.isRegularFile(paths.snapshot(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isRegularFile(paths.anchor(),java.nio.file.LinkOption.NOFOLLOW_LINKS)
                ||!Files.isDirectory(paths.events(),java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("loaded Saved continuation requires its existing complete retained store");
        var origin=saved.origin();
        var expected=new org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan(
                config.machineId(),origin.windowId(),origin.targetDays());
        byte[] wanted=org.xar.ck3.control.continuity.FreshContinuityGenesis.encode(expected);
        byte[] actual;
        try(var input=Files.newInputStream(paths.snapshot().getParent().resolve("genesis-request.json"))) {
            actual=input.readNBytes(org.xar.ck3.control.continuity.FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES+1);
        }
        if(!java.util.Arrays.equals(wanted,actual))
            throw new IOException("loaded Saved genesis request differs from the actual confirmed source policy");
        var prepared=prepare(config,clock);
        try {
            prepared.bindOriginalSavedRecoverySource(source);
            return prepared;
        }catch(IOException|RuntimeException|Error failure) {
            try{prepared.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }

    private static org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan genesisRequest(Path request,
            org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan expected)throws IOException {
        byte[] wanted=org.xar.ck3.control.continuity.FreshContinuityGenesis.encode(expected);
        try(var channel=java.nio.channels.FileChannel.open(request,java.nio.file.StandardOpenOption.CREATE_NEW,
                java.nio.file.StandardOpenOption.WRITE)) {
            var buffer=java.nio.ByteBuffer.wrap(wanted);while(buffer.hasRemaining())channel.write(buffer);channel.force(true);
        }catch(java.nio.file.FileAlreadyExistsException retained) {
            // An existing exact request is retained, never replaced by a second policy.
        }
        byte[] actual;
        try(var input=Files.newInputStream(request)) {
            actual=input.readNBytes(org.xar.ck3.control.continuity.FreshContinuityGenesis.MAXIMUM_REQUEST_BYTES+1);
        }
        if(!java.util.Arrays.equals(wanted,actual))throw new IOException("saved-load genesis request differs from its actual confirmed source policy");
        return expected;
    }

    public record PreparedCleanupResult(org.xar.ck3.control.application.action.ActionReceipt childReceipt,
            org.xar.ck3.control.application.action.ActionReceipt parentReceipt,ExactRef preparationRef){
        public PreparedCleanupResult{Objects.requireNonNull(childReceipt);Objects.requireNonNull(parentReceipt);Objects.requireNonNull(preparationRef);}
        public boolean complete(){return childReceipt.settled()&&parentReceipt.settled();}
    }
    public static final class Prepared implements AutoCloseable {
        private final RootOrdinaryRuntimeConfiguration config;
        private final Clock clock;
        private final NativeLaunchPlan plan;
        private final RootOrdinaryImplementationMetadata metadata;
        private final RootApplicationConfiguration app;
        private final RootCoreBoundPorts ports;
        private final RootRuntimeStorageGuard storage;
        private final CheckpointFiles files;
        private final RootRuntimeSourceProducts.PlainPrepared products;
        private final RootRuntimeCatalogFactory catalogs;
        private final List<NativePrivateActionPermission> permissions;
        private final JavaGameLifecycle lifecycle;
        private final StorageWriteGuard noWrites;
        private final OriginalWindowReducer.Policy cyclePolicy=new OriginalWindowReducer.Policy(OriginalWindowReducer.TARGET_DAYS);
        private final NativeReadiness.Policy policy=new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ZERO,false);
        private RootApplicationAssembly.Core core;
        private ManagedGameSession game;
        private boolean entered;
        private boolean closed;
        private RootJavaSavedBootstrap.ConfirmedSource loadedSavedSource;
        private RootJavaSavedBootstrap.ConfirmedSource retainedSavedSource;
        private RootJavaSavedBootstrap.ConfirmedSource originalSavedRecoverySource;
        private OrdinarySessionHost ordinaryHost = new OrdinarySessionHost();
        private boolean externalOrdinaryHostBound;
        private RootRuntimeDefinitions.Inputs publicInputs;
        private RootPublicHandlerProductsFactory.Prepared publicProducts;
        private RootRuntimePublicCatalog publicCatalog;
        private org.xar.ck3.control.service.mcp.PublicMcpHost publicHost;
        private org.xar.ck3.control.service.mcp.McpExecutableDirectory.Complete publicDirectory;
        private boolean publicInstallEntered;
        private IOException publicInstallFailure;
        private final boolean sourceOnly;
        private org.xar.ck3.control.platform.JavaGameLifecycle.ExitedGeneration exitedRecovery;
        private RootExitedSavedMaterialSource.PreparedImportedRestore importedRestore;
        private RootLoadedReplacementRecoveryInputs.ImportedRequest importedLoadedRequest;
        private RootProcessAttach.ImportedLoadedOriginals importedLoadedOriginals;
        private CommittedImportedStart committedImportedStart;

        private record CommittedImportedStart(RootLoadedReplacementRecoveryInputs.ImportedRequest input,
                WriterContracts.Pin attachment,RootProcessAttach.ImportedLoadedOriginals originals,
                ContinuityBatchJournal.ImportedRestoreRebindReadback readback) { }

        record CommittedImportedStage(DriverBootstrap.Adopted driver,RootInstalledCatalog catalog,
                RootSavedOrdinaryReopen.Committed original,RootCommittedOrdinaryRestoration domainOriginal) { }
        private org.xar.ck3.control.platform.SavedGameOwnerLifetime249.Retained exitedOwnerLifetime;
        private JavaGameLifecycle.Started exitedOwnerStart;
        private Path exitedOwnerDirectory;
        private String exitedOwnerParentRequest;
        private ManagedGameSession.CreatorOwnership exitedOriginalOwnership;

        private Prepared(RootOrdinaryRuntimeConfiguration config,Clock clock,NativeLaunchPlan plan,
                RootOrdinaryImplementationMetadata metadata,RootApplicationConfiguration app,RootCoreBoundPorts ports,
                RootRuntimeStorageGuard storage,CheckpointFiles files,RootRuntimeSourceProducts.PlainPrepared products,
                RootRuntimeCatalogFactory catalogs,List<NativePrivateActionPermission> permissions,JavaGameLifecycle lifecycle) {
            this(config,clock,plan,metadata,app,ports,storage,files,products,catalogs,permissions,lifecycle,null);
        }

        private Prepared(RootOrdinaryRuntimeConfiguration config,Clock clock,NativeLaunchPlan plan,
                RootOrdinaryImplementationMetadata metadata,RootApplicationConfiguration app,RootCoreBoundPorts ports,
                RootRuntimeStorageGuard storage,CheckpointFiles files,RootRuntimeSourceProducts.PlainPrepared products,
                RootRuntimeCatalogFactory catalogs,List<NativePrivateActionPermission> permissions,JavaGameLifecycle lifecycle,
                StorageWriteGuard noWrites) {
            this.config=config;this.clock=clock;this.plan=plan;this.metadata=metadata;this.app=app;this.ports=ports;
            this.storage=storage;this.files=files;this.products=products;this.catalogs=catalogs;
            this.permissions=List.copyOf(permissions);this.lifecycle=lifecycle;this.noWrites=noWrites;
            this.sourceOnly=noWrites!=null;
        }
        /** Observed immutable files only. This record is not Root, Native, directory or dispatch authority. */
        public record PublicDefinitionsProduction(org.xar.ck3.control.build.ControlBuild.FileRef requestOriginal,
                org.xar.ck3.control.build.ControlBuild.FileRef requestMaterial,
                org.xar.ck3.control.build.ControlBuild.FileRef application,
                org.xar.ck3.control.build.ControlBuild.FileRef provisionalDefinitions,
                org.xar.ck3.control.build.ControlBuild.FileRef admission,
                org.xar.ck3.control.build.ControlBuild.FileRef definitions) { }
        private boolean publicDefinitionProductionEntered;
        private PublicDefinitionsProduction publicDefinitionProduction;
        public synchronized Optional<PublicDefinitionsProduction> publicDefinitionsProduction() {
            return Optional.ofNullable(publicDefinitionProduction);
        }
        private void requireLoadedPublicPreparation() throws IOException {
            requireLoadedPublicPreparationState();
            core.requireConfirmedSavedPreentry(loadedSavedSource);
        }
        private void requireLoadedPublicPreparationState() throws IOException {
            if(closed||sourceOnly||entered||game!=null||core==null||loadedSavedSource==null||publicInputs!=null)
                throw new IOException("public input production requires this same unentered confirmed-Saved Prepared/Core");
        }
        private org.xar.ck3.control.build.ControlBuild.FileRef preservePublic(
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,byte[] body)throws IOException {
            core.writer().requireSession(same);
            return RootApplicationConfiguration.file(core.archive().withSession(same).preserveMaterial(org.xar.ck3.control.application.action.RawJson.fullMaterial(body)));
        }
        private synchronized void produceLoadedPublicDefinitions(RootRuntimeDefinitions.PublicInputRequest request)throws IOException {
            requireLoadedPublicPreparation();
            if(publicDefinitionProductionEntered||request.unbound().isEmpty())
                throw new IOException("original loaded public input production is absent or already entered; no replay");
            var unbound=request.unbound().orElseThrow();
            if(!RootRuntimeDefinitions.readUnboundApplication(request.original()).equals(unbound))
                throw new IOException("unbound public input request changed before publication");
            publicDefinitionProductionEntered=true;
            final PublicDefinitionsProduction produced;
            try { produced=core.writer().locked(same->{
                requireLoadedPublicPreparationState();core.writer().requireSession(same);
                var before=same.head();
                byte[] requestRaw=RootRuntimeDefinitions.read(request.original(),RootRuntimeDefinitions.MAXIMUM_BYTES);
                var requestMaterial=preservePublic(same,requestRaw);
                byte[] actualApplication=StrictJson.canonical(app.toJson(),RootApplicationConfiguration.MAXIMUM_BYTES);
                if(!RootApplicationConfiguration.fromJson(StrictJson.parse(actualApplication,RootApplicationConfiguration.MAXIMUM_BYTES)).equals(app))
                    throw new IOException("actual application codec readback differs before immutable publication");
                var application=preservePublic(same,actualApplication);
                var provisionalConfiguration=unbound.bind(application);
                var provisional=preservePublic(same,RootRuntimeDefinitions.encodeConfiguration(provisionalConfiguration));
                var provisionalInputs=RootRuntimeDefinitions.readInputsRetainingApplication(provisional,app,clock);
                RootRuntimeDefinitions.verifyStorageLease(provisionalInputs.storageLease(),provisionalInputs.configuration(),app);
                for(var original:provisionalInputs.configuration().originalData())original.originalRef().verify();
                provisionalInputs.configuration().runtimePackageRequestRef().verify();
                var registration=publicRegistration(provisionalInputs);
                var settings=RootRuntimeDomainSettings.readExact(
                        provisionalInputs.data(RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS),clock);
                var draft=RootPublicHandlerProductsFactory.prepareAdmissionData(
                        provisionalInputs,ports,catalogs,Optional.of(registration),settings,clock);
                var admissionData=RootPublicMcpAdmission.preparedData(provisionalInputs,draft,registration,clock);
                var admission=preservePublic(same,admissionData.bytes());
                var finalData=new ArrayList<RootRuntimeDefinitionModel.DataPin>();
                for(var original:provisionalConfiguration.originalData())
                    finalData.add(original.role()==RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION
                            ?new RootRuntimeDefinitionModel.DataPin(original.role(),admission):original);
                var finalConfiguration=RootRuntimeDefinitions.rebindInputs(provisionalConfiguration,application,List.copyOf(finalData));
                var definitions=preservePublic(same,RootRuntimeDefinitions.encodeConfiguration(finalConfiguration));
                var readback=RootRuntimeDefinitions.readInputsRetainingApplication(definitions,app,clock);
                if(!readback.configuration().equals(finalConfiguration)||readback.application()!=app
                        ||!RootRuntimeDefinitions.readUnboundApplication(request.original()).equals(unbound))
                    throw new IOException("published public definitions lost exact request, configuration or same application");
                if(!before.digest().equals(same.head().digest())||!Objects.equals(before.state().sequence(),same.head().state().sequence())
                        ||!before.state().toJson().equals(same.head().state().toJson()))
                    throw new IOException("public DATA publication changed the original canonical preentry head");
                requireLoadedPublicPreparationState();core.writer().requireSession(same);
                return new PublicDefinitionsProduction(request.original(),requestMaterial,application,provisional,admission,definitions);
            }); } catch(IOException|RuntimeException|Error original) {
                try { requireLoadedPublicPreparation(); }
                catch(IOException|RuntimeException|Error postguard) { if(postguard!=original)original.addSuppressed(postguard); }
                throw original;
            }
            requireLoadedPublicPreparation();
            var finalInputs=RootRuntimeDefinitions.readInputsRetainingApplication(produced.definitions(),app,clock);
            requireLoadedPublicPreparation();
            preparePublicProducts(finalInputs);
            publicDefinitionProduction=produced;
        }
        private RootSelectedRegistrationConfiguration.Bound publicRegistration(RootRuntimeDefinitions.Inputs inputs)throws IOException {
            var declarations=RootRuntimePublicCatalog.Sources.readOriginals(inputs);
            var configured=declarations.admission().stream()
                    .filter(value->value.admission()==org.xar.ck3.control.service.mcp.McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION)
                    .map(org.xar.ck3.control.service.mcp.McpCoverage.Decision::actualAdmissionProducer).distinct().toList();
            if(configured.size()!=1)throw new IOException("public exclusions require their one actual registration original");
            var registration=RootSelectedRegistrationConfiguration.readExact(configured.getFirst(),inputs,
                    catalogs.sources().frontend().originalDriverImport().frozenProfile(),plan,clock);
            if(!registration.configuration().source(RootSelectedRegistrationConfiguration.SourceRole.ORIGINAL_NATIVE_DRIVER)
                    .equals(inputs.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER)))
                throw new IOException("public and ordinary registration differ from the original Native Driver producer");
            return registration;
        }
        /** Prepare the existing complete public products on these identical ordinary ports and domain catalogs. */
        private void preparePublic(RootRuntimeDefinitions.Inputs inputs) throws IOException {
            if (closed || entered || core != null || sourceOnly || publicInputs != null || inputs.application() != app)
                throw new IOException("public products require the identical unentered ordinary application inputs");
            preparePublicProducts(inputs);
        }
        private void preparePublicProducts(RootRuntimeDefinitions.Inputs inputs)throws IOException {
            if(closed||entered||game!=null||sourceOnly||publicInputs!=null||inputs.application()!=app)
                throw new IOException("runtime public products lost their actual unentered application owner");
            var registration=publicRegistration(inputs);
            var settings = RootRuntimeDomainSettings.readExact(
                    inputs.data(RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS), clock);
            var prepared = RootPublicHandlerProductsFactory.prepare(inputs, ports, catalogs, Optional.of(registration), settings, clock);
            var catalog = new RootRuntimePublicCatalog(RootRuntimePublicCatalog.Sources.read(inputs, prepared.handlers()), clock);
            prepared.requireComplete(); catalog.requireCompleteDefinitions();
            publicInputs = inputs; publicProducts = prepared; publicCatalog = catalog;
        }
        private synchronized org.xar.ck3.control.service.mcp.McpExecutableDirectory.Complete installPublic(
                Running actual, org.xar.ck3.control.service.mcp.PublicMcpHost host) throws IOException, InterruptedException {
            Objects.requireNonNull(actual); Objects.requireNonNull(host);
            if (actual.owner != this || closed || sourceOnly || publicInputs == null || publicCatalog == null)
                throw new IOException("public host requires this original admitted ordinary Running and its prepared products");
            actual.catalog();
            if (publicDirectory != null) {
                if (publicHost != host || host.current().filter(value -> value == publicDirectory.directory()).isEmpty())
                    throw new IOException("ordinary public host or original directory identity changed");
                return publicDirectory;
            }
            if (publicInstallEntered)
                throw new IOException("original public installation is unresolved; directory replacement or replay is forbidden", publicInstallFailure);
            publicProducts.requireComplete(); publicCatalog.requireCompleteDefinitions();
            plan.sources().verify(); publicProducts.requireLoadedClasses(plan);
            publicInstallEntered = true; publicHost = host;
            try {
                var installed = publicCatalog.install(core, catalogs, host);
                actual.catalog();
                if (host.current().filter(value -> value == installed.directory()).isEmpty())
                    throw new IOException("same Quarkus host lost the actual complete ordinary public directory");
                publicDirectory = installed; return installed;
            } catch (IOException failure) { publicInstallFailure = failure; throw failure; }
            catch (InterruptedException failure) { publicInstallFailure = new IOException("original public installation interrupted", failure); throw failure; }
            catch (RuntimeException failure) { publicInstallFailure = new IOException("original public installation failed", failure); throw publicInstallFailure; }
        }
        public synchronized void bindOrdinaryHost(OrdinarySessionHost actual) throws IOException {
            Objects.requireNonNull(actual);
            if (sourceOnly || closed || entered || core != null || game != null || externalOrdinaryHostBound
                    || actual.current().isPresent())
                throw new IOException("ordinary public host must bind once before actual Root entry");
            ordinaryHost = actual;
            externalOrdinaryHostBound = true;
        }
        public RootOrdinaryRuntimeConfiguration configuration(){return config;}
        /** Uses this runtime's identical allocation owner and physical file producer. */
        public synchronized void appendWorkerBatchLog(byte[] completeLine)throws IOException {
            if(closed||sourceOnly||core==null)throw new IOException("worker batch log requires its open actual runtime writer");
            RootOrdinaryRuntimeAssembly.appendWorkerBatchLog(core.writer(),storage,files,config.stateDirectory(),
                    completeLine,MAX_WORKER_BATCH_LOG_BYTES);
        }
        public InitialEpisodePolicy initialPolicy(){return config.initialPolicy();}
        public NativeLaunchPlan plan(){return plan;}
        public List<NativePrivateActionPermission> privatePermissions(){
            if(sourceOnly)throw new IllegalStateException("source-only reader exposes no live private permissions");
            return permissions;
        }
        public RootRuntimeCatalogFactory catalogs(){
            if(sourceOnly)throw new IllegalStateException("source-only reader exposes no live catalog authority");
            return catalogs;
        }
        public JavaGameLifecycle lifecycle(){
            if(sourceOnly)throw new IllegalStateException("source-only reader exposes no live lifecycle authority");
            return lifecycle;
        }

        /** Uses only this Prepared graph's actual Saved creator result; this method never launches. */
        private synchronized void bindLoadedSavedSource(RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
            Objects.requireNonNull(source);
            if(closed||entered||core!=null||game!=null||loadedSavedSource!=null)
                throw new IOException("loaded Saved source graph is already consumed or closed");
            if(sourceOnly)throw new IOException("source-only reader cannot bind loaded Saved continuation");
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))
                throw new IOException("loaded Saved source requires the actual Saved plan");
            core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            core.bindFirstHeirMarriageEnabled(config.firstHeirMarriageEnabled());
            core.bindNewMarriageProposalsEnabled(config.newMarriageProposalsEnabled());
            ports.bindCore(core);catalogs.bindCore(core);
            core.requireConfirmedSavedPreentry(source);
            loadedSavedSource=source;
        }

        /** Binds the actual retained Saved source for an existing non-empty ledger; no fresh genesis or preentry check. */
        private synchronized void bindRetainedLoadedSavedSource(RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
            Objects.requireNonNull(source);
            if(closed||entered||core!=null||game!=null||loadedSavedSource!=null||retainedSavedSource!=null)
                throw new IOException("retained loaded Saved source graph is already consumed or closed");
            if(sourceOnly)throw new IOException("source-only reader cannot bind retained loaded Saved continuation");
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))
                throw new IOException("retained loaded Saved source requires the actual Saved plan");
            core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            core.bindFirstHeirMarriageEnabled(config.firstHeirMarriageEnabled());
            core.bindNewMarriageProposalsEnabled(config.newMarriageProposalsEnabled());
            ports.bindCore(core);catalogs.bindCore(core);
            core.requireRetainedConfirmedSaved(source);
            retainedSavedSource=source;
        }

        private synchronized void bindOriginalSavedRecoverySource(RootJavaSavedBootstrap.ConfirmedSource source)throws IOException {
            Objects.requireNonNull(source);
            if(closed||entered||core!=null||game!=null||loadedSavedSource!=null||retainedSavedSource!=null||originalSavedRecoverySource!=null)
                throw new IOException("retained loaded Saved source graph is already consumed or closed");
            if(sourceOnly)throw new IOException("source-only reader cannot bind retained loaded Saved continuation");
            if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))
                throw new IOException("retained loaded Saved source requires the actual Saved plan");
            core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            core.bindFirstHeirMarriageEnabled(config.firstHeirMarriageEnabled());
            core.bindNewMarriageProposalsEnabled(config.newMarriageProposalsEnabled());
            ports.bindCore(core);catalogs.bindCore(core);
            core.writer().locked(same->{RootJavaSavedBootstrap.existingSavedSource(source,same,core.archive());return null;});
            originalSavedRecoverySource=source;
        }

        /** Consumes an actual private loaded-Saved custody; no Started object or launch is synthesized. */
        public synchronized Running openLoadedSaved(ManagedGameSession actualAttached,
                RootJavaSavedBootstrap.ConfirmedSource source,
                org.xar.ck3.control.platform.RootProcessAttach.LoadedCustody custody,
                Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(actualAttached);Objects.requireNonNull(source);
            Objects.requireNonNull(custody);Objects.requireNonNull(deadline);
            if(sourceOnly)throw new IOException("source-only reader cannot open loaded Saved continuation");
            if(closed||entered||core==null||game!=null||loadedSavedSource!=source)
                throw new IOException("loaded Saved graph is unavailable or differs from its retained source");
            if(actualAttached.mode()!=ManagedGameSession.Mode.ATTACHED||actualAttached.launchPlan()!=plan
                    ||!(plan.load() instanceof NativeLaunchPlan.SavedGame)
                    ||custody.game()!=actualAttached||!custody.pair().equals(source.pair()))
                throw new IOException("loaded Saved requires the exact attached Game, Saved plan and private custody");
            custody.requireCurrent();actualAttached.verify();
            core.requireConfirmedSavedPreentry(source);
            entered=true;game=actualAttached;
            // This binds only the real attached lifecycle. Saved eligibility is minted below by admitLoaded.
            lifecycle.adoptAttached(actualAttached);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,plan);
            actualAttached.nativeTransport().awaitHello(clock.instant().plus(config.operationTimeout()));
            var hello=actualAttached.nativeTransport().originalHello();
            var sourceG2=new G2Source(actualAttached.machineId(),clock.instant().toString(),hello.gameSha256(),
                    metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            var opened=new Opened(this,sourceG2);
            var installed=runOperationPhase(clock,config.operationTimeout(),until->
                    catalogs.install(core,actualAttached,sourceG2,core.planningReads(),clock,until));
            opened.installed=installed;
            var driver=runOperationPhase(clock,Duration.ofMinutes(10),until->{
                config.initialPolicy().requireInitialSavedProjection(plan,source.pair().save());
                var admission=RootJavaSavedBootstrap.admitLoaded(source,installed.context(),custody,until,config.initialPolicy());
                return core.adoptConfirmedSaved(admission,sourceG2,config.retainedFrames(),until);
            });
            return opened.finishConfirmedSaved(driver,deadline);
        }

        /** Opens the actual retained loaded-Saved continuation without launching, replaying Entry or resetting the ledger. */
        public synchronized Running openRetainedLoadedSaved(ManagedGameSession actualAttached,
                RootJavaSavedBootstrap.ConfirmedSource source,
                org.xar.ck3.control.platform.RootProcessAttach.LoadedCustody custody,
                Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(actualAttached);Objects.requireNonNull(source);
            Objects.requireNonNull(custody);Objects.requireNonNull(deadline);
            if(sourceOnly)throw new IOException("source-only reader cannot open retained loaded Saved continuation");
            if(closed||entered||core==null||game!=null||retainedSavedSource!=source)
                throw new IOException("retained loaded Saved graph is unavailable or differs from its retained source");
            if(actualAttached.mode()!=ManagedGameSession.Mode.ATTACHED||actualAttached.launchPlan()!=plan
                    ||!(plan.load() instanceof NativeLaunchPlan.SavedGame)
                    ||custody.game()!=actualAttached||!custody.pair().equals(source.pair()))
                throw new IOException("retained loaded Saved requires the exact attached Game, Saved plan and private custody");
            custody.requireCurrent();actualAttached.verify();
            core.requireRetainedConfirmedSaved(source);
            entered=true;game=actualAttached;
            lifecycle.adoptAttached(actualAttached);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,plan);
            actualAttached.nativeTransport().awaitHello(clock.instant().plus(config.operationTimeout()));
            var hello=actualAttached.nativeTransport().originalHello();
            var actualExecutionSource=new G2Source(actualAttached.machineId(),clock.instant().toString(),hello.gameSha256(),
                    metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            var sourceG2=core.retainedSavedBusinessSource(source,actualAttached,actualExecutionSource);
            var opened=new Opened(this,sourceG2);
            var installed=runOperationPhase(clock,config.operationTimeout(),until->
                    catalogs.install(core,actualAttached,sourceG2,core.planningReads(),clock,until));
            opened.installed=installed;
            record RetainedAdoption(RootJavaSavedBootstrap.RetainedSaved source,DriverBootstrap.Adopted driver) { }
            var adoption=runOperationPhase(clock,Duration.ofMinutes(10),until->{
                config.initialPolicy().requireInitialSavedProjection(plan,source.pair().save(),custody.savedClone());
                var retained=RootJavaSavedBootstrap.reopenLoaded(source,installed.context(),custody,until);
                return new RetainedAdoption(retained,core.adoptRetainedSaved(retained,sourceG2,config.retainedFrames(),until));
            });
            return opened.finishConfirmedSaved(adoption.driver(),Optional.of(adoption.source()),deadline);
        }

        /** Reopens the original Saved ledger and the same attached Game, without a new Saved admission. */
        public Running openOriginalLoadedSavedRecovery(org.xar.ck3.control.platform.RootProcessAttach.LoadedCustody custody,Instant deadline)
                throws IOException,InterruptedException {
            Objects.requireNonNull(custody);Objects.requireNonNull(deadline);
            var source=originalSavedRecoverySource;
            var actual=custody.game();
            if(source==null||actual.launchPlan()!=plan||!custody.pair().equals(source.pair()))
                throw new IOException("original Saved recovery requires its exact retained pair and attached Saved plan");
            custody.requireCurrent();
            if(config.initialPolicy().isMaterializedSaved())
                config.initialPolicy().requireInitialSavedProjection(plan,source.pair().save(),custody.savedClone());
            var running=openSameGameBootstrapOpened(open(actual),actual,Optional.empty(),deadline,false);
            custody.releasePreparation();
            return running;
        }

        public synchronized Running openConfirmedSaved(JavaGameLifecycle.Started started,
                RootJavaSavedBootstrap.ConfirmedSource confirmed,Instant deadline)throws IOException,InterruptedException {
            Objects.requireNonNull(started);Objects.requireNonNull(confirmed);Objects.requireNonNull(deadline);
            if(sourceOnly)throw new IOException("source-only reader cannot open confirmed Saved continuation");
            if(closed||entered||core!=null||game!=null)
                throw new IOException("confirmed saved graph is already consumed or closed");
            var actual=Objects.requireNonNull(started.session());
            if(actual.mode()!=ManagedGameSession.Mode.OWNED||actual.launchPlan()!=plan
                    ||!(plan.load() instanceof NativeLaunchPlan.SavedGame)
                    ||lifecycle.currentSession().orElse(null)!=actual)
                throw new IOException("confirmed saved bootstrap requires this exact owned Saved creator and plan");
            actual.verify();entered=true;game=actual;
            core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            core.bindFirstHeirMarriageEnabled(config.firstHeirMarriageEnabled());
            core.bindNewMarriageProposalsEnabled(config.newMarriageProposalsEnabled());
            if(config.operatorQuarantine().isPresent()) RootOperatorQuarantineRuntime.install(core,actual,config.operatorQuarantine().orElseThrow(),clock);
            ports.bindCore(core);catalogs.bindCore(core);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,plan);
            actual.nativeTransport().awaitHello(clock.instant().plus(config.operationTimeout()));
            var hello=actual.nativeTransport().originalHello();
            var source=new G2Source(actual.machineId(),clock.instant().toString(),hello.gameSha256(),
                    metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            var opened=new Opened(this,source);
            var installed=runOperationPhase(clock,config.operationTimeout(),until->
                    catalogs.install(core,actual,source,core.planningReads(),clock,until));
            opened.installed=installed;
            var driver=runOperationPhase(clock,Duration.ofMinutes(10),until->{
                config.initialPolicy().requireInitialSavedProjection(plan,confirmed.pair().save());
                var admission=RootJavaSavedBootstrap.admit(confirmed,installed.context(),lifecycle,started,until,config.initialPolicy());
                return core.adoptConfirmedSaved(admission,source,config.retainedFrames(),until);
            });
            return opened.finishConfirmedSaved(driver,deadline);
        }



        /** Source-proven retirement runs before any old-Game attachment and never creates or queries Game. */
        public synchronized ActionReceipt retireExitedLifeInterruptionOnly(Path ownerDescriptor,
                org.xar.ck3.control.contracts.GameGeneration expected,Instant deadline)throws IOException {
            var exited=openExitedOriginal(ownerDescriptor,expected,deadline);
            return core.retireExitedLifeInterruptionOnly(lifecycle,exited,deadline);
        }

        private JavaGameLifecycle.ExitedGeneration openExitedOriginal(Path ownerDescriptor,
                org.xar.ck3.control.contracts.GameGeneration expected,Instant deadline)throws IOException {
            Objects.requireNonNull(ownerDescriptor);Objects.requireNonNull(expected);Objects.requireNonNull(deadline);
            if(sourceOnly||closed||entered||core!=null||game!=null)
                throw new IOException("exited retirement requires the unused actual writable preparation");
            var configured=config.operatorQuarantine().orElseThrow(()->new IOException("exited retirement requires its new configured operator request"));
            var exited=lifecycle.qualifyExitedOwner(ownerDescriptor,expected,plan,deadline);
            exitedRecovery=exited;
            var actual=openSavedSourceCore();
            RootOperatorQuarantineRuntime.installExited(actual,lifecycle,exited,configured,clock,deadline);
            return exited;
        }

        /** A new source-qualified daemon restores the exact original pair in the same canonical writer. */
        public synchronized Running openExitedCheckpointRecovery(Path ownerDescriptor,
                org.xar.ck3.control.contracts.GameGeneration expected,Instant deadline)throws IOException,InterruptedException {
            return openExitedCheckpointRecovery(ownerDescriptor,expected,Optional.empty(),deadline);
        }

        public synchronized Running openExitedCheckpointRecovery(Path ownerDescriptor,
                org.xar.ck3.control.contracts.GameGeneration expected,ExactRef importedRecoveryRequest,
                Instant deadline)throws IOException,InterruptedException {
            return openExitedCheckpointRecovery(ownerDescriptor,expected,Optional.of(importedRecoveryRequest),deadline);
        }

        private Running openExitedCheckpointRecovery(Path ownerDescriptor,
                org.xar.ck3.control.contracts.GameGeneration expected,Optional<ExactRef> importedRecoveryRequest,
                Instant deadline)throws IOException,InterruptedException {
            var configuredDecision=config.decisionProvider().orElseThrow(()->
                    new IOException("exited checkpoint recovery requires its explicit decision provider"));
            RootOperatorQuarantineRuntime.requireRestorableOperatorRequest(config.operatorQuarantine().orElseThrow(() ->
                    new IOException("exited checkpoint recovery requires its configured operator request")),importedRecoveryRequest.isPresent());
            var exited=openExitedOriginal(ownerDescriptor,expected,deadline);
            RootApplicationAssembly.Core.ColdRestoreSource original;
            Optional<RootFrozenRunProfile.FrozenRunProfile> restoredProfile;
            if(importedRecoveryRequest.isPresent()) {
                var owner=new SessionIdentity(exited.machineId(),exited.generation(),exited.sourceSessionId());
                importedRestore=RootExitedSavedMaterialSource.prepareImportedRestore(importedRecoveryRequest.orElseThrow(),
                        core,config,files,owner,clock);
                var preflight=core.qualifyAndRetireExitedImported(lifecycle,exited,importedRestore,plan,
                        config.stateDirectory(),cyclePolicy,deadline);
                original=preflight.source();restoredProfile=preflight.profile();
            } else {
                core.retireExitedLifeInterruptionOnly(lifecycle,exited,deadline);
                var qualified=RootExitedSavedMaterialSource.qualify(core,config,lifecycle,exited,deadline);
                var material=core.writer().locked(same->{
                    if(!clock.instant().isBefore(deadline))throw new IOException("cold saved material qualification deadline expired");
                    var checked=core.archive().inHistoricalReadScope(same,
                            new org.xar.ck3.control.application.action.ActionPorts.HistoricalReadLimits(1024,64L*1024*1024,2052),
                            ignoredArchive->qualified.material(same));
                    if(!clock.instant().isBefore(deadline))throw new IOException("cold saved material qualification deadline expired");
                    return checked;
                });
                original=core.qualifyColdRestoreSource(lifecycle,exited,qualified.materials(),material,
                        qualified.driverCheckpoints(),cyclePolicy,deadline);
                restoredProfile=RootExitedSavedMaterialSource.nativeCampaignProfile(material,plan,clock);
            }
            var material=original.material();
            var before=original.archivedBefore();
            // These are explicitly archived facts. An exited generation supplies no current paused-map readiness.
            var current=new org.xar.ck3.control.application.checkpoint.CheckpointRequest.Readiness(before.identity(),before.source(),
                    before.sessionId(),material.pair().lineageId(),false,false,false,
                    "source-proven exited generation; archived original frame only; no current Game readiness",before.originalEvidence(),before.observedAt());
            String head=core.writer().locked(same->{original.requireCurrent(same);return same.head().digest();});
            String requestId=RootPublicRestoreRuntime.requestIdentity(original.previousOwner(),head,material.pair());
            var request=new org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.Request(requestId,material.pair(),current,head,deadline,material);
            var source=new G2Source(config.machineId(),clock.instant().toString(),plan.sources().review().gameExecutable().sha256(),
                    metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            var readiness=new RootRuntimeReadiness(core,policy,config.freshness(),clock);
            var publication=restoredProfile.isPresent()
                    ?new RootPostAdoptionCollector(core,ports,catalogs,readiness,config.freshness(),clock,restoredProfile.orElseThrow())
                    :RootPostAdoptionCollector.ordinary(core,ports,catalogs,readiness,config.freshness(),clock);
            var materials=RootRestoreMaterialFactory.exited(core.writer(),core.archive(),lifecycle,files,original,
                    metadata.implementation(RootRestoreMaterials.class),config.retainedFrames(),restoredProfile);
            var adapters=new RootRestoreAdapters(core.writer(),core.archive(),core.actions(),original,
                    original.materials().ordinaryStore(),original.materials(),materials,publication);
            core.bindColdRestoreAdapters(original,adapters);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,plan);
            var physical=original.importedSource().isPresent()
                    ?org.xar.ck3.control.platform.GameRestoreAdapter.importedExited(lifecycle,plan,exited,files,clock,
                            this::retainExitedStarted)
                    :new org.xar.ck3.control.platform.GameRestoreAdapter(lifecycle,plan,exited);
            var replacement=new org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.LifecyclePort() {
                @Override public org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.LaunchResult replaceOnce(
                        org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.Request actual)throws IOException,InterruptedException {
                    rememberExitedReplacement(actual.requestId());
                    var result=physical.replaceOnce(actual);retainExitedReplacement(actual.requestId());return result;
                }
                @Override public org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.LaunchResult query(String id,Instant until)throws IOException,InterruptedException {
                    rememberExitedReplacement(id);
                    var result=physical.query(id,until);retainExitedReplacement(id);return result;
                }
            };
            var nativeFrames=new org.xar.ck3.control.platform.GameRestoreNativeAdapter(lifecycle,source,material.pair().lineageId(),
                    core.archive(),core.writer(),core.writer()::activeSession,core.writer()::requireSession);
            var service=new org.xar.ck3.control.application.checkpoint.RestoreCheckpointService(files,original.driverCheckpoints(),replacement,
                    nativeFrames,core.writer(),original.materials(),adapters,adapters,clock);
            var result=service.restore(request);
            if(!(result instanceof org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.Restored restored))
                throw new IOException("exited restoration retains its exact original result and replacement; no relaunch: "+result);
            game=lifecycle.currentSession().orElseThrow(()->new IOException("actual restored owned Game unavailable"));
            var base=sessionConfiguration(deadline);var paths=base.checkpoints();
            var saveOutput=original.importedSource().isPresent()?importedCheckpointOutput(game.launchPlan(),material.pair()):
                    Path.of(material.pair().save().reference().path());
            var checkpoints=new RootStartupConfiguration.CheckpointPaths(paths.driverCheckpoint(),paths.checkpointEvidence(),paths.attachmentEvidence(),
                    material.pair().lineageId(),saveOutput);
            var configuration=new RootApplicationAssembly.FreshSessionConfiguration(base.authorityId(),base.policy(),base.freshness(),
                    checkpoints,base.cyclePolicy(),deadline);
            var selector=new RootOnlineDecisionSelector(configuredDecision,clock,raw->{
                var writer=core.writer();var active=writer.activeSession();
                if(active.isPresent())return core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                return writer.locked(same->core.archive().withSession(same).preserveMaterial(raw));
            });
            core.bindDecisionSelector(selector);
            var session=core.finishColdRestored(original,adapters,service,restored.binding(),game,configuration,services(source));
            session.install(ordinaryHost,deadline);
            return new Running(this,session,original.savedController().batchPrefix(),original.savedController().nextBatchSequence());
        }


        /** The newly held process has already loaded the separately preserved save. */
        synchronized Running openExternalSavedRecovery(ManagedGameSession attached, RootExternalSavedRecoveryInput input,
                Instant deadline) throws IOException, InterruptedException {
            if (sourceOnly || closed || entered || core != null || game != null || attached.launchPlan() != plan)
                throw new IOException("external saved recovery requires the unused original business preparation and actual successor");
            var decision = config.decisionProvider().orElseThrow(() -> new IOException("external saved recovery requires its explicit decision provider"));
            if (!decision.codexFile()) throw new IOException("external saved recovery requires the configured direct Codex file provider");
            var operator = config.operatorQuarantine().orElseThrow(() -> new IOException("external saved recovery requires the original operator decision"));
            var predecessor = RootProcessAttach.retainExternalSavedPredecessor(attached, input.departedOwner(), input.departed(), deadline);
            var request = input.remountFrom();
            Optional<RootProcessAttach.ExternalSavedPredecessor> remountFrom = Optional.empty();
            if (request.isPresent()) {
                var from = request.orElseThrow();
                remountFrom = Optional.of(RootProcessAttach.retainExternalSavedPredecessor(attached, from.owner(), from.game(), deadline));
            }
            var actual = openSavedSourceCore();
            RootOperatorQuarantineRuntime.installExternalSaved(actual, predecessor, operator, clock, deadline);
            game = attached;
            lifecycle.adoptAttached(attached);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle, plan);
            var driver = actual.adoptExternalSavedObservation(lifecycle, predecessor, remountFrom, input.namedSave(), input.dateRaw(), input.player(),
                    cyclePolicy, config.retainedFrames(), deadline);
            var installed = catalogs.install(actual, attached, driver.source(), actual.planningReads(), clock, deadline);
            var history = actual.externalSavedControllerHistory(driver);
            var saved = history.savedPair().orElseThrow();
            var configuration = retainImportedCheckpointPaths(sessionConfiguration(deadline), attached.launchPlan(), saved, saved, files);
            actual.bindDecisionSelector(new RootOnlineDecisionSelector(decision, clock, raw -> {
                var writer = actual.writer();
                var active = writer.activeSession();
                if (active.isPresent()) return actual.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                return writer.locked(same -> actual.archive().withSession(same).preserveMaterial(raw));
            }));
            var session = actual.finishExternalSavedObservation(installed, driver, configuration, services(driver.source()));
            session.install(ordinaryHost, deadline);
            return new Running(this, session, history.batchPrefix(), history.nextBatchSequence());
        }

        /** Same canonical writer and already-created Game. This route has no lifecycle replacement call. */
        public synchronized Running openLoadedCheckpointRecovery(
                org.xar.ck3.control.platform.ManagedGameSession attached,
                org.xar.ck3.control.platform.RootProcessAttach.LoadedReplacement loaded,
                RootLoadedReplacementRecoveryInputs.Request input)throws IOException,InterruptedException {
            Objects.requireNonNull(attached);Objects.requireNonNull(loaded);Objects.requireNonNull(input);
            var configuredDecision=config.decisionProvider().orElseThrow(()->new IOException("loaded recovery requires its explicit decision provider"));
            if(!configuredDecision.codexFile())throw new IOException("loaded recovery requires the configured direct Codex file provider");
            input.requireCurrent(clock);loaded.requireCurrent(input.deadline());
            if(sourceOnly||closed||entered||core!=null||game!=null||loaded.attached()!=attached
                    ||attached.mode()!=ManagedGameSession.Mode.ATTACHED||attached.launchPlan()!=plan
                    ||!config.machineId().equals(input.machineId())
                    ||!Path.of(input.ownerDescriptor().path()).equals(config.launchPlanFile())
                    ||!RootLoadedReplacementRecoveryInputs.same(
                            org.xar.ck3.control.build.ControlBuild.FileRef.measure(config.configurationFile()),input.runtimeConfiguration()))
                throw new IOException("loaded recovery requires its exact unused configured writer and actual read-only attached owner");
            var actualCore=openSavedSourceCore();
            actualCore.writer().locked(same->{
                storage.requireReadScope(same,files);
                if(!same.head().digest().equals(input.expectedHeadDigest()))throw new IOException("loaded recovery original predecessor changed");
                return null;
            });
            var configured=config.operatorQuarantine().orElseThrow(()->new IOException("loaded recovery requires its existing historical operator source"));
            RootOperatorQuarantineRuntime.installLoaded(actualCore,loaded,configured,clock,input.deadline());
            var qualified=RootExitedSavedMaterialSource.qualifyLoaded(actualCore,config,files,loaded,input.deadline());
            if(!qualified.pair().equals(input.pair()))throw new IOException("loaded source changed its original exact checkpoint pair");
            var material=actualCore.writer().locked(same->actualCore.archive().inHistoricalReadScope(same,
                    new org.xar.ck3.control.application.action.ActionPorts.HistoricalReadLimits(1024,64L*1024*1024,2052),
                    ignored->qualified.material(same)));
            var original=actualCore.qualifyLoadedRestoreSource(lifecycle,loaded,qualified.materials(),material,
                    qualified.driverCheckpoints(),cyclePolicy,input.deadline());
            Optional<RootFrozenRunProfile.FrozenRunProfile> frozen;
            if(input.mode()==RootLoadedReplacementRecoveryInputs.Mode.ORDINARY_PROFILE3) {
                actualCore.writer().locked(same->{
                    RootLoadedOrdinaryProfile.readExact(input.currentLoadedProfile(),input.savedPolicy(),input.runtimeConfiguration(),
                            plan,loaded,same,material,config.initialPolicy(),clock);return null;
                });
                frozen=Optional.empty();
            } else {
                var nativeProfile=RootFrozenRunProfile.readLoadedExact(input.currentLoadedProfile(),plan,input.savedPolicy(),loaded,clock);
                nativeProfile.requireExplicitNativeCampaign();frozen=Optional.of(nativeProfile);
            }
            var running=finishLoadedCheckpointRecovery(attached,loaded,original,frozen,configuredDecision,input.deadline());
            input.requireCurrent(clock);
            return running;
        }

        /** Bind the archived retired frontier and its two independent physical subjects before opening a Native pipe. */
        public synchronized RootProcessAttach.ImportedLoadedOriginals prepareImportedLoadedRecovery(
                RootLoadedReplacementRecoveryInputs.ImportedRequest input)throws IOException {
            Objects.requireNonNull(input);input.requireCurrent(clock);
            if(sourceOnly||closed||entered||core!=null||game!=null||!config.machineId().equals(input.machineId()))
                throw new IOException("imported loaded recovery requires an unused writer for the original machine");
            var configured=config.operatorQuarantine().orElseThrow(()->new IOException("imported recovery requires its configured original operator source"));
            var decision=RootOperatorQuarantineRuntime.readConfigured(configured);
            var exit=decision.exitedLife().orElseThrow(()->new IOException("imported recovery requires its original exited Life decision"));
            var departed=new SessionIdentity(decision.machineId(),decision.game(),exit.ownerSessionId());
            var actualCore=openSavedSourceCore();
            var retainedAttachment=actualCore.writer().locked(same->{
                storage.requireReadScope(same,files);
                var head=same.head();
                if(head.state().sequence()>input.expectedPredecessorSequence()) {
                    long sequence=Math.addExact(input.expectedPredecessorSequence(),1);
                    var path=Path.of(same.persistedHead().path()).resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS")
                            .resolve(String.format(java.util.Locale.ROOT,"%08d.json",sequence));
                    return Optional.of(head.documents().stream().filter(pin->Path.of(pin.reference().path()).equals(path))
                            .findFirst().orElseThrow(()->new IOException("original committed imported attachment is not in the canonical writer")));
                }
                requireImportedLoadedPredecessor(head,input,decision,departed);
                same.requireHistoricalHead(decision.expectedHeadSequence(),decision.expectedHeadDigest());
                var archive=actualCore.archive().withSession(same);
                var terminal=ContinuityActionJournal.lookup(head.state(),decision.parentActionId(),archive)
                        .orElseThrow(()->new IOException("missing canonical imported retirement"));
                if(terminal.sequence()!=input.expectedPredecessorSequence()
                        ||!(terminal.state() instanceof ActionState.CompositeOperatorQuarantined)
                        ||!terminal.command().sessionId().equals(departed.sessionId())
                        ||!terminal.command().origin().game().equals(departed.game())
                        ||!terminal.bodySha256().equals(decision.parentBodySha256())
                        ||!CompositeOperatorQuarantineObservation.load(terminal,archive).requestSource().equals(configured))
                    throw new IOException("imported loaded recovery requires its already-committed exact operator decision");
                return Optional.<WriterContracts.Pin>empty();
            });
            if(retainedAttachment.isPresent())return prepareCommittedImportedRecovery(input,retainedAttachment.orElseThrow(),actualCore);
            importedRestore=RootExitedSavedMaterialSource.prepareImportedRestore(input.originalRecoveryRequest(),
                    actualCore,config,files,departed,clock);
            var archived=importedRestore.imported();
            if(!archived.headDigest().equals(input.expectedHeadDigest()))
                throw new IOException("imported source changed its canonical retired frontier while reading the physical SAVE");
            String parent=RootPublicRestoreRuntime.requestIdentity(departed,input.expectedHeadDigest(),archived.pair());
            var originals=RootProcessAttach.readImportedLoadedOriginals(input.ownerDescriptor(),input.parentControl(),
                    input.generationClaim(),archived.pair(),departed,parent);
            input.requireCurrent(clock);
            actualCore.writer().locked(same->{requireImportedLoadedPredecessor(same.head(),input,decision,departed);return null;});
            importedLoadedRequest=input;importedLoadedOriginals=originals;
            return originals;
        }

        public synchronized Running openImportedLoadedCheckpointRecovery(ManagedGameSession attached,
                RootProcessAttach.LoadedReplacement loaded,RootLoadedReplacementRecoveryInputs.ImportedRequest input)
                throws IOException,InterruptedException {
            if(committedImportedStart!=null)return finishCommittedImportedRecovery(attached,loaded,input);
            input.requireCurrent(clock);
            if(input!=importedLoadedRequest||closed||game!=null||loaded.attached()!=attached
                    ||!loaded.ownerDescriptor().equals(input.ownerDescriptor())||!loaded.parentControl().equals(input.parentControl())
                    ||!loaded.generationClaim().equals(input.generationClaim())
                    ||!loaded.previousOwner().equals(importedLoadedOriginals.departed())
                    ||!loaded.cachedAck().importedSaveTransfer().filter(importedLoadedOriginals.transfer()::equals).isPresent())
                throw new IOException("imported loaded recovery crossed its qualified original owner or transfer");
            var configuredDecision=config.decisionProvider().orElseThrow(()->new IOException("loaded recovery requires its explicit decision provider"));
            if(!configuredDecision.codexFile())throw new IOException("loaded recovery requires its configured direct Codex file provider");
            var operator=config.operatorQuarantine().orElseThrow();
            RootOperatorQuarantineRuntime.installLoaded(core,loaded,operator,clock,input.deadline());
            var result=core.qualifyLoadedImportedRestoreSource(lifecycle,loaded,importedRestore,plan,config.stateDirectory(),cyclePolicy,input.deadline());
            var running=finishLoadedCheckpointRecovery(attached,loaded,result.source(),result.profile(),configuredDecision,input.deadline());
            input.requireCurrent(clock);
            return running;
        }

        /** Verifies the already committed attachment before opening a new READ connection to its successor. */
        private RootProcessAttach.ImportedLoadedOriginals prepareCommittedImportedRecovery(
                RootLoadedReplacementRecoveryInputs.ImportedRequest input,WriterContracts.Pin attachment,
                RootApplicationAssembly.Core actualCore)throws IOException {
            input.requireCurrent(clock);
            var start=actualCore.writer().locked(same->{
                storage.requireReadScope(same,files);
                var original=actualCore.readCommittedImportedStart(same,attachment,cyclePolicy);
                var basis=original.recoveryBasis();
                if(!basis.departed().machineId().equals(input.machineId())
                        ||basis.predecessorSequence()!=input.expectedPredecessorSequence()
                        ||!basis.predecessorDigest().equals(input.expectedHeadDigest())
                        ||!basis.lifecycleControl().reference().equals(input.parentControl())
                        ||!original.importedOrigin().recoveryRequest().equals(input.originalRecoveryRequest())
                        ||!original.savedPair().equals(input.original().pair()))
                    throw new IOException("committed imported recovery requires the same departed frontier, request and physical SAVE");
                var originals=RootProcessAttach.readImportedLoadedOriginals(input.ownerDescriptor(),input.parentControl(),
                        input.generationClaim(),original.savedPair(),basis.departed(),basis.requestId());
                if(!originals.owner().generation().equals(basis.successor().game())
                        ||!originals.owner().sessionId().equals(basis.successor().sessionId())
                        ||!originals.transfer().proof().equals(basis.transferProof().reference())
                        ||!originals.transfer().staged().reference().equals(basis.stagedLoad()))
                    throw new IOException("committed imported recovery crossed its successor owner or original LOAD transfer");
                same.verifyPin(basis.lifecycleControl());same.verifyPin(basis.transferProof());
                input.requireCurrent(clock);
                return new CommittedImportedStart(input,attachment,originals,original);
            });
            importedRestore=RootExitedSavedMaterialSource.reopenCommittedImportedRestore(start.readback(),actualCore,config,files,clock);
            input.requireCurrent(clock);
            committedImportedStart=start;
            return start.originals();
        }

        private Running finishCommittedImportedRecovery(ManagedGameSession attached,RootProcessAttach.LoadedReplacement loaded,
                RootLoadedReplacementRecoveryInputs.ImportedRequest input)throws IOException,InterruptedException {
            var configuredDecision=config.decisionProvider().orElseThrow(()->new IOException("committed imported recovery requires its explicit decision provider"));
            if(!configuredDecision.codexFile())throw new IOException("committed imported recovery requires the configured direct Codex file provider");
            var stage=readCommittedImportedRecovery(attached,loaded,input);
            var history=core.writer().locked(same->core.readCommittedImportedControllerHistory(same,stage.original().attachment(),cyclePolicy));
            var imported = stage.original().pair();
            var configuration=retainImportedCheckpointPaths(sessionConfiguration(input.deadline()),
                    attached.launchPlan(),imported,imported,files);
            var selector=new RootOnlineDecisionSelector(configuredDecision,clock,raw->{
                var writer=core.writer();var active=writer.activeSession();
                if(active.isPresent())return core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                return writer.locked(same->core.archive().withSession(same).preserveMaterial(raw));
            });
            core.bindDecisionSelector(selector);
            var session=core.finishCommittedImported(stage,configuration,services(stage.driver().source()),history);
            session.install(ordinaryHost,input.deadline());
            return new Running(this,session,history.batchPrefix(),history.nextBatchSequence());
        }

        synchronized CommittedImportedStage readCommittedImportedRecovery(ManagedGameSession attached,
                RootProcessAttach.LoadedReplacement loaded,RootLoadedReplacementRecoveryInputs.ImportedRequest input)
                throws IOException,InterruptedException {
            var start=committedImportedStart;
            if(start==null||start.input()!=input||closed||game!=null||loaded.attached()!=attached
                    ||attached.mode()!=ManagedGameSession.Mode.ATTACHED||attached.launchPlan()!=plan
                    ||!loaded.ownerDescriptor().equals(input.ownerDescriptor())||!loaded.parentControl().equals(input.parentControl())
                    ||!loaded.generationClaim().equals(input.generationClaim())
                    ||!loaded.previousOwner().equals(start.originals().departed())
                    ||loaded.cachedAck().importedSaveTransfer().filter(start.originals().transfer()::equals).isEmpty())
                throw new IOException("committed imported recovery crossed its prepared owner, Game or original transfer");
            input.requireCurrent(clock);loaded.requireCurrent(input.deadline());
            var operator=config.operatorQuarantine().orElseThrow(()->new IOException("committed imported recovery requires its original operator source"));
            RootOperatorQuarantineRuntime.installLoaded(core,loaded,operator,clock,input.deadline());
            game=attached;lifecycle.adoptAttached(attached);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,plan);
            var source=new G2Source(config.machineId(),clock.instant().toString(),attached.nativeTransport().originalHello().gameSha256(),
                    metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            var driver=core.adoptCommittedImported(attached,lifecycle,loaded,start.attachment(),source,config.retainedFrames(),input.deadline());
            var catalog=catalogs.install(core,attached,source,core.planningReads(),clock,input.deadline());
            return core.writer().locked(same->{
                var original=catalog.prepareCommittedImported(same,driver,start.attachment(),input.deadline());
                var domainOriginal=catalog.captureCommittedImportedDomainOriginal(same,original,importedRestore,input.deadline());
                return new CommittedImportedStage(driver,catalog,original,domainOriginal);
            });
        }

        private Running finishLoadedCheckpointRecovery(ManagedGameSession attached,RootProcessAttach.LoadedReplacement loaded,
                RootApplicationAssembly.Core.ColdRestoreSource original,Optional<RootFrozenRunProfile.FrozenRunProfile> frozen,
                RootOrdinaryRuntimeConfiguration.DecisionProvider configuredDecision,Instant deadline)throws IOException,InterruptedException {
            var actualCore=core;
            var material=original.material();
            var before=original.archivedBefore();
            var archived=new org.xar.ck3.control.application.checkpoint.CheckpointRequest.Readiness(before.identity(),before.source(),
                    before.sessionId(),material.pair().lineageId(),false,false,false,
                    "archived original before the actual already-created replacement; no current readiness granted",
                    before.originalEvidence(),before.observedAt());
            String head=actualCore.writer().locked(same->{original.requireCurrent(same);return same.head().digest();});
            String parent=RootPublicRestoreRuntime.requestIdentity(original.previousOwner(),head,material.pair());
            if(!parent.equals(loaded.originalParentId()))throw new IOException("existing replacement differs from the exact original restore identity");
            var request=new org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.Request(parent,material.pair(),archived,
                    head,loaded.originalDeadline(),material);
            loaded.requireOriginalRequest(request);
            game=attached;lifecycle.adoptAttached(attached);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,attached.launchPlan());
            var source=loadedExecutionSource(config.machineId(),clock.instant(),attached.launchPlan().sources().review().gameExecutable(),
                    before.source(),metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            var readiness=new RootRuntimeReadiness(actualCore,policy,config.freshness(),clock);
            var publication=frozen.isPresent()
                    ?new RootPostAdoptionCollector(actualCore,ports,catalogs,readiness,config.freshness(),clock,frozen.orElseThrow())
                    :RootPostAdoptionCollector.ordinary(actualCore,ports,catalogs,readiness,config.freshness(),clock);
            var materials=RootRestoreMaterialFactory.exited(actualCore.writer(),actualCore.archive(),lifecycle,files,original,
                    metadata.implementation(RootRestoreMaterials.class),config.retainedFrames(),frozen);
            var adapters=new RootRestoreAdapters(actualCore.writer(),actualCore.archive(),actualCore.actions(),original,
                    original.materials().ordinaryStore(),original.materials(),materials,publication);
            actualCore.bindColdRestoreAdapters(original,adapters);
            var physical=new org.xar.ck3.control.platform.GameRestoreAdapter(lifecycle,plan,loaded);
            var nativeFrames=new org.xar.ck3.control.platform.GameRestoreNativeAdapter(lifecycle,source,material.pair().lineageId(),
                    actualCore.archive(),actualCore.writer(),actualCore.writer()::activeSession,actualCore.writer()::requireSession,loaded);
            var service=new org.xar.ck3.control.application.checkpoint.RestoreCheckpointService(files,original.driverCheckpoints(),physical,
                    nativeFrames,actualCore.writer(),original.materials(),adapters,adapters,clock);
            java.time.Instant readDeadline=clock.instant().plus(java.time.Duration.ofMinutes(30));
            if(readDeadline.isAfter(deadline))readDeadline=deadline;
            var result=service.restoreExisting(request,readDeadline);
            if(!(result instanceof org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.Restored restored))
                throw new IOException("same existing replacement retains its original read result; no relaunch: "+result);
            var base=sessionConfiguration(readDeadline);var paths=base.checkpoints();
            var saveOutput=original.importedSource().isPresent()?importedCheckpointOutput(attached.launchPlan(),material.pair()):
                    Path.of(material.pair().save().reference().path());
            var checkpoints=new RootStartupConfiguration.CheckpointPaths(paths.driverCheckpoint(),paths.checkpointEvidence(),paths.attachmentEvidence(),
                    material.pair().lineageId(),saveOutput);
            var configuration=new RootApplicationAssembly.FreshSessionConfiguration(base.authorityId(),base.policy(),base.freshness(),
                    checkpoints,base.cyclePolicy(),readDeadline);
            var selector=new RootOnlineDecisionSelector(configuredDecision,clock,raw->{
                var writer=actualCore.writer();var active=writer.activeSession();
                if(active.isPresent())return actualCore.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                return writer.locked(same->actualCore.archive().withSession(same).preserveMaterial(raw));
            });
            actualCore.bindDecisionSelector(selector);
            var session=actualCore.finishColdRestored(original,adapters,service,restored.binding(),attached,configuration,services(source));
            session.install(ordinaryHost,readDeadline);
            return new Running(this,session,original.savedController().batchPrefix(),original.savedController().nextBatchSequence());
        }


        /** Retain the exact durable parent before replacement IO can return UNKNOWN after creating its child. */
        private synchronized void rememberExitedReplacement(String parent)throws IOException {
            StrictJson.text(parent);
            if(exitedOwnerParentRequest!=null&&!exitedOwnerParentRequest.equals(parent))
                throw new IOException("exited replacement cannot replace its original owner parent identity");
            exitedOwnerParentRequest=parent;
        }
        /** Original creator registry only; no PID open, lookup fallback, Stop or new capture. */
        private synchronized ManagedGameSession.CreatorOwnership exitedOriginalOwnership()throws IOException {
            if(exitedOriginalOwnership!=null)return exitedOriginalOwnership;
            if(exitedOwnerParentRequest==null)return null;
            String child=JavaGameLifecycle.replacementRequestId(exitedOwnerParentRequest);
            var original=lifecycle.startedOwner(child);
            if(original.isPresent()) {
                var actual=original.orElseThrow();
                StrictJson.require(actual.requestId().equals(child),"exited creator registry returned another child identity");
                exitedOriginalOwnership=actual;
            }
            return exitedOriginalOwnership;
        }
        private synchronized void retainExitedReplacement(String requestId)throws IOException {
            rememberExitedReplacement(requestId);
            if(lifecycle.queryReplacement(requestId) instanceof JavaGameLifecycle.Replaced replaced)
                retainExitedStarted(requestId,replaced.replacement());
        }
        /** Actual child HELLO ownership can be published before the parent's load/acceptance checks. */
        private synchronized void retainExitedStarted(String requestId,JavaGameLifecycle.Started started)throws IOException {
            rememberExitedReplacement(requestId);
            Path directory=exitedReplacementOwnerDirectory(config.stateDirectory(),requestId);
            if(exitedOwnerLifetime!=null) {
                if(exitedOwnerStart!=started||!directory.equals(exitedOwnerDirectory))
                    throw new IOException("exited replacement changed its original Started owner publication");
                return;
            }
            var actual=lifecycle.captureStartedOwner(started);
            if(exitedOriginalOwnership!=null&&exitedOriginalOwnership!=actual)
                throw new IOException("exited replacement changed its exact original creator custody");
            exitedOriginalOwnership=actual;
            var retained=org.xar.ck3.control.platform.SavedGameOwnerLifetime249.retain(lifecycle,started,directory);
            exitedOwnerStart=started;
            exitedOwnerDirectory=directory;
            exitedOwnerLifetime=retained;
        }
        public synchronized ManagedGameSession exitedReplacementGame()throws IOException {
            if(exitedOwnerStart==null)throw new IOException("exited restoration has no retained original replacement");
            return exitedOwnerStart.session();
        }
        public synchronized Path exitedReplacementOwnerDescriptor()throws IOException {
            if(exitedOwnerDirectory==null||exitedOwnerStart==null)
                throw new IOException("exited restoration has no published actual Saved owner");
            return exitedOwnerDirectory.resolve(org.xar.ck3.control.platform.GameSupervisorControl.DESCRIPTOR_FILE);
        }
        /** Reuse the existing Saved owner loop before the ordinary business finally may close its OWNED Game. */
        public void awaitExitedReplacementOwner()throws IOException,InterruptedException {
            var original=exitedOriginalOwnership();
            if(original==null) {
                if(exitedOwnerLifetime!=null)throw new IOException("published exited owner lost its original creator custody");
                return;
            }
            var lifetime=exitedOwnerLifetime;
            awaitOwnerAfterBusinessRelease(()->closeBusinessResources(core,storage),
                    ()->original.session().nativeTransport().close(),()->{
                        Throwable failure=null;
                        try {if(lifetime!=null)requireOwnerTerminalSuccess(lifetime.awaitExit());}
                        catch(IOException|InterruptedException|RuntimeException|Error awaiting){failure=awaiting;}
                        finally {
                            // Publication/observer failures cannot bypass the actual original Job root+empty proof.
                            var terminal=original.awaitOriginalExit();
                            try {
                                StrictJson.require(terminal.generation().equals(original.generation()),"creator terminal crossed original Game generation");
                                requireCreatorOwnerResult(terminal.terminal().exitCode(),terminal.kind(),terminal.resourcesClosed(),terminal.failures());
                            }catch(IOException|RuntimeException|Error cleanup){failure=merge(failure,cleanup);}
                        }
                        if(failure instanceof InterruptedException interrupted)throw interrupted;
                        if(failure!=null)throwClose(failure);
                    });
        }

        /** Opens only this configured old writer and source graph; it creates no Game or live authority. */
        public synchronized RootApplicationAssembly.Core openSavedSourceCore()throws IOException {
            if(closed||entered||core!=null||game!=null)
                throw new IOException("saved source graph is already consumed or closed");
            if(sourceOnly) {
                StorageWriteGuard.requireNoWritesOpen(noWrites);
                core=RootApplicationAssembly.openReadOnlySavedSource(app,clock,catalogs.domainRegistrations(),noWrites);
            } else {
                core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            }
            entered=true;
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            core.bindFirstHeirMarriageEnabled(config.firstHeirMarriageEnabled());
            core.bindNewMarriageProposalsEnabled(config.newMarriageProposalsEnabled());
            ports.bindCore(core);catalogs.bindCore(core);
            return core;
        }


        private synchronized void openCore(ManagedGameSession actual)throws IOException {
            if(sourceOnly)throw new IOException("source-only reader cannot open a live Core");
            if(closed||entered||(core!=null&&originalSavedRecoverySource==null)||loadedSavedSource!=null)throw new IOException("ordinary worker composition is already consumed or closed");
            Objects.requireNonNull(actual);
            if(actual.mode()!=ManagedGameSession.Mode.ATTACHED)throw new IOException("ordinary worker requires the actual supervisor attachment");
            entered=true;game=actual;lifecycle.adoptAttached(actual);
            if(core==null) {
            core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            core.bindFirstHeirMarriageEnabled(config.firstHeirMarriageEnabled());
            core.bindNewMarriageProposalsEnabled(config.newMarriageProposalsEnabled());
            if(config.operatorQuarantine().isPresent()) RootOperatorQuarantineRuntime.install(core,actual,config.operatorQuarantine().orElseThrow(),clock);
            ports.bindCore(core);catalogs.bindCore(core);
            } else if(config.operatorQuarantine().isPresent()) {
                RootOperatorQuarantineRuntime.install(core,actual,config.operatorQuarantine().orElseThrow(),clock);
            }
            if(originalSavedRecoverySource!=null)core.writer().locked(same->{
                var original=RootJavaSavedBootstrap.existingSavedSource(originalSavedRecoverySource,same,core.archive());
                var marker=org.xar.ck3.control.continuity.ContinuityJson.parseObject(original.getValue().details(),org.xar.ck3.control.contracts.StrictJson.INPUT_MAX_BYTES);
                var owner=org.xar.ck3.control.application.session.OrdinaryCycleTransitions.sessionFromJson(marker.get("session"));
                if(!owner.game().equals(actual.generation())||!owner.sessionId().equals(actual.sessionId()))throw new IOException("original Saved recovery attached another actual Game/session");
                return null;
            });
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,plan);
        }

        public Opened open(ManagedGameSession actual)throws IOException,InterruptedException {
            if(sourceOnly)throw new IOException("source-only reader cannot open live ordinary session");
            openCore(actual);
            actual.nativeTransport().awaitHello(clock.instant().plus(config.operationTimeout()));
            var hello=actual.nativeTransport().originalHello();
            var source=new G2Source(actual.machineId(),clock.instant().toString(),hello.gameSha256(),
                    metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            return new Opened(this,source);
        }

        /** Re-entry of the exact already-committed configured decision is ordinary recovery, never a new decision. */
        private boolean configuredOperatorRecoveryCommitted(RootApplicationAssembly.Core actualCore)throws IOException {
            var source=actualCore.operatorQuarantineSource().orElseThrow(()->new IOException("operator re-entry requires its installed configured source"));
            return actualCore.writer().locked(same->{
                var head=same.head();var originals=actualCore.archive().withSession(same);var request=source.request();
                var found=org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(head.state(),request.parentActionId(),originals);
                if(found.isEmpty()||!(found.orElseThrow().state() instanceof ActionState.CompositeOperatorQuarantined))return false;
                var terminal=found.orElseThrow();
                var observation=org.xar.ck3.control.application.action.CompositeOperatorQuarantineObservation.load(terminal,originals);
                org.xar.ck3.control.contracts.StrictJson.require(observation.requestSource().equals(source.requestReference()),
                        "operator re-entry cannot substitute a different configured decision or retained prior request");
                source.verify(same,head,terminal,originals);
                long recoverySequence=Math.addExact(terminal.sequence(),1);
                WriterContracts.HistoricalTransition recovery=null;
                for(var pin:head.documents()) {
                    String name=Path.of(pin.reference().path()).getFileName().toString();
                    if(name.equals(String.format(java.util.Locale.ROOT,"%08d.json",recoverySequence))) {
                        if(recovery!=null)throw new IOException("duplicate original operator recovery event");
                        recovery=same.readHistoricalTransition(pin);
                    }
                }
                if(recovery==null) {
                    if(request.reservedTailInterruption()) {
                        org.xar.ck3.control.contracts.StrictJson.require(head.state().sequence()==terminal.sequence()
                                &&!head.snapshotNeedsRecovery()&&head.indexRepairs().isEmpty(),"reserved terminal-only re-entry requires the complete exact current WAL and absent next event");
                        return false; // The explicit v3 branch below resumes recovery; it never re-appends retirement.
                    }
                    throw new IOException("configured operator terminal has no committed recovery; cannot repeat its original decision");
                }
                var keys=new java.util.HashSet<String>(java.util.Set.of("evidence_id","source","session","operation","predecessor_head_digest","receipt_ref","operator_observation",
                        "controller_ref","retained_driver","batch_id","next_sequence","consumed_batches","semantic"));
                if(request.reservedTailInterruption()){keys.add("completion_issued_at");keys.add("completion_deadline");}
                var details=org.xar.ck3.control.contracts.StrictJson.object(org.xar.ck3.control.contracts.StrictJson.parse(recovery.details()),keys);
                var owner=org.xar.ck3.control.application.session.OrdinaryCycleTransitions.sessionFromJson(details.get("session"));
                String operation=request.lifeInterruption()?"OPERATOR_LIFE_INTERRUPTION_RECOVERY":"OPERATOR_QUARANTINE_RECOVERY";
                String recoverySource=request.reservedTailInterruption()?"java-operator-life-interruption-recovery/v2":request.lifeInterruption()?"java-operator-life-interruption-recovery/v1":"java-operator-quarantine-recovery/v1";
                org.xar.ck3.control.contracts.StrictJson.require(recovery.sequence()==recoverySequence
                        &&org.xar.ck3.control.application.session.OrdinaryCycleTransitions.CYCLE_KIND.equals(recovery.kind())
                        &&operation.equals(org.xar.ck3.control.contracts.StrictJson.text(details.get("operation")))
                        &&recoverySource.equals(org.xar.ck3.control.contracts.StrictJson.text(details.get("source")))
                        &&owner.machineId().equals(request.machineId())&&owner.game().equals(request.game())&&owner.sessionId().equals(request.episodeRunId())
                        &&org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("receipt_ref")).equals(originals.receiptReferenceOf(terminal))
                        &&org.xar.ck3.control.contracts.ExactRef.fromJson(details.get("operator_observation")).equals(((ActionState.CompositeOperatorQuarantined)terminal.state()).observationRef())
                        &&org.xar.ck3.control.continuity.ContinuityJson.digest(recovery.before().toJson()).equals(org.xar.ck3.control.contracts.StrictJson.text(details.get("predecessor_head_digest")))
                        &&recovery.before().status()==org.xar.ck3.control.continuity.ContinuityState.Status.REPAIR_REQUIRED
                        &&recovery.after().status()==org.xar.ck3.control.continuity.ContinuityState.Status.RUNNING,
                        "operator re-entry requires its exact committed typed recovery and original predecessor/owner/observation");
                var atPoint=org.xar.ck3.control.application.action.ContinuityActionJournal.lookup(recovery.before(),request.parentActionId(),originals).orElseThrow();
                org.xar.ck3.control.contracts.StrictJson.require(java.util.Arrays.equals(
                        org.xar.ck3.control.application.action.ActionReceiptCodec.encodeReceipt(atPoint,originals),
                        org.xar.ck3.control.application.action.ActionReceiptCodec.encodeReceipt(terminal,originals)),
                        "operator recovery did not follow its exact canonical configured terminal");
                // The unchanged normal reader below independently validates all history, SEM, credit and the latest unknown action.
                return true;
            });
        }

        /** Explicit new operator decision; never a fresh campaign or replay fallback. */
        public Running openOperatorQuarantineRecovery(ManagedGameSession actual,Instant deadline)throws IOException,InterruptedException {
            if(config.operatorQuarantine().isEmpty())throw new IOException("operator-quarantine mode requires its explicit configured request pin");
            var opened=open(actual);
            var operator=opened.core().operatorQuarantineSource().orElseThrow();
            if(operator.request().reservedTailInterruption()) {
                // Administrative UNKNOWN_EFFECT retirement precedes generic Driver/history reconstruction.
                opened.core().retireReservedLifeInterruptionOnly(actual,deadline);
                if(configuredOperatorRecoveryCommitted(opened.core()))return openSameGameBootstrapOpened(opened,actual,Optional.empty(),deadline,false);
                var original=opened.core().readRetiredLifeInterruptionOriginal(actual,cyclePolicy);
                var driver=opened.core().adoptRetiredLifeInterruption(actual,original,config.retainedFrames(),deadline);
                return new Opened(this,driver.source()).finishRetiredLifeInterruption(driver,original,deadline);
            }
            if(configuredOperatorRecoveryCommitted(opened.core()))
                return openSameGameBootstrapOpened(opened,actual,Optional.empty(),deadline,false);
            var data=opened.core().readOperatorQuarantineOriginal(actual,cyclePolicy).orElseThrow(()->new IOException("operator recovery requires its original authoritative unresolved same-Game data"));
            var driver=runOperationPhase(clock,config.operationTimeout(),phaseDeadline->opened.core().adoptUnresolvedSameGame(actual,data,config.retainedFrames(),cyclePolicy,phaseDeadline));
            return new Opened(this,driver.source()).finishOperatorQuarantine(driver,data,deadline);
        }

public Running openSameGameBootstrap(ManagedGameSession actual, Optional<ContinuityBatchJournal.CleanRestartTicket> pointer, Instant deadline) throws IOException, InterruptedException {
    return openSameGameBootstrapInternal(actual, pointer, deadline, true);
}

/** Existing authoritative same-Game data only; this entry never creates an observed initial map. */
public Running openExistingSameGameRecovery(ManagedGameSession actual, Optional<ContinuityBatchJournal.CleanRestartTicket> pointer, Instant deadline) throws IOException, InterruptedException {
    return openSameGameBootstrapInternal(actual, pointer, deadline, false);
}

private Running openSameGameBootstrapInternal(ManagedGameSession actual, Optional<ContinuityBatchJournal.CleanRestartTicket> pointer, Instant deadline, boolean allowObservedInitial) throws IOException, InterruptedException {
    if(originalSavedRecoverySource!=null)throw new IOException("original Saved recovery must consume its actual loaded custody");
    return openSameGameBootstrapOpened(open(actual),actual,pointer,deadline,allowObservedInitial);
}

/** Reuses the one already-opened actual Core; existing readers retain all recovery authority. */
private Running openSameGameBootstrapOpened(Opened opened, ManagedGameSession actual, Optional<ContinuityBatchJournal.CleanRestartTicket> pointer, Instant deadline, boolean allowObservedInitial) throws IOException, InterruptedException {
    RootLifecycleAuthority.requireCapturedProjectionLinkage();
    // Mint once before DATA/history preparation. Only the Core's exact ARM role may consume this separate budget.
    final Instant armPreparationEnvelope=clock.instant().plus(java.time.Duration.ofMinutes(45));
    if (pointer.isPresent() && opened.core().matchesCleanRestartHead(pointer.orElseThrow())) {
        var driver = runOperationPhase(clock,java.time.Duration.ofMinutes(10),phaseDeadline->
                opened.core().adoptCleanRestart(actual,pointer.orElseThrow(),config.retainedFrames(),cyclePolicy,phaseDeadline,
                        ()->clock.instant().plus(java.time.Duration.ofMinutes(10))));
        return new Opened(this, driver.source()).finish(driver, Optional.of(opened.core().cleanRestartAdmission(driver)), deadline);
    }
    var settled = opened.core().readSettledSameGame(actual,cyclePolicy,files,checkpointPaths());
    if(settled.isPresent()) {
        var data=settled.orElseThrow();
        var driver=runOperationPhase(clock,config.operationTimeout(),phaseDeadline->
                opened.core().adoptSettledSameGame(actual,data,config.retainedFrames(),cyclePolicy,phaseDeadline));
        return new Opened(this,driver.source()).finishSettledSameGame(driver,data,deadline);
    }
    // Check for unresolved same-game data before initial/fresh recovery
    var unresolved = opened.core().readUnresolvedSameGame(actual,cyclePolicy);
    if (unresolved.isPresent()) {
        var unresolvedData=unresolved.orElseThrow();
        var driver = runOperationPhase(clock,config.operationTimeout(),phaseDeadline->
                opened.core().adoptUnresolvedSameGame(actual, unresolvedData, config.retainedFrames(), cyclePolicy, phaseDeadline, deadline, armPreparationEnvelope));
        return new Opened(this, driver.source()).finishUnresolvedSameGame(driver, unresolvedData, deadline);
    }
    if(originalSavedRecoverySource!=null)throw new IOException("original Saved recovery requires actual settled or qualified unresolved source; initial-entry fallback is forbidden");
    if (opened.core().hasCanonicalGameplayEntry()) {
        var driver = opened.core().adoptInitialRecovery(actual,config.retainedFrames(),cyclePolicy, () -> clock.instant().plus(config.operationTimeout()));
        return new Opened(this,driver.source()).finish(driver, Optional.empty(), deadline);
    }
    if (!allowObservedInitial) {
        throw new IOException("existing same-Game recovery requires authoritative settled, unresolved or canonical initial data; fresh observed map initialization is not permitted");
    }
    var outcome = runOperationPhase(clock,config.operationTimeout(),actual.nativeTransport()::readFreshFullState);
    if (!(outcome instanceof NativeFreshSnapshotPort.Received)) {
        throw new IOException("actual current-map full read unavailable: "+outcome);
    }
    var received = (NativeFreshSnapshotPort.Received) outcome;
    var initial = InitialDriverState.create(received.originalFrame(), actual.nativeTransport().pipeName(), plan.sessionId(), config.initialPolicy().kind(), config.initialPolicy().lifecycle());
    return runOperationPhase(clock,config.operationTimeout(),phaseDeadline->opened.finishObservedMap(received,initial,phaseDeadline));
}

        /** Independent read-only terminal entry. Does not install a Host, start a worker or continue/reconcile the parent. */
        public org.xar.ck3.control.application.action.ActionReceipt reconcilePostExitCleanupNoEffectOnly(ManagedGameSession actual,Instant deadline)
                throws IOException,InterruptedException {
            var opened=open(actual);
            var data=opened.core().readUnresolvedSameGame(actual,cyclePolicy)
                    .orElseThrow(()->new IOException("NoEffect-only reconciliation requires the exact existing unresolved same-Game data"));
            var driver=runOperationPhase(clock,config.operationTimeout(),until->
                    opened.core().adoptUnresolvedSameGame(actual,data,config.retainedFrames(),cyclePolicy,until));
            var retained=new Opened(this,driver.source());
            retained.consumed=true;
            retained.installed=runOperationPhase(clock,config.operationTimeout(),until->catalogs.install(core,game,driver.source(),core.planningReads(),clock,until));
            var configuration=runOperationPhase(clock,config.operationTimeout(),this::sessionConfiguration);
            var session=core.finishUnresolvedSameGame(retained.installed,driver,configuration,services(driver.source()));
            var life=retained.installed.remainingDomains().life();
            var token=life.postExitNoEffectReconciliation(deadline);
            return session.reconcilePostExitCleanupNoEffect(token);
        }

        /** Independent readonly fifth-child NoEffect entry; no ordinary Host, parent continuation or Native control. */
        public org.xar.ck3.control.application.action.ActionReceipt reconcilePreparedCleanupNoEffectOnly(ManagedGameSession actual,Instant deadline)
                throws IOException,InterruptedException {
            var opened=open(actual);
            var data=opened.core().readUnresolvedSameGame(actual,cyclePolicy)
                    .orElseThrow(()->new IOException("prepared NoEffect requires the exact unresolved same-Game history"));
            var driver=runOperationPhase(clock,config.operationTimeout(),until->
                    opened.core().adoptUnresolvedSameGame(actual,data,config.retainedFrames(),cyclePolicy,until));
            var retained=new Opened(this,driver.source());retained.consumed=true;
            retained.installed=runOperationPhase(clock,config.operationTimeout(),until->catalogs.install(core,game,driver.source(),core.planningReads(),clock,until));
            var configuration=runOperationPhase(clock,config.operationTimeout(),this::sessionConfiguration);
            var session=core.finishUnresolvedSameGame(retained.installed,driver,configuration,services(driver.source()));
            var token=retained.installed.remainingDomains().life().preparedCleanupNoEffectReconciliation(deadline);
            return session.reconcilePreparedCleanupNoEffect(token);
        }

        /** Independent readonly reserved-sixth NoEffect entry; no ordinary Host, parent continuation or Native control. */
        public org.xar.ck3.control.application.action.ActionReceipt reconcileReservedPreparedCleanupNoEffectOnly(ManagedGameSession actual,Instant deadline)
                throws IOException,InterruptedException {
            var opened=open(actual);
            var data=opened.core().readUnresolvedSameGame(actual,cyclePolicy)
                    .orElseThrow(()->new IOException("reserved NoEffect requires the exact unresolved same-Game history"));
            var driver=runOperationPhase(clock,config.operationTimeout(),until->
                    opened.core().adoptUnresolvedSameGame(actual,data,config.retainedFrames(),cyclePolicy,until));
            var retained=new Opened(this,driver.source());retained.consumed=true;
            retained.installed=runOperationPhase(clock,config.operationTimeout(),until->catalogs.install(core,game,driver.source(),core.planningReads(),clock,until));
            var configuration=runOperationPhase(clock,config.operationTimeout(),this::sessionConfiguration);
            var session=core.finishUnresolvedSameGame(retained.installed,driver,configuration,services(driver.source()));
            var reference=retained.installed.remainingDomains().life().reservedPreparedCleanupNoEffectProof(deadline);
            return session.reconcileReservedPreparedCleanupNoEffect(reference,deadline);
        }

        /** One independent C81 cleanup operation. No ordinary Host, Controller
         * loop, lifecycle action or Quarkus worker is installed or started here. */
        public PreparedCleanupResult finishPreparedCleanupOnly(ManagedGameSession actual,Instant deadline)throws IOException,InterruptedException {
            var opened=open(actual);
            var data=opened.core().readUnresolvedSameGame(actual,cyclePolicy).orElseThrow(()->new IOException("prepared cleanup requires its original unresolved same-Game data"));
            var driver=runOperationPhase(clock,config.operationTimeout(),until->opened.core().adoptUnresolvedSameGame(actual,data,config.retainedFrames(),cyclePolicy,until));
            var retained=new Opened(this,driver.source());retained.consumed=true;
            retained.installed=runOperationPhase(clock,config.operationTimeout(),until->catalogs.install(core,game,driver.source(),core.planningReads(),clock,until));
            var configuration=runOperationPhase(clock,config.operationTimeout(),this::sessionConfiguration);
            var session=core.finishUnresolvedSameGame(retained.installed,driver,configuration,services(driver.source()));
            var life=retained.installed.remainingDomains().life();
            var parent=core.actions().find("action-c1bbea09a8bffc735d1ac887e9c3020a1de4f59cca8d647378ec7a3efc47c5a8").orElseThrow();
            var token=life.composite().preparedCleanupToken(parent,deadline).orElseThrow(()->new IOException("actual Life source did not issue a new distinct prepared cleanup; existing/UNKNOWN is collection only"));
            session.continuePreparedCleanup(token);
            var child=core.actions().find(token.prepared().command().actionId()).orElseThrow();
            var current=core.actions().find(parent.command().actionId()).orElseThrow();
            return new PreparedCleanupResult(child,current,token.prepared().reference());
        }
        /** Distinct ordinal-six recovery only after actual canonical C5 NoEffect; never retries the fifth action. */
        public PreparedCleanupResult finishPreparedCleanupSuccessorOnly(ManagedGameSession actual,Instant deadline)throws IOException,InterruptedException {
            var opened=open(actual);
            var data=opened.core().readUnresolvedSameGame(actual,cyclePolicy).orElseThrow(()->new IOException("prepared successor requires its exact unresolved original history"));
            var driver=runOperationPhase(clock,config.operationTimeout(),until->opened.core().adoptUnresolvedSameGame(actual,data,config.retainedFrames(),cyclePolicy,until));
            var retained=new Opened(this,driver.source());retained.consumed=true;
            retained.installed=runOperationPhase(clock,config.operationTimeout(),until->catalogs.install(core,game,driver.source(),core.planningReads(),clock,until));
            var configuration=runOperationPhase(clock,config.operationTimeout(),this::sessionConfiguration);
            var session=core.finishUnresolvedSameGame(retained.installed,driver,configuration,services(driver.source()));
            var life=retained.installed.remainingDomains().life();
            var parent=core.actions().find("action-c1bbea09a8bffc735d1ac887e9c3020a1de4f59cca8d647378ec7a3efc47c5a8").orElseThrow();
            var token=life.composite().preparedCleanupSuccessorToken(parent,deadline)
                    .orElseThrow(()->new IOException("actual source did not issue a distinct ordinal-six preparation after canonical C5 NoEffect"));
            session.continuePreparedCleanup(token);
            var child=core.actions().find(token.prepared().command().actionId()).orElseThrow();
            var current=core.actions().find(parent.command().actionId()).orElseThrow();
            return new PreparedCleanupResult(child,current,token.prepared().reference());
        }
        public Running openCleanRestart(ManagedGameSession actual,ContinuityBatchJournal.CleanRestartTicket ticket,
                Instant deadline)throws IOException,InterruptedException {
            if(sourceOnly)throw new IOException("source-only reader cannot open clean restart");
            openCore(actual);
            var driver=runOperationPhase(clock,java.time.Duration.ofMinutes(10),phaseDeadline->
                    core.adoptCleanRestart(actual,Objects.requireNonNull(ticket),config.retainedFrames(),cyclePolicy,phaseDeadline));
            var admission=core.cleanRestartAdmission(driver);
            var opened=new Opened(this,driver.source());
            return opened.finish(driver,Optional.of(admission),deadline);
        }

        private RootStartupConfiguration.CheckpointPaths checkpointPaths() {
            Path state=config.stateDirectory();
            return new RootStartupConfiguration.CheckpointPaths(state.resolve("driver/checkpoint.json"),
                    state.resolve("checkpoints/evidence"),state.resolve("checkpoints/attachments"),config.authorityId()+"-lineage",
                    plan.profileDirectory().resolve("save games/xar_checkpoint.ck3"));
        }

        private RootApplicationAssembly.FreshSessionConfiguration sessionConfiguration(Instant deadline)throws IOException {
            var checkpoints=checkpointPaths();
            for(Path directory:List.of(checkpoints.driverCheckpoint().getParent(),checkpoints.checkpointEvidence(),
                    checkpoints.attachmentEvidence(),checkpoints.save().getParent()))storage.createManagedDirectories(directory);
            return new RootApplicationAssembly.FreshSessionConfiguration(config.authorityId(),policy,config.freshness(),checkpoints,cyclePolicy,deadline);
        }

        private RootApplicationAssembly.FreshSessionServices services(G2Source source)throws IOException {
            var offline=new RootOfflineAnalysisWorker.Prepared(new RootOfflineAnalysisWorker.Settings(
                    new OfflineAnalysisWorker.Settings(config.stateDirectory().resolve("offline/work"),4,128),
                    config.stateDirectory().resolve("offline/knowledge"),config.stateDirectory().resolve("offline/grants.json")),storage,files);
            core.bindOrdinaryOfflineWorker(offline,storage);
            var readiness=new RootRuntimeReadiness(core,policy,config.freshness(),clock);
            return new RootApplicationAssembly.FreshSessionServices(files,offline,new SessionClock.SystemClock(),
                    new RootEpisodeContinuationRuntime(core,catalogs),new RootM7CheckpointCaptureFactory(core.writer(),
                    core.writer()::requireSession,core.journal(),core.archive(),new RootCheckpointRuntimeAuthority(core,catalogs)),
                    RootRestoreMaterialFactory.ordinary(lifecycle,source.sourceRef(),config.retainedFrames(),game),
                    RootPostAdoptionCollector.ordinary(core,ports,catalogs,readiness,config.freshness(),clock));
        }

        /** Drain only Core/catalog/offline/storage custody before a retained Saved owner wait. */
        void closeBusinessResourcesOnly()throws IOException {closeBusinessResources(core,storage);}
        public void closeResourcesOnly()throws IOException {close();}
        @Override public synchronized void close()throws IOException {
            if(closed)return;closed=true;Throwable failure=closeBusinessResourcesFailure(core,storage);
            if(sourceOnly) {
                try {noWrites.close();}catch(IOException|RuntimeException|Error close){failure=merge(failure,close);}
                try {storage.close();}catch(IOException|RuntimeException|Error close){failure=merge(failure,close);}
            }
            if(importedRestore!=null)try {importedRestore.close();}catch(IOException|RuntimeException|Error close){failure=merge(failure,close);}
            if(game!=null)try {game.close();}catch(IOException|RuntimeException|Error close){failure=merge(failure,close);}
            if(failure!=null)throwClose(failure);
        }
    }

    public static final class Opened implements AutoCloseable {
        private final Prepared owner;
        private final G2Source source;
        private RootInstalledCatalog installed;
        private boolean consumed;
        private Opened(Prepared owner,G2Source source){this.owner=owner;this.source=source;}
        public RootApplicationAssembly.Core core(){return owner.core;}
        public G2Source source(){return source;}
        public RootInstalledCatalog catalog(){return Objects.requireNonNull(installed,"actual catalog is not installed yet");}
public Running finishObservedMap(NativeFreshSnapshotPort.Received received, InitialDriverState.Produced initial, Instant deadline) throws IOException, InterruptedException {
    if (consumed) {
        throw new IOException("ordinary physical adoption is already consumed");
    }
    consumed = true;
    var driver = owner.core.adoptObservedMap(owner.game, received, initial, source, owner.config.retainedFrames(), deadline);
    return finish(driver, Optional.empty(), deadline);
}

        public Running finishFresh(org.xar.ck3.control.application.action.NativeActionPort.AckReceived originalStartAck,
                NativeFreshSnapshotPort.Received received,InitialDriverState.Produced initial,
                Instant deadline)throws IOException,InterruptedException {
            if(consumed)throw new IOException("ordinary physical adoption is already consumed");
            consumed=true;
            var driver=owner.core.adoptFresh(owner.game,originalStartAck,received,initial,source,owner.config.retainedFrames(),deadline);
            return finish(driver,Optional.empty(),deadline);
        }
        private Running finish(DriverBootstrap.Adopted driver,Optional<ContinuityBatchJournal.CleanRestartAdmission> restart,
                Instant deadline)throws IOException,InterruptedException {
            var noDispatch=owner.core.initialNoDispatchRecovery(driver);
            if(noDispatch.isPresent()&&!noDispatch.orElseThrow().batchPrefix().equals(owner.config.loop().batchIdPrefix()))
                throw new IOException("initial no-dispatch recovery changed the original batch prefix");
            consumed=true;
            if (owner.config.decisionProvider().isPresent()) {
                var selector = new RootOnlineDecisionSelector(owner.config.decisionProvider().orElseThrow(), owner.clock, raw -> {
                    var writer = owner.core.writer();
                    var active = writer.activeSession();
                    if (active.isPresent()) return owner.core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                    return writer.locked(same -> owner.core.archive().withSession(same).preserveMaterial(raw));
                });
                owner.core.bindDecisionSelector(selector);
            }
            installed=runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->
                    owner.catalogs.install(owner.core,owner.game,source,owner.core.planningReads(),owner.clock,phaseDeadline));
            var configuration=runOperationPhase(owner.clock,owner.config.operationTimeout(),owner::sessionConfiguration);
            var services=owner.services(source);
            RootApplicationSession session;
            if (restart.isPresent()) {
                session = owner.core.finishCleanRestart(installed, driver, configuration, services);
            } else if (owner.core.initialRecoveryAdmission(driver).isPresent()) {
                session = owner.core.finishInitialRecovery(installed, driver, configuration, services);
            } else {
                session = owner.core.finishFresh(installed, driver, configuration, services);
            }
            runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->{
                session.install(owner.ordinaryHost,phaseDeadline);
                return null;
            });
            String prefix=restart.isPresent()?restart.orElseThrow().controller().batchPrefix():
                    noDispatch.map(ContinuityBatchJournal.InitialNoDispatchRecovery::batchPrefix).orElse(owner.config.loop().batchIdPrefix());
            long next=restart.isPresent()?restart.orElseThrow().controller().nextBatchSequence():
                    noDispatch.map(ContinuityBatchJournal.InitialNoDispatchRecovery::nextBatchSequence).orElse(0L);
            return new Running(owner,session,prefix,next);
        }

        private Running finishConfirmedSaved(DriverBootstrap.Adopted driver,Instant deadline)throws IOException,InterruptedException {
            return finishConfirmedSaved(driver,Optional.empty(),deadline);
        }
        private Running finishConfirmedSaved(DriverBootstrap.Adopted driver,Optional<RootJavaSavedBootstrap.RetainedSaved> retained,
                Instant deadline)throws IOException,InterruptedException {
            try {
                if(consumed||installed==null)throw new IOException("actual saved graph installation is unavailable or consumed");
                long next=0L;
                if(retained.isPresent()) {
                    var actual=retained.orElseThrow();
                    owner.core.writer().locked(same->{actual.requireProjectionCurrent(same);return null;});
                    String prefix=owner.config.loop().batchIdPrefix();long previous=-1L;
                    for(String id:actual.consumedBatchIds()) {
                        if(!id.startsWith(prefix+"-"))throw new IOException("retained Saved batch prefix differs from actual loop configuration");
                        String ordinal=id.substring(prefix.length()+1);
                        if(!ordinal.matches("0|[1-9][0-9]*"))throw new IOException("retained Saved batch ordinal is not canonical");
                        long value=new java.math.BigInteger(ordinal).longValueExact();
                        if(value<=previous)throw new IOException("retained Saved batch IDs are not strictly ordered and unique");
                        previous=value;
                    }
                    next=actual.nextSequence();
                    if(next!=(previous<0?0L:Math.addExact(previous,1L)))
                        throw new IOException("retained Saved next batch sequence differs from its actual consumed IDs");
                }
                consumed=true;
                if(owner.config.decisionProvider().isPresent()) {
                    var selector=new RootOnlineDecisionSelector(owner.config.decisionProvider().orElseThrow(),owner.clock,raw->{
                        var writer=owner.core.writer();var active=writer.activeSession();
                        if(active.isPresent())return owner.core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                        return writer.locked(same->owner.core.archive().withSession(same).preserveMaterial(raw));
                    });
                    owner.core.bindDecisionSelector(selector);
                }
                var configuration=runOperationPhase(owner.clock,owner.config.operationTimeout(),owner::sessionConfiguration);
                var session=owner.core.finishConfirmedSaved(installed,driver,configuration,owner.services(source));
                runOperationPhase(owner.clock,owner.config.operationTimeout(),until->{
                    session.install(owner.ordinaryHost,until);return null;
                });
                if(retained.isPresent())owner.core.writer().locked(same->{retained.orElseThrow().requireProjectionCurrent(same);return null;});
                owner.core.promoteSavedLive(session);
                return new Running(owner,session,owner.config.loop().batchIdPrefix(),next);
            }catch(IOException|InterruptedException|RuntimeException|Error failure) {
                // Admission, phase work and release share the original source-custody owner thread.
                // Successful promotion releases through activateSavedLive; an early failure owns this cleanup.
                try {owner.core.closeSavedProjectionCustody();}
                catch(IOException|RuntimeException|Error cleanup) {
                    if(cleanup!=failure)failure.addSuppressed(cleanup);
                }
                throw failure;
            }
        }

        private Running finishSettledSameGame(DriverBootstrap.Adopted driver,
                ContinuityBatchJournal.SettledSameGameData data,Instant deadline)throws IOException,InterruptedException {
            consumed=true;
            if(owner.config.decisionProvider().isPresent()) {
                var selector=new RootOnlineDecisionSelector(owner.config.decisionProvider().orElseThrow(),owner.clock,raw->{
                    var writer=owner.core.writer();var active=writer.activeSession();
                    if(active.isPresent())return owner.core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                    return writer.locked(same->owner.core.archive().withSession(same).preserveMaterial(raw));
                });
                owner.core.bindDecisionSelector(selector);
            }
            installed=runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->
                    owner.catalogs.install(owner.core,owner.game,source,owner.core.planningReads(),owner.clock,phaseDeadline));
            var configuration=runOperationPhase(owner.clock,owner.config.operationTimeout(),owner::sessionConfiguration);
            if (data.startingPoint() instanceof ContinuityBatchJournal.SameGameEntry.CommittedImportedRebind imported) {
                configuration = retainImportedCheckpointPaths(configuration,owner.game.launchPlan(),
                        imported.importedPair(),data.controller().savedPair().orElseThrow(),owner.files);
            }
            var session=owner.core.finishSettledSameGame(installed,driver,configuration,owner.services(source));
            owner.core.completeSettledEventOutcomeOnly(session,data,deadline);
            runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->{
                session.install(owner.ordinaryHost,phaseDeadline);return null;
            });
            return new Running(owner,session,data.controller().batchPrefix(),data.controller().nextBatchSequence());
        }

        private Running finishRetiredLifeInterruption(DriverBootstrap.Adopted driver,ContinuityBatchJournal.RetiredLifeInterruptionOriginal original,Instant deadline)throws IOException,InterruptedException {
            consumed=true;
            if(owner.config.decisionProvider().isPresent()) {
                var selector=new RootOnlineDecisionSelector(owner.config.decisionProvider().orElseThrow(),owner.clock,raw->{
                    var writer=owner.core.writer();var active=writer.activeSession();
                    if(active.isPresent())return owner.core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                    return writer.locked(same->owner.core.archive().withSession(same).preserveMaterial(raw));
                });owner.core.bindDecisionSelector(selector);
            }
            installed=runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->owner.catalogs.install(owner.core,owner.game,source,owner.core.planningReads(),owner.clock,phaseDeadline));
            var configuration=runOperationPhase(owner.clock,owner.config.operationTimeout(),owner::sessionConfiguration);
            var session=owner.core.finishUnresolvedSameGame(installed,driver,configuration,owner.services(source));
            long next=owner.core.completeRetiredLifeInterruptionRecovery(session,driver,original);
            runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->{session.install(owner.ordinaryHost,phaseDeadline);return null;});
            return new Running(owner,session,original.retainedHistory().controller().batchPrefix(),next);
        }
        private Running finishOperatorQuarantine(DriverBootstrap.Adopted driver,ContinuityBatchJournal.UnresolvedSameGameData data,Instant deadline)throws IOException,InterruptedException {
            consumed=true;
            if(owner.config.decisionProvider().isPresent()) {
                var selector=new RootOnlineDecisionSelector(owner.config.decisionProvider().orElseThrow(),owner.clock,raw->{
                    var writer=owner.core.writer();var active=writer.activeSession();
                    if(active.isPresent())return owner.core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                    return writer.locked(same->owner.core.archive().withSession(same).preserveMaterial(raw));
                });owner.core.bindDecisionSelector(selector);
            }
            installed=runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->owner.catalogs.install(owner.core,owner.game,source,owner.core.planningReads(),owner.clock,phaseDeadline));
            var configuration=runOperationPhase(owner.clock,owner.config.operationTimeout(),owner::sessionConfiguration);
            var session=owner.core.finishUnresolvedSameGame(installed,driver,configuration,owner.services(source));
            long next=owner.core.completeOperatorQuarantineRecovery(session,driver,data);
            runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->{session.install(owner.ordinaryHost,phaseDeadline);return null;});
            return new Running(owner,session,data.capturedController().batchPrefix(),next);
        }

        private Running finishUnresolvedSameGame(DriverBootstrap.Adopted driver, ContinuityBatchJournal.UnresolvedSameGameData data, Instant deadline) throws IOException, InterruptedException {
            consumed=true;
            if (owner.config.decisionProvider().isPresent()) {
                var selector = new RootOnlineDecisionSelector(owner.config.decisionProvider().orElseThrow(), owner.clock, raw -> {
                    var writer = owner.core.writer();
                    var active = writer.activeSession();
                    if (active.isPresent()) return owner.core.archive().withSession(active.orElseThrow()).preserveMaterial(raw);
                    return writer.locked(same -> owner.core.archive().withSession(same).preserveMaterial(raw));
                });
                owner.core.bindDecisionSelector(selector);
            }
            installed=runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->
                    owner.catalogs.install(owner.core,owner.game,source,owner.core.planningReads(),owner.clock,phaseDeadline));
            var configuration=runOperationPhase(owner.clock,owner.config.operationTimeout(),owner::sessionConfiguration);
            var services=owner.services(source);
            RootApplicationSession session = owner.core.finishUnresolvedSameGame(installed, driver, configuration, services);
            runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->{
                session.install(owner.ordinaryHost,phaseDeadline);
                return null;
            });
            // Restore quarantine and reconcile unresolved action
            session.restoreUnresolvedSameGame(data);
            // The original mutation is read-only here; closing its retained cycle can
            // require a fresh full semantic read and multiple durable ledger commits.
            org.xar.ck3.control.application.action.ActionReceipt receipt = null;
            if (data.unresolvedActions().size() == 1
                    && data.unresolvedActions().getFirst().command().operation().value().equals("private-assign-councillor-v1")) {
                var original = data.unresolvedActions().getFirst();
                receipt = runOperationPhase(owner.clock, java.time.Duration.ofMinutes(10), phaseDeadline -> {
                    var recovered = session.recoverOriginalCouncil(original.command().actionId(), phaseDeadline);
                    return recovered.settled() ? session.reconcileUnresolvedOriginal(data, phaseDeadline) : recovered;
                });
            }
            if (data.unresolvedActions().size() == 1) {
                var retainedOriginal = data.unresolvedActions().getFirst();
                if (org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(retainedOriginal.command().operation().value())) {
                    receipt = runOperationPhase(owner.clock, java.time.Duration.ofMinutes(10), phaseDeadline -> {
                        var life=installed.remainingDomains().life().composite();
                        if(retainedOriginal.state() instanceof ActionState.CompositeUnknown unknown
                                &&unknown.reason().startsWith(org.xar.ck3.control.application.advance.LifePostResumePauseCleanupEvidence.CURSOR_PREFIX))
                            return session.reconcileUnresolvedOriginal(data,phaseDeadline);
                        var postResumeCancellation=life.postResumePauseCancellationToken(retainedOriginal,phaseDeadline);
                        if(postResumeCancellation.isPresent()) {
                            session.continueOriginalComposite(postResumeCancellation.orElseThrow());
                            return session.reconcileUnresolvedOriginal(data,phaseDeadline);
                        }
                        var cancellation = life.cancellationToken(retainedOriginal, phaseDeadline);
                        if (cancellation.isEmpty()) return null;
                        session.continueOriginalComposite(cancellation.orElseThrow());
                        return session.reconcileUnresolvedOriginal(data, phaseDeadline);
                    });
                }
            }
            boolean attemptedLifeCancellation = receipt != null;
            if (receipt == null) {
                receipt = runOperationPhase(owner.clock, java.time.Duration.ofMinutes(10), phaseDeadline -> {
                    var first = session.reconcileUnresolvedOriginal(data, phaseDeadline);
                    if (first.settled()) return first;
                    var command = first.command();
                    if (!command.operation().value().equals("save-checkpoint")) return first;
                    var dispatch = ActionTransitions.dispatch(first.state());
                    if (dispatch.isEmpty() || !(dispatch.orElseThrow() instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk()) return first;
                    var state = first.state();
                    if (!(state instanceof ActionState.Unknown unknown) || !unknown.reason().equals("SAVE awaits second stable physical observation")) return first;
                    return session.reconcileUnresolvedOriginal(data, phaseDeadline);
                });
            }
            if (receipt != null && !receipt.settled()
                    && !attemptedLifeCancellation
                    && org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(receipt.command().operation().value())) {
                var original = receipt;
                receipt = runOperationPhase(owner.clock, java.time.Duration.ofMinutes(10), phaseDeadline -> {
                    var source = installed.remainingDomains().life().composite();
                    if(original.state() instanceof ActionState.CompositeUnknown unknown
                            &&unknown.reason().startsWith(org.xar.ck3.control.application.advance.LifePostResumePauseCleanupEvidence.CURSOR_PREFIX))
                        return session.reconcileUnresolvedOriginal(data,phaseDeadline);
                    var postResumeCancellation=source.postResumePauseCancellationToken(original,phaseDeadline);
                    if(postResumeCancellation.isPresent()) {
                        session.continueOriginalComposite(postResumeCancellation.orElseThrow());
                        return session.reconcileUnresolvedOriginal(data,phaseDeadline);
                    }
                    var cancellation = source.cancellationToken(original, phaseDeadline);
                    if (cancellation.isEmpty()) return original;
                    session.continueOriginalComposite(cancellation.orElseThrow());
                    // Consume the real retained settlement through the existing Controller/cycle path; no replay of the parent run.
                    return session.reconcileUnresolvedOriginal(data, phaseDeadline);
                });
            }
            if (receipt == null || !receipt.settled() || session.controllerForPublication().isQuarantined()) {
                throw new IOException("unresolved same-game action remains isolated; cannot proceed to ordinary loop");
            }
            return new Running(owner, session, data.capturedController().batchPrefix(), data.nextBatchSequence());
        }
        public void closeResourcesOnly()throws IOException {owner.close();}
        @Override public void close()throws IOException {owner.close();}
    }

    public static final class Running implements AutoCloseable {
        private final Prepared owner;
        private final RootApplicationSession session;
        private final String prefix;
        private final long next;
        private Running(Prepared owner,RootApplicationSession session,String prefix,long next) {
            this.owner=owner;this.session=session;this.prefix=prefix;this.next=next;
        }
        public RootApplicationAssembly.Core core(){return owner.core;}
        public RootApplicationSession session(){return session;}
        public org.xar.ck3.control.service.mcp.McpExecutableDirectory.Complete installPublic(
                org.xar.ck3.control.service.mcp.PublicMcpHost host) throws IOException, InterruptedException {
            return owner.installPublic(this, host);
        }
        /** This private Running is issued only after actual Driver/Root adoption; DATA cannot supply its catalog. */
        public RootInstalledCatalog catalog() throws IOException {
            synchronized (owner) {
                if (owner.closed || owner.core == null || owner.game == null
                        || owner.core.sessionAccess().current() != session)
                    throw new IOException("public attachment requires the identical live admitted Running owner");
                owner.game.verify();
                var actual = owner.catalogs.requireCurrentCatalog(session.identity());
                if (actual.context().core() != owner.core || actual.context().actions() != session)
                    throw new IOException("public attachment lost its identical actual Core/catalog/Root");
                return actual;
            }
        }
        public String batchPrefix(){return prefix;}
        public long nextBatchSequence(){return next;}
        public void closeResourcesOnly()throws IOException {owner.close();}
        @Override public void close()throws IOException {owner.close();}
    }

    @FunctionalInterface interface BusinessRelease {void run()throws IOException;}
    @FunctionalInterface interface OwnerWait {void run()throws IOException,InterruptedException;}

    /** Consumes only the DATA returned by the original opaque creator wait; it issues no exit proof. */
    static void requireCreatorOwnerResult(int exitCode,org.xar.ck3.control.contracts.GameLifecycle.TerminalKind kind,
            boolean resourcesClosed,List<Throwable> failures)throws IOException {
        Objects.requireNonNull(kind);
        Throwable failure=null;
        for(Throwable original:List.copyOf(failures))failure=merge(failure,original);
        if(kind==org.xar.ck3.control.contracts.GameLifecycle.TerminalKind.UNKNOWN)
            failure=merge(failure,new IOException("original creator owner terminal remains UNKNOWN"));
        if(!resourcesClosed)failure=merge(failure,new IOException("original creator owner resources remain unclosed"));
        if(kind==org.xar.ck3.control.contracts.GameLifecycle.TerminalKind.NATURAL_EXIT&&exitCode!=0)
            failure=merge(failure,new IOException("original creator owner natural exit returned failure "+exitCode));
        if(failure!=null)throwClose(failure);
    }
    /** Preserve a failed original Saved owner result through the void cleanup callback. */
    static void requireOwnerTerminalSuccess(int actualExit)throws IOException {
        if(actualExit!=0)throw new IOException("original Saved owner terminal returned failure "+actualExit);
    }

    /** Business-only drain. No Game/session/lifetime object or shutdown authority enters this method. */
    static void closeBusinessResources(RootApplicationAssembly.Core core,RootRuntimeStorageGuard storage)throws IOException {
        Throwable failure=closeBusinessResourcesFailure(core,storage);
        if(failure!=null)throwClose(failure);
    }
    private static Throwable closeBusinessResourcesFailure(RootApplicationAssembly.Core core,RootRuntimeStorageGuard storage) {
        Throwable failure=null;
        if(core!=null) {
            try {core.close();}catch(RuntimeException|Error close){failure=close;}
            try {core.closeCompletion().toCompletableFuture().join();}
            catch(RuntimeException|Error close){failure=merge(failure,close);}
        }else try {storage.close();}catch(IOException|RuntimeException|Error close){failure=close;}
        return failure;
    }
    static Path exitedReplacementOwnerDirectory(Path stateDirectory,String parentRequestId) {
        return stateDirectory.resolve("restored-owner-"+org.xar.ck3.control.application.action.ActionCodec.sha256(
                parentRequestId.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }

    /** Cleanup failures remain observable after the original single-use owner wait, never bypass it. */
    static void awaitOwnerAfterBusinessRelease(BusinessRelease business,BusinessRelease transport,OwnerWait owner)
            throws IOException,InterruptedException {
        Throwable failure=null;
        try {business.run();}catch(IOException|RuntimeException|Error close){failure=close;}
        try {transport.run();}catch(IOException|RuntimeException|Error close){failure=merge(failure,close);}
        try {owner.run();}catch(IOException|InterruptedException|RuntimeException|Error waiting){failure=merge(failure,waiting);}
        if(failure instanceof InterruptedException interrupted)throw interrupted;
        if(failure!=null)throwClose(failure);
    }

    private static Throwable merge(Throwable first,Throwable next) {
        if(first==null)return next;if(first!=next)first.addSuppressed(next);return first;
    }
    private static void throwClose(Throwable actual)throws IOException {
        Throwable failure=actual;
        while((failure instanceof CompletionException||failure instanceof UncheckedIOException)&&failure.getCause()!=null)
            failure=failure.getCause();
        if(failure instanceof Error fatal)throw fatal;
        if(failure instanceof IOException io)throw io;
        throw new IOException("ordinary worker resource close failed",actual);
    }
}
