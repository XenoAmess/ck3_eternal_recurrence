package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.CompletionException;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.InitialDriverState;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.service.OfflineAnalysisWorker;
import org.xar.ck3.control.service.OrdinarySessionHost;

/** Ordinary worker composition. The supervisor retains ownership of the living Game. */
public final class RootOrdinaryRuntimeAssembly {
    private RootOrdinaryRuntimeAssembly() { }

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

    /** Source-only reader for an existing old Saved daemon; no allocation, genesis, or write authority. */
    public static Prepared prepareReadOnlySavedSource(RootOrdinaryRuntimeConfiguration config,Clock clock)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);
        var metadata=new RootOrdinaryImplementationMetadata();
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application parent");
        byte[] raw;
        try(InputStream input=Files.newInputStream(config.launchPlanFile())) {
            raw=input.readNBytes(NativeLaunchPlanCodec.MAXIMUM_BYTES+1);
        }
        if(raw.length>NativeLaunchPlanCodec.MAXIMUM_BYTES)throw new IOException("launch configuration exceeds its codec limit");
        var planDocument=org.xar.ck3.control.contracts.StrictJson.parse(raw,NativeLaunchPlanCodec.MAXIMUM_BYTES);
        var planConfiguration=planDocument.has("configuration")?planDocument.get("configuration"):planDocument;
        NativeLaunchPlan plan=NativeLaunchPlanCodec.fromJson(planConfiguration).accept();
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
            var lifecycle=new JavaGameLifecycle(permissions,config.operationTimeout());
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
        var prepared=prepare(config,clock,Optional.of(expected));
        try {
            prepared.bindLoadedSavedSource(source);
            return prepared;
        }catch(IOException|RuntimeException|Error failure) {
            try{prepared.close();}catch(IOException|RuntimeException|Error close){if(close!=failure)failure.addSuppressed(close);}
            throw failure;
        }
    }

    private static Prepared prepare(RootOrdinaryRuntimeConfiguration config,Clock clock,
            Optional<org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan> savedGenesis)throws IOException {
        Objects.requireNonNull(config);Objects.requireNonNull(clock);
        var metadata=new RootOrdinaryImplementationMetadata();
        Path root=Objects.requireNonNull(config.stateDirectory().getParent(),"state directory needs an application parent");
        byte[] raw;
        try(InputStream input=Files.newInputStream(config.launchPlanFile())) {
            raw=input.readNBytes(NativeLaunchPlanCodec.MAXIMUM_BYTES+1);
        }
        if(raw.length>NativeLaunchPlanCodec.MAXIMUM_BYTES)throw new IOException("launch configuration exceeds its codec limit");
        var planDocument=org.xar.ck3.control.contracts.StrictJson.parse(raw,NativeLaunchPlanCodec.MAXIMUM_BYTES);
        var planConfiguration=planDocument.has("configuration")?planDocument.get("configuration"):planDocument;
        NativeLaunchPlan plan=NativeLaunchPlanCodec.fromJson(planConfiguration).accept();
        var paths=new WriterContracts.InitialLayout(root.resolve("continuity/continuity.json"),
                root.resolve("continuity/genesis-anchor.json"),config.machineId());
        Path archiveRoot=root.resolve("continuity/artifacts");
        var outputRoots=List.of(config.stateDirectory(),archiveRoot,paths.snapshot().getParent(),
                root.resolve("checkpoints"),root.resolve("receipts"),root.resolve("artifacts"),plan.profileDirectory().resolve("save games"),plan.evidenceRoot());
        for(Path directory:outputRoots)Files.createDirectories(directory);
        Files.createDirectories(config.stateDirectory().resolve("incidents/inputs"));
        Files.createDirectories(config.stateDirectory().resolve("incidents/scan"));
        Files.createDirectories(plan.profileDirectory().resolve("save games/tutorial"));
        boolean anchor=Files.exists(paths.anchor()),snapshot=Files.exists(paths.snapshot()),events=Files.exists(paths.events());
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
            var app=new RootApplicationConfiguration(config.machineId(),HostMode.COMPLETE_MIGRATION,clock.instant(),
                    metadata.file(config.launchPlanFile()),layout,List.of(metadata.implementation(RootOrdinaryRuntimeAssembly.class)),
                    archiveRoot,config.maximumStorageBytes());
            var ports=new RootCoreBoundPorts(app);actualPorts.set(ports);
            var files=storage.checkpointFiles(new NativeCheckpointFiles());
            var operator=RootOperatorCharacterAuthority.prepareOrdinary(metadata.file(config.nativeImplementation()),metadata);
            var runtimePorts=new RootRuntimeSourceProducts.OrdinaryRuntimePorts(ports,files,storage,
                    OriginalRuntimeHandoffProof.unavailable(),operator,metadata,clock);
            var products=RootOrdinaryPlainProducts.prepare(config,app,runtimePorts,config.initialPolicy(),plan);
            var catalogs=products.runtime().catalogs();
            var permissions=catalogs.privatePermissions(ports::qualifyPrivate);
            var lifecycle=new JavaGameLifecycle(permissions,config.operationTimeout());
            return new Prepared(config,clock,plan,metadata,app,ports,storage,files,products,catalogs,permissions,lifecycle);
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
        private final boolean sourceOnly;

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
        public RootOrdinaryRuntimeConfiguration configuration(){return config;}
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
                var admission=RootJavaSavedBootstrap.admitLoaded(source,installed.context(),custody,until);
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
            var sourceG2=new G2Source(actualAttached.machineId(),clock.instant().toString(),hello.gameSha256(),
                    metadata.implementation(RootOrdinaryRuntimeAssembly.class));
            var opened=new Opened(this,sourceG2);
            var installed=runOperationPhase(clock,config.operationTimeout(),until->
                    catalogs.install(core,actualAttached,sourceG2,core.planningReads(),clock,until));
            opened.installed=installed;
            var driver=runOperationPhase(clock,Duration.ofMinutes(10),until->{
                var retained=RootJavaSavedBootstrap.reopenLoaded(source,installed.context(),custody,until);
                return core.adoptRetainedSaved(retained,sourceG2,config.retainedFrames(),until);
            });
            return opened.finishConfirmedSaved(driver,deadline);
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
                var admission=RootJavaSavedBootstrap.admit(confirmed,installed.context(),lifecycle,started,until);
                return core.adoptConfirmedSaved(admission,source,config.retainedFrames(),until);
            });
            return opened.finishConfirmedSaved(driver,deadline);
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
            if(closed||entered||core!=null||loadedSavedSource!=null)throw new IOException("ordinary worker composition is already consumed or closed");
            Objects.requireNonNull(actual);
            if(actual.mode()!=ManagedGameSession.Mode.ATTACHED)throw new IOException("ordinary worker requires the actual supervisor attachment");
            entered=true;game=actual;lifecycle.adoptAttached(actual);
            core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            core.bindFirstHeirMarriageEnabled(config.firstHeirMarriageEnabled());
            core.bindNewMarriageProposalsEnabled(config.newMarriageProposalsEnabled());
            ports.bindCore(core);catalogs.bindCore(core);
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

