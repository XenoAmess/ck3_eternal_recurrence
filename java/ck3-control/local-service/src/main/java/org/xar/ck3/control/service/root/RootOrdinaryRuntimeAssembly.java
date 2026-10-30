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
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
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
                root.resolve("checkpoints"),root.resolve("receipts"),root.resolve("artifacts"));
        for(Path directory:outputRoots)Files.createDirectories(directory);
        Files.createDirectories(config.stateDirectory().resolve("incidents/inputs"));
        Files.createDirectories(config.stateDirectory().resolve("incidents/scan"));
        Files.createDirectories(plan.profileDirectory().resolve("save games/tutorial"));
        boolean anchor=Files.exists(paths.anchor()),snapshot=Files.exists(paths.snapshot()),events=Files.exists(paths.events());
        if((anchor||snapshot||events)&&!(anchor&&snapshot&&events))
            throw new IOException("partial canonical ledger initialization is retained for recovery; it cannot be overwritten");
        Path request=paths.snapshot().getParent().resolve("genesis-request.json");
        var genesis=anchor?Optional.<org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan>empty()
                :Optional.of(genesisRequest(request,config.machineId(),clock));
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
        private final OriginalWindowReducer.Policy cyclePolicy=new OriginalWindowReducer.Policy(OriginalWindowReducer.TARGET_DAYS);
        private final NativeReadiness.Policy policy=new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ZERO,false);
        private RootApplicationAssembly.Core core;
        private ManagedGameSession game;
        private boolean entered;
        private boolean closed;

        private Prepared(RootOrdinaryRuntimeConfiguration config,Clock clock,NativeLaunchPlan plan,
                RootOrdinaryImplementationMetadata metadata,RootApplicationConfiguration app,RootCoreBoundPorts ports,
                RootRuntimeStorageGuard storage,CheckpointFiles files,RootRuntimeSourceProducts.PlainPrepared products,
                RootRuntimeCatalogFactory catalogs,List<NativePrivateActionPermission> permissions,JavaGameLifecycle lifecycle) {
            this.config=config;this.clock=clock;this.plan=plan;this.metadata=metadata;this.app=app;this.ports=ports;
            this.storage=storage;this.files=files;this.products=products;this.catalogs=catalogs;
            this.permissions=List.copyOf(permissions);this.lifecycle=lifecycle;
        }
        public RootOrdinaryRuntimeConfiguration configuration(){return config;}
        public InitialEpisodePolicy initialPolicy(){return config.initialPolicy();}
        public NativeLaunchPlan plan(){return plan;}
        public List<NativePrivateActionPermission> privatePermissions(){return permissions;}
        public RootRuntimeCatalogFactory catalogs(){return catalogs;}

        private synchronized void openCore(ManagedGameSession actual)throws IOException {
            if(closed||entered)throw new IOException("ordinary worker composition is already consumed or closed");
            Objects.requireNonNull(actual);
            if(actual.mode()!=ManagedGameSession.Mode.ATTACHED)throw new IOException("ordinary worker requires the actual supervisor attachment");
            entered=true;game=actual;lifecycle.adoptAttached(actual);
            core=RootApplicationAssembly.open(app,clock,catalogs.domainRegistrations(),Optional.empty(),storage);
            core.bindM5JointPeacetimeEnabled(config.m5JointPeacetimeEnabled());
            ports.bindCore(core);catalogs.bindCore(core);
            products.domains().lifecycle().bindManagedLifecycle(lifecycle,plan);
        }

        public Opened open(ManagedGameSession actual)throws IOException,InterruptedException {
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
        var driver = runOperationPhase(clock,config.operationTimeout(),phaseDeadline->
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
            openCore(actual);
            var driver=runOperationPhase(clock,config.operationTimeout(),phaseDeadline->
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
            var receipt = runOperationPhase(owner.clock,java.time.Duration.ofMinutes(10),phaseDeadline->
                    session.reconcileUnresolvedOriginal(data,phaseDeadline));
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