public Running openSameGameBootstrap(ManagedGameSession actual, Optional<ContinuityBatchJournal.CleanRestartTicket> pointer, Instant deadline) throws IOException, InterruptedException {
    var opened = open(actual);
    if (pointer.isPresent() && opened.core().matchesCleanRestartHead(pointer.orElseThrow())) {
        var driver = runOperationPhase(clock,java.time.Duration.ofMinutes(10),phaseDeadline->
                opened.core().adoptCleanRestart(actual,pointer.orElseThrow(),config.retainedFrames(),cyclePolicy,phaseDeadline));
        return new Opened(this, driver.source()).finish(driver, Optional.of(opened.core().cleanRestartAdmission(driver)), deadline);
    }
    var settled = opened.core().readSettledSameGame(actual,cyclePolicy);
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
                opened.core().adoptUnresolvedSameGame(actual, unresolvedData, config.retainedFrames(), cyclePolicy, phaseDeadline));
        return new Opened(this, driver.source()).finishUnresolvedSameGame(driver, unresolvedData, deadline);
    }
    if (opened.core().hasCanonicalGameplayEntry()) {
        var driver = opened.core().adoptInitialRecovery(actual,config.retainedFrames(),cyclePolicy, () -> clock.instant().plus(config.operationTimeout()));
        return new Opened(this,driver.source()).finish(driver, Optional.empty(), deadline);
    }
    var outcome = runOperationPhase(clock,config.operationTimeout(),actual.nativeTransport()::readFreshFullState);
    if (!(outcome instanceof NativeFreshSnapshotPort.Received)) {
        throw new IOException("actual current-map full read unavailable: "+outcome);
    }
    var received = (NativeFreshSnapshotPort.Received) outcome;
    var initial = InitialDriverState.create(received.originalFrame(), actual.nativeTransport().pipeName(), plan.sessionId(), config.initialPolicy().kind(), config.initialPolicy().lifecycle());
    return runOperationPhase(clock,config.operationTimeout(),phaseDeadline->opened.finishObservedMap(received,initial,phaseDeadline));
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

        private RootApplicationAssembly.FreshSessionConfiguration sessionConfiguration(Instant deadline)throws IOException {
            Path state=config.stateDirectory();
            var checkpoints=new RootStartupConfiguration.CheckpointPaths(state.resolve("driver/checkpoint.json"),
                    state.resolve("checkpoints/evidence"),state.resolve("checkpoints/attachments"),config.authorityId()+"-lineage",
                    plan.profileDirectory().resolve("save games/xar_checkpoint.ck3"));
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

        public void closeResourcesOnly()throws IOException {close();}
        @Override public synchronized void close()throws IOException {
            if(closed)return;closed=true;Throwable failure=null;
            if(core!=null) {
                try {core.close();}catch(RuntimeException|Error close){failure=close;}
                try {core.closeCompletion().toCompletableFuture().join();}
                catch(RuntimeException|Error close){failure=merge(failure,close);}
            }else try {storage.close();}catch(IOException|RuntimeException|Error close){failure=close;}
            if(sourceOnly) {
                try {noWrites.close();}catch(IOException|RuntimeException|Error close){failure=merge(failure,close);}
                try {storage.close();}catch(IOException|RuntimeException|Error close){failure=merge(failure,close);}
            }
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
                session.install(new OrdinarySessionHost(),phaseDeadline);
                return null;
            });
            String prefix=restart.isPresent()?restart.orElseThrow().controller().batchPrefix():
                    noDispatch.map(ContinuityBatchJournal.InitialNoDispatchRecovery::batchPrefix).orElse(owner.config.loop().batchIdPrefix());
            long next=restart.isPresent()?restart.orElseThrow().controller().nextBatchSequence():
                    noDispatch.map(ContinuityBatchJournal.InitialNoDispatchRecovery::nextBatchSequence).orElse(0L);
            return new Running(owner,session,prefix,next);
        }

        private Running finishConfirmedSaved(DriverBootstrap.Adopted driver,Instant deadline)throws IOException,InterruptedException {
            if(consumed||installed==null)throw new IOException("actual saved graph installation is unavailable or consumed");
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
                session.install(new OrdinarySessionHost(),until);return null;
            });
            return new Running(owner,session,owner.config.loop().batchIdPrefix(),0L);
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
            var session=owner.core.finishSettledSameGame(installed,driver,configuration,owner.services(source));
            runOperationPhase(owner.clock,owner.config.operationTimeout(),phaseDeadline->{
                session.install(new OrdinarySessionHost(),phaseDeadline);return null;
            });
            return new Running(owner,session,data.controller().batchPrefix(),data.controller().nextBatchSequence());
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
                session.install(new OrdinarySessionHost(),phaseDeadline);
                return null;
            });
            // Restore quarantine and reconcile unresolved action
            session.restoreUnresolvedSameGame(data);
            // The original mutation is read-only here; closing its retained cycle can
            // require a fresh full semantic read and multiple durable ledger commits.
            org.xar.ck3.control.application.action.ActionReceipt receipt = null;
            if (data.unresolvedActions().size() == 1) {
                var retainedOriginal = data.unresolvedActions().getFirst();
                if (org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(retainedOriginal.command().operation().value())) {
                    receipt = runOperationPhase(owner.clock, java.time.Duration.ofMinutes(10), phaseDeadline -> {
                        var cancellation = installed.remainingDomains().life().composite().cancellationToken(retainedOriginal, phaseDeadline);
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
        public String batchPrefix(){return prefix;}
        public long nextBatchSequence(){return next;}
        public void closeResourcesOnly()throws IOException {owner.close();}
        @Override public void close()throws IOException {owner.close();}
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
